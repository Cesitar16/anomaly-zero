import 'maplibre-gl/dist/maplibre-gl.css'
import { Map as MapLibreMap, NavigationControl, setWorkerUrl } from 'maplibre-gl'
import type { ImageSource, StyleSpecification } from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import { useEffect, useRef, useState } from 'react'
import { COPY } from '../content/exploreCopy'
import type { Bbox, ResolvedRaster } from '../lib/rasterTarget'
import { monthLabel } from '../lib/months'
import type { YearMonth } from '../types/contracts'

// MapLibre GL JS 6 busca su worker como un archivo hermano que no existe al empaquetar con Vite
// ("Worker failed to load"). Vite empaqueta el worker con `?worker&url` y se lo entregamos antes de crear el mapa.
setWorkerUrl(workerUrl)

const SOURCE_ID = 'frame'
const LAYER_ID = 'frame-layer'

// Sin mapa base: ni teselas ni servicios de terceros. Solo un lienzo neutro. El gris NO es un mapa.
const NEUTRAL_STYLE: StyleSpecification = {
  version: 8,
  sources: {},
  layers: [{ id: 'background', type: 'background', paint: { 'background-color': '#e8edf0' } }],
}

/** Esquinas en el orden que exige MapLibre para un ImageSource: NO, NE, SE, SO. */
function corners(bbox: Bbox): [[number, number], [number, number], [number, number], [number, number]] {
  return [
    [bbox.west, bbox.north],
    [bbox.east, bbox.north],
    [bbox.east, bbox.south],
    [bbox.west, bbox.south],
  ]
}

async function loadBitmap(url: string, signal: AbortSignal): Promise<ImageBitmap> {
  const response = await fetch(url, { signal })
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return createImageBitmap(await response.blob())
}

export interface MapCanvasProps {
  raster: ResolvedRaster
  month: YearMonth
}

/**
 * Lienzo de MapLibre. Se carga de forma diferida (React.lazy) y solo cuando hay una capa dibujable, que
 * hoy son las capas SINTÉTICAS de demostración. Crea el mapa UNA vez y cambia de mes con `updateImage`;
 * mientras carga una imagen oculta la anterior, así nunca se ve un mes bajo la etiqueta de otro.
 */
export default function MapCanvas({ raster, month }: MapCanvasProps) {
  const container = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MapLibreMap | null>(null)
  const shown = useRef<string | null>(null)
  const [ready, setReady] = useState(false)
  const [retry, setRetry] = useState(0)
  const [settled, setSettled] = useState<{ key: string; error: boolean } | null>(null)
  const key = `${raster.url}#${retry}`

  useEffect(() => {
    if (!container.current) return
    const map = new MapLibreMap({
      container: container.current,
      style: NEUTRAL_STYLE,
      bounds: [
        [raster.bbox.west, raster.bbox.south],
        [raster.bbox.east, raster.bbox.north],
      ],
      fitBoundsOptions: { padding: 24 },
      attributionControl: false,
      dragRotate: false,
      touchPitch: false,
      locale: { 'NavigationControl.ZoomIn': 'Acercar', 'NavigationControl.ZoomOut': 'Alejar' },
    })
    map.addControl(new NavigationControl({ showCompass: false }), 'top-right')
    map.getCanvas().setAttribute('aria-label', COPY.map.demoLayer)
    map.on('load', () => {
      map.addSource(SOURCE_ID, { type: 'image', coordinates: corners(raster.bbox) })
      map.addLayer({
        id: LAYER_ID,
        type: 'raster',
        source: SOURCE_ID,
        layout: { visibility: 'none' },
        // nearest: la rejilla es discreta; suavizarla sugeriría una precisión que no existe.
        // fade 0: el cambio de mes es un salto, nunca una animación interpolada.
        paint: { 'raster-resampling': 'nearest', 'raster-fade-duration': 0 },
      })
      setReady(true)
    })
    mapRef.current = map
    return () => {
      map.remove()
      mapRef.current = null
      shown.current = null
      setReady(false)
    }
    // El mapa se crea una vez; la imagen cambia por `updateImage`.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    const map = mapRef.current
    if (!ready || !map) return
    if (shown.current === key) {
      map.setLayoutProperty(LAYER_ID, 'visibility', 'visible')
      return
    }
    map.setLayoutProperty(LAYER_ID, 'visibility', 'none')
    const controller = new AbortController()
    loadBitmap(raster.url, controller.signal)
      .then((bitmap) => {
        if (controller.signal.aborted) return
        const source = map.getSource(SOURCE_ID) as ImageSource
        source.updateImage({ image: bitmap, coordinates: corners(raster.bbox) })
        shown.current = key
        map.setLayoutProperty(LAYER_ID, 'visibility', 'visible')
        setSettled({ key, error: false })
      })
      .catch(() => {
        if (!controller.signal.aborted) setSettled({ key, error: true })
      })
    return () => controller.abort()
  }, [ready, key, raster])

  const busy = settled?.key !== key
  const failed = settled?.key === key && settled.error

  return (
    <div className="explore-map" aria-busy={busy} data-testid="map-canvas">
      <div ref={container} className="explore-map__canvas" />
      <p className="explore-map__status" role="status">
        {busy ? COPY.map.loading(monthLabel(month)) : ''}
      </p>
      {failed && (
        <div className="explore-map__message" role="alert">
          <p>{COPY.map.loadError(monthLabel(month))}</p>
          <button type="button" className="btn btn--secondary" onClick={() => setRetry((count) => count + 1)}>
            {COPY.map.retry}
          </button>
        </div>
      )}
    </div>
  )
}

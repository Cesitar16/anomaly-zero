import 'maplibre-gl/dist/maplibre-gl.css'
import '../lib/maplibreWorker'
import type { ImageSource, Map as MapLibreMap, StyleSpecification } from 'maplibre-gl'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Map as ReactMap } from 'react-map-gl/maplibre'
import type { MapRef } from 'react-map-gl/maplibre'
import { buildGraticule, SYNTHETIC_POLYGON } from '../data/fixtures'
import { loadFrameBitmap } from '../lib/frameLoader'
import { resolveFrameTarget } from '../lib/frameTarget'
import { imageCoordinates } from '../lib/geo'
import { monthLabel } from '../lib/months'
import type { FrameManifest, FrameStatus, ImageVariant, MapMode, RasterLayer, YearMonth } from '../types'

const FRAME_SOURCE = 'frame'
const FRAME_LAYER = 'frame-layer'

// Sin mapa base: ni teselas, ni claves, ni servicios de terceros. Solo un fondo neutro.
const NEUTRAL_STYLE: StyleSpecification = {
  version: 8,
  sources: {},
  layers: [{ id: 'background', type: 'background', paint: { 'background-color': '#e8edf0' } }],
}

export interface MapPanelProps {
  month: YearMonth
  mode: MapMode
  variant: ImageVariant
  manifest: FrameManifest
  rasterLayers: RasterLayer[]
  onStatusChange?: (status: FrameStatus) => void
}

/** Contadores de depuración solo en desarrollo: permiten comprobar que el mapa NO se reconstruye por mes. */
interface SpikeDebug {
  mapLoads: number
  imageUpdates: number
  hiddenCount: number
  visibleMonth: string | null
  coordinates: number[][] | null
}

declare global {
  interface Window {
    __SPIKE__?: SpikeDebug
    __SPIKE_MAP__?: MapLibreMap
  }
}

function debug(): SpikeDebug | null {
  if (!import.meta.env.DEV) return null
  window.__SPIKE__ ??= { mapLoads: 0, imageUpdates: 0, hiddenCount: 0, visibleMonth: null, coordinates: null }
  return window.__SPIKE__
}

function setupLayers(map: MapLibreMap, manifest: FrameManifest) {
  const coordinates = imageCoordinates(manifest.bbox)
  // Fuente de imagen SIN url: se alimenta únicamente con updateImage (sin reconstruir el mapa).
  map.addSource(FRAME_SOURCE, { type: 'image', coordinates })
  map.addLayer({
    id: FRAME_LAYER,
    type: 'raster',
    source: FRAME_SOURCE,
    layout: { visibility: 'none' },
    // nearest: la rejilla es discreta; suavizarla sugeriría una precisión que no existe.
    // fade 0: sin fundido entre meses; el cambio es un salto, nunca una animación interpolada.
    paint: { 'raster-resampling': 'nearest', 'raster-fade-duration': 0, 'raster-opacity': 1 },
  })

  // Meridianos y paralelos cada 2° SOBRE la imagen: si la georreferenciación es correcta, las marcas
  // blancas de latitud quedan alineadas con estas líneas.
  map.addSource('graticule', { type: 'geojson', data: buildGraticule(manifest.bbox) })
  map.addLayer({
    id: 'graticule-lines',
    type: 'line',
    source: 'graticule',
    paint: { 'line-color': '#10222b', 'line-width': 0.7, 'line-opacity': 0.5 },
  })

  map.addSource('synthetic-polygon', { type: 'geojson', data: SYNTHETIC_POLYGON })
  map.addLayer({
    id: 'synthetic-polygon-outline',
    type: 'line',
    source: 'synthetic-polygon',
    paint: { 'line-color': '#b42318', 'line-width': 2, 'line-dasharray': [3, 2] },
  })
}

export function MapPanel({ month, mode, variant, manifest, rasterLayers, onStatusChange }: MapPanelProps) {
  const mapRef = useRef<MapRef>(null)
  const [mapReady, setMapReady] = useState(false)
  // Resultado de la última carga terminada (se escribe solo desde callbacks asíncronos, no desde el cuerpo del efecto).
  const [loaded, setLoaded] = useState<{ key: string; error: string | null } | null>(null)
  const [retryKey, setRetryKey] = useState(0)
  // Clave de la imagen que está realmente dentro del ImageSource ahora mismo.
  const shownKey = useRef<string | null>(null)
  const requestId = useRef(0)

  const target = useMemo(
    () => resolveFrameTarget({ month, mode, variant, manifest, rasterLayers, basePath: import.meta.env.BASE_URL }),
    [month, mode, variant, manifest, rasterLayers],
  )
  const key = target.kind === 'frame' ? `${target.url}#${retryKey}` : null

  // El estado visible se DERIVA: no se duplica en un useState sincronizado por efecto.
  const status: FrameStatus = useMemo(() => {
    if (target.kind === 'missing') return { kind: 'missing', month, reason: target.reason }
    if (loaded?.key === key) {
      return loaded.error === null ? { kind: 'ready', month } : { kind: 'error', month, message: loaded.error }
    }
    return { kind: 'loading', month }
  }, [target, month, loaded, key])

  const initialView = useMemo(
    () => ({
      bounds: [
        [manifest.bbox.west, manifest.bbox.south],
        [manifest.bbox.east, manifest.bbox.north],
      ] as [[number, number], [number, number]],
      fitBoundsOptions: { padding: 24 },
    }),
    [manifest.bbox],
  )

  useEffect(() => {
    onStatusChange?.(status)
  }, [status, onStatusChange])

  const handleLoad = useCallback(() => {
    const map = mapRef.current?.getMap()
    if (!map) return
    setupLayers(map, manifest)
    map.getCanvas().setAttribute('aria-label', 'Mapa de prueba con datos sintéticos. Use las flechas para desplazar y más o menos para acercar.')
    const counters = debug()
    if (counters) {
      counters.mapLoads += 1
      window.__SPIKE_MAP__ = map
    }
    setMapReady(true)
  }, [manifest])

  useEffect(() => {
    const map = mapRef.current?.getMap()
    if (!mapReady || !map) return
    const id = ++requestId.current
    const controller = new AbortController()
    const counters = debug()

    const show = (shownMonth: string | null) => {
      map.setLayoutProperty(FRAME_LAYER, 'visibility', shownMonth ? 'visible' : 'none')
      if (counters) counters.visibleMonth = shownMonth
    }

    // Mes sin capa: se oculta lo que hubiera y se declara ausente. Jamás se deja visible el mes anterior.
    if (target.kind === 'missing') {
      show(null)
      return
    }
    // La imagen que ya está en el ImageSource es justo la pedida: solo se vuelve a mostrar.
    if (shownKey.current === key) {
      show(month)
      return
    }

    // Mientras carga, la capa anterior se oculta: nunca se ve un mes bajo la etiqueta de otro.
    show(null)
    loadFrameBitmap(target.url, controller.signal)
      .then((bitmap) => {
        if (id !== requestId.current) return // llegó tarde: ya hay otra solicitud vigente
        const source = map.getSource(FRAME_SOURCE) as ImageSource
        const coordinates = imageCoordinates(manifest.bbox)
        source.updateImage({ image: bitmap, coordinates })
        shownKey.current = key
        show(month)
        if (counters) {
          counters.imageUpdates += 1
          counters.coordinates = coordinates
        }
        setLoaded({ key: key as string, error: null })
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted || id !== requestId.current) return
        setLoaded({ key: key as string, error: error instanceof Error ? error.message : 'Error desconocido al cargar el frame.' })
      })
    return () => controller.abort()
  }, [mapReady, target, key, month, manifest.bbox])

  const busy = status.kind === 'loading'
  const message =
    status.kind === 'missing' && target.kind === 'missing'
      ? { title: `Capa no disponible para ${month}`, detail: target.message }
      : status.kind === 'error'
        ? { title: `No se pudo cargar la capa de ${month}`, detail: 'La imagen no se pudo descargar o decodificar. Puedes reintentar.' }
        : null

  return (
    <div className="map-panel">
      <div
        className="map-frame"
        aria-busy={busy}
        data-testid="map-frame"
        data-status={status.kind}
        data-visible-month={status.kind === 'ready' ? status.month : ''}
      >
        <ReactMap
          ref={mapRef}
          mapStyle={NEUTRAL_STYLE}
          initialViewState={initialView}
          attributionControl={false}
          dragRotate={false}
          touchPitch={false}
          style={{ width: '100%', height: '100%' }}
          onLoad={handleLoad}
        />
        <div className="map-status" role="status" aria-live="polite">
          {busy && <span className="map-status__loading">Cargando capa de {monthLabel(month)}…</span>}
          {status.kind === 'ready' && <span className="visually-hidden">Capa de {monthLabel(month)} mostrada.</span>}
        </div>
        {message && (
          <div className="map-message" role="alert">
            <strong>{message.title}</strong>
            <span>{message.detail}</span>
            {status.kind === 'error' && (
              <button type="button" className="button" onClick={() => setRetryKey((count) => count + 1)}>
                Reintentar
              </button>
            )}
          </div>
        )}
      </div>
      <p className="map-badge">Vista cartográfica de prueba · sin mapa base. El fondo gris es el lienzo, no un mapa base.</p>
    </div>
  )
}

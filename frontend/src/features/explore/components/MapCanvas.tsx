import 'maplibre-gl/dist/maplibre-gl.css'
import { AttributionControl, Map as MapLibreMap, Marker, NavigationControl, Popup, setWorkerUrl } from 'maplibre-gl'
import type { GeoJSONSource, ImageSource, StyleSpecification } from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import { useEffect, useRef, useState } from 'react'
import type { Bbox, ResolvedRaster } from '../lib/rasterTarget'
import { MURRAY_DARLING_VIEW, toMapLibreCoordinates } from '../lib/contextMap'
import type { ContextGeometryOverlay, MapMarkerDetails } from '../lib/contextMap'
import type { YearMonth } from '../types/contracts'

// Vite empaqueta el worker de MapLibre en un archivo independiente.
setWorkerUrl(workerUrl)

const OSM_TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
const SOURCE_ID = 'demo-frame'
const LAYER_ID = 'demo-frame-layer'
const TRANSPARENT_PIXEL =
  'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p7sAAAAASUVORK5CYII='

const CONTEXT_BOUNDS: [[number, number], [number, number]] = [
  [MURRAY_DARLING_VIEW.west, MURRAY_DARLING_VIEW.south],
  [MURRAY_DARLING_VIEW.east, MURRAY_DARLING_VIEW.north],
]

const BASE_STYLE: StyleSpecification = {
  version: 8,
  sources: {
    openstreetmap: {
      type: 'raster',
      tiles: [OSM_TILE_URL],
      tileSize: 256,
      attribution: '© OpenStreetMap contributors',
    },
  },
  layers: [{ id: 'openstreetmap-raster', type: 'raster', source: 'openstreetmap', paint: { 'raster-fade-duration': 0 } }],
}

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

function popupContent(point: MapMarkerDetails): HTMLElement {
  const content = document.createElement('div')
  content.className = 'explore-map-popup'
  content.setAttribute('role', 'dialog')
  content.setAttribute('aria-label', `Información de ${point.label}`)
  const rows = [
    [point.label, point.synthetic ? 'Datos sintéticos de demostración' : 'Observación NASA'],
    ['Producto', `${point.productName} (${point.productId}), versión ${point.productVersion}`],
    ['Celda', point.cellId ?? 'No informada'],
    ['Coordenadas', `${point.latitude.toFixed(4)}, ${point.longitude.toFixed(4)} (latitud, longitud)`],
    ['Unidad', point.unit || 'No informada'],
    ['Soporte', 'point_sample · muestra puntual'],
    ['Calidad', `${point.verificationState}; flags del proveedor aplicados: ${point.providerFlagsApplied ? 'sí' : 'no'}; QA no aprobada`],
  ]
  for (const [label, value] of rows) {
    const paragraph = document.createElement('p')
    const strong = document.createElement('strong')
    strong.textContent = `${label}: `
    paragraph.append(strong, document.createTextNode(value))
    content.append(paragraph)
  }
  return content
}

export interface MapCanvasProps {
  raster?: ResolvedRaster | null
  month?: YearMonth | null
  marker?: MapMarkerDetails | null
  contextGeometry?: ContextGeometryOverlay | null
}

/** Mapa base contextual, con raster exclusivamente para las capas sintéticas existentes de demostración. */
export default function MapCanvas({ raster = null, month = null, marker = null, contextGeometry = null }: MapCanvasProps) {
  const container = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MapLibreMap | null>(null)
  const markerRef = useRef<Marker | null>(null)
  const popupRef = useRef<Popup | null>(null)
  const [retry, setRetry] = useState(0)
  const [loaded, setLoaded] = useState(false)
  const [baseMapFailed, setBaseMapFailed] = useState(false)
  const [geometryFailed, setGeometryFailed] = useState(false)
  const [rasterState, setRasterState] = useState<{ key: string; status: 'loading' | 'ready' | 'error' } | null>(null)
  const rasterKey = raster ? `${raster.url}:${month ?? ''}:${retry}` : null

  useEffect(() => {
    if (!container.current) return
    setLoaded(false)
    setBaseMapFailed(false)
    setGeometryFailed(false)
    setRasterState(null)
    let map: MapLibreMap
    try {
      map = new MapLibreMap({
        container: container.current,
        style: BASE_STYLE,
        bounds: raster ? [[raster.bbox.west, raster.bbox.south], [raster.bbox.east, raster.bbox.north]] : CONTEXT_BOUNDS,
        fitBoundsOptions: { padding: 38, maxZoom: 6 },
        minZoom: 3,
        maxZoom: 16,
        maxPitch: 0,
        attributionControl: false,
        dragRotate: false,
        touchPitch: false,
        locale: { 'NavigationControl.ZoomIn': 'Acercar', 'NavigationControl.ZoomOut': 'Alejar' },
      })
    } catch {
      setLoaded(false)
      setBaseMapFailed(true)
      return
    }

    map.addControl(new NavigationControl({ showCompass: false }), 'top-right')
    map.addControl(new AttributionControl({ compact: false }), 'bottom-right')
    map.getCanvas().setAttribute(
      'aria-label',
      'Mapa geográfico interactivo de referencia de Murray–Darling. Use las teclas de flecha para desplazarse y los controles para cambiar el zoom.',
    )
    map.getCanvas().setAttribute('role', 'region')
    map.on('load', () => setLoaded(true))
    map.on('error', (event) => {
      const sourceId = (event as typeof event & { sourceId?: string }).sourceId
      if (sourceId === SOURCE_ID) return
      if (sourceId === 'context-region') {
        setGeometryFailed(true)
        return
      }
      setBaseMapFailed(true)
      setLoaded(true)
    })
    mapRef.current = map
    return () => {
      markerRef.current?.remove()
      markerRef.current = null
      popupRef.current?.remove()
      popupRef.current = null
      map.remove()
      mapRef.current = null
    }
    // Map is recreated only for explicit retry; its initial extent is set from the current raster once.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [retry])

  useEffect(() => {
    const map = mapRef.current
    if (!loaded || !map) return
    if (!raster || !rasterKey) {
      if (map.getLayer(LAYER_ID)) map.setLayoutProperty(LAYER_ID, 'visibility', 'none')
      setRasterState(null)
      return
    }

    const controller = new AbortController()
    setRasterState({ key: rasterKey, status: 'loading' })
    if (!map.getSource(SOURCE_ID)) {
      map.addSource(SOURCE_ID, {
        type: 'image',
        url: TRANSPARENT_PIXEL,
        coordinates: corners(raster.bbox),
      })
      map.addLayer({
        id: LAYER_ID,
        type: 'raster',
        source: SOURCE_ID,
        layout: { visibility: 'none' },
        paint: { 'raster-resampling': 'nearest', 'raster-fade-duration': 0 },
      })
    }
    map.setLayoutProperty(LAYER_ID, 'visibility', 'none')
    loadBitmap(raster.url, controller.signal)
      .then((bitmap) => {
        if (controller.signal.aborted) {
          bitmap.close()
          return
        }
        const source = map.getSource(SOURCE_ID) as ImageSource
        source.updateImage({ image: bitmap, coordinates: corners(raster.bbox) })
        map.setLayoutProperty(LAYER_ID, 'visibility', 'visible')
        setRasterState({ key: rasterKey, status: 'ready' })
      })
      .catch(() => {
        if (!controller.signal.aborted) setRasterState({ key: rasterKey, status: 'error' })
      })
    return () => controller.abort()
  }, [loaded, raster, rasterKey])

  useEffect(() => {
    const map = mapRef.current
    if (!loaded || !map || !contextGeometry) return
    try {
      const source = map.getSource('context-region') as GeoJSONSource | undefined
      if (source) {
        source.setData(contextGeometry.data)
      } else {
        map.addSource('context-region', {
          type: 'geojson',
          data: contextGeometry.data,
        })
        // A thin outline is contextual only; it is never used to mask or aggregate observations.
        map.addLayer({
          id: 'context-region-outline',
          type: 'line',
          source: 'context-region',
          paint: { 'line-color': '#9d482f', 'line-width': 2, 'line-dasharray': [2, 1] },
        })
      }
      setGeometryFailed(false)
    } catch {
      setGeometryFailed(true)
    }
  }, [contextGeometry, loaded])

  useEffect(() => {
    const map = mapRef.current
    if (!loaded || !map) return
    markerRef.current?.remove()
    markerRef.current = null
    popupRef.current?.remove()
    popupRef.current = null
    if (!marker) return

    const element = document.createElement('button')
    element.type = 'button'
    element.className = `explore-map-marker${marker.synthetic ? ' explore-map-marker--synthetic' : ''}`
    element.setAttribute('aria-label', `${marker.label}; celda ${marker.cellId ?? 'no informada'}; seleccionar para ver detalles`)
    element.title = marker.label
    const popup = new Popup({ closeButton: true, closeOnClick: false, focusAfterOpen: true }).setDOMContent(popupContent(marker))
    element.addEventListener('click', () => popup.addTo(map))
    const mapMarker = new Marker({ element, anchor: 'bottom' }).setLngLat(toMapLibreCoordinates(marker)).addTo(map)
    markerRef.current = mapMarker
    popupRef.current = popup
    return () => {
      mapMarker.remove()
      popup.remove()
      if (markerRef.current === mapMarker) markerRef.current = null
      if (popupRef.current === popup) popupRef.current = null
    }
  }, [loaded, marker])

  const rasterBusy = rasterKey !== null && (rasterState?.key !== rasterKey || rasterState.status === 'loading')
  const rasterFailed = rasterKey !== null && rasterState?.key === rasterKey && rasterState.status === 'error'

  return (
    <div className="explore-map" aria-busy={!loaded || rasterBusy} data-testid="map-canvas">
      <div ref={container} className="explore-map__canvas" />
      <p className="explore-map__status" role="status" aria-live="polite">
        {!loaded ? 'Cargando mapa geográfico…' : baseMapFailed ? 'Mapa base no disponible; el resto del explorador sigue funcionando.' : rasterBusy && month ? `Cargando capa sintética ${month}…` : ''}
      </p>
      {(baseMapFailed || rasterFailed) && (
        <div className="explore-map__message" role="alert">
          <p>
            {baseMapFailed
              ? 'No se pudo cargar el mapa base. Comprueba la conexión e inténtalo de nuevo.'
              : 'No se pudo cargar la capa sintética de demostración para este mes.'}
          </p>
          <button type="button" className="btn btn--secondary" onClick={() => setRetry((count) => count + 1)}>
            Reintentar mapa
          </button>
        </div>
      )}
      {geometryFailed && <p className="explore-map__message" role="status">No se pudo dibujar el límite de referencia. El mapa y la serie siguen disponibles.</p>}
    </div>
  )
}

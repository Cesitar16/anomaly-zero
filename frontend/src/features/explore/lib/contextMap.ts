import type { GeoJSONSourceSpecification } from 'maplibre-gl'
import type { SpatialAggregation } from '../types/contracts'

export interface MapPoint {
  latitude: number
  longitude: number
  cellId: string | null
}

export interface MapMarkerDetails extends MapPoint {
  label: string
  productId: string
  productName: string
  productVersion: string
  unit: string
  synthetic: boolean
  verificationState: string
  providerFlagsApplied: boolean
}

/** Forma normalizada del GeoJSON BE-10 para MapLibre, con procedencia retenida aparte del GeoJSON. */
export interface ContextGeometryOverlay {
  data: Exclude<GeoJSONSourceSpecification['data'], string>
  label: string
  attribution: string
  sourceUrl: string
  licenseName: string
  licenseUrl: string
  sha256: string
}

/** Resuelve únicamente un point_sample declarado; nunca deriva un punto del encuadre regional. */
export function pointFromSupport(support: SpatialAggregation | null): MapPoint | null {
  if (!support || support.support_type !== 'point_sample') return null
  const point = (support as { point?: unknown }).point
  if (typeof point !== 'object' || point === null) return null
  const { latitude, longitude, cell_id: cellId } = point as Record<string, unknown>
  if (
    typeof latitude !== 'number' ||
    typeof longitude !== 'number' ||
    !Number.isFinite(latitude) ||
    !Number.isFinite(longitude) ||
    latitude < -90 || latitude > 90 ||
    longitude < -180 || longitude > 180
  ) {
    return null
  }
  return { latitude, longitude, cellId: typeof cellId === 'string' && cellId.trim() ? cellId : null }
}

/** MapLibre requiere [longitud, latitud], aunque el contrato enumera latitude antes que longitude. */
export function toMapLibreCoordinates(point: MapPoint): [longitude: number, latitude: number] {
  return [point.longitude, point.latitude]
}

/** Requires provenance and a Polygon/MultiPolygon FeatureCollection before any future BE-10 overlay is drawn. */
export function hasVerifiedContextGeometry(overlay: ContextGeometryOverlay | null | undefined): overlay is ContextGeometryOverlay {
  if (
    !overlay ||
    typeof overlay.label !== 'string' || !overlay.label.trim() ||
    typeof overlay.attribution !== 'string' || !overlay.attribution.trim() ||
    typeof overlay.licenseName !== 'string' || !overlay.licenseName.trim() ||
    typeof overlay.sha256 !== 'string' || !/^[a-f\d]{64}$/i.test(overlay.sha256) ||
    typeof overlay.sourceUrl !== 'string' || typeof overlay.licenseUrl !== 'string'
  ) return false
  const isHttps = (value: string) => {
    try { return new URL(value).protocol === 'https:' } catch { return false }
  }
  if (!isHttps(overlay.sourceUrl) || !isHttps(overlay.licenseUrl)) return false
  const data = overlay.data as unknown as { type?: unknown; features?: unknown }
  if (typeof data !== 'object' || data === null) return false
  if (data.type !== 'FeatureCollection' || !Array.isArray(data.features) || data.features.length === 0) return false
  return data.features.every((item) => {
    if (typeof item !== 'object' || item === null || !('geometry' in item)) return false
    const geometry = (item as { geometry?: unknown }).geometry
    if (typeof geometry !== 'object' || geometry === null || !('type' in geometry) || !('coordinates' in geometry)) return false
    const type = (geometry as { type?: unknown }).type
    const coordinates = (geometry as { coordinates?: unknown }).coordinates
    return (type === 'Polygon' || type === 'MultiPolygon') && Array.isArray(coordinates)
  })
}

/** Extensión de navegación aproximada documentada; se usa para encuadrar, nunca se dibuja como límite. */
export const MURRAY_DARLING_VIEW = {
  west: 138.5685,
  south: -37.6821,
  east: 152.4885,
  north: -24.5856,
} as const

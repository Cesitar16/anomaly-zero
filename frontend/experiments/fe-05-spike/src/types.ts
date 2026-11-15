// Subconjunto de los tipos del contrato v0 (docs/openapi-contract-v0.yaml, `contract_version: 0.1-draft`)
// que necesita el spike. Los nombres y valores siguen al OpenAPI integrado en `dev`; no se inventa ningún
// campo. Todo lo que NO está en el contrato está marcado como "solo prototipo".

export type YearMonth = string // YYYY-MM, validado por UI (patrón del contrato: ^\d{4}-(0[1-9]|1[0-2])$)

// --- Contrato ---
export type PointQualityState = 'unassessed' | 'missing' | 'unknown'

export interface ProviderFlag {
  name: string
  value: unknown
}

export interface PointQuality {
  state: PointQualityState
  provider_flags: ProviderFlag[]
  missing_reason: string | null
}

export interface SeriesPoint {
  date: string // primer día del mes: YYYY-MM-01
  value: number | null // cero es un valor válido; null es faltante
  quality: PointQuality
}

export type RasterLayerType = 'value' | 'anomaly' | 'slope' | 'significance'

export interface RasterLayer {
  dataset_id: string
  date: YearMonth
  layer_type: RasterLayerType
  unit: string | null
  state: 'unavailable' | 'available'
  format: string | null
  tile_template: string | null
}

// --- Solo prototipo (NO forman parte del contrato API) ---
export interface Bbox {
  west: number
  south: number
  east: number
  north: number
}

export type ImageVariant = 'native' | 'mercator'

export interface ScaleClass {
  color: string
  from: number
  to: number
}

export interface FrameMonth {
  date: YearMonth
  frame: string | null
  reason: string | null
}

export interface FrameManifest {
  synthetic: true
  label: string
  generator: string
  crs: string
  bbox: Bbox
  resolution_deg: number
  variants: Record<ImageVariant, { width: number; height: number; description: string }>
  scale: { unit: string; min: number; max: number; classes: ScaleClass[]; fixed_across_months: boolean }
  nodata: { representation: string }
  months: FrameMonth[]
}

export type MapMode = 'prototype-frames' | 'contract'

export type FrameStatus =
  | { kind: 'idle' }
  | { kind: 'loading'; month: YearMonth }
  | { kind: 'ready'; month: YearMonth }
  | { kind: 'missing'; month: YearMonth; reason: string }
  | { kind: 'error'; month: YearMonth; message: string }

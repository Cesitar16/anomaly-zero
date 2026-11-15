/**
 * Tipos del contrato AZ-04 `0.1-draft` (docs/openapi-contract-v0.yaml, integrado en `dev`).
 *
 * Se escribieron a mano siguiendo los esquemas del OpenAPI, sin `any` y sin campos inventados.
 * No se confía solo en estos tipos: `test/contracts.test.ts` valida las fixtures contra los
 * esquemas reales del OpenAPI, y los ejemplos oficiales deben coincidir con los del YAML.
 *
 * Todo lo que NO viene del contrato (resultados de la capa de datos, estados de la pantalla)
 * está al final, bajo "Tipos propios de la interfaz".
 */

export type YearMonth = string // ^\d{4}-(0[1-9]|1[0-2])$

export interface Envelope {
  contract_version: '0.1-draft'
  /** `true` solo en fixtures. Las respuestas reales usan `false`. */
  synthetic: boolean
  generated_at: string
}

// --- Catálogo -------------------------------------------------------------------------------

export interface Region {
  region_id: string
  name: string
  geometry_version: string | null
  geometry_source: string | null
  crs: string | null
  area_km2: number | null
}

export interface RegionsResponse extends Envelope {
  regions: Region[]
}

export interface Source {
  agency: string
  distributor: string | null
  collection_id: string | null
  doi: string | null
  source_urls: string[]
  granule_ids: string[]
}

export interface MonthRange {
  start: YearMonth
  end: YearMonth
}

export interface InclusiveMonthRange extends MonthRange {
  end_inclusive: true
}

export type ProductAvailability = 'available' | 'partial' | 'unavailable'

export interface Product {
  product_id: string
  short_name: string
  product_version: string
  variable: string
  quantity: string
  unit: string
  availability: ProductAvailability
  source: Source
  current_dataset_id: string | null
  coverage: MonthRange | null
  quality: Quality | null
}

export interface ProductsResponse extends Envelope {
  region_id: string
  products: Product[]
}

// --- Calidad, cobertura y procedencia ---------------------------------------------------------

export interface Provenance {
  source_sha256: string[]
  source_updated_at: string | null
  retrieved_at: string | null
  snapshot_created_at: string | null
  manifest_version: string | null
  manifest_sha256: string | null
  original_file_count: number | null
}

export interface Temporal {
  frequency: 'monthly'
  calendar: string | null
  date_label: 'month_start'
}

export interface SpatialCoverage {
  evaluated_cells: number | null
  valid_cells: number | null
  intersection_area_km2: number | null
  valid_area_km2: number | null
  basin_area_km2: number | null
  valid_area_fraction_of_intersection: number | null
  valid_area_fraction_of_basin: number | null
}

export interface Coverage {
  expected_periods: number
  present_periods: number
  valid_periods: number
  missing_periods: YearMonth[]
  /** Opcional: el backend actual la omite siempre (observación O14 de FE-03). */
  spatial_coverage?: SpatialCoverage | null
}

/** Los cuatro atributos son de esquema libre (`{}`): pueden ser número, texto o `null`. */
export interface SourceMissingAttributes {
  fill_value: unknown
  missing_value: unknown
  scale_factor: unknown
  add_offset: unknown
}

export type VerificationState = 'unassessed' | 'basic_checks_only' | 'provider_qa_applied'

export type QualityCheckState = 'not_run' | 'passed' | 'failed' | 'partial'

export interface QualityCheck {
  check_id: string
  version: string | null
  applied: boolean
  state: QualityCheckState
  excluded_count: number | null
  exclusion_reasons: string[]
}

export interface Quality {
  source_flag_fields: string[]
  provider_flags_applied: boolean
  source_missing_attributes: SourceMissingAttributes
  finite_non_fill_filter_applied: boolean
  verification_state: VerificationState
  mask_applied: string | null
  qa_checks?: QualityCheck[]
  uninterpreted_provider_fields?: string[]
}

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

// --- Soporte espacial (oneOf discriminado por `support_type`) -----------------------------------

export interface PointReference {
  cell_id: string
  latitude: number | null
  longitude: number | null
}

export interface PointSampleSupport {
  support_type: 'point_sample'
  approval_state: 'not_assessed'
  method: null
  area_weighted: null
  weighting_reference: null
  mask_version: null
  point: PointReference
}

export interface DescriptiveMeanSupport {
  support_type: 'descriptive_mean'
  approval_state: 'descriptive_only'
  method: string
  cell_count: number
  area_weighted: boolean
  weighting_reference: string | null
  mask_version: string | null
}

export interface ApprovedRegionalSupport {
  support_type: 'regional_aggregate'
  approval_state: 'approved'
  method: string
  area_weighted: boolean
  weighting_reference: string | null
  mask_version: string
  approval_reference: string
}

export type SpatialAggregation =
  | PointSampleSupport
  | DescriptiveMeanSupport
  | ApprovedRegionalSupport

export interface Transformation {
  operation: string
  parameters: Record<string, unknown>
  input_unit: string | null
  output_unit: string | null
  code_version: string | null
}

// --- Serie ---------------------------------------------------------------------------------

export interface SeriesPoint {
  /** Primer día del mes: AAAA-MM-01. */
  date: string
  /** Cero es un valor válido; `null` es faltante. */
  value: number | null
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

export type DataState = 'available' | 'available_with_gaps' | 'no_data'

export interface SeriesResponse extends Envelope {
  // DatasetSnapshot
  dataset_id: string | null
  provenance: Provenance | null
  coverage: Coverage
  quality: Quality
  spatial_aggregation: SpatialAggregation | null
  transformations: Transformation[]
  // Propio de la serie
  data_state: DataState
  region: Region
  product: Product
  temporal: Temporal
  requested_coverage: InclusiveMonthRange
  available_coverage: MonthRange | null
  /** Opcional: el backend actual nunca lo envía. */
  raster_layers?: RasterLayer[]
  series: SeriesPoint[]
  message?: string
}

// --- Errores y análisis ----------------------------------------------------------------------

export type ErrorCode =
  | 'INVALID_PARAMETER'
  | 'PERIOD_OUT_OF_COVERAGE'
  | 'LIMIT_EXCEEDED'
  | 'RESOURCE_NOT_FOUND'
  | 'INSUFFICIENT_DATA'
  | 'ANALYSIS_METHOD_UNAVAILABLE'
  | 'SERVICE_UNAVAILABLE'
  | 'INTERNAL_ERROR'

export interface Metrics {
  slope: number | null
  slope_unit: string | null
  confidence_interval: [number, number] | null
  p_value: number | null
  significance: boolean | null
}

export interface UnavailableAnalysis {
  state: 'not_available'
  analysis_id: null
  dataset_id: string
  region_id: string
  product_id: string
  window: InclusiveMonthRange
  method: null
  metrics: Metrics
}

/** `additionalProperties: true`: el ejemplo oficial 422 trae `field` y `received`, que el esquema no declara (O5). */
export interface ErrorDetails {
  dataset_id?: string | null
  provider_status?: number | null
  analysis?: UnavailableAnalysis
  [extra: string]: unknown
}

export interface ApiErrorBody {
  code: ErrorCode
  message: string
  retryable: boolean
  request_id: string
  details: ErrorDetails | null
}

export interface ErrorResponse extends Envelope {
  error: ApiErrorBody
}

export interface CreateAnalysisRequest {
  dataset_id: string
  window: InclusiveMonthRange
}

export interface Method {
  name: string
  version: string | null
}

/** Solo se tipa lo necesario para no inventar nada: esta pantalla no muestra resultados de análisis (D5). */
export interface AnalysisResponse extends Envelope {
  analysis_id: string
  dataset_id: string
  region_id: string
  product_id: string
  status: 'pending' | 'complete'
  method: Method
  metrics: Metrics
  limitations: string[]
}

// --- Tipos propios de la interfaz (NO son parte del contrato) -----------------------------------

/** Una respuesta con sobre de error del contrato. */
export interface ApiFailure {
  kind: 'api'
  httpStatus: number
  body: ErrorResponse
}

/** La petición falló sin cuerpo utilizable (el contrato no define este caso; ver O13 de FE-03). */
export interface NetworkFailure {
  kind: 'network'
}

export type ExploreFailure = ApiFailure | NetworkFailure

export type ApiResult<T> = { ok: true; data: T } | { ok: false; failure: ExploreFailure }

/** Estado de una petición. No se reduce a un booleano `isLoading`. */
export type Remote<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; failure: ExploreFailure }

export interface SeriesQuery {
  regionId: string
  productId: string
  start: YearMonth
  end: YearMonth
}

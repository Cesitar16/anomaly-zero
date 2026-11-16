/**
 * Adaptador de datos de `/explore`. Es la ÚNICA puerta a los datos: ningún componente hace `fetch`.
 *
 * Hay dos implementaciones intercambiables:
 *  - `mockExploreApi`: respuestas sintéticas conformes al OpenAPI (modo por defecto de desarrollo y QA).
 *  - `httpExploreApi`: cliente HTTP compatible con el backend de `dev`. Está aislado y NO se usa por
 *    defecto: conectar la API real a la pantalla es una integración controlada que se aprueba aparte.
 *
 * Cada método devuelve un `ApiResult`: o los datos tipados, o un fallo. Un fallo es un sobre de error del
 * contrato (`kind: 'api'`) o una petición sin cuerpo utilizable (`kind: 'network'`). Un 503 o un 500 nunca
 * se disfrazan de "sin datos".
 */
import type { RasterResolver } from '../lib/rasterTarget'
import type { ContextGeometryOverlay } from '../lib/contextMap'
import type {
  AnalysisResponse,
  ApiResult,
  CreateAnalysisRequest,
  ErrorResponse,
  ProductsResponse,
  RegionsResponse,
  SeriesQuery,
  SeriesResponse,
} from '../types/contracts'

export interface ExploreCapabilities {
  /**
   * `true` solo si este adaptador puede pedir `POST /analyses`. El adaptador HTTP lo deja en `false`:
   * `/analyses` no existe en `dev` y no hay método estadístico aprobado (decisión D5 de FE-03).
   */
  analyses: boolean
  /** Cómo se dibuja una capa raster. En modo real no se dibuja ninguna (Gate M sin aprobar). */
  raster: RasterResolver
}

export interface ExploreApi {
  readonly mode: 'mock' | 'http'
  readonly capabilities: ExploreCapabilities
  listRegions(signal?: AbortSignal): Promise<ApiResult<RegionsResponse>>
  listProducts(regionId: string, signal?: AbortSignal): Promise<ApiResult<ProductsResponse>>
  getSeries(query: SeriesQuery, signal?: AbortSignal): Promise<ApiResult<SeriesResponse>>
  downloadSeriesCsv?(query: SeriesQuery, signal?: AbortSignal): Promise<ApiResult<Blob>>
  getContextGeometry?(regionId: string, signal?: AbortSignal): Promise<ApiResult<ContextGeometryOverlay>>
  createAnalysis(
    request: CreateAnalysisRequest,
    signal?: AbortSignal,
  ): Promise<ApiResult<AnalysisResponse>>
  getAnalysis(analysisId: string, signal?: AbortSignal): Promise<ApiResult<AnalysisResponse>>
}

// --- Guardas mínimas de forma (la validación completa contra el OpenAPI vive en las pruebas) ----------

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

export function isErrorResponse(value: unknown): value is ErrorResponse {
  if (!isRecord(value) || !isRecord(value.error)) return false
  const { code, message, retryable, request_id: requestId } = value.error
  return (
    typeof value.contract_version === 'string' &&
    typeof code === 'string' &&
    typeof message === 'string' &&
    typeof retryable === 'boolean' &&
    typeof requestId === 'string'
  )
}

export function isRegionsResponse(value: unknown): value is RegionsResponse {
  return isRecord(value) && typeof value.contract_version === 'string' && Array.isArray(value.regions)
}

export function isProductsResponse(value: unknown): value is ProductsResponse {
  return isRecord(value) && typeof value.contract_version === 'string' && Array.isArray(value.products)
}

const DATA_STATES = ['available', 'available_with_gaps', 'no_data']

export function isSeriesResponse(value: unknown): value is SeriesResponse {
  return (
    isRecord(value) &&
    typeof value.contract_version === 'string' &&
    typeof value.data_state === 'string' &&
    DATA_STATES.includes(value.data_state) &&
    Array.isArray(value.series) &&
    isRecord(value.region) &&
    isRecord(value.product) &&
    isRecord(value.coverage) &&
    isRecord(value.quality) &&
    isRecord(value.requested_coverage)
  )
}

export function isAnalysisResponse(value: unknown): value is AnalysisResponse {
  return (
    isRecord(value) &&
    typeof value.contract_version === 'string' &&
    typeof value.analysis_id === 'string' &&
    typeof value.status === 'string'
  )
}

export function isContextGeometryResponse(value: unknown): value is Record<string, unknown> & {
  type: 'FeatureCollection'
  synthetic: false
  features: Array<{ properties: { name: string }; geometry: { type: 'Polygon' | 'MultiPolygon'; coordinates: unknown[] } }>
  metadata: Record<string, unknown>
} {
  if (!isRecord(value) || value.type !== 'FeatureCollection' || value.synthetic !== false || !Array.isArray(value.features) || !isRecord(value.metadata)) return false
  const metadata = value.metadata
  if (
    metadata.region_id !== 'murray-darling-basin' ||
    metadata.geometry_use !== 'contextual_outline_only' || metadata.scientific_approval !== 'not_approved' ||
    typeof metadata.source_url !== 'string' || typeof metadata.source_item_url !== 'string' ||
    typeof metadata.license !== 'string' || typeof metadata.license_url !== 'string' ||
    typeof metadata.attribution !== 'string' || !/^[a-f\d]{64}$/i.test(String(metadata.artifact_sha256 ?? ''))
  ) return false
  return value.features.length > 0 && value.features.every((feature) => {
    if (!isRecord(feature) || !isRecord(feature.properties) || !isRecord(feature.geometry)) return false
    return feature.properties.region_id === 'murray-darling-basin' && typeof feature.properties.name === 'string' &&
      (feature.geometry.type === 'Polygon' || feature.geometry.type === 'MultiPolygon') &&
      Array.isArray(feature.geometry.coordinates)
  })
}

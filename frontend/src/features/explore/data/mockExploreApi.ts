/**
 * Servicio SIMULADO de `/explore`: devuelve fixtures sintéticas (`synthetic: true`) conformes al OpenAPI.
 * Es el modo predeterminado de desarrollo y QA. Nunca habla con la red ni con NASA.
 *
 * Reglas que respeta (para que la pantalla se pruebe como si fuera la API):
 *  - Solo P02 (IMERG) tiene serie, y solo para 2005-01 a 2005-03: un rango dentro de esa ventana devuelve
 *    los puntos del ejemplo oficial recortados, sin inventar un solo valor; fuera de ella, `422`.
 *  - Los demás productos responden `200 no_data`, como el backend de `dev` sin snapshot.
 *  - `createAnalysis` responde el `409 ANALYSIS_METHOD_UNAVAILABLE` del contrato. `getAnalysis` responde
 *    `404`: no existe ningún análisis.
 *
 * Los `scenario` fuerzan estados concretos para revisarlos (ver COPY.demo.options).
 */
import { monthCount, monthOfDate, monthRange, isYearMonth, MAX_MONTHS } from '../lib/months'
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
import { demoRasterLayers, demoRasterResolver } from './demoRaster'
import type { ExploreApi } from './exploreApi'
import {
  error404NotFound,
  error422LimitExceeded,
  error422PeriodOutOfCoverage,
  error500Internal,
  productsAll,
  regionsEmpty,
  regionsOne,
} from './fixtures/derived'
import {
  error409MethodUnavailable,
  error422InvalidParameter,
  error503SnapshotUnavailable,
  seriesNoData,
  seriesPointSample,
} from './fixtures/official'

export const MOCK_DATASET_ID = 'ds-synthetic-001'
const IMERG_COVERAGE = { start: '2005-01', end: '2005-03' } as const

export interface MockOptions {
  scenario?: string | null
  /** Demora simulada de cada respuesta, para que se vean los estados de carga. */
  delayMs?: number
}

/** Copia profunda: una fixture compartida nunca se muta por accidente. */
function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

function failure(httpStatus: number, body: ErrorResponse): ApiResult<never> {
  return { ok: false, failure: { kind: 'api', httpStatus, body: clone(body) } }
}

function success<T>(data: T): ApiResult<T> {
  return { ok: true, data: clone(data) }
}

export function createMockExploreApi(options: MockOptions = {}): ExploreApi {
  const { scenario = null, delayMs = 400 } = options

  const pause = (signal?: AbortSignal): Promise<void> =>
    delayMs <= 0 || signal?.aborted
      ? Promise.resolve()
      : new Promise((resolve) => window.setTimeout(resolve, delayMs))

  function seriesFor(query: SeriesQuery): ApiResult<SeriesResponse> {
    switch (scenario) {
      case 'error-503':
        return failure(503, error503SnapshotUnavailable)
      case 'error-500':
        return failure(500, error500Internal)
      case 'sin-red':
        return { ok: false, failure: { kind: 'network' } }
      case 'no-encontrado':
        return failure(404, error404NotFound)
    }

    if (query.regionId !== regionsOne.regions[0].region_id) return failure(404, error404NotFound)
    const product = productsAll.products.find((candidate) => candidate.product_id === query.productId)
    if (!product) return failure(404, error404NotFound)

    for (const field of ['start', 'end'] as const) {
      if (!isYearMonth(query[field])) {
        const body = clone(error422InvalidParameter)
        body.error.details = { field, received: query[field] }
        return failure(422, body)
      }
    }
    const count = monthCount(query.start, query.end)
    if (count < 1) {
      const body = clone(error422InvalidParameter)
      body.error.details = { field: 'start', received: query.start }
      return failure(422, body)
    }
    if (count > MAX_MONTHS) return failure(422, error422LimitExceeded)

    const months = monthRange(query.start, query.end)
    const requested = { start: query.start, end: query.end, end_inclusive: true } as const

    if (product.product_id !== seriesPointSample.product.product_id) {
      // Sin snapshot para este producto: 200 no_data (no es un error).
      const body = clone(seriesNoData)
      body.product = clone(product)
      body.requested_coverage = { ...requested }
      body.coverage = {
        expected_periods: count,
        present_periods: 0,
        valid_periods: 0,
        missing_periods: months,
      }
      return success(body)
    }

    if (query.start < IMERG_COVERAGE.start || query.end > IMERG_COVERAGE.end) {
      return failure(422, error422PeriodOutOfCoverage)
    }

    const body = clone(seriesPointSample)
    const series = body.series.filter((point) => months.includes(monthOfDate(point.date)))
    const missing = series.filter((point) => point.value === null).map((point) => monthOfDate(point.date))
    body.series = series
    body.requested_coverage = { ...requested }
    body.coverage = {
      expected_periods: count,
      present_periods: series.length,
      valid_periods: series.length - missing.length,
      missing_periods: missing,
    }
    body.data_state = missing.length > 0 ? 'available_with_gaps' : 'available'

    if (scenario === 'capas-mixtas' || scenario === 'capas-no-disponibles') {
      // Enero y marzo con capa; febrero declarado no disponible (E9 y E10). O todas no disponibles (E6).
      body.raster_layers = demoRasterLayers({
        datasetId: MOCK_DATASET_ID,
        months,
        availableMonths: scenario === 'capas-mixtas' ? ['2005-01', '2005-03'] : [],
        unit: body.product.unit,
      })
    }
    return success(body)
  }

  return {
    mode: 'mock',
    capabilities: { analyses: true, raster: demoRasterResolver },

    async listRegions(signal) {
      await pause(signal)
      return success<RegionsResponse>(scenario === 'catalogo-vacio' ? regionsEmpty : regionsOne)
    },

    async listProducts(regionId, signal) {
      await pause(signal)
      if (regionId !== regionsOne.regions[0].region_id) return failure(404, error404NotFound)
      return success<ProductsResponse>(productsAll)
    },

    async getSeries(query, signal) {
      await pause(signal)
      return seriesFor(query)
    },

    async createAnalysis(request: CreateAnalysisRequest, signal) {
      await pause(signal)
      if (request.dataset_id !== MOCK_DATASET_ID) return failure(404, error404NotFound)
      // El contrato responde 409: no hay método aprobado y no se crea ningún análisis.
      const body = clone(error409MethodUnavailable)
      const analysis = body.error.details?.analysis
      if (analysis) {
        analysis.dataset_id = request.dataset_id
        analysis.window = { ...request.window }
      }
      return failure(409, body)
    },

    async getAnalysis(_analysisId: string, signal) {
      await pause(signal)
      // No existe ningún análisis: la pantalla nunca consulta un identificador inventado.
      return failure(404, error404NotFound) as ApiResult<AnalysisResponse>
    },
  }
}

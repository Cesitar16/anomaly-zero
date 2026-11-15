/**
 * Cliente HTTP compatible con el backend de `dev` (`GET /api/v1/regions`, `/products`, `/series`).
 * Está AISLADO: no se usa salvo que se pida con `VITE_EXPLORE_API=http`. Conectar la API real a la
 * pantalla es una integración controlada que se aprueba aparte (ver la tarjeta FUL-119).
 *
 * Lo que respeta del backend real (docs/fe-03-explorer-ux.md, observaciones O13 y O14):
 *  - Una respuesta de error sin sobre del contrato (por ejemplo el `404 {"detail": "Not Found"}` de una
 *    ruta inexistente) se trata como "sin respuesta" (`network`), no como un código del contrato.
 *  - Los campos opcionales pueden faltar (`raster_layers`, `message`, `spatial_coverage`).
 *  - No llama a `/analyses`: no existe en `dev` y no hay método aprobado (`capabilities.analyses: false`).
 */
import type { ApiResult, CreateAnalysisRequest, SeriesQuery } from '../types/contracts'
import {
  isAnalysisResponse,
  isErrorResponse,
  isProductsResponse,
  isRegionsResponse,
  isSeriesResponse,
} from './exploreApi'
import type { ExploreApi } from './exploreApi'

export const DEFAULT_API_BASE = '/api/v1'

export function createHttpExploreApi(
  baseUrl: string = DEFAULT_API_BASE,
  fetchImpl: typeof fetch = (input, init) => fetch(input, init),
): ExploreApi {
  async function request<T>(
    path: string,
    init: RequestInit,
    isExpected: (body: unknown) => body is T,
    signal?: AbortSignal,
  ): Promise<ApiResult<T>> {
    let response: Response
    let body: unknown
    try {
      response = await fetchImpl(`${baseUrl}${path}`, {
        ...init,
        signal,
        headers: { Accept: 'application/json', ...init.headers },
      })
      body = await response.json()
    } catch {
      // Red caída, petición cancelada o cuerpo que no es JSON.
      return { ok: false, failure: { kind: 'network' } }
    }
    if (response.ok) {
      return isExpected(body)
        ? { ok: true, data: body }
        : { ok: false, failure: { kind: 'network' } }
    }
    return isErrorResponse(body)
      ? { ok: false, failure: { kind: 'api', httpStatus: response.status, body } }
      : { ok: false, failure: { kind: 'network' } }
  }

  const get = { method: 'GET' } satisfies RequestInit

  return {
    mode: 'http',
    capabilities: { analyses: false, raster: () => null },

    listRegions: (signal) => request('/regions', get, isRegionsResponse, signal),

    listProducts: (regionId, signal) =>
      request(
        `/products?${new URLSearchParams({ region_id: regionId })}`,
        get,
        isProductsResponse,
        signal,
      ),

    getSeries: (query: SeriesQuery, signal) =>
      request(
        `/series?${new URLSearchParams({
          region_id: query.regionId,
          product_id: query.productId,
          start: query.start,
          end: query.end,
          frequency: 'monthly',
        })}`,
        get,
        isSeriesResponse,
        signal,
      ),

    createAnalysis: (body: CreateAnalysisRequest, signal) =>
      request(
        '/analyses',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        },
        isAnalysisResponse,
        signal,
      ),

    getAnalysis: (analysisId, signal) =>
      request(`/analyses/${encodeURIComponent(analysisId)}`, get, isAnalysisResponse, signal),
  }
}

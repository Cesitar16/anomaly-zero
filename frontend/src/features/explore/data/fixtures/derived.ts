/**
 * Fixtures DERIVADAS (no son ejemplos oficiales del OpenAPI). Todas son `synthetic: true`.
 * - Los errores 404, 500 y 422 (cobertura y límite) se derivaron de las respuestas reales observadas en
 *   `dev` (docs/fe-03/ejemplos-observados/): mismo `code`, mismo mensaje, `details: null`.
 * - La región sintética REG01 es la del ejemplo oficial `pointSample`.
 * - P01 se derivó del catálogo del backend (nombre, versión y unidad de MERRA-2); P02 y P03 son los
 *   productos de los ejemplos oficiales. Ninguna fixture trae observaciones NASA.
 * `test/contracts.test.ts` valida todas contra los esquemas del OpenAPI.
 */
import type { ErrorResponse, Product, RegionsResponse, ProductsResponse } from '../../types/contracts'
import { seriesNoData, seriesPointSample } from './official'

const GENERATED_AT = '2026-11-15T00:00:00Z'

export const regionsOne: RegionsResponse = {
  contract_version: '0.1-draft',
  synthetic: true,
  generated_at: GENERATED_AT,
  regions: [seriesPointSample.region],
}

/** Ejemplo A de la tarjeta FE-04: catálogo sin regiones publicadas (HTTP 200). */
export const regionsEmpty: RegionsResponse = {
  contract_version: '0.1-draft',
  synthetic: true,
  generated_at: GENERATED_AT,
  regions: [],
}

export const productP01: Product = {
  "product_id": "P01",
  "short_name": "M2TMNXSLV",
  "product_version": "5.12.4",
  "variable": "T2M",
  "quantity": "air_temperature_2m",
  "unit": "K",
  "availability": "unavailable",
  "source": {
    "agency": "NASA GMAO",
    "distributor": "GES DISC",
    "collection_id": "C1276812859-GES_DISC",
    "doi": "10.5067/AP1B0BA5PD2K",
    "source_urls": [],
    "granule_ids": []
  },
  "current_dataset_id": null,
  "coverage": null,
  "quality": null
}

export const productsAll: ProductsResponse = {
  contract_version: '0.1-draft',
  synthetic: true,
  generated_at: GENERATED_AT,
  region_id: seriesPointSample.region.region_id,
  products: [productP01, seriesPointSample.product, seriesNoData.product],
}

export const error404NotFound: ErrorResponse = {
  "contract_version": "0.1-draft",
  "synthetic": true,
  "generated_at": "2026-11-15T00:00:00Z",
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "La región o el producto solicitado no existe.",
    "retryable": false,
    "request_id": "fixture-fe04-404",
    "details": null
  }
}

export const error500Internal: ErrorResponse = {
  "contract_version": "0.1-draft",
  "synthetic": true,
  "generated_at": "2026-11-15T00:00:00Z",
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Ocurrió un error interno.",
    "retryable": false,
    "request_id": "fixture-fe04-500",
    "details": null
  }
}

export const error422LimitExceeded: ErrorResponse = {
  "contract_version": "0.1-draft",
  "synthetic": true,
  "generated_at": "2026-11-15T00:00:00Z",
  "error": {
    "code": "LIMIT_EXCEEDED",
    "message": "La consulta excede el máximo de 240 meses.",
    "retryable": false,
    "request_id": "fixture-fe04-422-limit",
    "details": null
  }
}

export const error422PeriodOutOfCoverage: ErrorResponse = {
  "contract_version": "0.1-draft",
  "synthetic": true,
  "generated_at": "2026-11-15T00:00:00Z",
  "error": {
    "code": "PERIOD_OUT_OF_COVERAGE",
    "message": "El período solicitado excede la cobertura publicada.",
    "retryable": false,
    "request_id": "fixture-fe04-422-coverage",
    "details": null
  }
}

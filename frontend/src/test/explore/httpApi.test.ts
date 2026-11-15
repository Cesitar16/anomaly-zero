import { describe, expect, it, vi } from 'vitest'
import { createHttpExploreApi } from '../../features/explore/data/httpExploreApi'
import { observed } from './helpers'

function respond(body: unknown, status = 200): Response {
  return new Response(typeof body === 'string' ? body : JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function apiWith(handler: (url: string, init?: RequestInit) => Response) {
  const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => Promise.resolve(handler(String(input), init)))
  return { api: createHttpExploreApi('/api/v1', fetchMock as unknown as typeof fetch), fetchMock }
}

const query = { regionId: 'r', productId: 'p', start: '2005-01', end: '2005-03' }

describe('Cliente HTTP (compatible con el backend integrado en dev)', () => {
  it('no se activa solo: declara que no soporta análisis ni capas raster', () => {
    const { api } = apiWith(() => respond({}))
    expect(api.mode).toBe('http')
    expect(api.capabilities.analyses).toBe(false)
    const layer = { dataset_id: 'd', date: '2005-01', layer_type: 'value', unit: null, state: 'available', format: 'image/png', tile_template: '/x.png' } as const
    expect(api.capabilities.raster(layer)).toBeNull()
  })

  it('lee las respuestas reales observadas (catálogo, productos y no_data)', async () => {
    const { api } = apiWith((url) =>
      url.includes('/regions')
        ? respond(observed('regions_dev'))
        : url.includes('/products')
          ? respond(observed('products_dev_sin_snapshot'))
          : respond(observed('series_no_data_dev')),
    )
    const regions = await api.listRegions()
    const products = await api.listProducts('murray-darling-basin')
    const series = await api.getSeries({ regionId: 'murray-darling-basin', productId: 'P02', start: '2005-01', end: '2005-03' })
    expect(regions.ok && regions.data.regions[0].region_id).toBe('murray-darling-basin')
    expect(products.ok && products.data.products.every((product) => product.availability === 'unavailable')).toBe(true)
    expect(series.ok && series.data.data_state).toBe('no_data')
    // El backend real omite estos campos opcionales: el cliente no los exige.
    expect(series.ok && series.data.raster_layers).toBeUndefined()
    expect(series.ok && series.data.synthetic).toBe(false)
  })

  it('arma las URL con region_id, product_id, start, end y frequency=monthly', async () => {
    const { api, fetchMock } = apiWith(() => respond(observed('series_no_data_dev')))
    await api.getSeries({ regionId: 'murray-darling-basin', productId: 'P02', start: '2005-01', end: '2005-03' })
    const url = new URL(String(fetchMock.mock.calls[0][0]), 'http://localhost')
    expect(url.pathname).toBe('/api/v1/series')
    expect(Object.fromEntries(url.searchParams)).toEqual({
      region_id: 'murray-darling-basin',
      product_id: 'P02',
      start: '2005-01',
      end: '2005-03',
      frequency: 'monthly',
    })
  })

  it.each([
    ['error_404_producto_dev', 404, 'RESOURCE_NOT_FOUND'],
    ['error_422_limit_exceeded_dev', 422, 'LIMIT_EXCEEDED'],
    ['error_422_periodo_fuera_de_cobertura_dev', 422, 'PERIOD_OUT_OF_COVERAGE'],
    ['error_500_dev', 500, 'INTERNAL_ERROR'],
    ['error_503_dev', 503, 'SERVICE_UNAVAILABLE'],
  ])('un error del contrato (%s) llega con su código y su estado HTTP', async (file, status, code) => {
    const { api } = apiWith(() => respond(observed(file), status))
    const result = await api.getSeries(query)
    if (result.ok || result.failure.kind !== 'api') throw new Error('debía ser un error del contrato')
    expect(result.failure.httpStatus).toBe(status)
    expect(result.failure.body.error.code).toBe(code)
  })

  it('el 503 es reintentable y el 500 no', async () => {
    const r503 = await apiWith(() => respond(observed('error_503_dev'), 503)).api.getSeries(query)
    const r500 = await apiWith(() => respond(observed('error_500_dev'), 500)).api.getSeries(query)
    expect(!r503.ok && r503.failure.kind === 'api' && r503.failure.body.error.retryable).toBe(true)
    expect(!r500.ok && r500.failure.kind === 'api' && r500.failure.body.error.retryable).toBe(false)
  })

  it('una ruta inexistente ({"detail":"Not Found"}) NO se confunde con un código del contrato', async () => {
    const { api } = apiWith(() => respond(observed('ruta_inexistente_dev'), 404))
    const result = await api.listRegions()
    expect(!result.ok && result.failure.kind).toBe('network')
  })

  it('red caída, cuerpo que no es JSON y forma inesperada son "sin respuesta"', async () => {
    const down = createHttpExploreApi('/api/v1', (() => Promise.reject(new TypeError('Failed to fetch'))) as typeof fetch)
    const notJson = apiWith(() => respond('<html>502</html>', 502)).api
    const wrongShape = apiWith(() => respond({ hola: 'mundo' })).api
    for (const result of [await down.listRegions(), await notJson.listRegions(), await wrongShape.listRegions()]) {
      expect(!result.ok && result.failure.kind).toBe('network')
    }
  })
})

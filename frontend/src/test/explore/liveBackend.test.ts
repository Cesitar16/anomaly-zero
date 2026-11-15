import { describe, expect, it } from 'vitest'
import { createHttpExploreApi } from '../../features/explore/data/httpExploreApi'
import { validateAgainst } from './helpers'

/**
 * Integración real frontend ↔ backend. Se OMITE si no hay un FastAPI en ejecución.
 *
 *   EXPLORE_LIVE_API=http://127.0.0.1:8000/api/v1 npm test --prefix frontend -- liveBackend
 *
 * Usa el MISMO cliente HTTP tipado que la pantalla y valida cada respuesta contra el OpenAPI real. No exige
 * que haya snapshot: con snapshot comprueba la serie puntual; sin snapshot comprueba el `no_data` honesto.
 * Las comprobaciones con datos reales (`synthetic: false`) se informan por separado y nunca se versionan.
 */
const base = process.env.EXPLORE_LIVE_API

describe.skipIf(!base)('Cliente HTTP contra FastAPI en ejecución', () => {
  const api = createHttpExploreApi(base ?? '')
  const range = { start: '2005-01', end: '2005-12' }

  it('GET /regions cumple RegionsResponse y publica la cuenca Murray-Darling', async () => {
    const result = await api.listRegions()
    expect(result.ok).toBe(true)
    if (!result.ok) return
    expect(validateAgainst('RegionsResponse', result.data)).toEqual([])
    expect(result.data.regions.map((region) => region.region_id)).toContain('murray-darling-basin')
  })

  it('GET /products cumple ProductsResponse; IMERG (P02) y los demás siguen su disponibilidad real', async () => {
    const result = await api.listProducts('murray-darling-basin')
    expect(result.ok).toBe(true)
    if (!result.ok) return
    expect(validateAgainst('ProductsResponse', result.data)).toEqual([])
    const ids = result.data.products.map((product) => product.product_id)
    expect(ids).toEqual(expect.arrayContaining(['P01', 'P02', 'P03']))
    // MERRA-2 y GLDAS no se publican como series reales aunque existan archivos NASA descargados.
    for (const product of result.data.products.filter((item) => item.product_id !== 'P02')) {
      expect(product.availability).toBe('unavailable')
    }
  })

  it('GET /series cumple SeriesResponse y conserva cero, nulo, unidad y soporte puntual', async () => {
    const result = await api.getSeries({ regionId: 'murray-darling-basin', productId: 'P02', ...range })
    expect(result.ok).toBe(true)
    if (!result.ok) return
    expect(validateAgainst('SeriesResponse', result.data)).toEqual([])
    const body = result.data
    expect(body.product.unit).toBe('mm/hr')
    if (body.data_state === 'no_data') {
      // Sin snapshot: ausencia honesta, nada inventado.
      expect(body.series).toEqual([])
      return
    }
    expect(body.spatial_aggregation?.support_type).toBe('point_sample')
    expect(body.series.length).toBeGreaterThan(0)
    for (const point of body.series) {
      expect(point.value === null || typeof point.value === 'number').toBe(true)
      // `null` y 0 son cosas distintas: un hueco nunca llega como número.
      if (point.value === null) expect(point.quality.state).not.toBe('unassessed')
    }
  })

  it('GET /series con una región desconocida responde 404 con el sobre de error del contrato', async () => {
    const result = await api.getSeries({ regionId: 'no-existe', productId: 'P02', ...range })
    expect(result.ok).toBe(false)
    if (result.ok || result.failure.kind !== 'api') throw new Error('se esperaba un error de la API')
    expect(result.failure.httpStatus).toBe(404)
    expect(validateAgainst('ErrorResponse', result.failure.body)).toEqual([])
    expect(result.failure.body.error.code).toBe('RESOURCE_NOT_FOUND')
  })

  it('GET /series con el rango invertido responde 422 con el sobre de error del contrato', async () => {
    const result = await api.getSeries({ regionId: 'murray-darling-basin', productId: 'P02', start: '2005-12', end: '2005-01' })
    expect(result.ok).toBe(false)
    if (result.ok || result.failure.kind !== 'api') throw new Error('se esperaba un error de la API')
    expect(result.failure.httpStatus).toBe(422)
    expect(validateAgainst('ErrorResponse', result.failure.body)).toEqual([])
  })

  it('el cliente no declara análisis ni capas raster y nunca llama a /analyses', async () => {
    expect(api.capabilities.analyses).toBe(false)
    expect(api.capabilities.raster({ dataset_id: 'd', date: '2005-01', layer_type: 'value', unit: null, state: 'available', format: null, tile_template: null })).toBeNull()
  })
})

import { describe, expect, it } from 'vitest'
import { createMockExploreApi } from '../../features/explore/data/mockExploreApi'
import {
  error404NotFound,
  error422LimitExceeded,
  error422PeriodOutOfCoverage,
  error500Internal,
  productsAll,
  regionsEmpty,
  regionsOne,
} from '../../features/explore/data/fixtures/derived'
import {
  error409MethodUnavailable,
  error422InvalidParameter,
  error503SnapshotUnavailable,
  seriesNoData,
  seriesPointSample,
} from '../../features/explore/data/fixtures/official'
import { observed, openApi, validateAgainst } from './helpers'

function example(responsePath: string, name: string): unknown {
  const responses = openApi.paths as Record<string, { get: { responses: Record<string, { content: Record<string, { examples: Record<string, { value: unknown }> }> }> } }>
  return responses[responsePath].get.responses['200'].content['application/json'].examples[name].value
}

describe('Fixtures oficiales: idénticas a los ejemplos del OpenAPI', () => {
  it('seriesPointSample coincide con el ejemplo `pointSample` de GET /series', () => {
    expect(seriesPointSample).toEqual(example('/series', 'pointSample'))
  })

  it('seriesNoData coincide con el ejemplo `noData` de GET /series', () => {
    expect(seriesNoData).toEqual(example('/series', 'noData'))
  })

  it('los errores oficiales coinciden con los ejemplos de components.responses', () => {
    const responses = openApi.components.responses as Record<string, { content: Record<string, { examples: Record<string, { value: unknown }> }> }>
    const pick = (name: string, key: string) => responses[name].content['application/json'].examples[key].value
    expect(error422InvalidParameter).toEqual(pick('InvalidRequest', 'invalidParameters'))
    expect(error503SnapshotUnavailable).toEqual(pick('ServiceUnavailable', 'snapshotUnavailable'))
    expect(error409MethodUnavailable).toEqual(pick('AnalysisUnavailable', 'methodUnavailable'))
  })
})

describe('Fixtures: validan contra los esquemas del OpenAPI', () => {
  const cases: Array<[string, string, unknown]> = [
    ['SeriesResponse', 'seriesPointSample', seriesPointSample],
    ['SeriesResponse', 'seriesNoData', seriesNoData],
    ['RegionsResponse', 'regionsOne', regionsOne],
    ['RegionsResponse', 'regionsEmpty', regionsEmpty],
    ['ProductsResponse', 'productsAll', productsAll],
    ['ErrorResponse', 'error404NotFound', error404NotFound],
    ['ErrorResponse', 'error500Internal', error500Internal],
    ['ErrorResponse', 'error422LimitExceeded', error422LimitExceeded],
    ['ErrorResponse', 'error422PeriodOutOfCoverage', error422PeriodOutOfCoverage],
    ['ErrorResponse', 'error422InvalidParameter', error422InvalidParameter],
    ['ErrorResponse', 'error503SnapshotUnavailable', error503SnapshotUnavailable],
    ['ErrorResponse', 'error409MethodUnavailable', error409MethodUnavailable],
  ]

  it.each(cases)('%s: %s', (schema, _name, value) => {
    expect(validateAgainst(schema, value)).toEqual([])
  })

  it('el validador de verdad detecta un incumplimiento (control negativo)', () => {
    const broken = { ...seriesPointSample, data_state: 'casi_completo' }
    expect(validateAgainst('SeriesResponse', broken).length).toBeGreaterThan(0)
  })

  it('todas las fixtures son sintéticas y ninguna se hace pasar por una observación real', () => {
    for (const [, name, value] of cases) {
      expect((value as { synthetic: boolean }).synthetic, name).toBe(true)
    }
  })
})

describe('Respuestas reales observadas en `dev`: validan contra el mismo contrato', () => {
  it.each([
    ['RegionsResponse', 'regions_dev'],
    ['ProductsResponse', 'products_dev_sin_snapshot'],
    ['SeriesResponse', 'series_no_data_dev'],
    ['ErrorResponse', 'error_404_producto_dev'],
    ['ErrorResponse', 'error_422_parametro_dev'],
    ['ErrorResponse', 'error_503_dev'],
  ])('%s: %s', (schema, file) => {
    expect(validateAgainst(schema, observed(file))).toEqual([])
  })
})

describe('Servicio simulado: todo lo que responde cumple el contrato', () => {
  const api = createMockExploreApi({ delayMs: 0 })

  it('catálogo, productos y series (con y sin datos)', async () => {
    const regions = await api.listRegions()
    const products = await api.listProducts('REG01')
    const complete = await api.getSeries({ regionId: 'REG01', productId: 'P02', start: '2005-01', end: '2005-03' })
    const partial = await api.getSeries({ regionId: 'REG01', productId: 'P02', start: '2005-02', end: '2005-03' })
    const empty = await api.getSeries({ regionId: 'REG01', productId: 'P03', start: '2005-01', end: '2005-12' })
    const unavailable = await api.getSeries({ regionId: 'REG01', productId: 'P01', start: '2005-01', end: '2005-02' })

    const checks: Array<[string, unknown]> = [
      ['RegionsResponse', regions.ok ? regions.data : null],
      ['ProductsResponse', products.ok ? products.data : null],
      ['SeriesResponse', complete.ok ? complete.data : null],
      ['SeriesResponse', partial.ok ? partial.data : null],
      ['SeriesResponse', empty.ok ? empty.data : null],
      ['SeriesResponse', unavailable.ok ? unavailable.data : null],
    ]
    for (const [schema, value] of checks) {
      expect(value, schema).not.toBeNull()
      expect(validateAgainst(schema, value)).toEqual([])
    }
  })

  it('cada error cumple el esquema de error', async () => {
    const failures = await Promise.all([
      api.getSeries({ regionId: 'NOPE', productId: 'P02', start: '2005-01', end: '2005-02' }),
      api.getSeries({ regionId: 'REG01', productId: 'P02', start: '2005-01', end: '2999-12' }),
      api.getSeries({ regionId: 'REG01', productId: 'P02', start: '2005-01', end: '2006-13' }),
      api.getSeries({ regionId: 'REG01', productId: 'P02', start: '1990-01', end: '2000-12' }),
      api.createAnalysis({ dataset_id: 'ds-synthetic-001', window: { start: '2005-01', end: '2005-03', end_inclusive: true } }),
    ])
    for (const result of failures) {
      expect(result.ok).toBe(false)
      if (!result.ok && result.failure.kind === 'api') {
        expect(validateAgainst('ErrorResponse', result.failure.body)).toEqual([])
      }
    }
  })

  it('las capas de los escenarios de mapa cumplen el esquema RasterLayer', async () => {
    for (const scenario of ['capas-mixtas', 'capas-no-disponibles']) {
      const result = await createMockExploreApi({ delayMs: 0, scenario }).getSeries({
        regionId: 'REG01',
        productId: 'P02',
        start: '2005-01',
        end: '2005-03',
      })
      expect(result.ok).toBe(true)
      if (!result.ok) continue
      expect(result.data.raster_layers).toHaveLength(3)
      expect(validateAgainst('SeriesResponse', result.data)).toEqual([])
      for (const layer of result.data.raster_layers ?? []) expect(validateAgainst('RasterLayer', layer)).toEqual([])
    }
  })
})

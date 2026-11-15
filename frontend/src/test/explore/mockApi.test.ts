import { describe, expect, it } from 'vitest'
import { createMockExploreApi } from '../../features/explore/data/mockExploreApi'
import type { ApiResult } from '../../features/explore/types/contracts'

const api = createMockExploreApi({ delayMs: 0 })
const base = { regionId: 'REG01', productId: 'P02' }

function failureCode<T>(result: ApiResult<T>): { status: number; code: string } {
  if (result.ok || result.failure.kind !== 'api') throw new Error('Se esperaba un error del contrato')
  return { status: result.failure.httpStatus, code: result.failure.body.error.code }
}

describe('Servicio simulado', () => {
  it('es el predeterminado y permite simular el 409 de análisis', () => {
    expect(api.mode).toBe('mock')
    expect(api.capabilities.analyses).toBe(true)
  })

  it('serie completa: conserva el cero y el faltante del ejemplo oficial', async () => {
    const result = await api.getSeries({ ...base, start: '2005-01', end: '2005-03' })
    expect(result.ok).toBe(true)
    if (!result.ok) return
    expect(result.data.synthetic).toBe(true)
    expect(result.data.data_state).toBe('available_with_gaps')
    expect(result.data.series.map((point) => point.value)).toContain(0)
    expect(result.data.series.map((point) => point.value)).toContain(null)
    expect(result.data.spatial_aggregation?.support_type).toBe('point_sample')
    expect(result.data.raster_layers).toBeUndefined()
  })

  it('un subrango recorta la serie y recalcula la cobertura sin inventar valores', async () => {
    const full = await api.getSeries({ ...base, start: '2005-01', end: '2005-03' })
    const part = await api.getSeries({ ...base, start: '2005-02', end: '2005-03' })
    if (!full.ok || !part.ok) throw new Error('debía responder 200')
    expect(part.data.series).toEqual(full.data.series.slice(1))
    expect(part.data.coverage.expected_periods).toBe(2)
    expect(part.data.requested_coverage).toEqual({ start: '2005-02', end: '2005-03', end_inclusive: true })
  })

  it('un rango sin faltantes se declara `available` y no `available_with_gaps`', async () => {
    const full = await api.getSeries({ ...base, start: '2005-01', end: '2005-03' })
    if (!full.ok) throw new Error('debía responder 200')
    const withValue = full.data.series.find((point) => point.value !== null)!.date.slice(0, 7)
    const single = await api.getSeries({ ...base, start: withValue, end: withValue })
    expect(single.ok && single.data.data_state).toBe('available')
  })

  it('los productos sin snapshot responden 200 no_data (no es un error)', async () => {
    for (const productId of ['P01', 'P03']) {
      const result = await api.getSeries({ regionId: 'REG01', productId, start: '2005-01', end: '2005-12' })
      expect(result.ok, productId).toBe(true)
      if (!result.ok) continue
      expect(result.data.data_state).toBe('no_data')
      expect(result.data.series).toEqual([])
      expect(result.data.coverage.missing_periods).toHaveLength(12)
      expect(result.data.provenance).toBeNull()
    }
  })

  it('errores del contrato con su código y estado HTTP', async () => {
    expect(failureCode(await api.getSeries({ ...base, start: '2005-01', end: '2999-12' }))).toEqual({ status: 422, code: 'LIMIT_EXCEEDED' })
    expect(failureCode(await api.getSeries({ ...base, start: '1990-01', end: '1990-03' }))).toEqual({ status: 422, code: 'PERIOD_OUT_OF_COVERAGE' })
    expect(failureCode(await api.getSeries({ ...base, start: '2005-01', end: '2006-13' }))).toEqual({ status: 422, code: 'INVALID_PARAMETER' })
    expect(failureCode(await api.getSeries({ regionId: 'NOPE', productId: 'P02', start: '2005-01', end: '2005-03' }))).toEqual({ status: 404, code: 'RESOURCE_NOT_FOUND' })
    expect(failureCode(await api.listProducts('NOPE'))).toEqual({ status: 404, code: 'RESOURCE_NOT_FOUND' })
  })

  it('INVALID_PARAMETER indica qué campo falló', async () => {
    const result = await api.getSeries({ ...base, start: '2005-01', end: 'abril' })
    if (result.ok || result.failure.kind !== 'api') throw new Error('debía fallar')
    expect(result.failure.body.error.details?.field).toBe('end')
  })

  it.each([
    ['error-503', 503, 'SERVICE_UNAVAILABLE'],
    ['error-500', 500, 'INTERNAL_ERROR'],
    ['no-encontrado', 404, 'RESOURCE_NOT_FOUND'],
  ])('escenario %s', async (scenario, status, code) => {
    const scenic = createMockExploreApi({ delayMs: 0, scenario })
    expect(failureCode(await scenic.getSeries({ ...base, start: '2005-01', end: '2005-03' }))).toEqual({ status, code })
  })

  it('escenario sin-red: sin respuesta utilizable', async () => {
    const scenic = createMockExploreApi({ delayMs: 0, scenario: 'sin-red' })
    const result = await scenic.getSeries({ ...base, start: '2005-01', end: '2005-03' })
    expect(!result.ok && result.failure.kind).toBe('network')
  })

  it('escenario catalogo-vacio: 200 con regiones vacías', async () => {
    const result = await createMockExploreApi({ delayMs: 0, scenario: 'catalogo-vacio' }).listRegions()
    expect(result.ok && result.data.regions).toEqual([])
  })

  it('escenario capas-mixtas declara capa en enero y marzo y no en febrero', async () => {
    const scenic = createMockExploreApi({ delayMs: 0, scenario: 'capas-mixtas' })
    const result = await scenic.getSeries({ ...base, start: '2005-01', end: '2005-03' })
    if (!result.ok) throw new Error('debía responder 200')
    expect(result.data.raster_layers?.map((layer) => [layer.date, layer.state])).toEqual([
      ['2005-01', 'available'],
      ['2005-02', 'unavailable'],
      ['2005-03', 'available'],
    ])
    expect(result.data.raster_layers?.find((layer) => layer.date === '2005-02')?.tile_template).toBeNull()
  })

  it('POST /analyses responde 409 ANALYSIS_METHOD_UNAVAILABLE y NO crea ningún análisis', async () => {
    const result = await api.createAnalysis({
      dataset_id: 'ds-synthetic-001',
      window: { start: '2005-01', end: '2005-03', end_inclusive: true },
    })
    if (result.ok || result.failure.kind !== 'api') throw new Error('debía fallar con 409')
    expect(result.failure.httpStatus).toBe(409)
    expect(result.failure.body.error.code).toBe('ANALYSIS_METHOD_UNAVAILABLE')
    const analysis = result.failure.body.error.details?.analysis
    expect(analysis?.analysis_id).toBeNull()
    expect(analysis?.method).toBeNull()
    expect(analysis?.state).toBe('not_available')
    expect(JSON.stringify(result.failure.body)).not.toMatch(/"(slope|p_value|confidence_interval)":\s*-?\d/)
  })

  it('GET /analyses/{id} responde 404: no existe ningún análisis', async () => {
    expect(failureCode(await api.getAnalysis('cualquiera'))).toEqual({ status: 404, code: 'RESOURCE_NOT_FOUND' })
  })

  it('cada respuesta es una copia: mutarla no contamina las siguientes', async () => {
    const first = await api.getSeries({ ...base, start: '2005-01', end: '2005-03' })
    if (!first.ok) throw new Error('debía responder 200')
    first.data.series[0].value = 999
    const second = await api.getSeries({ ...base, start: '2005-01', end: '2005-03' })
    expect(second.ok && second.data.series[0].value).not.toBe(999)
  })
})

import { describe, expect, it } from 'vitest'
import { describePoint, describeSeries, missingMonths, toChartPoints, yAxisMax, yDomain } from '../../features/explore/lib/chartModel'
import { buildParams, queryKey, readUrl } from '../../features/explore/lib/exploreUrl'
import { formatLooseValue, formatValue, orNotInformed } from '../../features/explore/lib/format'
import { MAX_MONTHS, isYearMonth, monthCount, monthRange, validateRange } from '../../features/explore/lib/months'
import { monthsWithLayer, resolveMapTarget } from '../../features/explore/lib/rasterTarget'
import type { RasterLayer } from '../../features/explore/types/contracts'
import { seriesPointSample } from '../../features/explore/data/fixtures/official'

describe('months', () => {
  it('reconoce AAAA-MM y rechaza lo demás', () => {
    expect(isYearMonth('2005-01')).toBe(true)
    expect(isYearMonth('2005-12')).toBe(true)
    for (const bad of ['2005-13', '2005-00', '2005-1', '05-01', '2005/01', '2005-01-01', '', ' 2005-01']) {
      expect(isYearMonth(bad), bad).toBe(false)
    }
  })

  it('el rango es inclusivo y cruza años', () => {
    expect(monthCount('2005-01', '2005-03')).toBe(3)
    expect(monthRange('2005-11', '2006-02')).toEqual(['2005-11', '2005-12', '2006-01', '2006-02'])
    expect(monthRange('2005-05', '2005-05')).toEqual(['2005-05'])
  })

  it('valida orden y máximo de 240 meses', () => {
    expect(validateRange('2005-01', '2005-03')).toEqual({})
    expect(validateRange('2005-01', '2024-12')).toEqual({}) // exactamente 240
    expect(monthCount('2005-01', '2024-12')).toBe(MAX_MONTHS)
    expect(validateRange('2005-01', '2025-01').end).toMatch(/240/)
    expect(validateRange('2005-03', '2005-01').start).toMatch(/posterior/)
    expect(validateRange('2005-1', '2005-03').start).toMatch(/AAAA-MM/)
    expect(validateRange('', '').end).toMatch(/AAAA-MM/)
  })
})

describe('format', () => {
  it('conserva el cero y nunca escribe "null"', () => {
    expect(formatValue(0)).toBe('0')
    expect(formatValue(1.5)).toBe('1,5')
    expect(orNotInformed(null)).toBe('No informado')
    expect(orNotInformed(undefined)).toBe('No informado')
    expect(orNotInformed('')).toBe('No informado')
    expect(orNotInformed(0)).toBe('0')
    expect(formatLooseValue(null)).toBe('No informado')
    expect(formatLooseValue(0)).toBe('0')
    expect(formatLooseValue(-9999)).toBe('-9.999')
  })
})

describe('chartModel', () => {
  const points = toChartPoints(seriesPointSample.series)

  it('conserva exactamente el cero y el null del contrato', () => {
    expect(points.map((point) => point.value)).toEqual(seriesPointSample.series.map((point) => point.value))
    expect(points.some((point) => point.value === 0)).toBe(true)
    expect(points.some((point) => point.value === null)).toBe(true)
    expect(missingMonths(points)).toEqual(seriesPointSample.coverage.missing_periods)
  })

  it('describe cero y hueco con palabras distintas', () => {
    const zero = points.find((point) => point.value === 0)!
    const gap = points.find((point) => point.value === null)!
    expect(describePoint(zero, 'mm/hr')).toContain('cero válido')
    expect(describePoint(gap, 'mm/hr')).toContain('sin dato')
    expect(describePoint(gap, 'mm/hr')).not.toMatch(/\b0\b/)
  })

  it('la descripción del gráfico detalla pocos meses y resume muchos', () => {
    expect(describeSeries(points, 'mm/hr')).toContain('3 meses')
    expect(describeSeries([], 'mm/hr')).toMatch(/Sin meses/)
    const many = Array.from({ length: 20 }, (_, index) => ({
      ...points[0],
      month: `2005-${String(index + 1).padStart(2, '0')}`,
      value: index === 3 ? null : 1,
    }))
    expect(describeSeries(many, 'mm/hr')).toMatch(/19 con valor y 1 sin dato/)
  })

  it('el eje de una tasa parte de cero; el de otras magnitudes no se fuerza', () => {
    expect(yDomain(points, 'mm/hr')[0]).toBe(0)
    expect(yDomain(points, 'K')).toEqual(['auto', 'auto'])
    expect(yAxisMax([])).toBeGreaterThan(0)
  })
})

describe('rasterTarget', () => {
  const months = ['2005-01', '2005-02', '2005-03']
  const layer = (date: string, over: Partial<RasterLayer> = {}): RasterLayer => ({
    dataset_id: 'ds',
    date,
    layer_type: 'value',
    unit: 'mm/hr',
    state: 'available',
    format: 'image/png',
    tile_template: `/x/${date}.png`,
    ...over,
  })
  const drawAll = (item: RasterLayer) => ({ url: item.tile_template ?? '', bbox: { west: 0, south: 0, east: 1, north: 1 } })

  it('sin capas (lo que publica el backend hoy): ausente, y no se llama al resolvedor', () => {
    let calls = 0
    const resolver = () => {
      calls += 1
      return null
    }
    expect(resolveMapTarget({ layers: undefined, months, month: '2005-01', resolver })).toEqual({ kind: 'absent' })
    expect(resolveMapTarget({ layers: [], months, month: '2005-01', resolver })).toEqual({ kind: 'absent' })
    expect(calls).toBe(0)
  })

  it('una capa "disponible" sin formato o sin plantilla se trata como no disponible', () => {
    const layers = [layer('2005-01', { format: null }), layer('2005-02', { tile_template: null })]
    expect(monthsWithLayer(layers, months).size).toBe(0)
    expect(resolveMapTarget({ layers, months, month: '2005-01', resolver: drawAll })).toEqual({ kind: 'absent' })
  })

  it('un mes sin capa se declara ausente y no reutiliza otro mes', () => {
    const layers = [
      layer('2005-01'),
      layer('2005-02', { state: 'unavailable', format: null, tile_template: null }),
      layer('2005-03'),
    ]
    expect(resolveMapTarget({ layers, months, month: '2005-02', resolver: drawAll })).toEqual({ kind: 'month-absent' })
    const target = resolveMapTarget({ layers, months, month: '2005-03', resolver: drawAll })
    expect(target.kind === 'frame' && target.raster.url).toBe('/x/2005-03.png')
  })

  it('una capa declarada que el resolvedor no sabe leer es "no dibujable" (modo real)', () => {
    const target = resolveMapTarget({ layers: [layer('2005-01')], months, month: '2005-01', resolver: () => null })
    expect(target.kind).toBe('not-drawable')
  })

  it('solo cuentan las capas de valor (no anomalía, pendiente ni significancia)', () => {
    const layers = [layer('2005-01', { layer_type: 'slope' }), layer('2005-02', { layer_type: 'significance' })]
    expect(monthsWithLayer(layers, months).size).toBe(0)
  })
})

describe('exploreUrl', () => {
  it('una dirección completa y válida produce la consulta', () => {
    const state = readUrl(new URLSearchParams('region=REG01&product=P02&start=2005-01&end=2005-03&month=2005-02&demo=error-503'))
    expect(state.query).toEqual({ regionId: 'REG01', productId: 'P02', start: '2005-01', end: '2005-03' })
    expect(state.month).toBe('2005-02')
    expect(state.scenario).toBe('error-503')
    expect(queryKey(state.query)).toBe('REG01|P02|2005-01|2005-03')
  })

  it('una dirección incompleta rellena el formulario pero no consulta', () => {
    const state = readUrl(new URLSearchParams('region=REG01&product=P02'))
    expect(state.query).toBeNull()
    expect(state.draft).toEqual({ regionId: 'REG01', productId: 'P02', start: '', end: '' })
  })

  it('un rango inválido escrito a mano no consulta y explica el error', () => {
    const state = readUrl(new URLSearchParams('region=REG01&product=P02&start=2005-13&end=2005-03'))
    expect(state.query).toBeNull()
    expect(state.rangeErrors.start).toMatch(/AAAA-MM/)
    expect(readUrl(new URLSearchParams('region=R&product=P&start=2005-01&end=2030-01')).rangeErrors.end).toMatch(/240/)
  })

  it('ignora un month con formato inválido', () => {
    expect(readUrl(new URLSearchParams('month=enero')).month).toBeNull()
  })

  it('buildParams ida y vuelta', () => {
    const query = { regionId: 'REG01', productId: 'P02', start: '2005-01', end: '2005-03' }
    const params = buildParams({ query, month: null, scenario: 'capas-mixtas' })
    expect(readUrl(params).query).toEqual(query)
    expect(params.get('demo')).toBe('capas-mixtas')
    expect(params.has('month')).toBe(false)
  })
})

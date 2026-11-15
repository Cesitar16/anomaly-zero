import { SERIES } from '../data/fixtures'
import { describePoint, missingMonths, toChartPoints, yAxisMax } from '../lib/chartModel'

const points = toChartPoints(SERIES)
const byMonth = (month: string) => points.find((point) => point.month === month)!

describe('chartModel', () => {
  it('conserva 12 meses y el mismo periodo que la línea de tiempo', () => {
    expect(points).toHaveLength(12)
    expect(points[0].month).toBe('2005-01')
    expect(points[11].month).toBe('2005-12')
  })

  it('un cero legítimo sigue siendo 0, no null', () => {
    expect(byMonth('2005-03').value).toBe(0)
    expect(describePoint(byMonth('2005-03'), 'v', 'u')).toContain('cero, valor válido')
  })

  it('un faltante sigue siendo null y nunca se convierte en cero', () => {
    const missing = byMonth('2005-04')
    expect(missing.value).toBeNull()
    expect(missing.qualityState).toBe('missing')
    expect(describePoint(missing, 'v', 'u')).toContain('sin dato (provider_fill_value)')
    expect(describePoint(missing, 'v', 'u')).not.toMatch(/\b0\b/)
  })

  it('solo cuenta como faltantes los null, no los ceros', () => {
    expect(missingMonths(points)).toEqual(['2005-04'])
  })

  it('un punto de calidad desconocida mantiene su valor y lo declara', () => {
    const unknown = byMonth('2005-09')
    expect(unknown.value).not.toBeNull()
    expect(describePoint(unknown, 'v', 'u')).toContain('calidad desconocida')
    expect(unknown.flags).toEqual([{ name: 'synthetic_flag', value: 2 }])
  })

  it('el eje Y parte de cero y el máximo ignora los null', () => {
    expect(yAxisMax(points)).toBe(0.7)
    expect(yAxisMax([])).toBe(1)
  })
})

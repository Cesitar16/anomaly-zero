import { isYearMonth, monthLabel, monthRange, monthStart } from '../lib/months'

describe('months', () => {
  it('genera el rango inclusivo de 12 meses', () => {
    const months = monthRange('2005-01', '2005-12')
    expect(months).toHaveLength(12)
    expect(months[0]).toBe('2005-01')
    expect(months.at(-1)).toBe('2005-12')
  })

  it('cruza el cambio de año y respeta end_inclusive', () => {
    expect(monthRange('2005-11', '2006-02')).toEqual(['2005-11', '2005-12', '2006-01', '2006-02'])
    expect(monthRange('2005-05', '2005-05')).toEqual(['2005-05'])
  })

  it('rechaza rangos invertidos o con formato inválido (como el 422 del contrato)', () => {
    expect(() => monthRange('2005-06', '2005-05')).toThrow(RangeError)
    expect(() => monthRange('2005-13', '2005-14')).toThrow(RangeError)
  })

  it('valida el patrón YYYY-MM del contrato', () => {
    expect(isYearMonth('2005-01')).toBe(true)
    expect(isYearMonth('2005-13')).toBe(false)
    expect(isYearMonth('2005-1')).toBe(false)
  })

  it('etiqueta el mes con su primer día, como pide el contrato', () => {
    expect(monthStart('2005-04')).toBe('2005-04-01')
    expect(monthLabel('2005-04')).toBe('abril de 2005')
  })
})

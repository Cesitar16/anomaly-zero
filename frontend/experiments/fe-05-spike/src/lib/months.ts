import type { YearMonth } from '../types'

const YEAR_MONTH = /^\d{4}-(0[1-9]|1[0-2])$/

export function isYearMonth(value: string): value is YearMonth {
  return YEAR_MONTH.test(value)
}

/** Meses consecutivos [start, end] inclusivos, como pide el contrato (`end_inclusive: true`). */
export function monthRange(start: YearMonth, end: YearMonth): YearMonth[] {
  if (!isYearMonth(start) || !isYearMonth(end) || start > end) {
    throw new RangeError(`Rango mensual inválido: ${start}..${end}`)
  }
  const months: YearMonth[] = []
  let [year, month] = start.split('-').map(Number)
  const [endYear, endMonth] = end.split('-').map(Number)
  while (year < endYear || (year === endYear && month <= endMonth)) {
    months.push(`${year}-${String(month).padStart(2, '0')}`)
    month += 1
    if (month > 12) {
      month = 1
      year += 1
    }
  }
  return months
}

/** El contrato etiqueta cada mes con su primer día: YYYY-MM-01. */
export function monthStart(month: YearMonth): string {
  return `${month}-01`
}

export function monthLabel(month: YearMonth): string {
  return new Intl.DateTimeFormat('es-CL', { month: 'long', year: 'numeric', timeZone: 'UTC' }).format(
    new Date(`${monthStart(month)}T00:00:00Z`),
  )
}

import { COPY } from '../content/exploreCopy'
import type { YearMonth } from '../types/contracts'

/** Máximo de meses por consulta (`GET /series`, OpenAPI). */
export const MAX_MONTHS = 240

const YEAR_MONTH = /^\d{4}-(0[1-9]|1[0-2])$/

export function isYearMonth(value: string): value is YearMonth {
  return YEAR_MONTH.test(value)
}

function toIndex(month: YearMonth): number {
  const [year, monthNumber] = month.split('-').map(Number)
  return year * 12 + (monthNumber - 1)
}

/** Cantidad de meses del rango inclusivo [start, end]. */
export function monthCount(start: YearMonth, end: YearMonth): number {
  return toIndex(end) - toIndex(start) + 1
}

/** Meses consecutivos [start, end] inclusivos, como pide el contrato (`end_inclusive: true`). */
export function monthRange(start: YearMonth, end: YearMonth): YearMonth[] {
  const count = monthCount(start, end)
  if (!isYearMonth(start) || !isYearMonth(end) || count < 1) {
    throw new RangeError(`Rango mensual inválido: ${start}..${end}`)
  }
  const first = toIndex(start)
  return Array.from({ length: count }, (_, offset) => {
    const index = first + offset
    return `${Math.floor(index / 12)}-${String((index % 12) + 1).padStart(2, '0')}`
  })
}

/** El contrato etiqueta cada mes con su primer día: AAAA-MM-01. */
export function monthStart(month: YearMonth): string {
  return `${month}-01`
}

export function monthOfDate(date: string): YearMonth {
  return date.slice(0, 7)
}

export function monthLabel(month: YearMonth): string {
  return new Intl.DateTimeFormat('es-CL', { month: 'long', year: 'numeric', timeZone: 'UTC' }).format(
    new Date(`${monthStart(month)}T00:00:00Z`),
  )
}

export type RangeErrors = Partial<Record<'start' | 'end', string>>

/** Validación local del rango: formato, orden y máximo de 240 meses. No consulta nada. */
export function validateRange(start: string, end: string): RangeErrors {
  const errors: RangeErrors = {}
  if (!isYearMonth(start)) errors.start = COPY.filters.invalidMonth
  if (!isYearMonth(end)) errors.end = COPY.filters.invalidMonth
  if (errors.start || errors.end) return errors
  const count = monthCount(start as YearMonth, end as YearMonth)
  if (count < 1) errors.start = COPY.filters.startAfterEnd
  else if (count > MAX_MONTHS) errors.end = COPY.filters.tooLong
  return errors
}

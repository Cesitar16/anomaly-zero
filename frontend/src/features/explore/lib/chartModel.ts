import { COPY } from '../content/exploreCopy'
import type { PointQualityState, ProviderFlag, SeriesPoint, YearMonth } from '../types/contracts'
import { formatValue } from './format'
import { monthOfDate } from './months'

/**
 * Punto listo para graficar. `value` conserva EXACTAMENTE lo que dice el contrato:
 * el cero sigue siendo 0 y `null` sigue siendo `null` (nunca se convierte, promedia ni interpola).
 */
export interface ChartPoint {
  month: YearMonth
  date: string
  value: number | null
  qualityState: PointQualityState
  missingReason: string | null
  flags: ProviderFlag[]
}

export function toChartPoints(series: SeriesPoint[]): ChartPoint[] {
  return series.map((point) => ({
    month: monthOfDate(point.date),
    date: point.date,
    value: point.value,
    qualityState: point.quality.state,
    missingReason: point.quality.missing_reason,
    flags: point.quality.provider_flags,
  }))
}

export function missingMonths(points: ChartPoint[]): YearMonth[] {
  return points.filter((point) => point.value === null).map((point) => point.month)
}

export function qualityText(state: PointQualityState): string {
  return COPY.quality.point[state]
}

/** Texto único (tooltip, tabla, descripción accesible) para un punto. */
export function describePoint(point: ChartPoint, unit: string): string {
  if (point.value === null) {
    const reason = point.missingReason ? ` (${point.missingReason})` : ''
    return `${point.month}: ${COPY.state.gap.toLowerCase()}${reason}`
  }
  const zero = point.value === 0 ? ' (cero válido)' : ''
  return `${point.month}: ${formatValue(point.value)} ${unit}${zero}`
}

/**
 * Párrafo que describe el gráfico con palabras, generado desde los datos. Es la descripción accesible
 * (`aria-describedby`) y no sustituye a la tabla. Con muchos meses se resume; el detalle vive en la tabla.
 */
export function describeSeries(points: ChartPoint[], unit: string): string {
  if (points.length === 0) return COPY.state.noMonths
  const first = points[0].month
  const last = points[points.length - 1].month
  const missing = missingMonths(points).length
  const head = `${points.length} ${points.length === 1 ? 'mes' : 'meses'}, de ${first} a ${last}.`
  if (points.length > 12) {
    return `${head} ${points.length - missing} con valor y ${missing} sin dato. La tabla siguiente tiene el detalle mes por mes.`
  }
  return `${head} ${points.map((point) => `${describePoint(point, unit)}.`).join(' ')}`
}

/** Eje Y desde cero hasta el máximo redondeado hacia arriba; `null` no cuenta como dato. */
export function yAxisMax(points: ChartPoint[]): number {
  const values = points.flatMap((point) => (point.value === null ? [] : [point.value]))
  const max = values.length > 0 ? Math.max(...values) : 1
  return Math.max(0.1, Math.ceil(max * 10) / 10)
}

/**
 * Dominio del eje Y. Una tasa (mm/hr) parte de cero: así un mes con cero se ve como cero. Para otras
 * magnitudes (por ejemplo kelvin) no se fuerza el cero, porque aplastaría la variación sin aportar nada.
 */
export function yDomain(points: ChartPoint[], unit: string): [number | 'auto', number | 'auto'] {
  return unit === 'mm/hr' ? [0, yAxisMax(points)] : ['auto', 'auto']
}

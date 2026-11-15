import type { PointQualityState, ProviderFlag, SeriesPoint, YearMonth } from '../types'

/**
 * Punto listo para graficar. `value` conserva EXACTAMENTE lo que dice el contrato:
 * cero sigue siendo 0 y null sigue siendo null (nunca se convierte, promedia ni interpola).
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
    month: point.date.slice(0, 7),
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

export function formatValue(value: number): string {
  return value.toLocaleString('es-CL', { maximumFractionDigits: 3 })
}

const QUALITY_TEXT: Record<PointQualityState, string> = {
  unassessed: 'calidad no evaluada',
  missing: 'sin dato',
  unknown: 'calidad desconocida',
}

export function qualityText(state: PointQualityState): string {
  return QUALITY_TEXT[state]
}

/** Texto único (tooltip, tabla, descripción accesible) para un punto. */
export function describePoint(point: ChartPoint, variable: string, unit: string): string {
  if (point.value === null) {
    const reason = point.missingReason ? ` (${point.missingReason})` : ''
    return `${point.month} · ${variable}: sin dato${reason}`
  }
  const zero = point.value === 0 ? ' (cero, valor válido)' : ''
  return `${point.month} · ${variable}: ${formatValue(point.value)} ${unit}${zero} · ${qualityText(point.qualityState)}`
}

/** Eje Y desde cero hasta el máximo redondeado hacia arriba; null no cuenta como dato. */
export function yAxisMax(points: ChartPoint[]): number {
  const values = points.flatMap((point) => (point.value === null ? [] : [point.value]))
  const max = values.length > 0 ? Math.max(...values) : 1
  return Math.max(0.1, Math.ceil(max * 10) / 10)
}

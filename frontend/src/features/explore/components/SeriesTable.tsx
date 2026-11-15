import { COPY } from '../content/exploreCopy'
import { formatValue } from '../lib/format'
import { qualityText } from '../lib/chartModel'
import type { ChartPoint } from '../lib/chartModel'
import type { YearMonth } from '../types/contracts'

export interface SeriesTableProps {
  points: ChartPoint[]
  unit: string
  selectedMonth: YearMonth | null
}

/**
 * Tabla accesible con los mismos valores del gráfico. Es la alternativa textual del gráfico, no un adorno:
 * conserva cero (se escribe «0 (cero válido)») y null (se escribe «Sin dato», con su motivo si lo hay).
 */
export function SeriesTable({ points, unit, selectedMonth }: SeriesTableProps) {
  if (points.length === 0) return <p>{COPY.state.noMonths}</p>
  return (
    <div className="explore-table-wrap" role="region" aria-label={COPY.chart.tableCaption} tabIndex={0}>
      <table className="explore-table">
        <caption className="sr-only">{COPY.chart.tableCaption}</caption>
        <thead>
          <tr>
            <th scope="col">Mes</th>
            <th scope="col">
              Valor (<span className="explore-mono">{unit}</span>)
            </th>
            <th scope="col">Calidad</th>
          </tr>
        </thead>
        <tbody>
          {points.map((point) => (
            <tr key={point.month} aria-current={point.month === selectedMonth ? 'true' : undefined}>
              <th scope="row" className="explore-mono">
                {point.month}
              </th>
              <td>
                {point.value === null ? (
                  <>
                    {COPY.state.gap}
                    {point.missingReason ? <span className="explore-muted"> ({point.missingReason})</span> : null}
                  </>
                ) : point.value === 0 ? (
                  COPY.state.zero
                ) : (
                  formatValue(point.value)
                )}
              </td>
              <td>
                {qualityText(point.qualityState)}
                {point.flags.length > 0 ? (
                  <span className="explore-muted">
                    {' '}
                    ({point.flags.map((flag) => `${flag.name}: ${String(flag.value)}`).join(', ')})
                  </span>
                ) : null}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

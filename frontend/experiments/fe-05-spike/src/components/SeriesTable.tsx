import { formatValue, qualityText } from '../lib/chartModel'
import type { ChartPoint } from '../lib/chartModel'

/** Alternativa tabular del gráfico: misma información, sin depender de canvas, color ni hover. */
export function SeriesTable({ points, variable, unit, selectedMonth }: { points: ChartPoint[]; variable: string; unit: string; selectedMonth: string }) {
  return (
    <div className="table-wrap">
      <table className="series-table">
        <caption>
          {variable} por mes ({unit}). Datos sintéticos.
        </caption>
        <thead>
          <tr>
            <th scope="col">Mes</th>
            <th scope="col">Valor ({unit})</th>
            <th scope="col">Calidad</th>
            <th scope="col">Motivo / flags</th>
          </tr>
        </thead>
        <tbody>
          {points.map((point) => (
            <tr key={point.month} aria-current={point.month === selectedMonth ? 'true' : undefined}>
              <th scope="row">{point.month}</th>
              <td>{point.value === null ? <em>sin dato</em> : formatValue(point.value)}</td>
              <td>{qualityText(point.qualityState)}</td>
              <td>
                {point.missingReason ?? '-'}
                {point.flags.length > 0 && ` · ${point.flags.map((flag) => `${flag.name}=${String(flag.value)}`).join(', ')}`}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

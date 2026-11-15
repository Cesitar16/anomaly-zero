import { useId } from 'react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { TooltipContentProps } from 'recharts'
import { COPY, quantityLabel } from '../content/exploreCopy'
import { describePoint, describeSeries, missingMonths, yDomain } from '../lib/chartModel'
import type { ChartPoint } from '../lib/chartModel'
import type { YearMonth } from '../types/contracts'

export interface TimeSeriesChartProps {
  points: ChartPoint[]
  quantity: string
  unit: string
  selectedMonth: YearMonth | null
  onSelectMonth(month: YearMonth): void
}

// Recharts no entrega payload cuando el valor es null: el mes sin dato quedaría en silencio. Por eso el
// tooltip busca el punto por su etiqueta (el mes) y anuncia explícitamente "sin dato".
function PointTooltip({
  active,
  label,
  points,
  unit,
}: Partial<TooltipContentProps> & { points: ChartPoint[]; unit: string }) {
  if (!active || label === undefined) return null
  const point = points.find((candidate) => candidate.month === String(label))
  if (!point) return null
  return <div className="explore-tooltip">{describePoint(point, unit)}</div>
}

/**
 * Serie mensual. Cero se dibuja en 0; `null` deja un hueco (sin interpolar ni conectar) marcado «sin dato».
 * El gráfico es una imagen con descripción textual; su equivalente accesible es la tabla de debajo.
 */
export function TimeSeriesChart({ points, quantity, unit, selectedMonth, onSelectMonth }: TimeSeriesChartProps) {
  const titleId = useId()
  const descriptionId = useId()
  const gaps = missingMonths(points)
  const gapStripWidth = Math.max(3, Math.min(28, Math.floor(280 / Math.max(points.length, 1))))
  return (
    <figure className="explore-chart">
      <figcaption>
        <h3 id={titleId} className="explore-chart__title">
          {COPY.chart.title}: {quantityLabel(quantity)} (<span className="explore-mono">{unit}</span>)
        </h3>
        <p className="explore-chart__note">{COPY.chart.note}</p>
      </figcaption>
      <p id={descriptionId} className="sr-only">
        {describeSeries(points, unit)}
      </p>
      {/* La imagen es el lienzo; título y descripción textual la acompañan. La tabla es su equivalente. */}
      <div className="explore-chart__canvas" role="img" aria-labelledby={titleId} aria-describedby={descriptionId}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={points}
            margin={{ top: 12, right: 16, bottom: 4, left: 4 }}
            accessibilityLayer={false}
            onClick={(state) => {
              const label = state?.activeLabel
              if (label !== undefined && label !== null) onSelectMonth(String(label))
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-line)" />
            <XAxis dataKey="month" tick={{ fontSize: 11 }} minTickGap={16} padding={{ left: 24, right: 24 }} />
            <YAxis
              domain={yDomain(points, unit)}
              tick={{ fontSize: 11 }}
              width={48}
              label={{ value: unit, angle: -90, position: 'insideLeft', fontSize: 11 }}
            />
            <Tooltip content={(props) => <PointTooltip {...props} points={points} unit={unit} />} />
            {/* Franja ámbar por cada mes sin dato. El eje es de categorías, así que la franja es una línea gruesa. */}
            {gaps.map((month) => (
              <ReferenceLine
                key={month}
                x={month}
                stroke="var(--color-accent-ink)"
                strokeOpacity={0.18}
                strokeWidth={gapStripWidth}
                ifOverflow="visible"
              />
            ))}
            {selectedMonth !== null && (
              <ReferenceLine x={selectedMonth} stroke="var(--color-accent-ink)" strokeDasharray="4 3" />
            )}
            {/* connectNulls={false}: null deja un hueco. Cero es un valor y se dibuja en 0. */}
            <Line
              type="linear"
              dataKey="value"
              stroke="var(--color-primary)"
              strokeWidth={2}
              connectNulls={false}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      {gaps.length > 0 && (
        <p className="explore-chart__note">
          Las franjas ámbar marcan meses sin dato ({gaps.join(', ')}). No se rellenan ni se interpolan.
        </p>
      )}
    </figure>
  )
}

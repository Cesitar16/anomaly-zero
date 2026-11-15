import { Brush, CartesianGrid, Line, LineChart, ReferenceArea, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { TooltipContentProps } from 'recharts'
import { describePoint, missingMonths, yAxisMax } from '../lib/chartModel'
import type { ChartPoint } from '../lib/chartModel'
import type { SeriesChartProps } from './SeriesChartEcharts'

// Recharts omite el payload de una serie cuando el valor es null, así que el mes sin dato
// no traería ningún dato en `payload`. Por eso se busca el punto por su etiqueta (el mes):
// un hueco debe anunciarse como "sin dato", no quedar en silencio. Además Recharts oculta el
// contenedor (visibility: hidden) cuando no hay punto activo, y eso lo saca del árbol de
// accesibilidad; por eso se fuerza visible y el contenido decide si muestra algo.
function PointTooltip({ active, label, points, variable, unit }: Partial<TooltipContentProps> & { points: ChartPoint[]; variable: string; unit: string }) {
  if (!active || label === undefined) return null
  const point = points.find((candidate) => candidate.month === String(label))
  if (!point) return null
  return (
    <div className="chart-tooltip" role="status">
      {describePoint(point, variable, unit)}
    </div>
  )
}

export function SeriesChartRecharts({ points, variable, unit, selectedMonth, onSelectMonth }: SeriesChartProps) {
  return (
    <div
      className="chart"
      role="group"
      aria-label={`Gráfico de ${variable} por mes (${unit}). Datos sintéticos. Hay una tabla equivalente debajo.`}
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={points}
          margin={{ top: 16, right: 16, bottom: 8, left: 8 }}
          accessibilityLayer
          onClick={(state) => {
            const label = state?.activeLabel
            if (label !== undefined && label !== null) onSelectMonth(String(label))
          }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="month" tick={{ fontSize: 11 }} />
          <YAxis domain={[0, yAxisMax(points)]} tick={{ fontSize: 11 }} label={{ value: unit, angle: -90, position: 'insideLeft', fontSize: 11 }} />
          <Tooltip wrapperStyle={{ visibility: 'visible' }} content={(props) => <PointTooltip {...props} points={points} variable={variable} unit={unit} />} />
          {missingMonths(points).map((month) => (
            <ReferenceArea key={month} x1={month} x2={month} fill="#b42318" fillOpacity={0.1} label={{ value: 'sin dato', fontSize: 11, fill: '#7a1a12' }} />
          ))}
          <ReferenceLine x={selectedMonth} stroke="#b42318" strokeDasharray="4 3" />
          {/* connectNulls={false}: un valor null deja un hueco. Cero se dibuja como un punto en 0. */}
          <Line type="linear" dataKey="value" name={variable} stroke="#0b5c63" strokeWidth={2} connectNulls={false} dot={{ r: 4 }} isAnimationActive={false} />
          <Brush dataKey="month" height={22} stroke="#0b5c63" travellerWidth={10} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

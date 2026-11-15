import { LineChart } from 'echarts/charts'
import { AriaComponent, DataZoomComponent, GridComponent, MarkAreaComponent, MarkLineComponent, TooltipComponent } from 'echarts/components'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { useEffect, useRef } from 'react'
import { describePoint, missingMonths, yAxisMax } from '../lib/chartModel'
import type { ChartPoint } from '../lib/chartModel'

// Importación modular: solo lo que usa el gráfico (ver measure/ para el costo frente a la importación completa).
echarts.use([LineChart, GridComponent, TooltipComponent, DataZoomComponent, MarkLineComponent, MarkAreaComponent, AriaComponent, CanvasRenderer])

export interface SeriesChartProps {
  points: ChartPoint[]
  variable: string
  unit: string
  selectedMonth: string
  onSelectMonth: (month: string) => void
}

const escapeHtml = (text: string) => text.replace(/[&<>"']/g, (char) => `&#${char.charCodeAt(0)};`)

export function SeriesChartEcharts({ points, variable, unit, selectedMonth, onSelectMonth }: SeriesChartProps) {
  const container = useRef<HTMLDivElement>(null)
  const chart = useRef<echarts.ECharts | null>(null)
  const onSelectRef = useRef(onSelectMonth)
  useEffect(() => {
    onSelectRef.current = onSelectMonth
  }, [onSelectMonth])

  useEffect(() => {
    if (!container.current) return
    const instance = echarts.init(container.current, undefined, { renderer: 'canvas' })
    chart.current = instance
    instance.on('click', (params) => {
      const month = (params as { name?: string }).name
      if (month) onSelectRef.current(month)
    })
    const observer = new ResizeObserver(() => instance.resize())
    observer.observe(container.current)
    return () => {
      observer.disconnect()
      instance.dispose()
      chart.current = null
    }
  }, [])

  useEffect(() => {
    const byMonth = new Map(points.map((point) => [point.month, point]))
    chart.current?.setOption({
      animation: false,
      aria: { enabled: true, label: { description: `Gráfico de línea mensual de ${variable} en ${unit}. Datos sintéticos de demostración. Los meses sin dato aparecen como huecos y no se unen.` } },
      grid: { left: 52, right: 16, top: 44, bottom: 64 },
      tooltip: {
        trigger: 'axis',
        confine: true,
        formatter: (raw: unknown) => {
          const first = (Array.isArray(raw) ? raw[0] : raw) as { name?: string }
          const point = first?.name ? byMonth.get(first.name) : undefined
          return point ? escapeHtml(describePoint(point, variable, unit)) : ''
        },
      },
      xAxis: { type: 'category', data: points.map((point) => point.month), boundaryGap: true, name: 'Mes', nameLocation: 'middle', nameGap: 28 },
      yAxis: { type: 'value', min: 0, max: yAxisMax(points), name: unit, nameGap: 14, nameTextStyle: { align: 'left' } },
      dataZoom: [{ type: 'inside' }, { type: 'slider', height: 18, bottom: 6 }],
      series: [
        {
          type: 'line',
          name: variable,
          data: points.map((point) => point.value), // null se deja como null: ECharts abre un hueco (connectNulls por defecto es false)
          connectNulls: false,
          showSymbol: true,
          symbolSize: 8,
          markLine: {
            silent: true,
            symbol: 'none',
            lineStyle: { type: 'dashed', color: '#b42318' },
            label: { formatter: 'mes seleccionado', position: 'insideEndTop' },
            data: [{ xAxis: selectedMonth }],
          },
          markArea: {
            silent: true,
            itemStyle: { color: 'rgba(180, 35, 24, 0.10)' },
            label: { show: true, formatter: 'sin dato', position: 'insideTop', color: '#7a1a12' },
            data: missingMonths(points).map((month) => [{ xAxis: month }, { xAxis: month }]),
          },
        },
      ],
    })
  }, [points, variable, unit, selectedMonth])

  return <div ref={container} className="chart" role="img" aria-label={`Gráfico de ${variable} por mes (${unit}). Datos sintéticos. Hay una tabla equivalente debajo.`} />
}

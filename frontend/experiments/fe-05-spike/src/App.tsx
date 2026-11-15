import { useMemo, useState } from 'react'
import { ContractPanel } from './components/ContractPanel'
import { MapPanel } from './components/MapPanel'
import { MonthTimeline } from './components/MonthTimeline'
import { ProvenancePanel } from './components/ProvenancePanel'
import { RasterLegend } from './components/RasterLegend'
import { SeriesChartEcharts } from './components/SeriesChartEcharts'
import { SeriesChartRecharts } from './components/SeriesChartRecharts'
import { SeriesTable } from './components/SeriesTable'
import { SyntheticBanner } from './components/SyntheticBanner'
import { FRAME_MANIFEST } from './data/frames'
import { RASTER_LAYERS, SERIES, SERIES_MONTHS, SYNTHETIC_PRODUCT } from './data/fixtures'
import { toChartPoints } from './lib/chartModel'
import type { FrameStatus, ImageVariant, MapMode, YearMonth } from './types'

export function App() {
  const [selectedMonth, setSelectedMonth] = useState<YearMonth>('2005-01')
  const [isPlaying, setPlaying] = useState(false)
  const [mode, setMode] = useState<MapMode>('prototype-frames')
  const [variant, setVariant] = useState<ImageVariant>('mercator')
  const [status, setStatus] = useState<FrameStatus>({ kind: 'idle' })

  const points = useMemo(() => toChartPoints(SERIES), [])
  const timelineMonths = useMemo(
    () =>
      SERIES_MONTHS.map((month) => ({
        month,
        // En modo contrato ningún mes tiene capa renderizable; en modo prototipo, solo los que traen frame.
        hasFrame: mode === 'prototype-frames' && FRAME_MANIFEST.months.some((item) => item.date === month && item.frame !== null),
      })),
    [mode],
  )

  return (
    <>
      <SyntheticBanner />
      <main className="spike">
        <header className="spike__header">
          <p className="eyebrow">FE-05 · FUL-121 · spike descartable</p>
          <h1>Mapa mensual y gráfico, con datos sintéticos</h1>
          <p>
            Evalúa MapLibre, ECharts y Recharts con meses de 2005 ficticios: tres con capa, uno ausente a propósito y el resto sin capa. La
            elección final de stack es de César.
          </p>
        </header>

        <div className="spike__grid">
          <section className="spike__map" aria-labelledby="map-title">
            <h2 id="map-title">Mapa del mes seleccionado</h2>
            <MapPanel
              month={selectedMonth}
              mode={mode}
              variant={variant}
              manifest={FRAME_MANIFEST}
              rasterLayers={RASTER_LAYERS}
              onStatusChange={setStatus}
            />
            <MonthTimeline
              months={timelineMonths}
              selectedMonth={selectedMonth}
              onSelectMonth={setSelectedMonth}
              isPlaying={isPlaying}
              onPlayingChange={setPlaying}
            />
            <RasterLegend scale={FRAME_MANIFEST.scale} />
          </section>

          <section className="spike__side" aria-labelledby="chart-title">
            <h2 id="chart-title">Serie mensual (sintética)</h2>
            <p className="note">
              Cero real en 2005-03, faltante en 2005-04 (hueco, no cero) y calidad desconocida en 2005-09. Haz clic en un punto para cambiar de mes.
            </p>
            <h3>ECharts</h3>
            <SeriesChartEcharts points={points} variable={SYNTHETIC_PRODUCT.variable} unit={SYNTHETIC_PRODUCT.unit} selectedMonth={selectedMonth} onSelectMonth={(month) => { setPlaying(false); setSelectedMonth(month) }} />
            <h3>Recharts</h3>
            <SeriesChartRecharts points={points} variable={SYNTHETIC_PRODUCT.variable} unit={SYNTHETIC_PRODUCT.unit} selectedMonth={selectedMonth} onSelectMonth={(month) => { setPlaying(false); setSelectedMonth(month) }} />
          </section>
        </div>

        <div className="spike__details">
          <ContractPanel month={selectedMonth} layers={RASTER_LAYERS} mode={mode} onModeChange={setMode} variant={variant} onVariantChange={setVariant} />
          <ProvenancePanel manifest={FRAME_MANIFEST} mode={mode} status={status} />
        </div>

        <section aria-labelledby="table-title">
          <h2 id="table-title">Tabla equivalente del gráfico</h2>
          <SeriesTable points={points} variable={SYNTHETIC_PRODUCT.variable} unit={SYNTHETIC_PRODUCT.unit} selectedMonth={selectedMonth} />
        </section>
      </main>
    </>
  )
}

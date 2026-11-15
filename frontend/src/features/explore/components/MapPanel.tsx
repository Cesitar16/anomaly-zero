import { lazy, Suspense, useState } from 'react'
import { COPY } from '../content/exploreCopy'
import { monthsWithLayer, resolveMapTarget } from '../lib/rasterTarget'
import type { RasterResolver } from '../lib/rasterTarget'
import type { RasterLayer, YearMonth } from '../types/contracts'
import { MonthTimeline } from './MonthTimeline'
import { RasterLegend } from './RasterLegend'

// MapLibre es pesado: solo se descarga cuando hay una capa dibujable que mostrar.
const MapCanvas = lazy(() => import('./MapCanvas'))

export interface MapPanelProps {
  layers: RasterLayer[] | undefined
  months: YearMonth[]
  month: YearMonth | null
  resolver: RasterResolver
  onSelectMonth(month: YearMonth): void
}

const LAYER_KINDS = ['value', 'anomaly', 'slope', 'significance'] as const

/**
 * Mapa. Mientras la API no publique capas, la ausencia es el resultado: se dice con todas las letras y no se
 * dibuja mapa, límite de cuenca, leyenda de color ni herramienta por píxel. Solo se dibuja una capa si la API la
 * declara disponible Y esta versión sabe leer su formato (hoy: las capas sintéticas de demostración).
 */
export function MapPanel({ layers, months, month, resolver, onSelectMonth }: MapPanelProps) {
  const [isPlaying, setPlaying] = useState(false)
  const withLayer = monthsWithLayer(layers, months)
  const target =
    month === null ? ({ kind: 'absent' } as const) : resolveMapTarget({ layers, months, month, resolver })

  return (
    <section className="explore-card explore-map-panel" aria-labelledby="explore-map-title">
      <h3 id="explore-map-title" className="explore-chart__title">
        {COPY.map.title}
      </h3>

      {target.kind === 'frame' && month !== null ? (
        <>
          <Suspense fallback={<p role="status">{COPY.map.loading(month)}</p>}>
            <MapCanvas raster={target.raster} month={month} />
          </Suspense>
          <p className="explore-notice explore-notice--mock">{COPY.map.demoLayer}</p>
        </>
      ) : (
        <div className="explore-placeholder" role="note">
          <p className="explore-placeholder__title">{COPY.map.unavailable}</p>
          <p>
            {target.kind === 'absent'
              ? COPY.map.unavailableNote
              : target.kind === 'month-absent'
                ? COPY.map.monthMissing
                : COPY.map.notDrawable}
          </p>
        </div>
      )}

      <RasterLegend mode={target.kind === 'frame' ? 'demo' : 'none'} />

      <fieldset className="explore-layers">
        <legend>Capa</legend>
        {LAYER_KINDS.map((kind) => (
          <label key={kind} className={kind === 'value' ? undefined : 'explore-muted'}>
            <input type="radio" name="explore-layer" value={kind} checked={kind === 'value'} readOnly disabled={kind !== 'value'} />{' '}
            {COPY.map.layerTypes[kind]}
            {kind === 'value' ? '' : ` (${COPY.map.layerDisabled.toLowerCase()})`}
          </label>
        ))}
      </fieldset>

      {month !== null && months.length > 0 && (
        <MonthTimeline
          months={months.map((item) => ({ month: item, hasLayer: withLayer.has(item) }))}
          selectedMonth={month}
          onSelectMonth={onSelectMonth}
          isPlaying={isPlaying}
          onPlayingChange={setPlaying}
        />
      )}
    </section>
  )
}

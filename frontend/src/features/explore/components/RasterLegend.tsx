import { COPY } from '../content/exploreCopy'

/**
 * Leyenda del mapa. Sin capa no hay escala: no se dibuja una leyenda para algo que no se muestra.
 * Con una capa sintética de demostración, la escala es solo un degradado sin valores numéricos.
 */
export function RasterLegend({ mode }: { mode: 'none' | 'demo' }) {
  if (mode === 'none') return <p className="explore-legend explore-muted">{COPY.map.noLegend}</p>
  return (
    <div className="explore-legend">
      <div className="explore-legend__bar" aria-hidden="true" />
      <p>{COPY.map.legendDemo}</p>
      <p className="explore-muted">{COPY.map.legendNoData}</p>
    </div>
  )
}

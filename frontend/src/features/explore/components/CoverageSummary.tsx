import { COPY } from '../content/exploreCopy'
import { formatValue, orNotInformed } from '../lib/format'
import type { Coverage, InclusiveMonthRange, MonthRange } from '../types/contracts'

export interface CoverageSummaryProps {
  coverage: Coverage
  requested: InclusiveMonthRange
  available: MonthRange | null
}

/**
 * Cobertura: cuenta MESES (no área). El contrato también define cobertura espacial, pero el backend actual
 * la omite; si algún día llega, se muestra tal cual, con "No informado" para cada `null`.
 */
export function CoverageSummary({ coverage, requested, available }: CoverageSummaryProps) {
  const spatial = coverage.spatial_coverage
  const stats: Array<[string, string]> = [
    ['Rango pedido', `${requested.start} a ${requested.end}`],
    ['Cobertura publicada', available ? `${available.start} a ${available.end}` : COPY.notInformed],
    ['Meses pedidos', String(coverage.expected_periods)],
    ['Meses presentes', String(coverage.present_periods)],
    ['Meses con valor', String(coverage.valid_periods)],
    ['Meses sin dato', String(coverage.missing_periods.length)],
  ]
  return (
    <section className="explore-card" aria-labelledby="explore-coverage-title">
      <h2 id="explore-coverage-title" className="explore-panel__title">
        {COPY.provenance.coverageTitle}
      </h2>
      <dl className="explore-dl">
        {stats.map(([term, description]) => (
          <div key={term}>
            <dt>{term}</dt>
            <dd>{description}</dd>
          </div>
        ))}
      </dl>
      {coverage.missing_periods.length > 0 && (
        <p>
          Meses sin dato: <span className="explore-mono">{coverage.missing_periods.join(', ')}</span>
        </p>
      )}
      <p className="explore-card__note">{COPY.coverageNote}</p>
      {spatial && (
        <dl className="explore-dl">
          <div>
            <dt>Celdas evaluadas</dt>
            <dd>{spatial.evaluated_cells === null ? COPY.notInformed : formatValue(spatial.evaluated_cells)}</dd>
          </div>
          <div>
            <dt>Celdas con valor</dt>
            <dd>{spatial.valid_cells === null ? COPY.notInformed : formatValue(spatial.valid_cells)}</dd>
          </div>
          <div>
            <dt>Área de intersección (km²)</dt>
            <dd>{orNotInformed(spatial.intersection_area_km2)}</dd>
          </div>
        </dl>
      )}
    </section>
  )
}

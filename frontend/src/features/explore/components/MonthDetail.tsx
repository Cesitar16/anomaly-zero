import { COPY } from '../content/exploreCopy'
import { formatValue, orNotInformed } from '../lib/format'
import { monthLabel } from '../lib/months'
import { qualityText } from '../lib/chartModel'
import type { ChartPoint } from '../lib/chartModel'
import type { SpatialAggregation } from '../types/contracts'

export interface MonthDetailProps {
  point: ChartPoint | null
  unit: string
  support: SpatialAggregation | null
}

type Kind = 'value' | 'zero' | 'missing'

function kindOf(point: ChartPoint): Kind {
  if (point.value === null) return 'missing'
  return point.value === 0 ? 'zero' : 'value'
}

function supportText(support: SpatialAggregation): string {
  switch (support.support_type) {
    case 'point_sample':
      return COPY.detail.supportPoint
    case 'descriptive_mean':
      return COPY.detail.supportMean
    case 'regional_aggregate':
      return COPY.detail.supportRegional
  }
}

/**
 * Detalle del mes seleccionado. Solo repite lo que dice la respuesta del servicio para ese mes: el valor tal cual
 * (el cero es un valor y `null` es «Sin dato»), su calidad y el soporte espacial. No calcula ni compara nada.
 */
export function MonthDetail({ point, unit, support }: MonthDetailProps) {
  if (point === null) return null
  const kind = kindOf(point)
  const coordinates =
    support !== null && support.support_type === 'point_sample'
      ? support.point.latitude !== null && support.point.longitude !== null
        ? `${support.point.latitude.toLocaleString('es-CL')}, ${support.point.longitude.toLocaleString('es-CL')}`
        : COPY.notInformed
      : null
  return (
    <section className="explore-detail" aria-labelledby="explore-detail-title">
      <h3 id="explore-detail-title" className="explore-detail__eyebrow">
        {COPY.detail.title}
      </h3>
      <p className="explore-detail__month">{monthLabel(point.month)}</p>
      <p className="explore-detail__value">
        {point.value === null ? (
          COPY.state.gap
        ) : (
          <>
            <span className="explore-mono">{formatValue(point.value)}</span>{' '}
            <span className="explore-detail__unit">{unit}</span>
          </>
        )}
      </p>
      <p className={`explore-detail__state explore-detail__state--${kind}`}>{COPY.detail.state[kind]}</p>
      <p>{COPY.detail.explain[kind]}</p>
      <dl className="explore-detail__facts">
        <div>
          <dt>{COPY.detail.quality}</dt>
          <dd>{qualityText(point.qualityState)}</dd>
        </div>
        {point.missingReason !== null && (
          <div>
            <dt>{COPY.detail.reason}</dt>
            <dd>{orNotInformed(point.missingReason)}</dd>
          </div>
        )}
        {support !== null && (
          <div>
            <dt>{COPY.detail.support}</dt>
            <dd>{supportText(support)}</dd>
          </div>
        )}
        {coordinates !== null && (
          <div>
            <dt>{COPY.detail.coordinates}</dt>
            <dd>{coordinates}</dd>
          </div>
        )}
      </dl>
    </section>
  )
}

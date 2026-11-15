import { COPY, quantityLabel } from '../content/exploreCopy'
import { orNotInformed } from '../lib/format'
import type { SpatialAggregation } from '../types/contracts'

/**
 * Dice QUÉ representa cada valor de la serie. El contrato lo declara en `spatial_aggregation`:
 * - `point_sample`: la muestra de UNA celda. Nunca se rotula "promedio de la cuenca".
 * - `descriptive_mean`: promedio descriptivo, sin aprobación.
 * - `regional_aggregate`: único soporte aprobado (hoy no existe en el backend).
 */
export function SupportNotice({ support, quantity }: { support: SpatialAggregation | null; quantity: string }) {
  if (support === null) return null
  switch (support.support_type) {
    case 'point_sample': {
      const { latitude, longitude, cell_id: cellId } = support.point
      const place =
        latitude !== null && longitude !== null
          ? `${latitude.toLocaleString('es-CL')}, ${longitude.toLocaleString('es-CL')}`
          : COPY.noCoordinates
      return (
        <div className="explore-support explore-support--point">
          <p className="explore-support__label">{COPY.sample}</p>
          <p>{COPY.supportPoint}</p>
          <p className="explore-support__meta">
            Celda <code>{cellId}</code> ({place}) · {quantityLabel(quantity)}
          </p>
        </div>
      )
    }
    case 'descriptive_mean':
      return (
        <div className="explore-support">
          <p className="explore-support__label">Promedio descriptivo, sin aprobación</p>
          <p>
            Promedio de {support.cell_count} celdas ({support.method}). No es un agregado regional aprobado.
          </p>
          <p className="explore-support__meta">
            Ponderación por área: {support.area_weighted ? 'sí' : 'no'} · Máscara: {orNotInformed(support.mask_version)}
          </p>
        </div>
      )
    case 'regional_aggregate':
      return (
        <div className="explore-support">
          <p className="explore-support__label">Agregado regional aprobado</p>
          <p className="explore-support__meta">
            Método: {support.method} · Referencia de aprobación: {support.approval_reference} · Máscara:{' '}
            {support.mask_version}
          </p>
        </div>
      )
  }
}

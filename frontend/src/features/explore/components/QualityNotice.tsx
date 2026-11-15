import { COPY, verificationText } from '../content/exploreCopy'
import { formatLooseValue, orNotInformed } from '../lib/format'
import type { Quality } from '../types/contracts'

const CHECK_STATE: Record<string, string> = {
  not_run: 'No ejecutado',
  passed: 'Aprobado',
  failed: 'Fallido',
  partial: 'Parcial',
}

function yesNo(value: boolean): string {
  return value ? 'Sí' : 'No'
}

/**
 * Calidad de los datos. El texto sale de `verification_state` y NUNCA dice "calidad aprobada" salvo que el
 * contrato diga `provider_qa_applied`. `unassessed` y `basic_checks_only` se muestran como advertencia.
 */
export function QualityNotice({ quality }: { quality: Quality }) {
  const checks = quality.qa_checks ?? []
  const uninterpreted = quality.uninterpreted_provider_fields ?? []
  const attributes = quality.source_missing_attributes
  const warn = quality.verification_state !== 'provider_qa_applied'
  return (
    <section className="explore-card" aria-labelledby="explore-quality-title">
      <h2 id="explore-quality-title" className="explore-panel__title">
        {COPY.quality.title}
      </h2>
      <p className={warn ? 'explore-notice explore-notice--warn' : 'explore-notice'}>
        {verificationText(quality.verification_state)}
      </p>
      <dl className="explore-dl">
        <div>
          <dt>Calidad del proveedor aplicada</dt>
          <dd>{yesNo(quality.provider_flags_applied)}</dd>
        </div>
        <div>
          <dt>Filtro de valores no finitos y de relleno</dt>
          <dd>{yesNo(quality.finite_non_fill_filter_applied)}</dd>
        </div>
        <div>
          <dt>Máscara aplicada</dt>
          <dd>{orNotInformed(quality.mask_applied)}</dd>
        </div>
        <div>
          <dt>Campos de calidad de la fuente</dt>
          <dd className="explore-mono">
            {quality.source_flag_fields.length > 0 ? quality.source_flag_fields.join(', ') : COPY.notInformed}
          </dd>
        </div>
        <div>
          <dt>Valor de relleno</dt>
          <dd className="explore-mono">{formatLooseValue(attributes.fill_value)}</dd>
        </div>
        <div>
          <dt>Valor faltante</dt>
          <dd className="explore-mono">{formatLooseValue(attributes.missing_value)}</dd>
        </div>
        <div>
          <dt>Factor de escala</dt>
          <dd className="explore-mono">{formatLooseValue(attributes.scale_factor)}</dd>
        </div>
        <div>
          <dt>Desplazamiento</dt>
          <dd className="explore-mono">{formatLooseValue(attributes.add_offset)}</dd>
        </div>
      </dl>
      {uninterpreted.length > 0 && (
        <p>
          Campos del proveedor sin interpretar: <span className="explore-mono">{uninterpreted.join(', ')}</span>
        </p>
      )}
      {checks.length === 0 ? (
        <p>{COPY.quality.checksEmpty}</p>
      ) : (
        <ul className="explore-list">
          {checks.map((check) => (
            <li key={check.check_id}>
              <span className="explore-mono">{check.check_id}</span>: {CHECK_STATE[check.state] ?? check.state}
              {check.applied ? '' : ' (no aplicado)'}
              {check.excluded_count !== null ? `, ${check.excluded_count} excluidos` : ''}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

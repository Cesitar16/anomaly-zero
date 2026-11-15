import { COPY, ERROR_COPY } from '../content/exploreCopy'
import type { AnalysisResponse, Remote, SpatialAggregation } from '../types/contracts'

export interface AnalysisUnavailableProps {
  support: SpatialAggregation | null
  /** Solo con servicio simulado: pide `POST /analyses` y muestra la respuesta 409 del contrato. */
  onProbe?: () => void
  probe?: Remote<AnalysisResponse>
}

/**
 * Análisis de tendencia: SIEMPRE no disponible. No hay método estadístico aprobado, así que el control está
 * deshabilitado y no se calcula ninguna pendiente, intervalo ni valor p. Con el servicio simulado se puede
 * ver la respuesta `409 ANALYSIS_METHOD_UNAVAILABLE` del contrato; no hay otra respuesta posible.
 */
export function AnalysisUnavailable({ support, onProbe, probe }: AnalysisUnavailableProps) {
  const failure = probe?.status === 'error' && probe.failure.kind === 'api' ? probe.failure : null
  const analysis = failure?.body.error.details?.analysis
  const code = failure?.body.error.code
  return (
    <section className="explore-card" aria-labelledby="explore-analysis-title">
      <h2 id="explore-analysis-title" className="explore-panel__title">
        {ERROR_COPY.ANALYSIS_METHOD_UNAVAILABLE.title}
      </h2>
      <p>{COPY.analysis.body}</p>
      {support?.support_type === 'point_sample' && <p>{COPY.analysis.point}</p>}
      <p>
        <button type="button" className="btn btn--secondary" disabled aria-describedby="explore-analysis-reason">
          {COPY.analysis.disabledControl}
        </button>
      </p>
      <p id="explore-analysis-reason" className="explore-card__note">
        {COPY.analysis.disabledReason}
      </p>

      {onProbe && (
        <div className="explore-probe">
          <button
            type="button"
            className="btn btn--secondary"
            onClick={onProbe}
            disabled={probe?.status === 'loading'}
          >
            Ver la respuesta del servicio simulado
          </button>
          {failure && analysis && (
            <details open>
              <summary>{COPY.analysis.technical}</summary>
              <dl className="explore-dl">
                <div>
                  <dt>Código</dt>
                  <dd className="explore-mono">{code}</dd>
                </div>
                <div>
                  <dt>Estado HTTP</dt>
                  <dd className="explore-mono">{failure.httpStatus}</dd>
                </div>
                <div>
                  <dt>Identificador del análisis</dt>
                  <dd>{COPY.analysis.notCreated}</dd>
                </div>
                <div>
                  <dt>Método</dt>
                  <dd>{COPY.analysis.noMethod}</dd>
                </div>
                <div>
                  <dt>Pendiente</dt>
                  <dd>{COPY.analysis.notComputed.f}</dd>
                </div>
                <div>
                  <dt>Intervalo de confianza</dt>
                  <dd>{COPY.analysis.notComputed.m}</dd>
                </div>
                <div>
                  <dt>Valor p</dt>
                  <dd>{COPY.analysis.notComputed.m}</dd>
                </div>
              </dl>
            </details>
          )}
        </div>
      )}
    </section>
  )
}

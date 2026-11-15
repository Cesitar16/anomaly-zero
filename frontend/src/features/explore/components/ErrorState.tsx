import { ERROR_COPY, invalidParameterBody } from '../content/exploreCopy'
import type { ExploreFailure } from '../types/contracts'

export interface ErrorStateProps {
  failure: ExploreFailure
  onRetry?: () => void
  /** Texto del botón de reintento. */
  retryLabel?: string
  headingLevel?: 'h2' | 'h3'
}

function copyFor(failure: ExploreFailure): { title: string; body: string } {
  if (failure.kind === 'network') return ERROR_COPY.NETWORK
  const { code, details } = failure.body.error
  if (code === 'INVALID_PARAMETER') {
    const field = typeof details?.field === 'string' ? details.field : undefined
    return { title: ERROR_COPY.INVALID_PARAMETER.title, body: invalidParameterBody(field) }
  }
  return code in ERROR_COPY ? ERROR_COPY[code] : ERROR_COPY.INTERNAL_ERROR
}

/**
 * Error de la API o de la red. El `code` elige el texto; el mensaje del servicio y el `request_id` quedan
 * como detalle secundario. Un 503 o un 500 NUNCA se presenta como "sin datos". Solo se ofrece reintentar
 * cuando el servicio dice que es reintentable (`retryable`) o cuando no hubo respuesta.
 */
export function ErrorState({ failure, onRetry, retryLabel = 'Reintentar', headingLevel = 'h3' }: ErrorStateProps) {
  const { title, body } = copyFor(failure)
  const Heading = headingLevel
  const canRetry = onRetry !== undefined && (failure.kind === 'network' || failure.body.error.retryable)
  return (
    <div className="explore-error" role="alert">
      <Heading className="explore-error__title">{title}</Heading>
      <p>{body}</p>
      {failure.kind === 'api' && (
        <p className="explore-error__meta">
          Código: <code>{failure.body.error.code}</code> · Referencia: <code>{failure.body.error.request_id}</code>
        </p>
      )}
      {canRetry && (
        <button type="button" className="btn btn--secondary" onClick={onRetry}>
          {retryLabel}
        </button>
      )}
    </div>
  )
}

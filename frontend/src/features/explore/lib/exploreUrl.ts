import type { SeriesQuery, YearMonth } from '../types/contracts'
import { isYearMonth, validateRange } from './months'
import type { RangeErrors } from './months'

/** Filtros tal como se muestran en el formulario: texto sin validar ('' = sin elegir). */
export interface DraftFilters {
  regionId: string
  productId: string
  start: string
  end: string
}

export const EMPTY_DRAFT: DraftFilters = { regionId: '', productId: '', start: '', end: '' }

export interface UrlState {
  /** Lo que dice la dirección, sin validar, para rellenar el formulario. */
  draft: DraftFilters
  /** La consulta, solo si TODA la dirección es válida; si no, no se consulta nada. */
  query: SeriesQuery | null
  /** Errores de rango de una dirección escrita a mano (se validan como si los hubiera escrito la persona). */
  rangeErrors: RangeErrors
  month: YearMonth | null
  /** Escenario de demostración (solo lo entiende el servicio simulado). */
  scenario: string | null
}

/**
 * Lee `region`, `product`, `start`, `end`, `month` y `demo` de la dirección.
 * Una dirección incompleta o inválida rellena el formulario pero no dispara ninguna consulta.
 */
export function readUrl(params: URLSearchParams): UrlState {
  const draft: DraftFilters = {
    regionId: params.get('region') ?? '',
    productId: params.get('product') ?? '',
    start: params.get('start') ?? '',
    end: params.get('end') ?? '',
  }
  const hasAny = Object.values(draft).some((value) => value !== '')
  const rangeErrors = hasAny && draft.start !== '' && draft.end !== '' ? validateRange(draft.start, draft.end) : {}
  const complete = Object.values(draft).every((value) => value !== '')
  const query: SeriesQuery | null =
    complete && Object.keys(rangeErrors).length === 0
      ? { regionId: draft.regionId, productId: draft.productId, start: draft.start, end: draft.end }
      : null
  const month = params.get('month')
  return {
    draft,
    query,
    rangeErrors,
    month: month !== null && isYearMonth(month) ? month : null,
    scenario: params.get('demo'),
  }
}

export function queryKey(query: SeriesQuery | null): string {
  return query === null ? '' : [query.regionId, query.productId, query.start, query.end].join('|')
}

/** Construye la dirección de una consulta enviada. El escenario de demostración se conserva. */
export function buildParams(input: {
  query: SeriesQuery
  month: YearMonth | null
  scenario: string | null
}): URLSearchParams {
  const params = new URLSearchParams({
    region: input.query.regionId,
    product: input.query.productId,
    start: input.query.start,
    end: input.query.end,
  })
  if (input.month) params.set('month', input.month)
  if (input.scenario) params.set('demo', input.scenario)
  return params
}

import { useCallback, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { COPY } from '../content/exploreCopy'
import type { ExploreApi } from '../data/exploreApi'
import { buildParams, queryKey, readUrl } from '../lib/exploreUrl'
import type { DraftFilters } from '../lib/exploreUrl'
import { MAX_MONTHS, isYearMonth, monthOfDate, validateRange } from '../lib/months'
import { monthsWithLayer } from '../lib/rasterTarget'
import type {
  AnalysisResponse,
  ApiResult,
  Product,
  Region,
  Remote,
  SeriesQuery,
  SeriesResponse,
  YearMonth,
} from '../types/contracts'
import { useResource } from './useResource'

export interface FieldErrors {
  region?: string
  product?: string
  start?: string
  end?: string
}

export interface Explorer {
  api: ExploreApi
  draft: DraftFilters
  regions: Remote<Region[]>
  products: Remote<Product[]>
  /** `true` si los filtros cambiaron después de la última consulta enviada. */
  dirty: boolean
  fieldErrors: FieldErrors
  /** `true` si hay una consulta enviada (aunque todavía esté cargando). */
  submitted: boolean
  series: Remote<SeriesResponse>
  month: YearMonth | null
  months: YearMonth[]
  /** Sondeo del servicio de análisis (solo servicio simulado): siempre responde "no disponible". */
  analysis: Remote<AnalysisResponse>
  setRegion(regionId: string): void
  setProduct(productId: string): void
  setStart(value: string): void
  setEnd(value: string): void
  submit(): void
  retrySeries(): void
  retryCatalog(): void
  selectMonth(month: YearMonth): void
  probeAnalysis(): void
}

function lastMonthOfWindow(start: YearMonth, end: YearMonth): YearMonth {
  const [startYear, startMonth] = start.split('-').map(Number)
  const index = startYear * 12 + (startMonth - 1) + (MAX_MONTHS - 1)
  const limit = `${Math.floor(index / 12)}-${String((index % 12) + 1).padStart(2, '0')}`
  return end < limit ? end : limit
}

export function useExplorer(api: ExploreApi, scenario: string | null): Explorer {
  const [params, setParams] = useSearchParams()
  const url = useMemo(() => readUrl(params), [params])
  // Cambiar de fuente (simulada o real) o de escenario invalida todo lo cargado antes.
  const sourceKey = `${api.mode}:${scenario ?? ''}`

  // --- Filtros del formulario. Siguen a la dirección cuando esta cambia (atrás/adelante). ------------
  const urlDraftKey = JSON.stringify(url.draft)
  const [draftOverride, setDraftOverride] = useState<{ base: string; draft: DraftFilters } | null>(null)
  const draftState: DraftFilters =
    draftOverride !== null && draftOverride.base === urlDraftKey ? draftOverride.draft : url.draft
  const [showErrors, setShowErrors] = useState(false)
  const [retryNonce, setRetryNonce] = useState(0)
  const [catalogNonce, setCatalogNonce] = useState(0)

  // --- Catálogo ----------------------------------------------------------------------------------
  const regionsRemote = useResource(
    `${sourceKey}|regions`,
    (signal) => api.listRegions(signal).then((result) => mapResult(result, (body) => body.regions)),
    catalogNonce,
  )
  const singleRegionId =
    regionsRemote.status === 'success' && regionsRemote.data.length === 1
      ? regionsRemote.data[0].region_id
      : ''
  const draft = useMemo<DraftFilters>(
    () => ({
      ...draftState,
      regionId: draftState.regionId !== '' ? draftState.regionId : singleRegionId,
    }),
    [draftState, singleRegionId],
  )

  const productsRemote = useResource(
    draft.regionId === '' ? null : `${sourceKey}|products|${draft.regionId}`,
    (signal) =>
      api.listProducts(draft.regionId, signal).then((result) => mapResult(result, (body) => body.products)),
    catalogNonce,
  )

  const editDraft = useCallback(
    (change: (current: DraftFilters) => DraftFilters) => {
      setDraftOverride({ base: urlDraftKey, draft: change(draft) })
    },
    [draft, urlDraftKey],
  )

  // --- Consulta enviada (la dirección manda) -----------------------------------------------------
  const regionKnown =
    url.query === null ||
    regionsRemote.status !== 'success' ||
    regionsRemote.data.some((region) => region.region_id === url.query?.regionId)
  const productKnown =
    url.query === null ||
    productsRemote.status !== 'success' ||
    url.query.regionId !== draft.regionId ||
    productsRemote.data.some((product) => product.product_id === url.query?.productId)

  // La consulta espera a que el catálogo responda para poder avisar de una región o producto desconocidos.
  const waitingForCatalog =
    url.query !== null && (regionsRemote.status === 'loading' || productsRemote.status === 'loading')
  const sendQuery: SeriesQuery | null =
    url.query !== null && !waitingForCatalog && regionKnown && productKnown ? url.query : null

  const seriesRemote = useResource(
    sendQuery === null ? null : `${sourceKey}|series|${queryKey(sendQuery)}`,
    (signal) => (sendQuery === null ? Promise.resolve(NO_QUERY) : api.getSeries(sendQuery, signal)),
    retryNonce,
  )
  const series: Remote<SeriesResponse> = waitingForCatalog ? { status: 'loading' } : seriesRemote

  // --- Errores de formulario ---------------------------------------------------------------------
  const liveErrors = useMemo<FieldErrors>(() => {
    const errors: FieldErrors = {}
    if (draft.regionId === '') errors.region = COPY.filters.required.region
    if (draft.productId === '') errors.product = COPY.filters.required.product
    Object.assign(errors, validateRange(draft.start, draft.end))
    return errors
  }, [draft.regionId, draft.productId, draft.start, draft.end])

  const urlErrors: FieldErrors = {}
  if (!regionKnown) urlErrors.region = COPY.filters.unknownRegion
  if (!productKnown) urlErrors.product = COPY.filters.unknownProduct
  Object.assign(urlErrors, url.rangeErrors)
  const fieldErrors: FieldErrors = showErrors ? { ...urlErrors, ...liveErrors } : urlErrors

  const dirty =
    url.query === null
      ? false
      : url.query.regionId !== draft.regionId ||
        url.query.productId !== draft.productId ||
        url.query.start !== draft.start ||
        url.query.end !== draft.end

  // --- Mes seleccionado ----------------------------------------------------------------------------
  const seriesData = series.status === 'success' ? series.data : null
  const months = useMemo(
    () => (seriesData ? seriesData.series.map((point) => monthOfDate(point.date)) : []),
    [seriesData],
  )
  const defaultMonth = useMemo<YearMonth | null>(() => {
    const withLayer = monthsWithLayer(seriesData?.raster_layers, months)
    return months.find((month) => withLayer.has(month)) ?? months[0] ?? null
  }, [seriesData, months])
  const month = url.month !== null && months.includes(url.month) ? url.month : defaultMonth

  // --- Acciones ------------------------------------------------------------------------------------
  const setRegion = useCallback(
    (regionId: string) => editDraft((current) => ({ ...current, regionId, productId: '' })),
    [editDraft],
  )

  const setProduct = useCallback(
    (productId: string) =>
      editDraft((current) => {
        const next = { ...current, productId }
        const product =
          productsRemote.status === 'success'
            ? productsRemote.data.find((candidate) => candidate.product_id === productId)
            : undefined
        // Con los meses vacíos se propone la cobertura publicada (máximo 240 meses). La persona la puede cambiar.
        if (product?.coverage && next.start === '' && next.end === '') {
          next.start = product.coverage.start
          next.end = lastMonthOfWindow(product.coverage.start, product.coverage.end)
        }
        return next
      }),
    [editDraft, productsRemote],
  )

  const setStart = useCallback(
    (start: string) => editDraft((current) => ({ ...current, start })),
    [editDraft],
  )
  const setEnd = useCallback((end: string) => editDraft((current) => ({ ...current, end })), [editDraft])

  const submit = useCallback(() => {
    if (Object.keys(liveErrors).length > 0) {
      setShowErrors(true)
      return
    }
    setShowErrors(false)
    const query: SeriesQuery = {
      regionId: draft.regionId,
      productId: draft.productId,
      start: draft.start,
      end: draft.end,
      siteId: params.get('site_id') ?? undefined,
    }
    if (queryKey(query) === queryKey(url.query)) {
      setRetryNonce((nonce) => nonce + 1)
      return
    }
    setParams(buildParams({ query, month: null, scenario, source: url.source }))
  }, [liveErrors, draft, url.query, url.source, scenario, setParams, params])

  const retrySeries = useCallback(() => setRetryNonce((nonce) => nonce + 1), [])
  const retryCatalog = useCallback(() => setCatalogNonce((nonce) => nonce + 1), [])

  const selectMonth = useCallback(
    (next: YearMonth) => {
      if (!isYearMonth(next)) return
      const updated = new URLSearchParams(params)
      updated.set('month', next)
      setParams(updated, { replace: true })
    },
    [params, setParams],
  )

  // --- Sondeo del servicio de análisis (solo servicio simulado) --------------------------------------
  const seriesKey = sendQuery === null ? '' : queryKey(sendQuery)
  const [probe, setProbe] = useState<{ key: string; state: Remote<AnalysisResponse> } | null>(null)
  const analysis: Remote<AnalysisResponse> =
    probe !== null && probe.key === seriesKey ? probe.state : { status: 'idle' }

  const probeAnalysis = useCallback(() => {
    if (!api.capabilities.analyses || seriesData === null || seriesData.dataset_id === null) return
    const key = seriesKey
    setProbe({ key, state: { status: 'loading' } })
    void api
      .createAnalysis({ dataset_id: seriesData.dataset_id, window: seriesData.requested_coverage })
      .then((result) =>
        setProbe({
          key,
          state: result.ok
            ? { status: 'success', data: result.data }
            : { status: 'error', failure: result.failure },
        }),
      )
  }, [api, seriesData, seriesKey])

  return {
    api,
    draft,
    regions: regionsRemote,
    products: productsRemote,
    dirty,
    fieldErrors,
    submitted: url.query !== null,
    series,
    month,
    months,
    analysis,
    setRegion,
    setProduct,
    setStart,
    setEnd,
    submit,
    retrySeries,
    retryCatalog,
    selectMonth,
    probeAnalysis,
  }
}

const NO_QUERY: ApiResult<SeriesResponse> = { ok: false, failure: { kind: 'network' } }

function mapResult<T, U>(result: ApiResult<T>, map: (data: T) => U): ApiResult<U> {
  return result.ok ? { ok: true, data: map(result.data) } : result
}

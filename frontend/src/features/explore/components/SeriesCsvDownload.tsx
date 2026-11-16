import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import type { ExploreApi } from '../data/exploreApi'
import type { ExploreFailure, Remote, SeriesResponse, SeriesQuery } from '../types/contracts'
import { ErrorState } from './ErrorState'

function safePart(value: string): string {
  return value.replace(/[^a-zA-Z0-9_-]/g, '-')
}

function queryFor(series: SeriesResponse): SeriesQuery {
  return {
    regionId: series.region.region_id,
    productId: series.product.product_id,
    start: series.requested_coverage.start,
    end: series.requested_coverage.end,
  }
}

export function SeriesCsvDownload({
  api,
  series,
  dirty,
}: {
  api: ExploreApi
  series: Remote<SeriesResponse>
  dirty: boolean
}) {
  const [pendingKey, setPendingKey] = useState<string | null>(null)
  const [lastFailure, setLastFailure] = useState<{ key: string; failure: ExploreFailure } | null>(null)
  const activeRequest = useRef<AbortController | null>(null)
  const current = series.status === 'success' ? series.data : null
  const query = current ? queryFor(current) : null
  const requestKey = JSON.stringify([api.mode, dirty, query])
  const latestRequestKey = useRef(requestKey)
  const pending = pendingKey === requestKey
  const failure = lastFailure?.key === requestKey ? lastFailure.failure : null
  const available = current !== null && current.data_state !== 'no_data' && current.coverage.valid_periods > 0 && current.series.length > 0
  const disabled =
    api.mode !== 'http' ||
    api.downloadSeriesCsv === undefined ||
    dirty ||
    series.status !== 'success' ||
    !available ||
    pending

  useEffect(() => {
    activeRequest.current?.abort()
    activeRequest.current = null
    return () => activeRequest.current?.abort()
  }, [requestKey])

  useLayoutEffect(() => {
    latestRequestKey.current = requestKey
  }, [requestKey])

  const reason = api.mode !== 'http'
    ? 'Disponible solo con una consulta de la API real.'
    : dirty
      ? 'Aplica los filtros antes de descargar; la serie visible corresponde a la consulta anterior.'
      : series.status === 'loading'
        ? 'Espera a que termine la consulta.'
        : !available
          ? 'No hay observaciones disponibles para exportar.'
          : pending
            ? 'La descarga está en curso.'
            : 'Descarga la serie mensual mostrada en formato CSV.'

  async function download() {
    if (disabled || activeRequest.current !== null || query === null || current === null || api.downloadSeriesCsv === undefined) return
    const controller = new AbortController()
    activeRequest.current = controller
    setPendingKey(requestKey)
    setLastFailure(null)
    const result = await api.downloadSeriesCsv(query, controller.signal)
    if (controller.signal.aborted || latestRequestKey.current !== requestKey) return
    activeRequest.current = null
    if (!result.ok) {
      setLastFailure({ key: requestKey, failure: result.failure })
      setPendingKey(null)
      return
    }
    const url = URL.createObjectURL(result.data)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `anomaly-zero_${safePart(query.regionId)}_${safePart(query.productId)}_${query.start}_${query.end}.csv`
    anchor.hidden = true
    document.body.append(anchor)
    anchor.click()
    anchor.remove()
    window.setTimeout(() => URL.revokeObjectURL(url), 0)
    setPendingKey(null)
  }

  return (
    <div className="explore-csv-download">
      <button type="button" className="btn btn--secondary" disabled={disabled} title={reason} onClick={download}>
        {pending ? 'Preparando CSV…' : 'Descargar CSV'}
      </button>
      <p className="explore-muted" role="note">{reason}</p>
      {failure && <ErrorState failure={failure} headingLevel="h3" />}
    </div>
  )
}

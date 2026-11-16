import { useEffect, useState } from 'react'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { ExploreApi } from '../data/exploreApi'
import type { SeriesQuery, SeriesResponse } from '../types/contracts'

const VARIABLES = [
  { id: 'P01', title: 'MERRA-2 · T2M', unit: 'K', color: '#315f83' },
  { id: 'P02', title: 'IMERG · precipitation', unit: 'mm/hr', color: '#16816b' },
  { id: 'P03', title: 'GLDAS · SoilMoi0_10cm_inst', unit: 'kg m-2', color: '#a66b20' },
] as const

interface Props {
  api: ExploreApi
  query: SeriesQuery
}

export function MultivariableComparison({ api, query }: Props) {
  const { regionId, siteId, start, end } = query
  const key = `${regionId}|${siteId ?? ''}|${start}|${end}`
  const [state, setState] = useState<{ key: string; results?: SeriesResponse[]; failed?: boolean } | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    void Promise.all(VARIABLES.map((variable) => api.getSeries({ regionId, siteId, start, end, productId: variable.id }, controller.signal)))
      .then((responses) => {
        if (controller.signal.aborted) return
        if (responses.some((response) => !response.ok || response.data.data_state === 'no_data')) {
          setState({ key, failed: true })
          return
        }
        setState({ key, results: responses.flatMap((response) => response.ok ? [response.data] : []) })
      })
      .catch(() => { if (!controller.signal.aborted) setState({ key, failed: true }) })
    return () => controller.abort()
  }, [api, regionId, siteId, start, end, key])

  const results = state?.key === key ? state.results ?? null : null
  const failed = state?.key === key && state.failed === true

  return (
    <section className="az-multivariable" aria-labelledby="az-multivariable-title">
      <h2 id="az-multivariable-title">Comparación descriptiva mensual</h2>
      <p>Escalas independientes; la misma etiqueta de sitio candidato no significa que las celdas o huellas sean co-localizadas. Sin correlaciones ni inferencia.</p>
      {failed && <p role="status">No se pudieron cargar las tres series completas para este sitio y período.</p>}
      {!results && !failed && <p role="status" aria-busy="true">Cargando series comparativas…</p>}
      {results && <div className="az-multivariable__grid">
        {VARIABLES.map((variable, index) => {
          const response = results[index]
          const points = response.series.map((point) => ({ month: point.date.slice(0, 7), value: point.value }))
          const point = response.spatial_aggregation?.support_type === 'point_sample' ? response.spatial_aggregation.point : null
          return <figure key={variable.id} className="az-multivariable__chart">
            <figcaption><strong>{variable.title}</strong><span>{variable.unit}</span><small>{point?.cell_id ?? 'Soporte espacial no informado'}</small></figcaption>
            <div role="img" aria-label={`${variable.title}, ${variable.unit}, serie mensual descriptiva`} className="az-multivariable__plot">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={points} margin={{ top: 12, right: 16, bottom: 8, left: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                  <YAxis unit={` ${variable.unit}`} width={72} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(value) => [`${value ?? 'Sin dato'} ${variable.unit}`, variable.title]} />
                  <Line type="linear" dataKey="value" stroke={variable.color} strokeWidth={2} dot={{ r: 2 }} connectNulls={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <table className="az-multivariable__table">
              <caption>{variable.title} — {variable.unit}</caption>
              <thead><tr><th scope="col">Mes</th><th scope="col">Valor ({variable.unit})</th></tr></thead>
              <tbody>{points.map((point) => <tr key={point.month}><th scope="row">{point.month}</th><td>{point.value === null ? 'Sin dato' : point.value}</td></tr>)}</tbody>
            </table>
          </figure>
        })}
      </div>}
    </section>
  )
}

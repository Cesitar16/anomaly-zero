import { useId, useMemo } from 'react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { PlotPoint, ScientificSeriesPanelProps } from './types'
import './scientific-series.css'

const dateFormatter = new Intl.DateTimeFormat('es', { month: 'short', year: 'numeric', timeZone: 'UTC' })
const numberFormatter = new Intl.NumberFormat('es', { maximumFractionDigits: 4 })

function monthLabel(value: string): string {
  const date = new Date(`${value.slice(0, 7)}-01T00:00:00Z`)
  return Number.isNaN(date.getTime()) ? value : dateFormatter.format(date)
}

function qualityLabel(state: string): string {
  const known: Record<string, string> = {
    unassessed: 'No evaluada',
    missing: 'Dato faltante',
    unknown: 'Desconocida',
    passed: 'Indicador del proveedor: aprobado',
    failed: 'Indicador del proveedor: rechazado',
  }
  return known[state] ?? `Estado QA: ${state}`
}

function valueLabel(value: number | null, unit?: string): string {
  if (value === null) return 'Sin dato'
  return `${numberFormatter.format(value)}${unit ? ` ${unit}` : ''}`
}

function monthSequence(start?: string, end?: string): string[] {
  if (!start || !end) return []
  const from = /^(\d{4})-(\d{2})/.exec(start)
  const to = /^(\d{4})-(\d{2})/.exec(end)
  if (!from || !to) return []
  let year = Number(from[1])
  let month = Number(from[2])
  const endYear = Number(to[1])
  const endMonth = Number(to[2])
  if (month < 1 || month > 12 || endMonth < 1 || endMonth > 12) return []
  const result: string[] = []
  while ((year < endYear || (year === endYear && month <= endMonth)) && result.length < 240) {
    result.push(`${year}-${String(month).padStart(2, '0')}-01`)
    month += 1
    if (month === 13) { year += 1; month = 1 }
  }
  return result
}

function SeriesTooltip({ active, label, payload, points, unit }: {
  active?: boolean
  label?: string | number
  payload?: ReadonlyArray<{ payload?: PlotPoint }>
  points: readonly PlotPoint[]
  unit?: string
}) {
  if (!active) return null
  const point = payload?.find((item) => item.payload)?.payload
    ?? points.find((item) => item.date === String(label))
  if (!point) return null
  return <div className="ssp-tooltip" role="status">
    <strong>{monthLabel(point.date)}</strong>
    <span>{valueLabel(point.value, unit)}</span>
    <span>{qualityLabel(point.qualityState)}</span>
    {point.missingReason && <span>{point.missingReason}</span>}
  </div>
}

export function ScientificSeriesPanel({ response, className }: ScientificSeriesPanelProps) {
  const titleId = useId()
  const points = useMemo<PlotPoint[]>(() => {
    const byDate = new Map(response.series.map((item) => [item.date, item]))
    const dates = monthSequence(response.requested_coverage?.start, response.requested_coverage?.end)
    const rows = dates.length > 0 ? dates.map((date) => byDate.get(date) ?? {
      date,
      value: null,
      quality: { state: 'missing', missing_reason: 'Período mensual ausente en la respuesta', provider_flags: [] },
    }) : response.series
    return rows.map((item) => ({
      month: monthLabel(item.date),
      date: item.date,
      value: item.value,
      qualityState: item.quality?.state ?? (item.value === null ? 'missing' : 'unassessed'),
      missingReason: item.quality?.missing_reason ?? null,
      flags: item.quality?.provider_flags ?? [],
      invalidValue: typeof item.value === 'number' && !Number.isFinite(item.value),
    }))
  }, [response.series, response.requested_coverage?.start, response.requested_coverage?.end])

  const product = response.product
  const unit = product.unit?.trim() || undefined
  const stateText = response.data_state === 'available'
    ? 'Datos disponibles'
    : response.data_state === 'available_with_gaps'
      ? 'Datos disponibles con períodos faltantes; los huecos no se interpolan.'
      : 'No hay datos disponibles para esta consulta.'
  const title = [product.short_name ?? product.product_id ?? 'Producto NASA', product.variable]
    .filter(Boolean).join(' · ')
  const spatialKind = response.spatial_aggregation?.support_type

  return <section className={`scientific-series-panel${className ? ` ${className}` : ''}`} aria-labelledby={titleId}>
    <header className="ssp-header">
      <div>
        <h2 id={titleId}>{title}</h2>
        <p>{product.quantity ?? 'Serie mensual'}{unit ? ` · ${unit}` : ''}{product.product_version ? ` · versión ${product.product_version}` : ''}</p>
      </div>
      <div className="ssp-badges">
        <span className={`ssp-state ssp-state--${response.data_state}`} role="status">{stateText}</span>
        {response.synthetic && <span className="ssp-synthetic" role="note">Datos sintéticos · no son observaciones NASA</span>}
      </div>
    </header>

    {spatialKind === 'point_sample' && <p className="ssp-warning">Muestra puntual (point_sample): no representa un promedio regional Murray–Darling.</p>}
    {spatialKind !== 'regional_aggregate' && <p className="ssp-warning">No se proporcionó una agregación regional aprobada.</p>}
    {response.quality?.verification_state !== 'provider_qa_applied' && <p className="ssp-warning">La QA del proveedor no está aplicada o aprobada para esta respuesta.</p>}

    {response.data_state !== 'no_data' && points.length > 0 && <div className="ssp-chart" aria-label="Gráfico de serie temporal mensual">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={points} margin={{ top: 12, right: 18, left: 8, bottom: 8 }} accessibilityLayer>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" tickFormatter={monthLabel} minTickGap={28} />
          <YAxis width={72} tickFormatter={(value: number) => numberFormatter.format(value)} label={unit ? { value: unit, angle: -90, position: 'insideLeft' } : undefined} />
          <Tooltip content={<SeriesTooltip points={points} unit={unit} />} />
          <Line type="linear" dataKey="value" name={title} stroke="#2563eb" strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 5 }} connectNulls={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>}
    {response.data_state === 'no_data' && <p className="ssp-empty">No hay observaciones que graficar.</p>}
    {response.data_state !== 'no_data' && points.length === 0 && <p className="ssp-empty">La respuesta no contiene puntos para graficar.</p>}

    <div className="ssp-table-wrap">
      <table>
        <caption>Valores mensuales de {title}; la tabla conserva los faltantes explícitos.</caption>
        <thead><tr><th scope="col">Mes</th><th scope="col">Valor{unit ? ` (${unit})` : ''}</th><th scope="col">Calidad</th><th scope="col">Motivo / flags</th></tr></thead>
        <tbody>{points.length === 0
          ? <tr><td colSpan={4}>Sin filas: no hay observaciones en la respuesta.</td></tr>
          : points.map((point) => <tr key={point.date}>
            <th scope="row">{monthLabel(point.date)}</th>
            <td>{point.invalidValue ? 'Valor inválido' : valueLabel(point.value, unit)}</td>
            <td>{qualityLabel(point.qualityState)}</td>
            <td>{[point.missingReason, ...point.flags.map((flag) => `${flag.name}: ${String(flag.value)}`)].filter(Boolean).join(' · ') || 'Sin detalle adicional'}</td>
          </tr>)}</tbody>
      </table>
    </div>

    <details className="ssp-provenance">
      <summary>Procedencia y metadatos</summary>
      <dl>
        <dt>Producto</dt><dd>{product.short_name ?? product.product_id ?? 'No informado'}</dd>
        <dt>Versión</dt><dd>{product.product_version ?? 'No informada'}</dd>
        <dt>Variable</dt><dd>{product.variable ?? 'No informada'}</dd>
        <dt>Unidad</dt><dd>{unit ?? 'No informada'}</dd>
        <dt>Agencia</dt><dd>{product.source?.agency ?? 'No informada'}</dd>
        <dt>Colección</dt><dd>{product.source?.collection_id ?? 'No informada'}</dd>
        <dt>DOI</dt><dd>{product.source?.doi ?? 'No informado'}</dd>
        <dt>Estado de verificación QA</dt><dd>{response.quality?.verification_state ? qualityLabel(response.quality.verification_state) : 'No informado'}</dd>
      </dl>
      {product.source?.granule_ids && product.source.granule_ids.length > 0 && <p>Gránulos: {product.source.granule_ids.join(', ')}</p>}
      {response.provenance?.source_sha256 && response.provenance.source_sha256.length > 0 && <p>SHA-256 de fuentes: {response.provenance.source_sha256.join(', ')}</p>}
    </details>
  </section>
}

export default ScientificSeriesPanel

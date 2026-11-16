import { lazy, Suspense, useState } from 'react'
import { COPY } from '../content/exploreCopy'
import { monthsWithLayer, resolveMapTarget } from '../lib/rasterTarget'
import type { RasterResolver } from '../lib/rasterTarget'
import { hasVerifiedContextGeometry, pointFromSupport } from '../lib/contextMap'
import type { ContextGeometryOverlay, MapMarkerDetails } from '../lib/contextMap'
import type { Product, Quality, RasterLayer, SpatialAggregation, YearMonth } from '../types/contracts'
import { MonthTimeline } from './MonthTimeline'
import { RasterLegend } from './RasterLegend'
import { MapCanvasBoundary } from './MapCanvasBoundary'

// MapLibre is only downloaded when the lazy /explore route renders this panel.
const MapCanvas = lazy(() => import('./MapCanvas'))

export interface MapPanelProps {
  layers: RasterLayer[] | undefined
  months: YearMonth[]
  month: YearMonth | null
  resolver: RasterResolver
  onSelectMonth(month: YearMonth): void
  support: SpatialAggregation | null
  product: Product
  quality: Quality
  synthetic: boolean
  /** Local UI adapter for a future verified BE-10 GeoJSON response; never fetched or fabricated here. */
  contextGeometry?: ContextGeometryOverlay | null
}

const LAYER_KINDS = ['value', 'anomaly', 'slope', 'significance'] as const

function markerDetails(props: MapPanelProps): MapMarkerDetails | null {
  const point = pointFromSupport(props.support)
  if (!point) return null
  const imerg = props.product.product_id === 'P02'
  return {
    ...point,
    label: imerg ? 'Muestra puntual IMERG' : `Muestra puntual ${props.product.short_name}`,
    productId: props.product.product_id,
    productName: props.product.short_name,
    productVersion: props.product.product_version,
    unit: props.product.unit,
    synthetic: props.synthetic,
    verificationState: props.quality.verification_state,
    providerFlagsApplied: props.quality.provider_flags_applied,
  }
}

function safeHttpsUrl(value: string): string | null {
  try {
    const url = new URL(value)
    return url.protocol === 'https:' ? url.href : null
  } catch {
    return null
  }
}

export function MapPanel(props: MapPanelProps) {
  const { layers, months, month, resolver, onSelectMonth, support, synthetic, contextGeometry } = props
  const [isPlaying, setPlaying] = useState(false)
  const withLayer = monthsWithLayer(layers, months)
  const target = month === null ? ({ kind: 'absent' } as const) : resolveMapTarget({ layers, months, month, resolver })
  const marker = markerDetails(props)
  const verifiedGeometry = hasVerifiedContextGeometry(contextGeometry) ? contextGeometry : null
  const raster = target.kind === 'frame' ? target.raster : null
  const rasterMessage = target.kind === 'absent'
    ? COPY.map.unavailableNote
    : target.kind === 'month-absent'
      ? COPY.map.monthMissing
      : target.kind === 'not-drawable'
        ? COPY.map.notDrawable
        : null

  return (
    <section className="explore-card explore-map-panel" aria-labelledby="explore-map-title">
      <h3 id="explore-map-title" className="explore-chart__title">{COPY.map.title}</h3>

      <MapCanvasBoundary>
        <Suspense fallback={<p role="status">Cargando mapa geográfico…</p>}>
          <MapCanvas raster={raster} month={month} marker={marker} contextGeometry={verifiedGeometry} />
        </Suspense>
      </MapCanvasBoundary>

      {target.kind === 'frame' && <p className="explore-notice explore-notice--mock">{COPY.map.demoLayer}</p>}

      <div className="explore-map-context" aria-live="polite">
        <p><strong>Mapa geográfico contextual.</strong> El encuadre aproxima Murray–Darling y no dibuja un límite oficial.</p>
        {marker ? (
          <>
            <p className="explore-map-context__point">
              <strong>{marker.label}</strong> · Celda <code>{marker.cellId ?? 'no informada'}</code> · {marker.unit} · soporte <code>point_sample</code>.
            </p>
            <p className="explore-muted">Una muestra puntual no representa un promedio regional. Verificación: {marker.verificationState}; QA del proveedor no aprobada.</p>
            {synthetic && <p className="explore-notice explore-notice--mock">El marcador y la serie son sintéticos y pertenecen a la demostración; no son observaciones NASA.</p>}
          </>
        ) : support?.support_type === 'point_sample' ? (
          <p>Coordenadas no disponibles o inválidas; no se dibuja ningún marcador. No se infiere una ubicación a partir del centro de la cuenca.</p>
        ) : (
          <p>No hay coordenadas de muestra puntual verificadas para esta respuesta.</p>
        )}
        {verifiedGeometry && (
          <p className="explore-muted">
            {verifiedGeometry.label}: referencia cartográfica; no se usa como máscara ni para agregación. Fuente: {verifiedGeometry.attribution}
            {safeHttpsUrl(verifiedGeometry.sourceUrl) && <> · <a href={safeHttpsUrl(verifiedGeometry.sourceUrl)!} target="_blank" rel="noopener noreferrer">ver fuente</a></>}
            {' '}· Licencia {verifiedGeometry.licenseName}
            {safeHttpsUrl(verifiedGeometry.licenseUrl) && <> (<a href={safeHttpsUrl(verifiedGeometry.licenseUrl)!} target="_blank" rel="noopener noreferrer">ver licencia</a>)</>}
            {' '}· versión <code>{verifiedGeometry.geometryVersion}</code> · SHA-256 <code>{verifiedGeometry.sha256}</code>
          </p>
        )}
        {contextGeometry && !verifiedGeometry && <p role="status">Geometría contextual sin procedencia verificable; no se dibuja.</p>}
        {rasterMessage && <p className="explore-map-context__raster"><strong>Capa raster NASA:</strong> {rasterMessage}</p>}
        <p className="explore-map__attribution">
          Mapa base © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap contributors</a> (ODbL).
        </p>
      </div>

      <RasterLegend mode={target.kind === 'frame' ? 'demo' : 'none'} />

      <fieldset className="explore-layers">
        <legend>Capa</legend>
        {LAYER_KINDS.map((kind) => (
          <label key={kind} className={kind === 'value' ? undefined : 'explore-muted'}>
            <input type="radio" name="explore-layer" value={kind} checked={kind === 'value'} readOnly disabled={kind !== 'value'} />{' '}
            {COPY.map.layerTypes[kind]}
            {kind === 'value' ? '' : ` (${COPY.map.layerDisabled.toLowerCase()})`}
          </label>
        ))}
      </fieldset>

      {month !== null && months.length > 0 && (
        <MonthTimeline
          months={months.map((item) => ({ month: item, hasLayer: withLayer.has(item) }))}
          selectedMonth={month}
          onSelectMonth={onSelectMonth}
          isPlaying={isPlaying}
          onPlayingChange={setPlaying}
        />
      )}
    </section>
  )
}

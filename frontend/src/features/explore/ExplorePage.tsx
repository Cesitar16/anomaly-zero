import { useCallback, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import Badge from '../../components/ui/Badge'
import ButtonLink from '../../components/ui/ButtonLink'
import Container from '../../components/ui/Container'
import { ROUTES, SITE } from '../../config/site'
import useDocumentTitle from '../../hooks/useDocumentTitle'
import { AnalysisUnavailable } from './components/AnalysisUnavailable'
import { CoverageSummary } from './components/CoverageSummary'
import { DataSourceSwitch } from './components/DataSourceSwitch'
import { DemoScenarios } from './components/DemoScenarios'
import { ErrorState } from './components/ErrorState'
import { ExploreFilters } from './components/ExploreFilters'
import { FiltersPanel } from './components/FiltersPanel'
import { MapPanel } from './components/MapPanel'
import { MonthDetail } from './components/MonthDetail'
import { MockDataNotice } from './components/MockDataNotice'
import { QualityNotice } from './components/QualityNotice'
import { SeriesTable } from './components/SeriesTable'
import { SourceProvenance } from './components/SourceProvenance'
import { SeriesCsvDownload } from './components/SeriesCsvDownload'
import { MultivariableComparison } from './components/MultivariableComparison'
import { SupportNotice } from './components/SupportNotice'
import { TimeSeriesChart } from './components/TimeSeriesChart'
import { COPY, DEMO_SCENARIOS, productLabel } from './content/exploreCopy'
import type { DemoScenarioId } from './content/exploreCopy'
import { createExploreApi, defaultSource } from './data/createExploreApi'
import { useExplorer } from './hooks/useExplorer'
import { toChartPoints } from './lib/chartModel'
import { isExploreSource } from './lib/exploreUrl'
import type { ExploreSource } from './lib/exploreUrl'
import type { SeriesResponse } from './types/contracts'
import './explore.css'

function isScenario(value: string | null): value is DemoScenarioId {
  return value !== null && (DEMO_SCENARIOS as string[]).includes(value)
}

function stateLabel(series: SeriesResponse): string {
  switch (series.data_state) {
    case 'available':
      return COPY.state.complete
    case 'available_with_gaps':
      return COPY.state.gaps
    case 'no_data':
      return COPY.state.noData
  }
}

/**
 * /explore: panel de filtros plegable a la izquierda y, a su derecha, la franja de estado, la serie mensual, el
 * detalle del mes, el mapa (o su ausencia honesta), la tabla, la cobertura, la calidad, la procedencia y el
 * análisis no disponible. Todo pasa por `ExploreApi`; por defecto es el servicio simulado (datos sintéticos).
 */
export default function ExplorePage() {
  const [params, setParams] = useSearchParams()
  const requestedSource = params.get('fuente')
  const source: ExploreSource = isExploreSource(requestedSource) ? requestedSource : defaultSource()
  const requested = params.get('demo')
  // Los escenarios solo existen en el servicio simulado.
  const scenario = source === 'demo' && isScenario(requested) ? requested : null
  const api = useMemo(() => createExploreApi(source, scenario), [source, scenario])
  const explorer = useExplorer(api, scenario)
  const { series, regions } = explorer
  const isMock = api.mode === 'mock'
  const [filtersOpen, setFiltersOpen] = useState(true)

  useDocumentTitle(`${COPY.page.title} | ${SITE.name}`)

  const changeScenario = useCallback(
    (next: string | null) => {
      const updated = new URLSearchParams(params)
      if (next === null) updated.delete('demo')
      else updated.set('demo', next)
      setParams(updated)
    },
    [params, setParams],
  )

  const changeSource = useCallback(
    (next: ExploreSource) => {
      // Los identificadores de un servicio no existen en el otro: se parte de cero y se conserva solo la fuente.
      setParams(new URLSearchParams({ fuente: next }))
    },
    [setParams],
  )

  const points = series.status === 'success' ? toChartPoints(series.data.series) : []
  const noCatalog = regions.status === 'success' && regions.data.length === 0
  const regionName =
    regions.status === 'success'
      ? (regions.data.find((region) => region.region_id === explorer.draft.regionId)?.name ?? null)
      : null
  const productItem =
    explorer.products.status === 'success'
      ? explorer.products.data.find((product) => product.product_id === explorer.draft.productId)
      : undefined
  const summary = {
    region: regionName,
    product: productItem ? productLabel(productItem) : null,
    range:
      explorer.draft.start !== '' && explorer.draft.end !== ''
        ? `${explorer.draft.start} a ${explorer.draft.end}`
        : null,
    site: params.get('site_id') ? `Sitio ${params.get('site_id')}` : null,
  }

  return (
    <section className="explore" aria-labelledby="explore-titulo">
      <Container>
        <div className="explore__header">
          <h1 id="explore-titulo" className="explore__title" tabIndex={-1}>
            {COPY.page.title} {isMock && <Badge status="in-progress">{COPY.page.badgeDemo}</Badge>}
          </h1>
          <p className="explore__lead">{isMock ? COPY.page.leadMock : COPY.page.leadHttp}</p>
        </div>

        {(isMock || (series.status === 'success' && series.data.synthetic)) && <MockDataNotice />}

        <div className={filtersOpen ? 'explore-layout' : 'explore-layout explore-layout--collapsed'}>
          <div className="explore-layout__aside">
            <FiltersPanel open={filtersOpen} onToggle={() => setFiltersOpen((open) => !open)} summary={summary}>
              <ExploreFilters
                regions={explorer.regions}
                products={explorer.products}
                draft={explorer.draft}
                errors={explorer.fieldErrors}
                dirty={explorer.dirty}
                busy={series.status === 'loading'}
                onRegion={explorer.setRegion}
                onProduct={explorer.setProduct}
                onStart={explorer.setStart}
                onEnd={explorer.setEnd}
                onSubmit={explorer.submit}
                onRetryCatalog={explorer.retryCatalog}
              />
              {source === 'api' && (
                <div className="explore-site-select">
                  <label htmlFor="explore-site">Sitio candidato DS-09</label>
                  <select
                    id="explore-site"
                    value={params.get('site_id') ?? ''}
                    onChange={(event) => {
                      const updated = new URLSearchParams(params)
                      if (event.target.value) updated.set('site_id', event.target.value)
                      else updated.delete('site_id')
                      setParams(updated)
                    }}
                  >
                    <option value="">Selecciona un sitio candidato</option>
                    <option value="site_west_extent">Extensión oeste (no aprobado)</option>
                    <option value="site_central_extent">Extensión central (no aprobado)</option>
                    <option value="site_east_extent">Extensión este (no aprobado)</option>
                  </select>
                  <p role="note">Las celdas de cada producto son distintas; las relaciones y correlaciones siguen deshabilitadas.</p>
                </div>
              )}
              <DataSourceSwitch source={source} onChange={changeSource} />
            </FiltersPanel>
          </div>

          <div className="explore-layout__main">
            {explorer.submitted && <SeriesCsvDownload api={api} series={series} dirty={explorer.dirty} />}

            {noCatalog ? (
              <div className="explore-placeholder" role="note">
                <p className="explore-placeholder__title">{COPY.empty.regions}</p>
                <p>{COPY.empty.regionsNote}</p>
              </div>
            ) : !explorer.submitted ? (
              <p className="explore-idle" role="status">
                {explorer.draft.regionId === '' ? COPY.filters.needRegion : COPY.filters.idle}
              </p>
            ) : series.status === 'loading' || series.status === 'idle' ? (
              <p className="explore-idle" role="status" aria-busy="true">
                {COPY.filters.submitBusy}
              </p>
            ) : series.status === 'error' ? (
              <ErrorState failure={series.failure} onRetry={explorer.retrySeries} headingLevel="h2" />
            ) : (
              <SeriesResult series={series.data} points={points} explorer={explorer} />
            )}

            {source === 'api' && params.get('site_id') && explorer.submitted && !explorer.dirty && series.status === 'success' && series.data.data_state !== 'no_data' && (
              <MultivariableComparison
                api={api}
                query={{
                  regionId: series.data.region.region_id,
                  productId: series.data.product.product_id,
                  start: series.data.requested_coverage.start,
                  end: series.data.requested_coverage.end,
                  siteId: params.get('site_id') ?? undefined,
                }}
              />
            )}

            {isMock && <DemoScenarios scenario={scenario} onChange={changeScenario} />}
          </div>
        </div>

        <div className="explore__actions">
          <ButtonLink to={ROUTES.home} variant="secondary">
            {COPY.page.back}
          </ButtonLink>
        </div>
      </Container>
    </section>
  )
}

function SeriesResult({
  series,
  points,
  explorer,
}: {
  series: SeriesResponse
  points: ReturnType<typeof toChartPoints>
  explorer: ReturnType<typeof useExplorer>
}) {
  const { month, months } = explorer
  const noData = series.data_state === 'no_data'
  return (
    <>
      <section className="explore-results" aria-labelledby="explore-results-title">
        <h2 id="explore-results-title" className="explore-panel__title">
          Resultado
        </h2>
        <div className={noData ? 'explore-notice explore-status explore-notice--warn' : 'explore-notice explore-status'} role="status">
          <strong>{stateLabel(series)}.</strong>{' '}
          {series.data_state === 'available_with_gaps'
            ? COPY.state.gapsText(series.coverage.missing_periods.length, series.coverage.expected_periods)
            : noData
              ? COPY.state.noDataText
              : ''}
          {series.message ? ` ${series.message}` : ''}
        </div>

        {!noData && (
          <>
            <SupportNotice support={series.spatial_aggregation} quantity={series.product.quantity} />
            <div className="explore-results__layout">
              <div className="explore-results__col">
                <div className="explore-slot explore-slot--chart">
                  <TimeSeriesChart
                    points={points}
                    quantity={series.product.quantity}
                    unit={series.product.unit}
                    selectedMonth={month}
                    onSelectMonth={explorer.selectMonth}
                  />
                </div>
                <div className="explore-slot explore-slot--table">
                  <h3 className="explore-chart__title">Datos mes a mes</h3>
                  <SeriesTable points={points} unit={series.product.unit} selectedMonth={month} />
                </div>
              </div>
              <div className="explore-results__col">
                <div className="explore-slot explore-slot--detail">
                  <MonthDetail
                    point={points.find((point) => point.month === month) ?? null}
                    unit={series.product.unit}
                    support={series.spatial_aggregation}
                  />
                </div>
                <div className="explore-slot explore-slot--map">
                  <MapPanel
                    layers={series.raster_layers}
                    months={months}
                    month={month}
                    resolver={explorer.api.capabilities.raster}
                    onSelectMonth={explorer.selectMonth}
                    support={series.spatial_aggregation}
                    product={series.product}
                    quality={series.quality}
                    synthetic={series.synthetic}
                  />
                </div>
              </div>
            </div>
          </>
        )}
      </section>

      <div className="explore-cards">
        <CoverageSummary
          coverage={series.coverage}
          requested={series.requested_coverage}
          available={series.available_coverage}
        />
        <QualityNotice quality={series.quality} />
        <SourceProvenance product={series.product} provenance={series.provenance} datasetId={series.dataset_id} />
        <AnalysisUnavailable
          support={series.spatial_aggregation}
          onProbe={explorer.api.capabilities.analyses ? explorer.probeAnalysis : undefined}
          probe={explorer.analysis}
        />
      </div>
    </>
  )
}

import { useCallback, useMemo } from 'react'
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
import { MapPanel } from './components/MapPanel'
import { MockDataNotice } from './components/MockDataNotice'
import { QualityNotice } from './components/QualityNotice'
import { SeriesTable } from './components/SeriesTable'
import { SourceProvenance } from './components/SourceProvenance'
import { SeriesCsvDownload } from './components/SeriesCsvDownload'
import { SupportNotice } from './components/SupportNotice'
import { TimeSeriesChart } from './components/TimeSeriesChart'
import { COPY, DEMO_SCENARIOS } from './content/exploreCopy'
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
 * /explore: filtros, serie mensual, mapa (o su ausencia honesta), tabla, cobertura, calidad, procedencia y
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

        <DataSourceSwitch source={source} onChange={changeSource} />

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

        {isMock && <DemoScenarios scenario={scenario} onChange={changeScenario} />}

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
        <div className={noData ? 'explore-notice explore-notice--warn' : 'explore-notice'} role="status">
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
            <div className="explore-results__grid">
              <TimeSeriesChart
                points={points}
                quantity={series.product.quantity}
                unit={series.product.unit}
                selectedMonth={month}
                onSelectMonth={explorer.selectMonth}
              />
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
            <h3 className="explore-chart__title">Datos mes a mes</h3>
            <SeriesTable points={points} unit={series.product.unit} selectedMonth={month} />
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

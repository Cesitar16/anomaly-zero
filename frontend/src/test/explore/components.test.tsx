import { fireEvent, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AnalysisUnavailable } from '../../features/explore/components/AnalysisUnavailable'
import { CoverageSummary } from '../../features/explore/components/CoverageSummary'
import { ErrorState } from '../../features/explore/components/ErrorState'
import { ExploreFilters } from '../../features/explore/components/ExploreFilters'
import { MapPanel } from '../../features/explore/components/MapPanel'
import { MonthTimeline } from '../../features/explore/components/MonthTimeline'
import { QualityNotice } from '../../features/explore/components/QualityNotice'
import { SeriesTable } from '../../features/explore/components/SeriesTable'
import { SourceProvenance } from '../../features/explore/components/SourceProvenance'
import { SupportNotice } from '../../features/explore/components/SupportNotice'
import { TimeSeriesChart } from '../../features/explore/components/TimeSeriesChart'
import { productsAll, regionsOne } from '../../features/explore/data/fixtures/derived'
import { error503SnapshotUnavailable, seriesNoData, seriesPointSample } from '../../features/explore/data/fixtures/official'
import { error404NotFound, error500Internal } from '../../features/explore/data/fixtures/derived'
import { toChartPoints } from '../../features/explore/lib/chartModel'
import type { RasterLayer, Quality, ErrorResponse } from '../../features/explore/types/contracts'

// MapLibre no corre en jsdom (necesita WebGL): el lienzo se reemplaza por un marcador.
vi.mock('../../features/explore/components/MapCanvas', () => ({
  default: ({ month }: { month: string }) => <div data-testid="map-canvas">{month}</div>,
}))

afterEach(() => vi.useRealTimers())

const points = toChartPoints(seriesPointSample.series)

describe('SeriesTable', () => {
  it('escribe el cero como «0 (cero válido)» y el null como «Sin dato», nunca como "null"', () => {
    const { container } = render(<SeriesTable points={points} unit="mm/hr" selectedMonth="2005-02" />)
    const table = screen.getByRole('table')
    expect(within(table).getByText('0 (cero válido)')).toBeInTheDocument()
    const gap = points.find((point) => point.value === null)!
    const gapRow = within(table).getByRole('row', { name: new RegExp(gap.month) })
    expect(within(gapRow).getAllByRole('cell')[0]).toHaveTextContent('Sin dato')
    expect(container.textContent).not.toMatch(/null|undefined|NaN/)
    expect(within(table).getAllByRole('row')).toHaveLength(points.length + 1)
  })

  it('marca el mes seleccionado y avisa si no hay meses', () => {
    const { rerender } = render(<SeriesTable points={points} unit="mm/hr" selectedMonth="2005-02" />)
    expect(document.querySelector('tr[aria-current="true"]')).toHaveTextContent('2005-02')
    rerender(<SeriesTable points={[]} unit="mm/hr" selectedMonth={null} />)
    expect(screen.queryByRole('table')).toBeNull()
    expect(screen.getByText(/Sin meses para mostrar/)).toBeInTheDocument()
  })
})

describe('QualityNotice', () => {
  it('no evaluada: se muestra como advertencia y jamás dice "aprobada"', () => {
    const quality: Quality = { ...seriesPointSample.quality, verification_state: 'unassessed' }
    const { container } = render(<QualityNotice quality={quality} />)
    expect(screen.getByText(/Calidad no evaluada/)).toHaveClass('explore-notice--warn')
    expect(container.textContent).not.toMatch(/aprobad/i)
  })

  it('solo controles básicos: no afirma calidad del proveedor', () => {
    const quality: Quality = { ...seriesPointSample.quality, verification_state: 'basic_checks_only', provider_flags_applied: false }
    render(<QualityNotice quality={quality} />)
    expect(screen.getByText(/Solo controles básicos/)).toBeInTheDocument()
    expect(screen.getByText(/No se aplicó la calidad del proveedor/)).toBeInTheDocument()
  })

  it('sin qa_checks: dice que no hay controles y que eso no significa que la calidad pasó', () => {
    const quality: Quality = { ...seriesPointSample.quality }
    delete quality.qa_checks
    render(<QualityNotice quality={quality} />)
    expect(screen.getByText(/Eso no significa que la calidad haya pasado/)).toBeInTheDocument()
  })

  it('los atributos de esquema libre null se escriben «No informado»', () => {
    const quality: Quality = {
      ...seriesPointSample.quality,
      source_missing_attributes: { fill_value: null, missing_value: null, scale_factor: 1, add_offset: 0 },
    }
    render(<QualityNotice quality={quality} />)
    expect(screen.getAllByText('No informado').length).toBeGreaterThanOrEqual(2)
    expect(screen.getByText('Desplazamiento').nextSibling).toHaveTextContent('0')
  })
})

describe('SupportNotice', () => {
  it('serie de un punto: se rotula muestra, no promedio de la región', () => {
    render(<SupportNotice support={seriesPointSample.spatial_aggregation} quantity="monthly_mean_rate" />)
    expect(screen.getByText('Muestra NASA exploratoria. Es el valor de un solo punto, no el promedio validado de la cuenca.')).toBeInTheDocument()
    expect(screen.getByText(/No es el promedio de la región/)).toBeInTheDocument()
    expect(screen.getByText(/coordenadas no informadas/)).toBeInTheDocument()
  })

  it('promedio descriptivo y agregado aprobado se distinguen', () => {
    const { rerender } = render(
      <SupportNotice
        support={{ support_type: 'descriptive_mean', approval_state: 'descriptive_only', method: 'media simple', cell_count: 12, area_weighted: false, weighting_reference: null, mask_version: null }}
        quantity="monthly_mean_rate"
      />,
    )
    expect(screen.getByText(/Promedio descriptivo, sin aprobación/)).toBeInTheDocument()
    rerender(
      <SupportNotice
        support={{ support_type: 'regional_aggregate', approval_state: 'approved', method: 'm', area_weighted: true, weighting_reference: 'w', mask_version: 'v1', approval_reference: 'AZ-99' }}
        quantity="monthly_mean_rate"
      />,
    )
    expect(screen.getByText(/Agregado regional aprobado/)).toBeInTheDocument()
    expect(screen.getByText(/AZ-99/)).toBeInTheDocument()
  })

  it('sin soporte (no_data) no muestra nada', () => {
    const { container } = render(<SupportNotice support={null} quantity="x" />)
    expect(container).toBeEmptyDOMElement()
  })
})

describe('CoverageSummary y SourceProvenance', () => {
  it('cobertura cuenta meses y lista los que faltan; el backend actual omite la cobertura espacial', () => {
    render(
      <CoverageSummary coverage={seriesPointSample.coverage} requested={seriesPointSample.requested_coverage} available={seriesPointSample.available_coverage} />,
    )
    expect(screen.getByText('Meses pedidos').nextSibling).toHaveTextContent('3')
    expect(screen.getByText('Meses sin dato').nextSibling).toHaveTextContent('1')
    expect(screen.getByText(/La cobertura cuenta meses; no mide el área/)).toBeInTheDocument()
    expect(screen.queryByText('Celdas evaluadas')).toBeNull()
  })

  it('procedencia: DOI enlazado y huellas; sin snapshot lo dice', () => {
    const { rerender } = render(<SourceProvenance product={seriesPointSample.product} provenance={seriesPointSample.provenance} datasetId={seriesPointSample.dataset_id} />)
    expect(screen.getByRole('link', { name: new RegExp(seriesPointSample.product.source.doi ?? '10.') })).toHaveAttribute('href', expect.stringMatching(/^https:\/\/doi\.org\/10\./))
    rerender(<SourceProvenance product={seriesNoData.product} provenance={null} datasetId={null} />)
    expect(screen.getByText(/no hay un snapshot verificado/i)).toBeInTheDocument()
    expect(document.body.textContent).not.toMatch(/null|undefined/)
  })
})

describe('ErrorState', () => {
  it('503 reintentable: ofrece reintentar y no habla de "sin datos"', async () => {
    const onRetry = vi.fn()
    render(<ErrorState failure={{ kind: 'api', httpStatus: 503, body: error503SnapshotUnavailable }} onRetry={onRetry} />)
    expect(screen.getByRole('alert')).toHaveTextContent('Los datos no están disponibles por ahora')
    expect(screen.getByRole('alert')).not.toHaveTextContent(/sin datos/i)
    await userEvent.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(onRetry).toHaveBeenCalledOnce()
  })

  it('500 no reintentable: sin botón de reintento', () => {
    render(<ErrorState failure={{ kind: 'api', httpStatus: 500, body: error500Internal }} onRetry={vi.fn()} />)
    expect(screen.queryByRole('button')).toBeNull()
    expect(screen.getByText('INTERNAL_ERROR')).toBeInTheDocument()
  })

  it('404 y sin respuesta tienen su propio texto', () => {
    const { rerender } = render(<ErrorState failure={{ kind: 'api', httpStatus: 404, body: error404NotFound }} />)
    expect(screen.getByRole('alert')).toHaveTextContent('No encontramos lo que pediste')
    rerender(<ErrorState failure={{ kind: 'network' }} onRetry={vi.fn()} />)
    expect(screen.getByRole('alert')).toHaveTextContent('No pudimos conectar')
    expect(screen.getByRole('button', { name: 'Reintentar' })).toBeInTheDocument()
  })

  it('INVALID_PARAMETER nombra el campo que falló', () => {
    const body: ErrorResponse = { ...error503SnapshotUnavailable, error: { ...error503SnapshotUnavailable.error, code: 'INVALID_PARAMETER', retryable: false, details: { field: 'end' } } }
    render(<ErrorState failure={{ kind: 'api', httpStatus: 422, body }} />)
    expect(screen.getByRole('alert')).toHaveTextContent('«Hasta»')
  })
})

describe('AnalysisUnavailable', () => {
  it('el control está deshabilitado y no hay ningún resultado estadístico', () => {
    const { container } = render(<AnalysisUnavailable support={seriesPointSample.spatial_aggregation} />)
    expect(screen.getByRole('button', { name: 'Calcular tendencia' })).toBeDisabled()
    expect(screen.getByText(/Una serie de un solo punto no equivale a una tendencia/)).toBeInTheDocument()
    expect(container.textContent).not.toMatch(/p\s*[=<]\s*0|pendiente\s*[=:]\s*-?\d|intervalo.*\d/i)
    expect(screen.queryByRole('button', { name: /Ver la respuesta/ })).toBeNull()
  })

  it('con servicio simulado: muestra el 409 sin identificador ni método', async () => {
    const onProbe = vi.fn()
    const body = { ...error503SnapshotUnavailable, error: { ...error503SnapshotUnavailable.error, code: 'ANALYSIS_METHOD_UNAVAILABLE' as const, retryable: false, details: { analysis: { state: 'not_available' as const, analysis_id: null, dataset_id: 'd', region_id: 'r', product_id: 'p', window: { start: '2005-01', end: '2005-03', end_inclusive: true as const }, method: null, metrics: {} as never } } } }
    render(<AnalysisUnavailable support={null} onProbe={onProbe} probe={{ status: 'error', failure: { kind: 'api', httpStatus: 409, body } }} />)
    await userEvent.click(screen.getByRole('button', { name: /Ver la respuesta/ }))
    expect(onProbe).toHaveBeenCalledOnce()
    expect(screen.getByText('ANALYSIS_METHOD_UNAVAILABLE')).toBeInTheDocument()
    expect(screen.getByText('No se creó')).toBeInTheDocument()
    expect(screen.getByText('Ninguno habilitado')).toBeInTheDocument()
    expect(screen.getAllByText(/No calculad[ao]/)).toHaveLength(3)
  })
})

describe('TimeSeriesChart', () => {
  it('es una imagen con nombre y descripción textual; la tabla es su equivalente', () => {
    render(<TimeSeriesChart points={points} quantity="monthly_mean_rate" unit="mm/hr" selectedMonth="2005-01" onSelectMonth={vi.fn()} />)
    const chart = screen.getByRole('img', { name: /Serie mensual: tasa media mensual/ })
    expect(chart).toHaveAccessibleDescription(/3 meses, de 2005-01 a 2005-03/)
    expect(chart).toHaveAccessibleDescription(/sin dato/)
    expect(chart).toHaveAccessibleDescription(/cero válido/)
    expect(screen.getByText(/No es el total acumulado del mes/)).toBeInTheDocument()
    expect(screen.getByText(/Las franjas ámbar marcan meses sin dato/)).toBeInTheDocument()
  })
})

describe('MapPanel: ausencia honesta de capas raster', () => {
  const months = ['2005-01', '2005-02', '2005-03']
  const layer = (date: string, over: Partial<RasterLayer> = {}): RasterLayer => ({ dataset_id: 'ds', date, layer_type: 'value', unit: 'mm/hr', state: 'available', format: 'image/png', tile_template: `/x/${date}.png`, ...over })
  const draw = (item: RasterLayer) => ({ url: item.tile_template ?? '', bbox: { west: 0, south: 0, east: 1, north: 1 } })

  it('sin raster_layers (el backend de hoy): no hay mapa, ni leyenda de color, ni lienzo', () => {
    const { container } = render(<MapPanel layers={undefined} months={months} month="2005-01" resolver={() => null} onSelectMonth={vi.fn()} />)
    expect(screen.getByText('Sin capa geográfica disponible para este mes.')).toBeInTheDocument()
    expect(screen.getByText(/La API todavía no publica una capa de mapa/)).toBeInTheDocument()
    expect(screen.getByText(/no se dibuja una escala/)).toBeInTheDocument()
    expect(screen.queryByTestId('map-canvas')).toBeNull()
    expect(container.querySelector('.explore-legend__bar')).toBeNull()
    expect(container.querySelector('canvas, img')).toBeNull()
  })

  it('solo la capa de valor está habilitada; el resto figura como no disponible', () => {
    render(<MapPanel layers={undefined} months={months} month="2005-01" resolver={() => null} onSelectMonth={vi.fn()} />)
    expect(screen.getByRole('radio', { name: 'Valor' })).toBeEnabled()
    for (const name of [/Anomalía/, /Tendencia \(pendiente\)/, /Significancia/]) {
      expect(screen.getByRole('radio', { name })).toBeDisabled()
    }
  })

  it('mes con capa: dibuja y avisa que la capa es sintética', async () => {
    render(<MapPanel layers={[layer('2005-01'), layer('2005-03')]} months={months} month="2005-01" resolver={draw} onSelectMonth={vi.fn()} />)
    expect(await screen.findByTestId('map-canvas')).toHaveTextContent('2005-01')
    expect(screen.getByText(/Capa sintética de demostración/)).toBeInTheDocument()
    expect(screen.getByText(/La escala de colores es de demostración/)).toBeInTheDocument()
  })

  it('mes sin capa: se declara ausente y NO se deja la capa de otro mes', () => {
    render(<MapPanel layers={[layer('2005-01'), layer('2005-02', { state: 'unavailable', format: null, tile_template: null }), layer('2005-03')]} months={months} month="2005-02" resolver={draw} onSelectMonth={vi.fn()} />)
    expect(screen.getByText(/Este mes no tiene capa en la API/)).toBeInTheDocument()
    expect(screen.queryByTestId('map-canvas')).toBeNull()
  })

  it('capa declarada pero con formato que esta versión no sabe leer: no se dibuja', () => {
    render(<MapPanel layers={[layer('2005-01')]} months={months} month="2005-01" resolver={() => null} onSelectMonth={vi.fn()} />)
    expect(screen.getByText(/todavía no sabe dibujarla/)).toBeInTheDocument()
    expect(screen.queryByTestId('map-canvas')).toBeNull()
  })

  it('el selector de mes funciona aunque no haya capas', async () => {
    const onSelectMonth = vi.fn()
    render(<MapPanel layers={undefined} months={months} month="2005-01" resolver={() => null} onSelectMonth={onSelectMonth} />)
    await userEvent.click(screen.getByRole('button', { name: 'Mes siguiente' }))
    expect(onSelectMonth).toHaveBeenCalledWith('2005-02')
  })
})

describe('MonthTimeline', () => {
  const timeline = (withLayer: boolean[]) => withLayer.map((hasLayer, index) => ({ month: `2005-0${index + 1}`, hasLayer }))

  it('Reproducir exige al menos 2 meses con capa y explica por qué', () => {
    const { rerender } = render(<MonthTimeline months={timeline([true, false, false])} selectedMonth="2005-01" onSelectMonth={vi.fn()} isPlaying={false} onPlayingChange={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Reproducir' })).toBeDisabled()
    expect(screen.getByText(/Reproducir necesita al menos 2 meses con capa/)).toBeInTheDocument()
    rerender(<MonthTimeline months={timeline([true, false, true])} selectedMonth="2005-01" onSelectMonth={vi.fn()} isPlaying={false} onPlayingChange={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Reproducir' })).toBeEnabled()
  })

  it('reproduce mes a mes, un salto por vez, y se detiene en el último', () => {
    vi.useFakeTimers()
    const onSelectMonth = vi.fn()
    const onPlayingChange = vi.fn()
    const { rerender } = render(<MonthTimeline months={timeline([true, true, true])} selectedMonth="2005-01" onSelectMonth={onSelectMonth} isPlaying onPlayingChange={onPlayingChange} playIntervalMs={500} />)
    vi.advanceTimersByTime(500)
    expect(onSelectMonth).toHaveBeenCalledWith('2005-02')
    rerender(<MonthTimeline months={timeline([true, true, true])} selectedMonth="2005-03" onSelectMonth={onSelectMonth} isPlaying onPlayingChange={onPlayingChange} playIntervalMs={500} />)
    expect(onPlayingChange).toHaveBeenCalledWith(false)
  })

  it('el control deslizante anuncia el mes y si tiene capa', () => {
    render(<MonthTimeline months={timeline([true, false, true])} selectedMonth="2005-02" onSelectMonth={vi.fn()} isPlaying={false} onPlayingChange={vi.fn()} />)
    const slider = screen.getByRole('slider', { name: 'Mes (AAAA-MM)' })
    expect(slider).toHaveAttribute('aria-valuetext', '2005-02, sin capa')
    fireEvent.change(slider, { target: { value: '2' } })
  })
})

describe('ExploreFilters', () => {
  const noop = vi.fn()
  const handlers = { onRegion: noop, onProduct: noop, onStart: noop, onEnd: noop, onSubmit: noop, onRetryCatalog: noop }
  const base = {
    regions: { status: 'success', data: regionsOne.regions } as const,
    products: { status: 'success', data: productsAll.products } as const,
    draft: { regionId: 'REG01', productId: '', start: '', end: '' },
    errors: {},
    dirty: false,
    busy: false,
    ...handlers,
  }

  it('los errores quedan asociados a su campo (aria-invalid y aria-describedby)', () => {
    render(<ExploreFilters {...base} errors={{ product: 'Elige una variable.', start: 'Mes no válido. Usa AAAA-MM.' }} />)
    const product = screen.getByLabelText('Variable NASA')
    expect(product).toHaveAttribute('aria-invalid', 'true')
    expect(product).toHaveAccessibleDescription(/Elige una variable/)
    expect(screen.getByLabelText('Desde')).toHaveAccessibleDescription(/Mes no válido/)
    expect(screen.getByLabelText('Hasta')).not.toHaveAttribute('aria-invalid')
  })

  it('un producto no disponible se puede elegir, con su aviso', () => {
    render(<ExploreFilters {...base} draft={{ ...base.draft, productId: 'P01' }} />)
    expect(screen.getByRole('option', { name: /Temperatura del aire a 2 m \(MERRA-2\) · K \(No disponible\)/ })).toBeInTheDocument()
    expect(screen.getByLabelText('Variable NASA')).toHaveAccessibleDescription(/figura como no disponible/)
  })

  it('mientras envía no permite enviar de nuevo; si cambió algo lo avisa', () => {
    const { rerender } = render(<ExploreFilters {...base} busy />)
    expect(screen.getByRole('button', { name: 'Cargando serie' })).toBeDisabled()
    rerender(<ExploreFilters {...base} dirty />)
    expect(screen.getByRole('status')).toHaveTextContent('Cambiaste los filtros')
  })

  it('catálogo cargando o vacío usa textos honestos', () => {
    const { rerender } = render(<ExploreFilters {...base} regions={{ status: 'loading' }} products={{ status: 'idle' }} draft={{ ...base.draft, regionId: '' }} />)
    expect(screen.getByRole('option', { name: 'Cargando regiones' })).toBeInTheDocument()
    rerender(<ExploreFilters {...base} regions={{ status: 'success', data: [] }} products={{ status: 'idle' }} draft={{ ...base.draft, regionId: '' }} />)
    expect(screen.getByRole('option', { name: 'Sin regiones publicadas' })).toBeInTheDocument()
    expect(screen.getByLabelText('Región')).toBeDisabled()
  })
})

describe('Render en ruta (el ErrorState no depende del router)', () => {
  it('monta dentro de un MemoryRouter sin romper', () => {
    render(<MemoryRouter><ErrorState failure={{ kind: 'network' }} /></MemoryRouter>)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })
})

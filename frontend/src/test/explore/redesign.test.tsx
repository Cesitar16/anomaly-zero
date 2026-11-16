import { configure, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { useState } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi, type MockInstance } from 'vitest'
import App from '../../App'
import { FiltersPanel } from '../../features/explore/components/FiltersPanel'
import { MonthDetail } from '../../features/explore/components/MonthDetail'
import { seriesPointSample } from '../../features/explore/data/fixtures/official'
import { toChartPoints } from '../../features/explore/lib/chartModel'

configure({ asyncUtilTimeout: 6000 })
vi.setConfig({ testTimeout: 20000 })

// MapLibre no corre en jsdom (necesita WebGL): el lienzo se reemplaza por un marcador.
vi.mock('../../features/explore/components/MapCanvas', () => ({
  default: ({ month }: { month: string }) => <div data-testid="map-canvas">{month}</div>,
}))

const points = toChartPoints(seriesPointSample.series)
const withValue = points.find((point) => point.value !== null && point.value > 0)!
const zero = points.find((point) => point.value === 0)!
const gap = points.find((point) => point.value === null)!
const support = seriesPointSample.spatial_aggregation

describe('MonthDetail', () => {
  it('mes con valor: lo escribe con su unidad, dice que es la muestra de un punto y no un promedio', () => {
    const { container } = render(<MonthDetail point={withValue} unit="mm/hr" support={support} />)
    const card = screen.getByRole('region', { name: 'Detalle del mes' })
    expect(within(card).getByText('Con valor')).toBeInTheDocument()
    expect(within(card).getByText('mm/hr')).toBeInTheDocument()
    expect(within(card).getByText('Muestra de un punto, no el promedio de la región')).toBeInTheDocument()
    expect(container.textContent).not.toMatch(/null|undefined|NaN/)
  })

  it('cero: es un valor válido, no un dato faltante', () => {
    render(<MonthDetail point={zero} unit="mm/hr" support={support} />)
    expect(screen.getByText('Cero válido')).toBeInTheDocument()
    expect(screen.getByText(/No es un dato faltante/)).toBeInTheDocument()
    expect(screen.getByText('0')).toBeInTheDocument()
    expect(screen.queryByText('Sin dato')).toBeNull()
  })

  it('sin dato: no muestra número ni unidad y dice que el hueco no es cero', () => {
    const { container } = render(<MonthDetail point={gap} unit="mm/hr" support={support} />)
    const card = screen.getByRole('region', { name: 'Detalle del mes' })
    expect(within(card).getAllByText('Sin dato').length).toBeGreaterThan(0)
    expect(within(card).getByText(/no como cero/)).toBeInTheDocument()
    expect(within(card).queryByText('mm/hr')).toBeNull()
    expect(container.textContent).not.toMatch(/null|undefined|NaN/)
  })

  it('las coordenadas que el servicio no informa se escriben «No informado»', () => {
    render(<MonthDetail point={withValue} unit="mm/hr" support={support} />)
    if (support?.support_type === 'point_sample' && support.point.latitude === null) {
      expect(screen.getByText('Coordenadas').nextElementSibling).toHaveTextContent('No informado')
    }
  })

  it('sin mes elegido no dibuja nada', () => {
    const { container } = render(<MonthDetail point={null} unit="mm/hr" support={support} />)
    expect(container).toBeEmptyDOMElement()
  })
})

describe('FiltersPanel', () => {
  function Harness() {
    const [open, setOpen] = useState(true)
    return (
      <FiltersPanel
        open={open}
        onToggle={() => setOpen((value) => !value)}
        summary={{ region: 'Región sintética', product: 'Precipitación (IMERG Final)', range: '2005-01 a 2005-03', site: 'Sitio site_central_extent' }}
      >
        <label>
          Campo <input type="text" />
        </label>
      </FiltersPanel>
    )
  }

  it('abierto muestra el formulario; plegado lo oculta y resume lo elegido en etiquetas', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    const toggle = screen.getByRole('button', { name: 'Ocultar filtros' })
    expect(toggle).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByLabelText('Campo')).toBeVisible()
    expect(screen.queryByRole('list', { name: 'Filtros elegidos' })).toBeNull()

    await user.click(toggle)
    const show = screen.getByRole('button', { name: 'Mostrar filtros' })
    expect(show).toHaveAttribute('aria-expanded', 'false')
    expect(screen.getByLabelText('Campo')).not.toBeVisible()
    const chips = within(screen.getByRole('list', { name: 'Filtros elegidos' })).getAllByRole('listitem')
    expect(chips.map((chip) => chip.textContent)).toEqual([
      'Región sintética',
      'Precipitación (IMERG Final)',
      '2005-01 a 2005-03',
      'Sitio site_central_extent',
    ])

    await user.click(show)
    expect(screen.getByLabelText('Campo')).toBeVisible()
  })

  it('el botón controla el cuerpo del panel (aria-controls apunta a él)', () => {
    render(<Harness />)
    const toggle = screen.getByRole('button', { name: 'Ocultar filtros' })
    const body = document.getElementById(toggle.getAttribute('aria-controls')!)
    expect(body).not.toBeNull()
    expect(body).toContainElement(screen.getByLabelText('Campo'))
  })
})

describe('/explore con el nuevo layout', () => {
  let fetchSpy: MockInstance<typeof fetch>
  beforeEach(() => {
    fetchSpy = vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('fetch no debería llamarse'))
  })
  afterEach(() => fetchSpy.mockRestore())

  async function open(path: string) {
    document.documentElement.lang = 'es'
    render(
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>,
    )
    await screen.findByRole('heading', { level: 1, name: /Explorador de tendencias/ })
  }

  it('el detalle del mes sigue al mes elegido y los filtros se pliegan sin perder lo elegido', async () => {
    const user = userEvent.setup()
    await open('/explore?region=REG01&product=P02&start=2005-01&end=2005-03')
    const card = await screen.findByRole('region', { name: 'Detalle del mes' })
    expect(within(card).getByText(/enero de 2005/i)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Mes siguiente' }))
    expect(within(screen.getByRole('region', { name: 'Detalle del mes' })).getByText(/febrero de 2005/i)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Ocultar filtros' }))
    expect(screen.getByRole('list', { name: 'Filtros elegidos' })).toHaveTextContent('2005-01 a 2005-03')
    expect(screen.getByRole('table')).toBeInTheDocument()
    expect(fetchSpy).not.toHaveBeenCalled()
  })
})

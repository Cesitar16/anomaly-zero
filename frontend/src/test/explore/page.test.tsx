import { configure, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import axe from 'axe-core'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../../App'
import { createExploreApi } from '../../features/explore/data/createExploreApi'

// La primera carga de la ruta diferida (gráficos incluidos) tarda más en jsdom que el valor por defecto.
configure({ asyncUtilTimeout: 6000 })
vi.setConfig({ testTimeout: 20000 })

// MapLibre no corre en jsdom (necesita WebGL): el lienzo se reemplaza por un marcador.
vi.mock('../../features/explore/components/MapCanvas', () => ({
  default: ({ month }: { month: string }) => <div data-testid="map-canvas">{month}</div>,
}))

const SERIES = 'region=REG01&product=P02&start=2005-01&end=2005-03'

function LocationProbe() {
  const { pathname, search } = useLocation()
  return <output data-testid="location">{`${pathname}${search}`}</output>
}

async function openPage(path: string) {
  document.documentElement.lang = 'es'
  const view = render(
    <MemoryRouter initialEntries={[path]}>
      <App />
      <LocationProbe />
    </MemoryRouter>,
  )
  await screen.findByRole('heading', { level: 1, name: /Explorador de tendencias/ })
  return view
}

const location = () => screen.getByTestId('location').textContent

async function expectNoA11yViolations(root: HTMLElement) {
  const results = await axe.run(root, { rules: { 'color-contrast': { enabled: false } } })
  expect(results.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.html).join(' | ')}`)).toEqual([])
}

let fetchSpy: ReturnType<typeof vi.spyOn>

beforeEach(() => {
  // El modo predeterminado es el servicio simulado: NADA sale a la red ni pide imágenes.
  fetchSpy = vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('fetch no debería llamarse'))
})

afterEach(() => {
  fetchSpy.mockRestore()
  vi.unstubAllEnvs()
})

describe('Entrada al explorador', () => {
  it('desde la landing, el botón lleva a /explore y carga la pantalla de forma diferida', async () => {
    document.documentElement.lang = 'es'
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
        <LocationProbe />
      </MemoryRouter>,
    )
    const [cta] = screen.getAllByRole('link', { name: /Abrir el explorador/ })
    await userEvent.click(cta)
    expect(await screen.findByRole('heading', { level: 1, name: /Explorador de tendencias/ })).toBeInTheDocument()
    expect(location()).toBe('/explore')
    expect(document.title).toMatch(/Explorador de tendencias \| Anomaly Zero/)
  })

  it('estado inicial: aviso sintético, una región ya elegida y sin gráfico ni tabla', async () => {
    await openPage('/explore')
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Demostración')
    expect(screen.getByRole('note', { name: '' })).toHaveTextContent(/Datos sintéticos de demostración/)
    await waitFor(() => expect(screen.getByLabelText('Región')).toHaveValue('REG01'))
    expect(await screen.findByRole('option', { name: /Precipitación \(IMERG Final\)/ })).toBeInTheDocument()
    expect(screen.getByText(/Elige una variable y un rango de meses/)).toBeInTheDocument()
    expect(screen.queryByRole('table')).toBeNull()
    expect(screen.queryByRole('img')).toBeNull()
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('el modo HTTP no se activa solo: sin la variable el adaptador es el simulado', () => {
    expect(createExploreApi(null).mode).toBe('mock')
    vi.stubEnv('VITE_EXPLORE_API', 'http')
    expect(createExploreApi(null).mode).toBe('http')
  })
})

describe('Consulta de una serie', () => {
  it('elegir producto propone su cobertura; «Ver serie» consulta y escribe la dirección', async () => {
    const user = userEvent.setup()
    await openPage('/explore')
    await screen.findByRole('option', { name: /Precipitación/ })
    await user.selectOptions(screen.getByLabelText('Variable NASA'), 'P02')
    expect(screen.getByLabelText('Desde')).toHaveValue('2005-01')
    expect(screen.getByLabelText('Hasta')).toHaveValue('2005-03')

    await user.click(screen.getByRole('button', { name: 'Ver serie' }))
    expect(await screen.findByText(/Serie con huecos/)).toBeInTheDocument()
    expect(location()).toBe(`/explore?${SERIES}`)
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('la dirección con filtros completos consulta sola y conserva cero y faltante', async () => {
    await openPage(`/explore?${SERIES}`)
    expect(await screen.findByText(/Serie con huecos/)).toBeInTheDocument()
    expect(screen.getByLabelText('Región')).toHaveValue('REG01')
    expect(screen.getByLabelText('Variable NASA')).toHaveValue('P02')

    const table = screen.getByRole('table')
    expect(within(table).getByText('0 (cero válido)')).toBeInTheDocument()
    expect(within(table).getAllByText(/Sin dato/).length).toBeGreaterThan(0)
    expect(screen.getByText(/Hay datos, pero faltan 1 de 3 meses/)).toBeInTheDocument()
    expect(screen.getByRole('img', { name: /Serie mensual: tasa media mensual/ })).toBeInTheDocument()
    expect(screen.getByText(/Tasa media mensual en mm\/hr\. No es el total acumulado/)).toBeInTheDocument()
  })

  it('soporte puntual: se rotula muestra NASA exploratoria, no promedio de la cuenca', async () => {
    await openPage(`/explore?${SERIES}`)
    await screen.findByText(/Serie con huecos/)
    expect(screen.getByText(/Muestra NASA exploratoria/)).toBeInTheDocument()
    expect(screen.getByText(/Serie de un punto: cada valor es la muestra de una sola celda/)).toBeInTheDocument()
    expect(screen.queryByText(/Agregado regional aprobado/)).toBeNull()
  })

  it('sin capas: la ausencia del mapa es explícita y no se pide ninguna imagen', async () => {
    await openPage(`/explore?${SERIES}`)
    await screen.findByText(/Serie con huecos/)
    expect(screen.getByText('Sin capa geográfica disponible para este mes.')).toBeInTheDocument()
    expect(screen.queryByTestId('map-canvas')).toBeNull()
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('calidad, cobertura, procedencia y análisis no disponible aparecen siempre con datos', async () => {
    await openPage(`/explore?${SERIES}`)
    await screen.findByText(/Serie con huecos/)
    for (const name of ['Calidad de los datos', 'Cobertura', 'Fuente y procedencia', 'Análisis de tendencia: no disponible']) {
      expect(screen.getByRole('heading', { level: 2, name })).toBeInTheDocument()
    }
    expect(screen.getByRole('button', { name: 'Calcular tendencia' })).toBeDisabled()
  })

  it('el servicio simulado muestra el 409 del contrato y no crea ningún análisis', async () => {
    const user = userEvent.setup()
    await openPage(`/explore?${SERIES}`)
    await screen.findByText(/Serie con huecos/)
    await user.click(screen.getByRole('button', { name: /Ver la respuesta del servicio simulado/ }))
    expect(await screen.findByText('ANALYSIS_METHOD_UNAVAILABLE')).toBeInTheDocument()
    expect(screen.getByText('No se creó')).toBeInTheDocument()
    expect(screen.getByText('Ninguno habilitado')).toBeInTheDocument()
  })

  it('200 no_data no es un error: dice «Sin datos» y no dibuja gráfico, mapa ni tabla', async () => {
    await openPage('/explore?region=REG01&product=P03&start=2005-01&end=2005-12')
    expect(await screen.findByText(/No hay datos para el rango pedido/)).toBeInTheDocument()
    expect(screen.queryByRole('alert')).toBeNull()
    expect(screen.queryByRole('table')).toBeNull()
    expect(screen.queryByRole('img')).toBeNull()
    expect(screen.getByText('Meses sin dato').nextSibling).toHaveTextContent('12')
    expect(screen.getByText(/no hay un snapshot verificado/i)).toBeInTheDocument()
  })

  it('un producto no disponible se puede consultar y responde sin datos', async () => {
    await openPage('/explore?region=REG01&product=P01&start=2005-01&end=2005-02')
    expect(await screen.findByText(/No hay datos para el rango pedido/)).toBeInTheDocument()
  })

  it('al cambiar un filtro avisa que la serie mostrada ya no coincide', async () => {
    const user = userEvent.setup()
    await openPage(`/explore?${SERIES}`)
    await screen.findByText(/Serie con huecos/)
    await user.clear(screen.getByLabelText('Hasta'))
    await user.type(screen.getByLabelText('Hasta'), '2005-02')
    expect(screen.getByText(/Cambiaste los filtros/)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Ver serie' }))
    await waitFor(() => expect(location()).toContain('end=2005-02'))
    await waitFor(() => expect(screen.queryByText(/Cambiaste los filtros/)).toBeNull())
  })
})

describe('Validación de los filtros', () => {
  it('sin variable ni meses no consulta y explica qué falta', async () => {
    const user = userEvent.setup()
    await openPage('/explore')
    await screen.findByRole('option', { name: /Precipitación/ })
    await user.click(screen.getByRole('button', { name: 'Ver serie' }))
    expect(screen.getByText('Elige una variable.')).toBeInTheDocument()
    expect(screen.getAllByText('Mes no válido. Usa AAAA-MM.')).toHaveLength(2)
    expect(location()).toBe('/explore')
  })

  it('rango invertido y rango de más de 240 meses', async () => {
    const user = userEvent.setup()
    await openPage('/explore')
    await screen.findByRole('option', { name: /Precipitación/ })
    await user.selectOptions(screen.getByLabelText('Variable NASA'), 'P02')
    const start = screen.getByLabelText('Desde')
    const end = screen.getByLabelText('Hasta')

    await user.clear(start)
    await user.type(start, '2005-03')
    await user.clear(end)
    await user.type(end, '2005-01')
    await user.click(screen.getByRole('button', { name: 'Ver serie' }))
    expect(screen.getByText(/"Desde" no puede ser posterior a "Hasta"/)).toBeInTheDocument()

    await user.clear(start)
    await user.type(start, '2005-01')
    await user.clear(end)
    await user.type(end, '2030-01')
    expect(screen.getByText(/El rango supera 240 meses/)).toBeInTheDocument()
    expect(location()).toBe('/explore')
  })

  it('una región desconocida en la dirección se avisa y no consulta la serie', async () => {
    await openPage('/explore?region=NOPE&product=P02&start=2005-01&end=2005-03')
    expect(await screen.findByText('La región de la dirección no existe. Elige otra.')).toBeInTheDocument()
    expect(screen.queryByRole('table')).toBeNull()
    expect(screen.queryByRole('heading', { level: 2, name: 'Resultado' })).toBeNull()
  })

  it('una dirección con un mes inválido rellena el formulario y marca el campo', async () => {
    await openPage('/explore?region=REG01&product=P02&start=2005-13&end=2005-03')
    expect(await screen.findByText('Mes no válido. Usa AAAA-MM.')).toBeInTheDocument()
    expect(screen.getByLabelText('Desde')).toHaveValue('2005-13')
    expect(screen.queryByRole('table')).toBeNull()
  })
})

describe('Errores: nunca se disfrazan de «sin datos»', () => {
  it.each([
    ['error-503', 'Los datos no están disponibles por ahora', true],
    ['error-500', 'Algo falló de nuestro lado', false],
    ['no-encontrado', 'No encontramos lo que pediste', false],
    ['sin-red', 'No pudimos conectar', true],
  ])('%s', async (scenario, title, canRetry) => {
    await openPage(`/explore?${SERIES}&demo=${scenario}`)
    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent(title)
    if (canRetry) expect(within(alert).getByRole('button', { name: 'Reintentar' })).toBeInTheDocument()
    else expect(within(alert).queryByRole('button')).toBeNull()
    expect(screen.queryByText(/No hay datos para el rango pedido/)).toBeNull()
    expect(screen.queryByRole('table')).toBeNull()
  })

  it('el botón Reintentar vuelve a pedir la serie', async () => {
    const user = userEvent.setup()
    await openPage(`/explore?${SERIES}&demo=error-503`)
    const alert = await screen.findByRole('alert')
    await user.click(within(alert).getByRole('button', { name: 'Reintentar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Los datos no están disponibles por ahora')
  })

  it('catálogo sin regiones: lo dice y no ofrece consultar', async () => {
    await openPage('/explore?demo=catalogo-vacio')
    expect(await screen.findByText('Todavía no hay regiones publicadas.')).toBeInTheDocument()
    expect(screen.getByLabelText('Región')).toBeDisabled()
  })
})

describe('Mapa con capas sintéticas de demostración (E9 y E10)', () => {
  it('abre en el primer mes con capa; un mes sin capa se declara ausente y queda en la dirección', async () => {
    const user = userEvent.setup()
    await openPage(`/explore?${SERIES}&demo=capas-mixtas`)
    expect(await screen.findByTestId('map-canvas')).toHaveTextContent('2005-01')
    expect(screen.getByText(/Capa sintética de demostración/)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Mes siguiente' }))
    expect(await screen.findByText(/Este mes no tiene capa en la API/)).toBeInTheDocument()
    expect(screen.queryByTestId('map-canvas')).toBeNull()
    expect(location()).toContain('month=2005-02')
    expect(document.querySelector('tr[aria-current="true"]')).toHaveTextContent('2005-02')

    await user.click(screen.getByRole('button', { name: 'Mes siguiente' }))
    expect(await screen.findByTestId('map-canvas')).toHaveTextContent('2005-03')
  })

  it('capas declaradas no disponibles: igual que sin capas, y sin pedir imágenes', async () => {
    await openPage(`/explore?${SERIES}&demo=capas-no-disponibles`)
    expect(await screen.findByText('Sin capa geográfica disponible para este mes.')).toBeInTheDocument()
    expect(screen.queryByTestId('map-canvas')).toBeNull()
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('el selector de escenarios cambia el servicio simulado y queda en la dirección', async () => {
    const user = userEvent.setup()
    await openPage(`/explore?${SERIES}`)
    await screen.findByText(/Serie con huecos/)
    await user.selectOptions(screen.getByLabelText('Escenario'), 'error-503')
    expect(await screen.findByRole('alert')).toHaveTextContent('Los datos no están disponibles por ahora')
    expect(location()).toContain('demo=error-503')
  })
})

describe('Accesibilidad (axe) y estructura', () => {
  it('serie con datos', async () => {
    const { container } = await openPage(`/explore?${SERIES}`)
    await screen.findByText(/Serie con huecos/)
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1)
    await expectNoA11yViolations(container.ownerDocument.body)
  })

  it('sin datos, con errores y con capas', async () => {
    for (const path of [
      '/explore',
      '/explore?region=REG01&product=P03&start=2005-01&end=2005-12',
      `/explore?${SERIES}&demo=error-503`,
      `/explore?${SERIES}&demo=capas-mixtas`,
    ]) {
      const { container, unmount } = await openPage(path)
      await waitFor(() => expect(screen.queryByRole('status', { busy: true })).toBeNull())
      await expectNoA11yViolations(container.ownerDocument.body)
      unmount()
    }
  })
})

import { configure, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import axe from 'axe-core'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi, type MockInstance } from 'vitest'
import App from '../../App'
import { observed } from './helpers'

// MapLibre requiere WebGL y una red de teselas; las pruebas de la página verifican el contrato del panel sin red.
vi.mock('../../features/explore/components/MapCanvas', () => ({
  default: ({ month, raster, marker }: { month?: string | null; raster?: unknown; marker?: { longitude: number; latitude: number } | null }) => (
    <div data-testid="map-canvas" data-month={month ?? ''} data-raster={raster ? 'true' : 'false'} data-marker={marker ? `${marker.longitude},${marker.latitude}` : ''}>{month}</div>
  ),
}))
import { createExploreApi, defaultSource } from '../../features/explore/data/createExploreApi'
import { seriesPointSample } from '../../features/explore/data/fixtures/official'

// La primera carga de la ruta diferida (gráficos incluidos) tarda más en jsdom que el valor por defecto.
configure({ asyncUtilTimeout: 6000 })
vi.setConfig({ testTimeout: 20000 })

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

let fetchSpy: MockInstance<typeof fetch>

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

  it('la fuente por defecto es la simulada; VITE_EXPLORE_API=http solo cambia el valor por defecto', () => {
    expect(defaultSource()).toBe('demo')
    expect(createExploreApi('demo').mode).toBe('mock')
    vi.stubEnv('VITE_EXPLORE_API', 'http')
    expect(defaultSource()).toBe('api')
    expect(createExploreApi('api').mode).toBe('http')
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

  it('sin capas raster NASA sigue habiendo mapa contextual; no se pide imagen de precipitación', async () => {
    await openPage(`/explore?${SERIES}`)
    await screen.findByText(/Serie con huecos/)
    expect(screen.getByText(/Mapa geográfico contextual/)).toBeInTheDocument()
    expect(screen.getByTestId('map-canvas')).toHaveAttribute('data-raster', 'false')
    expect(screen.getByText(/Capa raster NASA/)).toBeInTheDocument()
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

describe('Errores del contrato que llegan de la API (no de la validación local)', () => {
  it('422 PERIOD_OUT_OF_COVERAGE: rango válido pero fuera de lo publicado', async () => {
    await openPage('/explore?region=REG01&product=P02&start=1990-01&end=1990-03')
    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('El rango está fuera de la cobertura')
    expect(within(alert).queryByRole('button')).toBeNull()
    expect(screen.getByText('PERIOD_OUT_OF_COVERAGE')).toBeInTheDocument()
  })
})

describe('Pantalla conectada al cliente HTTP con las respuestas reales observadas en dev', () => {
  function serveDev() {
    fetchSpy.mockImplementation((input: RequestInfo | URL) => {
      const url = String(input)
      const body = url.includes('/regions')
        ? observed('regions_dev')
        : url.includes('/products')
          ? observed('products_dev_sin_snapshot')
          : observed('series_no_data_dev')
      return Promise.resolve(new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    })
  }

  it('sin snapshot: no_data real, sin aviso sintético, sin demos y sin llamar a /analyses', async () => {
    vi.stubEnv('VITE_EXPLORE_API', 'http')
    serveDev()
    await openPage('/explore?region=murray-darling-basin&product=P02&start=2005-01&end=2005-03')
    expect(await screen.findByText(/No hay datos para el rango pedido/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Descargar CSV' })).toBeDisabled()

    // Datos reales (`synthetic: false`): no se rotula como demostración.
    expect(screen.queryByText(/Datos sintéticos de demostración/)).toBeNull()
    expect(screen.queryByText('Demostración', { selector: '.badge' })).toBeNull()
    expect(screen.queryByRole('heading', { name: 'Escenarios de demostración' })).toBeNull()
    // Todos los productos del catálogo real figuran como no disponibles.
    expect(screen.getByLabelText('Variable NASA')).toHaveValue('P02')
    expect(screen.getAllByRole('option').filter((option) => /No disponible/.test(option.textContent ?? ''))).toHaveLength(3)
    // El análisis sigue deshabilitado y no existe el botón que simula `POST /analyses`.
    expect(screen.getByRole('button', { name: 'Calcular tendencia' })).toBeDisabled()
    expect(screen.queryByRole('button', { name: /Ver la respuesta del servicio simulado/ })).toBeNull()

    const urls: string[] = fetchSpy.mock.calls.map((call) => String(call[0]))
    expect(urls.some((url) => url.startsWith('/api/v1/series?'))).toBe(true)
    expect(urls.some((url) => url.includes('/analyses'))).toBe(false)
  })

  it('una ruta de la API que no existe se muestra como «sin respuesta», no como un código del contrato', async () => {
    vi.stubEnv('VITE_EXPLORE_API', 'http')
    fetchSpy.mockImplementation(() =>
      Promise.resolve(new Response(JSON.stringify(observed('ruta_inexistente_dev')), { status: 404 })),
    )
    await openPage('/explore')
    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('No pudimos conectar')
    expect(within(alert).getByRole('button', { name: 'Reintentar' })).toBeInTheDocument()
  })
})

describe('Descarga CSV de la consulta visible (fixtures sintéticas)', () => {
  function serveHttpWithCsv(csv: Response | Promise<Response> = Promise.resolve(new Response('record_type\n', { headers: { 'Content-Type': 'text/csv; charset=utf-8' } }))) {
    const series = { ...structuredClone(seriesPointSample), region: { ...seriesPointSample.region, region_id: 'murray-darling-basin' } }
    fetchSpy.mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      if (url.includes('/series/export.csv')) return Promise.resolve(csv).then((response) => {
        expect(init?.headers).toMatchObject({ Accept: 'text/csv' })
        return response
      })
      const body = url.includes('/regions')
        ? observed('regions_dev')
        : url.includes('/products')
          ? observed('products_dev_sin_snapshot')
          : series
      return Promise.resolve(new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    })
  }

  it('descarga como archivo con la URL exacta de la consulta aplicada y nombre seguro', async () => {
    vi.stubEnv('VITE_EXPLORE_API', 'http')
    serveHttpWithCsv()
    const createUrl = vi.fn((_blob: Blob) => 'blob:test-csv')
    const revokeUrl = vi.fn()
    const clickedDownloads: string[] = []
    const anchorClick = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) {
      clickedDownloads.push(this.download)
    })
    Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: createUrl })
    Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: revokeUrl })
    await openPage('/explore?fuente=api&region=murray-darling-basin&product=P02&start=2005-01&end=2005-03')
    const button = await screen.findByRole('button', { name: 'Descargar CSV' })
    await waitFor(() => expect(button).toBeEnabled())
    const user = userEvent.setup()
    await user.click(button)
    await waitFor(() => expect(fetchSpy.mock.calls.some(([input]) => String(input).includes('/series/export.csv'))).toBe(true))
    const call = fetchSpy.mock.calls.find(([input]) => String(input).includes('/series/export.csv'))
    const url = new URL(String(call?.[0]), 'http://localhost')
    expect(url.pathname).toBe('/api/v1/series/export.csv')
    expect(Object.fromEntries(url.searchParams)).toEqual({
      region_id: 'murray-darling-basin', product_id: 'P02', start: '2005-01', end: '2005-03', frequency: 'monthly',
    })
    expect(fetchSpy.mock.calls.filter(([input]) => String(input).includes('/series/export.csv'))).toHaveLength(1)
    await waitFor(() => expect(createUrl).toHaveBeenCalledOnce())
    const downloadedBlob = createUrl.mock.calls[0]?.[0] as Blob | undefined
    expect(downloadedBlob?.size).toBeGreaterThan(0)
    expect(downloadedBlob?.type).toContain('text/csv')
    expect(anchorClick).toHaveBeenCalledOnce()
    expect(clickedDownloads).toEqual(['anomaly-zero_murray-darling-basin_P02_2005-01_2005-03.csv'])
    await new Promise((resolve) => window.setTimeout(resolve, 5))
    expect(revokeUrl).toHaveBeenCalledWith('blob:test-csv')
    anchorClick.mockRestore()
  })

  it('no habilita el modo demo ni no_data', async () => {
    const demoPage = await openPage(`/explore?${SERIES}`)
    await screen.findByText(/Serie con huecos/)
    expect(screen.getByRole('button', { name: 'Descargar CSV' })).toBeDisabled()
    demoPage.unmount()
    vi.stubEnv('VITE_EXPLORE_API', 'http')
    fetchSpy.mockImplementation((input: RequestInfo | URL) => {
      const url = String(input)
      const body = url.includes('/regions') ? observed('regions_dev') : url.includes('/products') ? observed('products_dev_sin_snapshot') : observed('series_no_data_dev')
      return Promise.resolve(new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    })
    await openPage('/explore?fuente=api&region=murray-darling-basin&product=P02&start=2005-01&end=2005-03')
    expect(await screen.findByRole('button', { name: 'Descargar CSV' })).toBeDisabled()
  })

  it('mantiene la descarga deshabilitada mientras carga la consulta real', async () => {
    vi.stubEnv('VITE_EXPLORE_API', 'http')
    fetchSpy.mockImplementation((input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/series?')) return new Promise<Response>(() => {})
      const body = url.includes('/regions') ? observed('regions_dev') : observed('products_dev_sin_snapshot')
      return Promise.resolve(new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    })
    await openPage('/explore?fuente=api&region=murray-darling-basin&product=P02&start=2005-01&end=2005-03')
    const button = await screen.findByRole('button', { name: 'Descargar CSV' })
    expect(button).toBeDisabled()
    expect(screen.getByText('Espera a que termine la consulta.')).toBeInTheDocument()
  })

  it('no descarga HTML del proxy y muestra el contenido inesperado', async () => {
    vi.stubEnv('VITE_EXPLORE_API', 'http')
    serveHttpWithCsv(new Response('<html>proxy error</html>', { status: 502, headers: { 'Content-Type': 'text/html' } }))
    await openPage('/explore?fuente=api&region=murray-darling-basin&product=P02&start=2005-01&end=2005-03')
    const button = await screen.findByRole('button', { name: 'Descargar CSV' })
    await waitFor(() => expect(button).toBeEnabled())
    await userEvent.click(button)
    expect(await screen.findByText('La respuesta no era un archivo CSV')).toBeInTheDocument()
    expect(screen.getByText(/HTTP 502/)).toBeInTheDocument()
  })

  it('los filtros pendientes bloquean una descarga y abortan una solicitud obsoleta', async () => {
    vi.stubEnv('VITE_EXPLORE_API', 'http')
    let signal: AbortSignal | undefined
    const series = { ...structuredClone(seriesPointSample), region: { ...seriesPointSample.region, region_id: 'murray-darling-basin' } }
    fetchSpy.mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      if (url.includes('/series/export.csv')) {
        signal = init?.signal ?? undefined
        return new Promise<Response>(() => {})
      }
      const body = url.includes('/regions') ? observed('regions_dev') : url.includes('/products') ? observed('products_dev_sin_snapshot') : series
      return Promise.resolve(new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    })
    const user = userEvent.setup()
    await openPage('/explore?fuente=api&region=murray-darling-basin&product=P02&start=2005-01&end=2005-03')
    const button = await screen.findByRole('button', { name: 'Descargar CSV' })
    await waitFor(() => expect(button).toBeEnabled())
    await user.click(button)
    await user.clear(screen.getByLabelText('Hasta'))
    await user.type(screen.getByLabelText('Hasta'), '2005-02')
    await waitFor(() => expect(button).toBeDisabled())
    expect(signal?.aborted).toBe(true)
  })
})

describe('Fuente de los datos: simulada o real, siempre a la vista y sin respaldo automático', () => {
  function serveDev() {
    fetchSpy.mockImplementation((input: RequestInfo | URL) => {
      const url = String(input)
      const body = url.includes('/regions')
        ? observed('regions_dev')
        : url.includes('/products')
          ? observed('products_dev_sin_snapshot')
          : observed('series_no_data_dev')
      return Promise.resolve(new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    })
  }

  it('por defecto la fuente es el servicio simulado y está marcada en el selector', async () => {
    await openPage('/explore')
    const group = screen.getByRole('group', { name: 'Fuente de los datos' })
    expect(within(group).getByRole('radio', { name: 'Servicio simulado (demostración)' })).toBeChecked()
    expect(within(group).getByRole('radio', { name: 'Servicio real (API)' })).not.toBeChecked()
  })

  it('al cambiar a la API real se pide el catálogo real, se descartan los filtros y desaparece lo simulado', async () => {
    const user = userEvent.setup()
    serveDev()
    await openPage(`/explore?${SERIES}`)
    await screen.findByText(/Serie con huecos/)

    await user.click(screen.getByRole('radio', { name: 'Servicio real (API)' }))

    expect(location()).toBe('/explore?fuente=api')
    await waitFor(() => expect(screen.getByLabelText('Región')).toHaveValue('murray-darling-basin'))
    // Nada de lo simulado sobrevive: ni la serie, ni el aviso, ni la insignia, ni los escenarios.
    expect(screen.queryByText(/Serie con huecos/)).toBeNull()
    expect(screen.queryByRole('table')).toBeNull()
    expect(screen.queryByText(/Datos sintéticos de demostración/)).toBeNull()
    expect(screen.getByRole('heading', { level: 1 })).not.toHaveTextContent('Demostración')
    expect(screen.queryByRole('heading', { name: 'Escenarios de demostración' })).toBeNull()
    const urls: string[] = fetchSpy.mock.calls.map((call) => String(call[0]))
    expect(urls.some((url) => url.startsWith('/api/v1/regions'))).toBe(true)
  })

  it('un escenario de demostración en la dirección no afecta a la API real', async () => {
    serveDev()
    await openPage('/explore?fuente=api&demo=error-503')
    await waitFor(() => expect(screen.getByLabelText('Región')).toHaveValue('murray-darling-basin'))
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('si la API real no responde se muestra el error y NO se pasa a datos simulados', async () => {
    await openPage('/explore?fuente=api')
    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('No pudimos conectar')
    expect(screen.queryByText(/Datos sintéticos de demostración/)).toBeNull()
    expect(screen.queryByRole('option', { name: /Precipitación \(IMERG Final\)/ })).toBeNull()
  })

  it('volver al servicio simulado restablece el catálogo simulado', async () => {
    const user = userEvent.setup()
    serveDev()
    await openPage('/explore?fuente=api')
    await waitFor(() => expect(screen.getByLabelText('Región')).toHaveValue('murray-darling-basin'))
    await user.click(screen.getByRole('radio', { name: 'Servicio simulado (demostración)' }))
    expect(location()).toBe('/explore?fuente=demo')
    await waitFor(() => expect(screen.getByLabelText('Región')).toHaveValue('REG01'))
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Demostración')
  })

  it('enviar una consulta conserva la fuente elegida en la dirección', async () => {
    const user = userEvent.setup()
    await openPage('/explore?fuente=demo')
    await waitFor(() => expect(screen.getByLabelText('Región')).toHaveValue('REG01'))
    await screen.findByRole('option', { name: /Precipitación/ })
    await user.selectOptions(screen.getByLabelText('Variable NASA'), 'P02')
    await user.click(screen.getByRole('button', { name: 'Ver serie' }))
    expect(await screen.findByText(/Serie con huecos/)).toBeInTheDocument()
    expect(location()).toBe(`/explore?${SERIES}&fuente=demo`)
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
    expect(screen.getByTestId('map-canvas')).toHaveAttribute('data-raster', 'false')
    expect(location()).toContain('month=2005-02')
    expect(document.querySelector('tr[aria-current="true"]')).toHaveTextContent('2005-02')

    await user.click(screen.getByRole('button', { name: 'Mes siguiente' }))
    expect(await screen.findByTestId('map-canvas')).toHaveTextContent('2005-03')
  })

  it('capas declaradas no disponibles mantienen el mapa contextual sin pedir raster', async () => {
    await openPage(`/explore?${SERIES}&demo=capas-no-disponibles`)
    expect(await screen.findByText(/Mapa geográfico contextual/)).toBeInTheDocument()
    expect(await screen.findByTestId('map-canvas')).toHaveAttribute('data-raster', 'false')
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

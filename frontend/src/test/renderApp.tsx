import { render } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from '../App'

/** Renderiza la app completa en una ruta dada, sin navegador ni servidor. */
export function renderApp(path = '/') {
  document.documentElement.lang = 'es'
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

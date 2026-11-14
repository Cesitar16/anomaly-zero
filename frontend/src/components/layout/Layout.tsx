import { Outlet } from 'react-router-dom'
import Footer from './Footer'
import Navbar from './Navbar'
import ScrollManager from './ScrollManager'
import SkipLink from './SkipLink'

/**
 * Layout compartido por todas las rutas (patrón "Layout Route").
 * Cada página solo aporta su contenido; la estructura, la navegación y el pie
 * se escriben una vez aquí. Los landmarks (header, nav, main, footer) viven en
 * este árbol para que la jerarquía semántica sea la misma en toda la app.
 */
export default function Layout() {
  return (
    <>
      <SkipLink />
      <Navbar />
      <main id="contenido" tabIndex={-1}>
        <Outlet />
      </main>
      <Footer />
      <ScrollManager />
    </>
  )
}

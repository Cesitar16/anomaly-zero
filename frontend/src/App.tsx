import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Container from './components/ui/Container'
import LandingPage from './pages/LandingPage'
import NotFoundPage from './pages/NotFoundPage'

// El explorador arrastra gráficos y (cuando hace falta) el mapa: se descarga solo al entrar en /explore.
const ExplorePage = lazy(() => import('./features/explore/ExplorePage'))

function RouteFallback() {
  return (
    <Container>
      <p className="route-loading" role="status">
        Cargando el explorador
      </p>
    </Container>
  )
}

/** Tabla de rutas. El router (BrowserRouter / MemoryRouter) se provee desde fuera. */
export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<LandingPage />} />
        <Route
          path="explore"
          element={
            <Suspense fallback={<RouteFallback />}>
              <ExplorePage />
            </Suspense>
          }
        />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}

import { Route, Routes } from 'react-router-dom'
import Layout from './components/layout/Layout'
import ExplorerPage from './pages/ExplorerPage'
import LandingPage from './pages/LandingPage'
import NotFoundPage from './pages/NotFoundPage'

/** Tabla de rutas. El router (BrowserRouter / MemoryRouter) se provee desde fuera. */
export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<LandingPage />} />
        <Route path="explore" element={<ExplorerPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}

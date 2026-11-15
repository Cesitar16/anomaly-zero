import type { ExploreApi } from './exploreApi'
import { createHttpExploreApi, DEFAULT_API_BASE } from './httpExploreApi'
import { createMockExploreApi } from './mockExploreApi'

/**
 * Elige el adaptador. Por defecto es el servicio simulado: la app no depende de FastAPI, de Earthdata
 * ni de credenciales. `VITE_EXPLORE_API=http` activa el cliente HTTP (integración controlada, aparte).
 */
export function createExploreApi(scenario: string | null): ExploreApi {
  const mode: unknown = import.meta.env.VITE_EXPLORE_API
  if (mode === 'http') {
    const base: unknown = import.meta.env.VITE_API_BASE_URL
    return createHttpExploreApi(typeof base === 'string' && base !== '' ? base : DEFAULT_API_BASE)
  }
  // En las pruebas las respuestas llegan sin demora; en el navegador se simula una breve para ver la carga.
  return createMockExploreApi({ scenario, delayMs: import.meta.env.MODE === 'test' ? 0 : 400 })
}

import type { ExploreSource } from '../lib/exploreUrl'
import type { ExploreApi } from './exploreApi'
import { createHttpExploreApi, DEFAULT_API_BASE } from './httpExploreApi'
import { createMockExploreApi } from './mockExploreApi'

/**
 * Fuente por defecto de la compilación. Es el servicio simulado: la app no depende de FastAPI, de Earthdata
 * ni de credenciales. `VITE_EXPLORE_API=http` cambia el valor por defecto a la API real; en cualquier caso la
 * persona puede cambiar de fuente en la pantalla (`fuente=demo|api` en la dirección).
 */
export function defaultSource(): ExploreSource {
  const mode: unknown = import.meta.env.VITE_EXPLORE_API
  return mode === 'http' ? 'api' : 'demo'
}

/**
 * Crea el adaptador de la fuente elegida. Nunca hay respaldo automático: si la API real falla, la pantalla
 * muestra el error y no pasa a datos simulados por su cuenta.
 */
export function createExploreApi(source: ExploreSource, scenario: string | null = null): ExploreApi {
  if (source === 'api') {
    const base: unknown = import.meta.env.VITE_API_BASE_URL
    return createHttpExploreApi(typeof base === 'string' && base !== '' ? base : DEFAULT_API_BASE)
  }
  // En las pruebas las respuestas llegan sin demora; en el navegador se simula una breve para ver la carga.
  return createMockExploreApi({ scenario, delayMs: import.meta.env.MODE === 'test' ? 0 : 400 })
}

/**
 * Configuración global de la landing.
 * Es el único lugar donde viven los "interruptores" del producto.
 */

export const SITE = {
  name: 'Anomaly Zero',
  tagline:
    'Explora cómo cambian las variables ambientales y qué evidencia respaldan sus tendencias.',
  challengeName: 'Be an Earth System Trend Detective!',
  year: 2026,
} as const

export const ROUTES = {
  home: '/',
  explore: '/explore',
} as const

/** IDs de las secciones de la página de inicio (se usan como anclas). */
export const SECTION_IDS = {
  problem: 'problema',
  solution: 'propuesta',
  how: 'como-funciona',
  team: 'equipo',
  sources: 'fuentes',
  access: 'acceso',
} as const

/**
 * Feature flag del explorador.
 * Mientras sea `false`, la ruta /explore muestra un placeholder explícito
 * "En desarrollo" y ningún resultado simulado.
 * Cuando exista el explorador real (FE-02 en adelante), cambia a `true`
 * y reemplaza el contenido de `pages/ExplorerPage.tsx`.
 */
// Se anota como boolean para que TypeScript no reduzca la condición al literal `false`.
export const EXPLORER_AVAILABLE: boolean = false

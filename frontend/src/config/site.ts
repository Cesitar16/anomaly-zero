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
 * Estado del explorador (/explore). Es el único "interruptor": hero, barra y sección de acceso lo leen.
 *  - 'in-development': la ruta solo explica el estado del proyecto.
 *  - 'demo': el explorador existe y funciona con datos SINTÉTICOS (FE-04). No hay datos NASA reales.
 *  - 'available': el explorador usa datos reales revisados. Cámbialo solo cuando César lo apruebe.
 */
export type ExplorerStatus = 'in-development' | 'demo' | 'available'

// Se anota con el tipo para que TypeScript no reduzca las comparaciones al literal.
export const EXPLORER_STATUS: ExplorerStatus = 'demo'

/** Etiqueta corta de un estado; `null` cuando está disponible y no hace falta ninguna. */
export function explorerStatusLabel(status: ExplorerStatus): string | null {
  if (status === 'available') return null
  return status === 'demo' ? 'Demostración' : 'En desarrollo'
}

export const EXPLORER_STATUS_LABEL: string | null = explorerStatusLabel(EXPLORER_STATUS)

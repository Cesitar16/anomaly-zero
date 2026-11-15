import type { To } from 'react-router-dom'
import { ROUTES, SECTION_IDS } from '../config/site'

export interface NavLinkItem {
  label: string
  to: To
}

const anchor = (id: string): To => ({ pathname: ROUTES.home, hash: `#${id}` })

/** Enlaces de la barra superior. Las anclas apuntan a secciones de la home. */
export const NAV_LINKS: NavLinkItem[] = [
  { label: 'Problema', to: anchor(SECTION_IDS.problem) },
  { label: 'Propuesta', to: anchor(SECTION_IDS.solution) },
  { label: 'Cómo funciona', to: anchor(SECTION_IDS.how) },
  { label: 'Equipo', to: anchor(SECTION_IDS.team) },
  { label: 'Fuentes', to: anchor(SECTION_IDS.sources) },
]

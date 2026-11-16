import { useId } from 'react'
import type { ReactNode } from 'react'
import { COPY } from '../content/exploreCopy'

export interface FiltersSummary {
  region: string | null
  product: string | null
  range: string | null
  site?: string | null
}

export interface FiltersPanelProps {
  open: boolean
  onToggle(): void
  summary: FiltersSummary
  children: ReactNode
}

/**
 * Contenedor plegable de los filtros. Plegado, el formulario sigue en el documento pero oculto, y una fila de
 * etiquetas resume lo que hay elegido. No decide nada: el estado de abierto o cerrado lo tiene la página.
 */
export function FiltersPanel({ open, onToggle, summary, children }: FiltersPanelProps) {
  const bodyId = useId()
  const chips = [summary.region, summary.product, summary.range, summary.site ?? null].filter(
    (chip): chip is string => chip !== null && chip !== '',
  )
  return (
    <div className="explore-panel">
      <div className="explore-panel__bar">
        <button
          type="button"
          className="btn btn--secondary"
          aria-expanded={open}
          aria-controls={bodyId}
          onClick={onToggle}
        >
          {open ? COPY.filters.hide : COPY.filters.show}
        </button>
        {!open && chips.length > 0 && (
          <ul className="explore-chips" aria-label={COPY.filters.summary}>
            {chips.map((chip) => (
              <li key={chip}>{chip}</li>
            ))}
          </ul>
        )}
      </div>
      <div id={bodyId} className="explore-panel__body" hidden={!open}>
        {children}
      </div>
    </div>
  )
}

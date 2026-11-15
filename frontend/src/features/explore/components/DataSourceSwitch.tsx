import { COPY } from '../content/exploreCopy'
import type { ExploreSource } from '../lib/exploreUrl'

export interface DataSourceSwitchProps {
  source: ExploreSource
  onChange(source: ExploreSource): void
}

/**
 * Cambio explícito y visible entre el servicio simulado y la API real. Cambiar de fuente descarta lo cargado
 * antes y los filtros que dependen del catálogo, porque los identificadores de uno no existen en el otro.
 */
export function DataSourceSwitch({ source, onChange }: DataSourceSwitchProps) {
  return (
    <fieldset className="explore-source">
      <legend>{COPY.source.legend}</legend>
      <div className="explore-source__options">
        <label className="explore-source__option">
          <input
            type="radio"
            name="explore-source"
            value="demo"
            checked={source === 'demo'}
            onChange={() => onChange('demo')}
          />
          <span>{COPY.source.demo}</span>
        </label>
        <label className="explore-source__option">
          <input
            type="radio"
            name="explore-source"
            value="api"
            checked={source === 'api'}
            onChange={() => onChange('api')}
          />
          <span>{COPY.source.api}</span>
        </label>
      </div>
      <p className="explore-muted">{source === 'demo' ? COPY.source.demoNote : COPY.source.apiNote}</p>
    </fieldset>
  )
}

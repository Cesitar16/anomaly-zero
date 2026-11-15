import type { ImageVariant, MapMode, RasterLayer, YearMonth } from '../types'

interface ContractPanelProps {
  month: YearMonth
  layers: RasterLayer[]
  mode: MapMode
  onModeChange: (mode: MapMode) => void
  variant: ImageVariant
  onVariantChange: (variant: ImageVariant) => void
}

export function ContractPanel({ month, layers, mode, onModeChange, variant, onVariantChange }: ContractPanelProps) {
  const layer = layers.find((candidate) => candidate.date === month)
  return (
    <section className="contract" aria-labelledby="contract-title">
      <h3 id="contract-title">Origen de la capa</h3>
      <fieldset>
        <legend>Qué alimenta al mapa</legend>
        <label>
          <input type="radio" name="mode" checked={mode === 'prototype-frames'} onChange={() => onModeChange('prototype-frames')} />
          <span>
            Frames locales de prototipo (recurso visual sintético, <strong>no</strong> es respuesta de la API)
          </span>
        </label>
        <label>
          <input type="radio" name="mode" checked={mode === 'contract'} onChange={() => onModeChange('contract')} />
          <span>
            Descriptor <code>raster_layers[]</code> del contrato (<code>state: unavailable</code> → no hay capa ni peticiones)
          </span>
        </label>
      </fieldset>
      {mode === 'prototype-frames' && (
        <fieldset>
          <legend>Alineación de la imagen con el mapa</legend>
          <label>
            <input type="radio" name="variant" checked={variant === 'mercator'} onChange={() => onVariantChange('mercator')} />
            <span>Remuestreada a Web Mercator (correcta)</span>
          </label>
          <label>
            <input type="radio" name="variant" checked={variant === 'native'} onChange={() => onVariantChange('native')} />
            <span>Rejilla nativa EPSG:4326 estirada entre las esquinas del bbox (para ver el desplazamiento)</span>
          </label>
        </fieldset>
      )}
      <p className="contract__caption">
        Descriptor del contrato para <strong>{month}</strong> (fixture con la forma de <code>RasterLayer</code> en <code>docs/openapi-contract-v0.yaml</code>; el contrato no trae un ejemplo oficial):
      </p>
      <pre className="contract__json" tabIndex={0} aria-label={`Descriptor de capa del contrato para ${month}`}>
        {JSON.stringify(layer ?? null, null, 2)}
      </pre>
      <p className="contract__note">
        Este objeto significa <strong>no hay capa renderizable</strong>. No es un endpoint, no autoriza mostrar una imagen y{' '}
        <code>tile_template: null</code> no es una URL. Un <code>tile_template</code> real exigirá backend, formato, licencia, procedencia y CRS aprobados.
      </p>
    </section>
  )
}

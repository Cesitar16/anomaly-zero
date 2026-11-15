import type { FrameManifest, FrameStatus, MapMode } from '../types'

export function ProvenancePanel({ manifest, mode, status }: { manifest: FrameManifest; mode: MapMode; status: FrameStatus }) {
  const { bbox } = manifest
  const rows: Array<[string, string]> = [
    ['Fuente', 'Sintética: generada por scripts/generate-frames.mjs. No proviene de NASA ni de ningún proveedor.'],
    ['Versión', 'Fixture del spike FE-05; contrato de referencia 0.1-draft'],
    ['Marca de tiempo', 'No aplica: los frames son deterministas y no tienen fecha de observación ni de descarga.'],
    ['Calidad (QA)', 'unassessed · no aplica a datos sintéticos'],
    ['Soporte espacial', 'No aplica. No es point_sample, descriptive_mean ni regional_aggregate.'],
    ['CRS y recuadro', `${manifest.crs} · O ${bbox.west}° · S ${bbox.south}° · E ${bbox.east}° · N ${bbox.north}°`],
    ['Resolución', `${manifest.resolution_deg}° por celda (rejilla discreta, sin suavizado)`],
    ['Origen de la capa mostrada', mode === 'contract' ? 'Descriptor de contrato (sin capa)' : 'Frame local de prototipo'],
    ['Estado actual', status.kind],
  ]
  return (
    <section className="provenance" aria-labelledby="provenance-title">
      <h3 id="provenance-title">Procedencia</h3>
      <dl>
        {rows.map(([term, detail]) => (
          <div key={term}>
            <dt>{term}</dt>
            <dd>{detail}</dd>
          </div>
        ))}
      </dl>
      <p className="provenance__warning">
        Una imagen RGB de un mes no permite recuperar el valor numérico de un píxel, por eso este mapa no ofrece tooltips por celda: sería
        mostrar como medida lo que es un color.
      </p>
    </section>
  )
}

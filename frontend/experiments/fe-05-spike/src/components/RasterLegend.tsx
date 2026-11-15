import type { FrameManifest } from '../types'

export function RasterLegend({ scale }: { scale: FrameManifest['scale'] }) {
  const format = (value: number) => value.toLocaleString('es-CL', { maximumFractionDigits: 2 })
  return (
    <section className="legend" aria-labelledby="legend-title">
      <h3 id="legend-title">Leyenda</h3>
      <p className="legend__scale">
        Escala fija de {scale.classes.length} clases, de {format(scale.min)} a {format(scale.max)} <strong>{scale.unit}</strong>. Es la misma en
        todos los meses, así que los colores son comparables entre fechas. Los colores no indican significancia.
      </p>
      <ol className="legend__classes">
        {scale.classes.map((item) => (
          <li key={item.color}>
            <span className="legend__swatch" style={{ background: item.color }} aria-hidden="true" />
            <span>
              {format(item.from)} a {format(item.to)}
            </span>
          </li>
        ))}
      </ol>
      <ul className="legend__extras">
        <li>
          <span className="legend__swatch legend__swatch--nodata" aria-hidden="true" />
          <span>Sin dato (celda transparente): se ve el fondo del mapa, no un color de la escala.</span>
        </li>
        <li>
          <span className="legend__swatch legend__swatch--mark" aria-hidden="true" />
          <span>Marcas blancas y negra de referencia de georreferenciación (no son valores).</span>
        </li>
        <li>
          <span className="legend__swatch legend__swatch--polygon" aria-hidden="true" />
          <span>Polígono ficticio de prueba (no es la cuenca Murray–Darling).</span>
        </li>
      </ul>
    </section>
  )
}

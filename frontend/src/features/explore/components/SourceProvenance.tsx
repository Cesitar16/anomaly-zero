import { COPY, productLabel, quantityLabel } from '../content/exploreCopy'
import { formatDateTime, orNotInformed } from '../lib/format'
import type { Product, Provenance } from '../types/contracts'
import ExternalLink from '../../../components/ui/ExternalLink'

export interface SourceProvenanceProps {
  product: Product
  provenance: Provenance | null
  datasetId: string | null
}

function when(value: string | null): string {
  return value === null ? COPY.notInformed : formatDateTime(value)
}

/** Fuente y procedencia: de dónde sale el dato, qué versión y de qué snapshot verificado. */
export function SourceProvenance({ product, provenance, datasetId }: SourceProvenanceProps) {
  const { source } = product
  return (
    <section className="explore-card" aria-labelledby="explore-source-title">
      <h2 id="explore-source-title" className="explore-panel__title">
        {COPY.provenance.title}
      </h2>
      <dl className="explore-dl">
        <div>
          <dt>Producto</dt>
          <dd>
            {productLabel(product)} (<span className="explore-mono">{product.short_name}</span>, versión{' '}
            <span className="explore-mono">{product.product_version}</span>)
          </dd>
        </div>
        <div>
          <dt>Variable</dt>
          <dd>
            <span className="explore-mono">{product.variable}</span>: {quantityLabel(product.quantity)}
          </dd>
        </div>
        <div>
          <dt>Unidad</dt>
          <dd className="explore-mono">{product.unit}</dd>
        </div>
        <div>
          <dt>Agencia</dt>
          <dd>{orNotInformed(source.agency)}</dd>
        </div>
        <div>
          <dt>Distribuidor</dt>
          <dd>{orNotInformed(source.distributor)}</dd>
        </div>
        <div>
          <dt>Colección</dt>
          <dd className="explore-mono">{orNotInformed(source.collection_id)}</dd>
        </div>
        <div>
          <dt>DOI</dt>
          <dd>
            {source.doi ? (
              <ExternalLink href={`https://doi.org/${source.doi}`}>{source.doi}</ExternalLink>
            ) : (
              COPY.notInformed
            )}
          </dd>
        </div>
        <div>
          <dt>Conjunto de datos</dt>
          <dd className="explore-mono">{orNotInformed(datasetId)}</dd>
        </div>
      </dl>

      {provenance === null ? (
        <p>{COPY.provenance.none}</p>
      ) : (
        <dl className="explore-dl">
          <div>
            <dt>Snapshot creado</dt>
            <dd>{when(provenance.snapshot_created_at)}</dd>
          </div>
          <div>
            <dt>Descargado</dt>
            <dd>{when(provenance.retrieved_at)}</dd>
          </div>
          <div>
            <dt>Fuente actualizada</dt>
            <dd>{when(provenance.source_updated_at)}</dd>
          </div>
          <div>
            <dt>Archivos originales</dt>
            <dd>{orNotInformed(provenance.original_file_count)}</dd>
          </div>
          <div>
            <dt>Versión del manifiesto</dt>
            <dd className="explore-mono">{orNotInformed(provenance.manifest_version)}</dd>
          </div>
          <div>
            <dt>Huella del manifiesto (SHA-256)</dt>
            <dd className="explore-mono explore-hash">{orNotInformed(provenance.manifest_sha256)}</dd>
          </div>
          {provenance.source_sha256.length > 0 && (
            <div>
              <dt>Huellas de la fuente (SHA-256)</dt>
              <dd className="explore-mono explore-hash">{provenance.source_sha256.join(', ')}</dd>
            </div>
          )}
        </dl>
      )}
    </section>
  )
}

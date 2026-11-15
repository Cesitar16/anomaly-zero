import { COPY } from '../content/exploreCopy'

/** Aviso de datos sintéticos. Es parte del contrato (`synthetic: true`) y no se puede ocultar ni minimizar. */
export function MockDataNotice() {
  return (
    <p className="explore-notice explore-notice--mock" role="note">
      <strong>{COPY.page.badgeDemo}.</strong> {COPY.mock}
    </p>
  )
}

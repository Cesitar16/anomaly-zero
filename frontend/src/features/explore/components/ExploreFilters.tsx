import { COPY, productLabel } from '../content/exploreCopy'
import type { FieldErrors } from '../hooks/useExplorer'
import type { DraftFilters } from '../lib/exploreUrl'
import type { Product, Region, Remote } from '../types/contracts'
import { ErrorState } from './ErrorState'

export interface ExploreFiltersProps {
  regions: Remote<Region[]>
  products: Remote<Product[]>
  draft: DraftFilters
  errors: FieldErrors
  dirty: boolean
  busy: boolean
  onRegion(regionId: string): void
  onProduct(productId: string): void
  onStart(value: string): void
  onEnd(value: string): void
  onSubmit(): void
  onRetryCatalog(): void
}

interface FieldProps {
  id: string
  label: string
  error?: string
  hint?: string
  children: (describedBy: string | undefined) => React.ReactNode
}

function Field({ id, label, error, hint, children }: FieldProps) {
  const ids = [hint ? `${id}-hint` : null, error ? `${id}-error` : null].filter(Boolean)
  const describedBy = ids.length > 0 ? ids.join(' ') : undefined
  return (
    <div className="explore-field">
      <label htmlFor={id}>{label}</label>
      {children(describedBy)}
      {hint && (
        <p id={`${id}-hint`} className="explore-field__hint">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} className="explore-field__error">
          {error}
        </p>
      )}
    </div>
  )
}

/** Filtros del explorador: región, variable NASA y rango de meses. No consulta nada hasta pulsar «Ver serie». */
export function ExploreFilters(props: ExploreFiltersProps) {
  const { regions, products, draft, errors, dirty, busy } = props
  const regionList = regions.status === 'success' ? regions.data : []
  const productList = products.status === 'success' ? products.data : []
  const selectedRegion = regionList.find((region) => region.region_id === draft.regionId)
  const selectedProduct = productList.find((product) => product.product_id === draft.productId)

  const regionPlaceholder =
    regions.status === 'loading'
      ? COPY.filters.loading.regions
      : regionList.length === 0
        ? COPY.filters.noRegions
        : COPY.filters.choose.region
  const productPlaceholder =
    draft.regionId === ''
      ? COPY.filters.choose.product
      : products.status === 'loading'
        ? COPY.filters.loading.products
        : COPY.filters.choose.product

  const catalogFailure =
    regions.status === 'error' ? regions.failure : products.status === 'error' ? products.failure : null

  return (
    <form
      className="explore-filters"
      aria-labelledby="explore-filters-title"
      noValidate
      onSubmit={(event) => {
        event.preventDefault()
        if (!busy) props.onSubmit()
      }}
    >
      <h2 id="explore-filters-title" className="explore-panel__title">
        {COPY.filters.title}
      </h2>

      {catalogFailure && <ErrorState failure={catalogFailure} onRetry={props.onRetryCatalog} />}

      <div className="explore-filters__grid">
        <Field
          id="explore-region"
          label={COPY.filters.region}
          error={errors.region}
          hint={
            selectedRegion
              ? selectedRegion.area_km2 !== null
                ? COPY.filters.area(selectedRegion.area_km2.toLocaleString('es-CL'))
                : undefined
              : undefined
          }
        >
          {(describedBy) => (
            <select
              id="explore-region"
              value={draft.regionId}
              disabled={regionList.length === 0}
              aria-invalid={errors.region ? true : undefined}
              aria-describedby={describedBy}
              onChange={(event) => props.onRegion(event.target.value)}
            >
              <option value="">{regionPlaceholder}</option>
              {regionList.map((region) => (
                <option key={region.region_id} value={region.region_id}>
                  {region.name}
                </option>
              ))}
            </select>
          )}
        </Field>

        <Field
          id="explore-product"
          label={COPY.filters.product}
          error={errors.product}
          hint={
            selectedProduct
              ? selectedProduct.availability === 'unavailable'
                ? COPY.filters.productUnavailable
                : selectedProduct.coverage
                  ? COPY.filters.coverage(selectedProduct.coverage.start, selectedProduct.coverage.end)
                  : undefined
              : productList.length === 0 && products.status === 'success'
                ? COPY.filters.productsEmpty
                : undefined
          }
        >
          {(describedBy) => (
            <select
              id="explore-product"
              value={draft.productId}
              disabled={draft.regionId === '' || productList.length === 0}
              aria-invalid={errors.product ? true : undefined}
              aria-describedby={describedBy}
              onChange={(event) => props.onProduct(event.target.value)}
            >
              <option value="">{productPlaceholder}</option>
              {productList.map((product) => (
                <option key={product.product_id} value={product.product_id}>
                  {productLabel(product)} · {product.unit}
                  {product.availability === 'available' ? '' : ` (${COPY.availability[product.availability]})`}
                </option>
              ))}
            </select>
          )}
        </Field>

        <Field id="explore-start" label={COPY.filters.start} error={errors.start} hint={COPY.filters.formatHelp}>
          {(describedBy) => (
            <input
              id="explore-start"
              type="text"
              inputMode="numeric"
              autoComplete="off"
              placeholder="2005-01"
              value={draft.start}
              aria-invalid={errors.start ? true : undefined}
              aria-describedby={describedBy}
              onChange={(event) => props.onStart(event.target.value.trim())}
            />
          )}
        </Field>

        <Field id="explore-end" label={COPY.filters.end} error={errors.end} hint={COPY.filters.help}>
          {(describedBy) => (
            <input
              id="explore-end"
              type="text"
              inputMode="numeric"
              autoComplete="off"
              placeholder="2005-03"
              value={draft.end}
              aria-invalid={errors.end ? true : undefined}
              aria-describedby={describedBy}
              onChange={(event) => props.onEnd(event.target.value.trim())}
            />
          )}
        </Field>
      </div>

      <div className="explore-filters__actions">
        <button type="submit" className="btn btn--primary" disabled={busy}>
          {busy ? COPY.filters.submitBusy : COPY.filters.submit}
        </button>
        <p className="explore-filters__dirty" role="status">
          {dirty ? COPY.filters.dirty : ''}
        </p>
      </div>
    </form>
  )
}

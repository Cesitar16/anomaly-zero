import { SECTION_IDS } from '../../config/site'
import { SOURCES, doiUrl } from '../../content/sources'
import ExternalLink from '../ui/ExternalLink'
import Section from '../ui/Section'

export default function SourcesSection() {
  const {
    eyebrow,
    title,
    intro,
    resourcesHeading,
    resources,
    productsHeading,
    productsIntro,
    products,
    disclaimer,
  } = SOURCES

  return (
    <Section id={SECTION_IDS.sources} eyebrow={eyebrow} title={title} intro={intro} tone="surface">
      <div className="sources__group">
        <h3 className="sources__heading">{resourcesHeading}</h3>
        <ul className="source-list">
          {resources.map((resource) => (
            <li key={resource.name} className="source-item">
              <ExternalLink href={resource.href} className="source-item__name">
                {resource.name}
              </ExternalLink>
              <p className="source-item__owner">{resource.owner}</p>
              <p className="source-item__note">{resource.note}</p>
            </li>
          ))}
        </ul>
      </div>

      <div className="sources__group">
        <h3 className="sources__heading">{productsHeading}</h3>
        <p className="sources__lead">{productsIntro}</p>
        <ul className="source-list">
          {products.map((product) => (
            <li key={product.doi} className="source-item">
              <p className="source-item__name">{product.name}</p>
              <p className="source-item__owner">{product.owner}</p>
              <p className="source-item__note">
                <ExternalLink href={doiUrl(product.doi)}>DOI {product.doi}</ExternalLink>
              </p>
            </li>
          ))}
        </ul>
      </div>

      <div className="notice" role="note">
        <h3 className="notice__title">{disclaimer.title}</h3>
        <p>{disclaimer.text}</p>
      </div>
    </Section>
  )
}

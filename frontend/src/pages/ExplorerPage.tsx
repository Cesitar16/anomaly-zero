import Badge from '../components/ui/Badge'
import ButtonLink from '../components/ui/ButtonLink'
import Container from '../components/ui/Container'
import { ROUTES, SITE } from '../config/site'
import { EXPLORER } from '../content/explorer'
import useDocumentTitle from '../hooks/useDocumentTitle'

/**
 * Ruta reservada del explorador (/explore).
 * Hoy es un placeholder explícito: no hay datos, gráficos ni mapas, ni siquiera de ejemplo.
 * Cuando exista el explorador real, esta página es el punto de montaje (ver EXPLORER_AVAILABLE).
 */
export default function ExplorerPage() {
  const { title, statusLabel, lead, whenReadyHeading, whenReady, emptyPanelLabel, emptyPanelText } =
    EXPLORER.page

  useDocumentTitle(`${title} (${statusLabel.toLowerCase()}) | ${SITE.name}`)

  return (
    <section className="explore" aria-labelledby="explore-titulo">
      <Container>
        <div className="explore__header">
          <h1 id="explore-titulo" className="explore__title" tabIndex={-1}>
            {title} <Badge status="in-progress">{statusLabel}</Badge>
          </h1>
          <p className="explore__lead">{lead}</p>
        </div>

        <div className="explore__panel">
          <p className="explore__panel-label">{emptyPanelLabel}</p>
          <p className="explore__panel-text">{emptyPanelText}</p>
        </div>

        <div className="explore__ready">
          <h2>{whenReadyHeading}</h2>
          <ul className="explore__ready-list">
            {whenReady.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="explore__actions">
          <ButtonLink to={ROUTES.home} variant="primary">
            Volver al inicio
          </ButtonLink>
        </div>
      </Container>
    </section>
  )
}

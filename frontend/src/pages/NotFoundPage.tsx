import ButtonLink from '../components/ui/ButtonLink'
import Container from '../components/ui/Container'
import { ROUTES, SITE } from '../config/site'
import useDocumentTitle from '../hooks/useDocumentTitle'

export default function NotFoundPage() {
  useDocumentTitle(`Página no encontrada | ${SITE.name}`)

  return (
    <section className="explore" aria-labelledby="notfound-titulo">
      <Container>
        <div className="explore__header">
          <h1 id="notfound-titulo" className="explore__title" tabIndex={-1}>
            Página no encontrada
          </h1>
          <p className="explore__lead">La dirección que buscas no existe en este sitio.</p>
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

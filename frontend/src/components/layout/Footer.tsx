import { Link } from 'react-router-dom'
import { EXPLORER_STATUS_LABEL, ROUTES, SITE } from '../../config/site'
import { NAV_LINKS } from '../../content/navigation'
import { SOURCES } from '../../content/sources'
import Container from '../ui/Container'

export default function Footer() {
  return (
    <footer className="site-footer">
      <Container>
        <div className="site-footer__grid">
          <div>
            <p className="site-footer__heading">{SITE.name}</p>
            <p>
              Proyecto en desarrollo del NASA Space Apps Challenge {SITE.year}. Esta página es una
              presentación y no contiene datos reales.
            </p>
          </div>

          <nav aria-label="Pie de página">
            <p className="site-footer__heading">Secciones</p>
            <ul className="site-footer__list">
              {NAV_LINKS.map(({ label, to }) => (
                <li key={label}>
                  <Link to={to}>{label}</Link>
                </li>
              ))}
              <li>
                <Link to={ROUTES.explore}>
                  Explorador{EXPLORER_STATUS_LABEL ? ` (${EXPLORER_STATUS_LABEL.toLowerCase()})` : ''}
                </Link>
              </li>
            </ul>
          </nav>

          <div>
            <p className="site-footer__heading">{SOURCES.disclaimer.title}</p>
            <p>{SOURCES.disclaimer.text}</p>
          </div>
        </div>

        <p className="site-footer__bottom">
          © {SITE.year} {SITE.name}. Proyecto independiente.
        </p>
      </Container>
    </footer>
  )
}

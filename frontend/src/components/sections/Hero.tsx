import { ROUTES, SECTION_IDS, SITE } from '../../config/site'
import ButtonLink from '../ui/ButtonLink'
import Container from '../ui/Container'
import ExplorerCta from '../ui/ExplorerCta'
import HeroArt from './HeroArt'

export default function Hero() {
  return (
    <section className="hero" aria-labelledby="hero-titulo">
      <Container>
        <div className="hero__grid">
          <div>
            <p className="eyebrow">NASA Space Apps Challenge {SITE.year} · Proyecto independiente</p>
            <h1 id="hero-titulo" className="hero__title">
              {SITE.name}
            </h1>
            <p className="hero__lead">{SITE.tagline}</p>
            <p className="hero__support">
              Una herramienta en desarrollo para elegir una variable, una región y un período,
              observar cómo evoluciona y estimar cuánto cambia y con qué respaldo estadístico.
            </p>

            <div className="hero__actions">
              <ExplorerCta variant="accent" />
              <ButtonLink
                to={{ pathname: ROUTES.home, hash: `#${SECTION_IDS.solution}` }}
                variant="secondary"
              >
                Conoce la propuesta
              </ButtonLink>
            </div>

            <p className="hero__note">
              Esta página es una presentación. Todavía no muestra datos, tendencias ni mapas reales.
            </p>
          </div>

          <HeroArt />
        </div>
      </Container>
    </section>
  )
}

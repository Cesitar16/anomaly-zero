import type { ReactNode } from 'react'
import type { SectionTone } from '../../types'
import Container from './Container'

interface SectionProps {
  id: string
  title: string
  eyebrow?: string
  intro?: string
  tone?: SectionTone
  children: ReactNode
}

/**
 * Sección de página con encabezado estándar (eyebrow, h2, introducción).
 * - Genera el id del título a partir del `id` de la sección, para aria-labelledby.
 * - El h2 es enfocable por código (tabIndex -1) para que, al navegar con un ancla,
 *   el foco del teclado y de los lectores de pantalla llegue a la sección.
 */
export default function Section({
  id,
  eyebrow,
  title,
  intro,
  tone = 'paper',
  children,
}: SectionProps) {
  const titleId = `${id}-titulo`

  return (
    <section id={id} className={`section section--${tone}`} aria-labelledby={titleId}>
      <Container>
        <div className="section__header">
          {eyebrow && <p className="eyebrow">{eyebrow}</p>}
          <h2 id={titleId} className="section__title" tabIndex={-1}>
            {title}
          </h2>
          {intro && <p className="section__intro">{intro}</p>}
        </div>
        {children}
      </Container>
    </section>
  )
}

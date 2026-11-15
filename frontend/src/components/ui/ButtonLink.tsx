import type { ReactNode } from 'react'
import { Link, type To } from 'react-router-dom'
import type { ButtonVariant } from '../../types'
import ExternalLink from './ExternalLink'

/** Un botón-enlace va a una ruta interna (`to`) o a una URL externa (`href`), nunca a ambas. */
type LinkTarget = { to: To; href?: never } | { href: string; to?: never }

type ButtonLinkProps = LinkTarget & {
  variant?: ButtonVariant
  children: ReactNode
}

/**
 * Enlace con aspecto de botón. Es polimórfico: decide por sí mismo qué elemento
 * renderizar según el destino.
 *   - `to`   -> <Link> de React Router (navegación interna, sin recargar)
 *   - `href` -> <a> externo seguro
 *
 * Semántica: es un enlace porque navega. Un <button> sería incorrecto aquí.
 * El tipo `LinkTarget` hace imposible por compilación pasar `to` y `href` a la vez.
 */
export default function ButtonLink({ variant = 'primary', children, ...target }: ButtonLinkProps) {
  const className = `btn btn--${variant}`

  if (target.href !== undefined) {
    return (
      <ExternalLink href={target.href} className={className}>
        {children}
      </ExternalLink>
    )
  }

  return (
    <Link to={target.to} className={className}>
      {children}
    </Link>
  )
}

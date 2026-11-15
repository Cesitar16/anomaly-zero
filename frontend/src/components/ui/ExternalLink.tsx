import type { ReactNode } from 'react'

interface ExternalLinkProps {
  href: string
  className?: string
  children: ReactNode
}

/**
 * Enlace a un sitio externo. Se abre en pestaña nueva de forma segura y avisa
 * a los lectores de pantalla.
 */
export default function ExternalLink({ href, className, children }: ExternalLinkProps) {
  return (
    <a href={href} className={className} target="_blank" rel="noopener noreferrer">
      {children}
      <svg
        className="external-icon"
        viewBox="0 0 16 16"
        aria-hidden="true"
        focusable="false"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M6 3H3v10h10v-3" />
        <path d="M9 2.5h4.5V7" />
        <path d="M13.5 2.5 7.5 8.5" />
      </svg>
      <span className="sr-only"> (se abre en una pestaña nueva)</span>
    </a>
  )
}

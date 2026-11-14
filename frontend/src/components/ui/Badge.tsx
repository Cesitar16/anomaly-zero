import type { ReactNode } from 'react'
import type { BadgeStatus } from '../../types'

interface BadgeProps {
  status?: BadgeStatus
  children: ReactNode
}

/**
 * Etiqueta de estado. El significado siempre va en texto (no solo en color),
 * y lleva un punto como refuerzo visual. TypeScript impide pasar un estado inválido.
 */
export default function Badge({ status = 'planned', children }: BadgeProps) {
  return <span className={`badge badge--${status}`}>{children}</span>
}

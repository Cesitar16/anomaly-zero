import { EXPLORER_STATUS, EXPLORER_STATUS_LABEL, ROUTES } from '../../config/site'
import type { ButtonVariant } from '../../types'
import ButtonLink from './ButtonLink'

interface ExplorerCtaProps {
  variant?: ButtonVariant
}

/**
 * Llamada a la acción hacia el explorador.
 * Es el único componente que conoce el estado del explorador (feature flag),
 * así que hero, barra y sección de acceso se mantienen coherentes.
 */
export default function ExplorerCta({ variant = 'accent' }: ExplorerCtaProps) {
  return (
    <ButtonLink to={ROUTES.explore} variant={variant}>
      {EXPLORER_STATUS === 'in-development' ? 'Ver estado del explorador' : 'Abrir el explorador'}
      {EXPLORER_STATUS_LABEL && <span className="btn__tag">{EXPLORER_STATUS_LABEL}</span>}
    </ButtonLink>
  )
}

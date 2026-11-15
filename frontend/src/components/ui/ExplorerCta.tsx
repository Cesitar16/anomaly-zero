import { EXPLORER_AVAILABLE, ROUTES } from '../../config/site'
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
      {EXPLORER_AVAILABLE ? 'Abrir el explorador' : 'Ver estado del explorador'}
      {!EXPLORER_AVAILABLE && <span className="btn__tag">En desarrollo</span>}
    </ButtonLink>
  )
}

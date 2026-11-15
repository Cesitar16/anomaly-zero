import { useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'

const prefersReducedMotion = (): boolean =>
  window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false

/**
 * Gestiona scroll y foco cuando cambia la ubicación (React Router no lo hace solo).
 *  - Con ancla (#problema): desplaza hasta la sección y enfoca su título.
 *  - Sin ancla: vuelve arriba y enfoca <main>, para que teclado y lectores de pantalla
 *    "aterricen" en la nueva página.
 * No actúa en la primera carga: así el enlace "Saltar al contenido" sigue siendo
 * lo primero que alcanza quien navega con Tab.
 */
export default function ScrollManager() {
  const { pathname, hash } = useLocation()
  const isFirstRender = useRef(true)

  useEffect(() => {
    const isInitialLoad = isFirstRender.current
    isFirstRender.current = false

    if (hash) {
      const target = document.getElementById(decodeURIComponent(hash.slice(1)))
      if (target) {
        target.scrollIntoView?.({
          behavior: prefersReducedMotion() || isInitialLoad ? 'auto' : 'smooth',
          block: 'start',
        })
        if (!isInitialLoad) {
          target.querySelector<HTMLElement>('h1, h2')?.focus({ preventScroll: true })
        }
        return
      }
    }

    if (isInitialLoad) return
    window.scrollTo({ top: 0, left: 0, behavior: 'auto' })
    document.getElementById('contenido')?.focus({ preventScroll: true })
  }, [pathname, hash])

  return null
}

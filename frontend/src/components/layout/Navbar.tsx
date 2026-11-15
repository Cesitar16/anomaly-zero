import { useEffect, useRef, useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { EXPLORER_STATUS_LABEL, ROUTES } from '../../config/site'
import { NAV_LINKS } from '../../content/navigation'
import Logo from './Logo'

const MENU_ID = 'menu-principal'

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false)
  const toggleRef = useRef<HTMLButtonElement>(null)

  const closeMenu = () => setIsOpen(false)

  // Escape cierra el menú móvil y devuelve el foco al botón que lo abrió.
  useEffect(() => {
    if (!isOpen) return undefined

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false)
        toggleRef.current?.focus()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen])

  return (
    <header className="site-header">
      <div className="container site-header__inner">
        <Link to={ROUTES.home} aria-label="Anomaly Zero, ir al inicio" onClick={closeMenu}>
          <Logo />
        </Link>

        <button
          ref={toggleRef}
          type="button"
          className="nav-toggle"
          aria-expanded={isOpen}
          aria-controls={MENU_ID}
          onClick={() => setIsOpen((open) => !open)}
        >
          <span className="nav-toggle__bars" aria-hidden="true" />
          Menú
        </button>

        <nav id={MENU_ID} aria-label="Principal" className={`site-nav${isOpen ? ' is-open' : ''}`}>
          <ul className="site-nav__list">
            {NAV_LINKS.map(({ label, to }) => (
              <li key={label}>
                <Link to={to} className="site-nav__link" onClick={closeMenu}>
                  {label}
                </Link>
              </li>
            ))}
            <li>
              <NavLink to={ROUTES.explore} className="site-nav__link" onClick={closeMenu}>
                Explorador
                {EXPLORER_STATUS_LABEL && <span className="site-nav__tag">{EXPLORER_STATUS_LABEL}</span>}
              </NavLink>
            </li>
          </ul>
        </nav>
      </div>
    </header>
  )
}

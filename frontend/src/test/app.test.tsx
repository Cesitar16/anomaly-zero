import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import axe from 'axe-core'
import { describe, expect, it } from 'vitest'
import { SECTION_IDS } from '../config/site'
import { renderApp } from './renderApp'

/**
 * axe-core en jsdom no puede medir contraste (no hay motor de render).
 * El contraste se verifica aparte en contrast.test.ts.
 */
async function expectNoA11yViolations(root: HTMLElement) {
  const results = await axe.run(root, { rules: { 'color-contrast': { enabled: false } } })
  const summary = results.violations.map(
    (violation) => `${violation.id}: ${violation.nodes.map((node) => node.html).join(' | ')}`,
  )
  expect(summary).toEqual([])
}

describe('Landing (/)', () => {
  it('tiene un único h1 y los landmarks principales', () => {
    renderApp('/')

    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1)
    expect(screen.getByRole('heading', { level: 1, name: 'Anomaly Zero' })).toBeInTheDocument()
    expect(screen.getByRole('banner')).toBeInTheDocument()
    expect(screen.getByRole('main')).toBeInTheDocument()
    expect(screen.getByRole('contentinfo')).toBeInTheDocument()
    expect(screen.getByRole('navigation', { name: 'Principal' })).toBeInTheDocument()
  })

  it('incluye las secciones requeridas, cada una como región con nombre', () => {
    renderApp('/')

    Object.values(SECTION_IDS).forEach((id) => {
      const section = document.getElementById(id)
      expect(section, `falta la sección #${id}`).toBeInTheDocument()
      const title = within(section as HTMLElement).getByRole('heading', { level: 2 })
      expect(section).toHaveAccessibleName(title.textContent ?? '')
    })
  })

  it('muestra la promesa verificable del hero', () => {
    renderApp('/')
    expect(
      screen.getByText(
        'Explora cómo cambian las variables ambientales y qué evidencia respaldan sus tendencias.',
      ),
    ).toBeInTheDocument()
  })

  it('el acceso al explorador apunta a /explore y dice "En desarrollo"', () => {
    renderApp('/')

    const ctas = screen.getAllByRole('link', { name: /Ver estado del explorador/i })
    expect(ctas.length).toBeGreaterThanOrEqual(2) // hero y sección de acceso
    ctas.forEach((cta) => {
      expect(cta).toHaveAttribute('href', '/explore')
      expect(cta).toHaveTextContent('En desarrollo')
    })
  })

  it('incluye el aviso de proyecto independiente', () => {
    renderApp('/')
    expect(
      screen.getAllByText(/no está desarrollado, patrocinado ni respaldado por la NASA/i).length,
    ).toBeGreaterThanOrEqual(1)
  })

  it('los enlaces externos abren en pestaña nueva de forma segura', () => {
    renderApp('/')

    const external = screen
      .getAllByRole('link')
      .filter((link) => link.getAttribute('href')?.startsWith('http'))

    expect(external.length).toBeGreaterThan(0)
    external.forEach((link) => {
      expect(link).toHaveAttribute('target', '_blank')
      expect(link.getAttribute('rel')).toContain('noopener')
      expect(link.getAttribute('href')).toMatch(/^https:\/\//)
    })
  })

  it('no tiene violaciones de accesibilidad detectables por axe', async () => {
    const { container } = renderApp('/')
    await expectNoA11yViolations(container.ownerDocument.body)
  })
})

describe('Menú móvil', () => {
  it('se abre con el botón, y Escape lo cierra devolviendo el foco', async () => {
    const user = userEvent.setup()
    renderApp('/')

    const toggle = screen.getByRole('button', { name: 'Menú' })
    expect(toggle).toHaveAttribute('aria-expanded', 'false')

    await user.click(toggle)
    expect(toggle).toHaveAttribute('aria-expanded', 'true')

    await user.keyboard('{Escape}')
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    expect(toggle).toHaveFocus()
  })
})

describe('Explorador (/explore)', () => {
  it('es un placeholder explícito, sin datos simulados', () => {
    const { container } = renderApp('/explore')

    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      /Explorador de tendencias\s*En desarrollo/,
    )
    expect(screen.getByText(/no hay ningún dato, gráfico ni mapa/i)).toBeInTheDocument()
    expect(container.querySelector('canvas, img, [role="img"], table')).toBeNull()
  })

  it('no tiene violaciones de accesibilidad detectables por axe', async () => {
    const { container } = renderApp('/explore')
    await expectNoA11yViolations(container.ownerDocument.body)
  })
})

describe('Ruta desconocida', () => {
  it('muestra una página 404 con salida al inicio', () => {
    renderApp('/no-existe')

    expect(
      screen.getByRole('heading', { level: 1, name: 'Página no encontrada' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Volver al inicio' })).toHaveAttribute('href', '/')
  })
})

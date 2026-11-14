import { readFileSync } from 'node:fs'
import { resolve as resolvePath } from 'node:path'
import { describe, expect, it } from 'vitest'

/**
 * Verifica el contraste WCAG AA (4,5:1) de cada par texto/fondo que usa la interfaz.
 * Lee los colores reales de src/styles/tokens.css, así que si alguien cambia un
 * token y rompe el contraste, este test falla.
 */
// `npm test` se ejecuta desde la raíz de frontend/
const tokensCss = readFileSync(resolvePath(process.cwd(), 'src/styles/tokens.css'), 'utf8')

const tokens: Record<string, string> = Object.fromEntries(
  [...tokensCss.matchAll(/--([\w-]+):\s*(#[0-9a-fA-F]{6})\s*;/g)].map(([, name, hex]) => [
    name,
    hex,
  ]),
)

const channel = (value: number): number => {
  const c = value / 255
  return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
}

const luminance = (hex: string): number => {
  const [r, g, b] = [1, 3, 5].map((i) => channel(parseInt(hex.slice(i, i + 2), 16)))
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

const contrast = (a: string, b: string): number => {
  const [light, dark] = [luminance(a), luminance(b)].sort((x, y) => y - x)
  return (light + 0.05) / (dark + 0.05)
}

const WHITE = '#ffffff'
// Fondo más claro del degradado del hero (rgb(47 91 102 / .55) sobre --color-deep)
const HERO_GRADIENT_PEAK = '#20444e'

type Pair = [foreground: string, background: string, usage: string]

const PAIRS: Pair[] = [
  ['ink', 'paper', 'texto general'],
  ['ink', 'surface', 'texto general sobre blanco'],
  ['muted', 'paper', 'texto secundario'],
  ['muted', 'surface', 'texto secundario sobre blanco'],
  ['primary', 'paper', 'enlaces sobre papel'],
  ['primary', 'surface', 'enlaces sobre blanco'],
  ['accent-ink', 'paper', 'eyebrow, roles y fuentes'],
  ['accent-ink', 'surface', 'eyebrow sobre blanco'],
  [WHITE, 'primary', 'botón primario y avatares'],
  [WHITE, 'primary-hover', 'botón primario (hover)'],
  ['deep-sunken', 'accent', 'botón de acento'],
  ['on-deep', 'deep', 'texto sobre oscuro'],
  ['on-deep-muted', 'deep', 'texto secundario sobre oscuro'],
  ['on-deep', 'deep-raised', 'texto en tarjetas oscuras'],
  ['on-deep-muted', 'deep-raised', 'texto secundario en tarjetas oscuras'],
  ['accent', 'deep', 'eyebrow, enlaces y números sobre oscuro'],
  ['accent', 'deep-raised', 'enlaces en tarjetas oscuras'],
  ['on-deep', 'deep-sunken', 'pie de página'],
  ['on-deep-muted', 'deep-sunken', 'pie de página (texto secundario)'],
  ['on-deep-muted', HERO_GRADIENT_PEAK, 'texto del hero sobre el degradado'],
  ['on-deep', HERO_GRADIENT_PEAK, 'texto del hero sobre el degradado'],
  ['badge-available-fg', 'badge-available-bg', 'badge Disponible'],
  ['badge-progress-fg', 'badge-progress-bg', 'badge En desarrollo'],
  ['badge-planned-fg', 'badge-planned-bg', 'badge Planificado'],
  ['badge-candidate-fg', 'badge-candidate-bg', 'badge Candidata'],
]

const resolveColor = (value: string): string | undefined =>
  value.startsWith('#') ? value : (tokens[`color-${value}`] ?? tokens[value])

describe('Contraste de color (WCAG AA)', () => {
  it('encuentra los tokens de color', () => {
    expect(Object.keys(tokens).length).toBeGreaterThan(10)
  })

  it.each(PAIRS)('%s sobre %s (%s) cumple 4,5:1', (fg, bg, usage) => {
    const foreground = resolveColor(fg)
    const background = resolveColor(bg)
    if (!foreground || !background) throw new Error(`token no encontrado: ${fg} o ${bg}`)
    expect(contrast(foreground, background), usage).toBeGreaterThanOrEqual(4.5)
  })
})

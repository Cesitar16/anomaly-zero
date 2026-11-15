import { describe, expect, it } from 'vitest'
import { EXPLORER } from '../content/explorer'
import { HOW_IT_WORKS } from '../content/howItWorks'
import { PROBLEM } from '../content/problem'
import { SOLUTION } from '../content/solution'
import { SOURCES } from '../content/sources'
import { TEAM } from '../content/team'

/**
 * Guardas de honestidad de la tarjeta FE-01:
 * la landing no puede publicar tendencias, valores p ni cifras de resultados,
 * ni contactos del equipo.
 */
const ALL_CONTENT = { PROBLEM, SOLUTION, HOW_IT_WORKS, TEAM, SOURCES, EXPLORER }

const collectStrings = (value: unknown): string[] => {
  if (typeof value === 'string') return [value]
  if (Array.isArray(value)) return value.flatMap(collectStrings)
  if (value && typeof value === 'object') return Object.values(value).flatMap(collectStrings)
  return []
}

const allText = collectStrings(ALL_CONTENT).join('\n')

describe('Guardas de contenido (sin resultados inventados)', () => {
  const forbidden: [RegExp, string][] = [
    [/\bp\s*[=<>≤]\s*0[.,]\d/i, 'valor p'],
    [/valor(es)?\s+p\s*[=<>]/i, 'valor p'],
    [/\d+[.,]?\d*\s*°\s*C\s*(\/|por)\s*(década|año)/i, 'tasa de cambio con cifra'],
    [/\d+[.,]?\d*\s*%/, 'porcentaje'],
    [
      /\b(aument[oó]|disminuy[oó]|ha subido|ha bajado|se ha calentado|se ha secado)\b/i,
      'afirmación de cambio observado',
    ],
  ]

  it.each(forbidden)('no contiene %s', (pattern, label) => {
    expect(allText, label).not.toMatch(pattern)
  })

  it('no publica contactos del equipo (correos, teléfonos, redes)', () => {
    const teamText = collectStrings(TEAM.members).join('\n')
    expect(teamText).not.toMatch(/@|https?:\/\/|\+?\d{7,}/)
  })

  it('no publica correos ni teléfonos en ninguna parte del contenido', () => {
    expect(allText).not.toMatch(/[\w.+-]+@[\w-]+\.[\w.]+/)
    expect(allText).not.toMatch(/\+?\d[\d\s-]{8,}\d/)
  })
})

describe('Atribuciones', () => {
  it('cada producto candidato tiene productor, distribuidor y DOI', () => {
    SOURCES.products.forEach((product) => {
      expect(product.owner).toMatch(/NASA/)
      expect(product.doi).toMatch(/^10\.\d{4,}\//)
    })
  })

  it('cada recurso enlazado usa https y tiene responsable', () => {
    const linked = [
      ...SOURCES.resources,
      PROBLEM.challengeNote,
      TEAM.teamPage,
      TEAM.event.link,
    ]
    linked.forEach((item) => expect(item.href).toMatch(/^https:\/\//))
    SOURCES.resources.forEach((resource) => expect(resource.owner).toBeTruthy())
  })

  it('el aviso aclara que no hay respaldo institucional', () => {
    expect(SOURCES.disclaimer.text).toMatch(/independiente/i)
    expect(SOURCES.disclaimer.text).toMatch(/no está desarrollado, patrocinado ni respaldado/i)
  })

  it('las variables candidatas y la región están marcadas como propuesta, no como decisión', () => {
    expect(HOW_IT_WORKS.scopeNote).toMatch(/propuesta de trabajo/i)
    expect(HOW_IT_WORKS.scopeNote).toMatch(/aún no están aprobados/i)
  })
})

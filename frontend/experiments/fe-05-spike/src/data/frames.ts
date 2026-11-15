import type { FrameManifest } from '../types'
import raw from './frames.manifest.json'

function fail(reason: string): never {
  throw new Error(`frames.manifest.json inválido: ${reason}`)
}

/** Valida el manifiesto en tiempo de ejecución en vez de confiar en un `as`. */
export function parseManifest(input: unknown): FrameManifest {
  if (typeof input !== 'object' || input === null) fail('no es un objeto')
  const value = input as Record<string, unknown>
  if (value.synthetic !== true) fail('debe declarar synthetic: true')
  const bbox = value.bbox as Record<string, unknown> | undefined
  for (const side of ['west', 'south', 'east', 'north']) {
    if (typeof bbox?.[side] !== 'number') fail(`bbox.${side} no es un número`)
  }
  if (!Array.isArray(value.months) || value.months.length === 0) fail('months vacío')
  const scale = value.scale as { classes?: unknown } | undefined
  if (!Array.isArray(scale?.classes) || scale.classes.length === 0) fail('scale.classes vacío')
  if (typeof value.crs !== 'string') fail('crs ausente')
  return input as FrameManifest
}

export const FRAME_MANIFEST: FrameManifest = parseManifest(raw)

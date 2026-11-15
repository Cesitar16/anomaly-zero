import type { FrameManifest, ImageVariant, MapMode, RasterLayer, YearMonth } from '../types'

export type FrameTarget =
  | { kind: 'frame'; url: string }
  | { kind: 'missing'; reason: string; message: string }

/**
 * Decide qué debe mostrar el mapa para un mes. Es una función pura para poder probar sin WebGL
 * las dos reglas que importan:
 *
 *  - modo `contract`: la fuente de verdad es `RasterLayer`. Con `state !== 'available'` o sin
 *    `tile_template`, NO hay capa y NO se hace ninguna petición (jamás se inventa una URL).
 *  - modo `prototype-frames`: recursos visuales locales y sintéticos del spike, separados del contrato.
 *    Si el mes no tiene frame, se declara ausente; nunca se reutiliza el de otro mes.
 */
export function resolveFrameTarget(input: {
  month: YearMonth
  mode: MapMode
  variant: ImageVariant
  manifest: FrameManifest
  rasterLayers: RasterLayer[]
  basePath: string
}): FrameTarget {
  const { month, mode, variant, manifest, rasterLayers, basePath } = input

  if (mode === 'contract') {
    const layer = rasterLayers.find((candidate) => candidate.date === month && candidate.layer_type === 'value')
    if (!layer) {
      return { kind: 'missing', reason: 'no_raster_layer_descriptor', message: 'La respuesta no trae descriptor de capa para este mes.' }
    }
    if (layer.state !== 'available' || layer.tile_template === null) {
      return {
        kind: 'missing',
        reason: 'raster_layer_unavailable',
        message: 'La API declara esta capa como no disponible (state: unavailable). No se carga ninguna imagen ni teselas.',
      }
    }
    // Un tile_template real exige formato, licencia, procedencia y CRS aprobados (Gate M). Fuera del spike.
    return {
      kind: 'missing',
      reason: 'tile_template_not_supported_in_spike',
      message: 'El spike no consume tile_template: falta el Gate M y un backend real.',
    }
  }

  const entry = manifest.months.find((candidate) => candidate.date === month)
  if (!entry || entry.frame === null) {
    const intentional = entry?.reason === 'intentional_absent_synthetic'
    return {
      kind: 'missing',
      reason: entry?.reason ?? 'no_frame_provided',
      message: intentional
        ? 'Mes ausente a propósito en este fixture sintético. No se reemplaza por otro mes.'
        : 'Este fixture no incluye frame para el mes. No se reemplaza por otro mes.',
    }
  }
  return { kind: 'frame', url: `${basePath}frames/${variant}/${entry.frame}` }
}

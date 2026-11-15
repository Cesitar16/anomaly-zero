import type { RasterLayer, YearMonth } from '../types/contracts'

export interface Bbox {
  west: number
  south: number
  east: number
  north: number
}

/** Una imagen ya lista para dibujar sobre el mapa, con su caja geográfica. */
export interface ResolvedRaster {
  url: string
  bbox: Bbox
}

/**
 * Decide cómo se dibuja una capa. Es lo ÚNICO que sabe de formatos: el mapa no interpreta
 * `tile_template`. En modo real devuelve `null` hasta que César apruebe formato, licencia y CRS
 * (Gate M); en demostración solo reconoce las imágenes sintéticas empaquetadas con la app.
 */
export type RasterResolver = (layer: RasterLayer) => ResolvedRaster | null

/** Una capa "disponible" sin formato o sin plantilla se trata como no disponible (O4 de FE-03). */
export function isUsableValueLayer(layer: RasterLayer): boolean {
  return (
    layer.layer_type === 'value' &&
    layer.state === 'available' &&
    layer.format !== null &&
    layer.tile_template !== null
  )
}

export function valueLayerForMonth(
  layers: RasterLayer[] | undefined,
  month: YearMonth,
): RasterLayer | undefined {
  return layers?.find((layer) => layer.layer_type === 'value' && layer.date === month)
}

/** Meses que el contrato declara con capa de valor disponible. */
export function monthsWithLayer(layers: RasterLayer[] | undefined, months: YearMonth[]): Set<YearMonth> {
  const withLayer = new Set<YearMonth>()
  for (const month of months) {
    const layer = valueLayerForMonth(layers, month)
    if (layer && isUsableValueLayer(layer)) withLayer.add(month)
  }
  return withLayer
}

export type MapTarget =
  /** Ninguna capa disponible en toda la serie (E6): la API no publica capas. */
  | { kind: 'absent' }
  /** Hay capas en otros meses pero no en este (E10): se dice y no se muestra otra. */
  | { kind: 'month-absent' }
  /** La API declara la capa pero esta versión no sabe dibujarla (formato sin aprobar). */
  | { kind: 'not-drawable'; layer: RasterLayer }
  /** E9: capa disponible y dibujable. */
  | { kind: 'frame'; layer: RasterLayer; raster: ResolvedRaster }

export function resolveMapTarget(input: {
  layers: RasterLayer[] | undefined
  months: YearMonth[]
  month: YearMonth
  resolver: RasterResolver
}): MapTarget {
  const { layers, months, month, resolver } = input
  const anywhere = monthsWithLayer(layers, months)
  if (anywhere.size === 0) return { kind: 'absent' }
  const layer = valueLayerForMonth(layers, month)
  if (!layer || !isUsableValueLayer(layer)) return { kind: 'month-absent' }
  const raster = resolver(layer)
  return raster ? { kind: 'frame', layer, raster } : { kind: 'not-drawable', layer }
}

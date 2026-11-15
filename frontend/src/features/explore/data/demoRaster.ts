/**
 * Capas raster SINTÉTICAS de demostración (E9 y E10). Existen solo para el servicio simulado.
 *
 * Son tres imágenes diminutas generadas con el spike FE-05: no son IMERG, ni precipitación, ni ninguna
 * observación. El modo real no las usa: su resolvedor no dibuja ninguna capa hasta que César apruebe
 * formato, licencia y CRS (Gate M). Aquí solo se reconocen las URL de estos tres archivos empaquetados.
 */
import type { RasterLayer, YearMonth } from '../types/contracts'
import type { Bbox, RasterResolver } from '../lib/rasterTarget'
import january from './demo-frames/2005-01.png?url'
import february from './demo-frames/2005-02.png?url'
import march from './demo-frames/2005-03.png?url'

/** Caja geográfica (EPSG:4326) de las imágenes sintéticas. Solo vale para ellas. */
export const DEMO_BBOX: Bbox = { west: 138, south: -38, east: 153, north: -24 }

const DEMO_FRAME_URLS: Record<YearMonth, string> = {
  '2005-01': january,
  '2005-02': february,
  '2005-03': march,
}

export const demoRasterResolver: RasterResolver = (layer) => {
  const url = DEMO_FRAME_URLS[layer.date]
  if (url === undefined || layer.tile_template !== url) return null
  return { url, bbox: DEMO_BBOX }
}

/**
 * Descriptores `RasterLayer` conformes al esquema. `availableMonths` lista los meses con capa; el resto
 * se declara `unavailable` con `format` y `tile_template` en `null` (nunca se inventa una URL).
 */
export function demoRasterLayers(input: {
  datasetId: string
  months: YearMonth[]
  availableMonths: YearMonth[]
  unit: string
}): RasterLayer[] {
  return input.months.map((month): RasterLayer => {
    const url = DEMO_FRAME_URLS[month]
    const available = input.availableMonths.includes(month) && url !== undefined
    return {
      dataset_id: input.datasetId,
      date: month,
      layer_type: 'value',
      unit: input.unit,
      state: available ? 'available' : 'unavailable',
      format: available ? 'image/png' : null,
      tile_template: available ? url : null,
    }
  })
}

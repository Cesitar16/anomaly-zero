import type { FeatureCollection, LineString, Polygon } from 'geojson'
import { monthRange, monthStart } from '../lib/months'
import type { RasterLayer, SeriesPoint } from '../types'

// TODO el contenido de este archivo es SINTÉTICO y existe solo para el spike. Nada representa una
// observación NASA, un promedio de cuenca, una anomalía ni un resultado estadístico.

export const SERIES_MONTHS = monthRange('2005-01', '2005-12')

/** La unidad real de un producto llega en `Product.unit` del contrato. Aquí es deliberadamente ficticia. */
export const SYNTHETIC_PRODUCT = {
  variable: 'valor sintético',
  unit: 'u.a. sintéticas',
  datasetId: 'ds-synthetic-001',
} as const

const VALUES: Array<number | null> = [0.42, 0.55, 0.0, null, 0.31, 0.47, 0.62, 0.58, 0.36, 0.29, 0.44, 0.51]

function pointFor(date: string, value: number | null): SeriesPoint {
  if (value === null) {
    return { date, value, quality: { state: 'missing', provider_flags: [], missing_reason: 'provider_fill_value' } }
  }
  // 2005-09 simula un dato presente pero con calidad desconocida y un flag original del proveedor.
  if (date === '2005-09-01') {
    return {
      date,
      value,
      quality: { state: 'unknown', provider_flags: [{ name: 'synthetic_flag', value: 2 }], missing_reason: null },
    }
  }
  return { date, value, quality: { state: 'unassessed', provider_flags: [], missing_reason: null } }
}

/**
 * 12 meses con: un cero legítimo (2005-03), un faltante (2005-04, que además es el mes de frame
 * ausente a propósito) y un punto de calidad desconocida (2005-09).
 */
export const SERIES: SeriesPoint[] = SERIES_MONTHS.map((month, index) => pointFor(monthStart(month), VALUES[index]))

/**
 * Descriptores `raster_layers[]` de la respuesta de serie, con la forma del esquema `RasterLayer` del OpenAPI.
 * OJO: el OpenAPI NO trae un ejemplo oficial de `raster_layers`; estos valores son un fixture derivado del
 * esquema y de la descripción de docs/contracts-v0.md (hasta comprobar datos, `state: unavailable`,
 * `format: null`, `tile_template: null`). Significan literalmente "NO hay capa renderizable".
 */
export const RASTER_LAYERS: RasterLayer[] = SERIES_MONTHS.map((date) => ({
  dataset_id: 'ds-synthetic-001',
  date,
  layer_type: 'value',
  unit: 'mm/hr',
  state: 'unavailable',
  format: null,
  tile_template: null,
}))

type Position = [number, number]
export type LineFeatureCollection = FeatureCollection<LineString>
export type PolygonFeatureCollection = FeatureCollection<Polygon>

/** Polígono FICTICIO de prueba dentro del recuadro. No es la cuenca Murray–Darling ni ninguna geometría real. */
export const SYNTHETIC_POLYGON: PolygonFeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { synthetic: true, label: 'Polígono ficticio de prueba' },
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [142, -28],
            [146, -26.5],
            [150, -28.5],
            [149, -32],
            [151, -35],
            [146, -36],
            [143, -33],
            [142, -28],
          ] satisfies Position[],
        ],
      },
    },
  ],
}

/** Meridianos y paralelos cada 2° para comprobar a ojo la georreferenciación contra la imagen. */
export function buildGraticule(bbox: { west: number; south: number; east: number; north: number }): LineFeatureCollection {
  const features: LineFeatureCollection['features'] = []
  for (let lon = bbox.west; lon <= bbox.east; lon += 2) {
    features.push({
      type: 'Feature',
      properties: { kind: 'meridian', value: lon },
      geometry: { type: 'LineString', coordinates: [[lon, bbox.south], [lon, bbox.north]] },
    })
  }
  for (let lat = bbox.south; lat <= bbox.north; lat += 2) {
    features.push({
      type: 'Feature',
      properties: { kind: 'parallel', value: lat },
      geometry: { type: 'LineString', coordinates: [[bbox.west, lat], [bbox.east, lat]] },
    })
  }
  return { type: 'FeatureCollection', features }
}

import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs'
import { join, resolve } from 'node:path'
import { FRAME_MANIFEST, parseManifest } from '../data/frames'
import { RASTER_LAYERS, SERIES, SYNTHETIC_POLYGON } from '../data/fixtures'

// Rutas relativas a este archivo (no al directorio de ejecución), para que den lo mismo se corran
// desde el spike o desde otra raíz.
const SPIKE_ROOT = resolve(import.meta.dirname, '../..')
const SRC = resolve(SPIKE_ROOT, 'src')

function sourceFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name)
    if (statSync(path).isDirectory()) return name === 'test' ? [] : sourceFiles(path)
    return /\.(ts|tsx|css)$/.test(name) ? [path] : []
  })
}

describe('guardas de honestidad científica', () => {
  it('el manifiesto de frames declara synthetic: true y se valida en ejecución', () => {
    expect(FRAME_MANIFEST.synthetic).toBe(true)
    expect(() => parseManifest({ ...FRAME_MANIFEST, synthetic: false })).toThrow(/synthetic/)
  })

  it('los 12 descriptores raster son unavailable, sin formato y sin tile_template', () => {
    expect(RASTER_LAYERS).toHaveLength(12)
    for (const layer of RASTER_LAYERS) {
      expect(layer).toMatchObject({ layer_type: 'value', state: 'unavailable', format: null, tile_template: null })
    }
  })

  it('los descriptores tienen exactamente los campos required de RasterLayer en el OpenAPI integrado', () => {
    const openapi = resolve(SPIKE_ROOT, '../../../docs/openapi-contract-v0.yaml')
    if (!existsSync(openapi)) return // el spike puede copiarse fuera del repo
    const yaml = readFileSync(openapi, 'utf8')
    const block = yaml.split('    RasterLayer:')[1]
    const required = /required: \[([^\]]+)\]/.exec(block)?.[1].split(',').map((field) => field.trim())
    expect(required).toBeDefined()
    expect(Object.keys(RASTER_LAYERS[0]).sort()).toEqual([...(required ?? [])].sort())
  })

  it('el polígono de prueba es un Polygon cerrado y marcado como sintético (nunca un LineString como cuenca)', () => {
    for (const feature of SYNTHETIC_POLYGON.features) {
      expect(feature.properties).toMatchObject({ synthetic: true })
      expect(feature.geometry.type).toBe('Polygon')
      const ring = feature.geometry.coordinates[0]
      expect(ring[0]).toEqual(ring.at(-1))
    }
  })

  it('la serie tiene un cero real, un null y ningún NaN', () => {
    const values = SERIES.map((point) => point.value)
    expect(values).toContain(0)
    expect(values).toContain(null)
    expect(values.every((value) => value === null || Number.isFinite(value))).toBe(true)
  })

  it('el código no usa la geometría de ejemplo LineString', () => {
    for (const file of sourceFiles(SRC)) {
      expect(readFileSync(file, 'utf8'), file).not.toMatch(/murray_darling_boundary_segment/i)
    }
  })

  it('las palabras tendencia, significancia, anomalía, p-value o pendiente solo aparecen para NEGARLAS, en archivos conocidos', () => {
    const forbidden = /p[- _]?value|significancia|anomal[ií]a|tendencia|pendiente/i
    // Archivo permitido -> frase de negación que debe acompañarlo en ese mismo archivo.
    const negations: Record<string, RegExp> = {
      'components/SyntheticBanner.tsx': /Nada de esta página es/,
      'components/RasterLegend.tsx': /Los colores no indican significancia/,
      'data/fixtures.ts': /Nada representa/,
    }
    const offenders = sourceFiles(SRC)
      .filter((file) => forbidden.test(readFileSync(file, 'utf8')))
      // En Windows las rutas usan \ ; se normalizan a / para compararlas con las claves de `negations`.
      .map((file) => file.slice(SRC.length + 1).replaceAll('\\', '/'))
    expect(offenders.sort()).toEqual(Object.keys(negations).sort())
    for (const [file, negation] of Object.entries(negations)) {
      expect(readFileSync(join(SRC, file), 'utf8'), file).toMatch(negation)
    }
  })

  it('ninguna URL externa de teselas o de descarga NASA aparece en el código', () => {
    for (const file of sourceFiles(SRC)) {
      const text = readFileSync(file, 'utf8')
      expect(text, file).not.toMatch(/https?:\/\/[^\s'"`]*(\.nc4?|\.hdf5?|earthdata|gesdisc|tile\.openstreetmap|mapbox\.com)/i)
    }
  })
})

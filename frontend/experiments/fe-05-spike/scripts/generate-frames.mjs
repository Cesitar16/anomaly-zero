// Genera los frames SINTÉTICOS del spike FE-05 (FUL-121). Sin dependencias: solo Node.
//
//   npm run frames
//
// Qué produce (public/frames/):
//   native/2005-01.png ... 2005-03.png    rejilla discreta en EPSG:4326, 0,1° por celda, filas lineales en latitud
//   mercator/2005-01.png ... 2005-03.png  la MISMA rejilla remuestreada (vecino más cercano) a filas lineales en Web Mercator
//   (src/data/frames.manifest.json)       bbox, CRS, resolución, escala, nodata y meses (uno ausente a propósito)
//
// IMPORTANTE: los valores NO son precipitación, NO son IMERG ni ninguna observación. Son diagonales
// artificiales a propósito, para que nadie las confunda con un campo físico. El script es determinista:
// sin aleatoriedad ni fechas, así que repetirlo produce los mismos bytes.

import { mkdirSync, writeFileSync } from 'node:fs'
import { deflateSync } from 'node:zlib'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const OUT = join(ROOT, 'public', 'frames')
const MANIFEST = join(ROOT, 'src', 'data', 'frames.manifest.json')

// --- Geometría de prueba (mismo recuadro que la vista exploratoria, pero SIN significado científico) ---
const BBOX = { west: 138, south: -38, east: 153, north: -24 }
const RES = 0.1
const W = Math.round((BBOX.east - BBOX.west) / RES) // 150
const H = Math.round((BBOX.north - BBOX.south) / RES) // 140

// Escala fija de 6 clases (viridis, apta para daltonismo). Igual en todos los meses.
const CLASS_COLORS = ['#440154', '#414487', '#2a788e', '#22a884', '#7ad151', '#fde725']
const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16))

// Marcas de referencia (no son valores: quedan fuera de la escala y de la leyenda de datos).
const MARK_WHITE = [255, 255, 255, 255]
const MARK_BLACK = [0, 0, 0, 255]
const NODATA = [0, 0, 0, 0] // alpha 0: transparente

// Valor sintético en [0, 1): diagonales que se desplazan con el mes.
function syntheticValue(lon, lat, monthIndex) {
  const v = 0.35 * (lon - BBOX.west) + 0.5 * (lat - BBOX.south) + 0.17 * (monthIndex - 1)
  return v - Math.floor(v)
}

function nativePixel(r, c, monthIndex) {
  // Marcas de referencia para verificar orientación y georreferenciación.
  if (r < 8 && c < 8) return MARK_WHITE // esquina noroeste
  if (r >= H - 8 && c >= W - 8) return MARK_BLACK // esquina sureste
  for (const tickRow of [20, 60, 100]) {
    // Borde superior de la fila = -26, -30 y -34 grados.
    if (r === tickRow && c >= 10 && c < 22) return MARK_WHITE
  }
  // Sin dato: un hueco rectangular y tres celdas aisladas.
  if (r >= 70 && r < 90 && c >= 80 && c < 100) return NODATA
  if ((r === 30 && c === 40) || (r === 31 && c === 41) || (r === 120 && c === 20)) return NODATA

  const lon = BBOX.west + (c + 0.5) * RES
  const lat = BBOX.north - (r + 0.5) * RES
  const v = syntheticValue(lon, lat, monthIndex)
  const klass = Math.min(5, Math.floor(v * 6))
  return [...hex(CLASS_COLORS[klass]), 255]
}

// --- Web Mercator ---
const rad = (deg) => (deg * Math.PI) / 180
const mercY = (latDeg) => Math.log(Math.tan(Math.PI / 4 + rad(latDeg) / 2))
const invMercY = (y) => ((2 * Math.atan(Math.exp(y)) - Math.PI / 2) * 180) / Math.PI

const yNorth = mercY(BBOX.north)
const ySouth = mercY(BBOX.south)
const midLat = (BBOX.north + BBOX.south) / 2
// Filas de Mercator con altura de celda comparable a la nativa en la latitud central.
const H_MERC = Math.round((yNorth - ySouth) / (rad(RES) / Math.cos(rad(midLat))))

function mercatorFromNative(native) {
  const out = new Uint8Array(W * H_MERC * 4)
  for (let rr = 0; rr < H_MERC; rr++) {
    const y = yNorth - ((rr + 0.5) * (yNorth - ySouth)) / H_MERC
    const lat = invMercY(y)
    const r = Math.min(H - 1, Math.max(0, Math.floor((BBOX.north - lat) / RES)))
    out.set(native.subarray(r * W * 4, (r + 1) * W * 4), rr * W * 4)
  }
  return out
}

// --- Codificador PNG mínimo (RGBA 8 bits, sin entrelazado) ---
const CRC_TABLE = Array.from({ length: 256 }, (_, n) => {
  let c = n
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1
  return c >>> 0
})
function crc32(buf) {
  let c = 0xffffffff
  for (const b of buf) c = CRC_TABLE[(c ^ b) & 0xff] ^ (c >>> 8)
  return (c ^ 0xffffffff) >>> 0
}
function chunk(type, data) {
  const len = Buffer.alloc(4)
  len.writeUInt32BE(data.length)
  const body = Buffer.concat([Buffer.from(type, 'ascii'), data])
  const crc = Buffer.alloc(4)
  crc.writeUInt32BE(crc32(body))
  return Buffer.concat([len, body, crc])
}
function encodePng(width, height, rgba) {
  const header = Buffer.alloc(13)
  header.writeUInt32BE(width, 0)
  header.writeUInt32BE(height, 4)
  header[8] = 8 // profundidad
  header[9] = 6 // RGBA
  const stride = width * 4
  const raw = Buffer.alloc((stride + 1) * height)
  for (let y = 0; y < height; y++) {
    raw[y * (stride + 1)] = 0 // filtro: ninguno
    Buffer.from(rgba.buffer, rgba.byteOffset + y * stride, stride).copy(raw, y * (stride + 1) + 1)
  }
  return Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    chunk('IHDR', header),
    chunk('IDAT', deflateSync(raw, { level: 9 })),
    chunk('IEND', Buffer.alloc(0)),
  ])
}

// --- Salida ---
mkdirSync(join(OUT, 'native'), { recursive: true })
mkdirSync(join(OUT, 'mercator'), { recursive: true })

const FRAME_MONTHS = ['2005-01', '2005-02', '2005-03']
for (const [i, month] of FRAME_MONTHS.entries()) {
  const native = new Uint8Array(W * H * 4)
  for (let r = 0; r < H; r++) {
    for (let c = 0; c < W; c++) native.set(nativePixel(r, c, i + 1), (r * W + c) * 4)
  }
  writeFileSync(join(OUT, 'native', `${month}.png`), encodePng(W, H, native))
  writeFileSync(join(OUT, 'mercator', `${month}.png`), encodePng(W, H_MERC, mercatorFromNative(native)))
}

const ALL_MONTHS = Array.from({ length: 12 }, (_, i) => `2005-${String(i + 1).padStart(2, '0')}`)
const months = ALL_MONTHS.map((date) => {
  if (FRAME_MONTHS.includes(date)) return { date, frame: `${date}.png`, reason: null }
  if (date === '2005-04') return { date, frame: null, reason: 'intentional_absent_synthetic' }
  return { date, frame: null, reason: 'no_frame_provided' }
})

const manifest = {
  synthetic: true,
  label: 'Frames sintéticos de prueba. No son IMERG, ni precipitación, ni ninguna observación.',
  generator: 'scripts/generate-frames.mjs',
  crs: 'EPSG:4326',
  bbox: BBOX,
  resolution_deg: RES,
  variants: {
    native: {
      width: W,
      height: H,
      description: 'Rejilla discreta de 0,1° con filas lineales en latitud (EPSG:4326 sin remuestrear).',
    },
    mercator: {
      width: W,
      height: H_MERC,
      description: 'La misma rejilla remuestreada por vecino más cercano a filas lineales en Web Mercator.',
    },
  },
  scale: {
    unit: 'u.a. sintéticas',
    min: 0,
    max: 1,
    classes: CLASS_COLORS.map((color, i) => ({ color, from: i / 6, to: (i + 1) / 6 })),
    fixed_across_months: true,
  },
  nodata: { representation: 'alpha=0' },
  months,
}
writeFileSync(MANIFEST, `${JSON.stringify(manifest, null, 2)}\n`)
console.log(`OK: ${FRAME_MONTHS.length} frames x 2 variantes (nativa ${W}x${H}, Mercator ${W}x${H_MERC}) en ${OUT}`)

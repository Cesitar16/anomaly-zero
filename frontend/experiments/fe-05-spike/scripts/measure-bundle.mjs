// Mide el costo en bundle de cada librería del spike, construyendo CADA una por separado.
//
//   npm run measure
//
// Cada entrada de measure/ se empaqueta sola con Vite (producción, minificada). Se suman los .js y
// .css emitidos (incluido el worker de MapLibre, que se carga aparte) y se reporta el tamaño sin
// comprimir y con gzip nivel 9. "Costo de la librería" = entrada menos la línea base (React + react-dom)
// SOLO en las entradas que incluyen React; las que no lo incluyen (maplibre-gl y echarts completo sin
// React) se informan tal cual, para no restar algo que no contienen.
// Es una MEDICIÓN DE SPIKE sobre estas versiones exactas, no un presupuesto de rendimiento aprobado.

import react from '@vitejs/plugin-react'
import { mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { gzipSync } from 'node:zlib'
import { build } from 'vite'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const OUT = join(ROOT, 'measure-out')
// [archivo, etiqueta, ¿incluye React?]
const ENTRIES = [
  ['baseline', 'React 19 + react-dom (línea base)', true],
  ['maplibre', 'maplibre-gl solo, sin React (+ CSS + worker)', false],
  ['react-map-gl', 'react-map-gl/maplibre + maplibre-gl, con React (+ CSS + worker)', true],
  ['echarts-modular', 'echarts modular (LineChart, ejes, tooltip, dataZoom, markLine/markArea, aria, canvas), con React', true],
  ['echarts-full', "echarts completo (import * from 'echarts'), sin React", false],
  ['recharts', 'recharts (LineChart + Tooltip + Brush + ReferenceArea/Line), con React', true],
]

rmSync(OUT, { recursive: true, force: true })
mkdirSync(OUT, { recursive: true })

const kb = (bytes) => Math.round((bytes / 1024) * 10) / 10
const results = []

for (const [name, label, withReact] of ENTRIES) {
  const html = join(OUT, `${name}.html`)
  writeFileSync(
    html,
    `<!doctype html><html><head><meta charset="utf-8"></head><body><div id="root"></div><script type="module" src="/measure/${name}.tsx"></script></body></html>`,
  )
  const outDir = join(OUT, `dist-${name}`)
  await build({
    root: ROOT,
    configFile: false,
    logLevel: 'error',
    plugins: [react()],
    build: { outDir, emptyOutDir: true, rollupOptions: { input: html }, chunkSizeWarningLimit: 100000 },
  })
  let raw = 0
  let gzip = 0
  const files = []
  const assets = join(outDir, 'assets')
  for (const file of readdirSync(assets)) {
    if (!/\.(js|css)$/.test(file)) continue
    const buffer = readFileSync(join(assets, file))
    raw += buffer.length
    gzip += gzipSync(buffer, { level: 9 }).length
    files.push(`${file.replace(/-[\w-]{8}(\.\w+)$/, '$1')} ${kb(buffer.length)} kB`)
  }
  results.push({ name, label, withReact, raw, gzip, files })
}

const base = results.find((r) => r.name === 'baseline')
const cost = (r) => ({ raw: r.raw - (r.withReact ? base.raw : 0), gzip: r.gzip - (r.withReact ? base.gzip : 0) })
const lines = [
  '| Entrada | Total sin comprimir (kB) | Total gzip (kB) | Costo de la librería sin comprimir (kB) | Costo de la librería gzip (kB) |',
  '| --- | ---: | ---: | ---: | ---: |',
  ...results.map((r) => {
    const c = cost(r)
    return `| ${r.label} | ${kb(r.raw)} | ${kb(r.gzip)} | ${r.name === 'baseline' ? '-' : kb(c.raw)} | ${r.name === 'baseline' ? '-' : kb(c.gzip)} |`
  }),
]
writeFileSync(join(OUT, 'results.json'), JSON.stringify(results, null, 2))
writeFileSync(join(OUT, 'results.md'), `${lines.join('\n')}\n`)
console.log(lines.join('\n'))
console.log('\nArchivos por entrada:')
for (const r of results) console.log(`- ${r.name}: ${r.files.join(' · ')}`)

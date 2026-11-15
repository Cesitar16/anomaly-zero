import { FRAME_MANIFEST } from '../data/frames'
import { RASTER_LAYERS } from '../data/fixtures'
import { resolveFrameTarget } from '../lib/frameTarget'
import type { ImageVariant, MapMode, RasterLayer } from '../types'

const resolve = (month: string, mode: MapMode, variant: ImageVariant = 'mercator', layers: RasterLayer[] = RASTER_LAYERS) =>
  resolveFrameTarget({ month, mode, variant, manifest: FRAME_MANIFEST, rasterLayers: layers, basePath: '/' })

describe('resolveFrameTarget', () => {
  it('modo contrato: state unavailable NO produce capa ni URL, en ninguno de los 12 meses', () => {
    for (const layer of RASTER_LAYERS) {
      const target = resolve(layer.date, 'contract')
      expect(target.kind).toBe('missing')
      expect(JSON.stringify(target)).not.toMatch(/https?:|frames\//)
    }
  })

  it('modo contrato: un tile_template real tampoco se consume dentro del spike', () => {
    const available: RasterLayer[] = [{ ...RASTER_LAYERS[0], state: 'available', format: 'png', tile_template: 'https://ejemplo.invalid/{z}/{x}/{y}.png' }]
    const target = resolve('2005-01', 'contract', 'mercator', available)
    expect(target).toMatchObject({ kind: 'missing', reason: 'tile_template_not_supported_in_spike' })
  })

  it('modo contrato: un mes sin descriptor se declara ausente', () => {
    expect(resolve('2005-01', 'contract', 'mercator', [])).toMatchObject({ kind: 'missing', reason: 'no_raster_layer_descriptor' })
  })

  it('prototipo: los meses con frame apuntan al archivo de su propio mes y variante', () => {
    expect(resolve('2005-02', 'prototype-frames', 'mercator')).toEqual({ kind: 'frame', url: '/frames/mercator/2005-02.png' })
    expect(resolve('2005-03', 'prototype-frames', 'native')).toEqual({ kind: 'frame', url: '/frames/native/2005-03.png' })
  })

  it('prototipo: el mes ausente a propósito no reutiliza el frame de otro mes', () => {
    const target = resolve('2005-04', 'prototype-frames')
    expect(target).toMatchObject({ kind: 'missing', reason: 'intentional_absent_synthetic' })
  })

  it('prototipo: los meses sin frame se declaran ausentes', () => {
    for (const month of ['2005-05', '2005-08', '2005-12']) {
      expect(resolve(month, 'prototype-frames')).toMatchObject({ kind: 'missing', reason: 'no_frame_provided' })
    }
  })
})

import { FRAME_MANIFEST } from '../data/frames'
import { imageCoordinates, latitudeFromMercatorY, maxLatitudeStretchError, mercatorY } from '../lib/geo'

describe('geo', () => {
  it('ordena las esquinas como MapLibre: noroeste, noreste, sureste, suroeste', () => {
    const [nw, ne, se, sw] = imageCoordinates(FRAME_MANIFEST.bbox)
    expect(nw).toEqual([138, -24])
    expect(ne).toEqual([153, -24])
    expect(se).toEqual([153, -38])
    expect(sw).toEqual([138, -38])
  })

  it('Mercator es invertible', () => {
    expect(latitudeFromMercatorY(mercatorY(-31.2))).toBeCloseTo(-31.2, 9)
  })

  it('estirar una rejilla EPSG:4326 por su bbox desplaza filas más de 2 celdas de 0,1° (hallazgo del spike)', () => {
    const error = maxLatitudeStretchError(FRAME_MANIFEST.bbox)
    expect(error).toBeGreaterThan(0.25)
    expect(error).toBeLessThan(0.27)
    expect(error / FRAME_MANIFEST.resolution_deg).toBeGreaterThan(2)
  })

  it('un bbox sin extensión en latitud no tiene error', () => {
    expect(maxLatitudeStretchError({ west: 0, east: 1, north: -30, south: -30 })).toBeCloseTo(0, 12)
  })
})

import type { Bbox } from '../types'

const rad = (deg: number) => (deg * Math.PI) / 180
const deg = (radians: number) => (radians * 180) / Math.PI

export function mercatorY(latitude: number): number {
  return Math.log(Math.tan(Math.PI / 4 + rad(latitude) / 2))
}

export function latitudeFromMercatorY(y: number): number {
  return deg(2 * Math.atan(Math.exp(y)) - Math.PI / 2)
}

/** Esquinas en el orden que exige MapLibre para un ImageSource: NO, NE, SE, SO (sentido horario). */
export function imageCoordinates(bbox: Bbox): [[number, number], [number, number], [number, number], [number, number]] {
  return [
    [bbox.west, bbox.north],
    [bbox.east, bbox.north],
    [bbox.east, bbox.south],
    [bbox.west, bbox.south],
  ]
}

/**
 * Error máximo de latitud (en grados) al estirar una imagen con filas LINEALES EN LATITUD (EPSG:4326)
 * entre las cuatro esquinas de su bbox en Web Mercator. MapLibre interpola la imagen de forma lineal en
 * el espacio Mercator, así que las filas interiores quedan desplazadas respecto de su latitud real.
 * Es un cálculo analítico: no depende de MapLibre ni de ninguna imagen.
 */
export function maxLatitudeStretchError(bbox: Bbox, samples = 2000): number {
  const yNorth = mercatorY(bbox.north)
  const ySouth = mercatorY(bbox.south)
  let worst = 0
  for (let i = 0; i <= samples; i++) {
    const fraction = i / samples
    const linearLat = bbox.north + fraction * (bbox.south - bbox.north)
    const displayedLat = latitudeFromMercatorY(yNorth + fraction * (ySouth - yNorth))
    worst = Math.max(worst, Math.abs(displayedLat - linearLat))
  }
  return worst
}

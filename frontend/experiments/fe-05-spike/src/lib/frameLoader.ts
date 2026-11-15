/** Descarga y decodifica un frame. Devuelve un ImageBitmap para entregarlo a `ImageSource.updateImage({ image })`. */
export async function loadFrameBitmap(url: string, signal: AbortSignal): Promise<ImageBitmap> {
  const response = await fetch(url, { signal })
  if (!response.ok) {
    throw new Error(`No se pudo cargar el frame (${response.status}).`)
  }
  const blob = await response.blob()
  // premultiplyAlpha 'none' conserva el alpha 0 del nodata sin teñir los bordes.
  return createImageBitmap(blob, { premultiplyAlpha: 'none' })
}

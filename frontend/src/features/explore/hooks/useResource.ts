import { useEffect, useRef, useState } from 'react'
import type { ApiResult, Remote } from '../types/contracts'

interface Settled<T> {
  key: string
  nonce: number
  result: ApiResult<T>
}

/**
 * Carga un recurso y lo expone como `Remote<T>` (idle, loading, success, error).
 *
 * - `key === null` significa "no hay nada que pedir" (`idle`).
 * - Cuando `key` o `nonce` cambian, la petición anterior se cancela y su respuesta se ignora, así que una
 *   respuesta lenta nunca pisa a una más nueva.
 * - El estado `loading` se DERIVA de que la última respuesta no corresponde a la clave actual; no se escribe
 *   dentro del efecto.
 */
export function useResource<T>(
  key: string | null,
  load: (signal: AbortSignal) => Promise<ApiResult<T>>,
  nonce = 0,
): Remote<T> {
  const [settled, setSettled] = useState<Settled<T> | null>(null)
  const loadRef = useRef(load)

  useEffect(() => {
    loadRef.current = load
  })

  useEffect(() => {
    if (key === null) return
    const controller = new AbortController()
    void loadRef.current(controller.signal).then((result) => {
      if (!controller.signal.aborted) setSettled({ key, nonce, result })
    })
    return () => controller.abort()
  }, [key, nonce])

  if (key === null) return { status: 'idle' }
  if (settled && settled.key === key && settled.nonce === nonce) {
    return settled.result.ok
      ? { status: 'success', data: settled.result.data }
      : { status: 'error', failure: settled.result.failure }
  }
  return { status: 'loading' }
}

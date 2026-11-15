import { act, renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { useResource } from '../../features/explore/hooks/useResource'
import type { ApiResult } from '../../features/explore/types/contracts'

function deferred<T>() {
  let resolve!: (value: ApiResult<T>) => void
  const promise = new Promise<ApiResult<T>>((done) => {
    resolve = done
  })
  return { promise, resolve }
}

describe('useResource', () => {
  it('sin clave está en reposo y no pide nada', () => {
    let calls = 0
    const { result } = renderHook(() =>
      useResource<string>(null, () => {
        calls += 1
        return Promise.resolve({ ok: true, data: 'x' })
      }),
    )
    expect(result.current).toEqual({ status: 'idle' })
    expect(calls).toBe(0)
  })

  it('pasa de loading a success y a error según la respuesta', async () => {
    const { result } = renderHook(() => useResource<string>('a', () => Promise.resolve({ ok: true, data: 'hola' })))
    expect(result.current.status).toBe('loading')
    await waitFor(() => expect(result.current).toEqual({ status: 'success', data: 'hola' }))

    const failing = renderHook(() =>
      useResource<string>('a', () => Promise.resolve({ ok: false, failure: { kind: 'network' } })),
    )
    await waitFor(() => expect(failing.result.current.status).toBe('error'))
  })

  it('una respuesta lenta de una consulta anterior no pisa a la más nueva', async () => {
    const slow = deferred<string>()
    const fast = deferred<string>()
    const { result, rerender } = renderHook(
      ({ key }) => useResource<string>(key, () => (key === 'vieja' ? slow.promise : fast.promise)),
      { initialProps: { key: 'vieja' } },
    )
    rerender({ key: 'nueva' })
    await act(async () => fast.resolve({ ok: true, data: 'nueva' }))
    await waitFor(() => expect(result.current).toEqual({ status: 'success', data: 'nueva' }))
    await act(async () => slow.resolve({ ok: true, data: 'vieja' }))
    expect(result.current).toEqual({ status: 'success', data: 'nueva' })
  })

  it('al cambiar la clave vuelve a loading (nunca muestra el dato de la clave anterior)', async () => {
    const { result, rerender } = renderHook(
      ({ key }) => useResource<string>(key, () => Promise.resolve({ ok: true, data: key })),
      { initialProps: { key: 'a' } },
    )
    await waitFor(() => expect(result.current.status).toBe('success'))
    rerender({ key: 'b' })
    expect(result.current.status).toBe('loading')
    await waitFor(() => expect(result.current).toEqual({ status: 'success', data: 'b' }))
  })
})

import '@testing-library/jest-dom/vitest'
import { afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'

// jsdom no implementa scroll; lo reemplazamos por espías.
window.scrollTo = vi.fn() as unknown as typeof window.scrollTo
Element.prototype.scrollIntoView = vi.fn()
// axe-core consulta canvas para detectar iconos; jsdom no lo implementa y solo genera ruido.
HTMLCanvasElement.prototype.getContext = vi.fn(
  () => null,
) as unknown as typeof HTMLCanvasElement.prototype.getContext

// jsdom no implementa ResizeObserver y Recharts (ResponsiveContainer) lo necesita.
globalThis.ResizeObserver = class {
  observe() {}
  unobserve() {}
  disconnect() {}
}

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

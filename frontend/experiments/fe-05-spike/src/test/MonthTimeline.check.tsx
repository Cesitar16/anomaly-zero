// Este archivo no exporta componentes: es una prueba. oxlint solo exime de esta regla a los nombres *.test.*,
// y estos se llaman *.check.* (ver vite.config.ts).
/* oxlint-disable react/only-export-components */
import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { MonthTimeline } from '../components/MonthTimeline'
import type { TimelineMonth } from '../components/MonthTimeline'

const MONTHS: TimelineMonth[] = [
  { month: '2005-01', hasFrame: true },
  { month: '2005-02', hasFrame: true },
  { month: '2005-03', hasFrame: false },
  { month: '2005-04', hasFrame: true },
]

function Harness({ months = MONTHS, start = '2005-01', playIntervalMs = 1000 }: { months?: TimelineMonth[]; start?: string; playIntervalMs?: number }) {
  const [month, setMonth] = useState(start)
  const [playing, setPlaying] = useState(false)
  return <MonthTimeline months={months} selectedMonth={month} onSelectMonth={setMonth} isPlaying={playing} onPlayingChange={setPlaying} playIntervalMs={playIntervalMs} />
}

describe('MonthTimeline', () => {
  it('Anterior está deshabilitado en el primer mes y Siguiente en el último', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    expect(screen.getByRole('button', { name: 'Anterior' })).toBeDisabled()
    await user.click(screen.getByRole('button', { name: 'Siguiente' }))
    await user.click(screen.getByRole('button', { name: 'Siguiente' }))
    await user.click(screen.getByRole('button', { name: 'Siguiente' }))
    expect(screen.getByTestId('selected-month')).toHaveTextContent('2005-04')
    expect(screen.getByRole('button', { name: 'Siguiente' })).toBeDisabled()
  })

  it('el slider anuncia el mes y si tiene capa; un mes sin capa conserva su fecha', async () => {
    const user = userEvent.setup()
    render(<Harness start="2005-02" />)
    const slider = screen.getByRole('slider', { name: 'Mes (YYYY-MM)' })
    expect(slider).toHaveAttribute('aria-valuetext', '2005-02, con capa')
    await user.click(screen.getByRole('button', { name: 'Siguiente' }))
    expect(slider).toHaveAttribute('aria-valuetext', '2005-03, sin capa')
    expect(screen.getByTestId('selected-month')).toHaveTextContent('2005-03')
    expect(screen.getByTestId('selected-month')).toHaveTextContent('sin capa')
  })

  it('Reproducir avanza mes a mes SIN saltarse el mes sin capa y se detiene al final', () => {
    vi.useFakeTimers()
    try {
      render(<Harness playIntervalMs={1000} />)
      act(() => screen.getByRole('button', { name: 'Reproducir' }).click())
      const seen = [screen.getByTestId('selected-month').textContent]
      for (let step = 0; step < 3; step++) {
        act(() => {
          vi.advanceTimersByTime(1000)
        })
        seen.push(screen.getByTestId('selected-month').textContent)
      }
      expect(seen.map((text) => text?.slice(0, 7))).toEqual(['2005-01', '2005-02', '2005-03', '2005-04'])
      expect(seen[2]).toContain('sin capa')
      act(() => {
        vi.advanceTimersByTime(1000)
      })
      expect(screen.getByRole('button', { name: 'Reproducir' })).toHaveAttribute('aria-pressed', 'false')
      expect(screen.getByTestId('selected-month')).toHaveTextContent('2005-04') // sin bucle
    } finally {
      vi.useRealTimers()
    }
  })

  it('una acción manual pausa la reproducción', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    await user.click(screen.getByRole('button', { name: 'Reproducir' }))
    expect(screen.getByRole('button', { name: 'Pausar' })).toHaveAttribute('aria-pressed', 'true')
    await user.click(screen.getByRole('button', { name: 'Siguiente' }))
    expect(screen.getByRole('button', { name: 'Reproducir' })).toHaveAttribute('aria-pressed', 'false')
  })

  it('Reproducir se deshabilita con menos de 2 meses con capa (regla de FE-03)', () => {
    render(<Harness months={MONTHS.map((item, index) => ({ ...item, hasFrame: index === 0 }))} />)
    expect(screen.getByRole('button', { name: 'Reproducir' })).toBeDisabled()
    expect(screen.getByText(/al menos 2 meses con capa/)).toBeInTheDocument()
  })
})

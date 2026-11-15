import { useEffect } from 'react'
import { monthLabel } from '../lib/months'
import type { YearMonth } from '../types'

export interface TimelineMonth {
  month: YearMonth
  hasFrame: boolean
}

export interface MonthTimelineProps {
  months: TimelineMonth[]
  selectedMonth: YearMonth
  onSelectMonth: (month: YearMonth) => void
  isPlaying: boolean
  onPlayingChange: (playing: boolean) => void
  /** Pausa entre meses al reproducir. */
  playIntervalMs?: number
}

/**
 * Selector temporal CONTROLADO (`selectedMonth` vive en el padre).
 * - Anterior/Siguiente y slider cambian el mes de forma discreta, sin interpolar entre fechas.
 * - Play recorre TODOS los meses del rango y se detiene al final (no hace bucle). Un mes sin capa se
 *   muestra como "sin capa"; nunca se salta ni se reemplaza por el mes anterior.
 * - Play solo se habilita con al menos 2 meses que tengan capa (regla de FE-03).
 */
export function MonthTimeline({
  months,
  selectedMonth,
  onSelectMonth,
  isPlaying,
  onPlayingChange,
  playIntervalMs = 1200,
}: MonthTimelineProps) {
  const index = Math.max(0, months.findIndex((item) => item.month === selectedMonth))
  const current = months[index]
  const last = months.length - 1
  const framesAvailable = months.filter((item) => item.hasFrame).length
  const canPlay = framesAvailable >= 2

  // Un temporizador por paso: avanza un mes y el efecto se vuelve a armar con el nuevo índice.
  // Al llegar al último mes la reproducción termina sola (sin bucle).
  useEffect(() => {
    if (!isPlaying) return
    if (index >= last) {
      onPlayingChange(false)
      return
    }
    const timer = window.setTimeout(() => onSelectMonth(months[index + 1].month), playIntervalMs)
    return () => window.clearTimeout(timer)
  }, [isPlaying, index, last, months, onSelectMonth, onPlayingChange, playIntervalMs])

  function select(next: number) {
    onPlayingChange(false) // cualquier acción manual pausa la reproducción
    onSelectMonth(months[Math.min(last, Math.max(0, next))].month)
  }

  const stateText = current.hasFrame ? 'con capa' : 'sin capa'

  return (
    <section className="timeline" aria-labelledby="timeline-title">
      <h3 id="timeline-title">Mes seleccionado</h3>
      <div className="timeline__controls">
        <button type="button" className="button" onClick={() => select(index - 1)} disabled={index === 0}>
          Anterior
        </button>
        <output className="timeline__month" aria-live="polite" data-testid="selected-month">
          <span className="timeline__month-id">{current.month}</span>
          <span className="timeline__month-label">{monthLabel(current.month)}</span>
          <span className={`timeline__state timeline__state--${current.hasFrame ? 'frame' : 'none'}`}>{stateText}</span>
        </output>
        <button type="button" className="button" onClick={() => select(index + 1)} disabled={index === last}>
          Siguiente
        </button>
        <button
          type="button"
          className="button button--primary"
          aria-pressed={isPlaying}
          onClick={() => onPlayingChange(!isPlaying)}
          disabled={!canPlay}
          title={canPlay ? undefined : 'Se necesitan al menos 2 meses con capa para reproducir.'}
        >
          {isPlaying ? 'Pausar' : 'Reproducir'}
        </button>
      </div>
      <input
        type="range"
        className="timeline__slider"
        min={0}
        max={last}
        step={1}
        value={index}
        aria-label="Mes (YYYY-MM)"
        aria-valuetext={`${current.month}, ${stateText}`}
        onChange={(event) => select(Number(event.target.value))}
      />
      <p className="timeline__hint">
        {framesAvailable} de {months.length} meses con capa. Un mes sin capa se muestra como ausente: no se reutiliza otra fecha.
        {!canPlay && ' Reproducir está deshabilitado: hacen falta al menos 2 meses con capa.'}
      </p>
    </section>
  )
}

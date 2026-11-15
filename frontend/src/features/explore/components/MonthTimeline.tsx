import { useEffect } from 'react'
import { COPY } from '../content/exploreCopy'
import { monthLabel } from '../lib/months'
import type { YearMonth } from '../types/contracts'

export interface TimelineMonth {
  month: YearMonth
  hasLayer: boolean
}

export interface MonthTimelineProps {
  months: TimelineMonth[]
  selectedMonth: YearMonth
  onSelectMonth(month: YearMonth): void
  isPlaying: boolean
  onPlayingChange(playing: boolean): void
  playIntervalMs?: number
}

/**
 * Selector de mes CONTROLADO (el mes vive en la dirección). Cambia de mes de forma discreta, sin interpolar.
 * «Reproducir» recorre los meses y se detiene al final; solo se habilita con al menos 2 meses con capa.
 * Un mes sin capa se anuncia como «sin capa»: nunca se salta ni se reemplaza por otro mes.
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
  const withLayer = months.filter((item) => item.hasLayer).length
  const canPlay = withLayer >= 2

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
    onPlayingChange(false)
    onSelectMonth(months[Math.min(last, Math.max(0, next))].month)
  }

  const stateText = current.hasLayer ? 'con capa' : 'sin capa'

  return (
    <div className="explore-timeline">
      <div className="explore-timeline__controls">
        <button type="button" className="btn btn--secondary" onClick={() => select(index - 1)} disabled={index === 0}>
          Mes anterior
        </button>
        <output className="explore-timeline__month" aria-live="polite">
          <span className="explore-mono">{current.month}</span> {monthLabel(current.month)} · {stateText}
        </output>
        <button type="button" className="btn btn--secondary" onClick={() => select(index + 1)} disabled={index === last}>
          Mes siguiente
        </button>
        <button
          type="button"
          className="btn btn--primary"
          aria-pressed={isPlaying}
          disabled={!canPlay}
          aria-describedby={canPlay ? undefined : 'explore-timeline-hint'}
          onClick={() => onPlayingChange(!isPlaying)}
        >
          {isPlaying ? 'Pausar' : 'Reproducir'}
        </button>
      </div>
      <input
        type="range"
        className="explore-timeline__slider"
        min={0}
        max={last}
        step={1}
        value={index}
        aria-label="Mes (AAAA-MM)"
        aria-valuetext={`${current.month}, ${stateText}`}
        onChange={(event) => select(Number(event.target.value))}
      />
      <p id="explore-timeline-hint" className="explore-muted">
        {withLayer} de {months.length} meses con capa. {canPlay ? '' : COPY.map.timelineDisabled}
      </p>
    </div>
  )
}

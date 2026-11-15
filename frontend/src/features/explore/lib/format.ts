import { COPY } from '../content/exploreCopy'

/** Número con coma decimal (es-CL). Conserva el cero: 0 se escribe "0". */
export function formatValue(value: number): string {
  return value.toLocaleString('es-CL', { maximumFractionDigits: 3 })
}

/** Fecha y hora UTC legible. Un texto que no es una fecha se muestra tal cual, sin inventar. */
export function formatDateTime(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  const text = new Intl.DateTimeFormat('es-CL', {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone: 'UTC',
  }).format(date)
  return `${text} UTC`
}

/** `null`, `undefined` y cadena vacía se escriben «No informado». Nunca "null" ni "undefined". */
export function orNotInformed(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === '') return COPY.notInformed
  return String(value)
}

/** Texto para un atributo de esquema libre (`fill_value`, etc.). */
export function formatLooseValue(value: unknown): string {
  if (value === null || value === undefined) return COPY.notInformed
  if (typeof value === 'number') return formatValue(value)
  if (typeof value === 'string') return value === '' ? COPY.notInformed : value
  return JSON.stringify(value)
}

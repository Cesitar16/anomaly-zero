/**
 * Ilustración decorativa del hero: curvas de nivel y una línea ámbar de "anomalía cero".
 * No representa datos reales: se genera con una función matemática simple y está oculta
 * a los lectores de pantalla (aria-hidden).
 */
const CENTER = { x: 240, y: 220 }
const RING_RADII = [34, 66, 98, 130, 162, 194]
const POINTS_PER_RING = 96

function ringPath(radius: number, index: number): string {
  const wobble = radius * 0.09
  const phase = index * 0.9

  const points = Array.from({ length: POINTS_PER_RING }, (_, i) => {
    const angle = (i / POINTS_PER_RING) * Math.PI * 2
    const r =
      radius +
      wobble * Math.sin(3 * angle + phase) +
      wobble * 0.5 * Math.sin(5 * angle - phase * 1.7)
    return [CENTER.x + r * Math.cos(angle), CENTER.y + r * 0.88 * Math.sin(angle)]
  })

  return `M${points.map(([x, y]) => `${x.toFixed(1)} ${y.toFixed(1)}`).join('L')}Z`
}

const RINGS = RING_RADII.map((radius, index) => ({ index, d: ringPath(radius, index) }))

export default function HeroArt() {
  return (
    <svg
      className="hero__art"
      viewBox="0 0 480 440"
      aria-hidden="true"
      focusable="false"
      xmlns="http://www.w3.org/2000/svg"
    >
      {RINGS.map(({ index, d }) => (
        <path key={index} d={d} className={index < 2 ? 'contour contour--inner' : 'contour'} />
      ))}
      <line x1="16" y1={CENTER.y} x2="464" y2={CENTER.y} className="zero-line" />
      <circle cx={CENTER.x} cy={CENTER.y} r="7" className="zero-dot" />
    </svg>
  )
}

/** Marca: anillos concéntricos (curvas de nivel) y una línea ámbar de "anomalía cero". */
export default function Logo() {
  return (
    <span className="logo">
      <svg className="logo__mark" viewBox="0 0 64 64" aria-hidden="true" focusable="false">
        <rect width="64" height="64" rx="14" fill="#143843" />
        <circle cx="32" cy="32" r="19" fill="none" stroke="#4d8791" strokeWidth="2" />
        <circle cx="32" cy="32" r="11" fill="none" stroke="#4d8791" strokeWidth="2" />
        <line
          x1="8"
          y1="32"
          x2="56"
          y2="32"
          stroke="#f2a65a"
          strokeWidth="3"
          strokeDasharray="5 4"
          strokeLinecap="round"
        />
        <circle cx="32" cy="32" r="4.5" fill="#f2a65a" />
      </svg>
      <span className="logo__text">Anomaly Zero</span>
    </span>
  )
}

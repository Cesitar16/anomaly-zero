interface Step {
  title: string
  text: string
}

interface CandidateVariable {
  name: string
  detail: string
  product: string
}

interface HowItWorksContent {
  eyebrow: string
  title: string
  intro: string
  steps: Step[]
  variablesHeading: string
  variablesIntro: string
  variables: CandidateVariable[]
  scopeNote: string
}

export const HOW_IT_WORKS: HowItWorksContent = {
  eyebrow: 'Cómo funciona',
  title: 'Cuatro pasos, de la pregunta a la evidencia.',
  intro: 'Así está pensado el recorrido dentro del explorador cuando esté disponible.',
  steps: [
    {
      title: 'Elige',
      text: 'Escoge una variable ambiental, una región y un período.',
    },
    {
      title: 'Observa',
      text: 'Revisa la serie histórica, mensual o anual, con unidades y definición a la vista.',
    },
    {
      title: 'Estima',
      text: 'Mira cuánto cambia la variable por década y qué tan incierta es esa estimación.',
    },
    {
      title: 'Verifica',
      text: 'Consulta el método estadístico, la cobertura de datos y de dónde viene cada valor: producto, versión y productor.',
    },
  ],
  variablesHeading: 'Variables candidatas',
  variablesIntro:
    'Empezaríamos con tres variables mensuales. Cada una conserva su origen y su resolución; no mezclamos productos con definiciones distintas sin avisarlo.',
  variables: [
    {
      name: 'Temperatura del aire',
      detail: 'A 2 metros sobre la superficie',
      product: 'MERRA-2 (NASA GMAO)',
    },
    {
      name: 'Precipitación',
      detail: 'Acumulación mensual',
      product: 'GPM IMERG (NASA y JAXA)',
    },
    {
      name: 'Humedad del suelo',
      detail: 'Capa de 0 a 10 cm, modelada',
      product: 'GLDAS Noah (NASA GSFC)',
    },
  ],
  scopeNote:
    'Los productos, la región candidata (la cuenca Murray-Darling, en Australia) y el período (aproximadamente 2005 a 2025) aún no están aprobados. Son una propuesta de trabajo y pueden cambiar cuando el equipo revise la calidad de los datos.',
}

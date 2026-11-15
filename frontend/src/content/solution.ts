import type { BadgeStatus } from '../types'

interface Goal {
  title: string
  text: string
}

interface StatusItem {
  status: BadgeStatus
  statusLabel: string
  title: string
  text: string
}

interface SolutionContent {
  eyebrow: string
  title: string
  intro: string
  goals: Goal[]
  statusHeading: string
  statusIntro: string
  statusItems: StatusItem[]
}

export const SOLUTION: SolutionContent = {
  eyebrow: 'La propuesta',
  title: 'Una guía para pasar de la pregunta a la evidencia.',
  intro:
    'Anomaly Zero es el objetivo de un explorador público de tendencias ambientales. La idea es acompañar todo el recorrido, desde elegir qué mirar hasta entender qué respalda el resultado.',
  goals: [
    {
      title: 'Elegir',
      text: 'Seleccionar una variable, una región y un período de interés.',
    },
    {
      title: 'Observar',
      text: 'Ver cómo evoluciona esa variable en el tiempo, con sus unidades.',
    },
    {
      title: 'Estimar',
      text: 'Calcular la tasa de cambio, por ejemplo por década, con su intervalo de incertidumbre.',
    },
    {
      title: 'Evaluar',
      text: 'Mostrar la significancia, el método y la procedencia de los datos, sin confundir "significativo" con "importante".',
    },
  ],
  statusHeading: 'Qué existe hoy y qué no',
  statusIntro:
    'Para no generar falsas expectativas, separamos el objetivo del producto de lo que ya está disponible.',
  statusItems: [
    {
      status: 'available',
      statusLabel: 'Disponible',
      title: 'Esta presentación del proyecto',
      text: 'Explica el problema, la propuesta, el equipo y las fuentes.',
    },
    {
      status: 'in-progress',
      statusLabel: 'En desarrollo',
      title: 'Explorador de variables y tendencias',
      text: 'Selección de variable y región, series históricas, pendiente con intervalo y método.',
    },
    {
      status: 'planned',
      statusLabel: 'Planificado',
      title: 'Ampliaciones',
      text: 'Mapa mensual de la variable elegida y variables adicionales, como vegetación y humedad satelital.',
    },
  ],
}

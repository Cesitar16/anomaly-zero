interface ProblemPoint {
  title: string
  text: string
}

interface ChallengeNote {
  title: string
  text: string
  linkLabel: string
  href: string
}

interface ProblemContent {
  eyebrow: string
  title: string
  intro: string
  points: ProblemPoint[]
  challengeNote: ChallengeNote
}

export const PROBLEM: ProblemContent = {
  eyebrow: 'El problema',
  title: 'Hay muchos datos de la Tierra. Entenderlos es otra cosa.',
  intro:
    'Los satélites, los modelos y los reanálisis producen una cantidad enorme de productos sobre el planeta. Que estén disponibles no significa que sea fácil usarlos para responder una pregunta concreta.',
  points: [
    {
      title: 'Demasiados productos',
      text: 'Cada producto tiene su propia resolución, unidad, período y versión. Elegir uno exige leer documentación técnica antes de ver un solo gráfico.',
    },
    {
      title: 'Nombres parecidos, medidas distintas',
      text: 'La temperatura del aire y la temperatura de la superficie no son lo mismo. La humedad del suelo a 5 cm y a 10 cm tampoco. Confundirlas cambia la conclusión.',
    },
    {
      title: 'Subir o bajar no basta',
      text: 'Para hablar de tendencia hay que estimar cuánto cambia por década y si ese cambio se distingue de la variabilidad natural. No encontrar significancia no prueba que todo siga estable.',
    },
    {
      title: 'Las regiones no son homogéneas',
      text: 'Una misma variable puede subir en una región y bajar en otra, aunque el proceso que la mueve sea el mismo. Un promedio regional puede esconder esos contrastes. Por eso importa dónde se mira, además de qué se mira.',
    },
  ],
  challengeNote: {
    title: 'El desafío de la NASA',
    text: 'El reto Be an Earth System Trend Detective! del NASA Space Apps Challenge 2026 pide crear una herramienta que permita seleccionar variables de misiones o modelos de ciencias de la Tierra, visualizar cómo cambian en el tiempo y determinar qué cambia, dónde, cuánto y si ese cambio es significativo en el sentido científico.',
    linkLabel: 'Ver el desafío en NASA Space Apps',
    href: 'https://www.spaceappschallenge.org/2026/challenges/earth-system-trend-detective/',
  },
}

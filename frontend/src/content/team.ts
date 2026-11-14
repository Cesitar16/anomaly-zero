interface TeamMember {
  name: string
  role: string
  focus: string
}

interface ExternalLinkData {
  label: string
  href: string
}

interface TeamContent {
  eyebrow: string
  title: string
  intro: string
  members: TeamMember[]
  privacyNote: string
  teamPage: ExternalLinkData
  event: { text: string; link: ExternalLinkData }
}

/**
 * Equipo. Solo nombres y roles.
 * No agregar correos, redes, teléfonos ni fotografías sin permiso expreso
 * de cada persona (restricción de FE-01).
 *
 * Los roles siguen los "responsables funcionales" de la descripción del proyecto en Linear
 * (14-11-2026). La tarjeta pide roles consensuados: cada integrante debe confirmar el suyo
 * antes de publicar (ver docs/FE-01-evidencia.md).
 */
export const TEAM: TeamContent = {
  eyebrow: 'Equipo',
  title: 'Quiénes están detrás de Anomaly Zero.',
  intro: 'Un equipo de cuatro personas que participa en el NASA Space Apps Challenge 2026.',
  members: [
    {
      name: 'César Rojas',
      role: 'Data Science y estadística',
      focus: 'Exploración estadística, decisiones de método y coordinación técnico-científica.',
    },
    {
      name: 'Lucas Moncada',
      role: 'Datos NASA e investigación científica',
      focus: 'Catálogo de productos, cobertura, procedencia y verificación de los datos.',
    },
    {
      name: 'Alaín',
      role: 'Ingeniería de datos y API',
      focus: 'Extracción de muestras y el servicio FastAPI que entrega los datos a la interfaz.',
    },
    {
      name: 'Alejandra Reyes',
      role: 'Frontend y comunicación',
      focus: 'Esta presentación y el explorador que usará la gente.',
    },
  ],
  privacyNote: 'No publicamos fotografías ni datos de contacto personales.',
  teamPage: {
    label: 'Página del equipo en NASA Space Apps',
    href: 'https://www.spaceappschallenge.org/2026/find-a-team/anomaly-zero/',
  },
  // Dato tomado de la página del evento local. No incluir nombres ni correos de sus organizadores.
  event: {
    text: 'Participamos desde el evento local de Santiago, Chile, organizado por Caja La Araucana en alianza con American Space.',
    link: {
      label: 'Página del evento local',
      href: 'https://www.spaceappschallenge.org/2026/local-events/santiago-chile/',
    },
  },
}

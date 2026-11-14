interface SourceResource {
  name: string
  owner: string
  note: string
  href: string
}

interface SourceProduct {
  name: string
  owner: string
  doi: string
}

interface SourcesContent {
  eyebrow: string
  title: string
  intro: string
  resourcesHeading: string
  resources: SourceResource[]
  productsHeading: string
  productsIntro: string
  products: SourceProduct[]
  disclaimer: { title: string; text: string }
}

/**
 * Fuentes y atribuciones.
 * Todo lo que la landing dice sobre la NASA debe poder rastrearse a una de estas entradas.
 * Los DOI provienen del catálogo de datasets del equipo (hoja "Productos científicos").
 */
export const SOURCES: SourcesContent = {
  eyebrow: 'Fuentes y atribuciones',
  title: 'De dónde vendría cada dato.',
  intro:
    'Anomaly Zero consultará recursos de la NASA y de instituciones asociadas. Cuando haya resultados, cada uno indicará el producto, su versión y quién lo produce.',
  resourcesHeading: 'Desafío y plataformas de consulta',
  resources: [
    {
      name: 'NASA Space Apps Challenge 2026: Be an Earth System Trend Detective!',
      owner: 'NASA Space Apps Challenge',
      note: 'Desafío que da origen al proyecto.',
      href: 'https://www.spaceappschallenge.org/2026/challenges/earth-system-trend-detective/',
    },
    {
      name: 'NASA Giovanni',
      owner: 'NASA GES DISC',
      note: 'Plataforma de exploración de series de datos. Primera herramienta de consulta prevista.',
      href: 'https://giovanni.gsfc.nasa.gov/',
    },
    {
      name: 'NASA AppEEARS',
      owner: 'NASA LP DAAC',
      note: 'Consulta exploratoria para productos de vegetación y superficie. Aún no es una selección final.',
      href: 'https://appeears.earthdatacloud.nasa.gov/',
    },
  ],
  productsHeading: 'Productos candidatos',
  productsIntro: 'Propuestos para las tres variables iniciales, sujetos a revisión de calidad.',
  products: [
    {
      name: 'MERRA-2, diagnósticos mensuales de superficie',
      owner: 'NASA GMAO. Distribuye NASA GES DISC.',
      doi: '10.5067/AP1B0BA5PD2K',
    },
    {
      name: 'GPM IMERG Final, precipitación mensual',
      owner: 'Equipo NASA GPM, misión NASA y JAXA. Distribuye NASA GES DISC.',
      doi: '10.5067/GPM/IMERG/3B-MONTH/07',
    },
    {
      name: 'GLDAS Noah, 0,25 grados mensual',
      owner: 'NASA GSFC. Distribuye NASA GES DISC.',
      doi: '10.5067/SXAVCZFAQLNO',
    },
  ],
  disclaimer: {
    title: 'Aviso',
    text: 'Anomaly Zero es un proyecto independiente, creado por un equipo participante del NASA Space Apps Challenge 2026. No está desarrollado, patrocinado ni respaldado por la NASA ni por las demás instituciones mencionadas. Sus nombres se usan solo para identificar las fuentes de datos.',
  },
}

export const doiUrl = (doi: string): string => `https://doi.org/${doi}`

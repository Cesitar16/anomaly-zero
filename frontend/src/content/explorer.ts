interface ExplorerContent {
  /** Bloque de la home */
  access: { eyebrow: string; title: string; text: string; honesty: string }
}

export const EXPLORER: ExplorerContent = {
  access: {
    eyebrow: 'Acceso al explorador',
    title: 'El explorador ya se puede abrir, en versión de demostración.',
    text: 'Vive en esta misma aplicación, en la ruta /explore. Hoy funciona con datos sintéticos de prueba que sirven para revisar cada pantalla y cada estado: no son observaciones de la NASA.',
    honesty: 'No publicamos tendencias, valores p, mapas ni cifras reales hasta tener datos revisados.',
  },
}

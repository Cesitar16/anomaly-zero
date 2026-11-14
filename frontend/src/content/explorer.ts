interface ExplorerContent {
  /** Bloque de la home */
  access: { eyebrow: string; title: string; text: string; honesty: string }
  /** Página /explore */
  page: {
    title: string
    statusLabel: string
    lead: string
    whenReadyHeading: string
    whenReady: string[]
    emptyPanelLabel: string
    emptyPanelText: string
  }
}

export const EXPLORER: ExplorerContent = {
  access: {
    eyebrow: 'Acceso al explorador',
    title: 'El explorador todavía no está disponible.',
    text: 'Estamos construyéndolo. Cuando exista, vivirá en esta misma aplicación, en la ruta /explore. Mientras tanto, ese enlace lleva a una página que explica el estado del proyecto y no muestra datos.',
    honesty: 'No publicamos tendencias, valores p, mapas ni cifras hasta tener datos revisados.',
  },
  page: {
    title: 'Explorador de tendencias',
    statusLabel: 'En desarrollo',
    lead: 'Esta pantalla es un marcador de posición. El explorador aún no existe y por eso no hay ningún dato, gráfico ni mapa en ella.',
    whenReadyHeading: 'Qué podrás hacer cuando esté listo',
    whenReady: [
      'Elegir una variable, una región y un período.',
      'Ver la serie histórica con sus unidades y su definición.',
      'Consultar la pendiente de cambio con su intervalo, el método y la significancia.',
      'Revisar la procedencia de cada dato: producto, versión y productor.',
    ],
    emptyPanelLabel: 'Espacio reservado para el explorador',
    emptyPanelText: 'Aquí aparecerán las series y tendencias cuando existan datos revisados.',
  },
}

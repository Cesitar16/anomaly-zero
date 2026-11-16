/**
 * Catálogo de texto literal de `/explore` (español de Chile, tuteo).
 * Fuente: docs/fe-03-explorer-ux.md, sección 8. Los textos son una PROPUESTA: los que afirman algo
 * científico (calidad, soporte espacial, análisis, "muestra NASA exploratoria") los revisa César
 * antes de darlos por cerrados (decisión D2 de FE-03). Ninguna cifra ni resultado vive aquí.
 */
import type { ErrorCode, PointQualityState, VerificationState } from '../types/contracts'

export const COPY = {
  page: {
    title: 'Explorador de tendencias',
    badgeDemo: 'Demostración',
    leadMock:
      'Elige una región, una variable NASA y un rango de meses para ver la serie mensual con su fuente, su unidad y su calidad. Esta versión funciona con datos de demostración.',
    leadHttp:
      'Elige una región, una variable NASA y un rango de meses para ver la serie mensual con su fuente, su unidad y su calidad.',
    back: 'Volver al inicio',
  },
  source: {
    legend: 'Fuente de los datos',
    demo: 'Servicio simulado (demostración)',
    api: 'Servicio real (API)',
    demoNote: 'Todas las respuestas son sintéticas y se generan en este navegador.',
    apiNote:
      'Consulta la API de Anomaly Zero. Si no responde verás el error; nunca se cambia a datos simulados por su cuenta.',
  },
  mock: 'Datos sintéticos de demostración. Nada de esta pantalla es una observación NASA ni un resultado estadístico.',
  sample:
    'Muestra NASA exploratoria. Es el valor de un solo punto, no el promedio validado de la cuenca.',
  supportPoint:
    'Serie de un punto: cada valor es la muestra de una sola celda de la grilla. No es el promedio de la región.',
  supportLocked: 'Agregado regional: no disponible. Todavía no está aprobado.',
  rate: 'Tasa media mensual en mm/hr. No es el total acumulado del mes.',
  coverageNote: 'La cobertura cuenta meses; no mide el área de la región.',
  notInformed: 'No informado',
  noCoordinates: 'coordenadas no informadas',

  filters: {
    title: 'Filtros',
    hide: 'Ocultar filtros',
    show: 'Mostrar filtros',
    summary: 'Filtros elegidos',
    region: 'Región',
    product: 'Variable NASA',
    start: 'Desde',
    end: 'Hasta',
    submit: 'Ver serie',
    submitBusy: 'Cargando serie',
    choose: { region: 'Elige una región', product: 'Elige una variable' },
    loading: { regions: 'Cargando regiones', products: 'Cargando variables' },
    noRegions: 'Sin regiones publicadas',
    help: 'Rango inclusivo, de a meses, hasta 240 meses.',
    formatHelp: 'Formato AAAA-MM, por ejemplo 2005-01.',
    productsEmpty: 'Esta región todavía no tiene productos publicados.',
    productUnavailable:
      'Esta variable figura como no disponible. Puedes consultar el rango, pero lo más probable es que no devuelva datos.',
    coverage: (start: string, end: string) => `Cobertura publicada: ${start} a ${end}`,
    area: (km2: string) => `Área: ${km2} km²`,
    dirty: 'Cambiaste los filtros. Pulsa «Ver serie» para ver la serie nueva.',
    idle: 'Elige una variable y un rango de meses, y pulsa «Ver serie».',
    needRegion: 'Elige una región para empezar.',
    required: { region: 'Elige una región.', product: 'Elige una variable.' },
    invalidMonth: 'Mes no válido. Usa AAAA-MM.',
    startAfterEnd: '"Desde" no puede ser posterior a "Hasta".',
    tooLong: 'El rango supera 240 meses. Acórtalo.',
    unknownRegion: 'La región de la dirección no existe. Elige otra.',
    unknownProduct: 'La variable de la dirección no existe en esta región. Elige otra.',
  },

  availability: {
    available: 'Disponible',
    partial: 'Parcial',
    unavailable: 'No disponible',
  },

  state: {
    complete: 'Serie completa',
    gaps: 'Serie con huecos',
    noData: 'Sin datos',
    gapsText: (missing: number, total: number) =>
      `Hay datos, pero faltan ${missing} de ${total} meses. Los huecos se muestran como «sin dato», no como cero.`,
    noDataText:
      'No hay datos para el rango pedido. No es un error: la consulta fue válida y no devolvió meses.',
    gap: 'Sin dato',
    zero: '0 (cero válido)',
    noMonths: 'Sin meses para mostrar. No hay gráfico ni tabla para este rango.',
  },

  quality: {
    title: 'Calidad de los datos',
    unassessed:
      'Calidad no evaluada. No se aplicó ninguna verificación de calidad del proveedor.',
    basic:
      'Solo controles básicos de estructura y de valores no finitos o de relleno. No se aplicó la calidad del proveedor.',
    providerApplied: 'Se aplicó la calidad del proveedor.',
    checksEmpty:
      'No se reportan controles de calidad. Eso no significa que la calidad haya pasado.',
    point: {
      unassessed: 'Calidad no evaluada',
      missing: 'Sin dato',
      unknown: 'Calidad desconocida',
    } satisfies Record<PointQualityState, string>,
  },

  detail: {
    title: 'Detalle del mes',
    state: { value: 'Con valor', zero: 'Cero válido', missing: 'Sin dato' },
    explain: {
      value: 'Valor de la muestra de este mes.',
      zero: 'Hubo medición y el valor es cero. No es un dato faltante.',
      missing: 'No hay valor para este mes. Se muestra como hueco, no como cero.',
    },
    quality: 'Calidad del dato',
    reason: 'Motivo',
    support: 'Soporte',
    coordinates: 'Coordenadas',
    supportPoint: 'Muestra de un punto, no el promedio de la región',
    supportMean: 'Promedio descriptivo, sin aprobación',
    supportRegional: 'Agregado regional aprobado',
  },

  chart: {
    title: 'Serie mensual',
    note: 'Tasa media mensual en mm/hr. No es el total acumulado del mes.',
    tableCaption: 'Valores del gráfico, mes por mes. Los huecos no se rellenan.',
    selectedMonth: 'mes seleccionado',
  },

  map: {
    title: 'Mapa',
    unavailable: 'Sin capa geográfica disponible para este mes.',
    unavailableNote:
      'La API todavía no publica una capa de mapa para este producto. La serie y la tabla siguen siendo válidas.',
    monthMissing:
      'Este mes no tiene capa en la API. Los otros meses sí; el mapa no muestra la capa de otro mes en su lugar.',
    notDrawable:
      'La API declara una capa para este mes, pero esta versión del explorador todavía no sabe dibujarla: falta aprobar su formato, su licencia y su sistema de referencia.',
    layerDisabled: 'No disponible todavía',
    timelineDisabled: 'Reproducir necesita al menos 2 meses con capa disponible.',
    noLegend:
      'Sin capa no hay leyenda de color: no se dibuja una escala para algo que no se está mostrando.',
    demoLayer:
      'Capa sintética de demostración. Los colores y la forma no son observaciones NASA ni valores aprobados.',
    legendDemo:
      'La escala de colores es de demostración y no tiene valores numéricos aprobados.',
    legendNoData: 'Sin dato: celda transparente',
    unitNotInformed: 'Unidad no informada',
    loading: (month: string) => `Cargando capa de ${month}`,
    loadError: (month: string) => `No se pudo cargar la capa de ${month}.`,
    retry: 'Reintentar',
    layerTypes: {
      value: 'Valor',
      anomaly: 'Anomalía',
      slope: 'Tendencia (pendiente)',
      significance: 'Significancia',
    },
  },

  analysis: {
    title: 'Análisis de tendencia: no disponible',
    body: 'No hay un método estadístico aprobado y habilitado; no se creó un análisis. No se calculó ninguna pendiente, intervalo de confianza ni valor p.',
    point:
      'Una serie de un solo punto no equivale a una tendencia ni a un promedio de la región.',
    technical: 'Detalle técnico de la respuesta del servicio',
    notCreated: 'No se creó',
    noMethod: 'Ninguno habilitado',
    notComputed: { f: 'No calculada', m: 'No calculado' },
    disabledControl: 'Calcular tendencia',
    disabledReason: 'Deshabilitado: todavía no hay un método estadístico aprobado.',
  },

  empty: {
    regions: 'Todavía no hay regiones publicadas.',
    regionsNote:
      'El explorador mostrará mapa y series cuando exista al menos una región con datos revisados.',
  },

  provenance: {
    title: 'Fuente y procedencia',
    coverageTitle: 'Cobertura',
    sample: 'Muestra exploratoria',
    none: 'Sin procedencia: no hay un snapshot verificado detrás de esta respuesta.',
  },

  demo: {
    title: 'Escenarios de demostración',
    note: 'Solo existen con datos sintéticos. Cambian lo que responde el servicio simulado para revisar cada estado de la pantalla.',
    label: 'Escenario',
    options: {
      '': 'Predeterminado (serie con huecos y cero)',
      'catalogo-vacio': 'Sin regiones publicadas',
      'capas-mixtas': 'Mapa con capas mixtas (mes con capa y mes sin capa)',
      'capas-no-disponibles': 'Mapa con capas declaradas no disponibles',
      'no-encontrado': 'La serie responde 404',
      'error-503': 'La serie responde 503 (reintentable)',
      'error-500': 'La serie responde 500',
      'sin-red': 'La serie no responde',
    },
  },
} as const

export type DemoScenarioId = Exclude<keyof typeof COPY.demo.options, ''>

export const DEMO_SCENARIOS = Object.keys(COPY.demo.options).filter(
  (id): id is DemoScenarioId => id !== '',
)

export function verificationText(state: VerificationState): string {
  switch (state) {
    case 'unassessed':
      return COPY.quality.unassessed
    case 'basic_checks_only':
      return COPY.quality.basic
    case 'provider_qa_applied':
      return COPY.quality.providerApplied
  }
}

export interface ErrorCopy {
  title: string
  body: string
}

/** El `code` elige el texto; el mensaje del servicio queda como detalle secundario. */
export const ERROR_COPY: Record<ErrorCode | 'NETWORK', ErrorCopy> = {
  INVALID_PARAMETER: {
    title: 'Revisa los filtros',
    body: 'Alguno de los valores de los filtros no es válido. Corrígelo y vuelve a intentar.',
  },
  PERIOD_OUT_OF_COVERAGE: {
    title: 'El rango está fuera de la cobertura',
    body: 'El rango pedido no está dentro de los meses publicados. Ajusta «Desde» y «Hasta».',
  },
  LIMIT_EXCEEDED: {
    title: 'El rango es demasiado largo',
    body: 'El máximo es 240 meses por consulta. Acórtalo.',
  },
  RESOURCE_NOT_FOUND: {
    title: 'No encontramos lo que pediste',
    body: 'La región o el producto no existe. Elige otra opción en los filtros.',
  },
  SERVICE_UNAVAILABLE: {
    title: 'Los datos no están disponibles por ahora',
    body: 'El servicio tuvo un problema temporal. Esto no significa que no haya datos. Puedes reintentar.',
  },
  INTERNAL_ERROR: {
    title: 'Algo falló de nuestro lado',
    body: 'Ocurrió un error inesperado. No hay datos que mostrar en este momento.',
  },
  ANALYSIS_METHOD_UNAVAILABLE: {
    title: 'Análisis de tendencia: no disponible',
    body: 'No hay un método estadístico aprobado y habilitado; no se creó un análisis.',
  },
  INSUFFICIENT_DATA: {
    title: 'No hay datos suficientes',
    body: 'No hay suficientes observaciones para esta operación.',
  },
  NETWORK: {
    title: 'No pudimos conectar',
    body: 'No hubo respuesta del servicio. Revisa tu conexión y vuelve a intentar.',
  },
}

/** Texto de `INVALID_PARAMETER` cuando el servicio dice qué campo falló (`details.field`). */
export function invalidParameterBody(field: string | undefined): string {
  switch (field) {
    case 'start':
      return 'El campo «Desde» no tiene un mes válido. Usa el formato AAAA-MM, por ejemplo 2005-01.'
    case 'end':
      return 'El campo «Hasta» no tiene un mes válido. Usa el formato AAAA-MM, por ejemplo 2005-01.'
    case 'region_id':
      return 'El campo «Región» no tiene un valor válido.'
    case 'product_id':
      return 'El campo «Variable NASA» no tiene un valor válido.'
    default:
      return ERROR_COPY.INVALID_PARAMETER.body
  }
}

/** Etiquetas legibles de los productos conocidos. Para cualquier otro se usa el nombre del contrato. */
const PRODUCT_LABELS: Record<string, string> = {
  GPM_3IMERGM: 'Precipitación (IMERG Final)',
  M2TMNXSLV: 'Temperatura del aire a 2 m (MERRA-2)',
  GLDAS_NOAH025_M: 'Humedad del suelo, 0 a 10 cm (GLDAS)',
}

const QUANTITY_LABELS: Record<string, string> = {
  monthly_mean_rate: 'tasa media mensual',
  air_temperature_2m: 'temperatura del aire a 2 m',
  soil_moisture_layer_0_10_cm: 'humedad del suelo, capa de 0 a 10 cm',
}

export function productLabel(product: { short_name: string; variable: string }): string {
  return PRODUCT_LABELS[product.short_name] ?? `${product.variable} (${product.short_name})`
}

export function quantityLabel(quantity: string): string {
  return QUANTITY_LABELS[quantity] ?? quantity
}

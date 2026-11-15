# DS-05 — Feature Engineering y protocolo de modelado

**Estado:** diseño con un pipeline univariado inicial implementado; no contiene resultados multivariables NASA ni entrenamiento. **Decisión:** avanzar con la preparación y adquisición incremental; mantener bloqueado el modelado hasta contar con soporte común validado y años suficientes.

## Evaluación de features

| Familia | Estado | Fundamento y uso | Riesgo/condición |
|---|---|---|---|
| Mes cíclico (`sin`, `cos`) y estación austral | Implementado; probado con fixtures sintéticos | Codifica periodicidad suave; verano DJF, otoño MAM, invierno JJA, primavera SON | Describe calendario, no anomalías ni tendencia. No se ajusta con el target. |
| Rezagos 1, 3, 6, 12 meses | Implementado; probado | Persistencia hidrológica y dependencia temporal | Filas de t usan solo t−lag. Sin imputación; el calendario completo se reindexa para que una ausencia corte el rezago. |
| Media/desviación móvil trailing 3 y diferencia mensual | Implementado; probado | Persistencia y cambio reciente | Incluye t; usable tras cerrar el mes t para pronosticar t+1. `min_periods=3`; faltantes no se saltan ni cruzan silenciosamente. |
| Año calendario/tendencia | Propuesto, no implementado | Puede capturar cambios de régimen de producto/clima | Confunde tiempo con cambio de sensor/versión y extrapola tendencia; requiere más años y análisis de estabilidad. |
| Acumulación IMERG a profundidad mensual y ventanas 3/6/12 | Conversión opt-in implementada, acumulaciones posteriores propuestas | La tasa `mm/hr` se multiplica por horas reales del mes para obtener mm | Solo con interpretación de promedio sobre todo el intervalo confirmada por metadatos. No sumar tasas mensuales. Mantener la tasa original y guardar unidad/método. |
| Anomalía mensual, z-score/climatología | Bloqueada | Puede expresar desviación del ciclo climatológico | Doce meses de 2005 no estiman climatología. Exigir período de referencia explícito, meses representados y evaluación fuera de período; no ajustar normalización usando futuro del fold. |
| Persistencia seca/húmeda, umbrales/extremos | Bloqueada | Potencialmente útil para alertas | Necesita variable objetivo y umbral con base física/impacto local validada; no inventar percentiles con un año ni inferir sequía desde un solo producto modelado. |
| Interacciones `P×T`, `P×SM` | Propuestas, bloqueadas | Pueden representar respuesta hidrológica no aditiva | Requieren panel co-localizado y considerar dependencia de GLDAS de forzantes meteorológicos; no interpretar coeficientes causalmente. |
| Latitud/longitud, grilla, resolución, máscara, cobertura | Solo metadatos de soporte; predictores bloqueados | Sirven para estratificar y auditar disponibilidad | Un identificador/celda es metadato, no transformación a promedio regional. Gate R, máscara y bounds siguen pendientes. No hay topografía con fuente/licencia/linaje verificados incorporada. |

### Implementación

`research.ful122_features.build_monthly_features` recibe una serie de una variable, un producto y un `support_id`; comprueba unidad, elegibilidad, procedencia/hash de granule NASA o etiqueta explícita de fixture sintético, unicidad mensual y soporte constante. Devuelve una tabla con calendario, rezagos y estadísticas trailing, más metadatos de período ausente, unidad, soporte, QA y disponibilidad/bloqueo de familias. No hace joins de productos, relleno, escalado, target engineering ni agregación regional.

`monthly_rate_to_depth` exige `unit="mm/hr"` y confirmación explícita de la interpretación temporal; usa el número real de horas del mes (incluidos años bisiestos) y devuelve mm sin alterar la tasa de entrada. No se aplicó a observaciones NASA en esta tarjeta, dado que primero debe confirmarse el significado operacional del campo para el intervalo completo en los metadatos del producto.

Las pruebas de estas transformaciones usan valores inventados con `source_kind=synthetic_fixture` y bandera obligatoria. Son pruebas de software, no hallazgos NASA. El pipeline rechaza features de fuentes declaradas inelegibles.

## Leakage y validación

El constructor no conoce un target y no calcula una fila futura. Los lags se desplazan desde el pasado y las ventanas son trailing e incluyen el valor de cierre t; una predicción para t+1 usa fila t. Reindexar a meses calendario antes de desplazar impide que “mes anterior observado” oculte huecos. Se reportan períodos ausentes; no se imputa.

Para el experimento posterior: generar la tabla de filas elegibles y alinear productos **antes** de fold solo por claves de identidad/tiempo/soporte, sin usar targets; luego, dentro de cada fold, ajustar cualquier escalador, imputador, selección y climatología solo en entrenamiento. Walk-forward con origen creciente y bloques de prueba contiguos de 12 meses (años enteros); conservar un gap de al menos 12 meses cuando haya ventanas/targets solapados de ese horizonte. El holdout final no participa en tuning. Informar métricas por fold y contra baseline; diagnosticar autocorrelación y tamaño efectivo. Split aleatorio no es válido como evaluación principal.

## Problemas predictivos candidatos

| Problema | Objetivo/horizonte y unidad | Baselines y alternativas simples | Condición de datos y límite | Prioridad |
|---|---|---|---|---|
| A. Humedad del suelo al mes siguiente | GLDAS `SoilMoi0_10cm_inst`, kg m-2, t+1 en soporte común de celda/área aprobada | Persistencia `SM(t)`; baseline estacional `SM(t-12)`; Ridge con historia de SM y luego precipitación/temperatura rezagadas | Validar contra holdouts anuales; GLDAS es salida de modelo/sistema de asimilación, no observación directa; dependencias con forzantes impiden decir causalidad. Primera tarea predictiva más concreta una vez satisfechos datos. | **1** |
| B. Condición relativamente seca/húmeda | Clase definida previamente para objetivo y ventana (p. ej. SM relativa a climatología local; horizonte t+1), no umbral ad hoc | Persistencia de clase; frecuencia/climatología estacional; logística regularizada | Requiere referencia climática multianual, umbral local defendible, eventos/clases representados en cada fold y métricas de calibración/desbalance. Es la salida más interpretable para alertas, pero su definición científica aún está abierta. | **2, después de A/climatología** |
| C. Evolución de precipitación o T2M | IMERG tasa o MERRA-2 T2M, t+1 y soporte nativo/co-localizado | `y(t)` y `y(t-12)`; Ridge autorregresiva | Los productos ya son estimaciones/análisis y no necesariamente la verdad observada; un modelo puede solo reproducir persistencia/estación, con baja utilidad frente a producto NASA. Comparar habilidad fuera de muestra antes de ofrecer predicción. | **3** |

### Familias y umbral práctico de preparación

Comparar baseline estacional (`y(t-12)`) y persistencia (`y(t)`) contra Ridge/Elastic Net; AR/estacional estadístico como alternativa univariada. Random Forest/Gradient Boosting solo si tamaño efectivo y validación sostienen comparación. No proponer LSTM/redes neuronales para unas pocas centenas de meses.

Requisito inicial propuesto, no gate científico aprobado: al menos 10 años completos emparejados (120 meses) para iniciar una validación walk-forward de factibilidad, perder hasta 12 meses por lag y conservar varios bloques anuales fuera de muestra; preferible 20+ años si cada colección conserva versión/linaje comparable. Aun con n=120, la autocorrelación reduce n efectivo y no garantiza potencia o habilidad. Para clasificar sequía, exigir además eventos suficientes por clase y folds; determinarlo mediante análisis de prevalencia antes de entrenar. Estos umbrales son salvaguardas de ingeniería a revisar con DS, no garantía estadística.

## Adquisición incremental propuesta

Prioridad inmediata: completar MERRA-2 `M2TMNXSLV` v5.12.4 y GLDAS `GLDAS_NOAH025_M` v2.1 para febrero–diciembre de 2005 (22 granules), y verificar sidecars/hashes, atributos de unidad, calendario y forma antes de ampliar ventana. Los tamaños observados en enero implican aproximadamente 599 MB de MERRA-2 y 276 MB de GLDAS para los 11 meses faltantes, ~875 MB total sin sidecars/procesado; son extrapolaciones de un solo archivo por producto.

La cobertura de catálogo reportada para estas colecciones contiene el período candidato: IMERG mensual desde 2000-06, GLDAS Noah mensual desde 2000-01 y MERRA-2 mensual desde 1980 (catálogo actualizado en octubre de 2026). Esto indica que 2005–2024 es históricamente adquirible, no que los 240 granules estén individualmente recuperables o verificados. Los tres catálogos tienen suficiente cobertura bruta para la ventana; hay que confirmar cada mes y versión vía CMR antes de planificar el panel. Para terminar 2005 faltan solo 22 granules; para una ventana 2005–2024, contando 240 meses/producto y lo que ya se tiene, se estiman ~22 GiB globales en crudo, extrapolación de escasas muestras y sin sidecars/derivados.

La documentación GES DISC indica que el subsetting está disponible solo para colecciones que lo muestran y requiere login Earthdata; la UI puede seleccionar variables, región espacial, dimensiones y formato. La ficha GLDAS Noah mensual expone subset/download; MERRA-2 dispone de catálogo y directorio granule, pero el soporte exacto de subsetting para `M2TMNXSLV` y las opciones para estos granules deben confirmarse en la ficha antes de estimar ahorro. Las fichas actuales indican ventanas históricas que incluyen 2005–2024 y el catálogo MERRA-2 informa latencia de unas tres semanas; GLDAS e IMERG Final también son productos retrasados. No se ejecutó solicitud ni se descargó ningún archivo. [GES DISC: guía de subsetting y requisito Earthdata](https://disc.gsfc.nasa.gov/help), [NASA: IMERG mensual, cobertura y latencia](https://catalog.data.gov/dataset/gpm-imerg-final-precipitation-l3-1-month-0-1-degree-x-0-1-degree-v07-gpm_3imergm), [NASA: GLDAS Noah mensual, cobertura](https://data.nasa.gov/dataset/gldas-noah-land-surface-model-l4-monthly-0-25-x-0-25-degree-v2-1-gldas-noah025-m-at-ges-di-23acd), [NASA: MERRA-2 mensual, cobertura y catálogo](https://catalog.data.gov/dataset/merra-2-tavgm_2d_slv_nx-2dmonthly-meantime-averagedsingle-levelassimilationsingle-level-di).

Procedimiento propuesto: buscar primero en CMR por la colección/mes exacto; consultar si GES DISC ofrece subset de variable+ventana; probar un solo mes para caja Murray–Darling ampliada a una celda de margen y confirmar grilla/bounds/unidades/hash y metadatos; escribir descarga a temporal y renombrar solo después de verificación, persistir manifest con CMR IDs, solicitud, bytes/hash/fecha, reintentar idempotentemente por archivo; conservar original y registrar fallo por granule. Si subsetting no está soportado o cambia/omite metadatos/bounds, preferir pocos NetCDF completos de ~25–55 MB cada uno. 20 años globales estimados en la nota de auditoría (~22 GiB) quedan como orden de magnitud basado en escasos tamaños de muestra, no presupuesto confirmado.

## Recomendación de alcance siguiente

1. Completar 2005 en MERRA-2 y GLDAS; actualizar matriz desde el inventario y validar el archivo/metadata resultante.
2. Preparar un panel **puntual exploratorio** con un soporte espacial escogido y documentado, preservando cada grilla original; no llamarlo MDBA regional. Antes de la decisión de soporte regional, revisar bounds y máscara con responsables de Gate R.
3. Solo tras continuidad QA/linaje, completar bloques de años. Evaluar A (humedad del suelo t+1) con baseline y Ridge/AR bajo walk-forward. Diseñar B junto con dominio de sequía y validación de umbral, no como etiqueta de conveniencia.
4. Proponer tarjeta FUL siguiente para adquisición/verificación temporal GLDAS+MERRA y armonización puntual, con aceptación y QA propias. Mantener este código separado de API/serving.

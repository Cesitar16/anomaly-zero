# Contrato de intercambio Frontend–FastAPI–Data Science v0 (propuesta)

> **Estado: propuesta para revisión; no aprobada.** Este documento continúa el borrador de la PR #3 y concreta una forma inicial del intercambio. Las rutas, campos, límites e identificadores marcados aquí son propuestas de contrato; no son decisiones aceptadas por el equipo. No implementa endpoints, modelos Pydantic, análisis, procesamiento de datos ni componentes React.

Relacionada con [AZ-04 / FUL-108](https://linear.app/fullstack-track/issue/FUL-108/az-04-disenar-y-aprobar-contratos-frontend-fastapi-data-science).

## Estado del repositorio y alcance

El código actual contiene FastAPI con `GET /health`; los módulos `backend/app/api/`, `schemas/`, `services/` y `analysis/` no tienen implementaciones. React sigue siendo la plantilla Vite y no hay clientes de datos ni vistas consumidoras. Estas rutas definen una interfaz futura de Anomaly Zero; no son endpoints NASA.

El catálogo candidato incluye MERRA-2 T2M, GPM IMERG Final precipitation y GLDAS Noah SoilMoi0_10cm_inst. La región Murray–Darling y 2005-01 a 2024-12 son contexto de trabajo, no cobertura científica aprobada. El inventario, los archivos reales y las revisiones de FUL-104/106/107 determinan qué datos llegan a publicarse.

Los cinco ejemplos al final son fixtures sintéticos. Cada raíz lleva `"synthetic": true`; el servicio real devolvería `false`. Ningún número de los ejemplos representa una observación o resultado estadístico.

## Convenciones propuestas

- Prefijo `/api/v1`; versión informativa `contract_version: "0.1-draft"`. Romper compatibilidad requeriría una versión mayor de ruta; añadir campos opcionales podría permanecer en la versión menor, sujeto a acuerdo.
- JSON UTF-8. IDs son cadenas opacas, estables y no reutilizadas: `region_id`, `product_id`, `dataset_id`, `analysis_id`. Los ejemplos usan IDs sintéticos.
- Las peticiones de series usan `start` y `end` en `YYYY-MM`, meses inclusivos, con `start <= end`. La respuesta etiqueta cada mes con su primer día (`YYYY-MM-01`). `calendar` es `null` mientras no se haya verificado para la fuente.
- La frecuencia disponible en v0 es `monthly`. No se remuestrea ni se interpola.
- `null` significa no disponible/no calculado/desconocido según el campo y su razón; nunca significa cero. Cero es un valor numérico válido. JSON no puede contener NaN ni Infinity.
- `generated_at` es la hora de esa respuesta API en RFC 3339 UTC. `source_updated_at` refleja una fecha de actualización publicada por la fuente; `retrieved_at`, cuándo se recuperó el original; `snapshot_created_at`, cuándo se materializó el snapshot. Cada fecha es `null` si se desconoce y no se sustituye por la hora de consulta.
- Las etiquetas mensuales no contienen hora ni zona.
- La API lee snapshots internos verificados; una petición de React no descarga NASA ni abre NetCDF/HDF5.
- Política propuesta de frescura: un `dataset_id` identifica contenido inmutable, incluidos fuentes, selección y transformaciones; si cambian bytes fuente, selección espacial o transformaciones, se publica otro ID. `generated_at` no cambia el dataset. El cliente no asume frescura por una respuesta de catálogo; las respuestas usan `Cache-Control: no-store` mientras no se acuerde una política distinta. No se propone infraestructura de caché.

### Envolventes comunes

Toda respuesta JSON propuesta lleva `contract_version`, `synthetic` y `generated_at`. En producción, `synthetic` es `false`; los fixtures de esta página usan `true`.

La respuesta de error tiene `contract_version`, `synthetic` y `error`. El objeto `error` contiene `code`, `message`, `retryable`, `request_id` y `details`; este último es un objeto seguro con campos de contexto o `null`. El ejemplo 3 muestra el envelope completo.

`request_id` identifica la petición y sirve para soporte; no es un token de acceso. `details` puede ser `null` si no hay detalles seguros que exponer. Nunca se devuelven cookies, credenciales ni mensajes internos del proveedor.

Mapa propuesto: `422` (`INVALID_PARAMETER`, `PERIOD_OUT_OF_COVERAGE`, `LIMIT_EXCEEDED`, `INSUFFICIENT_DATA`) y `409` (`ANALYSIS_METHOD_UNAVAILABLE`) no son reintentables sin cambiar la petición o habilitar un método; `404 RESOURCE_NOT_FOUND` tampoco. `503 SERVICE_UNAVAILABLE` representa una indisponibilidad temporal y usa `retryable: true`. `500 INTERNAL_ERROR` usa `retryable: false`; el cliente no deduce éxito, ausencia de datos ni estado pendiente desde un mensaje. El campo `code` guía la UI; `message` es informativo.

## Catálogo de dominio y significado

### Región

Propuesta de descriptor: `region_id`, `name`, `geometry_version`, `geometry_source`, `crs` y `area_km2`. El área, versión, geometría y CRS se devuelven como `null` hasta validar y aprobar esos datos. Una coordenada de centro dentro de un polígono no implica que toda su celda esté cubierta.

### Producto y dataset

`product_id` identifica la definición de variable/producto; `dataset_id` identifica un snapshot inmutable específico usado por una respuesta o análisis. Un snapshot distinto, checksum distinto o transformación distinta debe tener otro `dataset_id`. La API lo asigna y lo entrega en la respuesta de serie; no lo inventa ni lo construye el frontend.

Descriptor de producto propuesto:

- `product_id`, `short_name`, `product_version`, `variable`, `quantity`, `unit`, `availability`, `current_dataset_id`, `coverage` y `quality`.
- `source`: agencia, distribuidor, ID de colección, DOI/URLs y nombres/IDs de granules cuando estén disponibles.
- `availability`: `available` si hay snapshot para todo el rango publicado, `partial` si hay snapshot con huecos, `unavailable` si no hay snapshot utilizable.
- `current_dataset_id`, `coverage` y `quality` pueden ser `null` si no hay snapshot publicado.

La respuesta de serie lleva `dataset_id` (snapshot exacto), `provenance` (hashes originales, tiempos y manifiesto), `coverage`, `quality`, `transformations` y `spatial_aggregation` en su envelope, no dentro de `Product`. La identidad del snapshot se resuelve con `dataset_id` y `manifest_sha256`; cada checksum de archivo referencia el original conservado. Los campos desconocidos son `null`, no estimaciones. El objeto `quality` incluye `source_flag_fields` (nombres disponibles), `provider_flags_applied`, `source_missing_attributes` (atributos `_FillValue`, `missing_value`, `scale_factor`, `add_offset` con valores crudos o `null`), `finite_non_fill_filter_applied`, `verification_state`, `mask_applied`, `qa_checks` y `uninterpreted_provider_fields`. `qa_checks` registra controles ejecutados con identificador/versión, estado, si se aplicaron, exclusiones y motivos conocidos; lista vacía significa que no se reportan controles, no que QA haya pasado. Los campos de proveedor disponibles y los efectivamente aplicados son distintos. `quality.verification_state` puede ser `unassessed`, `basic_checks_only` o `provider_qa_applied`; el último solo se usa si se aplicaron de verdad flags de la fuente. Para IMERG, `precipitationQualityIndex`, `randomError` y `gaugeRelativeWeighting` conservan su identidad y significado; no se sustituyen entre sí ni se reinterpretan como porcentaje de exactitud. En `series[].quality.provider_flags` se devuelven pares `{name, value}` originales sin reinterpretarlos.

Catálogo candidato y significado/unidad de trabajo (IDs, versiones y catálogo no quedan aprobados por este borrador):

| ID propuesto | Colección CMR candidata / versión | Variable original → nombre en contrato | Significado que debe conservarse | Unidad observada en muestra | DOI candidato |
| --- | --- | --- | --- | --- | --- |
| `P01` | MERRA-2 `M2TMNXSLV`, concept ID `C1276812859-GES_DISC`, `5.12.4` | `T2M` → `T2M` | Temperatura del aire a 2 m; no temperatura superficial | `K` | `10.5067/AP1B0BA5PD2K` |
| `P02` | IMERG Final `GPM_3IMERGM`, concept ID `C2723754851-GES_DISC`, colección `07`; los archivos de muestra declaran `V07B` | `Grid/precipitation` → `precipitation` | Tasa media mensual; no acumulado mensual | `mm/hr` | `10.5067/GPM/IMERG/3B-MONTH/07` |
| `P03` | GLDAS Noah `GLDAS_NOAH025_M`, concept ID `C1342986036-GES_DISC`, `2.1` | `SoilMoi0_10cm_inst` → `SoilMoi0_10cm_inst` | Humedad modelada de suelo, capa 0–10 cm; salida mensual promedia salidas de 3 horas, no es medición puntual directa | `kg m-2` | `10.5067/SXAVCZFAQLNO` |

MERRA-2 `T2M` significa temperatura del aire a 2 m. IMERG `precipitation` se conserva como tasa en `mm/hr`, no se multiplica por horas para presentarla como acumulado. No completar huecos de IMERG Final con Early/Late; el inventario consultado registra Final V07 hasta 2025-09, que no equivale a cobertura válida. GLDAS Noah 2.1 es modelado; no confundir la producción principal con Early Product. Contrastar las referencias con [catálogo y límites](datasets.md) y [muestras BE-02](be-02-sample-workflow.md) antes de implementar.

La versión exacta, atributos de archivo y campos de calidad deben concordar con los originales y manifiestos. Finito/distinto de fill solo acredita ese filtro básico; **no significa que se aplicaran flags QA**. El conteo de centros no mide superficie cubierta. Si se transforma una unidad, `transformations` debe registrar operación, parámetros, unidad inicial/final y versión del código; en ausencia de transformación, es una lista vacía. Esta v0 no solicita ni propone aplicar conversiones.

### Serie

Cada elemento de `series` es `{date, value, quality}`. `value` está en la unidad declarada por `product.unit`, con significado físico declarado arriba, o es `null`. `quality.state` describe el conocimiento de calidad: `unassessed`, `missing` o `unknown`; no afirma QA aprobada. `provider_flags` contiene solo los flags originales observados, no reinterpretaciones. `missing_reason` es texto/código o `null`.

`coverage.expected_periods`, `present_periods`, `valid_periods` y `missing_periods` describen períodos de la serie. `present_periods` cuenta períodos con una entrada temporal de la fuente aunque su valor sea fill; `valid_periods` cuenta valores finitos no-fill, sin afirmar que se filtraran QA flags ni medir área. `missing_periods` lista puntos con `value: null`. Un cero finito no-fill cuenta como presente y en `valid_periods`. La propiedad opcional `spatial_coverage` conserva conteos de celdas y áreas/razones cuando el método espacial los haya calculado: `valid_area_km2 / intersection_area_km2` es cobertura del soporte intersectado y `valid_area_km2 / basin_area_km2` es cobertura de la cuenca completa. Ambos denominadores son distintos; centros de celda o `valid_periods` no los sustituyen. Si no hay medida validada, los números son `null` y no se infieren.

`spatial_aggregation` declara qué soporte espacial representa cada valor de toda la serie. `support_type` distingue `point_sample`, `descriptive_mean` y `regional_aggregate`; no se infiere el significado desde la geometría de `region`.

- `point_sample` identifica una celda/punto (`point.cell_id` y coordenadas, `null` si no se conocen), no una media de la región.
- `descriptive_mean` significa una media explícita del conjunto de celdas señalado por `cell_count`, con método y referencia de ponderación (si aplica), y estado `descriptive_only`; no se presenta como media de cuenca validada ni como porcentaje de superficie.
- `regional_aggregate` solo se emite con `approval_state: "approved"`, método, máscara, referencia de ponderación (si aplica) y referencia de aprobación registrados. La decisión queda pendiente; este contrato no declara ninguna agregación aprobada.

Si no hay registros, `spatial_aggregation` es `null`. En el ejemplo de éxito todas las fechas describen el mismo punto sintético; cada `value` corresponde a una muestra de esa celda. El frontend puede distinguirla de una media descriptiva o de una agregación regional aprobada leyendo `support_type` y `approval_state`.

### Resultado de análisis

`analysis_id` lo asigna el backend al crear un recurso mediante `201` o `202`. El frontend lo guarda para abrir la vista y consultar `GET /api/v1/analyses/{analysis_id}` al navegar o recargar. El contrato no propone colas ni polling automático. Un cálculo que de verdad se aceptó puede pasar de `pending` a `complete`; si no hay procesador, no se crea el recurso y se usa `409 ANALYSIS_METHOD_UNAVAILABLE`. Repetir GET devuelve el estado actual mientras se retenga el registro. Cuando se solicita otra ejecución, recibe otro ID.

El objeto propuesto incluye `analysis_id`, `dataset_id`, `region_id`, `product_id`, `product_version`, `variable`, `quantity`, `input_unit`, ventana mensual inclusiva, `source`, `provenance`, `transformations`, `spatial_aggregation`, `status`, `method`, `metrics` y `limitations`. `spatial_aggregation` conserva el mismo soporte de los datos usados por el análisis. `input_unit` y `quantity` describen los datos analizados; `metrics.slope_unit` describe la salida y queda `null` hasta definir método y unidad de tiempo. En `pending`, el método aceptado debe estar identificado y las métricas todavía no calculadas son `null`; nunca usar `p_value: 0` para representar ausencia. No se fija método, mínimo de muestra, unidad de pendiente, intervalo de confianza, valor p ni umbral de significancia en esta propuesta.

Estados y creación se distinguen así: `not_available` es un rechazo previo a crear el recurso (`409 ANALYSIS_METHOD_UNAVAILABLE`, sin `analysis_id`); `insufficient_data` es rechazo previo (`422 INSUFFICIENT_DATA`); `pending` solo significa que el cálculo fue aceptado y un procesador confirmó que ya está trabajando (respuesta `202` con `analysis_id`); `complete` significa cálculo terminado. El contrato v0 no habilita un método ni exige un procesador: por ello no produce `pending` hasta que exista esa capacidad. No hay colas ni consulta automática periódica; el cliente puede hacer un GET explícito al navegar a un análisis aceptado. Un error técnico usa el envelope de error y nunca se disfraza de `pending`, `no_data` o `complete`.

## Recursos propuestos

### `GET /api/v1/regions`

- **Parámetros:** ninguno.
- **Validaciones:** ninguna; devuelve regiones publicadas. Una lista vacía es válida.
- **200:** `{contract_version, synthetic, generated_at, regions: Region[]}`. Cada `Region` usa el descriptor de región definido arriba.
- **Errores:** `503 SERVICE_UNAVAILABLE` si no se puede leer el catálogo interno; respuesta de error común con `retryable: true`.
- **Caché:** se propone `Cache-Control: no-store` mientras no se apruebe otra política.

### `GET /api/v1/products?region_id=REG01`

- **Parámetros:** requerido `region_id`.
- **Validaciones:** ID no vacío; la región debe existir. Un ID desconocido produce 404.
- **200:** `{contract_version, synthetic, generated_at, region_id, products: Product[]}`. Cada producto informa disponibilidad `available`, `partial` o `unavailable`, variable/unidad, fuente, cobertura temporal, calidad y el `current_dataset_id` del snapshot actual o `null`.
- **Errores:** 422 `INVALID_PARAMETER` si falta/formato inválido; 404 `RESOURCE_NOT_FOUND` si la región no existe; 503 `SERVICE_UNAVAILABLE` si falla el catálogo interno.
- **Caché:** se propone `Cache-Control: no-store` mientras no se apruebe otra política.

### `GET /api/v1/series?region_id=REG01&product_id=P02&start=2005-01&end=2005-12&frequency=monthly`

- **Parámetros requeridos:** `region_id`, `product_id`, `start`, `end`, `frequency`.
- **Validaciones:** región y producto deben existir y estar relacionados; formato mensual ISO válido; inicio no posterior al fin; frecuencia exactamente `monthly`; máximo propuesto de 240 meses por respuesta. Si existe un período de cobertura publicado, una solicitud fuera de ese rango produce `PERIOD_OUT_OF_COVERAGE`; no se trunca silenciosamente. Un rango válido sin registros devuelve `data_state: "no_data"`.
- **200 con datos:** respuesta `SeriesResponse` con `generated_at`, `data_state: "available"` o `"available_with_gaps"`, `dataset_id`, producto, procedencia, coberturas, calidad, agregación, transformaciones y períodos ordenados ascendentemente.
- **200 sin registros:** mismo envelope con `data_state: "no_data"`, `dataset_id: null`, `provenance: null`, cobertura disponible nula, `valid_periods: 0`, lista `series: []` y mensaje. Es distinto de un valor cero y de un error temporal del snapshot.
- **Huecos dentro de datos:** un período esperado sin valor se devuelve como punto con `value: null` y razón; no se rellena con cero.
- **Errores:** 422 `INVALID_PARAMETER`, `PERIOD_OUT_OF_COVERAGE` o `LIMIT_EXCEEDED`; 404 `RESOURCE_NOT_FOUND` para región/producto desconocidos; 503 `SERVICE_UNAVAILABLE` si el snapshot no se puede leer.
- **Caché:** se propone `Cache-Control: no-store`; el identificador de snapshot permite detectar contenido idéntico, pero no sustituye una política de frescura aprobada.

### `POST /api/v1/analyses`

- **Parámetros:** JSON `{dataset_id, window: {start, end, end_inclusive: true}}`. La ventana usa los meses `YYYY-MM` inclusivos definidos arriba. `dataset_id` debe ser el que entregó una respuesta de serie; no se aceptan archivos NASA ni IDs del cliente.
- **Validaciones:** snapshot existente; ventana mensual ISO inclusiva dentro de cobertura del dataset; máximo 240 meses. Si no hay observaciones suficientes para una operación habilitada, responder 422 `INSUFFICIENT_DATA` con forma de error común.
- **201:** solo para análisis completado sincrónicamente; devuelve `AnalysisResponse` con `status: "complete"` y `analysis_id`.
- **202:** solo cuando hay un procesador que aceptó el cálculo y confirmó que está activo; devuelve `status: "pending"`, método identificado, métricas todavía nulas y `analysis_id`. `Location` apunta al GET del análisis. La existencia de este estado no exige diseñar colas ni polling automático.
- **Errores:** 422 `INVALID_PARAMETER`, `PERIOD_OUT_OF_COVERAGE`, `LIMIT_EXCEEDED` o `INSUFFICIENT_DATA`; 404 `RESOURCE_NOT_FOUND` si `dataset_id` no existe; 409 `ANALYSIS_METHOD_UNAVAILABLE` si no hay método habilitado/aprobado, antes de crear ID; 503 `SERVICE_UNAVAILABLE` si el snapshot no está disponible. Un 503/5xx no se debe convertir en “sin datos”.
- El método no disponible no crea ni persiste un análisis: la UI muestra que aún no está habilitado y no espera una transición. La durabilidad/retención del registro tras `201` o `202` no se garantiza en v0 y requiere decisión de implementación; mientras el registro exista, GET representa el mismo snapshot/ventana/resultado; si expiró o no existe devuelve 404.

### `GET /api/v1/analyses/{analysis_id}`

- **Parámetros:** ID opaco en la ruta.
- **Validaciones:** no vacío y formato de ID admitido por el servicio.
- **200:** el mismo `AnalysisResponse` creado por POST, incluidos `dataset_id`, ventana y procedencia.
- **Caché:** se propone `Cache-Control: no-store`; el cliente consulta al navegar o recargar, no en un bucle.
- **Errores:** 404 `RESOURCE_NOT_FOUND` si el ID no existe o el registro expiró; 503 `SERVICE_UNAVAILABLE` si el snapshot/registro no se puede leer temporalmente.

### Límites, latencia y raster opcional

Las series quedan limitadas a 240 puntos mensuales por respuesta; se propone JSON sin paginación para ese máximo. No hay SLO de latencia ni tiempos medidos; los endpoints de datos/estadística se proponen sincrónicos solo con ese límite acotado. El límite temporal y el modo sincrónico requieren medición con implementación real antes de considerarse garantía.

No se transmiten rasters NetCDF/HDF5 completos a React. Se propone un descriptor opcional de capa, no una URL de descarga de archivos pesados: `{dataset_id, date, layer_type, unit, state, format, tile_template}`. `date` identifica un instante/mes; `layer_type` distingue `value`, `anomaly`, `slope` o `significance`, y cada tipo conserva esa semántica en la UI. Hasta comprobar datos, formato y necesidad de mapa, `state` será `unavailable` y `format`/`tile_template` serán `null`. Si se aprueba, servir tiles o imágenes derivadas con descriptores pequeños; codificación, tamaño máximo por tile y latencia quedan por medir y aprobar. La especificación OpenAPI modela esta forma como `RasterLayer`; su presencia no afirma disponibilidad. No se propone recurso de exportación: AZ-04 no pide exportar.

## Decisiones que requieren aprobación

| Decisión pendiente | Campos/operación afectados | Responsable de aprobación | Implementación que depende |
| --- | --- | --- | --- |
| IDs/versiones definitivos, cobertura por producto, unidades/calendario y semántica de variables; procedencia y flags disponibles en originales | Catálogo `GET /products`; `Product`, `Source`, `coverage`, `quality`, `unit`, fechas | Lucas; revisión estadística de César cuando cambie interpretación | Catálogo backend, ingesta de snapshots y validaciones de frontend |
| Geometría exacta, máscara y agregación; cuándo usar ponderación y qué significa una serie “regional” | `GET /series`; `spatial_aggregation`, cobertura/calidad, unidad y valor | Lucas (geometría/procedencia) y César (semántica del agregado) | Agregación Data Science y mapas/cobertura de React |
| Método estadístico, mínimos de datos, unidad de pendiente, incertidumbre, p-valor y regla de significancia | `POST/GET /analyses`; `method`, `metrics`, estados `pending/complete` y errores `INSUFFICIENT_DATA` | César; Lucas si depende de unidades/productos | Cálculo Data Science y presentación/interpretación en React |
| Campos visibles, errores/estados y experiencia de crear/abrir `analysis_id` | Todos los envelopes; `Location`; nombres de rutas | Alejandra | Cliente React, rutas de vista y mensajes de estado |
| Rasters, tile descriptor/formato, tamaño máximo y latencia aceptable | Descriptor de raster opcional; respuestas y límites | Lucas (validez/cobertura), Alejandra (uso UI) y backend (servicio/límites) | Publicación raster, capa de mapa y política de rendimiento |
| Propuesta de versión `/api/v1`, campos obligatorios y límites | Todos los recursos | Alejandra, César, Lucas y responsable backend | Esquemas OpenAPI/Pydantic y compatibilidad del cliente |

La colección y el alcance científico siguen condicionados por [FUL-107](https://linear.app/fullstack-track/issue/FUL-107/az-03-aprobar-alcance-cientifico-inicial-con-matriz-de-productos-region-y-calidad); arquitectura y API base dependen además de FUL-99 y FUL-103. Esta propuesta no cierra esos bloqueos.

## Glosario

| Término | Significado en este contrato |
| --- | --- |
| `product_id` | Identidad estable de la definición de producto y variable; no identifica bytes concretos. |
| `dataset_id` | Identidad opaca de un snapshot inmutable con sus fuentes, selección espacial y transformaciones. |
| `analysis_id` | Identificador asignado por el servicio solo tras aceptar y crear un análisis. No existe si el método se rechaza como no disponible. |
| `generated_at` | Instante UTC en que se generó la respuesta API. |
| `source_updated_at` | Marca publicada por el proveedor/original, si se conoce; no equivale a recuperación ni materialización. |
| `retrieved_at` | Instante de recuperación del original. |
| `snapshot_created_at` | Instante de materialización del snapshot derivado. |
| `present_periods` / `valid_periods` | Meses con entrada temporal / con valor finito distinto de fill. Ninguno demuestra que se aplicaron QA flags ni mide superficie cubierta. |
| `pending` | Análisis creado y aceptado cuyo procesamiento está confirmado en curso. No significa método no disponible ni datos insuficientes. |
| `not_available` | Rechazo previo a crear el recurso porque no existe método aprobado y habilitado; se representa con `409` y no incluye `analysis_id`. |
| `synthetic` | Marca explícita de fixtures; no indica calidad ni observación real. |

## ADR AZ-04-001 — Contrato de intercambio v0

**Estado:** Proposed; pendiente de revisión multidisciplinaria. No es un acuerdo del equipo.

- **Objetivo:** permitir que React, FastAPI y Data Science implementen contra un intercambio común sin hacer depender las vistas de la disponibilidad del pipeline NASA o de métricas científicas aún no aprobadas.
- **Recursos:** se proponen catálogo de regiones/productos, lectura de series por rango y creación/consulta de análisis. No se proponen exportación ni nuevos endpoints raster; el descriptor raster permanece opcional.
- **Identificadores:** IDs opacos. El backend entrega `dataset_id` al responder una serie y entrega `analysis_id` solo en un `201` completado o `202` realmente aceptado. React conserva el ID de análisis y lo usa en GET.
- **Versionado:** prefijo propuesto `/api/v1` y `contract_version: "0.1-draft"`; cambios incompatibles requieren revisión y una versión mayor de ruta.
- **Análisis:** no se crea registro para método no aprobado (`409 not_available`) ni datos insuficientes (`422`). `pending` solo se devuelve si un procesador ya aceptó el trabajo; el v0 no requiere cola, polling ni cálculo. `complete` se devuelve solo con cálculo ejecutado. Un error técnico usa el envelope común.
- **Datos y frescura:** `dataset_id` y `manifest_sha256` identifican snapshot inmutable; cambios de originales o transformaciones generan otro dataset. La respuesta separa marcas de fuente, recuperación, snapshot y generación API. No se promete persistencia durable ni política HTTP de caché más allá de `no-store` propuesto.
- **Faltantes y calidad:** `null` no es cero; no-data es una respuesta exitosa vacía solo para una consulta válida; errores upstream siguen siendo errores. Finito/no-fill no implica QA aplicada y el conteo de centros no expresa superficie.
- **Alternativas descartadas por ahora:** frontend descargando NASA/HDF/NetCDF, crear un análisis pendiente sin procesador, inferir un snapshot desde `product_id`, añadir jobs/colas/polling, y publicar métricas o agregaciones sin decisión científica.
- **Consecuencias:** mocks tipados pueden avanzar; implementación real queda sujeta a aprobación de unidades, calendario, geometría, agregación, estadística, retención y raster. Los endpoints descritos aún no existen.

## Registro de revisión y aprobación

Este registro no contiene conformidades ni firmas; cada persona debe completar su resultado tras revisar el documento y [OpenAPI](openapi-contract-v0.yaml).

| Revisor | Comprobación solicitada | Resultado | Evidencia / observaciones |
| --- | --- | --- | --- |
| César | Semántica estadística, métricas, unidades derivadas y limitaciones | Pending review | Pendiente de respuesta registrada en PR o Linear. |
| Lucas | Fuentes, versiones, calidad/flags, geometría, calendario y procedencia | Pending review | Pendiente de respuesta registrada en PR o Linear. |
| Alejandra | Consumo React, estados UI y flujo `analysis_id` | Pending review | Pendiente de respuesta registrada en PR o Linear. |
| Alaín | Viabilidad técnica FastAPI, errores y consistencia OpenAPI | Pending review | Pendiente de respuesta registrada en PR o Linear. |

## Ejemplos JSON sintéticos

Los ejemplos son fixtures de forma, no datos ni resultados científicos. `synthetic: true` aparece en la raíz de cada respuesta. `generated_at` es una marca sintética en estos fixtures; una respuesta real usaría la hora UTC de la petición. El primer ejemplo asigna cada valor a una sola celda sintética; no es un promedio espacial.

### 1. Serie con cero válido y un valor ausente

```json
{
  "contract_version": "0.1-draft",
  "synthetic": true,
  "data_state": "available_with_gaps",
  "region": {
    "region_id": "REG01",
    "name": "Región sintética",
    "geometry_version": null,
    "geometry_source": null,
    "crs": null,
    "area_km2": null
  },
  "product": {
    "product_id": "P02",
    "short_name": "GPM_3IMERGM",
    "product_version": "V07B",
    "variable": "precipitation",
    "quantity": "monthly_mean_rate",
    "unit": "mm/hr",
    "availability": "partial",
    "source": {
      "agency": "NASA/JAXA",
      "distributor": "GES DISC",
      "collection_id": "C2723754851-GES_DISC",
      "doi": "10.5067/GPM/IMERG/3B-MONTH/07",
      "source_urls": [],
      "granule_ids": []
    },
    "current_dataset_id": "ds-synthetic-001",
    "coverage": {
      "start": "2005-01",
      "end": "2005-03"
    },
    "quality": {
      "source_flag_fields": [],
      "provider_flags_applied": false,
      "source_missing_attributes": {
        "fill_value": -9999.9,
        "missing_value": null,
        "scale_factor": null,
        "add_offset": null
      },
      "finite_non_fill_filter_applied": true,
      "verification_state": "basic_checks_only",
      "mask_applied": null
    }
  },
  "dataset_id": "ds-synthetic-001",
  "provenance": {
    "source_sha256": [],
    "retrieved_at": null,
    "manifest_version": null,
    "source_updated_at": null,
    "snapshot_created_at": null,
    "manifest_sha256": null,
    "original_file_count": null
  },
  "temporal": {
    "frequency": "monthly",
    "calendar": null,
    "date_label": "month_start"
  },
  "requested_coverage": {
    "start": "2005-01",
    "end": "2005-03",
    "end_inclusive": true
  },
  "available_coverage": {
    "start": "2005-01",
    "end": "2005-03"
  },
  "coverage": {
    "expected_periods": 3,
    "present_periods": 3,
    "valid_periods": 2,
    "missing_periods": [
      "2005-02"
    ]
  },
  "quality": {
    "source_flag_fields": [],
    "provider_flags_applied": false,
    "source_missing_attributes": {
      "fill_value": -9999.9,
      "missing_value": null,
      "scale_factor": null,
      "add_offset": null
    },
    "finite_non_fill_filter_applied": true,
    "verification_state": "basic_checks_only",
    "mask_applied": null
  },
  "spatial_aggregation": {
    "support_type": "point_sample",
    "approval_state": "not_assessed",
    "method": null,
    "area_weighted": null,
    "weighting_reference": null,
    "mask_version": null,
    "point": {
      "cell_id": "cell-synthetic-001",
      "latitude": null,
      "longitude": null
    }
  },
  "transformations": [],
  "series": [
    {
      "date": "2005-01-01",
      "value": 0.42,
      "quality": {
        "state": "unassessed",
        "provider_flags": [],
        "missing_reason": null
      }
    },
    {
      "date": "2005-02-01",
      "value": null,
      "quality": {
        "state": "missing",
        "provider_flags": [],
        "missing_reason": "provider_fill_value"
      }
    },
    {
      "date": "2005-03-01",
      "value": 0.0,
      "quality": {
        "state": "unassessed",
        "provider_flags": [],
        "missing_reason": null
      }
    }
  ],
  "generated_at": "2026-01-01T00:00:00Z"
}
```

### 2. Período sin datos

```json
{
  "contract_version": "0.1-draft",
  "synthetic": true,
  "data_state": "no_data",
  "region": {
    "region_id": "REG01",
    "name": "Región sintética",
    "geometry_version": null,
    "geometry_source": null,
    "crs": null,
    "area_km2": null
  },
  "product": {
    "product_id": "P03",
    "short_name": "GLDAS_NOAH025_M",
    "product_version": "2.1",
    "variable": "SoilMoi0_10cm_inst",
    "quantity": "soil_moisture_layer_0_10_cm",
    "unit": "kg m-2",
    "availability": "unavailable",
    "source": {
      "agency": "NASA",
      "distributor": "GES DISC",
      "collection_id": "C1342986036-GES_DISC",
      "doi": "10.5067/SXAVCZFAQLNO",
      "source_urls": [],
      "granule_ids": []
    },
    "current_dataset_id": null,
    "coverage": null,
    "quality": null
  },
  "dataset_id": null,
  "provenance": null,
  "temporal": {
    "frequency": "monthly",
    "calendar": null,
    "date_label": "month_start"
  },
  "requested_coverage": {
    "start": "2005-01",
    "end": "2005-03",
    "end_inclusive": true
  },
  "available_coverage": null,
  "coverage": {
    "expected_periods": 3,
    "present_periods": 0,
    "valid_periods": 0,
    "missing_periods": [
      "2005-01",
      "2005-02",
      "2005-03"
    ]
  },
  "quality": {
    "source_flag_fields": [],
    "provider_flags_applied": false,
    "source_missing_attributes": {
      "fill_value": null,
      "missing_value": null,
      "scale_factor": null,
      "add_offset": null
    },
    "finite_non_fill_filter_applied": false,
    "verification_state": "unassessed",
    "mask_applied": null
  },
  "spatial_aggregation": null,
  "transformations": [],
  "series": [],
  "message": "No hay datos disponibles para el período solicitado.",
  "generated_at": "2026-01-01T00:00:00Z"
}
```

### 3. Snapshot/fuente no disponible

```json
{
  "contract_version": "0.1-draft",
  "synthetic": true,
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "El snapshot de datos no está disponible temporalmente.",
    "retryable": true,
    "request_id": "req-synthetic-001",
    "details": {
      "dataset_id": "ds-synthetic-001",
      "provider_status": null
    }
  },
  "generated_at": "2026-01-01T00:00:00Z"
}
```

### 4. Método de análisis no disponible (no se crea recurso)

La respuesta representa un rechazo previo a crear un análisis: `409`, sin `analysis_id`. El estado `not_available` explica la UI; no es un trabajo en curso ni debe consultarse repetidamente.

```json
{
  "contract_version": "0.1-draft",
  "synthetic": true,
  "generated_at": "2026-01-01T00:00:00Z",
  "error": {
    "code": "ANALYSIS_METHOD_UNAVAILABLE",
    "message": "No hay un método estadístico aprobado y habilitado; no se creó un análisis.",
    "retryable": false,
    "request_id": "req-synthetic-analysis-001",
    "details": {
      "analysis": {
        "state": "not_available",
        "analysis_id": null,
        "dataset_id": "ds-synthetic-001",
        "region_id": "REG01",
        "product_id": "P02",
        "window": {
          "start": "2005-01",
          "end": "2005-03",
          "end_inclusive": true
        },
        "method": null,
        "metrics": {
          "slope": null,
          "slope_unit": null,
          "confidence_interval": null,
          "p_value": null,
          "significance": null
        }
      }
    }
  }
}
```

### 5. Análisis aceptado que sigue en procesamiento (forma 202)

Este fixture enseña el envelope `202` si un procesador real aceptó y confirmó el trabajo. El identificador/nombre del método son sintéticos; no acreditan método aprobado ni ejecución existente. Todas las métricas permanecen `null`.

```json
{
  "contract_version": "0.1-draft",
  "synthetic": true,
  "generated_at": "2026-01-01T00:00:00Z",
  "analysis_id": "analysis-synthetic-pending-001",
  "dataset_id": "ds-synthetic-001",
  "region_id": "REG01",
  "product_id": "P02",
  "product_version": "V07B",
  "variable": "precipitation",
  "quantity": "monthly_mean_rate",
  "input_unit": "mm/hr",
  "window": {
    "start": "2005-01",
    "end": "2005-03",
    "end_inclusive": true
  },
  "source": {
    "agency": "NASA/JAXA",
    "distributor": "GES DISC",
    "collection_id": "C2723754851-GES_DISC",
    "doi": "10.5067/GPM/IMERG/3B-MONTH/07",
    "source_urls": [],
    "granule_ids": []
  },
  "provenance": {
    "source_sha256": [],
    "retrieved_at": null,
    "manifest_version": null,
    "source_updated_at": null,
    "snapshot_created_at": null,
    "manifest_sha256": null,
    "original_file_count": null
  },
  "transformations": [],
  "spatial_aggregation": {
    "support_type": "point_sample",
    "approval_state": "not_assessed",
    "method": null,
    "area_weighted": null,
    "weighting_reference": null,
    "mask_version": null,
    "point": {
      "cell_id": "cell-synthetic-001",
      "latitude": null,
      "longitude": null
    }
  },
  "status": "pending",
  "method": {
    "name": "synthetic-demonstration-method",
    "version": "0.0-synthetic"
  },
  "metrics": {
    "slope": null,
    "slope_unit": null,
    "confidence_interval": null,
    "p_value": null,
    "significance": null
  },
  "limitations": [
    "Fixture sintético de la forma 202; no representa un método aprobado ni un cálculo real."
  ]
}
```


### 6. Parámetro inválido

Respuesta sintética `422 INVALID_PARAMETER` para un mes fuera del formato/calendario admitido. La petición se corrige; el error no representa ausencia de datos.

```json
{
  "contract_version": "0.1-draft",
  "synthetic": true,
  "generated_at": "2026-01-01T00:00:00Z",
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "El formato del mes debe ser YYYY-MM.",
    "retryable": false,
    "request_id": "req-synthetic-invalid-001",
    "details": {"field": "start", "received": "2005-13"}
  }
}
```

## Archivos del contrato y siguiente implementación

La especificación declarativa versionada está en [`openapi-contract-v0.yaml`](openapi-contract-v0.yaml) y comparte nombres, estados, tipos y ejemplos con este documento. No se añadieron modelos Pydantic ejecutables porque la API aún no implementa estos recursos. Lucas revisa procedencia, producto, unidades, calendario, QA y cobertura; César revisa el significado estadístico y límites de los resultados; Alejandra comprueba los envelopes, estados y flujo React de obtención/uso de `analysis_id`; Alaín verifica viabilidad FastAPI y consistencia OpenAPI. La aprobación de AZ-04 aún depende de las relaciones existentes con FUL-107, FUL-103 y FUL-99; esta propuesta no las elimina.

No se añade exportación, integración NASA desde React, cola de trabajos ni formato raster ejecutable en esta tarjeta.

# FUL-107 — alcance científico provisional del MVP

**Estado:** propuesta para discusión, no selección aprobada. Corte de repositorio: `origin/dev` `b51ca0617a96d582e0239d661c00647da2a32e11` (15-11-2026). FUL-104, FUL-105 y FUL-106 están integradas mediante PR #14/#15, #11 y #9. No se registra aquí conformidad de Lucas, Alaín ni del equipo. Linear no se pudo consultar en esta sesión; confirmar allí estados y criterios textuales de FUL-107/FUL-110 antes del cierre.

Este documento sintetiza evidencia con soporte en [catálogo](catalog_mvp.json), [FUL-104](validacion_cientifica_ful104.md), [plan inferencial FUL-105](ful-105-plan-inferencia.md), [muestras BE-02](be-02-sample-workflow.md), [región MDBA](region_murray_darling.md), [contraste de fuentes](contraste_fuentes.md) y [notebook de EDA](../research/notebooks/02_eda_nasa_products.ipynb). Las tarjetas y decisiones científicas siguen siendo responsabilidad de sus titulares.

## Pregunta inicial propuesta

**¿Cómo varían descriptivamente, en el tiempo, la temperatura del aire a 2 m, la tasa de precipitación y el agua modelada en los primeros 10 cm del suelo en la cuenca Murray–Darling, y qué cobertura y calidad respaldan cada observación?**

Es descriptiva, no causal. Para el primer corte del MVP se propone mostrar una muestra real, su procedencia y sus límites; no se afirma aún una media regional validada, tendencia, anomalía ni significancia. La respuesta temporal solo se habilita cuando la serie y el protocolo superen los gates R y T.

## Inventario de evidencia por producto

Convenciones: **DOC** = metadato/documentación; **TEC** = lectura/comprobación ejecutada y descrita; **PARCIAL** = evidencia directa limitada al soporte/periodo indicado; **INF** = recomendación; **PEND** = no verificado. Los estados no son escalas de calidad científica.

| Campo | Temperatura del aire | Precipitación | Agua del suelo superficial |
| --- | --- | --- | --- |
| Producto / variable | MERRA-2 `M2TMNXSLV` 5.12.4, `T2M` (aire a 2 m) | GPM IMERG Final `GPM_3IMERGM`, colección 07, archivo `V07B`, `Grid/precipitation` | GLDAS Noah `GLDAS_NOAH025_M` 2.1 / granule 021, `SoilMoi0_10cm_inst` |
| DOI / origen | [10.5067/AP1B0BA5PD2K](https://doi.org/10.5067/AP1B0BA5PD2K), NASA GMAO/GES DISC | [10.5067/GPM/IMERG/3B-MONTH/07](https://doi.org/10.5067/GPM/IMERG/3B-MONTH/07), NASA GPM/GES DISC | [10.5067/SXAVCZFAQLNO](https://doi.org/10.5067/SXAVCZFAQLNO), NASA GSFC/GES DISC |
| Evidencia y localizador | FUL-104/105/106; PR #9/#11/#14/#15; granule/manifiesto Release BE-02, SHA en `be-02-sample-workflow.md` | FUL-104/105/106; PR #9/#11/#14/#15; doce granules/manifiestos en Release BE-02, hashes en `be-02-sample-workflow.md` | FUL-103/104/105/106; PR #9/#11/#14/#15; granule/manifiesto en Release/probe y `be-02-sample-workflow.md` |
| Unidad original / conversión | K; conversión derivada posible `°C = K − 273.15`, conservar K de origen | mm/h (tasa media mensual); no convertir en acumulado sin duración/convención explícitas | kg m⁻²; contenido de agua modelado en capa 0–10 cm, no humedad volumétrica |
| Resolución nativa y frecuencia | 0,625° lon × 0,5° lat; mensual; NetCDF4 | 0,1° × 0,1°; mensual; HDF5 | 0,25° × 0,25°; mensual; NetCDF4; `_inst` describe campos mensuales derivados de pasos de 3 h según el producto |
| Periodo inventariado | 240 meses CMR en bbox, 2005-01–2024-12 | 240 meses CMR en bbox, 2005-01–2024-12 | 240 meses CMR en bbox, 2005-01–2024-12 |
| Datos realmente inspeccionados | Granule original enero 2005; FUL-104 reporta también enero 2021. Se conserva fuera de Git. | Doce granules originales enero–diciembre 2005 en FUL-105; FUL-104 compara enero 2005/2021. | Original enero 2005 y muestra enero 2021 según FUL-104; EDA rectangular de enero 2005 y QA por centros MDBA en FUL-105/106. |
| QA disponible / aplicado | Fill y finitos; muestra enero 2005/2021. **No** existe regla QA aprobada/aplicada para toda la serie. | Fill/nonfinite revisados; candidatos `precipitationQualityIndex`, `randomError`. No se aplicaron filtros de esos flags. | Fill/nonfinite revisados. QA de proveedor y linaje temporal de máscara de agua pendientes. |
| Cobertura reportada | Enero 2005: 323 centros MDBA, 323 finitos/no-fill; no porcentaje de área | Enero 2005: 10.092/10.092 centros; los doce meses de 2005 mantienen 10.092/10.092, según notebook; denominador es número de centros | Enero 2005: 1.615/1.617 centros finitos/no-fill; dos faltantes. La caja global FUL-105 tiene otro denominador y no es cobertura de cuenca. |
| Comparación espacial FUL-104 | Enero 2005, centros vs fracción de área: 299,606 vs 299,730 K | 0,037816 vs 0,037790 mm/h | 15,904 vs 15,945 kg/m² |
| Estado de evidencia | **PARCIAL** — gránulo NASA abierto y QA básico, no serie regional | **PARCIAL** — doce meses abiertos y panel de 20 centros validado contra grilla; no filtro QA ni serie de 20 años | **PARCIAL** — lectura y muestra espacial; linaje 2005 indeterminado |
| Limitación principal | Dataset de reanálisis; QA/producto y máscara deben ser revisados; muestra corta | Tasa no es acumulado; `07`/`V07B` requiere semántica concordada por Lucas; flags no filtrados | No se determinó si enero 2005 incorpora corrección posterior de agua interior; no usar como agregado final validado |

**Interpretación correcta de inventarios:** las 240 fechas CMR por producto solo indican granules localizados dentro de un bbox de consulta. No significan 240 descargas, 240 archivos abiertos, valores finitos, valores que superan QA, celdas con cobertura espacial de cuenca, ni una serie regional validada. La Release `be02-samples-2005-v1` distribuye archivos/manifiestos; la copia portable IMERG contiene 240 valores (12 meses × 20 centros), no una muestra representativa de toda el área. Datos originales y geometría permanecen fuera de Git.

## Comparación de alternativas del MVP

| Alternativa | Relevancia y significado | Evidencia / viabilidad | Calidad y dependencias | Visualización y análisis futuro | Recomendación provisional |
| --- | --- | --- | --- | --- | --- |
| Aire a 2 m, MERRA-2 `T2M` | Temperatura atmosférica cerca de superficie, útil para describir estado térmico; no es temperatura de superficie terrestre | Muestra mensual nativa 0,5° × 0,625° abierta; enero 2005/2021 reportados por FUL-104 | Revisión QA completa, cobertura y homogeneidad temporal; es reanálisis y no observación directa de estación | Raster nativo de baja/mediana resolución y serie mensual futura | Candidato propuesto para primera serie temporal, condicionado a FUL-110 y Gate R |
| Precipitación, IMERG Final | Tasa media mensual de precipitación, no total mensual | Grilla 0,1° y doce meses de 2005 abiertos; adecuada para una demo de mapa de granule | Interpretar V07B, flags, valores cero, faltantes y cobertura; método espacial y QA pendientes | Mejor detalle visual de las tres muestras; serie futura no establecida por 12 meses | Propuesta para demo raster acotada, no ranking científico aprobado |
| Agua del suelo 0–10 cm, GLDAS Noah | Agua modelada en capa superficial, unidad masa/área; no equivalente a humedad volumétrica ni medición in situ | Resolución 0,25°; enero 2005 y 2021; EDA/reproducibilidad ya disponible | Linaje de máscara continental del granule 2005 desconocido; QA y sensibilidad temporal | Demo de valores de un granule posible con caveat; serie depende de resolver linaje | Mantener como variable candidata; no seleccionarla aún para serie regional |

**Propuesta para que el equipo evalúe:** IMERG permite una demo de grilla/raster etiquetada por fecha, fuente, unidad y QA pendiente; MERRA-2 `T2M` es un candidato condicional para la primera serie; GLDAS continúa en la terna y requiere resolver su linaje 2005. Ninguna alternativa es hoy un producto científicamente aprobado. Las tres fuentes no son independientes ni intercambiables: difieren en magnitud, resolución, método/forzantes y soporte.

## Región, periodo y agregación espacial

### Región propuesta

Murray–Darling es la región inicial **propuesta** porque la pregunta se formula para la cuenca y se dispone de una geometría MDBA completa reportada como Polygon EPSG:4326, con hash SHA-256 `d36fe31424758cc4fb8eef25e21b835bb5c05c793c746e8a1eb7b5a5841f6a53`, caché local y referencia de servicio en `region_murray_darling.md`. Antes de uso productivo, Lucas debe revisar la adecuación científica de la geometría y Alaín debe hacer reproducible la distribución/acceso. Confirmar datum, precisión de bordes, licencia/atribución y CRS de los granules. No usar el `LineString` demostrativo del repositorio como polígono. NSW puede ser una futura región administrativa para consulta, no grupo de control independiente ni réplica causal.

### Método de soporte

FUL-104 comparó selección por centro, celdas intersectadas y fracción de área en enero 2005/2021; FUL-105 usa centros para diagnóstico IMERG. En enero de 2005 la diferencia numérica centro/fracción fue pequeña para los tres productos, pero solo se observó en fechas y grillas concretas. No valida método, límites, geometría, cobertura ni faltantes para las otras 240 fechas. La media no ponderada de centros trata cada píxel seleccionado igual y no es media ponderada por superficie.

Matriz a resolver junto a FUL-110:

| Opción | Qué estima | Qué comprobar antes de aprobar |
| --- | --- | --- |
| Centro dentro del polígono | Estadístico de celdas cuyo centro está dentro; límites excluyen cruces sin centro interior | Resolución/área desigual, bordes, huecos y sensibilidad por producto/mes |
| Intersección | Selecciona celdas que tocan el polígono | Tratamiento de fracción diminuta, duplicidad/topología y pesos efectivos |
| Fracción de área | Peso por porción de celda que intersecta el polígono | Área geodésica/CRS, antimeridiano/topología, resolución y manejo de celdas faltantes |
| Media sin ponderar | Igual peso por celda seleccionada | Solo descriptiva; sesgo de área si áreas de celdas difieren; denominar soporte y no llamarla media de cuenca |

**Propuesta:** mantener fracción de área como alternativa a evaluar, sin seleccionarla; no crear agregador en esta tarjeta. Lucas prepara el dictamen científico y prueba sensibilidad por dataset; equipo aprueba método y denominador.

### Calendario

Ventana objetivo: enero 2005–diciembre 2024 (240 meses por producto, frecuencia mensual). Inventario CMR, archivos descargados, archivos abiertos, observaciones finitas, observaciones post-QA y valores regionales son niveles distintos. Por evidencia del handoff, las ventanas abiertas incluyen: MERRA-2 enero 2005 y muestras comparativas puntuales; IMERG enero–diciembre 2005; GLDAS enero 2005 y muestra comparativa enero 2021. Los valores regionales mensuales de 240 meses **no existen** en el proyecto.

Para aceptar la ventana se necesitará: manifest/hash por archivo, identidad homogénea/versionado o explicación de cambios, exactamente un archivo/estado por mes esperado, auditoría de meses faltantes/duplicados, atributos de tiempo/calendario/unidad, reglas QA por periodo, cobertura y método espacial reproducible, registro de meses excluidos y revisión independiente. No imputar ni convertir faltantes a cero.

## Tres niveles de producto

| Nivel | Permitido cuando | Contenido permitido | Estado actual |
| --- | --- | --- | --- |
| A — demo técnica | Granule auténtico/manifiesto reproducibles; identidad/variable/unidad/periodo verificados; fill y finitos contados; procedencia y soporte etiquetados | Ficha de muestra; gráfico/raster de la grilla nativa con fecha y unidad; QA `unassessed`/parcial; mensaje “muestra, sin inferencia ni media validada de cuenca” | Muestras disponibles; demo requiere UI/captions y handoff reproducible |
| B — serie regional | Gate R aprobado para un producto y ventana especificados | Serie mensual con meses esperados/observados, valor/null, QA, cobertura/denominador, geometría y agregación identificados | No alcanzado |
| C — tendencias históricas | Nivel B + Gate T y protocolo estadístico validado | Pendiente/unidad temporal, IC y p-value/significancia cuando corresponda, diagnóstico y sensibilidad, límites explícitos | No alcanzado; no calcular en FUL-107 |

## Gates de publicación

| Gate | Insumos y comprobaciones concretas | Evidencia de aprobación | Responsable | Estado y faltante |
| --- | --- | --- | --- | --- |
| **D — demo exploratoria** | Original + manifest SHA/tamaño; identificadores de producto/variable/DOI/versión; unidad/tiempo; forma y resolución; total, fill, no finitos y válidos; indicar si QA proveedor se aplicó; declarar “grilla global”, “celda”, “punto” o máscara por centros; si hay geometría, origen/CRS/hash; título/caption con fecha y no representatividad | Registro de lectura repetible y captura/caption que muestra fuente, periodo, unidad, soporte, QA state, faltantes y límite de muestra | Alaín reproducibilidad, César semántica, Alejandra presentación | Parcial; cierre al ejecutar y revisar presentación de la demo |
| **R — serie regional** | Todos los meses de la ventana/cobertura declarada; inventario y manifest por granule; versionado/unidad/calendario; QA por proveedor/fecha; geometry license/hash/CRS; máscara/ponderación escogidas; denominador por mes; porcentaje/área válida; política para mes parcial/faltante; reproducibilidad end-to-end; sensibilidad y comparación independiente | Reporte de 240 estados mensuales; checks por cada producto y periodo; config/versionado; validación independiente de valores y cobertura; acta que aprueba el método para producto/región/ventana | Alaín pipeline, Lucas dictamen científico, César análisis; equipo aprueba | No aprobado; no hay serie procesada ni método aceptado |
| **T — tendencia** | Serie R completa o ventana declarada con regla de suficiencia; estacionalidad/calendario; autocorrelación; faltantes; rupturas/homogeneidad; outliers; hipótesis/método; pendiente/unidad; incertidumbre/IC y p-value si procede; corrección multiplicidad si varias pruebas; sensibilidad de inicio/final y especificación reproducible | Protocolo previo, diagnósticos, resultados reproducibles, incertidumbre y límites, revisión científica independiente; sin causalidad implícita | César + Lucas y revisor del equipo | No aprobado; no existe serie regional ni modelo validado |
| **M — mapas** | Grilla/coords/orientación y CRS; nodata; geometría y transformación; leyenda/unidad/escala; reglas de QA; reproyección/remuestreo adecuado a variable; máscara y versión; para anomalía, baseline explícito; para significancia espacial, dependencia/autocorrelación y multiplicidad | QA raster por muestra/periodo, prueba de alineación, archivo de configuración y leyenda con soporte y limitaciones | Lucas geoespacial/ciencia, Alaín pipeline, Alejandra UI | Solo demo de raster nativo con Gate D; regional/anomalía/significancia bloqueados por R/T |

## Registro de decisiones

El registro detallado, opciones, riesgos, responsables, pruebas pendientes y estado (Proposed/Pending) está en [AZ-03 de `decisions.md`](decisions.md#az-03--definición-del-alcance-científico-inicial-de-anomaly-zero). Ningún elemento se marca Approved. Decisiones mínimas: región; demo/variable; primera serie; terna; horizonte; método espacial; QA; faltantes; visualización; raster; inferencia; campos de contrato.

## Transferencia y compatibilidad FUL-108/UI

### Para Alaín / FUL-108

El contrato debe poder preservar colección, DOI/product ID/version, variable, unidad nativa y conversiones, periodo/calendario, geometría/CRS/hash, soporte espacial y su estado de aprobación/referencia, denominadores/cobertura, conteos faltantes/QA, flags y regla QA versionada, manifest/hash/provenance, snapshot/código de procesamiento, y método/métricas estadísticas nullable. `0` es valor observado; `null` es no disponible/no calculado. La PR #13 abierta ya representa states de disponibilidad, provenance, coverage, quality, transformations, method/metrics y variantes de soporte (`point_sample`, `descriptive_mean`, `regional_aggregate`). Verificar que `approved` requiera referencia aprobatoria verificable y que `unassessed` no se confunda con QA exitoso. Esta observación no modifica ni aprueba PR #13.

### Para Alejandra / UI

Estados propuestos: disponibilidad `available`, `partial`, `no_data`; QA `unassessed`, `partial`, `passed`, `failed` únicamente tras definir criterios; análisis `not_available`, `pending`, `complete`; soporte espacial `point_sample`, `descriptive_mean`, `regional_aggregate` con badge de estado. Mostrar producto/versión, variable/unidad, periodo, fuente, cobertura/denominador, QA y limitaciones cerca del gráfico. No implementar componentes aquí ni comunicar `null` como cero.

### Para Lucas / FUL-110

Solicitar dictamen sobre interpretación/QA de cada colección; priorización de la variable; método espacial por producto; geometría, CRS y sensibilidad; significado de `V07B`/colección `07`; linaje GLDAS 2005; viabilidad de raster y condiciones para mapas derivados. No se duplica ni edita `docs/apoyo-cientifico-az03.md`.

## Backlog científico propuesto (no crear tarjetas aún)

| Trabajo | Entregable/aceptación sugerida | Dependencias | Responsable sugerido | Riesgo |
| --- | --- | --- | --- | --- |
| Ingesta mensual histórica | Estado de 240 meses por producto, archivos/manifests y hashes, control de duplicados, faltantes e idempotencia | Alcance y acceso/licencias aprobados | Alaín | Inventario no garantiza descarga |
| QA por producto/mes | Reglas de fill/flags justificadas, conteos antes/después y sensibilidad temporal | FUL-110, docs oficiales | Lucas + César | Umbral arbitrario y sesgo |
| Normalización espacial | Geometry/CRS/versiones, alineación, prueba de bordes y método elegido | AZ03-D01/D06 | Alaín + Lucas | Pérdida de soporte/señal |
| Serie regional reproducible | Un estado/valor/null por mes con cobertura, QA, provenance y método | Gate R, FUL-108 | Data Science + Backend | Huecos ocultos |
| Snapshots/versionado | Derivado inmutable con hashes y configuración/código identificados | Estrategia de storage | Alaín | No reproducibilidad del resultado |
| Motor estadístico | Implementación posterior de método aprobado y diagnósticos; métricas nullables cuando no se calculan | Serie R + Gate T | César + Lucas | Significancia engañosa |
| Validación de tendencias | Pruebas/sensibilidad, incertidumbre, homogeneidad e informe reproducible | Motor estadístico | César + Lucas | Rupturas y falsos positivos |
| Mapas temporales | Raster/salida cartográfica con nodata, QA, procedencia, CRS y leyenda | Gates R/M; almacenamiento raster | Alaín + Alejandra + Lucas | Resolución aparente y reproyección |

## Limitaciones, aprobación y siguiente paso

- La geometría, las reglas QA, el método espacial, la prioridad del producto y la primera serie siguen **propuestos o pendientes**. Los resultados FUL-104 son sensibilidad de muestras, no consenso metodológico.
- No hay una serie regional de 240 meses, tendencia, p-value, anomalía ni significancia espacial aprobados.
- FUL-110, revisión de Alaín y decisión explícita del equipo son requisitos para pasar de Draft a Ready y considerar cierre de FUL-107. La rama inicial puede documentar evidencia ya integrada sin esperar FUL-110; la conclusión y el merge no deben anticiparse.
- Al publicarse FUL-110: contrastar cada fila con las fuentes, registrar coincidencias/discrepancias, actualizar la recomendación con evidencia, solicitar a Alaín reproducción/contrato y a Alejandra confirmar estados de UI, registrar aprobaciones con autor/fecha/referencia, actualizar Linear y solo entonces solicitar revisión final.

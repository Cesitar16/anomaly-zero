# FUL-107 — alcance científico provisional del MVP

**Estado:** propuesta de alcance contrastada con FUL-110; recomendaciones científicas integradas, pero sin aprobación de equipo. Corte: `origin/dev` `c00a1c75a49b1c66178900ac1329b795080aef85` (PR #18, 15-11-2026). PR #9/#11/#14/#15/#18 integradas. Linear no está conectado en esta sesión; estado de tarjetas y criterios originales no verificados.

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
| QA disponible / aplicado | Fill/missing/finitos inspeccionados; no hay QA flag específico en la muestra ni regla de serie aprobada. No interpretar `1e15` como observación. | Fill/nonfinite revisados; QIm (equivalentes de gauge por caja 2,5°×2,5°), `randomError` (RMS aleatorio) y `gaugeRelativeWeighting` (peso relativo) son diagnósticos; no prueban bias ni se filtraron. | Fill/nonfinite revisados; `cell_methods=time: mean`; QA de proveedor y linaje de máscara de agua pendientes. |
| Cobertura reportada | Enero 2005: 323 centros MDBA, 323 finitos/no-fill; no porcentaje de área | Enero 2005: 10.092/10.092 centros; los doce meses de 2005 mantienen 10.092/10.092, según notebook; denominador es número de centros | Enero 2005: 1.615/1.617 centros finitos/no-fill; dos faltantes. La caja global FUL-105 tiene otro denominador y no es cobertura de cuenca. |
| Área válida dentro de celdas intersectadas (FUL-104 Jan samples) | Ene-2005/2021: 100% del soporte intersectado válido (no cobertura de cuenca completa) | Ene-2005/2021: 100% del soporte intersectado válido (no cobertura de cuenca completa) | Ene-2005/2021: 99,88% del soporte intersectado válido (no cobertura de toda la cuenca) |
| Comparación espacial FUL-104 (centros vs fracción) | Ene-2005: 299,606 vs 299,730 K; ene-2021: 298,538 vs 298,648 K | Ene-2005: 0,037816 vs 0,037790 mm/h; ene-2021: 0,085357 vs 0,085528 mm/h | Ene-2005: 15,904 vs 15,945 kg/m²; ene-2021: 18,719 vs 18,753 kg/m² |
| Estado de evidencia | **PARCIAL** — gránulo NASA abierto y QA básico, no serie regional | **PARCIAL** — doce meses abiertos y panel de 20 centros validado contra grilla; no filtro QA ni serie de 20 años | **PARCIAL** — lectura y muestra espacial; linaje 2005 indeterminado |
| Limitación principal | Reanálisis; no se declara QA flag específico; continuidad/QA regional no revisados | Tasa no es acumulado; `07` y `V07B` identifican colección/archivo distintos; sin filtro QA | No se determinó si enero 2005 incorpora la máscara de aguas MOD44W de 2020; no usar aún en serie final |

**Interpretación correcta de inventarios:** las 240 fechas CMR por producto solo indican granules localizados dentro de un bbox de consulta. No significan 240 descargas, 240 archivos abiertos, valores finitos, valores que superan QA, celdas con cobertura espacial de cuenca, ni una serie regional validada. La Release `be02-samples-2005-v1` distribuye archivos/manifiestos; la copia portable IMERG contiene 240 valores (12 meses × 20 centros), no una muestra representativa de toda el área. Datos originales y geometría permanecen fuera de Git.

## Comparación de alternativas del MVP

| Alternativa | Relevancia y significado | Evidencia / viabilidad | Calidad y dependencias | Visualización y análisis futuro | Recomendación provisional |
| --- | --- | --- | --- | --- | --- |
| Aire a 2 m, MERRA-2 `T2M` | Temperatura del aire, no superficie | Dos granules auténticos ene-2005/2021; colección mensual desde 1980; K; 0,625°×0,5° | Reanálisis; no QA flag específico; continuidad y cobertura regional pendientes | Ruta para primera serie mensual después de Gate R | Candidato provisional de menor fricción según FUL-110; no serie aprobada |
| Precipitación, IMERG Final | Tasa media mensual mm/hr, no total | Grilla 0,1°; muestras auténticas ene-2005/2021 y doce meses 2005 | QIm/error/gauge weighting tienen significados distintos; sin umbral/filtro aprobado; fill y faltantes visibles | Raster nativo de una muestra, con fecha, versión, fuente y advertencia | Demo recomendada por FUL-110; no producto regional aprobado |
| Agua del suelo 0–10 cm, GLDAS Noah | Agua modelada, no observación ni humedad volumétrica | Dos muestras auténticas; 0,25°, kg/m²; EDA 2005 | Re-máscara de agua de 2020 posible, pero no confirma revisión del granule 2005 | Muestra demo con incertidumbre; serie diferida | Candidato retenido; linaje 2005 `INDETERMINADO` según FUL-110 |

**Recomendación científica de Lucas (`INF`) incorporada para decisión:** IMERG para demo raster de una muestra; MERRA-2 `T2M` como camino provisional más defendible a evaluar para primera serie histórica; GLDAS sigue en la terna, pero su muestra 2005 solo sirve como exploración hasta resolver linaje. Son recomendaciones, no selecciones aprobadas por el equipo. Las fuentes no son intercambiables ni necesariamente independientes: difieren en cantidad, resolución y forzantes.

## Región, periodo y agregación espacial

### Región propuesta

Murray–Darling es la región inicial **propuesta** porque la pregunta es de cuenca y la geometría MDBA disponible se reporta como Polygon EPSG:4326, SHA-256 `d36fe31424758cc4fb8eef25e21b835bb5c05c793c746e8a1eb7b5a5841f6a53`. Lucas revisó procedencia, CRS servido/exportado, atribución y caveats; la exportación no identifica CRS/datum original. Alaín debe asegurar acceso/versionado reproducible y confirmar licencia de la geometría exacta. No usar el `LineString` demostrativo como polígono. NSW no es control independiente ni réplica causal.

### Método de soporte

FUL-104 comparó seis granules de enero 2005/2021; FUL-105 usa centros para diagnóstico IMERG. Las medias por centro/fracción son cercanas en esas muestras, pero las celdas y faltantes cambian. El ensayo usó EPSG:3577, no densificó bordes y dedujo bounds MERRA/GLDAS de la resolución nominal; el cierre de área dependió de bounds supuestos/redondeados. No valida geometría, pesos ni cobertura temporal. La media sin ponderar de centros da igual peso a cada celda, no a cada unidad de superficie.

FUL-110 recomienda evaluar primero el **área de intersección fraccional** en proyección apropiada con geometría completa versionada y compararla con centros y área completa. Es recomendación (`INF`), no método aprobado. Matriz para decisión:

| Opción | Qué estima | Qué comprobar antes de aprobar |
| --- | --- | --- |
| Centro dentro del polígono | Estadístico de celdas cuyo centro está dentro; límites excluyen cruces sin centro interior | Resolución/área desigual, bordes, huecos y sensibilidad por producto/mes |
| Intersección | Selecciona celdas que tocan el polígono | Tratamiento de fracción diminuta, duplicidad/topología y pesos efectivos |
| Fracción de área de intersección | Peso por superficie de celda que cae dentro del polígono; candidato preferido a probar | Bounds, datum/operación, CRS de área, topología, densificación, cobertura y faltantes |
| Media sin ponderar | Igual peso por celda seleccionada | Solo descriptiva; sesgo de área si áreas de celdas difieren; denominar soporte y no llamarla media de cuenca |

**Propuesta actualizada:** evaluar fracción-intersección como preferida; conservar centros y área completa como sensibilidades. No crear agregador aquí ni seleccionar método productivo hasta verificar geometría, denominadores y sensibilidad en fechas/estaciones.

### Calendario

Ventana objetivo: enero 2005–diciembre 2024, frecuencia mensual. CMR lista 240 fechas por colección en el bbox, no 240 archivos descargados/abiertos/post-QA ni valores de cuenca. FUL-104/110 reporta granules auténticos enero 2005/2021 de los tres productos; FUL-105 abrió MERRA-2 y GLDAS enero 2005 e IMERG enero–diciembre 2005. No hay serie regional de 240 meses. Para aceptarla se necesitarán manifests/hash, control mensual, versiones/reprocesamiento, calendario/unidad, QA, cobertura, método espacial reproducible y meses excluidos. No convertir missing a cero ni interpolar silenciosamente.

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
| **D — demo exploratoria** | Original + manifest SHA/tamaño; producto/variable/DOI/versión; unidad/tiempo; forma/resolución; conteos total/fill/no finitos/válidos; QA aplicado/no aplicado; soporte espacial; missing visible; geometry fuente/fecha/licencia/CRS si se muestra; sin suavizar/interpolar | Registro reproducible y caption/UI con fuente, mes, unidad, soporte, QA, missing y aviso “muestra, no media/tendencia validada de cuenca”; IMERG como tasa mm/hr | Alaín provenance, César semántica, Alejandra presentación | Parcial: granules existen; publicar solo cuando metadatos y advertencia estén visibles |
| **R — serie regional** | Estado/manifest por cada mes declarado; identity/version/calendar/unit; QA por producto; geometry/CRS/datum/licencia/hash; bounds/pesos reproducibles; `A_valid/A_intersection` y `A_valid/A_basin`; faltantes por causa; cobertura mínima fijada antes de publicar | Reporte mensual completo, reproducibilidad en checkout limpio, sensibilidad a faltantes/método, validación independiente y aprobación para producto/región/ventana | Alaín datos/geometría; Lucas ciencia; César análisis; equipo aprueba | No aprobado; no hay serie regional ni método operativo |
| **T — tendencia** | Serie R completa o ventana declarada con regla de suficiencia; estacionalidad/calendario; autocorrelación; faltantes; rupturas/homogeneidad; outliers; hipótesis/método; pendiente/unidad; incertidumbre/IC y p-value si procede; corrección multiplicidad si varias pruebas; sensibilidad de inicio/final y especificación reproducible | Protocolo previo, diagnósticos, resultados reproducibles, incertidumbre y límites, revisión científica independiente; sin causalidad implícita | César + Lucas y revisor del equipo | No aprobado; no existe serie regional ni modelo validado |
| **M — mapas** | Grilla/coords/orientación y CRS; nodata; geometría y transformación; leyenda/unidad/escala; reglas de QA; reproyección/remuestreo adecuado a variable; máscara y versión; para anomalía, baseline explícito; para significancia espacial, dependencia/autocorrelación y multiplicidad | QA raster por muestra/periodo, prueba de alineación, archivo de configuración y leyenda con soporte y limitaciones | Lucas geoespacial/ciencia, Alaín pipeline, Alejandra UI | Solo demo de raster nativo con Gate D; regional/anomalía/significancia bloqueados por R/T |

## Registro de decisiones

El registro detallado, opciones, riesgos, responsables, pruebas pendientes y estado (Proposed/Pending) está en [AZ-03 de `decisions.md`](decisions.md#az-03--definición-del-alcance-científico-inicial-de-anomaly-zero). Ningún elemento se marca Approved. Decisiones mínimas: región; demo/variable; primera serie; terna; horizonte; método espacial; QA; faltantes; visualización; raster; inferencia; campos de contrato.

## Transferencia y compatibilidad FUL-108/UI

### Para Alaín / FUL-108

El contrato debe poder preservar colección, DOI/product ID/version, variable, unidad nativa y conversiones, periodo/calendario, geometría/CRS/hash, soporte espacial y su estado de aprobación/referencia, denominadores/cobertura, conteos faltantes/QA, flags y regla QA versionada, manifest/hash/provenance, snapshot/código de procesamiento, y método/métricas estadísticas nullable. `0` es valor observado; `null` es no disponible/no calculado. La PR #13 abierta ya representa states de disponibilidad, provenance, coverage, quality, transformations, method/metrics y variantes de soporte (`point_sample`, `descriptive_mean`, `regional_aggregate`). Verificar que `approved` requiera referencia aprobatoria verificable y que `unassessed` no se confunda con QA exitoso. Esta observación no modifica ni aprueba PR #13.

### Para Alejandra / UI

Estados propuestos: disponibilidad `available`, `partial`, `no_data`; QA `unassessed`, `partial`, `passed`, `failed` solo tras definir criterios; análisis `not_available`, `pending`, `complete`; soporte espacial `point_sample`, `descriptive_mean`, `regional_aggregate` con referencia de aprobación. Mostrar producto/versión, variable/unidad, periodo, fuente, QA, faltantes y ambos denominadores de cobertura junto al dato. No implementar UI ni comunicar `null` como cero. Falta confirmar que Alejandra recibió este handoff.

### Concordancia de recomendaciones FUL-110

| Propuesta previa FUL-107 | Evidencia/recomendación de Lucas | Ajuste AZ-03 | Estado |
| --- | --- | --- | --- |
| IMERG para demo por mayor resolución | FUL-110 §§4–5, 9–11 verifica muestras ene-2005/2021; tasa `mm/hr`; QIm equivale a gauges por caja 2,5°×2,5°, `randomError` es RMS aleatorio, `gaugeRelativeWeighting` es peso relativo, no exactitud | Demo raster original con fecha, colección `07`, archivo `V07B`, DOI, unidad, missing y estado QA; sin conversión a acumulado ni descarte automático | Confirmada como recomendación `Proposed`, no aprobación |
| MERRA-2 T2M candidato a serie | FUL-110 §4/§11: aire a 2 m, mensual desde 1980; dos granules inspeccionados; reanálisis, 0,625°×0,5° | Candidato provisional de menor fricción; requiere QA, homogeneidad, cobertura y agregación antes de producir una serie | Confirmada `Proposed`, no serie lista |
| Incertidumbre de GLDAS 2005 | FUL-110 §8 contrasta `history` y aviso MOD44W de 2020; el archivo actual no identifica su revisión de máscara | Dictamen `INDETERMINADO`; demo rotulada posible; diferir serie hasta confirmar con GES DISC/comparación MOD44W | Confirmada `Proposed`; prueba pendiente |
| Murray–Darling y agregación fraccional | FUL-110 §7 respalda la cuenca, recomienda fracción de intersección y expone riesgos de CRS/datum/licencia/bounds | Probar fracción frente a centros/área completa; publicar ambos denominadores; no considerar media de FUL-104 oficial | Recomendación recibida `Proposed`; ingeniería/aprobación pendientes |

FUL-110 está integrada por [PR #18](https://github.com/Cesitar16/anomaly-zero/pull/18). El informe califica sus conclusiones como recomendaciones provisionales; su merge no aprueba AZ-03. No editar [docs/apoyo-cientifico-az03.md](apoyo-cientifico-az03.md).

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

## Criterios de aceptación FUL-107 y conformidades

El texto vigente de Linear no está accesible en esta sesión. Esta matriz se basa en los criterios enumerados en la solicitud y debe cotejarse con la tarjeta antes del cierre. Cumplir el criterio documental no implica aprobación científica ni requiere descargar 240 meses o calcular tendencias; esos son trabajos posteriores.

| Criterio | Evidencia actual | Estado | Bloqueo / responsable |
| --- | --- | --- | --- |
| Pregunta inicial definida, descriptiva/no causal | Pregunta arriba; distingue variabilidad de inferencia | Documentado | Equipo debe aprobar formulación |
| Región justificada con fuente y condiciones | MDBA/Water Act, entidad/fuente, EPSG:4326 hash, licencia y riesgos | Parcial | Alaín confirma procedencia/versionado/licencia; Lucas pertinencia |
| Tres productos: identidad, variable, versión, DOI, unidad, resolución | Matriz ejecutiva y `catalog_mvp.json` | Documentado para muestras | Verificar versiones/lotes en Gate R |
| Ventana objetivo distinta de inventario/archivos/serie válida | 240 CMR se distingue de las muestras realmente inspeccionadas | Documentado | No requiere obtener 240 meses para aprobar alcance |
| EDA FUL-105 incorporado correctamente | IMERG 12 meses, panel 20 centros y límites FUL-104/105 | Documentado | No equivale a cobertura superficial ni serie completa |
| Recomendaciones FUL-110 incorporadas | Matriz de concordancia, QA, geometría, mapas y GLDAS; PR #18 integrada | Documentado (`INF`) | Lucas debe revisar específicamente el acta AZ-03 |
| Demo/serie/tendencia/mapas separados | Niveles A/B/C y gates D/R/T/M | Documentado | La aprobación de gates sigue pendiente |
| Cifras, unidades, denominadores y método coherentes | Muestras ene-2005/2021, centros y área contrastados con FUL-104/110 | Documentado como sensibilidad | Pruebas geométricas/temporales ampliadas pendientes |
| QA y política de faltantes | Fill vs finite vs QA; QIm/randomError/gauge weighting; linaje GLDAS | Documentado con límites | Reglas y cobertura mínima requieren Lucas/equipo |
| Método espacial no aprobado sin pruebas | Fracción-intersección preferida a evaluar; centros/área completa como sensibilidad | Documentado (`Proposed`) | CRS/datum, bounds, densificación y sensibilidad; Lucas/Alaín |
| Viabilidad de mapas clasificada | Muestra raster nativa posible; regional/anomalía/significancia gated | Documentado | UX y aprobación del equipo pendientes |
| Backlog futuro con dependencia/criterios | Tabla de ingesta, QA, geometría, serie, snapshot, análisis y mapas | Documentado | Prioridad/asignación no aprobadas |
| Transferencia a FUL-108/UI | Campos de QA/provenance/coverage/support y estados sugeridos | Documentado como handoff | Alaín/Alejandra deben confirmar recepción/factibilidad |
| Conformidades explícitas verificables | PR #18 integrada pero recomendaciones `INF`; PR #16 sin reviews formales | **Pendiente** | Lucas sobre AZ-03; Alaín sobre contrato/formatos; Alejandra handoff; César/equipo decisión |
| Merge de PR #16 y Done de la tarjeta | Aún no ejecutados | **Pendiente** | Requiere conformidades, CI HEAD final y revisión sin bloqueos |

## Registro de revisores y aprobaciones

| Persona / función | Evidencia actual | Estado |
| --- | --- | --- |
| Lucas — ciencia | PR #18 integrada; informe da recomendaciones, no aprobación AZ-03; sin review formal de PR #16 | Falta conformidad específica al acta |
| Alaín — formatos/procedencia/FUL-108 | PR #13 abierta; no hay revisión de este alcance | Falta revisar formatos, geometría, estados API/QA y compatibilidad |
| César — alcance y decisiones | El agente preparó el borrador por encargo; no se registra como aprobación del titular | Falta conformidad explícita |
| Alejandra — UI | Requisitos escritos; sin evidencia verificable de recepción/comentario | Falta confirmar handoff/impacto UX |

GitHub no registra reviews formales en PR #16 al último chequeo. Linear no está conectado, por lo que no pude verificar si FUL-107 aparece `Done` ni corregir su estado. Si aparece cerrada antes de registrar acuerdos/merge, solicitar moverla a `In Review` o `In Progress` conservando historial; requiere acceso y comprobación.

## Limitaciones, aprobación y siguiente paso

- La geometría, las reglas QA, el método espacial, la prioridad del producto y la primera serie siguen **propuestos o pendientes**. FUL-110 entregó recomendaciones; resultados FUL-104 son sensibilidad de muestras, no consenso metodológico.
- No hay una serie regional de 240 meses, tendencia, p-value, anomalía ni significancia espacial aprobados.
- FUL-110 ya está integrada por PR #18. Falta la conformidad de Lucas sobre el acta AZ-03, revisión técnica de Alaín, recepción UI de Alejandra y conformidad explícita de César/equipo. Hasta tener evidencia, PR #16 permanece Draft y no debe fusionarse.
- Siguiente paso: registrar autor/fecha/alcance/enlace de cada conformidad, cotejar criterios con Linear, sincronizar `dev`, validar CI en el HEAD final y solo entonces pasar la PR a Ready. Si Linear marca FUL-107 Done prematuramente, solicitar corregir a In Review/In Progress preservando historial; no se pudo verificar ni actualizar Linear en esta sesión.

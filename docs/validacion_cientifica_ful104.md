# FUL-104 · Matriz de validación técnico-científica

**Estado:** borrador de trabajo; recomendación provisional, pendiente de revisión de César y Alaín y acuerdo de FUL-107. La consulta de este archivo es una síntesis de la evidencia en [datasets.md](datasets.md), [contraste_fuentes.md](contraste_fuentes.md), [region_murray_darling.md](region_murray_darling.md) y [earthdata-probe.md](earthdata-probe.md), no una nueva validación de todos los archivos.

**Fecha de contraste documental:** 2026-11-14. Las URLs oficiales debajo identifican las fichas/guías usadas; la matriz especifica por separado qué propiedades se confirmaron solo en muestras.

**Fecha de revisión y cálculo espacial local:** 2026-11-15. Se contrastaron los archivos ABS/MDBA ya recuperados en caché y se calculó su intersección como se documenta abajo.

**Acceso:** el 2026-11-15 `earthaccess.login(strategy="netrc")` autenticó correctamente en este equipo. Se descargaron muestras NASA originales de enero de 2005 MERRA-2 e IMERG y de enero de 2021 GLDAS. Los binarios permanecen en `data/raw/nasa/ful104/`, excluidos de Git; no se guardaron credenciales ni URLs firmadas.

**Comparación NASA↔NCAR, enero 2005:** IMERG tiene el mismo SHA-256 en el gránulo NASA y la copia NCAR (`bac3b9bc…c4e73d5`), por tanto son idénticos byte a byte para ese archivo. MERRA-2 tiene SHA distintos porque la copia NCAR contiene la dimensión anual concatenada; al comparar su corte enero con el gránulo NASA, los arrays `T2M` son idénticos (`361×576`, 207.936 valores finitos, diferencia máxima 0 K). Esto verifica igualdad de los campos comparados de enero, no de metadatos, archivo anual completo o meses distintos.

| Fecha/producto | Granule ID CMR / archivo local | Bytes | SHA-256 |
|---|---|---:|---|
| MERRA-2 2005-01 | `G1278025954-GES_DISC` · `MERRA2_300.tavgM_2d_slv_Nx.200501.nc4` | 54.419.597 | `103d95aa3ffe9b8d7e98caea5f6a764831bad3b70155370d3a84c2dfd95616c6` |
| MERRA-2 2021-01 | `G2011583259-GES_DISC` · `MERRA2_400.tavgM_2d_slv_Nx.202101.nc4` | 78.841.049 | `2f1ec2cd12fd0f8e910c23956fc010f942c1cc7bf88454445fd012361fb0244d` |
| IMERG 2005-01 | `G2823464479-GES_DISC` · `3B-MO.MS.MRG.3IMERG.20050101-S000000-E235959.01.V07B.HDF5` | 18.028.945 | `bac3b9bc5ee8cc3eb1e5fe844778d54fd86e2b722813055b37f3872e6e4c73d5` |
| IMERG 2021-01 | `G2829125431-GES_DISC` · `3B-MO.MS.MRG.3IMERG.20210101-S000000-E235959.01.V07B.HDF5` | 18.135.691 | `fd4932244b891beca7d87b61e290df182592d11227d037a4c02069bfd131bf5f` |
| GLDAS 2005-01 | `G1413723174-GES_DISC` · `GLDAS_NOAH025_M.A200501.021.nc4` | 25.075.859 | `5fe42fc81dae292f3be27c3b3460249609a3aa1699532edba25a88fa53b08593` |
| GLDAS 2021-01 | `G2040571257-GES_DISC` · `GLDAS_NOAH025_M.A202101.021.nc4` | 24.908.188 | `4580e2cea40b8f50a13f6438298b09c086037cf0565796ad9763259b5aec4d64` |

Las muestras se recuperaron vía `earthaccess 0.19.0`, `search_data` por shortname/versión/mes/bbox y descarga de un solo granule coincidente; las fechas de adquisición son 2026-11-15 UTC. Los identificadores y checksums permiten volver a verificar los archivos sin guardar las credenciales.

La muestra GLDAS Jan-2005 declara `history=created on date: 2019-10-31T04:18:41.350`; Jan-2021 declara `history=created on date: 2021-04-23T11:19:32.357`. Ambas tienen fill `-9999`, `cell_methods=time: mean` y la misma fracción válida sobre el polígono (99,88 % por área en este análisis). La diferencia de fechas de creación y valores no demuestra qué edición de la máscara de aguas interiores recibió Jan-2005; esa historia queda **indeterminada** con los dos archivos y campos observados. Mantener enero 2005 como muestra de inspección, sin asumirlo válido para agregados finales, hasta que la ficha/archivo confirme el posprocesamiento.

## Estados de evidencia

- **DOC:** ficha o manual de fuente primaria contrastado.
- **TEC:** medición reproducible directa sobre respuesta o archivo identificado.
- **PARCIAL:** prueba técnica con alcance limitado, muestra no integral o procesador/linaje distinto.
- **INF:** interpretación o recomendación que requiere revisión.
- **PEND:** falta prueba o decisión.

Cada estado se aplica a la afirmación de su fila, no al producto completo. Inventario CMR no demuestra que haya píxeles válidos en el polígono.

## Compatibilidad de los candidatos

| Producto y definición | Resolución y formato | Unidad y soporte temporal | Evidencia técnica disponible | Riesgos y pendientes |
|---|---|---|---|---|
| **MERRA-2 `M2TMNXSLV` v5.12.4**, `T2M`: temperatura del aire a 2 m; reanálisis. DOI [10.5067/AP1B0BA5PD2K](https://doi.org/10.5067/AP1B0BA5PD2K); [CMR colección](https://cmr.earthdata.nasa.gov/search/concepts/C1276812859-GES_DISC.umm_json), [metadato CMR de variable](https://cmr.earthdata.nasa.gov/search/concepts/V3188345197-GES_DISC.umm_json). | Mensual; 0,625° lon × 0,5° lat; NetCDF4. | Gránulo NASA confirma K, `_FillValue=missing_value=1e15`, `VersionID=5.12.4`; T2M no es LST. | **DOC/TEC (muestra):** archivo oficial `MERRA2_300.tavgM_2d_slv_Nx.200501.nc4`, grilla 1×361×576, T2M completa en enero; SHA-256 `103d95aa3ffe9b8d7e98caea5f6a764831bad3b70155370d3a84c2dfd95616c6`. La copia se obtuvo vía Earthdata, no se confunde con NCAR. | **PEND:** inspección QA/escala completa y cobertura en polígono para otros meses; interpretar calidad solo con manual/ficha de la colección. |
| **GPM IMERG Final `GPM_3IMERGM` v07**, `Grid/precipitation`: tasa mensual de precipitación. DOI [10.5067/GPM/IMERG/3B-MONTH/07](https://doi.org/10.5067/GPM/IMERG/3B-MONTH/07); [CMR colección](https://cmr.earthdata.nasa.gov/search/concepts/C2723754851-GES_DISC.umm_json), [NASA GPM monthly directory](https://gpm.nasa.gov/data/directory). | Mensual; 0,1° × 0,1°; HDF5. | Gránulo NASA confirma precipitation y randomError en mm/hr, gaugeRelativeWeighting en percent; `_FillValue=-9999.9004` (y -9999 para weighting). | **DOC/TEC:** gránulo NASA `3B-MO.MS.MRG.3IMERG.20050101-S000000-E235959.01.V07B.HDF5`; sha256 `bac3b9bc5ee8cc3eb1e5fe844778d54fd86e2b722813055b37f3872e6e4c73d5`, igual a copia NCAR 200501. Las cuatro capas (`precipitation`, `randomError`, `gaugeRelativeWeighting`, `precipitationQualityIndex`) contienen 6.425.329 valores finitos no-fill en grilla global. `precipitation` varía 0–2,331 mm/h; `randomError` 0,001–0,264 mm/h; weighting 0–100 %. | **PEND:** revisión de QA conforme al manual (no inferir umbral del rango), máscara de cuenca y más fechas; la igualdad de checksum solo autentica identidad binaria de esta muestra, no todas las copias o meses. |
| **GLDAS Noah `GLDAS_NOAH025_M` v2.1**, `SoilMoi0_10cm_inst`: humedad/agua modelada en capa 0–10 cm. DOI [10.5067/SXAVCZFAQLNO](https://doi.org/10.5067/SXAVCZFAQLNO). | Mensual; 0,25° × 0,25°; NetCDF4. | Muestra declara kg m⁻², `_FillValue=-9999`, `cell_methods=time: mean`; `_inst` nombra el tipo de campo, no significa que el mensual sea una lectura instantánea. No convertir a porcentaje sin modelo de espesor/densidad apropiado. | **DOC/TEC:** muestra NASA enero 2005 y enero 2021 descargadas autenticadamente; ambas son NetCDF4, grilla 1×600×1440, con atributos esperados. SHA-256 de 2005 `5fe42fc81dae292f3be27c3b3460249609a3aa1699532edba25a88fa53b08593`; de 2021 `4580e2cea40b8f50a13f6438298b09c086037cf0565796ad9763259b5aec4d64`. En ambos, caja rectangular: 3.045/3.360 valores finitos no-fill (90,625 %). | **PEND:** la muestra 2021 no resuelve el linaje/posprocesamiento de la muestra histórica 2005; faltan QA, faltantes y cobertura en varias fechas, y máscara de cuenca. No es medición directa ni humedad volumétrica. |

La fuente de las características de GLDAS-2.1 incluye [NASA LDAS](https://ldas.gsfc.nasa.gov/gldas/dataset), que informa 0,25°/1° y frecuencia mensual/3-horaria; la ficha de [especificaciones GLDAS](https://ldas.gsfc.nasa.gov/gldas/specifications) describe la estructura de capas de Noah. El detalle observado en la muestra prevalece para describir esa muestra, no toda la serie.

## Ventana, territorio y uso espacial

**Inventario, no cobertura válida:** consultas CMR documentadas encontraron 240 meses por colección entre 2005-01 y 2024-12 dentro del bbox 138°–153° E, 38°–24° S. Esto prueba registros de catálogo que intersectan la caja. No demuestra descarga, píxeles válidos, continuidad dentro del polígono ni calidad del agregado.

**Geometría candidata:** el límite publicado por MDBA corresponde a la definición de la cuenca bajo Water Act 2007 y su ficha en la [MDBA Library](https://library.mdba.gov.au/data_product/https-mdba-maps-arcgis-com-home-item-html-id-ba731d77d80947fbbcbf7524364372ff-overview) indica licencia Creative Commons Attribution. La documentación local registra servicio, exportación a EPSG:4326, procedencia y advertencias. El GeoJSON versionado es solo un segmento de línea, no el polígono completo. Confirmar la ficha/licencia vigentes al reutilizar el límite.

**Contraste separado NSW vs cuenca:** NSW es un estado de Australia y la cuenca Murray–Darling es una cuenca hidrográfica definida legalmente; sus significados y límites no son equivalentes. El límite MDBA (derivado de Australia’s River Basins 1997) se extiende por NSW y otros estados/territorios, por lo que NSW solapa solo parcialmente y tampoco es un control independiente. Se intersectaron el ZIP de [límites ABS ASGS 2026](https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-4-july-2026-june-2031/access-and-downloads/digital-boundary-files/STE_2026_AUST_SHP_GDA2020.zip) (252 partes; EPSG:7844) y el GeoJSON MDBA de caché (EPSG:4326), reproyectados a EPSG:3577 (GDA94 / Australian Albers). Shapely 2.2.0 reportó geometrías e intersección válidas. El área de intersección calculada es **597.895,38 km²**, aproximadamente **74,66 % del área de NSW** y **56,48 % del área de la cuenca** calculadas en esta misma proyección. Son resultados del overlay de los archivos recuperados, no cifras oficiales: la geometría MDBA es una salida ArcGIS convertida a EPSG:4326 y la transformación a GDA94 implica cambio de datum/operación de coordenadas. Antes de tratar esos porcentajes como medición de publicación, validar datum/precisión y densificación del límite. El metadato ABS reporta área 800.797,7073 km², cercano al área proyectada calculada de 800.797,71 km². El XML del ZIP enlaza licencia CC BY-SA 4.0; revisar compatibilidad con términos generales ABS y atribución antes de redistribuir. Para análisis, elegir una sola máscara y no etiquetar NSW como región de control.

La extensión de los productos permite estudiar la cuenca, pero las celdas tienen resoluciones distintas. Los ensayos documentados de IMERG enero 2005 comparan centros, celdas intersectadas y pesos de área; muestran sensibilidad a bordes para una fecha y no aprueban una máscara ni método productivo.

**Recomendación geográfica provisional (INF):** mantener la cuenca completa como territorio candidato porque es el objeto del caso, y probar un agregado ponderado por fracción de área de celda en una rejilla de igual área, con faltantes explícitos y análisis de sensibilidad frente a centros/celdas completas. No fijar esa regla hasta revisar el polígono íntegro, datum/transformación, QA y más de una fecha. No tratar NSW como control.

### Reproducción espacial en muestras NASA

El script [auditar_espacial_ful104.py](../research/auditar_espacial_ful104.py) leyó las seis muestras NASA locales (enero 2005 y enero 2021 por producto) y produjo el resumen regenerable `data/cache/ful104/spatial_audit.json` (ignorado por Git). El cálculo usa intersecciones de cajas de celda con el polígono en EPSG:3577; MERRA-2/GLDAS no declaran límites de celda en estos archivos y sus bounds se infieren desde la grilla nominal. No se densifican lados al reproyectar.

| Producto / mes | Celdas intersectadas | Centros dentro (válidos) | Intersección/fracción (válidas) | Área de intersección con valor válido | Media centros | Media por fracción de área |
|---|---:|---:|---:|---:|---:|---:|
| IMERG 2005-01 | 10.467 | 10.092 (10.092) | 10.467 (10.467) | 100 % | 0,037816 mm/h | 0,037790 mm/h |
| IMERG 2021-01 | 10.467 | 10.092 (10.092) | 10.467 (10.467) | 100 % | 0,085357 mm/h | 0,085528 mm/h |
| MERRA-2 2005-01 | 384 | 323 (323) | 384 (384) | 100 % | 299,606 K | 299,730 K |
| MERRA-2 2021-01 | 384 | 323 (323) | 384 (384) | 100 % | 298,538 K | 298,648 K |
| GLDAS 2005-01 | 1.756 | 1.617 (1.615) | 1.756 (1.749) | 99,88 % | 15,904 kg/m² | 15,945 kg/m² |
| GLDAS 2021-01 | 1.756 | 1.617 (1.615) | 1.756 (1.749) | 99,88 % | 18,719 kg/m² | 18,753 kg/m² |

Las diferencias entre medias de centro y fraccional son pequeñas en estas muestras, pero el conteo de celdas y los dos faltantes GLDAS muestran que la máscara/ponderación altera la población incluida. No se aplicó filtro QA de producto: “válido” aquí significa finito y distinto del fill. No se debe interpretar esta tabla como promedio oficial ni como demostración de continuidad en otros meses. Para producción falta validar la geometría y transformación (incluida densificación), interpretar flags QA, estudiar faltantes y repetir con más fechas representativas. El JSON también conserva rangos de campos auxiliares de IMERG; estos no implican umbrales de aceptación.

## Visualizaciones, comparabilidad y recomendación provisional

| Salida | Requisito de datos | Estado actual |
|---|---|---|
| Timeline raster mensual | Grilla y coordenadas por período; versión y calendario estables. | **DOC/PARCIAL:** los tres son productos gridded y hay inventario mensual; la inspección de todos los gránulos/meses no está hecha. No implica que cada mes tenga píxeles válidos sobre la cuenca. |
| Serie promedio del polígono | Grilla más geometría completa, pesos de área, máscara QA y política de faltantes. | **PEND:** hay ensayo de una fecha IMERG, no serie validada ni estimación oficial de cuenca. |
| Mapa de anomalía | Serie temporal homogénea, baseline y definición de anomalía aprobadas. | **PEND:** no calcular dentro de FUL-104. |
| Mapa de pendiente/significancia por celda | Serie larga homogénea y método estadístico, multiplicidad y autocorrelación tratados. | **Fuera de alcance:** corresponde a análisis posterior, no a recomendar a partir de una muestra. |

**Recomendación provisional por variable (INF):**

| Variable de interés | Principal provisional | Respaldo | Motivo / condición |
|---|---|---|---|
| Temperatura del aire a 2 m | MERRA-2 `T2M` | Ninguno aprobado. MOD11C3 es LST, no un sustituto equivalente. | Coincide con el constructo requerido y tiene resolución mensual; las muestras originales NASA de enero 2005/2021 ya se inspeccionaron. Faltan reglas QA/linaje acordadas y validación de cobertura para una serie regional. |
| Precipitación | IMERG Final V07 `precipitation` | Ninguno aprobado. GLDAS precipitación sería modelada y no intercambiable sin comparar definición y sesgos. | Es el candidato de mayor resolución y las muestras originales NASA de enero 2005/2021 ya se inspeccionaron. Sus campos QA auxiliares están inventariados, pero sus reglas aún no se interpretan ni aplican; también faltan validación independiente y reprocesamiento espacial defendible. Para una primera demo raster es el candidato operativo, condicionado a esos controles. |
| Agua del suelo 0–10 cm | GLDAS Noah 2.1 `SoilMoi0_10cm_inst` | Ninguno aprobado. SMAP observado/modelado tiene distinta profundidad, época de inicio y semántica. | Es el único candidato actual de la terna para esa capa y tiene una muestra auténtica; resolver linaje 2005, QA y máscara antes de seleccionarlo para serie. |

No proponer un respaldo entre productos distintos solo para completar una casilla: las alternativas listadas no son equivalentes. La recomendación principal es provisional, no una selección aprobada.

Las rejillas no tienen la misma resolución. Cualquier comparación futura exige una grilla objetivo acordada, remuestreo conservador para precipitación/agua y tratamiento explícito para temperatura; no se debe fingir equivalencia ni independencia. IMERG incorpora información/referencias vinculadas a modelos atmosféricos, por lo que la terna no debe presentarse como tres observaciones independientes.

## Paquete de transferencia

**Para Alaín / FUL-106:** las muestras NASA originales de enero 2005/2021 están inspeccionadas por Lucas y los checksums/atributos observados figuran arriba; reproducir sus lecturas desde manifiestos/gránulos y compartir rutas de acceso reproducibles, sin añadir binarios ni secretos al repo. El bbox solo descubre archivos y no recorta. Para MERRA-2 confirmar `T2M` y unidad; para IMERG confirmar grupo/campo, unidades y QA; para GLDAS registrar `SoilMoi0_10cm_inst`, dimensión/capa, agregación y linaje del procesamiento.

**Para César / FUL-105:** preservar unidades originales y transformaciones; distinguir T2M de LST, tasa mm/h de acumulado mensual y kg m⁻² de contenido volumétrico; explicitar límites del piloto GLDAS de un mes y la caja rectangular. No derivar tendencia, significancia o causalidad de una muestra.

## Decisiones y vacíos que bloquean el cierre

1. Completar la interpretación científica de QA/manuales para MERRA-2 e IMERG y decidir si se necesitan más fechas; las muestras originales NASA de enero 2005 y 2021 ya se abrieron y describieron, pero aún no se acordó/aplicó un filtro QA.
2. Confirmar tratamiento/linaje de GLDAS 2005 frente al posprocesamiento NASA de aguas interiores; una muestra de enero 2021 no basta para establecerlo.
3. Validar datum/precisión/transformación de las geometrías y sensibilidad del overlay NSW–cuenca; cerrar el análisis de método espacial en más de una fecha/resolución y resolver licencia/atribución NSW antes de redistribuir.
4. Obtener revisión explícita de Alaín (IDs/formatos) y César (semántica/unidades), y registrar selección provisional/acuerdo en FUL-107.
5. Confirmar términos de uso y atribución de cada entrega antes de redistribuir datos o derivados.

La evidencia y limitaciones de Work siguen referenciadas desde `revision_work.md`; no se requiere esperar el ZIP ausente. El estado de esta matriz no cambia el estado de Linear ni marca FUL-104 como Done.

## Checklist FUL-104

- [x] Fichas NASA específicas enlazadas con shortname, versión, variable, unidad, DOI y fecha de comprobación; los campos no confirmados en producto auténtico están señalados.
- [x] Ventana enero 2005–diciembre 2024 etiquetada como inventario de 240 meses, no como cobertura válida de píxeles.
- [x] Fuente oficial de geometría MDBA, CRS de salida, atribución/licencia declarada y limitación del fragmento versionado documentados.
- [x] Contraste NSW separado: geometrías oficiales identificadas e intersección calculada con método y métricas provisionales; queda revisar datum/precisión y términos antes de publicación.
- [x] Comparar bordes y agregaciones por centro/fracción de área en dos fechas y rejillas de los tres productos; el script y sus datos/limitaciones están documentados. La regla productiva aún requiere revisión de CRS/QA.
- [x] Recomendar provisionalmente cuenca completa por el objetivo del caso y ponderación de fracción de área como candidata, con faltantes explícitos; decisión final sujeta a validación/revisión humana.
- [x] Recomendación principal provisional y razón documentadas por variable; respaldos no equivalentes quedan sin aprobar.
- [x] Abrir muestras NASA originales MERRA-2 e IMERG de enero 2005 y verificar estructura, variables/unidades, atributos básicos, checksum y disponibilidad de grilla; QA científico completo y más fechas siguen pendientes.
- [x] Revisar linaje/posprocesamiento GLDAS con muestras NASA de enero 2005 y enero 2021, atributos `history` y documentación; conclusión: el procesamiento histórico específico de enero 2005 no se puede determinar con evidencia actual y por eso queda fuera de cualquier aprobación final.
- [x] Disponibilidad de grilla temporal diferenciada de promedio regional; timeline documentado como viable en principio, sujeto a validación de gránulos.
- [ ] Obtener revisión explícita de Alaín (IDs/acceso/formato) y César (unidades/interpretación) y registrar sus comentarios.
- [ ] Incorporar acuerdo provisional de selección y enlace al entregable en FUL-107.
- [x] Hallazgos etiquetados DOC/TEC/PARCIAL/INF/PEND y comprobaciones técnicas existentes descritas con fecha, método y límites.
- [x] Registrar fuentes, condiciones de uso encontradas y atribución necesaria. Como persiste una ambigüedad de licencia ABS para NSW, la decisión operativa es solo enlazar la fuente y no redistribuir geometría NSW ni derivados hasta aclaración del titular.

### Bloqueos y preparación para completar

- Las muestras enero 2005 MERRA-2/IMERG y enero 2021 GLDAS se descargaron tras autenticar con Earthdata Login. No se deben compartir credenciales en Linear, chat ni Git.
- El overlay NSW–cuenca se reproduce como parte del script sobre los archivos ABS/MDBA locales; aún falta sensibilidad de las áreas a datum, densificación y precisión geométrica, por lo que el porcentaje se mantiene como resultado reproducible provisional, no cifra oficial.
- La sensibilidad de muestra ya se comparó para enero de 2005 y enero de 2021 en las tres resoluciones; no representa otros meses/estaciones ni valida una serie. Antes de aprobar una máscara operativa faltan análisis QA, meses/estaciones adicionales, datum/transformación y revisión científica del método.
- Las revisiones de Alaín y César y la aprobación en FUL-107 son dependencias humanas. La matriz puede preparar preguntas y propuesta, pero no registrar respuesta o acuerdo hasta recibirlos.
- Para licencia, la política operativa conservadora es mantener los datos NASA y ABS fuera del repositorio, conservar DOI/cita y provenance, y enlazar las fuentes. La página ABS vigente declara CC BY 4.0 por defecto salvo indicación distinta; el XML del ZIP específico localizado en Work declara CC BY-SA 4.0. Hasta confirmar cuál se aplica al archivo exacto, el repositorio enlaza la fuente y no redistribuye el ZIP NSW ni derivados. NASA GPM publica su cita y declara sus datos de misión disponibles para el público; para MERRA-2/GLDAS mantener cita DOI y condiciones `UseConstraints` de CMR sin afirmar una licencia CC específica que no aparece en esos metadatos. Véanse [ABS digital boundaries](https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-4-july-2026-june-2031/access-and-downloads/digital-boundary-files) y [NASA GPM data directory](https://gpm.nasa.gov/data/directory).

Este checklist audita documentación y trabajo de FUL-104; no actualiza por sí mismo las casillas de Linear. Los elementos marcados `[x]` son cumplimientos documentales acotados, no aprobación científica final de los productos.

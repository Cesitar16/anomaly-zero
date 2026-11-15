# FUL-110 — Apoyo científico a FUL-107: QA NASA, método espacial y recomendación de MVP

**Estado:** recomendación científica provisional para revisión de César y del equipo; no aprueba el MVP, una máscara final ni una serie regional.
**Responsable de FUL-110:** Lucas Moncada. **Tarjeta de decisión:** [FUL-107](https://linear.app/fullstack-track/issue/FUL-107), a cargo de César Rojas.
**Consulta de fuentes y archivos:** 2026-11-15.
**Rama de trabajo:** `feature/ful-110-apoyo-cientifico-az03-lucas`, creada desde `origin/dev` en `b51ca0617a96d582e0239d661c00647da2a32e11`.

## 1. Resumen ejecutivo científico

FUL-104, FUL-105 y FUL-106 dejaron una base suficiente para decidir qué evidencia debe preceder al primer MVP, pero no para declarar una serie regional 2005–2024 validada. Están inspeccionados gránulos auténticos NASA de enero de 2005 y enero de 2021 para MERRA-2, IMERG Final y GLDAS Noah 2.1. También hay doce archivos IMERG de 2005 y un panel EDA de hasta 20 centros de grilla por mes. Eso es distinto de tener 240 meses por producto descargados, con QA, agregados para toda la cuenca y validados.

**Recomendación para decisión de equipo:**

- Para una **primera demo raster acotada**, IMERG Final mensual `Grid/precipitation` ofrece la rejilla más detallada (0,1°) y las muestras originales de enero de 2005 y 2021 están verificadas. Mostrar el valor mensual como tasa media (`mm/hr`), mes y versión; mostrar faltantes por separado. No presentarlo como precipitación acumulada mensual, lluvia observada en cada punto ni anomalía validada.
- Para el **camino inicial más defendible hacia una serie mensual histórica**, MERRA-2 `T2M` es la opción provisional de menor fricción científica dentro de la terna: colección mensual desde 1980, T2M directamente representa aire a 2 m, y dos gránulos auténticos fueron inspeccionados. Su resolución es más gruesa (0,625° × 0,5°), es reanálisis y no se ha validado una agregación de cuenca ni su consistencia temporal regional. Esta preferencia no equivale a selección o aprobación de FUL-107.
- **GLDAS Noah 2.1 `SoilMoi0_10cm_inst`** es el candidato directamente pertinente para el estado del agua en la capa de suelo 0–10 cm, pero la máscara/edición de la muestra de enero de 2005 no se puede identificar de manera concluyente con la evidencia de archivo disponible. Puede mostrarse como muestra exploratoria etiquetada; postergar su uso en la serie final hasta resolver el linaje.
- El método espacial preferible para evaluar en una futura serie es el promedio ponderado por **área de intersección de cada celda con el polígono completo**, con la geometría y las celdas en un CRS/proyección equivalente, pesos versionados, denominador de cobertura válida informado y sensibilidad frente al método por centros. Es una recomendación de método, no una máscara aprobada. Los ensayos actuales usaron una geometría/proyección y límites de grilla con supuestos que aún afectan la precisión.
- No publicar todavía anomalías regionales, tendencias, significancia, ni un mapa raster derivado como “resultado de cuenca”. El notebook EDA de FUL-105 no tiene salidas ejecutadas/versionadas en `dev`; sus resultados numéricos están escritos en documentos y CSV del handoff, y la verificación local depende de cachés ignoradas.

La mayor evidencia nueva para la decisión no es una media puntual, sino la delimitación exacta de lo que sí se comprobó: versión/atributos y hashes de muestras, diferencia entre QA y validez numérica, sensibilidad de método en dos meses, y la incertidumbre específica del archivo GLDAS 2005.

## 2. Objetivo, límites y estado de integración

Esta nota proporciona evidencia y opciones para que César resuelva en FUL-107 región, producto, pregunta de investigación, ventana y salidas iniciales. No edita `docs/decisions.md` ni `docs/alcance-cientifico-provisional.md`, no implementa el pipeline, no fija la máscara final y no marca FUL-107 como Done.

Se consultó el HEAD actual de `origin/dev` y el estado remoto de las PR citadas. Las PR **#9 (FUL-106), #11 (FUL-105), #14 (FUL-104) y #15 (correcciones de FUL-104) están MERGED hacia `dev`**; los documentos de referencia que todavía dicen “Draft”, “sin integrar” o que no se abrieron los originales reflejan estados anteriores. La evidencia técnica actual sobre originales prevalece: MERRA-2 e IMERG de enero 2005 y 2021 se documentan en FUL-104; GLDAS auténtico de ambas fechas también.

### Niveles de evidencia usados

| Código | Alcance aplicado aquí |
|---|---|
| `DOC` | Definición/regla indicada por documentación primaria oficial, identificada por enlace y fecha de consulta. |
| `TEC` | Atributo, estructura, checksum o cálculo observado sobre archivo/respuesta identificados. |
| `PARCIAL` | Muestra, fecha, subconjunto, cálculo con supuesto geométrico o prueba reproducible que no caracteriza todo el producto/periodo. |
| `INF` | Interpretación/recomendación condicionada, no hecho observado ni decisión de equipo. |
| `PEND` | Falta evidencia específica, validación o aprobación. |

Una afirmación puede ser `DOC` en su definición y `PARCIAL` en la aplicación al proyecto. “Valor finito y distinto del fill” significa que pasó una prueba estructural, no que sea físicamente correcto o adecuado para un análisis.

## 3. Metodología de comprobación

1. Leí la descripción y criterios completos de [FUL-110](https://linear.app/fullstack-track/issue/FUL-110) antes de preparar el entregable y revisé la relación con FUL-107.
2. Actualicé referencias Git con `git fetch origin`, confirmé `origin/dev` (`b51ca061…`) y que el checkout no tenía cambios locales; no existía rama previa FUL-110. Creé una rama de esta tarjeta desde ese `dev`.
3. Revisé los entregables científicos nombrados en la tarjeta, con foco en `docs/validacion_cientifica_ful104.md`, `docs/datasets.md`, `docs/catalog_mvp.json`, `docs/contraste_fuentes.md`, `docs/region_murray_darling.md`, `docs/ful-105-plan-inferencia.md`, `docs/be-02-sample-workflow.md`, el notebook y el script/pruebas de auditoría espacial.
4. Consulté directamente los seis archivos NASA que FUL-104 registra en `data/raw/nasa/ful104/` (rutas ignoradas por Git) mediante sus atributos HDF5/NetCDF sin aplicar escala ni offset. Los nombres, bytes, SHA-256 e identificadores CMR están en FUL-104; los atributos citados abajo se observaron directamente. Las cifras agregadas espaciales se toman de la auditoría de FUL-104, no se recalcularon con otra geometría.
5. Contrapuse definiciones, resoluciones, DOI, intervalos, QA y reprocesamiento con fichas/manuales oficiales NASA/GES DISC y fuentes oficiales de geometría. Consulté los enlaces el 2026-11-15 salvo donde se indique fecha en la fuente.
6. Traté las comparaciones de 2005/2021 como análisis de sensibilidad de muestras. No descargué décadas nuevas, no estimé tendencias y no generé promedios finales.

### Matriz de evidencia y afirmación → método → limitación → consecuencia

| Afirmación | Fuente/fecha | Método y evidencia | Limitación/interpretación | Consecuencia MVP | Estado |
|---|---|---|---|---|---|
| Las muestras nativas MERRA-2 e IMERG de 2005 y 2021 existen y abren como grillas esperadas. | NASA CMR + gránulos locales; FUL-104, adquisición 2026-11-15. | SHA-256/bytes/CMR IDs consignados en §5; lectura de atributos y formas en HDF5/NetCDF. | Dos meses por producto; no prueba 240 meses ni continuidad regional. | Permite demo etiquetada de esos meses y prueba de lector, no una serie. `TEC/PARCIAL` |
| La copia IMERG NASA enero 2005 coincide byte a byte con la copia NCAR citada en FUL-104; la porción MERRA T2M del mismo mes coincide numéricamente con NCAR. | FUL-104, 2026-11-15. | SHA idéntico IMERG; para MERRA, arrays T2M 361×576, 207.936 valores finitos y diferencia máxima 0 K. | Solo esa fecha/campo; la copia anual NCAR tiene otro envoltorio/metadata. | Confirma identidad/comparabilidad de la muestra, no de otros meses ni QA. `TEC/PARCIAL` |
| Los inventarios CMR 2005–2024 reflejan registros de catálogo, no observaciones regionales válidas. | FUL-104/105; consultas de catálogo anteriores. | Conteo de 240 registros mensuales en caja/bbox. | No descarga, valores, cobertura de cuenca, filtro QA ni serie regional. | No anunciar “240 meses completos” como dataset listo. `DOC/TEC/PARCIAL` |
| Selección por centro y fracción de área dan resultados cercanos en enero de 2005/2021, pero cambian celdas y faltantes. | `docs/validacion_cientifica_ful104.md`, prueba 2026-11-15. | Comparación espacial de los seis gránulos; §7 incluye conteos/medias exactos. | Geometría/proyección, grilla y topología con limitaciones; dos fechas de enero, no sensibilidad estacional. | Conservar resultados como referencia; hacer prueba geométrica/temporal antes de producción. `PARCIAL` |
| La muestra GLDAS 2005 declara creación 2019 y la de 2021 creación 2021; NASA describe posprocesamiento de aguas en octubre de 2020. | Atributos de dos archivos + aviso oficial GES DISC de 2020, consultado 2026-11-15. | `history` y metadata comparados; aviso recomienda redescargar datos pre-nov-2020. | El `history` no dice si el archivo histórico fue reescrito; CMR `ProductionDateTime` 2020 no prueba aplicación por celda/versión. `PARCIAL`. | No excluirlo de toda demo, pero no usarlo como base de una serie final sin comprobar su máscara. `PEND` |
| QIm mensual no es una probabilidad ni una métrica de sesgo total. | ATBD NASA IMERG V07, versión documento 2026-08-13, §3.12.2/9.5; consultado 2026-11-15. | Interpretación como número equivalente de pluviómetros por caja 2,5°×2,5°; el ATBD dice que aborda error aleatorio, no sesgo. | Valores por píxel 0,1° representan una métrica cuyo soporte conceptual es mucho más grueso; clases stoplight son descriptivas. | Exponer QIm como contexto; no descartar píxeles con un umbral arbitrario. `DOC` |
| La atribución/licencia del límite MDBA y de los límites NSW no debe inferirse de una sola licencia general. | MDBA ArcGIS item / ABS ASGS Edition 4 consultados 2026-11-15; documentos locales. | La ficha MDBA declara CC BY 4.0; ABS indica CC BY 4.0 por defecto; el XML del ZIP NSW inspeccionado por FUL-104 indica CC BY-SA 4.0. | Ficha MDBA no pudo abrirse ahora desde el navegador (403), aunque el item ArcGIS y copia se documentaron localmente. El ZIP exacto y sus metadatos deben revisarse para redistribución. | Usar geometría fuente con cita/versionado, no incluir ZIP/derivados ambiguos en publicación sin resolver licencia. `DOC/PARCIAL/PEND` |

## 4. Comparativa científica de productos

| Candidato | Fuente, identificador, versión y DOI | Variable/definición; frecuencia, resolución y unidad | Archivos auténticos inspeccionados | Ventajas para MVP y serie | Limitaciones, continuidad y riesgos de inferencia |
|---|---|---|---|---|---|
| **MERRA-2** | NASA GMAO/GES DISC; `M2TMNXSLV`, versión 5.12.4; [DOI 10.5067/AP1B0BA5PD2K](https://doi.org/10.5067/AP1B0BA5PD2K). | `T2M`: temperatura del aire a 2 m; colección de medias mensuales temporales; global 0,625° lon × 0,5° lat; K. NetCDF4. | `MERRA2_300.tavgM_2d_slv_Nx.200501.nc4` (CMR `G1278025954-GES_DISC`) y `MERRA2_400.tavgM_2d_slv_Nx.202101.nc4` (`G2011583259-GES_DISC`). Ambos atributo `VersionID=5.12.4`; jan-2005 T2M coincide con enero de copia NCAR. | Construcción física directa de la variable, mensual y cobertura que permite una ventana 2005–2024; comparación de 2005/21 disponible. Sirve para anomalía térmica después de verificar climatología, homogeneidad y agregación. | Es reanálisis (modelo + asimilación de observaciones), no observación directa; rejilla más gruesa; campo mensual sin bandera QA específica declarada en estos metadatos. `T2M` no es temperatura superficial terrestre (`LST`). Revisar relleno, discontinuidades, revisión/reprocesamiento y validación regional independiente. |
| **IMERG Final** | NASA GPM/GES DISC; `GPM_3IMERGM`, versión de colección `07`; DOI [10.5067/GPM/IMERG/3B-MONTH/07](https://doi.org/10.5067/GPM/IMERG/3B-MONTH/07). Gránulo inspeccionado marca versión de archivo `V07B`. | `Grid/precipitation`: estimación combinada satélite–pluviómetro de precipitación mensual, expresada como tasa media en mm/hr; mensual Final; grilla 0,1° × 0,1°; HDF5 compatible con NetCDF4. | `3B-MO.MS.MRG.3IMERG.20050101-S000000-E235959.01.V07B.HDF5` (`G2823464479-GES_DISC`) y equivalente 2021-01 (`G2829125431-GES_DISC`). Los hashes están en §6. Enero 2005 coincide byte a byte con la copia NCAR verificada. | Mayor detalle espacial de la terna; apropiado para una demo raster de una muestra y para lluvia mensual una vez QA/espacio estén acordados. La serie de 12 meses IMERG 2005 facilita una prueba temporal limitada. | La tasa `mm/hr` no es acumulado; conversión requiere horas exactas del intervalo calendario y una regla de datos faltantes. Final incorpora gauge analysis y tiene latencia. `randomError` y QIm solo describen error aleatorio/calidad según alcance del ATBD, no sesgo. Las versiones/sensores y reprocesamientos deben mantenerse consistentes; no llamar “observaciones independientes” a tres productos. |
| **GLDAS Noah 2.1** | NASA LDAS/GES DISC; `GLDAS_NOAH025_M.2.1`, versión 2.1; DOI [10.5067/SXAVCZFAQLNO](https://doi.org/10.5067/SXAVCZFAQLNO). | `SoilMoi0_10cm_inst`: humedad/almacenamiento de agua modelado en capa de suelo 0–10 cm; mensual, 0,25° × 0,25°, kg m⁻²; NetCDF4. En la muestra `cell_methods=time: mean`. | `GLDAS_NOAH025_M.A200501.021.nc4` (`G1413723174-GES_DISC`) y `GLDAS_NOAH025_M.A202101.021.nc4` (`G2040571257-GES_DISC`). Atributos `history` 2019-10-31 y 2021-04-23, respectivamente. | Tiene significado cercano a un estado del suelo asociado a sequía, y ofrece cobertura mensual desde 2000; es el candidato de la terna para capa de 0–10 cm. | Producto terrestre/modelado, sin variable directa de agua disponible para plantas; NASA especifica que GLDAS-2.1 no asimila variables. La re-máscara de agua interior de 2020 hace incierto el linaje específico del archivo 2005. `kg m⁻²` no es porcentaje de saturación ni contenido volumétrico sin supuestos/parametrización. |

### Cobertura de catálogo y calendario observado

Las fechas siguientes describen la cobertura publicada de la colección consultada, no meses que hayamos descargado o validado. Las colecciones siguen activas y sus extremos pueden cambiar; se registran la institución y la consulta para que el período sea reproducible.

| Producto | Cobertura espacial y período publicado al consultar | Consulta/fuente del período | Calendario y semántica temporal de la muestra inspeccionada |
|---|---|---|---|
| MERRA-2 `M2TMNXSLV` 5.12.4 | Global, longitud −180° a 180°, latitud −90° a 90°; catálogo indica enero de 1980–presente. Media mensual de diagnósticos temporales. | Ficha NASA GES DISC en NASA Open Data, metadata actualizada 2026-11-05; consultada 2026-11-15: [M2TMNXSLV](https://catalog.data.gov/dataset/merra-2-tavgm_2d_slv_nx-2dmonthly-meantime-averagedsingle-levelassimilationsingle-level-di). | Las muestras usan `time` con unidades minutos desde las 00:30 UTC del primer día, incremento mensual de 60.000 minutos y `begin_date=YYYY0101`; no exponen atributo `calendar`. No inferimos un calendario distinto a partir de su omisión. La semántica mensual procede de la colección `tavgM`. |
| IMERG Final `GPM_3IMERGM` colección 07 / archivo V07B | Global, −180° a 180° y −90° a 90°; las fuentes oficiales consultadas no coinciden en el inicio publicado: la ficha GES DISC indica junio de 2000–presente y la página NASA GPM de V07B indica enero de 1998–presente. Ambas cubren la ventana objetivo 2005–2024. | Ficha NASA GES DISC en NASA Open Data, revisada 2026-11-05, y [NASA GPM Data Directory](https://gpm.nasa.gov/data/directory), consultado 2026-11-15. Mantener visible la discrepancia hasta comprobar el registro CMR/versiones para cualquier fecha anterior a junio de 2000. | `Grid/time` declara calendario `julian`, segundos desde `1980-01-06 00:00:00 UTC`, bounds y tiempo representativo mensual; el LongName advierte que el cálculo no suma leap seconds. No sustituir este atributo por una conversión de calendario asumida sin probarla. |
| GLDAS Noah 2.1 `GLDAS_NOAH025_M` | Global; NASA LDAS indica período 2000–presente, rejillas de 0,25° y 1°, frecuencia mensual y 3-horaria para la familia. El granule seleccionado aquí es el producto mensual Noah de 0,25°. | [NASA LDAS Dataset](https://ldas.gsfc.nasa.gov/gldas/dataset), consultado 2026-11-15. | Enero 2005 declara `calendar=standard`, días desde `2000-01-01`; enero 2021 no declara `calendar` y expone `time_increment=one month`, `begin_date=20210101`, `end_date=20210131`, `end_time=210000`. Tratar el atributo ausente como una limitación de metadata de esa muestra y validar con los bounds al leer, no como prueba de otro calendario. |

**Lectura para FUL-107:** la ventana 2005-01–2024-12 queda dentro de los períodos publicados de las tres colecciones al momento de consulta; esto solo acredita elegibilidad temporal de catálogo. El inventario de 240 registros citado abajo sigue sin acreditar 240 archivos descargados ni valores válidos. Para IMERG, no usar la diferencia de cobertura anterior a 2000 como una certeza resuelta: queda registrada como discrepancia documental que no afecta la ventana objetivo.

### Inventario, descargas, valores y series: cuatro estados distintos

- **Inventario:** en la ventana/caja consultada constan 240 meses por candidato. Es un resultado de CMR; no prueba integridad de los pixels.
- **Archivos descargados:** las muestras listadas arriba y los 12 gránulos IMERG de 2005 del handoff tienen archivos/manifiestos locales identificados. Sus binarios y cachés están ignorados por Git.
- **Valores válidos:** depende de variable, tipo, `_FillValue`, finitud, QA y región. Para IMERG 2005 global, 6.425.329/6.480.000 valores de `precipitation` fueron finitos/no-fill; para GLDAS fueron 242.753/864.000 y para MERRA enero 2005 207.936/207.936. Conteos globales no son cobertura regional.
- **Serie regional validada:** no existe todavía. FUL-105 tiene doce meses IMERG 2005, máscaras por centros y un panel de 20 centros idénticos (240 filas); sin filtro QA, sin fracción de área y sin representar la cuenca completa. No hay serie regional de 240 meses ni tendencia validada.

### Alternativas comparables que podrían cambiar la selección

Estas son alternativas para un estudio comparativo posterior, no productos inspeccionados en FUL-110:

- **Temperatura del aire:** ERA5 mensual single levels, Copernicus C3S, DOI [10.24381/cds.f17050d7](https://doi.org/10.24381/cds.f17050d7), con `2m_temperature`, registro desde 1940 y rejilla reanálisis 0,25°. Es una comparación independiente de NASA útil para robustez; tampoco es estación observada y tiene su propia política/versionado.
- **Precipitación:** GPCP mensual de satélite + pluviómetros es una referencia potencial de largo periodo, pero la versión mensual global habitual es mucho más gruesa que IMERG. Puede servir para plausibilidad a gran escala, no resolver bordes de Murray–Darling.
- **Humedad de suelo:** SMAP L4 9 km asimila brillo de temperatura SMAP a un modelo, desde 2015; profundidad/semántica y época no son equivalentes a GLDAS 0–10 cm ni cubren 2005. Sirve para contraste moderno, no sustituye sin más la ventana completa.
- Cualquier alternativa exige comparar definición física, periodo, datum, máscara, unidades, QA, versiones y dependencia entre forzantes/productos antes de llamarla validación independiente.

### Respuestas provisionales a las decisiones de producto

| Pregunta | Recomendación FUL-110 (`INF`, revisión pendiente) |
|---|---|
| Mejor para la primera demostración técnica | IMERG Final `precipitation` si la demo es un raster de una muestra mensual y la interfaz preserva `mm/hr`, fecha, versión, fill y carácter estimado. Para una serie regional, no está listo. |
| Camino más defendible hacia una serie regional | MERRA-2 `T2M` como primer candidato de la terna, por constructo directo, resolución temporal mensual y cobertura desde 1980; después evaluar ERA5 como comparación. La agregación regional, continuidad de producción, QA y cobertura deben pasar puertas antes de anunciar una serie. |
| Primera visualización raster razonable | IMERG enero 2005/2021 permite mostrar patrón espacial con 0,1°; MERRA-2/GLDAS son raster válido para explicar distintas variables pero de resolución más gruesa. No interpolar para hacer parecer más detalle. |
| Riesgo dominante | MERRA-2: no inferir error desde la ausencia de flag QA; IMERG: QA/fill y tasa vs acumulado; GLDAS: máscara de agua/linaje 2005 y significado de variable modelada. Todos: límites, áreas, versión y cobertura. |
| Evidencia que cambiaría la recomendación | Resultado de validación independiente regional; disponibilidad/continuidad y revisión de calidad de todos los meses 2005–2024; análisis de cambio de versión; QA/rendimiento comparativo; máscara/linaje GLDAS 2005 resueltos; geometría MDBA versionada, exacta y con licencia clara; pruebas de sensibilidad espacial y temporal. |

## 5. QA: semántica, atributos y reglas

El manual no da licencia para llamar “bueno” a todo valor no-fill. Se distinguen expresamente: **cero físico** (si el dominio lo admite), **faltante** (ausencia semántica), **fill** (código de almacenamiento), **valor numéricamente válido** (finito/no-fill/rango estructural), **supera QA** (pasa una regla aprobada y documentada) y **apto para una inferencia concreta** (además de QA, definición, cobertura, escala y supuestos adecuados). Ninguna categoría implica automáticamente la siguiente.

| Producto | Variable o atributo | Fuente | Unidad | Fill/missing observado | Criterio QA (documentado/propuesto) | Evidencia | Estado | Riesgo | Recomendación |
|---|---|---|---|---|---|---|---|---|---|
| IMERG | `Grid/precipitation` | ATBD V07 NASA §3.13; granules 2005/2021 | `mm/hr` | En los dos granules `_FillValue` float32 `-9999.9`; el valor representable observado es `-9999.900390625`; `CodeMissingValue=-9999.9`. | Leer con fill del archivo/tipo nativo antes de estadística; finito/no-fill es solo validez de almacenamiento. Cero no se reemplaza ni se elimina por ser cero. Proposed QA: evaluar junto con campos auxiliares y evaluación externa, sin regla numérica aprobada. | HDF5 auténtico, `DimensionNames=time,lon,lat`; LongName “Merged microwave-infrared-gauge precipitation estimate”. | `DOC/TEC/PARCIAL` | Comparar float32 con literal Python/float64 puede no detectar fill; conversión errada a mm acumulados puede cambiar significado. | Preservar tasa/unidad y raw fill; convertir acumulado solo con período exacto y regla de cobertura aprobada. |
| IMERG | `Grid/randomError` | ATBD V07 NASA §3.12.2, tabla 5 | `mm/hr` | `_FillValue` float32 `-9999.9` (representado `-9999.900390625`); `CodeMissingValue=-9999.9`. | Campo de estimación de error aleatorio de precipitación combinada. Reportar/resumir distribución contra precipitación y tiempo; no inferir error sistemático ni utilizar un umbral como filtro sin validación y aprobación. | `LongName`: RMS error estimate for merged microwave-infrared-gauge precipitation. | `DOC/TEC/PARCIAL` | `randomError` no contiene sesgo total, error por validación de estación ni intervalo de confianza automático. | Mostrar como diagnóstico de contexto; filtrar solo tras experimento y decisión explícita. |
| IMERG | `Grid/gaugeRelativeWeighting` | ATBD V07 NASA tabla 5 | `percent` | `_FillValue=-9999` (`int16`), `CodeMissingValue=-9999`. Rango en muestras descrito como 0–100% salvo missing. | Cuantifica ponderación de gauge respecto del campo multisatélite en la combinación; es diagnóstico de contribución, no “porcentaje correcto” ni sustituto de independencia. No se propone corte. | HDF5 authentic 2005/2021, `LongName` exacto de ponderación relativa. | `DOC/TEC/PARCIAL` | Interpretar valor alto como garantía de exactitud o independencia sería incorrecto. | Conservarlo para análisis de procedencia/estratificación; sin umbral de descarte. |
| IMERG | `Grid/precipitationQualityIndex` (QIm mensual) | ATBD NASA V07, §3.12.2, apéndice 9.5, documento 2026-08-13 | Sin unidad física; número equivalente de gauges por área de referencia | `_FillValue` float32 `-9999.9`; `CodeMissingValue=-9999.9`; atributo `Units` ausente en granules consultados. | NASA define QIm como equivalente de gauges por caja 2,5° × 2,5°; aborda error aleatorio, no bias. V07 da grupos descriptivos: `<3` red, `3–<10` yellow, `≥10` green; son clases de contexto de densidad de red, elegidas por distribución razonable, no umbrales obligatorios de enmascarado. Su aplicación a píxeles 0,1° requiere cautela. | HDF5 auténtico tiene variable y fill; ATBD interpreta QIm y alerta sobre superficie congelada/ambigüedad. | `DOC/TEC/PARCIAL` | Confundirlo con QI semihorario (0–1) o probabilidad; usar cortes por pixel puede crear patrón/selección espacial y sesgo muestral. | Etiquetar como “índice/calidad mensual (equivalentes de pluviómetros)” y evaluar clases; FUL-107 debe aprobar cualquier efecto de filtro. |
| MERRA-2 | `T2M` | Ficha NASA GES DISC + atributos de muestra | `K` | `_FillValue`, `missing_value`, `fmissing_value` observados como float32 `1e15` (valor representado `999999986991104`); `valid_range` amplio `[-1e15,1e15]`. Sin `scale_factor`/`add_offset` en archivos inspeccionados. | Aplicar primero missing/fill/non-finite; el `valid_range` de archivo incluye el fill límite y no es un umbral físico útil. No inventar bandera QA ni cortes meteorológicos; comprobar unidades, rango plausible contextualizado, consistencia temporal y diferencias contra una fuente independiente. | Gránulos auténticos, dimensiones 1×361×576, `VersionID=5.12.4`, unidades K, long name `2-meter_air_temperature`. | `DOC/TEC/PARCIAL` | Tratar `1e15` como temperatura válida; convertir a °C antes de enmascarar; confundir aire con LST o interpretar un reanálisis como observación. | Enmascarar fill crudo primero; preservar K fuente y registrar cualquier transformación. No hay QA flag declarado por esta muestra/colección. |
| GLDAS | `SoilMoi0_10cm_inst` | NASA GLDAS-2 README, tablas Noah y §3; atributos muestras 2005/2021 | `kg m-2` | Ambos archivos: `_FillValue=-9999`, `missing_value=-9999`; en muestra 2021 `scale_factor=1`, `add_offset=0`; en muestra 2005 estos atributos no constan. | `cell_methods=time: mean`; `_inst` identifica campo tipo instantáneo en datos subhorarios, pero el archivo mensual declara media temporal. Enmascarar fill y evaluar cobertura/agua; no aplicar valores de `vmin/vmax` como filtro científico sin semántica/documentación. | `standard_name=soil_moisture_content`, `long_name=Soil moisture`; Noah capa 0–10 cm y 0.25°. | `DOC/TEC/PARCIAL` | Llamarlo humedad observada o porcentaje; asumir `_inst` significa que el archivo mensual es snapshot; ocultar agua/lagunas como cero. | Mantener kg m⁻² y tipo modelado; probar máscara/cobertura. No pasar a porcentaje/saturación sin datos de profundidad, porosidad y parámetros. |
| GLDAS | Máscara de agua/valores en masas de agua | Aviso GES DISC NASA Oct-2020; muestra GLDAS Jan2005 | N/A | NASA dice que antes algunos píxeles de agua interior fueron tratados como tierra y tenían valores no missing; el postprocesamiento posterior los enmascara. | Regla oficial de archivo: archivos descargados antes de nov-2020 deben volver a descargarse. Para esta copia, verificar a nivel de muestra con máscara MOD44W vigente/correspondiente y con original anterior/postprocesamiento o confirmación GES DISC. | `history` enero 2005 2019-10-31; enero 2021 2021-04-23; gránulo 2005 descargado del archivo oficial en 2026, sin atributo que marque explícitamente water-mask revision. | `DOC/PARCIAL/PEND` | Una muestra aparentemente numérica de río/lago puede inflar humedad regional; los metadatos no permiten asignar la política exacta a la fecha 2005. | Dictamen indeterminado; no aceptar la fecha 2005 para promedio final hasta validar. |

**Comparación robusta de fill:** el valor de `_FillValue` debe leerse como tipo nativo del dataset. Para un arreglo `float32`, castear el sentinel al mismo dtype antes de comparar igualdad, por ejemplo `sentinel = np.asarray(attr, dtype=data.dtype)` y luego comparar el raw array. El número decimal Python `-9999.9` convertido a `float64` no es representable exactamente como el float32 del archivo (`-9999.900390625`); la igualdad cruzada puede dar falso negativo. Si se usa tolerancia, documentar tolerancia y comprobar que no pueda incluir valores científicos válidos. Preferir el decoder CF/HDF5 compatible cuando se necesite aplicar máscara automática, conservando el raw fill y verificando atributos `CodeMissingValue` también.

**QA para publicación:** no hay un filtro global NASA llamado para estas tres variables. En el informe no se introducen cortes de plausibilidad ni porcentaje de cobertura arbitrarios. Proponer y aprobar reglas separadas por producto/uso; registrar como parámetros versionados, describir impacto por mes y área, y publicar cobertura junto al valor. Una disponibilidad aparente de valores dentro de la cuenca no confirma precisión.

## 6. Identidad y estructura de muestras

Los hashes/dimensiones proceden de la inspección técnica consignada por FUL-104/106. No se han incorporado datos binarios a la rama. La colección y la versión del archivo se informan por separado para IMERG.

| Producto/mes | Granule ID | Archivo original | Bytes | SHA-256 |
|---|---|---|---:|---|
| MERRA-2 2005-01 | `G1278025954-GES_DISC` | `MERRA2_300.tavgM_2d_slv_Nx.200501.nc4` | 54.419.597 | `103d95aa3ffe9b8d7e98caea5f6a764831bad3b70155370d3a84c2dfd95616c6` |
| MERRA-2 2021-01 | `G2011583259-GES_DISC` | `MERRA2_400.tavgM_2d_slv_Nx.202101.nc4` | 78.841.049 | `2f1ec2cd12fd0f8e910c23956fc010f942c1cc7bf88454445fd012361fb0244d` |
| IMERG 2005-01 | `G2823464479-GES_DISC` | `3B-MO.MS.MRG.3IMERG.20050101-S000000-E235959.01.V07B.HDF5` | 18.028.945 | `bac3b9bc5ee8cc3eb1e5fe844778d54fd86e2b722813055b37f3872e6e4c73d5` |
| IMERG 2021-01 | `G2829125431-GES_DISC` | `3B-MO.MS.MRG.3IMERG.20210101-S000000-E235959.01.V07B.HDF5` | 18.135.691 | `fd4932244b891beca7d87b61e290df182592d11227d037a4c02069bfd131bf5f` |
| GLDAS 2005-01 | `G1413723174-GES_DISC` | `GLDAS_NOAH025_M.A200501.021.nc4` | 25.075.859 | `5fe42fc81dae292f3be27c3b3460249609a3aa1699532edba25a88fa53b08593` |
| GLDAS 2021-01 | `G2040571257-GES_DISC` | `GLDAS_NOAH025_M.A202101.021.nc4` | 24.908.188 | `4580e2cea40b8f50a13f6438298b09c086037cf0565796ad9763259b5aec4d64` |

Archivos MERRA-2 y GLDAS: `time,lat,lon`; IMERG: grupo `Grid`, ejes `time,lon,lat`. Rejillas: MERRA 1×361×576; GLDAS 1×600×1440; IMERG 1×3600×1800. Son granules originales autenticados, no solo metadatos CMR ni una serie completa.

## 7. Murray–Darling: geometría, licencia y agregación

### Geometría y licencia

- **Territorio:** cuenca hidrográfica definida en la ficha “Murray–Darling Basin Boundary as defined in Section 4(1) of the Water Act 2007”. El ítem ArcGIS identifica a MDBA como publicador; atribuye la fuente al departamento federal DCCEEW y describe derivación desde *Australia’s River Basins 1997*, con procesamiento posterior departamental. El ítem fue modificado el 2026-01-14; ese timestamp no es la fecha de creación de la geometría. Fuente consultada por FUL-104: [ítem ArcGIS MDBA](https://www.arcgis.com/sharing/rest/content/items/ba731d77d80947fbbcbf7524364372ff?f=json), [FeatureServer capa 0](https://services8.arcgis.com/5xxEi7I2m6ml97fE/arcgis/rest/services/boundary_gdb/FeatureServer/0), [entrada MDBA Library](https://library.mdba.gov.au/data_product/https-mdba-maps-arcgis-com-home-item-html-id-ba731d77d80947fbbcbf7524364372ff-overview). La respuesta anterior archivada del servicio en EPSG:4326 tenía SHA-256 `d36fe31424758cc4fb8eef25e21b835bb5c05c793c746e8a1eb7b5a5841f6a53`; caché ignorada, no evidencia persistente en el repo.
- El servicio anuncia extensión WKID 102100/3857 y permite pedir `outSR=4326`. Eso no prueba cuál fue el CRS/datum de la fuente original ni resuelve transformación. La versión almacenada y su CRS deben quedar explícitos por FUL-107/implementación posterior.
- La ficha del item indica CC BY 4.0, lo que requiere atribución de datos y cambios; confirmar vigencia en la fuente al crear cualquier redistribución. El ABS publica la excepción general CC BY 4.0 para digital boundaries ASGS 2026; en el ZIP NSW exacto revisado por FUL-104 el XML ISO declaró CC BY-SA 4.0. Son fuentes/archivos distintos. Mientras el permiso del derivado combinado no se resuelva, enlazar fuentes, atribuir cambios y no versionar el ZIP ABS ni publicar geometrías derivadas como si tuvieran una sola licencia.
- NSW es límite administrativo y cubre solo parte de la cuenca. La intersección calculada con las geometrías de muestra fue 597.895,38 km²: 74,66% del área NSW y 56,48% del área MDBA según el mismo overlay en EPSG:3577. Son cifras calculadas, no superficies oficiales ni fundamento para tratar NSW como control independiente.
- El archivo `examples/murray_darling_boundary_segment.geojson` del repositorio es una línea de 12 vértices, no el polígono completo, y no puede usarse como máscara o área.

### Qué dicen los ensayos FUL-104

El script `research/auditar_espacial_ful104.py` usó las seis muestras, caja de celda × polígono en EPSG:3577, no densificó bordes y dedujo bounds de MERRA/GLDAS desde la grilla nominal. Resultados de enero:

| Producto/mes | Centros dentro: celdas (válidas) | Intersección: celdas (válidas) | Media por centros iguales | Media ponderada por fracción de área |
|---|---:|---:|---:|---:|
| IMERG 2005-01 | 10.092 (10.092) | 10.467 (10.467) | 0,037816 mm/hr | 0,037790 mm/hr |
| IMERG 2021-01 | 10.092 (10.092) | 10.467 (10.467) | 0,085357 mm/hr | 0,085528 mm/hr |
| MERRA-2 2005-01 | 323 (323) | 384 (384) | 299,606 K | 299,730 K |
| MERRA-2 2021-01 | 323 (323) | 384 (384) | 298,538 K | 298,648 K |
| GLDAS 2005-01 | 1.617 (1.615) | 1.756 (1.749) | 15,904 kg/m² | 15,945 kg/m² |
| GLDAS 2021-01 | 1.617 (1.615) | 1.756 (1.749) | 18,719 kg/m² | 18,753 kg/m² |

Las medias de `intersección` en la tabla usan las áreas de intersección según informe FUL-104, no el promedio de celdas completas que meramente tocan la cuenca. GLDAS tuvo 99,88% de cobertura válida del área intersectada en estas muestras; esto no es cobertura garantizada mes a mes. FUL-105 seleccionó centros para su EDA, conservando explícitamente `quality_filter_applied=False`.

### Evaluación de métodos y sensibilidad

| Método | Qué estima/ventaja | Riesgo en esta cuenca y decisión sugerida |
|---|---|---|
| Centro de celda dentro | Más sencillo, reproducible y próximo a EDA FUL-105; no corta polígonos. | Excluye celdas limítrofes con centro fuera; población y área cambian con resolución. Útil como línea base de sensibilidad, no asumir representatividad. |
| Toda celda que intersecta | Conserva todas las celdas con soporte dentro del polígono; no pierde una celda tocada. | Si la celda completa recibe peso, incorpora área exterior; bordes/huecos pueden introducir sesgo. No usar como promedio de cuenca salvo que la pregunta sea “celdas que tocan”. |
| Área completa de celda como peso | Compensa diferencia área física de celdas lat/lon por latitud, según áreas de celdas. | No corrige cuánto de la celda cae fuera del polígono. No confundir con fracción-intersección. |
| Fracción de área de intersección | Asigna peso solo a área de celda dentro de cuenca; método más interpretable para una media espacial de la superficie delimitada, en principio. | Depende de celdas correctas, topología, datum, proyección, bordes densificados y máscara de faltantes. Si se normaliza solo por área válida puede ocultar baja cobertura. Candidato preferido a probar, pendiente de validación. |
| Media sin ponderar | Resumen de celdas seleccionadas con peso igual. | En latitud/longitud representa celdas con tamaño físico variable; punto medio cerca de Murray-Darling no corrige área ni distribución de celdas de borde. Reportar como sensibilidad, no media area-representativa por defecto. |
| Ponderación por superficie de intersección | Estadístico interpretable como integral espacial sobre porción cubierta, con denominador explícito. | Requiere definir cobertura: `A_valida/A_total_cuenca` y, por separado, `A_valida/A_intersectada`. No rellenar huecos con 0 ni expandir una media válida a toda la cuenca silenciosamente. |

**Riesgos geométricos identificados:** celdas que solo tocan borde; 747 celdas IMERG parcialmente intersectadas en la muestra de enero 2005 (375 con centro exterior, 372 interior); agujeros/bordes deben respetar predicados topológicos; lat/lon no equivale a área; resoluciones nativas distintas; cambio CRS/datum puede desplazar fronteras; límite MDBA se sirve como 3857 pero se pidió 4326; ABS NSW era GDA2020 (EPSG:7844) y el ensayo empleó EPSG:3577 GDA94; bounds MERRA/GLDAS fueron inferidos; los límites IMERG float32 se redondearon a 0,01° en ensayo posterior; no se densificaron bordes. En el ensayo inicial las áreas parciales sumaban ~48 km² más que el área del polígono (0,0046%); con límites redondeados al nominal, EPSG:3577 cerró casi exactamente, pero ese cierre es interno al supuesto y **no demuestra exactitud** ni justifica el redondeo para producción.

**Recomendación provisional de método:** mantener cuenca MDBA completa como región objeto; probar overlay fraccional con geometría integral versionada y CRS/datum conocido, bounds de celda oficiales o reconstruidos de forma comprobable, geodesia/densificación y conservación de área. Calcular cobertura válida total y por soporte disponible. Compararlo al menos con centros y área completa en fechas de distintas estaciones/años en los tres productos y documentar efecto de faltantes/QA. FUL-104 cubre enero 2005 y enero 2021, no cumple esa amplitud. FUL-107 debe seleccionar el método provisional para el prototipo; aprobación operativa depende de dichas pruebas/revisión.

### Métricas mínimas que deberá emitir el futuro pipeline espacial

Para que dos agregados regionales puedan compararse y auditarse, cada fila producto-mes deberá guardar, con CRS, regla QA y método explícitos:

| Métrica | Definición/denominador obligatorio |
|---|---|
| `n_centers_inside` | Número de centros de celda dentro del polígono con la regla topológica documentada; no usarlo como denominador de área. |
| `n_cells_intersecting`, `n_cells_partial`, `n_cells_full` | Celdas con área de intersección positiva, y su desglose parcial/completo; declarar si “touch-only” (contacto de área cero) se excluye. |
| `n_valid`, `n_fill`, `n_missing`, `n_qa_rejected` | Conteo dentro de celdas seleccionadas, separado por causa. `n_valid` significa pasa el fill/finito y la regla QA aplicada; si no hay regla, marcar `QA_NOT_APPLIED`, no equiparar válido-numérico con QA aprobado. |
| `A_basin` | Área del polígono de cuenca en el CRS de área de análisis, medida una vez y versionada. |
| `A_intersection` | Suma de áreas de intersección de las celdas de la grilla con la cuenca; la cobertura espacial del soporte del producto debe informarse respecto a `A_basin`. |
| `A_valid` | Suma de pesos/áreas de intersección de celdas que pasan la validez y la regla QA declarada. |
| `coverage_intersection = A_valid / A_intersection` | Fracción del soporte cubierto por la grilla que queda válida. Denominador: superficie intersectada, no toda la cuenca. |
| `coverage_basin = A_valid / A_basin` | Fracción de la superficie completa de cuenca efectivamente respaldada por valores válidos. Este denominador incluye sectores fuera del soporte de grilla y no debe sustituirse por `A_intersection`. |
| `regional_mean` | `sum(value_i × area_intersection_i) / A_valid`; publicar solo con `A_valid`, ambas coberturas y política de faltantes, sin imputar missing a cero ni expandir la media a área no cubierta. |
| Identidad reproducible | Shortname, colección y versión de archivo, mes, granule ID, manifest/hash del archivo, hash del polígono y de la máscara/pesos, URL/fuente, fecha de consulta y unidades. |
| Contrato espacial y QA | CRS/datum de entrada de geometría y grilla, CRS proyectado para área, operación de transformación identificada, origen/convención de cell bounds, método (`center`, `intersects`, `fractional_area`), versión de pesos y regla QA; flags/estados por separado para fill, no finito, QA fail y QA no aplicado. |

Estas variables son un **requisito recomendado de trazabilidad**, no un pipeline implementado en FUL-110 ni umbrales de aceptación aprobados. Los porcentajes deben publicar siempre numerador y denominador; reportar solo “% válido” no basta.

## 8. GLDAS 2005: dictamen de linaje

### Pregunta

¿Hay evidencia suficiente para identificar el procesamiento histórico y la máscara de aguas continentales aplicada al gránulo GLDAS Noah 2.1 de enero de 2005?

### Evidencia observada y documentación

1. La muestra auténtica `GLDAS_NOAH025_M.A200501.021.nc4`, CMR `G1413723174-GES_DISC`, presenta `history = created on date: 2019-10-31T04:18:41.350`, `_FillValue=-9999`, `cell_methods=time: mean` y `SoilMoi0_10cm_inst` `kg m-2`.
2. Muestra `GLDAS_NOAH025_M.A202101.021.nc4`, CMR `G2040571257-GES_DISC`, presenta `history = created on date: 2021-04-23T11:19:32.357`; también declara `_FillValue=-9999` y `cell_methods=time: mean`. Atributos de llenado/escalado difieren parcialmente (2021 declara scale 1/offset 0), pero la fecha de `history` no es un identificador de edición de la máscara.
3. NASA GES DISC anunció que en octubre de 2020 se posprocesaron todas las salidas GLDAS-2 mensuales y de 3 horas con máscara MOD44W; antes, algunos píxeles de agua interior aparecían como tierra y con valores. El posproceso enmascaró la salida del modelo sobre agua interior, no alteró los campos de forzamiento. El aviso indicó volver a descargar archivos obtenidos antes de noviembre de 2020.
4. Esta copia 2005 se descargó del archivo autenticado en 2026 y su nombre/CMR/granule/hash se verificaron, lo que respalda que es la copia actualmente servida. Sin embargo, el archivo no registra `mask_revision`, checksum de publicación de la revisión, metadata que lo marque como reescrito, ni se comparó con un archivo anterior a la re-máscara. `history` 2019 registra creación histórica, no necesariamente el momento del postprocesamiento. El `ProductionDateTime` CMR citado por FUL-104 tampoco es prueba inequívoca del contenido de cada celda.

### Dictamen: **INDETERMINADO** (`DOC/PARCIAL/PEND`)

La documentación de NASA hace **probable** que una descarga actual de la colección incluya la corrección, pero no es evidencia específica suficiente para identificar la máscara y la edición exactas aplicadas al granule de enero 2005 inspeccionado. No se puede afirmar que el archivo esté sin procesar ni que esté confirmado como procesado. La diferencia frente a `history` de 2021 obliga a conservar esta incertidumbre, no a asumir linaje idéntico.

- **Qué no se concluye:** no se atribuye la presencia/ausencia de los valores de agua a una edición concreta de MOD44W; no se certifica homogeneidad en 2005–2024; no se valida todo GLDAS Noah 2.1.
- **Consecuencia para MVP:** se puede usar el granule 2005 en demo exploratoria, con aviso de incertidumbre y sin convertirlo en evidencia de tendencia/serie. Posponer GLDAS como candidato de serie final hasta cerrar validación del archivo y sensibilidad de la máscara.
- **Prueba que podría resolverlo:** solicitar a GES DISC el identificador/revision checksum por granule y confirmar que CMR `G1413723174-GES_DISC` se reemplazó conforme al aviso; comparar bytes/píxeles interiores de agua con la edición archivada antes del 2020 o un inventario de versiones; cruzar el raster de fill/no-fill del archivo actual con la máscara MOD44W aplicable y cuantificar superficie/cambios. El mero hecho de que píxeles de agua sean missing ahora apoyaría máscara, pero sería insuficiente para probar la versión histórica sin datum/máscara correctos.

## 9. Viabilidad de las visualizaciones

| Visualización/uso | Categoría | Evidencia y límites | Condición para publicar |
|---|---|---|---|
| Muestra mensual como mapa raster original IMERG, enero 2005 o 2021 | **Viable como demo con datos inspeccionados** | Hay dos gránulos auténticos con hashes, unidad, versión, axes/fill verificados. Solo muestra y raw grid; el reporte no la declara máscara final de cuenca ni medida independiente validada. | Rótulo dataset/versión/mes, unidad de tasa mm/hr; leyenda y missing diferenciados; no interpolar ni llenar missing como cero; atribución DOI/fuente; mostrar límite con licencia. |
| Mapa de una variable MERRA o GLDAS de enero 2005/2021 | **Viable como demo de muestra, con cautelas específicas** | Estructura validada; GLDAS 2005 tiene linaje/agua indeterminado, MERRA es reanálisis. | Indicar modelado/reanálisis y mes; mantener K/kg m⁻²; en GLDAS 2005 advertencia visible; missing visible. |
| Comparación de medias regionales de muestra por centro vs fracción | **Viable como diagnóstico de investigación**, no indicador de cuenca validado | Hay resultados en dos fechas para tres rejillas; geometría/método aún provisional. | Etiquetar explícitamente “ensayo de sensibilidad”, incluir fecha, máscara, método, coverage y limitaciones; no mostrar como KPI científico. |
| Serie regional mensual 2005–2024 | **Viable en principio, condicionado a pruebas** | Inventario de 240 meses, pero faltan gránulos verificados, reglas QA, método espacial acordado y resultado regional completo. | Pasar gate B (§10) para cada variable; no unir vacíos por interpolación silenciosa. |
| Raster mensual de 240 meses | **Viable en principio, condicionado a nuevas pruebas** | Hay muestras originales y formatos conocidos, no se comprobó proceso completo de 240 meses por producto; faltan consistencia de versión/QA/máscara y cobertura. | Validar identidad/atributos por lote; registrar QA/flags/fecha; reproyección/resampling físico documentado; preservar fuente/fill. |
| Mapa de anomalía mensual raster | **Pendiente de investigación** | No existe baseline revisado/validado ni serie gridded QA para años completos; no se calculó anomalía aprobada. | Climatología de referencia versionada y por mes/calendario, mínimo de observaciones/cobertura acordado, procedimiento para valores faltantes, independencia del baseline y etiquetas de incertidumbre. |
| Tendencia regional, pendiente, IC y significancia | **Fase posterior** | No se estimó tendencia; no hay una serie regional apta ni hipótesis aprobada. | Gate C (§10); predefinir pregunta, intervalo, autocorrelación, estacionalidad, discontinuidades y sensibilidad antes de observar resultado. |
| Mapa de tendencia/significancia por píxel | **Fase posterior** | Ningún raster histórico evaluado para inferencia; problema de multiplicidad espacial y autocorrelación. | Gate D (§10); tamaño temporal, máscara estable, prueba/corrección espacial, incertidumbre y cobertura. No colorear p-valores como magnitud de anomalía. |

## 10. Criterios científicos propuestos para publicar

Son gates recomendados (`INF`) para discutir; no son política aprobada del equipo.

### A. Demo exploratoria

- Identificar producto, colección, versión de colección **y** archivo, DOI, mes, unidad original, variable, fuente y checksum.
- Identificar si el contenido es estimación satelital, reanálisis o salida de un modelo; no llamarlo “observación local” si es un grid estimate/model state.
- Enmascarar `_FillValue`/`CodeMissingValue` y NaN usando tipo nativo; preservar cero; mostrar missing con transparencia/color separado.
- Publicar raster en grilla original o describir remuestreo; no suavizar para fingir resolución; incluir geometría como límite de referencia con fuente/fecha/licencia.
- Etiquetar como muestra/mes; decir expresamente qué QA no se aplicó y si el área mostrada es cuenca o bbox.
- En GLDAS 2005, declarar linaje de agua indeterminado. En IMERG, presentar `precipitation` en tasa; campos QIm/error como contexto sin umbral automático.

### B. Serie regional mensual

- Confirmar colección/versión/granule y archivo para todos los meses objetivo; hacer control de duplicados/meses ausentes y de cambios de versión/reprocesamiento.
- Verificar variable/unidades/calendario/intervalo temporal y fill por muestra y por lote. Para IMERG, aclarar tasa media vs acumulado y horas válidas; para GLDAS, revisar `cell_methods` y edición de máscara.
- Versionar geometría completa con fecha, entidad responsable, atribución, licencia, feature ID, CRS/datum originales; validar geometría completa y topología.
- Definir una grilla/celda espacial exacta y bounds; justificar reproyección, densificación y pesos de área; demostrar cierre geométrico, más pruebas de borde/agujeros y análisis de resolución.
- Por mes y variable informar `A válida/A intersección` y `A válida/A cuenca`, faltantes QA y no solo cantidad de celdas. Establecer previamente el mínimo de cobertura apto para el uso junto al equipo; sin umbral acordado, no publicar la media como serie representativa.
- Aprobar manejo de QA: IMERG QIm/randomError no son pruebas de bias; análisis comparativo con fuente independiente o estaciones representativas si la afirmación requiere exactitud local.
- No rellenar ausentes con cero; no interpolar meses o pixeles silenciosamente. Si se usa una imputación, informar método, incertidumbre y análisis con/sin imputación.
- Reproducir de extremo a extremo en checkout nuevo con manifiestos, rutas configurables e insumos autorizados; asegurar que datos privados/voluminosos y credenciales no quedan en Git.

### C. Inferencia de tendencia

- Verificar ventana realmente disponible y tamaño efectivo (meses/años válidos) después de QA/cobertura, sin sustituir inventario por observaciones.
- Definir variable/escala, hipótesis, periodo, baseline, estimando (tendencia por estación/mes/anual), modelo y criterio de inferencia antes de analizar.
- Modelar estacionalidad mensual; evaluar autocorrelación y tamaño efectivo, heterocedasticidad/estructura de residuos, extremos y distribución; seleccionar un método robusto justificado.
- Identificar saltos de sensores, composición de constelación, versiones/reprocesamientos NASA, cambios de máscara/área válida; evaluar rupturas y realizar sensibilidad excluyendo tramos/decisiones.
- Reportar pendiente con unidad/tiempo, intervalo de confianza, magnitud de efecto, supuestos y cobertura; no presentar p-value aislado ni significancia como importancia práctica.
- Analizar sensibilidad a centro vs área, QA, geometría, periodo base, imputación, resolución y alternativas (p. ej. ERA5/estaciones).

### D. Mapas

- Para **valores**: conservar variable/unidad, versión, leyenda física razonable, missing distinguible, grilla/resolución y mes; indicar raster fuente frente a reproyección.
- Para **anomalía**: definir climatología mensual/base y población mínima por celda; comparar los mismos meses del año; no mezclar tasa con acumulado ni períodos de diferente cobertura; representar falta de base como missing.
- Para **significancia**: definir prueba por pixel, tamaño temporal, autocorrelación/estacionalidad, independencia de observaciones, multiplicidad/FDR, máscara estable y certeza de geolocalización; poner la magnitud y su incertidumbre junto al indicador de significancia.
- Evitar interpolación visual que oculte tamaño de pixel; incluir fecha de las fuentes, CRS, unidad, máscara y estado exploratorio/validado en metadata/caption.

## 11. Recomendación provisional de MVP para FUL-107

1. **Alcance inicial:** una pregunta descriptiva y no causal sobre variabilidad mensual; empezar con una visualización raster de precipitación mensual IMERG de una fecha inspeccionada. Si el objetivo de la primera serie tiene que ser estrictamente regional e histórico, priorizar evaluación de MERRA-2 `T2M` como piloto, no presentar aún un resultado de 20 años.
2. **Región:** mantener Murray–Darling completa como región candidata, porque corresponde a una cuenca definida legalmente y al caso hidrológico. No sustituirla por NSW ni declarar NSW como control. La máscara debe permanecer explícitamente provisional hasta resolver CRS/datum/licencia, geometría completa, bounds, fracción de área, faltantes y sensibilidad.
3. **Ventana/periodicidad:** tratar 2005–2024 mensual como ventana objetivo de catálogo/inventario. Validar disponibilidad real granule-a-granule por variable antes de cualquier serie. La disponibilidad de la fecha inicial no es prueba de 240 datos aptos.
4. **Producto inicial sugerido:** IMERG Final mensual para mapa exploratorio debido a 0,1° y gránulos inspeccionados. Como primer camino a serie histórica de una variable, MERRA-2 T2M tiene la recomendación provisional de mayor defendibilidad por definición/cobertura; equipo debe resolver si esto sirve la pregunta y la audiencia. GLDAS 2005 queda como exploratorio, sujeto a resolución de máscara.
5. **Agregación:** evaluar área fraccional en proyección equivalente con geometría versionada y cobertura válida informada; comparar contra centros y ponderación por área completa. No adoptar el resultado de FUL-104 como promedio oficial.
6. **Faltantes/QA:** nunca convertir fill a 0. Separar missing de cero; almacenar máscaras y razones por celda/mes; no filtrar IMERG por umbral numérico no aprobado. Antes de serie, proponer reglas y mostrar resumen por producto y cobertura.
7. **Visualización inicial permitida:** mapa de muestra raster original con metadatos/atribución y missing distinguidos; panel comparativo como diagnóstico si se titula como exploratorio. Series regionales, anomalías y mapas estadísticos pasan gates de §10.

### Riesgos científicos priorizados

| Prioridad | Riesgo | Efecto si no se controla | Mitigación antes del gate |
|---|---|---|---|
| Alta | Inventario CMR o una muestra se comunica como serie regional completa. | Falsa afirmación de continuidad/cobertura y confianza del usuario. | Manifiesto completo por mes + QA por píxel/área y reporte cobertura regional antes de emitir serie. |
| Alta | Mezcla tasa y acumulado IMERG o interpreta QIm/randomError como QA concluyente. | Unidad/magnitud incorrecta; filtrado sesgado o confianza injustificada. | Mantener unidad fuente, verificar periodo y revisar ATBD; elegir regla solo con sensibilidad aprobada. |
| Alta | Linaje de aguas GLDAS 2005 no resuelto. | Valores de superficie de agua pueden contaminar el indicador de humedad terrestre/histórico. | Confirmación por granule + comparar máscara de aguas y archivos/versión previa. |
| Alta | Se usa polígono/CRS equivocado o se mezcla GDA94/GDA2020/WGS84 sin transformación trazable. | Desplazamiento de celdas y pesos, cambio de cobertura. | Congelar versión/CRS/datum, transformar con operación identificada, densificar y verificar geometría. |
| Media-alta | Ponderar celdas completas solo porque intersectan, o tratar la media de centros como representativa. | Sesgo fronterizo/latitudinal y sensibilidad artificial de la escala. | Comparar centros, cell-area y fraction-intersection; publicar coverage y sensibilidad. |
| Media | Diferencias de versión/constelación/reprocesamiento en serie multidecenal IMERG/MERRA/GLDAS. | Ruptura artificial interpretada como señal climática. | Auditoría release/version por meses, pruebas de homogeneidad/rupturas; alternativa independiente. |
| Media | Transferir licencia/redistribución de geometría/derivados mezclados sin permiso claro. | Incumplimiento de atribución/condición share-alike. | Confirmar metadatos del archivo exacto y atribuir fuentes y modificaciones; enlazar en lugar de redistribuir mientras siga ambiguo. |

## 12. Pruebas pendientes y responsables sugeridos

Los responsables siguientes son propuestas para coordinación, no tareas ya aceptadas. La asignación final corresponde al equipo.

| Prueba/decisión pendiente | Acción concreta y criterio de cierre | Responsable sugerido | Dependencia |
|---|---|---|---|
| QA IMERG y política de faltantes | Definir presentación/uso de `precipitationQualityIndex`, `randomError`, `gaugeRelativeWeighting`; revisar clases ATBD vs desempeño regional; medir cobertura espacial/temporal sin fijar cortes arbitrarios; proponer versión de regla y efecto. | Lucas (ciencia); revisión César | Decidir si la pregunta de MVP requiere selección/ponderación QA o solo visualización contextual. |
| Ensayo espacial ampliado | Repetir en meses/estaciones/fechas de distintos años para los tres productos; validar bounds, huecos/borde, densificación, datum, área conservada y coverage válida; reportar centro vs intersección fraccional. | Lucas + Alaín (datos/CRS/procedencia), aprobación metodológica del equipo | Acceso a geometría completa con CRS y licencia identificados. |
| Geometría Murray–Darling | Registrar URL/ID de ítem, fecha/versión/checksum, autor/publicador, CRS original/exportado, licencia y atribución; resolver operación de transformación y condiciones de productos derivados. | Alaín (extracción/procedencia) + César (selección de región) | La ficha MDBA Library devolvió 403 durante consulta web actual; API ArcGIS responde según FUL-104. |
| Confirmación GLDAS 2005 | Preguntar a GES DISC por reescritura/versión del granule CMR `G1413723174-GES_DISC`; cotejar máscara MOD44W y/o copia pre/post octubre 2020, comprobar coherencia de fill en aguas. | Alaín (descarga/archivo) + Lucas (validación) | No disponible un checksum histórico pre-remáscara en evidencia revisada. |
| Serie y cobertura 2005–2024 | Obtener manifiesto de fuentes para cada fecha, confirmar identidad/versiones y cobertura en cuenca; no contar inventario como dato descargado. | Alaín | No ejecutar descarga masiva hasta que FUL-107 elija candidato/pregunta. |
| Recomendación de caso/MVP | Decidir primera variable, región, pregunta descriptiva no causal, ventana y tipo de mapa/serie; registrar selección y decisiones en documentos de César. | César/equipo (FUL-107) | Este informe entrega opciones; no aprueba unilateralmente. |
| Revisión científica de recomendaciones | Comparar recomendación de mapa IMERG y serie MERRA con EDA de FUL-105 y contexto del caso de uso; cerrar comentarios sobre unidades, cobertura y límites. | César; Alaín para ingestión/formato | PR FUL-110 publicada y fuente de EDA accesible. |

## 13. Preguntas para resolver en FUL-107

1. ¿La primera experiencia busca demostrar calidad técnica de raster, o responder una pregunta de cuenca? Para cada fin la recomendación inicial de variable puede ser distinta.
2. ¿Se acepta que la primera demo sea un mapa IMERG mensual de muestra claramente rotulado, dejando la serie regional como fase siguiente?
3. Si se exige una primera serie histórica, ¿acepta el equipo MERRA-2 T2M como candidato de menor riesgo inicial dentro de la terna, sujeto a cobertura/QA/versionado y comparación ERA5?
4. ¿Murray–Darling completa se mantiene como región objeto, con geometría oficial versionada y cálculo de área fraccional que aún debe validarse? ¿Cuál será la fuente/version de límite que se atribuye?
5. ¿Qué definición de cobertura regional y qué mínimo decidirá el equipo antes de considerar publicable un mes? Evitar fijarlo por intuición de este informe.
6. ¿IMERG QIm se mostrará como diagnóstico contextual (incluidas las bandas stoplight opcionales de NASA) sin descarte automático, o se requiere un experimento específico para una política QA?
7. ¿El grupo acepta mantener GLDAS fuera de la serie final hasta confirmar el tratamiento de máscara de aguas 2005, aun cuando siga disponible como muestra exploratoria?
8. ¿Qué fuentes observacionales independientes están disponibles para evaluar pertinencia regional (estaciones BoM/radar u otra fuente), con qué representatividad y licencia?
9. ¿Qué pregunta no causal, población de años y baseline se comprometerán para no sugerir pronóstico, causalidad o tendencia ya probada?
10. ¿Qué evidencia de licencias se necesita antes de guardar o publicar la geometría completa y derivadas de límites MDBA/ABS?

## 14. Fuentes primarias, DOI y fecha de consulta

Fuentes consultadas el **2026-11-15**, excepto donde se anota fecha de publicación/actualización. Fichas web son temporales: verificar versión/cita de colección al descargar/publicar.

### NASA/GES DISC — productos y QA

- [NASA GPM, IMERG V07 ATBD, versión del documento 2026-08-13 (PDF)](https://gpm.nasa.gov/sites/default/files/2026-08/IMERG_V07_ATBD_final_260813.pdf): campos mensuales y semihorarios, QIm, random error, significado de gauge-relative weight y orientación de uso §3.12.2, tabla 5 y apéndice 9.5.
- [NASA IMERG Final Monthly DOI](https://doi.org/10.5067/GPM/IMERG/3B-MONTH/07) — `GPM_3IMERGM`, colección `07`; el granule FUL-104 indica `ProductVersion=V07B`. **Versión de colección `07` y sufijo de archivo `V07B` son identificadores distintos**, no intercambiables.
- [NASA GPM data directory](https://gpm.nasa.gov/data/directory): describe algoritmo/periodo y lista ATBD/FAQ vigentes; consultado 2026-11-15.
- [NASA GES DISC, catálogo MERRA-2 M2TMNXSLV](https://catalog.data.gov/dataset/merra-2-tavgm_2d_slv_nx-2dmonthly-meantime-averagedsingle-levelassimilationsingle-level-di), colección global de medias mensuales, v5.12.4, grid 0,625° × 0,5°, registro 1980–actual, latencia reportada ~3 semanas; metadata consultada 2026-11-15.
- [NASA GMAO MERRA-2 citation table](https://gmao.gsfc.nasa.gov/gmao-products/merra-2/citing-merra-2-data_merra-2/): vincula `tavgM_2d_slv_Nx` y `M2TMNXSLV` al DOI `10.5067/AP1B0BA5PD2K`; consultado 2026-11-15.
- [NASA GES DISC, README GLDAS V2](https://hydro1.gesdisc.eosdis.nasa.gov/data/GLDAS/GLDAS_NOAH025_M.2.1/doc/README_GLDAS2.pdf): capa Noah, tipos `_inst`, fill, significado de mensual/3-hourmente; manual consultado 2026-11-15.
- [NASA LDAS, especificaciones GLDAS](https://ldas.gsfc.nasa.gov/gldas/dataset): GLDAS-2.1 periodo 2000–presente, 0,25°/1°, mensual/3h, forzamientos y no variables asimiladas; consultado 2026-11-15.
- [NASA LDAS, fuentes de forzamiento](https://ldas.gsfc.nasa.gov/gldas/forcing-data): GLDAS-2.1 combina GDAS, precipitación GPCP desagregada y radiación AFWA; consultado 2026-11-15.
- [Aviso GES DISC sobre posprocesamiento de GLDAS-2](https://forum.earthdata.nasa.gov/viewtopic.php?t=659): aviso de octubre 2020 sobre MOD44W y descargas previas a noviembre 2020. El foro no abrió en la consulta actual, pero el resultado del dominio oficial y las citas en FUL-104/contraste conservan su contenido; consultar el aviso con GES DISC antes de resolver el granule 2005.
- [DOI GLDAS Noah 2.1 mensual 0,25°](https://doi.org/10.5067/SXAVCZFAQLNO).

### Geometría, licencias y alternativas

- [MDBA boundary item API](https://www.arcgis.com/sharing/rest/content/items/ba731d77d80947fbbcbf7524364372ff?f=json), [MDBA FeatureServer layer 0](https://services8.arcgis.com/5xxEi7I2m6ml97fE/arcgis/rest/services/boundary_gdb/FeatureServer/0), [MDBA Library record](https://library.mdba.gov.au/data_product/https-mdba-maps-arcgis-com-home-item-html-id-ba731d77d80947fbbcbf7524364372ff-overview). La última devolvió 403 en lectura actual; el informe usa metadatos/ensayo archivados en FUL-104 y no afirma que la geometría de cache sea una publicación versionada.
- [ABS ASGS Edition 4 boundary downloads/metadata](https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-4-july-2026-june-2031/access-and-downloads/digital-boundary-files), fecha publicada 2026-07-22, datum GDA2020 y CC BY 4.0 salvo indicación distinta; consultado 2026-11-15. Revisar además la licencia del ZIP específico NSW empleado antes de redistribuir.
- [ERA5 monthly single-level reanalysis](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-monthly-means?tab=overview), variable 2m temperature, DOI [10.24381/cds.f17050d7](https://doi.org/10.24381/cds.f17050d7), alternativa no NASA consultada 2026-11-15.
- [SMAP L4 version 8 data](https://nsidc.org/data/smap/data) y [User Guide](https://nsidc.org/sites/default/files/documents/user-guide/multi_spl4smau-v008-userguide.pdf), serie inicia 2015, superficie/raíz, rejilla EASE-Grid; alternativa moderna de humedad de suelo con definición distinta, consultada 2026-11-15.

### Evidencia integrada del repositorio y cambios integrados

- [FUL-104 scientific validation](validacion_cientifica_ful104.md), [catalog dataset notes](datasets.md), [catalog MVP](catalog_mvp.json), [source contrast](contraste_fuentes.md), [Murray–Darling region](region_murray_darling.md), [FUL-105 inference plan](ful-105-plan-inferencia.md), [BE-02 handoff](be-02-sample-workflow.md).
- [Spatial audit script](../research/auditar_espacial_ful104.py), [offline spatial tests](../research/tests/test_ful104_spatial_audit.py), [NASA product EDA notebook](../research/notebooks/02_eda_nasa_products.ipynb). La ejecución anterior se conserva como documentos/resultados del handoff; el notebook versionado no lleva outputs de ejecución.
- [PR #9 — FUL-106](https://github.com/Cesitar16/anomaly-zero/pull/9), [PR #11 — FUL-105](https://github.com/Cesitar16/anomaly-zero/pull/11), [PR #14 — FUL-104](https://github.com/Cesitar16/anomaly-zero/pull/14), [PR #15 — correcciones FUL-104](https://github.com/Cesitar16/anomaly-zero/pull/15). Estado consultado con `gh pr view` el 2026-11-15: las cuatro `MERGED` a `dev`.

## 15. Transferencia a César / FUL-107

La decisión de equipo que puede adoptar César sin afirmar más de lo que demuestran los datos es una demo exploratoria de muestra IMERG raster, manteniendo Murray–Darling como región candidata y explicitando tasa/unidad/faltantes. Si el alcance exige una serie mensual regional, MERRA-2 T2M es la propuesta provisional de menor riesgo dentro de la terna, con compuerta de cobertura/QA/CRS y validación; no hay base para anunciarla ya. GLDAS puede ilustrar humedad superficial en una muestra, pero la selección histórica debe esperar resolución del linaje 2005.

Quedan bajo decisión de César/equipo: primera pregunta/variable, caso/región y geometría que se registrará, política QA/cobertura, condición para serie, mapa permitido y baseline para cualquier anomalía. Alaín debe revisar procedencia/formatos/CRS y ayudar a resolver la descarga/edición de GLDAS y límites. No existe aprobación de César o Alaín incorporada a este documento. FUL-107 sigue siendo propiedad de César y no se altera desde FUL-110.

### Checklist de los 13 criterios de aceptación de FUL-110

La tarjeta permanece en **In Review**. “Cumplido” abajo significa que el entregable demuestra el criterio documental; no afirma que César/Alaín hayan aprobado el contenido ni que FUL-107 esté decidido.

- [x] **1. Fichas de los tres productos:** identidad, versión, DOI, unidad, frecuencia, resolución, formato, tipo de fuente, granules y fecha; se consolidan cobertura global/período publicado y calendario/metadata temporal observados en §4. La discrepancia de período de IMERG queda visible y acotada a pre-2000.
- [x] **2. Matriz QA:** separa fill, cero, QA del proveedor, diagnóstico, filtros aplicados/no aplicados, estado, incertidumbre y reglas elegibles/bloqueadas; no inventa umbrales (§5).
- [x] **3. Versiones y unidades:** distingue IMERG colección 07/archivo V07B y mm/hr; MERRA T2M K; GLDAS kg/m² y riesgos de conversión (§4–§5).
- [x] **4. Geometría y permiso:** identifica ítem/servicio MDBA, origen, salida CRS, datum incierto, licencia/atribución, hash de muestra y límite del LineString (§7).
- [x] **5. Métodos espaciales:** cifras de enero 2005/2021 para tres productos, conteos válidos y denominadores; propone el método fraccional como candidato y añade el contrato de métricas/denominadores para el pipeline (§7).
- [x] **6. NSW frente a cuenca:** diferencia territorial, porcentajes con denominadores y cautela de redistribución (§7).
- [x] **7. Linaje GLDAS 2005:** dictamen **Indeterminado**, evidencia, alcance, consecuencia y prueba posterior (§8).
- [x] **8. Visualizaciones:** distingue muestra raster, media descriptiva, serie regional, anomalía y significancia; ninguna se declara existente por el catálogo (§9).
- [x] **9. Recomendación de MVP:** opción condicionada para demo frente al camino candidato para caso/serie validable, alternativas no aprobadas y evidencia que cambiaría la selección (§4, §11).
- [x] **10. Gates de publicación:** demo, serie regional e inferencia/tendencia tienen criterios separados, responsables/evidencias y requisitos de cobertura (§10, §12).
- [x] **11. Trazabilidad:** afirmaciones y recomendaciones se vinculan a fuentes primarias, fecha, estado, riesgo y limitación (§3, §14).
- [x] **12. Límites de alcance:** no se descargaron 240 meses, no se implementaron API/UI/pipeline, ni se aprobaron QA o agregación definitivos (§2–§3).
- [x] **13. Transferencia y revisión:** el informe y la PR #18 están vinculados a FUL-110 y formulan decisiones para FUL-107 (§13, §15). Solicitudes de revisión a César y Alaín se enviaron desde la cuenta GitHub de Lucas; no se adjudica aprobación mientras no exista revisión.

**Fuera de estos criterios documentales y aún pendiente por decisión externa:** revisar el informe/PR; confirmar procedencia y licencia de fuentes específicas; que César registre los acuerdos y decisiones en FUL-107; integrar la PR solo después de revisión. Nada de ello se marca como aprobación científica ya recibida.

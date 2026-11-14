# Catálogo científico inicial

Catálogo para [FUL-102](https://linear.app/fullstack-track/issue/FUL-102/nasa-01-consolidar-investigacion-work-en-catalogo-nasa-verificable-y). Colecciones, región y período son **candidatos**. Se inspeccionaron muestras IMERG V07B y una copia MERRA-2 reorganizada por NCAR; siguen pendientes el gránulo NASA original MERRA-2, una muestra GLDAS y la validación científica y espacial completa. FUL-104 profundiza la verificación y FUL-107 registra la decisión del equipo. El archivo [catalog_mvp.json](catalog_mvp.json) contiene las fichas estructuradas, [region_murray_darling.md](region_murray_darling.md) describe la región y [contraste_fuentes.md](contraste_fuentes.md) registra pruebas y límites del contraste.

## Evidencia

- **DOC:** documentación primaria identificada; no implica haber abierto un archivo.
- **TEC:** comprobación directa reproducible con fecha y método.
- **INF:** interpretación o propuesta, pendiente de decisión cuando corresponda.
- **PARCIAL:** hay comprobaciones directas con límites y aspectos pendientes.
- **PEND:** falta comprobar o está bloqueado. Las afirmaciones del informe de Work no contrastadas también permanecen pendientes.

Una etiqueta se aplica a una afirmación, no a todo el producto. La investigación Work (PDF y planilla recibidos por el equipo) es un insumo secundario. Las pruebas indicadas como propias se realizaron nuevamente el 2026-11-14 UTC.

## Hallazgos para la revisión del equipo

- **Cobertura:** 2005–2024 está inventariado en CMR para las tres colecciones; IMERG Final V07 llega a septiembre de 2025 en la consulta ampliada. El inventario no certifica píxeles válidos.
- **Interpretación:** MERRA-2 `T2M` es aire a 2 m; IMERG mensual es una tasa en mm/h; GLDAS describe agua de la capa 0–10 cm. Las conversiones y las dependencias entre productos requieren revisión científica.
- **Muestras:** se abrieron gránulos IMERG y una copia MERRA-2 reorganizada. En la caja de estudio se comprobaron valores finitos y distintos del fill durante los doce meses de 2005 para ambos productos; ello no valida la calidad. La comparación exploratoria con estaciones de Wagga Wagga muestra diferencias que no prueban por sí solas error o sesgo; faltan ventanas temporales alineadas e independencia. El gránulo NASA original MERRA-2 y GLDAS no se abrieron.
- **Alternativas:** se detectaron [conflictos de metadatos SMAP L4 y MOD11A2 en AppEEARS](contraste_fuentes.md#conflicto-de-unidades-en-metadatos-appeears-de-smap-l4). No aplicar automáticamente unidades o fill sin revisar la entrega real.
- **Geografía:** Murray–Darling es la región candidata; NSW es un estado parcialmente solapado. La prueba de bordes es exploratoria y no aprueba una ponderación o máscara de producción.
- **Evidencia Work:** se verificaron por hash 35 respuestas o archivos individuales; las otras pruebas y sus límites están en [pruebas_work.csv](pruebas_work.csv). El ZIP completo no se recibió y no se espera para continuar.

## Terna candidata

| Variable | Colección / versión CMR | Campo propuesto | Unidad original | Resolución nominal | Estado |
| --- | --- | --- | --- | --- | --- |
| Temperatura del aire a 2 m | MERRA-2 `M2TMNXSLV` / `5.12.4` | `T2M` | K en copia NCAR; confirmar en archivo NASA | Mensual; 0,625° longitud × 0,5° latitud | TEC copia NCAR reorganizada; PEND gránulo NASA y QA |
| Precipitación | IMERG Final `GPM_3IMERGM` / `07` | `Grid/precipitation` | mm/h, tasa confirmada en muestras | Mensual; 0,1° × 0,1° | TEC muestras 2005 y enero 2010 y control básico; PEND máscara y validación independiente |
| Agua modelada de suelo 0–10 cm | GLDAS Noah `GLDAS_NOAH025_M` / `2.1` | `SoilMoi0_10cm_inst` | kg/m² documentado; confirmar atributos del archivo | Mensual; 0,25° × 0,25° | DOC colección y tabla Noah; TEC UMM-Var e inventario; PEND apertura y QA |

**Procedencia GLDAS:** NASA distingue producción principal y temprana por sus forzantes; además recomienda obtener las versiones posteriores al posprocesamiento de octubre de 2020 que enmascaró salidas inválidas sobre aguas continentales. Ver [detalle y fuentes](contraste_fuentes.md#gldas-21-revisión-de-procedencia-y-máscara-histórica).

En GLDAS mensual, el sufijo `_inst` identifica el tipo de campo de origen y **no** significa que el valor mensual sea una sola instantánea: el manual describe un promedio de los pasos de tres horas. Confirmar los atributos y el tratamiento de faltantes al abrir el archivo. Ver [contraste del manual](contraste_fuentes.md#contraste-de-la-terna).

MERRA-2 es un reanálisis; temperatura del aire no equivale a temperatura radiométrica superficial. GLDAS 2.1 es un modelo terrestre sin asimilación, según [NASA LDAS](https://ldas.gsfc.nasa.gov/gldas/dataset); no es una medición puntual directa. Para IMERG, NASA describe `precipitation` como tasa en su [guía V07](https://gpm.nasa.gov/sites/default/files/2025-02/FAQ%20for%20IMERG%20V07%20Applications%20Users_202502.pdf). Confirmar la semántica de la entrega mensual en el manual y el archivo.

El [manual NASA IMERG](https://gpm.nasa.gov/sites/default/files/2023-07/IMERG_TechnicalDocumentation_final_230713.pdf), páginas 22 y 24–25, define la variable mensual como tasa media en mm/h; la conversión de tasa por las horas reales del mes se probó en dos celdas de enero; sigue pendiente validar calidad, límites temporales y aplicación regional. No interpretar kg/m² de una capa de suelo como porcentaje sin justificar espesor, densidad y definición. Conservar unidad original, conversión y procedencia.

## Inventario de enero 2005 a diciembre 2024

**TEC:** el 2026-11-14 entre 17:07:53 y 17:07:56 UTC se consultó [NASA CMR](https://cmr.earthdata.nasa.gov/search/granules.json) por cada concept ID, con `bounding_box=138,-38,153,-24`, `temporal=2005-01-01T00:00:00Z,2024-12-31T23:59:59Z`, `page_size=300` y `sort_key=start_date`. Para cada colección se contaron 240 registros, 240 claves mensuales distintas en `time_start`, ningún mes esperado ausente y ningún mes duplicado. Primer y último mes: 2005-01 y 2024-12.

Esto comprueba registros CMR que intersectan una **caja contenedora**, no archivos descargados ni píxeles válidos o un promedio regional. La [actualización NASA de agosto de 2026](https://gpm.nasa.gov/data/news/update-imerg-v08-transition-schedule-aug-2026) revisó la previsión de transición a V08; consultar el [detalle y los límites de la búsqueda](contraste_fuentes.md#estado-de-transición-imerg-v08) antes de extender el período. La consulta ampliada documentada en contraste_fuentes.md encontró registros IMERG Final V07 hasta septiembre de 2025; esto es inventario, no cobertura válida de píxeles. No mezclar versiones o productos para completar períodos sin decisión explícita.

Ejemplo reproducible: [consulta GLDAS](https://cmr.earthdata.nasa.gov/search/granules.json?collection_concept_id=C1342986036-GES_DISC&page_size=300&sort_key=start_date&bounding_box=138%2C-38%2C153%2C-24&temporal=2005-01-01T00%3A00%3A00Z%2C2024-12-31T23%3A59%3A59Z). Sustituir el concept ID para las otras colecciones; comparar meses distintos con los 240 esperados y comprobar paginación si cambian los parámetros. La caja se expresa oeste,sur,este,norte.

## Primer y último gránulo y tamaño orientativo

**TEC:** consulta CMR del 2026-11-14 18:12 UTC con la caja `138,-38,153,-24`, `page_size=1` y orden ascendente o descendente por fecha. Los extremos corresponden a registros inventariados; no prueban continuidad, calidad, píxeles válidos ni descarga en esos extremos. La cifra de tamaño es el campo `granule_size` de CMR para enero de 2005, no una medición de almacenamiento ni un tamaño fijo para todos los meses. La [documentación CMR](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html) denomina a este tamaño en megabytes, sin precisar ahí si son decimales o binarios.

| Producto | Primer mes CMR | Último mes CMR | `granule_size` de enero de 2005 |
| --- | --- | --- | ---: |
| MERRA-2 | 1980-01 | 2026-09 | 51,8986 |
| IMERG Final V07 | 1998-01 | 2025-09 | 17,1937 |
| GLDAS Noah 2.1 | 2000-01 | 2026-07 | 23,9142 |

Para el ejemplo IMERG, multiplicar la cifra por 1.048.576 coincide con los 18.028.945 bytes de la copia NCAR. La misma operación para GLDAS da 25.075.859 bytes, coincidentes con el [listado OPeNDAP NASA](https://hydro1.gesdisc.eosdis.nasa.gov/opendap/GLDAS/GLDAS_NOAH025_M.2.1/2005/contents.html). Esto respalda la interpretación binaria en esos dos registros, pero no verifica todos los proveedores o gránulos. Medir ejemplos antes de planificar capacidad. Los nombres exactos de los gránulos de ejemplo y la fecha de consulta figuran en el JSON.

## Entrega a Alaín: primera muestra

Consultar cada concept ID para enero de 2005 y la caja indicada; usar el punto de prueba de la ficha regional. CMR descubre gránulos: obtener la URL de acceso desde sus metadatos. El catálogo respondió públicamente en la prueba; descargar puede requerir [Earthdata Login](https://urs.earthdata.nasa.gov/) y autorización. No guardar secretos en Git ni en el frontend.

| Producto / concept ID | Archivo esperado por metadatos | Campo en metadatos CMR | Comprobar al abrir |
| --- | --- | --- | --- |
| MERRA-2 `C1276812859-GES_DISC` | `.nc4` | `T2M` | Dimensiones, coordenadas, calendario, unidad K, fill, escala y versión |
| IMERG `C2723754851-GES_DISC` | `.HDF5`, archivo V07B | `Grid/precipitation` | Grupo, nombre, mm/h, definición mensual, ejes, fill y calidad |
| GLDAS `C1342986036-GES_DISC` | `.nc4`, archivos `021` | `SoilMoi0_10cm_inst` | Unidad kg/m², capa, agregación mensual, ejes, fill y máscara |

Las muestras IMERG de NCAR abrieron el grupo y campo indicados; MERRA-2 solo se ha abierto en una copia reorganizada y GLDAS sigue pendiente de apertura. Consultar los manuales antes de interpretar QA o aplicar escalas: no suponer que cero significa dato faltante. Registrar gránulo, colección, versión, URL descubierta, fecha, checksum si está disponible, método, resultado o error. FUL-103 cubre la primera muestra y FUL-106 la extracción de las tres. La guía no bloquea el descubrimiento en paralelo.

### Descubrimiento de variables en otros servicios

**TEC, 2026-11-14:** en la respuesta completa [configured-variables de Giovanni](https://api.giovanni.earthdata.nasa.gov/configured-variables) aparecen `GPM_3IMERGM_07_precipitation` y `GLDAS_NOAH025_M_2_1_SoilMoi0_10cm_inst`. No aparece el identificador exacto `M2TMNXSLV_5_12_4_T2M` ni otra entrada de `M2TMNXSLV`; sí hay otras colecciones MERRA. La respuesta completa coincide con el hash registrado por Work. Esto es descubrimiento, no prueba de que una petición autenticada funcione; no reemplazar la colección mensual por otra solo porque esté disponible.

La respuesta [AppEEARS de productos](https://appeears.earthdatacloud.nasa.gov/api/product), también recuperada con el hash de Work, no incluye entradas con los tres shortnames exactos de la terna. Sí incluye alternativas MODIS y SMAP; sus variables, temporalidad y QA deben evaluarse para el caso de uso. La ausencia se limita al catálogo consultado y no significa que los productos no existan en NASA. Más detalle en [contraste de fuentes](contraste_fuentes.md#respuestas-completas-recuperadas-de-giovanni-y-appeears).

## Alternativas y asuntos abiertos

| Alternativa | Uso potencial | Condición |
| --- | --- | --- |
| GLDAS 2.1 como colección única de aire, lluvia y suelo | Si tres integraciones bloquean una demostración | Propuesta de Work; verificar campos y unidades en archivos. Las variables comparten modelo y forzantes. El manual IMERG indica además que Final usa campos MERRA-2 para desplazamientos, por lo que la terna no debe asumirse totalmente independiente. |
| [SMAP SPL3SMP V9](https://nsidc.org/data/spl3smp/versions/9) | Contraste reciente de humedad superficial | Inicio en 2015 y profundidad aproximada 0–5 cm; no sustituye sin análisis GLDAS 0–10 cm. Verificar QA y muestra. |
| [SMAP SPL4SMGP V8](https://nsidc.org/data/spl4smgp/versions/8) | Humedad modelada 0–5 cm y 0–100 cm | No es plenamente independiente de IMERG en Australia. Revisar [discrepancias de metadatos AppEEARS](contraste_fuentes.md#conflicto-de-unidades-en-metadatos-appeears-de-smap-l4), geolocalización y muestras. |
| [MOD11C3.061](https://doi.org/10.5067/MODIS/MOD11C3.061) | Temperatura superficial mensual en malla de 0,05° | Es temperatura superficial y no sustituye directamente la del aire; capas, escala y QA documentadas en [contraste de fuentes](contraste_fuentes.md#mod11c3-capas-y-tratamiento-de-calidad-documentados). Falta abrir una muestra; no figuró en el catálogo AppEEARS consultado. |
| [Estaciones BoM en NOAA GHCN-Daily](https://www.ncei.noaa.gov/pub/data/ghcn/daily/all/ASN00072150.dly) | Contraste exploratorio de precipitación | Wagga Wagga AMO y estaciones cercanas comparadas para 2005; falta alinear horarios, comprobar independencia de IMERG y condiciones de redistribución. |

| Pregunta pendiente | Responsable propuesto | Siguiente paso |
| --- | --- | --- |
| Campos, atributos, QA y muestra real | Alaín + Lucas | FUL-103 y FUL-106: abrir gránulos NASA y registrar unidades, fill, escalas, calendario y orden de ejes; contrastar con fichas oficiales |
| Unidades, calendario y conversiones | César + Lucas | Revisar T2M aire frente a LST, tasa IMERG en mm/h frente a acumulado y tratamiento de `SoilMoi0_10cm_inst` antes del EDA |
| Máscara y ponderación espacial | Lucas + César | FUL-104/107: elegir tratamiento de celdas de borde y área tras revisar el polígono y las grillas |
| Licencias y estaciones de contraste | Lucas | Comprobar condiciones de cada entrega antes de redistribuir |
| Contrato y publicación | Alaín + equipo | FUL-108 tras la puerta de evidencia |

Los 13 recursos están inventariados en el informe y la hoja «Inventario de fuentes» de Work; una página de evento local reproduce las mismas direcciones salvo HTTP/HTTPS en GEO.ca, con el alcance secundario descrito en [revisión Work](revision_work.md#contraste-secundario-de-los-13-recursos-del-reto). Incluyen plataformas, artículos, misiones y tutoriales: no son 13 datasets equivalentes. Giovanni y AppEEARS son plataformas; CMR es catálogo de metadatos; NOAA, KNMI y agencias canadienses no son NASA. Verificar derechos por recurso y producto.

**Revisión humana pendiente:** César debe revisar unidades y semántica; Alaín, identificadores, acceso y formatos. No se registra su conformidad antes de recibirla.


## Estado frente a los criterios de FUL-102

| Criterio | Evidencia local | Estado |
| --- | --- | --- |
| Tres fichas con variables, versiones, unidades y fuentes | [Catálogo estructurado](catalog_mvp.json) y tabla de terna | Preparado; productos aún candidatos |
| 13 recursos originales diferenciados de datasets | [Referencias Work](referencias_work.csv), IDs R01–R13 | Inventariados; contraste por referencia parcial |
| Ventana 2005–2024 y límites de calidad | Inventario CMR y [contraste](contraste_fuentes.md) | 240 meses por colección en metadatos; QA integral pendiente |
| Región oficial, CRS y licencia | [Ficha de Murray–Darling](region_murray_darling.md) | Preparada; atribución de derivados y método espacial por revisar |
| Parámetros y checklist para Alaín | Sección «Entrega a Alaín» de este documento | Preparado; extracción autenticada no ejecutada aquí |
| Alternativas, estados y condiciones | Sección «Alternativas» y catálogo estructurado | Preparadas como opciones, no aprobadas |
| Revisión de César y Alaín; enlace a la entrega en la card | No hay conformidad registrada ni enlace publicado en Linear | Pendiente de revisión y coordinación del equipo |

Esta tabla describe el estado de los materiales locales y no marca la card como terminada. El usuario indicó no esperar el ZIP ni acceso GLDAS; sus ausencias se mantienen explícitas como límites de la evidencia.

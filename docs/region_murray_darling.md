# Región de referencia exploratoria: Murray–Darling

## Publicación en el catálogo BE-03

César autorizó publicar **Murray–Darling Basin** con el ID estable `murray-darling-basin` como referencia geográfica y administrativa para exploración puntual. El catálogo cita el [ítem ArcGIS publicado por MDBA](https://www.arcgis.com/sharing/rest/content/items/ba731d77d80947fbbcbf7524364372ff?f=json), que documenta la fuente del límite. El ítem declara CC BY 4.0, identifica a DCCEEW como fuente de los límites y a MDBA como publicador; la atribución y las condiciones de redistribución constan en la sección siguiente. Esto no publica una geometría ni aprueba una máscara, agregación regional, QA o inferencia. Por ello `geometry_source` identifica el ítem documental, mientras `geometry_version`, `crs` y `area_km2` siguen `null`: la exportación consultada en EPSG:4326 no determina por sí sola el CRS nativo ni establece una versión oficial validada para el contrato.

El catálogo permite consultar metadatos de MERRA-2, IMERG Final y GLDAS Noah asociados a esa referencia. Los tres permanecen `unavailable`, con `current_dataset_id`, `coverage` y `quality` en `null`, hasta publicar y verificar snapshots mediante el mecanismo de la API. Archivos locales o cobertura histórica de NASA no bastan para declararlos disponibles.

La autorización no modifica AZ-03 ni los gates R/T, no valida área o cobertura espacial, y no autoriza medias regionales, tendencias, anomalías ni inferencia. Los valores observados de IMERG siguen siendo muestras puntuales en `mm/hr`; contar centros no mide superficie.

**Estado científico:** región de referencia autorizada para exploración puntual; geometría y uso como unidad estadística siguen sin aprobación. Se ha ensayado una máscara temporal de centros para una muestra IMERG y se compararon promedios exploratorios para una fecha, pero no se ha calculado una serie regional ni seleccionado una ponderación definitiva. Nueva Gales del Sur es una alternativa administrativa que se solapa parcialmente con la cuenca y no representa una región de control independiente.

## Límite y condiciones

- **DOC / TEC, 2026-11-14 UTC:** [ítem ArcGIS publicado por MDBA](https://www.arcgis.com/sharing/rest/content/items/ba731d77d80947fbbcbf7524364372ff?f=json), titulado «Murray—Darling Basin Boundary as defined in Section 4 (1) of the Water Act 2007», propietario `MDBAGISPUBLISHER`, acceso público. El ítem declara [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Confirmar atribución y condiciones actuales antes de redistribuir derivados.
- [Servicio FeatureServer, capa 0](https://services8.arcgis.com/5xxEi7I2m6ml97fE/arcgis/rest/services/boundary_gdb/FeatureServer/0): geometría poligonal. Los metadatos muestran extensión WKID 102100 / 3857; se puede solicitar salida en EPSG:4326 con `outSR=4326`. No asumir que el CRS del conjunto histórico original sea 4326.
- Extensión aproximada en longitud/latitud: oeste 138,5685; sur −37,6821; este 152,4885; norte −24,5856. El atributo consultado `AREA_HA=105857400` no es una nueva medición. No usar el área Web Mercator como área geodésica equivalente.
- El metadato `modified` del ítem consultado corresponde al 14 de enero de 2026 a las 21:08:32 UTC; es la fecha de modificación del ítem, no necesariamente de la geometría original. El ítem atribuye el recurso al Australian Government Department of Climate Change, Energy, the Environment and Water (DCCEEW) y describe su derivación desde Australia’s River Basins 1997, con procesamiento posterior del departamento. MDBA figura como publicador del ítem. Antes de redistribuir una entrega distinta, confirmar sus condiciones y atribución específicas.

## Fragmento geométrico de integración

El [segmento GeoJSON](examples/murray_darling_boundary_segment.geojson) contiene 12 vértices consecutivos extraídos de la geometría MDBA descargada como EPSG:4326. Incluye la atribución DCCEEW indicada en el ítem, el publicador MDBA, enlaces, licencia CC BY 4.0 y descripción de la modificación. Está representado como `LineString` para probar lectura de coordenadas: **no es un polígono cerrado ni sirve para recortar, calcular superficies o decidir si un punto está en la cuenca**. La geometría completa debe obtenerse del servicio oficial y verificarse al usarla.

## Punto de prueba

**TEC:** el 2026-11-14 UTC se consultó la capa 0 con el punto `147.36,-35.11` (longitud, latitud), `inSR=4326`, `spatialRel=esriSpatialRelIntersects` y `returnCountOnly=true`; el servicio devolvió `count=1`. Es un punto de ensayo en el entorno de Wagga Wagga, no una muestra representativa de la cuenca ni un polígono de subcuenca.

[Repetir consulta de intersección](https://services8.arcgis.com/5xxEi7I2m6ml97fE/arcgis/rest/services/boundary_gdb/FeatureServer/0/query?f=json&where=1%3D1&returnCountOnly=true&geometry=147.36%2C-35.11&geometryType=esriGeometryPoint&inSR=4326&spatialRel=esriSpatialRelIntersects).

Para una copia GeoJSON, consultar el servicio con `where=1=1`, `outFields=*`, `outSR=4326` y `f=geojson`. Verificar resultado y licencia antes de guardar o redistribuir. La respuesta utilizada en la prueba queda únicamente en la caché local ignorada; no se incorpora una copia versionada aquí.

## Uso con productos NASA

La caja `138,-38,153,-24` contiene la extensión aproximada y sirve para descubrir gránulos, no para recortar el límite. Una máscara requiere intersectar el polígono con las celdas y documentar bordes, áreas y valores faltantes. Las grillas tienen resoluciones distintas. FUL-104 debe revisar archivos y proponer área; César y Lucas deben acordar ponderación antes de producir medias regionales.


## Prueba espacial de una muestra IMERG

El 2026-11-14 se consultó la geometría MDBA con `outSR=4326` y GeoJSON; la respuesta guardada temporalmente en `data/cache/ful-102/mdba_boundary_4326.geojson` contiene un polígono válido según Shapely 2.2.0 y tiene SHA-256 `d36fe31424758cc4fb8eef25e21b835bb5c05c793c746e8a1eb7b5a5841f6a53`. La prueba compara coordenadas geográficas con los centros y límites declarados en el gránulo IMERG mensual V07B de enero de 2005; no transforma las coordenadas ni calcula áreas. La extensión del polígono queda dentro de la caja revisada de 138–153° E, 38–24° S.

De las 21 000 celdas cuyos centros quedan en esa caja, **10 092 centros** están cubiertos por el polígono, todos con precipitación finita y distinta del `_FillValue` en esta muestra. Si en lugar de centros se incluyen las cajas de celda que intersectan el polígono, hay **10 467 celdas**; 9 720 están cubiertas completamente y 747 intersectan parcialmente. De estas últimas, 375 tienen el centro fuera y 372 lo tienen dentro. `covers` incluye el borde y `intersects` incluye el contacto con el borde; los resultados dependen de la geometría y precisión usadas.

Esta primera comprobación solo cuenta celdas; la sección siguiente explora áreas y promedios para la misma fecha. La selección por centro excluye parte de las celdas de borde y la selección por intersección incluye sus porciones externas; para una serie regional debe acordarse el método, gestionar áreas, faltantes, licencia y reproducibilidad, y evaluar su sensibilidad.


## Sensibilidad exploratoria de los bordes

Con la misma geometría MDBA y muestra IMERG de enero de 2005 se compararon cuatro ponderaciones para **una única fecha**. Para los promedios por área se calcularon áreas geodésicas WGS84 con pyproj 3.8.0. En el caso fraccional se intersectaron primero las cajas y el polígono en coordenadas geográficas mediante Shapely 2.2.0 y después se calcularon áreas geodésicas de las intersecciones; esto es una aproximación cuya precisión y topología requieren revisión. Los valores finitos distintos del fill se convirtieron de tasa media a acumulado multiplicando por 744 horas.

| Selección y ponderación | Tasa media exploratoria (mm/h) | Conversión enero (mm) |
| --- | ---: | ---: |
| Centro dentro, pesos iguales | 0,03781639 | 28,13539 |
| Centro dentro, área completa de celda | 0,03780881 | 28,12975 |
| Toda celda intersectada, área completa | 0,03857728 | 28,70150 |
| Área de cada celda dentro del polígono | 0,03778986 | 28,11565 |

La diferencia entre los dos últimos resultados en esta muestra es aproximadamente 0,586 mm, pero **no** permite generalizar el efecto a otros meses ni elegir una metodología. No se han aplicado criterios científicos de calidad o validación independiente y el promedio no es una cifra oficial.

Existe además una limitación numérica observable: entre los límites consecutivos `float32` de esta caja hay 60 pares de longitudes con pequeño solapamiento (máximo 0,0000152588°) y 88 pares de latitudes con pequeñas separaciones (máximo 0,0000038147°). La suma geodésica de las intersecciones por celda fue aproximadamente 1 058 622 km² frente a 1 058 574 km² calculados directamente para el polígono, una diferencia de aproximadamente 48 km² (0,0046%). Ambos cálculos incluyen además diferencias de discretización geodésica; no se ha atribuido esta diferencia a una sola causa ni resuelto el ajuste de topología. No emplear el área resultante como dato oficial ni esta aproximación como máscara de producción sin normalizar la grilla y verificar conservación de área.


## Ensayo de cierre con grilla regular y proyección equivalente

Para investigar la diferencia de cierre anterior, se repitió la prueba para enero de 2005 usando la misma geometría y valores, pero redondeando a dos decimales los límites declarados por el archivo. El redondeo es un **supuesto de ensayo** coherente con la grilla nominal de 0,1°, no una corrección oficial del producto. Tras redondear, los límites adyacentes de la caja no presentan diferencias numéricas. Se transformaron el polígono y las esquinas de las celdas desde EPSG:4326 a `EPSG:3577` (GDA94 / Australian Albers), una [proyección de áreas equivalentes](https://www.agriculture.gov.au/sites/default/files/documents/nlum_250m_descriptivemetadata_20220622.pdf), y se intersectaron en ese plano con Shapely 2.2.0 y pyproj 3.8.0. El cálculo usa segmentos rectos entre las esquinas proyectadas, sin densificación, y la transformación de datum seleccionada por pyproj; requiere revisión antes de aplicarse operacionalmente.

Las **10 467 celdas intersectadas** poseen área positiva y valores finitos distintos del fill. La suma de áreas intersectadas es 1 058 574,001227789 km²; el área del mismo polígono transformado es 1 058 574,001227787 km². La diferencia computada es 0,0028 m² (aproximadamente `2,7e-15` de la superficie), lo que verifica el cierre interno de esta partición proyectada a precisión numérica. La tasa media ponderada en esta muestra resulta 0,03778984 mm/h o **28,11564 mm** al multiplicar por 744 horas.

El buen cierre no prueba exactitud geográfica, validez de redondear los límites, independencia de datos ni calidad física. No demuestra por sí solo la causa exacta de los 48 km² observados en el ensayo anterior: simultáneamente cambiaron los límites y el método de intersección/área. Tampoco constituye aprobación de una máscara o serie de producción. Deben evaluarse densificación de bordes, transformación de datum, precisión del límite, tratamiento de calidad y sensibilidad en varias fechas antes de decidir.

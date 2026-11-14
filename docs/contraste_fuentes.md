# Contraste de fuentes y primeras pruebas científicas

**Estado: contraste documentado con evidencia disponible, con limitaciones explícitas.** Este documento registra comprobaciones independientes realizadas el 14 de noviembre de 2026 y su alcance. Incluye la apertura de trece muestras mensuales IMERG V07B y una copia MERRA-2 reorganizada por NCAR; todavía no se han abierto gránulos originales de MERRA-2 ni GLDAS. Las fechas y disponibilidad de los servicios pueden cambiar.

## Evidencia original recuperada parcialmente

El informe Work (referencia E01, p. 47–49) apunta a `Anomaly_Zero_Evidencia.zip`. El paquete no fue recibido ni se encontró en las ubicaciones revisadas, y Lucas indicó que no conoce su ruta. La hoja «Pruebas técnicas» identifica hashes, tamaño, URL y fecha. Se recuperaron quince respuestas o archivos públicos de esas URL y se reconstruyeron veinte respuestas usando la planilla y consultas repetidas; los treinta y cinco cuerpos tienen exactamente el SHA-256 registrado en la hoja. La coincidencia respalda cada recuperación individual, no el paquete E01 completo ni los scripts propios:

| Prueba Work | Documento recuperado | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| `gldas_readme`, fila 39 | [README NASA GLDAS Version 2](https://docserver.gesdisc.eosdis.nasa.gov/public/project/hydrology/README_GLDAS2.pdf) | 1.114.575 | `aa37fce1e9f92bc3e3b00209016f9ac7a8089596839aa43c22e3b21246097ac7` |
| `merra_readme`, fila 41 | [MERRA-2 File Specification](https://docserver.gesdisc.eosdis.nasa.gov/public/project/MERRA/MERRA2.README.pdf) | 1.064.850 | `4cf82170a569803a4b296537d5e836951db82c0856e172a77b62ca8793c0cb0c` |
| `smap4_guide`, fila 40 | [Guía NSIDC SMAP L4 V8](https://nsidc.org/sites/default/files/documents/user-guide/multi_spl4smau-v008-userguide.pdf) | 767.583 | `9e46b1325358e5a1ab4c732f5b10725b6cf78c41cba00a86e7fc3bf2a94504f6` |
| `nsw_boundary_zip`, fila 38 | [Límites ABS ASGS 2026, ZIP](https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-4-july-2026-june-2031/access-and-downloads/digital-boundary-files/STE_2026_AUST_SHP_GDA2020.zip) | 21.331.858 | `057befed53bc7bd095e54d1594fe32925ed324443df767d66a889c52ba655c03` |
| `mdba_geometry`, fila 33 | [Geometría MDBA en EPSG:4326](https://services8.arcgis.com/5xxEi7I2m6ml97fE/arcgis/rest/services/boundary_gdb/FeatureServer/0/query?where=1%3D1&outFields=%2A&returnGeometry=true&outSR=4326&f=geojson) | 477.805 | `d36fe31424758cc4fb8eef25e21b835bb5c05c793c746e8a1eb7b5a5841f6a53` |
| `nasa_migration`, fila 12 | [Guía NASA de migración GES DISC](https://raw.githubusercontent.com/nasa/gesdisc-tutorials/main/user-guidance/GES_DISC_Migration_to_Earthdata_Website_and_Earthdata_Cloud.md) | 11.534 | `8d59158a4f00315aae3f0aa25d68bac94f1b5cb49e7403a707ae4e4d1baff74e` |
| `gio_notebook`, fila 28 | [Notebook NASA Giovanni en la nube](https://raw.githubusercontent.com/nasa/gesdisc-tutorials/main/notebooks/How_to_Access_GiC_Time_Series_Service.ipynb) | 67.941 | `4ca741d37eeb3dabc1972c75cb3c6907710a179b26534e7993964c2099f963ae` |
| `sar_license`, fila 36 | [Licencia del tutorial SAR de CSA](https://raw.githubusercontent.com/asc-csa/Synthetic_Aperture_Radar_Tutorial/main/LICENSE) | 3.555 | `0c17b21d6573e738faa074752a528033e441c5e4547f6280aa2541288370da9c` |
| `appeears_products`, fila 7 | [Catálogo AppEEARS](https://appeears.earthdatacloud.nasa.gov/api/product) | 111.855 | `c0244fcd0a3e3cd00d026c393b39899b0a44d3375051160b4994bf69a1e4ff45` |
| `giovanni_variables`, fila 9 | [Variables configuradas Giovanni](https://api.giovanni.earthdata.nasa.gov/configured-variables) | 28.975 | `b7fce83e82211f1f2fb9eed6bd93517a3905c557229cb1d862e9fad68c66d8f8` |
| `ntrs`, fila 11 | [Metadatos NASA NTRS](https://ntrs.nasa.gov/api/citations/20090042747) | 4.579 | `b97d6fb6ad0a4cc7fba5bf1c836749e2bbfd546639754461e62459c588873e03` |
| `appeears_mod11a2`, fila 29 | [Capas AppEEARS MOD11A2.061](https://appeears.earthdatacloud.nasa.gov/api/product/MOD11A2.061) | 6.038 | `7eebb59b991914e69d64725b0c60ea073bebd87846c7b8ce83c885fd8a70e10a` |
| `appeears_mod13a3`, fila 30 | [Capas AppEEARS MOD13A3.061](https://appeears.earthdatacloud.nasa.gov/api/product/MOD13A3.061) | 6.054 | `6db022f95baae707ca8e00433a1631760a4ffc0732b84a019a56fd1313e3a8aa` |
| `mdba_service`, fila 31 | [Servicio MDBA](https://services8.arcgis.com/5xxEi7I2m6ml97fE/arcgis/rest/services/boundary_gdb/FeatureServer?f=json) | 3.185 | `3b8899beedd7bb2a51d3e89815c5299ed0a9d889903d6629ba9eab881f2dd05e` |
| `mdba_layer`, fila 32 | [Capa MDBA](https://services8.arcgis.com/5xxEi7I2m6ml97fE/arcgis/rest/services/boundary_gdb/FeatureServer/0?f=json) | 8.934 | `923e56d96deff75bc14acfdb1604fa1bbe19db4c96a63086358a15bd56328924` |
| `cmr_imerg_v08`, fila 26 | [Consulta CMR original](https://cmr.earthdata.nasa.gov/search/collections.json?short_name=GPM_3IMERGM&version=08&page_size=10), reconstruida desde celda completa | 203 | `e870d178068497c00593adb0210141b42281ea94d24ed9a60c354ca7542704a9` |
| `gldas_2005_2025`, fila 15 | Inventario CMR reconstruido con marca de respuesta original | 922.136 | `32c41a6f707d0f18c97f3c225726d40c1e295eb07f0b6eabeaa92bff2ece74f8` |
| `imerg_2005_2025`, fila 18 | Inventario CMR reconstruido con marca de respuesta original | 1.115.290 | `9b885524026ee0cf3985a6110834a846741995f03a9a9a74bde274418a0a1d22` |
| `mdba_item`, fila 27 | Ítem ArcGIS reconstruido con contadores originales | 4.393 | `63fd9559378e89f3ca8646722bb058e81d4bb79ecfe8d5fc11d486541fcbf47d` |
| `power_sample`, fila 34 | Respuesta POWER reconstruida con tiempo original | 944 | `b047382d9fa98e149a739c5440dee87cb8d916caf537c028d29eb529f3eefbc7` |

| `cmr_gldas`. fila 2 | Respuesta CMR reconstruida con marca original | 35.425 | `449e1625bf566b7bfd426e49480d58a2a04fa296cd62e19814f004997a25862a` |
| `cmr_imerg`. fila 3 | Respuesta CMR reconstruida con marca original | 39.163 | `03ff2c3e75637d11748ac8ec3717db9b86db97c989bd7eb328c061fd722a7093` |
| `cmr_merra`. fila 4 | Respuesta CMR reconstruida con marca original | 20.460 | `2d1bae58c05dad7f35067c3733f17a42282323f9ab8afe46137aa7e824d78e7c` |
| `cmr_smap_l3`. fila 5 | Respuesta CMR reconstruida con marca original | 12.611 | `3426fc1dd54b68094b4f5dbb4560e9195c345b3f38fa7521d0f0f92602d8aeda` |
| `cmr_smap_l4`. fila 6 | Respuesta CMR reconstruida con marca original | 10.151 | `a19ba29b561bf116e9c6695db9436134d799583db75becdc3c498ce2c0b5a2d6` |
| `gldas_first`. fila 13 | Respuesta CMR reconstruida con marca original | 3.966 | `9289fbde1cb06bafd51b1fe3df9164b4c065acf770e07afea3209f74d3ec3a31` |
| `gldas_last`. fila 14 | Respuesta CMR reconstruida con marca original | 3.953 | `e1267167b67ed53569d7e8a35cfb12bc580b746aae97a2edd43c3fee03d99f84` |
| `imerg_first`. fila 16 | Respuesta CMR reconstruida con marca original | 4.749 | `70569dc8b251d4aea5db8e46feeb38a6568fd82535638c33365c1e2b7c5c67ab` |
| `imerg_last`. fila 17 | Respuesta CMR reconstruida con marca original | 4.750 | `980e6cde7128a7224fd153b43dbeb7c6d890983f24efff6073041ca612bcd841` |
| `merra_first`. fila 19 | Respuesta CMR reconstruida con marca original | 4.096 | `05a8ae6c43555cb6b9b6cef9699964088a3700af42489a69f3e1f9c291014026` |
| `merra_last`. fila 20 | Respuesta CMR reconstruida con marca original | 4.097 | `569a63cb0f5208f09203c851310f029521a16bb5ce1f42e884f372be535dfe6a` |
| `smap_l3_first`. fila 22 | Respuesta CMR reconstruida con marca original | 5.281 | `9819df5453f68ea14361be0a13bcb26db672766cb6892cf36de41428d84f21bd` |
| `smap_l3_last`. fila 23 | Respuesta CMR reconstruida con marca original | 4.756 | `02f02f781ce8318cafb3e069b3d6abaa492e6d8604e2b74f9ef2fd114f8783b9` |
| `smap_l4_first`. fila 24 | Respuesta CMR reconstruida con marca original | 4.913 | `0b85e79c38afa52571262814d038048832df5899381867042d0598b41286a182` |
| `smap_l4_last`. fila 25 | Respuesta CMR reconstruida con marca original | 4.912 | `e71e2103046b5b23258e0b9a15811d12adabaff6d8dc44fc627ce72b8bbe7490` |

El ZIP ABS contiene un XML ISO que enlaza explícitamente a CC BY-SA 4.0; falta resolver su relación con los términos generales del sitio antes de redistribuir derivados. Se verificaron nuevamente los 35 cuerpos por tamaño y SHA-256 y hay una copia de cada uno en `data/cache/ful-102/`, ignorada por Git. La columna `archivo_local_ignorado` de `pruebas_work.csv` identifica la copia local correspondiente; no se incluye su contenido en el repositorio y hay que volver a obtenerlo para reproducir la comprobación en otro equipo. El SHA-256 del conjunto completo E01 no está disponible. Los inventarios originales de GLDAS e IMERG se reconstruyeron y verificaron como se explica abajo; el de MERRA-2 sigue sin recuperarse. Una consulta nueva es una prueba diferente.

## Contraste de la terna

| Afirmación o pregunta de contraste | Fuente primaria | Resultado y límites |
| --- | --- | --- |
| MERRA-2 `M2TMNXSLV` corresponde al DOI `10.5067/AP1B0BA5PD2K`. | Manual MERRA-2, p. 60; [CMR colección](https://cmr.earthdata.nasa.gov/search/collections.json?concept_id=C1276812859-GES_DISC). | **DOC/TEC:** la tabla del manual vincula el shortname con ese DOI; CMR devolvió el concepto y versión 5.12.4. |
| `T2M` es temperatura del aire a 2 m en K. | Manual MERRA-2, p. 43–45; CMR describe la colección mensual. | **DOC:** el manual define T2M en K en la colección horaria y lista la colección mensual; el UMM-Var asociado a esa colección confirma la variable y unidad en metadatos. Confirmar atributos en el gránulo mensual exacto. No confundir con `TS`, temperatura de piel. |
| `GLDAS_NOAH025_M` 2.1 contiene `SoilMoi0_10cm_inst` en kg/m². | Manual GLDAS, p. 7 y 22; [NASA LDAS GLDAS](https://ldas.gsfc.nasa.gov/gldas/dataset); [CMR colección](https://cmr.earthdata.nasa.gov/search/collections.json?concept_id=C1342986036-GES_DISC). | **DOC/TEC:** el manual lista capa y unidad para Noah, y dice que los productos mensuales promedian los de tres horas. CMR identifica la colección. La existencia y atributos dentro de un archivo concreto siguen pendientes. |
| ¿El sufijo `_inst` hace que el dato mensual sea una única instantánea? | Manual GLDAS p. 25, puntos 6–8. | **No:** de acuerdo con el informe y el manual, los campos instantáneos mensuales se promedian entre los pasos de 00 UTC del primer día y 21 UTC del último día. No aplicarles factores de acumulación de flujos. |
| IMERG Final mensual `precipitation` está en mm/h y representa tasa media del mes. | [Documentación técnica NASA IMERG V07](https://gpm.nasa.gov/sites/default/files/2023-07/IMERG_TechnicalDocumentation_final_230713.pdf), p. 13, 22, 24–25; [CMR colección](https://cmr.earthdata.nasa.gov/search/collections.json?concept_id=C2723754851-GES_DISC). | **DOC/TEC:** NASA identifica DOI y variable para 3IMERGM, documenta unidad y tasa media durante el mes calendario. Conversión propuesta a mm/mes: tasa × horas del mes, sin sustituir faltantes por cero. Confirmar el atributo en el gránulo. |
| ¿Son completamente independientes los tres productos y POWER? | Manual IMERG p. 25; NASA LDAS y documentación POWER. | **No debe suponerse:** el manual indica que IMERG Final utiliza campos MERRA-2 para desplazamientos. POWER documenta procedencia meteorológica MERRA-2. Verificar otras entradas compartidas antes de llamar independiente a un contraste. |

El documento IMERG fue recuperado de NASA para este contraste; no se afirma que sea byte a byte parte del paquete E01. Sus páginas se cuentan como páginas del PDF, que coinciden con la numeración impresa consultada.

## Variables asociadas a cada colección en CMR

**TEC, 2026-11-14 UTC:** se obtuvieron las asociaciones `variables` de cada colección desde `collections.json`, y se consultaron los conceptos UMM-Var asociados. Los tres nombres siguientes pertenecen a las colecciones candidatas según CMR. Sus dimensiones y fill son **metadatos catalogados**, no atributos comprobados en el gránulo particular:

| Colección | Variable asociada | Unidad declarada | Dimensiones declaradas | Fill declarado |
| --- | --- | --- | --- | --- |
| MERRA-2 5.12.4 | [`T2M`, V3188345197](https://cmr.earthdata.nasa.gov/search/concepts/V3188345197-GES_DISC.umm_json) | K | time=1, lat=361, lon=576 | 999999986991104 |
| IMERG 07 | [`Grid/precipitation`, V3171500685](https://cmr.earthdata.nasa.gov/search/concepts/V3171500685-GES_DISC.umm_json) | mm/hr | Grid/time=1, Grid/lon=3600, Grid/lat=1800 | -9999.900390625 |
| GLDAS 2.1 | [`SoilMoi0_10cm_inst`, V3384930202](https://cmr.earthdata.nasa.gov/search/concepts/V3384930202-GES_DISC.umm_json) | kg m-2 | time=1, lat=600, lon=1440 | -9999 |

Los fills deben leerse del archivo real y compararse con el tipo y las reglas del lector; no fijar estas cifras como reglas universales. En particular, la ruta de IMERG incluye el grupo `Grid` y sus metadatos declaran el orden lon/lat. La muestra IMERG abierta posteriormente confirma ese orden para lectura con h5py; verificarlo de nuevo en cualquier otro archivo o lector. La consulta también identificó un concepto distinto para `T2MDEW`; no seleccionar por coincidencia parcial de nombre.

## Reproducción completa de las consultas de inventario

El 2026-11-14 entre 17:34:11 y 17:34:13 UTC se repitieron las consultas de las filas 15, 18 y 21 de «Pruebas técnicas» de Work, con los mismos conceptos, caja y ventana 2005–2025. Las respuestas completas nuevas se guardaron localmente bajo `data/cache/ful-102/`, excluido de Git. Cada respuesta indica un total CMR inferior a `page_size=300`, por lo que la única página recuperada cubrió todos los resultados de esa consulta. Se contaron `time_start` mensuales distintos, faltantes y duplicados:

| Producto | HTTP / registros | Meses distintos | Ausentes | SHA-256 de la respuesta nueva |
| --- | --- | --- | --- | --- |
| GLDAS | 200 / 252 | 252 | Ninguno | `073d82bd80d5278393ec74ee363dc0fbb26098cfacb8f16d7cd4ecbaf80dc7cb` |
| IMERG | 200 / 249 | 249 | 2025-10, 2025-11, 2025-12 | `7c5551812e181b8d7f3db7f3e36966fd099ce5519f1b134711464f52a40a48c3` |
| MERRA-2 | 200 / 252 | 252 | Ninguno | `d913e89dfb40bf5d9c2107cd647e7d99c1fa94f3f62cd46e5343d2ce1d5e1429` |

No hubo meses duplicados. Los conteos y ausencias reproducen los reportados por Work. Los hashes de las tres respuestas repetidas difieren de los de Work. Posteriormente se reconstruyeron los cuerpos originales de GLDAS e IMERG reemplazando únicamente la marca temporal y verificando el hash; el cuerpo original MERRA-2 no pudo recuperarse así. Estos resultados son inventario en caja, no cobertura válida de píxeles.

## Primera muestra abierta: NASA POWER

El 2026-11-14 UTC se repitió [la consulta oficial POWER mensual](https://power.larc.nasa.gov/api/temporal/monthly/point?parameters=T2M%2CPRECTOTCORR&community=AG&longitude=147.36&latitude=-35.11&format=JSON&start=2005&end=2005). Respuesta HTTP 200, 944 bytes, SHA-256 `afb8592c6d5cf7e348e5a5512febb42cf782a54c29f0c849c916e1789a0303a0`; se guardó en `data/cache/ful-102/power_2005_wagga.json`, excluido de Git. El hash difiere del registrado por Work (`b047382d9fa98e149a739c5440dee87cb8d916caf537c028d29eb529f3eefbc7`); más abajo se documenta la reconstrucción exacta, que identifica la diferencia en `times.data`.

El JSON declara `fill_value=-999`, estándar LST, `T2M` en °C y `PRECTOTCORR` en mm/día. Para cada variable hay 12 claves mensuales de 2005, sin fill entre los valores de la respuesta; la clave `200513` es anual. Enero: `T2M=25.21 °C`, `PRECTOTCORR=0.88 mm/día`; la multiplicación por 31 días resulta en 27.28 mm estimados. La respuesta original de Work se reconstruyó posteriormente y confirma estos valores; la comparación completa se describe más abajo. [Documentación NASA POWER mensual](https://power.larc.nasa.gov/docs/services/api/temporal/monthly/).

Este ensayo valida lectura y unidades declaradas de **una respuesta puntual POWER**, no un promedio de Murray–Darling, no valida las tres colecciones originales y no es una muestra de grilla ni prueba de precisión local. No se calculó tendencia ni se seleccionó método estadístico.

**Contraste interno con valores diarios:** se consultó el mismo punto y variables en la [API diaria POWER](https://power.larc.nasa.gov/docs/services/api/temporal/daily/), enero de 2005 y `time-standard=LST`. Respuesta HTTP 200, SHA-256 `1e1f8ade74efd49bd03cd985e5801f34531a1493ef659119cdb362b66b7075e5`, conservada en `data/cache/ful-102/power_daily_200501_wagga.json`. La respuesta contiene 31 días por variable sin fill. La media diaria de T2M es 25.2081 °C frente a 25.21 °C en el producto mensual. La suma de valores diarios de PRECTOTCORR es 27.31 mm frente a 27.28 mm al multiplicar la tasa mensual publicada (0.88 mm/día) por 31. La diferencia de 0.03 mm es compatible con el redondeo de valores publicados, pero no se ha demostrado su causa. Conservar la distinción, no forzar igualdad exacta ni presentar esta comparación entre productos POWER como validación independiente.


## Muestra espacial pública adicional POWER

**TEC, 2026-11-14 UTC:** el servicio [NASA POWER mensual regional](https://power.larc.nasa.gov/docs/services/api/temporal/monthly/) respondió HTTP 200 para `T2M`, comunidad `AG`, `latitude-min=-36`, `latitude-max=-34`, `longitude-min=146`, `longitude-max=148`, `start=2005`, `end=2005` y formato JSON. Se conservó en `data/cache/ful-102/power_regional_2005.json` con SHA-256 `0f162fd194f402ef6e42c2be87a8746a62c58431d29535becffe0b1e1299feb3` (datos excluidos de Git).

El `FeatureCollection` contiene 15 puntos con 12 meses de T2M cada uno y una clave anual adicional; los 180 valores mensuales no contienen el fill declarado `-999`. Las coordenadas de centros devueltos son longitudes 146.25, 146.875 y 147.5; latitudes −36.0, −35.5, −35.0, −34.5 y −34.0. Para enero los valores declarados van de 22.39 a 27.23 °C. La cabecera declara fuente MERRA2 y estándar LST. Se verificó estructura y unidades reportadas, no exactitud física.

Una consulta preliminar de 1° × 1° devolvió HTTP 422 con mensaje de mínimo de 2° por dimensión; esto documenta el comportamiento del servicio durante esta prueba, no una garantía de configuración futura. La región solicitada es rectangular, incluye celdas que podrían quedar fuera de la cuenca y no se aplicó máscara ni promedio de cuenca. Esta muestra POWER no constituye el archivo nativo MERRA-2 de GES DISC, una validación independiente ni una muestra IMERG o GLDAS.

## Acceso a los tres gránulos candidatos

Se descubrió un gránulo de enero 2005 por colección usando CMR y se hizo una petición HTTPS anónima de rango pequeño a la URL de datos devuelta por el catálogo. El 2026-11-14 entre 17:28:40 y 17:28:45 UTC las tres solicitudes redirigieron a `urs.earthdata.nasa.gov` y terminaron con **HTTP 401**. No se introdujeron ni guardaron credenciales. Es evidencia de la prueba anónima realizada, no de que un usuario autenticado no pueda descargar los archivos.

| Producto | Gránulo descubierto | Resultado |
| --- | --- | --- |
| MERRA-2 | `MERRA2_300.tavgM_2d_slv_Nx.200501.nc4` | 302 → 401, sin abrir datos |
| IMERG | `3B-MO.MS.MRG.3IMERG.20050101-S000000-E235959.01.V07B.HDF5` | 302 → 401, sin abrir datos |
| GLDAS | `GLDAS_NOAH025_M.A200501.021.nc4` | 302 → 401, sin abrir datos |

Para continuar se necesita acceso Earthdata Login autorizado para GES DISC o muestras auténticas ya obtenidas por el equipo. Mantener credenciales fuera de Git y del chat. [Acceso GES DISC](https://www.earthdata.nasa.gov/centers/ges-disc/data-access).

## Inconsistencia de enlaces CMR observada

Los registros de gránulo consultados el 14-11-2026 devuelven enlaces de documentación de colecciones no relacionadas entre sus metadatos: el gránulo MERRA-2 incluye un enlace a `ges-disc-gpm-3gprofnoaa21atms-day-07`, IMERG uno a `ges-disc-m2t3nvcld-5.12.4`, y GLDAS uno a `ges-disc-tovsadng-01`. **TEC:** comprobado en los resultados CMR de enero 2005. No usar esos enlaces para identificar las colecciones. Validar shortname, versión, concept ID, DOI y descripción conjuntamente. La inconsistencia de enlaces no prueba que los archivos científicos sean incorrectos.

## Limitaciones y posibles verificaciones posteriores

- Inspeccionar los demás archivos originales de E01, incluidos scripts y respuestas completas, si el paquete aparece. No se puede recuperar su contenido de los resúmenes truncados de la planilla.
- Contrastar las demás referencias, productos secundarios y afirmaciones de los materiales con sus fuentes primarias, registrando si cada una se verificó o sigue pendiente.
- Abrir y validar muestras auténticas de las tres colecciones: coordenadas, dimensiones, variable, unidades, calendario, valores faltantes, calidad, porción de la cuenca y procedencia. Las pruebas de acceso anónimo no satisfacen esta condición.
- Solicitar revisión humana de unidades a César y de formatos/acceso a Alaín por los canales que el equipo acuerde.

## Inventario de referencias y colecciones secundarias

Se creó [referencias_work.csv](referencias_work.csv), con las 79 referencias de la hoja de Work, su estado declarado, disponibilidad HTTP observada y estado de revisión de contenido. El 2026-11-14 UTC se usó una solicitud GET con `Range: bytes=0-0`, siguiendo redirecciones, sin autenticar: 73 respondieron 200 o 206; cinco dieron error de TLS o conexión en este entorno y E01 es un archivo local no disponible. **Una respuesta HTTP exitosa no verifica autoría, contenido, licencia, vigencia ni la conclusión científica.** Los casos fallidos tampoco demuestran que el recurso no exista. El campo `verificacion_contenido` indica qué afirmación se contrastó y distingue revisión parcial de pendiente; ninguna marca implica que se hayan auditado todos los contenidos de una referencia.

Como contraste acotado de metadatos CMR, el 2026-11-14 UTC se consultaron `short_name` y `version` exactos, con `page_size=50`. Se obtuvo una coincidencia para cada uno de los once pares siguientes. No se verificaron datos, calidad ni cobertura completa mediante esta consulta:

| ID Work | Shortname / versión | Concept ID devuelto por CMR | Observación |
| --- | --- | --- | --- |
| P01 | M2TMNXSLV / 5.12.4 | `C1276812859-GES_DISC` | Coincide con Work |
| P02 | GPM_3IMERGM / 07 | `C2723754851-GES_DISC` | Coincide con Work |
| P03 | GLDAS_NOAH025_M / 2.1 | `C1342986036-GES_DISC` | Coincide con Work |
| P04 | SPL3SMP / 009 | `C2938664585-NSIDC_CPRD` | Coincide con Work |
| P05 | SPL4SMGP / 008 | `C3480440870-NSIDC_CPRD` | Coincide con Work |
| P06 | MOD11A2 / 061 | `C2269056084-LPCLOUD` | Coincide con Work |
| P07 | MOD11C3 / 061 | `C2565788897-LPCLOUD` | Concept ID pendiente en Work; identificado en CMR |
| P08 | MOD13A3 / 061 | `C2327962326-LPCLOUD` | Coincide con Work |
| P09 | MOD16A2GF / 061 | `C2565791021-LPCLOUD` | Coincide con Work |
| P10 | AIRS3STM / 7.0 | `C1701805662-GES_DISC` | Concept ID y DOI pendientes en Work; CMR declara DOI `10.5067/UBENJB9D3T2H` |
| P11 | OMTO3d / 004 | `C3377057241-GES_DISC` | Concept ID pendiente en Work; CMR declara DOI `10.5067/Aura/OMI/DATA3401` |

Los registros UMM consultados de P07, P10 y P11 declaran inicios 2000-02-01, 2002-09-01 y 2004-10-01 respectivamente y un extremo abierto. Ese metadato **no** demuestra último gránulo, continuidad, calidad o cobertura real australiana. Las fechas y campos deben contrastarse con documentación y muestras antes de usarse. Consulta de ejemplo: [CMR UMM AIRS3STM](https://cmr.earthdata.nasa.gov/search/concepts/C1701805662-GES_DISC.umm_json). P12 es una familia Landsat con varios sensores y P13 es un servicio POWER: no se les inventó un concept ID único.

## Contraste parcial de los recursos originales

La lectura directa se hizo para clasificar los recursos y sus afirmaciones concretas, no para aprobar todos sus datos o licencias. El detalle y estado por referencia consta en `referencias_work.csv`.

- **R01 Giovanni:** [manual GLDAS NASA](https://docserver.gesdisc.eosdis.nasa.gov/public/project/hydrology/README_GLDAS2.pdf) y el [portal Giovanni](https://giovanni.gsfc.nasa.gov/giovanni/) lo presentan como herramienta de visualización y análisis; la descarga de series autenticada no se ha repetido.
- **R02 Hydrology Time Series:** la página original depende de JavaScript y la extracción disponible no permitió verificar la descripción completa. Mantener como pendiente y no inferir indisponibilidad.
- **R03 AppEEARS:** el [material NASA/USGS](https://www.earthdata.nasa.gov/s3fs-public/2025-06/AppEEARSposterdraft_AGU2024.pdf) y la [documentación API](https://appeears.earthdatacloud.nasa.gov/api/) describen extracción por punto y área; una tarea autenticada no fue ejecutada.
- **R04 NOAA:** [Climate Data Online](https://www.ncei.noaa.gov/cdo-web/) describe datos climáticos y de estaciones. Aún no se validaron estaciones concretas para la cuenca ni sus condiciones de redistribución.
- **R05 SeaWiFS:** el [registro NASA NTRS](https://ntrs.nasa.gov/citations/20090042747) confirma autores, carácter de preprint y estudio de clorofila costera, con advertencias por sedimentos y materia orgánica. El registro consigna publicación en 2009; la investigación Work había evitado asignar una fecha editorial exacta. Confirmar correspondencia editorial antes de citar una versión definitiva.
- **R06 KNMI:** la [página histórica de KNMI](https://climexp.knmi.nl/history/) describe exploración de estaciones, grillas y reanálisis. No se validó API de ingesta contractual.
- **R07 y R08:** el [artículo Medium](https://medium.com/@snp.kriss/statistical-test-methods-to-detect-trends-in-time-series-data-b361a0ec530b) usa datos de juguete y enumera métodos; la [página Statsig](https://www.statsig.com/perspectives/a-comprehensive-guide-to-statistical-significance) es divulgativa. Ambos se clasifican como recursos editoriales, no como datos ni elección metodológica validada.
- **R09 RCM:** el enlace original no respondió satisfactoriamente desde el entorno. Las condiciones de acceso y licencia de la entrega concreta siguen pendientes.
- **R10 GEO.ca:** se consultó su [portada](https://geo.ca/); no se comprobó un dataset australiano pertinente ni una licencia para todos sus recursos.
- **R11/R12 SWOT:** la [ficha de misión CSA](https://www.asc-csa.gc.ca/eng/satellites/swot/) identifica lanzamiento en 2022, estado activo y liderazgo NASA/CNES. La [página divulgativa de ecosistemas](https://www.asc-csa.gc.ca/eng/satellites/everyday-lives/monitoring-and-protecting-our-ecosystems-from-space.asp) todavía dice «en desarrollo»; no usar esa descripción histórica como estado de misión.
- **R13 tutorial SAR:** el [repositorio CSA](https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial) describe ejercicios con Python/QGIS y datos RADARSAT. Su [licencia](https://raw.githubusercontent.com/asc-csa/Synthetic_Aperture_Radar_Tutorial/main/LICENSE) incluye texto tipo MIT y una cláusula relativa al uso promocional del nombre; no implica una licencia automática para datos de terceros.

## Evidencia contextual y alternativas verificadas parcialmente

- [NASA GPM](https://gpm.nasa.gov/data/news/imerg-v08-transition-schedule) explica que el registro Final V07 se detiene en septiembre de 2025 por el cambio de versiones de productos de entrada. Esto concuerda con la consulta CMR repetida; no determina disponibilidad V08 en todos los canales.
- [NSIDC SPL3SMP V9](https://nsidc.org/data/spl3smp/versions/9) documenta producto diario en malla de 36 km desde marzo 2015; [NSIDC SPL4SMGP V8](https://nsidc.org/data/spl4smgp/versions/8) documenta producto de tres horas y malla de 9 km. La segunda página muestra aviso de geolocalización para el 14 de mayo–28 de julio de 2026. No se han abierto archivos ni confirmado la validez de gránulos individuales.
- Los resúmenes de [Hirsch, Slack y Smith (1982)](https://www.usgs.gov/publications/techniques-trend-analysis-monthly-water-quality-data-0) y [Hirsch y Slack (1984)](https://www.usgs.gov/publications/a-nonparametric-trend-test-seasonal-data-serial-dependence) distinguen Kendall estacional y una extensión para dependencia serial, con límites. Son evidencia contextual, no una prueba ejecutada ni una decisión de método para el proyecto.
- BoM documenta [sequía e impactos sobre Murray–Darling](https://www.bom.gov.au/climate/current/statements/scs70.pdf) y [lluvia persistente e inundaciones de 2022](https://www.bom.gov.au/climate/current/statements/scs77.pdf). Es contexto para formular preguntas y sensibilidad temporal; no determina el signo de la tendencia de la muestra.


## Acceso, formatos y datos australianos: contraste documental adicional

- La [guía NASA de migración GES DISC](https://github.com/nasa/gesdisc-tutorials/blob/main/user-guidance/GES_DISC_Migration_to_Earthdata_Website_and_Earthdata_Cloud.md) describe acceso mediante Earthdata Cloud y descubrimiento de URLs por CMR; informa que HOSS no ofrece el remallado del antiguo servicio. Son instrucciones institucionales, no una prueba de que una consulta autenticada del proyecto funcione.
- La [guía Giovanni 2024.1](https://giovanni.gsfc.nasa.gov/giovanni/doc/UsersManualworkingdocument.docx.html) distingue acceso invitado limitado y acceso completo mediante Earthdata Login y autorización de GES DISC. No se asumirá que una API de catálogo permita descargar todos los archivos.
- La [documentación de xarray](https://docs.xarray.dev/en/stable/user-guide/io.html) explica que `decode_cf=True` intenta aplicar convenciones CF, incluidas escalas y desplazamientos. Al inspeccionar muestras, registrar si el lector ya decodificó los datos para evitar aplicar dos veces la transformación; comparar también atributos originales. En IMERG el grupo `Grid` debe abrirse explícitamente según la biblioteca.
- [AGCD de BoM](https://www.bom.gov.au/climate/austmaps/about-agcd-maps.shtml) combina observaciones de pluviómetros con análisis gridded; es una estimación espacial, no una medición puntual independiente en cada celda. [ACORN-SAT](https://www.bom.gov.au/climate/data/acorn-sat/) identifica la versión 2.7 y ajustes sobre estaciones. La cobertura y licencia de cada estación o archivo seleccionado todavía se deben comprobar.
- [DEA Water Observations](https://knowledge.dea.ga.gov.au/data/product/dea-water-observations-landsat/) clasifica agua superficial observada a partir de escenas Landsat y declara CC BY 4.0 para ese producto. Puede servir como contexto espacial de inundaciones, pero no representa directamente precipitación ni humedad en una capa de suelo.
- [ABS](https://www.abs.gov.au/website-privacy-copyright-and-disclaimer) establece CC BY 4.0 para material de su web con excepciones y prevé términos específicos por producto. El XML del ZIP original enlaza a CC BY-SA 4.0; aún debe aclararse la condición aplicable al derivado concreto antes de publicarlo. [BoM](https://www.bom.gov.au/copyright) establece límites de uso cuando no existen términos específicos: verificar cada entrega antes de redistribuir.
- [USGS Landsat ST](https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-temperature) documenta la conversión `K = DN × 0.00341802 + 149.0`; es temperatura superficial, no aire a 2 m. La máscara y la versión del producto deben verificarse antes de usarla.

Estas revisiones son por afirmaciones concretas. No equivalen a evaluar el contenido completo de las fuentes, descargar los productos ni seleccionar la arquitectura o metodología definitiva.


La guía SMAP L4 recuperada (páginas PDF 4 y 15) especifica promedios verticales 0–5 cm y 0–100 cm y explica que utiliza precipitación IMERG V07 fuera de Norteamérica y latitudes altas. Por ello SMAP L4 V8 no debe presentarse como contraste plenamente independiente de IMERG; tampoco representa la misma capa que GLDAS 0–10 cm. Este contraste es documental y no comprueba píxeles o calidad de ningún gránulo.


## Inspección del límite administrativo original

El ZIP de ABS recuperado con el mismo SHA-256 registrado por Work contiene diez registros en su DBF. La lectura directa del primer registro identifica `STE_CODE26=1`, `STE_NAME26=New South Wales` y `AREASQKM26=800797.7073`. El registro asociado del SHP es de tipo polígono (`5`) y declara límites `(140.99927228, -37.50514656, 159.10922375, -28.1568795)` en el orden longitud mínima, latitud mínima, longitud máxima y latitud máxima. El PRJ declara GDA2020, `EPSG:7844`. Estos son atributos y extensión declarados en el archivo, no resultados de un cálculo independiente de área ni de una transformación de coordenadas.

El recurso es un límite administrativo de Nueva Gales del Sur, no el polígono de la cuenca Murray–Darling. La coincidencia del hash recupera este insumo concreto, pero no el paquete E01 completo. Antes de construir una máscara espacial deben seleccionarse y comprobarse el límite hidrográfico apropiado, su licencia y el tratamiento de CRS; aún no se ha calculado una intersección de polígonos ni una máscara de píxeles.


## POWER regional: punto espacial y agregado anual

La muestra regional POWER de temperatura T2M para 2005 contiene 15 puntos y 12 valores mensuales por punto, además de la clave `200513`. Los quince puntos consultados individualmente contra la capa oficial MDBA devuelven una intersección con la cuenca. Esto verifica la posición de los puntos representativos, **no** que las celdas completas estén dentro del polígono ni que los puntos sean una muestra representativa de toda la cuenca. Las respuestas repetidas quedan en la caché ignorada `data/cache/ful-102/power_regional_murray_intersections.json`, junto con el SHA-256 de la respuesta POWER utilizada.

En el punto `146.25,-36`, la misma consulta POWER en formato CSV etiqueta los doce valores `JAN`–`DEC` y el valor adicional `ANN`; sus números coinciden con los del JSON regional, incluido `200513=15.70 °C`. Por tanto, en esta respuesta esa clave corresponde al agregado anual y no debe contarse como un decimotercer mes. La [API mensual/anual POWER](https://power.larc.nasa.gov/docs/services/api/temporal/monthly/) documenta resultados mensuales y anuales. [Consulta puntual CSV](https://power.larc.nasa.gov/api/temporal/monthly/point?parameters=T2M&community=AG&longitude=146.25&latitude=-36&format=CSV&start=2005&end=2005&time-standard=LST).

Como comprobación numérica descriptiva, en ese punto la media aritmética simple de los 12 valores mensuales publicados es 15.7208 °C, mientras que la media ponderada por los días de 2005 es 15.6960 °C y el valor `ANN` publicado es 15.70 °C. En los 15 puntos, la diferencia absoluta entre `ANN` y la ponderación por días de los valores mensuales mostrados es inferior a 0.005 °C. La [descripción de procesamiento POWER](https://power.larc.nasa.gov/docs/methodology/data/processing/) presenta el agregado anual como media de meses sin aclarar ahí una ponderación; el resultado observado no basta para establecer cómo se calcula internamente ni para resolver esa posible ambigüedad. Evitar reconstruir el anual sin confirmar su definición y tratamiento de faltantes.

La cabecera identifica MERRA-2 como fuente y hora solar local (`LST`): esto es una prueba de consistencia del servicio POWER, no validación independiente del producto nativo MERRA-2 ni de IMERG o GLDAS.


## Muestra nativa IMERG V07B: enero de 2010

El 2026-11-14 se descargó anónimamente del [archivo NCAR GDEX](https://gdex.ucar.edu/datasets/d736000/filelist/1/) el archivo `3B-MO.MS.MRG.3IMERG.20100101-S000000-E235959.01.V07B.HDF5` (17 865 117 bytes; SHA-256 `59d477ca483062e697e5d6e2c4a4947399ef3a1c008df16ed5494a52fb03007b`). La copia está en caché local ignorada por Git. El [registro NASA CMR G2829186145-GES_DISC](https://cmr.earthdata.nasa.gov/search/concepts/G2829186145-GES_DISC.umm_json) coincide en identificador, fechas, fecha de producción y tamaño declarado; la cabecera del archivo declara DOI `10.5067/GPM/IMERG/3B-MONTH/07` y versión V07B. CMR no proporcionó checksum en el registro consultado: estas coincidencias apoyan la identificación pero **no verifican igualdad byte a byte con el archivo NASA**. No es el gránulo original de Work de enero de 2005.

Se abrió el HDF5 con `h5py` y se inspeccionaron datos y atributos originales, sin decodificación CF automática:

- `Grid/precipitation` tiene dimensiones `(time, lon, lat) = (1, 3600, 1800)`, tipo `float32`, unidades `mm/hr` y atributo `_FillValue` representado como `-9999.9`. El orden longitud antes de latitud es fundamental al extraer una región.
- `Grid/lon` y `Grid/lat` declaran coordenadas centrales a 0,1°; el grupo contiene también límites de coordenadas y tiempo. `Grid/time` declara segundos desde 1980-01-06 UTC y `calendar=julian`; su descripción indica que no incorpora segundos intercalares. Usar un lector compatible con los atributos en lugar de imponer un calendario o una zona horaria distintos.
- En la caja de descubrimiento 138–153° E y 38–24° S se inspeccionaron 150 × 140 centros: 21 000 valores finitos distintos de `_FillValue`, con tasas entre 0,001 y 0,300 mm/h. Esta caja incluye áreas fuera de la cuenca; no es una máscara ni un análisis de calidad o representatividad.
- La celda con centro más cercano a `147.36,-35.11` es aproximadamente `147.35,-35.15` y contiene 0,008 mm/h. Multiplicar esa tasa mensual por 744 horas da 5,952 mm como conversión aritmética orientativa para enero de 2010, sujeta a confirmar la interpretación de faltantes y calidad. Es una celda, no una medición puntual de estación ni una validación independiente.
- El archivo también contiene `randomError`, `gaugeRelativeWeighting` y `precipitationQualityIndex`. Su sola presencia no implica que se haya evaluado la calidad del píxel; falta revisar su interpretación y aplicar criterios adecuados.

Esta prueba confirma la lectura de una muestra IMERG mensual V07B de 2010; más abajo se añade otra de 2005. Más abajo se documentan controles adicionales de calidad y una copia reorganizada de MERRA-2; siguen pendientes la muestra original GLDAS, una comparación independiente y la recuperación de E01.


## MERRA-2: copia reorganizada y contraste con POWER

Se descargó del [archivo NCAR GDEX d927358](https://gdex.ucar.edu/datasets/d927358/) `T2M_MERRA2_asm_mon_200501_200512.nc4` (5 533 931 bytes, SHA-256 `8359bed3bc8bd11f95dda6bb1a57e82b1acfc40262affa99edeb4832174e1073`), guardado en caché ignorada por Git. NCAR describe este conjunto como una copia reorganizada por variable; el atributo `History` declara la concatenación con `ncrcat` de los gránulos mensuales NASA de 2005. Es un derivado útil para contrastar valores, **no** una copia idéntica ni una inspección directa del gránulo original.

En lectura HDF5, el archivo declara `ShortName=M2TMNXSLV`, versión `5.12.4` y DOI NASA `10.5067/AP1B0BA5PD2K`; `T2M` tiene dimensiones `(time,lat,lon)=(12,361,576)`, unidades `K`, y un valor faltante declarado `1.e+15`. El eje temporal declara calendario `standard` y `days since 2005-01-01T00:30:00`; se observaron los doce valores mensuales. Sus ejes de latitud y longitud utilizan incrementos de 0,5° y 0,625°. Este orden de dimensiones difiere del IMERG inspeccionado.

En la comparación de enero de 2005 para los 15 centros comunes con la muestra regional POWER LST, se convirtió la copia NCAR de K a °C restando 273,15. POWER resulta entre 0,0371 y 0,0714 °C más frío en esos puntos. Por ejemplo, en `147.5,-35.0`, NCAR declara 298,4313 K (25,2813 °C) y POWER 25,21 °C. La comparación muestra una diferencia, no su causa: la convención horaria, el procesamiento o el redondeo podrían influir, pero aquí no se han aislado. Ambos productos derivan de MERRA-2, así que no constituyen validación observacional independiente.

Quedan pendientes la inspección del gránulo NASA original MERRA-2, el archivo nativo GLDAS, el análisis de calidad y el contraste independiente.


## IMERG mensual: campos de calidad de la muestra

Se volvieron a leer los campos del gránulo IMERG de enero de 2010 en la misma caja rectangular (21 000 celdas) y en la celda cercana a Wagga Wagga. Se excluyeron valores no finitos y el `_FillValue` declarado por cada campo; los 21 000 valores de cada uno de los cuatro campos inspeccionados permanecieron válidos bajo ese filtro. El resultado es una comprobación de integridad básica, no una certificación de precisión ni una máscara de cuenca.

| Campo | Unidad / interpretación | Celda cercana a Wagga | Mínimo–máximo de la caja |
| --- | --- | ---: | ---: |
| `precipitation` | tasa, mm/h | 0,008 | 0,001–0,300 |
| `randomError` | estimación de error aleatorio, mm/h | 0,001 | 0,001–0,046 |
| `gaugeRelativeWeighting` | peso relativo de pluviómetros, % | 99 | 0–99 |
| `precipitationQualityIndex` | número equivalente de pluviómetros por caja de 2,5° × 2,5° | 344,65 | 2,89–636,78 |

La [documentación técnica NASA IMERG V07](https://gpm.nasa.gov/sites/default/files/2023-07/IMERG_TechnicalDocumentation_final_230713.pdf), tabla 2 y apartado «Quality Index for Monthly Data», define el índice mensual como un número **equivalente**, no como el conteo real de estaciones; aborda error aleatorio, no sesgo. Los rangos sugeridos por NASA para este índice mensual no son los de su índice de media hora: no debe recortarse a `[0,1]` ni confundirse con una probabilidad. La documentación también expone supuestos y limitaciones del campo `randomError`. No se ha fijado un umbral de rechazo ni se ha validado la precipitación contra observaciones independientes.


## Contraste exploratorio con una estación BoM

La [ficha de estación BoM 072150](https://www.bom.gov.au/clim_data/cdio/metadata/pdf/siteinfo/IDCJMD0040.072150.SiteInfo.pdf) ubica Wagga Wagga AMO en `147.4575,-35.1583`. Esta posición cae dentro de la celda IMERG con centro aproximado `147.45,-35.15` y límites `147.4–147.5,-35.2–-35.1`; se ha usado la ubicación de la estación, no el punto Wagga aproximado empleado en el ejemplo anterior.

Para enero de 2010, el [resumen mensual BoM publicado el 1 de febrero](https://www.bom.gov.au/climate/current/month/nsw/archive/201001.summary.shtml) informa **7,0 mm** de lluvia en Wagga Wagga AMO y advierte que el resumen no se actualiza normalmente tras su publicación. En la celda que contiene la estación, IMERG declara **0,009 mm/h**, equivalente aritméticamente a **6,696 mm** para 744 horas; la diferencia es −0,304 mm frente al dato publicado de estación. El archivo informa en esa celda `randomError=0,001 mm/h`, `gaugeRelativeWeighting=99%` y `precipitationQualityIndex=349` equivalentes por caja de 2,5°.

Es una comparación exploratoria de un mes, una medición puntual y una estimación promedio de celda. El mes de IMERG es UTC y no se ha comprobado el cierre horario del acumulado BoM, ni la versión definitiva, calidad, condiciones de lectura o contribución de esta estación a la corrección por pluviómetros IMERG. Por tanto no se afirma independencia ni se infiere precisión general, sesgo o desempeño del producto. Antes de usarlo como validación se requieren datos de estación con control de calidad y períodos y representatividad alineados.


## IMERG: gránulo de enero de 2005 identificado en Work

NCAR GDEX ofrece también `3B-MO.MS.MRG.3IMERG.20050101-S000000-E235959.01.V07B.HDF5`, el mismo identificador indicado en Work. Se descargó el 2026-11-14: 18 028 945 bytes y SHA-256 `bac3b9bc5ee8cc3eb1e5fe844778d54fd86e2b722813055b37f3872e6e4c73d5`. La cabecera coincide con el [registro NASA CMR G2823464479-GES_DISC](https://cmr.earthdata.nasa.gov/search/concepts/G2823464479-GES_DISC.umm_json) en identificador, fechas, versión, fecha de producción y tamaño; declara DOI `10.5067/GPM/IMERG/3B-MONTH/07`. CMR no ofreció un checksum en ese registro y no contamos con un hash del gránulo dentro de E01: **no se ha demostrado identidad byte a byte con el archivo de NASA o la evidencia original de Work**. La descarga NCAR queda en caché ignorada por Git.

La inspección directa confirma `Grid/precipitation` con dimensiones `(1,3600,1800)`, unidades `mm/hr` y `_FillValue=-9999.9`; el campo temporal declara `calendar=julian`. Dentro de la caja 138–153° E y 38–24° S hay 21 000 valores finitos distintos del fill, entre 0 y 0,372 mm/h. Es una caja rectangular, no una máscara de cuenca. La celda que contiene la estación Wagga Wagga AMO registra 0,041 mm/h; multiplicado por 744 horas equivale a 30,504 mm, sujeto a las salvedades de tiempo y calidad ya indicadas. Sus campos asociados son `randomError=0,002 mm/h`, peso de pluviómetros `99%` e índice de calidad `193,66` equivalentes por caja de 2,5°. No se ha contrastado este dato de enero de 2005 con una observación de estación validada.

## Horario de las observaciones de lluvia BoM

La [documentación de lluvias BoM](https://www.bom.gov.au/climate/cdo/about/about-rain-data.shtml) indica que las observaciones diarias se registran nominalmente a las 9:00 de la hora local y abarcan las 24 horas anteriores; también explica posibles acumulaciones que cruzan el mes y diferencias históricas entre hora estándar y hora de reloj. Esto refuerza la necesidad de verificar los intervalos efectivos de la estación y del producto mensual concreto antes de comparar su total con un mes UTC de IMERG. No se ha demostrado que las ventanas específicas del resumen de 2010 coincidan.


## Acceso a la serie mensual de la estación

El 2026-11-14 se intentó consultar la serie mensual de lluvia BoM para la estación 072150 mediante la URL de Climate Data Online (`p_nccObsCode=139`). La respuesta fue HTTP 403 con un mensaje que identifica posible acceso automatizado y pide detener ese tipo de solicitud. Se respetó la restricción y no se realizaron intentos adicionales de acceso automatizado a ese servicio. La respuesta recomienda consultar los canales oficiales de distribución; no demuestra inexistencia de la serie ni impide que un usuario la consulte manualmente según las condiciones aplicables. No se obtuvo el dato de enero de 2005 ni se puede verificar aún su calidad o alineación temporal.


## GLDAS 2.1: revisión de procedencia y máscara histórica

La [ficha NASA de GLDAS Noah mensual 0,25° V2.1](https://data.nasa.gov/dataset/gldas-noah-land-surface-model-l4-monthly-0-25-x-0-25-degree-v2-1-gldas-noah025-m-at-ges-di-23acd) distingue una producción principal, que incorpora el forzante combinado con GPCP 1.3 cuando está disponible, de una producción temprana que todavía no lo incorpora. La ficha corresponde a la producción principal. No se debe completar una serie mezclando ambas producciones sin registrar la procedencia y evaluar el efecto del cambio de forzantes. El producto 2.1 es `open-loop` (sin asimilación de datos en esa ejecución); esto no significa que sus forzantes no incluyan observaciones.

El [manual original NASA GLDAS-2](https://docserver.gesdisc.eosdis.nasa.gov/public/project/hydrology/README_GLDAS2.pdf) y el [aviso GES DISC de posprocesamiento](https://forum.earthdata.nasa.gov/viewtopic.php?t=659) indican que en octubre de 2020 se aplicó la máscara MOD44W a salidas de modelo GLDAS-2 para excluir valores inválidos sobre aguas continentales; las variables de forzamiento meteorológico no se modificaron con ese proceso. NASA recomienda volver a descargar las copias anteriores a noviembre de 2020. Antes de aceptar una muestra histórica debe comprobarse su linaje y procesamiento: la fecha científica del mes no es la fecha de obtención o de posprocesamiento del archivo. No se ha abierto todavía un archivo GLDAS y esta advertencia no prueba el estado de una copia concreta.


## Comprobación espacial IMERG–MDBA

Se ensayaron los límites y centros del gránulo IMERG de enero de 2005 contra el polígono oficial MDBA: 10 092 centros cubiertos y 10 467 celdas que intersectan, con 747 celdas parcialmente cubiertas. El método, hash de geometría, predicados y limitaciones están en [region_murray_darling.md](region_murray_darling.md#prueba-espacial-de-una-muestra-imerg). Esta prueba no es una serie ni una validación independiente de los valores de precipitación.


La [prueba de sensibilidad espacial](region_murray_darling.md#sensibilidad-exploratoria-de-los-bordes) comparó cuatro formas de tratar bordes en una fecha. Detectó también solapamientos y separaciones muy pequeños en los límites `float32` declarados por el archivo, y una diferencia de cierre de área; la máscara y ponderación definitiva siguen pendientes.


Una [repetición con límites regularizados y proyección equivalente](region_murray_darling.md#ensayo-de-cierre-con-grilla-regular-y-proyección-equivalente) consiguió cierre interno cercano a precisión numérica. Es una prueba exploratoria; no atribuye la diferencia anterior a una sola causa ni valida una máscara de producción.


## Enunciado oficial: resultado indexado y límite de acceso

El 2026-11-14 una búsqueda devolvió un extracto indexado de la [URL pública del desafío](https://www.spaceappschallenge.org/2026/challenges/earth-system-trend-detective/) que describe una herramienta para elegir variables de ciencias de la Tierra medidas por misiones o modelos, visualizarlas en el tiempo y evaluar qué cambia, dónde, cuánto y su significancia. Al intentar abrir esa URL desde el entorno, el servidor siguió devolviendo HTTP 502; por tanto solo se contrastó ese extracto indexado, no el contenido completo, la pestaña Resources ni la versión actual íntegra.

El extracto indexado visible usa una formulación general de misiones y modelos de ciencias de la Tierra. La [versión de staging previamente revisada](https://staging-web-v2.spaceappschallenge.org/2026/challenges/earth-system-trend-detective2/) menciona explícitamente misiones y modelos NASA y ofrece más contexto. La diferencia entre el extracto y staging no prueba que la página pública completa permita o excluya otros orígenes: podría existir texto adicional no visible en el índice. No se atribuyen a producción los detalles exclusivos de staging. Conviene mantener trazabilidad de los datos NASA y verificar el enunciado completo y sus recursos cuando puedan consultarse sin retrasar el trabajo autorizado.


## Reproducir la lectura de las muestras

Desde la raíz del repositorio, `python research/validar_muestras_ful102.py` verifica los SHA-256 de las dos muestras IMERG y la copia MERRA-2 documentadas, revisa dimensiones y unidades, comprueba que la celda IMERG seleccionada contiene la estación y emite las tasas y conversiones en JSON. Requiere `h5py` y `numpy`, ya declarados en `pyproject.toml`, y los archivos en `data/cache/ful-102`; `--cache` permite indicar otra carpeta. El programa no descarga ni modifica datos. El hash comprueba que se utiliza la misma copia NCAR revisada, no su igualdad criptográfica con los gránulos de NASA. Es una prueba limitada a esas muestras y coordenadas; no reproduce la máscara regional ni certifica calidad o significancia.


## Estado de transición IMERG V08

La [actualización NASA del 6 de agosto de 2026](https://gpm.nasa.gov/data/news/update-imerg-v08-transition-schedule-aug-2026) modificó la previsión anterior: el equipo esperaba V08 Final más probablemente en el otoño boreal de 2026, sujeto a la disponibilidad y comportamiento de productos de entrada; Early y Late se proyectaban para no antes del invierno boreal. Era una **previsión**, no una confirmación de lanzamiento. Mientras tanto, NASA describe Early y Late V07 como procesamiento híbrido, con posibles discontinuidades; no son una extensión intercambiable de Final V07.

Como comprobación puntual, el 2026-11-14 a las 18:00:40 UTC la [consulta CMR por `short_name=GPM_3IMERGM` y `version=08`](https://cmr.earthdata.nasa.gov/search/collections.umm_json?short_name=GPM_3IMERGM&version=08&page_size=100) respondió HTTP 200 con `CMR-Hits=0`. Esto solo describe esa búsqueda exacta en ese momento: no demuestra que no exista V08 con otro identificador, proveedor o en otro sistema, ni que el pronóstico siga vigente. No unir versiones o tipos de procesamiento sin documentar cambios y validar continuidad.


El notebook público NASA recuperado contiene nueve celdas Markdown y ocho de código; explica un ejemplo de series de Giovanni y la obtención de token mediante Earthdata Login. Se inspeccionó su estructura sin ejecutar la autenticación. Es un tutorial externo identificado en Work, no un script personalizado del paquete E01. La respuesta POWER obtenida posteriormente conserva 944 bytes como la original pero tiene SHA-256 distinto (`afb8592c6d5cf7e348e5a5512febb42cf782a54c29f0c849c916e1789a0303a0` frente a `b047382d9fa98e149a739c5440dee87cb8d916caf537c028d29eb529f3eefbc7`); la igualdad de tamaño por sí sola no prueba identidad; la reconstrucción posterior confirma que el campo `times.data` era diferente.


## Respuestas completas recuperadas de Giovanni y AppEEARS

Las siete respuestas anteriores coinciden en tamaño y SHA-256 con las filas 7, 9, 11, 29, 30, 31 y 32 de Work. Por ello se puede leer el cuerpo íntegro registrado en esas filas; esto no recupera las demás respuestas truncadas ni los scripts del ZIP. Los resultados siguientes son metadatos, no archivos científicos procesados ni tareas autenticadas.

- `configured-variables` contiene 867 identificadores: incluye exactamente `GLDAS_NOAH025_M_2_1_SoilMoi0_10cm_inst` y `GPM_3IMERGM_07_precipitation`. No incluye `M2TMNXSLV_5_12_4_T2M` ni otra entrada con `M2TMNXSLV`; sí aparecen identificadores de otras colecciones MERRA. Esto no demuestra ausencia del producto mensual en otros servicios y no autoriza a sustituir silenciosamente una colección por otra.
- Para MOD11A2.061, la respuesta AppEEARS declara `LST_Day_1km`, unidades K, factor 0,02, valor faltante original 0 y capa de calidad `QC_Day`. Para MOD13A3.061, declara `_1_km_monthly_NDVI`, factor 0,0001, fill −3000 y capa `_1_km_monthly_VI_Quality`. Registrar el tipo y escala de la entrega concreta: AppEEARS también declara tipo de salida `float32`, y no se ha comprobado en una descarga si la escala ya fue aplicada. No aplicar el factor dos veces ni tratar la temperatura superficial MODIS como aire a 2 m.


## Inventario AppEEARS recuperado: productos candidatos

La respuesta íntegra `appeears_products` recuperada con el SHA-256 de Work contiene 193 elementos. Al buscar por el campo `Product` exacto y leer `Version`, `Available` y `Deleted`, la respuesta incluye una entrada disponible y no eliminada para cada uno de `MOD11A2.061`, `MOD13A3.061`, `MOD16A2GF.061`, `SPL3SMP.009` y `SPL4SMGP.008`. No contiene entradas cuyo `Product` sea exactamente `MOD11C3`, `M2TMNXSLV`, `GPM_3IMERGM` o `GLDAS_NOAH025_M`. Son resultados de esa respuesta registrada el 2026-11-14, no una garantía futura ni una búsqueda por alias.

En particular, la ausencia de MOD11C3 en este catálogo concuerda con el HTTP 404 registrado por Work para la ruta de capas `MOD11C3.061`; no significa que el producto no exista en NASA. MOD11A2 es un producto distinto, de ocho días, y no reemplaza automáticamente el producto mensual MOD11C3. La disponibilidad de un registro tampoco prueba cobertura efectiva en una región, calidad ni éxito de una tarea de extracción autenticada. La fuente completa se conserva en `data/cache/ful-102/appeears_products.repeat.json`, ignorada por Git.

La respuesta AppEEARS además declara `TemporalGranularity=Daily` para `SPL4SMGP.008`, mientras que [NSIDC describe el producto SPL4SMGP V8](https://nsidc.org/data/spl4smgp/versions/8) con resolución temporal de tres horas. Son descripciones en dos niveles o servicios distintos; no se ha probado qué intervalos devuelve una extracción AppEEARS ni se debe inferir que el producto original sea diario o que AppEEARS preserve todos los intervalos. El equipo debe comprobar las marcas de tiempo de una entrega real antes de usarla.


## Lluvia de estación mediante NOAA GHCN-Daily

NOAA publica la [serie GHCN-Daily ASN00072150](https://www.ncei.noaa.gov/pub/data/ghcn/daily/all/ASN00072150.dly), identificada en su inventario como WAGGA WAGGA AMO (`−35.1583,147.4573`, 212 m, WMO 94910). El archivo consultado el 2026-11-14 tiene 1 098 090 bytes y SHA-256 `20715522da8333f1da5c0d715ca30f46341181dee1914d23480dd9f08c412761`; se conserva en caché ignorada y puede cambiar con actualizaciones. Las coordenadas de NOAA y BoM difieren ligeramente y ambos puntos caen en la misma celda IMERG seleccionada.

Según el [formato y banderas NOAA](https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt), `PRCP` está en décimas de mm, `−9999` indica ausencia, QFLAG vacío indica que no falló controles y SFLAG `a` identifica origen BoM. Para enero de 2005 y enero de 2010, los 31 valores de cada mes están presentes, con QFLAG y MFLAG vacíos y SFLAG `a`. Las sumas de esas fechas son **13,2 mm** y **7,0 mm**, respectivamente. El valor de 2010 coincide con el resumen provisional BoM consultado; ambas fuentes remiten al mismo organismo y no constituyen observaciones independientes entre sí.

La celda IMERG que contiene la estación da tasas mensuales equivalentes a 30,504 mm (2005) y 6,696 mm (2010), diferencias de +17,304 mm y −0,304 mm frente a las respectivas sumas de estación. Estas son comparaciones descriptivas de solo dos meses: no comprueban sesgo o desempeño general, ni independencia de la estación respecto a los pluviómetros incorporados en IMERG. Además, una celda representa un área y la estación un punto; no se han alineado las ventanas diarias locales de observación con el mes UTC del producto. Las banderas vacías no garantizan ausencia total de errores. Para publicar o redistribuir los datos, revisar las condiciones aplicables a NOAA y al proveedor de origen.


## IMERG y estación: doce meses de 2005

Se amplió la comparación exploratoria a los doce gránulos mensuales V07B de 2005 de [NCAR GDEX](https://gdex.ucar.edu/datasets/d736000/filelist/1/) y la misma estación NOAA GHCN-Daily `ASN00072150`. En cada HDF5 se verificaron identificador en el inventario CMR guardado, versión declarada, dimensiones `(1,3600,1800)`, unidades `mm/hr` y valor finito diferente de `_FillValue` para la celda que contiene la estación. Se multiplicó cada tasa por las horas del mes; se sumaron los valores diarios de estación en décimas de mm. Los 365 días figuran presentes, con banderas MFLAG y QFLAG vacías y fuente BoM `a`. El detalle reproducido, con nombre, concept ID, SHA-256 y banderas por mes, se conservó en `data/cache/ful-102/comparison_imerg_station_2005.json`; los gránulos también se encuentran en caché ignorada. La correspondencia por metadatos con CMR no verifica la igualdad byte a byte con NASA.

| Mes de 2005 | Estación (mm) | IMERG celda (mm) |
| --- | ---: | ---: |
| Enero | 13,2 | 30,50 |
| Febrero | 46,8 | 67,20 |
| Marzo | 6,6 | 15,62 |
| Abril | 14,6 | 14,40 |
| Mayo | 4,6 | 2,23 |
| Junio | 69,0 | 119,52 |
| Julio | 65,0 | 63,24 |
| Agosto | 56,4 | 81,10 |
| Septiembre | 85,0 | 100,80 |
| Octubre | 77,6 | 76,63 |
| Noviembre | 44,8 | 43,92 |
| Diciembre | 29,4 | 38,69 |

La suma de los doce valores sin redondear es aproximadamente **513,0 mm** en la estación y **653,856 mm** en la celda. IMERG supera el valor puntual en siete meses y queda por debajo en cinco; junio concentra la mayor diferencia positiva, de aproximadamente 50,52 mm. Estos resultados describen un sitio y un año, no una evaluación estadística ni un sesgo general. Permanecen sin resolver las distintas ventanas temporales, la representatividad espacial, la calidad específica y la posible incorporación de la estación en el análisis de pluviómetros usado por IMERG. No se califican como validación independiente ni como prueba de que alguno de los productos sea erróneo.


## Junio de 2005: estaciones cercanas

Para examinar la variación espacial, se consultaron en el inventario GHCN-Daily de NOAA las nueve estaciones más cercanas a Wagga Wagga AMO dentro de la caja exploratoria `147.15–147.75 E, 35.40–34.90 S`, además de la estación original. De esas nueve, tres tienen los 30 valores diarios `PRCP` presentes en junio de 2005, con MFLAG y QFLAG vacíos y SFLAG `a` (BoM); otras dos tienen solo 28 y 24 días y cuatro no tenían fila PRCP de ese mes. Se excluyeron los dos totales incompletos. La posición de cada estación se comparó con los límites de la celda IMERG que la contiene.

| Estación NOAA | Precipitación diaria sumada (mm) | Celda IMERG correspondiente (mm) |
| --- | ---: | ---: |
| `ASN00072150`, Wagga Wagga AMO | 69,0 | 119,52 |
| `ASN00072138`, Ladysmith (Tywong Street) | 87,8 | 124,56 |
| `ASN00074127`, Wagga Wagga (Gurwood Street) | 78,0 | 117,36 |
| `ASN00072040`, Wagga Wagga (Berrillee) | 100,4 | 118,80 |

Los cuatro totales puntuales varían 31,4 mm y los cuatro valores de celda son mayores que su respectivo total puntual. El resultado describe un solo mes y cuatro estaciones cercanas, con ventanas locales aún no alineadas con UTC. Puede haber dependencias entre las observaciones usadas por IMERG y BoM; no se ha comprobado si esas estaciones integran el análisis GPCC. La selección no es una muestra estadística representativa y no permite atribuir diferencias ni establecer sesgo. Los archivos GHCN se guardaron en caché ignorada; sus SHA-256 son `20715522da8333f1da5c0d715ca30f46341181dee1914d23480dd9f08c412761` (72150), `a3e44746a91b9f479c39b65fb8b5c5ed29083bb0e2dea126e6713f64cbbc5328` (72138), `c0befda49578f23938ce6fb77cf084e96428bb5dffc18f1d4ae15631c730300d` (74127) y `66203bc17f08869011188ed67c21250b1f9a633bcc6e1db072fd9402a42579ef` (72040).


## Lluvia en torno al límite junio–julio de 2005

Para examinar el posible efecto de los cortes temporales, se leyeron los registros diarios GHCN de las mismas cuatro estaciones alrededor del límite de mes. Wagga Wagga AMO registra 6,6 mm el 30 de junio, 12,6 mm el 1 de julio y 8,0 mm el 2 de julio; las otras tres estaciones registran respectivamente 4,6–8,6 mm, 6,4–13,2 mm y 1,8–6,4 mm en esas fechas. Todas esas lecturas tienen banderas MFLAG/QFLAG vacías y SFLAG `a`. En torno al comienzo del mes, las cuatro estaciones registran entre 0 y 1 mm el 1 de junio y 0 mm el 2 de junio.

Esto demuestra que hubo lluvia cerca del corte junio–julio, de modo que la alineación temporal merece comprobarse. Los datos diarios no indican la hora exacta de la lluvia ni establecen la ventana concreta que aplicó GHCN a cada estación; tampoco delimitan la variación en toda la celda. No se puede, con estas cifras, calcular cuánto de la diferencia IMERG–estación se explica por el horario, ni asumir que el evento coincida con el borde UTC. Para hacerlo se necesitarían intervalos subdiarios con horarios y procedencia verificados.


Para reproducir la tabla anterior desde la raíz del repositorio, `python research/comparar_imerg_estacion_2005.py` lee las doce muestras y el archivo NOAA desde `data/cache/ful-102` (o la ruta indicada mediante `--cache`), verifica sus SHA-256 y rechaza meses incompletos, banderas inesperadas, valores faltantes o una celda que no contiene la estación. Emite JSON sin realizar descargas ni modificar archivos. Requiere las dependencias `numpy` y `h5py` ya declaradas. Los hashes fijan las copias concretas usadas aquí: una actualización válida de un archivo NOAA requeriría revisarla antes de cambiar el hash. Esta verificación reproduce el cálculo, pero no alinea las ventanas horarias ni demuestra independencia o precisión.


## Conflicto de unidades en metadatos AppEEARS de SMAP L4

El 2026-11-14 se consultó la respuesta completa de [capas AppEEARS `SPL4SMGP.008`](https://appeears.earthdatacloud.nasa.gov/api/product/SPL4SMGP.008): HTTP 200, 30 401 bytes, SHA-256 `2ebbcf46cd368d447b756dc4ada99896c41f97a7d572ef35fb29f0a83864f3d3`, guardada en caché ignorada. Es una consulta nueva y no se atribuye al paquete Work. Contiene 45 capas. Para `Geophysical_Data_sm_surface` declara `m^3/m^3` y capa 0–5 cm; para `Geophysical_Data_sm_rootzone` declara la misma unidad y 0–100 cm.

Se detectó un **conflicto** en `Geophysical_Data_sm_profile`: la API AppEEARS describe humedad del perfil pero informa `Units: W/m^2`, mientras la [especificación NSIDC/GMAO V8, versión 1.7](https://nsidc.org/sites/default/files/documents/technical-reference/smap_l4_sm_psd_v17_for_l4sm_version_8.pdf), tabla 9 y descripción de `sm_profile`, indica `m³/m³`. Son unidades físicamente distintas. No se ha abierto un gránulo o entrega AppEEARS para determinar el origen del conflicto ni si afecta el atributo del archivo generado; no usar automáticamente esa etiqueta ni corregir datos por suposición. Contrastar el atributo de una muestra real y la documentación del proveedor antes de aplicar transformaciones o publicar.

El [anuncio LP DAAC de julio de 2025](https://forum.earthdata.nasa.gov/viewtopic.php?t=6976) confirma que AppEEARS incorporó la versión 008; no aclara las marcas de tiempo de su extracción. La diferencia entre la granularidad `Daily` del catálogo y el intervalo de tres horas documentado por NSIDC continúa sin resolver mediante muestras.


Al contrastar también campos de nieve de la misma respuesta AppEEARS apareció un segundo conflicto: `Geophysical_Data_snow_mass` declara `kg/m^2/s`, mientras la tabla 9 de la especificación NSIDC/GMAO V8 indica `kg/m²` para masa de nieve. En cambio, para `snow_melt_flux` ambas referencias indican una tasa en `kg/m²/s`. Confundir masa con flujo puede producir conversiones temporales incorrectas. Como antes, esta comparación identifica una discrepancia **entre metadatos**: no hemos examinado un archivo de salida AppEEARS ni determinado si el dato o su atributo final están afectados.


## Comparación de unidades: 45 capas SMAP L4

Se cotejaron por nombre las 45 capas de la respuesta AppEEARS `SPL4SMGP.008` con las 45 variables geofísicas de la [tabla 9 de la especificación NSIDC/GMAO V8](https://nsidc.org/sites/default/files/documents/technical-reference/smap_l4_sm_psd_v17_for_l4sm_version_8.pdf), páginas impresas 47–50. El cotejo cubre solo el **campo de unidades de metadatos**, no datos ni calidad. Para comparar se reconocieron escrituras equivalentes como `kg/m^2/s` y `kg m⁻² s⁻¹`, sin transformar valores.

- **35 capas:** la unidad declarada en AppEEARS coincide con la unidad de la tabla bajo esa normalización.
- **Dos capas:** `sm_profile` y `snow_mass` presentan los conflictos detallados arriba.
- **Ocho capas:** AppEEARS deja `Units` vacío mientras la especificación indica que son adimensionales: las cuatro fracciones de superficie, los tres campos `sm_*_wetness` y `vegetation_greenness_fraction`. Un campo vacío no identifica por sí solo una unidad; para interpretarlo se requiere la documentación de la variable.

Esta comparación se realizó con la respuesta de 30 401 bytes y SHA-256 indicado arriba. No prueba que la entrega descargada conserve esas etiquetas ni que sus píxeles sean correctos. Tampoco resuelve la discrepancia de granularidad temporal.


## Consistencia interna de los inventarios CMR

Se inspeccionaron íntegramente las entradas de las tres respuestas CMR repetidas para 2005–2025 guardadas en caché: 252 de MERRA-2, 249 de IMERG y 252 de GLDAS. Para cada registro se contrastaron el año y mes de `time_start` con el nombre del gránulo, el inicio en el día 1, el final en el último día del mismo mes y el sufijo `.nc4`, `.V07B.HDF5` o `.021.nc4`, según la colección. Se verificó además que ninguna clave de mes se repitiera. Bajo esas comprobaciones no se detectaron inconsistencias en las entradas obtenidas.

La prueba solo comprueba metadatos y el día de inicio y fin: no verifica horas exactas, contenidos, continuidad espacial, calidad o que cada descarga funcione. Como se documentó antes, faltan los tres meses de octubre a diciembre de 2025 en la respuesta IMERG V07; tampoco se dispone del cuerpo original Work para comparar los inventarios byte a byte.


## MOD11A2: precaución con el valor cero en QA

La respuesta AppEEARS `MOD11A2.061` recuperada con el hash de Work informa `FillValue=0` y rango original 0–255 para `QC_Day` y `QC_Night`. La [guía LP DAAC MOD11](https://lpdaac.usgs.gov/documents/715/MOD11_User_Guide_V61.pdf), tabla de capas MOD11A2, indica rango 0–255 y deja el fill de ambas capas QA como no aplicable; su tabla de bits describe `00` en los bits 0–1 como LST producida con buena calidad. Para la capa **LST**, en cambio, la misma guía sí identifica cero como fill y factor 0,02 K.

Por tanto, aplicar ciegamente el fill declarado por la API al campo de bits QA podría eliminar valores de QA válidos. Existe un conflicto de metadatos que debe comprobarse en un resultado concreto de AppEEARS antes de decidir cómo leer su máscara; no se ha ejecutado una tarea ni se afirma que su archivo de salida enmascare realmente los ceros. Separar el fill de LST de la interpretación de sus bits QA y contrastar los atributos del archivo entregado. La escala y el offset pueden estar ya aplicados por el servicio y también requieren comprobación.


## Respuesta CMR V08 reconstruida desde la planilla

La celda G26 de «Pruebas técnicas» contiene íntegra la representación Python de la respuesta JSON de 203 bytes, a diferencia de los inventarios largos cortados a 400 caracteres. Se interpretó esa representación de forma literal y se serializó como JSON compacto; el resultado tiene SHA-256 `e870d178068497c00593adb0210141b42281ea94d24ed9a60c354ca7542704a9`, idéntico al registrado en I26. La coincidencia de tamaño y hash demuestra la recuperación byte a byte de **esa respuesta concreta** de Work, no del ZIP completo. La copia reconstruida se conserva en `data/cache/ful-102/work_reconstructed_row_26.json`, ignorada por Git.

La respuesta original contiene una lista `entry` vacía para la consulta exacta `GPM_3IMERGM`, versión `08`, en el momento registrado. Esto respalda solo esa consulta y no una conclusión sobre otras colecciones o disponibilidad posterior. Se intentó el mismo procedimiento con otras representaciones literales completas de la hoja que tienen tamaño y SHA registrados; únicamente G26 pudo interpretarse y reproducirse exactamente. Las demás respuestas siguen sin recuperarse por este método.


## Obtener de nuevo las muestras para los scripts

Los datos no están versionados en Git. Para ejecutar las comprobaciones en otro equipo, se necesitan estas copias en una carpeta local (por defecto `data/cache/ful-102`):

1. **IMERG:** desde el [listado NCAR GDEX](https://gdex.ucar.edu/datasets/d736000/filelist/1/), obtener los doce gránulos mensuales de 2005 y el de enero de 2010 que figuran en este documento. Guardar cada uno como `imerg_AAAAMM_v07b_ncar.h5`, por ejemplo `imerg_200501_v07b_ncar.h5`. Son archivos HDF5 completos; la extensión local no cambia su contenido.
2. **MERRA-2:** desde el [listado NCAR de 2005](https://gdex.ucar.edu/datasets/d927358/filelist/26/), obtener `T2M_MERRA2_asm_mon_200501_200512.nc4` y guardarlo como `merra2_t2m_2005_ncar.nc4`. Es la copia anual reorganizada de NCAR.
3. **Estación:** obtener [ASN00072150.dly de NOAA](https://www.ncei.noaa.gov/pub/data/ghcn/daily/all/ASN00072150.dly) y guardarlo como `noaa_ghcnd_ASN00072150.dly`. NOAA puede actualizar este archivo, por lo que una versión posterior puede fallar el hash aun siendo válida; revisarla antes de actualizar los valores esperados.

Después, ejecutar `python research/validar_muestras_ful102.py`, `python research/comparar_imerg_estacion_2005.py` y `python research/inspeccionar_imerg_caja_2005.py`, o pasar `--cache RUTA` a cada comando. Los tres verifican los hashes fijados antes de procesar; la comparación NOAA y la inspección de la caja necesitan los doce meses de 2005, mientras que la primera necesita enero de 2005, enero de 2010 y la copia MERRA. Las dependencias ya figuran en `pyproject.toml`. Estas pruebas no descargan datos, no validan el archivo GLDAS ni sustituyen la revisión científica del equipo.


## Consulta horaria NOAA para Wagga Wagga

Se consultó el inventario NOAA ISD y se identificó `949100-99999` como Wagga Wagga (`−35.165,147.466`; no se ha probado que toda su instrumentación histórica sea idéntica a la de GHCN). El [archivo NOAA Global Hourly de 2005](https://noaa-global-hourly-pds.s3.amazonaws.com/2005/94910099999.csv) recuperado el 2026-11-14 tiene 3 492 543 bytes y SHA-256 `ec8de79a28c182e60ef12b8ae02284a6340b8f28183e2ae1375813728e418983`; queda en caché ignorada. El enlace corresponde al depósito público al que remite el portal de NOAA.

Para junio se hallaron 815 registros meteorológicos, de los cuales 120 incluyen un campo `AA1`: 30 con período de 6 horas, 30 de 12, 30 de 18 y 30 de 24. Según el [formato ISD de NOAA](https://www.ncei.noaa.gov/pub/data/noaa/isd-format-document.pdf), la primera parte del campo indica duración de la precipitación, no una tasa horaria. De esas 120 entradas, 116 tienen código de calidad `1` y cuatro `9`; el código de condición también debe interpretarse. Por ejemplo, alrededor del 30 de junio aparecen acumulados de distinta duración. No se deben sumar directamente porque pueden solaparse.

Por tanto esta búsqueda **no proporcionó una serie continua de precipitación horaria** para alinear exactamente la comparación mensual. Se ha revisado solo este campo y período, sin descartar otras variables, fuentes o registros más detallados. Tampoco se ha establecido independencia de estos reportes respecto a GHCN o IMERG.


## Temperatura de estación y copia MERRA-2: 2005

El archivo NOAA GHCN-Daily `ASN00072150` ya identificado incluye `TAVG` en los doce meses de 2005. Cada mes contiene todos sus días, QFLAG vacío, MFLAG `H` y SFLAG `S`. Según el [README GHCN-Daily](https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt), `TAVG` está en décimas de °C, `H` indica promedio de valores horarios para temperatura y `S` identifica Global Summary of the Day derivado de reportes horarios. Es una fuente distinta del flag `a` de precipitación; no debe atribuirse automáticamente al mismo flujo.

Se promediaron los valores diarios publicados en cada mes y se compararon con `T2M` en la copia anual NCAR de MERRA-2, convirtiendo K a °C. El centro MERRA más cercano a la estación es aproximadamente `147.5,-35.0`, distinto de la posición puntual `147.4573,-35.1583`.

| Mes 2005 | Media de TAVG diaria estación (°C) | Celda MERRA-2 (°C) |
| --- | ---: | ---: |
| Enero | 24,455 | 25,281 |
| Febrero | 21,300 | 21,647 |
| Marzo | 19,658 | 19,687 |
| Abril | 18,643 | 19,093 |
| Mayo | 11,629 | 12,714 |
| Junio | 10,660 | 10,058 |
| Julio | 8,787 | 7,791 |
| Agosto | 8,903 | 8,187 |
| Septiembre | 11,417 | 11,256 |
| Octubre | 14,761 | 15,161 |
| Noviembre | 18,757 | 19,404 |
| Diciembre | 22,255 | 22,939 |

La estación contiene 365 valores diarios no faltantes y sin bandera de fallo, lo cual no demuestra que cada promedio use igual número de horas ni ausencia de errores. Las ventanas de tiempo, altura e intervalos de observación, representación espacial y eventual incorporación de datos a la reanálisis no se han alineado o establecido. Esta comparación de un solo punto y año es exploratoria; no constituye validación independiente ni evaluación general del producto NASA. La copia NCAR no es el gránulo original.


## Cobertura horaria de temperatura de estación

En el archivo NOAA Global Hourly `949100-99999` de 2005, cuya procedencia y hash constan arriba, se inspeccionó `TMP` solo en marcas exactamente a la hora, con valor presente y código de calidad `1`. Se contaron horas únicas de cada mes. Abril tiene **720 de 720** horas esperadas y sin duplicados en esa selección. Enero tiene 734 de 744, julio 725 de 744 y diciembre 722 de 744; agosto, septiembre y octubre presentan además marcas duplicadas con valores diferentes. Estos conteos no establecen que no haya otras observaciones fuera de la hora exacta ni cuál de los duplicados debe preferirse.

En abril, el promedio de las 720 temperaturas seleccionadas es **18,650 °C**, frente a **19,093 °C** en la celda mensual MERRA-2 de la copia NCAR cuyo centro es el más cercano a la estación. La [especificación ISD](https://www.ncei.noaa.gov/pub/data/noaa/isd-format-document.pdf) define la hora de observación en UTC. Esta prueba mejora la comparación temporal para un mes, pero sigue comparando observaciones puntuales horarias con un promedio de celda, sin confirmar equivalencia exacta de instrumentación, representación temporal ni independencia respecto al reanálisis. No extrapolarla al año completo ni interpretar las horas ausentes como cero; revisar fuente y calidad antes de resolver duplicados.


## Acceso a MERRA-2 en la nube

El [registro NASA MERRA-2 en AWS](https://registry.opendata.aws/nasa-merra-2/) identifica `M2TMNXSLV` como colección en almacenamiento S3 de **acceso controlado**. No se encontró en esta búsqueda una copia pública verificable del gránulo NASA mensual original que sustituya la extracción autorizada. La copia anual de NCAR ya analizada conserva su condición de producto reorganizado. Esta búsqueda no demuestra que no exista otra copia o vía de acceso; no se necesita esperar el gránulo para utilizar el catálogo y las evidencias disponibles.


## Reconstrucción de inventarios originales de GLDAS e IMERG

Las respuestas CMR repetidas para las filas 15 y 18 tenían el mismo tamaño registrado por Work. Se sustituyó únicamente `feed.updated` por la marca completa visible en cada celda original; los cuerpos resultantes coinciden exactamente con los SHA-256 de Work: `32c41a6f707d0f18c97f3c225726d40c1e295eb07f0b6eabeaa92bff2ece74f8` para GLDAS y `9b885524026ee0cf3985a6110834a846741995f03a9a9a74bde274418a0a1d22` para IMERG. La coincidencia verifica byte a byte cada respuesta reconstruida, incluidos sus inventarios completos de 2005–2025. Se conservan en `data/cache/ful-102/work_reconstructed_row_15.json` y `work_reconstructed_row_18.json`, ignorados por Git.

El mismo procedimiento **no** recuperó la respuesta MERRA-2 de la fila 21: la repetida tiene 957 072 bytes frente a 957 094 registrados por Work y el SHA-256 no coincide. No se infiere qué partes cambiaron ni se considera reconstruida. Una consulta adicional posterior volvió a producir 957.072 bytes y el mismo contenido JSON que la primera repetición al excluir `feed.updated`; esto confirma consistencia entre ambas consultas nuevas, pero no identifica los 22 bytes de diferencia con Work ni recupera su respuesta original. Ninguno de los 252 registros repetidos declara `updated` posterior a la consulta de Work; ese campo por sí solo no permite descartar cambios en la respuesta generada ni reconstruir los bytes faltantes. Como contraste adicional, se repitió la búsqueda con `revision_date[]=2026-11-14T05:08:46Z,` y los mismos filtros de colección, caja y período: CMR informó `CMR-Hits=0`. Según la [documentación de CMR](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html), ese filtro consulta la fecha de revisión de los registros actuales, distinta de su campo `updated`; no reconstruye automáticamente una respuesta histórica ni descarta cambios en registros eliminados o en la generación de enlaces. Estas reconstrucciones no recuperan el paquete E01 completo ni los scripts propios.

## Otras respuestas CMR reconstruidas

Se repitieron las consultas CMR de las filas 2–6, 13–14, 16–17, 19–20 y 22–25. En cada respuesta se sustituyó únicamente `feed.updated` por la marca completa visible en la celda de Work. Las quince reconstrucciones coinciden en tamaño y SHA-256 con la hoja; sus identificadores y hashes figuran en la tabla inicial y las copias están en la caché local ignorada. Son respuestas de metadatos, no gránulos científicos ni el ZIP de evidencia.

La inspección de las quince respuestas recuperadas confirma una entrada en cada una: cinco colecciones y diez consultas de extremos de gránulos. En las respuestas originales de Work, los últimos registros consultados son GLDAS julio de 2026, IMERG septiembre de 2025, MERRA-2 septiembre de 2026, SMAP L3 12 de noviembre de 2026 y SMAP L4 10 de noviembre de 2026. En el último caso, el nombre contiene `T223000` y `time_start` es `21:00 UTC`. La [guía NSIDC SMAP L4 V8](https://nsidc.org/sites/default/files/documents/user-guide/multi_spl4smau-v008-userguide.pdf), tabla de nombres de archivos, especifica que la marca de los archivos `gph` representa el punto central del intervalo promedio de tres horas. Por tanto, la marca `22:30` es coherente con un intervalo de 21:00 a 00:00 UTC y con el inicio declarado; esto interpreta los metadatos, sin abrir el archivo. Estos extremos no prueban continuidad ni calidad.

### Auditoría reproducible de respuestas reconstruidas

El script [`research/auditar_respuestas_cmr_work.py`](../research/auditar_respuestas_cmr_work.py) vuelve a comprobar tamaño y SHA-256 de las 18 respuestas CMR reconstruidas frente a `pruebas_work.csv`, lee sus JSON y comprueba la identidad de las cinco colecciones. Para los dos inventarios reconstruidos contabiliza meses y duplicados en los registros: GLDAS contiene 252 meses distintos entre 2005 y 2025, sin faltantes ni duplicados; IMERG contiene 249, faltan octubre–diciembre de 2025 y no hay meses duplicados. Ejecutar desde la raíz con `python research/auditar_respuestas_cmr_work.py`; requiere las respuestas en la caché local ignorada. Con `python research/auditar_respuestas_cmr_work.py --todas` se verifican también las 35 copias individuales que el manifiesto marca con hash coincidente, incluidos documentos y archivos no JSON; esta opción requiere que estén en la caché indicada. La opción `--merra-repetida` verifica aparte el hash de la consulta MERRA-2 repetida y reproduce sus 252 meses distintos, sin faltantes ni duplicados para 2005–2025; su salida advierte que no es la respuesta original de Work. La verificación no sustituye inspección de grillas ni pruebas de calidad.

## Cobertura de las doce muestras IMERG de 2005 en la caja

El script [`research/inspeccionar_imerg_caja_2005.py`](../research/inspeccionar_imerg_caja_2005.py) comprueba los hashes de las doce copias NCAR y examina los centros de celda en la caja 138–153° E, 38–24° S. En cada mes encontró 21.000 celdas, todas finitas y distintas del `_FillValue`; ninguna tasa observada fue negativa. Las tasas máximas mensuales dentro de la caja variaron entre 0,201 mm/h en abril y 0,408 mm/h en junio. El resultado se reproduce con `python research/inspeccionar_imerg_caja_2005.py` y requiere las muestras locales ignoradas y las dependencias del proyecto.

Esta prueba es de presencia y rangos básicos: la caja incluye áreas fuera de la cuenca y no se aplicaron máscara regional ni filtros de calidad. Que un valor sea finito y distinto del fill no demuestra precisión ni calidad científica; tampoco se comprueba la identidad binaria de las copias NCAR con NASA. Los resultados se limitan a esos doce meses.

## Cobertura mensual de la copia MERRA-2 en la caja

Se amplió [`research/validar_muestras_ful102.py`](../research/validar_muestras_ful102.py) para revisar los doce tiempos y las celdas cuyos centros caen en la misma caja rectangular de 138–153° E y 38–24° S. En la copia anual reorganizada por NCAR, se encontraron 24 longitudes por 29 latitudes (696 celdas) por mes: todas las temperaturas `T2M` fueron finitas y distintas del `_FillValue`. Los mínimos y máximos por mes en la caja, convertidos de K a °C, abarcan desde 2,95 °C en julio hasta 34,41 °C en diciembre. Se verificaron también los doce desplazamientos mensuales del eje de tiempo y sus unidades y calendario declarados.

Esta es una comprobación de presencia y rangos básicos de la copia NCAR, sin máscara de cuenca ni verificación de precisión o independencia. No equivale a abrir el gránulo NASA original ni demuestra calidad de los valores. La salida completa se reproduce con `python research/validar_muestras_ful102.py` y requiere las muestras locales y dependencias del proyecto.

## Contraste de los fragmentos cuando el hash no coincide

Para las filas 21 (MERRA-2), 27 (ítem de límites MDBA) y 34 (punto NASA POWER) se compararon los 400 caracteres guardados en la columna G con la representación Python de las respuestas repetidas interpretadas como JSON. Los tres fragmentos coinciden. Para MERRA-2 primero se sustituyó en la copia repetida la marca `feed.updated` por la visible en Work; el fragmento POWER incluye los doce valores mensuales de `PRECTOTCORR` y su clave anual.

La coincidencia del fragmento no prueba igualdad del cuerpo íntegro. El inventario MERRA-2 repetido tiene un tamaño distinto al de Work y su original sigue sin recuperarse. La respuesta POWER repetida tiene el mismo tamaño pero diferente SHA-256; se reconstruyó posteriormente como se describe abajo. El ítem MDBA consultado nuevamente devolvió 4.393 bytes con SHA-256 `f252d6ee6de02fec37a0e46d4ba4c3b867a3fec7af4809a6aaed46f6b126dae9`, diferente del hash Work; posteriormente se reconstruyó y verificó como se explica a continuación.

Para el ítem MDBA, se probaron valores anteriores de los campos variables `numViews` y `lastViewed` en una consulta repetida, conservando el resto de los bytes. Con `numViews=48645` y `lastViewed=1794628800000` (2026-11-14 04:00 UTC), el resultado tiene 4.393 bytes y SHA-256 `63fd9559378e89f3ca8646722bb058e81d4bb79ecfe8d5fc11d486541fcbf47d`, exactamente el registrado por Work. La coincidencia identifica esa respuesta reconstruida, no el ZIP completo. Se conserva como `data/cache/ful-102/work_reconstructed_row_27.json`, ignorada por Git.

## MOD11C3: capas y tratamiento de calidad documentados

La [guía MOD11 de LP DAAC](https://lpdaac.usgs.gov/documents/715/MOD11_User_Guide_V61.pdf), sección 10 y tabla 23, describe MOD11C3 como un producto mensual de temperatura superficial en malla geográfica de 0,05°, construido a partir de valores diarios MOD11C1. Las capas `LST_Day_CMG` y `LST_Night_CMG` se documentan como enteros `uint16`, con fill 0, factor de escala 0,02 y unidad K. La misma tabla describe `QC_Day` y `QC_Night` como `uint8` con rango 0–255 y sin fill aplicable; por tanto, el cero de esas capas QA no debe tratarse automáticamente como el cero de la capa LST.

Las capas `Clear_sky_days` y `Clear_sky_nights` son máscaras de 32 bits sobre días y noches de cielo despejado con LST válida. La sección 10.5 remite a los indicadores de calidad de la tabla 13; interpretar estas capas y la entrega concreta antes de definir filtros o agregaciones. No se ha abierto una muestra MOD11C3 ni comprobado esos atributos en una descarga. LST superficial tampoco equivale a temperatura del aire `T2M`.

## Cita y condiciones declaradas en CMR para la terna

Las respuestas UMM de las colecciones [MERRA-2](https://cmr.earthdata.nasa.gov/search/concepts/C1276812859-GES_DISC.umm_json), [IMERG](https://cmr.earthdata.nasa.gov/search/concepts/C2723754851-GES_DISC.umm_json) y [GLDAS](https://cmr.earthdata.nasa.gov/search/concepts/C1342986036-GES_DISC.umm_json), consultadas el 2026-11-14, remiten en `UseConstraints` a las [orientaciones de uso y cita EOSDIS](https://earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance) y a las [directrices GES DISC](https://disc.gsfc.nasa.gov/data-guidelines). En la inspección web, la primera URL respondió 403 y la segunda redirigió a una página cuyo contenido no fue legible; por eso no se ha verificado el texto de esas directrices. La [política científica general de NASA](https://science.nasa.gov/researchers/science-information-policy/) sí se pudo consultar y describe el principio de apertura de información de investigaciones financiadas por SMD. No se atribuye una licencia Creative Commons concreta a estas colecciones a partir de esas fuentes generales.

Los campos de cita identifican como creadores a GMAO para MERRA-2; Huffman, Stocker, Bolvin, Nelkin y Tan para IMERG; y Beaudoing y Rodell para GLDAS, con GES DISC como publicador. El catálogo estructurado guarda creadores y DOI para facilitar una cita precisa de la versión usada; consultar la ficha vigente antes de publicar. `AccessConstraints` dice `None` en IMERG y GLDAS y está ausente en MERRA-2: esto es un campo de metadatos y **no demuestra que una descarga funcione sin autenticación**. Verificar términos de la entrega y las copias de terceros antes de redistribuir.

## Campos auxiliares de calidad IMERG en la caja de 2005

La comprobación reproducible de las doce copias NCAR también inspeccionó `randomError`, `gaugeRelativeWeighting` y `precipitationQualityIndex`. En cada campo y mes, las 21.000 celdas de la caja resultaron finitas y distintas de su fill. En conjunto, los rangos observados fueron 0,001–0,077 mm/h para `randomError`, 0–99 % para `gaugeRelativeWeighting` y 2,15–1.016,72 para `precipitationQualityIndex`. Son rangos sobre una caja y doce muestras, no sobre toda la colección ni la cuenca.

El [documento técnico IMERG V07](https://gpm.nasa.gov/sites/default/files/2023-07/IMERG_V07_ATBD_final_230712.pdf), sección 9, explica que el índice mensual se interpreta como un número equivalente de pluviómetros en una caja de 2,5° × 2,5°, y que es una medida relativa de desempeño. No debe confundirse con el índice semihorario ni tratarse automáticamente como una probabilidad entre cero y uno. Tampoco se ha definido aquí un umbral de descarte o una validación independiente; eso requiere revisión científica.

## Respuesta original POWER reconstruida

La respuesta repetida de la fila 34 tiene 944 bytes. Se ensayaron valores del campo de tiempo de ejecución `times.data` conservando el resto de los bytes; con `0.115` en lugar de `0.123`, el resultado tiene SHA-256 `b047382d9fa98e149a739c5440dee87cb8d916caf537c028d29eb529f3eefbc7`, igual al registrado por Work. La comparación de ambos JSON confirma que el único campo diferente es `times.data`; sus valores mensuales y anuales coinciden íntegramente. La copia reconstruida se conserva en `data/cache/ful-102/work_reconstructed_row_34.json`, ignorada por Git. Esto recupera esa respuesta individual, no el ZIP de evidencia.

## Integridad y apertura de las copias recuperadas

Además de los hashes, se interpretaron sin errores los 28 archivos recuperados con extensión JSON o GeoJSON y el notebook NASA de 17 celdas. El ZIP ABS contiene seis entradas y `ZipFile.testzip()` no detectó errores de CRC. Se abrieron las 34 páginas del manual GLDAS, 66 del manual MERRA-2 y 23 de la guía SMAP L4 y se extrajo texto no vacío de cada una. Estas son comprobaciones de estructura, integridad y disponibilidad de texto; no implican que cada página se haya auditado visualmente ni que todos sus contenidos o fórmulas estén validados. Los archivos permanecen en la caché local ignorada.

# Inventario de evidencia externa — Anomaly Zero (14-11-2026)

> **Estado: EVIDENCIA DE DESCUBRIMIENTO, NO VALIDACIÓN DE GRILLAS.**  
> Fuente auditada: ZIP aportado por el equipo, `Anomaly_Zero_Evidencia.zip`; archivo **no añadido al repositorio**. Esta página resume lo inspeccionado y ofrece enlaces oficiales para volver a comprobarlo. No debe utilizarse para declarar que los productos finales han sido descargados, analizados ni aprobados.

## 1. Integridad y alcance del paquete

- ZIP examinado: **60 entradas**, con `manifest.json` de **59 archivos registrados**.
- Auditoría local: **59/59 hashes SHA-256 y tamaños coincidentes**, incluyendo respuestas CMR, bitácoras y geometría.
- SHA-256 del ZIP completo: `c5066dd538d94fedf7753d77db135d538ab7e7a815417eeb7bbdd7190d7803ba`.
- Contiene respuestas HTTP registradas el **14 de noviembre de 2026**, scripts en `research/probe*.py`, inventarios de granules, catálogo de fuentes, GeoJSON MDBA/NSW y texto de investigación.
- **No contiene** los cubos/archivos NetCDF o HDF5 reales de los tres productos; tampoco los PDF/XLSX terminados (solo sus comprobaciones en `calidad/`). Los logs registran pruebas de lecturas y URLs públicas, no autenticación Earthdata confirmada.
- Los scripts del ZIP no fueron ejecutados; se inspeccionaron los cuerpos JSON guardados y se recalcularon hashes, fechas y cobertura directamente desde las respuestas.

## 2. Identificadores y cobertura del catálogo CMR

Consultas de **colecciones** registradas como HTTP 200 en `evidencia/log.json`. Consultas de **gránulos** registradas como HTTP 200 en `evidencia/log2.json`, con bounding box **138,-38,153,-24** y rango **2005-01-01 a 2025-12-31**. Los cuerpos de gránulos tienen un registro por mes, que se recontó independientemente:

| Producto candidato | CMR Collection Concept ID | Versión | Archivo típico según título de gránulo | Conteo mensual 2005–2024 | Último mes de la captura |
| --- | --- | --- | --- | --- | --- |
| MERRA-2 `M2TMNXSLV` | `C1276812859-GES_DISC` | `5.12.4` | `.nc4` | **240/240**, sin duplicados en respuesta | 2025-12 |
| GPM IMERG Final `GPM_3IMERGM` | `C2723754851-GES_DISC` | `07` | `.HDF5` | **240/240**, sin duplicados en respuesta | 2025-09 |
| GLDAS Noah `GLDAS_NOAH025_M` | `C1342986036-GES_DISC` | `2.1` | `.nc4` | **240/240**, sin duplicados en respuesta | 2025-12 |

Las respuestas `evidencia/merra_2005_2025.body`, `imerg_2005_2025.body` y `gldas_2005_2025.body` contienen respectivamente **252, 249 y 252 entradas** del período extendido 2005–2025. Sus subconjuntos 2005–2024 contienen 240 meses únicos sin huecos de inventario. **No extrapolar a cobertura de píxeles, completitud de los archivos o suficiencia de serie regional.**

En la captura de IMERG V07 no aparecen octubre–diciembre de 2025. **No completar ese período mezclando versiones o productos** para la demostración. La ventana 2005–2024 no tiene ese problema de catálogo.

**Consultas oficiales repetibles:**
- [MERRA-2 colección CMR](https://cmr.earthdata.nasa.gov/search/collections.json?short_name=M2TMNXSLV&version=5.12.4) · [Gránulos MERRA-2](https://cmr.earthdata.nasa.gov/search/granules.json?collection_concept_id=C1276812859-GES_DISC&page_size=5).
- [IMERG colección CMR](https://cmr.earthdata.nasa.gov/search/collections.json?short_name=GPM_3IMERGM&version=07) · [Gránulos IMERG](https://cmr.earthdata.nasa.gov/search/granules.json?collection_concept_id=C2723754851-GES_DISC&page_size=5).
- [GLDAS colección CMR](https://cmr.earthdata.nasa.gov/search/collections.json?short_name=GLDAS_NOAH025_M&version=2.1) · [Gránulos GLDAS](https://cmr.earthdata.nasa.gov/search/granules.json?collection_concept_id=C1342986036-GES_DISC&page_size=5).

**Cautela:** el criterio de bounding box en CMR **filtra gránulos que intersectan la búsqueda**, no recorta datos, no valida una celda del polígono y no demuestra que haya observaciones válidas dentro de toda la cuenca. Algunos enlaces secundarios de metadatos CMR en el paquete parecen corresponder a otros productos: cotejar el ID de colección, shortname, versión y título; no seleccionar una fuente solo por un enlace metadata ambiguo.

## 3. Geometría oficial candidata

- El paquete incluye `geometrias/murray_darling.geojson`, **una Feature Polygon** con `DDIV_NAME = Murray-Darling Basin` y CRS declarado **EPSG:4326**, 14.138 pares de coordenadas de borde.
- Inspección geométrica local: **polígono válido** en Shapely, bounding box aprox. **longitudes 138.5685–152.4885**, **latitudes -37.6821 a -24.5856**.
- El punto del piloto FUL-101 en Wagga Wagga (longitud **147.353737883333**, latitud **-35.1257741166667**) cae **dentro** de este polígono según el test `covers`.
- Fuente guardada: [servicio ArcGIS MDBA, capa boundary](https://services8.arcgis.com/5xxEi7I2m6ml97fE/arcgis/rest/services/boundary_gdb/FeatureServer/0), [ítem de catálogo](https://www.arcgis.com/home/item.html?id=ba731d77d80947fbbcbf7524364372ff). El título declara que es la delimitación de la cuenca establecida en Section 4(1) del Water Act 2007. El ítem atribuye la información al Australian Government Department of Climate Change, Energy, the Environment and Water y declara licencia **CC BY 4.0**.
- Hash SHA-256 del GeoJSON guardado: `d36fe31424758cc4fb8eef25e21b835bb5c05c793c746e8a1eb7b5a5841f6a53`.
- La geometría es **candidata técnicamente respaldada**, pero Lucas debe revisar su autoridad, atribución, adecuación científica de la máscara y la definición territorial elegida antes de incorporarla al motor regional.

**Alternativa NSW:** contiene GeoJSON y una copia simplificada para visualización, con metadatos ISO de ABS ASGS 2026. El XML del producto indica **CC BY-SA 4.0** para NSW; no se debe asumir la misma licencia que la geometría MDBA. La simplificación a 0.005 grados es **solo para dibujo**, no para calcular promedios regionales. No mezclar «NSW» y «cuenca Murray–Darling»: son territorios distintos.

## 4. Consecuencias para FUL-99: qué puede cerrarse y qué NO

| Tema | Estado a partir de esta evidencia | Próxima acción / dueño |
| --- | --- | --- |
| IDs de las 3 colecciones y versiones candidatas | **Inventario verificado en captura CMR** | Lucas incorpora a FUL-102/104, comprobando versión vigente y documentación |
| Inventario de 240 meses 2005–2024 por producto | **Confirmado para las respuestas CMR**, no para calidad de píxeles | Alaín descarga muestras reales y confirma atributos/cobertura; FUL-103/106 |
| Existencia de un polígono de la cuenca | **GeoJSON técnicamente válido + fuente y licencia identificadas** | Lucas valida su idoneidad y atribución; FUL-104/107 |
| Ubicación del punto Wagga Wagga respecto al polígono | **Dentro del polígono empaquetado** | Mantener FUL-101 como ejemplo puntual, nunca como promedio regional |
| Patrón de rutas de granules (`.nc4` y `.HDF5`) | **Extensiones constatadas en nombres del catálogo** | Alaín debe abrir un archivo verdadero; no asumir variables/attrs por extensión |
| Datos regionales 2005–2024, máscara, pesos y cobertura | **PENDIENTE** | Lucas/César/Alaín: archivo real, QA y método de área; FUL-104/106/105 |
| Primera variable funcional | **PENDIENTE de elección científica** | MERRA-2/T2M puede priorizarse para una primera prueba por continuidad con POWER, solo tras revisar acceso, QA y complejidad; FUL-107 |
| Estadística de tendencias y significancia | **PENDIENTE** | César después de tener suficientes meses regionales; FUL-105 y módulo posterior |
| API externa, deployment y mapas temporales | **PENDIENTE** | FUL-108/109 después de confirmar snapshots y grillas |

## 5. Recomendación operativa

- **Para Lucas:** convertir las tres colecciones y su evidencia CMR en fichas de `docs/datasets.md` / catálogo de FUL-102; validar geometría MDBA, fuente y licencia, CRS, cobertura del polígono.
- **Para Alaín:** usar los tres CMR IDs para buscar una muestra mensual por producto, autenticarse sin exponer credenciales y conservar **archivo real + manifest + atributos** (no solo URL/título CMR).
- **Para César:** preparar QA de muestras y especificación de serie regional sin inferencia prematura; la máscara y ponderación deben comprobarse con grillas descargadas.
- **Para FUL-99:** este archivo **sustenta decisiones de arquitectura**, no desplaza la revisión de Lucas y Alaín ni permite cerrar FUL-104/106/105/107.

**Procedencia del reporte:** `Anomaly_Zero_Evidencia.zip` y su `manifest.json`, `evidencia/coverage.json`, `evidencia/log*.json`, `evidencia/cmr_*.body`, `evidencia/*_2005_2025.body`, `geometrias/murray_darling.geojson` y `evidencia/mdba_item.body`. La captura es histórica al 14-11-2026; NASA puede revisar metadatos, colecciones y disponibilidad posteriormente.

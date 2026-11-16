# MAP-01/P2 — Viabilidad de capa IMERG 2005-01

**Estado Gate M: HOLD.** La fuente y su grilla son verificables, pero no hay una decisión registrada de César sobre el formato del derivado, su colocación en MapLibre, la escala/leyenda ni su distribución. No se generó ni publicó una imagen, descriptor o endpoint. Esto registra el bloqueo actual; no sustituye la decisión científica.

## Evidencia del insumo

- Gránulo: `GPM_3IMERGM`, colección NASA GES DISC `C2723754851-GES_DISC`, gránulo `G2823464479-GES_DISC`, versión 07, archivo V07B, enero de 2005; DOI `10.5067/GPM/IMERG/3B-MONTH/07`.
- Manifiesto y HDF5 abiertos desde el handoff local `.be04-snapshot-reader`; tamaño observado `18,028,945` bytes y SHA-256 `bac3b9bc5ee8cc3eb1e5fe844778d54fd86e2b722813055b37f3872e6e4c73d5`, coincidentes con el manifiesto. Variable `Grid/precipitation`, forma `(time, lon, lat)=(1, 3600, 1800)`, `float32`, unidad original `mm/hr`; no se aplican `scale_factor` ni `add_offset`. Es una tasa media mensual, no un acumulado.
- Longitud y latitud ascienden; los centros y `lon_bnds`/`lat_bnds` son nativos. DS-03 conserva el recorte bbox EPSG:4326 138–153°E, 38–24°S como arrays `(lon, lat)` de 150×140; no aplica polígono MDBA, máscara ni QA. Los bounds IMERG tienen pequeños gaps/overlaps float32 documentados en DS-03/DS-07; no se corrigen aquí.
- La inspección de grilla completa registró 54,671 valores fill, 6,425,329 valores finitos no-fill y 895,459 ceros válidos. En el bbox recortado: 21,000 centros, 0 fill, 0 no-finitos y 270 ceros válidos. Esos conteos describen datos y centros; no equivalen a área cubierta ni a QA. `precipitationQualityIndex` y `randomError` no se aplican; QA permanece `unassessed`.
- El snapshot puntual DS-03 y la superficie son soportes distintos. No se construirá una imagen a partir del valor de `/series`, ni se describirá el recorte rectangular como la cuenca.

## Propuesta para decisión Gate M

| Etapa | Propuesta concreta; requiere aprobación antes de implementar |
| --- | --- |
| Fuente | HDF5 V07B enero indicado arriba y su manifiesto local verificado; preservar hash fuente y hash del manifiesto en la procedencia del derivado. No incluir originales en Git ni en la imagen del contenedor. |
| Extensión | Solo el recorte rectangular de centros y bounds nativos documentado por DS-03 (138–153°E, 38–24°S); no usar la geometría MDBA para enmascarar valores. |
| Píxel/posición | El valor pertenece al centro de cada celda de 0.1°; para una imagen norte-arriba se requeriría pasar de `[lon, lat]` ascendente a filas `[lat, lon]` descendentes. No se ha aplicado esa transformación. |
| Exportación/proyección | La opción mínima sería PNG RGBA pequeño, con transparencia solo para fill/no finitos, y resampling nearest. Sin embargo, MapLibre coloca `ImageSource` mediante cuatro esquinas geográficas y el mapa actual usa Web Mercator. Una imagen de filas equiespaciadas en latitud no queda alineada en sus filas interiores con una simple bbox: una interpolación lineal en coordenada Mercator entre −24° y −38° sitúa la fila central cerca de −31.26°, no −31.00° (≈0.26°, 2.6 celdas nominales). Se requiere decidir/validar una reproyección de visualización o aceptar y documentar una aproximación con puntos de control interiores. El cálculo es geométrico, no una prueba visual del raster en MapLibre. |
| Nodata y cero | Nodata (`_FillValue` y no finitos) transparente; cero finito permanece como valor observado y debe tener color opaco. No interpretar ni filtrar flags del proveedor. |
| Escala/leyenda | Unidad `mm/hr`, con leyenda explícita y etiqueta de tasa mensual. El rango observado del gránulo va de 0 a 2.33100009; no se seleccionó escala, cortes ni paleta. Solicitar una regla fija aprobada para que el color no sugiera una escala automática o QA. |
| Identidad y contrato | El contrato actual `RasterLayer` solo admite `tile_template`, definido para una plantilla de tiles, mientras el consumidor `ImageSource` necesita URL de imagen y bbox. No reutilizar `tile_template` con otro significado. Propuesta mínima pendiente: añadir al descriptor `image_url`, `bbox`, `artifact_sha256`, hashes de fuente/manifiesto, procedimiento/versionado del derivado y `synthetic:false`; conservar un ID de capa derivada distinto del `dataset_id` de la serie puntual. |
| Publicación | Derivado estático versionado con build o artefacto reproducible y disponible para Render; no depender del worktree local ni de un mount Compose. Atribuir GPM/IMERG y GES DISC conforme a la cita de colección y a las guías enlazadas en el metadato CMR. El campo `UseConstraints` de esa colección remite a las guías NASA/GES DISC; no asigna por sí mismo un literal de licencia al archivo. Confirmar la redacción de atribución/distribución antes de exponer el derivado públicamente. |
| Límite de uso | Solo representación contextual descriptiva de un mes, `mm/hr`, sin máscara de cuenca, media regional, anomalía, tendencia, significancia ni QA aprobada. Enero disponible únicamente; otros meses sin capa. |

### Respuesta que falta de César

Confirmar explícitamente si se continúa con esta capa derivada de visualización y resolver: (1) PNG e identidad/metadatos de procedencia; (2) reproyección/colocación, incluyendo tolerancia y puntos de control interiores; (3) nodata transparente y cero opaco; (4) escala y paleta fija en `mm/hr`; (5) atribución/condiciones para publicar el derivado; (6) ampliación mínima de `RasterLayer` y quién aprueba el cambio de contrato. Hasta entonces Gate M queda en HOLD.

## Visor y despliegue

- FE-08 ya usa `MapCanvas`/MapLibre `ImageSource`, `raster-resampling: nearest`, y mantiene el resolver real en `null` hasta Gate M. El contrato OpenAPI define `tile_template` como URL de tiles pequeños; `ResolvedRaster` solo lleva `url` y `bbox`. Sin agregar campos no puede expresar el formato, hash y linaje de una imagen real. No se tocó FE-08 ni OpenAPI.
- El grafo `graphify-out/graph.json` no está presente en el checkout. Se usaron búsquedas dirigidas (`rg`) y se contrastaron consumidores y tipos directamente en `MapCanvas.tsx`, `MapPanel.tsx`, `rasterTarget.ts`, `RasterLegend.tsx`, `types/contracts.ts` y `docs/openapi-contract-v0.yaml`.
- Estado remoto incongruente: Linear AZ-07/FUL-139 afirma que ambos servicios están desplegados desde `feature/render-free`; la descripción de PR #44 sigue diciendo que los servicios aún no se crearon y que Docker/build público no se comprobaron. PR #44 continúa abierta Draft, HEAD `2d0feaaa28e8aad2ca6131d0f2e4e42ab4034732`. En las URLs registradas, el frontend devuelve 200 y `/health` devuelve 200; `/api/v1/products?region_id=murray-darling-basin` devuelve 500 sanitizado (`request_id=60bdaba1-142d-4990-82c3-75b3558ab2b6`), y el endpoint de geometría BE-10 devuelve 404. No se pudo confirmar qué commit está desplegado. Esto no cuenta como QA de navegador.
- Para completar QA Render se necesita que AZ-07 reconcilie la revisión/branch desplegada y corrija o explique el 500 de catálogo y el 404 de BE-10. Después del despliegue autorizado: confirmar snapshot, consultar enero real y validar descriptor, tipo MIME, puntos interiores, leyenda, atribución y meses sin capa desde navegador.

## Fuentes consultadas

- Evidencia del proyecto: [DS-03](ds-03-snapshot-imerg-demo.md), [DS-07](ds-07-colocalizacion-espacial-nasa-2005.md), [DS-08](ds-08-decision-soporte-espacial-nasa-2005.md), [FE-08](fe-08-context-map.md) y [BE-10](be-10-context-geometry.md).
- [Metadato de colección CMR GPM_3IMERGM](https://cmr.earthdata.nasa.gov/search/concepts/C2723754851-GES_DISC.umm_json) registra la colección y DOI; `UseConstraints` dirige a [NASA Earthdata data-use guidance](https://www.earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance) y [GES DISC data guidelines](https://disc.gsfc.nasa.gov/data-guidelines) para uso/citación. La colección recomienda conservar la cita de GES DISC y su DOI.
- [NASA IMERG V07 technical documentation](https://gpm.nasa.gov/resources/documents/imerg-v07-technical-documentation) respalda la resolución nominal de 0.1°; [MapLibre ImageSource](https://maplibre.org/maplibre-gl-js/docs/API/classes/ImageSource/), [coordenadas de ImageSource](https://maplibre.org/maplibre-gl-js/docs/API/type-aliases/Coordinates/) y [guía CRS](https://maplibre.org/maplibre-gl-js/docs/guides/custom-crs/) documentan las cuatro esquinas y Web Mercator por defecto.

**Conclusión:** no publicar la capa todavía. El insumo es identificable y el recorte de enero es reproducible, pero la representación interior en Web Mercator, la escala visual, el descriptor de procedencia, las condiciones de distribución y la revisión del entorno Render todavía no están resueltos.

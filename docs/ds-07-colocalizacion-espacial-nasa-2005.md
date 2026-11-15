# DS-07 — Co-localización espacial NASA 2005

**Tarjeta:** FUL-124 · **Dictamen técnico:** `conditional` para continuar únicamente con EDA descriptivo espacial exploratorio, no aprobado · **Estado científico:** ninguna máscara, superficie regional o regla QA queda aprobada.

## Resumen

El inventario local se reprodujo con `research.ful122_inventory` sobre las raíces de FUL-105/116/122 y FUL-123: 51 archivos candidatos, 36 elegibles (12 meses por producto) y 15 copias idénticas descartadas. Los 36 manifiestos/payloads elegibles pasaron identidad, tamaño, SHA-256 y lectura estructural nativa. IMERG, MERRA-2 y GLDAS tienen grillas completas sobre la extensión bbox del límite MDBA utilizado en el diagnóstico; eso no valida el límite como máscara ni demuestra comparabilidad de las celdas.

El límite local MDBA tiene SHA-256 `d36fe31424758cc4fb8eef25e21b835bb5c05c793c746e8a1eb7b5a5841f6a53`, es un `Polygon` válido de un componente, sin agujeros y con 14.138 vértices contando cierre. La grilla produce distancias entre centros de producto no nulas, cantidades de centros distintas a cantidades de celdas que tocan el límite y una discrepancia de cierre de área para IMERG. Las celdas de MERRA-2 y GLDAS no declaran bounds espaciales; sus celdas se infirieron de los centros.

Los diagnósticos son **provisionales**. No se combinaron variables, calcularon promedios espaciales, inferencias, tendencias ni modelos. Los campos QA no se aplicaron. Gate R, Gate T, QA IMERG y el linaje de máscara GLDAS permanecen pendientes. No se selecciona definitivamente ninguna estrategia espacial.

## Alcance, fuentes y geometría

### Límite MDBA

El archivo explorado es una caché local ignorada por Git, no un artefacto entregado por esta PR. La geometría se leyó en modo solo lectura y su hash se fijó como condición de auditoría. El ítem de [MDBA en ArcGIS](https://www.arcgis.com/sharing/rest/content/items/ba731d77d80947fbbcbf7524364372ff?f=pjson) define el límite de Murray–Darling bajo Section 4(1) del Water Act 2007, atribuye los límites a DCCEEW y dice que deriva de *Australia’s River Basins 1997*, fechado 30-jun-1997. El ítem declara licencia CC BY 4.0 y lista a MDBA como publicador. El [servicio de la capa](https://services8.arcgis.com/5xxEi7I2m6ml97fE/arcgis/rest/services/boundary_gdb/FeatureServer/0?f=pjson) expone geometría poligonal en EPSG:3857 (ArcGIS WKID 102100/3857); el GeoJSON local declara CRS EPSG:4326. La metadata del ítem consultada el 15-nov-2026 indica modificación el 14-ene-2026 21:08:32 UTC; esa fecha corresponde al ítem, no a una versión topográfica verificable.

La metadata del producto de Geoscience Australia para la cartografía de cuencas de 1997 indica vigencia junio de 1997 y datum AGD66 ([GA product catalogue](https://www.ga.gov.au/bigobj/GA8096.pdf)). Esa descripción de la fuente histórica **no demuestra** que el datum nativo de la geometría legal que MDBA re-publica sea AGD66, ni documenta su cadena exacta de transformaciones. Por tanto, se mantienen separados: fuente histórica atribuida (Australia’s River Basins 1997), CRS del servicio (3857) y CRS declarado por el GeoJSON exportado (4326). La geometría, su fecha/versionado geográfico y su uso como unidad estadística requieren decisión de César. No se distribuye el archivo.

| Propiedad geométrica observada | Diagnóstico |
|---|---|
| Hash / tamaño del artefacto | SHA-256 `d36fe31424758cc4fb8eef25e21b835bb5c05c793c746e8a1eb7b5a5841f6a53`; 477.805 bytes |
| Tipo / validez | Un `Polygon`, válido según Shapely 2.2.0; 1 componente, 0 agujeros, 14.138 vértices con cierre |
| Bbox del GeoJSON, lon/lat | 138,568466639°E, −37,682084144°; 152,488546389°E, −24,585618079° |
| CRS exportado / servicio | EPSG:4326 / EPSG:3857 (WKID 102100) |
| Datum de fuente original | No resuelto para la geometría MDBA re-servida; la cartografía GA 1997 de origen declara AGD66 |
| Licencia del ítem | CC BY 4.0 declarada por el ítem ArcGIS; comprobar atribución de derivados antes de redistribución |
| Área oficial | No determinada ni utilizada como valor oficial |

La forma contiene coordenadas en el bbox austral, sin cruce del antimeridiano. Las pruebas sintéticas sí comprueban que el ejecutor rechace un polígono envolvente antimeridiano. La validez topológica computacional no resuelve exactitud posicional, definición del límite legal, linaje, escala de captura ni licencia específica de un derivado. El fragmento LineString versionado en `docs/examples` no se usa como polígono.

## Auditoría de los productos y grillas

Se volvieron a validar los 36 payloads con el inventario FUL-122 y sus manifiestos adyacentes. Para cada producto las coordenadas y bounds usados por el diagnóstico son invariantes entre los doce meses (hash de coordenadas reproducible). Los tres productos cubren el bbox completo del polígono, pero esto solo expresa dominio de grilla.

| Producto / variable | Grilla observada | Orientación / bounds | Dominio respecto al bbox MDBA |
|---|---|---|---|
| IMERG Final V07B `Grid/precipitation`, `mm/hr` | `(time, lon, lat)=(1,3600,1800)`; coordenadas con incremento mediano ~0,1° lat × ~0,1° lon; nominal 0,1°; cobertura global | Latitud −89,95 a 89,95°, longitud −179,95 a 179,95°; ambas ascendentes. `lat_bnds` y `lon_bnds` nativos; límites float32 tienen pequeños huecos/solapamientos | Bbox MDBA dentro de la grilla global |
| MERRA-2 M2TMNXSLV `T2M`, `K` | `(time, lat, lon)=(1,361,576)`; 0,5° lat × 0,625° lon | Latitud −90 a 90°, longitud −180 a 179,375°; ascendente. El archivo no declara bounds lat/lon; inferidos por puntos medios y media separación de borde | Bbox MDBA dentro de grilla global |
| GLDAS Noah `SoilMoi0_10cm_inst`, `kg m-2` | `(time, lat, lon)=(1,600,1440)`; 0,25° × 0,25° | Latitud −59,875 a 89,875°, longitud −179,875 a 179,875°; ascendente. No declara bounds lat/lon; inferidos por puntos medios y media separación de borde | Bbox MDBA está dentro del dominio, cuyo límite sur es −59,875° |

Los incrementos IMERG medidos directamente en las coordenadas float32 de los archivos son aproximadamente 0,09999943° en latitud y 0,09999847° en longitud; 0,1° es la resolución nominal documentada por [NASA GPM IMERG](https://gpm.nasa.gov/resources/documents/imerg-v07-technical-documentation). El producto mensual es una media temporal de tasa de precipitación por mes según la documentación NASA; se conserva `mm/hr` y no se convirtió a acumulado. `time` IMERG declara calendario juliano y `time_bnds` del mes.

GLDAS declara calendario `standard`, `time_bnds` mensual y `cell_methods=time: mean`; `_inst` forma parte del nombre de variable, no convierte el producto mensual en una lectura instantánea. MERRA-2 es la colección mensual tavg; en cada archivo inspeccionado `time=0` con unidades `minutes since YYYY-MM-01 00:30:00`, sin atributo calendario ni bounds temporales espaciales/de celda. No se infieren bounds desde ese timestamp. Las fechas de gránulos e identidades mensuales se mantienen desde CMR/manifiestos.

Valores fill declarados: IMERG `precipitation` −9999,9004 aprox. en representación float32; MERRA-2 1e15; GLDAS −9999. Los marcadores no se tratan como mediciones. La evaluación QA IMERG continúa `unassessed`; sus campos `precipitationQualityIndex`, `randomError`, `gaugeRelativeWeighting` y el diagnóstico de fase se conservan sin filtros. La presencia de `randomError` o de un índice no es un pase QA. No se identificaron nombres explícitos QA/flag/error en las variables examinadas de MERRA-2/GLDAS; eso tampoco representa aprobación. El linaje de máscara de agua GLDAS 2005 continúa incierto.

### Lecturas puntuales del soporte candidato

Se contaron categorías de valor exclusivamente en centros que el polígono caché cubre, recortando la lectura a la extensión bbox y leyendo los archivos en modo solo lectura. Es un **reporte de candidatos por centro**, sin ponderación, agregación ni máscara QA, no una cobertura por superficie.

| Producto | Centros por mes | Fill en los 12 meses | No finitos distintos de fill | Finitos no-fill | Ceros finitos no-fill | Negativos finitos no-fill |
|---|---:|---:|---:|---:|---:|---:|
| IMERG | 10.092 | 0 | 0 | 121.104 | 1.911 | 0 |
| MERRA-2 | 323 | 0 | 0 | 3.876 | 0 | 0 |
| GLDAS | 1.617 | 24 (2/mes) | 0 | 19.380 | 0 | 0 |

Los ceros IMERG permanecen válidos en este conteo; no se transforman a faltantes. Los números de GLDAS describen la regla geométrica de centro en los archivos disponibles, no la aceptación científica de esos datos ni de la máscara. Las celdas parciales no participan en este cuadro de valores.

## Comparación de estrategias de soporte

Los resultados geométricos se obtuvieron con la misma referencia exploratoria y una transformación candidata WGS84→EPSG:3577 (Australian Albers), densificando segmentos en lon/lat con máximo de 0,02°. EPSG:3577 proporciona una superficie plana equivalente para investigar el overlay, pero la operación de datum no quedó fijada y PROJ no declara exactitud de transformación en este entorno. La geometría, los bounds inferidos y la precisión float32 de IMERG limitan las áreas. Todos los valores de área de abajo son diagnostics de cierre de la partición, **no área oficial MDBA ni denominadores publicables**.

| Grilla | Centros cubiertos por el polígono | Celdas con intersección de área positiva | Parciales | Suma de áreas de intersección proyectadas (km²) |
|---|---:|---:|---:|---:|
| IMERG | 10.092 | 10.467 | 747 (7,14 %) | 1.058.622,38 |
| MERRA-2 | 323 | 384 | 123 (32,03 %) | 1.058.574,01 |
| GLDAS | 1.617 | 1.756 | 281 (16,00 %) | 1.058.574,01 |

El área del polígono transformado por el mismo método es 1.058.574,01 km² en este cálculo numérico; no se adopta como área del Basin. La suma IMERG excede ese valor diagnóstico en 48,38 km² (~0,00457 %). Cerca del bbox, los bounds IMERG contienen pares contiguos de latitudes/longitudes con brechas y solapamientos float32; los grids MERRA-2 y GLDAS tienen límites inferidos y no muestran seams numéricos bajo la regla de puntos medios. El cierre de MERRA/GLDAS cercano a cero muestra consistencia interna de esta teselación aproximada, no precisión o exactitud del límite. El desacuerdo IMERG impide interpretar el conteo por celdas como una superficie que cierra sin sensibilidad adicional.

| Estrategia | Evidencia/ventaja | Riesgo y coste | Estado |
|---|---|---|---|
| (1) Emparejar centros próximos o sitios puntuales | Bajo coste; offsets geodésicos se miden de forma explícita. MERRA→IMERG: mediana 6,03 km, p95 7,39 km, máximo 7,49 km; GLDAS→IMERG: 3,64 / 3,73 / 8,68 km. La dirección inversa tiene más centros y offsets mayores: IMERG→MERRA mediana 22,92 km y p95 37,33 km; IMERG→GLDAS 10,77 / 15,81 km. | No es una correspondencia uno-a-uno: al invertir la búsqueda cambian población/offsets; un centro cercano no significa huella idéntica. La elección del punto y la sensibilidad al sitio deben justificarse. | Candidato; no aprobado |
| (2) Intersección geométrica celda–polígono | Expone centros, celdas tocadas y parciales por separado; puede calcular pesos de superficie explícitos una vez fijados límite, bounds y denominadores. | Bounds MERRA/GLDAS inferidos; IMERG presenta discontinuidades float32; el área depende de geometría/versionado, segmentos proyectados, operación de datum y valores faltantes. Coste medio; los tests no prueban exactitud geográfica. | Candidato de diagnóstico; no aprobado |
| (3) Rejilla común / regrillado / ponderación por área | Podría devolver soportes coincidentes sobre una rejilla objetivo o ponderar conservativamente celdas cuando los bounds y semánticas lo permitan. | Coste y complejidad mayores; resampling puede suavizar/cambiar variabilidad, requiere reglas distintas para una tasa (mm/hr), una temperatura (K) y una cantidad de agua modelada (kg m⁻²), y depende de validación de bordes, nodata y conservación. No se implementó ni probó con valores. | Propuesta solamente |

Los offsets son distancias a vecinos más cercanos, no pares de observaciones ni prueba de independencia. No se seleccionó un punto de referencia o rejilla objetivo. El análisis de celdas no calculó promedios, sumas de variables ni series regionales.

## Implementación y reproducibilidad

`research/ful124_spatial_audit.py` implementa la auditoría offline; `research/tests/test_ful124_spatial_audit.py` usa únicamente fixtures **sintéticas**. El manifiesto [`ful124-spatial-audit-2005.json`](../research/manifests/ful124-spatial-audit-2005.json) registra hashes/tamaños, IDs CMR, periodos, grillas, hashes de coordenadas, counts candidatos, bounds, distancias, fill/zero/nonfinite y supuestos de proyección. No contiene rutas locales ni binarios. Incluye estado explícito `diagnostic_only_not_approved` y QA/gates pendientes.

Para regenerar, instalar el grupo de investigación y configurar rutas existentes solo lectura:

```powershell
uv sync --group dev --group research

uv run python -m research.ful124_spatial_audit `
  --input-dir "RUTA\checkout-original\data\raw\nasa" `
  --input-dir "RUTA\checkout-ful105\data\raw\nasa" `
  --input-dir "RUTA\checkout-ful105\data\cache\ful-105\be02-handoff\data_root\data\raw\nasa" `
  --input-dir "RUTA\checkout-ful123\data\raw\nasa" `
  --boundary-geojson "RUTA\cache-local\mdba_boundary_4326.geojson" `
  --output research/manifests/ful124-spatial-audit-2005.json
```

La herramienta vuelve a ejecutar el inventario; exige 12 registros nativos elegibles por producto; compara coordenadas de los doce archivos; registra SHA-256 de payload/manifiesto; produce solo resumen espacial y conteos de categorías del soporte por centro; no descarga, escribe datos raw, interpola, selecciona QA ni agrega valores. Si no están disponibles raíces/raws o la geometría no coincide con el hash fijado, falla en vez de sustituirlos silenciosamente.

### Pruebas

Las nueve pruebas FUL-124 son offline y deterministas: polígono válido/inválido, rechazo del antimeridiano, missing/no monotonicidad de coordenadas, bounds explícitos/inferidos y orientación, puntos dentro/fuera/borde/agujero, celdas parciales, fill/NaN/cero/negativo sintéticos sin convertir ni filtrar, y estrategia siempre candidata/no aprobada. No presentan fixtures como datos NASA.

## Dictamen técnico y gates

### Dictamen `conditional`

Existe evidencia suficiente para continuar diseñando una EDA **descriptiva y provisional** de soportes puntuales, siempre que antes César elija/autorice el artefacto de límite y defina la política de emparejamiento que se va a evaluar. No hay evidencia suficiente para una serie o promedio de Murray–Darling, ni para afirmar que las tres variables son comparables espacialmente. Una continuación condicional no representa aprobación automática de Gate R, Gate T o QA.

### Decisiones pendientes de César

1. Identificar y autorizar la edición geométrica MDBA que se usará como referencia analítica; confirmar su fecha/versionado, datum/tratamiento de transformación y atribución requerida. El GeoJSON actual sigue en estado candidato.
2. Seleccionar para el siguiente ensayo el soporte y objetivo: puntos fijos con regla explícita de distancia, overlay de huellas de celdas o una grilla/ponderación común. No se recomienda aplicar un método productivo sin una decisión registrada.
3. Si se prueba una agregación futura, aprobar antes el denominador de área, bounds/MERRA-GLDAS inferidos vs fuente oficial, protocolo de bordes y criterio mínimo de cobertura válida por producto/mes.
4. Definir reglas QA de IMERG y aceptar o resolver la incertidumbre de máscara/linaje GLDAS con evidencia de NASA. Hasta entonces mantener `unassessed` / incierto.
5. Mantener Gate R y Gate T pendientes. Cualquier conversión de tasa IMERG a acumulado mensual requiere aprobación explícita de la semántica temporal/unidad y no pertenece a este diagnóstico.

## Fuentes y limitaciones que continúan

- [MDBA ArcGIS item metadata](https://www.arcgis.com/sharing/rest/content/items/ba731d77d80947fbbcbf7524364372ff?f=pjson) y [FeatureServer layer](https://services8.arcgis.com/5xxEi7I2m6ml97fE/arcgis/rest/services/boundary_gdb/FeatureServer/0?f=pjson).
- [Geoscience Australia, Australia's River Basins product catalogue](https://www.ga.gov.au/bigobj/GA8096.pdf); fuente histórica del límite según MDBA, no metadata de datum de la geometría legal re-publicada.
- [NASA GPM IMERG V07 documentation](https://gpm.nasa.gov/resources/documents/imerg-v07-technical-documentation), [FUL-112 QA IMERG](nasa-04-qa-imerg-muestras.md), [NASA-03 auditoría espacial anterior](nasa-03-auditoria-espacial.md), [NASA-05 linaje GLDAS](nasa-05-linaje-gldas-2005.md), [DS-06 adquisición](ds-06-adquisicion-nasa-2005.md).
- QA IMERG permanece `unassessed`; ningún umbral o flag se aplicó. El linaje de máscara de agua GLDAS 2005 no está confirmado. MERRA-2 tampoco pasa automáticamente una validación QA por leerse estructuralmente.
- Los datos usados son del año 2005; doce meses no autorizan tendencia, causalidad, p-values o modelo predictivo. No se cambió API/frontend, no se descargaron ni copiaron datos NASA, y no se versionó geometría pesada.

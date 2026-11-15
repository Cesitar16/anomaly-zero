# NASA-03 — Auditoría espacial y cobertura Murray–Darling

**Estado:** informe de investigación reproducible; ningún método queda aprobado para producción.
**Corte de datos:** muestras auténticas de enero de 2005 y enero de 2021.
**Dictamen breve:** los ensayos reproducen conteos y comparan medias por centro e intersección fraccional. La cobertura IMERG calculada supera 100 % del área de cuenca, una señal de que el overlay y/o los bounds no cierran físicamente con el polígono; por tanto, las coberturas y medias fraccionales siguen siendo diagnósticas, no aprobables.

## Pregunta y alcance

¿Cómo cambian la población de celdas, cobertura válida y promedio al seleccionar centros de celda frente a ponderar por el área de intersección con la cuenca completa MDBA? Se reutiliza la auditoría FUL-104 para las seis muestras NASA disponibles. No se genera una serie histórica, no se aplica filtro QA y no se recomienda una regla de producción.

## Geometría e insumos

| Insumo | Evidencia observada | Interpretación / límite |
|---|---|---|
| Límite MDBA | GeoJSON local ignorado por Git `data/cache/ful-102/mdba_boundary_4326.geojson`; SHA-256 `d36fe31424758cc4fb8eef25e21b835bb5c05c793c746e8a1eb7b5a5841f6a53`; un `Polygon`, 1 anillo, 0 agujeros y 14.138 vértices contando cierre; CRS exportado EPSG:4326. | No confundir con el `LineString` de 12 vértices versionado en `docs/examples`. La caché no es parte del commit ni se redistribuye. El ítem ArcGIS declara CC BY 4.0; verificar atribución/condiciones de derivados antes de publicarlos. Fuente y fecha de consulta: ficha ArcGIS MDBA consultada el 2026-11-14 UTC, documentada también en `docs/region_murray_darling.md`. |
| CRS de análisis | Polígono y esquinas de celda se transforman de EPSG:4326 a EPSG:3577 (GDA94 / Australian Albers), mediante `pyproj.Transformer.from_crs(..., always_xy=True)`. Operación PROJ observada: “Inverse of GDA94 to WGS 84 (1) + Australian Albers (with axis order normalized for visualization)”; definición `proj=pipeline step proj=unitconvert xy_in=deg xy_out=rad step proj=aea lat_0=0 lon_0=132 lat_1=-18 lat_2=-36 x_0=0 y_0=0 ellps=GRS80`; exactitud declarada 3 m. | No se densifican bordes. La operación de datum seleccionada es aproximada (3 m) y los segmentos proyectados son supuestos del ensayo, no prueba de precisión posicional. |
| NASA | MERRA-2 `T2M` enero 2005/2021; IMERG Final `Grid/precipitation` V07B enero 2005/2021; GLDAS Noah `SoilMoi0_10cm_inst` enero 2005/2021. | Los seis archivos se hallaron en `data/raw/nasa/ful104` del checkout local de FUL-104. Sus SHA-256 y tamaños están versionados en [`nasa-03-manifiesto-insumos.json`](nasa-03-manifiesto-insumos.json). La salida de cálculo detallada sigue en `data/cache/ful111/spatial_audit.json`, excluida de Git. |

La ventana de medición usa exclusivamente los meses inspeccionados. Se buscaron gránulos IMERG de 2005 en `data/raw/nasa` del checkout original, `E:\Descargas` y `C:\Users\LzzZ\Downloads`; solo estaba enero de 2005. No se afirma sensibilidad estacional y no se exigen descargas nuevas.

## Método reproducible

El script `research/auditar_espacial_ful104.py` comprueba tipo, validez topológica y anillos de la geometría, calcula centros cubiertos con `covers`, construye celdas desde bounds declarados o, cuando no existen, desde coordenadas y resolución nominal inferida. Intersecta esas celdas con el polígono proyectado y calcula pesos por área. El informe desglosa por celdas intersectadas valores no finitos, fill, finitos no-fill y ceros válidos. No se aplica QA científica.

En esta corrida las celdas MERRA-2 y GLDAS no declaran bounds en la función lectora: sus límites se infieren de la grilla nominal. IMERG usa bounds del HDF5, pero los límites float32 presentan discrepancias de continuidad ya descritas en FUL-104. Estos supuestos afectan tanto las celdas parciales como el cierre de áreas.

Para reproducir desde cualquier checkout, con dependencias de investigación disponibles y rutas locales configurables:

```powershell
uv run python -m research.auditar_espacial_ful104 `
  --data-dir E:\datos\nasa\ful104 `
  --mdba-geojson E:\datos\cache\mdba_boundary_4326.geojson `
  --nsw-zip E:\datos\cache\nsw_boundary.zip `
  --output data\cache\ful111\spatial_audit.json
```

Los datos NASA, geometrías cacheadas y resultado JSON no se versionan. `--data-dir`, `--mdba-geojson`, `--nsw-zip` y `--output` permiten ejecutarlo desde otro checkout sin copiar insumos al repositorio. `docs/nasa-03-manifiesto-insumos.json` preserva metadatos y checksums de las muestras auténticas inspeccionadas. El comando exige las seis muestras NASA obligatorias y termina con error si alguna falta o no se procesa.

## Resultados de seis muestras

Las áreas están en km²; las medias conservan la unidad original de cada variable. `celdas válidas/seleccionadas` es conteo, no cobertura por superficie. `A_intersection` incluye el área del overlay de todas las celdas intersectadas; `A_valid` suma las áreas de esas celdas con valor finito no-fill; `A_basin` es el área proyectada del polígono.

| Producto / muestra | Centros dentro (válidos / total) | Intersecciones (válidas / total) | Celdas parciales (centro dentro/fuera) | `A_intersection` | `A_valid` | `A_basin` | `A_valid/A_intersection` | `A_valid/A_basin` | Media centros | Media fraccional |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| MERRA-2, 2005-01, K | 323/323 | 384/384 | 123 (62/61) | 1.058.574,00 | 1.058.574,00 | 1.058.574,00 | 100,0000 % | 100,0000 % | 299,60616706 | 299,73048156 |
| MERRA-2, 2021-01, K | 323/323 | 384/384 | 123 (62/61) | 1.058.574,00 | 1.058.574,00 | 1.058.574,00 | 100,0000 % | 100,0000 % | 298,53793354 | 298,64771271 |
| IMERG, 2005-01, mm/hr | 10.092/10.092 | 10.467/10.467 | 747 (372/375) | 1.058.622,38 | 1.058.622,38 | 1.058.574,00 | 100,0000 % | **100,0046 %** | 0,03781639 | 0,03778986 |
| IMERG, 2021-01, mm/hr | 10.092/10.092 | 10.467/10.467 | 747 (372/375) | 1.058.622,38 | 1.058.622,38 | 1.058.574,00 | 100,0000 % | **100,0046 %** | 0,08535692 | 0,08552790 |
| GLDAS, 2005-01, kg/m² | 1.615/1.617 | 1.749/1.756 | 281 (142/139) | 1.058.574,00 | 1.057.349,08 | 1.058.574,00 | 99,8844 % | 99,8844 % | 15,90424858 | 15,94506722 |
| GLDAS, 2021-01, kg/m² | 1.615/1.617 | 1.749/1.756 | 281 (142/139) | 1.058.574,00 | 1.057.349,08 | 1.058.574,00 | 99,8844 % | 99,8844 % | 18,71877499 | 18,75333999 |

Los estados de valores en las celdas intersectadas son mutuamente distinguibles: el conteo de fill/non-finite/cero válido fue MERRA-2 2005 `0/0/0`, MERRA-2 2021 `0/0/0`, IMERG 2005 `0/0/227`, IMERG 2021 `0/0/0`, GLDAS 2005 `7/0/0` y GLDAS 2021 `7/0/0`. En todas las muestras restantes, `finite_non_fill` coincide con total menos fill y no finitos. Un cero válido se mantiene en el conjunto de datos; no se elimina por valor.

### Interpretación

- IMERG conserva 10.092 centros y 10.467 celdas que tocan/intersectan la geometría, consistente con los conteos FUL-104. La diferencia entre promedio por centros y fraccional es pequeña en 2005-01 y distinta en 2021-01; dos meses no establecen estabilidad temporal.
- **La cobertura IMERG sobre cuenca excede 100 % en 48,38 km² (~0,0046 %).** Esto no es cobertura física posible: revela un desajuste numérico/geométrico del overlay, bounds y/o partición de celdas. No normalizar ni ocultar el exceso; investigar densificación, continuidad de bounds, datum y conservación de área antes de usar esas áreas para decisiones.
- GLDAS presenta valores fill/no válidos en 7 celdas intersectadas y 2 centros interiores. Los ceros, si los hubiera, no se excluyen por ser cero. La cobertura de 99,8844 % corresponde solo a estas dos muestras.
- MERRA-2 no presenta faltantes en las celdas seleccionadas en estas muestras; no existe un flag QA específico declarado por este ensayo.
- Las medias no son indicadores regionales validados ni prueba de calidad estadística. No son comparables entre productos sin atender diferencias físicas, temporales y de unidades.

## Reproducción de FUL-104 y discrepancias

Se reprodujeron los conteos de centros/intersecciones IMERG de enero de 2005 (10.092/10.467) y los seis resultados por producto/fecha. La salida guarda nombre, SHA-256, bytes, shape, conteos, áreas y promedios. La diferencia de cierre IMERG de ~48,38 km² coincide en magnitud con el problema provisional documentado previamente; el ensayo FUL-104 de redondeo a 0,01° cerraba casi exactamente, pero simultáneamente cambiaba límites y operación geométrica. Este nuevo resultado no permite atribuir una causa única.

La prueba con grilla redondeada en FUL-104 queda como sensibilidad previa, no como método adoptado. La auditoría aquí reproduce el camino que usa bounds del archivo, sin redondearlos. Cualquier discrepancia restante debe juzgarse considerando versiones de Shapely/PROJ y hashes del insumo.

## Riesgos, licencia y recomendación a César

1. **Crítico — cierre de área:** IMERG tiene `A_valid/A_basin > 1`; no usar áreas fraccionales para serie regional hasta resolverlo y demostrar conservación con una grilla de límites consistente.
2. **Alto — bounds inferidos:** MERRA-2/GLDAS usan resolución nominal para celdas porque no hay bounds en el lector; obtener/validar definición oficial antes del pipeline.
3. **Alto — datum y bordes:** EPSG:3577 es una proyección equivalente apropiada para el ensayo de Australia, pero la operación de datum, precisión de geometría, segmentos sin densificar y límites float32 requieren sensibilidad.
4. **Medio — licencia:** el ítem ArcGIS declara CC BY 4.0. Conservar atribución de DCCEEW/MDBA y verificar términos vigentes de geometría y derivados antes de versionar o redistribuir.
5. **Medio — disponibilidad temporal:** solo enero de 2005 y 2021 en los tres productos. Faltan meses/estaciones para evaluar variabilidad de método.

**Recomendación INF:** conservar centro de celda como línea base reproducible de comparación; mantener overlay fraccional como candidato de investigación, no de producción, hasta corregir el exceso de área, validar bounds/datum/densificación y repetir sensibilidad en fechas/estaciones adicionales. La elección final corresponde a César/equipo.

### Preguntas de aprobación para César

1. ¿Se acepta conservar la selección por centros como línea base solamente, manteniendo el método productivo pendiente?
2. ¿Qué fuente/versionado/licencia de la geometría completa se autoriza para el repositorio y para derivados?
3. ¿Qué bounds oficiales deben usarse para MERRA-2 y GLDAS cuando el archivo no los declara?
4. ¿Qué tolerancia de cierre de área y qué análisis de datum/densificación deben cumplirse antes de volver a evaluar pesos fraccionales?
5. ¿Qué meses/estaciones adicionales disponibles deben constituir el siguiente conjunto de sensibilidad?

## Matriz de aceptación FUL-111

| Criterio | Evidencia en esta entrega | Estado |
|---|---|---|
| Método/insumos trazables | Comando configurable; manifiesto versionado de seis muestras con nombres, versiones, tamaños y SHA-256; SHA de polígono documentado. | TEC |
| Reproducir FUL-104 | Conteos y seis ensayos regenerados; límites y diferencias explicados. | TEC |
| CRS/datum/bounds/polígono | Polygon íntegro con anillos/agujeros/validez; CRS, operación PROJ, exactitud declarada, bounds y supuestos descritos; LineString excluido. | TEC/PARCIAL |
| Conteos y áreas con denominadores | Tabla separa conteos, `A_intersection`, `A_valid`, `A_basin` y ambos cocientes. | TEC |
| Centro vs fracción/sensibilidad | Seis muestras en dos fechas; se buscaron archivos locales IMERG 2005 en checkout y Descargas, solo enero está disponible. | TEC |
| Missing/fill/cero y QA | Salida por muestra reporta total, no finito, fill, finito no-fill y cero válido; sin filtro QA. | TEC |
| Pruebas offline | Casos sintéticos de selección, borde tocante, área parcial, cierre de áreas, faltantes/fill/cero y geometría válida/inválida. | TEC |
| Límites/licencia/preguntas | Riesgos y cinco preguntas concretas para decisión humana. | DOC/INF/PEND |
| CI y PR para revisión | Verificaciones locales y checks backend/frontend de GitHub exitosos; PR [#19 hacia `dev`](https://github.com/Cesitar16/anomaly-zero/pull/19) abierta y revisión solicitada a César. | TEC/PEND |

## Fuentes

- [`docs/region_murray_darling.md`](region_murray_darling.md): ítem y servicio MDBA, fecha, licencia declarada, hash de geometría y resultados exploratorios previos.
- [`docs/nasa-03-manifiesto-insumos.json`](nasa-03-manifiesto-insumos.json): checksums y metadatos de los seis gránulos NASA y del polígono MDBA realmente inspeccionados.
- [`docs/validacion_cientifica_ful104.md`](validacion_cientifica_ful104.md) y FUL-104: inventario científico de muestras, unidades y límites.
- [`research/auditar_espacial_ful104.py`](../research/auditar_espacial_ful104.py) y [`test_ful104_spatial_audit.py`](../research/tests/test_ful104_spatial_audit.py): cálculo y pruebas reproducibles.
- Fuentes MDBA citadas en el informe regional: [ítem ArcGIS MDBA](https://www.arcgis.com/sharing/rest/content/items/ba731d77d80947fbbcbf7524364372ff?f=json) y [FeatureServer capa 0](https://services8.arcgis.com/5xxEi7I2m6ml97fE/arcgis/rest/services/boundary_gdb/FeatureServer/0).

# DS-08 — Geometría MDBA y primer ensayo de soporte espacial

**Tarjeta:** FUL-125 · **Dictamen para el siguiente ensayo descriptivo restringido:** `conditional` · **Recomendación a César sobre el artefacto:** `approve_specific_artifact_for_test` (propuesta; no aprobada) · **Estado:** ningún soporte, máscara, regla QA, Gate R o Gate T queda aprobado.

## Resumen ejecutivo

FUL-124/DS-07 ya registró 36 granules NASA 2005 elegibles y señaló un exceso de cierre IMERG de 48,38 km². Esta tarea vuelve a auditar los archivos originales en modo de solo lectura y compara dos convenciones para bounds IMERG.

La auditoría local volvió a obtener 12 meses por producto, 36 registros elegibles, 15 copias idénticas excluidas y 12 meses de coincidencia temporal triple. El polígono MDBA local coincide byte por byte con una nueva respuesta GeoJSON del servicio oficial consultada el 15-nov-2026: ambas tienen 477.805 bytes y SHA-256 `d36fe31424758cc4fb8eef25e21b835bb5c05c793c746e8a1eb7b5a5841f6a53`. Esto vuelve reproducible **la exportación actual del artefacto**; no determina la exactitud posicional ni el datum fuente de la geometría legal.

Con bounds nativos float32, el exceso de cierre se reprodujo en **48,375556 km² (~0,00456988 %)**. Con bounds derivados por puntos medios entre los centros float32, el cierre fue cero dentro de la precisión numérica observada. El resultado se mantuvo prácticamente igual entre segmentaciones 0,05°, 0,02° y 0,01° y las proyecciones EPSG:3577/EPSG:6933. La variante derivada cierra porque crea intervalos contiguos por construcción; ese cierre **no demuestra** que sea científicamente más correcta.

El ensayo puntual selecciona de manera determinista un punto interior de la geometría exploratoria y ajusta cada grilla a su centro más cercano. Los centros resultantes son distintos y sus huellas varían aproximadamente de 106 a 3.309 km² en el cálculo proyectado diagnóstico. El ejemplo valida el procedimiento, no propone un sitio científico ni una observación espacialmente co-localizada.

La recomendación técnica es que César considere autorizar este GeoJSON **solo como artefacto de prueba** y que el primer ensayo descriptivo futuro use coordenadas de sitio declaradas previamente, con una celda independiente por producto, offsets y bounds conservados. César debe elegir los sitios y aprobar la regla. QA IMERG permanece `unassessed`; el linaje de máscara GLDAS es incierto; Gate R y Gate T siguen pendientes. No se leyeron valores científicos para este ensayo puntual, no se calcularon agregaciones regionales y no se realizaron inferencias ni entrenamiento.

## Evidencia y procedencia de la geometría

### Artefacto auditado

El GeoJSON exploratorio se leyó en el checkout original, en modo solo lectura. Es un `Polygon` válido, de un componente, sin agujeros y con 14.138 vértices incluyendo el cierre. Su bbox WGS84 es `[138,568466639, −37,682084144087, 152,488546389, −24,5856180792855]`. El archivo tiene 477.805 bytes. El artefacto no se copia ni versiona con esta PR.

### Comprobación oficial en línea

El [ítem de la biblioteca MDBA](https://library.mdba.gov.au/data_product/https-mdba-maps-arcgis-com-home-item-html-id-ba731d77d80947fbbcbf7524364372ff-overview) describe el límite definido en Section 4(1) del Water Act 2007, dice que deriva de *Australia’s River Basins 1997* (30-jun-1997) y declara licencia Creative Commons Attribution. La metadata ArcGIS consultada identifica como publicador a MDBA, atribución a DCCEEW y licencia CC BY 4.0; el timestamp `modified` del ítem fue 14-ene-2026 21:08:32 UTC, y no se trata como fecha de edición topográfica.

El [FeatureServer de MDBA](https://services8.arcgis.com/5xxEi7I2m6ml97fE/arcgis/rest/services/boundary_gdb/FeatureServer/0?f=pjson) expone una capa poligonal en WKID 102100/latestWkid 3857 (EPSG:3857). La consulta de lectura usada para reproducir la exportación fue `where=1=1`, `outFields=*`, `returnGeometry=true`, `outSR=4326`, `f=geojson`. La respuesta de un feature tuvo el mismo tamaño y SHA-256 del artefacto local, y la geometría fue topológicamente igual (Hausdorff 0; diferencia simétrica 0). El procedimiento y el resultado se registran en el manifiesto.

La exportación reproducible no identifica qué datum/transformación se usó para generar la geometría del servicio desde su fuente. El CRS 3857 informado por la capa y EPSG:4326 de salida describen servicio/exportación; no prueban el datum de captura. La guía oficial de Geoscience Australia para [Australia’s River Basins 1997](https://www.ga.gov.au/bigobj/GA3352.pdf) indica coordenadas geográficas en grados decimales con datum AGD66 para **el dataset original**. MDBA señala ese dataset como origen, pero no publica en la metadata consultada la cadena de transformaciones del límite legal re-servido. Por ello, no atribuyo AGD66 automáticamente a ese límite.

| Propiedad | Evidencia | Límite de interpretación |
|---|---|---|
| Origen declarado | *Australia’s River Basins 1997*, fechado 30-jun-1997, según MDBA | No prueba que la exportación legal sea idéntica al dato fuente ni fija datum de la capa actual |
| Servicio | EPSG:3857 (WKID 102100/3857) | CRS de almacenamiento/servicio declarado, no datum del origen |
| Exportación | GeoJSON EPSG:4326 mediante query `outSR=4326` | Hash byte-identical con la caché en la consulta del 15-nov-2026; un servicio vivo puede cambiar |
| Datum del original | AGD66 para Australia’s River Basins 1997, según guía GA | La transformación exacta al servicio no se encontró documentada |
| Licencia | MDBA declara CC BY 4.0 / Creative Commons Attribution | Conservar atribución MDBA y DCCEEW; verificar requisitos de derivados antes de redistribuir |
| Geometría/área | Polígono válido; hash local y remoto idéntico; área solo diagnóstica | No establece exactitud posicional, escala, edición histórica legal ni área oficial |

### Alternativas de artefacto

1. **Exportación del límite legal actual del FeatureServer (recomendación para un test controlado).** Su query y respuesta se reprodujeron exactamente en la verificación actual. La consulta puede volver a ejecutarse y el hash permite detectar cambios. Conserva el propósito legal del límite MDBA, aunque la versión de geometría/datum fuente sigue desconocida.
2. **Dataset fuente Australia’s River Basins 1997.** La guía GA informa AGD66, lo que aporta una referencia para estudiar la procedencia del original. No se obtuvo ni comparó el archivo nacional original en esta tarea; el dataset es fuente atribuida, no sustituto automáticamente equivalente del límite legal Section 4(1).
3. **Otros productos de cuenca, límites de plan o jurisdicciones.** No son intercambiables con el límite del Water Act por nombre o proximidad. No se encontró en esta auditoría un artefacto alternativo documentado que mantenga la misma definición jurídica y mejore la trazabilidad completa.

**Recomendación para decisión de César:** `approve_specific_artifact_for_test` para el hash anterior, si desea autorizar pruebas geométricas controladas. La recomendación cubre solo la identidad/exportación para test; no aprueba el uso como máscara estadística, el datum, Gate R ni un denominador regional. Si esa autorización no se concede, los resultados existentes deben seguir rotulados como diagnóstico de una referencia exploratoria.

## Sensibilidad de bounds IMERG

### Métodos y alcance

- **A — `native_float32_bounds`:** lee `Grid/lat_bnds` y `Grid/lon_bnds` del granule original y convierte los números float32 a float64 solo durante el cálculo. Nunca modifica el HDF5.
- **B — `center_midpoint_bounds`:** deriva por separado bounds desde los centros float32 almacenados, usando puntos medios contiguos en float64 y media separación terminal en los extremos. No reemplaza ni edita los bounds NASA.

Para ambos métodos se cuentan gaps/overlaps locales bajo tolerancias angulares explícitas; se calculan intersecciones y fracciones de celdas en EPSG:3577 y EPSG:6933 con segmentos de hasta 0,05°, 0,02° y 0,01°. La misma geometría se proyecta bajo cada configuración. La operación PROJ no está fijada a una operación de datum aprobada. Las áreas son sumas planas de un overlay diagnóstico, nunca áreas oficiales.

### Resultados reproducidos

En la ventana de bounds que intersecta el bbox MDBA más el centro inmediatamente adyacente a cada lado, a tolerancia estricta `1e-12°`:

| Bounds IMERG | Gaps latitud | Overlaps latitud | Gaps longitud | Overlaps longitud | Máximo gap | Máximo overlap |
|---|---:|---:|---:|---:|---:|---:|
| Nativos float32 | 83 | 0 | 0 | 56 | ~3,81×10⁻⁶° (suma 0,000202179°) | ~1,53×10⁻⁵° (suma 0,000854492°) |
| Derivados por puntos medios | 0 | 0 | 0 | 0 | 0° | 0° |

Los conteos cambian al aumentar la tolerancia: a `1e-6°` siguen contando los seams nativos; a `1e-5°` los gaps de latitud dejan de clasificarse, mientras que overlaps de longitud mayores a la tolerancia permanecen; a `2e-5°` no se clasifican seams locales. La tolerancia solo controla el conteo; no cambia ni arregla coordenadas o bounds.

En EPSG:3577 y segmentación 0,02°, A reprodujo 10.467 celdas con intersección positiva, 747 parciales y suma de intersecciones `1.058.622,381821 km²`; el área transformada de referencia fue `1.058.574,006265 km²`. Exceso: `48,375557 km²` o `0,00456988 %`. B retuvo 10.467 y 747 y produjo `1.058.574,006265 km²`, diferencia numérica de cierre aproximadamente cero.

El exceso nativo se mantuvo en `48,375556–48,375557 km²` a través de los seis ajustes de proyección/segmentación. La suma derivada cerró al área proyectada en todos los casos por construcción de intervalos contiguos. Cambiar la segmentación/proyección alteró el área transformada del polígono aproximadamente milésimas de km², muy por debajo del exceso; cambiar los bounds alteró la suma en aproximadamente 48,3756 km². **Esto vincula el exceso reproducido con la partición nativa de bounds frente a la alternativa contigua dentro de este algoritmo**, pero no permite concluir que float32 sea la única causa ni que la alternativa B sea correcta. El cierre cero de B es una propiedad del método de teselación y no una validación independiente.

La sensibilidad identifica causas potenciales y su magnitud observada:

- **Gaps/overlaps y límite de celdas:** los bounds nativos incluyen seams locales medibles; los intervalos midpoint son contiguos por definición. Este cambio domina la diferencia del cierre en el cálculo actual.
- **Precisión float32:** los centros y límites nativos tienen cuantización float32; los puntos medios calculados a float64 evitan duplicar/omitir límites internos, pero derivan igualmente de centros cuantizados.
- **Segmentización:** las tres longitudes no removieron el exceso ni alteraron conteos de celdas en esta zona; el área de referencia varió a escala de milésimas de km².
- **Proyección:** EPSG:3577 y EPSG:6933 dieron el mismo exceso nativo con diferencias pequeñas de referencia. Esto no acredita exactitud, ni fija la transformación datum/posición de la frontera.
- **Convención de celda y precisión geométrica:** el área depende de bordes construidos como segmentos en lon/lat, su segmentización y la geometría MDBA usada. El test no posee una huella física independiente que permita establecer el límite correcto de cada píxel.

No se fija una tolerancia QA por este resultado. Los conteos por tolerancia sirven para sensibilidad técnica, no para excluir mediciones. B se conserva como alternativa de comparación, no como reemplazo de la metadata NASA.

## Ensayo puntual de soporte común

La prueba de concepto usa el punto `representative_point` de la geometría MDBA actual, solo para seleccionar una ubicación determinista y reproducible. Para cada producto localiza su celda de centro más cercano en EPSG:3577, mide el offset geodésico desde el punto y guarda índices fila/columna, centro, bounds, método, unidad y SHA-256 de enero. Los resultados llevan `candidate_not_approved`.

| Producto | Variable / unidad | Índice 0-based (fila, columna) | Centro lon/lat | Offset al punto | Área proyectada de huella diagnóstica |
|---|---|---|---|---:|---:|
| IMERG Final | precipitation · mm/hr | (588, 3270) | (147,05000305°, −31,14999962°) | 3,176 km | 105,73 km² |
| MERRA-2 | T2M · K | (118, 523) | (146,875°, −31,000°) | 20,463 km | 3.308,90 km² |
| GLDAS Noah | SoilMoi0_10cm_inst · kg m⁻² | (115, 1308) | (147,125°, −31,125°) | 9,851 km | 660,93 km² |

Las distancias entre los tres centros seleccionados varían entre `7,671 km` (GLDAS–IMERG), `23,569 km` (IMERG–MERRA-2) y `27,593 km` (GLDAS–MERRA-2). Cada celda tiene resolución y forma diferentes. Las áreas proyectadas se reportan solo para hacer visible la escala de las huellas, no como áreas de cobertura aprobadas. El punto no se considera un sitio científico representativo; depende de la geometría candidata y requiere selección explícita de César.

### Matriz de alternativas

| Criterio | A. Punto predefinido y celda por producto | B. Intersección celda-polígono | C. Regrillado / pesos de área |
|---|---|---|---|
| Comparabilidad del soporte | Media para ubicación común declarada; las huellas de píxel siguen diferentes | Alta en el sentido geométrico si bounds/geometría se fijan; no homogeneiza variable ni resolución | Podría ser alta en una grilla destino, sujeto a algoritmo y conservación por variable |
| Reproducción | Alta si coordenadas, regla de asignación, hashes e índices se congelan | Alta con bounds, CRSs, versión y tolerancias fijadas | Media: requiere pesos, método y versiones precisos |
| Sesgo/interpolación | Bajo si solo selecciona celda; persiste error de representatividad de sitio | Medio: fracciones dependen de límite, bordes y nodata | Alto: interpolación/promedio puede suavizar y alterar resolución/variabilidad |
| Sensibilidad a bordes | Baja para sitio interior; alta si sitio cae cerca de un borde | Alta; 747 celdas IMERG, 123 MERRA-2 y 281 GLDAS fueron parciales en DS-07 con la geometría candidata | Alta si máscara/weights y bordes varían |
| Diferencias de resolución | No las oculta; las reporta como offsets y huellas distintas | Las deja explícitas, pero genera pesos de área solo si aprobados | Busca homogeneizar, pero puede degradar la resolución fina o inventar detalle grueso |
| Faltantes/QA | Mantener estado por celda; QA por producto aún pendiente | Debe definir validez y fracción de cobertura; no aplicar flags no aprobados | Reglas necesarias antes de interpolar/ponderar; faltantes pueden propagarse |
| Coste | Bajo | Medio | Alto |
| Estado | Recomendación para un primer **ensayo**, por menor transformación y mayor trazabilidad; César debe escoger sitios/regla | Candidato diagnóstico; no usar como denominador productivo | Propuesta conceptual, no implementada |

### Protocolo de primer ensayo propuesto

1. César selecciona y documenta uno o más sitios WGS84 y su fuente/justificación; no usar automáticamente el punto geométrico de esta corrida.
2. Congelar geometría usada solo como referencia, sitio, versión de productos, hashes, instante/mes y regla de lookup (contener punto si los bounds se aprueban; si se usa centro más cercano, registrar el offset y probar sensibilidad a la alternativa).
3. Para cada producto emitir un registro independiente: CMR/granule ID, variable, unidad original, periodo, SHA, índice, centro, bounds nativos o inferidos, valor nativo sin transformar y estados fill/NaN/QA separados. No construir un único valor multivariable que sugiera soporte idéntico.
4. Reportar distancia del sitio al centro y distancias entre centros; conservar grillas y footprints. No declarar tolerancia universal basada solo en tamaño de píxel: César debe aprobar criterio acorde a pregunta y escala.
5. Repetir frente a alternativa de asignación/vecindad y bounds IMERG; informar la sensibilidad sin elegir la variante que “cierra mejor” por conveniencia.

## Propuesta de protocolo de Gate R

Gate R evalúa si existe base reproducible para una serie/soporte espacial regional aprobado. **Propuesta, no aprobación:**

1. **Geometría:** César selecciona una edición y propósito; archivo/licencia/atribución, fecha, identidad, SHA-256, geometría válida, CRS de fuente/exportación y operación de datum deben estar documentados. Si datum o precisión son inciertos, explicitar impacto y limitar el alcance; no inferirlos desde un CRS de servicio.
2. **Soporte:** declarar por producto si el observable es celda, sitio, rejilla común o polígono. Mantener bounds NASA y bounds inferidos separados; conservar la transformación como artefacto versionado con parámetros, software/versión y pruebas.
3. **Bordes:** probar puntos y celdas dentro/fuera/en borde, agujeros, discontinuidades, antimeridiano y región sin cobertura. Si hay fracción/área, cuantificar seams, celdas parciales, conservación y sensibilidad a bounds/proyección/segmentación.
4. **Faltantes y QA:** inventariar por producto/mes `finite`, `fill`, `missing`, QA presente/aplicada/rechazada; reglas explícitas con revisión científica. Cero legítimo no equivale a null. IMERG sigue `unassessed` hasta evaluación de criterios. El linaje de máscara GLDAS debe resolverse o reconocerse como limitación aceptada explícitamente.
5. **Cobertura y denominadores:** si una agregación futura se autoriza, definir *antes* `A_valid/A_intersection`, `A_valid/A_basin`, regla para pesos, cobertura mínima y tratamiento de meses incompletos; revisar ambos denominadores y sensibilidad. No presentar área proyectada actual como área oficial.
6. **Validación independiente:** reproducir una muestra por producto y mes desde hashes/manifiestos; demostrar idempotencia, no filtración de fuentes, conservación de unidades y comparación de alternativas; revisión por César antes de marcar aprobado.

**Gate R** trata geometría, QA espacial, soporte, faltantes y cobertura de una serie regional. **Gate T** trata suficiencia temporal, calendarios, homogeneidad temporal y protocolo de tendencia. Tener doce meses de 2005 no supera Gate T ni permite tendencia de largo plazo, correlaciones inferenciales o modelos productivos.

## Reproducibilidad

El módulo [`research/ful125_support_experiment.py`](../research/ful125_support_experiment.py) reutiliza el inventario de FUL-122, el lector de grillas y validaciones geométricas de FUL-124. Accede a archivos NASA en solo lectura, exige 12 registros nativos elegibles por producto y verifica que coordenadas/bounds no cambien en los 12 meses. La salida portable está en [`ful125-support-experiment-2005.json`](../research/manifests/ful125-support-experiment-2005.json); incluye IDs, unidades, SHA-256 y tamaño, no rutas locales ni datos crudos.

Las pruebas sintéticas están en [`test_ful125_support_experiment.py`](../research/tests/test_ful125_support_experiment.py). Incluyen hash incorrecto, geometría ausente, discontinuidades y sensibilidad por tolerancia, bounds nativos/derivados, cierre de fixture, repetibilidad, selección de celdas por producto, unidades y estado candidato. Las pruebas FUL-124 existentes cubren geometría inválida, antimeridiano, bordes, ausencia/no monotonicidad de coordenadas y clasificación separada de fill, NaN, cero legítimo y negativos. Las fixtures son sintéticas; no prueban precisión geográfica de NASA/MDBA.

Reproducir desde PowerShell, con rutas existentes de los checkouts anteriores:

```powershell
uv sync --group dev --group research

uv run python -m research.ful125_support_experiment `
  --input-dir "RUTA\checkout-original\data\raw\nasa" `
  --input-dir "RUTA\checkout-ful105\data\raw\nasa" `
  --input-dir "RUTA\checkout-ful105\data\cache\ful-105\be02-handoff\data_root\data\raw\nasa" `
  --input-dir "RUTA\checkout-ful123\data\raw\nasa" `
  --boundary-geojson "RUTA\cache-local\mdba_boundary_4326.geojson" `
  --output research\manifests\ful125-support-experiment-2005.json
```

La prueba local de exportación oficial se hizo por separado mediante la query del FeatureServer; el ejecutor offline no contacta la red. Los valores del manifiesto son reproducibles con los payloads y la versión/configuración de dependencias disponible, pero la operación de transformación PROJ no se fija como fuente científica oficial.

## Decisiones pendientes de César

1. ¿Autoriza el artefacto exacto `d36fe314…f1a6f53` solo para pruebas controladas, manteniendo su datum fuente como desconocido y sin aprobarlo como máscara estadística?
2. ¿Qué sitios y fuente de coordenadas deben usarse en el primer ensayo descriptivo real?
3. ¿La asignación debe usar celda que contiene el punto, centro más cercano, o ambas como sensibilidad? ¿Qué tolerancia, si alguna, exige la pregunta científica?
4. ¿Se mantiene el bounds original IMERG y su exceso medido, o se conserva además un derivado midpoint como análisis de sensibilidad? No se propone sustituir el original.
5. Antes de Gate R: ¿qué tratamiento de fracciones, valores faltantes, QA por producto, máscara/linaje GLDAS, cobertura mínima y denominadores se autorizaría?
6. Gate T permanece por separado: la ventana 2005 disponible no basta para tendencias multianuales.

## Fuentes

- [MDBA Library — Murray–Darling Basin Boundary, Water Act 2007](https://library.mdba.gov.au/data_product/https-mdba-maps-arcgis-com-home-item-html-id-ba731d77d80947fbbcbf7524364372ff-overview).
- [MDBA ArcGIS FeatureServer layer metadata](https://services8.arcgis.com/5xxEi7I2m6ml97fE/arcgis/rest/services/boundary_gdb/FeatureServer/0?f=pjson) y [query endpoint](https://services8.arcgis.com/5xxEi7I2m6ml97fE/arcgis/rest/services/boundary_gdb/FeatureServer/0/query).
- [Geoscience Australia — Australia’s River Basins 1997 user guide](https://www.ga.gov.au/bigobj/GA3352.pdf).
- Evidencia integrada DS-07: [informe](ds-07-colocalizacion-espacial-nasa-2005.md), [código](../research/ful124_spatial_audit.py) y [manifiesto](../research/manifests/ful124-spatial-audit-2005.json).
- Evidencia de QA/linaje: [NASA-03](nasa-03-auditoria-espacial.md), [NASA-04](nasa-04-qa-imerg-muestras.md), [NASA-05](nasa-05-linaje-gldas-2005.md), [DS-06](ds-06-adquisicion-nasa-2005.md) y [registro de decisiones](decisions.md).

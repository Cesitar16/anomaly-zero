# FUL-112 · QA empírica IMERG mensual

**Estado:** Fases 1–3 implementadas en la rama de trabajo. La evaluación de píxeles QA permanece **`unassessed`**; no se aplican filtros ni umbrales. La decisión de producto y publicación corresponde a César.
**Alcance de la Fase 1:** identificar las muestras locales y comprobar su identidad declarada, estructura HDF5, atributos y campos disponibles. Los resultados empíricos y su interpretación provisional se documentan en las secciones de Fases 2 y 3.

## Procedencia y distinción de fuentes

Se inspeccionaron 14 archivos locales: dos gránulos bajo `data/raw/nasa/ful104` identificados como originales NASA (enero de 2005 y enero de 2021) y doce archivos etiquetados como copias NCAR bajo `data/cache/ful-102` (enero a diciembre de 2005). Sus nombres locales, periodos, versión V07B, nombres de granule conservados en `FileHeader`, tamaños y SHA-256 están en [`nasa-04-manifiesto-insumos.json`](nasa-04-manifiesto-insumos.json). Los archivos originales/cache no se incluyen en Git.

La comparación local NASA/NCAR de enero de 2005 produjo el mismo SHA-256 (`bac3b9bc5ee8cc3eb1e5fe844778d54fd86e2b722813055b37f3872e6e4c73d5`) y tamaño, así que esas dos copias son idénticas byte a byte. Para febrero–diciembre no se afirma equivalencia con granules NASA: sus `FileHeader` declaran el nombre original de cada granule, pero no hay una segunda copia NASA local con la que comparar sus hashes. El granule NASA de enero de 2021 es un archivo adicional, no parte de la colección de copias NCAR de 2005.

Los headers identifican `DOIshortName=3IMERGM`, `AlgorithmID=3IMERGM`, `AlgorithmVersion=3IMERGM_7.0`, colección DOI `10.5067/GPM/IMERG/3B-MONTH/07` y `ProductVersion=V07B`. Se preservan como metadatos de producto; este inventario no los convierte en evaluación de QA.

## Estructura y atributos observados

Los 14 archivos tienen el grupo `Grid`, con `precipitation` de shape `(1, 3600, 1800)`, orden declarado `time,lon,lat`, tipo `float32` y unidades `mm/hr`. La variable declara `_FillValue=-9999.900390625` en su representación float32 y `CodeMissingValue=-9999.9`; se registran ambos valores y no se comparan aquí para clasificar píxeles. En `precipitation` no aparecen atributos `scale_factor` ni `add_offset`.

| Campo HDF5 | Presencia en las 14 muestras | Shape / tipo | Atributos registrados en el manifiesto |
|---|---|---|---|
| `Grid/precipitation` | Presente | `(1, 3600, 1800)`, `float32` | `DimensionNames=time,lon,lat`, `units=mm/hr`, `_FillValue`, `CodeMissingValue`, `LongName`; sin escala/offset declarados. |
| `Grid/precipitationQualityIndex` | Presente | `(1, 3600, 1800)`, `float32` | `DimensionNames`, `_FillValue`, `CodeMissingValue`; no declara `units`, `scale_factor` ni `add_offset`. |
| `Grid/randomError` | Presente | `(1, 3600, 1800)`, `float32` | `DimensionNames`, `units=mm/hr`, `_FillValue`, `CodeMissingValue`, `LongName`; sin escala/offset declarados. |
| `Grid/gaugeRelativeWeighting` | Presente | `(1, 3600, 1800)`, `int16` | `DimensionNames`, `units=percent`, `_FillValue=-9999`, `CodeMissingValue=-9999`, `LongName`; sin escala/offset declarados. |

Ninguna de las cuatro variables `Grid/*` inventariadas declara `scale_factor` o `add_offset`; el manifiesto registra explícitamente esos atributos como no declarados. La variable QIm tampoco declara unidades en las muestras inspeccionadas.

Todos los archivos tienen los campos QA listados. Su presencia estructural no significa que hayan sido evaluados, aplicados como filtro ni aprobados. Sus significados científicos y distribuciones quedan para fases posteriores.

Las coordenadas son `time (1)`, `lon (3600)`, `lat (1800)`, `lon_bnds (3600, 2)`, `lat_bnds (1800, 2)` y `time_bnds (1, 2)`. `time` declara unidades en segundos desde `1980-01-06 00:00:00 UTC`, calendario `julian` y bounds `time_bnds`; las coordenadas declaran sus ejes/unidades. Shapes, tipos y atributos útiles de coordenadas están en el manifiesto; los arrays completos no se copian al manifiesto.

## Método reproducible

La herramienta [`research/auditar_imerg_qa.py`](../research/auditar_imerg_qa.py) calcula SHA-256, comprueba el nombre y periodo contra el `FileName` interno de `FileHeader`, verifica `DOIshortName`, `AlgorithmID`, versión, unidad, dimensiones y shapes esenciales, y registra cada campo QA como presente o ausente. Los campos QA son opcionales para la estructura: si faltan, el inventario los anota y continúa; precipitación, coordenadas, bounds, identidad o dimensiones esenciales inconsistentes hacen fallar el proceso.

El JSON detallado se guarda por defecto en `data/cache/ful112/imerg_qa_inventory.json`, excluido de Git. Las rutas se pueden configurar desde cualquier checkout:

```powershell
uv run python -m research.auditar_imerg_qa `
  --nasa-dir E:\datos\nasa\ful104 `
  --ncar-dir E:\datos\cache\ful-102 `
  --output data\cache\ful112\imerg_qa_inventory.json
```

La fase se probó con fixtures HDF5 offline para campos QA presentes/ausentes, atributos fill float32 y `CodeMissingValue`, hash, identidad/periodo incompatibles y dimensiones inválidas. No se leyeron estadísticas de píxeles para producir este inventario.

## Estado de los entregables de Fase 1

- [x] Rama aislada de Lucas creada desde `origin/dev`; no se modificó la rama ni la PR de FUL-111.
- [x] Dos archivos NASA y doce archivos NCAR inventariados; identidad byte a byte comprobada para NASA/NCAR enero de 2005.
- [x] Manifiesto versionable con hash, metadatos y perfil estructural de los 14 archivos.
- [x] Script reproducible con rutas configurables; campos QA opcionales registrados y errores esenciales rechazados.
- [x] Pruebas offline pasan; en el conjunto `research/tests` se ejecutaron 52 pruebas.
- [x] Estado QA reportado como `unassessed`; sin umbrales ni filtros.

## Límites y continuación

- La etiqueta “NASA” corresponde a la ubicación y procedencia documentada de los dos gránulos autenticados. Las copias NCAR se mantienen separadas, y la identidad binaria con NASA solo está demostrada para enero de 2005.
- La lectura de `_FillValue` y `CodeMissingValue` en esta fase es descriptiva; no define todavía la máscara de missing, tratamiento QA o reglas de publicación.
- QIm, `randomError` y `gaugeRelativeWeighting` aún no se resumen ni interpretan empíricamente aquí.
- No se calculan conteos por universo global, caja o centros/cuenca en esta fase. Esos ámbitos y denominadores pertenecen a la Fase 2.
- No se infieren medias regionales, tendencias, series multidecenales ni aprobación de QA.

## Fuentes internas

- [Manifiesto estructural y de hashes](nasa-04-manifiesto-insumos.json).
- [FUL-105: lector IMERG mensual y pruebas](../research/ful105_imerg.py), [inspector previo de caja 2005](../research/inspeccionar_imerg_caja_2005.py).
- [FUL-110: apoyo científico y fuentes oficiales NASA](apoyo-cientifico-az03.md), sección 5; no se repite aquí su explicación teórica.

## Fase 2 · Conteos y distribuciones por ámbito

### Selección y universos analizados

Se procesaron 13 muestras sin duplicar enero de 2005: NASA enero de 2005, copias NCAR febrero–diciembre de 2005 y NASA enero de 2021. Los análisis de cada mes se limitan al archivo y fuente indicados. Las 12 copias NCAR preservan un nombre de granule NASA en `FileHeader`; solo enero de 2005 tiene equivalencia byte a byte confirmada con el granule NASA.

Los universos son independientes: `global` (todas las celdas), `bbox_centers` (centros dentro de 138–153°E y −38–−24°, límites inclusivos) y `basin_centers` (centros dentro de la geometría MDBA mediante `CenterMaskCache`; sin ponderación de área). El GeoJSON de MDBA utilizado (`mdba_boundary_4326.geojson`) tiene SHA-256 `d36fe31424758cc4fb8eef25e21b835bb5c05c793c746e8a1eb7b5a5841f6a53`, incluido también en cada muestra del resumen JSON. El orden nativo de los arrays es `time,lon,lat`; las máscaras `lat,lon` se trasponen una sola vez y se prueban contra fixtures con coordenadas asimétricas.

Convención de celdas: `N` es el denominador total del ámbito. En cada variable se muestran `F/NF/V/0` = fill / no finito distinto de fill / finito no-fill / cero válido. Cero es subconjunto de `V`; `F + NF + V = N`. Los campos auxiliares se resumen tal cual se almacenan; no se aplica QA.

### Conteos por mes, campo y ámbito

| Periodo | Origen | Ámbito | N | Precipitación F/NF/V/0 | QIm F/NF/V/0 | RandomError F/NF/V/0 | GaugeWeight F/NF/V/0 |
|---|---|---|---:|---:|---:|---:|---:|
| 2005-01 | NASA | global | 6480000 | 54671/0/6425329/895459 | 54671/0/6425329/0 | 54671/0/6425329/0 | 54671/0/6425329/4928353 |
| 2005-01 | NASA | bbox_centers | 21000 | 0/0/21000/270 | 0/0/21000/0 | 0/0/21000/0 | 0/0/21000/1701 |
| 2005-01 | NASA | basin_centers | 10092 | 0/0/10092/218 | 0/0/10092/0 | 0/0/10092/0 | 0/0/10092/0 |
| 2005-02 | NCAR | global | 6480000 | 57530/0/6422470/976666 | 57530/0/6422470/0 | 57530/0/6422470/0 | 57530/0/6422470/4921637 |
| 2005-02 | NCAR | bbox_centers | 21000 | 0/0/21000/1859 | 0/0/21000/0 | 0/0/21000/0 | 0/0/21000/1701 |
| 2005-02 | NCAR | basin_centers | 10092 | 0/0/10092/90 | 0/0/10092/0 | 0/0/10092/0 | 0/0/10092/0 |
| 2005-03 | NCAR | global | 6480000 | 57193/0/6422807/1022661 | 57193/0/6422807/0 | 57193/0/6422807/0 | 57193/0/6422807/4921650 |
| 2005-03 | NCAR | bbox_centers | 21000 | 0/0/21000/749 | 0/0/21000/0 | 0/0/21000/0 | 0/0/21000/1701 |
| 2005-03 | NCAR | basin_centers | 10092 | 0/0/10092/266 | 0/0/10092/0 | 0/0/10092/0 | 0/0/10092/0 |
| 2005-04 | NCAR | global | 6480000 | 58833/0/6421167/868762 | 58833/0/6421167/0 | 58833/0/6421167/0 | 58833/0/6421167/4920197 |
| 2005-04 | NCAR | bbox_centers | 21000 | 0/0/21000/2109 | 0/0/21000/0 | 0/0/21000/0 | 0/0/21000/1701 |
| 2005-04 | NCAR | basin_centers | 10092 | 0/0/10092/1298 | 0/0/10092/0 | 0/0/10092/0 | 0/0/10092/0 |
| 2005-05 | NCAR | global | 6480000 | 54001/0/6425999/809529 | 54001/0/6425999/0 | 54001/0/6425999/0 | 54001/0/6425999/4924872 |
| 2005-05 | NCAR | bbox_centers | 21000 | 0/0/21000/347 | 0/0/21000/0 | 0/0/21000/0 | 0/0/21000/1701 |
| 2005-05 | NCAR | basin_centers | 10092 | 0/0/10092/23 | 0/0/10092/0 | 0/0/10092/0 | 0/0/10092/0 |
| 2005-06 | NCAR | global | 6480000 | 41302/0/6438698/942652 | 41302/0/6438698/0 | 41302/0/6438698/0 | 41302/0/6438698/4940395 |
| 2005-06 | NCAR | bbox_centers | 21000 | 0/0/21000/0 | 0/0/21000/0 | 0/0/21000/0 | 0/0/21000/1701 |
| 2005-06 | NCAR | basin_centers | 10092 | 0/0/10092/0 | 0/0/10092/0 | 0/0/10092/0 | 0/0/10092/0 |
| 2005-07 | NCAR | global | 6480000 | 39547/0/6440453/1068404 | 39547/0/6440453/0 | 39547/0/6440453/0 | 39547/0/6440453/4942526 |
| 2005-07 | NCAR | bbox_centers | 21000 | 0/0/21000/16 | 0/0/21000/0 | 0/0/21000/0 | 0/0/21000/1701 |
| 2005-07 | NCAR | basin_centers | 10092 | 0/0/10092/16 | 0/0/10092/0 | 0/0/10092/0 | 0/0/10092/0 |
| 2005-08 | NCAR | global | 6480000 | 32471/0/6447529/1086771 | 32471/0/6447529/0 | 32471/0/6447529/0 | 32471/0/6447529/4946549 |
| 2005-08 | NCAR | bbox_centers | 21000 | 0/0/21000/289 | 0/0/21000/0 | 0/0/21000/0 | 0/0/21000/1701 |
| 2005-08 | NCAR | basin_centers | 10092 | 0/0/10092/0 | 0/0/10092/0 | 0/0/10092/0 | 0/0/10092/0 |
| 2005-09 | NCAR | global | 6480000 | 28493/0/6451507/1045227 | 28493/0/6451507/0 | 28493/0/6451507/0 | 28493/0/6451507/4951971 |
| 2005-09 | NCAR | bbox_centers | 21000 | 0/0/21000/0 | 0/0/21000/0 | 0/0/21000/0 | 0/0/21000/1701 |
| 2005-09 | NCAR | basin_centers | 10092 | 0/0/10092/0 | 0/0/10092/0 | 0/0/10092/0 | 0/0/10092/0 |
| 2005-10 | NCAR | global | 6480000 | 31474/0/6448526/1054894 | 31474/0/6448526/0 | 31474/0/6448526/0 | 31474/0/6448526/4947150 |
| 2005-10 | NCAR | bbox_centers | 21000 | 0/0/21000/0 | 0/0/21000/0 | 0/0/21000/0 | 0/0/21000/1701 |
| 2005-10 | NCAR | basin_centers | 10092 | 0/0/10092/0 | 0/0/10092/0 | 0/0/10092/0 | 0/0/10092/0 |
| 2005-11 | NCAR | global | 6480000 | 31188/0/6448812/943883 | 31188/0/6448812/0 | 31188/0/6448812/0 | 31188/0/6448812/4948461 |
| 2005-11 | NCAR | bbox_centers | 21000 | 0/0/21000/3 | 0/0/21000/0 | 0/0/21000/0 | 0/0/21000/1701 |
| 2005-11 | NCAR | basin_centers | 10092 | 0/0/10092/0 | 0/0/10092/0 | 0/0/10092/0 | 0/0/10092/0 |
| 2005-12 | NCAR | global | 6480000 | 31484/0/6448516/1049305 | 31484/0/6448516/0 | 31484/0/6448516/0 | 31484/0/6448516/4948988 |
| 2005-12 | NCAR | bbox_centers | 21000 | 0/0/21000/0 | 0/0/21000/0 | 0/0/21000/0 | 0/0/21000/1701 |
| 2005-12 | NCAR | basin_centers | 10092 | 0/0/10092/0 | 0/0/10092/0 | 0/0/10092/0 | 0/0/10092/0 |
| 2021-01 | NASA | global | 6480000 | 39564/0/6440436/973379 | 39564/0/6440436/0 | 39564/0/6440436/0 | 39564/0/6440436/4917792 |
| 2021-01 | NASA | bbox_centers | 21000 | 0/0/21000/0 | 0/0/21000/0 | 0/0/21000/0 | 0/0/21000/1701 |
| 2021-01 | NASA | basin_centers | 10092 | 0/0/10092/0 | 0/0/10092/0 | 0/0/10092/0 | 0/0/10092/0 |

Los denominadores son constantes por scope porque los 14 archivos comparten la grilla 3600×1800: global 6.480.000, bbox 21.000 y centros de cuenca 10.092. Estos son conteos de celdas de centro, no cobertura de superficie.

### Resúmenes de distribución empírica

Las celdas de esta tabla reportan `n; min / p05 / p25 / p50 / p75 / p95 / max` entre valores finitos no-fill, sin recodificación ni cortes. QIm no declara unidades en los HDF5; `randomError` se mantiene en mm/hr y `gaugeRelativeWeighting` en percent. El histograma exacto del peso de gauge se entrega por valor observado en el JSON local regenerable, sin agruparlo en clases inventadas.

| Periodo | Origen | Ámbito | QIm | RandomError (mm/hr) | GaugeRelativeWeighting (%) |
|---|---|---|---|---|---|
| 2005-01 | NASA | global | n=6425329; 0.250 / 2.170 / 2.620 / 3.650 / 3.990 / 23.020 / 1074.200 | n=6425329; 0.00100 / 0.00600 / 0.00800 / 0.01400 / 0.02900 / 0.06200 / 0.26400 | n=6425329; 0 / 0 / 0 / 0 / 0 / 85 / 100 |
| 2005-01 | NASA | bbox_centers | n=21000; 2.760 / 3.800 / 27.150 / 69.220 / 218.622 / 425.515 / 957.420 | n=21000; 0.00100 / 0.00200 / 0.00200 / 0.00300 / 0.00500 / 0.02600 / 0.05700 | n=21000; 0 / 0 / 93 / 96 / 98 / 99 / 99 |
| 2005-01 | NASA | basin_centers | n=10092; 20.480 / 26.540 / 49.215 / 98.805 / 224.417 / 402.277 / 892.080 | n=10092; 0.00100 / 0.00200 / 0.00200 / 0.00300 / 0.00300 / 0.00500 / 0.00700 | n=10092; 92 / 93 / 95 / 97 / 99 / 99 / 99 |
| 2005-02 | NCAR | global | n=6422470; 0.320 / 1.960 / 2.400 / 3.340 / 3.610 / 22.670 / 938.890 | n=6422470; 0.00100 / 0.00600 / 0.00800 / 0.01500 / 0.03400 / 0.06600 / 0.33300 | n=6422470; 0 / 0 / 0 / 0 / 0 / 86 / 100 |
| 2005-02 | NCAR | bbox_centers | n=21000; 2.700 / 3.480 / 29.890 / 68.725 / 210.507 / 441.595 / 660.570 | n=21000; 0.00100 / 0.00100 / 0.00200 / 0.00300 / 0.00400 / 0.03300 / 0.07200 | n=21000; 0 / 0 / 93 / 97 / 98 / 99 / 99 |
| 2005-02 | NCAR | basin_centers | n=10092; 15.890 / 30.490 / 48.895 / 97.675 / 229.947 / 453.117 / 612.140 | n=10092; 0.00100 / 0.00200 / 0.00200 / 0.00300 / 0.00400 / 0.00500 / 0.00800 | n=10092; 92 / 94 / 96 / 98 / 99 / 99 / 99 |
| 2005-03 | NCAR | global | n=6422807; 0.340 / 2.170 / 2.760 / 3.760 / 4.000 / 22.840 / 1145.200 | n=6422807; 0.00100 / 0.00600 / 0.00800 / 0.01700 / 0.03500 / 0.06200 / 0.22200 | n=6422807; 0 / 0 / 0 / 0 / 0 / 85 / 100 |
| 2005-03 | NCAR | bbox_centers | n=21000; 2.660 / 3.710 / 31.300 / 75.140 / 215.775 / 447.932 / 793.490 | n=21000; 0.00100 / 0.00100 / 0.00200 / 0.00200 / 0.00300 / 0.02100 / 0.07300 | n=21000; 0 / 0 / 93 / 97 / 99 / 99 / 99 |
| 2005-03 | NCAR | basin_centers | n=10092; 17.610 / 29.655 / 52.975 / 106.440 / 222.475 / 423.009 / 687.460 | n=10092; 0.00100 / 0.00100 / 0.00200 / 0.00200 / 0.00200 / 0.00300 / 0.00600 | n=10092; 91 / 94 / 96 / 98 / 99 / 99 / 99 |
| 2005-04 | NCAR | global | n=6421167; 0.420 / 2.100 / 2.640 / 3.620 / 3.860 / 22.770 / 1156.590 | n=6421167; 0.00100 / 0.00600 / 0.00800 / 0.01600 / 0.03400 / 0.06200 / 0.39300 | n=6421167; 0 / 0 / 0 / 0 / 0 / 86 / 100 |
| 2005-04 | NCAR | bbox_centers | n=21000; 2.720 / 3.550 / 34.280 / 74.580 / 185.955 / 433.311 / 1016.720 | n=21000; 0.00100 / 0.00100 / 0.00100 / 0.00200 / 0.00200 / 0.02000 / 0.04800 | n=21000; 0 / 0 / 94 / 97 / 99 / 99 / 99 |
| 2005-04 | NCAR | basin_centers | n=10092; 19.860 / 34.820 / 58.620 / 105.515 / 197.930 / 402.433 / 823.320 | n=10092; 0.00100 / 0.00100 / 0.00100 / 0.00100 / 0.00200 / 0.00200 / 0.00300 | n=10092; 92 / 94 / 96 / 98 / 99 / 99 / 99 |
| 2005-05 | NCAR | global | n=6425999; 0.280 / 2.170 / 2.810 / 3.730 / 3.990 / 22.970 / 1028.200 | n=6425999; 0.00100 / 0.00600 / 0.00900 / 0.01600 / 0.03300 / 0.06100 / 0.26900 | n=6425999; 0 / 0 / 0 / 0 / 0 / 85 / 100 |
| 2005-05 | NCAR | bbox_centers | n=21000; 2.740 / 3.580 / 33.547 / 80.385 / 191.875 / 456.640 / 911.250 | n=21000; 0.00100 / 0.00100 / 0.00100 / 0.00200 / 0.00400 / 0.01900 / 0.06600 | n=21000; 0 / 0 / 92 / 96 / 99 / 99 / 99 |
| 2005-05 | NCAR | basin_centers | n=10092; 17.730 / 37.641 / 59.827 / 105.950 / 201.505 / 369.289 / 624.560 | n=10092; 0.00100 / 0.00100 / 0.00100 / 0.00200 / 0.00300 / 0.00600 / 0.00800 | n=10092; 90 / 92 / 96 / 98 / 99 / 99 / 99 |
| 2005-06 | NCAR | global | n=6438698; 0.160 / 2.100 / 2.610 / 3.560 / 3.870 / 22.370 / 1286.200 | n=6438698; 0.00100 / 0.00600 / 0.00800 / 0.01600 / 0.03200 / 0.06200 / 0.31600 | n=6438698; 0 / 0 / 0 / 0 / 0 / 86 / 100 |
| 2005-06 | NCAR | bbox_centers | n=21000; 3.410 / 3.770 / 35.817 / 83.550 / 225.887 / 424.590 / 833.390 | n=21000; 0.00200 / 0.00400 / 0.00500 / 0.00700 / 0.01000 / 0.03500 / 0.07700 | n=21000; 0 / 0 / 90 / 96 / 98 / 99 / 99 |
| 2005-06 | NCAR | basin_centers | n=10092; 23.890 / 38.930 / 58.090 / 118.230 / 247.502 / 406.951 / 680.490 | n=10092; 0.00200 / 0.00400 / 0.00500 / 0.00600 / 0.00900 / 0.01100 / 0.01300 | n=10092; 87 / 91 / 94 / 97 / 99 / 99 / 99 |
| 2005-07 | NCAR | global | n=6440453; 0.550 / 2.170 / 2.890 / 3.700 / 4.000 / 22.360 / 1114.120 | n=6440453; 0.00100 / 0.00600 / 0.00800 / 0.01800 / 0.03200 / 0.06200 / 0.28900 | n=6440453; 0 / 0 / 0 / 0 / 0 / 86 / 100 |
| 2005-07 | NCAR | bbox_centers | n=21000; 2.660 / 3.860 / 29.410 / 80.045 / 236.752 / 474.254 / 862.100 | n=21000; 0.00100 / 0.00100 / 0.00200 / 0.00300 / 0.00500 / 0.02800 / 0.06500 | n=21000; 0 / 0 / 92 / 97 / 98 / 99 / 99 |
| 2005-07 | NCAR | basin_centers | n=10092; 19.700 / 28.081 / 59.195 / 106.745 / 264.685 / 471.239 / 751.470 | n=10092; 0.00100 / 0.00100 / 0.00200 / 0.00200 / 0.00400 / 0.00600 / 0.00700 | n=10092; 88 / 92 / 95 / 97 / 99 / 99 / 99 |
| 2005-08 | NCAR | global | n=6447529; 0.320 / 2.170 / 2.730 / 3.700 / 4.000 / 22.290 / 1038.640 | n=6447529; 0.00100 / 0.00600 / 0.00800 / 0.01700 / 0.03300 / 0.06200 / 0.27100 | n=6447529; 0 / 0 / 0 / 0 / 0 / 85 / 100 |
| 2005-08 | NCAR | bbox_centers | n=21000; 2.740 / 3.760 / 34.710 / 85.425 / 203.667 / 420.700 / 764.360 | n=21000; 0.00100 / 0.00100 / 0.00200 / 0.00300 / 0.00400 / 0.02500 / 0.04400 | n=21000; 0 / 0 / 92 / 97 / 98 / 99 / 99 |
| 2005-08 | NCAR | basin_centers | n=10092; 26.800 / 40.795 / 69.557 / 117.085 / 250.062 / 415.799 / 718.550 | n=10092; 0.00100 / 0.00100 / 0.00200 / 0.00300 / 0.00400 / 0.00600 / 0.00800 | n=10092; 89 / 92 / 95 / 97 / 99 / 99 / 99 |
| 2005-09 | NCAR | global | n=6451507; 0.430 / 2.100 / 2.690 / 3.550 / 3.880 / 21.900 / 1193.530 | n=6451507; 0.00100 / 0.00600 / 0.00800 / 0.01700 / 0.03100 / 0.06500 / 0.29800 | n=6451507; 0 / 0 / 0 / 0 / 0 / 85 / 100 |
| 2005-09 | NCAR | bbox_centers | n=21000; 2.150 / 3.760 / 31.852 / 84.220 / 221.642 / 428.830 / 768.840 | n=21000; 0.00100 / 0.00200 / 0.00300 / 0.00400 / 0.00600 / 0.03000 / 0.06700 | n=21000; 0 / 0 / 91 / 96 / 98 / 99 / 99 |
| 2005-09 | NCAR | basin_centers | n=10092; 21.360 / 36.205 / 64.398 / 103.140 / 239.547 / 409.222 / 684.230 | n=10092; 0.00100 / 0.00200 / 0.00300 / 0.00400 / 0.00500 / 0.00700 / 0.00900 | n=10092; 88 / 91 / 95 / 97 / 99 / 99 / 99 |
| 2005-10 | NCAR | global | n=6448526; 0.340 / 2.170 / 2.520 / 3.690 / 4.000 / 22.100 / 1035.820 | n=6448526; 0.00100 / 0.00600 / 0.00700 / 0.01600 / 0.03200 / 0.06200 / 0.23700 | n=6448526; 0 / 0 / 0 / 0 / 0 / 85 / 100 |
| 2005-10 | NCAR | bbox_centers | n=21000; 3.310 / 3.900 / 27.897 / 88.665 / 219.670 / 415.423 / 672.140 | n=21000; 0.00200 / 0.00300 / 0.00400 / 0.00500 / 0.00600 / 0.03600 / 0.06400 | n=21000; 0 / 0 / 91 / 96 / 98 / 99 / 99 |
| 2005-10 | NCAR | basin_centers | n=10092; 16.790 / 26.950 / 63.517 / 114.955 / 240.467 / 381.377 / 590.800 | n=10092; 0.00200 / 0.00300 / 0.00400 / 0.00400 / 0.00500 / 0.00700 / 0.00900 | n=10092; 91 / 92 / 95 / 97 / 98 / 99 / 99 |
| 2005-11 | NCAR | global | n=6448812; 0.340 / 2.100 / 2.490 / 3.590 / 3.870 / 21.790 / 1021.420 | n=6448812; 0.00100 / 0.00600 / 0.00800 / 0.01600 / 0.03300 / 0.06400 / 0.28900 | n=6448812; 0 / 0 / 0 / 0 / 0 / 85 / 100 |
| 2005-11 | NCAR | bbox_centers | n=21000; 3.280 / 3.830 / 30.240 / 82.435 / 225.090 / 427.420 / 887.950 | n=21000; 0.00200 / 0.00300 / 0.00300 / 0.00400 / 0.00500 / 0.04200 / 0.06900 | n=21000; 0 / 0 / 92 / 96 / 98 / 99 / 99 |
| 2005-11 | NCAR | basin_centers | n=10092; 22.360 / 34.080 / 59.057 / 114.550 / 244.255 / 398.813 / 555.930 | n=10092; 0.00200 / 0.00300 / 0.00300 / 0.00400 / 0.00500 / 0.00600 / 0.00800 | n=10092; 89 / 92 / 95 / 97 / 99 / 99 / 99 |
| 2005-12 | NCAR | global | n=6448516; 0.180 / 2.170 / 2.550 / 3.670 / 3.990 / 21.460 / 940.020 | n=6448516; 0.00100 / 0.00500 / 0.00700 / 0.01400 / 0.03200 / 0.06400 / 0.29500 | n=6448516; 0 / 0 / 0 / 0 / 0 / 84 / 100 |
| 2005-12 | NCAR | bbox_centers | n=21000; 3.180 / 3.760 / 27.327 / 78.675 / 201.630 / 421.503 / 940.020 | n=21000; 0.00100 / 0.00200 / 0.00200 / 0.00300 / 0.00400 / 0.02500 / 0.05700 | n=21000; 0 / 0 / 92 / 96 / 98 / 99 / 99 |
| 2005-12 | NCAR | basin_centers | n=10092; 17.780 / 31.695 / 53.880 / 110.280 / 249.410 / 403.790 / 917.730 | n=10092; 0.00100 / 0.00200 / 0.00200 / 0.00300 / 0.00300 / 0.00500 / 0.00800 | n=10092; 91 / 93 / 95 / 97 / 99 / 99 / 99 |
| 2021-01 | NASA | global | n=6440436; 0.380 / 2.170 / 2.650 / 3.650 / 4.000 / 10.290 / 247.570 | n=6440436; 0.00200 / 0.00600 / 0.00800 / 0.01500 / 0.03000 / 0.06600 / 0.21900 | n=6440436; 0 / 0 / 0 / 0 / 0 / 68 / 97 |
| 2021-01 | NASA | bbox_centers | n=21000; 2.010 / 3.650 / 6.370 / 10.670 / 22.840 / 45.630 / 78.350 | n=21000; 0.00400 / 0.00700 / 0.01000 / 0.01300 / 0.01700 / 0.02500 / 0.04700 | n=21000; 0 / 0 / 46 / 66 / 83 / 91 / 93 |
| 2021-01 | NASA | basin_centers | n=10092; 4.340 / 7.350 / 9.840 / 13.445 / 23.552 / 42.020 / 64.950 | n=10092; 0.00400 / 0.00700 / 0.01000 / 0.01300 / 0.01700 / 0.02100 / 0.03300 | n=10092; 33 / 52 / 63 / 73 / 84 / 90 / 92 |

### Interpretación permitida en esta fase

- Los campos QA están presentes en las 13 muestras elegidas; su presencia estructural no significa que una regla se haya aplicado. El estado sigue `unassessed` y `filters_applied`/`thresholds_applied` están vacíos.
- Los valores de QIm se reportan en su escala cruda, sin convertirlos a porcentaje de confianza, exactitud ni clases.
- `randomError` se describe como distribución del campo almacenado; no se interpreta como sesgo o error total.
- El peso de gauge conserva sus valores observados y unidad porcentual; el histograma es descriptivo, no una regla de aceptación.
- No se calculan medias regionales de precipitación, tendencias ni series multidecenales. Los resultados usan centro de celda y no sustituyen los análisis geométricos de FUL-111.

### Reproducción de esta fase

El siguiente comando regenera el inventario y el resumen local usado para estas tablas:

```powershell
uv run python -m research.auditar_imerg_qa `
  --nasa-dir E:\datos\nasa\ful104 `
  --ncar-dir E:\datos\cache\ful-102 `
  --basin-geojson E:\datos\cache\mdba_boundary_4326.geojson `
  --output data\cache\ful112\imerg_qa_inventory.json `
  --summary-output data\cache\ful112\imerg_qa_summary.json
```

El JSON de auditoría contiene hashes por muestra, denominadores, conteos y distribuciones completos y permanece en `data/cache/ful112`, excluido de Git. Las tablas anteriores conservan los resultados agregados que sí deben poder revisarse en el repositorio.


### Cierre de Fase 2

- [x] Trece meses procesados: enero–diciembre de 2005 sin duplicar enero, más enero de 2021; enero de 2005 usa NASA y febrero–diciembre copias NCAR.
- [x] Conteos por campo y universo: total, fill, no finito distinto de fill, finito no-fill y ceros válidos como subconjunto de estos últimos.
- [x] Distribuciones empíricas de QIm, `randomError` y `gaugeRelativeWeighting`; el histograma exacto por valor de este último está en el JSON local regenerable.
- [x] Universo global, caja inclusiva y centros MDBA independientes; orientación `time,lon,lat`/`lat,lon` probada.
- [x] El script no aplica filtros ni umbrales; todos los resultados mantienen estado `unassessed`.
- [x] Suite `research/tests`: 58 pruebas aprobadas; Ruff y `git diff --check` aprobados. No se añadieron gránulos ni cachés al diff.


## Fase 3 · Interpretación científica y opciones para la demo

**Estado de interpretación:** recomendación científica provisional (`DOC/TEC/PARCIAL/INF`). La QA de las muestras permanece `unassessed`: no se aplicaron reglas de aceptación ni filtros y no se fijan umbrales por este informe.

### Fuente primaria y método de contraste

Se contrastaron los atributos de los gránulos y las distribuciones de la Fase 2 contra *IMERG V07 Algorithm Theoretical Basis Document*, versión documental 7.2, fechada el 13 de agosto de 2026. Se consultaron §3.11 (error), §3.12.2 (QIm mensual), §3.13 y tabla 5 (campos de salida), y apéndice §§9.4–9.5 (definición y consejo de uso de QIm). La consulta fue el 15 de noviembre de 2026. El ATBD señala que no existe una definición consensuada de un índice simple y universal de calidad para IMERG; distingue QIh (media hora) de QIm (mensual), y dice que evaluar si esos índices son informativos sigue siendo asunto de investigación.

El método fue: cotejar definición y limitaciones del ATBD con nombre, versión, unidad, atributos y hashes del manifiesto, y después con los conteos y cuantiles de cada muestra/ámbito en las tablas de la Fase 2. Los resúmenes describen celdas del arreglo almacenado. No constituyen una validación externa de precisión, una máscara QA aprobada ni una serie regional independiente.

### Matriz de evidencia e interpretación

| Campo y fuente | Definición documental | Evidencia local y resumen observado | Límite/riesgo de interpretación | Recomendación provisional / estado |
|---|---|---|---|---|
| `Grid/precipitation`; ATBD §3.13 y tabla 5; atributo del gránulo | Estimación combinada satélite–gauge; el campo mensual Final se almacena en mm/hr en los gránulos inspeccionados. El ATBD recomienda este campo merged para uso general. | En las 13 muestras elegidas el campo está presente; fechas, fuente, versión, hashes, `_FillValue` y conteos están en el manifiesto y las tablas Fase 1/2. NASA enero 2005 y enero 2021 son gránulos V07B inspeccionados. | `mm/hr` es una tasa media, no un total mensual en mm. Una conversión depende de duración exacta del periodo y política de faltantes; esta fase no la realiza. Una tasa estimada no equivale por sí sola a observación de gauge. | Para una demo raster, conservar valor y unidad del archivo, fecha, producto/versión y faltantes; rotularlo como tasa mensual estimada. `DOC/TEC/PARCIAL/INF`. |
| `Grid/precipitationQualityIndex` (QIm); ATBD §§3.12.2, 9.4–9.5 | Índice mensual interpretado como número equivalente de gauges requerido para producir el error aleatorio estimado, dadas la precipitación estimada y el área de referencia; el área se expresa como 2,5° × 2,5° lat/lon. No tiene unidad física declarada en los gránulos. | Está presente en las 13 muestras y se guarda sobre el arreglo nativo 0,1°. En enero de 2005, mediana observada: 3,65 global, 69,22 en la caja y 98,805 sobre centros MDBA; distribuciones y denominadores completos por mes están en Fase 2. | La celda de almacenamiento de 0,1° no convierte la cifra en una cuenta de gauges independiente por cada píxel de 0,1°: el soporte de interpretación del índice es 2,5° × 2,5°. El ATBD dice que QIm solo aborda error aleatorio, no sesgo; advierte ambigüedad sobre nieve/superficies congeladas y que el índice mensual es relativamente nuevo a escala 0,1°. No es probabilidad ni exactitud por píxel. Las medianas de ámbitos distintos no son directamente intercambiables. | Si se muestra, hacerlo como diagnóstico contextual con la escala de soporte indicada; evitar colorear o descartar píxeles como si fueran evaluaciones independientes. `DOC/TEC/PARCIAL/INF`. |
| `Grid/randomError`; ATBD §3.11, §3.12.2 y tabla 5 | Estimación de error aleatorio de la precipitación combinada satélite–gauge; el producto la almacena en mm/hr. La fórmula asociada a QIm usa este componente aleatorio, no un error sistemático. | Presente en las 13 muestras, unidades `mm/hr`. Ejemplo enero 2005: mediana 0,014 global, 0,003 en caja y 0,003 en centros MDBA. Cuantiles por mes/ámbito en Fase 2. | No es sesgo, error total, exactitud validada contra estaciones ni intervalo de confianza automático. Un cuantil bajo no demuestra que la precipitación sea exacta en una región. | Puede exponerse como estimación de componente aleatorio junto a unidad, producto y ámbito, sin semáforo de precisión. `DOC/TEC/PARCIAL/INF`. |
| `Grid/gaugeRelativeWeighting`; ATBD §3.13, tabla 5 y atributo del gránulo | Peso relativo de la precipitación de gauge frente a la precipitación multisatélite en la combinación; la unidad declarada localmente es `percent`. | Presente en las 13 muestras. En enero 2005, mediana observada: 0% global, 96% en caja y 97% en centros MDBA. El histograma exacto de cada mes/ámbito está en el JSON local regenerable; el resumen descriptivo completo está en Fase 2. | El porcentaje es una ponderación del proceso de combinación, no el porcentaje de celdas “correctas”, cobertura de estaciones, independencia o garantía de precisión. | Si se incluye en el panel informativo, nombrarlo como ponderación relativa de gauge y mantenerlo separado del mapa de precipitación. `DOC/TEC/PARCIAL/INF`. |

La evidencia cuantitativa de la tabla es `TEC/PARCIAL`: cálculo reproducible sobre las muestras y los ámbitos especificados, no sobre toda la serie histórica ni sobre observaciones independientes. Los valores cero, fill, no finitos y finitos no-fill están separados en la Fase 2; “finito no-fill” significa válido numéricamente para ese conteo, no que supere QA ni que sea apto para inferencia.

### Consejo del ATBD para QIm, sin convertirlo en filtro

El ATBD V07 §9.5 ofrece las etiquetas descriptivas “red” para `0 ≤ QIm < 3`, “yellow” para `3 ≤ QIm < 10` y “green” para `QIm ≥ 10`, asociadas respectivamente a contexto de red gauge pobre, suficiente para ajuste de sesgo con interpolación frecuente, y redes buenas a excelentes. NASA indica que eligió esos rangos para obtener una distribución razonable de las tres clases. Son consejo contextual del documento; **no son umbrales obligatorios de enmascarado, QA universal ni regla aprobada para esta demo**. Tampoco corrigen la diferencia entre el soporte del índice y la grilla fina. La Fase 2 no los aplicó a los datos.

### Opciones de presentación para decisión de César

| Elemento que podría mostrarse | Información necesaria para no inducir a error | Estado |
|---|---|---|
| Mapa mensual de `precipitation` | Producto/colección y versión de archivo; periodo; tasa `mm/hr`; resolución nativa 0,1°; ámbito/geometría y método espacial; faltantes diferenciados de cero; aviso de QA no aplicada. | Opción exploratoria, pendiente de decisión de César y de los gates de geometría/licencia que correspondan. |
| QIm mensual | Valor original y etiqueta de índice mensual; explicar equivalente de gauges por área 2,5° × 2,5° aunque el archivo lo almacene en grilla 0,1°; no llamarlo probabilidad ni exactitud por píxel. Si se usan bandas de color descriptivas del ATBD, identificarlas como consejo contextual no validado para la política de producto. | Propuesta informativa, no aprobada; no descarta celdas. |
| `randomError` | Unidad `mm/hr`, nombre como estimación de error aleatorio y nota de que no es error total ni sesgo. | Propuesta informativa, no aprobada. |
| `gaugeRelativeWeighting` | Unidad `percent`, descripción de peso relativo de gauge frente a multisatélite; sin usarlo como porcentaje de exactitud. | Propuesta informativa, no aprobada. |
| Estado QA | Mensaje explícito `unassessed` / “QA no aplicada”; si faltan variables en un futuro archivo, indicarlo como ausentes en vez de cero. | Requisito preventivo recomendado para cualquier demo que exponga estos datos. |

Estas opciones son material para que César decida qué necesita el MVP. No cambian FUL-107, no aprueban el producto inicial y no afirman que los campos auxiliares deban estar visibles en la interfaz.

### Experimentos necesarios antes de una regla QA

1. **Alinear escala espacial de QIm:** verificar, con documentación y arreglos originales, cómo se representa en la grilla de 0,1° un índice cuyo soporte de interpretación es 2,5° × 2,5°; cuantificar valores repetidos/vecindad y evitar contar píxeles vecinos como observaciones independientes. Informar método y límite de cualquier remapeo.
2. **Precisar el uso previsto:** separar decisión de mapa contextual, serie regional y afirmación de precisión local; cada uso requiere evidencia y política de faltantes distintas.
3. **Evaluar sensibilidad, no escoger un corte a partir de la distribución:** si César solicita estudiar las bandas del ATBD, comparar explícitamente valores/cobertura espacial y temporal retenidos y descartados, por mes y ámbito, usando solo periodos realmente inspeccionados hasta que se autoricen más muestras. No escoger la banda que “se vea mejor”.
4. **Buscar validación independiente cuando se pretenda hablar de exactitud:** cotejar precipitación con estaciones o una referencia independiente pertinente, verificar que la referencia no sea la misma información gauge que contribuyó a la combinación IMERG, documentar periodo, resolución, sesgos y representatividad regional.
5. **Probar continuidad antes de extrapolar:** revisar versiones, meses y estaciones adicionales si se propone una serie temporal; las 13 muestras actuales no constituyen continuidad 2005–2024 ni validan umbrales históricos.

Hasta que esas pruebas y las decisiones correspondientes se completen, conservar QA como `unassessed`, publicar faltantes/cobertura según el ámbito ensayado y no aplicar filtro, corte, ponderación ni clase como criterio de aceptación.

### Preguntas abiertas para FUL-107 / César

- ¿La primera demo debe mostrar solo la tasa de precipitación o también diagnósticos QA? Si muestra estos, ¿QIm se presentará como contexto con su soporte de 2,5°?
- ¿La pregunta del MVP necesita una visualización raster de muestra o una serie regional? No son intercambiables y las muestras actuales solo respaldan la primera como opción exploratoria.
- ¿Se requiere decidir una política QA para la demo? Si sí, ¿qué afirmación pretende sostener y qué validación independiente respaldaría esa regla?
- ¿Qué ámbito se mostrará y cómo se indicarán la geometría, el método de selección y la cobertura? Los conteos por centro de la Fase 2 no son cobertura de superficie.
- ¿Se usarán bandas de color del ATBD solo como anotación informativa o se necesitan experimentos de sensibilidad antes de mostrarlas? Cualquier uso como filtro queda fuera de esta fase y requiere decisión explícita.

### Checklist de Fase 3

- [x] Contraste con fuente primaria NASA V07 y fecha de consulta registrados.
- [x] QIm diferenciado de QIh; soporte interpretativo 2,5° × 2,5° explicado frente a almacenamiento 0,1°.
- [x] Significados y límites de `randomError` y `gaugeRelativeWeighting` separados de exactitud y sesgo.
- [x] Evidencia empírica asociada a valores por muestra/ámbito sin convertir rangos observados en umbrales.
- [x] Opciones de demo y experimentos futuros documentados como propuestas para César, no decisiones aprobadas.
- [x] Se conserva `unassessed`; no se aplican filtros, clases ni conversiones de tasa a acumulado.
- [x] Revisión de consistencia, pruebas de repo y diff de FUL-112 completados; rama basada en el `origin/dev` vigente y cambio listo para PR hacia `dev`.

### Fuentes primarias

- [NASA GPM, IMERG V07 Algorithm Theoretical Basis Document, v7.2, 13-08-2026 (PDF)](https://gpm.nasa.gov/sites/default/files/2026-08/IMERG_V07_ATBD_final_260813.pdf): §3.11 (error estimates), §3.12.2 (QIm), §3.13/tabla 5 (salidas), apéndice §§9.4–9.5 (QIm y consejo de uso). Consulta: 2026-11-15.
- [DOI de IMERG Final Monthly, colección 07](https://doi.org/10.5067/GPM/IMERG/3B-MONTH/07); los archivos inspeccionados reportan además versión de archivo `V07B` en el manifiesto de Fase 1.

# FUL-112 · QA empírica IMERG mensual — Fase 1

**Estado:** inventario estructural y de procedencia completado. La evaluación de píxeles QA permanece **`unassessed`**; no se aplica filtro ni umbral.
**Alcance de esta fase:** identificar las muestras locales y comprobar su identidad declarada, estructura HDF5, atributos y campos disponibles. No calcular estadísticas de QA ni presentar resultados como calidad validada.

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

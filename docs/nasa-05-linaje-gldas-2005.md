# FUL-113 · Inventario y procedencia de muestras GLDAS

**Fase 1 — inventario, estructura y procedencia**
**Consulta y verificación local:** 15 de noviembre de 2026
**Estado QA:** `unassessed`

## Alcance de esta fase

Este inventario identifica y describe dos gránulos mensuales de GLDAS Noah 2.1: enero de 2005 y enero de 2021. Se verificaron directamente el nombre, tamaño, SHA-256, estructura NetCDF4/HDF5, coordenadas, variable `SoilMoi0_10cm_inst`, atributos y metadatos temporales. El manifiesto versionado y el script reproducen las verificaciones de identidad y estructura.

Esta fase **no determina** qué versión de la máscara de aguas continentales se aplicó a enero de 2005, no interpreta el efecto de esa máscara sobre los valores y no aprueba los datos para una serie regional. Las diferencias observadas entre archivos son evidencia de metadatos, no prueba del linaje de procesamiento.

## Procedencia de los archivos

| Periodo | Identidad CMR | GranuleUR / archivo | Bytes observados | SHA-256 observado | Evidencia |
|---|---|---|---:|---|---|
| 2005-01 | `G1413723174-GES_DISC` | `GLDAS_NOAH025_M.2.1:GLDAS_NOAH025_M.A200501.021.nc4` | 25.075.859 | `5fe42fc81dae292f3be27c3b3460249609a3aa1699532edba25a88fa53b08593` | `TEC`: archivo local y [UMM JSON de NASA CMR](https://cmr.earthdata.nasa.gov/search/concepts/G1413723174-GES_DISC.umm_json) |
| 2021-01 | `G2040571257-GES_DISC` | `GLDAS_NOAH025_M.2.1:GLDAS_NOAH025_M.A202101.021.nc4` | 24.908.188 | `4580e2cea40b8f50a13f6438298b09c086037cf0565796ad9763259b5aec4d64` | `TEC`: archivo local y [UMM JSON de NASA CMR](https://cmr.earthdata.nasa.gov/search/concepts/G2040571257-GES_DISC.umm_json) |

Ambos pertenecen a la colección `GLDAS_NOAH025_M`, versión `2.1`, proveedor NASA GES DISC; DOI de colección/producto: [10.5067/SXAVCZFAQLNO](https://doi.org/10.5067/SXAVCZFAQLNO). CMR declara fechas de producción `2020-10-19T17:41:05Z` para el granule de 2005 y `2021-04-26T19:06:40Z` para 2021. Una fecha de producción del catálogo, por sí sola, **no demuestra** qué edición de máscara o posprocesamiento se aplicó a las celdas del archivo.

Los archivos brutos permanecen fuera de Git. En este equipo se encontraron bajo `data/raw/nasa/ful104/` del checkout previo. El script acepta sus rutas explícitamente, por lo que no depende de esa ubicación ni versiona rutas absolutas locales.

## Método reproducible

El manifiesto pequeño [`research/manifests/gldas_ful113_samples.json`](../research/manifests/gldas_ful113_samples.json) registra periodos, nombres, IDs CMR, tamaños y SHA-256 esperados, además de los valores temporales observados. [`research/inspeccionar_linaje_gldas.py`](../research/inspeccionar_linaje_gldas.py) comprueba el hash y tamaño, y falla si no coinciden nombre, periodo, dimensiones, tipo, unidades o `cell_methods`. Registra atributos del archivo, dimensiones y atributos de coordenadas, conservando la representación de los metadatos y sin decodificar ni transformar los valores científicos.

Desde la raíz del repositorio, con las dependencias del proyecto instaladas:

```powershell
uv run python research/inspeccionar_linaje_gldas.py `
  --gldas-2005 "RUTA\GLDAS_NOAH025_M.A200501.021.nc4" `
  --gldas-2021 "RUTA\GLDAS_NOAH025_M.A202101.021.nc4"
```

El resultado se escribe por defecto en `data/cache/ful113/gldas_sample_inventory.json`, una ruta ignorada por Git. Se pueden configurar también `--manifest` y `--output`. No requiere autenticación Earthdata para inspeccionar archivos ya descargados. Las pruebas offline usan un NetCDF4/HDF5 sintético pequeño y verifican identidad, metadatos, dimensiones, SHA-256 y rechazo de periodo/hash incompatibles; no sustituyen la comprobación de los gránulos NASA.

## Atributos y estructura observados

| Campo | Enero 2005 | Enero 2021 | Estado / interpretación limitada |
|---|---|---|---|
| Formato y grilla | NetCDF4/HDF5; `lat=600`, `lon=1440` | NetCDF4/HDF5; `lat=600`, `lon=1440` | `TEC`: ambos archivos mantienen forma global compatible con 0,25°; no es una prueba de cobertura válida regional. |
| Variable | `/SoilMoi0_10cm_inst`, `float32`, forma `(time, lat, lon)=(1,600,1440)` | Igual | `TEC`: variable y orden de ejes confirmados. En HDF5 se leen escalas de dimensión `time`, `lat`, `lon`. |
| Significado/atributos | `standard_name=soil_moisture_content`; `long_name=Soil moisture`; `units=kg m-2`; `cell_methods=time: mean` | Mismos valores declarados | `TEC`: atributos del granule. La etiqueta `_inst` en el nombre no convierte el promedio mensual en una observación instantánea. |
| Fill y faltantes declarados | `_FillValue=-9999`; `missing_value=-9999` | `_FillValue=-9999`; `missing_value=-9999` | `TEC`: codificación de los atributos. En esta fase no se cuentan valores ni se evalúa QA. |
| Escala | No se observan `scale_factor` ni `add_offset` en la variable | `scale_factor=1`; `add_offset=0` | `TEC`: diferencia de presencia de metadatos. No se infiere que los archivos recibieran igual o distinto proceso solo por esto. |
| Tiempo | `time=1827`, límites `[1827,1858]`, días desde `2000-01-01 00:00:00`; calendario `standard` | `time=7671`, límites `[7671,7702]`, mismas unidades de referencia | `TEC`: límites son compatibles con enero de cada año. Enero de 2021 incluye además `begin_date=20210101`, `end_date=20210131` y `time_increment=one month`; esos metadatos no aparecen en el eje temporal 2005. |
| `history` | `created on date: 2019-10-31T04:18:41.350` | `created on date: 2021-04-23T11:19:32.357` | `TEC`: cadenas literales del atributo raíz. No identifican inequívocamente un commit, configuración, versión de máscara o resultado por celda. |
| Fuente declarada | `Noah_v3.6 forced with GDAS-AGRMET-GPCPv13rA1` | `Noah_v3.6 forced with GDAS-AGRMET-GPCPv13rA1_202101` | `TEC`: texto del atributo `source`; no detalla el posprocesamiento de agua continental. |
| Atributos globales | `institution=NASA GSFC`, `title=GLDAS2.1 LIS land surface model output monthly mean`, `Conventions=CF-1.6`, proyección cilíndrica equidistante, `DX=DY=0.25` | Los mismos campos declarativos principales | `TEC`: descripción propia del archivo, no auditoría de producción externa. |

No se reescribieron los atributos, no se escaló la variable y no se clasificaron los valores de `SoilMoi0_10cm_inst`. El JSON local retiene atributos observados completos para las muestras; esta tabla destaca solo los campos pertinentes al inventario inicial.

## Relación entre evidencia y conclusión de Fase 1

| Afirmación | Fuente y método | Evidencia | Límite / consecuencia |
|---|---|---|---|
| Los dos archivos son los granules mensuales declarados en CMR para enero 2005 y enero 2021. | `DOC/TEC`: registros UMM JSON de CMR y comprobación local de nombre, periodo interno, tamaño y SHA-256 frente al manifiesto. Consulta: 2026-11-15. | IDs CMR, GranuleUR y hashes de la tabla; verificador reproducible. | Confirma identidad e integridad respecto al manifiesto local. No demuestra la historia de algoritmos de procesamiento ni que los valores sean adecuados para una inferencia. |
| Ambos contienen la variable mensual de humedad de suelo en la capa Noah 0–10 cm declarada como `kg m-2`. | `TEC`: atributos y estructura del dataset en los dos archivos. | `SoilMoi0_10cm_inst`, `float32`, `(1,600,1440)`, `cell_methods=time: mean`, unidades y fechas/bounds registrados. | Los nombres/atributos no explican por sí solos los pasos de re-procesamiento ni autorizan convertirla a humedad volumétrica. |
| Los metadatos de producción y algunos atributos difieren entre muestras. | `TEC`: comparación directa de atributos y CMR. | `history`, `source`, presencia de escala y metadatos temporales varían como se muestra arriba. | No permite confirmar qué versión de máscara de aguas interiores se aplicó a enero de 2005. La investigación de linaje queda para las siguientes fases. |

**Resultado de Fase 1:** identidad, procedencia declarada, hash, estructura y atributos esenciales quedan inventariados. La evaluación QA continúa `unassessed`; no se recomienda filtro, exclusión ni aprobación de uso de enero de 2005.

## Fase 2 · Cronología y evidencia de máscara

**Consulta de fuentes y ejecución local:** 15 de noviembre de 2026. La comparación es descriptiva; no aplica un filtro de datos ni identifica por sí sola la versión histórica de la máscara.

### Cronología comprobada

| Fecha | Evidencia | Qué demuestra | Límite |
|---|---|---|---|
| 2019-10-31 | `history` de `GLDAS_NOAH025_M.A200501.021.nc4`: `created on date: 2019-10-31T04:18:41.350`. | `TEC`: el atributo de la muestra conserva esa cadena. | No identifica revisión ni procesamiento posterior; no fecha necesariamente el contenido que se descargó en 2026. |
| 2020-10-06 | `history` del archivo oficial candidato `GLDASp5_landmask_025d.nc4`: `created on date: Tue Oct 6 17:26:50 2020`. | `TEC`: la máscara enlazada por LDAS registra esa fecha de creación. | La fecha no identifica una revisión de la máscara de cada granule Noah. |
| Octubre de 2020 | NASA informa que se posprocesaron todas las salidas GLDAS-2 mensuales y de 3 horas con MOD44W para enmascarar datos de aguas interiores; el aviso pide volver a descargar los archivos obtenidos antes de noviembre de 2020. | `DOC`: el aviso establece el alcance general y la ventana anunciada. | No enumera el ID CMR `G1413723174-GES_DISC`, su revisión ni el SHA del archivo. [README GLDAS-2 de GES DISC](https://docserver.gesdisc.eosdis.nasa.gov/public/project/hydrology/README_GLDAS2.pdf); [anuncio GES DISC](https://forum.earthdata.nasa.gov/viewtopic.php?p=1407&t=659). |
| 2020-10-19 | CMR actual asocia al granule 2005 `ProviderDates` Insert/Update y `ProductionDateTime` con `2020-10-19T17:41:05Z`; el archivo vigente conserva el SHA de Fase 1. | `TEC`: los metadatos actuales colocan la inserción/actualización y producción del registro en la ventana anunciada. | CMR no registra en esos campos la razón de la actualización ni el algoritmo/máscara incorporados al contenido. |
| 2021-04-23 / 2021-04-26 | `history` del archivo 2021 declara creación el 23-abr-2021; CMR declara Insert/Update y `ProductionDateTime` el 26-abr-2021. | `TEC`: cronología del archivo 2021 y del registro actual. | No prueba que todos los meses compartan una trayectoria idéntica ni identifica la máscara exacta del archivo 2005. |
| 2026-06-10 | CMR devuelve la revisión actual 8 del granule 2005 (`revision-date=2026-06-10T14:44:28.249Z`) y la revisión actual 4 del granule 2021 (`2026-06-10T14:43:30.890Z`). | `TEC`: los registros de catálogo tienen revisiones actuales posteriores. | La fecha de revisión de metadatos no es un checksum de datos ni una fecha de reprocesamiento de píxeles. |

El CMR actual del producto refiere la colección `C1342986036-GES_DISC`, `GLDAS_NOAH025_M` versión `2.1`; sus [`UseConstraints`](https://cmr.earthdata.nasa.gov/search/concepts/C1342986036-GES_DISC.umm_json) enlazan la [guía de uso y cita EOSDIS/NASA](https://earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance). La guía enlazada y la ficha LDAS no proporcionan en el archivo máscara inspeccionado una licencia individual explícita. Por eso el binario descargado se conserva solo en `data/raw/nasa/ful113/` (ignorado por Git), se cita su fuente y no se redistribuye en este trabajo.

La consulta pública de `search/granules.umm_json` entrega el `revision-id` y la fecha actuales. En esta consulta `all_revisions=true` no es un parámetro reconocido para granules, y las rutas directas de revisiones históricas ensayadas (2005: 1–7; 2021: 1–3) devolvieron 404; solo respondieron las revisiones vigentes 8 y 4. La API documenta la recuperación de revisiones de otros conceptos, pero la evidencia que obtuvimos no expone aquí un historial antiguo del granule. Esto limita la reconstrucción; no demuestra que esas revisiones nunca existieran. Véase [CMR Search API](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html).

### Máscara candidata publicada por NASA

La página oficial LDAS enlaza el archivo NetCDF de máscara GLDAS de 0,25° y describe la máscara estándar derivada de MOD44W: estima porcentaje de agua a 0,01° en cada caja GLDAS; las cajas con más del 50 % de agua se codifican como agua (`0`) y las demás como tierra (`1`). Esta regla describe la máscara publicada, no es un umbral QA de `SoilMoi0_10cm_inst` ni demuestra que se aplicara esa misma revisión al granule 2005. [GLDAS Vegetation Class/Mask](https://ldas.gsfc.nasa.gov/gldas/vegetation-class-mask).

El archivo descargado desde el enlace oficial fue identificado como `GLDASp5_landmask_025d.nc4`, 72.395 bytes, SHA-256 `de8244247dd4685c04cb91101968ab2ec6cc635090a982d95f73f68e4d95f791`. El dataset `/GLDAS_mask` es `float32`, forma `(1,600,1440)`, con ejes `time,lat,lon`, fill `-9999` y atributo `units=0 = water; 1 = land`. Sus coordenadas `lat` y `lon` son exactamente iguales, celda a celda, a las de ambas muestras. El atributo `long_name` dice **“GLDAS MOD44W land mask modified for HYMAP”**. Esta mención a HYMAP obliga a tratar el archivo como **máscara candidata de comparación**, no como prueba documental de ser la máscara operativa de GLDAS Noah mensual. La página oficial dice “standard” y provee el enlace; el atributo del propio archivo añade esa limitación de aplicabilidad.

### Prueba reproducible de clases de máscara y valores

[`research/comparar_mascara_gldas_ful113.py`](../research/comparar_mascara_gldas_ful113.py) valida el nombre, tamaño y hash de los archivos contra manifiestos; comprueba el orden de ejes y la igualdad exacta de centros; después contabiliza, sin transformar datos, `_FillValue`, no finitos y finitos no-fill por clase almacenada de máscara. No realiza QA, no aplica la regla de porcentaje de agua y no excluye celdas.

```powershell
uv run python research/comparar_mascara_gldas_ful113.py `
  --gldas-2005 "RUTA\GLDAS_NOAH025_M.A200501.021.nc4" `
  --gldas-2021 "RUTA\GLDAS_NOAH025_M.A202101.021.nc4" `
  --mask "RUTA\GLDASp5_landmask_025d.nc4"
```

El JSON de salida se escribe por defecto en `data/cache/ful113/gldas_mask_comparison.json`, excluido de Git. El manifiesto [`research/manifests/gldas_ful113_mask.json`](../research/manifests/gldas_ful113_mask.json) registra URL de origen, hash, tamaño, estructura y atributos de advertencia; no contiene el binario. Las rutas son configurables y los tests usan arreglos pequeños sintéticos para verificar alineación, fill/no finitos/valores finitos y rechazo de grillas incompatibles.

**Resultado global (`TEC`, gránulos auténticos):** la máscara tiene 621.247 celdas `water_0` y 242.753 `land_1`. En **cada una** de las dos muestras, las 621.247 celdas `water_0` coinciden con `_FillValue=-9999`, sin valores finitos ni no finitos; las 242.753 celdas `land_1` son finitas y distintas de fill. No aparecen clases de máscara adicionales ni fill/no finitos en la máscara.

**Ventana interior diagnóstica (`TEC`, selección de centros inclusiva):** en `137°–140°E, 30°–26°S` se seleccionan 192 centros de celda: 3 con máscara `water_0` y 189 con `land_1`. En ambas muestras, los tres centros de agua son fill y los 189 centros de tierra son finitos no-fill. La ventana incluye la ubicación interior publicada de Lake Eyre North y South (cerca de 137°20′E, 29°02′S y 29°20′S); **no** se atribuyen por eso esos tres centros de máscara a Lake Eyre. Es una ventana de diagnóstico, no el polígono de Murray–Darling ni una máscara hidrográfica independiente. [Gobierno de South Australia, listado de ubicaciones](https://data.environment.sa.gov.au/Content/Publications/Cooper-Creek-BioSurvey.pdf).

La coincidencia completa respalda que el **contenido actualmente servido** es espacialmente coherente con esta máscara candidata. También es consistente con el aviso de NASA y con la fecha CMR de 2020. Sin embargo, la fuente candidata declara una modificación para HYMAP, CMR no expone en esta consulta el historial previo del granule, y no se comparó el archivo con un binario anterior al aviso. Por tanto, esta prueba **no demuestra que el granule Noah 2005 recibiera exactamente esa revisión de MOD44W en el reprocesamiento de octubre de 2020**. Un patrón idéntico puede corroborar compatibilidad del estado actual sin identificar por sí mismo la ruta histórica.

| Hipótesis contrastada | Evidencia observada | Resultado acotado |
|---|---|---|
| El archivo actual 2005 conserva valores finitos en las celdas de agua de la máscara candidata. | Cero de 621.247 celdas `water_0` finitas; en la ventana interior, cero de 3. | No se observa ese patrón en las muestras actuales; no falsifica por sí solo una versión anterior o una máscara distinta. |
| El archivo actual 2005 es consistente con celdas de agua rellenadas y tierra válida bajo la máscara candidata. | Coincidencia exacta global y en la ventana interior; enero 2021 también coincide. | Hipótesis compatible con datos; no identifica con certeza el algoritmo/revisión histórica específica. |
| La máscara descargada es demostrablemente el artefacto exacto usado para reprocesar Noah 2005. | El archivo oficial se fecha en 6-oct-2020 y coincide espacialmente; su `long_name` indica “modified for HYMAP”. | No confirmado: falta una asociación explícita granule→revisión de máscara o un checksum/registro de ejecución de NASA. |

**Estado al cerrar Fase 2:** evidencia primaria general y comparación técnica reproducible disponibles; QA `unassessed`; sin filtro ni decisión de producto. La fase siguiente debe consolidar el dictamen `CONFIRMADO / DESCARTADO / INDETERMINADO`, separar la consecuencia para demo y serie, y preparar —sin enviar— la consulta técnica que pide el criterio de FUL-113 si la incertidumbre persiste.

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

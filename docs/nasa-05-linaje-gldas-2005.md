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

**Estado al cerrar Fase 2:** evidencia primaria general y comparación técnica reproducible disponibles; QA `unassessed`; sin filtro ni decisión de producto. La Fase 3 consolida el dictamen y sus consecuencias, y deja una consulta técnica en borrador si persiste la incertidumbre.

## Fase 3 · Dictamen y transferencia a César

### Dictamen

**INDETERMINADO** para la afirmación específica: *“el granule GLDAS Noah 2.1 de enero de 2005 actualmente identificado como `G1413723174-GES_DISC` recibió exactamente la revisión de máscara MOD44W usada en el posprocesamiento anunciado por NASA en octubre de 2020”*.

La evidencia no permite confirmar ni descartar esa ruta histórica. El aviso NASA cubre en términos generales datos GLDAS-2 mensuales y de 3 horas y recomienda descargar de nuevo los archivos previos a noviembre de 2020. El registro CMR actual del granule 2005 tiene `ProviderDates` Insert/Update y `ProductionDateTime` el 19-oct-2020. Además, la muestra actual coincide celda a celda con la máscara candidata publicada: todas las celdas `water_0` están en fill y todas las `land_1` tienen valores finitos. Estas piezas hacen que el archivo actual sea **consistente con** el posprocesamiento descrito.

La relación causal no queda demostrada: CMR no ofrece en la consulta realizada el historial anterior de revisiones ni un checksum anterior/posterior; los atributos `history` de los gránulos no identifican la máscara; y el propio archivo candidato se describe como una máscara MOD44W “modified for HYMAP”, sin un registro que lo vincule como artefacto exacto del proceso Noah mensual. La coincidencia de fill no identifica el código, la versión de máscara ni cuándo se aplicó.

**Grado de certeza expresado por alcance:** `TEC` alto para la identidad de las muestras y la coincidencia numérica con el archivo candidato; `DOC` para el aviso de alcance general de NASA; `PEND` para asociar una revisión concreta de máscara con el granule 2005. Esto no es una probabilidad estadística. La QA científica del producto permanece `unassessed`.

### Consecuencia separada para demo y serie

| Contexto | Consecuencia científica de este dictamen | Límite de decisión |
|---|---|---|
| Demo exploratoria | Si FUL-107 decide mostrar la muestra 2005, acompañarla con producto/versión, periodo, `SoilMoi0_10cm_inst`, unidad `kg m-2`, procedencia/hash, QA `unassessed` y una nota de que el contenido actual coincide con una máscara candidata pero la revisión histórica exacta no está confirmada. | Esto no aprueba que GLDAS sea el producto de demo ni valida valores para una inferencia. La decisión de uso corresponde a César/equipo. |
| Serie histórica validada | La muestra 2005 no puede presentarse como prueba de homogeneidad temporal 2005–2024 a partir de esta evidencia. Antes de tratarla como parte de una serie validada se requiere resolver el linaje o que el equipo determine y documente una política explícita de inclusión, exclusión o sensibilidad. | Este dictamen no elige producto, no fija una política de faltantes y no decide si se excluye el mes. No rellenar ni sustituir silenciosamente valores. |

### Consulta técnica preparada, no enviada

FUL-113 pide redactar una consulta si persiste la incertidumbre. Este borrador es para pedir metadatos técnicos; **no solicita a NASA que apruebe una decisión del proyecto y no se ha enviado**.

**Subject:** GLDAS Noah 2.1 January 2005 granule — MOD44W post-processing lineage

> Hello GES DISC / GLDAS team,
>
> Could you help us verify the processing lineage of the currently distributed monthly 0.25-degree Noah 2.1 granule `GLDAS_NOAH025_M.A200501.021.nc4` (CMR concept ID `G1413723174-GES_DISC`, granule UR `GLDAS_NOAH025_M.2.1:GLDAS_NOAH025_M.A200501.021.nc4`)? The local file we inspected is 25,075,859 bytes with SHA-256 `5fe42fc81dae292f3be27c3b3460249609a3aa1699532edba25a88fa53b08593`.
>
> The GLDAS-2 documentation states that monthly and 3-hourly outputs were post-processed with MOD44W in October 2020 and recommends re-downloading files obtained before November 2020. CMR currently reports Insert/Update and ProductionDateTime as 2020-10-19 for this granule. We also found that the current file’s fill pattern matches the publicly linked 0.25-degree GLDAS mask, whose variable metadata says “modified for HYMAP.”
>
> Could you confirm whether this exact Noah monthly granule was replaced or post-processed in that October 2020 update? If available, could you identify the mask artifact/revision or processing release used, and whether any pre/post-update granule checksum or processing record is retained? Does `GLDASp5_landmask_025d.nc4` correspond to the mask used for this monthly Noah granule, despite the “modified for HYMAP” description?
>
> We are seeking provenance information only; we are not asking NASA to approve a project product or scientific decision. Thank you.

### Próximos pasos propuestos para César

| Paso opcional | Esfuerzo estimado | Riesgo/dependencia | Qué resolvería |
|---|---:|---|---|
| Revisar este dictamen y decidir si la formulación refleja el nivel de certeza aceptable para FUL-107. | Bajo | Revisión del responsable; no requiere nuevos datos. | Acordar cómo representar la incertidumbre en las decisiones del equipo. |
| Si considera útil resolver la trazabilidad, autorizar que el borrador se envíe a GES DISC. | Bajo para enviar; plazo de respuesta externo desconocido. | La respuesta puede no identificar revisión histórica o puede no existir un checksum previo. | Posible confirmación técnica específica del granule; no sustituye aprobación del equipo. |
| Si NASA no conserva el historial, evaluar una política explícita para la serie (p. ej., mantener pendiente, excluir con trazabilidad o presentar sensibilidad). | Medio | Requiere decisión metodológica del equipo y no se resuelve con el análisis actual. | Evitar atribuir homogeneidad sin evidencia. No se elige una alternativa en FUL-113. |

## Auditoría de criterios de aceptación FUL-113

| Criterio | Resultado documentado | Estado |
|---|---|---|
| Asociar atributos, IDs y hashes 2005/2021 al archivo correcto. | Manifiesto y verificación local repetible en Fase 1. | Cumplido para las dos muestras. |
| Distinguir aviso NASA 2020 de evidencia del granule específico. | Aviso general separado de `ProviderDates`, `ProductionDateTime`, CMR revision y atributos locales. | Cumplido con limitaciones explícitas. |
| Documentar prueba reproducible o razón concreta de imposibilidad. | Comparación reproducible con máscara pública candidata, pruebas sintéticas y advertencia de compatibilidad HYMAP. | Cumplido; prueba no identifica revisión histórica. |
| Dictamen con fuente, límite y grado de certeza. | `INDETERMINADO`, evidencia `DOC/TEC/PEND` y fundamento explícito. | Cumplido para la afirmación definida arriba. |
| Consecuencia separada para demo y serie. | Tabla de demo exploratoria y serie validada, sin aprobar selección. | Cumplido como evaluación de consecuencias. |
| Consulta externa redactada, no enviada; NASA no es aprobador. | Borrador técnico incluido; ninguna consulta enviada. | Cumplido. |
| No aprobar umbral, producto ni procesamiento histórico. | QA sigue `unassessed`; no se tomó ninguna de esas decisiones. | Cumplido. |
| Validaciones/PR documentadas y revisión de César requerida. | Validaciones locales abajo; PR a `dev` preparada para solicitar revisión de César. | Lista para revisión; aprobación de César pendiente. |

## Validaciones y publicación

- `uv run --locked --python 3.12 ruff check backend research`: correcto (`All checks passed!`).
- `uv run --locked --python 3.12 pytest --basetemp E:\\tmp\\pytest-ful113 backend/tests research/tests`: correcto (89 passed, 1 warning). El directorio temporal ASCII en el mismo volumen evita una incompatibilidad de `netCDF4` con rutas Windows que contienen caracteres acentuados y con temporales en otro volumen; la primera repetición en `data/cache` falló al crear fixtures, antes de evaluar sus aserciones.
- `git diff --check`: correcto. Revisión del diff limitada al informe de FUL-113; los gránulos, la máscara y los JSON bajo `data/raw`/`data/cache` permanecen locales e ignorados.
- La PR se publicará desde la rama propia de Lucas hacia `dev`, con resumen de evidencia, limitaciones y validaciones, y solicitud de revisión de César mediante `gh` CLI. **No se hará merge ni se cerrará FUL-113 sin revisión humana.**

# DS-05 — Auditoría de disponibilidad y viabilidad multivariable

**Tarjeta:** FUL-122. **Corte local:** 2026-11-15. **Dictamen:** *no-go* para inferencia multivariable o entrenamiento; *go* para ampliar datos y preparar un análisis descriptivo posterior. No se modifica ni aprueba Gate R, Gate T ni política QA.

## Alcance y procedencia

Se inspeccionaron los archivos `data/raw/nasa` del checkout del usuario y la caché local preservada en `anomaly-zero-ful-105-eda/data/cache/ful-105/be02-handoff/data_root`. Los archivos no están versionados. Sus sidecars de NASA GES DISC/CMR se cotejaron con nombre, período, tamaño y SHA-256; los bytes observados coinciden con los checksums declarados. La caché se leyó en sitio y no se movió ni alteró.

| Producto | Variable / unidad nativa | Colección y versión | Archivos locales y período real | Tamaño y SHA-256 de enero 2005 |
|---|---|---|---|---|
| GPM IMERG Final mensual | `Grid/precipitation`, mm/hr (tasa media mensual) | `GPM_3IMERGM`, V07B; DOI `10.5067/GPM/IMERG/3B-MONTH/07`; GES DISC | 12 HDF5, 2005-01…2005-12 | 18,028,945 B; `bac3b9bc5ee8cc3eb1e5fe844778d54fd86e2b722813055b37f3872e6e4c73d5` |
| MERRA-2 mensual | `T2M`, K | `M2TMNXSLV`, 5.12.4; DOI `10.5067/AP1B0BA5PD2K`; GES DISC | 1 NetCDF4, 2005-01 | 54,419,597 B; `103d95aa3ffe9b8d7e98caea5f6a764831bad3b70155370d3a84c2dfd95616c6` |
| GLDAS Noah mensual | `SoilMoi0_10cm_inst`, kg m-2 | `GLDAS_NOAH025_M`, 2.1; DOI `10.5067/SXAVCZFAQLNO`; GES DISC | 1 NetCDF4, 2005-01 | 25,075,859 B; `5fe42fc81dae292f3be27c3b3460249609a3aa1699532edba25a88fa53b08593` |

Disponibilidad observada por mes (no por catálogo):

| Período 2005 | IMERG | MERRA-2 | GLDAS | Coincidencia triple |
|---|---:|---:|---:|---:|
| Enero | ✓ | ✓ | ✓ | ✓ |
| Febrero–diciembre, cada mes | ✓ | — | — | — |
| Total de meses presentes | 12 | 1 | 1 | 1 |

Las documentaciones históricas describen muestras de enero de 2021, pero no se localizaron esos archivos en los dos directorios auditados. No se cuentan como datos disponibles aquí. Tampoco se infieren 240 meses a partir de cobertura de catálogo. Los HDF5 IMERG mensuales son grillas nativas `lon,lat` de 0.1°; MERRA-2 tiene 576×361 centros globales (~0.625°×0.5°); GLDAS tiene 1440×600 centros (~0.25°). Todos son globales, pero una grilla más fina no crea observaciones independientes ni justifica promedios de cuenca.

## Comparabilidad y calidad

El tiempo representativo de MERRA-2 enero está en `2005-01-01T00:30`; GLDAS en `2005-01-01T00:00` con bounds mensuales. IMERG declara un mes calendario con calendario Julian y límites propios. Son resúmenes mensuales con convenciones temporales distintas; el emparejamiento mensual por etiqueta sirve para una tabla descriptiva, no elimina diferencias en definición temporal ni dependencia entre productos.

La muestra IMERG heredada de FUL-116 es un único centro de grilla (145.75°E, 37.6499977°S), 12 meses, `point_sample`, QA `unassessed`. En enero se verificaron los NetCDF auténticos y las variables esperadas; sus grillas tienen soportes distintos. No se ha establecido una regla aprobada de co-localización ni una máscara regional aprobada. Los análisis FUL-104/111 documentan cobertura válida IMERG de 100.0046% del área MDBA bajo el método examinado; no se usa ni corrige esa agregación. GLDAS tiene fill en 7 celdas que intersectan la geometría en las muestras históricas y su linaje de máscara para 2005 sigue indeterminado. IMERG inventaría campos de calidad pero no tiene umbrales QA aprobados. No filtrar o rellenar faltantes sin decisión metodológica.

Por tanto, no se calculan correlaciones, pruebas, p-valores, rezagos, diferencias estacionales ni anomalías entre productos. Un solo mes triple no permite separar co-variación de ciclo estacional, estimar dependencia temporal, ni dividir cronológicamente entrenamiento y evaluación. Los campos GLDAS pueden compartir información física/metodológica con forzantes meteorológicos; una correlación posterior tampoco probaría causalidad.

## Decisión de análisis y modelos

**No-go con la muestra presente.** Doce observaciones puntuales de IMERG no constituyen una serie multivariable emparejada con GLDAS y MERRA-2. No se entrenan regresión regularizada ni modelo con rezagos y no se comparan métricas ficticias. La baseline estacional tampoco se puede evaluar fuera de muestra con una sola observación de cada mes y sin años replicados.

Al completar los datos, pre-registrar como experimento: usar una unidad espacial común cuya geometría, bounds y máscara hayan pasado revisión; conservar el valor nativo y registrar la transformación; alinear períodos por bounds y documentar cualquier conversión de unidad; reportar cobertura y faltantes por producto antes del inner join; mantener QA como atributo hasta aprobar reglas; comparar baseline climatológica mensual, Ridge con predictores contemporáneos y Ridge con rezagos predefinidos. Evaluar solo con particiones cronológicas de años completos, ajuste de escalado dentro de cada fold, métricas contra baseline, y análisis de sensibilidad a autocorrelación, faltantes, soporte y estación. Definir previamente objetivo/horizonte y no interpretar coeficientes como causalidad.

## Plan de adquisición, antes de descargar

Estimación usando bytes observados (sin compromiso de descarga): 12 meses de cada producto serían aproximadamente 0.21 GiB de IMERG (tamaño mensual observado ~18–20 MB), 0.61 GiB de MERRA-2 (enero observado ~54.4 MB/mes) y 0.28 GiB de GLDAS (~25.1 MB/mes); total orientativo ~1.10 GiB por año y ~22 GiB por 2005–2024, sin duplicados, sidecars ni almacenamiento procesado. MERRA-2 se estimó linealmente a partir de un solo granule, por lo que su variación mensual puede cambiar el total. Los tres archivos mensuales completos ocupan ~87.5 MiB; una ventana espacial pequeña puede ahorrar transferencia si NASA GES DISC permite subsetting para las colecciones y formato solicitados, sujeto a verificación del servicio. Acceso requiere Earthdata Login para descarga autenticada; la lectura local no requiere credenciales. Antes de solicitar 240 meses, probar una sola solicitud de subsetting para un mes/ventana tras confirmar soporte de servicio, estimar cuotas/latencia y revisar que la respuesta preserve bounds, metadatos y variables. No se descargó nada en FUL-122.

## Reproducción y siguientes pasos

Regenerar la matriz y verificar hashes/tamaños de todos los granules con:

```powershell
uv run python -m research.ful122_inventory `
  --input-dir "C:\ruta\al\checkout\data" `
  --input-dir "C:\ruta\al\cache\data_root" `
  --output "C:\ruta\al\resultado\ful122_inventory.json"
```

Revisar identidad/variable/dimensiones con los manifiestos FUL-116, FUL-113 y FUL-105, y volver a abrir los NetCDF con `uv run python` + xarray (`decode_cf`/escala automáticas deben registrarse). Recalcular SHA-256 antes de reutilizar. Para pasar el go/no-go se necesitan archivos auténticos, hash y manifiesto verificables, al menos varios años completos con los tres productos, política espacial revisada sin aprobarla unilateralmente, QA documentada y una partición cronológica independiente. La primera adquisición recomendada es enero–diciembre de 2005 de MERRA-2 y GLDAS (11 archivos faltantes de cada uno), luego comprobar integridad, solapamiento, tamaño y soporte antes de extender la ventana.

Esta nota es un diagnóstico de disponibilidad y diseño experimental; no produce resultados de EDA espacial o de tendencia ni cambia servicios de FastAPI/frontend.

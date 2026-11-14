# FUL-105 — EDA preliminar GLDAS (enero de 2005)

## Objetivo y alcance

Preparar una inspección reproducible de una muestra mensual GLDAS Noah 2.1, con controles de faltantes y una primera visualización global/regional. Esta rama parte de `feature/ful-103-earthdata-probe`, SHA base `cf3cd22897b2173ec389af4a4f6754793dbef2da`. El conector y sus 13 pruebas existentes se reutilizan sin cambios.

## Descubrimiento CMR observado

Consulta pública efectuada el 2026-11-14 con `uv run python -m backend.app.data_sources.earthdata_probe discover --month 2005-01 --limit 1`. No requiere autenticación. Los tres productos devolvieron estado `found`:

| Producto / versión | Variable | Colección | Gránulo | Período observado | Tamaño CMR (MB) |
| --- | --- | --- | --- | --- | ---: |
| MERRA-2 `M2TMNXSLV` / 5.12.4 | `T2M` | `C1276812859-GES_DISC` | `G1278025954-GES_DISC`; `MERRA2_300.tavgM_2d_slv_Nx.200501.nc4` | 2005-01-01–2005-01-31 | 51.8986 |
| GPM IMERG `GPM_3IMERGM` / 07 | `precipitation` | `C2723754851-GES_DISC` | `G2823464479-GES_DISC`; `3B-MO.MS.MRG.3IMERG.20050101-S000000-E235959.01.V07B.HDF5` | 2005-01-01–2005-01-31 | 17.1937 |
| GLDAS `GLDAS_NOAH025_M` / 2.1 | `SoilMoi0_10cm_inst` | `C1342986036-GES_DISC` | `G1413723174-GES_DISC`; `GLDAS_NOAH025_M.A200501.021.nc4` | 2005-01-01–2005-01-31 | 23.9142 |

El bbox utilizado (`138,-38,153,-24`) filtra archivos candidatos en CMR; no recorta los píxeles del archivo.

## Muestra y estado de acceso

En este checkout no existe el NetCDF objetivo ni su manifiesto bajo `data/raw/nasa/gldas/`. La documentación heredada de FUL-103 registra un SHA y una descarga previa, pero eso no verifica que el objeto exista localmente ahora. Se hizo un único intento con el comando interactivo autorizado y límite de 64 MiB. Earthaccess llegó a `Enter your Earthdata Login username:`; se interrumpió en ese prompt sin introducir credenciales ni persistir autenticación.

Por tanto, **no se descargó ni se leyó una muestra en esta ejecución**. No hay hallazgos de píxeles NASA ni gráficos observados que reportar. El notebook informa el bloqueo al ejecutarse sin muestra y queda preparado para leer datos auténticos una vez instalados localmente con el flujo oficial. Cuando se obtenga el archivo, conservar junto a él el manifiesto generado por FUL-103; el notebook verifica su SHA-256 antes del análisis.

## QA implementado y visualizaciones preparadas

`research/gldas_qa.py` abre con xarray y `decode_cf=False`, `mask_and_scale=False`, `decode_times=False`. Selecciona latitud/longitud inclusivas dentro del rectángulo, admite coordenadas ascendentes o descendentes, excluye NaN y los atributos `_FillValue`/`missing_value` de los resúmenes y conserva el cero como valor válido. Reporta cobertura, forma, coordenadas, atributos y estadísticos de valores almacenados. No aplica escala, offset, conversiones, QA flags ni agregación.

El notebook prepara mapa global, mapa del bbox y distribución de valores válidos. Se mostrarán solo cuando estén presentes el archivo auténtico y su manifiesto. El bbox rectangular no es una máscara hidrográfica ni un promedio ponderado de cuenca. No se encontró `Anomaly_Zero_Evidencia.zip` dentro del repositorio para validar la geometría; queda pendiente confirmar con Lucas el polígono fuente, CRS, rasterización, celdas de borde y ponderación por área.

La prueba de `research/tests/test_gldas_qa.py` usa un NetCDF sintético temporal para validar conteo de sentinelas, cobertura, selección espacial y archivo ausente. Es una prueba de código y **no constituye resultado de NASA**.

## Reproducibilidad

Desde la raíz del repositorio:

```powershell
uv sync --group research --group dev
uv run python -m backend.app.data_sources.earthdata_probe discover --month 2005-01 --limit 1
uv run pytest backend/tests/test_earthdata_probe.py research/tests/test_gldas_qa.py
uv run ruff check backend research
uv run jupyter nbconvert --to notebook --execute research/notebooks/ful_105_eda_gldas_200501.ipynb --output ful_105_eda_gldas_200501.executed.ipynb --output-dir research/notebooks
```

Para habilitar celdas de EDA, ejecutar una única descarga acotada desde un terminal local: `uv run python -m backend.app.data_sources.earthdata_probe download-gldas --month 2005-01 --max-mib 64 --auth-strategy interactive`. Earthaccess pedirá autenticación por terminal; no registrar secretos ni persistirlos como parte de este análisis.

## Decisiones y siguientes entregas

- **Alaín / FUL-106:** integrar la base FUL-103 según el flujo del equipo y facilitar el descubrimiento/manifiestos de MERRA-2 e IMERG; cualquier extracción futura debe seguir limitada y con QA de procedencia. Esta rama no implementa descargas de esos productos.
- **Lucas / FUL-104:** validar el polígono de Murray–Darling, CRS, cobertura y algoritmo de ponderación antes de producir un agregado regional comparable.
- **FUL-105:** tras conseguir la muestra real, ejecutar el notebook y revisar atributos/unidades/faltantes con evidencia del archivo; luego acordar comparabilidad temporal y espacial de las tres variables. No inferir tendencias desde este único mes.

La integración debe partir del historial de FUL-103 ya incluido aquí. Una vez que la base oficial integre FUL-103, trasladar los commits propios de esta rama mediante cherry-pick o rebase acordado tras revisar divergencia; no duplicar cambios del conector. No se crea PR en esta tarea.

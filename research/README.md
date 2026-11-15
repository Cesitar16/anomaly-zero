# Laboratorio de investigación

Este espacio contiene un piloto de EDA puntual con NASA POWER y funciones reusables, independiente de los adaptadores Earthdata que desarrolla Alaín. El notebook no pretende caracterizar toda la cuenca Murray–Darling ni sustituir MERRA-2, GPM IMERG o GLDAS.

## Reproducir

Desde la raíz del repositorio:

    uv sync --group research --group dev
    uv run jupyter lab research/notebooks

Abre y ejecuta todas las celdas de 01_eda_piloto_power.ipynb. La primera ejecución consulta NASA POWER y conserva el JSON original y sus metadatos en data/raw/. Si ya existe el archivo local, se reutiliza. Para descargar otra vez, borra únicamente el JSON local o invoca fetch_power_response(..., force=True) desde un entorno de confianza.

Ejecuta las pruebas offline con uv run pytest research/tests. No requieren conectividad NASA.

## Auditoría espacial de FUL-104

Instala las dependencias de investigación y geoespaciales desde la raíz del checkout:

    uv sync --group research --group dev

La auditoría exige estas seis muestras originales (enero de 2005 y enero de 2021 para cada producto):

| Producto | 2005-01 | 2021-01 |
|---|---|---|
| MERRA-2 `M2TMNXSLV` | `MERRA2_300.tavgM_2d_slv_Nx.200501.nc4` | `MERRA2_400.tavgM_2d_slv_Nx.202101.nc4` |
| GPM IMERG mensual final `GPM_3IMERGM` | `3B-MO.MS.MRG.3IMERG.20050101-S000000-E235959.01.V07B.HDF5` | `3B-MO.MS.MRG.3IMERG.20210101-S000000-E235959.01.V07B.HDF5` |
| GLDAS Noah `GLDAS_NOAH025_M` | `GLDAS_NOAH025_M.A200501.021.nc4` | `GLDAS_NOAH025_M.A202101.021.nc4` |

Descárgalas autenticándote localmente con Earthdata (por ejemplo, `uv run python -c "import earthaccess; earthaccess.login(strategy='interactive', persist=True)"`) y consultando las colecciones/versiones correspondientes en CMR; referencia identificadores y atributos en [validacion_cientifica_ful104.md](../docs/validacion_cientifica_ful104.md). Conserva los nombres exactos y coloca los archivos juntos. No compartas `.netrc`, tokens ni URLs firmadas. En otro checkout, también descarga la geometría MDBA completa `mdba_boundary_4326.geojson` desde el servicio descrito en [region_murray_darling.md](../docs/region_murray_darling.md) y el shapefile estatal ABS 2026 en un ZIP (debe incluir `.shp` y `.dbf`).

La configuración predeterminada espera las muestras en `data/raw/nasa/ful104/` y las geometrías en `data/cache/ful-102/`. Todos los paths se pueden cambiar:

```powershell
uv run python research/auditar_espacial_ful104.py `
  --data-dir "E:\NASA\ful104" `
  --mdba-geojson "E:\geometria\mdba_boundary_4326.geojson" `
  --nsw-zip "E:\geometria\nsw_boundary.zip" `
  --output "E:\resultados\spatial_audit.json"
```

El comando anterior usa continuación de línea de PowerShell. También se puede ejecutar como una sola línea. La auditoría termina con error si falta una de las seis muestras o si no pudo procesarla; el JSON de salida conserva los errores por muestra para diagnóstico.

El informe JSON se escribe en `data/cache/ful104/spatial_audit.json`, ignorado por Git. Incluye los checksums, cobertura válida de las celdas intersectadas, promedios de diagnóstico y rangos QA no-fill. Los valores fill QA se leen del atributo `_FillValue` de cada dataset y se comparan en la precisión almacenada. No filtra QA, no calcula una serie de 240 meses y no aprueba una máscara operacional. La reproyección de celdas no densifica sus bordes y los bounds MERRA-2/GLDAS se infieren de la resolución nominal cuando no están en el archivo.

## Datos y alcance

La consulta piloto usa la API mensual puntual de NASA POWER para T2M, comunidad AG, y Wagga Wagga (NSW), entre 2005 y 2024. La API agrupa por años y puede incluir el mes 13 como resumen anual; el parser conserva la respuesta cruda completa y excluye ese registro solo de la serie mensual. El archivo original y su sidecar de procedencia están ignorados por Git bajo data/raw/.

Las funciones de calidad, estadísticas descriptivas y anomalías están en series_quality.py; el cliente y parser están en power_data.py. Estas funciones no conectan con el backend y no constituyen todavía el motor estadístico productivo.

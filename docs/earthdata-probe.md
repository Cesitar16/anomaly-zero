# Sondeo acotado de Earthdata (FUL-103)

> Implementación de descubrimiento e inspección preliminar. No ingiere lotes, recorta grillas, calcula series regionales ni ejecuta análisis estadístico.

## Productos y parámetros

La herramienta consulta un único mes, limitado a 2005-01–2024-12, y una caja Murray–Darling de referencia `138,-38,153,-24`. El bbox selecciona granulos que intersectan la caja; no recorta sus píxeles. Se consultan como máximo tres granulos por producto por defecto y el límite configurable no puede superar diez.

| Producto candidato | Versión candidata | Campo | Concept ID observado en E01 | DOI de referencia de E01 |
| --- | --- | --- | --- |
| MERRA-2 `M2TMNXSLV` | 5.12.4 | `T2M` | `C1276812859-GES_DISC` | `10.5067/AP1B0BA5PD2K` |
| IMERG Final `GPM_3IMERGM` | 07; nombre V07B | `precipitation` | `C2723754851-GES_DISC` | `10.5067/GPM/IMERG/3B-MONTH/07` |
| GLDAS `GLDAS_NOAH025_M` | 2.1 | `SoilMoi0_10cm_inst` | `C1342986036-GES_DISC` | `10.5067/SXAVCZFAQLNO` |

E01 guardaba respuestas CMR con 2005-01 presente para los tres, y el inventario 2005-2024 completo. IMERG Final V07 observado termina en 2025-09. El catálogo solo demuestra disponibilidad declarada; no prueba autenticación, descarga ni validez de píxeles.

La ejecución pública del CLI desde PowerShell (2026-11-14) encontró un granulo para enero de 2005 en cada colección:

| Producto | Granule ID | Producer granule ID | Tamaño CMR (MiB) |
| --- | --- | --- | ---: |
| MERRA-2 | `G1278025954-GES_DISC` | `M2TMNXSLV.5.12.4:MERRA2_300.tavgM_2d_slv_Nx.200501.nc4` | 51.8986 |
| IMERG Final | `G2823464479-GES_DISC` | `GPM_3IMERGM.07:3B-MO.MS.MRG.3IMERG.20050101-S000000-E235959.01.V07B.HDF5` | 17.1937 |
| GLDAS | `G1413723174-GES_DISC` | `GLDAS_NOAH025_M.2.1:GLDAS_NOAH025_M.A200501.021.nc4` | 23.9142 |

Estos resultados verifican el descubrimiento CMR en vivo. Earthaccess 0.19.0 requiere además `short_name` (o `entry_title`) junto con el `bounding_box`; la CLI envía ambos `short_name` y versión. El componente después de `:` en `ProducerGranuleId` es el nombre del archivo; el manifiesto conserva el identificador original completo.

El 2026-11-14 se autenticó con Earthdata Login tras aceptar la EULA de NASA GESDISC DATA ARCHIVE y se descargó el granulo GLDAS `G1413723174-GES_DISC`. El archivo `GLDAS_NOAH025_M.A200501.021.nc4` tiene 25,075,859 bytes (23.91420269012451 MiB en CMR) y SHA-256 `5fe42fc81dae292f3be27c3b3460249609a3aa1699532edba25a88fa53b08593`. El manifiesto local registra autenticación, descarga, lectura e inspección exitosas. NetCDF4 abre como una grilla global con dimensiones `time=1`, `lat=600`, `lon=1440`; `SoilMoi0_10cm_inst` tiene forma `[1, 600, 1440]`, `float32`, unidades `kg m-2` y fill value `-9999.0`.

La versión instalada `earthaccess 0.19.0` define `DataGranule.size` como MB, pero su ruta de respaldo convierte `SizeInBytes` dividiendo por `1024²`. El valor observado para esta muestra equivale a MiB: `23.91420269012451 × 1,048,576 = 25,075,859` bytes. La sonda compara bytes enteros con un límite convertido desde MiB y el manifiesto registra `expected_size_mib`, `expected_size_bytes`, `download_limit_mib` y `download_limit_bytes` para evitar unidades ambiguas.

Esto es verificación técnica de una muestra auténtica; el bbox seleccionó el archivo, pero no recortó la grilla. No se interpretaron variables QA, ni se calcularon agregaciones, tendencias o métricas de cuenca. La muestra y su manifiesto permanecen en `data/raw/`, excluidos de Git.

## Uso

Desde la raíz del repositorio:

```powershell
uv run python -m backend.app.data_sources.earthdata_probe discover --month 2005-01 --limit 3
uv run python -m backend.app.data_sources.earthdata_probe inspect data/raw/nasa/gldas/GLDAS_NOAH025_M.A200501.021.nc4
```

La búsqueda pública no requiere login. El comando de descarga acepta solo GLDAS mensual, usa un máximo explícito por defecto de 64 MiB (límite configurable hasta 128 MiB), comprueba el tamaño de CMR antes de autenticar y exige que la respuesta abra como NetCDF4 con `SoilMoi0_10cm_inst`.

Si falla una operación externa, el JSON de error identifica la etapa (catálogo, autenticación o descarga) y el tipo de excepción; omite el mensaje crudo, cuerpos HTTP y URLs del proveedor.

Una vez que la cuenta esté configurada localmente en el terminal:

```powershell
uv run python -m backend.app.data_sources.earthdata_probe download-gldas --month 2005-01 --max-mib 64 --auth-strategy netrc
```

Si aún no hay `_netrc`, se puede iniciar el flujo oficial dentro del terminal con `--auth-strategy interactive --persist-auth`; earthaccess pide los datos localmente. No poner credenciales en argumentos, archivos del repo, logs ni chat. La persistencia guarda `_netrc` en el perfil Windows en texto plano; no usarla en cuentas compartidas/no confiables.

## Descarga e inspección

El CLI descarga exactamente un granulo a un directorio temporal excluido de Git. Rechaza tamaño CMR desconocido o superior al límite, cero bytes, exceso real de tamaño, HTML y archivos que no abren como NetCDF4. Solo tras abrir y comprobar la variable mueve el original a `data/raw/nasa/gldas/` y crea un manifiesto JSON junto a él. El `.gitignore` excluye `data/raw/**`.

El manifiesto registra producto/versión/DOI, colección/granulo, identificadores públicos, mes, tamaño esperado y real, SHA-256, ruta relativa, fecha UTC y estados separados de autenticación, descarga, lectura NetCDF e inspección de variable. `relative_path` se resuelve desde el directorio que contiene el propio manifiesto (por ejemplo, `manifest_path.parent / relative_path`), incluso si `output_dir` es personalizado. Solo se escriben como exitosas las etapas que terminaron. No guarda enlaces de descarga ni URLs firmadas.

El NetCDF y el manifiesto se preparan y validan en el directorio temporal antes de publicar. Cada archivo se publica con una operación atómica que no reemplaza un destino existente (`rename` en Windows y enlace duro en POSIX); si publicar el manifiesto falla después del NetCDF, la sonda intenta retirar solo el archivo nuevo. La publicación de dos archivos no es atómica como conjunto. Los archivos válidos preexistentes se preservan y bloquean la sobrescritura.

La lectura usa `xarray` con `decode_cf=False`, `mask_and_scale=False` y `decode_times=False`. El informe enumera dimensiones, coordenadas y tiempo, atributos originales de la variable (incluidos `units`, `_FillValue`, `missing_value`, `scale_factor` y `add_offset` si existen), candidatos de variables QA y un subconjunto pequeño. Los faltantes del subconjunto se muestran como `null`; el cero se conserva. No se aplican escala/offset, conversiones, máscaras espaciales, agregaciones ni tendencias. Unidad, calendario, flags y atributos ausentes quedan pendientes de validación científica.

## Pruebas offline

`backend/tests/test_earthdata_probe.py` usa un cliente CMR simulado y archivos NetCDF4 sintéticos; no inicia login ni accede a NASA. GitHub Actions sincroniza Python desde `uv.lock` (`--locked`) y frontend desde `package-lock.json` (`npm ci`); no descarga datos NASA.

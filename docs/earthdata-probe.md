# Sondeo acotado de Earthdata (FUL-103)

> Implementaci�n de descubrimiento e inspecci�n preliminar. No ingiere lotes, recorta grillas, calcula series regionales ni ejecuta an�lisis estad�stico.

## Productos y par�metros

La herramienta consulta un �nico mes, limitado a 2005-01-2024-12, y una caja Murray-Darling de referencia `138,-38,153,-24`. El bbox selecciona granulos que intersectan la caja; no recorta sus p�xeles. Se consultan como m�ximo tres granulos por producto por defecto y el l�mite configurable no puede superar diez.

| Producto candidato | Versi�n candidata | Campo | Concept ID observado en E01 | DOI de referencia de E01 |
| --- | --- | --- | --- |
| MERRA-2 `M2TMNXSLV` | 5.12.4 | `T2M` | `C1276812859-GES_DISC` | `10.5067/AP1B0BA5PD2K` |
| IMERG Final `GPM_3IMERGM` | 07; nombre V07B | `precipitation` | `C2723754851-GES_DISC` | `10.5067/GPM/IMERG/3B-MONTH/07` |
| GLDAS `GLDAS_NOAH025_M` | 2.1 | `SoilMoi0_10cm_inst` | `C1342986036-GES_DISC` | `10.5067/SXAVCZFAQLNO` |

E01 guardaba respuestas CMR con 2005-01 presente para los tres, y el inventario 2005-2024 completo. IMERG Final V07 observado termina en 2025-09. El cat�logo solo demuestra disponibilidad declarada; no prueba autenticaci�n, descarga ni validez de p�xeles.

La ejecuci�n p�blica del CLI desde PowerShell (2026-11-14) encontr� un granulo para enero de 2005 en cada colecci�n:

| Producto | Granule ID | Producer granule ID | Tama�o CMR (MiB) |
| --- | --- | --- | ---: |
| MERRA-2 | `G1278025954-GES_DISC` | `M2TMNXSLV.5.12.4:MERRA2_300.tavgM_2d_slv_Nx.200501.nc4` | 51.8986 |
| IMERG Final | `G2823464479-GES_DISC` | `GPM_3IMERGM.07:3B-MO.MS.MRG.3IMERG.20050101-S000000-E235959.01.V07B.HDF5` | 17.1937 |
| GLDAS | `G1413723174-GES_DISC` | `GLDAS_NOAH025_M.2.1:GLDAS_NOAH025_M.A200501.021.nc4` | 23.9142 |

Estos resultados verifican el descubrimiento CMR en vivo. Earthaccess 0.19.0 requiere adem�s `short_name` (o `entry_title`) junto con el `bounding_box`; la CLI env�a ambos `short_name` y versi�n. El componente despu�s de `:` en `ProducerGranuleId` es el nombre del archivo; el manifiesto conserva el identificador original completo.

El 2026-11-14 se autentic� con Earthdata Login tras aceptar la EULA de NASA GESDISC DATA ARCHIVE y se descarg� el granulo GLDAS `G1413723174-GES_DISC`. El archivo `GLDAS_NOAH025_M.A200501.021.nc4` tiene 25,075,859 bytes (23.91420269012451 MiB en CMR) y SHA-256 `5fe42fc81dae292f3be27c3b3460249609a3aa1699532edba25a88fa53b08593`. El manifiesto local registra autenticaci�n, descarga, lectura e inspecci�n exitosas. NetCDF4 abre como una grilla global con dimensiones `time=1`, `lat=600`, `lon=1440`; `SoilMoi0_10cm_inst` tiene forma `[1, 600, 1440]`, `float32`, unidades `kg m-2` y fill value `-9999.0`.

La versi�n instalada `earthaccess 0.19.0` define `DataGranule.size` como MB, pero su ruta de respaldo convierte `SizeInBytes` dividiendo por `1024�`. El valor observado para esta muestra equivale a MiB: `23.91420269012451 x 1,048,576 = 25,075,859` bytes. La sonda compara bytes enteros con un l�mite convertido desde MiB y el manifiesto registra `expected_size_mib`, `expected_size_bytes`, `download_limit_mib` y `download_limit_bytes` para evitar unidades ambiguas.

Esto es verificaci�n t�cnica de una muestra aut�ntica; el bbox seleccion� el archivo, pero no recort� la grilla. No se interpretaron variables QA, ni se calcularon agregaciones, tendencias o m�tricas de cuenca. La muestra y su manifiesto permanecen en `data/raw/`, excluidos de Git.

## Uso

Desde la ra�z del repositorio:

```powershell
uv run python -m backend.app.data_sources.earthdata_probe discover --month 2005-01 --limit 3
uv run python -m backend.app.data_sources.earthdata_probe inspect data/raw/nasa/gldas/GLDAS_NOAH025_M.A200501.021.nc4
```

La b�squeda p�blica no requiere login. El comando de descarga acepta solo GLDAS mensual, usa un m�ximo expl�cito por defecto de 64 MiB (l�mite configurable hasta 128 MiB), comprueba el tama�o de CMR antes de autenticar y exige que la respuesta abra como NetCDF4 con `SoilMoi0_10cm_inst`.

Si falla una operaci�n externa, el JSON de error identifica la etapa (cat�logo, autenticaci�n o descarga) y el tipo de excepci�n; omite el mensaje crudo, cuerpos HTTP y URLs del proveedor.

Una vez que la cuenta est� configurada localmente en el terminal:

```powershell
uv run python -m backend.app.data_sources.earthdata_probe download-gldas --month 2005-01 --max-mib 64 --auth-strategy netrc
```

Si a�n no hay `_netrc`, se puede iniciar el flujo oficial dentro del terminal con `--auth-strategy interactive --persist-auth`; earthaccess pide los datos localmente. No poner credenciales en argumentos, archivos del repo, logs ni chat. La persistencia guarda `_netrc` en el perfil Windows en texto plano; no usarla en cuentas compartidas/no confiables.

## Descarga e inspecci�n

El CLI descarga exactamente un granulo a un directorio temporal excluido de Git. Rechaza tama�o CMR desconocido o superior al l�mite, cero bytes, exceso real de tama�o, HTML y archivos que no abren como NetCDF4. Solo tras abrir y comprobar la variable mueve el original a `data/raw/nasa/gldas/` y crea un manifiesto JSON junto a �l. El `.gitignore` excluye `data/raw/**`.

El manifiesto registra producto/versi�n/DOI, colecci�n/granulo, identificadores p�blicos, mes, tama�o esperado y real, SHA-256, ruta relativa, fecha UTC y estados separados de autenticaci�n, descarga, lectura NetCDF e inspecci�n de variable. `relative_path` se resuelve desde el directorio que contiene el propio manifiesto (por ejemplo, `manifest_path.parent / relative_path`), incluso si `output_dir` es personalizado. Solo se escriben como exitosas las etapas que terminaron. No guarda enlaces de descarga ni URLs firmadas.

El NetCDF y el manifiesto se preparan y validan en el directorio temporal antes de publicar. Cada archivo se publica con una operaci�n at�mica que no reemplaza un destino existente (`rename` en Windows y enlace duro en POSIX); si publicar el manifiesto falla despu�s del NetCDF, la sonda intenta retirar solo el archivo nuevo. La publicaci�n de dos archivos no es at�mica como conjunto. Los archivos v�lidos preexistentes se preservan y bloquean la sobrescritura.

La lectura usa `xarray` con `decode_cf=False`, `mask_and_scale=False` y `decode_times=False`. El informe enumera dimensiones, coordenadas y tiempo, atributos originales de la variable (incluidos `units`, `_FillValue`, `missing_value`, `scale_factor` y `add_offset` si existen), candidatos de variables QA y un subconjunto peque�o. Los faltantes del subconjunto se muestran como `null`; el cero se conserva. No se aplican escala/offset, conversiones, m�scaras espaciales, agregaciones ni tendencias. Unidad, calendario, flags y atributos ausentes quedan pendientes de validaci�n cient�fica.

## Pruebas offline

`backend/tests/test_earthdata_probe.py` usa un cliente CMR simulado y archivos NetCDF4 sint�ticos; no inicia login ni accede a NASA. GitHub Actions sincroniza Python desde `uv.lock` (`--locked`) y frontend desde `package-lock.json` (`npm ci`); no descarga datos NASA.


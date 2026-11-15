# DS-06 — Adquisición NASA mensual 2005

**Tarjeta:** FUL-123 · **Estado de ejecución:** parcial, adquisición bloqueada por Earthdata Login · **Rama:** `feature/ful-123-ds-06-adquisicion-nasa-2005`.

## Preflight reproducible

Se ejecutó `research.ful122_inventory` sobre los tres roots locales usados por FUL-105/116/122: el workspace original, `anomaly-zero-ful-105-eda/data/raw/nasa` y el handoff `data/cache/ful-105/be02-handoff/data_root/data/raw/nasa`. El auditor verificó identidad CMR, manifiesto, SHA-256, tamaño y payload NetCDF/HDF5 antes de considerar una copia elegible.

| Producto | Elegibles 2005 | Copias idénticas excluidas | Meses elegibles | Meses por adquirir |
|---|---:|---:|---|---|
| IMERG Final V07B | 12 | 13 | enero–diciembre | ninguno |
| MERRA-2 `M2TMNXSLV` 5.12.4 | 1 | 1 | enero | febrero–diciembre (11) |
| GLDAS Noah `GLDAS_NOAH025_M` 2.1 | 1 | 1 | enero | febrero–diciembre (11) |

Las 14 observaciones elegibles son únicas por producto/mes y contenido. Una copia idéntica por mes y ubicación se mantiene fuera del conteo. No se detectaron conflictos entre payloads elegibles. La lista de los 22 faltantes se genera dinámicamente desde los meses elegibles; no presupone que tener un archivo en disco lo haga válido.

El archivo portátil [`research/manifests/ful123-acquisition-plan-2005.json`](../research/manifests/ful123-acquisition-plan-2005.json) registra los 22 IDs CMR, collection IDs, GranuleUR, periodo, tamaño estimado, URL pública UMM, ROI usada únicamente para buscar granulos y método aún pendiente de piloto. No incluye rutas locales, datos, cookies, credenciales, cabeceras de autorización ni URLs de descarga potencialmente firmadas. Regenerar con:

```powershell
uv run python -m research.ful123_acquisition `
  --input-dir "C:\ruta\data\raw\nasa" `
  --input-dir "C:\ruta\ful-105\data\raw\nasa" `
  --input-dir "C:\ruta\ful-105\data\cache\ful-105\be02-handoff\data_root\data\raw\nasa" `
  --output research/manifests/ful123-acquisition-plan-2005.json `
  --discover
```

Discovery usa CMR sin autenticación y solo guarda metadata pública. `--discover` no descarga granulos. La estimación total se calcula sumando los tamaños CMR de los elementos `discovered`; no es transferencia observada.

## Fuentes y subsetting

La página oficial de GLDAS confirma resoluciones de 0.25° y 1°, frecuencia mensual y acceso GES DISC con servicios que permiten subset espacial, temporal y por variable ([NASA LDAS GLDAS Dataset](https://ldas.gsfc.nasa.gov/gldas/dataset)). La ficha oficial GES DISC de MERRA-2 `M2TMNXSLV` identifica la colección 5.12.4 ([MERRA-2 dataset](https://disc.gsfc.nasa.gov/datasets/M2TMNXSLV_5.12.4/summary)). Los registros CMR UMM actuales de febrero exponen enlaces de descarga de Earthdata Cloud y `OPENDAP DATA` para ambas colecciones; la metadata se consultó en `cmr.earthdata.nasa.gov`, no se copiaron URLs de transferencia al plan.

GES DISC anunció que el acceso HTTPS y OPeNDAP on-premises se migraría a Earthdata Cloud para septiembre de 2026 y recomienda Earthaccess para los flujos Python. También indica que HOSS reemplaza el servicio L3/L4 de subset y que los servicios cloud requieren seguir sus flujos nuevos ([guía de migración GES DISC](https://github.com/nasa/gesdisc-tutorials/blob/main/user-guidance/GES_DISC_Migration_to_Earthdata_Website_and_Earthdata_Cloud.md)). Por ello no se codifican URLs antiguas `*.gesdisc.eosdis.nasa.gov` ni se infiere soporte de selección de variable/ROI a partir de la mera presencia de un enlace OPeNDAP.

El bbox exploratorio actual es `138–153°E, 38–24°S`, usado por la búsqueda CMR existente del proyecto. Su semántica se restringe a seleccionar el granulo global que contiene la zona; no es el polígono Murray–Darling, no recorta celdas, no resuelve celdas de borde y no valida una máscara. Aún falta comparar los resultados de un subset autenticado de variable/ROI con la estructura global. No se afirma que ningún subset preserve íntegramente los metadatos o sea idéntico al original.

**Decisión de adquisición pendiente del piloto:** full granule es la opción de referencia para conservar estructura, coordenadas, metadatos y trazabilidad byte a byte; subset solo se seleccionará si el piloto real demuestra que la respuesta conserva la identidad de origen, variable, unidad, calendario/bounds, coordenadas/bounds, fill, QA disponible y consulta de transformación. Para un subset, el hash es el del derivado, nunca el SHA del granulo fuente. Sin autenticación no se declara aprobado ninguno de los métodos ni se inicia un lote.

## Presupuesto y acceso

- Volumen libre en el volumen C: **133.11 GiB** durante el preflight (requisito: 4 GiB).
- Estimación CMR de los 11 meses MERRA-2: **596,950,031 bytes**; GLDAS: **276,815,804 bytes**; total 22 granulos: **873,765,835 bytes (~833.1 MiB)**. Los tamaños CMR de febrero son 51.924 MiB (MERRA-2) y 23.560 MiB (GLDAS). La referencia de planificación de Linear (~875 MB) es aproximada y ninguna de estas cifras es transferencia observada.
- Tope de planificación: 1.5 GiB de transferencia. El orquestador comprueba el límite y el espacio antes de cualquier lote; esta validación no reemplaza la medición real.
- Transferencia real en DS-06 hasta el momento: **0 bytes**.
- No se descargaron ni modificaron los archivos NASA ni notebooks previos.

Se intentó únicamente determinar si ya había credenciales/sesión reutilizable: no existen `EARTHDATA_USERNAME`, `EARTHDATA_PASSWORD` ni `EARTHDATA_TOKEN` en el entorno; tampoco se encontró `.netrc`, `_netrc` ni cache local de Earthaccess. El login interactivo se probó sin persistencia y terminó en EOF porque requiere entrada del usuario. No se solicitó ni registró ningún secreto.

**Paso necesario para continuar el piloto:** en esta misma máquina, iniciar sesión en Earthdata Login y autorizar el acceso de la aplicación **NASA GES DISC DATA ARCHIVE**. La herramienta FUL-123 acepta la sesión local vía Earthaccess. Desde el worktree aislado, ejecutar primero el discovery si no se ha generado o actualizado el plan:

```powershell
uv run python -m research.ful123_acquisition `
  --input-dir "C:\ruta\workspace\data\raw\nasa" `
  --input-dir "C:\ruta\ful-105\data\raw\nasa" `
  --input-dir "C:\ruta\ful-105\data\cache\ful-105\be02-handoff\data_root\data\raw\nasa" `
  --output research/manifests/ful123-acquisition-plan-2005.json `
  --discover
```

Después, ejecutar desde la misma carpeta los pilotos de febrero. El flujo reintenta como máximo tres veces solo fallos de transferencia, publica cada granulo y manifiesto de forma atómica mediante los downloaders existentes, valida el resultado con el inventario y registra progreso local en un archivo ignorado por Git. Los granulos completos ya válidos se omiten en una reejecución; los meses restantes se rechazan hasta que ambos pilotos de febrero estén elegibles.

```powershell
uv run python -m research.ful123_acquisition `
  --input-dir "C:\ruta\workspace\data\raw\nasa" `
  --input-dir "C:\ruta\ful-105\data\raw\nasa" `
  --input-dir "C:\ruta\ful-105\data\cache\ful-105\be02-handoff\data_root\data\raw\nasa" `
  --output research/manifests/ful123-acquisition-plan-2005.json `
  --data-dir data/raw/nasa `
  --acquire-pilot `
  --auth-strategy interactive
```

Tras comprobar ambos pilotos y volver a auditar el payload, `--acquire-rest --auth-strategy interactive` adquiere secuencialmente los meses marzo–diciembre aún pendientes. No compartir aquí credenciales, cookies, tokens ni capturas del login. Inspeccionar ambos NetCDF y detener el lote si falla identidad, payload o criterio de recursos.

El comando GLDAS existente debe ejecutarse desde el worktree aislado en la rama FUL-123; el downloader preexistente escribe bajo `data/raw/nasa/gldas`. MERRA usa `data/raw/nasa/merra2`. Esas carpetas están ignoradas por Git. Los tests del proyecto no acceden a red ni a secretos.

## Criterio científico y handoff

Hasta contar con pilotos payload-verified, los conteos se mantienen en 1/12 MERRA-2 y 1/12 GLDAS; el solapamiento triple elegible se mantiene en enero 2005. La metadata de febrero confirma identidad/catalogo y fecha mensual, pero no representa un valor de observación local. QA IMERG sigue `unassessed`, Gate R y Gate T continúan pendientes, y la incertidumbre de linaje de máscara GLDAS continúa vigente.

La coincidencia de periodos no valida co-localización. La próxima etapa debe comparar las grillas nativas MERRA-2 (0.625° × 0.5°) y GLDAS (0.25°), coordenadas, bounds, calendarios, fill/máscaras y soporte de la muestra IMERG (0.1°). Proponer puntos de grilla co-localizados explícitos y sensibilidad a celdas vecinas, tras fijar la geometría versionada de cuenca. DS-06 no calcula agregados regionales, correlaciones, tendencias ni modelos.

## Verificaciones realizadas en el worktree limpio

- `uv sync --group dev --group research`: instaló los grupos necesarios; el primer pytest había mostrado la ausencia de `shapely` en el entorno recién creado.
- `uv run pytest research/tests/test_ful123_acquisition.py -q`: **16 passed** (fixtures sintéticos, sin red).
- `uv run pytest backend/tests research/tests -q`: **194 passed**, una advertencia upstream de deprecación Starlette/httpx.
- `uv run ruff check backend research`: pasó.
- `git diff --check`: pasó.
- CMR: búsqueda verificada para los 22 periodos faltantes en ambos productos; identidad, colección, versión, productor, fechas y tamaños se guardan en el manifiesto.
- Payloads y SHA enero: validados por el inventario existente desde los datos locales. No se pudo reproducir una descarga nueva ni validar los bytes de febrero porque no hay autenticación.
- Tests de FUL-123 cubren faltantes dinámicos, identidad/período/collection inválidos y CMR ambiguo, presupuesto, reintentos acotados, recuperación idempotente a nivel de granulo, gate de pilotos, no sobrescritura y reporte local sin secretos.

Este es un avance parcial y no satisface Done de adquisición. FUL-123 debe permanecer In Progress hasta ejecutar y validar los pilotos, y solo después adquirir los otros meses en lotes pequeños.

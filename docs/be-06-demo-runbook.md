# BE-06 — FastAPI y snapshot IMERG para demo

## Preparación e inicio

Desde la raíz del repositorio, con Python 3.12, uv y Node 22:

```powershell
uv sync --locked --python 3.12 --group dev --group research
npm ci --prefix frontend
```

Los originales y manifiestos NASA deben estar disponibles localmente en `data/raw/nasa/imerg_final/`. Si falta el derivado, regénéralo offline con el productor DS-03 existente; no descarga datos:

```powershell
uv run --locked --python 3.12 python -m research.build_ful116_snapshot --input-dir data/raw/nasa/imerg_final --point research/manifests/ful105_imerg_panel_point.json --output-dir data/processed/ful116
```

El snapshot local validado para esta evidencia está en `.be04-snapshot-reader/data/processed/ful116/imerg_2005_point_snapshot.json`. En otro equipo, usa la ruta local legible equivalente. Configura la variable **en la misma PowerShell antes de iniciar**; el proceso Uvicorn hereda este valor:

```powershell
$env:ANOMALY_ZERO_IMERG_SNAPSHOT = 'C:\ruta\legible\imerg_2005_point_snapshot.json'
uv run --locked --python 3.12 uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

No se debe copiar el snapshot a Git. Sin variable, FastAPI busca `data/processed/ful116/imerg_2005_point_snapshot.json` desde el checkout. La ruta explícita debe ser accesible desde la cuenta que ejecuta Uvicorn.

## Smoke HTTP

En otra PowerShell, contra `http://127.0.0.1:8000`:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/regions
Invoke-RestMethod 'http://127.0.0.1:8000/api/v1/products?region_id=murray-darling-basin'
$series = Invoke-RestMethod 'http://127.0.0.1:8000/api/v1/series?region_id=murray-darling-basin&product_id=P02&start=2005-01&end=2005-12&frequency=monthly'
$body = @{ dataset_id = $series.dataset_id; window = @{ start = '2005-01'; end = '2005-12'; end_inclusive = $true } } | ConvertTo-Json -Depth 4
try { Invoke-WebRequest 'http://127.0.0.1:8000/api/v1/analyses' -Method Post -ContentType 'application/json' -Body $body } catch { $_.Exception.Response.StatusCode }
```

Con el snapshot validado: health, regiones, productos y series devuelven 200; IMERG está `available`, la serie tiene 12 meses auténticos y `synthetic:false`, con unidad `mm/hr`, soporte `point_sample`, doce registros fuente y `provider_flags_applied:false`. Una petición POST válida a `/api/v1/analyses` devuelve 409 `ANALYSIS_METHOD_UNAVAILABLE`; no crea análisis.

Sin snapshot por defecto, una consulta válida a series devuelve 200 `no_data`. Una ruta explícita inaccesible devuelve 503 `SERVICE_UNAVAILABLE`; un snapshot presente pero inválido devuelve 500 `INTERNAL_ERROR` sanitizado. Región/producto desconocido devuelve 404 y parámetros inválidos 422. Estos estados negativos se cubren con la suite automatizada; no se altera el snapshot real para provocarlos.

## Frontend y límites

El frontend debe solicitar rutas relativas `/api/v1`. FE-04 es responsable del proxy Vite o del mismo origen; el checkout actual no configura proxy. Vite usa normalmente `http://localhost:5173` y FastAPI `http://127.0.0.1:8000`; el proxy debe apuntar al segundo. No se habilita CORS wildcard. La QA navegador ↔ API queda pendiente hasta que FE-04 esté disponible.

El endpoint expone solo IMERG puntual para 2005. Conserva `mm/hr` (tasa mensual, no acumulado), `point_sample` y QA sin aprobación del proveedor; finito/no-fill no implica flags QA aplicados. El punto pertenece al extracto de trabajo de veinte centros, lo que no equivale a superficie cubierta. MERRA-2 y GLDAS no están disponibles en esta API. No hay raster, agregaciones regionales, promedios ni inferencia.

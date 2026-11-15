# Catálogos FastAPI v1 (BE-03)

Catálogo offline de `GET /api/v1/regions` y `GET /api/v1/products?region_id=…` conforme a [OpenAPI v0](openapi-contract-v0.yaml) y [contracts-v0](contracts-v0.md). AZ-04/OpenAPI v0.1-draft está integrado en `dev`; la matriz de [`contracts-v0.md`](contracts-v0.md#rutas-implementadas-en-dev) describe también las rutas de BE-04/BE-05. Publicar Murray–Darling como referencia exploratoria no aprueba geometría de máscara, área, agregación regional ni inferencia.

## Estado publicado por la API

El catálogo de productos se basa en los metadatos versionados de [catalog_mvp.json](catalog_mvp.json), [datasets.md](datasets.md) y el contrato. Conserva las versiones de colección (MERRA-2 `5.12.4`, IMERG `07`, GLDAS `2.1`); `V07B` identifica los archivos IMERG de muestra, no la versión de colección. Las unidades y cantidades son `T2M` / temperatura del aire a 2 m / `K`, `precipitation` / tasa media mensual / `mm/hr`, y `SoilMoi0_10cm_inst` / humedad modelada de 0–10 cm / `kg m-2`.

`/regions` publica Murray–Darling Basin (`murray-darling-basin`) como referencia exploratoria autorizada por César, no como geometría o unidad estadística aprobada. `geometry_source` apunta al ítem oficial MDBA documentado; `geometry_version`, `crs` y `area_km2` quedan `null` porque la geometría/versionado y CRS nativo no están validados para el contrato. `region_id` es obligatorio y no vacío; `/products` responde `404 RESOURCE_NOT_FOUND` para cualquier ID que no esté publicado. Sin snapshot accesible, los tres productos están `unavailable`, con `current_dataset_id`, `coverage` y `quality` en `null`. Si `ANOMALY_ZERO_IMERG_SNAPSHOT` o la ruta default resuelve a un snapshot verificado, solo P02 cambia a `available`/`partial`; `product_version` pasa del valor de catálogo `07` a la versión de archivo `V07B`. MERRA-2 y GLDAS siguen `unavailable`. Las rutas de `source` apuntan a los DOI documentados; `granule_ids` se llena desde los registros del snapshot IMERG validado.

Las respuestas usan `contract_version: "0.1-draft"`, `synthetic: false` en producción, `generated_at` UTC y `Cache-Control: no-store`. Los errores usan el envelope `ErrorResponse`: 404 `RESOURCE_NOT_FOUND`, 422 `INVALID_PARAMETER`, 503 `SERVICE_UNAVAILABLE` con `retryable: true` y 500 `INTERNAL_ERROR` sanitizado. Los errores no exponen mensajes internos ni detalles del proveedor. `/health` mantiene su respuesta previa.

Ejemplos de consulta local:

```bash
curl http://127.0.0.1:8000/api/v1/regions
curl 'http://127.0.0.1:8000/api/v1/products?region_id=murray-darling-basin'
```

`/regions` devuelve la referencia Murray–Darling. La consulta de productos devuelve metadatos y disponibilidad condicionada por snapshot; un ID de región no publicado responde 404. El catálogo no contiene valores de series: `GET /api/v1/series` los lee del snapshot IMERG verificado, como documenta [BE-04](be-04-snapshot-reader.md). Cero se conserva como dato y `null` con `missing_reason` como ausencia.

Los tests inyectan una región sintética solo para verificar el camino 200 de `/products`; esa fixture no se sirve en producción. También validan respuestas contra los schemas integrados en OpenAPI, parámetros generados, rutas, errores y unidades.

## Ejecución local

Desde la raíz del repositorio, con las dependencias bloqueadas ya sincronizadas:

```bash
uv run uvicorn backend.app.main:app --reload
uv run pytest backend/tests research/tests
uv run ruff check backend research
```

La documentación interactiva queda en `/docs`; el esquema generado en `/openapi.json`.

Para iniciar FastAPI con snapshot real, comprobar `ANOMALY_ZERO_IMERG_SNAPSHOT`, reproducir smoke HTTP y conocer la coordinación pendiente con FE-04, seguir el [runbook BE-06](be-06-demo-runbook.md). BE-05 implementa `POST /api/v1/analyses` con `409 ANALYSIS_METHOD_UNAVAILABLE` para una petición válida y `GET /api/v1/analyses/{analysis_id}` con `404 RESOURCE_NOT_FOUND`; no hay método, persistencia ni resultados productivos ([detalle](be-05-analyses-v1.md)).

BE-04 sirve únicamente una serie IMERG puntual de 2005: `point_sample`, precipitación en `mm/hr` (tasa mensual, no acumulado) y QA del proveedor no aprobada. Sin snapshot default válido `/series` responde `200 no_data`; una ruta explícita inaccesible produce `503`, y un snapshot inválido `500` sanitizado. Finito/no-fill no equivale a aplicar flags QA; el conteo de centros no mide superficie. Las muestras son extractos de trabajo y no resultados regionales aprobados. No hay raster, máscaras, agregaciones, promedios, tendencias ni inferencia implementados. FE-04 sigue en revisión y sin integración publicada; no se ha verificado consumo desde navegador.

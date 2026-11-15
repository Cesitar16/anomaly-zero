# Catálogos FastAPI v1 (BE-03)

Implementación offline de `GET /api/v1/regions` y `GET /api/v1/products?region_id=…` conforme a [OpenAPI v0](openapi-contract-v0.yaml) y [contracts-v0](contracts-v0.md). Este documento describe el estado del backend; las decisiones de AZ-04 siguen siendo propuestas del equipo.

## Estado publicado por la API

El catálogo de productos se basa en los metadatos versionados de [catalog_mvp.json](catalog_mvp.json), [datasets.md](datasets.md) y el contrato. Conserva las versiones de colección (MERRA-2 `5.12.4`, IMERG `07`, GLDAS `2.1`); `V07B` identifica los archivos IMERG de muestra, no la versión de colección. Las unidades y cantidades son `T2M` / temperatura del aire a 2 m / `K`, `precipitation` / tasa media mensual / `mm/hr`, y `SoilMoi0_10cm_inst` / humedad modelada de 0–10 cm / `kg m-2`.

`/regions` publica Murray–Darling Basin (`murray-darling-basin`) como referencia exploratoria autorizada por César, no como geometría o unidad estadística aprobada. `geometry_source` apunta al ítem oficial MDBA documentado; `geometry_version`, `crs` y `area_km2` quedan `null` porque la geometría/versionado y CRS nativo no están validados para el contrato. `region_id` es obligatorio y no vacío; `/products` responde `404 RESOURCE_NOT_FOUND` para cualquier ID que no esté publicado. Los tres productos siguen `unavailable`, con `current_dataset_id`, `coverage` y `quality` en `null`: no hay snapshot API publicado. Las rutas de `source` apuntan a los DOI documentados; `granule_ids` permanece vacío porque no se publican aquí granules como datasets actuales.

Las respuestas usan `contract_version: "0.1-draft"`, `synthetic: false` en producción, `generated_at` UTC y `Cache-Control: no-store`. Los errores usan el envelope `ErrorResponse`: 404 `RESOURCE_NOT_FOUND`, 422 `INVALID_PARAMETER`, 503 `SERVICE_UNAVAILABLE` con `retryable: true` y 500 `INTERNAL_ERROR` sanitizado. Los errores no exponen mensajes internos ni detalles del proveedor. `/health` mantiene su respuesta previa.

Ejemplos de consulta local:

```bash
curl http://127.0.0.1:8000/api/v1/regions
curl 'http://127.0.0.1:8000/api/v1/products?region_id=murray-darling-basin'
```

`/regions` devuelve la referencia Murray–Darling. La consulta de productos devuelve los tres productos no disponibles; un ID no publicado responde 404. El catálogo no contiene valores de series; el manejo de mediciones en cero corresponde a `/series`, fuera de BE-03.

Los tests inyectan una región sintética solo para verificar el camino 200 de `/products`; esa fixture no se sirve en producción. También validan respuestas contra los schemas integrados en OpenAPI, parámetros generados, rutas, errores y unidades.

## Ejecución local

Desde la raíz del repositorio, con las dependencias bloqueadas ya sincronizadas:

```bash
uv run uvicorn backend.app.main:app --reload
uv run pytest backend/tests research/tests
uv run ruff check backend research
```

La documentación interactiva queda en `/docs`; el esquema generado en `/openapi.json`.

No se implementan `/series`, `/analyses`, procesamiento científico, descarga NASA, geometría, máscara ni agregaciones. Que una muestra tenga valores finitos/no-fill no equivale a aplicar flags QA; el conteo de centros no mide superficie. Las muestras son extractos de trabajo y no son resultados regionales aprobados.

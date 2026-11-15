# BE-04 — lectura puntual desde snapshot DS-03

La rama integra el catálogo exploratorio de BE-03 y monta `GET /api/v1/series`. Lee únicamente un JSON DS-03 ya generado; la petición no abre HDF5, accede a la red ni ejecuta el pipeline. Sin snapshot local, una consulta válida devuelve `200` con `data_state: no_data`, IDs y procedencia nulos, y los períodos solicitados como faltantes. Un snapshot configurado inaccesible devuelve `503`; uno ilegible o inconsistente devuelve `500` con un error sanitizado.

## Contrato HTTP

La operación acepta `region_id`, `product_id`, `start`, `end` (`YYYY-MM`) y `frequency=monthly`. El rango es inclusivo, debe estar ordenado y no puede exceder 240 meses. Región o producto desconocidos devuelven `404`; parámetros, límite o período fuera de la cobertura del snapshot devuelven `422`. Las respuestas usan `Cache-Control: no-store` y el envelope AZ-04.

La región `murray-darling-basin` es una referencia exploratoria autorizada. Cada valor servido es el valor de una celda IMERG en el punto del snapshot (`spatial_aggregation.support_type: point_sample`), no una media de la cuenca. El producto servido identifica IMERG Final collection `07`, archivo `V07B`, precipitación como tasa media mensual en `mm/hr`. Cero se conserva; `null` conserva su `missing_reason`. `provider_flags_applied` sigue `false`; `basic_checks_only` no significa QA del proveedor aprobada.

### Comprobación espacial del punto

El punto usado (`ful105-panel-row-001`, −37.64999771118164°, 145.75°) viene del panel FUL-105, descrito como 20 centros dentro de Murray–Darling. DS-03 registra que esta coordenada es el centro IMERG `(lon 3257, lat 523)` y fue elegida de los centros dentro de la geometría MDBA con SHA-256 `d36fe31424758cc4fb8eef25e21b835bb5c05c793c746e8a1eb7b5a5841f6a53`; el nuevo informe DS-07 / FUL-124 identifica esa misma geometría por hash y reporta los conteos de centros IMERG. Por tanto, la pertenencia puntual está respaldada por la selección espacial documentada. En esta actualización no se recalculó la contención del punto contra el polígono: el GeoJSON completo es una caché local ignorada y no está en el worktree. Esa limitación no cambia `point_sample` ni convierte la referencia exploratoria en una máscara o cobertura de superficie aprobada.

## Lector e identidad

`backend/app/services/snapshot_reader.py` limita a 1 MiB antes de parsear, rechaza claves duplicadas y números no finitos, y valida esquema `1.0.0`, identidad, producto/unidad, origen, hash canónico, doce períodos, cobertura, valores, soporte puntual y QA. Productor y lector comparten `snapshot_sha256`, `canonical_json` y `dataset_id_for_input_fingerprint` en `research/snapshot_format.py`; el hash del snapshot excluye `snapshot_sha256`.

El servidor busca por defecto `data/processed/ful116/imerg_2005_point_snapshot.json`. `ANOMALY_ZERO_IMERG_SNAPSHOT` permite seleccionar otra ruta controlada por el despliegue. Solo un snapshot que el lector valide cambia el producto IMERG de `/products` a `available` y entrega su `current_dataset_id`, cobertura, calidad y granule IDs. Los otros productos siguen `unavailable`.

### Configuración de despliegue

- Con `ANOMALY_ZERO_IMERG_SNAPSHOT` apuntando a un snapshot válido y completo, `/products?region_id=murray-darling-basin` informa IMERG `available`; si el snapshot válido tiene faltantes, informa `partial`. `/series` usa ese mismo `dataset_id`.
- Si la variable no está configurada y el snapshot por defecto no existe, una consulta válida responde `200` con `data_state: no_data`; `/products` mantiene IMERG `unavailable`.
- Si la variable está configurada y el archivo no puede leerse o no existe, `/series` responde `503 SERVICE_UNAVAILABLE` (reintentable). Un JSON legible pero inválido responde `500 INTERNAL_ERROR` sanitizado.

Ejemplo en PowerShell antes de iniciar el servicio:

```powershell
$env:ANOMALY_ZERO_IMERG_SNAPSHOT = 'C:\data\imerg_2005_point_snapshot.json'
```

La ruta es local al proceso del servidor y debe montar un artefacto verificado de forma legible. Esta PR no copia datos NASA al repositorio ni a la imagen del servicio.

La salida real local fue regenerada desde 12 HDF5 y 12 manifiestos laterales con el productor DS-03, sin editar las entradas:

- `synthetic: false`, dataset `imerg-2005-point-66cf65a5bcf2d99309af`.
- 12 períodos válidos; punto `IMERG-v07b-center-lon3257-lat523` (`-37.64999771118164`, `145.75`).
- SHA-256 del snapshot: `7e95f434df5e2bc4b27c0c5d3317e02fc3f6c30506c68823f55637e57071ba51`.
- El snapshot permanece local/ignorado y no se incluye en Git ni en la imagen por esta PR.

Comando de reproducción en un entorno que ya tenga los originales y manifiestos verificados:

```powershell
python -m uv run --locked --python 3.12 python -m research.build_ful116_snapshot --input-dir data/raw/nasa/imerg_final --point research/manifests/ful105_imerg_panel_point.json --output-dir data/processed/ful116
```

## Mapeo DS-03 → `SeriesResponse`

| DS-03 | Respuesta | Transformación | Evidencia |
| --- | --- | --- | --- |
| `dataset_id` | `dataset_id`, `product.current_dataset_id` | Copiar tras validar el hash. | Prueba de respuesta completa y lector. |
| `synthetic` | `synthetic` | Copiar; los tests usan `true`, el artefacto verificado es `false`. | Pruebas sintéticas y snapshot local. |
| `product` | `product` | Resolver `GPM_3IMERGM` contra el catálogo `P02`; conservar collection `07`, archivo `V07B` y `mm/hr`. | Pruebas de respuesta/producto. |
| No existe | `region` | Resolver desde el catálogo integrado; no inferir geometría ni área. | ID publicado y respuesta validada. |
| `requested_coverage` | `requested_coverage` | Usar el rango pedido, inclusivo. | Prueba de rango parcial. |
| `available_coverage` | `available_coverage` | Copiar luego de validar cobertura anual. | Lector y contrato OpenAPI. |
| `coverage` y `series` | `coverage`, `series` | Filtrar por mes; recalcular expected/present/valid y faltantes sin transformar valores. | Cero, null, faltante y rango parcial probados. |
| `quality` | `quality` | Copiar los estados respaldados; nunca afirmar flags aplicados. | Prueba `provider_flags_applied: false`. |
| `spatial_aggregation` | `spatial_aggregation` | Copiar solo `point_sample`; no agregar por región. | Prueba de soporte puntual. |
| `provenance.source_records[].sha256` | `provenance.source_sha256` | Extraer los doce hashes en orden mensual. | Respuesta OpenAPI y hash del snapshot. |
| `retrieved_at` por archivo, `manifest_sha256` por archivo, `processing` | `retrieved_at`, `manifest_sha256`, `snapshot_created_at` | Mantener `null`: el contrato espera marcas singulares y no existe un agregado canónico acordado. No confundir el hash del snapshot con hash de manifiesto. | Prueba del payload frente a OpenAPI. |
| `provenance.transformations` | `transformations` | Mover la lista sin conversión adicional. | Contrato y prueba de respuesta. |
| No existe | `temporal`, `generated_at`, `contract_version` | Derivar frecuencia mensual/etiqueta month-start; generar hora de respuesta y versión API. | Esquema OpenAPI y respuesta HTTP. |

## Comprobaciones y límites

Las pruebas de `backend/tests/test_snapshot_reader.py` mantienen la lectura offline, inmóvil y separada del productor. `backend/tests/test_series_v1.py` valida respuestas y errores contra los esquemas OpenAPI, cobertura, cero/null, producto y soporte. También hace una petición HTTP con el catálogo real Murray–Darling/P02 y cubre la ruta de entorno válida, snapshot por defecto ausente y ruta explícita ausente. Las pruebas usan fixtures sintéticas; no representan una validación científica. El snapshot real local sí fue leído por el mismo lector, pero no es portable ni evidencia de despliegue/recepción por César.

El endpoint sirve solo IMERG puntual 2005. No calcula máscaras, promedios, cobertura de superficie, tendencias, p-values, reproyecciones, tiles ni análisis. GLDAS y MERRA-2 siguen sin datasets accesibles desde este endpoint. La autorización de una región exploratoria no aprueba geometría de máscara, QA del proveedor ni inferencia.

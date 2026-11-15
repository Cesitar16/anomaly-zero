# BE-04 — preparación de lector DS-03

**Alcance de esta entrega:** lector offline del JSON DS-03, validación del artefacto y mapeo al contrato AZ-04. No añade ni monta `GET /api/v1/series`. Es preparación técnica para completar BE-04 cuando estén sus dependencias.

## Lector reutilizable

`backend/app/services/snapshot_reader.py` lee una ruta seleccionada por el servidor. Limita el JSON a 1 MiB antes de cargarlo, rechaza claves duplicadas y números no finitos, y distingue `SnapshotUnavailableError` (ausente o inaccesible) de `SnapshotInvalidError` (tamaño, JSON, versión, identidad, procedencia, cobertura o hash inválidos). Los mensajes no incluyen rutas ni detalles de sistema. El lector no hace escrituras, HDF5, red ni generación de snapshots.

Para la verificación de integridad, productor y lector comparten `snapshot_sha256`, `canonical_json` y `dataset_id_for_input_fingerprint` en `research/snapshot_format.py`. Ese módulo usa solo la biblioteca estándar, por lo que importar el lector no carga el pipeline HDF5/NumPy. Se mantiene la exclusión del único campo `snapshot_sha256` y no se duplica el algoritmo de identidad derivada. El lector se fija al esquema DS-03 `1.0.0`, IMERG Final collection `07`/archivo `V07B`, `precipitation`, `mm/hr`, doce meses de 2005 y soporte `point_sample`. La coherencia entre `series`, valores cero/nulos, `missing_reason`, conteos, hashes fuente, identidad derivada y estado QA también se valida.

Las pruebas generan entradas HDF5 pequeñas desde la fixture sintética ya existente de DS-03, invocan el productor una vez para disponer de su JSON canónico y después prueban el lector aislado. Durante lectura se bloquean llamadas de red, HDF5 y al productor; también se cotejan bytes/hash de insumos y snapshot antes/después. Los JSON de prueba mantienen `synthetic: true`.

## Mapeo DS-03 → `SeriesResponse`

El snapshot DS-03 es un artefacto propio de investigación. No contiene el envelope ni todos los campos del contrato, así que **no se devuelve directamente como `SeriesResponse`**. La suite DS-04 ya valida cada `series[]` contra `SeriesPoint`; esta entrega vuelve a comprobar esa correspondencia para la salida del lector y comprueba que el objeto completo DS-03 no valida como respuesta completa.

| Campo DS-03 | Campo `SeriesResponse` | Transformación necesaria | Prueba/evidencia |
| --- | --- | --- | --- |
| `dataset_id` | `dataset_id` | Copia solo tras validar estructura y hash. | `test_reads_valid_synthetic_snapshot_without_changing_inputs`; hash negativo. |
| `synthetic` | `synthetic` | Copia; una fixture no puede presentarse como producción. | Lectura sintética y mutación del marcador/identidad. |
| `snapshot_sha256` | Sin campo equivalente | Verificación local de integridad; no asignarlo a `provenance.manifest_sha256`. | Hash cambiado es rechazado. |
| `snapshot_schema_version` | Sin campo equivalente | Exigir versión conocida `1.0.0`; el contrato tiene versión separada. | Versión incompatible es rechazada. |
| `data_state` | `data_state` | Copia después de comprobar coherencia con valores faltantes. | Validación de cobertura/estado. |
| `product` | `product` | Resolver contra el catálogo BE-03 por `short_name`; el `product_id` DS-03 (`GPM_3IMERGM`) no es el ID opaco de API. Preservar colección `07` y archivo `V07B` sin confundirlos. | Identidad, variable y unidad del lector; resolución de catálogo queda pendiente de BE-03. |
| No existe | `region` | Obtener descriptor e ID solo del catálogo BE-03 tras la decisión de publicación. El punto de DS-03 no crea ni aprueba una región. | Pendiente de BE-03 y decisión de César en PR #24. |
| `requested_coverage` | `requested_coverage` | Copia para el snapshot completo; una futura consulta parcial tendrá que filtrar meses y recalcular respuesta. | Cobertura fija 2005-01…12 comprobada; filtro HTTP pendiente. |
| `available_coverage` | `available_coverage` | Copia tras cotejar período esperado. | Cobertura y períodos comprobados. |
| `coverage` | `coverage` | Copia tras recalcular conteos desde `series`; `spatial_coverage` sigue `null`. | Coherencia de conteos y faltantes. |
| `quality` | `quality` | Copia; conservar `basic_checks_only`, `provider_flags_applied: false`, QA no aplicada y máscara `null`. | Validación de estados QA del lector; DS-04 cubre semántica. |
| `spatial_aggregation` | `spatial_aggregation` | Copia solo como `point_sample`; no convertir en media ni agregar por geometría. | El lector rechaza soporte distinto; fixtures DS-04 prueban punto. |
| `series[].date/value/quality` | `series[]` (`SeriesPoint`) | Copia sin conversión; cero permanece cero y `null` conserva `missing_reason`. | Validación OpenAPI `SeriesPoint`, cero y null con razón. |
| `provenance.source_records[].sha256` | `provenance.source_sha256` | Extraer los doce hashes fuente en orden mensual. | El lector valida formato/orden; mapeo documentado. |
| `source_records[].manifest_sha256`, `retrieved_at`; `processing` | `provenance.manifest_sha256`, `retrieved_at`, `snapshot_created_at` | El destino espera un hash y timestamps singulares, pero DS-03 conserva hashes/timestamps mensuales y no tiene `snapshot_created_at`. Definir manifest agregado/semántica antes de serializar; desconocidos quedan `null`, sin inventar agregación. | Pendiente del adaptador HTTP. |
| `provenance.transformations` | `transformations` | Mover la lista al nivel superior; se conserva vacía para este flujo sin conversiones. | Fixture DS-03 y contraste del contrato. |
| No existe | `temporal` | Derivar `frequency: monthly`, `date_label: month_start`; `calendar` queda `null` salvo que se acuerde exponerlo. | Fechas mensuales y DS-04. |
| No existe | `generated_at` | Generar al responder HTTP; no usar una fecha fija ni inferirla de timestamps de NASA. | Pendiente de endpoint. |
| No existe | `contract_version` | Añadir `0.1-draft` desde la versión integrada, no desde el snapshot. | Contrato integrado; fixture de respuesta OpenAPI. |

Los cinco ejemplos sintéticos del anexo BE-04 en Linear se parsearon y validaron contra `SeriesResponse`/`ErrorResponse` y las reglas semánticas de DS-04. Dos code blocks tenían `\[`/`\]` literales que impedían parsearlos como JSON; se corrigieron solo esos escapes en FUL-115 y se revalidaron los cinco. Los ejemplos del contrato integrado también se validan con `test_all_openapi_response_examples_validate_and_are_explicitly_synthetic` y `test_markdown_json_fixtures_validate_against_matching_openapi_schema`. El artefacto DS-03 solo se valida como `SeriesPoint` y su falta de campos de respuesta completa queda probada explícitamente.

## Pendientes independientes para integrar HTTP

1. **Dependencia técnica BE-03:** PR #24 sigue abierta hacia `dev`. Esta rama se basa en `origin/dev` y no incorpora código de BE-03. El endpoint futuro necesita el montaje y las respuestas de catálogo integrados.
2. **Región/ID:** AZ-03 conserva Murray–Darling como candidata, no hay ID real acordado. César debe decidir en BE-03/PR #24 si se publica como referencia para exploración puntual. Campos inciertos deben seguir nulos. Gate R/T pendiente no prohíbe automáticamente una muestra exploratoria ni la autoriza por sí mismo.
3. **Snapshot real:** DS-03 documenta como salida local ignorada `data/processed/ful116/imerg_2005_point_snapshot.json`. Esa ruta no está en Git. El archivo no existe en los worktrees conocidos BE-04, BE-03, FUL-106, AZ-04 ni en el checkout principal/clone BE-02; por tanto, no se afirma haber leído ni verificado aquí una salida real. La prueba actual usa exclusivamente la fixture sintética reproducible.
4. **Aprobaciones científicas:** soporte puntual y `mm/hr` se conservan; QA sigue `unassessed`, sin máscara ni agregado regional. César revisa el significado, unidad y QA antes de publicación según el uso previsto. No se atribuyen aprobaciones nuevas.

La integración futura debe revalidar endpoint, envelope completo, estado de catálogo, `dataset_id`, filtro del rango, `generated_at` y errores. Estos tests del lector **no** son aceptación de `GET /api/v1/series`.

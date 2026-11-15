# BE-05 — Rutas de análisis sin procesador habilitado

La API valida las solicitudes y la identidad/cobertura del dataset publicado, pero hoy no tiene un método estadístico ni almacenamiento de análisis aprobado. Por eso `POST /api/v1/analyses` no crea trabajos ni IDs: para un dataset verificado y una ventana admisible responde `409 ANALYSIS_METHOD_UNAVAILABLE`. Un dataset desconocido responde `404 RESOURCE_NOT_FOUND`; una fuente configurada que no puede leerse responde `503 SERVICE_UNAVAILABLE`.

## POST `/api/v1/analyses`

El body es `CreateAnalysisRequest`: `dataset_id` opaco devuelto por `/api/v1/series` y ventana mensual inclusiva. Se rechazan propiedades adicionales en el objeto de solicitud, tal como exige su schema; `window` reutiliza `InclusiveMonthRange` sin endurecerlo fuera del OpenAPI integrado. El API no convierte `dataset_id` en ruta ni acepta método, región o producto del cliente. Se valida el cuerpo, el orden de fechas y el máximo de 240 meses antes de comprobar el método. Para el snapshot DS-03 existente, una ventana fuera de enero–diciembre de 2005 responde `422 PERIOD_OUT_OF_COVERAGE`; una ventana superior a 240 meses responde `422 LIMIT_EXCEEDED`.

| Solicitud/situación | Respuesta | Prueba |
| --- | --- | --- |
| Body ausente, campo extra, mes inválido, rango invertido o `end_inclusive:false` | 422 `INVALID_PARAMETER` | `test_create_analysis_rejects_invalid_body_before_resolving_snapshot` |
| Dataset no publicado o snapshot por defecto ausente | 404 `RESOURCE_NOT_FOUND` | `test_create_analysis_unknown_dataset_and_no_default_snapshot_return_404` |
| Ventana mayor a 240 meses / fuera de cobertura | 422 `LIMIT_EXCEEDED` / `PERIOD_OUT_OF_COVERAGE` | `test_create_analysis_reports_limit_coverage_and_unavailable_source` |
| Snapshot configurado que no puede leerse | 503 `SERVICE_UNAVAILABLE`, reintentable | `test_create_analysis_reports_limit_coverage_and_unavailable_source` |
| Snapshot JSON inválido | 500 `INTERNAL_ERROR` sanitizado | `test_create_analysis_sanitizes_invalid_snapshot_content` |
| Dataset verificado, ventana cubierta y método no habilitado | 409 `ANALYSIS_METHOD_UNAVAILABLE`, sin recurso ni ID creado | `test_create_analysis_validates_existing_dataset_then_returns_contractual_409` |
| OpenAPI del runtime, schemas integrados y rutas existentes | Sin 201/202 habilitados; health, regiones, productos y series siguen respondiendo | `test_analysis_routes_match_contract_and_do_not_advertise_disabled_success`; `test_health_catalog_and_series_routes_remain_mounted` |

El ejemplo sintético 409 `methodUnavailable` y `UnavailableAnalysis` canónicos están en `docs/openapi-contract-v0.yaml`; las pruebas validan ese schema y el envelope runtime. El error productivo contiene `analysis_id`, método y todas las métricas como `null`, con `synthetic:false`, `generated_at` UTC, `request_id` aleatorio y `retryable:false`; no expone rutas, stack traces ni secretos. La fixture pendiente 202 del contrato conserva `synthetic:true` y todas las métricas `null`, mientras el endpoint no anuncia 201/202. Las pruebas verifican que `0` también sigue siendo un número válido y distinto de `null`.

## GET `/api/v1/analyses/{analysis_id}`

No hay registro de análisis ni persistencia aprobados. Todo ID no vacío responde 404 `RESOURCE_NOT_FOUND`. El parámetro OpenAPI tiene `minLength: 1`; sin segmento de ID, `GET /api/v1/analyses` no tiene operación definida y responde 405 porque la colección solo acepta POST.

El contrato permite consultar un análisis mientras su registro se retenga, pero no define plazo ni mecanismo de retención. Esta implementación no crea registros; una futura política de expiración/retención queda pendiente junto con el almacén aprobado.

El OpenAPI integrado mantiene las formas contractuales 201 `complete` y 202 `pending` para una futura implementación con procesador y recurso real, pero esta API no las anuncia como respuestas de estas rutas ni puede emitirlas. Los ejemplos sintéticos de esas formas permanecen exclusivamente en la validación de conformidad del contrato; no representan ejecuciones ni activan un endpoint. La suite DS-04 valida que los ejemplos OpenAPI, incluidos null y cero, se ajustan a sus schemas.

## Límites y dependencias pendientes

- Se reusa el catálogo BE-03 y el lector/hash canónico de snapshot DS-03 que usa BE-04; la lectura es local, de solo lectura y no descarga NASA.
- Los productos fuera del snapshot compatible siguen sin poder analizarse mediante este lector. No se evalúan reglas de suficiencia ni se emite `INSUFFICIENT_DATA` sin un método cuya precondición se haya ejecutado.
- No se calculan tendencias, anomalías, pendientes, p-values, intervalos, significancia, conversiones ni agregaciones. La serie DS-03 sigue siendo `point_sample`, IMERG en `mm/hr`, QA del proveedor no aplicada y `not_assessed`.
- Habilitar `201/202` exige una tarjeta posterior con método, ejecución, almacenamiento/retención y criterios de aceptación revisados por César; esta entrega no selecciona método ni altera decisiones científicas.
- El grafo Graphify no está presente en el checkout; se usaron búsquedas dirigidas y se contrastaron rutas, servicios, modelos y tests con el código integrado.

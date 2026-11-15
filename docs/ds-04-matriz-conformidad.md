# DS-04 — Matriz de conformidad científica

**Estado:** pruebas offline y matriz implementadas; contrato OpenAPI usado sin alterarlo. Las decisiones científicas AZ-03/Gates D/R/T/M siguen siendo provisionales o pendientes donde el registro de decisiones así lo indica.

## Matriz de reglas

| Campo/regla contractual | Fuente AZ-03 / AZ-04 | Prueba | Requisito abierto o límite |
|---|---|---|---|
| OpenAPI 3.1, references locales y examples de respuestas | `docs/openapi-contract-v0.yaml`; contrato integrado FUL-108 | `test_all_openapi_response_examples_validate_and_are_explicitly_synthetic` | Las validaciones son locales; schemas no fijan todas las unidades o relaciones cruzadas. |
| Fixtures Markdown y schemas de `SeriesResponse`, `AnalysisResponse`, `ErrorResponse` | `docs/contracts-v0.md`, FUL-108 | `test_markdown_json_fixtures_validate_against_matching_openapi_schema` | Los ejemplos `synthetic:true` sirven para forma, no como resultado real. |
| Snapshot FUL-116 `date/value/quality` compatible con `SeriesPoint` | FUL-116, FUL-108 `SeriesPoint` | `test_ful116_snapshot_points_conform_to_series_point_schema` | Requiere proveedor/product/region descriptor del catálogo para completar `SeriesResponse`. |
| Identidad de producto/unidad: MERRA-2 T2M K; IMERG precipitation mm/hr; GLDAS SoilMoi0_10cm_inst kg m-2 | `docs/decisions.md`, `docs/alcance-cientifico-provisional.md`, contrato AZ-04 | `test_scientific_semantics_rejects_false_or_unsupported_claims` | Transformaciones deben conservar unidad de entrada/salida, parámetros y versión del código. |
| `0` valor numérico; `null` faltante requiere razón; mensual ordenado en primer día | FUL-110 §5; FUL-108 | `test_scientific_semantics_accept_zero_null_and_fill_reason`; negativos parametrizados | Fill/no-finito se traduce explícitamente al producir el snapshot; no imputación. |
| Fuente/flags QA presentes no equivalen a flags aplicadas | `docs/nasa-04-qa-imerg-muestras.md`; FUL-110 §5 | negativos de `provider_qa_applied`/`provider_flags_applied` sin control aplicado | QA IMERG queda `unassessed`, sin umbrales. |
| `point_sample` no equivale a regional; `approved` regional exige referencia documental registrada | FUL-110 §7; `docs/alcance-cientifico-provisional.md` Gate R | rechaza referencia faltante y texto arbitrario; fixtures positivos usan point samples | Gate R no está aprobado; allowlist de referencias vacía hasta decisión documentada. |
| Área válida requiere ambos denominadores; cobertura mayor que cuenca bloquea aprobación regional | FUL-111; FUL-110 §7; OpenAPI `SpatialCoverage` | negativo `A_valid/A_basin > 1` cuando se afirma regional aggregate | El OpenAPI restringe la fracción a ≤1, por lo que no representa el valor diagnóstico 1,000046 de FUL-111; preservar el hallazgo en docs/diagnóstico, no truncar ni normalizar. Cambio del contrato requiere coordinación con Alaín/César. |
| Nada de significancia/pendiente inventado antes de Gate T y motor | `docs/decisions.md` AZD-03; `docs/ful-105-plan-inferencia.md` | `test_gate_t_does_not_allow_production_complete_or_pending_metrics` | Fixtures `synthetic:true` describen solo shape; no acreditan método/procesador. |
| Marcas sintéticas explícitas | FUL-108; FUL-116/117 | Todas las respuestas OpenAPI/Markdown y snapshot fixture comprueban `synthetic:true` | Datos reales solo se identifican cuando manifest, hash, header e identidad concuerdan. |
| Nada aprobado por mera existencia de muestras | Gate D/R/T/M; `docs/decisions.md` | prueba de aprobación regional y QA demostrado; `test_ful116_snapshot_points_conform_to_series_point_schema` | El equipo conserva autoridad para aprobar gates; no existe aprobación por este código. |

## Ejecución

```powershell
uv sync --group dev --group research
uv run pytest research/tests/test_ful116_snapshot.py research/tests/test_ful117_contract.py -q
uv run ruff check research/build_ful116_snapshot.py research/audit_imerg_bounds_precision.py research/ful117_contract.py research/tests/test_ful116_snapshot.py research/tests/test_ful117_contract.py
```

Los tests de contrato usan PyYAML y `jsonschema`, instalados como dependencias dev declaradas; los tests de snapshot usan fixtures sintéticos HDF5 pequeños y nunca consultan NASA o requieren credenciales. Los fixtures se identifican con `synthetic_fixture:true` en sus manifests y producen `synthetic:true` para que no puedan confundirse con observaciones. Los tests se limitan a documentación, conversión de muestra y reglas de coherencia; no testean ni implementan endpoints FastAPI.

## Resolución de discrepancias

- No se cambió unilateralmente `docs/openapi-contract-v0.yaml` ni `docs/contracts-v0.md`.
- El contrato permite `spatial_coverage` y define la razón de área máxima 1.0. El dato FUL-111 `A_valid/A_basin=1.000046` no es serializable bajo ese schema sin perder el hallazgo. Debe permanecer en el reporte diagnóstico con QA `unassessed`; si Alaín necesita exponerlo, proponer un estado/campo de diagnóstico coordinado que no autorice `regional_aggregate`.
- El snapshot local tiene 12 períodos reales, pero su soporte es un solo punto. Cobertura temporal de 12/12 no expresa cobertura de área.
- Las puertas Gate D (demo), R (serie regional), T (tendencias) y M (mapas) no se marcan superadas por esta suite. Los cambios de geometría, regla QA, unidad, método o gates requieren decisión humana documentada.

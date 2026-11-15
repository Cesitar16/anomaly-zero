# AZ-06 / FUL-132 — Informe de validación E2E

**Resultado: BLOQUEADO para aceptación E2E completa.** Docker, API, snapshot auténtico y CSV se validaron correctamente. El recorrido funcional navegador → explorador React → API no se puede aceptar todavía: FE-04 sigue en la PR #36 abierta y no forma parte de `dev`.

## Identidad y entorno

- Repositorio: `Cesitar16/anomaly-zero`.
- Rama de prueba: `test/ful-132-az-06-e2e-validation`.
- SHA de `origin/dev` probado: `2022cf435ee4f67002360f1d7bf47974cf387cde` (incluye Docker Compose #37 y export CSV #38).
- Docker Engine 29.9.2; Docker Compose 5.6.1; imágenes Linux.
- Python de host 3.12.13, uv 0.11.8; Node 24.15.0, npm 11.6.2.
- Compose de prueba aislado: proyecto `az-ful132`, puertos locales 18080/18000. El directorio procesado se enlazó desde una ruta local configurada solo en el proceso de Compose; no se versionó ninguna ruta personal.
- FE-04: [PR #36](https://github.com/Cesitar16/anomaly-zero/pull/36) sigue `OPEN`, contra `dev`; sus checks reportaban backend/frontend aprobados. Por ello, las comprobaciones de interfaz que dependen de FE-04 quedan pendientes.

## Docker y rutas

Comandos ejecutados: `docker compose -p az-ful132 config --quiet`, `docker compose -p az-ful132 build`, `docker compose -p az-ful132 up -d` y `docker compose -p az-ful132 ps`.

- Ambas imágenes construyeron. Backend y frontend aparecen `healthy`.
- La portada `http://127.0.0.1:18080/` respondió HTTP 200.
- `/health` respondió correctamente tanto en backend directo (`:18000`) como a través del proxy Nginx (`:18080`).
- `/api/v1/regions`, `/api/v1/products` y `/api/v1/series` respondieron por el proxy; se recibieron 1 región y 3 productos.
- `/explore?fuente=api` devuelve HTTP 200 por el fallback SPA, pero eso no prueba que el explorador funcione: el `ExplorerPage` de `dev` continúa siendo el placeholder mientras #36 siga abierta.
- El volumen del contenedor está montado en `/app/data/processed` con `readOnly=true`.
- Se comprobó que las imágenes no incluyen el snapshot ni `data/raw`; la imagen frontend tampoco contiene `.env` ni directorios de datos. Los Dockerfiles copian solo fuentes necesarias y `.dockerignore` excluye datos, notebooks, credenciales y cachés.

## Snapshot y evidencia científica

El snapshot local se leyó con el validador `read_snapshot` del backend. También cotejé en el host cada payload y su manifiesto local contra los hashes y bytes declarados por la procedencia del snapshot.

| Comprobación | Resultado |
|---|---|
| Producto | GPM_3IMERGM, IMERG Final V07B; variable `Grid/precipitation`; unidad `mm/hr` |
| Clasificación y soporte | `synthetic:false`; `point_sample`; sin aprobación de soporte regional |
| QA | `basic_checks_only`; `provider_flags_applied:false` |
| Cobertura del snapshot | 12 períodos esperados, 12 presentes, 12 válidos, 0 nulos |
| Proveniencia de gránulos | 12 registros CMR `verified_nasa_granule`; 12/12 archivos coinciden en SHA-256 y tamaño |
| Manifiestos | 12/12 SHA-256 de sidecars coinciden |
| Identidad | `dataset_id=imerg-2005-point-66cf65a5bcf2d99309af` |
| SHA-256 del archivo snapshot | `4fc3fb07e4e56ae65e27c7c3cce510363437d0f8547f20e1dfde53f01561be94` |
| `snapshot_sha256` interno | `7c1ac31560771bc8bb76df836a7dbba378ec5d35febf17fd75478b31c28d5904` |

La API real, consultada por Nginx con `region_id=murray-darling-basin`, `product_id=P02` y enero–diciembre de 2005, devolvió HTTP 200, `data_state=available`, doce puntos, `synthetic:false`, IMERG V07B, `mm/hr`, `point_sample`, QA `basic_checks_only` y `provider_flags_applied:false`. El `dataset_id` y los hashes de fuente coinciden con el snapshot montado. En este snapshot los doce valores son válidos: no hubo nulos ni valores cero. Los tests con fixtures sintéticas cubren cero frente a null; esos fixtures no se presentan como observaciones NASA.

## Export CSV

`GET /api/v1/series/export.csv` con los mismos parámetros respondió HTTP 200, `Content-Type: text/csv; charset=utf-8`, `Content-Disposition: attachment; filename="anomaly-zero-series.csv"` y `Cache-Control: no-store`.

El CSV contiene doce filas `observation`. Comparé fila por fila período, valor, estado QA, motivo de faltante, versión, unidad, soporte espacial, `synthetic`, `provider_flags_applied` y dataset ID. Los hashes fuente del CSV coinciden con la procedencia JSON. Resultado: **CSV y JSON coinciden**. Esta comprobación es del endpoint; no prueba una descarga implementada en el frontend (BE-08).

## Estados negativos y fixtures

- HTTP observados contra el contenedor con snapshot: región desconocida 404; producto desconocido 404; parámetro inválido 422; rango fuera de cobertura 422.
- Contenedor sin snapshot predeterminado: 200 `no_data`, serie vacía y `dataset_id:null`.
- Snapshot configurado pero ausente: 503 `SERVICE_UNAVAILABLE`, sin ruta de archivo expuesta.
- Test existente de snapshot inválido: 500 `INTERNAL_ERROR` sanitizado, aprobado.
- Suites existentes con fixtures cubren cero/null en JSON/CSV, `no_data`, validación de errores, snapshot inválido y rechazo de hashes. Ninguna fixture se usó como evidencia NASA.
- Error de red visible en la interfaz, aviso de sintéticos de FE-04, tabla/gráfico integrados, navegación y tamaños móvil/escritorio: **no ejecutados** porque FE-04 no está integrada en `dev`.
- No se capturó screenshot del flujo del explorador: la implementación de ese flujo sigue pendiente de #36.

## Validaciones de código

Ejecutadas en el SHA indicado arriba:

- `uv sync --locked --python 3.12 --group dev --group research` — pasó.
- `uv run pytest backend/tests research/tests -q` — **274 passed**, 1 warning de deprecación Starlette/httpx.
- `uv run ruff check backend research` — pasó.
- `npm ci --prefix frontend` — pasó, 0 vulnerabilidades informadas.
- `npm run lint --prefix frontend` — pasó.
- `npm run test --prefix frontend` — **56 passed**. Tests de `ScientificSeriesPanel` — **8 passed**.
- `npm run build --prefix frontend` — pasó.
- `git diff --check` — pasó.
- Enfoque de series y CSV: **14 passed**; lector de snapshot: **15 passed**; caso API de snapshot inválido: **1 passed**.

No se encontraron defectos que justificaran cambios de código o de contratos. No se modificaron filtros, rutas, adaptadores, algoritmos, QA ni datos.

## Checklist de aceptación FUL-132

- [x] Docker construye y ambos servicios están saludables.
- [x] Nginx → FastAPI → snapshot IMERG auténtico, montado en solo lectura.
- [x] JSON autentica 12 períodos, producto, unidad, soporte, QA e identidad/procedencia.
- [x] CSV coincide con JSON para los doce períodos y metadatos comprobados.
- [x] Errores HTTP y respuestas `no_data` comprobados; los casos de `500` sanitizado y cero/null están cubiertos por tests existentes con fixtures.
- [ ] Flujo navegador → FE-04 → API: bloqueado hasta que PR #36 se fusione en `dev`.
- [ ] Gráfico, tabla, copy, error de red, demo sintética y adaptación móvil en la aplicación integrada: pendiente de FE-04.
- [ ] Aceptación E2E completa y recomendación de release: pendiente del flujo navegador real.

No se afirma aprobación E2E completa. La conclusión científica de esta ejecución se limita al punto IMERG 2005 verificado: doce meses en `mm/hr`, soporte puntual y QA básica; no equivale a promedio regional, QA de proveedor aprobada, tendencia ni inferencia.

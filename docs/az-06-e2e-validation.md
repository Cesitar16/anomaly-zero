# AZ-06 / FUL-132 — Informe de validación E2E

**Resultado: serie E2E NASA verificada; BE-08 validado por API, parser local y pruebas automatizadas. Descarga desde el botón del navegador pendiente de comprobación manual.** No se completó esa interacción de navegador en esta actualización. La evidencia no constituye aprobación científica de QA regional, una tendencia ni autorización para publicar inferencias o modelos.

## Identidad del entorno

- Rama de validación: `test/ful-132-az-06-e2e-validation`.
- `origin/dev` integrado: `1bd970d88a549af96e34021e8f5096a200d8a03d` (incluye FE-04 / PR #36 y BE-08 / PR #40).
- Commit de merge local de `origin/dev`: `cb9fdd67c26dc2d61b815afd5278743360332d45`.
- SHA de `origin/dev` evaluado: `1bd970d88a549af96e34021e8f5096a200d8a03d`.
- Snapshot de Compose: proyecto `az-ful132`; frontend `127.0.0.1:18080`, backend `127.0.0.1:18000`.
- Los puertos 8080 y 8000 estaban ocupados por otro proyecto Compose activo; no se detuvo ni modificó ese proyecto. Se eligieron puertos aislados para no interrumpirlo.
- Ambos contenedores quedaron `healthy`. La configuración del entorno apunta al directorio local procesado mediante un bind mount de solo lectura.

## Docker e imágenes

Se ejecutaron `docker compose -p az-ful132 config`, `build`, `up -d` y `ps`. Las dos imágenes se reconstruyeron desde esta rama, que ya contiene la página FE-04. Vite empaquetó `ExplorePage` y los componentes del explorador.

Comprobaciones de límites de datos:

- El backend no contiene el snapshot ni `/app/data/raw` dentro de la imagen.
- El frontend no contiene `.env` ni un directorio de datos.
- Docker informa el montaje de `/app/data/processed` como `readOnly=true` (`RW=false`).
- No se añadieron datos NASA, credenciales ni rutas personales al commit.

## Explorador y serie NASA

La iteración anterior de AZ-06 (build sin BE-08, SHA `927a4782783cb9c2cbb41b9b8dd6a361c330d59d`) comprobó la serie real en Edge, con gráfico, tabla, unidad y advertencias. Para esta actualización reconstruí FE-04 + BE-08; la API y el snapshot se volvieron a consultar. Al iniciar la repetición del flujo visual, Computer Use fue detenido por Escape físico; no afirmo haber revisado en navegador esta build ni el click del botón de descarga. Los puntos siguientes describen aquella ejecución previa.

- Landing y `/explore` respondieron y se renderizaron. La fuente activa fue **Servicio real (API)**.
- Apareció `Serie completa`, sin el aviso de datos sintéticos asociado a la respuesta (`MockDataNotice`). La cabecera conserva la etiqueta global `Demostración` que representa el estado general configurado del explorador, no el origen de esta respuesta; en la página, el selector confirmó API.
- Se observó el gráfico y una tabla accesible de 12 filas. Los valores/meses visibles coinciden con la respuesta HTTP; la tabla rotula `mm/hr` y `Calidad no evaluada`.
- Se mostró la advertencia de muestra de un solo punto y de que no es un promedio validado de la cuenca.
- La calidad indica `basic_checks_only`, que los flags del proveedor no se aplicaron y que no se interpretan sus campos QA. No presenta la QA como aprobada.
- El mapa informa que no hay capa geográfica y no dibuja una escala engañosa. El análisis de tendencia aparece no disponible y su botón deshabilitado.
- En escritorio maximizado (1536 px) comprobé el formulario y el gráfico. En una ventana compacta de 632 px (por debajo del breakpoint de 768 px) comprobé que los filtros se apilan y que el gráfico y la tabla siguen accesibles. Esto prueba el layout responsive en viewport estrecho, no una emulación de dispositivo físico ni una auditoría exhaustiva de accesibilidad móvil.
- La ruta sin parámetros también conserva el modo de demostración configurado por defecto. No fue necesario establecer `VITE_EXPLORE_API=http`: `?fuente=api` selecciona explícitamente la API y el control de la interfaz permite cambiar a demo. No alteré el modo inicial del sitio.
- No se guardó una captura nueva para esta actualización.

## Snapshot y respuesta JSON auténticos

El archivo local se validó con el lector del backend y su SHA-256 completo coincide con la auditoría anterior:

| Propiedad | Resultado |
|---|---|
| Producto | `GPM_3IMERGM`, IMERG Final V07B |
| Variable y unidad | `Grid/precipitation`, `mm/hr` |
| Clasificación | `synthetic:false` |
| Soporte espacial | `point_sample`; una celda, no promedio regional |
| QA | `basic_checks_only`; `provider_flags_applied:false` |
| Dataset | `imerg-2005-point-66cf65a5bcf2d99309af` |
| Cobertura | 12 esperados, 12 presentes, 12 válidos, 0 faltantes |
| Nulos / ceros observados | 0 / 0 en este snapshot |
| Registros fuente y hashes | 12 registros NASA verificados y 12 SHA-256 en la respuesta |
| SHA-256 del archivo snapshot | `4fc3fb07e4e56ae65e27c7c3cce510363437d0f8547f20e1dfde53f01561be94` |
| SHA-256 interno del snapshot | `7c1ac31560771bc8bb76df836a7dbba378ec5d35febf17fd75478b31c28d5904` |

La respuesta conserva el identificador de dataset y hashes de los doce archivos fuente. El backend no informa en este payload las fechas de creación/descarga del snapshot ni hash/versión de manifiesto (`null`); esos campos aparecen como “No informado” en la interfaz y no se dedujeron a partir del SHA del archivo snapshot.

La serie se pidió a través del proxy Nginx. `/health`, `/api/v1/regions`, `/api/v1/products` y `/api/v1/series` respondieron correctamente. El recurso de productos expone tres productos; en la interfaz MERRA-2 y GLDAS se muestran como no disponibles para esta API. No se presentan los datos descargados en investigación offline como series API aprobadas.

## BE-08 — exportación CSV

`GET /api/v1/series/export.csv` a través del proxy respondió HTTP 200 con `Content-Type: text/csv; charset=utf-8`, encabezado de descarga y doce filas `observation`. Guardé la respuesta en `%TEMP%\anomaly-zero_be08_imerg_2005.csv` y `Import-Csv` la abrió y parseó correctamente: 12 filas, desde `2005-01-01` hasta `2005-12-01`, y 12 hashes fuente. El archivo temporal quedó fuera del repositorio.

Comparé las doce filas con `/api/v1/series`: período, valor, estado de calidad, producto/versión, unidad, soporte, dataset, hashes fuente, `synthetic` y `provider_flags_applied`. **Las 12 filas coinciden.** Los valores permanecen en `mm/hr`; QA continúa `unassessed` por observación y `basic_checks_only` como estado de verificación; no se aplican flags del proveedor.

La funcionalidad BE-08 está integrada y sus pruebas de página/adaptador automatizadas verifican: Blob y nombre de descarga, MIME `text/csv`, parámetros de la consulta, bloqueo en modo demo, `no_data`, carga y filtros sin aplicar, cancelación de solicitud obsoleta, y rechazo de respuesta HTML/error para impedir archivos inválidos. Sin embargo, el click y la descarga del botón en un navegador real **no se verificaron** en esta ejecución.

## Estados y límites verificados

- HTTP 404 por región desconocida y HTTP 422 por rango inválido: cliente frontend integrado con FastAPI real, 6 pruebas de integración HTTP aprobadas en total.
- Respuesta CSV real del endpoint: 200, `text/csv`, archivo parseable, 12/12 valores y metadatos coincidentes con JSON.
- `no_data`, 404, 422, 500, 503, pérdida de respuesta, datos sintéticos y la distinción cero/null están cubiertos por las pruebas de contrato, cliente, componentes y página de FE-04 con fixtures rotuladas. Esos casos de error no se provocaron manipulando el snapshot real.
- Cero frente a null se valida con fixtures sintéticas. El snapshot NASA observado contiene doce valores válidos no nulos y ninguno igual a cero.
- No se calculó agregación regional, correlación, tendencia ni modelo. No se aprobó Gate R, Gate T ni QA de proveedor.

## Validaciones ejecutadas

- `uv sync --locked --python 3.12 --group dev --group research` — correcto.
- `uv run pytest backend/tests research/tests -q` — **274 passed**, 1 advertencia existente de deprecación Starlette/httpx.
- `uv run ruff check backend research` — correcto.
- `npm ci --prefix frontend` — correcto; npm informó 0 vulnerabilidades.
- `npm run lint --prefix frontend` — correcto.
- `npm run test --prefix frontend` — **205 passed, 6 skipped** porque son las pruebas condicionales contra un backend en vivo.
- `EXPLORE_LIVE_API=http://127.0.0.1:18000/api/v1 npm run test --prefix frontend -- --run liveBackend` — **6 passed**; quedaron ejercitadas las pruebas condicionales anteriores contra FastAPI en Docker.
- `npm run build --prefix frontend` — correcto. Vite advierte que un chunk del mapa supera 500 kB; el build no falla.
- `git diff --check` — correcto.

Las 6 pruebas condicionales se ejecutaron también contra el backend real, por lo que el resultado combinado del frontend es **211 pruebas aprobadas**. La prueba de exportación en el navegador usa fixtures sintéticas; la respuesta HTTP independiente sí se verificó contra el snapshot NASA local.

## Checklist FUL-132

- [x] FE-04 actualizada desde el merge presente en `origin/dev`; cambios incorporados sin conflicto.
- [x] Docker reconstruido; frontend y backend saludables; proxy y snapshot de solo lectura comprobados.
- [x] Serie real IMERG NASA, 12 períodos, metadatos, procedencia y hashes verificados por API.
- [x] CSV del endpoint parseado localmente; sus doce filas y metadatos coinciden con JSON.
- [x] BE-08 probado con fixtures para MIME/Blob, disponibilidad, filtros pendientes y errores.
- [ ] Confirmar en navegador que el botón BE-08 se habilita con la serie real, iniciar descarga y abrir el archivo bajado.
- [x] Layout escritorio y compacto revisados; estadísticas no autorizadas permanecen deshabilitadas.
- [x] Suite backend/frontend, Ruff, lint, build y pruebas HTTP en vivo aprobadas.
- [ ] Revisión humana y merge de PR #39.

La serie del MVP sigue siendo una **muestra puntual exploratoria** y no equivale a un promedio espacial, QA del proveedor aprobada, tendencia científica ni resultado inferencial. Para cerrar la aceptación de BE-08 falta que una persona ejecute el click de descarga en Edge, confirme la descarga y abra el archivo descargado; el endpoint y su CSV sí están verificados.

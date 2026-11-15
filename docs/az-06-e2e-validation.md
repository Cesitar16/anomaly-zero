# AZ-06 / FUL-132 — Informe de validación E2E

**Resultado: E2E funcional aprobado para la demo local con IMERG auténtico.** La rama incorpora FE-04 y se verificó el recorrido navegador → Nginx → FastAPI → snapshot NASA. Esto no constituye aprobación científica de QA regional, una tendencia, ni autorización para publicar inferencias o modelos.

## Identidad del entorno

- Rama de validación: `test/ful-132-az-06-e2e-validation`.
- `origin/dev` integrado: `5512fdb03961c6daec5e992874c1196edd326589` (merge de FE-04 / PR #36).
- Commit de integración local de `origin/dev`: `d7bff8fe6b94084d8dd8933d3303d41416523b83`.
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

## Navegador y recorrido

En Microsoft Edge abrí la landing local y la ruta `/explore?fuente=api`; seleccioné la cuenca Murray–Darling, precipitación IMERG P02 y el rango inclusivo `2005-01`–`2005-12`, y envié el formulario.

- Landing y `/explore` respondieron y se renderizaron. La fuente activa fue **Servicio real (API)**.
- Apareció `Serie completa`, sin el aviso de datos sintéticos asociado a la respuesta (`MockDataNotice`). La cabecera conserva la etiqueta global `Demostración` que representa el estado general configurado del explorador, no el origen de esta respuesta; en la página, el selector confirmó API.
- Se observó el gráfico y una tabla accesible de 12 filas. Los valores/meses visibles coinciden con la respuesta HTTP; la tabla rotula `mm/hr` y `Calidad no evaluada`.
- Se mostró la advertencia de muestra de un solo punto y de que no es un promedio validado de la cuenca.
- La calidad indica `basic_checks_only`, que los flags del proveedor no se aplicaron y que no se interpretan sus campos QA. No presenta la QA como aprobada.
- El mapa informa que no hay capa geográfica y no dibuja una escala engañosa. El análisis de tendencia aparece no disponible y su botón deshabilitado.
- En escritorio maximizado (1536 px) comprobé el formulario y el gráfico. En una ventana compacta de 632 px (por debajo del breakpoint de 768 px) comprobé que los filtros se apilan y que el gráfico y la tabla siguen accesibles. Esto prueba el layout responsive en viewport estrecho, no una emulación de dispositivo físico ni una auditoría exhaustiva de accesibilidad móvil.
- La ruta sin parámetros también conserva el modo de demostración configurado por defecto. No fue necesario establecer `VITE_EXPLORE_API=http`: `?fuente=api` selecciona explícitamente la API y el control de la interfaz permite cambiar a demo. No alteré el modo inicial del sitio.
- No guardé una captura en el repositorio; las vistas se inspeccionaron en vivo en Edge.

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

## Paridad de exportación CSV

`GET /api/v1/series/export.csv` respondió HTTP 200 con tipo `text/csv; charset=utf-8`, descarga adjunta y 12 filas `observation`. Comparé las 12 filas con JSON: período, valor, estado QA, motivo de faltante, región, producto y versión, variable, cantidad, unidad, soporte y estado de aprobación espacial, dataset, los 12 hashes fuente, clasificación sintética y flags del proveedor. **Los valores y metadatos comparados coinciden en las 12 filas.** Esta verificación cubre el endpoint CSV; no afirma que haya una función de descarga CSV en la interfaz.

## Estados y límites verificados

- HTTP 404 por región desconocida y HTTP 422 por rango inválido: cliente frontend integrado con FastAPI real, 6 pruebas de integración HTTP aprobadas en total.
- `no_data`, 404, 422, 500, 503, pérdida de respuesta, datos sintéticos y la distinción cero/null están cubiertos por las pruebas de contrato, cliente, componentes y página de FE-04 con fixtures rotuladas. Esos casos de error no se provocaron manipulando el snapshot real.
- Cero frente a null se valida con fixtures sintéticas. El snapshot NASA observado contiene doce valores válidos no nulos y ninguno igual a cero.
- No se calculó agregación regional, correlación, tendencia ni modelo. No se aprobó Gate R, Gate T ni QA de proveedor.

## Validaciones ejecutadas

- `uv sync --locked --python 3.12 --group dev --group research` — correcto.
- `uv run pytest backend/tests research/tests -q` — **274 passed**, 1 advertencia existente de deprecación Starlette/httpx.
- `uv run ruff check backend research` — correcto.
- `npm ci --prefix frontend` — correcto; npm informó 0 vulnerabilidades.
- `npm run lint --prefix frontend` — correcto.
- `npm run test --prefix frontend` — **197 passed, 6 skipped** porque son las pruebas condicionales contra un backend en vivo.
- `EXPLORE_LIVE_API=http://127.0.0.1:18000/api/v1 npm run test --prefix frontend -- --run liveBackend` — **6 passed**; quedaron ejercitadas las pruebas condicionales anteriores contra FastAPI en Docker.
- `npm run build --prefix frontend` — correcto. Vite advierte que un chunk del mapa supera 500 kB; el build no falla.
- `git diff --check` — correcto.

Las 6 pruebas condicionales se ejecutaron también contra el backend real, por lo que el resultado combinado del frontend es **203 pruebas aprobadas**, sin atribuir datos de fixture al snapshot NASA.

## Checklist FUL-132

- [x] FE-04 actualizada desde el merge presente en `origin/dev`; cambios incorporados sin conflicto.
- [x] Docker reconstruido; frontend y backend saludables; proxy y snapshot de solo lectura comprobados.
- [x] Recorrido real en navegador con 12 valores IMERG NASA, gráfico, tabla y advertencias.
- [x] Metadatos científicos, procedencia y 12 hashes comprobados; CSV comparado con JSON.
- [x] Layout escritorio y compacto revisados; estadísticas no autorizadas permanecen deshabilitadas.
- [x] Suite backend/frontend, Ruff, lint, build y pruebas HTTP en vivo aprobadas.
- [ ] Revisión humana y merge de PR #39.

La demo local es funcional con datos NASA auténticos como **muestra puntual exploratoria**. No equivale a una demo de promedio espacial, QA del proveedor aprobada, tendencia científica, ni resultado inferencial. Repetir el smoke test después de cualquier cambio de datos o código antes de usarlo en una presentación.

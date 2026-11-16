# FE-08 — Mapa contextual del explorador

El panel `/explore` reutiliza el MapLibre GL JS que ya tenía el frontend. Cuando hay una serie cargada, muestra el mapa base de OpenStreetMap aunque la respuesta no traiga `raster_layers`. El mapa solo aporta contexto geográfico: el encuadre de Murray–Darling se toma de la extensión aproximada documentada y no se dibuja como si fuera el límite oficial de la cuenca.

## Proveedor del mapa base

Se usa la teselación raster pública `https://tile.openstreetmap.org/{z}/{x}/{y}.png`. La atribución visible enlaza a [OpenStreetMap Copyright](https://www.openstreetmap.org/copyright); los datos OSM se distribuyen bajo ODbL. El servicio de teselas es de mejor esfuerzo, no tiene SLA y sus recursos son limitados. Se deben respetar las cabeceras de caché del navegador, evitar precarga/descarga masiva y revisar la [política oficial de uso de teselas](https://operations.osmfoundation.org/policies/tiles/) antes de aumentar el tráfico. Para despliegues de mayor volumen se debe elegir un proveedor con condiciones y capacidad apropiadas.

No se configuran `Referrer-Policy` restrictivas ni cabeceras de no-cache en Nginx. No se descargan teselas durante build ni se incluyen datos cartográficos locales en la imagen.

## Marcador de observación

El marcador solo se crea cuando `spatial_aggregation.support_type` es `point_sample` y `latitude`/`longitude` son números finitos dentro de sus rangos geográficos. La conversión a MapLibre es `[longitude, latitude]`. La celda, el producto, la unidad, `verification_state`, flags del proveedor y `synthetic` se conservan para la ficha accesible del marcador. Si no hay coordenadas válidas, se informa su ausencia y no se infiere un punto desde el centro de la cuenca.

El panel mantiene visible que `point_sample` no equivale a promedio regional y que la QA del proveedor no está aprobada. Una respuesta sintética conserva la etiqueta explícita de demostración. La capa raster de demostración se sigue dibujando solo si la serie sintética declara y el resolver reconoce esa capa; en modo API no se genera raster artificial.

## Límite de cuenca y BE-10

FUL-137 / BE-10 no tiene aún un contrato o implementación publicada; por ello no se hace una petición ni se incorpora un polígono. El componente acepta opcionalmente un `ContextGeometryOverlay` interno (GeoJSON Polygon/MultiPolygon en memoria, etiqueta, atribución, URL segura de fuente/licencia, versión geométrica y SHA-256). No es un contrato de FastAPI. El panel rechaza el overlay sin procedencia HTTPS, hash SHA-256 de 64 caracteres y geometría poligonal. Cuando BE-10 publique su esquema y evidencia, el adaptador de la API deberá validar fuente, CRS, tipo de geometría, atribución y licencia antes de mapearla a esa interfaz. La capa futura se representa solo con un contorno discontinuo contextual y nunca como máscara de celdas, cálculo de área o agregación.

## Carga y fallos

MapLibre y su worker siguen cargándose con `React.lazy` desde la ruta Explore. Errores de inicialización, teselas o capa de demostración se muestran dentro del panel; el gráfico, la tabla, los filtros y la descarga CSV permanecen fuera de esa frontera. El usuario puede reintentar el mapa. El panel se adapta al ancho disponible y conserva los controles de zoom, navegación por teclado y atribución visible en móvil.

## Verificación de la rama FE-08 — 2026-11-16

- Base: `origin/dev` `3ed8e9f50e84fd1fef757e20cf9e4ccf4b86c20f`.
- Compose `az-ful132`: solo se reconstruyó el frontend desde este worktree; backend quedó saludable y sin recrear. Nginx `GET /health` devolvió 200. El snapshot continúa montado desde `data/processed` en solo lectura (`RW=false`).
- Serie real consultada mediante el proxy Nginx: `available`, 12 observaciones, `synthetic:false`, `mm/hr`, `point_sample`; punto `145.75° E, -37.6499977° S`, celda `IMERG-v07b-center-lon3257-lat523`. `basic_checks_only`, `provider_flags_applied:false`; QA del proveedor sigue sin aprobar.
- Suites: `uv run pytest backend/tests research/tests -q` — 279 aprobadas; `uv run ruff check backend research` — correcto; frontend Vitest — 214 aprobadas y 6 pruebas live omitidas en la ejecución estándar; lint/build — correctos; `git diff --check` — correcto. La advertencia del build por el chunk MapLibre >500 kB permanece; ese chunk se carga diferido al abrir el mapa.
- Revisión de Edge no completada: Computer Use se detuvo por Escape físico antes de abrir la aplicación. No hay captura ni afirmación de que las teselas o el marcador se hayan visto en navegador. La aplicación queda disponible en Docker para completar esa revisión manual.

URL para revisión visual local: `http://127.0.0.1:18080/explore?fuente=api&region=murray-darling-basin&product=P02&start=2005-01&end=2005-12`.

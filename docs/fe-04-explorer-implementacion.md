# FE-04 · Implementación de `/explore` con mocks tipados y estados científicos verificables

Tarjeta: **FUL-119 / FE-04**. Rama: `feature/ful-119-fe-04-explore-mocks-tipados`, creada desde el último `origin/dev` (con FE-03 y FE-05 ya integradas).

Este documento explica **qué se construyó**, **cómo se ejecuta**, **qué endpoint alimenta qué componente**, **qué estado de FE-03 se ve dónde** y **qué quedó pendiente de revisión**. No define ciencia nueva: la pantalla solo muestra lo que el contrato AZ-04 `0.1-draft` permite mostrar.

## 1. Resumen

- `/explore` es ahora una pantalla real dentro de la app React existente (no hay una app nueva). El marcador de posición anterior se eliminó.
- Toda la pantalla lee datos por **una sola puerta**: la interfaz `ExploreApi`. Hay dos fuentes, y la persona puede cambiar entre ellas con un selector visible ("Fuente de los datos"):
  - **Servicio simulado** (`MockExploreApi`): respuestas **explícitamente sintéticas** que cumplen el OpenAPI. Es la fuente por defecto de desarrollo y QA, rotulada de forma permanente ("Demostración").
  - **Servicio real** (`HttpExploreApi`): cliente `fetch` tipado hacia `/api/v1`. En desarrollo Vite reenvía `/api/v1` y `/health` al FastAPI local (proxy, mismo origen, sin CORS abierto).
- **Nunca hay respaldo automático**: si la API real falla o no responde, la pantalla muestra el error. No pasa sola a datos simulados. Cambiar de fuente descarta todo lo cargado y los filtros (los identificadores de un servicio no existen en el otro).
- El mapa (MapLibre GL JS) y el gráfico (Recharts) se cargan de forma diferida junto con la ruta `/explore`. El mapa solo se descarga si existe una capa dibujable.
- Los análisis estadísticos siguen **deshabilitados**: `POST /analyses` se muestra como no disponible y el modo real no lo llama.
- Mientras el backend no publique `raster_layers`, el mapa dice con honestidad que no hay capa. No dibuja frames falsos, contorno de cuenca, leyenda científica ni herramientas por píxel.

## 2. Cómo ejecutarlo

### Solo el frontend (servicio simulado)

Desde `frontend/`:

```bash
npm ci
npm run dev        # http://localhost:5173/explore (fuente: servicio simulado)
npm run lint       # oxlint
npm test           # vitest (197 pruebas; las 6 de integración real se omiten si no hay backend)
npm run build      # tsc -b + vite build
```

### Frontend + FastAPI (dos procesos, API real)

Terminal 1, desde la raíz del repositorio (backend):

```bash
uv sync --group dev
uv run uvicorn backend.app.main:app --port 8000
```

Sin snapshot, el backend responde con honestidad: `/products` marca todo como `unavailable` y `/series` responde `200 no_data`.

Con un snapshot configurado en **el proceso del backend** se sirve la serie puntual de IMERG 2005. Para probar sin datos NASA, genera un snapshot **sintético** (valores ficticios, el backend responde `synthetic: true`):

```bash
uv run --group dev python scripts/make_synthetic_imerg_snapshot.py data/processed/ful116-sintetico
ANOMALY_ZERO_IMERG_SNAPSHOT=data/processed/ful116-sintetico/processed/imerg_2005_point_snapshot.json \
  uv run uvicorn backend.app.main:app --port 8000
```

El snapshot real de DS-03 (`data/processed/ful116/imerg_2005_point_snapshot.json`) no se versiona; si existe, el backend lo usa por defecto. Los resultados con datos reales se informan por separado.

Terminal 2 (`frontend/`):

```bash
npm run dev
```

Abre `http://localhost:5173/explore?fuente=api`. Vite reenvía `/api/v1` y `/health` a `http://127.0.0.1:8000`; para otro destino, `API_PROXY_TARGET=http://127.0.0.1:9000 npm run dev` (variable del proceso de Vite, no `VITE_*`, no llega al navegador). Para que la fuente real sea la predeterminada de esa compilación: `VITE_EXPLORE_API=http`.

Comprobación rápida por el proxy:

```bash
curl http://localhost:5173/health
curl "http://localhost:5173/api/v1/regions"
```

### Con Docker Compose (frontend en Nginx + FastAPI)

`docker-compose-mvp.md` (BE-07/infra, ya en `dev`) levanta FastAPI y una compilación estática de este frontend servida por Nginx, que reenvía `/api/v1/*` y `/health` al backend en el mismo origen. El cliente real de FE-04 pide rutas relativas `/api/v1`, así que funciona sin cambios ni CORS.

```powershell
Copy-Item .env.example .env       # ANOMALY_ZERO_PROCESSED_DIR debe contener ful116/imerg_2005_point_snapshot.json
docker compose up -d --build
```

Abre `http://127.0.0.1:8080/explore?fuente=api` (o elige "Servicio real (API)" en el selector). La compilación de Docker no define `VITE_EXPLORE_API`, así que **sin `?fuente=api` la pantalla arranca en el servicio simulado**; es intencional. Con el snapshot auténtico montado, la serie llega con `synthetic: false`; sin snapshot, `no_data`. Esta ruta (Docker + snapshot real) no se probó en esta rama.

### Prueba de integración real (frontend ↔ backend)

Con el backend en marcha (y, si quieres, el proxy de Vite):

```bash
EXPLORE_LIVE_API=http://127.0.0.1:5173/api/v1 npm test --prefix frontend -- liveBackend
```

Usa el mismo cliente HTTP tipado que la pantalla y valida cada respuesta contra el OpenAPI real: catálogo, productos, serie (cero, nulo, unidad `mm/hr`, `point_sample`), `404` y `422`. Funciona con y sin snapshot. Sin `EXPLORE_LIVE_API` se omite (así el CI no necesita Python en el job del frontend).

### Parámetros de la URL

Los filtros viven en la URL para poder compartir una vista. Se validan como entrada de usuario.

| Parámetro | Ejemplo | Qué hace |
|---|---|---|
| `fuente` | `api` o `demo` | Fuente de datos. Sin el parámetro, manda `VITE_EXPLORE_API` (por defecto, simulada) |
| `region` | `REG01` | Región elegida. Si no existe en el catálogo, error en el campo y **no** se consulta la serie |
| `product` | `P02` | Variable NASA elegida (mismo tratamiento) |
| `start`, `end` | `2005-01`, `2005-03` | Rango mensual `AAAA-MM`, hasta 240 meses |
| `month` | `2005-02` | Mes mostrado en el mapa (si hay capas) |
| `demo` | `error-503` | Escenario del servicio simulado (solo existe con `fuente=demo`) |

Vista de referencia (simulada): `/explore?region=REG01&product=P02&start=2005-01&end=2005-03`.
Vista de referencia (API real con snapshot): `/explore?fuente=api&region=murray-darling-basin&product=P02&start=2005-01&end=2005-12`.

## 3. Estados de FE-03 y dónde verlos

| Estado FE-03 | Qué lo provoca | Cómo verlo | Captura |
|---|---|---|---|
| **E1** Sin regiones | `GET /regions` con `regions: []` | `/explore?demo=catalogo-vacio` | `07-catalogo-vacio-*` |
| **E2** Serie con huecos y cero | `200`, `available_with_gaps`, `synthetic: true` | `/explore?region=REG01&product=P02&start=2005-01&end=2005-03` | `02-serie-con-huecos-*` |
| **E3** `no_data` | `200` con `data_state: no_data` | `/explore?region=REG01&product=P03&start=2005-01&end=2005-12` | `03-sin-datos-*` |
| **E4** `404` y `422` | recurso inexistente, parámetro inválido, límite, fuera de cobertura | `?demo=no-encontrado`, o escribir un rango inválido en los filtros | (cubierto por pruebas, ver sección 6) |
| **E5** `503` (y 500, sin red) | servicio no disponible | `...&demo=error-503` (también `error-500` y `sin-red`) | `04-error-503-*` |
| **E6** Capa no disponible | `raster_layers` ausente (lo que sirve `dev`) o `state: unavailable` | modo predeterminado (ausente) o `?demo=capas-no-disponibles` | visible en `02-serie-con-huecos-*` (panel del mapa) |
| **E7** `409 ANALYSIS_METHOD_UNAVAILABLE` | `POST /analyses` | tarjeta "Análisis", botón "Calcular tendencia" deshabilitado; en modo simulado hay un botón auxiliar que muestra la respuesta 409 | visible en `02-serie-con-huecos-*` |
| **E8** Soporte puntual (`point_sample`) | `support_type: point_sample`, `mm/hr` | aviso de soporte de la serie (misma vista que E2) | visible en `02-serie-con-huecos-*` |
| **E9** Capas mixtas, mes con capa | `raster_layers` mixtas, mes `available` | `...&demo=capas-mixtas` | `05-capa-demo-enero-*` |
| **E10** Capas mixtas, mes sin capa | mes seleccionado `unavailable` | `...&demo=capas-mixtas&month=2005-02` | `06-mes-sin-capa-*` |

Fuente real (API), capturadas con FastAPI local detrás del proxy de Vite:

| Situación | Cómo verla | Captura |
|---|---|---|
| API real con snapshot **sintético** (`synthetic: true`): serie puntual con cero y huecos, aviso de datos sintéticos | backend con snapshot sintético y `/explore?fuente=api&region=murray-darling-basin&product=P02&start=2005-01&end=2005-12` | `08-api-con-snapshot-sintetico-*` |
| API real **sin snapshot**: `200 no_data` honesto, productos no disponibles, sin aviso sintético | backend sin snapshot, misma dirección | `09-api-sin-snapshot-*` |
| API real **sin conexión**: error de conexión con "Reintentar", sin pasar a datos simulados | `/explore?fuente=api` con el backend apagado | `10-api-sin-conexion-*` |

Todas las capturas están en `docs/fe-04/capturas/` en versión escritorio (1280 px) y móvil (390 px), y las generó la aplicación compilada, no un maquetado. Ninguna usa datos NASA reales.

Lo que **no** se puede mostrar como captura: una serie real con `synthetic: false` y valores, porque los valores reales de DS-03 viven en un snapshot local que Git ignora. Lo que sí se comprueba por prueba automática es la parte que importa: con la fuente real no aparece el aviso de "sintético" salvo que la respuesta lo traiga, ni los escenarios de demostración.

## 4. Qué endpoint alimenta qué componente

| Endpoint | Componente | Notas |
|---|---|---|
| `GET /regions` | `ExploreFilters` (`RegionSelect`) | Con una sola región, se elige sola |
| `GET /products?region_id=` | `ExploreFilters` (`ProductSelect`) | Los productos `unavailable` se listan con su rótulo y siguen consultables (ver D10) |
| `GET /series` | `TimeSeriesChart`, `SeriesTable`, `MapPanel`, `QualityNotice`, `SupportNotice`, `CoverageSummary`, `SourceProvenance` | `raster_layers` solo alimenta el mapa |
| `POST /analyses` | `AnalysisUnavailable` (`AnalysisStatus`) | Siempre "no disponible". No se llama en modo HTTP |
| `GET /analyses/{id}` | (ninguno) | En `dev` siempre responde `404 RESOURCE_NOT_FOUND`; el frontend no lo llama |

## 5. Qué se conservó del dato (y cómo se verifica)

- **Cero válido**: se dibuja en 0 y la tabla dice "0 (cero válido)".
- **Nulo**: se dibuja como hueco (la línea no se une, `connectNulls={false}`), con una franja ámbar, y la tabla dice "Sin dato". Nulo no es cero.
- **Unidades**: `mm/hr`, rotulado como tasa media mensual. El eje Y parte de 0 solo para `mm/hr`.
- **Soporte puntual**: `point_sample` se avisa como "punto, no área". La cobertura cuenta meses; no mide el área de la región.
- **Calidad**: sin evaluar y "solo controles básicos" se muestran como advertencia, nunca como "aprobada".
- **Errores**: `404`, `422`, `500`, `503` y la falta de red son estados distintos y ninguno se disfraza de "sin datos".
- **Accesibilidad**: el gráfico tiene descripción para lector de pantalla y siempre hay una tabla equivalente; las pruebas corren `axe`. Los textos de error usan `role="alert"`.

## 6. Pruebas

Total: **197 pruebas** que corren siempre (189 de esta rama y 8 del `ScientificSeriesPanel` de FUL-130), más **6 de integración real** que se activan con `EXPLORE_LIVE_API` (`src/test/`).

| Archivo | Qué comprueba |
|---|---|
| `explore/contracts.test.ts` | Las fixtures oficiales son idénticas a los ejemplos del OpenAPI; todas las respuestas (fixtures, simulado y capturas reales de `dev`) validan contra los esquemas con Ajv 2020 |
| `explore/lib.test.ts` | Rangos de meses, formato, modelo del gráfico (cero/nulo), resolución del mapa, lectura y escritura de la URL |
| `explore/mockApi.test.ts` | Respuestas del simulado, escenarios, `422` con `details.field`, `409` de análisis, clones sin mutación |
| `explore/httpApi.test.ts` | Cliente HTTP contra las respuestas reales de `dev`, incluida la ruta inexistente (`{"detail":"Not Found"}` se trata como falla de red) |
| `explore/useResource.test.tsx` | Carga, cancelación de peticiones obsoletas |
| `explore/components.test.tsx` | Cada componente, incluida la ausencia honesta del mapa |
| `explore/page.test.tsx` | Pantalla completa: flujos, validación, errores, selector de fuente (sin respaldo automático, cambio de fuente descarta lo anterior), modo HTTP con respuestas reales, capas de demostración y `axe` |
| `explore/liveBackend.test.ts` | **Integración real** contra FastAPI en ejecución (se omite sin `EXPLORE_LIVE_API`) |
| `app.test.tsx` | Navegación desde la landing (CTA, barra y pie) |

Verificado en este entorno (reporte separado de los datos reales): FastAPI local **sin snapshot** y **con snapshot sintético** pasan las 6 pruebas de integración a través del proxy de Vite. **No** se ejecutó contra el snapshot real de DS-03, que no está en el repositorio.

CI: `Checks` ejecuta `npm test` del frontend antes de compilar (paso "Frontend tests", en un commit aparte). La integración real no corre en CI.

## 7. Diferencias y observaciones del contrato

1. **`raster_layers`**: el OpenAPI lo define, pero `dev` nunca lo emite. Es la razón de la ausencia honesta del mapa. Los ejemplos con capas (E9, E10) son derivados del esquema, no oficiales.
2. **Campos opcionales**: `dev` los omite en vez de enviarlos `null`. Los tipos del frontend los tratan como opcionales.
3. **Errores**: `details` llega siempre `null` en `dev` (O5). El simulado sí envía `details.field` en `INVALID_PARAMETER`, como el ejemplo oficial.
4. **Rutas inexistentes**: `dev` responde `{"detail":"Not Found"}`, que no es un sobre de error del contrato (O13). El cliente HTTP lo clasifica como "sin respuesta del servicio".
5. **Versión de producto**: `dev` toma `product_version` del snapshot (`V07B`), mientras que `/products` sin snapshot informa la colección `07` (O15). La pantalla muestra lo que llegue.
6. **`/analyses`**: BE-05 (PR #31) ya está en `dev`: `POST /api/v1/analyses` valida la petición y responde `409 ANALYSIS_METHOD_UNAVAILABLE` (no crea análisis) y `GET /api/v1/analyses/{id}` responde `404`. Esta pantalla igual no llama a `/analyses` en modo real: mantiene el botón "Calcular tendencia" deshabilitado hasta que exista un método estadístico aprobado.
7. **Tarjeta vs FE-03**: la tabla antigua de la tarjeta decía "deshabilitar consulta" para productos no disponibles, y FE-03 los deja consultables (para ver el `200 no_data` real). Se siguió FE-03 (D10).

## 8. Decisiones

La tarjeta (decisión de César del 15-11) aprueba FE-03 como base de UX, MapLibre GL JS + Recharts, la ruta diferida y D1 a D9 de FE-03 con condiciones. Estado frente a esta implementación:

| Id | Tema | Estado |
|---|---|---|
| D1, D5, D6, D7, D8 | Flujo y 10 estados, análisis no disponible, filtros en URL, gráfico antes que mapa en móvil, mocks de E9/E10 | Aprobadas e implementadas |
| D2 | Copy científico, condicionado a usarlo según el estado real de la respuesta | Implementado en `content/exploreCopy.ts` (un solo archivo). Pendiente su revisión de textos |
| D3 | MapLibre GL JS 6.18.0 (directo) y Recharts `^3.10.1` (resuelve a 3.10.1) | Aprobado. Recharts coincide con la PR #33 de FUL-130, ya fusionada en `dev` (ver sección 12) |
| D4 | Encuadre del mapa sin geometría | Extensión ilustrativa solo para la demostración sintética, rotulada. Sin límite de cuenca |
| D9 | Marcador «Punto de muestra» | **No implementado.** La tarjeta lo permite solo con coordenadas de una respuesta auténtica. Hoy el punto se muestra como texto (celda y coordenadas) en el aviso de soporte. Pendiente opcional |
| D10 | Productos `unavailable` | Se pueden consultar (FE-03), para mostrar el `200 no_data` real que exige la tarjeta sin snapshot. Pendiente de confirmar |
| Mes | Entrada del mes como texto `AAAA-MM` | Campo de texto con validación, en vez de `<input type="month">` (soporte irregular) |
| Fuente | Selector visible, sin respaldo automático | La fuente predeterminada es la simulada (el sitio público no tiene backend desplegado). Pendiente de confirmar si la real debe ser la predeterminada al integrar |
| CI | Paso de pruebas del frontend en `Checks` | Agregado en un commit aparte, fácil de revertir |
| Demo | Botón auxiliar que muestra el `409` | Solo con la fuente simulada; con la real no existe y no se llama a `/analyses` |

## 9. Tamaño del paquete

| Pieza | Tamaño | Cuándo se descarga |
|---|---|---|
| Entrada de la app | ~283 kB (90 kB gzip) | Siempre |
| Ruta `/explore` (con Recharts) | ~427 kB (125 kB gzip) | Al abrir `/explore` |
| Mapa (MapLibre) | ~1,07 MB (291 kB gzip) + worker ~519 kB | Solo si hay una capa dibujable (hoy, solo la demostración sintética) |

Vite avisa de chunks de más de 500 kB; es un aviso, no un error. El mapa no se descarga en modo real mientras el backend no publique capas.

## 10. Archivos principales

```
frontend/src/features/explore/
  ExplorePage.tsx            pantalla (default export, carga diferida)
  explore.css                estilos (solo tokens del diseño)
  types/contracts.ts         tipos del contrato
  content/exploreCopy.ts     textos en español (propuesta pendiente de César)
  data/                      ExploreApi, simulado, cliente HTTP, fixtures sintéticas
  hooks/                     useResource, useExplorer
  lib/                       meses, formato, modelo del gráfico, resolución del mapa, URL
  components/                filtros, selector de fuente, gráfico, tabla, mapa, avisos, procedencia, calidad, errores
frontend/src/test/explore/   pruebas
docs/fe-04/capturas/         capturas escritorio y móvil
frontend/vite.config.ts      proxy de desarrollo /api/v1 y /health
scripts/make_synthetic_imerg_snapshot.py   snapshot IMERG sintético para probar contra FastAPI
```

## 11. Qué falta para la integración real

Hecho: cliente HTTP tipado, proxy de Vite, selector de fuente, prueba de integración real con y sin snapshot, procedimiento de dos procesos (sección 2).

Pendiente, a propósito, hasta que lo apruebe quien corresponda:

1. **Despliegue**: no se afirma que el proyecto esté desplegado. En un sitio sin backend, `fuente=api` muestra el error de conexión; es lo esperado.
2. **Capas raster**: cuando el backend publique `raster_layers` `available`, hay que entregar un `RasterResolver` real al cliente HTTP (hoy devuelve `null` a propósito: el modo real nunca dibuja).
3. **Análisis**: `POST /analyses` ya existe en `dev` (BE-05, PR #31) pero solo responde `409`. Cuando haya un método estadístico aprobado, se cambia `capabilities.analyses` del cliente HTTP y se agrega la vista del resultado. Antes de eso, no.
4. **Datos reales de DS-03**: probar con el snapshot real verificado y reportarlo aparte (no hay snapshot en el repositorio).

## 12. Coordinación y revisiones solicitadas

- **FUL-130 (César, PR #33, ya en `dev`)**: agregó Recharts `^3.10.1` y el módulo `scientific-series` (`ScientificSeriesPanel`). Al actualizar esta rama con `dev` el único conflicto fue `package.json` y `package-lock.json` (una sola entrada de Recharts; lockfile regenerado). Evaluación de reutilizarlo (no se hizo en esta PR, ver abajo):
  - **Compatible por tipos**: un `SeriesResponse` completo se puede pasar al panel sin adaptadores (verificado con `tsc`).
  - **No cubre la selección de mes**: no tiene `selectedMonth` ni `onSelectMonth`, el gráfico no responde al clic, no marca el mes elegido y la tabla no marca la fila activa. Aquí el clic sincroniza gráfico, línea de tiempo, mapa y tabla.
  - **Duplica avisos que `/explore` ya muestra** (soporte puntual, QA, procedencia, estado y datos sintéticos): habría que quitar los de esta rama o agregar al panel opciones para ocultarlos, y reescribir las pruebas que verifican ese texto.
  - **Texto fijo "Murray–Darling"** en el aviso de `point_sample`: aparecería también con otras regiones (por ejemplo `REG01` en la demostración). Conviene corregirlo en el panel antes de usarlo en `/explore`.
  - **Diseño**: trae su propio `h2`, colores fijos (`#2563eb`, etc.) en vez de los tokens del sitio y todo en un solo bloque, mientras que aquí el gráfico va junto al mapa y la tabla debajo.
  - **Conclusión**: la unificación exige tocar el componente de FE-07 (props de selección y de avisos), `ExplorePage` y varias pruebas. No es un cambio chico, así que **queda fuera de esta entrega** y se propone como PR de seguimiento, acordada con César. `/explore` mantiene `TimeSeriesChart` y `SeriesTable`; `ScientificSeriesPanel` sigue sin usarse en la ruta.
- **César**: UX y ciencia (D2, D9, D10), y la decisión de FUL-130 anterior.
- **Alaín**: contrato (sección 7) y el proxy de Vite sin CORS abierto en FastAPI.

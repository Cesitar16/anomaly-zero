# FE-04 · Implementación de `/explore` con mocks tipados y estados científicos verificables

Tarjeta: **FUL-119 / FE-04**. Rama: `feature/ful-119-fe-04-explore-mocks-tipados`, creada desde el último `origin/dev` (con FE-03 y FE-05 ya integradas).

Este documento explica **qué se construyó**, **cómo se ejecuta**, **qué endpoint alimenta qué componente**, **qué estado de FE-03 se ve dónde** y **qué quedó pendiente de revisión**. No define ciencia nueva: la pantalla solo muestra lo que el contrato AZ-04 `0.1-draft` permite mostrar.

## 1. Resumen

- `/explore` es ahora una pantalla real dentro de la app React existente (no hay una app nueva). El marcador de posición anterior se eliminó.
- Toda la pantalla lee datos por **una sola puerta**: la interfaz `ExploreApi`. Hay dos implementaciones:
  - `MockExploreApi` (predeterminada en desarrollo y QA): respuestas **explícitamente sintéticas** que cumplen el OpenAPI.
  - `HttpExploreApi` (separada): cliente `fetch` para una integración futura con FastAPI. No es obligatorio conectarlo a producción en esta tarjeta.
- El mapa (MapLibre GL JS) y el gráfico (Recharts) se cargan de forma diferida junto con la ruta `/explore`. El mapa solo se descarga si existe una capa dibujable.
- Los análisis estadísticos siguen **deshabilitados**: `POST /analyses` se muestra como no disponible.
- Mientras el backend no publique `raster_layers`, el mapa dice con honestidad que no hay capa. No dibuja frames falsos, contorno de cuenca, leyenda científica ni herramientas por píxel.

## 2. Cómo ejecutarlo

Desde `frontend/`:

```bash
npm ci
npm run dev        # http://localhost:5173/explore, con el servicio simulado
npm run lint       # oxlint
npm test           # vitest (183 pruebas)
npm run build      # tsc -b + vite build
```

Para apuntar al backend integrado en `dev` (opcional, solo para comprobar el adaptador HTTP):

```bash
VITE_EXPLORE_API=http VITE_API_BASE_URL=http://localhost:8000/api/v1 npm run dev
```

Sin `VITE_EXPLORE_API=http` se usa siempre el servicio simulado. `VITE_API_BASE_URL` por defecto es `/api/v1`.

### Parámetros de la URL

Los filtros viven en la URL para poder compartir una vista. Se validan como entrada de usuario.

| Parámetro | Ejemplo | Qué hace |
|---|---|---|
| `region` | `REG01` | Región elegida. Si no existe en el catálogo, error en el campo y **no** se consulta la serie |
| `product` | `P02` | Variable NASA elegida (mismo tratamiento) |
| `start`, `end` | `2005-01`, `2005-03` | Rango mensual `AAAA-MM`, hasta 240 meses |
| `month` | `2005-02` | Mes mostrado en el mapa (si hay capas) |
| `demo` | `error-503` | Escenario del servicio simulado (solo existe en modo simulado) |

Vista de referencia: `/explore?region=REG01&product=P02&start=2005-01&end=2005-03`

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

Todas las capturas están en `docs/fe-04/capturas/` en versión escritorio (1280 px) y móvil (390 px), y las generó la aplicación compilada, no un maquetado.

Lo que **no** se puede mostrar como captura: una serie real con `synthetic: false` y valores, porque los valores reales de DS-03 viven en un snapshot local que Git ignora. Lo que sí se comprueba por prueba automática es la parte que importa: con datos reales no aparece el aviso de "sintético" ni los escenarios de demostración.

## 4. Qué endpoint alimenta qué componente

| Endpoint | Componente | Notas |
|---|---|---|
| `GET /regions` | `ExploreFilters` (`RegionSelect`) | Con una sola región, se elige sola |
| `GET /products?region_id=` | `ExploreFilters` (`ProductSelect`) | Los productos `unavailable` se listan con su rótulo y siguen consultables (ver D10) |
| `GET /series` | `TimeSeriesChart`, `SeriesTable`, `MapPanel`, `QualityNotice`, `SupportNotice`, `CoverageSummary`, `SourceProvenance` | `raster_layers` solo alimenta el mapa |
| `POST /analyses` | `AnalysisUnavailable` (`AnalysisStatus`) | Siempre "no disponible". No se llama en modo HTTP |
| `GET /analyses/{id}` | (ninguno) | No existe en `dev`; el simulado responde 404 |

## 5. Qué se conservó del dato (y cómo se verifica)

- **Cero válido**: se dibuja en 0 y la tabla dice "0 (cero válido)".
- **Nulo**: se dibuja como hueco (la línea no se une, `connectNulls={false}`), con una franja ámbar, y la tabla dice "Sin dato". Nulo no es cero.
- **Unidades**: `mm/hr`, rotulado como tasa media mensual. El eje Y parte de 0 solo para `mm/hr`.
- **Soporte puntual**: `point_sample` se avisa como "punto, no área". La cobertura cuenta meses; no mide el área de la región.
- **Calidad**: sin evaluar y "solo controles básicos" se muestran como advertencia, nunca como "aprobada".
- **Errores**: `404`, `422`, `500`, `503` y la falta de red son estados distintos y ninguno se disfraza de "sin datos".
- **Accesibilidad**: el gráfico tiene descripción para lector de pantalla y siempre hay una tabla equivalente; las pruebas corren `axe`. Los textos de error usan `role="alert"`.

## 6. Pruebas

Total: **10 archivos, 183 pruebas** (`src/test/`).

| Archivo | Qué comprueba |
|---|---|
| `explore/contracts.test.ts` | Las fixtures oficiales son idénticas a los ejemplos del OpenAPI; todas las respuestas (fixtures, simulado y capturas reales de `dev`) validan contra los esquemas con Ajv 2020 |
| `explore/lib.test.ts` | Rangos de meses, formato, modelo del gráfico (cero/nulo), resolución del mapa, lectura y escritura de la URL |
| `explore/mockApi.test.ts` | Respuestas del simulado, escenarios, `422` con `details.field`, `409` de análisis, clones sin mutación |
| `explore/httpApi.test.ts` | Cliente HTTP contra las respuestas reales de `dev`, incluida la ruta inexistente (`{"detail":"Not Found"}` se trata como falla de red) |
| `explore/useResource.test.tsx` | Carga, cancelación de peticiones obsoletas |
| `explore/components.test.tsx` | Cada componente, incluida la ausencia honesta del mapa |
| `explore/page.test.tsx` | Pantalla completa: flujos, validación, errores, modo HTTP con respuestas reales, capas de demostración y `axe` |
| `app.test.tsx` | Navegación desde la landing (CTA, barra y pie) |

CI: `Checks` ahora ejecuta `npm test` del frontend antes de compilar (paso "Frontend tests", en un commit aparte).

## 7. Diferencias y observaciones del contrato

1. **`raster_layers`**: el OpenAPI lo define, pero `dev` nunca lo emite. Es la razón de la ausencia honesta del mapa. Los ejemplos con capas (E9, E10) son derivados del esquema, no oficiales.
2. **Campos opcionales**: `dev` los omite en vez de enviarlos `null`. Los tipos del frontend los tratan como opcionales.
3. **Errores**: `details` llega siempre `null` en `dev` (O5). El simulado sí envía `details.field` en `INVALID_PARAMETER`, como el ejemplo oficial.
4. **Rutas inexistentes**: `dev` responde `{"detail":"Not Found"}`, que no es un sobre de error del contrato (O13). El cliente HTTP lo clasifica como "sin respuesta del servicio".
5. **Versión de producto**: `dev` toma `product_version` del snapshot (`V07B`), mientras que `/products` sin snapshot informa la colección `07` (O15). La pantalla muestra lo que llegue.
6. **`/analyses`**: no está en `dev` (BE-05, PR #31, no integrada). Si existiera, la pantalla debería seguir mostrando `ANALYSIS_METHOD_UNAVAILABLE` con honestidad.
7. **Tarjeta vs FE-03**: la tabla antigua de la tarjeta decía "deshabilitar consulta" para productos no disponibles, y FE-03 los deja consultables (para ver el `200 no_data` real). Se siguió FE-03 (D10).

## 8. Decisiones abiertas

| Id | Tema | Qué se hizo | Quién decide |
|---|---|---|---|
| D2 | Textos científicos (calidad, soporte espacial, análisis, "muestra NASA exploratoria") | Quedan como **propuesta** en `content/exploreCopy.ts`, en un solo archivo | César |
| D3 | Librería de mapa y de gráficos | MapLibre GL JS 6.18.0 y Recharts 3.10.1, como **recomendación** de la tarjeta | César (aprobación final) |
| D9 | Marcador del punto de muestra en el mapa sin capa | **No** se dibuja: ausencia honesta, como en los wireframes | César |
| D10 | Productos `unavailable` | Se pueden consultar | César / Alaín |
| Mes | Entrada del mes como texto `AAAA-MM` | Campo de texto con validación, en vez de `<input type="month">` (soporte irregular) | César (UX) |
| CI | Paso de pruebas del frontend en `Checks` | Agregado en un commit aparte, fácil de revertir | Equipo |
| Demo | Botón auxiliar que muestra el `409` | Solo en modo simulado; en modo HTTP no existe y no se llama a `/analyses` | César |

## 9. Tamaño del paquete

| Pieza | Tamaño | Cuándo se descarga |
|---|---|---|
| Entrada de la app | ~283 kB (90 kB gzip) | Siempre |
| Ruta `/explore` (con Recharts) | ~424 kB (124 kB gzip) | Al abrir `/explore` |
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
  components/                filtros, gráfico, tabla, mapa, avisos, procedencia, calidad, errores
frontend/src/test/explore/   pruebas
docs/fe-04/capturas/         capturas escritorio y móvil
```

## 11. Cómo pasar a la integración real

1. Levantar el backend de `dev` y arrancar el frontend con `VITE_EXPLORE_API=http`.
2. Mientras el backend no publique `raster_layers`, el mapa seguirá en ausencia honesta. No hay que tocar la pantalla: cuando lleguen descriptores `available` con su bbox y URL de capa, hay que entregar un `RasterResolver` real al cliente HTTP (hoy devuelve `null` a propósito).
3. Cuando exista `POST /analyses` aprobado, se cambia `capabilities.analyses` del cliente HTTP y se agrega la vista del resultado. Antes de eso, no.

## 12. Revisiones solicitadas

- **César**: UX y ciencia (textos D2, soporte puntual, calidad), aprobación del stack (D3) y de D9/D10.
- **Alaín**: revisión del contrato (sección 7).

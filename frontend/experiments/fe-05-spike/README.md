# Spike FE-05: mapa mensual y gráfico con datos sintéticos

Tarjeta FUL-121 (FE-05). **Experimento descartable y aislado**: no forma parte de la landing, no se despliega y no define el stack final. La decisión de librerías es de César; el análisis y la recomendación están en [`docs/fe-05-evaluacion-mapa-graficos.md`](../../../docs/fe-05-evaluacion-mapa-graficos.md).

> **Todo lo que muestra este spike es sintético.** Ningún frame, valor, polígono o escala es una observación NASA, un promedio de la cuenca Murray-Darling, una anomalía, una tendencia ni un resultado estadístico. Los frames los genera `scripts/generate-frames.mjs` con una fórmula determinista.

## Qué evalúa

- **Mapa:** cambiar de mes sobre un único mapa MapLibre (`ImageSource.updateImage`), sin reconstruirlo y sin mapa base externo.
- **Línea de tiempo controlada:** `selectedMonth` vive en el padre; Anterior, Siguiente, Reproducir/Pausar y slider.
- **Gráfico:** ECharts frente a Recharts con los mismos 12 puntos sintéticos: un cero real, un `null` (hueco) y una calidad desconocida.
- **Ausencia honesta:** un mes sin frame se declara ausente; nunca se reutiliza otra fecha. Una `RasterLayer` con `state: "unavailable"` no produce capa ni peticiones.

## Cómo ejecutarlo

Requiere Node 22 en CI (el repo lo usa). `maplibre-gl@6.18.0` declara una dependencia transitiva que exige Node >= 22; con Node 20.19 `npm install` muestra un aviso `EBADENGINE` pero el spike compila y pasa las pruebas.

```bash
cd frontend/experiments/fe-05-spike
npm install
npm run dev        # http://localhost:5173
npm run lint       # oxlint
npm run test       # vitest (34 pruebas, archivos *.check.*)
npm run build      # tsc --noEmit && vite build
npm run frames     # regenera public/frames y src/data/frames.manifest.json (determinista)
npm run measure    # peso de cada librería, una por una (ver abajo)
```

Scripts opcionales de verificación en navegador real (requieren `playwright` de Python, Chrome y `npm run dev` en marcha). No forman parte de CI:

```bash
python scripts/verify_spike.py http://127.0.0.1:5173         # 15 comprobaciones + capturas
python scripts/measure_runtime.py http://127.0.0.1:5173      # tiempos de cambio de mes y heap
python scripts/probe_chart_a11y.py http://127.0.0.1:5173     # sondeo de teclado y ARIA de ambos gráficos
python scripts/probe_states.py http://127.0.0.1:5173         # error + reintento, respuesta tardía, clic en gráficos
```

Los scripts asumen el puerto que se les pase; ajusta si Vite usa otro.

## Estructura

```
scripts/generate-frames.mjs    generador determinista de frames sintéticos (sin dependencias)
scripts/measure-bundle.mjs     construye cada librería por separado y mide gzip
scripts/verify_spike.py        verificación en Chrome real
scripts/measure_runtime.py     tiempos y memoria
scripts/probe_chart_a11y.py    sondeo de accesibilidad de los gráficos
scripts/probe_states.py        sondeo de estados del mapa (error, reintento, respuesta tardía) y clic en gráficos
measure/*.tsx                  una entrada mínima por librería para medir peso
public/frames/{native,mercator}/2005-0{1,2,3}.png   3 frames de 0.9 KB
src/data/frames.manifest.json  manifiesto (synthetic: true, bbox, escala fija, 12 meses)
src/data/fixtures.ts           serie de 12 puntos y 12 RasterLayer copiadas de la forma del contrato
src/lib/frameTarget.ts         función pura que decide qué mostrar por mes y modo
src/components/                MapPanel, MonthTimeline, RasterLegend, SeriesChart*, SeriesTable, ...
src/test/                      pruebas *.check.*, incluidas las de honestidad (no inventar datos)
```

## Patrones de diseño usados

- **Función pura para la decisión** (`resolveFrameTarget`): la regla "sin descriptor disponible no hay capa ni petición" se prueba sin WebGL.
- **Uniones discriminadas** (`FrameStatus`, `FrameTarget`): los estados imposibles no se pueden representar.
- **Componente controlado** (`MonthTimeline`): el padre es la única fuente de verdad del mes.
- **Estado derivado, no sincronizado con efectos:** el estado visible del mapa se calcula desde `target`, `loaded` y la clave del frame.
- **Validación en el borde** (`parseManifest`): el manifiesto se valida al cargarlo; un dato mal formado falla de forma explícita.
- **Pruebas de honestidad** (`honesty.check.ts`): las reglas de la tarjeta (sintético visible, sin URLs externas, `RasterLayer` alineada con el OpenAPI, polígono que no es LineString) son pruebas que fallan si alguien las rompe.

## Convivencia con la landing

- Tiene su propio `package.json` y `package-lock.json`; no comparte `node_modules` con `frontend/`.
- Solo importa de la landing `src/styles/tokens.css` (tokens de diseño), sin copiarlo.
- Las pruebas se llaman `*.check.*` y no `*.test.*` a propósito: el `vitest run` de `frontend/` usa el patrón por defecto desde su raíz y, con el nombre habitual, recogía estas pruebas (y las rompía por rutas relativas). Así no hace falta tocar `frontend/vite.config.ts`.
- `npm run lint` de `frontend/` también recorre esta carpeta y debe seguir sin avisos. Se comprobó junto con `npm test` y `npm run build` de la landing.

## Límites conocidos

- Mediciones hechas con Chrome headless y WebGL por software (SwiftShader), sin GPU: sirven para comparar entre sí, no como cifras de un dispositivo real.
- No se probó con lector de pantalla real ni en dispositivos físicos.
- El spike no consume el backend ni el contrato en vivo; `RasterLayer` y la serie son fixtures con la misma forma que `docs/openapi-contract-v0.yaml`.
- Cosmético: en móvil, la etiqueta rotada "mes seleccionado" de ECharts puede rozar las marcas del eje Y cuando el mes elegido es el primero.

# Registro de decisiones — Anomaly Zero

> **FUL-99 / estado global:** borrador de arquitectura para revisión de Lucas Moncada, César Rojas y Alaín (Jod). **No aprobado por el equipo.** Fecha de propuesta: 14 de noviembre de 2026.  
> **Uso del documento:** distinguir decisiones técnicas ya implementadas, propuestas aún no ratificadas y asuntos que requieren evidencia real. Este archivo **no** aprueba resultados científicos ni contratos finales de API.

## 1. Decisiones y hechos tecnológicos ya implementados

| ID | Hecho o decisión existente | Evidencia / alcance |
| --- | --- | --- |
| H-01 | Monorepositorio para frontend, backend e investigación | FUL-98; `Cesitar16/anomaly-zero` |
| H-02 | React, TypeScript y Vite para frontend; FastAPI y Python 3.12 para backend | `frontend/`, `backend/app/main.py` y `pyproject.toml` |
| H-03 | Proyecto Python único, administrado con `uv` y lockfile; grupos `dev` y `research` | `pyproject.toml`, `uv.lock` |
| H-04 | Carpetas locales `data/raw/`, `data/processed/` y `data/cache/`; contenido ignorado en Git | `data/README.md` y `.gitignore` |
| H-05 | FastAPI inicial expone `/health` y documentación `/docs` | FUL-98; pruebas iniciales de backend |
| H-06 | EDA puntual NASA POWER `T2M` de Wagga Wagga publicado en `dev` | FUL-101; PR #1 fusionada. **No** es validación científica de Murray–Darling |
| H-07 | Investigación inicial de temperatura de aire, precipitación y humedad de suelo para región candidata Murray–Darling, 2005–2024 | Objetivo de investigación; **productos, cobertura espacial y período no validados con archivos NASA** |

**Nota:** que una carpeta o dependencia exista no implica que su módulo de negocio esté implementado. Los adaptadores Earthdata, agregados espaciales, cálculo inferencial y contratos API de producto siguen pendientes.

## 2. Decisiones propuestas en FUL-99 (pendientes de ratificación)

**Estado de todas las filas de esta sección:** `PROPUESTA`, no `APROBADA`.

| ID | Propuesta y razón | Criterio de aceptación / dueño de validación |
| --- | --- | --- |
| P-01 | **Primera pantalla científica: serie regional y estadísticas.** Reduce el alcance inicial sin descartar un futuro mapa temporal | César define métricas científicas mínimas; Alejandra revisa interacción; aprobación en FUL-107 |
| P-02 | **Primera versión funcional con una variable**, reutilizando interfaz de ingestión/QA para ampliar a tres. No descartar las otras dos, solo secuenciar implementación | Lucas identifica primera variable viable desde fuentes/descarga; César y Alaín verifican complejidad; FUL-104/107 |
| P-03 | **Ingesta y procesamiento fuera del request web; FastAPI sirve snapshots validados.** Evita espera, fallas y credenciales del proveedor en cada consulta React | Alaín confirma procedimientos/snapshot y contrato de lectura; FUL-103/106/108 |
| P-04 | **Conservar original y derivados por separado.** `raw` no se modifica, `processed` contiene series/grillas con versión, `cache` es regenerable | César y Alaín acuerdan escritura y verificación; FUL-99/106 |
| P-05 | **Sin base de datos obligatoria al inicio.** Usar archivos y manifiestos por snapshot hasta medir volumen, concurrencia y latencia | Alaín verifica rendimiento y límites; documentar condición concreta de migración |
| P-06 | **Tabla mensual larga para la interfaz interna de ciencia de datos** (`period`, `variable_id`, `value`, `unit`, `product_id`, `version`, `region_id`, `spatial_support`, `quality_status`, `snapshot_id` y cobertura opcional) | César valida, Lucas revisa semántica, Alaín revisa consumo; no es contrato público FUL-108 |
| P-07 | **Manifiesto obligatorio de procedencia por snapshot.** Granules, producto/versión, fuente pública/DOI, hashes, período, región, unidad, QA, transformaciones y fechas | Lucas + Alaín + César; revisar contra el primer archivo NASA auténtico |
| P-08 | **Notebooks exploratorios y código productivo separados.** Utilidades validadas pasan a funciones Python reutilizables; React nunca recalcula análisis científico | César y Alaín acuerdan ubicación/importaciones; conservar FUL-101 en `research/` hasta que la migración esté justificada |
| P-09 | **Pruebas unitarias offline + comprobaciones reales controladas.** Tests del backend/QA sin red; descarga de muestra autenticada por ejecución explícita | Alaín y César; comprobar sin depender de Earthdata en CI/tests ordinarios |
| P-10 | **Mapa temporal como evolución condicionada a raster auténtico.** Preservar grillas y metadatos mientras el MVP comienza con serie regional | Lucas confirma disponibilidad y geografía; Alejandra revisa UX; FUL-107/109 |
| P-11 | **Estados explícitos para datos/análisis no disponibles.** No representar null o falta de inferencia con cero, ni mostrar snapshot antiguo como recién actualizado | César especifica semántica, Alaín diseña servicio, Alejandra muestra estados; FUL-108 |
| P-12 | **Publicación segura de snapshots.** Datos procesados solo pasan a «último válido» tras QA y escritura completa; no se publica un archivo parcialmente generado | Alaín define mecanismo mínimo y César define validaciones; implementación fuera de FUL-99 |

### Decisiones específicas que César propone

- **MVP orientado a una serie regional:** el valor representado como «región» requiere máscara/polígono y método de agregación científicamente justificado. Hasta tenerlo, solo mostrar una **serie puntual** explícitamente rotulada o «región aún no disponible».
- **No seleccionar una variable por preferencia estética:** escoger la primera según acceso y metadatos verificados de las tres colecciones. Aun usando una sola al principio, el modelo tendrá campos de producto/variable que permitan ampliación.
- **Frecuencia mensual candidata:** mantenerla como interfaz preferida para comparar series, pero conservar períodos y calendarios del productor; conversiones/compatibilidad se validan por fuente.
- **Sin tendencias inferenciales ficticias:** mostrar estadística descriptiva antes de calcular p-values, pendientes y significancia. El método definitivo depende del EDA de FUL-105 y de suficiente historia real.

## 3. Pendientes que NO se resolverán prematuramente en FUL-99

| ID | Pregunta abierta | Dueño propuesto / evidencia requerida | Tarjeta |
| --- | --- | --- | --- |
| O-01 | ¿Qué producto NASA, versión y variable exacta será la primera implementación? | Lucas; fichas GES DISC/CMR y al menos una muestra legible | FUL-104/106/107 |
| O-02 | ¿Qué región/polígono oficial representará el MVP y bajo qué licencia/CRS? | Lucas; geometría oficial comprobada | FUL-102/104/107 |
| O-03 | ¿Cómo convertir unidades y cómo realizar máscara y ponderación espacial por producto? | Lucas + César; atributos reales y prueba geoespacial | FUL-105/106 |
| O-04 | ¿Qué meses tienen datos válidos dentro de la cuenca? | Alaín + Lucas + César; QA sobre grillas auténticas; inventario CMR no basta | FUL-106/105 |
| O-05 | ¿Qué método estadístico, prueba de significancia, tratamiento de autocorrelación y reglas de incertidumbre utilizar? | César; diagnóstico con serie regional suficientemente extensa | FUL-105 y trabajo posterior |
| O-06 | ¿Cuáles serán endpoints, payloads Pydantic y versionamiento del contrato público? | Alaín + César + Alejandra + Lucas; ejemplo con datos reales y mocks | FUL-108 |
| O-07 | ¿Qué librería/mapa/tiles usar y qué capas mostrar por mes? | Lucas y Alejandra; grillas accesibles, tamaño/QA y diseño | FUL-107/109 |
| O-08 | ¿Se requiere base de datos, formato Parquet, CDN, almacenamiento de objetos o scheduler? | Alaín + César; mediciones reales de carga, costo y necesidad | Después de BE-02 |
| O-09 | ¿Con qué frecuencia se actualizarán snapshots y cómo se reporta su frescura? | Alaín + Lucas; latencia y versión de cada fuente | FUL-106/108 |
| O-10 | ¿Qué estrategia de deployment, seguridad pública y hosting usar? | Equipo; requisitos y presupuesto del MVP | Fase posterior |
| O-11 | ¿Qué reglas de ramas, PR, protecciones y CI adoptará el equipo? | Equipo; **deliberadamente pospuestas**; no configurar en FUL-99 | Decisión futura |

## 4. Comparación de alternativas

### Consulta bajo demanda vs procesamiento previo

- **Opción propuesta:** snapshots validados, producidos fuera de la petición web. Proporcionan trazabilidad y reducen dependencia en tiempo real de NASA.
- **Alternativa no elegida provisionalmente:** consultar Earthdata, abrir un granule y calcular tendencias por cada request React. Riesgos de latencia, autenticación y cómputo imprevisible. Reevaluar si surge un caso de exploración dinámica justificado.

### Una variable primero vs tres simultáneamente

- **Opción propuesta:** completar una ruta vertical y extender a tres productos con una interfaz repetible.
- **Alternativa diferida:** exigir tres productos y todos los mapas antes de mostrar cualquier resultado. Riesgo de bloquear el MVP por una sola fuente.

### Snapshots de archivos vs base de datos desde el inicio

- **Opción propuesta:** persistencia local de prototipo con manifests; no se asume que sea la solución de despliegue final.
- **Alternativa pendiente de evidencia:** base de datos o almacén geoespacial para consultas concurrentes, volumen alto, controles de acceso o capas raster. Decidir después de mediciones.

### Serie regional vs mapa temporal desde el inicio

- **Opción propuesta:** priorizar serie mensual regional correcta, con grillas preservadas para el mapa futuro.
- **Alternativa aplazada:** mapa por píxel desde la primera iteración; requiere geometría, raster mensual y estrategias de publicación no demostradas por FUL-101.

## 5. Registro de aprobación y control de cambios

**Revisión del borrador (sin conformidades ficticias):**

| Persona | Rol | Estado | Qué debe revisar |
| --- | --- | --- | --- |
| Lucas Moncada | Responsable FUL-99 / ciencia NASA | **Pendiente** | Productos, estructura, fuentes y polígono |
| Alaín (Jod) | Datos y backend | **Pendiente** | Ingesta, sidecars, publicación de snapshots y FastAPI |
| César Rojas | Data Science / proponente | **Pendiente de revisión del documento final** | Tipos y QA, entradas/salidas y análisis |
| Alejandra Reyes | Frontend | **Consulta posterior** | Estados y alcance UI; la landing no se bloquea |

**Regla:** una propuesta se convierte en **aprobada** solo cuando quede registrada la revisión y acuerdo del equipo; no equivale a que se haya implementado. Las decisiones científicas de región, selección de producto y validez estadística pasan por FUL-107/105.

**Referencias internas:** `docs/architecture.md` (diseño y esquemas provisionales), `docs/datasets.md` (productos candidatos), FUL-99, FUL-101 (piloto), FUL-102/104 (Lucas), FUL-103/106 (Alaín), FUL-105 (César), FUL-107 (puerta científica) y FUL-108 (contratos).

**Referencias de implementación:** [Repositorio](https://github.com/Cesitar16/anomaly-zero) · [NASA GES DISC](https://disc.gsfc.nasa.gov/) · [Earthdata](https://www.earthdata.nasa.gov/) · [NASA POWER](https://power.larc.nasa.gov/).

## 6. Incorporación de evidencias del ZIP de investigación (14-11-2026)

**Documento asociado:** [docs/evidence_inventory_2026-11-14.md](evidence_inventory_2026-11-14.md). Se inspeccionaron archivos del ZIP y se compararon **59/59 hashes** de su manifiesto; el ZIP no se publicó en GitHub. Se registraron datos verificables de **CMR** y de un **polígono MDBA**, diferenciando evidencia histórica de las decisiones científicas pendientes.

| ID | Evidencia nueva (captura 14-11-2026) | Actualiza, pero NO cierra |
| --- | --- | --- |
| E-01 | MERRA-2 `M2TMNXSLV` v5.12.4: `C1276812859-GES_DISC`; **240/240 meses 2005–2024** en el inventario CMR | O-01 y O-04: aún falta descargar y examinar grilla |
| E-02 | IMERG Final `GPM_3IMERGM` v07: `C2723754851-GES_DISC`; **240/240** meses en CMR; en la captura extendida llega hasta septiembre 2025 | O-01/O-04; no completar meses posteriores mezclando versiones |
| E-03 | GLDAS Noah `GLDAS_NOAH025_M` v2.1: `C1342986036-GES_DISC`; **240/240** meses en CMR | O-01 y O-04; aún falta QA de variable y área |
| E-04 | Polígono Murray–Darling EPSG:4326, válido, publicado mediante servicio ArcGIS relacionado con MDBA, licencia CC BY 4.0; Wagga Wagga queda dentro | O-02: candidato geográfico ya disponible, pendiente aceptación de Lucas y revisión de máscara |
| E-05 | Metadata ABS/NSW 2026 del ZIP declara CC BY-SA 4.0; geometría simplificada NSW es para dibujo | O-02/O-07: no emplear como máscara ni confundir territorio/licencia con MDBA |

**Implicación para P-02:** puede priorizarse una prueba inicial de **MERRA-2 T2M** por continuidad con el análisis de temperatura de FUL-101, pero **no** aprobar esa elección ni declararla funcional hasta que FUL-103/106 pueda abrir un granule auténtico y Lucas valide las variables y unidades. La evidencia de 240 meses es de inventario, no de 240 valores de cuenca.

**Siguen pendientes:** EDL/descarga efectiva, lectura NetCDF/HDF5 y atributos, meses/píxeles válidos dentro del polígono, máscara/pesos y calidad regional, inferencia de tendencias, backend de snapshots, contrato público, mapas y revisión formal de Lucas/Alaín. Conservar el estado global de FUL-99 en **In Review**, no Done.


## 7. FUL-99 — Línea base técnica v0.1 para acordar con el equipo (14-11-2026)

**Naturaleza de las decisiones:** César ya eligió como dirección de producto **serie regional primero**, **una variable extensible a tres**, **procesamiento previo por snapshots**. Las especificaciones detalladas aquí son una **propuesta concreta de implementación de esas elecciones**, elaborada para revisión por Lucas y Alaín; **no** constan como aprobadas por los demás integrantes. La línea base define arquitectura, NO la validez científica de un dataset.

### 7.1 Decisiones suficientemente definibles sin descarga de granules

| ID | Decisión técnica propuesta | Regla verificable / alcance |
| --- | --- | --- |
| B-01 | **MVP vertical: MERRA-2 `M2TMNXSLV`/T2M como plan A**, antes de sumar IMERG y GLDAS | Elegido para primera prueba por mensualidad, cobertura CMR de 240 meses y continuidad con FUL-101; **sujeto** a abrir gránulo y QA. Si falla la extracción/QA, revisar alternativa con Lucas; no fabricar serie |
| B-02 | **Región inicial candidata: Murray–Darling** usando GeoJSON MDBA del paquete investigado (EPSG:4326) | Conservar URI/autor/licencia/versionado y **SHA-256 del polígono**, sin tratarlo como máscara QA validada hasta probarlo sobre grilla |
| B-03 | **Ventana de análisis candidata fija: 2005-01 a 2024-12** | 240 períodos mensuales esperados; gránulo en CMR `!=` píxeles/mes válidos. Contar faltantes reales |
| B-04 | **Flujo batch → snapshot → API de solo lectura → React** | El request HTTP no descarga archivos históricos ni recalcula toda la cuenca; acceso NASA falla sin afectar `/health` |
| B-05 | **Un solo conjunto Python con uv** y sin microservicios nuevos | Reutilizar `backend/app/data_sources/`, `backend/app/analysis/`, `backend/app/services/`, `research/` y `docs/` existentes |
| B-06 | **`raw` inmutable, `processed` derivado versionado, `cache` regenerable** | Archivos voluminosos, sidecars, originales y credenciales fuera de Git. No borrar o sobrescribir `raw` sin decisión explícita |
| B-07 | **Tabla larga por período mensual y soporte espacial** | Campos mínimos y semántica de la sección 5 de `architecture.md`. Usar `value=null` para faltantes; `0` se conserva como dato válido donde corresponda |
| B-08 | **Snapshot con manifiesto obligatorio**, hash de entradas y geometría, versión de colección y transformación | Permite reproducir/atribuir datos; no exponer derivados sin QA; publicar `snapshot_id` y `generated_at_utc` |
| B-09 | **Publicación sin estados intermedios visibles** | Crear en área de trabajo temporal; validar archivos y manifiesto; solo después actualizar referencia al último snapshot válido, sin reemplazar versión anterior válida |
| B-10 | **Procesamiento científico exclusivamente en Python reutilizable** | `research` explora; análisis validado pertenece al módulo común. React dibuja, no recalcula pendientes, QA o p-values |
| B-11 | **Primera pantalla: serie mensual y estadística descriptiva** | Fuente, unidad, período, n válidos/esperados, cobertura, fecha del snapshot y advertencias visibles. Tendencias solo si análisis validado existe |
| B-12 | **Mapas espaciales diferidos**, sin descartar raster derivado | No confundir serie agregada de 240 meses con 240 grillas listas para animar |
| B-13 | **Pruebas offline obligatorias en cada frontera**, integración real explícita | Fixtures sintéticos solo en tests; un gránulo autenticado real debe abrirse y auditarse antes de afirmar que funciona producción |
| B-14 | **No incorporar de inicio DB, Redis, workers, nuevos despliegues o endpoints definitivos** | Evaluar solo después de medir archivos y necesidades. Contratos públicos se fijan en FUL-108 |
| B-15 | **No mezclar productos ni versiones para tapar huecos** | En especial: captura CMR IMERG V07 no incluye oct–dic 2025; se usa 2005–2024 como ventana objetivo. Mantener missing explícitos |

### 7.2 Política del primer producto (decisión de secuenciación, no aceptación científica)

**Plan A:** `M2TMNXSLV` v5.12.4, colección `C1276812859-GES_DISC`, variable `T2M`, escala mensual en Murray–Darling. Catálogo ZIP describe temperatura en K, grilla 0.625° lon × 0.5° lat; **atributos reales aún no inspeccionados**. La salida de visualización sugerida es °C **solo cuando unidad fuente esté comprobada y conversión registrada**.

**Plan B:** no se elige todavía un segundo producto; Lucas y Alaín revisarán la causa concreta si MERRA-2 no es viable. NASA POWER FUL-101 se conserva como **demostración puntual rotulada**, no sustituto silencioso de promedio regional.

**Hito mínimo para pasar a implementación regional:** descargar y abrir un gránulo real; identificar coordenadas, ejes, calendario, fill/QA y unidad; comprobar al menos algunas celdas dentro del polígono; producir una agregación documentada del mes de prueba. Luego probar 12 meses, y solo después escalar a 240. Si falla una puerta, el estado queda `not_ready`, no `validated`.

### 7.3 Contrato interno provisional que sí se puede acordar antes de FastAPI

- **Clave de cada serie:** `snapshot_id + variable_id + region_id + spatial_support + period` (debe ser única para una serie regional; múltiples celdas requieren identificador de celda o grilla separada).
- **Período:** texto `YYYY-MM` normalizado, conservando en metadatos el intervalo/convención temporal del producto original. No inferir que distintos promedios mensuales son intercambiables.
- **Valor:** numérico finito o null. Fill, NaN, infinitos y meses ausentes se detectan; el motor no imputa sin decisión científica explícita.
- **Identidad:** colección CMR, shortname, versión, variable, unidades fuente y derivadas, región y procedencia del granule.
- **Espacio:** `point`, `grid_cell`, `polygon_aggregate` obligatorios; un valor puntual nunca se presenta como promedio de cuenca.
- **Calidad:** `valid`, `partial`, `missing`, `rejected`, junto con `coverage_fraction` cuando sea aplicable (0–1). Los umbrales que separan válido/parcial quedan para QA real.
- **Análisis:** `not_computed`, `insufficient_data`, `completed` o `error`; método, pendiente, incertidumbre, p-value y diagnósticos **opcionales** según evidencia, nunca rellenados artificialmente.
- **Tiempo de publicación:** `generated_at_utc`, `source_retrieved_at_utc`, `snapshot_id` y fecha del último mes para que el usuario distinga actualización técnica de período cubierto.
- **Fallas:** error de NASA no corrompe ni borra `last_valid_snapshot`; ausencia de snapshot debe indicar `data_unavailable`, no devolver cero ni mostrar el piloto como cuenca.

Los **nombres exactos en Pydantic, endpoints, códigos HTTP, rutas públicas y formatos finales** se decidirán en FUL-108. Aquí se define semántica compartida para que ninguna área trabaje a ciegas.

### 7.4 Umbral de aprobación de la arquitectura vs. validación de datos

**FUL-99 puede cerrarse sin extracción real** cuando Lucas, César y Alaín ratifiquen B-01–B-15, o documenten disensos/ajustes, y concuerden en las interfaces. La extracción y validación de granules son dependencias de **FUL-103/104/106/105**, no prerequisito para aprobar un diseño provisional. No es aceptable marcar la variable inicial como "científicamente validada" o publicar promedios/p-values sin esas pruebas.

**Pendientes genuinamente dependientes de datos:** máscara espacial y regla definitiva de ponderación (área efectiva), tasa/acumulado y unidades de cada producto, tolerancia de cobertura, missing reales, método inferencial, almacenamiento/raster final y viabilidad de descarga autenticada. Todos tienen dueño y tarjeta en las secciones anteriores.


## 8. Respuestas propuestas a las tres confirmaciones de FUL-99 (14-11-2026)

**Estado: RECOMENDACIÓN TÉCNICA DEL BORRADOR; faltan conformidades de Lucas y Alaín.** Las tres preguntas de revisión reciben una respuesta explícita para reducir discusiones abiertas, pero no se convierten automáticamente en decisiones del equipo.

### R-01 — Lucas: ¿MERRA-2/T2M y polígono MDBA?

**Respuesta propuesta: SÍ, como Plan A y geometría candidata del prototipo.**
- **Producto:** MERRA-2 `M2TMNXSLV` v5.12.4, CMR `C1276812859-GES_DISC`, variable `T2M`, frecuencia mensual; NASA lo documenta como reanálisis de media mensual con resolución nominal 0,5° × 0,625°. Fuente oficial: https://data.nasa.gov/dataset/merra-2-tavgm-2d-slv-nx-2dmonthly-meantime-averagedsingle-levelassimilationsingle-level-di-892ac .
- **Área:** polígono Murray–Darling del servicio MDBA guardado en el ZIP (EPSG:4326, fuente/licencia consignadas en el inventario de evidencias). **No** usar el contorno NSW simplificado ni asumir que una intersección CMR valida la cuenca.
- **Tiempo:** enero 2005–diciembre 2024; las respuestas CMR del ZIP tienen 240 entradas mensuales. Esto acredita inventario, no calidad espacial ni meses de serie regional.
- **Primera entrega:** media mensual regional científicamente definida, no promedio de una estación ni de todos los píxeles sin máscara; mostrar cobertura de área, fuente y unidad. Conservar grillas para mapa futuro.
- **Puerta obligatoria:** antes de declarar el producto viable, abrir 1 gránulo auténtico y comprobar `T2M`, dimensiones, unidad, calendario, fill values, píxeles válidos dentro del polígono, posibles celdas parcialmente superpuestas y ponderación defendible. Documentar las decisiones; si falla, revisar Plan B con Lucas. **No validar método espacial sin ese archivo**.

### R-02 — Alaín: ¿batch, manifiestos y snapshots sobre carpetas existentes?

**Respuesta propuesta: SÍ, para un MVP local, con tres reglas de protección.**
1. **Persistencia:** `data/raw/<producto>/<versión>/` conserva descargas originales con hashes; `data/processed/snapshots/<snapshot_id>/` contiene resultados derivados, QA y manifiesto; `data/cache/` es recuperable. No subir datos pesados/credenciales a Git. No crear DB ni colas ahora.
2. **Publicación:** producir el snapshot fuera del request web; validar consistencia de `series.csv`, `manifest.json` y `qa_summary.json`; publicar una referencia lógica al **último válido** solo cuando finalicen todos los archivos. No mostrar resultados incompletos; errores de NASA no bloquean `/health` ni borran snapshots previos.
3. **Consumo:** FastAPI lee snapshots y metadatos de forma acotada y sirve series y estados; React presenta la fuente, período, cobertura, unidad y fecha de generación. El formato externo/endpoints pertenecen a FUL-108.

**Condición de ingeniería:** verificar con 1 gránulo real tamaño, latencia y consumo de RAM/disco; reevaluar almacenamiento si las métricas lo justifican. La propuesta de rutas es una convención local, no infraestructura desplegada.

### R-03 — César: ¿campos suficientes para un EDA regional trazable?

**Respuesta propuesta: SÍ, si se conserva la tabla mínima y se amplía el manifiesto de calidad.** El esquema de serie en `architecture.md` contiene `period` (`YYYY-MM`), `variable_id`, `value` (numérico finito/null), `unit`, `product_id`, `product_version`, `region_id`, `spatial_support`, `quality_status` y `snapshot_id`. Para resultados de **cuenca**, exigir además `coverage_fraction` (área válida/área nominal de la máscara, documentando denominador). Para punto o grilla, puede ser nulo. El total y número de celdas válidas, así como la cobertura temporal cuando aplique, son diagnósticos y no sustituyen cobertura de área.

**Datos obligatorios del manifiesto:**
- Dataset/versión, IDs y SHA-256 de granules, fecha UTC de extracción y proceso; `snapshot_id` e identificador/revisión del código.
- Polígono con fuente, CRS y hash; máscara/pesos, método de agregación, y tratamiento de celdas de borde y píxeles faltantes.
- Unidad original/derivada y transformación exacta con fórmula/convención de tiempo; nombre de variable, `_FillValue`, flags QA y decisiones sobre filtrado.
- Meses esperados, recibidos, válidos, faltantes y repetidos; cobertura espacial por mes, conteos y advertencias de calidad.
- Separar `raw`, serie agregada, raster derivado y análisis inferencial; no etiquetar un dato puntual como `polygon_aggregate`.

**Política:** el cero es válido si lo es para la variable; ausencia se expresa mediante null/estado. Un mes sin mediciones utilizables no se interpola automáticamente. Los umbrales para `valid`/`partial` y los métodos de pesos quedan **sin fijar** hasta abrir gránulos y acordar QA en FUL-104/105/106. Tendencias/p-values e intervalos solo cuando el método sea evaluado y aprobado.

### R-04 — Qué falta de FUL-99 para pasar de Draft a acuerdo de equipo

No se necesita extraer 240 archivos para aprobar esta arquitectura. Basta con que:
- **Lucas** responda «acepto R-01 como plan inicial» o indique una objeción fundamentada; no exige declarar datos científicos listos.
- **Alaín** confirme R-02 o identifique límites concretos del patrón en su implementación.
- **César** revise R-03 y registre conformidad con el formato interno y controles obligatorios.
- Se documenten los cambios/discordancias en esta PR; las decisiones pendientes de archivos quedan explícitamente transferidas a FUL-103/104/105/106/107 y los endpoints externos a FUL-108.

**No marcar FUL-99 Done ni fusionar esta PR como consenso hasta tener constancia de las tres revisiones.**

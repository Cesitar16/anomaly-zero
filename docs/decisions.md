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

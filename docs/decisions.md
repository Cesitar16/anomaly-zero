# Registro breve de decisiones y preguntas — FUL-99

Este registro distingue hechos del repositorio de decisiones del equipo. **Implementado no significa aprobación científica.** No se registran conformidades de Lucas, Alaín o el equipo si no existe una revisión o acta que las respalde.

## Hechos comprobados en `dev`

| Hecho técnico | Evidencia |
| --- | --- |
| Monorepo React/TypeScript/Vite y Python/FastAPI con un `pyproject.toml` raíz | `README.md`, `frontend/`, `backend/`, `pyproject.toml` |
| `GET /health` es el único endpoint API actual | `backend/app/main.py`; `api/`, `services/`, `schemas/` no tienen implementación |
| En `dev`, Earthdata Probe descubre tres colecciones CMR y descarga solo un granulo mensual GLDAS con límites, manifiesto y hash | `backend/app/data_sources/earthdata_probe.py`, `backend/tests/test_earthdata_probe.py`, `docs/earthdata-probe.md`; la extensión de muestras para MERRA-2/IMERG está en PR #9 Draft y aún no está integrada |
| Investigación contiene piloto POWER puntual, QA GLDAS y ensayos de catálogo/región | `research/`, `docs/eda-gldas-preliminar.md`, `docs/contraste_fuentes.md`, `docs/region_murray_darling.md` |
| Originales NASA y resultados personales permanecen fuera de Git | `.gitignore`; `data/raw/**`, `data/cache/**` |

## Registro de decisiones

| ID | Decisión o pregunta | Estado | Motivo y evidencia | Quién debe validar | Tarjeta |
| --- | --- | --- | --- | --- | --- |
| AZD-01 | Conservar temperatura, precipitación y humedad del suelo como terna candidata y 2005–2024 como ventana objetivo | Provisional; no aprobación del MVP | Catálogo CMR para 240 meses por colección; cobertura válida regional y calidad integral no probadas | Lucas + equipo | FUL-102, FUL-107 |
| AZD-02 | Priorizar un primer recorrido técnico de una fuente sin eliminar las otras dos del alcance | Pendiente | PR #9 documenta una muestra auténtica por producto y QA espacial de una fecha, pero está sin merge/revisión; la elección científica depende de calidad, geometría y serie real | Lucas, Alaín, César | FUL-104, FUL-106, FUL-107 |
| AZD-03 | Mantener archivos originales y manifiestos locales; evaluar derivados versionados/snapshots reproducibles | Parte implementada / parte propuesta | FUL-103 publica muestra y manifest en `data/raw` local, ignorado por Git; no existe proceso de snapshots | Alaín + César | FUL-106, FUL-108 |
| AZD-04 | Usar Murray–Darling como región candidata, sin afirmar todavía un agregado oficial de cuenca | Pendiente | Fuente MDBA y ensayos de borde están documentados; el segmento versionado no es polígono y no hay serie regional aprobada | Lucas | FUL-104, FUL-107 |
| AZD-05 | No aceptar aún un método de máscara, ponderación, umbral QA o conversión común para los tres productos | Pendiente | Hay atributos y ensayos parciales específicos por producto; GLDAS solo tiene un mes de EDA rectangular y linaje por revisar | Lucas + César | FUL-104, FUL-105, FUL-106 |
| AZD-06 | Mantener lectura vía API como diseño futuro; no descargar NASA durante una petición y no prometer endpoints de series/tendencias | Provisional | Hoy FastAPI ofrece únicamente `/health`; snapshots y servicios de datos no existen | Alaín + equipo | FUL-99, FUL-108 |
| AZD-07 | Preservar en contratos futuros fuente, periodo, unidad, región, método, cobertura, calidad, incertidumbre y nulos explícitos | Pendiente de contrato | Campos necesarios para no perder semántica; no son aún un schema aprobado | Alaín + César + Lucas | FUL-108 |
| AZD-08 | Definir análisis de tendencias solo tras validar serie temporal, faltantes y método inferencial | Pendiente | No hay serie regional de 240 meses ni motor analítico productivo | César + Lucas | FUL-105, FUL-107 |

## Propuestas que requieren revisión

1. Procesar datos fuera del ciclo HTTP y hacer que un servicio futuro lea snapshots ya verificados.
2. Versionar cada derivado con hash, producto, variable, calendario, unidad, geometría/CRS, método, cobertura y estado de calidad.
3. Mantener los tres productos en el alcance de investigación aunque se elija un primer vertical slice técnico.
4. Representar datos o métricas no disponibles mediante estado y `null`; cero debe conservar su significado observado.

Estas propuestas proceden en parte de la PR #2 cerrada, pero no se trasladan como decisiones aprobadas. La PR #2 terminó con `base_ref_deleted`, sin merge ni reviews; la actualización vigente es el borrador conciso de [architecture.md](architecture.md).

## Preguntas para FUL-107 y revisores

- ¿Qué fuente puede sustentar primero una demostración y cuál es el nivel de afirmación permitido: píxel, rectángulo, cuenca o punto?
- ¿Qué evidencias faltan para pasar de inventario CMR a serie regional validada?
- ¿Qué regla de calidad, máscara, ponderación y calendario se aprobará por producto?
- ¿FUL-105 mantiene su alcance original (recomendación de este borrador: reabrirla a In Progress para completar MERRA-2, IMERG y metodología) o se decide conservarla Done con sucesora explícita? La decisión corresponde al equipo y no se modifica aquí.
- ¿Qué metadatos y estados debe fijar FUL-108 después de la decisión científica?

# Registro de decisiones y preguntas — FUL-99 / AZ-03

Este registro distingue hechos del repositorio de decisiones del equipo. **Implementado no significa aprobación científica.** No se registran conformidades de Lucas, Alaín o el equipo si no existe una revisión o acta que las respalde.

## Hechos comprobados en `dev`

| Hecho técnico | Evidencia |
| --- | --- |
| Monorepo React/TypeScript/Vite y Python/FastAPI con un `pyproject.toml` raíz | `README.md`, `frontend/`, `backend/`, `pyproject.toml` |
| `GET /health` es el único endpoint API actual | `backend/app/main.py`; `api/`, `services/`, `schemas/` no tienen implementación |
| En `dev`, Earthdata Probe descubre tres colecciones CMR; BE-02 proporciona muestras/manifiestos para GLDAS, MERRA-2 y los doce meses IMERG de 2005, distribuidos como Release y fuera de Git | `backend/app/data_sources/earthdata_probe.py`, `backend/app/data_sources/earthdata_samples.py`, `docs/be-02-sample-workflow.md`, Release `be02-samples-2005-v1`, PR #9 integrada |
| El notebook FUL-105 contiene EDA global de muestras nativas y diagnóstico temporal descriptivo IMERG 2005; la auditoría FUL-104 compara métodos espaciales en enero 2005/2021 | `research/notebooks/02_eda_nasa_products.ipynb`, `docs/ful-105-plan-inferencia.md`, PR #11, #14 y #15 integradas |
| Originales NASA y resultados personales permanecen fuera de Git | `.gitignore`; `data/raw/**`, `data/cache/**` |

## Registro de decisiones

| ID | Decisión o pregunta | Estado | Motivo y evidencia | Quién debe validar | Tarjeta |
| --- | --- | --- | --- | --- | --- |
| AZD-01 | Conservar temperatura, precipitación y humedad del suelo como terna candidata y 2005–2024 como ventana objetivo | Provisional; no aprobación del MVP | Catálogo CMR para 240 meses por colección; cobertura válida regional y calidad integral no probadas | Lucas + equipo | FUL-102, FUL-107 |
| AZD-02 | Priorizar un primer recorrido técnico de una fuente sin eliminar las otras dos del alcance | Pendiente | PR #9 integrada; Release BE-02 contiene muestras/manifiestos y FUL-104/105 aporta inspección y QA descriptiva acotada. Ningún producto tiene todavía serie regional aprobada | Lucas, Alaín, César, equipo | FUL-104, FUL-106, FUL-107 |
| AZD-03 | Mantener archivos originales y manifiestos locales; evaluar derivados versionados/snapshots reproducibles | Parte implementada / parte propuesta | FUL-103 publica muestra y manifest en `data/raw` local, ignorado por Git; no existe proceso de snapshots | Alaín + César | FUL-106, FUL-108 |
| AZD-04 | Usar Murray–Darling como región candidata, sin afirmar todavía un agregado oficial de cuenca | Pendiente | Fuente MDBA y ensayos de borde están documentados; el segmento versionado no es polígono y no hay serie regional aprobada | Lucas | FUL-104, FUL-107 |
| AZD-05 | No aceptar aún un método de máscara, ponderación, umbral QA o conversión común para los tres productos | Pendiente | FUL-104 compara centros, intersección y fracción de área en dos fechas; FUL-105 conserva selección por centro descriptiva. GLDAS 2005 tiene linaje de máscara de agua indeterminado | Lucas + César | FUL-104, FUL-105, FUL-106 |
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
- FUL-105 PR #11 está integrada y su EDA/QA exploratorio consta en `dev`; confirmar en Linear su estado de tarjeta y decidir aparte si se requiere trabajo sucesor de serie histórica. Esta propuesta no reabre ni altera FUL-105.
- ¿Qué metadatos y estados debe fijar FUL-108 después de la decisión científica?

## AZ-03 — Definición del alcance científico inicial de Anomaly Zero

**Estado del registro:** propuesta de César para discusión; decisiones no aprobadas. FUL-110 (Lucas), revisión de Alaín y acuerdo explícito del equipo siguen pendientes. Fecha de corte de repositorio: `origin/dev` `b51ca0617a96d582e0239d661c00647da2a32e11` (15-11-2026).

### Contexto y pregunta

El MVP necesita un caso entendible que permita mostrar observaciones de sistemas terrestres con procedencia y límites visibles, sin confundir una muestra con una media de cuenca ni una serie de catálogo con una serie procesada. Pregunta propuesta: **¿Cómo varían descriptivamente, en el tiempo, la temperatura del aire a 2 m, la tasa de precipitación y el agua modelada en los primeros 10 cm del suelo en la cuenca Murray–Darling, y qué cobertura y calidad respaldan cada observación?** Es una pregunta descriptiva y no causal. Su versión inferencial solo se habilitaría después de superar los gates R y T.

### Evidencias consolidadas

- FUL-104, FUL-105 y FUL-106 están integradas en `dev` (PR #14, #15, #11 y #9, respectivamente). FUL-104 reporta muestras originales de enero de 2005 y 2021 para comparar métodos; FUL-106 empaqueta muestras/manifiestos verificables y geometría; FUL-105 reporta EDA de grillas nativas y doce meses IMERG de 2005.
- CMR inventarió 240 meses 2005-01–2024-12 por colección en un bbox; esto no prueba descargas, apertura, QA ni cobertura de la cuenca para 240 meses.
- En enero de 2005, la selección exploratoria por centros reportó MERRA-2 323/323 válidos, IMERG 10.092/10.092, GLDAS 1.615/1.617 (dos faltantes). “Válido” significa finito y distinto del fill, sin filtros QA de productor.
- Para centros frente a fracción de área, FUL-104 reportó en enero 2005 IMERG 0,037816 vs 0,037790 mm/h; MERRA-2 299,606 vs 299,730 K; GLDAS 15,904 vs 15,945 kg/m². Son sensibilidades de muestra, no reglas aprobadas.
- FUL-105 analizó grillas globales de muestras (GLDAS/MERRA-2 enero; IMERG 2005) y una caja rectangular GLDAS previa. La media descriptiva de 10.092 centros y el panel IMERG de 20 puntos no equivalen a media de área ni son muestras independientes de superficie.
- GLDAS enero 2005 declara `history` 2019-10-31 frente a enero 2021 2021-04-23. No se pudo determinar si el archivo de 2005 recibió el posprocesamiento posterior de máscara de aguas interiores.
- La versión de colección IMERG se reporta como `07` y el archivo como `V07B`; los QA `precipitationQualityIndex` y `randomError` están identificados, pero no filtrados.
- Geometría MDBA: Polygon en EPSG:4326, hash documentado en FUL-105; se debe preservar procedencia/licencia y revisar la ruta de acceso reproducible. El fragmento LineString que vive en repo no es una máscara.
- El backend solo ofrece `/health`; no hay API de series, snapshot científico ni motor de tendencias. La PR #13 de FUL-108 permanece abierta y su contrato es provisional.

### Alternativas consideradas (recomendación, no aprobación)

| Alternativa | Ventaja para un primer recorrido | Riesgo / límite | Recomendación propuesta |
| --- | --- | --- | --- |
| MERRA-2 `T2M`, aire a 2 m | Coincide con la variable física temperatura del aire; mensual, grilla 0,5° × 0,625°, muestra original inspeccionada | Reanálisis; NASA original/QA completo y regla regional necesitan revisión; resolución más gruesa | Candidato para primera serie de temperatura si Lucas valida semántica/QA y se supera Gate R |
| IMERG Final `precipitation` | Grilla mensual 0,1° y doce meses 2005 ya abiertos; mayor detalle para demo de un raster de muestra | Es tasa mm/h, no acumulado; QA no aplicado; V07B/07 debe concordar; valores finitos no bastan | Candidato operativo a demo raster etiquetada, no producto regional aprobado |
| GLDAS Noah `SoilMoi0_10cm_inst` | Muestra auténtica y EDA ya reproducible; mensual, 0,25°, profundidad 0–10 cm | Agua modelada; linaje de máscara en 2005 indeterminado; dos faltantes entre centros y QA de serie pendiente | Mantener en evaluación y demo técnica controlada; no priorizar como serie aprobada hasta resolver linaje |

No son intercambiables ni tres observaciones independientes: los productos representan cantidades distintas, usan grillas diferentes y pueden compartir información/forzantes. Recomendación provisional para discusión: **usar IMERG para una demo raster de una muestra** y **mantener MERRA-2 T2M como candidato de primer vertical slice temporal**, sujeto a FUL-110; GLDAS sigue como tercera variable candidata, sujeto al linaje. No se establece ranking científico definitivo.

### Registro de decisiones AZ-03

| ID | Pregunta | Opciones | Evidencia | Recomendación | Riesgos | Prueba pendiente | Responsable (recomienda / aprueba) | Estado | Justificación |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AZ03-D01 | Región inicial | Murray–Darling; subregión administrativa NSW | Polígono MDBA completo y objetivo de cuenca; NSW no es control independiente | Murray–Darling como región candidata | Bordes, datum, licencia, máscara y diferencias de grilla | Confirmar fuente/licencia/CRS/hash y comparar soporte espacial | César / Lucas + equipo | Proposed | Coincide con objetivo hidroclimático; no usar NSW como control causal |
| AZ03-D02 | Primera variable de demo | MERRA-2 T2M; IMERG precipitación; GLDAS humedad superficial | Gránulos reales; IMERG doce meses en 2005, MERRA/GLDAS muestras; FUL-105/106 | IMERG para mapa raster de muestra; advertir tasa/unidad y QA pendiente | El mapa podría interpretarse como superficie validada | FUL-110 revisa QA, bordes, variables y V07B | César / Lucas + equipo | Proposed | Mayor detalle espacial disponible, pero solo como demo claramente acotada |
| AZ03-D03 | Candidato a primera serie | T2M; precipitación; GLDAS; posponer | Solo ventanas parciales inspeccionadas; método/QA pendientes | T2M como candidato condicional, sin declararlo aprobado | Reanálisis y validación QA incompleta; poca cobertura procesada | Validar NASA original, QA, calendario, cobertura y sensibilidad | César / Lucas + equipo | Proposed | Variable físicamente clara; no equivale a independencia observacional |
| AZ03-D04 | Productos incluidos | Terna; selección única | Colecciones/DOI y muestras existen para tres variables distintas | Mantener los tres en investigación; implementar por etapas | Comparabilidad espuria por unidades, resolución o forzantes | Hacer análisis específico por producto; declarar no equivalencia | César / equipo | Proposed | Seleccionar una primera ruta no elimina alcance científico de las otras |
| AZ03-D05 | Ventana temporal | Enero 2005–diciembre 2024 mensual; ventana más corta | 240 meses CMR por colección; gránulos efectivos solo para los períodos señalados en evidencia | Conservar 2005-01–2024-12 como objetivo sujeto a QA | Confundir inventario CMR con observaciones válidas | Inventario de archivos/manifests, duplicados, meses y QA por producto | Alaín + César / Lucas + equipo | Proposed | La ventana es objetivo, no serie actualmente disponible |
| AZ03-D06 | Método espacial | Centro; intersección; fracción de área | Comparación FUL-104 de muestra 2005/2021; métricas pequeñas pero cercanas | No elegir todavía; fracción de área es candidata a evaluar | Geometría y denominadores distintos; bordes y faltantes | Lucas completa comparación por producto/fecha; evaluar conservación/sensibilidad | César / Lucas + equipo | Pending | El cálculo de muestra no resuelve el método operativo |
| AZ03-D07 | QA | Solo fill/finite; reglas por proveedor; excluir por umbral | FUL-105/106 distinguen fill de QA; flags IMERG no aplicados | No fijar umbrales comunes; preservar flags y versionar reglas por producto | Valores válidos pueden ser científicamente deficientes; sesgo de selección | Lucas interpreta documentación y cuantifica impacto de cada regla | Lucas + César / equipo | Pending | No hay criterio/umbral justificado aprobado |
| AZ03-D08 | Faltantes | Mes completo con null; umbral de cobertura; interpolación | GLDAS dos faltantes entre centros en enero; no hay serie de cuenca | Registrar faltantes y denominador; no interpolar en demo | Cobertura variable sesga serie y mapas | Acordar reglas por producto y sensibilidad en meses/área | César + Lucas / equipo | Proposed | Sin imputación explícita no se oculta falta de observación |
| AZ03-D09 | Primera visualización | Ficha/píxel; raster; promedio regional; tendencia | Muestras reales y grillas; no hay serie regional ni inferencia | Ficha de granule y raster global/nativo con fecha, unidad y QA state; no promedio regional | Usuarios pueden leer la muestra como conclusión de cuenca | UX revisa advertencias, soporte, faltantes y leyenda | César / Alejandra + equipo | Proposed | El soporte del dato debe permanecer visible |
| AZ03-D10 | Mapas raster | Grilla original; remuestreo; choropleth regional | Grillas de distintas resoluciones y CRS/metadatos variables | Solo mapa de muestra original con fuente y fecha; mapas derivados pendientes | Remuestreo y máscara pueden alterar señal | Revisar grilla/CRS, QA, geometría y conservación | Lucas + Alaín / equipo | Proposed | No hay pipeline espacial validado |
| AZ03-D11 | Inferencia | Ninguna; OLS-HAC; Theil–Sen/estacional MK; alternativas | Plan FUL-105 enumera candidatos y supuestos; no existen 240 valores regionales | No escoger método aún; Gate T tras serie aprobada y protocolo prerregistrado | Autocorrelación, estacionalidad, rupturas, multiplicidad | Simulación/validación, autocorrelación, sensibilidad e incertidumbre | César + Lucas / equipo | Pending | Evita p-values y pendientes ficticios |
| AZ03-D12 | Contrato FUL-108 | Campos mínimos de procedencia/QA/soporte; schema actual PR #13 | PR #13 tiene states, coverage, quality, soporte espacial y métricas nullables | Usar criterios científicos abajo para revisar PR; no aprobar contrato | `approved` podría ser afirmado sin referencia de autorización; confusión null/cero | Alinear vocabulario y vincular evidencia/approval reference al gate | Alaín / César + Lucas + Alejandra | Pending | El contrato es propuesta técnica, no aprobación científica |

### Gates de publicación

| Gate | Propósito y entradas | Comprobaciones obligatorias / evidencia | Riesgo si se publica antes | Responsable | Estado actual y criterio de aprobación |
| --- | --- | --- | --- | --- | --- |
| D — Demo exploratoria | Mostrar un granule/mes NASA real; original, manifest, producto, variable, DOI, versión, unidad, timestamp, resolución y soporte | Verificar SHA/tamaño/manifest; variable y atributos de unidad/calendario; máscara y CRS si hay polígono; contar total/finito/fill; mostrar QA `unassessed` o reglas ejecutadas; etiquetar ámbito/global/centro/punto, fecha, faltantes y advertencia “muestra, no tendencia ni media validada de cuenca” | Sobreinterpretación como cobertura o tendencia | Alaín reproduce provenance; César contenido; Alejandra advertencia UI | **Parcial**: artefactos existen. Aprobar demo cuando cada campo citado y denominador se reproduce y la advertencia se ve en pantalla/caption |
| R — Serie regional | Granules/manifests del intervalo aprobado, geometría versionada y reglas de QA/espacio | Exactamente un registro por producto-mes esperado; auditar faltantes/duplicados; verificar identidad/versiones/unidades/calendario y QA en raw; máscara CRS/licencia/hash; comparar cobertura válida con denominador de área/celdas según método; ejecutar método aprobado reproduciblemente; sensibilidad a faltantes y al menos fechas representativas; revisión independiente de resultados | Serie sesgada por máscaras, huecos o cambio de producto | Alaín ingesta/procedencia; Lucas ciencia; César agregación independiente | **No superado**. Aprobar solo con calendario aceptado, trazas por mes, reglas/método documentados, prueba repetible y firmas/referencias de revisión |
| T — Tendencia | Serie R aprobada y protocolo temporal | Confirmar ventana y unidades; autocorrelación/estacionalidad; faltantes y sensibilidad; homogeneidad/rupturas; método, hipótesis y unidad de pendiente; IC, p-value si aplicable, multiplicidad cuando varias regiones/productos; falsos positivos y diagnóstico residual; análisis reproducible y revisión independiente | Falsa significancia o causalidad; cambio de producto confundido con clima | César + Lucas; revisión de equipo | **No superado**. Aprobar con protocolo congelado, todos los diagnósticos reportados, incertidumbre y limitaciones, reproducibilidad y revisión; sin inferencia con muestras parciales |
| M — Mapas | Grillas por fecha con atributos intactos, reglas QA, CRS y geometría | Verificar orientación/ejes, antimeridiano/bordes, transformación CRS, reproyección/resampling conservador adecuado a la variable, escala/leyenda/unidad y nodata; máscara y versión; para anomalía, baseline temporal validado; para significancia espacial, corrección por multiplicidad/autocorrelación y soporte de datos | Artefactos visuales o significancia espuria | Lucas geodatos/ciencia; Alaín pipeline; Alejandra presentación | **Solo demo nativa global posible**. Mapa regional requiere Gate R; anomalía requiere baseline; significancia requiere Gate T + control espacial/multiplicidad |

### Propuesta de backlog (sin crear tarjetas)

| Futuro trabajo | Entregable y aceptación propuesta | Dependencias | Responsable sugerido | Riesgo principal |
| --- | --- | --- | --- | --- |
| Ingesta histórica mensual de tres productos | Inventario local con 240 estados por producto; manifests/hash, idempotencia y reporte de meses ausentes | Credenciales/licencias, acceso y aprobación del caso | Alaín | Catálogo disponible no implica descarga íntegra |
| Validación QA por producto/mes | Especificación reproducible de fill, flags y umbrales, con conteos antes/después y sensibilidad | FUL-110 y documentos de productor | Lucas + César | Umbral arbitrario o sesgo temporal |
| Normalización y geometría | Snapshots versionados, CRS/geometría/hash y pruebas de límites/resolución | Decisión AZ03-D01/D06 | Alaín + Lucas | Diferencias de soporte alteran agregados |
| Series regionales | Tabla mensual reproducible con valor/cobertura/estado/null y procedencia | Gates R, FUL-108 contrato acordado | Data Science + Backend | Meses incompletos ocultos |
| Versionado de datos | Manifest/snapshot inmutable y pipeline reproducible identificado por commit | Diseño backend/almacenamiento | Alaín | Reprocesado no reproducible |
| Motor estadístico | Pendiente, IC, p-value/método nullable y diagnósticos con protocolo | Serie R, Gate T | César + Lucas | Inferencia inválida o no comunicable |
| Validación de tendencias | Pruebas simuladas, sensibilidad, validación temporal/independiente y reporte | Motor estadístico | César + Lucas | Falsos positivos y rupturas |
| Raster/mapas temporales | COG/tiles o mecanismo acordado, QA espacial y leyenda/procedencia | Gates R/M, raster storage | Alaín + Alejandra + Lucas | Visualización implica precisión no soportada |

### Transferencia y condiciones para reconsiderar

- **A FUL-110/Lucas:** revisar variable/QA por producto, prioridad, método centro/intersección/fracción, linaje GLDAS 2005, CRS/geometría y viabilidad de raster. Esta propuesta no sustituye su investigación ni edita `docs/apoyo-cientifico-az03.md`.
- **A FUL-108/Alaín:** el payload debe conservar product/collection/DOI/version, variable/unidad nativa, periodo/calendario, geometry/CRS/hash, spatial support + approval state/reference, denominador/coverage, faltantes, flags y reglas QA, transformations, snapshot/provenance y method/metrics nullable. `0` es valor; `null` es desconocido/no disponible. La PR #13 ya modela `available/available_with_gaps/no_data`, coverage, quality, transformaciones y tipos de soporte; alinear sus enums `unassessed`/`descriptive_only`/`approved` con Gates D/R y no permitir `approved` sin referencia verificable. Esto es revisión de compatibilidad, no cambio ni aprobación de PR #13.
- **A Alejandra:** estados UI propuestos: `available`, `partial`, `no_data`; QA `unassessed`, `partial`, `passed`, `failed` (solo si el pipeline define criterios); análisis `not_available`, `pending`, `complete`; soporte `point_sample`, `descriptive_mean`, `regional_aggregate` con etiqueta de aprobación. Mostrar unidad, fecha, fuente, denominador/cobertura, fuente/versiones y limitación junto al dato. No tratar ausencia como cero.
- Reconsiderar propuestas si FUL-110 aporta evidencia contradictoria, si no se puede reproducir un producto/geométrico/periodo, si cambia la versión o definición del dataset, o si el equipo selecciona otro fenómeno/región. Reabrir las decisiones afectadas y guardar la razón y evidencia; no reescribir historia.

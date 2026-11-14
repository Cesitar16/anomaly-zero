# FUL-107 — borrador de alcance científico provisional

**Estado:** propuesta para discusión; no es selección aprobada del MVP. Mantiene en alcance la terna de Anomaly Zero y usa el catálogo de FUL-102 como fuente de detalle para evitar duplicarlo.

## Matriz de evidencia

| Variable | Producto y versión | Evidencia documental | Descarga / datos abiertos | EDA y calidad | Región | Viabilidad para MVP | Pendientes / validadores |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Temperatura del aire | MERRA-2 `M2TMNXSLV` 5.12.4, `T2M` | CMR y catálogo registran colección, campo y 240 meses 2005–2024. K está comprobado en copia NCAR reorganizada, no en el granulo NASA original. | Gránulo original NASA no abierto; intento anónimo a GES DISC devolvió 401. Hay copia NCAR de los 12 meses de 2005. | QA de finitos/fill en la caja para los 12 meses NCAR; filtros de calidad, QA independiente y archivo nativo NASA pendientes. POWER comparte ascendencia MERRA-2 y no es contraste independiente. | Solo caja rectangular en comprobaciones de la copia; sin agregado de cuenca. | Candidato, evidencia nativa insuficiente para serie regional. No priorizar como resultado científico sin resolver acceso y calidad. | Alaín: acceso, granulo y manifest. Lucas: metadatos/unidades/QA. César: comparabilidad con POWER. FUL-104/105/106. |
| Precipitación | GPM IMERG Final `GPM_3IMERGM` 07/V07B, `Grid/precipitation` | Catálogo y documentación NASA describen tasa mensual en mm/h; CMR inventaría 240 meses 2005–2024. | Muestras NCAR/GDEX de 12 meses de 2005 y enero de 2010 abiertas; las coincidencias CMR ayudan a identificar enero de 2010 pero no prueban identidad byte a byte con descarga NASA. | 12 muestras 2005 con valores finitos, no fill y no negativos en la caja; hay campos auxiliares de calidad con semántica documental. No hay umbral QA ni validación independiente aprobado. | Ensayos con geometría MDBA para una fecha: centro, intersección y pesos producen resultados distintos. Ensayo de área equivalente cierra numéricamente bajo supuestos explícitos, aún experimental. | Candidato útil para validar la ruta espacial, pero no para declarar serie de cuenca/trend sin fijar QA, fuente y método. | Lucas: QA y polígono. Alaín: muestra nativa/manifiesto. César: calendario, faltantes, dependencia de productos y sensibilidad en varias fechas. FUL-104/105/106. |
| Humedad del suelo | GLDAS Noah `GLDAS_NOAH025_M` 2.1, `SoilMoi0_10cm_inst` | Catálogo/manual confirman capa de suelo, unidad kg m⁻² y semántica mensual de promedio de pasos de 3 h. CMR inventaría 240 meses 2005–2024. | Un granulo NASA auténtico autenticado: enero 2005; 25.075.859 bytes y SHA-256 `5fe42fc81dae292f3be27c3b3460249609a3aa1699532edba25a88fa53b08593`. | FUL-105: caja con 3.360 celdas, 3.045 válidas, 315 faltantes (90,625 %), media sin pesos 16,0753 kg/m². Sin `scale_factor`/`add_offset`. QA de serie, máscara y linaje histórico pendientes. | Caja `138,-38,153,-24`, no polígono ni agregado de cuenca. Archivo declara `history` 2019; su estado respecto del enmascarado de aguas continentales posterior a 2020 debe revisarse. | Es la mejor ruta técnica para un spike reproducible de una muestra mensual. No hay evidencia suficiente para llamarlo primer producto científico regional o construir una serie temporal. | Lucas: idoneidad/linaje y geometría. Alaín: cobertura de descarga y procedencia futura. César: QA y comparabilidad. FUL-104/105/106. |

Las 240 entradas CMR son inventario de catálogo, no 240 grillas descargadas ni 240 valores válidos de cuenca. Los detalles y referencias originales por fuente permanecen en [catalog_mvp.json](catalog_mvp.json), [contraste_fuentes.md](contraste_fuentes.md) y [region_murray_darling.md](region_murray_darling.md).

## Propuesta provisional para decisión

### 1. Primera variable implementable

Ninguna fuente cumple hoy los requisitos para una serie mensual regional Murray–Darling validada. Si el equipo necesita un **vertical slice técnico**, GLDAS es el candidato práctico más próximo porque existe un archivo NASA autenticado y un EDA reproducible. El slice debe limitarse explícitamente a inspección/QA de enero de 2005 en la caja rectangular. Esto no selecciona GLDAS como producto oficial del MVP ni reduce el alcance permanente de temperatura, lluvia y suelo.

IMERG puede ser una ruta paralela para probar geografía, porque existen muestras mensuales y ensayos de bordes documentados; los métodos comparados aún no están aprobados. MERRA-2 necesita primero resolver el acceso y la validación del gránulo NASA original.

### 2. Qué requiere una representación de la cuenca

- Obtener una geometría completa MDBA reutilizable, con atribución/licencia, CRS y hash registrados. El segmento `LineString` del repositorio no sirve de máscara; la copia geométrica completa citada en la investigación no está versionada aquí.
- Acordar transformación, precisión de bordes, centros frente a intersecciones, fracción de área, ponderación de celdas y comportamiento ante faltantes.
- Probar conservación de área, sensibilidad y cobertura en varias fechas/productos; documentar incertidumbre y QA. No adoptar el resultado exploratorio de IMERG de enero de 2005 como método definitivo.

### 3. Fuentes que necesitan más validación

Las tres. MERRA-2 requiere archivo NASA nativo; IMERG requiere fuente/procedencia reproducible, semántica temporal/QA y filtro aprobado; GLDAS requiere QA de serie y resolución de linaje/procesamiento histórico. En todas faltan la máscara y una cobertura regional observada con reglas acordadas.

### 4–6. Gráficos, meses y mapas

Hoy no hay base suficiente para un gráfico mensual **regional de cuenca**: CMR ofrece inventario y las muestras no constituyen la serie procesada. Puede presentarse como artefacto de investigación una visualización de una muestra mensual o el piloto puntual NASA POWER, etiquetando fuente, fecha, soporte espacial, cobertura y limitaciones; no llamarla tendencia de la cuenca.

No se ha demostrado disponibilidad de 240 meses de píxeles válidos para ningún producto. Hay 240 meses inventariados en CMR; muestras directas/derivadas disponibles cubren solo ciertos archivos/meses. Los mapas temporales requieren grillas por fecha armonizadas, QA, geometría y método espacial, por lo que no están justificados todavía.

### 7. Requisitos para tendencias

Primero una serie regional mensual verificable con meses esperados/observados, faltantes, cobertura y QA. Después, decisión científica sobre continuidad, estacionalidad, autocorrelación, definición de anomalía, modelo/prueba, incertidumbre, supuestos y validación independiente. No especifica ni aprueba aquí un test, pendiente o umbral estadístico.

### 8. Información que FUL-108 debería preservar

Sin definir schemas ni endpoints, los contratos deberían poder transportar: producto, versión, colección/DOI, variable, unidad original y conversión aplicada, tiempo/periodo/calendario, región y geometría/CRS, método de selección y ponderación, total/válido/faltante/cobertura, indicadores QA y sus reglas, procedencia/hashes del archivo y del derivado, versión de procesamiento, incertidumbre, estado (incluidos `no_data`/`partial`/`pending`) y métricas no disponibles como `null`.

## Discrepancia de alcance de FUL-105

Según el contexto recibido, Linear muestra FUL-105 como `Done` tras fusionarse la PR #7, aunque el texto original cubre los tres productos y un informe metodológico. No se modificó tarjeta ni dependencia. Se recomienda al equipo la **opción A**: conservar el objetivo original y volver la tarjeta a In Progress hasta completar las variables y metodología. Alternativamente, la opción B conserva FUL-105 como el primer EDA GLDAS y crea explícitamente una sucesora para MERRA-2, IMERG y el plan científico. Ambas requieren acuerdo del equipo; no se ejecuta ninguna aquí.

## Preguntas de revisión

- **Lucas:** ¿es correcta la prioridad técnica GLDAS como muestra de trabajo, manteniendo sin decisión el producto/región científica? ¿Qué linaje y criterio QA exige la muestra GLDAS de 2005? ¿Qué método de polígono/borde debe probarse a continuación?
- **Alaín:** ¿cuál es el estado real de FUL-106 y qué productos nativos, versiones, hashes, atributos y limitaciones puede entregar? La rama remota observada está detrás de `dev` y no tiene commits únicos ni PR abierta; confirmar si el trabajo sigue en otro lugar.
- **César:** ¿qué checks de QA y cobertura deben ser puerta antes de construir una serie? ¿Qué soporte temporal/unidad se conserva para comparar variables?
- **Equipo:** ¿FUL-105 sigue In Progress con el objetivo original o se divide en avance GLDAS y tarjeta sucesora? ¿Qué evidencia mínima habilita FUL-107 y después FUL-108?

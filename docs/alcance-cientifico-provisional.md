# FUL-107 — borrador de alcance científico provisional

**Estado:** propuesta para discusión; no es selección aprobada del MVP. Mantiene en alcance la terna de Anomaly Zero y usa el catálogo de FUL-102 como fuente de detalle para evitar duplicarlo. Actualización de evidencia: la [PR #9](https://github.com/Cesitar16/anomaly-zero/pull/9) (FUL-106), Draft hacia `dev` en HEAD `e2174d5`, documenta una muestra NASA auténtica inspeccionada por producto y una QA espacial acotada. Sus datos originales, manifiestos y CSV permanecen fuera de Git; esta evidencia aún requiere revisión independiente y no es funcionalidad integrada en `dev` ni aprobación científica.

## Matriz de evidencia

| Variable | Producto y versión | Evidencia documental | Descarga / datos abiertos | EDA y calidad | Región | Viabilidad para MVP | Pendientes / validadores |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Temperatura del aire | MERRA-2 `M2TMNXSLV` 5.12.4, `T2M` | CMR y catálogo inventarían 240 meses 2005–2024. PR #9 documenta el granule `MERRA2_300.tavgM_2d_slv_Nx.200501.nc4`, 54.419.597 bytes, SHA-256 `103d95aa3ffe9b8d7e98caea5f6a764831bad3b70155370d3a84c2dfd95616c6`; la unidad reportada es K. | Una muestra NASA auténtica de enero de 2005 está descrita en la PR #9; el archivo y su manifest no están en Git para inspección independiente. | PR #9 reporta NetCDF4, forma 1×361×576, 0,5°×0,625°, fill observado y 323/323 centros MDBA finitos/no-fill. No reporta candidatos QA; esto no equivale a validar todos los píxeles ni una serie. POWER comparte ascendencia MERRA-2 y no es contraste independiente. | QA espacial exploratoria de una fecha por centros; sin agregado mensual regional de producción. | Candidato con acceso nativo demostrado en el reporte de FUL-106; todavía insuficiente para aprobar serie regional. | Alaín: archivos/manifest y reproducción. Lucas: identidad, unidades, QA y geometría. César: comparabilidad con POWER. FUL-104/105/106. |
| Precipitación | GPM IMERG Final `GPM_3IMERGM` versión de colección 07, granule `V07B`, `Grid/precipitation` | Catálogo y documentación NASA describen tasa mensual en mm/h; CMR inventaría 240 meses 2005–2024. PR #9 documenta el granule auténtico `3B-MO.MS.MRG.3IMERG.20050101-S000000-E235959.01.V07B.HDF5`, 18.028.945 bytes, SHA-256 `bac3b9bc5ee8cc3eb1e5fe844778d54fd86e2b722813055b37f3872e6e4c73d5`. | Una muestra NASA auténtica de enero de 2005 está descrita en la PR #9; archivo y manifest fuera de Git. La nomenclatura de colección `07` frente a `ProductVersion=V07B` requiere confirmación de Lucas. | PR #9 reporta HDF5, forma 1×3600×1800, 0,1°, unidad mm/hr, fill y 10.092/10.092 centros MDBA finitos/no-fill. Los candidatos `precipitationQualityIndex` y `randomError` no se interpretan ni filtran. | QA espacial exploratoria de una fecha por centros; los ensayos anteriores de intersección/ponderación siguen experimentales y no sustituyen una regla validada. | Candidato para ruta espacial; no declara serie de cuenca ni producto científico validado. | Lucas: nomenclatura, QA y polígono. Alaín: archivos/manifests y reproducción. César: calendario, faltantes, dependencia de productos y sensibilidad. FUL-104/105/106. |
| Humedad del suelo | GLDAS Noah `GLDAS_NOAH025_M` 2.1, `SoilMoi0_10cm_inst` | Catálogo/manual confirman capa de suelo, unidad kg m⁻² y semántica mensual de promedio de pasos de 3 h. CMR inventaría 240 meses 2005–2024. | Un granulo NASA auténtico autenticado: enero 2005; 25.075.859 bytes y SHA-256 `5fe42fc81dae292f3be27c3b3460249609a3aa1699532edba25a88fa53b08593`. | FUL-105: caja con 3.360 celdas, 3.045 válidas, 315 faltantes (90,625 %), media sin pesos 16,0753 kg/m². PR #9 reporta además 1.617 centros MDBA, 1.615 finitos/no-fill y 2 faltantes. Son denominadores espaciales distintos. Sin `scale_factor`/`add_offset`; QA de serie y linaje histórico pendientes. | QA de una fecha en caja y por centros MDBA; ninguno es una serie de cuenca. El archivo declara `history` 2019; su estado respecto del enmascarado de aguas continentales posterior a 2020 debe revisarse. | Es la ruta con EDA previo más reproducible para un primer spike técnico mensual; esto no selecciona GLDAS como producto científico del MVP. | Lucas: idoneidad/linaje y geometría. Alaín: archivo/manifest y procedencia. César: QA y comparabilidad. FUL-104/105/106. |

Las 240 entradas CMR son inventario de catálogo, no 240 grillas descargadas ni 240 valores válidos de cuenca. PR #9 reporta una sola muestra por producto; sus hashes y dimensiones están documentados, pero los archivos originales/manifests/CSV se conservan fuera de Git y la PR sigue sin merge/revisión. Los detalles y referencias originales por fuente permanecen en [catalog_mvp.json](catalog_mvp.json), [contraste_fuentes.md](contraste_fuentes.md) y [region_murray_darling.md](region_murray_darling.md).

## Matriz de decisiones para FUL-107

| Decisión pendiente | Evidencia disponible | Evidencia faltante | Quién valida | Tarjeta | Estado |
| --- | --- | --- | --- | --- | --- |
| Distinguir demostración técnica de selección científica | PR #9 documenta una muestra auténtica por producto y QA espacial de una fecha; GLDAS cuenta además con EDA FUL-105. La nota de coordinación enlazada a FUL-99 nombra MERRA-2/T2M Plan A provisional, sin excluir los demás. | Criterios de aceptación de una demostración y ratificación o ajuste de la prioridad provisional para el primer vertical slice regional. | Lucas + equipo; César aporta QA | FUL-104, FUL-107 | Pendiente; no hay producto científico aprobado |
| Confirmar identidades, versiones, unidades y granules | FUL-104 inspeccionó localmente muestras NASA originales MERRA-2 e IMERG de enero 2005/2021; GLDAS, enero 2005/2021. Archivos y hashes se documentan en el informe, y los binarios siguen fuera de Git. | Reproducir la lectura desde manifiestos/gránulos accesibles al equipo; aclarar `07` frente a `V07B` para IMERG y completar revisión independiente de Lucas. | Lucas + Alaín | FUL-104, FUL-106 | Evidencia local reportada por FUL-104; reproducción/revisión pendiente |
| Aprobar región y método de selección espacial | PR #9 informa uso de geometría MDBA completa, EPSG:4326 y hash; cuenta centros y faltantes por producto. | Lucas debe confirmar procedencia/CRS/geometría; comparar centros con intersección/área fraccional, sensibilidad y faltantes. El conteo central no pondera superficie. | Lucas; César revisa QA | FUL-104, FUL-107 | Exploratorio; sin método regional aprobado |
| Aprobar reglas de QA por producto | Fill y candidatos QA están reportados; PR #9 no aplica los filtros auxiliares de IMERG. | Umbrales/reglas por producto, efecto de cada filtro y validación independiente. | Lucas + César | FUL-104, FUL-105, FUL-106 | Pendiente |
| Establecer condiciones para serie mensual regional | Catálogo CMR inventaría 240 meses por colección; muestras documentadas cubren enero de 2005. | Archivos y manifests por mes, calendario, duplicados/faltantes, cobertura común, criterios QA y método espacial reproducible. | César + Lucas; Alaín entrega archivos | FUL-105, FUL-106, FUL-107 | No hay serie temporal regional |
| Definir visualización responsable | Frontend sigue como starter Vite y backend expone solo `/health`; una ficha de muestra puede mostrar fecha, fuente, variable, unidad y límites. | Contrato FUL-108 y método validado antes de presentar agregados, mapas de cuenca o tendencias. | Alejandra + César + Lucas | FUL-107, FUL-108 | Puede mostrarse solo evidencia de muestra con advertencias |

### Tres niveles de alcance

| Nivel | Situación actual | Decisión |
| --- | --- | --- |
| Primera demostración técnica | Las tres muestras de enero de 2005 y QA espacial están reportadas por PR #9; GLDAS tiene además una ruta de EDA ya integrada. La nota de coordinación FUL-99 identifica MERRA-2/T2M como prioridad Plan A provisional para una ruta regional. | FUL-107 debe ratificar el vertical slice; GLDAS puede seguir sirviendo para demostrar EDA y MERRA-2 para la ruta regional prevista, sin elevar ninguno a producto validado. |
| Primer producto científicamente validado | Ninguna variable tiene serie mensual regional, QA, cobertura y agregación aceptadas por Lucas/equipo. | Aún no existe; FUL-104 y FUL-107 deben resolverlo. |
| MVP completo | Requiere el alcance temporal/regional acordado, entradas reproducibles, reglas QA, resultados y contrato/UI aprobados. | Propuesto, no construido ni aprobado; no implica descargar los 240 meses antes de acordar el caso. |

## Propuesta provisional para decisión

### 1. Primera variable implementable

Ninguna fuente cumple hoy los requisitos para una serie mensual regional Murray–Darling validada. Si el equipo necesita un **vertical slice técnico**, puede usar GLDAS por su EDA ya integrado o comparar las lecturas de los tres productos inspeccionadas en FUL-104; los archivos originales permanecen fuera de Git y el acceso reproducible para otros checkouts/manifiestos queda por coordinar con Alaín. El EDA GLDAS FUL-105 en caja sigue siendo distinto del conteo por centros MDBA reportado por FUL-106. Esto no selecciona GLDAS como producto científico oficial del MVP ni reduce el alcance de temperatura, lluvia y suelo.

IMERG y MERRA-2 tienen muestras NASA auténticas de enero de 2005 y 2021 inspeccionadas por FUL-104; permanecen pendientes de revisión independiente. IMERG puede ayudar a continuar pruebas geográficas; los métodos comparados aún no están aprobados. La identidad, unidad y estructura de las muestras MERRA-2 están documentadas, pero su QA, pertinencia y uso en una serie deben revisarse.

### 2. Qué requiere una representación de la cuenca

- FUL-106 informa que usó una geometría completa MDBA con atribución/licencia, EPSG:4326 y hash; el original y los CSV no están versionados en la PR. Lucas debe confirmar procedencia y CRS, y Alaín debe facilitar una forma reproducible de acceder al archivo. El segmento `LineString` versionado en el repositorio nunca sirve de máscara.
- Acordar transformación, precisión de bordes, centros frente a intersecciones, fracción de área, ponderación de celdas y comportamiento ante faltantes.
- Probar conservación de área, sensibilidad y cobertura en varias fechas/productos; documentar incertidumbre y QA. No adoptar el resultado exploratorio de IMERG de enero de 2005 como método definitivo.

### 3. Fuentes que necesitan más validación

Las tres. FUL-104 inspeccionó gránulos NASA nativos por producto y reporta la comparación espacial de dos meses; todavía requiere reproducción y revisión independiente del equipo. Para MERRA-2 falta acordar QA; para IMERG, confirmar la nomenclatura de versión y semántica temporal y acordar filtro QA; para GLDAS, QA de serie y linaje histórico. En todas faltan reglas acordadas y una serie regional mensual validada.

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
- **Alaín:** ¿puedes facilitar originales y manifests de las tres muestras de enero de 2005 documentadas en la PR #9 (`e2174d5`) para reproducir inspección y QA, y confirmar sus limitaciones de acceso/versión? La PR sigue Draft y sus datos no están en Git.
- **César:** ¿qué checks de QA y cobertura deben ser puerta antes de construir una serie? ¿Qué soporte temporal/unidad se conserva para comparar variables?
- **Equipo:** ¿FUL-105 sigue In Progress con el objetivo original o se divide en avance GLDAS y tarjeta sucesora? ¿Qué evidencia mínima habilita FUL-107 y después FUL-108?

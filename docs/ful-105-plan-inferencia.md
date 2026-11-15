# FUL-105 — Plan de inferencia y puertas para EDA comparativo

**Estado:** plan previo al análisis inferencial. No se estiman tendencias ni se aprueba aquí una región, regla de QA o método de agregación.  
**Corte de evidencia:** 2026-11-14.  
**Relación con el trabajo anterior:** el EDA GLDAS de enero de 2005 y su documentación permanecen en [eda-gldas-preliminar.md](eda-gldas-preliminar.md). Esta nota define qué debe ocurrir antes de extender ese avance a MERRA-2 e IMERG y, más adelante, a una serie histórica.

## Estado de evidencia y límite de este entregable

En el checkout original está disponible el NetCDF GLDAS auténtico de enero de 2005 y su manifiesto. La inspección independiente ya documentada identifica `GLDAS_NOAH025_M.2.1`, `SoilMoi0_10cm_inst`, `kg m-2`, 25.075.859 bytes y SHA-256 `5fe42fc81dae292f3be27c3b3460249609a3aa1699532edba25a88fa53b08593`; ambos valores de integridad coinciden. La selección previa fue una caja rectangular, no el polígono de la cuenca.

En esta rama aislada basada en `origin/dev`, no están los archivos crudos ni manifiestos MERRA-2 e IMERG. Tras integrar el lector de FUL-106, se obtuvo la geometría pública de MDBA descrita en [region_murray_darling.md](region_murray_darling.md) desde el FeatureServer con `outSR=4326`: un `Polygon` EPSG:4326 de 477.805 bytes y SHA-256 `d36fe31424758cc4fb8eef25e21b835bb5c05c793c746e8a1eb7b5a5841f6a53`, coincidente con el hash reportado en PR #9. Se conservó como caché local ignorada en `data/cache/ful-105/mdba_boundary_4326.geojson`; no se añadió a Git.

Se usó `earthdata_spatial.spatial_qa` sobre el granule GLDAS auténtico y su manifiesto del checkout original. Reprodujo de forma independiente la selección por centros reportada en PR #9: **1.617** centros dentro, **1.615** finitos/no-fill, **2** faltantes, **99,8763 %** válidos. No aplica filtros QA ni pondera área; no es cobertura de superficie ni promedio de cuenca. El resultado reproduce el QA espacial de GLDAS de Alaín, no convierte el EDA rectangular previo en un análisis comparativo.

Los originales y manifiestos MERRA-2 e IMERG continúan ausentes localmente. El intento acotado de MERRA-2 enero de 2005 con `--auth-strategy netrc` llegó a autenticación pero terminó con `LoginStrategyUnavailable`; no se inició un login interactivo. Por ello esta entrega **no es un EDA comparativo**, no incorpora datos simulados ni crea un notebook vacío que sugiera resultados inexistentes. El notebook ejecutado GLDAS local se conserva fuera de este worktree y no se modifica.

## Preparación de la serie mensual

### Inventario y calendario

1. Antes de descargar o analizar, fijar producto, colección/versión, variable, calendario y ventana. La ventana propuesta para evaluar es enero de 2005 a diciembre de 2024: 240 meses nominales. El inventario CMR de 240 granules por sí solo no demuestra que se hayan descargado, abierto o validado 240 observaciones.
2. Mantener un registro por `producto × versión × variable × mes × granule`, con URI/procedencia, tamaño, SHA-256, fecha de adquisición, formato, calendario, nombre de variable y estado de inspección. Mantener separados los conteos de meses esperados, granules encontrados, granules abiertos y meses que pasan QA.
3. Rechazar duplicados de clave y periodos fuera de ventana; comprobar huecos, orden temporal, límites/centro del periodo, calendario y consistencia entre unidades y metadatos. No rellenar meses ausentes por interpolación durante el EDA base. Informar explícitamente los huecos y estudiar cualquier imputación en sensibilidad separada, si el equipo la autoriza.
4. Conservar una traza de la transformación desde valores crudos hasta resumen mensual y agregado espacial. No modificar los NetCDF/HDF5 originales. Registrar versiones de librerías y código, y hashes de entradas y derivados.

### Variables y conversiones

| Fuente y variable | Semántica/unidad a preservar | Regla inicial de manejo |
| --- | --- | --- |
| MERRA-2 `M2TMNXSLV`, `T2M` | Temperatura del aire a 2 m; K | Mantener K en el conjunto crudo. Cualquier conversión a °C debe ser explícita, derivada y reversible; no llamarla temperatura superficial. |
| IMERG Final `GPM_3IMERGM`, `Grid/precipitation` | Tasa de precipitación mensual; mm h⁻¹ | No etiquetar como mm/mes. Una conversión a profundidad mensual requiere confirmar la semántica de la variable y multiplicar por las horas efectivas del periodo/calendario, con regla explícita para cobertura temporal incompleta. |
| GLDAS Noah 2.1 `SoilMoi0_10cm_inst` | Agua en capa de suelo de 0–10 cm; kg m⁻² | Conservar unidad y semántica declaradas; no convertir a porcentaje volumétrico sin densidad/definición validada. Interpretar junto a `cell_methods` y linaje del producto. |

Las conversiones no reemplazan el valor ni la unidad originales. Antes de combinar fuentes, Lucas debe validar identidad, versión, soporte temporal y significado físico; magnitudes con unidades distintas no se comparan directamente.

### QA de valores y productos

Para cada mes y variable se registrarán tamaño de la muestra evaluada, finitos, NaN/Inf, `_FillValue`, `missing_value`, `scale_factor`, `add_offset`, ceros, candidatos de flags QA, mínimo, percentiles (1, 5, 25, 50, 75, 95, 99), máximo y proporción válida. Distinguir valores almacenados de valores escalados/decodificados. Los ceros se conservan salvo que documentación oficial de la variable los defina como inválidos; los extremos se marcan para revisión, no se borran automáticamente.

No se ha aprobado aún una regla de calidad compartida. Los flags y umbrales deben definirse por producto a partir de documentación de versión y revisión de Lucas. Para IMERG, evaluar los campos QA disponibles (por ejemplo, `precipitationQualityIndex` y `randomError` si están presentes) como diagnósticos separados; no atribuir un filtrado a la muestra PR #9 ni aplicarlo hasta acordar la regla. Informar resultados antes y después de cada filtro propuesto, junto a su efecto sobre cobertura.

GLDAS requiere además resolver el linaje y el tratamiento de aguas continentales para enero de 2005 señalado en el EDA precedente. No inferir que una variable candidata ausente implica calidad perfecta.

## Región y soporte espacial

La caja `138–153° E, 38–24° S` del EDA anterior solo sirve para una exploración rectangular. El GeoJSON de ejemplo versionado es un fragmento `LineString` y no se usa como máscara. PR #9 reporta un polígono MDBA completo y un hash, pero el original no está en este worktree para verificar bytes, procedencia o CRS.

Puerta previa a un resumen de cuenca:

1. Recuperar el polígono fuente con su atribución/licencia, geometría íntegra, CRS declarado y SHA-256; comprobar validez, extensión y transformación.
2. Describir la grilla nativa de cada producto y separar selección por centro, intersección y fracción de área. No llamar “cobertura de superficie” al porcentaje de centros válidos.
3. Comparar métodos espaciales candidatos en soporte nativo, documentar ponderación por área y tratamiento de celdas parciales/faltantes; verificar cierre de áreas y sensibilidad a precisión geométrica y proyección.
4. Obtener revisión de Lucas/FUL-104 antes de nombrar un resultado como media de Murray–Darling. Hasta entonces, cualquier agregado se etiqueta como exploratorio con método y fecha, o se omite.

No remuestrear a una resolución común por conveniencia. Si se ensaya remuestreo, conservar original, método, supuestos y sensibilidad, y no mezclar ese ensayo con resultados nativos.

## Requisitos antes de inferir tendencia

La inferencia solo se considera después de obtener series mensuales regionales trazables, con cobertura y QA definidas. Por producto deben publicarse meses esperados/observados, faltantes, regla de cobertura espacial, cambios de versión, periodos discontinuos y cualquier transformación. La selección de una ventana completa, subperiodo común o tratamiento de huecos se debe preespecificar; no elegirla por el resultado más significativo.

Antes del test se examinarán ciclo estacional, autocorrelación (incluida la estacional), distribución, heterocedasticidad, rupturas documentadas y eventos extremos. Se conservarán las observaciones extremas válidas y se evaluará su influencia en análisis de sensibilidad. Si cambia el producto o la versión dentro de la ventana, se evaluará homogeneidad antes de interpretar una pendiente.

| Método candidato | Uso condicional y decisiones pendientes |
| --- | --- |
| Descripción por mes/estación y gráficos | Primero describir cobertura, distribución, ciclo anual y faltantes. Mostrar incertidumbre espacial y soporte, no solo una línea suavizada. |
| Pendiente Theil–Sen | Estimador robusto de magnitud por unidad temporal; reportar escala, intervalo de confianza y ventana. No implica por sí mismo significancia ni corrige autocorrelación. |
| Mann–Kendall estacional | Candidato para tendencia monotónica con estacionalidad controlada si las observaciones mensuales son comparables y el diseño respeta la estacionalidad. Dependencia serial puede alterar la inferencia: evaluar métodos de corrección apropiados y declarar supuestos. |
| Regresión con errores HAC | Análisis complementario si una tendencia paramétrica y la estructura residual tienen justificación. Preespecificar regresores, kernel y rezagos; HAC no repara discontinuidades, QA deficiente ni una agregación espacial sesgada. |
| Intervalos, sensibilidad y multiplicidad | Declarar nivel de confianza, procedimiento y familia de hipótesis para tres productos/variables. Comparar ventana, QA, geometría, faltantes y método espacial con análisis identificados como sensibilidad, no como selección oportunista. |

No se elige aquí una prueba definitiva ni se presentan pendientes, p-values o significancia. La selección deberá ser revisada por Lucas con la serie y el diagnóstico de dependencia disponibles. Las referencias metodológicas son Hirsch, Slack & Smith sobre Kendall estacional ([USGS, 1982](https://pubs.usgs.gov/publication/70011649)); Hirsch & Slack sobre dependencia serial estacional ([USGS, 1984](https://pubs.usgs.gov/publication/70012890)); guía estadística de agua del USGS ([2020](https://pubs.usgs.gov/publication/tm4A3)); documentación de [Theil–Sen de SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.theilslopes.html) y [errores robustos HAC de Statsmodels](https://www.statsmodels.org/dev/generated/statsmodels.regression.linear_model.RegressionResults.get_robustcov_results.html). La elección de una fuente no sustituye revisión de supuestos ni aprobación científica.

## Contrato de datos que conviene preservar para FUL-108

Esto es una lista de necesidades, no un esquema ni endpoint aprobado. Cada resultado futuro debería poder conservar:

- producto, versión, colección/DOI, variable, unidad nativa y conversiones;
- inicio/fin del periodo, frecuencia y calendario;
- región, identificador/hash de geometría, CRS y método espacial;
- QA aplicado y versión de las reglas; celdas/área evaluadas, válidas, faltantes y cobertura;
- procedencia, granules, SHA-256 de originales y derivados, versión de código/procesamiento;
- método estadístico, ventana, unidad temporal de pendiente e intervalo de confianza cuando se hayan calculado;
- diagnóstico de supuestos, sensibilidad e incertidumbre;
- estado explícito (`pending`, `partial`, `no_data`, `review_required`, `complete`, según acuerde el equipo) y valores `null` para resultados aún no calculados.

No implementar el contrato definitivo en FUL-105. No marcar `complete` si las puertas de datos, QA o revisión están pendientes.

## Matriz de preparación para FUL-107

| Componente | Hecho reproducible hoy | Falta antes de serie regional | Revisor/entrega |
| --- | --- | --- | --- |
| GLDAS | EDA de una muestra enero 2005 sobre caja integrado en PR #7; lector FUL-106 y `spatial_qa` reproducen metadatos, SHA/manifiesto y conteos MDBA 1.617/1.615/2. | Revisar linaje/QA GLDAS y método espacial; obtener serie mensual si se aprueba el alcance. | César documenta; Lucas revisa; Alaín facilita insumos. |
| MERRA-2 | PR #9 reporta una muestra enero 2005, no reproducida localmente aquí. | Original + manifiesto, apertura independiente, metadatos/QA y cobertura multi-mes. | Alaín entrega handoff reproducible; César reproduce; Lucas valida semántica. |
| IMERG | PR #9 reporta una muestra enero 2005, no reproducida localmente aquí. | Original + manifiesto, reglas QA, calendario/conversión y cobertura multi-mes. | Alaín entrega; César reproduce; Lucas valida identidad y QA. |
| Cuenca | Se obtuvo del FeatureServer el polígono completo EPSG:4326 (hash coincide con PR #9) y se reprodujo para GLDAS el conteo por centros. La copia está en caché ignorada. | Lucas debe revisar procedencia/CRS y aprobar método/bordes/pesos/cobertura; conteos por centro no cubren área. | Lucas/FUL-104 valida; Alaín aporta handoff reproducible. |
| Inferencia | Este plan define diagnósticos y métodos candidatos, sin calcular tendencia. | Serie regional QA, diagnósticos temporales, preespecificación y revisión. | César prepara; Lucas revisa; equipo decide el caso FUL-107. |

FUL-107 sigue pendiente: esta matriz no selecciona producto ni método y no valida una visualización de tendencia.

## Acciones siguientes

- **César:** conservar el notebook ejecutado GLDAS fuera de Git; coordinar FUL-105 en Linear cuando haya acceso; reproducir MERRA-2/IMERG cuando se facilite autenticación bajo control del usuario y los manifiestos; no iniciar tendencia todavía.
- **Alaín:** facilitar ruta de handoff permitida para los NetCDF/HDF5 originales de MERRA-2 e IMERG, manifiestos, SHA-256, metadatos y script/comando exactos de inspección; incluir IMERG febrero solo si ayuda a validar calendario, sin confundir dos meses con una serie.
- **Lucas:** revisar identidad, unidades, linaje GLDAS, reglas QA, polígono/CRS, cobertura/ponderación y supuestos estadísticos antes de aprobar agregados o inferencia.

FUL-105 continúa incompleta frente a su alcance original; FUL-107 no debe cerrarse con esta entrega.

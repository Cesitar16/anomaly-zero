# FUL-105 — Plan de inferencia y puertas para EDA comparativo

**Estado:** plan previo al análisis inferencial. No se estiman tendencias ni se aprueba aquí una región, regla de QA o método de agregación.  
**Corte de evidencia:** 2026-11-15 UTC.
**Relación con el trabajo anterior:** el EDA GLDAS de enero de 2005 y su documentación permanecen en [eda-gldas-preliminar.md](eda-gldas-preliminar.md). Esta nota conserva las puertas de inferencia y ahora registra la reproducción del handoff BE-02 y el diagnóstico descriptivo IMERG de enero–diciembre de 2005. No aprueba una regla QA, método regional ni inferencia histórica.

## Estado de evidencia y límite de este entregable

La Release `be02-samples-2005-v1` se descargó en una caché ignorada y aislada. Los tres ZIP pasaron SHA-256 publicado; se verificaron 14 granules y sus 14 manifiestos contra `inventory.json` (tamaño y SHA), y cada manifiesto concuerda con los metadatos de su original. La extracción común quedó bajo `data/cache/ful-105/be02-handoff/data_root`, sin sobrescribir los datos locales. La EDA rectangular GLDAS anterior permanece separada de la selección espacial MDBA de esta nota.

Se obtuvo la geometría pública de MDBA descrita en [region_murray_darling.md](region_murray_darling.md) desde el FeatureServer con `outSR=4326`: un `Polygon` EPSG:4326 de 477.805 bytes y SHA-256 `d36fe31424758cc4fb8eef25e21b835bb5c05c793c746e8a1eb7b5a5841f6a53`, coincidente con el hash reportado en PR #9. Se conservó como caché local ignorada en `data/cache/ful-105/mdba_boundary_4326.geojson`; no se añadió a Git.

El notebook [02_eda_nasa_products.ipynb](../research/notebooks/02_eda_nasa_products.ipynb) verifica procedencia, resume distribuciones globales y reutiliza `inspect_product`/`spatial_qa` de FUL-106 para los tres granules. La copia ejecutada permanece en caché local ignorada. Los resultados reproducidos se describen abajo. Solo cubren enero de 2005; no representan una serie temporal ni una comparación directa de magnitudes.

La Release aporta MERRA-2 y GLDAS enero, e IMERG enero–diciembre de 2005 con originales y manifiestos. El CSV portable de 240 filas se validó contra los HDF5 fuente: 12 meses, 20 centros idénticos por mes, referencias resueltas, identidad/unidad constantes, valores sin conversión y QA no aplicado. Los notebooks/datos preexistentes no fueron sobrescritos; la ejecución nueva permanece en caché ignorada.

### Resultados de enero de 2005 reproducidos

Los estadísticos siguientes se calcularon sobre cada grilla global nativa, tras excluir solo valores no finitos y sentinelas de faltantes declarados. El porcentaje válido usa el total de celdas de la grilla; no representa cobertura de superficie terrestre o de la cuenca.

| Producto / variable | Resolución nominal lon × lat | Celdas total / válidas / faltantes | Ceros válidos | Unidad cruda | Mínimo | P05 | Mediana | Media | P95 | Máximo |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| MERRA-2 `T2M` | 0,625° × 0,500° | 207.936 / 207.936 / 0 | 0 | K | 231,973 | 244,804 | 280,087 | 277,502 | 301,005 | 310,168 |
| IMERG `Grid/precipitation` | 0,100° × 0,100° | 6.480.000 / 6.425.329 / 54.671 | 895.459 | mm h⁻¹ | 0 | 0 | 0,037 | 0,0833 | 0,339 | 2,331 |
| GLDAS `SoilMoi0_10cm_inst` | 0,250° × 0,250° | 864.000 / 242.753 / 621.247 | 0 | kg m⁻² | 2,000 | 8,556 | 27,869 | 29,703 | 49,841 | 100,000 |

MERRA-2 es versión 5.12.4 (`C1276812859-GES_DISC`, granule `G1278025954-GES_DISC`); IMERG Final indica colección 07 y `ProductVersion=V07B` (`C2723754851-GES_DISC`, granule `G2823464479-GES_DISC`); GLDAS es versión 2.1 (`C1342986036-GES_DISC`, granule `G1413723174-GES_DISC`). Los archivos son NetCDF4, HDF5 y NetCDF4, respectivamente. SHA-256 reproducidos: MERRA-2 `103d95aa3ffe9b8d7e98caea5f6a764831bad3b70155370d3a84c2dfd95616c6`; IMERG `bac3b9bc5ee8cc3eb1e5fe844778d54fd86e2b722813055b37f3872e6e4c73d5`; GLDAS `5fe42fc81dae292f3be27c3b3460249609a3aa1699532edba25a88fa53b08593`. No se informaron ni aplicaron `scale_factor` o `add_offset`. IMERG reporta `precipitationQualityIndex` y `randomError`; no se aplicaron. MERRA-2 `T2M` es aire a 2 m; la conversión derivada a °C en el notebook no sustituye el valor original en K.

| Selección exploratoria MDBA por centros | Dentro | Finito/no-fill | Faltantes | Válidos de centros |
| --- | ---: | ---: | ---: | ---: |
| MERRA-2 enero | 323 | 323 | 0 | 100 % |
| IMERG enero | 10.092 | 10.092 | 0 | 100 % |
| GLDAS enero | 1.617 | 1.615 | 2 | 99,8763 % |

Los conteos son reproducidos con el polígono indicado, grillas nativas y el método por centros. No se aplican filtros QA científicos, pesos de área ni intersección fraccional. Los histogramas, boxplots y mapas del notebook describen cada grilla global separadamente; no son promedios de cuenca.

Para regenerar el notebook ejecutado en una ubicación local ignorada:

```powershell
uv sync --group research --group dev
uv run jupyter nbconvert --to notebook --execute research/notebooks/02_eda_nasa_products.ipynb --output 02_eda_nasa_products.executed.ipynb --output-dir data/cache/ful-105 --ExecutePreprocessor.timeout=300
```

Se necesitan los tres granules, sus manifiestos y `data/cache/ful-105/mdba_boundary_4326.geojson`; el notebook no descarga datos ni modifica los originales.

## Actualización de evidencia — handoff y año IMERG 2005

La rama se sincronizó con el merge oficial de PR #9 en `origin/dev` (`7e51dac`). El handoff fue verificado antes de extraer: `SHA256SUMS.txt` coincide para todos los assets listados; los ZIP pasan CRC; los 14 granules más 14 manifiestos coinciden con los tamaños/SHA-256 de `inventory.json`; el manifiesto enlaza correctamente bytes/hash del original. No hubo discrepancias. Los originales de la Release coexisten en `data/cache/ful-105/be02-handoff/data_root` y no reemplazan los granules previos del checkout. Las versiones verificadas son GLDAS Noah 2.1, MERRA-2 `M2TMNXSLV` 5.12.4 e IMERG `GPM_3IMERGM` colección 07 (`Grid/precipitation`, `mm/hr`).

El CSV portable tiene 240 filas (12 × 20), claves mes/centro únicas y exactamente los mismos 20 centros en cada mes. `original_file` y `manifest` resuelven dentro de `data_root`; cada valor se comparó con su celda del HDF5 referido y coincide a tolerancia de almacenamiento. Unidad constante `mm/hr`; candidatos `Grid/precipitationQualityIndex` y `Grid/randomError`; `quality_filter_applied=False`. Este panel es solo una selección de 20 centros, sin representatividad de superficie.

El notebook [02_eda_nasa_products.ipynb](../research/notebooks/02_eda_nasa_products.ipynb) ahora admite `FUL105_DATA_ROOT` y reproduce para cada mes la inspección del granule, manifiesto, grilla global y `spatial_qa`. Las coordenadas nativas y polígono conservan SHA/identidad; el predicado geométrico oficial se memoiza por centro exacto para acelerar las doce llamadas, sin alterar su lógica. La tabla de estadísticos de cuenca usa los originales y todos los centros seleccionados por el polígono; el CSV de 20 filas por mes se reporta por separado.

| Mes 2005 | Global válidas / faltantes | Media global (mm/hr) | Mediana global | P95 global | Máximo global | Centros MDBA válidos / faltantes | Media centros MDBA (mm/hr) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Ene | 6.425.329 / 54.671 | 0,083306 | 0,037 | 0,339 | 2,331 | 10.092 / 0 | 0,038 |
| Feb | 6.422.470 / 57.530 | 0,090473 | 0,037 | 0,340 | 2,994 | 10.092 / 0 | 0,047 |
| Mar | 6.422.807 / 57.193 | 0,092655 | 0,048 | 0,331 | 1,838 | 10.092 / 0 | 0,017 |
| Abr | 6.421.167 / 58.833 | 0,090939 | 0,044 | 0,320 | 3,927 | 10.092 / 0 | 0,007 |
| May | 6.425.999 / 54.001 | 0,090182 | 0,047 | 0,321 | 2,401 | 10.092 / 0 | 0,021 |
| Jun | 6.438.698 / 41.302 | 0,090492 | 0,045 | 0,326 | 2,928 | 10.092 / 0 | 0,142 |
| Jul | 6.440.453 / 39.547 | 0,093854 | 0,050 | 0,336 | 2,644 | 10.092 / 0 | 0,038 |
| Ago | 6.447.529 / 32.471 | 0,093809 | 0,049 | 0,334 | 2,422 | 10.092 / 0 | 0,047 |
| Sep | 6.451.507 / 28.493 | 0,089333 | 0,044 | 0,345 | 2,696 | 10.092 / 0 | 0,069 |
| Oct | 6.448.526 / 31.474 | 0,087814 | 0,043 | 0,332 | 2,020 | 10.092 / 0 | 0,081 |
| Nov | 6.448.812 / 31.188 | 0,089515 | 0,044 | 0,331 | 2,584 | 10.092 / 0 | 0,073 |
| Dic | 6.448.516 / 31.484 | 0,088690 | 0,035 | 0,359 | 2,726 | 10.092 / 0 | 0,037 |

Las proporciones globales de faltantes oscilan entre 0,44 % y 0,91 %; en los 10.092 centros MDBA seleccionados no hay fill en estos doce granules. Los candidatos QA permanecen sin aplicar. Las medias mensuales MDBA son descripciones de la selección por centros sin ponderar por área; no son una media regional aprobada. El panel de 20 centros muestra medias entre 0,0285 (mayo) y 0,2155 mm/hr (febrero), pero no sustituye la grilla completa. Los estadísticos globales abarcan el dominio global y se muestran como diagnóstico de distribución, no como estimación MDBA. Un año no permite inferir tendencia climática.

El notebook ejecutado final y sus tres gráficos están en `data/cache/ful-105/` (ignorado por Git); se regeneran, con la ruta de Release, mediante:

```powershell
$env:FUL105_DATA_ROOT = 'C:/ruta/al/data_root'
uv run jupyter nbconvert --to notebook --execute research/notebooks/02_eda_nasa_products.ipynb --output 02_eda_nasa_products.executed.ipynb --output-dir data/cache/ful-105 --ExecutePreprocessor.timeout=2400
```

## Trabajo completado y pendiente

**Completado:** sincronización local con `origin/dev` tras PR #9; verificación integral del handoff; validación del panel portable contra granules originales; EDA comparativo enero de 2005; diagnóstico mensual IMERG 2005 y QA por centros con código FUL-106; rutas del notebook configurables.

**Pendiente:** revisión científica final de Lucas; aprobación del método espacial, flags/umbrales QA y cobertura; decisión sobre agregación regional; datos de mayor extensión temporal; diagnóstico de autocorrelación, estacionalidad/rupturas y método inferencial; validación de FUL-104 y planificación FUL-107. FUL-105 permanece In Progress y la PR #11 debe permanecer Draft hasta completar estas puertas.

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

La caja `138–153° E, 38–24° S` del EDA anterior solo sirve para una exploración rectangular. El GeoJSON de ejemplo versionado es un fragmento `LineString` y no se usa como máscara. La geometría MDBA completa se recuperó desde el FeatureServer documentado en `region_murray_darling.md`; su respuesta GeoJSON declara EPSG:4326 y su SHA coincide con PR #9. La prueba espacial se limita a centros; Lucas todavía debe revisar la fuente, licencia/atribución y método de borde para un uso científico.

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
| MERRA-2 | Enero 2005 abierto; SHA/manifiesto coinciden; estadísticos globales y QA por centros reproducidos. | Confirmar semántica/QA con Lucas y obtener meses adicionales solo si se acuerda el alcance temporal. | Lucas valida semántica; Alaín confirma reproducibilidad. |
| IMERG | Enero 2005 abierto; SHA/manifiesto coinciden; ceros/fill, estadísticos globales y QA por centros reproducidos. | Obtener manifiestos/granules de febrero–diciembre de handoff accesible o autenticación del usuario; definir reglas QA y calendario/conversión. | Alaín facilita archivos; Lucas valida versión/QA; César reproduce y compara temporalmente. |
| Cuenca | Se obtuvo del FeatureServer el polígono completo EPSG:4326 (hash coincide con PR #9) y se reprodujo para GLDAS el conteo por centros. La copia está en caché ignorada. | Lucas debe revisar procedencia/CRS y aprobar método/bordes/pesos/cobertura; conteos por centro no cubren área. | Lucas/FUL-104 valida; Alaín aporta handoff reproducible. |
| Inferencia | Este plan define diagnósticos y métodos candidatos, sin calcular tendencia. | Serie regional QA, diagnósticos temporales, preespecificación y revisión. | César prepara; Lucas revisa; equipo decide el caso FUL-107. |

FUL-107 sigue pendiente: esta matriz no selecciona producto ni método y no valida una visualización de tendencia.

## Acciones siguientes

- **César:** conservar el notebook ejecutado GLDAS fuera de Git; sincronizar FUL-105 en Linear cuando haya acceso; usar la EDA enero como baseline y no iniciar tendencia todavía.
- **Alaín:** facilitar ruta de handoff compartida para IMERG febrero–diciembre, los manifiestos y el CSV portable de 12 meses; confirmar rutas, hashes y validación actuales sin asumir acceso a archivos de su máquina.
- **Lucas:** revisar identidad, unidades, linaje GLDAS, reglas QA, polígono/CRS, cobertura/ponderación y supuestos estadísticos antes de aprobar agregados o inferencia.

FUL-105 continúa incompleta frente a su alcance original; FUL-107 no debe cerrarse con esta entrega.

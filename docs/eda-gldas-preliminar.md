# FUL-105 — EDA preliminar GLDAS (enero de 2005)

## Objetivo y alcance

Este avance verifica la procedencia y estructura de una muestra GLDAS Noah 2.1 auténtica, describe faltantes y distribución, y explora su grilla con mapas. No completa FUL-105: faltan EDA de MERRA-2 e IMERG, análisis temporal y revisión científica de la agregación regional.

## Procedencia e integridad verificadas

El archivo local `data/raw/nasa/gldas/GLDAS_NOAH025_M.A200501.021.nc4` fue obtenido el **2026-11-14 20:49 UTC** mediante el flujo interactivo Earthdata Login de `earthaccess`; el manifiesto registra autenticación, descarga de un archivo, lectura NetCDF4 e inspección exitosas. No se guardaron credenciales en el repositorio.

| Campo | Valor observado |
| --- | --- |
| Producto / versión | GLDAS Noah `GLDAS_NOAH025_M` / `2.1` |
| Variable | `SoilMoi0_10cm_inst` |
| Colección / gránulo | `C1342986036-GES_DISC` / `G1413723174-GES_DISC` |
| Período | 2005-01-01 a 2005-01-31 UTC |
| Tamaño | 25.075.859 bytes (23,9142 MB indicados por CMR) |
| SHA-256 | `5fe42fc81dae292f3be27c3b3460249609a3aa1699532edba25a88fa53b08593` |
| Formato y estructura | NetCDF4; `time=1`, `bnds=2`, `lat=600`, `lon=1440`; variable `float32`, forma `[1,600,1440]` |
| Unidad y atributos de almacenamiento | `kg m-2`; `_FillValue=-9999`, `missing_value=-9999`, `cell_methods=time: mean`; no hay `scale_factor` ni `add_offset` |

El SHA-256 calculado localmente coincide con el manifiesto y con el registro de la muestra GLDAS en [contraste_fuentes.md](contraste_fuentes.md). La apertura se hizo sin decodificación CF ni aplicación de máscara/escala. Por tanto, los estadísticos siguientes describen los valores numéricos almacenados, reportados con la unidad declarada; no se aplicó conversión. La unidad y los metadatos del modelo no equivalen a validación independiente del contenido físico.

## QA y resumen del rectángulo

La selección inclusiva `138,-38,153,-24` devuelve 56 latitudes (`-37,875` a `-24,125`) por 60 longitudes (`138,125` a `152,875`): **3.360 celdas**. Es una selección rectangular sobre la grilla global, no la máscara hidrográfica Murray–Darling.

| Indicador sobre el rectángulo | Resultado observado |
| --- | ---: |
| Celdas válidas | 3.045 |
| Celdas faltantes (`_FillValue`/`missing_value` o no finitas) | 315 |
| Cobertura válida | 90,625 % |
| Mínimo válido | 5,5918 kg m⁻² |
| Mediana | 14,6866 kg m⁻² |
| Media aritmética sin ponderación por área | 16,0753 kg m⁻² |
| Máximo válido | 38,2782 kg m⁻² |

La media supera a la mediana en esta muestra; estos resúmenes describen un solo campo mensual y no caracterizan por sí solos la forma completa de su distribución. El cálculo asigna el mismo peso a cada celda válida. No es un promedio ponderado por área ni una estimación de toda la cuenca.

No aparecieron variables candidatas de calidad por nombre en el archivo. Los valores fill se excluyen del resumen; el cero se conserva como válido. Las pruebas automatizadas verifican por separado ceros, fill, NaN, selección con latitudes descendentes, caja sin celdas, campo totalmente faltante, archivo ausente, coordenadas inválidas y variable ausente. Sus NetCDF son fixtures sintéticos, no datos científicos.

## Notebook y gráficos

El notebook reproducible es [ful_105_eda_gldas_200501.ipynb](../research/notebooks/ful_105_eda_gldas_200501.ipynb). Su copia ejecutada se guarda localmente como `research/notebooks/ful_105_eda_gldas_200501.executed.ipynb`; no se versiona y se regenera con:

```powershell
uv run jupyter nbconvert --to notebook --execute research/notebooks/ful_105_eda_gldas_200501.ipynb --output ful_105_eda_gldas_200501.executed.ipynb --output-dir research/notebooks
```

Produce dos figuras: una con el mapa global y el mapa de la selección rectangular, y otra con el histograma global de valores válidos. Los sentinelas faltantes se enmascaran para graficar. El mapa rectangular incluye celdas fuera del límite de la cuenca; ninguno de los gráficos es una máscara oficial ni un promedio regional.

## Límites científicos y contexto de Lucas

La guía del equipo confirma que GLDAS 2.1 es un producto modelado y registra que NASA recomienda obtener salidas posteriores al posprocesamiento de octubre de 2020 para enmascarar salidas inválidas sobre aguas continentales. El archivo de enero de 2005 declara `history` de 2019; con esta muestra no queda resuelta su condición respecto de aquel posprocesamiento. Revisar linaje, período y tratamiento de faltantes antes de elegirla para una serie. La variable mensual tiene `cell_methods=time: mean`; `_inst` identifica el campo de origen, no convierte el promedio mensual en una observación instantánea. Véanse [datasets.md](datasets.md) y [contraste_fuentes.md](contraste_fuentes.md#muestra-gldas-de-enero-de-2005-entregada-por-lucas).

Lucas documentó la fuente de la geometría MDBA, CRS, licencia y advertencias de bordes en [region_murray_darling.md](region_murray_darling.md). Ese documento también presenta ensayos exploratorios con una muestra IMERG y varias reglas de ponderación para una fecha; sus diferencias y límites no eligen un método para producción. El segmento GeoJSON versionado no es el polígono completo, y la copia completa en caché local no está disponible en este checkout. Esta EDA usa solo el rectángulo. Antes de un agregado se deben revisar con Lucas/FUL-104 la geometría completa, CRS/transformación, celdas parciales, áreas, faltantes y sensibilidad temporal.

Una muestra mensual no permite estimar tendencias, anomalías temporales, p-values, significancia ni causalidad. Tampoco se pueden atribuir a la cuenca los valores del rectángulo ni interpretar la media sin ponderación como estimación espacial oficial.

## Estado Git, CI y siguientes pasos

FUL-103 (PR #4), la consolidación de `develop` en `dev` (PR #6) y FUL-102 (PR #5) están integradas en `dev`. Esta rama FUL-105 parte del probe FUL-103, incorpora el catálogo actual de `dev` y conserva sus cambios en commits propios. El avance está publicado como [PR #7 en Draft hacia `dev`](https://github.com/Cesitar16/anomaly-zero/pull/7). No modifica los PRs ni commits de otros integrantes.

En la revisión del workflow compartido, `.github/workflows/checks.yml` aún ejecuta `pull_request` solo para `develop` y `push` solo para la antigua rama `feature/ful-103-earthdata-probe`. Además, `pyproject.toml` limita el descubrimiento predeterminado de pytest a `backend/tests`, por lo que `research/tests` requiere incluirse explícitamente. Se recomienda una corrección pequeña e independiente de infraestructura para que PRs hacia `dev` ejecuten lint y ambos grupos de pruebas; no se modificó el workflow en esta rama.

Siguientes pasos:

- **FUL-105:** integrar y revisar MERRA-2 e IMERG con procedencia verificada; armonizar unidades, soporte temporal y QA; luego comparar series mensuales de 2005–2024.
- **Lucas / FUL-104:** validar geometría, CRS, ponderación y sensibilidad de bordes antes de una media de cuenca.
- **Alaín / FUL-106:** mantener la extracción acotada y los manifiestos reproducibles para los tres productos; confirmar límites y semántica de calidad del insumo.
- Revisar el linaje GLDAS de 2005 y decidir si corresponde al producto apropiado para el período y uso analítico.

La EDA es un avance parcial y reproducible, no el cierre de FUL-105.

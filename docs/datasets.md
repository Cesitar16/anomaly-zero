# Productos NASA candidatos

FUL-103 incorpora un sondeo acotado con `earthaccess`. Se descargó y abrió una muestra GLDAS de enero de 2005; esto verifica el flujo técnico, no la validez científica de píxeles ni el análisis propuesto. La evidencia CMR de E01 confirma inventario de catálogo para 2005-2024. Véase [earthdata-probe.md](earthdata-probe.md) para IDs, parámetros, evidencia y límites.

Los productos y variables siguientes son candidatos de investigación. No se han descargado ni validado para el análisis propuesto.

| Variable | Producto | Variable del producto |
| --- | --- | --- |
| Temperatura del aire | MERRA-2 `M2TMNXSLV` | `T2M` |
| Precipitación | GPM IMERG Final V07 `GPM_3IMERGM` | `precipitation` |
| Humedad del suelo | GLDAS Noah V2.1 `GLDAS_NOAH025_M` | `SoilMoi0_10cm_inst` |

La región candidata es la cuenca Murray-Darling, Australia, para enero de 2005 a diciembre de 2024. Giovanni se usará para exploración; el acceso a archivos originales mediante Earthdata/CMR y `earthaccess` ya se probó con una muestra GLDAS global. No se han recortado grillas, validado científicamente los productos ni ejecutado análisis.

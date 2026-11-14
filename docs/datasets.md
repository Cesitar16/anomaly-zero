# Productos NASA candidatos

Los productos y variables siguientes son candidatos de investigación; tener una muestra no implica validación científica del producto, sus píxeles ni del análisis propuesto.

| Variable | Producto | Variable del producto |
| --- | --- | --- |
| Temperatura del aire | MERRA-2 `M2TMNXSLV` | `T2M` |
| Precipitación | GPM IMERG Final V07 `GPM_3IMERGM` | `precipitation` |
| Humedad del suelo | GLDAS Noah V2.1 `GLDAS_NOAH025_M` | `SoilMoi0_10cm_inst` |

La región candidata es la cuenca Murray–Darling, Australia, para enero de 2005 a diciembre de 2024. Giovanni se usará para exploración. FUL-103 añadió un sondeo acotado con `earthaccess` y descargó/abrió una muestra GLDAS global de enero de 2005, verificando el flujo técnico y algunos metadatos, no la validez científica de los píxeles. El acceso a MERRA-2 e IMERG aún debe investigarse y probarse. No se han recortado grillas ni calculado agregados de cuenca. Véase [earthdata-probe.md](earthdata-probe.md) para los IDs CMR, parámetros, evidencia y límites.

## Piloto metodológico FUL-101

Para desarrollar procedimientos de EDA antes de recibir las muestras regionales, se descargó localmente una serie **puntual** de NASA POWER: T2M mensual, comunidad AG, Wagga Wagga (NSW), 2005–2024. La respuesta API indica unidad C, fuente meteorológica MERRA2 y convención LST. El archivo original y el sidecar de procedencia están en `data/raw/` y excluidos de Git. Este piloto no valida ni reemplaza los tres productos del MVP, no representa el promedio de la cuenca y no es un resultado científico definitivo. Detalle y notebook ejecutable: `research/notebooks/01_eda_piloto_power.ipynb`.

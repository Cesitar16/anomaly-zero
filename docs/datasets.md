# Productos NASA candidatos

Los productos y variables siguientes son candidatos de investigación. No se han descargado ni validado para el análisis propuesto.

| Variable | Producto | Variable del producto |
| --- | --- | --- |
| Temperatura del aire | MERRA-2 `M2TMNXSLV` | `T2M` |
| Precipitación | GPM IMERG Final V07 `GPM_3IMERGM` | `precipitation` |
| Humedad del suelo | GLDAS Noah V2.1 `GLDAS_NOAH025_M` | `SoilMoi0_10cm_inst` |

La región candidata es la cuenca Murray–Darling, Australia, para enero de 2005 a diciembre de 2024. Giovanni se usará para exploración; el acceso a los tres productos del MVP mediante Earthdata/CMR y earthaccess debe investigarse y probarse. Todavía no se han descargado ni validado esos tres productos.

## Piloto metodológico FUL-101

Para desarrollar procedimientos de EDA antes de recibir las muestras regionales, se descargó localmente una serie **puntual** de NASA POWER: T2M mensual, comunidad AG, Wagga Wagga (NSW), 2005–2024. La respuesta API indica unidad C, fuente meteorológica MERRA2 y convención LST. El archivo original y el sidecar de procedencia están en `data/raw/` y excluidos de Git. Este piloto no valida ni reemplaza los tres productos del MVP, no representa el promedio de la cuenca y no es un resultado científico definitivo. Detalle y notebook ejecutable: `research/notebooks/01_eda_piloto_power.ipynb`.

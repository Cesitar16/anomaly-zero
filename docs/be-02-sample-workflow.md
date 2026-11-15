# BE-02: muestras GLDAS, MERRA-2 e IMERG

Este procedimiento amplía BE-01 con muestras reales y pruebas espaciales acotadas. Conserva originales/manifiestos fuera de Git, resoluciones nativas y unidades originales; no aplica conversiones ni filtros de calidad.

## Reproducción y publicación de muestras

Desde la raíz del repositorio, con Earthdata Login y uso/descarga autorizados:

    python -m backend.app.data_sources.earthdata_samples merra2 --month 2005-01 --max-mib 64
    python -m backend.app.data_sources.earthdata_samples imerg_final --month 2005-01 --max-mib 64

GLDAS reutiliza la muestra local verificada en BE-01. Cada archivo se acompaña de manifiesto con identidad del granule, tamaño, SHA-256 y metadatos observados. No se sobrescriben muestras existentes. Archivo y manifiesto se preparan antes de publicarse; su publicación no es una transacción conjunta. Si falla la publicación del manifiesto, el flujo intenta limpiar el archivo nuevo y preserva originales válidos.

El `relative_path` del manifiesto se resuelve desde `relative_path_base`, que registra el directorio de trabajo desde el que se ejecutó el comando. Los tamaños reportados por earthaccess/CMR se expresan en MiB y el tamaño local en bytes.

## Estructura inspeccionada sin transformaciones

| Producto y archivo | Variable / soporte | Dimensiones y resolución nativa | Unidad y faltantes | Transformaciones |
|---|---|---|---|---|
| GLDAS Noah 2.1, `GLDAS_NOAH025_M.A200501.021.nc4` | `SoilMoi0_10cm_inst`, NetCDF4 | 1×600×1440; 0.25° | kg m-2; fill -9999 | Ninguna |
| MERRA-2 `M2TMNXSLV`, `MERRA2_300.tavgM_2d_slv_Nx.200501.nc4` | `T2M`, NetCDF4/HDF5 | 1×361×576; 0.5°×0.625° | K; fill 999999986991104.0 | Ninguna; sin escala/offset |
| IMERG Final `GPM_3IMERGM`, enero `3B-MO.MS.MRG.3IMERG.20050101-S000000-E235959.01.V07B.HDF5` | `Grid/precipitation`, HDF5 | 1×3600×1800; 0.1° | mm/hr; fill -9999.900390625, CodeMissingValue -9999.9 | Ninguna; sin escala/offset |

- GLDAS y MERRA-2 se leen como NetCDF4 con `decode_cf=False`, `mask_and_scale=False` y `decode_times=False`. Sus variables tienen ejes `time,lat,lon`.
- MERRA-2 declara VersionID `5.12.4`, período 2005-01-01 a 2005-01-31 y tiempo raw 0 minutos desde 2005-01-01 00:30. No reporta candidatos QA.
- IMERG enero declara `ProductVersion=V07B`, DOI de colección `GPM/IMERG/3B-MONTH/07`, período enero 2005 e intervalo MONTH. El atributo `DimensionNames=time,lon,lat` permite resolver ejes cuando h5py no expone etiquetas DIMENSION. Las coordenadas ascendentes se validan contra las longitudes de ejes antes de orientar los datos. Candidatos QA `Grid/precipitationQualityIndex` y `Grid/randomError` no se interpretan ni aplican.
- Febrero de 2005 también se abrió con el lector IMERG/HDF5. Se conserva como archivo mensual separado; no se combinaron ni promediaron sus valores con enero.
- Los valores cero válidos se conservan; los faltantes se identifican con el fill correspondiente. No se aplican escalas, offsets, conversiones, agregación de valores ni selección de calidad.

Los tamaños y hashes verificados son:

- GLDAS enero: 25,075,859 bytes; SHA-256 `5fe42fc81dae292f3be27c3b3460249609a3aa1699532edba25a88fa53b08593`.
- MERRA-2 enero: 54,419,597 bytes; SHA-256 `103d95aa3ffe9b8d7e98caea5f6a764831bad3b70155370d3a84c2dfd95616c6`.
- IMERG enero: 18,028,945 bytes; SHA-256 `bac3b9bc5ee8cc3eb1e5fe844778d54fd86e2b722813055b37f3872e6e4c73d5`.
- IMERG febrero: 18,706,618 bytes; SHA-256 `fe0aa14ac528459d485ca5a8685f2d4e4019992b976379ca2880a3422bc85e24`; tamaño y hash coincidieron con el manifiesto.

Las identidades candidatas de catálogo son MERRA-2 concept ID `C1276812859-GES_DISC`, versión `5.12.4`, e IMERG mensual `C2723754851-GES_DISC`, versión de colección `07`. El archivo IMERG indica `V07B`; Lucas debe resolver esta nomenclatura en FUL-104. Referencias: [MERRA-2 mensual](https://doi.org/10.5067/AP1B0BA5PD2K), [IMERG Final mensual](https://cmr.earthdata.nasa.gov/search/site/collections/directory/GES_DISC/gov.nasa.eosdis), [GLDAS Noah mensual 2.1](https://doi.org/10.5067/SXAVCZFAQLNO). No se midieron tiempos de descarga.

## Geografía, QA y diccionario de tabla

Se reutilizó sin modificar el polígono oficial MDBA de E01, EPSG:4326, SHA-256 `d36fe31424758cc4fb8eef25e21b835bb5c05c793c746e8a1eb7b5a5841f6a53`. E01 conserva procedencia, servicio FeatureServer, atribución y licencia.

La regla de inclusión es centro de celda dentro del polígono; incluye bordes exteriores y de huecos, excluye interiores de huecos. Grillas nativas, sin remuestreo. Resultados reales:

| Producto / período | Centros dentro (denominador) | Finito/no-fill | Faltantes | Porcentaje válido |
|---|---:|---:|---:|---:|
| GLDAS enero | 1,617 | 1,615 | 2 | 99.8763% |
| MERRA-2 enero | 323 | 323 | 0 | 100% |
| IMERG enero | 10,092 | 10,092 | 0 | 100% |
| IMERG febrero | 10,092 | 10,092 | 0 | 100% |

El denominador cuenta centros de celda, no superficie cubierta. Excluye celdas cuyo centro cae fuera aunque su borde cruce la cuenca y no pondera área. “Válido” significa finito y distinto del fill; no implica que candidatos QA de IMERG se aplicaran ni equivale a aprobación científica.

Los CSV locales por mes contienen hasta 20 filas cada uno. La tabla temporal de prueba `data/derived/be02_imerg_2005-01_02.csv` concatena enero y febrero (40 filas; 20 centros compartidos entre ambos meses). No promedia valores ni representa una climatología. Sus referencias a originales/manifiestos son rutas relativas a la raíz del repositorio. Campos:
- `period`: mes de referencia;
- `product`, `version`, `variable`: identidad y variable reportadas;
- `latitude`, `longitude`: coordenadas del centro de celda;
- `value`, `unit`: valor crudo y unidad original;
- `quality_candidates`, `quality_filter_applied`: candidatos listados y si se aplicó un filtro (False);
- `original_file`, `manifest`: rutas al original y manifiesto.

El conteo de faltantes cubre todos los centros seleccionados; los CSV están limitados a 20 filas por mes. Estas muestras no son una serie de veinte años, promedio de cuenca, máscara de producción ni producto científico aprobado.

## Ampliación temporal acotada

Para IMERG mensual, el tamaño observado enero+febrero fue 36,735,563 bytes; promedio de dos muestras: 18,367,781.5 bytes por mes. Extrapolación a 12 meses: aproximadamente 220,413,378 bytes (210.2 MiB / 0.205 GiB), suponiendo tamaño constante. Con límite de 24 MiB por archivo, el máximo para 12 meses es 288 MiB (0.281 GiB), antes de manifiestos y temporales. Los tamaños mensuales pueden variar; todavía falta comprobar el resto de 2005. No se midieron tiempos de transferencia.

Para 240 meses por producto (enero de 2005–diciembre de 2024), con tamaño constante igual a la muestra de enero: aproximadamente 23,405,856,240 bytes (21.80 GiB): MERRA-2 12.16 GiB, IMERG 4.03 GiB y GLDAS 5.60 GiB. No incluye manifiestos, temporales ni índices. Es una extrapolación, no una descarga histórica.

## Verificación y pendientes

- Pruebas offline cubren lectores/ejes distintos, fill frente a cero, dispatch NetCDF/HDF5 y máscara espacial. Actions pasó en HEAD `e2174d57ca0d58a320a01280ed71d724ba6c7c7c` (run `43655308235`): backend y frontend.
- La prueba de febrero se ejecutó sobre el archivo local preexistente, sin sobrescribirlo ni descargarlo de nuevo. El CSV de 40 filas es un primer chequeo de ensamblaje temporal de dos meses, no una serie anual.
- Faltan marzo–diciembre 2005 para llegar a 12 meses de IMERG. FUL-104, Lucas y César deben revisar identidades/versiones, unidades, calidad, geografía y utilidad para EDA. No se aprueban decisiones científicas en BE-02.
- Sin conversiones, tendencias, significancia, mapas completos ni contratos finales.

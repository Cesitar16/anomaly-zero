# BE-02: muestras GLDAS, MERRA-2 e IMERG

Este procedimiento amplía BE-01 con muestras reales y pruebas espaciales acotadas. Conserva originales/manifiestos fuera de Git, resoluciones nativas y unidades originales; no aplica conversiones ni filtros de calidad.

## Reproducción y publicación de muestras

Desde la raíz del repositorio, con el entorno virtual del proyecto activo, Earthdata Login y uso/descarga autorizados:

    python -m backend.app.data_sources.earthdata_samples merra2 --month 2005-01 --max-mib 64
    python -m backend.app.data_sources.earthdata_samples imerg_final --month 2005-01 --max-mib 64

GLDAS reutiliza la muestra local verificada en BE-01. Cada archivo se acompaña de manifiesto con identidad del granule, tamaño, SHA-256 y metadatos observados. No se sobrescriben muestras existentes. Archivo y manifiesto se preparan antes de publicarse; su publicación no es una transacción conjunta. Si falla la publicación del manifiesto, el flujo intenta limpiar el archivo nuevo y preserva originales válidos.

El `relative_path` de cada manifiesto se resuelve desde el `relative_path_base` guardado en ese mismo manifiesto. Las columnas `original_file` y `manifest` de los CSV son referencias distintas: en el CSV anual original, las 20 filas de febrero conservan una ruta absoluta de la máquina de Jod y los demás meses usan rutas relativas desde la raíz del checkout `anomaly-zero-be02`. La copia portable normaliza ambas columnas a rutas `data/raw/...` y declara explícitamente esa raíz lógica en el README del handoff. Los tamaños reportados por earthaccess/CMR se expresan en MiB y el tamaño local en bytes.

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
- Marzo–diciembre de 2005 se descargaron como diez archivos mensuales separados. Los diez manifiestos coinciden en tamaño y SHA-256; cada HDF5 se abrió sin escalas, offsets ni conversiones.
- Los valores cero válidos se conservan; los faltantes se identifican con el fill correspondiente. No se aplican escalas, offsets, conversiones, agregación de valores ni selección de calidad.

Los tamaños y hashes verificados son:

- GLDAS enero: 25,075,859 bytes; SHA-256 `5fe42fc81dae292f3be27c3b3460249609a3aa1699532edba25a88fa53b08593`.
- MERRA-2 enero: 54,419,597 bytes; SHA-256 `103d95aa3ffe9b8d7e98caea5f6a764831bad3b70155370d3a84c2dfd95616c6`.
- IMERG enero: 18,028,945 bytes; SHA-256 `bac3b9bc5ee8cc3eb1e5fe844778d54fd86e2b722813055b37f3872e6e4c73d5`.
- IMERG febrero: 18,706,618 bytes; SHA-256 `fe0aa14ac528459d485ca5a8685f2d4e4019992b976379ca2880a3422bc85e24`; tamaño y hash coincidieron con el manifiesto.
- IMERG marzo: 18,870,125 bytes; SHA-256 `ddc2aa593acf426ba0314a2deea1ab67292936deae7dbfa7a2450a528bc76e38`.
- IMERG abril: 18,937,100 bytes; SHA-256 `7cc4510027369ac01919d8e3eb37dba1b38f5947e8d66fff37092ae4d78e415f`.
- IMERG mayo: 19,223,538 bytes; SHA-256 `18968b856e22a83a783807cdc7f6dcf55fed8399bc4ba7abfca0bcea583373fd`.
- IMERG junio: 19,297,239 bytes; SHA-256 `f5bf5b041a941de0274e86851f3d3a32265c9dc314b8626e728ae1e4896ca92c`.
- IMERG julio: 18,919,255 bytes; SHA-256 `6bdc0ab9dcc8844adcd997f3ad48b21491c2bc03f8aab30ef75167c68c877e0d`.
- IMERG agosto: 18,895,129 bytes; SHA-256 `02fb3b1fde299ec18d4855a7cbfa3a291bbf1536da508a158db04f7291b507e6`.
- IMERG septiembre: 18,958,777 bytes; SHA-256 `a11525d4772209293adcff54209d0e83d405ce593e89a6767e567088673fc126`.
- IMERG octubre: 18,659,588 bytes; SHA-256 `2010f5adf42e99ceec0c968399360944e13ed2c06ba5e68f65984ed4b21c6529`.
- IMERG noviembre: 18,941,510 bytes; SHA-256 `378adc0ff8210c10354f694301f2536444cea73ca557838240ebc71cdc93daf8`.
- IMERG diciembre: 18,525,166 bytes; SHA-256 `6566b1594efc9163cc4952767df58d9396cd2db206c4baa1f6540b04077661c3`.

Los manifiestos de marzo–diciembre se contrastaron con el tamaño y hash SHA-256 locales; los diez archivos están por debajo del límite de 24 MiB.

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
| IMERG marzo–diciembre (cada mes) | 10,092 | 10,092 | 0 | 100% |

El denominador cuenta centros de celda, no superficie cubierta. Excluye celdas cuyo centro cae fuera aunque su borde cruce la cuenca y no pondera área. “Válido” significa finito y distinto del fill; no implica que candidatos QA de IMERG se aplicaran ni equivale a aprobación científica.

Los CSV locales por mes contienen hasta 20 filas cada uno. La tabla `data/derived/be02_imerg_2005-01_02.csv` conserva el primer ensamblaje de enero y febrero (40 filas). La tabla `data/derived/be02_imerg_2005-01_12.csv` concatena los doce meses (240 filas; 20 centros compartidos por todos los meses). Ambas conservan valores mensuales crudos, sin promedios, conversiones ni climatología. La copia `data/derived/be02_handoff/be02_imerg_2005-01_12.portable.csv` corrige solo las dos columnas de referencias, conserva orden/valores/unidades y resuelve desde la base lógica `anomaly-zero-be02/`; las rutas todavía apuntan a los originales locales, no prueban acceso desde otro equipo. Campos:
- `period`: mes de referencia;
- `product`, `version`, `variable`: identidad y variable reportadas;
- `latitude`, `longitude`: coordenadas del centro de celda;
- `value`, `unit`: valor crudo y unidad original;
- `quality_candidates`, `quality_filter_applied`: candidatos listados y si se aplicó un filtro (False);
- `original_file`, `manifest`: rutas al original y manifiesto.

El conteo de faltantes cubre todos los centros seleccionados; los CSV están limitados a 20 filas por mes. Estas muestras no son una serie de veinte años, promedio de cuenca, máscara de producción ni producto científico aprobado.

## Ampliación temporal acotada

Los doce originales IMERG de 2005 suman 225,962,990 bytes (215.5 MiB); el promedio de tamaño fue 18,830,249 bytes (17.958 MiB) por archivo. El mayor fue junio, con 19,297,239 bytes (18.403 MiB). Todos quedaron por debajo del límite de 24 MiB; el máximo autorizado para doce archivos sigue siendo 288 MiB antes de manifiestos y temporales. No se midieron tiempos de transferencia.

Para descargar solo marzo–diciembre de 2005 desde una PowerShell autenticada con Earthdata, situada en la raíz del repositorio, ejecutar:

```powershell
foreach ($month in 3..12) {
    $period = "2005-{0:D2}" -f $month
    python -m backend.app.data_sources.earthdata_samples imerg_final --month $period --max-mib 24
    if ($LASTEXITCODE -ne 0) { throw "Descarga o validación fallida para $period; se detuvo el lote." }
}
```

El lote marzo–diciembre se ejecutó secuencialmente desde PowerShell. CMR y el archivo local se limitaron a 24 MiB; la herramienta rechazó cualquier ruta de muestra/manifiesto ya existente, sin sobrescribirla. Si un mes falla, el lote se detiene y los meses restantes se pueden ejecutar ajustando el rango. Enero y febrero no formaron parte de esta descarga.

Para 240 meses por producto (enero de 2005–diciembre de 2024), con tamaño constante igual a la muestra de enero: aproximadamente 23,405,856,240 bytes (21.80 GiB): MERRA-2 12.16 GiB, IMERG 4.03 GiB y GLDAS 5.60 GiB. No incluye manifiestos, temporales ni índices. Es una extrapolación, no una descarga histórica.

## Verificación y pendientes

- Pruebas offline cubren lectores/ejes distintos, fill frente a cero, dispatch NetCDF/HDF5 y máscara espacial. Actions pasó en HEAD `f6c2d63` (run `43662284990`, backend y frontend). El run `43661111462` pasó en el HEAD previo `20d7a7d`; `43660988203` pertenece al HEAD histórico `baaedad`.
- La prueba de febrero se ejecutó sobre el archivo local preexistente, sin sobrescribirlo ni descargarlo de nuevo. Los diez meses nuevos abrieron correctamente con HDF5; QA espacial reportó 10,092 centros válidos y 0 faltantes en cada mes, con el mismo polígono E01. El CSV anual de 240 filas conserva veinte centros por mes y no agrega valores.
- FUL-104, Lucas y César deben revisar identidades/versiones, unidades, calidad, geografía y utilidad para EDA. No se aprueban decisiones científicas en BE-02.
- Sin conversiones, tendencias, significancia, mapas completos ni contratos finales.

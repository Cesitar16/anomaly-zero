# BE-02: muestras MERRA-2 e IMERG

Este procedimiento amplía el adaptador BE-01 sin cambiar las unidades ni aplicar máscaras de calidad automáticamente.

## Muestras limitadas

Desde la raíz del repositorio, una vez configurado Earthdata Login y con uso/descarga autorizados:

    python -m backend.app.data_sources.earthdata_samples merra2 --month 2005-01 --max-mib 64
    python -m backend.app.data_sources.earthdata_samples imerg_final --month 2005-01 --max-mib 64
    python -m backend.app.data_sources.earthdata_spatial imerg_final data/raw/nasa/imerg_final/<archivo>.HDF5 data/raw/nasa/imerg_final/<archivo>.HDF5.manifest.json ../E01/geometrias/murray_darling.geojson --csv data/derived/be02_imerg_2005-01.csv --max-rows 20

Cada comando consulta CMR para el mes y caja de descubrimiento, exige el short name, versión y concept ID configurados, verifica el tamaño antes de autenticar y descargar, abre el formato obtenido, calcula SHA-256 y prepara un manifiesto antes de publicar. Los archivos quedan bajo `data/raw/nasa/<product-key>/`, excluidos de Git. Se rehúsa sobrescribir muestras existentes. La publicación de archivo y manifiesto no es una transacción conjunta; si falla la segunda publicación, la rutina intenta eliminar solo el archivo nuevo.

El `relative_path` de estos manifiestos se resuelve contra `relative_path_base`, que registra el directorio de trabajo actual al ejecutar el comando. Las unidades son MiB del tamaño reportado por `earthaccess`/CMR y bytes reales por separado.

## Lectura sin transformaciones

- MERRA-2 `M2TMNXSLV`, V5.12.4, variable `T2M`: el lector NetCDF4 reporta dimensiones, coordenadas, unidad, fechas y atributos, con `decode_cf=False`, `mask_and_scale=False` y `decode_times=False`.
- IMERG Final `GPM_3IMERGM`, V07, variable HDF5 `Grid/precipitation`: el lector informa grupos y rutas de datasets, atributos y ejes etiquetados. Reporta candidatos QA por ruta; no interpreta ni aplica los flags. Los ejes HDF5 sin etiquetas se mantienen como ambiguos.
- Los ceros válidos se conservan. El fill se representa como nulo solo en el preview y conserva el valor crudo en los atributos. No se aplican factores de escala, offsets, conversiones, agregación ni selección de calidad.

Identidades y DOI contrastados en el catálogo del proyecto y fuentes NASA actuales: [MERRA-2 mensual](https://doi.org/10.5067/AP1B0BA5PD2K), [IMERG Final mensual V07](https://cmr.earthdata.nasa.gov/search/site/collections/directory/GES_DISC/gov.nasa.eosdis), y [GLDAS Noah mensual 2.1](https://doi.org/10.5067/SXAVCZFAQLNO). El catálogo NASA consultado identifica para MERRA-2 el concept ID `C1276812859-GES_DISC` y versión `5.12.4`; para IMERG mensual, `C2723754851-GES_DISC`, versión `07`. La consulta autenticada CMR desde el entorno del agente devolvió ConnectionError; por ello no hay en esta entrega gránulo MERRA-2 o IMERG descargado ni inspeccionado. Reintentar los comandos desde un proceso con acceso NASA y conservar su resultado, sin sustituir la fuente ni interpretar el error de red como discrepancia científica.

## Geometría candidata y contrato de la tabla

Se reutiliza sin modificar el polígono oficial MDBA que E01 conserva en `E01/geometrias/murray_darling.geojson`, EPSG:4326, SHA-256 `d36fe31424758cc4fb8eef25e21b835bb5c05c793c746e8a1eb7b5a5841f6a53`. Procedencia, servicio FeatureServer, atribución y licencia se mantienen en E01 y `docs/region_murray_darling.md`.

Una primera tabla reproducible debe incluir los centros de celda cubiertos por el polígono: incluye los bordes exteriores y los bordes de huecos, y excluye el interior de estos. Debe mantener cada resolución nativa y registrar por separado:
- celdas con centro dentro del polígono;
- celdas de ese denominador con dato finito y distinto del fill;
- celdas faltantes y porcentaje válido con denominador explícito.

Este conteo no representa superficie cubierta. Excluye celdas cuyo centro queda fuera aunque su borde cruce la cuenca y no pondera área. No utilizarlo como máscara de producción ni como promedio científico sin revisión de Lucas y César. Registrar en cada fila período, producto/versión, variable, latitud/longitud del centro, valor crudo, unidad original, candidato QA, archivo original y manifiesto. Esos campos conservan trazabilidad; no significan que un mes sea una serie de veinte años.

La tabla con valores reales y la comprobación del límite aún están pendientes: faltan muestras accesibles en este proceso. No se genera un CSV vacío ni se presenta una muestra global como estadística de cuenca.

## Volumen histórico: estimación, no descarga

E01/catálogo registra para enero de 2005 51.8986 MiB para MERRA-2 y 17.1937 MiB para IMERG según CMR; GLDAS tiene 23.9142 MiB reportados y su archivo local documenta 25,075,859 bytes. Suponiendo 240 meses por producto y tamaño constante igual al granule de enero de 2005, el total de referencia es aproximadamente 22,322 MiB (21.80 GiB binarios): MERRA-2 12.16 GiB, IMERG 4.03 GiB y GLDAS 5.60 GiB. No incluye manifiestos, copias temporales ni índices. Los tamaños MERRA-2 e IMERG no fueron medidos en descargas de este entorno; las diferencias mensuales y revisiones del proveedor pueden cambiar el total. No se descargaron los 240 meses.

## Evidencia comprobada y pendiente

- **H1 / GLDAS:** desde PowerShell normal se reutilizó la muestra local de enero de 2005, sin re-descarga ni modificación. Tamaño calculado `25,075,859` bytes y SHA-256 `5fe42fc81dae292f3be27c3b3460249609a3aa1699532edba25a88fa53b08593` coinciden con el manifiesto. Se abrió como NetCDF4: `time=1`, `bnds=2`, `lat=600`, `lon=1440`; variable `SoilMoi0_10cm_inst`, unidad `kg m-2`, fill `-9999.0`. El preview de las cuatro celdas iniciales contiene fill y no representa cobertura regional.
- **H2 pendiente:** obtener muestras NASA auténticas MERRA-2 e IMERG, medir tamaños y tiempos, y revisar sus metadatos reales antes de aceptar las identidades candidatas.
- **H3 pendiente:** ejecutar la prueba espacial sobre grillas auténticas verificadas y generar una tabla CSV con manifiestos localizables. Esta prueba usa centros de celda; no estima superficie cubierta.
- **Revisión científica pendiente:** FUL-104, Lucas y César deben revisar productos, unidades, QA y método. No se aplican conversiones ni se autoaprueban decisiones científicas.


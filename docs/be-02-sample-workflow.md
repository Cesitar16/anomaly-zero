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

- MERRA-2 candidato `M2TMNXSLV`, versión de archivo `5.12.4`, variable `T2M`: lector NetCDF4 con `decode_cf=False`, `mask_and_scale=False`, `decode_times=False`. No aplicó transformaciones.
- IMERG Final candidato `GPM_3IMERGM`, variable HDF5 `Grid/precipitation`: el archivo declara `ProductVersion=V07B` y `DimensionNames=time,lon,lat`. h5py devuelve vacías las etiquetas DIMENSION, así que el lector ahora recurre a `DimensionNames`; el QA valida esas posiciones contra las longitudes de `Grid/lat` y `Grid/lon` antes de orientar el arreglo.
- En el archivo IMERG real, la grilla declara registro CENTER, origen SOUTHWEST y resolución de 0.1°; latitudes y longitudes están almacenadas en orden ascendente. La variable mide 1×3600×1800 en orden `time,lon,lat`. Se observan candidatos QA `Grid/precipitationQualityIndex` y `Grid/randomError`; no se interpretan ni aplican.
- Los ceros válidos se conservan. El fill queda como nulo solo en el preview y mantiene el valor crudo en atributos. No se aplican escalas, offsets, conversiones, agregación temporal o selección de calidad.

### Muestras autenticadas del usuario (enero de 2005)

- **MERRA-2:** `MERRA2_300.tavgM_2d_slv_Nx.200501.nc4`, 54,419,597 bytes, SHA-256 `103d95aa3ffe9b8d7e98caea5f6a764831bad3b70155370d3a84c2dfd95616c6`. El archivo declara `M2TMNXSLV`, VersionID `5.12.4`, 2005-01-01 a 2005-01-31, NetCDF-4/HDF-5. `T2M`: forma 1×361×576, `time,lat,lon`, unidad K, fill `999999986991104.0`; atributos de escala/offset ausentes; grilla global 0.5°×0.625°. Tiempo raw: 0 minutos desde 2005-01-01 00:30. Sin candidatos QA reportados.
- **IMERG:** `3B-MO.MS.MRG.3IMERG.20050101-S000000-E235959.01.V07B.HDF5`, 18,028,945 bytes, SHA-256 `bac3b9bc5ee8cc3eb1e5fe844778d54fd86e2b722813055b37f3872e6e4c73d5`. El header declara el período 2005-01-01/31, intervalo MONTH, DOI GPM/IMERG/3B-MONTH/07 y `ProductVersion=V07B`. `Grid/precipitation`: forma 1×3600×1800, `time,lon,lat`, unidad mm/hr, fill `-9999.900390625`, `CodeMissingValue=-9999.9`; escalas/offsets ausentes. Los cuatro valores del preview global inicial son fill, no describen la cuenca.
- La ejecución guardó manifiesto por archivo y retornó `downloaded_and_opened`; ambos originales quedan fuera de Git. No se registró duración de transferencia, así que no se presenta un tiempo de descarga medido. El período de los datos sí está registrado arriba.

El catálogo/fuentes NASA consultados identifican MERRA-2 con concept ID `C1276812859-GES_DISC`, versión `5.12.4`; IMERG mensual con `C2723754851-GES_DISC`, versión de colección `07`. Estos candidatos concuerdan con los metadatos observados, que muestran `V07B` en el archivo IMERG; la diferencia de nomenclatura debe revisarse en FUL-104. DOI: [MERRA-2 mensual](https://doi.org/10.5067/AP1B0BA5PD2K), [IMERG Final mensual V07](https://cmr.earthdata.nasa.gov/search/site/collections/directory/GES_DISC/gov.nasa.eosdis), [GLDAS Noah mensual 2.1](https://doi.org/10.5067/SXAVCZFAQLNO). La consulta CMR del agente devolvió ConnectionError; el usuario obtuvo las dos muestras con ejecución autenticada local. Esto evidencia descarga y apertura, no aprobación científica de identidades, unidades o QA.

## Geometría candidata y contrato de la tabla

Se reutiliza sin modificar el polígono oficial MDBA que E01 conserva en `E01/geometrias/murray_darling.geojson`, EPSG:4326, SHA-256 `d36fe31424758cc4fb8eef25e21b835bb5c05c793c746e8a1eb7b5a5841f6a53`. Procedencia, servicio FeatureServer, atribución y licencia se mantienen en E01 y `docs/region_murray_darling.md`.

Una primera tabla reproducible debe incluir los centros de celda cubiertos por el polígono: incluye los bordes exteriores y los bordes de huecos, y excluye el interior de estos. Debe mantener cada resolución nativa y registrar por separado:
- celdas con centro dentro del polígono;
- celdas de ese denominador con dato finito y distinto del fill;
- celdas faltantes y porcentaje válido con denominador explícito.

Este conteo no representa superficie cubierta. Excluye celdas cuyo centro queda fuera aunque su borde cruce la cuenca y no pondera área. No utilizarlo como máscara de producción ni como promedio científico sin revisión de Lucas y César. Registrar en cada fila período, producto/versión, variable, latitud/longitud del centro, valor crudo, unidad original, candidato QA, archivo original y manifiesto. Esos campos conservan trazabilidad; no significan que un mes sea una serie de veinte años.

La tabla con valores reales y la comprobación del límite aún están pendientes: faltan muestras accesibles en este proceso. No se genera un CSV vacío ni se presenta una muestra global como estadística de cuenca.

## Volumen histórico: estimación, no descarga

Los tamaños medidos de las muestras de enero de 2005 son MERRA-2 54,419,597 bytes, IMERG 18,028,945 bytes y GLDAS 25,075,859 bytes. Suponiendo 240 meses por producto (enero de 2005–diciembre de 2024) y tamaño constante igual a esa muestra, la referencia es aproximadamente 23,405,856,240 bytes (21.80 GiB): MERRA-2 12.16 GiB, IMERG 4.03 GiB y GLDAS 5.60 GiB. No incluye manifiestos, copias temporales ni índices; el tamaño mensual puede variar. Es una extrapolación desde tres archivos, no una descarga de 240 meses. No se registraron tiempos de transferencia, así que no hay estimación de duración observada.

## Evidencia comprobada y pendiente

- **H1 / GLDAS:** desde PowerShell con el grupo Administrators habilitado (SID S-1-5-32-544) se reutilizó la muestra local de enero de 2005, sin re-descarga ni modificación. Tamaño calculado `25,075,859` bytes y SHA-256 `5fe42fc81dae292f3be27c3b3460249609a3aa1699532edba25a88fa53b08593` coinciden con el manifiesto. Se abrió como NetCDF4: `time=1`, `bnds=2`, `lat=600`, `lon=1440`; variable `SoilMoi0_10cm_inst`, unidad `kg m-2`, fill `-9999.0`. El preview de las cuatro celdas iniciales contiene fill y no representa cobertura regional.
- **H2 / MERRA-2 e IMERG:** el usuario descargó y abrió una muestra mensual de cada producto; tamaños, SHA-256 y metadatos observados están arriba. `DimensionNames` real de IMERG no coincidía con etiquetas DIMENSION h5py; el lector y pruebas offline ahora usan el atributo y validan tamaños de coordenadas. Sin duración de transferencia observada. Lucas debe verificar IDs/versiones/unidades/QA en FUL-104.
- **H3 pendiente:** ejecutar la prueba espacial sobre grillas auténticas verificadas y generar una tabla CSV con manifiestos localizables. Esta prueba usa centros de celda; no estima superficie cubierta.
- **Revisión científica pendiente:** FUL-104, Lucas y César deben revisar productos, unidades, QA y método. No se aplican conversiones ni se autoaprueban decisiones científicas.


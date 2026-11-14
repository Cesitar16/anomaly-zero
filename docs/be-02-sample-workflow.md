# BE-02: muestras MERRA-2 e IMERG

Este procedimiento ampl�a el adaptador BE-01 sin cambiar las unidades ni aplicar m�scaras de calidad autom�ticamente.

## Muestras limitadas

Desde la ra�z del repositorio, una vez configurado Earthdata Login y con uso/descarga autorizados:

    python -m backend.app.data_sources.earthdata_samples merra2 --month 2005-01 --max-mib 64
    python -m backend.app.data_sources.earthdata_samples imerg_final --month 2005-01 --max-mib 64
    python -m backend.app.data_sources.earthdata_spatial imerg_final data/raw/nasa/imerg_final/<archivo>.HDF5 data/raw/nasa/imerg_final/<archivo>.HDF5.manifest.json ../E01/geometrias/murray_darling.geojson --csv data/derived/be02_imerg_2005-01.csv --max-rows 20

Cada comando consulta CMR para el mes y caja de descubrimiento, exige el short name, versi�n y concept ID configurados, verifica el tama�o antes de autenticar y descargar, abre el formato obtenido, calcula SHA-256 y prepara un manifiesto antes de publicar. Los archivos quedan bajo \`data/raw/nasa/<product-key>/\`, excluidos de Git. Se reh�sa sobrescribir muestras existentes. La publicaci�n de archivo y manifiesto no es una transacci�n conjunta; si falla la segunda publicaci�n, la rutina intenta eliminar solo el archivo nuevo.

El \`relative_path\` de estos manifiestos se resuelve contra \`relative_path_base\`, que registra el directorio de trabajo actual al ejecutar el comando. Las unidades son MiB del tama�o reportado por \`earthaccess\`/CMR y bytes reales por separado.

## Lectura sin transformaciones

- MERRA-2 \`M2TMNXSLV\`, V5.12.4, variable \`T2M\`: el lector NetCDF4 reporta dimensiones, coordenadas, unidad, fechas y atributos, con \`decode_cf=False\`, \`mask_and_scale=False\` y \`decode_times=False\`.
- IMERG Final \`GPM_3IMERGM\`, V07, variable HDF5 \`Grid/precipitation\`: el lector informa grupos y rutas de datasets, atributos y ejes etiquetados. Reporta candidatos QA por ruta; no interpreta ni aplica los flags. Los ejes HDF5 sin etiquetas se mantienen como ambiguos.
- Los ceros v�lidos se conservan. El fill se representa como nulo solo en el preview y conserva el valor crudo en los atributos. No se aplican factores de escala, offsets, conversiones, agregaci�n ni selecci�n de calidad.

Identidades y DOI contrastados en el cat�logo del proyecto y fuentes NASA actuales: [MERRA-2 mensual](https://doi.org/10.5067/AP1B0BA5PD2K), [IMERG Final mensual V07](https://cmr.earthdata.nasa.gov/search/site/collections/directory/GES_DISC/gov.nasa.eosdis), y [GLDAS Noah mensual 2.1](https://doi.org/10.5067/SXAVCZFAQLNO). El cat�logo NASA consultado identifica para MERRA-2 el concept ID \`C1276812859-GES_DISC\` y versi�n \`5.12.4\`; para IMERG mensual, \`C2723754851-GES_DISC\`, versi�n \`07\`. La consulta autenticada CMR desde el entorno del agente devolvi� ConnectionError; por ello no hay en esta entrega gr�nulo MERRA-2 o IMERG descargado ni inspeccionado. Reintentar los comandos desde un proceso con acceso NASA y conservar su resultado, sin sustituir la fuente ni interpretar el error de red como discrepancia cient�fica.

## Geometr�a candidata y contrato de la tabla

Se reutiliza sin modificar el pol�gono oficial MDBA que E01 conserva en \`E01/geometrias/murray_darling.geojson\`, EPSG:4326, SHA-256 \`d36fe31424758cc4fb8eef25e21b835bb5c05c793c746e8a1eb7b5a5841f6a53\`. Procedencia, servicio FeatureServer, atribuci�n y licencia se mantienen en E01 y \`docs/region_murray_darling.md\`.

Una primera tabla reproducible debe usar centros de celda en el pol�gono (incluye borde), mantener cada resoluci�n original y registrar por separado:
- celdas con centro dentro del pol�gono;
- celdas de ese denominador con dato finito y distinto del fill;
- celdas faltantes y porcentaje v�lido con denominador expl�cito.

Este conteo no representa superficie cubierta. Excluye celdas cuyo centro queda fuera aunque su borde cruce la cuenca y no pondera �rea. No utilizarlo como m�scara de producci�n ni como promedio cient�fico sin revisi�n de Lucas y C�sar. Registrar en cada fila per�odo, producto/versi�n, variable, latitud/longitud del centro, valor crudo, unidad original, candidato QA, archivo original y manifiesto. Esos campos conservan trazabilidad; no significan que un mes sea una serie de veinte a�os.

La tabla con valores reales y la comprobaci�n del l�mite a�n est�n pendientes: faltan muestras accesibles en este proceso. No se genera un CSV vac�o ni se presenta una muestra global como estad�stica de cuenca.

## Volumen hist�rico: estimaci�n, no descarga

E01/cat�logo registra para enero de 2005 51.8986 MiB para MERRA-2 y 17.1937 MiB para IMERG seg�n CMR; GLDAS tiene 23.9142 MiB reportados y su archivo local documenta 25,075,859 bytes. Suponiendo 240 meses por producto y tama�o constante igual al granule de enero de 2005, el total de referencia es aproximadamente 22,322 MiB (21.80 GiB binarios): MERRA-2 12.16 GiB, IMERG 4.03 GiB y GLDAS 5.60 GiB. No incluye manifiestos, copias temporales ni �ndices. Los tama�os MERRA-2 e IMERG no fueron medidos en descargas de este entorno; las diferencias mensuales y revisiones del proveedor pueden cambiar el total. No se descargaron los 240 meses.

## Evidencia pendiente

1. Abrir/verificar localmente la muestra GLDAS: el agente puede leer su manifiesto pero no los bytes del NetCDF. La presencia del archivo y su manifiesto no son una nueva apertura.
2. Obtener muestras NASA aut�nticas MERRA-2 e IMERG, registrar tama�os y tiempos medidos y revisar los metadatos reales antes de aceptar identidades.
3. Ejecutar la prueba espacial con las tres grillas verificadas y crear la tabla CSV con manifiestos localizables.
4. Revisi�n cient�fica de FUL-104, Lucas y C�sar; sin conversiones o decisiones cient�ficas autoaprobadas.


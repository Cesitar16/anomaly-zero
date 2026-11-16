# AZ-08 — Series multivariables descriptivas

## Fuente disponible y nivel de verificación

La integración consume los nueve CSV de `research/results/ful126` y el manifiesto `research/manifests/ful126-point-eda-2005.json`, versionados por DS-09. Los CSV contienen 3 productos × 3 sitios candidatos × 12 meses. Cada fila conserva unidad, centro de celda, índice de grilla, granule ID y SHA-256 del payload NASA que DS-09 registró.

El servicio lee y valida el artefacto derivado (esquema tabular, meses ordenados, identidad de sitio, unidad, valores finitos, coordenadas y referencias SHA256). Calcula además el hash de archivo del CSV y del manifiesto servidos. **No vuelve a abrir ni verificar los granules NASA originales**; esos hashes son referencias heredadas del manifiesto DS-09. Las observaciones siguen marcadas como `diagnostic_only_not_approved`.

## Sitio y contrato

`GET /api/v1/series` y `/api/v1/series/export.csv` admiten `site_id` (`site_west_extent`, `site_central_extent`, `site_east_extent`). Sin `site_id`, el endpoint conserva la ruta histórica IMERG. Con el parámetro, devuelve la serie derivada solicitada y la celda/producto propios en `spatial_aggregation.point`; nunca fuerza una coordenada común. P01 conserva K, P02 mm/hr (tasa media; no acumulado), y P03 kg m-2.

El selector de la interfaz etiqueta los sitios como candidatos no aprobados. No se aplica conversión de unidad, imputación, agregación regional ni máscara. QA del proveedor no está aplicada. La metadata de soporte no significa que el sitio esté validado ni que las huellas de las distintas grillas coincidan.

## Integración de exploración y mapa contextual

El rediseño del explorador conserva los filtros plegables, el detalle mensual, la selección de mes, la tabla, el CSV y el panel MapLibre. El `site_id` se muestra también en el resumen de filtros plegado. El adaptador HTTP consulta el endpoint BE-10 de geometría únicamente en modo API y pasa al mapa el GeoJSON junto con su atribución, licencia y SHA-256 de artefacto. Este hash identifica el contorno contextual; no es una versión temporal ni una aprobación científica. El contorno es cartográfico y no se usa como máscara o agregación.

El endpoint solo entrega el límite cuando está montado el artefacto oficial local, con tamaño 477805 bytes y SHA-256 `d36fe31424758cc4fb8eef25e21b835bb5c05c793c746e8a1eb7b5a5841f6a53`. Su estado sigue siendo `contextual_outline_only` y `not_approved`. Gate M continúa en HOLD: no se genera ni publica raster NASA.

## Métodos estadísticos

La serie temporal individual es descriptiva. `/explore` muestra tres small multiples con eje Y propio por variable/unidad y tablas HTML accesibles; los meses se alinean por etiqueta, y cada panel indica su cell ID para hacer visibles las posiciones distintas. Esta vista lado a lado no prueba co-localización. Comparación de unidades mezcladas, correlaciones, scatter, regresión, tendencias, p-values e incertidumbre permanecen deshabilitadas. Los tres productos comparten etiquetas de mes, pero el experimento DS-09 no aprobó soporte espacial/temporal comparable; con solo un año también existe estacionalidad y dependencia serial. No se interpreta causalidad.

## Límites locales

Los datos derivados son pequeños y están en el repositorio; no se copian granules a imágenes. Los archivos originales permanecen fuera de Git. Los valores reales de este endpoint deben citar DS-09 y mantener la aclaración de que el runtime no verificó de nuevo los payloads fuente.

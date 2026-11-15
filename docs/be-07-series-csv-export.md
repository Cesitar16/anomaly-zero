# BE-07 — Exportación CSV de series mensuales

`GET /api/v1/series/export.csv` descarga la misma respuesta mensual que `GET /api/v1/series`, serializada desde `build_series_response()` y el lector DS-03 existente. Requiere `region_id`, `product_id`, `start`, `end` (`YYYY-MM`) y `frequency=monthly`; el rango es inclusivo y conserva el máximo actual de 240 meses y sus validaciones.

La respuesta es UTF-8 `text/csv`, con `Content-Disposition: attachment` y `Cache-Control: no-store`. La columna `record_type=observation` identifica períodos devueltos por un snapshot verificado. Cero se escribe como `0`; un faltante tiene `value` vacío, `quality_state=missing` y su `missing_reason`. En `no_data`, el archivo tiene encabezado y una única fila `record_type=status`, sin período, valor o `dataset_id`.

El CSV incluye identidad de región/producto/dataset, período, unidad, estado, soporte espacial, `synthetic`, `provider_flags_applied`, hashes de fuentes disponibles, `manifest_sha256` tal como aparece en `SeriesResponse` (actualmente `null`) y transformaciones declaradas. `null` se escribe literalmente cuando el campo es nulo; arreglos/objetos se serializan como JSON compacto. No se agregan hashes de snapshot ni datos que la respuesta no entregue.

Los campos de texto que comiencen, incluso tras espacios o controles, con `=`, `+`, `-` o `@` se prefijan con apóstrofo para evitar que una planilla los evalúe como fórmulas. Las columnas numéricas no pasan por esa protección y sus valores observados se conservan.

Ejemplo PowerShell:

```powershell
$query = 'region_id=murray-darling-basin&product_id=P02&start=2005-01&end=2005-12&frequency=monthly'
Invoke-WebRequest "http://127.0.0.1:8000/api/v1/series/export.csv?$query" -OutFile .\imerg-2005.csv
```

Para comprobar la estructura, leerlo con un parser CSV UTF-8 y revisar `record_type`, `data_state`, `dataset_id`, `synthetic`, unidad, soporte espacial, `provider_flags_applied`, hashes y estados de `value`/`missing_reason`. Verifica los hashes de fuentes contra sus originales cuando estén disponibles. Los ejemplos de OpenAPI marcan `synthetic=true` y no son observaciones NASA. Una observación IMERG sigue siendo `point_sample` en `mm/hr`; `provider_flags_applied=false` y QA `basic_checks_only` no significan QA del proveedor aprobada ni cobertura de superficie de la cuenca.

Los errores mantienen el envelope existente: 404 para región/producto desconocido; 422 para parámetros, límites y períodos inválidos/fuera de cobertura; 503 para snapshot configurado inaccesible; 500 sanitizado para snapshot inválido.

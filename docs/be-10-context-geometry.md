# Contorno contextual MDBA

`GET /api/v1/regions/{region_id}/geometry` sirve únicamente `murray-darling-basin` para dibujar un contorno de referencia en MapLibre. Devuelve `application/geo+json`, un `FeatureCollection` de una entidad y un miembro superior `metadata`. El cuerpo no modifica las coordenadas del GeoJSON MDBA. Omite el miembro legado `crs` porque la salida declara EPSG:4326, y conserva solo `region_id` y `name` en `properties`; no copia `AREA_HA`, `Shape__Area` ni `Shape__Length`.

`metadata.geometry_use` es `contextual_outline_only`; `metadata.scientific_approval` es `not_approved`; `metadata.native_datum` es `null`. `artifact_sha256` identifica los bytes exactos del archivo GeoJSON almacenado (477805 bytes), no los bytes de la respuesta serializada con metadatos. La fuente declara CC BY 4.0; conserva la atribución a DCCEEW y al publicador MDBA. El CRS 3857 es el CRS declarado por la capa; EPSG:4326 es la salida solicitada. El datum nativo sigue desconocido.

Para el adaptador de FE-08, pasa el `FeatureCollection` completo como `data`, `features[0].properties.name` como `label`, `metadata.attribution` a `attribution`, `metadata.source_item_url` a `sourceUrl`, `metadata.license` a `licenseName`, `metadata.license_url` a `licenseUrl` y `metadata.artifact_sha256` a `sha256`. El hash identifica reproduciblemente el contenido, no es fecha ni versión semántica. El tipo actual de FE-08 también pide `geometryVersion`; no lo rellenes con `source_item_modified_utc`: al integrar, preséntalo como identidad del artefacto o ajusta el tipo/copy de FE-08 para llamarlo hash. La API no inventa ni publica un `geometry_version`. Mantén el `metadata` del cuerpo por separado de la fuente de MapLibre, ya que esta puede quitar miembros GeoJSON foráneos.

MapLibre puede consumir directamente el `FeatureCollection`. Los miembros GeoJSON foráneos, como `metadata`, pueden descartarse tras el tiling; conserva esos metadatos del cuerpo HTTP antes de añadirlo como source si la interfaz debe mostrarlos ([GeoJSONSource](https://maplibre.org/maplibre-gl-js/docs/API/classes/GeoJSONSource/)). La estructura usa un miembro foráneo permitido por [RFC 7946](https://www.rfc-editor.org/rfc/rfc7946).

El contorno es solo cartográfico. No representa una máscara, una superficie estadística ni aprobación de agregación, área, QA o inferencia. No modifica los metadatos de geometría del catálogo.

## Preparar el archivo local

No se versiona ni se copia a la imagen. En PowerShell, desde la raíz del repositorio, descárgalo una vez a la carpeta contextual local y verifica que es exactamente el artefacto aprobado:

```powershell
$dir = Join-Path (Get-Location) 'data/contextual'
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$file = Join-Path $dir 'mdba_boundary_4326.geojson'
if (Test-Path -LiteralPath $file) { throw "Ya existe $file; no se sobrescribió." }
$url = 'https://services8.arcgis.com/5xxEi7I2m6ml97fE/arcgis/rest/services/boundary_gdb/FeatureServer/0/query?where=1%3D1&outFields=%2A&returnGeometry=true&outSR=4326&f=geojson'
Invoke-WebRequest -Uri $url -OutFile $file -TimeoutSec 60
$bytes = (Get-Item -LiteralPath $file).Length
$sha256 = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
if ($bytes -ne 477805 -or $sha256 -ne 'd36fe31424758cc4fb8eef25e21b835bb5c05c793c746e8a1eb7b5a5841f6a53') {
    throw "El archivo no coincide con el artefacto autorizado: bytes=$bytes SHA256=$sha256"
}
```

El ítem oficial [MDBA ArcGIS](https://www.arcgis.com/sharing/rest/content/items/ba731d77d80947fbbcbf7524364372ff?f=pjson) declara CC BY 4.0 y atribución a DCCEEW; MDBA es el publicador. La capa 0 declara WKID 102100/3857. El archivo fue exportado con `outSR=4326`; esto no resuelve el datum de origen.

## Montaje Docker read-only

Compose monta el directorio del host en `/app/data/contextual` como solo lectura y configura dentro del backend `ANOMALY_ZERO_CONTEXT_GEOMETRY=/app/data/contextual/mdba_boundary_4326.geojson`. Por defecto usa `./data/contextual`; el `.gitkeep` hace que el servicio pueda arrancar antes de descargar el archivo y responder 503 al endpoint hasta que esté disponible.

Para apuntar a otra carpeta, establece `ANOMALY_ZERO_CONTEXT_GEOMETRY_DIR` en el host antes de iniciar Compose:

```powershell
$env:ANOMALY_ZERO_CONTEXT_GEOMETRY_DIR = (Resolve-Path '.\data\contextual').Path
docker compose up --build -d
Invoke-WebRequest 'http://localhost:8000/api/v1/regions/murray-darling-basin/geometry'
```

También puede fijarse `ANOMALY_ZERO_CONTEXT_GEOMETRY_DIR` en `.env` (que no se versiona), con una ruta absoluta a la carpeta que contiene el archivo. Si el endpoint devuelve 500, comprueba de nuevo tamaño y hash en el host; la API nunca descarga ni repara geometrías durante una solicitud.

## Respuestas y límites operativos

- `200`: FeatureCollection GeoJSON verificado, `Cache-Control: no-store`.
- `404`: región desconocida o distinta de la única región publicada.
- `503`: ruta no configurada, archivo ausente o inaccesible.
- `500`: contenido inválido, fuera de límites, distinto del hash/tamaño aprobado o estructuralmente inconsistente. El error no expone rutas locales.

En cada lectura, el backend limita bytes, verifica tamaño y SHA-256, parsea JSON con rechazo de claves duplicadas y NaN/Infinity, valida tipo/CRS, estructura de anillos, longitud/latitud finitas y bbox fijada al artefacto. La validez topológica fue verificada fuera de HTTP con Shapely 2.2.0: Polygon válido, 1 componente, 0 huecos, 14138 vértices incluyendo cierre. Runtime no importa Shapely ni contacta ArcGIS.

La recuperación verificada fue de 477805 bytes con SHA-256 `d36fe31424758cc4fb8eef25e21b835bb5c05c793c746e8a1eb7b5a5841f6a53`. Es una referencia geográfica contextual; no es máscara científica aprobada, agregación regional, cálculo de área, tendencia ni validación QA del proveedor.

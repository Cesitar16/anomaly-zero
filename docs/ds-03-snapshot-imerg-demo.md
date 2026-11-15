# DS-03 — Snapshot IMERG Final 2005 para demo y handoff API

**Estado:** snapshot offline reproducible; muestra puntual exploratoria, no serie regional aprobada.
**Tarjeta:** FUL-116 / DS-03. **Contrato de intercambio:** AZ-04/FUL-108 fusionado en `dev`; versión `0.1-draft` mantiene carácter de contrato documental, no implementado.

## Diagnóstico y decisión de formato

Se contrastaron tres opciones: CSV para 12 puntos, Parquet para consulta tabular y JSON más NPZ para snapshot y vista espacial. Se elige **JSON canónico para el manifiesto/serie y NPZ comprimido para el preview**: son pequeños, legibles desde Python/FastAPI, preservan nulos y tipos, y no requieren instalar un motor tabular adicional. El preview conserva arrays nativos en `(lon, lat)` y agrega máscaras binarias; no reproyecta, interpola ni aplica la cuenca.

Los originales HDF5 y manifests ya existían localmente en el handoff previo FUL-105. Se copiaron al directorio `data/raw/nasa/imerg_final/`, que Git ignora; no se hizo una descarga masiva. Cada período tiene un manifest de descarga NASA GES DISC/CMR, un SHA-256 que coincide con el original y nombre/producto/período/versión verificables. En la consulta CMR del 2026-11-15, los 12 IDs de granule respondieron HTTP 200 y `GranuleUR`, short name y versión 07 coincidieron con cada HDF5 V07B. Los SHA-256 de los archivos también aparecen en el inventario FUL-112 etiquetados como copias NCAR. Este pipeline consume los HDF5 con manifest de descarga NASA GES DISC y contrasta cada granule con CMR; la procedencia se sustenta en el manifest y la verificación de identidad, no en la etiqueta del inventario secundario.

Los doce nombres, períodos y SHA se copian al manifest portátil del snapshot generado; no es necesario comprometer los datos originales. Cada HDF5 fue abierto y cotejado con `Grid/FileHeader`, colección, variable, unidad, shape `(1,3600,1800)`, dimensiones `time,lon,lat`, bounds, calendario juliano, tiempo dentro de `time_bnds`, valor, fill y campos QA presentes. No se decodifica ni escala automáticamente el contenido.

## Ubicación y soporte espacial

El punto `ful105-panel-row-001` reutiliza el primer centro distinto del panel CSV FUL-105: latitud `-37.64999771118164°`, longitud `145.75°`, orden explícito latitud/longitud. Coincide con el centro `(lon index 3257, lat index 523)` en cada gránulo y con la selección de centros dentro de la geometría MDBA versionada por SHA-256 `d36fe31424758cc4fb8eef25e21b835bb5c05c793c746e8a1eb7b5a5841f6a53`. Es una muestra `point_sample`; el soporte espacial no transforma su valor en promedio de cuenca.

El preview es enero 2005, bbox inclusivo EPSG:4326 `west=138, south=-38, east=153, north=-24`. Retiene centros de grilla nativa, arrays `(longitude, latitude)` ascendentes, `values_raw`, `fill_mask`, `nonfinite_mask` y `finite_nonfill_mask`. No usa el polígono, áreas ni QA y se rotula “muestra NASA exploratoria”. La unidad es `mm/hr`: precipitación media mensual como **tasa**, no acumulado.

## Resultado reproducible

- 12/12 meses 2005 disponibles y reabiertos; la muestra puntual no tuvo fill ni valor no finito: 12 períodos presentes y válidos, ninguno ausente. Esto solo describe este centro y esta ventana.
- El fixture de pruebas diferencia cero observado, fill convertido a `null` con razón `provider_fill_value`, y no finito convertido a `null` con razón `non_finite_source_value`.
- QA permanece `unassessed`; `verification_state=basic_checks_only` indica identidad/estructura/hash y enmascaramiento de no finito/fill, no aprobación de índices QA. `precipitationQualityIndex`, `randomError` y `gaugeRelativeWeighting` se inventarían si están presentes, no se interpretan ni aplican.
- No hay anomalía, tendencia, inferencia, significancia, media regional ni suma mensual.
- `dataset_id` deriva de la versión del pipeline, identidad, coordenadas/índices y hashes fuente. `snapshot_sha256` cubre el JSON canónico sin incluir el campo de su propio hash. NPZ usa tiempos ZIP fijos para repetición byte a byte.

### Reproducir

Desde la raíz del repositorio, con los doce HDF5 y sus manifests en el directorio de entrada:

```powershell
uv sync --group research
uv run python -m research.build_ful116_snapshot
```

Opciones:

```powershell
uv run python -m research.build_ful116_snapshot `
  --input-dir data/raw/nasa/imerg_final `
  --point research/manifests/ful105_imerg_panel_point.json `
  --output-dir data/processed/ful116 `
  --bbox 138,-38,153,-24
```

El programa falla si falta cualquiera de los doce meses, falta un manifest, CMR/producto/versión/período/header no coincide, cambia hash/tamaño, bounds o forma no coinciden, o el centro no existe exactamente en la grilla. Por defecto, un año parcial no se llama snapshot anual. No requiere Earthdata Login para leer insumos ya existentes. Las salidas de `data/processed/` son locales e ignoradas por Git.

### Auditoría puntual de bounds IMERG

Se añadió `research.audit_imerg_bounds_precision` para contrastar los límites float32 originales con continuidad entre intervalos, sin corregirlos:

```powershell
uv run python -m research.audit_imerg_bounds_precision
```

En enero 2005 registró para longitud 542 gaps y 1.577 overlaps adyacentes (máximos `3.8147e-6°` y `1.5259e-5°`); para latitud 542 gaps y 553 overlaps (máximos `3.8147e-6°` y `7.6294e-6°`). Los centros permanecen dentro de sus propios bounds. Esto hace plausible que los bounds publicados, junto con supuestos de transformación de celdas y bordes del polígono, contribuyan al exceso FUL-111; no atribuye de forma única los 48,38 km² ni aprueba bounds de midpoint como sustituto. Las áreas fraccionales y agregación regional permanecen bloqueadas. No se trunca ni normaliza ninguna cobertura.

## Artefactos

Versionados:

- `research/build_ful116_snapshot.py`: pipeline determinista e idempotente.
- `research/manifests/ful105_imerg_panel_point.json`: identidad y coordenada heredada del panel.
- `research/audit_imerg_bounds_precision.py`: auditoría diagnóstica de bounds declarados.
- `research/tests/test_ful116_snapshot.py`: fixtures pequeños de HDF5 y casos de entrada/salida.
- `docs/ds-03-snapshot-imerg-demo.md`: método, limitaciones y handoff.

Locales, fuera de Git:

- `data/raw/nasa/imerg_final/*.HDF5` y `*.manifest.json`: gránulos NASA fuente y manifests.
- `data/cache/ful-102/mdba_boundary_4326.geojson`: geometría local ya existente para comprobar que el punto del panel es un centro interior.
- `data/processed/ful116/imerg_2005_point_snapshot.json`: valores de la serie puntual, QA, cobertura temporal, origen, hashes y limits.
- `data/processed/ful116/imerg_2005-01_bbox_preview.npz`: recorte espacial nativo de enero.

## Handoff para Alaín / FUL-115

El objeto local es un **snapshot de investigación propio**, no una respuesta API completa. El backend puede consumir `dataset_id`, `product`, `requested_coverage`, `available_coverage`, `coverage`, `series`, `spatial_aggregation`, `quality`, `provenance` y `limitations`. Antes de envolverlo en `SeriesResponse`, obtenga IDs/product descriptors y `Region` desde el catálogo backend; el punto debe seguir etiquetado como `point_sample`. No prometer que `availability=available` sea disponibilidad pública antes de servir la ruta. En la respuesta HTTP, generar `generated_at` para esa petición; el snapshot derivado es determinista y no debe usar una hora de consulta fija.

`source_records` incluye un checksum y hash de manifest por mes, IDs CMR/granule, nombre, DOI/collection/product/version, unidad, variable, tiempo real de recuperación y URL de metadata. `provenance.source_sha256` de API puede mapear los doce hashes de originales y `manifest_sha256` al hash del manifest agregado/snapshot según el esquema de servicios. Mantener los timestamps de descarga separados de `generated_at`.

Las limitaciones visibles para API/UI son: `sample NASA exploratory`; unidad nativa `mm/hr` (tasa mensual); soporte `point_sample`; QA `unassessed`; variables QA presentes pero sin filtro; enero preview bbox sin máscara MDBA; nada en el snapshot prueba cobertura espacial regional, QA aprobada ni inferencia histórica. El contrato y endpoints son interfaz objetivo: FUL-115 / GET `/api/v1/series` se implementa en otra tarjeta; este pipeline no modifica FastAPI ni OpenAPI.


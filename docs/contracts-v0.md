# Contrato de intercambio Frontend–FastAPI–Data Science v0 (propuesta)

> **Estado: propuesta para revisión; no aprobada.** Este documento continúa el borrador de la PR #3 y concreta una forma inicial del intercambio. Las rutas, campos, límites e identificadores marcados aquí son propuestas de contrato; no son decisiones aceptadas por el equipo. No implementa endpoints, modelos Pydantic, análisis, procesamiento de datos ni componentes React.

Relacionada con [AZ-04 / FUL-108](https://linear.app/fullstack-track/issue/FUL-108/az-04-disenar-y-aprobar-contratos-frontend-fastapi-data-science).

## Estado del repositorio y alcance

El código actual contiene FastAPI con `GET /health`; los módulos `backend/app/api/`, `schemas/`, `services/` y `analysis/` no tienen implementaciones. React sigue siendo la plantilla Vite y no hay clientes de datos ni vistas consumidoras. Estas rutas definen una interfaz futura de Anomaly Zero; no son endpoints NASA.

El catálogo candidato incluye MERRA-2 T2M, GPM IMERG Final precipitation y GLDAS Noah SoilMoi0_10cm_inst. La región Murray–Darling y 2005-01 a 2024-12 son contexto de trabajo, no cobertura científica aprobada. El inventario, los archivos reales y las revisiones de FUL-104/106/107 determinan qué datos llegan a publicarse.

Los cuatro ejemplos al final son fixtures sintéticos. Cada raíz lleva `"synthetic": true`; el servicio real devolvería `false`. Ningún número de los ejemplos representa una observación o resultado estadístico.

## Convenciones propuestas

- Prefijo `/api/v1`; versión informativa `contract_version: "0.1-draft"`. Romper compatibilidad requeriría una versión mayor de ruta; añadir campos opcionales podría permanecer en la versión menor, sujeto a acuerdo.
- JSON UTF-8. IDs son cadenas opacas, estables y no reutilizadas: `region_id`, `product_id`, `dataset_id`, `analysis_id`. Los ejemplos usan IDs sintéticos.
- Las peticiones de series usan `start` y `end` en `YYYY-MM`, meses inclusivos, con `start <= end`. La respuesta etiqueta cada mes con su primer día (`YYYY-MM-01`). `calendar` es `null` mientras no se haya verificado para la fuente.
- La frecuencia disponible en v0 es `monthly`. No se remuestrea ni se interpola.
- `null` significa no disponible/no calculado/desconocido según el campo y su razón; nunca significa cero. Cero es un valor numérico válido. JSON no puede contener NaN ni Infinity.
- Fechas de actualización se expresan en RFC 3339 UTC o como `null` si no se conocen. Las etiquetas mensuales no contienen hora ni zona.
- La API lee snapshots internos verificados; una petición de React no descarga NASA ni abre NetCDF/HDF5.

### Envolventes comunes

Toda respuesta JSON propuesta lleva `contract_version` y `synthetic`. En producción, `synthetic` es `false`; los fixtures de esta página usan `true`.

La respuesta de error tiene `contract_version`, `synthetic` y `error`. El objeto `error` contiene `code`, `message`, `retryable`, `request_id` y `details`; este último es un objeto seguro con campos de contexto o `null`. El ejemplo 3 muestra el envelope completo.

`request_id` identifica la petición y sirve para soporte; no es un token de acceso. `details` puede ser `null` si no hay detalles seguros que exponer. Nunca se devuelven cookies, credenciales ni mensajes internos del proveedor.

## Catálogo de dominio y significado

### Región

Propuesta de descriptor: `region_id`, `name`, `geometry_version`, `geometry_source` y `area_km2`. El área, versión y geometría se devuelven como `null` hasta validar y aprobar esos datos. Una coordenada de centro dentro de un polígono no implica que toda su celda esté cubierta.

### Producto y dataset

`product_id` identifica la definición de variable/producto; `dataset_id` identifica un snapshot inmutable específico usado por una respuesta o análisis. Un snapshot distinto, checksum distinto o transformación distinta debe tener otro `dataset_id`. La API lo asigna y lo entrega en la respuesta de serie; no lo inventa ni lo construye el frontend.

Descriptor de producto propuesto:

- `product_id`, `short_name`, `product_version`, `variable`, `quantity`, `unit`, `availability`.
- `source`: agencia, distribuidor, ID de colección, DOI/URLs y nombres/IDs de granules cuando estén disponibles.
- `availability`: `available` si hay snapshot para todo el rango publicado, `partial` si hay snapshot con huecos, `unavailable` si no hay snapshot utilizable.

La respuesta de serie lleva `dataset_id` (snapshot exacto), `provenance` (hashes originales, `retrieved_at` y versión del manifiesto), `coverage`, `quality`, `transformations` y `spatial_aggregation` en su envelope, no dentro de `Product`. Los campos desconocidos son `null`, no estimaciones. El objeto `quality` incluye `source_flag_fields` (nombres disponibles), `provider_flags_applied`, `source_missing_attributes` (atributos `_FillValue`, `missing_value`, `scale_factor`, `add_offset` con valores crudos o `null`), `finite_non_fill_filter_applied`, `verification_state` y `mask_applied`. Flags disponibles y flags efectivamente aplicados son campos distintos. `quality.verification_state` puede ser `unassessed`, `basic_checks_only` o `provider_qa_applied`; el último solo se usa si se aplicaron de verdad los flags de la fuente. En `series[].quality.provider_flags` se devuelven pares `{name, value}` originales sin reinterpretarlos.

Catálogo candidato y significado/unidad de trabajo (IDs, versiones y catálogo no quedan aprobados por este borrador):

| ID propuesto | Colección CMR candidata / versión | Variable | Significado que debe conservarse | Unidad observada en muestra | DOI candidato |
| --- | --- | --- | --- | --- | --- |
| `P01` | MERRA-2 `M2TMNXSLV`, concept ID `C1276812859-GES_DISC`, `5.12.4` | `T2M` | Temperatura del aire a 2 m; no temperatura superficial | `K` | `10.5067/AP1B0BA5PD2K` |
| `P02` | IMERG Final `GPM_3IMERGM`, concept ID `C2723754851-GES_DISC`, colección `07`; los archivos de muestra declaran `V07B` | `Grid/precipitation` | Tasa media mensual; no acumulado mensual | `mm/hr` | `10.5067/GPM/IMERG/3B-MONTH/07` |
| `P03` | GLDAS Noah `GLDAS_NOAH025_M`, concept ID `C1342986036-GES_DISC`, `2.1` | `SoilMoi0_10cm_inst` | Humedad modelada de suelo, capa 0–10 cm; salida mensual promedia salidas de 3 horas, no es medición puntual directa | `kg m-2` | `10.5067/SXAVCZFAQLNO` |

MERRA-2 `T2M` significa temperatura del aire a 2 m. IMERG `precipitation` se conserva como tasa en `mm/hr`, no se multiplica por horas para presentarla como acumulado. No completar huecos de IMERG Final con Early/Late; el inventario consultado registra Final V07 hasta 2025-09, que no equivale a cobertura válida. GLDAS Noah 2.1 es modelado; no confundir la producción principal con Early Product. Contrastar las referencias con [catálogo y límites](datasets.md) y [muestras BE-02](be-02-sample-workflow.md) antes de implementar.

La versión exacta, atributos de archivo y campos de calidad deben concordar con los originales y manifiestos. Finito/distinto de fill solo acredita ese filtro básico; **no significa que se aplicaran flags QA**. El conteo de centros no mide superficie cubierta. Si se transforma una unidad, `transformations` debe registrar operación, parámetros, unidad inicial/final y versión del código; en ausencia de transformación, es una lista vacía. Esta v0 no solicita ni propone aplicar conversiones.

### Serie

Cada elemento de `series` es `{date, value, quality}`. `value` está en la unidad declarada por `product.unit`, con significado físico declarado arriba, o es `null`. `quality.state` describe el conocimiento de calidad: `unassessed`, `missing` o `unknown`; no afirma QA aprobada. `provider_flags` contiene solo los flags originales observados, no reinterpretaciones. `missing_reason` es texto/código o `null`.

`coverage.expected_periods`, `present_periods`, `valid_periods` y `missing_periods` describen períodos de la serie. `present_periods` cuenta períodos con una entrada temporal de la fuente aunque su valor sea fill; `valid_periods` cuenta valores finitos no-fill, sin afirmar que se filtraran QA flags ni medir área. `missing_periods` lista puntos con `value: null`. Un cero finito no-fill cuenta como presente y en `valid_periods`.

`spatial_aggregation.method`, `area_weighted` y `mask_version` son explícitos y nullable. Mientras no se apruebe el método espacial, la API no debe describir la serie como promedio validado de cuenca; la decisión pendiente se indica abajo.

### Resultado de análisis

`analysis_id` lo asigna el backend en la respuesta sincrónica de creación. El frontend lo guarda para abrir la vista y consultar `GET /api/v1/analyses/{analysis_id}` al navegar o recargar. No hay colas, polling, ni transición automática de estado en esta propuesta. Si un método no está disponible/aprobado, el registro queda `pending`; repetir GET devuelve ese registro. Cuando un método aceptado esté implementado, una nueva petición crea otro ID y otro resultado.

El objeto propuesto incluye `analysis_id`, `dataset_id`, `region_id`, `product_id`, `product_version`, `variable`, `quantity`, `input_unit`, ventana mensual inclusiva, `source`, `provenance`, `transformations`, `status`, `method`, `metrics` y `limitations`. `input_unit` y `quantity` describen los datos analizados; `metrics.slope_unit` describe la salida y queda `null` hasta definir método y unidad de tiempo. En `pending`, `method` y todas las métricas no calculadas son `null`. Nunca usar `p_value: 0` para representar ausencia. No se fija método, mínimo de muestra, unidad de pendiente, intervalo de confianza, valor p ni umbral de significancia en esta propuesta.

## Recursos propuestos

### `GET /api/v1/regions`

- **Parámetros:** ninguno.
- **Validaciones:** ninguna; devuelve regiones publicadas. Una lista vacía es válida.
- **200:** `{contract_version, synthetic, regions: Region[]}`. Cada `Region` usa el descriptor de región definido arriba.
- **Errores:** `503 SERVICE_UNAVAILABLE` si no se puede leer el catálogo interno; respuesta de error común con `retryable: true`.

### `GET /api/v1/products?region_id=REG01`

- **Parámetros:** requerido `region_id`.
- **Validaciones:** ID no vacío; la región debe existir. Un ID desconocido produce 404.
- **200:** `{contract_version, synthetic, region_id, products: Product[]}`. Cada producto informa disponibilidad `available`, `partial` o `unavailable`, variable/unidad, fuente, cobertura temporal, calidad y el `dataset_id` del snapshot actual o `null`.
- **Errores:** 422 `INVALID_PARAMETER` si falta/formato inválido; 404 `RESOURCE_NOT_FOUND` si la región no existe; 503 `SERVICE_UNAVAILABLE` si falla el catálogo interno.

### `GET /api/v1/series?region_id=REG01&product_id=P02&start=2005-01&end=2005-12&frequency=monthly`

- **Parámetros requeridos:** `region_id`, `product_id`, `start`, `end`, `frequency`.
- **Validaciones:** región y producto deben existir y estar relacionados; formato mensual ISO válido; inicio no posterior al fin; frecuencia exactamente `monthly`; máximo propuesto de 240 meses por respuesta. El rango solicitado debe estar dentro del período de cobertura publicado; no se trunca silenciosamente.
- **200 con datos:** respuesta `SeriesResponse` con `data_state: "available"` o `"available_with_gaps"`, `dataset_id`, producto, procedencia, coberturas, calidad, agregación, transformaciones y períodos ordenados ascendentemente.
- **200 sin registros:** mismo envelope con `data_state: "no_data"`, `dataset_id: null`, `provenance: null`, cobertura disponible nula, `valid_periods: 0`, lista `series: []` y mensaje. Es distinto de un valor cero.
- **Huecos dentro de datos:** un período esperado sin valor se devuelve como punto con `value: null` y razón; no se rellena con cero.
- **Errores:** 422 `INVALID_PARAMETER`, `PERIOD_OUT_OF_COVERAGE` o `LIMIT_EXCEEDED`; 404 `RESOURCE_NOT_FOUND` para región/producto desconocidos; 503 `SERVICE_UNAVAILABLE` si el snapshot no se puede leer.

### `POST /api/v1/analyses`

- **Parámetros:** JSON `{dataset_id, window: {start, end}}`. La ventana usa los meses `YYYY-MM` inclusivos definidos arriba. `dataset_id` debe ser el que entregó una respuesta de serie; no se aceptan archivos NASA ni IDs del cliente.
- **Validaciones:** snapshot existente; ventana mensual ISO inclusiva dentro de cobertura del dataset; máximo 240 meses. Si no hay observaciones suficientes para una operación habilitada, responder 422 `INSUFFICIENT_DATA` con forma de error común.
- **201:** creación sincrónica del recurso y devolución de `AnalysisResponse` con `analysis_id`. Si el método no está aprobado/disponible, `status: "pending"`, `method: null` y métricas `null`. Si está habilitado en el futuro, el cálculo se ejecuta dentro de la petición y devuelve `status: "complete"`; no se promete un método en v0.
- **Errores:** 422 `INVALID_PARAMETER`, `PERIOD_OUT_OF_COVERAGE`, `LIMIT_EXCEEDED` o `INSUFFICIENT_DATA`; 404 `RESOURCE_NOT_FOUND` si `dataset_id` no existe; 503 `SERVICE_UNAVAILABLE` si el snapshot no está disponible. Un 503/5xx no se debe convertir en “sin datos”.
- La respuesta incluye `Location: /api/v1/analyses/{analysis_id}`; el recurso creado y su ID deben estar disponibles para el GET posterior.

### `GET /api/v1/analyses/{analysis_id}`

- **Parámetros:** ID opaco en la ruta.
- **Validaciones:** no vacío y formato de ID admitido por el servicio.
- **200:** el mismo `AnalysisResponse` creado por POST, incluidos `dataset_id`, ventana y procedencia.
- **Errores:** 404 `RESOURCE_NOT_FOUND` si no existe; 503 `SERVICE_UNAVAILABLE` si el snapshot/registro no se puede leer.

### Límites, latencia y raster opcional

Las series quedan limitadas a 240 puntos mensuales por respuesta; se propone JSON sin paginación para ese máximo. No hay SLO de latencia ni tiempos medidos; los endpoints de datos/estadística se proponen sincrónicos solo con ese límite acotado. El límite temporal y el modo sincrónico requieren medición con implementación real antes de considerarse garantía.

No se transmiten rasters NetCDF/HDF5 completos a React. Se propone un descriptor opcional de capa, no una URL de descarga de archivos pesados: `{dataset_id, date, layer_type, unit, state, format, tile_template}`. `date` identifica un instante/mes; `layer_type` distingue `value`, `anomaly`, `slope` o `significance`. Hasta comprobar datos, formato y necesidad de mapa, `state` será `unavailable` y `format`/`tile_template` serán `null`. Si se aprueba, servir tiles o imágenes derivadas con descriptores pequeños; codificación, tamaño máximo por tile y latencia quedan por medir y aprobar. No se propone recurso de exportación: AZ-04 no pide exportar.

## Decisiones que requieren aprobación

| Decisión pendiente | Campos/operación afectados | Responsable de aprobación | Implementación que depende |
| --- | --- | --- | --- |
| IDs/versiones definitivos, cobertura por producto, unidades/calendario y semántica de variables; procedencia y flags disponibles en originales | Catálogo `GET /products`; `Product`, `Source`, `coverage`, `quality`, `unit`, fechas | Lucas; revisión estadística de César cuando cambie interpretación | Catálogo backend, ingesta de snapshots y validaciones de frontend |
| Geometría exacta, máscara y agregación; cuándo usar ponderación y qué significa una serie “regional” | `GET /series`; `spatial_aggregation`, cobertura/calidad, unidad y valor | Lucas (geometría/procedencia) y César (semántica del agregado) | Agregación Data Science y mapas/cobertura de React |
| Método estadístico, mínimos de datos, unidad de pendiente, incertidumbre, p-valor y regla de significancia | `POST/GET /analyses`; `method`, `metrics`, estados `pending/complete` y errores `INSUFFICIENT_DATA` | César; Lucas si depende de unidades/productos | Cálculo Data Science y presentación/interpretación en React |
| Campos visibles, errores/estados y experiencia de crear/abrir `analysis_id` | Todos los envelopes; `Location`; nombres de rutas | Alejandra | Cliente React, rutas de vista y mensajes de estado |
| Rasters, tile descriptor/formato, tamaño máximo y latencia aceptable | Descriptor de raster opcional; respuestas y límites | Lucas (validez/cobertura), Alejandra (uso UI) y backend (servicio/límites) | Publicación raster, capa de mapa y política de rendimiento |
| Propuesta de versión `/api/v1`, campos obligatorios y límites | Todos los recursos | Alejandra, César, Lucas y responsable backend | Esquemas OpenAPI/Pydantic y compatibilidad del cliente |

## Ejemplos JSON sintéticos

Los cuatro objetos son fixtures de forma, no datos ni resultados científicos. `synthetic: true` aparece en la raíz de cada respuesta. En producción el servicio lo devolvería como `false`.

### 1. Serie con cero válido y un valor ausente

```json
{
  "contract_version": "0.1-draft",
  "synthetic": true,
  "data_state": "available_with_gaps",
  "region": {
    "region_id": "REG01",
    "name": "Región sintética",
    "geometry_version": null,
    "geometry_source": null,
    "area_km2": null
  },
  "product": {
    "product_id": "P02",
    "short_name": "GPM_3IMERGM",
    "product_version": "V07B",
    "variable": "precipitation",
    "quantity": "monthly_mean_rate",
    "unit": "mm/hr",
    "availability": "partial",
    "source": {
      "agency": "NASA/JAXA",
      "distributor": "GES DISC",
      "collection_id": "C2723754851-GES_DISC",
      "doi": "10.5067/GPM/IMERG/3B-MONTH/07",
      "source_urls": [],
      "granule_ids": []
    }
  },
  "dataset_id": "ds-synthetic-001",
  "provenance": {
    "source_sha256": [],
    "retrieved_at": null,
    "manifest_version": null
  },
  "temporal": {
    "frequency": "monthly",
    "calendar": null,
    "date_label": "month_start"
  },
  "requested_coverage": {
    "start": "2005-01",
    "end": "2005-03",
    "end_inclusive": true
  },
  "available_coverage": {
    "start": "2005-01",
    "end": "2005-03"
  },
  "coverage": {
    "expected_periods": 3,
    "present_periods": 3,
    "valid_periods": 2,
    "missing_periods": ["2005-02"]
  },
  "quality": {
    "source_flag_fields": ["precipitationQualityIndex", "randomError"],
    "provider_flags_applied": false,
    "source_missing_attributes": {
      "fill_value": -9999.9,
      "missing_value": null,
      "scale_factor": null,
      "add_offset": null
    },
    "finite_non_fill_filter_applied": true,
    "verification_state": "basic_checks_only",
    "mask_applied": null
  },
  "spatial_aggregation": {
    "method": null,
    "area_weighted": null,
    "mask_version": null
  },
  "transformations": [],
  "series": [
    {
      "date": "2005-01-01",
      "value": 0.42,
      "quality": {"state": "unassessed", "provider_flags": [], "missing_reason": null}
    },
    {
      "date": "2005-02-01",
      "value": null,
      "quality": {"state": "missing", "provider_flags": [], "missing_reason": "provider_fill_value"}
    },
    {
      "date": "2005-03-01",
      "value": 0.0,
      "quality": {"state": "unassessed", "provider_flags": [], "missing_reason": null}
    }
  ]
}
```

### 2. Período sin datos

```json
{
  "contract_version": "0.1-draft",
  "synthetic": true,
  "data_state": "no_data",
  "region": {
    "region_id": "REG01",
    "name": "Región sintética",
    "geometry_version": null,
    "geometry_source": null,
    "area_km2": null
  },
  "product": {
    "product_id": "P03",
    "short_name": "GLDAS_NOAH025_M",
    "product_version": "2.1",
    "variable": "SoilMoi0_10cm_inst",
    "quantity": "soil_moisture_layer_0_10_cm",
    "unit": "kg m-2",
    "availability": "unavailable",
    "source": {
      "agency": "NASA",
      "distributor": "GES DISC",
      "collection_id": "C1342986036-GES_DISC",
      "doi": "10.5067/SXAVCZFAQLNO",
      "source_urls": [],
      "granule_ids": []
    }
  },
  "dataset_id": null,
  "provenance": null,
  "temporal": {"frequency": "monthly", "calendar": null, "date_label": "month_start"},
  "requested_coverage": {"start": "2005-01", "end": "2005-03", "end_inclusive": true},
  "available_coverage": null,
  "coverage": {
    "expected_periods": 3,
    "present_periods": 0,
    "valid_periods": 0,
    "missing_periods": ["2005-01", "2005-02", "2005-03"]
  },
  "quality": {
    "source_flag_fields": [],
    "provider_flags_applied": false,
    "source_missing_attributes": {
      "fill_value": null,
      "missing_value": null,
      "scale_factor": null,
      "add_offset": null
    },
    "finite_non_fill_filter_applied": false,
    "verification_state": "unassessed",
    "mask_applied": null
  },
  "spatial_aggregation": {"method": null, "area_weighted": null, "mask_version": null},
  "transformations": [],
  "series": [],
  "message": "No hay datos disponibles para el período solicitado."
}
```

### 3. Snapshot/fuente no disponible

```json
{
  "contract_version": "0.1-draft",
  "synthetic": true,
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "El snapshot de datos no está disponible temporalmente.",
    "retryable": true,
    "request_id": "req-synthetic-001",
    "details": {"dataset_id": "ds-synthetic-001", "provider_status": null}
  }
}
```

### 4. Análisis creado sin cálculo disponible

```json
{
  "contract_version": "0.1-draft",
  "synthetic": true,
  "analysis_id": "analysis-synthetic-001",
  "dataset_id": "ds-synthetic-001",
  "region_id": "REG01",
  "product_id": "P02",
  "product_version": "V07B",
  "variable": "precipitation",
  "quantity": "monthly_mean_rate",
  "input_unit": "mm/hr",
  "window": {"start": "2005-01", "end": "2005-03", "end_inclusive": true},
  "source": {
    "agency": "NASA/JAXA",
    "distributor": "GES DISC",
    "collection_id": "C2723754851-GES_DISC",
    "doi": "10.5067/GPM/IMERG/3B-MONTH/07",
    "source_urls": [],
    "granule_ids": []
  },
  "provenance": {
    "source_sha256": [],
    "retrieved_at": null,
    "manifest_version": null
  },
  "transformations": [],
  "status": "pending",
  "method": null,
  "metrics": {
    "slope": null,
    "slope_unit": null,
    "confidence_interval": null,
    "p_value": null,
    "significance": null
  },
  "limitations": ["Método, unidades y criterios pendientes de aprobación científica."]
}
```

## Revisión y siguiente implementación

Lucas revisa procedencia, producto, unidades, calendario, QA y cobertura; César revisa el significado estadístico y límites de los resultados; Alejandra comprueba los envelopes, estados y flujo React de obtención/uso de `analysis_id`. Alaín convierte solo las decisiones aprobadas en modelos OpenAPI/Pydantic posteriormente. La aprobación de AZ-04 aún depende de las relaciones existentes con FUL-107, FUL-103 y FUL-99; esta propuesta no las elimina.

No se añade exportación, integración NASA desde React, cola de trabajos ni formato raster ejecutable en esta tarjeta.

# Contrato API–React–Data Science v0 (borrador)

> **Estado: borrador para coordinación. No aprobado.** No implementa rutas, esquemas Pydantic, extracción NASA ni análisis. Los nombres de ruta y varios campos son propuestas sujetas a FUL-103, FUL-106, FUL-107 y revisión de César, Lucas y Alejandra.

## Alcance y estado de las decisiones

**Consta en el repositorio como base del MVP (todavía candidata científica):** React + TypeScript + Vite; Python + FastAPI; cuenca Murray–Darling; período candidato enero de 2005 a diciembre de 2024; MERRA-2 para T2M, GPM IMERG Final para precipitación y GLDAS Noah para humedad del suelo. La API solo tiene `GET /health`. No hay endpoints de datos ni análisis implementados.

**Propuesto para discutir:** prefijo `/api/v1`; IDs `REG01`, `P01`–`P03`; recursos de regiones, productos, series y análisis; parámetros, nombres de propiedades, errores y límites descritos abajo. Son formas de coordinación, no un contrato aceptado.

Los ejemplos son **JSON ficticio** para UI/validación de forma. Ningún valor es observación NASA, ningún estado describe una extracción completada y no deben usarse como datos científicos.

## Catálogo candidato y metadatos por verificar

El informe de investigación del proyecto identifica estos productos y atributos como referencia documental. FUL-103/FUL-106 deben comprobarlos con archivos/grillas descargados. El atributo de cada archivo será la fuente de verdad al ingestar; si difiere, conservar el atributo original y documentar la decisión.

| ID propuesto | Producto y campo candidato | Fuente y particularidad | Unidad esperada, pendiente de verificar en archivo |
| --- | --- | --- | --- |
| P01 | MERRA-2 `M2TMNXSLV` 5.12.4 · `T2M` | Reanálisis NASA GMAO, distribuido por GES DISC; media mensual de temperatura del aire a 2 m. DOI: `10.5067/AP1B0BA5PD2K`. | K; `_FillValue` y `missing_value` no inspeccionados en bytes de datos. La conversión K → °C (restar 273.15) es una transformación propuesta, que debe registrarse y verificarse. |
| P02 | GPM IMERG Final `GPM_3IMERGM` V07B · `precipitation` | Combinación multisatélite y pluviómetros de NASA/JAXA; producto mensual. DOI: `10.5067/GPM/IMERG/3B-MONTH/07`. No completar huecos de Final V07 con Early/Late; la cobertura inventariada termina en septiembre de 2025. | mm h⁻¹ esperados para tasa media mensual; leer atributos. Convertir a acumulación mensual solo si se aprueba integrar la tasa por las horas del mes. Calidad/atributos `randomError` y `precipitationQualityIndex` pendientes de revisar en archivo/grilla. |
| P03 | GLDAS Noah `GLDAS_NOAH025_M` V2.1 · `SoilMoi0_10cm_inst` | Modelo terrestre open-loop con forzantes combinados; humedad de la capa 0–10 cm; salidas mensuales como promedios de salidas de 3 horas. DOI: `10.5067/SXAVCZFAQLNO`. No confundir con Early Product. | kg m⁻² esperados; `-9999` está documentado como faltante, pero confirmar atributos tras descarga. Máscara y calidad por celda pendientes. |

La cobertura candidata común es 2005-01 a 2024-12 (240 meses), no garantía de que cada producto tenga 240 observaciones válidas en la cuenca. Región, geometría, versión/hash del polígono, máscaras y cobertura efectiva siguen pendientes de validación. Distinguir versión del producto, versión del contrato y versión de cualquier transformación.

## Recursos y forma propuesta

Todas estas rutas son **propuestas internas de Anomaly Zero**, no rutas NASA ni endpoints operativos:

| Recurso propuesto | Uso |
| --- | --- |
| `GET /api/v1/regions` | Catálogo de regiones disponibles. |
| `GET /api/v1/products?region_id=REG01` | Productos/variables disponibles para una región, cobertura y metadatos de fuente. |
| `GET /api/v1/series?region_id=REG01&product_id=P02&start=2005-01&end=2005-12&frequency=monthly` | Serie regional agregada y metadatos de procedencia/calidad. |
| `GET /api/v1/analyses/{analysis_id}` | Estado y resultado de un análisis; la semántica estadística sigue pendiente. |

Forma común propuesta para respuestas: `contract_version`, `data_state`, identificadores estables, `source`, `coverage`, `quality`, `transformations` y `spatial_aggregation`. Una serie incluye períodos explícitos en orden ascendente y valor numérico o `null`. Mantener el registro original de unidad/fill/flags de proveedor junto a cualquier normalización. Método de resumen regional (máscara, ponderación por área y tratamiento de celdas parciales) permanece pendiente; no inferirlo como media simple.

### Entradas, validaciones y límites propuestos

- `region_id` y `product_id`: requeridos para series; deben existir y estar habilitados en el catálogo publicado.
- `start`, `end`: ISO `YYYY-MM`; límites inclusivos; `start <= end`. Rechazar formato inválido con error de campo legible.
- `frequency`: `monthly` para el MVP. No prometer frecuencia diaria ni remuestreo.
- Propuesta de máximo: 240 períodos por respuesta, alineado con la ventana candidata de 20 años. Fuera del límite, devolver error explícito con máximo permitido; no truncar silenciosamente.
- Si se solicita un período válido sin registros, devolver estado sin datos y cobertura vacía; no convertir faltantes a cero. El cero numérico se conserva cuando el proveedor entrega un cero válido.
- Propuesta de fecha de período: `date` en ISO `YYYY-MM-01` como etiqueta del mes. `calendar` y zona/hora se publican cuando el eje temporal del archivo sea inspeccionado; “gregoriano” es una expectativa por verificar, no un hecho de todos los archivos.

### Valores, calidad, cobertura y procedencia

Propuesta de punto temporal: `{date, value, unit, quality}`. `value` es finito o `null`; nunca usar NaN/Infinity en JSON. Un faltante de fuente, máscara o QA permanece `null`, acompañado por causa/flag disponible. El cero puede representar una medición real. Los códigos normalizados de calidad todavía requieren revisión; guardar flags originales sin reinterpretarlos.

Propuesta de metadatos de producto/serie:

- `product_id`, `short_name`, `variable`, `product_version`, `contract_version`.
- `source.agency`, `source.distributor`, `source.collection_id`, `source.doi`, URL/origen consultado y fecha de consulta/actualización cuando estén comprobados.
- `unit` + `unit_status`; unidad declarada por archivo vs. unidad derivada. Las unidades de la tabla son esperadas y pendientes de verificación.
- `requested_coverage`, `available_coverage`, conteos de períodos esperados/presentes/válidos y faltantes explícitos, sin insinuar cobertura espacial completa.
- `transformations[]`: orden, operación, parámetros, unidad de entrada/salida y referencia de implementación. Lista vacía significa que no se declara transformación aplicada.
- Calidad: flags nativos, máscara aplicada, regla de agregación y estado de verificación; indicar “pendiente” cuando no se ha inspeccionado.

### Resultado estadístico aún no definido

El objeto de análisis es una forma de coordinación, no el método aprobado. No fijar prueba, pendiente, intervalo, nivel de confianza, umbral, valor p ni significancia hasta revisión científica. Mientras el cálculo no exista, publicar `status: "pending"` y `null` en todas las métricas numéricas; no sustituir ausencia de resultado por cero. Método, ventana, unidades de tasa, incertidumbre, supuestos y limitaciones deben documentarse antes de presentar un resultado.

### Errores y comportamiento esperado de React

Códigos HTTP propuestos; ajustar a las convenciones FastAPI acordadas antes de implementar:

| HTTP propuesto | Código | Interfaz esperada |
| --- | --- | --- |
| 400 | `INVALID_PARAMETER` | Marcar campo y explicar formato/rango esperado; permitir corregir la consulta. |
| 404 | `RESOURCE_NOT_FOUND` | Mensaje de recurso inexistente; conservar selección editable. |
| 422 | `PERIOD_OUT_OF_COVERAGE` o `LIMIT_EXCEEDED` | Mostrar cobertura/límite; no recortar silenciosamente. |
| 200 | `NO_DATA` en respuesta de serie | Estado vacío con región, producto y período consultado; distinguirlo de cero. |
| 502/503 | `UPSTREAM_UNAVAILABLE` | Mensaje de fuente temporalmente no disponible, opción de reintentar y consulta visible. |
| 202 | análisis `pending` | Indicador “análisis pendiente”; no graficar ni etiquetar métricas nulas como cero. |

Sobre acordar: forma única de error, códigos finales, reintentos, estados de carga, frescura/caché, paginación (probablemente innecesaria para 240 puntos), raster/tile e interacción de cancelación. Esta versión no promete latencia ni procesamiento sincrónico.

## Ejemplos ficticios

### 1. Serie disponible, con cero real y un mes faltante

Todos los números son inventados. El cero de marzo es un valor numérico ilustrativo; febrero conserva el faltante como `null`.

```json
{
  "contract_version": "0.1-draft",
  "data_state": "available_with_gaps",
  "region": {"id": "REG01", "name": "Murray-Darling (ficticio)", "geometry_version": null},
  "product": {
    "id": "P02",
    "short_name": "GPM_3IMERGM",
    "product_version": "V07B",
    "variable": "precipitation",
    "unit": "mm h-1",
    "unit_status": "expected_pending_file_verification",
    "source": {
      "agency": "NASA/JAXA GPM",
      "distributor": "GES DISC",
      "collection_id": "C2723754851-GES_DISC",
      "doi": "10.5067/GPM/IMERG/3B-MONTH/07"
    }
  },
  "frequency": "monthly",
  "calendar": null,
  "requested_coverage": {"start": "2005-01", "end": "2005-03", "end_inclusive": true},
  "available_coverage": {"start": "2005-01", "end": "2005-03"},
  "coverage": {"expected_periods": 3, "present_periods": 3, "valid_periods": 2, "missing_periods": ["2005-02"]},
  "transformations": [],
  "spatial_aggregation": {"method": null, "mask_version": null, "area_weighted": null},
  "series": [
    {"date": "2005-01-01", "value": 0.42, "unit": "mm h-1", "quality": {"status": "unknown", "provider_flags": []}},
    {"date": "2005-02-01", "value": null, "unit": "mm h-1", "quality": {"status": "missing", "provider_flags": [], "reason": "fictional_missing_value"}},
    {"date": "2005-03-01", "value": 0.0, "unit": "mm h-1", "quality": {"status": "unknown", "provider_flags": []}}
  ]
}
```

### 2. Ausencia de datos

```json
{
  "contract_version": "0.1-draft",
  "data_state": "no_data",
  "region_id": "REG01",
  "product_id": "P02",
  "requested_coverage": {"start": "2005-01", "end": "2005-03", "end_inclusive": true},
  "available_coverage": null,
  "coverage": {"expected_periods": 3, "present_periods": 0, "valid_periods": 0, "missing_periods": ["2005-01", "2005-02", "2005-03"]},
  "series": [],
  "message": "No hay datos disponibles para el período solicitado (respuesta ficticia)."
}
```

### 3. Fallo de proveedor

La envoltura y el código son propuestas; no exponen secretos ni datos del proveedor.

```json
{
  "contract_version": "0.1-draft",
  "error": {
    "code": "UPSTREAM_UNAVAILABLE",
    "message": "La fuente de datos no está disponible temporalmente.",
    "retryable": true,
    "request_id": "mock-req-001",
    "details": {"provider": "NASA data source", "provider_status": null}
  }
}
```

### 4. Análisis pendiente

No hay método ni resultado inferencial asignado en este ejemplo.

```json
{
  "contract_version": "0.1-draft",
  "analysis_id": "mock-analysis-001",
  "status": "pending",
  "method": null,
  "window": {"start": "2005-01", "end": "2024-12"},
  "slope": null,
  "slope_unit": null,
  "confidence_interval": null,
  "p_value": null,
  "significance": null,
  "limitations": ["Método, unidades y criterios pendientes de revisión científica."]
}
```

## Preguntas para revisión antes de aprobar

**César (estadística):** ¿Qué método y mínimos de datos exige el caso? ¿Qué definición y unidad tendrá la tasa? ¿Qué intervalo de incertidumbre, tratamiento del valor p y lenguaje de significancia son correctos? ¿Qué estados distinguen “pendiente”, “insuficiente” y “no aplicable”?

**Lucas (NASA/datos):** ¿Confirma los identificadores/versiones y el DOI de cada producto? Tras una descarga de muestra, ¿cuáles son unidades, calendario/eje temporal, fill/scale y flags QA efectivos? ¿Qué agregado espacial, máscara y cobertura de Murray–Darling puede sostenerse? Para IMERG Final, ¿se conserva explícitamente el cierre V07 en 2025-09?

**Alejandra (React):** ¿Le sirve separar catálogo, serie y análisis con estos campos? ¿Qué estados/errores necesita mostrar y qué detalle de cobertura/calidad debe ser visible? ¿240 puntos y etiqueta mensual `YYYY-MM-01` bastan para el explorador inicial?

## Pendiente para pasar de borrador a contrato

Revisar respuestas; contrastar atributos y cobertura con las muestras reales de FUL-103/FUL-106; esperar aprobación científica de FUL-107 y arquitectura FUL-99; acordar el shape con React; y luego convertir solo las partes aceptadas en OpenAPI/Pydantic con ejemplos validados. FUL-108 conserva sus bloqueos nativos y sigue sin aprobarse.

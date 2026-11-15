# DS-06 — Adquisición NASA mensual 2005

**Tarjeta:** FUL-123 · **Estado:** adquisición reproducida y lista para revisión científica · **Rama:** `feature/ful-123-ds-06-adquisicion-nasa-2005`.

## Resultado reproducido

La auditoría ejecutada sobre los roots locales de FUL-105/116/122 y `data/raw/nasa` de este worktree verificó identidad de producto/gránulo, manifiesto adyacente, tamaño, SHA-256 y payload NetCDF/HDF5. El inventario encontró 51 archivos candidatos: 36 registros producto-mes elegibles y 15 copias duplicadas idénticas excluidas del conteo. No encontró conflictos entre payloads elegibles ni archivos incompletos o corruptos.

| Producto | Colección / versión | Elegibles | Meses | Copias idénticas excluidas |
|---|---|---:|---|---:|
| IMERG Final V07B | GPM_3IMERGM V07B | 12 | enero–diciembre | 13 |
| MERRA-2 `T2M` | `M2TMNXSLV` 5.12.4 | 12 | enero–diciembre | 1 |
| GLDAS Noah `SoilMoi0_10cm_inst` | `GLDAS_NOAH025_M` 2.1 | 12 | enero–diciembre | 1 |

**Cobertura auditada:** 36/36 registros producto-mes; coincidencia temporal triple de 12/12 meses. Los enero MERRA-2/GLDAS se reutilizaron desde las ubicaciones locales históricas elegibles; febrero–diciembre de ambos productos (22 gránulos) están en `data/raw/nasa` de FUL-123. IMERG no requirió descarga.

El manifiesto portátil [`ful123-acquisition-results-2005.json`](../research/manifests/ful123-acquisition-results-2005.json) es la evidencia detallada de identidad CMR, IDs de colección/gránulo, productor, periodo, tamaño, hash SHA-256 del payload, hash del manifiesto del archivo, variable/unidad, versión, inspección de metadatos y método. Cada hash fue reproducido desde el archivo local. El manifiesto no contiene rutas absolutas, secretos ni enlaces de transferencia autenticados. Los dos pilotos de febrero constan como payload verificados; los 20 resultados de marzo–diciembre reportan `attempts: 1`. El registro local de progreso es transitorio e ignorado por Git; no se usa como evidencia portable.

### Reproducción

Desde el worktree FUL-123, auditar todos los roots pertinentes:

```powershell
uv run python -m research.ful122_inventory `
  --input-dir "C:\ruta\hackNasa2026\data\raw\nasa" `
  --input-dir "C:\ruta\anomaly-zero-ful-105-eda\data\raw\nasa" `
  --input-dir "C:\ruta\anomaly-zero-ful-105-eda\data\cache\ful-105\be02-handoff\data_root\data\raw\nasa" `
  --input-dir data/raw/nasa `
  --output research/manifests/ful123-inventory-audit-2005.json
```

Para regenerar el resumen portable de resultados a partir de los archivos encontrados por el inventario y el plan CMR versionado:

```powershell
uv run python -m research.ful123_acquisition `
  --input-dir "C:\ruta\hackNasa2026\data\raw\nasa" `
  --input-dir "C:\ruta\anomaly-zero-ful-105-eda\data\raw\nasa" `
  --input-dir "C:\ruta\anomaly-zero-ful-105-eda\data\cache\ful-105\be02-handoff\data_root\data\raw\nasa" `
  --input-dir data/raw/nasa `
  --data-dir data/raw/nasa `
  --plan-file research/manifests/ful123-acquisition-plan-2005.json `
  --output research/manifests/ful123-acquisition-results-2005.json `
  --record-results
```

El manifiesto de plan conserva el inventario CMR y estimaciones previas; el manifiesto de resultados registra los bytes e integridad realmente auditados. No se versionan archivos de datos crudos.

## Descarga, método y recursos

Los 22 archivos de febrero a diciembre son **gránulos NASA completos**, descargados con los clientes Earthaccess del proyecto y verificados como payloads nativos. No se aplicó subsetting espacial o de variable, reproyección, interpolación ni máscara. Tampoco se presentan recortes o valores derivados como si fueran el original. La adquisición completa conserva la grilla global, variables disponibles, atributos y trazabilidad del objeto fuente y permite repetir validaciones sobre el producto nativo; su costo es transferir más datos y requerir almacenamiento local mayor que un subset. Las URLs firmadas/autenticadas no se guardan en el repositorio.

- Estimación CMR para los 22: **873,765,835 bytes** (aprox. 833.1 MiB).
- Payload de los 22 archivos adquiridos y verificados: **873,765,835 bytes**.
- Diferencia real menos estimación: **0 bytes**. Es la suma de tamaños de payload, no una medición de overhead de red.
- Los 20 resultados de marzo–diciembre registran un intento cada uno. Los dos pilotos de febrero se verificaron satisfactoriamente; su contador de intentos no se atribuye porque el registro portable no lo conserva.
- Los datos permanecen fuera de Git bajo `data/raw/nasa`; no se deben agregar al commit.

Se eligieron los gránulos completos como referencia reproducible porque el flujo nativo entregó payload verificable, metadatos y hashes, sin depender de que un servicio de subset conserve todos los atributos necesarios. Esto no demuestra que un subset sea científicamente inválido; solo evita introducir un derivado espacial en esta tarjeta. La documentación oficial informa disponibilidad de productos y servicios de datos/subsetting en [NASA LDAS GLDAS](https://ldas.gsfc.nasa.gov/gldas/dataset), y la ficha identifica [MERRA-2 M2TMNXSLV 5.12.4](https://disc.gsfc.nasa.gov/datasets/M2TMNXSLV_5.12.4/summary). El acceso y el modo de transferencia pueden evolucionar; por reproducibilidad se registra aquí el método observado en esta adquisición, no se codifican enlaces autenticados.

## Compatibilidad temporal y metadatos nativos

La cobertura mensual se comprobó por gránulo y los 12 periodos de cada producto cubren enero–diciembre de 2005. Las fechas mensuales son compatibles para construir un índice común de inventario; esto no convierte las observaciones en una muestra espacial común ni implica que sus instantes representativos sean idénticos.

| Producto | Frecuencia/calendario y tiempo | Resolución y coordenadas nativas | Variable/unidad | Fill y QA |
|---|---|---|---|---|
| IMERG Final V07B | Mensual; calendario/granularidad declarados por producto en payload/manifiesto | Grilla global IMERG nominal 0.1°; coordenadas provienen del archivo nativo | Precipitación mensual; `mm/hr` conforme al inventario del proyecto | QA IMERG sigue sin evaluación científica definitiva; no se promueve el estado de ingestión como aprobación QA |
| MERRA-2 | Mensual, un registro por archivo; calendario `standard`/gregoriano según coordenada temporal del NetCDF. Intervalo mensual del gránulo CMR | `lat` 361 puntos de −90 a 90°, paso 0.5°; `lon` 576 puntos de −180 a 179.375°, paso 0.625° | `T2M`, dimensiones `(time, lat, lon)`, unidad `K` | `_FillValue` y `missing_value` 1e15; sin variables QA explícitas identificadas por el chequeo de nombres |
| GLDAS Noah | Mensual, `calendar=standard`, coordenada `time` con `time_bnds` | `lat` 600 puntos de −59.875 a 89.875°, paso 0.25°; `lon` 1440 puntos de −179.875 a 179.875°, paso 0.25° | `SoilMoi0_10cm_inst`, dimensiones `(time, lat, lon)`, unidad `kg m-2` | `_FillValue` y `missing_value` −9999; no se identificaron variables QA explícitas para esta variable |

Los doce archivos de MERRA-2 comparten forma de variable `[1,361,576]`; los doce GLDAS `[1,600,1440]`. GLDAS contiene coordenadas de límites temporales `time_bnds`; MERRA-2 no declara bounds en el resumen de la variable temporal examinado. Los metadatos específicos por archivo (incluidos valores temporales) están en el manifiesto de resultados. Los marcadores fill son códigos de ausencia, no mediciones; antes de cualquier estadística deberán enmascararse de acuerdo con el tipo y atributos del archivo. “Sin variables QA explícitas identificadas” no significa que la observación haya pasado una evaluación QA científica.

IMERG, MERRA-2 y GLDAS emplean soportes, resoluciones, máscaras y convenciones distintas. La coincidencia mensual solo demuestra cobertura temporal en el inventario. Aún se deben establecer la geometría versionada de Murray–Darling, soporte espacial común, tratamiento de borde y faltantes, linaje de máscara GLDAS y evaluación QA IMERG antes de proponer co-localización. No se calculan aquí promedios regionales, correlaciones, tendencias ni modelos. **Gate R y Gate T siguen pendientes; no hay aprobación para inferencia ni modelado productivo.**

## Ejecutador y salvaguardas

El CLI retorna un código distinto de cero ante fallos y cualquier resultado bloqueado, incluido `blocked_existing_identity_mismatch`; una prueba de regresión cubre este caso. El manifiesto de resultados es portable: guarda rutas relativas, hashes y metadatos de adquisición, y excluye rutas locales y datos de autenticación. Los errores no se convierten en éxito silencioso. No se modificaron archivos originales, notebooks personales ni los archivos crudos.

## Validación de ingeniería

La validación final de pytest, Ruff y `git diff --check` se registra junto al commit de esta actualización y en los checks de PR #26. Las pruebas de adquisición usan fixtures locales; no requieren acceso de red ni credenciales.

## Próximo EDA científico

Preparar primero una especificación de co-localización reproducible: congelar la geometría de cuenca y su procedencia; documentar las coordenadas y límites nativos; identificar una estrategia de puntos/celdas con soporte común para IMERG 0.1°, MERRA-2 0.625° × 0.5° y GLDAS 0.25°; y evaluar sensibilidad de bordes, máscaras, fill y QA sin agregación o inferencia hasta aprobar Gate R y Gate T. Luego generar una tabla de auditoría de disponibilidad espacial-temporal y someterla a revisión científica antes de construir un panel multivariable.

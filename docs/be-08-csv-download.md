# BE-08 · Descargar la serie visible

En `/explore`, selecciona **Servicio real (API)** y consulta una serie. Con observaciones disponibles y sin cambios pendientes en los filtros, **Descargar CSV** pide `GET /api/v1/series/export.csv` con la región, producto y rango de la respuesta mostrada. El navegador trata `text/csv` como archivo y conserva el contenido y los metadatos que proporciona BE-07. En modo demo, `no_data`, carga o filtros sin aplicar, la acción queda deshabilitada.

La descarga no convierte `point_sample` en agregado de cuenca, no cambia `mm/hr` y no aprueba flags QA. Las fixtures de frontend son sintéticas y solo verifican el flujo de interfaz.

## Evidencia de QA

- Pruebas de componentes/adaptador: URLs y parámetros, Blob CSV, nombre determinista, liberación de object URL, modo demo, `no_data`, filtros obsoletos/cancelación y HTML de proxy.
- QA de navegador con IMERG auténtico: pendiente. El snapshot real DS-03 no está disponible en este worktree; solo se encontraron snapshots temporales sintéticos de pruebas.
- Docker/Compose: no disponible en el entorno (comando `docker` ausente). Puede verificarse con backend y Vite locales cuando el snapshot auténtico esté accesible.

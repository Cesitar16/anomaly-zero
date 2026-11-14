# Laboratorio de investigación

Este espacio contiene un piloto de EDA puntual con NASA POWER y funciones reusables, independiente de los adaptadores Earthdata que desarrolla Alaín. El notebook no pretende caracterizar toda la cuenca Murray–Darling ni sustituir MERRA-2, GPM IMERG o GLDAS.

## Reproducir

Desde la raíz del repositorio:

    uv sync --group research --group dev
    uv run jupyter lab research/notebooks

Abre y ejecuta todas las celdas de 01_eda_piloto_power.ipynb. La primera ejecución consulta NASA POWER y conserva el JSON original y sus metadatos en data/raw/. Si ya existe el archivo local, se reutiliza. Para descargar otra vez, borra únicamente el JSON local o invoca fetch_power_response(..., force=True) desde un entorno de confianza.

Ejecuta las pruebas offline con uv run pytest research/tests. No requieren conectividad NASA.

## Datos y alcance

La consulta piloto usa la API mensual puntual de NASA POWER para T2M, comunidad AG, y Wagga Wagga (NSW), entre 2005 y 2024. La API agrupa por años y puede incluir el mes 13 como resumen anual; el parser conserva la respuesta cruda completa y excluye ese registro solo de la serie mensual. El archivo original y su sidecar de procedencia están ignorados por Git bajo data/raw/.

Las funciones de calidad, estadísticas descriptivas y anomalías están en series_quality.py; el cliente y parser están en power_data.py. Estas funciones no conectan con el backend y no constituyen todavía el motor estadístico productivo.

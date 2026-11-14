# Arquitectura inicial

1. **Fuentes NASA:** productos candidatos consultados durante la exploración en Giovanni y, por validar, Earthdata/CMR con `earthaccess`.
2. **Extracción:** adaptadores dedicados obtendrán archivos originales; todavía no están implementados.
3. **Procesamiento científico:** limpieza, agregación espacial/temporal y análisis en `backend/app/analysis/` y notebooks.
4. **FastAPI:** expondrá resultados mediante endpoints; por ahora solo existe `/health`.
5. **React:** interfaz para elegir región, variable y período, y visualizar series y tendencias.

Los contratos finales entre extracción, análisis, API y frontend aún no están definidos.

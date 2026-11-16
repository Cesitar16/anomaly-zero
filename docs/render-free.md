# Render Free: frontend estático y API Docker

Seguimiento: [FUL-139](https://linear.app/fullstack-track/issue/FUL-139/az-07-publicar-anomaly-zero-en-render-free-frontend-estatico-y-api).

Este despliegue crea dos servicios: `anomaly-zero-web` (Static Site, gratuito) y `anomaly-zero-api` (Web Service Docker, plan Free). No crea bases de datos, discos ni recursos pagados. `compose.yaml` sigue siendo el entorno local; no se usa como Dockerfile ni como Blueprint.

## Crear los servicios

1. En Render, elige **New → Blueprint** y conecta `Cesitar16/anomaly-zero`.
2. Selecciona la rama que contenga este cambio: `feature/render-free` para probarlo, o `dev` después de integrar la PR. Usa `render.yaml` de la raíz como Blueprint Path. Los servicios heredan la rama del Blueprint.
3. Revisa los recursos: backend **Free**, frontend **Static Site**. Crea el Blueprint con los dos servicios y espera sus builds.
4. Copia las URLs HTTPS reales asignadas a cada servicio. Render puede añadir sufijos; no deduzcas las URLs a partir de los nombres.

Alternativa manual si el flujo Blueprint solicita un método de pago: crea estos mismos servicios con **New → Web Service** y **New → Static Site**, usando la misma rama y los valores de la tabla. Mantén el backend en **Free** y no habilites recursos pagados.

| Campo | API: Web Service | Frontend: Static Site |
|---|---|---|
| Root Directory | Vacío (raíz del repositorio) | `frontend` |
| Language / Runtime | Docker | Static Site |
| Dockerfile Path | `backend/Dockerfile` | No aplica |
| Docker Build Context Directory | `.` | No aplica |
| Docker Command | Vacío (CMD de la imagen, puerto 8000) | No aplica |
| Build Command | Dockerfile | `npm ci && npm run build` |
| Publish Directory | No aplica | `dist` |
| Health Check Path | `/health` | No aplica |
| Variables iniciales | Ninguna | `NODE_VERSION=22`, `VITE_EXPLORE_API=http` |
| Rewrite SPA | No aplica | Source `/*`, Destination `/index.html`, Action `Rewrite` |

El sitio todavía no podrá consultar la API hasta completar el siguiente paso. No uses `frontend/Dockerfile`: su Nginx está configurado para la red de Compose.

## Enlazar las URLs

Los ejemplos siguientes son ficticios; sustitúyelos por las URLs reales del dashboard.

1. API → **Environment**: añade `ANOMALY_ZERO_FRONTEND_ORIGIN=https://mi-web.onrender.com` y elige **Save and deploy**. Debe ser solo el origen del frontend, sin `/explore`, query ni credenciales. No uses `*`. Sin esta variable, CORS permanece deshabilitado y el flujo local de mismo origen continúa funcionando.
2. Frontend → **Environment**: añade `VITE_API_BASE_URL=https://mi-api.onrender.com/api/v1`. Conserva `VITE_EXPLORE_API=http` y elige **Save, rebuild, and deploy**. El sufijo `/api/v1` es necesario; no añadas una barra al final. Vite incorpora las variables al compilar: guardar sin reconstruir no actualiza el sitio.
3. Estas dos variables se añaden después de conocer las URLs; el Blueprint no las sobrescribe en sincronizaciones posteriores. Si cambias un dominio, actualiza la variable correspondiente y vuelve a desplegar.

## Datos IMERG opcionales

La imagen excluye los datos NASA locales. Sin snapshot, la API arranca y las series responden `no_data`; el alojamiento no inventa datos ni habilita análisis científicos. La demo sintética sigue disponible seleccionando esa fuente en el explorador.

Para servir el snapshot auténtico ya verificado sin subirlo al repositorio:

1. En la API → **Environment → Secret Files**, añade `imerg_2005_point_snapshot.json` con el contenido del snapshot verificado. El total de archivos de este mecanismo no puede superar 1 MB.
2. Añade `ANOMALY_ZERO_IMERG_SNAPSHOT=/etc/secrets/imerg_2005_point_snapshot.json` y despliega de nuevo. Render monta estos archivos también en servicios Docker. No copies gránulos crudos, tokens Earthdata ni `.env` a la imagen o al frontend.
3. Comprueba la serie con `murray-darling-basin`, `P02` y `2005-01` a `2005-12`: doce meses, `synthetic:false`, `mm/hr`, `point_sample`. Conserva las limitaciones de QA indicadas por la API. Una ruta explícita sin archivo accesible da 503, no `no_data`.

## Comprobación final

- Abre `https://mi-api.onrender.com/health`: debe devolver `status: ok`.
- Abre `/api/v1/regions` en la API: debe responder el catálogo.
- Abre directamente `https://mi-web.onrender.com/explore?fuente=api` y recarga: no debe dar 404 ni errores CORS. Comprueba catálogos, serie y CSV si hay snapshot.
- Sin snapshot, comprueba el estado sin datos; cambia a demostración y verifica su aviso sintético.
- Registra las URLs y el resultado real de estas pruebas en FUL-139. No marques el despliegue como verificado solo porque la compilación pasó.

## Límites del plan Free

La API se suspende tras 15 minutos sin tráfico y el siguiente acceso puede tardar aproximadamente un minuto. Las 750 horas mensuales gratuitas se comparten entre los Web Services del workspace; el Static Site no consume esas horas. Los archivos escritos en el contenedor se pierden al reiniciar. No añadas un disco o una base de datos para este despliegue. Los archivos configurados mediante Secret Files se vuelven a montar al desplegar.

Para mantener costo cero, utiliza el plan de workspace gratuito y el backend Free, y revisa cuotas de transferencia y builds. Sin método de pago, al agotarse cuotas Render suspende servicios o nuevos builds; con método de pago puede cobrar excedentes. No actives upgrades para resolver límites durante esta publicación.

Referencias: [Blueprints](https://render.com/docs/blueprint-spec), [Docker](https://render.com/docs/docker), [Free](https://render.com/docs/free), [variables y Secret Files](https://render.com/docs/configure-environment-variables), [rutas SPA](https://render.com/docs/redirects-rewrites).

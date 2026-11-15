# Docker Compose para el MVP

Este entorno levanta FastAPI y una build estática de React servida por Nginx. Nginx entrega el frontend, conserva las rutas SPA y reenvía `/api/v1/*` al servicio `backend` dentro de la red privada de Compose. El entorno no descarga ni empaqueta datos NASA.

## Requisitos

- Docker Engine/Desktop con soporte para `docker compose`.
- Para datos IMERG reales, un directorio local `data/processed` que contenga `ful116/imerg_2005_point_snapshot.json`. El snapshot se monta en solo lectura; nunca se copia a la imagen ni a Git.
- Sin snapshot, FastAPI puede iniciar y devuelve `no_data` para la serie. Esto no representa una observación real.

## Configuración e inicio

Desde la raíz del repositorio, crea el archivo local de configuración:

```powershell
Copy-Item .env.example .env
```

En `.env`, `ANOMALY_ZERO_PROCESSED_DIR` debe apuntar al directorio `data/processed` del equipo. Si el snapshot se encuentra fuera de este checkout, se puede usar una ruta absoluta, por ejemplo `C:/Users/usuario/proyecto/data/processed`. Las otras variables controlan las IP de escucha y puertos publicados; por defecto ambos servicios solo aceptan conexiones locales (`127.0.0.1`). No pongas secretos en el archivo `.env`.

```powershell
docker compose config
docker compose build
docker compose up -d
docker compose ps
```

Accesos por defecto:

- Frontend: <http://127.0.0.1:8080>
- FastAPI directo (diagnóstico): <http://127.0.0.1:8000/health>
- FastAPI a través del proxy del frontend: <http://127.0.0.1:8080/health>

## Comprobaciones manuales

```powershell
Invoke-RestMethod http://127.0.0.1:8080/health
Invoke-RestMethod http://127.0.0.1:8080/api/v1/regions
Invoke-RestMethod 'http://127.0.0.1:8080/api/v1/products?region_id=murray-darling-basin'
Invoke-RestMethod 'http://127.0.0.1:8080/api/v1/series?region_id=murray-darling-basin&product_id=P02&start=2005-01&end=2005-12&frequency=monthly'
```

Con el snapshot validado, la respuesta de series debe conservar lo documentado en [BE-06](be-06-demo-runbook.md): `synthetic:false`, doce meses IMERG 2005, unidad `mm/hr` y soporte `point_sample`. La QA sigue en `basic_checks_only`, sin aprobación de QA del proveedor. La coincidencia temporal y el punto seleccionado no son una agregación regional ni una evaluación científica nueva.

## Logs y detención

```powershell
docker compose logs -f backend frontend
docker compose down
```

`docker compose down` detiene y elimina los contenedores de este proyecto; no elimina el directorio local de datos montado.

## Diagnóstico frecuente

- **Frontend muestra 502/504 para `/api/v1`:** revisa `docker compose ps` y `docker compose logs backend frontend`. Compose inicia el frontend después de que el healthcheck de FastAPI responde; verifica que ambos servicios estén saludables.
- **Serie devuelve `no_data`:** confirma que `.env` apunta al directorio que contiene `ful116/imerg_2005_point_snapshot.json`, que Docker Desktop puede acceder a ese directorio y que el nombre del archivo coincide. El montaje es de solo lectura.
- **Compose informa que no encuentra el directorio de datos:** crea el directorio configurado o corrige `ANOMALY_ZERO_PROCESSED_DIR`; la configuración evita crear silenciosamente una ruta vacía.
- **El puerto ya está ocupado:** cambia `FRONTEND_PORT` o `BACKEND_PORT` en `.env` y vuelve a ejecutar `docker compose up -d`.

La imagen incluye el frontend de la rama que se construya. Desde el merge de FE-04, `dev` sirve el explorador funcional en `/explore`; por defecto usa el modo de demostración. Para consultar explícitamente la API real, abre `/explore?fuente=api`. La infraestructura no implica que haya series reales para todos los productos: comprueba la disponibilidad indicada por la API y conserva las limitaciones científicas de cada producto.

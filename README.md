# Anomaly Zero

Aplicación científica web para investigar tendencias ambientales con datos de observación terrestre y modelos NASA. Desafío NASA Space Apps Challenge 2026: **Be an Earth Systems Trend Detective!**

El objetivo es seleccionar una región, variable y período histórico, visualizar series temporales y calcular tasas de cambio con su significancia estadística. La región inicial candidata es la cuenca Murray–Darling, Australia (enero de 2005–diciembre de 2024).

## Equipo

- César Rojas: Data Science, análisis estadístico y coordinación técnica.
- Lucas Moncada: investigación NASA, datasets y procesamiento científico.
- Alaín: backend, extracción e integración de datos.
- Alejandra Reyes: frontend, landing page y explorador.

## Tecnologías

React, TypeScript, Vite, npm; Python 3.12, FastAPI, Uvicorn, uv; NumPy, pandas, xarray, JupyterLab, SciPy, statsmodels, Matplotlib, earthaccess, netCDF4 y h5py.

## Estructura

```text
frontend/                 React + TypeScript generado con Vite
backend/app/              API, fuentes de datos y análisis
backend/tests/            Pruebas del backend
research/notebooks/       Investigación compartiendo el entorno uv
data/{raw,processed,cache}/ Datos locales excluidos de Git
docs/                     Arquitectura, productos candidatos y decisiones
```

## Requisitos

Node.js y npm, Python 3.12 disponible mediante uv, uv y Git. GitHub CLI se necesita solo para publicar el repositorio.

## Instalación y ejecución

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Entorno Python desde la raíz:

```bash
uv sync --group research --group dev
```

FastAPI (desde la raíz):

```bash
uv run uvicorn backend.app.main:app --reload
```

La API queda en `http://127.0.0.1:8000`; salud en `/health` y documentación en `/docs`.

Pruebas y lint:

```bash
uv run pytest
uv run ruff check backend
```

Notebooks:

```bash
uv run jupyter lab research/notebooks
```

## Seguimiento

Tarjeta de Linear: [FUL-98](https://linear.app/fullstack-track/issue/FUL-98).

Contribuciones y flujo Git: [CONTRIBUTING.md](CONTRIBUTING.md). Las pull requests usan la [plantilla del proyecto](.github/PULL_REQUEST_TEMPLATE.md). Este repositorio se distribuye bajo la [licencia MIT](LICENSE).

## Estado

Base inicial configurada: plantilla React + TypeScript de Vite y API mínima con `GET /health`. FUL-101 incorpora un piloto puntual de NASA POWER T2M. FUL-103 incorpora descubrimiento CMR de MERRA-2, IMERG y GLDAS, además de una descarga autenticada y acotada de GLDAS; FUL-105 añade EDA de un único mes GLDAS sobre un rectángulo. Los tres productos siguen siendo candidatos, sin serie regional de cuenca ni tendencias validadas. El frontend todavía es el starter Vite; siguen pendientes la validación científica, el procesamiento regional, los contratos y el explorador.

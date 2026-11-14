# Guía de contribución

Esta guía establece el flujo de trabajo del equipo para Anomaly Zero. Las reglas describen el proceso acordado; no están aplicadas mediante protección automática de ramas en GitHub.

## Flujo Gitflow

Usaremos Gitflow con estas ramas:

- main: historial estable y versiones listas para integrar/publicar.
- develop: integración del trabajo completado para la siguiente entrega.
- feature/nombre: funcionalidades iniciadas desde develop.
- release/version: preparación y estabilización de una entrega, iniciada desde develop.
- hotfix/nombre: correcciones urgentes de producción, iniciadas desde main.

### Crear una funcionalidad

    git switch develop
    git pull origin develop
    git switch -c feature/nombre-breve

Al terminar, publica la rama y abre una pull request hacia develop:

    git push -u origin feature/nombre-breve

Usa una rama por cambio coherente. No trabajes directamente sobre main ni develop.

### Releases y correcciones urgentes

- Una rama release/version sale de develop. En ella se permiten correcciones de estabilización y documentación de la entrega. Al terminar, se integra en main y se devuelve a develop para mantener ambos historiales alineados.
- Una rama hotfix/nombre sale de main. Al terminar, se integra en main y también se incorpora a develop (o a la release activa) para que la corrección no se pierda.
- Las integraciones se hacen mediante pull requests y revisión del equipo. No uses --force para publicar ramas compartidas.

### Estado actual de ramas

El repositorio mantiene main como rama estable y develop como rama de integración. No se han habilitado reglas de protección ni automatizaciones; esa configuración queda pendiente de decisión del equipo.

## Pull requests

1. Actualiza la rama base y resuelve conflictos en tu rama de trabajo.
2. Completa la [plantilla de pull request](.github/PULL_REQUEST_TEMPLATE.md), incluyendo el impacto científico si aplica.
3. Ejecuta verificaciones pertinentes y registra sus resultados. No afirmes que una prueba pasó si no la ejecutaste.
4. Revisa que no incluyas credenciales, tokens ni archivos de datos NASA locales.
5. Solicita revisión a las personas responsables del área afectada.
6. Integra el cambio solo después de resolver comentarios y confirmar que la rama destino es la correcta.

## Áreas y responsables

- Data Science y coordinación técnica: César Rojas.
- Investigación NASA, datasets y procesamiento científico: Lucas Moncada.
- Backend, extracción e integración: Alaín.
- Frontend, landing y explorador: Alejandra Reyes.

Los cambios transversales pueden solicitar revisión de más de un área.

## Cuidado de datos y credenciales

- Mantén archivos originales en data/raw/, productos derivados en data/processed/ y archivos temporales en data/cache/; su contenido está excluido de Git.
- No subas credenciales Earthdata, archivos .env, tokens ni datos personales. Usa .env.example solo para documentar nombres de variables y valores ficticios.
- Registra procedencia, versión, período, unidades y transformaciones de cualquier muestra o resultado científico que se apruebe para versionar.

## Convenciones prácticas

- Mantén los cambios pequeños, enfocados y descritos con lenguaje claro.
- Prefiere nombres de ramas descriptivos en minúsculas separados por guiones.
- Escribe mensajes de commit breves y en modo imperativo; no existe todavía un formato obligatorio.
- Documenta decisiones de métodos, supuestos y limitaciones junto al código o en docs/.
- No añadas nuevas dependencias o servicios fuera del alcance de la tarea sin explicar su necesidad en la pull request.

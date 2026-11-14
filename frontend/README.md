# Anomaly Zero · Frontend (landing pública, FE-01)

Aplicación React + TypeScript del monorepositorio de Anomaly Zero (NASA Space Apps Challenge 2026). Hoy contiene la landing pública: problema, propuesta, cómo funciona, equipo, fuentes y acceso futuro al explorador.

> **Alcance honesto.** Esta landing no se conecta a la NASA, a FastAPI ni a autenticación, y no muestra datos, tendencias, valores p ni mapas. La ruta `/explore` es un placeholder explícito "En desarrollo".

## Requisitos

- Node.js 20 o superior (probado con Node 22)
- npm 10 o superior

No necesita backend, variables de entorno ni credenciales. Las fuentes están autoalojadas (paquetes `@fontsource`), así que la página no hace ninguna petición a servicios externos.

## Cómo ejecutarla

```bash
cd frontend
npm install
npm run dev        # servidor de desarrollo en http://localhost:5173
```

Otros comandos:

| Comando           | Para qué sirve                                                          |
| ----------------- | ----------------------------------------------------------------------- |
| `npm run build`   | Revisa tipos (`tsc -b`) y compila a `dist/`                             |
| `npm run preview` | Sirve la compilación en http://localhost:4173                           |
| `npm test`        | Pruebas con vitest: estructura, accesibilidad (axe), contraste, contenido |
| `npm run lint`    | Oxlint (el linter del scaffold oficial de Vite)                         |

## Rutas

| Ruta           | Contenido                                                      |
| -------------- | -------------------------------------------------------------- |
| `/`            | Landing con todas las secciones                                |
| `/explore`     | Placeholder del explorador, claramente marcado "En desarrollo" |
| cualquier otra | Página 404 con enlace al inicio                                |

Como la app usa rutas reales (`BrowserRouter`), el hosting debe devolver `index.html` para cualquier ruta (fallback de SPA). Vite ya lo hace en `dev` y `preview`. Aún no hay proveedor de hosting elegido; cuando exista, hay que configurar esa regla.

## Estructura

```
frontend/
├── index.html
├── public/favicon.svg
├── src/
│   ├── main.tsx                 punto de entrada: fuentes, estilos y router
│   ├── App.tsx                  tabla de rutas
│   ├── types.ts                 tipos compartidos (BadgeStatus, ButtonVariant, SectionTone)
│   ├── config/site.ts           nombre, rutas, ids de sección y feature flag del explorador
│   ├── content/                 TODO el texto de la landing, por sección, con tipos
│   ├── components/
│   │   ├── ui/                  piezas reutilizables: Section, Container, Badge, ButtonLink, ExternalLink, ExplorerCta
│   │   ├── layout/              Layout, Navbar, Footer, SkipLink, ScrollManager, Logo
│   │   └── sections/            Hero, Problem, Solution, HowItWorks, Team, Sources, ExplorerAccess
│   ├── pages/                   LandingPage, ExplorerPage, NotFoundPage
│   ├── hooks/useDocumentTitle.ts
│   ├── utils/getInitials.ts
│   ├── services/                vacío a propósito: aquí irá el cliente de la API cuando exista el contrato (AZ-04)
│   ├── styles/                  tokens.css, base.css, components.css, sections.css
│   └── test/                    pruebas (excluidas de la compilación de la app, ver tsconfig.test.json)
└── docs/
    ├── FE-01-evidencia.md       cierre de la tarjeta: criterios, hallazgos, decisiones abiertas
    └── capturas/                capturas de móvil, tablet y escritorio
```

## Cómo editar sin romper nada

- **Cambiar un texto:** edita el archivo de `src/content/` de esa sección. Los componentes no contienen texto de negocio.
- **Cambiar un color o tamaño:** `src/styles/tokens.css`. Si un cambio rompe el contraste mínimo (WCAG AA), `npm test` falla y te dice qué par de colores es.
- **Agregar una sección:** crea el contenido tipado en `content/`, un componente en `components/sections/` que use `<Section>` y agrégalo en `pages/LandingPage.tsx`.
- **Publicar el explorador real:** pon `EXPLORER_AVAILABLE = true` en `src/config/site.ts` y reemplaza el contenido de `pages/ExplorerPage.tsx`.

## Patrones de diseño usados

| Patrón                                      | Dónde                                    | Para qué                                                              |
| ------------------------------------------- | ---------------------------------------- | --------------------------------------------------------------------- |
| Separación datos / presentación             | `content/*` y `components/sections/*`    | Revisar o cambiar textos sin tocar componentes                        |
| Composición                                 | `Section`, `Container`                   | Todas las secciones comparten estructura sin herencia                 |
| Layout Route (React Router)                 | `Layout` con `Outlet`                    | Navbar, pie y saltar al contenido se escriben una sola vez            |
| Feature flag                                | `EXPLORER_AVAILABLE`                     | Un único interruptor para pasar de placeholder a explorador real      |
| Componente polimórfico con unión discriminada | `ButtonLink` (`to` o `href`, nunca ambos) | El compilador impide mezclar enlace interno y externo                 |
| Design tokens                               | `styles/tokens.css`                      | Un solo lugar para colores y tamaños, vigilado por el test de contraste |
| Custom hook                                 | `useDocumentTitle`                       | Encapsula el efecto secundario de cambiar el título                   |

## Reglas de contenido (restricciones de FE-01)

`src/test/content.test.ts` protege estas reglas automáticamente:

- No se publican tendencias, valores p, porcentajes ni afirmaciones de cambio observado.
- No se publican correos, teléfonos ni redes del equipo. Tampoco fotografías.
- Todo recurso NASA tiene responsable y enlace `https`; cada producto candidato tiene DOI.
- El aviso de proyecto independiente (sin respaldo de la NASA) se mantiene.

## Accesibilidad

- Idioma `es`, un solo `h1`, jerarquía `h1 > h2 > h3 > h4` y landmarks (`header`, `nav`, `main`, `footer`).
- Enlace "Saltar al contenido principal" como primer elemento enfocable.
- Navegación completa con teclado; foco visible en cualquier fondo. Menú móvil con `aria-expanded`, `aria-controls` y cierre con Escape.
- Al navegar con un ancla o a otra ruta, el foco pasa al título de la sección o a `<main>`.
- Estados (Disponible, En desarrollo, Planificado) siempre en texto, nunca solo en color.
- Contraste AA verificado por pruebas sobre los tokens reales.
- Objetivos táctiles de al menos 24 px; respeta `prefers-reduced-motion`.
- Enlaces externos con `rel="noopener noreferrer"` y aviso para lectores de pantalla.

## Verificación realizada

- `npx tsc -b`, `npm run build` y `npm run lint` sin errores ni avisos.
- `npm test`: 48 pruebas pasando (estructura, axe, contraste, contenido).
- Chrome en 320, 390, 768 y 1440 px de ancho: sin desbordamiento horizontal, sin errores de consola y sin peticiones externas. Capturas en `docs/capturas/`.
- Teclado, anclas, menú móvil, recarga en `/explore` y 404 probados con Playwright sobre la compilación.

No se probó con un lector de pantalla real (NVDA, VoiceOver) ni en dispositivos físicos. Conviene hacerlo en la revisión.

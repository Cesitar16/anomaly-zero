# FE-01 · Evidencia de cierre

Landing pública de Anomaly Zero en React + TypeScript (Linear: FUL-100). Documento para la revisión de César, Lucas y la persona que haga la revisión técnica.

**Estado: listo para revisión. No marcar como completada hasta cerrar los puntos marcados como pendientes.**

## Entregables

| Entregable                          | Dónde                                                        |
| ----------------------------------- | ------------------------------------------------------------ |
| Código de la landing                | `frontend/src/`                                              |
| Ruta prevista del explorador        | `/explore` (`src/pages/ExplorerPage.tsx`)                    |
| Documentación de arranque           | `frontend/README.md`                                         |
| Capturas móvil, tablet y escritorio | `frontend/docs/capturas/`                                    |
| Rama                                | `feature/ful-100-fe-01-landing-page` (sale de `dev`)         |
| URL de la PR                        | **Pendiente.** Se completa al abrir la PR                    |

## Cómo reproducirla o inspeccionarla

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
npm test         # estructura, accesibilidad, contraste y reglas de contenido
npm run build && npm run preview   # http://localhost:4173
```

## Criterios de aceptación (Definition of Done)

| Criterio | Estado | Cómo se comprobó |
| --- | --- | --- |
| Secciones problema, solución, funcionamiento, equipo, fuentes y acceso futuro, accesibles y coherentes | Cumplido | Prueba automática por sección (región con nombre) y revisión visual |
| Sin desbordamientos ni controles inutilizables en escritorio y móvil; teclado y jerarquía semántica | Cumplido | Chrome a 320, 390, 768 y 1440 px: ancho de scroll igual al del viewport; orden de Tab, anclas y menú móvil probados; axe sin violaciones; ningún control bajo 24 px |
| Carga sin backend ni credenciales externas e integrada al repositorio aprobado | Parcial | Sin backend ni peticiones externas verificado. Código integrado en la rama `feature/ful-100-fe-01-landing-page`; **falta subirla y abrir la PR** |
| Todos los claims sobre NASA atribuidos; sin falso respaldo ni datos calculados | Cumplido, falta revisión de contenido | Pruebas de contenido (sin cifras, valores p ni afirmaciones de cambio; DOI y responsable por producto; aviso de independencia) |
| El enlace al explorador no conduce a una experiencia engañosa | Cumplido | `/explore` es un placeholder explícito sin ningún dato ni gráfico, también probado |
| Revisión de contenido por César/Lucas y revisión técnica de código por otra persona; README | **Pendiente** (README hecho) | Requiere a las personas revisoras |

## Hallazgos y decisiones que siguen abiertas

1. **Referencia a AZ-01 (resuelta).** En el Excel, AZ-01 es "Congelar catálogo y versiones", pero en Linear AZ-01 es FUL-98, "Inicializar monorepositorio React/TypeScript + FastAPI/Python y GitHub", ya cerrada, y es la que bloquea a FE-01. Se tomó la numeración de Linear. La landing se aplicó sobre el `frontend/` real de `dev` (scaffold `react-ts` con el `.oxlintrc.json` del equipo) y se verificó ahí: `tsc -b`, `oxlint`, 48 pruebas y `build` sin errores.
2. **Roles del equipo sin confirmar.** Los roles de la sección Equipo siguen a los "responsables funcionales" de la descripción del proyecto en Linear. La tarjeta pide roles consensuados: cada integrante debe confirmar el suyo. Alaín aparece sin apellido, como en los documentos; confirmar cómo quiere figurar.
3. **Alcance técnico publicado como propuesta.** La tarjeta pide mencionar tres variables candidatas. Además se incluyó la región candidata (cuenca Murray-Darling), el período aproximado 2005 a 2025 y los productos candidatos (MERRA-2, GPM IMERG, GLDAS) con su DOI, marcados como "propuesta de trabajo", porque Linear los registra como no aprobados (AZ-03 sigue pendiente). Si el equipo prefiere no hacerlos públicos todavía, se quitan en `src/content/howItWorks.ts` (`scopeNote` y `product`) y `src/content/sources.ts` (`products`).
4. **Enlaces a Space Apps.** Se enlazan el desafío, la página del equipo y la del evento local de Santiago. La página del equipo es contenido generado por participantes (Space Apps lo avisa en la propia página). El enlace del desafío viene del catálogo del equipo, que el 14-11-2026 registraba errores 502/503 al abrirlo: conviene comprobar que abra antes de la demostración. No se publicó nombre ni correo del Local Lead del evento.
5. **Sin proveedor de hosting.** Las rutas reales exigen que el hosting reescriba cualquier ruta a `index.html`.
6. **Pruebas pendientes.** No se probó con lector de pantalla real ni en dispositivos físicos; solo en Chrome con viewports emulados.
7. **Estado en Linear.** FUL-100 sigue en "Todo" y sin comentarios. No se modificó nada en Linear. Según el documento de gobernanza, para cerrar hay que enlazar PR o artefacto, comprobar los criterios uno a uno y tener revisión ajena.
8. **Rama base.** `CONTRIBUTING.md` habla de `develop`, pero el repo tiene `dev` y las PR recientes (#5 y #7) se integraron ahí. La rama sale de `dev`. Confirmar a qué rama debe apuntar la PR.
9. **Metadatos en imágenes.** Las capturas y `public/favicon.svg` llevan metadatos de procedencia C2PA (Content Credentials de Anthropic) añadidos al copiarlos. No cambian cómo se ven; el favicon pesa por eso unos 8 KB. Se puede reemplazar por una versión limpia si se prefiere.

## Decisiones tomadas

- Un solo proyecto React con rutas (`/`, `/explore`), no una web separada, en línea con la decisión de Linear: "landing y portal científico bajo la misma aplicación web".
- Todo el texto vive en `src/content/` para que la revisión de contenido no requiera tocar componentes.
- El estado del explorador se controla con un único feature flag (`EXPLORER_AVAILABLE`).
- Fuentes autoalojadas para que la página no dependa de ningún servicio externo.
- Sin fotografías ni datos de contacto del equipo, según la restricción de la tarjeta.
- TypeScript estricto sobre el scaffold oficial, con las mismas reglas que trae (`verbatimModuleSyntax`, `erasableSyntaxOnly`, variables sin usar prohibidas).
- `src/services/` queda vacío a propósito: la landing no consume API y el contrato lo define AZ-04.

## Desbloquea

FE-02 (FUL-109) puede usar como base visual los tokens (`styles/tokens.css`), los componentes de `components/ui/` y el `Layout`.

// MapLibre GL JS 6 resuelve su worker como un archivo hermano (`./maplibre-gl-worker.mjs`) relativo al
// módulo que lo importa. Al empaquetar con Vite, ese archivo no existe junto al bundle y el mapa falla
// con "Worker failed to load" (probado en `vite dev` y en `vite build`). Vite puede empaquetar el worker
// con sus dependencias y devolver su URL (`?worker&url`); se la entregamos a MapLibre antes de crear el mapa.
import { setWorkerUrl } from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'

setWorkerUrl(workerUrl)

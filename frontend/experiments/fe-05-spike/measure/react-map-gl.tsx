import 'maplibre-gl/dist/maplibre-gl.css'
import { createRoot } from 'react-dom/client'
import { Map } from 'react-map-gl/maplibre'
import '../src/lib/maplibreWorker'

createRoot(document.getElementById('root') as HTMLElement).render(
  <Map mapStyle={{ version: 8, sources: {}, layers: [] }} initialViewState={{ longitude: 145, latitude: -31, zoom: 4 }} style={{ width: 400, height: 300 }} />,
)

import 'maplibre-gl/dist/maplibre-gl.css'
import { Map } from 'maplibre-gl'
import '../src/lib/maplibreWorker'

const container = document.getElementById('root') as HTMLElement
new Map({ container, style: { version: 8, sources: {}, layers: [] }, center: [145, -31], zoom: 4 })

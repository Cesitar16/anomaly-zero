import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

// Fuentes autoalojadas (sin peticiones a servicios externos)
import '@fontsource-variable/fraunces'
import '@fontsource/ibm-plex-sans/latin-400.css'
import '@fontsource/ibm-plex-sans/latin-500.css'
import '@fontsource/ibm-plex-sans/latin-600.css'
import '@fontsource/ibm-plex-mono/latin-500.css'

import './styles/tokens.css'
import './styles/base.css'
import './styles/components.css'
import './styles/sections.css'

import App from './App'

const rootElement = document.getElementById('root')
if (!rootElement) throw new Error('No se encontró el elemento #root en index.html')

createRoot(rootElement).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)

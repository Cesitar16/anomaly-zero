import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// Destino del proxy de desarrollo hacia FastAPI. Se lee del entorno del proceso de Vite (no es un secreto
// `VITE_*`, no llega al navegador) y por defecto apunta al backend local.
const apiTarget = process.env.API_PROXY_TARGET ?? 'http://127.0.0.1:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // La app llama a `/api/v1` en el mismo origen; Vite lo reenvía al backend. Sin CORS abierto en FastAPI.
    proxy: {
      '/api/v1': { target: apiTarget, changeOrigin: false },
      '/health': { target: apiTarget, changeOrigin: false },
    },
  },
  preview: {
    proxy: {
      '/api/v1': { target: apiTarget, changeOrigin: false },
      '/health': { target: apiTarget, changeOrigin: false },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
    css: false,
  },
})

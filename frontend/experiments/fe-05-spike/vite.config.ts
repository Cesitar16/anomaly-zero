import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// Spike aislado: no comparte node_modules ni lockfile con la app de producción (frontend/).
// fs.allow deja importar los tokens de diseño de la landing sin copiarlos.
export default defineConfig({
  plugins: [react()],
  server: { fs: { allow: ['../..'] } },
  build: { chunkSizeWarningLimit: 1500 },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
    css: false,
    // Los archivos se llaman *.check.* a propósito: el vitest de la landing (frontend/) usa el patrón por
    // defecto *.test.* desde su raíz y recogería estas pruebas. Con este nombre no las ve y no hace falta
    // tocar frontend/vite.config.ts.
    include: ['src/test/**/*.check.{ts,tsx}'],
  },
})

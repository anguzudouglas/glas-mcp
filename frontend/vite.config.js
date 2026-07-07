import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  build: {
    // Output directly into glas_mcp/static so FastAPI can serve it
    outDir: resolve(__dirname, '../glas_mcp/static'),
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      '/api':      { target: 'http://localhost:8000', changeOrigin: true },
      '/sse':      { target: 'http://localhost:8000', changeOrigin: true },
      '/health':   { target: 'http://localhost:8000', changeOrigin: true },
      '/messages': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})

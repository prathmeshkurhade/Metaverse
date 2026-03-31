import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// WHY proxy?
// In development, the frontend runs on port 5173 (Vite) but the API is on port 8000.
// The proxy forwards /api requests to the backend, avoiding CORS issues in dev.
// In production (Docker/Nginx), Nginx handles this routing instead.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // WHY does /api/v1/ai come BEFORE /api?
      // Vite matches proxies top-to-bottom. Without this, /api/v1/ai/chat
      // would match /api first and go to port 8000 (HTTP API) instead of
      // port 8002 (AI Assistant). More specific routes must come first.
      '/api/v1/ai': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8001',
        ws: true,
      },
    },
  },
})

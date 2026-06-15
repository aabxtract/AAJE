import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const backendProxy = {
  // Legacy domain-folder routes
  '/api': { target: 'http://localhost:8000', changeOrigin: true },
  '/flow': { target: 'http://localhost:8000', changeOrigin: true },
  // Shared infra
  '/auth': { target: 'http://localhost:8000', changeOrigin: true },
  '/health': { target: 'http://localhost:8000', changeOrigin: true },
  // New layer-per-concern routes (MVP)
  '/store': { target: 'http://localhost:8000', changeOrigin: true },
  '/products': { target: 'http://localhost:8000', changeOrigin: true },
  '/orders': { target: 'http://localhost:8000', changeOrigin: true },
  '/bizprint': { target: 'http://localhost:8000', changeOrigin: true },
  '/webhook': { target: 'http://localhost:8000', changeOrigin: true },
  '/templates': { target: 'http://localhost:8000', changeOrigin: true },
  '/onboarding': { target: 'http://localhost:8000', changeOrigin: true },
}

// Wildcard hosts so <slug>.localtest.me works in dev/preview without
// /etc/hosts edits. localtest.me resolves to 127.0.0.1 for any subdomain.
const allowedHosts = ['.localtest.me', '.aaje.store', 'localhost', '127.0.0.1']

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    host: true,
    allowedHosts,
    proxy: backendProxy,
  },
  preview: {
    port: 4173,
    host: true,
    allowedHosts,
    proxy: backendProxy,
  },
})

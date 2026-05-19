import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(__dirname, '..')
const certPath = path.join(repoRoot, 'config', 'certs', 'dev-cert.pem')
const keyPath = path.join(repoRoot, 'config', 'certs', 'dev-key.pem')

function readDevHttpsOptions(): { key: Buffer; cert: Buffer } | undefined {
  const useHttpsDev =
    process.env.VITE_DEV_HTTPS === '1' || process.env.VITE_DEV_HTTPS === 'true'
  if (!useHttpsDev) return undefined

  try {
    if (!fs.existsSync(certPath) || !fs.existsSync(keyPath)) {
      console.warn(
        '[vite] VITE_DEV_HTTPS aktiv, aber Dateien config/certs/dev-cert.pem oder dev-key.pem fehlen — starte ohne HTTPS.',
      )
      return undefined
    }
    return {
      cert: fs.readFileSync(certPath),
      key: fs.readFileSync(keyPath),
    }
  } catch (e) {
    console.warn('[vite] HTTPS-Zertifikate konnten nicht gelesen werden — starte ohne HTTPS.', e)
    return undefined
  }
}

const devHttps = readDevHttpsOptions()

const backendDevProxyTarget = 'http://localhost:30610'
const devServerProxy = {
  '/api': {
    target: backendDevProxyTarget,
    changeOrigin: true,
    secure: false,
  },
  '/uploads': {
    target: backendDevProxyTarget,
    changeOrigin: true,
    secure: false,
  },
} as const

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'pwa-192.svg', 'pwa-512.svg'],
      manifest: {
        name: 'Freiraum Baustellen-Doku',
        short_name: 'Baustellen-Doku',
        description: 'Tagesberichte für Handwerk — aus dem Kopf, aus dem Sinn.',
        theme_color: '#f97316',
        background_color: '#09090b',
        display: 'standalone',
        scope: '/',
        start_url: '/',
        icons: [
          {
            src: '/pwa-192.svg',
            sizes: '192x192',
            type: 'image/svg+xml',
            purpose: 'any',
          },
          {
            src: '/pwa-512.svg',
            sizes: '512x512',
            type: 'image/svg+xml',
            purpose: 'any',
          },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
      },
    }),
  ],
  server: {
    host: '0.0.0.0',
    port: 51710,
    strictPort: true,
    ...(devHttps ? { https: devHttps } : {}),
    proxy: devServerProxy,
  },
  preview: {
    host: '0.0.0.0',
    port: 51710,
    strictPort: true,
    ...(devHttps ? { https: devHttps } : {}),
    proxy: devServerProxy,
  },
})

/// <reference types="vite/client" />
/// <reference types="vite-plugin-pwa/client" />

interface ImportMetaEnv {
  /**
   * Optional: volle Basis-URL des Backends (z. B. anderes Hosting).
   * Ohne gesetzten Wert: im Browser relative Aufrufe `/api`, `/uploads` (Vite-Dev-Proxy).
   */
  readonly VITE_API_BASE_URL?: string
}

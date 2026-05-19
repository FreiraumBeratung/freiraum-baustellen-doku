import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import './index.css'
import App from './App.tsx'

// PWA Service Worker (vite-plugin-pwa, dev: nur nach build aktiv)
import { registerSW } from 'virtual:pwa-register'

registerSW({
  immediate: true,
  onOfflineReady() {},
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)

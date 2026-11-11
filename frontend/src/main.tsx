import React from 'react'
import ReactDOM from 'react-dom/client'
import { App } from './app/App'
import { AppProviders } from './app/providers'
import './styles/index.css'

// Automatically recover from stale chunks caused by newer Vercel deployments
window.addEventListener('vite:preloadError', (event) => {
  console.warn('Vite preload error detected, reloading to fetch latest assets...', event)
  window.location.reload()
})

window.addEventListener('error', (event) => {
  const msg = (event.message || '').toLowerCase()
  if (
    msg.includes('failed to fetch dynamically imported module') ||
    msg.includes('error loading dynamically imported module')
  ) {
    const lastReload = parseInt(sessionStorage.getItem('last_chunk_reload') || '0', 10)
    const now = Date.now()
    if (now - lastReload > 8000) {
      sessionStorage.setItem('last_chunk_reload', String(now))
      window.location.reload()
    }
  }
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AppProviders>
      <App />
    </AppProviders>
  </React.StrictMode>,
)

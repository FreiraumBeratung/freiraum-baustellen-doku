import { useEffect } from 'react'
import { forcePwaRepaint } from '../utils/pwaRepaint'

/** Hilft gegen schwarzen PWA-Screen nach Rueckkehr aus der nativen Kamera/Galerie. */
export function useMobilePwaRepaint() {
  useEffect(() => {
    const onVisibility = () => {
      if (document.visibilityState === 'visible') forcePwaRepaint()
    }

    window.addEventListener('pageshow', forcePwaRepaint)
    document.addEventListener('visibilitychange', onVisibility)
    return () => {
      window.removeEventListener('pageshow', forcePwaRepaint)
      document.removeEventListener('visibilitychange', onVisibility)
    }
  }, [])
}

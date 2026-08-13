import { useMemo } from 'react'
import { isTabletDevice } from '../utils/isTabletDevice'

export type PhotoUploadOverlayMode = 'off' | 'active' | 'success' | 'closing'

type PhotoUploadOverlayProps = {
  mode: PhotoUploadOverlayMode
  message: string
}

/**
 * Inline-Overlay (kein Portal) — bleibt in der App-Ebene.
 * Halbtransparent, unten als Karte: weniger dominant, iOS composited die Seite darunter mit.
 */
export function PhotoUploadOverlay({ mode, message }: PhotoUploadOverlayProps) {
  // Nur Tablet breiter — Handy-Overlay bleibt max-w-[390px].
  const cardMax = useMemo(() => (isTabletDevice() ? 'max-w-[720px]' : 'max-w-[390px]'), [])

  if (mode === 'off') return null

  const isSuccess = mode === 'success'
  const isClosing = mode === 'closing'
  const label = message || (isSuccess ? 'Foto übernommen' : 'Foto wird übernommen…')

  return (
    <div
      className={`fixed inset-0 z-[100] flex items-end justify-center px-4 pb-[calc(6.75rem+env(safe-area-inset-bottom,0px))] transition-opacity duration-300 ease-out ${
        isClosing ? 'pointer-events-none opacity-0' : 'opacity-100'
      }`}
      style={{ backgroundColor: isClosing ? 'rgba(9,9,11,0)' : 'rgba(9,9,11,0.45)' }}
      role="status"
      aria-live="polite"
      aria-busy={!isSuccess && !isClosing}
    >
      <div className={`w-full ${cardMax} rounded-2xl border border-zinc-700/70 bg-zinc-900/95 px-4 py-3.5 shadow-lg shadow-black/40`}>
        <div className="flex items-center gap-3">
          {isSuccess ? (
            <span
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-500/15 text-sm text-emerald-400"
              aria-hidden
            >
              ✓
            </span>
          ) : (
            <div
              className="h-8 w-8 shrink-0 animate-spin rounded-full border-2 border-orange-500/25 border-t-orange-400"
              aria-hidden
            />
          )}
          <div className="min-w-0 text-left">
            <p className="text-sm font-medium text-white">{label}</p>
            {!isSuccess ? (
              <p className="mt-0.5 text-xs text-zinc-400">Bitte kurz warten…</p>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  )
}

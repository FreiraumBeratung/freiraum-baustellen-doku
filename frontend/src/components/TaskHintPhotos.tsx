import { useEffect, useState } from 'react'
import {
  deleteTaskHintPhoto,
  listTaskHintPhotos,
  resolveBackendPublicUrl,
  type ReportPhoto,
} from '../api/client'

export function TaskHintPhotos({
  taskId,
  count,
  canManage,
  writeBlocked,
  onChanged,
}: {
  taskId: string
  count: number
  canManage: boolean
  writeBlocked: boolean
  onChanged?: () => void
}) {
  const [open, setOpen] = useState(false)
  const [photos, setPhotos] = useState<ReportPhoto[]>([])
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [viewer, setViewer] = useState<{ src: string; alt: string } | null>(null)

  useEffect(() => {
    if (!open) return
    let cancelled = false
    setBusy(true)
    setErr('')
    void listTaskHintPhotos(taskId)
      .then((res) => {
        if (!cancelled) setPhotos(Array.isArray(res.photos) ? res.photos : [])
      })
      .catch((ex) => {
        if (!cancelled) setErr(ex instanceof Error ? ex.message : 'Foto konnte nicht geladen werden.')
      })
      .finally(() => {
        if (!cancelled) setBusy(false)
      })
    return () => {
      cancelled = true
    }
  }, [open, taskId])

  useEffect(() => {
    if (!viewer) return
    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setViewer(null)
    }
    window.addEventListener('keydown', onKey)
    return () => {
      document.body.style.overflow = prevOverflow
      window.removeEventListener('keydown', onKey)
    }
  }, [viewer])

  if (count <= 0) return null

  async function removePhoto(photoId: string) {
    if (!canManage || writeBlocked || busy) return
    setBusy(true)
    setErr('')
    try {
      await deleteTaskHintPhoto(taskId, photoId)
      const next = photos.filter((p) => p.id !== photoId)
      setPhotos(next)
      setViewer(null)
      if (!next.length) setOpen(false)
      onChanged?.()
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : 'Foto konnte nicht entfernt werden.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation()
          setOpen((cur) => !cur)
          setViewer(null)
        }}
        className="rounded-xl border border-white/[0.12] bg-black/40 px-2.5 py-1.5 text-xs font-medium text-zinc-200"
      >
        {open ? 'Foto schließen' : count > 1 ? `Foto ansehen (${count})` : 'Foto ansehen'}
      </button>
      {open ? (
        <div className="space-y-2 rounded-2xl border border-white/[0.08] bg-black/30 p-2.5">
          <p className="text-[0.7rem] font-medium uppercase tracking-wide text-zinc-500">
            Hinweis vom Chef
          </p>
          {busy && !photos.length ? <p className="text-xs text-zinc-500">Lädt…</p> : null}
          {photos.length ? (
            <ul className="grid grid-cols-2 gap-2">
              {photos.map((photo) => {
                const src = resolveBackendPublicUrl(photo.url) ?? photo.url ?? ''
                const alt = photo.originalFilename || 'Hinweis-Foto'
                return (
                  <li
                    key={photo.id}
                    className="relative overflow-hidden rounded-xl border border-white/[0.08] bg-zinc-950"
                  >
                    {src ? (
                      <button
                        type="button"
                        className="block h-36 w-full"
                        onClick={(e) => {
                          e.stopPropagation()
                          setViewer({ src, alt })
                        }}
                      >
                        <img
                          src={src}
                          alt={alt}
                          className="h-36 w-full object-cover"
                          loading="lazy"
                          decoding="async"
                        />
                      </button>
                    ) : (
                      <div className="flex h-36 items-center justify-center text-xs text-zinc-600">Foto</div>
                    )}
                    {canManage ? (
                      <button
                        type="button"
                        disabled={busy || writeBlocked}
                        aria-label="Hinweis-Foto entfernen"
                        className="absolute right-1 top-1 rounded-md bg-black/70 px-1.5 py-0.5 text-xs text-zinc-200 hover:bg-red-900/80 disabled:opacity-40"
                        onClick={(e) => {
                          e.stopPropagation()
                          void removePhoto(photo.id)
                        }}
                      >
                        ✕
                      </button>
                    ) : null}
                  </li>
                )
              })}
            </ul>
          ) : !busy ? (
            <p className="text-xs text-zinc-500">Kein Foto gefunden.</p>
          ) : null}
          {err ? <p className="text-xs text-red-400">{err}</p> : null}
        </div>
      ) : null}
      {viewer ? (
        <div
          className="fixed inset-0 z-[120] flex flex-col bg-black/92 px-3 pb-[calc(1rem+env(safe-area-inset-bottom,0px))] pt-[calc(0.75rem+env(safe-area-inset-top,0px))]"
          role="dialog"
          aria-modal="true"
          aria-label="Hinweis-Foto"
          onClick={(e) => {
            e.stopPropagation()
            setViewer(null)
          }}
        >
          <div className="mb-3 flex justify-end">
            <button
              type="button"
              className="rounded-xl border border-white/[0.12] bg-black/50 px-3 py-1.5 text-xs font-medium text-zinc-200"
              onClick={(e) => {
                e.stopPropagation()
                setViewer(null)
              }}
            >
              Schließen
            </button>
          </div>
          <div className="flex min-h-0 flex-1 items-center justify-center">
            <img src={viewer.src} alt={viewer.alt} className="max-h-full max-w-full object-contain" />
          </div>
        </div>
      ) : null}
    </div>
  )
}

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

  if (count <= 0) return null

  async function removePhoto(photoId: string) {
    if (!canManage || writeBlocked || busy) return
    setBusy(true)
    setErr('')
    try {
      await deleteTaskHintPhoto(taskId, photoId)
      const next = photos.filter((p) => p.id !== photoId)
      setPhotos(next)
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
                return (
                  <li
                    key={photo.id}
                    className="relative overflow-hidden rounded-xl border border-white/[0.08] bg-zinc-950"
                  >
                    {src ? (
                      <a href={src} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()}>
                        <img
                          src={src}
                          alt={photo.originalFilename || 'Hinweis-Foto'}
                          className="h-36 w-full object-cover"
                          loading="lazy"
                          decoding="async"
                        />
                      </a>
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
    </div>
  )
}

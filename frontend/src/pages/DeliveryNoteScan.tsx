import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  api,
  createDeliveryNote,
  deleteDeliveryNotePhoto,
  downloadExport,
  listDeliveryNotePhotos,
  resolveBackendPublicUrl,
  uploadDeliveryNotePhoto,
  type DeliveryNote,
  type ReportPhoto,
} from '../api/client'
import { InlineCameraModal } from '../components/InlineCameraModal'
import { BigButton, Card, PageTitle } from '../components/ui'
import { useWriteBlocked } from '../hooks/useWriteBlocked'
import { compressImageForUpload } from '../utils/compressImage'

type Project = { id: string; name: string; customer: string; status: string }

const MAX_PAGES = 8

export function DeliveryNoteScanPage() {
  const nav = useNavigate()
  const { writeBlocked } = useWriteBlocked()

  const [projects, setProjects] = useState<Project[]>([])
  const [projectId, setProjectId] = useState('')
  const today = useMemo(() => new Date().toISOString().slice(0, 10), [])
  const [date, setDate] = useState(today)
  const [note, setNote] = useState('')

  const [doc, setDoc] = useState<DeliveryNote | null>(null)
  const [photos, setPhotos] = useState<ReportPhoto[]>([])
  const [maxPhotos, setMaxPhotos] = useState(MAX_PAGES)

  const [createBusy, setCreateBusy] = useState(false)
  const [uploadBusy, setUploadBusy] = useState(false)
  const [officeBusy, setOfficeBusy] = useState(false)
  const [dlBusy, setDlBusy] = useState(false)
  const [err, setErr] = useState('')
  const [msg, setMsg] = useState('')
  const [sentOk, setSentOk] = useState(false)
  const [cameraOpen, setCameraOpen] = useState(false)
  const galleryRef = useRef<HTMLInputElement>(null)

  const selected = projects.find((p) => p.id === projectId)
  const atLimit = photos.length >= maxPhotos
  const canScan = Boolean(doc) && !writeBlocked && !uploadBusy && !atLimit

  useEffect(() => {
    api<{ projects: Project[] }>('/api/projects')
      .then((r) => {
        const aktiv = r.projects.filter((p) => ((p.status as string | undefined) || 'aktiv') === 'aktiv')
        setProjects(aktiv)
        const firstId = aktiv[0]?.id
        if (firstId) setProjectId(firstId)
        else setProjectId('')
      })
      .catch(() => setProjects([]))
  }, [])

  async function startScan() {
    if (writeBlocked || createBusy || !projectId || !selected) return
    setErr('')
    setMsg('')
    setSentOk(false)
    setCreateBusy(true)
    try {
      const created = await createDeliveryNote({
        projectId,
        projectName: selected.name,
        customerName: selected.customer || '',
        date,
        note: note.trim(),
      })
      setDoc(created)
      const listed = await listDeliveryNotePhotos(created.id)
      setPhotos(listed.photos)
      setMaxPhotos(listed.maxPhotos || MAX_PAGES)
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : 'Lieferschein konnte nicht angelegt werden.')
    } finally {
      setCreateBusy(false)
    }
  }

  async function processFiles(files: File[]) {
    if (!doc || writeBlocked || uploadBusy || !files.length) return
    setErr('')
    setMsg('')
    setSentOk(false)
    setUploadBusy(true)
    try {
      let count = photos.length
      for (let i = 0; i < files.length; i++) {
        if (count >= maxPhotos) break
        const prepared = await compressImageForUpload(files[i]!)
        const res = await uploadDeliveryNotePhoto(doc.id, prepared)
        setPhotos(res.photos)
        setMaxPhotos(res.maxPhotos)
        count = res.count
      }
      setMsg('Scan-Seite übernommen.')
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : 'Upload fehlgeschlagen.')
    } finally {
      setUploadBusy(false)
      if (galleryRef.current) galleryRef.current.value = ''
    }
  }

  async function removePhoto(photoId: string) {
    if (!doc || writeBlocked || uploadBusy) return
    setErr('')
    setSentOk(false)
    try {
      const res = await deleteDeliveryNotePhoto(doc.id, photoId)
      setPhotos((prev) => prev.filter((p) => p.id !== photoId))
      setMaxPhotos(res.maxPhotos)
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : 'Foto konnte nicht entfernt werden.')
    }
  }

  async function sendOffice() {
    if (!doc || writeBlocked || officeBusy) return
    if (!photos.length) {
      setErr('Bitte mindestens eine Seite scannen.')
      return
    }
    setErr('')
    setMsg('')
    setOfficeBusy(true)
    try {
      const res = await api<{ ok: boolean; simulated: boolean; message: string }>(
        `/api/delivery-notes/${encodeURIComponent(doc.id)}/send-office`,
        { method: 'POST' },
      )
      setMsg(res.message?.trim() || 'Lieferschein wurde ans Büro gesendet.')
      setSentOk(true)
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : 'Versand fehlgeschlagen.')
      setSentOk(false)
    } finally {
      setOfficeBusy(false)
    }
  }

  async function downloadPdf() {
    if (!doc || dlBusy) return
    setErr('')
    setDlBusy(true)
    try {
      await downloadExport(`/api/delivery-notes/${encodeURIComponent(doc.id)}/export/pdf`)
    } catch {
      setErr('PDF konnte nicht erstellt werden.')
    } finally {
      setDlBusy(false)
    }
  }

  function resetFlow() {
    setDoc(null)
    setPhotos([])
    setMaxPhotos(MAX_PAGES)
    setNote('')
    setDate(today)
    setErr('')
    setMsg('')
    setSentOk(false)
  }

  return (
    <div>
      <PageTitle
        title="Lieferschein scannen"
        subtitle="Baustelle wählen, Seiten fotografieren, PDF ans Büro senden."
      />

      {!doc ? (
        <Card className="space-y-4">
          {projects.length === 0 ? (
            <p className="text-sm text-zinc-400">
              Keine aktive Baustelle. Bitte zuerst unter Baustellen eine anlegen.
            </p>
          ) : (
            <>
              <label className="block">
                <span className="text-sm text-zinc-400">Baustelle</span>
                <select
                  className="mt-2 w-full rounded-xl border border-white/[0.1] bg-black/55 px-3 py-3 text-white outline-none focus:border-orange-500/55"
                  value={projectId}
                  onChange={(e) => setProjectId(e.target.value)}
                  disabled={createBusy || writeBlocked}
                >
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </label>

              <label className="block">
                <span className="text-sm text-zinc-400">Datum</span>
                <input
                  type="date"
                  className="mt-2 w-full rounded-xl border border-white/[0.1] bg-black/55 px-3 py-3 text-white outline-none focus:border-orange-500/55"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  disabled={createBusy || writeBlocked}
                />
              </label>

              <label className="block">
                <span className="text-sm text-zinc-400">Notiz (optional)</span>
                <textarea
                  className="mt-2 min-h-[88px] w-full rounded-xl border border-white/[0.1] bg-black/55 px-3 py-3 text-white outline-none focus:border-orange-500/55"
                  placeholder="z. B. Material, Lieferant, Besonderheit…"
                  value={note}
                  maxLength={500}
                  onChange={(e) => setNote(e.target.value)}
                  disabled={createBusy || writeBlocked}
                />
              </label>

              <BigButton
                type="button"
                disabled={!projectId || createBusy || writeBlocked}
                onClick={() => void startScan()}
              >
                {createBusy ? '…' : 'Weiter — Seiten scannen'}
              </BigButton>
            </>
          )}

          {err ? <p className="text-sm text-red-300">{err}</p> : null}

          <BigButton type="button" variant="secondary" onClick={() => nav('/')}>
            Zurück
          </BigButton>
        </Card>
      ) : (
        <Card className="space-y-4">
          <div className="rounded-xl border border-orange-500/20 bg-orange-500/[0.07] px-3 py-2.5 text-sm text-orange-100/90">
            <p className="font-medium">{doc.projectName}</p>
            <p className="mt-0.5 text-orange-200/75">
              {doc.date}
              {doc.customerName ? ` · ${doc.customerName}` : ''}
            </p>
            {doc.note ? <p className="mt-1 text-xs text-orange-200/65">{doc.note}</p> : null}
          </div>

          <div>
            <p className="text-sm text-zinc-400">
              Scan-Seiten ({photos.length}/{maxPhotos})
            </p>
            <p className="mt-1 text-xs text-zinc-500">
              Kamera oder Galerie — bis zu {maxPhotos} Seiten. Kein Extra-Scanner nötig.
            </p>

            {photos.length > 0 ? (
              <div className="mt-3 grid grid-cols-3 gap-2">
                {photos.map((p, idx) => {
                  const src = resolveBackendPublicUrl(p.url) ?? p.url ?? ''
                  return (
                    <div
                      key={p.id}
                      className="relative aspect-square overflow-hidden rounded-xl ring-1 ring-white/[0.1]"
                    >
                      {src ? (
                        <img src={src} alt={`Seite ${idx + 1}`} className="h-full w-full object-cover" />
                      ) : (
                        <div className="flex h-full items-center justify-center bg-zinc-800 text-xs text-zinc-400">
                          Seite {idx + 1}
                        </div>
                      )}
                      <button
                        type="button"
                        aria-label="Seite entfernen"
                        className="absolute right-1 top-1 flex h-7 w-7 items-center justify-center rounded-full bg-black/70 text-sm text-white"
                        onClick={() => void removePhoto(p.id)}
                        disabled={uploadBusy || writeBlocked}
                      >
                        ×
                      </button>
                    </div>
                  )
                })}
              </div>
            ) : null}

            {canScan ? (
              <div className="mt-3 flex flex-wrap gap-2">
                <BigButton
                  type="button"
                  variant="secondary"
                  className="min-h-11 flex-1 px-3 text-sm"
                  disabled={uploadBusy || writeBlocked}
                  onClick={() => setCameraOpen(true)}
                >
                  Foto aufnehmen
                </BigButton>
                <BigButton
                  type="button"
                  variant="secondary"
                  className="min-h-11 flex-1 px-3 text-sm"
                  disabled={uploadBusy || writeBlocked}
                  onClick={() => galleryRef.current?.click()}
                >
                  Aus Galerie
                </BigButton>
                <input
                  ref={galleryRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp,image/*"
                  className="sr-only"
                  multiple
                  onChange={(e) => {
                    const list = e.target.files
                    if (!list?.length) return
                    void processFiles(Array.from(list))
                  }}
                  disabled={uploadBusy || writeBlocked}
                />
              </div>
            ) : null}
            {uploadBusy ? <p className="mt-2 text-sm text-zinc-400">Wird hochgeladen…</p> : null}
          </div>

          {sentOk ? (
            <div className="rounded-xl border border-orange-500/35 bg-orange-500/[0.12] px-3 py-3 text-sm text-orange-100">
              <p className="font-semibold">Im Büro angekommen</p>
              <p className="mt-1 text-orange-200/85">{msg || 'Lieferschein wurde ans Büro gesendet.'}</p>
            </div>
          ) : msg ? (
            <p className="text-sm text-orange-300">{msg}</p>
          ) : null}
          {err ? <p className="text-sm text-red-300">{err}</p> : null}

          {sentOk ? (
            <>
              <BigButton type="button" onClick={resetFlow}>
                Noch einen Lieferschein scannen
              </BigButton>
              <BigButton type="button" variant="secondary" disabled={dlBusy} onClick={() => void downloadPdf()}>
                {dlBusy ? '…' : 'PDF laden'}
              </BigButton>
              <BigButton
                type="button"
                variant="secondary"
                disabled={!photos.length || officeBusy || writeBlocked}
                onClick={() => void sendOffice()}
              >
                {officeBusy ? 'Wird gesendet…' : 'Erneut ans Büro senden'}
              </BigButton>
            </>
          ) : (
            <>
              <BigButton
                type="button"
                disabled={!photos.length || officeBusy || writeBlocked}
                onClick={() => void sendOffice()}
              >
                {officeBusy ? 'Wird gesendet…' : 'Ans Büro senden'}
              </BigButton>
              <BigButton type="button" variant="secondary" disabled={dlBusy} onClick={() => void downloadPdf()}>
                {dlBusy ? '…' : 'PDF laden'}
              </BigButton>
              <BigButton type="button" variant="secondary" onClick={resetFlow}>
                Noch einen Lieferschein scannen
              </BigButton>
            </>
          )}

          <BigButton type="button" variant="secondary" onClick={() => nav('/')}>
            Zum Dashboard
          </BigButton>
        </Card>
      )}

      <InlineCameraModal
        open={cameraOpen}
        onClose={() => setCameraOpen(false)}
        onCapture={(file) => {
          setCameraOpen(false)
          void processFiles([file])
        }}
      />
    </div>
  )
}

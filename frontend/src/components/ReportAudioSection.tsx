import { useCallback, useEffect, useRef, useState } from 'react'
import { api, uploadReportAudio } from '../api/client'
import { useWriteBlocked } from '../hooks/useWriteBlocked'
import { BigButton, Card } from './ui'
import {
  browserSupportsMediaRecording,
  inferExtensionFromMime,
  pickMediaRecorderMimeType,
} from '../utils/mediaRecorderMime'

type PanelPhase = 'bereit' | 'recording' | 'stopped' | 'uploading' | 'upload_ok' | 'upload_fail'

const PHASE_LABEL: Record<PanelPhase, string> = {
  bereit: 'Bereit zur Aufnahme',
  recording: 'Aufnahme läuft',
  stopped: 'Aufnahme beendet',
  uploading: 'Wird übermittelt',
  upload_ok: 'Übernommen',
  upload_fail: 'Konnte nicht verarbeitet werden',
}

type Props = {
  reportDraftId: string
  projectId: string
  date: string
  strukturierungBusy?: boolean
  /** kleinere Steuerungsfläche (z. B. eingeklappt) */
  compact?: boolean
  onApplyTranscript?: (text: string) => void
}

export function ReportAudioSection({
  reportDraftId,
  projectId,
  date,
  strukturierungBusy,
  compact,
  onApplyTranscript,
}: Props) {
  const { writeBlocked } = useWriteBlocked()
  const chunksRef = useRef<BlobPart[]>([])
  const streamRef = useRef<MediaStream | null>(null)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const previewUrlRef = useRef<string | null>(null)
  const usedMimeRef = useRef<string>('')

  const [phase, setPhase] = useState<PanelPhase>('bereit')
  const [recordingBlob, setRecordingBlob] = useState<Blob | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [barError, setBarError] = useState('')
  const [uploadSuccessLine, setUploadSuccessLine] = useState('')
  const [supports] = useState(() => browserSupportsMediaRecording())
  const [uploadedAudioId, setUploadedAudioId] = useState<string | null>(null)
  const [transcribeBusy, setTranscribeBusy] = useState(false)

  const revokePreview = useCallback(() => {
    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current)
      previewUrlRef.current = null
    }
    setPreviewUrl(null)
  }, [])

  const stopStreamTracks = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
  }, [])

  const cleanupAfterDiscard = useCallback(() => {
    recorderRef.current = null
    chunksRef.current = []
    stopStreamTracks()
    revokePreview()
    setRecordingBlob(null)
    usedMimeRef.current = ''
  }, [revokePreview, stopStreamTracks])

  const prepareForNewRecording = useCallback(() => {
    cleanupAfterDiscard()
    setUploadSuccessLine('')
  }, [cleanupAfterDiscard])

  const teardownOnUnmount = useCallback(() => {
    const rec = recorderRef.current
    if (rec && rec.state !== 'inactive') {
      try {
        rec.stop()
      } catch {
        /* ignore */
      }
    }
    cleanupAfterDiscard()
    setPhase('bereit')
    setBarError('')
    setUploadSuccessLine('')
    setUploadedAudioId(null)
  }, [cleanupAfterDiscard])

  useEffect(() => () => teardownOnUnmount(), [teardownOnUnmount])

  const handleDiscard = () => {
    setBarError('')
    setUploadSuccessLine('')
    const rec = recorderRef.current
    if (rec && rec.state !== 'inactive') {
      recorderRef.current = null
      rec.ondataavailable = null
      rec.onerror = null
      rec.onstop = () => {
        cleanupAfterDiscard()
        setPhase('bereit')
      }
      try {
        rec.stop()
      } catch {
        cleanupAfterDiscard()
        setPhase('bereit')
      }
      return
    }
    cleanupAfterDiscard()
    setPhase('bereit')
  }

  const handleStart = async () => {
    setBarError('')
    if (!supports) return
    if (phase === 'recording' || phase === 'uploading') {
      setBarError(
        phase === 'uploading'
          ? 'Moment bitte — die Übermittlung läuft noch.'
          : 'Bitte zuerst Aufnahme stoppen oder verwerfen.',
      )
      return
    }
    prepareForNewRecording()
    setPhase('bereit')

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      const picked = pickMediaRecorderMimeType()
      const recorder =
        picked && MediaRecorder.isTypeSupported(picked)
          ? new MediaRecorder(stream, { mimeType: picked })
          : new MediaRecorder(stream)
      recorderRef.current = recorder
      usedMimeRef.current = recorder.mimeType || picked || ''

      recorder.ondataavailable = (ev) => {
        if (ev.data?.size > 0) chunksRef.current.push(ev.data)
      }

      recorder.onerror = () => {
        setBarError('Aufnahmefehler.')
        handleDiscard()
      }

      recorder.onstop = () => {
        stopStreamTracks()
        recorderRef.current = null
        const mime = usedMimeRef.current || recorder.mimeType || 'audio/webm'
        if (chunksRef.current.length === 0) {
          chunksRef.current = []
          revokePreview()
          setPhase('bereit')
          setBarError('Aufnahme enthält keine Daten — evtl. zu kurz?')
          return
        }
        const blob = new Blob(chunksRef.current, { type: mime || undefined })
        chunksRef.current = []
        setRecordingBlob(blob)
        revokePreview()
        const url = URL.createObjectURL(blob)
        previewUrlRef.current = url
        setPreviewUrl(url)
        setPhase('stopped')
      }

      recorder.start(120)
      setPhase('recording')
    } catch (e: unknown) {
      cleanupAfterDiscard()
      const name = e instanceof DOMException ? e.name : ''
      if (name === 'NotAllowedError' || name === 'SecurityError') {
        setBarError('Bitte Mikrofonzugriff erlauben.')
      } else if (name === 'NotFoundError') {
        setBarError('Kein Mikrofon gefunden.')
      } else if (name === 'NotReadableError') {
        setBarError('Mikrofon ist belegt oder nicht lesbar.')
      } else {
        setBarError('Aufnahme konnte nicht gestartet werden.')
      }
      setPhase('bereit')
    }
  }

  const handleStop = () => {
    const rec = recorderRef.current
    setBarError('')
    if (!rec || rec.state === 'inactive') return
    try {
      rec.stop()
    } catch {
      setBarError('Aufnahme konnte nicht gestoppt werden.')
    }
  }

  const handleUpload = async () => {
    if (!recordingBlob) return
    setBarError('')
    setUploadSuccessLine('')
    const mime = recordingBlob.type || usedMimeRef.current || 'audio/webm'
    const ext = inferExtensionFromMime(mime)
    const clientName = `aufname.${ext}`

    setPhase('uploading')
    try {
      const res = await uploadReportAudio(recordingBlob, clientName, { reportDraftId, projectId, date })
      setPhase('upload_ok')
      setUploadedAudioId(res.audioId)
      setUploadSuccessLine('Audio wurde übernommen. Als Nächstes können Sie die Sprache in Text umwandeln.')
    } catch (err) {
      setUploadedAudioId(null)
      setPhase('upload_fail')
      setBarError(err instanceof Error ? err.message : 'Übermittlung fehlgeschlagen')
    }
  }

  async function handleTranscribe() {
    if (!uploadedAudioId || !onApplyTranscript) return
    setBarError('')
    setTranscribeBusy(true)
    try {
      const data = await api<{ ok: boolean; transcript: string; audioId: string }>(
        `/api/audio/${encodeURIComponent(uploadedAudioId)}/transcribe`,
        { method: 'POST', body: '{}' },
      )
      const t = typeof data.transcript === 'string' ? data.transcript : ''
      onApplyTranscript(t)
      setUploadSuccessLine((line) =>
        line.includes('Text wurde eingefügt') ? line : `${line}\nText wurde eingefügt.`,
      )
    } catch (err) {
      setBarError(err instanceof Error ? err.message : 'Sprache konnte nicht verarbeitet werden')
    } finally {
      setTranscribeBusy(false)
    }
  }

  const uploadBlocked = strukturierungBusy || phase === 'uploading'

  const btnClass = compact ? 'min-h-11 rounded-xl py-2.5 text-sm' : ''

  return (
    <Card
      className={`space-y-4 border-transparent bg-black/35 shadow-none ring-1 ring-white/[0.08] ${compact ? 'px-5 py-[1rem]' : ''}`}>
      <div>
        <h3 className={`font-semibold text-white ${compact ? 'text-sm' : 'text-base'}`}>Zusätzliche Aufzeichnung</h3>
        <p className={`mt-1.5 leading-relaxed text-zinc-500 ${compact ? 'text-[0.8rem]' : 'text-[0.9rem]'}`}>
          Hier können Sie optional eine eigene Aufnahme speichern und den gesprochenen Inhalt später unten übernehmen.
        </p>
      </div>
      {!supports ? (
        <div className="rounded-2xl bg-amber-500/10 px-4 py-[0.75rem] text-[0.88rem] text-amber-200/92 ring-1 ring-amber-500/35">
          <span className="font-medium">Aufzeichnung wird in diesem Browser nicht unterstützt.</span>
        </div>
      ) : (
        <div className="rounded-2xl bg-white/[0.04] px-4 py-3 text-[0.88rem] ring-1 ring-white/[0.07]">
          <span className="text-zinc-500">Ablauf:&nbsp;</span>
          <span className="font-medium text-zinc-200">{PHASE_LABEL[phase]}</span>
        </div>
      )}

      {supports ? (
        <div className="grid grid-cols-1 gap-2">
          <BigButton
            type="button"
            variant="secondary"
            className={btnClass}
            disabled={writeBlocked || strukturierungBusy || phase === 'recording' || phase === 'uploading'}
            onClick={() => void handleStart()}
          >
            Aufnahme starten
          </BigButton>
          <BigButton
            type="button"
            variant="secondary"
            className={btnClass}
            disabled={writeBlocked || phase !== 'recording'}
            onClick={() => handleStop()}
          >
            Aufnahme stoppen
          </BigButton>
          <BigButton
            type="button"
            variant="secondary"
            className={btnClass}
            disabled={writeBlocked || phase === 'uploading' || (phase !== 'recording' && phase !== 'stopped')}
            onClick={() => handleDiscard()}
          >
            Aufnahme verwerfen
          </BigButton>
          <BigButton
            type="button"
            variant="secondary"
            className={btnClass}
            disabled={writeBlocked || phase !== 'stopped' || !recordingBlob || uploadBlocked}
            onClick={() => void handleUpload()}
          >
            Audio verarbeiten
          </BigButton>
          {uploadedAudioId && onApplyTranscript ? (
            <BigButton
              type="button"
              variant="secondary"
              className={btnClass}
              disabled={writeBlocked || strukturierungBusy || transcribeBusy || !uploadedAudioId}
              onClick={() => void handleTranscribe()}
            >
              {transcribeBusy ? 'Sprache wird verarbeitet …' : 'Sprache in Text übernehmen'}
            </BigButton>
          ) : null}
        </div>
      ) : null}

      {supports && previewUrl ? (
        <div className="rounded-[1rem] bg-black/50 p-[0.4rem] ring-1 ring-white/[0.08]">
          <audio className="w-full" controls src={previewUrl}>
            Aufnahme
          </audio>
        </div>
      ) : null}

      {barError ? (
        <p className="whitespace-pre-wrap text-sm text-red-400" role="alert">
          {barError}
        </p>
      ) : null}
      {uploadSuccessLine ? (
        <p className="whitespace-pre-line text-sm text-orange-300" role="status">
          {uploadSuccessLine}
        </p>
      ) : null}
    </Card>
  )
}

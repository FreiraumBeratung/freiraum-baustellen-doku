import { Check, Mic } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { api, polishProtocolText, type ProtocolMode } from '../api/client'
import { BigButton, Card, PageTitle } from '../components/ui'
import { useWriteBlocked } from '../hooks/useWriteBlocked'
import type { BrowserSpeechRecognition } from '../utils/speechRecognition'
import { getSpeechRecognition, speechRecognitionSupported } from '../utils/speechRecognition'

type Project = { id: string; name: string; customer: string; status: string }

export type ProtocolPreviewState = {
  mode: ProtocolMode
  projectId: string
  projectName: string
  customerName: string
  date: string
  participants: string
  exportFormat: string
  rawText: string
  polishedText?: string
}

export function ProtocolNewPage() {
  const nav = useNavigate()
  const location = useLocation()
  const mode = (location.state as { mode?: ProtocolMode } | null)?.mode ?? 'quick'
  const { writeBlocked } = useWriteBlocked()

  const [projects, setProjects] = useState<Project[]>([])
  const [projectId, setProjectId] = useState('')
  const today = useMemo(() => new Date().toISOString().slice(0, 10), [])
  const [date, setDate] = useState(today)
  const [participants, setParticipants] = useState('')
  const [exportFormat, setExportFormat] = useState('PDF')
  const [rawText, setRawText] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [voiceActive, setVoiceActive] = useState(false)
  const [voiceSavedFlash, setVoiceSavedFlash] = useState(false)
  const voiceRef = useRef<BrowserSpeechRecognition | null>(null)
  const voiceFeedbackTimerRef = useRef<number | null>(null)
  const voiceSupported = speechRecognitionSupported()

  useEffect(() => {
    if (!location.state) {
      nav('/protokoll', { replace: true })
    }
  }, [location.state, nav])

  useEffect(() => {
    api<{ projects: Project[] }>('/api/projects').then((r) => {
      const aktiv = r.projects.filter((p) => ((p.status as string | undefined) || 'aktiv') === 'aktiv')
      setProjects(aktiv)
      const firstId = aktiv[0]?.id
      if (firstId) setProjectId(firstId)
      else setProjectId('')
    })
    api<{ defaultExportFormat: string }>('/api/company-profile').then((p) => {
      if (p.defaultExportFormat === 'Word' || p.defaultExportFormat === 'PDF') {
        setExportFormat(p.defaultExportFormat)
      }
    })
  }, [])

  useEffect(() => {
    return () => {
      if (voiceFeedbackTimerRef.current) window.clearTimeout(voiceFeedbackTimerRef.current)
      try {
        voiceRef.current?.abort()
      } catch {
        /* ignore */
      }
      voiceRef.current = null
    }
  }, [])

  function flashVoiceSaved() {
    if (voiceFeedbackTimerRef.current) window.clearTimeout(voiceFeedbackTimerRef.current)
    setVoiceSavedFlash(true)
    voiceFeedbackTimerRef.current = window.setTimeout(() => {
      setVoiceSavedFlash(false)
      voiceFeedbackTimerRef.current = null
    }, 2000)
  }

  function stopVoice(opts?: { success?: boolean }) {
    try {
      voiceRef.current?.stop()
    } catch {
      /* ignore */
    }
    voiceRef.current = null
    setVoiceActive(false)
    if (opts?.success) flashVoiceSaved()
  }

  function toggleVoice() {
    setErr('')
    if (!voiceSupported) return
    if (voiceActive) {
      stopVoice({ success: true })
      return
    }
    const r = getSpeechRecognition()
    if (!r) {
      setErr('Spracheingabe konnte nicht gestartet werden.')
      return
    }
    r.lang = 'de-DE'
    r.continuous = true
    r.interimResults = false
    r.onresult = (e) => {
      let chunk = ''
      for (let i = e.resultIndex; i < e.results.length; i++) {
        chunk += e.results[i]![0]!.transcript
      }
      const t = chunk.trim()
      if (!t.length) return
      setRawText((prev) => (prev.trim() ? `${prev.trim()} ${t}` : t))
    }
    r.onerror = () => stopVoice()
    r.onend = () => {
      voiceRef.current = null
      setVoiceActive(false)
    }
    voiceRef.current = r
    try {
      r.start()
      setVoiceActive(true)
    } catch {
      voiceRef.current = null
      setVoiceActive(false)
      setErr('Spracheingabe konnte nicht gestartet werden.')
    }
  }

  const proj = projects.find((p) => p.id === projectId)
  const modeLabel = mode === 'signed' ? 'Protokoll mit Unterschrift' : 'Schnellnotiz'

  async function continueToPreview() {
    setErr('')
    stopVoice()
    if (!proj) {
      setErr('Bitte Baustelle wählen.')
      return
    }
    const text = rawText.trim()
    if (text.length < 3) {
      setErr('Bitte mindestens ein paar Worte eingeben oder sprechen.')
      return
    }
    setBusy(true)
    let polishedText = text
    try {
      const res = await polishProtocolText(text)
      polishedText = res.polishedText.trim() || text
    } catch {
      polishedText = text
    } finally {
      setBusy(false)
    }
    const state: ProtocolPreviewState = {
      mode,
      projectId: proj.id,
      projectName: proj.name,
      customerName: proj.customer || '',
      date,
      participants: participants.trim(),
      exportFormat,
      rawText: text,
      polishedText,
    }
    nav('/protokoll/vorschau', { state })
  }

  return (
    <div className="overflow-x-hidden pb-2">
      <PageTitle title="Protokoll" subtitle={modeLabel} />

      <div className="space-y-8">
        <Card className="space-y-5 border-transparent bg-black/35 px-[1.35rem] py-8 shadow-none ring-1 ring-white/[0.06] backdrop-blur-sm">
          <label className="block min-w-0">
            <span className="text-[0.875rem] text-zinc-500">Baustelle</span>
            <select
              className="mt-1.5 w-full min-w-0 rounded-2xl border border-white/[0.1] bg-black/55 px-3 py-2.5 text-white outline-none focus:border-orange-500/65 focus:ring-[2px] focus:ring-orange-500/35"
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              disabled={!projects.length}
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                  {p.customer ? ` (${p.customer})` : ''}
                </option>
              ))}
            </select>
            {!projects.length ? (
              <p className="mt-2 text-sm text-amber-400">
                Keine aktive Baustelle — unter „Baustellen“ Projekt auf <strong>aktiv</strong> setzen.
              </p>
            ) : null}
          </label>

          <label className="block">
            <span className="text-[0.875rem] text-zinc-500">Datum</span>
            <input
              type="date"
              className="mt-1.5 w-full min-w-0 rounded-2xl border border-white/[0.1] bg-black/55 px-3 py-2.5 text-white outline-none focus:border-orange-500/65 focus:ring-[2px] focus:ring-orange-500/35"
              value={date}
              onChange={(e) => setDate(e.target.value)}
            />
          </label>

          {mode === 'signed' ? (
            <label className="block">
              <span className="text-[0.875rem] text-zinc-500">Teilnehmer (optional)</span>
              <input
                type="text"
                className="mt-1.5 w-full min-w-0 rounded-2xl border border-white/[0.1] bg-black/55 px-3 py-2.5 text-white outline-none focus:border-orange-500/65 focus:ring-[2px] focus:ring-orange-500/35"
                value={participants}
                onChange={(e) => setParticipants(e.target.value)}
                placeholder="z. B. Bauherr, Architekt, Polier"
              />
            </label>
          ) : null}
        </Card>

        <Card className="relative overflow-hidden border-transparent bg-[linear-gradient(180deg,rgba(255,255,255,0.05),transparent_52%)] px-[1.15rem] py-6 shadow-none ring-1 ring-orange-400/14 backdrop-blur-sm">
          <div
            aria-hidden
            className="pointer-events-none absolute inset-x-1/4 top-[-35%] h-[62%] rounded-full bg-orange-500/[0.08] blur-[44px]"
          />
          <div className="relative space-y-5">
            <div>
              <p className="text-[0.68rem] font-medium tracking-[0.14em] text-orange-300/85">Aufnahme</p>
              <p className="mt-2 text-[0.86rem] leading-[1.5] text-zinc-500">Frei sprechen oder unten schreiben.</p>
            </div>

            {voiceSupported ? (
              <div className="flex flex-col items-center gap-3 py-0">
                <div className="rounded-[1.8rem] bg-black/35 p-[0.3rem] ring-1 ring-white/[0.07]">
                  <button
                    type="button"
                    disabled={writeBlocked || busy}
                    onClick={() => toggleVoice()}
                    className={`flex h-[5.5rem] w-[5.5rem] items-center justify-center rounded-full bg-gradient-to-br from-orange-400 to-orange-600 text-zinc-950 outline-none ring-2 ring-orange-400/45 ring-offset-2 ring-offset-zinc-950 transition hover:from-orange-300 hover:to-orange-500 disabled:opacity-35 focus-visible:ring-orange-400/70 ${voiceActive ? 'freiraum-mic-recording' : voiceSavedFlash ? '' : 'freiraum-mic-idle'}`}
                    aria-pressed={voiceActive}
                    aria-label={voiceActive ? 'Spracheingabe stoppen' : 'Spracheingabe starten'}
                  >
                    {voiceSavedFlash && !voiceActive ? (
                      <Check className="h-9 w-9" strokeWidth={2.5} aria-hidden />
                    ) : (
                      <Mic className="h-9 w-9" strokeWidth={2} aria-hidden />
                    )}
                  </button>
                </div>
                <p
                  className={`min-h-[1.9rem] text-center text-[0.95rem] font-medium tracking-tight ${voiceActive ? 'text-orange-400' : voiceSavedFlash ? 'text-orange-400/92' : 'text-zinc-500'}`}
                >
                  {voiceActive
                    ? 'Aufnahme läuft…'
                    : voiceSavedFlash
                      ? 'Aussprache übernommen'
                      : 'Tippen zum Sprechen'}
                </p>
              </div>
            ) : (
              <div className="rounded-2xl bg-amber-500/10 px-4 py-[0.875rem] text-center text-[0.9rem] text-amber-100/93 ring-1 ring-amber-400/38">
                Spracheingabe wird hier nicht unterstützt — bitte den Text eingeben.
              </div>
            )}

            <label className="block">
              <span className="text-[0.875rem] text-zinc-500">Protokolltext</span>
              <textarea
                className="mt-2 min-h-[11.5rem] w-full min-w-0 rounded-[1.15rem] border border-white/[0.09] bg-black/55 px-4 py-[0.875rem] text-base leading-relaxed text-white outline-none backdrop-blur-sm focus:border-orange-500/60 focus:ring-[1px] focus:ring-orange-500/55"
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                placeholder="Was wurde besprochen oder festgestellt?"
              />
            </label>
          </div>
        </Card>

        {err ? <p className="text-sm text-red-400">{err}</p> : null}
        <BigButton
          type="button"
          disabled={writeBlocked || busy || !projectId || rawText.trim().length < 3}
          onClick={() => void continueToPreview()}
        >
          {busy ? 'Wird geglättet…' : 'Weiter zur Vorschau'}
        </BigButton>
      </div>
    </div>
  )
}

import { Check, ChevronDown, ChevronUp, FileText, Layers, Mic } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { ReportAudioSection } from '../components/ReportAudioSection'
import { BigButton, Card, PageTitle } from '../components/ui'
import { useWriteBlocked } from '../hooks/useWriteBlocked'
import type { BrowserSpeechRecognition } from '../utils/speechRecognition'
import { getSpeechRecognition, speechRecognitionSupported } from '../utils/speechRecognition'

type Project = { id: string; name: string; customer: string; status: string }
type Employee = { id: string; name: string; active: boolean }

export type ReportPreviewState = {
  projectId: string
  projectName: string
  customerName: string
  date: string
  employees: string[]
  employeeIds: string[]
  startTime: string
  endTime: string
  breakMinutes: number
  exportFormat: string
  rawText: string
  structured: StructuredPayload
  /** zurück von /api/structure-report */
  structuredBy?: 'openai' | 'local'
  /** Folgebericht: Bericht wird dem laufenden Durchlauf der Baustelle zugeordnet */
  seriesMode?: boolean
  /** freie Besonderheiten/Notiz für diesen Tag (Folge- wie Einzelbericht) */
  notes?: string
}

export type StructuredPayload = {
  summary: string
  activities: string[]
  materials: string[]
  materialSuggestions: string[]
  machineSuggestions: string[]
  machineHours: string[]
  problems: string[]
  openItems: string[]
  customerTalk: string
  /** strukturierte Arbeitszeile vom Backend */
  workTime?: string
  /** Anzeige der Beteiligten (wie erkannt/weitergegeben) */
  participantsLine?: string
}

export function ReportNewPage() {
  const nav = useNavigate()
  const { writeBlocked } = useWriteBlocked()
  const [reportDraftId] = useState(() =>
    typeof crypto !== 'undefined' && 'randomUUID' in crypto ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`,
  )
  const [projects, setProjects] = useState<Project[]>([])
  const [employees, setEmployees] = useState<Employee[]>([])
  const [projectId, setProjectId] = useState('')

  const today = useMemo(() => new Date().toISOString().slice(0, 10), [])
  const [date, setDate] = useState(today)
  const [selectedEmp, setSelectedEmp] = useState<Record<string, boolean>>({})
  const [startTime, setStartTime] = useState('08:00')
  const [endTime, setEndTime] = useState('16:30')
  const [breakMinutes, setBreakMinutes] = useState(45)
  const [exportFormat, setExportFormat] = useState('PDF')
  const [rawText, setRawText] = useState('')
  const [notes, setNotes] = useState('')
  const [reportMode, setReportMode] = useState<'single' | 'series'>('single')
  const [showModeModal, setShowModeModal] = useState(true)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [voiceActive, setVoiceActive] = useState(false)
  const [voiceSavedFlash, setVoiceSavedFlash] = useState(false)
  const voiceRef = useRef<BrowserSpeechRecognition | null>(null)
  const voiceFeedbackTimerRef = useRef<number | null>(null)
  const voiceSupported = speechRecognitionSupported()
  const [extrasOpen, setExtrasOpen] = useState(false)

  useEffect(() => {
    api<{ projects: Project[] }>('/api/projects').then((r) => {
      const aktiv = r.projects.filter((p) => ((p.status as string | undefined) || 'aktiv') === 'aktiv')
      setProjects(aktiv)
      const firstId = aktiv[0]?.id
      if (firstId) setProjectId(firstId)
      else setProjectId('')
    })
    api<{ employees: Employee[] }>('/api/employees').then((r) => {
      const active = r.employees.filter((e) => e.active)
      setEmployees(active)
      const sel: Record<string, boolean> = {}
      active.forEach((e) => {
        sel[e.id] = true
      })
      setSelectedEmp(sel)
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
    r.onerror = () => {
      stopVoice()
    }
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

  async function structure() {
    setErr('')
    stopVoice()
    setBusy(true)
    try {
      const names = employees.filter((e) => selectedEmp[e.id]).map((e) => e.name)
      const ids = employees.filter((e) => selectedEmp[e.id]).map((e) => e.id)
      const r = await api<{
        projectName: string
        customerName: string
        date: string
        exportFormat: string
        structured: StructuredPayload & Record<string, unknown>
        structuredBy?: 'openai' | 'local'
      }>('/api/structure-report', {
        method: 'POST',
        body: JSON.stringify({
          projectId,
          projectName: proj?.name,
          customerName: proj?.customer,
          date,
          employeeNames: names,
          startTime,
          endTime,
          exportFormat,
          rawText,
        }),
      })
      const st = r.structured as StructuredPayload & {
        workTime?: string
        participants?: string[]
      }
      const structured: StructuredPayload = {
        summary: String(st.summary ?? ''),
        activities: Array.isArray(st.activities) ? st.activities : [],
        materials: Array.isArray(st.materials) ? st.materials : [],
        materialSuggestions: Array.isArray(st.materialSuggestions) ? st.materialSuggestions : [],
        machineSuggestions: Array.isArray(st.machineSuggestions) ? st.machineSuggestions : [],
        machineHours: Array.isArray(st.machineHours) ? st.machineHours : [],
        problems: Array.isArray(st.problems) ? st.problems : [],
        openItems: Array.isArray(st.openItems) ? st.openItems : [],
        customerTalk: String(st.customerTalk ?? ''),
        workTime: typeof st.workTime === 'string' ? st.workTime : undefined,
        participantsLine: Array.isArray(st.participants)
          ? st.participants.join(', ')
          : undefined,
      }
      const state: ReportPreviewState = {
        projectId,
        projectName: proj?.name || r.projectName,
        customerName: proj?.customer || r.customerName,
        date: r.date,
        employees: names,
        employeeIds: ids,
        startTime,
        endTime,
        breakMinutes,
        exportFormat: r.exportFormat,
        rawText,
        structured,
        structuredBy: r.structuredBy === 'openai' ? 'openai' : 'local',
        seriesMode: reportMode === 'series',
        notes: notes.trim(),
      }
      nav('/bericht/vorschau', { state })
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Strukturierung fehlgeschlagen.')
    } finally {
      setBusy(false)
    }
  }

  function toggleEmp(id: string) {
    setSelectedEmp((s) => ({ ...s, [id]: !s[id] }))
  }

  return (
    <div className="overflow-x-hidden pb-2">
      {showModeModal ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4 backdrop-blur-sm">
          <div className="w-full max-w-sm rounded-3xl border border-white/[0.1] bg-zinc-950 p-6 shadow-2xl ring-1 ring-white/[0.06]">
            <h2 className="text-center text-lg font-semibold text-white">Welche Art Bericht?</h2>
            <p className="mt-2 text-center text-sm leading-relaxed text-zinc-500">
              Folgeberichte werden zu einer laufenden Baustelle gesammelt — am Ende entsteht daraus ein
              Gesamtbericht.
            </p>
            <div className="mt-6 space-y-3">
              <button
                type="button"
                onClick={() => {
                  setReportMode('single')
                  setShowModeModal(false)
                }}
                className="flex w-full items-start gap-3 rounded-2xl border border-white/[0.1] bg-black/55 px-4 py-3.5 text-left ring-1 ring-transparent transition hover:border-orange-500/60 hover:ring-orange-500/30"
              >
                <FileText strokeWidth={2} className="mt-0.5 h-5 w-5 shrink-0 text-orange-400" aria-hidden />
                <span>
                  <span className="block font-medium text-white">Einzelbericht</span>
                  <span className="mt-0.5 block text-[0.8rem] leading-snug text-zinc-500">
                    Ein eigenständiger Tagesbericht (wie bisher).
                  </span>
                </span>
              </button>
              <button
                type="button"
                onClick={() => {
                  setReportMode('series')
                  setShowModeModal(false)
                }}
                className="flex w-full items-start gap-3 rounded-2xl border border-white/[0.1] bg-black/55 px-4 py-3.5 text-left ring-1 ring-transparent transition hover:border-orange-500/60 hover:ring-orange-500/30"
              >
                <Layers strokeWidth={2} className="mt-0.5 h-5 w-5 shrink-0 text-orange-400" aria-hidden />
                <span>
                  <span className="block font-medium text-white">Folgebericht</span>
                  <span className="mt-0.5 block text-[0.8rem] leading-snug text-zinc-500">
                    Zu einer laufenden Baustelle sammeln (Gesamtbericht am Ende).
                  </span>
                </span>
              </button>
            </div>
          </div>
        </div>
      ) : null}

      <PageTitle title="Tagesbericht" subtitle="Sprache und Notizen" />

      <div className="space-y-8">
        <Card className="space-y-5 border-transparent bg-black/35 px-[1.35rem] py-8 shadow-none ring-1 ring-white/[0.06] backdrop-blur-sm">
          <div className="flex items-center justify-between gap-3">
            <p className="text-[0.68rem] font-medium tracking-[0.14em] text-zinc-600">Projekt</p>
            <button
              type="button"
              onClick={() => setShowModeModal(true)}
              className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-[0.22rem] text-[0.7rem] font-semibold tracking-wide transition ${
                reportMode === 'series'
                  ? 'border border-orange-400/45 bg-orange-500/[0.1] text-orange-300/95'
                  : 'border border-white/[0.12] bg-black/40 text-zinc-400'
              }`}
            >
              {reportMode === 'series' ? (
                <Layers strokeWidth={2} className="h-3.5 w-3.5" aria-hidden />
              ) : (
                <FileText strokeWidth={2} className="h-3.5 w-3.5" aria-hidden />
              )}
              {reportMode === 'series' ? 'Folgebericht' : 'Einzelbericht'}
              <span className="text-[0.62rem] font-normal text-zinc-500">· ändern</span>
            </button>
          </div>

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
                Keine aktive Baustelle — unter „Baustellen“ Projekt auf <strong>aktiv</strong> setzen oder neu
                anlegen.
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

          <div className="grid grid-cols-2 gap-3">
            <label className="block">
              <span className="text-[0.875rem] text-zinc-500">Start</span>
              <input
                type="time"
                className="mt-1.5 w-full min-w-0 rounded-2xl border border-white/[0.1] bg-black/55 px-3 py-2.5 text-white outline-none focus:border-orange-500/65 focus:ring-[2px] focus:ring-orange-500/35"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
              />
            </label>
            <label className="block">
              <span className="text-[0.875rem] text-zinc-500">Ende</span>
              <input
                type="time"
                className="mt-1.5 w-full min-w-0 rounded-2xl border border-white/[0.1] bg-black/55 px-3 py-2.5 text-white outline-none focus:border-orange-500/65 focus:ring-[2px] focus:ring-orange-500/35"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
              />
            </label>
          </div>

          <label className="block">
            <span className="text-[0.875rem] text-zinc-500">Pause</span>
            <select
              className="mt-1.5 w-full min-w-0 rounded-2xl border border-white/[0.1] bg-black/55 px-3 py-2.5 text-white outline-none focus:border-orange-500/65 focus:ring-[2px] focus:ring-orange-500/35"
              value={breakMinutes}
              onChange={(e) => setBreakMinutes(Number(e.target.value))}
            >
              <option value={0}>Keine Pause</option>
              <option value={30}>30 Minuten</option>
              <option value={45}>45 Minuten</option>
              <option value={60}>60 Minuten</option>
              <option value={90}>90 Minuten</option>
            </select>
          </label>

          <label className="block">
            <span className="text-[0.875rem] text-zinc-500">Ausgabeformat</span>
            <select
              className="mt-1.5 w-full min-w-0 rounded-2xl border border-white/[0.1] bg-black/55 px-3 py-2.5 text-white outline-none focus:border-orange-500/65 focus:ring-[2px] focus:ring-orange-500/35"
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value)}
            >
              <option value="PDF">PDF</option>
              <option value="Word">Word</option>
            </select>
          </label>

          <div>
            <span className="text-[0.875rem] text-zinc-500">Mitarbeitende</span>
            <div className="mt-2 grid gap-2">
              {employees.map((e) => (
                <label
                  key={e.id}
                  className="flex min-w-0 cursor-pointer items-center gap-3 rounded-2xl border border-transparent bg-black/55 px-3 py-2.5 ring-1 ring-white/[0.08]"
                >
                  <input
                    type="checkbox"
                    checked={Boolean(selectedEmp[e.id])}
                    onChange={() => toggleEmp(e.id)}
                    className="h-5 w-5 accent-orange-500"
                  />
                  <span className="text-white">{e.name}</span>
                </label>
              ))}
              {employees.length === 0 ? <p className="text-sm text-zinc-500">Keine aktiven Mitarbeitenden.</p> : null}
            </div>
          </div>
        </Card>

        <Card className="relative overflow-hidden border-transparent bg-[linear-gradient(180deg,rgba(255,255,255,0.05),transparent_52%)] px-[1.15rem] py-9 shadow-none ring-1 ring-orange-400/14 backdrop-blur-sm">
          <div
            aria-hidden
            className="pointer-events-none absolute inset-x-1/4 top-[-35%] h-[62%] rounded-full bg-orange-500/[0.08] blur-[44px]"
          />
          <div className="relative space-y-7">
            <div>
              <p className="text-[0.68rem] font-medium tracking-[0.14em] text-orange-300/85">Aufnahme</p>
              <p className="mt-3 text-[0.88rem] leading-[1.55] text-zinc-500">Frei sprechen oder unten schreiben.</p>
            </div>

            {voiceSupported ? (
              <div className="flex flex-col items-center gap-5 py-2">
                <div className="rounded-[2.1rem] bg-black/35 p-[0.35rem] ring-1 ring-white/[0.07]">
                <button
                  type="button"
                  disabled={busy || writeBlocked}
                  onClick={() => toggleVoice()}
                  className={`flex h-[6.85rem] w-[6.85rem] items-center justify-center rounded-full bg-gradient-to-br from-orange-400 to-orange-600 text-zinc-950 outline-none ring-2 ring-orange-400/45 ring-offset-4 ring-offset-zinc-950 transition hover:from-orange-300 hover:to-orange-500 disabled:opacity-35 focus-visible:ring-orange-400/70 ${voiceActive ? 'freiraum-mic-recording' : voiceSavedFlash ? '' : 'freiraum-mic-idle'}`}
                  aria-pressed={voiceActive}
                  aria-label={voiceActive ? 'Spracheingabe stoppen' : 'Spracheingabe starten'}
                >
                  {voiceSavedFlash && !voiceActive ? (
                    <Check className="h-12 w-12" strokeWidth={2.5} aria-hidden />
                  ) : (
                    <Mic className="h-12 w-12" strokeWidth={2} aria-hidden />
                  )}
                </button>
                </div>
                <p className={`min-h-[2.875rem] text-center text-[0.95rem] font-medium tracking-tight ${voiceActive ? 'text-orange-400' : voiceSavedFlash ? 'text-orange-400/92' : 'text-zinc-500'}`}>
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
              <span className="text-[0.875rem] text-zinc-500">Notizen / Bericht</span>
              <textarea
                className="mt-2 min-h-[11.5rem] w-full min-w-0 rounded-[1.15rem] border border-white/[0.09] bg-black/55 px-4 py-[0.875rem] text-base leading-relaxed text-white outline-none backdrop-blur-sm focus:border-orange-500/60 focus:ring-[1px] focus:ring-orange-500/55"
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                placeholder="Notizen…"
              />
            </label>

            <label className="block">
              <span className="text-[0.875rem] text-zinc-500">Besonderheiten (optional)</span>
              <textarea
                className="mt-2 min-h-[5rem] w-full min-w-0 rounded-[1.15rem] border border-white/[0.09] bg-black/55 px-4 py-[0.875rem] text-base leading-relaxed text-white outline-none backdrop-blur-sm focus:border-orange-500/60 focus:ring-[1px] focus:ring-orange-500/55"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="z. B. Arbeit unterbrochen, weil der Maler kam …"
              />
              <span className="mt-1.5 block text-[0.72rem] leading-snug text-zinc-600">
                Freier Text — landet 1:1 im (Gesamt-)Bericht, ohne automatische Auswertung. Tipp: über das
                Mikrofon der Handy-Tastatur kann man hier diktieren.
              </span>
            </label>
          </div>
        </Card>

        <div className="rounded-3xl bg-black/45 ring-1 ring-white/[0.08]">
          <button
            type="button"
            aria-expanded={extrasOpen}
            onClick={() => setExtrasOpen((o) => !o)}
            className="flex w-full items-center justify-between gap-3 rounded-[1.125rem_1.125rem_0_0] px-4 py-[0.78rem] text-left text-[0.9rem] font-medium text-zinc-400 transition hover:bg-black/45"
          >
            <span>Erweiterter Aufzeichnungsbereich</span>
            {extrasOpen ? (
              <ChevronUp strokeWidth={2} className="h-5 w-5 shrink-0 text-zinc-500" aria-hidden />
            ) : (
              <ChevronDown strokeWidth={2} className="h-5 w-5 shrink-0 text-zinc-500" aria-hidden />
            )}
          </button>
          {extrasOpen ? (
            <div className="border-t border-white/[0.06] px-3 pb-[0.6rem] pt-1">
              <ReportAudioSection
                reportDraftId={reportDraftId}
                projectId={projectId}
                date={date}
                strukturierungBusy={busy}
                compact
                onApplyTranscript={(text) =>
                  setRawText((prev) => {
                    const p = prev.trim()
                    const t = text.trim()
                    if (!t) return prev
                    return p ? `${p}\n\n${t}` : t
                  })
                }
              />
            </div>
          ) : null}
        </div>

        {err ? <p className="text-sm text-red-400">{err}</p> : null}
        <BigButton type="button" disabled={busy || writeBlocked || !projectId || !rawText.trim()} onClick={() => structure()}>
          {busy ? '…' : 'Bericht strukturieren'}
        </BigButton>
      </div>
    </div>
  )
}

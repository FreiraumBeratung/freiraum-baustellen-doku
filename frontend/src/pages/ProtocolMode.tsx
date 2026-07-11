import { FileText, PenLine } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { PageTitle } from '../components/ui'
import type { ProtocolMode } from '../api/client'

export function ProtocolModePage() {
  const nav = useNavigate()

  function choose(mode: ProtocolMode) {
    nav('/protokoll/neu', { state: { mode } })
  }

  return (
    <div className="overflow-x-hidden pb-2">
      <PageTitle title="Protokoll" subtitle="Art wählen" />

      <div className="space-y-3">
        <button
          type="button"
          onClick={() => choose('quick')}
          className="flex w-full items-center gap-4 rounded-[1.35rem] border border-white/[0.1] bg-black/55 px-5 py-5 text-left ring-1 ring-white/[0.06] transition hover:border-orange-500/55 hover:ring-orange-500/25 active:scale-[0.99]"
        >
          <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-orange-500/15 text-orange-400 ring-1 ring-orange-400/25">
            <FileText strokeWidth={2} className="h-6 w-6" aria-hidden />
          </span>
          <span className="min-w-0">
            <span className="block text-base font-semibold text-white">Schnellnotiz</span>
            <span className="mt-1 block text-sm leading-snug text-zinc-500">
              Kurz festhalten, glätten, als PDF ans Büro — ohne Nummer und ohne Unterschrift.
            </span>
          </span>
        </button>

        <button
          type="button"
          onClick={() => choose('signed')}
          className="flex w-full items-center gap-4 rounded-[1.35rem] border border-white/[0.1] bg-black/55 px-5 py-5 text-left ring-1 ring-white/[0.06] transition hover:border-orange-500/55 hover:ring-orange-500/25 active:scale-[0.99]"
        >
          <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-orange-500/15 text-orange-400 ring-1 ring-orange-400/25">
            <PenLine strokeWidth={2} className="h-6 w-6" aria-hidden />
          </span>
          <span className="min-w-0">
            <span className="block text-base font-semibold text-white">Protokoll mit Unterschrift</span>
            <span className="mt-1 block text-sm leading-snug text-zinc-500">
              Begehungsprotokoll mit fortlaufender Nr. pro Baustelle — optional Kunde &amp; Mitarbeiter unterschreiben.
            </span>
          </span>
        </button>
      </div>
    </div>
  )
}

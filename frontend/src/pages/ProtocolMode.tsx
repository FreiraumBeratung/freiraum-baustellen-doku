import { FileText, Lightbulb, PenLine } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
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

      <div className="grid grid-cols-2 gap-2.5">
        <button
          type="button"
          onClick={() => choose('quick')}
          className="group flex aspect-square flex-col items-center justify-center gap-2.5 rounded-[1.25rem] border border-white/[0.07] bg-zinc-900/[0.5] px-2 text-center ring-1 ring-white/[0.04] transition hover:bg-white/[0.05] hover:ring-white/[0.1] active:scale-[0.98]"
        >
          <span className="flex h-12 w-12 items-center justify-center rounded-[1rem] bg-black/45 text-[1.45rem] ring-1 ring-white/[0.08]">
            <FileText strokeWidth={2} className="h-6 w-6 text-orange-400" aria-hidden />
          </span>
          <span className="text-[0.8rem] font-medium leading-tight tracking-tight text-zinc-300">Schnellnotiz</span>
        </button>

        <button
          type="button"
          onClick={() => choose('signed')}
          className="group flex aspect-square flex-col items-center justify-center gap-2.5 rounded-[1.25rem] border border-white/[0.07] bg-zinc-900/[0.5] px-2 text-center ring-1 ring-white/[0.04] transition hover:bg-white/[0.05] hover:ring-white/[0.1] active:scale-[0.98]"
        >
          <span className="flex h-12 w-12 items-center justify-center rounded-[1rem] bg-black/45 text-[1.45rem] ring-1 ring-white/[0.08]">
            <PenLine strokeWidth={2} className="h-6 w-6 text-orange-400" aria-hidden />
          </span>
          <span className="text-[0.72rem] font-medium leading-tight tracking-tight text-zinc-300">
            Protokoll mit Unterschrift
          </span>
        </button>

        <button
          type="button"
          onClick={() => choose('thoughts')}
          className="group col-span-2 flex min-h-[7.5rem] flex-col items-center justify-center gap-2.5 rounded-[1.25rem] border border-white/[0.07] bg-zinc-900/[0.5] px-3 py-4 text-center ring-1 ring-white/[0.04] transition hover:bg-white/[0.05] hover:ring-white/[0.1] active:scale-[0.98]"
        >
          <span className="flex h-12 w-12 items-center justify-center rounded-[1rem] bg-black/45 text-[1.45rem] ring-1 ring-white/[0.08]">
            <Lightbulb strokeWidth={2} className="h-6 w-6 text-orange-400" aria-hidden />
          </span>
          <span className="text-[0.8rem] font-medium leading-tight tracking-tight text-zinc-300">Gedankensammlung</span>
        </button>
      </div>

      <div className="mt-8">
        <Link
          to="/protokolle"
          className="flex w-full items-center justify-center rounded-2xl border border-white/[0.1] bg-black/40 px-4 py-3.5 text-sm font-semibold text-orange-300 ring-1 ring-white/[0.06] transition hover:bg-black/55 hover:ring-orange-500/25"
        >
          Gespeicherte Protokolle
        </Link>
      </div>
    </div>
  )
}

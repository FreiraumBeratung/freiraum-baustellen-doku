import { Card } from './ui'
import {
  addDaysIso,
  formatDayMonth,
  startOfWeekMonday,
  todayIsoLocal,
  weekDates,
  weekdayLong,
  weekdayShort,
  weekLabel,
} from '../utils/taskWeek'

type WeekTask = {
  projectName?: string
  assigneeNames?: string[]
}

type DayBlock = {
  date: string
  tasks: WeekTask[]
}

function whoWhere(tasks: WeekTask[]): string[] {
  const byProject = new Map<string, Set<string>>()
  for (const t of tasks) {
    const project = String(t.projectName || 'Baustelle').trim() || 'Baustelle'
    const names = byProject.get(project) ?? new Set<string>()
    for (const name of t.assigneeNames || []) {
      if (name.trim()) names.add(name.trim())
    }
    byProject.set(project, names)
  }
  return [...byProject.entries()].map(([project, names]) =>
    names.size ? `${project}: ${[...names].join(', ')}` : project,
  )
}

export function TasksWeekView({
  weekStart,
  selectedDay,
  days,
  onWeekChange,
  onSelectDay,
}: {
  weekStart: string
  selectedDay: string
  days: DayBlock[]
  onWeekChange: (nextStart: string) => void
  onSelectDay: (iso: string) => void
}) {
  const dates = weekDates(weekStart)
  const today = todayIsoLocal()
  const byDate = new Map(days.map((d) => [d.date, d.tasks]))

  return (
    <div className="mb-4 space-y-3">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => onWeekChange(addDaysIso(weekStart, -7))}
          className="rounded-2xl border border-white/[0.08] bg-black/40 px-3 py-2.5 text-sm text-zinc-300"
          aria-label="Vorherige Woche"
        >
          ‹
        </button>
        <p className="min-w-0 flex-1 text-center text-sm font-medium text-zinc-200">
          {weekLabel(weekStart)}
        </p>
        <button
          type="button"
          onClick={() => onWeekChange(addDaysIso(weekStart, 7))}
          className="rounded-2xl border border-white/[0.08] bg-black/40 px-3 py-2.5 text-sm text-zinc-300"
          aria-label="Nächste Woche"
        >
          ›
        </button>
      </div>

      <button
        type="button"
        onClick={() => {
          onWeekChange(startOfWeekMonday(today))
          onSelectDay(today)
        }}
        className="w-full rounded-2xl border border-orange-400/35 bg-orange-500/10 px-3 py-2 text-sm font-semibold text-orange-200"
      >
        Heute
      </button>

      <div className="grid grid-cols-7 gap-1">
        {dates.map((date) => {
          const count = byDate.get(date)?.length || 0
          const active = date === selectedDay
          const isToday = date === today
          return (
            <button
              key={date}
              type="button"
              onClick={() => onSelectDay(date)}
              className={`rounded-xl px-0.5 py-2 text-center ${
                active
                  ? 'border border-orange-400/45 bg-orange-500/[0.12] text-orange-200'
                  : 'border border-white/[0.08] bg-black/40 text-zinc-400'
              }`}
            >
              <span className="block text-[0.62rem] font-semibold">{weekdayShort(date)}</span>
              <span className={`block text-xs ${isToday && !active ? 'text-orange-300' : ''}`}>
                {formatDayMonth(date).slice(0, 2)}
              </span>
              <span className="mt-0.5 block text-[0.6rem] text-zinc-500">{count || '·'}</span>
            </button>
          )
        })}
      </div>

      <div className="space-y-2">
        {dates.map((date) => {
          const tasks = byDate.get(date) || []
          const lines = whoWhere(tasks)
          return (
            <button
              key={`agenda-${date}`}
              type="button"
              onClick={() => onSelectDay(date)}
              className={`w-full rounded-2xl border px-3 py-2.5 text-left ${
                date === selectedDay
                  ? 'border-orange-400/35 bg-orange-500/[0.08]'
                  : 'border-white/[0.06] bg-black/30'
              }`}
            >
              <p className="text-xs font-semibold text-zinc-200">
                {weekdayLong(date)} {formatDayMonth(date)}
                <span className="ml-2 font-normal text-zinc-500">
                  {tasks.length ? `${tasks.length} Aufgabe${tasks.length === 1 ? '' : 'n'}` : 'frei'}
                </span>
              </p>
              {lines.length ? (
                <p className="mt-1 text-xs leading-relaxed text-zinc-400">{lines.join(' · ')}</p>
              ) : (
                <p className="mt-1 text-xs text-zinc-600">Keine Einsätze</p>
              )}
            </button>
          )
        })}
      </div>

      <Card className="!py-3">
        <p className="text-xs font-medium uppercase tracking-wide text-orange-400/90">
          {weekdayLong(selectedDay)} {formatDayMonth(selectedDay)}
        </p>
        <p className="mt-1 text-xs text-zinc-500">Aufgaben dieses Tages — wer ist wo.</p>
      </Card>
    </div>
  )
}

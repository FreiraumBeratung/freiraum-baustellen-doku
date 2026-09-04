/** Web Speech API (Prototyp). `lib.dom` liefert Event-Typen, nicht die Recognition-Klasse. */

export type BrowserSpeechRecognition = {
  lang: string
  continuous: boolean
  interimResults: boolean
  start(): void
  stop(): void
  abort(): void
  onresult: ((ev: SpeechRecognitionEvent) => void) | null
  onerror: ((ev: SpeechRecognitionErrorEvent) => void) | null
  onend: ((ev: Event) => void) | null
}

type SpeechRecognitionConstructor = new () => BrowserSpeechRecognition

/** Android-Chrome beendet continuous oft nach Stille — iOS/WebKit nicht. */
export function isAndroidSpeechEngine(): boolean {
  if (typeof navigator === 'undefined') return false
  return /Android/i.test(navigator.userAgent || '')
}

const FATAL_SPEECH_ERRORS = new Set([
  'not-allowed',
  'service-not-allowed',
  'audio-capture',
  'language-not-supported',
  'network',
])

export type DictationSessionOptions = {
  /** true = Nutzer will noch aufnehmen (Button noch „aktiv“) */
  wantActive: () => boolean
  onTranscript: (chunk: string) => void
  /** Session wirklich zu Ende (UI aus) */
  onBecameInactive: () => void
}

/**
 * continuous=true + Android: bei onend sanft neu starten, solange wantActive.
 * iOS: unverändert — kein Restart, Fehler beenden die Session wie bisher.
 */
export function configureDictationSession(
  recognition: BrowserSpeechRecognition,
  opts: DictationSessionOptions,
): { dispose: () => void } {
  let restartTimer: number | null = null
  let startFails = 0
  const MAX_START_FAILS = 5

  const clearRestartTimer = () => {
    if (restartTimer != null) {
      window.clearTimeout(restartTimer)
      restartTimer = null
    }
  }

  const finishInactive = () => {
    clearRestartTimer()
    opts.onBecameInactive()
  }

  const tryRestartAndroid = () => {
    clearRestartTimer()
    if (!opts.wantActive() || !isAndroidSpeechEngine()) {
      finishInactive()
      return
    }
    if (startFails >= MAX_START_FAILS) {
      finishInactive()
      return
    }
    // Kurzer Delay: Chrome erlaubt start() oft nicht synchron in onend.
    restartTimer = window.setTimeout(() => {
      restartTimer = null
      if (!opts.wantActive()) {
        finishInactive()
        return
      }
      try {
        recognition.start()
      } catch {
        startFails += 1
        if (startFails >= MAX_START_FAILS || !opts.wantActive()) {
          finishInactive()
          return
        }
        restartTimer = window.setTimeout(() => {
          restartTimer = null
          if (!opts.wantActive()) {
            finishInactive()
            return
          }
          try {
            recognition.start()
          } catch {
            finishInactive()
          }
        }, 220)
      }
    }, 120)
  }

  recognition.lang = 'de-DE'
  recognition.continuous = true
  recognition.interimResults = false

  recognition.onresult = (e) => {
    startFails = 0
    let chunk = ''
    for (let i = e.resultIndex; i < e.results.length; i++) {
      chunk += e.results[i]![0]!.transcript
    }
    const t = chunk.trim()
    if (t) opts.onTranscript(t)
  }

  recognition.onerror = (ev) => {
    const code = String(ev.error || '')
    // Android: Pause → oft no-speech, danach onend → Restart (wenn wantActive).
    if (isAndroidSpeechEngine() && (code === 'no-speech' || code === 'aborted')) {
      return
    }
    // iOS und fatale Fehler: Session beenden (bisheriges Verhalten).
    if (!isAndroidSpeechEngine() || FATAL_SPEECH_ERRORS.has(code)) {
      finishInactive()
    }
  }

  recognition.onend = () => {
    if (!opts.wantActive()) {
      finishInactive()
      return
    }
    if (isAndroidSpeechEngine()) {
      tryRestartAndroid()
      return
    }
    // iOS: kein Auto-Restart — Engine hält continuous selbst.
    finishInactive()
  }

  return {
    dispose: () => {
      clearRestartTimer()
    },
  }
}

export function getSpeechRecognition(): BrowserSpeechRecognition | null {
  if (typeof window === 'undefined') return null
  const w = window as Window &
    Partial<{ SpeechRecognition: SpeechRecognitionConstructor; webkitSpeechRecognition: SpeechRecognitionConstructor }>
  const Ctor = w.SpeechRecognition ?? w.webkitSpeechRecognition
  if (!Ctor) return null
  try {
    return new Ctor()
  } catch {
    return null
  }
}

export function speechRecognitionSupported(): boolean {
  if (typeof window === 'undefined') return false
  const w = window as Window &
    Partial<{ SpeechRecognition: unknown; webkitSpeechRecognition: unknown }>
  return Boolean(w.SpeechRecognition ?? w.webkitSpeechRecognition)
}

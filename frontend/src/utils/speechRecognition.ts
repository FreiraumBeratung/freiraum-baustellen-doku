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

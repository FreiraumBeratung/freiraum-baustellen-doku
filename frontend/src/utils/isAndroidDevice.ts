/** Erkennt Android-Geraete (Handy/Tablet) in Browser und PWA. */
export function isAndroidDevice(): boolean {
  if (typeof navigator === 'undefined') return false
  return /Android/i.test(navigator.userAgent)
}

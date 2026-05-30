/** Erkennt iPhone/iPad (inkl. iPadOS mit Desktop-UA). */
export function isIosDevice(): boolean {
  if (typeof navigator === 'undefined') return false
  const ua = navigator.userAgent
  const classic = /iPad|iPhone|iPod/.test(ua)
  const ipadOs =
    navigator.platform === 'MacIntel' && typeof navigator.maxTouchPoints === 'number' && navigator.maxTouchPoints > 1
  return classic || ipadOs
}

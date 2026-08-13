/** Erkennt Tablets (Android-Tab / iPad) — Handys bewusst ausgeschlossen. */

export function isTabletDevice(): boolean {
  if (typeof navigator === 'undefined') return false
  const ua = navigator.userAgent || ''

  // iPad (klassisches UA)
  if (/iPad/i.test(ua)) return true

  // iPadOS mit Desktop-UA (kein iPhone)
  if (
    navigator.platform === 'MacIntel' &&
    typeof navigator.maxTouchPoints === 'number' &&
    navigator.maxTouchPoints > 1 &&
    !/iPhone|iPod/i.test(ua)
  ) {
    return true
  }

  // Explizite Tablet-Kennungen (u. a. Samsung Galaxy Tab SM-T / SM-X)
  if (/Tablet|\bSM-T\w|\bSM-X\w|Lenovo TB|Galaxy Tab/i.test(ua)) return true

  // Android ohne „Mobile“ im UA = typisches Tablet (Handys haben fast immer Mobile)
  if (/Android/i.test(ua) && !/Mobile/i.test(ua)) return true

  return false
}

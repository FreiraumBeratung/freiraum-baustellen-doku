import { isAndroidDevice } from './isAndroidDevice'
import { isIosDevice } from './isIosDevice'
import { isTabletDevice } from './isTabletDevice'

/** iOS/Android-PWA: voller Seitenwechsel nach Foto-Upload (wie manueller Reload). */
export function mobileHardRedirectAfterPhotoUpload(
  entityId: string,
  kind: 'report' | 'protocol' = 'report',
): void {
  const id = encodeURIComponent(entityId)
  const base =
    kind === 'protocol'
      ? `/protokolle/${id}?photos=1&uploaded=1`
      : `/berichte/${id}?photos=1&uploaded=1`

  // Tablet: replace + Cache-Bust (Samsung-Tabs hängen sonst oft am alten Screen).
  // Handy-Pfad unverändert: location.assign ohne Extra-Parameter.
  if (isTabletDevice()) {
    window.location.replace(`${base}&_r=${Date.now()}`)
    return
  }

  window.location.assign(base)
}

/** Mobil-PWA braucht harten Reload nach Kamera/Galerie (Black-Screen-Workaround). */
export function needsMobilePhotoHardRedirect(): boolean {
  // Tablets zusätzlich absichern (falls UA ohne „Mobile“ / Sonderfälle).
  // Handys: unverändert über iOS/Android.
  return isIosDevice() || isAndroidDevice() || isTabletDevice()
}

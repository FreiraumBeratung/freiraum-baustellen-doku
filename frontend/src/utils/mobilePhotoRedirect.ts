import { isAndroidDevice } from './isAndroidDevice'
import { isIosDevice } from './isIosDevice'

/** iOS/Android-PWA: voller Seitenwechsel nach Foto-Upload (wie manueller Reload). */
export function mobileHardRedirectAfterPhotoUpload(reportId: string): void {
  const id = encodeURIComponent(reportId)
  window.location.assign(`/berichte/${id}?photos=1&uploaded=1`)
}

/** Mobil-PWA braucht harten Reload nach Kamera/Galerie (Black-Screen-Workaround). */
export function needsMobilePhotoHardRedirect(): boolean {
  return isIosDevice() || isAndroidDevice()
}

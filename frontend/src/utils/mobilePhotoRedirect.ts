import { isAndroidDevice } from './isAndroidDevice'
import { isIosDevice } from './isIosDevice'

/** iOS/Android-PWA: voller Seitenwechsel nach Foto-Upload (wie manueller Reload). */
export function mobileHardRedirectAfterPhotoUpload(
  entityId: string,
  kind: 'report' | 'protocol' = 'report',
): void {
  const id = encodeURIComponent(entityId)
  if (kind === 'protocol') {
    window.location.assign(`/protokolle/${id}?photos=1&uploaded=1`)
    return
  }
  window.location.assign(`/berichte/${id}?photos=1&uploaded=1`)
}

/** Mobil-PWA braucht harten Reload nach Kamera/Galerie (Black-Screen-Workaround). */
export function needsMobilePhotoHardRedirect(): boolean {
  return isIosDevice() || isAndroidDevice()
}

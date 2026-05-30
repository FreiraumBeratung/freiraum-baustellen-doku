/** iOS-PWA: voller Seitenwechsel nach Foto-Upload (wie manueller Reload). */
export function iosHardRedirectAfterPhotoUpload(reportId: string): void {
  const id = encodeURIComponent(reportId)
  window.location.assign(`/berichte/${id}?photos=1&uploaded=1&signatures=1`)
}

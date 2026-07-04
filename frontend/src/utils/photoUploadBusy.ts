/** Steuert iOS/Android-PWA-Hacks waehrend Foto-Upload (Nav ohne backdrop-blur). */
export function setPhotoUploadBusy(active: boolean): void {
  if (active) {
    document.body.dataset.photoUploadBusy = '1'
    return
  }
  delete document.body.dataset.photoUploadBusy
}

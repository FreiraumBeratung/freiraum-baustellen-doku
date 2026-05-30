/** Erzwingt ein Neuzeichnen der PWA-Oberflaeche (iOS-Workaround nach Kamera/Galerie). */
export function forcePwaRepaint(): void {
  requestAnimationFrame(() => {
    document.body.style.setProperty('transform', 'translateZ(0)')
    const scrollY = window.scrollY
    window.scrollTo(0, scrollY + 1)
    window.scrollTo(0, scrollY)
    requestAnimationFrame(() => {
      document.body.style.removeProperty('transform')
    })
  })
}

/** Gibt dem Browser Zeit, ein Overlay zu rendern, bevor schwere Arbeit startet. */
export function yieldForPaint(delayMs = 180): Promise<void> {
  return new Promise((resolve) => {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        window.setTimeout(resolve, delayMs)
      })
    })
  })
}

/** Weckt die Seite nach Foto-Upload mehrfach (iOS-PWA Repaint nach Overlay-Ende). */
export async function wakePageAfterPhotoUpload(): Promise<void> {
  for (let i = 0; i < 4; i += 1) {
    forcePwaRepaint()
    window.dispatchEvent(new Event('resize'))
    await yieldForPaint(70)
  }
}

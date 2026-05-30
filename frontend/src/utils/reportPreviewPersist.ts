/** Kurzzeit-Persistenz fuer die Bericht-Vorschau (Kamera-Reload auf dem Handy). */

const STORAGE_KEY = 'freiraum_baustellen_preview_v1'

export type ReportPreviewPersist = {
  reportSyncKey: string
  savedReportId: string
}

export function loadReportPreviewPersist(): ReportPreviewPersist | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const data = JSON.parse(raw) as ReportPreviewPersist
    if (!data?.reportSyncKey || !data?.savedReportId) return null
    return data
  } catch {
    return null
  }
}

export function saveReportPreviewPersist(data: ReportPreviewPersist): void {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  } catch {
    // sessionStorage voll/blockiert — Upload darf trotzdem weiterlaufen.
  }
}

export function clearReportPreviewPersist(): void {
  try {
    sessionStorage.removeItem(STORAGE_KEY)
  } catch {
    // ignore
  }
}

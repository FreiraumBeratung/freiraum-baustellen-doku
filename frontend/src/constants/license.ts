export const LICENSE_SUSPENDED_MESSAGE =
  'Ihr Zugang ist pausiert. Bitte wenden Sie sich an Freiraum Unternehmensberatung.'

export const LICENSE_SUSPENDED_EVENT = 'freiraum-license-suspended'
export const LICENSE_REACTIVATED_EVENT = 'freiraum-license-reactivated'

export function isLicenseSuspendedDetail(detail: string | null | undefined): boolean {
  if (!detail) return false
  return detail.includes('Zugang ist pausiert')
}

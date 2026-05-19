/** Firmenprofil wie von GET /api/company-profile zurückgegeben */

export type CompanyProfileResponse = {
  companyName?: string
  contactPerson?: string
  officeEmail?: string
  phone?: string
  address?: string
  defaultExportFormat?: string
  defaultRecipientEmail?: string
  logoUrl?: string | null
}

const looseEmailOk = (s: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s)

/**
 * V1: „Vollständig“ wenn alle onboarding-relevanten Pflichtfelder gesetzt sind.
 * Logo bleibt optional.
 */
export function isCompanyProfileComplete(p: CompanyProfileResponse | null | undefined): boolean {
  if (!p) return false
  const office = (p.officeEmail ?? '').trim()
  return (
    (p.companyName ?? '').trim().length >= 1 &&
    (p.contactPerson ?? '').trim().length >= 1 &&
    looseEmailOk(office) &&
    (p.phone ?? '').trim().length >= 1 &&
    (p.address ?? '').trim().length >= 1 &&
    ['PDF', 'Word'].includes((p.defaultExportFormat ?? 'PDF').trim())
  )
}

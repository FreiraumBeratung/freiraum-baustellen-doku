/** Ort/Laterne unter der Baustelle — nur dieser eine Mandant (Backend-Allowlist identisch). */
export const SITE_SPOT_TENANT_IDS = new Set(['5431c9e2-2160-4441-ae92-b6a6840b3245'])
export const SITE_SPOT_MAX_LEN = 80

export function hasSiteSpotField(tenantId: string | null | undefined): boolean {
  return SITE_SPOT_TENANT_IDS.has(String(tenantId || '').trim())
}

export function formatBaustelleLabel(
  projectName: string | null | undefined,
  siteSpot?: string | null,
): string {
  const name = String(projectName || '').trim() || '—'
  const spot = String(siteSpot || '').trim()
  return spot ? `${name} · ${spot}` : name
}

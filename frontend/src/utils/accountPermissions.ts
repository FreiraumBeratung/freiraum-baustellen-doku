/** Rollen/Rechte — Owner sieht alles; Worker nur Basis + Haken. */

export type AccountRole = 'owner' | 'worker'

export type AppPermission =
  | 'report'
  | 'protocol'
  | 'projects'
  | 'reports_list'
  | 'time_accounts'
  | 'delivery_notes'
  | 'employees'
  | 'company_profile'
  | 'admin'

export const EXTRA_PERMISSION_OPTIONS: { key: AppPermission; label: string }[] = [
  { key: 'projects', label: 'Baustellen' },
  { key: 'reports_list', label: 'Berichte-Liste' },
  { key: 'time_accounts', label: 'Stundenkonto' },
  { key: 'delivery_notes', label: 'Lieferschein' },
]

const OWNER_ALL: AppPermission[] = [
  'report',
  'protocol',
  'projects',
  'reports_list',
  'time_accounts',
  'delivery_notes',
  'employees',
  'company_profile',
  'admin',
]

export function isOwnerRole(role: AccountRole | string | null | undefined): boolean {
  return role !== 'worker'
}

export function hasAppPermission(
  role: AccountRole | string | null | undefined,
  permissions: string[] | null | undefined,
  needed: AppPermission,
): boolean {
  if (isOwnerRole(role)) return true
  const set = new Set((permissions || []).map(String))
  // Basisrechte für Worker immer
  if (needed === 'report' || needed === 'protocol') return true
  return set.has(needed)
}

export function permissionsForOwner(): AppPermission[] {
  return [...OWNER_ALL]
}

/** Dashboard-Kachel → benötigtes Recht */
export function tilePermission(path: string): AppPermission | null {
  switch (path) {
    case '/bericht':
      return 'report'
    case '/protokoll':
      return 'protocol'
    case '/lieferschein':
      return 'delivery_notes'
    case '/berichte':
      return 'reports_list'
    case '/stunden':
      return 'time_accounts'
    case '/baustellen':
      return 'projects'
    case '/mitarbeiter':
      return 'employees'
    case '/profil':
      return 'company_profile'
    default:
      return null
  }
}

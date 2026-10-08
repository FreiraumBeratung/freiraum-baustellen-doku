/** Rollen/Rechte — Owner sieht alles; Worker nur Basis + Haken. */

export type AccountRole = 'owner' | 'worker'

export type AppPermission =
  | 'report'
  | 'protocol'
  | 'tasks'
  | 'leave'
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

/** Admin-Paket: alles an außer Lieferschein. Tagesbericht bleibt Kern (kein Haken). */
export const FIRM_MODULE_KEYS = [
  'tasks',
  'protocol',
  'reports_list',
  'time_accounts',
  'leave',
  'projects',
  'employees',
  'delivery_notes',
] as const

export type FirmModuleKey = (typeof FIRM_MODULE_KEYS)[number]

export type FirmModules = Record<FirmModuleKey, boolean>

export const FIRM_MODULE_OPTIONS: { key: FirmModuleKey; label: string }[] = [
  { key: 'tasks', label: 'To-do' },
  { key: 'protocol', label: 'Protokoll' },
  { key: 'reports_list', label: 'Berichte' },
  { key: 'time_accounts', label: 'Stundenkonto' },
  { key: 'leave', label: 'Urlaub' },
  { key: 'projects', label: 'Baustellen' },
  { key: 'employees', label: 'Mitarbeiter' },
  { key: 'delivery_notes', label: 'Lieferschein' },
]

const DEFAULT_OFF_FIRM_MODULES = new Set<FirmModuleKey>(['delivery_notes'])

export function normalizeFirmModules(raw: unknown): FirmModules {
  const src =
    raw && typeof raw === 'object' && !Array.isArray(raw)
      ? (raw as Record<string, unknown>)
      : {}
  const out = {} as FirmModules
  for (const key of FIRM_MODULE_KEYS) {
    out[key] = key in src ? Boolean(src[key]) : !DEFAULT_OFF_FIRM_MODULES.has(key)
  }
  return out
}

export function firmModuleAllows(
  needed: AppPermission,
  modules: FirmModules | null | undefined,
): boolean {
  if (!(FIRM_MODULE_KEYS as readonly string[]).includes(needed)) return true
  const m = normalizeFirmModules(modules)
  return m[needed as FirmModuleKey]
}

const OWNER_ALL: AppPermission[] = [
  'report',
  'protocol',
  'tasks',
  'leave',
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
  firmModules?: FirmModules | null,
): boolean {
  if (!firmModuleAllows(needed, firmModules)) return false
  if (isOwnerRole(role)) return true
  const set = new Set((permissions || []).map(String))
  // Basisrechte für Worker immer — sofern die Firma das Modul hat
  if (needed === 'report' || needed === 'protocol' || needed === 'tasks' || needed === 'leave') return true
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
    case '/aufgaben':
      return 'tasks'
    case '/protokoll':
      return 'protocol'
    case '/lieferschein':
      return 'delivery_notes'
    case '/berichte':
      return 'reports_list'
    case '/stunden':
      return 'time_accounts'
    case '/urlaub':
      return 'leave'
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

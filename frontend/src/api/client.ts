import {
  isLicenseSuspendedDetail,
  LICENSE_REACTIVATED_EVENT,
  LICENSE_SUSPENDED_EVENT,
} from '../constants/license'

const TOKEN_KEY = 'freiraum_baustellen_token'
const LICENSE_ACTIVE_KEY = 'freiraum_baustellen_license_active'
const IS_ADMIN_KEY = 'freiraum_baustellen_is_admin'

function viteApiBaseOverride(): string | undefined {
  const t = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim().replace(/\/$/, '')
  return t ? t : undefined
}

/** Ohne Override: im Browser relativ (`""`) → Requests auf `/api` und `/uploads` (Vite-Proxy zu localhost:30610). */
function resolveRuntimeApiBase(): string {
  const o = viteApiBaseOverride()
  if (o) return o
  if (typeof window === 'undefined') return 'http://localhost:30610'
  return ''
}

/** Basis-URL für `fetch`; leer im Browser ohne Override (`/api…` relativ zum Dev-Server). */
export const API_BASE_URL = resolveRuntimeApiBase()

/** Kurze Anzeige für Login-Debug und Fehlermeldungen. */
export function apiAuthDebugOriginLabel(): string {
  const o = viteApiBaseOverride()
  if (o) return o
  return 'relativ: /api, /uploads'
}

export function unreachableBackendDevMessage(): string {
  if (
    typeof window !== 'undefined' &&
    window.location.protocol === 'https:' &&
    API_BASE_URL.startsWith('http:')
  ) {
    return (
      'Backend nicht erreichbar: `VITE_API_BASE_URL` zeigt unter einer HTTPS-Seite auf HTTP ' +
      '(Mixed Content). Entfernen Sie das Override in der `.env`/Shell oder nutzen Sie HTTPS.'
    )
  }
  return 'Backend nicht erreichbar'
}

/** Öffentliche Backend-Pfade (`/uploads/…`): relativ ohne Override; absolute URLs bleiben unverändert. */
export function resolveBackendPublicUrl(pathOrUrl: string | null | undefined): string | null {
  if (!pathOrUrl?.trim()) return null
  const u = pathOrUrl.trim()
  if (/^https?:\/\//i.test(u)) return u
  const rel = u.startsWith('/') ? u : `/${u}`
  if (!API_BASE_URL) return rel
  return `${API_BASE_URL}${rel}`
}

function resolveApiUrl(path: string): string {
  const p = path.trim()
  if (/^https?:\/\//i.test(p)) return p
  const rel = p.startsWith('/') ? p : `/${p}`
  const base = API_BASE_URL
  if (!base) return rel
  return `${base}${rel}`
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(t: string) {
  localStorage.setItem(TOKEN_KEY, t)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
  clearLicenseActive()
  clearIsAdmin()
}

export function getIsAdmin(): boolean {
  return localStorage.getItem(IS_ADMIN_KEY) === '1'
}

export function setIsAdmin(isAdmin: boolean) {
  if (isAdmin) localStorage.setItem(IS_ADMIN_KEY, '1')
  else localStorage.removeItem(IS_ADMIN_KEY)
}

export function clearIsAdmin() {
  localStorage.removeItem(IS_ADMIN_KEY)
}

/** true = aktiv; fehlender Eintrag gilt als aktiv (bestehende Sessions). */
export function getLicenseActive(): boolean {
  const raw = localStorage.getItem(LICENSE_ACTIVE_KEY)
  if (raw === null) return true
  return raw !== '0' && raw !== 'false'
}

export function setLicenseActive(active: boolean) {
  localStorage.setItem(LICENSE_ACTIVE_KEY, active ? '1' : '0')
}

export function clearLicenseActive() {
  localStorage.removeItem(LICENSE_ACTIVE_KEY)
}

function notifyLicenseSuspendedIfNeeded(detail: string | null | undefined) {
  if (!isLicenseSuspendedDetail(detail)) return
  setLicenseActive(false)
  window.dispatchEvent(new Event(LICENSE_SUSPENDED_EVENT))
}

export function notifyLicenseReactivated() {
  if (!getLicenseActive()) {
    setLicenseActive(true)
    window.dispatchEvent(new Event(LICENSE_REACTIVATED_EVENT))
  }
}

export type AuthSessionResponse = {
  ok: boolean
  licenseActive: boolean
  isAdmin: boolean
}

/** Lizenzstatus vom Server holen (z. B. nach Admin-Reaktivierung). */
export async function fetchAuthSession(): Promise<AuthSessionResponse | null> {
  const token = getToken()
  if (!token) return null
  try {
    const data = await api<AuthSessionResponse>('/api/auth/session')
    const active = data.licenseActive !== false
    setLicenseActive(active)
    setIsAdmin(data.isAdmin === true)
    if (active) notifyLicenseReactivated()
    return data
  } catch {
    return null
  }
}

function parseApiDetail(err: ApiError, fallback: string): string {
  return typeof err.detail === 'string' ? err.detail : fallback
}

type ApiError = { detail?: string }

/** Für Login-/Register-Fetches: strukturierte Fehler (Netzwerk vs. HTTP, inkl. erreichbarem Backend). */
export type LoginFailureKind = 'network' | 'http'

export class LoginRequestError extends Error {
  declare readonly kind: LoginFailureKind
  declare readonly apiBase: string
  declare readonly status: number | undefined
  declare readonly reachable: boolean
  declare readonly backendMessage: string | undefined

  constructor(
    opts: {
      kind: LoginFailureKind
      apiBase: string
      backendMessage?: string
      status?: number
      reachable?: boolean
    },
    message?: string,
  ) {
    super(message ?? opts.backendMessage ?? 'Login fehlgeschlagen')
    this.name = 'LoginRequestError'
    this.kind = opts.kind
    this.apiBase = opts.apiBase
    this.backendMessage = opts.backendMessage
    this.status = opts.status
    this.reachable = Boolean(opts.reachable)
  }
}

export type AuthLoginResponse = {
  access_token: string
  licenseActive?: boolean
  isAdmin?: boolean
}

export type AdminUserRow = {
  id: string
  tenantId: string
  companyName: string
  entrepreneurName: string
  email: string
  createdAt: string
  licenseActive: boolean
  isAdmin: boolean
}

export type FeedbackCategory = 'Problem' | 'Verbesserung' | 'Lob'

export async function listAdminUsers(): Promise<{ users: AdminUserRow[] }> {
  return api<{ users: AdminUserRow[] }>('/api/admin/users')
}

export async function setAdminUserLicense(userId: string, licenseActive: boolean): Promise<{ ok: boolean; user: AdminUserRow }> {
  return api<{ ok: boolean; user: AdminUserRow }>(`/api/admin/users/${encodeURIComponent(userId)}/license`, {
    method: 'PATCH',
    body: JSON.stringify({ licenseActive }),
  })
}

export async function deleteAdminUser(userId: string): Promise<{ ok: boolean }> {
  return api<{ ok: boolean }>(`/api/admin/users/${encodeURIComponent(userId)}`, { method: 'DELETE' })
}

export async function sendFeedback(payload: {
  category: FeedbackCategory
  message: string
  page?: string
  appVersion?: string
}): Promise<{ ok: boolean; message: string }> {
  return api<{ ok: boolean; message: string }>('/api/feedback', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function postAuthLogin(email: string, password: string): Promise<AuthLoginResponse> {
  const dbg = apiAuthDebugOriginLabel()
  const url = resolveApiUrl('/api/auth/login')
  let res: Response
  try {
    res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
  } catch {
    throw new LoginRequestError(
      { kind: 'network', apiBase: dbg, reachable: false },
      unreachableBackendDevMessage(),
    )
  }

  if (res.ok) {
    const data = (await res.json()) as AuthLoginResponse
    setLicenseActive(data.licenseActive !== false)
    setIsAdmin(data.isAdmin === true)
    return data
  }

  const err = (await res.json().catch(() => ({}))) as ApiError
  const backendMessage =
    typeof err.detail === 'string' ? err.detail : res.statusText || undefined
  throw new LoginRequestError(
    {
      kind: 'http',
      apiBase: dbg,
      status: res.status,
      backendMessage,
      reachable: true,
    },
    backendMessage,
  )
}

/** Verbindungs-Check ohne Auth (DEV / Login-Hilfe). */
export async function getDebugPing(): Promise<{ ok: boolean; message?: string }> {
  const url = resolveApiUrl('/api/debug/ping')
  try {
    const res = await fetch(url, { method: 'GET' })
    if (!res.ok) return { ok: false }
    return (await res.json()) as { ok: boolean; message?: string }
  } catch {
    return { ok: false, message: unreachableBackendDevMessage() }
  }
}

export type AudioUploadResponse = {
  ok: boolean
  audioId: string
  filename: string
  message?: string
}

export async function uploadReportAudio(
  blob: Blob,
  uploadFilename: string,
  fields: { reportDraftId?: string; projectId?: string; date?: string },
): Promise<AudioUploadResponse> {
  const fd = new FormData()
  fd.append('file', blob, uploadFilename)
  const draft = fields.reportDraftId?.trim()
  const pid = fields.projectId?.trim()
  const d = fields.date?.trim()
  if (draft) fd.append('reportDraftId', draft)
  if (pid) fd.append('projectId', pid)
  if (d) fd.append('date', d)

  const url = resolveApiUrl('/api/audio/upload')
  const headers: Record<string, string> = {}
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`

  let res: Response
  try {
    res = await fetch(url, { method: 'POST', body: fd, headers })
  } catch {
    throw new Error(unreachableBackendDevMessage())
  }

  if (res.status === 401) {
    clearToken()
    window.location.assign('/login')
    throw new Error('Nicht angemeldet')
  }

  if (!res.ok) {
    const err = (await res.json().catch(() => ({}))) as ApiError
    const detail = parseApiDetail(err, res.statusText || 'Übermittlung fehlgeschlagen')
    if (res.status === 403) notifyLicenseSuspendedIfNeeded(detail)
    throw new Error(detail)
  }

  notifyLicenseReactivated()
  return res.json() as Promise<AudioUploadResponse>
}

export type ReportPhoto = {
  id: string
  filename: string
  originalFilename?: string | null
  contentType?: string | null
  sizeBytes?: number | null
  uploadedAt?: string | null
  url: string | null
}

export type ReportPhotosResponse = {
  photos: ReportPhoto[]
  count: number
  maxPhotos: number
}

export async function listReportPhotos(reportId: string): Promise<ReportPhotosResponse> {
  return api<ReportPhotosResponse>(`/api/reports/${encodeURIComponent(reportId)}/photos`)
}

export async function uploadReportPhoto(reportId: string, file: File): Promise<ReportPhotosResponse & { ok: boolean; photo: ReportPhoto }> {
  const fd = new FormData()
  fd.append('file', file, file.name || 'photo.jpg')

  const url = resolveApiUrl(`/api/reports/${encodeURIComponent(reportId)}/photos`)
  const headers: Record<string, string> = {}
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`

  let res: Response
  try {
    res = await fetch(url, { method: 'POST', body: fd, headers })
  } catch {
    throw new Error(unreachableBackendDevMessage())
  }

  if (res.status === 401) {
    clearToken()
    window.location.assign('/login')
    throw new Error('Nicht angemeldet')
  }

  if (!res.ok) {
    const err = (await res.json().catch(() => ({}))) as ApiError
    const detail = parseApiDetail(err, res.statusText || 'Foto konnte nicht hochgeladen werden')
    if (res.status === 403) notifyLicenseSuspendedIfNeeded(detail)
    throw new Error(detail)
  }

  notifyLicenseReactivated()
  return res.json() as Promise<ReportPhotosResponse & { ok: boolean; photo: ReportPhoto }>
}

export async function deleteReportPhoto(reportId: string, photoId: string): Promise<{ ok: boolean; count: number; maxPhotos: number }> {
  return api<{ ok: boolean; count: number; maxPhotos: number }>(
    `/api/reports/${encodeURIComponent(reportId)}/photos/${encodeURIComponent(photoId)}`,
    { method: 'DELETE' },
  )
}

export type SignatureRole = 'customer' | 'employee'

export type ReportSignature = {
  id: string
  role: SignatureRole
  filename: string
  contentType?: string | null
  sizeBytes?: number | null
  signedAt?: string | null
  signedByLabel?: string | null
  url: string | null
}

export type ReportSignaturesResponse = {
  signatures: {
    customer: ReportSignature | null
    employee: ReportSignature | null
  }
  count: number
}

export async function listReportSignatures(reportId: string): Promise<ReportSignaturesResponse> {
  return api<ReportSignaturesResponse>(`/api/reports/${encodeURIComponent(reportId)}/signatures`)
}

export async function uploadReportSignature(
  reportId: string,
  role: SignatureRole,
  file: File,
  signedByLabel?: string,
): Promise<ReportSignaturesResponse & { ok: boolean; signature: ReportSignature }> {
  const fd = new FormData()
  fd.append('file', file, file.name || 'signature.png')
  if (signedByLabel?.trim()) {
    fd.append('signedByLabel', signedByLabel.trim())
  }

  const url = resolveApiUrl(`/api/reports/${encodeURIComponent(reportId)}/signatures/${encodeURIComponent(role)}`)
  const headers: Record<string, string> = {}
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`

  let res: Response
  try {
    res = await fetch(url, { method: 'POST', body: fd, headers })
  } catch {
    throw new Error(unreachableBackendDevMessage())
  }

  if (res.status === 401) {
    clearToken()
    window.location.assign('/login')
    throw new Error('Nicht angemeldet')
  }

  if (!res.ok) {
    const err = (await res.json().catch(() => ({}))) as ApiError
    const detail = parseApiDetail(err, res.statusText || 'Unterschrift konnte nicht gespeichert werden')
    if (res.status === 403) notifyLicenseSuspendedIfNeeded(detail)
    throw new Error(detail)
  }

  return res.json() as Promise<ReportSignaturesResponse & { ok: boolean; signature: ReportSignature }>
}

export async function deleteReportSignature(
  reportId: string,
  role: SignatureRole,
): Promise<ReportSignaturesResponse & { ok: boolean }> {
  return api<ReportSignaturesResponse & { ok: boolean }>(
    `/api/reports/${encodeURIComponent(reportId)}/signatures/${encodeURIComponent(role)}`,
    { method: 'DELETE' },
  )
}

export type ProtocolMode = 'quick' | 'signed'

export type SiteProtocol = {
  id: string
  projectId: string
  projectName: string
  customerName: string
  date: string
  mode: ProtocolMode
  sequenceNumber: number | null
  participants: string
  rawText: string
  polishedText: string
  exportFormat: string
  signatures: ReportSignaturesResponse['signatures']
  createdAt: string
}

export async function polishProtocolText(rawText: string): Promise<{ polishedText: string; polishedBy: string }> {
  return api<{ polishedText: string; polishedBy: string }>('/api/protocols/polish-text', {
    method: 'POST',
    body: JSON.stringify({ rawText }),
  })
}

export async function createProtocol(body: {
  projectId: string
  projectName: string
  customerName: string
  date: string
  mode: ProtocolMode
  rawText: string
  polishedText: string
  participants: string
  exportFormat: string
}): Promise<SiteProtocol> {
  return api<SiteProtocol>('/api/protocols', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function listProtocolSignatures(protocolId: string): Promise<ReportSignaturesResponse> {
  return api<ReportSignaturesResponse>(`/api/protocols/${encodeURIComponent(protocolId)}/signatures`)
}

export async function uploadProtocolSignature(
  protocolId: string,
  role: SignatureRole,
  file: File,
  signedByLabel?: string,
): Promise<ReportSignaturesResponse & { ok: boolean; signature: ReportSignature }> {
  const fd = new FormData()
  fd.append('file', file, file.name || 'signature.png')
  if (signedByLabel?.trim()) {
    fd.append('signedByLabel', signedByLabel.trim())
  }

  const url = resolveApiUrl(
    `/api/protocols/${encodeURIComponent(protocolId)}/signatures/${encodeURIComponent(role)}`,
  )
  const headers: Record<string, string> = {}
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`

  let res: Response
  try {
    res = await fetch(url, { method: 'POST', body: fd, headers })
  } catch {
    throw new Error(unreachableBackendDevMessage())
  }

  if (res.status === 401) {
    clearToken()
    window.location.assign('/login')
    throw new Error('Nicht angemeldet')
  }

  if (!res.ok) {
    const err = (await res.json().catch(() => ({}))) as ApiError
    const detail = parseApiDetail(err, res.statusText || 'Unterschrift konnte nicht gespeichert werden')
    if (res.status === 403) notifyLicenseSuspendedIfNeeded(detail)
    throw new Error(detail)
  }

  return res.json() as Promise<ReportSignaturesResponse & { ok: boolean; signature: ReportSignature }>
}

export async function deleteProtocolSignature(
  protocolId: string,
  role: SignatureRole,
): Promise<ReportSignaturesResponse & { ok: boolean }> {
  return api<ReportSignaturesResponse & { ok: boolean }>(
    `/api/protocols/${encodeURIComponent(protocolId)}/signatures/${encodeURIComponent(role)}`,
    { method: 'DELETE' },
  )
}

export async function listProtocols(params?: {
  projectId?: string
  month?: string
}): Promise<{ protocols: SiteProtocol[] }> {
  const p = new URLSearchParams()
  if (params?.projectId) p.set('projectId', params.projectId)
  if (params?.month && params.month.length >= 7) p.set('month', `${params.month}-01`)
  const qs = p.toString()
  return api<{ protocols: SiteProtocol[] }>(`/api/protocols${qs ? `?${qs}` : ''}`)
}

export async function deleteProtocol(protocolId: string): Promise<{ ok: boolean }> {
  return api<{ ok: boolean }>(`/api/protocols/${encodeURIComponent(protocolId)}`, { method: 'DELETE' })
}

export async function listProtocolPhotos(protocolId: string): Promise<ReportPhotosResponse> {
  return api<ReportPhotosResponse>(`/api/protocols/${encodeURIComponent(protocolId)}/photos`)
}

export async function uploadProtocolPhoto(
  protocolId: string,
  file: File,
): Promise<ReportPhotosResponse & { ok: boolean; photo: ReportPhoto }> {
  const fd = new FormData()
  fd.append('file', file, file.name || 'photo.jpg')

  const url = resolveApiUrl(`/api/protocols/${encodeURIComponent(protocolId)}/photos`)
  const headers: Record<string, string> = {}
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`

  let res: Response
  try {
    res = await fetch(url, { method: 'POST', body: fd, headers })
  } catch {
    throw new Error(unreachableBackendDevMessage())
  }

  if (res.status === 401) {
    clearToken()
    window.location.assign('/login')
    throw new Error('Nicht angemeldet')
  }

  if (!res.ok) {
    const err = (await res.json().catch(() => ({}))) as ApiError
    const detail = parseApiDetail(err, res.statusText || 'Foto konnte nicht hochgeladen werden')
    if (res.status === 403) notifyLicenseSuspendedIfNeeded(detail)
    throw new Error(detail)
  }

  notifyLicenseReactivated()
  return res.json() as Promise<ReportPhotosResponse & { ok: boolean; photo: ReportPhoto }>
}

export async function deleteProtocolPhoto(
  protocolId: string,
  photoId: string,
): Promise<{ ok: boolean; count: number; maxPhotos: number }> {
  return api<{ ok: boolean; count: number; maxPhotos: number }>(
    `/api/protocols/${encodeURIComponent(protocolId)}/photos/${encodeURIComponent(photoId)}`,
    { method: 'DELETE' },
  )
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = resolveApiUrl(path)
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> | undefined),
  }
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }
  const token = getToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(url, { ...options, headers })

  if (res.status === 401) {
    const errBody = (await res.json().catch(() => ({}))) as ApiError
    const detail = typeof errBody.detail === 'string' ? errBody.detail : null
    const isLogin = path.includes('/api/auth/login')
    if (!isLogin) {
      clearToken()
      if (!path.includes('/auth/')) {
        window.location.assign('/login')
      }
      throw new Error(detail ?? 'Nicht angemeldet')
    }
    clearToken()
    throw new Error(detail ?? 'Ungültige Zugangsdaten')
  }

  if (!res.ok) {
    const err = (await res.json().catch(() => ({}))) as ApiError
    const detail = parseApiDetail(err, res.statusText)
    if (res.status === 403) notifyLicenseSuspendedIfNeeded(detail)
    throw new Error(detail)
  }

  if (res.status === 204) return undefined as T
  const method = (options.method || 'GET').toUpperCase()
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    notifyLicenseReactivated()
  }
  return res.json() as Promise<T>
}

/** PDF/DOCX Blob-Download — Pfad relativ (ohne Override) unter `/api/…`. */
export async function downloadExport(apiPath: string): Promise<void> {
  const url = resolveApiUrl(apiPath)
  const headers: Record<string, string> = {}
  const token = getToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(url, { headers })

  if (res.status === 401) {
    clearToken()
    if (!apiPath.includes('/auth/')) window.location.assign('/login')
    throw new Error('Nicht angemeldet')
  }

  if (!res.ok) {
    throw new Error('Export konnte nicht erstellt werden.')
  }

  let filename = 'download'
  const cd = res.headers.get('Content-Disposition')
  if (cd) {
    const mStar = cd.match(/filename\*=UTF-8''([^;\s]+)/i)
    if (mStar) {
      filename = decodeURIComponent(mStar[1])
    } else {
      const m = cd.match(/filename="([^"]+)"/i)
      if (m) filename = m[1]
    }
  } else if (apiPath.includes('/export/pdf')) {
    filename = apiPath.includes('/protocols/') ? 'protokoll.pdf' : 'tagesbericht.pdf'
  } else if (apiPath.includes('/export/word')) {
    filename = 'tagesbericht.docx'
  } else if (apiPath.includes('/export/csv')) {
    filename = 'stundenkonto.csv'
  } else if (apiPath.includes('/export/xlsx')) {
    filename = 'stundenkonto.xlsx'
  }

  const blob = await res.blob()
  const blobUrl = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = blobUrl
  a.download = filename
  a.rel = 'noopener'
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(blobUrl)
}

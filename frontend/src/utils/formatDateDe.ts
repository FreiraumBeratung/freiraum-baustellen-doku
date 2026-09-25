/** ISO YYYY-MM-DD oder DE TT.MM.JJJJ → TT.MM.JJJJ. Unbekanntes Format unverändert. */
export function formatDateDe(raw: string): string {
  const s = String(raw || '').trim()
  if (!s) return ''
  const iso = /^(\d{4})-(\d{2})-(\d{2})/.exec(s)
  if (iso) return `${iso[3]}.${iso[2]}.${iso[1]}`
  const de = /^(\d{1,2})\.(\d{1,2})\.(\d{4})/.exec(s)
  if (de) return `${de[1]!.padStart(2, '0')}.${de[2]!.padStart(2, '0')}.${de[3]}`
  return s
}

/** Wert für <input type="date"> — YYYY-MM-DD oder leer, nichts erfinden. */
export function toIsoDateInput(raw: string): string {
  const s = String(raw || '').trim()
  const iso = /^(\d{4})-(\d{2})-(\d{2})/.exec(s)
  if (iso) return `${iso[1]}-${iso[2]}-${iso[3]}`
  const de = /^(\d{1,2})\.(\d{1,2})\.(\d{4})/.exec(s)
  if (de) return `${de[3]}-${de[2]!.padStart(2, '0')}-${de[1]!.padStart(2, '0')}`
  return ''
}

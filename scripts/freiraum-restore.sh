#!/usr/bin/env bash
# Freiraum Baustellen-Doku — Wiederherstellung aus Backup-Archiv
#
# Nutzung:
#   ./scripts/freiraum-restore.sh /pfad/zu/freiraum-backup_2026-06-05_03-15-00.tar.gz
#
# Sicherheit:
# - Legt vor dem Restore ein Pre-Restore-Backup an (falls data/ oder uploads/ existieren)
# - .env wird NICHT aus dem Archiv wiederhergestellt (liegt nicht im Backup)

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Nutzung: $0 <backup.tar.gz> [BACKEND_DIR]" >&2
  exit 1
fi

ARCHIVE="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

BACKEND_DIR="${2:-${FREIRAUM_BACKEND_DIR:-${REPO_ROOT}/backend}}"

if [[ ! -f "${ARCHIVE}" ]]; then
  echo "FEHLER: Archiv nicht gefunden: ${ARCHIVE}" >&2
  exit 1
fi

if ! tar -tzf "${ARCHIVE}" data >/dev/null 2>&1; then
  echo "FEHLER: Archiv enthält kein data/ — falsches Backup?" >&2
  exit 1
fi

echo "=== Freiraum Restore ==="
echo "Archiv:  ${ARCHIVE}"
echo "Backend: ${BACKEND_DIR}"
echo ""
echo "ACHTUNG: data/ und uploads/ werden überschrieben."
read -r -p "Fortfahren? (ja/nein): " CONFIRM
if [[ "${CONFIRM}" != "ja" ]]; then
  echo "Abgebrochen."
  exit 0
fi

# Pre-Restore-Sicherung
if [[ -d "${BACKEND_DIR}/data" || -d "${BACKEND_DIR}/uploads" ]]; then
  PRE_DIR="${BACKEND_DIR}/../backups"
  mkdir -p "${PRE_DIR}"
  PRE_TS="$(date +%Y-%m-%d_%H-%M-%S)"
  PRE_ARCHIVE="${PRE_DIR}/pre-restore_${PRE_TS}.tar.gz"
  echo "Pre-Restore-Backup: ${PRE_ARCHIVE}"
  (
    cd "${BACKEND_DIR}"
    ITEMS=(data)
    [[ -d uploads ]] && ITEMS+=(uploads)
    tar -czf "${PRE_ARCHIVE}" "${ITEMS[@]}"
  )
fi

mkdir -p "${BACKEND_DIR}"

# Alte Ordner weg, dann entpacken
rm -rf "${BACKEND_DIR}/data"
rm -rf "${BACKEND_DIR}/uploads"

tar -xzf "${ARCHIVE}" -C "${BACKEND_DIR}"

echo ""
echo "Restore fertig."
echo "Nächste Schritte:"
echo "  1. Backend neu starten (systemctl restart … / uvicorn)"
echo "  2. Login testen, Bericht + Foto prüfen"
echo "  3. .env separat prüfen (liegt nicht im Backup)"

#!/usr/bin/env bash
# Freiraum Baustellen-Doku — Datensicherung (data/ + uploads/)
#
# Nutzung:
#   ./scripts/freiraum-backup.sh
#   FREIRAUM_BACKEND_DIR=/opt/freiraum/backend FREIRAUM_BACKUP_DIR=/var/backups/freiraum ./scripts/freiraum-backup.sh
#
# Cron-Beispiel (täglich 03:15):
#   15 3 * * * FREIRAUM_BACKEND_DIR=/opt/freiraum/backend FREIRAUM_BACKUP_DIR=/var/backups/freiraum /opt/freiraum/scripts/freiraum-backup.sh >> /var/log/freiraum-backup.log 2>&1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

BACKEND_DIR="${FREIRAUM_BACKEND_DIR:-${REPO_ROOT}/backend}"
BACKUP_DIR="${FREIRAUM_BACKUP_DIR:-${REPO_ROOT}/backups}"
RETENTION_DAYS="${FREIRAUM_BACKUP_RETENTION_DAYS:-7}"

DATA_DIR="${BACKEND_DIR}/data"
UPLOADS_DIR="${BACKEND_DIR}/uploads"

if [[ ! -d "${DATA_DIR}" ]]; then
  echo "FEHLER: data/ nicht gefunden: ${DATA_DIR}" >&2
  exit 1
fi

mkdir -p "${BACKUP_DIR}"

TIMESTAMP="$(date +%Y-%m-%d_%H-%M-%S)"
ARCHIVE="${BACKUP_DIR}/freiraum-backup_${TIMESTAMP}.tar.gz"
MANIFEST="${BACKUP_DIR}/freiraum-backup_${TIMESTAMP}.manifest.txt"

echo "=== Freiraum Backup ${TIMESTAMP} ==="
echo "Backend:  ${BACKEND_DIR}"
echo "Ziel:     ${ARCHIVE}"

# uploads/ kann bei frischer Installation fehlen — dann leeres Archiv- Mitglied
UPLOADS_ARG=()
if [[ -d "${UPLOADS_DIR}" ]]; then
  UPLOADS_ARG=("uploads")
else
  echo "Hinweis: uploads/ fehlt — nur data/ wird gesichert."
fi

(
  cd "${BACKEND_DIR}"
  tar -czf "${ARCHIVE}" data "${UPLOADS_ARG[@]:-}"
)

BYTES="$(wc -c < "${ARCHIVE}" | tr -d ' ')"
{
  echo "created_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "hostname=$(hostname 2>/dev/null || echo unknown)"
  echo "backend_dir=${BACKEND_DIR}"
  echo "archive=${ARCHIVE}"
  echo "bytes=${BYTES}"
  if command -v git >/dev/null 2>&1 && git -C "${REPO_ROOT}" rev-parse HEAD >/dev/null 2>&1; then
    echo "git_commit=$(git -C "${REPO_ROOT}" rev-parse --short HEAD)"
  fi
  echo "--- tar contents (top level) ---"
  tar -tzf "${ARCHIVE}" | head -n 40
} > "${MANIFEST}"

echo "Archiv:   ${BYTES} Bytes"
echo "Manifest: ${MANIFEST}"

# Alte Backups löschen (Dateiname-Prefix freiraum-backup_)
if [[ "${RETENTION_DAYS}" =~ ^[0-9]+$ ]] && [[ "${RETENTION_DAYS}" -gt 0 ]]; then
  DELETED="$(find "${BACKUP_DIR}" -maxdepth 1 -type f -name 'freiraum-backup_*.tar.gz' -mtime +"${RETENTION_DAYS}" -print -delete | wc -l | tr -d ' ')"
  find "${BACKUP_DIR}" -maxdepth 1 -type f -name 'freiraum-backup_*.manifest.txt' -mtime +"${RETENTION_DAYS}" -delete 2>/dev/null || true
  echo "Rotation: Backups älter als ${RETENTION_DAYS} Tage entfernt (${DELETED} Archiv/e)."
fi

echo "Backup fertig."

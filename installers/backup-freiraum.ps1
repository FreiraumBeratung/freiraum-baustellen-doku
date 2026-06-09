# Freiraum Baustellen-Doku — lokales Backup (Windows / Dev)
# Entspricht scripts/freiraum-backup.sh für Tests vor dem Hetzner-Deploy.

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$data = Join-Path $backend "data"
$uploads = Join-Path $backend "uploads"
$backupDir = if ($env:FREIRAUM_BACKUP_DIR) { $env:FREIRAUM_BACKUP_DIR } else { Join-Path $root "backups" }
$retentionDays = if ($env:FREIRAUM_BACKUP_RETENTION_DAYS) { [int]$env:FREIRAUM_BACKUP_RETENTION_DAYS } else { 7 }

if (-not (Test-Path $data)) {
  Write-Error "data/ nicht gefunden: $data"
}

New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$archive = Join-Path $backupDir "freiraum-backup_$timestamp.zip"

$items = @($data)
if (Test-Path $uploads) {
  $items += $uploads
}

Write-Host "=== Freiraum Backup $timestamp ==="
Write-Host "Backend: $backend"
Write-Host "Ziel:    $archive"

Compress-Archive -Path $items -DestinationPath $archive -Force

$bytes = (Get-Item $archive).Length
Write-Host "Archiv:  $bytes Bytes"

if ($retentionDays -gt 0) {
  $cutoff = (Get-Date).AddDays(-$retentionDays)
  Get-ChildItem $backupDir -Filter "freiraum-backup_*.zip" | Where-Object { $_.LastWriteTime -lt $cutoff } | ForEach-Object {
    Write-Host "Rotation: loesche $($_.Name)"
    Remove-Item $_.FullName -Force
  }
}

Write-Host "Backup fertig."

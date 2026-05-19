# Freiraum Baustellen-Doku — zwei Fenster (Backend 30610, Frontend 51710)
$root = Split-Path -Parent $PSScriptRoot
$shell = if (Get-Command pwsh -ErrorAction SilentlyContinue) { 'pwsh' } else { 'powershell' }
Start-Process $shell -ArgumentList @(
  '-NoExit', '-Command',
  "Set-Location '$root\backend'; py -3.13 -m uvicorn main:app --host 0.0.0.0 --port 30610 --reload"
)
Start-Process $shell -ArgumentList @(
  '-NoExit', '-Command',
  "Set-Location '$root\frontend'; npm run dev"
)

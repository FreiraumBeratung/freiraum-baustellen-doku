# Lokale HTTPS-Zertifikate (Dev — nicht commiten)

Keine Produkt-Zertifikate hier ablegen. Für **HTTPS-Frontend** unter Vite eigene **`mkcert`‑Dateien** erzeugen und hier speichern:

- `dev-cert.pem`
- `dev-key.pem`

Die Dateien liegen zusätzlich in der **Projekt‑`.gitignore`** (`*.pem`), damit nichts versehentlich ins Repository wandert.

## mkcert unter Windows

1. **mkcert installieren** (über winget oder die offizielle Releases-Seite von Filippo Valsorda):

   ```powershell
   winget install FiloSottile.mkcert
   ```

2. Lokale Certificate Authority im System registrieren:

   ```powershell
   mkcert -install
   ```

3. Zertifikat und Key erstellen (**LAN-IPv4 durch deine Adresse aus `ipconfig` ersetzen**, z. B. `192.168.178.55`):

   ```powershell
   cd Pfad-zum-repo\freiraum-baustellen-doku
   mkdir -Force .\config\certs
   cd .\config\certs
   mkcert -cert-file dev-cert.pem -key-file dev-key.pem localhost 127.0.0.1 ::1 192.168.178.55
   ```

Nach Schritt 3 sollten **`dev-cert.pem`** und **`dev-key.pem`** unter **`config\certs`** liegen. Anschließend im Frontend **`npm run dev:https`** starten (siehe Haupt‑`README.md`).

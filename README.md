# freiraum-baustellen-doku

Mobile-first **PWA** für Handwerksbetriebe: Tagesberichte per Text (später Sprache) erfassen, strukturieren, speichern und ans Büro vorbereiten — **ohne App Store**, **ohne Google Play**.

**Produktvision:** *Aus dem Kopf. Aus dem Sinn.*

---

## Zielgruppe

Handwerksbetriebe: Unternehmer, Vorarbeiter und Montagemitarbeiter, die Baustellen sauber dokumentieren wollen — ohne Zettelwirtschaft, ohne vergessene Berichte und ohne WhatsApp-Sprachnachrichten am Feierabend.

---

## Technikstack

| Bereich    | Technologie |
|-----------|-------------|
| Frontend  | React, Vite, TypeScript, Tailwind CSS, `vite-plugin-pwa` |
| Backend   | FastAPI (Python 3.13-kompatibel), Uvicorn |
| Daten V1  | Lokale JSON-Dateien unter `backend/data/` |
| Später    | SQLite / PostgreSQL (vorbereitet durch klare Datenzugriffsschicht im Backend) |

---

## Feste Ports

| Dienst   | Port   |
|----------|--------|
| Frontend | **51710** |
| Backend  | **30610** |

Keine anderen Ports verwenden — in `frontend/vite.config.ts` und beim Start von Uvicorn fest verdrahtet dokumentiert.

Für Zugriffe aus dem LAN siehe **„Handy-Test im WLAN“**; Frontend und Backend lauschen dort mit **`0.0.0.0`**, Ports unverändert.

---

## Installation

### Voraussetzungen

- **Node.js** (LTS) mit `npm`
- **Python 3.13** (oder 3.11+ mit angepasster Umgebung)

### Backend

```bash
cd backend
py -3.13 -m pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

---

## Start Backend

```bash
cd backend
py -3.13 -m uvicorn main:app --host 0.0.0.0 --port 30610 --reload
```

`--host 0.0.0.0` macht das API im LAN erreichbar (zusammen mit Frontend-WLAN-Test). Ohne Reload: gleicher Befehl ohne `--reload`.

Healthcheck vom Laptop: `GET http://127.0.0.1:30610/` oder `GET http://<deine-LAN-IP>:30610/` → JSON mit `status`, `service`, `port`.

### CORS (DEV / Handy)

Erlaubte Browser-Herkünfte sind u. a. **`http://localhost:51710`**, **`https://localhost:51710`**, **`127.0.0.1`** sowie **privates IPv4-LAN auf Port 51710** per Regex (z. B. **`http://`** oder **`https://192.168.x.x:51710`**), solange **`FREIRAUM_DEV_LAN_CORS` nicht auf `0` steht** (Standard: eingeschaltet — siehe `backend/.env.example`).

Zum Abschalten der LAN-Regex (nur noch localhost):

```powershell
set FREIRAUM_DEV_LAN_CORS=0
```

### OpenAI (optional — KI-Strukturierung)

Für **`POST /api/structure-report`** kann optional die **OpenAI API** den Rohtext strukturieren.

**So trägst du nur den Key ein:**

1. Falls du noch keine lokale Umgebungsdatei hast: **`backend/.env.example`** nach **`backend/.env`** kopieren (gleicher Ordner `backend/`).
2. Datei **`backend/.env`** öffnen.
3. Die Zeile **`OPENAI_API_KEY=`** suchen und **direkt hinter das `=`** deinen OpenAI-Schlüssel einfügen — **ohne** Anführungszeichen, alles in **einer Zeile**.  
   Beispiel: `OPENAI_API_KEY=sk-proj-...`  
   (`OPENAI_MODEL` kannst du so lassen wie in der Vorlage, z. B. `gpt-4o-mini`.)
4. Backend **neu starten**, damit `python-dotenv` den Key lädt.

**Wichtig:** Echten Schlüssel **nur** in **`backend/.env`** — diese Datei wird von Git ignoriert. **Nicht** in **`backend/.env.example`** einfügen (die Vorlage kann ins Repo).

**Ohne** ausgefülltes `OPENAI_API_KEY`: Strukturierung bleibt **lokal**; im Frontend steht **„Lokal strukturiert“**.

**Mit** gültigem Key: zuerst **KI**; bei Erfolg **„Strukturiert mit KI“** — bei API-/JSON-Fehlern automatisch **lokaler Fallback** (`structuredBy`: `local`).

---

## Start Frontend

| Skript | Bedeutung |
|--------|-----------|
| `npm run dev` | **HTTP** — Standard‑Entwicklung (wie bisher); `vite.config.ts` setzt bereits `host` und Port. |
| `npm run dev:lan` | **HTTP**, Host/Port explizit (**`0.0.0.0:51710`**) für Erreichbarkeit im WLAN. |
| `npm run dev:https` | **HTTPS‑Dev**, sofern `config/certs/dev-cert.pem` und `dev-key.pem` existieren (siehe **Handy‑Audio/Https** unten); sonst Fallback mit Warnung auf **HTTP**. |

```bash
cd frontend
npm run dev
```

Entspricht ebenfalls **`npm run dev -- --host 0.0.0.0 --port 51710`** (Konfig liegt in `vite.config.ts`).

WLAN / HTTPS:

```bash
cd frontend
npm run dev:lan
npm run dev:https
```

Die App läuft lokal unter **http://localhost:51710/** und im LAN unter **`http://<LAN-IP>:51710`** (siehe unten).

**API-URL im Browser (Dev):** Ohne gesetztes `VITE_API_BASE_URL` rufen alle `fetch`-Aufrufe die API **relativ zum Vite‑Dev‑Server** auf: **`/api/…`** und **`/uploads/…`**. Der Vite‑Proxy unter `frontend/vite.config.ts` leitet das intern weiter an **`http://localhost:30610`** (`changeOrigin`, `secure: false`). So bleiben **HTTPS‑Frontend (Port 51710)** und Browser dieselbe Ursprungs‑„Origin“ — **kein Mixed Content**.

Optional kann **`VITE_API_BASE_URL`** in einer `.env` / Shell gesetzt sein (z. B. anderes Setup); dann verwendet das Frontend diese Basis statt relativer Pfade — bei **HTTPS‑Seite und `http://…`‑Override** gilt weiterhin Mixed‑Content‑Sperren der Browser.

**Produktion:** Frontend und Backend hinter gemeinsamen sicheren Ursprung oder Reverse‑Proxy; die gebaute **`dist`**-Auslieferung enthält ohne weiteren Reverse‑Proxy keine automatische Backend‑Umleitung — dort `VITE_API_BASE_URL` passend zum Hosting setzen.

## HTTPS-Handy-Test mit Vite Proxy

1. Backend wie üblich starten (**`0.0.0.0:30610`**).
2. Zertifikate wie unter **„Handy-Audioaufnahme testen mit HTTPS“** anlegen (`mkcert`).
3. **`npm run dev:https`** im Ordner **`frontend`** — die App liegt unter **`https://<LAN-IP>:51710`**.
4. Im Browser gilt: alle API‑Requests gehen gegen **`https://<LAN-IP>:51710/api/…`** bzw. **`…/uploads/…`**; **nur der Vite‑Prozess auf dem Laptop** spricht dann per Proxy HTTP mit **`localhost:30610`**. Für das Handy gibt es keine direkten Aufrufe auf **`http://…:30610`** mehr → **Safari/iOS blockiert Mixed Content hier nicht.**

## Handy-Test im WLAN

So testest du die App auf dem Telefon gegen den Rechner im gleichen Netzwerk.

1. **IPv4-Adresse des Laptops ermitteln (PowerShell):**

   ```powershell
   ipconfig
   ```

   Unter dem aktiven Adapter (WLAN, oft „Wireless LAN adapter Wi-Fi“) die Zeile **IPv4 Address** notieren — z. B. `192.168.178.55`.

2. **Backend** (Terminal auf dem Laptop, Port **30610**):

   ```bash
   cd backend
   py -3.13 -m uvicorn main:app --host 0.0.0.0 --port 30610 --reload
   ```

3. **Frontend** (zweites Terminal, Port **51710**):

   ```bash
   cd frontend
   npm run dev
   ```

   (Host `0.0.0.0` kommt bereits aus `vite.config.ts`; alternativ **`npm run dev -- --host 0.0.0.0 --port 51710`**.)

4. **Browser auf dem Laptop:** weiter **`http://localhost:51710`**.

5. **Browser auf dem Handy:** **`http://<DEINE-IP>:51710`** — z. B. **`http://192.168.178.55:51710`**.

6. Falls die Verbindung scheitert: **Windows Defender Firewall** — Zugriff für **private Netzwerke** erlauben (Python/Node) oder Freigaben für TCP **51710** und **30610** prüfen.

### Audioaufnahme (PWA / Handy)

Für **Zugriff auf das Mikrofon** verlangen Browser oft eine **vertrauenswürdige/sichere Kontext-Umgebung** (üblich: **`https://`** oder ausnahmsweise **`localhost`**). Über **reines LAN-HTTP**, z. B. **`http://192.168.x.x:51710`**, kann **Safari/iOS** **MediaRecorder** und ähnliche APIs **unterbinden**.

- Für **echten Kundeneinsatz** soll die PWA **unter HTTPS‑Hosting** ausgeliefert werden.
- **`localhost`** gilt auf dem Laptop oft weiter als vertrauenswürdig; **WLAN‑IP ohne TLS** häufig nicht — das ist nicht mit „App-Hacks“, sondern mit **Browser‑Sicherheit** zu klären.

### Handy-Audioaufnahme testen mit HTTPS

Mit dem optionalen **HTTPS‑Dev‑Modus** (Vite) kannst du z. B. auf dem iPhone **`https://<LAN-IP>:51710`** erreichbare Seiten testen, damit oft **„Secure Context“** möglich ist.

1. **`mkcert`** installieren und lokale CA anlegen (**PowerShell**):

   ```powershell
   winget install FiloSottile.mkcert
   mkcert -install
   ```

2. Zertifikat und Schlüssel **ohne Produkt‑Dateien aus dem Repo** erzeugen (LAN‑IP durch deine Adresse aus `ipconfig` ersetzen, z. B. `192.168.178.55`):

   ```powershell
   cd Pfad-zum-repo\freiraum-baustellen-doku
   mkdir -Force .\config\certs | Out-Null
   cd .\config\certs
   mkcert -cert-file dev-cert.pem -key-file dev-key.pem localhost 127.0.0.1 ::1 192.168.178.55
   ```

   Die beiden Dateien liegen danach in **`config/certs/`**. (Details: **`config/certs/README.md`**. Sie sind durch **`.gitignore`** von Git ausgeschlossen.)

3. **Frontend starten**:

   ```bash
   cd frontend
   npm run dev:https
   ```

   **Ohne Zertifikate** startet das Skript ebenfalls (**HTTP**) und schreibt eine **Warnung** ins Terminal.

**Hinweise**

- **`npm run dev`** bleibt **HTTP‑Standard** ohne Zertifikat‑Zwänge — relativ **`/api`** funktioniert gleichermaßen über den Proxy.
- **Backend** weiterhin **`http://localhost:30610`** (von Vite‑Proxy erreicht).
- Mixed Content entfällt im üblichen Dev‑Pfad ohne `VITE_API_BASE_URL`-Override (relativ zu `/api` und `/uploads`).
- Zum Schnellcheck dienen im **Profil** die **„Kontext-Diagnose“**-Felder (**Secure Context**, **MediaDevices**, **MediaRecorder**, **SpeechRecognition**).

---

## PWA-Hinweis

- **Dev:** Service Worker und Caching sind produktionsnah; volle PWA-Features sind nach `npm run build` und `npm run preview` am ehesten spürbar.
- **Install:** Am Desktop oder Mobilgerät „Zum Startbildschirm hinzufügen“ / Installation über den Browser (Chrome, Edge, Safari iOS).
- **Manifest:** App-Name *Freiraum Baustellen-Doku*, Kurzname *Baustellen-Doku*, Theme `#f97316`, Hintergrund `#09090b`.

---

## V1-Funktionen

- Lokale Registrierung / Login (`users.json`)
- Firmenprofil inkl. Logoupload (`company_profile.json`, Dateien in `backend/uploads/logos/`)
- Mitarbeiterverwaltung (`employees.json`)
- Baustellen/Projekte (`projects.json`)
- Tagesbericht erfassen → **regelbasierte Strukturierung** (`POST /api/structure-report`)
- Bericht speichern & listen & Detail (`reports.json`)
- Dunkles UI, große Buttons, **Bottom Navigation** (Home, Bericht, Berichte, Baustellen, Profil)

---

## V1.1-Roadmap (Auszug)

Siehe **`docs/ROADMAP.md`**: Speech-to-Text, PDF/Word-Export, E-Mail-Versand, Fotodokumentation, Offline.

---

## Hinweise für späteren Produktivbetrieb

- **Passwörter:** In V1 Klartext im Code markiert — vor Produktivbetrieb **Passwort-Hashing** (z. B. bcrypt/argon2) und sichere Session/Tokens einführen.
- **Datenhaltung:** JSON ist nur für lokale V1-Demos gedacht; für Mehrbenutzer und Backup **Datenbank** (SQLite/Postgres) und Backups planen.
- **HTTPS:** PWA und APIs im öffentlichen Netz nur mit TLS betreiben.
- **Uploads:** Größenlimits und Virus-Scan erwägen.

---

## Projektstruktur (Kurz)

```
/backend          FastAPI, data/, uploads/
/frontend         Vite React App
/assets           optionale Marken-Assets
/config           Port-Dokumentation
/docs             ROADMAP etc.
/installers       Hilfsskripte zum Starten
```

---

## Lizenz / Nutzung

Internes Freiraum-Projekt; Standalone, ohne Kopplung an andere Repositories, soweit nicht anders vereinbart.

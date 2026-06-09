# Backup — Freiraum Baustellen-Doku

Sichert alle Mandanten-Daten und Uploads vor Datenverlust auf dem Server.

## Was wird gesichert?

| Pfad | Inhalt |
|------|--------|
| `backend/data/` | User, Mandanten-JSON, Mail-Config, Verschlüsselungsschlüssel |
| `backend/uploads/` | Logos, Fotos, Signaturen, Audio pro Mandant |

**Nicht** im Archiv: `backend/.env` (separat sichern, z. B. Passwort-Manager oder verschlüsselte Kopie).

---

## Welle 1 — Skript lokal testen (Windows)

```powershell
cd C:\Users\denis\freiraum-baustellen-doku
.\installers\backup-freiraum.ps1
```

Ergebnis: `backups/freiraum-backup_<datum>.zip`

---

## Welle 2 — Hetzner einrichten

### 1. Skripte auf den Server

Nach `git pull` liegen die Skripte unter `scripts/`. Ausführbar machen:

```bash
chmod +x scripts/freiraum-backup.sh scripts/freiraum-restore.sh
```

`FREIRAUM_BACKEND_DIR` setzen, wenn das Backend **nicht** im Repo-Root liegt, z. B.:

```bash
export FREIRAUM_BACKEND_DIR=/opt/freiraum/backend
export FREIRAUM_BACKUP_DIR=/var/backups/freiraum
```

### 2. Erstes manuelles Backup

```bash
sudo mkdir -p /var/backups/freiraum
FREIRAUM_BACKEND_DIR=/pfad/zum/backend FREIRAUM_BACKUP_DIR=/var/backups/freiraum ./scripts/freiraum-backup.sh
```

### 3. Restore einmal testen (Staging oder Testordner)

```bash
FREIRAUM_BACKEND_DIR=/tmp/freiraum-restore-test ./scripts/freiraum-restore.sh /var/backups/freiraum/freiraum-backup_....tar.gz /tmp/freiraum-restore-test
```

Nur wenn der Test ok ist → Cron aktivieren.

### 4. Cron (täglich 03:15)

```bash
sudo crontab -e
```

Zeile (Pfade anpassen):

```
15 3 * * * FREIRAUM_BACKEND_DIR=/opt/freiraum/backend FREIRAUM_BACKUP_DIR=/var/backups/freiraum /opt/freiraum/scripts/freiraum-backup.sh >> /var/log/freiraum-backup.log 2>&1
```

Rotation: Standard **7 Tage** (`FREIRAUM_BACKUP_RETENTION_DAYS`).

### 5. Off-Site (empfohlen vor Pilot-Start)

Backups **zusätzlich** vom Server kopieren:

- Hetzner Storage Box (`rsync` / `scp`)
- oder wöchentlich per `scp` auf deinen PC

Ein Backup nur auf derselben Festplatte schützt nicht vor Totalausfall des Servers.

---

## Vor jedem Deploy

Kurz manuell sichern, bevor du auf Hetzner `git pull` + Backend-Restart machst:

```bash
./scripts/freiraum-backup.sh
```

---

## Restore (Notfall)

1. Backend stoppen
2. `./scripts/freiraum-restore.sh <neuestes-backup.tar.gz>`
3. Backend starten
4. Login, Bericht, Foto prüfen
5. `.env` prüfen (falls Mail/Admin nicht geht)

Das Skript legt automatisch ein **Pre-Restore-Backup** an, falls du dich vertust.

---

## Checkliste vor ersten Pilot-Testern

- [ ] Mindestens ein manuelles Backup auf Hetzner
- [ ] Restore einmal durchgespielt
- [ ] Cron aktiv
- [ ] Eine Kopie off-site (PC oder Storage Box)
- [ ] `.env` separat dokumentiert

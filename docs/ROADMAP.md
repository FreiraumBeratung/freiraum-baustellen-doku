# Roadmap — Freiraum Baustellen-Doku

## V1 (aktueller Stand)

- Login / Registrierung lokal (`users.json`)
- Firmenprofil inkl. Standard-Exportformat & Büro-E-Mail
- Logo-Upload & Anzeige im UI
- Mitarbeiterverwaltung (aktiv/inaktiv)
- Baustellenverwaltung mit Status
- Tagesbericht erfassen (Text, Zeiten, Baustelle, Team)
- Bericht **regelbasiert** strukturieren (`/api/structure-report`)
- Bericht speichern, Liste mit Filtern, Detailansicht
- PWA-Grundlage (Manifest, Service Worker, Theme-Farben, Installierbarkeit vorbereitet)

---

## V1.1

- Echte **Speech-to-Text**-Anbindung für das große Eingabefeld
- **PDF-Export** (serverseitig oder clientseitig)
- **Word-Export**
- **Echter E-Mail-Versand** ans Büro (SMTP/API)
- **Fotodokumentation** am Bericht

---

## V1.2

- **Offline-Modus** mit klarer Sync-Strategie
- Automatische **Synchronisation** mit dem Büro-Backend
- **Volltextsuche** über Berichte/Baustellen
- Verbesserte **KI-Strukturierung** (optional cloudbasiert, datenschutzkonform)

---

## V2

- Anbindung **Plancraft**, **Lexware**, **DATEV** (Auswahl je nach Kundenstack)
- **Projektstatus** & Auswertungen
- **Materialauswertung** über erfasste Berichte
- **Nachkalkulation** light
- **Kundenunterschrift** digital
- **Multi-Firmenfähigkeit** (Mandanten)
- **Cloud-Hosting** der PWA + API

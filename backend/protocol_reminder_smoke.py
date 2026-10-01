"""Smoke: Protokoll-Erinnerung (Firmenprofil-Uhr + Home-Hinweis).

Additiv: Schalter default aus, Uhr 21:00 Berlin, faellig erst nach Uhr
und nur bei ungesendeten Stuecken mit Text (letzte 7 Tage).
Kein Rohtext in der API. Sendepfad und create_protocol_doc unveraendert.

Laeuft in-process mit isoliertem Temp-Verzeichnis; beruehrt keine echten Daten.
"""

from __future__ import annotations

import os
import sys
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

os.environ.setdefault("OPENAI_API_KEY", "")

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

_TMP_DIR = Path(tempfile.mkdtemp(prefix="freiraum_protocol_reminder_smoke_"))
print(f"[smoke] using tmp data dir: {_TMP_DIR}")

import main  # noqa: E402
from app.services.site_protocol import (  # noqa: E402
    BERLIN,
    create_protocol_doc,
    mark_protocol_office_sent,
    reminder_clock_due,
)
from app.services.tenant_storage import TenantStore  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(_TMP_DIR)

BERLIN_TZ = ZoneInfo("Europe/Berlin")


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def _owner_headers() -> tuple[dict[str, str], str, TenantStore]:
    user_id = str(uuid.uuid4())
    main.save_users(
        [
            {
                "id": user_id,
                "tenantId": user_id,
                "companyName": "Smoke GmbH",
                "entrepreneurName": "Tester",
                "email": f"protocol-reminder-smoke-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "createdAt": "2026-01-01T00:00:00+00:00",
            }
        ]
    )
    return {"Authorization": f"Bearer {user_id}"}, user_id, TenantStore(user_id)


PROFILE = {
    "companyName": "Smoke GmbH",
    "contactPerson": "Tester",
    "officeEmail": "buero@example.com",
    "phone": "0123",
    "address": "Weg 1",
    "defaultExportFormat": "PDF",
    "defaultRecipientEmail": "",
}

client = TestClient(main.app)
hdrs, owner_id, store = _owner_headers()

# Uhr-Helfer: aus = nie, vor 21:00 = nein, ab 21:00 = ja
_expect(
    reminder_clock_due(False, "21:00", now=datetime(2026, 10, 1, 22, 0, tzinfo=BERLIN_TZ)) is False,
    "disabled clock",
)
_expect(
    reminder_clock_due(True, "21:00", now=datetime(2026, 10, 1, 20, 59, tzinfo=BERLIN_TZ)) is False,
    "before 21:00",
)
_expect(
    reminder_clock_due(True, "21:00", now=datetime(2026, 10, 1, 21, 0, tzinfo=BERLIN_TZ)) is True,
    "at 21:00",
)
_expect(
    reminder_clock_due(True, "00:00", now=datetime(2026, 10, 1, 0, 0, tzinfo=BERLIN_TZ)) is True,
    "at 00:00",
)
_expect(BERLIN.key == "Europe/Berlin", "berlin tz")

# GET Profil: Default aus, 21:00, Fotos bleiben aus
res = client.get("/api/company-profile", headers=hdrs)
_expect(res.status_code == 200, f"profile get: {res.status_code} {res.text}")
prof = res.json()
_expect(prof.get("protocolReminderEnabled") is False, "default reminder off")
_expect(prof.get("protocolReminderTime") == "21:00", f"default time: {prof.get('protocolReminderTime')}")
_expect(prof.get("includePhotosInPdf") is False, "photos default must stay off")

# POST ohne Erinnerungsfelder: bleibt aus / 21:00, Fotos unangetastet
res = client.post("/api/company-profile", headers=hdrs, json=PROFILE)
_expect(res.status_code == 200, f"profile post bare: {res.status_code} {res.text}")
prof = res.json()
_expect(prof.get("protocolReminderEnabled") is False, "bare post must leave reminder off")
_expect(prof.get("protocolReminderTime") == "21:00", "bare post must keep 21:00")
_expect(prof.get("includePhotosInPdf") is False, "bare post must not turn photos on")

# Ungueltige Uhr: 400, Bestand bleibt
res = client.post(
    "/api/company-profile",
    headers=hdrs,
    json={**PROFILE, "protocolReminderEnabled": True, "protocolReminderTime": "99:99"},
)
_expect(res.status_code == 400, f"bad time should 400: {res.status_code} {res.text}")
prof = client.get("/api/company-profile", headers=hdrs).json()
_expect(prof.get("protocolReminderEnabled") is False, "bad time must not enable")
_expect(prof.get("protocolReminderTime") == "21:00", "bad time must not write clock")

# An: 00:00 damit der Smoke unabhängig von der echten Uhr faellig sein kann
res = client.post(
    "/api/company-profile",
    headers=hdrs,
    json={**PROFILE, "protocolReminderEnabled": True, "protocolReminderTime": "00:00"},
)
_expect(res.status_code == 200, f"enable reminder: {res.status_code} {res.text}")
prof = res.json()
_expect(prof.get("protocolReminderEnabled") is True, "enabled")
_expect(prof.get("protocolReminderTime") == "00:00", f"time: {prof.get('protocolReminderTime')}")
_expect(prof.get("includePhotosInPdf") is False, "enable reminder must not touch photos")

# POST ohne Erinnerungsfelder laesst An/00:00 stehen (None-means-leave)
res = client.post("/api/company-profile", headers=hdrs, json=PROFILE)
_expect(res.status_code == 200, f"leave reminder: {res.status_code} {res.text}")
prof = res.json()
_expect(prof.get("protocolReminderEnabled") is True, "None must leave enabled")
_expect(prof.get("protocolReminderTime") == "00:00", "None must leave time")

today = datetime.now(BERLIN).date()
today_iso = today.isoformat()

# Aus: trotz offenem Stueck kein Hinweis (Scan wird nicht angefasst, due=false)
store.write_json(
    "company_profile.json",
    {**store.read_json("company_profile.json", {}), "protocolReminderEnabled": False},
)
thoughts = create_protocol_doc(
    store,
    company_name="Smoke GmbH",
    company_logo_url=None,
    office_email="buero@example.com",
    project_id="",
    project_name="",
    customer_name="",
    date=today_iso,
    mode="thoughts",
    raw_text="Idee fuer Montage und Material",
    polished_text="Idee fuer Montage und Material",
    participants="",
    export_format="PDF",
)
res = client.get("/api/reminders/protocol", headers=hdrs)
_expect(res.status_code == 200, f"reminders off: {res.status_code} {res.text}")
body = res.json()
_expect(body.get("enabled") is False, "enabled false while off")
_expect(body.get("due") is False, "due false while off")
_expect(body.get("items") == [], f"no items while off: {body.get('items')}")
_expect("rawText" not in body, "no rawText on envelope")

# An: Gedankensammlung ungesendet -> due + Titel, ohne Rohtext
store.write_json(
    "company_profile.json",
    {
        **store.read_json("company_profile.json", {}),
        "protocolReminderEnabled": True,
        "protocolReminderTime": "00:00",
    },
)
res = client.get("/api/reminders/protocol", headers=hdrs)
_expect(res.status_code == 200, f"reminders on: {res.status_code} {res.text}")
body = res.json()
_expect(body.get("enabled") is True, "enabled true")
_expect(body.get("time") == "00:00", f"time: {body.get('time')}")
_expect(body.get("due") is True, "due with unsent thoughts")
items = body.get("items") or []
_expect(len(items) == 1, f"one item: {items}")
_expect(items[0].get("id") == thoughts["id"], "id match")
_expect(items[0].get("mode") == "thoughts", "mode thoughts")
_expect(items[0].get("title") == "Gedankensammlung", items[0].get("title"))
_expect(items[0].get("date") == today_iso, items[0].get("date"))
_expect("rawText" not in items[0], "no rawText on item")
_expect("polishedText" not in items[0], "no polishedText on item")

# Schnellnotiz (braucht Baustelle) und unterschriebenes Protokoll ebenfalls
quick = create_protocol_doc(
    store,
    company_name="Smoke GmbH",
    company_logo_url=None,
    office_email="buero@example.com",
    project_id="p1",
    project_name="Schmitz",
    customer_name="Kunde",
    date=today_iso,
    mode="quick",
    raw_text="Kurz notiert auf der Baustelle",
    polished_text="Kurz notiert auf der Baustelle",
    participants="",
    export_format="PDF",
)
signed = create_protocol_doc(
    store,
    company_name="Smoke GmbH",
    company_logo_url=None,
    office_email="buero@example.com",
    project_id="p1",
    project_name="Schmitz",
    customer_name="Kunde",
    date=today_iso,
    mode="signed",
    raw_text="Begehung mit Unterschrift Text",
    polished_text="Begehung mit Unterschrift Text",
    participants="Uli",
    export_format="PDF",
)
res = client.get("/api/reminders/protocol", headers=hdrs)
body = res.json()
modes = {i.get("mode") for i in (body.get("items") or [])}
_expect(body.get("due") is True, "due with three modes")
_expect(modes == {"thoughts", "quick", "signed"}, f"modes: {modes}")
_expect(all("rawText" not in i for i in body.get("items") or []), "no rawText in list")

# Aelter als 7 Tage: nicht in der Liste
old = create_protocol_doc(
    store,
    company_name="Smoke GmbH",
    company_logo_url=None,
    office_email="buero@example.com",
    project_id="p1",
    project_name="Schmitz",
    customer_name="Kunde",
    date=(today - timedelta(days=8)).isoformat(),
    mode="quick",
    raw_text="Alte Schnellnotiz ausserhalb Fenster",
    polished_text="Alte Schnellnotiz ausserhalb Fenster",
    participants="",
    export_format="PDF",
)
res = client.get("/api/reminders/protocol", headers=hdrs)
ids = {i.get("id") for i in (res.json().get("items") or [])}
_expect(old["id"] not in ids, "8 days old must be ignored")
_expect(thoughts["id"] in ids and quick["id"] in ids and signed["id"] in ids, "recent still listed")

# Nach Senden-Markierung (gleicher Pfad wie Sendepfad) verschwindet das Stueck
marked = mark_protocol_office_sent(store, thoughts["id"])
_expect(bool(marked and marked.get("officeSentAt")), "officeSentAt set")
res = client.get("/api/reminders/protocol", headers=hdrs)
ids = {i.get("id") for i in (res.json().get("items") or [])}
_expect(thoughts["id"] not in ids, "sent thoughts must drop")
_expect(quick["id"] in ids, "unsent quick remains")

print("PROTOCOL-REMINDER-SMOKE: OK")

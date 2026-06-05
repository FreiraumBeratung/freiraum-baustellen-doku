"""End-to-End Smoke fuer die neue Mail-Integration.

Was wird abgesichert:
1. Discovery liefert sinnvolle Kandidaten fuer Preset- und Guess-Domains.
2. Mail-Store kann verschluesseln, lesen, ueberschreiben, loeschen.
3. /api/auth/register weist Anlage ab, wenn SMTP-Verify fehlschlaegt,
   und legt User + Mail-Config an, wenn Verify gemockt erfolgreich ist.
4. /api/auth/login synchronisiert das lokale Passwort, wenn der User
   sein Mail-Passwort beim Provider geaendert hat (Fallback-Pfad).
5. /api/reports/{id}/send-office liefert einen klaren 400-Fehler,
   wenn keine Mail-Config gespeichert ist (kein Dry-Run).

Der Test laeuft komplett in-process, mockt verify_smtp_credentials und
beruehrt KEINEN echten SMTP-Server.
"""

from __future__ import annotations

import os
import sys
import tempfile
import uuid
from pathlib import Path

os.environ.setdefault("OPENAI_API_KEY", "")

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

# Isolierte Test-Datenverzeichnisse, damit reale users.json/mail_configs.json
# nicht beeinflusst werden.
_TMP_DIR = Path(tempfile.mkdtemp(prefix="freiraum_mail_smoke_"))
print(f"[smoke] using tmp data dir: {_TMP_DIR}")

import main  # noqa: E402
from app.services import mail_autodiscover, mail_store  # noqa: E402
from app.services.mail_autodiscover import SmtpCandidate, SmtpVerifyResult  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(_TMP_DIR)
mail_store._KEY_FILE = _TMP_DIR / ".mail_key"
mail_store._STORE_FILE = _TMP_DIR / "mail_configs.json"


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


# -- 1. Discovery -----------------------------------------------------------
candidates_web = mail_autodiscover.discover_smtp_servers("foo@web.de")
_expect(any(c.source == "preset" and c.host == "smtp.web.de" for c in candidates_web), "web.de preset fehlt")

candidates_gmail = mail_autodiscover.discover_smtp_servers("foo@gmail.com")
_expect(any(c.host == "smtp.gmail.com" and c.port == 587 for c in candidates_gmail), "gmail preset fehlt")

candidates_unknown = mail_autodiscover.discover_smtp_servers("foo@beispielfirma.eu")
_expect(any(c.host == "smtp.beispielfirma.eu" for c in candidates_unknown), "guess smtp.<domain> fehlt")
_expect(any(c.host == "mail.beispielfirma.eu" for c in candidates_unknown), "guess mail.<domain> fehlt")

# IONOS-Firmendomain per gemocktem MX (ohne echten SMTP-Login)
mail_autodiscover._mx_lookup_override = lambda domain: (  # type: ignore[attr-defined]
    ["mx00.ionos.de", "mx01.ionos.de"] if domain == "freiraum-unternehmensberatung.de" else []
)
candidates_ionos = mail_autodiscover.discover_smtp_servers("info@freiraum-unternehmensberatung.de")
_expect(
    any(c.source == "mx" and c.host == "smtp.ionos.de" for c in candidates_ionos),
    "IONOS-Firmendomain: smtp.ionos.de via MX fehlt",
)
mail_autodiscover._mx_lookup_override = None  # type: ignore[attr-defined]

_expect(mail_autodiscover.provider_hint_for("foo@gmail.com") is not None, "gmail hint fehlt")
_expect(mail_autodiscover.provider_hint_for("foo@web.de") is None, "web.de sollte keinen App-Pw-Hinweis haben")

# -- 2. Mail-Store Roundtrip ------------------------------------------------
mail_store.save_mail_config(
    "demo@web.de", "geheim-1",
    host="smtp.web.de", port=587, use_tls=True, use_ssl=False, source="preset",
)
cfg = mail_store.get_mail_config("demo@web.de")
_expect(cfg is not None and cfg["password"] == "geheim-1", "store roundtrip 1 fehlgeschlagen")

mail_store.save_mail_config(
    "demo@web.de", "neues-pw-2",
    host="smtp.web.de", port=587, use_tls=True, use_ssl=False, source="preset",
)
cfg2 = mail_store.get_mail_config("demo@web.de")
_expect(cfg2 is not None and cfg2["password"] == "neues-pw-2", "ueberschreiben des passworts fehlgeschlagen")

# Klartext darf NICHT in der Datei stehen
raw = (mail_store._STORE_FILE).read_text(encoding="utf-8")
_expect("neues-pw-2" not in raw, "Klartext-Passwort liegt unverschluesselt in mail_configs.json")

_expect(mail_store.delete_mail_config("demo@web.de") is True, "delete sollte True zurueckgeben")
_expect(mail_store.get_mail_config("demo@web.de") is None, "nach delete sollte get None liefern")


# -- 3. Auth-Endpoints mit gemocktem SMTP-Verify ----------------------------
_VERIFY_OK = SmtpVerifyResult(
    ok=True,
    candidate=SmtpCandidate(host="smtp.web.de", port=587, use_tls=True, use_ssl=False, source="preset"),
    error=None,
    provider_hint=None,
)
_VERIFY_FAIL = SmtpVerifyResult(
    ok=False,
    candidate=None,
    error="Authentifizierung fehlgeschlagen: 535 ...",
    provider_hint="Bei Gmail muss ein App-Passwort verwendet werden",
)


def _patch_verify(result: SmtpVerifyResult) -> None:
    def fake(email, password, candidates=None, timeout=10.0):  # noqa: ANN001
        _ = (email, password, candidates, timeout)
        return result

    main.verify_smtp_credentials = fake  # type: ignore[attr-defined]
    mail_autodiscover.verify_smtp_credentials = fake  # type: ignore[assignment]


client = TestClient(main.app)
TEST_EMAIL = f"smoke-{uuid.uuid4().hex[:8]}@web.de"

# 3a) Register schlaegt fehl, wenn SMTP-Verify fehlschlaegt -> kein User angelegt.
_patch_verify(_VERIFY_FAIL)
res = client.post(
    "/api/auth/register",
    json={"companyName": "Acme", "entrepreneurName": "Mux", "email": TEST_EMAIL, "password": "wrong-pw"},
)
_expect(res.status_code == 400, f"register-fail erwartete 400, war {res.status_code}: {res.text}")
detail = res.json().get("detail", "")
_expect("App-Passwort" in detail, f"Provider-Hinweis fehlt in detail: {detail!r}")
_expect(mail_store.get_mail_config(TEST_EMAIL) is None, "Mail-Config sollte bei fail nicht existieren")
_expect(main.find_user_by_email(TEST_EMAIL) is None, "User sollte bei fail nicht existieren")

# 3b) Register klappt bei verify_ok -> User + Mail-Config angelegt.
_patch_verify(_VERIFY_OK)
res = client.post(
    "/api/auth/register",
    json={"companyName": "Acme", "entrepreneurName": "Mux", "email": TEST_EMAIL, "password": "right-pw"},
)
_expect(res.status_code == 200, f"register-ok erwartete 200, war {res.status_code}: {res.text}")
js = res.json()
_expect(js.get("access_token"), "access_token fehlt nach register-ok")
_expect(js.get("mail", {}).get("configured") is True, "mail.configured fehlt")
cfg = mail_store.get_mail_config(TEST_EMAIL)
_expect(cfg is not None and cfg["password"] == "right-pw", "Mail-Config nach register fehlt/falsch")
token = js["access_token"]

# 3c) Login mit korrektem lokalen Passwort: best-effort sync, kein Verify-Block bei Fehler.
res = client.post("/api/auth/login", json={"email": TEST_EMAIL, "password": "right-pw"})
_expect(res.status_code == 200, f"login-ok erwartete 200, war {res.status_code}: {res.text}")

# 3d) Login mit FALSCHEM lokalen Passwort, aber SMTP klappt -> Passwort wird synchronisiert.
_patch_verify(_VERIFY_OK)
res = client.post("/api/auth/login", json={"email": TEST_EMAIL, "password": "neues-mail-pw"})
_expect(res.status_code == 200, f"login-sync erwartete 200, war {res.status_code}: {res.text}")
_expect(res.json().get("mail", {}).get("synced_password") is True, "synced_password flag fehlt")
# Lokales Passwort sollte jetzt das neue sein.
user = main.find_user_by_email(TEST_EMAIL)
_expect(user is not None and user["password"] == "neues-mail-pw", "lokales pw nicht synchronisiert")
cfg = mail_store.get_mail_config(TEST_EMAIL)
_expect(cfg is not None and cfg["password"] == "neues-mail-pw", "mail-store nicht synchronisiert")

# 3e) Login mit falschem pw + SMTP fail -> 401 + Provider-Hint.
_patch_verify(_VERIFY_FAIL)
res = client.post("/api/auth/login", json={"email": TEST_EMAIL, "password": "voellig-falsch"})
_expect(res.status_code == 401, f"login-fail erwartete 401, war {res.status_code}: {res.text}")
detail = res.json().get("detail", "")
_expect("App-Passwort" in detail, f"Provider-Hinweis fehlt im 401-detail: {detail!r}")


# -- 4. /api/reports/.../send-office ohne Mail-Config -> 400 ----------------
# Wir loeschen die Mail-Config und legen einen minimalen Report an.
mail_store.delete_mail_config(TEST_EMAIL)

report_id = "smoke-report-" + uuid.uuid4().hex[:8]
user = main.find_user_by_email(TEST_EMAIL)
_expect(user is not None, "user for send-office test missing")
store = TenantStore(str(user.get("tenantId") or user["id"]))
reports_doc = store.read_json("reports.json", {"reports": []})
reports_doc.setdefault("reports", []).append(
    {"id": report_id, "projectName": "Smoke", "date": "2026-05-25", "exportFormat": "PDF"}
)
store.write_json("reports.json", reports_doc)

prof = store.read_json("company_profile.json", {})
prof["officeEmail"] = "office@example.com"
store.write_json("company_profile.json", prof)

# Aktueller Token ist noch der vom Register-Schritt.
res = client.post(
    f"/api/reports/{report_id}/send-office",
    headers={"Authorization": f"Bearer {token}"},
)
_expect(res.status_code == 400, f"send-office ohne Mail-Config erwartete 400, war {res.status_code}: {res.text}")
_expect("Mail-Anbindung" in res.json().get("detail", ""), "Hinweistext zur fehlenden Mail-Config fehlt")

print("MAIL-INTEGRATION-SMOKE: OK")

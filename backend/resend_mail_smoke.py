"""Smoke: Resend-Pfad additiv, SMTP-Bestandskunden unangetastet."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("OPENAI_API_KEY", "")

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

_TMP = Path(tempfile.mkdtemp(prefix="freiraum_resend_smoke_"))
print(f"[smoke] tmp dir: {_TMP}")

import main  # noqa: E402
from app.services import mail_store, resend_mail  # noqa: E402
from app.services.mail_autodiscover import SmtpVerifyResult  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from office_mail import send_report_to_office  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(_TMP)
mail_store._KEY_FILE = _TMP / ".mail_key"
mail_store._STORE_FILE = _TMP / "mail_configs.json"


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


# -- 1. Key-Schutz: OpenAI-Key zaehlt nicht als Resend --------------------------
os.environ["RESEND_API_KEY"] = "sk-proj-not-resend"
_expect(resend_mail.resend_is_configured() is False, "sk- Key darf Resend nicht aktivieren")
os.environ.pop("RESEND_API_KEY", None)

# -- 2. Anzeigename -------------------------------------------------------------
header = resend_mail.format_from_header(
    {"companyName": "Sven Klein Garten- und Landschaftsbau"},
    "freiraum@berichte.freiraum-unternehmensberatung.de",
)
_expect("Sven Klein" in header, f"Firmenname fehlt im From: {header}")
_expect("via Freiraum" in header, f"via Freiraum fehlt im From: {header}")
_expect("berichte.freiraum-unternehmensberatung.de" in header, f"Domain fehlt: {header}")
_expect("\n" not in header, "From darf keine Zeilenumbrueche haben")

unsafe = resend_mail.format_from_header(
    {"companyName": 'Evil <hack@x.com>\r\nBcc: a@b.de'},
    "freiraum@berichte.freiraum-unternehmensberatung.de",
)
_expect("\r" not in unsafe and "\n" not in unsafe, "Header-Injection nicht gefiltert")
_expect("<hack@" not in unsafe, "spitze Klammern im Namen nicht entfernt")

# -- 3. Fremde From-Domain wird verworfen ---------------------------------------
os.environ["RESEND_FROM_EMAIL"] = "jemand@gmail.com"
_expect(
    resend_mail.from_email() == resend_mail.DEFAULT_FROM_EMAIL,
    "fremde From-Domain muss auf Default fallen",
)
os.environ["RESEND_FROM_EMAIL"] = "freiraum@berichte.freiraum-unternehmensberatung.de"

# -- 4. Ohne Key: Register weiter SMTP-pflichtig --------------------------------
def _verify_fail(email, password, candidates=None, timeout=10.0):  # noqa: ANN001
    _ = (email, password, candidates, timeout)
    return SmtpVerifyResult(ok=False, candidate=None, error="SMTP tot", provider_hint=None)


main.verify_smtp_credentials = _verify_fail  # type: ignore[attr-defined]
client = TestClient(main.app)
smtp_email = f"smtp-{uuid.uuid4().hex[:8]}@web.de"
res = client.post(
    "/api/auth/register",
    json={"companyName": "Alt GmbH", "entrepreneurName": "Chef", "email": smtp_email, "password": "pw-alt"},
)
_expect(res.status_code == 400, f"ohne Resend-Key muss SMTP-Register 400 sein: {res.text}")
_expect(main.find_user_by_email(smtp_email) is None, "User darf ohne SMTP nicht angelegt werden")

# -- 5. Mit Key: Register ohne SMTP, mailMode=freiraum --------------------------
os.environ["RESEND_API_KEY"] = "re_" + ("a" * 40)
_expect(resend_mail.resend_is_configured() is True, "re_ Key muss Resend aktivieren")

frei_email = f"frei-{uuid.uuid4().hex[:8]}@kunde.de"
res = client.post(
    "/api/auth/register",
    json={
        "companyName": "Sven Klein Garten- und Landschaftsbau",
        "entrepreneurName": "Sven Klein",
        "email": frei_email,
        "password": "nur-app-passwort",
    },
)
_expect(res.status_code == 200, f"Resend-Register: {res.text}")
user = main.find_user_by_email(frei_email)
_expect(user is not None, "Freiraum-User fehlt")
_expect(user.get("mailMode") == "freiraum", f"mailMode falsch: {user.get('mailMode')}")
_expect(mail_store.get_mail_config(frei_email) is None, "kein SMTP-Store fuer Freiraum-User")
_expect(res.json().get("mail", {}).get("source") == "freiraum", "mail.source fehlt")
token = res.json()["access_token"]

# Login mit App-Passwort, ohne SMTP
res = client.post("/api/auth/login", json={"email": frei_email, "password": "nur-app-passwort"})
_expect(res.status_code == 200, f"Freiraum-Login: {res.text}")
_expect(res.json().get("mail", {}).get("source") == "freiraum", "Login mail.source falsch")
res = client.post("/api/auth/login", json={"email": frei_email, "password": "falsch"})
_expect(res.status_code == 401, "Freiraum-Login mit falschem PW muss 401 sein")

# -- 6. Send-Office ueber gemocktes Resend --------------------------------------
store = TenantStore(str(user.get("tenantId") or user["id"]))
report_id = "resend-report-" + uuid.uuid4().hex[:8]
reports_doc = store.read_json("reports.json", {"reports": []})
reports_doc.setdefault("reports", []).append(
    {
        "id": report_id,
        "projectName": "Testgarten",
        "date": "2026-09-23",
        "exportFormat": "PDF",
        "employees": ["Sven"],
        "startTime": "07:00",
        "endTime": "16:00",
        "structured": {"summary": "Test", "activities": [], "materials": [], "problems": [], "openItems": [], "customerTalk": ""},
        "rawText": "Test",
        "photos": [],
    }
)
store.write_json("reports.json", reports_doc)
prof = store.read_json("company_profile.json", {})
prof["officeEmail"] = "buero@kunde.de"
prof["companyName"] = "Sven Klein Garten- und Landschaftsbau"
store.write_json("company_profile.json", prof)


class _FakeResendResp:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):  # noqa: ANN002
        return False

    def read(self) -> bytes:
        return b'{"id":"mock"}'


captured: dict[str, object] = {}


def _fake_urlopen(req, timeout=30):  # noqa: ANN001
    captured["url"] = req.full_url
    captured["body"] = req.data
    auth = req.get_header("Authorization") or req.headers.get("Authorization")
    _expect(auth is not None and str(auth).startswith("Bearer re_"), "Authorization fehlt/falsch")
    return _FakeResendResp()


with patch("app.services.resend_mail.urllib.request.urlopen", _fake_urlopen):
    res = client.post(
        f"/api/reports/{report_id}/send-office",
        headers={"Authorization": f"Bearer {token}"},
    )
_expect(res.status_code == 200, f"send-office Resend: {res.status_code} {res.text}")
_expect(captured.get("url") == resend_mail.RESEND_API_URL, "falsche Resend-URL")
body = json.loads(captured["body"])
_expect("via Freiraum" in body.get("from", ""), f"From-Anzeigename fehlt: {body.get('from')}")
_expect(body.get("to") == ["buero@kunde.de"], f"To falsch: {body.get('to')}")
_expect(body.get("reply_to") == "buero@kunde.de", f"Reply-To falsch: {body.get('reply_to')}")
_expect("attachments" in body, "PDF-Anhang fehlt")

# -- 7. SMTP gewinnt, auch wenn mailMode=freiraum -------------------------------
mail_store.save_mail_config(
    frei_email,
    "smtp-secret",
    host="smtp.example.com",
    port=587,
    use_tls=True,
    use_ssl=False,
    source="preset",
)
smtp_cfg = mail_store.get_mail_config(frei_email)
_expect(smtp_cfg is not None, "SMTP-Config zum Vorrang-Test fehlt")

class _FakeSMTP:
    last_message = None

    def __init__(self, *args, **kwargs):  # noqa: ANN002, ANN003
        _ = (args, kwargs)

    def __enter__(self):
        return self

    def __exit__(self, *args):  # noqa: ANN002
        return False

    def ehlo(self) -> None:
        return None

    def starttls(self, context=None) -> None:  # noqa: ANN001
        _ = context

    def login(self, user: str, password: str) -> None:
        _ = (user, password)

    def send_message(self, msg) -> None:  # noqa: ANN001
        _FakeSMTP.last_message = msg


_FakeSMTP.last_message = None
with patch("office_mail.smtplib.SMTP", _FakeSMTP):
    ok, simulated, message = send_report_to_office(
        {
            "id": "prio",
            "projectName": "Alt",
            "date": "2026-09-23",
            "exportFormat": "PDF",
            "employees": [],
            "structured": {"summary": "", "activities": [], "materials": [], "problems": [], "openItems": [], "customerTalk": ""},
            "rawText": "",
            "photos": [],
        },
        {"companyName": "Alt GmbH"},
        "office@example.com",
        mail_config=smtp_cfg,
        photos_upload_dir=_TMP / "photos",
    )
_expect(ok is True, f"SMTP-Pfad muss weiter gehen: {message}")
_expect(_FakeSMTP.last_message is not None, "SMTP wurde nicht genutzt")
_expect(_FakeSMTP.last_message["From"] == frei_email, "SMTP-From darf nicht umgeschrieben werden")
_expect(_FakeSMTP.last_message.get("Reply-To") is None, "SMTP darf kein Reply-To bekommen")

# Aufraeumen, Key nicht in der Umgebung lassen
os.environ.pop("RESEND_API_KEY", None)
print("RESEND-MAIL-SMOKE: OK")

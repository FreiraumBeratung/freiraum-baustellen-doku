"""Smoke Welle M4: Passwort-Hashing — bcrypt, Lazy-Migration, Login/Register."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import uuid
from pathlib import Path

os.environ.setdefault("OPENAI_API_KEY", "")

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

_TMP = Path(tempfile.mkdtemp(prefix="freiraum_password_m4_"))
print(f"[smoke] tmp dir: {_TMP}")

import main  # noqa: E402
from app.services.password_security import hash_password, is_password_hashed, verify_password  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(_TMP)


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def _users_raw_text() -> str:
    return (_TMP / "users.json").read_text(encoding="utf-8")


client = TestClient(main.app)

from app.services import mail_autodiscover  # noqa: E402


def _fake_verify_ok(email, password, candidates=None, timeout=10.0):  # noqa: ANN001
    _ = (email, candidates, timeout)
    if password == "falsch":
        from app.services.mail_autodiscover import SmtpVerifyResult

        return SmtpVerifyResult(ok=False, candidate=None, error="Authentifizierung fehlgeschlagen", provider_hint=None)
    from app.services.mail_autodiscover import SmtpCandidate, SmtpVerifyResult

    c = SmtpCandidate(host="smtp.example.com", port=587, use_tls=True, use_ssl=False, source="preset")
    return SmtpVerifyResult(ok=True, candidate=c, error=None, provider_hint=None)


mail_autodiscover.verify_smtp_credentials = _fake_verify_ok  # type: ignore[assignment]
main.verify_smtp_credentials = _fake_verify_ok  # type: ignore[attr-defined]

# -- 1. Register speichert passwordHash, kein Klartext -----------------------
email_new = f"new-{uuid.uuid4().hex[:8]}@example.com"
res_reg = client.post(
    "/api/auth/register",
    json={
        "companyName": "Neu GmbH",
        "entrepreneurName": "Chef",
        "email": email_new,
        "password": "geheim-register",
    },
)
_expect(res_reg.status_code == 200, f"register: {res_reg.text}")
user_new = main.find_user_by_email(email_new)
_expect(user_new is not None, "user missing after register")
_expect(is_password_hashed(user_new.get("passwordHash")), "passwordHash must be bcrypt")
_expect("password" not in user_new, "no legacy password field on register")
_expect("geheim-register" not in _users_raw_text(), "plaintext must not appear in users.json")

# -- 2. Login mit passwordHash ------------------------------------------------
res_login = client.post("/api/auth/login", json={"email": email_new, "password": "geheim-register"})
_expect(res_login.status_code == 200, f"login hashed user: {res_login.text}")

res_bad = client.post("/api/auth/login", json={"email": email_new, "password": "falsch"})
_expect(res_bad.status_code == 401, "wrong password must 401")

# -- 3. Legacy-Klartext migriert beim Login -----------------------------------
legacy_email = f"legacy-{uuid.uuid4().hex[:8]}@example.com"
legacy_id = str(uuid.uuid4())
main.save_users(
    main.get_users()
    + [
        {
            "id": legacy_id,
            "tenantId": legacy_id,
            "companyName": "Legacy",
            "entrepreneurName": "Alt",
            "email": legacy_email,
            "password": "legacy-plain",
            "licenseActive": True,
            "createdAt": "2026-01-01T00:00:00+00:00",
        }
    ]
)
_expect("legacy-plain" in _users_raw_text(), "legacy plaintext seeded")

res_legacy = client.post("/api/auth/login", json={"email": legacy_email, "password": "legacy-plain"})
_expect(res_legacy.status_code == 200, f"legacy login: {res_legacy.text}")
legacy_user = main.find_user_by_email(legacy_email)
_expect(legacy_user is not None, "legacy user missing")
_expect(is_password_hashed(legacy_user.get("passwordHash")), "legacy migrated to hash")
_expect("password" not in legacy_user, "legacy password field removed")
_expect(verify_password("legacy-plain", legacy_user), "verify after migration")
_expect("legacy-plain" not in _users_raw_text(), "plaintext removed from users.json after login")

# -- 4. Admin-Liste ohne Passwort-Felder --------------------------------------
admin_id = str(uuid.uuid4())
main.save_users(
    main.get_users()
    + [
        {
            "id": admin_id,
            "tenantId": admin_id,
            "companyName": "Admin",
            "email": f"admin-{uuid.uuid4().hex[:6]}@example.com",
            "passwordHash": hash_password("admin-secret"),
            "isAdmin": True,
            "licenseActive": True,
            "createdAt": "2026-06-01T00:00:00+00:00",
        }
    ]
)
listed = client.get("/api/admin/users", headers={"Authorization": f"Bearer {admin_id}"})
_expect(listed.status_code == 200, f"admin list: {listed.text}")
rows = listed.json().get("users") or []
_expect(all("password" not in r and "passwordHash" not in r for r in rows), "admin API hides password fields")
raw_list = json.dumps(rows)
_expect("admin-secret" not in raw_list, "no password leak in admin list")

print("PASSWORD-M4-SMOKE: OK")

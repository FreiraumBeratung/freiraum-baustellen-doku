"""Smoke: Passwort ändern, Admin-Temp, Passwort vergessen — ohne Klartext in users.json."""

from __future__ import annotations

import os
import sys
import tempfile
import uuid
from pathlib import Path
from urllib.parse import parse_qs, urlparse

os.environ.setdefault("OPENAI_API_KEY", "")

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

_TMP = Path(tempfile.mkdtemp(prefix="freiraum_password_reset_"))
print(f"[smoke] tmp dir: {_TMP}")

import main  # noqa: E402
from app.services import password_reset as pwd_reset  # noqa: E402
from app.services.password_security import hash_password, verify_password  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(_TMP)

captured: dict[str, str] = {}


def _fake_send(*, to_email: str, reset_url: str) -> bool:
    captured["email"] = to_email
    captured["url"] = reset_url
    return True


pwd_reset.send_reset_email = _fake_send  # type: ignore[assignment]
main.pwd_reset.send_reset_email = _fake_send  # type: ignore[assignment]


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def _users_raw() -> str:
    return (_TMP / "users.json").read_text(encoding="utf-8")


def _add_owner(tag: str, password: str, *, is_admin: bool = False) -> tuple[str, str, dict[str, str]]:
    user_id = str(uuid.uuid4())
    email = f"{tag}-{uuid.uuid4().hex[:8]}@example.com"
    user = {
        "id": user_id,
        "tenantId": user_id,
        "accountRole": "owner",
        "companyName": f"Firma {tag}",
        "entrepreneurName": f"Chef {tag}",
        "email": email,
        "passwordHash": hash_password(password),
        "licenseActive": True,
        "mailMode": "freiraum",
        "createdAt": "2026-11-04T00:00:00+00:00",
    }
    if is_admin:
        user["isAdmin"] = True
    users = main.get_users()
    users.append(user)
    main.save_users(users)
    return user_id, email, {"Authorization": f"Bearer {user_id}"}


client = TestClient(main.app)

admin_id, admin_email, admin_hdrs = _add_owner("admin", "admin-secret-9", is_admin=True)
user_id, user_email, user_hdrs = _add_owner("pilot", "alt-passwort-1")

# -- 1. Passwort ändern -------------------------------------------------------
bad_cur = client.post(
    "/api/auth/change-password",
    headers=user_hdrs,
    json={"currentPassword": "falsch", "newPassword": "neu-passwort-2"},
)
_expect(bad_cur.status_code == 401, f"wrong current: {bad_cur.text}")
_expect(verify_password("alt-passwort-1", main.find_user_by_id(user_id) or {}), "old pw must still work")

weak = client.post(
    "/api/auth/change-password",
    headers=user_hdrs,
    json={"currentPassword": "alt-passwort-1", "newPassword": "123456"},
)
_expect(weak.status_code == 400, f"weak pw: {weak.text}")

changed = client.post(
    "/api/auth/change-password",
    headers=user_hdrs,
    json={"currentPassword": "alt-passwort-1", "newPassword": "neu-passwort-2"},
)
_expect(changed.status_code == 200, f"change: {changed.text}")
_expect(changed.json().get("mustChangePassword") is False, "flag cleared after self-change")
fresh = main.find_user_by_id(user_id)
_expect(fresh is not None and verify_password("neu-passwort-2", fresh), "new pw works")
_expect(not verify_password("alt-passwort-1", fresh or {}), "old pw dead")
_expect("neu-passwort-2" not in _users_raw(), "plaintext must not land in users.json")

login_new = client.post("/api/auth/login", json={"email": user_email, "password": "neu-passwort-2"})
_expect(login_new.status_code == 200, f"login after change: {login_new.text}")

# -- 2. Admin temporäres Passwort --------------------------------------------
denied = client.post(f"/api/admin/users/{user_id}/temporary-password", headers=user_hdrs)
_expect(denied.status_code == 403, f"non-admin temp: {denied.text}")

issued = client.post(f"/api/admin/users/{user_id}/temporary-password", headers=admin_hdrs)
_expect(issued.status_code == 200, f"admin temp: {issued.text}")
temp = str(issued.json().get("temporaryPassword") or "")
_expect(len(temp) >= 8, "temp password length")
_expect(temp not in _users_raw(), "temp plaintext not stored")
after_temp = main.find_user_by_id(user_id)
_expect(after_temp is not None and after_temp.get("mustChangePassword") is True, "mustChange set")
_expect(verify_password(temp, after_temp or {}), "temp verifies")
login_temp = client.post("/api/auth/login", json={"email": user_email, "password": temp})
_expect(login_temp.status_code == 200, f"login temp: {login_temp.text}")
_expect(login_temp.json().get("mustChangePassword") is True, "session flag after temp")

listed = client.get("/api/admin/users", headers=admin_hdrs)
rows = listed.json().get("users") or []
_expect(all("password" not in r and "passwordHash" not in r and "temporaryPassword" not in r for r in rows), "list hides secrets")

# -- 3. Passwort vergessen ----------------------------------------------------
unknown = client.post("/api/auth/forgot-password", json={"email": "niemand@example.com"})
_expect(unknown.status_code == 200, f"unknown forgot: {unknown.text}")
_expect(unknown.json().get("ok") is True, "generic ok")
_expect("Link" in unknown.json().get("message", "") or "Konto" in unknown.json().get("message", ""), "generic copy")

captured.clear()
forgot = client.post("/api/auth/forgot-password", json={"email": user_email})
_expect(forgot.status_code == 200, f"forgot: {forgot.text}")
_expect(forgot.json().get("message") == unknown.json().get("message"), "same message known/unknown")
_expect(captured.get("email") == user_email, "mail to owner")
reset_url = captured.get("url") or ""
_expect("/passwort-zuruecksetzen?token=" in reset_url, f"reset url: {reset_url}")
token = parse_qs(urlparse(reset_url).query).get("token", [""])[0]
_expect(len(token) >= 16, "token present")
token_file = (_TMP / "password_reset_tokens.json").read_text(encoding="utf-8")
_expect(token not in token_file, "raw token not stored")

reset_ok = client.post(
    "/api/auth/reset-password",
    json={"token": token, "newPassword": "reset-passwort-9"},
)
_expect(reset_ok.status_code == 200, f"reset: {reset_ok.text}")
after_reset = main.find_user_by_id(user_id)
_expect(after_reset is not None and verify_password("reset-passwort-9", after_reset), "reset pw works")
_expect(not after_reset.get("mustChangePassword"), "flag cleared after reset")
_expect("reset-passwort-9" not in _users_raw(), "reset plaintext absent")

reuse = client.post(
    "/api/auth/reset-password",
    json={"token": token, "newPassword": "anderes-passwort-9"},
)
_expect(reuse.status_code == 400, "token one-time")

bogus = client.post(
    "/api/auth/reset-password",
    json={"token": "x" * 32, "newPassword": "anderes-passwort-9"},
)
_expect(bogus.status_code == 400, "bogus token")

login_reset = client.post("/api/auth/login", json={"email": user_email, "password": "reset-passwort-9"})
_expect(login_reset.status_code == 200, f"login after reset: {login_reset.text}")
_expect(login_reset.json().get("mustChangePassword") is not True, "no must-change after self reset")

# Admin-Login unverändert
admin_login = client.post("/api/auth/login", json={"email": admin_email, "password": "admin-secret-9"})
_expect(admin_login.status_code == 200, f"admin login still works: {admin_login.text}")

print("PASSWORD-RESET-SMOKE: OK")

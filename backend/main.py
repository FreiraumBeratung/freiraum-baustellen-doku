"""Freiraum Baustellen-Doku — FastAPI Backend (V1, lokale JSON-Datenhaltung)."""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field, field_validator

from office_mail import send_report_to_office
from report_export import build_attachment_names, build_docx_bytes, build_pdf_bytes
from report_structure import structure_report_fields
from app.services import time_account
from app.services.mail_autodiscover import (
    provider_hint_for,
    verify_smtp_credentials,
)
from app.services.mail_store import (
    get_mail_config,
    has_mail_config,
    save_mail_config,
)
from app.services.quality_filter import apply_quality_filter
from services.ai_report_service import structure_report_with_ai
from services.trade_language_service import (
    build_professional_summary,
    extract_activity_hints,
    extract_material_hints,
    infer_materials_from_activities,
    normalize_trade_language,
)
from services.transcription_service import transcribe_audio

# --- Pfade ---
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = BASE_DIR / "uploads" / "logos"
USERS_FILE = DATA_DIR / "users.json"
COMPANY_FILE = DATA_DIR / "company_profile.json"
EMPLOYEES_FILE = DATA_DIR / "employees.json"
PROJECTS_FILE = DATA_DIR / "projects.json"
REPORTS_FILE = DATA_DIR / "reports.json"
TIME_ENTRIES_FILE = DATA_DIR / "time_entries.json"
AUDIO_UPLOAD_DIR = BASE_DIR / "uploads" / "audio"
AUDIO_UPLOADS_FILE = DATA_DIR / "audio_uploads.json"
PHOTOS_UPLOAD_DIR = BASE_DIR / "uploads" / "photos"
SIGNATURES_UPLOAD_DIR = BASE_DIR / "uploads" / "signatures"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PHOTOS_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
SIGNATURES_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

time_account.configure(TIME_ENTRIES_FILE)

MAX_PHOTOS_PER_REPORT = 10
MAX_PHOTO_UPLOAD_BYTES = 5 * 1024 * 1024
SIGNATURE_ROLES = frozenset({"customer", "employee"})
MAX_SIGNATURE_BYTES = 512 * 1024
MIN_SIGNATURE_BYTES = 80
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

# --- CORS (DEV / WLAN-Handy): localhost + LAN-IPs auf Frontend-Port 51710 -------------
# FREIRAUM_DEV_LAN_CORS=0 schaltet Regex ab (nur noch localhost / 127.0.0.1).
_DEV_LAN_CORS_DISABLED = os.environ.get("FREIRAUM_DEV_LAN_CORS", "1").strip().lower() in (
    "0",
    "false",
    "no",
)
_ORIGINS_FRONTEND_DEV = (
    "http://localhost:51710",
    "http://127.0.0.1:51710",
    "https://localhost:51710",
    "https://127.0.0.1:51710",
)
# Private IPv4-Ziele, Frontend exakt Port 51710 (RFC 1918, typ. Heim-WLAN).
_DEV_WLAN_FRONTEND_REGEX = (
    r"^https?://(?:192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"172\.(?:1[6-9]|2[0-9]|3[01])\.\d{1,3}\.\d{1,3}):51710$"
)

app = FastAPI(title="freiraum-baustellen-doku", version="1.0.0")

_cors_kw: dict[str, Any] = {
    "allow_origins": list(_ORIGINS_FRONTEND_DEV),
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
if not _DEV_LAN_CORS_DISABLED:
    _cors_kw["allow_origin_regex"] = _DEV_WLAN_FRONTEND_REGEX

app.add_middleware(CORSMiddleware, **_cors_kw)


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


MAX_AUDIO_UPLOAD_BYTES = 25 * 1024 * 1024


def _get_audio_uploads_list() -> list[dict[str, Any]]:
    data = _read_json(AUDIO_UPLOADS_FILE, [])
    return data if isinstance(data, list) else []


def _save_audio_uploads_list(items: list[dict[str, Any]]) -> None:
    _write_json(AUDIO_UPLOADS_FILE, items)


def _guess_audio_extension(content_type: str | None, original_name: str) -> str:
    ct = (content_type or "").lower()
    on = (original_name or "").lower()
    if "webm" in ct or on.endswith(".webm"):
        return "webm"
    if "mpeg" in ct or "mp3" in ct or on.endswith(".mp3"):
        return "mp3"
    if "mp4" in ct or "audio/mp4" in ct or on.endswith(".m4a") or on.endswith(".mp4"):
        return "m4a"
    if "ogg" in ct or on.endswith(".ogg"):
        return "ogg"
    if "wav" in ct or on.endswith(".wav"):
        return "wav"
    if "caf" in ct or on.endswith(".caf"):
        return "caf"
    return "webm"


# --- Auth (V1: Klartext-Passwort — TODO Produktiv: Hashing) ---
class RegisterBody(BaseModel):
    companyName: str = Field(..., min_length=1)
    entrepreneurName: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=1)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_register(cls, v: Any) -> str:
        return str(v).strip().lower()


class LoginBody(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_login(cls, v: Any) -> str:
        return str(v).strip().lower()


def hash_password_plain_v1(password: str) -> str:
    # TODO: Passwort-Hashing für Produktivbetrieb ergänzen (bcrypt/argon2)
    return password


def _format_smtp_error_message(
    headline: str,
    smtp_error: str | None,
    provider_hint: str | None,
) -> str:
    """Kompakte, mehrzeilige Fehlermeldung fuer das Login-/Register-UI.

    Das Frontend rendert HTTPException-``detail``-Strings mit ``whitespace-pre-line``,
    so dass wir Provider-Hinweise (z.B. App-Passwort) direkt anhaengen koennen.
    """
    parts: list[str] = [headline]
    if smtp_error:
        parts.append(smtp_error)
    if provider_hint:
        parts.append("Hinweis: " + provider_hint)
    return "\n".join(parts)


def _verify_and_store_smtp(email: str, password: str) -> dict[str, Any]:
    """Führt Auto-Discovery + SMTP-Login durch und speichert die Konfiguration
    bei Erfolg im verschlüsselten Mail-Store. Liefert ein kompaktes Status-Dict
    zurück, das dem Frontend Provider-Hinweise und Quelle (Preset/Guess) zeigt.
    """
    result = verify_smtp_credentials(email, password)
    if not result.ok or result.candidate is None:
        return {
            "ok": False,
            "error": result.error or "SMTP-Verifizierung fehlgeschlagen",
            "provider_hint": result.provider_hint or provider_hint_for(email),
        }
    cand = result.candidate
    save_mail_config(
        email,
        password,
        host=cand.host,
        port=cand.port,
        use_tls=cand.use_tls,
        use_ssl=cand.use_ssl,
        source=cand.source,
    )
    return {
        "ok": True,
        "host": cand.host,
        "port": cand.port,
        "use_tls": cand.use_tls,
        "use_ssl": cand.use_ssl,
        "source": cand.source,
    }


def get_users() -> list[dict]:
    return _read_json(USERS_FILE, [])


def save_users(users: list[dict]) -> None:
    _write_json(USERS_FILE, users)


def find_user_by_email(email: str) -> dict | None:
    for u in get_users():
        if u.get("email", "").lower() == email.lower():
            return u
    return None


def require_bearer(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
    token = authorization.replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Ungültiges Token")
    user = next((u for u in get_users() if u.get("id") == token), None)
    if not user:
        raise HTTPException(status_code=401, detail="Ungültiges Token")
    return token


# --- Company ---
class CompanyProfileBody(BaseModel):
    companyName: str = ""
    contactPerson: str = ""
    officeEmail: str = ""
    phone: str = ""
    address: str = ""
    defaultExportFormat: str = "PDF"
    defaultRecipientEmail: str = ""


# --- Employees ---
class EmployeeCreate(BaseModel):
    name: str
    role: str | None = ""
    active: bool = True
    hoursBalanceStart: float = 0.0
    hoursBalanceStartDate: str | None = None


class EmployeePatch(BaseModel):
    name: str | None = None
    role: str | None = None
    active: bool | None = None
    hoursBalanceStart: float | None = None
    hoursBalanceStartDate: str | None = None


class TimeEntryCreate(BaseModel):
    employeeId: str
    date: str
    hours: float
    note: str


# --- Projects ---
class ProjectCreate(BaseModel):
    name: str
    customer: str = ""
    address: str = ""
    contactPerson: str = ""
    note: str = ""
    status: str = "aktiv"


class ProjectPatch(BaseModel):
    name: str | None = None
    customer: str | None = None
    address: str | None = None
    contactPerson: str | None = None
    note: str | None = None
    status: str | None = None


# --- Structure report ---
class StructureReportBody(BaseModel):
    projectId: str | None = None
    projectName: str | None = None
    customerName: str | None = None
    date: str
    employeeNames: list[str] = []
    startTime: str
    endTime: str
    exportFormat: str = "PDF"
    rawText: str


# --- Save report ---
class StructuredBlock(BaseModel):
    summary: str = ""
    activities: list[str] = []
    materials: list[str] = []
    materialSuggestions: list[str] = []
    machineSuggestions: list[str] = []
    machineHours: list[str] = []
    problems: list[str] = []
    openItems: list[str] = []
    customerTalk: str = ""


class ReportCreateBody(BaseModel):
    companyName: str
    companyLogoUrl: str | None = None
    officeEmail: str = ""
    projectId: str
    projectName: str
    customerName: str = ""
    date: str
    employees: list[str] = []
    employeeIds: list[str] = []
    startTime: str
    endTime: str
    breakMinutes: int = Field(default=45, ge=0, le=480)
    exportFormat: str = "PDF"
    rawText: str
    structured: StructuredBlock


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "freiraum-baustellen-doku",
        "port": 30610,
    }


@app.get("/api/debug/ping")
def debug_ping() -> dict[str, Any]:
    """Connectivity-Check ohne Auth — z. B. Login-Seite / Handy im WLAN."""
    return {
        "ok": True,
        "message": "backend reachable",
        "service": "freiraum-baustellen-doku",
    }


@app.post("/api/auth/register")
def register(body: RegisterBody):
    email_norm = str(body.email).strip().lower()
    if find_user_by_email(email_norm):
        raise HTTPException(status_code=400, detail="E-Mail bereits registriert")

    # SMTP-Auto-Discovery + Login-Test als Eintrittsbedingung. Ohne gueltige
    # Mail-Credentials wird KEIN User angelegt - so ist sichergestellt, dass der
    # Tagesbericht-Versand direkt funktioniert.
    smtp_status = _verify_and_store_smtp(email_norm, body.password)
    if not smtp_status.get("ok"):
        raise HTTPException(
            status_code=400,
            detail=_format_smtp_error_message(
                "Mail-Anbindung fehlgeschlagen",
                smtp_status.get("error"),
                smtp_status.get("provider_hint"),
            ),
        )

    pwd_store = hash_password_plain_v1(body.password)
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "companyName": body.companyName,
        "entrepreneurName": body.entrepreneurName,
        "email": email_norm,
        "password": pwd_store,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    users = get_users()
    users.append(user)
    save_users(users)

    prof = _read_json(
        COMPANY_FILE,
        {
            "companyName": "",
            "contactPerson": "",
            "officeEmail": "",
            "phone": "",
            "address": "",
            "logoFilename": None,
            "defaultExportFormat": "PDF",
            "defaultRecipientEmail": "",
        },
    )
    if not prof.get("companyName"):
        prof["companyName"] = body.companyName
        prof["contactPerson"] = body.entrepreneurName
        prof["officeEmail"] = email_norm
        prof["defaultRecipientEmail"] = email_norm
        _write_json(COMPANY_FILE, prof)

    return {
        "access_token": user_id,
        "token_type": "bearer",
        "user_id": user_id,
        "mail": {
            "configured": True,
            "host": smtp_status.get("host"),
            "port": smtp_status.get("port"),
            "source": smtp_status.get("source"),
        },
    }


@app.post("/api/auth/login")
def login(body: LoginBody):
    email_norm = str(body.email).strip().lower()
    user = find_user_by_email(email_norm)

    if not user:
        # Kein lokaler User vorhanden - aktuelle Auth-Architektur erfordert
        # eine separate Registrierung. Wir geben den gleichen 401 zurueck wie
        # bei Passwort-Fehlern und lassen das Frontend auf "Registrieren" leiten.
        raise HTTPException(status_code=401, detail="Ungültige Zugangsdaten")

    local_pw_ok = user.get("password") == hash_password_plain_v1(body.password)

    if not local_pw_ok:
        # Fallback: Vielleicht wurde das Mail-Passwort beim Provider geaendert.
        # Wenn der echte SMTP-Login erfolgreich ist, synchronisieren wir das
        # lokale Passwort und lassen den User durch. Sonst harter 401.
        smtp_status = _verify_and_store_smtp(email_norm, body.password)
        if not smtp_status.get("ok"):
            raise HTTPException(
                status_code=401,
                detail=_format_smtp_error_message(
                    "Ungültige Zugangsdaten",
                    smtp_status.get("error"),
                    smtp_status.get("provider_hint"),
                ),
            )
        users = get_users()
        for u in users:
            if u.get("email", "").lower() == email_norm:
                u["password"] = hash_password_plain_v1(body.password)
                break
        save_users(users)
        return {
            "access_token": user["id"],
            "token_type": "bearer",
            "user_id": user["id"],
            "mail": {
                "configured": True,
                "host": smtp_status.get("host"),
                "port": smtp_status.get("port"),
                "source": smtp_status.get("source"),
                "synced_password": True,
            },
        }

    # Lokales Passwort stimmt. SMTP wird best-effort verifiziert/aktualisiert -
    # ein Fehler hier blockiert den App-Login NICHT, damit der User auch offline
    # oder bei kurzzeitigen Provider-Problemen weiterarbeiten kann.
    smtp_status = _verify_and_store_smtp(email_norm, body.password)
    return {
        "access_token": user["id"],
        "token_type": "bearer",
        "user_id": user["id"],
        "mail": {
            "configured": bool(smtp_status.get("ok")) or has_mail_config(email_norm),
            "host": smtp_status.get("host"),
            "port": smtp_status.get("port"),
            "source": smtp_status.get("source"),
            "smtp_error": None if smtp_status.get("ok") else smtp_status.get("error"),
            "provider_hint": None if smtp_status.get("ok") else smtp_status.get("provider_hint"),
        },
    }


@app.post("/api/auth/logout")
def logout(_user: str = Depends(require_bearer)):
    """Stateless Logout-Endpoint.

    Das eigentliche Auslog-Token wird im Frontend (localStorage) entfernt. Die
    zentrale Mail-Konfiguration bleibt bewusst erhalten, da innerhalb einer
    Firma mehrere Mitarbeiter dieselbe Geschaefts-Mail nutzen koennen - jeder
    naechste Login synchronisiert das Passwort bei Bedarf automatisch.
    """
    _ = _user
    return {"ok": True}


@app.get("/api/company-profile")
def get_company_profile(_user: str = Depends(require_bearer)):
    _ = _user
    prof = _read_json(COMPANY_FILE, {})
    logo_fn = prof.get("logoFilename")
    logo_url = None
    if logo_fn:
        logo_url = f"/uploads/logos/{logo_fn}"
    return {**prof, "logoUrl": logo_url}


@app.post("/api/company-profile")
def post_company_profile(body: CompanyProfileBody, _user: str = Depends(require_bearer)):
    _ = _user
    existing = _read_json(COMPANY_FILE, {})
    merged = {**existing, **body.model_dump()}
    _write_json(COMPANY_FILE, merged)
    return get_company_profile()


@app.post("/api/company-logo")
async def upload_logo(file: UploadFile = File(...), _user: str = Depends(require_bearer)):
    _ = _user
    if not file.filename:
        raise HTTPException(status_code=400, detail="Keine Datei")

    ext = Path(file.filename).suffix.lower()
    if ext not in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}:
        raise HTTPException(status_code=400, detail="Nur Bilddateien erlaubt")

    new_name = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOADS_DIR / new_name
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Datei zu groß (max. 5 MB)")
    dest.write_bytes(content)

    prof = _read_json(COMPANY_FILE, {})
    old = prof.get("logoFilename")
    if old:
        old_path = UPLOADS_DIR / old
        if old_path.exists():
            try:
                old_path.unlink()
            except OSError:
                pass
    prof["logoFilename"] = new_name
    _write_json(COMPANY_FILE, prof)
    return {"logoFilename": new_name, "logoUrl": f"/uploads/logos/{new_name}"}


@app.post("/api/audio/upload")
async def upload_audio(
    file: UploadFile = File(...),
    reportDraftId: str | None = Form(default=None),
    projectId: str | None = Form(default=None),
    date: str | None = Form(default=None),
    _user: str = Depends(require_bearer),
):
    """Audio-Rohtrack speichern; Transkription separat unter /api/audio/{id}/transcribe."""
    _ = _user
    content = await file.read()
    n = len(content)
    if n > MAX_AUDIO_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Datei zu groß (max. 25 MB)")
    if n == 0:
        raise HTTPException(status_code=400, detail="Leere Audiodatei")

    aid = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    ext = _guess_audio_extension(file.content_type, file.filename or "")
    safe_name = f"audio_{ts}_{aid}.{ext}"
    dest = AUDIO_UPLOAD_DIR / safe_name
    dest.write_bytes(content)

    draft = (reportDraftId or "").strip()
    pid = (projectId or "").strip()
    ds = (date or "").strip()
    original = file.filename if file.filename else ""
    ctype = file.content_type if file.content_type else "application/octet-stream"

    rec: dict[str, Any] = {
        "id": aid,
        "filename": safe_name,
        "originalFilename": original,
        "contentType": ctype,
        "sizeBytes": n,
        "projectId": pid or None,
        "date": ds or None,
        "reportDraftId": draft or None,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }

    uploads = list(_get_audio_uploads_list())
    uploads.append(rec)
    _save_audio_uploads_list(uploads)

    return {
        "ok": True,
        "audioId": aid,
        "filename": safe_name,
        "message": "Audio wurde gespeichert. Transkription folgt im nächsten Schritt.",
    }


def _resolve_audio_upload_path(rec: dict[str, Any]) -> Path:
    fn = rec.get("filename")
    if not isinstance(fn, str) or not fn or "/" in fn or "\\" in fn or fn.strip() != fn:
        raise HTTPException(status_code=400, detail="Ungültiger Audiodateiname")
    base = AUDIO_UPLOAD_DIR.resolve()
    path = (AUDIO_UPLOAD_DIR / fn).resolve()
    try:
        path.relative_to(base)
    except ValueError:
        raise HTTPException(status_code=404, detail="Audiodatei nicht gefunden")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Audiodatei nicht gefunden")
    return path


@app.post("/api/audio/{audio_id}/transcribe")
def transcribe_stored_audio(audio_id: str, _user: str = Depends(require_bearer)):
    """Transkription eines zuvor hochgeladenen Tracks (V1: Dummy-Text)."""
    _ = _user
    uploads = _get_audio_uploads_list()
    rec = next((u for u in uploads if isinstance(u, dict) and str(u.get("id")) == audio_id), None)
    if not rec:
        raise HTTPException(status_code=404, detail="Audio nicht gefunden")
    path = _resolve_audio_upload_path(rec)
    text = transcribe_audio(str(path))
    return {"ok": True, "audioId": audio_id, "transcript": text}


@app.get("/api/audio/uploads")
def list_audio_uploads(_user: str = Depends(require_bearer)):
    """Chronologie der gespeicherten Audio-Tracks (JSON-Liste)."""
    _ = _user
    uploads = list(_get_audio_uploads_list())
    uploads_sorted = sorted(uploads, key=lambda x: str(x.get("createdAt", "")), reverse=True)
    return {"uploads": uploads_sorted}


@app.get("/api/employees")
def list_employees(_user: str = Depends(require_bearer)):
    _ = _user
    data = _read_json(EMPLOYEES_FILE, {"employees": []})
    return data


@app.post("/api/employees")
def create_employee(body: EmployeeCreate, _user: str = Depends(require_bearer)):
    _ = _user
    data = _read_json(EMPLOYEES_FILE, {"employees": []})
    emp = {
        "id": str(uuid.uuid4()),
        "name": body.name.strip(),
        "role": (body.role or "").strip(),
        "active": body.active,
        "hoursBalanceStart": round(float(body.hoursBalanceStart), 2),
    }
    start_date = time_account.employee_hours_balance_start_date({"hoursBalanceStartDate": body.hoursBalanceStartDate})
    hours_start = emp["hoursBalanceStart"]
    if hours_start != 0 and not start_date:
        raise HTTPException(status_code=400, detail="Stand zum Datum erforderlich bei Startsaldo ungleich 0")
    if start_date:
        emp["hoursBalanceStartDate"] = start_date
    data.setdefault("employees", []).append(emp)
    _write_json(EMPLOYEES_FILE, data)
    return emp


@app.patch("/api/employees/{employee_id}")
def patch_employee(employee_id: str, body: EmployeePatch, _user: str = Depends(require_bearer)):
    _ = _user
    data = _read_json(EMPLOYEES_FILE, {"employees": []})
    for e in data.get("employees", []):
        if e.get("id") == employee_id:
            if body.name is not None:
                e["name"] = body.name
            if body.role is not None:
                e["role"] = body.role
            if body.active is not None:
                e["active"] = body.active
            if body.hoursBalanceStart is not None:
                e["hoursBalanceStart"] = round(float(body.hoursBalanceStart), 2)
            if body.hoursBalanceStartDate is not None:
                raw_date = str(body.hoursBalanceStartDate or "").strip()
                if not raw_date:
                    e.pop("hoursBalanceStartDate", None)
                else:
                    normalized = time_account.employee_hours_balance_start_date({"hoursBalanceStartDate": raw_date})
                    if not normalized:
                        raise HTTPException(status_code=400, detail="Ungültiges Datum für Startsaldo (YYYY-MM-DD)")
                    e["hoursBalanceStartDate"] = normalized
            hours_start = round(float(e.get("hoursBalanceStart") or 0), 2)
            if hours_start != 0 and not time_account.employee_hours_balance_start_date(e):
                raise HTTPException(status_code=400, detail="Stand zum Datum erforderlich bei Startsaldo ungleich 0")
            if hours_start == 0:
                e.pop("hoursBalanceStartDate", None)
            _write_json(EMPLOYEES_FILE, data)
            return e
    raise HTTPException(status_code=404, detail="Mitarbeiter nicht gefunden")


@app.get("/api/time-entries")
def list_time_entries_endpoint(
    employeeId: str | None = None,
    month: str | None = None,
    _user: str = Depends(require_bearer),
):
    _ = _user
    entries = time_account.list_time_entries(
        read_json=_read_json,
        employee_id=employeeId,
        month=month,
    )
    return {"entries": entries, "count": len(entries)}


@app.post("/api/time-entries")
def create_time_entry_endpoint(body: TimeEntryCreate, _user: str = Depends(require_bearer)):
    _ = _user
    employees_data = _read_json(EMPLOYEES_FILE, {"employees": []})
    try:
        entry = time_account.create_manual_time_entry(
            employee_id=body.employeeId,
            date_str=body.date,
            hours=body.hours,
            note=body.note,
            employees=list(employees_data.get("employees") or []),
            read_json=_read_json,
            write_json=_write_json,
        )
    except ValueError as exc:
        code = str(exc)
        messages = {
            "employee_not_found": "Mitarbeiter nicht gefunden",
            "invalid_date": "Ungültiges Datum (YYYY-MM-DD)",
            "hours_zero": "Stunden dürfen nicht 0 sein",
            "hours_out_of_range": "Stunden müssen zwischen -24 und +24 liegen",
            "note_required": "Bitte kurzen Grund angeben (mind. 2 Zeichen)",
        }
        raise HTTPException(status_code=400, detail=messages.get(code, "Ungültige Korrektur")) from exc
    return entry


@app.delete("/api/time-entries/{entry_id}")
def delete_time_entry_endpoint(entry_id: str, _user: str = Depends(require_bearer)):
    _ = _user
    removed = time_account.delete_time_entry(entry_id, read_json=_read_json, write_json=_write_json)
    if not removed:
        raise HTTPException(status_code=404, detail="Buchung nicht gefunden")
    return {"ok": True}


@app.get("/api/time-accounts")
def list_time_accounts_endpoint(
    month: str | None = None,
    _user: str = Depends(require_bearer),
):
    _ = _user
    employees_data = _read_json(EMPLOYEES_FILE, {"employees": []})
    return time_account.list_time_accounts(
        list(employees_data.get("employees") or []),
        read_json=_read_json,
        month=month,
    )


def _time_export_payload(month: str | None) -> dict[str, Any]:
    month_prefix = str(month or datetime.now(timezone.utc).strftime("%Y-%m")).strip()[:7]
    if not re.match(r"^\d{4}-\d{2}$", month_prefix):
        raise HTTPException(status_code=400, detail="Ungültiger Monat (YYYY-MM)")

    employees_data = _read_json(EMPLOYEES_FILE, {"employees": []})
    employees = list(employees_data.get("employees") or [])
    entries = time_account.list_time_entries(read_json=_read_json, month=month_prefix)
    reports_data = _read_json(REPORTS_FILE, {"reports": []})
    reports_by_id = {
        str(r.get("id") or ""): r for r in (reports_data.get("reports") or []) if isinstance(r, dict) and r.get("id")
    }
    entries = time_account.enrich_entries_for_export(entries, reports_by_id)
    accounts_doc = time_account.list_time_accounts(employees, read_json=_read_json, month=month_prefix)
    company = _read_json(COMPANY_FILE, {})
    company_name = str(company.get("companyName") or "")

    return {
        "entries": entries,
        "accounts": list(accounts_doc.get("accounts") or []),
        "month": month_prefix,
        "company_name": company_name,
    }


@app.get("/api/time-accounts/export/csv")
def export_time_accounts_csv(
    month: str | None = None,
    _user: str = Depends(require_bearer),
):
    _ = _user
    payload = _time_export_payload(month)
    blob = time_account.build_time_export_csv(**payload)
    ascii_fn = f"stundenkonto_{payload['month']}.csv"
    return Response(
        content=blob,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": _content_disposition_attachment(ascii_fn, ascii_fn),
        },
    )


@app.get("/api/time-accounts/export/xlsx")
def export_time_accounts_xlsx(
    month: str | None = None,
    _user: str = Depends(require_bearer),
):
    _ = _user
    payload = _time_export_payload(month)
    try:
        blob = time_account.build_time_export_xlsx(**payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Excel-Export konnte nicht erstellt werden.") from exc
    ascii_fn = f"stundenkonto_{payload['month']}.xlsx"
    return Response(
        content=blob,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": _content_disposition_attachment(ascii_fn, ascii_fn),
        },
    )


@app.get("/api/projects")
def list_projects(_user: str = Depends(require_bearer)):
    _ = _user
    return _read_json(PROJECTS_FILE, {"projects": []})


@app.post("/api/projects")
def create_project(body: ProjectCreate, _user: str = Depends(require_bearer)):
    _ = _user
    data = _read_json(PROJECTS_FILE, {"projects": []})
    proj = {
        "id": str(uuid.uuid4()),
        "name": body.name.strip(),
        "customer": body.customer.strip(),
        "address": body.address.strip(),
        "contactPerson": body.contactPerson.strip(),
        "note": body.note.strip(),
        "status": body.status if body.status in {"aktiv", "pausiert", "abgeschlossen"} else "aktiv",
    }
    data.setdefault("projects", []).append(proj)
    _write_json(PROJECTS_FILE, data)
    return proj


@app.patch("/api/projects/{project_id}")
def patch_project(project_id: str, body: ProjectPatch, _user: str = Depends(require_bearer)):
    _ = _user
    data = _read_json(PROJECTS_FILE, {"projects": []})
    for p in data.get("projects", []):
        if p.get("id") == project_id:
            if body.name is not None:
                p["name"] = body.name
            if body.customer is not None:
                p["customer"] = body.customer
            if body.address is not None:
                p["address"] = body.address
            if body.contactPerson is not None:
                p["contactPerson"] = body.contactPerson
            if body.note is not None:
                p["note"] = body.note
            if body.status is not None:
                if body.status in {"aktiv", "pausiert", "abgeschlossen"}:
                    p["status"] = body.status
            _write_json(PROJECTS_FILE, data)
            return p
    raise HTTPException(status_code=404, detail="Baustelle nicht gefunden")


def _merge_ai_core_into_local_structured(ai_core: dict[str, Any], local: dict[str, Any]) -> dict[str, Any]:
    """Übernimmt KI-Zusammenfassung & Bereiche; Arbeitszeit/Participants/Rohtext bleiben lokal konsistent."""
    merged = dict(local)
    merged["summary"] = str(ai_core.get("summary") or "")
    merged["activities"] = list(ai_core.get("activities") or [])
    merged["materials"] = list(ai_core.get("materials") or [])
    merged["problems"] = list(ai_core.get("problems") or [])
    merged["openItems"] = list(ai_core.get("openItems") or [])
    merged["customerTalk"] = str(ai_core.get("customerTalk") or "")
    return merged


def _dedupe_preserve(seq: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in seq:
        val = str(raw or "").strip()
        if not val:
            continue
        key = val.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(val)
    return out


def _ensure_clean_structured(structured: dict[str, Any]) -> dict[str, Any]:
    result = dict(structured)
    result["activities"] = _dedupe_preserve([str(x) for x in (result.get("activities") or [])])
    result["materials"] = _dedupe_preserve([str(x) for x in (result.get("materials") or [])])
    result["materialSuggestions"] = _dedupe_preserve([str(x) for x in (result.get("materialSuggestions") or [])])
    result["machineSuggestions"] = _dedupe_preserve([str(x) for x in (result.get("machineSuggestions") or [])])
    result["machineHours"] = _dedupe_preserve([str(x) for x in (result.get("machineHours") or [])])
    result["problems"] = _dedupe_preserve(list(result.get("problems") or []))
    result["openItems"] = _dedupe_preserve(list(result.get("openItems") or []))
    result["summary"] = str(result.get("summary") or "").strip() or "Keine Angabe"
    result["customerTalk"] = str(result.get("customerTalk") or "").strip() or "Keine Angabe"
    return result


def _ensure_clean_structured_final(structured: dict[str, Any]) -> dict[str, Any]:
    result = dict(structured)
    result["activities"] = _dedupe_preserve([str(x) for x in (result.get("activities") or [])])
    result["materials"] = _dedupe_preserve([str(x) for x in (result.get("materials") or [])])
    result["materialSuggestions"] = _dedupe_preserve([str(x) for x in (result.get("materialSuggestions") or [])])
    result["machineSuggestions"] = _dedupe_preserve([str(x) for x in (result.get("machineSuggestions") or [])])
    result["machineHours"] = _dedupe_preserve([str(x) for x in (result.get("machineHours") or [])])
    result["problems"] = _dedupe_preserve([str(x) for x in (result.get("problems") or [])])
    result["openItems"] = _dedupe_preserve([str(x) for x in (result.get("openItems") or [])])
    result["summary"] = str(result.get("summary") or "").strip() or "Keine Angabe"
    result["customerTalk"] = str(result.get("customerTalk") or "").strip() or "Keine Angabe"
    return result


@app.post("/api/structure-report")
def api_structure_report(body: StructureReportBody, _user: str = Depends(require_bearer)):
    _ = _user
    prof = _read_json(COMPANY_FILE, {})
    company_nm = str(prof.get("companyName") or "").strip()
    normalized_raw = normalize_trade_language(body.rawText)

    local_structured = structure_report_fields(
        normalized_raw,
        body.employeeNames,
        body.startTime,
        body.endTime,
        body.date,
        project_name=body.projectName,
        customer_name=body.customerName,
    )

    structured_by: str = "local"
    structured_dict: dict[str, Any] = local_structured

    ai_try = structure_report_with_ai(
        {
            "companyName": company_nm,
            "projectName": body.projectName,
            "customerName": body.customerName,
            "date": body.date,
            "employeeNames": body.employeeNames,
            "startTime": body.startTime,
            "endTime": body.endTime,
            "rawText": normalized_raw,
        }
    )
    if ai_try:
        structured_dict = _merge_ai_core_into_local_structured(ai_try, local_structured)
        structured_by = "openai"

    structured_dict = _ensure_clean_structured_final(structured_dict)

    activity_hints = extract_activity_hints(normalized_raw)
    structured_dict["activities"] = _dedupe_preserve(
        [str(x) for x in (list(structured_dict.get("activities") or []) + activity_hints)]
    )

    inferred_materials = infer_materials_from_activities(structured_dict.get("activities") or [])
    hinted_materials = extract_material_hints(normalized_raw)
    structured_dict["materials"] = _dedupe_preserve(
        [
            str(x)
            for x in (list(structured_dict.get("materials") or []) + inferred_materials + hinted_materials)
        ]
    )

    has_acts = bool(structured_dict.get("activities"))
    if has_acts:
        structured_dict["summary"] = build_professional_summary(
            {
                "projectName": body.projectName,
                "date": body.date,
                "employeeNames": body.employeeNames,
            },
            structured_dict,
        )

    structured_dict = apply_quality_filter(
        {
            "projectName": body.projectName,
            "date": body.date,
            "employeeNames": body.employeeNames,
            "rawText": body.rawText,
        },
        structured_dict,
    )

    structured_dict = _ensure_clean_structured_final(structured_dict)

    return {
        "projectId": body.projectId,
        "projectName": body.projectName or "Keine Angabe",
        "customerName": body.customerName or "Keine Angabe",
        "date": body.date,
        "exportFormat": body.exportFormat,
        "structured": structured_dict,
        "structuredBy": structured_by,
    }


@app.get("/api/reports")
def list_reports(
    projectId: str | None = None,
    month: str | None = None,
    _user: str = Depends(require_bearer),
):
    _ = _user
    data = _read_json(REPORTS_FILE, {"reports": []})
    reports = list(data.get("reports", []))
    reports.sort(key=lambda r: r.get("createdAt", ""), reverse=True)

    if projectId:
        reports = [r for r in reports if r.get("projectId") == projectId]
    if month and len(month) >= 7:
        prefix = month[:7]
        reports = [r for r in reports if str(r.get("date", "")).startswith(prefix)]

    return {"reports": reports}


@app.post("/api/reports")
def create_report(body: ReportCreateBody, _user: str = Depends(require_bearer)):
    _ = _user
    prof = _read_json(COMPANY_FILE, {})
    logo_fn = prof.get("logoFilename")
    base = "http://localhost:30610"
    company_logo_url = None
    if logo_fn:
        company_logo_url = f"{base}/uploads/logos/{logo_fn}"
    if body.companyLogoUrl:
        company_logo_url = body.companyLogoUrl

    rid = str(uuid.uuid4())
    doc = {
        "id": rid,
        "companyId": "local-company",
        "companyName": body.companyName,
        "companyLogoUrl": company_logo_url,
        "officeEmail": body.officeEmail or prof.get("officeEmail", ""),
        "projectId": body.projectId,
        "projectName": body.projectName,
        "customerName": body.customerName,
        "date": body.date,
        "employees": body.employees,
        "employeeIds": [str(x).strip() for x in body.employeeIds if str(x).strip()],
        "startTime": body.startTime,
        "endTime": body.endTime,
        "breakMinutes": int(body.breakMinutes),
        "exportFormat": body.exportFormat,
        "rawText": body.rawText,
        "structured": body.structured.model_dump(),
        "photos": [],
        "signatures": {"customer": None, "employee": None},
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    _write_json_reports(doc)
    employees_data = _read_json(EMPLOYEES_FILE, {"employees": []})
    doc["timeBooking"] = time_account.sync_entries_for_report(
        doc,
        list(employees_data.get("employees") or []),
        read_json=_read_json,
        write_json=_write_json,
    )
    return doc


def _write_json_reports(new_report: dict) -> None:
    data = _read_json(REPORTS_FILE, {"reports": []})
    data.setdefault("reports", []).append(new_report)
    _write_json(REPORTS_FILE, data)


def _find_report_doc(report_id: str) -> dict[str, Any]:
    data = _read_json(REPORTS_FILE, {"reports": []})
    for r in data.get("reports", []):
        if r.get("id") == report_id:
            return r
    raise HTTPException(status_code=404, detail="Bericht nicht gefunden")


def _report_photos_list(report: dict[str, Any]) -> list[dict[str, Any]]:
    raw = report.get("photos")
    if not isinstance(raw, list):
        return []
    return [p for p in raw if isinstance(p, dict)]


def _photo_public_url(filename: str) -> str:
    return f"/uploads/photos/{filename}"


def _photo_api_item(entry: dict[str, Any]) -> dict[str, Any]:
    fn = str(entry.get("filename") or "")
    return {
        "id": entry.get("id"),
        "filename": fn,
        "originalFilename": entry.get("originalFilename"),
        "contentType": entry.get("contentType"),
        "sizeBytes": entry.get("sizeBytes"),
        "uploadedAt": entry.get("uploadedAt"),
        "url": _photo_public_url(fn) if fn else None,
    }


def _resolve_photo_path(filename: str) -> Path:
    fn = str(filename or "")
    if not fn or "/" in fn or "\\" in fn or fn.strip() != fn:
        raise HTTPException(status_code=400, detail="Ungültiger Fotodateiname")
    base = PHOTOS_UPLOAD_DIR.resolve()
    path = (PHOTOS_UPLOAD_DIR / fn).resolve()
    try:
        path.relative_to(base)
    except ValueError:
        raise HTTPException(status_code=404, detail="Foto nicht gefunden")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Foto nicht gefunden")
    return path


def _guess_photo_extension(content_type: str | None, filename: str) -> str:
    ct = (content_type or "").split(";")[0].strip().lower()
    if ct == "image/jpeg":
        return "jpg"
    if ct == "image/png":
        return "png"
    if ct == "image/webp":
        return "webp"
    ext = Path(filename or "").suffix.lower()
    if ext == ".jpeg":
        return "jpg"
    if ext in {".jpg", ".png", ".webp"}:
        return ext.lstrip(".")
    return "jpg"


def _save_report_photos(report_id: str, photos: list[dict[str, Any]]) -> None:
    data = _read_json(REPORTS_FILE, {"reports": []})
    for r in data.get("reports", []):
        if r.get("id") == report_id:
            r["photos"] = photos
            _write_json(REPORTS_FILE, data)
            return
    raise HTTPException(status_code=404, detail="Bericht nicht gefunden")


def _delete_report_photo_files(report: dict[str, Any]) -> None:
    for entry in _report_photos_list(report):
        fn = entry.get("filename")
        if not isinstance(fn, str) or not fn:
            continue
        try:
            path = _resolve_photo_path(fn)
            path.unlink(missing_ok=True)
        except HTTPException:
            pass
        except OSError:
            pass


def _empty_signatures_doc() -> dict[str, Any]:
    return {"customer": None, "employee": None}


def _report_signatures_doc(report: dict[str, Any]) -> dict[str, Any]:
    raw = report.get("signatures")
    out = _empty_signatures_doc()
    if not isinstance(raw, dict):
        return out
    for role in SIGNATURE_ROLES:
        entry = raw.get(role)
        if isinstance(entry, dict) and entry.get("filename"):
            out[role] = entry
    return out


def _signature_public_url(filename: str) -> str:
    return f"/uploads/signatures/{filename}"


def _signature_api_item(role: str, entry: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(entry, dict):
        return None
    fn = str(entry.get("filename") or "")
    if not fn:
        return None
    return {
        "id": entry.get("id"),
        "role": role,
        "filename": fn,
        "contentType": entry.get("contentType"),
        "sizeBytes": entry.get("sizeBytes"),
        "signedAt": entry.get("signedAt"),
        "signedByLabel": entry.get("signedByLabel"),
        "url": _signature_public_url(fn),
    }


def _resolve_signature_path(filename: str) -> Path:
    fn = str(filename or "")
    if not fn or "/" in fn or "\\" in fn or fn.strip() != fn:
        raise HTTPException(status_code=400, detail="Ungültiger Signaturdateiname")
    base = SIGNATURES_UPLOAD_DIR.resolve()
    path = (SIGNATURES_UPLOAD_DIR / fn).resolve()
    try:
        path.relative_to(base)
    except ValueError:
        raise HTTPException(status_code=404, detail="Signatur nicht gefunden")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Signatur nicht gefunden")
    return path


def _validate_signature_role(role: str) -> str:
    r = str(role or "").strip().lower()
    if r not in SIGNATURE_ROLES:
        raise HTTPException(status_code=400, detail="Ungültige Signatur-Rolle.")
    return r


def _validate_signature_png(content: bytes) -> None:
    n = len(content)
    if n < MIN_SIGNATURE_BYTES:
        raise HTTPException(status_code=400, detail="Signatur ist leer oder zu klein.")
    if n > MAX_SIGNATURE_BYTES:
        raise HTTPException(status_code=400, detail="Signaturdatei zu groß.")
    if not content.startswith(PNG_MAGIC):
        raise HTTPException(status_code=400, detail="Nur PNG-Signaturen erlaubt.")


def _save_report_signatures(report_id: str, signatures: dict[str, Any]) -> None:
    data = _read_json(REPORTS_FILE, {"reports": []})
    for r in data.get("reports", []):
        if r.get("id") == report_id:
            r["signatures"] = signatures
            _write_json(REPORTS_FILE, data)
            return
    raise HTTPException(status_code=404, detail="Bericht nicht gefunden")


def _delete_signature_file(filename: str | None) -> None:
    if not isinstance(filename, str) or not filename:
        return
    try:
        _resolve_signature_path(filename).unlink(missing_ok=True)
    except HTTPException:
        pass
    except OSError:
        pass


def _delete_report_signature_files(report: dict[str, Any]) -> None:
    for entry in _report_signatures_doc(report).values():
        if isinstance(entry, dict):
            _delete_signature_file(entry.get("filename"))


def _content_disposition_attachment(ascii_filename: str, utf8_filename: str) -> str:
    enc = quote(utf8_filename, safe="")
    return f'attachment; filename="{ascii_filename}"; filename*=UTF-8\'\'{enc}'


@app.get("/api/reports/{report_id}")
def get_report(report_id: str, _user: str = Depends(require_bearer)):
    _ = _user
    return _find_report_doc(report_id)


@app.delete("/api/reports/{report_id}")
def delete_report(report_id: str, _user: str = Depends(require_bearer)):
    _ = _user
    data = _read_json(REPORTS_FILE, {"reports": []})
    reports_list = list(data.get("reports", []))
    target = next((r for r in reports_list if r.get("id") == report_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Bericht nicht gefunden")
    _delete_report_photo_files(target)
    _delete_report_signature_files(target)
    time_account.delete_entries_for_report(report_id, read_json=_read_json, write_json=_write_json)
    next_list = [r for r in reports_list if r.get("id") != report_id]
    data["reports"] = next_list
    _write_json(REPORTS_FILE, data)
    return {"ok": True}


@app.get("/api/reports/{report_id}/photos")
def list_report_photos(report_id: str, _user: str = Depends(require_bearer)):
    _ = _user
    report = _find_report_doc(report_id)
    photos = [_photo_api_item(p) for p in _report_photos_list(report)]
    return {
        "photos": photos,
        "count": len(photos),
        "maxPhotos": MAX_PHOTOS_PER_REPORT,
    }


@app.post("/api/reports/{report_id}/photos")
async def upload_report_photo(
    report_id: str,
    file: UploadFile = File(...),
    _user: str = Depends(require_bearer),
):
    """Baustellenfoto zu einem gespeicherten Tagesbericht hochladen (max. 10 pro Bericht)."""
    _ = _user
    report = _find_report_doc(report_id)
    photos = _report_photos_list(report)
    if len(photos) >= MAX_PHOTOS_PER_REPORT:
        raise HTTPException(
            status_code=400,
            detail=f"Maximal {MAX_PHOTOS_PER_REPORT} Fotos pro Bericht erlaubt.",
        )

    if not file.filename:
        raise HTTPException(status_code=400, detail="Keine Datei")

    ext = Path(file.filename).suffix.lower()
    if ext == ".jpeg":
        ext = ".jpg"
    if ext not in {".jpg", ".png", ".webp"}:
        raise HTTPException(status_code=400, detail="Nur JPEG-, PNG- oder WebP-Bilder erlaubt")

    content = await file.read()
    n = len(content)
    if n == 0:
        raise HTTPException(status_code=400, detail="Leere Bilddatei")
    if n > MAX_PHOTO_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="Datei zu groß (max. 5 MB)")

    photo_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    file_ext = _guess_photo_extension(file.content_type, file.filename or "")
    safe_name = f"photo_{ts}_{photo_id}.{file_ext}"
    dest = PHOTOS_UPLOAD_DIR / safe_name
    dest.write_bytes(content)

    original = file.filename if file.filename else ""
    ctype = file.content_type if file.content_type else "application/octet-stream"
    entry: dict[str, Any] = {
        "id": photo_id,
        "filename": safe_name,
        "originalFilename": original,
        "contentType": ctype,
        "sizeBytes": n,
        "uploadedAt": datetime.now(timezone.utc).isoformat(),
    }
    photos.append(entry)
    _save_report_photos(report_id, photos)

    return {
        "ok": True,
        "photo": _photo_api_item(entry),
        "count": len(photos),
        "maxPhotos": MAX_PHOTOS_PER_REPORT,
    }


@app.delete("/api/reports/{report_id}/photos/{photo_id}")
def delete_report_photo(
    report_id: str,
    photo_id: str,
    _user: str = Depends(require_bearer),
):
    _ = _user
    report = _find_report_doc(report_id)
    photos = _report_photos_list(report)
    kept: list[dict[str, Any]] = []
    removed: dict[str, Any] | None = None
    for p in photos:
        if str(p.get("id")) == photo_id and removed is None:
            removed = p
            continue
        kept.append(p)
    if removed is None:
        raise HTTPException(status_code=404, detail="Foto nicht gefunden")

    fn = removed.get("filename")
    if isinstance(fn, str) and fn:
        try:
            _resolve_photo_path(fn).unlink(missing_ok=True)
        except HTTPException:
            pass
        except OSError:
            pass

    _save_report_photos(report_id, kept)
    return {
        "ok": True,
        "count": len(kept),
        "maxPhotos": MAX_PHOTOS_PER_REPORT,
    }


def _signatures_api_payload(report: dict[str, Any]) -> dict[str, Any]:
    doc = _report_signatures_doc(report)
    return {
        role: _signature_api_item(role, doc.get(role))
        for role in sorted(SIGNATURE_ROLES)
    }


@app.get("/api/reports/{report_id}/signatures")
def list_report_signatures(report_id: str, _user: str = Depends(require_bearer)):
    _ = _user
    report = _find_report_doc(report_id)
    signatures = _signatures_api_payload(report)
    count = sum(1 for v in signatures.values() if v is not None)
    return {"signatures": signatures, "count": count}


@app.post("/api/reports/{report_id}/signatures/{role}")
async def upload_report_signature(
    report_id: str,
    role: str,
    file: UploadFile = File(...),
    signedByLabel: str | None = Form(None),
    _user: str = Depends(require_bearer),
):
    """Unterschrift fuer Kunde oder Mitarbeiter speichern (PNG, max. eine pro Rolle)."""
    _ = _user
    sig_role = _validate_signature_role(role)
    report = _find_report_doc(report_id)

    if not file.filename:
        raise HTTPException(status_code=400, detail="Keine Datei")

    content = await file.read()
    _validate_signature_png(content)

    signatures = _report_signatures_doc(report)
    previous = signatures.get(sig_role)
    if isinstance(previous, dict):
        _delete_signature_file(previous.get("filename"))

    sig_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    safe_name = f"sig_{ts}_{sig_role}_{sig_id}.png"
    dest = SIGNATURES_UPLOAD_DIR / safe_name
    dest.write_bytes(content)

    label = str(signedByLabel or "").strip()[:120] or None
    entry: dict[str, Any] = {
        "id": sig_id,
        "role": sig_role,
        "filename": safe_name,
        "contentType": "image/png",
        "sizeBytes": len(content),
        "signedAt": datetime.now(timezone.utc).isoformat(),
    }
    if label:
        entry["signedByLabel"] = label

    signatures[sig_role] = entry
    _save_report_signatures(report_id, signatures)

    item = _signature_api_item(sig_role, entry)
    count = sum(1 for v in signatures.values() if isinstance(v, dict))
    return {"ok": True, "signature": item, "signatures": _signatures_api_payload({"signatures": signatures}), "count": count}


@app.delete("/api/reports/{report_id}/signatures/{role}")
def delete_report_signature(
    report_id: str,
    role: str,
    _user: str = Depends(require_bearer),
):
    _ = _user
    sig_role = _validate_signature_role(role)
    report = _find_report_doc(report_id)
    signatures = _report_signatures_doc(report)
    previous = signatures.get(sig_role)
    if not isinstance(previous, dict):
        raise HTTPException(status_code=404, detail="Signatur nicht gefunden")

    _delete_signature_file(previous.get("filename"))
    signatures[sig_role] = None
    _save_report_signatures(report_id, signatures)
    count = sum(1 for v in signatures.values() if isinstance(v, dict))
    return {"ok": True, "signatures": _signatures_api_payload({"signatures": signatures}), "count": count}


class SendOfficeResponse(BaseModel):
    ok: bool
    simulated: bool
    message: str


@app.post("/api/reports/{report_id}/send-office", response_model=SendOfficeResponse)
def send_report_to_office_endpoint(
    report_id: str,
    _user: str = Depends(require_bearer),
) -> SendOfficeResponse:
    rep = _find_report_doc(report_id)
    prof = _read_json(COMPANY_FILE, {})
    office = str(prof.get("officeEmail") or "").strip()
    if not office:
        raise HTTPException(
            status_code=400,
            detail="Keine Büro-E-Mail im Firmenprofil hinterlegt.",
        )

    # SMTP-Daten aus dem verschluesselten User-Store laden. Token = user_id.
    sender_email = ""
    for u in get_users():
        if u.get("id") == _user:
            sender_email = str(u.get("email", "")).strip().lower()
            break
    if not sender_email:
        raise HTTPException(
            status_code=401,
            detail="Versand nicht möglich: Anmeldung nicht mehr gültig. Bitte erneut anmelden.",
        )
    mail_config = get_mail_config(sender_email)
    if not mail_config:
        raise HTTPException(
            status_code=400,
            detail=(
                "Mail-Anbindung fehlt. Bitte einmal in der App ausloggen und "
                "wieder einloggen, damit die SMTP-Daten geprüft und gespeichert werden."
            ),
        )

    ok, simulated, message = send_report_to_office(
        rep,
        prof,
        office,
        mail_config=mail_config,
        photos_upload_dir=PHOTOS_UPLOAD_DIR,
    )
    if not ok:
        raise HTTPException(status_code=500, detail=message or "Bericht konnte nicht gesendet werden.")
    return SendOfficeResponse(ok=True, simulated=simulated, message=message)


@app.get("/api/reports/{report_id}/export/pdf")
def export_report_pdf(report_id: str, _user: str = Depends(require_bearer)):
    _ = _user
    rep = _find_report_doc(report_id)
    prof = _read_json(COMPANY_FILE, {})
    try:
        blob = build_pdf_bytes(rep, prof)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Export konnte nicht erstellt werden.",
        )
    ascii_fn, desc_fn = build_attachment_names(rep, "pdf")
    return Response(
        content=blob,
        media_type="application/pdf",
        headers={
            "Content-Disposition": _content_disposition_attachment(ascii_fn, desc_fn),
        },
    )


@app.get("/api/reports/{report_id}/export/word")
def export_report_word(report_id: str, _user: str = Depends(require_bearer)):
    _ = _user
    rep = _find_report_doc(report_id)
    prof = _read_json(COMPANY_FILE, {})
    try:
        blob = build_docx_bytes(rep, prof)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Export konnte nicht erstellt werden.",
        )
    ascii_fn, desc_fn = build_attachment_names(rep, "docx")
    return Response(
        content=blob,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": _content_disposition_attachment(ascii_fn, desc_fn),
        },
    )


app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR.parent)), name="uploads")


# Optional: Root für Health auch ohne trailing — bereits GET /

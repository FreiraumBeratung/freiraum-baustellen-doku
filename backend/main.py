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

from logo_image_utils import normalize_logo_bytes
from office_mail import (
    send_collective_protocol_to_office,
    send_collective_to_office,
    send_delivery_note_to_office,
    send_feedback_mail,
    send_protocol_to_office,
    send_report_to_office,
)
from report_export import (
    build_attachment_names,
    build_collective_attachment_names,
    build_collective_docx_bytes,
    build_collective_pdf_bytes,
    build_collective_protocol_attachment_names,
    build_collective_protocol_pdf_bytes,
    build_delivery_note_attachment_names,
    build_delivery_note_pdf_bytes,
    build_docx_bytes,
    build_pdf_bytes,
    build_protocol_attachment_names,
    build_protocol_pdf_bytes,
)
from report_structure import structure_report_fields
from app.services import time_account
from app.services.delivery_note import (
    MAX_PAGES_PER_DELIVERY_NOTE,
    create_delivery_note_doc,
    delivery_note_photos_list,
    find_delivery_note,
    read_delivery_notes,
    remove_delivery_note,
    save_delivery_note_photos,
)
from app.services.site_protocol import (
    create_protocol_doc,
    find_protocol,
    is_thoughts_mode,
    mark_protocol_office_sent,
    protocol_entrepreneur_display_name,
    protocol_partner_display_name,
    protocol_photos_list,
    protocol_signatures_doc,
    read_protocols,
    remove_protocol,
    save_protocol_photos,
    save_protocol_signatures,
)
from app.services.quality_filter import apply_quality_filter
from app.services.mail_autodiscover import (
    provider_hint_for,
    verify_smtp_credentials,
)
from app.services.mail_store import (
    get_mail_config,
    has_mail_config,
    save_mail_config,
)
from app.services.password_security import (
    apply_password_hash_to_user,
    hash_password,
    user_needs_password_migration,
    verify_password,
)
from app.services.admin_users import (
    bootstrap_admin_from_env,
    delete_user_account,
    is_user_admin,
    list_users_public,
    set_user_license,
)
from app.services.account_roles import (
    access_public_view,
    effective_permissions,
    find_tenant_owner,
    find_user_by_username,
    find_worker_for_employee,
    find_workers_by_username,
    has_permission,
    is_company_owner,
    is_worker,
    normalize_permissions,
    normalize_username,
    owner_email_for_smtp,
    username_taken_in_tenant,
    worker_login_active,
)
from app.services.license import LICENSE_SUSPENDED_DETAIL, is_license_active
from app.services.tenant_storage import (
    TenantStore,
    migrate_legacy_data_if_needed,
    repair_owner_tenant_from_legacy_backup,
    tenant_id_for_user,
)
from services.ai_report_service import (
    polish_collective_summary_with_ai,
    polish_customer_talk_with_ai,
    polish_problem_open_with_ai,
    polish_protocol_transcript_with_ai,
    polish_summary_with_ai,
    structure_report_with_ai,
)
from app.services.activity_canonicalizer import collect_unmatched_chunks
from app.services.speech_telemetry import record_unmatched_speech
from app.services import collective_report as collective
from app.services import collective_protocol as collective_proto
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
USERS_FILE = DATA_DIR / "users.json"
# Legacy-Pfade (nur Migration); Laufzeit-Daten liegen unter data/tenants/{tenantId}/
UPLOADS_DIR = BASE_DIR / "uploads" / "logos"
PHOTOS_UPLOAD_DIR = BASE_DIR / "uploads" / "photos"
SIGNATURES_UPLOAD_DIR = BASE_DIR / "uploads" / "signatures"
AUDIO_UPLOAD_DIR = BASE_DIR / "uploads" / "audio"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PHOTOS_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
SIGNATURES_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_PHOTOS_PER_REPORT = 10
MAX_PHOTOS_PER_PROTOCOL = 10
MAX_PHOTOS_PER_DELIVERY_NOTE = MAX_PAGES_PER_DELIVERY_NOTE
MAX_PHOTO_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_FEEDBACK_ATTACHMENTS = 3
SIGNATURE_ROLES = frozenset({"customer", "employee"})
MAX_SIGNATURE_BYTES = 512 * 1024
MIN_SIGNATURE_BYTES = 80
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
FEEDBACK_RECEIVER_EMAIL = "info@freiraum-unternehmensberatung.de"

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


def _get_audio_uploads_list(store: TenantStore) -> list[dict[str, Any]]:
    data = store.read_json("audio_uploads.json", [])
    return data if isinstance(data, list) else []


def _save_audio_uploads_list(store: TenantStore, items: list[dict[str, Any]]) -> None:
    store.write_json("audio_uploads.json", items)


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


# --- Auth (M4: bcrypt passwordHash, Lazy-Migration von legacy password) ---
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
    # API-Feld bleibt "email" (Frontend-Kompatibilität), Inhalt: E-Mail ODER Benutzername.
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_login_identity(cls, v: Any) -> str:
        return str(v).strip()


class EmployeeAccessBody(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=4, max_length=200)
    permissions: list[str] = Field(default_factory=list)
    loginActive: bool = True


class EmployeeAccessPatchBody(BaseModel):
    username: str | None = Field(default=None, min_length=2, max_length=64)
    password: str | None = Field(default=None, min_length=4, max_length=200)
    permissions: list[str] | None = None
    loginActive: bool | None = None


def _persist_user_password(email_norm: str, plain: str) -> None:
    users = get_users()
    for u in users:
        if str(u.get("email", "")).lower() == email_norm:
            apply_password_hash_to_user(u, plain)
            save_users(users)
            return


def _migrate_user_password_if_needed(email_norm: str, plain: str) -> None:
    users = get_users()
    for u in users:
        if str(u.get("email", "")).lower() == email_norm:
            if user_needs_password_migration(u):
                apply_password_hash_to_user(u, plain)
                save_users(users)
            return


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


def find_user_by_id(user_id: str) -> dict | None:
    for u in get_users():
        if u.get("id") == user_id:
            return u
    return None


def require_admin(user_id: str = Depends(require_bearer)) -> str:
    user = find_user_by_id(user_id)
    if not user or not is_user_admin(user):
        raise HTTPException(status_code=403, detail="Kein Administrator-Zugang")
    return user_id


def _auth_session_fields(user: dict[str, Any]) -> dict[str, Any]:
    owner = is_company_owner(user)
    return {
        "licenseActive": _effective_license_active(user),
        "isAdmin": is_user_admin(user),
        "accountRole": "owner" if owner else "worker",
        "permissions": sorted(effective_permissions(user)),
        "displayName": (
            str(user.get("entrepreneurName") or user.get("companyName") or user.get("email") or "")
            if owner
            else str(user.get("displayName") or user.get("username") or "")
        ),
    }


def _effective_license_active(user: dict[str, Any]) -> bool:
    """Worker erben die Lizenz vom Firmen-Owner — Pilot-Konten unverändert."""
    if is_company_owner(user):
        return is_license_active(user)
    owner = find_tenant_owner(get_users(), tenant_id_for_user(user))
    if not owner:
        return False
    return is_license_active(owner)


def get_tenant_store(user_id: str = Depends(require_bearer)) -> TenantStore:
    user = next((u for u in get_users() if u.get("id") == user_id), None)
    if not user:
        raise HTTPException(status_code=401, detail="Ungültiges Token")
    if is_worker(user) and not worker_login_active(user):
        raise HTTPException(status_code=403, detail="Zugang gesperrt. Bitte den Geschäftsführer kontaktieren.")
    return TenantStore(tenant_id_for_user(user))


def require_active_license(user_id: str = Depends(require_bearer)) -> str:
    user = next((u for u in get_users() if u.get("id") == user_id), None)
    if not user:
        raise HTTPException(status_code=401, detail="Ungültiges Token")
    if is_worker(user) and not worker_login_active(user):
        raise HTTPException(status_code=403, detail="Zugang gesperrt. Bitte den Geschäftsführer kontaktieren.")
    if not _effective_license_active(user):
        raise HTTPException(status_code=403, detail=LICENSE_SUSPENDED_DETAIL)
    return user_id


def require_company_owner(user_id: str = Depends(require_active_license)) -> str:
    user = find_user_by_id(user_id)
    if not user or not is_company_owner(user):
        raise HTTPException(
            status_code=403,
            detail="Nur der Geschäftsführer kann diese Funktion nutzen.",
        )
    return user_id


def require_permission(permission: str):
    def _dep(user_id: str = Depends(require_active_license)) -> str:
        user = find_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="Ungültiges Token")
        if is_company_owner(user):
            return user_id
        if has_permission(user, permission):
            return user_id
        raise HTTPException(status_code=403, detail="Keine Berechtigung für diese Funktion.")

    return _dep


def _smtp_sender_email_for_user_id(user_id: str) -> str:
    user = find_user_by_id(user_id)
    return owner_email_for_smtp(get_users(), user)


def get_tenant_store_write(user_id: str = Depends(require_active_license)) -> TenantStore:
    user = next((u for u in get_users() if u.get("id") == user_id), None)
    if not user:
        raise HTTPException(status_code=401, detail="Ungültiges Token")
    return TenantStore(tenant_id_for_user(user))


@app.on_event("startup")
def _startup_m1_tenant_migration() -> None:
    migrate_legacy_data_if_needed(read_users=get_users, save_users=save_users)
    repair_owner_tenant_from_legacy_backup(read_users=get_users)
    bootstrap_admin_from_env(read_users=get_users, save_users=save_users)


def _normalize_company_profile(prof: dict[str, Any]) -> dict[str, Any]:
    export_fmt = str(prof.get("defaultExportFormat") or "PDF").strip()
    if export_fmt.lower() == "pdf":
        export_fmt = "PDF"
    elif export_fmt.lower() == "word":
        export_fmt = "Word"
    return {
        "companyName": str(prof.get("companyName") or ""),
        "contactPerson": str(prof.get("contactPerson") or ""),
        "officeEmail": str(prof.get("officeEmail") or ""),
        "phone": str(prof.get("phone") or ""),
        "address": str(prof.get("address") or ""),
        "defaultExportFormat": export_fmt,
        "defaultRecipientEmail": str(prof.get("defaultRecipientEmail") or ""),
        "logoFilename": prof.get("logoFilename"),
    }


def _logo_public_url(store: TenantStore, logo_fn: str | None) -> str | None:
    if not logo_fn:
        return None
    return f"/uploads/tenants/{store.tenant_id}/logos/{logo_fn}"


def _company_profile_response(store: TenantStore) -> dict[str, Any]:
    raw = store.read_json("company_profile.json", {})
    prof = _normalize_company_profile(raw if isinstance(raw, dict) else {})
    logo_fn = prof.get("logoFilename")
    logo_url = None
    if logo_fn:
        fn = str(logo_fn)
        if store.resolve_upload_file("logos", fn):
            logo_url = _logo_public_url(store, fn)
        elif (UPLOADS_DIR / fn).is_file():
            logo_url = f"/uploads/logos/{fn}"
    return {**prof, "logoUrl": logo_url}


# --- Company ---
class CompanyProfileBody(BaseModel):
    companyName: str = ""
    contactPerson: str = ""
    officeEmail: str = ""
    phone: str = ""
    address: str = ""
    defaultExportFormat: str = "PDF"
    defaultRecipientEmail: str = ""


def _validate_company_profile_body(body: CompanyProfileBody) -> None:
    if not body.companyName.strip():
        raise HTTPException(status_code=400, detail="Firmenname fehlt")
    if not body.contactPerson.strip():
        raise HTTPException(status_code=400, detail="Ansprechpartner fehlt")
    office = body.officeEmail.strip()
    if not office or "@" not in office:
        raise HTTPException(status_code=400, detail="Gültige Büro-E-Mail erforderlich")
    if not body.phone.strip():
        raise HTTPException(status_code=400, detail="Telefonnummer fehlt")
    if not body.address.strip():
        raise HTTPException(status_code=400, detail="Adresse fehlt")
    fmt = body.defaultExportFormat.strip()
    if fmt not in {"PDF", "Word"}:
        raise HTTPException(status_code=400, detail="Exportformat muss PDF oder Word sein")


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
    # Folgebericht/Sammelbericht (optional, rein additiv): seriesMode=True ordnet den
    # Bericht dem laufenden Durchlauf der Baustelle zu. notes = freie Besonderheiten.
    seriesMode: bool = False
    notes: str = Field(default="", max_length=5000)


class ProtocolPolishBody(BaseModel):
    rawText: str = Field(..., min_length=3, max_length=50000)


class ProtocolCreateBody(BaseModel):
    projectId: str = ""
    projectName: str = ""
    customerName: str = ""
    date: str
    mode: str = Field(default="quick", pattern="^(quick|signed|thoughts)$")
    rawText: str = Field(..., min_length=3, max_length=50000)
    polishedText: str = Field(default="", max_length=50000)
    participants: str = Field(default="", max_length=500)
    exportFormat: str = "PDF"


class DeliveryNoteCreateBody(BaseModel):
    projectId: str = Field(..., min_length=1, max_length=200)
    projectName: str = Field(default="", max_length=300)
    customerName: str = Field(default="", max_length=300)
    date: str = ""
    note: str = Field(default="", max_length=500)


class FeedbackCreateBody(BaseModel):
    category: str = Field(default="Verbesserung")
    message: str = Field(..., min_length=3, max_length=5000)
    page: str = ""
    appVersion: str = ""
    reportId: str = ""


def _image_attachment_parts(content_type: str | None, filename: str) -> tuple[str, str]:
    ct = (content_type or "").split(";")[0].strip().lower()
    fn = filename.lower()
    if ct in {"image/jpeg", "image/jpg"} or fn.endswith((".jpg", ".jpeg")):
        return "image", "jpeg"
    if ct == "image/png" or fn.endswith(".png"):
        return "image", "png"
    if ct == "image/webp" or fn.endswith(".webp"):
        return "image", "webp"
    return "application", "octet-stream"


async def _read_feedback_attachments(files: list[UploadFile]) -> list[tuple[str, bytes, str, str]]:
    if len(files) > MAX_FEEDBACK_ATTACHMENTS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximal {MAX_FEEDBACK_ATTACHMENTS} Anhänge erlaubt.",
        )
    out: list[tuple[str, bytes, str, str]] = []
    for i, file in enumerate(files):
        if not file.filename:
            continue
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
        original = Path(file.filename).name or f"anhang-{i + 1}{ext}"
        main, sub = _image_attachment_parts(file.content_type, original)
        out.append((original, content, main, sub))
    return out


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


@app.post("/api/feedback")
async def create_feedback(
    category: str = Form(default="Verbesserung"),
    message: str = Form(...),
    page: str = Form(default=""),
    appVersion: str = Form(default=""),
    reportId: str = Form(default=""),
    files: list[UploadFile] = File(default=[]),
    user_id: str = Depends(require_bearer),
):
    user = find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Ungültiges Token")

    store = TenantStore(tenant_id_for_user(user))
    profile = store.read_json("company_profile.json", {})
    company_name = str(profile.get("companyName") or user.get("companyName") or "").strip()
    category_norm = str(category or "Verbesserung").strip().title()
    if category_norm not in {"Problem", "Verbesserung", "Lob"}:
        category_norm = "Verbesserung"

    message_text = str(message or "").strip()
    if len(message_text) < 3:
        raise HTTPException(status_code=400, detail="Feedback ist zu kurz.")
    if len(message_text) > 5000:
        raise HTTPException(status_code=400, detail="Feedback ist zu lang.")

    page_path = str(page or "").strip()[:200]
    app_version = str(appVersion or "").strip()[:80]
    report_id = str(reportId or "").strip()[:80]
    report_meta: dict[str, Any] | None = None
    if report_id:
        try:
            report_doc = _find_report_doc(store, report_id)
            report_meta = {
                "id": report_id,
                "projectName": str(report_doc.get("projectName") or "").strip(),
                "customerName": str(report_doc.get("customerName") or "").strip(),
                "date": str(report_doc.get("date") or "").strip(),
            }
        except HTTPException:
            report_meta = {"id": report_id}

    attachments = await _read_feedback_attachments(files)

    created_at = datetime.now(timezone.utc).isoformat()
    feedback_entry: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "createdAt": created_at,
        "category": category_norm,
        "message": message_text,
        "page": page_path,
        "appVersion": app_version,
        "userId": user_id,
        "userEmail": str(user.get("email") or "").strip().lower(),
        "companyName": company_name,
        "reportId": report_id or None,
        "attachmentCount": len(attachments),
    }
    feedback_rows = store.read_json("feedback.json", {"items": []})
    items = feedback_rows.get("items") if isinstance(feedback_rows, dict) else []
    if not isinstance(items, list):
        items = []
    items.append(feedback_entry)
    store.write_json("feedback.json", {"items": items})

    sender_email = _smtp_sender_email_for_user_id(user_id)
    mail_config = get_mail_config(sender_email) if sender_email else None
    if not mail_config:
        raise HTTPException(
            status_code=400,
            detail=(
                "Mail-Anbindung fehlt. Bitte einmal ausloggen und wieder einloggen, "
                "damit SMTP-Daten aktualisiert werden."
            ),
        )

    local_time = datetime.now().strftime("%d.%m.%Y %H:%M")
    subject = f"[App-Feedback] {category_norm} | {company_name or sender_email or 'Unbekannt'}"
    lines = [
        "Neues App-Feedback eingegangen.",
        "",
        f"Kategorie: {category_norm}",
        f"Firma: {company_name or 'Keine Angabe'}",
        f"Absender: {sender_email or 'Keine Angabe'}",
        f"Seite: {page_path or 'Unbekannt'}",
        f"App-Version: {app_version or 'Unbekannt'}",
        f"Zeitpunkt: {local_time}",
    ]
    if report_meta:
        lines.extend(
            [
                "",
                "Verknüpfter Bericht:",
                f"Bericht-ID: {report_meta.get('id') or report_id}",
            ]
        )
        if report_meta.get("projectName"):
            lines.append(f"Baustelle: {report_meta['projectName']}")
        if report_meta.get("customerName"):
            lines.append(f"Kunde: {report_meta['customerName']}")
        if report_meta.get("date"):
            lines.append(f"Datum: {report_meta['date']}")
    if attachments:
        lines.extend(["", f"Anhänge: {len(attachments)} Bild(er)"])
    lines.extend(["", "Feedback-Text:", message_text])
    ok, send_message = send_feedback_mail(
        to_email=FEEDBACK_RECEIVER_EMAIL,
        subject=subject,
        body="\n".join(lines),
        mail_config=mail_config,
        attachments=attachments,
    )
    if not ok:
        raise HTTPException(status_code=500, detail=send_message or "Feedback konnte nicht gesendet werden.")

    if attachments:
        return {
            "ok": True,
            "message": f"Danke! Feedback mit {len(attachments)} Anhang/Anhängen wurde gesendet.",
        }
    return {"ok": True, "message": "Danke! Feedback wurde gesendet."}


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

    pwd_hash = hash_password(body.password)
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "tenantId": user_id,
        "accountRole": "owner",
        "companyName": body.companyName,
        "entrepreneurName": body.entrepreneurName,
        "email": email_norm,
        "passwordHash": pwd_hash,
        "licenseActive": True,
        "isAdmin": False,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    users = get_users()
    users.append(user)
    save_users(users)

    store = TenantStore(user_id)
    prof = store.read_json(
        "company_profile.json",
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
        store.write_json("company_profile.json", prof)

    return {
        "access_token": user_id,
        "token_type": "bearer",
        "user_id": user_id,
        **_auth_session_fields(user),
        "mail": {
            "configured": True,
            "host": smtp_status.get("host"),
            "port": smtp_status.get("port"),
            "source": smtp_status.get("source"),
        },
    }


@app.post("/api/auth/login")
def login(body: LoginBody):
    identity = str(body.email or "").strip()
    identity_l = identity.lower()
    users = get_users()

    # E-Mail (@) → Owner; sonst Benutzername → Worker (firma-eindeutig).
    if "@" in identity_l:
        user = find_user_by_email(identity_l)
    else:
        matches = find_workers_by_username(users, identity_l)
        if len(matches) == 0:
            user = None
        elif len(matches) == 1:
            user = matches[0]
        else:
            # Selber Username in mehreren Firmen: Passwort entscheidet (genau ein Treffer).
            pwd_hits = [u for u in matches if verify_password(body.password, u)]
            if len(pwd_hits) == 1:
                user = pwd_hits[0]
            else:
                raise HTTPException(
                    status_code=401,
                    detail="Benutzername mehrdeutig. Bitte den Geschäftsführer um einen eindeutigen Benutzernamen bitten.",
                )

    if not user:
        raise HTTPException(status_code=401, detail="Ungültige Zugangsdaten")

    # Mitarbeiter-Zugang: kein SMTP-Sync, nur lokales Passwort + Sperre.
    if is_worker(user):
        if not worker_login_active(user):
            raise HTTPException(
                status_code=403,
                detail="Zugang gesperrt. Bitte den Geschäftsführer kontaktieren.",
            )
        if not verify_password(body.password, user):
            raise HTTPException(status_code=401, detail="Ungültige Zugangsdaten")
        if not _effective_license_active(user):
            raise HTTPException(status_code=403, detail=LICENSE_SUSPENDED_DETAIL)
        return {
            "access_token": user["id"],
            "token_type": "bearer",
            "user_id": user["id"],
            **_auth_session_fields(user),
            "mail": {"configured": bool(owner_email_for_smtp(users, user))},
        }

    email_norm = str(user.get("email") or "").strip().lower()
    local_pw_ok = verify_password(body.password, user)

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
        _persist_user_password(email_norm, body.password)
        return {
            "access_token": user["id"],
            "token_type": "bearer",
            "user_id": user["id"],
            **_auth_session_fields(user),
            "mail": {
                "configured": True,
                "host": smtp_status.get("host"),
                "port": smtp_status.get("port"),
                "source": smtp_status.get("source"),
                "synced_password": True,
            },
        }

    # Lokales Passwort stimmt. Legacy-Klartext bei Bedarf migrieren.
    _migrate_user_password_if_needed(email_norm, body.password)

    # SMTP wird best-effort verifiziert/aktualisiert -
    # ein Fehler hier blockiert den App-Login NICHT, damit der User auch offline
    # oder bei kurzzeitigen Provider-Problemen weiterarbeiten kann.
    smtp_status = _verify_and_store_smtp(email_norm, body.password)
    return {
        "access_token": user["id"],
        "token_type": "bearer",
        "user_id": user["id"],
        **_auth_session_fields(user),
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


@app.get("/api/auth/session")
def auth_session(user_id: str = Depends(require_bearer)):
    """Aktueller Lizenz-/Admin-Status (Token = User-ID). Für Frontend-Sync nach Reaktivierung."""
    user = find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Ungültiges Token")
    return {"ok": True, **_auth_session_fields(user)}


# --- Admin (M3): Account-Metadaten, keine Mandantendaten ---
class AdminLicenseBody(BaseModel):
    licenseActive: bool


@app.get("/api/admin/users")
def admin_list_users(_admin_id: str = Depends(require_admin)):
    return {"users": list_users_public(get_users())}


@app.patch("/api/admin/users/{target_user_id}/license")
def admin_set_user_license(
    target_user_id: str,
    body: AdminLicenseBody,
    admin_id: str = Depends(require_admin),
):
    if target_user_id == admin_id and not body.licenseActive:
        raise HTTPException(
            status_code=400,
            detail="Der eigene Administrator-Zugang kann nicht pausiert werden.",
        )
    users = get_users()
    updated = set_user_license(users, target_user_id, body.licenseActive)
    if updated is None:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    save_users(users)
    return {"ok": True, "user": updated}


@app.delete("/api/admin/users/{target_user_id}")
def admin_delete_user(target_user_id: str, admin_id: str = Depends(require_admin)):
    if target_user_id == admin_id:
        raise HTTPException(
            status_code=400,
            detail="Der eigene Administrator-Account kann nicht gelöscht werden.",
        )
    if not delete_user_account(read_users=get_users, save_users=save_users, user_id=target_user_id):
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    return {"ok": True}


@app.get("/api/company-profile")
def get_company_profile(store: TenantStore = Depends(get_tenant_store)):
    return _company_profile_response(store)


@app.post("/api/company-profile")
def post_company_profile(
    body: CompanyProfileBody,
    _owner_id: str = Depends(require_company_owner),
    store: TenantStore = Depends(get_tenant_store_write),
):
    _validate_company_profile_body(body)
    existing_raw = store.read_json("company_profile.json", {})
    existing = _normalize_company_profile(existing_raw if isinstance(existing_raw, dict) else {})
    payload = body.model_dump()
    payload["defaultExportFormat"] = payload["defaultExportFormat"].strip()
    if not payload.get("defaultRecipientEmail", "").strip():
        payload["defaultRecipientEmail"] = payload["officeEmail"].strip()
    merged = {**existing, **payload}
    # logoFilename kommt nicht aus dem Profil-Formular (separater Upload-Endpoint).
    # Bestehenden Dateinamen bewahren, damit ein vorher hochgeladenes Logo nicht verloren geht.
    if existing.get("logoFilename"):
        merged["logoFilename"] = existing["logoFilename"]
    try:
        store.write_json("company_profile.json", merged)
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail="Profil konnte nicht gespeichert werden. Bitte Schreibrechte für backend/data/tenants/ auf dem Server prüfen.",
        ) from exc
    return _company_profile_response(store)


@app.post("/api/company-logo")
async def upload_logo(
    file: UploadFile = File(...),
    _owner_id: str = Depends(require_company_owner),
    store: TenantStore = Depends(get_tenant_store_write),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Keine Datei")

    ext = Path(file.filename).suffix.lower()
    if ext not in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}:
        raise HTTPException(status_code=400, detail="Nur Bilddateien erlaubt")

    new_name = f"{uuid.uuid4().hex}{ext}"
    logos_dir = store.uploads_dir("logos")
    dest = logos_dir / new_name
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Datei zu groß (max. 5 MB)")
    content = normalize_logo_bytes(content, ext)
    dest.write_bytes(content)

    prof = store.read_json("company_profile.json", {})
    old = prof.get("logoFilename")
    if old:
        for old_path in (logos_dir / old, UPLOADS_DIR / old):
            if old_path.exists():
                try:
                    old_path.unlink()
                except OSError:
                    pass
    prof["logoFilename"] = new_name
    store.write_json("company_profile.json", prof)
    return {"logoFilename": new_name, "logoUrl": _logo_public_url(store, new_name)}


@app.post("/api/audio/upload")
async def upload_audio(
    file: UploadFile = File(...),
    reportDraftId: str | None = Form(default=None),
    projectId: str | None = Form(default=None),
    date: str | None = Form(default=None),
    store: TenantStore = Depends(get_tenant_store_write),
):
    """Audio-Rohtrack speichern; Transkription separat unter /api/audio/{id}/transcribe."""
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
    dest = store.uploads_dir("audio") / safe_name
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

    uploads = list(_get_audio_uploads_list(store))
    uploads.append(rec)
    _save_audio_uploads_list(store, uploads)

    return {
        "ok": True,
        "audioId": aid,
        "filename": safe_name,
        "message": "Audio wurde gespeichert. Transkription folgt im nächsten Schritt.",
    }


def _resolve_audio_upload_path(store: TenantStore, rec: dict[str, Any]) -> Path:
    fn = rec.get("filename")
    if not isinstance(fn, str) or not fn or "/" in fn or "\\" in fn or fn.strip() != fn:
        raise HTTPException(status_code=400, detail="Ungültiger Audiodateiname")
    path = store.resolve_upload_file("audio", fn)
    if path is None:
        base = AUDIO_UPLOAD_DIR.resolve()
        legacy = (AUDIO_UPLOAD_DIR / fn).resolve()
        try:
            legacy.relative_to(base)
        except ValueError:
            raise HTTPException(status_code=404, detail="Audiodatei nicht gefunden")
        if not legacy.is_file():
            raise HTTPException(status_code=404, detail="Audiodatei nicht gefunden")
        return legacy
    return path


@app.post("/api/audio/{audio_id}/transcribe")
def transcribe_stored_audio(audio_id: str, store: TenantStore = Depends(get_tenant_store_write)):
    """Transkription eines zuvor hochgeladenen Tracks (V1: Dummy-Text)."""
    uploads = _get_audio_uploads_list(store)
    rec = next((u for u in uploads if isinstance(u, dict) and str(u.get("id")) == audio_id), None)
    if not rec:
        raise HTTPException(status_code=404, detail="Audio nicht gefunden")
    path = _resolve_audio_upload_path(store, rec)
    text = transcribe_audio(str(path))
    return {"ok": True, "audioId": audio_id, "transcript": text}


@app.get("/api/audio/uploads")
def list_audio_uploads(store: TenantStore = Depends(get_tenant_store)):
    """Chronologie der gespeicherten Audio-Tracks (JSON-Liste)."""
    uploads = list(_get_audio_uploads_list(store))
    uploads_sorted = sorted(uploads, key=lambda x: str(x.get("createdAt", "")), reverse=True)
    return {"uploads": uploads_sorted}


@app.get("/api/employees")
def list_employees(
    user_id: str = Depends(require_active_license),
    store: TenantStore = Depends(get_tenant_store),
):
    data = store.read_json("employees.json", {"employees": []})
    employees = list(data.get("employees") or [])
    users = get_users()
    tid = store.tenant_id
    enriched = []
    for emp in employees:
        if not isinstance(emp, dict):
            continue
        row = dict(emp)
        worker = find_worker_for_employee(users, tid, str(emp.get("id") or ""))
        access = access_public_view(worker)
        row["access"] = access if access else {"hasAccess": False, "loginActive": False, "permissions": []}
        enriched.append(row)
    return {"employees": enriched}


@app.post("/api/employees")
def create_employee(
    body: EmployeeCreate,
    _owner_id: str = Depends(require_company_owner),
    store: TenantStore = Depends(get_tenant_store_write),
):
    data = store.read_json("employees.json", {"employees": []})
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
    store.write_json("employees.json", data)
    emp_out = dict(emp)
    emp_out["access"] = {"hasAccess": False, "loginActive": False, "permissions": []}
    return emp_out


@app.patch("/api/employees/{employee_id}")
def patch_employee(
    employee_id: str,
    body: EmployeePatch,
    _owner_id: str = Depends(require_company_owner),
    store: TenantStore = Depends(get_tenant_store_write),
):
    data = store.read_json("employees.json", {"employees": []})
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
            store.write_json("employees.json", data)
            # Anzeigename am Worker-Login mitziehen (nur displayName, Login-Username unverändert).
            users = get_users()
            worker = find_worker_for_employee(users, store.tenant_id, employee_id)
            if worker and body.name is not None:
                worker["displayName"] = str(body.name).strip()
                save_users(users)
            out = dict(e)
            out["access"] = access_public_view(worker) or {
                "hasAccess": False,
                "loginActive": False,
                "permissions": [],
            }
            return out
    raise HTTPException(status_code=404, detail="Mitarbeiter nicht gefunden")


@app.delete("/api/employees/{employee_id}")
def delete_employee(
    employee_id: str,
    _owner_id: str = Depends(require_company_owner),
    store: TenantStore = Depends(get_tenant_store_write),
):
    """Entfernt einen Mitarbeiter dauerhaft (z. B. bei Kündigung).

    Additiv: bereits gespeicherte Tagesberichte/Stunden bleiben unverändert erhalten,
    da sie die Namen selbst tragen. Es wird nur der Stammdaten-Eintrag entfernt.
    Zugehöriger App-Zugang wird gesperrt/entfernt.
    """
    data = store.read_json("employees.json", {"employees": []})
    employees_list = list(data.get("employees", []))
    target = next((r for r in employees_list if r.get("id") == employee_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Mitarbeiter nicht gefunden")
    data["employees"] = [r for r in employees_list if r.get("id") != employee_id]
    store.write_json("employees.json", data)

    users = get_users()
    worker = find_worker_for_employee(users, store.tenant_id, employee_id)
    if worker:
        users = [u for u in users if str(u.get("id") or "") != str(worker.get("id") or "")]
        save_users(users)
    return {"ok": True}


@app.post("/api/employees/{employee_id}/access")
def create_employee_access(
    employee_id: str,
    body: EmployeeAccessBody,
    owner_id: str = Depends(require_company_owner),
    store: TenantStore = Depends(get_tenant_store_write),
):
    """Zugang erstellen für bestehenden Mitarbeiter (Username + Passwort, firma-eindeutig)."""
    data = store.read_json("employees.json", {"employees": []})
    emp = next((e for e in data.get("employees", []) if e.get("id") == employee_id), None)
    if emp is None:
        raise HTTPException(status_code=404, detail="Mitarbeiter nicht gefunden")

    username = normalize_username(body.username)
    if not username or "@" in username:
        raise HTTPException(status_code=400, detail="Benutzername ungültig (kein E-Mail-Format).")
    if not re.fullmatch(r"[a-z0-9._-]{2,64}", username):
        raise HTTPException(
            status_code=400,
            detail="Benutzername: nur Kleinbuchstaben, Zahlen, Punkt, Unterstrich, Bindestrich.",
        )

    users = get_users()
    tid = store.tenant_id
    existing = find_worker_for_employee(users, tid, employee_id)
    if existing:
        raise HTTPException(status_code=400, detail="Für diesen Mitarbeiter existiert bereits ein Zugang.")
    if username_taken_in_tenant(users, tid, username):
        raise HTTPException(status_code=400, detail="Benutzername in dieser Firma bereits vergeben.")

    owner = find_user_by_id(owner_id) or find_tenant_owner(users, tid)
    worker = {
        "id": str(uuid.uuid4()),
        "tenantId": tid,
        "accountRole": "worker",
        "employeeId": employee_id,
        "username": username,
        "displayName": str(emp.get("name") or username),
        "companyName": str((owner or {}).get("companyName") or ""),
        "passwordHash": hash_password(body.password),
        "permissions": normalize_permissions(body.permissions),
        "loginActive": bool(body.loginActive),
        "licenseActive": True,
        "isAdmin": False,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    users.append(worker)
    save_users(users)
    return {"ok": True, "access": access_public_view(worker)}


@app.patch("/api/employees/{employee_id}/access")
def patch_employee_access(
    employee_id: str,
    body: EmployeeAccessPatchBody,
    _owner_id: str = Depends(require_company_owner),
    store: TenantStore = Depends(get_tenant_store_write),
):
    users = get_users()
    tid = store.tenant_id
    worker = find_worker_for_employee(users, tid, employee_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Kein Zugang für diesen Mitarbeiter.")

    if body.username is not None:
        username = normalize_username(body.username)
        if not username or "@" in username:
            raise HTTPException(status_code=400, detail="Benutzername ungültig (kein E-Mail-Format).")
        if not re.fullmatch(r"[a-z0-9._-]{2,64}", username):
            raise HTTPException(
                status_code=400,
                detail="Benutzername: nur Kleinbuchstaben, Zahlen, Punkt, Unterstrich, Bindestrich.",
            )
        if username_taken_in_tenant(users, tid, username, exclude_user_id=str(worker.get("id") or "")):
            raise HTTPException(status_code=400, detail="Benutzername in dieser Firma bereits vergeben.")
        worker["username"] = username

    if body.password is not None:
        apply_password_hash_to_user(worker, body.password)
    if body.permissions is not None:
        worker["permissions"] = normalize_permissions(body.permissions)
    if body.loginActive is not None:
        worker["loginActive"] = bool(body.loginActive)

    save_users(users)
    return {"ok": True, "access": access_public_view(worker)}


@app.get("/api/time-entries")
def list_time_entries_endpoint(
    employeeId: str | None = None,
    month: str | None = None,
    _perm: str = Depends(require_permission("time_accounts")),
    store: TenantStore = Depends(get_tenant_store),
):
    entries = time_account.list_time_entries(
        read_json=store.time_account_read_json,
        employee_id=employeeId,
        month=month,
    )
    return {"entries": entries, "count": len(entries)}


@app.post("/api/time-entries")
def create_time_entry_endpoint(body: TimeEntryCreate, store: TenantStore = Depends(get_tenant_store_write)):
    employees_data = store.read_json("employees.json", {"employees": []})
    try:
        entry = time_account.create_manual_time_entry(
            employee_id=body.employeeId,
            date_str=body.date,
            hours=body.hours,
            note=body.note,
            employees=list(employees_data.get("employees") or []),
            read_json=store.time_account_read_json,
            write_json=store.time_account_write_json,
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
def delete_time_entry_endpoint(entry_id: str, store: TenantStore = Depends(get_tenant_store_write)):
    removed = time_account.delete_time_entry(
        entry_id,
        read_json=store.time_account_read_json,
        write_json=store.time_account_write_json,
    )
    if not removed:
        raise HTTPException(status_code=404, detail="Buchung nicht gefunden")
    return {"ok": True}


@app.get("/api/time-accounts")
def list_time_accounts_endpoint(
    month: str | None = None,
    _perm: str = Depends(require_permission("time_accounts")),
    store: TenantStore = Depends(get_tenant_store),
):
    employees_data = store.read_json("employees.json", {"employees": []})
    return time_account.list_time_accounts(
        list(employees_data.get("employees") or []),
        read_json=store.time_account_read_json,
        month=month,
    )


def _time_export_payload(store: TenantStore, month: str | None) -> dict[str, Any]:
    month_prefix = str(month or datetime.now(timezone.utc).strftime("%Y-%m")).strip()[:7]
    if not re.match(r"^\d{4}-\d{2}$", month_prefix):
        raise HTTPException(status_code=400, detail="Ungültiger Monat (YYYY-MM)")

    employees = list(store.read_json("employees.json", {"employees": []}).get("employees") or [])
    entries = time_account.list_time_entries(read_json=store.time_account_read_json, month=month_prefix)
    reports_data = store.read_json("reports.json", {"reports": []})
    reports_by_id = {
        str(r.get("id") or ""): r for r in (reports_data.get("reports") or []) if isinstance(r, dict) and r.get("id")
    }
    entries = time_account.enrich_entries_for_export(entries, reports_by_id)
    accounts_doc = time_account.list_time_accounts(employees, read_json=store.time_account_read_json, month=month_prefix)
    company = store.read_json("company_profile.json", {})
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
    store: TenantStore = Depends(get_tenant_store),
):
    payload = _time_export_payload(store, month)
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
    store: TenantStore = Depends(get_tenant_store),
):
    payload = _time_export_payload(store, month)
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
def list_projects(store: TenantStore = Depends(get_tenant_store)):
    return store.read_json("projects.json", {"projects": []})


@app.post("/api/projects")
def create_project(
    body: ProjectCreate,
    _perm: str = Depends(require_permission("projects")),
    store: TenantStore = Depends(get_tenant_store_write),
):
    data = store.read_json("projects.json", {"projects": []})
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
    store.write_json("projects.json", data)
    return proj


@app.patch("/api/projects/{project_id}")
def patch_project(
    project_id: str,
    body: ProjectPatch,
    _perm: str = Depends(require_permission("projects")),
    store: TenantStore = Depends(get_tenant_store_write),
):
    data = store.read_json("projects.json", {"projects": []})
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
            store.write_json("projects.json", data)
            return p
    raise HTTPException(status_code=404, detail="Baustelle nicht gefunden")


@app.delete("/api/projects/{project_id}")
def delete_project(
    project_id: str,
    _perm: str = Depends(require_permission("projects")),
    store: TenantStore = Depends(get_tenant_store_write),
):
    """Entfernt eine Baustelle dauerhaft aus der Liste.

    Additiv: vorhandene Tagesberichte dieser Baustelle bleiben unter „Berichte"
    erhalten (sie tragen ihre Daten selbst). Es wird nur der Projekteintrag entfernt.
    """
    data = store.read_json("projects.json", {"projects": []})
    projects_list = list(data.get("projects", []))
    target = next((p for p in projects_list if p.get("id") == project_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Baustelle nicht gefunden")
    data["projects"] = [p for p in projects_list if p.get("id") != project_id]
    store.write_json("projects.json", data)
    return {"ok": True}


def _assign_series_run(store: TenantStore, project_id: str) -> str | None:
    """Ordnet einen Folgebericht dem laufenden Durchlauf der Baustelle zu.

    Legt bei Bedarf einen neuen Durchlauf an (additiv auf dem Projekt). Existiert die
    Baustelle nicht, wird None zurueckgegeben (Bericht bleibt dann ohne runId).
    """
    data = store.read_json("projects.json", {"projects": []})
    now_iso = datetime.now(timezone.utc).isoformat()
    for p in data.get("projects", []):
        if p.get("id") == project_id:
            run_id = collective.ensure_open_run(p, now_iso=now_iso, new_run_id=str(uuid.uuid4()))
            store.write_json("projects.json", data)
            return run_id
    return None


@app.post("/api/projects/{project_id}/close-run")
def close_project_run(project_id: str, store: TenantStore = Depends(get_tenant_store_write)):
    """Schliesst den laufenden Durchlauf einer Baustelle (Status -> abgeschlossen)."""
    data = store.read_json("projects.json", {"projects": []})
    now_iso = datetime.now(timezone.utc).isoformat()
    for p in data.get("projects", []):
        if p.get("id") == project_id:
            info = collective.close_run(p, now_iso=now_iso)
            store.write_json("projects.json", data)
            return {"ok": True, "project": p, **info}
    raise HTTPException(status_code=404, detail="Baustelle nicht gefunden")


def _build_collective(store: TenantStore, project_id: str, run_id: str | None) -> dict[str, Any]:
    projects = store.read_json("projects.json", {"projects": []}).get("projects", [])
    project = next((p for p in projects if p.get("id") == project_id), None)
    if project is None:
        raise HTTPException(status_code=404, detail="Baustelle nicht gefunden")
    resolved_run = collective.resolve_run_id(project, run_id)
    reports = list(store.read_json("reports.json", {"reports": []}).get("reports", []))
    payload = collective.build_collective_payload(project, reports, run_id=resolved_run)
    # Foto-URLs mandantenspezifisch aufloesen.
    for ph in payload.get("photos", []):
        fn = ph.get("filename")
        if isinstance(fn, str) and fn:
            ph["url"] = _photo_public_url(store, fn)
    # Gesamt-Zusammenfassung natuerlich UND ueber alle Tage kombiniert formulieren
    # (nur aus geprueften Daten; ohne KI bleibt die deterministische Kombi-Summary).
    try:
        polished = polish_collective_summary_with_ai(payload, str(payload.get("summary") or ""))
        if polished:
            payload["summary"] = polished
    except Exception:
        pass
    return payload


def _build_collective_protocol(store: TenantStore, project_id: str) -> dict[str, Any]:
    projects = store.read_json("projects.json", {"projects": []}).get("projects", [])
    project = next((p for p in projects if p.get("id") == project_id), None)
    if project is None:
        raise HTTPException(status_code=404, detail="Baustelle nicht gefunden")
    protocols = read_protocols(store)
    payload = collective_proto.build_collective_protocol_payload(project, protocols)
    if not payload.get("entries"):
        raise HTTPException(status_code=400, detail="Keine Begehungsprotokolle für diese Baustelle vorhanden.")
    return payload


@app.get("/api/projects/{project_id}/collective-protocol")
def get_collective_protocol(project_id: str, store: TenantStore = Depends(get_tenant_store)):
    return _build_collective_protocol(store, project_id)


@app.get("/api/projects/{project_id}/collective-protocol/export/pdf")
def export_collective_protocol_pdf(
    project_id: str,
    store: TenantStore = Depends(get_tenant_store),
):
    payload = _build_collective_protocol(store, project_id)
    prof = store.read_json("company_profile.json", {})
    try:
        blob = build_collective_protocol_pdf_bytes(
            payload,
            prof,
            resolve_logo=_export_resolve_logo(store),
            resolve_signature=_export_resolve_signature(store),
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Gesamtprotokoll-Export konnte nicht erstellt werden.")
    ascii_fn, desc_fn = build_collective_protocol_attachment_names(payload, "pdf")
    return Response(
        content=blob,
        media_type="application/pdf",
        headers={"Content-Disposition": _content_disposition_attachment(ascii_fn, desc_fn)},
    )


@app.get("/api/projects/{project_id}/collective-report")
def get_collective_report(
    project_id: str,
    runId: str | None = None,
    store: TenantStore = Depends(get_tenant_store),
):
    return _build_collective(store, project_id, runId)


def _export_resolve_photo(store: TenantStore):
    def resolve(filename: str) -> Path | None:
        path = store.resolve_upload_file("photos", filename)
        if path is not None:
            return path
        legacy = PHOTOS_UPLOAD_DIR / filename
        return legacy if legacy.is_file() else None

    return resolve


@app.get("/api/projects/{project_id}/collective-report/export/pdf")
def export_collective_pdf(
    project_id: str,
    runId: str | None = None,
    store: TenantStore = Depends(get_tenant_store),
):
    payload = _build_collective(store, project_id, runId)
    prof = store.read_json("company_profile.json", {})
    try:
        blob = build_collective_pdf_bytes(
            payload,
            prof,
            resolve_logo=_export_resolve_logo(store),
            resolve_photo=_export_resolve_photo(store),
            resolve_signature=_export_resolve_signature(store),
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Gesamtbericht-Export konnte nicht erstellt werden.")
    ascii_fn, desc_fn = build_collective_attachment_names(payload, "pdf")
    return Response(
        content=blob,
        media_type="application/pdf",
        headers={"Content-Disposition": _content_disposition_attachment(ascii_fn, desc_fn)},
    )


@app.get("/api/projects/{project_id}/collective-report/export/word")
def export_collective_word(
    project_id: str,
    runId: str | None = None,
    store: TenantStore = Depends(get_tenant_store),
):
    payload = _build_collective(store, project_id, runId)
    prof = store.read_json("company_profile.json", {})
    try:
        blob = build_collective_docx_bytes(
            payload,
            prof,
            resolve_logo=_export_resolve_logo(store),
            resolve_photo=_export_resolve_photo(store),
            resolve_signature=_export_resolve_signature(store),
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Gesamtbericht-Export konnte nicht erstellt werden.")
    ascii_fn, desc_fn = build_collective_attachment_names(payload, "docx")
    return Response(
        content=blob,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": _content_disposition_attachment(ascii_fn, desc_fn)},
    )


def _ai_structuring_enabled() -> bool:
    """Opt-in-Schalter fuer die KI-Strukturierung der Taetigkeiten/Materialien.

    Standard: AUS. Damit bleibt die Strukturierung rein deterministisch (wie in
    allen Tests abgesichert), auch wenn ein OPENAI_API_KEY gesetzt ist. Der Key
    aktiviert dann ausschliesslich die natuerlichere Zusammenfassung (Hebel 1).
    Zum bewussten Einschalten: FREIRAUM_AI_STRUCTURING=1 (bzw. true/yes/on).
    """
    flag = (os.environ.get("FREIRAUM_AI_STRUCTURING") or "").strip().casefold()
    return flag in {"1", "true", "yes", "on"}


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
    summary = str(result.get("summary") or "").strip() or "Keine Angabe"
    try:
        from app.services.summary_material_guard import strip_material_echo_from_summary

        summary = strip_material_echo_from_summary(
            summary,
            result["materials"],
            result["activities"],
        )
    except Exception:
        pass
    result["summary"] = summary.strip() or "Keine Angabe"
    result["customerTalk"] = str(result.get("customerTalk") or "").strip() or "Keine Angabe"
    return result


@app.post("/api/structure-report")
def api_structure_report(body: StructureReportBody, store: TenantStore = Depends(get_tenant_store_write)):
    prof = store.read_json("company_profile.json", {})
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

    ai_try = (
        structure_report_with_ai(
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
        if _ai_structuring_enabled()
        else None
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

    # Hebel 1: Zusammenfassung natuerlicher formulieren — ausschliesslich aus den
    # bereits geprueften Daten. Ohne Key/bei Fehler bleibt die deterministische
    # Zusammenfassung erhalten (kein Bestehendes wird veraendert).
    try:
        polished_summary = polish_summary_with_ai(
            structured_dict,
            {"date": body.date, "projectName": body.projectName},
        )
        if polished_summary:
            structured_dict["summary"] = polished_summary
    except Exception:
        pass

    # Hebel 3: Kundengespraech natuerlicher formulieren — nur aus isoliertem Inhalt.
    try:
        polished_customer = polish_customer_talk_with_ai(
            structured_dict,
            raw_text=body.rawText,
        )
        if polished_customer:
            structured_dict["customerTalk"] = polished_customer
    except Exception:
        pass

    # Hebel 4: Probleme und offene Punkte natuerlicher formulieren — nur isolierter Inhalt.
    try:
        polished_problem_open = polish_problem_open_with_ai(
            structured_dict,
            raw_text=body.rawText,
        )
        if polished_problem_open:
            if polished_problem_open.get("problems") is not None:
                structured_dict["problems"] = polished_problem_open["problems"]
            if polished_problem_open.get("openItems") is not None:
                structured_dict["openItems"] = polished_problem_open["openItems"]
    except Exception:
        pass

    structured_dict = _ensure_clean_structured_final(structured_dict)

    # Hebel 2: nicht erkannte Saetze mandantenspezifisch protokollieren (best-effort,
    # beeinflusst die Ausgabe nicht).
    try:
        unmatched = collect_unmatched_chunks(body.rawText)
        if unmatched:
            record_unmatched_speech(
                store,
                raw_text=body.rawText,
                unmatched=unmatched,
                meta={"projectId": body.projectId, "date": body.date},
            )
    except Exception:
        pass

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
    _perm: str = Depends(require_permission("reports_list")),
    store: TenantStore = Depends(get_tenant_store),
):
    data = store.read_json("reports.json", {"reports": []})
    reports = list(data.get("reports", []))
    reports.sort(key=lambda r: r.get("createdAt", ""), reverse=True)

    if projectId:
        reports = [r for r in reports if r.get("projectId") == projectId]
    if month and len(month) >= 7:
        prefix = month[:7]
        reports = [r for r in reports if str(r.get("date", "")).startswith(prefix)]

    return {"reports": reports}


@app.post("/api/reports")
def create_report(body: ReportCreateBody, store: TenantStore = Depends(get_tenant_store_write)):
    prof = store.read_json("company_profile.json", {})
    logo_fn = prof.get("logoFilename")
    company_logo_url = _logo_public_url(store, logo_fn) if logo_fn else None
    if logo_fn and not company_logo_url:
        legacy_logo = UPLOADS_DIR / str(logo_fn)
        if legacy_logo.is_file():
            company_logo_url = f"/uploads/logos/{logo_fn}"
    if body.companyLogoUrl:
        company_logo_url = body.companyLogoUrl

    rid = str(uuid.uuid4())
    # Folgebericht: dem laufenden Durchlauf der Baustelle zuordnen (legt bei Bedarf
    # einen neuen Durchlauf an). Einzelbericht (Standard) bleibt ohne runId -> exakt
    # bisheriges Verhalten.
    run_id: str | None = None
    if body.seriesMode and body.projectId:
        run_id = _assign_series_run(store, body.projectId)
    doc = {
        "id": rid,
        "companyId": store.tenant_id,
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
        "notes": str(body.notes or "").strip(),
        "runId": run_id,
        "photos": [],
        "signatures": {"customer": None, "employee": None},
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    _write_json_reports(store, doc)
    employees_data = store.read_json("employees.json", {"employees": []})
    doc["timeBooking"] = time_account.sync_entries_for_report(
        doc,
        list(employees_data.get("employees") or []),
        read_json=store.time_account_read_json,
        write_json=store.time_account_write_json,
    )
    return doc


@app.put("/api/reports/{report_id}")
def update_report(
    report_id: str,
    body: ReportCreateBody,
    store: TenantStore = Depends(get_tenant_store_write),
):
    """Bestehenden Bericht aktualisieren — Fotos/Unterschriften/runId bleiben erhalten."""
    data = store.read_json("reports.json", {"reports": []})
    reports_list = list(data.get("reports", []))
    idx = next((i for i, r in enumerate(reports_list) if r.get("id") == report_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Bericht nicht gefunden")
    existing = dict(reports_list[idx])

    prof = store.read_json("company_profile.json", {})
    logo_fn = prof.get("logoFilename")
    company_logo_url = existing.get("companyLogoUrl")
    if logo_fn:
        resolved = _logo_public_url(store, logo_fn)
        if resolved:
            company_logo_url = resolved
        else:
            legacy_logo = UPLOADS_DIR / str(logo_fn)
            if legacy_logo.is_file():
                company_logo_url = f"/uploads/logos/{logo_fn}"
    if body.companyLogoUrl:
        company_logo_url = body.companyLogoUrl

    existing.update(
        {
            "companyName": body.companyName,
            "companyLogoUrl": company_logo_url,
            "officeEmail": body.officeEmail or prof.get("officeEmail", "") or existing.get("officeEmail", ""),
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
            "notes": str(body.notes or "").strip(),
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        }
    )
    # Fotos, Signaturen, createdAt, runId, id, companyId bewusst unangetastet.
    reports_list[idx] = existing
    data["reports"] = reports_list
    store.write_json("reports.json", data)

    employees_data = store.read_json("employees.json", {"employees": []})
    existing["timeBooking"] = time_account.sync_entries_for_report(
        existing,
        list(employees_data.get("employees") or []),
        read_json=store.time_account_read_json,
        write_json=store.time_account_write_json,
    )
    return existing


def _write_json_reports(store: TenantStore, new_report: dict) -> None:
    data = store.read_json("reports.json", {"reports": []})
    data.setdefault("reports", []).append(new_report)
    store.write_json("reports.json", data)


def _find_report_doc(store: TenantStore, report_id: str) -> dict[str, Any]:
    data = store.read_json("reports.json", {"reports": []})
    for r in data.get("reports", []):
        if r.get("id") == report_id:
            return r
    raise HTTPException(status_code=404, detail="Bericht nicht gefunden")


def _report_photos_list(report: dict[str, Any]) -> list[dict[str, Any]]:
    raw = report.get("photos")
    if not isinstance(raw, list):
        return []
    return [p for p in raw if isinstance(p, dict)]


def _photo_public_url(store: TenantStore, filename: str) -> str:
    return f"/uploads/tenants/{store.tenant_id}/photos/{filename}"


def _photo_api_item(store: TenantStore, entry: dict[str, Any]) -> dict[str, Any]:
    fn = str(entry.get("filename") or "")
    url = None
    if fn:
        url = _photo_public_url(store, fn)
        if not store.resolve_upload_file("photos", fn):
            legacy = PHOTOS_UPLOAD_DIR / fn
            if legacy.is_file():
                url = f"/uploads/photos/{fn}"
    return {
        "id": entry.get("id"),
        "filename": fn,
        "originalFilename": entry.get("originalFilename"),
        "contentType": entry.get("contentType"),
        "sizeBytes": entry.get("sizeBytes"),
        "uploadedAt": entry.get("uploadedAt"),
        "url": url,
    }


def _resolve_photo_path(store: TenantStore, filename: str) -> Path:
    fn = str(filename or "")
    if not fn or "/" in fn or "\\" in fn or fn.strip() != fn:
        raise HTTPException(status_code=400, detail="Ungültiger Fotodateiname")
    path = store.resolve_upload_file("photos", fn)
    if path is not None:
        return path
    base = PHOTOS_UPLOAD_DIR.resolve()
    legacy = (PHOTOS_UPLOAD_DIR / fn).resolve()
    try:
        legacy.relative_to(base)
    except ValueError:
        raise HTTPException(status_code=404, detail="Foto nicht gefunden")
    if not legacy.is_file():
        raise HTTPException(status_code=404, detail="Foto nicht gefunden")
    return legacy


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


def _save_report_photos(store: TenantStore, report_id: str, photos: list[dict[str, Any]]) -> None:
    data = store.read_json("reports.json", {"reports": []})
    for r in data.get("reports", []):
        if r.get("id") == report_id:
            r["photos"] = photos
            store.write_json("reports.json", data)
            return
    raise HTTPException(status_code=404, detail="Bericht nicht gefunden")


def _delete_report_photo_files(store: TenantStore, report: dict[str, Any]) -> None:
    for entry in _report_photos_list(report):
        fn = entry.get("filename")
        if not isinstance(fn, str) or not fn:
            continue
        try:
            path = _resolve_photo_path(store, fn)
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


def _signature_public_url(store: TenantStore, filename: str) -> str:
    return f"/uploads/tenants/{store.tenant_id}/signatures/{filename}"


def _signature_api_item(store: TenantStore, role: str, entry: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(entry, dict):
        return None
    fn = str(entry.get("filename") or "")
    if not fn:
        return None
    url = _signature_public_url(store, fn)
    if not store.resolve_upload_file("signatures", fn):
        legacy = SIGNATURES_UPLOAD_DIR / fn
        if legacy.is_file():
            url = f"/uploads/signatures/{fn}"
    return {
        "id": entry.get("id"),
        "role": role,
        "filename": fn,
        "contentType": entry.get("contentType"),
        "sizeBytes": entry.get("sizeBytes"),
        "signedAt": entry.get("signedAt"),
        "signedByLabel": entry.get("signedByLabel"),
        "url": url,
    }


def _resolve_signature_path(store: TenantStore, filename: str) -> Path:
    fn = str(filename or "")
    if not fn or "/" in fn or "\\" in fn or fn.strip() != fn:
        raise HTTPException(status_code=400, detail="Ungültiger Signaturdateiname")
    path = store.resolve_upload_file("signatures", fn)
    if path is not None:
        return path
    base = SIGNATURES_UPLOAD_DIR.resolve()
    legacy = (SIGNATURES_UPLOAD_DIR / fn).resolve()
    try:
        legacy.relative_to(base)
    except ValueError:
        raise HTTPException(status_code=404, detail="Signatur nicht gefunden")
    if not legacy.is_file():
        raise HTTPException(status_code=404, detail="Signatur nicht gefunden")
    return legacy


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


def _save_report_signatures(store: TenantStore, report_id: str, signatures: dict[str, Any]) -> None:
    data = store.read_json("reports.json", {"reports": []})
    for r in data.get("reports", []):
        if r.get("id") == report_id:
            r["signatures"] = signatures
            store.write_json("reports.json", data)
            return
    raise HTTPException(status_code=404, detail="Bericht nicht gefunden")


def _delete_signature_file(store: TenantStore, filename: str | None) -> None:
    if not isinstance(filename, str) or not filename:
        return
    try:
        _resolve_signature_path(store, filename).unlink(missing_ok=True)
    except HTTPException:
        pass
    except OSError:
        pass


def _delete_report_signature_files(store: TenantStore, report: dict[str, Any]) -> None:
    for entry in _report_signatures_doc(report).values():
        if isinstance(entry, dict):
            _delete_signature_file(store, entry.get("filename"))


def _content_disposition_attachment(ascii_filename: str, utf8_filename: str) -> str:
    enc = quote(utf8_filename, safe="")
    return f'attachment; filename="{ascii_filename}"; filename*=UTF-8\'\'{enc}'


@app.get("/api/reports/{report_id}")
def get_report(report_id: str, store: TenantStore = Depends(get_tenant_store)):
    return _find_report_doc(store, report_id)


@app.delete("/api/reports/{report_id}")
def delete_report(report_id: str, store: TenantStore = Depends(get_tenant_store_write)):
    data = store.read_json("reports.json", {"reports": []})
    reports_list = list(data.get("reports", []))
    target = next((r for r in reports_list if r.get("id") == report_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Bericht nicht gefunden")
    _delete_report_photo_files(store, target)
    _delete_report_signature_files(store, target)
    time_account.delete_entries_for_report(
        report_id,
        read_json=store.time_account_read_json,
        write_json=store.time_account_write_json,
    )
    next_list = [r for r in reports_list if r.get("id") != report_id]
    data["reports"] = next_list
    store.write_json("reports.json", data)
    return {"ok": True}


@app.get("/api/reports/{report_id}/photos")
def list_report_photos(report_id: str, store: TenantStore = Depends(get_tenant_store)):
    report = _find_report_doc(store, report_id)
    photos = [_photo_api_item(store, p) for p in _report_photos_list(report)]
    return {
        "photos": photos,
        "count": len(photos),
        "maxPhotos": MAX_PHOTOS_PER_REPORT,
    }


@app.post("/api/reports/{report_id}/photos")
async def upload_report_photo(
    report_id: str,
    file: UploadFile = File(...),
    store: TenantStore = Depends(get_tenant_store_write),
):
    """Baustellenfoto zu einem gespeicherten Tagesbericht hochladen (max. 10 pro Bericht)."""
    report = _find_report_doc(store, report_id)
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
    dest = store.uploads_dir("photos") / safe_name
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
    _save_report_photos(store, report_id, photos)

    return {
        "ok": True,
        "photo": _photo_api_item(store, entry),
        "count": len(photos),
        "maxPhotos": MAX_PHOTOS_PER_REPORT,
    }


@app.delete("/api/reports/{report_id}/photos/{photo_id}")
def delete_report_photo(
    report_id: str,
    photo_id: str,
    store: TenantStore = Depends(get_tenant_store_write),
):
    report = _find_report_doc(store, report_id)
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
            _resolve_photo_path(store, fn).unlink(missing_ok=True)
        except HTTPException:
            pass
        except OSError:
            pass

    _save_report_photos(store, report_id, kept)
    return {
        "ok": True,
        "count": len(kept),
        "maxPhotos": MAX_PHOTOS_PER_REPORT,
    }


def _signatures_api_payload(store: TenantStore, report: dict[str, Any]) -> dict[str, Any]:
    doc = _report_signatures_doc(report)
    return {
        role: _signature_api_item(store, role, doc.get(role))
        for role in sorted(SIGNATURE_ROLES)
    }


@app.get("/api/reports/{report_id}/signatures")
def list_report_signatures(report_id: str, store: TenantStore = Depends(get_tenant_store)):
    report = _find_report_doc(store, report_id)
    signatures = _signatures_api_payload(store, report)
    count = sum(1 for v in signatures.values() if v is not None)
    return {"signatures": signatures, "count": count}


@app.post("/api/reports/{report_id}/signatures/{role}")
async def upload_report_signature(
    report_id: str,
    role: str,
    file: UploadFile = File(...),
    signedByLabel: str | None = Form(None),
    store: TenantStore = Depends(get_tenant_store_write),
):
    """Unterschrift fuer Kunde oder Mitarbeiter speichern (PNG, max. eine pro Rolle)."""
    sig_role = _validate_signature_role(role)
    report = _find_report_doc(store, report_id)

    if not file.filename:
        raise HTTPException(status_code=400, detail="Keine Datei")

    content = await file.read()
    _validate_signature_png(content)

    signatures = _report_signatures_doc(report)
    previous = signatures.get(sig_role)
    if isinstance(previous, dict):
        _delete_signature_file(store, previous.get("filename"))

    sig_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    safe_name = f"sig_{ts}_{sig_role}_{sig_id}.png"
    dest = store.uploads_dir("signatures") / safe_name
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
    _save_report_signatures(store, report_id, signatures)

    item = _signature_api_item(store, sig_role, entry)
    count = sum(1 for v in signatures.values() if isinstance(v, dict))
    return {
        "ok": True,
        "signature": item,
        "signatures": _signatures_api_payload(store, {"signatures": signatures}),
        "count": count,
    }


@app.delete("/api/reports/{report_id}/signatures/{role}")
def delete_report_signature(
    report_id: str,
    role: str,
    store: TenantStore = Depends(get_tenant_store_write),
):
    sig_role = _validate_signature_role(role)
    report = _find_report_doc(store, report_id)
    signatures = _report_signatures_doc(report)
    previous = signatures.get(sig_role)
    if not isinstance(previous, dict):
        raise HTTPException(status_code=404, detail="Signatur nicht gefunden")

    _delete_signature_file(store, previous.get("filename"))
    signatures[sig_role] = None
    _save_report_signatures(store, report_id, signatures)
    count = sum(1 for v in signatures.values() if isinstance(v, dict))
    return {
        "ok": True,
        "signatures": _signatures_api_payload(store, {"signatures": signatures}),
        "count": count,
    }


class SendOfficeResponse(BaseModel):
    ok: bool
    simulated: bool
    message: str


@app.post("/api/reports/{report_id}/send-office", response_model=SendOfficeResponse)
def send_report_to_office_endpoint(
    report_id: str,
    user_id: str = Depends(require_active_license),
    store: TenantStore = Depends(get_tenant_store_write),
) -> SendOfficeResponse:
    rep = _find_report_doc(store, report_id)
    prof = store.read_json("company_profile.json", {})
    office = str(prof.get("officeEmail") or "").strip()
    if not office:
        raise HTTPException(
            status_code=400,
            detail="Keine Büro-E-Mail im Firmenprofil hinterlegt.",
        )

    sender_email = _smtp_sender_email_for_user_id(user_id)
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
        photos_upload_dir=store.uploads_dir("photos"),
        resolve_logo=_export_resolve_logo(store),
        resolve_signature=_export_resolve_signature(store),
    )
    if not ok:
        raise HTTPException(status_code=500, detail=message or "Bericht konnte nicht gesendet werden.")
    return SendOfficeResponse(ok=True, simulated=simulated, message=message)


@app.post("/api/projects/{project_id}/collective-report/send-office", response_model=SendOfficeResponse)
def send_collective_to_office_endpoint(
    project_id: str,
    runId: str | None = None,
    user_id: str = Depends(require_active_license),
    store: TenantStore = Depends(get_tenant_store_write),
) -> SendOfficeResponse:
    payload = _build_collective(store, project_id, runId)
    prof = store.read_json("company_profile.json", {})
    office = str(prof.get("officeEmail") or "").strip()
    if not office:
        raise HTTPException(status_code=400, detail="Keine Büro-E-Mail im Firmenprofil hinterlegt.")

    sender_email = _smtp_sender_email_for_user_id(user_id)
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

    ok, simulated, message = send_collective_to_office(
        payload,
        prof,
        office,
        mail_config=mail_config,
        photos_upload_dir=store.uploads_dir("photos"),
        resolve_logo=_export_resolve_logo(store),
        resolve_photo=_export_resolve_photo(store),
        resolve_signature=_export_resolve_signature(store),
    )
    if not ok:
        raise HTTPException(status_code=500, detail=message or "Gesamtbericht konnte nicht gesendet werden.")
    return SendOfficeResponse(ok=True, simulated=simulated, message=message)


@app.post("/api/projects/{project_id}/collective-protocol/send-office", response_model=SendOfficeResponse)
def send_collective_protocol_to_office_endpoint(
    project_id: str,
    user_id: str = Depends(require_active_license),
    store: TenantStore = Depends(get_tenant_store_write),
) -> SendOfficeResponse:
    payload = _build_collective_protocol(store, project_id)
    prof = store.read_json("company_profile.json", {})
    office = str(prof.get("officeEmail") or "").strip()
    if not office:
        raise HTTPException(status_code=400, detail="Keine Büro-E-Mail im Firmenprofil hinterlegt.")

    sender_email = _smtp_sender_email_for_user_id(user_id)
    if not sender_email:
        raise HTTPException(status_code=401, detail="Versand nicht möglich: Anmeldung nicht mehr gültig.")
    mail_config = get_mail_config(sender_email)
    if not mail_config:
        raise HTTPException(
            status_code=400,
            detail=(
                "Mail-Anbindung fehlt. Bitte einmal in der App ausloggen und "
                "wieder einloggen, damit die SMTP-Daten geprüft und gespeichert werden."
            ),
        )

    ok, simulated, message = send_collective_protocol_to_office(
        payload,
        prof,
        office,
        mail_config=mail_config,
        resolve_logo=_export_resolve_logo(store),
        resolve_signature=_export_resolve_signature(store),
    )
    if not ok:
        raise HTTPException(status_code=500, detail=message or "Gesamtprotokoll konnte nicht gesendet werden.")
    return SendOfficeResponse(ok=True, simulated=simulated, message=message)


def _export_resolve_logo(store: TenantStore):
    def resolve(_report: dict[str, Any], prof: dict[str, Any]) -> Path | None:
        logo_fn = str(prof.get("logoFilename") or "").strip()
        if logo_fn:
            return store.resolve_upload_file("logos", logo_fn)
        return None

    return resolve


def _export_resolve_signature(store: TenantStore):
    def resolve(filename: str) -> Path | None:
        return store.resolve_upload_file("signatures", filename)

    return resolve


@app.get("/api/reports/{report_id}/export/pdf")
def export_report_pdf(report_id: str, store: TenantStore = Depends(get_tenant_store)):
    rep = _find_report_doc(store, report_id)
    prof = store.read_json("company_profile.json", {})
    try:
        blob = build_pdf_bytes(
            rep,
            prof,
            resolve_logo=_export_resolve_logo(store),
            resolve_signature=_export_resolve_signature(store),
        )
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
def export_report_word(report_id: str, store: TenantStore = Depends(get_tenant_store)):
    rep = _find_report_doc(store, report_id)
    prof = store.read_json("company_profile.json", {})
    try:
        blob = build_docx_bytes(rep, prof, resolve_logo=_export_resolve_logo(store))
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


def _protocol_signatures_api_payload(store: TenantStore, protocol: dict[str, Any]) -> dict[str, Any]:
    doc = protocol_signatures_doc(protocol)
    return {
        "customer": _signature_api_item(store, "customer", doc.get("customer")),
        "employee": _signature_api_item(store, "employee", doc.get("employee")),
    }


@app.post("/api/protocols/polish-text")
def polish_protocol_text(body: ProtocolPolishBody) -> dict[str, Any]:
    polished = polish_protocol_transcript_with_ai(body.rawText)
    if polished:
        return {"polishedText": polished, "polishedBy": "openai"}
    return {"polishedText": body.rawText.strip(), "polishedBy": "local"}


@app.get("/api/protocols")
def list_protocols(
    projectId: str | None = None,
    month: str | None = None,
    store: TenantStore = Depends(get_tenant_store),
):
    protocols = read_protocols(store)
    protocols.sort(key=lambda p: p.get("createdAt", ""), reverse=True)
    if projectId:
        protocols = [p for p in protocols if p.get("projectId") == projectId]
    if month and len(month) >= 7:
        prefix = month[:7]
        protocols = [p for p in protocols if str(p.get("date", "")).startswith(prefix)]
    return {"protocols": protocols}


@app.post("/api/protocols")
def create_protocol(body: ProtocolCreateBody, store: TenantStore = Depends(get_tenant_store_write)):
    prof = store.read_json("company_profile.json", {})
    logo_fn = prof.get("logoFilename")
    company_logo_url = _logo_public_url(store, logo_fn) if logo_fn else None
    if logo_fn and not company_logo_url:
        legacy_logo = UPLOADS_DIR / str(logo_fn)
        if legacy_logo.is_file():
            company_logo_url = f"/uploads/logos/{logo_fn}"

    doc = create_protocol_doc(
        store,
        company_name=str(prof.get("companyName") or ""),
        company_logo_url=company_logo_url,
        office_email=str(prof.get("officeEmail") or ""),
        project_id=body.projectId,
        project_name=body.projectName,
        customer_name=body.customerName,
        date=body.date,
        mode=body.mode,
        raw_text=body.rawText,
        polished_text=body.polishedText or body.rawText,
        participants=body.participants,
        export_format=body.exportFormat,
    )
    return doc


@app.get("/api/protocols/{protocol_id}")
def get_protocol(protocol_id: str, store: TenantStore = Depends(get_tenant_store)):
    return find_protocol(store, protocol_id)


@app.delete("/api/protocols/{protocol_id}")
def delete_protocol(protocol_id: str, store: TenantStore = Depends(get_tenant_store_write)):
    def _del_photo(_store: TenantStore, filename: str) -> None:
        try:
            path = _resolve_photo_path(_store, filename)
            path.unlink(missing_ok=True)
        except HTTPException:
            pass
        except OSError:
            pass

    remove_protocol(
        store,
        protocol_id,
        delete_photo_file=lambda _s, fn: _del_photo(store, fn),
        delete_signature_file=_delete_signature_file,
    )
    return {"ok": True}


@app.get("/api/protocols/{protocol_id}/photos")
def list_protocol_photos(protocol_id: str, store: TenantStore = Depends(get_tenant_store)):
    protocol = find_protocol(store, protocol_id)
    photos = [_photo_api_item(store, p) for p in protocol_photos_list(protocol)]
    return {
        "photos": photos,
        "count": len(photos),
        "maxPhotos": MAX_PHOTOS_PER_PROTOCOL,
    }


@app.post("/api/protocols/{protocol_id}/photos")
async def upload_protocol_photo(
    protocol_id: str,
    file: UploadFile = File(...),
    store: TenantStore = Depends(get_tenant_store_write),
):
    protocol = find_protocol(store, protocol_id)
    if str(protocol.get("mode") or "") != "signed":
        raise HTTPException(status_code=400, detail="Fotos sind nur bei Protokollen mit Unterschrift möglich.")
    photos = protocol_photos_list(protocol)
    if len(photos) >= MAX_PHOTOS_PER_PROTOCOL:
        raise HTTPException(
            status_code=400,
            detail=f"Maximal {MAX_PHOTOS_PER_PROTOCOL} Fotos pro Protokoll erlaubt.",
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
    dest = store.uploads_dir("photos") / safe_name
    dest.write_bytes(content)

    entry: dict[str, Any] = {
        "id": photo_id,
        "filename": safe_name,
        "originalFilename": file.filename if file.filename else "",
        "contentType": file.content_type if file.content_type else "application/octet-stream",
        "sizeBytes": n,
        "uploadedAt": datetime.now(timezone.utc).isoformat(),
    }
    photos.append(entry)
    save_protocol_photos(store, protocol_id, photos)
    item = _photo_api_item(store, entry)
    return {
        "ok": True,
        "photo": item,
        "photos": [_photo_api_item(store, p) for p in photos],
        "count": len(photos),
        "maxPhotos": MAX_PHOTOS_PER_PROTOCOL,
    }


@app.delete("/api/protocols/{protocol_id}/photos/{photo_id}")
def delete_protocol_photo(
    protocol_id: str,
    photo_id: str,
    store: TenantStore = Depends(get_tenant_store_write),
):
    protocol = find_protocol(store, protocol_id)
    photos = protocol_photos_list(protocol)
    kept: list[dict[str, Any]] = []
    removed: dict[str, Any] | None = None
    for p in photos:
        if str(p.get("id") or "") == photo_id:
            removed = p
        else:
            kept.append(p)
    if removed is None:
        raise HTTPException(status_code=404, detail="Foto nicht gefunden")
    fn = removed.get("filename")
    if isinstance(fn, str) and fn:
        try:
            path = _resolve_photo_path(store, fn)
            path.unlink(missing_ok=True)
        except HTTPException:
            pass
        except OSError:
            pass
    save_protocol_photos(store, protocol_id, kept)
    return {"ok": True, "count": len(kept), "maxPhotos": MAX_PHOTOS_PER_PROTOCOL}


@app.get("/api/protocols/{protocol_id}/signatures")
def list_protocol_signatures(protocol_id: str, store: TenantStore = Depends(get_tenant_store)):
    protocol = find_protocol(store, protocol_id)
    signatures = _protocol_signatures_api_payload(store, protocol)
    count = sum(1 for v in signatures.values() if v is not None)
    return {"signatures": signatures, "count": count}


@app.post("/api/protocols/{protocol_id}/signatures/{role}")
async def upload_protocol_signature(
    protocol_id: str,
    role: str,
    file: UploadFile = File(...),
    signedByLabel: str | None = Form(None),
    store: TenantStore = Depends(get_tenant_store_write),
):
    sig_role = _validate_signature_role(role)
    protocol = find_protocol(store, protocol_id)
    if not file.filename:
        raise HTTPException(status_code=400, detail="Keine Datei")
    content = await file.read()
    _validate_signature_png(content)

    signatures = protocol_signatures_doc(protocol)
    previous = signatures.get(sig_role)
    if isinstance(previous, dict):
        _delete_signature_file(store, previous.get("filename"))

    sig_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    safe_name = f"sig_{ts}_{sig_role}_{sig_id}.png"
    dest = store.uploads_dir("signatures") / safe_name
    dest.write_bytes(content)

    prof = store.read_json("company_profile.json", {})
    if sig_role == "customer":
        label = protocol_entrepreneur_display_name(protocol, prof)[:120] or None
    elif sig_role == "employee":
        label = protocol_partner_display_name(protocol)[:120] or None
    else:
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
    save_protocol_signatures(store, protocol_id, signatures)
    item = _signature_api_item(store, sig_role, entry)
    count = sum(1 for v in signatures.values() if isinstance(v, dict))
    return {
        "ok": True,
        "signature": item,
        "signatures": _protocol_signatures_api_payload(store, {"signatures": signatures}),
        "count": count,
    }


@app.delete("/api/protocols/{protocol_id}/signatures/{role}")
def delete_protocol_signature(
    protocol_id: str,
    role: str,
    store: TenantStore = Depends(get_tenant_store_write),
):
    sig_role = _validate_signature_role(role)
    protocol = find_protocol(store, protocol_id)
    signatures = protocol_signatures_doc(protocol)
    previous = signatures.get(sig_role)
    if not isinstance(previous, dict):
        raise HTTPException(status_code=404, detail="Signatur nicht gefunden")
    _delete_signature_file(store, previous.get("filename"))
    signatures[sig_role] = None
    save_protocol_signatures(store, protocol_id, signatures)
    count = sum(1 for v in signatures.values() if isinstance(v, dict))
    return {
        "ok": True,
        "signatures": _protocol_signatures_api_payload(store, {"signatures": signatures}),
        "count": count,
    }


@app.post("/api/protocols/{protocol_id}/send-office", response_model=SendOfficeResponse)
def send_protocol_to_office_endpoint(
    protocol_id: str,
    user_id: str = Depends(require_active_license),
    store: TenantStore = Depends(get_tenant_store_write),
) -> SendOfficeResponse:
    protocol = find_protocol(store, protocol_id)
    prof = store.read_json("company_profile.json", {})
    office = str(prof.get("officeEmail") or "").strip()
    if not office:
        raise HTTPException(status_code=400, detail="Keine Büro-E-Mail im Firmenprofil hinterlegt.")

    sender_email = _smtp_sender_email_for_user_id(user_id)
    if not sender_email:
        raise HTTPException(status_code=401, detail="Versand nicht möglich: Anmeldung nicht mehr gültig.")
    mail_config = get_mail_config(sender_email)
    if not mail_config:
        raise HTTPException(
            status_code=400,
            detail=(
                "Mail-Anbindung fehlt. Bitte einmal in der App ausloggen und "
                "wieder einloggen, damit die SMTP-Daten geprüft und gespeichert werden."
            ),
        )

    ok, simulated, message = send_protocol_to_office(
        protocol,
        prof,
        office,
        mail_config=mail_config,
        resolve_logo=_export_resolve_logo(store),
        resolve_signature=_export_resolve_signature(store),
        photos_upload_dir=store.uploads_dir("photos"),
    )
    if not ok:
        raise HTTPException(status_code=500, detail=message or "Protokoll konnte nicht gesendet werden.")
    # Gedankensammlung: nach Versand Tages-Entwurf schließen (weitere Einträge → neuer Entwurf).
    if is_thoughts_mode(str(protocol.get("mode") or "")):
        mark_protocol_office_sent(store, protocol_id)
    return SendOfficeResponse(ok=True, simulated=simulated, message=message)


@app.get("/api/protocols/{protocol_id}/export/pdf")
def export_protocol_pdf(protocol_id: str, store: TenantStore = Depends(get_tenant_store)):
    protocol = find_protocol(store, protocol_id)
    prof = store.read_json("company_profile.json", {})
    try:
        blob = build_protocol_pdf_bytes(
            protocol,
            prof,
            resolve_logo=_export_resolve_logo(store),
            resolve_signature=_export_resolve_signature(store),
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Export konnte nicht erstellt werden.")
    ascii_fn, desc_fn = build_protocol_attachment_names(protocol, "pdf")
    return Response(
        content=blob,
        media_type="application/pdf",
        headers={"Content-Disposition": _content_disposition_attachment(ascii_fn, desc_fn)},
    )


# --- Lieferschein-Scan V1 (additiv) ----------------------------------------------------


@app.get("/api/delivery-notes")
def list_delivery_notes(
    projectId: str | None = None,
    _perm: str = Depends(require_permission("delivery_notes")),
    store: TenantStore = Depends(get_tenant_store),
):
    notes = read_delivery_notes(store)
    notes.sort(key=lambda n: n.get("createdAt", ""), reverse=True)
    if projectId:
        notes = [n for n in notes if n.get("projectId") == projectId]
    return {"deliveryNotes": notes}


@app.post("/api/delivery-notes")
def create_delivery_note(
    body: DeliveryNoteCreateBody,
    _perm: str = Depends(require_permission("delivery_notes")),
    store: TenantStore = Depends(get_tenant_store_write),
):
    prof = store.read_json("company_profile.json", {})
    logo_fn = prof.get("logoFilename")
    company_logo_url = _logo_public_url(store, logo_fn) if logo_fn else None
    if logo_fn and not company_logo_url:
        legacy_logo = UPLOADS_DIR / str(logo_fn)
        if legacy_logo.is_file():
            company_logo_url = f"/uploads/logos/{logo_fn}"

    projects = store.read_json("projects.json", {"projects": []}).get("projects") or []
    project = next((p for p in projects if str(p.get("id") or "") == body.projectId), None)
    project_name = (body.projectName or "").strip()
    customer_name = (body.customerName or "").strip()
    if project:
        if not project_name:
            project_name = str(project.get("name") or "").strip()
        if not customer_name:
            customer_name = str(project.get("customer") or "").strip()

    return create_delivery_note_doc(
        store,
        company_name=str(prof.get("companyName") or ""),
        company_logo_url=company_logo_url,
        office_email=str(prof.get("officeEmail") or ""),
        project_id=body.projectId,
        project_name=project_name,
        customer_name=customer_name,
        date=body.date,
        note=body.note,
    )


@app.get("/api/delivery-notes/{note_id}")
def get_delivery_note(note_id: str, store: TenantStore = Depends(get_tenant_store)):
    return find_delivery_note(store, note_id)


@app.delete("/api/delivery-notes/{note_id}")
def delete_delivery_note(note_id: str, store: TenantStore = Depends(get_tenant_store_write)):
    def _del_photo(_store: TenantStore, filename: str) -> None:
        try:
            path = _resolve_photo_path(_store, filename)
            path.unlink(missing_ok=True)
        except HTTPException:
            pass
        except OSError:
            pass

    remove_delivery_note(
        store,
        note_id,
        delete_photo_file=lambda _s, fn: _del_photo(store, fn),
    )
    return {"ok": True}


@app.get("/api/delivery-notes/{note_id}/photos")
def list_delivery_note_photos(note_id: str, store: TenantStore = Depends(get_tenant_store)):
    note = find_delivery_note(store, note_id)
    photos = [_photo_api_item(store, p) for p in delivery_note_photos_list(note)]
    return {
        "photos": photos,
        "count": len(photos),
        "maxPhotos": MAX_PHOTOS_PER_DELIVERY_NOTE,
    }


@app.post("/api/delivery-notes/{note_id}/photos")
async def upload_delivery_note_photo(
    note_id: str,
    file: UploadFile = File(...),
    store: TenantStore = Depends(get_tenant_store_write),
):
    note = find_delivery_note(store, note_id)
    photos = delivery_note_photos_list(note)
    if len(photos) >= MAX_PHOTOS_PER_DELIVERY_NOTE:
        raise HTTPException(
            status_code=400,
            detail=f"Maximal {MAX_PHOTOS_PER_DELIVERY_NOTE} Scan-Seiten pro Lieferschein erlaubt.",
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
    dest = store.uploads_dir("photos") / safe_name
    dest.write_bytes(content)

    entry: dict[str, Any] = {
        "id": photo_id,
        "filename": safe_name,
        "originalFilename": file.filename if file.filename else "",
        "contentType": file.content_type if file.content_type else "application/octet-stream",
        "sizeBytes": n,
        "uploadedAt": datetime.now(timezone.utc).isoformat(),
    }
    photos.append(entry)
    save_delivery_note_photos(store, note_id, photos)
    item = _photo_api_item(store, entry)
    return {
        "ok": True,
        "photo": item,
        "photos": [_photo_api_item(store, p) for p in photos],
        "count": len(photos),
        "maxPhotos": MAX_PHOTOS_PER_DELIVERY_NOTE,
    }


@app.delete("/api/delivery-notes/{note_id}/photos/{photo_id}")
def delete_delivery_note_photo(
    note_id: str,
    photo_id: str,
    store: TenantStore = Depends(get_tenant_store_write),
):
    note = find_delivery_note(store, note_id)
    photos = delivery_note_photos_list(note)
    kept: list[dict[str, Any]] = []
    removed: dict[str, Any] | None = None
    for p in photos:
        if str(p.get("id") or "") == photo_id:
            removed = p
        else:
            kept.append(p)
    if removed is None:
        raise HTTPException(status_code=404, detail="Foto nicht gefunden")
    fn = removed.get("filename")
    if isinstance(fn, str) and fn:
        try:
            path = _resolve_photo_path(store, fn)
            path.unlink(missing_ok=True)
        except HTTPException:
            pass
        except OSError:
            pass
    save_delivery_note_photos(store, note_id, kept)
    return {"ok": True, "count": len(kept), "maxPhotos": MAX_PHOTOS_PER_DELIVERY_NOTE}


@app.post("/api/delivery-notes/{note_id}/send-office", response_model=SendOfficeResponse)
def send_delivery_note_to_office_endpoint(
    note_id: str,
    user_id: str = Depends(require_active_license),
    store: TenantStore = Depends(get_tenant_store_write),
) -> SendOfficeResponse:
    note = find_delivery_note(store, note_id)
    if not delivery_note_photos_list(note):
        raise HTTPException(status_code=400, detail="Mindestens eine Scan-Seite ist erforderlich.")

    prof = store.read_json("company_profile.json", {})
    office = str(prof.get("officeEmail") or "").strip()
    if not office:
        raise HTTPException(status_code=400, detail="Keine Büro-E-Mail im Firmenprofil hinterlegt.")

    sender_email = _smtp_sender_email_for_user_id(user_id)
    if not sender_email:
        raise HTTPException(status_code=401, detail="Versand nicht möglich: Anmeldung nicht mehr gültig.")
    mail_config = get_mail_config(sender_email)
    if not mail_config:
        raise HTTPException(
            status_code=400,
            detail=(
                "Mail-Anbindung fehlt. Bitte einmal in der App ausloggen und "
                "wieder einloggen, damit die SMTP-Daten geprüft und gespeichert werden."
            ),
        )

    ok, simulated, message = send_delivery_note_to_office(
        note,
        prof,
        office,
        mail_config=mail_config,
        resolve_logo=_export_resolve_logo(store),
        resolve_photo=_export_resolve_photo(store),
        photos_upload_dir=store.uploads_dir("photos"),
    )
    if not ok:
        raise HTTPException(status_code=500, detail=message or "Lieferschein konnte nicht gesendet werden.")
    return SendOfficeResponse(ok=True, simulated=simulated, message=message)


@app.get("/api/delivery-notes/{note_id}/export/pdf")
def export_delivery_note_pdf(note_id: str, store: TenantStore = Depends(get_tenant_store)):
    note = find_delivery_note(store, note_id)
    prof = store.read_json("company_profile.json", {})
    try:
        blob = build_delivery_note_pdf_bytes(
            note,
            prof,
            resolve_logo=_export_resolve_logo(store),
            resolve_photo=_export_resolve_photo(store),
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Export konnte nicht erstellt werden.")
    ascii_fn, desc_fn = build_delivery_note_attachment_names(note, "pdf")
    return Response(
        content=blob,
        media_type="application/pdf",
        headers={"Content-Disposition": _content_disposition_attachment(ascii_fn, desc_fn)},
    )


app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR.parent)), name="uploads")


# Optional: Root für Health auch ohne trailing — bereits GET /

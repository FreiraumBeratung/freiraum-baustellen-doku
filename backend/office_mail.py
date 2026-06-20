"""SMTP-Versand des Tagesberichts ans Büro.

Architektur (V2):
- KEINE Environment-Variablen mehr. Die SMTP-Konfiguration wird explizit
  übergeben (``mail_config`` Parameter). Die Konfiguration stammt aus dem
  verschlüsselten Mail-Store (siehe ``app.services.mail_store``), der beim
  App-Login pro Firmen-E-Mail befüllt wird.
- Wenn keine Konfiguration vorhanden ist, wird kein Dry-Run mehr simuliert,
  sondern ein klarer Fehlerstatus zurückgegeben, damit der User in der App
  erneut den Login durchläuft.
"""

from __future__ import annotations

import logging
import re
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from report_export import (
    LogoPathResolver,
    PhotoPathResolver,
    SignaturePathResolver,
    build_attachment_names,
    build_collective_attachment_names,
    build_collective_pdf_bytes,
    build_docx_bytes,
    build_pdf_bytes,
)

logger = logging.getLogger(__name__)

MSG_NOT_CONFIGURED = (
    "Mail-Anbindung ist nicht konfiguriert. Bitte erneut in der App anmelden, "
    "damit die SMTP-Daten geprüft und gespeichert werden."
)
MSG_SENT = "Bericht wurde ans Büro gesendet."
MSG_SENT_WITH_PHOTOS = "Bericht mit {count} Foto(s) wurde ans Büro gesendet."
MSG_FEEDBACK_SENT = "Feedback wurde gesendet."


def _format_date_de(date_raw: Any) -> str:
    """Formatiert ein Datum fuer den Mail-Text im deutschen Stil (z.B. 25.5.2026)."""
    s = str(date_raw or "").strip()
    if not s or s == "—":
        return "—"
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
    if m:
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{day}.{month}.{year}"
    return s


def _company_signoff_name(profile: dict[str, Any]) -> str:
    """Firmenname aus dem Profil fuer die Grußformel."""
    name = str(profile.get("companyName") or "").strip()
    if name:
        return name
    contact = str(profile.get("contactPerson") or "").strip()
    if contact:
        return contact
    return "Ihr Team"


def _build_mail_body(report: dict[str, Any], profile: dict[str, Any], *, photo_count: int = 0) -> str:
    site = report.get("projectName") or "—"
    day = _format_date_de(report.get("date"))
    company = _company_signoff_name(profile)
    employees = report.get("employees")
    if isinstance(employees, list) and employees:
        emps = ", ".join(str(e) for e in employees)
    else:
        emps = "Keine Angabe"
    start = report.get("startTime") or "?"
    end = report.get("endTime") or "?"
    photo_line = ""
    if photo_count > 0:
        label = "Baustellenfoto" if photo_count == 1 else "Baustellenfotos"
        photo_line = f"{label}: {photo_count} Bild(er) im Anhang.\n\n"
    return (
        "Hallo,\n\n"
        f"anbei der Tagesbericht zur Baustelle {site} vom {day}.\n\n"
        f"{photo_line}"
        f"Mitarbeiter: {emps}\n"
        f"Arbeitszeit: {start} – {end}\n\n"
        "Mit freundlichen Grüßen\n"
        f"{company}\n\n\n"
        "Powered by Freiraum Beratung"
    )


def _report_photos_list(report: dict[str, Any]) -> list[dict[str, Any]]:
    raw = report.get("photos")
    if not isinstance(raw, list):
        return []
    return [p for p in raw if isinstance(p, dict)]


def _safe_photo_path(filename: str, photos_dir: Path) -> Path | None:
    fn = str(filename or "")
    if not fn or "/" in fn or "\\" in fn or fn.strip() != fn:
        return None
    base = photos_dir.resolve()
    path = (photos_dir / fn).resolve()
    try:
        path.relative_to(base)
    except ValueError:
        return None
    if not path.is_file():
        return None
    return path


def _photo_mime(filename: str, content_type: Any) -> tuple[str, str]:
    ct = str(content_type or "").split(";")[0].strip().lower()
    if ct in {"image/jpeg", "image/png", "image/webp"}:
        main, sub = ct.split("/", 1)
        return main, sub
    ext = Path(filename).suffix.lower()
    if ext in {".jpg", ".jpeg"}:
        return "image", "jpeg"
    if ext == ".png":
        return "image", "png"
    if ext == ".webp":
        return "image", "webp"
    return "application", "octet-stream"


def _photo_attachment_filename(entry: dict[str, Any], index: int) -> str:
    original = str(entry.get("originalFilename") or "").strip()
    if original:
        name = Path(original).name
        safe = re.sub(r"[^\w.\-]+", "_", name, flags=re.UNICODE)
        if safe and len(safe) <= 120:
            return safe
    stored = str(entry.get("filename") or "")
    ext = Path(stored).suffix.lower() or ".jpg"
    if ext == ".jpeg":
        ext = ".jpg"
    return f"baustellenfoto_{index}{ext}"


def _count_attachable_photos(report: dict[str, Any], photos_dir: Path | None) -> int:
    if photos_dir is None:
        return 0
    count = 0
    for entry in _report_photos_list(report):
        fn = entry.get("filename")
        if isinstance(fn, str) and _safe_photo_path(fn, photos_dir) is not None:
            count += 1
    return count


def _attach_report_photos(msg: EmailMessage, report: dict[str, Any], photos_dir: Path | None) -> int:
    if photos_dir is None:
        return 0
    attached = 0
    for i, entry in enumerate(_report_photos_list(report), start=1):
        fn = entry.get("filename")
        if not isinstance(fn, str):
            continue
        path = _safe_photo_path(fn, photos_dir)
        if path is None:
            logger.warning("Baustellenfoto nicht gefunden oder ungueltig: %s", fn)
            continue
        try:
            blob = path.read_bytes()
        except OSError:
            logger.warning("Baustellenfoto konnte nicht gelesen werden: %s", fn)
            continue
        main, sub = _photo_mime(fn, entry.get("contentType"))
        attach_name = _photo_attachment_filename(entry, i)
        msg.add_attachment(blob, maintype=main, subtype=sub, filename=attach_name)
        attached += 1
    return attached


def send_report_to_office(
    report: dict[str, Any],
    profile: dict[str, Any],
    to_email: str,
    *,
    mail_config: dict[str, Any] | None = None,
    photos_upload_dir: Path | str | None = None,
    resolve_logo: LogoPathResolver | None = None,
    resolve_signature: SignaturePathResolver | None = None,
) -> tuple[bool, bool, str]:
    """Sendet den Tagesbericht per SMTP ans Büro.

    Args:
        report: Tagesbericht-Datensatz (mind. ``projectName``, ``date``,
            ``exportFormat``).
        profile: Firmenprofil (für PDF/DOCX-Erzeugung).
        to_email: Empfänger-E-Mail (Büro-Mail aus dem Firmenprofil).
        mail_config: SMTP-Konfiguration mit Feldern ``host``, ``port``,
            ``use_tls``, ``use_ssl``, ``email``, ``password``. Wird beim Login
            befüllt und aus dem verschlüsselten Mail-Store geladen.
        photos_upload_dir: Verzeichnis der hochgeladenen Baustellenfotos
            (``report["photos"]`` → Dateien auf Platte).

    Returns:
        Tuple ``(ok, simulated, message)``. ``simulated`` ist immer ``False``
        in V2: ohne gültige Konfiguration wird klar ``ok=False`` mit Hinweis
        zurückgegeben, statt einen Dry-Run vorzutäuschen.
    """
    if not mail_config or not mail_config.get("host") or not mail_config.get("password"):
        return False, False, MSG_NOT_CONFIGURED

    from_addr = str(mail_config.get("email") or "").strip()
    user = str(mail_config.get("email") or "").strip()
    password = str(mail_config.get("password") or "")
    host = str(mail_config.get("host") or "").strip()
    port = int(mail_config.get("port") or 0)
    use_tls = bool(mail_config.get("use_tls", True))
    use_ssl = bool(mail_config.get("use_ssl", False))

    if not from_addr or not user or not password or not host or not port:
        return False, False, MSG_NOT_CONFIGURED

    subject_day = _format_date_de(report.get("date"))
    subject = f"Tagesbericht: {report.get('projectName') or '—'} vom {subject_day}"

    fmt = str(report.get("exportFormat") or "PDF").strip().lower()
    try:
        if fmt == "word":
            blob = build_docx_bytes(report, profile, resolve_logo=resolve_logo)
            ascii_fn, _desc = build_attachment_names(report, "docx")
            main = "application"
            sub = "vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            blob = build_pdf_bytes(
                report,
                profile,
                resolve_logo=resolve_logo,
                resolve_signature=resolve_signature,
            )
            ascii_fn, _desc = build_attachment_names(report, "pdf")
            main = "application"
            sub = "pdf"
    except Exception:
        logger.exception("Anhang für Mail konnte nicht erzeugt werden")
        return False, False, "Der Berichtsanhang konnte nicht erzeugt werden."

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email

    photos_dir = Path(photos_upload_dir) if photos_upload_dir else None
    photo_count = _count_attachable_photos(report, photos_dir)
    msg.set_content(_build_mail_body(report, profile, photo_count=photo_count))
    msg.add_attachment(blob, maintype=main, subtype=sub, filename=ascii_fn)
    attached_photos = _attach_report_photos(msg, report, photos_dir)
    if attached_photos != photo_count:
        photo_count = attached_photos

    ctx = ssl.create_default_context()
    try:
        if use_ssl:
            with smtplib.SMTP_SSL(host, port, timeout=60, context=ctx) as smtp:
                smtp.login(user, password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=60) as smtp:
                smtp.ehlo()
                if use_tls:
                    smtp.starttls(context=ctx)
                    smtp.ehlo()
                smtp.login(user, password)
                smtp.send_message(msg)
    except OSError:
        logger.exception("SMTP Netzwerkfehler beim Versand")
        return False, False, "Netzwerkfehler beim Versand. Bitte erneut versuchen."
    except smtplib.SMTPAuthenticationError:
        logger.exception("SMTP-Authentifizierung beim Versand fehlgeschlagen")
        return (
            False,
            False,
            "Mail-Zugangsdaten wurden vom Anbieter abgelehnt. Bitte erneut anmelden.",
        )
    except smtplib.SMTPException:
        logger.exception("SMTP-Fehler beim Versand")
        return False, False, "SMTP-Fehler beim Versand. Bitte später erneut versuchen."

    return True, False, MSG_SENT_WITH_PHOTOS.format(count=photo_count) if photo_count else MSG_SENT


def send_collective_to_office(
    payload: dict[str, Any],
    profile: dict[str, Any],
    to_email: str,
    *,
    mail_config: dict[str, Any] | None = None,
    photos_upload_dir: Path | str | None = None,
    resolve_logo: LogoPathResolver | None = None,
    resolve_photo: PhotoPathResolver | None = None,
    resolve_signature: SignaturePathResolver | None = None,
) -> tuple[bool, bool, str]:
    """Sendet den Gesamtbericht (Sammelbericht eines Durchlaufs) per SMTP ans Büro.

    Baut das PDF aus dem aggregierten ``payload`` (siehe ``collective_report``) und
    hängt die Fotos des Durchlaufs an. Spiegelt die Versand-/Fehlerlogik von
    ``send_report_to_office`` (rein additiv, ohne diese zu verändern).
    """
    if not mail_config or not mail_config.get("host") or not mail_config.get("password"):
        return False, False, MSG_NOT_CONFIGURED

    from_addr = str(mail_config.get("email") or "").strip()
    user = str(mail_config.get("email") or "").strip()
    password = str(mail_config.get("password") or "")
    host = str(mail_config.get("host") or "").strip()
    port = int(mail_config.get("port") or 0)
    use_tls = bool(mail_config.get("use_tls", True))
    use_ssl = bool(mail_config.get("use_ssl", False))

    if not from_addr or not user or not password or not host or not port:
        return False, False, MSG_NOT_CONFIGURED

    project_name = str(payload.get("projectName") or "—")
    df = _format_date_de(payload.get("dateFrom"))
    dt = _format_date_de(payload.get("dateTo"))
    zeitraum = df if df == dt else f"{df} – {dt}"
    subject = f"Gesamtbericht: {project_name} ({zeitraum})"

    try:
        blob = build_collective_pdf_bytes(
            payload,
            profile,
            resolve_logo=resolve_logo,
            resolve_photo=resolve_photo,
            resolve_signature=resolve_signature,
        )
        ascii_fn, _desc = build_collective_attachment_names(payload, "pdf")
    except Exception:
        logger.exception("Gesamtbericht-Anhang für Mail konnte nicht erzeugt werden")
        return False, False, "Der Gesamtbericht-Anhang konnte nicht erzeugt werden."

    # Fotos des Durchlaufs anhängen (Foto-Helfer arbeiten auf einem report-Dict mit "photos").
    photos_report = {"photos": payload.get("photos") or []}
    photos_dir = Path(photos_upload_dir) if photos_upload_dir else None
    photo_count = _count_attachable_photos(photos_report, photos_dir)

    totals = payload.get("totals") if isinstance(payload.get("totals"), dict) else {}
    body_lines = [
        "Guten Tag,",
        "",
        f"anbei der Gesamtbericht zur Baustelle {project_name} (Zeitraum {zeitraum}).",
        f"Arbeitstage: {totals.get('reportCount') or 0}.",
        "",
        "Diese E-Mail wurde automatisch über Freiraum Baustellen-Doku erstellt.",
        "",
        f"{_company_signoff_name(profile)}",
    ]

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email
    msg.set_content("\n".join(body_lines))
    msg.add_attachment(blob, maintype="application", subtype="pdf", filename=ascii_fn)
    attached_photos = _attach_report_photos(msg, photos_report, photos_dir)
    if attached_photos != photo_count:
        photo_count = attached_photos

    ctx = ssl.create_default_context()
    try:
        if use_ssl:
            with smtplib.SMTP_SSL(host, port, timeout=60, context=ctx) as smtp:
                smtp.login(user, password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=60) as smtp:
                smtp.ehlo()
                if use_tls:
                    smtp.starttls(context=ctx)
                    smtp.ehlo()
                smtp.login(user, password)
                smtp.send_message(msg)
    except OSError:
        logger.exception("SMTP Netzwerkfehler beim Gesamtbericht-Versand")
        return False, False, "Netzwerkfehler beim Versand. Bitte erneut versuchen."
    except smtplib.SMTPAuthenticationError:
        logger.exception("SMTP-Authentifizierung beim Gesamtbericht-Versand fehlgeschlagen")
        return False, False, "Mail-Zugangsdaten wurden vom Anbieter abgelehnt. Bitte erneut anmelden."
    except smtplib.SMTPException:
        logger.exception("SMTP-Fehler beim Gesamtbericht-Versand")
        return False, False, "SMTP-Fehler beim Versand. Bitte später erneut versuchen."

    return True, False, (
        f"Gesamtbericht mit {photo_count} Foto(s) wurde ans Büro gesendet."
        if photo_count
        else "Gesamtbericht wurde ans Büro gesendet."
    )


def send_feedback_mail(
    *,
    to_email: str,
    subject: str,
    body: str,
    mail_config: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    """Sendet eine einfache Text-Feedback-Mail via gespeicherter SMTP-Konfiguration."""
    if not mail_config or not mail_config.get("host") or not mail_config.get("password"):
        return False, MSG_NOT_CONFIGURED

    from_addr = str(mail_config.get("email") or "").strip()
    user = str(mail_config.get("email") or "").strip()
    password = str(mail_config.get("password") or "")
    host = str(mail_config.get("host") or "").strip()
    port = int(mail_config.get("port") or 0)
    use_tls = bool(mail_config.get("use_tls", True))
    use_ssl = bool(mail_config.get("use_ssl", False))

    if not from_addr or not user or not password or not host or not port:
        return False, MSG_NOT_CONFIGURED

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email
    msg.set_content(body)

    ctx = ssl.create_default_context()
    try:
        if use_ssl:
            with smtplib.SMTP_SSL(host, port, timeout=60, context=ctx) as smtp:
                smtp.login(user, password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=60) as smtp:
                smtp.ehlo()
                if use_tls:
                    smtp.starttls(context=ctx)
                    smtp.ehlo()
                smtp.login(user, password)
                smtp.send_message(msg)
    except OSError:
        logger.exception("SMTP Netzwerkfehler beim Feedback-Versand")
        return False, "Netzwerkfehler beim Versand. Bitte erneut versuchen."
    except smtplib.SMTPAuthenticationError:
        logger.exception("SMTP-Authentifizierung beim Feedback-Versand fehlgeschlagen")
        return False, "Mail-Zugangsdaten wurden vom Anbieter abgelehnt. Bitte erneut anmelden."
    except smtplib.SMTPException:
        logger.exception("SMTP-Fehler beim Feedback-Versand")
        return False, "SMTP-Fehler beim Versand. Bitte später erneut versuchen."

    return True, MSG_FEEDBACK_SENT

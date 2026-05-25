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
from typing import Any

from report_export import build_attachment_names, build_docx_bytes, build_pdf_bytes

logger = logging.getLogger(__name__)

MSG_NOT_CONFIGURED = (
    "Mail-Anbindung ist nicht konfiguriert. Bitte erneut in der App anmelden, "
    "damit die SMTP-Daten geprüft und gespeichert werden."
)
MSG_SENT = "Bericht wurde ans Büro gesendet."


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


def _build_mail_body(report: dict[str, Any], profile: dict[str, Any]) -> str:
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
    return (
        "Hallo,\n\n"
        f"anbei der Tagesbericht zur Baustelle {site} vom {day}.\n\n"
        f"Mitarbeiter: {emps}\n"
        f"Arbeitszeit: {start} – {end}\n\n"
        "Mit freundlichen Grüßen\n"
        f"{company}\n\n\n"
        "Powered by Freiraum Beratung"
    )


def send_report_to_office(
    report: dict[str, Any],
    profile: dict[str, Any],
    to_email: str,
    *,
    mail_config: dict[str, Any] | None = None,
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
    body = _build_mail_body(report, profile)

    fmt = str(report.get("exportFormat") or "PDF").strip().lower()
    try:
        if fmt == "word":
            blob = build_docx_bytes(report, profile)
            ascii_fn, _desc = build_attachment_names(report, "docx")
            main = "application"
            sub = "vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            blob = build_pdf_bytes(report, profile)
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
    msg.set_content(body)
    msg.add_attachment(blob, maintype=main, subtype=sub, filename=ascii_fn)

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

    return True, False, MSG_SENT

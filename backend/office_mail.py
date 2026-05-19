"""SMTP-Versand Tagesbericht ans Büro (optional; ohne Konfiguration: Dry-Run)."""

from __future__ import annotations

import logging
import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Any

from report_export import build_attachment_names, build_docx_bytes, build_pdf_bytes

logger = logging.getLogger(__name__)

MSG_SIMULATED = "SMTP ist noch nicht konfiguriert. Versand wurde simuliert."
MSG_SENT = "Bericht wurde ans Büro gesendet."


def _smtp_config() -> dict[str, Any]:
    port_raw = os.environ.get("SMTP_PORT", "587").strip()
    try:
        port = int(port_raw)
    except ValueError:
        port = 587
    tls_val = os.environ.get("SMTP_USE_TLS", "true").strip().lower()
    use_tls = tls_val in {"1", "true", "yes", "ja"}
    return {
        "host": os.environ.get("SMTP_HOST", "").strip(),
        "port": port,
        "user": os.environ.get("SMTP_USER", "").strip(),
        "password": os.environ.get("SMTP_PASSWORD", "").strip(),
        "from_addr": os.environ.get("SMTP_FROM", "").strip(),
        "use_tls": use_tls,
    }


def smtp_ready() -> bool:
    c = _smtp_config()
    return bool(c["host"] and c["user"] and c["password"])


def _build_mail_body(report: dict[str, Any]) -> str:
    site = report.get("projectName") or "—"
    day = report.get("date") or "—"
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
        "Freiraum Baustellen-Doku\n\n"
        "Powered by Freiraum Beratung"
    )


def send_report_to_office(
    report: dict[str, Any],
    profile: dict[str, Any],
    to_email: str,
) -> tuple[bool, bool, str]:
    """
    Returns: (success, simulated, message)
    """
    cfg = _smtp_config()
    from_addr = cfg["from_addr"] or cfg["user"] or "noreply@localhost"

    if not smtp_ready():
        logger.info(
            "SMTP nicht konfiguriert – simulierter Versand (report_id=%s, to=%s)",
            report.get("id"),
            to_email,
        )
        return True, True, MSG_SIMULATED

    subject = f"Tagesbericht: {report.get('projectName') or '—'} vom {report.get('date') or '—'}"
    body = _build_mail_body(report)

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
        return False, False, ""

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email
    msg.set_content(body)
    msg.add_attachment(blob, maintype=main, subtype=sub, filename=ascii_fn)

    host = cfg["host"]
    port = int(cfg["port"])
    password = cfg["password"]
    user = cfg["user"]

    ctx = ssl.create_default_context()

    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=60, context=ctx) as smtp:
                smtp.login(user, password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=60) as smtp:
                smtp.ehlo()
                if cfg["use_tls"]:
                    smtp.starttls(context=ctx)
                    smtp.ehlo()
                smtp.login(user, password)
                smtp.send_message(msg)
    except OSError:
        logger.exception("SMTP Netzwerkfehler")
        return False, False, ""
    except smtplib.SMTPException:
        logger.exception("SMTP-Fehler")
        return False, False, ""

    return True, False, MSG_SENT

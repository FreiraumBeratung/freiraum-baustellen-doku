"""SMTP-Server-Auto-Discovery + Verifizierung.

Funktion: aus einer E-Mail-Adresse die passenden SMTP-Server-Daten ermitteln
(Presets für gängige Provider + Domain-Guess als Fallback) und die übergebenen
Credentials durch einen echten SMTP-Login-Versuch verifizieren.

Es werden bewusst KEINE Environment-Variablen gelesen. Der Aufrufer übergibt
E-Mail und Passwort; das Ergebnis ist ein verifizierter Server-Kandidat oder
ein Fehler mit nutzerfreundlichem Hinweis (z.B. Gmail-App-Passwort-Hinweis).
"""

from __future__ import annotations

import logging
import smtplib
import socket
import ssl
from dataclasses import dataclass
from typing import Iterable

logger = logging.getLogger(__name__)


@dataclass
class SmtpCandidate:
    host: str
    port: int
    use_tls: bool
    use_ssl: bool
    source: str  # "preset" oder "guess"


@dataclass
class SmtpVerifyResult:
    ok: bool
    candidate: SmtpCandidate | None
    error: str | None
    provider_hint: str | None


# Bekannte Provider-Presets (DE-Fokus). Tupel: (host, port, use_tls, use_ssl)
_PRESETS: dict[str, tuple[str, int, bool, bool]] = {
    # Google
    "gmail.com": ("smtp.gmail.com", 587, True, False),
    "googlemail.com": ("smtp.gmail.com", 587, True, False),
    # Microsoft
    "outlook.com": ("smtp.office365.com", 587, True, False),
    "outlook.de": ("smtp.office365.com", 587, True, False),
    "hotmail.com": ("smtp.office365.com", 587, True, False),
    "hotmail.de": ("smtp.office365.com", 587, True, False),
    "live.com": ("smtp.office365.com", 587, True, False),
    "live.de": ("smtp.office365.com", 587, True, False),
    "office365.com": ("smtp.office365.com", 587, True, False),
    # United Internet (web.de / GMX / 1und1)
    "web.de": ("smtp.web.de", 587, True, False),
    "gmx.de": ("mail.gmx.net", 587, True, False),
    "gmx.net": ("mail.gmx.net", 587, True, False),
    "gmx.com": ("mail.gmx.com", 587, True, False),
    "gmx.at": ("mail.gmx.net", 587, True, False),
    "1und1.de": ("smtp.1und1.de", 587, True, False),
    "1und1.com": ("smtp.1und1.de", 587, True, False),
    # Deutsche Telekom
    "t-online.de": ("securesmtp.t-online.de", 587, True, False),
    "magenta.de": ("securesmtp.t-online.de", 587, True, False),
    # Yahoo
    "yahoo.com": ("smtp.mail.yahoo.com", 587, True, False),
    "yahoo.de": ("smtp.mail.yahoo.com", 587, True, False),
    # Mailbox.org / Posteo
    "mailbox.org": ("smtp.mailbox.org", 587, True, False),
    "posteo.de": ("posteo.de", 587, True, False),
    "posteo.net": ("posteo.de", 587, True, False),
    # Ionos / Strato
    "ionos.de": ("smtp.ionos.de", 587, True, False),
    "ionos.com": ("smtp.ionos.de", 587, True, False),
    "strato.de": ("smtp.strato.de", 587, True, False),
    # Apple
    "icloud.com": ("smtp.mail.me.com", 587, True, False),
    "me.com": ("smtp.mail.me.com", 587, True, False),
    "mac.com": ("smtp.mail.me.com", 587, True, False),
}


_PROVIDER_HINTS: dict[str, str] = {
    "gmail.com": (
        "Bei Gmail muss ein App-Passwort verwendet werden (nicht das normale "
        "Google-Passwort). Bitte unter myaccount.google.com/apppasswords ein "
        "App-Passwort erstellen und hier eintragen."
    ),
    "googlemail.com": (
        "Bei Gmail muss ein App-Passwort verwendet werden (nicht das normale "
        "Google-Passwort). Bitte unter myaccount.google.com/apppasswords ein "
        "App-Passwort erstellen und hier eintragen."
    ),
    "outlook.com": (
        "Bei Outlook/Microsoft 365 ist häufig ein App-Passwort erforderlich, "
        "wenn die Zwei-Faktor-Authentifizierung aktiv ist. Bitte unter "
        "account.microsoft.com/security ein App-Passwort erstellen."
    ),
    "outlook.de": (
        "Bei Outlook/Microsoft 365 ist häufig ein App-Passwort erforderlich, "
        "wenn die Zwei-Faktor-Authentifizierung aktiv ist. Bitte unter "
        "account.microsoft.com/security ein App-Passwort erstellen."
    ),
    "hotmail.com": (
        "Bei Hotmail/Microsoft ist häufig ein App-Passwort erforderlich, wenn "
        "die Zwei-Faktor-Authentifizierung aktiv ist."
    ),
    "hotmail.de": (
        "Bei Hotmail/Microsoft ist häufig ein App-Passwort erforderlich, wenn "
        "die Zwei-Faktor-Authentifizierung aktiv ist."
    ),
    "yahoo.com": (
        "Bei Yahoo wird ein App-Passwort benötigt. Bitte unter login.yahoo.com "
        "in den Sicherheitseinstellungen ein App-Passwort erstellen."
    ),
    "yahoo.de": (
        "Bei Yahoo wird ein App-Passwort benötigt. Bitte unter login.yahoo.com "
        "in den Sicherheitseinstellungen ein App-Passwort erstellen."
    ),
    "icloud.com": (
        "Bei iCloud wird ein App-spezifisches Passwort benötigt. Bitte unter "
        "appleid.apple.com ein App-Passwort erstellen."
    ),
}


def _domain_from_email(email_address: str) -> str:
    s = str(email_address or "").strip().lower()
    if "@" not in s:
        return ""
    return s.split("@", 1)[1].strip()


def provider_hint_for(email_address: str) -> str | None:
    """Liefert einen Provider-spezifischen Hinweis (z.B. App-Passwort), wenn
    bekannt. Sonst None."""
    domain = _domain_from_email(email_address)
    if not domain:
        return None
    return _PROVIDER_HINTS.get(domain)


def discover_smtp_servers(email_address: str) -> list[SmtpCandidate]:
    """Liefert eine geordnete Liste von SMTP-Kandidaten für die E-Mail-Adresse.

    Reihenfolge:
    1. Preset (wenn Domain bekannt)
    2. Domain-Guess: smtp.<domain>:587 STARTTLS
    3. Domain-Guess: mail.<domain>:587 STARTTLS
    4. Domain-Guess: smtp.<domain>:465 SSL
    """
    domain = _domain_from_email(email_address)
    out: list[SmtpCandidate] = []
    if not domain:
        return out

    preset = _PRESETS.get(domain)
    if preset:
        host, port, use_tls, use_ssl = preset
        out.append(SmtpCandidate(host=host, port=port, use_tls=use_tls, use_ssl=use_ssl, source="preset"))

    guesses: tuple[tuple[str, int, bool, bool], ...] = (
        (f"smtp.{domain}", 587, True, False),
        (f"mail.{domain}", 587, True, False),
        (f"smtp.{domain}", 465, False, True),
    )
    seen_keys = {(c.host, c.port) for c in out}
    for host, port, use_tls, use_ssl in guesses:
        key = (host, port)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        out.append(SmtpCandidate(host=host, port=port, use_tls=use_tls, use_ssl=use_ssl, source="guess"))

    return out


def _try_smtp_login(candidate: SmtpCandidate, username: str, password: str, timeout: float = 10.0) -> tuple[bool, str | None]:
    ctx = ssl.create_default_context()
    try:
        if candidate.use_ssl:
            with smtplib.SMTP_SSL(candidate.host, candidate.port, timeout=timeout, context=ctx) as smtp:
                smtp.login(username, password)
            return True, None
        with smtplib.SMTP(candidate.host, candidate.port, timeout=timeout) as smtp:
            smtp.ehlo()
            if candidate.use_tls:
                smtp.starttls(context=ctx)
                smtp.ehlo()
            smtp.login(username, password)
        return True, None
    except (socket.gaierror, socket.timeout, ConnectionError, TimeoutError, OSError) as exc:
        return False, f"Netzwerkfehler: {exc}"
    except smtplib.SMTPAuthenticationError as exc:
        return False, f"Authentifizierung fehlgeschlagen: {exc.smtp_error.decode(errors='replace') if isinstance(exc.smtp_error, bytes) else exc.smtp_error}"
    except smtplib.SMTPException as exc:
        return False, f"SMTP-Fehler: {exc}"
    except Exception as exc:  # noqa: BLE001
        return False, f"Unerwarteter Fehler: {exc}"


def verify_smtp_credentials(
    email_address: str,
    password: str,
    candidates: Iterable[SmtpCandidate] | None = None,
    timeout: float = 10.0,
) -> SmtpVerifyResult:
    """Verifiziert E-Mail + Passwort gegen die Kandidatenliste.

    Liefert den ersten erfolgreichen Treffer zurück. Bei Misserfolg wird der
    letzte Fehlertext plus ggf. ein Provider-Hinweis (App-Passwort) gemeldet.
    """
    email_norm = str(email_address or "").strip()
    if not email_norm or not password:
        return SmtpVerifyResult(ok=False, candidate=None, error="E-Mail oder Passwort fehlt", provider_hint=None)

    if candidates is None:
        candidates = discover_smtp_servers(email_norm)
    candidates = list(candidates)
    if not candidates:
        return SmtpVerifyResult(
            ok=False,
            candidate=None,
            error="Kein passender SMTP-Server für die Domain gefunden.",
            provider_hint=provider_hint_for(email_norm),
        )

    last_error: str | None = None
    saw_auth_error = False
    for candidate in candidates:
        ok, err = _try_smtp_login(candidate, email_norm, password, timeout=timeout)
        if ok:
            return SmtpVerifyResult(ok=True, candidate=candidate, error=None, provider_hint=None)
        last_error = err
        if err and "Authentifizierung" in err:
            saw_auth_error = True

    hint = provider_hint_for(email_norm) if saw_auth_error else None
    return SmtpVerifyResult(ok=False, candidate=None, error=last_error, provider_hint=hint)

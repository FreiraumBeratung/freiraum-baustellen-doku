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
from typing import Callable, Iterable

logger = logging.getLogger(__name__)

# Test-Hook: MX-Hosts mocken (Smoke-Tests ohne echten DNS-Lookup).
_mx_lookup_override: Callable[[str], list[str]] | None = None


@dataclass
class SmtpCandidate:
    host: str
    port: int
    use_tls: bool
    use_ssl: bool
    source: str  # "preset", "mx" oder "guess"


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

# MX-Host-Fragment -> ein oder mehrere SMTP-Server (Reihenfolge = Priorität).
_MX_SMTP_HINTS: tuple[tuple[tuple[str, ...], tuple[tuple[str, int, bool, bool], ...]], ...] = (
    (("aspmx.l.google.com", "google.com", "googlemail.com"), (("smtp.gmail.com", 587, True, False),)),
    (("mail.protection.outlook.com", "outlook.com", "microsoft.com"), (("smtp.office365.com", 587, True, False),)),
    (
        ("exchange.ionos.eu", "ionos.de", "ionos.com", "1and1.de", "1und1.de", "ui-dns.de", "kundenserver.de"),
        (
            ("smtp.exchange.ionos.eu", 587, True, False),
            ("smtp.ionos.de", 587, True, False),
        ),
    ),
    (("strato.de", "rzone.de"), (("smtp.strato.de", 587, True, False),)),
    (("kasserver.com",), (("smtp.kasserver.com", 587, True, False),)),
    (("secureserver.net",), (("smtpout.secureserver.net", 587, True, False),)),
    (("hosteurope.de", "he.net", "hosting.zone"), (("smtp.hosteurope.de", 587, True, False),)),
    (("mailbox.org",), (("smtp.mailbox.org", 587, True, False),)),
    (("posteo.de", "posteo.net"), (("posteo.de", 587, True, False),)),
    (("netcup.net",), (("mx.netcup.net", 587, True, False),)),
    (("mcdns.net", "mittwald.de"), (("smtp.mittwald.de", 587, True, False),)),
)


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
        "die Zwei-Faktor-Authentifizierung aktiv ist. Bitte unter "
        "account.microsoft.com/security ein App-Passwort erstellen und hier "
        "statt dem normalen Passwort verwenden."
    ),
    "live.com": (
        "Bei Microsoft (Live) ist häufig ein App-Passwort erforderlich, wenn "
        "die Zwei-Faktor-Authentifizierung aktiv ist. Bitte unter "
        "account.microsoft.com/security ein App-Passwort erstellen."
    ),
    "live.de": (
        "Bei Microsoft (Live) ist häufig ein App-Passwort erforderlich, wenn "
        "die Zwei-Faktor-Authentifizierung aktiv ist. Bitte unter "
        "account.microsoft.com/security ein App-Passwort erstellen."
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


def _lookup_mx_hosts(domain: str) -> list[str]:
    """MX-Records der Domain (Hostnamen, lowercase). Leer bei Fehler/Timeout."""
    if _mx_lookup_override is not None:
        return _mx_lookup_override(domain)

    domain = str(domain or "").strip().lower().rstrip(".")
    if not domain:
        return []

    try:
        import dns.resolver

        resolver = dns.resolver.Resolver()
        resolver.lifetime = 4.0
        answers = resolver.resolve(domain, "MX")
        hosts: list[str] = []
        for rdata in answers:
            host = str(rdata.exchange).rstrip(".").lower()
            if host:
                hosts.append(host)
        return hosts
    except Exception:
        logger.debug("MX lookup failed for domain %s", domain, exc_info=True)
        return []


def _candidates_from_mx(domain: str) -> list[SmtpCandidate]:
    mx_hosts = _lookup_mx_hosts(domain)
    if not mx_hosts:
        return []

    mx_blob = " ".join(mx_hosts)
    out: list[SmtpCandidate] = []
    seen: set[tuple[str, int]] = set()
    for needles, smtp_list in _MX_SMTP_HINTS:
        if not any(needle in mx_blob for needle in needles):
            continue
        for host, port, use_tls, use_ssl in smtp_list:
            key = (host, port)
            if key in seen:
                continue
            seen.add(key)
            out.append(SmtpCandidate(host=host, port=port, use_tls=use_tls, use_ssl=use_ssl, source="mx"))
    return out


def _append_candidate(
    out: list[SmtpCandidate],
    seen_keys: set[tuple[str, int]],
    host: str,
    port: int,
    use_tls: bool,
    use_ssl: bool,
    source: str,
) -> None:
    key = (host, port)
    if key in seen_keys:
        return
    seen_keys.add(key)
    out.append(SmtpCandidate(host=host, port=port, use_tls=use_tls, use_ssl=use_ssl, source=source))


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
    1. Preset (wenn Domain bekannt, z. B. web.de / hotmail.de → smtp.office365.com)
    2. MX-Inferenz (Firmendomain gehostet bei IONOS, Strato, Microsoft 365, …)
    3. Domain-Guess nur wenn KEIN Preset existiert (sonst z. B. smtp.hotmail.de → DNS-Fail)
       - smtp.<domain>:587 STARTTLS
       - mail.<domain>:587 STARTTLS
       - smtp.<domain>:465 SSL
    """
    domain = _domain_from_email(email_address)
    out: list[SmtpCandidate] = []
    if not domain:
        return out

    seen_keys: set[tuple[str, int]] = set()

    preset = _PRESETS.get(domain)
    if preset:
        host, port, use_tls, use_ssl = preset
        _append_candidate(out, seen_keys, host, port, use_tls, use_ssl, "preset")

    for candidate in _candidates_from_mx(domain):
        _append_candidate(out, seen_keys, candidate.host, candidate.port, candidate.use_tls, candidate.use_ssl, candidate.source)

    # Bei bekannten Providern keine Domain-Guesses: smtp.hotmail.de existiert nicht
    # und überschreibt sonst die Fehlermeldung von smtp.office365.com.
    if preset is None:
        guesses: tuple[tuple[str, int, bool, bool], ...] = (
            (f"smtp.{domain}", 587, True, False),
            (f"mail.{domain}", 587, True, False),
            (f"smtp.{domain}", 465, False, True),
        )
        for host, port, use_tls, use_ssl in guesses:
            _append_candidate(out, seen_keys, host, port, use_tls, use_ssl, "guess")

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
        err_text = str(exc).lower()
        if "name or service not known" in err_text or "getaddrinfo failed" in err_text:
            return False, f"Mail-Server {candidate.host} nicht erreichbar (DNS)."
        return False, f"Netzwerkfehler: {exc}"
    except smtplib.SMTPAuthenticationError as exc:
        return False, f"Authentifizierung fehlgeschlagen: {exc.smtp_error.decode(errors='replace') if isinstance(exc.smtp_error, bytes) else exc.smtp_error}"
    except smtplib.SMTPException as exc:
        return False, f"SMTP-Fehler: {exc}"
    except Exception as exc:  # noqa: BLE001
        return False, f"Unerwarteter Fehler: {exc}"


def _error_priority(candidate: SmtpCandidate, err: str) -> int:
    """Niedriger = bevorzugter Fehlertext für die UI."""
    if "Authentifizierung" in err:
        return 0
    if candidate.source == "guess":
        return 40
    if "nicht erreichbar (DNS)" in err:
        return 20
    if "Netzwerkfehler" in err:
        return 10
    return 15


def verify_smtp_credentials(
    email_address: str,
    password: str,
    candidates: Iterable[SmtpCandidate] | None = None,
    timeout: float = 10.0,
) -> SmtpVerifyResult:
    """Verifiziert E-Mail + Passwort gegen die Kandidatenliste.

    Liefert den ersten erfolgreichen Treffer zurück. Bei Misserfolg wird ein
    sinnvoller Fehlertext (Preset/MX vor Domain-Guess) plus Provider-Hinweis gemeldet.
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

    best_error: str | None = None
    best_rank = 999
    saw_auth_error = False
    saw_dns_error = False
    for candidate in candidates:
        ok, err = _try_smtp_login(candidate, email_norm, password, timeout=timeout)
        if ok:
            return SmtpVerifyResult(ok=True, candidate=candidate, error=None, provider_hint=None)
        if not err:
            continue
        if "Authentifizierung" in err:
            saw_auth_error = True
        if "nicht erreichbar (DNS)" in err or "Name or service not known" in err:
            saw_dns_error = True
        rank = _error_priority(candidate, err)
        if rank < best_rank:
            best_rank = rank
            best_error = err

    domain = _domain_from_email(email_norm)
    hint = provider_hint_for(email_norm)
    tried_ionos = any(c.host in ("smtp.exchange.ionos.eu", "smtp.ionos.de") for c in candidates)
    if not hint and saw_auth_error and tried_ionos:
        hint = (
            "Bitte das Mail-Passwort prüfen (nicht das IONOS-Kundenlogin). "
            "Volle E-Mail-Adresse als Benutzername verwenden."
        )
    # Firmen-Domain-Hinweis nur bei unbekannten Domains — nicht bei Hotmail/Outlook-Presets.
    if not hint and saw_dns_error and not saw_auth_error and domain not in _PRESETS:
        hint = (
            "Für Ihre Firmen-Domain konnte kein Mail-Server ermittelt werden. "
            "Bitte prüfen Sie, ob SMTP-Versand bei Ihrem Mail-Provider aktiv ist."
        )
    return SmtpVerifyResult(ok=False, candidate=None, error=best_error, provider_hint=hint)

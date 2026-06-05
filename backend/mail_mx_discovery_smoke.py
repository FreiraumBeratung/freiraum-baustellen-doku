"""Smoke Welle Mail-MX: SMTP-Erkennung für gehostete Firmendomains (IONOS, Strato, …)."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from app.services import mail_autodiscover  # noqa: E402


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def _mock_mx(hosts_by_domain: dict[str, list[str]]):
    def lookup(domain: str) -> list[str]:
        return list(hosts_by_domain.get(domain.lower(), []))

    mail_autodiscover._mx_lookup_override = lookup  # type: ignore[attr-defined]


# -- 1. Preset-Domains unverändert ------------------------------------------
_mock_mx({})
web = mail_autodiscover.discover_smtp_servers("foo@web.de")
_expect(web[0].source == "preset" and web[0].host == "smtp.web.de", "web.de preset")

# -- 2. IONOS-Firmendomain (MX -> smtp.ionos.de vor Domain-Guess) ------------
_mock_mx({"freiraum-unternehmensberatung.de": ["mx00.ionos.de", "mx01.ionos.de"]})
ionos_firma = mail_autodiscover.discover_smtp_servers("info@freiraum-unternehmensberatung.de")
_expect(any(c.source == "mx" and c.host == "smtp.ionos.de" for c in ionos_firma), "IONOS MX fehlt")
ionos_idx = next(i for i, c in enumerate(ionos_firma) if c.host == "smtp.ionos.de")
guess_idx = next(i for i, c in enumerate(ionos_firma) if c.source == "guess")
_expect(ionos_idx < guess_idx, "smtp.ionos.de muss vor Domain-Guess kommen")

# -- 3. Strato-Firmendomain ---------------------------------------------------
_mock_mx({"mueller-gartenbau.de": ["mx.strato.de"]})
strato = mail_autodiscover.discover_smtp_servers("info@mueller-gartenbau.de")
_expect(any(c.source == "mx" and c.host == "smtp.strato.de" for c in strato), "Strato MX fehlt")

# -- 4. Microsoft 365 Custom Domain -------------------------------------------
_mock_mx({"beispiel-handwerk.de": ["beispiel-handwerk-de.mail.protection.outlook.com"]})
m365 = mail_autodiscover.discover_smtp_servers("buero@beispiel-handwerk.de")
_expect(any(c.source == "mx" and c.host == "smtp.office365.com" for c in m365), "M365 MX fehlt")

# -- 5. Unbekannte Domain: weiterhin Domain-Guess als Fallback ----------------
_mock_mx({"beispielfirma.eu": []})
unknown = mail_autodiscover.discover_smtp_servers("foo@beispielfirma.eu")
_expect(any(c.host == "smtp.beispielfirma.eu" for c in unknown), "guess fallback fehlt")
_expect(all(c.source != "mx" for c in unknown), "ohne MX kein mx-Kandidat")

# -- 6. Optional: Live-DNS IONOS-Domain (wenn Netzwerk verfügbar) -----------
mail_autodiscover._mx_lookup_override = None  # type: ignore[attr-defined]
live = mail_autodiscover.discover_smtp_servers("info@freiraum-unternehmensberatung.de")
if any(c.source == "mx" and c.host == "smtp.ionos.de" for c in live):
    print("[smoke] live DNS: freiraum-unternehmensberatung.de -> smtp.ionos.de OK")
else:
    print("[smoke] live DNS: übersprungen oder MX nicht erreichbar (kein harter Fehler)")

print("MAIL-MX-DISCOVERY-SMOKE: OK")

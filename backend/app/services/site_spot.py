"""Optionaler Ort/Laterne-Zusatz zur Baustelle — nur für explizit freigeschaltete Mandanten.

Liegt getrennt von ``notes`` und dem Rohtext. Wird nicht in die Tätigkeitserkennung
eingespeist. Andere Mandanten speichern und sehen das Feld nicht.
"""

from __future__ import annotations

from typing import Any

# Stadt / Laterne 1–3 — bewusst eine harte Allowlist, keine globale UI.
SITE_SPOT_TENANT_IDS = frozenset({"5431c9e2-2160-4441-ae92-b6a6840b3245"})
SITE_SPOT_MAX_LEN = 80


def site_spot_enabled_for_tenant(tenant_id: str | None) -> bool:
    return str(tenant_id or "").strip() in SITE_SPOT_TENANT_IDS


def normalize_site_spot(raw: str | None) -> str:
    if raw is None:
        return ""
    text = " ".join(str(raw).split())
    if len(text) > SITE_SPOT_MAX_LEN:
        text = text[:SITE_SPOT_MAX_LEN].rstrip()
    return text


def site_spot_for_create(tenant_id: str | None, incoming: str | None) -> str:
    if not site_spot_enabled_for_tenant(tenant_id):
        return ""
    return normalize_site_spot(incoming)


def site_spot_for_update(
    tenant_id: str | None,
    incoming: str | None,
    existing: str | None,
) -> str:
    """Andere Mandanten: eingehenden Wert verwerfen. Fehlt das Feld, Bestand behalten."""
    if not site_spot_enabled_for_tenant(tenant_id):
        return normalize_site_spot(existing)
    if incoming is None:
        return normalize_site_spot(existing)
    return normalize_site_spot(incoming)


def format_baustelle_display(
    report_or_name: dict[str, Any] | str | None = None,
    site_spot: str | None = None,
) -> str:
    if isinstance(report_or_name, dict):
        name = str(report_or_name.get("projectName") or "").strip()
        spot = normalize_site_spot(report_or_name.get("siteSpot"))
    else:
        name = str(report_or_name or "").strip()
        spot = normalize_site_spot(site_spot)
    if not name:
        name = "—"
    if spot:
        return f"{name} · {spot}"
    return name

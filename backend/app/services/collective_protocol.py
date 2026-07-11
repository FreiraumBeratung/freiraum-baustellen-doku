"""Gesamtprotokoll — kumulierte Begehungsprotokolle pro Baustelle (rein additiv).

Aggregiert vorhandene signed-Protokolle aus ``protocols.json`` zu einer View/PDF.
Einzelprotokolle bleiben unveraendert.
"""

from __future__ import annotations

from typing import Any

from app.services.site_protocol import protocol_display_text


def signed_protocols_for_project(
    protocols: list[dict[str, Any]],
    *,
    project_id: str,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in protocols:
        if not isinstance(item, dict):
            continue
        if str(item.get("projectId") or "") != str(project_id):
            continue
        if str(item.get("mode") or "") != "signed":
            continue
        out.append(item)
    out.sort(
        key=lambda p: (
            int(p.get("sequenceNumber") or 0),
            str(p.get("date") or ""),
            str(p.get("createdAt") or ""),
        )
    )
    return out


def _zeitraum_label(dates: list[str]) -> str:
    cleaned = sorted({d for d in dates if d})
    if not cleaned:
        return "—"
    if len(cleaned) == 1:
        return cleaned[0]
    return f"{cleaned[0]} – {cleaned[-1]}"


def build_collective_protocol_payload(
    project: dict[str, Any],
    protocols: list[dict[str, Any]],
) -> dict[str, Any]:
    """Baut den Gesamtprotokoll-Datensatz fuer eine Baustelle."""
    project_id = str(project.get("id") or "")
    signed = signed_protocols_for_project(protocols, project_id=project_id)
    entries: list[dict[str, Any]] = []
    dates: list[str] = []
    seq_nums: list[int] = []

    for p in signed:
        seq = p.get("sequenceNumber")
        if isinstance(seq, int) and seq > 0:
            seq_nums.append(seq)
        day = str(p.get("date") or "")
        if day:
            dates.append(day)
        entries.append(
            {
                "id": p.get("id"),
                "sequenceNumber": seq,
                "date": day,
                "participants": str(p.get("participants") or "").strip(),
                "text": protocol_display_text(p),
                "signatures": p.get("signatures"),
            }
        )

    customer = ""
    if signed:
        customer = str(signed[0].get("customerName") or "").strip()
    if not customer:
        customer = str(project.get("customer") or "").strip()

    company_name = ""
    if signed:
        company_name = str(signed[0].get("companyName") or "").strip()

    nr_label = ""
    if seq_nums:
        lo, hi = min(seq_nums), max(seq_nums)
        nr_label = f"Nr. {lo}" if lo == hi else f"Nr. {lo}–{hi}"

    return {
        "projectId": project_id,
        "projectName": str(project.get("name") or signed[0].get("projectName") if signed else project.get("name") or "—"),
        "customerName": customer or "—",
        "companyName": company_name,
        "visitCount": len(entries),
        "sequenceRange": nr_label,
        "dateRange": _zeitraum_label(dates),
        "entries": entries,
    }

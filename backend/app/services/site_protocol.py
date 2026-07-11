"""Baustellen-Protokoll (Schnellnotiz / Protokoll mit Unterschrift) — rein additiv."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from app.services.tenant_storage import TenantStore

PROTOCOL_MODES = frozenset({"quick", "signed"})


def read_protocols(store: TenantStore) -> list[dict[str, Any]]:
    data = store.read_json("protocols.json", {"protocols": []})
    return list(data.get("protocols") or [])


def write_protocols(store: TenantStore, protocols: list[dict[str, Any]]) -> None:
    store.write_json("protocols.json", {"protocols": protocols})


def find_protocol(store: TenantStore, protocol_id: str) -> dict[str, Any]:
    for item in read_protocols(store):
        if str(item.get("id") or "") == protocol_id:
            return item
    raise HTTPException(status_code=404, detail="Protokoll nicht gefunden")


def next_signed_sequence_number(store: TenantStore, project_id: str) -> int:
    nums: list[int] = []
    for item in read_protocols(store):
        if str(item.get("projectId") or "") != project_id:
            continue
        if str(item.get("mode") or "") != "signed":
            continue
        n = item.get("sequenceNumber")
        if isinstance(n, int) and n > 0:
            nums.append(n)
    return (max(nums) if nums else 0) + 1


def empty_signatures() -> dict[str, Any]:
    return {"customer": None, "employee": None}


def protocol_signatures_doc(protocol: dict[str, Any]) -> dict[str, Any]:
    raw = protocol.get("signatures")
    out = empty_signatures()
    if not isinstance(raw, dict):
        return out
    for role in ("customer", "employee"):
        entry = raw.get(role)
        if isinstance(entry, dict) and entry.get("filename"):
            out[role] = entry
    return out


def save_protocol_signatures(store: TenantStore, protocol_id: str, signatures: dict[str, Any]) -> None:
    protocols = read_protocols(store)
    for item in protocols:
        if str(item.get("id") or "") == protocol_id:
            item["signatures"] = signatures
            write_protocols(store, protocols)
            return
    raise HTTPException(status_code=404, detail="Protokoll nicht gefunden")


def protocol_display_text(protocol: dict[str, Any]) -> str:
    polished = str(protocol.get("polishedText") or "").strip()
    if polished:
        return polished
    return str(protocol.get("rawText") or "").strip()


def create_protocol_doc(
    store: TenantStore,
    *,
    company_name: str,
    company_logo_url: str | None,
    office_email: str,
    project_id: str,
    project_name: str,
    customer_name: str,
    date: str,
    mode: str,
    raw_text: str,
    polished_text: str,
    participants: str,
    export_format: str,
) -> dict[str, Any]:
    mode_norm = str(mode or "quick").strip().lower()
    if mode_norm not in PROTOCOL_MODES:
        raise HTTPException(status_code=400, detail="Ungültiger Protokoll-Modus.")

    raw = str(raw_text or "").strip()
    if len(raw) < 3:
        raise HTTPException(status_code=400, detail="Protokolltext ist zu kurz.")

    seq: int | None = None
    if mode_norm == "signed":
        seq = next_signed_sequence_number(store, project_id)

    doc = {
        "id": str(uuid.uuid4()),
        "companyId": store.tenant_id,
        "companyName": company_name,
        "companyLogoUrl": company_logo_url,
        "officeEmail": office_email,
        "projectId": project_id,
        "projectName": project_name,
        "customerName": customer_name,
        "date": date,
        "mode": mode_norm,
        "sequenceNumber": seq,
        "participants": str(participants or "").strip(),
        "rawText": raw,
        "polishedText": str(polished_text or "").strip(),
        "exportFormat": export_format if export_format in {"PDF", "Word"} else "PDF",
        "signatures": empty_signatures(),
        "photos": [],
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    protocols = read_protocols(store)
    protocols.append(doc)
    write_protocols(store, protocols)
    return doc


def protocol_photos_list(protocol: dict[str, Any]) -> list[dict[str, Any]]:
    raw = protocol.get("photos")
    if not isinstance(raw, list):
        return []
    return [p for p in raw if isinstance(p, dict)]


def save_protocol_photos(store: TenantStore, protocol_id: str, photos: list[dict[str, Any]]) -> None:
    protocols = read_protocols(store)
    for item in protocols:
        if str(item.get("id") or "") == protocol_id:
            item["photos"] = photos
            write_protocols(store, protocols)
            return
    raise HTTPException(status_code=404, detail="Protokoll nicht gefunden")


def delete_protocol_files(store: TenantStore, protocol: dict[str, Any], *, delete_photo_file, delete_signature_file) -> None:
    """Löscht zugehörige Upload-Dateien (Fotos, Unterschriften) — Callbacks aus main."""
    for entry in protocol_photos_list(protocol):
        fn = entry.get("filename")
        if isinstance(fn, str) and fn:
            delete_photo_file(store, fn)
    sigs = protocol_signatures_doc(protocol)
    for role in ("customer", "employee"):
        entry = sigs.get(role)
        if isinstance(entry, dict):
            delete_signature_file(store, entry.get("filename"))


def remove_protocol(store: TenantStore, protocol_id: str, *, delete_photo_file, delete_signature_file) -> None:
    protocols = read_protocols(store)
    target = next((p for p in protocols if str(p.get("id") or "") == protocol_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Protokoll nicht gefunden")
    delete_protocol_files(store, target, delete_photo_file=delete_photo_file, delete_signature_file=delete_signature_file)
    write_protocols(store, [p for p in protocols if str(p.get("id") or "") != protocol_id])


def update_protocol_polished(store: TenantStore, protocol_id: str, polished_text: str) -> dict[str, Any]:
    protocols = read_protocols(store)
    for item in protocols:
        if str(item.get("id") or "") == protocol_id:
            item["polishedText"] = str(polished_text or "").strip()
            write_protocols(store, protocols)
            return item
    raise HTTPException(status_code=404, detail="Protokoll nicht gefunden")

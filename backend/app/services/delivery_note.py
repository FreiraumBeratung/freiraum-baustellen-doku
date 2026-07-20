"""Lieferschein-Scan V1 — baustellenbezogen, Fotos → PDF → Büro. Rein additiv."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from app.services.tenant_storage import TenantStore

MAX_PAGES_PER_DELIVERY_NOTE = 8


def read_delivery_notes(store: TenantStore) -> list[dict[str, Any]]:
    data = store.read_json("delivery_notes.json", {"deliveryNotes": []})
    return list(data.get("deliveryNotes") or [])


def write_delivery_notes(store: TenantStore, notes: list[dict[str, Any]]) -> None:
    store.write_json("delivery_notes.json", {"deliveryNotes": notes})


def find_delivery_note(store: TenantStore, note_id: str) -> dict[str, Any]:
    for item in read_delivery_notes(store):
        if str(item.get("id") or "") == note_id:
            return item
    raise HTTPException(status_code=404, detail="Lieferschein nicht gefunden")


def delivery_note_photos_list(note: dict[str, Any]) -> list[dict[str, Any]]:
    raw = note.get("photos")
    if not isinstance(raw, list):
        return []
    return [p for p in raw if isinstance(p, dict)]


def save_delivery_note_photos(store: TenantStore, note_id: str, photos: list[dict[str, Any]]) -> None:
    notes = read_delivery_notes(store)
    for item in notes:
        if str(item.get("id") or "") == note_id:
            item["photos"] = photos
            write_delivery_notes(store, notes)
            return
    raise HTTPException(status_code=404, detail="Lieferschein nicht gefunden")


def create_delivery_note_doc(
    store: TenantStore,
    *,
    company_name: str,
    company_logo_url: str | None,
    office_email: str,
    project_id: str,
    project_name: str,
    customer_name: str,
    date: str,
    note: str = "",
) -> dict[str, Any]:
    pid = str(project_id or "").strip()
    if not pid:
        raise HTTPException(status_code=400, detail="Baustelle fehlt.")
    pname = str(project_name or "").strip() or "Baustelle"
    day = str(date or "").strip()
    if not day:
        day = datetime.now(timezone.utc).date().isoformat()

    doc = {
        "id": str(uuid.uuid4()),
        "companyId": store.tenant_id,
        "companyName": company_name,
        "companyLogoUrl": company_logo_url,
        "officeEmail": office_email,
        "projectId": pid,
        "projectName": pname,
        "customerName": str(customer_name or "").strip(),
        "date": day,
        "note": str(note or "").strip()[:500],
        "photos": [],
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    notes = read_delivery_notes(store)
    notes.append(doc)
    write_delivery_notes(store, notes)
    return doc


def remove_delivery_note(
    store: TenantStore,
    note_id: str,
    *,
    delete_photo_file,
) -> None:
    notes = read_delivery_notes(store)
    target = next((n for n in notes if str(n.get("id") or "") == note_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Lieferschein nicht gefunden")
    for entry in delivery_note_photos_list(target):
        fn = entry.get("filename")
        if isinstance(fn, str) and fn:
            delete_photo_file(store, fn)
    write_delivery_notes(store, [n for n in notes if str(n.get("id") or "") != note_id])

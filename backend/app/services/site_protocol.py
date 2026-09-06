"""Baustellen-Protokoll (Schnellnotiz / Protokoll mit Unterschrift / Gedankensammlung) — rein additiv."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import HTTPException

from app.services.tenant_storage import TenantStore

PROTOCOL_MODES = frozenset({"quick", "signed", "thoughts"})
# Fester Baustellen-Platzhalter: Gedankensammlung ist bewusst nicht baustellengebunden.
THOUGHTS_PROJECT_ID = "__gedankensammlung__"
THOUGHTS_PROJECT_NAME = "Gedankensammlung"
BERLIN = ZoneInfo("Europe/Berlin")


def is_thoughts_mode(mode: str | None) -> bool:
    return str(mode or "").strip().lower() == "thoughts"


def protocol_kind_label(protocol: dict[str, Any]) -> str:
    mode = str(protocol.get("mode") or "quick")
    seq = protocol.get("sequenceNumber")
    if mode == "signed" and isinstance(seq, int) and seq > 0:
        return f"Begehungsprotokoll Nr. {seq}"
    if mode == "signed":
        return "Begehungsprotokoll"
    if mode == "thoughts":
        return "Gedankensammlung"
    return "Schnellnotiz"


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


def find_open_thoughts_day_draft(store: TenantStore, date: str) -> dict[str, Any] | None:
    """Offener Tages-Entwurf der Gedankensammlung (noch nicht ans Büro gesendet)."""
    want = str(date or "").strip()
    if not want:
        return None
    candidates: list[dict[str, Any]] = []
    for item in read_protocols(store):
        if not is_thoughts_mode(str(item.get("mode") or "")):
            continue
        if str(item.get("date") or "").strip() != want:
            continue
        if not item.get("dayDraft"):
            continue
        if str(item.get("officeSentAt") or "").strip():
            continue
        candidates.append(item)
    if not candidates:
        return None
    candidates.sort(key=lambda p: str(p.get("updatedAt") or p.get("createdAt") or ""), reverse=True)
    return candidates[0]


def _append_thoughts_chunk(existing: dict[str, Any], *, raw: str, polished: str) -> dict[str, Any]:
    stamp = datetime.now(BERLIN).strftime("%H:%M")
    sep = f"\n\n—— {stamp} ——\n\n"
    prev_raw = str(existing.get("rawText") or "").strip()
    prev_pol = str(existing.get("polishedText") or "").strip() or prev_raw
    new_raw = str(raw or "").strip()
    new_pol = str(polished or "").strip() or new_raw
    existing["rawText"] = f"{prev_raw}{sep}{new_raw}" if prev_raw else new_raw
    existing["polishedText"] = f"{prev_pol}{sep}{new_pol}" if prev_pol else new_pol
    existing["updatedAt"] = datetime.now(timezone.utc).isoformat()
    existing["dayDraft"] = True
    return existing


def mark_protocol_office_sent(store: TenantStore, protocol_id: str) -> dict[str, Any] | None:
    protocols = read_protocols(store)
    for item in protocols:
        if str(item.get("id") or "") != protocol_id:
            continue
        item["officeSentAt"] = datetime.now(timezone.utc).isoformat()
        item["updatedAt"] = item["officeSentAt"]
        write_protocols(store, protocols)
        return item
    return None


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

    pid = str(project_id or "").strip()
    pname = str(project_name or "").strip()
    cname = str(customer_name or "").strip()
    parts = str(participants or "").strip()
    date_norm = str(date or "").strip()
    polished = str(polished_text or "").strip() or raw

    # Gedankensammlung: immer ohne echte Baustelle (additiv, signed/quick unverändert).
    if mode_norm == "thoughts":
        pid = THOUGHTS_PROJECT_ID
        pname = THOUGHTS_PROJECT_NAME
        cname = ""
        parts = ""
        # Offenen Tages-Entwurf erweitern statt viele Einzelmails zu erzeugen.
        open_draft = find_open_thoughts_day_draft(store, date_norm)
        if open_draft is not None:
            protocols = read_protocols(store)
            for item in protocols:
                if str(item.get("id") or "") == str(open_draft.get("id") or ""):
                    _append_thoughts_chunk(item, raw=raw, polished=polished)
                    write_protocols(store, protocols)
                    return item
    elif not pid:
        raise HTTPException(status_code=400, detail="Baustelle fehlt.")

    seq: int | None = None
    if mode_norm == "signed":
        seq = next_signed_sequence_number(store, pid)

    now = datetime.now(timezone.utc).isoformat()
    doc: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "companyId": store.tenant_id,
        "companyName": company_name,
        "companyLogoUrl": company_logo_url,
        "officeEmail": office_email,
        "projectId": pid,
        "projectName": pname,
        "customerName": cname,
        "projectAddress": "",
        "projectCity": "",
        "date": date_norm,
        "mode": mode_norm,
        "sequenceNumber": seq,
        "participants": parts,
        "rawText": raw,
        "polishedText": polished,
        "exportFormat": export_format if export_format in {"PDF", "Word"} else "PDF",
        "signatures": empty_signatures(),
        "photos": [],
        "createdAt": now,
        "updatedAt": now,
    }
    if mode_norm != "thoughts" and pid:
        projects = store.read_json("projects.json", {"projects": []})
        for p in projects.get("projects") or []:
            if not isinstance(p, dict):
                continue
            if str(p.get("id") or "") != pid:
                continue
            doc["projectAddress"] = str(p.get("address") or "").strip()
            doc["projectCity"] = str(p.get("city") or "").strip()
            if not cname:
                doc["customerName"] = str(p.get("customer") or "").strip()
            break
    if mode_norm == "thoughts":
        doc["dayDraft"] = True
        doc["officeSentAt"] = None
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


def protocol_entrepreneur_display_name(protocol: dict[str, Any], company_profile: dict[str, Any] | None = None) -> str:
    prof = company_profile if isinstance(company_profile, dict) else {}
    return (
        str(prof.get("contactPerson") or "").strip()
        or str(prof.get("companyName") or "").strip()
        or str(protocol.get("companyName") or "").strip()
    )


def protocol_partner_display_name(protocol: dict[str, Any]) -> str:
    return str(protocol.get("participants") or "").strip()


def protocol_for_pdf_signatures(protocol: dict[str, Any], company_profile: dict[str, Any]) -> dict[str, Any]:
    """Kopie mit korrekten Namen unter den Unterschriften für die PDF."""
    entrepreneur = protocol_entrepreneur_display_name(protocol, company_profile)
    partner = protocol_partner_display_name(protocol)
    sigs = protocol_signatures_doc(protocol)
    out_sigs: dict[str, Any] = {"customer": sigs.get("customer"), "employee": sigs.get("employee")}
    if isinstance(out_sigs.get("customer"), dict) and entrepreneur:
        entry = dict(out_sigs["customer"])
        entry["signedByLabel"] = entrepreneur
        out_sigs["customer"] = entry
    if isinstance(out_sigs.get("employee"), dict) and partner:
        entry = dict(out_sigs["employee"])
        entry["signedByLabel"] = partner
        out_sigs["employee"] = entry
    out = dict(protocol)
    out["signatures"] = out_sigs
    return out


def update_protocol_polished(store: TenantStore, protocol_id: str, polished_text: str) -> dict[str, Any]:
    protocols = read_protocols(store)
    for item in protocols:
        if str(item.get("id") or "") == protocol_id:
            item["polishedText"] = str(polished_text or "").strip()
            write_protocols(store, protocols)
            return item
    raise HTTPException(status_code=404, detail="Protokoll nicht gefunden")

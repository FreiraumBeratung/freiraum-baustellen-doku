"""Hebel 2: Telemetrie fuer nicht erkannte Sprach-Saetze.

Speichert pro Mandant (ueber TenantStore, daher automatisch test-isoliert) die
Roh-Saetze, deren Chunks zu keiner Taetigkeit kanonisiert werden konnten. Dient
ausschliesslich dem Lernen aus echtem Baustellen-Sprech.

Strikt best-effort: jede Funktion faengt Fehler ab und beeinflusst die
Berichts-Strukturierung in keiner Weise.
"""

from __future__ import annotations

import datetime
from typing import Any

_FILE = "speech_telemetry.json"
_MAX_ENTRIES = 500


def record_unmatched_speech(
    store: Any,
    *,
    raw_text: str,
    unmatched: list[str],
    meta: dict[str, Any] | None = None,
) -> None:
    """Haengt einen Telemetrie-Eintrag an die mandantenspezifische Datei an.

    Tut nichts, wenn keine unerkannten Chunks vorliegen oder ein Fehler auftritt.
    """
    try:
        cleaned = [str(x).strip() for x in (unmatched or []) if str(x).strip()]
        if not cleaned:
            return
        existing = store.read_json(_FILE, [])
        if not isinstance(existing, list):
            existing = []
        existing.append(
            {
                "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "rawText": str(raw_text or ""),
                "unmatched": cleaned,
                "meta": dict(meta or {}),
            }
        )
        if len(existing) > _MAX_ENTRIES:
            existing = existing[-_MAX_ENTRIES:]
        store.write_json(_FILE, existing)
    except Exception:
        # Telemetrie darf den Request niemals stoeren.
        return

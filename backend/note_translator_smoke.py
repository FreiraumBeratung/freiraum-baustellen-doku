"""Smoke: Notiz-Übersetzer (Stichpunkte) — Sprach-Sätze bleiben unberührt."""

from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path

os.environ["OPENAI_API_KEY"] = ""
os.environ["FREIRAUM_AI_STRUCTURING"] = ""

from smoke_isolation import isolate_smoke_data

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_notes_")))

from app.services.note_translator import expand_notes_if_guarded, looks_like_notes  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402
from main import StructureReportBody, api_structure_report  # noqa: E402

_STORE = TenantStore(str(uuid.uuid4()))

CUSTOMER_RAW = """Laterne 1

2qm Pflaster
1 Std. Handschachtung
5 Meter Kabel"""


def _structure(raw: str) -> dict:
    body = StructureReportBody(
        projectId="p-notes",
        projectName="Kundenbaustelle",
        customerName="Testkunde",
        date="2026-09-16",
        employeeNames=["Max"],
        startTime="07:00",
        endTime="16:00",
        exportFormat="PDF",
        rawText=raw,
    )
    return (api_structure_report(body, store=_STORE).get("structured") or {})


def _joined(items: object) -> str:
    return " ".join(str(x) for x in (items or [])).casefold()


def main() -> int:
    assert looks_like_notes(CUSTOMER_RAW) is True
    speech = "Heute haben wir fünfzig Quadratmeter Pflaster verlegt und danach die Hecke geschnitten."
    assert looks_like_notes(speech) is False
    assert expand_notes_if_guarded(speech) == speech

    s1 = _structure(CUSTOMER_RAW)
    acts = _joined(s1.get("activities"))
    summary = str(s1.get("summary") or "")
    assert "Keine Angabe" not in summary, summary
    assert "pflaster" in acts and "verlegt" in acts, s1.get("activities")
    assert "kabel" in acts, s1.get("activities")
    assert "handschacht" in acts, s1.get("activities")
    assert "laterne" not in acts, s1.get("activities")
    assert "2qm Pflaster" in str(s1.get("rawText") or "")

    s2 = _structure("3 m Randstein\n10 m² Splitt")
    acts2 = _joined(s2.get("activities"))
    assert "randstein" in acts2 and "gesetzt" in acts2, s2.get("activities")
    assert "splitt" in acts2, s2.get("activities")
    assert "Keine Angabe" not in str(s2.get("summary") or "")

    s3 = _structure("8 m KG-Rohr\n2 m³ Schotter")
    acts3 = _joined(s3.get("activities"))
    assert "rohr" in acts3, s3.get("activities")
    assert "schotter" in acts3, s3.get("activities")
    assert "Keine Angabe" not in str(s3.get("summary") or "")

    s4 = _structure(speech)
    acts4 = _joined(s4.get("activities"))
    assert "pflaster" in acts4 and "verlegt" in acts4, s4.get("activities")
    assert "hecke" in acts4, s4.get("activities")

    print("NOTE-TRANSLATOR-SMOKE: OK")
    print("customer activities:", s1.get("activities"))
    print("customer summary:", s1.get("summary"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

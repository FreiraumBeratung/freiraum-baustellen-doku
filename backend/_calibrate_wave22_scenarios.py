"""Einmal-Kalibrierung für Welle-22-Szenarien (nicht in Regression)."""
from __future__ import annotations

import os
import sys
import tempfile
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ["OPENAI_API_KEY"] = ""
os.environ["FREIRAUM_AI_STRUCTURING"] = ""

from main import StructureReportBody, api_structure_report  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402
from priority_p123_wave22_scenarios import SCENARIOS  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp()))
store = TenantStore(str(uuid.uuid4()))

for trade, specs in SCENARIOS.items():
    for i, spec in enumerate(specs, 1):
        raw = spec["raw"]
        out = api_structure_report(
            StructureReportBody(
                projectId="c",
                projectName="T",
                customerName="K",
                date="2026-07-29",
                employeeNames=["M"],
                startTime="08:00",
                endTime="16:00",
                exportFormat="PDF",
                rawText=raw,
            ),
            store=store,
        )
        s = out.get("structured") or {}
        print(
            f"{trade}_{i:02d}",
            "acts",
            s.get("activities"),
            "mats",
            s.get("materials"),
            "prob",
            s.get("problems"),
            "open",
            s.get("openItems"),
            "cust",
            (s.get("customerTalk") or "")[:55],
        )

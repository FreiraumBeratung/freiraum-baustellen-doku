"""Kalibriert pilot_real_speech_wave51 Szenarien (N-Variante) — nur Dev-Hilfe."""
from __future__ import annotations

import os
import sys
import tempfile
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ["OPENAI_API_KEY"] = ""

from main import StructureReportBody, api_structure_report  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402
from pilot_real_speech_wave51_scenarios import all_base_scenarios  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="cal_w51_")))
store = TenantStore(str(uuid.uuid4()))

for i, spec in enumerate(all_base_scenarios(), 1):
    out = api_structure_report(
        StructureReportBody(
            projectId="cal-w51",
            projectName="Schmitz Außenanlage",
            customerName="K",
            date="2026-07-11",
            employeeNames=["M"],
            startTime="08:00",
            endTime="16:00",
            exportFormat="PDF",
            rawText=spec["raw"],
        ),
        store=store,
    )
    s = out.get("structured") or {}
    print(
        f"{i:02d}",
        "acts=", s.get("activities"),
        "| mats=", s.get("materials"),
        "| prob=", s.get("problems"),
        "| open=", s.get("openItems"),
        "| msug=", s.get("machineSuggestions"),
    )

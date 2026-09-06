"""Folgebericht / Sammelbericht (kumulierte Berichterstattung pro Baustellen-Durchlauf).

Rein additiv: bestehende Tagesbericht-Logik bleibt unberuehrt. Ein "Run"/Durchlauf
buendelt mehrere Tagesberichte einer Baustelle. Der Gesamtbericht ist eine reine
Aggregation (View) ueber vorhandene Berichte in `reports.json` — es gibt KEINE
parallele Speicherung, damit nichts auseinanderlaeuft.

Alle Kernfunktionen sind pur (ohne Storage/HTTP), damit sie isoliert testbar sind.
"""

from __future__ import annotations

from typing import Any

from app.services.time_account import compute_booked_hours, work_time_for_employee

VALID_PROJECT_STATUS = {"aktiv", "pausiert", "abgeschlossen"}


def ensure_open_run(project: dict[str, Any], *, now_iso: str, new_run_id: str) -> str:
    """Stellt sicher, dass die Baustelle einen offenen Durchlauf hat und gibt dessen ID zurueck.

    Mutiert ``project`` additiv (neue Felder ``currentRunId``/``runStartedAt``).
    Hat die Baustelle bereits einen offenen Run, wird dieser fortgesetzt.
    """
    rid = str(project.get("currentRunId") or "").strip()
    if rid:
        return rid
    project["currentRunId"] = new_run_id
    project["runStartedAt"] = now_iso
    # Ein neuer Durchlauf reaktiviert eine abgeschlossene Baustelle.
    if str(project.get("status") or "") == "abgeschlossen" or not project.get("status"):
        project["status"] = "aktiv"
    return new_run_id


def close_run(project: dict[str, Any], *, now_iso: str) -> dict[str, Any]:
    """Schliesst den offenen Durchlauf der Baustelle (Status -> abgeschlossen).

    Mutiert ``project`` additiv. Gibt Infos zum geschlossenen Run zurueck.
    """
    rid = str(project.get("currentRunId") or "").strip() or None
    started = project.get("runStartedAt")
    project["status"] = "abgeschlossen"
    project["lastClosedRunId"] = rid
    project["lastClosedRunStartedAt"] = started
    project["lastClosedRunClosedAt"] = now_iso
    project["currentRunId"] = None
    return {"runId": rid, "runStartedAt": started, "runClosedAt": now_iso}


def resolve_run_id(project: dict[str, Any], requested: str | None) -> str | None:
    """Ermittelt die anzuzeigende Run-ID: explizit angefragt, sonst aktueller, sonst letzter."""
    req = str(requested or "").strip()
    if req:
        return req
    cur = str(project.get("currentRunId") or "").strip()
    if cur:
        return cur
    last = str(project.get("lastClosedRunId") or "").strip()
    return last or None


def _as_list(v: Any) -> list[str]:
    if not isinstance(v, list):
        return []
    return [str(x).strip() for x in v if str(x).strip()]


def _dedupe(seq: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in seq:
        key = item.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def reports_for_run(
    reports: list[dict[str, Any]], *, project_id: str, run_id: str | None
) -> list[dict[str, Any]]:
    """Liefert die Tagesberichte eines Durchlaufs, chronologisch sortiert.

    Ist ``run_id`` gesetzt, wird strikt danach gefiltert. Ohne ``run_id`` werden
    alle Berichte der Baustelle genommen (Fallback fuer Alt-Berichte ohne runId).
    """
    out: list[dict[str, Any]] = []
    for r in reports:
        if not isinstance(r, dict):
            continue
        if str(r.get("projectId") or "") != str(project_id):
            continue
        if run_id is not None and str(r.get("runId") or "") != str(run_id):
            continue
        out.append(r)
    out.sort(key=lambda r: (str(r.get("date") or ""), str(r.get("createdAt") or "")))
    return out


def _day_hours(report: dict[str, Any]) -> float:
    hours = compute_booked_hours(
        str(report.get("startTime") or ""),
        str(report.get("endTime") or ""),
        int(report.get("breakMinutes") if report.get("breakMinutes") is not None else 0),
    )
    return float(hours or 0.0)


def _employee_day_hours(report: dict[str, Any], employee_id: str) -> float:
    start, end, br = work_time_for_employee(report, employee_id)
    hours = compute_booked_hours(start, end, br)
    if hours is None:
        return _day_hours(report)
    return float(hours)


def build_collective_payload(
    project: dict[str, Any],
    reports: list[dict[str, Any]],
    *,
    run_id: str | None,
) -> dict[str, Any]:
    """Aggregiert die Tagesberichte eines Durchlaufs zu einem Gesamtbericht-Datensatz.

    Reine Funktion: kein Storage, keine Foto-Aufloesung (URLs setzt der Aufrufer).
    """
    pid = str(project.get("id") or "")
    run_reports = reports_for_run(reports, project_id=pid, run_id=run_id)

    days: list[dict[str, Any]] = []
    all_materials: list[str] = []
    all_open: list[str] = []
    all_problems: list[str] = []
    all_activities: list[str] = []
    hours_by_emp: dict[str, float] = {}
    total_hours = 0.0
    photos: list[dict[str, Any]] = []
    signatures: list[dict[str, Any]] = []

    for r in run_reports:
        st = r.get("structured") if isinstance(r.get("structured"), dict) else {}
        acts = _as_list(st.get("activities"))
        mats = _as_list(st.get("materials"))
        probs = _as_list(st.get("problems"))
        opens = _as_list(st.get("openItems"))
        notes = str(r.get("notes") or "").strip()
        ktalk = str(st.get("customerTalk") or "").strip()
        day_summary = str(st.get("summary") or "").strip()
        emps = _as_list(r.get("employees"))
        emp_ids = _as_list(r.get("employeeIds"))
        day_h = _day_hours(r)
        total_hours += day_h
        for idx, name in enumerate(emps):
            eid = emp_ids[idx] if idx < len(emp_ids) else ""
            person_h = _employee_day_hours(r, eid) if eid else day_h
            hours_by_emp[name] = round(hours_by_emp.get(name, 0.0) + person_h, 2)

        all_materials.extend(mats)
        all_open.extend(opens)
        all_problems.extend(probs)
        all_activities.extend(acts)

        for ph in (r.get("photos") or []):
            if isinstance(ph, dict) and ph.get("filename"):
                photos.append(
                    {
                        "reportId": r.get("id"),
                        "date": r.get("date"),
                        "filename": ph.get("filename"),
                        "originalFilename": ph.get("originalFilename"),
                        "contentType": ph.get("contentType"),
                    }
                )

        sig_doc = r.get("signatures") if isinstance(r.get("signatures"), dict) else {}
        for role in ("customer", "employee"):
            entry = sig_doc.get(role)
            if isinstance(entry, dict) and entry.get("filename"):
                signatures.append(
                    {
                        "reportId": r.get("id"),
                        "date": str(r.get("date") or ""),
                        "role": role,
                        "filename": entry.get("filename"),
                        "signedByLabel": entry.get("signedByLabel"),
                        "signedAt": entry.get("signedAt"),
                    }
                )

        days.append(
            {
                "reportId": r.get("id"),
                "date": str(r.get("date") or ""),
                "employees": emps,
                "startTime": r.get("startTime"),
                "endTime": r.get("endTime"),
                "breakMinutes": r.get("breakMinutes"),
                "hours": round(day_h, 2),
                "activities": acts,
                "materials": mats,
                "problems": probs,
                "openItems": opens,
                "notes": notes,
                "customerTalk": ktalk,
                "summary": day_summary,
            }
        )

    dates = [d["date"] for d in days if d["date"]]
    date_from = min(dates) if dates else ""
    date_to = max(dates) if dates else ""

    customer_name = ""
    company_name = ""
    office_email = ""
    company_logo_url = None
    for r in run_reports:
        customer_name = customer_name or str(r.get("customerName") or "")
        company_name = company_name or str(r.get("companyName") or "")
        office_email = office_email or str(r.get("officeEmail") or "")
        if company_logo_url is None and r.get("companyLogoUrl"):
            company_logo_url = r.get("companyLogoUrl")

    deterministic_summary = _build_deterministic_summary(
        project_name=str(project.get("name") or ""),
        date_from=date_from,
        date_to=date_to,
        day_count=len(days),
        total_hours=total_hours,
        activities=_dedupe(all_activities),
        days=days,
    )

    return {
        "projectId": pid,
        "projectName": str(project.get("name") or ""),
        "customerName": customer_name or str(project.get("customer") or ""),
        "address": str(project.get("address") or ""),
        "companyName": company_name,
        "officeEmail": office_email,
        "companyLogoUrl": company_logo_url,
        "runId": run_id,
        "runStartedAt": project.get("runStartedAt") or project.get("lastClosedRunStartedAt"),
        "status": str(project.get("status") or ""),
        "dateFrom": date_from,
        "dateTo": date_to,
        "days": days,
        "totals": {
            "reportCount": len(days),
            "totalHours": round(total_hours, 2),
            "hoursByEmployee": [
                {"name": name, "hours": round(h, 2)}
                for name, h in sorted(hours_by_emp.items(), key=lambda kv: kv[0].casefold())
            ],
            "materials": _dedupe(all_materials),
            "openItems": _dedupe(all_open),
            "problems": _dedupe(all_problems),
            "activities": _dedupe(all_activities),
        },
        "summary": deterministic_summary,
        "photos": photos,
        "signatures": signatures,
    }


def _fmt_date_de(date_str: str) -> str:
    s = str(date_str or "").strip()
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        return f"{s[8:10]}.{s[5:7]}.{s[0:4]}"
    return s or "—"


def _fmt_hours_de(hours: float) -> str:
    return f"{hours:.2f}".replace(".", ",")


def _build_deterministic_summary(
    *,
    project_name: str,
    date_from: str,
    date_to: str,
    day_count: int,
    total_hours: float,
    activities: list[str],
    days: list[dict[str, Any]] | None = None,
) -> str:
    """Deterministische Gesamt-Zusammenfassung, die tatsaechlich ueber alle Tage
    kombiniert (Fallback, wenn keine KI-Formulierung verfuegbar ist)."""
    if day_count == 0:
        return "Keine Angabe"
    if date_from and date_to and date_from != date_to:
        zeitraum = f"Zeitraum {_fmt_date_de(date_from)} bis {_fmt_date_de(date_to)}"
    else:
        zeitraum = f"am {_fmt_date_de(date_from or date_to)}"
    parts: list[str] = []
    head = f"Baustelle {project_name}".strip() if project_name else "Baustelle"
    parts.append(
        f"{head}: {zeitraum}, {day_count} Arbeitstag(e), insgesamt {_fmt_hours_de(total_hours)} Stunden."
    )
    # Pro-Tag-Verlauf zusammenfuehren, damit der Text wirklich alle Tage abbildet.
    day_lines: list[str] = []
    for day in days or []:
        if not isinstance(day, dict):
            continue
        d_label = _fmt_date_de(str(day.get("date") or ""))
        acts = _as_list(day.get("activities"))
        recap = "; ".join(acts[:4]) if acts else (str(day.get("summary") or "").strip() or "—")
        day_lines.append(f"{d_label}: {recap}")
    if day_lines:
        parts.append("Verlauf: " + " | ".join(day_lines) + ".")
    elif activities:
        parts.append("Ausgefuehrte Arbeiten: " + "; ".join(activities[:8]) + ".")
    return " ".join(parts)

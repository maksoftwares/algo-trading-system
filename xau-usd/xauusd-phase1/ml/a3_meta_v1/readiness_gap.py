from __future__ import annotations

import csv
import json
import math
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_READINESS_GAP_REPORT.json"
SCHEMA_VERSION = "a3_ml_readiness_gap_report_v1"


def generate_readiness_gap_report(root: Path, report_json: Path | None = None) -> Path:
    root = root.resolve()
    reports = root / "outputs" / "reports"
    report_json = (report_json or reports / "A3_ML_READINESS_GAP_REPORT.json").resolve()
    pointer = _read_json(reports / "C02_DATASET_POINTER.json")
    c03 = _read_json(reports / "C03_TRAINING_READINESS_REPORT.json")
    c01 = _read_json(reports / "C02_C01_DATA_AUDIT.json")
    slippage = _read_json(reports / "C02_SLIPPAGE_READINESS.json")
    export = _read_json(reports / "C02_BAR_TICK_EXPORT_REPORT.json")
    decisions_path = Path(pointer.get("c02_labeled_decisions_csv", reports / "C02_LABELED_DECISIONS.csv"))
    decisions = _decision_coverage(decisions_path)
    gate_gaps = _gate_gaps(c03)
    slippage_gap = _slippage_gap(slippage)
    export_coverage = _export_coverage(export)
    backfill = _backfill_assessment(decisions, export_coverage, gate_gaps)
    status = _status(c03, gate_gaps, backfill)
    payload = {
        "status": status,
        "stage": "C11-READINESS-GAP",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": pointer.get("dataset_version", c03.get("dataset_version", "")),
        "c03_status": c03.get("status", "MISSING"),
        "decision_coverage": decisions,
        "c01_snapshot": {
            "status": c01.get("status", "MISSING"),
            "snapshot_rows": c01.get("raw_source_row_counts", {}).get("snapshot_rows", 0),
            "exact_unique_signals": c01.get("raw_source_row_counts", {}).get("exact_unique_signals", 0),
            "candidate_trainable_groups": c01.get("labeled_and_trainable_setup_groups", {}).get("candidate_trainable_groups", 0),
            "selected_features": len(c01.get("selected_features", [])),
            "regime_balance": c01.get("regime_balance", {}),
        },
        "gate_gaps": gate_gaps,
        "slippage_gap": slippage_gap,
        "export_coverage": export_coverage,
        "backfill_assessment": backfill,
        "boundary": {
            "mt5_connection_attempted": False,
            "data_export_attempted": False,
            "terminal_runtime_change_authorized": False,
            "model_training_authorized": False,
            "python_demo_predictions_authorized": False,
            "broker_action_authorized": False,
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
        },
        "next_actions": _next_actions(status, gate_gaps, backfill),
    }
    _write_status(report_json, payload)
    _update_pointer(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", payload)
    return report_json


def render_readiness_gap_report_md(payload: dict[str, Any]) -> str:
    gap_rows = [
        {
            "Gate": item.get("gate", ""),
            "Passed": str(item.get("passed", False)).lower(),
            "Observed": item.get("observed", ""),
            "Required": item.get("required", ""),
            "Gap": item.get("gap_text", ""),
        }
        for item in payload.get("gate_gaps", [])
    ]
    account_rows = [
        {
            "Account": item.get("account_label", ""),
            "Entry": item.get("entry_fills", ""),
            "SL": item.get("sl_exits", ""),
            "TP": item.get("tp_exits", ""),
            "Request": item.get("request_price_resolved", ""),
            "Status": item.get("slippage_status", ""),
        }
        for item in payload.get("slippage_gap", {}).get("accounts", [])
    ]
    coverage_rows = [
        {
            "Account": item.get("account_label", ""),
            "Bars": item.get("bar_range", ""),
            "Tick Days": item.get("tick_days_with_rows", ""),
            "Tick Rows": item.get("tick_rows", ""),
        }
        for item in payload.get("export_coverage", {}).get("accounts", [])
    ]
    next_lines = "\n".join(f"- {item}" for item in payload.get("next_actions", [])) or "- none"
    return "\n".join(
        [
            "# A3 ML Readiness Gap Report",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            f"C03 status: {payload.get('c03_status', '')}",
            "",
            "## Decision Coverage",
            "",
            f"- Rows: {payload['decision_coverage'].get('rows', 0)}",
            f"- Min decision UTC: {payload['decision_coverage'].get('min_decision_utc', '')}",
            f"- Max decision UTC: {payload['decision_coverage'].get('max_decision_utc', '')}",
            f"- Active span weeks: {payload['decision_coverage'].get('active_span_weeks', 0)}",
            "",
            "## Gate Gaps",
            "",
            _table(gap_rows, ["Gate", "Passed", "Observed", "Required", "Gap"]) if gap_rows else "No C03 gates found.",
            "",
            "## Slippage Gap",
            "",
            f"- Overall status: {payload.get('slippage_gap', {}).get('status', 'MISSING')}",
            _table(account_rows, ["Account", "Entry", "SL", "TP", "Request", "Status"]) if account_rows else "No slippage account rows.",
            "",
            "## Export Coverage",
            "",
            _table(coverage_rows, ["Account", "Bars", "Tick Days", "Tick Rows"]) if coverage_rows else "No export coverage rows.",
            "",
            "## Backfill Assessment",
            "",
            f"- Verdict: {payload.get('backfill_assessment', {}).get('verdict', '')}",
            f"- Detail: {payload.get('backfill_assessment', {}).get('detail', '')}",
            f"- Estimated earliest C03 active-weeks date: {payload.get('backfill_assessment', {}).get('estimated_active_weeks_pass_date_utc', '')}",
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Data export attempted: false.",
            "- Terminal runtime change authorized: false.",
            "- Model training authorized: false.",
            "- Python demo predictions authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Next Actions",
            "",
            next_lines,
            "",
        ]
    )


def _gate_gaps(c03: dict[str, Any]) -> list[dict[str, Any]]:
    gaps = []
    for check in c03.get("checks", []):
        observed = str(check.get("observed", ""))
        required = str(check.get("required", ""))
        observed_number = _number(observed)
        required_number = _number(required)
        gap_value: float | None = None
        if observed_number is not None and required_number is not None and ">=" in required:
            gap_value = max(0.0, required_number - observed_number)
        gaps.append(
            {
                "gate": check.get("gate", ""),
                "passed": bool(check.get("passed")),
                "observed": observed,
                "required": required,
                "gap_value": gap_value,
                "gap_text": _gap_text(check.get("gate", ""), gap_value, observed, required),
            }
        )
    return gaps


def _slippage_gap(slippage: dict[str, Any]) -> dict[str, Any]:
    requirements = slippage.get("requirements", {})
    accounts = []
    for account in slippage.get("accounts", []):
        row = dict(account)
        row["deficits_if_per_account"] = {
            key: max(0, int(requirements.get(key, 0)) - int(account.get(key, 0) or 0))
            for key in ("entry_fills", "sl_exits", "tp_exits", "request_price_resolved")
        }
        accounts.append(row)
    totals = {
        key: sum(int(account.get(key, 0) or 0) for account in slippage.get("accounts", []))
        for key in ("entry_fills", "sl_exits", "tp_exits", "request_price_resolved")
    }
    total_deficits = {key: max(0, int(requirements.get(key, 0)) - totals.get(key, 0)) for key in totals}
    return {
        "status": slippage.get("status", "MISSING"),
        "requirements": requirements,
        "totals": totals,
        "total_deficits": total_deficits,
        "accounts": accounts,
    }


def _decision_coverage(path: Path) -> dict[str, Any]:
    rows = _read_csv(path)
    times = [_parse_time(row.get("decision_time", "") or row.get("decision_time_utc", "")) for row in rows]
    times = [item for item in times if item is not None]
    min_time = min(times) if times else None
    max_time = max(times) if times else None
    span_days = ((max_time - min_time).total_seconds() / 86400.0) if min_time and max_time else 0.0
    return {
        "path": str(path),
        "rows": len(rows),
        "min_decision_utc": _iso(min_time) if min_time else "",
        "max_decision_utc": _iso(max_time) if max_time else "",
        "active_span_days": round(span_days, 4),
        "active_span_weeks": round(span_days / 7.0, 4),
    }


def _export_coverage(export: dict[str, Any]) -> dict[str, Any]:
    accounts = []
    for record in export.get("account_records", []):
        bars = record.get("coverage", {}).get("bars", {})
        m5 = bars.get("M5", {})
        chunks = record.get("coverage", {}).get("ticks", {}).get("chunks", [])
        tick_rows = sum(int(chunk.get("row_count", 0) or 0) for chunk in chunks)
        tick_days = sum(1 for chunk in chunks if int(chunk.get("row_count", 0) or 0) > 0)
        accounts.append(
            {
                "account_label": record.get("account_label", ""),
                "status": record.get("status", ""),
                "bar_range": _range_text(m5.get("min_time_utc", ""), m5.get("max_time_utc", "")),
                "m5_rows": int(m5.get("row_count", 0) or 0),
                "tick_days_with_rows": tick_days,
                "tick_rows": tick_rows,
            }
        )
    return {
        "status": export.get("status", "MISSING"),
        "requested_start_utc": export.get("requested_start_utc", ""),
        "snapshot_cutoff_utc": export.get("snapshot_cutoff_utc", ""),
        "accounts": accounts,
    }


def _backfill_assessment(decisions: dict[str, Any], export_coverage: dict[str, Any], gaps: list[dict[str, Any]]) -> dict[str, Any]:
    active_gap = next((item for item in gaps if item.get("gate") == "active_weeks"), {})
    setup_gap = next((item for item in gaps if item.get("gate") == "market_setup_groups"), {})
    remaining_weeks = float(active_gap.get("gap_value") or 0.0)
    max_time = _parse_time(decisions.get("max_decision_utc", ""))
    estimated_date = max_time + timedelta(weeks=remaining_weeks) if max_time and remaining_weeks > 0 else None
    requested_start = _parse_time(export_coverage.get("requested_start_utc", ""))
    min_decision = _parse_time(decisions.get("min_decision_utc", ""))
    older_export_exists = bool(requested_start and min_decision and requested_start < min_decision)
    if remaining_weeks > 0 and older_export_exists:
        verdict = "OLDER_MARKET_HISTORY_EXISTS_BUT_NO_OLDER_USABLE_DECISIONS"
        detail = "MT5 market history begins before the first labeled decision, so bars/ticks alone are not enough; older EA decision logs or more live observer time are needed."
    elif remaining_weeks > 0:
        verdict = "NEEDS_MORE_ACTIVE_DECISION_TIME"
        detail = "The active-weeks gate is still short; collect more A1/A2/A3 decisions/fills or import older compatible decision logs."
    elif float(setup_gap.get("gap_value") or 0.0) > 0:
        verdict = "NEEDS_MORE_MARKET_SETUP_GROUPS"
        detail = "Calendar span is enough, but setup-group count is still short."
    else:
        verdict = "NO_BACKFILL_GAP_DETECTED"
        detail = "C03 blockers are not calendar/setup-count related."
    return {
        "verdict": verdict,
        "detail": detail,
        "remaining_active_weeks": round(remaining_weeks, 4),
        "estimated_active_weeks_pass_date_utc": _iso(estimated_date) if estimated_date else "",
        "older_market_history_before_first_decision": older_export_exists,
    }


def _status(c03: dict[str, Any], gaps: list[dict[str, Any]], backfill: dict[str, Any]) -> str:
    if c03.get("status") == "PASS":
        return "C03_PASS"
    if backfill.get("verdict") == "OLDER_MARKET_HISTORY_EXISTS_BUT_NO_OLDER_USABLE_DECISIONS":
        return "WAITING_FOR_DECISION_HISTORY"
    if any(not item.get("passed") for item in gaps):
        return "GAP_REMAINS"
    return "UNKNOWN"


def _next_actions(status: str, gaps: list[dict[str, Any]], backfill: dict[str, Any]) -> list[str]:
    actions = []
    if status == "C03_PASS":
        return ["Run C10 with --publish to publish the EA handoff if C05/C04/C06 are ready."]
    if backfill.get("older_market_history_before_first_decision"):
        actions.append("Import older compatible EA decision/observer logs if available; market bars/ticks alone cannot satisfy active decision weeks.")
    actions.append("Keep A1/A2/A3 terminals collecting passive observer data and rerun C10 with --refresh-live-readonly after new market sessions.")
    active_gap = next((item for item in gaps if item.get("gate") == "active_weeks"), {})
    setup_gap = next((item for item in gaps if item.get("gate") == "market_setup_groups"), {})
    if active_gap.get("gap_value"):
        actions.append(f"Need about {float(active_gap['gap_value']):.2f} more active weeks unless older compatible decisions are imported.")
    if setup_gap.get("gap_value"):
        actions.append(f"Need about {int(math.ceil(float(setup_gap['gap_value'])))} more market setup groups.")
    return actions


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_readiness_gap_report_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c11_readiness_gap_report"] = payload["outputs"]["status_report_json"]
    pointer["c11_readiness_gap_status"] = payload["status"]
    pointer["python_demo_predictions_authorized"] = False
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)


def _read_json(path_or_text: str | Path) -> dict[str, Any]:
    if not path_or_text:
        return {}
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _parse_time(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _number(value: str) -> float | None:
    match = re.search(r"-?\d+(?:\.\d+)?", value)
    return float(match.group(0)) if match else None


def _gap_text(gate: str, gap_value: float | None, observed: str, required: str) -> str:
    if gap_value is None:
        return "needs different category/state" if observed != required else "none"
    if gate in {"market_setup_groups", "feature_budget", "minority_labels"}:
        return str(int(math.ceil(gap_value)))
    if gate == "active_weeks":
        return f"{gap_value:.2f} weeks"
    return f"{gap_value:g}"


def _range_text(start: str, end: str) -> str:
    if not start and not end:
        return ""
    return f"{start} to {end}"

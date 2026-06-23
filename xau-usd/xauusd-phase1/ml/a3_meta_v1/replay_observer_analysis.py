from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .market_data_export import _table, _utc_now, _write_json_atomic, parse_utc


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_REPLAY_OBSERVER_ANALYSIS_STATUS.json"
DEFAULT_C56_JSON = Path("outputs") / "reports" / "A3_ML_REPLAY_IMPORT_STATUS.json"
DEFAULT_C03_JSON = Path("outputs") / "reports" / "C03_TRAINING_READINESS_REPORT.json"
DEFAULT_C01_JSON = Path("outputs") / "reports" / "C02_C01_DATA_AUDIT.json"
STATUS_READY = "REPLAY_OBSERVER_ANALYSIS_READY_RESEARCH_ONLY"
STATUS_BLOCKED = "REPLAY_OBSERVER_ANALYSIS_BLOCKED"
SCHEMA_VERSION = "a3_ml_replay_observer_analysis_status_v1"
SOURCE_TYPE = "strategy_tester_replay"
LABEL_STATUS = "REPLAY_OBSERVER_ONLY"


def analyze_replay_observer_evidence(
    root: Path,
    report_json: Path | None = None,
    *,
    c56_json: Path | None = None,
    c03_json: Path | None = None,
    c01_json: Path | None = None,
) -> Path:
    root = root.resolve()
    reports = root / "outputs" / "reports"
    pointer_path = reports / "C02_DATASET_POINTER.json"
    pointer = _read_json(pointer_path)
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    c56 = _read_json(c56_json or root / DEFAULT_C56_JSON)
    c03 = _read_json(c03_json or root / DEFAULT_C03_JSON)
    c01 = _read_json(c01_json or root / DEFAULT_C01_JSON)
    replay_csv = Path(str(c56.get("outputs", {}).get("quarantined_observer_csv") or pointer.get("c56_replay_quarantined_observer_csv", "")))
    replay_rows = _read_csv(replay_csv)
    market_groups = _read_csv(Path(str(pointer.get("market_setup_groups_csv", ""))))
    labeled_decisions = _read_csv(Path(str(pointer.get("c02_labeled_decisions_csv", reports / "C02_LABELED_DECISIONS.csv"))))
    safety = _safety_checks(c56, replay_rows)
    status = STATUS_READY if safety["passed"] and replay_rows else STATUS_BLOCKED
    would_rows = [row for row in replay_rows if _bool(row.get("would_signal"))]
    payload = {
        "status": status,
        "stage": "C57-REPLAY-OBSERVER-ANALYSIS",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": pointer.get("dataset_version", c56.get("dataset_version", "")),
        "selected_lane_id": c56.get("selected_lane_id", ""),
        "analysis_scope": "research_only_quarantined_replay_observer",
        "source_type": SOURCE_TYPE,
        "label_status": LABEL_STATUS,
        "safety": safety,
        "usefulness_summary": _usefulness_summary(replay_rows, would_rows),
        "duplicate_overlap": _duplicate_overlap(would_rows, market_groups, labeled_decisions),
        "setup_buckets": _setup_buckets(would_rows),
        "feature_and_contract_notes": _feature_and_contract_notes(replay_rows, would_rows, c01),
        "live_data_needed": _live_data_needed(c03, c01),
        "inputs": {
            "c56_replay_import": str(c56_json or root / DEFAULT_C56_JSON),
            "c03_training_readiness": str(c03_json or root / DEFAULT_C03_JSON),
            "c01_data_audit": str(c01_json or root / DEFAULT_C01_JSON),
            "quarantined_replay_csv": str(replay_csv),
            "market_setup_groups_csv": str(pointer.get("market_setup_groups_csv", "")),
            "c02_labeled_decisions_csv": str(pointer.get("c02_labeled_decisions_csv", "")),
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
        },
        "authorization": {
            "training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "boundary": {
            "model_training_attempted": False,
            "c03_rebuild_attempted": False,
            "label_promotion_attempted": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(pointer_path, payload)
    return report_json


def render_replay_observer_analysis_md(payload: dict[str, Any]) -> str:
    useful = payload.get("usefulness_summary", {})
    overlap = payload.get("duplicate_overlap", {})
    feature = payload.get("feature_and_contract_notes", {})
    needed = payload.get("live_data_needed", {})
    setup = payload.get("setup_buckets", {})
    safety_rows = [
        {"Check": item.get("check", ""), "Pass": str(item.get("passed", False)).lower(), "Detail": item.get("detail", "")}
        for item in payload.get("safety", {}).get("checks", [])
    ]
    need_rows = [
        {"Gate": item.get("gate", ""), "Observed": item.get("observed", ""), "Needed": item.get("needed", ""), "Action": item.get("action", "")}
        for item in needed.get("failed_gates", [])
    ]
    top_rows = [
        {"Bucket": item.get("bucket", ""), "Value": item.get("value", ""), "Rows": item.get("rows", 0)}
        for item in setup.get("top_buckets", [])
    ]
    return "\n".join(
        [
            "# A3 ML Replay Observer Analysis",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            f"Selected lane: {payload.get('selected_lane_id', '')}",
            f"Scope: {payload.get('analysis_scope', '')}",
            "",
            "## Safety",
            "",
            _table(safety_rows, ["Check", "Pass", "Detail"]) if safety_rows else "No safety checks.",
            "",
            "## Usefulness",
            "",
            f"- Replay signal rows: {useful.get('signal_rows', 0)}.",
            f"- Would-signal rows: {useful.get('would_signal_rows', 0)}.",
            f"- Research candidate rows: {useful.get('research_candidate_rows', 0)}.",
            f"- Date range UTC: {useful.get('first_timestamp_utc', '')} to {useful.get('last_timestamp_utc', '')}.",
            f"- Approx active weeks: {useful.get('active_weeks', 0)}.",
            f"- Direction balance: {useful.get('direction_balance', {})}.",
            "",
            "## Duplicate / Overlap",
            "",
            f"- Exact live setup overlap: {overlap.get('exact_live_setup_overlap_rows', 0)} rows.",
            f"- Exact live setup overlap pct: {overlap.get('exact_live_setup_overlap_pct', 0)}.",
            f"- Date-direction live overlap: {overlap.get('date_direction_overlap_rows', 0)} rows.",
            f"- Live labeled decision time overlap: {overlap.get('live_decision_time_overlap_rows', 0)} rows.",
            "",
            "## Setup Buckets",
            "",
            _table(top_rows, ["Bucket", "Value", "Rows"]) if top_rows else "No setup bucket rows.",
            "",
            "## Feature / Contract Notes",
            "",
            f"- Core replay feature missing rows: {feature.get('core_feature_missing_rows', {})}.",
            f"- C01 feature budget now: {feature.get('c01_global_feature_budget', 0)}.",
            f"- C01 missingness: {feature.get('c01_missingness', {})}.",
            f"- Contract note: {feature.get('contract_note', '')}",
            "",
            "## Live Data Still Needed",
            "",
            _table(need_rows, ["Gate", "Observed", "Needed", "Action"]) if need_rows else "No failed live-data gates.",
            "",
            "## Boundary",
            "",
            "- Model training attempted: false.",
            "- C03 rebuild attempted: false.",
            "- Label promotion attempted: false.",
            "- Training authorized: false.",
            "- Python demo predictions authorized: false.",
            "- EA consumption authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _safety_checks(c56: dict[str, Any], rows: list[dict[str, str]]) -> dict[str, Any]:
    checks = [
        _check("c56_import_quarantined", c56.get("status") == "REPLAY_OBSERVER_IMPORT_QUARANTINED", str(c56.get("status", "MISSING"))),
        _check("rows_present", bool(rows), str(len(rows))),
        _check("source_type_strategy_tester_replay", all(row.get("source_type") == SOURCE_TYPE for row in rows), SOURCE_TYPE),
        _check("label_status_replay_observer_only", all(row.get("label_status") == LABEL_STATUS for row in rows), LABEL_STATUS),
        _check("candidate_trainable_false", all(not _bool(row.get("candidate_trainable")) for row in rows), "all false"),
        _check("training_authorized_false", all(not _bool(row.get("training_authorized")) for row in rows), "all false"),
        _check("broker_action_authorized_false", all(not _bool(row.get("broker_action_authorized")) for row in rows), "all false"),
    ]
    return {"passed": all(check["passed"] for check in checks), "checks": checks}


def _usefulness_summary(rows: list[dict[str, str]], would_rows: list[dict[str, str]]) -> dict[str, Any]:
    timestamps = [_parse_time(row.get("timestamp_utc")) for row in rows]
    timestamps = [value for value in timestamps if value is not None]
    research_rows = [
        row
        for row in would_rows
        if _float(row.get("stop_distance_points")) > 0
        and _float(row.get("entry_price")) > 0
        and _float(row.get("stop_loss")) > 0
        and _float(row.get("take_profit")) > 0
        and _bool(row.get("dry_run"))
        and not _bool(row.get("broker_action_allowed"))
    ]
    return {
        "signal_rows": len(rows),
        "would_signal_rows": len(would_rows),
        "research_candidate_rows": len(research_rows),
        "first_timestamp_utc": _iso(min(timestamps)) if timestamps else "",
        "last_timestamp_utc": _iso(max(timestamps)) if timestamps else "",
        "active_weeks": round((max(timestamps) - min(timestamps)).total_seconds() / (7 * 24 * 3600), 2) if len(timestamps) >= 2 else 0,
        "direction_balance": dict(Counter(row.get("direction", "") for row in would_rows)),
        "reason_code_counts": dict(Counter(row.get("reason_code", "") for row in would_rows).most_common(10)),
    }


def _duplicate_overlap(
    would_rows: list[dict[str, str]],
    market_groups: list[dict[str, str]],
    labeled_decisions: list[dict[str, str]],
) -> dict[str, Any]:
    live_setup_keys = {_live_setup_key(row) for row in market_groups}
    live_setup_keys.discard("")
    live_date_direction = {_date_direction_key(row.get("retest_bar_time_utc"), row.get("direction")) for row in market_groups}
    live_date_direction.discard("")
    live_decision_time = {_decision_time_key(row) for row in labeled_decisions}
    live_decision_time.discard("")
    replay_keys = [_replay_setup_key(row) for row in would_rows]
    replay_date_direction = [_date_direction_key(row.get("m5_bar_time") or row.get("timestamp_utc"), row.get("direction")) for row in would_rows]
    replay_decision_time = [_date_direction_key(row.get("timestamp_utc"), row.get("direction")) for row in would_rows]
    exact_overlap = sum(1 for key in replay_keys if key and key in live_setup_keys)
    date_direction_overlap = sum(1 for key in replay_date_direction if key and key in live_date_direction)
    decision_time_overlap = sum(1 for key in replay_decision_time if key and key in live_decision_time)
    total = max(len(would_rows), 1)
    return {
        "exact_live_setup_overlap_rows": exact_overlap,
        "exact_live_setup_overlap_pct": round(exact_overlap / total, 6),
        "date_direction_overlap_rows": date_direction_overlap,
        "date_direction_overlap_pct": round(date_direction_overlap / total, 6),
        "live_decision_time_overlap_rows": decision_time_overlap,
        "live_decision_time_overlap_pct": round(decision_time_overlap / total, 6),
        "live_setup_groups_compared": len(live_setup_keys),
        "replay_would_signal_rows_compared": len(would_rows),
        "dedup_recommendation": "keep replay separate and cross-source-dedup before any future promotion",
    }


def _setup_buckets(would_rows: list[dict[str, str]]) -> dict[str, Any]:
    counters = {
        "session": Counter(_session_label(_parse_time(row.get("timestamp_utc"))) for row in would_rows),
        "hour_utc": Counter(str(_hour(_parse_time(row.get("timestamp_utc")))) for row in would_rows),
        "direction_session": Counter(f"{row.get('direction', '')}|{_session_label(_parse_time(row.get('timestamp_utc')))}" for row in would_rows),
        "trend_pair": Counter(f"{row.get('h1_trend', '')}|{row.get('h4_trend', '')}" for row in would_rows),
        "reason_code": Counter(row.get("reason_code", "") for row in would_rows),
        "cost_bucket": Counter(_cost_bucket(_float(row.get("estimated_cost_R"))) for row in would_rows),
    }
    top = []
    for bucket, counter in counters.items():
        for value, count in counter.most_common(8):
            top.append({"bucket": bucket, "value": value, "rows": count})
    return {"top_buckets": top}


def _feature_and_contract_notes(rows: list[dict[str, str]], would_rows: list[dict[str, str]], c01: dict[str, Any]) -> dict[str, Any]:
    core_fields = (
        "level_price",
        "entry_price",
        "stop_loss",
        "take_profit",
        "stop_distance_points",
        "estimated_cost_R",
        "dirstate_regime",
        "dirstate_strength",
        "h1_trend",
        "h4_trend",
    )
    missing = {
        field: sum(1 for row in would_rows if not str(row.get(field, "")).strip() or str(row.get(field, "")).strip() in {"0", "0.00", "0.0000"})
        for field in core_fields
    }
    return {
        "core_feature_missing_rows": missing,
        "c01_global_feature_budget": c01.get("global_feature_budget", 0),
        "c01_missingness": c01.get("missingness", {}),
        "contract_note": (
            "Replay rows are breakout_retest tier1-compatible observer evidence. They remain outside supervised labels "
            "until a separate promotion review defines features, weighting, and validation treatment."
        ),
    }


def _live_data_needed(c03: dict[str, Any], c01: dict[str, Any]) -> dict[str, Any]:
    failed = []
    for check in c03.get("checks", []):
        if check.get("passed"):
            continue
        gate = check.get("gate", "")
        observed = check.get("observed", "")
        failed.append({"gate": gate, "observed": observed, "needed": _needed(gate, observed, c01), "action": _action(gate, c01)})
    return {
        "c03_status": c03.get("status", "MISSING"),
        "failed_gates": failed,
        "training_authorized": False,
        "python_demo_predictions_authorized": False,
        "broker_action_authorized": False,
    }


def _needed(gate: str, observed: str, c01: dict[str, Any]) -> str:
    if gate == "market_setup_groups":
        return f"{max(300 - _int(observed), 0)} more live setup groups"
    if gate == "active_weeks":
        return f"{max(8.0 - _float(observed), 0):.2f} more live active weeks"
    if gate == "feature_budget":
        return f"{max(6 - _int(observed), 0)} more trainable feature slots"
    if gate == "at_least_two_regimes":
        return "at least one additional non-UNKNOWN live regime beyond current balance"
    if gate == "slippage_readiness":
        slip = c01.get("slippage_adequacy_status", {})
        return (
            f"entry fills {slip.get('entry_fills', 0)}/{slip.get('required_entry_fills', 200)}, "
            f"SL exits {slip.get('sl_exits', 0)}/{slip.get('required_sl_exits', 100)}, "
            f"TP exits {slip.get('tp_exits', 0)}/{slip.get('required_tp_exits', 50)}"
        )
    if gate == "dataset_status":
        return "C01 must reach EXPLORATORY_MODEL or higher on live/trainable evidence"
    return "gate-specific live evidence still required"


def _action(gate: str, c01: dict[str, Any]) -> str:
    actions = {
        "market_setup_groups": "keep A1/A2/A3 collecting live decisions; replay remains excluded from gate counts",
        "active_weeks": "continue live collection until span reaches 8 weeks or import separately reviewed live-compatible history",
        "feature_budget": "resolve label promotion/slippage gates before supervised features become trainable",
        "at_least_two_regimes": "wait for live data in another detected regime; do not synthesize regime diversity from replay",
        "slippage_readiness": "collect real fills/exits/request-price evidence; replay has no fills",
        "dataset_status": "keep C01 fail-closed until live evidence and labels meet exploratory thresholds",
    }
    return actions.get(gate, "review C03 gate and collect required live evidence")


def _live_setup_key(row: dict[str, str]) -> str:
    time = _norm_time(row.get("retest_bar_time_utc"))
    level = _price(row.get("normalized_level_price"))
    if not time or not level:
        return ""
    return "|".join([row.get("symbol", ""), row.get("direction", ""), time, level])


def _replay_setup_key(row: dict[str, str]) -> str:
    time = _norm_time(row.get("m5_bar_time"))
    level = _price(row.get("level_price"))
    if not time or not level:
        return ""
    return "|".join([row.get("symbol", ""), row.get("direction", ""), time, level])


def _decision_time_key(row: dict[str, str]) -> str:
    signal_id = str(row.get("signal_id", ""))
    parts = signal_id.split("|")
    direction = parts[3] if len(parts) > 3 else ""
    return _date_direction_key(row.get("decision_time"), direction)


def _date_direction_key(time_value: Any, direction: Any) -> str:
    parsed = _parse_time(time_value)
    if not parsed:
        return ""
    return f"{parsed.date().isoformat()}|{str(direction or '').strip()}"


def _norm_time(value: Any) -> str:
    parsed = _parse_time(value)
    return parsed.strftime("%Y-%m-%d %H:%M:%S") if parsed else ""


def _price(value: Any) -> str:
    numeric = _float(value)
    return f"{numeric:.2f}" if numeric else ""


def _session_label(value: datetime | None) -> str:
    hour = _hour(value)
    if hour is None:
        return "UNKNOWN"
    if 0 <= hour < 7:
        return "ASIA"
    if 7 <= hour < 13:
        return "LONDON"
    if 13 <= hour < 21:
        return "NEW_YORK"
    return "ROLLOVER"


def _hour(value: datetime | None) -> int | None:
    return value.hour if value else None


def _cost_bucket(value: float) -> str:
    if value <= 0.05:
        return "<=0.05R"
    if value <= 0.10:
        return "<=0.10R"
    if value <= 0.15:
        return "<=0.15R"
    if value <= 0.30:
        return "<=0.30R"
    return ">0.30R"


def _parse_time(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        if "." in text.split(" ", 1)[0]:
            return datetime.strptime(text, "%Y.%m.%d %H:%M:%S").replace(tzinfo=timezone.utc)
        return parse_utc(text)
    except (TypeError, ValueError):
        return None


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _next_allowed_stage(status: str) -> str:
    if status == STATUS_READY:
        return (
            "Use this analysis for reviewer planning only. Keep replay rows quarantined until a separate promotion review; "
            "continue collecting live A1/A2/A3 data for C03."
        )
    return "Fix C56 import/safety issues before analyzing replay evidence."


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_replay_observer_analysis_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c57_replay_observer_analysis_report"] = payload["outputs"]["status_report_json"]
    pointer["c57_replay_observer_analysis_status"] = payload["status"]
    pointer["training_authorized"] = False
    pointer["python_demo_predictions_authorized"] = False
    pointer["ea_consumption_authorized"] = False
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path or not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _read_json(path_or_text: str | Path) -> dict[str, Any]:
    if not path_or_text:
        return {}
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": name, "passed": bool(passed), "detail": detail}


def _bool(value: Any) -> bool:
    return str(value or "").strip().casefold() == "true"


def _float(value: Any) -> float:
    try:
        return float(str(value or "").strip())
    except (TypeError, ValueError):
        return 0.0


def _int(value: Any) -> int:
    try:
        return int(float(str(value or "").strip()))
    except (TypeError, ValueError):
        return 0

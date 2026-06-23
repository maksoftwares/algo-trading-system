from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "C03_TRAINING_READINESS_REPORT.json"


def generate_c03_training_readiness_report(root: Path, report_json: Path | None = None) -> Path:
    root = root.resolve()
    pointer = _load_pointer(root)
    c01 = _read_json(root / "outputs" / "reports" / "C02_C01_DATA_AUDIT.json")
    labels = _read_json(pointer.get("label_audit_report", ""))
    slippage = _read_json(pointer.get("slippage_readiness_report", ""))
    grouping = _read_json(pointer.get("signal_grouping_audit_report", ""))
    source_scope = _source_scope(c01, labels, slippage, grouping)
    checks = _checks(c01, labels, slippage, grouping, source_scope)
    passed = all(check["passed"] for check in checks)
    payload = {
        "status": "PASS" if passed else "NO_GO",
        "stage": "C03-READINESS",
        "created_at_utc": _utc_now(),
        "dataset_version": pointer["dataset_version"],
        "authorization": {
            "training_authorized": passed,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "source_scope": source_scope,
        "checks": checks,
        "next_allowed_stage": (
            "C04 purged walk-forward training scaffold"
            if passed
            else "continue evidence collection and rerun C02/C03 after more signals/fills"
        ),
    }
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    report_md = report_json.with_suffix(".md")
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_md.write_text(render_c03_readiness_md(payload), encoding="utf-8")
    pointer["c03_training_readiness_report"] = str(report_json)
    pointer["c03_training_readiness_status"] = payload["status"]
    pointer["training_authorized"] = passed
    pointer["python_demo_predictions_authorized"] = False
    _write_json_atomic(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", pointer)
    return report_json


def render_c03_readiness_md(payload: dict[str, Any]) -> str:
    rows = [
        {
            "Gate": check["gate"],
            "Passed": str(check["passed"]).lower(),
            "Observed": check["observed"],
            "Required": check["required"],
        }
        for check in payload["checks"]
    ]
    return "\n".join(
        [
            "# C03 Training Readiness Report",
            "",
            f"Overall status: {payload['status']}",
            "",
            "## Authorization",
            "",
            f"- Training authorized: {str(payload['authorization']['training_authorized']).lower()}",
            f"- Python demo predictions authorized: {str(payload['authorization']['python_demo_predictions_authorized']).lower()}",
            f"- EA consumption authorized: {str(payload['authorization']['ea_consumption_authorized']).lower()}",
            f"- Broker action authorized: {str(payload['authorization']['broker_action_authorized']).lower()}",
            "",
            "## Gates",
            "",
            _table(rows, ["Gate", "Passed", "Observed", "Required"]),
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _checks(
    c01: dict[str, Any],
    labels: dict[str, Any],
    slippage: dict[str, Any],
    grouping: dict[str, Any],
    source_scope: dict[str, Any],
) -> list[dict[str, Any]]:
    prefer_live_only = bool(source_scope.get("non_live_source_present", False))
    label_counts = _gate_counts(labels, prefer_live_only)
    grouping_counts = _gate_counts(grouping, prefer_live_only)
    active_weeks = _active_weeks(c01, prefer_live_only)
    regimes = set(_balance(c01, "regime_balance", prefer_live_only)) - {"UNKNOWN", ""}
    directions = set(_balance(c01, "direction_balance", prefer_live_only)) - {""}
    c01_class = _balance(c01, "class_balance", prefer_live_only)
    c01_status = _gate_value(c01, "status", prefer_live_only, missing="NON_LIVE_SOURCE_PRESENT_LIVE_ONLY_STATUS_MISSING")
    feature_budget = _int(_gate_value(c01, "global_feature_budget", prefer_live_only, missing=0))
    leakage_violations = _gate_value(c01, "leakage_violations", prefer_live_only, missing=["LIVE_ONLY_LEAKAGE_MISSING"])
    slippage_status = _gate_value(slippage, "status", prefer_live_only, missing="NON_LIVE_SOURCE_PRESENT_LIVE_ONLY_STATUS_MISSING")
    return [
        _check("dataset_status", c01_status in {"EXPLORATORY_MODEL", "CANDIDATE_MODEL", "MATURE_MODEL"}, c01_status, "EXPLORATORY_MODEL or higher"),
        _check("market_setup_groups", grouping_counts.get("market_setup_groups", 0) >= 300, grouping_counts.get("market_setup_groups", 0), ">=300"),
        _check("minority_labels", min(label_counts.get("positive", 0), label_counts.get("negative", 0)) >= 90, min(label_counts.get("positive", 0), label_counts.get("negative", 0)), ">=90"),
        _check("active_weeks", active_weeks >= 8, f"{active_weeks:.2f}", ">=8"),
        _check("both_directions", len(directions) >= 2, ",".join(sorted(directions)), "LONG and SHORT"),
        _check("at_least_two_regimes", len(regimes) >= 2, ",".join(sorted(regimes)) or "none", ">=2 non-UNKNOWN regimes"),
        _check("feature_budget", feature_budget >= 6, feature_budget, ">=6"),
        _check("slippage_readiness", slippage_status == "ADEQUATE", slippage_status, "ADEQUATE"),
        _check("leakage", len(leakage_violations) == 0, len(leakage_violations), "0"),
    ]


def _check(gate: str, passed: bool, observed: Any, required: str) -> dict[str, Any]:
    return {"gate": gate, "passed": bool(passed), "observed": str(observed), "required": required}


def _active_weeks(c01: dict[str, Any], prefer_live_only: bool = False) -> float:
    fold_diagnostics = _fold_diagnostics(c01, prefer_live_only)
    times = []
    for fold in fold_diagnostics:
        for key in ("train_start_utc", "test_end_utc"):
            value = fold.get(key)
            if value:
                times.append(_parse_time(value))
    if not times:
        return 0.0
    return max((max(times) - min(times)).total_seconds() / (7 * 24 * 3600), 0.0)


def _source_scope(*reports: dict[str, Any]) -> dict[str, Any]:
    source_counts: dict[str, int] = {}
    for report in reports:
        for key in ("source_type_counts", "source_counts"):
            value = report.get(key, {})
            if isinstance(value, dict):
                for source, count in value.items():
                    source_counts[str(source)] = source_counts.get(str(source), 0) + _int(count)
        by_source = report.get("counts_by_source_type", {})
        if isinstance(by_source, dict):
            for source, value in by_source.items():
                if isinstance(value, dict):
                    source_counts[str(source)] = source_counts.get(str(source), 0) + sum(_int(item) for item in value.values())
                else:
                    source_counts[str(source)] = source_counts.get(str(source), 0) + _int(value)
    non_live = {source: count for source, count in source_counts.items() if _is_non_live_source(source)}
    return {
        "source_counts": source_counts,
        "non_live_source_present": bool(non_live),
        "non_live_source_counts": non_live,
        "gate_counts_source": "live_only" if non_live else "aggregate",
    }


def _is_non_live_source(source: str) -> bool:
    return source.strip().casefold() in {"strategy_tester_replay"}


def _gate_counts(report: dict[str, Any], prefer_live_only: bool) -> dict[str, Any]:
    if not prefer_live_only:
        return report.get("counts", {})
    for key in ("live_only_counts", "counts_live_only"):
        value = report.get(key, {})
        if isinstance(value, dict) and value:
            return value
    by_source = report.get("counts_by_source_type", {})
    if isinstance(by_source, dict):
        live = by_source.get("live", {})
        if isinstance(live, dict):
            return live
    return {}


def _balance(c01: dict[str, Any], key: str, prefer_live_only: bool) -> dict[str, Any]:
    if not prefer_live_only:
        return c01.get(key, {})
    direct = c01.get(f"live_only_{key}", {})
    if isinstance(direct, dict) and direct:
        return direct
    nested = c01.get("live_only", {})
    if isinstance(nested, dict) and isinstance(nested.get(key), dict):
        return nested[key]
    by_source = c01.get("balances_by_source_type", {})
    if isinstance(by_source, dict) and isinstance(by_source.get("live"), dict):
        live = by_source["live"].get(key, {})
        if isinstance(live, dict):
            return live
    return {}


def _gate_value(report: dict[str, Any], key: str, prefer_live_only: bool, *, missing: Any) -> Any:
    if not prefer_live_only:
        return report.get(key, missing)
    direct_key = f"live_only_{key}"
    if direct_key in report:
        return report[direct_key]
    nested = report.get("live_only", {})
    if isinstance(nested, dict) and key in nested:
        return nested[key]
    by_source = report.get("values_by_source_type", {})
    if isinstance(by_source, dict) and isinstance(by_source.get("live"), dict) and key in by_source["live"]:
        return by_source["live"][key]
    return missing


def _fold_diagnostics(c01: dict[str, Any], prefer_live_only: bool) -> list[dict[str, Any]]:
    if not prefer_live_only:
        return c01.get("fold_diagnostics", [])
    direct = c01.get("live_only_fold_diagnostics", [])
    if isinstance(direct, list) and direct:
        return direct
    nested = c01.get("live_only", {})
    if isinstance(nested, dict) and isinstance(nested.get("fold_diagnostics"), list):
        return nested["fold_diagnostics"]
    return []


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)


def _load_pointer(root: Path) -> dict[str, Any]:
    return _read_json(root / "outputs" / "reports" / "C02_DATASET_POINTER.json")


def _read_json(path_or_text: str | Path) -> dict[str, Any]:
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))

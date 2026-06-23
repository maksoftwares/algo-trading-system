from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .market_data_export import _table, _utc_now, _write_json_atomic, parse_utc


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_HISTORICAL_BACKFILL_REPLAY_PLAN_STATUS.json"
SCHEMA_VERSION = "a3_ml_historical_backfill_replay_plan_status_v1"
STATUS_READY = "HISTORICAL_BACKFILL_REPLAY_PLAN_READY"
DEFAULT_LOOKBACK_DAYS = 120
DEFAULT_MAX_TICK_DAYS = 14


def generate_historical_backfill_replay_plan(
    root: Path,
    report_json: Path | None = None,
    *,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    max_tick_days: int = DEFAULT_MAX_TICK_DAYS,
) -> Path:
    root = root.resolve()
    reports = root / "outputs" / "reports"
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    pointer = _read_json(reports / "C02_DATASET_POINTER.json")
    c03 = _read_json(reports / "C03_TRAINING_READINESS_REPORT.json")
    c33 = _read_json(reports / "A3_ML_DEMO_SHADOW_COLLECTION_HEALTH_STATUS.json")
    c46 = _read_json(reports / "A3_ML_READINESS_PROGRESS_TRACKER_STATUS.json")
    cutoff = _snapshot_cutoff(pointer)
    start = cutoff - timedelta(days=max(1, int(lookback_days)))
    payload = {
        "status": STATUS_READY,
        "stage": "C50-HISTORICAL-BACKFILL-REPLAY-PLAN",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": pointer.get("dataset_version", c03.get("dataset_version", "")),
        "window": {
            "historical_start_utc": _iso(start),
            "snapshot_cutoff_utc": _iso(cutoff),
            "lookback_days": int(lookback_days),
            "max_tick_days": int(max_tick_days),
            "accounts": ["A1", "A2", "A3"],
            "symbol": "XAUUSD",
        },
        "current_readiness": _current_readiness(c03, c33, c46),
        "tracks": _tracks(c03),
        "commands": _commands(root, start, max_tick_days),
        "evidence_rules": _evidence_rules(),
        "operator_sequence": _operator_sequence(),
        "authorization": {
            "historical_export_authorized_by_this_plan": False,
            "strategy_tester_launch_authorized_by_this_plan": False,
            "training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "boundary": {
            "mt5_connection_attempted": False,
            "data_export_attempted": False,
            "strategy_tester_launch_attempted": False,
            "terminal_runtime_change_authorized": False,
            "profile_or_chart_file_write_attempted": False,
            "model_training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
        },
        "next_allowed_stage": (
            "Run the read-only historical export command when terminals are already open, then snapshot logs and rebuild C07. "
            "Treat Strategy Tester/replay output as reviewer-gated evidence, not automatic training labels."
        ),
    }
    _write_status(report_json, payload)
    _update_pointer(reports / "C02_DATASET_POINTER.json", payload)
    return report_json


def render_historical_backfill_replay_plan_md(payload: dict[str, Any]) -> str:
    readiness = payload.get("current_readiness", {})
    window = payload.get("window", {})
    tracks = [
        {
            "Track": item.get("track", ""),
            "Can Help": item.get("can_help", ""),
            "Limits": item.get("limits", ""),
            "Next": item.get("next_action", ""),
        }
        for item in payload.get("tracks", [])
    ]
    rules = [
        {
            "Evidence": item.get("evidence", ""),
            "Use": item.get("allowed_use", ""),
            "Cannot Do": item.get("cannot_do", ""),
        }
        for item in payload.get("evidence_rules", [])
    ]
    commands = "\n".join(f"- {key}: `{value}`" for key, value in payload.get("commands", {}).items())
    sequence = "\n".join(f"{index}. {item}" for index, item in enumerate(payload.get("operator_sequence", []), start=1))
    return "\n".join(
        [
            "# A3 ML Historical Backfill And EA Replay Plan",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Window",
            "",
            f"- Historical start UTC: {window.get('historical_start_utc', '')}.",
            f"- Snapshot cutoff UTC: {window.get('snapshot_cutoff_utc', '')}.",
            f"- Lookback days: {window.get('lookback_days', '')}.",
            f"- Tick export cap: last {window.get('max_tick_days', '')} days.",
            f"- Accounts: {', '.join(window.get('accounts', []))}.",
            "",
            "## Current Readiness",
            "",
            f"- C03: {readiness.get('c03_status', '')}.",
            f"- C33 collection: {readiness.get('c33_status', '')}.",
            f"- C46 progress: {readiness.get('c46_status', '')}.",
            f"- Failed gates: {', '.join(readiness.get('failed_gates', [])) or 'none'}.",
            "",
            "## Tracks",
            "",
            _table(tracks, ["Track", "Can Help", "Limits", "Next"]),
            "",
            "## Evidence Rules",
            "",
            _table(rules, ["Evidence", "Use", "Cannot Do"]),
            "",
            "## Commands",
            "",
            commands,
            "",
            "## Operator Sequence",
            "",
            sequence,
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Data export attempted: false.",
            "- Strategy Tester launch attempted: false.",
            "- Terminal runtime change authorized: false.",
            "- Profile or chart file write attempted: false.",
            "- Model training authorized: false.",
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


def _current_readiness(c03: dict[str, Any], c33: dict[str, Any], c46: dict[str, Any]) -> dict[str, Any]:
    failed = [str(item.get("gate", "")) for item in c03.get("checks", []) if not item.get("passed")]
    return {
        "c03_status": c03.get("status", "MISSING"),
        "c33_status": c33.get("status", "MISSING"),
        "c46_status": c46.get("status", "MISSING"),
        "failed_gates": failed,
        "all_accounts_collecting": bool(c33.get("collection_health", {}).get("all_accounts_collecting", False)),
    }


def _tracks(c03: dict[str, Any]) -> list[dict[str, str]]:
    failed = {str(item.get("gate", "")) for item in c03.get("checks", []) if not item.get("passed")}
    return [
        {
            "track": "Keep live A1/A2/A3 collection running",
            "can_help": "Adds real fills, request prices, and fresh shadow observations.",
            "limits": "Cannot instantly create 8 weeks of active history.",
            "next_action": "Do not stop terminals; rerun C43/C46 after market data advances.",
        },
        {
            "track": "MT5 historical bars/ticks export",
            "can_help": _can_help_text(failed, {"active_weeks", "market_setup_groups", "at_least_two_regimes"}),
            "limits": "Bars alone do not prove EA trade outcomes or live slippage.",
            "next_action": "Run C02 read-only export for the wider window, then C02 history snapshot and C07 rebuild.",
        },
        {
            "track": "EA Strategy Tester/replay logs",
            "can_help": _can_help_text(failed, {"market_setup_groups", "feature_budget", "dataset_status"}),
            "limits": "Replay output is not live fill evidence unless reviewer explicitly accepts that contract.",
            "next_action": "Run replay in tester-only mode and submit replay manifest/log hashes to reviewer before promoting labels.",
        },
        {
            "track": "Reviewer decision",
            "can_help": _can_help_text(failed, {"dataset_status", "feature_budget"}),
            "limits": "Approval still cannot authorize broker action and must flow through C42/C43.",
            "next_action": "Ask reviewer whether replay/backfill evidence may be admitted and exactly which gates it may satisfy.",
        },
    ]


def _evidence_rules() -> list[dict[str, str]]:
    return [
        {
            "evidence": "MT5 historical bars/ticks",
            "allowed_use": "Extend market span, regimes, and setup discovery after C02/C07 rebuild.",
            "cannot_do": "Cannot count as live fills or authorize model training by itself.",
        },
        {
            "evidence": "MT5 account history/deals",
            "allowed_use": "Can count only when account, symbol, source contract, and time window match the C02 catalog.",
            "cannot_do": "Cannot import out-of-scope logs without reviewer-approved contract expansion.",
        },
        {
            "evidence": "EA Strategy Tester/replay logs",
            "allowed_use": "Research/reviewer evidence for more labels and setup behavior.",
            "cannot_do": "Cannot close live slippage readiness or bypass C03 unless reviewer explicitly approves a replay evidence contract.",
        },
        {
            "evidence": "Live A1/A2/A3 collection",
            "allowed_use": "Authoritative source for slippage/fill deficits and demo shadow freshness.",
            "cannot_do": "Does not override gates until C03/C05/C04/C06/C10/C23 pass.",
        },
    ]


def _operator_sequence() -> list[str]:
    return [
        "Keep A1/A2/A3 live collection running in the background.",
        "Run the C50 historical export command only while the existing MT5 terminals are already open.",
        "Run the C50 history/log snapshot command for the same dataset.",
        "Run C07 to rebuild normalized data, labels, C03, and C05 fail-closed.",
        "Run C43 without refresh to regenerate reviewer package and readiness reports.",
        "If using Strategy Tester/replay, keep it tester-only, collect output hashes, and ask reviewer before admitting replay labels.",
    ]


def _commands(root: Path, start: datetime, max_tick_days: int) -> dict[str, str]:
    python = _quote(sys.executable)
    root_arg = _quote(str(root))
    start_arg = _iso(start)
    return {
        "historical_readonly_export": (
            f"{python} {_quote(str(root / 'scripts' / 'c02_export_mt5_market_data.py'))} "
            f"--root {root_arg} --requested-start-utc {start_arg} --accounts A1,A2,A3 --max-tick-days {int(max_tick_days)}"
        ),
        "history_log_snapshot": f"{python} {_quote(str(root / 'scripts' / 'c02_snapshot_history_logs.py'))} --root {root_arg} --accounts A1,A2,A3",
        "offline_rebuild": f"{python} {_quote(str(root / 'scripts' / 'c07_run_ml_readiness_pipeline.py'))} --root {root_arg}",
        "status_cycle": f"{python} {_quote(str(root / 'scripts' / 'c43_run_demo_readiness_cycle.py'))} --root {root_arg}",
        "reviewer_question": "Ask reviewer whether Strategy Tester/replay labels may satisfy dataset_status/feature_budget/slippage gates, and under what contract.",
    }


def _snapshot_cutoff(pointer: dict[str, Any]) -> datetime:
    value = pointer.get("snapshot_cutoff_utc")
    if isinstance(value, str) and value.strip():
        return parse_utc(value)
    return datetime.now(timezone.utc).replace(second=0, microsecond=0)


def _can_help_text(failed: set[str], gates: set[str]) -> str:
    overlap = sorted(failed & gates)
    if not overlap:
        return "Supports audit/reviewer context; no current direct gate target."
    return "Can target: " + ", ".join(overlap)


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_historical_backfill_replay_plan_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c50_historical_backfill_replay_plan_report"] = payload["outputs"]["status_report_json"]
    pointer["c50_historical_backfill_replay_plan_status"] = payload["status"]
    pointer["python_demo_predictions_authorized"] = False
    pointer["ea_consumption_authorized"] = False
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)


def _read_json(path_or_text: str | Path) -> dict[str, Any]:
    if not path_or_text:
        return {}
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _quote(value: str) -> str:
    return f'"{value}"' if " " in value else value


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

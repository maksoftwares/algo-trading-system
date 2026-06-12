from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_RESOLUTION_ROWS = Path("outputs") / "reports" / "OBSERVER_OUTCOME_RESOLUTION_ROWS.csv"
DEFAULT_BARS_DIR = Path("outputs") / "reports" / "m5_replay_bars"
DEFAULT_COST_MODEL = Path("..") / "xauusd-phase0" / "outputs" / "reports" / "cost_model_measured.csv"
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "OBSERVER_REPLAY_CALIBRATION_REPORT.json"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "OBSERVER_REPLAY_CALIBRATION_REPORT.md"
DEFAULT_OUTPUT_CSV = Path("outputs") / "reports" / "OBSERVER_REPLAY_CALIBRATION_ROWS.csv"


def generate_observer_replay_calibration(
    phase1_root: Path,
    resolution_rows_csv: Path | None = None,
    bars_dir: Path | None = None,
    cost_model_csv: Path | None = None,
    output_json: Path | None = None,
) -> Path:
    phase1_root = phase1_root.resolve()
    resolution_rows_csv = (resolution_rows_csv or phase1_root / DEFAULT_RESOLUTION_ROWS).resolve()
    bars_dir = (bars_dir or phase1_root / DEFAULT_BARS_DIR).resolve()
    cost_model_csv = (cost_model_csv or phase1_root / DEFAULT_COST_MODEL).resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_OUTPUT_JSON.name else phase1_root / DEFAULT_OUTPUT_MD
    output_csv = output_json.with_suffix(".csv") if output_json.name != DEFAULT_OUTPUT_JSON.name else phase1_root / DEFAULT_OUTPUT_CSV
    output_json.parent.mkdir(parents=True, exist_ok=True)

    resolver = _load_resolver()
    all_rows = _read_csv(resolution_rows_csv)
    broker_rows = [row for row in all_rows if row.get("resolution_status", "").startswith("BROKER_")]
    bars_cache: dict[str, list[dict[str, str]]] = {}
    cost_model = resolver._load_cost_model(cost_model_csv)
    calibration_rows: list[dict[str, str]] = []
    for row in broker_rows:
        replay = resolver._replay_resolution(row, bars_dir, bars_cache, cost_model)
        broker_outcome = _outcome_from_broker(row)
        v2_outcome = _outcome_from_replay(replay or {})
        v1_outcome = _outcome_from_status((replay or {}).get("v1_resolution_status", ""))
        calibration_rows.append(
            {
                "candidate": row.get("candidate", ""),
                "family": row.get("family", ""),
                "symbol": row.get("symbol", ""),
                "time_bucket": row.get("time_bucket", ""),
                "direction": row.get("direction", ""),
                "normalized_direction": row.get("normalized_direction", ""),
                "m5_bar_time": row.get("m5_bar_time", ""),
                "broker_status": row.get("resolution_status", ""),
                "broker_outcome": broker_outcome,
                "broker_profit_aed": row.get("actual_profit_aed", ""),
                "v1_replay_status": replay.get("v1_resolution_status", "UNRESOLVED_REPLAY_MISSING") if replay else "UNRESOLVED_REPLAY_MISSING",
                "v1_replay_outcome": v1_outcome,
                "v1_replay_net_r": replay.get("v1_net_outcome_r", "") if replay else "",
                "v1_outcome_match": str(broker_outcome in {"WIN", "LOSS"} and broker_outcome == v1_outcome).lower(),
                "v1_pnl_sign_match": str(_pnl_sign(row.get("actual_profit_aed")) == _outcome_sign(v1_outcome)).lower(),
                "v2_replay_model": replay.get("replay_model", "executor_v2") if replay else "executor_v2",
                "v2_replay_status": replay.get("resolution_status", "UNRESOLVED_REPLAY_MISSING") if replay else "UNRESOLVED_REPLAY_MISSING",
                "v2_replay_outcome": v2_outcome,
                "v2_replay_entry_price": replay.get("replay_entry_price", "") if replay else "",
                "v2_replay_synthetic_stop_loss": replay.get("replay_synthetic_stop_loss", "") if replay else "",
                "v2_replay_synthetic_take_profit": replay.get("replay_synthetic_take_profit", "") if replay else "",
                "v2_replay_signal_risk_points": replay.get("replay_signal_risk_points", "") if replay else "",
                "v2_replay_spread_points": replay.get("replay_spread_points", "") if replay else "",
                "v2_replay_net_r": replay.get("net_outcome_r", "") if replay else "",
                "v2_outcome_match": str(broker_outcome in {"WIN", "LOSS"} and broker_outcome == v2_outcome).lower(),
                "v2_pnl_sign_match": str(_pnl_sign(row.get("actual_profit_aed")) == _outcome_sign(v2_outcome)).lower(),
                "v1_vs_v2_outcome_same": str(v1_outcome == v2_outcome).lower(),
            }
        )

    closed_rows = [row for row in calibration_rows if row["broker_outcome"] in {"WIN", "LOSS"}]
    outcome_matches = sum(1 for row in closed_rows if row["v2_outcome_match"] == "true")
    pnl_matches = sum(1 for row in closed_rows if row["v2_pnl_sign_match"] == "true")
    v1_outcome_matches = sum(1 for row in closed_rows if row["v1_outcome_match"] == "true")
    v1_pnl_matches = sum(1 for row in closed_rows if row["v1_pnl_sign_match"] == "true")
    outcome_pct = outcome_matches / len(closed_rows) * 100.0 if closed_rows else 0.0
    pnl_pct = pnl_matches / len(closed_rows) * 100.0 if closed_rows else 0.0
    v1_outcome_pct = v1_outcome_matches / len(closed_rows) * 100.0 if closed_rows else 0.0
    v1_pnl_pct = v1_pnl_matches / len(closed_rows) * 100.0 if closed_rows else 0.0
    payload: dict[str, Any] = {
        "status": _status(outcome_pct, len(closed_rows)),
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": "Read-only replay calibration. It compares broker-joined outcomes against M5 replay and does not touch MT5 runtime.",
        "replay_model_under_test": "executor_v2",
        "resolution_rows_csv": str(resolution_rows_csv),
        "bars_dir": str(bars_dir),
        "cost_model_csv": str(cost_model_csv),
        "broker_joined_rows": len(broker_rows),
        "closed_broker_rows": len(closed_rows),
        "v1_outcome_match_count": v1_outcome_matches,
        "v1_outcome_match_pct": round(v1_outcome_pct, 2),
        "v1_pnl_sign_match_count": v1_pnl_matches,
        "v1_pnl_sign_match_pct": round(v1_pnl_pct, 2),
        "outcome_match_count": outcome_matches,
        "outcome_match_pct": round(outcome_pct, 2),
        "pnl_sign_match_count": pnl_matches,
        "pnl_sign_match_pct": round(pnl_pct, 2),
        "by_symbol_bucket": _rollup(calibration_rows, ["symbol", "time_bucket"]),
        "by_candidate": _rollup(calibration_rows, ["candidate"]),
        "notes": [
            "executor_v2 is judged against the same rule: >=90% usable, 75-90% usable with error bar, <75% quarantined.",
            "If executor_v2 remains below 75%, replay is marked PERMANENTLY_QUARANTINED_PENDING_NEW_DESIGN and scoreboards must be broker-joined-only.",
            "Per-row CSV preserves v1 plan replay, v2 executor replay, and actual broker outcome for audit diffing.",
        ],
    }
    _write_csv(output_csv, calibration_rows, _fields())
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return output_json


def _status(outcome_pct: float, closed_count: int) -> str:
    if closed_count == 0:
        return "NO_BROKER_JOINED_CLOSED_ROWS"
    if outcome_pct >= 90.0:
        return "PASS_REPLAY_USABLE"
    if outcome_pct >= 75.0:
        return "WARN_REPLAY_USABLE_WITH_ERROR_BAR"
    return "PERMANENTLY_QUARANTINED_PENDING_NEW_DESIGN"


def _outcome_from_broker(row: dict[str, str]) -> str:
    status = row.get("resolution_status", "")
    if status == "BROKER_CLOSED_WIN":
        return "WIN"
    if status == "BROKER_CLOSED_LOSS":
        return "LOSS"
    if status == "BROKER_MATCH_OPEN":
        return "OPEN"
    return "FLAT_OR_UNKNOWN"


def _outcome_from_replay(row: dict[str, str]) -> str:
    return _outcome_from_status(row.get("resolution_status", ""))


def _outcome_from_status(status: str) -> str:
    if status == "REPLAY_TP":
        return "WIN"
    if status == "REPLAY_SL":
        return "LOSS"
    return "UNRESOLVED"


def _pnl_sign(value: str) -> str:
    try:
        number = float(str(value or "0").strip())
    except ValueError:
        return "UNKNOWN"
    if number > 0:
        return "WIN"
    if number < 0:
        return "LOSS"
    return "FLAT"


def _outcome_sign(value: str) -> str:
    if value in {"WIN", "LOSS"}:
        return value
    return "UNKNOWN"


def _rollup(rows: list[dict[str, str]], keys: list[str]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(tuple(row.get(key, "") or "UNKNOWN" for key in keys), []).append(row)
    out: list[dict[str, Any]] = []
    for key, items in sorted(grouped.items()):
        closed = [row for row in items if row["broker_outcome"] in {"WIN", "LOSS"}]
        matches = sum(1 for row in closed if row["v2_outcome_match"] == "true")
        item = {column: value for column, value in zip(keys, key)}
        item.update(
            {
                "rows": len(items),
                "closed": len(closed),
                "outcome_match_count": matches,
                "outcome_match_pct": round(matches / len(closed) * 100.0, 2) if closed else 0.0,
            }
        )
        out.append(item)
    return out


def _fields() -> list[str]:
    return [
        "candidate",
        "family",
        "symbol",
        "time_bucket",
        "direction",
        "normalized_direction",
        "m5_bar_time",
        "broker_status",
        "broker_outcome",
        "broker_profit_aed",
        "v1_replay_status",
        "v1_replay_outcome",
        "v1_replay_net_r",
        "v1_outcome_match",
        "v1_pnl_sign_match",
        "v2_replay_model",
        "v2_replay_status",
        "v2_replay_outcome",
        "v2_replay_entry_price",
        "v2_replay_synthetic_stop_loss",
        "v2_replay_synthetic_take_profit",
        "v2_replay_signal_risk_points",
        "v2_replay_spread_points",
        "v2_replay_net_r",
        "v2_outcome_match",
        "v2_pnl_sign_match",
        "v1_vs_v2_outcome_same",
    ]


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _render_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Observer Replay Calibration Report",
            "",
            f"Status: `{payload['status']}`",
            "",
            payload["authority"],
            "",
            f"Replay model under test: `{payload['replay_model_under_test']}`",
            f"Broker-joined rows: `{payload['broker_joined_rows']}`",
            f"Closed broker rows: `{payload['closed_broker_rows']}`",
            f"v1 outcome agreement: `{payload['v1_outcome_match_count']}` / `{payload['closed_broker_rows']}` = `{payload['v1_outcome_match_pct']}%`",
            f"v1 PnL-sign agreement: `{payload['v1_pnl_sign_match_count']}` / `{payload['closed_broker_rows']}` = `{payload['v1_pnl_sign_match_pct']}%`",
            f"v2 outcome agreement: `{payload['outcome_match_count']}` / `{payload['closed_broker_rows']}` = `{payload['outcome_match_pct']}%`",
            f"v2 PnL-sign agreement: `{payload['pnl_sign_match_count']}` / `{payload['closed_broker_rows']}` = `{payload['pnl_sign_match_pct']}%`",
            "",
            "## By Symbol And Bucket",
            "",
            _table(payload["by_symbol_bucket"], ["symbol", "time_bucket", "rows", "closed", "outcome_match_count", "outcome_match_pct"]),
            "",
            "## By Candidate",
            "",
            _table(payload["by_candidate"], ["candidate", "rows", "closed", "outcome_match_count", "outcome_match_pct"]),
            "",
            "## Rule",
            "",
            "- >=90% outcome agreement: replay rows are usable.",
            "- 75-90% outcome agreement: replay rows are usable with a disclosed error bar.",
            "- <75% outcome agreement after executor_v2 means `PERMANENTLY_QUARANTINED_PENDING_NEW_DESIGN`; scoreboards must be broker-joined-only.",
            "",
        ]
    )


def _table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def _load_resolver():
    path = Path(__file__).resolve().with_name("generate_observer_outcome_resolution.py")
    spec = importlib.util.spec_from_file_location("generate_observer_outcome_resolution", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description="Calibrate M5 replay against broker-joined observer outcomes.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--resolution-rows-csv", type=Path, default=None)
    parser.add_argument("--bars-dir", type=Path, default=None)
    parser.add_argument("--cost-model-csv", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args()
    output = generate_observer_replay_calibration(
        args.phase1_root,
        resolution_rows_csv=args.resolution_rows_csv,
        bars_dir=args.bars_dir,
        cost_model_csv=args.cost_model_csv,
        output_json=args.output_json,
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

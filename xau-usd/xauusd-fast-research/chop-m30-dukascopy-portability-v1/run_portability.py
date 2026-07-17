from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
LOCAL_SRC = ROOT / "src"
sys.path.insert(0, str(LOCAL_SRC))

from portability import evaluate_gate, run_portability, stage_metrics  # noqa: E402


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if hasattr(value, "item"):
        return json_ready(value.item())
    return value


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(json_ready(payload), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def frame_digest(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return hashlib.sha256(b"").hexdigest()
    payload = frame[columns].to_csv(index=False, lineterminator="\n", float_format="%.10g").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def render_report(payload: dict[str, Any], stages: pd.DataFrame) -> str:
    lines = [
        "# XAUUSD M30 Chop Dukascopy Portability V1 Result",
        "",
        f"Decision: **{payload['decision']}**",
        "",
        "Frozen Capital.com candidate replayed unchanged on verified Dukascopy Bid/Ask data.",
        "",
        "| Stage | Trades | Trades/day | PF | Stress PF | Stress avg R | Stress net R | DD R | Gate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in stages.to_dict("records"):
        pf = "NA" if row["profit_factor"] is None else f"{row['profit_factor']:.3f}"
        stress_pf = "NA" if row["stress_profit_factor"] is None else f"{row['stress_profit_factor']:.3f}"
        lines.append(
            f"| {row['stage']} | {row['trades']} | {row['trades_per_source_day']:.3f} | {pf} | "
            f"{stress_pf} | {row['average_stress_r']:.3f} | {row['stress_net_r']:.3f} | "
            f"{row['stress_drawdown_r']:.3f} | {'PASS' if row['pass'] else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            payload["interpretation"],
            "",
            "Research only. No Python prediction, EA, demo, live, or broker authorization is granted.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    config_path = ROOT / "config" / "portability_v1.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    run = run_portability(config)
    rows: list[dict[str, Any]] = []
    audit: dict[str, Any] = {}
    for stage in ("train", "validation", "exam", "full"):
        start, end = map(pd.Timestamp, config["windows"][stage])
        gate = config["gates"][stage]
        value = stage_metrics(run.trades, run.source_m5, start, end, int(gate["top_winners_removed"]))
        passed, checks = evaluate_gate(value, gate)
        rows.append({"stage": stage, "pass": passed, **value})
        audit[stage] = {"pass": passed, "checks": checks, "metrics": value}
    stages = pd.DataFrame(rows)
    passed = bool(stages["pass"].all())
    if passed:
        decision = "RETROSPECTIVE_CHOP_M30_PORTABILITY_SURVIVOR_REQUIRES_VALIDATION"
        interpretation = (
            "The unchanged specialist transferred across venue and passed every chronological and cost gate. "
            "It remains a candidate pending exact MT5 parity, independent review, and prospective shadow evidence."
        )
    else:
        decision = "CHOP_M30_DUKASCOPY_PORTABILITY_REJECTED"
        interpretation = (
            "The unchanged specialist failed at least one frozen cross-venue gate. It is not rescued or tuned in V1."
        )
    trade_digest = frame_digest(
        run.trades,
        ["strategy_id", "entry_time", "exit_time", "direction", "net_r", "stress_net_r"],
    )
    payload = {
        "schema_version": config["schema_version"],
        "decision": decision,
        "interpretation": interpretation,
        "gate_audit": audit,
        "signal_rows": int(len(run.signals)),
        "trade_rows": int(len(run.trades)),
        "trade_digest": trade_digest,
        "data_evidence": run.evidence,
        "authorization": config["research_controls"],
    }
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    run.signals.to_csv(output / config["outputs"]["signals"], index=False, lineterminator="\n")
    run.trades.to_csv(output / config["outputs"]["trades"], index=False, lineterminator="\n")
    stages.to_csv(output / config["outputs"]["stage_metrics"], index=False, lineterminator="\n")
    write_json(output / config["outputs"]["result_json"], payload)
    (output / config["outputs"]["result_markdown"]).write_text(render_report(payload, stages), encoding="utf-8")
    ancestry_root = ROOT.parent / "chop-v1"
    manifest = {
        "config_sha256": sha256_file(config_path),
        "portability_sha256": sha256_file(LOCAL_SRC / "portability.py"),
        "runner_sha256": sha256_file(ROOT / "run_portability.py"),
        "source_feature_sha256": run.evidence["feature_sha256"],
        "ancestry_hashes": {
            "original_config_sha256": sha256_file(ancestry_root / "config" / "chop_fast_discovery_v1.json"),
            "regime_sha256": sha256_file(ancestry_root / "src" / "regime.py"),
            "strategies_sha256": sha256_file(ancestry_root / "src" / "strategies.py"),
            "backtest_sha256": sha256_file(ancestry_root / "src" / "backtest.py"),
            "data_adapter_sha256": sha256_file(ancestry_root / "src" / "data_adapter.py"),
        },
        "signal_rows": int(len(run.signals)),
        "trade_rows": int(len(run.trades)),
        "trade_digest": trade_digest,
    }
    write_json(output / config["outputs"]["manifest"], manifest)
    print(json.dumps({"decision": decision, "trades": len(run.trades), "trade_digest": trade_digest}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

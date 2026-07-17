from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
SHARED_SRC = ROOT.parent / "independent-specialists-v1" / "src"
sys.path.insert(0, str(SHARED_SRC))
sys.path.insert(0, str(ROOT / "src"))

from data import load_bundle, sha256_file  # noqa: E402
from engine import generate_candidates, replay, stage_audit  # noqa: E402


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


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(json_ready(value), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def frame_digest(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return hashlib.sha256(b"").hexdigest()
    return hashlib.sha256(
        frame[columns]
        .to_csv(index=False, lineterminator="\n", float_format="%.10g")
        .encode("utf-8")
    ).hexdigest()


def render_report(result: dict[str, Any], stages: pd.DataFrame) -> str:
    lines = [
        "# XAUUSD Cost-Aware Breakout-Retest V2 Result",
        "",
        f"Decision: **{result['decision']}**",
        "",
        "V1 remains cost-suspended. This V2 result is research-only and receives no diversification credit.",
        "",
        "| Stage | Eligible | Trades | Trades/day | Stress PF | Avg stress R | Drawdown R | Gate |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in stages.to_dict("records"):
        pf = row["stress_pf"]
        pf_text = "NA" if pf is None else f"{pf:.3f}"
        lines.append(
            f"| {row['stage']} | {row['decision_eligible']} | {row['trades']} | "
            f"{row['trades_per_source_day']:.3f} | {pf_text} | "
            f"{row['average_stress_r']:.3f} | {row['closed_drawdown_r']:.3f} | "
            f"{'PASS' if row['promoted'] else 'FAIL' if row['decision_eligible'] else 'INELIGIBLE'} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            result["interpretation"],
            "",
            "A pass would still require exact-tick parity and prospective shadow observation before any execution discussion.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    config_path = ROOT / "config" / "cost_aware_breakout_retest_v2.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    bundle = load_bundle(config)
    m5 = bundle.bars["M5"]
    candidates = generate_candidates(m5, config["strategy"], config["costs"])
    result = replay(m5, candidates, config)
    stages, audit = stage_audit(result.trades, m5, config)
    survivor = bool(audit["recent_tail"]["promoted"])
    decision = (
        "RETROSPECTIVE_SAME_FAMILY_SURVIVOR_REQUIRES_TICK_PARITY_AND_FORWARD_SHADOW"
        if survivor
        else "REJECTED_COST_AWARE_BREAKOUT_RETEST_V2"
    )
    interpretation = (
        "The fixed cost-aware event survived every chronological and recent-tail gate. "
        "It counts as one same-family research survivor, not an independent portfolio."
        if survivor
        else "The fixed cost-aware event failed the chronological firewall. V2 is closed without tuning."
    )
    candidate_digest = frame_digest(
        result.candidates,
        ["signal_time", "direction", "signal_accepted", "rejection_reason"],
    )
    trade_digest = frame_digest(
        result.trades,
        ["entry_time", "exit_time", "direction", "stress_net_r"],
    )
    payload = {
        "schema_version": config["schema_version"],
        "decision": decision,
        "survivor": survivor,
        "interpretation": interpretation,
        "stage_audit": audit,
        "candidate_rows": int(len(result.candidates)),
        "trade_rows": int(len(result.trades)),
        "candidate_digest": candidate_digest,
        "trade_digest": trade_digest,
        "data_evidence": bundle.evidence,
        "authorization": config["research_controls"],
    }
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    result.candidates.to_csv(output / config["outputs"]["candidate_ledger"], index=False, lineterminator="\n")
    result.trades.to_csv(output / config["outputs"]["trade_ledger"], index=False, lineterminator="\n")
    stages.to_csv(output / config["outputs"]["stage_metrics"], index=False, lineterminator="\n")
    write_json(output / config["outputs"]["result_json"], payload)
    (output / config["outputs"]["result_markdown"]).write_text(render_report(payload, stages), encoding="utf-8")
    manifest = {
        "config_sha256": sha256_file(config_path),
        "shared_data_loader_sha256": sha256_file(SHARED_SRC / "data.py"),
        "feature_sha256": bundle.evidence["feature_sha256"],
        "candidate_rows": int(len(result.candidates)),
        "trade_rows": int(len(result.trades)),
        "candidate_digest": candidate_digest,
        "trade_digest": trade_digest,
    }
    write_json(output / config["outputs"]["manifest"], manifest)
    print(
        json.dumps(
            {
                "decision": decision,
                "candidate_rows": len(result.candidates),
                "trade_rows": len(result.trades),
                "result": str(output / config["outputs"]["result_markdown"]),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

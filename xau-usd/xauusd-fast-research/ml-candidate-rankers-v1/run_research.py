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
from engine import (  # noqa: E402
    FAMILIES,
    generate_candidates,
    label_candidates,
    portfolio_exam,
    run_walk_forward,
)


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
    payload = frame[columns].to_csv(index=False, lineterminator="\n", float_format="%.10g").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def render_report(payload: dict[str, Any], stages: pd.DataFrame) -> str:
    lines = [
        "# XAUUSD ML Candidate Rankers V1 Result",
        "",
        f"Decision: **{payload['decision']}**",
        "",
        "Research only. No model score is authorized for Python prediction, EA consumption, demo, or live execution.",
        "",
        "| Family | Stage | Eligible | Trades | Trades/day | Stress PF | Avg R | Drawdown R | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in stages.to_dict("records"):
        pf = row["stress_pf"]
        pf_text = "NA" if pf is None else f"{pf:.3f}"
        status = "PASS" if row["promoted"] else "FAIL" if row["decision_eligible"] else "INELIGIBLE"
        lines.append(
            f"| `{row['family_id']}` | {row['stage']} | {row['decision_eligible']} | "
            f"{row['trades']} | {row['trades_per_source_day']:.3f} | {pf_text} | "
            f"{row['average_stress_r']:.3f} | {row['closed_drawdown_r']:.3f} | {status} |"
        )
    portfolio = payload["portfolio"]["metrics"]
    lines.extend(
        [
            "",
            "## Portfolio",
            "",
            f"Survivors: {', '.join(payload['survivors']) if payload['survivors'] else 'none'}.",
            f"Exam portfolio: {portfolio['trades']} trades, {portfolio['trades_per_source_day']:.3f}/source-day, "
            f"stress PF {portfolio['stress_pf']}, average {portfolio['average_stress_r']:.3f}R, "
            f"drawdown {portfolio['closed_drawdown_r']:.3f}R.",
            "",
            "## Interpretation",
            "",
            payload["interpretation"],
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    config_path = ROOT / "config" / "ml_candidate_rankers_v1.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    bundle = load_bundle(config)
    m5, m15 = bundle.bars["M5"], bundle.bars["M15"]
    mechanical = generate_candidates(m15, m5, config)
    labeled = label_candidates(mechanical, m5, config["execution"])
    walk = run_walk_forward(labeled, m5, config)
    portfolio_trades, portfolio = portfolio_exam(
        walk.selected_trades, walk.survivors, m5, config
    )
    if portfolio["pass"]:
        decision = "RETROSPECTIVE_ML_RANKED_PORTFOLIO_SURVIVOR_REQUIRES_FORWARD_SHADOW"
        interpretation = (
            "Both ranked candidate families survived the frozen walk-forward, recent-tail, "
            "independence, and portfolio gates. Exact-tick parity and prospective shadow evidence remain mandatory."
        )
    elif walk.survivors:
        decision = "NO_ACCEPTABLE_ML_RANKED_PORTFOLIO"
        interpretation = (
            "At least one ranker survived alone, but breadth, independence, frequency, or portfolio gates failed."
        )
    else:
        decision = "NO_ML_RANKER_SURVIVOR"
        interpretation = (
            "Neither fixed ranker passed the full chronological firewall. V1 is rejected without tuning."
        )
    candidate_digest = frame_digest(
        walk.candidates,
        ["family_id", "signal_time", "direction", "entry_time", "exit_time", "stress_net_r"],
    )
    selected_digest = frame_digest(
        walk.selected_trades,
        ["family_id", "stage", "entry_time", "exit_time", "direction", "model_score", "stress_net_r"],
    )
    payload = {
        "schema_version": config["schema_version"],
        "decision": decision,
        "interpretation": interpretation,
        "survivors": walk.survivors,
        "gate_audit": walk.gate_audit,
        "portfolio": portfolio,
        "mechanical_candidate_rows": int(len(mechanical)),
        "labeled_candidate_rows": int(len(labeled)),
        "selected_trade_rows": int(len(walk.selected_trades)),
        "portfolio_trade_rows": int(len(portfolio_trades)),
        "candidate_digest": candidate_digest,
        "selected_digest": selected_digest,
        "data_evidence": bundle.evidence,
        "authorization": config["research_controls"],
    }
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    walk.candidates.to_csv(output / config["outputs"]["candidate_ledger"], index=False, lineterminator="\n")
    walk.selected_trades.to_csv(output / config["outputs"]["selected_trade_ledger"], index=False, lineterminator="\n")
    walk.stage_metrics.to_csv(output / config["outputs"]["stage_metrics"], index=False, lineterminator="\n")
    walk.diagnostics.to_csv(output / config["outputs"]["model_diagnostics"], index=False, lineterminator="\n")
    write_json(output / config["outputs"]["result_json"], payload)
    (output / config["outputs"]["result_markdown"]).write_text(
        render_report(payload, walk.stage_metrics), encoding="utf-8"
    )
    manifest = {
        "config_sha256": sha256_file(config_path),
        "shared_data_loader_sha256": sha256_file(SHARED_SRC / "data.py"),
        "feature_sha256": bundle.evidence["feature_sha256"],
        "mechanical_candidate_rows": int(len(mechanical)),
        "labeled_candidate_rows": int(len(labeled)),
        "selected_trade_rows": int(len(walk.selected_trades)),
        "candidate_digest": candidate_digest,
        "selected_digest": selected_digest,
    }
    write_json(output / config["outputs"]["manifest"], manifest)
    print(
        json.dumps(
            {
                "decision": decision,
                "survivors": walk.survivors,
                "mechanical_candidates": len(mechanical),
                "labeled_candidates": len(labeled),
                "selected_trades": len(walk.selected_trades),
                "result": str(output / config["outputs"]["result_markdown"]),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

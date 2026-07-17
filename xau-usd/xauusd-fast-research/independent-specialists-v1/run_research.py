from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from data import load_bundle, sha256_file  # noqa: E402
from research import (  # noqa: E402
    SPECIALISTS,
    generate_candidates,
    independence_audit,
    portfolio_exam,
    run_backtest,
    stage_audit,
)


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if hasattr(value, "item"):
        return _json_ready(value.item())
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(
            _json_ready(payload), indent=2, sort_keys=True, allow_nan=False
        )
        + "\n",
        encoding="utf-8",
    )


def _frame_digest(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return hashlib.sha256(b"").hexdigest()
    payload = frame[columns].to_csv(
        index=False, lineterminator="\n", float_format="%.10g"
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _report(result: dict[str, Any], stage_metrics: pd.DataFrame) -> str:
    lines = [
        "# XAUUSD Independent Specialists V1 Result",
        "",
        f"Campaign decision: **{result['campaign_decision']}**",
        "",
        "Research only. This result does not authorize model training, EA consumption, demo orders, or live orders.",
        "",
        "## Specialist Decisions",
        "",
        "| Specialist | Train | Validation | Internal test | Exam | Decision |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for specialist in SPECIALISTS:
        audit = result["gate_audit"][specialist]
        decisions = [
            "PASS"
            if audit[stage]["promoted"]
            else "FAIL"
            if audit[stage]["decision_eligible"]
            else "INELIGIBLE"
            for stage in ("train", "validation", "internal_test", "exam")
        ]
        lines.append(
            f"| `{specialist}` | "
            + " | ".join(decisions)
            + f" | {result['specialist_decisions'][specialist]} |"
        )
    lines.extend(["", "## Stage Metrics", ""])
    for row in stage_metrics.to_dict("records"):
        pf = row["stress_pf"]
        pf_text = "NA" if pf is None else f"{pf:.3f}"
        lines.append(
            f"- `{row['specialist_id']}` / `{row['stage']}`: "
            f"{row['trades']} trades, {row['trades_per_source_day']:.3f}/source-day, "
            f"stress PF {pf_text}, average {row['average_stress_r']:.3f}R, "
            f"drawdown {row['closed_drawdown_r']:.3f}R."
        )
    lines.extend(
        [
            "",
            "## Portfolio",
            "",
            f"Survivors: {', '.join(result['survivors']) if result['survivors'] else 'none'}.",
        ]
    )
    portfolio_metrics = result["portfolio"]["metrics"]
    lines.append(
        f"Exam portfolio: {portfolio_metrics['trades']} trades, "
        f"{portfolio_metrics['trades_per_source_day']:.3f}/source-day, "
        f"stress PF {portfolio_metrics['stress_pf']}, "
        f"average {portfolio_metrics['average_stress_r']:.3f}R, "
        f"drawdown {portfolio_metrics['closed_drawdown_r']:.3f}R."
    )
    lines.extend(["", "## Interpretation", "", result["interpretation"], ""])
    return "\n".join(lines)


def main() -> int:
    config_path = ROOT / "config" / "independent_specialists_v1.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    bundle = load_bundle(config)
    candidates, routed = generate_candidates(bundle.bars, config)
    replay = run_backtest(routed["M5"], candidates, config)
    stage_metrics, gate_audit = stage_audit(replay.trades, routed["M5"], config)
    survivors = [
        specialist
        for specialist in SPECIALISTS
        if gate_audit[specialist]["exam"]["promoted"]
    ]
    independence, independent = independence_audit(
        replay.trades, survivors, config
    )
    portfolio_trades, portfolio = portfolio_exam(
        replay.trades, survivors, routed["M5"], config
    )
    portfolio["independence_pass"] = independent
    portfolio["pass"] = bool(
        portfolio["pass"] and independent and len(survivors) >= 2
    )
    decisions = {
        specialist: "SURVIVOR" if specialist in survivors else "REJECT"
        for specialist in SPECIALISTS
    }
    if portfolio["pass"]:
        campaign_decision = (
            "RETROSPECTIVE_PORTFOLIO_SURVIVOR_REQUIRES_TICK_PARITY_AND_FORWARD_SHADOW"
        )
        interpretation = (
            "Several mechanically distinct specialists survived every frozen retrospective gate. "
            "Exact-tick parity and prospective shadow evidence remain mandatory."
        )
    elif survivors:
        campaign_decision = "NO_ACCEPTABLE_INDEPENDENT_PORTFOLIO"
        interpretation = (
            "At least one family survived alone, but the frozen independence, breadth, "
            "frequency, or portfolio gates failed. No trading promotion follows."
        )
    else:
        campaign_decision = "NO_SPECIALIST_SURVIVOR"
        interpretation = (
            "No family passed the full chronological firewall. These definitions are "
            "rejected and will not be tuned in V1."
        )
    result = {
        "schema_version": config["schema_version"],
        "campaign_decision": campaign_decision,
        "specialist_decisions": decisions,
        "survivors": survivors,
        "gate_audit": gate_audit,
        "independence": independence,
        "portfolio": portfolio,
        "data_evidence": bundle.evidence,
        "candidate_digest": _frame_digest(
            replay.candidates,
            [
                "specialist_id",
                "signal_time",
                "direction",
                "signal_accepted",
                "rejection_reason",
            ],
        ),
        "trade_digest": _frame_digest(
            replay.trades,
            [
                "specialist_id",
                "entry_time",
                "exit_time",
                "direction",
                "stress_net_r",
            ],
        ),
        "interpretation": interpretation,
        "authorization": config["research_controls"],
    }
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    replay.candidates.to_csv(
        output / config["outputs"]["candidate_ledger"],
        index=False,
        lineterminator="\n",
    )
    replay.trades.to_csv(
        output / config["outputs"]["trade_ledger"],
        index=False,
        lineterminator="\n",
    )
    stage_metrics.to_csv(
        output / config["outputs"]["stage_metrics"],
        index=False,
        lineterminator="\n",
    )
    _write_json(output / config["outputs"]["gate_audit"], gate_audit)
    _write_json(output / config["outputs"]["result_json"], result)
    (output / config["outputs"]["result_markdown"]).write_text(
        _report(result, stage_metrics), encoding="utf-8"
    )
    manifest = {
        "config_sha256": sha256_file(config_path),
        "feature_sha256": bundle.evidence["feature_sha256"],
        "candidate_digest": result["candidate_digest"],
        "trade_digest": result["trade_digest"],
        "candidate_rows": int(len(replay.candidates)),
        "trade_rows": int(len(replay.trades)),
        "portfolio_trade_rows": int(len(portfolio_trades)),
    }
    _write_json(output / config["outputs"]["manifest"], manifest)
    print(
        json.dumps(
            {
                "campaign_decision": campaign_decision,
                "survivors": survivors,
                "candidate_rows": len(replay.candidates),
                "trade_rows": len(replay.trades),
                "result": str(output / config["outputs"]["result_markdown"]),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

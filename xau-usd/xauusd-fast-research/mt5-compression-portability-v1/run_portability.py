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

from portability import evaluate_gate, run_portability, stage_metrics  # noqa: E402


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
        json.dumps(_json_ready(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _frame_digest(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return hashlib.sha256(b"").hexdigest()
    payload = frame[columns].to_csv(
        index=False, lineterminator="\n", float_format="%.10g"
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _report(result: dict[str, Any], metrics: pd.DataFrame) -> str:
    lines = [
        "# MT5 Compression Breakout Dukascopy Portability V1 Result",
        "",
        f"Decision: **{result['decision']}**",
        "",
        "Research only. This does not authorize model training, EA consumption, demo orders, or live orders.",
        "",
        "## Stage Metrics",
        "",
        "| Policy | Stage | Trades | Trades/day | Stress PF | Avg stress R | DD R | Top removed R | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in metrics.to_dict("records"):
        pf = "NA" if row["stress_pf"] is None else f"{row['stress_pf']:.3f}"
        gate = "PASS" if row["gate_pass"] else "FAIL"
        lines.append(
            f"| `{row['policy_id']}` | `{row['stage']}` | {row['trades']} | "
            f"{row['trades_per_source_day']:.3f} | {pf} | "
            f"{row['average_stress_r']:.3f} | {row['closed_drawdown_r']:.3f} | "
            f"{row['top_winners_removed_stress_net_r']:.3f} | {gate} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            result["interpretation"],
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    config_path = ROOT / "config" / "mt5_compression_portability_v1.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    run = run_portability(config)
    rows: list[dict[str, Any]] = []
    audit: dict[str, Any] = {}
    for policy_id, policy in config["policies"].items():
        policy_frame = run.policy_trades.loc[
            run.policy_trades["policy_id"].eq(policy_id)
        ]
        eligible = bool(policy["eligible_for_decision"])
        audit[policy_id] = {}
        for stage, (start_text, end_text) in config["windows"].items():
            gate = config["gates"][stage]
            value = stage_metrics(
                policy_frame,
                run.source_m5,
                pd.Timestamp(start_text),
                pd.Timestamp(end_text),
                int(gate["top_winners_removed"]),
            )
            passed, checks = evaluate_gate(value, gate)
            audit[policy_id][stage] = {
                "eligible_for_decision": eligible,
                "gate_pass": passed,
                "checks": checks,
                "metrics": value,
            }
            rows.append(
                {
                    "policy_id": policy_id,
                    "stage": stage,
                    "eligible_for_decision": eligible,
                    "gate_pass": passed,
                    **value,
                }
            )
    metric_frame = pd.DataFrame(rows)
    primary_id = "PORTFOLIO_CONSTRAINED_PRIMARY"
    primary_pass = all(
        audit[primary_id][stage]["gate_pass"] for stage in config["windows"]
    )
    if primary_pass:
        decision = "RETROSPECTIVE_PORTABILITY_SURVIVOR_REQUIRES_FORWARD_SHADOW"
        interpretation = (
            "The portfolio-constrained rule passed every frozen Dukascopy stability gate. "
            "It remains retrospective and requires exact-tick parity plus prospective shadow evidence."
        )
    else:
        decision = "REJECT_PORTABILITY"
        interpretation = (
            "The portfolio-constrained rule failed at least one frozen Dukascopy stability gate. "
            "The MT5 headline is not portable enough for specialist qualification."
        )
    result = {
        "schema_version": config["schema_version"],
        "decision": decision,
        "primary_policy": primary_id,
        "gate_audit": audit,
        "data_evidence": run.evidence,
        "candidate_digest": _frame_digest(
            run.candidates,
            ["candidate_id", "signal_time", "accepted", "rejection_reason"],
        ),
        "trade_digest": _frame_digest(
            run.policy_trades,
            ["policy_id", "candidate_id", "entry_time", "exit_time", "stress_net_r"],
        ),
        "interpretation": interpretation,
        "authorization": config["research_controls"],
    }
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    run.candidates.to_csv(
        output / config["outputs"]["candidates"], index=False, lineterminator="\n"
    )
    run.all_trades.to_csv(
        output / config["outputs"]["all_trades"], index=False, lineterminator="\n"
    )
    run.policy_trades.to_csv(
        output / config["outputs"]["policy_trades"], index=False, lineterminator="\n"
    )
    metric_frame.to_csv(
        output / config["outputs"]["stage_metrics"], index=False, lineterminator="\n"
    )
    _write_json(output / config["outputs"]["result_json"], result)
    (output / config["outputs"]["result_markdown"]).write_text(
        _report(result, metric_frame), encoding="utf-8"
    )
    _write_json(
        output / config["outputs"]["manifest"],
        {
            "config_sha256": _sha256(config_path),
            "feature_sha256": run.evidence["feature_sha256"],
            "candidate_digest": result["candidate_digest"],
            "trade_digest": result["trade_digest"],
            "candidate_rows": int(len(run.candidates)),
            "all_trade_rows": int(len(run.all_trades)),
            "policy_trade_rows": int(len(run.policy_trades)),
        },
    )
    print(
        json.dumps(
            {
                "decision": decision,
                "candidate_rows": len(run.candidates),
                "all_trade_rows": len(run.all_trades),
                "result": str(output / config["outputs"]["result_markdown"]),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

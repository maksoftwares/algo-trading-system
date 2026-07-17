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
EXECUTION_SRC = ROOT.parent / "ml-candidate-rankers-v1" / "src"
sys.path.insert(0, str(LOCAL_SRC))
sys.path.insert(0, str(EXECUTION_SRC))

from data import load_inputs, sha256_file  # noqa: E402
from engine import (  # noqa: E402
    _select_trades,
    _source_days,
    evaluate_gate,
    label_candidates,
    metrics,
    portfolio_exam,
)
from specialists import FAMILIES, generate_candidates  # noqa: E402


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


def evaluate_stages(
    labeled: pd.DataFrame, m5: pd.DataFrame, config: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], list[str]]:
    selected_frames: list[pd.DataFrame] = []
    metric_rows: list[dict[str, Any]] = []
    audit: dict[str, Any] = {family: {} for family in FAMILIES}
    exam_selected: dict[str, pd.DataFrame] = {}
    for family in FAMILIES:
        family_rows = labeled.loc[labeled["family_id"].eq(family)].copy()
        eligible = True
        for stage in ("train", "validation", "internal_test", "exam"):
            start, end = map(pd.Timestamp, config["windows"][stage])
            stage_rows = family_rows.loc[
                (family_rows["entry_time"] >= start) & (family_rows["entry_time"] < end)
            ]
            selected = _select_trades(stage_rows, float("-inf"), config["execution"])
            if not selected.empty:
                selected = selected.copy()
                selected["stage"] = stage
                selected_frames.append(selected)
            if stage == "exam":
                exam_selected[family] = selected
            gate = config["gates"][stage]
            value = metrics(
                selected,
                _source_days(m5, start, end),
                int(gate["top_winners_removed"]),
            )
            raw_pass, checks = evaluate_gate(value, gate)
            decision_eligible = bool(eligible)
            promoted = bool(eligible and raw_pass)
            audit[family][stage] = {
                "decision_eligible": decision_eligible,
                "raw_gate_pass": raw_pass,
                "promoted": promoted,
                "checks": checks,
                "metrics": value,
            }
            metric_rows.append(
                {
                    "family_id": family,
                    "stage": stage,
                    "decision_eligible": decision_eligible,
                    "raw_gate_pass": raw_pass,
                    "promoted": promoted,
                    **value,
                }
            )
            eligible = promoted
        tail_start, tail_end = map(pd.Timestamp, config["windows"]["recent_tail"])
        tail = exam_selected.get(family, pd.DataFrame())
        if not tail.empty:
            tail = tail.loc[
                (tail["entry_time"] >= tail_start) & (tail["entry_time"] < tail_end)
            ].copy()
            tail["stage"] = "recent_tail"
        gate = config["gates"]["recent_tail"]
        value = metrics(
            tail,
            _source_days(m5, tail_start, tail_end),
            int(gate["top_winners_removed"]),
        )
        raw_pass, checks = evaluate_gate(value, gate)
        decision_eligible = bool(eligible)
        promoted = bool(eligible and raw_pass)
        audit[family]["recent_tail"] = {
            "decision_eligible": decision_eligible,
            "raw_gate_pass": raw_pass,
            "promoted": promoted,
            "checks": checks,
            "metrics": value,
        }
        metric_rows.append(
            {
                "family_id": family,
                "stage": "recent_tail",
                "decision_eligible": decision_eligible,
                "raw_gate_pass": raw_pass,
                "promoted": promoted,
                **value,
            }
        )
    survivors = [family for family in FAMILIES if audit[family]["recent_tail"]["promoted"]]
    selected = pd.concat(selected_frames, ignore_index=True) if selected_frames else pd.DataFrame()
    return selected, pd.DataFrame(metric_rows), audit, survivors


def render_report(payload: dict[str, Any], stages: pd.DataFrame) -> str:
    lines = [
        "# XAUUSD Intraday Macro Specialists V1 Result",
        "",
        f"Decision: **{payload['decision']}**",
        "",
        "Research only. No family is authorized for Python prediction, EA consumption, demo, or live execution.",
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
    config_path = ROOT / "config" / "intraday_macro_specialists_v1.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    inputs = load_inputs(config)
    m5 = inputs.gold.bars["M5"]
    candidates = generate_candidates(inputs.gold.bars["M15"], inputs.macro_m15, config)
    labeled = label_candidates(candidates, m5, config["execution"])
    selected, stages, audit, survivors = evaluate_stages(labeled, m5, config)
    portfolio_trades, portfolio = portfolio_exam(selected, survivors, m5, config)
    if portfolio["pass"]:
        decision = "RETROSPECTIVE_INTRADAY_MACRO_PORTFOLIO_SURVIVOR_REQUIRES_VALIDATION"
        interpretation = (
            "At least two specialists survived the frozen chronological and portfolio gates. "
            "Independent reproduction, cost sensitivity, exact-tick parity, and forward shadow remain mandatory."
        )
    elif survivors:
        decision = "NO_ACCEPTABLE_INTRADAY_MACRO_PORTFOLIO"
        interpretation = (
            "At least one specialist survived alone, but breadth, independence, frequency, or portfolio gates failed."
        )
    else:
        decision = "NO_INTRADAY_MACRO_SPECIALIST_SURVIVOR"
        interpretation = "No frozen family passed the full chronological firewall. V1 is rejected without tuning."
    candidate_digest = frame_digest(
        labeled,
        ["family_id", "signal_time", "direction", "entry_time", "exit_time", "stress_net_r"],
    )
    selected_digest = frame_digest(
        selected,
        ["family_id", "stage", "entry_time", "exit_time", "direction", "stress_net_r"],
    )
    payload = {
        "schema_version": config["schema_version"],
        "decision": decision,
        "interpretation": interpretation,
        "survivors": survivors,
        "gate_audit": audit,
        "portfolio": portfolio,
        "mechanical_candidate_rows": int(len(candidates)),
        "labeled_candidate_rows": int(len(labeled)),
        "selected_trade_rows": int(len(selected)),
        "portfolio_trade_rows": int(len(portfolio_trades)),
        "candidate_digest": candidate_digest,
        "selected_digest": selected_digest,
        "data_evidence": inputs.evidence,
        "authorization": config["research_controls"],
    }
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    labeled.to_csv(output / config["outputs"]["candidate_ledger"], index=False, lineterminator="\n")
    selected.to_csv(output / config["outputs"]["selected_trade_ledger"], index=False, lineterminator="\n")
    stages.to_csv(output / config["outputs"]["stage_metrics"], index=False, lineterminator="\n")
    write_json(output / config["outputs"]["result_json"], payload)
    (output / config["outputs"]["result_markdown"]).write_text(
        render_report(payload, stages), encoding="utf-8"
    )
    manifest = {
        "config_sha256": sha256_file(config_path),
        "data_loader_sha256": sha256_file(LOCAL_SRC / "data.py"),
        "specialists_sha256": sha256_file(LOCAL_SRC / "specialists.py"),
        "execution_engine_sha256": sha256_file(EXECUTION_SRC / "engine.py"),
        "gold_feature_sha256": inputs.evidence["gold"]["feature_sha256"],
        "macro_feature_sha256": inputs.evidence["intraday_macro"]["feature_sha256"],
        "mechanical_candidate_rows": int(len(candidates)),
        "labeled_candidate_rows": int(len(labeled)),
        "selected_trade_rows": int(len(selected)),
        "candidate_digest": candidate_digest,
        "selected_digest": selected_digest,
    }
    write_json(output / config["outputs"]["manifest"], manifest)
    print(
        json.dumps(
            {
                "decision": decision,
                "survivors": survivors,
                "mechanical_candidates": len(candidates),
                "labeled_candidates": len(labeled),
                "selected_trades": len(selected),
                "result": str(output / config["outputs"]["result_markdown"]),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

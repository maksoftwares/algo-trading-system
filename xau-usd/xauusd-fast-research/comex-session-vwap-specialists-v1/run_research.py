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
ENGINE_SRC = ROOT.parent / "ml-candidate-rankers-v1" / "src"
sys.path.insert(0, str(LOCAL_SRC))
sys.path.insert(0, str(ENGINE_SRC))

from data import load_inputs, sha256_file  # noqa: E402
from engine import _select_trades, _source_days, evaluate_gate, label_candidates, metrics  # noqa: E402
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
    payload = frame[columns].to_csv(
        index=False, lineterminator="\n", float_format="%.10g"
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def evaluate_stages(
    labeled: pd.DataFrame,
    m5: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], list[str]]:
    selected_frames: list[pd.DataFrame] = []
    metric_rows: list[dict[str, Any]] = []
    audit: dict[str, Any] = {family: {} for family in FAMILIES}
    survivors: list[str] = []
    for family in FAMILIES:
        eligible = True
        family_rows = labeled.loc[labeled["family_id"].eq(family)]
        for stage in ("fit", "development"):
            start, end = map(pd.Timestamp, config["windows"][stage])
            rows = family_rows.loc[
                (family_rows["entry_time"] >= start) & (family_rows["entry_time"] < end)
            ]
            selected = _select_trades(rows, float("-inf"), config["execution"])
            if not selected.empty:
                selected = selected.copy()
                selected["stage"] = stage
                selected_frames.append(selected)
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
        if eligible:
            survivors.append(family)
    selected_all = pd.concat(selected_frames, ignore_index=True) if selected_frames else pd.DataFrame()
    return selected_all, pd.DataFrame(metric_rows), audit, survivors


def render_report(payload: dict[str, Any], stages: pd.DataFrame) -> str:
    lines = [
        "# XAUUSD COMEX Session-VWAP Specialists V1 Result",
        "",
        f"Decision: **{payload['decision']}**",
        "",
        "Research only. No Python prediction, EA, demo, live, or broker authorization is granted.",
        "",
        "| Family | Stage | Eligible | Trades | Trades/day | Stress PF | Avg R | Drawdown R | Top five removed R | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in stages.to_dict("records"):
        pf = row["stress_pf"]
        status = "PASS" if row["promoted"] else "FAIL" if row["decision_eligible"] else "INELIGIBLE"
        lines.append(
            f"| `{row['family_id']}` | {row['stage']} | {row['decision_eligible']} | "
            f"{row['trades']} | {row['trades_per_source_day']:.3f} | "
            f"{'NA' if pf is None else f'{pf:.3f}'} | {row['average_stress_r']:.3f} | "
            f"{row['closed_drawdown_r']:.3f} | {row['top_winners_removed_stress_net_r']:.3f} | {status} |"
        )
    lines.extend(["", "## Interpretation", "", payload["interpretation"], ""])
    return "\n".join(lines)


def main() -> int:
    config_path = ROOT / "config" / "comex_session_vwap_specialists_v1.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    inputs = load_inputs(config)
    m5 = inputs.gold.bars["M5"]
    candidates = generate_candidates(m5, inputs.comex_vwap, config)
    labeled = label_candidates(candidates, m5, config["execution"])
    selected, stages, audit, survivors = evaluate_stages(labeled, m5, config)
    if survivors:
        decision = "EXTEND_COMEX_VWAP_CACHE_FOR_EXAM"
        interpretation = (
            "At least one frozen family passed fit and development. Build the 2024-26 COMEX VWAP cache, "
            "then run an unchanged exam before making any further claim."
        )
    else:
        decision = "REJECT_COMEX_SESSION_VWAP_V1"
        interpretation = (
            "Neither frozen family passed the chronological fit and development firewall. "
            "Do not spend time extending the cache for this version."
        )
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
        "mechanical_candidate_rows": int(len(candidates)),
        "labeled_candidate_rows": int(len(labeled)),
        "selected_trade_rows": int(len(selected)),
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
        "execution_engine_sha256": sha256_file(ENGINE_SRC / "engine.py"),
        "gold_feature_sha256": inputs.evidence["gold"]["feature_sha256"],
        "comex_vwap_sha256": inputs.evidence["comex_vwap"]["sha256"],
        "candidate_digest": candidate_digest,
        "selected_digest": selected_digest,
        "mechanical_candidate_rows": int(len(candidates)),
        "labeled_candidate_rows": int(len(labeled)),
        "selected_trade_rows": int(len(selected)),
    }
    write_json(output / config["outputs"]["manifest"], manifest)
    print(json.dumps({"decision": decision, "survivors": survivors, "candidates": len(candidates), "selected": len(selected)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import csv
import json
import math
import os
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.campaign import (  # noqa: E402
    benjamini_hochberg,
    build_or_load_h1_cache,
    write_csv,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def number(value: str) -> float:
    return float(value)


def main() -> int:
    config = json.loads(
        (ROOT / "config" / "eurusd_thousand_strategy_campaign_v1.json").read_text(
            encoding="utf-8"
        )
    )
    outputs = ROOT / "outputs"
    storage_root = Path(
        os.environ.get(
            config["source"]["storage_environment_variable"],
            config["source"]["default_storage_root"],
        )
    )
    _, source_metadata = build_or_load_h1_cache(storage_root, config)
    result_path = outputs / "EURUSD_HUNT_V1_RESULT.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["source"] = source_metadata
    result_path.write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    metrics = read_csv(outputs / "EURUSD_HUNT_V1_DISCOVERY_METRICS.csv")
    by_candidate: dict[str, dict[str, dict[str, str]]] = {}
    for row in metrics:
        by_candidate.setdefault(row["candidate_id"], {})[row["stage"]] = row
    p_values = {
        candidate_id: max(
            number(stages["discovery_fit"]["one_sided_mean_p_value"]),
            number(stages["discovery_confirm"]["one_sided_mean_p_value"]),
        )
        for candidate_id, stages in by_candidate.items()
    }
    adjusted = benjamini_hochberg(p_values)
    gates = config["discovery_gates"]
    census = []
    failure_counts: Counter[str] = Counter()
    for candidate_id, stages in by_candidate.items():
        candidate_failures = []
        row: dict[str, object] = {
            "candidate_id": candidate_id,
            "archetype": stages["discovery_fit"]["archetype"],
            "direction": stages["discovery_fit"]["direction"],
            "threshold": number(stages["discovery_fit"]["threshold"]),
            "stop_atr": number(stages["discovery_fit"]["stop_atr"]),
            "target_r": number(stages["discovery_fit"]["target_r"]),
        }
        stage_passes = []
        for stage in ("discovery_fit", "discovery_confirm"):
            source = stages[stage]
            checks = {
                "trades": int(source["trades"]) >= gates["minimum_trades"],
                "stress_pf": number(source["stress_profit_factor"])
                >= gates["minimum_stress_profit_factor"],
                "stress_net": number(source["stress_net_pips"])
                > gates["minimum_stress_net_pips"],
                "positive_month_share": number(
                    source["positive_active_month_share"]
                )
                >= gates["minimum_positive_active_month_share"],
                "top5_removed_pf": number(source["top5_removed_profit_factor"])
                >= gates["minimum_top5_removed_profit_factor"],
            }
            for gate_name, passed in checks.items():
                row[f"{stage}_{gate_name}_pass"] = passed
                if not passed:
                    failure = f"{stage}:{gate_name}"
                    candidate_failures.append(failure)
                    failure_counts[failure] += 1
            row[f"{stage}_trades"] = int(source["trades"])
            row[f"{stage}_stress_pf"] = number(source["stress_profit_factor"])
            row[f"{stage}_stress_net_pips"] = number(source["stress_net_pips"])
            stage_passes.append(all(checks.values()))
        weakest_pf = min(
            float(row["discovery_fit_stress_pf"]),
            float(row["discovery_confirm_stress_pf"]),
        )
        row["weakest_discovery_stress_pf"] = weakest_pf
        row["both_stage_gates_pass"] = all(stage_passes)
        row["worst_one_sided_p_value"] = p_values[candidate_id]
        row["bh_adjusted_p_value"] = adjusted[candidate_id]
        row["fdr_gate_pass"] = (
            adjusted[candidate_id] <= config["selection"]["false_discovery_rate"]
        )
        if not row["fdr_gate_pass"]:
            candidate_failures.append("campaign:fdr")
            failure_counts["campaign:fdr"] += 1
        row["failure_reasons"] = "|".join(candidate_failures)
        census.append(row)

    census.sort(
        key=lambda row: (
            bool(row["both_stage_gates_pass"]),
            float(row["weakest_discovery_stress_pf"])
            if math.isfinite(float(row["weakest_discovery_stress_pf"]))
            else -math.inf,
            int(row["discovery_fit_trades"])
            + int(row["discovery_confirm_trades"]),
        ),
        reverse=True,
    )
    write_csv(outputs / "EURUSD_HUNT_V1_CANDIDATE_GATE_CENSUS.csv", census)
    near = [
        row
        for row in census
        if int(row["discovery_fit_trades"]) >= gates["minimum_trades"]
        and int(row["discovery_confirm_trades"]) >= gates["minimum_trades"]
    ][:20]
    diagnostic = {
        "schema_version": "eurusd_hunt_v1_gate_diagnostic",
        "candidates": len(census),
        "both_stage_gate_pass": sum(
            bool(row["both_stage_gates_pass"]) for row in census
        ),
        "both_stage_and_fdr_pass": sum(
            bool(row["both_stage_gates_pass"]) and bool(row["fdr_gate_pass"])
            for row in census
        ),
        "failure_counts": dict(sorted(failure_counts.items())),
        "top_twenty_minimum_trade_near_misses": near,
        "interpretation": (
            "No candidate is authorized. Later windows remain unopened. "
            "Near-miss rankings are diagnostic only and cannot be tuned in V1."
        ),
    }
    (outputs / "EURUSD_HUNT_V1_GATE_DIAGNOSTIC.json").write_text(
        json.dumps(diagnostic, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    write_csv(
        outputs / "EURUSD_HUNT_V1_SHORTLIST.csv",
        [],
        fieldnames=[
            "candidate_id",
            "attempt",
            "archetype",
            "direction",
            "threshold",
            "stop_atr",
            "target_r",
            "max_hold_bars",
            "sha256",
            "fit_trades",
            "fit_stress_pf",
            "confirm_trades",
            "confirm_stress_pf",
            "weakest_discovery_stress_pf",
            "worst_one_sided_p_value",
            "bh_adjusted_p_value",
            "both_stage_gates_pass",
            "fdr_gate_pass",
        ],
    )
    write_csv(
        outputs / "EURUSD_HUNT_V1_SHORTLIST_TRADES.csv",
        [],
        fieldnames=[
            "candidate_id",
            "archetype",
            "direction",
            "signal_time",
            "entry_time",
            "exit_time",
            "entry",
            "exit",
            "stop",
            "target",
            "spread_pips",
            "net_pips",
            "stress_net_pips",
            "exit_reason",
            "stage",
        ],
    )
    print(json.dumps(diagnostic, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

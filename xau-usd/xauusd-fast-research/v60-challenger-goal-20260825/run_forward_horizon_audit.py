from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
V6_ROOT = (
    REPO_ROOT
    / "xau-usd"
    / "xauusd-fast-research"
    / "v60-dynamic-followthrough-union-v6"
)
PROSPECTIVE_ROOT = (
    REPO_ROOT
    / "xau-usd"
    / "xauusd-fast-research"
    / "v60-dynamic-followthrough-union-prospective-v6"
)
OUTPUT_JSON = ROOT / "FORWARD_COMPONENT_HORIZON_AUDIT.json"
OUTPUT_MD = ROOT / "FORWARD_COMPONENT_HORIZON_AUDIT.md"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def poisson_probability_at_least(target: int, mean: float) -> float:
    if target <= 0:
        return 1.0
    if mean < 0.0 or not math.isfinite(mean):
        raise ValueError("Poisson mean must be finite and nonnegative")
    probability_below = math.exp(-mean) * sum(
        mean**value / math.factorial(value) for value in range(target)
    )
    return 1.0 - probability_below


def poisson_mean_for_probability(target: int, probability: float) -> float:
    if target <= 0:
        return 0.0
    if not 0.0 < probability < 1.0:
        raise ValueError("Probability must be strictly between zero and one")
    low = 0.0
    high = float(max(1, target))
    while poisson_probability_at_least(target, high) < probability:
        high *= 2.0
    for _ in range(100):
        middle = (low + high) / 2.0
        if poisson_probability_at_least(target, middle) >= probability:
            high = middle
        else:
            low = middle
    return high


def component_horizon(
    *,
    observed_events: int,
    observed_trades: int,
    required_events: int,
    annual_trades: float,
) -> dict[str, Any]:
    if observed_events <= 0 or observed_trades <= 0 or annual_trades <= 0.0:
        raise ValueError("Observed events, trades, and annual trades must be positive")
    rate = observed_events / observed_trades
    expected_trades = required_events / rate
    mean_90 = poisson_mean_for_probability(required_events, 0.90)
    trades_90 = mean_90 / rate
    return {
        "observed_events": observed_events,
        "observed_trades": observed_trades,
        "event_rate_per_trade": rate,
        "required_events": required_events,
        "expected_trades_to_required_events": expected_trades,
        "expected_years_to_required_events": expected_trades / annual_trades,
        "trades_for_90_percent_poisson_probability": trades_90,
        "years_for_90_percent_poisson_probability": trades_90 / annual_trades,
    }


def build_result(
    v6: Mapping[str, Any],
    prospective: Mapping[str, Any],
    august_rows: pd.DataFrame,
) -> dict[str, Any]:
    baseline = v6["baseline"]
    acceptance = prospective["acceptance"]
    historical_trades = int(baseline["trades_closed"])
    annual_trades = float(baseline["trades_per_weekday"]) * 365.2425 * 5.0 / 7.0
    proposal_counts = v6["composition_audit"]["proposal_rule_counts"]
    v2_events = int(proposal_counts["V2_SOURCE_HEALTH"])
    anti_events = int(proposal_counts["V57_WEAK_FOLLOWTHROUGH_ANTICHASE"])
    union_events = int(v6["composition_audit"]["executed_vetoes"])

    executed_august = august_rows.loc[
        august_rows["baseline_executed"].astype(str).str.lower().eq("true")
    ]
    recent_anti = int(
        executed_august["refined_antichase_proposal"]
        .astype(str)
        .str.lower()
        .eq("true")
        .sum()
    )
    recent_v2 = int(
        executed_august["v2_baseline_path_proposal"]
        .astype(str)
        .str.lower()
        .eq("true")
        .sum()
    )
    recent_trades = int(len(executed_august))
    pooled_anti = component_horizon(
        observed_events=anti_events + recent_anti,
        observed_trades=historical_trades + recent_trades,
        required_events=int(acceptance["minimum_resolved_anti_chase_vetoes"]),
        annual_trades=annual_trades,
    )
    return {
        "schema_version": "v60_dynamic_v6_forward_component_horizon_v1",
        "evidence_status": "DESCRIPTIVE_PLANNING_APPROXIMATION_NOT_AN_ACCEPTANCE_GATE",
        "deployment_authorized": False,
        "historical_baseline_trades": historical_trades,
        "annualized_baseline_trades": annual_trades,
        "arithmetic_retention_floor": {
            "minimum_resolved_baseline_executions": int(
                acceptance["minimum_resolved_baseline_executions"]
            ),
            "minimum_resolved_union_vetoes": int(
                acceptance["minimum_resolved_vetoes"]
            ),
            "minimum_trade_retention": float(acceptance["minimum_trade_retention"]),
            "years_at_historical_frequency": int(
                acceptance["minimum_resolved_baseline_executions"]
            )
            / annual_trades,
        },
        "historical_rate_scenarios": {
            "v2_source_health": component_horizon(
                observed_events=v2_events,
                observed_trades=historical_trades,
                required_events=int(acceptance["minimum_resolved_v2_vetoes"]),
                annual_trades=annual_trades,
            ),
            "v57_weak_followthrough_anti_chase": component_horizon(
                observed_events=anti_events,
                observed_trades=historical_trades,
                required_events=int(
                    acceptance["minimum_resolved_anti_chase_vetoes"]
                ),
                annual_trades=annual_trades,
            ),
            "union": component_horizon(
                observed_events=union_events,
                observed_trades=historical_trades,
                required_events=int(acceptance["minimum_resolved_vetoes"]),
                annual_trades=annual_trades,
            ),
        },
        "exposed_august_diagnostic": {
            "baseline_trades": recent_trades,
            "v2_events": recent_v2,
            "anti_chase_events": recent_anti,
            "selection_contaminated": True,
        },
        "pooled_historical_plus_exposed_anti_chase_scenario": {
            **pooled_anti,
            "selection_contaminated": True,
            "not_usable_for_authorization": True,
        },
        "planning_conclusion": (
            "The anti-chase component is the evidence bottleneck. Preserve frozen V6 "
            "collection, but research a higher-support causal August mechanism under a "
            "separate preregistration instead of weakening V6's component gates."
        ),
        "limitations": [
            "Event arrivals are clustered and not truly Poisson; the 90% horizon is a planning approximation.",
            "The August anti-chase rate is selection-contaminated and cannot estimate authorization evidence.",
            "No horizon estimate substitutes for actual causal forward outcomes.",
        ],
    }


def write_outputs(result: Mapping[str, Any]) -> None:
    OUTPUT_JSON.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    scenarios = result["historical_rate_scenarios"]
    lines = [
        "# Dynamic V6 Forward Component Horizon Audit",
        "",
        "Descriptive planning only. This report never authorizes deployment.",
        "",
        "| Component | Observed events | Historical rate | Expected years | 90% Poisson years |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, item in scenarios.items():
        lines.append(
            f"| {name} | {item['observed_events']} | {item['event_rate_per_trade']:.4%} | "
            f"{item['expected_years_to_required_events']:.2f} | "
            f"{item['years_for_90_percent_poisson_probability']:.2f} |"
        )
    lines.extend(
        [
            "",
            f"The 2,000-trade retention floor is about {result['arithmetic_retention_floor']['years_at_historical_frequency']:.2f} years at the historical frequency.",
            "",
            result["planning_conclusion"],
            "",
            "The exposed August rate is not authorization evidence.",
            "",
        ]
    )
    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    v6_path = V6_ROOT / "outputs" / "RESULT.json"
    prospective_path = PROSPECTIVE_ROOT / "config" / "prospective.json"
    august_path = V6_ROOT / "outputs" / "AUGUST_2026_TRADE_AUDIT.csv"
    v6 = json.loads(v6_path.read_text(encoding="utf-8"))
    prospective = json.loads(
        prospective_path.read_text(encoding="utf-8")
    )
    august = pd.read_csv(august_path)
    result = build_result(v6, prospective, august)
    result["input_sha256"] = {
        "v6_result": sha256_file(v6_path),
        "prospective_contract": sha256_file(prospective_path),
        "august_trade_audit": sha256_file(august_path),
    }
    write_outputs(result)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

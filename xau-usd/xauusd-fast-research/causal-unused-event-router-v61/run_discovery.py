from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from src.router import (  # noqa: E402
    causal_state_health,
    development_passes,
    eligible_actions,
    enrich_actions,
    evaluate_policy,
    govern_new_lane,
    qualified_event_keys,
    verify_sources,
)


def flatten_metrics(metrics: dict[str, dict]) -> dict[str, float | int]:
    flat: dict[str, float | int] = {}
    for window_name, sources in metrics.items():
        for source_name, values in sources.items():
            for metric, value in values.items():
                flat[f"{window_name}_{source_name}_{metric}"] = value
    return flat


def main() -> None:
    config_path = ROOT / "config" / "causal_unused_event_router_v61.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    verified = verify_sources(REPO_ROOT, config["sources"])
    sources = config["sources"]
    cutoff = pd.Timestamp(config["development_cutoff_exclusive_utc"])

    actions = enrich_actions(
        pd.read_parquet(REPO_ROOT / sources["action_ledger"]["path"])
    )
    actions = actions.loc[
        actions["signal_time"].lt(cutoff) & actions["exit_time"].lt(cutoff)
    ].copy()
    v57 = pd.read_parquet(
        REPO_ROOT / sources["qualified_v57_candidates"]["path"]
    )
    excluded_keys = qualified_event_keys(v57)
    frozen = pd.read_parquet(REPO_ROOT / sources["frozen_v59_trades"]["path"])
    for column in ("signal_time", "entry_time", "exit_time"):
        frozen[column] = pd.to_datetime(frozen[column], utc=True)

    grid = config["policy_grid"]
    filter_config = config["candidate_filter"]
    rows: list[dict] = []
    selected_by_policy: dict[str, pd.DataFrame] = {}
    for schema_index, state_schema in enumerate(grid["state_schemas"], start=1):
        for short_window, long_window in grid["short_long_windows"]:
            health = causal_state_health(
                actions,
                state_schema,
                int(short_window),
                int(long_window),
            )
            for minimum_pf in grid["minimum_profit_factors"]:
                policy_id = (
                    f"S{schema_index}_W{short_window}_{long_window}"
                    f"_PF{str(minimum_pf).replace('.', 'P')}"
                )
                candidates = eligible_actions(
                    health,
                    excluded_keys,
                    float(filter_config["maximum_risk_usd"]),
                    int(short_window),
                    int(long_window),
                    float(minimum_pf),
                )
                selected = govern_new_lane(candidates, frozen, config["account"])
                metrics = evaluate_policy(
                    selected, frozen, config["windows"], cutoff
                )
                passed = development_passes(metrics, config["development_gates"])
                rows.append(
                    {
                        "policy_id": policy_id,
                        "state_schema": "|".join(state_schema),
                        "short_window": int(short_window),
                        "long_window": int(long_window),
                        "minimum_profit_factor": float(minimum_pf),
                        "eligible_unused_events": int(len(candidates)),
                        "selected_new_trades_total": int(len(selected)),
                        "passed_development": bool(passed),
                        **flatten_metrics(metrics),
                    }
                )
                selected_by_policy[policy_id] = selected

    result = pd.DataFrame(rows)
    result["minimum_development_new_pf"] = result[
        [
            "development_1_new_profit_factor",
            "development_2_new_profit_factor",
        ]
    ].min(axis=1)
    result = result.sort_values(
        [
            "passed_development",
            "minimum_development_new_pf",
            "development_2_combined_trades_per_weekday",
            "policy_id",
        ],
        ascending=[False, False, False, True],
        kind="mergesort",
    ).reset_index(drop=True)
    passing = result.loc[result["passed_development"]]
    selected_policy = str(passing.iloc[0]["policy_id"]) if len(passing) else None

    output_dir = ROOT / config["outputs"]["directory"]
    output_dir.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_dir / config["outputs"]["policy_grid"], index=False)
    if selected_policy is not None:
        selected_by_policy[selected_policy].to_parquet(
            output_dir / config["outputs"]["selected_new_trades"], index=False
        )
    payload = {
        "schema_version": config["schema_version"],
        "development_cutoff_exclusive_utc": str(cutoff),
        "verified_sources": verified,
        "policy_count": int(len(result)),
        "passing_policy_count": int(result["passed_development"].sum()),
        "selected_policy_id": selected_policy,
        "selected_policy": (
            result.iloc[0].to_dict() if selected_policy is not None else None
        ),
        "research_controls": config["research_controls"],
    }
    (output_dir / config["outputs"]["result_json"]).write_text(
        json.dumps(payload, indent=2, allow_nan=False, default=str) + "\n",
        encoding="utf-8",
    )
    columns = [
        "policy_id",
        "state_schema",
        "short_window",
        "long_window",
        "minimum_profit_factor",
        "passed_development",
        "development_1_new_trades",
        "development_1_new_profit_factor",
        "development_1_new_net_usd",
        "development_2_new_trades",
        "development_2_new_profit_factor",
        "development_2_new_net_usd",
        "development_2_combined_trades_per_weekday",
        "development_2_combined_profit_factor",
        "development_2_combined_closed_drawdown_usd",
    ]
    print(result.loc[:, columns].head(12).to_string(index=False))
    print(json.dumps(payload, indent=2, allow_nan=False, default=str))


if __name__ == "__main__":
    main()

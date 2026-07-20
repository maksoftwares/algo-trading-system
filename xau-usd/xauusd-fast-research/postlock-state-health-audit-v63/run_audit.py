from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def flatten(windows: pd.DataFrame) -> dict[str, float | int]:
    values: dict[str, float | int] = {}
    for row in windows.itertuples(index=False):
        for metric in (
            "trades",
            "trades_per_weekday",
            "net_usd",
            "profit_factor",
            "closed_drawdown_usd",
            "top5_removed_net_usd",
            "positive_month_share",
        ):
            values[f"{row.window}_{row.portfolio_id.lower()}_{metric}"] = getattr(
                row, metric
            )
    return values


def core_gate_pass(windows: pd.DataFrame, gates: dict) -> bool:
    lookup = windows.set_index(["window", "portfolio_id"])
    for window_name in gates["required_windows"]:
        new = lookup.loc[(window_name, "NEW")]
        combined = lookup.loc[(window_name, "COMBINED")]
        if not all(
            [
                new["trades"] >= gates["minimum_new_trades"],
                new["profit_factor"] >= gates["minimum_new_profit_factor"],
                new["net_usd"] > gates["minimum_new_net_usd"],
                new["top5_removed_net_usd"]
                > gates["minimum_new_top5_removed_net_usd"],
                combined["trades_per_weekday"]
                >= gates["minimum_combined_trades_per_weekday"],
                combined["profit_factor"]
                >= gates["minimum_combined_profit_factor"],
                combined["net_usd"] > gates["minimum_combined_net_usd"],
                combined["closed_drawdown_usd"]
                <= gates["maximum_combined_closed_drawdown_usd"],
            ]
        ):
            return False
    return True


def main() -> None:
    config = json.loads(
        (ROOT / "config" / "postlock_state_health_audit_v63.json").read_text(
            encoding="utf-8"
        )
    )
    source = config["sources"]
    v61_config = json.loads(
        (REPO_ROOT / source["v61_config"]).read_text(encoding="utf-8")
    )
    v62_config = json.loads(
        (REPO_ROOT / source["v62_config"]).read_text(encoding="utf-8")
    )
    router = load_module("v63_router", REPO_ROOT / source["v61_router_module"])
    evaluator = load_module(
        "v63_evaluator", REPO_ROOT / source["v62_evaluator_module"]
    )
    actions = router.enrich_actions(pd.read_parquet(REPO_ROOT / source["action_ledger"]))
    v57 = pd.read_parquet(REPO_ROOT / source["qualified_v57_candidates"])
    frozen = pd.read_parquet(REPO_ROOT / source["frozen_v59_trades"])
    for column in ("signal_time", "entry_time", "exit_time"):
        frozen[column] = pd.to_datetime(frozen[column], utc=True)
    excluded = router.qualified_event_keys(v57)

    rows: list[dict] = []
    grid = v61_config["policy_grid"]
    for schema_index, state_schema in enumerate(grid["state_schemas"], start=1):
        for short_window, long_window in grid["short_long_windows"]:
            health = router.causal_state_health(
                actions, state_schema, int(short_window), int(long_window)
            )
            for minimum_pf in grid["minimum_profit_factors"]:
                policy_id = (
                    f"S{schema_index}_W{short_window}_{long_window}"
                    f"_PF{str(minimum_pf).replace('.', 'P')}"
                )
                candidates = router.eligible_actions(
                    health,
                    excluded,
                    float(v61_config["candidate_filter"]["maximum_risk_usd"]),
                    int(short_window),
                    int(long_window),
                    float(minimum_pf),
                )
                selected = router.govern_new_lane(
                    candidates, frozen, v62_config["account"]
                )
                combined = pd.concat(
                    [frozen, selected], ignore_index=True, sort=False
                )
                windows = evaluator.evaluate_windows(
                    router, selected, combined, v62_config["windows"]
                )
                full_gates = evaluator.gate_results(windows, v62_config["gates"])
                rows.append(
                    {
                        "policy_id": policy_id,
                        "state_schema": "|".join(state_schema),
                        "short_window": int(short_window),
                        "long_window": int(long_window),
                        "minimum_profit_factor": float(minimum_pf),
                        "core_frequency_edge_dd_pass": core_gate_pass(
                            windows, v62_config["gates"]
                        ),
                        "full_v62_gate_pass": all(
                            result["passed"] for result in full_gates
                        ),
                        **flatten(windows),
                    }
                )
    frame = pd.DataFrame(rows).sort_values(
        [
            "core_frequency_edge_dd_pass",
            "final_combined_trades_per_weekday",
            "final_new_profit_factor",
            "policy_id",
        ],
        ascending=[False, False, False, True],
        kind="mergesort",
    )
    output_dir = ROOT / config["outputs"]["directory"]
    output_dir.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_dir / config["outputs"]["policy_audit"], index=False)
    payload = {
        "schema_version": config["schema_version"],
        "policy_count": int(len(frame)),
        "core_frequency_edge_dd_pass_count": int(
            frame["core_frequency_edge_dd_pass"].sum()
        ),
        "full_v62_gate_pass_count": int(frame["full_v62_gate_pass"].sum()),
        "maximum_final_combined_frequency": float(
            frame["final_combined_trades_per_weekday"].max()
        ),
        "maximum_final_frequency_with_positive_new_net": float(
            frame.loc[
                frame["final_new_net_usd"].gt(0.0),
                "final_combined_trades_per_weekday",
            ].max()
        ),
        "research_controls": config["research_controls"],
    }
    (output_dir / config["outputs"]["result"]).write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    columns = [
        "policy_id",
        "state_schema",
        "core_frequency_edge_dd_pass",
        "development_2_combined_trades_per_weekday",
        "confirmation_combined_trades_per_weekday",
        "final_combined_trades_per_weekday",
        "final_new_trades",
        "final_new_net_usd",
        "final_new_profit_factor",
        "final_combined_profit_factor",
        "final_combined_closed_drawdown_usd",
    ]
    print(frame.loc[:, columns].head(15).to_string(index=False))
    print(json.dumps(payload, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()

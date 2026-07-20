from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.scale import (  # noqa: E402
    apply_policy,
    candidate_signals,
    load_m5,
    market_arrays,
    parameter_grid,
    passes_gates,
    prepare_scale_features,
    simulate_candidates,
    variant_id,
    window_metrics,
)


def main() -> None:
    config_path = ROOT / "config" / "box_breakout_scale_replication_v65.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    m5, evidence = load_m5(config)
    arrays = market_arrays(m5)
    grid = list(parameter_grid(config))
    expected = int(config["research_controls"]["bounded_variant_count"])
    if len(grid) * len(config["scales"]) != expected:
        raise ValueError("V65 variant count does not match the preregistered bound")
    rows: list[dict] = []
    survivor_frames: list[pd.DataFrame] = []
    cache: dict[tuple, dict | None] = {}
    for scale in config["scales"]:
        features = prepare_scale_features(
            m5,
            scale,
            config["features"],
            sorted(set(config["parameter_grid"]["box_bars"])),
        )
        for params in grid:
            identity = variant_id(str(scale["scale_id"]), params)
            candidates = candidate_signals(features, params)
            outcomes = simulate_candidates(
                candidates,
                arrays,
                float(scale["maximum_hold_hours"]),
                config["execution"],
                cache,
            )
            trades = apply_policy(
                outcomes,
                int(config["execution"]["maximum_open_positions_per_variant"]),
                int(config["execution"]["maximum_entries_per_variant_utc_day"]),
            )
            metrics = {
                name: window_metrics(
                    trades,
                    pd.Timestamp(bounds[0]),
                    pd.Timestamp(bounds[1]),
                    int(config["gates"]["top_winners_removed"]),
                )
                for name, bounds in config["windows"].items()
            }
            passed = passes_gates(metrics, config["gates"])
            row = {
                "variant_id": identity,
                "scale_id": scale["scale_id"],
                **params,
                "candidate_signals": int(len(candidates)),
                "executable_outcomes": int(len(outcomes)),
                "policy_trades": int(len(trades)),
                "passed": bool(passed),
            }
            for window_name, values in metrics.items():
                for metric, value in values.items():
                    row[f"{window_name}_{metric}"] = value
            row["minimum_window_pf"] = min(
                values["stress_profit_factor"] for values in metrics.values()
            )
            row["minimum_window_frequency"] = min(
                values["trades_per_weekday"] for values in metrics.values()
            )
            rows.append(row)
            if passed:
                survivor_frames.append(
                    trades.assign(
                        variant_id=identity,
                        scale_id=scale["scale_id"],
                        direction=params["direction"],
                    )
                )
    result = pd.DataFrame(rows).sort_values(
        ["passed", "minimum_window_pf", "minimum_window_frequency", "variant_id"],
        ascending=[False, False, False, True],
        kind="mergesort",
    )
    survivors = (
        pd.concat(survivor_frames, ignore_index=True)
        if survivor_frames
        else pd.DataFrame()
    )
    output_dir = ROOT / config["outputs"]["directory"]
    output_dir.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_dir / config["outputs"]["metrics"], index=False)
    survivors.to_parquet(
        output_dir / config["outputs"]["survivor_trades"], index=False
    )
    payload = {
        "schema_version": config["schema_version"],
        "variant_count": int(len(result)),
        "survivor_count": int(result["passed"].sum()),
        "survivor_variant_ids": result.loc[
            result["passed"], "variant_id"
        ].tolist(),
        "outcome_cache_rows": int(len(cache)),
        "data_evidence": evidence,
        "research_controls": config["research_controls"],
    }
    (output_dir / config["outputs"]["result"]).write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    columns = [
        "variant_id",
        "scale_id",
        "direction",
        "regime_mode",
        "box_bars",
        "target_r",
        "passed",
        "development_1_trades_per_weekday",
        "development_1_stress_profit_factor",
        "development_2_trades_per_weekday",
        "development_2_stress_profit_factor",
        "confirmation_trades_per_weekday",
        "confirmation_stress_profit_factor",
        "minimum_window_pf",
    ]
    print(result.loc[:, columns].head(20).to_string(index=False))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

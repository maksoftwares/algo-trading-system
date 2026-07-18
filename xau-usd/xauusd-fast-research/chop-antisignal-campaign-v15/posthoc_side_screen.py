from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import run_screen as locked


ROOT = Path(__file__).resolve().parent


def main() -> int:
    config = json.loads(
        (ROOT / "config" / "chop_antisignal_campaign_v15.json").read_text(
            encoding="utf-8"
        )
    )
    lock = locked.verify_lock(config)
    output = ROOT / config["outputs"]["directory"]
    metrics_path = output / "CHOP_ANTISIGNAL_V15_POSTHOC_SIDE_METRICS.csv"
    summary_path = output / "CHOP_ANTISIGNAL_V15_POSTHOC_SIDE_SUMMARY.json"
    if metrics_path.exists() or summary_path.exists():
        raise FileExistsError("V15 post hoc side outputs already exist")

    manifest = pd.read_csv(output / config["outputs"]["manifest"])
    bundle = locked.DATA.load_bundle(config)
    frame = locked.CAMPAIGN.prepare_frame(
        bundle.bars["M15"],
        bundle.bars["H4"],
        config,
        locked.ADAPTIVE,
        locked.REGIMES,
        locked.BASE,
    )
    frame["entry_time_key"] = frame["bar_start_utc"].shift(-1)
    cache: dict[tuple[object, ...], dict[str, object] | None] = {}
    rows: list[dict[str, object]] = []
    for offset, item in enumerate(manifest.itertuples(index=False), 1):
        trades = locked.CAMPAIGN.simulate_variant(frame, item, config, cache)
        for side in ("LONG", "SHORT"):
            subset = trades.loc[trades["direction"].eq(side)]
            rows.append(
                {
                    **item._asdict(),
                    "side": side,
                    **locked.BASE.score_variant(subset, frame, config),
                }
            )
        if offset % 100 == 0:
            print(f"side_scored={offset}/{len(manifest)}", flush=True)

    metrics = pd.DataFrame(rows)
    metrics["daily_fdr_qvalue"] = locked.BASE.bh_adjust(metrics["daily_pvalue"])
    metrics["statistical_pass"] = metrics["daily_fdr_qvalue"].le(
        float(config["selection"]["false_discovery_rate"])
    )
    with metrics_path.open("w", encoding="utf-8", newline="\n") as handle:
        metrics.to_csv(handle, index=False, lineterminator="\n")

    eligible = metrics.loc[
        metrics["whole_trades"].ge(
            int(config["economic_gates"]["minimum_total_trades"])
        )
    ]
    ranked = eligible.sort_values(
        [
            "economic_pass",
            "minimum_era_stress_pf",
            "whole_stress_pf",
            "whole_trades",
        ],
        ascending=[False, False, False, False],
        kind="mergesort",
    )
    summary = {
        "schema_version": "xauusd_chop_antisignal_v15_posthoc_side_screen",
        "contract_sha256": lock["contract_sha256"],
        "hypotheses_scored": int(len(metrics)),
        "posthoc_exploratory_only": True,
        "can_qualify_v15": False,
        "economic_passes": int(metrics["economic_pass"].sum()),
        "fdr_and_economic_passes": int(
            (metrics["economic_pass"] & metrics["statistical_pass"]).sum()
        ),
        "best_eligible": [
            {
                "attempt_no": int(row.attempt_no),
                "paired_source_attempt_no": int(row.paired_source_attempt_no),
                "mechanic": str(row.mechanic),
                "side": str(row.side),
                "trades": int(row.whole_trades),
                "stress_net_r": float(row.whole_stress_net_r),
                "stress_pf": float(row.whole_stress_pf),
                "minimum_era_trades": int(row.minimum_era_trades),
                "minimum_era_stress_pf": float(row.minimum_era_stress_pf),
                "minimum_era_average_stress_r": float(
                    row.minimum_era_average_stress_r
                ),
                "economic_pass": bool(row.economic_pass),
                "daily_fdr_qvalue": float(row.daily_fdr_qvalue),
                "parameters_json": str(row.parameters_json),
            }
            for row in ranked.head(20).itertuples(index=False)
        ],
        "training_authorized": False,
        "execution_authorized": False,
    }
    locked.write_json(summary_path, summary)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

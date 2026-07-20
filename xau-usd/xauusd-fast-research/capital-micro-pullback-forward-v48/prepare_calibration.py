from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from pullback import (  # noqa: E402
    build_features,
    canonical_hash,
    discover_calibration_files,
    eligible_calibration_dates,
    generate_candidates,
    load_calibration_quotes,
    load_config,
    policy_grid,
    policy_metrics,
    resample_quotes,
    select_policy,
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    config = load_config(ROOT)
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    paths = discover_calibration_files(config)
    quotes, records = load_calibration_quotes(paths, config)
    bars = resample_quotes(quotes, config)
    eligible_dates = eligible_calibration_dates(bars, config)
    if len(eligible_dates) < int(config["sampling"]["minimum_calibration_weekdays"]):
        raise ValueError("V48 has too few eligible outcome-blind calibration weekdays")
    bars = bars.loc[bars["date_utc"].isin(eligible_dates)].copy()
    features = pd.concat(
        [
            build_features(group, config)
            for _, group in bars.groupby("date_utc", sort=True)
        ],
        ignore_index=True,
    )

    grid_rows: list[dict[str, Any]] = []
    candidate_cache: dict[str, pd.DataFrame] = {}
    for policy in policy_grid(config):
        candidates = generate_candidates(features, policy, config)
        metrics = policy_metrics(candidates, eligible_dates)
        grid_rows.append({**policy, **metrics})
        candidate_cache[policy["policy_id"]] = candidates
    grid = pd.DataFrame(grid_rows).sort_values("policy_id").reset_index(drop=True)
    selected = select_policy(grid, config)
    selected_candidates = (
        candidate_cache[str(selected["policy_id"])]
        if selected is not None
        else pd.DataFrame()
    )

    manifest = {
        "schema_version": "xauusd_v48_calibration_source_manifest",
        "source_files": records,
        "source_file_count": len(records),
        "economic_outcomes_opened": False,
    }
    manifest["manifest_sha256"] = canonical_hash(manifest, "manifest_sha256")
    manifest_path = output / config["outputs"]["calibration_source_manifest"]
    write_json(manifest_path, manifest)

    grid_path = output / config["outputs"]["calibration_grid"]
    candidates_path = output / config["outputs"]["calibration_candidates"]
    grid.to_csv(grid_path, index=False, lineterminator="\n")
    selected_candidates.to_csv(candidates_path, index=False, lineterminator="\n")
    audit = {
        "schema_version": "xauusd_v48_outcome_blind_calibration_audit",
        "decision": (
            "V48_CALIBRATION_STRUCTURE_PASS_READY_TO_LOCK"
            if selected is not None
            else "V48_CALIBRATION_STRUCTURE_FAIL_TERMINAL"
        ),
        "calibration_structure_passed": selected is not None,
        "registered_grid_policies": int(len(grid)),
        "eligible_full_weekdays": eligible_dates,
        "eligible_full_weekday_count": int(len(eligible_dates)),
        "resampled_quote_rows": int(len(bars)),
        "selected_policy": selected,
        "selected_candidate_rows": int(len(selected_candidates)),
        "calibration_source_manifest_sha256": manifest["manifest_sha256"],
        "economic_outcomes_opened": False,
        "future_candidate_prices_opened": False,
        "pnl_calculated": False,
        "model_training_authorized": False,
        "python_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
        "payment_authorized": False,
        "broker_action_authorized": False,
    }
    audit["audit_sha256"] = canonical_hash(audit, "audit_sha256")
    write_json(output / config["outputs"]["calibration_audit"], audit)
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

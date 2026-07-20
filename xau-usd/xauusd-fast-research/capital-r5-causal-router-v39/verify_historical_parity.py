from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Iterable

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from router_forward import (  # noqa: E402
    load_config,
    load_frozen,
    route_stats,
    verify_contract,
)


def _canonical_sha(frame: pd.DataFrame, columns: Iterable[str]) -> str:
    selected = frame.loc[:, list(columns)].copy()
    for column in selected.columns:
        if isinstance(selected[column].dtype, pd.DatetimeTZDtype):
            selected[column] = selected[column].map(
                lambda value: pd.Timestamp(value).isoformat()
            )
    payload = selected.to_json(orient="records", double_precision=15)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _same_number(left: float, right: float) -> bool:
    if np.isinf(left) and np.isinf(right):
        return True
    return bool(np.isclose(left, right, rtol=0.0, atol=1e-12))


def main() -> int:
    config = load_config()
    contract = verify_contract(config)
    frozen = load_frozen(config)
    source = config["source"]
    component_trades = pd.read_parquet(REPO_ROOT / source["v9_component_trades"])
    reference_routes = frozen.router.route_candidates(
        component_trades, frozen.policy, frozen.base_weights
    )
    mismatches: list[dict[str, Any]] = []
    for reference in reference_routes.itertuples(index=False):
        multiplier, reason, stats, _, prospective_rows = route_stats(
            int(reference.component_attempt_no),
            pd.Timestamp(reference.entry_time),
            component_trades,
            [],
            frozen,
        )
        checks = {
            "route_multiplier": _same_number(
                multiplier, float(reference.route_multiplier)
            ),
            "route_reason": reason == str(reference.route_reason),
            "shadow_count": int(stats.count) == int(reference.shadow_count),
            "shadow_mean_r": _same_number(
                float(stats.mean_r), float(reference.shadow_mean_r)
            ),
            "shadow_profit_factor": _same_number(
                float(stats.profit_factor), float(reference.shadow_profit_factor)
            ),
            "shadow_drawdown_r": _same_number(
                float(stats.drawdown_r), float(reference.shadow_drawdown_r)
            ),
            "prospective_rows": prospective_rows == 0,
        }
        if not all(checks.values()):
            mismatches.append(
                {
                    "candidate_id": str(reference.candidate_id),
                    "checks": checks,
                }
            )

    generated_selected = frozen.router.build_routed_trades(
        component_trades,
        frozen.policy,
        frozen.base_weights,
        int(frozen.v11_config["portfolio"]["maximum_trades_per_utc_day"]),
    )
    artifact = pd.read_parquet(REPO_ROOT / source["v11_selected_trades"])
    artifact = artifact.loc[
        artifact["attempt_no"].eq(int(config["frozen_identity"]["router_attempt"]))
    ].reset_index(drop=True)
    columns = tuple(generated_selected.columns)
    generated_sha = _canonical_sha(generated_selected, columns)
    artifact_sha = _canonical_sha(artifact, columns)
    result = {
        "schema_version": "xauusd_capital_r5_causal_router_historical_parity_v39",
        "contract_sha256": contract["contract_sha256"],
        "route_candidate_rows": int(len(reference_routes)),
        "route_stat_mismatch_rows": int(len(mismatches)),
        "selected_trade_rows": int(len(generated_selected)),
        "generated_selected_sha256": generated_sha,
        "artifact_selected_sha256": artifact_sha,
        "historical_parity_passed": bool(
            not mismatches
            and len(generated_selected)
            == int(config["frozen_identity"]["historical_selected_trade_rows"])
            and generated_sha == artifact_sha
        ),
        "aggregate_economics_opened": False,
        "broker_action_authorized": False,
    }
    if not result["historical_parity_passed"]:
        raise ValueError(f"V39 historical parity failed: {result}")
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    path = output / config["outputs"]["historical_parity"]
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

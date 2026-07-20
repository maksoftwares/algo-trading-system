from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from resolver import (  # noqa: E402
    atomic_write_json,
    load_config,
    load_module,
    validate_frozen_identity,
    verify_contract,
)


def _v28_checks(config: dict[str, object]) -> dict[str, object]:
    historical = config["historical"]
    candidates = pd.read_parquet(REPO_ROOT / historical["v28_candidates"])
    components = pd.read_parquet(REPO_ROOT / historical["v28_component_trades"])
    composites = pd.read_parquet(REPO_ROOT / historical["v28_composite_trades"])
    identity = config["frozen_identity"]["v28"]
    source_config_path = (
        REPO_ROOT
        / "xau-usd/xauusd-fast-research/regime-composite-rawtick-v1/config/regime_composite_rawtick_v1.json"
    )
    source_config = json.loads(source_config_path.read_text(encoding="utf-8"))
    module = load_module(
        "capital_core_v40_historical_v28",
        REPO_ROOT
        / "xau-usd/xauusd-fast-research/regime-composite-rawtick-v1/src/composite.py",
    )
    rebuilt = module.build_composite_trades(components, source_config)
    pd.testing.assert_frame_equal(
        rebuilt.reset_index(drop=True),
        composites.reset_index(drop=True),
        check_exact=True,
    )
    execution = source_config["execution"]
    frozen_execution = config["execution"]["v28"]
    checks = {
        "candidate_rows": int(len(candidates)),
        "component_trade_rows": int(len(components)),
        "composite_trade_rows": int(len(composites)),
        "component_attempts": sorted(
            int(value) for value in candidates["origin_attempt"].unique()
        ),
        "trade_candidate_ids_are_known": bool(
            set(components["candidate_id"]).issubset(set(candidates["candidate_id"]))
        ),
        "composite_rebuild_exact": True,
        "execution_semantics_exact": bool(
            float(execution["maximum_entry_gap_minutes"])
            == float(frozen_execution["maximum_entry_gap_minutes"])
            and float(execution["maximum_horizon_gap_hours"]) * 60.0
            == float(frozen_execution["maximum_horizon_gap_minutes"])
            and int(execution["maximum_trades_per_component_utc_day"])
            == int(frozen_execution["maximum_trades_per_component_utc_day"])
        ),
    }
    checks["pass"] = bool(
        checks["candidate_rows"] == int(identity["historical_candidate_rows"])
        and checks["component_trade_rows"]
        == int(identity["historical_component_trade_rows"])
        and checks["component_attempts"]
        == sorted(int(value) for value in identity["component_attempts"])
        and checks["trade_candidate_ids_are_known"]
        and checks["execution_semantics_exact"]
    )
    return checks


def _v29_checks(config: dict[str, object]) -> dict[str, object]:
    historical = config["historical"]
    orders = pd.read_csv(
        REPO_ROOT / historical["v29_orders"], sep="\t", index_col=False
    )
    accepted = orders.loc[orders["action"].eq("ORDER_SEND_OK")].copy()
    trades = pd.read_csv(REPO_ROOT / historical["v29_trades"])
    accepted["entry_reference"] = pd.to_numeric(accepted["entry_reference"])
    accepted["sl"] = pd.to_numeric(accepted["sl"])
    accepted["tp"] = pd.to_numeric(accepted["tp"])
    accepted["stop_points"] = pd.to_numeric(accepted["stop_points"])
    point = float(config["execution"]["v29"]["point_size"])
    risk = accepted["entry_reference"] - accepted["sl"]
    target_r = (accepted["tp"] - accepted["entry_reference"]) / risk
    stop_error = np.abs(risk - accepted["stop_points"] * point)
    trade_by_deal = trades.set_index(trades["entry_deal"].astype(str), drop=False)
    accepted_deals = accepted["deal_ticket"].astype(str)
    deal_identity = accepted_deals.isin(trade_by_deal.index).all()
    if deal_identity:
        matched = trade_by_deal.loc[accepted_deals]
        price_error = np.abs(
            matched["entry_price"].to_numpy(dtype=float)
            - accepted["entry_reference"].to_numpy(dtype=float)
        )
    else:
        price_error = np.array([np.inf])
    entries = pd.to_datetime(trades["entry_time"], format="%Y.%m.%d %H:%M:%S", utc=True)
    exits = pd.to_datetime(trades["exit_time"], format="%Y.%m.%d %H:%M:%S", utc=True)
    order = np.argsort(entries.to_numpy())
    active: list[pd.Timestamp] = []
    maximum_open = 0
    for index in order:
        entry = entries.iloc[int(index)]
        active = [value for value in active if value > entry]
        active.append(exits.iloc[int(index)])
        maximum_open = max(maximum_open, len(active))
    maximum_daily = int(entries.groupby(entries.dt.date).size().max())
    identity = config["frozen_identity"]["v29"]
    checks = {
        "accepted_order_rows": int(len(accepted)),
        "trade_rows": int(len(trades)),
        "accepted_deals_pair_to_trades": bool(deal_identity),
        "maximum_entry_price_error": float(np.max(price_error)),
        "maximum_stop_price_error": float(stop_error.max()),
        "maximum_target_r_error": float(np.max(np.abs(target_r - 2.0))),
        "all_exits_are_stop_or_target": bool(
            trades["exit_comment"].astype(str).str.match(r"^(sl|tp) ").all()
        ),
        "maximum_concurrent_positions": int(maximum_open),
        "maximum_trades_per_utc_day": int(maximum_daily),
    }
    checks["pass"] = bool(
        checks["accepted_order_rows"] == int(identity["historical_candidate_rows"])
        and checks["trade_rows"] == int(identity["historical_trade_rows"])
        and checks["accepted_deals_pair_to_trades"]
        and checks["maximum_entry_price_error"] <= 0.0
        and checks["maximum_stop_price_error"] <= 0.011
        and checks["maximum_target_r_error"] <= 0.005
        and checks["all_exits_are_stop_or_target"]
        and checks["maximum_concurrent_positions"]
        <= int(config["execution"]["v29"]["maximum_open_positions"])
        and checks["maximum_trades_per_utc_day"]
        <= int(config["execution"]["v29"]["maximum_trades_per_utc_day"])
    )
    return checks


def _v34_checks(config: dict[str, object]) -> dict[str, object]:
    historical = config["historical"]
    candidates = pd.read_parquet(REPO_ROOT / historical["v34_candidates"])
    trades = pd.read_parquet(REPO_ROOT / historical["v34_trades"])
    identity = config["frozen_identity"]["v34"]
    source_config = json.loads(
        (
            REPO_ROOT
            / "xau-usd/xauusd-fast-research/chop-three-mechanism-rawtick-v26/config/chop_three_mechanism_rawtick_v26.json"
        ).read_text(encoding="utf-8")
    )
    ordered = trades.sort_values("entry_time", kind="mergesort").reset_index(drop=True)
    entries = pd.to_datetime(ordered["entry_time"], utc=True)
    exits = pd.to_datetime(ordered["exit_time"], utc=True)
    cooldown = pd.Timedelta(
        minutes=float(source_config["execution"]["cooldown_minutes"])
    )
    no_overlap = bool(
        (
            entries.iloc[1:].reset_index(drop=True)
            >= (exits.iloc[:-1] + cooldown).reset_index(drop=True)
        ).all()
    )
    daily_max = int(entries.groupby(entries.dt.date).size().max())
    frozen_execution = config["execution"]["v34"]
    checks = {
        "candidate_rows": int(len(candidates)),
        "trade_rows": int(len(trades)),
        "component_attempts": sorted(
            int(value) for value in candidates["origin_attempt"].unique()
        ),
        "trade_candidate_ids_are_known": bool(
            set(trades["candidate_id"]).issubset(set(candidates["candidate_id"]))
        ),
        "shared_position_and_cooldown_hold": no_overlap,
        "maximum_trades_per_utc_day": daily_max,
        "execution_semantics_exact": bool(
            float(source_config["execution"]["maximum_entry_gap_minutes"])
            == float(frozen_execution["maximum_entry_gap_minutes"])
            and float(source_config["execution"]["maximum_horizon_gap_minutes"])
            == float(frozen_execution["maximum_horizon_gap_minutes"])
            and float(source_config["execution"]["cooldown_minutes"])
            == float(frozen_execution["cooldown_minutes"])
            and int(source_config["execution"]["maximum_trades_per_variant_utc_day"])
            == int(frozen_execution["maximum_trades_per_utc_day"])
        ),
    }
    checks["pass"] = bool(
        checks["candidate_rows"] == int(identity["historical_candidate_rows"])
        and checks["trade_rows"] == int(identity["historical_trade_rows"])
        and checks["component_attempts"]
        == sorted(int(value) for value in identity["component_attempts"])
        and checks["trade_candidate_ids_are_known"]
        and checks["shared_position_and_cooldown_hold"]
        and checks["maximum_trades_per_utc_day"]
        <= int(frozen_execution["maximum_trades_per_utc_day"])
        and checks["execution_semantics_exact"]
    )
    return checks


def main() -> int:
    config = load_config()
    contract = verify_contract(config)
    validate_frozen_identity(config)
    result = {
        "schema_version": "xauusd_capital_core_causal_outcome_semantic_parity_v40",
        "contract_sha256": contract["contract_sha256"],
        "v28": _v28_checks(config),
        "v29": _v29_checks(config),
        "v34": _v34_checks(config),
        "aggregate_economics_opened": False,
        "broker_action_authorized": False,
    }
    result["semantic_parity_passed"] = bool(
        result["v28"]["pass"] and result["v29"]["pass"] and result["v34"]["pass"]
    )
    if not result["semantic_parity_passed"]:
        raise ValueError(f"V40 historical semantic parity failed: {result}")
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    atomic_write_json(output / config["outputs"]["historical_semantic_parity"], result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

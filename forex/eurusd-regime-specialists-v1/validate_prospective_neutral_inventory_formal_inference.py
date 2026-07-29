from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import validate_prospective_neutral_inventory_clock_portfolio as portfolio
import validate_prospective_neutral_inventory_portfolio_risk as risk
from capture_prospective_neutral_inventory_unwind_0005 import _serialize, _timestamp
from eurusd_regime_specialists.research import PACKAGE_ROOT, sha256_file

CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_prospective_neutral_inventory_formal_inference_v1.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_INVENTORY_FORMAL_INFERENCE_"
    "PREREG_2026_07_29.sha256.json"
)
PRIMARY_ROOT = Path(
    "D:/AlgoTradingData/prospective/eurusd-neutral-inventory-unwind-0005-v1"
)
TRANSFER_ROOT = Path(
    "D:/AlgoTradingData/prospective/eurusd-neutral-inventory-clock-transfer-v1"
)


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_preregistration() -> dict[str, Any]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    required = {
        "locked_before_first_portfolio_observation": True,
        "locked_with_zero_decisions": True,
        "locked_with_zero_trade_paths": True,
        "locked_with_zero_oracle_records": True,
        "historical_backtest_allowed": False,
        "historical_eurusd_pnl_allowed": False,
        "economic_output_before_formal_readiness_allowed": False,
        "repeated_formal_evaluation_allowed": False,
        "network_request_allowed": False,
        "broker_action_allowed": False,
    }
    if any(lock.get(key) is not value for key, value in required.items()):
        raise RuntimeError("Formal-inference preregistration is incomplete")
    for relative, expected in lock["files"].items():
        if sha256_file(PACKAGE_ROOT / relative) != expected:
            raise RuntimeError(f"Formal-inference implementation drift: {relative}")
    risk.verify_preregistration()
    return lock


def _closed_rows(evaluated_at_utc: Any) -> tuple[pd.DataFrame, pd.DataFrame]:
    routed = portfolio.collect_portfolio_rows(evaluated_at_utc=evaluated_at_utc)
    closed = routed[routed["status"].eq("CLOSED")].copy()
    return routed, closed


def _sample_counts(closed: pd.DataFrame) -> dict[str, Any]:
    by_clock = {
        clock: int(closed["clock"].eq(clock).sum()) for clock in portfolio.CLOCKS
    }
    by_side = {
        side: int(closed["side"].eq(side).sum()) for side in ("LONG", "SHORT")
    }
    return {
        "closed_trades": int(len(closed)),
        "by_clock": by_clock,
        "by_side": by_side,
    }


def formal_readiness(
    evaluated_at_utc: Any,
    counts: Mapping[str, Any],
    *,
    pending_paths: int,
    config: Mapping[str, Any] | None = None,
) -> dict[str, bool]:
    cfg = load_config() if config is None else config
    sample = cfg["sample_contract"]
    time_ready = _timestamp(evaluated_at_utc) >= _timestamp(
        cfg["earliest_formal_evaluation_utc"]
    )
    return {
        "exact_full_year_time_boundary": time_ready,
        "minimum_closed_trades": int(counts["closed_trades"])
        >= int(sample["minimum_closed_trades"]),
        "minimum_0005_trades": int(counts["by_clock"]["0005"])
        >= int(sample["minimum_0005_trades"]),
        "minimum_0605_trades": int(counts["by_clock"]["0605"])
        >= int(sample["minimum_0605_trades"]),
        "minimum_1205_trades": int(counts["by_clock"]["1205"])
        >= int(sample["minimum_1205_trades"]),
        "minimum_each_side_trades": all(
            int(counts["by_side"][side]) >= int(sample["minimum_each_side_trades"])
            for side in ("LONG", "SHORT")
        ),
        "all_signal_paths_closed": int(pending_paths) == 0,
    }


def build_blinded_status(
    *,
    evaluated_at_utc: Any | None = None,
    verify_lock: bool = True,
) -> dict[str, Any]:
    if verify_lock:
        verify_preregistration()
    cfg = load_config()
    evaluated = (
        pd.Timestamp.now(tz="UTC").as_unit("ns")
        if evaluated_at_utc is None
        else _timestamp(evaluated_at_utc)
    )
    routed, closed = _closed_rows(evaluated)
    counts = _sample_counts(closed)
    pending = int(routed["status"].eq("PENDING_PATH").sum())
    readiness = formal_readiness(
        evaluated,
        counts,
        pending_paths=pending,
        config=cfg,
    )
    ready = all(readiness.values())
    if not readiness["exact_full_year_time_boundary"]:
        status = "WAITING_FOR_EXACT_FULL_YEAR_BOUNDARY"
    elif not ready:
        status = "WAITING_FOR_FROZEN_SAMPLE_COUNTS"
    else:
        status = "FORMAL_ORACLE_AND_COMPONENT_READINESS_CHECK_REQUIRED"
    return {
        "schema_version": cfg["schema_version"],
        "status": status,
        "prospective_start_utc": cfg["prospective_start_utc"],
        "earliest_formal_evaluation_utc": cfg["earliest_formal_evaluation_utc"],
        "evaluated_at_utc": evaluated.isoformat(),
        "eligible_decisions_recorded": int(len(routed)),
        "signals": int(routed["decision_status"].eq("SIGNAL").sum()),
        "cash_decisions": int(routed["decision_status"].eq("CASH").sum()),
        "pending_signal_paths": pending,
        **counts,
        "formal_readiness": readiness,
        "formal_sample_count_ready": ready,
        "economic_outcomes_exposed": False,
        "formal_result_exists": _existing_formal_result(
            Path(cfg["output_root"])
        )
        is not None,
        "research_review_allowed": False,
        "controlled_demo_ready": False,
        "historical_eurusd_pnl_loaded": False,
        "network_request_made": False,
        "broker_action_allowed": False,
    }


def _day_statistics(frame: pd.DataFrame, column: str) -> dict[str, np.ndarray]:
    values = frame[["entry_date_utc", column]].copy()
    values["value"] = values[column].astype(float)
    values["win"] = values["value"].clip(lower=0.0)
    values["loss"] = (-values["value"].clip(upper=0.0)).astype(float)
    values["wins"] = values["value"].gt(0.0).astype(int)
    values["losses"] = values["value"].lt(0.0).astype(int)
    values["trades"] = 1
    grouped = values.groupby("entry_date_utc", sort=True)[
        ["win", "loss", "value", "wins", "losses", "trades"]
    ].sum()
    return {
        name: grouped[name].to_numpy(dtype=float)
        for name in ("win", "loss", "value", "wins", "losses", "trades")
    }


def _bootstrap_metrics(
    statistics: Mapping[str, np.ndarray],
    indices: np.ndarray,
) -> dict[str, np.ndarray]:
    totals = {
        name: values[indices].sum(axis=1) for name, values in statistics.items()
    }
    profit_factor = np.divide(
        totals["win"],
        totals["loss"],
        out=np.full_like(totals["win"], np.inf),
        where=totals["loss"] > 0.0,
    )
    expectancy = np.divide(
        totals["value"],
        totals["trades"],
        out=np.zeros_like(totals["value"]),
        where=totals["trades"] > 0.0,
    )
    win_rate = np.divide(
        totals["wins"],
        totals["trades"],
        out=np.zeros_like(totals["wins"]),
        where=totals["trades"] > 0.0,
    )
    average_win = np.divide(
        totals["win"],
        totals["wins"],
        out=np.zeros_like(totals["win"]),
        where=totals["wins"] > 0.0,
    )
    average_loss = np.divide(
        totals["loss"],
        totals["losses"],
        out=np.zeros_like(totals["loss"]),
        where=totals["losses"] > 0.0,
    )
    payoff = np.divide(
        average_win,
        average_loss,
        out=np.full_like(average_win, np.inf),
        where=average_loss > 0.0,
    )
    return {
        "profit_factor": profit_factor,
        "expectancy_r": expectancy,
        "win_rate": win_rate,
        "payoff_ratio": payoff,
    }


def day_block_inference(
    closed: pd.DataFrame,
    *,
    simulations: int,
    block_length_days: int,
    seed: int,
    lower_quantile: float,
) -> dict[str, Any]:
    if closed.empty:
        raise ValueError("Formal inference requires closed trades")
    frame = closed.copy()
    frame["entry_date_utc"] = pd.to_datetime(
        frame["entry_time_utc"], utc=True
    ).dt.strftime("%Y-%m-%d")
    days = sorted(frame["entry_date_utc"].unique())
    day_count = len(days)
    blocks = int(math.ceil(day_count / block_length_days))
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, day_count, size=(simulations, blocks))
    offsets = np.arange(block_length_days)
    indices = (starts[:, :, None] + offsets) % day_count
    indices = indices.reshape(simulations, -1)[:, :day_count]
    results: dict[str, Any] = {}
    for label, column in (
        ("base", "r"),
        ("extra_half_pip", "extra_half_pip_stress_r"),
    ):
        boot = _bootstrap_metrics(_day_statistics(frame, column), indices)
        point = portfolio.primary.trade_metrics(frame[column])
        results[label] = {
            "point": point,
            "one_sided_lower_bounds": {
                name: float(np.quantile(values, lower_quantile))
                for name, values in boot.items()
            },
        }
    return {
        "method": "CIRCULAR_MOVING_BLOCK_BOOTSTRAP",
        "resampling_unit": "UTC_ACTIVE_TRADING_DAY",
        "active_days": day_count,
        "block_length_active_days": int(block_length_days),
        "simulations": int(simulations),
        "random_seed": int(seed),
        "lower_confidence_quantile": float(lower_quantile),
        "results": results,
    }


def inference_gates(
    inference: Mapping[str, Any],
    config: Mapping[str, Any],
) -> dict[str, bool]:
    contract = config["inference_contract"]
    base = inference["results"]["base"]["one_sided_lower_bounds"]
    stress = inference["results"]["extra_half_pip"]["one_sided_lower_bounds"]
    return {
        "base_profit_factor_lower_bound": float(base["profit_factor"])
        > float(contract["base_profit_factor_lower_bound_exclusive"]),
        "stressed_profit_factor_lower_bound": float(stress["profit_factor"])
        > float(contract["stressed_profit_factor_lower_bound_exclusive"]),
        "base_expectancy_lower_bound": float(base["expectancy_r"])
        > float(contract["base_expectancy_r_lower_bound_exclusive"]),
        "stressed_expectancy_lower_bound": float(stress["expectancy_r"])
        > float(contract["stressed_expectancy_r_lower_bound_exclusive"]),
    }


def evidence_chain(roots: Mapping[str, Path]) -> dict[str, Any]:
    digest = hashlib.sha256()
    files = 0
    for label, root in sorted(roots.items()):
        if not root.exists():
            continue
        for path in sorted(
            (item for item in root.rglob("*") if item.is_file()),
            key=lambda item: item.relative_to(root).as_posix(),
        ):
            relative = path.relative_to(root).as_posix()
            digest.update(label.encode("utf-8"))
            digest.update(relative.encode("utf-8"))
            digest.update(bytes.fromhex(sha256_file(path)))
            files += 1
    return {"files": files, "sha256": digest.hexdigest()}


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(_serialize(value), indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _existing_formal_result(output_root: Path) -> dict[str, Any] | None:
    paths = sorted((output_root / "manifests").glob("FORMAL_INFERENCE_*.json"))
    if not paths:
        return None
    if len(paths) != 1:
        raise RuntimeError("Multiple formal inference results exist")
    path = paths[0]
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if path.name != f"FORMAL_INFERENCE_{digest[:16]}.json":
        raise RuntimeError("Formal inference filename/hash drift")
    return {
        **json.loads(payload),
        "manifest_relative_path": path.relative_to(output_root).as_posix(),
        "manifest_sha256": digest,
    }


def write_formal_result(
    output_root: Path,
    result: Mapping[str, Any],
) -> dict[str, Any]:
    existing = _existing_formal_result(output_root)
    if existing is not None:
        return existing
    payload = _json_bytes(result)
    digest = hashlib.sha256(payload).hexdigest()
    path = output_root / "manifests" / f"FORMAL_INFERENCE_{digest[:16]}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(payload)
    return {
        **json.loads(payload),
        "manifest_relative_path": path.relative_to(output_root).as_posix(),
        "manifest_sha256": digest,
    }


def evaluate_formally(
    *,
    evaluated_at_utc: Any | None = None,
) -> dict[str, Any]:
    verify_preregistration()
    cfg = load_config()
    output_root = Path(cfg["output_root"])
    existing = _existing_formal_result(output_root)
    if existing is not None:
        return existing
    evaluated = (
        pd.Timestamp.now(tz="UTC").as_unit("ns")
        if evaluated_at_utc is None
        else _timestamp(evaluated_at_utc)
    )
    blinded = build_blinded_status(
        evaluated_at_utc=evaluated,
        verify_lock=False,
    )
    if not blinded["formal_sample_count_ready"]:
        return blinded
    portfolio_status = portfolio.build_validation_status(
        evaluated_at_utc=evaluated
    )
    component_ready = all(portfolio_status["component_readiness"].values())
    oracle_ready = bool(
        portfolio_status["oracle_gate_results"]["all_closed_trade_oracle_dates"]
    )
    if not component_ready or not oracle_ready:
        return {
            **blinded,
            "status": "WAITING_FOR_COMPLETE_ORACLE_AND_COMPONENT_EVIDENCE",
            "component_readiness": portfolio_status["component_readiness"],
            "all_closed_trade_oracle_dates": oracle_ready,
        }
    routed, closed = _closed_rows(evaluated)
    inference_cfg = cfg["inference_contract"]
    inference = day_block_inference(
        closed,
        simulations=int(inference_cfg["simulations"]),
        block_length_days=int(inference_cfg["block_length_active_days"]),
        seed=int(inference_cfg["random_seed"]),
        lower_quantile=float(inference_cfg["lower_confidence_quantile"]),
    )
    statistical_gates = inference_gates(inference, cfg)
    risk_status = risk.build_status(evaluated_at_utc=evaluated)
    all_passed = bool(
        portfolio_status["all_gates_passed"]
        and risk_status["all_risk_gates_passed"]
        and all(statistical_gates.values())
    )
    result = {
        "schema_version": cfg["schema_version"],
        "campaign_id": cfg["campaign_id"],
        "status": (
            "INDEPENDENT_RESEARCH_REVIEW_REQUIRED"
            if all_passed
            else "REJECTED_WITHOUT_RETUNING"
        ),
        "formal_evaluated_at_utc": evaluated,
        "earliest_formal_evaluation_utc": cfg[
            "earliest_formal_evaluation_utc"
        ],
        "promotion_unit": "FIXED_THREE_CLOCK_0005_0605_1205_PORTFOLIO",
        "counts": _sample_counts(closed),
        "portfolio_all_gates_passed": bool(
            portfolio_status["all_gates_passed"]
        ),
        "portfolio_risk_all_gates_passed": bool(
            risk_status["all_risk_gates_passed"]
        ),
        "inference": inference,
        "inference_gate_results": statistical_gates,
        "all_formal_gates_passed": all_passed,
        "evidence_chain": evidence_chain(
            {
                "primary_ledger": PRIMARY_ROOT / "ledger",
                "primary_oracle": PRIMARY_ROOT / "oracle",
                "primary_path": PRIMARY_ROOT / "path",
                "transfer_ledger": TRANSFER_ROOT / "ledger",
                "transfer_oracle": TRANSFER_ROOT / "oracle",
                "transfer_path": TRANSFER_ROOT / "path",
            }
        ),
        "first_complete_formal_result_is_authoritative": True,
        "research_review_allowed": all_passed,
        "controlled_demo_ready": False,
        "exact_mt5_parity_verified": False,
        "historical_eurusd_pnl_loaded": False,
        "network_request_made": False,
        "broker_action_allowed": False,
    }
    return write_formal_result(output_root, result)


def status() -> dict[str, Any]:
    verify_preregistration()
    existing = _existing_formal_result(Path(load_config()["output_root"]))
    return existing if existing is not None else build_blinded_status(
        verify_lock=False
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("status", "evaluate"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = (
        status()
        if args.command == "status"
        else evaluate_formally()
    )
    print(json.dumps(_serialize(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

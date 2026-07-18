from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any, Mapping

import numpy as np
import pandas as pd

from proxy_data import build_pressure_frame, load_proxy_cache


RESEARCH_ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


DATA = load_module(
    "macro_transition_proxy_data",
    RESEARCH_ROOT / "independent-specialists-v1" / "src" / "data.py",
)
REGIMES = load_module(
    "macro_transition_proxy_regimes",
    RESEARCH_ROOT / "independent-specialists-v1" / "src" / "research.py",
)
ADAPTIVE = load_module(
    "macro_transition_proxy_adaptive",
    RESEARCH_ROOT / "adaptive-h4-specialists-v1" / "src" / "adaptive.py",
)
FEATURES = load_module(
    "macro_transition_proxy_features",
    RESEARCH_ROOT / "m15-regime-target-campaign-v1" / "src" / "campaign.py",
)
CLOCK = load_module(
    "macro_transition_proxy_clock",
    RESEARCH_ROOT / "m15-regime-target-campaign-v2" / "src" / "correction.py",
)
ROUTER = load_module(
    "macro_transition_proxy_router",
    RESEARCH_ROOT / "walkforward-state-action-router-v1" / "src" / "router.py",
)
V1 = load_module(
    "macro_transition_proxy_v1_campaign",
    RESEARCH_ROOT / "macro-regime-routing-v1" / "src" / "campaign.py",
)


@dataclass(frozen=True)
class Foundation:
    execution_frame: pd.DataFrame
    arrays: dict[str, np.ndarray]
    decisions: dict[str, pd.DataFrame]
    evidence: dict[str, Any]


def _gold_with_execution_index(config: Mapping[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    bundle = DATA.load_bundle(dict(config))
    frame = FEATURES.prepare_features(
        bundle.bars["M15"],
        bundle.bars["H4"],
        config,
        ADAPTIVE,
        REGIMES,
    )
    frame = frame.sort_values("timestamp_utc", kind="mergesort").reset_index(drop=True)
    frame["execution_index"] = np.arange(len(frame), dtype=np.int64)
    elapsed = frame["timestamp_utc"] - frame["timestamp_utc"].shift(4)
    frame["gold_return_H1_atr"] = (
        (frame["mid_close"] - frame["mid_close"].shift(4))
        / frame["atr14"].replace(0.0, np.nan)
    ).where(elapsed.eq(pd.Timedelta(hours=1)))
    frame["hour_utc"] = frame["timestamp_utc"].dt.hour
    return frame, bundle.evidence


def load_foundation(config: Mapping[str, Any]) -> Foundation:
    gold, gold_evidence = _gold_with_execution_index(config)
    proxy_cache, proxy_evidence = load_proxy_cache(config)
    decisions: dict[str, pd.DataFrame] = {}
    decision_evidence: list[dict[str, Any]] = []
    for proxy_symbol, (raw_start, raw_end) in config["windows"].items():
        pressure = build_pressure_frame(
            proxy_cache, str(proxy_symbol), config["macro_translation"]
        )
        frame = gold.merge(pressure, on="timestamp_utc", how="inner", validate="one_to_one")
        start, end = pd.Timestamp(raw_start), pd.Timestamp(raw_end)
        frame = frame.loc[
            frame["timestamp_utc"].ge(start) & frame["timestamp_utc"].lt(end)
        ].copy()
        frame = frame.sort_values("timestamp_utc", kind="mergesort").reset_index(drop=True)
        if frame.empty:
            raise ValueError(f"No exact gold/proxy decisions for {proxy_symbol}")
        decisions[str(proxy_symbol)] = frame
        ready = frame[["dxy_pressure_H1_D2", "bond_pressure_H1_D2"]].notna().all(axis=1)
        decision_evidence.append(
            {
                "proxy_symbol": str(proxy_symbol),
                "rows": int(len(frame)),
                "pressure_ready_rows": int(ready.sum()),
                "first_timestamp_utc": frame["timestamp_utc"].min().isoformat(),
                "last_timestamp_utc": frame["timestamp_utc"].max().isoformat(),
            }
        )
    arrays = CLOCK.execution_arrays(gold)
    for proxy_symbol, frame in decisions.items():
        mapped = frame["execution_index"].to_numpy(dtype=np.int64)
        mapped_times = gold["timestamp_utc"].iloc[mapped].reset_index(drop=True)
        if not mapped_times.equals(frame["timestamp_utc"].reset_index(drop=True)):
            raise ValueError(f"Decision-to-execution timestamp mapping failed for {proxy_symbol}")
    return Foundation(
        execution_frame=gold,
        arrays=arrays,
        decisions=decisions,
        evidence={
            "gold": gold_evidence,
            "proxy": proxy_evidence,
            "decision_inventory": decision_evidence,
            "execution_rows": int(len(gold)),
        },
    )


def fixed_manifest_row(config: Mapping[str, Any]) -> SimpleNamespace:
    candidate = config["candidate"]
    parameters = dict(candidate["parameters"])
    canonical = json.dumps(parameters, sort_keys=True, separators=(",", ":"))
    return SimpleNamespace(
        parameters_json=canonical,
        mechanic=str(candidate["mechanic"]),
        geometry_id=str(candidate["geometry_id"]),
        regime_owner=str(candidate["regime_owner"]),
    )


def simulate_proxy(
    frame: pd.DataFrame,
    arrays: Mapping[str, np.ndarray],
    config: Mapping[str, Any],
    outcome_cache: dict[tuple[int, int, str], dict[str, Any] | None],
) -> tuple[pd.DataFrame, int]:
    row = fixed_manifest_row(config)
    parameters = json.loads(row.parameters_json)
    mask, _ = V1.signal_mask_direction(frame, row.mechanic, parameters)
    trades = V1.simulate_variant(
        frame,
        arrays,
        row,
        config,
        outcome_cache,
        ROUTER.simulate_fixed_trade,
    )
    return trades, int(mask.sum())


def profit_factor(values: pd.Series) -> float:
    gains = float(values.loc[values > 0.0].sum())
    losses = float(-values.loc[values < 0.0].sum())
    if losses == 0.0:
        return float("inf") if gains > 0.0 else 0.0
    return gains / losses


def closed_drawdown(values: pd.Series) -> float:
    equity = np.concatenate(([0.0], values.fillna(0.0).to_numpy(dtype=float).cumsum()))
    peaks = np.maximum.accumulate(equity)
    return float(np.max(peaks - equity)) if len(equity) else 0.0


def summarize(trades: pd.DataFrame, remove_winners: int) -> dict[str, Any]:
    values = (
        trades["stress_net_r"].astype(float)
        if not trades.empty
        else pd.Series(dtype=float)
    )
    removed = values.drop(values.nlargest(min(remove_winners, len(values))).index)
    return {
        "trades": int(len(values)),
        "stress_net_r": float(values.sum()),
        "stress_profit_factor": profit_factor(values),
        "average_stress_r": float(values.mean()) if len(values) else 0.0,
        "closed_drawdown_r": closed_drawdown(values),
        "top_winners_removed": int(remove_winners),
        "top_winners_removed_stress_net_r": float(removed.sum()),
    }


def proxy_gate_checks(summary: Mapping[str, Any], gates: Mapping[str, Any]) -> dict[str, bool]:
    return {
        "minimum_trades": int(summary["trades"]) >= int(gates["proxy_minimum_trades"]),
        "minimum_net_r": float(summary["stress_net_r"]) > float(gates["proxy_minimum_net_r"]),
        "minimum_profit_factor": float(summary["stress_profit_factor"])
        >= float(gates["proxy_minimum_profit_factor"]),
        "minimum_average_r": float(summary["average_stress_r"])
        >= float(gates["proxy_minimum_average_r"]),
        "minimum_removed_net_r": float(summary["top_winners_removed_stress_net_r"])
        >= float(gates["proxy_minimum_removed_net_r"]),
        "maximum_drawdown_r": float(summary["closed_drawdown_r"])
        <= float(gates["proxy_maximum_drawdown_r"]),
    }


def pooled_gate_checks(summary: Mapping[str, Any], gates: Mapping[str, Any]) -> dict[str, bool]:
    return {
        "minimum_trades": int(summary["trades"]) >= int(gates["pooled_minimum_trades"]),
        "minimum_profit_factor": float(summary["stress_profit_factor"])
        >= float(gates["pooled_minimum_profit_factor"]),
        "minimum_average_r": float(summary["average_stress_r"])
        >= float(gates["pooled_minimum_average_r"]),
        "minimum_removed_net_r": float(summary["top_winners_removed_stress_net_r"])
        > float(gates["pooled_minimum_removed_net_r"]),
        "maximum_drawdown_r": float(summary["closed_drawdown_r"])
        <= float(gates["pooled_maximum_drawdown_r"]),
    }


def unique_pooled_trades(trades: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    if trades.empty:
        return trades.copy(), 0
    ordered = trades.sort_values(
        ["entry_time", "signal_time", "direction_sign", "proxy_symbol"], kind="mergesort"
    )
    duplicate = ordered.duplicated(["signal_time", "direction_sign"], keep="first")
    return ordered.loc[~duplicate].reset_index(drop=True), int(duplicate.sum())

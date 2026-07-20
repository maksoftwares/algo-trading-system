from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Mapping

import numpy as np
import pandas as pd


REQUIRED_LEDGER_COLUMNS = {
    "trade_id",
    "specialist_id",
    "regime",
    "source_strategy",
    "entry_time_utc",
    "exit_time_utc",
    "pnl_usd_0p01_equiv",
}


@dataclass(frozen=True)
class AuditArtifacts:
    result: dict[str, Any]
    windows: pd.DataFrame
    cap_decisions: pd.DataFrame
    episode_trades: pd.DataFrame


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def verify_sources(
    repo_root: Path, records: Mapping[str, Mapping[str, str]], external: bool
) -> dict[str, dict[str, Any]]:
    verified: dict[str, dict[str, Any]] = {}
    for name, record in records.items():
        path = Path(record["path"]) if external else repo_root / record["path"]
        if not path.is_file():
            raise FileNotFoundError(path)
        actual = sha256_file(path)
        if actual != record["sha256"]:
            raise ValueError(f"Source SHA-256 mismatch for {name}: {actual}")
        verified[name] = {
            "path": str(path.resolve()),
            "bytes": int(path.stat().st_size),
            "sha256": actual,
        }
    return verified


def load_ledger(path: Path) -> pd.DataFrame:
    ledger = pd.read_parquet(path)
    missing = sorted(REQUIRED_LEDGER_COLUMNS.difference(ledger.columns))
    if missing:
        raise ValueError(f"Normalized ledger is missing columns: {missing}")
    if ledger["trade_id"].duplicated().any():
        raise ValueError("Normalized ledger contains duplicate trade IDs")
    result = ledger.copy()
    for column in ("entry_time_utc", "exit_time_utc"):
        result[column] = pd.to_datetime(result[column], utc=True, errors="raise")
    result["pnl_usd_0p01_equiv"] = pd.to_numeric(
        result["pnl_usd_0p01_equiv"], errors="raise"
    )
    if bool((result["exit_time_utc"] < result["entry_time_utc"]).any()):
        raise ValueError("Normalized ledger contains an exit before entry")
    return result.sort_values(
        ["exit_time_utc", "entry_time_utc", "trade_id"], kind="mergesort"
    ).reset_index(drop=True)


def profit_factor(values: pd.Series) -> float | None:
    gains = float(values.loc[values > 0.0].sum())
    losses = float(-values.loc[values < 0.0].sum())
    if losses == 0.0:
        return None if gains == 0.0 else float("inf")
    return gains / losses


def drawdown_episode(
    trades: pd.DataFrame,
    pnl_column: str,
    time_column: str,
    baseline_time: pd.Timestamp,
) -> dict[str, Any]:
    ordered = trades.sort_values(
        [time_column, "trade_id"], kind="mergesort"
    ).reset_index(drop=True)
    pnl = ordered[pnl_column].fillna(0.0).to_numpy(dtype=float)
    equity = np.concatenate(([0.0], np.cumsum(pnl)))
    peaks = np.maximum.accumulate(equity)
    drawdown = peaks - equity
    trough_position = int(np.argmax(drawdown))
    peak_position = int(np.argmax(equity[: trough_position + 1]))
    peak_time = (
        baseline_time
        if peak_position == 0
        else pd.Timestamp(ordered.iloc[peak_position - 1][time_column])
    )
    trough_time = (
        baseline_time
        if trough_position == 0
        else pd.Timestamp(ordered.iloc[trough_position - 1][time_column])
    )
    return {
        "maximum_drawdown_dollars": float(drawdown[trough_position]),
        "peak_equity_dollars": float(equity[peak_position]),
        "trough_equity_dollars": float(equity[trough_position]),
        "peak_time_utc": peak_time.isoformat(),
        "trough_time_utc": trough_time.isoformat(),
    }


def apply_frozen_r1_cap(
    ledger: pd.DataFrame, control: Mapping[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    target = ledger.loc[
        ledger["specialist_id"].eq(control["specialist_id"])
        & ledger["source_strategy"].eq(control["source_strategy"])
    ].sort_values(["entry_time_utc", "trade_id"], kind="mergesort")
    maximum_concurrent = int(control["maximum_concurrent_positions"])
    maximum_daily = int(control["maximum_entries_per_utc_day"])
    active: list[pd.Timestamp] = []
    daily: dict[Any, int] = {}
    accepted_ids: set[str] = set()
    decisions: list[dict[str, Any]] = []
    for row in target.itertuples(index=False):
        entry = pd.Timestamp(row.entry_time_utc)
        active = [exit_time for exit_time in active if exit_time > entry]
        day = entry.date()
        if len(active) >= maximum_concurrent:
            reason = "MAXIMUM_CONCURRENT_POSITIONS"
            accepted = False
        elif daily.get(day, 0) >= maximum_daily:
            reason = "MAXIMUM_ENTRIES_PER_UTC_DAY"
            accepted = False
        else:
            reason = "ACCEPTED"
            accepted = True
            accepted_ids.add(str(row.trade_id))
            active.append(pd.Timestamp(row.exit_time_utc))
            daily[day] = daily.get(day, 0) + 1
        decisions.append(
            {
                "trade_id": str(row.trade_id),
                "entry_time_utc": entry,
                "exit_time_utc": pd.Timestamp(row.exit_time_utc),
                "accepted": accepted,
                "decision_reason": reason,
                "active_before_decision": len(active) - int(accepted),
                "entries_on_day_before_decision": daily.get(day, 0) - int(accepted),
            }
        )
    is_target = ledger["specialist_id"].eq(control["specialist_id"]) & ledger[
        "source_strategy"
    ].eq(control["source_strategy"])
    kept = ledger.loc[
        ~is_target | ledger["trade_id"].astype(str).isin(accepted_ids)
    ].copy()
    kept = kept.sort_values(
        ["exit_time_utc", "entry_time_utc", "trade_id"], kind="mergesort"
    ).reset_index(drop=True)
    return kept, pd.DataFrame(decisions)


def window_metrics(
    ledger: pd.DataFrame,
    start: pd.Timestamp,
    cutoff: pd.Timestamp,
    policy: str,
) -> dict[str, Any]:
    frame = ledger.loc[
        ledger["exit_time_utc"].ge(start) & ledger["exit_time_utc"].lt(cutoff)
    ].copy()
    values = frame["pnl_usd_0p01_equiv"]
    episode = drawdown_episode(frame, "pnl_usd_0p01_equiv", "exit_time_utc", start)
    weekdays = int(np.busday_count(start.date(), cutoff.date()))
    pf = profit_factor(values)
    return {
        "policy": policy,
        "window_start_utc": start.isoformat(),
        "cutoff_exclusive_utc": cutoff.isoformat(),
        "trades": int(len(frame)),
        "calendar_weekdays": weekdays,
        "trades_per_weekday": float(len(frame) / weekdays) if weekdays else 0.0,
        "net_pnl_dollars": float(values.sum()),
        "profit_factor": pf,
        "closed_drawdown_dollars": episode["maximum_drawdown_dollars"],
    }


def _load_portability_module(path: Path) -> Any:
    name = "xau_historical_core_drawdown_v43_portability"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load R1 portability module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _drawdown_from_extremes(
    high_equity: np.ndarray, low_equity: np.ndarray
) -> tuple[float, int, int]:
    peak = -np.inf
    peak_index = 0
    maximum = 0.0
    maximum_peak = 0
    trough = 0
    for index in range(len(high_equity)):
        if high_equity[index] > peak:
            peak = float(high_equity[index])
            peak_index = index
        value = peak - float(low_equity[index])
        if value > maximum:
            maximum = value
            maximum_peak = peak_index
            trough = index
    return maximum, maximum_peak, trough


def mark_portability_policy(
    trades: pd.DataFrame,
    m5: pd.DataFrame,
    execution: Mapping[str, Any],
    stress: bool,
) -> dict[str, Any]:
    count = len(m5)
    low_equity = np.zeros(count, dtype=float)
    high_equity = np.zeros(count, dtype=float)
    starts = m5["bar_start_utc"].to_numpy(dtype="datetime64[ns]")
    ends = m5["bar_end_utc"].to_numpy(dtype="datetime64[ns]")
    bid_low = m5["bid_low"].to_numpy(dtype=float)
    bid_high = m5["bid_high"].to_numpy(dtype=float)
    for trade in trades.itertuples(index=False):
        entry = np.datetime64(pd.Timestamp(trade.entry_time).tz_convert(None))
        exit_time = np.datetime64(pd.Timestamp(trade.exit_time).tz_convert(None))
        first = int(np.searchsorted(starts, entry, side="left"))
        last = min(count - 1, int(np.searchsorted(ends, exit_time, side="left")))
        entry_price = float(trade.entry_price)
        risk = float(trade.initial_risk_price)
        low_mark = np.maximum(bid_low[first : last + 1], float(trade.stop))
        high_mark = np.minimum(bid_high[first : last + 1], float(trade.target))
        low_pnl = low_mark - entry_price
        high_pnl = high_mark - entry_price
        if stress:
            elapsed_days = np.maximum(
                0.0,
                (
                    m5["bar_start_utc"].iloc[first : last + 1]
                    - pd.Timestamp(trade.entry_time)
                )
                .dt.total_seconds()
                .to_numpy(dtype=float)
                / 86_400.0,
            )
            costs = (
                float(execution["ticket_cost_usd"])
                + elapsed_days * float(execution["holding_cost_per_24h_usd"])
                + float(execution["stress_slippage_r"]) * risk
            )
            low_pnl = low_pnl - costs
            high_pnl = high_pnl - costs
        if str(trade.exit_reason) == "GAP_THROUGH_STOP":
            realized = (
                float(trade.stress_net_r) * risk
                if stress
                else float(trade.exit_price) - entry_price
            )
            low_pnl[-1] = realized
            high_pnl[-1] = realized
        low_equity[first : last + 1] += low_pnl
        high_equity[first : last + 1] += high_pnl
        if last + 1 < count:
            realized = (
                float(trade.stress_net_r) * risk
                if stress
                else float(trade.exit_price) - entry_price
            )
            low_equity[last + 1 :] += realized
            high_equity[last + 1 :] += realized
    maximum, peak, trough = _drawdown_from_extremes(high_equity, low_equity)
    return {
        "maximum_drawdown_dollars": float(maximum),
        "peak_bar_start_utc": pd.Timestamp(m5.iloc[peak]["bar_start_utc"]).isoformat(),
        "trough_bar_start_utc": pd.Timestamp(
            m5.iloc[trough]["bar_start_utc"]
        ).isoformat(),
        "peak_equity_dollars": float(high_equity[peak]),
        "trough_equity_dollars": float(low_equity[trough]),
        "bar_count": int(count),
    }


def load_dukascopy_hour(path: Path, price_decimals: int = 3) -> pd.DataFrame:
    payload = json.loads(path.read_text(encoding="utf-8"))
    arrays = ("times", "bids", "asks", "bidVolumes", "askVolumes")
    missing = [
        key
        for key in ("timestamp", "multiplier", "bid", "ask", *arrays)
        if key not in payload
    ]
    if missing:
        raise ValueError(f"Dukascopy fields missing in {path}: {missing}")
    lengths = {len(payload[key]) for key in arrays}
    if len(lengths) != 1:
        raise ValueError(f"Dukascopy arrays differ in {path}")
    multiplier = float(payload["multiplier"])
    if multiplier <= 0.0 or not np.isfinite(multiplier):
        raise ValueError(f"Invalid Dukascopy multiplier in {path}")
    factor = float(10**price_decimals)
    times = int(payload["timestamp"]) + np.cumsum(
        np.asarray(payload["times"], dtype=np.int64), dtype=np.int64
    )
    bid = (
        np.floor(
            (
                float(payload["bid"])
                + np.cumsum(np.asarray(payload["bids"], dtype=float)) * multiplier
            )
            * factor
            + 0.5
            + 1e-9
        )
        / factor
    )
    ask = (
        np.floor(
            (
                float(payload["ask"])
                + np.cumsum(np.asarray(payload["asks"], dtype=float)) * multiplier
            )
            * factor
            + 0.5
            + 1e-9
        )
        / factor
    )
    if bool(np.any(np.diff(times) < 0)):
        raise ValueError(f"Dukascopy timestamps are unsorted in {path}")
    if bool(np.any((bid <= 0.0) | (ask < bid))):
        raise ValueError(f"Dukascopy quotes are invalid in {path}")
    return pd.DataFrame({"timestamp_ms": times, "bid": bid, "ask": ask})


def tick_equity_curve(
    ticks: pd.DataFrame,
    trades: pd.DataFrame,
    execution: Mapping[str, Any],
    stress: bool,
) -> np.ndarray:
    times = ticks["timestamp_ms"].to_numpy(dtype=np.int64)
    bid = ticks["bid"].to_numpy(dtype=float)
    equity = np.zeros(len(ticks), dtype=float)
    for trade in trades.itertuples(index=False):
        entry_ms = int(pd.Timestamp(trade.entry_time).value // 1_000_000)
        exit_ms = int(pd.Timestamp(trade.exit_time).value // 1_000_000)
        active = (times >= entry_ms) & (times < exit_ms)
        exited = times >= exit_ms
        risk = float(trade.initial_risk_price)
        if bool(active.any()):
            pnl = np.clip(bid[active], float(trade.stop), float(trade.target)) - float(
                trade.entry_price
            )
            if stress:
                elapsed_days = (times[active] - entry_ms) / 86_400_000.0
                pnl -= (
                    float(execution["ticket_cost_usd"])
                    + elapsed_days * float(execution["holding_cost_per_24h_usd"])
                    + float(execution["stress_slippage_r"]) * risk
                )
            equity[active] += pnl
        if bool(exited.any()):
            equity[exited] += (
                float(trade.stress_net_r) * risk
                if stress
                else float(trade.exit_price) - float(trade.entry_price)
            )
    return equity


def exact_tick_drawdown(
    peak_ticks: pd.DataFrame,
    trough_ticks: pd.DataFrame,
    trades: pd.DataFrame,
    execution: Mapping[str, Any],
    stress: bool,
) -> dict[str, Any]:
    peak_curve = tick_equity_curve(peak_ticks, trades, execution, stress)
    trough_curve = tick_equity_curve(trough_ticks, trades, execution, stress)
    peak_index = int(np.argmax(peak_curve))
    trough_index = int(np.argmin(trough_curve))
    peak = float(peak_curve[peak_index])
    trough = float(trough_curve[trough_index])
    return {
        "maximum_drawdown_dollars": peak - trough,
        "peak_equity_dollars": peak,
        "trough_equity_dollars": trough,
        "peak_time_utc": pd.Timestamp(
            int(peak_ticks.iloc[peak_index]["timestamp_ms"]), unit="ms", tz="UTC"
        ).isoformat(),
        "trough_time_utc": pd.Timestamp(
            int(trough_ticks.iloc[trough_index]["timestamp_ms"]),
            unit="ms",
            tz="UTC",
        ).isoformat(),
        "peak_tick_rows": int(len(peak_ticks)),
        "trough_tick_rows": int(len(trough_ticks)),
    }


def account_sizing(
    stress_drawdown: float, account: Mapping[str, Any]
) -> dict[str, Any]:
    equity = float(account["current_equity_dollars"])
    limit = float(account["maximum_equity_drawdown_fraction"])
    buffer = float(account["capital_safety_buffer_multiple"])
    reference_lot = float(account["reference_lot"])
    allowed = equity * limit
    minimum_equity = stress_drawdown / limit
    buffered_minimum = stress_drawdown * buffer / limit
    maximum_lot = reference_lot * allowed / (stress_drawdown * buffer)
    legacy = float(account["legacy_core_floating_drawdown_dollars"])
    legacy_minimum = legacy / limit
    buffered_legacy_minimum = legacy * buffer / limit
    broker_minimum = float(account["broker_minimum_lot"])
    return {
        "current_equity_dollars": equity,
        "maximum_allowed_drawdown_dollars": allowed,
        "capped_r1_stress_drawdown_fraction": stress_drawdown / equity,
        "minimum_equity_capped_r1_dollars": minimum_equity,
        "buffered_minimum_equity_capped_r1_dollars": buffered_minimum,
        "maximum_lot_at_current_equity_with_buffer": maximum_lot,
        "broker_minimum_lot": broker_minimum,
        "broker_lot_step": float(account["broker_lot_step"]),
        "capped_r1_fits_without_buffer": stress_drawdown <= allowed,
        "capped_r1_fits_with_buffer": stress_drawdown * buffer <= allowed,
        "broker_can_express_safe_lot": broker_minimum <= maximum_lot,
        "legacy_core_floating_drawdown_dollars": legacy,
        "minimum_equity_legacy_core_dollars": legacy_minimum,
        "buffered_minimum_equity_legacy_core_dollars": buffered_legacy_minimum,
        "account_readiness_decision": "FAIL_CURRENT_ACCOUNT_CAPITAL_INADEQUATE",
    }


def _episode_rows(original: pd.DataFrame, episode: Mapping[str, Any]) -> pd.DataFrame:
    peak = pd.Timestamp(episode["peak_time_utc"])
    trough = pd.Timestamp(episode["trough_time_utc"])
    return original.loc[
        original["exit_time_utc"].gt(peak) & original["exit_time_utc"].le(trough)
    ].copy()


def run_audit(config: Mapping[str, Any], repo_root: Path) -> AuditArtifacts:
    source_audit = verify_sources(repo_root, config["sources"], external=False)
    external_audit = verify_sources(
        repo_root, config["external_sources"], external=True
    )
    ledger_path = repo_root / config["sources"]["normalized_core_ledger"]["path"]
    ledger = load_ledger(ledger_path)
    capped, decisions = apply_frozen_r1_cap(ledger, config["frozen_control"])
    cutoff = pd.Timestamp(config["cutoff_exclusive_utc"])
    rows: list[dict[str, Any]] = []
    for window, start_text in config["windows"].items():
        start = pd.Timestamp(start_text)
        for policy, frame in (("ORIGINAL", ledger), ("FROZEN_R1_CAP", capped)):
            rows.append(
                {
                    "window": window,
                    **window_metrics(frame, start, cutoff, policy),
                }
            )
    windows = pd.DataFrame(rows)
    one_year = ledger.loc[
        ledger["exit_time_utc"].ge(pd.Timestamp(config["windows"]["1Y"]))
        & ledger["exit_time_utc"].lt(cutoff)
    ]
    original_episode = drawdown_episode(
        one_year,
        "pnl_usd_0p01_equiv",
        "exit_time_utc",
        pd.Timestamp(config["windows"]["1Y"]),
    )
    episode = _episode_rows(one_year, original_episode)
    attribution = (
        episode.groupby(
            ["specialist_id", "regime", "source_strategy"],
            dropna=False,
            observed=True,
        )["pnl_usd_0p01_equiv"]
        .agg([("trades", "size"), ("net_pnl_dollars", "sum")])
        .reset_index()
        .sort_values("net_pnl_dollars")
    )

    portability_path = Path(source_audit["r1_portability_module"]["path"])
    portability = _load_portability_module(portability_path)
    portability_config_path = Path(source_audit["r1_portability_config"]["path"])
    portability_config = json.loads(portability_config_path.read_text(encoding="utf-8"))
    portability_run = portability.run_portability(portability_config)
    policy_id = config["frozen_control"]["source_policy_id"]
    policy_trades = portability_run.policy_trades.loc[
        portability_run.policy_trades["policy_id"].eq(policy_id)
    ].copy()
    base_m5 = mark_portability_policy(
        policy_trades,
        portability_run.source_m5,
        portability_config["execution"],
        stress=False,
    )
    stress_m5 = mark_portability_policy(
        policy_trades,
        portability_run.source_m5,
        portability_config["execution"],
        stress=True,
    )
    peak_ticks = load_dukascopy_hour(Path(external_audit["exact_peak_hour"]["path"]))
    trough_ticks = load_dukascopy_hour(
        Path(external_audit["exact_trough_hour"]["path"])
    )
    base_exact = exact_tick_drawdown(
        peak_ticks,
        trough_ticks,
        policy_trades,
        portability_config["execution"],
        stress=False,
    )
    stress_exact = exact_tick_drawdown(
        peak_ticks,
        trough_ticks,
        policy_trades,
        portability_config["execution"],
        stress=True,
    )
    if pd.Timestamp(base_m5["peak_bar_start_utc"]).floor("h") != pd.Timestamp(
        base_exact["peak_time_utc"]
    ).floor("h"):
        raise ValueError("Exact peak hour does not match global M5 peak hour")
    if pd.Timestamp(base_m5["trough_bar_start_utc"]).floor("h") != pd.Timestamp(
        base_exact["trough_time_utc"]
    ).floor("h"):
        raise ValueError("Exact trough hour does not match global M5 trough hour")

    sizing = account_sizing(
        float(stress_exact["maximum_drawdown_dollars"]),
        config["account_reference"],
    )
    original_1y = windows.loc[
        windows["window"].eq("1Y") & windows["policy"].eq("ORIGINAL")
    ].iloc[0]
    capped_1y = windows.loc[
        windows["window"].eq("1Y") & windows["policy"].eq("FROZEN_R1_CAP")
    ].iloc[0]
    result = {
        "schema_version": config["schema_version"],
        "decision": "R1_STACKING_CONTROL_EFFECTIVE_ACCOUNT_NOT_READY",
        "source_audit": source_audit,
        "external_source_audit": external_audit,
        "original_one_year_drawdown_episode": original_episode,
        "original_one_year_episode_attribution": attribution.to_dict("records"),
        "frozen_cap_audit": {
            "target_rows": int(len(decisions)),
            "accepted_rows": int(decisions["accepted"].sum()),
            "rejected_rows": int((~decisions["accepted"]).sum()),
            "original_ledger_rows": int(len(ledger)),
            "capped_ledger_rows": int(len(capped)),
            "one_year_original_closed_drawdown_dollars": float(
                original_1y["closed_drawdown_dollars"]
            ),
            "one_year_capped_closed_drawdown_dollars": float(
                capped_1y["closed_drawdown_dollars"]
            ),
            "one_year_drawdown_reduction_fraction": 1.0
            - float(capped_1y["closed_drawdown_dollars"])
            / float(original_1y["closed_drawdown_dollars"]),
            "one_year_original_trades_per_weekday": float(
                original_1y["trades_per_weekday"]
            ),
            "one_year_capped_trades_per_weekday": float(
                capped_1y["trades_per_weekday"]
            ),
        },
        "dukascopy_frozen_policy": {
            "policy_id": policy_id,
            "trades": int(len(policy_trades)),
            "base_m5_conservative": base_m5,
            "stress_m5_conservative": stress_m5,
            "base_exact_tick": base_exact,
            "stress_exact_tick": stress_exact,
        },
        "account_sizing": sizing,
        "required_controls": {
            "r1_maximum_concurrent_positions": int(
                config["frozen_control"]["maximum_concurrent_positions"]
            ),
            "r1_maximum_entries_per_utc_day": int(
                config["frozen_control"]["maximum_entries_per_utc_day"]
            ),
            "reject_reference_lot_until_buffered_equity_requirement_met": True,
            "reject_reference_lot_when_broker_minimum_exceeds_safe_lot": True,
            "retain_v42_exact_shared_account_forward_gate": True,
            "demo_or_live_activation_authorized": False,
        },
        "limitations": {
            "diagnostic_after_outcome_observation": True,
            "normalized_ledger_has_no_intratrade_marks": True,
            "full_five_specialist_historical_floating_curve_reconstructed": False,
            "v42_forward_shared_account_evidence_required": True,
        },
        "research_controls": config["research_controls"],
    }
    return AuditArtifacts(result, windows, decisions, episode)

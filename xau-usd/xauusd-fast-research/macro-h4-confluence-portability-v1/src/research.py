from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[4]
FAST_ROOT = REPO_ROOT / "xau-usd" / "xauusd-fast-research"
PHASE0_ROOT = REPO_ROOT / "xau-usd" / "xauusd-phase0"
PHASE0_SRC = PHASE0_ROOT / "src"
SHARED_DATA_PATH = FAST_ROOT / "independent-specialists-v1" / "src" / "data.py"
sys.path.insert(0, str(PHASE0_SRC))

from phase0.credit_spread_data import CREDIT_SPREAD_FRAME_KEY, load_credit_spread_context  # noqa: E402
from phase0.financial_conditions_data import (  # noqa: E402
    FINANCIAL_CONDITIONS_FRAME_KEY,
    load_financial_conditions_context,
)
from phase0.gvz_volatility_data import GVZ_FRAME_KEY, load_gvz_volatility_context  # noqa: E402
from phase0.inflation_expectations_data import (  # noqa: E402
    INFLATION_EXPECTATIONS_FRAME_KEY,
    load_inflation_expectations_context,
)
from phase0.macro_real_yield_data import MACRO_FRAME_KEY, load_macro_real_yield_context  # noqa: E402
from phase0.strategies.h4_macro_momentum_confluence_v0 import (  # noqa: E402
    H4MacroMomentumConfluenceV0Strategy,
)
from phase0.treasury_curve_data import TREASURY_CURVE_FRAME_KEY, load_treasury_curve_context  # noqa: E402
from phase0.vix_risk_data import VIX_FRAME_KEY, load_vix_risk_context  # noqa: E402


STRATEGY_ID = "h4_macro_momentum_confluence_v0"


def _load_shared_data() -> Any:
    name = "xau_macro_h4_shared_data"
    spec = importlib.util.spec_from_file_location(name, SHARED_DATA_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load shared data module from {SHARED_DATA_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SHARED_DATA = _load_shared_data()


@dataclass(frozen=True)
class ResearchRun:
    signals: pd.DataFrame
    trades: pd.DataFrame
    source_m5: pd.DataFrame
    evidence: dict[str, Any]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_frozen_sources(config: dict[str, Any]) -> dict[str, str]:
    observed: dict[str, str] = {}
    for item in config["frozen_sources"]:
        path = REPO_ROOT / item["path"]
        actual = sha256_file(path)
        if actual != item["sha256"]:
            raise ValueError(f"Frozen source hash mismatch for {path}: {actual}")
        observed[item["path"]] = actual
    return observed


def adapt_m5(source: pd.DataFrame) -> pd.DataFrame:
    frame = source.copy()
    required = {"tick_spread_max", "xau_tick_count"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Dukascopy cache is missing macro portability columns: {missing}")
    for column in ("bar_start_utc", "bar_end_utc", "timestamp_utc"):
        frame[column] = pd.to_datetime(frame[column], utc=True).astype("datetime64[ns, UTC]")
    for field in ("open", "high", "low", "close"):
        frame[field] = frame[f"mid_{field}"]
    frame["volume"] = frame["xau_tick_count"].astype(float)
    frame["broker"] = "dukascopy"
    frame["symbol"] = "XAUUSD"
    return frame


def _strategy_bars(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for field in ("open", "high", "low", "close"):
        result[field] = result[f"mid_{field}"]
    return result


def _macro_context(start: pd.Timestamp, end: pd.Timestamp) -> dict[str, pd.DataFrame]:
    project = SimpleNamespace(root=PHASE0_ROOT)
    context = {
        MACRO_FRAME_KEY: load_macro_real_yield_context(project, start, end),
        INFLATION_EXPECTATIONS_FRAME_KEY: load_inflation_expectations_context(project, start, end),
        TREASURY_CURVE_FRAME_KEY: load_treasury_curve_context(project, start, end),
        CREDIT_SPREAD_FRAME_KEY: load_credit_spread_context(project, start, end),
        VIX_FRAME_KEY: load_vix_risk_context(project, start, end),
        GVZ_FRAME_KEY: load_gvz_volatility_context(project, start, end),
        FINANCIAL_CONDITIONS_FRAME_KEY: load_financial_conditions_context(project, start, end),
    }
    for frame in context.values():
        frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True).astype("datetime64[ns, UTC]")
    return context


def generate_candidates(h4: pd.DataFrame, d1: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    start = pd.Timestamp(config["windows"]["full"][0])
    end = pd.Timestamp(config["windows"]["full"][1]) - pd.Timedelta(days=1)
    context: dict[str, Any] = {
        "symbol": "XAUUSD",
        "H4": _strategy_bars(h4),
        "D1": _strategy_bars(d1),
        **_macro_context(start, end),
    }
    strategy = H4MacroMomentumConfluenceV0Strategy()
    rows: list[dict[str, Any]] = []
    for signal in strategy.generate_signals(context):
        plan = strategy.build_trade_plan(signal, context)
        rows.append(
            {
                "strategy_id": STRATEGY_ID,
                "signal_time": pd.Timestamp(signal.timestamp_utc),
                "direction": signal.direction,
                "stop": float(plan.stop_loss),
                "target": float(plan.take_profit),
                "max_holding_bars": int(plan.metadata["max_holding_bars"]),
                "macro_composite_score": int(signal.metadata["macro_composite_score"]),
                "macro_bull_votes": int(signal.metadata["macro_bull_votes"]),
                "macro_bear_votes": int(signal.metadata["macro_bear_votes"]),
                "h4_atr14": float(signal.metadata["h4_atr14"]),
                "d1_return_5": float(signal.metadata["d1_return_5"]),
            }
        )
    columns = [
        "strategy_id", "signal_time", "direction", "stop", "target", "max_holding_bars",
        "macro_composite_score", "macro_bull_votes", "macro_bear_votes", "h4_atr14", "d1_return_5",
    ]
    return pd.DataFrame(rows, columns=columns).sort_values("signal_time", kind="mergesort").reset_index(drop=True)


def _execution_spread(row: pd.Series, at_open: bool) -> float:
    suffix = "open" if at_open else "close"
    return max(0.0, float(row[f"ask_{suffix}"] - row[f"bid_{suffix}"]))


def _simulate_one(m5: pd.DataFrame, entry_index: int, candidate: pd.Series, execution: dict[str, Any]) -> dict[str, Any]:
    direction = str(candidate["direction"])
    entry_row = m5.iloc[entry_index]
    entry = float(entry_row["ask_open"] if direction == "LONG" else entry_row["bid_open"])
    stop = float(candidate["stop"])
    target = float(candidate["target"])
    risk = entry - stop if direction == "LONG" else stop - entry
    reward = target - entry if direction == "LONG" else entry - target
    if not np.isfinite(risk) or risk <= 0 or not np.isfinite(reward) or reward <= 0:
        return {"accepted": False, "rejection_reason": "INVALID_EXECUTABLE_GEOMETRY"}
    if risk * float(execution["ounces"]) > float(execution["maximum_initial_risk_usd"]):
        return {"accepted": False, "rejection_reason": "MINIMUM_LOT_RISK_EXCEEDED"}

    end = min(entry_index + int(candidate["max_holding_bars"]), len(m5))
    exit_index = end - 1
    exit_reason = "END_OF_DATA" if end == len(m5) else "TIME_STOP"
    exit_at_open = False
    exit_price = float(m5.iloc[exit_index]["bid_close"] if direction == "LONG" else m5.iloc[exit_index]["ask_close"])
    ambiguous = False
    barrier_resolved = False
    for index in range(entry_index, end):
        row = m5.iloc[index]
        if direction == "LONG":
            executable_open = float(row["bid_open"])
            if executable_open <= stop:
                exit_index, exit_reason, exit_price, exit_at_open = index, "GAP_THROUGH_STOP", executable_open, True
                barrier_resolved = True
                break
            stop_hit = float(row["bid_low"]) <= stop
            target_hit = float(row["bid_high"]) >= target
        else:
            executable_open = float(row["ask_open"])
            if executable_open >= stop:
                exit_index, exit_reason, exit_price, exit_at_open = index, "GAP_THROUGH_STOP", executable_open, True
                barrier_resolved = True
                break
            stop_hit = float(row["ask_high"]) >= stop
            target_hit = float(row["ask_low"]) <= target
        if stop_hit or target_hit:
            ambiguous = bool(stop_hit and target_hit)
            exit_index = index
            exit_reason = "AMBIGUOUS_STOP_FIRST" if ambiguous else ("STOP" if stop_hit else "TARGET")
            exit_price = stop if stop_hit else target
            barrier_resolved = True
            break

    if end == len(m5) and not barrier_resolved:
        return {"accepted": False, "rejection_reason": "UNRESOLVED_END_OF_DATA"}

    exit_row = m5.iloc[exit_index]
    entry_time = pd.Timestamp(entry_row["bar_start_utc"])
    exit_time = pd.Timestamp(exit_row["bar_start_utc"] if exit_at_open else exit_row["timestamp_utc"])
    sign = 1.0 if direction == "LONG" else -1.0
    net_r = sign * (exit_price - entry) / risk
    entry_spread = _execution_spread(entry_row, True)
    exit_spread = _execution_spread(exit_row, exit_at_open)
    entry_max = max(entry_spread, float(entry_row["tick_spread_max"]))
    exit_max = max(exit_spread, float(exit_row["tick_spread_max"]))
    spread_stress_r = (0.5 * (entry_max - entry_spread) + 0.5 * (exit_max - exit_spread)) / risk
    holding_days = max(0.0, (exit_time - entry_time).total_seconds() / 86400.0)
    risk_usd = risk * float(execution["ounces"])
    cash_cost_r = (
        float(execution["ticket_cost_usd"])
        + holding_days * float(execution["holding_cost_per_24h_usd"])
    ) / risk_usd
    all_in_extra_cost_r = spread_stress_r + float(execution["stress_slippage_r"]) + cash_cost_r
    return {
        "accepted": True,
        "entry_time": entry_time,
        "exit_time": exit_time,
        "entry_price": entry,
        "exit_price": exit_price,
        "stop": stop,
        "target": target,
        "initial_risk": risk,
        "initial_risk_usd": risk_usd,
        "exit_reason": exit_reason,
        "ambiguous_bar": ambiguous,
        "holding_minutes": (exit_time - entry_time).total_seconds() / 60.0,
        "net_r": net_r,
        "stress_net_r": net_r - all_in_extra_cost_r,
        "stress_extra_cost_r": all_in_extra_cost_r,
        "spread_stress_r": spread_stress_r,
        "cash_cost_r": cash_cost_r,
    }


def simulate_signals(m5: pd.DataFrame, candidates: pd.DataFrame, execution: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    starts = m5["bar_start_utc"].to_numpy(dtype="datetime64[ns]")
    signal_rows: list[dict[str, Any]] = []
    trade_rows: list[dict[str, Any]] = []
    open_until = pd.Timestamp.min.tz_localize("UTC")
    for _, candidate in candidates.sort_values("signal_time", kind="mergesort").iterrows():
        signal_time = pd.Timestamp(candidate["signal_time"])
        ledger = candidate.to_dict()
        entry_index = int(np.searchsorted(starts, np.datetime64(signal_time.tz_convert(None)), side="left"))
        if entry_index >= len(m5):
            outcome = {"accepted": False, "rejection_reason": "NO_ENTRY_BAR"}
        elif signal_time <= open_until:
            outcome = {"accepted": False, "rejection_reason": "POSITION_ALREADY_OPEN"}
        else:
            outcome = _simulate_one(m5, entry_index, candidate, execution)
        ledger.update(outcome)
        signal_rows.append(ledger)
        if outcome["accepted"]:
            trade_rows.append(ledger)
            open_until = pd.Timestamp(outcome["exit_time"])
    signals = pd.DataFrame(signal_rows)
    trades = pd.DataFrame(trade_rows)
    if not trades.empty:
        trades = trades.sort_values("entry_time", kind="mergesort").reset_index(drop=True)
    return signals, trades


def run_research(config: dict[str, Any]) -> ResearchRun:
    frozen_hashes = verify_frozen_sources(config)
    source, evidence = SHARED_DATA.load_m5(config)
    m5 = adapt_m5(source)
    end = pd.Timestamp(config["windows"]["full"][1])
    m5 = m5.loc[m5["bar_start_utc"] < end].reset_index(drop=True)
    h4 = SHARED_DATA.aggregate_complete_bars(m5, 240, "H4")
    d1 = SHARED_DATA.aggregate_complete_bars(m5, 1440, "D1")
    candidates = generate_candidates(h4, d1, config)
    signals, trades = simulate_signals(m5, candidates, config["execution"])
    evidence = {
        **evidence,
        "frozen_source_hashes": frozen_hashes,
        "m5_rows_used": int(len(m5)),
        "h4_rows": int(len(h4)),
        "d1_rows": int(len(d1)),
        "candidate_rows": int(len(candidates)),
        "trade_rows": int(len(trades)),
        "last_source_bar_used": m5["timestamp_utc"].max().isoformat(),
    }
    return ResearchRun(signals, trades, m5, evidence)


def profit_factor(values: pd.Series) -> float | None:
    positive = float(values.loc[values > 0].sum())
    negative = float(-values.loc[values < 0].sum())
    if negative == 0:
        return None if positive == 0 else float("inf")
    return positive / negative


def drawdown(values: pd.Series) -> float:
    equity = values.fillna(0.0).cumsum()
    return float((equity.cummax() - equity).max()) if len(equity) else 0.0


def stage_metrics(trades: pd.DataFrame, source_m5: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp, top_n: int) -> dict[str, Any]:
    stage = trades.loc[(trades["entry_time"] >= start) & (trades["entry_time"] < end)].copy()
    source_days = int(
        source_m5.loc[
            (source_m5["bar_start_utc"] >= start) & (source_m5["bar_start_utc"] < end),
            "bar_start_utc",
        ].dt.date.nunique()
    )
    baseline = stage["net_r"].astype(float) if not stage.empty else pd.Series(dtype=float)
    stress = stage["stress_net_r"].astype(float) if not stage.empty else pd.Series(dtype=float)
    years = (
        stage.assign(year=stage["entry_time"].dt.year).groupby("year")["stress_net_r"].sum()
        if not stage.empty else pd.Series(dtype=float)
    )
    removed = stress.drop(stress.nlargest(min(top_n, len(stress))).index) if len(stress) else stress
    return {
        "trades": int(len(stage)),
        "long_trades": int(stage["direction"].eq("LONG").sum()) if len(stage) else 0,
        "short_trades": int(stage["direction"].eq("SHORT").sum()) if len(stage) else 0,
        "source_days": source_days,
        "trades_per_source_day": len(stage) / source_days if source_days else 0.0,
        "net_r": float(baseline.sum()),
        "profit_factor": profit_factor(baseline),
        "average_r": float(baseline.mean()) if len(baseline) else 0.0,
        "stress_net_r": float(stress.sum()),
        "stress_profit_factor": profit_factor(stress),
        "average_stress_r": float(stress.mean()) if len(stress) else 0.0,
        "stress_drawdown_r": drawdown(stress),
        "positive_active_year_share": float((years > 0).mean()) if len(years) else 0.0,
        "top_winners_removed_stress_net_r": float(removed.sum()),
    }


def evaluate_gate(value: dict[str, Any], gate: dict[str, Any]) -> tuple[bool, dict[str, bool]]:
    checks = {
        "minimum_trades": value["trades"] >= int(gate["minimum_trades"]),
        "both_directions": value["long_trades"] > 0 and value["short_trades"] > 0,
        "minimum_frequency": value["trades_per_source_day"] >= float(gate["minimum_trades_per_source_day"]),
        "minimum_pf": value["profit_factor"] is not None and value["profit_factor"] >= float(gate["minimum_pf"]),
        "minimum_stress_pf": value["stress_profit_factor"] is not None and value["stress_profit_factor"] >= float(gate["minimum_stress_pf"]),
        "minimum_average_stress_r": value["average_stress_r"] >= float(gate["minimum_average_stress_r"]),
        "maximum_drawdown_r": value["stress_drawdown_r"] <= float(gate["maximum_drawdown_r"]),
        "top_winners_removed_positive": value["top_winners_removed_stress_net_r"] > 0,
    }
    if "minimum_positive_active_year_share" in gate:
        checks["minimum_positive_active_year_share"] = value["positive_active_year_share"] >= float(
            gate["minimum_positive_active_year_share"]
        )
    return all(checks.values()), checks

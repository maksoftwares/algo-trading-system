from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.research import PIP, _load_v1_module, _quarantine_filter, _write_csv, add_h4_regimes, measure
from run_v2r_sequential import session_mask

CACHE = Path("C:/DukascopyTickDataFoundationV1/research/eurusd-regime-specialists-v2/EURUSD_M5_BIDASK_2024_07_2026_06.csv.gz")
METADATA = CACHE.with_suffix("").with_suffix(".metadata.json")


def exact_simulate(
    h1: pd.DataFrame,
    m5: pd.DataFrame,
    mask: np.ndarray,
    specialist: dict,
    execution: dict,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> tuple[list[dict], dict]:
    slippage = float(execution["entry_exit_slippage_pips_each"]) * PIP
    stress_extra = float(execution["primary_stress_extra_pips_roundtrip"])
    m5_times = m5["timestamp"].to_numpy()
    time_to_index = {pd.Timestamp(value): index for index, value in enumerate(m5_times)}
    arrays = {
        field: m5[field].to_numpy(dtype=float)
        for field in (
            "bid_open", "bid_high", "bid_low", "bid_close",
            "ask_open", "ask_high", "ask_low", "ask_close",
        )
    }
    eligible = np.flatnonzero(
        mask
        & (h1["timestamp"] >= start).to_numpy()
        & (h1["timestamp"] < end).to_numpy()
    )
    trades = []
    diagnostics = {
        "eligible_h1_signals": len(eligible),
        "missing_exact_entry_bar": 0,
        "spread_rejections": 0,
        "overlap_rejections": 0,
        "invalid_atr_rejections": 0,
    }
    blocked_until = -1
    for signal_index in eligible:
        signal_time = pd.Timestamp(h1["timestamp"].iloc[signal_index])
        entry_time = signal_time + pd.Timedelta(hours=1)
        entry_index = time_to_index.get(entry_time)
        if entry_index is None:
            diagnostics["missing_exact_entry_bar"] += 1
            continue
        if entry_index <= blocked_until:
            diagnostics["overlap_rejections"] += 1
            continue
        spread = (arrays["ask_open"][entry_index] - arrays["bid_open"][entry_index]) / PIP
        if spread > float(execution["maximum_entry_spread_pips"]):
            diagnostics["spread_rejections"] += 1
            continue
        stop_distance = float(specialist["stop_atr"]) * float(h1["atr"].iloc[signal_index])
        if not math.isfinite(stop_distance) or stop_distance <= 0:
            diagnostics["invalid_atr_rejections"] += 1
            continue
        entry = arrays["bid_open"][entry_index] - slippage
        stop = entry + stop_distance
        target = entry - float(specialist["target_r"]) * stop_distance
        final_index = min(entry_index + int(specialist["max_hold_bars"]) * 12 - 1, len(m5) - 1)
        exit_index = final_index
        exit_price = arrays["ask_close"][final_index] + slippage
        reason = "time"
        for index in range(entry_index, final_index + 1):
            if arrays["ask_open"][index] >= stop:
                exit_price = arrays["ask_open"][index] + slippage
                exit_index = index
                reason = "stop_gap"
                break
            stop_hit = arrays["ask_high"][index] >= stop
            target_hit = arrays["ask_low"][index] <= target
            if stop_hit:
                exit_price = stop + slippage
                exit_index = index
                reason = "stop"
                break
            if target_hit:
                exit_price = target + slippage
                exit_index = index
                reason = "target"
                break
        net_pips = (entry - exit_price) / PIP
        trades.append(
            {
                "candidate_id": specialist["specialist_id"],
                "archetype": "session_expansion_short",
                "direction": "short",
                "signal_time": signal_time.isoformat(),
                "entry_time": pd.Timestamp(m5_times[entry_index]).isoformat(),
                "exit_time": pd.Timestamp(m5_times[exit_index]).isoformat(),
                "entry": entry,
                "exit": exit_price,
                "stop": stop,
                "target": target,
                "spread_pips": spread,
                "net_pips": net_pips,
                "stress_net_pips": net_pips - stress_extra,
                "exit_reason": reason,
            }
        )
        blocked_until = exit_index
    return trades, diagnostics


def main() -> None:
    base = json.loads(
        (ROOT / "config" / "eurusd_regime_specialists_v2.json").read_text(encoding="utf-8")
    )
    classifier = json.loads(
        (ROOT / "config" / "eurusd_regime_specialists_v2r_train_hunt.json").read_text(encoding="utf-8")
    )["classifier"]
    frozen = json.loads(
        (ROOT / "config" / "eurusd_v4_final_exam.json").read_text(encoding="utf-8")
    )
    specialist = frozen["candidate"]
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    if hashlib.sha256(CACHE.read_bytes()).hexdigest() != metadata["cache_sha256"]:
        raise RuntimeError("M5 cache checksum mismatch")
    storage = Path(base["source"]["storage_root"])
    h1_cache = storage / base["source"]["h1_cache"]
    h1 = pd.read_csv(h1_cache, compression="gzip", parse_dates=["timestamp"])
    h1["timestamp"] = pd.to_datetime(h1["timestamp"], utc=True)
    h1, _ = add_h4_regimes(h1, classifier)
    module = _load_v1_module(ROOT)
    h1 = module.add_features(h1, base)
    mask = session_mask(h1, specialist).to_numpy()
    m5 = pd.read_csv(CACHE, compression="gzip", parse_dates=["timestamp"])
    m5["timestamp"] = pd.to_datetime(m5["timestamp"], utc=True)
    start, end = (pd.Timestamp(value) for value in frozen["exam_window"])
    trades, diagnostics = exact_simulate(
        h1, m5, mask, specialist, base["execution"], start, end
    )
    trades = _quarantine_filter(trades, base["source"]["quarantined_utc_intervals"])
    row = measure(trades, specialist, "exact_m5_exam", frozen["exam_gate"])
    h1_trades = pd.read_csv(ROOT / "outputs" / "v4_final_exam" / "EXAM_TRADES.csv")
    h1_entries = set(h1_trades["entry_time"])
    m5_entries = {trade["entry_time"] for trade in trades}
    parity = {
        **diagnostics,
        "h1_screen_trades": len(h1_trades),
        "exact_m5_trades": len(trades),
        "common_entry_timestamps": len(h1_entries & m5_entries),
        "h1_only_entry_timestamps": len(h1_entries - m5_entries),
        "m5_only_entry_timestamps": len(m5_entries - h1_entries),
        "m5_cache_sha256": metadata["cache_sha256"],
    }
    output = ROOT / "outputs" / "v4_exact_m5"
    output.mkdir(parents=True, exist_ok=True)
    _write_csv(output / "EXACT_M5_METRICS.csv", [row])
    _write_csv(output / "EXACT_M5_TRADES.csv", trades)
    (output / "PARITY.json").write_text(
        json.dumps(parity, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    economic = bool(
        row["stress_profit_factor"] >= frozen["exam_gate"]["minimum_stress_profit_factor"]
        and row["average_r"] >= frozen["exam_gate"]["minimum_average_r"]
        and row["positive_active_month_share"] >= frozen["exam_gate"]["minimum_positive_active_month_share"]
        and row["maximum_drawdown_r"] <= frozen["exam_gate"]["maximum_drawdown_r"]
        and row["removed_profit_factor"] >= frozen["exam_gate"]["minimum_removed_profit_factor"]
    )
    verdict = {
        "exact_m5_gate_pass": bool(row["gate_pass"]),
        "exact_m5_economic_gates_pass": economic,
        "frequency_shortfall_only": economic and row["trades"] < frozen["exam_gate"]["minimum_trades"],
        "mt5_replication_required_for_ordering_demo": economic,
        "shadow_demo_candidate": economic,
        "ordering_demo_ready": False,
        "verdict": "LOW_FREQUENCY_SHADOW_DEMO_CANDIDATE" if economic else "EXACT_M5_FAIL_STOP",
    }
    (output / "VERDICT.json").write_text(
        json.dumps(verdict, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps({"metrics": row, "parity": parity, "verdict": verdict}, indent=2))


if __name__ == "__main__":
    main()

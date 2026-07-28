from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from .ensemble import load_ensemble_config
from .neutral_causal import oracle_match
from .neutral_session_oco import (
    _effective_ask,
    _walk_exit,
    summarize,
    write_json,
)
from .research import (
    PACKAGE_ROOT,
    PIP,
    is_quarantined,
    load_inputs,
    sha256_file,
)


FAMILY = "N19_NEUTRAL_SESSION_OPENING_DRIVE"
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_opening_drive"


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_opening_drive.json"
        ).read_text(encoding="utf-8")
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_OPENING_DRIVE_PREREG_2026_07_28.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if (
        lock.get("locked_before_opening_drive_outcome_pass")
        is not True
    ):
        raise RuntimeError("Neutral opening-drive contract is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                "Neutral opening-drive preregistration mismatch: "
                f"{relative}"
            )
        checked[relative] = actual
    return checked


def build_drive_candidates(
    m5: pd.DataFrame,
    state: pd.DataFrame,
    cfg: dict[str, Any],
    *,
    enforce_frozen_census: bool,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    strategy = cfg["strategy"]
    anchor_hours = set(
        int(value) for value in strategy["anchor_hours_utc"]
    )
    anchors = m5.index[
        (m5.index.minute == 0)
        & np.isin(m5.index.hour, list(anchor_hours))
        & (m5.index.weekday < 5)
    ]
    observation_minutes = int(
        strategy["observation_window_minutes"]
    )
    expected_bars = observation_minutes // 5
    minimum_body = (
        float(strategy["minimum_absolute_body_pips"]) * PIP
    )
    close_location_threshold = float(
        strategy["minimum_directional_close_location"]
    )
    records: list[dict[str, Any]] = []
    for anchor in anchors:
        start = int(m5.index.searchsorted(anchor, side="left"))
        entry_time = anchor + pd.Timedelta(
            minutes=observation_minutes
        )
        end = int(m5.index.searchsorted(entry_time, side="left"))
        observation = m5.iloc[start:end]
        if (
            len(observation) != expected_bars
            or observation.index[0] != anchor
            or observation.index[-1]
            != entry_time - pd.Timedelta(minutes=5)
            or end >= len(m5)
            or m5.index[end] != entry_time
        ):
            continue
        open_price = float(observation.iloc[0]["bid_open"])
        high = float(observation["bid_high"].max())
        low = float(observation["bid_low"].min())
        close = float(observation.iloc[-1]["bid_close"])
        bar_range = high - low
        body = close - open_price
        if bar_range <= 0:
            side = "CASH"
            close_location = 0.5
        else:
            close_location = (close - low) / bar_range
            if (
                body >= minimum_body
                and close_location >= close_location_threshold
            ):
                side = "LONG"
            elif (
                body <= -minimum_body
                and close_location
                <= 1.0 - close_location_threshold
            ):
                side = "SHORT"
            else:
                side = "CASH"
        records.append(
            {
                "family": FAMILY,
                "anchor_time_utc": anchor,
                "signal_time_utc": entry_time,
                "entry_time_utc": entry_time,
                "entry_position": end,
                "state_time_utc": anchor.floor("h")
                - pd.Timedelta(hours=1),
                "drive_open": open_price,
                "drive_high": high,
                "drive_low": low,
                "drive_close": close,
                "drive_range_pips": bar_range / PIP,
                "drive_body_pips": body / PIP,
                "drive_close_location": close_location,
                "side": side,
                "drive_signal": side != "CASH",
            }
        )
    raw = pd.DataFrame(records)
    if raw.empty:
        return raw, {}
    raw["state_time_utc"] = raw["state_time_utc"].dt.as_unit(
        "ns"
    )
    state_columns = [
        "direction",
        "shock",
        "DXY_compressed",
        "EURUSD_compressed",
    ]
    states = (
        state[state_columns]
        .reset_index()
        .rename(columns={"timestamp_utc": "matched_state_time_utc"})
        .sort_values("matched_state_time_utc")
    )
    states["matched_state_time_utc"] = states[
        "matched_state_time_utc"
    ].dt.as_unit("ns")
    joined = pd.merge_asof(
        raw.sort_values("state_time_utc"),
        states,
        left_on="state_time_utc",
        right_on="matched_state_time_utc",
        direction="backward",
        allow_exact_matches=True,
    )
    shock = joined["shock"].astype("boolean").fillna(True)
    compression = (
        joined["DXY_compressed"].astype("boolean").fillna(False)
        & joined["EURUSD_compressed"].astype("boolean").fillna(False)
    )
    joined["neutral_eligible"] = (
        joined["direction"].eq(
            cfg["neutral_ownership"]["requires_direction"]
        )
        & ~shock
        & ~compression
    )
    joined["trade_candidate"] = (
        joined["neutral_eligible"] & joined["drive_signal"]
    )
    joined["window"] = "OUTSIDE"
    for name, (start_raw, end_raw) in cfg["windows"].items():
        in_window = joined["entry_time_utc"].between(
            pd.Timestamp(start_raw),
            pd.Timestamp(end_raw),
            inclusive="both",
        )
        joined.loc[in_window, "window"] = name
    census = {
        "anchors": int(len(joined)),
        "neutral_anchors": int(joined["neutral_eligible"].sum()),
        "drive_signals": int(joined["drive_signal"].sum()),
        "trade_candidates": int(joined["trade_candidate"].sum()),
        "long_candidates": int(
            (
                joined["trade_candidate"]
                & joined["side"].eq("LONG")
            ).sum()
        ),
        "short_candidates": int(
            (
                joined["trade_candidate"]
                & joined["side"].eq("SHORT")
            ).sum()
        ),
        "by_window": {
            name: int(group["trade_candidate"].sum())
            for name, group in joined.groupby("window")
            if name != "OUTSIDE"
        },
    }
    if (
        enforce_frozen_census
        and census != cfg["outcome_blind_census"]
    ):
        raise RuntimeError(
            "Opening-drive census drift: "
            f"actual={census!r} "
            f"frozen={cfg['outcome_blind_census']!r}"
        )
    return (
        joined.sort_values("entry_time_utc").reset_index(drop=True),
        census,
    )


def simulate(
    candidates: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    strategy = cfg["strategy"]
    execution = cfg["execution"]
    spread_floor = (
        float(execution["minimum_retail_spread_pips"]) * PIP
    )
    slippage = (
        float(execution["extra_slippage_pips_per_side"]) * PIP
    )
    risk = float(execution["risk_pips"]) * PIP
    target_distance = float(execution["target_r"]) * risk
    hold = pd.Timedelta(
        hours=float(execution["maximum_hold_hours"])
    )
    base = load_ensemble_config()
    open_until: pd.Timestamp | None = None
    daily_count: dict[str, int] = {}
    diagnostics: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    for _, candidate in candidates[
        candidates["trade_candidate"]
    ].iterrows():
        entry_time = candidate["entry_time_utc"]
        diagnostic = {
            "anchor_time_utc": candidate["anchor_time_utc"],
            "entry_time_utc": entry_time,
            "side": candidate["side"],
            "drive_body_pips": candidate["drive_body_pips"],
            "drive_range_pips": candidate["drive_range_pips"],
            "drive_close_location": candidate[
                "drive_close_location"
            ],
            "status": "CANDIDATE",
        }
        if open_until is not None and entry_time <= open_until:
            diagnostic["status"] = "SKIP_POSITION_OPEN"
            diagnostics.append(diagnostic)
            continue
        if is_quarantined(
            entry_time, "EURUSD", base["quarantine"]
        ):
            diagnostic["status"] = "SKIP_QUARANTINE"
            diagnostics.append(diagnostic)
            continue
        date = entry_time.strftime("%Y-%m-%d")
        if daily_count.get(date, 0) >= int(
            strategy["maximum_trades_per_utc_day"]
        ):
            diagnostic["status"] = "SKIP_DAILY_CAP"
            diagnostics.append(diagnostic)
            continue
        position = int(candidate["entry_position"])
        bar = m5.iloc[position]
        side = str(candidate["side"])
        if side == "LONG":
            entry = (
                _effective_ask(bar, "open", spread_floor)
                + slippage
            )
            stop = entry - risk
            target = entry + target_distance
        else:
            entry = float(bar["bid_open"]) - slippage
            stop = entry + risk
            target = entry - target_distance
        exit_time, exit_price, reason = _walk_exit(
            m5,
            position,
            entry_time + hold,
            side,
            stop,
            target,
            spread_floor,
            slippage,
        )
        pnl = (
            exit_price - entry
            if side == "LONG"
            else entry - exit_price
        )
        result_r = pnl / risk
        records.append(
            {
                "family": FAMILY,
                "regime": "NEUTRAL",
                "side": side,
                "anchor_time_utc": candidate["anchor_time_utc"],
                "signal_time_utc": candidate["signal_time_utc"],
                "state_time_utc": candidate["state_time_utc"],
                "matched_state_time_utc": candidate[
                    "matched_state_time_utc"
                ],
                "entry_time_utc": entry_time,
                "exit_time_utc": exit_time,
                "entry_price": entry,
                "stop_price": stop,
                "target_price": target,
                "exit_price": exit_price,
                "exit_reason": reason,
                "risk_distance": risk,
                "r": result_r,
                "extra_half_pip_stress_r": (
                    result_r - 0.5 * PIP / risk
                ),
                "fixed_0p01_lot_usd": pnl * 1000.0,
                "drive_body_pips": candidate[
                    "drive_body_pips"
                ],
                "drive_range_pips": candidate[
                    "drive_range_pips"
                ],
                "drive_close_location": candidate[
                    "drive_close_location"
                ],
            }
        )
        diagnostic["status"] = "EXECUTED"
        diagnostic["exit_time_utc"] = exit_time
        diagnostic["exit_reason"] = reason
        diagnostics.append(diagnostic)
        open_until = exit_time
        daily_count[date] = daily_count.get(date, 0) + 1
    return pd.DataFrame(records), pd.DataFrame(diagnostics)


def run_census() -> dict[str, Any]:
    cfg = load_config()
    base = load_ensemble_config()
    m5, state, _ = load_inputs(base)
    _, census = build_drive_candidates(
        m5,
        state,
        cfg,
        enforce_frozen_census=False,
    )
    return census


def run_neutral_opening_drive() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    verify_lock()
    cfg = load_config()
    base = load_ensemble_config()
    m5, state, manifests = load_inputs(base)
    candidates, census = build_drive_candidates(
        m5,
        state,
        cfg,
        enforce_frozen_census=True,
    )
    trades, diagnostics = simulate(candidates, m5, cfg)
    summary = summarize(trades, m5, cfg)
    match, matches = oracle_match(trades, cfg)
    prospective_start = pd.Timestamp(
        cfg["prospective"]["start_utc"]
    )
    prospective_candidates = candidates[
        candidates["entry_time_utc"] >= prospective_start
    ]
    result = {
        "campaign_id": cfg["campaign_id"],
        "status": (
            "CAUSAL_RESEARCH_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if summary["admitted"]
            else "REJECTED_NEUTRAL_OPENING_DRIVE_V1"
        ),
        "information_status": cfg["information_status"],
        "source_manifests": manifests,
        "causality": {
            "direction": (
                "Sign of fully completed first 30-minute session bar"
            ),
            "entry": (
                "Next M5 open after the completed observation window"
            ),
            "regime": cfg["neutral_ownership"]["state"],
            "future_information_in_signal_or_execution": False,
            "oracle_usage": "evaluation only after trade ledger",
        },
        "outcome_blind_census": census,
        "strategy": summary,
        "oracle_imitation": match,
        "prospective": {
            "start_utc": cfg["prospective"]["start_utc"],
            "historical_rows_before_start_are_research_only": True,
            "available_candidates_after_start": int(
                prospective_candidates["trade_candidate"].sum()
            ),
            "status": (
                "WAITING_FOR_POST_LOCK_MARKET_DATA"
                if prospective_candidates.empty
                else "POST_LOCK_CANDIDATES_AVAILABLE"
            ),
        },
        "verdict": (
            "The fixed opening-drive rule passed historical gates; "
            "only post-lock rows may confirm it."
            if summary["admitted"]
            else "The fixed opening-drive rule failed its frozen "
            "historical gates and is closed without repair."
        ),
    }
    return result, {
        "CANDIDATES": candidates,
        "EXECUTION_DIAGNOSTICS": diagnostics,
        "TRADES": trades,
        "ORACLE_MATCHES": matches,
    }

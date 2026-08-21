from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import numpy as np

from replay import (
    Candidate,
    CONTRACT_PATH,
    DAY_MS,
    Scenario,
    ScenarioSpec,
    _decode_hour,
    apply_portfolio_protection,
    apply_runtime_risk_mode,
    effective_threshold,
    load_candidates,
    load_json,
    resolve_input,
)


def test_effective_threshold_supports_absolute_only_demo_mode():
    risk = {
        "equity_fraction_limits_enabled": False,
        "floating_drawdown_hard_stop_usd": 449.7675,
        "floating_drawdown_hard_stop_fraction": 0.15,
    }
    assert effective_threshold(
        risk, 987.6623553437713, "floating_drawdown_hard_stop_usd"
    ) == 449.7675


def test_effective_threshold_supports_activation_equity_scaled_mode():
    risk = {
        "equity_fraction_limits_enabled": True,
        "floating_drawdown_hard_stop_usd": 449.7675,
        "floating_drawdown_hard_stop_fraction": 0.15,
    }
    assert np.isclose(
        effective_threshold(
            risk,
            987.6623553437713,
            "floating_drawdown_hard_stop_usd",
        ),
        148.14935330156568,
    )


def test_effective_threshold_supports_mixed_fixed_lot_drawdown_mode():
    risk = {
        "equity_fraction_limits_enabled": True,
        "drawdown_equity_fraction_limits_enabled": False,
        "floating_drawdown_hard_stop_usd": 420.0,
        "floating_drawdown_hard_stop_fraction": 0.25,
        "maximum_account_concurrent_initial_risk_usd": 60.0,
        "maximum_account_concurrent_initial_risk_fraction": 0.06,
    }
    assert effective_threshold(
        risk, 987.6623553437713, "floating_drawdown_hard_stop_usd"
    ) == 420.0
    assert np.isclose(
        effective_threshold(
            risk,
            987.6623553437713,
            "maximum_account_concurrent_initial_risk_usd",
        ),
        59.259741320626276,
    )


def real_inputs():
    contract = load_json(
        CONTRACT_PATH.parent / "SAFETY_REPAIR_REPLAY_CONTRACT.json"
    )
    config = apply_runtime_risk_mode(
        load_json(resolve_input(contract["inputs"]["demo_config"])),
        required_equity_scaling=True,
    )
    return contract, config


def candidate(
    trade_id: str,
    *,
    entry_ms: int,
    exit_ms: int,
    pnl: float = 2.0,
    source_id: str = "R4_CHOP",
    sleeve_type: str = "CORE",
    direction: str = "LONG",
    cooldown: int = 0,
    event_id: str | None = None,
    risk: float = 3.0,
    entry_price: float = 1000.1,
) -> Candidate:
    return Candidate(
        trade_id=trade_id,
        source_id=source_id,
        specialist_id=source_id,
        sleeve_type=sleeve_type,
        entry_ms=entry_ms,
        exit_ms=exit_ms,
        direction=direction,
        risk_usd=risk,
        pnl_usd=pnl,
        entry_price=entry_price,
        exit_price=entry_price + pnl,
        open_cost_usd=0.0,
        maximum_risk_usd=45.0,
        maximum_spread_r=0.15,
        maximum_open_positions=4,
        maximum_entries_per_utc_day=12,
        maximum_entry_gap_minutes=10,
        cooldown_minutes=cooldown,
        event_id=event_id,
    )


def scenario(
    rows: list[Candidate],
    *,
    guardian: bool = False,
    activation: float = 3000.0,
    rebaseline_days: int | None = None,
    guardian_exit_attribution: str = "DEPLOYED_MAGIC_FILTER",
    protection: bool = False,
    guardian_close_positions: bool | None = None,
) -> Scenario:
    contract, config = real_inputs()
    if guardian_close_positions is not None:
        contract["guardian"]["daily_loss_stop_close_positions"] = (
            guardian_close_positions
        )
    if protection:
        contract["inputs"]["portfolio_protection_overlay"] = (
            "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/"
            "config/v60_drawdown_protection_v1_overlay.json"
        )
        config = apply_portfolio_protection(contract, config)
    return Scenario(
        ScenarioSpec(
            scenario_id="test",
            starting_equity_usd=activation,
            activation_equity_usd=activation,
            rebaseline_days=rebaseline_days,
            guardian_enabled=guardian,
            guardian_exit_attribution=guardian_exit_attribution,
        ),
        config,
        contract,
        rows,
    )


def test_locked_population_and_r1_risk_reconstruction():
    contract, config = real_inputs()
    rows, audit = load_candidates(contract, config)
    assert len(rows) == 1703
    assert audit["r1_native_risk_rows"] == 444
    box = [row for row in rows if row.source_id == "R1_BOX"]
    pullback = [row for row in rows if row.source_id == "R1_PULLBACK"]
    assert len(box) == 31
    assert len(pullback) == 413
    assert sum(row.risk_usd > 45.0 for row in box) == 12
    assert not any(row.risk_usd > 45.0 for row in pullback)


def test_vector_decoder_matches_source_rounding():
    root = Path(
        "D:/AlgoTradingData/C_DRIVE/DukascopyTickDataFoundationV1/raw/"
        "XAUUSD/year=2021/month=01"
    )
    path = root / "2021010400.json"
    raw = path.read_bytes()
    payload = json.loads(raw)
    times, bids, asks = _decode_hour(raw)
    timestamp = int(payload["timestamp"])
    bid = float(payload["bid"])
    ask = float(payload["ask"])
    for index in range(len(payload["times"])):
        timestamp += int(payload["times"][index])
        bid = np.floor(
            (bid + float(payload["bids"][index]) * payload["multiplier"])
            * 1000.0
            + 0.5
            + 1e-9
        ) / 1000.0
        ask = np.floor(
            (ask + float(payload["asks"][index]) * payload["multiplier"])
            * 1000.0
            + 0.5
            + 1e-9
        ) / 1000.0
        if index in {0, 1, 50, 500, len(times) - 1}:
            assert times[index] == timestamp
            assert bids[index] == bid
            assert asks[index] == ask


def test_exit_settles_before_same_cycle_entry():
    first = candidate("first", entry_ms=0, exit_ms=5000, pnl=-10.0)
    second = replace(
        candidate("second", entry_ms=5000, exit_ms=10000),
        maximum_open_positions=1,
    )
    replay = scenario([first, second])
    replay.process_cycle(0, 0, 1000.0, 1000.1)
    replay.process_cycle(5000, 5000, 1000.0, 1000.1)
    assert "first" not in replay.positions
    assert "second" in replay.positions
    assert replay.account_closed_pnl == -10.0
    assert replay.v60_closed_pnl == -10.0


def test_v57_cooldown_uses_only_accepted_loss():
    first = candidate(
        "loss",
        entry_ms=0,
        exit_ms=5000,
        pnl=-3.0,
        source_id="V57_BREAK_SWING_H4ADX_HIGH",
        sleeve_type="ADDON",
        cooldown=120,
        event_id="one",
    )
    second = candidate(
        "next",
        entry_ms=5000,
        exit_ms=10000,
        source_id="V57_BREAK_SWING_H4ADX_HIGH",
        sleeve_type="ADDON",
        cooldown=120,
        event_id="two",
    )
    replay = scenario([first, second])
    replay.process_cycle(0, 0, 1000.0, 1000.1)
    replay.process_cycle(5000, 5000, 1000.0, 1000.1)
    assert replay.rejections["SAME_DIRECTION_POST_LOSS_COOLDOWN"] == 1
    assert "next" not in replay.positions


def test_guardian_daily_loss_locks_and_closes():
    trade = candidate(
        "guardian-loss",
        entry_ms=0,
        exit_ms=20000,
        entry_price=1000.1,
    )
    replay = scenario([trade], guardian=True)
    replay.process_cycle(0, 0, 1000.0, 1000.1)
    replay.process_cycle(5000, 5000, 970.0, 970.1)
    assert replay.guardian.locked
    assert replay.guardian_locks == 1
    assert not replay.positions
    assert replay.account_closed_pnl < -29.0
    assert replay.v60_closed_pnl == 0.0


def test_position_attribution_counterfactual_tracks_guardian_close():
    trade = candidate(
        "guardian-loss-attributed",
        entry_ms=0,
        exit_ms=20000,
        entry_price=1000.1,
    )
    replay = scenario(
        [trade],
        guardian=True,
        guardian_exit_attribution="POSITION_ORIGIN",
    )
    replay.process_cycle(0, 0, 1000.0, 1000.1)
    replay.process_cycle(5000, 5000, 970.0, 970.1)
    assert replay.guardian.locked
    assert replay.v60_closed_pnl == replay.account_closed_pnl


def test_guardian_daily_loss_halt_only_preserves_open_position():
    trade = candidate(
        "guardian-halt-only",
        entry_ms=0,
        exit_ms=20000,
        pnl=2.0,
        entry_price=1000.1,
    )
    replay = scenario(
        [trade],
        guardian=True,
        guardian_exit_attribution="POSITION_ORIGIN",
        guardian_close_positions=False,
    )
    replay.process_cycle(0, 0, 1000.0, 1000.1)
    replay.process_cycle(5000, 5000, 970.0, 970.1)

    assert replay.guardian.locked
    assert "guardian-halt-only" in replay.positions
    assert replay.account_closed_pnl == 0.0
    replay.process_cycle(20000, 20000, 1002.0, 1002.1)
    assert not replay.positions
    assert replay.account_closed_pnl == 2.0


def test_execution_quarantine_rejects_v8_but_keeps_candidate_observable():
    trade = candidate(
        "v8-quarantine",
        entry_ms=0,
        exit_ms=5000,
        source_id="V8_RETEST_HEALTH",
        sleeve_type="ADDON",
        event_id="v8",
    )
    replay = scenario([trade])

    replay.process_cycle(0, 0, 1000.0, 1000.1)

    assert "v8-quarantine" not in replay.positions
    assert replay.rejections["SOURCE_EXECUTION_QUARANTINED"] == 1


def test_floating_hard_stop_closes_position():
    trade = candidate(
        "floating-stop",
        entry_ms=0,
        exit_ms=20000,
        entry_price=1000.1,
    )
    replay = scenario([trade], activation=1000.0)
    replay.process_cycle(0, 0, 1000.0, 1000.1)
    replay.process_cycle(5000, 5000, 500.0, 500.1)
    assert replay.first_hard_stop_ms == 5000
    assert not replay.positions
    assert replay.emergency_closes == 1


def test_closed_drawdown_recovery_accepts_one_bounded_confirmed_core():
    trade = candidate(
        "recovery-core",
        entry_ms=0,
        exit_ms=5000,
        source_id="R1_PULLBACK",
        risk=20.0,
        pnl=30.0,
    )
    replay = scenario([trade], activation=1000.0)
    replay.account_closed_pnl = -230.0
    replay.v60_closed_pnl = -230.0

    replay.process_cycle(0, 0, 1000.0, 1000.1)

    assert replay.drawdown_suspended
    assert replay.recovery_entries == 1
    assert "recovery-core" in replay.positions


def test_closed_drawdown_recovery_rejects_addons():
    trade = candidate(
        "recovery-addon",
        entry_ms=0,
        exit_ms=5000,
        source_id="V7_SWING_HEALTH",
        sleeve_type="ADDON",
        risk=20.0,
    )
    replay = scenario([trade], activation=1000.0)
    replay.account_closed_pnl = -230.0
    replay.v60_closed_pnl = -230.0

    replay.process_cycle(0, 0, 1000.0, 1000.1)

    assert replay.drawdown_suspended
    assert replay.recovery_entries == 0
    assert replay.rejections["DRAWDOWN_RECOVERY_CORE_ONLY"] == 1


def test_rebaseline_does_not_forgive_peak_equity():
    replay = scenario([], activation=1000.0, rebaseline_days=14)
    replay.account_closed_pnl = -100.0
    replay.v60_closed_pnl = -100.0
    replay.policy_peak_closed = 0.0
    replay.lifetime_peak_closed = 0.0
    replay.peak_equity = 1200.0
    replay.drawdown_suspended = True
    replay.flat_since_ms = 0
    replay._maybe_rebaseline(14 * DAY_MS)
    assert replay.policy_peak_closed == -100.0
    assert replay.peak_equity == 1200.0
    assert not replay.drawdown_suspended
    assert replay.rebaselines == 1


def test_profit_protection_closes_after_locked_giveback():
    trade = candidate(
        "protected",
        entry_ms=0,
        exit_ms=30000,
        risk=10.0,
        entry_price=1000.1,
    )
    replay = scenario([trade], protection=True)

    replay.process_cycle(0, 0, 1000.0, 1000.1)
    replay.process_cycle(5000, 5000, 1015.2, 1015.3)
    replay.process_cycle(10000, 10000, 1005.0, 1005.1)

    assert replay.profit_protection_arms == 1
    assert replay.profit_giveback_closes == 1
    assert not replay.positions
    assert replay.close_pnls[0] > 4.0


def test_protection_deduplicates_same_direction_r4_v25():
    r4 = candidate(
        "r4",
        entry_ms=0,
        exit_ms=20000,
        source_id="R4_CHOP",
        direction="LONG",
    )
    v25 = candidate(
        "v25",
        entry_ms=5000,
        exit_ms=20000,
        source_id="V25_CHOP",
        sleeve_type="ADDON",
        direction="LONG",
        event_id="v25",
    )
    replay = scenario([r4, v25], protection=True)

    replay.process_cycle(0, 0, 1000.0, 1000.1)
    replay.process_cycle(5000, 5000, 1000.0, 1000.1)

    assert "r4" in replay.positions
    assert "v25" not in replay.positions
    assert replay.rejections["SAME_DIRECTION_PROTECTION_FAMILY"] == 1

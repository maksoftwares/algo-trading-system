from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from evaluator import (  # noqa: E402
    JsonlSnapshot,
    TRADE_COLUMNS,
    StageNotReady,
    _core_trade,
    _require_stage_resolutions,
    _verify_consumed_prefix,
    evaluate_gates,
    floating_equity_metrics,
    load_config,
    normalize_satellite_trades,
    route_composite_rows,
    sha256_bytes,
)


def test_composite_router_uses_entry_then_attempt_and_blocks_overlap() -> None:
    rows = [
        {
            "candidate_id": "late-priority",
            "origin_attempt": 11266,
            "entry_time_utc": "2026-07-20T10:00:00Z",
            "exit_time_utc": "2026-07-20T11:00:00Z",
        },
        {
            "candidate_id": "first-priority",
            "origin_attempt": 11142,
            "entry_time_utc": "2026-07-20T10:00:00Z",
            "exit_time_utc": "2026-07-20T10:30:00Z",
        },
        {
            "candidate_id": "overlap",
            "origin_attempt": 11142,
            "entry_time_utc": "2026-07-20T10:15:00Z",
            "exit_time_utc": "2026-07-20T10:45:00Z",
        },
        {
            "candidate_id": "after",
            "origin_attempt": 11266,
            "entry_time_utc": "2026-07-20T10:30:00Z",
            "exit_time_utc": "2026-07-20T11:30:00Z",
        },
    ]
    selected = route_composite_rows(rows)
    assert [row["candidate_id"] for row in selected] == ["first-priority", "after"]


def test_stage_remains_sealed_until_every_candidate_is_resolved() -> None:
    candidates = [
        {"candidate_id": "a", "signal_time_utc": "2026-07-20T01:00:00Z"},
        {"candidate_id": "b", "signal_time_utc": "2026-07-20T02:00:00Z"},
    ]
    resolutions = [{"candidate_id": "a"}]
    with pytest.raises(StageNotReady, match="1 unresolved"):
        _require_stage_resolutions(
            candidates,
            resolutions,
            {"2026-07-20"},
            "signal_time_utc",
            "test",
        )


def test_consumed_prefix_allows_append_but_rejects_mutation(tmp_path: Path) -> None:
    consumed = b'{"candidate_id":"a"}\n'
    appended = consumed + b'{"candidate_id":"b"}\n'
    state_path = tmp_path / "state.json"
    state_path.write_text(
        '{"contract_sha256":"contract","source_prefix_bytes":'
        f'{len(consumed)},"source_prefix_sha256":"{sha256_bytes(consumed)}"}}',
        encoding="utf-8",
    )
    snapshot = JsonlSnapshot([], appended, len(appended), sha256_bytes(appended))
    _verify_consumed_prefix(
        snapshot,
        state_path,
        bytes_field="source_prefix_bytes",
        sha_field="source_prefix_sha256",
        expected_contract="contract",
        label="test",
    )
    mutated = b'{"candidate_id":"x"}\n' + appended[len(consumed) :]
    with pytest.raises(ValueError, match="mutated"):
        _verify_consumed_prefix(
            JsonlSnapshot([], mutated, len(mutated), sha256_bytes(mutated)),
            state_path,
            bytes_field="source_prefix_bytes",
            sha_field="source_prefix_sha256",
            expected_contract="contract",
            label="test",
        )


def test_r5_weighted_economics_are_not_misreported_as_minimum_lot() -> None:
    config = load_config()
    candidate = {
        "candidate_id": "r5",
        "origin_attempt": 24877,
        "direction_sign": 1,
        "scheduled_entry_time_utc": "2026-07-20T01:00:00Z",
    }
    resolution = {
        "entry_time_utc": "2026-07-20T01:00:00Z",
        "exit_time_utc": "2026-07-20T02:00:00Z",
        "entry_price": 4000.0,
        "exit_price": 4020.0,
        "risk_usd": 10.0,
        "gross_r": 2.0,
        "stress_net_r": 1.8,
    }
    trade = _core_trade(
        candidate,
        resolution,
        specialist_id="R5_TRANSITION",
        source_lane="V38_V39_R5",
        stage_time_field="scheduled_entry_time_utc",
        config=config,
        risk_weight=0.125,
    )
    assert trade["stress_pnl_dollars"] == pytest.approx(2.25)
    assert trade["base_pnl_dollars"] == pytest.approx(2.3125)
    assert trade["effective_lot"] == pytest.approx(0.00125)
    assert trade["broker_lot_exact"] is False


def _write_ticks(
    path: Path, timestamps: list[int], bids: list[float], asks: list[float]
) -> None:
    frame = pd.DataFrame(
        {
            "schema_version": "xau_prospective_tick_v1",
            "timestamp_utc": [
                pd.Timestamp(value, unit="ms", tz="UTC").strftime(
                    "%Y.%m.%d %H:%M:%S.%f"
                )[:-3]
                + "Z"
                for value in timestamps
            ],
            "tick_time_msc": timestamps,
            "account_login": 1033669,
            "account_server": "Capital.ComMena-Demo",
            "symbol": "XAUUSD",
            "bid": bids,
            "ask": asks,
            "spread_price": [ask - bid for bid, ask in zip(bids, asks, strict=True)],
            "dry_run": True,
            "trade_permission": False,
            "broker_action_allowed": False,
            "python_execution_authorized": False,
        }
    )
    frame.to_csv(path, index=False)


def _trade(
    trade_id: str,
    sign: int,
    entry_ms: int,
    exit_ms: int,
    entry_price: float,
    base_pnl: float,
    stress_pnl: float,
) -> dict[str, object]:
    return {
        "trade_id": trade_id,
        "stage_date_utc": "2026-07-20",
        "specialist_id": "TEST",
        "source_lane": "TEST",
        "candidate_id": trade_id,
        "origin_attempt": 1,
        "direction": "LONG" if sign > 0 else "SHORT",
        "direction_sign": sign,
        "entry_time_utc": pd.Timestamp(entry_ms, unit="ms", tz="UTC").isoformat(),
        "exit_time_utc": pd.Timestamp(exit_ms, unit="ms", tz="UTC").isoformat(),
        "entry_time_msc": entry_ms,
        "exit_time_msc": exit_ms,
        "entry_price": entry_price,
        "exit_price": entry_price,
        "dollars_per_price_unit": 1.0,
        "reference_lot": 0.01,
        "risk_weight": 1.0,
        "effective_lot": 0.01,
        "base_cost_dollars": 0.1,
        "stress_cost_dollars": 0.2,
        "base_pnl_dollars": base_pnl,
        "stress_pnl_dollars": stress_pnl,
        "broker_lot_exact": True,
    }


def test_floating_equity_marks_overlap_on_every_tick(tmp_path: Path) -> None:
    base = int(pd.Timestamp("2026-07-20T00:00:00Z").value // 1_000_000)
    timestamps = [base + value for value in (1000, 2000, 3000, 4000, 5000)]
    tick_path = tmp_path / "ticks.csv"
    _write_ticks(
        tick_path,
        timestamps,
        bids=[99.0, 101.0, 98.0, 100.0, 101.0],
        asks=[100.0, 102.0, 99.0, 101.0, 102.0],
    )
    trades = pd.DataFrame(
        [
            _trade("long", 1, timestamps[0], timestamps[3], 100.0, 0.5, 0.4),
            _trade("short", -1, timestamps[1], timestamps[4], 102.0, 1.0, 0.8),
        ],
        columns=TRADE_COLUMNS,
    )
    metrics = floating_equity_metrics(trades, [tick_path], load_config())
    assert metrics["marked_tick_rows"] == 5
    assert metrics["maximum_concurrent_positions"] == 2
    assert metrics["maximum_gross_lots"] == pytest.approx(0.02)
    assert metrics["maximum_absolute_directional_lots"] == pytest.approx(0.01)
    assert metrics["stress_floating_drawdown_dollars"] > 0.0


def test_satellite_normalization_uses_observed_bid_ask_and_locked_pnl() -> None:
    raw = pd.DataFrame(
        [
            {
                "source_lane": "V24_1",
                "date_utc": "2026-07-20",
                "candidate_time_msc": 1000,
                "side": "LONG",
                "entry_time_msc": 1001,
                "exit_time_msc": 2001,
                "entry_bid": 99.0,
                "entry_ask": 100.0,
                "exit_bid": 101.0,
                "exit_ask": 102.0,
                "observed_bidask_move": 1.0,
                "base_pnl_dollars": 0.9,
                "stress_pnl_dollars": 0.7,
                "reference_lot": 0.01,
            }
        ]
    )
    trade = normalize_satellite_trades(raw, load_config()).iloc[0]
    assert trade["entry_price"] == 100.0
    assert trade["base_cost_dollars"] == pytest.approx(0.1)
    assert trade["stress_cost_dollars"] == pytest.approx(0.3)


def test_research_can_pass_while_current_account_remains_not_ready() -> None:
    config = load_config()
    metrics = {
        "trades_per_weekday": 3.2,
        "base_net_dollars": 100.0,
        "stress_net_dollars": 80.0,
        "base_profit_factor": 1.5,
        "stress_profit_factor": 1.3,
        "profitable_day_share": 0.6,
        "first_half_base_profit_factor": 1.2,
        "second_half_base_profit_factor": 1.1,
        "base_closed_drawdown_dollars": 100.0,
        "stress_floating_drawdown_dollars": 200.0,
        "worst_daily_stress_loss_dollars": 50.0,
        "maximum_margin_dollars": 300.0,
        "maximum_concurrent_positions": 4,
        "maximum_absolute_directional_lots": 0.04,
        "all_trade_lots_broker_exact": True,
    }
    research, account, readiness = evaluate_gates(
        metrics, v27_gate_passed=True, config=config
    )
    assert all(research.values())
    assert account["historical_core_drawdown_fits"] is False
    assert account["r5_broker_sizing_mapping_preregistered"] is False
    assert readiness["research_gate_passed"] is True
    assert readiness["account_gate_passed"] is False
    assert readiness["minimum_equity_required_dollars"] == pytest.approx(11555.8)

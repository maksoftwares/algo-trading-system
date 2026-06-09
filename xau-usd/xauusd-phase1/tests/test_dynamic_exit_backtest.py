from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "backtest_dynamic_exit_variants.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("dynamic_exit_backtest", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _trade(direction: str = "LONG"):
    mod = _load_module()
    if direction == "LONG":
        return mod.ReplayTrade(
            trade_id="T1",
            candidate="breakout_retest",
            symbol="XAUUSD",
            direction="LONG",
            entry_time=datetime(2026, 6, 1, 10, 0),
            entry_price=100.0,
            initial_sl=90.0,
            initial_tp=115.0,
        )
    return mod.ReplayTrade(
        trade_id="T1",
        candidate="breakout_retest",
        symbol="XAUUSD",
        direction="SHORT",
        entry_time=datetime(2026, 6, 1, 10, 0),
        entry_price=100.0,
        initial_sl=110.0,
        initial_tp=85.0,
    )


def _bar(minutes: int, high: float, low: float, close: float, atr14: float | None = 2.0):
    mod = _load_module()
    return mod.Bar(
        time=datetime(2026, 6, 1, 10, 0) + timedelta(minutes=minutes),
        open=100.0,
        high=high,
        low=low,
        close=close,
        atr14=atr14,
    )


def test_variant_a_hits_one_r_then_be_returns_half_r_before_cost():
    mod = _load_module()
    replay = mod.replay_dynamic_exits(_trade(), [_bar(0, 111, 101, 110), _bar(5, 110, 100, 100)])

    assert replay.partial_be.final_r == 0.5
    assert replay.partial_be.exit_reason == "PARTIAL_BE_RUNNER_BE"
    assert replay.partial_be.partial_triggered is True


def test_variant_a_hits_one_r_then_tp_returns_one_point_two_five_r_before_cost():
    mod = _load_module()
    replay = mod.replay_dynamic_exits(_trade(), [_bar(0, 111, 101, 110), _bar(5, 115, 105, 115)])

    assert replay.partial_be.final_r == 1.25
    assert replay.partial_be.exit_reason == "PARTIAL_BE_RUNNER_TP"


def test_variant_b_hits_one_r_then_be_returns_zero_r():
    mod = _load_module()
    replay = mod.replay_dynamic_exits(_trade(), [_bar(0, 111, 101, 110), _bar(5, 110, 100, 100)])

    assert replay.be_only.final_r == 0.0
    assert replay.be_only.exit_reason == "BE"
    assert replay.be_only.be_triggered is True


def test_variant_b_hits_one_r_then_tp_returns_one_point_five_r():
    mod = _load_module()
    replay = mod.replay_dynamic_exits(_trade(), [_bar(0, 111, 101, 110), _bar(5, 115, 105, 115)])

    assert replay.be_only.final_r == 1.5
    assert replay.be_only.exit_reason == "TP"


def test_variant_c_does_not_trail_before_one_r():
    mod = _load_module()
    replay = mod.replay_dynamic_exits(_trade(), [_bar(0, 109, 95, 101), _bar(5, 108, 96, 102)])

    assert replay.atr_trail.trail_triggered is False
    assert replay.atr_trail.exit_reason == "TIME_OR_DATA_END"


def test_variant_c_trail_never_moves_farther_away():
    mod = _load_module()
    replay = mod.replay_dynamic_exits(
        _trade(),
        [
            _bar(0, 111, 101, 110, atr14=2.0),
            _bar(5, 114, 110, 113, atr14=2.0),
            _bar(10, 113, 110, 111, atr14=2.0),
        ],
    )

    assert replay.atr_trail.trail_triggered is True
    assert replay.atr_trail.exit_reason in {"ATR_TRAIL", "TIME_OR_DATA_END"}


def test_early_loser_before_one_r_remains_minus_one_for_all_variants():
    mod = _load_module()
    replay = mod.replay_dynamic_exits(_trade(), [_bar(0, 105, 90, 90)])

    assert replay.control.final_r == -1.0
    assert replay.partial_be.final_r == -1.0
    assert replay.be_only.final_r == -1.0
    assert replay.atr_trail.final_r == -1.0


def test_ambiguous_same_bar_uses_adverse_first():
    mod = _load_module()
    replay = mod.replay_dynamic_exits(_trade(), [_bar(0, 116, 89, 100)])

    assert replay.control.final_r == -1.0
    assert replay.partial_be.final_r == -1.0
    assert replay.be_only.final_r == -1.0
    assert replay.control.intrabar_ambiguous is True


def test_partial_extra_cost_is_included_in_variant_a_net_r():
    mod = _load_module()
    replay = mod.replay_dynamic_exits(
        _trade(),
        [_bar(0, 111, 101, 110), _bar(5, 115, 105, 115)],
        partial_extra_cost_r=0.1,
    )

    assert replay.partial_be.final_r == 1.15
    assert replay.partial_be.extra_cost_r == 0.1


def test_missing_candle_path_blocks_replay_instead_of_guessing():
    mod = _load_module()
    replay = mod.replay_dynamic_exits(_trade(), None)

    assert replay.replay_status == "BLOCKED_NO_PRICE_PATH"
    assert replay.mfe_r is None
    assert replay.partial_be.final_r is None


def test_generate_reports_writes_only_offline_report_paths(tmp_path: Path):
    mod = _load_module()
    root = tmp_path / "xauusd-phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    (reports / "PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv").write_text(
        "\n".join(
            [
                "entry_time,exit_time,candidate,status,symbol,direction,volume,entry_price,exit_price,sl,tp,state,profit_aed,position_ticket,duplicate_role,is_duplicate",
                "2026-06-02 10:00:00,2026-06-02 10:30:00,breakout_retest,ACCEPTED,XAUUSD,BUY,0.01,100,90,95,107.5,CLOSED,-18,T1,kept,false",
            ]
        ),
        encoding="utf-8",
    )

    output = mod.generate_dynamic_exit_backtest(root)

    assert output.status == "BLOCKED_NO_PRICE_PATH"
    assert output.report_path.exists()
    for path in root.rglob("*"):
        assert "MetaQuotes" not in str(path)
        assert "Terminal" not in str(path)
        assert path.suffix.lower() not in {".mq5", ".mqh", ".set"}


def test_bounds_show_how_many_losses_must_be_saved():
    mod = _load_module()
    rows = [
        {
            "entry_price": "100",
            "sl": "90",
            "tp": "115",
            "exit_price": "115",
            "direction": "BUY",
        },
        {
            "entry_price": "100",
            "sl": "90",
            "tp": "115",
            "exit_price": "90",
            "direction": "BUY",
        },
    ]

    bounds = mod.variant_bounds_for_view("test", rows)
    partial = next(row for row in bounds if row["variant"].startswith("DYNEXIT_PartialBE"))
    be_only = next(row for row in bounds if row["variant"].startswith("DYNEXIT_BEOnly"))

    assert partial["variant_min_net_R_before_extra_cost"] == 0.25
    assert partial["variant_max_net_R_before_extra_cost"] == 1.75
    assert partial["protected_losses_needed_to_beat_control"] == 1
    assert be_only["variant_min_net_R_before_extra_cost"] == 0.5
    assert be_only["variant_max_net_R_before_extra_cost"] == 1.5
    assert be_only["protected_losses_needed_to_beat_control"] == 0


def test_script_does_not_import_or_edit_mql_files():
    text = SCRIPT.read_text(encoding="utf-8")

    assert "import MetaTrader" not in text
    assert 'Path("mt5")' not in text
    assert "rglob(\"*.mq" not in text
    assert "write_text(\".mq" not in text


def test_exact_logged_path_saves_loser_that_reached_one_r():
    mod = _load_module()
    row = {
        "position_ticket": "T100",
        "candidate": "breakout_retest",
        "entry_time": "2026-06-02 10:00:00",
        "exit_time": "2026-06-02 10:20:00",
        "direction": "BUY",
        "entry_price": "100",
        "exit_price": "90",
        "sl": "90",
        "tp": "115",
        "profit_aed": "-20",
        "is_duplicate": "false",
    }
    snapshots = {
        "breakout_retest": [
            mod.SignalSnapshot(datetime(2026, 6, 2, 10, 5), "breakout_retest", 111.0, 111.5, "test.csv"),
            mod.SignalSnapshot(datetime(2026, 6, 2, 10, 15), "breakout_retest", 90.0, 90.5, "test.csv"),
        ]
    }

    replay = mod.exact_logged_path_replay_row(row, snapshots)

    assert replay["partial_be_r"] == 0.5
    assert replay["partial_be_aed"] == 10.0
    assert replay["be_only_r"] == 0.0
    assert replay["be_only_aed"] == 0.0
    assert replay["be_only_status"] == "LOSS_REACHED_1R_THEN_BE_ONLY_SAVES_TO_0R"


def test_exact_logged_path_partial_drag_on_winner():
    mod = _load_module()
    row = {
        "position_ticket": "T101",
        "candidate": "breakout_retest",
        "entry_time": "2026-06-02 10:00:00",
        "exit_time": "2026-06-02 10:20:00",
        "direction": "BUY",
        "entry_price": "100",
        "exit_price": "115",
        "sl": "90",
        "tp": "115",
        "profit_aed": "30",
        "is_duplicate": "false",
    }

    replay = mod.exact_logged_path_replay_row(row, {})

    assert replay["partial_be_r"] == 1.25
    assert replay["partial_be_aed"] == 25.0
    assert replay["be_only_r"] == 1.5
    assert replay["be_only_aed"] == 30.0

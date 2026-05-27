from __future__ import annotations

import importlib.util
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_gap_classifier_marks_normal_m5_cadence():
    module = _load_module()

    classification = module.classify_gap(
        datetime(2026, 5, 26, 12, 0),
        datetime(2026, 5, 26, 12, 5),
        _row("2026.05.26 12:00:00"),
        _row("2026.05.26 12:05:00"),
    )

    assert classification.reason == "NORMAL_M5_CADENCE"
    assert classification.resets_active_market_streak is False
    assert classification.counts_as_runtime_warning is False


def test_gap_classifier_pauses_for_configured_daily_broker_break():
    module = _load_module()

    classification = module.classify_gap(
        datetime(2026, 5, 26, 20, 55),
        datetime(2026, 5, 26, 22, 0),
        _row("2026.05.26 20:55:00", session="ROLLOVER", execution_state="MARKET_CLOSED"),
        _row("2026.05.26 22:00:00", session="NEW_YORK"),
    )

    assert classification.reason == "EXPECTED_DAILY_BROKER_BREAK"
    assert classification.is_expected_pause is True
    assert classification.resets_active_market_streak is False
    assert classification.counts_as_runtime_warning is False


def test_gap_classifier_resets_on_unexpected_active_market_gap():
    module = _load_module()

    classification = module.classify_gap(
        datetime(2026, 5, 26, 12, 0),
        datetime(2026, 5, 26, 13, 5),
        _row("2026.05.26 12:00:00"),
        _row("2026.05.26 13:05:00"),
    )

    assert classification.reason == "UNEXPECTED_BAR_GAP"
    assert classification.resets_active_market_streak is True
    assert classification.counts_as_runtime_warning is True


def test_gap_classifier_pauses_for_weekend_break():
    module = _load_module()

    classification = module.classify_gap(
        datetime(2026, 5, 22, 20, 55),
        datetime(2026, 5, 25, 0, 5),
        _row("2026.05.22 20:55:00"),
        _row("2026.05.25 00:05:00", session="ASIA"),
    )

    assert classification.reason == "EXPECTED_WEEKEND_BREAK"
    assert classification.is_expected_pause is True
    assert classification.counts_as_runtime_warning is False


def test_gap_classifier_pauses_for_rollover_gap():
    module = _load_module()

    classification = module.classify_gap(
        datetime(2026, 5, 26, 21, 55),
        datetime(2026, 5, 26, 22, 20),
        _row("2026.05.26 21:55:00"),
        _row("2026.05.26 22:20:00", session="ROLLOVER", execution_state="MARKET_CLOSED"),
    )

    assert classification.reason in {"EXPECTED_DAILY_BROKER_BREAK", "EXPECTED_ROLLOVER_BREAK"}
    assert classification.is_expected_pause is True


def test_active_market_row_rejects_unsafe_states():
    module = _load_module()

    assert module.is_active_market_row(_row("2026.05.26 12:00:00")) is True
    assert module.is_active_market_row(_row("2026.05.26 12:00:00", dry_run="false")) is False
    assert module.is_active_market_row(_row("2026.05.26 12:00:00", trade_permission="true")) is False
    assert module.is_active_market_row(_row("2026.05.26 12:00:00", server_time_status="CLOCK_DRIFT")) is False
    assert module.is_active_market_row(_row("2026.05.26 12:00:00", execution_state="STALE_TICK")) is False
    assert module.is_active_market_row(_row("2026.05.26 12:00:00", execution_state="MARKET_CLOSED")) is False


def test_expected_pause_row_requires_real_weekend_timestamp():
    module = _load_module()

    assert module.is_expected_pause_row(_row("2026.05.23 12:00:00", session="WEEKEND")) is True
    assert module.is_expected_pause_row(_row("2026.05.21 12:00:00", session="WEEKEND")) is False


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "phase1_gap_classifier.py"
    spec = importlib.util.spec_from_file_location("phase1_gap_classifier", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["phase1_gap_classifier"] = module
    spec.loader.exec_module(module)
    return module


def _row(
    timestamp: str,
    session: str = "LONDON",
    execution_state: str = "EXECUTION_OK",
    dry_run: str = "true",
    trade_permission: str = "false",
    server_time_status: str = "CLOCK_OK",
) -> dict[str, str]:
    return {
        "timestamp_broker": timestamp,
        "bar_time": timestamp,
        "lifecycle_state": "DRY_RUN",
        "session": session,
        "execution_state": execution_state,
        "dry_run": dry_run,
        "trade_permission": trade_permission,
        "server_time_status": server_time_status,
        "magic_namespace_ok": "true",
    }

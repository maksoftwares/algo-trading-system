from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_session_extreme_forensics_scores_kept_rows_and_clones(tmp_path: Path):
    module = _load_module()
    actual_trades = tmp_path / "outputs" / "reports" / "PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv"
    impulse_rows = tmp_path / "outputs" / "reports" / "PHASE2_IMPULSE_VETO_SHADOW_ROWS.csv"
    bars_dir = tmp_path / "outputs" / "reports" / "m5_replay_bars"
    output_doc = tmp_path / "docs" / "SESSION_EXTREME_ENTRY_FORENSICS_2026_06_13.md"
    output_json = tmp_path / "outputs" / "reports" / "SESSION_EXTREME_ENTRY_FORENSICS_2026_06_13.json"
    _write_actual_trades(actual_trades)
    _write_impulse_rows(impulse_rows)
    _write_m5_bars(bars_dir)

    output = module.generate_session_extreme_entry_forensics(
        tmp_path,
        actual_trades_csv=actual_trades,
        impulse_rows_csv=impulse_rows,
        bars_dir=bars_dir,
        output_doc=output_doc,
        output_json=output_json,
    )

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    summary = payload["summaries"]["session_extreme_exact_duplicate_hidden"]
    clone_summary = payload["summaries"]["same_duplicate_key_clones"]
    markdown = output.markdown_path.read_text(encoding="utf-8")

    assert output.status == "FORENSICS_READY"
    assert output.exact_duplicate_hidden_rows == 3
    assert output.clone_rows == 1
    assert summary["closed"] == 3
    assert summary["closed_pnl_aed"] == -5.0
    assert clone_summary["closed"] == 1
    assert payload["breakdowns"]["session_extreme_level_type"]
    assert "session_high_retest" in markdown
    assert "Magic band 933200-933299 remains reserved but unused" in markdown


def test_session_extreme_forensics_has_no_runtime_mt5_calls():
    text = (ROOT / "scripts" / "generate_session_extreme_entry_forensics.py").read_text(encoding="utf-8")
    for forbidden in ("MetaTrader5", "mt5.initialize", "OrderSend", "PositionClose"):
        assert forbidden not in text


def _write_actual_trades(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        _trade("2026-06-08 14:00:00", "session_extreme_retest_v0", "XAUUSD", "BUY", 10.0, "1", "k1"),
        _trade("2026-06-08 14:05:00", "session_extreme_retest_v0", "XAUUSD", "BUY", -20.0, "2", "k2"),
        _trade("2026-06-08 15:00:00", "session_extreme_retest_v0", "XAUUSD", "SELL", 5.0, "3", "k3"),
        _trade(
            "2026-06-08 14:05:00",
            "round_number_retest_v0",
            "XAUUSD",
            "BUY",
            -20.0,
            "4",
            "k2",
            duplicate=True,
        ),
        _trade(
            "2026-06-08 16:00:00",
            "session_extreme_retest_v0",
            "XAUUSD",
            "SELL",
            -5.0,
            "5",
            "k4",
            duplicate=True,
        ),
    ]
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_impulse_rows(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "position_ticket",
        "impulse_status",
        "ret12_atr",
        "atr14_m5",
        "impulse_alignment",
        "impulse_bucket",
        "lt_neg_1_5_shadow_action",
    ]
    rows = [
        {
            "position_ticket": str(ticket),
            "impulse_status": "RESOLVED",
            "ret12_atr": "1.0",
            "atr14_m5": "2.0",
            "impulse_alignment": "1.0",
            "impulse_bucket": "aligned_0_to_1_5",
            "lt_neg_1_5_shadow_action": "KEEP",
        }
        for ticket in range(1, 6)
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_m5_bars(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "bar_start_utc": "2026-06-08 00:00:00",
            "bar_end_utc": "2026-06-08 00:05:00",
            "open": "100.0",
            "symbol": "XAUUSD",
            "timeframe": "M5",
        },
        {
            "bar_start_utc": "2026-06-08 07:00:00",
            "bar_end_utc": "2026-06-08 07:05:00",
            "open": "101.0",
            "symbol": "XAUUSD",
            "timeframe": "M5",
        },
    ]
    with (path / "XAUUSD_M5_20260601_to_latest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _trade(
    entry_time: str,
    candidate: str,
    symbol: str,
    direction: str,
    pnl: float,
    ticket: str,
    duplicate_key: str,
    *,
    duplicate: bool = False,
) -> dict[str, str]:
    return {
        "entry_time": entry_time,
        "exit_time": entry_time,
        "candidate": candidate,
        "status": "PROVISIONAL",
        "symbol": symbol,
        "direction": direction,
        "volume": "0.01",
        "entry_price": "102.0",
        "exit_price": "103.0",
        "sl": "100.0",
        "tp": "105.0",
        "state": "CLOSED",
        "profit_aed": str(pnl),
        "position_ticket": ticket,
        "duplicate_key": duplicate_key,
        "duplicate_role": "duplicate" if duplicate else "unique",
        "is_duplicate": "true" if duplicate else "false",
        "time_bucket": "Evening 16:00-19:59",
    }


def _load_module():
    path = ROOT / "scripts" / "generate_session_extreme_entry_forensics.py"
    spec = importlib.util.spec_from_file_location("generate_session_extreme_entry_forensics", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_session_extreme_entry_forensics"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

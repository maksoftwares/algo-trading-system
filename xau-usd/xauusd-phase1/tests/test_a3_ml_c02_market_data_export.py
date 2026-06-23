from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.a3_meta_v1.market_data_export import export_account_bars_ticks_read_only, parse_utc, render_bar_tick_export_report_md
from ml.a3_meta_v1.safety import scan_c02_python_safety
from ml.a3_meta_v1.terminal_verification import RunningProcess


REGISTRY = ROOT / "config" / "ml" / "mt5_accounts.yaml"


def test_c02_bar_tick_export_writes_hashed_snapshot_with_fake_client(tmp_path: Path) -> None:
    client = _FakeMarketClient("1033030", "C:/MT5PortableTier1BestEA")
    processes = [RunningProcess(pid=10, exe="C:/MT5PortableTier1BestEA/terminal64.exe")]

    record = export_account_bars_ticks_read_only(
        ROOT,
        REGISTRY,
        "A2",
        datetime(2026, 6, 1, tzinfo=timezone.utc),
        datetime(2026, 6, 2, tzinfo=timezone.utc),
        "TEST_DATASET",
        output_root=tmp_path,
        process_provider=lambda: processes,
        client_factory=lambda: client,
        terminal_exists=lambda _: True,
    )

    assert record["status"] == "PASS"
    assert record["code"] == "BAR_TICK_EXPORT_PASS"
    assert record["data_exported"] is True
    assert record["model_training_authorized"] is False
    bar_path = tmp_path / "TEST_DATASET" / "raw" / "A2" / "bars" / "XAUUSD_M5.csv"
    tick_path = tmp_path / "TEST_DATASET" / "raw" / "A2" / "ticks" / "XAUUSD_ticks_20260601.csv"
    manifest_path = tmp_path / "TEST_DATASET" / "raw" / "A2" / "manifest" / "BAR_TICK_MANIFEST.json"
    assert bar_path.exists()
    assert tick_path.exists()
    assert manifest_path.exists()
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["training_authorized"] is False
    with bar_path.open("r", encoding="utf-8", newline="") as handle:
        assert len(list(csv.DictReader(handle))) == 2


def test_c02_bar_tick_export_requires_utc_datetimes(tmp_path: Path) -> None:
    client = _FakeMarketClient("1033030", "C:/MT5PortableTier1BestEA")

    try:
        export_account_bars_ticks_read_only(
            ROOT,
            REGISTRY,
            "A2",
            datetime(2026, 6, 1),
            datetime(2026, 6, 2, tzinfo=timezone.utc),
            "TEST_DATASET",
            output_root=tmp_path,
            process_provider=lambda: [],
            client_factory=lambda: client,
            terminal_exists=lambda _: True,
        )
    except ValueError as exc:
        assert "timezone-aware UTC" in str(exc)
    else:
        raise AssertionError("export accepted a naive datetime")


def test_c02_bar_tick_export_script_and_report_keep_training_blocked() -> None:
    module = load_script("c02_export_mt5_market_data")
    assert hasattr(module, "main")
    payload = {
        "status": "PASS",
        "dataset_version": "TEST",
        "requested_start_utc": "2026-06-01T00:00:00Z",
        "snapshot_cutoff_utc": "2026-06-02T00:00:00Z",
        "output_root": "data/ml/a3_meta_v1/c02/TEST",
        "boundary": {"data_exported": True},
        "account_records": [
            {
                "account_label": "A1",
                "account_scope": "1025742",
                "status": "PASS",
                "code": "BAR_TICK_EXPORT_PASS",
                "coverage": {"bars": {"M5": {"row_count": 2}}, "ticks": {"chunks": [{"row_count": 1}]}},
            }
        ],
        "next_allowed_stage": "C02-03 history/log snapshots after bars/ticks review",
    }

    report = render_bar_tick_export_report_md(payload)

    assert "Model training authorized: false" in report
    assert "Broker action authorized: false" in report
    assert "Data exported: true" in report
    assert parse_utc("2026-06-01T00:00:00Z").tzinfo is not None


def test_c02_market_export_keeps_python_safety_scan_clean() -> None:
    findings = scan_c02_python_safety(ROOT / "ml" / "a3_meta_v1")

    assert findings == []


class _FakeMarketClient:
    def __init__(self, login: str, terminal_root: str):
        self.login = login
        self.terminal_root = terminal_root
        self.shutdown_count = 0

    def initialize(self, spec):
        assert spec.terminal_exe.startswith(self.terminal_root)
        return True

    def shutdown(self):
        self.shutdown_count += 1

    def last_error(self):
        return (0, "ok")

    def account_info(self):
        return SimpleNamespace(login=self.login, server="Capital.ComMena-Demo", trade_mode=0, currency="AED")

    def terminal_info(self):
        return SimpleNamespace(path=self.terminal_root, data_path=self.terminal_root, connected=True, build=5833)

    def symbol_info(self, symbol: str):
        assert symbol == "XAUUSD"
        return SimpleNamespace(point=0.01, digits=2, visible=True)

    def timeframe_value(self, name: str):
        return {"M5": 5, "M15": 15, "H1": 60, "H4": 240, "D1": 1440}[name]

    def copy_ticks_all_flags(self):
        return 0

    def copy_rates_range(self, symbol, timeframe, date_from, date_to):
        assert symbol == "XAUUSD"
        assert date_from.tzinfo is not None
        return [
            {
                "time": 1780272000,
                "open": 3300.0,
                "high": 3301.0,
                "low": 3299.0,
                "close": 3300.5,
                "tick_volume": 10,
                "spread": 25,
                "real_volume": 0,
            },
            {
                "time": 1780272300,
                "open": 3300.5,
                "high": 3301.5,
                "low": 3300.0,
                "close": 3301.0,
                "tick_volume": 12,
                "spread": 26,
                "real_volume": 0,
            },
        ]

    def copy_ticks_range(self, symbol, date_from, date_to, flags):
        assert symbol == "XAUUSD"
        assert date_from.tzinfo is not None
        return [
            {
                "time": 1780272000,
                "time_msc": 1780272000000,
                "bid": 3300.0,
                "ask": 3300.25,
                "last": 0.0,
                "volume": 0,
                "volume_real": 0.0,
                "flags": 6,
            }
        ]

    def positions_get(self, symbol=None):
        return []

    def orders_get(self, symbol=None):
        return []

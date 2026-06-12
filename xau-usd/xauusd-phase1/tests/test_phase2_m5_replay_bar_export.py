from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_m5_replay_bar_export_continuity_reports_gaps_and_duplicates():
    module = _load_module()
    requested_start = datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)
    requested_end = datetime(2026, 6, 1, 0, 20, tzinfo=timezone.utc)
    rows = [
        {"bar_start_utc": "2026-06-01 00:00:00"},
        {"bar_start_utc": "2026-06-01 00:05:00"},
        {"bar_start_utc": "2026-06-01 00:05:00"},
        {"bar_start_utc": "2026-06-01 00:20:00"},
    ]

    result = module._continuity(
        symbol="XAUUSD",
        rows=rows,
        requested_start=requested_start,
        requested_end=requested_end,
    )

    assert result["status"] == "WARN_GAPS_OR_DUPLICATES"
    assert result["rows"] == 4
    assert result["gap_count_gt_5m"] == 1
    assert result["max_gap_minutes"] == "15.0"
    assert result["duplicate_bar_times"] == 1


def test_m5_replay_bar_export_markdown_states_read_only_boundary():
    module = _load_module()
    payload = {
        "status": "PASS",
        "authority": "Read-only M5 replay-bar export.",
        "requested_start_utc": "2026-06-01 00:00:00",
        "requested_end_utc": "2026-06-12 12:00:00",
        "output_dir": "outputs/reports/m5_replay_bars",
        "symbols": [
            {
                "symbol": "XAUUSD",
                "status": "PASS",
                "rows": 3,
                "first_bar_utc": "2026-06-01 00:00:00",
                "last_bar_utc": "2026-06-01 00:10:00",
                "gap_count_gt_5m": 0,
                "max_gap_minutes": "0.0",
                "duplicate_bar_times": 0,
                "continuity_pct_from_first_to_last": "100.00",
            }
        ],
    }

    report = module._render_markdown(payload)

    assert "Read-only history export" in report
    assert "No chart attachments" in report
    assert "partial exports cannot silently drive replay conclusions" in report


def _load_module():
    path = ROOT / "scripts" / "export_phase2_m5_replay_bars.py"
    spec = importlib.util.spec_from_file_location("export_phase2_m5_replay_bars", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["export_phase2_m5_replay_bars"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

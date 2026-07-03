from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "diagnose_xau_920101_breakout_retest_failures.py"
VARIANTS = [
    "baseline_24h_no_smart",
    "current_24h_h1_smart",
    "current_24h_h1_cost010",
    "server_16_19_h1_smart",
    "repair_24h_h1_faststop_min800",
]


def load_module():
    spec = importlib.util.spec_from_file_location("diagnose_xau_920101_breakout_retest_failures", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def make_trade_rows() -> list[dict[str, object]]:
    return [
        {
            "entry_time": "2026.04.01 16:00:00",
            "entry_date": "2026-04-01",
            "entry_hour": "16",
            "entry_session": "server_16_19",
            "direction": "LONG",
            "entry_deal": "11",
            "volume": "0.01",
            "entry_price": "3300.00",
            "entry_comment": "P2DEMO_br_XAUUSD",
            "exit_time": "2026.04.01 16:20:00",
            "exit_date": "2026-04-01",
            "exit_hour": "16",
            "exit_session": "server_16_19",
            "date": "2026-04-01",
            "hour": "16",
            "session": "server_16_19",
            "exit_deal": "12",
            "exit_price": "3315.00",
            "profit_aed": "45.00",
            "balance": "1045.00",
            "exit_comment": "tp 3315.00",
        },
        {
            "entry_time": "2026.04.01 17:00:00",
            "entry_date": "2026-04-01",
            "entry_hour": "17",
            "entry_session": "server_16_19",
            "direction": "SHORT",
            "entry_deal": "13",
            "volume": "0.01",
            "entry_price": "3310.00",
            "entry_comment": "P2DEMO_br_XAUUSD",
            "exit_time": "2026.04.01 17:09:00",
            "exit_date": "2026-04-01",
            "exit_hour": "17",
            "exit_session": "server_16_19",
            "date": "2026-04-01",
            "hour": "17",
            "session": "server_16_19",
            "exit_deal": "14",
            "exit_price": "3318.00",
            "profit_aed": "-24.00",
            "balance": "1021.00",
            "exit_comment": "sl 3318.00",
        },
    ]


def make_order_rows() -> list[dict[str, object]]:
    return [
        {
            "timestamp_broker": "2026.04.01 16:00:00",
            "action": "ORDER_SEND_OK",
            "direction": "LONG",
            "deal_ticket": "11",
            "estimated_cost_R": "0.041",
            "stop_distance_points": "1220",
            "spread_at_order_points": "50",
            "guard_reason": "pass",
        },
        {
            "timestamp_broker": "2026.04.01 17:00:00",
            "action": "ORDER_SEND_OK",
            "direction": "SHORT",
            "deal_ticket": "13",
            "estimated_cost_R": "0.120",
            "stop_distance_points": "417",
            "spread_at_order_points": "50",
            "guard_reason": "pass",
        },
        {
            "timestamp_broker": "2026.04.01 17:05:00",
            "action": "GUARD_BLOCK",
            "direction": "SHORT",
            "deal_ticket": "0",
            "estimated_cost_R": "0.140",
            "stop_distance_points": "360",
            "spread_at_order_points": "50",
            "guard_reason": "open_instance_exposure_exists",
        },
    ]


def test_failure_forensic_builds_offline_payload_and_report(tmp_path: Path) -> None:
    module = load_module()
    variants = []
    for name in VARIANTS:
        trade_csv = tmp_path / f"{name}_trades.csv"
        order_csv = tmp_path / f"{name}_orders.csv"
        write_csv(trade_csv, make_trade_rows())
        write_csv(order_csv, make_order_rows())
        variants.append(
            {
                "name": name,
                "label": name,
                "note": "test variant",
                "trade_csv": str(trade_csv),
                "order_csv": str(order_csv),
            }
        )
    source_json = tmp_path / "source.json"
    source_json.write_text(json.dumps({"scope": {"period": "test"}, "variants": variants}), encoding="utf-8")

    payload = module.build_payload(source_json)
    markdown = module.render_markdown(payload)

    assert payload["status"] == "OFFLINE_FORENSIC_NO_RUNTIME_CHANGE"
    assert payload["variants"]["current_24h_h1_smart"]["cost_bucket"]["cost_R_<=0.05"]["trades"] == 1
    assert payload["variants"]["current_24h_h1_smart"]["stop_bucket"]["stop_<500pt"]["trades"] == 1
    assert payload["variants"]["current_24h_h1_smart"]["hold_bucket"]["hold_<=15m"]["pnl_aed"] == -24.0
    assert payload["variants"]["current_24h_h1_smart"]["order_activity"]["actions"]["GUARD_BLOCK"] == 1
    assert "repair_24h_h1_faststop_min800" in payload["display_variants"]
    assert "repair_24h_h1_faststop_min800" in markdown
    assert "No MT5 chart, preset, order, position, or runtime setting was changed." in markdown


def test_break_even_win_rate_uses_observed_avg_win_loss() -> None:
    module = load_module()
    trades = [{"profit_aed": 45.0}, {"profit_aed": -30.0}, {"profit_aed": -30.0}]

    assert module.break_even_win_rate(trades) == 40.0

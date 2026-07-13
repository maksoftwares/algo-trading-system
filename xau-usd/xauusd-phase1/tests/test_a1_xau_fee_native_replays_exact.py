from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_a1_xau_fee_native_replays_exact.py"


def _load():
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location("run_a1_xau_fee_native_replays_exact", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


R = _load()


def _frozen_config() -> str:
    return """[Common]
Login=1025742
Server=Capital.ComMena-Demo

[Tester]
Expert=old.ex5
Symbol=XAUUSD
Period=M5
Optimization=0
Model=0
FromDate=2022.07.01
ToDate=2026.06.30
Visual=0
ShutdownTerminal=1
UseLocal=1
UseRemote=0
UseCloud=0
Report=Reports\\old

[TesterInputs]
InpAllowDemoTrading=true
InpSignalMode=7
InpStartupLogFileName=old_startup.csv
InpSignalLogFileName=old_signals.csv
InpOrderLogFileName=old_orders.csv
InpManagementLogFileName=old_management.csv
InpDealLogFileName=old_deals.csv
"""


def test_derived_config_strips_account_section_and_changes_only_audit_paths() -> None:
    spec = R.SOURCE_SPECS[0]
    text, log_names = R.derive_replay_config(_frozen_config(), spec)
    parsed = R.exact.parse_ini(text)
    assert set(parsed) == {"Tester", "TesterInputs"}
    assert "[Common]" not in text
    assert parsed["Tester"]["Expert"].endswith(f"{spec.expert_name}.ex5")
    assert parsed["TesterInputs"]["InpSignalMode"] == "7"
    assert parsed["TesterInputs"]["InpAllowDemoTrading"] == "true"
    assert set(log_names) == set(R.LOG_INPUTS)


def _write_tsv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_deal_projection_requires_exact_rows_and_rejects_subcent_fee(tmp_path: Path) -> None:
    fields = [
        "timestamp_broker", "timestamp_local", "run_id", "account", "symbol", "magic",
        "deal_ticket", "position_id", "entry_code", "type_code", "reason_code", "direction",
        "volume", "price", "profit", "commission", "swap", "order_ticket", "comment",
    ]
    row = {field: field for field in fields}
    historical = tmp_path / "historical.tsv"
    replay = tmp_path / "replay.tsv"
    _write_tsv(historical, fields, [row])
    replay_fields = fields[:17] + ["fee"] + fields[17:]
    _write_tsv(replay, replay_fields, [{**row, "fee": "0.0000000000000000"}])
    result, overlay = R.compare_fee_deals(historical, replay, "source")
    assert result["pass"] is True
    assert overlay[0]["fee"] == "0.0000000000000000"

    _write_tsv(replay, replay_fields, [{**row, "fee": "0.0000000000000001"}])
    result, _ = R.compare_fee_deals(historical, replay, "source")
    assert result["pass"] is False
    assert result["all_fee_values_exact_zero"] is False


def test_all_four_sources_and_1356_deals_are_mandatory() -> None:
    assert [item.source_id for item in R.SOURCE_SPECS] == [
        "h4_d1_long_best_box2_atr80",
        "r1_h1_pullback_long_v1",
        "r2_continuation_short_v1",
        "r2_pullback_rejection_short_v1",
    ]
    assert sum(item.trades for item in R.SOURCE_SPECS) == 678
    assert sum(item.deals for item in R.SOURCE_SPECS) == R.EXPECTED_TOTAL_DEALS == 1_356


def test_order_comparison_ignores_guard_text_but_not_executed_rows(tmp_path: Path) -> None:
    fields = ["action", "order_ticket", "deal_ticket", "result_price", "reason"]
    frozen = tmp_path / "frozen.tsv"
    replay = tmp_path / "replay.tsv"
    executed = {"action": "ORDER_SEND_OK", "order_ticket": "1", "deal_ticket": "2", "result_price": "3", "reason": "pass"}
    _write_tsv(frozen, fields, [{"action": "GUARD_BLOCK", "order_ticket": "0", "deal_ticket": "0", "result_price": "0", "reason": "old"}, executed])
    _write_tsv(replay, fields, [{"action": "GUARD_BLOCK", "order_ticket": "0", "deal_ticket": "0", "result_price": "0", "reason": "new"}, executed])
    assert R.compare_executed_order_rows(frozen, replay)["pass"] is True
    changed = {**executed, "result_price": "4"}
    _write_tsv(replay, fields, [changed])
    assert R.compare_executed_order_rows(frozen, replay)["pass"] is False


def test_cli_has_no_live_demo_or_attachment_surface() -> None:
    destinations = {action.dest for action in R.build_parser()._actions}
    assert destinations.issuperset({"tester_sandbox", "metaeditor", "package_dir", "output_dir"})
    assert destinations.isdisjoint({"live", "demo", "account", "server", "profile", "attach"})

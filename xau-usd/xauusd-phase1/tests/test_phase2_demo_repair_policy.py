from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def test_repair_decision_classifies_policy_buckets(tmp_path: Path):
    _make_repo(tmp_path)
    decision = _load("generate_phase2_demo_repair_decision.py", "repair_decision")

    output = decision.generate_repair_decision(tmp_path)
    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    by_key = {(row["candidate"], row["symbol"], row["time_bucket"]): row for row in payload["bucket_decisions"]}

    assert output.status == "REPAIR_DECISION_READY_NO_RUNTIME_CHANGE"
    assert by_key[("symbol_normalized_round_retest_v0", "XAUUSD", "Morning 06:00-11:59")]["classification"] == "SUSPEND_NO_NEW_ENTRIES"
    assert by_key[("session_extreme_retest_v0", "XAUUSD", "Night 20:00-05:59")]["classification"] == "SUSPEND_NO_NEW_ENTRIES"
    assert by_key[("breakout_retest", "XAUUSD", "Morning 06:00-11:59")]["classification"] == "REDUCE_DEMO"
    assert by_key[("breakout_retest", "EURUSD", "Evening 16:00-19:59")]["classification"] == "OWNER_REVIEW_REQUIRED"
    assert by_key[("breakout_retest", "USDJPY", "Evening 16:00-19:59")]["classification"] == "DISABLED_SYMBOL"


def test_repair_applier_is_dry_run_only(tmp_path: Path):
    _make_repo(tmp_path)
    applier = _load("apply_phase2_demo_repair_policy.py", "repair_applier")

    output = applier.apply_repair_policy(tmp_path)
    dry_run = json.loads((tmp_path / "outputs" / "reports" / "PHASE2_DEMO_REPAIR_POLICY_DRY_RUN.json").read_text(encoding="utf-8"))
    reconciliation = (tmp_path / "outputs" / "reports" / "PHASE2_DEMO_REPAIR_RECONCILIATION_2026_06_09.md").read_text(encoding="utf-8")

    assert output.status == "DRY_RUN_ONLY_NO_RUNTIME_CHANGE"
    assert dry_run["runtime_mutation_performed"] is False
    assert "No runtime change was made" in reconciliation


def test_repair_monitor_reports_shadow_findings_before_enforcement(tmp_path: Path):
    _make_repo(tmp_path)
    monitor = _load("generate_phase2_demo_repair_monitor.py", "repair_monitor")

    output = monitor.generate_repair_monitor(tmp_path, since="2026-06-09 00:00:00")
    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    types = {finding["type"] for finding in payload["findings"]}

    assert output.status == "SHADOW_REPAIR_POLICY_WOULD_BLOCK_EVENTS_OBSERVED"
    assert payload["policy_enforced"] is False
    assert {finding["severity"] for finding in payload["findings"]} == {"SHADOW"}
    assert "SUSPENDED_CANDIDATE_ORDER" in types
    assert "DISABLED_SYMBOL_ORDER" in types
    assert "P2WEAKNESS_LOT_EXCEEDED" in types


def test_repair_monitor_flags_policy_leaks_after_effective_time(tmp_path: Path):
    _make_repo(tmp_path)
    policy_path = tmp_path / "config" / "phase2_demo_repair_policy.yaml"
    policy_path.write_text(
        policy_path.read_text(encoding="utf-8").replace("effective_at_dubai: null", 'effective_at_dubai: "2026-06-09 00:00:00"'),
        encoding="utf-8",
    )
    monitor = _load("generate_phase2_demo_repair_monitor.py", "repair_monitor_enforced")

    output = monitor.generate_repair_monitor(tmp_path, since="2026-06-09 00:00:00")
    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    types = {finding["type"] for finding in payload["findings"]}

    assert output.status == "RED_REPAIR_POLICY_LEAK_FOUND"
    assert payload["policy_enforced"] is True
    assert {finding["severity"] for finding in payload["findings"]} == {"RED"}
    assert "SUSPENDED_CANDIDATE_ORDER" in types
    assert "DISABLED_SYMBOL_ORDER" in types
    assert "P2WEAKNESS_LOT_EXCEEDED" in types


def test_forward_week_report_stays_pending_without_post_sample(tmp_path: Path):
    _make_repo(tmp_path, post_rows=False)
    forward = _load("generate_phase2_demo_repair_forward_week_report.py", "repair_forward")

    output = forward.generate_forward_week_report(tmp_path, since="2026-06-09 00:00:00")
    payload = json.loads(output.json_path.read_text(encoding="utf-8"))

    assert output.status == "PENDING_FORWARD_WEEK_NO_POST_REPAIR_SAMPLE"
    assert payload["promotion_decision"] == "NOT_ELIGIBLE_FORWARD_WEEK_PENDING"
    assert payload["post_repair_rule_v1"]["target_delta_closed_pnl_aed"] == 0.0


def test_last_week_repair_backtest_shows_repair_improvement(tmp_path: Path):
    _make_repo(tmp_path)
    _write_repair_rules(tmp_path / "outputs" / "reports" / "PHASE2_REPAIR_CANDIDATE_RULES.csv")
    backtest = _load("generate_phase2_demo_repair_last_week_backtest.py", "repair_last_week")

    output = backtest.generate_last_week_repair_backtest(tmp_path)
    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    by_candidate = {row["candidate"]: row for row in payload["candidate_results"]}

    assert output.status == "REPAIR_LAST_WEEK_BACKTEST_READY"
    assert payload["target_duplicate_hidden_baseline"]["closed_pnl_aed"] < 0
    assert payload["repair_rule_v1"]["would_keep"]["closed_pnl_aed"] > payload["target_duplicate_hidden_baseline"]["closed_pnl_aed"]
    assert by_candidate["symbol_normalized_round_retest_v0"]["repair_rule_v1_delta_closed_pnl_aed"] > 0
    assert by_candidate["session_extreme_retest_v0"]["repair_rule_v1_delta_closed_pnl_aed"] > 0


def test_repair_scripts_do_not_import_mt5_runtime():
    for name in (
        "generate_phase2_demo_repair_decision.py",
        "apply_phase2_demo_repair_policy.py",
        "generate_phase2_demo_repair_monitor.py",
        "generate_phase2_demo_repair_forward_week_report.py",
        "generate_phase2_demo_repair_last_week_backtest.py",
    ):
        text = (SCRIPTS / name).read_text(encoding="utf-8")
        for forbidden in ("MetaTrader5", "mt5.initialize", "OrderSend", "terminal64.exe"):
            assert forbidden not in text


def _make_repo(root: Path, post_rows: bool = True) -> None:
    reports = root / "outputs" / "reports"
    config = root / "config"
    reports.mkdir(parents=True)
    config.mkdir(parents=True)
    (config / "phase2_demo_repair_policy.yaml").write_text(
        """
policy_id: phase2_demo_repair_policy_2026_06_09_v1
canonical_phase2_authorized: false
live_trading_authorized: false
experimental_demo_only: true
effective_at_dubai: null
suspend_candidates:
  - symbol_normalized_round_retest_v0
  - session_extreme_retest_v0
disable_symbols:
  - USDJPY
observer_only_candidates:
  - swing_breakout_retest_v0
  - round_number_retest_v0
  - WR50_BreakoutEvening_v0
conditional_session_blocks_shadow:
  - symbol: XAUUSD
    start_dubai: "06:00"
    end_dubai: "15:59"
    status: shadow_forward_week_required
keep_candidates:
  - breakout_retest
p2weakness:
  candidate: breakout_retest
  symbol: XAUUSD
  magic: 931000
  max_orders_per_day: 2
  max_account_orders_per_day: 3
  max_family_positions: 1
  fixed_lot: 0.01
  max_cost_r: 0.15
  status: owner_authorized_demo_quarantine_only
""".strip()
        + "\n",
        encoding="utf-8",
    )
    rows = [
        _row("2026-06-08 10:00:00", "breakout_retest", "XAUUSD", "BUY", "0.01", "10", "1", "920101"),
        _row("2026-06-08 17:00:00", "breakout_retest", "EURUSD", "SELL", "0.05", "8", "2", "920102"),
        _row("2026-06-08 17:05:00", "breakout_retest", "USDJPY", "SELL", "0.01", "-2", "3", "920103"),
    ]
    if post_rows:
        rows.extend(
            [
                _row("2026-06-09 10:00:00", "symbol_normalized_round_retest_v0", "XAUUSD", "BUY", "0.01", "-9", "4", "920301"),
                _row("2026-06-09 21:00:00", "session_extreme_retest_v0", "XAUUSD", "SELL", "0.01", "-7", "5", "920501"),
                _row("2026-06-09 17:00:00", "breakout_retest", "USDJPY", "SELL", "0.01", "-1", "6", "920103"),
                _row("2026-06-09 18:00:00", "p2weakness_br_v1", "XAUUSD", "BUY", "0.02", "3", "7", "931000"),
            ]
        )
    _write_trades(reports / "PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv", rows)
    (reports / "PHASE2_EA_WEAKNESS_SHADOW_REPORT.json").write_text(
        json.dumps(
            {
                "account": {"login": 1025742, "server": "Capital.ComMena-Demo", "currency": "AED"},
                "weakness_shadow": {
                    "combined_keep_summary": _summary(76, 481.11, 46.05, 2.21),
                    "combined_block_summary": _summary(142, -448.15, 34.51, 0.76),
                },
            }
        ),
        encoding="utf-8",
    )


def _write_trades(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "entry_time",
        "exit_time",
        "candidate",
        "status",
        "symbol",
        "direction",
        "volume",
        "entry_price",
        "exit_price",
        "sl",
        "tp",
        "state",
        "profit_aed",
        "position_ticket",
        "magic",
        "is_duplicate",
        "time_bucket",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_repair_rules(path: Path) -> None:
    fieldnames = ["candidate", "repair_id", "rule_type", "symbol", "time_bucket", "direction", "runtime_action"]
    rows = [
        {
            "candidate": "session_extreme_retest_v0",
            "repair_id": "session_extreme_retest_v0_repair_v1",
            "rule_type": "BLOCK_CLUSTER",
            "symbol": "XAUUSD",
            "time_bucket": "Night 20:00-05:59",
            "direction": "SELL",
            "runtime_action": "NONE_SHADOW_ONLY",
        },
        {
            "candidate": "symbol_normalized_round_retest_v0",
            "repair_id": "symbol_normalized_round_retest_v0_repair_v1",
            "rule_type": "BLOCK_CLUSTER",
            "symbol": "XAUUSD",
            "time_bucket": "Morning 06:00-11:59",
            "direction": "BUY",
            "runtime_action": "NONE_SHADOW_ONLY",
        },
        {
            "candidate": "round_number_retest_v0",
            "repair_id": "round_number_retest_v0_repair_v1",
            "rule_type": "DUPLICATE_ONLY_REBUILD",
            "symbol": "ANY",
            "time_bucket": "ANY",
            "direction": "ANY",
            "runtime_action": "NONE_SHADOW_ONLY",
        },
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _row(entry: str, candidate: str, symbol: str, direction: str, volume: str, pnl: str, ticket: str, magic: str) -> dict[str, str]:
    return {
        "entry_time": entry,
        "exit_time": entry,
        "candidate": candidate,
        "status": "ACCEPTED",
        "symbol": symbol,
        "direction": direction,
        "volume": volume,
        "entry_price": "100",
        "exit_price": "101",
        "sl": "99",
        "tp": "102",
        "state": "CLOSED",
        "profit_aed": pnl,
        "position_ticket": ticket,
        "magic": magic,
        "is_duplicate": "false",
        "time_bucket": "",
    }


def _summary(closed: int, pnl: float, win_rate: float, pf: float) -> dict[str, object]:
    return {
        "actual_trades": closed,
        "closed_trades": closed,
        "open_trades": 0,
        "wins": 0,
        "losses": 0,
        "closed_win_rate_pct": win_rate,
        "closed_pnl_aed": pnl,
        "floating_pnl_aed": 0.0,
        "total_pnl_aed": pnl,
        "profit_factor": pf,
        "avg_win_aed": None,
        "avg_loss_aed": None,
    }


def _load(filename: str, module_name: str):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    path = SCRIPTS / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

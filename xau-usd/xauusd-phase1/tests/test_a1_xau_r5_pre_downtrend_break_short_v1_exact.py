from __future__ import annotations

import importlib.util
import json
import sys
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
RUNNER = SCRIPTS / "run_a1_r5_pre_downtrend_break_short_v1_exact.py"
EA = ROOT / "mt5" / "Experts" / "A1XauM5MomentumContinuationExecutor.mq5"


def load_runner():
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location("run_a1_r5_pre_downtrend_break_short_v1_exact", RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_r5_is_one_locked_q55_cell_with_no_addon_filters() -> None:
    module = load_runner()
    variant = module.build_variant()
    checks = module.static_checks(variant)
    assert all(checks.values()), checks
    assert len(module.HORIZONS) == 2
    assert [(item.name, item.from_date, item.to_date, item.minimum_trades) for item in module.HORIZONS] == [
        ("five_year", "2021.07.01", "2026.06.30", 75),
        ("ten_year", "2016.07.01", "2026.06.30", 150),
    ]
    assert variant.tester_inputs == module.R5_INPUTS
    assert module.stable_hash(variant.tester_inputs) == module.stable_hash(module.R5_INPUTS)
    assert module.portable_source_path(module.PREREG).startswith("docs/")
    assert not Path(module.portable_source_path(module.PREREG)).is_absolute()


def test_r5_compile_result_is_fail_closed() -> None:
    module = load_runner()
    assert module.compile_result("Result: 0 errors, 0 warnings, 3083 ms elapsed") == (0, 0)
    try:
        module.compile_result("MetaEditor exited without a summary")
    except RuntimeError as exc:
        assert "no recognized" in str(exc)
    else:
        raise AssertionError("missing compile result must fail closed")


def test_r5_tester_config_removes_account_session_section() -> None:
    module = load_runner()
    source = "[Common]\nLogin=1025742\nServer=Demo\n\n[Tester]\nModel=0\n\n[TesterInputs]\nInpAllowedAccountLogin=1025742\n"
    safe = module.tester_only_config_text(source)
    assert safe.startswith("[Tester]\n")
    assert "[Common]" not in safe
    assert "\nLogin=" not in safe
    assert "\nServer=" not in safe
    assert "InpAllowedAccountLogin=1025742" in safe
    try:
        module.tester_only_config_text(source + "\n[Extra]\nKey=Value\n")
    except RuntimeError as exc:
        assert "unsafe or incomplete" in str(exc)
    else:
        raise AssertionError("unexpected tester section must fail closed")


def test_signal_log_compression_is_deterministic_and_lossless(tmp_path: Path) -> None:
    import gzip

    module = load_runner()
    source = tmp_path / "signals.csv"
    original = ("timestamp\treason\n2026.01.01 00:00:00\tchop\n" * 20).encode()
    source.write_bytes(original)
    evidence = module.compress_signal_log(source)
    archive = Path(evidence["path"])
    assert not source.exists()
    assert archive.is_file()
    assert evidence["uncompressed_bytes"] == len(original)
    assert gzip.decompress(archive.read_bytes()) == original


def test_archived_run_metadata_uses_portable_existing_artifact_paths(tmp_path: Path) -> None:
    module = load_runner()
    run_dir = tmp_path / "runs" / "five_year"
    variant_dir = run_dir / "variant"
    variant_dir.mkdir(parents=True)
    summary_path = variant_dir / "summary.json"
    summary_path.write_text(
        json.dumps({"tester_config": r"C:\runtime\tester.ini", "signal_csv": r"C:\deleted\signals.csv"}),
        encoding="utf-8",
    )
    component_path = run_dir / "mt5_components.json"
    component_path.write_text(
        json.dumps(
            {
                "compile_log": r"C:\runtime\compile.log",
                "scope": {"terminal_sandbox": r"C:\runtime"},
                "variants": [{"summary_json": str(summary_path), "signal_csv": r"C:\deleted\signals.csv"}],
            }
        ),
        encoding="utf-8",
    )
    component_markdown_path = run_dir / "mt5_components.md"
    component_markdown_path.write_text(
        "- Profit/loss table values are in tester currency `USD`.\n"
        "- Signal CSV: `C:\\deleted\\signals.csv`\n",
        encoding="utf-8",
    )
    artifact_paths = {
        "tester_config": "runs/five_year/tester.ini",
        "html_report": "runs/five_year/variant/report.htm",
        "trade_csv": "runs/five_year/variant/trades.csv",
        "order_csv": "runs/five_year/variant/orders.csv",
        "management_csv": "runs/five_year/variant/management.csv",
        "deal_csv": "runs/five_year/variant/deals.csv",
        "summary_json": "runs/five_year/variant/summary.json",
        "signal_csv_gzip": "runs/five_year/variant/signals.csv.gz",
        "compile_log": "runs/five_year/compile.log",
    }
    for relative in artifact_paths.values():
        path = tmp_path / relative
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"")
    horizon = {
        "name": "five_year",
        "artifacts": artifact_paths,
        "signal_log_archive": {"path": artifact_paths["signal_csv_gzip"], "sha256": "abc"},
    }
    module.rewrite_archived_run_metadata(tmp_path, horizon)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    component = json.loads(component_path.read_text(encoding="utf-8"))
    component_markdown = component_markdown_path.read_text(encoding="utf-8")
    assert summary["signal_csv"] == artifact_paths["signal_csv_gzip"]
    assert summary["tester_config"] == artifact_paths["tester_config"]
    assert component["compile_log"] == artifact_paths["compile_log"]
    assert component["scope"]["terminal_sandbox"] == "runtime-only; not archived"
    assert component["variants"][0]["signal_csv"] == artifact_paths["signal_csv_gzip"]
    assert "tester-currency USD" in summary["legacy_currency_field_note"]
    assert "C:\\" not in json.dumps(summary)
    assert "C:\\" not in json.dumps(component)
    assert "C:\\" not in component_markdown
    assert "Signal CSV (gzip)" in component_markdown
    assert "tester-currency USD" in component_markdown


def test_ea_router_mode_5_allows_only_short_in_uptrend_or_chop_and_tags_success() -> None:
    text = EA.read_text(encoding="utf-8")
    assert "REGIME_ROUTER_OFF = 0" in text
    assert "REGIME_ROUTER_LONG_R1_UPTREND_ONLY = 1" in text
    assert "REGIME_ROUTER_SHORT_R2_DOWNTREND_ONLY = 2" in text
    assert "REGIME_ROUTER_DIRECTIONAL_R1_LONG_R2_SHORT = 3" in text
    assert "REGIME_ROUTER_R4_CHOP_ONLY = 4" in text
    assert "REGIME_ROUTER_SHORT_R5_UPTREND_CHOP_ONLY = 5" in text
    assert 'return "short_r5_uptrend_chop_only";' in text
    assert 'direction == "SHORT" && (regime == XAU_REGIME_UPTREND || regime == XAU_REGIME_CHOP)' in text
    assert 'block_reason = "regime_router_allow_" + mode_name + "_state_" + regime_name;' in text
    assert "InpRegimeRouterMode == REGIME_ROUTER_SHORT_R5_UPTREND_CHOP_ONLY) ? regime_block_reason : \"pass\"" in text
    assert "input RegimeRouterMode InpRegimeRouterMode   = REGIME_ROUTER_OFF;" in text
    assert "bool RegimeRouterDataAvailable()" in text
    router = text[text.index("bool RegimeRouterAllows(") : text.index("double OwnClosedPnlBetween(")]
    unavailable = "InpRegimeRouterMode == REGIME_ROUTER_SHORT_R5_UPTREND_CHOP_ONLY && !RegimeRouterDataAvailable()"
    assert unavailable in router
    assert 'block_reason = "regime_router_block_" + mode_name + "_state_unknown";' in router
    assert router.index(unavailable) < router.index("const XauRegimeState regime = CurrentXauRegime();")


def test_r5_metrics_apply_locked_stress_and_concentration() -> None:
    module = load_runner()
    rows = []
    for index, pnl in enumerate((10.0, 10.0, -5.0, -5.0), start=1):
        timestamp = datetime(2020, 1, index, 12)
        rows.append(
            {
                "entry_time": timestamp,
                "entry_date": timestamp.date(),
                "exit_time": timestamp,
                "exit_date": timestamp.date(),
                "pnl_usd": pnl,
                "source_row": index,
            }
        )
    base = module.pnl_metrics(rows)
    stress = module.pnl_metrics(rows, cost_per_trade=0.30)
    concentration = module.concentration_metrics(rows)
    assert base == {
        "trades": 4,
        "wins": 2,
        "losses": 2,
        "win_rate_pct": 50.0,
        "realized_win_loss": 2.0,
        "profit_factor": 2.0,
        "net_usd": 10.0,
        "max_closed_drawdown_usd": 10.0,
    }
    assert stress["net_usd"] == 8.8
    assert stress["profit_factor"] == 1.830189
    assert concentration["top10_winning_trades_removed_net_usd"] == -10.0
    assert concentration["top3_winning_entry_days_removed_net_usd"] == -10.0


def test_r5_exposure_episode_and_daily_correlation_helpers_are_deterministic() -> None:
    module = load_runner()
    h4 = [
        {"entry_time": "2020-01-01 00:00:00", "exit_time": "2020-01-03 00:00:00"},
        {"entry_time": "2020-01-02 00:00:00", "exit_time": "2020-01-04 00:00:00"},
        {"entry_time": "2020-02-01 00:00:00", "exit_time": "2020-02-02 00:00:00"},
    ]
    episodes = module.merge_exposure_episodes(h4)
    assert episodes == [
        (datetime(2020, 1, 1), datetime(2020, 1, 4)),
        (datetime(2020, 2, 1), datetime(2020, 2, 2)),
    ]
    assert module.touched_episode_count([datetime(2020, 1, 2), datetime(2020, 2, 1)], episodes) == 2
    assert module.pearson_daily_pnl(
        {date(2020, 1, 1): 1.0, date(2020, 1, 2): -1.0},
        {date(2020, 1, 1): -1.0, date(2020, 1, 2): 1.0},
    ) == -1.0


def test_r5_valid_signal_coverage_uses_only_post_router_risk_eligible_rows() -> None:
    module = load_runner()
    rows = [
        {"timestamp_broker": "2020.01.01 01:00:00", "action": "ORDER_SEND_OK", "reason": next(iter(module.ALLOWED_R5_ORDER_TAGS))},
        {"timestamp_broker": "2020.01.02 01:00:00", "action": "GUARD_BLOCK", "reason": "daily_trade_cap_reached"},
        {"timestamp_broker": "2020.01.03 01:00:00", "action": "GUARD_BLOCK", "reason": "own_position_exists"},
        {"timestamp_broker": "2020.01.04 01:00:00", "action": "GUARD_BLOCK", "reason": "stop_ceiling_exceeded"},
        {"timestamp_broker": "2020.01.05 01:00:00", "action": "GUARD_BLOCK", "reason": "regime_router_block_short_r5_uptrend_chop_only_state_downtrend"},
    ]
    assert module.valid_signal_times(rows) == [
        datetime(2020, 1, 1, 1),
        datetime(2020, 1, 2, 1),
        datetime(2020, 1, 3, 1),
    ]


def test_r5_reads_effective_inputs_from_native_report_not_generated_ini() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    assert 'actual_inputs = effective_inputs.parse_effective_inputs(Path(result["html_report"]))' in text
    assert 'intended_inputs = parse_tester_inputs(Path(result["tester_config"]))' in text
    assert '"native_effective_inputs_match_generated_ini": effective_inputs_match' in text

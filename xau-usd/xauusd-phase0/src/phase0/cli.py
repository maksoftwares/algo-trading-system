from __future__ import annotations

import argparse
from pathlib import Path

from phase0.adversarial import create_adversarial_packets
from phase0.aggregation import aggregate_matrix_results
from phase0.bar_builder import build_bars_for_latest_ticks, parse_timeframes
from phase0.config import ConfigError, build_cell_configs, load_project_config
from phase0.constants import EXPERTS
from phase0.data_availability import (
    assert_processed_data_available,
    check_processed_data_availability,
    generate_data_requirements_csv,
    generate_data_readiness_report,
)
from phase0.data_import import import_required_bar_exports
from phase0.deciles import run_decile_tests
from phase0.hashing import HashingError, hash_manifest_path, register_hypotheses, validate_hypotheses
from phase0.manifests import generate_data_manifest, generate_required_data_manifest, generate_result_manifest
from phase0.matrix import run_phase0_matrix
from phase0.multisymbol import run_multisymbol_checks
from phase0.mt5_presets import generate_mt5_bar_export_presets
from phase0.normalizer import (
    NormalizationError,
    normalize_broker_bar_files,
    normalize_broker_bars,
    normalize_broker_ticks,
    validate_raw_files_without_writing,
)
from phase0.reports import generate_all_reports
from phase0.safety import audit_no_live_trading_calls
from phase0.snapshot import generate_snapshot
from phase0.spread_analysis import analyze_spread_logs
from phase0.utils import configure_run_logging, log_command_failure, log_command_success
from phase0.workflow import run_all_phase0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging_setup = configure_run_logging(args.root, args.command)
    try:
        exit_code = int(args.func(args))
        log_command_success(args.command, logging_setup.log_path)
        return exit_code
    except (ConfigError, HashingError, NormalizationError) as exc:
        log_command_failure(args.command, exc, logging_setup.log_path)
        parser.exit(1, f"Configuration error: {exc}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="phase0", description="XAUUSD Phase 0 research CLI")
    parser.add_argument(
        "--root",
        default=Path.cwd(),
        type=Path,
        help="Phase 0 project root. Defaults to the current working directory.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_config = subparsers.add_parser("validate-config", help="Validate all YAML configs.")
    validate_config.set_defaults(func=_cmd_validate_config)

    audit_safety = subparsers.add_parser("audit-safety", help="Scan for forbidden live-trading calls.")
    audit_safety.set_defaults(func=_cmd_audit_safety)

    hash_hypotheses = subparsers.add_parser("hash-hypotheses", help="Register or validate hypotheses.")
    hash_hypotheses.add_argument("--register", action="store_true", help="Register current hashes.")
    hash_hypotheses.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the manifest. Only use before any result-producing run.",
    )
    hash_hypotheses.set_defaults(func=_cmd_hash_hypotheses)

    validate_data = subparsers.add_parser("validate-data", help="Validate raw or processed data.")
    _add_broker_symbol_args(validate_data)
    validate_data.set_defaults(func=_cmd_validate_data)

    check_data = subparsers.add_parser(
        "check-data-availability",
        help="Check processed bars required by real-data Phase 0 runs.",
    )
    check_data.add_argument("--skip-multisymbol", action="store_true")
    check_data.set_defaults(func=_cmd_check_data_availability)

    data_readiness = subparsers.add_parser(
        "generate-data-readiness",
        help="Write a real-data readiness report for Phase 0.",
    )
    data_readiness.add_argument("--skip-multisymbol", action="store_true")
    data_readiness.set_defaults(func=_cmd_generate_data_readiness)

    data_requirements = subparsers.add_parser(
        "generate-data-requirements",
        help="Write the required broker/symbol/timeframe acquisition checklist.",
    )
    data_requirements.add_argument("--skip-multisymbol", action="store_true")
    data_requirements.set_defaults(func=_cmd_generate_data_requirements)

    data_manifest = subparsers.add_parser(
        "generate-data-manifest",
        help="Write an auditable manifest for required Phase 0 data files.",
    )
    data_manifest.add_argument("--skip-multisymbol", action="store_true")
    data_manifest.set_defaults(func=_cmd_generate_data_manifest)

    mt5_presets = subparsers.add_parser(
        "generate-mt5-bar-presets",
        help="Write MT5 bar-export .set files from Phase 0 data requirements.",
    )
    mt5_presets.add_argument("--skip-multisymbol", action="store_true")
    mt5_presets.add_argument(
        "--server-to-utc-offset-hours",
        type=int,
        default=0,
        help="Fixed MT5 server offset from UTC used in generated exporter presets.",
    )
    mt5_presets.set_defaults(func=_cmd_generate_mt5_bar_presets)

    normalize_data = subparsers.add_parser("normalize-data", help="Normalize source data.")
    _add_broker_symbol_args(normalize_data)
    normalize_data.set_defaults(func=_cmd_normalize_data)

    normalize_bars = subparsers.add_parser("normalize-bars", help="Normalize broker OHLC bar CSV exports.")
    _add_broker_symbol_args(normalize_bars)
    normalize_bars.add_argument("--timeframe", required=True)
    normalize_bars.add_argument(
        "--input-file",
        type=Path,
        help="Normalize one exact OHLC bar CSV path, even if the filename lacks symbol/timeframe tokens.",
    )
    normalize_bars.add_argument(
        "--timestamp-is",
        choices=("bar_start", "bar_end"),
        default="bar_start",
        help="Interpret source timestamps as bar starts or bar ends. MT5 history exports usually use bar_start.",
    )
    normalize_bars.set_defaults(func=_cmd_normalize_bars)

    import_required_bars = subparsers.add_parser(
        "import-required-bars",
        help="Batch-import raw OHLC bar exports for all required Phase 0 sets.",
    )
    import_required_bars.add_argument("--skip-multisymbol", action="store_true")
    import_required_bars.add_argument(
        "--timestamp-is",
        choices=("bar_start", "bar_end"),
        default="bar_start",
        help="Interpret generic source timestamps as bar starts or bar ends.",
    )
    import_required_bars.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Return non-zero when any required broker/symbol/timeframe set is still missing.",
    )
    import_required_bars.set_defaults(func=_cmd_import_required_bars)

    build_bars = subparsers.add_parser("build-bars", help="Build M1/M5/M15/H1/H4/D1 bars.")
    _add_broker_symbol_args(build_bars)
    build_bars.add_argument("--timeframes", default="M1,M5,M15,H1,H4,D1")
    build_bars.set_defaults(func=_cmd_build_bars)

    run_matrix = subparsers.add_parser("run-matrix", help="Run the 9-cell Phase 0 matrix.")
    run_matrix.add_argument("--expert", choices=(*EXPERTS, "all"), required=True)
    run_matrix.add_argument(
        "--synthetic-sample",
        action="store_true",
        help="Run deterministic synthetic data through the matrix as a smoke test.",
    )
    run_matrix.set_defaults(func=_cmd_run_matrix)

    run_deciles = subparsers.add_parser("run-deciles", help="Run decile persistence tests.")
    run_deciles.add_argument("--expert", choices=(*EXPERTS, "all"), required=True)
    run_deciles.add_argument("--synthetic-sample", action="store_true")
    run_deciles.add_argument("--unlock-true-holdout", action="store_true")
    run_deciles.set_defaults(func=_cmd_run_deciles)

    run_multisymbol = subparsers.add_parser("run-multisymbol", help="Run multisymbol checks.")
    run_multisymbol.add_argument("--expert", choices=(*EXPERTS, "all"), required=True)
    run_multisymbol.add_argument("--broker", default="capital_com")
    run_multisymbol.add_argument("--cost-model", default="median")
    run_multisymbol.add_argument("--synthetic-sample", action="store_true")
    run_multisymbol.add_argument("--unlock-true-holdout", action="store_true")
    run_multisymbol.set_defaults(func=_cmd_run_multisymbol)

    adversarial = subparsers.add_parser(
        "create-adversarial-packets",
        help="Create adversarial review packets.",
    )
    adversarial.add_argument("--expert", choices=(*EXPERTS, "all"), required=True)
    adversarial.set_defaults(func=_cmd_create_adversarial_packets)

    aggregate = subparsers.add_parser("aggregate-results", help="Aggregate Phase 0 outputs.")
    aggregate.add_argument("--expert", choices=(*EXPERTS, "all"), required=True)
    aggregate.set_defaults(func=_cmd_aggregate_results)

    generate_verdict = subparsers.add_parser("generate-verdict", help="Generate PHASE0_VERDICT.md.")
    generate_verdict.set_defaults(func=_cmd_generate_verdict)

    result_manifest = subparsers.add_parser(
        "generate-result-manifest",
        help="Hash generated Phase 0 result artifacts.",
    )
    result_manifest.set_defaults(func=_cmd_generate_result_manifest)

    generate_snapshot = subparsers.add_parser("generate-snapshot", help="Generate audit snapshot bundle.")
    generate_snapshot.add_argument("--include-raw-data", action="store_true")
    generate_snapshot.set_defaults(func=_cmd_generate_snapshot)

    analyze_spreads = subparsers.add_parser("analyze-spread-logs", help="Analyze passive spread logs.")
    analyze_spreads.add_argument("--input-dir", type=Path)
    analyze_spreads.add_argument("--glob", default="spread_log_*.csv")
    analyze_spreads.set_defaults(func=_cmd_analyze_spread_logs)

    run_all = subparsers.add_parser("run-all", help="Run the full Phase 0 workflow.")
    run_all.add_argument("--synthetic-sample", action="store_true")
    run_all.add_argument("--unlock-true-holdout", action="store_true")
    run_all.set_defaults(func=_cmd_run_all)

    return parser


def _cmd_validate_config(args: argparse.Namespace) -> int:
    config = load_project_config(args.root)
    cells = build_cell_configs(config)
    print(f"Config OK: {config.phase0['project']['name']}")
    print(f"Enabled experts: {', '.join(_enabled_experts(config.phase0))}")
    print(f"Phase 0 cells: {len(cells)}")
    return 0


def _cmd_audit_safety(args: argparse.Namespace) -> int:
    config = load_project_config(args.root)
    findings = audit_no_live_trading_calls(config)
    if findings:
        print(f"Safety audit failed: {len(findings)} finding(s)")
        for finding in findings:
            print(f"{finding.path}:{finding.line_number}: {finding.pattern}: {finding.line}")
        return 1
    print("Safety audit OK: no forbidden live-trading calls found.")
    return 0


def _cmd_hash_hypotheses(args: argparse.Namespace) -> int:
    config = load_project_config(args.root)
    if args.register:
        rows = register_hypotheses(config, force=args.force)
        print(f"Registered {len(rows)} hypothesis hash(es): {hash_manifest_path(config)}")
        return 0

    validate_hypotheses(config)
    print(f"Hypothesis hashes OK: {hash_manifest_path(config)}")
    return 0


def _cmd_validate_data(args: argparse.Namespace) -> int:
    config = load_project_config(args.root)
    reports = validate_raw_files_without_writing(config, args.broker, args.symbol)
    manifest_path = generate_data_manifest(config, args.broker, args.symbol, reports)
    error_count = sum(report.error_count for report in reports)
    warning_count = sum(report.warning_count for report in reports)
    print(
        f"Validated {len(reports)} raw file(s) for broker={args.broker}, symbol={args.symbol}: "
        f"{error_count} error(s), {warning_count} warning(s)."
    )
    print(f"Validation artifacts: {config.root / 'outputs' / 'manifests'}")
    print(f"Data manifest: {manifest_path}")
    return 0


def _cmd_check_data_availability(args: argparse.Namespace) -> int:
    config = load_project_config(args.root)
    include_multisymbol = not args.skip_multisymbol
    assert_processed_data_available(config, include_multisymbol=include_multisymbol)
    checks = check_processed_data_availability(config, include_multisymbol=include_multisymbol)
    print(f"Processed data availability OK: {len(checks)} timeframe set(s) found.")
    return 0


def _cmd_generate_data_readiness(args: argparse.Namespace) -> int:
    config = load_project_config(args.root)
    output_path = generate_data_readiness_report(
        config,
        include_multisymbol=not args.skip_multisymbol,
    )
    checks = check_processed_data_availability(
        config,
        include_multisymbol=not args.skip_multisymbol,
    )
    missing = [check for check in checks if not check.available]
    print(f"Data readiness report: {output_path}")
    print(f"Ready: {len(checks) - len(missing)}/{len(checks)} required timeframe set(s)")
    return 0


def _cmd_generate_data_requirements(args: argparse.Namespace) -> int:
    config = load_project_config(args.root)
    output_path = generate_data_requirements_csv(
        config,
        include_multisymbol=not args.skip_multisymbol,
    )
    checks = check_processed_data_availability(
        config,
        include_multisymbol=not args.skip_multisymbol,
    )
    print(f"Data requirements: {output_path}")
    print(f"Required timeframe sets: {len(checks)}")
    return 0


def _cmd_generate_data_manifest(args: argparse.Namespace) -> int:
    config = load_project_config(args.root)
    output_path = generate_required_data_manifest(
        config,
        include_multisymbol=not args.skip_multisymbol,
    )
    print(f"Data manifest: {output_path}")
    return 0


def _cmd_generate_mt5_bar_presets(args: argparse.Namespace) -> int:
    config = load_project_config(args.root)
    output = generate_mt5_bar_export_presets(
        config,
        include_multisymbol=not args.skip_multisymbol,
        server_to_utc_offset_hours=args.server_to_utc_offset_hours,
    )
    print(f"MT5 bar export presets: {len(output.preset_paths)} file(s)")
    for path in output.preset_paths:
        print(path)
    print(f"Preset manifest: {output.manifest_path}")
    return 0


def _cmd_normalize_data(args: argparse.Namespace) -> int:
    config = load_project_config(args.root)
    written = normalize_broker_ticks(config, args.broker, args.symbol)
    manifest_path = generate_data_manifest(config, args.broker, args.symbol)
    print(f"Normalized {len(written)} tick file(s):")
    for path in written:
        print(path)
    print(f"Data manifest: {manifest_path}")
    return 0


def _cmd_normalize_bars(args: argparse.Namespace) -> int:
    config = load_project_config(args.root)
    if args.input_file is None:
        written = normalize_broker_bars(
            config,
            args.broker,
            args.symbol,
            args.timeframe.upper(),
            timestamp_is=args.timestamp_is,
        )
    else:
        input_file = args.input_file if args.input_file.is_absolute() else config.root / args.input_file
        written = normalize_broker_bar_files(
            config,
            args.broker,
            args.symbol,
            args.timeframe.upper(),
            [input_file],
            timestamp_is=args.timestamp_is,
        )
    manifest_path = generate_data_manifest(config, args.broker, args.symbol)
    print(f"Normalized {len(written)} bar file(s):")
    for path in written:
        print(path)
    print(f"Data manifest: {manifest_path}")
    return 0


def _cmd_import_required_bars(args: argparse.Namespace) -> int:
    config = load_project_config(args.root)
    output = import_required_bar_exports(
        config,
        include_multisymbol=not args.skip_multisymbol,
        timestamp_is=args.timestamp_is,
    )
    requirements_path = generate_data_requirements_csv(
        config,
        include_multisymbol=not args.skip_multisymbol,
    )
    readiness_path = generate_data_readiness_report(
        config,
        include_multisymbol=not args.skip_multisymbol,
    )
    manifest_path = generate_required_data_manifest(
        config,
        include_multisymbol=not args.skip_multisymbol,
    )
    imported = sum(1 for result in output.results if result.status == "IMPORTED")
    missing = sum(1 for result in output.results if result.status == "MISSING")
    failed = sum(1 for result in output.results if result.status == "FAILED")
    print(
        f"Required bar import complete: {imported} imported, "
        f"{missing} missing, {failed} failed."
    )
    print(f"Import report: {output.report_path}")
    print(f"Data requirements: {requirements_path}")
    print(f"Data manifest: {manifest_path}")
    print(f"Data readiness report: {readiness_path}")
    return 1 if failed or (args.fail_on_missing and missing) else 0


def _cmd_build_bars(args: argparse.Namespace) -> int:
    config = load_project_config(args.root)
    timeframes = parse_timeframes(args.timeframes)
    written = build_bars_for_latest_ticks(config, args.broker, args.symbol, timeframes)
    manifest_path = generate_data_manifest(config, args.broker, args.symbol)
    print(f"Built {len(written)} bar file(s):")
    for path in written:
        print(path)
    print(f"Data manifest: {manifest_path}")
    return 0


def _cmd_run_matrix(args: argparse.Namespace) -> int:
    config = load_project_config(args.root)
    validate_hypotheses(config)
    outputs = run_phase0_matrix(config, args.expert, synthetic_sample=args.synthetic_sample)
    print(f"Matrix run complete: {len(outputs)} cell output set(s)")
    for output in outputs:
        print(output.summary_path)
        print(output.trades_path)
        print(output.equity_path)
    return 0


def _cmd_aggregate_results(args: argparse.Namespace) -> int:
    config = load_project_config(args.root)
    outputs = aggregate_matrix_results(config, args.expert)
    print(f"Aggregated matrix results for {len(outputs)} expert(s)")
    for output in outputs:
        print(output.metrics_path)
        print(output.gates_path)
    return 0


def _cmd_run_deciles(args: argparse.Namespace) -> int:
    config = load_project_config(args.root)
    validate_hypotheses(config)
    outputs = run_decile_tests(
        config,
        args.expert,
        synthetic_sample=args.synthetic_sample,
        unlock_true_holdout=args.unlock_true_holdout,
    )
    print(f"Decile tests complete: {len(outputs)} expert result file(s)")
    for output in outputs:
        print(output.results_path)
    return 0


def _cmd_run_multisymbol(args: argparse.Namespace) -> int:
    config = load_project_config(args.root)
    validate_hypotheses(config)
    outputs = run_multisymbol_checks(
        config,
        args.expert,
        synthetic_sample=args.synthetic_sample,
        broker=args.broker,
        cost_model=args.cost_model,
        unlock_true_holdout=args.unlock_true_holdout,
    )
    print(f"Multisymbol checks complete: {len(outputs)} expert summary file(s)")
    for output in outputs:
        print(output.summary_path)
        for trades_path in output.trades_paths:
            print(trades_path)
    return 0


def _cmd_create_adversarial_packets(args: argparse.Namespace) -> int:
    config = load_project_config(args.root)
    outputs = create_adversarial_packets(config, args.expert)
    print(f"Adversarial packets complete: {len(outputs)} expert review file(s)")
    for output in outputs:
        print(f"{output.review_path} ({output.selected_trades}/{output.losing_trades} losing trade(s))")
    return 0


def _cmd_generate_verdict(args: argparse.Namespace) -> int:
    config = load_project_config(args.root)
    output = generate_all_reports(config)
    print(f"Generated {len(output.expert_reports)} expert report(s)")
    for report in output.expert_reports:
        print(report.report_path)
    print(output.verdict_path)
    return 0


def _cmd_generate_result_manifest(args: argparse.Namespace) -> int:
    config = load_project_config(args.root)
    output_path = generate_result_manifest(config)
    print(f"Result manifest: {output_path}")
    return 0


def _cmd_generate_snapshot(args: argparse.Namespace) -> int:
    config = load_project_config(args.root)
    output = generate_snapshot(config, include_raw_data=args.include_raw_data)
    print(f"Snapshot created: {output.snapshot_path}")
    print(f"Included files: {len(output.included_files)}")
    return 0


def _cmd_analyze_spread_logs(args: argparse.Namespace) -> int:
    config = load_project_config(args.root)
    output = analyze_spread_logs(config, input_dir=args.input_dir, file_glob=args.glob)
    print(f"Analyzed {len(output.source_files)} spread log file(s)")
    print(output.measured_cost_model_path)
    print(output.report_path)
    return 0


def _cmd_run_all(args: argparse.Namespace) -> int:
    config = load_project_config(args.root)
    output = run_all_phase0(
        config,
        synthetic_sample=args.synthetic_sample,
        unlock_true_holdout=args.unlock_true_holdout,
    )
    print("Run-all complete")
    print(f"Matrix output sets: {len(output.matrix_outputs)}")
    print(f"Decile files: {len(output.decile_outputs)}")
    print(f"Multisymbol summaries: {len(output.multisymbol_outputs)}")
    print(f"Adversarial packets: {len(output.adversarial_outputs)}")
    print(f"Aggregation files: {len(output.aggregation_outputs)}")
    print(output.report_output.verdict_path)
    print(output.result_manifest_path)
    return 0


def _add_broker_symbol_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--broker", required=True)
    parser.add_argument("--symbol", required=True)


def _enabled_experts(phase0: dict) -> list[str]:
    return [name for name, details in phase0["experts"].items() if details.get("enabled")]

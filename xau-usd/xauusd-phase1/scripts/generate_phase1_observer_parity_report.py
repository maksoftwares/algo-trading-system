from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


DEFAULT_REPORT = Path("outputs") / "reports" / "PHASE1_OBSERVER_PARITY_REPORT.md"
PHASE1_OBSERVER = Path("mt5") / "Include" / "Phase1" / "Phase1BreakoutRetest.mqh"
PHASE0_STRATEGY = Path("src") / "phase0" / "strategies" / "breakout_retest.py"


@dataclass(frozen=True)
class ParityCheck:
    name: str
    status: str
    evidence: str


@dataclass(frozen=True)
class ParityReport:
    status: str
    report_path: Path
    checks: tuple[ParityCheck, ...]


def generate_phase1_observer_parity_report(
    phase1_root: Path,
    report_path: Path | None = None,
    phase0_root: Path | None = None,
) -> ParityReport:
    phase1_root = phase1_root.resolve()
    if phase0_root is None:
        phase0_root = phase1_root.parent / "xauusd-phase0"
    phase0_root = phase0_root.resolve()
    if report_path is None:
        report_path = phase1_root / DEFAULT_REPORT
    report_path = report_path.resolve()

    observer_path = phase1_root / PHASE1_OBSERVER
    strategy_path = phase0_root / PHASE0_STRATEGY
    observer_text = _read_text(observer_path)
    strategy_text = _read_text(strategy_path)

    checks = [
        _file_check("Phase 1 MQL observer", observer_path),
        _file_check("Phase 0 Python strategy", strategy_path),
        _token_pair_check(
            "Break window",
            observer_text,
            strategy_text,
            "m_break_window_bars = 20",
            "retest_position - 20",
            "Both implementations use a 20-bar breakout lookback before the retest bar.",
        ),
        _token_pair_check(
            "Break ATR threshold",
            observer_text,
            strategy_text,
            "m_break_atr_multiplier = 0.30",
            "0.3 * break_atr",
            "Both require the break close to clear the level by 0.30 ATR.",
        ),
        _token_pair_check(
            "Retest tolerance",
            observer_text,
            strategy_text,
            "m_retest_tolerance_points = 5.0",
            "5.0 * point_size",
            "Both use a 5-point retest tolerance around the broken level.",
        ),
        _token_pair_check(
            "Stop ATR buffer",
            observer_text,
            strategy_text,
            "m_stop_atr_multiplier = 0.10",
            "0.1 * retest_atr",
            "Both place the stop with a 0.10 ATR retest-bar buffer.",
        ),
        _token_pair_check(
            "Reward multiple",
            observer_text,
            strategy_text,
            "m_reward_multiple = 1.50",
            "1.5 * risk_price",
            "Both use a 1.5R target from entry-to-stop risk.",
        ),
        _all_tokens_check(
            "Level universe",
            observer_text,
            (
                "previous_daily_high",
                "previous_weekly_high",
                "latest_swing_high",
                "previous_daily_low",
                "previous_weekly_low",
                "latest_swing_low",
            ),
            "MQL observer evaluates daily, weekly, and latest-swing levels for both directions.",
        ),
        _all_tokens_check(
            "Python level universe",
            strategy_text,
            (
                "previous_daily_high",
                "previous_weekly_high",
                "latest_swing_high",
                "previous_daily_low",
                "previous_weekly_low",
                "latest_swing_low",
            ),
            "Python strategy evaluates the same daily, weekly, and latest-swing levels.",
        ),
        _token_pair_check(
            "Duplicate-level tolerance",
            observer_text,
            strategy_text,
            "10.0 * point",
            "10.0 * point_size",
            "Both collapse duplicate candidate levels within 10 points.",
        ),
        _token_pair_check(
            "Candidate selection",
            observer_text,
            strategy_text,
            "candidate.stop_distance_points < best.stop_distance_points",
            "item[\"stop_distance\"]",
            "Both select the lowest stop-distance candidate when multiple levels qualify.",
        ),
        _token_pair_check(
            "Dry-run reason-code mapping",
            observer_text,
            strategy_text,
            "BREAKOUT_RETEST_LONG_DRY_RUN",
            "BREAKOUT_RETEST_LONG",
            "Phase 1 preserves the Phase 0 reason-code stem and adds an explicit dry-run suffix.",
        ),
    ]
    status = _overall_status(checks)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render_report(status, phase1_root, phase0_root, checks), encoding="utf-8")
    return ParityReport(status, report_path, tuple(checks))


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _file_check(name: str, path: Path) -> ParityCheck:
    if path.exists() and path.stat().st_size > 0:
        return ParityCheck(name, "PASS", f"Found `{path}`.")
    return ParityCheck(name, "FAIL", f"Missing or empty `{path}`.")


def _token_pair_check(
    name: str,
    observer_text: str,
    strategy_text: str,
    observer_token: str,
    strategy_token: str,
    evidence: str,
) -> ParityCheck:
    missing = []
    if observer_token not in observer_text:
        missing.append(f"MQL token `{observer_token}`")
    if strategy_token not in strategy_text:
        missing.append(f"Python token `{strategy_token}`")
    if missing:
        return ParityCheck(name, "FAIL", "Missing " + ", ".join(missing) + ".")
    return ParityCheck(name, "PASS", evidence)


def _all_tokens_check(name: str, text: str, tokens: tuple[str, ...], evidence: str) -> ParityCheck:
    missing = [token for token in tokens if token not in text]
    if missing:
        return ParityCheck(name, "FAIL", "Missing token(s): " + ", ".join(f"`{token}`" for token in missing) + ".")
    return ParityCheck(name, "PASS", evidence)


def _overall_status(checks: list[ParityCheck]) -> str:
    if any(check.status == "FAIL" for check in checks):
        return "FAIL"
    return "PASS"


def _render_report(
    status: str,
    phase1_root: Path,
    phase0_root: Path,
    checks: list[ParityCheck],
) -> str:
    return "\n".join(
        [
            "# Phase 1 Observer Parity Report",
            "",
            f"Overall status: {status}",
            "",
            "## Scope",
            "",
            (
                "This report proves source-level parity between the Phase 1 MQL "
                "`breakout_retest` observer and the Phase 0 Python `breakout_retest` strategy. "
                "A PASS report is required before Phase 2 paper-mode implementation can begin."
            ),
            "",
            "## Inputs",
            "",
            f"- Phase 1 root: `{phase1_root}`",
            f"- Phase 0 root: `{phase0_root}`",
            "",
            "## Checks",
            "",
            _markdown_table(
                [{"Check": item.name, "Status": item.status, "Evidence": item.evidence} for item in checks],
                ["Check", "Status", "Evidence"],
            ),
            "",
            "## Boundary",
            "",
            "- This is parity evidence only; it does not authorize paper mode or live trading.",
            "- Runtime would-signal review still remains a separate Phase 1 evidence gate.",
            "",
        ]
    )


def _markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    if not rows:
        return "No rows."
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(_escape(str(row.get(column, ""))) for column in columns) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the Phase 1 observer parity report.")
    parser.add_argument(
        "--phase1-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Phase 1 workspace root.",
    )
    parser.add_argument("--phase0-root", type=Path, default=None, help="Phase 0 workspace root.")
    parser.add_argument("--report", type=Path, default=None, help="Markdown report path.")
    args = parser.parse_args(argv)

    output = generate_phase1_observer_parity_report(args.phase1_root, args.report, args.phase0_root)
    print(f"Phase 1 observer parity report: {output.status}")
    print(output.report_path)
    for check in output.checks:
        print(f"{check.status}: {check.name} - {check.evidence}")
    return 1 if output.status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())

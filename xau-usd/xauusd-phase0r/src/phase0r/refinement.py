from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from phase0r.cost_feasibility import DEFAULT_SPREAD_ASSUMPTIONS
from phase0r.hypothesis_lock import locked_hypotheses_match_manifest


DEFAULT_ACTUAL_TRADE_LOG = Path("outputs") / "reports" / "PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv"
DEFAULT_SIGNAL_LEDGER = Path("outputs") / "reports" / "DEMO_14_EA_ALL_TRADES_REFRESHED.csv"
DEFAULT_PASSIVE_COST_LOG = Path("outputs") / "paper_observer" / "passive_cost_observer_log.csv"
DEFAULT_REPORT_DIR = Path("outputs") / "reports"

LOSS_CLASSES = (
    "VALID_LOSS",
    "SPREAD_COST_DAMAGE",
    "STOP_TOO_TIGHT_FOR_COST",
    "DUPLICATE_FAMILY_SIGNAL",
    "SESSION_CONTEXT_PROBLEM",
    "HTF_CONTEXT_MISMATCH",
    "ROUTER_OPPORTUNITY",
    "EXECUTION_AMBIGUITY",
    "DATA_ISSUE",
    "LOGIC_GAP",
)

REPORT_FILENAMES = {
    "performance": "DEMO_EA_PERFORMANCE_REVIEW.md",
    "deduped": "DEMO_EA_DEDUPED_PERFORMANCE_REVIEW.md",
    "expectancy": "EA_WIN_RATE_EXPECTANCY_REPORT.md",
    "loss_quality": "EA_LOSS_QUALITY_REPORT.md",
    "cost_bucket": "EA_COST_R_BUCKET_REPORT.md",
    "session_bucket": "EA_SESSION_BUCKET_REPORT.md",
    "stop_bucket": "EA_STOP_DISTANCE_BUCKET_REPORT.md",
    "duplicate_family": "EA_DUPLICATE_FAMILY_SIGNAL_REPORT.md",
    "vnext": "EA_CANDIDATE_VNEXT_PROPOSALS.md",
    "promotion_blockers": "EA_PROMOTION_BLOCKERS.md",
    "manifest": "EA_REFINEMENT_REPORTS.json",
}

CANDIDATE_PRIORITY = {
    "breakout_retest": 0,
    "symbol_normalized_round_retest_v0": 1,
    "swing_breakout_retest_v0": 2,
    "round_number_retest_v0": 3,
    "session_extreme_retest_v0": 4,
}

VNEXT_PROPOSALS = (
    {
        "proposed_name": "round_number_retest_v1_cost_aware",
        "status": "DRAFT_UNREGISTERED",
        "parent_candidate": "round_number_retest_v0",
        "failure_reason_addressed": "Same-family retest signals duplicated canonical exposure and remain cost-sensitive under measured spread.",
        "market_mechanics_justification": "Round-number retests may still matter on XAUUSD, but only when stop geometry is wide enough and the level has fresh intraday participation.",
        "expected_median_stop_distance": "500-800 points",
        "expected_trade_count": "Lower than v0; target enough rows for Phase 0R matrix gates before any promotion discussion.",
        "expected_hold_time": "M15-H1 observation, usually under one session.",
        "expected_cost_r": "<=0.15R median, <=0.30R p95 required before matrix scoring.",
        "required_validation_gates": "New locked hypothesis, structural cost precheck, 9-cell matrix, deciles, measured-cost revalidation, duplicate-family audit.",
    },
    {
        "proposed_name": "session_extreme_retest_v1_htf_confirmed",
        "status": "DRAFT_REGISTERED_NOT_LOCKED",
        "parent_candidate": "session_extreme_retest_v0",
        "failure_reason_addressed": "Weak early win rate and losses clustered in a provisional same-family lane.",
        "market_mechanics_justification": "Session extremes are more defensible when aligned with higher-timeframe rejection or failed auction evidence.",
        "expected_median_stop_distance": "450-700 points",
        "expected_trade_count": "Lower activity than v0; enough cross-session samples required.",
        "expected_hold_time": "One to three sessions.",
        "expected_cost_r": "<=0.20R median and <=0.30R p95.",
        "required_validation_gates": "HTF context rule locked before test, session bucket survival, loss-quality review, standard Phase 0R gates.",
    },
    {
        "proposed_name": "h4_d1_contraction_expansion_v1_directional",
        "status": "DRAFT_UNREGISTERED",
        "parent_candidate": "h4_d1_volatility_contraction_expansion_v0",
        "failure_reason_addressed": "Cost precheck passed, but first-pass matrix showed no durable edge.",
        "market_mechanics_justification": "Compression release needs a pre-registered directional mechanism instead of a generic expansion trigger.",
        "expected_median_stop_distance": "500-900 points",
        "expected_trade_count": "Low-to-moderate; H4/D1 only.",
        "expected_hold_time": "24-96 hours.",
        "expected_cost_r": "<=0.15R median and <=0.25R p95.",
        "required_validation_gates": "Directional filter rationale, no wick-only breakouts, 9-cell matrix, deciles, measured-cost sensitivity.",
    },
    {
        "proposed_name": "gld_flow_reversal_v2_satellite",
        "status": "DRAFT_UNREGISTERED",
        "parent_candidate": "h4_gld_etf_flow_reversal_v0",
        "failure_reason_addressed": "Interesting PF cells but failed activity, trade-count, and concentration gates.",
        "market_mechanics_justification": "GLD-flow behavior may work as a context or satellite signal rather than a primary entry engine.",
        "expected_median_stop_distance": "400-700 points",
        "expected_trade_count": "Low frequency by design; satellite classification must be pre-registered.",
        "expected_hold_time": "H4 to D1 holding window.",
        "expected_cost_r": "<=0.25R p95.",
        "required_validation_gates": "Satellite gate set, concentration-in-R review, out-of-sample review, no standalone allocation approval.",
    },
    {
        "proposed_name": "macro_context_router_filter_v0",
        "status": "DRAFT_UNREGISTERED",
        "parent_candidate": "failed macro/intermarket standalone candidates",
        "failure_reason_addressed": "Standalone macro candidates lacked direct entry edge but may explain adverse regimes.",
        "market_mechanics_justification": "Macro context is better tested as an exposure filter or regime label than as a direct entry trigger.",
        "expected_median_stop_distance": "n/a, no entries generated",
        "expected_trade_count": "n/a, filter only",
        "expected_hold_time": "Context window only",
        "expected_cost_r": "n/a, should reduce cost exposure instead of adding rows",
        "required_validation_gates": "Router-only hypothesis, no entry generation, blocked-opportunity audit, out-of-sample impact review.",
    },
)


@dataclass(frozen=True)
class RefinementData:
    phase0r_root: Path
    phase1_root: Path
    actual_rows: tuple[dict[str, str], ...]
    signal_rows: tuple[dict[str, str], ...]
    passive_rows: tuple[dict[str, str], ...]
    actual_log_path: Path | None
    signal_log_path: Path | None
    passive_log_path: Path | None
    synthetic_sample: bool = False


@dataclass(frozen=True)
class RefinementReportOutput:
    report_paths: tuple[Path, ...]
    manifest_path: Path
    actual_rows: int
    signal_rows: int
    passive_rows: int


def load_refinement_data(
    phase0r_root: Path,
    phase1_root: Path | None = None,
    *,
    actual_log_path: Path | None = None,
    signal_log_path: Path | None = None,
    passive_log_path: Path | None = None,
    synthetic_sample: bool = False,
) -> RefinementData:
    phase0r_root = phase0r_root.resolve()
    phase1_root = (phase1_root or phase0r_root.parent / "xauusd-phase1").resolve()
    if synthetic_sample:
        actual_rows, signal_rows, passive_rows = synthetic_demo_rows()
        return RefinementData(
            phase0r_root=phase0r_root,
            phase1_root=phase1_root,
            actual_rows=tuple(actual_rows),
            signal_rows=tuple(signal_rows),
            passive_rows=tuple(passive_rows),
            actual_log_path=None,
            signal_log_path=None,
            passive_log_path=None,
            synthetic_sample=True,
        )

    actual_log_path = (actual_log_path or phase1_root / DEFAULT_ACTUAL_TRADE_LOG).resolve()
    signal_log_path = (signal_log_path or phase1_root / DEFAULT_SIGNAL_LEDGER).resolve()
    passive_log_path = (passive_log_path or phase1_root / DEFAULT_PASSIVE_COST_LOG).resolve()
    return RefinementData(
        phase0r_root=phase0r_root,
        phase1_root=phase1_root,
        actual_rows=tuple(_read_csv(actual_log_path)),
        signal_rows=tuple(_read_csv(signal_log_path)),
        passive_rows=tuple(_read_csv(passive_log_path)),
        actual_log_path=actual_log_path,
        signal_log_path=signal_log_path,
        passive_log_path=passive_log_path,
        synthetic_sample=False,
    )


def generate_all_refinement_reports(
    data: RefinementData,
    report_dir: Path | None = None,
) -> RefinementReportOutput:
    report_dir = (report_dir or data.phase0r_root / DEFAULT_REPORT_DIR).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)
    writers = (
        write_demo_ea_performance_review,
        write_demo_ea_deduped_review,
        write_ea_win_rate_expectancy_report,
        write_ea_loss_quality_report,
        write_ea_cost_r_bucket_report,
        write_ea_session_bucket_report,
        write_ea_stop_distance_bucket_report,
        write_ea_duplicate_family_signal_report,
        write_vnext_candidate_proposals,
        write_promotion_blockers_report,
    )
    report_paths = tuple(writer(data, report_dir) for writer in writers)
    manifest_path = report_dir / REPORT_FILENAMES["manifest"]
    manifest = {
        "status": "REFINEMENT_RESEARCH_ONLY",
        "created_at_utc": _now(),
        "synthetic_sample": data.synthetic_sample,
        "actual_rows": len(data.actual_rows),
        "signal_rows": len(data.signal_rows),
        "passive_rows": len(data.passive_rows),
        "canonical_phase2_authorized": False,
        "locked_candidates_modified": False,
        "source_paths": {
            "actual_log": "" if data.actual_log_path is None else str(data.actual_log_path),
            "signal_ledger": "" if data.signal_log_path is None else str(data.signal_log_path),
            "passive_cost_log": "" if data.passive_log_path is None else str(data.passive_log_path),
        },
        "report_paths": {path.name: str(path) for path in report_paths},
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return RefinementReportOutput(
        report_paths=report_paths,
        manifest_path=manifest_path,
        actual_rows=len(data.actual_rows),
        signal_rows=len(data.signal_rows),
        passive_rows=len(data.passive_rows),
    )


def write_demo_ea_performance_review(data: RefinementData, report_dir: Path | None = None) -> Path:
    report_dir = _report_dir(data, report_dir)
    path = report_dir / REPORT_FILENAMES["performance"]
    signal_events = _primary_signal_events(data)
    actual_events = _actual_events(data)
    duplicate_events = duplicate_family_signals(actual_events or signal_events)
    duplicate_ids = {id(item["event"]) for item in duplicate_events if item["role"] == "duplicate"}
    rows = _performance_rows(signal_events, actual_events, duplicate_ids)
    headline = _performance_headline(actual_events, signal_events)

    lines = [
        "# Demo EA Performance Review",
        "",
        f"Generated at UTC: {_now()}",
        "",
        "Status: REFINEMENT_RESEARCH_ONLY",
        "",
        "This report diagnoses demo and passive observer evidence. It does not modify any locked candidate, does not approve current EAs, and does not change Phase 2 readiness.",
        "",
        "Actual P/L is read from the demo broker ledger when present. Estimated R is a proxy from demo signal or passive observer rows.",
        "",
        "## Sources",
        "",
        _source_table(data),
        "",
        "## Headline",
        "",
        _table(
            ("Metric", "Value"),
            [
                ("Actual trades", headline["actual_trades"]),
                ("Closed actual trades", headline["closed_actual_trades"]),
                ("Open actual trades", headline["open_actual_trades"]),
                ("Closed win rate", _fmt_pct(headline["closed_win_rate"])),
                ("Closed P/L AED", _fmt_num(headline["closed_pnl_aed"])),
                ("Open P/L AED", _fmt_num(headline["open_pnl_aed"])),
                ("Total P/L AED", _fmt_num(headline["total_pnl_aed"])),
                ("Signal rows used", len(signal_events)),
                ("Duplicate family rows detected", len(duplicate_events)),
            ],
        ),
        "",
        "## Candidate / Symbol / Date Detail",
        "",
        _table(
            (
                "candidate",
                "symbol",
                "status",
                "date",
                "signals",
                "trades",
                "closed",
                "open",
                "win_rate",
                "closed_pnl_aed",
                "open_pnl_aed",
                "duplicate_count",
                "net_expectancy_proxy_R",
            ),
            [
                (
                    row["candidate"],
                    row["symbol"],
                    row["status"],
                    row["date"],
                    row["signals"],
                    row["trades"],
                    row["closed"],
                    row["open"],
                    _fmt_pct(row["win_rate"]),
                    _fmt_num(row["closed_pnl_aed"]),
                    _fmt_num(row["open_pnl_aed"]),
                    row["duplicate_count"],
                    _fmt_num(row["net_expectancy_proxy_r"]),
                )
                for row in rows
            ],
        ),
        "",
        "## Interpretation Guardrails",
        "",
        "- Small demo samples can diagnose cost, duplicate, and loss-quality issues.",
        "- They are not direct optimization input for locked candidates.",
        "- New ideas must become versioned draft hypotheses before testing.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_demo_ea_deduped_review(data: RefinementData, report_dir: Path | None = None) -> Path:
    report_dir = _report_dir(data, report_dir)
    path = report_dir / REPORT_FILENAMES["deduped"]
    base_events = _actual_events(data) or _primary_signal_events(data)
    deduped, details = dedupe_family_events(base_events)
    raw_summary = _actual_money_summary(base_events)
    deduped_summary = _actual_money_summary(deduped)
    detail_rows = _dedupe_detail_rows(details)

    lines = [
        "# Demo EA Deduped Performance Review",
        "",
        f"Generated at UTC: {_now()}",
        "",
        "Status: REFINEMENT_RESEARCH_ONLY",
        "",
        "This report removes same-family overlap by bar, direction, level, and symbol. It identifies a primary row for analysis only; it does not authorize or prioritize execution.",
        "",
        "## Raw vs Deduped",
        "",
        _table(
            ("view", "rows", "closed", "open", "win_rate", "closed_pnl_aed", "open_pnl_aed", "total_pnl_aed"),
            [
                _money_summary_table_row("raw", raw_summary),
                _money_summary_table_row("deduped", deduped_summary),
            ],
        ),
        "",
        "## Primary Selection Logic",
        "",
        "Primary selection prefers an existing kept marker, then canonical same-family priority, accepted status, lower cost_R, and stable candidate ordering. This is a research baseline only.",
        "",
        "## Duplicate Groups",
        "",
        _table(
            ("group_key", "primary_candidate", "duplicate_candidates", "rows", "symbol", "direction", "bar"),
            detail_rows[:50],
        ),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_ea_win_rate_expectancy_report(data: RefinementData, report_dir: Path | None = None) -> Path:
    report_dir = _report_dir(data, report_dir)
    path = report_dir / REPORT_FILENAMES["expectancy"]
    rows = _expectancy_rows(_r_bearing_events(data))
    lines = [
        "# EA Win Rate Expectancy Report",
        "",
        f"Generated at UTC: {_now()}",
        "",
        "Status: REFINEMENT_RESEARCH_ONLY",
        "",
        "Win rate is secondary to net expectancy after measured cost. A high win rate can still lose money if average losses or cost_R dominate.",
        "",
        "Formula used for gross outcome rows:",
        "",
        "`expected_R = (win_rate * avg_win_R) - ((1 - win_rate) * abs(avg_loss_R)) - cost_R`",
        "",
        "`break_even_win_rate = abs(avg_loss_R) / (avg_win_R + abs(avg_loss_R))`",
        "",
        "## Candidate Expectancy",
        "",
        _table(
            (
                "candidate",
                "symbol",
                "rows",
                "win_rate",
                "avg_win_R",
                "avg_loss_R",
                "payoff_ratio",
                "avg_cost_R",
                "net_expectancy_R",
                "formula_expectancy_R",
                "break_even_win_rate",
            ),
            [
                (
                    row["candidate"],
                    row["symbol"],
                    row["rows"],
                    _fmt_pct(row["win_rate"]),
                    _fmt_num(row["avg_win_r"]),
                    _fmt_num(row["avg_loss_r"]),
                    _fmt_num(row["payoff_ratio"]),
                    _fmt_num(row["avg_cost_r"]),
                    _fmt_num(row["net_expectancy_r"]),
                    _fmt_num(row["formula_expectancy_r"]),
                    _fmt_pct(row["break_even_win_rate"]),
                )
                for row in rows
            ],
        ),
        "",
        "Rows without R information are excluded from this table. Actual P/L rows remain useful for the performance report, but they do not define R expectancy unless a risk unit is present.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_ea_loss_quality_report(data: RefinementData, report_dir: Path | None = None) -> Path:
    report_dir = _report_dir(data, report_dir)
    path = report_dir / REPORT_FILENAMES["loss_quality"]
    events = _diagnostic_events(data)
    loss_rows = [event for event in events if _is_loss(event)]
    counts = _loss_quality_rows(loss_rows)
    example_rows = _loss_examples(loss_rows)

    lines = [
        "# EA Loss Quality Report",
        "",
        f"Generated at UTC: {_now()}",
        "",
        "Status: REFINEMENT_RESEARCH_ONLY",
        "",
        "Loss labels are diagnostics. They do not auto-approve, auto-reject, or tune any current candidate.",
        "",
        "## Loss-Class Counts",
        "",
        _table(
            ("candidate", "symbol", "losses", *LOSS_CLASSES),
            [
                (
                    row["candidate"],
                    row["symbol"],
                    row["losses"],
                    *[row[class_name] for class_name in LOSS_CLASSES],
                )
                for row in counts
            ],
        ),
        "",
        "## Example Losses",
        "",
        _table(
            ("candidate", "symbol", "timestamp", "class", "net_R", "pnl_aed", "cost_R", "stop_points", "session"),
            example_rows[:50],
        ),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_ea_cost_r_bucket_report(data: RefinementData, report_dir: Path | None = None) -> Path:
    report_dir = _report_dir(data, report_dir)
    path = report_dir / REPORT_FILENAMES["cost_bucket"]
    rows = _bucket_rows(_cost_bearing_events(data), bucket_func=cost_r_bucket, bucket_field="cost_bucket")
    lines = [
        "# EA Cost R Bucket Report",
        "",
        f"Generated at UTC: {_now()}",
        "",
        "Status: REFINEMENT_RESEARCH_ONLY",
        "",
        "Cost_R buckets show where measured or projected transaction cost consumes the edge. Rows can be signals or actual trades depending on available source fields.",
        "",
        "## Cost_R Buckets",
        "",
        _table(
            ("candidate", "symbol", "bucket", "rows", "win_rate", "avg_cost_R", "expectancy_R_proxy", "avg_pnl_aed"),
            [
                (
                    row["candidate"],
                    row["symbol"],
                    row["bucket"],
                    row["rows"],
                    _fmt_pct(row["win_rate"]),
                    _fmt_num(row["avg_cost_r"]),
                    _fmt_num(row["expectancy_r"]),
                    _fmt_num(row["avg_pnl_aed"]),
                )
                for row in rows
            ],
        ),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_ea_session_bucket_report(data: RefinementData, report_dir: Path | None = None) -> Path:
    report_dir = _report_dir(data, report_dir)
    path = report_dir / REPORT_FILENAMES["session_bucket"]
    rows = _session_rows(_diagnostic_events(data))
    lines = [
        "# EA Session Bucket Report",
        "",
        f"Generated at UTC: {_now()}",
        "",
        "Status: REFINEMENT_RESEARCH_ONLY",
        "",
        "Session buckets help identify loss and cost clustering. They are hypothesis-generation evidence only.",
        "",
        _table(
            ("candidate", "symbol", "session", "rows", "losses", "win_rate", "avg_cost_R", "expectancy_R_proxy", "avg_pnl_aed"),
            [
                (
                    row["candidate"],
                    row["symbol"],
                    row["session"],
                    row["rows"],
                    row["losses"],
                    _fmt_pct(row["win_rate"]),
                    _fmt_num(row["avg_cost_r"]),
                    _fmt_num(row["expectancy_r"]),
                    _fmt_num(row["avg_pnl_aed"]),
                )
                for row in rows
            ],
        ),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_ea_stop_distance_bucket_report(data: RefinementData, report_dir: Path | None = None) -> Path:
    report_dir = _report_dir(data, report_dir)
    path = report_dir / REPORT_FILENAMES["stop_bucket"]
    rows = _bucket_rows(_stop_bearing_events(data), bucket_func=stop_distance_bucket, bucket_field="stop_bucket")
    p95_spread = float(DEFAULT_SPREAD_ASSUMPTIONS.measured_p95_spread_points)
    lines = [
        "# EA Stop Distance Bucket Report",
        "",
        f"Generated at UTC: {_now()}",
        "",
        "Status: REFINEMENT_RESEARCH_ONLY",
        "",
        f"Measured P95 spread reference: {p95_spread:.2f} points.",
        "",
        "The flag column is raised when P95 spread is greater than 30% of the stop distance or when the stop bucket is structurally tight.",
        "",
        _table(
            (
                "candidate",
                "symbol",
                "bucket",
                "rows",
                "win_rate",
                "avg_stop_points",
                "avg_cost_R",
                "expectancy_R_proxy",
                "p95_spread_flag",
            ),
            [
                (
                    row["candidate"],
                    row["symbol"],
                    row["bucket"],
                    row["rows"],
                    _fmt_pct(row["win_rate"]),
                    _fmt_num(row["avg_stop_points"]),
                    _fmt_num(row["avg_cost_r"]),
                    _fmt_num(row["expectancy_r"]),
                    row["p95_spread_flag"],
                )
                for row in rows
            ],
        ),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_ea_duplicate_family_signal_report(data: RefinementData, report_dir: Path | None = None) -> Path:
    report_dir = _report_dir(data, report_dir)
    path = report_dir / REPORT_FILENAMES["duplicate_family"]
    base_events = _actual_events(data) or _primary_signal_events(data)
    _deduped, details = dedupe_family_events(base_events)
    detail_rows = _dedupe_detail_rows(details)
    by_candidate = Counter()
    for detail in details:
        for event in detail["duplicates"]:
            by_candidate[str(event["candidate"])] += 1

    lines = [
        "# EA Duplicate Family Signal Report",
        "",
        f"Generated at UTC: {_now()}",
        "",
        "Status: REFINEMENT_RESEARCH_ONLY",
        "",
        "Same-family duplicates are counted as exposure-quality problems, not diversification.",
        "",
        "## Duplicate Counts By Candidate",
        "",
        _table(("candidate", "duplicate_rows"), sorted(by_candidate.items())),
        "",
        "## Duplicate Groups",
        "",
        _table(
            ("group_key", "primary_candidate", "duplicate_candidates", "rows", "symbol", "direction", "bar"),
            detail_rows[:80],
        ),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_vnext_candidate_proposals(data: RefinementData, report_dir: Path | None = None) -> Path:
    report_dir = _report_dir(data, report_dir)
    path = report_dir / REPORT_FILENAMES["vnext"]
    lines = [
        "# EA Candidate vNext Proposals",
        "",
        f"Generated at UTC: {_now()}",
        "",
        "Status: VNEXT_RESEARCH_ONLY",
        "",
        "These are proposal sketches and draft registrations only. They must not run until the owner explicitly approves the next gate.",
        "",
    ]
    for proposal in VNEXT_PROPOSALS:
        lines.extend(
            [
                f"## {proposal['proposed_name']}",
                "",
                f"Status: {proposal.get('status', 'DRAFT_UNREGISTERED')}",
                "",
                _table(
                    ("Field", "Value"),
                    [
                        ("Proposed name", proposal["proposed_name"]),
                        ("Status", proposal.get("status", "DRAFT_UNREGISTERED")),
                        ("Parent candidate", proposal["parent_candidate"]),
                        ("Failure reason addressed", proposal["failure_reason_addressed"]),
                        ("Market-mechanics justification", proposal["market_mechanics_justification"]),
                        ("Expected median stop distance", proposal["expected_median_stop_distance"]),
                        ("Expected trade count", proposal["expected_trade_count"]),
                        ("Expected hold time", proposal["expected_hold_time"]),
                        ("Expected cost_R", proposal["expected_cost_r"]),
                        ("Required validation gates", proposal["required_validation_gates"]),
                    ],
                ),
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_promotion_blockers_report(data: RefinementData, report_dir: Path | None = None) -> Path:
    report_dir = _report_dir(data, report_dir)
    path = report_dir / REPORT_FILENAMES["promotion_blockers"]
    readiness_path = data.phase1_root / "outputs" / "reports" / "PHASE2_READINESS_REPORT.md"
    readiness_status = _readiness_status(readiness_path)
    duplicate_count = len(duplicate_family_signals(_actual_events(data) or _primary_signal_events(data)))
    high_cost_rows = sum(1 for event in _cost_bearing_events(data) if (event.get("cost_r") or 0.0) > 0.30)
    tight_stop_rows = sum(1 for event in _stop_bearing_events(data) if _stop_flag(event))
    lines = [
        "# EA Promotion Blockers",
        "",
        f"Generated at UTC: {_now()}",
        "",
        "Status: PHASE2_REMAINS_BLOCKED_REFINEMENT_RESEARCH_ONLY",
        "",
        "This report intentionally preserves the current promotion discipline. It is not a readiness override.",
        "",
        _table(
            ("Blocker", "Current read"),
            [
                ("Phase 2 readiness", readiness_status),
                ("Project owner approval", "Required before any Phase 2 status change"),
                ("Measured-cost discipline", "Must pass objective gates, not demo impressions"),
                ("Duplicate-family exposure", f"{duplicate_count} same-family duplicate rows detected"),
                ("High cost_R rows", high_cost_rows),
                ("Tight-stop / P95 spread rows", tight_stop_rows),
                ("vNext candidates", "Draft only, unregistered, not executed"),
            ],
        ),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def guard_no_locked_candidate_mutations(root: Path, manifest_path: Path | None = None) -> list[str]:
    errors = locked_hypotheses_match_manifest(root, manifest_path)
    if errors:
        return [
            *errors,
            "Locked hypotheses must stay unchanged. Create a separate versioned draft instead of editing the locked file.",
        ]
    return []


def break_even_win_rate(avg_win_r: float, avg_loss_r: float) -> float | None:
    avg_win_r = float(avg_win_r)
    avg_loss_abs = abs(float(avg_loss_r))
    denominator = avg_win_r + avg_loss_abs
    if denominator <= 0.0:
        return None
    return avg_loss_abs / denominator


def expectancy_after_cost(win_rate: float, avg_win_r: float, avg_loss_r: float, cost_r: float = 0.0) -> float:
    win_rate = float(win_rate)
    avg_win_r = float(avg_win_r)
    avg_loss_abs = abs(float(avg_loss_r))
    cost_r = float(cost_r)
    return (win_rate * avg_win_r) - ((1.0 - win_rate) * avg_loss_abs) - cost_r


def cost_r_bucket(cost_r: float | None) -> str:
    if cost_r is None:
        return "unknown"
    value = float(cost_r)
    if value <= 0.15:
        return "<=0.15R"
    if value <= 0.30:
        return "0.15R_to_0.30R"
    if value <= 0.50:
        return "0.30R_to_0.50R"
    return ">0.50R"


def stop_distance_bucket(stop_points: float | None) -> str:
    if stop_points is None:
        return "unknown"
    value = float(stop_points)
    if value < 250.0:
        return "<250"
    if value < 375.0:
        return "250_to_374"
    if value < 500.0:
        return "375_to_499"
    return "500_plus"


def synthetic_demo_rows() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    actual_rows = [
        {
            "entry_time": "2026-06-02 10:00:00",
            "exit_time": "2026-06-02 10:30:00",
            "candidate": "breakout_retest",
            "status": "ACCEPTED",
            "symbol": "XAUUSD",
            "direction": "BUY",
            "state": "CLOSED",
            "profit_aed": "30.00",
            "entry_price": "4520.00",
            "sl": "4514.00",
            "duplicate_key": "2026-06-02 10:00|XAUUSD|BUY|0.01",
            "duplicate_role": "kept",
            "is_duplicate": "false",
        },
        {
            "entry_time": "2026-06-02 10:00:01",
            "exit_time": "2026-06-02 10:30:00",
            "candidate": "swing_breakout_retest_v0",
            "status": "ACCEPTED",
            "symbol": "XAUUSD",
            "direction": "BUY",
            "state": "CLOSED",
            "profit_aed": "28.00",
            "entry_price": "4520.10",
            "sl": "4514.00",
            "duplicate_key": "2026-06-02 10:00|XAUUSD|BUY|0.01",
            "duplicate_role": "duplicate",
            "is_duplicate": "true",
        },
        {
            "entry_time": "2026-06-02 11:00:00",
            "exit_time": "2026-06-02 11:15:00",
            "candidate": "session_extreme_retest_v0",
            "status": "PROVISIONAL",
            "symbol": "XAUUSD",
            "direction": "SELL",
            "state": "CLOSED",
            "profit_aed": "-18.00",
            "entry_price": "4530.00",
            "sl": "4532.00",
            "duplicate_key": "2026-06-02 11:00|XAUUSD|SELL|0.01",
            "duplicate_role": "unique",
            "is_duplicate": "false",
        },
    ]
    signal_rows = [
        {
            "timestamp_utc": "2026.06.02 10:00:00",
            "candidate": "breakout_retest",
            "candidate_status": "ACCEPTED",
            "symbol": "XAUUSD",
            "direction": "LONG",
            "entry_price": "4520.00",
            "stop_loss": "4514.00",
            "level_price": "4520.00",
            "stop_distance_points": "600",
            "spread_points": "50",
            "outcome": "WIN_TP",
            "estimated_r": "1.50",
            "estimated_pnl_aed": "150",
        },
        {
            "timestamp_utc": "2026.06.02 10:00:00",
            "candidate": "swing_breakout_retest_v0",
            "candidate_status": "ACCEPTED",
            "symbol": "XAUUSD",
            "direction": "LONG",
            "entry_price": "4520.10",
            "stop_loss": "4514.00",
            "level_price": "4520.00",
            "stop_distance_points": "610",
            "spread_points": "50",
            "outcome": "WIN_TP",
            "estimated_r": "1.45",
            "estimated_pnl_aed": "145",
        },
        {
            "timestamp_utc": "2026.06.02 11:00:00",
            "candidate": "session_extreme_retest_v0",
            "candidate_status": "PROVISIONAL",
            "symbol": "XAUUSD",
            "direction": "SHORT",
            "entry_price": "4530.00",
            "stop_loss": "4532.00",
            "level_price": "4530.00",
            "stop_distance_points": "200",
            "spread_points": "75",
            "outcome": "LOSS_STOP",
            "estimated_r": "-1.00",
            "estimated_pnl_aed": "-100",
        },
    ]
    passive_rows = [
        {
            "timestamp_utc": "2026-06-02 10:00:00",
            "symbol": "XAUUSD",
            "candidate": "breakout_retest",
            "candidate_family": "breakout_retest_family",
            "candidate_status": "ACCEPTED",
            "would_signal": "true",
            "signal_direction": "LONG",
            "intended_entry_price": "4520.00",
            "intended_stop_loss": "4514.00",
            "stop_distance_points": "600",
            "spread_points": "50",
            "estimated_total_cost_R": "0.0833",
            "estimated_gross_edge_R": "0.55",
            "estimated_net_edge_R": "0.4667",
            "session_label": "LONDON",
            "hour_utc": "10",
        },
        {
            "timestamp_utc": "2026-06-02 11:00:00",
            "symbol": "XAUUSD",
            "candidate": "session_extreme_retest_v0",
            "candidate_family": "breakout_retest_family",
            "candidate_status": "PROVISIONAL",
            "would_signal": "true",
            "signal_direction": "SHORT",
            "intended_entry_price": "4530.00",
            "intended_stop_loss": "4532.00",
            "stop_distance_points": "200",
            "spread_points": "75",
            "estimated_total_cost_R": "0.3750",
            "estimated_gross_edge_R": "0.15",
            "estimated_net_edge_R": "-0.2250",
            "session_label": "NY",
            "hour_utc": "11",
        },
    ]
    return actual_rows, signal_rows, passive_rows


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        return list(csv.DictReader(handle))


def _report_dir(data: RefinementData, report_dir: Path | None) -> Path:
    output = (report_dir or data.phase0r_root / DEFAULT_REPORT_DIR).resolve()
    output.mkdir(parents=True, exist_ok=True)
    return output


def _actual_events(data: RefinementData) -> list[dict[str, Any]]:
    return [_normalize_actual(row) for row in data.actual_rows]


def _primary_signal_events(data: RefinementData) -> list[dict[str, Any]]:
    if data.signal_rows:
        return [_normalize_signal(row) for row in data.signal_rows if _signal_row_is_event(row)]
    return [_normalize_passive(row) for row in data.passive_rows if _passive_row_is_signal(row)]


def _diagnostic_events(data: RefinementData) -> list[dict[str, Any]]:
    events = _actual_events(data)
    events.extend(_primary_signal_events(data))
    if data.signal_rows and data.passive_rows:
        events.extend(_normalize_passive(row) for row in data.passive_rows if _passive_row_is_signal(row))
    return events


def _r_bearing_events(data: RefinementData) -> list[dict[str, Any]]:
    return [event for event in _diagnostic_events(data) if event.get("net_r") is not None]


def _cost_bearing_events(data: RefinementData) -> list[dict[str, Any]]:
    return [event for event in _diagnostic_events(data) if event.get("cost_r") is not None]


def _stop_bearing_events(data: RefinementData) -> list[dict[str, Any]]:
    return [event for event in _diagnostic_events(data) if event.get("stop_points") is not None]


def _normalize_actual(row: dict[str, str]) -> dict[str, Any]:
    direction = _normalize_direction(row.get("direction"))
    pnl = _float(row.get("profit_aed") or row.get("profit"))
    state = (row.get("state") or "").upper()
    timestamp = row.get("entry_time") or row.get("timestamp") or row.get("timestamp_utc") or ""
    symbol = row.get("symbol") or "UNKNOWN"
    stop_points = _float(row.get("stop_distance_points"))
    if stop_points is None:
        stop_points = _stop_points_from_prices(symbol, row.get("entry_price"), row.get("sl") or row.get("stop_loss"))
    return {
        "source": "actual",
        "candidate": row.get("candidate") or "UNKNOWN",
        "family": _candidate_family(row.get("candidate"), row.get("candidate_family")),
        "status": row.get("status") or row.get("candidate_status") or "UNKNOWN",
        "symbol": symbol,
        "direction": direction,
        "timestamp": timestamp,
        "date": _date_key(timestamp),
        "bar": _bar_key(timestamp),
        "level": _level_key(row.get("level_price") or row.get("entry_price")),
        "state": state,
        "closed": state == "CLOSED",
        "open": state == "OPEN",
        "pnl_aed": pnl,
        "net_r": None,
        "cost_r": _float(row.get("cost_r")),
        "stop_points": stop_points,
        "spread_points": _float(row.get("spread_points")),
        "session": _session_from_row(row, timestamp),
        "duplicate_key": row.get("duplicate_key") or "",
        "duplicate_role": row.get("duplicate_role") or "",
        "is_duplicate": _truthy(row.get("is_duplicate")),
        "raw": row,
    }


def _normalize_signal(row: dict[str, str]) -> dict[str, Any]:
    timestamp = row.get("timestamp_utc") or row.get("timestamp_local") or row.get("timestamp") or ""
    symbol = row.get("symbol") or "UNKNOWN"
    direction = _normalize_direction(row.get("direction") or row.get("signal_direction"))
    stop_points = _float(row.get("stop_distance_points"))
    if stop_points is None:
        stop_points = _stop_points_from_prices(symbol, row.get("entry_price"), row.get("stop_loss"))
    spread_points = _float(row.get("spread_points"))
    cost_r = _float(row.get("cost_R") or row.get("cost_r") or row.get("estimated_total_cost_R"))
    if cost_r is None and stop_points and spread_points is not None and stop_points > 0:
        cost_r = spread_points / stop_points
    net_r = _float(row.get("estimated_r") or row.get("net_r") or row.get("estimated_net_edge_R"))
    pnl = _float(row.get("estimated_pnl_aed") or row.get("pnl_aed") or row.get("profit_aed"))
    outcome = row.get("outcome") or row.get("state") or ""
    return {
        "source": "signal_ledger",
        "candidate": row.get("candidate") or "UNKNOWN",
        "family": _candidate_family(row.get("candidate"), row.get("candidate_family")),
        "status": row.get("candidate_status") or row.get("status") or "UNKNOWN",
        "symbol": symbol,
        "direction": direction,
        "timestamp": timestamp,
        "date": _date_key(timestamp),
        "bar": _bar_key(timestamp),
        "level": _level_key(row.get("level_price") or row.get("entry_price")),
        "state": outcome,
        "closed": _outcome_is_closed(outcome),
        "open": _outcome_is_open(outcome),
        "pnl_aed": pnl,
        "net_r": net_r,
        "cost_r": cost_r,
        "stop_points": stop_points,
        "spread_points": spread_points,
        "session": _session_from_row(row, timestamp),
        "duplicate_key": row.get("duplicate_key") or "",
        "duplicate_role": row.get("duplicate_role") or "",
        "is_duplicate": _truthy(row.get("is_duplicate")),
        "raw": row,
    }


def _normalize_passive(row: dict[str, str]) -> dict[str, Any]:
    timestamp = row.get("timestamp_utc") or row.get("timestamp_broker") or ""
    symbol = row.get("symbol") or "UNKNOWN"
    direction = _normalize_direction(row.get("signal_direction") or row.get("direction"))
    stop_points = _float(row.get("stop_distance_points"))
    spread_points = _float(row.get("spread_points"))
    cost_r = _float(row.get("estimated_total_cost_R") or row.get("estimated_total_cost_r") or row.get("cost_r"))
    if cost_r is None and stop_points and spread_points is not None and stop_points > 0:
        cost_r = spread_points / stop_points
    return {
        "source": "passive_cost_log",
        "candidate": row.get("candidate") or "UNKNOWN",
        "family": _candidate_family(row.get("candidate"), row.get("candidate_family")),
        "status": row.get("candidate_status") or row.get("status") or "UNKNOWN",
        "symbol": symbol,
        "direction": direction,
        "timestamp": timestamp,
        "date": _date_key(timestamp),
        "bar": _bar_key(timestamp),
        "level": _level_key(row.get("level_price") or row.get("intended_entry_price") or row.get("entry_price")),
        "state": row.get("signal_stage") or "PASSIVE_SIGNAL",
        "closed": False,
        "open": False,
        "pnl_aed": None,
        "net_r": _float(row.get("estimated_net_edge_R") or row.get("estimated_net_edge_r") or row.get("net_r")),
        "gross_r": _float(row.get("estimated_gross_edge_R") or row.get("estimated_gross_edge_r") or row.get("gross_r")),
        "cost_r": cost_r,
        "stop_points": stop_points,
        "spread_points": spread_points,
        "session": _session_from_row(row, timestamp),
        "duplicate_key": row.get("duplicate_key") or "",
        "duplicate_role": row.get("duplicate_role") or "",
        "is_duplicate": _truthy(row.get("is_duplicate")),
        "raw": row,
    }


def _signal_row_is_event(row: dict[str, str]) -> bool:
    outcome = (row.get("outcome") or "").upper()
    if outcome and outcome not in {"NO_SIGNAL", "WAIT"}:
        return True
    return _truthy(row.get("would_signal"))


def _passive_row_is_signal(row: dict[str, str]) -> bool:
    raw = row.get("would_signal")
    return True if raw is None or raw == "" else _truthy(raw)


def dedupe_family_events(events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        groups[_duplicate_group_key(event)].append(event)

    deduped: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []
    for key, group in groups.items():
        if len(group) == 1:
            deduped.append(group[0])
            continue
        primary = _primary_event(group)
        duplicates = [event for event in group if event is not primary]
        deduped.append(primary)
        details.append(
            {
                "group_key": key,
                "primary": primary,
                "duplicates": duplicates,
                "rows": group,
            }
        )
    return deduped, details


def duplicate_family_signals(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    _deduped, details = dedupe_family_events(events)
    rows: list[dict[str, Any]] = []
    for detail in details:
        rows.append({"role": "primary", "event": detail["primary"], "group_key": detail["group_key"]})
        for event in detail["duplicates"]:
            rows.append({"role": "duplicate", "event": event, "group_key": detail["group_key"]})
    return rows


def classify_loss(event: dict[str, Any], duplicate_group_keys: set[str] | None = None) -> str:
    duplicate_group_keys = duplicate_group_keys or set()
    if not event.get("candidate") or event.get("candidate") == "UNKNOWN":
        return "DATA_ISSUE"
    if event.get("is_duplicate") or _duplicate_group_key(event) in duplicate_group_keys:
        return "DUPLICATE_FAMILY_SIGNAL"
    if _session_problem(event):
        return "SESSION_CONTEXT_PROBLEM"
    stop_points = event.get("stop_points")
    cost_r = event.get("cost_r")
    if cost_r is not None and float(cost_r) > 0.30:
        return "SPREAD_COST_DAMAGE"
    if stop_points is not None and _stop_flag(event):
        return "STOP_TOO_TIGHT_FOR_COST"
    if "HTF" in str(event.get("state", "")).upper():
        return "HTF_CONTEXT_MISMATCH"
    if "ROUTER" in str(event.get("candidate", "")).upper():
        return "ROUTER_OPPORTUNITY"
    if "snapshot" in str(event.get("raw", {})).lower():
        return "EXECUTION_AMBIGUITY"
    return "VALID_LOSS"


def _duplicate_group_key(event: dict[str, Any]) -> str:
    explicit = str(event.get("duplicate_key") or "").strip()
    if explicit:
        return explicit
    return "|".join(
        [
            str(event.get("family") or event.get("candidate") or "UNKNOWN"),
            str(event.get("symbol") or "UNKNOWN"),
            str(event.get("bar") or ""),
            str(event.get("direction") or ""),
            str(event.get("level") or ""),
        ]
    )


def _primary_event(group: list[dict[str, Any]]) -> dict[str, Any]:
    kept = [event for event in group if str(event.get("duplicate_role", "")).lower() == "kept"]
    if kept:
        return kept[0]
    return sorted(group, key=_primary_sort_key)[0]


def _primary_sort_key(event: dict[str, Any]) -> tuple[int, int, int, float, str]:
    status_rank = 0 if str(event.get("status", "")).upper() == "ACCEPTED" else 1
    candidate = str(event.get("candidate") or "")
    priority = CANDIDATE_PRIORITY.get(candidate, 99)
    cost = event.get("cost_r")
    cost_rank = float(cost) if cost is not None else 99.0
    return (status_rank, priority, 0 if not event.get("is_duplicate") else 1, cost_rank, candidate)


def _performance_headline(actual_events: list[dict[str, Any]], signal_events: list[dict[str, Any]]) -> dict[str, Any]:
    closed = [event for event in actual_events if event["closed"]]
    open_rows = [event for event in actual_events if event["open"]]
    wins = [event for event in closed if (event.get("pnl_aed") or 0.0) > 0.0]
    closed_pnl = _sum_field(closed, "pnl_aed")
    open_pnl = _sum_field(open_rows, "pnl_aed")
    return {
        "actual_trades": len(actual_events),
        "closed_actual_trades": len(closed),
        "open_actual_trades": len(open_rows),
        "closed_win_rate": (len(wins) / len(closed)) if closed else None,
        "closed_pnl_aed": closed_pnl,
        "open_pnl_aed": open_pnl,
        "total_pnl_aed": closed_pnl + open_pnl,
        "signals": len(signal_events),
    }


def _performance_rows(
    signal_events: list[dict[str, Any]],
    actual_events: list[dict[str, Any]],
    duplicate_event_ids: set[int],
) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str, str, str], dict[str, Any]] = {}

    def row_for(event: dict[str, Any]) -> dict[str, Any]:
        key = (
            str(event["candidate"]),
            str(event["symbol"]),
            str(event["status"]),
            str(event["date"] or "UNKNOWN_DATE"),
        )
        if key not in by_key:
            by_key[key] = {
                "candidate": key[0],
                "symbol": key[1],
                "status": key[2],
                "date": key[3],
                "signals": 0,
                "trades": 0,
                "closed": 0,
                "open": 0,
                "wins": 0,
                "closed_pnl_aed": 0.0,
                "open_pnl_aed": 0.0,
                "duplicate_count": 0,
                "net_r_values": [],
            }
        return by_key[key]

    for event in signal_events:
        row = row_for(event)
        row["signals"] += 1
        if event.get("net_r") is not None:
            row["net_r_values"].append(float(event["net_r"]))
        if id(event) in duplicate_event_ids:
            row["duplicate_count"] += 1

    for event in actual_events:
        row = row_for(event)
        row["trades"] += 1
        if event["closed"]:
            row["closed"] += 1
            pnl = float(event.get("pnl_aed") or 0.0)
            row["closed_pnl_aed"] += pnl
            if pnl > 0.0:
                row["wins"] += 1
        if event["open"]:
            row["open"] += 1
            row["open_pnl_aed"] += float(event.get("pnl_aed") or 0.0)
        if event.get("is_duplicate"):
            row["duplicate_count"] += 1

    rows = []
    for row in by_key.values():
        closed = int(row["closed"])
        row["win_rate"] = (row["wins"] / closed) if closed else None
        values = row.pop("net_r_values")
        row["net_expectancy_proxy_r"] = mean(values) if values else None
        rows.append(row)
    return sorted(rows, key=lambda item: (str(item["candidate"]), str(item["symbol"]), str(item["date"])))


def _actual_money_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    closed = [event for event in events if event.get("closed")]
    open_rows = [event for event in events if event.get("open")]
    wins = [event for event in closed if (event.get("pnl_aed") or event.get("net_r") or 0.0) > 0.0]
    closed_pnl = _sum_field(closed, "pnl_aed")
    open_pnl = _sum_field(open_rows, "pnl_aed")
    return {
        "rows": len(events),
        "closed": len(closed),
        "open": len(open_rows),
        "win_rate": (len(wins) / len(closed)) if closed else None,
        "closed_pnl_aed": closed_pnl if any(event.get("pnl_aed") is not None for event in closed) else None,
        "open_pnl_aed": open_pnl if any(event.get("pnl_aed") is not None for event in open_rows) else None,
        "total_pnl_aed": (closed_pnl + open_pnl)
        if any(event.get("pnl_aed") is not None for event in events)
        else None,
    }


def _money_summary_table_row(name: str, summary: dict[str, Any]) -> tuple[Any, ...]:
    return (
        name,
        summary["rows"],
        summary["closed"],
        summary["open"],
        _fmt_pct(summary["win_rate"]),
        _fmt_num(summary["closed_pnl_aed"]),
        _fmt_num(summary["open_pnl_aed"]),
        _fmt_num(summary["total_pnl_aed"]),
    )


def _expectancy_rows(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        groups[(str(event["candidate"]), str(event["symbol"]))].append(event)
    rows: list[dict[str, Any]] = []
    for (candidate, symbol), group in groups.items():
        values = [float(event["net_r"]) for event in group if event.get("net_r") is not None]
        if not values:
            continue
        wins = [value for value in values if value > 0.0]
        losses = [value for value in values if value < 0.0]
        cost_values = [float(event["cost_r"]) for event in group if event.get("cost_r") is not None]
        avg_win = mean(wins) if wins else 0.0
        avg_loss = abs(mean(losses)) if losses else 0.0
        win_rate = len(wins) / len(values) if values else None
        avg_cost = mean(cost_values) if cost_values else 0.0
        rows.append(
            {
                "candidate": candidate,
                "symbol": symbol,
                "rows": len(values),
                "win_rate": win_rate,
                "avg_win_r": avg_win if wins else None,
                "avg_loss_r": avg_loss if losses else None,
                "payoff_ratio": (avg_win / avg_loss) if avg_win and avg_loss else None,
                "avg_cost_r": avg_cost if cost_values else None,
                "net_expectancy_r": mean(values),
                "formula_expectancy_r": expectancy_after_cost(win_rate or 0.0, avg_win, avg_loss, avg_cost),
                "break_even_win_rate": break_even_win_rate(avg_win, avg_loss) if avg_win and avg_loss else None,
            }
        )
    return sorted(rows, key=lambda item: (str(item["candidate"]), str(item["symbol"])))


def _loss_quality_rows(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    duplicate_keys = {item["group_key"] for item in duplicate_family_signals(events)}
    groups: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for event in events:
        classification = classify_loss(event, duplicate_keys)
        groups[(str(event["candidate"]), str(event["symbol"]))][classification] += 1
    rows = []
    for (candidate, symbol), counter in groups.items():
        row = {"candidate": candidate, "symbol": symbol, "losses": sum(counter.values())}
        for class_name in LOSS_CLASSES:
            row[class_name] = counter.get(class_name, 0)
        rows.append(row)
    return sorted(rows, key=lambda item: (str(item["candidate"]), str(item["symbol"])))


def _loss_examples(events: list[dict[str, Any]]) -> list[tuple[Any, ...]]:
    duplicate_keys = {item["group_key"] for item in duplicate_family_signals(events)}
    rows = []
    for event in sorted(events, key=lambda item: (str(item["candidate"]), str(item["timestamp"]))):
        rows.append(
            (
                event.get("candidate"),
                event.get("symbol"),
                event.get("timestamp"),
                classify_loss(event, duplicate_keys),
                _fmt_num(event.get("net_r")),
                _fmt_num(event.get("pnl_aed")),
                _fmt_num(event.get("cost_r")),
                _fmt_num(event.get("stop_points")),
                event.get("session") or "UNKNOWN",
            )
        )
    return rows


def _bucket_rows(
    events: list[dict[str, Any]],
    *,
    bucket_func: Any,
    bucket_field: str,
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    value_field = "cost_r" if bucket_field == "cost_bucket" else "stop_points"
    for event in events:
        groups[(str(event["candidate"]), str(event["symbol"]), bucket_func(event.get(value_field)))].append(event)
    rows: list[dict[str, Any]] = []
    for (candidate, symbol, bucket), group in groups.items():
        values = [float(event["net_r"]) for event in group if event.get("net_r") is not None]
        pnl_values = [float(event["pnl_aed"]) for event in group if event.get("pnl_aed") is not None]
        cost_values = [float(event["cost_r"]) for event in group if event.get("cost_r") is not None]
        stop_values = [float(event["stop_points"]) for event in group if event.get("stop_points") is not None]
        wins = sum(1 for event in group if _is_win(event))
        scored = sum(1 for event in group if _is_win(event) or _is_loss(event))
        row = {
            "candidate": candidate,
            "symbol": symbol,
            "bucket": bucket,
            "rows": len(group),
            "win_rate": (wins / scored) if scored else None,
            "avg_cost_r": mean(cost_values) if cost_values else None,
            "avg_stop_points": mean(stop_values) if stop_values else None,
            "expectancy_r": mean(values) if values else None,
            "avg_pnl_aed": mean(pnl_values) if pnl_values else None,
            "p95_spread_flag": "YES" if any(_stop_flag(event) for event in group) else "NO",
        }
        rows.append(row)
    return sorted(rows, key=lambda item: (str(item["candidate"]), str(item["symbol"]), str(item["bucket"])))


def _session_rows(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        groups[(str(event["candidate"]), str(event["symbol"]), str(event.get("session") or "UNKNOWN"))].append(event)
    rows: list[dict[str, Any]] = []
    for (candidate, symbol, session), group in groups.items():
        values = [float(event["net_r"]) for event in group if event.get("net_r") is not None]
        pnl_values = [float(event["pnl_aed"]) for event in group if event.get("pnl_aed") is not None]
        cost_values = [float(event["cost_r"]) for event in group if event.get("cost_r") is not None]
        wins = sum(1 for event in group if _is_win(event))
        losses = sum(1 for event in group if _is_loss(event))
        scored = wins + losses
        rows.append(
            {
                "candidate": candidate,
                "symbol": symbol,
                "session": session,
                "rows": len(group),
                "losses": losses,
                "win_rate": (wins / scored) if scored else None,
                "avg_cost_r": mean(cost_values) if cost_values else None,
                "expectancy_r": mean(values) if values else None,
                "avg_pnl_aed": mean(pnl_values) if pnl_values else None,
            }
        )
    return sorted(rows, key=lambda item: (str(item["candidate"]), str(item["symbol"]), str(item["session"])))


def _dedupe_detail_rows(details: list[dict[str, Any]]) -> list[tuple[Any, ...]]:
    rows = []
    for detail in sorted(details, key=lambda item: str(item["group_key"])):
        primary = detail["primary"]
        duplicates = detail["duplicates"]
        rows.append(
            (
                detail["group_key"],
                primary.get("candidate"),
                ", ".join(str(event.get("candidate")) for event in duplicates),
                len(detail["rows"]),
                primary.get("symbol"),
                primary.get("direction"),
                primary.get("bar"),
            )
        )
    return rows


def _source_table(data: RefinementData) -> str:
    return _table(
        ("Source", "Path", "Rows"),
        [
            ("Actual demo broker ledger", "synthetic sample" if data.actual_log_path is None else str(data.actual_log_path), len(data.actual_rows)),
            ("Demo signal ledger", "synthetic sample" if data.signal_log_path is None else str(data.signal_log_path), len(data.signal_rows)),
            ("Passive cost observer log", "synthetic sample" if data.passive_log_path is None else str(data.passive_log_path), len(data.passive_rows)),
        ],
    )


def _readiness_status(path: Path) -> str:
    if not path.exists():
        return "Readiness report not found; keep blocked."
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines()[:80]:
        if "FAIL" in line.upper():
            return "FAIL observed in current readiness report"
    return "Review required; this refinement report does not change readiness"


def _is_win(event: dict[str, Any]) -> bool:
    if event.get("pnl_aed") is not None:
        return float(event["pnl_aed"]) > 0.0
    if event.get("net_r") is not None:
        return float(event["net_r"]) > 0.0
    state = str(event.get("state") or "").upper()
    return state.startswith("WIN") or "TP" in state


def _is_loss(event: dict[str, Any]) -> bool:
    if event.get("pnl_aed") is not None:
        return float(event["pnl_aed"]) < 0.0
    if event.get("net_r") is not None:
        return float(event["net_r"]) < 0.0
    state = str(event.get("state") or "").upper()
    return state.startswith("LOSS") or "STOP" in state


def _session_problem(event: dict[str, Any]) -> bool:
    session = str(event.get("session") or "").upper()
    raw = event.get("raw") or {}
    return session in {"ROLLOVER", "UNKNOWN"} or _truthy(raw.get("is_rollover_window"))


def _stop_flag(event: dict[str, Any]) -> bool:
    stop_points = event.get("stop_points")
    if stop_points is None:
        return False
    stop_value = float(stop_points)
    if stop_value <= 0.0:
        return True
    if stop_value < 250.0:
        return True
    p95_spread = float(DEFAULT_SPREAD_ASSUMPTIONS.measured_p95_spread_points)
    return (p95_spread / stop_value) > 0.30


def _outcome_is_closed(outcome: str) -> bool:
    value = outcome.upper()
    return value.startswith("WIN") or value.startswith("LOSS")


def _outcome_is_open(outcome: str) -> bool:
    value = outcome.upper()
    return "OPEN" in value or "UNRESOLVED" in value


def _candidate_family(candidate: str | None, family: str | None = None) -> str:
    if family:
        return family
    candidate = candidate or ""
    if candidate in {
        "breakout_retest",
        "swing_breakout_retest_v0",
        "symbol_normalized_round_retest_v0",
        "quarter_round_retest_v0",
        "session_extreme_retest_v0",
        "round_number_retest_v0",
    }:
        return "breakout_retest_family"
    if "round" in candidate or "retest" in candidate:
        return "retest_family"
    if "gld" in candidate.lower():
        return "gld_flow_family"
    if "macro" in candidate.lower():
        return "macro_context_family"
    return candidate or "UNKNOWN_FAMILY"


def _normalize_direction(value: str | None) -> str:
    text = (value or "").upper()
    if text == "BUY":
        return "LONG"
    if text == "SELL":
        return "SHORT"
    return text or "UNKNOWN"


def _session_from_row(row: dict[str, str], timestamp: str) -> str:
    label = row.get("session_label") or row.get("session")
    if label:
        return _normalize_session_label(label)
    hour = row.get("hour_utc")
    if hour is None or hour == "":
        hour = _hour_from_timestamp(timestamp)
    try:
        hour_int = int(float(hour))
    except (TypeError, ValueError):
        return "UNKNOWN"
    if hour_int in {21, 22, 23, 0}:
        return "ROLLOVER"
    if 7 <= hour_int <= 11:
        return "LONDON"
    if 12 <= hour_int <= 16:
        return "NY"
    if 1 <= hour_int <= 6:
        return "ASIA"
    return "OFF_HOURS"


def _normalize_session_label(label: str) -> str:
    value = label.strip().upper().replace(" ", "_")
    if value in {"NEW_YORK", "US", "USA", "AMERICA"}:
        return "NY"
    if value in {"LON"}:
        return "LONDON"
    return value or "UNKNOWN"


def _hour_from_timestamp(timestamp: str) -> str:
    timestamp = timestamp.strip()
    if not timestamp:
        return ""
    for separator in ("T", " "):
        if separator in timestamp:
            time_part = timestamp.split(separator, 1)[1]
            return time_part[:2]
    return ""


def _date_key(timestamp: str) -> str:
    raw = (timestamp or "").strip()
    if not raw:
        return ""
    raw = raw.replace(".", "-")
    for separator in ("T", " "):
        if separator in raw:
            return raw.split(separator, 1)[0]
    return raw[:10]


def _bar_key(timestamp: str) -> str:
    raw = (timestamp or "").strip().replace(".", "-")
    if not raw:
        return ""
    if "T" in raw:
        date_part, time_part = raw.split("T", 1)
    elif " " in raw:
        date_part, time_part = raw.split(" ", 1)
    else:
        return raw[:16]
    return f"{date_part} {time_part[:5]}"


def _level_key(value: str | None) -> str:
    number = _float(value)
    if number is None:
        return (value or "").strip()
    if abs(number) >= 100.0:
        return f"{number:.2f}"
    return f"{number:.5f}"


def _stop_points_from_prices(symbol: str, entry: str | None, stop: str | None) -> float | None:
    entry_value = _float(entry)
    stop_value = _float(stop)
    if entry_value is None or stop_value is None:
        return None
    point_size = _point_size(symbol)
    if point_size <= 0.0:
        return None
    return abs(entry_value - stop_value) / point_size


def _point_size(symbol: str) -> float:
    symbol = symbol.upper()
    if symbol == "XAUUSD":
        return 0.01
    if symbol.endswith("JPY"):
        return 0.001
    return 0.00001


def _float(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "" or text.lower() in {"n/a", "na", "none", "nan"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _truthy(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _sum_field(events: Iterable[dict[str, Any]], field: str) -> float:
    return sum(float(event[field]) for event in events if event.get(field) is not None)


def _fmt_num(value: object) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, str):
        number = _float(value)
        if number is None:
            return value
        value = number
    if isinstance(value, int):
        return str(value)
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return str(value)


def _fmt_pct(value: object) -> str:
    if value is None:
        return "n/a"
    try:
        return f"{float(value) * 100.0:.2f}%"
    except (TypeError, ValueError):
        return str(value)


def _table(headers: tuple[Any, ...], rows: Iterable[Iterable[Any]]) -> str:
    output = [
        "| " + " | ".join(_escape_cell(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        output.append("| " + " | ".join(_escape_cell(value) for value in row) + " |")
    return "\n".join(output)


def _escape_cell(value: object) -> str:
    if value is None:
        return "n/a"
    return str(value).replace("|", "/")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError, ProjectConfig


@dataclass(frozen=True)
class RealityCheckOutput:
    status: str
    report_path: Path
    summary_path: Path
    manifest_path: Path
    winner: str
    white_reality_check_pvalue: float
    max_pairwise_spa_pvalue: float


@dataclass(frozen=True)
class FamilyClusteredRealityCheckOutput:
    status: str
    report_path: Path
    assignments_path: Path
    manifest_path: Path
    winner_family: str
    white_reality_check_pvalue: float
    max_pairwise_spa_pvalue: float
    family_count: int


BREAKOUT_RETEST_FAMILY = frozenset(
    {
        "breakout_retest",
        "swing_breakout_retest_v0",
        "round_number_retest_v0",
        "symbol_normalized_round_retest_v0",
        "session_extreme_retest_v0",
        "quarter_round_retest_v0",
    }
)
BREAKOUT_RETEST_FAMILY_NAME = "breakout_retest_family"


def run_reality_check(
    config: ProjectConfig,
    approved_expert: str = "breakout_retest",
    iterations: int = 5000,
    block_months: int = 3,
    max_pvalue: float = 0.10,
    seed: int = 20260521,
) -> RealityCheckOutput:
    if iterations < 100:
        raise ConfigError("Reality check requires at least 100 bootstrap iterations.")
    if block_months < 1:
        raise ConfigError("Reality check block_months must be positive.")
    if not 0.0 < max_pvalue < 1.0:
        raise ConfigError("Reality check max_pvalue must be between 0 and 1.")

    panel = _load_monthly_panel(config)
    if approved_expert not in panel.columns:
        raise ConfigError(f"Approved expert {approved_expert!r} is missing from matrix trade ledgers.")
    if len(panel.columns) < 2:
        raise ConfigError("Reality check requires at least two expert candidates.")
    if len(panel) < block_months * 2:
        raise ConfigError("Reality check monthly panel is too short for the requested block size.")
    effective_max_pvalue = 0.01 if len(panel.columns) >= 30 and max_pvalue > 0.01 else max_pvalue

    observed = panel.mean(axis=0)
    winner = str(observed.idxmax())
    white_pvalue, white_bootstrap_quantiles = _white_reality_check_pvalue(
        panel=panel,
        iterations=iterations,
        block_months=block_months,
        seed=seed,
    )
    pairwise_rows = _pairwise_spa_rows(
        panel=panel,
        approved_expert=approved_expert,
        iterations=iterations,
        block_months=block_months,
        seed=seed + 17,
        max_pvalue=effective_max_pvalue,
    )
    max_pairwise_pvalue = max(float(row["spa_pvalue"]) for row in pairwise_rows)
    status = (
        "PASS"
        if winner == approved_expert
        and float(observed[approved_expert]) > 0
        and white_pvalue <= effective_max_pvalue
        and all(row["status"] == "PASS" for row in pairwise_rows)
        else "FAIL"
    )

    reports_dir = config.root / "outputs" / "reports"
    manifests_dir = config.root / "outputs" / "manifests"
    reports_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "PHASE0_REALITY_CHECK.md"
    summary_path = reports_dir / "PHASE0_REALITY_CHECK_SUMMARY.csv"
    manifest_path = manifests_dir / "PHASE0_REALITY_CHECK_MANIFEST.json"

    summary_rows = _summary_rows(panel, observed, approved_expert, pairwise_rows)
    pd.DataFrame(summary_rows).to_csv(summary_path, index=False)
    report_path.write_text(
        _render_report(
            status=status,
            approved_expert=approved_expert,
            winner=winner,
            iterations=iterations,
            block_months=block_months,
            max_pvalue=max_pvalue,
            effective_max_pvalue=effective_max_pvalue,
            observed=observed,
            white_pvalue=white_pvalue,
            white_bootstrap_quantiles=white_bootstrap_quantiles,
            pairwise_rows=pairwise_rows,
            panel=panel,
        ),
        encoding="utf-8",
    )
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "approved_expert": approved_expert,
        "winner": winner,
        "method": "white_reality_check_and_spa_style_block_bootstrap_on_fixed_notional_monthly_r",
        "iterations": iterations,
        "block_months": block_months,
        "max_pvalue": max_pvalue,
        "effective_max_pvalue": effective_max_pvalue,
        "white_reality_check_pvalue": white_pvalue,
        "white_bootstrap_quantiles": white_bootstrap_quantiles,
        "max_pairwise_spa_pvalue": max_pairwise_pvalue,
        "month_count": int(len(panel)),
        "experts": list(panel.columns),
        "observed_mean_monthly_r": {str(key): float(value) for key, value in observed.items()},
        "pairwise_spa": pairwise_rows,
        "report_path": str(report_path.relative_to(config.root)),
        "summary_path": str(summary_path.relative_to(config.root)),
        "report_sha256": _sha256(report_path),
        "summary_sha256": _sha256(summary_path),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return RealityCheckOutput(
        status=status,
        report_path=report_path,
        summary_path=summary_path,
        manifest_path=manifest_path,
        winner=winner,
        white_reality_check_pvalue=white_pvalue,
        max_pairwise_spa_pvalue=max_pairwise_pvalue,
    )


def run_family_clustered_reality_check(
    config: ProjectConfig,
    approved_expert: str = "breakout_retest",
    approved_family: str = BREAKOUT_RETEST_FAMILY_NAME,
    iterations: int = 5000,
    block_months: int = 3,
    max_pvalue: float = 0.10,
    seed: int = 20260527,
    reviewer_accepted_method: bool = False,
) -> FamilyClusteredRealityCheckOutput:
    if iterations < 100:
        raise ConfigError("Family-clustered reality check requires at least 100 bootstrap iterations.")
    if block_months < 1:
        raise ConfigError("Family-clustered reality check block_months must be positive.")
    if not 0.0 < max_pvalue < 1.0:
        raise ConfigError("Family-clustered reality check max_pvalue must be between 0 and 1.")

    panel = _load_monthly_panel(config)
    if approved_expert not in panel.columns:
        raise ConfigError(f"Approved expert {approved_expert!r} is missing from matrix trade ledgers.")
    assignments = _family_assignments(panel.columns, approved_expert, approved_family)
    family_panel = _family_panel(panel, assignments)
    if approved_family not in family_panel.columns:
        raise ConfigError(f"Approved family {approved_family!r} is missing from family panel.")
    if len(family_panel.columns) < 2:
        raise ConfigError("Family-clustered reality check requires at least two families.")
    if len(family_panel) < block_months * 2:
        raise ConfigError(
            "Family-clustered reality check monthly panel is too short for the requested block size."
        )
    effective_max_pvalue = (
        0.01 if len(family_panel.columns) >= 30 and max_pvalue > 0.01 else max_pvalue
    )

    observed = family_panel.mean(axis=0)
    winner_family = str(observed.idxmax())
    white_pvalue, white_bootstrap_quantiles = _white_reality_check_pvalue(
        panel=family_panel,
        iterations=iterations,
        block_months=block_months,
        seed=seed,
    )
    pairwise_rows = _pairwise_spa_rows(
        panel=family_panel,
        approved_expert=approved_family,
        iterations=iterations,
        block_months=block_months,
        seed=seed + 17,
        max_pvalue=effective_max_pvalue,
    )
    max_pairwise_pvalue = max((float(row["spa_pvalue"]) for row in pairwise_rows), default=0.0)
    statistical_pass = (
        winner_family == approved_family
        and float(observed[approved_family]) > 0
        and white_pvalue <= effective_max_pvalue
        and all(row["status"] == "PASS" for row in pairwise_rows)
    )
    status = (
        "PASS"
        if statistical_pass and reviewer_accepted_method
        else "PASS_REVIEW_REQUIRED"
        if statistical_pass
        else "FAIL"
    )

    reports_dir = config.root / "outputs" / "reports"
    manifests_dir = config.root / "outputs" / "manifests"
    reports_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "PHASE0_REALITY_CHECK_FAMILY_CLUSTERED.md"
    assignments_path = reports_dir / "PHASE0_REALITY_CHECK_FAMILY_ASSIGNMENTS.csv"
    manifest_path = manifests_dir / "PHASE0_REALITY_CHECK_FAMILY_CLUSTERED_MANIFEST.json"

    pd.DataFrame(assignments).to_csv(assignments_path, index=False)
    report_path.write_text(
        _render_family_clustered_report(
            status=status,
            reviewer_accepted_method=reviewer_accepted_method,
            approved_expert=approved_expert,
            approved_family=approved_family,
            winner_family=winner_family,
            iterations=iterations,
            block_months=block_months,
            max_pvalue=max_pvalue,
            effective_max_pvalue=effective_max_pvalue,
            observed=observed,
            white_pvalue=white_pvalue,
            white_bootstrap_quantiles=white_bootstrap_quantiles,
            pairwise_rows=pairwise_rows,
            family_panel=family_panel,
            assignments=assignments,
        ),
        encoding="utf-8",
    )
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "statistical_pass": statistical_pass,
        "reviewer_accepted_method": reviewer_accepted_method,
        "approved_expert": approved_expert,
        "approved_family": approved_family,
        "winner_family": winner_family,
        "method": "D2_FAMILY_CLUSTERED_V0",
        "source_method_decision": "docs/D2_METHOD_DECISION_2026_05_27.md",
        "canonical_candidate_level_report_unchanged": True,
        "iterations": iterations,
        "block_months": block_months,
        "max_pvalue": max_pvalue,
        "effective_max_pvalue": effective_max_pvalue,
        "white_reality_check_pvalue": white_pvalue,
        "white_bootstrap_quantiles": white_bootstrap_quantiles,
        "max_pairwise_spa_pvalue": max_pairwise_pvalue,
        "month_count": int(len(family_panel)),
        "family_count": int(len(family_panel.columns)),
        "families": list(family_panel.columns),
        "assignment_count": len(assignments),
        "excluded_same_family_variants": [
            row["expert"]
            for row in assignments
            if row["role"] == "same_family_excluded_from_pairwise_spa"
        ],
        "observed_mean_monthly_r": {str(key): float(value) for key, value in observed.items()},
        "pairwise_spa": pairwise_rows,
        "report_path": str(report_path.relative_to(config.root)),
        "assignments_path": str(assignments_path.relative_to(config.root)),
        "report_sha256": _sha256(report_path),
        "assignments_sha256": _sha256(assignments_path),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return FamilyClusteredRealityCheckOutput(
        status=status,
        report_path=report_path,
        assignments_path=assignments_path,
        manifest_path=manifest_path,
        winner_family=winner_family,
        white_reality_check_pvalue=white_pvalue,
        max_pairwise_spa_pvalue=max_pairwise_pvalue,
        family_count=len(family_panel.columns),
    )


def _load_monthly_panel(config: ProjectConfig) -> pd.DataFrame:
    root = config.root / "outputs" / "matrix_results"
    if not root.exists():
        raise ConfigError(f"Missing matrix results directory: {root}")
    expert_series: dict[str, pd.Series] = {}
    for expert_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        series = _expert_monthly_series(expert_dir)
        if not series.empty:
            expert_series[expert_dir.name] = series
    if not expert_series:
        raise ConfigError(f"No expert trade ledgers found under {root}")
    return pd.DataFrame(expert_series).fillna(0.0).sort_index()


def _expert_monthly_series(expert_dir: Path) -> pd.Series:
    ledger_series: list[pd.Series] = []
    for trade_file in sorted(expert_dir.glob("*_trades.csv")):
        frame = pd.read_csv(
            trade_file,
            usecols=lambda column: column in {"entry_time_utc", "r_multiple", "net_pnl_usd"},
        )
        frame["entry_time_utc"] = pd.to_datetime(frame["entry_time_utc"], utc=True, errors="coerce")
        value_column = "r_multiple" if "r_multiple" in frame.columns else "net_pnl_usd"
        frame[value_column] = pd.to_numeric(frame[value_column], errors="coerce")
        frame = frame.dropna(subset=["entry_time_utc", value_column])
        if frame.empty:
            continue
        frame["month"] = frame["entry_time_utc"].dt.strftime("%Y-%m")
        ledger_series.append(frame.groupby("month")[value_column].sum())
    if not ledger_series:
        return pd.Series(dtype="float64")
    return pd.concat(ledger_series, axis=1).fillna(0.0).mean(axis=1)


def _family_assignments(
    experts: pd.Index,
    approved_expert: str,
    approved_family: str,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for expert in sorted(str(column) for column in experts):
        if expert == approved_expert:
            rows.append(
                {
                    "expert": expert,
                    "family": approved_family,
                    "representative": approved_expert,
                    "role": "family_representative",
                    "included_in_family_panel": "true",
                    "pairwise_spa_role": "approved_family_under_test",
                    "assignment_reason": (
                        "Pre-registered breakout-retest family representative from "
                        "D2_METHOD_DECISION_2026_05_27.md."
                    ),
                }
            )
        elif expert in BREAKOUT_RETEST_FAMILY:
            rows.append(
                {
                    "expert": expert,
                    "family": approved_family,
                    "representative": approved_expert,
                    "role": "same_family_excluded_from_pairwise_spa",
                    "included_in_family_panel": "false",
                    "pairwise_spa_role": "excluded_same_family_variant",
                    "assignment_reason": (
                        "Explicitly documented same-family level/retest variant; not diversification."
                    ),
                }
            )
        else:
            rows.append(
                {
                    "expert": expert,
                    "family": expert,
                    "representative": expert,
                    "role": "independent_representative",
                    "included_in_family_panel": "true",
                    "pairwise_spa_role": "independent_alternative_family",
                    "assignment_reason": (
                        "Not listed as same-family in the pre-registered family assignment rule; "
                        "kept as its own family."
                    ),
                }
            )
    return rows


def _family_panel(panel: pd.DataFrame, assignments: list[dict[str, str]]) -> pd.DataFrame:
    family_series: dict[str, pd.Series] = {}
    for row in assignments:
        if row["included_in_family_panel"] != "true":
            continue
        expert = row["expert"]
        family = row["family"]
        if expert not in panel.columns:
            continue
        family_series[family] = panel[expert]
    return pd.DataFrame(family_series).fillna(0.0).sort_index()


def _white_reality_check_pvalue(
    panel: pd.DataFrame,
    iterations: int,
    block_months: int,
    seed: int,
) -> tuple[float, dict[str, float]]:
    observed_means = panel.mean(axis=0)
    observed_max = float(observed_means.max())
    centered = panel - observed_means
    values = centered.to_numpy(dtype="float64")
    rng = np.random.default_rng(seed)
    bootstrap_stats = np.empty(iterations, dtype="float64")
    for index in range(iterations):
        sampled = values[_block_bootstrap_indices(len(values), block_months, rng)]
        bootstrap_stats[index] = float(sampled.mean(axis=0).max())
    pvalue = float((np.count_nonzero(bootstrap_stats >= observed_max) + 1) / (iterations + 1))
    quantiles = {
        "q90": float(np.quantile(bootstrap_stats, 0.90)),
        "q95": float(np.quantile(bootstrap_stats, 0.95)),
        "q99": float(np.quantile(bootstrap_stats, 0.99)),
    }
    return pvalue, quantiles


def _pairwise_spa_rows(
    panel: pd.DataFrame,
    approved_expert: str,
    iterations: int,
    block_months: int,
    seed: int,
    max_pvalue: float,
) -> list[dict[str, Any]]:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    for alternative in panel.columns:
        if alternative == approved_expert:
            continue
        diff = (panel[approved_expert] - panel[alternative]).to_numpy(dtype="float64")
        observed_diff = float(np.mean(diff))
        centered = diff - observed_diff
        bootstrap_stats = np.empty(iterations, dtype="float64")
        for index in range(iterations):
            sampled = centered[_block_bootstrap_indices(len(centered), block_months, rng)]
            bootstrap_stats[index] = float(np.mean(sampled))
        pvalue = float((np.count_nonzero(bootstrap_stats >= observed_diff) + 1) / (iterations + 1))
        rows.append(
            {
                "status": "PASS" if observed_diff > 0 and pvalue <= max_pvalue else "FAIL",
                "approved_expert": approved_expert,
                "alternative": str(alternative),
                "mean_monthly_edge_r": observed_diff,
                "spa_pvalue": pvalue,
                "bootstrap_q95": float(np.quantile(bootstrap_stats, 0.95)),
            }
        )
    return rows


def _block_bootstrap_indices(length: int, block_months: int, rng: np.random.Generator) -> np.ndarray:
    indices: list[int] = []
    while len(indices) < length:
        start = int(rng.integers(0, length))
        for offset in range(block_months):
            indices.append((start + offset) % length)
            if len(indices) == length:
                break
    return np.array(indices, dtype=int)


def _summary_rows(
    panel: pd.DataFrame,
    observed: pd.Series,
    approved_expert: str,
    pairwise_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = [
        {
            "row_type": "expert_monthly_mean",
            "expert": str(expert),
            "comparison": "",
            "mean_monthly_r": float(value),
            "total_r": float(panel[expert].sum()),
            "pvalue": "",
            "status": "APPROVED_EXPERT" if expert == approved_expert else "ALTERNATIVE",
        }
        for expert, value in observed.items()
    ]
    for row in pairwise_rows:
        rows.append(
            {
                "row_type": "pairwise_spa",
                "expert": row["approved_expert"],
                "comparison": row["alternative"],
                "mean_monthly_r": row["mean_monthly_edge_r"],
                "total_r": "",
                "pvalue": row["spa_pvalue"],
                "status": row["status"],
            }
        )
    return rows


def _render_report(
    status: str,
    approved_expert: str,
    winner: str,
    iterations: int,
    block_months: int,
    max_pvalue: float,
    effective_max_pvalue: float,
    observed: pd.Series,
    white_pvalue: float,
    white_bootstrap_quantiles: dict[str, float],
    pairwise_rows: list[dict[str, Any]],
    panel: pd.DataFrame,
) -> str:
    expert_table = _markdown_table(
        [
            {
                "Expert": str(expert),
                "Mean Monthly R": _fmt(value, 4),
                "Total R": _fmt(panel[expert].sum(), 2),
                "Role": "approved" if expert == approved_expert else "alternative",
            }
            for expert, value in observed.items()
        ],
        ["Expert", "Mean Monthly R", "Total R", "Role"],
    )
    pairwise_table = _markdown_table(
        [
            {
                "Alternative": str(row["alternative"]),
                "Status": str(row["status"]),
                "Mean Edge R": _fmt(row["mean_monthly_edge_r"], 4),
                "SPA p": _fmt(row["spa_pvalue"], 4),
                "Bootstrap q95 R": _fmt(row["bootstrap_q95"], 4),
            }
            for row in pairwise_rows
        ],
        ["Alternative", "Status", "Mean Edge R", "SPA p", "Bootstrap q95 R"],
    )
    return "\n".join(
        [
            "# PHASE0 REALITY CHECK",
            "",
            f"Status: {status}",
            f"Generated at UTC: {datetime.now(timezone.utc).replace(microsecond=0).isoformat()}",
            f"Approved expert under test: {approved_expert}",
            "",
            "## Method",
            "",
            (
                "This report applies a White Reality Check and SPA-style pairwise bootstrap to monthly "
                "fixed-notional R returns for the Phase 0 expert family. Each expert's monthly value is "
                "the average monthly R sum across its matrix trade ledgers, which keeps cost/broker cells "
                "from turning into separate optimized candidates and avoids compounding-dollar scale artifacts."
            ),
            "",
            f"- Bootstrap iterations: {iterations}",
            f"- Circular block length: {block_months} month(s)",
            f"- Maximum accepted p-value: {max_pvalue}",
            f"- Effective accepted p-value: {effective_max_pvalue}",
            "- Candidate universes with at least 30 non-empty matrix-ledger candidates are tightened to alpha = 0.01.",
            f"- Months in panel: {len(panel)}",
            "",
            "## White Reality Check",
            "",
            _markdown_table(
                [
                    {
                        "Winner": winner,
                        "White p": _fmt(white_pvalue, 4),
                        "q90 R": _fmt(white_bootstrap_quantiles["q90"], 4),
                        "q95 R": _fmt(white_bootstrap_quantiles["q95"], 4),
                        "q99 R": _fmt(white_bootstrap_quantiles["q99"], 4),
                    }
                ],
                ["Winner", "White p", "q90 R", "q95 R", "q99 R"],
            ),
            "",
            "## Expert Means",
            "",
            expert_table,
            "",
            "## SPA-Style Pairwise Checks",
            "",
            pairwise_table,
            "",
            "## Interpretation",
            "",
            (
                "A PASS means breakout_retest remains the family winner after a block-bootstrap adjustment "
                "for multiple tested expert candidates. This is statistical support only; it does not remove "
                "the need for Phase 1 soak completion, Phase 2 paper trading, or live drift monitoring."
            ),
            "",
            "Summary rows are written to `outputs/reports/PHASE0_REALITY_CHECK_SUMMARY.csv`.",
            "",
        ]
    )


def _render_family_clustered_report(
    status: str,
    reviewer_accepted_method: bool,
    approved_expert: str,
    approved_family: str,
    winner_family: str,
    iterations: int,
    block_months: int,
    max_pvalue: float,
    effective_max_pvalue: float,
    observed: pd.Series,
    white_pvalue: float,
    white_bootstrap_quantiles: dict[str, float],
    pairwise_rows: list[dict[str, Any]],
    family_panel: pd.DataFrame,
    assignments: list[dict[str, str]],
) -> str:
    family_table = _markdown_table(
        [
            {
                "Family": str(family),
                "Mean Monthly R": _fmt(value, 4),
                "Total R": _fmt(family_panel[family].sum(), 2),
                "Role": "approved_family" if family == approved_family else "alternative_family",
            }
            for family, value in observed.items()
        ],
        ["Family", "Mean Monthly R", "Total R", "Role"],
    )
    pairwise_table = _markdown_table(
        [
            {
                "Alternative Family": str(row["alternative"]),
                "Status": str(row["status"]),
                "Mean Edge R": _fmt(row["mean_monthly_edge_r"], 4),
                "SPA p": _fmt(row["spa_pvalue"], 4),
                "Bootstrap q95 R": _fmt(row["bootstrap_q95"], 4),
            }
            for row in pairwise_rows
        ],
        ["Alternative Family", "Status", "Mean Edge R", "SPA p", "Bootstrap q95 R"],
    )
    excluded_rows = [
        {
            "Expert": row["expert"],
            "Family": row["family"],
            "Representative": row["representative"],
            "Reason": row["assignment_reason"],
        }
        for row in assignments
        if row["role"] == "same_family_excluded_from_pairwise_spa"
    ]
    assignment_preview = _markdown_table(
        [
            {
                "Expert": row["expert"],
                "Family": row["family"],
                "Representative": row["representative"],
                "Role": row["role"],
                "Included": row["included_in_family_panel"],
            }
            for row in assignments
        ],
        ["Expert", "Family", "Representative", "Role", "Included"],
    )
    phase2_effect = (
        "Not readiness-authorizing until reviewer/owner acceptance is recorded."
        if not reviewer_accepted_method
        else "Method acceptance flag was supplied; readiness still depends on other gates."
    )
    return "\n".join(
        [
            "# PHASE0 REALITY CHECK - FAMILY CLUSTERED",
            "",
            f"Overall status: {status}",
            f"Generated at UTC: {datetime.now(timezone.utc).replace(microsecond=0).isoformat()}",
            "Method: D2_FAMILY_CLUSTERED_V0",
            f"Approved expert representative: {approved_expert}",
            f"Approved family under test: {approved_family}",
            f"Reviewer/owner accepted method: {str(reviewer_accepted_method).lower()}",
            "",
            "## Boundary",
            "",
            "- This report does not modify `PHASE0_REALITY_CHECK.md`.",
            "- This report does not convert the current candidate-level D2 FAIL into PASS.",
            f"- Phase 2 readiness effect: {phase2_effect}",
            "- Same-family variants are not diversification.",
            "",
            "## Method",
            "",
            (
                "This diagnostic applies the same fixed-notional monthly R-series White Reality Check and "
                "SPA-style bootstrap to pre-registered family representatives. The breakout-retest family "
                "uses `breakout_retest` as its fixed representative; same-family variants are listed in "
                "the assignment table and excluded from pairwise SPA as variants, not as hidden alternatives."
            ),
            "",
            f"- Bootstrap iterations: {iterations}",
            f"- Circular block length: {block_months} month(s)",
            f"- Maximum accepted p-value: {max_pvalue}",
            f"- Effective accepted p-value: {effective_max_pvalue}",
            "- Family universes with at least 30 non-empty representatives are tightened to alpha = 0.01.",
            f"- Months in panel: {len(family_panel)}",
            f"- Families in panel: {len(family_panel.columns)}",
            "",
            "## White Reality Check",
            "",
            _markdown_table(
                [
                    {
                        "Winner Family": winner_family,
                        "White p": _fmt(white_pvalue, 4),
                        "q90 R": _fmt(white_bootstrap_quantiles["q90"], 4),
                        "q95 R": _fmt(white_bootstrap_quantiles["q95"], 4),
                        "q99 R": _fmt(white_bootstrap_quantiles["q99"], 4),
                    }
                ],
                ["Winner Family", "White p", "q90 R", "q95 R", "q99 R"],
            ),
            "",
            "## Family Means",
            "",
            family_table,
            "",
            "## SPA-Style Pairwise Checks",
            "",
            pairwise_table,
            "",
            "## Excluded Same-Family Variants",
            "",
            _markdown_table(excluded_rows, ["Expert", "Family", "Representative", "Reason"]),
            "",
            "## Assignment Preview",
            "",
            assignment_preview,
            "",
            "## Interpretation",
            "",
            (
                "A statistical PASS here means the pre-registered breakout-retest family representative "
                "survived the family-level multiple-testing diagnostic against independent representatives. "
                "It does not choose between same-family deployment variants, does not provide diversification, "
                "and does not authorize Phase 2 paper-mode execution without reviewer/owner method acceptance "
                "plus all separate soak, measured-cost, VPS, and approval gates."
            ),
            "",
            "Assignments are written to `outputs/reports/PHASE0_REALITY_CHECK_FAMILY_ASSIGNMENTS.csv`.",
            "",
        ]
    )


def _markdown_table(rows: list[dict[str, str]], headers: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    return "\n".join(lines)


def _fmt(value: object, places: int = 3) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if math.isinf(number):
        return "inf"
    return f"{number:.{places}f}"


def _money(value: object) -> str:
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return str(value)


def _sha256(path: Path) -> str:
    digest = __import__("hashlib").sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import sqrt
from pathlib import Path
from typing import Iterable

import pandas as pd

from phase0.config import ProjectConfig
from phase0.rejection_audit import DEFAULT_APPROVED_EXPERTS, generate_rejection_gate_audit


NORMALIZED_TOP_TRADE_REVIEW_THRESHOLD = 1.00
NORMALIZED_TOP5_REVIEW_THRESHOLD = 2.50


@dataclass(frozen=True)
class ConcentrationFrequencyAuditOutput:
    report_path: Path
    summary_path: Path
    audited_candidates: int
    concentration_failed_candidates: int
    normalized_review_candidates: int


def generate_concentration_frequency_audit(
    config: ProjectConfig,
    approved_experts: Iterable[str] = DEFAULT_APPROVED_EXPERTS,
) -> ConcentrationFrequencyAuditOutput:
    """Audit absolute concentration failures with a frequency-normalized lens.

    This report answers Review #6 F3 without changing the Phase 0 gate result:
    candidates that failed absolute concentration remain rejected unless a new,
    pre-registered hypothesis is run. The normalized ratios only identify
    whether a low-frequency candidate deserves human review of the gate design.
    """

    matrix_root = config.root / "outputs" / "matrix_results"
    reports_dir = config.root / "outputs" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    rejection_audit = generate_rejection_gate_audit(config, approved_experts=approved_experts)
    rejected_df = pd.read_csv(rejection_audit.summary_path)
    rejected_by_candidate = {
        str(row["candidate"]): row.to_dict() for _, row in rejected_df.iterrows()
    }

    rows: list[dict[str, object]] = []
    for expert_dir in sorted(path for path in matrix_root.iterdir() if path.is_dir()):
        candidate = expert_dir.name
        gate_row = rejected_by_candidate.get(candidate, {})
        rows.append(_candidate_row(candidate, expert_dir, gate_row))

    summary_df = pd.DataFrame(rows).sort_values(["decision_scope", "candidate"])
    summary_path = reports_dir / "PHASE0_CONCENTRATION_FREQUENCY_NORMALIZED_AUDIT.csv"
    report_path = reports_dir / "PHASE0_CONCENTRATION_FREQUENCY_NORMALIZED_AUDIT.md"
    summary_df.to_csv(summary_path, index=False)
    _write_report(report_path, summary_df)

    concentration_failed = summary_df[summary_df["absolute_concentration_gate"] == "FAIL"]
    normalized_review = summary_df[
        summary_df["normalized_concentration_flag"] == "REVIEW_NORMALIZED_CONTEXT"
    ]
    return ConcentrationFrequencyAuditOutput(
        report_path=report_path,
        summary_path=summary_path,
        audited_candidates=int(len(summary_df)),
        concentration_failed_candidates=int(len(concentration_failed)),
        normalized_review_candidates=int(len(normalized_review)),
    )


def _candidate_row(candidate: str, expert_dir: Path, gate_row: dict[str, object]) -> dict[str, object]:
    cell_rows = [_cell_row(path) for path in sorted(expert_dir.glob("cell_*.csv")) if _is_summary_csv(path)]
    cell_rows = [row for row in cell_rows if row]
    if not cell_rows:
        return {
            "candidate": candidate,
            "decision_scope": str(gate_row.get("decision_scope", "UNKNOWN")),
            "frequency_bias_diagnosis": str(gate_row.get("frequency_bias_diagnosis", "UNKNOWN")),
            "absolute_concentration_gate": str(gate_row.get("concentration", "MISSING")),
            "cells": 0,
            "total_trades": 0,
            "max_absolute_single_trade_pct": 0.0,
            "max_absolute_top5_pct": 0.0,
            "max_normalized_top_trade_r": 0.0,
            "max_normalized_top5_trade_r": 0.0,
            "concentration_failed_cells": 0,
            "normalized_concentration_flag": "NO_MATRIX_ROWS",
            "gate_context": str(gate_row.get("failed_gates", "missing_matrix_summary")),
        }

    df = pd.DataFrame(cell_rows)
    absolute_gate = str(gate_row.get("concentration", "MISSING"))
    total_trades = int(df["trade_count"].sum())
    max_top = float(df["normalized_top_trade_r"].max())
    max_top5 = float(df["normalized_top5_trade_r"].max())
    concentration_failed_cells = int(
        (
            (df["largest_single_trade_pct_of_pnl"] > 10.0)
            | (df["top5_trades_pct_of_pnl"] > 40.0)
        ).sum()
    )
    normalized_flag = _normalized_flag(
        absolute_gate,
        max_top,
        max_top5,
        str(gate_row.get("decision_scope", "")),
        total_trades,
    )

    return {
        "candidate": candidate,
        "decision_scope": str(gate_row.get("decision_scope", "UNKNOWN")),
        "frequency_bias_diagnosis": str(gate_row.get("frequency_bias_diagnosis", "UNKNOWN")),
        "absolute_concentration_gate": absolute_gate,
        "cells": int(len(df)),
        "total_trades": total_trades,
        "max_absolute_single_trade_pct": round(float(df["largest_single_trade_pct_of_pnl"].max()), 4),
        "max_absolute_top5_pct": round(float(df["top5_trades_pct_of_pnl"].max()), 4),
        "max_normalized_top_trade_r": round(max_top, 6),
        "max_normalized_top5_trade_r": round(max_top5, 6),
        "concentration_failed_cells": concentration_failed_cells,
        "normalized_concentration_flag": normalized_flag,
        "gate_context": str(gate_row.get("failed_gates", "")),
    }


def _cell_row(path: Path) -> dict[str, object]:
    summary = pd.read_csv(path)
    if summary.empty:
        return {}
    first = summary.iloc[0].to_dict()
    trades = _load_trade_r_multiples(Path(str(path).replace(".csv", "_trades.csv")))
    normalized = _normalized_concentration(trades)
    return {
        "trade_count": _to_float(first.get("trade_count")),
        "largest_single_trade_pct_of_pnl": _to_float(first.get("largest_single_trade_pct_of_pnl")),
        "top5_trades_pct_of_pnl": _to_float(first.get("top5_trades_pct_of_pnl")),
        **normalized,
    }


def _is_summary_csv(path: Path) -> bool:
    name = path.name
    return name.startswith("cell_") and not name.endswith("_trades.csv") and not name.endswith("_equity.csv")


def _load_trade_r_multiples(path: Path) -> pd.Series:
    if not path.exists():
        return pd.Series(dtype=float)
    df = pd.read_csv(path, usecols=lambda column: column == "r_multiple")
    if "r_multiple" not in df.columns:
        return pd.Series(dtype=float)
    return pd.to_numeric(df["r_multiple"], errors="coerce").dropna()


def _normalized_concentration(r_multiples: pd.Series) -> dict[str, float]:
    n = int(len(r_multiples))
    if n == 0:
        return {"normalized_top_trade_r": 0.0, "normalized_top5_trade_r": 0.0}
    mean_abs_r = float(r_multiples.abs().mean())
    denominator = mean_abs_r * sqrt(n)
    if denominator <= 0:
        return {"normalized_top_trade_r": 0.0, "normalized_top5_trade_r": 0.0}
    winners = r_multiples[r_multiples > 0].sort_values(ascending=False)
    top_trade_r = float(winners.iloc[0]) if not winners.empty else 0.0
    top5_trade_r = float(winners.head(5).sum()) if not winners.empty else 0.0
    return {
        "normalized_top_trade_r": top_trade_r / denominator,
        "normalized_top5_trade_r": top5_trade_r / denominator,
    }


def _normalized_flag(
    absolute_gate: str,
    max_top: float,
    max_top5: float,
    decision_scope: str,
    total_trades: int,
) -> str:
    if absolute_gate != "FAIL":
        return "NOT_ABSOLUTE_CONCENTRATION_FAIL"
    if total_trades <= 0:
        return "NORMALIZATION_UNDEFINED_NO_TRADES"
    if decision_scope == "APPROVED_OR_ACTIVE":
        return "APPROVED_CONTEXT_ONLY"
    if (
        max_top <= NORMALIZED_TOP_TRADE_REVIEW_THRESHOLD
        and max_top5 <= NORMALIZED_TOP5_REVIEW_THRESHOLD
    ):
        return "REVIEW_NORMALIZED_CONTEXT"
    return "REMAINS_HIGH_NORMALIZED_CONCENTRATION"


def _write_report(report_path: Path, df: pd.DataFrame) -> None:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    concentration_failed = df[df["absolute_concentration_gate"] == "FAIL"]
    review_rows = df[df["normalized_concentration_flag"] == "REVIEW_NORMALIZED_CONTEXT"]
    high_rows = df[df["normalized_concentration_flag"] == "REMAINS_HIGH_NORMALIZED_CONCENTRATION"]

    lines = [
        "# Phase 0 Frequency-Normalized Concentration Audit",
        "",
        f"Generated at UTC: `{generated_at}`",
        "",
        "Overall status: PASS",
        "",
        "Purpose: answer Review #6 by checking whether absolute concentration failures are amplified by low trade frequency.",
        "",
        "This report does not approve, rescue, tune, or reclassify any rejected candidate. It is review context only.",
        "",
        "## Method",
        "",
        "- Absolute concentration remains the original Phase 0 gate.",
        "- Normalized top-trade ratio = `top_trade_R / (mean_abs_R * sqrt(n_trades))`.",
        "- Normalized top-5 ratio = `top5_trade_R_sum / (mean_abs_R * sqrt(n_trades))`.",
        f"- Review-context thresholds: top-trade <= {NORMALIZED_TOP_TRADE_REVIEW_THRESHOLD:.2f}, top-5 <= {NORMALIZED_TOP5_REVIEW_THRESHOLD:.2f}.",
        "",
        "## Summary",
        "",
        f"- Audited candidates: {len(df)}",
        f"- Absolute concentration-failed candidates: {len(concentration_failed)}",
        f"- Review-context candidates under normalized thresholds: {len(review_rows)}",
        f"- Candidates with high normalized concentration: {len(high_rows)}",
        "",
        "Conclusion: concentration-failed candidates remain rejected under the current Phase 0 rules. Normalized flags should only inform future gate design for new pre-registered low-frequency hypotheses.",
        "",
        "## Candidate Table",
        "",
        "| Candidate | Scope | Abs Gate | Cells | Trades | Max Single % | Max Top5 % | Norm Top | Norm Top5 | Flag | Gate Context |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for _, row in df.iterrows():
        lines.append(
            "| {candidate} | {decision_scope} | {absolute_concentration_gate} | {cells} | "
            "{total_trades} | {max_absolute_single_trade_pct} | {max_absolute_top5_pct} | "
            "{max_normalized_top_trade_r} | {max_normalized_top5_trade_r} | "
            "{normalized_concentration_flag} | {gate_context} |".format(**row.to_dict())
        )
    lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")


def _to_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

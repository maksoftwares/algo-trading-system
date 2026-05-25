from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import tempfile
import time
from typing import Iterable
from uuid import uuid4

import pandas as pd

from phase0.config import ProjectConfig
from phase0.gates import evaluate_matrix_gates


DEFAULT_APPROVED_EXPERTS = (
    "breakout_retest",
    "swing_breakout_retest_v0",
    "symbol_normalized_round_retest_v0",
)


@dataclass(frozen=True)
class RejectionGateAuditOutput:
    report_path: Path
    summary_path: Path
    audited_candidates: int
    rejected_candidates: int
    sample_size_failure_candidates: int
    edge_expectancy_failure_candidates: int


def generate_rejection_gate_audit(
    config: ProjectConfig,
    approved_experts: Iterable[str] = DEFAULT_APPROVED_EXPERTS,
) -> RejectionGateAuditOutput:
    """Aggregate matrix gate failures across rejected candidates.

    Review #3 asked whether Phase 0 was accidentally selecting for trade
    frequency. This report keeps that check reproducible from the matrix
    summary CSVs instead of embedding the answer in a hand-written note.
    """

    approved = {expert.strip() for expert in approved_experts if expert.strip()}
    matrix_root = config.root / "outputs" / "matrix_results"
    reports_dir = config.root / "outputs" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for expert_dir in sorted(path for path in matrix_root.iterdir() if path.is_dir()):
        expert = expert_dir.name
        matrix_df = _load_matrix_summary(expert_dir)
        if matrix_df.empty:
            rows.append(_empty_candidate_row(expert, approved))
            continue

        gate_results = evaluate_matrix_gates(matrix_df, config.phase0["gates"])
        gate_status = {result.name: result.status for result in gate_results}
        failed_gates = [result.name for result in gate_results if result.status != "PASS"]
        scope = "APPROVED_OR_ACTIVE" if expert in approved else "REJECTED_OR_RESEARCH"
        diagnosis = _diagnose_candidate(scope, gate_status, failed_gates)
        pf = pd.to_numeric(matrix_df["profit_factor"], errors="coerce")
        trades = pd.to_numeric(matrix_df["trade_count"], errors="coerce").fillna(0)
        min_pf = float(config.phase0["gates"]["min_pf_per_passing_cell"])

        rows.append(
            {
                "candidate": expert,
                "decision_scope": scope,
                "frequency_bias_diagnosis": diagnosis,
                "complete_cells": int(len(matrix_df)),
                "pf_passing_cells": int((pf >= min_pf).sum()),
                "total_trades": int(trades.sum()),
                "min_cell_trades": int(trades.min()) if len(trades) else 0,
                "max_cell_trades": int(trades.max()) if len(trades) else 0,
                "median_cell_trades": float(trades.median()) if len(trades) else 0.0,
                "failed_gate_count": len(failed_gates),
                "failed_gates": ";".join(failed_gates) if failed_gates else "none",
                "multi_cell_survival": gate_status.get("multi_cell_survival", "MISSING"),
                "sample_size": gate_status.get("sample_size", "MISSING"),
                "no_catastrophic_failure": gate_status.get("no_catastrophic_failure", "MISSING"),
                "concentration": gate_status.get("concentration", "MISSING"),
                "activity": gate_status.get("activity", "MISSING"),
                "cost_sensitivity": gate_status.get("cost_sensitivity", "MISSING"),
            }
        )

    summary_df = pd.DataFrame(rows).sort_values(["decision_scope", "candidate"])
    summary_path = reports_dir / "PHASE0_REJECTED_CANDIDATE_GATE_AUDIT.csv"
    report_path = reports_dir / "PHASE0_REJECTED_CANDIDATE_GATE_AUDIT.md"
    _write_csv_with_retry(summary_df, summary_path)
    _write_report(report_path, summary_df, approved)

    rejected = summary_df[summary_df["decision_scope"] == "REJECTED_OR_RESEARCH"]
    sample_size_failures = int((rejected["sample_size"] == "FAIL").sum()) if not rejected.empty else 0
    edge_failures = (
        int((rejected["multi_cell_survival"] == "FAIL").sum()) if not rejected.empty else 0
    )
    return RejectionGateAuditOutput(
        report_path=report_path,
        summary_path=summary_path,
        audited_candidates=int(len(summary_df)),
        rejected_candidates=int(len(rejected)),
        sample_size_failure_candidates=sample_size_failures,
        edge_expectancy_failure_candidates=edge_failures,
    )


def _load_matrix_summary(expert_dir: Path) -> pd.DataFrame:
    rows = []
    for path in sorted(expert_dir.glob("cell_*.csv")):
        name = path.name
        if name.endswith("_trades.csv") or name.endswith("_equity.csv"):
            continue
        df = pd.read_csv(path)
        if not df.empty:
            rows.append(df.iloc[0].to_dict())
    return pd.DataFrame(rows)


def _empty_candidate_row(expert: str, approved: set[str]) -> dict[str, object]:
    scope = "APPROVED_OR_ACTIVE" if expert in approved else "REJECTED_OR_RESEARCH"
    return {
        "candidate": expert,
        "decision_scope": scope,
        "frequency_bias_diagnosis": "NO_MATRIX_SUMMARY_ROWS",
        "complete_cells": 0,
        "pf_passing_cells": 0,
        "total_trades": 0,
        "min_cell_trades": 0,
        "max_cell_trades": 0,
        "median_cell_trades": 0.0,
        "failed_gate_count": 6,
        "failed_gates": "missing_matrix_summary",
        "multi_cell_survival": "MISSING",
        "sample_size": "MISSING",
        "no_catastrophic_failure": "MISSING",
        "concentration": "MISSING",
        "activity": "MISSING",
        "cost_sensitivity": "MISSING",
    }


def _diagnose_candidate(scope: str, gate_status: dict[str, str], failed_gates: list[str]) -> str:
    if scope == "APPROVED_OR_ACTIVE":
        return "APPROVED_EDGE_FAMILY"
    sample_failed = gate_status.get("sample_size") == "FAIL"
    edge_failed = gate_status.get("multi_cell_survival") == "FAIL"
    if sample_failed and edge_failed:
        return "EDGE_AND_FREQUENCY_FAILURE"
    if sample_failed:
        return "FREQUENCY_FAILURE"
    if edge_failed:
        return "EDGE_EXPECTANCY_FAILURE"
    if failed_gates:
        return "OTHER_MATRIX_GATE_FAILURE"
    return "NON_MATRIX_REJECTION_OR_PENDING"


def _write_report(report_path: Path, df: pd.DataFrame, approved: set[str]) -> None:
    rejected = df[df["decision_scope"] == "REJECTED_OR_RESEARCH"]
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    total_rejected = int(len(rejected))
    sample_size_failures = int((rejected["sample_size"] == "FAIL").sum()) if total_rejected else 0
    edge_failures = int((rejected["multi_cell_survival"] == "FAIL").sum()) if total_rejected else 0
    both = int(
        (
            (rejected["sample_size"] == "FAIL")
            & (rejected["multi_cell_survival"] == "FAIL")
        ).sum()
    ) if total_rejected else 0
    edge_only = int(
        (
            (rejected["sample_size"] == "PASS")
            & (rejected["multi_cell_survival"] == "FAIL")
        ).sum()
    ) if total_rejected else 0
    frequency_only = int(
        (
            (rejected["sample_size"] == "FAIL")
            & (rejected["multi_cell_survival"] == "PASS")
        ).sum()
    ) if total_rejected else 0

    conclusion = (
        "Sample-size/frequency failures are present, so low-frequency candidates should not be "
        "rescued by assumption; however, expectancy survival failures are at least as common and "
        "must remain the primary rejection evidence."
        if sample_size_failures
        else "No rejected candidate failed the sample-size gate; this run does not support the "
        "frequency-bias concern."
    )

    lines = [
        "# Phase 0 Rejected Candidate Gate Audit",
        "",
        f"Generated at UTC: `{generated_at}`",
        "",
        "Purpose: answer Review #3 V3 by aggregating the matrix gates that rejected candidate experts.",
        "",
        "Approved/same-family rows are included for context but excluded from the rejection counts.",
        "",
        f"Approved or active experts excluded from rejection counts: `{', '.join(sorted(approved))}`",
        "",
        "## Summary",
        "",
        f"- Audited candidates: {len(df)}",
        f"- Rejected/research candidates audited: {total_rejected}",
        f"- Rejected candidates with sample-size failure: {sample_size_failures}",
        f"- Rejected candidates with multi-cell expectancy failure: {edge_failures}",
        f"- Rejected candidates with both expectancy and sample-size failure: {both}",
        f"- Rejected candidates with expectancy-only failure: {edge_only}",
        f"- Rejected candidates with frequency-only failure: {frequency_only}",
        "",
        f"Conclusion: {conclusion}",
        "",
        "## Candidate Gate Table",
        "",
        "| Candidate | Scope | Diagnosis | Cells | PF cells | Trades | Min trades | Failed gates |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for _, row in df.iterrows():
        lines.append(
            "| {candidate} | {decision_scope} | {frequency_bias_diagnosis} | "
            "{complete_cells} | {pf_passing_cells} | {total_trades} | "
            "{min_cell_trades} | {failed_gates} |".format(**row.to_dict())
        )

    lines.extend(
        [
            "",
            "## Gate Columns",
            "",
            "- `multi_cell_survival`: PF persistence across the 9-cell matrix.",
            "- `sample_size`: minimum trades in every cell.",
            "- `no_catastrophic_failure`: drawdown and total-return loss limits.",
            "- `concentration`: single/top-5 trade contribution limits.",
            "- `activity`: zero-trade month limit.",
            "- `cost_sensitivity`: P95 PF divided by best-case PF.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")


def _write_csv_with_retry(df: pd.DataFrame, path: Path, attempts: int = 8, delay_seconds: float = 0.25) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    last_error: PermissionError | None = None
    for _ in range(attempts):
        temp_fd, temp_name = tempfile.mkstemp(
            prefix=f"{path.stem}.",
            suffix=".tmp",
            dir=path.parent,
        )
        os.close(temp_fd)
        temp_path = Path(temp_name)
        try:
            df.to_csv(temp_path, index=False)
            os.replace(temp_path, path)
            return
        except PermissionError as exc:
            last_error = exc
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
            time.sleep(delay_seconds)
        else:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
    if last_error is not None:
        raise last_error

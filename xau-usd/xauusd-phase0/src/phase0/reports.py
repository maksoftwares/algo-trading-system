from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from phase0.aggregation import aggregate_matrix_results
from phase0.config import ConfigError, ProjectConfig
from phase0.data_contracts import GateResult, GateStatus
from phase0.gates import (
    evaluate_adversarial_gate,
    evaluate_decile_gate,
    evaluate_multisymbol_gate,
)
from phase0.hashing import hash_manifest_path, load_hash_manifest, sha256_file


@dataclass(frozen=True)
class ExpertReportOutput:
    expert: str
    report_path: Path
    matrix_status: str
    decile_status: str
    adversarial_status: str
    multisymbol_status: str
    hypothesis_match_status: str
    final_status: str
    failed_gates: tuple[str, ...]
    ten_gate_statuses: tuple[str, ...]


@dataclass(frozen=True)
class ReportGenerationOutput:
    expert_reports: list[ExpertReportOutput]
    verdict_path: Path


def generate_all_reports(config: ProjectConfig) -> ReportGenerationOutput:
    reports_dir = _reports_dir(config)
    reports_dir.mkdir(parents=True, exist_ok=True)
    manifest = {row.expert: row for row in load_hash_manifest(hash_manifest_path(config))}

    expert_outputs = [
        generate_expert_report(config, expert, manifest) for expert in _enabled_experts(config)
    ]
    verdict_path = reports_dir / "PHASE0_VERDICT.md"
    verdict_path.write_text(_render_consolidated_verdict(config, expert_outputs), encoding="utf-8")
    return ReportGenerationOutput(expert_outputs, verdict_path)


def generate_expert_report(
    config: ProjectConfig,
    expert: str,
    manifest: dict[str, Any] | None = None,
) -> ExpertReportOutput:
    reports_dir = _reports_dir(config)
    reports_dir.mkdir(parents=True, exist_ok=True)
    manifest = manifest or {row.expert: row for row in load_hash_manifest(hash_manifest_path(config))}

    metrics_df, matrix_gate_df = _load_or_create_matrix_artifacts(config, expert)
    hash_summary = _hash_summary(config, expert, manifest)
    decile_summary = _decile_summary(config, expert)
    multisymbol_summary = _multisymbol_summary(config, expert)
    adversarial_summary = _adversarial_summary(config, expert)

    matrix_status = _overall_status(matrix_gate_df["status"].astype(str).tolist())
    hypothesis_match_status = "PASS" if hash_summary["hash_match"] else "FAIL"
    ten_gate_rows = _ten_gate_rows(
        matrix_gate_df,
        decile_summary.gate,
        multisymbol_summary.gate,
        adversarial_summary.gate,
        hypothesis_match_status,
    )
    category_statuses = [
        matrix_status,
        decile_summary.status,
        adversarial_summary.status,
        multisymbol_summary.status,
        hypothesis_match_status,
    ]
    final_status = _final_status(category_statuses)
    failed_gates = _failed_gates(
        matrix_gate_df,
        decile_summary.gate,
        adversarial_summary.gate,
        multisymbol_summary.gate,
        hypothesis_match_status,
    )

    report_path = reports_dir / f"phase0_{expert}_results.md"
    report_path.write_text(
        _render_expert_report(
            config=config,
            expert=expert,
            metrics_df=metrics_df,
            matrix_gate_df=matrix_gate_df,
            hash_summary=hash_summary,
            decile_summary=decile_summary,
            multisymbol_summary=multisymbol_summary,
            adversarial_summary=adversarial_summary,
            matrix_status=matrix_status,
            hypothesis_match_status=hypothesis_match_status,
            final_status=final_status,
            ten_gate_rows=ten_gate_rows,
            failed_gates=failed_gates,
        ),
        encoding="utf-8",
    )

    return ExpertReportOutput(
        expert=expert,
        report_path=report_path,
        matrix_status=matrix_status,
        decile_status=decile_summary.status,
        adversarial_status=adversarial_summary.status,
        multisymbol_status=multisymbol_summary.status,
        hypothesis_match_status=hypothesis_match_status,
        final_status=final_status,
        failed_gates=tuple(failed_gates),
        ten_gate_statuses=tuple(str(row["Status"]) for row in ten_gate_rows),
    )


@dataclass(frozen=True)
class OptionalGateSummary:
    status: str
    artifact_path: Path
    table: pd.DataFrame
    gate: GateResult


def _load_or_create_matrix_artifacts(config: ProjectConfig, expert: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    reports_dir = _reports_dir(config)
    metrics_path = reports_dir / f"{expert}_matrix_metrics.csv"
    gates_path = reports_dir / f"{expert}_gate_results.csv"
    if not metrics_path.exists() or not gates_path.exists():
        aggregate_matrix_results(config, expert)
    if not metrics_path.exists() or not gates_path.exists():
        raise ConfigError(f"Matrix report artifacts were not created for expert {expert}.")
    return pd.read_csv(metrics_path), pd.read_csv(gates_path)


def _hash_summary(config: ProjectConfig, expert: str, manifest: dict[str, Any]) -> dict[str, Any]:
    row = manifest.get(expert)
    if row is None:
        configured_file = str(config.phase0["experts"][expert]["hypothesis_file"])
        hypothesis_path = config.root / configured_file
        current_hash = sha256_file(hypothesis_path)
        return {
            "hypothesis_file": configured_file,
            "registered_sha256": "MISSING",
            "current_sha256": current_hash,
            "hash_match": False,
        }

    hypothesis_path = config.root / row.hypothesis_file
    current_hash = sha256_file(hypothesis_path)
    return {
        "hypothesis_file": row.hypothesis_file,
        "registered_sha256": row.sha256,
        "current_sha256": current_hash,
        "hash_match": current_hash == row.sha256,
    }


def _decile_summary(config: ProjectConfig, expert: str) -> OptionalGateSummary:
    path = config.root / "outputs" / "decile_results" / f"{expert}_decile_results.csv"
    if not path.exists():
        return _pending_optional_summary("decile_persistence", path)
    table = pd.read_csv(path)
    gate = evaluate_decile_gate(table, config.phase0["gates"])
    return OptionalGateSummary(gate.status, path, table, gate)


def _multisymbol_summary(config: ProjectConfig, expert: str) -> OptionalGateSummary:
    path = config.root / "outputs" / "multisymbol_results" / f"{expert}_multisymbol_summary.csv"
    if not path.exists():
        return _pending_optional_summary("multi_symbol_consistency", path)
    table = pd.read_csv(path)
    mechanism = _xau_specific_mechanism(config, expert, table)
    gate = evaluate_multisymbol_gate(table, config.phase0["gates"], mechanism)
    return OptionalGateSummary(gate.status, path, table, gate)


def _adversarial_summary(config: ProjectConfig, expert: str) -> OptionalGateSummary:
    path = config.root / "outputs" / "adversarial_review" / f"{expert}_losing_trades_review.csv"
    if not path.exists():
        return _pending_optional_summary("adversarial_review", path)

    table = pd.read_csv(path)
    if table.empty:
        logic_gap_failures_pct = 0.0
        manual_review_complete = True
    else:
        required = ("manual_failure_class", "reviewer", "reviewed_at_utc")
        missing = [column for column in required if column not in table.columns]
        if missing:
            raise ConfigError(
                f"Adversarial review {path} missing required column(s): {', '.join(missing)}."
            )
        reviewed = table[list(required)].fillna("").astype(str).apply(lambda row: all(row), axis=1)
        manual_review_complete = bool(reviewed.all())
        reviewed_rows = table[reviewed]
        denominator = len(reviewed_rows)
        if denominator == 0:
            logic_gap_failures_pct = None
        else:
            logic_gaps = (reviewed_rows["manual_failure_class"].astype(str) == "LOGIC_GAP").sum()
            logic_gap_failures_pct = float(logic_gaps) / denominator * 100.0

    gate = evaluate_adversarial_gate(
        logic_gap_failures_pct,
        config.phase0["gates"],
        manual_review_complete,
    )
    return OptionalGateSummary(gate.status, path, table, gate)


def _pending_optional_summary(gate_name: str, path: Path) -> OptionalGateSummary:
    gate = GateResult(
        name=gate_name,
        status="PENDING",
        threshold="artifact required",
        observed=f"missing {path}",
        message="Required Phase 0 artifact has not been generated yet.",
    )
    table = pd.DataFrame([{"status": "PENDING", "artifact": str(path), "message": gate.message}])
    return OptionalGateSummary("PENDING", path, table, gate)


def _xau_specific_mechanism(config: ProjectConfig, expert: str, table: pd.DataFrame) -> str:
    if "xau_specific_mechanism" in table.columns:
        values = table["xau_specific_mechanism"].dropna().astype(str)
        if not values.empty:
            return values.iloc[0]
    path = config.root / "outputs" / "multisymbol_results" / f"{expert}_xau_specific_mechanism.md"
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return ""


def _render_expert_report(
    *,
    config: ProjectConfig,
    expert: str,
    metrics_df: pd.DataFrame,
    matrix_gate_df: pd.DataFrame,
    hash_summary: dict[str, Any],
    decile_summary: OptionalGateSummary,
    multisymbol_summary: OptionalGateSummary,
    adversarial_summary: OptionalGateSummary,
    matrix_status: str,
    hypothesis_match_status: str,
    final_status: str,
    ten_gate_rows: list[dict[str, str]],
    failed_gates: list[str],
) -> str:
    generated_at = _generated_at_utc()
    matrix_columns = [
        "cell_id",
        "tick_source",
        "cost_model",
        "trade_count",
        "profit_factor",
        "total_return_pct",
        "max_drawdown_pct",
        "max_consecutive_zero_trade_months",
        "p95_to_best_pf_ratio",
    ]
    gate_columns = ["name", "status", "threshold", "observed", "message"]

    sections = [
        f"# Phase 0 Results: {_title(expert)}",
        "",
        f"Generated at UTC: {generated_at}",
        "",
        "## Hypothesis",
        "",
        _markdown_table(
            [
                {
                    "Field": "Hypothesis file name",
                    "Value": hash_summary["hypothesis_file"],
                },
                {
                    "Field": "Registered SHA256",
                    "Value": hash_summary["registered_sha256"],
                },
                {
                    "Field": "Current SHA256",
                    "Value": hash_summary["current_sha256"],
                },
                {
                    "Field": "Hash match",
                    "Value": "yes" if hash_summary["hash_match"] else "no",
                },
            ],
            ["Field", "Value"],
        ),
        "",
        "## 9-Cell Matrix Results",
        "",
        _markdown_table(_frame_rows(metrics_df, matrix_columns), matrix_columns),
        "",
        "## Gate Pass/Fail Summary",
        "",
        _markdown_table(_frame_rows(matrix_gate_df, gate_columns), gate_columns),
        "",
        "## Decile Test",
        "",
        _optional_gate_block(decile_summary, ["decile_id", "trade_count", "profit_factor", "verdict"]),
        "",
        "## Adversarial Search",
        "",
        _adversarial_block(adversarial_summary),
        "",
        "## Multi-Symbol Check",
        "",
        _optional_gate_block(multisymbol_summary, ["symbol", "trade_count", "profit_factor", "verdict"]),
        "",
        "## Hypothesis vs Reality",
        "",
        _markdown_table(_hypothesis_vs_reality(config, expert, metrics_df), ["Claim", "Hypothesis", "Observed", "Status"]),
        "",
        "## Ten-Gate Detail",
        "",
        _markdown_table(ten_gate_rows, ["Gate", "Name", "Status", "Threshold", "Observed"]),
        "",
        "## Final Verdict",
        "",
        _markdown_table(
            [
                {
                    "9-cell": matrix_status,
                    "Decile": decile_summary.status,
                    "Adversarial": adversarial_summary.status,
                    "Multi-symbol": multisymbol_summary.status,
                    "Hypothesis-match": hypothesis_match_status,
                    "FINAL": final_status,
                }
            ],
            ["9-cell", "Decile", "Adversarial", "Multi-symbol", "Hypothesis-match", "FINAL"],
        ),
        "",
        "## Failed Gates",
        "",
        _bullet_list(failed_gates) if failed_gates else "None.",
        "",
        "## Passing Evidence",
        "",
        _bullet_list(_passing_evidence(matrix_gate_df, decile_summary, adversarial_summary, multisymbol_summary, hash_summary)),
        "",
    ]
    return "\n".join(sections)


def _render_consolidated_verdict(
    config: ProjectConfig,
    expert_outputs: list[ExpertReportOutput],
) -> str:
    rows = [
        {
            "Expert": output.expert,
            "9-cell": output.matrix_status,
            "Decile": output.decile_status,
            "Adversarial": output.adversarial_status,
            "Multi-symbol": output.multisymbol_status,
            "Hypothesis-match": output.hypothesis_match_status,
            "FINAL": output.final_status,
        }
        for output in expert_outputs
    ]
    passing = [output.expert for output in expert_outputs if output.final_status == "PASS"]
    rejected = [output.expert for output in expert_outputs if output.final_status == "FAIL"]
    pending = [output.expert for output in expert_outputs if output.final_status == "PENDING"]
    action = _recommended_action(len(passing), len(expert_outputs))
    ten_gate_columns = [
        "Expert",
        "Gate 1",
        "Gate 2",
        "Gate 3",
        "Gate 4",
        "Gate 5",
        "Gate 6",
        "Gate 7",
        "Gate 8",
        "Gate 9",
        "Gate 10",
        "FINAL",
    ]
    ten_gate_rows = [
        {
            **{"Expert": output.expert},
            **{f"Gate {index}": status for index, status in enumerate(output.ten_gate_statuses, start=1)},
            **{"FINAL": output.final_status},
        }
        for output in expert_outputs
    ]

    return "\n".join(
        [
            "# Phase 0 Consolidated Verdict",
            "",
            f"Generated at UTC: {_generated_at_utc()}",
            "",
            "## Verdict Table",
            "",
            _markdown_table(
                rows,
                ["Expert", "9-cell", "Decile", "Adversarial", "Multi-symbol", "Hypothesis-match", "FINAL"],
            ),
            "",
            "## Ten-Gate Detail",
            "",
            _markdown_table(ten_gate_rows, ten_gate_columns),
            "",
            "## Experts Approved for Phase 1",
            "",
            _bullet_list(passing) if passing else "None.",
            "",
            "## Experts Rejected",
            "",
            _bullet_list(rejected) if rejected else "None.",
            "",
            "## Experts Pending Manual Review",
            "",
            _bullet_list(pending) if pending else "None.",
            "",
            "## Recommended Action",
            "",
            action,
            "",
            "## Report Files",
            "",
            _bullet_list([_relative(config, output.report_path) for output in expert_outputs]),
            "",
        ]
    )


def _optional_gate_block(summary: OptionalGateSummary, preferred_columns: list[str]) -> str:
    gate_rows = [
        {
            "name": summary.gate.name,
            "status": summary.gate.status,
            "threshold": summary.gate.threshold,
            "observed": summary.gate.observed,
            "message": summary.gate.message,
        }
    ]
    table = summary.table
    columns = [column for column in preferred_columns if column in table.columns]
    if not columns:
        columns = list(table.columns)
    return "\n\n".join(
        [
            _markdown_table(gate_rows, ["name", "status", "threshold", "observed", "message"]),
            _markdown_table(_frame_rows(table, columns), columns),
        ]
    )


def _adversarial_block(summary: OptionalGateSummary) -> str:
    table = summary.table
    if table.empty:
        review_rows = [
            {
                "reviewed_losing_trades": 0,
                "logic_gap_failures": 0,
                "logic_gap_failures_pct": 0.0,
            }
        ]
    elif {"manual_failure_class", "reviewer", "reviewed_at_utc"}.issubset(table.columns):
        reviewed = (
            table[["manual_failure_class", "reviewer", "reviewed_at_utc"]]
            .fillna("")
            .astype(str)
            .apply(lambda row: all(row), axis=1)
        )
        reviewed_table = table[reviewed]
        logic_gaps = int((reviewed_table["manual_failure_class"].astype(str) == "LOGIC_GAP").sum())
        denominator = len(reviewed_table)
        pct = 0.0 if denominator == 0 else logic_gaps / denominator * 100.0
        review_rows = [
            {
                "reviewed_losing_trades": denominator,
                "logic_gap_failures": logic_gaps,
                "logic_gap_failures_pct": pct,
            }
        ]
    else:
        review_rows = _frame_rows(table, list(table.columns))

    gate_rows = [
        {
            "name": summary.gate.name,
            "status": summary.gate.status,
            "threshold": summary.gate.threshold,
            "observed": summary.gate.observed,
            "message": summary.gate.message,
        }
    ]
    return "\n\n".join(
        [
            _markdown_table(gate_rows, ["name", "status", "threshold", "observed", "message"]),
            _markdown_table(
                review_rows,
                ["reviewed_losing_trades", "logic_gap_failures", "logic_gap_failures_pct"],
            )
            if review_rows and "reviewed_losing_trades" in review_rows[0]
            else _markdown_table(review_rows, list(review_rows[0]) if review_rows else []),
        ]
    )


def _hypothesis_vs_reality(
    config: ProjectConfig,
    expert: str,
    metrics_df: pd.DataFrame,
) -> list[dict[str, str]]:
    hypothesis_path = config.root / str(config.phase0["experts"][expert]["hypothesis_file"])
    expectations = _extract_expectations(hypothesis_path)
    total_trades = int(pd.to_numeric(metrics_df["trade_count"], errors="coerce").fillna(0).sum())
    pf = pd.to_numeric(metrics_df["profit_factor"].replace("inf", math.inf), errors="coerce")
    losing_month = pd.to_numeric(metrics_df["losing_month_pct"], errors="coerce")
    worst_month = pd.to_numeric(metrics_df["worst_month_usd"], errors="coerce")
    zero_months = pd.to_numeric(metrics_df["max_consecutive_zero_trade_months"], errors="coerce")
    avg_r = pd.to_numeric(metrics_df["avg_trade_R"], errors="coerce")
    median_r = pd.to_numeric(metrics_df["median_trade_R"], errors="coerce")

    return [
        {
            "Claim": "Trade count",
            "Hypothesis": expectations.get("Expected trade count per year", "Not specified"),
            "Observed": f"{total_trades} trades across {len(metrics_df)} matrix cells",
            "Status": _expectation_status(expectations.get("Expected trade count per year", "")),
        },
        {
            "Claim": "Cost-adjusted PF",
            "Hypothesis": expectations.get("Expected cost-adjusted PF", "Not specified"),
            "Observed": f"median PF {_format_value(pf.median())}; min PF {_format_value(pf.min())}",
            "Status": _expectation_status(expectations.get("Expected cost-adjusted PF", "")),
        },
        {
            "Claim": "Losing-month percentage",
            "Hypothesis": expectations.get("Expected losing-month percentage", "Not specified"),
            "Observed": f"worst cell {_format_value(losing_month.max())}%",
            "Status": _expectation_status(expectations.get("Expected losing-month percentage", "")),
        },
        {
            "Claim": "Worst single month",
            "Hypothesis": expectations.get("Expected worst single month", "Not specified"),
            "Observed": f"${_format_value(worst_month.min())}",
            "Status": _expectation_status(expectations.get("Expected worst single month", "")),
        },
        {
            "Claim": "Max consecutive zero months",
            "Hypothesis": expectations.get("Expected max consecutive zero months", "Not specified"),
            "Observed": _format_value(zero_months.max()),
            "Status": _expectation_status(expectations.get("Expected max consecutive zero months", "")),
        },
        {
            "Claim": "R-multiple distribution",
            "Hypothesis": expectations.get("Expected R-multiple distribution", "Not specified"),
            "Observed": f"avg R median {_format_value(avg_r.median())}; median R median {_format_value(median_r.median())}",
            "Status": _expectation_status(expectations.get("Expected R-multiple distribution", "")),
        },
    ]


def _extract_expectations(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    expectations: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("Expected ") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        expectations[key.strip()] = value.strip() or "Not specified"
    return expectations


def _expectation_status(value: str) -> str:
    text = value.strip().lower()
    if not text or text.startswith("tbd"):
        return "PENDING_HYPOTHESIS_VALUE"
    return "OBSERVED"


def _failed_gates(
    matrix_gate_df: pd.DataFrame,
    decile_gate: GateResult,
    adversarial_gate: GateResult,
    multisymbol_gate: GateResult,
    hypothesis_match_status: str,
) -> list[str]:
    failed: list[str] = []
    for _, row in matrix_gate_df.iterrows():
        if str(row["status"]) == "FAIL":
            failed.append(f"9-cell:{row['name']} - {row['message']}")
    for prefix, gate in (
        ("Decile", decile_gate),
        ("Adversarial", adversarial_gate),
        ("Multi-symbol", multisymbol_gate),
    ):
        if gate.status == "FAIL":
            failed.append(f"{prefix}:{gate.name} - {gate.message}")
    if hypothesis_match_status == "FAIL":
        failed.append("Hypothesis-match - current SHA256 does not match registered SHA256")
    return failed


def _ten_gate_rows(
    matrix_gate_df: pd.DataFrame,
    decile_gate: GateResult,
    multisymbol_gate: GateResult,
    adversarial_gate: GateResult,
    hypothesis_match_status: str,
) -> list[dict[str, str]]:
    matrix_by_name = {
        str(row["name"]): row.to_dict()
        for _, row in matrix_gate_df.iterrows()
    }
    rows: list[dict[str, str]] = []
    for gate_number, gate_name, label in (
        (1, "multi_cell_survival", "Multi-cell survival"),
        (2, "sample_size", "Sample size"),
        (3, "no_catastrophic_failure", "No catastrophic failure"),
        (4, "concentration", "Concentration"),
        (5, "activity", "Activity"),
        (6, "cost_sensitivity", "Cost sensitivity"),
    ):
        gate_row = matrix_by_name.get(gate_name)
        if gate_row is None:
            rows.append(_ten_gate_row(gate_number, label, "PENDING", "matrix gate required", "missing"))
            continue
        rows.append(
            _ten_gate_row(
                gate_number,
                label,
                str(gate_row["status"]),
                str(gate_row["threshold"]),
                str(gate_row["observed"]),
            )
        )

    for gate_number, label, gate in (
        (7, "Decile persistence", decile_gate),
        (8, "Multi-symbol consistency", multisymbol_gate),
        (9, "Adversarial review", adversarial_gate),
    ):
        rows.append(
            _ten_gate_row(
                gate_number,
                label,
                gate.status,
                gate.threshold,
                gate.observed,
            )
        )

    rows.append(
        _ten_gate_row(
            10,
            "Hypothesis SHA256 lock",
            hypothesis_match_status,
            "current SHA256 equals registered SHA256",
            "hash match" if hypothesis_match_status == "PASS" else "hash mismatch",
        )
    )
    return rows


def _ten_gate_row(
    gate_number: int,
    name: str,
    status: str,
    threshold: str,
    observed: str,
) -> dict[str, str]:
    return {
        "Gate": f"Gate {gate_number}",
        "Name": name,
        "Status": status,
        "Threshold": threshold,
        "Observed": observed,
    }


def _passing_evidence(
    matrix_gate_df: pd.DataFrame,
    decile_summary: OptionalGateSummary,
    adversarial_summary: OptionalGateSummary,
    multisymbol_summary: OptionalGateSummary,
    hash_summary: dict[str, Any],
) -> list[str]:
    evidence = [
        f"9-cell:{row['name']} - {row['observed']}"
        for _, row in matrix_gate_df.iterrows()
        if str(row["status"]) == "PASS"
    ]
    for prefix, summary in (
        ("Decile", decile_summary),
        ("Adversarial", adversarial_summary),
        ("Multi-symbol", multisymbol_summary),
    ):
        if _is_pass(summary.status):
            evidence.append(f"{prefix}:{summary.gate.name} - {summary.gate.observed}")
    if hash_summary["hash_match"]:
        evidence.append("Hypothesis SHA256 matches the registered manifest.")
    return evidence or ["No passing evidence yet."]


def _overall_status(statuses: list[str]) -> str:
    if any(status == "FAIL" for status in statuses):
        return "FAIL"
    if any(status == "PENDING" for status in statuses):
        return "PENDING"
    return "PASS"


def _final_status(statuses: list[str]) -> str:
    if any(status == "FAIL" for status in statuses):
        return "FAIL"
    if any(status == "PENDING" for status in statuses):
        return "PENDING"
    return "PASS"


def _is_pass(status: str | GateStatus) -> bool:
    return str(status).startswith("PASS")


def _recommended_action(pass_count: int, expert_count: int) -> str:
    if pass_count >= 3:
        return "Proceed to Phase 1 with the 3-expert v1 package."
    if pass_count in (1, 2):
        return f"Proceed to Phase 1 with the {pass_count}-expert reduced package."
    if expert_count == 0:
        return "Stop: no enabled experts were available for Phase 0 verdict generation."
    return "Stop before Phase 1: no expert currently has a full PASS."


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not columns:
        return "No rows."
    if not rows:
        return "No rows."
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| "
        + " | ".join(_escape_markdown(_format_value(row.get(column, ""))) for column in columns)
        + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def _frame_rows(df: pd.DataFrame, columns: list[str]) -> list[dict[str, Any]]:
    selected_columns = [column for column in columns if column in df.columns]
    return [
        {column: row[column] for column in selected_columns}
        for _, row in df[selected_columns].iterrows()
    ]


def _bullet_list(items: list[str] | tuple[str, ...]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _format_value(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    if isinstance(value, float):
        if math.isinf(value):
            return "inf" if value > 0 else "-inf"
        return f"{value:.4g}"
    return str(value)


def _escape_markdown(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _reports_dir(config: ProjectConfig) -> Path:
    return config.root / str(config.phase0["outputs"].get("reports", "outputs/reports"))


def _enabled_experts(config: ProjectConfig) -> list[str]:
    return [
        expert for expert, details in config.phase0["experts"].items() if details.get("enabled", False)
    ]


def _title(expert: str) -> str:
    return expert.replace("_", " ").title()


def _generated_at_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _relative(config: ProjectConfig, path: Path) -> str:
    try:
        return path.relative_to(config.root).as_posix()
    except ValueError:
        return str(path)

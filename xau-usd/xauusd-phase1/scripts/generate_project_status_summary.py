from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_JSON = Path("status_summary.json")
DEFAULT_MD = Path("status_summary.md")

GOVERNANCE_SCHEMA = "a1_xau_governance_status_v1"
GOVERNANCE_POINTER_SCHEMA = "a1_xau_status_pointer_v1"
GOVERNANCE_NORTH_STAR = (
    "Build an automated XAUUSD system that produces positive net returns over rolling 6- and 12-month "
    "periods, survives realistic costs and regime changes, limits portfolio equity drawdown, and can "
    "eventually support controlled withdrawals from accumulated profits."
)
GOVERNANCE_DOCUMENT_NAMES = {
    "master_direction": "A1_XAU_PROFITABLE_SYSTEM_MASTER_DIRECTION_2026_07_10.md",
    "current_research_freeze": "A1_XAU_CURRENT_RESEARCH_FREEZE_2026_07_10.md",
    "router_entry_hold_path_audit_prereg": "A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_PREREG_2026_07_10.md",
    "independent_specialist_primary_direction": (
        "A1_XAU_INDEPENDENT_SPECIALIST_PRIMARY_DIRECTION_2026_07_12.md"
    ),
}
GOVERNANCE_REQUIRED_STATEMENTS = [
    "R6 = primary independent specialist lane",
    "NP1-A = next action",
    "R1+R2 = research control only",
    "R3 = excluded",
    "R4 = no survivor",
    "router entry/hold audit = deferred control diagnostic",
    "parallel specialist lane = false",
    "all history through 2026-06-30 = DEVELOPMENT_DATA",
    "no demo/live/broker authorization",
]
GOVERNANCE_CONTROL_DIAGNOSTIC_COMPATIBILITY_STATEMENTS = [
    "R1+R2 = current research control",
    "R3 = standalone shadow only",
    "R3 portfolio use = killed by DD gate",
    "R4 = no survivor",
    "no demo/live authorization",
    "router entry/hold path audit preregistration remains frozen",
]
CURRENT_CONTROL_LEDGER_SHA256 = "47cbe6a562ba2874d93a97255affbde613566ed06340a149ed2795d69a5dae52"
CURRENT_CONTROL_LEDGER_PATH = (
    "xau-usd/xauusd-phase1/outputs/reports/"
    "A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_"
    "current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10_KEPT.csv"
)
GOVERNANCE_RULE_ADMISSIBILITY_SOURCES = [
    {
        "source_id": "h4_d1_long_best_box2_atr80",
        "admissibility_issue_type": "FORBIDDEN_SELECTION_RULE",
        "retained_rule_type": "PREVIOUS_MONTH_PNL_HEALTH_GATE",
        "retained_rule": "Previous-month P/L health gate (enabled; minimum net -$50)",
    },
    {
        "source_id": "r1_h1_pullback_long_v1",
        "admissibility_issue_type": "FORBIDDEN_SELECTION_RULE",
        "retained_rule_type": "R1_DIRECTIONAL_SESSION_GATE",
        "retained_rule": "R1 directional session 09 <= hour < 15",
    },
    {
        "source_id": "r2_pullback_rejection_short_v1",
        "admissibility_issue_type": "FORBIDDEN_SELECTION_RULE",
        "retained_rule_type": "R2_DIRECTIONAL_SESSION_GATE",
        "retained_rule": "R2 directional session 05 <= hour < 19",
    },
    {
        "source_id": "r2_continuation_short_v1",
        "admissibility_issue_type": "SOURCE_LOCAL_CONTAINMENT_NOT_ADMISSION_EVIDENCE",
        "retained_rule_type": "R2_DAILY_LOSS_STOP",
        "retained_rule": "R2 $10 daily-loss stop",
    },
]


def generate_project_status_summary(
    repo_root: Path,
    output_json: Path | None = None,
    output_md: Path | None = None,
    now: datetime | None = None,
) -> tuple[Path, Path]:
    repo_root = repo_root.resolve()
    output_json = (output_json or repo_root / DEFAULT_JSON).resolve()
    output_md = (output_md or repo_root / DEFAULT_MD).resolve()
    now = now or datetime.now(timezone.utc)

    phase1_root = repo_root / "xau-usd" / "xauusd-phase1"
    governance_documents = {
        key: phase1_root / "docs" / filename for key, filename in GOVERNANCE_DOCUMENT_NAMES.items()
    }
    present_governance_documents = {
        key: path for key, path in governance_documents.items() if path.is_file()
    }
    if present_governance_documents and len(present_governance_documents) != len(
        governance_documents
    ):
        missing_documents = [
            path.relative_to(repo_root).as_posix()
            for key, path in governance_documents.items()
            if key not in present_governance_documents
        ]
        raise FileNotFoundError(
            "A1 governance document set is incomplete; missing: "
            + ", ".join(missing_documents)
        )

    if len(present_governance_documents) == len(governance_documents):
        return _generate_governance_status(
            repo_root=repo_root,
            phase1_root=phase1_root,
            output_json=output_json,
            output_md=output_md,
            now=now,
            documents=governance_documents,
        )

    phase1_reports = phase1_root / "outputs" / "reports"
    quarantine_report = phase1_reports / "XAUUSD_ROUND_FAMILY_QUARANTINE_APPLIED_2026_06_17.json"
    a3_attachment_report = phase1_reports / "A3_TIER1_COMPAT_BROKER_ACTION_ATTACHMENT_2026_06_17.json"
    a3_review_followup_report = phase1_reports / "A3_REVIEW_FOLLOWUP_STATUS_2026_06_18.json"
    a3_pause_report = phase1_reports / "A3_EMERGENCY_PAUSE_APPLIED_2026_06_18.json"
    a3_pause_verify_report = phase1_reports / "A3_EMERGENCY_PAUSE_VERIFY_ONLY_2026_06_18.json"
    a3_p1_p2_report = phase1_reports / "A3_REPAIR_P1_P2_IMPLEMENTATION_REPORT_2026_06_18.json"
    runtime_inventory_csv = phase1_reports / "RUNTIME_CHART_INVENTORY_FORENSIC_2026_06_21.csv"
    a1_momentum_attachment_report = phase1_reports / "A1_XAU_M5_MOMENTUM_RR2_LONG_ONLY_FORWARD_ATTACHMENT_2026_07_02.json"
    a1_momentum_attachment_md = phase1_reports / "A1_XAU_M5_MOMENTUM_RR2_LONG_ONLY_FORWARD_ATTACHMENT_2026_07_02.md"
    a1_momentum_forward_spec = phase1_root / "docs" / "A1_XAU_M5_MOMENTUM_RR2_LONG_ONLY_FORWARD_V0_2026_07_02.md"
    a1_momentum_forward_spec_manifest = (
        phase1_root / "docs" / "A1_XAU_M5_MOMENTUM_RR2_LONG_ONLY_FORWARD_V0_2026_07_02.sha256.json"
    )
    a1_momentum_backtest_md = phase1_reports / "A1_XAU_M5_MOMENTUM_MT5_BACKTEST_JUNE2026.md"
    a1_momentum_backtest_json = (
        phase1_reports / "mt5_backtests" / "A1_XAU_M5_MOMENTUM_JUNE2026_SUMMARY.json"
    )
    a1_momentum_variant_backtest_md = phase1_reports / "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_Q2_2026.md"
    a1_momentum_variant_backtest_json = phase1_reports / "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_Q2_2026.json"
    a1_momentum_long_diagnosis_md = phase1_reports / "A1_XAU_M5_MOMENTUM_LONG_FAILURE_DIAGNOSIS_Q2_2026.md"
    a1_momentum_frequency_repair_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FREQUENCY_FIRST_V4_COMBO_RANK1_VERDICT_2026_07_02.md"
    )
    a1_momentum_frequency_repair_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FREQUENCY_FIRST_V4_COMBO_RANK1_VERDICT_2026_07_02.json"
    )
    a1_momentum_frequency_replacement_readiness = (
        phase1_root / "docs" / "A1_XAU_M5_MOMENTUM_FREQ_FIRST_V4_DEMO_REPLACEMENT_READINESS_2026_07_02.md"
    )
    a1_momentum_frequency_v6_diagnostic = (
        phase1_root / "docs" / "A1_XAU_M5_MOMENTUM_FREQ_FIRST_V6_DIAGNOSTIC_VERDICT_2026_07_02.md"
    )
    a1_momentum_frequency_v7_pullback = (
        phase1_root / "docs" / "A1_XAU_M5_MOMENTUM_FREQ_FIRST_V7_PULLBACK_VERDICT_2026_07_02.md"
    )
    a1_momentum_frequency_v8_compression = (
        phase1_root / "docs" / "A1_XAU_M5_MOMENTUM_FREQ_FIRST_V8_COMPRESSION_VERDICT_2026_07_02.md"
    )
    a1_momentum_frequency_v9_sweep = (
        phase1_root / "docs" / "A1_XAU_M5_MOMENTUM_FREQ_FIRST_V9_SWEEP_RECLAIM_VERDICT_2026_07_02.md"
    )
    a1_momentum_frequency_v10_opening_range = (
        phase1_root / "docs" / "A1_XAU_M5_MOMENTUM_FREQ_FIRST_V10_OPENING_RANGE_VERDICT_2026_07_02.md"
    )
    a1_momentum_frequency_v11_ema_trend = (
        phase1_root / "docs" / "A1_XAU_M5_MOMENTUM_FREQ_FIRST_V11_EMA_TREND_VERDICT_2026_07_02.md"
    )
    a1_momentum_frequency_v12_ema_trend_mask = (
        phase1_root / "docs" / "A1_XAU_M5_MOMENTUM_FREQ_FIRST_V12_EMA_TREND_MASK_VERDICT_2026_07_02.md"
    )
    a1_momentum_frequency_v13_directional_mask = (
        phase1_root / "docs" / "A1_XAU_M5_MOMENTUM_FREQ_FIRST_V13_DIRECTIONAL_MASK_VERDICT_2026_07_02.md"
    )
    a1_momentum_frequency_requirement_verdict = (
        phase1_root / "docs" / "A1_XAU_M5_MOMENTUM_FREQUENCY_REQUIREMENT_VERDICT_2026_07_02.md"
    )
    a1_momentum_portfolio_diagnostic_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_PORTFOLIO_COMBINATION_DIAGNOSTIC_2026_07_02.md"
    )
    a1_momentum_portfolio_diagnostic_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_PORTFOLIO_COMBINATION_DIAGNOSTIC_2026_07_02.json"
    )
    a1_momentum_portfolio_forward_draft = (
        phase1_root / "docs" / "A1_XAU_M5_MOMENTUM_V4_V13_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md"
    )
    a1_momentum_broad_portfolio_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_BROAD_PORTFOLIO_SEARCH_2026_07_02.md"
    )
    a1_momentum_broad_portfolio_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_BROAD_PORTFOLIO_SEARCH_2026_07_02.json"
    )
    a1_momentum_broad_portfolio_verdict = (
        phase1_root / "docs" / "A1_XAU_M5_MOMENTUM_BROAD_PORTFOLIO_SEARCH_VERDICT_2026_07_02.md"
    )
    a1_momentum_clean_portfolio_forward_draft = (
        phase1_root / "docs" / "A1_XAU_M5_MOMENTUM_CLEAN_LONG_SHORT_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md"
    )
    a1_momentum_deep_portfolio_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_SEARCH_2026_07_02.md"
    )
    a1_momentum_deep_portfolio_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_SEARCH_2026_07_02.json"
    )
    a1_momentum_deep_portfolio_stress_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_STRESS_2026_07_02.md"
    )
    a1_momentum_deep_portfolio_stress_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_STRESS_2026_07_02.json"
    )
    a1_momentum_deep_portfolio_verdict = (
        phase1_root / "docs" / "A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_SEARCH_VERDICT_2026_07_02.md"
    )
    a1_momentum_deep_portfolio_forward_draft = (
        phase1_root / "docs" / "A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md"
    )
    a1_momentum_robust_portfolio_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_SEARCH_2026_07_02.md"
    )
    a1_momentum_robust_portfolio_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_SEARCH_2026_07_02.json"
    )
    a1_momentum_robust_portfolio_stress_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_STRESS_2026_07_02.md"
    )
    a1_momentum_robust_portfolio_stress_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_STRESS_2026_07_02.json"
    )
    a1_momentum_robust_portfolio_forward_draft = (
        phase1_root / "docs" / "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md"
    )
    a1_momentum_robust_portfolio_walkforward_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_WALKFORWARD_2026_07_02.md"
    )
    a1_momentum_robust_portfolio_walkforward_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_WALKFORWARD_2026_07_02.json"
    )
    a1_momentum_robust_portfolio_repair_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_REPAIR_DIAGNOSTIC_2026_07_02.md"
    )
    a1_momentum_robust_portfolio_repair_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_REPAIR_DIAGNOSTIC_2026_07_02.json"
    )
    a1_momentum_robust_repair_walkforward_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_WALKFORWARD_2026_07_02.md"
    )
    a1_momentum_robust_repair_walkforward_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_WALKFORWARD_2026_07_02.json"
    )
    a1_momentum_robust_repair_forward_draft = (
        phase1_root / "docs" / "A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_FORWARD_DRAFT_2026_07_02.md"
    )
    a1_momentum_daily_fit_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_DAILY_FIT_PORTFOLIO_SEARCH_2026_07_02.md"
    )
    a1_momentum_daily_fit_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_DAILY_FIT_PORTFOLIO_SEARCH_2026_07_02.json"
    )
    a1_momentum_daily_fit_forward_draft = (
        phase1_root / "docs" / "A1_XAU_M5_MOMENTUM_DAILY_FIT_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md"
    )
    a1_momentum_daily_fit_stress_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_DAILY_FIT_PORTFOLIO_STRESS_2026_07_02.md"
    )
    a1_momentum_daily_fit_stress_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_DAILY_FIT_PORTFOLIO_STRESS_2026_07_02.json"
    )
    a1_momentum_daily_fit_repair_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_DAILY_FIT_REPAIR_DIAGNOSTIC_2026_07_02.md"
    )
    a1_momentum_daily_fit_repair_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_DAILY_FIT_REPAIR_DIAGNOSTIC_2026_07_02.json"
    )
    a1_momentum_daily_fit_repair_forward_draft = (
        phase1_root / "docs" / "A1_XAU_M5_MOMENTUM_DAILY_FIT_REPAIR_FORWARD_DRAFT_2026_07_02.md"
    )
    a1_momentum_daily_guard_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_DAILY_GUARD_SEARCH_2026_07_02.md"
    )
    a1_momentum_daily_guard_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_DAILY_GUARD_SEARCH_2026_07_02.json"
    )
    a1_momentum_daily_guard_forward_draft = (
        phase1_root / "docs" / "A1_XAU_M5_MOMENTUM_DAILY_GUARD_FORWARD_DRAFT_2026_07_02.md"
    )
    a1_momentum_daily_shape_optimizer_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_DAILY_SHAPE_OPTIMIZER_2026_07_02.md"
    )
    a1_momentum_pocket_portfolio_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_POCKET_PORTFOLIO_SEARCH_2026_07_02.md"
    )
    a1_momentum_pocket_portfolio_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_POCKET_PORTFOLIO_SEARCH_2026_07_02.json"
    )
    a1_momentum_pocket_portfolio_csv = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_POCKET_PORTFOLIO_SEARCH_2026_07_02.csv"
    )
    a1_momentum_daily_state_guard_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_DAILY_STATE_GUARD_SEARCH_2026_07_02.md"
    )
    a1_momentum_daily_state_guard_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_DAILY_STATE_GUARD_SEARCH_2026_07_02.json"
    )
    a1_momentum_daily_state_guard_csv = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_DAILY_STATE_GUARD_SEARCH_2026_07_02.csv"
    )
    a1_momentum_feature_loss_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_LOSS_CLUSTERS_2026_07_02.md"
    )
    a1_momentum_feature_loss_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_LOSS_CLUSTERS_2026_07_02.json"
    )
    a1_momentum_feature_loss_filter_csv = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_LOSS_FILTERS_2026_07_02.csv"
    )
    a1_momentum_feature_loss_bin_csv = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_LOSS_BINS_2026_07_02.csv"
    )
    a1_momentum_feature_loss_portfolio_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_LOSS_PORTFOLIO_VERDICT_2026_07_02.md"
    )
    a1_momentum_feature_loss_portfolio_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_LOSS_PORTFOLIO_VERDICT_2026_07_02.json"
    )
    a1_momentum_feature_loss_guard_optimizer_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_LOSS_DAILY_GUARD_OPTIMIZER_2026_07_02.md"
    )
    a1_momentum_feature_loss_guard_optimizer_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_LOSS_DAILY_GUARD_OPTIMIZER_2026_07_02.json"
    )
    a1_momentum_feature_loss_guard_optimizer_csv = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_LOSS_DAILY_GUARD_OPTIMIZER_2026_07_02.csv"
    )
    a1_momentum_feature_pair_filter_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_PAIR_FILTER_SEARCH_2026_07_02.md"
    )
    a1_momentum_feature_pair_filter_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_PAIR_FILTER_SEARCH_2026_07_02.json"
    )
    a1_momentum_feature_pair_filter_csv = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_PAIR_FILTER_SEARCH_2026_07_02.csv"
    )
    a1_momentum_feature_band_forward_draft = (
        phase1_root / "docs" / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_FORWARD_DRAFT_2026_07_02.md"
    )
    a1_momentum_feature_band_daily_income_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_TRADEOFF_2026_07_02.md"
    )
    a1_momentum_feature_band_daily_income_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_TRADEOFF_2026_07_02.json"
    )
    a1_momentum_feature_band_daily_income_csv = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_TRADEOFF_2026_07_02.csv"
    )
    a1_momentum_feature_band_daily_income_forward_draft = (
        phase1_root
        / "docs"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_FORWARD_DRAFT_2026_07_02.md"
    )
    a1_momentum_feature_band_daily_income_readiness_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_READINESS_2026_07_02.md"
    )
    a1_momentum_feature_band_daily_income_readiness_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_READINESS_2026_07_02.json"
    )
    a1_momentum_feature_band_day_state_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAY_STATE_SEARCH_2026_07_02.md"
    )
    a1_momentum_feature_band_day_state_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAY_STATE_SEARCH_2026_07_02.json"
    )
    a1_momentum_feature_band_day_state_csv = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAY_STATE_SEARCH_2026_07_02.csv"
    )
    a1_momentum_feature_band_daily_reliability_forward_draft = (
        phase1_root
        / "docs"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_RELIABILITY_FORWARD_DRAFT_2026_07_02.md"
    )
    a1_momentum_feature_band_daily_reliability_readiness_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_RELIABILITY_READINESS_2026_07_02.md"
    )
    a1_momentum_feature_band_daily_reliability_readiness_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_RELIABILITY_READINESS_2026_07_02.json"
    )
    a1_momentum_feature_band_residual_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RELIABILITY_RESIDUAL_SEARCH_2026_07_02.md"
    )
    a1_momentum_feature_band_residual_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RELIABILITY_RESIDUAL_SEARCH_2026_07_02.json"
    )
    a1_momentum_feature_band_residual_csv = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RELIABILITY_RESIDUAL_SEARCH_2026_07_02.csv"
    )
    a1_momentum_feature_band_residual_stress_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_STRESS_2026_07_02.md"
    )
    a1_momentum_feature_band_residual_stress_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_STRESS_2026_07_02.json"
    )
    a1_momentum_feature_band_residual_stress_csv = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_STRESS_2026_07_02.csv"
    )
    a1_momentum_feature_band_residual_package_optimizer_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PACKAGE_OPTIMIZER_2026_07_02.md"
    )
    a1_momentum_feature_band_residual_package_optimizer_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PACKAGE_OPTIMIZER_2026_07_02.json"
    )
    a1_momentum_feature_band_residual_package_optimizer_csv = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PACKAGE_OPTIMIZER_2026_07_02.csv"
    )
    a1_momentum_feature_band_residual_plus50_cooldown10_forward_draft = (
        phase1_root
        / "docs"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_FORWARD_DRAFT_2026_07_02.md"
    )
    a1_momentum_feature_band_residual_plus50_cooldown10_readiness_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_READINESS_2026_07_02.md"
    )
    a1_momentum_feature_band_residual_plus50_cooldown10_readiness_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_READINESS_2026_07_02.json"
    )
    a1_momentum_feature_band_residual_plus75_high_net_forward_draft = (
        phase1_root
        / "docs"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_FORWARD_DRAFT_2026_07_02.md"
    )
    a1_momentum_feature_band_residual_plus75_high_net_readiness_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_READINESS_2026_07_02.md"
    )
    a1_momentum_feature_band_residual_plus75_high_net_readiness_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_READINESS_2026_07_02.json"
    )
    a1_momentum_business_goal_scoreboard_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_SCOREBOARD_2026_07_02.md"
    )
    a1_momentum_business_goal_scoreboard_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_SCOREBOARD_2026_07_02.json"
    )
    a1_momentum_business_goal_scoreboard_csv = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_SCOREBOARD_2026_07_02.csv"
    )
    a1_momentum_business_goal_promotion_packet_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_PROMOTION_PACKET_2026_07_02.md"
    )
    a1_momentum_business_goal_promotion_packet_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_PROMOTION_PACKET_2026_07_02.json"
    )
    a1_momentum_business_goal_calendar_cadence_audit_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_CALENDAR_CADENCE_AUDIT_2026_07_02.md"
    )
    a1_momentum_business_goal_calendar_cadence_audit_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_BUSINESS_GOAL_CALENDAR_CADENCE_AUDIT_2026_07_02.json"
    )
    a1_momentum_market_day_coverage_search_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_MARKET_DAY_COVERAGE_SEARCH_CAUSAL_2026_07_03.md"
    )
    a1_momentum_market_day_coverage_search_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_MARKET_DAY_COVERAGE_SEARCH_CAUSAL_2026_07_03.json"
    )
    a1_momentum_market_day_coverage_search_csv = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_MARKET_DAY_COVERAGE_SEARCH_CAUSAL_2026_07_03.csv"
    )
    a1_momentum_market_day_coverage_stress_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_MARKET_DAY_COVERAGE_STRESS_CAUSAL_2026_07_03.md"
    )
    a1_momentum_market_day_coverage_stress_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_MARKET_DAY_COVERAGE_STRESS_CAUSAL_2026_07_03.json"
    )
    a1_momentum_market_day_coverage_stress_csv = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_MARKET_DAY_COVERAGE_STRESS_CAUSAL_2026_07_03_TRADES.csv"
    )
    a1_momentum_business_goal_owner_authorization = (
        phase1_root / "docs" / "A1_MOMENTUM_BUSINESS_GOAL_OWNER_AUTHORIZATION_2026_07_02.md"
    )
    a1_momentum_business_goal_claude_prompt = (
        repo_root / "CLAUDE_REVIEW_PROMPT_A1_MOMENTUM_BUSINESS_GOAL_PROMOTION_2026_07_02.md"
    )
    a1_momentum_feature_band_residual_reliability_forward_draft = (
        phase1_root
        / "docs"
        / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_FORWARD_DRAFT_2026_07_02.md"
    )
    a1_momentum_feature_band_residual_reliability_readiness_md = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_READINESS_2026_07_02.md"
    )
    a1_momentum_feature_band_residual_reliability_readiness_json = (
        phase1_reports / "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_READINESS_2026_07_02.json"
    )
    xau_920101_failure_forensic_md = phase1_reports / "XAU_920101_BREAKOUT_RETEST_FAILURE_FORENSIC_2026_07_01.md"
    xau_920101_failure_forensic_json = phase1_reports / "XAU_920101_BREAKOUT_RETEST_FAILURE_FORENSIC_2026_07_01.json"
    xau_920101_faststop_forensic_md = (
        phase1_reports / "XAU_920101_BREAKOUT_RETEST_FASTSTOP_REPAIR_FORENSIC_2026_07_01.md"
    )
    xau_920101_faststop_forensic_json = (
        phase1_reports / "XAU_920101_BREAKOUT_RETEST_FASTSTOP_REPAIR_FORENSIC_2026_07_01.json"
    )
    xau_920101_profit_protection_forensic_md = (
        phase1_reports / "XAU_920101_BREAKOUT_RETEST_PROFIT_PROTECTION_FORENSIC_2026_07_01.md"
    )
    xau_920101_profit_protection_forensic_json = (
        phase1_reports / "XAU_920101_BREAKOUT_RETEST_PROFIT_PROTECTION_FORENSIC_2026_07_01.json"
    )
    xau_920101_active_forensic_md = (
        xau_920101_profit_protection_forensic_md
        if xau_920101_profit_protection_forensic_json.exists()
        else xau_920101_faststop_forensic_md
        if xau_920101_faststop_forensic_json.exists()
        else xau_920101_failure_forensic_md
    )
    xau_920101_active_forensic_json = (
        xau_920101_profit_protection_forensic_json
        if xau_920101_profit_protection_forensic_json.exists()
        else xau_920101_faststop_forensic_json
        if xau_920101_faststop_forensic_json.exists()
        else xau_920101_failure_forensic_json
    )

    quarantine = _read_json(quarantine_report)
    a3_attachment = _read_json(a3_attachment_report)
    a3_review_followup = _read_json(a3_review_followup_report)
    a3_pause = _read_json(a3_pause_report)
    a1_momentum_attachment = _read_json(a1_momentum_attachment_report)
    a1_momentum_backtest = _read_json(a1_momentum_backtest_json)
    a1_momentum_variant_backtest = _read_json(a1_momentum_variant_backtest_json)
    a1_momentum_frequency_repair = _read_json(a1_momentum_frequency_repair_json)
    a1_momentum_portfolio_diagnostic = _read_json(a1_momentum_portfolio_diagnostic_json)
    a1_momentum_broad_portfolio = _read_json(a1_momentum_broad_portfolio_json)
    a1_momentum_deep_portfolio = _read_json(a1_momentum_deep_portfolio_json)
    a1_momentum_deep_portfolio_stress = _read_json(a1_momentum_deep_portfolio_stress_json)
    a1_momentum_robust_portfolio = _read_json(a1_momentum_robust_portfolio_json)
    a1_momentum_robust_portfolio_stress = _read_json(a1_momentum_robust_portfolio_stress_json)
    a1_momentum_robust_portfolio_walkforward = _read_json(a1_momentum_robust_portfolio_walkforward_json)
    a1_momentum_robust_portfolio_repair = _read_json(a1_momentum_robust_portfolio_repair_json)
    a1_momentum_robust_repair_walkforward = _read_json(a1_momentum_robust_repair_walkforward_json)
    a1_momentum_daily_fit = _read_json(a1_momentum_daily_fit_json)
    a1_momentum_daily_fit_stress = _read_json(a1_momentum_daily_fit_stress_json)
    a1_momentum_daily_fit_repair = _read_json(a1_momentum_daily_fit_repair_json)
    a1_momentum_daily_guard = _read_json(a1_momentum_daily_guard_json)
    a1_momentum_pocket_portfolio = _read_json(a1_momentum_pocket_portfolio_json)
    a1_momentum_daily_state_guard = _read_json(a1_momentum_daily_state_guard_json)
    a1_momentum_feature_loss = _read_json(a1_momentum_feature_loss_json)
    a1_momentum_feature_loss_portfolio = _read_json(a1_momentum_feature_loss_portfolio_json)
    a1_momentum_feature_loss_guard_optimizer = _read_json(a1_momentum_feature_loss_guard_optimizer_json)
    a1_momentum_feature_pair_filter = _read_json(a1_momentum_feature_pair_filter_json)
    a1_momentum_feature_band_daily_income = _read_json(a1_momentum_feature_band_daily_income_json)
    a1_momentum_feature_band_daily_income_readiness = _read_json(
        a1_momentum_feature_band_daily_income_readiness_json
    )
    a1_momentum_feature_band_day_state = _read_json(a1_momentum_feature_band_day_state_json)
    a1_momentum_feature_band_daily_reliability_readiness = _read_json(
        a1_momentum_feature_band_daily_reliability_readiness_json
    )
    a1_momentum_feature_band_residual = _read_json(a1_momentum_feature_band_residual_json)
    a1_momentum_feature_band_residual_stress = _read_json(a1_momentum_feature_band_residual_stress_json)
    a1_momentum_feature_band_residual_package_optimizer = _read_json(
        a1_momentum_feature_band_residual_package_optimizer_json
    )
    a1_momentum_feature_band_residual_plus50_cooldown10_readiness = _read_json(
        a1_momentum_feature_band_residual_plus50_cooldown10_readiness_json
    )
    a1_momentum_feature_band_residual_plus75_high_net_readiness = _read_json(
        a1_momentum_feature_band_residual_plus75_high_net_readiness_json
    )
    a1_momentum_business_goal_scoreboard = _read_json(a1_momentum_business_goal_scoreboard_json)
    a1_momentum_business_goal_promotion_packet = _read_json(a1_momentum_business_goal_promotion_packet_json)
    a1_momentum_business_goal_calendar_cadence_audit = _read_json(
        a1_momentum_business_goal_calendar_cadence_audit_json
    )
    a1_momentum_market_day_coverage_search = _read_json(a1_momentum_market_day_coverage_search_json)
    a1_momentum_market_day_coverage_stress = _read_json(a1_momentum_market_day_coverage_stress_json)
    a1_momentum_feature_band_residual_reliability_readiness = _read_json(
        a1_momentum_feature_band_residual_reliability_readiness_json
    )
    xau_920101_failure_forensic = _read_json(xau_920101_active_forensic_json)
    repo = _repo_state(repo_root)
    profile_backup = quarantine.get("terminal", {}).get("profile_backup_dir", "")
    historical_a3_authorization = _a3_historical_owner_authorization(a3_attachment)
    current_a3_runtime = _a3_current_runtime_state(a3_review_followup, a3_pause)
    effective_a3_authorization = current_a3_runtime.get("effective_runtime_authorization", "MISSING")
    a3_artifact_integrity = a3_review_followup.get("artifact_integrity_status", a3_pause.get("artifact_integrity_status", "MISSING"))
    a3_runtime_performance = a3_review_followup.get("runtime_performance_status", a3_pause.get("runtime_performance_status", "MISSING"))
    test_suite_status = _test_suite_status(phase1_reports)
    shadow_hypothesis = _shadow_hypothesis_status(phase1_root)
    shadow_hypothesis_status = shadow_hypothesis["status"]

    target_charts = _chart_summary(quarantine.get("after_target_charts", quarantine.get("target_charts", [])))
    historical_protected_charts = _chart_summary(quarantine.get("after_protected_charts", quarantine.get("protected_charts", [])))
    runtime_inventory = _read_runtime_inventory(runtime_inventory_csv)
    protected_charts = _protected_breakout_runtime_charts(runtime_inventory) or historical_protected_charts
    target_candidates = sorted(
        {
            str(item.get("candidate", ""))
            for item in quarantine.get("after_target_charts", quarantine.get("target_charts", []))
            if item.get("candidate")
        }
    ) or quarantine.get("scope", {}).get("target_candidates", [])
    protected_candidates = sorted({item["candidate"] for item in protected_charts if item.get("candidate")}) or [
        "breakout_retest"
    ]

    summary: dict[str, Any] = {
        "schema_version": "project_status_summary_v2",
        "generated_at_utc": now.isoformat().replace("+00:00", "Z"),
        "repo": repo,
        "source_artifacts": {
            "status_html": "status.html",
            "status_summary_json": "status_summary.json",
            "status_summary_md": "status_summary.md",
            "round_quarantine_applied": _rel(repo_root, quarantine_report),
            "a3_tier1_attachment": _rel(repo_root, a3_attachment_report),
            "a3_governance_override": "xau-usd/xauusd-phase1/docs/A3_TIER1_COMPAT_GOVERNANCE_OVERRIDE_2026_06_17.md",
            "a3_review_followup": _rel(repo_root, a3_review_followup_report),
            "a3_emergency_pause": _rel(repo_root, a3_pause_report),
            "a3_emergency_pause_verify_only": _rel(repo_root, a3_pause_verify_report),
            "a3_repair_p1_p2_implementation": _rel(repo_root, a3_p1_p2_report),
            "runtime_chart_inventory": _rel(repo_root, runtime_inventory_csv),
            "a1_xau_m5_momentum_attachment": _rel(repo_root, a1_momentum_attachment_md),
            "a1_xau_m5_momentum_forward_spec": _rel(repo_root, a1_momentum_forward_spec),
            "a1_xau_m5_momentum_forward_spec_manifest": _rel(repo_root, a1_momentum_forward_spec_manifest),
            "a1_xau_m5_momentum_frequency_first_replacement_readiness": _rel(
                repo_root, a1_momentum_frequency_replacement_readiness
            ),
            "a1_xau_m5_momentum_frequency_first_v6_diagnostic": _rel(
                repo_root, a1_momentum_frequency_v6_diagnostic
            ),
            "a1_xau_m5_momentum_frequency_first_v7_pullback": _rel(
                repo_root, a1_momentum_frequency_v7_pullback
            ),
            "a1_xau_m5_momentum_frequency_first_v8_compression": _rel(
                repo_root, a1_momentum_frequency_v8_compression
            ),
            "a1_xau_m5_momentum_frequency_first_v9_sweep_reclaim": _rel(
                repo_root, a1_momentum_frequency_v9_sweep
            ),
            "a1_xau_m5_momentum_frequency_first_v10_opening_range": _rel(
                repo_root, a1_momentum_frequency_v10_opening_range
            ),
            "a1_xau_m5_momentum_frequency_first_v11_ema_trend": _rel(
                repo_root, a1_momentum_frequency_v11_ema_trend
            ),
            "a1_xau_m5_momentum_frequency_first_v12_ema_trend_mask": _rel(
                repo_root, a1_momentum_frequency_v12_ema_trend_mask
            ),
            "a1_xau_m5_momentum_frequency_first_v13_directional_mask": _rel(
                repo_root, a1_momentum_frequency_v13_directional_mask
            ),
            "a1_xau_m5_momentum_frequency_requirement_verdict": _rel(
                repo_root, a1_momentum_frequency_requirement_verdict
            ),
            "a1_xau_m5_momentum_portfolio_diagnostic": _rel(
                repo_root, a1_momentum_portfolio_diagnostic_md
            ),
            "a1_xau_m5_momentum_portfolio_forward_draft": _rel(
                repo_root, a1_momentum_portfolio_forward_draft
            ),
            "a1_xau_m5_momentum_broad_portfolio_search": _rel(
                repo_root, a1_momentum_broad_portfolio_md
            ),
            "a1_xau_m5_momentum_broad_portfolio_verdict": _rel(
                repo_root, a1_momentum_broad_portfolio_verdict
            ),
            "a1_xau_m5_momentum_clean_portfolio_forward_draft": _rel(
                repo_root, a1_momentum_clean_portfolio_forward_draft
            ),
            "a1_xau_m5_momentum_deep_portfolio_search": _rel(
                repo_root, a1_momentum_deep_portfolio_md
            ),
            "a1_xau_m5_momentum_deep_portfolio_stress": _rel(
                repo_root, a1_momentum_deep_portfolio_stress_md
            ),
            "a1_xau_m5_momentum_deep_portfolio_verdict": _rel(
                repo_root, a1_momentum_deep_portfolio_verdict
            ),
            "a1_xau_m5_momentum_deep_portfolio_forward_draft": _rel(
                repo_root, a1_momentum_deep_portfolio_forward_draft
            ),
            "a1_xau_m5_momentum_daily_fit_portfolio_search": _rel(
                repo_root, a1_momentum_daily_fit_md
            ),
            "a1_xau_m5_momentum_daily_fit_portfolio_stress": _rel(
                repo_root, a1_momentum_daily_fit_stress_md
            ),
            "a1_xau_m5_momentum_daily_fit_repair_diagnostic": _rel(
                repo_root, a1_momentum_daily_fit_repair_md
            ),
            "a1_xau_m5_momentum_daily_fit_portfolio_forward_draft": _rel(
                repo_root, a1_momentum_daily_fit_forward_draft
            ),
            "a1_xau_m5_momentum_daily_fit_repair_forward_draft": _rel(
                repo_root, a1_momentum_daily_fit_repair_forward_draft
            ),
            "a1_xau_m5_momentum_daily_guard_search": _rel(
                repo_root, a1_momentum_daily_guard_md
            ),
            "a1_xau_m5_momentum_daily_guard_forward_draft": _rel(
                repo_root, a1_momentum_daily_guard_forward_draft
            ),
            "a1_xau_m5_momentum_daily_shape_optimizer": _rel(
                repo_root, a1_momentum_daily_shape_optimizer_md
            ),
            "a1_xau_m5_momentum_pocket_portfolio_search": _rel(
                repo_root, a1_momentum_pocket_portfolio_md
            ),
            "a1_xau_m5_momentum_pocket_portfolio_csv": _rel(
                repo_root, a1_momentum_pocket_portfolio_csv
            ),
            "a1_xau_m5_momentum_daily_state_guard_search": _rel(
                repo_root, a1_momentum_daily_state_guard_md
            ),
            "a1_xau_m5_momentum_daily_state_guard_csv": _rel(
                repo_root, a1_momentum_daily_state_guard_csv
            ),
            "a1_xau_m5_momentum_feature_loss_clusters": _rel(
                repo_root, a1_momentum_feature_loss_md
            ),
            "a1_xau_m5_momentum_feature_loss_filters_csv": _rel(
                repo_root, a1_momentum_feature_loss_filter_csv
            ),
            "a1_xau_m5_momentum_feature_loss_bins_csv": _rel(
                repo_root, a1_momentum_feature_loss_bin_csv
            ),
            "a1_xau_m5_momentum_feature_loss_portfolio_verdict": _rel(
                repo_root, a1_momentum_feature_loss_portfolio_md
            ),
            "a1_xau_m5_momentum_feature_loss_daily_guard_optimizer": _rel(
                repo_root, a1_momentum_feature_loss_guard_optimizer_md
            ),
            "a1_xau_m5_momentum_feature_loss_daily_guard_optimizer_csv": _rel(
                repo_root, a1_momentum_feature_loss_guard_optimizer_csv
            ),
            "a1_xau_m5_momentum_feature_pair_filter_search": _rel(
                repo_root, a1_momentum_feature_pair_filter_md
            ),
            "a1_xau_m5_momentum_feature_pair_filter_csv": _rel(
                repo_root, a1_momentum_feature_pair_filter_csv
            ),
            "a1_xau_m5_momentum_feature_band_forward_draft": _rel(
                repo_root, a1_momentum_feature_band_forward_draft
            ),
            "a1_xau_m5_momentum_feature_band_daily_income_tradeoff": _rel(
                repo_root, a1_momentum_feature_band_daily_income_md
            ),
            "a1_xau_m5_momentum_feature_band_daily_income_csv": _rel(
                repo_root, a1_momentum_feature_band_daily_income_csv
            ),
            "a1_xau_m5_momentum_feature_band_daily_income_forward_draft": _rel(
                repo_root, a1_momentum_feature_band_daily_income_forward_draft
            ),
            "a1_xau_m5_momentum_feature_band_daily_income_readiness": _rel(
                repo_root, a1_momentum_feature_band_daily_income_readiness_md
            ),
            "a1_xau_m5_momentum_feature_band_day_state_search": _rel(
                repo_root, a1_momentum_feature_band_day_state_md
            ),
            "a1_xau_m5_momentum_feature_band_day_state_csv": _rel(
                repo_root, a1_momentum_feature_band_day_state_csv
            ),
            "a1_xau_m5_momentum_feature_band_daily_reliability_forward_draft": _rel(
                repo_root, a1_momentum_feature_band_daily_reliability_forward_draft
            ),
            "a1_xau_m5_momentum_feature_band_daily_reliability_readiness": _rel(
                repo_root, a1_momentum_feature_band_daily_reliability_readiness_md
            ),
            "a1_xau_m5_momentum_feature_band_residual_search": _rel(
                repo_root, a1_momentum_feature_band_residual_md
            ),
            "a1_xau_m5_momentum_feature_band_residual_csv": _rel(
                repo_root, a1_momentum_feature_band_residual_csv
            ),
            "a1_xau_m5_momentum_feature_band_residual_reliability_forward_draft": _rel(
                repo_root, a1_momentum_feature_band_residual_reliability_forward_draft
            ),
            "a1_xau_m5_momentum_feature_band_residual_reliability_readiness": _rel(
                repo_root, a1_momentum_feature_band_residual_reliability_readiness_md
            ),
            "a1_xau_m5_momentum_feature_band_residual_plus50_cooldown10_forward_draft": _rel(
                repo_root, a1_momentum_feature_band_residual_plus50_cooldown10_forward_draft
            ),
            "a1_xau_m5_momentum_feature_band_residual_plus50_cooldown10_readiness": _rel(
                repo_root, a1_momentum_feature_band_residual_plus50_cooldown10_readiness_md
            ),
            "a1_xau_m5_momentum_feature_band_residual_plus75_high_net_forward_draft": _rel(
                repo_root, a1_momentum_feature_band_residual_plus75_high_net_forward_draft
            ),
            "a1_xau_m5_momentum_feature_band_residual_plus75_high_net_readiness": _rel(
                repo_root, a1_momentum_feature_band_residual_plus75_high_net_readiness_md
            ),
            "a1_xau_m5_momentum_business_goal_scoreboard": _rel(
                repo_root, a1_momentum_business_goal_scoreboard_md
            ),
            "a1_xau_m5_momentum_business_goal_scoreboard_csv": _rel(
                repo_root, a1_momentum_business_goal_scoreboard_csv
            ),
            "a1_xau_m5_momentum_business_goal_promotion_packet": _rel(
                repo_root, a1_momentum_business_goal_promotion_packet_md
            ),
            "a1_xau_m5_momentum_business_goal_calendar_cadence_audit": _rel(
                repo_root, a1_momentum_business_goal_calendar_cadence_audit_md
            ),
            "a1_xau_m5_momentum_market_day_coverage_search": _rel(
                repo_root, a1_momentum_market_day_coverage_search_md
            ),
            "a1_xau_m5_momentum_market_day_coverage_stress": _rel(
                repo_root, a1_momentum_market_day_coverage_stress_md
            ),
            "a1_xau_m5_momentum_business_goal_owner_authorization": _rel(
                repo_root, a1_momentum_business_goal_owner_authorization
            ),
            "a1_xau_m5_momentum_business_goal_claude_prompt": _rel(
                repo_root, a1_momentum_business_goal_claude_prompt
            ),
            "xau_920101_breakout_retest_failure_forensic": _rel(repo_root, xau_920101_failure_forensic_md),
            "xau_920101_breakout_retest_faststop_repair_forensic": _rel(repo_root, xau_920101_faststop_forensic_md),
            "xau_920101_breakout_retest_profit_protection_forensic": _rel(repo_root, xau_920101_profit_protection_forensic_md),
            "final_review_c9889cb": "FINAL_REVIEW_C9889CB_A3_FOLLOWUP_2026_06_18.md",
            "final_review_b7ea982": "FINAL_REVIEW_B7EA982_A3_REPAIR_IMPLEMENTATION_PLAN_2026_06_18.md",
            "final_review_response": "xau-usd/xauusd-phase1/outputs/reports/FINAL_REVIEW_D5DD2DE_RESPONSE_2026_06_18.md",
            "phase1_test_failure_triage": "xau-usd/xauusd-phase1/outputs/reports/PHASE1_TEST_FAILURE_TRIAGE_2026_06_18.md",
            "phase1_test_failure_closure": "xau-usd/xauusd-phase1/outputs/reports/PHASE1_TEST_FAILURE_CLOSURE_2026_06_18.md",
        },
        "accounts": {
            "A1": {
                "login": "1025742",
                "server": "Capital.ComMena-Demo",
                "role": "standard/noisy demo account",
                "round_quarantine_active": _is_quarantine_active(target_charts),
                "touched_by_round_quarantine": True,
                "target_charts": target_charts,
                "protected_charts": protected_charts,
                "protected_charts_source": "runtime_inventory" if runtime_inventory else "historical_quarantine_report",
                "historical_protected_charts": historical_protected_charts,
                "experimental_momentum_lane": _a1_momentum_lane(
                    repo_root,
                    a1_momentum_attachment_report,
                    a1_momentum_attachment_md,
                    a1_momentum_attachment,
                    a1_momentum_backtest_md,
                    a1_momentum_backtest_json,
                    a1_momentum_backtest,
                    a1_momentum_variant_backtest_md,
                    a1_momentum_variant_backtest_json,
                    a1_momentum_variant_backtest,
                    a1_momentum_long_diagnosis_md,
                    a1_momentum_frequency_repair_md,
                    a1_momentum_frequency_repair_json,
                    a1_momentum_frequency_repair,
                    a1_momentum_frequency_replacement_readiness,
                    a1_momentum_frequency_v6_diagnostic,
                    a1_momentum_frequency_requirement_verdict,
                    a1_momentum_portfolio_diagnostic_md,
                    a1_momentum_portfolio_diagnostic_json,
                    a1_momentum_portfolio_diagnostic,
                    a1_momentum_portfolio_forward_draft,
                    a1_momentum_broad_portfolio_md,
                    a1_momentum_broad_portfolio_json,
                    a1_momentum_broad_portfolio,
                    a1_momentum_broad_portfolio_verdict,
                    a1_momentum_clean_portfolio_forward_draft,
                    a1_momentum_deep_portfolio_md,
                    a1_momentum_deep_portfolio_json,
                    a1_momentum_deep_portfolio,
                    a1_momentum_deep_portfolio_stress_md,
                    a1_momentum_deep_portfolio_stress_json,
                    a1_momentum_deep_portfolio_stress,
                    a1_momentum_deep_portfolio_verdict,
                    a1_momentum_deep_portfolio_forward_draft,
                    a1_momentum_robust_portfolio_md,
                    a1_momentum_robust_portfolio_json,
                    a1_momentum_robust_portfolio,
                    a1_momentum_robust_portfolio_stress_md,
                    a1_momentum_robust_portfolio_stress_json,
                    a1_momentum_robust_portfolio_stress,
                    a1_momentum_robust_portfolio_forward_draft,
                    a1_momentum_robust_portfolio_walkforward_md,
                    a1_momentum_robust_portfolio_walkforward_json,
                    a1_momentum_robust_portfolio_walkforward,
                    a1_momentum_robust_portfolio_repair_md,
                    a1_momentum_robust_portfolio_repair_json,
                    a1_momentum_robust_portfolio_repair,
                    a1_momentum_robust_repair_walkforward_md,
                    a1_momentum_robust_repair_walkforward_json,
                    a1_momentum_robust_repair_walkforward,
                    a1_momentum_robust_repair_forward_draft,
                    a1_momentum_daily_fit_md,
                    a1_momentum_daily_fit_json,
                    a1_momentum_daily_fit,
                    a1_momentum_daily_fit_forward_draft,
                    a1_momentum_daily_fit_stress_md,
                    a1_momentum_daily_fit_stress_json,
                    a1_momentum_daily_fit_stress,
                    a1_momentum_daily_fit_repair_md,
                    a1_momentum_daily_fit_repair_json,
                    a1_momentum_daily_fit_repair,
                    a1_momentum_daily_fit_repair_forward_draft,
                    a1_momentum_daily_guard_md,
                    a1_momentum_daily_guard_json,
                    a1_momentum_daily_guard,
                    a1_momentum_daily_guard_forward_draft,
                    a1_momentum_pocket_portfolio_md,
                    a1_momentum_pocket_portfolio_json,
                    a1_momentum_pocket_portfolio,
                    a1_momentum_pocket_portfolio_csv,
                    a1_momentum_daily_state_guard_md,
                    a1_momentum_daily_state_guard_json,
                    a1_momentum_daily_state_guard,
                    a1_momentum_daily_state_guard_csv,
                    a1_momentum_feature_loss_md,
                    a1_momentum_feature_loss_json,
                    a1_momentum_feature_loss,
                    a1_momentum_feature_loss_filter_csv,
                    a1_momentum_feature_loss_bin_csv,
                    a1_momentum_feature_loss_portfolio_md,
                    a1_momentum_feature_loss_portfolio_json,
                    a1_momentum_feature_loss_portfolio,
                    a1_momentum_feature_loss_guard_optimizer_md,
                    a1_momentum_feature_loss_guard_optimizer_json,
                    a1_momentum_feature_loss_guard_optimizer_csv,
                    a1_momentum_feature_loss_guard_optimizer,
                    a1_momentum_feature_pair_filter_md,
                    a1_momentum_feature_pair_filter_json,
                    a1_momentum_feature_pair_filter_csv,
                    a1_momentum_feature_pair_filter,
                    a1_momentum_feature_band_daily_income_md,
                    a1_momentum_feature_band_daily_income_json,
                    a1_momentum_feature_band_daily_income_csv,
                    a1_momentum_feature_band_daily_income,
                    a1_momentum_feature_band_daily_income_forward_draft,
                    a1_momentum_feature_band_daily_income_readiness_md,
                    a1_momentum_feature_band_daily_income_readiness_json,
                    a1_momentum_feature_band_daily_income_readiness,
                    a1_momentum_feature_band_day_state_md,
                    a1_momentum_feature_band_day_state_json,
                    a1_momentum_feature_band_day_state_csv,
                    a1_momentum_feature_band_day_state,
                    a1_momentum_feature_band_daily_reliability_forward_draft,
                    a1_momentum_feature_band_daily_reliability_readiness_md,
                    a1_momentum_feature_band_daily_reliability_readiness_json,
                    a1_momentum_feature_band_daily_reliability_readiness,
                    a1_momentum_feature_band_residual_md,
                    a1_momentum_feature_band_residual_json,
                    a1_momentum_feature_band_residual_csv,
                    a1_momentum_feature_band_residual,
                    a1_momentum_feature_band_residual_stress_md,
                    a1_momentum_feature_band_residual_stress_json,
                    a1_momentum_feature_band_residual_stress_csv,
                    a1_momentum_feature_band_residual_stress,
                    a1_momentum_feature_band_residual_package_optimizer_md,
                    a1_momentum_feature_band_residual_package_optimizer_json,
                    a1_momentum_feature_band_residual_package_optimizer_csv,
                    a1_momentum_feature_band_residual_package_optimizer,
                    a1_momentum_feature_band_residual_plus50_cooldown10_forward_draft,
                    a1_momentum_feature_band_residual_plus50_cooldown10_readiness_md,
                    a1_momentum_feature_band_residual_plus50_cooldown10_readiness_json,
                    a1_momentum_feature_band_residual_plus50_cooldown10_readiness,
                    a1_momentum_feature_band_residual_plus75_high_net_forward_draft,
                    a1_momentum_feature_band_residual_plus75_high_net_readiness_md,
                    a1_momentum_feature_band_residual_plus75_high_net_readiness_json,
                    a1_momentum_feature_band_residual_plus75_high_net_readiness,
                    a1_momentum_business_goal_scoreboard_md,
                    a1_momentum_business_goal_scoreboard_json,
                    a1_momentum_business_goal_scoreboard_csv,
                    a1_momentum_business_goal_scoreboard,
                    a1_momentum_business_goal_promotion_packet_md,
                    a1_momentum_business_goal_promotion_packet_json,
                    a1_momentum_business_goal_promotion_packet,
                    a1_momentum_business_goal_calendar_cadence_audit_md,
                    a1_momentum_business_goal_calendar_cadence_audit_json,
                    a1_momentum_business_goal_calendar_cadence_audit,
                    a1_momentum_market_day_coverage_search_md,
                    a1_momentum_market_day_coverage_search_json,
                    a1_momentum_market_day_coverage_search_csv,
                    a1_momentum_market_day_coverage_search,
                    a1_momentum_market_day_coverage_stress_md,
                    a1_momentum_market_day_coverage_stress_json,
                    a1_momentum_market_day_coverage_stress_csv,
                    a1_momentum_market_day_coverage_stress,
                    a1_momentum_feature_band_residual_reliability_forward_draft,
                    a1_momentum_feature_band_residual_reliability_readiness_md,
                    a1_momentum_feature_band_residual_reliability_readiness_json,
                    a1_momentum_feature_band_residual_reliability_readiness,
                ),
            },
            "A2": {
                "login": "1033030",
                "server": "Capital.ComMena-Demo",
                "role": "Tier-1 clean breakout account",
                "round_quarantine_active": False,
                "touched_by_round_quarantine": False,
            },
            "A3": {
                "login": "1033669",
                "server": "Capital.ComMena-Demo",
                "role": "repair / Tier-1 compatibility demo account",
                "round_quarantine_active": False,
                "touched_by_round_quarantine": False,
                "historical_owner_authorization": historical_a3_authorization,
                "current_runtime_state": current_a3_runtime,
                "effective_runtime_authorization": effective_a3_authorization,
                "tier1_compat_demo_broker_action": historical_a3_authorization["933400_demo_broker_action"],
                "tier1_compat_attachment_status": a3_attachment.get("status", "MISSING"),
                "historical_attach_status": a3_attachment.get("status", "MISSING"),
                "review_followup_status": a3_review_followup.get("status", "MISSING"),
                "artifact_integrity_status": a3_artifact_integrity,
                "runtime_performance_status": a3_runtime_performance,
                "authorization_status": effective_a3_authorization,
                "runtime_authorization_status": effective_a3_authorization,
                "shadow_candidate_performance_status": "NOT_EVALUATED",
                "review_followup_summary": a3_review_followup.get("summary", {}),
                "plain_933200_stopped": _a3_lane_paused(a3_review_followup, "933200"),
                "improved_933300_paused": _a3_lane_paused(a3_review_followup, "933300"),
                "tier1_933400_paused": _a3_lane_paused(a3_review_followup, "933400"),
                "profit_lock_dryrun_disarmed": _profit_lock_disarmed(a3_review_followup),
                "emergency_pause_status": a3_pause.get("status", "MISSING"),
                "emergency_pause_report": _rel(repo_root, a3_pause_report),
                "emergency_pause_verify_only_report": _rel(repo_root, a3_pause_verify_report),
                "evidence_window_start_utc": a3_review_followup.get("window_start_utc", ""),
                "evidence_window_end_utc": a3_review_followup.get("window_end_utc", ""),
                "runtime_snapshot_at_utc": current_a3_runtime.get("verified_at_utc", ""),
                "artifact_generation_base_commit": repo.get("commit", ""),
                "artifact_commit_or_release_id": repo.get("commit", ""),
                "pause_artifact_runtime_consistency_status": _pause_artifact_runtime_consistency_status(a3_review_followup, a3_pause),
                "test_suite_status": test_suite_status,
                "family_mutex_status": "NOT_IMPLEMENTED",
                "containment_status": "NOT_IMPLEMENTED",
                "shadow_hypothesis_status": shadow_hypothesis_status,
                "shadow_hypothesis_manifest": shadow_hypothesis,
                "reactivation_gate_status": "BLOCKED",
                "next_allowed_transition": "P3 offline A3 signal-quality discovery screen; repo-only and no broker action.",
            },
        },
        "quarantine": {
            "status": quarantine.get("status", "MISSING"),
            "scope": "A1 XAUUSD round-family only",
            "target_candidates": target_candidates,
            "target_charts": target_charts,
            "protected_candidates": protected_candidates,
            "protected_charts": protected_charts,
            "protected_charts_source": "runtime_inventory" if runtime_inventory else "historical_quarantine_report",
            "historical_protected_charts": historical_protected_charts,
            "profile_backup_path": profile_backup,
            "rollback_backup_exists": bool(profile_backup),
            "keep_active_through_forward_week": True,
            "rollback_required_now": False,
        },
        "a3_tier1": {
            "historical_attach_status": a3_attachment.get("status", "MISSING"),
            "runtime_performance_status": a3_runtime_performance,
            "authorization_status": effective_a3_authorization,
            "shadow_candidate_performance_status": "NOT_EVALUATED",
            "historical_owner_authorization": historical_a3_authorization,
            "owner_authorized_demo_broker_action": (
                historical_a3_authorization["933400_demo_broker_action"] == "OWNER_AUTHORIZED_DEMO_BROKER_ACTION"
            ),
            "governance_note": "Historical owner override is preserved as audit evidence only; current runtime authorization is paused.",
            "current_runtime_state": current_a3_runtime,
            "effective_runtime_authorization": effective_a3_authorization,
            "review_followup_summary": a3_review_followup.get("summary", {}),
            "runtime_authorization_status": effective_a3_authorization,
            "emergency_pause_status": a3_pause.get("status", "MISSING"),
            "family_mutex_status": "NOT_IMPLEMENTED",
            "containment_status": "NOT_IMPLEMENTED",
            "shadow_hypothesis_status": shadow_hypothesis_status,
            "shadow_hypothesis_manifest": shadow_hypothesis,
            "reactivation_gate_status": "BLOCKED",
        },
        "experimental_lanes": {
            "a1_xau_m5_momentum_continuation": _a1_momentum_lane(
                repo_root,
                a1_momentum_attachment_report,
                a1_momentum_attachment_md,
                a1_momentum_attachment,
                a1_momentum_backtest_md,
                a1_momentum_backtest_json,
                a1_momentum_backtest,
                a1_momentum_variant_backtest_md,
                a1_momentum_variant_backtest_json,
                a1_momentum_variant_backtest,
                a1_momentum_long_diagnosis_md,
                a1_momentum_frequency_repair_md,
                a1_momentum_frequency_repair_json,
                a1_momentum_frequency_repair,
                a1_momentum_frequency_replacement_readiness,
                a1_momentum_frequency_v6_diagnostic,
                a1_momentum_frequency_requirement_verdict,
                a1_momentum_portfolio_diagnostic_md,
                a1_momentum_portfolio_diagnostic_json,
                a1_momentum_portfolio_diagnostic,
                a1_momentum_portfolio_forward_draft,
                a1_momentum_broad_portfolio_md,
                a1_momentum_broad_portfolio_json,
                a1_momentum_broad_portfolio,
                a1_momentum_broad_portfolio_verdict,
                a1_momentum_clean_portfolio_forward_draft,
                a1_momentum_deep_portfolio_md,
                a1_momentum_deep_portfolio_json,
                a1_momentum_deep_portfolio,
                a1_momentum_deep_portfolio_stress_md,
                a1_momentum_deep_portfolio_stress_json,
                a1_momentum_deep_portfolio_stress,
                a1_momentum_deep_portfolio_verdict,
                a1_momentum_deep_portfolio_forward_draft,
                a1_momentum_robust_portfolio_md,
                a1_momentum_robust_portfolio_json,
                a1_momentum_robust_portfolio,
                a1_momentum_robust_portfolio_stress_md,
                a1_momentum_robust_portfolio_stress_json,
                a1_momentum_robust_portfolio_stress,
                a1_momentum_robust_portfolio_forward_draft,
                a1_momentum_robust_portfolio_walkforward_md,
                a1_momentum_robust_portfolio_walkforward_json,
                a1_momentum_robust_portfolio_walkforward,
                a1_momentum_robust_portfolio_repair_md,
                a1_momentum_robust_portfolio_repair_json,
                a1_momentum_robust_portfolio_repair,
                a1_momentum_robust_repair_walkforward_md,
                a1_momentum_robust_repair_walkforward_json,
                a1_momentum_robust_repair_walkforward,
                a1_momentum_robust_repair_forward_draft,
                a1_momentum_daily_fit_md,
                a1_momentum_daily_fit_json,
                a1_momentum_daily_fit,
                a1_momentum_daily_fit_forward_draft,
                a1_momentum_daily_fit_stress_md,
                a1_momentum_daily_fit_stress_json,
                a1_momentum_daily_fit_stress,
                a1_momentum_daily_fit_repair_md,
                a1_momentum_daily_fit_repair_json,
                a1_momentum_daily_fit_repair,
                a1_momentum_daily_fit_repair_forward_draft,
                a1_momentum_daily_guard_md,
                a1_momentum_daily_guard_json,
                a1_momentum_daily_guard,
                a1_momentum_daily_guard_forward_draft,
                a1_momentum_pocket_portfolio_md,
                a1_momentum_pocket_portfolio_json,
                a1_momentum_pocket_portfolio,
                a1_momentum_pocket_portfolio_csv,
                a1_momentum_daily_state_guard_md,
                a1_momentum_daily_state_guard_json,
                a1_momentum_daily_state_guard,
                a1_momentum_daily_state_guard_csv,
                a1_momentum_feature_loss_md,
                a1_momentum_feature_loss_json,
                a1_momentum_feature_loss,
                a1_momentum_feature_loss_filter_csv,
                a1_momentum_feature_loss_bin_csv,
                a1_momentum_feature_loss_portfolio_md,
                a1_momentum_feature_loss_portfolio_json,
                a1_momentum_feature_loss_portfolio,
                a1_momentum_feature_loss_guard_optimizer_md,
                a1_momentum_feature_loss_guard_optimizer_json,
                a1_momentum_feature_loss_guard_optimizer_csv,
                a1_momentum_feature_loss_guard_optimizer,
                a1_momentum_feature_pair_filter_md,
                a1_momentum_feature_pair_filter_json,
                a1_momentum_feature_pair_filter_csv,
                a1_momentum_feature_pair_filter,
                a1_momentum_feature_band_daily_income_md,
                a1_momentum_feature_band_daily_income_json,
                a1_momentum_feature_band_daily_income_csv,
                a1_momentum_feature_band_daily_income,
                a1_momentum_feature_band_daily_income_forward_draft,
                a1_momentum_feature_band_daily_income_readiness_md,
                a1_momentum_feature_band_daily_income_readiness_json,
                a1_momentum_feature_band_daily_income_readiness,
                a1_momentum_feature_band_day_state_md,
                a1_momentum_feature_band_day_state_json,
                a1_momentum_feature_band_day_state_csv,
                a1_momentum_feature_band_day_state,
                a1_momentum_feature_band_daily_reliability_forward_draft,
                a1_momentum_feature_band_daily_reliability_readiness_md,
                a1_momentum_feature_band_daily_reliability_readiness_json,
                a1_momentum_feature_band_daily_reliability_readiness,
                a1_momentum_feature_band_residual_md,
                a1_momentum_feature_band_residual_json,
                a1_momentum_feature_band_residual_csv,
                a1_momentum_feature_band_residual,
                a1_momentum_feature_band_residual_stress_md,
                a1_momentum_feature_band_residual_stress_json,
                a1_momentum_feature_band_residual_stress_csv,
                a1_momentum_feature_band_residual_stress,
                a1_momentum_feature_band_residual_package_optimizer_md,
                a1_momentum_feature_band_residual_package_optimizer_json,
                a1_momentum_feature_band_residual_package_optimizer_csv,
                a1_momentum_feature_band_residual_package_optimizer,
                a1_momentum_feature_band_residual_plus50_cooldown10_forward_draft,
                a1_momentum_feature_band_residual_plus50_cooldown10_readiness_md,
                a1_momentum_feature_band_residual_plus50_cooldown10_readiness_json,
                a1_momentum_feature_band_residual_plus50_cooldown10_readiness,
                a1_momentum_feature_band_residual_plus75_high_net_forward_draft,
                a1_momentum_feature_band_residual_plus75_high_net_readiness_md,
                a1_momentum_feature_band_residual_plus75_high_net_readiness_json,
                a1_momentum_feature_band_residual_plus75_high_net_readiness,
                a1_momentum_business_goal_scoreboard_md,
                a1_momentum_business_goal_scoreboard_json,
                a1_momentum_business_goal_scoreboard_csv,
                a1_momentum_business_goal_scoreboard,
                a1_momentum_business_goal_promotion_packet_md,
                a1_momentum_business_goal_promotion_packet_json,
                a1_momentum_business_goal_promotion_packet,
                a1_momentum_business_goal_calendar_cadence_audit_md,
                a1_momentum_business_goal_calendar_cadence_audit_json,
                a1_momentum_business_goal_calendar_cadence_audit,
                a1_momentum_market_day_coverage_search_md,
                a1_momentum_market_day_coverage_search_json,
                a1_momentum_market_day_coverage_search_csv,
                a1_momentum_market_day_coverage_search,
                a1_momentum_market_day_coverage_stress_md,
                a1_momentum_market_day_coverage_stress_json,
                a1_momentum_market_day_coverage_stress_csv,
                a1_momentum_market_day_coverage_stress,
                a1_momentum_feature_band_residual_reliability_forward_draft,
                a1_momentum_feature_band_residual_reliability_readiness_md,
                a1_momentum_feature_band_residual_reliability_readiness_json,
                a1_momentum_feature_band_residual_reliability_readiness,
            )
        },
        "diagnostics": {
            "xau_920101_breakout_retest_failure_forensic": _xau_920101_failure_forensic(
                repo_root,
                xau_920101_active_forensic_md,
                xau_920101_active_forensic_json,
                xau_920101_failure_forensic,
            )
        },
        "authorization": {
            "canonical_phase2_pass": False,
            "live_trading_authorized": False,
            "real_capital_authorized": False,
            "broad_afternoon_ban_authorized": False,
            "direction_only_rule_authorized": False,
            "cost_threshold_runtime_rule_authorized": False,
            "a3_tier1_demo_broker_action": historical_a3_authorization["933400_demo_broker_action"],
            "a3_current_runtime_authorization": effective_a3_authorization,
            "a3_effective_runtime_authorization": effective_a3_authorization,
        },
        "next_evidence_required": [
            "SQ-01 hash-locked A3_SIGNAL_QUALITY_V1_IMPLEMENTATION_ADDENDUM_01.md",
            "SQ-02 hash-locked A3_SIGNAL_QUALITY_DIAGNOSTIC_SWEEP_V1_2026_06_18.md",
            "SQ-03 offline Python discovery sweep with frequency-quality and loss-attribution table",
            "Green CI run tied to the exact source commit before any shadow-terminal attachment",
            "A3 remains paused; no broker action, profile arming, or runtime attach before evidence gates pass",
            "A1 XAU M5 momentum-continuation lane: capture first magic 932200 order-log row or guard-block row after a valid break-and-run signal",
        ],
    }

    output_json.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    output_md.write_text(_render_markdown(summary), encoding="utf-8")
    return output_json, output_md


def _generate_governance_status(
    *,
    repo_root: Path,
    phase1_root: Path,
    output_json: Path,
    output_md: Path,
    now: datetime,
    documents: dict[str, Path],
) -> tuple[Path, Path]:
    generated_at = now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    ledger_path = repo_root / CURRENT_CONTROL_LEDGER_PATH
    if not ledger_path.is_file():
        raise FileNotFoundError(f"Frozen current-control ledger is missing: {ledger_path}")
    actual_ledger_sha256 = _sha256_file(ledger_path)
    ledger_representation = "exact_frozen_bytes"
    if actual_ledger_sha256 != CURRENT_CONTROL_LEDGER_SHA256:
        raw = ledger_path.read_bytes()
        # Git stores this tracked CSV with LF endings, while the immutable MT5/Python
        # artifact named by the preregistration was hashed with CRLF endings. Accept
        # only the exact Git-normalized byte representation of that same artifact.
        crlf_sha256 = hashlib.sha256(raw.replace(b"\n", b"\r\n")).hexdigest() if b"\r" not in raw else ""
        if crlf_sha256 == CURRENT_CONTROL_LEDGER_SHA256:
            ledger_representation = "git_lf_checkout_of_frozen_crlf_artifact"
        else:
            raise ValueError(
                "Frozen current-control ledger SHA256 mismatch: "
                f"expected={CURRENT_CONTROL_LEDGER_SHA256}; actual={actual_ledger_sha256}; path={ledger_path}"
            )
    source_documents = {
        key: {
            "path": _rel(repo_root, path),
            "sha256": _sha256_file(path),
        }
        for key, path in documents.items()
    }
    current = {
        "overall_status": "NO_GO_RESEARCH_ONLY",
        "north_star": GOVERNANCE_NORTH_STAR,
        "required_current_statements": list(GOVERNANCE_REQUIRED_STATEMENTS),
        "authority_map": {
            "authoritative_next_task_key": "primary_next_task",
            "authoritative_statements_key": "required_current_statements",
            "compatibility_next_task_key": "control_diagnostic_task",
            "compatibility_statements_key": "control_diagnostic_compatibility_statements",
        },
        "control_diagnostic_compatibility_statements": list(
            GOVERNANCE_CONTROL_DIAGNOSTIC_COMPATIBILITY_STATEMENTS
        ),
        "independent_specialist_program": {
            "id": "R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1",
            "status": "PRIMARY_INDEPENDENT_SPECIALIST_LANE",
            "next_action": "NP1-A",
            "np1_status": "MANDATORY_PREREQUISITE_WITHIN_R6",
            "parallel_specialist_lane_authorized": False,
            "range_box_status": "BACKLOG_ONLY_IF_R6_CLOSES",
            "historical_pnl_authorized": False,
        },
        "portfolio_control": {
            "id": "current_r1_r2_baseline",
            "status": "CURRENT_RESEARCH_CONTROL",
            "admission_status": "RESEARCH_CONTROL_NOT_DEPLOYMENT_AUTHORIZED",
            "ledger": CURRENT_CONTROL_LEDGER_PATH,
            "ledger_sha256": CURRENT_CONTROL_LEDGER_SHA256,
            "checkout_sha256": actual_ledger_sha256,
            "checkout_representation": ledger_representation,
            "metrics": {
                "trades": 678,
                "win_rate_pct": 51.03,
                "realized_win_loss": 2.6082,
                "profit_factor": 2.7182,
                "net_usd": 9640.05,
                "stress_net_minus_0_30_per_ticket_usd": 9436.65,
                "recent_three_month_net_usd": 764.92,
                "max_closed_drawdown_usd": 889.69,
                "positive_months": 26,
                "active_weekdays_pct_approx": 21.28,
            },
        },
        "specialists": {
            "R1": {
                "status": "RESEARCH_CONTROL_ONLY",
                "compatibility_frozen_status": "CURRENT_RESEARCH_CONTROL_COMPONENT",
                "role": "Primary bullish/uptrend profit engine",
            },
            "R2": {
                "status": "RESEARCH_CONTROL_ONLY",
                "compatibility_frozen_status": "CURRENT_RESEARCH_CONTROL_COMPONENT",
                "role": "Strict downtrend hedge and secondary profit source",
            },
            "R3": {
                "standalone_status": "EXCLUDED",
                "compatibility_frozen_status": "STANDALONE_SHADOW_ONLY",
                "portfolio_status": "KILLED_BY_DD_GATE",
            },
            "R4": {
                "status": "NO_SURVIVOR",
                "chop_default": "NO_TRADE",
            },
        },
        "rule_admissibility": {
            "status": "BLOCKED_LEGACY_RULE_ADMISSIBILITY",
            "identity_scope": "PRESERVES_678_ROW_AUDIT_IDENTITY_ONLY",
            "audit_identity_rows": 678,
            "rules_endorsed_for_integrated_admission": False,
            "sources": [dict(item) for item in GOVERNANCE_RULE_ADMISSIBILITY_SOURCES],
            "integrated_admission_requirement": (
                "Independently qualified rule-clean sources or later reviewed governance"
            ),
            "future_containment_requirement": "SHARED_PREREGISTERED_INTEGRATED_RISK_POLICY",
            "source_local_containment_reusable_for_standalone_admission": False,
            "otherwise": "NO_GO",
            "router_audit_rule_change_authorized": False,
        },
        "attribution_status": "REPAIR_REQUIRED_NATIVE_POSITION_JOIN",
        "attribution_repair": {
            "total_rows": 678,
            "legacy_pairing_method": "FIFO_BY_DIRECTION",
            "non_native_exit_deal_rows": 388,
            "non_native_individual_pnl_rows": 387,
            "aggregate_exit_pnl_multiset_exact": True,
            "source_totals_exact": True,
            "portfolio_totals_exact": True,
            "native_positions_recoverable": True,
            "native_position_count": 678,
            "required_before_classification": (
                "OUTCOME_BLIND_ENTRY_DEAL_TO_NATIVE_POSITION_ID_JOIN_AND_RECONCILIATION"
            ),
            "fifo_fallback_authorized": False,
            "strategy_change_authorized": False,
        },
        "historical_evidence": {
            "through": "2026-06-30",
            "classification": "DEVELOPMENT_DATA",
            "untouched_holdout": False,
        },
        "authorization": {
            "demo_authorized": False,
            "live_authorized": False,
            "broker_action_authorized": False,
            "runtime_touched": False,
        },
        "primary_next_task": {
            "id": "R6-NP1-A_MARKET_ONLY_NATIVE_PARITY_ACQUISITION_LOCKS",
            "status": "AUTHORIZED_NOT_STARTED",
            "strategy_change_authorized": False,
            "ea_trading_logic_change": "NONE",
        },
        "next_task": {
            "id": "R6-NP1-A_MARKET_ONLY_NATIVE_PARITY_ACQUISITION_LOCKS",
            "status": "AUTHORIZED_NOT_STARTED",
            "strategy_change_authorized": False,
            "ea_trading_logic_change": "NONE",
            "authority": "ALIAS_OF_PRIMARY_NEXT_TASK",
        },
        "control_diagnostic_task": {
            "id": "A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_V1",
            "status": "DEFERRED_CONTROL_DIAGNOSTIC",
            "original_lock_status": "PREREGISTERED_NOT_RUN",
            "authoritative_for_primary_program": False,
            "blocks_r6_standalone_discovery": False,
            "required_before_old_control_integration": True,
            "strategy_change_authorized": False,
            "ea_trading_logic_change": "NONE",
        },
        "router_entry_hold_audit": {
            "status": "DEFERRED_CONTROL_DIAGNOSTIC",
            "blocks_r6_standalone_discovery": False,
            "required_before_old_control_integration": True,
        },
    }
    summary: dict[str, Any] = {
        "schema_version": GOVERNANCE_SCHEMA,
        "generated_at_utc": generated_at,
        "repo": {
            "branch": _git(repo_root, "branch", "--show-current"),
            "base_commit": _git(repo_root, "rev-parse", "HEAD"),
        },
        "source_documents": source_documents,
        "current": current,
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(_render_governance_markdown(summary), encoding="utf-8")
    _write_phase_local_status_pointers(phase1_root, generated_at)
    return output_json, output_md


def _render_governance_markdown(summary: dict[str, Any]) -> str:
    current = _mapping(summary.get("current"))
    control = _mapping(current.get("portfolio_control"))
    metrics = _mapping(control.get("metrics"))
    specialists = _mapping(current.get("specialists"))
    r1 = _mapping(specialists.get("R1"))
    r2 = _mapping(specialists.get("R2"))
    r3 = _mapping(specialists.get("R3"))
    r4 = _mapping(specialists.get("R4"))
    rule_admissibility = _mapping(current.get("rule_admissibility"))
    attribution_repair = _mapping(current.get("attribution_repair"))
    history = _mapping(current.get("historical_evidence"))
    authorization = _mapping(current.get("authorization"))
    authority_map = _mapping(current.get("authority_map"))
    program = _mapping(current.get("independent_specialist_program"))
    next_task = _mapping(current.get("primary_next_task"))
    control_diagnostic = _mapping(current.get("control_diagnostic_task"))
    repo = _mapping(summary.get("repo"))
    documents = _mapping(summary.get("source_documents"))

    lines = [
        "# A1 XAUUSD Current Governance Status",
        "",
        f"Status: `{current.get('overall_status', 'UNKNOWN')}`",
        f"Schema: `{summary.get('schema_version', '')}`",
        f"Generated UTC: `{summary.get('generated_at_utc', '')}`",
        f"Branch: `{repo.get('branch', '')}`",
        f"Base commit: `{repo.get('base_commit', '')}`",
        "",
        "This is the only authoritative current status surface. Historical phase/runtime summaries are non-authorizing.",
        "",
        "## North star",
        "",
        f"> {current.get('north_star', '')}",
        "",
        "## Required current statements",
        "",
        "```text",
        *[str(item) for item in current.get("required_current_statements", [])],
        "```",
        "",
        "## Primary independent-specialist lane",
        "",
        f"Primary lane: `{program.get('id', '')}`",
        f"Standing: `{program.get('status', '')}`",
        f"Next action: `{program.get('next_action', '')}` — market-only native Router/contract acquisition locks",
        f"NP1 standing: `{program.get('np1_status', '')}`",
        f"Parallel specialist lane authorized: `{str(program.get('parallel_specialist_lane_authorized', False)).lower()}`",
        f"Historical R6 P/L authorized: `{str(program.get('historical_pnl_authorized', False)).lower()}`",
        "",
        "R6 owns the pre-downtrend distribution / failed-reclaim transition while Router V1 is `UPTREND` or `CHOP`.",
        "The H1/H4 objective range-box family is backlog only if R6 closes and a later owner/reviewer packet selects it.",
        "",
        "## Machine-readable authority",
        "",
        f"Authoritative task key: `{authority_map.get('authoritative_next_task_key', '')}`",
        f"Authoritative statements key: `{authority_map.get('authoritative_statements_key', '')}`",
        f"Compatibility task key: `{authority_map.get('compatibility_next_task_key', '')}`",
        "",
        "## Current research control",
        "",
        f"Control: `{control.get('id', '')}`",
        f"Standing: `{control.get('status', '')}`; `{control.get('admission_status', '')}`",
        f"Ledger SHA256: `{control.get('ledger_sha256', '')}`",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Trades | `{metrics.get('trades', '')}` |",
        f"| Win rate | `{metrics.get('win_rate_pct', '')}%` |",
        f"| Realized W/L | `{metrics.get('realized_win_loss', '')}` |",
        f"| Profit factor | `{metrics.get('profit_factor', '')}` |",
        f"| Net | `+${metrics.get('net_usd', 0):,.2f}` |",
        f"| Stress net at -$0.30/ticket | `+${metrics.get('stress_net_minus_0_30_per_ticket_usd', 0):,.2f}` |",
        f"| Recent-three-month net | `+${metrics.get('recent_three_month_net_usd', 0):,.2f}` |",
        f"| Maximum closed drawdown | `${metrics.get('max_closed_drawdown_usd', 0):,.2f}` |",
        f"| Positive months | `{metrics.get('positive_months', '')}` |",
        f"| Active weekdays | `approximately {metrics.get('active_weekdays_pct_approx', '')}%` |",
        "",
        "## Specialist ownership",
        "",
        "| Specialist | Primary-program standing | Frozen compatibility standing | Role / default |",
        "| --- | --- | --- | --- |",
        f"| R1 | `{r1.get('status', '')}` | `{r1.get('compatibility_frozen_status', '')}` | {r1.get('role', '')} |",
        f"| R2 | `{r2.get('status', '')}` | `{r2.get('compatibility_frozen_status', '')}` | {r2.get('role', '')} |",
        f"| R3 | `{r3.get('standalone_status', '')}` | `{r3.get('compatibility_frozen_status', '')}`; `{r3.get('portfolio_status', '')}` | Not independent; excluded from portfolio use |",
        f"| R4 | `{r4.get('status', '')}` | `{r4.get('status', '')}` | Chop default `{r4.get('chop_default', '')}` |",
        "",
        "## Post-audit rule admissibility",
        "",
        f"Status: `{rule_admissibility.get('status', '')}`",
        f"Identity scope: `{rule_admissibility.get('identity_scope', '')}`",
        "",
        "The four retained rules below preserve the 678-row audit identity only; they are not endorsed for integration.",
        "The first three are forbidden selection rules. The R2 $10 daily-loss stop is source-local containment, not standalone alpha/admission evidence, and cannot be reused as such.",
        "Future containment must be a shared preregistered integrated risk policy.",
        "Integrated admission requires independently qualified rule-clean sources or later reviewed governance.",
        "Otherwise the result is `NO_GO`. The router audit cannot remove or repair these rules.",
        "",
        "| Frozen source | Admissibility issue | Retained rule type | Retained rule |",
        "| --- | --- | --- | --- |",
    ]
    for source in rule_admissibility.get("sources", []):
        source = _mapping(source)
        lines.append(
            f"| `{source.get('source_id', '')}` | `{source.get('admissibility_issue_type', '')}` | "
            f"`{source.get('retained_rule_type', '')}` | {source.get('retained_rule', '')} |"
        )
    lines.extend(
        [
        "",
        "## Native-position attribution repair",
        "",
        f"Attribution status: `{current.get('attribution_status', '')}`",
        "",
        (
            f"The legacy direction-FIFO parser assigned a non-native exit deal to "
            f"`{attribution_repair.get('non_native_exit_deal_rows', '')}/"
            f"{attribution_repair.get('total_rows', '')}` rows and non-native individual P/L to "
            f"`{attribution_repair.get('non_native_individual_pnl_rows', '')}/"
            f"{attribution_repair.get('total_rows', '')}` rows."
        ),
        "The aggregate exit/P&L multiset and source/portfolio totals remain exact, and all 678 native positions are recoverable.",
        "The audit must complete the outcome-blind native position join and reconcile it before any router classification.",
        "FIFO fallback is prohibited. This is evidence-attribution repair only; no strategy change is authorized.",
        "",
        "## Evidence and authorization boundary",
        "",
        f"All inspected history through `{history.get('through', '')}` is `{history.get('classification', '')}`.",
        "It is not an untouched holdout.",
        "",
        "| Authorization fact | Value |",
        "| --- | ---: |",
        f"| Demo authorized | `{str(authorization.get('demo_authorized', False)).lower()}` |",
        f"| Live authorized | `{str(authorization.get('live_authorized', False)).lower()}` |",
        f"| Broker action authorized | `{str(authorization.get('broker_action_authorized', False)).lower()}` |",
        f"| Runtime touched | `{str(authorization.get('runtime_touched', False)).lower()}` |",
        "",
        "## Immediate next task",
        "",
        f"Next task: `{next_task.get('id', '')}`",
        f"Status: `{next_task.get('status', '')}`",
        f"Strategy change authorized: `{str(next_task.get('strategy_change_authorized', False)).lower()}`",
        f"EA trading-logic change: `{next_task.get('ea_trading_logic_change', '')}`",
        "",
        "## Deferred control diagnostic",
        "",
        f"Control task: `{control_diagnostic.get('id', '')}`",
        f"Status: `{control_diagnostic.get('status', '')}`",
        f"Authoritative for primary program: `{str(control_diagnostic.get('authoritative_for_primary_program', False)).lower()}`",
        "It remains required before the old R1+R2 control can enter an integrated portfolio, but it does not block R6 standalone discovery.",
        "",
        "### Frozen compatibility statements",
        "",
        "```text",
        *[str(item) for item in current.get("control_diagnostic_compatibility_statements", [])],
        "```",
        "",
        "## Governing documents",
        "",
        "| Document | SHA256 |",
        "| --- | --- |",
        ]
    )
    for key in GOVERNANCE_DOCUMENT_NAMES:
        document = _mapping(documents.get(key))
        path = str(document.get("path", ""))
        lines.append(f"| [{key}]({path}) | `{document.get('sha256', '')}` |")
    lines.append("")
    return "\n".join(lines)


def _write_phase_local_status_pointers(phase1_root: Path, generated_at: str) -> None:
    pointer_json = phase1_root / DEFAULT_JSON
    pointer_md = phase1_root / DEFAULT_MD
    pointer = {
        "schema_version": GOVERNANCE_POINTER_SCHEMA,
        "status": "LEGACY_LOCATION_NOT_CANONICAL",
        "generated_at_utc": generated_at,
        "authoritative_schema": GOVERNANCE_SCHEMA,
        "canonical_json": "../../status_summary.json",
        "canonical_markdown": "../../status_summary.md",
        "message": "This phase-local status location is a pointer only and carries no current authorization claim.",
    }
    pointer_json.parent.mkdir(parents=True, exist_ok=True)
    pointer_json.write_text(json.dumps(pointer, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    pointer_md.write_text(
        "\n".join(
            [
                "# Legacy Phase-Local Status Pointer",
                "",
                "Status: `LEGACY_LOCATION_NOT_CANONICAL`",
                "",
                "This phase-local path is non-authoritative and carries no current trading or authorization claim.",
                "",
                "Use the repository-root [status_summary.md](../../status_summary.md) and "
                "[status_summary.json](../../status_summary.json).",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _read_runtime_inventory(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    data = path.read_bytes()
    if b"\x00" in data[:200]:
        text = data.decode("utf-16", errors="replace")
    else:
        text = data.decode("utf-8-sig", errors="replace")
    return list(csv.DictReader(text.splitlines()))


def _a1_momentum_lane(
    repo_root: Path,
    report_json_path: Path,
    report_md_path: Path,
    report: dict[str, Any],
    backtest_md_path: Path | None = None,
    backtest_json_path: Path | None = None,
    backtest: dict[str, Any] | None = None,
    variant_backtest_md_path: Path | None = None,
    variant_backtest_json_path: Path | None = None,
    variant_backtest: dict[str, Any] | None = None,
    variant_diagnosis_md_path: Path | None = None,
    frequency_repair_md_path: Path | None = None,
    frequency_repair_json_path: Path | None = None,
    frequency_repair: dict[str, Any] | None = None,
    frequency_replacement_readiness_path: Path | None = None,
    frequency_v6_diagnostic_path: Path | None = None,
    frequency_requirement_verdict_path: Path | None = None,
    portfolio_diagnostic_md_path: Path | None = None,
    portfolio_diagnostic_json_path: Path | None = None,
    portfolio_diagnostic: dict[str, Any] | None = None,
    portfolio_forward_draft_path: Path | None = None,
    broad_portfolio_md_path: Path | None = None,
    broad_portfolio_json_path: Path | None = None,
    broad_portfolio: dict[str, Any] | None = None,
    broad_portfolio_verdict_path: Path | None = None,
    clean_portfolio_forward_draft_path: Path | None = None,
    deep_portfolio_md_path: Path | None = None,
    deep_portfolio_json_path: Path | None = None,
    deep_portfolio: dict[str, Any] | None = None,
    deep_portfolio_stress_md_path: Path | None = None,
    deep_portfolio_stress_json_path: Path | None = None,
    deep_portfolio_stress: dict[str, Any] | None = None,
    deep_portfolio_verdict_path: Path | None = None,
    deep_portfolio_forward_draft_path: Path | None = None,
    robust_portfolio_md_path: Path | None = None,
    robust_portfolio_json_path: Path | None = None,
    robust_portfolio: dict[str, Any] | None = None,
    robust_portfolio_stress_md_path: Path | None = None,
    robust_portfolio_stress_json_path: Path | None = None,
    robust_portfolio_stress: dict[str, Any] | None = None,
    robust_portfolio_forward_draft_path: Path | None = None,
    robust_portfolio_walkforward_md_path: Path | None = None,
    robust_portfolio_walkforward_json_path: Path | None = None,
    robust_portfolio_walkforward: dict[str, Any] | None = None,
    robust_portfolio_repair_md_path: Path | None = None,
    robust_portfolio_repair_json_path: Path | None = None,
    robust_portfolio_repair: dict[str, Any] | None = None,
    robust_repair_walkforward_md_path: Path | None = None,
    robust_repair_walkforward_json_path: Path | None = None,
    robust_repair_walkforward: dict[str, Any] | None = None,
    robust_repair_forward_draft_path: Path | None = None,
    daily_fit_md_path: Path | None = None,
    daily_fit_json_path: Path | None = None,
    daily_fit: dict[str, Any] | None = None,
    daily_fit_forward_draft_path: Path | None = None,
    daily_fit_stress_md_path: Path | None = None,
    daily_fit_stress_json_path: Path | None = None,
    daily_fit_stress: dict[str, Any] | None = None,
    daily_fit_repair_md_path: Path | None = None,
    daily_fit_repair_json_path: Path | None = None,
    daily_fit_repair: dict[str, Any] | None = None,
    daily_fit_repair_forward_draft_path: Path | None = None,
    daily_guard_md_path: Path | None = None,
    daily_guard_json_path: Path | None = None,
    daily_guard: dict[str, Any] | None = None,
    daily_guard_forward_draft_path: Path | None = None,
    pocket_portfolio_md_path: Path | None = None,
    pocket_portfolio_json_path: Path | None = None,
    pocket_portfolio: dict[str, Any] | None = None,
    pocket_portfolio_csv_path: Path | None = None,
    daily_state_guard_md_path: Path | None = None,
    daily_state_guard_json_path: Path | None = None,
    daily_state_guard: dict[str, Any] | None = None,
    daily_state_guard_csv_path: Path | None = None,
    feature_loss_md_path: Path | None = None,
    feature_loss_json_path: Path | None = None,
    feature_loss: dict[str, Any] | None = None,
    feature_loss_filter_csv_path: Path | None = None,
    feature_loss_bin_csv_path: Path | None = None,
    feature_loss_portfolio_md_path: Path | None = None,
    feature_loss_portfolio_json_path: Path | None = None,
    feature_loss_portfolio: dict[str, Any] | None = None,
    feature_loss_guard_optimizer_md_path: Path | None = None,
    feature_loss_guard_optimizer_json_path: Path | None = None,
    feature_loss_guard_optimizer_csv_path: Path | None = None,
    feature_loss_guard_optimizer: dict[str, Any] | None = None,
    feature_pair_filter_md_path: Path | None = None,
    feature_pair_filter_json_path: Path | None = None,
    feature_pair_filter_csv_path: Path | None = None,
    feature_pair_filter: dict[str, Any] | None = None,
    feature_band_daily_income_md_path: Path | None = None,
    feature_band_daily_income_json_path: Path | None = None,
    feature_band_daily_income_csv_path: Path | None = None,
    feature_band_daily_income: dict[str, Any] | None = None,
    feature_band_daily_income_forward_draft_path: Path | None = None,
    feature_band_daily_income_readiness_md_path: Path | None = None,
    feature_band_daily_income_readiness_json_path: Path | None = None,
    feature_band_daily_income_readiness: dict[str, Any] | None = None,
    feature_band_day_state_md_path: Path | None = None,
    feature_band_day_state_json_path: Path | None = None,
    feature_band_day_state_csv_path: Path | None = None,
    feature_band_day_state: dict[str, Any] | None = None,
    feature_band_daily_reliability_forward_draft_path: Path | None = None,
    feature_band_daily_reliability_readiness_md_path: Path | None = None,
    feature_band_daily_reliability_readiness_json_path: Path | None = None,
    feature_band_daily_reliability_readiness: dict[str, Any] | None = None,
    feature_band_residual_md_path: Path | None = None,
    feature_band_residual_json_path: Path | None = None,
    feature_band_residual_csv_path: Path | None = None,
    feature_band_residual: dict[str, Any] | None = None,
    feature_band_residual_stress_md_path: Path | None = None,
    feature_band_residual_stress_json_path: Path | None = None,
    feature_band_residual_stress_csv_path: Path | None = None,
    feature_band_residual_stress: dict[str, Any] | None = None,
    feature_band_residual_package_optimizer_md_path: Path | None = None,
    feature_band_residual_package_optimizer_json_path: Path | None = None,
    feature_band_residual_package_optimizer_csv_path: Path | None = None,
    feature_band_residual_package_optimizer: dict[str, Any] | None = None,
    feature_band_residual_plus50_cooldown10_forward_draft_path: Path | None = None,
    feature_band_residual_plus50_cooldown10_readiness_md_path: Path | None = None,
    feature_band_residual_plus50_cooldown10_readiness_json_path: Path | None = None,
    feature_band_residual_plus50_cooldown10_readiness: dict[str, Any] | None = None,
    feature_band_residual_plus75_high_net_forward_draft_path: Path | None = None,
    feature_band_residual_plus75_high_net_readiness_md_path: Path | None = None,
    feature_band_residual_plus75_high_net_readiness_json_path: Path | None = None,
    feature_band_residual_plus75_high_net_readiness: dict[str, Any] | None = None,
    business_goal_scoreboard_md_path: Path | None = None,
    business_goal_scoreboard_json_path: Path | None = None,
    business_goal_scoreboard_csv_path: Path | None = None,
    business_goal_scoreboard: dict[str, Any] | None = None,
    business_goal_promotion_packet_md_path: Path | None = None,
    business_goal_promotion_packet_json_path: Path | None = None,
    business_goal_promotion_packet: dict[str, Any] | None = None,
    business_goal_calendar_cadence_audit_md_path: Path | None = None,
    business_goal_calendar_cadence_audit_json_path: Path | None = None,
    business_goal_calendar_cadence_audit: dict[str, Any] | None = None,
    business_goal_market_day_coverage_search_md_path: Path | None = None,
    business_goal_market_day_coverage_search_json_path: Path | None = None,
    business_goal_market_day_coverage_search_csv_path: Path | None = None,
    business_goal_market_day_coverage_search: dict[str, Any] | None = None,
    business_goal_market_day_coverage_stress_md_path: Path | None = None,
    business_goal_market_day_coverage_stress_json_path: Path | None = None,
    business_goal_market_day_coverage_stress_csv_path: Path | None = None,
    business_goal_market_day_coverage_stress: dict[str, Any] | None = None,
    feature_band_residual_reliability_forward_draft_path: Path | None = None,
    feature_band_residual_reliability_readiness_md_path: Path | None = None,
    feature_band_residual_reliability_readiness_json_path: Path | None = None,
    feature_band_residual_reliability_readiness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not report:
        return {
            "status": "MISSING",
            "report": _rel(repo_root, report_md_path),
            "json": _rel(repo_root, report_json_path),
        }
    ea = report.get("ea", {})
    boundaries = report.get("boundaries", {})
    terminal = report.get("terminal", {})
    order_tail = report.get("order_tail", [])
    signal_tail = report.get("signal_tail", [])
    startup_tail = report.get("startup_tail", [])
    backtest = backtest or {}
    variant_backtest = variant_backtest or {}
    frequency_repair = frequency_repair or {}
    portfolio_diagnostic = portfolio_diagnostic or {}
    broad_portfolio = broad_portfolio or {}
    deep_portfolio = deep_portfolio or {}
    deep_portfolio_stress = deep_portfolio_stress or {}
    robust_portfolio = robust_portfolio or {}
    robust_portfolio_stress = robust_portfolio_stress or {}
    robust_portfolio_walkforward = robust_portfolio_walkforward or {}
    robust_portfolio_repair = robust_portfolio_repair or {}
    robust_repair_walkforward = robust_repair_walkforward or {}
    daily_fit = daily_fit or {}
    daily_fit_stress = daily_fit_stress or {}
    daily_fit_repair = daily_fit_repair or {}
    daily_guard = daily_guard or {}
    pocket_portfolio = pocket_portfolio or {}
    daily_state_guard = daily_state_guard or {}
    feature_loss = feature_loss or {}
    feature_loss_portfolio = feature_loss_portfolio or {}
    feature_loss_guard_optimizer = feature_loss_guard_optimizer or {}
    feature_pair_filter = feature_pair_filter or {}
    feature_band_daily_income = feature_band_daily_income or {}
    feature_band_daily_income_readiness = feature_band_daily_income_readiness or {}
    feature_band_residual_stress = feature_band_residual_stress or {}
    feature_band_residual_package_optimizer = feature_band_residual_package_optimizer or {}
    feature_band_residual_plus50_cooldown10_readiness = feature_band_residual_plus50_cooldown10_readiness or {}
    feature_band_residual_plus75_high_net_readiness = feature_band_residual_plus75_high_net_readiness or {}
    business_goal_scoreboard = business_goal_scoreboard or {}
    business_goal_promotion_packet = business_goal_promotion_packet or {}
    business_goal_calendar_cadence_audit = business_goal_calendar_cadence_audit or {}
    business_goal_market_day_coverage_search = business_goal_market_day_coverage_search or {}
    business_goal_market_day_coverage_stress = business_goal_market_day_coverage_stress or {}
    backtest_overall = backtest.get("overall", {})
    backtest_direction = backtest.get("direction", {})
    variant_winner = variant_backtest.get("winner", {})
    frequency_repaired = frequency_repair.get("repaired_variant", {})
    frequency_repair_decision = frequency_repair.get("decision", {})
    portfolio_summaries = portfolio_diagnostic.get("summaries", [])
    portfolio_candidate = next(
        (item for item in portfolio_summaries if item.get("name") == "v4_plus_v13_leading_raw"),
        portfolio_summaries[0] if portfolio_summaries else {},
    )
    broad_candidates = broad_portfolio.get("top_candidates", [])
    clean_broad_candidate = next(
        (
            item
            for item in broad_candidates
            if item.get("name") == "v5_v4_move12 + freq_h1_h4_short_rr0p7_v1_core_1_5_15_19"
        ),
        {},
    )
    headline_broad_candidate = broad_candidates[0] if broad_candidates else {}
    deep_candidates = deep_portfolio.get("top_candidates", [])
    headline_deep_candidate = deep_candidates[0] if deep_candidates else {}
    low_overlap_deep_candidate = next(
        (
            item
            for item in deep_candidates
            if item.get("name")
            == (
                "v6_freq_v4_rr0p7_max2 + "
                "v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning + "
                "freq_h1_h4_short_rr0p7_v1_core_1_5_15_19"
            )
        ),
        headline_deep_candidate,
    )
    robust_candidates = robust_portfolio.get("top_candidates", [])
    headline_robust_candidate = robust_candidates[0] if robust_candidates else {}
    robust_walkforward_half_year = robust_portfolio_walkforward.get("half_year", [])
    weakest_robust_half_year = (
        min(
            robust_walkforward_half_year,
            key=lambda row: float(row.get("profit_factor") or 0.0),
        )
        if robust_walkforward_half_year
        else {}
    )
    robust_repair_candidates = robust_portfolio_repair.get("top_candidates", [])
    robust_repair_best = next(
        (
            item
            for item in robust_repair_candidates
            if item.get("filters") == ["v13_ema_trend_h1h4_long_rr0p6_no_morning@18"]
        ),
        robust_repair_candidates[0] if robust_repair_candidates else {},
    )
    robust_repair_walkforward_half_year = robust_repair_walkforward.get("half_year", [])
    weakest_robust_repair_half_year = (
        min(
            robust_repair_walkforward_half_year,
            key=lambda row: float(row.get("profit_factor") or 0.0),
        )
        if robust_repair_walkforward_half_year
        else {}
    )
    daily_fit_candidates = daily_fit.get("top_candidates", [])
    headline_daily_fit_candidate = daily_fit_candidates[0] if daily_fit_candidates else {}
    daily_fit_stress_candidate = daily_fit_stress.get("candidate", {})
    daily_fit_repair_candidates = daily_fit_repair.get("top_repairs", daily_fit_repair.get("top_candidates", []))
    headline_daily_fit_repair = daily_fit_repair_candidates[0] if daily_fit_repair_candidates else {}
    daily_guard_candidates = daily_guard.get("top_results", [])
    headline_daily_guard = daily_guard_candidates[0] if daily_guard_candidates else {}
    pocket_candidates = pocket_portfolio.get("top_candidates", [])
    headline_pocket_candidate = pocket_candidates[0] if pocket_candidates else {}
    pocket_non_sample_fail_count = sum(
        1 for item in pocket_candidates if not str(item.get("decision", "")).startswith("FAIL_SAMPLE")
    )
    daily_state_guard_candidates = daily_state_guard.get("top_candidates", [])
    headline_daily_state_guard = daily_state_guard_candidates[0] if daily_state_guard_candidates else {}
    daily_state_guard_review_count = sum(
        1 for item in daily_state_guard_candidates if str(item.get("decision", "")).startswith("REVIEW")
    )
    feature_loss_filters = feature_loss.get("top_filters", [])
    headline_feature_loss_filter = feature_loss_filters[0] if feature_loss_filters else {}
    feature_loss_review_count = sum(
        1 for item in feature_loss_filters if item.get("decision") == "FEATURE_FILTER_REVIEW_CANDIDATE"
    )
    feature_loss_portfolio_summaries = feature_loss_portfolio.get("summaries", [])
    feature_loss_portfolio_best_name = feature_loss_portfolio.get("best_frequency_first_candidate")
    headline_feature_loss_portfolio = next(
        (item for item in feature_loss_portfolio_summaries if item.get("name") == feature_loss_portfolio_best_name),
        {},
    )
    if not headline_feature_loss_portfolio:
        headline_feature_loss_portfolio = next(
            (
                item
                for item in feature_loss_portfolio_summaries
                if item.get("name") == "feature_daily_guard_long_plus_feature_v13"
            ),
            feature_loss_portfolio_summaries[0] if feature_loss_portfolio_summaries else {},
        )
    headline_feature_loss_guard_optimizer = feature_loss_guard_optimizer.get("best_frequency_first_candidate", {})
    feature_pair_filter_candidates = feature_pair_filter.get("top_rows", [])
    headline_feature_pair_filter = feature_pair_filter_candidates[0] if feature_pair_filter_candidates else {}
    headline_feature_band_daily_income = feature_band_daily_income.get("balanced_daily_income_candidate", {})
    frequency_replacement_ready = bool(
        frequency_repair
        and frequency_repair_decision.get("meets_frequency_goal")
        and frequency_repair_decision.get("meets_winrate_goal")
        and frequency_repair_decision.get("ready_for_live") is False
    )
    split_report_specs = [
        (
            "split_be_tp1_v6_max2",
            "A1_XAU_M5_MOMENTUM_SPLIT_BE_TP1_V6_MAX2_ATTACHMENT_2026_07_03",
        ),
        (
            "split_be_tp1_weak_hours",
            "A1_XAU_M5_MOMENTUM_SPLIT_BE_TP1_WEAK_HOURS_ATTACHMENT_2026_07_03",
        ),
        (
            "split_be_tp1_v13",
            "A1_XAU_M5_MOMENTUM_SPLIT_BE_TP1_V13_ATTACHMENT_2026_07_03",
        ),
    ]
    split_reports = []
    phase1_reports = repo_root / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    for key, stem in split_report_specs:
        split_json_path = phase1_reports / f"{stem}.json"
        split_md_path = phase1_reports / f"{stem}.md"
        split_report = _read_json(split_json_path)
        if not split_report:
            continue
        split_ea = split_report.get("ea", {})
        split_boundaries = split_report.get("boundaries", {})
        split_reports.append(
            {
                "key": key,
                "status": split_report.get("status", "UNKNOWN"),
                "report": _rel(repo_root, split_md_path),
                "json": _rel(repo_root, split_json_path),
                "run_id": split_ea.get("run_id", ""),
                "chart": split_ea.get("chart", ""),
                "magic": str(split_ea.get("magic", "")),
                "lot": str(split_ea.get("lot", "")),
                "order_comment": split_ea.get("order_comment", ""),
                "broker_action": bool(split_boundaries.get("broker_action_enabled_for_new_lane", False)),
                "spec_sha256": split_boundaries.get("spec_sha256", ""),
                "a1_only": bool(split_boundaries.get("a1_only", False)),
                "a2_touched": bool(split_boundaries.get("a2_touched", True)),
                "a3_touched": bool(split_boundaries.get("a3_touched", True)),
            }
        )
    return {
        "status": report.get("status", "UNKNOWN"),
        "report": _rel(repo_root, report_md_path),
        "json": _rel(repo_root, report_json_path),
        "account": boundaries.get("account", ""),
        "a1_only": bool(boundaries.get("a1_only", False)),
        "a2_touched": bool(boundaries.get("a2_touched", True)),
        "a3_touched": bool(boundaries.get("a3_touched", True)),
        "existing_920101_chart_edited": bool(boundaries.get("existing_920101_chart_edited", True)),
        "broker_action_enabled_for_new_lane": bool(boundaries.get("broker_action_enabled_for_new_lane", False)),
        "spec_sha256": boundaries.get("spec_sha256", ""),
        "evidence_status": "SELECTED_ON_ALL_AVAILABLE_HISTORY_FORWARD_IS_FIRST_CLEAN_TEST",
        "forward_start_broker": "2026-07-02 04:46:42",
        "expected_100_trade_duration": "18-25 weeks",
        "expected_loss_streak": "8-10 trades is normal for this low-WR tail-capture lane",
        "kill_switch_file": "a1_xau_m5_momentum_rr2_kill_switch.txt",
        "attribution_report": "xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_RR2_ATTRIBUTION_EXPORT_2026_07_02.md",
        "shadow_counterfactual_report": "xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_RR2_SHADOW_COUNTERFACTUAL_2026_07_02.md",
        "ea": ea.get("name", ""),
        "symbol": ea.get("symbol", ""),
        "magic": str(ea.get("magic", "")),
        "lot": str(ea.get("lot", "")),
        "run_id": ea.get("run_id", ""),
        "order_comment": ea.get("order_comment", ""),
        "chart": ea.get("chart", ""),
        "compile_log": ea.get("compile_log", ""),
        "startup_log": ea.get("startup_log", ""),
        "signal_log": ea.get("signal_log", ""),
        "order_log": ea.get("order_log", ""),
        "profile_backup_path": terminal.get("profile_backup_dir", ""),
        "startup_rows_seen": max(0, len(startup_tail) - 1),
        "signal_rows_seen": max(0, len(signal_tail) - 1),
        "order_rows_seen": len(order_tail),
        "first_order_status": "PENDING_FIRST_ORDER_OR_GUARD_ROW" if not order_tail else "ORDER_OR_GUARD_ROW_PRESENT",
        "mt5_backtest": {
            "status": "FAIL_STANDALONE_BACKTEST" if backtest_overall else "MISSING",
            "report": _rel(repo_root, backtest_md_path) if backtest_md_path else "",
            "json": _rel(repo_root, backtest_json_path) if backtest_json_path else "",
            "period": "2026.06.01 -> 2026.06.30",
            "net_profit_aed": backtest_overall.get("pnl_aed"),
            "profit_factor": backtest_overall.get("profit_factor"),
            "win_rate_pct": backtest_overall.get("win_rate_pct"),
            "trades": backtest_overall.get("trades"),
            "short_net_profit_aed": backtest_direction.get("SHORT", {}).get("pnl_aed"),
            "long_net_profit_aed": backtest_direction.get("LONG", {}).get("pnl_aed"),
            "decision": "baseline_failed; research short-only/stricter-long variants offline",
        },
        "variant_mt5_backtest": {
            "status": variant_winner.get("status", "MISSING") if variant_backtest else "MISSING",
            "report": _rel(repo_root, variant_backtest_md_path) if variant_backtest_md_path else "",
            "json": _rel(repo_root, variant_backtest_json_path) if variant_backtest_json_path else "",
            "best_variant": variant_winner.get("best_by_pf", variant_winner.get("best_by_pnl", "")),
            "variant_count": variant_backtest.get("scope", {}).get("variant_count"),
            "note": variant_winner.get("note", ""),
            "diagnosis_report": _rel(repo_root, variant_diagnosis_md_path) if variant_diagnosis_md_path else "",
        },
        "frequency_first_repair": {
            "status": frequency_repair.get("status", "MISSING") if frequency_repair else "MISSING",
            "report": _rel(repo_root, frequency_repair_md_path) if frequency_repair_md_path else "",
            "json": _rel(repo_root, frequency_repair_json_path) if frequency_repair_json_path else "",
            "trades": frequency_repaired.get("trades"),
            "win_rate_pct": frequency_repaired.get("win_rate_pct"),
            "net_profit_usd": frequency_repaired.get("pnl_aed"),
            "profit_factor": frequency_repaired.get("profit_factor"),
            "avg_usd_per_trade": frequency_repaired.get("avg_pnl_aed"),
            "meets_frequency_goal": frequency_repair_decision.get("meets_frequency_goal"),
            "meets_winrate_goal": frequency_repair_decision.get("meets_winrate_goal"),
            "ready_for_live": frequency_repair_decision.get("ready_for_live"),
            "next_action": frequency_repair_decision.get("next_action", ""),
        },
        "frequency_first_replacement": {
            "status": "READY_FOR_REVIEW_NOT_ATTACHED" if frequency_replacement_ready else "MISSING_OR_NOT_READY",
            "readiness_doc": _rel(repo_root, frequency_replacement_readiness_path)
            if frequency_replacement_readiness_path
            else "",
            "v6_diagnostic_doc": _rel(repo_root, frequency_v6_diagnostic_path)
            if frequency_v6_diagnostic_path
            else "",
            "frequency_requirement_verdict": _rel(repo_root, frequency_requirement_verdict_path)
            if frequency_requirement_verdict_path
            else "",
            "candidate": "freq_h1_h4_long_rr0p7_v4_combo_rank1",
            "replace_or_stack": "replace_sparse_rr2_by_default",
            "currently_attached_lane": ea.get("run_id", ""),
            "currently_attached_business_fit": "TOO_SPARSE_FOR_PRIMARY_GOAL",
            "runtime_touched": False,
            "review_required": True,
            "owner_approval_required": True,
            "attach_command_after_approval": (
                "python xau-usd/xauusd-phase1/scripts/attach_a1_xau_m5_momentum_continuation.py "
                "--variant freq_v4"
            ),
            "expected_forward_contract": {
                "account": "1025742",
                "symbol": "XAUUSD",
                "timeframe": "M5",
                "magic": "932200",
                "lot": "0.01",
                "run_id": "A1_XAU_M5_MOMENTUM_FREQ_FIRST_V4_COMBO_RANK1_20260702",
                "direction": "LONG_ONLY",
                "risk_reward": "0.70",
                "max_estimated_cost_r": "0.05",
                "blocked_entry_hours": "2,9,10,11,12,13,17,19,21,23",
                "max_trades_per_day": "12",
                "cooldown_minutes": "5",
            },
        },
        "split_entry_be_tp1_forward": {
            "status": "PASS_ATTACHED" if len(split_reports) == 3 else "INCOMPLETE_OR_MISSING",
            "account": "1025742 / Capital.ComMena-Demo",
            "symbol": "XAUUSD",
            "timeframe": "M5",
            "magic": "932280",
            "component_count": len(split_reports),
            "components": split_reports,
            "owner_authorization": (
                "xau-usd/xauusd-phase1/docs/"
                "A1_XAU_M5_MOMENTUM_SPLIT_ENTRY_BE_TP1_OWNER_AUTHORIZATION_2026_07_03.md"
            ),
            "frozen_spec": (
                "xau-usd/xauusd-phase1/docs/"
                "A1_XAU_M5_MOMENTUM_SPLIT_ENTRY_BE_TP1_FORWARD_V0_2026_07_03.md"
            ),
            "hash_verification": (
                "xau-usd/xauusd-phase1/docs/"
                "A1_XAU_M5_MOMENTUM_SPLIT_BE_HASH_VERIFICATION_2026_07_03.md"
            ),
            "exposure_note": "Owner accepted 2 x 0.01 split-entry exposure; typical failed signal -20 to -30 USD, worst tested about -36 USD.",
            "boundary": "A1 demo only; no live trading, no real capital, no canonical Phase 2 approval.",
            "first_order_status": "PENDING_FIRST_VALID_SIGNAL",
        },
        "portfolio_combination_candidate": {
            "status": portfolio_diagnostic.get("status", "MISSING") if portfolio_diagnostic else "MISSING",
            "report": _rel(repo_root, portfolio_diagnostic_md_path) if portfolio_diagnostic_md_path else "",
            "json": _rel(repo_root, portfolio_diagnostic_json_path) if portfolio_diagnostic_json_path else "",
            "candidate": portfolio_candidate.get("name", ""),
            "decision": portfolio_candidate.get("decision", ""),
            "trades": portfolio_candidate.get("trades"),
            "win_rate_pct": portfolio_candidate.get("win_rate_pct"),
            "net_usd": portfolio_candidate.get("net_usd"),
            "profit_factor": portfolio_candidate.get("profit_factor"),
            "active_days": portfolio_candidate.get("active_days"),
            "trades_per_active_day": portfolio_candidate.get("trades_per_active_day"),
            "multi_trade_days": portfolio_candidate.get("multi_trade_days"),
            "positive_months": portfolio_candidate.get("positive_months"),
            "negative_months": portfolio_candidate.get("negative_months"),
            "max_closed_drawdown_usd": portfolio_candidate.get("max_closed_drawdown_usd"),
            "recommendation": "review_before_demo; possible V4 primary plus V13 companion forward-test",
            "forward_draft": _rel(repo_root, portfolio_forward_draft_path) if portfolio_forward_draft_path else "",
        },
        "broad_portfolio_search": {
            "status": broad_portfolio.get("status", "MISSING") if broad_portfolio else "MISSING",
            "report": _rel(repo_root, broad_portfolio_md_path) if broad_portfolio_md_path else "",
            "json": _rel(repo_root, broad_portfolio_json_path) if broad_portfolio_json_path else "",
            "verdict": _rel(repo_root, broad_portfolio_verdict_path) if broad_portfolio_verdict_path else "",
            "clean_forward_draft": _rel(repo_root, clean_portfolio_forward_draft_path)
            if clean_portfolio_forward_draft_path
            else "",
            "headline_candidate": headline_broad_candidate,
            "best_clean_candidate": clean_broad_candidate,
            "recommendation": "review best clean no-duplicate candidate before any demo attachment",
        },
        "deep_portfolio_search": {
            "status": deep_portfolio.get("status", "MISSING") if deep_portfolio else "MISSING",
            "report": _rel(repo_root, deep_portfolio_md_path) if deep_portfolio_md_path else "",
            "json": _rel(repo_root, deep_portfolio_json_path) if deep_portfolio_json_path else "",
            "stress_status": deep_portfolio_stress.get("status", "MISSING")
            if deep_portfolio_stress
            else "MISSING",
            "stress_verdict": deep_portfolio_stress.get("verdict", ""),
            "stress_report": _rel(repo_root, deep_portfolio_stress_md_path)
            if deep_portfolio_stress_md_path
            else "",
            "stress_json": _rel(repo_root, deep_portfolio_stress_json_path)
            if deep_portfolio_stress_json_path
            else "",
            "verdict": _rel(repo_root, deep_portfolio_verdict_path) if deep_portfolio_verdict_path else "",
            "forward_draft": _rel(repo_root, deep_portfolio_forward_draft_path)
            if deep_portfolio_forward_draft_path
            else "",
            "headline_candidate": headline_deep_candidate,
            "best_low_overlap_frequency_candidate": low_overlap_deep_candidate,
            "recommendation": "review low-overlap frequency portfolio as the next primary candidate; sparse RR2 remains too sparse",
        },
        "robust_portfolio_search": {
            "status": robust_portfolio.get("status", "MISSING") if robust_portfolio else "MISSING",
            "report": _rel(repo_root, robust_portfolio_md_path) if robust_portfolio_md_path else "",
            "json": _rel(repo_root, robust_portfolio_json_path) if robust_portfolio_json_path else "",
            "stress_status": robust_portfolio_stress.get("status", "MISSING")
            if robust_portfolio_stress
            else "MISSING",
            "stress_verdict": robust_portfolio_stress.get("verdict", ""),
            "stress_report": _rel(repo_root, robust_portfolio_stress_md_path)
            if robust_portfolio_stress_md_path
            else "",
            "stress_json": _rel(repo_root, robust_portfolio_stress_json_path)
            if robust_portfolio_stress_json_path
            else "",
            "forward_draft": _rel(repo_root, robust_portfolio_forward_draft_path)
            if robust_portfolio_forward_draft_path
            else "",
            "walkforward_status": robust_portfolio_walkforward.get("status", "MISSING")
            if robust_portfolio_walkforward
            else "MISSING",
            "walkforward_verdict": robust_portfolio_walkforward.get("verdict", ""),
            "walkforward_report": _rel(repo_root, robust_portfolio_walkforward_md_path)
            if robust_portfolio_walkforward_md_path
            else "",
            "walkforward_json": _rel(repo_root, robust_portfolio_walkforward_json_path)
            if robust_portfolio_walkforward_json_path
            else "",
            "weakest_half_year": weakest_robust_half_year,
            "repair_status": robust_portfolio_repair.get("status", "MISSING")
            if robust_portfolio_repair
            else "MISSING",
            "repair_report": _rel(repo_root, robust_portfolio_repair_md_path)
            if robust_portfolio_repair_md_path
            else "",
            "repair_json": _rel(repo_root, robust_portfolio_repair_json_path)
            if robust_portfolio_repair_json_path
            else "",
            "repair_walkforward_status": robust_repair_walkforward.get("status", "MISSING")
            if robust_repair_walkforward
            else "MISSING",
            "repair_walkforward_verdict": robust_repair_walkforward.get("verdict", ""),
            "repair_walkforward_report": _rel(repo_root, robust_repair_walkforward_md_path)
            if robust_repair_walkforward_md_path
            else "",
            "repair_walkforward_json": _rel(repo_root, robust_repair_walkforward_json_path)
            if robust_repair_walkforward_json_path
            else "",
            "repair_weakest_half_year": weakest_robust_repair_half_year,
            "repair_forward_draft": _rel(repo_root, robust_repair_forward_draft_path)
            if robust_repair_forward_draft_path
            else "",
            "best_repair_candidate": robust_repair_best,
            "best_candidate": headline_robust_candidate,
            "recommendation": "strongest current fit for active intraday frequency plus split-period robustness; review before any demo attachment",
        },
        "daily_fit_portfolio_search": {
            "status": daily_fit.get("status", "MISSING") if daily_fit else "MISSING",
            "report": _rel(repo_root, daily_fit_md_path) if daily_fit_md_path else "",
            "json": _rel(repo_root, daily_fit_json_path) if daily_fit_json_path else "",
            "forward_draft": _rel(repo_root, daily_fit_forward_draft_path)
            if daily_fit_forward_draft_path
            else "",
            "stress_status": daily_fit_stress.get("status", "MISSING")
            if daily_fit_stress
            else "MISSING",
            "stress_report": _rel(repo_root, daily_fit_stress_md_path)
            if daily_fit_stress_md_path
            else "",
            "stress_json": _rel(repo_root, daily_fit_stress_json_path)
            if daily_fit_stress_json_path
            else "",
            "stress_candidate": daily_fit_stress_candidate,
            "repair_status": daily_fit_repair.get("status", "MISSING")
            if daily_fit_repair
            else "MISSING",
            "repair_report": _rel(repo_root, daily_fit_repair_md_path)
            if daily_fit_repair_md_path
            else "",
            "repair_json": _rel(repo_root, daily_fit_repair_json_path)
            if daily_fit_repair_json_path
            else "",
            "repair_forward_draft": _rel(repo_root, daily_fit_repair_forward_draft_path)
            if daily_fit_repair_forward_draft_path
            else "",
            "best_repair_candidate": headline_daily_fit_repair,
            "pool_size": daily_fit.get("pool_size"),
            "searched_portfolios": daily_fit.get("searched_portfolios"),
            "best_candidate": headline_daily_fit_candidate,
            "recommendation": "best current candidate for the owner's daily-activity target; repair candidate improves PF/DD/month stability but needs review before demo attachment",
        },
        "daily_guard_search": {
            "status": daily_guard.get("status", "MISSING") if daily_guard else "MISSING",
            "report": _rel(repo_root, daily_guard_md_path) if daily_guard_md_path else "",
            "json": _rel(repo_root, daily_guard_json_path) if daily_guard_json_path else "",
            "forward_draft": _rel(repo_root, daily_guard_forward_draft_path)
            if daily_guard_forward_draft_path
            else "",
            "best_candidate": headline_daily_guard,
            "grid": daily_guard.get("grid", {}),
            "base_blocks": daily_guard.get("bases", {}),
            "recommendation": (
                "review the repaired daily-fit package with a shared portfolio guard: "
                "max 6 trades/day, -25 USD daily loss stop, no profit target; preserves "
                "3+ trades/active-day cadence while improving positive-day rate and drawdown"
            ),
        },
        "pocket_portfolio_search": {
            "status": pocket_portfolio.get("status", "MISSING") if pocket_portfolio else "MISSING",
            "report": _rel(repo_root, pocket_portfolio_md_path) if pocket_portfolio_md_path else "",
            "json": _rel(repo_root, pocket_portfolio_json_path) if pocket_portfolio_json_path else "",
            "csv": _rel(repo_root, pocket_portfolio_csv_path) if pocket_portfolio_csv_path else "",
            "variant_count": pocket_portfolio.get("variant_count"),
            "pocket_count": pocket_portfolio.get("pocket_count"),
            "searched_combo_count": pocket_portfolio.get("searched_combo_count"),
            "guarded_candidate_count": pocket_portfolio.get("guarded_candidate_count"),
            "best_candidate": headline_pocket_candidate,
            "non_sample_fail_count": pocket_non_sample_fail_count,
            "recommendation": (
                "do not pivot to sparse pocket pruning; the cleanest pockets failed the sample/frequency "
                "gate, so the daily-guard portfolio remains the current best frequent-trade candidate"
            ),
        },
        "daily_state_guard_search": {
            "status": daily_state_guard.get("status", "MISSING") if daily_state_guard else "MISSING",
            "report": _rel(repo_root, daily_state_guard_md_path) if daily_state_guard_md_path else "",
            "json": _rel(repo_root, daily_state_guard_json_path) if daily_state_guard_json_path else "",
            "csv": _rel(repo_root, daily_state_guard_csv_path) if daily_state_guard_csv_path else "",
            "searched_rules": daily_state_guard.get("searched_rules"),
            "base_summary": daily_state_guard.get("base_summary", {}),
            "best_candidate": headline_daily_state_guard,
            "review_candidate_count": daily_state_guard_review_count,
            "recommendation": (
                "daily-state lifecycle rules did not cross the daily-income bar; the best result remains "
                "the existing daily guard shape, so the next improvement probably needs a better entry "
                "or feature filter rather than more day-stop pruning"
            ),
        },
        "feature_loss_cluster_analysis": {
            "status": feature_loss.get("status", "MISSING") if feature_loss else "MISSING",
            "implementation_status": "CODED_DEFAULT_OFF_MT5_BACKTEST_VARIANT_READY",
            "report": _rel(repo_root, feature_loss_md_path) if feature_loss_md_path else "",
            "json": _rel(repo_root, feature_loss_json_path) if feature_loss_json_path else "",
            "filter_csv": _rel(repo_root, feature_loss_filter_csv_path) if feature_loss_filter_csv_path else "",
            "bin_csv": _rel(repo_root, feature_loss_bin_csv_path) if feature_loss_bin_csv_path else "",
            "raw_trade_count": feature_loss.get("raw_trade_count"),
            "enriched_trade_count": feature_loss.get("enriched_trade_count"),
            "enriched_trade_pct": feature_loss.get("enriched_trade_pct"),
            "base_guarded_summary": feature_loss.get("base_guarded_summary", {}),
            "best_filter": headline_feature_loss_filter,
            "feature_filter_review_candidate_count": feature_loss_review_count,
            "recommendation": (
                "the top single-feature filter is now coded default-off in "
                "A1XauM5MomentumContinuationExecutor and exposed as an MT5 tester variant: block SHORT "
                "entries where close_to_recent_extreme >= -0.75, then replay the daily guard; offline "
                "analysis preserved 3+ trades/active-day cadence and lifted positive active days to about "
                "57.5%. Next required proof is an exact MT5 real-tick backtest before any demo attachment."
            ),
        },
        "feature_loss_portfolio_verdict": {
            "status": feature_loss_portfolio.get("status", "MISSING") if feature_loss_portfolio else "MISSING",
            "report": _rel(repo_root, feature_loss_portfolio_md_path) if feature_loss_portfolio_md_path else "",
            "json": _rel(repo_root, feature_loss_portfolio_json_path) if feature_loss_portfolio_json_path else "",
            "best_frequency_first_candidate": feature_loss_portfolio_best_name,
            "best_summary": headline_feature_loss_portfolio,
            "recommendation": (
                "feature-filtered V13 plus the existing weak-hour long lane is the best current "
                "frequency-preserving repair shape from exact MT5 CSV evidence: it improves WR/PF and "
                "positive-day rate versus the old V13 daily-guard portfolio while keeping more than "
                "3 trades per active day. It remains review-ready, not promoted."
            ),
        },
        "feature_loss_daily_guard_optimizer": {
            "status": feature_loss_guard_optimizer.get("status", "MISSING") if feature_loss_guard_optimizer else "MISSING",
            "report": _rel(repo_root, feature_loss_guard_optimizer_md_path) if feature_loss_guard_optimizer_md_path else "",
            "json": _rel(repo_root, feature_loss_guard_optimizer_json_path) if feature_loss_guard_optimizer_json_path else "",
            "csv": _rel(repo_root, feature_loss_guard_optimizer_csv_path) if feature_loss_guard_optimizer_csv_path else "",
            "searched_rows": feature_loss_guard_optimizer.get("searched_rows"),
            "best_summary": headline_feature_loss_guard_optimizer,
            "recommendation": (
                "daily-control optimization around the feature-loss portfolio now selects the exact "
                "MT5-backed feature-band package as the best frequency-first candidate. The selected "
                "row must be read from the guard fields because the current best uses no shared daily "
                "portfolio guard. It remains review-ready, not promoted."
            ),
        },
        "feature_pair_filter_search": {
            "status": feature_pair_filter.get("status", "MISSING") if feature_pair_filter else "MISSING",
            "report": _rel(repo_root, feature_pair_filter_md_path) if feature_pair_filter_md_path else "",
            "json": _rel(repo_root, feature_pair_filter_json_path) if feature_pair_filter_json_path else "",
            "csv": _rel(repo_root, feature_pair_filter_csv_path) if feature_pair_filter_csv_path else "",
            "review_candidate_count": feature_pair_filter.get("review_candidate_count"),
            "base_summary": feature_pair_filter.get("base_summary", {}),
            "best_summary": headline_feature_pair_filter,
            "recommendation": (
                "feature-pair search found one more frequency-preserving repair candidate: block SHORT "
                "entries where close_to_recent_extreme <= -2.51 in addition to the existing >= -0.75 "
                "feature-loss block. It still keeps about 3.27 trades per active day and slightly improves "
                "positive-day rate. Next proof is exact MT5 real-tick testing of the new default-off band "
                "variant before any demo attachment."
            ),
        },
        "feature_band_daily_income_tradeoff": {
            "status": feature_band_daily_income.get("status", "MISSING") if feature_band_daily_income else "MISSING",
            "report": _rel(repo_root, feature_band_daily_income_md_path)
            if feature_band_daily_income_md_path
            else "",
            "json": _rel(repo_root, feature_band_daily_income_json_path)
            if feature_band_daily_income_json_path
            else "",
            "csv": _rel(repo_root, feature_band_daily_income_csv_path)
            if feature_band_daily_income_csv_path
            else "",
            "forward_draft": _rel(repo_root, feature_band_daily_income_forward_draft_path)
            if feature_band_daily_income_forward_draft_path
            else "",
            "eligible_count": feature_band_daily_income.get("eligible_count"),
            "max_net": feature_band_daily_income.get("max_net", {}),
            "owner_target_50_candidate": feature_band_daily_income.get("owner_target_50_candidate", {}),
            "balanced_daily_income_candidate": headline_feature_band_daily_income,
            "recommendation": (
                "daily-income tradeoff report separates the max-net feature-band package from the "
                "owner-target +50 USD / max 6 trades package, while also preserving the smoother "
                "+25 USD fallback for reviewer comparison. Review both before runtime selection "
                "because the daily-income versions improve positive active-day rate while giving up "
                "some total historical net."
            ),
        },
        "feature_band_daily_income_readiness": {
            "status": feature_band_daily_income_readiness.get("status", "MISSING")
            if feature_band_daily_income_readiness
            else "MISSING",
            "report": _rel(repo_root, feature_band_daily_income_readiness_md_path)
            if feature_band_daily_income_readiness_md_path
            else "",
            "json": _rel(repo_root, feature_band_daily_income_readiness_json_path)
            if feature_band_daily_income_readiness_json_path
            else "",
            "draft_sha256": feature_band_daily_income_readiness.get("draft_sha256", ""),
            "decision": feature_band_daily_income_readiness.get("decision", ""),
            "planned_variants": feature_band_daily_income_readiness.get("planned_variants", {}),
        },
        "feature_band_day_state_search": {
            "status": feature_band_day_state.get("status", "MISSING") if feature_band_day_state else "MISSING",
            "report": _rel(repo_root, feature_band_day_state_md_path) if feature_band_day_state_md_path else "",
            "json": _rel(repo_root, feature_band_day_state_json_path) if feature_band_day_state_json_path else "",
            "csv": _rel(repo_root, feature_band_day_state_csv_path) if feature_band_day_state_csv_path else "",
            "best": feature_band_day_state.get("best", {}) if feature_band_day_state else {},
            "recommendation": (
                "daily-state search promotes the +50/max6 feature-band package with a 15-minute "
                "package cooldown after any losing package trade. It keeps more than 3 trades per "
                "active day while improving win rate, PF, net, positive-day rate, drawdown, and "
                "top-100 robustness versus the plain +50/max6 package."
            ),
        },
        "feature_band_daily_reliability_readiness": {
            "status": feature_band_daily_reliability_readiness.get("status", "MISSING")
            if feature_band_daily_reliability_readiness
            else "MISSING",
            "report": _rel(repo_root, feature_band_daily_reliability_readiness_md_path)
            if feature_band_daily_reliability_readiness_md_path
            else "",
            "json": _rel(repo_root, feature_band_daily_reliability_readiness_json_path)
            if feature_band_daily_reliability_readiness_json_path
            else "",
            "forward_draft": _rel(repo_root, feature_band_daily_reliability_forward_draft_path)
            if feature_band_daily_reliability_forward_draft_path
            else "",
            "draft_sha256": feature_band_daily_reliability_readiness.get("draft_sha256", ""),
            "decision": feature_band_daily_reliability_readiness.get("decision", ""),
            "planned_variants": feature_band_daily_reliability_readiness.get("planned_variants", {}),
        },
        "feature_band_residual_search": {
            "status": feature_band_residual.get("status", "MISSING") if feature_band_residual else "MISSING",
            "report": _rel(repo_root, feature_band_residual_md_path) if feature_band_residual_md_path else "",
            "json": _rel(repo_root, feature_band_residual_json_path) if feature_band_residual_json_path else "",
            "csv": _rel(repo_root, feature_band_residual_csv_path) if feature_band_residual_csv_path else "",
            "baseline": feature_band_residual.get("baseline", {}) if feature_band_residual else {},
            "best": feature_band_residual.get("best", {}) if feature_band_residual else {},
            "recommendation": (
                "residual reliability search keeps the frequent +50/max6/15m-cooldown package and tests "
                "small residual filters. Current best blocks LONG server hour 18 and tightens the SHORT "
                "close-to-recent-extreme min block to -0.92, improving positive active days while keeping "
                "more than 3 trades per active day."
            ),
        },
        "feature_band_residual_stress": {
            "status": feature_band_residual_stress.get("status", "MISSING")
            if feature_band_residual_stress
            else "MISSING",
            "report": _rel(repo_root, feature_band_residual_stress_md_path)
            if feature_band_residual_stress_md_path
            else "",
            "json": _rel(repo_root, feature_band_residual_stress_json_path)
            if feature_band_residual_stress_json_path
            else "",
            "csv": _rel(repo_root, feature_band_residual_stress_csv_path)
            if feature_band_residual_stress_csv_path
            else "",
            "business_requirement": feature_band_residual_stress.get("business_requirement", {}),
            "residual": feature_band_residual_stress.get("residual", {}),
            "blocked": feature_band_residual_stress.get("blocked", {}),
            "recommendation": (
                "stress testing makes the owner's cadence rule explicit: sparse systems fail even when "
                "profitable. The residual candidate remains review-ready only because it keeps about "
                "3.19 trades per active day, has no negative half-year bucket, and has no negative "
                "rolling 250-trade window."
            ),
        },
        "feature_band_residual_package_optimizer": {
            "status": feature_band_residual_package_optimizer.get("status", "MISSING")
            if feature_band_residual_package_optimizer
            else "MISSING",
            "report": _rel(repo_root, feature_band_residual_package_optimizer_md_path)
            if feature_band_residual_package_optimizer_md_path
            else "",
            "json": _rel(repo_root, feature_band_residual_package_optimizer_json_path)
            if feature_band_residual_package_optimizer_json_path
            else "",
            "csv": _rel(repo_root, feature_band_residual_package_optimizer_csv_path)
            if feature_band_residual_package_optimizer_csv_path
            else "",
            "searched_rows": feature_band_residual_package_optimizer.get("searched_rows"),
            "best": feature_band_residual_package_optimizer.get("best", {}),
            "named_candidates": feature_band_residual_package_optimizer.get("named_candidates", {}),
            "recommendation": (
                "package optimizer searches daily target/cap/cooldown/loss-control permutations on the "
                "same residual-filtered signal base while preserving the sparse-strategy veto. It shows "
                "a trade-off: +75/no-trade-cap style rows maximize net, while the best +50 target row "
                "keeps the owner's target and improves on the prior 15-minute cooldown by using a "
                "10-minute cooldown after loss."
            ),
        },
        "feature_band_residual_plus50_cooldown10_readiness": {
            "status": feature_band_residual_plus50_cooldown10_readiness.get("status", "MISSING")
            if feature_band_residual_plus50_cooldown10_readiness
            else "MISSING",
            "report": _rel(repo_root, feature_band_residual_plus50_cooldown10_readiness_md_path)
            if feature_band_residual_plus50_cooldown10_readiness_md_path
            else "",
            "json": _rel(repo_root, feature_band_residual_plus50_cooldown10_readiness_json_path)
            if feature_band_residual_plus50_cooldown10_readiness_json_path
            else "",
            "forward_draft": _rel(repo_root, feature_band_residual_plus50_cooldown10_forward_draft_path)
            if feature_band_residual_plus50_cooldown10_forward_draft_path
            else "",
            "draft_sha256": feature_band_residual_plus50_cooldown10_readiness.get("draft_sha256", ""),
            "decision": feature_band_residual_plus50_cooldown10_readiness.get("decision", ""),
            "candidate": feature_band_residual_plus50_cooldown10_readiness.get("candidate", {}),
            "planned_variants": feature_band_residual_plus50_cooldown10_readiness.get("planned_variants", {}),
            "recommendation": (
                "this is the preferred owner-target package to send for review if the goal is to keep "
                "+50 USD target, max 6 trades/day, and frequent intraday cadence while improving the "
                "cooldown-after-loss from 15 minutes to 10 minutes."
            ),
        },
        "feature_band_residual_plus75_high_net_readiness": {
            "status": feature_band_residual_plus75_high_net_readiness.get("status", "MISSING")
            if feature_band_residual_plus75_high_net_readiness
            else "MISSING",
            "report": _rel(repo_root, feature_band_residual_plus75_high_net_readiness_md_path)
            if feature_band_residual_plus75_high_net_readiness_md_path
            else "",
            "json": _rel(repo_root, feature_band_residual_plus75_high_net_readiness_json_path)
            if feature_band_residual_plus75_high_net_readiness_json_path
            else "",
            "forward_draft": _rel(repo_root, feature_band_residual_plus75_high_net_forward_draft_path)
            if feature_band_residual_plus75_high_net_forward_draft_path
            else "",
            "draft_sha256": feature_band_residual_plus75_high_net_readiness.get("draft_sha256", ""),
            "decision": feature_band_residual_plus75_high_net_readiness.get("decision", ""),
            "candidate": feature_band_residual_plus75_high_net_readiness.get("candidate", {}),
            "planned_variants": feature_band_residual_plus75_high_net_readiness.get("planned_variants", {}),
            "recommendation": (
                "this is the higher-net, higher-cadence alternative. It removes the shared max-trade cap "
                "and uses a +75 USD target, so it needs explicit owner/reviewer choice because its "
                "positive active-day rate is lower than the +50/10m package."
            ),
        },
        "business_goal_scoreboard": {
            "status": business_goal_scoreboard.get("status", "MISSING") if business_goal_scoreboard else "MISSING",
            "report": _rel(repo_root, business_goal_scoreboard_md_path) if business_goal_scoreboard_md_path else "",
            "json": _rel(repo_root, business_goal_scoreboard_json_path) if business_goal_scoreboard_json_path else "",
            "csv": _rel(repo_root, business_goal_scoreboard_csv_path) if business_goal_scoreboard_csv_path else "",
            "top_candidate": business_goal_scoreboard.get("rows", [{}])[0]
            if business_goal_scoreboard.get("rows")
            else {},
            "passing_candidates": [
                row
                for row in business_goal_scoreboard.get("rows", [])
                if str(row.get("owner_goal_status", "")).startswith("OWNER_GOAL_PASS")
            ],
            "recommendation": (
                "rank candidates by the owner's frequent-intraday objective; sparse RR2-style systems "
                "are deliberately demoted even when their PF looks attractive."
            ),
        },
        "business_goal_promotion_packet": {
            "status": business_goal_promotion_packet.get("status", "MISSING")
            if business_goal_promotion_packet
            else "MISSING",
            "report": _rel(repo_root, business_goal_promotion_packet_md_path)
            if business_goal_promotion_packet_md_path
            else "",
            "json": _rel(repo_root, business_goal_promotion_packet_json_path)
            if business_goal_promotion_packet_json_path
            else "",
            "recommended_primary": business_goal_promotion_packet.get("recommended_primary", ""),
            "recommended_fallback": business_goal_promotion_packet.get("recommended_fallback", ""),
            "forward_demo_rules": business_goal_promotion_packet.get("forward_demo_rules", {}),
            "checks": business_goal_promotion_packet.get("checks", []),
            "decision": business_goal_promotion_packet.get("decision", ""),
            "recommendation": (
                "reviewer/owner approval packet for replacing the sparse RR2 lane with the best "
                "frequent intraday candidate at minimum demo lot."
            ),
        },
        "business_goal_calendar_cadence_audit": {
            "status": business_goal_calendar_cadence_audit.get("status", "MISSING")
            if business_goal_calendar_cadence_audit
            else "MISSING",
            "report": _rel(repo_root, business_goal_calendar_cadence_audit_md_path)
            if business_goal_calendar_cadence_audit_md_path
            else "",
            "json": _rel(repo_root, business_goal_calendar_cadence_audit_json_path)
            if business_goal_calendar_cadence_audit_json_path
            else "",
            "date_window": business_goal_calendar_cadence_audit.get("date_window", {}),
            "candidates": business_goal_calendar_cadence_audit.get("candidates", []),
            "recommendation": (
                "calendar-day cadence audit for the owner goal. It prevents overclaiming: the current "
                "packages are frequent on active days, but quiet market days still exist."
            ),
        },
        "business_goal_market_day_coverage_search": {
            "status": business_goal_market_day_coverage_search.get("status", "MISSING")
            if business_goal_market_day_coverage_search
            else "MISSING",
            "report": _rel(repo_root, business_goal_market_day_coverage_search_md_path)
            if business_goal_market_day_coverage_search_md_path
            else "",
            "json": _rel(repo_root, business_goal_market_day_coverage_search_json_path)
            if business_goal_market_day_coverage_search_json_path
            else "",
            "csv": _rel(repo_root, business_goal_market_day_coverage_search_csv_path)
            if business_goal_market_day_coverage_search_csv_path
            else "",
            "best_result": business_goal_market_day_coverage_search.get("best_result", {}),
            "reviewable_result_count": business_goal_market_day_coverage_search.get("reviewable_result_count", 0),
            "recommendation": (
                "deduped portfolio search for the owner's market-day cadence target. It looks for "
                "multi-lane momentum packages that keep WR/PF positive while producing multiple trades "
                "per weekday market day."
            ),
        },
        "business_goal_market_day_coverage_stress": {
            "status": business_goal_market_day_coverage_stress.get("status", "MISSING")
            if business_goal_market_day_coverage_stress
            else "MISSING",
            "report": _rel(repo_root, business_goal_market_day_coverage_stress_md_path)
            if business_goal_market_day_coverage_stress_md_path
            else "",
            "json": _rel(repo_root, business_goal_market_day_coverage_stress_json_path)
            if business_goal_market_day_coverage_stress_json_path
            else "",
            "selected_trades_csv": _rel(repo_root, business_goal_market_day_coverage_stress_csv_path)
            if business_goal_market_day_coverage_stress_csv_path
            else "",
            "decision": business_goal_market_day_coverage_stress.get("decision", ""),
            "summary": business_goal_market_day_coverage_stress.get("summary", {}),
            "rolling": business_goal_market_day_coverage_stress.get("rolling", []),
            "ablations": business_goal_market_day_coverage_stress.get("ablations", []),
            "recommendation": (
                "stress report for the market-day coverage portfolio. It checks half-year/quarter "
                "stability, rolling windows, large-winner removal, source contribution, and source "
                "ablation before any reviewer/owner decision."
            ),
        },
        "feature_band_residual_reliability_readiness": {
            "status": feature_band_residual_reliability_readiness.get("status", "MISSING")
            if feature_band_residual_reliability_readiness
            else "MISSING",
            "report": _rel(repo_root, feature_band_residual_reliability_readiness_md_path)
            if feature_band_residual_reliability_readiness_md_path
            else "",
            "json": _rel(repo_root, feature_band_residual_reliability_readiness_json_path)
            if feature_band_residual_reliability_readiness_json_path
            else "",
            "forward_draft": _rel(repo_root, feature_band_residual_reliability_forward_draft_path)
            if feature_band_residual_reliability_forward_draft_path
            else "",
            "draft_sha256": feature_band_residual_reliability_readiness.get("draft_sha256", ""),
            "decision": feature_band_residual_reliability_readiness.get("decision", ""),
            "planned_variants": feature_band_residual_reliability_readiness.get("planned_variants", {}),
        },
    }


def _xau_920101_failure_forensic(
    repo_root: Path,
    report_md_path: Path,
    report_json_path: Path,
    report: dict[str, Any],
) -> dict[str, Any]:
    if not report:
        return {
            "status": "MISSING",
            "report": _rel(repo_root, report_md_path),
            "json": _rel(repo_root, report_json_path),
        }
    variants = report.get("variants", {})
    current = variants.get("current_24h_h1_smart", {})
    evening = variants.get("server_16_19_h1_smart", {})
    cost010 = variants.get("current_24h_h1_cost010", {})
    repair = variants.get("repair_24h_h1_faststop_min800", {})
    profit_protection = variants.get("repair_24h_h1_faststop_min800_lock100_050", {})
    current_overall = current.get("overall", {})
    current_robustness = current.get("robustness", {})
    current_hold = current.get("hold_bucket", {})
    return {
        "status": report.get("status", "UNKNOWN"),
        "report": _rel(repo_root, report_md_path),
        "json": _rel(repo_root, report_json_path),
        "period": report.get("period", ""),
        "current_24h_h1": {
            "trades": current_overall.get("trades"),
            "win_rate_pct": current_overall.get("win_rate_pct"),
            "net_aed": current_overall.get("pnl_aed"),
            "profit_factor": current_overall.get("profit_factor"),
            "top3_removed_aed": current_robustness.get("top3_removed_pnl_aed"),
            "fast_exit_net_aed": current_hold.get("hold_<=15m", {}).get("pnl_aed"),
            "fast_exit_win_rate_pct": current_hold.get("hold_<=15m", {}).get("win_rate_pct"),
        },
        "cost010": {
            "trades": cost010.get("overall", {}).get("trades"),
            "net_aed": cost010.get("overall", {}).get("pnl_aed"),
            "profit_factor": cost010.get("overall", {}).get("profit_factor"),
            "top3_removed_aed": cost010.get("robustness", {}).get("top3_removed_pnl_aed"),
        },
        "server_16_19": {
            "trades": evening.get("overall", {}).get("trades"),
            "win_rate_pct": evening.get("overall", {}).get("win_rate_pct"),
            "net_aed": evening.get("overall", {}).get("pnl_aed"),
            "profit_factor": evening.get("overall", {}).get("profit_factor"),
            "top3_removed_aed": evening.get("robustness", {}).get("top3_removed_pnl_aed"),
        },
        "repair_24h_h1_faststop_min800": {
            "trades": repair.get("overall", {}).get("trades"),
            "win_rate_pct": repair.get("overall", {}).get("win_rate_pct"),
            "net_aed": repair.get("overall", {}).get("pnl_aed"),
            "profit_factor": repair.get("overall", {}).get("profit_factor"),
            "top3_removed_aed": repair.get("robustness", {}).get("top3_removed_pnl_aed"),
        },
        "repair_24h_h1_faststop_min800_lock100_050": {
            "trades": profit_protection.get("overall", {}).get("trades"),
            "win_rate_pct": profit_protection.get("overall", {}).get("win_rate_pct"),
            "net_aed": profit_protection.get("overall", {}).get("pnl_aed"),
            "profit_factor": profit_protection.get("overall", {}).get("profit_factor"),
            "top3_removed_aed": profit_protection.get("robustness", {}).get("top3_removed_pnl_aed"),
        },
        "finding": "Entry quality remains weak; fast-stop losses and top-winner dependence are the main repair targets.",
    }


def _protected_breakout_runtime_charts(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for row in rows:
        if (
            row.get("expert") == "Phase2ExperimentalDemoExecutor"
            and row.get("symbol") == "XAUUSD"
            and row.get("InpCandidate") == "breakout_retest"
            and row.get("derived_magic") == "920101"
            and row.get("broker_action_state") == "BROKER_ACTION_ENABLED"
            and row.get("InpAllowedAccountLoginsCsv") in {"1025742", "1033030"}
            and row.get("InpTradeSessionStartHour") == "0"
            and row.get("InpTradeSessionEndHour") == "23"
        ):
            output.append(
                {
                    "chart": f"{row.get('lane', '')} {row.get('chart', '')}".strip(),
                    "symbol": row.get("symbol", ""),
                    "candidate": row.get("InpCandidate", ""),
                    "dry_run": row.get("InpDryRunOnly", "").lower(),
                    "broker_action_allowed": row.get("InpBrokerActionAllowed", "").lower(),
                    "candidate_status": row.get("broker_action_state", ""),
                    "account": row.get("InpAllowedAccountLoginsCsv", ""),
                    "derived_magic": row.get("derived_magic", ""),
                    "session": f"{row.get('InpTradeSessionStartHour', '')}->{row.get('InpTradeSessionEndHour', '')}",
                    "smart_trend": (
                        f"enabled={row.get('InpSmartTrendFilterEnabled', '')} "
                        f"shadow={row.get('InpSmartTrendFilterShadowOnly', '')} "
                        f"D1_required={row.get('InpSmartTrendRequireD1', '')} "
                        f"D1={row.get('InpSmartTrendMinD1Aligned', '')} "
                        f"H1_required={row.get('InpSmartTrendRequireH1', '')} "
                        f"H1={row.get('InpSmartTrendMinH1Aligned', '')}"
                    ),
                }
            )
    return output


def _repo_state(repo_root: Path) -> dict[str, str]:
    return {
        "branch": _git(repo_root, "branch", "--show-current"),
        "commit": _git(repo_root, "rev-parse", "HEAD"),
        "main_remote_commit": _git(repo_root, "ls-remote", "origin", "refs/heads/main").split()[0]
        if _git(repo_root, "ls-remote", "origin", "refs/heads/main")
        else "",
    }


def _git(repo_root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=repo_root, text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def _chart_summary(charts: list[dict[str, Any]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for chart in charts:
        output.append(
            {
                "chart": str(chart.get("chart", "")),
                "symbol": str(chart.get("symbol", "")),
                "candidate": str(chart.get("candidate", "")),
                "dry_run": str(chart.get("dry_run", chart.get("dry_run_only", ""))).lower(),
                "broker_action_allowed": str(chart.get("broker_action_allowed", "")).lower(),
                "candidate_status": str(chart.get("candidate_status", "")),
            }
        )
    return output


def _is_quarantine_active(charts: list[dict[str, str]]) -> bool:
    return bool(charts) and all(
        chart.get("dry_run") == "true" and chart.get("broker_action_allowed") == "false" for chart in charts
    )


def _a3_broker_action_status(report: dict[str, Any]) -> str:
    lane = report.get("lane", {})
    if (
        str(report.get("status", "")).upper() == "PASS"
        and str(lane.get("account_login", "")) == "1033669"
        and str(lane.get("broker_action_allowed", "")).lower() == "true"
        and str(lane.get("dry_run", "")).lower() == "false"
    ):
        return "OWNER_AUTHORIZED_DEMO_BROKER_ACTION"
    return "PENDING_OR_NOT_VISIBLE"


def _a3_historical_owner_authorization(report: dict[str, Any]) -> dict[str, Any]:
    lane = report.get("lane", {})
    return {
        "933400_demo_broker_action": _a3_broker_action_status(report),
        "authorized_at_source": "A3_TIER1_COMPAT_BROKER_ACTION_OWNER_AUTHORIZATION_2026_06_17.md",
        "attachment_status": report.get("status", "MISSING"),
        "lane": {
            "magic": str(lane.get("magic", "")),
            "symbol": str(lane.get("symbol", "")),
            "dry_run_at_attachment": str(lane.get("dry_run", "")).lower(),
            "broker_action_allowed_at_attachment": str(lane.get("broker_action_allowed", "")).lower(),
            "fixed_lot": str(lane.get("fixed_lot", "")),
        },
        "current_permission": "SUPERSEDED_BY_EMERGENCY_PAUSE",
    }


def _a3_current_runtime_state(review: dict[str, Any], pause: dict[str, Any]) -> dict[str, Any]:
    after_broker = _mapping(pause.get("after_broker"))
    return {
        "effective_runtime_authorization": review.get(
            "runtime_authorization_status",
            pause.get("runtime_authorization_status", "MISSING"),
        ),
        "verified_at_utc": review.get("created_at_utc", pause.get("created_at_utc", "")),
        "open_positions": _to_int(after_broker.get("a3_positions_total")) or 0,
        "pending_orders": _to_int(after_broker.get("a3_orders_total")) or 0,
        "lanes": {
            "933200": _a3_lane_runtime_state(review, "933200"),
            "933300": _a3_lane_runtime_state(review, "933300"),
            "933400": _a3_lane_runtime_state(review, "933400"),
            "profit_lock": _profit_lock_runtime_state(review),
        },
    }


def _a3_lane_runtime_state(report: dict[str, Any], magic: str) -> str:
    for row in report.get("per_magic", []):
        if str(row.get("magic", "")) != magic:
            continue
        dry_run = str(row.get("dry_run_now", "")).lower()
        broker_action = str(row.get("broker_action_allowed_now", "")).lower()
        if dry_run == "true" and broker_action == "false":
            return "PAUSED"
        if dry_run == "false" and broker_action == "true":
            return "BROKER_ACTION_ENABLED"
        return f"UNKNOWN_DRY_RUN_{dry_run}_BROKER_{broker_action}"
    return "MISSING"


def _profit_lock_runtime_state(report: dict[str, Any]) -> str:
    for row in report.get("chart_state", {}).values():
        if row.get("expert") != "Account3ProfitLockExitManager":
            continue
        dry_run = str(row.get("dry_run", "")).lower()
        manage_action = str(row.get("manage_action_allowed", "")).lower()
        if dry_run == "true" and manage_action == "false":
            return "DRY_RUN_DISARMED"
        if dry_run == "false" and manage_action == "true":
            return "ARMED"
        return f"UNKNOWN_DRY_RUN_{dry_run}_MANAGE_{manage_action}"
    return "MISSING"


def _a3_lane_paused(report: dict[str, Any], magic: str) -> bool:
    for row in report.get("per_magic", []):
        if str(row.get("magic", "")) == magic:
            return str(row.get("dry_run_now", "")).lower() == "true" and str(row.get("broker_action_allowed_now", "")).lower() == "false"
    return False


def _profit_lock_disarmed(report: dict[str, Any]) -> bool:
    for row in report.get("chart_state", {}).values():
        if row.get("expert") == "Account3ProfitLockExitManager":
            return str(row.get("dry_run", "")).lower() == "true" and str(row.get("manage_action_allowed", "")).lower() == "false"
    return False


def _test_suite_status(report_dir: Path) -> dict[str, Any]:
    p1_p2 = report_dir / "A3_REPAIR_P1_P2_IMPLEMENTATION_REPORT_2026_06_18.json"
    payload = _read_json(p1_p2)
    phase1_result = str(payload.get("verification", {}).get("phase1_pytest", ""))
    if phase1_result:
        passed = _to_int(phase1_result.split()[0])
        failed = 0 if "failed" not in phase1_result.lower() else None
        return {
            "status": "PASS" if passed and failed == 0 else "UNKNOWN",
            "passed": passed,
            "failed": failed,
            "source": "xau-usd/xauusd-phase1/outputs/reports/A3_REPAIR_P1_P2_IMPLEMENTATION_REPORT_2026_06_18.json",
        }
    closure = report_dir / "PHASE1_TEST_FAILURE_CLOSURE_2026_06_18.md"
    if not closure.exists():
        return {"status": "UNKNOWN", "passed": None, "failed": None, "source": ""}
    text = closure.read_text(encoding="utf-8", errors="replace")
    passed = None
    failed = None
    for line in text.splitlines():
        if "passed" in line and "failed" in line:
            parts = line.replace("`", "").replace(",", "").split()
            for index, part in enumerate(parts):
                if part == "passed" and index > 0:
                    passed = _to_int(parts[index - 1])
                if part == "failed" and index > 0:
                    failed = _to_int(parts[index - 1])
            if passed is not None and failed is not None:
                break
    status = "PASS" if failed == 0 and passed else "FAIL" if failed else "UNKNOWN"
    return {
        "status": status,
        "passed": passed,
        "failed": failed,
        "source": "xau-usd/xauusd-phase1/outputs/reports/PHASE1_TEST_FAILURE_CLOSURE_2026_06_18.md",
    }


def _shadow_hypothesis_status(phase1_root: Path) -> dict[str, Any]:
    doc = phase1_root / "docs" / "A3_SIGNAL_QUALITY_HYPOTHESES_V1_2026_06_18.md"
    manifest = phase1_root / "outputs" / "manifests" / "A3_SIGNAL_QUALITY_HYPOTHESES_V1.sha256.json"
    if not doc.exists() or not manifest.exists():
        return {"status": "NOT_REGISTERED", "doc": str(doc), "manifest": str(manifest), "reason": "doc_or_manifest_missing"}
    payload = _read_json(manifest)
    if payload.get("status") != "LOCKED":
        return {"status": "MANIFEST_NOT_LOCKED", "doc": str(doc), "manifest": str(manifest), "manifest_status": payload.get("status", "MISSING")}
    digest = hashlib.sha256(doc.read_bytes()).hexdigest()
    expected = str(payload.get("sha256", ""))
    if digest != expected:
        return {
            "status": "HASH_MISMATCH",
            "doc": str(doc),
            "manifest": str(manifest),
            "sha256": digest,
            "expected_sha256": expected,
        }
    text_head = "\n".join(doc.read_text(encoding="utf-8", errors="replace").splitlines()[:8])
    note = ""
    if "PRE_REGISTERED_LOCK_PENDING_MANIFEST" in text_head:
        note = "Doc header still says PRE_REGISTERED_LOCK_PENDING_MANIFEST while manifest is LOCKED; discrepancy recorded without modifying locked file."
    return {
        "status": "REGISTERED_LOCKED",
        "doc": "docs/A3_SIGNAL_QUALITY_HYPOTHESES_V1_2026_06_18.md",
        "manifest": "outputs/manifests/A3_SIGNAL_QUALITY_HYPOTHESES_V1.sha256.json",
        "sha256": digest,
        "note": note,
    }


def _pause_artifact_runtime_consistency_status(review: dict[str, Any], pause: dict[str, Any]) -> str:
    if review.get("artifact_integrity_status") == "PASS" and pause.get("status") == "PASS":
        return "PASS"
    if review.get("artifact_integrity_status") == "PASS" and pause.get("status") == "ALREADY_PAUSED":
        return "PASS"
    if not review and not pause:
        return "MISSING"
    return "REVIEW_REQUIRED"


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _rel(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return str(path)


def _render_markdown(summary: dict[str, Any]) -> str:
    accounts = summary["accounts"]
    quarantine = summary["quarantine"]
    auth = summary["authorization"]
    lines = [
        "# Project Status Summary",
        "",
        f"Generated UTC: `{summary['generated_at_utc']}`",
        f"Artifact generation base commit: `{summary['repo']['commit']}`",
        f"Branch: `{summary['repo']['branch']}`",
        "",
        "This small file is the audit-friendly companion to the large `status.html` dashboard.",
        "",
        "## Accounts",
        "",
        "| Account | Login | Role | Round quarantine active | Touched by round quarantine |",
        "| --- | ---: | --- | ---: | ---: |",
    ]
    for key, account in accounts.items():
        lines.append(
            f"| {key} | `{account['login']}` | {account['role']} | "
            f"`{str(account['round_quarantine_active']).lower()}` | "
            f"`{str(account['touched_by_round_quarantine']).lower()}` |"
        )
    lines.extend(
        [
            "",
            "## A1 Round-Family Quarantine",
            "",
            f"Status: `{quarantine['status']}`",
            f"Scope: `{quarantine['scope']}`",
            f"Keep active through forward week: `{str(quarantine['keep_active_through_forward_week']).lower()}`",
            f"Rollback required now: `{str(quarantine['rollback_required_now']).lower()}`",
            "",
            "| Chart | Candidate | Dry run | Broker action | Status |",
            "| --- | --- | ---: | ---: | --- |",
        ]
    )
    for chart in quarantine["target_charts"]:
        lines.append(
            f"| `{chart['chart']}` | `{chart['candidate']}` | `{chart['dry_run']}` | "
            f"`{chart['broker_action_allowed']}` | `{chart['candidate_status']}` |"
        )
    lines.extend(
        [
            "",
            "## Protected Breakout Core",
            "",
            f"Source: `{quarantine.get('protected_charts_source', 'historical_quarantine_report')}`",
            "",
            "| Chart | Candidate | Account | Magic | Session | Smart trend | Dry run | Broker action | Status |",
            "| --- | --- | ---: | ---: | --- | --- | ---: | ---: | --- |",
        ]
    )
    for chart in quarantine["protected_charts"]:
        lines.append(
            f"| `{chart['chart']}` | `{chart['candidate']}` | `{chart.get('account', '')}` | "
            f"`{chart.get('derived_magic', '')}` | `{chart.get('session', '')}` | `{chart.get('smart_trend', '')}` | `{chart['dry_run']}` | "
            f"`{chart['broker_action_allowed']}` | `{chart['candidate_status']}` |"
        )
    diagnostics = summary.get("diagnostics", {})
    breakout_forensic = diagnostics.get("xau_920101_breakout_retest_failure_forensic", {})
    current_920101 = breakout_forensic.get("current_24h_h1", {})
    evening_920101 = breakout_forensic.get("server_16_19", {})
    repair_920101 = breakout_forensic.get("repair_24h_h1_faststop_min800", {})
    profit_repair_920101 = breakout_forensic.get("repair_24h_h1_faststop_min800_lock100_050", {})
    if breakout_forensic:
        lines.extend(
            [
                "",
                "## XAU 920101 Breakout-Retest Failure Forensic",
                "",
                f"Status: `{breakout_forensic.get('status', 'MISSING')}`",
                f"Finding: {breakout_forensic.get('finding', '')}",
                "",
                "| Slice | Trades | WR | Net AED | PF | Top 3 Removed |",
                "| --- | ---: | ---: | ---: | ---: | ---: |",
                (
                    f"| `current_24h_h1_smart` | `{current_920101.get('trades', 'n/a')}` | "
                    f"`{current_920101.get('win_rate_pct', 'n/a')}%` | `{current_920101.get('net_aed', 'n/a')}` | "
                    f"`{current_920101.get('profit_factor', 'n/a')}` | `{current_920101.get('top3_removed_aed', 'n/a')}` |"
                ),
                (
                    f"| `server_16_19_h1_smart` | `{evening_920101.get('trades', 'n/a')}` | "
                    f"`{evening_920101.get('win_rate_pct', 'n/a')}%` | `{evening_920101.get('net_aed', 'n/a')}` | "
                    f"`{evening_920101.get('profit_factor', 'n/a')}` | `{evening_920101.get('top3_removed_aed', 'n/a')}` |"
                ),
            ]
        )
        if repair_920101.get("trades"):
            lines.append(
                f"| `repair_24h_h1_faststop_min800` | `{repair_920101.get('trades', 'n/a')}` | "
                f"`{repair_920101.get('win_rate_pct', 'n/a')}%` | `{repair_920101.get('net_aed', 'n/a')}` | "
                f"`{repair_920101.get('profit_factor', 'n/a')}` | `{repair_920101.get('top3_removed_aed', 'n/a')}` |"
            )
        if profit_repair_920101.get("trades"):
            lines.append(
                f"| `repair_24h_h1_faststop_min800_lock100_050` | `{profit_repair_920101.get('trades', 'n/a')}` | "
                f"`{profit_repair_920101.get('win_rate_pct', 'n/a')}%` | `{profit_repair_920101.get('net_aed', 'n/a')}` | "
                f"`{profit_repair_920101.get('profit_factor', 'n/a')}` | `{profit_repair_920101.get('top3_removed_aed', 'n/a')}` |"
            )
        lines.extend(
            [
                "",
                (
                    f"Fast-exit warning: `hold_<=15m` in the current lane is "
                    f"`{current_920101.get('fast_exit_net_aed', 'n/a')} AED` at "
                    f"`{current_920101.get('fast_exit_win_rate_pct', 'n/a')}%` WR."
                ),
                f"Forensic report: `{breakout_forensic.get('report', '')}`",
            ]
        )
    momentum = summary.get("experimental_lanes", {}).get("a1_xau_m5_momentum_continuation", {})
    lines.extend(
        [
            "",
            "## A1 Momentum Continuation Lane",
            "",
            "This is a separate A1-only demo lane for M5 break-and-run moves. It is not part of the protected `920101` breakout-retest core.",
            "",
            "| Field | Value |",
            "| --- | --- |",
            f"| Status | `{momentum.get('status', 'MISSING')}` |",
            f"| Account | `{momentum.get('account', '')}` |",
            f"| EA | `{momentum.get('ea', '')}` |",
            f"| Symbol | `{momentum.get('symbol', '')}` |",
            f"| Magic | `{momentum.get('magic', '')}` |",
            f"| Lot | `{momentum.get('lot', '')}` |",
            f"| Run ID | `{momentum.get('run_id', '')}` |",
            f"| Order comment | `{momentum.get('order_comment', '')}` |",
            f"| Broker action enabled for new lane | `{str(momentum.get('broker_action_enabled_for_new_lane', False)).lower()}` |",
            f"| Existing 920101 chart edited | `{str(momentum.get('existing_920101_chart_edited', True)).lower()}` |",
            f"| A2 touched | `{str(momentum.get('a2_touched', True)).lower()}` |",
            f"| A3 touched | `{str(momentum.get('a3_touched', True)).lower()}` |",
            f"| Startup rows seen | `{momentum.get('startup_rows_seen', 0)}` |",
            f"| Signal rows seen | `{momentum.get('signal_rows_seen', 0)}` |",
            f"| Order proof | `{momentum.get('first_order_status', 'MISSING')}` |",
            f"| Evidence status | `{momentum.get('evidence_status', 'MISSING')}` |",
            f"| Spec SHA256 | `{momentum.get('spec_sha256', '')}` |",
            f"| Forward start broker time | `{momentum.get('forward_start_broker', '')}` |",
            f"| Expected 100-trade duration | `{momentum.get('expected_100_trade_duration', '')}` |",
            f"| Dedicated kill switch | `{momentum.get('kill_switch_file', '')}` |",
            f"| Attribution report | `{momentum.get('attribution_report', '')}` |",
            f"| Shadow counterfactual report | `{momentum.get('shadow_counterfactual_report', '')}` |",
            f"| Attachment report | `{momentum.get('report', '')}` |",
        ]
    )
    split_forward = momentum.get("split_entry_be_tp1_forward", {})
    split_components = split_forward.get("components", []) if isinstance(split_forward, dict) else []
    if split_forward:
        lines.extend(
            [
                "",
                "### A1 Momentum Split-Entry BE-on-TP1 Forward Lane",
                "",
                "This is the owner-approved A1-only experimental split-entry lane. It can place demo orders on A1 only, using a shared signal-claim guard so only the highest-priority component acts on an overlapping signal.",
                "",
                "| Field | Value |",
                "| --- | --- |",
                f"| Status | `{split_forward.get('status', 'MISSING')}` |",
                f"| Account | `{split_forward.get('account', '')}` |",
                f"| Symbol / timeframe | `{split_forward.get('symbol', '')} / {split_forward.get('timeframe', '')}` |",
                f"| Shared magic | `{split_forward.get('magic', '')}` |",
                f"| Components attached | `{split_forward.get('component_count', 'n/a')}` |",
                f"| First order status | `{split_forward.get('first_order_status', '')}` |",
                f"| Exposure note | `{split_forward.get('exposure_note', '')}` |",
                f"| Boundary | `{split_forward.get('boundary', '')}` |",
                f"| Frozen spec | `{split_forward.get('frozen_spec', '')}` |",
                f"| Owner authorization | `{split_forward.get('owner_authorization', '')}` |",
                f"| Hash verification | `{split_forward.get('hash_verification', '')}` |",
                "",
                "| Component | Run ID | Magic | Lot | Comment | Broker action | Report |",
                "| --- | --- | ---: | ---: | --- | ---: | --- |",
            ]
        )
        for component in split_components:
            lines.append(
                f"| `{component.get('key', '')}` | `{component.get('run_id', '')}` | "
                f"`{component.get('magic', '')}` | `{component.get('lot', '')}` | "
                f"`{component.get('order_comment', '')}` | "
                f"`{str(component.get('broker_action', False)).lower()}` | "
                f"`{component.get('report', '')}` |"
            )
    momentum_replacement = momentum.get("frequency_first_replacement", {})
    if momentum_replacement:
        replacement_contract = momentum_replacement.get("expected_forward_contract", {})
        lines.extend(
            [
                "",
                "### A1 Momentum Frequency-First Replacement Candidate",
                "",
                "This is the current candidate that better matches the project goal. It is not attached yet and should replace the sparse RR2 lane by default, not stack with it.",
                "",
                "| Field | Value |",
                "| --- | --- |",
                f"| Status | `{momentum_replacement.get('status', 'MISSING')}` |",
                f"| Candidate | `{momentum_replacement.get('candidate', '')}` |",
                f"| Replacement policy | `{momentum_replacement.get('replace_or_stack', '')}` |",
                f"| Currently attached business fit | `{momentum_replacement.get('currently_attached_business_fit', '')}` |",
                f"| Runtime touched by readiness work | `{momentum_replacement.get('runtime_touched', 'n/a')}` |",
                f"| Review required | `{momentum_replacement.get('review_required', 'n/a')}` |",
                f"| Owner approval required | `{momentum_replacement.get('owner_approval_required', 'n/a')}` |",
                f"| Run ID if approved | `{replacement_contract.get('run_id', '')}` |",
                f"| Direction | `{replacement_contract.get('direction', '')}` |",
                f"| Risk reward | `{replacement_contract.get('risk_reward', '')}` |",
                f"| Max cost R | `{replacement_contract.get('max_estimated_cost_r', '')}` |",
                f"| Blocked hours | `{replacement_contract.get('blocked_entry_hours', '')}` |",
                f"| Max trades/day | `{replacement_contract.get('max_trades_per_day', '')}` |",
                f"| Cooldown minutes | `{replacement_contract.get('cooldown_minutes', '')}` |",
                f"| Readiness doc | `{momentum_replacement.get('readiness_doc', '')}` |",
                f"| V6 diagnostic doc | `{momentum_replacement.get('v6_diagnostic_doc', '')}` |",
                f"| Frequency requirement verdict | `{momentum_replacement.get('frequency_requirement_verdict', '')}` |",
                f"| Attach command after approval | `{momentum_replacement.get('attach_command_after_approval', '')}` |",
            ]
        )
    portfolio_candidate = momentum.get("portfolio_combination_candidate", {})
    if portfolio_candidate:
        lines.extend(
            [
                "",
                "### A1 Momentum Portfolio Combination Candidate",
                "",
                "This diagnostic checks whether V4 can be paired with a V13 companion lane to satisfy the multiple-trades/day objective without collapsing edge quality.",
                "",
                "| Field | Value |",
                "| --- | --- |",
                f"| Status | `{portfolio_candidate.get('status', 'MISSING')}` |",
                f"| Candidate | `{portfolio_candidate.get('candidate', '')}` |",
                f"| Decision | `{portfolio_candidate.get('decision', '')}` |",
                f"| Trades | `{portfolio_candidate.get('trades', 'n/a')}` |",
                f"| Win rate | `{portfolio_candidate.get('win_rate_pct', 'n/a')}%` |",
                f"| Net PnL USD | `{portfolio_candidate.get('net_usd', 'n/a')}` |",
                f"| Profit factor | `{portfolio_candidate.get('profit_factor', 'n/a')}` |",
                f"| Active days | `{portfolio_candidate.get('active_days', 'n/a')}` |",
                f"| Trades / active day | `{portfolio_candidate.get('trades_per_active_day', 'n/a')}` |",
                f"| Multi-trade days | `{portfolio_candidate.get('multi_trade_days', 'n/a')}` |",
                f"| Positive / negative months | `{portfolio_candidate.get('positive_months', 'n/a')} / {portfolio_candidate.get('negative_months', 'n/a')}` |",
                f"| Max closed DD USD | `{portfolio_candidate.get('max_closed_drawdown_usd', 'n/a')}` |",
                f"| Recommendation | `{portfolio_candidate.get('recommendation', '')}` |",
                f"| Forward draft | `{portfolio_candidate.get('forward_draft', '')}` |",
                f"| Report | `{portfolio_candidate.get('report', '')}` |",
            ]
        )
    broad_search = momentum.get("broad_portfolio_search", {})
    clean_candidate = broad_search.get("best_clean_candidate", {}) if isinstance(broad_search, dict) else {}
    headline_candidate = broad_search.get("headline_candidate", {}) if isinstance(broad_search, dict) else {}
    if broad_search:
        lines.extend(
            [
                "",
                "### A1 Momentum Broad Portfolio Search",
                "",
                "This broader offline search ranks exact-MT5 portfolio combinations and flags duplicate-like same-minute stacking.",
                "",
                "| Field | Headline candidate | Best clean candidate |",
                "| --- | --- | --- |",
                f"| Name | `{headline_candidate.get('name', '')}` | `{clean_candidate.get('name', '')}` |",
                f"| Decision | `{headline_candidate.get('decision', '')}` | `{clean_candidate.get('decision', '')}` |",
                f"| Trades | `{headline_candidate.get('trades', 'n/a')}` | `{clean_candidate.get('trades', 'n/a')}` |",
                f"| Win rate | `{headline_candidate.get('win_rate_pct', 'n/a')}%` | `{clean_candidate.get('win_rate_pct', 'n/a')}%` |",
                f"| Net USD | `{headline_candidate.get('net_usd', 'n/a')}` | `{clean_candidate.get('net_usd', 'n/a')}` |",
                f"| Profit factor | `{headline_candidate.get('profit_factor', 'n/a')}` | `{clean_candidate.get('profit_factor', 'n/a')}` |",
                f"| Active days | `{headline_candidate.get('active_days', 'n/a')}` | `{clean_candidate.get('active_days', 'n/a')}` |",
                f"| Trades / active day | `{headline_candidate.get('trades_per_active_day', 'n/a')}` | `{clean_candidate.get('trades_per_active_day', 'n/a')}` |",
                f"| Duplicate-like trade pct | `{headline_candidate.get('duplicate_like_trade_pct', 'n/a')}%` | `{clean_candidate.get('duplicate_like_trade_pct', 'n/a')}%` |",
                f"| Max closed DD USD | `{headline_candidate.get('max_closed_drawdown_usd', 'n/a')}` | `{clean_candidate.get('max_closed_drawdown_usd', 'n/a')}` |",
                f"| Recommendation | `{broad_search.get('recommendation', '')}` | `{broad_search.get('recommendation', '')}` |",
                f"| Report | `{broad_search.get('report', '')}` | `{broad_search.get('report', '')}` |",
                f"| Verdict | `{broad_search.get('verdict', '')}` | `{broad_search.get('verdict', '')}` |",
                f"| Clean forward draft | `{broad_search.get('clean_forward_draft', '')}` | `{broad_search.get('clean_forward_draft', '')}` |",
            ]
        )
    deep_search = momentum.get("deep_portfolio_search", {})
    deep_headline = deep_search.get("headline_candidate", {}) if isinstance(deep_search, dict) else {}
    deep_low_overlap = (
        deep_search.get("best_low_overlap_frequency_candidate", {}) if isinstance(deep_search, dict) else {}
    )
    if deep_search:
        lines.extend(
            [
                "",
                "### A1 Momentum Deep Portfolio Search",
                "",
                "This deeper offline search tests one-, two-, and three-lane portfolios after deterministic same-minute same-direction de-duplication. It is the closest current work to the owner requirement: enough intraday frequency without counting clone stacks as edge.",
                "",
                "| Field | Headline deep candidate | Low-overlap frequency candidate |",
                "| --- | --- | --- |",
                f"| Name | `{deep_headline.get('name', '')}` | `{deep_low_overlap.get('name', '')}` |",
                f"| Decision | `{deep_headline.get('decision', '')}` | `{deep_low_overlap.get('decision', '')}` |",
                f"| Raw trades | `{deep_headline.get('raw_trades', 'n/a')}` | `{deep_low_overlap.get('raw_trades', 'n/a')}` |",
                f"| Deduped trades | `{deep_headline.get('deduped_trades', 'n/a')}` | `{deep_low_overlap.get('deduped_trades', 'n/a')}` |",
                f"| Win rate | `{deep_headline.get('win_rate_pct', 'n/a')}%` | `{deep_low_overlap.get('win_rate_pct', 'n/a')}%` |",
                f"| Net USD | `{deep_headline.get('net_usd', 'n/a')}` | `{deep_low_overlap.get('net_usd', 'n/a')}` |",
                f"| Profit factor | `{deep_headline.get('profit_factor', 'n/a')}` | `{deep_low_overlap.get('profit_factor', 'n/a')}` |",
                f"| Active days | `{deep_headline.get('active_days', 'n/a')}` | `{deep_low_overlap.get('active_days', 'n/a')}` |",
                f"| Trades / active day | `{deep_headline.get('trades_per_active_day', 'n/a')}` | `{deep_low_overlap.get('trades_per_active_day', 'n/a')}` |",
                f"| Raw duplicate-like pct | `{deep_headline.get('raw_duplicate_like_trade_pct', 'n/a')}%` | `{deep_low_overlap.get('raw_duplicate_like_trade_pct', 'n/a')}%` |",
                f"| Top25 removed USD | `{deep_headline.get('top25_removed_usd', 'n/a')}` | `{deep_low_overlap.get('top25_removed_usd', 'n/a')}` |",
                f"| Max closed DD USD | `{deep_headline.get('max_closed_drawdown_usd', 'n/a')}` | `{deep_low_overlap.get('max_closed_drawdown_usd', 'n/a')}` |",
                f"| Stress verdict | `{deep_search.get('stress_verdict', '')}` | `{deep_search.get('stress_verdict', '')}` |",
                f"| Recommendation | `{deep_search.get('recommendation', '')}` | `{deep_search.get('recommendation', '')}` |",
                f"| Report | `{deep_search.get('report', '')}` | `{deep_search.get('report', '')}` |",
                f"| Stress report | `{deep_search.get('stress_report', '')}` | `{deep_search.get('stress_report', '')}` |",
                f"| Verdict | `{deep_search.get('verdict', '')}` | `{deep_search.get('verdict', '')}` |",
                f"| Forward draft | `{deep_search.get('forward_draft', '')}` | `{deep_search.get('forward_draft', '')}` |",
            ]
        )
    robust_search = momentum.get("robust_portfolio_search", {})
    robust_candidate = robust_search.get("best_candidate", {}) if isinstance(robust_search, dict) else {}
    robust_weakest_half = robust_search.get("weakest_half_year", {}) if isinstance(robust_search, dict) else {}
    robust_repair = robust_search.get("best_repair_candidate", {}) if isinstance(robust_search, dict) else {}
    robust_repair_weakest_half = (
        robust_search.get("repair_weakest_half_year", {}) if isinstance(robust_search, dict) else {}
    )
    if robust_search:
        lines.extend(
            [
                "",
                "### A1 Momentum Robust Portfolio Search",
                "",
                "This is the current strongest match for the owner requirement: active XAU M5 trading, de-duplicated evidence, win rate above 50%, and positive older/newer split windows.",
                "",
                "| Field | Robust candidate |",
                "| --- | --- |",
                f"| Name | `{robust_candidate.get('name', '')}` |",
                f"| Decision | `{robust_candidate.get('decision', '')}` |",
                f"| Trades | `{robust_candidate.get('trades', 'n/a')}` |",
                f"| Win rate | `{robust_candidate.get('win_rate_pct', 'n/a')}%` |",
                f"| Net USD | `{robust_candidate.get('net_usd', 'n/a')}` |",
                f"| Profit factor | `{robust_candidate.get('profit_factor', 'n/a')}` |",
                f"| Active days | `{robust_candidate.get('active_days', 'n/a')}` |",
                f"| Trades / active day | `{robust_candidate.get('trades_per_active_day', 'n/a')}` |",
                f"| Older net / PF | `{robust_candidate.get('older_net_usd', 'n/a')} / {robust_candidate.get('older_profit_factor', 'n/a')}` |",
                f"| Newer net / PF | `{robust_candidate.get('newer_net_usd', 'n/a')} / {robust_candidate.get('newer_profit_factor', 'n/a')}` |",
                f"| Raw duplicate-like pct | `{robust_candidate.get('raw_duplicate_like_trade_pct', 'n/a')}%` |",
                f"| Top25 removed USD | `{robust_candidate.get('top25_removed_usd', 'n/a')}` |",
                f"| Max closed DD USD | `{robust_candidate.get('max_closed_drawdown_usd', 'n/a')}` |",
                f"| Stress verdict | `{robust_search.get('stress_verdict', '')}` |",
                f"| Walk-forward verdict | `{robust_search.get('walkforward_verdict', '')}` |",
                f"| Weakest half-year | `{robust_weakest_half.get('bucket', 'n/a')} / PF {robust_weakest_half.get('profit_factor', 'n/a')} / net {robust_weakest_half.get('net_usd', 'n/a')}` |",
                f"| Best repair | `{', '.join(robust_repair.get('filters', [])) if isinstance(robust_repair.get('filters', []), list) else robust_repair.get('filters', '')}` |",
                f"| Repair metrics | `{robust_repair.get('trades', 'n/a')} trades / WR {robust_repair.get('win_rate_pct', 'n/a')}% / PF {robust_repair.get('profit_factor', 'n/a')} / net {robust_repair.get('net_usd', 'n/a')}` |",
                f"| Repair 2022-H2 | `PF {robust_repair.get('weak_profit_factor', 'n/a')} / net {robust_repair.get('weak_net_usd', 'n/a')}` |",
                f"| Repair walk-forward verdict | `{robust_search.get('repair_walkforward_verdict', '')}` |",
                f"| Repair weakest half-year | `{robust_repair_weakest_half.get('bucket', 'n/a')} / PF {robust_repair_weakest_half.get('profit_factor', 'n/a')} / net {robust_repair_weakest_half.get('net_usd', 'n/a')}` |",
                f"| Recommendation | `{robust_search.get('recommendation', '')}` |",
                f"| Report | `{robust_search.get('report', '')}` |",
                f"| Stress report | `{robust_search.get('stress_report', '')}` |",
                f"| Walk-forward report | `{robust_search.get('walkforward_report', '')}` |",
                f"| Repair report | `{robust_search.get('repair_report', '')}` |",
                f"| Repair walk-forward report | `{robust_search.get('repair_walkforward_report', '')}` |",
                f"| Forward draft | `{robust_search.get('forward_draft', '')}` |",
                f"| Repair forward draft | `{robust_search.get('repair_forward_draft', '')}` |",
            ]
        )
    daily_fit = momentum.get("daily_fit_portfolio_search", {})
    daily_fit_candidate = daily_fit.get("best_candidate", {}) if isinstance(daily_fit, dict) else {}
    daily_fit_repair_candidate = daily_fit.get("best_repair_candidate", {}) if isinstance(daily_fit, dict) else {}
    if daily_fit:
        lines.extend(
            [
                "",
                "### A1 Momentum Daily-Fit Portfolio Search",
                "",
                "This is the newest diagnostic layer for the owner's actual operating target: multiple trades per active day, enough 3+ trade days, positive active-day rate, PF/net, and low duplicate-like overlap.",
                "",
                "| Field | Daily-fit candidate |",
                "| --- | --- |",
                f"| Status | `{daily_fit.get('status', 'MISSING')}` |",
                f"| Decision | `{daily_fit_candidate.get('decision', '')}` |",
                f"| Members | `{', '.join(daily_fit_candidate.get('members', [])) if isinstance(daily_fit_candidate.get('members', []), list) else daily_fit_candidate.get('members', '')}` |",
                f"| Trades | `{daily_fit_candidate.get('trades', 'n/a')}` |",
                f"| Win rate | `{daily_fit_candidate.get('win_rate_pct', 'n/a')}%` |",
                f"| Net USD | `{daily_fit_candidate.get('net_usd', 'n/a')}` |",
                f"| Profit factor | `{daily_fit_candidate.get('profit_factor', 'n/a')}` |",
                f"| Active days | `{daily_fit_candidate.get('active_days', 'n/a')}` |",
                f"| Trades / active day | `{daily_fit_candidate.get('trades_per_active_day', 'n/a')}` |",
                f"| 3+ trade day pct | `{daily_fit_candidate.get('three_plus_trade_day_pct', 'n/a')}%` |",
                f"| Positive day pct | `{daily_fit_candidate.get('positive_day_pct', 'n/a')}%` |",
                f"| Median day USD | `{daily_fit_candidate.get('median_day_usd', 'n/a')}` |",
                f"| Worst day USD | `{daily_fit_candidate.get('worst_day_usd', 'n/a')}` |",
                f"| Positive / negative months | `{daily_fit_candidate.get('positive_months', 'n/a')} / {daily_fit_candidate.get('negative_months', 'n/a')}` |",
                f"| Worst month USD | `{daily_fit_candidate.get('worst_month_usd', 'n/a')}` |",
                f"| Top100 removed USD | `{daily_fit_candidate.get('top100_removed_usd', 'n/a')}` |",
                f"| Older net / PF | `{daily_fit_candidate.get('older_net_usd', 'n/a')} / {daily_fit_candidate.get('older_profit_factor', 'n/a')}` |",
                f"| Newer net / PF | `{daily_fit_candidate.get('newer_net_usd', 'n/a')} / {daily_fit_candidate.get('newer_profit_factor', 'n/a')}` |",
                f"| Raw duplicate-like pct | `{daily_fit_candidate.get('raw_duplicate_like_trade_pct', 'n/a')}%` |",
                f"| Stress report | `{daily_fit.get('stress_report', '')}` |",
                f"| Repair status | `{daily_fit.get('repair_status', 'MISSING')}` |",
                f"| Best repair blocks | `{', '.join(daily_fit_repair_candidate.get('blocks', [])) if isinstance(daily_fit_repair_candidate.get('blocks', []), list) else daily_fit_repair_candidate.get('blocks', '')}` |",
                f"| Repaired metrics | `{daily_fit_repair_candidate.get('trades', 'n/a')} trades / WR {daily_fit_repair_candidate.get('win_rate_pct', 'n/a')}% / PF {daily_fit_repair_candidate.get('profit_factor', 'n/a')} / net {daily_fit_repair_candidate.get('net_usd', 'n/a')}` |",
                f"| Repaired active-day shape | `{daily_fit_repair_candidate.get('active_days', 'n/a')} active days / {daily_fit_repair_candidate.get('trades_per_active_day', 'n/a')} trades per active day / {daily_fit_repair_candidate.get('three_plus_trade_day_pct', 'n/a')}% 3+ trade days` |",
                f"| Repaired day/month stability | `{daily_fit_repair_candidate.get('positive_day_pct', 'n/a')}% positive days / {daily_fit_repair_candidate.get('positive_months', 'n/a')} positive months / {daily_fit_repair_candidate.get('negative_months', 'n/a')} negative months` |",
                f"| Repaired top100 removed USD | `{daily_fit_repair_candidate.get('top100_removed_usd', 'n/a')}` |",
                f"| Repaired older net / PF | `{daily_fit_repair_candidate.get('older_net_usd', 'n/a')} / {daily_fit_repair_candidate.get('older_profit_factor', 'n/a')}` |",
                f"| Recommendation | `{daily_fit.get('recommendation', '')}` |",
                f"| Report | `{daily_fit.get('report', '')}` |",
                f"| Forward draft | `{daily_fit.get('forward_draft', '')}` |",
                f"| Repair report | `{daily_fit.get('repair_report', '')}` |",
                f"| Repair forward draft | `{daily_fit.get('repair_forward_draft', '')}` |",
            ]
        )
    daily_guard = momentum.get("daily_guard_search", {})
    daily_guard_candidate = daily_guard.get("best_candidate", {}) if isinstance(daily_guard, dict) else {}
    if daily_guard:
        lines.extend(
            [
                "",
                "### A1 Momentum Daily Guard Search",
                "",
                "This is the lifecycle layer for the active daily-cadence candidate. It tests portfolio-wide trade caps and loss stops on exact MT5 trade CSVs without touching runtime.",
                "",
                "| Field | Daily guard candidate |",
                "| --- | --- |",
                f"| Status | `{daily_guard.get('status', 'MISSING')}` |",
                f"| Decision | `{daily_guard_candidate.get('decision', '')}` |",
                f"| Base | `{daily_guard_candidate.get('base', '')}` |",
                f"| Profit target USD | `{daily_guard_candidate.get('profit_target_usd', 'None')}` |",
                f"| Daily loss stop USD | `{daily_guard_candidate.get('loss_stop_usd', 'n/a')}` |",
                f"| Portfolio max trades/day | `{daily_guard_candidate.get('max_trades_per_day_guard', 'n/a')}` |",
                f"| Max losses/day | `{daily_guard_candidate.get('max_losses_per_day_guard', 'None')}` |",
                f"| Trades | `{daily_guard_candidate.get('trades', 'n/a')}` |",
                f"| Retention | `{daily_guard_candidate.get('retention_pct', 'n/a')}%` |",
                f"| Win rate | `{daily_guard_candidate.get('win_rate_pct', 'n/a')}%` |",
                f"| Net USD | `{daily_guard_candidate.get('net_usd', 'n/a')}` |",
                f"| Profit factor | `{daily_guard_candidate.get('profit_factor', 'n/a')}` |",
                f"| Active days | `{daily_guard_candidate.get('active_days', 'n/a')}` |",
                f"| Trades / active day | `{daily_guard_candidate.get('trades_per_active_day', 'n/a')}` |",
                f"| 3+ trade day pct | `{daily_guard_candidate.get('three_plus_trade_day_pct', 'n/a')}%` |",
                f"| Positive day pct | `{daily_guard_candidate.get('positive_day_pct', 'n/a')}%` |",
                f"| Median day USD | `{daily_guard_candidate.get('median_day_usd', 'n/a')}` |",
                f"| Worst day USD | `{daily_guard_candidate.get('worst_day_usd', 'n/a')}` |",
                f"| Max closed DD USD | `{daily_guard_candidate.get('max_closed_drawdown_usd', 'n/a')}` |",
                f"| Top25 / Top100 removed USD | `{daily_guard_candidate.get('top25_removed_usd', 'n/a')} / {daily_guard_candidate.get('top100_removed_usd', 'n/a')}` |",
                f"| Older net / PF | `{daily_guard_candidate.get('older_net_usd', 'n/a')} / {daily_guard_candidate.get('older_profit_factor', 'n/a')}` |",
                f"| Newer net / PF | `{daily_guard_candidate.get('newer_net_usd', 'n/a')} / {daily_guard_candidate.get('newer_profit_factor', 'n/a')}` |",
                f"| Trade-cap days | `{daily_guard_candidate.get('trade_cap_days', 'n/a')}` |",
                f"| Loss-stop days | `{daily_guard_candidate.get('loss_stop_days', 'n/a')}` |",
                f"| Recommendation | `{daily_guard.get('recommendation', '')}` |",
                f"| Report | `{daily_guard.get('report', '')}` |",
                f"| Forward draft | `{daily_guard.get('forward_draft', '')}` |",
            ]
        )
    pocket_search = momentum.get("pocket_portfolio_search", {})
    pocket_candidate = pocket_search.get("best_candidate", {}) if isinstance(pocket_search, dict) else {}
    if pocket_search:
        lines.extend(
            [
                "",
                "### A1 Momentum Pocket Portfolio Search",
                "",
                "This diagnostic tested whether cleaner `variant + direction + hour` pockets could replace the active daily-cadence portfolio. Result: the cleanest pockets were too sparse for the owner requirement.",
                "",
                "| Field | Pocket search |",
                "| --- | --- |",
                f"| Status | `{pocket_search.get('status', 'MISSING')}` |",
                f"| Best decision | `{pocket_candidate.get('decision', '')}` |",
                f"| Best pocket count | `{pocket_candidate.get('pocket_count', 'n/a')}` |",
                f"| Best trades | `{pocket_candidate.get('trades', 'n/a')}` |",
                f"| Best win rate | `{pocket_candidate.get('win_rate_pct', 'n/a')}%` |",
                f"| Best net USD | `{pocket_candidate.get('net_usd', 'n/a')}` |",
                f"| Best profit factor | `{pocket_candidate.get('profit_factor', 'n/a')}` |",
                f"| Best active days | `{pocket_candidate.get('active_days', 'n/a')}` |",
                f"| Best trades / active day | `{pocket_candidate.get('trades_per_active_day', 'n/a')}` |",
                f"| Best 3+ trade day pct | `{pocket_candidate.get('three_plus_trade_day_pct', 'n/a')}%` |",
                f"| Non-sample-fail rows in top set | `{pocket_search.get('non_sample_fail_count', 'n/a')}` |",
                f"| Recommendation | `{pocket_search.get('recommendation', '')}` |",
                f"| Report | `{pocket_search.get('report', '')}` |",
                f"| CSV | `{pocket_search.get('csv', '')}` |",
            ]
        )
    daily_state_guard = momentum.get("daily_state_guard_search", {})
    daily_state_candidate = daily_state_guard.get("best_candidate", {}) if isinstance(daily_state_guard, dict) else {}
    daily_state_base = daily_state_guard.get("base_summary", {}) if isinstance(daily_state_guard, dict) else {}
    if daily_state_guard:
        lines.extend(
            [
                "",
                "### A1 Momentum Daily-State Guard Search",
                "",
                "This diagnostic tests whether causal day-state rules can improve the frequent daily-guard package without collapsing trade cadence. Result: no state rule crossed the daily-income bar; the best shape remains the simple daily guard.",
                "",
                "| Field | Daily-state search |",
                "| --- | --- |",
                f"| Status | `{daily_state_guard.get('status', 'MISSING')}` |",
                f"| Searched rules | `{daily_state_guard.get('searched_rules', 'n/a')}` |",
                f"| Base trades / WR / PF | `{daily_state_base.get('trades', 'n/a')} / {daily_state_base.get('win_rate_pct', 'n/a')}% / {daily_state_base.get('profit_factor', 'n/a')}` |",
                f"| Base active shape | `{daily_state_base.get('active_days', 'n/a')} active days / {daily_state_base.get('trades_per_active_day', 'n/a')} trades per active day / {daily_state_base.get('positive_day_pct', 'n/a')}% positive days` |",
                f"| Best decision | `{daily_state_candidate.get('decision', '')}` |",
                f"| Best rule | `{daily_state_candidate.get('state_rule', '')}` |",
                f"| Best guard | `target={daily_state_candidate.get('profit_target_usd', 'None')}; stop={daily_state_candidate.get('loss_stop_usd', 'n/a')}; max_trades={daily_state_candidate.get('max_trades_per_day_guard', 'n/a')}; max_losses={daily_state_candidate.get('max_losses_per_day_guard', 'n/a')}; cooldown={daily_state_candidate.get('cooldown_after_loss_minutes', 'n/a')}` |",
                f"| Best trades / retention | `{daily_state_candidate.get('trades', 'n/a')} / {daily_state_candidate.get('retention_pct', 'n/a')}%` |",
                f"| Best WR / PF / net | `{daily_state_candidate.get('win_rate_pct', 'n/a')}% / {daily_state_candidate.get('profit_factor', 'n/a')} / {daily_state_candidate.get('net_usd', 'n/a')}` |",
                f"| Best active shape | `{daily_state_candidate.get('active_days', 'n/a')} active days / {daily_state_candidate.get('trades_per_active_day', 'n/a')} trades per active day / {daily_state_candidate.get('three_plus_trade_day_pct', 'n/a')}% 3+ trade days / {daily_state_candidate.get('positive_day_pct', 'n/a')}% positive days` |",
                f"| Top100 removed USD | `{daily_state_candidate.get('top100_removed_usd', 'n/a')}` |",
                f"| Review-count in top set | `{daily_state_guard.get('review_candidate_count', 'n/a')}` |",
                f"| Recommendation | `{daily_state_guard.get('recommendation', '')}` |",
                f"| Report | `{daily_state_guard.get('report', '')}` |",
                f"| CSV | `{daily_state_guard.get('csv', '')}` |",
            ]
        )
    feature_loss = momentum.get("feature_loss_cluster_analysis", {})
    feature_filter = feature_loss.get("best_filter", {}) if isinstance(feature_loss, dict) else {}
    feature_base = feature_loss.get("base_guarded_summary", {}) if isinstance(feature_loss, dict) else {}
    if feature_loss:
        lines.extend(
            [
                "",
                "### A1 Momentum Feature Loss-Cluster Analysis",
                "",
                "This diagnostic joins the frequent daily-guard trades back to MT5 signal features. Unlike sparse pocket pruning, it looks for measurable setup conditions that can block bad trades while preserving active-day cadence.",
                "",
                "| Field | Feature-loss result |",
                "| --- | --- |",
                f"| Status | `{feature_loss.get('status', 'MISSING')}` |",
                f"| Implementation | `{feature_loss.get('implementation_status', 'n/a')}` |",
                f"| Enriched trades | `{feature_loss.get('enriched_trade_count', 'n/a')} / {feature_loss.get('raw_trade_count', 'n/a')} ({feature_loss.get('enriched_trade_pct', 'n/a')}%)` |",
                f"| Daily-guard baseline | `{feature_base.get('trades', 'n/a')} trades / WR {feature_base.get('win_rate_pct', 'n/a')}% / PF {feature_base.get('profit_factor', 'n/a')} / net {feature_base.get('net_usd', 'n/a')} / positive days {feature_base.get('positive_day_pct', 'n/a')}%` |",
                f"| Review-candidate filters | `{feature_loss.get('feature_filter_review_candidate_count', 'n/a')}` |",
                f"| Best decision | `{feature_filter.get('decision', '')}` |",
                f"| Best block rule | `{feature_filter.get('direction_filter', '')} {feature_filter.get('feature', '')} {feature_filter.get('op', '')} {feature_filter.get('threshold', '')}` |",
                f"| Raw blocked trades | `{feature_filter.get('blocked_raw_trades', 'n/a')}` |",
                f"| Guarded result | `{feature_filter.get('trades', 'n/a')} trades / WR {feature_filter.get('win_rate_pct', 'n/a')}% / PF {feature_filter.get('profit_factor', 'n/a')} / net {feature_filter.get('net_usd', 'n/a')}` |",
                f"| Active-day shape | `{feature_filter.get('active_days', 'n/a')} active days / {feature_filter.get('trades_per_active_day', 'n/a')} trades per active day / {feature_filter.get('three_plus_trade_day_pct', 'n/a')}% 3+ trade days / {feature_filter.get('positive_day_pct', 'n/a')}% positive days` |",
                f"| Positive-day delta | `{feature_filter.get('positive_day_delta', 'n/a')} percentage points` |",
                f"| Top100 removed USD | `{feature_filter.get('top100_removed_usd', 'n/a')}` |",
                f"| Recommendation | `{feature_loss.get('recommendation', '')}` |",
                f"| Report | `{feature_loss.get('report', '')}` |",
                f"| Filter CSV | `{feature_loss.get('filter_csv', '')}` |",
                f"| Bin CSV | `{feature_loss.get('bin_csv', '')}` |",
            ]
        )
    feature_loss_portfolio = momentum.get("feature_loss_portfolio_verdict", {})
    feature_loss_portfolio_summary = (
        feature_loss_portfolio.get("best_summary", {}) if isinstance(feature_loss_portfolio, dict) else {}
    )
    if feature_loss_portfolio:
        lines.extend(
            [
                "",
                "### A1 Momentum Feature-Loss Portfolio Verdict",
                "",
                "This uses exact MT5 trade CSVs from the new default-off feature-loss EA variant and checks the portfolio-shaped goal: enough trades per active day, better win rate/PF, and better active-day positivity.",
                "",
                "| Field | Portfolio result |",
                "| --- | --- |",
                f"| Status | `{feature_loss_portfolio.get('status', 'MISSING')}` |",
                f"| Best portfolio | `{feature_loss_portfolio_summary.get('name', '')}` |",
                f"| Decision | `{feature_loss_portfolio_summary.get('decision', '')}` |",
                f"| Members | `{', '.join(feature_loss_portfolio_summary.get('members', []))}` |",
                f"| Result | `{feature_loss_portfolio_summary.get('trades', 'n/a')} trades / WR {feature_loss_portfolio_summary.get('win_rate_pct', 'n/a')}% / PF {feature_loss_portfolio_summary.get('profit_factor', 'n/a')} / net {feature_loss_portfolio_summary.get('net_usd', 'n/a')}` |",
                f"| Active-day shape | `{feature_loss_portfolio_summary.get('active_days', 'n/a')} active days / {feature_loss_portfolio_summary.get('trades_per_active_day', 'n/a')} trades per active day / {feature_loss_portfolio_summary.get('three_plus_trade_day_pct', 'n/a')}% 3+ trade days / {feature_loss_portfolio_summary.get('positive_day_pct', 'n/a')}% positive days` |",
                f"| Month stability | `{feature_loss_portfolio_summary.get('positive_months', 'n/a')} positive / {feature_loss_portfolio_summary.get('negative_months', 'n/a')} negative months` |",
                f"| Robustness | `top100 removed {feature_loss_portfolio_summary.get('top100_removed_usd', 'n/a')} / DD {feature_loss_portfolio_summary.get('max_closed_drawdown_usd', 'n/a')}` |",
                f"| Recommendation | `{feature_loss_portfolio.get('recommendation', '')}` |",
                f"| Report | `{feature_loss_portfolio.get('report', '')}` |",
            ]
        )
    feature_loss_guard_optimizer = momentum.get("feature_loss_daily_guard_optimizer", {})
    feature_loss_guard_summary = (
        feature_loss_guard_optimizer.get("best_summary", {}) if isinstance(feature_loss_guard_optimizer, dict) else {}
    )
    feature_loss_guard_guard = feature_loss_guard_summary.get("guard", {}) if isinstance(feature_loss_guard_summary, dict) else {}
    if feature_loss_guard_optimizer:
        lines.extend(
            [
                "",
                "### A1 Momentum Feature-Loss Daily Guard Optimizer",
                "",
                "This keeps the entry family fixed and searches daily lifecycle controls around the feature-loss portfolio. The goal is not sparse PF; it is a frequent intraday engine with better day-to-day reliability.",
                "",
                "| Field | Optimizer result |",
                "| --- | --- |",
                f"| Status | `{feature_loss_guard_optimizer.get('status', 'MISSING')}` |",
                f"| Searched rows | `{feature_loss_guard_optimizer.get('searched_rows', 'n/a')}` |",
                f"| Decision | `{feature_loss_guard_summary.get('decision', '')}` |",
                f"| Threshold | `{feature_loss_guard_summary.get('threshold_label', '')}` |",
                f"| Guard | `target={feature_loss_guard_summary.get('profit_target_usd')}, loss={feature_loss_guard_summary.get('loss_stop_usd')}, max_trades={feature_loss_guard_summary.get('max_trades_per_day_guard')}, max_losses={feature_loss_guard_summary.get('max_losses_per_day_guard')}` |",
                f"| Result | `{feature_loss_guard_summary.get('trades', 'n/a')} trades / WR {feature_loss_guard_summary.get('win_rate_pct', 'n/a')}% / PF {feature_loss_guard_summary.get('profit_factor', 'n/a')} / net {feature_loss_guard_summary.get('net_usd', 'n/a')}` |",
                f"| Active-day shape | `{feature_loss_guard_summary.get('active_days', 'n/a')} active days / {feature_loss_guard_summary.get('trades_per_active_day', 'n/a')} trades per active day / {feature_loss_guard_summary.get('three_plus_trade_day_pct', 'n/a')}% 3+ trade days / {feature_loss_guard_summary.get('positive_day_pct', 'n/a')}% positive days` |",
                f"| Month stability | `{feature_loss_guard_summary.get('positive_months', 'n/a')} positive / {feature_loss_guard_summary.get('negative_months', 'n/a')} negative months` |",
                f"| Robustness | `top100 removed {feature_loss_guard_summary.get('top100_removed_usd', 'n/a')} / DD {feature_loss_guard_summary.get('max_closed_drawdown_usd', 'n/a')}` |",
                f"| Guard hits | `skipped {feature_loss_guard_guard.get('skipped_trades', 'n/a')} / loss-stop days {feature_loss_guard_guard.get('loss_stop_days', 'n/a')} / trade-cap days {feature_loss_guard_guard.get('trade_cap_days', 'n/a')}` |",
                f"| Recommendation | `{feature_loss_guard_optimizer.get('recommendation', '')}` |",
                f"| Report | `{feature_loss_guard_optimizer.get('report', '')}` |",
                f"| CSV | `{feature_loss_guard_optimizer.get('csv', '')}` |",
            ]
        )
    feature_pair_filter = momentum.get("feature_pair_filter_search", {})
    feature_pair_summary = (
        feature_pair_filter.get("best_summary", {}) if isinstance(feature_pair_filter, dict) else {}
    )
    feature_pair_base = (
        feature_pair_filter.get("base_summary", {}) if isinstance(feature_pair_filter, dict) else {}
    )
    if feature_pair_filter:
        lines.extend(
            [
                "",
                "### A1 Momentum Feature-Pair Filter Search",
                "",
                "This keeps the frequent feature-loss portfolio intact, then checks whether one more signal-feature block can improve daily reliability without shrinking the engine below the multiple-trades/day requirement.",
                "",
                "| Field | Feature-pair result |",
                "| --- | --- |",
                f"| Status | `{feature_pair_filter.get('status', 'MISSING')}` |",
                f"| Review candidates | `{feature_pair_filter.get('review_candidate_count', 'n/a')}` |",
                f"| Baseline | `{feature_pair_base.get('trades', 'n/a')} trades / WR {feature_pair_base.get('win_rate_pct', 'n/a')}% / PF {feature_pair_base.get('profit_factor', 'n/a')} / {feature_pair_base.get('trades_per_active_day', 'n/a')} trades per active day / {feature_pair_base.get('positive_day_pct', 'n/a')}% positive days` |",
                f"| Best rule | `{feature_pair_summary.get('filter_rule', '')}` |",
                f"| Decision | `{feature_pair_summary.get('decision', '')}` |",
                f"| Result | `{feature_pair_summary.get('trades', 'n/a')} trades / WR {feature_pair_summary.get('win_rate_pct', 'n/a')}% / PF {feature_pair_summary.get('profit_factor', 'n/a')} / net {feature_pair_summary.get('net_usd', 'n/a')}` |",
                f"| Active-day shape | `{feature_pair_summary.get('active_days', 'n/a')} active days / {feature_pair_summary.get('trades_per_active_day', 'n/a')} trades per active day / {feature_pair_summary.get('three_plus_trade_day_pct', 'n/a')}% 3+ trade days / {feature_pair_summary.get('positive_day_pct', 'n/a')}% positive days` |",
                f"| Month stability | `{feature_pair_summary.get('positive_months', 'n/a')} positive / {feature_pair_summary.get('negative_months', 'n/a')} negative months` |",
                f"| Robustness | `top100 removed {feature_pair_summary.get('top100_removed_usd', 'n/a')} / DD {feature_pair_summary.get('max_closed_drawdown_usd', 'n/a')}` |",
                f"| Recommendation | `{feature_pair_filter.get('recommendation', '')}` |",
                f"| Report | `{feature_pair_filter.get('report', '')}` |",
                f"| CSV | `{feature_pair_filter.get('csv', '')}` |",
            ]
        )
    daily_income = momentum.get("feature_band_daily_income_tradeoff", {})
    daily_income_summary = (
        daily_income.get("owner_target_50_candidate", {})
        or daily_income.get("balanced_daily_income_candidate", {})
        if isinstance(daily_income, dict)
        else {}
    )
    fallback_daily_income_summary = (
        daily_income.get("balanced_daily_income_candidate", {}) if isinstance(daily_income, dict) else {}
    )
    max_net_summary = daily_income.get("max_net", {}) if isinstance(daily_income, dict) else {}
    if daily_income:
        lines.extend(
            [
                "",
                "### A1 Momentum Feature-Band Daily-Income Tradeoff",
                "",
                "This compares the max-net feature-band package with the owner-target daily-income guard shape. The headline daily-income version uses a +50 USD package target and max 6 package trades/day without falling below the multiple-trades/day requirement.",
                "",
                "| Field | Daily-income result |",
                "| --- | --- |",
                f"| Status | `{daily_income.get('status', 'MISSING')}` |",
                f"| Eligible rows | `{daily_income.get('eligible_count', 'n/a')}` |",
                f"| Max-net reference | `{max_net_summary.get('trades', 'n/a')} trades / WR {max_net_summary.get('win_rate_pct', 'n/a')}% / PF {max_net_summary.get('profit_factor', 'n/a')} / net {max_net_summary.get('net_usd', 'n/a')} / {max_net_summary.get('positive_day_pct', 'n/a')}% positive days` |",
                f"| Owner-target guard | `{daily_income_summary.get('guard_label', '')}` |",
                f"| Result | `{daily_income_summary.get('trades', 'n/a')} trades / WR {daily_income_summary.get('win_rate_pct', 'n/a')}% / PF {daily_income_summary.get('profit_factor', 'n/a')} / net {daily_income_summary.get('net_usd', 'n/a')}` |",
                f"| Active-day shape | `{daily_income_summary.get('active_days', 'n/a')} active days / {daily_income_summary.get('trades_per_active_day', 'n/a')} trades per active day / {daily_income_summary.get('three_plus_trade_day_pct', 'n/a')}% 3+ trade days / {daily_income_summary.get('positive_day_pct', 'n/a')}% positive days` |",
                f"| Month stability | `{daily_income_summary.get('positive_months', 'n/a')} positive / {daily_income_summary.get('negative_months', 'n/a')} negative months` |",
                f"| Robustness | `top100 removed {daily_income_summary.get('top100_removed_usd', 'n/a')} / DD {daily_income_summary.get('max_closed_drawdown_usd', 'n/a')}` |",
                f"| Smoother +25 fallback | `{fallback_daily_income_summary.get('trades', 'n/a')} trades / {fallback_daily_income_summary.get('positive_day_pct', 'n/a')}% positive days / net {fallback_daily_income_summary.get('net_usd', 'n/a')}` |",
                f"| Recommendation | `{daily_income.get('recommendation', '')}` |",
                f"| Forward draft | `{daily_income.get('forward_draft', '')}` |",
                f"| Report | `{daily_income.get('report', '')}` |",
                f"| CSV | `{daily_income.get('csv', '')}` |",
            ]
        )
    daily_income_readiness = momentum.get("feature_band_daily_income_readiness", {})
    if daily_income_readiness:
        planned = daily_income_readiness.get("planned_variants", {})
        planned_text = ", ".join(
            f"{name}:{data.get('magic')}" for name, data in planned.items() if isinstance(data, dict)
        )
        lines.extend(
            [
                "",
                "### A1 Momentum Feature-Band Daily-Income Readiness",
                "",
                "| Field | Readiness |",
                "| --- | --- |",
                f"| Status | `{daily_income_readiness.get('status', 'MISSING')}` |",
                f"| Decision | `{daily_income_readiness.get('decision', '')}` |",
                f"| Draft SHA256 | `{daily_income_readiness.get('draft_sha256', '')}` |",
                f"| Planned magics | `{planned_text}` |",
                f"| Report | `{daily_income_readiness.get('report', '')}` |",
                f"| JSON | `{daily_income_readiness.get('json', '')}` |",
            ]
        )
    daily_reliability = momentum.get("feature_band_day_state_search", {})
    reliability_readiness = momentum.get("feature_band_daily_reliability_readiness", {})
    if daily_reliability or reliability_readiness:
        best = daily_reliability.get("best", {}) if isinstance(daily_reliability, dict) else {}
        planned = reliability_readiness.get("planned_variants", {}) if isinstance(reliability_readiness, dict) else {}
        planned_text = ", ".join(
            f"{name}:{data.get('magic')}" for name, data in planned.items() if isinstance(data, dict)
        )
        lines.extend(
            [
                "",
                "### A1 Momentum Feature-Band Daily-Reliability Candidate",
                "",
                "This is the frequency-aligned candidate: it keeps the +50 USD / max 6 package shape, then adds a 15-minute package cooldown after a closed package loss. It is review-ready and not attached.",
                "",
                "| Field | Daily-reliability result |",
                "| --- | --- |",
                f"| Day-state status | `{daily_reliability.get('status', 'MISSING')}` |",
                f"| Best row | `{best.get('name', '')}` |",
                f"| Decision | `{best.get('decision', '')}` |",
                f"| Result | `{best.get('trades', 'n/a')} trades / WR {best.get('win_rate_pct', 'n/a')}% / PF {best.get('profit_factor', 'n/a')} / net {best.get('net_usd', 'n/a')}` |",
                f"| Active-day shape | `{best.get('active_days', 'n/a')} active days / {best.get('trades_per_active_day', 'n/a')} trades per active day / {best.get('three_plus_trade_day_pct', 'n/a')}% 3+ trade days / {best.get('positive_day_pct', 'n/a')}% positive days` |",
                f"| Robustness | `top100 removed {best.get('top100_removed_usd', 'n/a')} / DD {best.get('max_closed_drawdown_usd', 'n/a')}` |",
                f"| Readiness | `{reliability_readiness.get('status', 'MISSING')}` |",
                f"| Draft SHA256 | `{reliability_readiness.get('draft_sha256', '')}` |",
                f"| Planned magics | `{planned_text}` |",
                f"| Forward draft | `{reliability_readiness.get('forward_draft', '')}` |",
                f"| Report | `{reliability_readiness.get('report', '')}` |",
                f"| CSV | `{daily_reliability.get('csv', '')}` |",
            ]
        )
    residual = momentum.get("feature_band_residual_search", {})
    residual_stress = momentum.get("feature_band_residual_stress", {})
    residual_optimizer = momentum.get("feature_band_residual_package_optimizer", {})
    plus50_cooldown10 = momentum.get("feature_band_residual_plus50_cooldown10_readiness", {})
    plus75_high_net = momentum.get("feature_band_residual_plus75_high_net_readiness", {})
    business_scoreboard = momentum.get("business_goal_scoreboard", {})
    residual_readiness = momentum.get("feature_band_residual_reliability_readiness", {})
    if residual or residual_readiness:
        baseline = residual.get("baseline", {}) if isinstance(residual, dict) else {}
        best = residual.get("best", {}) if isinstance(residual, dict) else {}
        stressed = residual_stress.get("residual", {}) if isinstance(residual_stress, dict) else {}
        named = residual_optimizer.get("named_candidates", {}) if isinstance(residual_optimizer, dict) else {}
        owner_target_50 = named.get("owner_target_50", {}) if isinstance(named, dict) else {}
        max_net = named.get("max_net", {}) if isinstance(named, dict) else {}
        max_positive_day = named.get("max_positive_day", {}) if isinstance(named, dict) else {}
        plus50_candidate = plus50_cooldown10.get("candidate", {}) if isinstance(plus50_cooldown10, dict) else {}
        plus50_planned = plus50_cooldown10.get("planned_variants", {}) if isinstance(plus50_cooldown10, dict) else {}
        plus50_planned_text = ", ".join(
            f"{name}:{data.get('magic')}" for name, data in plus50_planned.items() if isinstance(data, dict)
        )
        plus75_candidate = plus75_high_net.get("candidate", {}) if isinstance(plus75_high_net, dict) else {}
        plus75_planned = plus75_high_net.get("planned_variants", {}) if isinstance(plus75_high_net, dict) else {}
        plus75_planned_text = ", ".join(
            f"{name}:{data.get('magic')}" for name, data in plus75_planned.items() if isinstance(data, dict)
        )
        planned = residual_readiness.get("planned_variants", {}) if isinstance(residual_readiness, dict) else {}
        planned_text = ", ".join(
            f"{name}:{data.get('magic')}" for name, data in planned.items() if isinstance(data, dict)
        )
        lines.extend(
            [
                "",
                "### A1 Momentum Feature-Band Residual-Reliability Candidate",
                "",
                "This keeps the frequent daily-reliability package and adds two residual blocks: LONG server hour 18 and SHORT close-to-recent-extreme >= -0.92. It is review-ready and not attached.",
                "",
                "| Field | Residual-reliability result |",
                "| --- | --- |",
                f"| Search status | `{residual.get('status', 'MISSING')}` |",
                f"| Best row | `{best.get('filter_name', '')}` |",
                f"| Decision | `{best.get('decision', '')}` |",
                f"| Baseline | `{baseline.get('trades', 'n/a')} trades / WR {baseline.get('win_rate_pct', 'n/a')}% / PF {baseline.get('profit_factor', 'n/a')} / net {baseline.get('net_usd', 'n/a')} / {baseline.get('positive_day_pct', 'n/a')}% positive days` |",
                f"| Candidate | `{best.get('trades', 'n/a')} trades / WR {best.get('win_rate_pct', 'n/a')}% / PF {best.get('profit_factor', 'n/a')} / net {best.get('net_usd', 'n/a')} / {best.get('positive_day_pct', 'n/a')}% positive days` |",
                f"| Active-day shape | `{best.get('active_days', 'n/a')} active days / {best.get('trades_per_active_day', 'n/a')} trades per active day / {best.get('three_plus_trade_day_pct', 'n/a')}% 3+ trade days` |",
                f"| Robustness | `top100 removed {best.get('top100_removed_usd', 'n/a')} / DD {best.get('max_closed_drawdown_usd', 'n/a')}` |",
                f"| Stress status | `{residual_stress.get('status', 'MISSING')}` |",
                f"| Stress cadence | `{stressed.get('trades', 'n/a')} trades / {stressed.get('trades_per_active_day', 'n/a')} trades per active day / {stressed.get('two_plus_trade_day_pct', 'n/a')}% 2+ days / {stressed.get('three_plus_trade_day_pct', 'n/a')}% 3+ days` |",
                f"| Stress robustness | `top100 removed {stressed.get('top100_removed_usd', 'n/a')} / top200 removed {stressed.get('top200_removed_usd', 'n/a')} / older-newer {stressed.get('older_net_usd', 'n/a')} and {stressed.get('newer_net_usd', 'n/a')}` |",
                f"| Package optimizer | `{residual_optimizer.get('status', 'MISSING')}` / searched `{residual_optimizer.get('searched_rows', 'n/a')}` rows |",
                f"| Best +50 target row | `{owner_target_50.get('trades', 'n/a')} trades / WR {owner_target_50.get('win_rate_pct', 'n/a')}% / PF {owner_target_50.get('profit_factor', 'n/a')} / net {owner_target_50.get('net_usd', 'n/a')} / {owner_target_50.get('positive_day_pct', 'n/a')}% positive days / cooldown {owner_target_50.get('cooldown_after_loss_minutes', 'n/a')}m` |",
                f"| Best net row | `{max_net.get('trades', 'n/a')} trades / WR {max_net.get('win_rate_pct', 'n/a')}% / PF {max_net.get('profit_factor', 'n/a')} / net {max_net.get('net_usd', 'n/a')} / {max_net.get('positive_day_pct', 'n/a')}% positive days` |",
                f"| Best positive-day row | `{max_positive_day.get('trades', 'n/a')} trades / WR {max_positive_day.get('win_rate_pct', 'n/a')}% / PF {max_positive_day.get('profit_factor', 'n/a')} / net {max_positive_day.get('net_usd', 'n/a')} / {max_positive_day.get('positive_day_pct', 'n/a')}% positive days` |",
                f"| Preferred +50/10m readiness | `{plus50_cooldown10.get('status', 'MISSING')}` |",
                f"| Preferred +50/10m candidate | `{plus50_candidate.get('trades', 'n/a')} trades / WR {plus50_candidate.get('win_rate_pct', 'n/a')}% / PF {plus50_candidate.get('profit_factor', 'n/a')} / net {plus50_candidate.get('net_usd', 'n/a')} / {plus50_candidate.get('positive_day_pct', 'n/a')}% positive days / cooldown {plus50_candidate.get('cooldown_after_loss_minutes', 'n/a')}m` |",
                f"| Preferred +50/10m magics | `{plus50_planned_text}` |",
                f"| Preferred +50/10m draft SHA256 | `{plus50_cooldown10.get('draft_sha256', '')}` |",
                f"| High-net +75 readiness | `{plus75_high_net.get('status', 'MISSING')}` |",
                f"| High-net +75 candidate | `{plus75_candidate.get('trades', 'n/a')} trades / WR {plus75_candidate.get('win_rate_pct', 'n/a')}% / PF {plus75_candidate.get('profit_factor', 'n/a')} / net {plus75_candidate.get('net_usd', 'n/a')} / {plus75_candidate.get('trades_per_active_day', 'n/a')} trades per active day / {plus75_candidate.get('positive_day_pct', 'n/a')}% positive days` |",
                f"| High-net +75 magics | `{plus75_planned_text}` |",
                f"| High-net +75 draft SHA256 | `{plus75_high_net.get('draft_sha256', '')}` |",
                f"| Readiness | `{residual_readiness.get('status', 'MISSING')}` |",
                f"| Draft SHA256 | `{residual_readiness.get('draft_sha256', '')}` |",
                f"| Planned magics | `{planned_text}` |",
                f"| Forward draft | `{residual_readiness.get('forward_draft', '')}` |",
                f"| Report | `{residual_readiness.get('report', '')}` |",
                f"| Stress report | `{residual_stress.get('report', '')}` |",
                f"| Package optimizer report | `{residual_optimizer.get('report', '')}` |",
                f"| Preferred +50/10m report | `{plus50_cooldown10.get('report', '')}` |",
                f"| Preferred +50/10m forward draft | `{plus50_cooldown10.get('forward_draft', '')}` |",
                f"| High-net +75 report | `{plus75_high_net.get('report', '')}` |",
                f"| High-net +75 forward draft | `{plus75_high_net.get('forward_draft', '')}` |",
                f"| CSV | `{residual.get('csv', '')}` |",
            ]
        )
    if business_scoreboard:
        top = business_scoreboard.get("top_candidate", {})
        passing = business_scoreboard.get("passing_candidates", [])
        lines.extend(
            [
                "",
                "### A1 Momentum Business-Goal Scoreboard",
                "",
                "This table ranks candidates by the owner's stated objective: multiple trades per active day, win rate above 50%, positive PF/net, and enough robustness that the result is not just a sparse PF artifact.",
                "",
                "| Field | Value |",
                "| --- | --- |",
                f"| Status | `{business_scoreboard.get('status', 'MISSING')}` |",
                f"| Top candidate | `{top.get('name', '')}` |",
                f"| Top status | `{top.get('owner_goal_status', '')}` |",
                f"| Top metrics | `{top.get('trades', 'n/a')} trades / WR {top.get('win_rate_pct', 'n/a')}% / PF {top.get('profit_factor', 'n/a')} / net {top.get('net', 'n/a')} {top.get('unit', '')} / {top.get('trades_per_active_day', 'n/a')} trades per active day / {top.get('positive_day_pct', 'n/a')}% positive days` |",
                f"| Passing candidates | `{len(passing)}` |",
                f"| Report | `{business_scoreboard.get('report', '')}` |",
                f"| CSV | `{business_scoreboard.get('csv', '')}` |",
            ]
        )
    calendar_cadence = momentum.get("business_goal_calendar_cadence_audit", {})
    if calendar_cadence:
        date_window = calendar_cadence.get("date_window", {})
        candidates = calendar_cadence.get("candidates", [])
        lines.extend(
            [
                "",
                "### A1 Momentum Calendar Cadence Audit",
                "",
                "This audit prevents a subtle overclaim: active-day cadence is not the same as market-day cadence. The current candidates are frequent on days they fire, but quiet market days still exist.",
                "",
                "| Field | Value |",
                "| --- | --- |",
                f"| Status | `{calendar_cadence.get('status', 'MISSING')}` |",
                f"| Window | `{date_window.get('start', '')} -> {date_window.get('end', '')}` |",
                f"| Weekday market days | `{date_window.get('market_days', 'n/a')}` |",
            ]
        )
        for candidate in candidates:
            lines.extend(
                [
                    f"| `{candidate.get('name', '')}` decision | `{candidate.get('decision', '')}` |",
                    f"| `{candidate.get('name', '')}` cadence | `{candidate.get('trades', 'n/a')} trades / {candidate.get('trades_per_market_day', 'n/a')} trades per market day / {candidate.get('trades_per_active_day', 'n/a')} trades per active day / {candidate.get('three_plus_market_day_pct', 'n/a')}% 3+ market days` |",
                ]
            )
        lines.extend(
            [
                f"| Report | `{calendar_cadence.get('report', '')}` |",
                f"| JSON | `{calendar_cadence.get('json', '')}` |",
            ]
        )
    market_day_coverage = momentum.get("business_goal_market_day_coverage_search", {})
    if market_day_coverage:
        best = market_day_coverage.get("best_result", {})
        lines.extend(
            [
                "",
                "### A1 Momentum Market-Day Coverage Search",
                "",
                "This search answers the owner's stricter objection: a candidate should not only look good on active days, it should produce multiple trades across the actual weekday market calendar. The result is still a review candidate, not a runtime approval.",
                "",
                "| Field | Value |",
                "| --- | --- |",
                f"| Status | `{market_day_coverage.get('status', 'MISSING')}` |",
                f"| Best candidate | `{best.get('portfolio_name', '')}` |",
                f"| Guard | `{best.get('guard_name', '')}` |",
                f"| Decision | `{best.get('decision', '')}` |",
                f"| Metrics | `{best.get('trades', 'n/a')} trades / WR {best.get('win_rate_pct', 'n/a')}% / PF {best.get('profit_factor', 'n/a')} / net {best.get('net_usd', 'n/a')} / {best.get('trades_per_market_day', 'n/a')} trades per market day / {best.get('trades_per_active_day', 'n/a')} trades per active day / {best.get('three_plus_market_day_pct', 'n/a')}% 3+ market days` |",
                f"| Robustness | `top100 removed {best.get('top100_removed_usd', 'n/a')} / top200 removed {best.get('top200_removed_usd', 'n/a')}` |",
                f"| Duplicate control | `{best.get('duplicate_drops', 'n/a')} same-direction 5m duplicate drops before scoring` |",
                f"| Report | `{market_day_coverage.get('report', '')}` |",
                f"| CSV | `{market_day_coverage.get('csv', '')}` |",
            ]
        )
    market_day_stress = momentum.get("business_goal_market_day_coverage_stress", {})
    if market_day_stress:
        stress_summary = market_day_stress.get("summary", {})
        rolling = market_day_stress.get("rolling", [])
        rolling_read = "; ".join(
            f"{row.get('window')}tr negative={row.get('negative_windows', 'n/a')} pf_lt_1={row.get('pf_below_1_windows', 'n/a')}"
            for row in rolling
        )
        lines.extend(
            [
                "",
                "### A1 Momentum Market-Day Coverage Stress",
                "",
                "This stress report checks whether the higher-cadence market-day candidate survives beyond the headline search score. It is still review evidence, not runtime approval.",
                "",
                "| Field | Value |",
                "| --- | --- |",
                f"| Status | `{market_day_stress.get('status', 'MISSING')}` |",
                f"| Decision | `{market_day_stress.get('decision', '')}` |",
                f"| Metrics | `{stress_summary.get('trades', 'n/a')} trades / WR {stress_summary.get('win_rate_pct', 'n/a')}% / PF {stress_summary.get('profit_factor', 'n/a')} / net {stress_summary.get('net_usd', 'n/a')} / {stress_summary.get('trades_per_market_day', 'n/a')} trades per market day / top300 removed {stress_summary.get('top300_removed_usd', 'n/a')}` |",
                f"| Rolling windows | `{rolling_read}` |",
                f"| Report | `{market_day_stress.get('report', '')}` |",
                f"| Selected trades CSV | `{market_day_stress.get('selected_trades_csv', '')}` |",
            ]
        )
    promotion_packet = momentum.get("business_goal_promotion_packet", {})
    if promotion_packet:
        rules = promotion_packet.get("forward_demo_rules", {})
        lines.extend(
            [
                "",
                "### A1 Momentum Business-Goal Promotion Packet",
                "",
                "This packet converts the scoreboard into an owner/reviewer decision: replace the sparse RR2 lane with the highest-ranked frequent package only after approval.",
                "",
                "| Field | Value |",
                "| --- | --- |",
                f"| Status | `{promotion_packet.get('status', 'MISSING')}` |",
                f"| Recommended primary | `{promotion_packet.get('recommended_primary', '')}` |",
                f"| Recommended fallback | `{promotion_packet.get('recommended_fallback', '')}` |",
                f"| Decision boundary | `{promotion_packet.get('decision', '')}` |",
                f"| Magics | `{rules.get('magics', '')}` |",
                f"| Package guard | `{rules.get('package_guard', '')}` |",
                f"| Forward pass rule | `{rules.get('pass_rule', '')}` |",
                f"| Forward kill rule | `{rules.get('kill_rule', '')}` |",
                f"| Report | `{promotion_packet.get('report', '')}` |",
                "| Owner authorization | `xau-usd/xauusd-phase1/docs/A1_MOMENTUM_BUSINESS_GOAL_OWNER_AUTHORIZATION_2026_07_02.md` |",
                "| Claude review prompt | `CLAUDE_REVIEW_PROMPT_A1_MOMENTUM_BUSINESS_GOAL_PROMOTION_2026_07_02.md` |",
            ]
        )
    momentum_backtest = momentum.get("mt5_backtest", {})
    if momentum_backtest:
        lines.extend(
            [
                "",
                "### A1 Momentum MT5 Backtest",
                "",
                "| Field | Value |",
                "| --- | --- |",
                f"| Status | `{momentum_backtest.get('status', 'MISSING')}` |",
                f"| Period | `{momentum_backtest.get('period', '')}` |",
                f"| Net PnL AED | `{momentum_backtest.get('net_profit_aed', 'n/a')}` |",
                f"| Profit factor | `{momentum_backtest.get('profit_factor', 'n/a')}` |",
                f"| Win rate | `{momentum_backtest.get('win_rate_pct', 'n/a')}%` |",
                f"| Trades | `{momentum_backtest.get('trades', 'n/a')}` |",
                f"| Short net AED | `{momentum_backtest.get('short_net_profit_aed', 'n/a')}` |",
                f"| Long net AED | `{momentum_backtest.get('long_net_profit_aed', 'n/a')}` |",
                f"| Decision | `{momentum_backtest.get('decision', '')}` |",
                f"| Report | `{momentum_backtest.get('report', '')}` |",
            ]
        )
    momentum_variant_backtest = momentum.get("variant_mt5_backtest", {})
    if momentum_variant_backtest:
        lines.extend(
            [
                "",
                "### A1 Momentum Variant MT5 Backtests",
                "",
                "| Field | Value |",
                "| --- | --- |",
                f"| Status | `{momentum_variant_backtest.get('status', 'MISSING')}` |",
                f"| Best diagnostic variant | `{momentum_variant_backtest.get('best_variant', '')}` |",
                f"| Variant count | `{momentum_variant_backtest.get('variant_count', 'n/a')}` |",
                f"| Note | `{momentum_variant_backtest.get('note', '')}` |",
                f"| Report | `{momentum_variant_backtest.get('report', '')}` |",
                f"| Diagnosis | `{momentum_variant_backtest.get('diagnosis_report', '')}` |",
            ]
        )
    momentum_frequency_repair = momentum.get("frequency_first_repair", {})
    if momentum_frequency_repair:
        lines.extend(
            [
                "",
                "### A1 Momentum Frequency-First Repair",
                "",
                "This is a diagnostic repair screen for the original high-frequency goal; it is not the currently attached sparse RR2 lane.",
                "",
                "| Field | Value |",
                "| --- | --- |",
                f"| Status | `{momentum_frequency_repair.get('status', 'MISSING')}` |",
                f"| Trades | `{momentum_frequency_repair.get('trades', 'n/a')}` |",
                f"| Win rate | `{momentum_frequency_repair.get('win_rate_pct', 'n/a')}%` |",
                f"| Net PnL USD | `{momentum_frequency_repair.get('net_profit_usd', 'n/a')}` |",
                f"| Profit factor | `{momentum_frequency_repair.get('profit_factor', 'n/a')}` |",
                f"| Avg USD/trade | `{momentum_frequency_repair.get('avg_usd_per_trade', 'n/a')}` |",
                f"| Meets frequency goal | `{momentum_frequency_repair.get('meets_frequency_goal', 'n/a')}` |",
                f"| Meets win-rate goal | `{momentum_frequency_repair.get('meets_winrate_goal', 'n/a')}` |",
                f"| Ready for live | `{momentum_frequency_repair.get('ready_for_live', 'n/a')}` |",
                f"| Next action | `{momentum_frequency_repair.get('next_action', '')}` |",
                f"| Report | `{momentum_frequency_repair.get('report', '')}` |",
            ]
        )
    a3 = accounts["A3"]
    a3_summary = a3.get("review_followup_summary", {})
    runtime_state = a3.get("current_runtime_state", {})
    runtime_lanes = runtime_state.get("lanes", {}) if isinstance(runtime_state, dict) else {}
    historical_authorization = a3.get("historical_owner_authorization", {})
    test_suite = a3.get("test_suite_status", {})
    lines.extend(
        [
            "",
            "## A3 Runtime Decision",
            "",
            f"Effective runtime authorization: `{a3.get('effective_runtime_authorization', 'MISSING')}`",
            f"Runtime snapshot UTC: `{a3.get('runtime_snapshot_at_utc', 'MISSING')}`",
            f"Open positions: `{runtime_state.get('open_positions', 'n/a') if isinstance(runtime_state, dict) else 'n/a'}`",
            f"Pending orders: `{runtime_state.get('pending_orders', 'n/a') if isinstance(runtime_state, dict) else 'n/a'}`",
            f"Artifact integrity: `{a3.get('artifact_integrity_status', 'MISSING')}`",
            f"Runtime performance: `{a3.get('runtime_performance_status', 'MISSING')}`",
            f"Shadow candidate performance: `{a3.get('shadow_candidate_performance_status', 'MISSING')}`",
            f"Pause artifact/runtime consistency: `{a3.get('pause_artifact_runtime_consistency_status', 'MISSING')}`",
            f"Emergency pause report: `{a3.get('emergency_pause_status', 'MISSING')}`",
            f"Test suite: `{test_suite.get('status', 'UNKNOWN')}` ({test_suite.get('passed', 'n/a')} passed, {test_suite.get('failed', 'n/a')} failed)",
            f"Family mutex: `{a3.get('family_mutex_status', 'MISSING')}`",
            f"Containment: `{a3.get('containment_status', 'MISSING')}`",
            f"Shadow hypothesis: `{a3.get('shadow_hypothesis_status', 'MISSING')}`",
            f"Reactivation gate: `{a3.get('reactivation_gate_status', 'MISSING')}`",
            "",
            "| Runtime lane | Current state |",
            "| --- | --- |",
            f"| `933200` plain | `{runtime_lanes.get('933200', 'MISSING')}` |",
            f"| `933300` improved | `{runtime_lanes.get('933300', 'MISSING')}` |",
            f"| `933400` Tier1 compat | `{runtime_lanes.get('933400', 'MISSING')}` |",
            f"| Profit-lock manager | `{runtime_lanes.get('profit_lock', 'MISSING')}` |",
            "",
            "## A3 Historical Authorization",
            "",
            f"Tier1 `933400` owner authorization: `{historical_authorization.get('933400_demo_broker_action', 'MISSING')}`",
            f"Current permission of that authorization: `{historical_authorization.get('current_permission', 'MISSING')}`",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
            f"| Closed trades | `{a3_summary.get('closed_trades', 'n/a')}` |",
            f"| Wins | `{a3_summary.get('wins', 'n/a')}` |",
            f"| Losses | `{a3_summary.get('losses', 'n/a')}` |",
            f"| Net PnL AED | `{a3_summary.get('net_pnl_aed', 'n/a')}` |",
            f"| Duplicate events | `{a3_summary.get('duplicate_event_count', 'n/a')}` |",
            f"| Profit-lock actions | `{a3_summary.get('profit_lock_actions', 'n/a')}` |",
        ]
    )
    lines.extend(
        [
            "",
            "## Authorization Boundary",
            "",
            "| Item | Value |",
            "| --- | --- |",
            f"| Canonical Phase 2 PASS | `{str(auth['canonical_phase2_pass']).lower()}` |",
            f"| Live trading authorized | `{str(auth['live_trading_authorized']).lower()}` |",
            f"| Real capital authorized | `{str(auth['real_capital_authorized']).lower()}` |",
            f"| A3 Tier-1 demo broker action | `{auth['a3_tier1_demo_broker_action']}` |",
            f"| A3 current runtime authorization | `{auth['a3_current_runtime_authorization']}` |",
            "",
            "## Next Evidence Required",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in summary["next_evidence_required"])
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a small audit-friendly project status summary.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    args = parser.parse_args(argv)
    json_path, md_path = generate_project_status_summary(args.repo_root, args.output_json, args.output_md)
    print(json_path)
    print(md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

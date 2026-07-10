from __future__ import annotations

import importlib.util
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_project_status_summary_records_account_boundaries(tmp_path: Path):
    repo = _repo_with_reports(tmp_path)
    module = _load_script("generate_project_status_summary")

    json_path, md_path = module.generate_project_status_summary(
        repo,
        now=datetime(2026, 6, 17, 12, 0, tzinfo=timezone.utc),
    )

    summary = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = md_path.read_text(encoding="utf-8")
    assert summary["schema_version"] == "project_status_summary_v2"
    assert summary["accounts"]["A1"]["round_quarantine_active"] is True
    assert summary["accounts"]["A1"]["touched_by_round_quarantine"] is True
    assert summary["accounts"]["A2"]["touched_by_round_quarantine"] is False
    assert summary["accounts"]["A3"]["touched_by_round_quarantine"] is False
    assert summary["quarantine"]["target_candidates"] == [
        "round_number_retest_v0",
        "symbol_normalized_round_retest_v0",
    ]
    assert summary["a3_tier1"]["owner_authorized_demo_broker_action"] is True
    assert "lane" not in summary["a3_tier1"]
    assert "status" not in summary["a3_tier1"]
    assert summary["a3_tier1"]["historical_attach_status"] == "PASS"
    assert summary["a3_tier1"]["runtime_performance_status"] == "FAIL"
    assert summary["a3_tier1"]["authorization_status"] == "A3_ENTRY_LANES_PAUSED"
    assert summary["a3_tier1"]["shadow_candidate_performance_status"] == "NOT_EVALUATED"
    assert summary["a3_tier1"]["historical_owner_authorization"]["933400_demo_broker_action"] == "OWNER_AUTHORIZED_DEMO_BROKER_ACTION"
    assert summary["a3_tier1"]["current_runtime_state"]["lanes"]["933400"] == "PAUSED"
    assert summary["a3_tier1"]["effective_runtime_authorization"] == "A3_ENTRY_LANES_PAUSED"
    assert summary["accounts"]["A3"]["pause_artifact_runtime_consistency_status"] == "PASS"
    assert summary["accounts"]["A3"]["next_allowed_transition"] == "P3 offline A3 signal-quality discovery screen; repo-only and no broker action."
    assert summary["accounts"]["A3"]["test_suite_status"]["passed"] == 425
    assert "A3_REPAIR_P1_P2_IMPLEMENTATION_REPORT_2026_06_18.json" in summary["accounts"]["A3"]["test_suite_status"]["source"]
    assert summary["next_evidence_required"] == [
        "SQ-01 hash-locked A3_SIGNAL_QUALITY_V1_IMPLEMENTATION_ADDENDUM_01.md",
        "SQ-02 hash-locked A3_SIGNAL_QUALITY_DIAGNOSTIC_SWEEP_V1_2026_06_18.md",
        "SQ-03 offline Python discovery sweep with frequency-quality and loss-attribution table",
        "Green CI run tied to the exact source commit before any shadow-terminal attachment",
        "A3 remains paused; no broker action, profile arming, or runtime attach before evidence gates pass",
        "A1 XAU M5 momentum-continuation lane: capture first magic 932200 order-log row or guard-block row after a valid break-and-run signal",
    ]
    assert summary["authorization"]["canonical_phase2_pass"] is False
    assert summary["authorization"]["live_trading_authorized"] is False
    assert "audit-friendly companion" in markdown
    assert "OWNER_AUTHORIZED_DEMO_BROKER_ACTION" in markdown
    assert "Effective runtime authorization: `A3_ENTRY_LANES_PAUSED`" in markdown


def test_forward_week_templates_are_pending_and_non_runtime(tmp_path: Path):
    repo = _repo_with_reports(tmp_path)
    module = _load_script("generate_xauusd_forward_week_evidence_templates")

    paths = module.generate_forward_week_evidence_templates(repo, report_date=date(2026, 6, 17))

    names = {path.name for path in paths}
    assert "XAUUSD_ROUND_FAMILY_FORWARD_WEEK_IMPACT_2026_06_17.md" in names
    assert "XAUUSD_PROTECTED_BREAKOUT_CORE_FORWARD_WEEK_2026_06_17.md" in names
    assert "XAUUSD_NON_ROUND_AFTERNOON_RESIDUAL_2026_06_17.md" in names
    assert "XAUUSD_ROUND_QUARANTINE_ROLLBACK_READINESS_2026_06_17.md" in names
    assert "A1_DIRECT_HISTORY_RECONCILIATION_2026_06_17.md" in names
    assert "A2_DIRECT_HISTORY_RECONCILIATION_2026_06_17.md" in names
    assert "A3_DIRECT_HISTORY_RECONCILIATION_2026_06_17.md" in names
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    assert "PENDING_FORWARD_WEEK" in combined
    assert "No runtime change is authorized" in combined
    assert "PENDING_DIRECT_MT5_REFRESH" in combined


def _repo_with_reports(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    reports = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    reports.mkdir(parents=True)
    (reports / "XAUUSD_ROUND_FAMILY_QUARANTINE_APPLIED_2026_06_17.json").write_text(
        json.dumps(
            {
                "status": "ROUND_FAMILY_QUARANTINE_APPLIED",
                "scope": {
                    "target_candidates": [
                        "round_number_retest_v0",
                        "symbol_normalized_round_retest_v0",
                    ]
                },
                "terminal": {"profile_backup_dir": "C:/backup"},
                "after_target_charts": [
                    {
                        "chart": "chart09.chr",
                        "symbol": "XAUUSD",
                        "candidate": "symbol_normalized_round_retest_v0",
                        "dry_run": "true",
                        "broker_action_allowed": "false",
                        "candidate_status": "OWNER_APPROVED_ROUND_FAMILY_QUARANTINED",
                    },
                    {
                        "chart": "chart11.chr",
                        "symbol": "XAUUSD",
                        "candidate": "round_number_retest_v0",
                        "dry_run": "true",
                        "broker_action_allowed": "false",
                        "candidate_status": "OWNER_APPROVED_ROUND_FAMILY_QUARANTINED",
                    },
                ],
                "after_protected_charts": [
                    {
                        "chart": "chart03.chr",
                        "symbol": "XAUUSD",
                        "candidate": "breakout_retest",
                        "dry_run": "false",
                        "broker_action_allowed": "true",
                        "candidate_status": "EXPERIMENTAL_QUARANTINE_REVIEW_ONLY",
                    },
                    {
                        "chart": "chart06.chr",
                        "symbol": "XAUUSD",
                        "candidate": "swing_breakout_retest_v0",
                        "dry_run": "false",
                        "broker_action_allowed": "true",
                        "candidate_status": "EXPERIMENTAL_QUARANTINE_REVIEW_ONLY",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (reports / "A3_TIER1_COMPAT_BROKER_ACTION_ATTACHMENT_2026_06_17.json").write_text(
        json.dumps(
            {
                "status": "PASS",
                "lane": {
                    "account_login": "1033669",
                    "broker_action_allowed": "true",
                    "dry_run": "false",
                    "symbol": "XAUUSD",
                    "magic": "933400",
                },
            }
        ),
        encoding="utf-8",
    )
    (reports / "A3_REVIEW_FOLLOWUP_STATUS_2026_06_18.json").write_text(
        json.dumps(
            {
                "status": "ARTIFACT_INTEGRITY_PASS",
                "artifact_integrity_status": "PASS",
                "runtime_performance_status": "FAIL",
                "runtime_authorization_status": "A3_ENTRY_LANES_PAUSED",
                "created_at_utc": "2026-06-18T07:44:27Z",
                "window_start_utc": "2026-06-16T00:00:00Z",
                "window_end_utc": "2026-06-18T07:44:27Z",
                "summary": {
                    "closed_trades": 23,
                    "wins": 1,
                    "losses": 22,
                    "net_pnl_aed": -758.79,
                    "duplicate_event_count": 5,
                    "profit_lock_actions": 0,
                },
                "per_magic": [
                    {"magic": "933200", "dry_run_now": "true", "broker_action_allowed_now": "false"},
                    {"magic": "933300", "dry_run_now": "true", "broker_action_allowed_now": "false"},
                    {"magic": "933400", "dry_run_now": "true", "broker_action_allowed_now": "false"},
                ],
                "chart_state": {
                    "chart05.chr": {
                        "expert": "Account3ProfitLockExitManager",
                        "dry_run": "true",
                        "manage_action_allowed": "false",
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    (reports / "A3_EMERGENCY_PAUSE_APPLIED_2026_06_18.json").write_text(
        json.dumps(
            {
                "status": "PASS",
                "created_at_utc": "2026-06-18T07:41:59Z",
                "runtime_authorization_status": "A3_ENTRY_LANES_PAUSED",
                "after_broker": {
                    "status": "PASS",
                    "a3_positions_total": 0,
                    "a3_orders_total": 0,
                },
            }
        ),
        encoding="utf-8",
    )
    (reports / "A3_REPAIR_P1_P2_IMPLEMENTATION_REPORT_2026_06_18.json").write_text(
        json.dumps(
            {
                "status": "PASS",
                "verification": {
                    "phase1_pytest": "425 passed",
                },
            }
        ),
        encoding="utf-8",
    )
    return repo


def _load_script(name: str):
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

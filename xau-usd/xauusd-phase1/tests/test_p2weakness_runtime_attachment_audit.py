from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_attachment_audit_flags_old_deployed_runtime(tmp_path):
    phase1_root = tmp_path / "phase1"
    terminal_root = tmp_path / "terminal"
    output_dir = tmp_path / "reports"
    repo_source = phase1_root / "mt5" / "Experts" / "Phase2WeaknessBreakoutRetestExecutor.mq5"
    deployed_source = terminal_root / "MQL5" / "Experts" / "Phase2WeaknessBreakoutRetestExecutor.mq5"
    chart_dir = terminal_root / "MQL5" / "Profiles" / "Charts" / "Default"
    files_dir = terminal_root / "MQL5" / "Files"
    repo_source.parent.mkdir(parents=True)
    deployed_source.parent.mkdir(parents=True)
    chart_dir.mkdir(parents=True)
    files_dir.mkdir(parents=True)
    (terminal_root / "terminal64.exe").write_text("", encoding="utf-8")
    repo_source.write_text(
        """
input bool InpDryRunOnly = true;
input bool InpBrokerActionAllowed = false;
input int InpMagicNumber = 931000;
""".strip(),
        encoding="utf-8",
    )
    deployed_source.write_text(
        """
input bool InpDryRunOnly = false;
input bool InpBrokerActionAllowed = true;
input int InpMagicNumber = 930101;
""".strip(),
        encoding="utf-8",
    )
    (chart_dir / "chart01.chr").write_text(
        """
<chart>
symbol=XAUUSD
<expert>
name=Phase2WeaknessBreakoutRetestExecutor
path=Experts\\Phase2WeaknessBreakoutRetestExecutor.ex5
InpDryRunOnly=false
InpBrokerActionAllowed=true
InpMagicNumber=930101
</expert>
</chart>
""".strip(),
        encoding="utf-8",
    )
    order_log = files_dir / "p2weakness_br_v1_order_log_xauusd.csv"
    startup_log = files_dir / "p2weakness_br_v1_startup_xauusd.csv"
    _write_csv(
        order_log,
        [
            {
                "timestamp_broker": "2026.06.08 08:55:00",
                "magic": "930101",
                "action": "GUARD_BLOCK",
                "guard_reason": "family_open_exposure_cap_reached",
            }
        ],
    )
    _write_csv(
        startup_log,
        [
            {
                "startup_status": "ATTACHED_WEAKNESS_REVIEW_DEMO_EXECUTOR_ENABLED",
                "magic": "930101",
                "dry_run": "false",
                "broker_action_allowed": "true",
            }
        ],
    )

    module = _load_module()
    result = module.generate_p2weakness_runtime_attachment_audit(
        phase1_root=phase1_root,
        terminal_root=terminal_root,
        output_dir=output_dir,
        order_log=order_log,
        startup_log=startup_log,
        kill_switch=files_dir / "p2weakness_br_v1_kill_switch.txt",
        use_mt5_bridge=False,
    )
    payload = json.loads((output_dir / "P2WEAKNESS_BR_V1_RUNTIME_ATTACHMENT_AUDIT.json").read_text(encoding="utf-8"))

    assert result.status == "QUARANTINE_RUNTIME_RISK_FOUND"
    assert payload["reviewer_questions"]["is_any_old_930101_ea_still_attached"] == "YES"
    assert payload["reviewer_questions"]["is_any_broker_action_capable_chart_active"] == "YES"
    assert payload["reviewer_questions"]["was_hardened_931000_source_deployed"] == "NO"
    assert payload["old_magic_930101"]["deployed_source_uses_old_magic"] is True
    assert payload["source_audit"]["deployed_source_matches_repo"] is False
    assert "deployed_source_still_uses_old_magic_930101" in payload["runtime_risks"]


def test_runtime_attachment_audit_reports_no_profile_evidence_when_chart_has_no_expert(tmp_path):
    phase1_root = tmp_path / "phase1"
    terminal_root = tmp_path / "terminal"
    repo_source = phase1_root / "mt5" / "Experts" / "Phase2WeaknessBreakoutRetestExecutor.mq5"
    deployed_source = terminal_root / "MQL5" / "Experts" / "Phase2WeaknessBreakoutRetestExecutor.mq5"
    chart_dir = terminal_root / "MQL5" / "Profiles" / "Charts" / "Default"
    repo_source.parent.mkdir(parents=True)
    deployed_source.parent.mkdir(parents=True)
    chart_dir.mkdir(parents=True)
    source = """
input bool InpDryRunOnly = true;
input bool InpBrokerActionAllowed = false;
input int InpMagicNumber = 931000;
""".strip()
    repo_source.write_text(source, encoding="utf-8")
    deployed_source.write_text(source, encoding="utf-8")
    (chart_dir / "chart01.chr").write_text("<chart>\nsymbol=XAUUSD\n</chart>\n", encoding="utf-8")

    module = _load_module()
    payload = module.build_audit_payload(
        phase1_root=phase1_root,
        terminal_root=terminal_root,
        order_log=terminal_root / "MQL5" / "Files" / "missing_order.csv",
        startup_log=terminal_root / "MQL5" / "Files" / "missing_startup.csv",
        kill_switch=terminal_root / "MQL5" / "Files" / "missing_kill_switch.txt",
        use_mt5_bridge=False,
    )

    assert payload["status"] == "NO_ACTIVE_P2WEAKNESS_RUNTIME_RISK_OBSERVED"
    assert payload["reviewer_questions"]["is_any_old_930101_ea_still_attached"] == "NO_PROFILE_EVIDENCE"
    assert payload["reviewer_questions"]["was_hardened_931000_source_deployed"] == "YES"


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_p2weakness_runtime_attachment_audit.py"
    spec = importlib.util.spec_from_file_location("generate_p2weakness_runtime_attachment_audit", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_p2weakness_runtime_attachment_audit"] = module
    spec.loader.exec_module(module)
    return module

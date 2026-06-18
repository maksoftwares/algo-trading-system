from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_a3_runtime_reports_generate_fixed_names(tmp_path: Path):
    module = _load_module()
    _write_minimal_a3_tree(tmp_path)

    output = module.generate_a3_runtime_reports(tmp_path, run_tests=False)

    summary = json.loads(output.summary_json.read_text(encoding="utf-8"))
    decommission = json.loads((tmp_path / "outputs" / "reports" / "A3_DECOMMISSION_REPORT.json").read_text(encoding="utf-8"))
    combined = json.loads((tmp_path / "outputs" / "reports" / "A3_COMBINED_PREFLIGHT_REPORT.json").read_text(encoding="utf-8"))

    assert "A3_DRY_RUN_SESSION_REPORT.md" in summary["reports"]["dry_run"]
    assert decommission["status"] == "PASS"
    assert combined["attach_decision"] == "DO_NOT_ATTACH"
    assert combined["status"] == "PENDING"


def _write_minimal_a3_tree(root: Path) -> None:
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (root / "mt5" / "Experts").mkdir(parents=True, exist_ok=True)
    (root / "mt5" / "Presets").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(parents=True, exist_ok=True)
    source_t1 = _source("933000", "FAMMUX_RD_XAUUSD")
    source_t2 = _source("933100", "FAMMUX_RDSTRUCT_XAUUSD")
    (root / "mt5" / "Experts" / "Account3RoundRetestGuardedExecutor.mq5").write_text(source_t1, encoding="utf-8")
    (root / "mt5" / "Experts" / "Account3RoundRetestStructuredExecutor.mq5").write_text(source_t2, encoding="utf-8")
    (root / "mt5" / "Presets" / "Account3RoundRetestGuardedExecutor.safe_xauusd.set").write_text(
        "InpDryRunOnly=true\nInpBrokerActionAllowed=false\nInpMagicNumber=933000\nInpAllowedAccountLoginsCsv=1033669\n",
        encoding="utf-8",
    )
    (root / "mt5" / "Presets" / "Account3RoundRetestStructuredExecutor.safe_xauusd.set").write_text(
        "InpDryRunOnly=true\nInpBrokerActionAllowed=false\nInpMagicNumber=933100\nInpAllowedAccountLoginsCsv=1033669\n",
        encoding="utf-8",
    )
    (root / "docs" / "A3_HYPOTHESIS_HASH_MANIFEST.json").write_text(
        json.dumps({"status": "LOCKED_BEFORE_FIRST_TRADE"}),
        encoding="utf-8",
    )
    (root / "docs" / "A3_OWNER_AUTHORIZATION_PACKET_TEMPLATE.md").write_text("template", encoding="utf-8")
    (reports / "A3_POSITION_PATH_OBSERVER_ATTACHMENT.json").write_text(
        json.dumps({"prepare_attempted": True, "attach_attempted": True, "launch_started": False, "startup_login_supplied": True, "portable_root": "C:/MT5PortableRepairLane"}),
        encoding="utf-8",
    )
    (reports / "P2WEAKNESS_BR_V1_RUNTIME_ATTACHMENT_AUDIT.json").write_text(
        json.dumps(
            {
                "status": "NO_ACTIVE_P2WEAKNESS_RUNTIME_RISK_OBSERVED",
                "reviewer_questions": {"is_any_old_930101_ea_still_attached": "NO_PROFILE_EVIDENCE"},
                "logs": {"order_log_exists": False, "startup_log_exists": False},
            }
        ),
        encoding="utf-8",
    )
    (reports / "A3_DECOMMISSION_EXPOSURE_AUDIT.json").write_text(
        json.dumps({"status": "PASS", "positions": [], "orders": [], "terminal": "fixture"}),
        encoding="utf-8",
    )


def _source(magic: str, namespace: str) -> str:
    return f'''
input long InpMagicNumber = {magic};
input string InpAllowedAccountLoginsCsv = "1033669";
input string InpExecutionKillSwitchFileName = "A3_EXECUTION_KILL.txt";
input string InpFullStopFileName = "A3_FULL_STOP.txt";
input double InpMaxEstimatedCostR = 0.15;
bool FullStopActive() {{ return true; }}
bool ExecutionKillSwitchActive() {{ return false; }}
bool PositionMagicMatches(long magic) {{ return magic == InpMagicNumber; }}
void OnTick() {{
  if((int)PositionGetInteger(POSITION_MAGIC) == InpMagicNumber) {{}}
  if((int)OrderGetInteger(ORDER_MAGIC) == InpMagicNumber) {{}}
  GlobalVariableSetOnCondition("{namespace}", InpMagicNumber, 0);
  OrderSend(request, result);
}}
'''


def _load_module():
    path = ROOT / "scripts" / "generate_a3_runtime_reports.py"
    spec = importlib.util.spec_from_file_location("generate_a3_runtime_reports", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_a3_runtime_reports"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_p2weakness_governance_reports_pass_and_warn_on_old_runtime_magic(tmp_path):
    order_log = tmp_path / "p2weakness_order_log.csv"
    startup_log = tmp_path / "p2weakness_startup_log.csv"
    _write_csv(
        order_log,
        [
            {
                "timestamp_broker": "2026.06.08 01:00:00",
                "magic": "930101",
                "action": "ORDER_SEND_OK",
                "estimated_cost_R": "0.0472",
                "family_open_exposure": "1",
                "account_orders_today": "1",
                "guard_reason": "pass",
            }
        ],
    )
    _write_csv(startup_log, [{"startup_status": "ATTACHED_WEAKNESS_REVIEW_DEMO_EXECUTOR_ENABLED"}])

    module = _load_module()
    result = module.generate_p2weakness_governance_reports(
        ROOT,
        output_dir=tmp_path,
        order_log=order_log,
        startup_log=startup_log,
    )

    assert result.status == "PASS"
    parity = json.loads((tmp_path / "P2WEAKNESS_BR_V1_SOURCE_GOVERNANCE_PARITY.json").read_text(encoding="utf-8"))
    magic = json.loads((tmp_path / "P2WEAKNESS_BR_V1_MAGIC_COLLISION_AUDIT.json").read_text(encoding="utf-8"))
    risk = json.loads((tmp_path / "EXPERIMENTAL_DEMO_DAILY_RISK_REPORT.json").read_text(encoding="utf-8"))

    assert parity["status"] == "PASS"
    assert magic["status"] == "PASS"
    assert magic["p2weakness_active_magic"] == 931000
    assert magic["runtime_previous_magic_warning"] is True
    assert risk["status"] == "REVIEW_ONLY"
    assert risk["executed_orders"] == 1


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
    path = scripts_dir / "generate_p2weakness_governance_reports.py"
    spec = importlib.util.spec_from_file_location("generate_p2weakness_governance_reports", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_p2weakness_governance_reports"] = module
    spec.loader.exec_module(module)
    return module

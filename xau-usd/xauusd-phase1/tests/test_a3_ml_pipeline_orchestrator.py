from __future__ import annotations

import sys

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c07_next_blocker_reports_failed_c03_gates() -> None:
    from ml.a3_meta_v1.pipeline_orchestrator import _next_blocker

    blocker = _next_blocker(
        {
            "c03": {
                "status": "NO_GO",
                "checks": [
                    {"gate": "market_setup_groups", "passed": False, "observed": "121", "required": ">=300"},
                    {"gate": "leakage", "passed": True, "observed": "0", "required": "0"},
                ],
            }
        }
    )

    assert blocker == "C03 readiness is not PASS: market_setup_groups observed 121 required >=300"


def test_c07_next_blocker_advances_to_training_gate_after_c03_pass() -> None:
    from ml.a3_meta_v1.pipeline_orchestrator import _next_blocker

    blocker = _next_blocker({"c03": {"status": "PASS", "checks": []}, "c05": {"status": "REFUSED_NOT_READY"}})

    assert blocker == "C05 training is REFUSED_NOT_READY, required TRAINED_SHADOW_ONLY"


def test_c07_render_mentions_boundaries() -> None:
    from ml.a3_meta_v1.pipeline_orchestrator import render_pipeline_run_status_md

    report = render_pipeline_run_status_md(
        {
            "status": "NOT_READY",
            "dataset_version": "TEST",
            "publish_requested": False,
            "steps": [{"step": "C03 readiness", "status": "PASS", "output": "report.json"}],
            "summary": {"c03": {"status": "NO_GO", "checks": []}},
            "next_blocker": "C03 readiness is not PASS",
            "boundary": {"ea_file_drop_authorized": False},
            "next_allowed_stage": "Collect more data.",
        }
    )

    assert "Overall status: NOT_READY" in report
    assert "MT5 connection attempted: false." in report
    assert "Broker action authorized: false." in report


def test_c07_script_loads() -> None:
    module = load_script("c07_run_ml_readiness_pipeline")

    assert hasattr(module, "main")


def test_c07_loads_c01_dataclass_script() -> None:
    from ml.a3_meta_v1.pipeline_orchestrator import _load_c01_module

    module = _load_c01_module(ROOT)

    assert hasattr(module, "generate_a3_ml_c01_pipeline")

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_position_path_attach_chart_is_single_readonly_instance():
    module = _load_module()

    chart = module._render_chart(ROOT)

    assert "path=Experts\\Phase2PositionPathObserver.ex5" in chart
    assert "InpRunId=phase2-position-path-observer-v0.1" in chart
    assert "InpDryRunOnly=true" in chart
    assert "InpSnapshotSeconds=10" in chart
    assert "InpExpectedServerMarker=Demo" in chart
    assert chart.count("<expert>") == 1
    assert "OrderSend" not in chart
    assert "CTrade" not in chart


def test_position_path_attach_refuses_standard_demo_terminal_by_default():
    module = _load_module()

    try:
        module._guard_not_standard_demo_terminal(
            module.STANDARD_DEMO_TERMINAL_DATA_DIR,
            module.DEFAULT_PORTABLE_ROOT / "terminal64.exe",
        )
    except RuntimeError as exc:
        assert "standard demo trading terminal" in str(exc)
    else:
        raise AssertionError("standard demo terminal was not rejected")


def test_position_path_attach_defaults_to_separate_portable_root():
    module = _load_module()

    assert module.DEFAULT_PORTABLE_ROOT.as_posix().endswith("MT5PortablePositionPathObserver")
    assert module.EA_NAME == "Phase2PositionPathObserver"
    assert module.PRESET_SOURCE.name == "Phase2PositionPathObserver.demo_account_readonly.set"


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "attach_phase2_position_path_observer.py"
    spec = importlib.util.spec_from_file_location("attach_phase2_position_path_observer", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["attach_phase2_position_path_observer"] = module
    spec.loader.exec_module(module)
    return module

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("v60_canonical_run", ROOT / "run_portfolio.py")
assert SPEC is not None and SPEC.loader is not None
RUN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUN
SPEC.loader.exec_module(RUN)


def test_config_has_exact_canonical_sources_and_no_ml_authority() -> None:
    config = RUN.load_config()
    assert len(config["sources"]) == 10
    assert config["account"]["expected_login"] == 1033030
    assert config["authorization"]["ml_runtime_authorized"] is False
    assert config["authorization"]["ml_shadow_authorized"] is False
    assert config["runtime"]["execution_enabled"] is True


def test_aed_account_values_are_converted_before_usd_risk_comparison() -> None:
    config = RUN.load_config()
    assert RUN.account_value_usd(367.25, config) == 100.0


def test_guardian_entry_halt_file_is_enforced(tmp_path) -> None:
    config = RUN.load_config()
    halt = tmp_path / "guardian_halt.txt"
    config["runtime"]["entry_halt_files"] = [str(halt)]
    assert RUN.active_entry_halts(config) == []
    halt.write_text("HALT\n", encoding="ascii")
    assert RUN.active_entry_halts(config) == [str(halt)]

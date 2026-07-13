from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load():
    path = ROOT / "scripts" / "build_a1_xau_r6_market_only_native_parity_oracle.py"
    spec = importlib.util.spec_from_file_location("np1_builder_safety", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


B = _load()


def test_oracle_has_zero_trading_surface_and_read_only_probe() -> None:
    text = B.OUTPUT_SOURCE.read_text(encoding="utf-8")

    B.assert_source_safety(text)
    assert all(token not in text for token in B.FORBIDDEN_TOKENS)
    assert "OrderCalcProfit" in text
    assert "MQLInfoInteger(MQL_TESTER)" in text
    assert "PositionsTotal()==0" in text
    assert "OrdersTotal()==0" in text
    assert "open_positions_zero" in text
    assert "pending_orders_zero" in text
    assert "FILE_COMMON" not in text
    assert "g_numeric_output_enabled=available" in text
    assert "ResetLastError();" in text
    assert "EvidenceBarCount" in text
    assert "%04d-%02d-%02dT%02d:%02d:%02d" in text
    assert "fixed_constant_InpRegimeCompressionRangeMedianMax" in text
    router_write = next(line for line in text.splitlines() if 'FileWrite(handle,"a1_xau_r6_native_router_row_v1"' in line)
    assert "iBars(" not in router_write


def test_oracle_locks_only_run_id_and_output_names_as_inputs() -> None:
    text = B.OUTPUT_SOURCE.read_text(encoding="utf-8")
    input_lines = [line.strip() for line in text.splitlines() if line.strip().startswith("input ")]

    assert len(input_lines) == 10
    assert all("string" in line for line in input_lines)
    assert "input string InpRunId" in text
    assert "input int InpAtrPeriod" not in text
    assert "int InpAtrPeriod = 14;" in text
    assert "double InpRegimeShockD1AtrPercentileMin = 95.00;" in text


def test_source_safety_rejects_every_forbidden_token() -> None:
    clean, _ = B.render_oracle()
    for token in B.FORBIDDEN_TOKENS:
        with pytest.raises(RuntimeError, match="forbidden trading token"):
            B.assert_source_safety(clean + "\n" + token)

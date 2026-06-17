from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_quarantine_chart_sets_non_broker_action_inputs(tmp_path: Path):
    module = _load_module()
    chart = tmp_path / "chart09.chr"
    chart.write_text(
        "\n".join(
            [
                "<chart>",
                "symbol=XAUUSD",
                "<expert>",
                "name=Phase2ExperimentalDemoExecutor",
                "<inputs>",
                "InpDryRunOnly=false",
                "InpBrokerActionAllowed=true",
                "InpCandidate=symbol_normalized_round_retest_v0",
                "InpCandidateStatus=EXPERIMENTAL_QUARANTINE_REVIEW_ONLY",
                "InpTargetSymbol=XAUUSD",
                "</inputs>",
                "</expert>",
                "</chart>",
                "",
            ]
        ),
        encoding="utf-8",
    )

    changed = module.quarantine_chart(chart)
    text = chart.read_text(encoding="utf-8")

    assert changed is True
    assert "InpDryRunOnly=true" in text
    assert "InpBrokerActionAllowed=false" in text
    assert "InpCandidateStatus=OWNER_APPROVED_ROUND_FAMILY_QUARANTINED" in text


def test_target_and_protected_chart_selection():
    module = _load_module()
    inventory = [
        _row("chart03.chr", "XAUUSD", "breakout_retest"),
        _row("chart06.chr", "XAUUSD", "swing_breakout_retest_v0"),
        _row("chart09.chr", "XAUUSD", "symbol_normalized_round_retest_v0"),
        _row("chart11.chr", "XAUUSD", "round_number_retest_v0"),
        _row("chart07.chr", "EURUSD", "symbol_normalized_round_retest_v0"),
    ]

    assert [row["chart"] for row in module.target_charts(inventory)] == ["chart09.chr", "chart11.chr"]
    assert [row["chart"] for row in module.protected_charts(inventory)] == ["chart03.chr", "chart06.chr"]


def _row(chart: str, symbol: str, candidate: str) -> dict[str, str]:
    return {
        "chart": chart,
        "path": chart,
        "symbol": symbol,
        "expert": "Phase2ExperimentalDemoExecutor",
        "dry_run": "false",
        "broker_action_allowed": "true",
        "candidate": candidate,
        "candidate_status": "EXPERIMENTAL_QUARANTINE_REVIEW_ONLY",
        "target_symbol": symbol,
        "qualified_symbols": symbol,
        "signal_log": "",
        "startup_log": "",
        "order_log": "",
    }


def _load_module():
    path = ROOT / "scripts" / "apply_xauusd_round_family_quarantine.py"
    spec = importlib.util.spec_from_file_location("apply_xauusd_round_family_quarantine", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["apply_xauusd_round_family_quarantine"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

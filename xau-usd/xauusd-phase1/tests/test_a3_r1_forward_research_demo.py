from __future__ import annotations

import json
from pathlib import Path

from ml.a3_meta_v1.r1_forward_research_demo import generate_r1_forward_research_demo_packet


ROOT = Path(__file__).resolve().parents[1]


def test_packet_is_ready_and_does_not_contact_terminal(tmp_path: Path) -> None:
    report = generate_r1_forward_research_demo_packet(
        ROOT,
        report_path=tmp_path / "packet.json",
        preset_path=tmp_path / "r1.set",
    )
    payload = json.loads(report.read_text(encoding="utf-8"))

    assert payload["status"] == "READY_FOR_A3_ISOLATED_DEMO_ATTACH"
    assert all(payload["boundary"][key] is False for key in payload["boundary"])
    assert all(check["passed"] for check in payload["checks"])


def test_preset_freezes_identity_signal_and_risk(tmp_path: Path) -> None:
    preset = tmp_path / "r1.set"
    generate_r1_forward_research_demo_packet(ROOT, report_path=tmp_path / "packet.json", preset_path=preset)
    values = dict(
        line.split("=", 1)
        for line in preset.read_text(encoding="utf-8").splitlines()
        if "=" in line
    )

    assert values["InpAllowedAccountLogin"] == "1033669"
    assert values["InpAllowNonDemoAccounts"] == "false"
    assert values["InpMagicNumber"] == "934100"
    assert values["InpSignalMode"] == "7"
    assert values["InpDirectionMode"] == "1"
    assert values["InpRegimeRouterMode"] == "1"
    assert values["InpUseRiskNormalizedLots"] == "true"
    assert values["InpRiskAmountUsd"] == "30.00"
    assert values["InpMaxRiskLots"] == "0.01"
    assert values["InpRejectRiskOvershootEnabled"] == "true"
    assert values["InpMaxRiskOvershootPct"] == "0.00"


def test_preset_retains_daily_position_and_cost_guards(tmp_path: Path) -> None:
    preset = tmp_path / "r1.set"
    generate_r1_forward_research_demo_packet(ROOT, report_path=tmp_path / "packet.json", preset_path=preset)
    text = preset.read_text(encoding="utf-8")

    for expected in (
        "InpPortfolioDailyGuardEnabled=true",
        "InpPortfolioMaxTradesPerDay=1",
        "InpPortfolioDailyLossStopUsd=60.00",
        "InpOnePositionPerMagic=true",
        "InpMaxOpenPositionsPerMagic=1",
        "InpMaxSpreadPoints=75",
        "InpMaxEstimatedCostR=0.15",
        "InpKillSwitchFileName=a3_r1_forward_research_kill_switch.txt",
    ):
        assert expected in text

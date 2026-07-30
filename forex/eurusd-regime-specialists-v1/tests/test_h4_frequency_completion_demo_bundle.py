from __future__ import annotations

import json
import zipfile
from pathlib import Path

from eurusd_regime_specialists.h4_frequency_completion_demo_bundle import (
    build_bundle,
    plan_shadow_install,
)


ROOT = Path(__file__).resolve().parent.parent
CONFIG = (
    ROOT
    / "config"
    / "frozen_h4_frequency_completion_demo_bundle_v1.json"
)


def _target(tmp_path: Path) -> Path:
    target = tmp_path / "dedicated_demo"
    (target / "MQL5" / "Experts").mkdir(parents=True)
    (target / "MQL5" / "Presets").mkdir(parents=True)
    (target / "Config").mkdir(parents=True)
    (target / "terminal64.exe").write_bytes(b"fixture terminal")
    return target


def test_bundle_is_deterministic_disarmed_and_contains_no_active_order_preset(
    tmp_path: Path,
) -> None:
    first = build_bundle(CONFIG, tmp_path / "one")
    second = build_bundle(CONFIG, tmp_path / "two")
    assert first.status == "BUNDLE_READY_NO_DEPLOYMENT"
    assert first.archive_sha256 == second.archive_sha256
    assert first.manifest_sha256 == second.manifest_sha256
    with zipfile.ZipFile(first.archive_path) as archive:
        names = set(archive.namelist())
        assert "MANIFEST.json" in names
        assert (
            "MQL5/Presets/"
            "EURUSD_H4_FREQUENCY_COMPLETION_SHADOW_DEMO.set"
        ) in names
        assert not any(name.endswith("ORDERING_DEMO.set") for name in names)
        shadow = archive.read(
            "MQL5/Presets/"
            "EURUSD_H4_FREQUENCY_COMPLETION_SHADOW_DEMO.set"
        ).decode("utf-8")
        startup = archive.read(
            "Config/"
            "EURUSD_H4_FREQUENCY_COMPLETION_LIVE_DEMO_SHADOW.ini"
        ).decode("utf-8")
        manifest = json.loads(archive.read("MANIFEST.json"))
    assert "InpShadowMode=true" in shadow
    assert "InpEnableDemoOrders=false" in shadow
    assert "InpEmergencyStop=true" in shadow
    assert "InpDemoArmToken=DISARMED" in shadow
    assert "AllowLiveTrading=0" in startup
    assert manifest["deployment_authorized"] is False
    assert manifest["demo_orders_authorized"] is False


def test_ready_preflight_is_read_only(tmp_path: Path) -> None:
    target = _target(tmp_path)
    before = sorted(
        (path.relative_to(target), path.read_bytes())
        for path in target.rglob("*")
        if path.is_file()
    )
    plan = plan_shadow_install(CONFIG, target)
    after = sorted(
        (path.relative_to(target), path.read_bytes())
        for path in target.rglob("*")
        if path.is_file()
    )
    assert plan.status == "READY_NO_WRITES"
    assert plan.target_writes_performed == 0
    assert before == after
    assert all(row["target_state"] == "ABSENT" for row in plan.planned_files)


def test_preflight_blocks_running_terminal_without_writing(tmp_path: Path) -> None:
    target = _target(tmp_path)
    plan = plan_shadow_install(
        CONFIG,
        target,
        running_terminal_executables=[target / "terminal64.exe"],
    )
    assert plan.status == "BLOCKED_NO_WRITES"
    assert plan.target_writes_performed == 0
    check = {
        row["name"]: row["passed"] for row in plan.checks
    }
    assert check["target_terminal_stopped"] is False
    assert not (
        target
        / "MQL5"
        / "Experts"
        / "EurUsdH4FrequencyCompletionControlledDemo.ex5"
    ).exists()


def test_preflight_blocks_hash_collision(tmp_path: Path) -> None:
    target = _target(tmp_path)
    destination = (
        target
        / "MQL5"
        / "Experts"
        / "EurUsdH4FrequencyCompletionControlledDemo.ex5"
    )
    destination.write_bytes(b"not the frozen binary")
    plan = plan_shadow_install(CONFIG, target)
    assert plan.status == "BLOCKED_NO_WRITES"
    assert plan.target_writes_performed == 0
    states = {
        Path(row["destination"]).name: row["target_state"]
        for row in plan.planned_files
    }
    assert (
        states["EurUsdH4FrequencyCompletionControlledDemo.ex5"]
        == "HASH_COLLISION"
    )


def test_preflight_contract_prohibits_reusing_existing_demo_terminals() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert "C:/MT5PortableM15RegimeShadow" in config[
        "prohibited_existing_demo_roots"
    ]
    assert config["decision_policy"][
        "existing_demo_terminal_reuse_is_prohibited"
    ]

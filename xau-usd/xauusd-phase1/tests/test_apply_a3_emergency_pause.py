from __future__ import annotations

from pathlib import Path

from phase2x_test_helpers import load_script


def test_a3_emergency_pause_dry_run_discovers_dynamic_a3_action_surface(tmp_path: Path, monkeypatch) -> None:
    pause = load_script("apply_a3_emergency_pause")
    portable = _portable(tmp_path)
    target = _write_chart(
        portable,
        "chart01.chr",
        "XAUUSD",
        "Account3FutureExecutor",
        {
            "InpRunId": "A3_FUTURE",
            "InpDryRunOnly": "false",
            "InpBrokerActionAllowed": "true",
            "InpMagicNumber": "933777",
        },
    )
    before = target.read_text(encoding="utf-8")
    _write_chart(portable, "chart02.chr", "XAUUSD", "NotA3Executor", {"InpMagicNumber": "123"})
    monkeypatch.setattr(pause, "broker_state", lambda _terminal: _broker("PASS"))

    payload = pause.apply_a3_emergency_pause(tmp_path, portable_root=portable, mode="dry-run")

    assert payload["status"] == "DRY_RUN_READY"
    assert target.read_text(encoding="utf-8") == before
    assert payload["changed_charts"] == []
    assert [row["chart"] for row in payload["target_charts"]] == ["chart01.chr"]
    plan = payload["planned_changes"][0]
    assert plan["replacements"]["InpDryRunOnly"] == "true"
    assert plan["replacements"]["InpBrokerActionAllowed"] == "false"
    assert plan["replacements"]["InpRunId"] == "A3_FUTURE_PAUSED_20260618"


def test_a3_emergency_pause_apply_aborts_before_write_when_exposure_exists(tmp_path: Path, monkeypatch) -> None:
    pause = load_script("apply_a3_emergency_pause")
    portable = _portable(tmp_path)
    target = _write_chart(
        portable,
        "chart01.chr",
        "XAUUSD",
        "Account3BreakoutImprovedExecutor",
        {"InpRunId": "A3_ARMED", "InpDryRunOnly": "false", "InpBrokerActionAllowed": "true", "InpMagicNumber": "933300"},
    )
    before = target.read_text(encoding="utf-8")
    monkeypatch.setattr(pause, "broker_state", lambda _terminal: _broker("FAIL", positions=1))
    monkeypatch.setattr(pause, "stop_terminal_for_profile_write", lambda _terminal: (_ for _ in ()).throw(AssertionError("must not stop terminal")))

    payload = pause.apply_a3_emergency_pause(tmp_path, portable_root=portable, mode="apply")

    assert payload["status"] == "FAIL_EXPOSURE_OR_UNKNOWN"
    assert target.read_text(encoding="utf-8") == before
    assert payload["changed_charts"] == []


def test_a3_emergency_pause_apply_writes_targets_only_and_is_idempotent(tmp_path: Path, monkeypatch) -> None:
    pause = load_script("apply_a3_emergency_pause")
    portable = _portable(tmp_path)
    target = _write_chart(
        portable,
        "chart01.chr",
        "XAUUSD",
        "Account3BreakoutTier1CompatExecutor",
        {"InpRunId": "A3_ARMED", "InpDryRunOnly": "false", "InpBrokerActionAllowed": "true", "InpMagicNumber": "933400"},
    )
    non_target = _write_chart(portable, "chart02.chr", "EURUSD", "Account3BreakoutTier1CompatExecutor", {"InpMagicNumber": "933400"})
    non_target_before = non_target.read_text(encoding="utf-8")
    monkeypatch.setattr(pause, "broker_state", lambda _terminal: _broker("PASS"))
    monkeypatch.setattr(pause, "stop_terminal_for_profile_write", lambda _terminal: _stopped())

    payload = pause.apply_a3_emergency_pause(tmp_path, portable_root=portable, mode="apply")

    assert payload["status"] == "PASS"
    assert len(payload["changed_charts"]) == 1
    assert "InpDryRunOnly=true" in target.read_text(encoding="utf-8")
    assert "InpBrokerActionAllowed=false" in target.read_text(encoding="utf-8")
    assert non_target.read_text(encoding="utf-8") == non_target_before
    assert any(item["name"] == "non_target_hashes_unchanged" and item["status"] == "PASS" for item in payload["checks"])

    second = pause.apply_a3_emergency_pause(tmp_path, portable_root=portable, mode="apply")

    assert second["status"] == "ALREADY_PAUSED"
    assert second["changed_charts"] == []


def test_a3_emergency_pause_apply_requires_terminal_fully_stopped(tmp_path: Path, monkeypatch) -> None:
    pause = load_script("apply_a3_emergency_pause")
    portable = _portable(tmp_path)
    target = _write_chart(
        portable,
        "chart01.chr",
        "XAUUSD",
        "Account3ProfitLockExitManager",
        {"InpRunId": "A3_PL_ARMED", "InpDryRunOnly": "false", "InpManageActionAllowed": "true", "InpManagedMagicsCsv": "933200,933400"},
    )
    before = target.read_text(encoding="utf-8")
    monkeypatch.setattr(pause, "broker_state", lambda _terminal: _broker("PASS"))
    monkeypatch.setattr(
        pause,
        "stop_terminal_for_profile_write",
        lambda _terminal: {
            "attempted": True,
            "stopped_before_profile_write": False,
            "process_snapshot_before_write": {"running": True, "pids": [123]},
            "close_result": {"returncode": 0},
        },
    )

    payload = pause.apply_a3_emergency_pause(tmp_path, portable_root=portable, mode="apply")

    assert payload["status"] == "FAIL_TERMINAL_STILL_RUNNING"
    assert target.read_text(encoding="utf-8") == before


def test_a3_emergency_pause_rolls_back_when_post_verify_fails(tmp_path: Path, monkeypatch) -> None:
    pause = load_script("apply_a3_emergency_pause")
    portable = _portable(tmp_path)
    target = _write_chart(
        portable,
        "chart01.chr",
        "XAUUSD",
        "Account3BreakoutImprovedExecutor",
        {"InpRunId": "A3_ARMED", "InpDryRunOnly": "false", "InpBrokerActionAllowed": "true", "InpMagicNumber": "933300"},
    )
    before = target.read_text(encoding="utf-8")
    monkeypatch.setattr(pause, "broker_state", lambda _terminal: _broker("PASS"))
    monkeypatch.setattr(pause, "stop_terminal_for_profile_write", lambda _terminal: _stopped())
    monkeypatch.setattr(pause, "build_checks", lambda _payload: [pause.check("forced_post_verify_fail", "FAIL", "fixture")])

    payload = pause.apply_a3_emergency_pause(tmp_path, portable_root=portable, mode="apply")

    assert payload["status"] == "FAIL_ROLLED_BACK"
    assert payload["rollback"]["status"] == "PASS"
    assert target.read_text(encoding="utf-8") == before


def _portable(tmp_path: Path) -> Path:
    portable = tmp_path / "portable"
    (portable / "MQL5" / "Profiles" / "Charts" / "Default").mkdir(parents=True)
    (portable / "MQL5" / "Files").mkdir(parents=True)
    (portable / "terminal64.exe").write_text("", encoding="utf-8")
    return portable


def _write_chart(portable: Path, name: str, symbol: str, expert: str, inputs: dict[str, str]) -> Path:
    chart = portable / "MQL5" / "Profiles" / "Charts" / "Default" / name
    body = [
        f"symbol={symbol}",
        "<expert>",
        f"name={expert}",
        "</expert>",
        "<inputs>",
        *[f"{key}={value}" for key, value in inputs.items()],
        "</inputs>",
        "",
    ]
    chart.write_text("\n".join(body), encoding="utf-8")
    return chart


def _broker(status: str, positions: int = 0, orders: int = 0) -> dict[str, object]:
    return {
        "status": status,
        "a3_positions_total": positions,
        "a3_orders_total": orders,
        "all_xau_positions_total": positions,
        "all_xau_orders_total": orders,
    }


def _stopped() -> dict[str, object]:
    return {
        "attempted": True,
        "stopped_before_profile_write": True,
        "process_snapshot_before_write": {"running": False, "pids": []},
        "close_result": {"returncode": 0},
    }

from __future__ import annotations

import plan_prospective_neutral_operations as base
import plan_prospective_neutral_operations_v1_1 as planner


def test_runtime_only_supersession_is_locked_and_offline() -> None:
    checked = planner.verify_lock()
    config = planner.load_config()

    assert config["schema_version"].endswith("_v1_1")
    assert config["supersedes"]["before_prospective_start_and_first_signal"]
    assert config["runtime"]["dependency_resolution_network_allowed"] is False
    assert config["runtime"]["strategy_or_evidence_semantics_changed"] is False
    assert checked

    launcher = config["runtime"]["launcher"]
    for command in config["commands"].values():
        assert command.startswith(f"{launcher} ")
    assert config["supersedes"]["path"] in checked


def test_wrapper_does_not_mutate_original_planner_contract() -> None:
    original = (base.CONFIG_PATH, base.LOCK_PATH, base.SCHEMA_VERSION)
    planner.verify_lock()
    assert (base.CONFIG_PATH, base.LOCK_PATH, base.SCHEMA_VERSION) == original


def test_default_evidence_roots_are_not_overridden_with_none(monkeypatch) -> None:
    calls = []

    def fake_build_operations_plan(*, evaluated_at_utc):
        calls.append(evaluated_at_utc)
        return {"schema_version": base.SCHEMA_VERSION}

    monkeypatch.setattr(
        base,
        "build_operations_plan",
        fake_build_operations_plan,
    )
    result = planner.build_operations_plan()

    assert calls == [None]
    assert result["schema_version"].endswith("_v1_1")

from __future__ import annotations

import importlib.util
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("v60_canonical_run", ROOT / "run_portfolio.py")
assert SPEC is not None and SPEC.loader is not None
RUN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUN
SPEC.loader.exec_module(RUN)


def test_config_has_exact_canonical_sources_and_no_ml_authority() -> None:
    config = RUN.load_config()
    assert len(config["sources"]) == 9
    assert "R5_TRANSITION" not in {
        str(source["source_id"]) for source in config["sources"]
    }
    assert config["account"]["expected_login"] == 1033030
    assert config["authorization"]["ml_runtime_authorized"] is False
    assert config["authorization"]["ml_shadow_authorized"] is False
    assert config["authorization"]["minimum_balance_requirement_enabled"] is False
    assert config["authorization"]["demo_balance_eligibility_waived"] is True
    assert config["risk"]["equity_fraction_limits_enabled"] is True
    parity = RUN.verify_deployment_parity(config)
    assert parity["status"] == "PASS"
    assert parity["unknown_execution_source_ids"] == []
    assert parity["probation_source_ids"] == [
        "V25_CHOP",
        "V8_RETEST_HEALTH",
    ]
    assert config["runtime"]["execution_enabled"] is True
    cooldowns = {
        str(source["source_id"]): int(
            source.get("same_direction_post_loss_cooldown_minutes", 0)
        )
        for source in config["sources"]
    }
    assert cooldowns["V57_BREAK_SWING_H4ADX_HIGH"] == 120
    assert all(value == 0 for key, value in cooldowns.items() if key != "V57_BREAK_SWING_H4ADX_HIGH")


def test_portable_ml_overlay_preserves_base_and_authorizes_demo_topup_only() -> None:
    base = RUN.load_config()
    config = RUN.load_config(ml_overlay_path=RUN.ML_OVERLAY_PATH)
    assert base["authorization"]["ml_runtime_authorized"] is False
    assert "ml_topup" not in base
    assert config["authorization"]["ml_runtime_authorized"] is True
    assert config["authorization"]["ml_shadow_authorized"] is False
    assert config["authorization"]["live_authorized"] is False
    assert config["ml_topup"]["failure_policy"] == "BASELINE_ONLY"
    assert config["ml_topup"]["topup_lot"] == config["account"]["fixed_lot"]
    assert "R1_BOX" not in config["ml_topup"]["eligible_source_ids"]
    assert "R1_PULLBACK" not in config["ml_topup"]["eligible_source_ids"]
    assert "V25_CHOP" not in config["ml_topup"]["eligible_source_ids"]
    assert "V8_RETEST_HEALTH" not in config["ml_topup"]["eligible_source_ids"]
    assert config["ml_topup"]["probation_source_ids"] == [
        "V8_RETEST_HEALTH",
        "V25_CHOP",
    ]


def test_config_rejects_absolute_only_demo_limits(tmp_path: Path) -> None:
    config = json.loads(RUN.CONFIG_PATH.read_text(encoding="utf-8"))
    config["risk"]["equity_fraction_limits_enabled"] = False
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(RuntimeError, match="activation-equity scaling"):
        RUN.load_config(path)


def test_ml_overlay_rejects_probation_source(tmp_path: Path) -> None:
    overlay = json.loads(RUN.ML_OVERLAY_PATH.read_text(encoding="utf-8"))
    overlay["ml_topup"]["eligible_source_ids"].append("V8_RETEST_HEALTH")
    path = tmp_path / "unsafe_overlay.json"
    path.write_text(json.dumps(overlay), encoding="utf-8")
    with pytest.raises(RuntimeError, match="probation sources"):
        RUN.load_config(ml_overlay_path=path)


def test_ml_topup_risk_gate_rejects_double_source_risk() -> None:
    config = RUN.load_config(ml_overlay_path=RUN.ML_OVERLAY_PATH)
    candidate = SimpleNamespace(
        candidate_id="risk",
        source_id="R3_COMPRESSION",
        sleeve_type="CORE",
        direction="LONG",
        initial_risk_usd=30.0,
        scheduled_at=datetime(2026, 7, 29, tzinfo=UTC),
    )
    assert RUN.ml_topup_risk_reason(
        candidate,
        config,
        {"positions": {}, "ml_topup": {"orders": {}, "daily_topups": {}}},
        [],
        active_initial_risk_usd=30.0,
        active_direction_risk_usd={"LONG": 30.0, "SHORT": 0.0},
        active_addon_risk_usd=0.0,
        effective_risk_limits={
            "maximum_account_concurrent_initial_risk_usd": 60.0,
            "maximum_directional_concurrent_initial_risk_usd": 60.0,
        },
    ) == "ML_TOPUP_SOURCE_RISK_LIMIT"


def test_ml_topup_rejects_when_historically_unknown_risk_position_is_open() -> None:
    config = RUN.load_config(ml_overlay_path=RUN.ML_OVERLAY_PATH)
    candidate = SimpleNamespace(
        candidate_id="known",
        source_id="V57_BREAK_SWING_H4ADX_HIGH",
        sleeve_type="ADDON",
        direction="SHORT",
        initial_risk_usd=5.0,
        scheduled_at=datetime(2026, 7, 29, tzinfo=UTC),
    )
    position = SimpleNamespace(ticket=7)
    state = {
        "positions": {
            "r1": {"ticket": 7, "source_id": "R1_BOX"},
        },
        "ml_topup": {"orders": {}, "daily_topups": {}},
    }
    assert RUN.ml_topup_risk_reason(
        candidate,
        config,
        state,
        [position],
        active_initial_risk_usd=10.0,
        active_direction_risk_usd={"LONG": 10.0, "SHORT": 0.0},
        active_addon_risk_usd=0.0,
        effective_risk_limits={
            "maximum_account_concurrent_initial_risk_usd": 60.0,
            "maximum_directional_concurrent_initial_risk_usd": 60.0,
        },
    ) == "ML_TOPUP_ACTIVE_HISTORICALLY_UNKNOWN_RISK"


def test_v57_post_loss_cooldown_uses_position_lifecycle_and_direction() -> None:
    config = RUN.load_config()
    opened = datetime(2026, 7, 23, 0, 30, tzinfo=UTC)
    closed = datetime(2026, 7, 23, 1, 48, tzinfo=UTC)
    deals = [
        SimpleNamespace(
            symbol="XAUUSD",
            position_id=77,
            magic=965757,
            entry=0,
            type=0,
            time_msc=int(opened.timestamp() * 1000),
            profit=0.0,
            commission=-0.1,
            swap=0.0,
            fee=0.0,
        ),
        SimpleNamespace(
            symbol="XAUUSD",
            position_id=77,
            magic=960001,
            entry=1,
            type=1,
            time_msc=int(closed.timestamp() * 1000),
            profit=-39.0,
            commission=-0.03,
            swap=0.0,
            fee=0.0,
        ),
    ]
    mt5 = SimpleNamespace(
        DEAL_ENTRY_IN=0,
        DEAL_ENTRY_OUT=1,
        DEAL_ENTRY_OUT_BY=3,
        DEAL_TYPE_BUY=0,
        history_deals_get=lambda *_args: deals,
    )
    losses, available = RUN.recent_same_direction_losses(
        mt5,
        config,
        {"activated_at_utc": "2026-07-21T00:00:00Z"},
        [],
        datetime(2026, 7, 23, 3, 20, tzinfo=UTC),
    )
    assert available is True
    assert losses[("V57_BREAK_SWING_H4ADX_HIGH", "LONG")] == closed

    candidate = SimpleNamespace(
        source_id="V57_BREAK_SWING_H4ADX_HIGH",
        direction="LONG",
        same_direction_post_loss_cooldown_minutes=120,
    )
    assert RUN.post_loss_cooldown_active(
        candidate, losses, datetime(2026, 7, 23, 3, 20, tzinfo=UTC)
    )
    candidate.direction = "SHORT"
    assert not RUN.post_loss_cooldown_active(
        candidate, losses, datetime(2026, 7, 23, 3, 20, tzinfo=UTC)
    )
    candidate.direction = "LONG"
    assert not RUN.post_loss_cooldown_active(
        candidate, losses, datetime(2026, 7, 23, 3, 49, tzinfo=UTC)
    )


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


def test_balance_waiver_still_refuses_non_demo_trade_mode() -> None:
    config = RUN.load_config()
    account = SimpleNamespace(
        login=1033030,
        server="Capital.ComMena-Demo",
        currency="AED",
        trade_mode=2,
        trade_allowed=True,
        trade_expert=True,
    )
    terminal = SimpleNamespace(connected=True, trade_allowed=True)
    symbol = SimpleNamespace(
        visible=True,
        trade_contract_size=100.0,
        volume_min=0.01,
    )
    mt5 = SimpleNamespace(
        account_info=lambda: account,
        terminal_info=lambda: terminal,
        symbol_info=lambda _symbol: symbol,
    )
    with pytest.raises(RuntimeError, match="Non-demo account trade mode refused"):
        RUN.assert_account(mt5, config)


def test_feed_heartbeat_keeps_executor_ready_during_bounded_slow_cycle(tmp_path) -> None:
    config = RUN.load_config()
    config["runtime"]["directory"] = str(tmp_path)
    now = datetime.now(UTC)
    required = {
        "R1_BOX",
        "R1_PULLBACK",
        "R2_R3",
        "R4",
        "CORE_OUTCOMES",
        "R5_COMPONENTS",
        "R5_RESOLVER",
        "R5_ROUTER",
        "ADDONS",
    }
    status = {
        "updated_at_utc": now.isoformat(),
        "cycle_in_progress": True,
        "cycle_started_at_utc": (now - timedelta(minutes=5)).isoformat(),
        "account_login": 1033030,
        "ml_used": False,
        "feeds": {name: {"ok": True} for name in required},
        "all_requested_feeds_ok": True,
    }
    (tmp_path / config["runtime"]["feed_status_filename"]).write_text(
        json.dumps(status), encoding="utf-8"
    )

    result = RUN.feed_preflight(config, require_ready=True)

    assert result["ready"] is True
    assert result["cycle_in_progress"] is True
    assert result["cycle_within_deadline"] is True


def test_feed_heartbeat_cannot_hide_cycle_that_exceeds_deadline(tmp_path) -> None:
    config = RUN.load_config()
    config["runtime"]["directory"] = str(tmp_path)
    now = datetime.now(UTC)
    required = {
        "R1_BOX",
        "R1_PULLBACK",
        "R2_R3",
        "R4",
        "CORE_OUTCOMES",
        "R5_COMPONENTS",
        "R5_RESOLVER",
        "R5_ROUTER",
        "ADDONS",
    }
    status = {
        "updated_at_utc": now.isoformat(),
        "cycle_in_progress": True,
        "cycle_started_at_utc": (now - timedelta(minutes=21)).isoformat(),
        "account_login": 1033030,
        "ml_used": False,
        "feeds": {name: {"ok": True} for name in required},
        "all_requested_feeds_ok": True,
    }
    (tmp_path / config["runtime"]["feed_status_filename"]).write_text(
        json.dumps(status), encoding="utf-8"
    )

    with pytest.raises(RuntimeError, match="Canonical feeds are not ready"):
        RUN.feed_preflight(config, require_ready=True)


def test_core_outcome_transport_does_not_leak_generic_resolver_module(
    monkeypatch,
) -> None:
    sys.path.insert(0, str(ROOT / "src"))
    import feeds

    sentinel = object()
    monkeypatch.setitem(sys.modules, "resolver", sentinel)

    class FakeModule:
        @staticmethod
        def load_config(_path=None):
            return {
                "source": {},
                "frozen_identity": {
                    "v28": {},
                    "v29": {},
                    "v34": {},
                },
                "outputs": {},
            }

        @staticmethod
        def run_cycle(_repo_root, _package):
            assert sys.modules["resolver"] is not sentinel
            return {"status": "ACTIVE_READ_ONLY_CAUSAL_RESOLVER"}

    def fake_load_module(_name, _path):
        sys.modules["resolver"] = object()
        return FakeModule

    monkeypatch.setattr(feeds, "_load_module", fake_load_module)
    config = RUN.load_config()

    result = feeds.run_core_outcomes(config)

    assert result["status"] == "ACTIVE_READ_ONLY_CAUSAL_RESOLVER"
    assert sys.modules["resolver"] is sentinel


def test_locate_position_never_guesses_between_same_magic_positions() -> None:
    positions = [
        SimpleNamespace(ticket=1, magic=961201, comment="OTHER_A"),
        SimpleNamespace(ticket=2, magic=961201, comment="OTHER_B"),
    ]
    mt5 = SimpleNamespace(positions_get=lambda **_kwargs: positions)
    assert RUN.locate_position(mt5, "XAUUSD", 961201, "EXPECTED") is None
    assert (
        RUN.locate_position(
            mt5,
            "XAUUSD",
            961201,
            "EXPECTED",
            before_tickets={1},
        ).ticket
        == 2
    )


def test_chart_inputs_must_match_on_the_same_chart(tmp_path) -> None:
    first = tmp_path / "chart01.chr"
    second = tmp_path / "chart02.chr"
    first.write_text(
        "name=Sensor\nInpRunId=LOCKED\nname=Main\n",
        encoding="utf-8",
    )
    second.write_text(
        "name=Sensor\nInpAllowDemoTrading=false\nname=Main\n",
        encoding="utf-8",
    )
    config = RUN.load_config()
    config["preflight"] = {
        "chart_profile_directory": str(tmp_path),
        "forbidden_chart_terms": [],
        "expected_charts": [
            {
                "id": "SENSOR",
                "expert": "Sensor",
                "inputs": {
                    "InpRunId": "LOCKED",
                    "InpAllowDemoTrading": "false",
                },
            }
        ],
    }
    with pytest.raises(RuntimeError, match="chart profile is incomplete"):
        RUN.audit_chart_profile(config, require_ready=True)

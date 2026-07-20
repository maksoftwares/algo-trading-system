from __future__ import annotations

from datetime import UTC, datetime
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from transition_forward import (  # noqa: E402
    COMPONENT_ATTEMPTS,
    OFFICIAL_INSTRUMENTS,
    ROUTER_ATTEMPT,
    completed_hours,
    dependency_sha256,
    route_forward_candidates,
)


def _load_router() -> object:
    path = (
        REPO_ROOT
        / "xau-usd"
        / "xauusd-fast-research"
        / "transition-online-component-router-v11"
        / "src"
        / "router.py"
    )
    spec = importlib.util.spec_from_file_location("v35_test_router", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["v35_test_router"] = module
    spec.loader.exec_module(module)
    return module


def test_completed_hours_excludes_incomplete_end_hour() -> None:
    result = completed_hours(
        datetime(2026, 7, 20, 0, 20, tzinfo=UTC),
        datetime(2026, 7, 20, 2, 59, tzinfo=UTC),
    )
    assert result == [
        datetime(2026, 7, 20, 0, tzinfo=UTC),
        datetime(2026, 7, 20, 1, tzinfo=UTC),
    ]


def test_official_macro_identity_is_exact() -> None:
    assert OFFICIAL_INSTRUMENTS["DOLLARIDXUSD"]["source_code"] == "DOLLAR.IDX-USD"
    assert OFFICIAL_INSTRUMENTS["USTBONDTRUSD"]["source_code"] == "USTBOND.TR-USD"
    assert COMPONENT_ATTEMPTS == (23925, 24877, 24995, 25048)
    assert ROUTER_ATTEMPT == 27135


def test_dependency_hash_is_independent_of_text_line_endings(tmp_path: Path) -> None:
    dependency = tmp_path / "rule.py"
    dependency.write_bytes(b"first\nsecond\n")
    lf_hash = dependency_sha256(tmp_path, ["rule.py"])
    dependency.write_bytes(b"first\r\nsecond\r\n")
    assert dependency_sha256(tmp_path, ["rule.py"]) == lf_hash


def test_router_uses_only_outcomes_closed_strictly_before_entry() -> None:
    entry = pd.Timestamp("2026-07-20T12:00:00Z")
    candidates = pd.DataFrame(
        {
            "candidate_id": ["candidate"],
            "origin_attempt": [23925],
            "scheduled_entry_time": [entry],
        }
    )
    history = pd.DataFrame(
        {
            "attempt_no": [23925, 23925, 23925],
            "exit_time": [
                entry - pd.Timedelta(days=2),
                entry - pd.Timedelta(days=1),
                entry,
            ],
            "stress_net_r": [1.0, -1.5, -100.0],
        }
    )
    frozen = SimpleNamespace(
        router_policy=SimpleNamespace(
            parameters_json=(
                '{"cold_start":"HALF","lookback_days":180,'
                '"minimum_history":1,"threshold":2.0,"weak_multiplier":0.25}'
            ),
            mechanic="TRAILING_DRAWDOWN_GATE",
            router_id="router",
        ),
        router_config={
            "portfolio": {
                "base_weights": {
                    "23925": 1.0,
                    "24877": 0.25,
                    "24995": 0.75,
                    "25048": 0.75,
                }
            }
        },
        router_module=_load_router(),
    )
    routed = route_forward_candidates(candidates, history, frozen)
    assert routed.iloc[0]["shadow_count"] == 2
    assert routed.iloc[0]["shadow_drawdown_r"] == 1.5
    assert routed.iloc[0]["route_multiplier"] == 1.0


def test_package_has_no_broker_action_path() -> None:
    prohibited = ("order_send", "order_check", "TRADE_ACTION", "positions_get")
    for path in [ROOT / "run_shadow.py", ROOT / "src" / "transition_forward.py"]:
        source = path.read_text(encoding="utf-8")
        for token in prohibited:
            assert token not in source

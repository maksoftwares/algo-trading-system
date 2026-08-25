from __future__ import annotations

from datetime import UTC, datetime, timedelta
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
V19_ROOT = REPO_ROOT / "xau-usd" / "xauusd-fast-research" / "v60-dynamic-capacity-twin-prospective-v19"
EXPECTED_CONTRACT = "fdabc9e2997592b06568bb5e405154abdb3888b921a61d70620e06bde2cb4905"
OUTPUT = ROOT / "outputs" / "RESULT.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def utc_ms(value: datetime) -> int:
    return int(round(value.timestamp() * 1000.0))


def fixture_warm_start(source_id: str) -> dict[str, Any]:
    start = datetime(2026, 7, 1, tzinfo=UTC)
    return {
        "retained_history_counts_by_source": {source_id: 50},
        "rows": [
            {
                "source_id": source_id,
                "candidate_id": f"FIXTURE_PRIOR_{index:02d}",
                "closed_at_utc": (start + timedelta(days=index)).isoformat().replace(
                    "+00:00", "Z"
                ),
                "pnl_usd": -1.0,
            }
            for index in range(20)
        ],
    }


def build_candidate(replay: Any, source: dict[str, Any], *, trade_id: str, entry: datetime, exit: datetime, pnl: float):
    return replay.Candidate(
        trade_id=trade_id,
        source_id=str(source["source_id"]),
        specialist_id=str(source["specialist_id"]),
        sleeve_type=str(source["sleeve_type"]),
        entry_ms=utc_ms(entry),
        exit_ms=utc_ms(exit),
        direction="LONG",
        risk_usd=10.0,
        pnl_usd=float(pnl),
        entry_price=100.2,
        exit_price=100.2 + float(pnl) + 0.3,
        open_cost_usd=0.3,
        maximum_risk_usd=float(source["maximum_risk_usd"]),
        maximum_spread_r=float(source["maximum_spread_r"]),
        maximum_open_positions=int(source["maximum_open_positions"]),
        maximum_entries_per_utc_day=int(source["maximum_entries_per_utc_day"]),
        maximum_entry_gap_minutes=int(source["maximum_entry_gap_minutes"]),
        cooldown_minutes=int(source.get("same_direction_post_loss_cooldown_minutes", 0)),
        event_id=trade_id,
    )


def run() -> dict[str, Any]:
    if str(V19_ROOT) not in sys.path:
        sys.path.insert(0, str(V19_ROOT))
    v19 = load_module("v19_locked_runner_audit", V19_ROOT / "run_evaluation.py")
    config = v19.read_json(V19_ROOT / "config" / "prospective.json")
    lock = v19.validate_contract_lock(Path(config["outputs"]["runtime_directory"]))
    if str(lock["contract_sha256"]) != EXPECTED_CONTRACT:
        raise ValueError("V19 locked contract identity changed")

    replay = load_module(
        "v19_locked_replay_audit",
        v19.resolve(config["inputs"]["tick_replay"]["path"]),
    )
    evaluator = load_module(
        "v19_locked_evaluator_audit",
        v19.resolve(config["inputs"]["shared_evaluator"]["path"]),
    )
    v6_scenario = load_module(
        "v19_locked_v6_scenario_audit",
        v19.resolve(config["inputs"]["v6_scenario"]["path"]),
    )
    portfolio = v19.read_json(v19.resolve(config["inputs"]["v60_config"]["path"]))
    overlay = v19.read_json(v19.resolve(config["inputs"]["protection_overlay"]["path"]))
    portfolio["portfolio_protection"] = overlay["portfolio_protection"]
    source = next(
        row
        for row in portfolio["sources"]
        if row["source_id"] == "V57_BREAK_SWING_H4ADX_HIGH"
    )
    if int(source["maximum_open_positions"]) != 1:
        raise ValueError("Fixture requires the locked V57 one-position cap")

    first_entry = datetime(2026, 8, 27, 12, 0, tzinfo=UTC)
    candidates = [
        build_candidate(
            replay,
            source,
            trade_id="FIXTURE_INFERIOR_OCCUPANT",
            entry=first_entry,
            exit=first_entry + timedelta(minutes=20),
            pnl=-10.30,
        ),
        build_candidate(
            replay,
            source,
            trade_id="FIXTURE_BETTER_REPLACEMENT",
            entry=first_entry + timedelta(minutes=5),
            exit=first_entry + timedelta(minutes=15),
            pnl=19.70,
        ),
    ]
    cycle_ms = np.arange(
        utc_ms(first_entry),
        utc_ms(first_entry + timedelta(minutes=25)) + 1,
        5_000,
        dtype=np.int64,
    )
    quotes = {
        "cycle_ms": cycle_ms,
        "tick_ms": cycle_ms.copy(),
        "bid": np.full(len(cycle_ms), 100.0, dtype=float),
        "ask": np.full(len(cycle_ms), 100.2, dtype=float),
    }
    contract = v19.read_json(v19.resolve(config["inputs"]["tick_replay_contract"]["path"]))
    contract["evaluation"]["entry_start_utc"] = "2026-08-27T00:00:00Z"
    contract["evaluation"]["entry_end_exclusive_utc"] = "2026-08-28T00:00:00Z"
    sealed = v19.read_json(v19.resolve(config["inputs"]["sealed_v6_prospective_contract"]["path"]))
    result = v19.simulate_pair(
        replay=replay,
        evaluator=evaluator,
        v6_scenario=v6_scenario,
        portfolio=portfolio,
        contract=contract,
        candidates=candidates,
        quotes=quotes,
        ranks={
            "FIXTURE_INFERIOR_OCCUPANT": 0.05,
            "FIXTURE_BETTER_REPLACEMENT": 0.50,
        },
        features={
            "FIXTURE_INFERIOR_OCCUPANT": {
                "execution_source_id": source["source_id"],
                "direction": "LONG",
                "rank": 0.05,
                "atr_ratio": 1.0,
                "dist_hi_24h": 2.0,
                "ret_4h": 0.1,
                "ret_24h": 0.2,
            },
            "FIXTURE_BETTER_REPLACEMENT": {
                "execution_source_id": source["source_id"],
                "direction": "LONG",
                "rank": 0.50,
                "atr_ratio": 1.0,
                "dist_hi_24h": 2.0,
                "ret_4h": 0.1,
                "ret_24h": 0.2,
            },
        },
        policy=sealed["lock"]["policy"],
        anti_rule=sealed["lock"]["anti_chase"],
        warm_start=fixture_warm_start(str(source["source_id"])),
        scenario_settings=config["scenario"],
        completed_month_keys=[],
    )
    checks = {
        "baseline_accepts_only_inferior": result["baseline_accepted_ids"]
        == ["FIXTURE_INFERIOR_OCCUPANT"],
        "challenger_accepts_only_replacement": result["challenger_accepted_ids"]
        == ["FIXTURE_BETTER_REPLACEMENT"],
        "v6_veto_is_inferior": result["v6_veto_ids"]
        == ["FIXTURE_INFERIOR_OCCUPANT"],
        "v6_replacement_is_better": result["v6_replacement_accept_ids"]
        == ["FIXTURE_BETTER_REPLACEMENT"],
        "baseline_finishes_flat": int(result["baseline"]["open_positions_at_end"]) == 0,
        "challenger_finishes_flat": int(result["challenger"]["open_positions_at_end"]) == 0,
        "baseline_pnl_exact": abs(float(result["baseline"]["net_pnl_usd"]) + 10.30)
        < 1e-12,
        "challenger_pnl_exact": abs(float(result["challenger"]["net_pnl_usd"]) - 19.70)
        < 1e-12,
    }
    payload = {
        "schema_version": "v19_replacement_capacity_mechanism_audit",
        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "contract_sha256": EXPECTED_CONTRACT,
        "decision": "MECHANISM_PARITY_PASS" if all(checks.values()) else "MECHANISM_PARITY_FAIL",
        "checks": checks,
        "baseline": result["baseline"],
        "challenger": result["challenger"],
        "baseline_accepted_ids": result["baseline_accepted_ids"],
        "challenger_accepted_ids": result["challenger_accepted_ids"],
        "v6_veto_ids": result["v6_veto_ids"],
        "v6_replacement_accept_ids": result["v6_replacement_accept_ids"],
        "broker_action_authorized": False,
        "deployment_authorized": False,
        "economic_evidence": False,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    result = run()
    print(json.dumps(result, sort_keys=True))
    return 0 if result["decision"] == "MECHANISM_PARITY_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

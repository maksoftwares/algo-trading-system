from datetime import UTC, datetime, timedelta

import numpy as np

import run_evaluation as runner


def candidate(replay, source, trade_id, entry, exit, pnl):
    return replay.Candidate(
        trade_id=trade_id,
        source_id=source["source_id"],
        specialist_id=source["specialist_id"],
        sleeve_type=source["sleeve_type"],
        entry_ms=int(entry.timestamp() * 1000),
        exit_ms=int(exit.timestamp() * 1000),
        direction="LONG",
        risk_usd=10.0,
        pnl_usd=pnl,
        entry_price=100.2,
        exit_price=100.2 + pnl + 0.3,
        open_cost_usd=0.3,
        maximum_risk_usd=source["maximum_risk_usd"],
        maximum_spread_r=source["maximum_spread_r"],
        maximum_open_positions=source["maximum_open_positions"],
        maximum_entries_per_utc_day=source["maximum_entries_per_utc_day"],
        maximum_entry_gap_minutes=source["maximum_entry_gap_minutes"],
        cooldown_minutes=source.get("same_direction_post_loss_cooldown_minutes", 0),
        event_id=trade_id,
    )


def test_full_guardian_and_replacement_capacity_path() -> None:
    config = runner.read_json(runner.CONFIG)
    replay = runner.load_module(
        "v19_integration_replay", runner.resolve(config["inputs"]["tick_replay"]["path"])
    )
    evaluator = runner.load_module(
        "v19_integration_evaluator",
        runner.resolve(config["inputs"]["shared_evaluator"]["path"]),
    )
    v6 = runner.load_module(
        "v19_integration_v6", runner.resolve(config["inputs"]["v6_scenario"]["path"])
    )
    portfolio = runner.read_json(runner.resolve(config["inputs"]["v60_config"]["path"]))
    overlay = runner.read_json(runner.resolve(config["inputs"]["protection_overlay"]["path"]))
    portfolio["portfolio_protection"] = overlay["portfolio_protection"]
    source = next(
        row for row in portfolio["sources"] if row["source_id"] == "V57_BREAK_SWING_H4ADX_HIGH"
    )
    start = datetime(2026, 8, 27, 12, tzinfo=UTC)
    candidates = [
        candidate(
            replay,
            source,
            "FIXTURE_INFERIOR_OCCUPANT",
            start,
            start + timedelta(minutes=20),
            -10.30,
        ),
        candidate(
            replay,
            source,
            "FIXTURE_BETTER_REPLACEMENT",
            start + timedelta(minutes=5),
            start + timedelta(minutes=15),
            19.70,
        ),
    ]
    cycles = np.arange(
        int(start.timestamp() * 1000),
        int((start + timedelta(minutes=25)).timestamp() * 1000) + 1,
        5_000,
        dtype=np.int64,
    )
    quotes = {
        "cycle_ms": cycles,
        "tick_ms": cycles.copy(),
        "bid": np.full(len(cycles), 100.0),
        "ask": np.full(len(cycles), 100.2),
    }
    contract = runner.read_json(
        runner.resolve(config["inputs"]["tick_replay_contract"]["path"])
    )
    contract["evaluation"]["entry_start_utc"] = "2026-08-27T00:00:00Z"
    contract["evaluation"]["entry_end_exclusive_utc"] = "2026-08-28T00:00:00Z"
    sealed = runner.read_json(
        runner.resolve(config["inputs"]["sealed_v6_prospective_contract"]["path"])
    )
    prior_start = datetime(2026, 7, 1, tzinfo=UTC)
    warm_start = {
        "retained_history_counts_by_source": {source["source_id"]: 50},
        "rows": [
            {
                "source_id": source["source_id"],
                "candidate_id": f"FIXTURE_PRIOR_{index:02d}",
                "closed_at_utc": (prior_start + timedelta(days=index)).isoformat(),
                "pnl_usd": -1.0,
            }
            for index in range(20)
        ],
    }
    feature = {
        "execution_source_id": source["source_id"],
        "direction": "LONG",
        "atr_ratio": 1.0,
        "dist_hi_24h": 2.0,
        "ret_4h": 0.1,
        "ret_24h": 0.2,
    }
    result = runner.simulate_pair(
        replay=replay,
        evaluator=evaluator,
        v6_scenario=v6,
        portfolio=portfolio,
        contract=contract,
        candidates=candidates,
        quotes=quotes,
        ranks={"FIXTURE_INFERIOR_OCCUPANT": 0.05, "FIXTURE_BETTER_REPLACEMENT": 0.5},
        features={
            "FIXTURE_INFERIOR_OCCUPANT": {**feature, "rank": 0.05},
            "FIXTURE_BETTER_REPLACEMENT": {**feature, "rank": 0.5},
        },
        policy=sealed["lock"]["policy"],
        anti_rule=sealed["lock"]["anti_chase"],
        warm_start=warm_start,
        scenario_settings=config["scenario"],
        completed_month_keys=[],
    )
    assert result["baseline_accepted_ids"] == ["FIXTURE_INFERIOR_OCCUPANT"]
    assert result["challenger_accepted_ids"] == ["FIXTURE_BETTER_REPLACEMENT"]
    assert result["v6_veto_ids"] == ["FIXTURE_INFERIOR_OCCUPANT"]
    assert result["v6_replacement_accept_ids"] == ["FIXTURE_BETTER_REPLACEMENT"]
    assert result["baseline"]["net_pnl_usd"] == -10.30
    assert result["challenger"]["net_pnl_usd"] == 19.70
    assert result["baseline"]["open_positions_at_end"] == 0
    assert result["challenger"]["open_positions_at_end"] == 0

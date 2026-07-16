from __future__ import annotations

import csv
import json
import math
import random
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping, Sequence

from ml.a3_meta_v1.dukascopy_label_factory import (
    HOUR_MS,
    VerifiedTickStore,
    _load_foundation,
    _month_range,
    _parse_utc,
    _sha256_file,
    _write_rows,
)
from ml.a3_meta_v1.dukascopy_xau_history_inventory import resolve_storage_root


DEFAULT_CONTRACT = Path("config/ml/a3_ml_r1_structural_risk_v1.json")
DAY_MS = 24 * HOUR_MS


class StructuralRiskError(RuntimeError):
    pass


def run_r1_structural_risk(
    phase1_root: Path, contract_path: Path | None = None
) -> Path:
    phase1_root = phase1_root.resolve()
    contract_file = (contract_path or phase1_root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    validate_contract(phase1_root, contract)
    rows = load_source_rows(phase1_root, contract)
    source = source_reconciliation(rows, contract)

    admissions: list[dict[str, Any]] = []
    accepted_by_profile: dict[str, list[dict[str, Any]]] = {}
    for profile in contract["profiles"]:
        decisions, accepted = admit_trades(rows, profile, contract)
        admissions.extend({"profile": profile["name"], **row} for row in decisions)
        accepted_by_profile[str(profile["name"])] = accepted

    storage_root = resolve_storage_root(contract)
    foundation = _load_foundation(phase1_root.parents[1])
    last_included = _parse_utc(contract["period"]["end_exclusive_utc"]) - timedelta(
        milliseconds=1
    )
    months = set(
        _month_range(
            contract["period"]["start_utc"][:7],
            f"{last_included.year:04d}-{last_included.month:02d}",
        )
    )
    tick_store = VerifiedTickStore(
        storage_root=storage_root,
        symbol=str(contract["symbol"]),
        foundation=foundation,
        prevalidated_months=months,
    )
    equity, hourly = exact_tick_equity(accepted_by_profile, tick_store, contract)

    profile_results: dict[str, Any] = {}
    episode_rows: list[dict[str, Any]] = []
    for profile in contract["profiles"]:
        name = str(profile["name"])
        accepted = accepted_by_profile[name]
        stats = trade_stats(accepted)
        episodes = exposure_episodes(accepted)
        episode_rows.extend({"profile": name, **row} for row in episodes)
        stability = stability_stats(accepted, contract)
        monte_carlo = episode_monte_carlo(episodes, contract)
        decisions = [row for row in admissions if row["profile"] == name]
        profile_results[name] = {
            "accepted": len(accepted),
            "rejected": len(rows) - len(accepted),
            "rejection_reasons": dict(
                sorted(
                    Counter(
                        row["decision_reason"]
                        for row in decisions
                        if not row["accepted"]
                    ).items()
                )
            ),
            "statistics": stats,
            "equity": equity[name],
            "episodes": episode_summary(episodes),
            "stability": stability,
            "monte_carlo": monte_carlo,
            "risk_limits_respected": risk_limits_respected(decisions, profile),
        }

    gates = gate_results(source, profile_results, contract)
    outputs = {
        key: (phase1_root / value).resolve()
        for key, value in contract["outputs"].items()
    }
    _write_rows(outputs["admissions_csv"], admissions)
    _write_rows(outputs["hourly_equity_csv"], hourly)
    _write_rows(outputs["episodes_csv"], episode_rows)
    payload = {
        "schema_version": contract["schema_version"],
        "classification": "STRUCTURAL_RISK_PASS"
        if all(gates.values())
        else "STRUCTURAL_RISK_FAIL",
        "generated_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace(
            "+00:00", "Z"
        ),
        "source_reconciliation": source,
        "profiles": profile_results,
        "gates": gates,
        "authorization": contract["authorization"],
        "limitations": [
            "All source outcomes are known historical development evidence, not an untouched holdout.",
            "The risk profile is causal but its historical result cannot establish new alpha.",
            "Episode-block Monte Carlo resamples episode net outcomes and does not invent intraday tick paths.",
            "Historical broker liquidation rules are approximated by the frozen margin-call level.",
        ],
        "artifacts": {
            "contract": str(contract_file),
            "contract_sha256": _sha256_file(contract_file),
            "admissions_csv": _artifact(outputs["admissions_csv"]),
            "hourly_equity_csv": _artifact(outputs["hourly_equity_csv"]),
            "episodes_csv": _artifact(outputs["episodes_csv"]),
        },
    }
    outputs["report_json"].parent.mkdir(parents=True, exist_ok=True)
    outputs["report_json"].write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    outputs["report_markdown"].write_text(render_report(payload), encoding="utf-8")
    return outputs["report_json"]


def validate_contract(phase1_root: Path, contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_r1_structural_risk_v1":
        raise StructuralRiskError("unsupported R1 structural-risk contract")
    if [row.get("name") for row in contract.get("profiles", [])] != [
        "frozen_r1_baseline",
        "demo_guard_10k",
    ]:
        raise StructuralRiskError("structural-risk profiles differ from the frozen order")
    authorization = contract.get("authorization", {})
    if authorization.get("research_only") is not True or any(
        authorization.get(key) is not False
        for key in (
            "strategy_promotion_authorized",
            "python_demo_predictions_authorized",
            "ea_consumption_authorized",
            "broker_action_authorized",
        )
    ):
        raise StructuralRiskError("structural-risk authorization boundary is open")
    for source in contract.get("source_lock", []):
        path = (phase1_root / str(source["path"])).resolve()
        if not path.is_file() or _sha256_file(path) != source["sha256"]:
            raise StructuralRiskError(f"source lock mismatch: {path}")
    if float(contract["account"]["server_utc_offset_hours"]) != 4.0:
        raise StructuralRiskError("structural-risk server day must remain UTC+4")


def load_source_rows(
    phase1_root: Path, contract: Mapping[str, Any]
) -> list[dict[str, Any]]:
    source = phase1_root / next(
        row["path"]
        for row in contract["source_lock"]
        if str(row["path"]).endswith("SELECTED_LABELS_V1.csv")
    )
    output: list[dict[str, Any]] = []
    units = float(contract["account"]["contract_size_ounces_per_lot"]) * float(
        contract["account"]["lot_size"]
    )
    leverage = float(contract["account"]["leverage"])
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        for raw in csv.DictReader(handle):
            if raw["family_id"] != contract["family_id"]:
                continue
            entry = _parse_utc(raw["entry_time_utc"])
            exit_time = _parse_utc(raw["exit_time_utc"])
            entry_price = float(raw["entry_price"])
            planned_stop = float(raw["planned_stop"])
            row = {
                **raw,
                "entry_dt": entry,
                "exit_dt": exit_time,
                "entry_ms": int(entry.timestamp() * 1000),
                "exit_ms": int(exit_time.timestamp() * 1000),
                "entry_price_value": entry_price,
                "entry_bid_value": float(raw["entry_bid"]),
                "gross_pnl_value": float(raw["gross_pnl_usd"]),
                "holding_stress_value": float(raw["holding_stress_usd"]),
                "stress_net_value": float(raw["stress_net_pnl_usd"]),
                "initial_risk_usd": max(0.0, entry_price - planned_stop) * units,
                "margin_usd": entry_price * units / leverage,
                "units": units,
            }
            if row["exit_ms"] < row["entry_ms"]:
                raise StructuralRiskError(f"trade exits before entry: {raw['candidate_id']}")
            output.append(row)
    output.sort(key=lambda row: (row["entry_ms"], row["candidate_id"]))
    if len({row["candidate_id"] for row in output}) != len(output):
        raise StructuralRiskError("duplicate R1 candidate IDs")
    return output


def source_reconciliation(
    rows: Sequence[Mapping[str, Any]], contract: Mapping[str, Any]
) -> dict[str, Any]:
    stats = trade_stats(rows)
    expected = contract["expected_source"]
    return {
        **stats,
        "trade_count_matches": len(rows) == int(expected["selected_r1_trades"]),
        "stress_net_matches": math.isclose(
            stats["stress_net_usd"],
            float(expected["stress_net_usd"]),
            abs_tol=0.01,
        ),
        "stress_profit_factor_matches": math.isclose(
            stats["stress_profit_factor"] or 0.0,
            float(expected["stress_profit_factor"]),
            abs_tol=1e-9,
        ),
    }


def admit_trades(
    rows: Sequence[dict[str, Any]],
    profile: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    balance = float(contract["account"]["initial_balance_usd"])
    extra_cost = float(contract["execution_stress"]["extra_cost_per_trade_usd"])
    offset = timedelta(hours=int(contract["account"]["server_utc_offset_hours"]))
    open_rows: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    accepted: list[dict[str, Any]] = []
    daily_start: dict[str, float] = {}
    daily_realized: defaultdict[str, float] = defaultdict(float)

    def close_until(timestamp_ms: int) -> None:
        nonlocal balance, open_rows
        closing = sorted(
            (row for row in open_rows if row["exit_ms"] <= timestamp_ms),
            key=lambda row: (row["exit_ms"], row["candidate_id"]),
        )
        for row in closing:
            day = (row["exit_dt"] + offset).date().isoformat()
            daily_start.setdefault(day, balance)
            realized = row["gross_pnl_value"] - row["holding_stress_value"]
            balance += realized
            daily_realized[day] += realized
        closing_ids = {row["candidate_id"] for row in closing}
        open_rows = [row for row in open_rows if row["candidate_id"] not in closing_ids]

    for row in rows:
        close_until(int(row["entry_ms"]))
        day = (row["entry_dt"] + offset).date().isoformat()
        daily_start.setdefault(day, balance)
        bid = float(row["entry_bid_value"])
        holding = sum(
            (row["entry_ms"] - other["entry_ms"])
            / DAY_MS
            * float(contract["execution_stress"]["holding_cost_per_24h_usd"])
            for other in open_rows
        )
        floating = sum(
            (bid - other["entry_price_value"]) * other["units"]
            for other in open_rows
        )
        equity = balance + floating - holding
        denominator = max(equity, 0.01)
        open_risk = sum(other["initial_risk_usd"] for other in open_rows)
        open_margin = sum(other["margin_usd"] for other in open_rows)
        trade_risk_pct = 100.0 * row["initial_risk_usd"] / denominator
        total_risk_pct = 100.0 * (open_risk + row["initial_risk_usd"]) / denominator
        margin_pct = 100.0 * (open_margin + row["margin_usd"]) / denominator
        daily_loss_pct = (
            100.0
            * max(0.0, -daily_realized[day])
            / max(daily_start[day], 0.01)
        )
        checks = (
            (
                len(open_rows) >= int(profile["maximum_concurrent_positions"]),
                "MAX_CONCURRENT_POSITIONS",
            ),
            (
                trade_risk_pct
                > float(profile["maximum_trade_initial_risk_pct"]),
                "MAX_TRADE_INITIAL_RISK",
            ),
            (
                total_risk_pct
                > float(profile["maximum_total_initial_risk_pct"]),
                "MAX_TOTAL_INITIAL_RISK",
            ),
            (
                total_risk_pct
                > float(profile["maximum_same_direction_initial_risk_pct"]),
                "MAX_SAME_DIRECTION_INITIAL_RISK",
            ),
            (
                margin_pct > float(profile["maximum_margin_utilization_pct"]),
                "MAX_MARGIN_UTILIZATION",
            ),
            (
                daily_loss_pct >= float(profile["daily_realized_loss_halt_pct"]),
                "DAILY_REALIZED_LOSS_HALT",
            ),
        )
        reason = next((code for failed, code in checks if failed), "ACCEPT")
        is_accepted = reason == "ACCEPT"
        decisions.append(
            {
                "candidate_id": row["candidate_id"],
                "entry_time_utc": row["entry_time_utc"],
                "accepted": is_accepted,
                "decision_reason": reason,
                "balance_before_usd": balance,
                "equity_before_usd": equity,
                "open_positions_before": len(open_rows),
                "trade_initial_risk_usd": row["initial_risk_usd"],
                "trade_initial_risk_pct": trade_risk_pct,
                "total_initial_risk_pct_after": total_risk_pct,
                "same_direction_initial_risk_pct_after": total_risk_pct,
                "margin_utilization_pct_after": margin_pct,
                "daily_realized_loss_pct": daily_loss_pct,
            }
        )
        if is_accepted:
            balance -= extra_cost
            daily_realized[day] -= extra_cost
            open_rows.append(row)
            accepted.append(row)
    return decisions, accepted


def exact_tick_equity(
    accepted_by_profile: Mapping[str, Sequence[dict[str, Any]]],
    tick_store: VerifiedTickStore,
    contract: Mapping[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    initial = float(contract["account"]["initial_balance_usd"])
    extra = float(contract["execution_stress"]["extra_cost_per_trade_usd"])
    holding_per_day = float(contract["execution_stress"]["holding_cost_per_24h_usd"])
    capital_values = [float(value) for value in contract["capital_observation_balances_usd"]]
    states = {
        name: _equity_state(rows, initial, capital_values)
        for name, rows in accepted_by_profile.items()
    }
    active_hours: set[int] = set()
    for rows in accepted_by_profile.values():
        for row in rows:
            hour = int(row["entry_ms"]) - int(row["entry_ms"]) % HOUR_MS
            end = int(row["exit_ms"]) - int(row["exit_ms"]) % HOUR_MS
            while hour <= end:
                active_hours.add(hour)
                hour += HOUR_MS
    hourly: list[dict[str, Any]] = []
    for hour_ms in sorted(active_hours):
        ticks = tick_store.load_hour(hour_ms)
        if not ticks:
            continue
        for tick in ticks:
            timestamp_ms = int(tick.timestamp_ms)
            bid = float(tick.bid)
            for state in states.values():
                _process_events_at_tick(state, timestamp_ms, bid, extra, holding_per_day)
                _mark_state(state, timestamp_ms, bid, holding_per_day, contract)
        for name, state in states.items():
            hourly.append(
                {
                    "profile": name,
                    "hour_utc": datetime.fromtimestamp(hour_ms / 1000, UTC)
                    .isoformat(timespec="seconds")
                    .replace("+00:00", "Z"),
                    "last_bid": float(ticks[-1].bid),
                    "stress_balance_usd": state["stress_balance"],
                    "stress_equity_usd": state["last_stress_equity"],
                    "drawdown_usd": state["peak_stress_equity"]
                    - state["last_stress_equity"],
                    "open_positions": len(state["open"]),
                    "margin_usd": state["open_margin"],
                    "original_stop_risk_usd": state["open_risk"],
                }
            )
    output: dict[str, Any] = {}
    for name, state in states.items():
        if state["event_index"] != len(state["events"]) or state["open"]:
            raise StructuralRiskError(f"unprocessed tick events remain for {name}")
        output[name] = {
            "ticks_marked": state["ticks_marked"],
            "final_native_balance_usd": state["native_balance"],
            "final_stress_balance_usd": state["stress_balance"],
            "max_floating_drawdown_usd": state["max_drawdown"],
            "max_floating_drawdown_pct": 100.0 * state["max_drawdown_fraction"],
            "max_floating_drawdown_timestamp_utc": _iso_ms(
                state["max_drawdown_timestamp_ms"]
            ),
            "max_concurrent_positions": state["max_positions"],
            "max_original_stop_risk_usd": state["max_open_risk"],
            "max_margin_usd": state["max_margin"],
            "max_margin_utilization_pct": 100.0 * state["max_margin_fraction"],
            "minimum_margin_level_pct": 100.0 * state["minimum_margin_level"],
            "gross_exit_reconciliation_max_abs_usd": state[
                "gross_reconciliation_max_abs"
            ],
            "capital_observations": {
                f"{capital:.2f}": {
                    "max_floating_drawdown_usd": item["max_drawdown"],
                    "max_floating_drawdown_pct": 100.0 * item["max_drawdown_fraction"],
                    "minimum_equity_usd": item["minimum_equity"],
                    "margin_call_observed": item["margin_call_observed"],
                }
                for capital, item in state["capital"].items()
            },
        }
    return output, hourly


def _equity_state(
    rows: Sequence[dict[str, Any]], initial: float, capital_values: Sequence[float]
) -> dict[str, Any]:
    events = sorted(
        [
            event
            for row in rows
            for event in (
                (int(row["entry_ms"]), 1, row),
                (int(row["exit_ms"]), 0, row),
            )
        ],
        key=lambda item: (item[0], item[1], item[2]["candidate_id"]),
    )
    return {
        "initial": initial,
        "events": events,
        "event_index": 0,
        "open": {},
        "open_units": 0.0,
        "open_entry_value": 0.0,
        "open_entry_ms_sum": 0,
        "open_margin": 0.0,
        "open_risk": 0.0,
        "native_balance": initial,
        "stress_balance": initial,
        "last_stress_equity": initial,
        "peak_stress_equity": initial,
        "max_drawdown": 0.0,
        "max_drawdown_fraction": 0.0,
        "max_drawdown_timestamp_ms": 0,
        "max_positions": 0,
        "max_open_risk": 0.0,
        "max_margin": 0.0,
        "max_margin_fraction": 0.0,
        "minimum_margin_level": math.inf,
        "gross_reconciliation_max_abs": 0.0,
        "ticks_marked": 0,
        "capital": {
            capital: {
                "peak": capital,
                "max_drawdown": 0.0,
                "max_drawdown_fraction": 0.0,
                "minimum_equity": capital,
                "margin_call_observed": False,
            }
            for capital in capital_values
        },
    }


def _process_events_at_tick(
    state: dict[str, Any],
    timestamp_ms: int,
    bid: float,
    extra: float,
    holding_per_day: float,
) -> None:
    events = state["events"]
    index = int(state["event_index"])
    if index < len(events) and events[index][0] < timestamp_ms:
        raise StructuralRiskError(
            f"no source tick matched event {events[index][2]['candidate_id']} at {events[index][0]}"
        )
    if index >= len(events) or events[index][0] != timestamp_ms:
        return
    _mark_state_values(state, timestamp_ms, bid, holding_per_day)
    while index < len(events) and events[index][0] == timestamp_ms:
        _, event_type, row = events[index]
        key = row["candidate_id"]
        if event_type == 0:
            if key not in state["open"]:
                raise StructuralRiskError(f"exit without open position: {key}")
            expected = (bid - row["entry_price_value"]) * row["units"]
            state["gross_reconciliation_max_abs"] = max(
                state["gross_reconciliation_max_abs"],
                abs(expected - row["gross_pnl_value"]),
            )
            state["native_balance"] += row["gross_pnl_value"]
            state["stress_balance"] += (
                row["gross_pnl_value"] - row["holding_stress_value"]
            )
            _remove_open(state, row)
        else:
            if key in state["open"]:
                raise StructuralRiskError(f"duplicate open position: {key}")
            state["stress_balance"] -= extra
            _add_open(state, row)
        index += 1
    state["event_index"] = index


def _add_open(state: dict[str, Any], row: Mapping[str, Any]) -> None:
    state["open"][row["candidate_id"]] = row
    state["open_units"] += row["units"]
    state["open_entry_value"] += row["entry_price_value"] * row["units"]
    state["open_entry_ms_sum"] += row["entry_ms"]
    state["open_margin"] += row["margin_usd"]
    state["open_risk"] += row["initial_risk_usd"]
    state["max_positions"] = max(state["max_positions"], len(state["open"]))
    state["max_open_risk"] = max(state["max_open_risk"], state["open_risk"])
    state["max_margin"] = max(state["max_margin"], state["open_margin"])


def _remove_open(state: dict[str, Any], row: Mapping[str, Any]) -> None:
    del state["open"][row["candidate_id"]]
    state["open_units"] -= row["units"]
    state["open_entry_value"] -= row["entry_price_value"] * row["units"]
    state["open_entry_ms_sum"] -= row["entry_ms"]
    state["open_margin"] -= row["margin_usd"]
    state["open_risk"] -= row["initial_risk_usd"]


def _mark_state(
    state: dict[str, Any],
    timestamp_ms: int,
    bid: float,
    holding_per_day: float,
    contract: Mapping[str, Any],
) -> None:
    stress_equity = _mark_state_values(state, timestamp_ms, bid, holding_per_day)
    state["ticks_marked"] += 1
    state["last_stress_equity"] = stress_equity
    if stress_equity > state["peak_stress_equity"]:
        state["peak_stress_equity"] = stress_equity
    drawdown = state["peak_stress_equity"] - stress_equity
    fraction = drawdown / max(state["peak_stress_equity"], 0.01)
    if fraction > state["max_drawdown_fraction"]:
        state["max_drawdown"] = drawdown
        state["max_drawdown_fraction"] = fraction
        state["max_drawdown_timestamp_ms"] = timestamp_ms
    margin_fraction = state["open_margin"] / max(stress_equity, 0.01)
    state["max_margin_fraction"] = max(
        state["max_margin_fraction"], margin_fraction
    )
    if state["open_margin"] > 0.0:
        state["minimum_margin_level"] = min(
            state["minimum_margin_level"], stress_equity / state["open_margin"]
        )
    for capital, item in state["capital"].items():
        equity = capital + (stress_equity - state["initial"])
        item["minimum_equity"] = min(item["minimum_equity"], equity)
        item["peak"] = max(item["peak"], equity)
        capital_drawdown = item["peak"] - equity
        capital_fraction = capital_drawdown / max(item["peak"], 0.01)
        if capital_fraction > item["max_drawdown_fraction"]:
            item["max_drawdown"] = capital_drawdown
            item["max_drawdown_fraction"] = capital_fraction
        margin_call_fraction = float(contract["account"]["margin_call_level_pct"]) / 100.0
        if state["open_margin"] > 0.0 and equity / state["open_margin"] <= margin_call_fraction:
            item["margin_call_observed"] = True


def _mark_state_values(
    state: Mapping[str, Any],
    timestamp_ms: int,
    bid: float,
    holding_per_day: float,
) -> float:
    floating = bid * state["open_units"] - state["open_entry_value"]
    holding = (
        timestamp_ms * len(state["open"]) - state["open_entry_ms_sum"]
    ) / DAY_MS * holding_per_day
    return state["stress_balance"] + floating - holding


def trade_stats(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: (row["exit_ms"], row["candidate_id"]))
    pnl = [float(row["stress_net_value"]) for row in ordered]
    gross_profit = sum(value for value in pnl if value > 0.0)
    gross_loss = -sum(value for value in pnl if value < 0.0)
    net = sum(pnl)
    return {
        "trades": len(rows),
        "wins": sum(value > 0.0 for value in pnl),
        "win_rate_pct": 100.0 * sum(value > 0.0 for value in pnl) / len(pnl)
        if pnl
        else 0.0,
        "stress_net_usd": net,
        "stress_profit_factor": gross_profit / gross_loss if gross_loss > 0.0 else None,
        "max_closed_drawdown_usd": max_drawdown(pnl),
    }


def exposure_episodes(
    rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    episodes: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda item: (item["entry_ms"], item["candidate_id"])):
        if not episodes or int(row["entry_ms"]) > int(episodes[-1]["end_ms"]):
            episodes.append(
                {
                    "episode_id": f"episode_{len(episodes) + 1:04d}",
                    "start_ms": int(row["entry_ms"]),
                    "end_ms": int(row["exit_ms"]),
                    "start_utc": row["entry_time_utc"],
                    "end_utc": row["exit_time_utc"],
                    "trades": 1,
                    "stress_net_usd": float(row["stress_net_value"]),
                }
            )
        else:
            episode = episodes[-1]
            if int(row["exit_ms"]) > int(episode["end_ms"]):
                episode["end_ms"] = int(row["exit_ms"])
                episode["end_utc"] = row["exit_time_utc"]
            episode["trades"] += 1
            episode["stress_net_usd"] += float(row["stress_net_value"])
    return episodes


def episode_summary(episodes: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    net = sum(float(row["stress_net_usd"]) for row in episodes)
    winners = sorted(
        (float(row["stress_net_usd"]) for row in episodes if float(row["stress_net_usd"]) > 0.0),
        reverse=True,
    )
    return {
        "episodes": len(episodes),
        "net_usd": net,
        "top_episode_profit_share": winners[0] / net
        if winners and net > 0.0
        else None,
        "top_three_episodes_removed_net_usd": net - sum(winners[:3]),
        "largest_episode_trades": max(
            (int(row["trades"]) for row in episodes), default=0
        ),
    }


def stability_stats(
    rows: Sequence[Mapping[str, Any]], contract: Mapping[str, Any]
) -> dict[str, Any]:
    pnl_by_month: defaultdict[str, float] = defaultdict(float)
    for row in rows:
        pnl_by_month[str(row["exit_time_utc"])[:7]] += float(row["stress_net_value"])
    months = [
        f"{year:04d}-{month:02d}"
        for year, month in _month_range(
            contract["period"]["start_utc"][:7],
            "2026-06",
        )
    ]
    blocks = [
        sum(pnl_by_month[month] for month in months[index : index + 6])
        for index in range(len(months) - 5)
    ]
    return {
        "rolling_six_month_blocks": len(blocks),
        "positive_six_month_share": sum(value > 0.0 for value in blocks) / len(blocks),
    }


def episode_monte_carlo(
    episodes: Sequence[Mapping[str, Any]], contract: Mapping[str, Any]
) -> dict[str, Any]:
    settings = contract["monte_carlo"]
    rng = random.Random(int(settings["seed"]))
    values = [float(row["stress_net_usd"]) for row in episodes]
    initial = float(contract["account"]["initial_balance_usd"])
    ruin_level = initial * float(settings["ruin_equity_fraction"])
    warning = float(settings["drawdown_warning_fraction"])
    simulations = int(settings["simulations"])
    ruins = 0
    warnings = 0
    drawdowns: list[float] = []
    for _ in range(simulations):
        equity = initial
        peak = initial
        maximum = 0.0
        ruined = False
        for _ in values:
            equity += values[rng.randrange(len(values))]
            peak = max(peak, equity)
            maximum = max(maximum, (peak - equity) / max(peak, 0.01))
            ruined = ruined or equity <= ruin_level
        ruins += ruined
        warnings += maximum >= warning
        drawdowns.append(maximum)
    drawdowns.sort()
    return {
        "seed": int(settings["seed"]),
        "simulations": simulations,
        "episodes_per_simulation": len(values),
        "ruin_probability": ruins / simulations,
        "drawdown_warning_probability": warnings / simulations,
        "median_max_drawdown_pct": 100.0 * percentile(drawdowns, 0.5),
        "p95_max_drawdown_pct": 100.0 * percentile(drawdowns, 0.95),
    }


def risk_limits_respected(
    decisions: Sequence[Mapping[str, Any]], profile: Mapping[str, Any]
) -> bool:
    return all(
        int(row["open_positions_before"])
        < int(profile["maximum_concurrent_positions"])
        and float(row["trade_initial_risk_pct"])
        <= float(profile["maximum_trade_initial_risk_pct"]) + 1e-9
        and float(row["total_initial_risk_pct_after"])
        <= float(profile["maximum_total_initial_risk_pct"]) + 1e-9
        and float(row["same_direction_initial_risk_pct_after"])
        <= float(profile["maximum_same_direction_initial_risk_pct"]) + 1e-9
        and float(row["margin_utilization_pct_after"])
        <= float(profile["maximum_margin_utilization_pct"]) + 1e-9
        and float(row["daily_realized_loss_pct"])
        < float(profile["daily_realized_loss_halt_pct"]) + 1e-9
        for row in decisions
        if row["accepted"]
    )


def gate_results(
    source: Mapping[str, Any],
    profiles: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, bool]:
    baseline = profiles["frozen_r1_baseline"]
    controlled = profiles["demo_guard_10k"]
    gates = contract["gates"]
    return {
        "source_reconciles": all(
            source[key]
            for key in (
                "trade_count_matches",
                "stress_net_matches",
                "stress_profit_factor_matches",
            )
        ),
        "baseline_admits_all_source_trades": baseline["accepted"]
        == int(contract["expected_source"]["selected_r1_trades"]),
        "baseline_final_stress_net_reconciles": math.isclose(
            baseline["equity"]["final_stress_balance_usd"]
            - float(contract["account"]["initial_balance_usd"]),
            source["stress_net_usd"],
            abs_tol=0.01,
        ),
        "tick_exit_prices_reconcile": all(
            row["equity"]["gross_exit_reconciliation_max_abs_usd"] <= 0.011
            for row in profiles.values()
        ),
        "baseline_floating_drawdown": baseline["equity"][
            "max_floating_drawdown_pct"
        ]
        <= float(gates["maximum_baseline_floating_drawdown_pct"]),
        "controlled_stress_profit_factor": (
            controlled["statistics"]["stress_profit_factor"] or 0.0
        )
        >= float(gates["minimum_controlled_stress_profit_factor"]),
        "controlled_trade_retention": controlled["accepted"]
        / max(baseline["accepted"], 1)
        >= float(gates["minimum_controlled_trade_retention_fraction"]),
        "controlled_net_retention": controlled["statistics"]["stress_net_usd"]
        / max(baseline["statistics"]["stress_net_usd"], 0.01)
        >= float(gates["minimum_controlled_net_retention_fraction"]),
        "controlled_floating_drawdown": controlled["equity"][
            "max_floating_drawdown_pct"
        ]
        <= float(gates["maximum_controlled_floating_drawdown_pct"]),
        "controlled_episode_concentration": controlled["episodes"][
            "top_episode_profit_share"
        ]
        is not None
        and controlled["episodes"]["top_episode_profit_share"]
        <= float(gates["maximum_controlled_top_episode_profit_share"]),
        "controlled_top_three_removed_positive": controlled["episodes"][
            "top_three_episodes_removed_net_usd"
        ]
        > 0.0,
        "controlled_six_month_stability": controlled["stability"][
            "positive_six_month_share"
        ]
        >= float(gates["minimum_controlled_positive_six_month_share"]),
        "controlled_monte_carlo_ruin": controlled["monte_carlo"][
            "ruin_probability"
        ]
        <= float(gates["maximum_monte_carlo_ruin_probability"]),
        "controlled_monte_carlo_drawdown": controlled["monte_carlo"][
            "drawdown_warning_probability"
        ]
        <= float(gates["maximum_monte_carlo_drawdown_warning_probability"]),
        "risk_limits_respected": controlled["risk_limits_respected"],
        "no_margin_call_at_10k": not controlled["equity"]["capital_observations"][
            "10000.00"
        ]["margin_call_observed"],
        "authorization_closed": contract["authorization"]["research_only"]
        and not any(
            contract["authorization"][key]
            for key in contract["authorization"]
            if key != "research_only"
        ),
    }


def render_report(payload: Mapping[str, Any]) -> str:
    baseline = payload["profiles"]["frozen_r1_baseline"]
    controlled = payload["profiles"]["demo_guard_10k"]
    lines = [
        "# A3 ML R1 Structural Risk V1",
        "",
        f"Classification: `{payload['classification']}`",
        "",
        "Known-history portfolio engineering only. Demo and broker action remain disabled.",
        "",
        "## Profiles",
        "",
        "| Profile | Accepted | Stress net | PF | Exact floating DD | Max positions | Max stop risk |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, row in (("Frozen baseline", baseline), ("Demo guard", controlled)):
        lines.append(
            f"| {name} | {row['accepted']} | {row['statistics']['stress_net_usd']:.2f} | "
            f"{row['statistics']['stress_profit_factor'] or 0.0:.4f} | "
            f"{row['equity']['max_floating_drawdown_usd']:.2f} "
            f"({row['equity']['max_floating_drawdown_pct']:.2f}%) | "
            f"{row['equity']['max_concurrent_positions']} | "
            f"{row['equity']['max_original_stop_risk_usd']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Controlled Diagnostics",
            "",
            f"- Rejected: `{controlled['rejected']}` ({controlled['rejection_reasons']})",
            f"- Top episode profit share: `{controlled['episodes']['top_episode_profit_share'] or 0.0:.4f}`",
            f"- Net after removing top three episodes: `${controlled['episodes']['top_three_episodes_removed_net_usd']:.2f}`",
            f"- Positive rolling six-month share: `{controlled['stability']['positive_six_month_share']:.4f}`",
            f"- Monte Carlo ruin probability: `{controlled['monte_carlo']['ruin_probability']:.4f}`",
            f"- Monte Carlo P(DD >= 15%): `{controlled['monte_carlo']['drawdown_warning_probability']:.4f}`",
            "",
            "## Capital Observations",
            "",
        ]
    )
    for capital, row in controlled["equity"]["capital_observations"].items():
        lines.append(
            f"- `${float(capital):.2f}`: DD `{row['max_floating_drawdown_pct']:.2f}%`, "
            f"minimum equity `${row['minimum_equity_usd']:.2f}`, margin call "
            f"`{'YES' if row['margin_call_observed'] else 'NO'}`"
        )
    lines.extend(["", "## Gates", ""])
    for name, passed in payload["gates"].items():
        lines.append(f"- `{name}`: {'PASS' if passed else 'FAIL'}")
    lines.extend(["", "No authorization flag changed.", ""])
    return "\n".join(lines)


def max_drawdown(values: Sequence[float]) -> float:
    equity = 0.0
    peak = 0.0
    maximum = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        maximum = max(maximum, peak - equity)
    return maximum


def percentile(values: Sequence[float], probability: float) -> float:
    if not values:
        return 0.0
    position = probability * (len(values) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(values[lower])
    weight = position - lower
    return float(values[lower] * (1.0 - weight) + values[upper] * weight)


def _iso_ms(timestamp_ms: int) -> str:
    if timestamp_ms <= 0:
        return ""
    return datetime.fromtimestamp(timestamp_ms / 1000, UTC).isoformat(
        timespec="milliseconds"
    ).replace("+00:00", "Z")


def _artifact(path: Path) -> dict[str, str]:
    return {"path": str(path), "sha256": _sha256_file(path)}

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import UTC, datetime
import json
import math
import os
from pathlib import Path
import tempfile
import time
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from src.capacity import (
    FINAL_RESOLUTION_STATUSES,
    advance_resolution,
    canonical_sha256,
    completed_tick_paths,
    five_second_cycles,
    initial_resolution,
    load_candidate_facts,
    load_causal_scores,
    load_module,
    load_tick_day,
    resolution_to_replay_candidate,
    sha256_file,
    tick_file_date,
    timestamp_ms,
    utc_timestamp,
    warm_started_challenger_class,
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG = ROOT / "config" / "prospective.json"
LOCK = ROOT / "outputs" / "CONTRACT_LOCK.json"


def resolve(path: str) -> Path:
    value = Path(path)
    return value if value.is_absolute() else REPO_ROOT / value


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def json_clean(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): json_clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_clean(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    return value


def validate_config(config: Mapping[str, Any]) -> None:
    authorization = config["authorization"]
    if not bool(authorization.get("read_only_inputs")):
        raise ValueError("V19 must explicitly use read-only inputs")
    if any(
        bool(authorization.get(key))
        for key in ("broker_actions", "runtime_changes", "demo_deployment", "live_deployment")
    ):
        raise ValueError("V19 has forbidden authorization")
    for name, item in config["inputs"].items():
        if not isinstance(item, Mapping) or "sha256" not in item:
            continue
        path = resolve(str(item["path"]))
        actual = sha256_file(path)
        if actual != str(item["sha256"]):
            raise ValueError(f"Locked V19 dependency changed: {name}: {actual}")


def validate_contract_lock(runtime: Path) -> dict[str, Any]:
    if not LOCK.is_file():
        raise FileNotFoundError("V19 contract lock is absent")
    lock = read_json(LOCK)
    unsigned = {key: value for key, value in lock.items() if key != "contract_sha256"}
    if canonical_sha256(unsigned) != str(lock.get("contract_sha256")):
        raise ValueError("V19 contract self-hash is invalid")
    for relative, identity in lock["package_files"].items():
        path = ROOT / relative
        if int(path.stat().st_size) != int(identity["bytes"]):
            raise ValueError(f"V19 locked file size changed: {relative}")
        if sha256_file(path) != str(identity["sha256"]):
            raise ValueError(f"V19 locked file hash changed: {relative}")
    runtime_lock = runtime / read_json(CONFIG)["outputs"]["contract_lock"]
    if not runtime_lock.is_file() or sha256_file(runtime_lock) != sha256_file(LOCK):
        raise ValueError("V19 runtime contract lock is absent or changed")
    return lock


def initial_state(boundary: pd.Timestamp, contract_hash: str) -> dict[str, Any]:
    return {
        "schema_version": "v60_dynamic_capacity_twin_v19_state",
        "contract_sha256": contract_hash,
        "boundary_utc": boundary.isoformat().replace("+00:00", "Z"),
        "candidate_prefixes": {},
        "candidate_resolutions": {},
        "tick_files": {},
        "run_sequence": 0,
        "previous_state_sha256": None,
    }


def state_sha256(state: Mapping[str, Any]) -> str:
    return canonical_sha256(
        {key: value for key, value in state.items() if key != "state_sha256"}
    )


def load_state(path: Path, boundary: pd.Timestamp, contract_hash: str) -> dict[str, Any]:
    if not path.is_file():
        return initial_state(boundary, contract_hash)
    state = read_json(path)
    if state.get("schema_version") != "v60_dynamic_capacity_twin_v19_state":
        raise ValueError("Unexpected V19 state schema")
    if str(state.get("contract_sha256")) != contract_hash:
        raise ValueError("V19 state belongs to another locked contract")
    if utc_timestamp(state["boundary_utc"]) != boundary:
        raise ValueError("V19 state boundary changed")
    if str(state.get("state_sha256")) != state_sha256(state):
        raise ValueError("V19 persisted state self-hash changed")
    return state


def quote_cache_path(runtime: Path, day) -> Path:
    return runtime / "quotes" / f"{day:%Y%m%d}.npz"


def save_quote_cache(runtime: Path, ticks, poll_seconds: int) -> dict[str, Any]:
    path = quote_cache_path(runtime, ticks.day)
    cycles = five_second_cycles(ticks, poll_seconds)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp.npz")
    np.savez_compressed(temporary, **cycles)
    os.replace(temporary, path)
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "cycles": int(len(cycles["cycle_ms"])),
        "first_cycle_msc": int(cycles["cycle_ms"][0]) if len(cycles["cycle_ms"]) else None,
        "last_cycle_msc": int(cycles["cycle_ms"][-1]) if len(cycles["cycle_ms"]) else None,
    }


def load_quotes(runtime: Path, tick_records: Sequence[Mapping[str, Any]]) -> dict[str, np.ndarray]:
    parts: dict[str, list[np.ndarray]] = {
        "cycle_ms": [],
        "tick_ms": [],
        "bid": [],
        "ask": [],
    }
    for record in sorted(tick_records, key=lambda item: str(item["day"])):
        cache = record["quote_cache"]
        path = Path(str(cache["path"]))
        if sha256_file(path) != str(cache["sha256"]):
            raise ValueError(f"V19 quote cache changed: {path}")
        with np.load(path) as payload:
            for key in parts:
                parts[key].append(np.asarray(payload[key]))
    return {
        key: np.concatenate(values) if values else np.asarray([], dtype=np.int64 if key.endswith("ms") else float)
        for key, values in parts.items()
    }


def load_scores(
    config: Mapping[str, Any], evidence_reader: Any
) -> tuple[dict, dict, dict, dict]:
    chain = Path(str(config["inputs"]["sealed_v6_evidence_chain"]))
    records = evidence_reader.load_chain(chain)
    return load_causal_scores(
        records,
        expected_contract_sha256=str(config["inputs"]["sealed_v6_prospective_contract"]["sha256"]),
        maximum_delay_seconds=int(config["boundary"]["maximum_decision_recording_delay_seconds"]),
        maximum_feature_age_minutes=int(config["boundary"]["maximum_feature_bar_age_minutes"]),
    )


def scenario_contract(
    historical: Mapping[str, Any], boundary: pd.Timestamp, cutoff_ms: int
) -> dict[str, Any]:
    contract = deepcopy(historical)
    contract["evaluation"]["entry_start_utc"] = boundary.isoformat().replace("+00:00", "Z")
    end = pd.Timestamp(cutoff_ms + 1, unit="ms", tz="UTC")
    if end.date() <= boundary.date():
        end = boundary + pd.Timedelta(days=1)
    contract["evaluation"]["entry_end_exclusive_utc"] = end.isoformat().replace("+00:00", "Z")
    contract["evaluation"]["poll_seconds"] = 5
    return contract


def accepted_ids(events: Sequence[Mapping[str, Any]]) -> set[str]:
    return {
        str(row["trade_id"])
        for row in events
        if str(row.get("event")) == "ORDER_FILLED"
    }


def completed_months(boundary: pd.Timestamp, cutoff_ms: int) -> list[str]:
    cutoff = pd.Timestamp(int(cutoff_ms), unit="ms", tz="UTC")
    first = boundary.tz_localize(None).to_period("M")
    if boundary != first.start_time.tz_localize("UTC"):
        first += 1
    last = cutoff.tz_localize(None).to_period("M")
    next_month_start = (last + 1).start_time.tz_localize("UTC")
    if cutoff < next_month_start - pd.Timedelta(milliseconds=1):
        last -= 1
    if last < first:
        return []
    return [str(item) for item in pd.period_range(first, last, freq="M")]


def monthly_pnl(
    events: Sequence[Mapping[str, Any]], months: Sequence[str]
) -> dict[str, float]:
    result: dict[str, float] = {str(month): 0.0 for month in months}
    for row in events:
        if str(row.get("event")) != "POSITION_CLOSED":
            continue
        month = str(row["timestamp_utc"])[:7]
        if month in result:
            result[month] += float(row["pnl_usd"])
    return dict(sorted(result.items()))


def downside(monthly: Mapping[str, float]) -> dict[str, Any]:
    negatives = [float(value) for value in monthly.values() if float(value) < 0.0]
    return {
        "months": len(monthly),
        "negative_months": len(negatives),
        "negative_month_pnl_usd": sum(negatives),
        "worst_month_pnl_usd": min(monthly.values()) if monthly else 0.0,
    }


def simulate_pair(
    *,
    replay: Any,
    evaluator: Any,
    v6_scenario: Any,
    portfolio: Mapping[str, Any],
    contract: Mapping[str, Any],
    candidates: Sequence[Any],
    quotes: Mapping[str, np.ndarray],
    ranks: Mapping[str, float],
    features: Mapping[str, Mapping[str, Any]],
    policy: Mapping[str, Any],
    anti_rule: Mapping[str, Any],
    warm_start: Mapping[str, Any],
    scenario_settings: Mapping[str, Any],
    completed_month_keys: Sequence[str],
) -> dict[str, Any]:
    spec = replay.ScenarioSpec(
        scenario_id="v19_clean_forward_capacity_twin",
        starting_equity_usd=float(scenario_settings["starting_equity_usd"]),
        activation_equity_usd=float(scenario_settings["activation_equity_usd"]),
        rebaseline_days=None,
        guardian_enabled=bool(scenario_settings["guardian_enabled"]),
        guardian_exit_attribution=str(scenario_settings["guardian_exit_attribution"]),
    )
    baseline = replay.Scenario(spec, portfolio, contract, list(candidates))
    baseline_metrics = baseline.simulate(quotes)
    dynamic = v6_scenario.combined_challenger_class(
        replay, evaluator, features, anti_rule
    )
    challenger_type = warm_started_challenger_class(dynamic, warm_start)
    challenger = challenger_type(
        spec,
        portfolio,
        contract,
        list(candidates),
        rank_map=ranks,
        policy=policy,
    )
    challenger_metrics = challenger.simulate(quotes)
    baseline_ids = accepted_ids(baseline.event_rows)
    challenger_ids = accepted_ids(challenger.event_rows)
    baseline_monthly = monthly_pnl(baseline.event_rows, completed_month_keys)
    challenger_monthly = monthly_pnl(challenger.event_rows, completed_month_keys)
    return {
        "baseline": baseline_metrics,
        "challenger": challenger_metrics,
        "baseline_accepted_ids": sorted(baseline_ids),
        "challenger_accepted_ids": sorted(challenger_ids),
        "common_accepted_ids": sorted(baseline_ids & challenger_ids),
        "v6_veto_ids": sorted(baseline_ids - challenger_ids),
        "v6_replacement_accept_ids": sorted(challenger_ids - baseline_ids),
        "routing_divergence_ids": sorted(baseline_ids ^ challenger_ids),
        "baseline_monthly_pnl_usd": baseline_monthly,
        "challenger_monthly_pnl_usd": challenger_monthly,
        "baseline_monthly_downside": downside(baseline_monthly),
        "challenger_monthly_downside": downside(challenger_monthly),
        "baseline_events": baseline.event_rows,
        "challenger_events": challenger.event_rows,
    }


def comparative_gates(result: Mapping[str, Any], acceptance: Mapping[str, Any]) -> dict[str, bool]:
    baseline = result["baseline"]
    challenger = result["challenger"]
    baseline_ids = set(result["baseline_accepted_ids"])
    common_ids = set(result["common_accepted_ids"])
    retention = len(common_ids) / len(baseline_ids) if baseline_ids else 0.0
    baseline_monthly = result["baseline_monthly_pnl_usd"]
    challenger_monthly = result["challenger_monthly_pnl_usd"]
    common_months = sorted(set(baseline_monthly) | set(challenger_monthly))

    def profit_factor_value(metrics: Mapping[str, Any]) -> float:
        value = metrics.get("profit_factor")
        if value is not None:
            return float(value)
        return math.inf if float(metrics.get("gross_profit_usd", 0.0)) > 0.0 else 0.0

    return {
        "net_pnl_strictly_higher": float(challenger["net_pnl_usd"]) > float(baseline["net_pnl_usd"]),
        "profit_factor_not_lower": profit_factor_value(challenger) >= profit_factor_value(baseline),
        "closed_drawdown_not_higher": float(challenger["maximum_lifetime_closed_drawdown_usd"])
        <= float(baseline["maximum_lifetime_closed_drawdown_usd"]),
        "equity_drawdown_not_higher": float(challenger["maximum_lifetime_equity_drawdown_usd"])
        <= float(baseline["maximum_lifetime_equity_drawdown_usd"]),
        "trade_retention": retention >= float(acceptance["minimum_trade_retention"]),
        "losing_month_burden_not_worse": float(
            result["challenger_monthly_downside"]["negative_month_pnl_usd"]
        )
        >= float(result["baseline_monthly_downside"]["negative_month_pnl_usd"]),
        "worst_month_not_worse": float(
            result["challenger_monthly_downside"]["worst_month_pnl_usd"]
        )
        >= float(result["baseline_monthly_downside"]["worst_month_pnl_usd"]),
        "every_completed_month_not_lower": all(
            float(challenger_monthly.get(month, 0.0)) >= float(baseline_monthly.get(month, 0.0))
            for month in common_months
        ),
        "baseline_has_no_open_positions": int(baseline["open_positions_at_end"]) == 0,
        "challenger_has_no_open_positions": int(challenger["open_positions_at_end"]) == 0,
    }


def run(now: datetime | None = None) -> dict[str, Any]:
    now = (now or datetime.now(UTC)).astimezone(UTC)
    config = read_json(CONFIG)
    validate_config(config)
    boundary = utc_timestamp(config["boundary"]["evidence_start_inclusive_utc"])
    runtime = Path(config["outputs"]["runtime_directory"])
    runtime.mkdir(parents=True, exist_ok=True)
    lock = validate_contract_lock(runtime)
    state_path = runtime / config["outputs"]["state"]
    state = load_state(state_path, boundary, str(lock["contract_sha256"]))

    portfolio = read_json(resolve(config["inputs"]["v60_config"]["path"]))
    overlay = read_json(resolve(config["inputs"]["protection_overlay"]["path"]))
    portfolio["portfolio_protection"] = overlay["portfolio_protection"]
    executor = load_module(
        "v19_deployed_executor", resolve(config["inputs"]["deployed_executor"]["path"])
    )
    facts, prefixes = load_candidate_facts(
        portfolio,
        executor,
        boundary=boundary,
        point_size=float(config["ticks"]["point_size"]),
        previous_prefixes=state.get("candidate_prefixes", {}),
    )
    state["candidate_prefixes"] = prefixes
    fact_map = {str(item.candidate.candidate_id): item for item in facts}
    resolutions = state.setdefault("candidate_resolutions", {})
    missing_facts = sorted(set(resolutions) - set(fact_map))
    if missing_facts:
        raise ValueError(f"Previously observed candidate facts disappeared: {missing_facts}")
    for candidate_id, fact in fact_map.items():
        if candidate_id not in resolutions:
            resolutions[candidate_id] = initial_resolution(fact)
        elif str(resolutions[candidate_id]["fact_sha256"]) != fact.fact_sha256:
            raise ValueError(f"Candidate fact mutated: {candidate_id}")

    tick_paths = [
        path
        for path in completed_tick_paths(
            Path(config["ticks"]["directory"]),
            str(config["ticks"]["filename_glob"]),
            now=now,
        )
        if tick_file_date(path) >= boundary.date()
    ]
    tick_records = state.setdefault("tick_files", {})
    missing_tick_files = sorted(set(tick_records) - {str(path.resolve()) for path in tick_paths})
    if missing_tick_files:
        raise ValueError(f"Previously consumed tick files disappeared: {missing_tick_files}")
    for path in tick_paths:
        key = str(path.resolve())
        prior = tick_records.get(key)
        if prior is not None:
            stat = path.stat()
            if int(stat.st_size) != int(prior["bytes"]) or int(
                stat.st_mtime_ns
            ) != int(prior["mtime_ns"]):
                raise ValueError(f"Completed tick file metadata changed: {path}")
            cache_path = Path(str(prior["quote_cache"]["path"]))
            if cache_path.is_file() and sha256_file(cache_path) != str(
                prior["quote_cache"]["sha256"]
            ):
                raise ValueError(f"V19 quote cache changed: {cache_path}")
        needs_quote_cache = prior is None or not Path(str(prior["quote_cache"]["path"])).is_file()
        needs_candidate_progress = False
        if prior is None:
            needs_candidate_progress = True
        else:
            last_ms_value = prior.get("last_tick_msc")
            if last_ms_value is not None:
                last_ms = int(last_ms_value)
                for candidate_id, fact in fact_map.items():
                    resolution = resolutions[candidate_id]
                    last_seen = resolution.get("last_tick_time_msc")
                    if (
                        resolution["status"] not in FINAL_RESOLUTION_STATUSES
                        and int(round(fact.candidate.scheduled_at.timestamp() * 1000.0)) <= last_ms
                        and (last_seen is None or int(last_seen) < last_ms)
                    ):
                        needs_candidate_progress = True
                        break
        if not needs_quote_cache and not needs_candidate_progress:
            continue
        ticks = load_tick_day(path, str(config["ticks"]["schema_version"]))
        if prior is not None and ticks.sha256 != str(prior["sha256"]):
            raise ValueError(f"Completed tick file changed: {path}")
        cache = (
            save_quote_cache(runtime, ticks, int(config["ticks"]["poll_seconds"]))
            if needs_quote_cache
            else prior["quote_cache"]
        )
        if len(ticks.times):
            for candidate_id, fact in fact_map.items():
                resolution = resolutions[candidate_id]
                if resolution["status"] in FINAL_RESOLUTION_STATUSES:
                    continue
                if int(round(fact.candidate.scheduled_at.timestamp() * 1000.0)) > int(ticks.times[-1]):
                    continue
                resolutions[candidate_id] = advance_resolution(
                    resolution,
                    fact,
                    ticks,
                    economics=config["economics"],
                    maximum_horizon_gap_minutes=int(config["ticks"]["maximum_horizon_gap_minutes"]),
                )
        tick_records[key] = {
            "day": ticks.day.isoformat(),
            "bytes": int(path.stat().st_size),
            "mtime_ns": int(path.stat().st_mtime_ns),
            "sha256": ticks.sha256,
            "duplicate_rows_collapsed": int(ticks.duplicate_rows_collapsed),
            "first_tick_msc": int(ticks.times[0]) if len(ticks.times) else None,
            "last_tick_msc": int(ticks.times[-1]) if len(ticks.times) else None,
            "quote_cache": cache,
        }

    evidence_reader = load_module(
        "v19_v6_evidence_reader",
        resolve(config["inputs"]["sealed_v6_evidence_reader"]["path"]),
    )
    ranks, features, score_timing, score_audit = load_scores(config, evidence_reader)
    inventory_resolved = [
        row for row in resolutions.values() if row["status"] in FINAL_RESOLUTION_STATUSES
    ]
    inventory_unresolved = [
        row for row in resolutions.values() if row["status"] not in FINAL_RESOLUTION_STATUSES
    ]
    latest_cycle = max(
        (
            int(item["quote_cache"]["last_cycle_msc"])
            for item in tick_records.values()
            if item["quote_cache"]["last_cycle_msc"] is not None
        ),
        default=None,
    )
    earliest_unresolved = min(
        (timestamp_ms(row["scheduled_entry_time_utc"]) for row in inventory_unresolved),
        default=None,
    )
    cutoff_ms = latest_cycle
    if cutoff_ms is not None and earliest_unresolved is not None:
        cutoff_ms = min(cutoff_ms, earliest_unresolved - 1)
    analysis_ids = {
        candidate_id
        for candidate_id, row in resolutions.items()
        if cutoff_ms is not None
        and timestamp_ms(row["scheduled_entry_time_utc"]) <= int(cutoff_ms)
    }
    analysis_resolved = [
        resolutions[candidate_id]
        for candidate_id in sorted(analysis_ids)
        if resolutions[candidate_id]["status"] in FINAL_RESOLUTION_STATUSES
        and timestamp_ms(resolutions[candidate_id]["evidence_end_time_utc"]) <= int(cutoff_ms)
    ]
    analysis_executed = [row for row in analysis_resolved if row["status"] == "EXECUTED"]
    if len(analysis_resolved) != len(analysis_ids):
        raise ValueError("V19 analysis cutoff includes an unresolved candidate")
    elapsed_days = (
        0.0
        if cutoff_ms is None
        else max(
            0.0,
            (pd.Timestamp(int(cutoff_ms), unit="ms", tz="UTC") - boundary).total_seconds()
            / 86_400.0,
        )
    )

    result: dict[str, Any] = {
        "schema_version": "v60_dynamic_capacity_twin_prospective_v19_status",
        "generated_at_utc": now.isoformat().replace("+00:00", "Z"),
        "evidence_start_inclusive_utc": boundary.isoformat().replace("+00:00", "Z"),
        "elapsed_days": elapsed_days,
        "contract_sha256": str(lock["contract_sha256"]),
        "broker_action_authorized": False,
        "deployment_authorized": False,
        "runtime_changes_authorized": False,
        "counts": {
            "candidate_facts": len(facts),
            "inventory_resolved_candidates": len(inventory_resolved),
            "inventory_unresolved_candidates": len(inventory_unresolved),
            "analysis_candidate_facts": len(analysis_ids),
            "resolved_candidates": len(analysis_resolved),
            "executed_candidate_endpoints": len(analysis_executed),
            "rejected_candidate_endpoints": len(analysis_resolved)
            - len(analysis_executed),
            "completed_tick_days": len(tick_records),
            "timely_score_rows": int(score_audit["timely_score_rows"]),
        },
        "score_audit": score_audit,
        "analysis_cutoff_msc": cutoff_ms,
        "decision": "CONTINUE_PROSPECTIVE_CAPACITY_COLLECTION",
        "limitations": [
            "V19 is a read-only raw-tick portfolio twin and never calls MT5 order_send.",
            "Only completed UTC tick days enter economic metrics.",
            "A passing V19 result requires review and does not authorize deployment.",
        ],
    }
    events: list[dict[str, Any]] = []

    if now < boundary.to_pydatetime():
        result["decision"] = "AWAITING_PROSPECTIVE_BOUNDARY"
    elif cutoff_ms is not None and analysis_executed:
        replay = load_module(
            "v19_tick_replay", resolve(config["inputs"]["tick_replay"]["path"])
        )
        evaluator = load_module(
            "v19_shared_evaluator", resolve(config["inputs"]["shared_evaluator"]["path"])
        )
        v6_scenario = load_module(
            "v19_v6_scenario", resolve(config["inputs"]["v6_scenario"]["path"])
        )
        warm_start = read_json(resolve(config["inputs"]["warm_start"]["path"]))
        sealed_v6 = read_json(
            resolve(config["inputs"]["sealed_v6_prospective_contract"]["path"])
        )
        historical_contract = read_json(
            resolve(config["inputs"]["tick_replay_contract"]["path"])
        )
        contract = scenario_contract(historical_contract, boundary, int(cutoff_ms))
        quotes = load_quotes(runtime, list(tick_records.values()))
        mask = (quotes["cycle_ms"] >= int(boundary.value // 1_000_000)) & (
            quotes["cycle_ms"] <= int(cutoff_ms)
        )
        quotes = {key: value[mask] for key, value in quotes.items()}
        if not len(quotes["cycle_ms"]):
            raise ValueError("V19 has endpoint outcomes but no five-second quotes")
        if any(len(value) != len(quotes["cycle_ms"]) for value in quotes.values()):
            raise ValueError("V19 quote arrays have inconsistent lengths")
        if np.any(np.diff(quotes["cycle_ms"]) <= 0):
            raise ValueError("V19 five-second quote cycles are not strictly increasing")
        selected_states = list(analysis_executed)
        selected_states.sort(key=lambda row: (int(row["entry_time_msc"]), str(row["candidate_id"])))
        sources = {str(row["source_id"]): row for row in portfolio["sources"]}
        completed_month_keys = completed_months(boundary, int(cutoff_ms))

        def candidate_set(
            additional_cost: float = 0.0, additional_cost_r: float = 0.0
        ) -> list[Any]:
            return [
                resolution_to_replay_candidate(
                    replay,
                    row,
                    sources[str(row["source_id"])],
                    additional_cost_usd=additional_cost,
                    additional_cost_r=additional_cost_r,
                )
                for row in selected_states
            ]

        nominal = simulate_pair(
            replay=replay,
            evaluator=evaluator,
            v6_scenario=v6_scenario,
            portfolio=portfolio,
            contract=contract,
            candidates=candidate_set(0.0),
            quotes=quotes,
            ranks=ranks,
            features=features,
            policy=sealed_v6["lock"]["policy"],
            anti_rule=sealed_v6["lock"]["anti_chase"],
            warm_start=warm_start,
            scenario_settings=config["scenario"],
            completed_month_keys=completed_month_keys,
        )
        result["portfolio"] = {key: value for key, value in nominal.items() if not key.endswith("_events")}
        result["counts"].update(
            routing_divergences=len(nominal["routing_divergence_ids"]),
            v6_vetoes=len(nominal["v6_veto_ids"]),
            v6_replacement_accepts=len(nominal["v6_replacement_accept_ids"]),
        )
        acceptance = config["acceptance"]
        population_ids = sorted(analysis_ids)
        rank_covered = 0
        feature_covered = 0
        timing_covered = 0
        for candidate_id in population_ids:
            fact = fact_map[candidate_id]
            if candidate_id not in ranks or candidate_id not in score_timing:
                continue
            rank_covered += 1
            timing = score_timing[candidate_id]
            if (
                utc_timestamp(timing["entry_time_utc"])
                == pd.Timestamp(fact.candidate.scheduled_at)
                and str(features[candidate_id]["execution_source_id"])
                == str(fact.candidate.source_id)
                and str(features[candidate_id]["direction"]).upper()
                == str(fact.candidate.direction).upper()
            ):
                timing_covered += 1
            if bool(timing["causal_policy_features_complete"]):
                feature_covered += 1

        def quote_covered(row: Mapping[str, Any]) -> bool:
            entry_ms = int(row["entry_time_msc"])
            exit_ms = int(row["exit_time_msc"])
            entry_index = int(np.searchsorted(quotes["cycle_ms"], entry_ms, side="left"))
            if entry_index >= len(quotes["cycle_ms"]):
                return False
            maximum_gap = int(
                sources[str(row["source_id"])]["maximum_entry_gap_minutes"]
            ) * 60_000
            return bool(
                int(quotes["cycle_ms"][entry_index]) <= entry_ms + maximum_gap
                and int(quotes["cycle_ms"][-1]) >= exit_ms
            )

        quote_covered_count = sum(quote_covered(row) for row in selected_states)
        population_count = len(population_ids)
        executed_count = len(selected_states)
        coverage = {
            "candidate_fact_fraction": (
                len(analysis_ids) / population_count if population_count else 0.0
            ),
            "resolved_outcome_fraction": (
                len(analysis_resolved) / population_count if population_count else 0.0
            ),
            "timely_rank_fraction": (
                rank_covered / population_count if population_count else 0.0
            ),
            "causal_feature_fraction": (
                feature_covered / population_count if population_count else 0.0
            ),
            "causal_identity_and_timing_fraction": (
                timing_covered / population_count if population_count else 0.0
            ),
            "five_second_quote_fraction": (
                quote_covered_count / executed_count if executed_count else 0.0
            ),
        }
        sample_gates = {
            "minimum_elapsed_days": elapsed_days >= float(acceptance["minimum_elapsed_days"]),
            "minimum_resolved_candidates": len(analysis_resolved)
            >= int(acceptance["minimum_resolved_candidates"]),
            "minimum_routing_divergences": len(nominal["routing_divergence_ids"])
            >= int(acceptance["minimum_routing_divergences"]),
            "minimum_v6_vetoes": len(nominal["v6_veto_ids"])
            >= int(acceptance["minimum_v6_vetoes"]),
            "minimum_v6_replacement_accepts": len(nominal["v6_replacement_accept_ids"])
            >= int(acceptance["minimum_v6_replacement_accepts"]),
            "complete_candidate_fact_coverage": coverage["candidate_fact_fraction"]
            >= float(acceptance["minimum_coverage"]),
            "complete_outcome_coverage": coverage["resolved_outcome_fraction"]
            >= float(acceptance["minimum_coverage"]),
            "complete_causal_score_coverage": coverage["timely_rank_fraction"]
            >= float(acceptance["minimum_coverage"]),
            "complete_causal_feature_coverage": coverage["causal_feature_fraction"]
            >= float(acceptance["minimum_coverage"]),
            "complete_causal_timing_coverage": coverage[
                "causal_identity_and_timing_fraction"
            ]
            >= float(acceptance["minimum_coverage"]),
            "complete_five_second_quote_coverage": coverage[
                "five_second_quote_fraction"
            ]
            >= float(acceptance["minimum_coverage"]),
        }
        comparative = comparative_gates(nominal, acceptance)
        cost_stress: dict[str, Any] = {}
        for cost in config["economics"]["additional_cost_stress_usd_per_trade"]:
            stressed = simulate_pair(
                replay=replay,
                evaluator=evaluator,
                v6_scenario=v6_scenario,
                portfolio=portfolio,
                contract=contract,
                candidates=candidate_set(float(cost)),
                quotes=quotes,
                ranks=ranks,
                features=features,
                policy=sealed_v6["lock"]["policy"],
                anti_rule=sealed_v6["lock"]["anti_chase"],
                warm_start=warm_start,
                scenario_settings=config["scenario"],
                completed_month_keys=completed_month_keys,
            )
            stress_gates = comparative_gates(stressed, acceptance)
            cost_stress[str(cost)] = {
                "additional_cost_usd_per_trade": float(cost),
                "gates": stress_gates,
                "all_gates_pass": all(stress_gates.values()),
                "baseline": stressed["baseline"],
                "challenger": stressed["challenger"],
            }
        all_cost = bool(cost_stress) and all(row["all_gates_pass"] for row in cost_stress.values())
        slippage_stress = simulate_pair(
            replay=replay,
            evaluator=evaluator,
            v6_scenario=v6_scenario,
            portfolio=portfolio,
            contract=contract,
            candidates=candidate_set(
                additional_cost_r=float(config["economics"]["stress_slippage_r"])
            ),
            quotes=quotes,
            ranks=ranks,
            features=features,
            policy=sealed_v6["lock"]["policy"],
            anti_rule=sealed_v6["lock"]["anti_chase"],
            warm_start=warm_start,
            scenario_settings=config["scenario"],
            completed_month_keys=completed_month_keys,
        )
        slippage_gates = comparative_gates(slippage_stress, acceptance)
        result["coverage"] = {
            "selected_candidate_endpoints": len(selected_states),
            "completed_calendar_months": completed_month_keys,
            **coverage,
        }
        result["gates"] = {
            **sample_gates,
            **comparative,
            "all_cost_stress_gates": all_cost,
            "stress_slippage_r_all_comparative_gates": all(
                slippage_gates.values()
            ),
        }
        result["cost_stress"] = cost_stress
        result["stress_slippage_r"] = {
            "additional_cost_r_per_trade": float(
                config["economics"]["stress_slippage_r"]
            ),
            "gates": slippage_gates,
            "all_gates_pass": all(slippage_gates.values()),
            "baseline": slippage_stress["baseline"],
            "challenger": slippage_stress["challenger"],
        }
        if all(result["gates"].values()):
            result["decision"] = "V6_CAPACITY_TWIN_PASSES_REVIEW_REQUIRED"
        elif all(sample_gates.values()):
            result["decision"] = "KEEP_DEPLOYED_V60_CAPACITY_TWIN_REJECTS_V6"
        events = [
            {"portfolio": "V60", **row} for row in nominal["baseline_events"]
        ] + [{"portfolio": "V6", **row} for row in nominal["challenger_events"]]

    prior_state_hash = state.get("state_sha256")
    state["previous_state_sha256"] = prior_state_hash
    state["run_sequence"] = int(state.get("run_sequence", 0)) + 1
    state["updated_at_utc"] = now.isoformat().replace("+00:00", "Z")
    state.pop("state_sha256", None)
    state["state_sha256"] = state_sha256(state)
    atomic_write(
        state_path, json.dumps(json_clean(state), indent=2, sort_keys=True) + "\n"
    )
    resolved_path = runtime / config["outputs"]["resolved_candidates"]
    atomic_write(
        resolved_path,
        "".join(
            json.dumps(json_clean(row), sort_keys=True) + "\n"
            for row in sorted(resolutions.values(), key=lambda item: str(item["candidate_id"]))
        ),
    )
    events_path = runtime / config["outputs"]["portfolio_events"]
    atomic_write(
        events_path,
        "".join(json.dumps(json_clean(row), sort_keys=True) + "\n" for row in events),
    )
    result["evidence_files"] = {
        "state_sha256": sha256_file(state_path),
        "resolved_candidates_sha256": sha256_file(resolved_path),
        "portfolio_events_sha256": sha256_file(events_path),
    }
    result = json_clean(result)
    result["status_sha256"] = canonical_sha256(result)
    atomic_write(
        runtime / config["outputs"]["status"],
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
    )
    return result


def persist_failure(exc: Exception) -> dict[str, Any]:
    failure = {
        "schema_version": "v60_dynamic_capacity_twin_prospective_v19_status",
        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "decision": "FAILED_CLOSED",
        "error": f"{type(exc).__name__}: {exc}",
        "broker_action_authorized": False,
        "deployment_authorized": False,
        "runtime_changes_authorized": False,
    }
    failure["status_sha256"] = canonical_sha256(failure)
    try:
        config = read_json(CONFIG)
        status_path = (
            Path(config["outputs"]["runtime_directory"])
            / config["outputs"]["status"]
        )
        atomic_write(
            status_path,
            json.dumps(failure, indent=2, sort_keys=True, allow_nan=False) + "\n",
        )
    except Exception as status_exc:
        failure["status_persistence_error"] = (
            f"{type(status_exc).__name__}: {status_exc}"
        )
    return failure


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only V19 prospective capacity twin")
    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=0,
        help="Repeat after this many seconds; zero runs exactly once.",
    )
    args = parser.parse_args(argv)
    if args.poll_seconds < 0:
        parser.error("--poll-seconds cannot be negative")
    while True:
        try:
            result = run()
        except Exception as exc:
            failure = persist_failure(exc)
            print(json.dumps(failure, sort_keys=True), flush=True)
            return 1
        print(json.dumps(result, sort_keys=True), flush=True)
        if args.poll_seconds == 0:
            return 0
        time.sleep(args.poll_seconds)

if __name__ == "__main__":
    raise SystemExit(main())

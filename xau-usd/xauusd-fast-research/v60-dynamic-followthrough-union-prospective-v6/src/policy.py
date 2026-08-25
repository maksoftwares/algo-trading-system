from __future__ import annotations

from collections import defaultdict, deque
from datetime import UTC, datetime
import math
from typing import Any, Mapping, Sequence

import pandas as pd


FEATURE_NAMES = (
    "atr_ratio",
    "rv_1h",
    "rv_24h",
    "slope_atr",
    "ret_1h",
    "ret_4h",
    "ret_24h",
    "dist_hi_24h",
    "dist_lo_24h",
)


def utc_time(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp is not timezone-aware: {value}")
    return parsed.astimezone(UTC)


def profit_factor(values: Sequence[float]) -> float:
    gross_profit = sum(value for value in values if value > 0.0)
    gross_loss = -sum(value for value in values if value < 0.0)
    if gross_loss == 0.0:
        return math.inf if gross_profit > 0.0 else 0.0
    return gross_profit / gross_loss


def attach_causal_features(
    runtime: Mapping[str, Any],
    candidates: Sequence[Mapping[str, Any]],
    decisions: dict[str, dict[str, Any]],
    *,
    maximum_bar_age_minutes: int,
) -> dict[str, Any]:
    feature_bars = runtime["feature_bars"]
    maximum_age = pd.Timedelta(minutes=int(maximum_bar_age_minutes))
    complete = 0
    reasons: dict[str, int] = {}
    for candidate in candidates:
        candidate_id = str(candidate["candidate_id"])
        decision = decisions.get(candidate_id)
        if decision is None or decision.get("reason") != "SCORE_COMPLETE":
            reason = "RANK_NOT_COMPLETE"
        else:
            timestamp = pd.Timestamp(candidate["scheduled_entry_time_utc"])
            if timestamp.tzinfo is None:
                raise ValueError("Candidate timestamp is not timezone-aware")
            timestamp = timestamp.tz_convert("UTC")
            completed = feature_bars.loc[feature_bars["decision_time_utc"].le(timestamp)]
            if completed.empty:
                reason = "FEATURE_BAR_MISSING"
            else:
                feature = completed.iloc[-1]
                feature_time = pd.Timestamp(feature["decision_time_utc"]).tz_convert("UTC")
                if timestamp - feature_time > maximum_age:
                    reason = "FEATURE_BAR_STALE"
                elif not all(math.isfinite(float(feature[name])) for name in FEATURE_NAMES):
                    reason = "FEATURE_NONFINITE"
                else:
                    reason = "FEATURE_COMPLETE"
                    decision["candidate_direction"] = str(candidate["direction"]).upper()
                    decision["feature_bar_time_utc"] = feature_time.isoformat().replace("+00:00", "Z")
                    for name in FEATURE_NAMES:
                        decision[name] = float(feature[name])
                    complete += 1
        reasons[reason] = reasons.get(reason, 0) + 1
    return {
        "schema_version": "v60_dynamic_v6_causal_feature_audit_v1",
        "candidate_rows": len(candidates),
        "complete_feature_rows": complete,
        "reason_counts": dict(sorted(reasons.items())),
    }


def anti_veto(
    row: Mapping[str, Any],
    decision: Mapping[str, Any],
    prior_count: int,
    rule: Mapping[str, Any],
) -> bool:
    values = [
        decision.get("rank"),
        decision.get("atr_ratio"),
        decision.get("dist_hi_24h"),
        decision.get("ret_4h"),
        decision.get("ret_24h"),
    ]
    if prior_count < int(rule["minimum_prior_source_closed_trades"]):
        return False
    if any(value is None or not math.isfinite(float(value)) for value in values):
        return False
    rank, atr_ratio, distance, ret_4h, ret_24h = map(float, values)
    if ret_24h <= float(rule["minimum_ret_24h_exclusive"]):
        return False
    return bool(
        str(row["source_id"]) == str(rule["source_id"])
        and str(decision.get("candidate_direction", "")).upper()
        == str(rule["direction"]).upper()
        and rank < float(rule["maximum_causal_rank_exclusive"])
        and atr_ratio >= float(rule["minimum_atr_ratio_inclusive"])
        and distance < float(rule["maximum_distance_to_24h_high_atr_exclusive"])
        and ret_4h / ret_24h
        < float(rule["maximum_ret_4h_to_ret_24h_exclusive"])
    )


def apply_dynamic_union(
    rows: Sequence[dict[str, Any]],
    decisions: Mapping[str, Mapping[str, Any]],
    *,
    warm_start: Mapping[str, Any],
    broker_outcomes: Mapping[str, Mapping[str, Any]],
    boundary: datetime,
    v2_policy: Mapping[str, Any],
    anti_rule: Mapping[str, Any],
) -> dict[str, Any]:
    lookback = int(v2_policy["lookback_closed_trades"])
    histories: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=lookback))
    counts: dict[str, int] = defaultdict(int)
    warm_rows: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for item in warm_start["rows"]:
        warm_rows[str(item["source_id"])].append(item)
    for source_id, count in warm_start["retained_history_counts_by_source"].items():
        counts[str(source_id)] = int(count)
        ordered = sorted(
            warm_rows.get(str(source_id), []),
            key=lambda item: (utc_time(item["closed_at_utc"]), str(item["candidate_id"])),
        )
        histories[str(source_id)].extend(float(item["pnl_usd"]) for item in ordered[-lookback:])

    pending: list[tuple[datetime, str, str, float]] = []
    for candidate_id, outcome in broker_outcomes.items():
        opened = outcome.get("opened_at_utc")
        if opened is None or utc_time(opened) >= boundary:
            continue
        closed = utc_time(outcome["closed_at_utc"])
        source_id = str(outcome["source_id"])
        pnl = float(outcome["pnl_usd"])
        if closed < boundary:
            histories[source_id].append(pnl)
            counts[source_id] += 1
        else:
            pending.append((closed, str(candidate_id), source_id, pnl))
    pending.sort(key=lambda item: (item[0], item[1]))

    policy_rows = sorted(rows, key=lambda row: (utc_time(row["entry_time_utc"]), str(row["candidate_id"])))
    pending_index = 0
    reasons: dict[str, int] = {}
    proposal_counts: dict[str, int] = {}
    for row in policy_rows:
        entry = utc_time(row["entry_time_utc"])
        while pending_index < len(pending) and pending[pending_index][0] <= entry:
            _, _, source_id, pnl = pending[pending_index]
            histories[source_id].append(pnl)
            counts[source_id] += 1
            pending_index += 1
        candidate_id = str(row["candidate_id"])
        source_id = str(row["source_id"])
        decision = decisions.get(candidate_id, {})
        rank = decision.get("rank") if decision.get("reason") == "SCORE_COMPLETE" else None
        prior_values = list(histories[source_id])
        mature = counts[source_id] >= int(v2_policy["minimum_prior_source_closed_trades"])
        prior_pf = profit_factor(prior_values[-lookback:]) if mature and len(prior_values) >= lookback else None
        v2_veto = bool(
            row["baseline_executed"]
            and prior_pf is not None
            and math.isfinite(prior_pf)
            and prior_pf < float(v2_policy["maximum_prior_profit_factor_exclusive"])
            and rank is not None
            and math.isfinite(float(rank))
            and float(rank) < float(v2_policy["maximum_causal_rank_exclusive"])
        )
        anti = bool(row["baseline_executed"] and anti_veto(row, decision, counts[source_id], anti_rule))
        would_veto = v2_veto or anti
        proposal_rule = (
            "V2_SOURCE_HEALTH+V57_WEAK_FOLLOWTHROUGH_ANTICHASE"
            if v2_veto and anti
            else "V2_SOURCE_HEALTH"
            if v2_veto
            else "V57_WEAK_FOLLOWTHROUGH_ANTICHASE"
            if anti
            else None
        )
        row["causal_score"] = decision.get("score")
        row["causal_rank"] = rank
        row["candidate_direction"] = decision.get("candidate_direction")
        row["feature_bar_time_utc"] = decision.get("feature_bar_time_utc")
        for name in FEATURE_NAMES:
            row[name] = decision.get(name)
        row["causal_policy_features_complete"] = all(
            decision.get(name) is not None and math.isfinite(float(decision[name]))
            for name in ("rank", "atr_ratio", "dist_hi_24h", "ret_4h", "ret_24h")
        ) and decision.get("candidate_direction") is not None
        row["prior_source_executed_count"] = counts[source_id]
        row["prior_health_window_count"] = len(prior_values[-lookback:])
        row["prior_executed_profit_factor"] = prior_pf if prior_pf is not None and math.isfinite(prior_pf) else None
        row["v2_veto_proposal"] = v2_veto
        row["anti_chase_veto_proposal"] = anti
        row["proposal_rule"] = proposal_rule
        row["would_veto"] = would_veto
        outcome = broker_outcomes.get(candidate_id)
        if not bool(row["baseline_executed"]):
            reason = "BASELINE_NOT_EXECUTED"
        elif rank is None:
            reason = "AWAITING_CAUSAL_RANK"
        elif not mature or prior_pf is None:
            reason = "INCOMPLETE_DYNAMIC_SOURCE_HEALTH"
        elif would_veto and not bool(row["broker_outcome_resolved"]):
            reason = "VETO_AWAITING_BROKER_OUTCOME"
        elif would_veto:
            reason = "VETO_RESOLVED"
        else:
            reason = "RETAIN"
        row["evidence_status"] = reason
        reasons[reason] = reasons.get(reason, 0) + 1
        if proposal_rule is not None:
            proposal_counts[proposal_rule] = proposal_counts.get(proposal_rule, 0) + 1
        if (
            bool(row["baseline_executed"])
            and not would_veto
            and outcome is not None
        ):
            pending.append(
                (
                    utc_time(outcome["closed_at_utc"]),
                    candidate_id,
                    source_id,
                    float(outcome["pnl_usd"]),
                )
            )
            pending[pending_index:] = sorted(
                pending[pending_index:], key=lambda item: (item[0], item[1])
            )
    return {
        "schema_version": "v60_dynamic_union_policy_audit_v1",
        "rows": len(policy_rows),
        "proposal_rule_counts": dict(sorted(proposal_counts.items())),
        "reason_counts": dict(sorted(reasons.items())),
        "state_recomputed_from_hypothetical_retained_path": True,
    }


def refresh_status(
    status: dict[str, Any],
    rows: Sequence[Mapping[str, Any]],
    acceptance: Mapping[str, Any],
) -> None:
    executed_scored = [
        row for row in rows if row["baseline_executed"] and row.get("causal_rank") is not None
    ]
    vetoes = [row for row in rows if row["would_veto"]]
    resolved = [row for row in vetoes if row["broker_outcome_resolved"]]
    resolved_v2 = [row for row in resolved if row.get("v2_veto_proposal")]
    resolved_anti_chase = [
        row for row in resolved if row.get("anti_chase_veto_proposal")
    ]
    values = [float(row["broker_pnl_usd"]) for row in resolved]
    v2_values = [float(row["broker_pnl_usd"]) for row in resolved_v2]
    anti_chase_values = [
        float(row["broker_pnl_usd"]) for row in resolved_anti_chase
    ]
    veto_pf = profit_factor(values) if values else None
    v2_pf = profit_factor(v2_values) if v2_values else None
    anti_chase_pf = profit_factor(anti_chase_values) if anti_chase_values else None
    avoided = -sum(values)
    v2_avoided = -sum(v2_values)
    anti_chase_avoided = -sum(anti_chase_values)
    status["counts"]["executed_scored_candidates"] = len(executed_scored)
    status["counts"]["veto_opportunities"] = len(vetoes)
    status["counts"]["resolved_vetoes"] = len(resolved)
    status["counts"]["resolved_v2_vetoes"] = len(resolved_v2)
    status["counts"]["resolved_anti_chase_vetoes"] = len(resolved_anti_chase)
    status["veto_broker_net_pnl_usd"] = sum(values)
    status["avoided_broker_pnl_usd"] = avoided
    status["veto_broker_profit_factor"] = (
        veto_pf if veto_pf is not None and math.isfinite(veto_pf) else None
    )
    status["component_evidence"] = {
        "v2_source_health": {
            "resolved_vetoes": len(resolved_v2),
            "veto_broker_net_pnl_usd": sum(v2_values),
            "avoided_broker_pnl_usd": v2_avoided,
            "veto_broker_profit_factor": (
                v2_pf if v2_pf is not None and math.isfinite(v2_pf) else None
            ),
        },
        "v57_weak_followthrough_anti_chase": {
            "resolved_vetoes": len(resolved_anti_chase),
            "veto_broker_net_pnl_usd": sum(anti_chase_values),
            "avoided_broker_pnl_usd": anti_chase_avoided,
            "veto_broker_profit_factor": (
                anti_chase_pf
                if anti_chase_pf is not None and math.isfinite(anti_chase_pf)
                else None
            ),
        },
    }
    status["gates"]["minimum_scored_executed_candidates"] = len(executed_scored) >= int(
        acceptance["minimum_scored_executed_candidates"]
    )
    status["gates"]["minimum_resolved_vetoes"] = len(resolved) >= int(
        acceptance["minimum_resolved_vetoes"]
    )
    status["gates"]["minimum_resolved_v2_vetoes"] = len(resolved_v2) >= int(
        acceptance["minimum_resolved_v2_vetoes"]
    )
    status["gates"]["minimum_resolved_anti_chase_vetoes"] = len(
        resolved_anti_chase
    ) >= int(acceptance["minimum_resolved_anti_chase_vetoes"])
    status["gates"]["v2_veto_broker_profit_factor"] = (
        v2_pf is not None
        and v2_pf < float(acceptance["maximum_v2_veto_broker_profit_factor_exclusive"])
    )
    status["gates"]["positive_v2_avoided_broker_pnl"] = v2_avoided > float(
        acceptance["minimum_v2_avoided_broker_pnl_usd_exclusive"]
    )
    status["gates"]["anti_chase_veto_broker_profit_factor"] = (
        anti_chase_pf is not None
        and anti_chase_pf
        < float(acceptance["maximum_anti_chase_veto_broker_profit_factor_exclusive"])
    )
    status["gates"]["positive_anti_chase_avoided_broker_pnl"] = (
        anti_chase_avoided
        > float(acceptance["minimum_anti_chase_avoided_broker_pnl_usd_exclusive"])
    )
    status["gates"]["veto_broker_profit_factor"] = veto_pf is not None and veto_pf < float(
        acceptance["maximum_veto_broker_profit_factor_exclusive"]
    )
    status["gates"]["positive_avoided_broker_pnl"] = avoided > float(
        acceptance["minimum_avoided_broker_pnl_usd_exclusive"]
    )

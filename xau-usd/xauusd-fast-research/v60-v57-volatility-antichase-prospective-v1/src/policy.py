from __future__ import annotations

from typing import Any, Mapping, Sequence

import math
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


def utc_timestamp(value: Any) -> pd.Timestamp:
    parsed = pd.Timestamp(value)
    if parsed.tzinfo is None:
        raise ValueError(f"Policy timestamp is not timezone-aware: {value}")
    return parsed.tz_convert("UTC")


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
            timestamp = utc_timestamp(candidate["scheduled_entry_time_utc"])
            completed = feature_bars.loc[
                feature_bars["decision_time_utc"].le(timestamp)
            ]
            if completed.empty:
                reason = "FEATURE_BAR_MISSING"
            else:
                feature = completed.iloc[-1]
                feature_time = utc_timestamp(feature["decision_time_utc"])
                if timestamp - feature_time > maximum_age:
                    reason = "FEATURE_BAR_STALE"
                elif not all(math.isfinite(float(feature[name])) for name in FEATURE_NAMES):
                    reason = "FEATURE_NONFINITE"
                else:
                    reason = "FEATURE_COMPLETE"
                    decision["candidate_direction"] = str(candidate["direction"]).upper()
                    decision["feature_bar_time_utc"] = feature_time.isoformat().replace(
                        "+00:00", "Z"
                    )
                    for name in FEATURE_NAMES:
                        decision[name] = float(feature[name])
                    complete += 1
        reasons[reason] = reasons.get(reason, 0) + 1
    return {
        "schema_version": "v60_antichase_causal_feature_audit_v1",
        "candidate_rows": len(candidates),
        "complete_feature_rows": complete,
        "reason_counts": dict(sorted(reasons.items())),
    }


def apply_policy(
    rows: Sequence[dict[str, Any]],
    decisions: Mapping[str, Mapping[str, Any]],
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    complete = 0
    vetoes = 0
    reasons: dict[str, int] = {}
    for row in rows:
        decision = decisions.get(str(row["candidate_id"]), {})
        row["candidate_direction"] = decision.get("candidate_direction")
        row["feature_bar_time_utc"] = decision.get("feature_bar_time_utc")
        for name in FEATURE_NAMES:
            row[name] = decision.get(name)
        values = [row.get("atr_ratio"), row.get("dist_hi_24h")]
        feature_complete = (
            row.get("candidate_direction") is not None
            and row.get("feature_bar_time_utc") is not None
            and all(value is not None and math.isfinite(float(value)) for value in values)
        )
        row["causal_policy_features_complete"] = feature_complete
        if feature_complete:
            complete += 1
        mature = int(row["prior_source_executed_count"]) >= int(
            policy["minimum_prior_source_closed_trades"]
        )
        would_veto = bool(
            row["baseline_executed"]
            and mature
            and feature_complete
            and row.get("causal_rank") is not None
            and math.isfinite(float(row["causal_rank"]))
            and float(row["causal_rank"])
            < float(policy["anti_chase_maximum_causal_rank_exclusive"])
            and str(row["candidate_direction"]).upper()
            == str(policy["anti_chase_direction"]).upper()
            and float(row["atr_ratio"])
            >= float(policy["anti_chase_minimum_atr_ratio_inclusive"])
            and float(row["dist_hi_24h"])
            < float(
                policy[
                    "anti_chase_maximum_distance_to_24h_high_atr_exclusive"
                ]
            )
        )
        row["would_veto"] = would_veto
        if not bool(row["baseline_executed"]):
            reason = "BASELINE_NOT_EXECUTED"
        elif row.get("causal_rank") is None:
            reason = "AWAITING_CAUSAL_RANK"
        elif not feature_complete:
            reason = "AWAITING_CAUSAL_POLICY_FEATURES"
        elif not mature:
            reason = "INCOMPLETE_BASELINE_SOURCE_MATURITY"
        elif would_veto and not bool(row["broker_outcome_resolved"]):
            reason = "VETO_AWAITING_BROKER_OUTCOME"
        elif would_veto:
            reason = "VETO_RESOLVED"
        else:
            reason = "RETAIN"
        row["evidence_status"] = reason
        reasons[reason] = reasons.get(reason, 0) + 1
        vetoes += int(would_veto)
    return {
        "schema_version": "v60_antichase_policy_audit_v1",
        "rows": len(rows),
        "complete_feature_rows": complete,
        "raw_veto_opportunities": vetoes,
        "reason_counts": dict(sorted(reasons.items())),
    }

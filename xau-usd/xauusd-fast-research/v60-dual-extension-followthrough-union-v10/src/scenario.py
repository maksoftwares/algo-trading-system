from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Mapping

import numpy as np


ANTI_FEATURES = ("execution_source_id", "direction", "rank", "atr_ratio", "dist_hi_24h", "ret_4h", "ret_24h")


def anti_chase_veto(
    feature: Mapping[str, Any] | None,
    prior_source_closed_count: int,
    rule: Mapping[str, Any],
) -> bool:
    if feature is None or prior_source_closed_count < int(rule["minimum_prior_source_closed_trades"]):
        return False
    if any(name not in feature for name in ANTI_FEATURES):
        return False
    if str(feature["execution_source_id"]) != str(rule["source_id"]):
        return False
    if str(feature["direction"]).upper() != str(rule["direction"]).upper():
        return False
    numeric = np.asarray(
        [feature["rank"], feature["atr_ratio"], feature["dist_hi_24h"], feature["ret_4h"], feature["ret_24h"]],
        dtype=float,
    )
    if not np.isfinite(numeric).all():
        return False
    rank, atr_ratio, distance, ret_4h, ret_24h = numeric
    if ret_24h <= float(rule["minimum_ret_24h_exclusive"]):
        return False
    return bool(
        rank < float(rule["maximum_causal_rank_exclusive"])
        and (
            atr_ratio >= float(rule["minimum_atr_ratio_inclusive"])
            or distance < float(rule["maximum_distance_to_24h_high_atr_exclusive"])
        )
        and ret_4h / ret_24h < float(rule["maximum_ret_4h_to_ret_24h_exclusive"])
    )


def combined_challenger_class(
    replay,
    evaluator,
    feature_map: Mapping[str, Mapping[str, Any]],
    anti_rule: Mapping[str, Any],
):
    class DynamicCombinedScenario(replay.Scenario):
        def __init__(
            self,
            *args: Any,
            rank_map: Mapping[str, float],
            policy: Mapping[str, Any],
            **kwargs: Any,
        ) -> None:
            super().__init__(*args, **kwargs)
            self.rank_map = rank_map
            self.veto_policy = policy
            self.source_closed: dict[str, deque[float]] = defaultdict(
                lambda: deque(maxlen=int(policy["lookback_closed_trades"]))
            )
            self.source_consecutive_losses: dict[str, int] = defaultdict(int)
            self.source_closed_count: dict[str, int] = defaultdict(int)
            self.virtual_profit_factors = evaluator.causal_virtual_profit_factors(
                self.candidates,
                str(policy["source_id"]),
                int(policy["lookback_closed_trades"]),
            )
            self.veto_audit: list[dict[str, Any]] = []

        def _close(
            self,
            trade_id: str,
            now_ms: int,
            pnl: float,
            reason: str,
            *,
            counted_by_v60: bool,
        ) -> None:
            source_id = self.positions[trade_id].candidate.source_id
            super()._close(
                trade_id,
                now_ms,
                pnl,
                reason,
                counted_by_v60=counted_by_v60,
            )
            if evaluator.policy_targets_source(source_id, self.veto_policy):
                self.source_closed[source_id].append(float(pnl))
                self.source_closed_count[source_id] += 1
                self.source_consecutive_losses[source_id] = (
                    self.source_consecutive_losses[source_id] + 1 if pnl < 0.0 else 0
                )

        def _entry_reason(self, candidate: Any, *args: Any, **kwargs: Any) -> str | None:
            reason = super()._entry_reason(candidate, *args, **kwargs)
            if reason is not None:
                return reason
            rank = self.rank_map.get(candidate.trade_id)
            v2_veto, recent_pf = evaluator.should_veto(
                source_id=candidate.source_id,
                rank=rank,
                prior_outcomes=list(self.source_closed[candidate.source_id]),
                policy=self.veto_policy,
                consecutive_losses=self.source_consecutive_losses[candidate.source_id],
                prior_source_closed_count=self.source_closed_count[candidate.source_id],
                virtual_profit_factor=self.virtual_profit_factors.get(candidate.trade_id),
            )
            anti_veto = anti_chase_veto(
                feature_map.get(candidate.trade_id),
                self.source_closed_count[candidate.source_id],
                anti_rule,
            )
            if not v2_veto and not anti_veto:
                return None
            proposal_rule = (
                "V2_SOURCE_HEALTH+V57_WEAK_FOLLOWTHROUGH_ANTICHASE"
                if v2_veto and anti_veto
                else "V2_SOURCE_HEALTH"
                if v2_veto
                else "V57_WEAK_FOLLOWTHROUGH_ANTICHASE"
            )
            self.veto_audit.append(
                {
                    "trade_id": candidate.trade_id,
                    "entry_time_utc": replay.utc_text(candidate.entry_ms),
                    "source_id": candidate.source_id,
                    "proposal_rule": proposal_rule,
                    "causal_rank": rank,
                    "prior_20_profit_factor": recent_pf,
                    "prior_virtual_profit_factor": self.virtual_profit_factors.get(candidate.trade_id),
                    "prior_consecutive_losses": self.source_consecutive_losses[candidate.source_id],
                    "prior_source_closed_count": self.source_closed_count[candidate.source_id],
                    "candidate_endpoint_pnl_usd": candidate.pnl_usd,
                }
            )
            return "V60_DYNAMIC_FOLLOWTHROUGH_UNION_VETO"

    return DynamicCombinedScenario

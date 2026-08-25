from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
import math
from typing import Any, Mapping


REJECTION_REASON = "V60_MONTHLY_QUALITY_RISK_OVERLAY"
PROPOSAL_RULE = "V14_MONTHLY_QUALITY_RISK"


def utc_month(timestamp_ms: int) -> str:
    return datetime.fromtimestamp(timestamp_ms / 1000.0, UTC).strftime("%Y-%m")


def should_veto_monthly(
    *,
    closed_trades: int,
    closed_pnl_usd: float,
    causal_rank: float | None,
    policy: Mapping[str, Any],
) -> bool:
    if closed_trades < int(policy["minimum_closed_trades_in_month"]):
        return False
    if not math.isfinite(float(closed_pnl_usd)):
        raise ValueError("Month P/L must be finite")
    if float(closed_pnl_usd) >= float(policy["maximum_month_pnl_usd_exclusive"]):
        return False
    if causal_rank is None or not math.isfinite(float(causal_rank)):
        return False
    return float(causal_rank) < float(policy["maximum_causal_rank_exclusive"])


def monthly_overlay_class(
    replay,
    base_scenario_type,
    policy: Mapping[str, Any],
):
    class MonthlyQualityScenario(base_scenario_type):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self.month_closed_count: dict[str, int] = defaultdict(int)
            self.month_closed_pnl_usd: dict[str, float] = defaultdict(float)
            self.monthly_overlay_veto_count = 0

        def _close(
            self,
            trade_id: str,
            now_ms: int,
            pnl: float,
            reason: str,
            *,
            counted_by_v60: bool,
        ) -> None:
            month = utc_month(now_ms)
            super()._close(
                trade_id,
                now_ms,
                pnl,
                reason,
                counted_by_v60=counted_by_v60,
            )
            self.month_closed_count[month] += 1
            self.month_closed_pnl_usd[month] += float(pnl)

        def _entry_reason(self, candidate: Any, *args: Any, **kwargs: Any) -> str | None:
            reason = super()._entry_reason(candidate, *args, **kwargs)
            if reason is not None:
                return reason
            month = utc_month(candidate.entry_ms)
            rank = self.rank_map.get(candidate.trade_id)
            if not should_veto_monthly(
                closed_trades=self.month_closed_count[month],
                closed_pnl_usd=self.month_closed_pnl_usd[month],
                causal_rank=rank,
                policy=policy,
            ):
                return None
            self.monthly_overlay_veto_count += 1
            self.veto_audit.append(
                {
                    "trade_id": candidate.trade_id,
                    "entry_time_utc": replay.utc_text(candidate.entry_ms),
                    "source_id": candidate.source_id,
                    "proposal_rule": PROPOSAL_RULE,
                    "causal_rank": rank,
                    "prior_month_closed_trades": self.month_closed_count[month],
                    "prior_month_closed_pnl_usd": self.month_closed_pnl_usd[month],
                    "candidate_endpoint_pnl_usd": candidate.pnl_usd,
                }
            )
            return REJECTION_REASON

    return MonthlyQualityScenario

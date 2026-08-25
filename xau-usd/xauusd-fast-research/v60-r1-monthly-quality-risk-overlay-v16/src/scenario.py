from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
import heapq
import math
from typing import Any, Mapping

import pandas as pd


REJECTION_REASON = "V60_R1_MONTHLY_QUALITY_RISK_OVERLAY"
PROPOSAL_RULE = "V16_R1_MONTHLY_QUALITY_RISK"


def utc_month(timestamp_ms: int) -> str:
    return datetime.fromtimestamp(timestamp_ms / 1000.0, UTC).strftime("%Y-%m")


def source_is_eligible(source_id: str, policy: Mapping[str, Any]) -> bool:
    return str(source_id) in {str(value) for value in policy["eligible_source_ids"]}


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


def monthly_overlay_class(replay, base_scenario_type, policy: Mapping[str, Any]):
    class R1MonthlyQualityScenario(base_scenario_type):
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
            if reason is not None or not source_is_eligible(candidate.source_id, policy):
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

    return R1MonthlyQualityScenario


def apply_overlay_sequence(
    frame: pd.DataFrame,
    policy: Mapping[str, Any],
    *,
    id_column: str,
    entry_column: str,
    exit_column: str,
    pnl_column: str,
    rank_column: str,
    base_veto_column: str,
    canonical_pnl_column: str | None = None,
) -> pd.DataFrame:
    work = frame.copy()
    work[entry_column] = pd.to_datetime(work[entry_column], utc=True, format="mixed")
    work[exit_column] = pd.to_datetime(work[exit_column], utc=True, format="mixed")
    work[pnl_column] = pd.to_numeric(work[pnl_column], errors="raise").astype(float)
    work[rank_column] = pd.to_numeric(work[rank_column], errors="coerce")
    work[base_veto_column] = work[base_veto_column].astype(bool)
    canonical = canonical_pnl_column or pnl_column
    work[canonical] = pd.to_numeric(work[canonical], errors="raise").astype(float)
    month_count: dict[str, int] = {}
    month_pnl: dict[str, float] = {}
    pending: list[tuple[int, int, str, float]] = []
    records: list[dict[str, Any]] = []
    sequence = 0
    for row in work.sort_values([entry_column, id_column], kind="stable").to_dict("records"):
        entry = pd.Timestamp(row[entry_column])
        while pending and pending[0][0] <= entry.value:
            _, _, month, pnl = heapq.heappop(pending)
            month_count[month] = month_count.get(month, 0) + 1
            month_pnl[month] = month_pnl.get(month, 0.0) + pnl
        month = entry.strftime("%Y-%m")
        before_count = month_count.get(month, 0)
        before_pnl = month_pnl.get(month, 0.0)
        rank = None if pd.isna(row[rank_column]) else float(row[rank_column])
        source_id = str(row.get("source_id") or row.get("runtime_source_id") or "")
        monthly_veto = False
        if not bool(row[base_veto_column]) and source_is_eligible(source_id, policy):
            monthly_veto = should_veto_monthly(
                closed_trades=before_count,
                closed_pnl_usd=before_pnl,
                causal_rank=rank,
                policy=policy,
            )
        retained = not bool(row[base_veto_column]) and not monthly_veto
        output = dict(row)
        output.update(
            {
                "prior_month_closed_trades": before_count,
                "prior_month_closed_pnl_usd": before_pnl,
                "monthly_quality_veto": monthly_veto,
                "v14_retained": retained,
            }
        )
        records.append(output)
        if retained:
            sequence += 1
            close = pd.Timestamp(row[exit_column])
            heapq.heappush(
                pending,
                (close.value, sequence, close.strftime("%Y-%m"), float(row[canonical])),
            )
    return pd.DataFrame(records)

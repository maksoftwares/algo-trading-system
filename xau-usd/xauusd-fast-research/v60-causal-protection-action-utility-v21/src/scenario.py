from __future__ import annotations

import math
from collections.abc import Mapping, MutableSequence
from datetime import UTC, datetime
from typing import Any

CATEGORICAL_FEATURES = ("source_id", "direction")
NUMERIC_FEATURES = (
    "own_open_pnl_r",
    "basket_open_pnl_r",
    "basket_peak_pnl_r",
    "basket_giveback_from_peak_r",
    "own_risk_share",
    "own_open_pnl_share",
    "holding_hours",
    "minutes_since_protection_arm",
    "open_position_count",
    "close_hour_sin",
    "close_hour_cos",
)
MODEL_FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES
FORBIDDEN_MODEL_FIELDS = {
    "action_year",
    "candidate_endpoint_pnl_usd",
    "candidate_endpoint_exit_time_utc",
    "keep_open_utility_r",
    "fold",
    "trade_id",
    "action_id",
    "action_time_utc",
}


def build_action_rows(
    *,
    replay: Any,
    positions: Mapping[str, Any],
    marked_pnl: Mapping[str, float],
    now_ms: int,
    arm_ms: int,
    active_risk: float,
    open_pnl: float,
    peak_open_pnl: float,
) -> list[dict[str, Any]]:
    if active_risk <= 0.0 or not math.isfinite(active_risk):
        raise ValueError("Protection action has invalid active risk")
    if arm_ms > now_ms:
        raise ValueError("Protection arm timestamp is after giveback timestamp")
    trade_ids = sorted(positions)
    if not trade_ids:
        raise ValueError("Protection action cannot be empty")
    action_time = str(replay.utc_text(now_ms))
    action_id = action_time + "|" + ",".join(trade_ids)
    timestamp = datetime.fromtimestamp(now_ms / 1000.0, UTC)
    minute_of_day = timestamp.hour * 60 + timestamp.minute
    angle = 2.0 * math.pi * minute_of_day / 1440.0
    position_count = len(trade_ids)
    rows: list[dict[str, Any]] = []
    for trade_id in trade_ids:
        position = positions[trade_id]
        candidate = position.candidate
        current_pnl = float(marked_pnl[trade_id])
        risk = float(candidate.risk_usd)
        if risk <= 0.0 or not math.isfinite(risk):
            raise ValueError(f"Position has invalid initial risk: {trade_id}")
        row = {
            "action_id": action_id,
            "action_time_utc": action_time,
            "action_year": int(timestamp.year),
            "trade_id": str(trade_id),
            "source_id": str(candidate.source_id),
            "direction": str(candidate.direction),
            "entry_time_utc": str(replay.utc_text(candidate.entry_ms)),
            "candidate_endpoint_exit_time_utc": str(replay.utc_text(candidate.exit_ms)),
            "positions_in_action": int(position_count),
            "action_sample_weight": 1.0 / position_count,
            "initial_risk_usd": risk,
            "protected_close_pnl_usd": current_pnl,
            "candidate_endpoint_pnl_usd": float(candidate.pnl_usd),
            "keep_open_utility_r": (float(candidate.pnl_usd) - current_pnl) / risk,
            "own_open_pnl_r": current_pnl / risk,
            "basket_open_pnl_r": open_pnl / active_risk,
            "basket_peak_pnl_r": peak_open_pnl / active_risk,
            "basket_giveback_from_peak_r": (peak_open_pnl - open_pnl) / active_risk,
            "own_risk_share": risk / active_risk,
            "own_open_pnl_share": (
                current_pnl / abs(open_pnl) if abs(open_pnl) > 1e-12 else 0.0
            ),
            "holding_hours": (now_ms - candidate.entry_ms) / 3_600_000.0,
            "minutes_since_protection_arm": (now_ms - arm_ms) / 60_000.0,
            "open_position_count": float(position_count),
            "close_hour_sin": math.sin(angle),
            "close_hour_cos": math.cos(angle),
        }
        numeric = [
            value
            for key, value in row.items()
            if key
            not in {
                "action_id",
                "action_time_utc",
                "trade_id",
                "source_id",
                "direction",
                "entry_time_utc",
                "candidate_endpoint_exit_time_utc",
            }
        ]
        if not all(math.isfinite(float(value)) for value in numeric):
            raise ValueError(f"Non-finite action snapshot: {trade_id}")
        rows.append(row)
    return rows


def observational_challenger_class(
    replay: Any,
    evaluator: Any,
    v6_scenario: Any,
    feature_map: Mapping[str, Mapping[str, Any]],
    anti_rule: Mapping[str, Any],
    instance_sink: MutableSequence[Any],
) -> type:
    parent_type = v6_scenario.combined_challenger_class(
        replay, evaluator, feature_map, anti_rule
    )

    class ObservationalDynamicV6(parent_type):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self.protection_action_snapshots: list[dict[str, Any]] = []
            self._observed_protection_arm_ms: int | None = None
            instance_sink.append(self)

        def _evaluate_profit_protection(
            self, now_ms: int, bid: float, ask: float
        ) -> None:
            settings = self.config.get("portfolio_protection")
            tickets = set(self.positions)
            enabled = isinstance(settings, Mapping) and bool(settings.get("enabled"))
            reset_for_disjoint_basket = bool(
                tickets
                and self.profit_protection_tickets
                and not self.profit_protection_tickets.intersection(tickets)
            )
            if not tickets or reset_for_disjoint_basket:
                self._observed_protection_arm_ms = None

            snapshot_rows: list[dict[str, Any]] = []
            capture_expected = False
            if enabled and tickets:
                effective_armed = (
                    False
                    if reset_for_disjoint_basket
                    else bool(self.profit_protection_armed)
                )
                prior_peak = (
                    0.0
                    if reset_for_disjoint_basket
                    else float(self.profit_protection_peak_open_pnl)
                )
                marked = {
                    trade_id: float(self._market_pnl(position, bid, ask))
                    for trade_id, position in self.positions.items()
                }
                active_risk = sum(
                    float(position.candidate.risk_usd)
                    for position in self.positions.values()
                )
                open_pnl = float(sum(marked.values()))
                peak_open_pnl = max(prior_peak, open_pnl)
                retain = float(settings["open_profit_retain_r"]) * active_risk
                capture_expected = bool(effective_armed and open_pnl <= retain)
                if capture_expected:
                    if self._observed_protection_arm_ms is None:
                        raise ValueError(
                            "Observed armed basket has no causal arm timestamp"
                        )
                    snapshot_rows = build_action_rows(
                        replay=replay,
                        positions=self.positions,
                        marked_pnl=marked,
                        now_ms=now_ms,
                        arm_ms=self._observed_protection_arm_ms,
                        active_risk=active_risk,
                        open_pnl=open_pnl,
                        peak_open_pnl=peak_open_pnl,
                    )

            event_start = len(self.event_rows)
            super()._evaluate_profit_protection(now_ms, bid, ask)
            new_events = self.event_rows[event_start:]
            arm_events = [
                row
                for row in new_events
                if row["event"] == "OPEN_PROFIT_PROTECTION_ARMED"
            ]
            giveback_events = [
                row
                for row in new_events
                if row["event"] == "POSITION_CLOSED"
                and row.get("reason") == "OPEN_PROFIT_GIVEBACK"
            ]
            if len(arm_events) > 1:
                raise ValueError("Multiple protection arm events in one cycle")
            if arm_events:
                self._observed_protection_arm_ms = now_ms

            if capture_expected:
                expected_ids = sorted(row["trade_id"] for row in snapshot_rows)
                observed_ids = sorted(str(row["trade_id"]) for row in giveback_events)
                if expected_ids != observed_ids:
                    raise ValueError(
                        "Snapshot and frozen giveback close IDs diverged: "
                        f"{expected_ids} != {observed_ids}"
                    )
                close_pnl = {
                    str(row["trade_id"]): float(row["pnl_usd"])
                    for row in giveback_events
                }
                for row in snapshot_rows:
                    if not math.isclose(
                        float(row["protected_close_pnl_usd"]),
                        close_pnl[str(row["trade_id"])],
                        rel_tol=0.0,
                        abs_tol=1e-12,
                    ):
                        raise ValueError("Snapshot P/L differs from frozen close P/L")
                self.protection_action_snapshots.extend(snapshot_rows)
                self._observed_protection_arm_ms = None
            elif giveback_events:
                raise ValueError("Frozen giveback close was not captured causally")

    return ObservationalDynamicV6

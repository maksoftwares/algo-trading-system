from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np


@dataclass
class ProtectionState:
    armed: bool = False
    peak_pnl_usd: float = 0.0


def protection_threshold(
    policy: Mapping[str, Any], risk_usd: float, peak_pnl_usd: float
) -> float:
    values = np.asarray([risk_usd, peak_pnl_usd], dtype=float)
    if not np.isfinite(values).all() or risk_usd <= 0.0:
        raise ValueError("Risk and peak P/L must be finite and risk positive")
    floor = float(policy["retain_r"]) * risk_usd
    giveback = policy.get("giveback_r")
    if giveback is None:
        return floor
    return max(floor, peak_pnl_usd - float(giveback) * risk_usd)


def update_protection(
    state: ProtectionState,
    policy: Mapping[str, Any],
    risk_usd: float,
    pnl_usd: float,
) -> str:
    values = np.asarray([risk_usd, pnl_usd], dtype=float)
    if not np.isfinite(values).all() or risk_usd <= 0.0:
        raise ValueError("Risk and open P/L must be finite and risk positive")
    state.peak_pnl_usd = max(state.peak_pnl_usd, pnl_usd)
    if not state.armed:
        if pnl_usd >= float(policy["arm_r"]) * risk_usd:
            state.armed = True
            return "ARM"
        return "HOLD"
    return (
        "CLOSE"
        if pnl_usd <= protection_threshold(policy, risk_usd, state.peak_pnl_usd)
        else "HOLD"
    )


def managed_challenger_class(
    replay,
    evaluator,
    v12_scenario,
    feature_map: Mapping[str, Mapping[str, Any]],
    anti_rule: Mapping[str, Any],
    individual_policy: Mapping[str, Any],
    source_health_cost_offset_usd: float = 0.0,
):
    base_type = v12_scenario.combined_challenger_class(
        replay,
        evaluator,
        feature_map,
        anti_rule,
        source_health_cost_offset_usd=source_health_cost_offset_usd,
    )

    class ManagedCombinedScenario(base_type):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self.individual_policy = dict(individual_policy)
            self.individual_states: dict[str, ProtectionState] = {}
            self.individual_profit_arms = 0
            self.individual_profit_closes = 0
            self.individual_profit_close_losses = 0

        def _close(
            self,
            trade_id: str,
            now_ms: int,
            pnl: float,
            reason: str,
            *,
            counted_by_v60: bool,
        ) -> None:
            self.individual_states.pop(trade_id, None)
            super()._close(
                trade_id,
                now_ms,
                pnl,
                reason,
                counted_by_v60=counted_by_v60,
            )

        def _evaluate_individual_protection(
            self, now_ms: int, bid: float, ask: float
        ) -> None:
            if not bool(self.individual_policy.get("enabled")):
                return
            for trade_id in sorted(list(self.positions)):
                position = self.positions.get(trade_id)
                if position is None:
                    continue
                state = self.individual_states.setdefault(trade_id, ProtectionState())
                pnl = self._market_pnl(position, bid, ask)
                action = update_protection(
                    state,
                    self.individual_policy,
                    position.candidate.risk_usd,
                    pnl,
                )
                if action == "ARM":
                    self.individual_profit_arms += 1
                    self._record(
                        "INDIVIDUAL_PROFIT_PROTECTION_ARMED",
                        now_ms,
                        position.candidate,
                        open_pnl_usd=pnl,
                        peak_pnl_usd=state.peak_pnl_usd,
                        initial_risk_usd=position.candidate.risk_usd,
                    )
                elif action == "CLOSE":
                    candidate = position.candidate
                    peak = state.peak_pnl_usd
                    threshold = protection_threshold(
                        self.individual_policy, candidate.risk_usd, peak
                    )
                    self._close(
                        trade_id,
                        now_ms,
                        pnl,
                        "INDIVIDUAL_PROFIT_GIVEBACK",
                        counted_by_v60=True,
                    )
                    self.individual_profit_closes += 1
                    if pnl < 0.0:
                        self.individual_profit_close_losses += 1
                    self._record(
                        "INDIVIDUAL_PROFIT_PROTECTION_CLOSED",
                        now_ms,
                        candidate,
                        pnl_usd=pnl,
                        original_source_pnl_usd=candidate.pnl_usd,
                        peak_pnl_usd=peak,
                        trigger_threshold_usd=threshold,
                    )

        def _evaluate_profit_protection(
            self, now_ms: int, bid: float, ask: float
        ) -> None:
            self._evaluate_individual_protection(now_ms, bid, ask)
            super()._evaluate_profit_protection(now_ms, bid, ask)

        def simulate(self, quotes: Mapping[str, np.ndarray]) -> dict[str, Any]:
            result = super().simulate(quotes)
            result.update(
                {
                    "individual_profit_protection_arms": self.individual_profit_arms,
                    "individual_profit_protection_closes": self.individual_profit_closes,
                    "individual_profit_protection_close_losses": self.individual_profit_close_losses,
                }
            )
            return result

    return ManagedCombinedScenario

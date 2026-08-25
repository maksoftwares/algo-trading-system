from __future__ import annotations

from typing import Any, Mapping


def protected_positions(
    positions: Mapping[str, Any], exempt_source_ids: set[str]
) -> dict[str, Any]:
    return {
        str(trade_id): position
        for trade_id, position in positions.items()
        if str(position.candidate.source_id) not in exempt_source_ids
    }


def v7_exempt_challenger_class(
    replay,
    evaluator,
    v6_scenario,
    feature_map: Mapping[str, Mapping[str, Any]],
    anti_rule: Mapping[str, Any],
    policy: Mapping[str, Any],
):
    base_type = v6_scenario.combined_challenger_class(
        replay, evaluator, feature_map, anti_rule
    )
    exempt_sources = {str(value) for value in policy["exempt_source_ids"]}

    class V7ExemptProtectionScenario(base_type):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            settings = self.config.get("portfolio_protection")
            if not isinstance(settings, Mapping) or not bool(settings.get("enabled")):
                raise ValueError("V18 requires the deployed portfolio protection overlay")
            if float(settings["open_profit_arm_r"]) != float(
                policy["account_profit_protection_arm_r"]
            ) or float(settings["open_profit_retain_r"]) != float(
                policy["account_profit_protection_retain_r"]
            ):
                raise ValueError("V18 portfolio protection thresholds changed")
            self.v7_exempt_cycles = 0
            self.v7_exempt_only_cycles = 0
            self.v7_exempt_overlap_cycles = 0
            self.v7_exempt_trade_ids: set[str] = set()

        def _reset_profit_protection(self) -> None:
            self.profit_protection_armed = False
            self.profit_protection_peak_open_pnl = 0.0
            self.profit_protection_tickets = set()

        def _evaluate_profit_protection(
            self, now_ms: int, bid: float, ask: float
        ) -> None:
            settings = self.config.get("portfolio_protection")
            if not isinstance(settings, Mapping) or not bool(settings.get("enabled")):
                return

            exempt = {
                str(trade_id): position
                for trade_id, position in self.positions.items()
                if str(position.candidate.source_id) in exempt_sources
            }
            if exempt:
                self.v7_exempt_cycles += 1
                self.v7_exempt_trade_ids.update(exempt)

            protected = protected_positions(self.positions, exempt_sources)
            tickets = set(protected)
            if exempt and protected:
                self.v7_exempt_overlap_cycles += 1
            elif exempt:
                self.v7_exempt_only_cycles += 1

            if not tickets:
                self._reset_profit_protection()
                return
            if self.profit_protection_tickets and not self.profit_protection_tickets.intersection(
                tickets
            ):
                self.profit_protection_armed = False
                self.profit_protection_peak_open_pnl = 0.0
            self.profit_protection_tickets = tickets

            active_risk = sum(
                position.candidate.risk_usd for position in protected.values()
            )
            open_pnl = sum(
                self._market_pnl(position, bid, ask) for position in protected.values()
            )
            self.profit_protection_peak_open_pnl = max(
                self.profit_protection_peak_open_pnl, open_pnl
            )
            arm = float(settings["open_profit_arm_r"]) * active_risk
            retain = float(settings["open_profit_retain_r"]) * active_risk
            if not self.profit_protection_armed and open_pnl >= arm:
                self.profit_protection_armed = True
                self.profit_protection_arms += 1
                self._record(
                    "OPEN_PROFIT_PROTECTION_ARMED",
                    now_ms,
                    open_pnl_usd=open_pnl,
                    active_initial_risk_usd=active_risk,
                    exempt_source_ids=sorted(exempt_sources),
                )
            elif self.profit_protection_armed and open_pnl <= retain:
                for trade_id in sorted(tickets):
                    position = self.positions.get(trade_id)
                    if position is None:
                        continue
                    self._close(
                        trade_id,
                        now_ms,
                        self._market_pnl(position, bid, ask),
                        "OPEN_PROFIT_GIVEBACK",
                        counted_by_v60=True,
                    )
                    self.profit_giveback_closes += 1
                self._reset_profit_protection()

        def simulate(self, quotes: Mapping[str, Any]) -> dict[str, Any]:
            result = super().simulate(quotes)
            result.update(
                {
                    "v7_profit_protection_exempt_cycles": self.v7_exempt_cycles,
                    "v7_profit_protection_exempt_only_cycles": self.v7_exempt_only_cycles,
                    "v7_profit_protection_exempt_overlap_cycles": self.v7_exempt_overlap_cycles,
                    "v7_profit_protection_exempt_trade_ids": sorted(
                        self.v7_exempt_trade_ids
                    ),
                }
            )
            return result

    return V7ExemptProtectionScenario

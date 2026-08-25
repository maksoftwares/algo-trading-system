from __future__ import annotations

from typing import Any, Mapping


def v7_solo_bypass_challenger_class(
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
    solo_source_id = str(policy["solo_source_id"])

    class V7SoloProtectionBypassScenario(base_type):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            settings = self.config.get("portfolio_protection")
            if not isinstance(settings, Mapping) or not bool(settings.get("enabled")):
                raise ValueError("V20 requires the deployed portfolio protection overlay")
            if float(settings["open_profit_arm_r"]) != float(
                policy["account_profit_protection_arm_r"]
            ) or float(settings["open_profit_retain_r"]) != float(
                policy["account_profit_protection_retain_r"]
            ):
                raise ValueError("V20 portfolio protection thresholds changed")
            self.v7_present_cycles = 0
            self.v7_solo_bypass_cycles = 0
            self.v7_mixed_basket_cycles = 0
            self.standard_protection_cycles = 0
            self.v7_solo_bypass_trade_ids: set[str] = set()

        def _reset_profit_protection(self) -> None:
            self.profit_protection_armed = False
            self.profit_protection_peak_open_pnl = 0.0
            self.profit_protection_tickets = set()

        def _evaluate_profit_protection(
            self, now_ms: int, bid: float, ask: float
        ) -> None:
            source_ids = {
                str(position.candidate.source_id)
                for position in self.positions.values()
            }
            v7_trade_ids = {
                str(trade_id)
                for trade_id, position in self.positions.items()
                if str(position.candidate.source_id) == solo_source_id
            }
            if v7_trade_ids:
                self.v7_present_cycles += 1

            if source_ids == {solo_source_id}:
                self.v7_solo_bypass_cycles += 1
                self.v7_solo_bypass_trade_ids.update(v7_trade_ids)
                self._reset_profit_protection()
                return

            if v7_trade_ids:
                self.v7_mixed_basket_cycles += 1
            self.standard_protection_cycles += 1
            super()._evaluate_profit_protection(now_ms, bid, ask)

        def simulate(self, quotes: Mapping[str, Any]) -> dict[str, Any]:
            result = super().simulate(quotes)
            result.update(
                {
                    "v7_present_cycles": self.v7_present_cycles,
                    "v7_solo_bypass_cycles": self.v7_solo_bypass_cycles,
                    "v7_mixed_basket_cycles": self.v7_mixed_basket_cycles,
                    "standard_protection_cycles": self.standard_protection_cycles,
                    "v7_solo_bypass_trade_ids": sorted(
                        self.v7_solo_bypass_trade_ids
                    ),
                }
            )
            return result

    return V7SoloProtectionBypassScenario

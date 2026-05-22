from __future__ import annotations

from typing import Any

from phase0.strategies.breakout_retest import BreakoutRetestStrategy


class SwingBreakoutRetestV0Strategy(BreakoutRetestStrategy):
    """Disabled research strategy for breakout-retest restricted to latest swing levels only."""

    name = "swing_breakout_retest_v0"
    version = "0.1-research-disabled"

    def _candidate_levels_from_arrays(
        self,
        arrays: dict[str, Any],
        position: int,
        direction: str,
        point_size: float,
    ) -> list[dict[str, Any]]:
        levels = super()._candidate_levels_from_arrays(arrays, position, direction, point_size)
        expected_kind = "latest_swing_high" if direction == "LONG" else "latest_swing_low"
        return [level for level in levels if level["level_kind"] == expected_kind]

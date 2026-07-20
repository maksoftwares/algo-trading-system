from __future__ import annotations

import itertools
import json
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_ROOT = ROOT.parent / "comex-size-segment-flow-v32"
BASE_SRC = BASE_ROOT / "src"
if str(BASE_SRC) not in sys.path:
    sys.path.insert(0, str(BASE_SRC))

import size_segment_flow as base  # noqa: E402


def load_config(path: Path) -> dict[str, Any]:
    overlay = json.loads(path.read_text(encoding="utf-8"))
    base_path = (ROOT / overlay["base_config"]).resolve()
    config = base.load_config(base_path)
    config["campaign_id"] = str(overlay["campaign_id"])
    config["calibration"] = dict(overlay["calibration"])
    config["selection"] = dict(overlay["selection"])
    config["v33_overlay"] = overlay
    return config


def policy_grid(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    calibration = config["calibration"]
    rows = []
    for values in itertools.product(
        calibration["large_trade_size_grid"],
        calibration["minimum_large_volume_grid"],
        calibration["minimum_absolute_large_imbalance_grid"],
        calibration["minimum_absolute_opposing_small_imbalance_grid"],
        calibration["minimum_small_volume_grid"],
        calibration["cooldown_minutes_grid"],
    ):
        size, volume, large_imbalance, small_imbalance, small_volume, cooldown = values
        rows.append(
            {
                "large_trade_size": int(size),
                "minimum_large_volume": int(volume),
                "minimum_absolute_large_imbalance": float(large_imbalance),
                "minimum_absolute_opposing_small_imbalance": float(small_imbalance),
                "minimum_small_volume": int(small_volume),
                "cooldown_minutes": int(cooldown),
            }
        )
    return rows


def policy_id(policy: Mapping[str, Any]) -> str:
    return (
        f"SZ{int(policy['large_trade_size']):02d}"
        f"__LV{int(policy['minimum_large_volume']):03d}"
        f"__LI{int(round(float(policy['minimum_absolute_large_imbalance']) * 100)):02d}"
        f"__SI{int(round(float(policy['minimum_absolute_opposing_small_imbalance']) * 100)):02d}"
        f"__SV{int(policy['minimum_small_volume']):03d}"
        f"__CD{int(policy['cooldown_minutes']):02d}"
    )


def generate_candidates(
    bars: Any, *, policy: Mapping[str, Any], rule: Mapping[str, Any]
) -> Any:
    adjusted_rule = dict(rule)
    adjusted_rule["minimum_small_volume"] = int(policy["minimum_small_volume"])
    adjusted_rule["cooldown_minutes"] = int(policy["cooldown_minutes"])
    clean_policy = {
        "large_trade_size": int(policy["large_trade_size"]),
        "minimum_large_volume": int(policy["minimum_large_volume"]),
        "minimum_absolute_large_imbalance": float(
            policy["minimum_absolute_large_imbalance"]
        ),
        "minimum_absolute_opposing_small_imbalance": float(
            policy["minimum_absolute_opposing_small_imbalance"]
        ),
    }
    return base.generate_candidates(bars, policy=clean_policy, rule=adjusted_rule)


def summarize_candidate_facts(
    candidates: Any,
    *,
    eligible_dates: list[str],
    policy: Mapping[str, Any],
    selection: Mapping[str, Any],
) -> dict[str, Any]:
    facts = base.summarize_candidate_facts(
        candidates,
        eligible_dates=eligible_dates,
        policy=policy,
        selection=selection,
    )
    facts["policy_id"] = policy_id(policy)
    return facts


def select_policy(
    rows: Iterable[Mapping[str, Any]], selection: Mapping[str, Any]
) -> dict[str, Any] | None:
    eligible = [dict(row) for row in rows if bool(row["selection_eligible"])]
    if not eligible:
        return None
    target = float(selection["target_candidates_per_full_weekday"])
    eligible.sort(
        key=lambda row: (
            abs(float(row["candidates_per_full_weekday"]) - target),
            -int(row["large_trade_size"]),
            -int(row["minimum_large_volume"]),
            -float(row["minimum_absolute_large_imbalance"]),
            -float(row["minimum_absolute_opposing_small_imbalance"]),
            -int(row["minimum_small_volume"]),
            -int(row["cooldown_minutes"]),
            str(row["policy_id"]),
        )
    )
    keys = {
        "policy_id",
        "large_trade_size",
        "minimum_large_volume",
        "minimum_absolute_large_imbalance",
        "minimum_absolute_opposing_small_imbalance",
        "minimum_small_volume",
        "cooldown_minutes",
    }
    return {key: value for key, value in eligible[0].items() if key in keys}

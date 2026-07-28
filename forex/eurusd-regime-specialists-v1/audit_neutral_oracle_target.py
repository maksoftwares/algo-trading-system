from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parent
DEFAULT_ORACLE = (
    ROOT
    / "outputs"
    / "retrospective_overfit"
    / "FULL_CALENDAR_PERFECT_FORESIGHT_TRADES.csv"
)


def _minute_of_day(value: str) -> int:
    parsed = pd.Timestamp(f"2000-01-01T{value}:00Z")
    return int(parsed.hour * 60 + parsed.minute)


def build_target_audit(
    oracle_path: Path = DEFAULT_ORACLE,
    *,
    anchor_time_utc: str = "12:45",
    windows_minutes: tuple[int, ...] = (15, 60, 240),
) -> dict[str, Any]:
    payload = oracle_path.read_bytes()
    try:
        oracle_label = oracle_path.resolve().relative_to(
            ROOT.resolve()
        ).as_posix()
    except ValueError:
        oracle_label = oracle_path.name
    frame = pd.read_csv(oracle_path)
    required = {
        "entry_time_utc",
        "side",
        "regime",
        "risk_tier_pips",
        "fallback_risk_tier",
    }
    if not required.issubset(frame.columns):
        raise ValueError("Perfect-foresight ledger lacks target audit fields")
    frame["entry_time_utc"] = pd.to_datetime(
        frame["entry_time_utc"], utc=True
    ).dt.as_unit("ns")
    neutral = frame[frame["regime"].eq("NEUTRAL")].copy()
    neutral["oracle_date"] = neutral["entry_time_utc"].dt.strftime(
        "%Y-%m-%d"
    )
    neutral["minute_of_day"] = (
        neutral["entry_time_utc"].dt.hour * 60
        + neutral["entry_time_utc"].dt.minute
    )
    anchor = _minute_of_day(anchor_time_utc)
    clock_counts = (
        neutral["entry_time_utc"]
        .dt.strftime("%H:%M")
        .value_counts()
        .sort_index()
    )
    window_metrics: dict[str, Any] = {}
    all_dates = pd.Index(sorted(neutral["oracle_date"].unique()))
    for window in windows_minutes:
        nearby = neutral[
            neutral["minute_of_day"].sub(anchor).abs().le(int(window))
        ]
        side_counts = (
            nearby.groupby("oracle_date")["side"]
            .nunique()
            .reindex(all_dates, fill_value=0)
        )
        window_metrics[f"plus_minus_{int(window)}_minutes"] = {
            "oracle_rows": len(nearby),
            "oracle_row_share": (
                float(len(nearby) / len(neutral)) if len(neutral) else 0.0
            ),
            "dates_with_any_oracle_side": int(side_counts.gt(0).sum()),
            "maximum_fixed_anchor_precision_if_side_known": float(
                side_counts.gt(0).mean()
            ),
            "uniform_side_precision_at_fixed_anchor": float(
                (side_counts / 2.0).mean()
            ),
        }
    return {
        "schema_version": "eurusd_neutral_oracle_target_timing_audit_v1",
        "development_data_only": True,
        "strategy_or_threshold_changed": False,
        "historical_pnl_used_for_selection": False,
        "oracle_relative_path": oracle_label,
        "oracle_sha256": hashlib.sha256(payload).hexdigest(),
        "all_oracle_rows": len(frame),
        "neutral_oracle_rows": len(neutral),
        "neutral_oracle_dates": int(neutral["oracle_date"].nunique()),
        "neutral_side_counts": {
            str(key): int(value)
            for key, value in neutral["side"].value_counts().items()
        },
        "neutral_risk_tier_counts": {
            str(key): int(value)
            for key, value in neutral["risk_tier_pips"]
            .value_counts(dropna=False)
            .items()
        },
        "neutral_fallback_risk_tier_share": float(
            neutral["fallback_risk_tier"].astype(bool).mean()
        ),
        "neutral_rows_at_0000_through_0015": int(
            neutral["minute_of_day"].le(15).sum()
        ),
        "neutral_rows_before_0100": int(
            neutral["minute_of_day"].lt(60).sum()
        ),
        "neutral_rows_before_0200": int(
            neutral["minute_of_day"].lt(120).sum()
        ),
        "neutral_rows_before_0100_share": float(
            neutral["minute_of_day"].lt(60).mean()
        ),
        "neutral_clock_counts": {
            str(key): int(value) for key, value in clock_counts.items()
        },
        "fixed_event_anchor_utc": anchor_time_utc,
        "fixed_event_anchor_proximity": window_metrics,
        "interpretation": (
            "The oracle scans M5 entries chronologically and stops after the "
            "first four target-before-stop winners. Its clock concentration "
            "is therefore a construction artifact, not an independent "
            "causal session hypothesis."
        ),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle", type=Path, default=DEFAULT_ORACLE)
    parser.add_argument("--anchor-time-utc", default="12:45")
    return parser


def main() -> None:
    args = _parser().parse_args()
    result = build_target_audit(
        args.oracle,
        anchor_time_utc=args.anchor_time_utc,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

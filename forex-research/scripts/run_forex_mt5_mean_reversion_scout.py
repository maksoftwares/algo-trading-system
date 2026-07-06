from __future__ import annotations

import argparse
import json
from pathlib import Path

import run_forex_mt5_frequency_scout as freq


FOREX_ROOT = Path(__file__).resolve().parents[1]
EA_NAME = "ForexMeanReversionScout"
EA_SOURCE = FOREX_ROOT / "mt5" / "Experts" / f"{EA_NAME}.mq5"
DEFAULT_OUTPUT_DIR = FOREX_ROOT / "outputs" / "reports" / "mt5_backtests" / "mean_reversion_scout"


VARIANTS = [
    freq.Variant(
        name="bb_close_fade",
        signal_mode="0",
        description="M5 Bollinger close outside band faded, RSI filter off.",
        inputs={
            "InpSignalMode": "0",
            "InpUseRsiFilter": "false",
            "InpBandsPeriod": "20",
            "InpBandsDeviation": "2.0",
            "InpStopAtrMultiple": "1.40",
            "InpRiskReward": "0.80",
        },
    ),
    freq.Variant(
        name="rsi_bb_close_fade",
        signal_mode="0",
        description="M5 Bollinger close outside band faded with RSI 35/65 confirmation.",
        inputs={
            "InpSignalMode": "0",
            "InpUseRsiFilter": "true",
            "InpRsiOversold": "35.0",
            "InpRsiOverbought": "65.0",
            "InpBandsPeriod": "20",
            "InpBandsDeviation": "2.0",
            "InpStopAtrMultiple": "1.40",
            "InpRiskReward": "0.80",
        },
    ),
    freq.Variant(
        name="bb_wick_reclaim",
        signal_mode="1",
        description="M5 Bollinger band wick breach then reclaim, RSI 35/65 confirmation.",
        inputs={
            "InpSignalMode": "1",
            "InpUseRsiFilter": "true",
            "InpRsiOversold": "35.0",
            "InpRsiOverbought": "65.0",
            "InpBandsPeriod": "20",
            "InpBandsDeviation": "2.0",
            "InpStopAtrMultiple": "1.40",
            "InpRiskReward": "0.80",
        },
    ),
    freq.Variant(
        name="rsi_extreme_fade",
        signal_mode="2",
        description="M5 RSI 30/70 extreme faded toward mean.",
        inputs={
            "InpSignalMode": "2",
            "InpUseRsiFilter": "true",
            "InpRsiOversold": "30.0",
            "InpRsiOverbought": "70.0",
            "InpBandsPeriod": "20",
            "InpBandsDeviation": "2.0",
            "InpStopAtrMultiple": "1.40",
            "InpRiskReward": "0.80",
        },
    ),
]


def selected_variants(names: str) -> list[freq.Variant]:
    if not names:
        return VARIANTS
    requested = {item.strip() for item in names.split(",") if item.strip()}
    found = [variant for variant in VARIANTS if variant.name in requested]
    missing = requested.difference({variant.name for variant in found})
    if missing:
        raise ValueError(f"Unknown mean-reversion variants: {', '.join(sorted(missing))}")
    return found


def expand_signal_timeframes(variants: list[freq.Variant], values_csv: str) -> list[freq.Variant]:
    requested = [item.strip().upper() for item in values_csv.split(",") if item.strip()]
    if not requested:
        requested = ["M5"]
    timeframe_map = {
        "M5": ("m5", "5"),
        "M15": ("m15", "15"),
        "M30": ("m30", "30"),
    }
    unknown = set(requested).difference(timeframe_map)
    if unknown:
        raise ValueError(f"Unknown signal timeframes: {', '.join(sorted(unknown))}")
    if requested == ["M5"]:
        return variants
    expanded: list[freq.Variant] = []
    for variant in variants:
        for timeframe in requested:
            label, mt5_value = timeframe_map[timeframe]
            expanded.append(
                freq.Variant(
                    name=f"{variant.name}_{label}",
                    signal_mode=variant.signal_mode,
                    description=f"{variant.description} Signal timeframe={timeframe}.",
                    inputs={**variant.inputs, "InpSignalTimeframe": mt5_value},
                )
            )
    return expanded


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MT5 Forex M5 mean-reversion frequency scout.")
    parser.add_argument("--from-date", default="2024.07.01")
    parser.add_argument("--to-date", default="2026.07.02")
    parser.add_argument("--tag", default="CURRENT_2024_2026_M5_MEAN_REVERSION")
    parser.add_argument("--symbols", default="EURUSD,GBPUSD,USDJPY")
    parser.add_argument("--variants", default="")
    parser.add_argument("--signal-timeframes", default="M5")
    parser.add_argument("--direction-modes", default="both")
    parser.add_argument("--session-modes", default="all")
    parser.add_argument("--blocked-hour-sets", default="")
    parser.add_argument("--risk-rewards", default="1.00")
    parser.add_argument("--backtest-root", type=Path, default=freq.DEFAULT_BACKTEST_ROOT)
    parser.add_argument("--metaeditor", type=Path, default=freq.DEFAULT_METAEDITOR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--deposit", default="1000")
    parser.add_argument("--currency", default="USD")
    args = parser.parse_args()

    symbols = [item.strip().upper() for item in args.symbols.split(",") if item.strip()]
    variants = freq.expand_risk_rewards(
        freq.expand_blocked_hour_sets(
            freq.expand_session_modes(
                freq.expand_direction_modes(
                    expand_signal_timeframes(selected_variants(args.variants), args.signal_timeframes),
                    args.direction_modes,
                ),
                args.session_modes,
            ),
            args.blocked_hour_sets,
        ),
        args.risk_rewards,
    )
    payload = freq.run_scout(
        backtest_root=args.backtest_root,
        metaeditor=args.metaeditor,
        ea_name=EA_NAME,
        ea_source=EA_SOURCE,
        output_dir=args.output_dir,
        from_date=args.from_date,
        to_date=args.to_date,
        tag=freq.safe_name(args.tag),
        symbols=symbols,
        variants=variants,
        timeout_seconds=args.timeout_seconds,
        deposit=args.deposit,
        currency=args.currency,
        tuning_attempted=(
            bool(args.blocked_hour_sets)
            or args.session_modes.strip().lower() != "all"
            or args.direction_modes.strip().lower() != "both"
            or args.risk_rewards.strip() != "1.00"
            or args.signal_timeframes.strip().upper() != "M5"
        ),
    )
    print(
        json.dumps(
            {
                "status": payload["status"],
                "top": [
                    {
                        "symbol": row["symbol"],
                        "variant": row["variant"],
                        "status": row["status"],
                        "summary": row["summary"]["overall"],
                        "mt5_pf": row["mt5_report_metrics"].get("Profit Factor", ""),
                    }
                    for row in payload["results"][:8]
                ],
                "next_step": payload["next_step"],
                "report_md": payload["artifacts"]["report_md"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

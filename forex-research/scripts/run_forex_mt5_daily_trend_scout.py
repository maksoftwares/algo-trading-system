from __future__ import annotations

import argparse
from pathlib import Path

import run_forex_mt5_frequency_scout as freq


FOREX_ROOT = Path(__file__).resolve().parents[1]
EA_NAME = "ForexDailyTrendScout"
EA_SOURCE = FOREX_ROOT / "mt5" / "Experts" / f"{EA_NAME}.mq5"
DEFAULT_OUTPUT_DIR = FOREX_ROOT / "outputs" / "reports" / "mt5_backtests" / "daily_trend_scout"


VARIANTS = [
    freq.Variant(
        name="d1_breakout_40_atr2_trail3",
        signal_mode="0",
        description=(
            "D1 close breakout beyond the prior 40 completed daily bars, "
            "2 ATR initial stop, 3 ATR daily trailing stop, max 120 holding days, no TP."
        ),
        inputs={
            "InpLookbackDays": "40",
            "InpAtrPeriod": "14",
            "InpInitialStopAtr": "2.00",
            "InpTrailStopAtr": "3.00",
            "InpMaxHoldingDays": "120",
            "InpStopFloorPoints": "30",
            "InpStopCeilingPoints": "5000",
            "InpMaxTradesPerDay": "1",
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
        raise ValueError(f"Unknown daily-trend variants: {', '.join(sorted(missing))}")
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MT5 Forex D1 trend-following scout.")
    parser.add_argument("--from-date", default="2024.07.01")
    parser.add_argument("--to-date", default="2026.07.03")
    parser.add_argument("--tag", default="CURRENT_2024_2026_D1_TREND_SLOW_BOOK_RAW")
    parser.add_argument("--symbols", default="EURUSD,GBPUSD,USDJPY,AUDUSD,NZDUSD,USDCAD,USDCHF")
    parser.add_argument("--variants", default="")
    parser.add_argument("--direction-modes", default="both")
    parser.add_argument("--blocked-hour-sets", default="")
    parser.add_argument("--backtest-root", type=Path, default=freq.DEFAULT_BACKTEST_ROOT)
    parser.add_argument("--metaeditor", type=Path, default=freq.DEFAULT_METAEDITOR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--deposit", default="1000")
    parser.add_argument("--currency", default="USD")
    args = parser.parse_args()

    symbols = [item.strip().upper() for item in args.symbols.split(",") if item.strip()]
    variants = freq.expand_blocked_hour_sets(
        freq.expand_direction_modes(selected_variants(args.variants), args.direction_modes),
        args.blocked_hour_sets,
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
        tuning_attempted=bool(args.blocked_hour_sets) or args.direction_modes.strip().lower() != "both",
    )
    top = sorted(
        payload["results"],
        key=lambda row: (
            row["summary"]["overall"]["profit_factor"],
            row["summary"]["overall"]["trades"],
            row["summary"]["overall"]["pnl"],
        ),
        reverse=True,
    )[:8]
    print(
        freq.json.dumps(
            {
                "status": payload["status"],
                "top": [
                    {
                        "symbol": row["symbol"],
                        "variant": row["variant"],
                        "status": row["status"],
                        "summary": row["summary"]["overall"],
                        "mt5_pf": row["mt5_report_metrics"].get("Profit Factor"),
                    }
                    for row in top
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

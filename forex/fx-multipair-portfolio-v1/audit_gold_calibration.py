"""Check the deployed XAUUSD sleeve controls against current gold volatility.

Read-only. Reads the frozen V60 config and the Dukascopy archive; writes only to
this package's outputs. It changes no runtime file, no preset and no broker state.

Why: `GOLD_TRADEABILITY_TREND.md` measured gold's median daily range rising from
$11.57 (2019) to $105.15 (2026) — 9.09x — while the broker's spread stayed fixed
at $0.30.

The important distinction, and the reason a naive sweep of the config misleads:

* **Dimensionless** parameters (``target_r_default``, R-multiples) scale
  automatically with whatever stop distance is chosen. If stops are ATR-derived,
  these need no revision, and expressing them as a "% of daily range" is
  meaningless. The V60 sleeves use R-multiple targets, which is good design.
* **Absolute** parameters (USD drawdown breakers, USD per-trade risk caps, point
  deviation tolerances) do *not* scale. Each was chosen in one volatility regime
  and is now being applied in a 9x wider one, so each has silently become a much
  tighter constraint relative to normal market movement.

This quantifies the second category, which is where the real exposure is.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import src.fxdata as fx  # noqa: E402

REPO = ROOT.parents[1]
CONFIG = REPO / "xau-usd/xauusd-fast-research/v60-canonical-demo-portfolio-v2/config/v60_canonical_demo_portfolio_v2.json"
STORAGE = Path(r"D:\AlgoTradingData\C_DRIVE\DukascopyTickDataFoundationV1")
DUKAS_POINT = 0.001  # Dukascopy XAUUSD is 3-decimal; the broker quotes 2-decimal
BROKER_POINT = 0.01
ACCOUNT_EQUITY_USD = 983.0  # account 1033030, read 2026-07-26
BASELINE_YEAR = 2023


def scalars(node, path="", out=None):
    if out is None:
        out = {}
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                out[f"{path}{key}"] = value
            scalars(value, f"{path}{key}.", out)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            scalars(value, f"{path}[{index}].", out)
    return out


def gold_daily_range_usd(year: int, months=(3, 6)) -> tuple[float, float]:
    fx.INSTRUMENTS.setdefault(
        "XAUUSD",
        {"source_code": "XAU-USD", "pip_size": 0.01, "point_size": DUKAS_POINT,
         "price_scale": 3, "quote_ccy": "USD", "contract_size": 100.0},
    )
    frames = []
    for month in months:
        try:
            frames.append(fx.build_month_m5(STORAGE, "XAUUSD", year, month))
        except Exception:
            continue
    if not frames:
        return float("nan"), float("nan")
    frame = pd.concat(frames, ignore_index=True)
    timed = fx.add_time_columns(frame)
    mid = (frame["bid_close"].to_numpy() + frame["ask_close"].to_numpy()) / 2.0
    grouped = pd.DataFrame({"d": timed["date"].to_numpy(), "m": mid}).groupby("d")["m"].agg(["max", "min"])
    return float((grouped["max"] - grouped["min"]).median()), float(np.median(mid))


def main() -> int:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    values = scalars(config)

    history = {}
    for year in (2019, 2021, 2023, 2025, 2026):
        rng, price = gold_daily_range_usd(year)
        if np.isfinite(rng):
            history[year] = {"daily_range_usd": round(rng, 2), "median_price": round(price, 0)}
    latest = max(history)
    now_range = history[latest]["daily_range_usd"]
    base_range = history[BASELINE_YEAR]["daily_range_usd"]
    scale = now_range / base_range

    print("=== gold median daily range (Dukascopy, March+June) ===")
    for year, row in sorted(history.items()):
        print(f"  {year}: price ${row['median_price']:>8,.0f}   daily range ${row['daily_range_usd']:>8,.2f}")
    print(f"\n  {BASELINE_YEAR} -> {latest}: {scale:.2f}x wider")

    # ---- dimensionless controls: fine, and worth saying so ----
    r_multiples = {k: v for k, v in values.items() if "target_r" in k.lower()}
    print(f"\n=== dimensionless controls ({len(r_multiples)}) — these self-scale, no action needed ===")
    for key, value in sorted(r_multiples.items())[:4]:
        print(f"  {key} = {value}")
    if len(r_multiples) > 4:
        print(f"  ... and {len(r_multiples)-4} more, all R-multiple targets")

    # ---- absolute controls: these are the exposure ----
    absolute = {
        k: v for k, v in values.items()
        if any(t in k.lower() for t in ("usd", "deviation_points", "spread_points"))
        and not isinstance(v, bool) and 0 < v < 1_000_000
    }
    print(f"\n=== absolute controls ({len(absolute)}) — fixed in USD or points, do NOT self-scale ===")
    print(f"  {'parameter':56s} {'value':>10} {'daily ranges':>14} {'was in ' + str(BASELINE_YEAR):>14}")
    print("  " + "-" * 98)
    rows = []
    for key, value in sorted(absolute.items()):
        if "deviation_points" in key or "spread_points" in key:
            usd = value * BROKER_POINT
            unit = "pts"
        else:
            usd = value
            unit = "usd"
        now_share = usd / now_range
        then_share = usd / base_range
        rows.append({"parameter": key, "value": value, "unit": unit, "usd_equivalent": round(usd, 2),
                     "daily_ranges_now": round(now_share, 3), "daily_ranges_then": round(then_share, 3)})
        print(f"  {key:56s} {value:>10,.1f} {now_share:>14.3f} {then_share:>14.3f}")

    print(f"\n=== what this means on the live account (equity ${ACCOUNT_EQUITY_USD:,.0f}) ===")
    breakers = [r for r in rows if "drawdown" in r["parameter"] and r["unit"] == "usd"]
    for row in breakers:
        print(
            f"  {row['parameter']}: ${row['usd_equivalent']:,.0f} = "
            f"{row['daily_ranges_now']:.2f} daily ranges today vs {row['daily_ranges_then']:.2f} in {BASELINE_YEAR} "
            f"({100*row['usd_equivalent']/ACCOUNT_EQUITY_USD:.0f}% of equity)"
        )
    deviation = [r for r in rows if "deviation_points" in r["parameter"]]
    for row in deviation:
        print(
            f"  {row['parameter']}: {row['value']:,.0f} pts = ${row['usd_equivalent']:.2f} slippage tolerance, "
            f"{row['daily_ranges_now']*100:.2f}% of a daily range (was {row['daily_ranges_then']*100:.2f}%)"
        )

    report = {
        "schema_version": "xau_calibration_audit_v2",
        "access": "READ_ONLY_no_runtime_preset_or_broker_state_touched",
        "config": str(CONFIG),
        "account_equity_usd": ACCOUNT_EQUITY_USD,
        "gold_daily_range_usd_by_year": history,
        "volatility_scale_2023_to_2026": round(scale, 3),
        "dimensionless_controls_count": len(r_multiples),
        "dimensionless_note": "R-multiple targets self-scale with stop distance; no revision implied",
        "absolute_controls": rows,
        "finding": (
            f"Gold's daily range is {scale:.2f}x wider than in {BASELINE_YEAR}. Every USD drawdown breaker "
            "and point deviation tolerance in the config is a fixed number chosen under the old regime, so "
            "each is now a proportionally much tighter constraint and will bind far more often than intended."
        ),
    }
    out = ROOT / "outputs" / "XAU_CALIBRATION_AUDIT.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

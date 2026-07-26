"""R4: the Tokyo-hour short-USD hypothesis, tested once on the holdout.

The intraday census (R3) left exactly one candidate with real magnitude and a
coherent economic reading: in 01:00-02:00 UTC, EURUSD and GBPUSD rise while
USDJPY falls, i.e. the USD weakens systematically in early Tokyo. On the design
window the basket earned +8.5 points/hour and was positive in 6 of 6 years.

This traded it literally and spent the holdout on it: one pre-specified rule,
one run, result reported as-is. Enter at the 01:00 UTC M5 open, exit at the
03:00 UTC M5 open, long EURUSD + long GBPUSD + short USDJPY.

Returns are gross of any retail markup — they already pay the *raw* Dukascopy
spread (buy the ask, sell the bid), so a positive mean is the maximum extra
markup per leg the effect could absorb before dying.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.fxdata import INSTRUMENTS, add_time_columns, load_m5  # noqa: E402
from src.report import PARTITIONS, slice_window  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1")
LEGS = {"EURUSD": +1, "GBPUSD": +1, "USDJPY": -1}  # +1 long the pair == short USD
ENTRY_HOUR, EXIT_HOUR = 1, 3


def leg_points(symbol: str, side: int, start: str, end: str) -> pd.DataFrame:
    bars = slice_window(load_m5(CACHE, symbol), start, end)
    timed = add_time_columns(bars).assign(
        bid_open=bars["bid_open"], ask_open=bars["ask_open"]
    )
    point = float(INSTRUMENTS[symbol]["point_size"])
    entry = timed[(timed["hour"] == ENTRY_HOUR) & (timed["minute"] == 0)]
    exit_ = timed[(timed["hour"] == EXIT_HOUR) & (timed["minute"] == 0)]
    joined = entry[["date", "bid_open", "ask_open"]].merge(
        exit_[["date", "bid_open", "ask_open"]], on="date", suffixes=("_in", "_out")
    )
    if side > 0:  # long: pay the ask, receive the bid
        gross = (joined["bid_open_out"] - joined["ask_open_in"]) / point
    else:  # short: receive the bid, pay the ask
        gross = (joined["bid_open_in"] - joined["ask_open_out"]) / point
    return pd.DataFrame({"date": joined["date"], "gross_points": gross})


def stat(values: np.ndarray) -> dict:
    mean = float(values.mean())
    t = mean / (float(values.std(ddof=1)) / np.sqrt(values.size))
    return {
        "n": int(values.size),
        "mean_points": round(mean, 2),
        "t": round(t, 2),
        "win_pct": round(100.0 * float((values > 0).mean()), 1),
        "breakeven_extra_markup_points_per_leg": round(mean, 2),
    }


def main() -> int:
    report: dict[str, object] = {
        "schema_version": "fx_tokyo_holdout_test_v1",
        "hypothesis": "USD weakens systematically in 01:00-03:00 UTC (early Tokyo)",
        "rule": "enter 01:00 UTC M5 open, exit 03:00 UTC M5 open; long EURUSD, long GBPUSD, short USDJPY",
        "cost_basis": "raw Dukascopy spread already paid; gross of retail markup",
        "partitions": {},
    }
    for partition, (start, end) in PARTITIONS.items():
        legs = {symbol: leg_points(symbol, side, start, end) for symbol, side in LEGS.items()}
        print(f"--- {partition}  ({start} .. {end})")
        per_leg = {}
        basket = None
        for symbol, frame in legs.items():
            values = frame["gross_points"].to_numpy()
            per_leg[symbol] = stat(values)
            print(
                f"   {symbol}: n={per_leg[symbol]['n']:5d} mean={per_leg[symbol]['mean_points']:+7.2f}pt "
                f"t={per_leg[symbol]['t']:+5.2f} win%={per_leg[symbol]['win_pct']:5.1f}"
            )
            series = frame.set_index("date")["gross_points"]
            basket = series if basket is None else basket.add(series, fill_value=np.nan)
        values = basket.dropna().to_numpy()
        basket_stat = stat(values)
        print(
            f"   BASKET: n={basket_stat['n']} mean={basket_stat['mean_points']:+7.2f}pt "
            f"t={basket_stat['t']:+5.2f}\n"
        )
        report["partitions"][partition] = {
            "window": {"start": start, "end_exclusive": end},
            "per_leg": per_leg,
            "basket": basket_stat,
        }

    design = report["partitions"]["design"]["basket"]["mean_points"]
    validation = report["partitions"]["validation"]["basket"]["mean_points"]
    exam = report["partitions"]["final_exam"]["basket"]["mean_points"]
    report["verdict"] = (
        "REJECTED_SIGN_REVERSED_OUT_OF_SAMPLE"
        if (design > 0 and (validation < 0 or exam < 0))
        else "NOT_REJECTED"
    )
    print(f"verdict: {report['verdict']}")
    print(f"design {design:+.2f}pt -> validation {validation:+.2f}pt -> exam {exam:+.2f}pt")

    out = ROOT / "outputs" / "TOKYO_HOLDOUT_TEST.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

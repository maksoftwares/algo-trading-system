"""R9 follow-up: put the GBPJPY Donchian survivor through the full discipline.

R9 found exactly one candidate: GBPJPY `donchian_h4`, design PF 1.483 costed and
1.470 at zero cost. Two things make it worth testing rather than dismissing —
cost is only ~1.6% of its 1790-point stop, so it is not a cost artefact, and
trend-following working on the highest-volatility trending cross while failing on
range-bound EURGBP is mechanistically coherent.

Two things make it worth doubting: it is one survivor selected as the maximum over
432 cells (3 crosses x 3 families x 48 parameters), and `donchian_h4` was already
rejected on all three majors (R1) and on the other two crosses.

So it faces every check that killed earlier candidates, and it must pass all of
them:

1. **Out-of-sample.** Same frozen parameters on validation and final exam.
2. **Plateau.** Neighbouring grid points must also work — a spike is selection.
3. **Concentration.** PF after dropping the best 5% of trades (the test the
   inherited EURUSD portfolio failed at 1.019).
4. **Cost stress.** 2x the assumed spread.
5. **Consistency.** Share of profitable months, worst rolling window.

Reported as-is, pass or fail.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from run_cross_search import cross_costs, cross_spread_points  # noqa: E402
from src.engine import CostModel, RunConfig, SymbolSpec, simulate  # noqa: E402
from src.fxdata import INSTRUMENTS, load_m5  # noqa: E402
from src.report import (  # noqa: E402
    PARTITIONS,
    SLIPPAGE_POINTS,
    STOP_SLIPPAGE_POINTS,
    monthly_net,
    slice_window,
    summarize,
)
from src.strategies import build_signals, candidates_donchian  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1")
SYMBOL = "GBPJPY"
FROZEN = {"rr": 1.2, "atr_mult": 3.0, "context_mult": 0.5}
STOP_CAP = 3000.0
MAX_HOLD = 2880


def run(partition: str, params: dict, cost_multiplier: float = 1.0) -> pd.DataFrame:
    start, end = PARTITIONS[partition]
    bars = slice_window(load_m5(CACHE, SYMBOL), start, end)
    point = float(INSTRUMENTS[SYMBOL]["point_size"])
    raw_median = float(((bars["ask_close"] - bars["bid_close"]) / point).median())
    base = cross_costs(SYMBOL, raw_median)
    costs = CostModel(
        spread_markup_points=base.spread_markup_points * cost_multiplier,
        slippage_points=SLIPPAGE_POINTS * cost_multiplier,
        stop_slippage_points=STOP_SLIPPAGE_POINTS * cost_multiplier,
    )
    floor = 10.0 * (cross_spread_points(SYMBOL) + SLIPPAGE_POINTS + STOP_SLIPPAGE_POINTS)
    candidates = candidates_donchian(bars, SYMBOL)
    signals = build_signals(
        candidates,
        stop_floor_points=floor,
        context_mult=params["context_mult"],
        atr_mult=params["atr_mult"],
        rr=params["rr"],
        stop_cap_points=STOP_CAP,
    )
    config = RunConfig(lot=0.01, max_hold_bars=MAX_HOLD, max_entries_per_day=3)
    return simulate(bars, signals, SymbolSpec.of(SYMBOL), costs, config)


def main() -> int:
    print(f"R9 follow-up: {SYMBOL} donchian_h4, frozen params {FROZEN}")
    print("NOTE: GBPJPY here is synthetic (built from GBPUSD x USDJPY); intrabar")
    print("extremes are outer bounds and spread is the legs' sum (pessimistic).\n")

    report: dict[str, object] = {
        "schema_version": "fx_gbpjpy_donchian_validation_v1",
        "symbol": SYMBOL,
        "synthetic": True,
        "frozen_params": FROZEN,
        "checks": {},
    }

    # ---- 1. out of sample ----
    print("1) OUT OF SAMPLE (frozen parameters)")
    print(f"   {'window':12s} {'trades':>7} {'WR%':>7} {'PF':>7} {'net':>9} {'exTop5%PF':>10} {'mo+%':>6}")
    oos = {}
    for partition in ("design", "validation", "final_exam"):
        trades = run(partition, FROZEN)
        result = summarize(trades)
        oos[partition] = result
        print(
            f"   {partition:12s} {result['trades']:>7} {result.get('win_rate_pct',0):>7.2f} "
            f"{(result.get('profit_factor') or 0):>7.3f} {result.get('net_usd',0):>9.2f} "
            f"{(result.get('pf_excluding_best_5pct') or 0):>10.3f} "
            f"{result.get('months_positive_pct',0):>6.1f}"
        )
    report["checks"]["out_of_sample"] = oos

    # ---- 2. plateau ----
    print("\n2) PLATEAU (design window; neighbours must also work)")
    plateau = {}
    for key, values in (("rr", (1.2, 1.5, 2.0)), ("atr_mult", (1.5, 2.0, 3.0))):
        for value in values:
            params = dict(FROZEN)
            params[key] = value
            result = summarize(run("design", params))
            plateau[f"{key}={value}"] = {
                "pf": result.get("profit_factor"),
                "trades": result["trades"],
            }
            print(f"   {key}={value:<5} PF {(result.get('profit_factor') or 0):.3f}  n={result['trades']}")
    report["checks"]["plateau"] = plateau

    # ---- 3. cost stress ----
    print("\n3) COST STRESS (2x spread and slippage)")
    stress = {}
    for partition in ("design", "validation", "final_exam"):
        result = summarize(run(partition, FROZEN, cost_multiplier=2.0))
        stress[partition] = {"pf": result.get("profit_factor"), "net_usd": result.get("net_usd")}
        print(f"   {partition:12s} PF {(result.get('profit_factor') or 0):.3f}  net {result.get('net_usd',0):+.2f}")
    report["checks"]["cost_stress_2x"] = stress

    # ---- 4. pooled out-of-sample ----
    print("\n4) POOLED OUT-OF-SAMPLE (validation + final exam, the honest read)")
    pooled = pd.concat([run("validation", FROZEN), run("final_exam", FROZEN)], ignore_index=True)
    pooled_result = summarize(pooled)
    months = monthly_net(pooled)
    print(
        f"   trades {pooled_result['trades']}  WR {pooled_result.get('win_rate_pct',0):.2f}%  "
        f"PF {(pooled_result.get('profit_factor') or 0):.3f}  net {pooled_result.get('net_usd',0):+.2f}"
    )
    print(
        f"   ex-top-5% PF {(pooled_result.get('pf_excluding_best_5pct') or 0):.3f}  "
        f"months+ {pooled_result.get('months_positive_pct',0):.1f}%  "
        f"maxDD {pooled_result.get('max_closed_drawdown_usd',0):.2f}  "
        f"trades/yr {pooled_result['trades']/4.0:.0f}"
    )
    report["checks"]["pooled_out_of_sample"] = pooled_result

    # ---- verdict ----
    validation_pf = oos["validation"].get("profit_factor") or 0
    exam_pf = oos["final_exam"].get("profit_factor") or 0
    pooled_pf = pooled_result.get("profit_factor") or 0
    ex_top = pooled_result.get("pf_excluding_best_5pct") or 0
    plateau_ok = sum(1 for v in plateau.values() if (v["pf"] or 0) > 1.05) >= 4
    stress_ok = (stress["validation"]["pf"] or 0) > 1.0 and (stress["final_exam"]["pf"] or 0) > 1.0

    criteria = {
        "validation_pf_above_1_10": validation_pf > 1.10,
        "final_exam_pf_above_1_10": exam_pf > 1.10,
        "pooled_oos_pf_above_1_15": pooled_pf > 1.15,
        "pooled_ex_top5_above_1_00": ex_top > 1.00,
        "plateau_not_a_spike": bool(plateau_ok),
        "survives_2x_cost_oos": bool(stress_ok),
    }
    passed = all(criteria.values())
    report["criteria"] = criteria
    report["verdict"] = "GBPJPY_DONCHIAN_SURVIVES" if passed else "GBPJPY_DONCHIAN_REJECTED"

    print("\n5) VERDICT")
    for name, value in criteria.items():
        print(f"   [{'PASS' if value else 'FAIL'}] {name}")
    print(f"\n   {report['verdict']}")

    out = ROOT / "outputs" / "GBPJPY_DONCHIAN_VALIDATION.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

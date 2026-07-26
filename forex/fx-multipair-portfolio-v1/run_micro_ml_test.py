"""R11: can a nonlinear model on microstructure features clear real cost?

The last methodological gap. R7, R8 and R10 all measured features **univariately**
(single-feature deciles, or a plain z-score average). None let a model find
*interactions* — and this repo's own record for gold is that tick-microstructure
features carried most of that edge, which was an ML result rather than a decile
table.

So: gradient boosting on the full microstructure feature set, predicting the
forward 60-minute mid return, scored against measured broker cost.

Discipline, given R8/R9/R10 all produced false positives:

* **One** pre-specified model configuration. No hyperparameter search, because
  tuning is what manufactures the result.
* Trained on the design window only, evaluated on validation. The final exam is
  not touched.
* Scored the way a strategy would actually trade it: take the model's most
  confident decile, and require the realised mean move there to exceed the full
  round-trip cost.
* Reported per pair, with the design-window number alongside, so in-sample
  inflation is visible rather than hidden.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.fxdata import INSTRUMENTS, load_m5, mid  # noqa: E402
from src.report import MEASURED_ROUND_TRIP_POINTS, PARTITIONS, slice_window  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1")
SYMBOLS = ("EURUSD", "GBPUSD", "USDJPY")
HORIZON_BARS = 12  # 60 minutes of M5
DECILES = 10

FEATURES = (
    "depth_imbalance",
    "micro_dev_points",
    "quote_asym",
    "signed_flow",
    "rv_points",
    "spread_mean_points",
    "spread_max_points",
    "tick_count",
    "depth_total",
    "hour",
    "vol_trailing",
    "flow_trailing",
    "imbalance_trailing",
)

# Frozen before any result was seen. Conservative depth and strong regularisation
# because the signal-to-noise here is known to be very low.
MODEL_KWARGS = dict(
    max_depth=3,
    max_iter=300,
    learning_rate=0.05,
    min_samples_leaf=200,
    l2_regularization=1.0,
    early_stopping=False,
    random_state=0,
)


def build(symbol: str, partition: str) -> pd.DataFrame:
    bars = slice_window(load_m5(CACHE, symbol), *PARTITIONS[partition])
    micro = pd.read_parquet(CACHE / "micro" / f"{symbol}_M5_MICRO.parquet")
    frame = bars.merge(micro, on="timestamp_ms", how="inner", suffixes=("", "_micro"))
    point = float(INSTRUMENTS[symbol]["point_size"])
    close = mid(frame, "close")

    forward = np.full(close.size, np.nan)
    forward[: close.size - HORIZON_BARS] = (
        close[HORIZON_BARS:] - close[: close.size - HORIZON_BARS]
    )
    frame["target_points"] = forward / point

    stamps = pd.to_datetime(frame["timestamp_ms"], unit="ms", utc=True)
    frame["hour"] = stamps.dt.hour.to_numpy()
    # Trailing context, strictly backward-looking.
    for source, name in (
        ("rv_points", "vol_trailing"),
        ("signed_flow", "flow_trailing"),
        ("depth_imbalance", "imbalance_trailing"),
    ):
        frame[name] = pd.Series(frame[source].to_numpy()).rolling(48).mean().shift(1).to_numpy()
    return frame


def decile_stats(prediction: np.ndarray, actual: np.ndarray) -> dict:
    edges = np.quantile(prediction, np.linspace(0, 1, DECILES + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    bucket = np.clip(np.searchsorted(edges, prediction, side="right") - 1, 0, DECILES - 1)
    top, bottom = actual[bucket == DECILES - 1], actual[bucket == 0]

    def stat(values: np.ndarray) -> tuple[float, float]:
        if values.size < 30:
            return float("nan"), float("nan")
        mean = float(values.mean())
        return mean, mean / (float(values.std(ddof=1)) / np.sqrt(values.size))

    top_mean, top_t = stat(top)
    bottom_mean, bottom_t = stat(bottom)
    return {
        "top_mean_points": round(top_mean, 2),
        "top_t": round(top_t, 2),
        "bottom_mean_points": round(bottom_mean, 2),
        "bottom_t": round(bottom_t, 2),
        "best_abs_edge_points": round(max(abs(top_mean), abs(bottom_mean)), 2),
        "n_top": int(top.size),
    }


def main() -> int:
    print("R11 microstructure ML — one frozen config, design->validation, no tuning")
    print(f"features: {len(FEATURES)} | horizon 60m | model {MODEL_KWARGS}\n")
    report: dict[str, object] = {
        "schema_version": "fx_micro_ml_v1",
        "features": list(FEATURES),
        "model": {k: str(v) for k, v in MODEL_KWARGS.items()},
        "horizon_bars": HORIZON_BARS,
        "results": {},
    }

    print(
        f"{'symbol':8s} {'cost':>6} | {'DESIGN edge':>12} {'t':>7} | "
        f"{'VALID edge':>11} {'t':>7} | {'clears':>7}"
    )
    print("-" * 72)
    any_clear = False
    for symbol in SYMBOLS:
        design = build(symbol, "design")
        validation = build(symbol, "validation")
        cost = MEASURED_ROUND_TRIP_POINTS[symbol]

        columns = list(FEATURES)
        train = design.dropna(subset=[*columns, "target_points"])
        test = validation.dropna(subset=[*columns, "target_points"])
        if len(train) < 20000 or len(test) < 5000:
            print(f"{symbol:8s} insufficient rows ({len(train)}/{len(test)})")
            continue

        model = HistGradientBoostingRegressor(**MODEL_KWARGS)
        model.fit(train[columns].to_numpy(), train["target_points"].to_numpy())

        # Non-overlapping evaluation samples, matching the forward horizon.
        train_eval = train.iloc[::HORIZON_BARS]
        test_eval = test.iloc[::HORIZON_BARS]
        design_stats = decile_stats(
            model.predict(train_eval[columns].to_numpy()),
            train_eval["target_points"].to_numpy(),
        )
        valid_stats = decile_stats(
            model.predict(test_eval[columns].to_numpy()),
            test_eval["target_points"].to_numpy(),
        )
        clears = valid_stats["best_abs_edge_points"] > cost
        any_clear = any_clear or clears
        report["results"][symbol] = {
            "cost_points": cost,
            "design": design_stats,
            "validation": valid_stats,
            "train_rows": int(len(train)),
            "test_rows": int(len(test)),
            "validation_clears_cost": bool(clears),
        }
        print(
            f"{symbol:8s} {cost:>6.0f} | {design_stats['best_abs_edge_points']:>12.2f} "
            f"{design_stats['top_t']:>7.2f} | {valid_stats['best_abs_edge_points']:>11.2f} "
            f"{valid_stats['top_t']:>7.2f} | {str(clears):>7}"
        )

    report["verdict"] = (
        "R11_ML_CLEARS_COST_INVESTIGATE" if any_clear else "R11_REJECTED_ML_BELOW_COST"
    )
    print(f"\nverdict: {report['verdict']}")
    out = ROOT / "outputs" / "MICRO_ML_TEST.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

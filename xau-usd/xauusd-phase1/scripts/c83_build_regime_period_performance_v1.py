from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "outputs" / "reports"
REGIME_JSON = REPORTS / "A1_XAU_10Y_REGIME_MAP_20260709.json"
REGIME_DAYS = REPORTS / "A1_XAU_10Y_REGIME_MAP_20260709_DAYS.csv"
REGIME_SEGMENTS = REPORTS / "A1_XAU_10Y_REGIME_MAP_20260709_SEGMENTS.csv"
TRADES = REPORTS / "A3_ML_REGIME_PORTFOLIO_CONTINUOUS_10Y_20260713_TRADES.csv"
OUTPUT_STEM = "A3_ML_REGIME_PERIOD_PERFORMANCE_V1_20260716"
REGIME_ORDER = ("uptrend", "downtrend", "chop", "compression", "shock", "transition", "unknown")


def main() -> None:
    daily = pd.read_csv(REGIME_DAYS)
    daily["date"] = pd.to_datetime(daily["date"])
    trades = pd.read_csv(TRADES)
    trades["entry_dt"] = pd.to_datetime(trades["entry_time"], format="%Y.%m.%d %H:%M:%S")
    trades["exit_dt"] = pd.to_datetime(trades["exit_time"], format="%Y.%m.%d %H:%M:%S")
    trades = trades.sort_values(["entry_dt", "source"], kind="mergesort").reset_index(drop=True)

    attributed = pd.merge_asof(
        trades,
        daily[["date", "regime"]].sort_values("date"),
        left_on="entry_dt",
        right_on="date",
        direction="backward",
        allow_exact_matches=False,
    )
    if attributed["regime"].isna().any():
        raise RuntimeError("a portfolio trade lacks a prior completed D1 regime")

    regime_rows = []
    total_stress = float(attributed["stress_profit_usd"].sum())
    day_counts = daily["regime"].value_counts().to_dict()
    for regime in REGIME_ORDER:
        selected = attributed[attributed["regime"] == regime].copy()
        metrics = metrics_for(selected)
        by_source = selected.groupby("source")["stress_profit_usd"].agg(["count", "sum"])
        regime_rows.append(
            {
                "regime": regime,
                "market_days": int(day_counts.get(regime, 0)),
                "market_day_share_pct": 100.0 * int(day_counts.get(regime, 0)) / len(daily),
                **metrics,
                "share_of_total_stress_profit_pct": (
                    100.0 * metrics["stress_net_usd"] / total_stress if total_stress else 0.0
                ),
                "r1_trades": source_value(by_source, "r1_box_clean_strict_uptrend", "count"),
                "r1_stress_net_usd": source_value(by_source, "r1_box_clean_strict_uptrend", "sum"),
                "r2_trades": source_value(by_source, "r2_pullback_short_h1_confirm", "count"),
                "r2_stress_net_usd": source_value(by_source, "r2_pullback_short_h1_confirm", "sum"),
            }
        )

    regime_map = json.loads(REGIME_JSON.read_text(encoding="utf-8"))
    episode_rows = []
    for episode in regime_map["major_episodes"]:
        start = pd.Timestamp(episode["start"])
        end_exclusive = pd.Timestamp(episode["end"]) + pd.Timedelta(days=1)
        selected = attributed[
            (attributed["entry_dt"] >= start) & (attributed["entry_dt"] < end_exclusive)
        ].copy()
        episode_rows.append(
            {
                "start": episode["start"],
                "end": episode["end"],
                "episode": episode["label"],
                "dominant_regime": episode["dominant_regime"],
                "dominant_share_pct": episode["dominant_share_pct"],
                "gold_return_pct": episode["return_pct"],
                **metrics_for(selected),
            }
        )

    regime_frame = pd.DataFrame(regime_rows)
    episode_frame = pd.DataFrame(episode_rows)
    attributed_output = attributed.drop(columns=["entry_dt", "exit_dt", "date"])
    outputs = {
        "by_regime_csv": REPORTS / f"{OUTPUT_STEM}_BY_REGIME.csv",
        "episodes_csv": REPORTS / f"{OUTPUT_STEM}_EPISODES.csv",
        "attributed_trades_csv": REPORTS / f"{OUTPUT_STEM}_ATTRIBUTED_TRADES.csv",
        "report_json": REPORTS / f"{OUTPUT_STEM}.json",
        "report_markdown": REPORTS / f"{OUTPUT_STEM}.md",
    }
    regime_frame.to_csv(outputs["by_regime_csv"], index=False, lineterminator="\n")
    episode_frame.to_csv(outputs["episodes_csv"], index=False, lineterminator="\n")
    attributed_output.to_csv(outputs["attributed_trades_csv"], index=False, lineterminator="\n")
    payload: dict[str, Any] = {
        "schema_version": "a3_ml_regime_period_performance_v1",
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "methodology": {
            "market_map": "Daily D1 regime classifier from the existing 10-year regime map.",
            "trade_attribution": "Strictly prior completed D1 regime at trade entry; same-date D1 close is not used.",
            "pnl": "Exact-MT5 fixed 0.01-lot R1/R2 portfolio; stress P/L subtracts USD 0.30 per trade.",
        },
        "inputs": {
            "regime_json": artifact(REGIME_JSON),
            "regime_days": artifact(REGIME_DAYS),
            "regime_segments": artifact(REGIME_SEGMENTS),
            "portfolio_trades": artifact(TRADES),
        },
        "totals": {
            "market_days": len(daily),
            "trades": len(attributed),
            "baseline_net_usd": float(attributed["profit_usd"].sum()),
            "stress_net_usd": total_stress,
        },
        "by_regime": regime_rows,
        "major_episodes": episode_rows,
        "limitations": [
            "The D1 descriptive classifier is not identical to the EA runtime router.",
            "A trade attributed to compression or chop remains an R1 or R2 trade; it is not evidence for a separate R3/R4 specialist.",
            "Shock contains too few trades for a reliable performance conclusion.",
            "All results are historical backtest outcomes, not future P/L forecasts.",
        ],
    }
    outputs["report_markdown"].write_text(render_markdown(payload), encoding="utf-8")
    payload["artifacts"] = {
        key: artifact(path) for key, path in outputs.items() if key != "report_json"
    }
    outputs["report_json"].write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(outputs["report_markdown"])


def metrics_for(frame: pd.DataFrame) -> dict[str, Any]:
    baseline = frame["profit_usd"].to_numpy(dtype=float)
    stress = frame["stress_profit_usd"].to_numpy(dtype=float)
    wins = stress[stress > 0]
    losses = stress[stress < 0]
    equity = np.cumsum(stress)
    peaks = np.maximum.accumulate(np.r_[0.0, equity]) if len(equity) else np.asarray([0.0])
    drawdown = peaks[1:] - equity if len(equity) else np.asarray([], dtype=float)
    return {
        "trades": int(len(frame)),
        "wins": int((baseline > 0).sum()),
        "win_rate_pct": 100.0 * float((baseline > 0).mean()) if len(frame) else 0.0,
        "baseline_net_usd": float(baseline.sum()),
        "stress_net_usd": float(stress.sum()),
        "stress_profit_factor": float(wins.sum() / -losses.sum()) if len(losses) else None,
        "average_stress_usd": float(stress.mean()) if len(stress) else 0.0,
        "maximum_closed_drawdown_usd": float(drawdown.max()) if len(drawdown) else 0.0,
    }


def source_value(frame: pd.DataFrame, source: str, column: str) -> float | int:
    if source not in frame.index:
        return 0
    value = frame.loc[source, column]
    return int(value) if column == "count" else float(value)


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# XAUUSD Regime Period and Performance Report",
        "",
        "Trade attribution uses the strictly prior completed D1 regime at entry. Results are exact-MT5 historical fixed 0.01-lot outcomes, not forecasts.",
        "",
        "## Performance by Regime",
        "",
        "| Regime | Days | Share | Trades | Win rate | Stress net | Stress PF | Avg/trade | Closed DD | R1 net | R2 net |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["by_regime"]:
        lines.append(
            f"| {row['regime']} | {row['market_days']} | {row['market_day_share_pct']:.2f}% | {row['trades']} | {row['win_rate_pct']:.2f}% | ${row['stress_net_usd']:.2f} | {float(row['stress_profit_factor'] or 0):.3f} | ${row['average_stress_usd']:.2f} | ${row['maximum_closed_drawdown_usd']:.2f} | ${row['r1_stress_net_usd']:.2f} | ${row['r2_stress_net_usd']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Major Regime Episodes",
            "",
            "| Period | Episode | Dominant regime | Gold return | Trades | Stress net | Stress PF | Win rate |",
            "|---|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in payload["major_episodes"]:
        lines.append(
            f"| {row['start']} to {row['end']} | {row['episode']} | {row['dominant_regime']} | {row['gold_return_pct']:.2f}% | {row['trades']} | ${row['stress_net_usd']:.2f} | {float(row['stress_profit_factor'] or 0):.3f} | {row['win_rate_pct']:.2f}% |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Uptrend entries generated most portfolio profit. This confirms that R1 is the main historical engine.",
            "- Downtrend results were positive but substantially weaker; R2 adds coverage, not comparable profitability.",
            "- Chop, compression, and transition attribution reflects R1/R2 trades under a different D1 classifier. It does not prove separate R3/R4 edges.",
            "- Shock performance is based on too few trades to interpret.",
            "",
        ]
    )
    return "\n".join(lines)


def artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": sha256(path)}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


LANE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = LANE_ROOT.parents[2]
SRC = LANE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from backtest import assert_no_outside_regime, run_cell  # noqa: E402
from data_adapter import load_bundle  # noqa: E402
from diagnostics import market_diagnostics, summarize_results  # noqa: E402
from regime import attach_regime, classify_chop  # noqa: E402
from strategies import STRATEGY_IDS, generate_signals  # noqa: E402


TIMEFRAMES = ("M5", "M15", "M30", "H1")
START_COMMIT = "fe0777c65b78fbb9d6002935221ab404a41dbaad"
START_TREE = "7de88a01a6ddf8d1708ff7e427359469ccad8d5d"


def _clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(item) for item in value]
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return None if not np.isfinite(value) else float(value)
    if pd.isna(value):
        return None
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(_clean(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _overall_decision(matrix: pd.DataFrame) -> str:
    baseline = matrix.loc[matrix["cost_scenario"] == "BASELINE"]
    categories = set(baseline["decision_category"])
    if "PROMISING_CONFIRMATION_REQUIRED" in categories:
        return "CHOP_STRATEGY_FOUND_CONFIRMATION_REQUIRED"
    if "BORDERLINE_DO_NOT_ENGINEER" in categories:
        return "CHOP_STRATEGY_BORDERLINE_NO_ENGINEERING"
    if "UNDERPOWERED" in categories and (baseline["baseline_net_r"] > 0).any():
        return "CHOP_STRATEGY_POSITIVE_BUT_UNDERPOWERED"
    return "NO_CHOP_EDGE_FOUND"


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value):.{digits}f}"


def _timeframe_explanations(matrix: pd.DataFrame, diagnostics: pd.DataFrame) -> list[str]:
    lines = []
    baseline = matrix.loc[matrix["cost_scenario"] == "BASELINE"]
    for strategy in STRATEGY_IDS:
        pieces = []
        for timeframe in TIMEFRAMES:
            row = baseline.loc[(baseline["strategy_id"] == strategy) & (baseline["timeframe"] == timeframe)].iloc[0]
            diag = diagnostics.loc[(diagnostics["strategy_id"] == strategy) & (diagnostics["timeframe"] == timeframe)].iloc[0]
            pieces.append(
                f"{timeframe}: {int(row['accepted_trades'])} trades, expectancy {_fmt(row['baseline_expectancy'])}R, "
                f"median cost {_fmt(diag['median_cost_r'])}R, median MFE/MAE {_fmt(diag['median_mfe_r'])}/{_fmt(diag['median_mae_r'])}R, "
                f"half-life {_fmt(diag['half_life_hours'])}h, VR(4h) {_fmt(diag['variance_ratio_4h'])}."
            )
        lines.append(f"- `{strategy}` - " + " ".join(pieces))
    return lines


def _render_report(payload: dict[str, Any], matrix: pd.DataFrame, diagnostics: pd.DataFrame, episodes: pd.DataFrame) -> str:
    baseline = matrix.loc[matrix["cost_scenario"] == "BASELINE"].copy()
    best = baseline.sort_values(["baseline_expectancy", "baseline_net_r"], ascending=False).iloc[0]
    passing = baseline.loc[baseline["decision_category"] == "PROMISING_CONFIRMATION_REQUIRED"]
    defensible = None if passing.empty else passing.sort_values("baseline_expectancy", ascending=False).iloc[0]
    coverage = payload["data_coverage"]
    regime = payload["regime_summary"]
    lines = [
        f"1. Exact branch: `codex/xau-chop-fast-discovery-v1`",
        f"2. Exact starting commit and tree: `{START_COMMIT}` / `{START_TREE}`",
        "3. Exact ending commit and tree: `PENDING_SINGLE_RESEARCH_COMMIT` (reported exactly in the owner response)",
        "4. Data source: Capital.com XAUUSD processed broker Bid/Ask bars; M30 causally aggregated from M5",
        f"5. Requested and actual date range: `{coverage['requested_start']}` to `{coverage['requested_end']}` / `{coverage['actual_start']}` to `{coverage['actual_end']}`",
        "6. Cost source: actual per-bar Capital.com Bid/Ask spread; stress uses measured bar P95 spread plus 0.05R slippage",
        f"7. Overall verdict: `{payload['overall_decision']}`",
        "",
        "# XAUUSD Chop Fast Discovery V1",
        "",
        "## A. Data and implementation status",
        "",
        f"- Coverage status: `{coverage['status']}`; common years: `{coverage['common_years']:.3f}`.",
        "- Native timeframes: M5, M15, H1, H4. M30 is exact 30-minute OHLC aggregation from six complete M5 bars.",
        f"- Missing intervals: `{json.dumps(coverage['missing_intervals'], sort_keys=True)}`.",
        "- Funding: `FUNDING_NOT_INCLUDED_IN_FAST_SCREEN`; rollover-crossing trades remain counted.",
        "- Execution: completed bars, next-bar Bid/Ask entry, adverse stop-first resolution, and causal H4 labels.",
        "- All history is development/research data; no deployment claim is made.",
        "",
        "## B. Chop-regime census",
        "",
        f"- Episodes: `{regime['episode_count']}`.",
        f"- Total chop days: `{regime['total_chop_days']:.2f}`.",
        f"- History classified as chop: `{regime['coverage_pct']:.2f}%`.",
        f"- Median episode days: `{regime['median_episode_days']:.2f}`; P90: `{regime['p90_episode_days']:.2f}`.",
        f"- Volatility subtype bar distribution: `{json.dumps(regime['volatility_subtype_distribution'], sort_keys=True)}`.",
        f"- Range-width subtype bar distribution: `{json.dumps(regime['range_width_subtype_distribution'], sort_keys=True)}`.",
        f"- Drift subtype bar distribution: `{json.dumps(regime['drift_subtype_distribution'], sort_keys=True)}`.",
        f"- Yearly chop coverage: `{json.dumps(regime['yearly_chop_coverage_pct'], sort_keys=True)}`.",
        "",
        "## C. Main result matrix",
        "",
        "| Strategy | TF | Trades | Setups | Chop episodes | PF | Exp R | Net R | Stress PF | DD R | B+C R | Category |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for _, row in baseline.sort_values(["strategy_id", "timeframe"]).iterrows():
        lines.append(
            f"| {row['strategy_id']} | {row['timeframe']} | {int(row['accepted_trades'])} | {int(row['unique_setup_episodes'])} | "
            f"{int(row['chop_episodes_traded'])} | {_fmt(row['baseline_profit_factor'])} | {_fmt(row['baseline_expectancy'])} | "
            f"{_fmt(row['baseline_net_r'])} | {_fmt(row['stress_profit_factor'])} | {_fmt(row['max_closed_drawdown_r'])} | "
            f"{_fmt(row['later_net_r'])} | {row['decision_category']} |"
        )
    lines.extend([
        "",
        "## D. Best numerical cell",
        "",
        f"`{best['strategy_id']} / {best['timeframe']}` had the highest baseline expectancy at `{_fmt(best['baseline_expectancy'])}R` per trade and `{_fmt(best['baseline_net_r'])}R` net. This is a numerical ranking only.",
        "",
        "## E. Best defensible cell",
        "",
        ("No cell met the complete advancement gate." if defensible is None else f"`{defensible['strategy_id']} / {defensible['timeframe']}` met the complete advancement gate."),
        "",
        "## F. Timeframe explanation",
        "",
        *_timeframe_explanations(matrix, diagnostics),
        "",
        "## G. General chop coverage",
        "",
        "Subtype results are reported without filtering in `CHOP_SUBTYPE_RESULTS.csv`. Empty and negative buckets are retained; no subtype was removed or used to rescue a cell.",
        "",
        "## H. Concentration and fragility",
        "",
        "Year, trade, day, direction, and subtype concentration fields are retained in the matrix, yearly, subtype, signal, and trade ledgers. Advancement gates penalize top-ten-winner and single-year concentration.",
        "",
        "## I. Final decision",
        "",
        f"`{payload['overall_decision']}`",
        "",
        "## J. Next action",
        "",
    ])
    if payload["overall_decision"] == "CHOP_STRATEGY_FOUND_CONFIRMATION_REQUIRED":
        lines.append("Run one bounded confirmation task for the single preferred passing cell on newly acquired broker history; do not engineer deployment yet.")
    else:
        lines.append("No tested chop strategy earned further engineering. A future, economically different hypothesis could test passive liquidity/auction imbalance, but it is not implemented here.")
    lines.extend([
        "",
        "## Limitations",
        "",
        "- The requested July 2025-June 2026 tail is unavailable in the common Capital.com bar set.",
        "- M1/tick data was not used; ambiguous same-bar stop/target touches are conservatively stop-first.",
        "- Trustworthy swap/funding values were unavailable for this fast screen.",
        "- Boundary-return probabilities are descriptive 12-hour diagnostics and were not used as filters or tuning inputs.",
    ])
    return "\n".join(lines) + "\n"


def run(config_path: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output_dir = REPO_ROOT / config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle = load_bundle(REPO_ROOT, config)
    regime_result = classify_chop(bundle.bars["H4"], config["regime"])
    all_signals, all_trades, diagnostic_frames = [], [], []
    for timeframe in TIMEFRAMES:
        minutes = int(config["timeframes_minutes"][timeframe])
        bars = attach_regime(bundle.bars[timeframe], regime_result.bars)
        candidates = generate_signals(bars, minutes, config)
        result = run_cell(bars, candidates, timeframe, int(config["cooldown_hours"]), float(config["stress_slippage_r"]))
        assert_no_outside_regime(result.trades)
        all_signals.append(result.signals)
        all_trades.append(result.trades)
        diagnostic_frames.append(market_diagnostics(bars, timeframe, minutes, result.trades, STRATEGY_IDS))
    signals = pd.concat(all_signals, ignore_index=True).sort_values(["signal_time", "strategy_id", "timeframe", "direction"], kind="mergesort").reset_index(drop=True)
    trades = pd.concat(all_trades, ignore_index=True).sort_values(["entry_time", "strategy_id", "timeframe", "direction"], kind="mergesort").reset_index(drop=True)
    diagnostics = pd.concat(diagnostic_frames, ignore_index=True)
    matrix, subtypes, yearly, segments = summarize_results(signals, trades, STRATEGY_IDS, TIMEFRAMES, len(regime_result.episodes))
    episodes = regime_result.episodes.copy()
    signal_counts = signals.groupby("chop_episode_id").size().rename("raw_signals")
    trade_counts = trades.groupby("chop_episode_id").size().rename("accepted_trades")
    net = trades.groupby("chop_episode_id")["net_r"].sum().rename("net_r")
    episodes = episodes.merge(signal_counts, left_on="chop_episode_id", right_index=True, how="left").merge(trade_counts, left_on="chop_episode_id", right_index=True, how="left").merge(net, left_on="chop_episode_id", right_index=True, how="left")
    episodes[["raw_signals", "accepted_trades", "net_r"]] = episodes[["raw_signals", "accepted_trades", "net_r"]].fillna(0)
    active_bars = int(regime_result.bars["chop_active"].sum())
    active_regime = regime_result.bars.loc[regime_result.bars["chop_active"]].copy()
    active_regime["year"] = active_regime["timestamp_utc"].dt.year
    all_by_year = regime_result.bars.assign(year=regime_result.bars["timestamp_utc"].dt.year).groupby("year").size()
    active_by_year = active_regime.groupby("year").size()
    yearly_coverage = (100.0 * active_by_year / all_by_year).fillna(0.0)
    regime_summary = {
        "episode_count": int(len(episodes)), "active_h4_bars": active_bars,
        "total_chop_days": active_bars * 4.0 / 24.0,
        "coverage_pct": 100.0 * active_bars / len(regime_result.bars),
        "median_episode_days": float(episodes["duration_days"].median()) if len(episodes) else 0.0,
        "p90_episode_days": float(episodes["duration_days"].quantile(0.9)) if len(episodes) else 0.0,
        "volatility_subtype_distribution": active_regime["volatility_subtype"].value_counts(sort=False).sort_index().astype(int).to_dict(),
        "range_width_subtype_distribution": active_regime["range_width_subtype"].value_counts(sort=False).sort_index().astype(int).to_dict(),
        "drift_subtype_distribution": active_regime["drift_subtype"].value_counts(sort=False).sort_index().astype(int).to_dict(),
        "yearly_chop_coverage_pct": {str(int(year)): float(value) for year, value in yearly_coverage.items()},
        "data_coverage": bundle.coverage,
    }
    overall = _overall_decision(matrix)
    result_payload = {
        "schema_version": "chop_fast_discovery_result_v1", "branch": "codex/xau-chop-fast-discovery-v1",
        "starting_commit": START_COMMIT, "starting_tree": START_TREE,
        "data_source": "Capital.com XAUUSD processed Bid/Ask broker bars",
        "cost_source": "actual Bid/Ask per bar; stress P95 per bar plus 0.05R",
        "funding_status": "FUNDING_NOT_INCLUDED_IN_FAST_SCREEN", "data_coverage": bundle.coverage,
        "regime_summary": regime_summary, "overall_decision": overall,
        "matrix": matrix.loc[matrix["cost_scenario"] == "BASELINE"].to_dict(orient="records"),
        "best_numerical_cell": matrix.loc[matrix["cost_scenario"] == "BASELINE"].sort_values(["baseline_expectancy", "baseline_net_r"], ascending=False).iloc[0].to_dict(),
        "best_defensible_cells": matrix.loc[(matrix["cost_scenario"] == "BASELINE") & (matrix["decision_category"] == "PROMISING_CONFIRMATION_REQUIRED")].to_dict(orient="records"),
    }
    paths = {
        "episodes": output_dir / "CHOP_REGIME_CENSUS.csv", "summary": output_dir / "CHOP_REGIME_SUMMARY.json",
        "matrix": output_dir / "CHOP_STRATEGY_TIMEFRAME_MATRIX.csv", "diagnostics": output_dir / "CHOP_TIMEFRAME_DIAGNOSTICS.csv",
        "subtypes": output_dir / "CHOP_SUBTYPE_RESULTS.csv", "yearly": output_dir / "CHOP_YEARLY_RESULTS.csv",
        "segments": output_dir / "CHOP_CHRONOLOGICAL_SEGMENTS.csv", "signals": output_dir / "CHOP_SIGNAL_LEDGER.csv",
        "trades": output_dir / "CHOP_TRADE_LEDGER.csv", "result_json": output_dir / "CHOP_FAST_DISCOVERY_RESULT.json",
        "result_md": output_dir / "CHOP_FAST_DISCOVERY_RESULT.md",
    }
    episodes.to_csv(paths["episodes"], index=False, lineterminator="\n")
    _write_json(paths["summary"], regime_summary)
    matrix.to_csv(paths["matrix"], index=False, lineterminator="\n")
    diagnostics.to_csv(paths["diagnostics"], index=False, lineterminator="\n")
    subtypes.to_csv(paths["subtypes"], index=False, lineterminator="\n")
    yearly.to_csv(paths["yearly"], index=False, lineterminator="\n")
    segments.to_csv(paths["segments"], index=False, lineterminator="\n")
    signals.to_csv(paths["signals"], index=False, lineterminator="\n")
    trades.to_csv(paths["trades"], index=False, lineterminator="\n")
    _write_json(paths["result_json"], result_payload)
    paths["result_md"].write_text(_render_report(result_payload, matrix, diagnostics, episodes), encoding="utf-8")
    principal = {name: _sha256(path) for name, path in paths.items() if path.suffix in {".csv", ".json"}}
    return {"overall_decision": overall, "outputs": {name: str(path) for name, path in paths.items()}, "sha256": principal}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    config_path = args.config if args.config.is_absolute() else REPO_ROOT / args.config
    print(json.dumps(run(config_path), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

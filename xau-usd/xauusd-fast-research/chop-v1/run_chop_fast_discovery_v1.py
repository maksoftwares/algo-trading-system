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
from diagnostics import market_diagnostics, profit_factor, summarize_results  # noqa: E402
from regime import attach_regime, classify_chop  # noqa: E402
from strategies import STRATEGY_IDS, generate_signals  # noqa: E402


TIMEFRAMES = ("M5", "M15", "M30", "H1")
START_COMMIT = "fe0777c65b78fbb9d6002935221ab404a41dbaad"
START_TREE = "7de88a01a6ddf8d1708ff7e427359469ccad8d5d"
FOLLOWUP_BRANCH = "codex/xau-chop-m30-bounded-verification-v1"
FOLLOWUP_BASE = "2cddc16f380f531c3cf4b5922f5bd9fca8e29fff"
SELECTED_STRATEGY = "CHOP_RANGE_ROTATION_CONTINUATION_V1"
SELECTED_TIMEFRAME = "M30"


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


def _portable(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _direction_results(selected: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for direction, group in selected.groupby("direction", sort=True):
        rows.append({
            "strategy_id": SELECTED_STRATEGY, "timeframe": SELECTED_TIMEFRAME, "direction": direction,
            "trades": int(len(group)), "net_r": float(group["net_r"].sum()),
            "profit_factor": profit_factor(group["net_r"]), "expectancy_r": float(group["net_r"].mean()),
            "stress_net_r": float(group["stress_net_r"].sum()), "stress_profit_factor": profit_factor(group["stress_net_r"]),
            "wins": int((group["net_r"] > 0).sum()), "losses": int((group["net_r"] < 0).sum()),
            "median_mfe_r": float(group["mfe_r"].median()), "median_mae_r": float(group["mae_r"].median()),
        })
    return pd.DataFrame(rows)


def _gate_audit(row: pd.Series, selected: pd.DataFrame, subtypes: pd.DataFrame, yearly: pd.DataFrame, segments: pd.DataFrame) -> dict[str, Any]:
    selected_subtypes = subtypes.loc[(subtypes["strategy_id"] == SELECTED_STRATEGY) & (subtypes["timeframe"] == SELECTED_TIMEFRAME)]
    selected_years = yearly.loc[(yearly["strategy_id"] == SELECTED_STRATEGY) & (yearly["timeframe"] == SELECTED_TIMEFRAME)]
    selected_segments = segments.loc[(segments["strategy_id"] == SELECTED_STRATEGY) & (segments["timeframe"] == SELECTED_TIMEFRAME)]
    positive_years = selected_years.loc[selected_years["net_r"] > 0, "net_r"]
    year_share = float(positive_years.max() / row["baseline_net_r"]) if len(positive_years) and row["baseline_net_r"] > 0 else 0.0
    bad_subtype = bool(((selected_subtypes["trades"] >= 30) & (selected_subtypes["profit_factor"].fillna(0) < 0.85)).any())
    positive_segments = int((selected_segments["net_r"] > 0).sum())
    gates = [
        ("accepted_trades", ">=", 100, int(row["accepted_trades"]), row["accepted_trades"] >= 100),
        ("unique_setup_episodes", ">=", 60, int(row["unique_setup_episodes"]), row["unique_setup_episodes"] >= 60),
        ("chop_episodes_traded", ">=", 40, int(row["chop_episodes_traded"]), row["chop_episodes_traded"] >= 40),
        ("baseline_profit_factor", ">=", 1.20, float(row["baseline_profit_factor"]), row["baseline_profit_factor"] >= 1.20),
        ("baseline_expectancy_r", ">=", 0.08, float(row["baseline_expectancy"]), row["baseline_expectancy"] >= 0.08),
        ("later_net_r", ">", 0.0, float(row["later_net_r"]), row["later_net_r"] > 0),
        ("later_profit_factor", ">=", 1.10, float(row["later_profit_factor"]), row["later_profit_factor"] >= 1.10),
        ("positive_chronological_segments", ">=", 2, positive_segments, positive_segments >= 2),
        ("stress_net_r", ">", 0.0, float(row["stress_net_r"]), row["stress_net_r"] > 0),
        ("stress_profit_factor", ">=", 1.05, float(row["stress_profit_factor"]), row["stress_profit_factor"] >= 1.05),
        ("max_closed_drawdown_r", "<=", 20.0, float(row["max_closed_drawdown_r"]), row["max_closed_drawdown_r"] <= 20),
        ("top_ten_winner_share", "<=", 0.50, float(row["top_ten_winner_share"]), row["top_ten_winner_share"] <= 0.50),
        ("single_positive_year_share", "<=", 0.50, year_share, year_share <= 0.50),
        ("populated_subtype_below_0p85_pf", "==", False, bad_subtype, not bad_subtype),
    ]
    return {
        "strategy_id": SELECTED_STRATEGY, "timeframe": SELECTED_TIMEFRAME,
        "unchanged_gate": True, "all_strategy_gates_pass": all(item[4] for item in gates),
        "data_tail_complete": False,
        "final_advancement_allowed": False,
        "gates": [{"name": name, "operator": op, "threshold": threshold, "observed": observed, "passed": bool(passed)} for name, op, threshold, observed, passed in gates],
    }


def _execution_diagnostics(selected: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (direction, reason), group in selected.groupby(["direction", "exit_reason"], sort=True):
        rows.append({
            "direction": direction, "exit_reason": reason, "trades": int(len(group)),
            "net_r": float(group["net_r"].sum()), "average_holding_minutes": float(group["holding_minutes"].mean()),
            "median_mfe_r": float(group["mfe_r"].median()), "median_mae_r": float(group["mae_r"].median()),
            "holding_overrun_trades": int((group["holding_overrun_minutes"] > 0).sum()),
            "execution_timeframes": ",".join(sorted(set(group["execution_timeframe"].astype(str)))),
        })
    return pd.DataFrame(rows)


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
    attached_bars = {timeframe: attach_regime(bundle.bars[timeframe], regime_result.bars) for timeframe in TIMEFRAMES}
    all_signals, all_trades, diagnostic_frames = [], [], []
    for timeframe in TIMEFRAMES:
        minutes = int(config["timeframes_minutes"][timeframe])
        bars = attached_bars[timeframe]
        candidates = generate_signals(bars, minutes, config)
        execution_bars = attached_bars["M5"] if timeframe == "M30" else None
        result = run_cell(
            bars, candidates, timeframe, int(config["cooldown_hours"]),
            float(config["stress_slippage_r"]), execution_bars=execution_bars,
        )
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

    bounded_dir = output_dir / "bounded_followup_v1"
    bounded_dir.mkdir(parents=True, exist_ok=True)
    selected_signals = signals.loc[(signals["strategy_id"] == SELECTED_STRATEGY) & (signals["timeframe"] == SELECTED_TIMEFRAME)].copy()
    selected_trades = trades.loc[(trades["strategy_id"] == SELECTED_STRATEGY) & (trades["timeframe"] == SELECTED_TIMEFRAME)].copy()
    selected_row = matrix.loc[
        (matrix["strategy_id"] == SELECTED_STRATEGY) & (matrix["timeframe"] == SELECTED_TIMEFRAME)
        & (matrix["cost_scenario"] == "BASELINE")
    ].iloc[0]
    direction_results = _direction_results(selected_trades)
    gate_audit = _gate_audit(selected_row, selected_trades, subtypes, yearly, segments)
    followup_outcome = (
        "FOLLOWUP_DATA_INCOMPLETE_NO_ADVANCEMENT"
        if pd.Timestamp(bundle.coverage["actual_end"]) < pd.Timestamp(config["requested_end"])
        else ("FOLLOWUP_GATE_PASSED_CONFIRMATION_REQUIRED" if gate_audit["all_strategy_gates_pass"] else "FOLLOWUP_GATE_FAILED_NO_ADVANCEMENT")
    )
    gate_audit["data_tail_complete"] = pd.Timestamp(bundle.coverage["actual_end"]) >= pd.Timestamp(config["requested_end"])
    gate_audit["final_advancement_allowed"] = bool(gate_audit["data_tail_complete"] and gate_audit["all_strategy_gates_pass"])
    bounded_payload = {
        "schema_version": "chop_m30_bounded_verification_v1", "branch": FOLLOWUP_BRANCH,
        "base_commit": FOLLOWUP_BASE, "strategy_id": SELECTED_STRATEGY, "timeframe": SELECTED_TIMEFRAME,
        "frozen_parameters_changed": False, "ordered_execution_replay": "M5_SUBBARS",
        "data_coverage": bundle.coverage, "outcome": followup_outcome,
        "corrected_m30_result": selected_row.to_dict(), "direction_results": direction_results.to_dict(orient="records"),
        "gate_audit": gate_audit,
        "corrections": [
            "REGIME_EXIT_RECORDED_AT_EXECUTABLE_OPEN_AND_COOLDOWN_STARTS_THERE",
            "MAX_HOLD_USES_ELAPSED_UTC_TIME",
            "GAP_THROUGH_STOP_USES_WORSE_EXECUTABLE_OPEN",
            "M30_EXIT_AND_MFE_MAE_REPLAYED_ON_ORDERED_M5_SUBBARS",
            "MEAN_REVERSION_DIAGNOSTICS_ARE_EPISODE_AND_GAP_SAFE",
        ],
        "diagnostic_timing_basis": "BOUNDARY_RETURN_AND_REMAINING_REGIME_DURATION_ARE_EX_POST_ONLY",
    }
    bounded_paths = {
        "result_md": bounded_dir / "CHOP_M30_BOUNDED_VERIFICATION_RESULT.md",
        "result_json": bounded_dir / "CHOP_M30_BOUNDED_VERIFICATION_RESULT.json",
        "gate_audit": bounded_dir / "CHOP_M30_GATE_AUDIT.json",
        "direction_results": bounded_dir / "CHOP_M30_DIRECTION_RESULTS.csv",
        "execution_diagnostics": bounded_dir / "CHOP_M30_EXECUTION_DIAGNOSTICS.csv",
        "signals": bounded_dir / "CHOP_M30_SIGNAL_LEDGER.csv",
        "trades": bounded_dir / "CHOP_M30_TRADE_LEDGER.csv",
        "matrix": bounded_dir / "CHOP_FULL_MATRIX_REGRESSION.csv",
        "manifest": bounded_dir / "CHOP_BOUNDED_FOLLOWUP_MANIFEST.json",
    }
    _write_json(bounded_paths["result_json"], bounded_payload)
    _write_json(bounded_paths["gate_audit"], gate_audit)
    direction_results.to_csv(bounded_paths["direction_results"], index=False, lineterminator="\n")
    _execution_diagnostics(selected_trades).to_csv(bounded_paths["execution_diagnostics"], index=False, lineterminator="\n")
    selected_signals.to_csv(bounded_paths["signals"], index=False, lineterminator="\n")
    selected_trades.to_csv(bounded_paths["trades"], index=False, lineterminator="\n")
    matrix.to_csv(bounded_paths["matrix"], index=False, lineterminator="\n")
    report_lines = [
        "# XAUUSD M30 Bounded Verification V1", "",
        f"- Branch: `{FOLLOWUP_BRANCH}`", f"- Base commit: `{FOLLOWUP_BASE}`",
        f"- Frozen candidate: `{SELECTED_STRATEGY} / {SELECTED_TIMEFRAME}`",
        f"- Outcome: `{followup_outcome}`", "- Engineering/deployment authorization: `NOT_AUTHORIZED`", "",
        "## Corrected result", "",
        f"- Trades/setups/episodes: `{int(selected_row['accepted_trades'])}` / `{int(selected_row['unique_setup_episodes'])}` / `{int(selected_row['chop_episodes_traded'])}`.",
        f"- PF / expectancy / net R: `{_fmt(selected_row['baseline_profit_factor'])}` / `{_fmt(selected_row['baseline_expectancy'])}` / `{_fmt(selected_row['baseline_net_r'])}`.",
        f"- Stress PF / stress net R: `{_fmt(selected_row['stress_profit_factor'])}` / `{_fmt(selected_row['stress_net_r'])}`.",
        f"- Later PF / later net R: `{_fmt(selected_row['later_profit_factor'], 6)}` / `{_fmt(selected_row['later_net_r'])}`.",
        f"- Unchanged strategy gate passed: `{gate_audit['all_strategy_gates_pass']}`.", "",
        "## Data boundary", "",
        f"- Requested end: `{bundle.coverage['requested_end']}`.", f"- Common actual end: `{bundle.coverage['actual_end']}`.",
        "- No trustworthy Capital.com extension through 2026-06-30 was present locally; the mandated incomplete-data outcome therefore overrides advancement.", "",
        "## Execution corrections", "",
        "- Regime exits and cooldowns use the next executable bar open timestamp.",
        "- Maximum holds use elapsed UTC time and report unavoidable market-closure overruns.",
        "- Long/short gap-through-stop exits fill at the worse executable Bid/Ask open.",
        "- M30 stop/target ordering and MFE/MAE use causal ordered M5 sub-bars.",
        "- Half-life and variance ratios do not cross chop episodes or timestamp gaps.",
        "- Boundary-return and remaining-regime-duration fields are explicitly ex-post diagnostics and are not trading or gate inputs.", "",
        "## Final action", "", "Close chop-v1 without another rescue variant unless the owner supplies the missing frozen-period broker history under a separately authorized task.",
    ]
    bounded_paths["result_md"].write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    bounded_hashes = {name: _sha256(path) for name, path in bounded_paths.items() if name != "manifest"}
    input_manifest = {
        tf: {"path": details["source"], "sha256": details["input_sha256"], "rows": details["rows"], "start": details["start"], "end": details["end"]}
        for tf, details in bundle.coverage["timeframes"].items() if tf != "M30"
    }
    manifest = {
        "schema_version": "chop_bounded_followup_manifest_v1", "branch": FOLLOWUP_BRANCH,
        "base_commit": FOLLOWUP_BASE, "config_path": _portable(config_path), "config_sha256": _sha256(config_path),
        "inputs": input_manifest, "outputs": {name: {"path": _portable(bounded_paths[name]), "sha256": digest} for name, digest in bounded_hashes.items()},
        "replay_command": f"python {_portable(Path(__file__).resolve())} --config {_portable(config_path)}",
        "outcome": followup_outcome,
    }
    _write_json(bounded_paths["manifest"], manifest)
    principal = {name: _sha256(path) for name, path in paths.items() if path.suffix in {".csv", ".json"}}
    return {
        "overall_decision": overall, "bounded_followup_outcome": followup_outcome,
        "outputs": {name: _portable(path) for name, path in paths.items()}, "sha256": principal,
        "bounded_outputs": {name: _portable(path) for name, path in bounded_paths.items()},
        "bounded_sha256": {**bounded_hashes, "manifest": _sha256(bounded_paths["manifest"])},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    config_path = args.config if args.config.is_absolute() else REPO_ROOT / args.config
    print(json.dumps(run(config_path), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

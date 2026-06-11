"""Lane A locked full-window rerun (campaign integrity correction, 2026-06-10).

Why this script exists
----------------------
The first Lane A v1_fullhist matrix runs executed the era-rotated cell windows
from phase0.yaml (capital_com 2016-2018, pepperstone 2019-2021, dukascopy
2022-2024). The locked v1_fullhist hypotheses specify *full available offline
broker windows* (Capital.com and Dukascopy full target window through
2025-06-30; Pepperstone owner-accepted partial 2019-2021). The locked
low-frequency gate evaluator (phase0.low_frequency_gates) was also never
invoked on those results. This script runs the pre-registered test exactly as
locked. It changes no committed config, no gate threshold, and no strategy
rule. Period overrides are in-memory only.

Research-only boundary: offline Python backtests. No MT5 runtime, observer,
demo, live, preset, or broker action is authorized by this script.
"""

from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PHASE0_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PHASE0_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from phase0.config import load_project_config
from phase0.hashing import validate_hypotheses, validate_hypotheses_complete
from phase0.low_frequency_gates import evaluate_low_frequency_matrix_gates
from phase0.matrix import run_phase0_matrix
from phase0.second_ea_preflight import evaluate_second_ea_preflight

LANE_A_CANDIDATES = (
    "d1_momentum_h4_pullback_v1_fullhist",
    "w1_d1_momentum_continuation_v1_fullhist",
    "h4_inside_bar_d1_momentum_breakout_v1_fullhist",
)

LANE_B_CANDIDATES = (
    "xau_london_open_expansion_flow_v0",
    "xau_lbma_am_fix_flow_v0",
    "xau_comex_settlement_flow_v0",
)

# Wave 2 (post-campaign, owner-directed continuation): gate selection per locked
# docs/PHASE0_WAVE2_GATE_SET_V1.md - LOWFREQ set if median trades/cell < 500,
# otherwise standard absolute gates plus the carried-over G7/G8/G9B.
WAVE2_CANDIDATES = (
    "xau_ny_morning_trend_pullback_v0",
    "xau_comex_open_drive_continuation_v0",
    "xau_d1_trend_ny_window_continuation_v0",
)

# Wave 3 (macro-state conditioning) uses the same locked Wave-2 gate-set rule.
WAVE3_CANDIDATES = (
    "xau_real_yield_regime_d1_trend_v0",
    "xau_cot_managed_money_flush_v0",
)

# Wave 4 (EURUSD instrument transfer): six-cell matrix per locked
# docs/PHASE0_WAVE4_FX_GATE_ADDENDUM_V1.md (no Pepperstone FX export exists).
WAVE4_CANDIDATES = ("eur_dual_session_d1_trend_continuation_v0",)
WAVE5_CANDIDATES = ("h4_gld_etf_flow_reversal_v1_fullhist",)
WAVE6_CANDIDATES = ("xau_ny_m5_momentum_ignition_v0",)
WAVE4_SYMBOL = "EURUSD"

ALLOWED_CANDIDATES = (*LANE_A_CANDIDATES, *LANE_B_CANDIDATES, *WAVE2_CANDIDATES, *WAVE3_CANDIDATES, *WAVE4_CANDIDATES, *WAVE5_CANDIDATES, *WAVE6_CANDIDATES)
FREQUENCY_AWARE_CANDIDATES = (*WAVE2_CANDIDATES, *WAVE3_CANDIDATES, *WAVE4_CANDIDATES, *WAVE5_CANDIDATES, *WAVE6_CANDIDATES)
HIGH_FREQUENCY_MEDIAN_TRADES = 500

# Locked v1_fullhist windows: full available offline broker window, true
# holdout (2025-07-01 onward) excluded. Pepperstone keeps its owner-accepted
# partial window (DATA_WINDOW_ASYMMETRY_PRESENT).
LOCKED_PERIOD_OVERRIDES = {
    "cell_1_3_start": "2016-01-01T00:00:00Z",
    "cell_1_3_end": "2025-06-30T23:59:59Z",
    "cell_4_6_start": "2019-01-01T00:00:00Z",
    "cell_4_6_end": "2021-12-31T23:59:59Z",
    "cell_7_9_start": "2016-01-01T00:00:00Z",
    "cell_7_9_end": "2025-06-30T23:59:59Z",
}

ERA_SLICES = (
    ("2016-2018", "2016-01-01T00:00:00+00:00", "2018-12-31T23:59:59+00:00"),
    ("2019-2021", "2019-01-01T00:00:00+00:00", "2021-12-31T23:59:59+00:00"),
    ("2022-2025-06-30", "2022-01-01T00:00:00+00:00", "2025-06-30T23:59:59+00:00"),
)
MODERN_ERA = "2022-2025-06-30"

MATRIX_RESULTS = PHASE0_ROOT / "outputs" / "matrix_results"
QUARANTINE_ROOT = PHASE0_ROOT / "outputs" / "matrix_results_quarantine" / "era_rotated_run_2026_06_10"
REPORTS = PHASE0_ROOT / "outputs" / "reports"

# XAUUSD economics for realized-cost computation (config/symbols.yaml).
USD_PER_POINT_PER_LOT = 0.01 * 100.0  # point_size * contract_size_per_lot

GATE_ORDER = (
    "G1_pf_survival",
    "G2_sample_size",
    "G3_catastrophic_failure",
    "G4_low_frequency_concentration",
    "G5_activity",
    "G6_cost_sensitivity",
    "G7_cross_venue_floor",
    "G8_modern_era_integrity",
    "G9B_realized_measured_cost",
    "G10_decile_persistence",
)
# G10 deciles are a later stage by design; PENDING does not block the matrix verdict.
VERDICT_GATES = GATE_ORDER[:9]


def quarantine_era_rotated_artifacts(candidate: str) -> str:
    source = MATRIX_RESULTS / candidate
    if not source.exists():
        return "no prior artifacts"
    QUARANTINE_ROOT.mkdir(parents=True, exist_ok=True)
    target = QUARANTINE_ROOT / candidate
    if target.exists():
        return f"already quarantined at {target}"
    shutil.move(str(source), str(target))
    return f"moved to {target}"


def cell_metrics(candidate: str) -> pd.DataFrame:
    rows = []
    result_dir = MATRIX_RESULTS / candidate
    summaries = sorted(
        p for p in result_dir.glob("cell_*_" + candidate + "_*.csv")
        if not p.name.endswith("_trades.csv") and not p.name.endswith("_equity.csv")
    )
    expected_cells = 6 if candidate in WAVE4_CANDIDATES else 9
    if len(summaries) != expected_cells:
        raise RuntimeError(f"{candidate}: expected {expected_cells} cell summaries, found {len(summaries)}")
    for summary_path in summaries:
        summary = pd.read_csv(summary_path).iloc[0]
        trades_path = summary_path.with_name(summary_path.stem + "_trades.csv")
        trades = pd.read_csv(trades_path)
        r = pd.to_numeric(trades["r_multiple"], errors="coerce").dropna()
        positive = r[r > 0].sort_values(ascending=False)
        mean_abs_r = float(r.abs().mean()) if len(r) else float("nan")
        spread_cost_usd = (
            pd.to_numeric(trades["metadata_spread_points"], errors="coerce")
            * USD_PER_POINT_PER_LOT
            * pd.to_numeric(trades["lots"], errors="coerce")
        )
        slippage_usd = (
            (
                pd.to_numeric(trades["metadata_entry_slippage_price"], errors="coerce").abs()
                + pd.to_numeric(trades["metadata_exit_slippage_price"], errors="coerce").abs()
            )
            * 100.0
            * pd.to_numeric(trades["lots"], errors="coerce")
        )
        risk_usd = pd.to_numeric(trades["metadata_actual_risk_usd"], errors="coerce")
        cost_r = ((spread_cost_usd + slippage_usd) / risk_usd).dropna()
        rows.append(
            {
                "cell_id": int(summary["cell_id"]),
                "broker": summary["broker"],
                "cost_model": summary["cost_model"],
                "window_start": str(summary["time_window_start"])[:10],
                "window_end": str(summary["time_window_end"])[:10],
                "trade_count": int(summary["trade_count"]),
                "win_rate": float(summary["win_rate"]),
                "profit_factor": float(summary["profit_factor"]),
                "avg_trade_R": float(summary["avg_trade_R"]),
                "total_net_r": float(r.sum()),
                "mean_abs_r": mean_abs_r,
                "top_positive_trade_r": float(positive.iloc[0]) if len(positive) else 0.0,
                "top5_positive_sum_r": float(positive.iloc[:5].sum()) if len(positive) else 0.0,
                "max_drawdown_pct": float(summary["max_drawdown_pct"]),
                "total_return_pct": float(summary["total_return_pct"]),
                "max_consecutive_zero_trade_months": int(summary["max_consecutive_zero_trade_months"]),
                "largest_single_trade_pct_of_pnl": float(summary["largest_single_trade_pct_of_pnl"]),
                "top5_trades_pct_of_pnl": float(summary["top5_trades_pct_of_pnl"]),
                "realized_median_cost_r": float(cost_r.median()) if len(cost_r) else float("nan"),
                "realized_p95_cost_r": float(cost_r.quantile(0.95)) if len(cost_r) else float("nan"),
                "_trades_path": str(trades_path),
            }
        )
    return pd.DataFrame(rows).sort_values("cell_id").reset_index(drop=True)


def era_slice_table(metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    median_cells = metrics[metrics["cost_model"] == "median"]
    for _, cell in median_cells.iterrows():
        trades = pd.read_csv(cell["_trades_path"])
        exit_times = pd.to_datetime(trades["exit_time_utc"], utc=True, format="mixed")
        r = pd.to_numeric(trades["r_multiple"], errors="coerce")
        for era_name, era_start, era_end in ERA_SLICES:
            mask = (exit_times >= pd.Timestamp(era_start)) & (exit_times <= pd.Timestamp(era_end))
            era_r = r[mask].dropna()
            gross_win = float(era_r[era_r > 0].sum())
            gross_loss = float(-era_r[era_r < 0].sum())
            if len(era_r) == 0:
                pf = float("nan")
            elif gross_loss == 0:
                pf = float("inf")
            else:
                pf = gross_win / gross_loss
            rows.append(
                {
                    "broker": cell["broker"],
                    "cost_model": "median",
                    "era_slice": era_name,
                    "trade_count": int(len(era_r)),
                    "profit_factor": pf,
                    "total_net_r": float(era_r.sum()),
                }
            )
    return pd.DataFrame(rows)


def absolute_concentration_gate(metrics: pd.DataFrame) -> dict:
    failed = metrics.loc[
        (metrics["largest_single_trade_pct_of_pnl"] > 10.0)
        | (metrics["top5_trades_pct_of_pnl"] > 40.0)
        | (metrics["total_net_r"] <= 0),
        "cell_id",
    ].astype(str).tolist()
    return {
        "name": "G4_low_frequency_concentration",
        "status": "PASS" if not failed else "FAIL",
        "threshold": "HIGH-FREQ branch: net_R > 0; largest trade <= 10% of PnL; top-5 <= 40% of PnL",
        "observed": "all cells" if not failed else f"failed cells: {', '.join(failed)}",
        "message": "Absolute concentration caps passed (high-frequency branch)."
        if not failed
        else "One or more cells breach the absolute concentration caps or are net-negative.",
    }


def modern_era_gate(era_df: pd.DataFrame) -> dict:
    modern = era_df[(era_df["era_slice"] == MODERN_ERA) & (era_df["trade_count"] > 0)]
    passing = int((pd.to_numeric(modern["profit_factor"], errors="coerce") >= 1.10).sum())
    observed = ", ".join(
        f"{row['broker']}: PF={row['profit_factor']:.4g} (n={row['trade_count']})"
        for _, row in modern.iterrows()
    ) or "no modern-era trades"
    return {
        "name": "G8_modern_era_integrity",
        "status": "PASS" if passing >= 2 else "FAIL",
        "threshold": "median-cost 2022-2025-06-30 PF >= 1.10 in at least 2 of 3 brokers",
        "observed": f"{passing}/3 brokers ({observed})",
        "message": "Modern-era integrity passed." if passing >= 2 else "Modern era did not persist in enough brokers.",
    }


def render_report(candidate: str, metrics: pd.DataFrame, era_df: pd.DataFrame, gates: list[dict], verdict: str, quarantine_note: str) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if candidate in (*WAVE2_CANDIDATES, *WAVE3_CANDIDATES):
        title = f"# {candidate} - Locked Full-Window First Pass (Wave 2/3)"
        why_header = "## Run provenance"
        why_body = [
            "First result-producing run for this Wave-2 candidate (owner-directed continuation",
            "of the second-EA search). The hypothesis and its SHA256 lock were registered before",
            "this run; windows are the locked full per-broker windows; gate selection follows the",
            "locked PHASE0_WAVE2_GATE_SET_V1 frequency rule; true holdout stays untouched.",
        ]
    elif candidate in LANE_B_CANDIDATES:
        title = f"# {candidate} - Locked Full-Window First Pass (Lane B)"
        why_header = "## Run provenance"
        why_body = [
            "First result-producing run for this Lane B mechanism-first candidate. The hypothesis",
            "and its SHA256 lock were registered before this run; the window set and gate",
            "evaluator are identical to the corrected Lane A runs (full per-broker windows,",
            "PHASE0_LOWFREQ_GATE_SET_V1, true holdout 2025-07-01 onward untouched).",
        ]
    else:
        title = f"# {candidate} - Locked Full-Window First Pass (Rerun)"
        why_header = "## Why this rerun exists"
        why_body = [
            "The previous v1_fullhist matrix run executed era-rotated windows that did not match the",
            "locked hypothesis (`data_window: full available offline broker windows`), and the locked",
            "low-frequency gate evaluator was never invoked on it. This rerun executes the",
            "pre-registered test exactly as locked: identical mechanical rules, identical gate set,",
            "full per-broker windows, true holdout (2025-07-01 onward) untouched. The era-rotated",
            f"artifacts were preserved as audit evidence: {quarantine_note}.",
        ]
    lines = [
        title,
        "",
        f"Verdict: `{verdict}`",
        f"Generated at UTC: {generated}",
        "",
        why_header,
        "",
        *why_body,
        "",
        "DATA_WINDOW_ASYMMETRY_PRESENT: Pepperstone remains owner-accepted partial (2019-2021).",
        "",
        "## Matrix cells (9 = 3 brokers x best/median/p95 measured cost)",
        "",
        "| cell | broker | cost | window | n | WR | PF | net R | norm_top | norm_top5 | maxDD% | med cost_R |",
        "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, c in metrics.iterrows():
        denom = c["mean_abs_r"] * (c["trade_count"] ** 0.5) if c["trade_count"] else float("nan")
        norm_top = c["top_positive_trade_r"] / denom if denom else float("nan")
        norm_top5 = c["top5_positive_sum_r"] / denom if denom else float("nan")
        lines.append(
            "| {cell} | {broker} | {cost} | {ws} to {we} | {n} | {wr:.1%} | {pf:.4f} | {nr:+.1f} | {nt:.3f} | {nt5:.3f} | {dd:.2f} | {mc:.4f} |".format(
                cell=int(c["cell_id"]), broker=c["broker"], cost=c["cost_model"], ws=c["window_start"],
                we=c["window_end"], n=int(c["trade_count"]), wr=c["win_rate"], pf=c["profit_factor"],
                nr=c["total_net_r"], nt=norm_top, nt5=norm_top5, dd=c["max_drawdown_pct"],
                mc=c["realized_median_cost_r"],
            )
        )
    lines += ["", "## Era slices (median cost)", "", "| broker | era | n | PF | net R |", "| --- | --- | ---: | ---: | ---: |"]
    for _, e in era_df.iterrows():
        pf_text = "n/a" if pd.isna(e["profit_factor"]) else f"{e['profit_factor']:.4f}"
        lines.append(
            f"| {e['broker']} | {e['era_slice']} | {int(e['trade_count'])} | {pf_text} | {e['total_net_r']:+.1f} |"
        )
    lines += ["", "## Locked low-frequency gate results (PHASE0_LOWFREQ_GATE_SET_V1)", "", "| gate | status | threshold | observed |", "| --- | --- | --- | --- |"]
    for g in gates:
        lines.append(f"| {g['name']} | {g['status']} | {g['threshold']} | {g['observed']} |")
    lines += [
        "",
        "## No-tuning notice",
        "",
        "No parameter, rule, filter, window, or gate was changed in response to results.",
        "This rerun corrects the executed test to match the pre-registered design; the verdict",
        "above is final for this version under NO_TUNING_RULES.md.",
        "",
        "## Boundary",
        "",
        "Offline Phase 0 research only. No EA approval, no observer/demo/live deployment,",
        "no MT5 runtime access, no broker action. Canonical Phase 2 stays blocked;",
        "breakout_retest family stays COST_SUSPENDED_CANONICAL.",
        "",
    ]
    return "\n".join(lines)


def render_first_pass(candidate: str, metrics: pd.DataFrame, era_df: pd.DataFrame, gates: list[dict], verdict: str) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if candidate in WAVE3_CANDIDATES:
        lane = "WAVE3"
    elif candidate in WAVE2_CANDIDATES:
        lane = "WAVE2"
    elif candidate in LANE_B_CANDIDATES:
        lane = "B"
    else:
        lane = "A"
    status = "COMPLETE_REJECTED" if verdict == "FAIL_REJECTED_VERSION_FINAL" else "COMPLETE_MATRIX_GATES_PASSED"
    pf = metrics["profit_factor"]
    lines = [
        f"# First Pass: {candidate}",
        "",
        f"Status: {status}",
        f"Final verdict: {verdict}",
        f"Generated at UTC: {generated}",
        "",
        "## Boundary",
        "",
        "This was an offline Phase 0 research matrix run only (locked full-window run). It does not",
        "approve an EA, does not authorize MT5 runtime access, does not authorize broker/demo/live/",
        "observer action, and does not use true holdout data after 2025-06-30 23:59:59 UTC.",
        "",
        "DATA_WINDOW_ASYMMETRY_PRESENT: Capital.com and Dukascopy cover the full target offline",
        "window; Pepperstone remains owner-accepted partial (2019-01-02 through 2021-12-31).",
        "",
        "## Evidence",
        "",
        f"- Hypothesis: `docs/hypothesis_{candidate}.md`",
        f"- Lock: `docs/hypothesis_{candidate}.sha256.json`",
        f"- Locked-gate report: `outputs/reports/{candidate.upper()}_LOCKED_FULLHIST_FIRST_PASS.md`",
        f"- Matrix directory: `outputs/matrix_results/{candidate}`",
        "- Run integrity audit: `outputs/reports/SECOND_EA_LANE_A_RUN_INTEGRITY_AUDIT_2026_06_10.md`",
        "",
        "## Matrix Summary (locked PHASE0_LOWFREQ_GATE_SET_V1)",
        "",
        "| Check | Result |",
        "| --- | --- |",
        f"| Lane | {lane} |",
        "| 9-cell matrix completed | PASS |",
        f"| PF min / average / max | {pf.min():.4f} / {pf.mean():.4f} / {pf.max():.4f} |",
    ]
    for gate in gates:
        lines.append(f"| {gate['name']} | {gate['status']} ({gate['observed']}) |")
    lines += [
        "",
        "## No-Tuning Notice",
        "",
        "No parameter, rule, filter, window, or gate was changed in response to results.",
        f"The verdict above is final for this version under NO_TUNING_RULES.md.",
        "",
    ]
    return "\n".join(lines)


def supersede_era_rotated_first_pass(candidate: str) -> None:
    path = REPORTS / f"FIRST_PASS_{candidate}.md"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    if "locked full-window" in text.lower():
        return
    superseded = REPORTS / f"FIRST_PASS_{candidate}_SUPERSEDED_ERA_ROTATED_2026_06_10.md"
    if not superseded.exists():
        path.rename(superseded)


def main() -> int:
    args = [arg for arg in sys.argv[1:]]
    report_only = "--report-only" in args
    requested = tuple(arg for arg in args if arg != "--report-only") or LANE_A_CANDIDATES
    unknown = [name for name in requested if name not in ALLOWED_CANDIDATES]
    if unknown:
        print(f"UNKNOWN_CANDIDATES: {', '.join(unknown)}")
        return 1

    preflight = evaluate_second_ea_preflight(PHASE0_ROOT)
    if not preflight.matrix_runs_allowed:
        print(f"PREFLIGHT_BLOCKED status={preflight.status}")
        return 1

    config = load_project_config(PHASE0_ROOT)
    validate_hypotheses(config)
    validate_hypotheses_complete(config)
    config.phase0["periods"].update(LOCKED_PERIOD_OVERRIDES)

    summary_rows = []
    for candidate in requested:
        if report_only:
            quarantine_note = "report-only pass over existing locked-run artifacts"
        else:
            quarantine_note = quarantine_era_rotated_artifacts(candidate)
            print(f"[{candidate}] quarantine: {quarantine_note}")
            if candidate in WAVE4_CANDIDATES:
                import phase0.matrix as _matrix_module
                from phase0.config import build_cell_configs as _build_cells
                def _wave4_cells(cfg, symbol="XAUUSD"):
                    cells = _build_cells(cfg, symbol=WAVE4_SYMBOL)
                    return [c for c in cells if c.broker != "pepperstone"]
                _matrix_module.build_cell_configs = _wave4_cells
            outputs = run_phase0_matrix(config, candidate, allow_research_candidate=True)
            print(f"[{candidate}] matrix complete: {len(outputs)} cells")

        metrics = cell_metrics(candidate)
        era_df = era_slice_table(metrics)
        gates_config = dict(config.phase0["gates"])
        if candidate in WAVE4_CANDIDATES:
            gates_config["total_cells"] = 6
            gates_config["min_cells_pf_pass"] = 5
        gate_results = evaluate_low_frequency_matrix_gates(
            metrics.drop(columns=["_trades_path"]), gates_config
        )
        gates = [
            {"name": g.name, "status": g.status, "threshold": g.threshold, "observed": g.observed, "message": g.message}
            for g in gate_results
        ]
        g8 = modern_era_gate(era_df)
        if candidate in WAVE4_CANDIDATES:
            modern = era_df[(era_df["era_slice"] == MODERN_ERA) & (era_df["trade_count"] > 0)]
            passing_modern = int((pd.to_numeric(modern["profit_factor"], errors="coerce") >= 1.10).sum())
            g8 = {"name": "G8_modern_era_integrity", "status": "PASS" if passing_modern >= 2 else "FAIL",
                  "threshold": "WAVE4: modern-era median-cost PF >= 1.10 in BOTH brokers",
                  "observed": f"{passing_modern}/2 brokers", "message": "Wave-4 modern era check."}
            duka = metrics[metrics["broker"] == "dukascopy"]
            duka_fail = duka.loc[pd.to_numeric(duka["profit_factor"], errors="coerce") < 1.20, "cost_model"].tolist()
            g7 = {"name": "G7_cross_venue_floor", "status": "PASS" if not duka_fail else "FAIL",
                  "threshold": "WAVE4: dukascopy PF >= 1.20 in every cost model",
                  "observed": "all cost models" if not duka_fail else f"failed: {', '.join(duka_fail)}",
                  "message": "Wave-4 cross-venue floor."}
            gates = [g for g in gates if g["name"] != "G7_cross_venue_floor"]
            gates.append(g7)
        gates = [g for g in gates if g["name"] != "G8_modern_era_integrity"]
        gates.append(g8)
        median_trades = float(metrics["trade_count"].median())
        if candidate in FREQUENCY_AWARE_CANDIDATES and median_trades >= HIGH_FREQUENCY_MEDIAN_TRADES:
            # Locked PHASE0_WAVE2_GATE_SET_V1 high-frequency branch: absolute
            # concentration caps replace normalized G4 (which stays reported in
            # the cell table); all other gates are shared.
            gates = [g for g in gates if g["name"] != "G4_low_frequency_concentration"]
            gates.append(absolute_concentration_gate(metrics))
            print(f"[{candidate}] gate branch: HIGH_FREQUENCY (median trades/cell {median_trades:.0f})")
        elif candidate in FREQUENCY_AWARE_CANDIDATES:
            print(f"[{candidate}] gate branch: LOW_FREQUENCY (median trades/cell {median_trades:.0f})")
        gates.sort(key=lambda g: GATE_ORDER.index(g["name"]) if g["name"] in GATE_ORDER else 99)

        blocking = [g for g in gates if g["name"] in VERDICT_GATES and g["status"] != "PASS"]
        verdict = (
            "PASS_MATRIX_GATES_ADVANCES_TO_DECILES_AND_D2"
            if not blocking
            else "FAIL_REJECTED_VERSION_FINAL"
        )
        report = render_report(candidate, metrics, era_df, gates, verdict, quarantine_note)
        report_path = REPORTS / f"{candidate.upper()}_LOCKED_FULLHIST_FIRST_PASS.md"
        report_path.write_text(report, encoding="utf-8")
        supersede_era_rotated_first_pass(candidate)
        first_pass_path = REPORTS / f"FIRST_PASS_{candidate}.md"
        first_pass_path.write_text(
            render_first_pass(candidate, metrics, era_df, gates, verdict), encoding="utf-8"
        )
        print(f"[{candidate}] verdict: {verdict}")
        print(f"[{candidate}] report: {report_path}")
        print(f"[{candidate}] first-pass: {first_pass_path}")
        failed_names = ", ".join(g["name"] for g in blocking) or "none"
        summary_rows.append((candidate, verdict, failed_names))

    print("")
    print("=== LOCKED FULL-WINDOW RUN SUMMARY ===")
    for candidate, verdict, failed in summary_rows:
        print(f"{candidate}: {verdict} (failed gates: {failed})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

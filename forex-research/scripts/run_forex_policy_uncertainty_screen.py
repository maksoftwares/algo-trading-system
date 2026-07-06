from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import pandas as pd

import run_forex_research_lane as lane


RUN_DATE = lane.RUN_DATE
POLICY_CONTEXT_MAX_AGE_DAYS = 7.0
EPU_PROMOTION_CAVEAT = (
    "The +1 day USEPUINDXD availability lag is acceptable for rejection evidence only; "
    "any EPU watchlist/promotion attempt must be rerun with a 5-day availability lag "
    "and a revision-robustness check."
)


def policy_uncertainty_source_path(p: lane.Paths) -> Path:
    return p.repo / "xau-usd" / "xauusd-phase0" / "data" / "raw" / "policy_uncertainty" / "FRED_USEPUINDXD.csv"


def load_policy_uncertainty_context(p: lane.Paths) -> pd.DataFrame:
    path = policy_uncertainty_source_path(p)
    if not path.exists():
        raise FileNotFoundError(f"Missing policy uncertainty source file: {path}")
    frame = pd.read_csv(path)
    required = {"observation_date", "USEPUINDXD"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{path} missing required columns: {', '.join(sorted(missing))}")
    ctx = pd.DataFrame(
        {
            "observation_utc": pd.to_datetime(frame["observation_date"], utc=True, errors="coerce"),
            "policy_uncertainty": pd.to_numeric(frame["USEPUINDXD"].replace(".", pd.NA), errors="coerce"),
        }
    ).dropna()
    ctx = ctx[ctx["policy_uncertainty"] > 0].sort_values("observation_utc").reset_index(drop=True)
    ctx["policy_epu_5d_mean"] = ctx["policy_uncertainty"].rolling(5, min_periods=5).mean()
    ctx["policy_epu_20d_mean"] = ctx["policy_uncertainty"].rolling(20, min_periods=15).mean()
    ctx["policy_epu_120d_median"] = ctx["policy_uncertainty"].rolling(120, min_periods=80).median()
    ctx["policy_epu_ratio_5d_120d"] = ctx["policy_epu_5d_mean"] / ctx["policy_epu_120d_median"]
    ctx["policy_epu_change_20d"] = ctx["policy_uncertainty"] - ctx["policy_uncertainty"].shift(20)
    change_mean = ctx["policy_epu_change_20d"].rolling(252, min_periods=126).mean()
    change_std = ctx["policy_epu_change_20d"].rolling(252, min_periods=126).std()
    ctx["policy_epu_change_z252"] = (ctx["policy_epu_change_20d"] - change_mean) / change_std
    ctx["policy_available_utc"] = ctx["observation_utc"] + pd.Timedelta(days=1)
    ctx["source_file"] = lane.relative(path)
    return ctx.dropna(
        subset=[
            "policy_epu_ratio_5d_120d",
            "policy_epu_change_z252",
            "policy_available_utc",
        ]
    ).reset_index(drop=True)


def merge_policy_context(frame: pd.DataFrame, symbol: str, context: pd.DataFrame) -> pd.DataFrame:
    features = lane.with_features(frame, symbol).sort_values("bar_start_utc")
    policy = context.sort_values("policy_available_utc")
    merged = pd.merge_asof(
        features,
        policy,
        left_on="bar_start_utc",
        right_on="policy_available_utc",
        direction="backward",
    )
    merged["policy_context_age_days"] = (
        merged["bar_start_utc"] - merged["policy_available_utc"]
    ) / pd.Timedelta(days=1)
    return merged


def policy_context_summary(context: pd.DataFrame, p: lane.Paths) -> dict[str, Any]:
    return {
        "source_file": lane.relative(policy_uncertainty_source_path(p)),
        "rows": len(context),
        "start_utc": lane.iso(context["observation_utc"].min()) if len(context) else "",
        "end_utc": lane.iso(context["observation_utc"].max()) if len(context) else "",
        "available_through_utc": lane.iso(context["policy_available_utc"].max()) if len(context) else "",
        "lag_policy": "FRED USEPUINDXD daily observations are available to intraday bars only from the next UTC date.",
        "staleness_guard": f"Signals require policy_context_age_days <= {POLICY_CONTEXT_MAX_AGE_DAYS}.",
    }


def candidate_definitions(context: pd.DataFrame) -> list[lane.CandidateSpec]:
    return [
        lane.CandidateSpec(
            candidate_id="eurusd_h4_policy_uncertainty_dollar_haven_reversal_v0",
            symbol="EURUSD",
            timeframe="H4",
            family="policy-uncertainty dollar-haven reversal",
            description="EURUSD H4 failed-break reversal under lagged US policy-uncertainty stress or relief.",
            generator=lambda frame: signals_policy_reversal(frame, "EURUSD", context, "eurusd_h4_policy_uncertainty_dollar_haven_reversal_v0", timeframe="H4"),
            max_hold_bars=12,
            target_r=1.25,
        ),
        lane.CandidateSpec(
            candidate_id="usdjpy_h4_policy_uncertainty_yen_haven_reversal_v0",
            symbol="USDJPY",
            timeframe="H4",
            family="policy-uncertainty yen-haven reversal",
            description="USDJPY H4 failed-break reversal under lagged US policy-uncertainty stress or relief.",
            generator=lambda frame: signals_policy_reversal(frame, "USDJPY", context, "usdjpy_h4_policy_uncertainty_yen_haven_reversal_v0", timeframe="H4"),
            max_hold_bars=12,
            target_r=1.25,
        ),
        lane.CandidateSpec(
            candidate_id="eurusd_h1_policy_uncertainty_session_reversion_v0",
            symbol="EURUSD",
            timeframe="H1",
            family="policy-uncertainty session reversion",
            description="EURUSD H1 London/NY failed-break reversion under lagged US policy-uncertainty stress or relief.",
            generator=lambda frame: signals_policy_reversal(frame, "EURUSD", context, "eurusd_h1_policy_uncertainty_session_reversion_v0", timeframe="H1"),
            max_hold_bars=8,
            target_r=1.15,
        ),
        lane.CandidateSpec(
            candidate_id="usdjpy_h1_policy_uncertainty_session_reversion_v0",
            symbol="USDJPY",
            timeframe="H1",
            family="policy-uncertainty session reversion",
            description="USDJPY H1 London/NY failed-break reversion under lagged US policy-uncertainty stress or relief.",
            generator=lambda frame: signals_policy_reversal(frame, "USDJPY", context, "usdjpy_h1_policy_uncertainty_session_reversion_v0", timeframe="H1"),
            max_hold_bars=8,
            target_r=1.15,
        ),
    ]


def signals_policy_reversal(
    frame: pd.DataFrame,
    symbol: str,
    context: pd.DataFrame,
    candidate_id: str,
    *,
    timeframe: str,
) -> list[dict[str, Any]]:
    f = merge_policy_context(frame, symbol, context)
    signals: list[dict[str, Any]] = []
    px = lane.point_size(symbol)
    lookback = 18 if timeframe == "H4" else 24
    min_idx = max(260, lookback + 2)
    for idx in range(min_idx, len(f) - 1):
        row = f.iloc[idx]
        if not lane.available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["policy_epu_ratio_5d_120d"],
            row["policy_epu_change_z252"],
            row["policy_context_age_days"],
        ):
            continue
        if float(row["policy_context_age_days"]) > POLICY_CONTEXT_MAX_AGE_DAYS:
            continue
        if timeframe == "H1":
            hour = int(row["hour_utc"])
            if hour < 6 or hour > 16:
                continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        stress = float(row["policy_epu_ratio_5d_120d"]) >= 1.35 or float(row["policy_epu_change_z252"]) >= 0.85
        relief = float(row["policy_epu_ratio_5d_120d"]) <= 0.82 and float(row["policy_epu_change_z252"]) <= -0.45
        if not stress and not relief:
            continue
        recent = f.iloc[idx - lookback : idx]
        prior_high = float(recent["high"].max())
        prior_low = float(recent["low"].min())
        close = float(row["close"])
        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        buffer = (0.04 if timeframe == "H4" else 0.06) * atr * px
        direction = ""
        reason = ""
        if stress:
            direction = stress_direction(symbol)
            reason = "POLICY_UNCERTAINTY_STRESS_HAVEN_REJECTION"
        elif relief:
            direction = relief_direction(symbol)
            reason = "POLICY_UNCERTAINTY_RELIEF_RECLAIM"
        if direction == "SHORT":
            failed_high = high > prior_high + buffer and close < prior_high and close < open_price
            if not failed_high:
                continue
            stop = max(high, close + (0.95 if timeframe == "H4" else 0.75) * atr * px)
        else:
            failed_low = low < prior_low - buffer and close > prior_low and close > open_price
            if not failed_low:
                continue
            stop = min(low, close - (0.95 if timeframe == "H4" else 0.75) * atr * px)
        signals.append(lane.signal(candidate_id, idx, row, direction, stop, reason))
    return signals


def stress_direction(symbol: str) -> str:
    # Policy-uncertainty stress maps to USD haven pressure for EURUSD and JPY haven pressure for USDJPY.
    return "SHORT"


def relief_direction(symbol: str) -> str:
    # Policy relief maps to EURUSD relief and USDJPY carry relief.
    return "LONG"


def run_historical(
    p: lane.Paths,
    cells: list[lane.CostCell],
    context: pd.DataFrame,
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    return lane.run_specs_screen(p, cells, candidate_definitions(context))


def run_recent(
    p: lane.Paths,
    cells: list[lane.CostCell],
    context: pd.DataFrame,
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    return lane.run_recent_proxy_stress_for_specs(p, cells, candidate_definitions(context))


def final_gate(historical: dict[str, Any], recent: dict[str, Any]) -> str:
    hist_decision = str(historical.get("decision", ""))
    if hist_decision != "WATCHLIST_NEEDS_SECOND_PASS":
        return hist_decision
    trades = int(recent.get("trade_count", 0))
    if trades < 20:
        return "RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR"
    pf = float(recent.get("profit_factor", 0.0))
    expectancy = float(recent.get("net_expectancy_r", 0.0))
    if not math.isfinite(pf) or pf < 1.15 or expectancy <= 0.03:
        return "RECENT_PROXY_FAIL_WEAK_EDGE"
    if float(recent.get("top_winner_removed_net_r", 0.0)) <= 0:
        return "RECENT_PROXY_FAIL_TOP_WINNER_DEPENDENT"
    return "WATCHLIST_ONLY_NEEDS_BROKER_REFRESH"


def write_outputs(
    p: lane.Paths,
    cells: list[lane.CostCell],
    context_summary: dict[str, Any],
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    recent_rows: list[dict[str, Any]],
    recent_trade_map: dict[str, list[dict[str, Any]]],
) -> dict[str, str]:
    summary_path = p.tables / f"FOREX_POLICY_UNCERTAINTY_SCREEN_SUMMARY_{RUN_DATE}.csv"
    recent_summary_path = p.tables / f"FOREX_POLICY_UNCERTAINTY_RECENT_STRESS_SUMMARY_{RUN_DATE}.csv"
    write_summary_csv(summary_path, rows)
    write_summary_csv(recent_summary_path, recent_rows)
    write_trade_files(p.tables, trade_map, "POLICY_UNCERTAINTY")
    write_trade_files(p.tables, recent_trade_map, "POLICY_UNCERTAINTY_RECENT_STRESS")
    overall = {row["candidate_id"]: row for row in rows if row["level"] == "overall"}
    recent = {row["candidate_id"]: row for row in recent_rows}
    gates = {candidate_id: final_gate(row, recent.get(candidate_id, {})) for candidate_id, row in overall.items()}
    status_path = p.reports / f"FOREX_POLICY_UNCERTAINTY_SCREEN_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "POLICY_UNCERTAINTY_SCREEN_RESEARCH_ONLY",
                "runtime_touched": False,
                "policy_context": context_summary,
                "historical": [lane.format_summary_row(row) for row in rows],
                "recent_proxy": [lane.format_summary_row(row) for row in recent_rows],
                "final_gates": gates,
                "caveat": "Recent stress uses public Yahoo FX proxy bars plus historical Capital.com spread proxies; policy context currently ends before July 2026 and uses an explicit staleness guard.",
                "promotion_caveat": EPU_PROMOTION_CAVEAT,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_report(rows, trade_map, recent_rows, recent_trade_map, cells, context_summary, summary_path, recent_summary_path, status_path, gates)
    (p.reports / f"FOREX_POLICY_UNCERTAINTY_SCREEN_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def write_summary_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(lane.format_summary_row(row))


def write_trade_files(table_dir: Path, trade_map: dict[str, list[dict[str, Any]]], suffix: str) -> None:
    for candidate_id, trades in trade_map.items():
        path = table_dir / f"{candidate_id}_{suffix}_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)


def render_report(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    recent_rows: list[dict[str, Any]],
    recent_trade_map: dict[str, list[dict[str, Any]]],
    cells: list[lane.CostCell],
    context_summary: dict[str, Any],
    summary_path: Path,
    recent_summary_path: Path,
    status_path: Path,
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    lines = [
        "# Forex Policy-Uncertainty Screen",
        "",
        f"Generated at UTC: {generated}",
        "Status: POLICY_UNCERTAINTY_SCREEN_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Purpose: test US policy-uncertainty stress/relief as a Forex-specific dollar-haven and yen-haven regime on EURUSD/USDJPY H4 and H1 cells.",
        "",
        f"Historical summary CSV: `{lane.relative(summary_path)}`",
        f"Recent proxy summary CSV: `{lane.relative(recent_summary_path)}`",
        f"Status JSON: `{lane.relative(status_path)}`",
        "",
        "## Policy Context",
        "",
        f"- Source: `{context_summary['source_file']}`",
        f"- Rows: {context_summary['rows']}",
        f"- Observation window: {context_summary['start_utc'][:10]} through {context_summary['end_utc'][:10]}",
        f"- Lookahead-safe availability through: {context_summary['available_through_utc'][:10]}",
        f"- Lag policy: {context_summary['lag_policy']}",
        f"- Staleness guard: {context_summary['staleness_guard']}",
        f"- Promotion caveat: {EPU_PROMOTION_CAVEAT}",
        "",
        "## Cost Context",
        "",
        "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for symbol in ("EURUSD", "USDJPY"):
        for timeframe in ("H1", "H4"):
            cell = lane.best_cell(cells, symbol, timeframe)
            if cell:
                lines.append(
                    f"| {symbol} | {timeframe} | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
                )
    lines.extend(["", "## Historical Results", ""])
    append_result_table(lines, rows, gates=None)
    lines.extend(["", "## Recent Proxy Stress", ""])
    append_result_table(lines, recent_rows, gates=gates)
    lines.extend(["", "## Historical Direction And Session Split", ""])
    append_split_tables(lines, trade_map)
    lines.extend(["", "## Recent Direction And Session Split", ""])
    append_split_tables(lines, recent_trade_map)
    lines.extend(
        [
            "",
            "## Read",
            "",
            "A pass here would still be watchlist-only because local broker bars end in 2025 and recent replay uses public Yahoo FX proxy bars with historical Capital.com spread proxies. Public policy-uncertainty evidence alone cannot authorize a Forex EA.",
            "",
            f"Promotion caveat: {EPU_PROMOTION_CAVEAT}",
            "",
        ]
    )
    return "\n".join(lines)


def append_result_table(lines: list[str], rows: list[dict[str, Any]], gates: dict[str, str] | None) -> None:
    lines.append("| candidate | level | broker | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | decision | final_gate |")
    lines.append("| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |")
    for row in rows:
        gate = gates.get(row["candidate_id"], "") if gates and row["level"] in {"overall", "recent_proxy"} else ""
        lines.append(
            "| {candidate_id} | {level} | {broker} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                level=row["level"],
                broker=row["broker"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=lane.display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gate,
            )
        )


def append_split_tables(lines: list[str], trade_map: dict[str, list[dict[str, Any]]]) -> None:
    for candidate_id, trades in trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, split_trades in lane.grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in split_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {lane.mean(net):.4f} |")
        for session, split_trades in lane.grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in split_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {lane.mean(net):.4f} |")
        lines.append("")


def main() -> int:
    p = lane.paths()
    lane.ensure_dirs(p)
    cells = lane.cost_geometry_scan(p)
    context = load_policy_uncertainty_context(p)
    rows, trade_map = run_historical(p, cells, context)
    recent_rows, recent_trade_map = run_recent(p, cells, context)
    write_outputs(p, cells, policy_context_summary(context, p), rows, trade_map, recent_rows, recent_trade_map)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

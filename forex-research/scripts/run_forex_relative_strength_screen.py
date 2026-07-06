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


def candidate_definitions() -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": "eurusd_h1_fx_relative_usd_pressure_catchup_v0",
            "symbol": "EURUSD",
            "anchor_symbol": "USDJPY",
            "timeframe": "H1",
            "family": "FX relative-strength USD-pressure catch-up",
            "description": (
                "EURUSD H1 trades in the lagging direction when EURUSD and USDJPY agree on short-term "
                "USD pressure/relief and EURUSD has not yet caught up."
            ),
            "signal_fn": signals_h1_fx_relative_usd_pressure_catchup,
            "max_hold_bars": 8,
            "target_r": 1.18,
        },
        {
            "candidate_id": "usdjpy_h1_fx_relative_usd_pressure_catchup_v0",
            "symbol": "USDJPY",
            "anchor_symbol": "EURUSD",
            "timeframe": "H1",
            "family": "FX relative-strength USD-pressure catch-up",
            "description": (
                "USDJPY H1 trades in the lagging direction when EURUSD and USDJPY agree on short-term "
                "USD pressure/relief and USDJPY has not yet caught up."
            ),
            "signal_fn": signals_h1_fx_relative_usd_pressure_catchup,
            "max_hold_bars": 8,
            "target_r": 1.18,
        },
        {
            "candidate_id": "eurusd_h4_fx_relative_dispersion_reversal_v0",
            "symbol": "EURUSD",
            "anchor_symbol": "USDJPY",
            "timeframe": "H4",
            "family": "FX relative-strength dispersion reversal",
            "description": (
                "EURUSD H4 fades unusually large EURUSD-vs-USDJPY USD-direction dispersion after a "
                "reversal candle. This tests cross-pair mean reversion rather than trend following."
            ),
            "signal_fn": signals_h4_fx_relative_dispersion_reversal,
            "max_hold_bars": 10,
            "target_r": 1.20,
        },
        {
            "candidate_id": "usdjpy_h4_fx_relative_dispersion_reversal_v0",
            "symbol": "USDJPY",
            "anchor_symbol": "EURUSD",
            "timeframe": "H4",
            "family": "FX relative-strength dispersion reversal",
            "description": (
                "USDJPY H4 fades unusually large USDJPY-vs-EURUSD USD-direction dispersion after a "
                "reversal candle. This tests cross-pair mean reversion rather than trend following."
            ),
            "signal_fn": signals_h4_fx_relative_dispersion_reversal,
            "max_hold_bars": 10,
            "target_r": 1.20,
        },
    ]


def make_spec(definition: dict[str, Any], anchor_frame: pd.DataFrame) -> lane.CandidateSpec:
    signal_fn = definition["signal_fn"]
    return lane.CandidateSpec(
        candidate_id=definition["candidate_id"],
        symbol=definition["symbol"],
        timeframe=definition["timeframe"],
        family=definition["family"],
        description=definition["description"],
        generator=lambda frame: signal_fn(frame, str(definition["symbol"]), anchor_frame, str(definition["anchor_symbol"]), str(definition["candidate_id"])),
        max_hold_bars=int(definition["max_hold_bars"]),
        target_r=float(definition["target_r"]),
    )


def run_screen(p: lane.Paths, cells: list[lane.CostCell]) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    proxy = lane.cost_proxy_from_cells(cells)
    rows: list[dict[str, Any]] = []
    trade_map: dict[str, list[dict[str, Any]]] = {}
    for definition in candidate_definitions():
        all_trades: list[dict[str, Any]] = []
        for broker in ("capital_com", "dukascopy", "pepperstone"):
            frame = lane.load_bars(p.bars, broker, definition["symbol"], definition["timeframe"])
            anchor = lane.load_bars(p.bars, broker, definition["anchor_symbol"], definition["timeframe"])
            if frame.empty or anchor.empty:
                continue
            if broker != "capital_com" and (definition["symbol"], definition["timeframe"]) not in proxy:
                continue
            spec = make_spec(definition, anchor)
            signals = spec.generator(frame)
            trades = lane.simulate_trades(spec, frame, broker, signals, proxy.get((spec.symbol, spec.timeframe)))
            all_trades.extend(trades)
            rows.append(lane.summary_metrics(spec, trades, broker=broker, level="broker"))
        overall_spec = make_spec(definition, pd.DataFrame())
        deduped = lane.dedupe_trades(all_trades)
        trade_map[definition["candidate_id"]] = deduped
        rows.append(lane.summary_metrics(overall_spec, deduped, broker="all_deduped", level="overall"))
    return rows, trade_map


def run_recent_stress(p: lane.Paths, cells: list[lane.CostCell]) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    proxy = lane.cost_proxy_from_cells(cells)
    rows: list[dict[str, Any]] = []
    trade_map: dict[str, list[dict[str, Any]]] = {}
    for definition in candidate_definitions():
        frame = lane.load_recent_proxy_bars(p, definition["symbol"], definition["timeframe"])
        anchor = lane.load_recent_proxy_bars(p, definition["anchor_symbol"], definition["timeframe"])
        spec = make_spec(definition, anchor)
        if frame.empty or anchor.empty or (spec.symbol, spec.timeframe) not in proxy:
            trade_map[spec.candidate_id] = []
            rows.append(lane.summary_metrics(spec, [], broker="yahoo_recent_proxy", level="recent_proxy"))
            continue
        signals = spec.generator(frame)
        trades = lane.simulate_trades(spec, frame, "yahoo_recent_proxy", signals, proxy.get((spec.symbol, spec.timeframe)))
        trade_map[spec.candidate_id] = trades
        rows.append(lane.summary_metrics(spec, trades, broker="yahoo_recent_proxy", level="recent_proxy"))
    return rows, trade_map


def with_relative_strength(
    frame: pd.DataFrame,
    symbol: str,
    anchor_frame: pd.DataFrame,
    anchor_symbol: str,
) -> pd.DataFrame:
    primary = add_usd_return_features(lane.with_features(frame, symbol), symbol, "primary")
    if anchor_frame.empty:
        return primary
    anchor = add_usd_return_features(lane.with_features(anchor_frame, anchor_symbol), anchor_symbol, "anchor")
    keep = [
        "bar_start_utc",
        "anchor_usd_ret_3",
        "anchor_usd_ret_6",
        "anchor_usd_ret_12",
        "anchor_usd_ret_24",
    ]
    merged = pd.merge_asof(
        primary.sort_values("bar_start_utc"),
        anchor[keep].sort_values("bar_start_utc"),
        on="bar_start_utc",
        direction="backward",
        tolerance=pd.Timedelta(hours=5 if primary_timeframe_hours(primary) >= 4 else 2),
    )
    for window in (3, 6, 12, 24):
        merged[f"consensus_usd_ret_{window}"] = (
            merged[f"primary_usd_ret_{window}"] + merged[f"anchor_usd_ret_{window}"]
        ) / 2.0
    merged["lag_usd_6"] = merged["consensus_usd_ret_6"].apply(sign) * (
        merged["anchor_usd_ret_6"] - merged["primary_usd_ret_6"]
    )
    merged["dispersion_usd_12"] = merged["primary_usd_ret_12"] - merged["anchor_usd_ret_12"]
    return merged


def primary_timeframe_hours(frame: pd.DataFrame) -> float:
    if len(frame) < 3:
        return 1.0
    diffs = frame["bar_start_utc"].diff().dropna()
    if diffs.empty:
        return 1.0
    return float(diffs.median() / pd.Timedelta(hours=1))


def add_usd_return_features(frame: pd.DataFrame, symbol: str, prefix: str) -> pd.DataFrame:
    result = frame.copy()
    orientation = -1.0 if symbol == "EURUSD" else 1.0
    for window in (3, 6, 12, 24):
        result[f"{prefix}_usd_ret_{window}"] = orientation * result["close"].pct_change(window) * 100.0
    return result


def signals_h1_fx_relative_usd_pressure_catchup(
    frame: pd.DataFrame,
    symbol: str,
    anchor_frame: pd.DataFrame,
    anchor_symbol: str,
    candidate_id: str,
) -> list[dict[str, Any]]:
    f = with_relative_strength(frame, symbol, anchor_frame, anchor_symbol)
    signals: list[dict[str, Any]] = []
    px = lane.point_size(symbol)
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if not lane.available(
            row["atr14_points"],
            row["ema20"],
            row["primary_usd_ret_6"],
            row["anchor_usd_ret_6"],
            row["consensus_usd_ret_6"],
            row["consensus_usd_ret_24"],
            row["lag_usd_6"],
        ):
            continue
        hour = int(row["hour_utc"])
        if hour < 6 or hour > 16:
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        consensus_6 = float(row["consensus_usd_ret_6"])
        consensus_24 = float(row["consensus_usd_ret_24"])
        lag = float(row["lag_usd_6"])
        if abs(consensus_6) < 0.11 or abs(consensus_24) < 0.16:
            continue
        if sign(consensus_6) != sign(consensus_24) or lag < 0.045:
            continue
        direction = price_direction_for_usd_pressure(symbol, consensus_6)
        if not candle_confirms(row, direction):
            continue
        close = float(row["close"])
        ema20 = float(row["ema20"])
        if direction == "LONG":
            if float(row["low"]) > ema20 + 0.50 * atr * px:
                continue
            recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
            stop = min(recent_low, close - 0.95 * atr * px)
        else:
            if float(row["high"]) < ema20 - 0.50 * atr * px:
                continue
            recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
            stop = max(recent_high, close + 0.95 * atr * px)
        signals.append(lane.signal(candidate_id, idx, row, direction, stop, "H1_FX_RELATIVE_USD_PRESSURE_CATCHUP"))
    return signals


def signals_h4_fx_relative_dispersion_reversal(
    frame: pd.DataFrame,
    symbol: str,
    anchor_frame: pd.DataFrame,
    anchor_symbol: str,
    candidate_id: str,
) -> list[dict[str, Any]]:
    f = with_relative_strength(frame, symbol, anchor_frame, anchor_symbol)
    signals: list[dict[str, Any]] = []
    px = lane.point_size(symbol)
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if not lane.available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["primary_usd_ret_12"],
            row["anchor_usd_ret_12"],
            row["dispersion_usd_12"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        dispersion = float(row["dispersion_usd_12"])
        if abs(dispersion) < 0.28:
            continue
        primary_usd_move = float(row["primary_usd_ret_12"])
        if abs(primary_usd_move) < 0.18:
            continue
        # Reverse the pair that over-expressed the shared USD move.
        direction = price_direction_against_usd_pressure(symbol, primary_usd_move)
        if not candle_confirms(row, direction):
            continue
        close = float(row["close"])
        if direction == "LONG":
            recent_low = float(f.iloc[idx - 4 : idx + 1]["low"].min())
            stop = min(recent_low, close - 1.05 * atr * px)
        else:
            recent_high = float(f.iloc[idx - 4 : idx + 1]["high"].max())
            stop = max(recent_high, close + 1.05 * atr * px)
        signals.append(lane.signal(candidate_id, idx, row, direction, stop, "H4_FX_RELATIVE_DISPERSION_REVERSAL"))
    return signals


def sign(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def price_direction_for_usd_pressure(symbol: str, usd_pressure: float) -> str:
    if symbol == "EURUSD":
        return "SHORT" if usd_pressure > 0 else "LONG"
    return "LONG" if usd_pressure > 0 else "SHORT"


def price_direction_against_usd_pressure(symbol: str, usd_pressure: float) -> str:
    if symbol == "EURUSD":
        return "LONG" if usd_pressure > 0 else "SHORT"
    return "SHORT" if usd_pressure > 0 else "LONG"


def candle_confirms(row: pd.Series, direction: str) -> bool:
    close = float(row["close"])
    open_price = float(row["open"])
    ema20 = float(row["ema20"]) if pd.notna(row["ema20"]) else close
    body_points = float(row["body_points"]) if pd.notna(row["body_points"]) else 0.0
    atr = float(row["atr14_points"]) if pd.notna(row["atr14_points"]) else 0.0
    if atr <= 0 or body_points < 0.18 * atr:
        return False
    if direction == "LONG":
        return close > open_price and close >= ema20
    return close < open_price and close <= ema20


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
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    recent_rows: list[dict[str, Any]],
    recent_trade_map: dict[str, list[dict[str, Any]]],
) -> dict[str, str]:
    summary_path = p.tables / f"FOREX_FX_RELATIVE_STRENGTH_SCREEN_SUMMARY_{RUN_DATE}.csv"
    recent_summary_path = p.tables / f"FOREX_FX_RELATIVE_STRENGTH_RECENT_STRESS_SUMMARY_{RUN_DATE}.csv"
    write_summary_csv(summary_path, rows)
    write_summary_csv(recent_summary_path, recent_rows)
    write_trade_files(p.tables, trade_map, "FX_RELATIVE_STRENGTH")
    write_trade_files(p.tables, recent_trade_map, "FX_RELATIVE_STRENGTH_RECENT_STRESS")
    overall = {row["candidate_id"]: row for row in rows if row["level"] == "overall"}
    recent = {row["candidate_id"]: row for row in recent_rows}
    gates = {candidate_id: final_gate(row, recent.get(candidate_id, {})) for candidate_id, row in overall.items()}
    status_path = p.reports / f"FOREX_FX_RELATIVE_STRENGTH_SCREEN_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "FX_RELATIVE_STRENGTH_SCREEN_RESEARCH_ONLY",
                "runtime_touched": False,
                "historical": [lane.format_summary_row(row) for row in rows],
                "recent_proxy": [lane.format_summary_row(row) for row in recent_rows],
                "final_gates": gates,
                "caveat": "Recent stress uses public Yahoo FX proxy bars plus historical Capital.com spread proxies; it is not broker-authoritative.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_report(rows, trade_map, recent_rows, recent_trade_map, cells, summary_path, recent_summary_path, status_path, gates)
    (p.reports / f"FOREX_FX_RELATIVE_STRENGTH_SCREEN_{RUN_DATE}.md").write_text(report, encoding="utf-8")
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
    summary_path: Path,
    recent_summary_path: Path,
    status_path: Path,
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    lines = [
        "# Forex FX Relative-Strength Screen",
        "",
        f"Generated at UTC: {generated}",
        "Status: FX_RELATIVE_STRENGTH_SCREEN_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Purpose: test whether EURUSD/USDJPY cross-pair USD-pressure agreement creates a catch-up edge, or whether unusually large cross-pair dispersion mean-reverts. This is Forex-native and not a gold momentum clone.",
        "",
        f"Historical summary CSV: `{lane.relative(summary_path)}`",
        f"Recent proxy summary CSV: `{lane.relative(recent_summary_path)}`",
        f"Status JSON: `{lane.relative(status_path)}`",
        "",
        "## Method",
        "",
        "- Convert EURUSD and USDJPY moves into a common USD-pressure orientation: EURUSD down and USDJPY up both mean positive USD pressure.",
        "- H1 catch-up candidates trade only during London through NY morning when both pairs agree on 6-hour and 24-hour USD pressure and the traded pair is lagging the other pair.",
        "- H4 dispersion candidates fade a pair that over-expressed the 12-bar USD move versus the other pair after a reversal candle.",
        "- Signals are generated from completed bars and entered at the next bar open through the existing simulator.",
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
            "A pass here would still be watchlist-only because the local broker bars end in 2025 and recent replay uses public Yahoo FX proxy bars with historical Capital.com spread proxies. Any viable clue needs broker-refresh confirmation before a demo-forward spec.",
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
    rows, trade_map = run_screen(p, cells)
    recent_rows, recent_trade_map = run_recent_stress(p, cells)
    write_outputs(p, cells, rows, trade_map, recent_rows, recent_trade_map)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

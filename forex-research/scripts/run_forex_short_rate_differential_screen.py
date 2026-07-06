import csv
import json
import math
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

import run_forex_research_lane as lane


RUN_DATE = lane.RUN_DATE
SOURCE_DIR = "fred_short_rates"
EUR_CONTEXT_MAX_AGE_DAYS = 10.0
JPY_CONTEXT_MAX_AGE_DAYS = 75.0
FRED_DOWNLOAD_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
SHORT_RATE_SOURCES = {
    "fed_effective": {
        "series_id": "DFF",
        "column": "DFF",
        "filename": "FRED_DFF.csv",
        "availability_lag_days": 1,
        "description": "Federal Funds Effective Rate, daily.",
    },
    "ecb_deposit": {
        "series_id": "ECBDFR",
        "column": "ECBDFR",
        "filename": "FRED_ECBDFR.csv",
        "availability_lag_days": 1,
        "description": "ECB Deposit Facility Rate, daily.",
    },
    "japan_call": {
        "series_id": "IRSTCI01JPM156N",
        "column": "IRSTCI01JPM156N",
        "filename": "FRED_IRSTCI01JPM156N.csv",
        "availability_lag_days": 45,
        "description": "Japan immediate call money/interbank rate, monthly, conservatively lagged 45 days.",
    },
}


def source_root(p: lane.Paths) -> Path:
    return p.external / SOURCE_DIR


def source_path(p: lane.Paths, source_key: str) -> Path:
    return source_root(p) / str(SHORT_RATE_SOURCES[source_key]["filename"])


def download_fred_series(path: Path, series_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    query = urllib.parse.urlencode({"id": series_id})
    request = urllib.request.Request(
        f"{FRED_DOWNLOAD_URL}?{query}",
        headers={"User-Agent": "forex-research/1.0"},
    )
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                body = response.read().decode("utf-8")
            if series_id not in body[:500]:
                raise RuntimeError(f"FRED response for {series_id} did not include the expected series header.")
            path.write_text(body, encoding="utf-8")
            return
        except Exception as exc:
            last_error = exc
            if path.exists() and path.stat().st_size > 100:
                return
            if attempt < 2:
                time.sleep(2 + attempt * 3)
    raise RuntimeError(f"Could not download FRED series {series_id}: {last_error}") from last_error


def valid_local_source(path: Path, series_id: str) -> bool:
    if not path.exists() or path.stat().st_size <= 100:
        return False
    try:
        header = path.read_text(encoding="utf-8", errors="ignore").splitlines()[0]
    except OSError:
        return False
    return "observation_date" in header and series_id in header


def ensure_sources(p: lane.Paths) -> dict[str, str]:
    outputs: dict[str, str] = {}
    for key, spec in SHORT_RATE_SOURCES.items():
        path = source_path(p, key)
        if not valid_local_source(path, str(spec["series_id"])):
            download_fred_series(path, str(spec["series_id"]))
        outputs[key] = lane.relative(path)
    return outputs


def load_source(p: lane.Paths, source_key: str) -> pd.DataFrame:
    spec = SHORT_RATE_SOURCES[source_key]
    path = source_path(p, source_key)
    if not valid_local_source(path, str(spec["series_id"])):
        download_fred_series(path, str(spec["series_id"]))
    frame = pd.read_csv(path)
    date_col = "observation_date" if "observation_date" in frame.columns else "DATE"
    value_col = str(spec["column"])
    if date_col not in frame.columns or value_col not in frame.columns:
        raise ValueError(f"{path} missing required FRED columns {date_col}/{value_col}")
    out = pd.DataFrame(
        {
            f"{source_key}_observation_utc": pd.to_datetime(frame[date_col], utc=True, errors="coerce"),
            source_key: pd.to_numeric(frame[value_col].replace(".", pd.NA), errors="coerce"),
        }
    ).dropna()
    out = out.sort_values(f"{source_key}_observation_utc").drop_duplicates(f"{source_key}_observation_utc")
    out[f"{source_key}_available_utc"] = out[f"{source_key}_observation_utc"] + pd.Timedelta(
        days=int(spec["availability_lag_days"])
    )
    return out.reset_index(drop=True)


def load_short_rate_context(p: lane.Paths) -> pd.DataFrame:
    ensure_sources(p)
    sources = {key: load_source(p, key) for key in SHORT_RATE_SOURCES}
    start = min(frame[f"{key}_available_utc"].min() for key, frame in sources.items()).floor("D")
    end = max(frame[f"{key}_available_utc"].max() for key, frame in sources.items()).floor("D")
    context = pd.DataFrame({"available_utc": pd.date_range(start=start, end=end, freq="D", tz="UTC")})
    for key, frame in sources.items():
        context = pd.merge_asof(
            context.sort_values("available_utc"),
            frame.sort_values(f"{key}_available_utc"),
            left_on="available_utc",
            right_on=f"{key}_available_utc",
            direction="backward",
        )
        context[f"{key}_source_age_days"] = (
            context["available_utc"] - context[f"{key}_observation_utc"]
        ) / pd.Timedelta(days=1)
    context = context.dropna(subset=["fed_effective", "ecb_deposit", "japan_call"]).reset_index(drop=True)
    context["eurusd_fed_ecb_diff"] = context["fed_effective"] - context["ecb_deposit"]
    context["usdjpy_fed_japan_diff"] = context["fed_effective"] - context["japan_call"]
    for prefix in ("eurusd", "usdjpy"):
        column = f"{prefix}_fed_{'ecb' if prefix == 'eurusd' else 'japan'}_diff"
        context[f"{prefix}_diff_change_20d"] = context[column] - context[column].shift(20)
        context[f"{prefix}_diff_change_60d"] = context[column] - context[column].shift(60)
        mean_252 = context[column].rolling(252, min_periods=126).mean()
        std_252 = context[column].rolling(252, min_periods=126).std()
        context[f"{prefix}_diff_z252"] = (context[column] - mean_252) / std_252
        context[f"{prefix}_diff_ma20"] = context[column].rolling(20, min_periods=15).mean()
        context[f"{prefix}_diff_ma60"] = context[column].rolling(60, min_periods=40).mean()
    return context.dropna(
        subset=[
            "eurusd_diff_change_20d",
            "eurusd_diff_z252",
            "usdjpy_diff_change_20d",
            "usdjpy_diff_z252",
        ]
    ).reset_index(drop=True)


def merge_context(frame: pd.DataFrame, symbol: str, context: pd.DataFrame) -> pd.DataFrame:
    features = lane.with_features(frame, symbol).sort_values("bar_start_utc")
    merged = pd.merge_asof(
        features,
        context.sort_values("available_utc"),
        left_on="bar_start_utc",
        right_on="available_utc",
        direction="backward",
    )
    merged["short_rate_context_age_days"] = (
        merged["bar_start_utc"] - merged["available_utc"]
    ) / pd.Timedelta(days=1)
    return merged


def context_summary(context: pd.DataFrame, p: lane.Paths) -> dict[str, Any]:
    return {
        "source_files": {key: lane.relative(source_path(p, key)) for key in SHORT_RATE_SOURCES},
        "source_descriptions": {key: spec["description"] for key, spec in SHORT_RATE_SOURCES.items()},
        "rows": len(context),
        "available_start_utc": lane.iso(context["available_utc"].min()) if len(context) else "",
        "available_through_utc": lane.iso(context["available_utc"].max()) if len(context) else "",
        "eurusd_context_guard": f"Fed/ECB source ages must be <= {EUR_CONTEXT_MAX_AGE_DAYS} days.",
        "usdjpy_context_guard": f"Fed/Japan source ages must be <= {JPY_CONTEXT_MAX_AGE_DAYS} days.",
        "availability_policy": "Fed and ECB daily observations are shifted by one day; Japan monthly call-rate observations are shifted by 45 days.",
    }


def candidate_definitions(context: pd.DataFrame) -> list[lane.CandidateSpec]:
    return [
        lane.CandidateSpec(
            candidate_id="eurusd_h4_short_rate_diff_failed_break_reversal_v0",
            symbol="EURUSD",
            timeframe="H4",
            family="short-rate differential failed-break reversal",
            description="EURUSD H4 failed-break reversal under Fed-ECB short-rate differential pressure.",
            generator=lambda frame: signals_short_rate_reversal(
                frame,
                "EURUSD",
                "eurusd_h4_short_rate_diff_failed_break_reversal_v0",
                context,
                timeframe="H4",
            ),
            max_hold_bars=12,
            target_r=1.25,
        ),
        lane.CandidateSpec(
            candidate_id="eurusd_h1_short_rate_diff_session_reversion_v0",
            symbol="EURUSD",
            timeframe="H1",
            family="short-rate differential session reversion",
            description="EURUSD H1 London/NY failed-break reversion under Fed-ECB short-rate differential pressure.",
            generator=lambda frame: signals_short_rate_reversal(
                frame,
                "EURUSD",
                "eurusd_h1_short_rate_diff_session_reversion_v0",
                context,
                timeframe="H1",
            ),
            max_hold_bars=8,
            target_r=1.15,
        ),
        lane.CandidateSpec(
            candidate_id="usdjpy_h4_short_rate_diff_carry_pullback_v0",
            symbol="USDJPY",
            timeframe="H4",
            family="short-rate differential carry pullback",
            description="USDJPY H4 carry pullback/failed-break reversal under Fed-Japan short-rate differential pressure.",
            generator=lambda frame: signals_short_rate_reversal(
                frame,
                "USDJPY",
                "usdjpy_h4_short_rate_diff_carry_pullback_v0",
                context,
                timeframe="H4",
            ),
            max_hold_bars=12,
            target_r=1.25,
        ),
        lane.CandidateSpec(
            candidate_id="usdjpy_h1_short_rate_diff_session_carry_v0",
            symbol="USDJPY",
            timeframe="H1",
            family="short-rate differential session carry",
            description="USDJPY H1 London/NY pullback/failed-break entries under Fed-Japan short-rate differential pressure.",
            generator=lambda frame: signals_short_rate_reversal(
                frame,
                "USDJPY",
                "usdjpy_h1_short_rate_diff_session_carry_v0",
                context,
                timeframe="H1",
            ),
            max_hold_bars=8,
            target_r=1.15,
        ),
    ]


def signals_short_rate_reversal(
    frame: pd.DataFrame,
    symbol: str,
    candidate_id: str,
    context: pd.DataFrame,
    *,
    timeframe: str,
) -> list[dict[str, Any]]:
    f = merge_context(frame, symbol, context)
    signals: list[dict[str, Any]] = []
    px = lane.point_size(symbol)
    lookback = 20 if timeframe == "H4" else 24
    min_idx = max(260, lookback + 2)
    for idx in range(min_idx, len(f) - 1):
        row = f.iloc[idx]
        prefix = symbol.lower()
        diff_col = "eurusd_fed_ecb_diff" if symbol == "EURUSD" else "usdjpy_fed_japan_diff"
        if not lane.available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row[diff_col],
            row[f"{prefix}_diff_change_20d"],
            row[f"{prefix}_diff_z252"],
            row["fed_effective_source_age_days"],
        ):
            continue
        if symbol == "EURUSD":
            if (
                float(row["fed_effective_source_age_days"]) > EUR_CONTEXT_MAX_AGE_DAYS
                or float(row["ecb_deposit_source_age_days"]) > EUR_CONTEXT_MAX_AGE_DAYS
            ):
                continue
        else:
            if (
                float(row["fed_effective_source_age_days"]) > EUR_CONTEXT_MAX_AGE_DAYS
                or float(row["japan_call_source_age_days"]) > JPY_CONTEXT_MAX_AGE_DAYS
            ):
                continue
        if timeframe == "H1":
            hour = int(row["hour_utc"])
            if hour < 6 or hour > 16:
                continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        diff = float(row[diff_col])
        change20 = float(row[f"{prefix}_diff_change_20d"])
        z252 = float(row[f"{prefix}_diff_z252"])
        prior = f.iloc[idx - lookback : idx]
        prior_high = float(prior["high"].max())
        prior_low = float(prior["low"].min())
        close = float(row["close"])
        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        buffer = (0.05 if timeframe == "H4" else 0.07) * atr * px
        if symbol == "EURUSD":
            usd_pressure = change20 >= 0.18 or z252 >= 0.70
            usd_relief = change20 <= -0.18 or z252 <= -0.70
            if usd_pressure:
                if high > prior_high + buffer and close < prior_high and close < open_price:
                    stop = max(high, close + (0.80 if timeframe == "H4" else 0.65) * atr * px)
                    signals.append(
                        lane.signal(candidate_id, idx, row, "SHORT", stop, "EURUSD_FED_ECB_DIFF_USD_PRESSURE_HIGH_REJECTION")
                    )
            elif usd_relief:
                if low < prior_low - buffer and close > prior_low and close > open_price:
                    stop = min(low, close - (0.80 if timeframe == "H4" else 0.65) * atr * px)
                    signals.append(
                        lane.signal(candidate_id, idx, row, "LONG", stop, "EURUSD_FED_ECB_DIFF_RELIEF_LOW_RECLAIM")
                    )
        else:
            carry_support = (diff >= 2.0 and change20 >= -0.08) or z252 >= 0.45
            carry_compression = change20 <= -0.20 or z252 <= -0.65
            if carry_support:
                trend_ok = close >= ema50 or ema20 >= ema50
                if trend_ok and low < prior_low - buffer and close > prior_low and close > open_price:
                    stop = min(low, close - (0.80 if timeframe == "H4" else 0.65) * atr * px)
                    signals.append(
                        lane.signal(candidate_id, idx, row, "LONG", stop, "USDJPY_FED_JAPAN_DIFF_CARRY_LOW_RECLAIM")
                    )
            elif carry_compression:
                if high > prior_high + buffer and close < prior_high and close < open_price:
                    stop = max(high, close + (0.80 if timeframe == "H4" else 0.65) * atr * px)
                    signals.append(
                        lane.signal(candidate_id, idx, row, "SHORT", stop, "USDJPY_FED_JAPAN_DIFF_COMPRESSION_HIGH_REJECTION")
                    )
    return signals


def final_gate(historical: dict[str, Any], recent: dict[str, Any]) -> str:
    hist_decision = str(historical.get("decision", ""))
    if hist_decision != "WATCHLIST_NEEDS_SECOND_PASS":
        return hist_decision
    trades = int(recent.get("trade_count", 0))
    if trades < 20:
        return "RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR"
    pf = float(recent.get("profit_factor", 0.0))
    expectancy = float(recent.get("net_expectancy_r", 0.0))
    top_removed = float(recent.get("top_winner_removed_net_r", 0.0))
    if not math.isfinite(pf) or pf < 1.05 or expectancy <= 0:
        return "RECENT_PROXY_FAIL_WEAK_EDGE"
    if top_removed <= 0:
        return "RECENT_PROXY_FAIL_TOP_WINNER_DEPENDENT"
    return "SHORT_RATE_DIFF_WATCHLIST_ONLY_NEEDS_BROKER_REFRESH"


def final_gates(rows: list[dict[str, Any]], recent_rows: list[dict[str, Any]]) -> dict[str, str]:
    historical = {row["candidate_id"]: row for row in rows if row.get("level") == "overall"}
    recent = {row["candidate_id"]: row for row in recent_rows if row.get("level") == "recent_proxy"}
    return {
        candidate_id: final_gate(row, recent.get(candidate_id, {}))
        for candidate_id, row in historical.items()
    }


def write_outputs(
    p: lane.Paths,
    cells: list[lane.CostCell],
    ctx_summary: dict[str, Any],
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    recent_rows: list[dict[str, Any]],
    recent_trade_map: dict[str, list[dict[str, Any]]],
) -> None:
    gates = final_gates(rows, recent_rows)
    summary_path = p.tables / f"FOREX_SHORT_RATE_DIFFERENTIAL_SCREEN_SUMMARY_{RUN_DATE}.csv"
    recent_summary_path = p.tables / f"FOREX_SHORT_RATE_DIFFERENTIAL_RECENT_STRESS_SUMMARY_{RUN_DATE}.csv"
    write_csv(summary_path, rows)
    write_csv(recent_summary_path, recent_rows)
    for candidate_id, trades in trade_map.items():
        write_csv(p.tables / f"{candidate_id.upper()}_SHORT_RATE_DIFFERENTIAL_TRADES_{RUN_DATE}.csv", trades)
    for candidate_id, trades in recent_trade_map.items():
        write_csv(p.tables / f"{candidate_id.upper()}_SHORT_RATE_DIFFERENTIAL_RECENT_STRESS_TRADES_{RUN_DATE}.csv", trades)
    status = {
        "generated_at_utc": now_utc(),
        "status": "SHORT_RATE_DIFFERENTIAL_SCREEN_RESEARCH_ONLY",
        "runtime_touched": False,
        "short_rate_context": ctx_summary,
        "historical": [lane.format_summary_row(row) for row in rows],
        "recent_proxy": [lane.format_summary_row(row) for row in recent_rows],
        "final_gates": gates,
        "caveat": "Recent stress uses public Yahoo FX proxy bars plus historical Capital.com spread proxies; FRED short-rate context is lagged by explicit availability rules.",
    }
    status_path = p.reports / f"FOREX_SHORT_RATE_DIFFERENTIAL_SCREEN_STATUS_{RUN_DATE}.json"
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    report = render_report(
        p,
        cells,
        ctx_summary,
        rows,
        trade_map,
        recent_rows,
        recent_trade_map,
        gates,
        summary_path,
        recent_summary_path,
        status_path,
    )
    (p.reports / f"FOREX_SHORT_RATE_DIFFERENTIAL_SCREEN_{RUN_DATE}.md").write_text(report, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def render_report(
    p: lane.Paths,
    cells: list[lane.CostCell],
    ctx_summary: dict[str, Any],
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    recent_rows: list[dict[str, Any]],
    recent_trade_map: dict[str, list[dict[str, Any]]],
    gates: dict[str, str],
    summary_path: Path,
    recent_summary_path: Path,
    status_path: Path,
) -> str:
    lines = [
        "# Forex Short-Rate Differential Screen",
        "",
        f"Generated at UTC: {now_utc()}",
        "Status: SHORT_RATE_DIFFERENTIAL_SCREEN_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Purpose: test Fed-vs-ECB and Fed-vs-Japan short-rate differential pressure as a Forex-native regime on EURUSD/USDJPY H4 and H1 cells.",
        "",
        f"Historical summary CSV: `{lane.relative(summary_path)}`",
        f"Recent proxy summary CSV: `{lane.relative(recent_summary_path)}`",
        f"Status JSON: `{lane.relative(status_path)}`",
        "",
        "## Short-Rate Context",
        "",
        f"- Rows: {ctx_summary['rows']}",
        f"- Available window: {str(ctx_summary['available_start_utc'])[:10]} through {str(ctx_summary['available_through_utc'])[:10]}",
        f"- Availability policy: {ctx_summary['availability_policy']}",
        f"- EURUSD guard: {ctx_summary['eurusd_context_guard']}",
        f"- USDJPY guard: {ctx_summary['usdjpy_context_guard']}",
        "",
        "Source files:",
        "",
    ]
    for key, path in ctx_summary["source_files"].items():
        lines.append(f"- `{key}`: `{path}`")
    lines.extend(["", "## Cost Context", ""])
    append_cost_table(lines, cells)
    lines.extend(["", "## Historical Results", ""])
    append_summary_table(lines, rows, gates=None)
    lines.extend(["", "## Recent Proxy Stress", ""])
    append_summary_table(lines, recent_rows, gates=gates)
    lines.extend(["", "## Historical Direction And Session Split", ""])
    append_split_tables(lines, trade_map)
    lines.extend(["", "## Recent Direction And Session Split", ""])
    append_split_tables(lines, recent_trade_map)
    lines.extend(
        [
            "## Read",
            "",
            "A pass here would still be watchlist-only because local broker bars end in 2025 and recent replay uses public Yahoo FX proxy bars with historical Capital.com spread proxies. Short-rate differential evidence alone cannot authorize a Forex EA.",
            "",
        ]
    )
    return "\n".join(lines)


def append_cost_table(lines: list[str], cells: list[lane.CostCell]) -> None:
    lines.append("| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |")
    lines.append("| --- | --- | --- | ---: | ---: | ---: |")
    for symbol, timeframe in (("EURUSD", "H1"), ("EURUSD", "H4"), ("USDJPY", "H1"), ("USDJPY", "H4")):
        cell = lane.best_cell(cells, symbol, timeframe)
        if cell is None:
            continue
        lines.append(
            f"| {symbol} | {timeframe} | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_recent_median_points:.2f} | {cell.spread_p95_points:.2f} |"
        )


def append_summary_table(lines: list[str], rows: list[dict[str, Any]], gates: dict[str, str] | None) -> None:
    lines.append(
        "| candidate | level | broker | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | decision | final_gate |"
    )
    lines.append(
        "| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |"
    )
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
        for direction, direction_trades in lane.grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {lane.mean(net):.4f} |")
        for session, session_trades in lane.grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {lane.mean(net):.4f} |")
        lines.append("")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def main() -> int:
    p = lane.paths()
    lane.ensure_dirs(p)
    cells = lane.cost_geometry_scan(p)
    context = load_short_rate_context(p)
    rows, trade_map = lane.run_specs_screen(p, cells, candidate_definitions(context))
    recent_rows, recent_trade_map = lane.run_recent_proxy_stress_for_specs(p, cells, candidate_definitions(context))
    write_outputs(p, cells, context_summary(context, p), rows, trade_map, recent_rows, recent_trade_map)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

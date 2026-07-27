from __future__ import annotations

import configparser
import csv
import hashlib
import html
import json
import math
import re
from html.parser import HTMLParser
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[1]
REGIME = REPO / "eur-usd" / "eurusd-fast-research" / "regime-specialists-v2"
LEGACY_OUTPUT = REGIME / "outputs" / "frequency_v2_mt5"
OUTPUT = PACKAGE / "outputs"
DATA_ROOT = Path(r"D:\AlgoTradingData")
FX_CACHE = DATA_ROOT / "research" / "fx-multipair-portfolio-v1"

M15_REPORT = LEGACY_OUTPUT / "M15_TREND_OVERLAY_REPORT.htm"
CONTROL_REPORT = LEGACY_OUTPUT / "CHOP_CONTROL_REPORT.htm"
M15_SOURCE = REPO / "forex-research" / "mt5" / "Experts" / "ForexMeanReversionScout.mq5"
M15_EX5 = REGIME / "mt5" / "Experts" / "ForexMeanReversionScout.ex5"
CONTROL_SOURCE = REGIME / "mt5" / "Experts" / "EurUsdV4AsiaLondonCompressionShort.mq5"
CONTROL_EX5 = REGIME / "mt5" / "Experts" / "EurUsdV4AsiaLondonCompressionShort.ex5"
M15_INI = REGIME / "mt5" / "Config" / "EURUSD_FREQUENCY_V2_M15_TREND_OVERLAY_202407_202607.ini"
CONTROL_INI = REGIME / "mt5" / "Config" / "EURUSD_CAPV2_CHOP_ORDERING_TESTER_202407_202606.ini"
M15_PRESET = REGIME / "mt5" / "Presets" / "EURUSD_FREQUENCY_V2_M15_SHADOW_DEMO.set"
CONTROL_PRESET = REGIME / "mt5" / "Presets" / "EURUSD_V4_SHADOW_DEMO.set"
M15_COMPILE_LOG = REGIME / "mt5" / "frequency_v2_m15_compile.log"
CONTROL_COMPILE_LOG = REGIME / "mt5" / "compile.log"
MISSING_BROKER_SOURCE = Path(
    r"C:\MT5A1M5MomentumBacktest\Tester\Agent-127.0.0.1-3000"
    r"\MQL5\Files\EURUSD_M15_CAPITAL_BROKER_201607_202607.csv"
)

DECLARED_ACTIVE_BROKER_DATES = 615
ACCOUNT_BALANCE_USD = 10_000.0
PIP_VALUE_USD_PER_LOT = 10.0
RNG_SEED = 20260727


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def profit_factor(values: np.ndarray) -> float:
    gross_profit = float(values[values > 0].sum())
    gross_loss = float(-values[values < 0].sum())
    if gross_loss == 0:
        return 0.0 if gross_profit == 0 else math.inf
    return gross_profit / gross_loss


def max_drawdown(values: np.ndarray) -> float:
    if len(values) == 0:
        return 0.0
    equity = np.cumsum(values)
    peaks = np.maximum.accumulate(np.insert(equity, 0, 0.0))[1:]
    return float(np.max(peaks - equity))


def top_removed_profit_factor(values: np.ndarray, fraction: float = 0.05) -> float:
    if len(values) == 0:
        return 0.0
    count = max(1, int(math.ceil(len(values) * fraction)))
    kept = np.delete(values, np.argsort(values)[-count:])
    return profit_factor(kept)


class _HtmlRows(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() == "tr":
            self._row = []
        elif tag.casefold() == "td" and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "td" and self._row is not None and self._cell is not None:
            value = html.unescape("".join(self._cell))
            self._row.append(re.sub(r"\s+", " ", value).strip())
            self._cell = None
        elif tag.casefold() == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None
            self._cell = None


def read_mt5_trades(path: Path, sleeve: str, direction: str) -> pd.DataFrame:
    parser = _HtmlRows()
    parser.feed(path.read_text(encoding="utf-16"))
    header_index = next(
        (
            index
            for index, row in enumerate(parser.rows)
            if "Deal" in row and "Direction" in row and "Commission" in row
        ),
        None,
    )
    if header_index is None:
        raise RuntimeError(f"Cannot locate MT5 deals table in {path}")
    columns = [
        "time",
        "deal",
        "symbol",
        "type",
        "direction",
        "volume",
        "price",
        "order",
        "commission",
        "swap",
        "profit",
        "balance",
        "comment",
    ]
    rows = [
        row
        for row in parser.rows[header_index + 1 :]
        if len(row) == len(columns)
        and row[2] == "EURUSD"
        and re.fullmatch(r"\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}", row[0])
    ]
    deals = pd.DataFrame(rows, columns=columns)
    deals = deals[deals["symbol"].eq("EURUSD")].copy()
    deals["time"] = pd.to_datetime(
        deals["time"], format="%Y.%m.%d %H:%M:%S", utc=True
    )
    for field in ("volume", "price", "commission", "swap", "profit"):
        deals[field] = pd.to_numeric(deals[field])
    entries = deals[deals["direction"].eq("in")].reset_index(drop=True)
    exits = deals[deals["direction"].eq("out")].reset_index(drop=True)
    if len(entries) != len(exits):
        raise RuntimeError(f"Unpaired MT5 deals in {path}")
    trades = pd.DataFrame(
        {
            "entry_time": entries["time"],
            "exit_time": exits["time"],
            "sleeve": sleeve,
            "trade_direction": direction,
            "volume": entries["volume"],
            "entry_price": entries["price"],
            "exit_price": exits["price"],
            "commission": exits["commission"],
            "swap": exits["swap"],
            "profit": exits["profit"],
            "net_pnl_usd": exits["commission"] + exits["swap"] + exits["profit"],
            "exit_comment": exits["comment"],
        }
    )
    # FIFO pairing is safe for these two standalone reports only if their own
    # positions never overlap. This does not prove same-account portfolio parity.
    if len(trades) > 1 and (
        trades["entry_time"].iloc[1:].reset_index(drop=True)
        < trades["exit_time"].iloc[:-1].reset_index(drop=True)
    ).any():
        raise RuntimeError(f"Standalone report contains overlapping positions: {path}")
    return trades


def ledger_metrics(frame: pd.DataFrame, values: np.ndarray | None = None) -> dict:
    if values is None:
        values = frame["net_pnl_usd"].to_numpy(dtype=float)
    else:
        values = np.asarray(values, dtype=float)
    wins = int((values > 0).sum())
    metric_frame = frame.assign(
        _metric_value=values,
        day=frame["exit_time"].dt.strftime("%Y-%m-%d"),
        month=frame["exit_time"].dt.strftime("%Y-%m"),
    )
    days = metric_frame.groupby("day")["_metric_value"].sum()
    months = metric_frame.groupby("month")["_metric_value"].sum()
    return {
        "trades": int(len(values)),
        "wins": wins,
        "win_rate": float(wins / len(values)) if len(values) else 0.0,
        "net_pnl_usd": float(values.sum()),
        "average_trade_usd": float(values.mean()) if len(values) else 0.0,
        "gross_profit_usd": float(values[values > 0].sum()),
        "gross_loss_usd": float(-values[values < 0].sum()),
        "profit_factor": profit_factor(values),
        "maximum_closed_trade_drawdown_usd": max_drawdown(values),
        "top_5pct_removed_profit_factor": top_removed_profit_factor(values),
        "positive_active_month_share": (
            float((months > 0).mean()) if len(months) else 0.0
        ),
        "worst_day_usd": float(days.min()) if len(days) else 0.0,
        "worst_month_usd": float(months.min()) if len(months) else 0.0,
    }


def recent_period_metrics(trades: pd.DataFrame) -> dict:
    end = trades["exit_time"].max()
    result: dict[str, dict | None] = {}
    for months in (3, 6, 12, 24):
        start = end - pd.DateOffset(months=months)
        selected = trades[trades["exit_time"] >= start]
        row = ledger_metrics(selected)
        row["start"] = start.isoformat()
        row["end"] = end.isoformat()
        result[f"last_{months}_months"] = row
    result["last_5_years"] = None
    result["last_5_years_note"] = (
        "Unavailable: packaged MT5 portfolio evidence covers only 2024-07 to 2026-07."
    )
    result["full_packaged_history"] = ledger_metrics(trades)
    return result


def stress_metrics(trades: pd.DataFrame, extra_round_trip_pips: float) -> dict:
    extra_cost = (
        trades["volume"].to_numpy(dtype=float)
        * PIP_VALUE_USD_PER_LOT
        * extra_round_trip_pips
    )
    stressed = trades["net_pnl_usd"].to_numpy(dtype=float) - extra_cost
    result = ledger_metrics(trades, stressed)
    result["extra_round_trip_pips"] = extra_round_trip_pips
    result["total_extra_cost_usd"] = float(extra_cost.sum())
    return result


def overlap_audit(m15: pd.DataFrame, control: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    rows = []
    for short_trade in control.itertuples():
        overlaps = m15[
            (m15["entry_time"] < short_trade.exit_time)
            & (m15["exit_time"] > short_trade.entry_time)
        ]
        for long_trade in overlaps.itertuples():
            rows.append(
                {
                    "overlap_start": max(long_trade.entry_time, short_trade.entry_time),
                    "overlap_end": min(long_trade.exit_time, short_trade.exit_time),
                    "m15_volume_long": float(long_trade.volume),
                    "control_volume_short": float(short_trade.volume),
                    "gross_eurusd_lots": float(long_trade.volume + short_trade.volume),
                    "net_eurusd_lots_long": float(long_trade.volume - short_trade.volume),
                }
            )
    details = pd.DataFrame(rows)
    if details.empty:
        return {
            "cross_sleeve_overlaps": 0,
            "maximum_gross_eurusd_lots": 0.0,
            "maximum_absolute_net_eurusd_lots": 0.0,
        }, details
    return {
        "cross_sleeve_overlaps": int(len(details)),
        "zero_net_overlap_count": int(
            np.isclose(details["net_eurusd_lots_long"], 0.0).sum()
        ),
        "net_long_overlap_count": int(
            (details["net_eurusd_lots_long"] > 0).sum()
        ),
        "maximum_gross_eurusd_lots": float(details["gross_eurusd_lots"].max()),
        "maximum_absolute_net_eurusd_lots": float(
            details["net_eurusd_lots_long"].abs().max()
        ),
        "account_mode_required_for_two_positions": "hedging",
        "account_mode_attested_in_packet": False,
    }, details


def report_value(path: Path, label: str) -> str:
    text = path.read_text(encoding="utf-16")
    match = re.search(
        re.escape(label) + r"</td>\s*<td[^>]*><b>([^<]+)</b>",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        raise RuntimeError(f"Missing report field {label!r} in {path}")
    return match.group(1).strip()


def leading_float(value: str) -> float:
    match = re.search(r"-?\d+(?:\.\d+)?", value.replace(" ", ""))
    if not match:
        raise ValueError(value)
    return float(match.group(0))


def ini_inputs(path: Path) -> list[str]:
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    parser.read(path, encoding="utf-8")
    return [f"{key}={value}" for key, value in parser["TesterInputs"].items()]


def report_inputs(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-16")
    before_results = text.split("<b>Results</b>", maxsplit=1)[0]
    values = re.findall(r"<b>([^<>]+=[^<>]+)</b>", before_results)
    return {re.sub(r"\s+", " ", value).strip() for value in values}


def input_parity(report: Path, ini: Path) -> dict:
    expected = ini_inputs(ini)
    actual = report_inputs(report)
    missing = [value for value in expected if value not in actual]
    return {
        "report_matches_tester_ini": not missing,
        "tester_input_count": len(expected),
        "missing_or_mismatched_inputs": missing,
    }


def block_bootstrap(values: np.ndarray, paths: int = 10_000, block: int = 20) -> dict:
    rng = np.random.default_rng(RNG_SEED)
    n = len(values)
    blocks_needed = math.ceil(n / block)
    maximum_start = max(1, n - block + 1)
    drawdowns = np.empty(paths)
    terminal = np.empty(paths)
    ruin = np.empty(paths, dtype=bool)
    hard_dd = np.empty(paths, dtype=bool)
    for index in range(paths):
        starts = rng.integers(0, maximum_start, size=blocks_needed)
        sample = np.concatenate([values[start : start + block] for start in starts])[:n]
        curve = np.cumsum(sample)
        drawdowns[index] = max_drawdown(sample)
        terminal[index] = curve[-1]
        ruin[index] = bool(np.min(ACCOUNT_BALANCE_USD + curve) <= 0)
        hard_dd[index] = bool(drawdowns[index] >= ACCOUNT_BALANCE_USD * 0.10)
    return {
        "method": "sequence_preserving_moving_block_bootstrap",
        "seed": RNG_SEED,
        "paths": paths,
        "block_trades": block,
        "terminal_pnl_p05_usd": float(np.quantile(terminal, 0.05)),
        "terminal_pnl_median_usd": float(np.quantile(terminal, 0.50)),
        "maximum_drawdown_p50_usd": float(np.quantile(drawdowns, 0.50)),
        "maximum_drawdown_p95_usd": float(np.quantile(drawdowns, 0.95)),
        "maximum_drawdown_p99_usd": float(np.quantile(drawdowns, 0.99)),
        "risk_of_ruin": float(ruin.mean()),
        "risk_of_10pct_drawdown": float(hard_dd.mean()),
        "limitation": (
            "Resamples an adaptively selected two-year ledger; it measures sequence risk "
            "conditional on this sample and cannot repair selection contamination."
        ),
    }


def source_safety_audit() -> dict:
    m15 = M15_SOURCE.read_text(encoding="utf-8")
    control = CONTROL_SOURCE.read_text(encoding="utf-8")
    on_init = control[control.index("int OnInit()") : control.index("void OnDeinit")]
    manage = control[
        control.index("void ManageTimeExit()") : control.index("void LogSignal")
    ]
    return {
        "m15_demo_rejected_during_init": (
            "ACCOUNT_TRADE_MODE_DEMO" in m15[m15.index("int OnInit()") :]
        ),
        "control_demo_rejected_during_init": "ACCOUNT_TRADE_MODE_DEMO" in on_init,
        "control_time_exit_checks_demo_mode": "ACCOUNT_TRADE_MODE_DEMO" in manage,
        "control_position_lookup_iterates_magic_owned_positions": (
            "PositionsTotal()" in control and "PositionSelectByTicket" in control
        ),
        "shared_account_daily_loss_guard": False,
        "shared_account_rolling_loss_guard": False,
        "shared_account_floating_drawdown_guard": False,
        "shared_account_margin_guard": False,
        "cross_sleeve_duplicate_opportunity_mutex": False,
        "portfolio_kill_switch": False,
        "trend_overlay_implementation": (
            "requested_lots += InpH4TrendAdditionalLots" in m15
        ),
        "trend_overlay_is_independent_entry": False,
    }


def evidence_hashes() -> dict:
    paths = {
        "m15_report": M15_REPORT,
        "m15_source": M15_SOURCE,
        "m15_ex5": M15_EX5,
        "m15_tester_ini": M15_INI,
        "m15_shadow_preset": M15_PRESET,
        "m15_compile_log": M15_COMPILE_LOG,
        "control_report": CONTROL_REPORT,
        "control_source": CONTROL_SOURCE,
        "control_ex5": CONTROL_EX5,
        "control_tester_ini": CONTROL_INI,
        "control_shadow_preset": CONTROL_PRESET,
        "control_compile_log": CONTROL_COMPILE_LOG,
    }
    return {
        name: {"path": str(path), "sha256": sha256(path), "bytes": path.stat().st_size}
        for name, path in paths.items()
    }


def overlay_decomposition(m15: pd.DataFrame) -> dict:
    multiplier = m15["volume"].to_numpy(dtype=float) / 0.01
    original = m15["net_pnl_usd"].to_numpy(dtype=float)
    base_values = original / multiplier
    overlay_mask = multiplier > 1.0
    overlay_frame = m15.loc[overlay_mask].copy()
    overlay_values = original[overlay_mask] - base_values[overlay_mask]
    return {
        "m15_reported": ledger_metrics(m15),
        "normalized_0_01_lot_core": ledger_metrics(m15, base_values),
        "same_entry_incremental_overlay": ledger_metrics(
            overlay_frame, overlay_values
        ),
        "overlay_trade_count": int(overlay_mask.sum()),
        "implementation_classification": (
            "same-opportunity position-size doubling with identical entry, stop, target, "
            "and exit; not an independent specialist or independent candidate stream"
        ),
    }


def prior_trial_registry() -> list[dict]:
    return [
        {"id": "R-EUR-M30-MASKED", "mechanism": "EURUSD M30 RSI/Bollinger hour-masked fade", "status": "DEVELOPMENT_ONLY_RETROSPECTIVE_MASK"},
        {"id": "R-EUR-M30-UNMASKED", "mechanism": "Unmasked EURUSD RSI/Bollinger baseline", "status": "REJECTED_COST_AND_RECENCY"},
        {"id": "R-EUR-H1-1000", "mechanism": "1,000 frozen H1 attempts / 10 archetypes", "status": "REJECTED_ZERO_FDR_SURVIVORS"},
        {"id": "R-EUR-STRICT-12", "mechanism": "Twelve regime specialists", "status": "REJECTED_ADAPTIVE_EXAM_PF_0_68"},
        {"id": "R-EUR-FREQ-FALLBACK", "mechanism": "M15 RSI long + same-entry trend lot overlay + H1 short", "status": "RESEARCH_WATCHLIST_AUDIT_BLOCKED"},
        {"id": "R-EUR-H4-CHOP", "mechanism": "H4 chop Asia/London short control", "status": "RESEARCH_WATCHLIST_SPARSE"},
        {"id": "R-USDJPY-LDN120", "mechanism": "USDJPY London120 D1 ATR20 breakout", "status": "RESEARCH_WATCHLIST_RECENT_ALT_FEED_FAIL"},
        {"id": "R1", "mechanism": "Uniform bar-geometry breakout/fade across majors", "status": "REJECTED"},
        {"id": "R2", "mechanism": "Inherited EURUSD RSI/Bollinger at retail cost", "status": "REJECTED"},
        {"id": "R3", "mechanism": "Intraday momentum/reversion conditioning", "status": "REJECTED"},
        {"id": "R4", "mechanism": "Tokyo short-USD drift", "status": "REJECTED_SIGN_REVERSAL"},
        {"id": "R5", "mechanism": "Price-only momentum and value", "status": "REJECTED"},
        {"id": "R6", "mechanism": "Carry with official rates and broker swaps", "status": "REJECTED_DEPLOYABILITY"},
        {"id": "R7", "mechanism": "Tick microstructure and order flow", "status": "REJECTED_BELOW_COST"},
        {"id": "R8", "mechanism": "Volatility-conditioned microstructure", "status": "REJECTED_REPLICATION"},
        {"id": "R9", "mechanism": "Synthetic crosses and GBPJPY Donchian", "status": "REJECTED_OOS"},
        {"id": "R10", "mechanism": "Fixed-spread dislocation", "status": "REJECTED_REPLICATION"},
        {"id": "R11", "mechanism": "Gradient-boosting microstructure ML", "status": "REJECTED_OOS_DECAY"},
    ]


def data_coverage() -> dict:
    bars_manifest_path = FX_CACHE / "bars" / "MANIFEST.json"
    micro_manifest_path = FX_CACHE / "micro" / "MANIFEST.json"
    fred_manifest_path = FX_CACHE / "fred" / "MANIFEST.json"
    bars_manifest = json.loads(bars_manifest_path.read_text(encoding="utf-8"))
    micro_manifest = json.loads(micro_manifest_path.read_text(encoding="utf-8"))
    fred_manifest = json.loads(fred_manifest_path.read_text(encoding="utf-8"))
    crosses = {}
    for symbol in ("EURGBP", "EURJPY", "GBPJPY"):
        path = FX_CACHE / "bars" / f"{symbol}_M5_BIDASK.parquet"
        timestamp = pd.read_parquet(path, columns=["timestamp_ms"])["timestamp_ms"]
        crosses[symbol] = {
            "path": str(path),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "rows": int(len(timestamp)),
            "first_utc": pd.to_datetime(timestamp.min(), unit="ms", utc=True).isoformat(),
            "last_utc": pd.to_datetime(timestamp.max(), unit="ms", utc=True).isoformat(),
            "manifest_status": "FILE_PRESENT_NOT_LISTED_IN_PRIMARY_BARS_MANIFEST",
        }
    raw_root = DATA_ROOT / "C_DRIVE" / "DukascopyTickDataFoundationV1" / "raw"
    raw_symbols = sorted(path.name for path in raw_root.iterdir() if path.is_dir())
    broker_h1 = FX_CACHE / "broker_h1"
    broker_h1_files = [path for path in broker_h1.rglob("*") if path.is_file()]
    quarantine = {
        "affected_symbols": ["EURUSD", "USDJPY"],
        "interval_utc": ["2024-10-09T23:00:00Z", "2024-10-10T01:00:00Z"],
        "failure": "Dukascopy source returned non-positive price or negative spread",
        "repair_status": "UNREPAIRED_EXPLICIT_QUARANTINE",
        "eurusd_h1_frozen_months": 119,
        "eurusd_h1_expected_months": 120,
        "missing_frozen_month": "2024-10",
    }
    return {
        "data_root": str(DATA_ROOT),
        "primary_bidask_m5": bars_manifest,
        "causal_microstructure_m5": micro_manifest,
        "synthetic_cross_bidask_m5": crosses,
        "fred_daily_panel": fred_manifest,
        "broker_h1": {
            "path": str(broker_h1),
            "files": len(broker_h1_files),
            "status": "EMPTY_NO_BROKER_H1_EVIDENCE",
        },
        "raw_symbols_present": raw_symbols,
        "audusd_intraday_status": (
            "NOT_PRESENT_IN_RAW_OR_PREPARED_INTRADAY_CACHE; FRED_DAILY_ONLY"
            if "AUDUSD" not in raw_symbols
            else "RAW_PRESENT"
        ),
        "october_2024_quarantine": quarantine,
        "manifest_hashes": {
            "bars": sha256(bars_manifest_path),
            "micro": sha256(micro_manifest_path),
            "fred": sha256(fred_manifest_path),
        },
    }


def gate(status: str, evidence: str) -> dict:
    return {"status": status, "evidence": evidence}


def write_markdown(audit: dict) -> None:
    base = audit["metrics"]["portfolio"]
    recent = audit["metrics"]["periods"]
    overlay = audit["metrics"]["overlay_decomposition"]
    stress = audit["metrics"]["cost_stress"]
    sleeves = audit["metrics"]["by_sleeve"]
    monte_carlo = audit["metrics"]["monte_carlo"]
    lines = [
        "# Forex Demo Readiness V1 — Independent Audit",
        "",
        f"Verdict: **`{audit['verdict']}`**",
        "",
        "The legacy `CONTROLLED_SHADOW_DEMO_READY` label is not substantiated by the",
        "evidence required for a shared-account controlled shadow or demo trial. The",
        "historical result remains a positive research lead, but it is downgraded to",
        "`RESEARCH_WATCHLIST` until the blockers below are closed prospectively.",
        "",
        "## Reproduced headline",
        "",
        "| Metric | Reproduced |",
        "|---|---:|",
        f"| Trades | {base['trades']} |",
        f"| Declared trades / active broker date | {audit['metrics']['declared_trades_per_active_broker_date']:.4f} |",
        f"| Win rate | {base['win_rate']:.2%} |",
        f"| Net P&L | ${base['net_pnl_usd']:.2f} |",
        f"| Profit factor | {base['profit_factor']:.4f} |",
        f"| Average trade | ${base['average_trade_usd']:.4f} |",
        f"| Maximum closed-trade drawdown | ${base['maximum_closed_trade_drawdown_usd']:.2f} |",
        f"| Worst day | ${base['worst_day_usd']:.2f} |",
        f"| Worst month | ${base['worst_month_usd']:.2f} |",
        f"| Positive active months | {base['positive_active_month_share']:.2%} |",
        f"| PF after removing top 5% | {base['top_5pct_removed_profit_factor']:.4f} |",
        "",
        "## Material findings",
        "",
    ]
    for finding in audit["material_findings"]:
        lines.append(f"- {finding}")
    lines += [
        "",
        "## Overlay decomposition",
        "",
        "| Component | Trades | Net | PF |",
        "|---|---:|---:|---:|",
        f"| M15 reported | {overlay['m15_reported']['trades']} | ${overlay['m15_reported']['net_pnl_usd']:.2f} | {overlay['m15_reported']['profit_factor']:.4f} |",
        f"| M15 normalized 0.01-lot core | {overlay['normalized_0_01_lot_core']['trades']} | ${overlay['normalized_0_01_lot_core']['net_pnl_usd']:.2f} | {overlay['normalized_0_01_lot_core']['profit_factor']:.4f} |",
        f"| Same-entry incremental overlay | {overlay['same_entry_incremental_overlay']['trades']} | ${overlay['same_entry_incremental_overlay']['net_pnl_usd']:.2f} | {overlay['same_entry_incremental_overlay']['profit_factor']:.4f} |",
        "",
        "The overlay is a risk multiplier on the same opportunity. It is not a second",
        "specialist, candidate, position owner, or independently timed exposure.",
        "",
        "## Specialist / sleeve evidence",
        "",
        "| Pair | Direction | Session / regime ownership | Sleeve | Trades | Net | PF |",
        "|---|---|---|---|---:|---:|---:|",
        f"| EURUSD | Long | M15 all-day RSI extreme; H4 trend only changes size | M15 core + overlay | {sleeves['m15']['trades']} | ${sleeves['m15']['net_pnl_usd']:.2f} | {sleeves['m15']['profit_factor']:.4f} |",
        f"| EURUSD | Short | Asia/London, completed-H4 chop | H1 control | {sleeves['control']['trades']} | ${sleeves['control']['net_pnl_usd']:.2f} | {sleeves['control']['profit_factor']:.4f} |",
        "",
        "No GBPUSD, USDJPY, cross-pair, or other Forex specialist is present in the",
        "packaged portfolio. Pair diversification is therefore zero.",
        "",
        "## Recent windows",
        "",
        "| Window | Trades | Net | PF | Closed DD |",
        "|---|---:|---:|---:|---:|",
    ]
    for key in ("last_3_months", "last_6_months", "last_12_months", "last_24_months"):
        row = recent[key]
        lines.append(
            f"| {key.replace('_', ' ')} | {row['trades']} | ${row['net_pnl_usd']:.2f} | "
            f"{row['profit_factor']:.4f} | ${row['maximum_closed_trade_drawdown_usd']:.2f} |"
        )
    lines += [
        "",
        "Five-year packaged MT5 portfolio evidence is unavailable.",
        "",
        "## Cost stress",
        "",
        "| Extra round-trip cost | Net | PF |",
        "|---|---:|---:|",
    ]
    for key in ("plus_0_5_pip", "plus_1_0_pip"):
        row = stress[key]
        lines.append(
            f"| +{row['extra_round_trip_pips']:.1f} pip | ${row['net_pnl_usd']:.2f} | "
        f"{row['profit_factor']:.4f} |"
        )
    lines += [
        "",
        "## Sequence-preserving Monte Carlo",
        "",
        f"- Method: moving-block bootstrap, {monte_carlo['paths']} paths, "
        f"{monte_carlo['block_trades']}-trade blocks, seed `{monte_carlo['seed']}`.",
        f"- Median maximum drawdown: ${monte_carlo['maximum_drawdown_p50_usd']:.2f}.",
        f"- 95th / 99th percentile maximum drawdown: "
        f"${monte_carlo['maximum_drawdown_p95_usd']:.2f} / "
        f"${monte_carlo['maximum_drawdown_p99_usd']:.2f}.",
        f"- Conditional risk of ruin / 10% drawdown: "
        f"{monte_carlo['risk_of_ruin']:.2%} / "
        f"{monte_carlo['risk_of_10pct_drawdown']:.2%}.",
        "- This resamples adaptively selected history and is not independent evidence.",
        "",
        "## New bounded research",
        "",
        "No new strategy outcome was opened. Eleven prior mechanism classes are already",
        "closed, AUDUSD has no local intraday cache, and no causal official",
        "event-surprise dataset with release-vintage controls is present. Retesting a",
        "closed price-only or microstructure family would create more selection debt.",
        "The pair-by-pair cache snapshot is in `DATA_COVERAGE_MANIFEST.json`; the",
        "append-only hypothesis history is in `PRIOR_TRIAL_REGISTRY.csv`.",
        "",
        "## Decision gates",
        "",
        "| Gate | Status | Evidence |",
        "|---|---|---|",
    ]
    for name, result in audit["acceptance_gates"].items():
        lines.append(
            f"| {name.replace('_', ' ')} | {result['status']} | "
            f"{result['evidence'].replace('|', '/')} |"
        )
    lines += [
        "",
        "## Remaining blockers",
        "",
    ]
    for blocker in audit["blockers"]:
        lines.append(f"- {blocker}")
    lines += [
        "",
        "## Reproduction",
        "",
        "```powershell",
        "python forex/forex-demo-readiness-v1/audit_demo_readiness.py",
        "python -m pytest forex/forex-demo-readiness-v1/tests -q",
        "```",
        "",
        "No terminal, account, chart, order, or broker runtime was touched.",
    ]
    (OUTPUT / "FOREX_DEMO_READINESS_AUDIT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    m15 = read_mt5_trades(
        M15_REPORT, "M15_RSI_LONG_H4_TREND_OVERLAY", "long"
    )
    control = read_mt5_trades(
        CONTROL_REPORT, "H1_CHOP_ASIA_LONDON_SHORT_CONTROL", "short"
    )
    trades = (
        pd.concat([m15, control], ignore_index=True)
        .sort_values(["exit_time", "sleeve"])
        .reset_index(drop=True)
    )
    overlap, overlap_rows = overlap_audit(m15, control)
    base = ledger_metrics(trades)
    stress_05 = stress_metrics(trades, 0.5)
    stress_10 = stress_metrics(trades, 1.0)
    report_equity = {
        "m15_maximum_equity_drawdown_usd": leading_float(
            report_value(M15_REPORT, "Equity Drawdown Maximal:")
        ),
        "control_maximum_equity_drawdown_usd": leading_float(
            report_value(CONTROL_REPORT, "Equity Drawdown Maximal:")
        ),
    }
    report_equity["sum_of_standalone_maxima_upper_bound_usd"] = (
        report_equity["m15_maximum_equity_drawdown_usd"]
        + report_equity["control_maximum_equity_drawdown_usd"]
    )
    safety = source_safety_audit()
    periods = recent_period_metrics(trades)
    monte_carlo = block_bootstrap(trades["net_pnl_usd"].to_numpy(dtype=float))
    recent_12_pf = periods["last_12_months"]["profit_factor"]

    gates = {
        "frequency_at_least_1_per_active_trading_day": gate(
            "UNVERIFIED",
            "1.1333 uses a hard-coded 615-date denominator; the hashed broker M15 source is absent.",
        ),
        "base_profit_factor_at_least_1_30": gate(
            "PASS" if base["profit_factor"] >= 1.30 else "FAIL",
            f"Report-derived combined PF {base['profit_factor']:.4f}.",
        ),
        "stressed_profit_factor_at_least_1_15": gate(
            "PASS" if stress_05["profit_factor"] >= 1.15 else "FAIL",
            f"PF {stress_05['profit_factor']:.4f} after +0.5 pip round-trip per trade.",
        ),
        "hard_1pip_cost_stress_profit_factor_at_least_1_15": gate(
            "PASS" if stress_10["profit_factor"] >= 1.15 else "FAIL",
            f"PF {stress_10['profit_factor']:.4f} after +1.0 pip round-trip per trade.",
        ),
        "cost_stressed_top_5pct_removed_profit_factor_at_least_1": gate(
            (
                "PASS"
                if stress_05["top_5pct_removed_profit_factor"] >= 1.0
                else "FAIL"
            ),
            (
                f"PF {stress_05['top_5pct_removed_profit_factor']:.4f} after "
                "+0.5 pip cost and removal of the top 5% of trades."
            ),
        ),
        "positive_expected_value_per_trade": gate(
            "PASS" if base["average_trade_usd"] > 0 else "FAIL",
            f"Average ${base['average_trade_usd']:.4f} per completed trade.",
        ),
        "trailing_12_month_pf_at_least_1_15_and_positive": gate(
            (
                "PASS"
                if recent_12_pf >= 1.15
                and periods["last_12_months"]["net_pnl_usd"] > 0
                else "FAIL"
            ),
            f"PF {recent_12_pf:.4f}, net ${periods['last_12_months']['net_pnl_usd']:.2f}.",
        ),
        "two_chronological_validation_windows_profitable": gate(
            "FAIL",
            "The packaged MT5 portfolio has one adaptive 2024-2026 interval and no two untouched validation windows.",
        ),
        "positive_active_month_share_at_least_55pct": gate(
            "PASS" if base["positive_active_month_share"] >= 0.55 else "FAIL",
            f"{base['positive_active_month_share']:.2%} of active months positive.",
        ),
        "top_5pct_winners_removed_pf_at_least_1": gate(
            "PASS" if base["top_5pct_removed_profit_factor"] >= 1.0 else "FAIL",
            f"PF {base['top_5pct_removed_profit_factor']:.4f}; only 0.019 above break-even.",
        ),
        "no_single_pair_direction_or_specialist_hides_failure": gate(
            "FAIL",
            "All 697 trades are EURUSD; 635/697 are one long-only M15 source and 120 use same-entry lot doubling.",
        ),
        "base_floating_equity_drawdown_at_most_5pct": gate(
            "UNVERIFIED",
            (
                "No combined-account equity path. Standalone maxima sum to a conservative "
                f"${report_equity['sum_of_standalone_maxima_upper_bound_usd']:.2f} bound only."
            ),
        ),
        "stressed_floating_equity_drawdown_at_most_10pct": gate(
            "UNVERIFIED",
            "No synchronized bid/ask position path or combined MT5 report exists.",
        ),
        "monte_carlo_risk_of_ruin_below_1pct": gate(
            "PASS" if monte_carlo["risk_of_ruin"] < 0.01 else "FAIL",
            (
                f"Conditional block-bootstrap ruin {monte_carlo['risk_of_ruin']:.2%}; "
                "does not repair adaptive selection."
            ),
        ),
        "no_duplicate_or_same_opportunity_stacking": gate(
            "FAIL",
            "The H4 trend overlay adds 0.01 lot to the identical M15 entry/SL/TP rather than owning a new opportunity.",
        ),
        "source_ex5_preset_report_build_chain_locked": gate(
            "FAIL",
            "Files are hashable, but no compiler attestation proves each EX5 was built from the exact hashed source; the control chain is absent from the legacy verdict.",
        ),
        "exact_combined_mt5_strategy_tester_parity": gate(
            "FAIL",
            "Only two standalone reports were arithmetically concatenated; no same-account combined Strategy Tester run exists.",
        ),
        "fail_closed_demo_only_account_and_server_guard": gate(
            "FAIL",
            "The control EA does not reject non-demo accounts in OnInit and its time-exit close path has no demo-mode check.",
        ),
        "fixed_initial_0_01_lot_research_sizing": gate(
            "FAIL",
            "120 M15 trades used 0.02 lots through the same-entry trend overlay.",
        ),
    }

    blockers = [
        "Adaptive selection contamination: the only packaged MT5 interval was inspected before the fallback and gates were declared.",
        "Missing Capital.com M15 broker-bar source prevents source reproduction and active-day denominator verification.",
        "No combined same-account MT5 run, account margin-mode attestation, or exact cross-sleeve fill/ownership parity.",
        "No synchronized combined floating-equity reconstruction or stressed floating drawdown.",
        "Trend overlay is same-opportunity lot doubling, not independent specialist exposure.",
        "No shared-account daily/rolling loss, margin, floating drawdown, USD exposure, concurrency, or kill-switch engine.",
        "Control EA live-safety and magic-owned position-selection defects.",
        "No exact source-to-EX5 compiler attestation for both EAs and no complete locked chain in the legacy verdict.",
        "Portfolio is single-pair and overwhelmingly one-direction/one-source; it is not the requested diversified Forex architecture.",
        "No genuinely untouched historical holdout remains; prospective evidence must be locked before observation.",
    ]
    findings = [
        "The legacy arithmetic is reproducible: 697 trades, $119.42 net, PF 1.3075, and 58 cross-sleeve time overlaps.",
        "The M15 standalone report itself is PF 1.29; the combined PF clears 1.30 only after adding the sparse H1 control.",
        "The trend overlay is implemented as `requested_lots += 0.01` on the same entry and exit, not as an independent candidate.",
        "The claimed maximum of two concurrent positions assumes a hedging account, but the packet does not attest the account margin mode.",
        "The reports were produced separately, so their concatenation cannot establish shared-account fills, ownership, margin, or equity drawdown.",
        "The existing test suite passes because it asserts the old adaptive label and shallow source-string guards; it does not test the missing portfolio controls.",
        "October 2024 remains explicitly quarantined for EURUSD and USDJPY at 2024-10-09 23:00 through 2024-10-10 01:00 UTC.",
    ]

    audit = {
        "schema_version": "forex_demo_readiness_v1_audit",
        "status": "SUPERSEDES_LEGACY_DEMO_READINESS_LABEL",
        "verdict": "RESEARCH_WATCHLIST",
        "controlled_shadow_ready": False,
        "controlled_demo_ready": False,
        "live_ready": False,
        "legacy_verdict": "CONTROLLED_SHADOW_DEMO_READY",
        "metrics": {
            "portfolio": base,
            "declared_active_broker_dates": DECLARED_ACTIVE_BROKER_DATES,
            "declared_trades_per_active_broker_date": len(trades)
            / DECLARED_ACTIVE_BROKER_DATES,
            "unique_dates_with_completed_trades": int(
                trades["exit_time"].dt.strftime("%Y-%m-%d").nunique()
            ),
            "by_sleeve": {
                "m15": ledger_metrics(m15),
                "control": ledger_metrics(control),
            },
            "overlay_decomposition": overlay_decomposition(m15),
            "overlap_and_exposure": overlap,
            "periods": periods,
            "cost_stress": {
                "plus_0_5_pip": stress_05,
                "plus_1_0_pip": stress_10,
            },
            "standalone_report_equity_drawdown": report_equity,
            "monte_carlo": monte_carlo,
        },
        "input_parity": {
            "m15": input_parity(M15_REPORT, M15_INI),
            "control": input_parity(CONTROL_REPORT, CONTROL_INI),
        },
        "source_safety": safety,
        "source_evidence": {
            "hashes": evidence_hashes(),
            "source_to_ex5_build_parity_proven": False,
            "combined_portfolio_report_present": False,
            "capital_m15_broker_source": {
                "path": str(MISSING_BROKER_SOURCE),
                "exists": MISSING_BROKER_SOURCE.exists(),
                "expected_sha256": "eacc532a5f0001ea66c80a558bd4cffe7ced5704bf9d9d4770cb2f783269bea0",
            },
        },
        "acceptance_gates": gates,
        "material_findings": findings,
        "blockers": blockers,
        "research_boundary": {
            "new_strategy_experiments_run": 0,
            "reason": (
                "Eleven prior mechanism classes are closed. AUDUSD has no prepared or raw "
                "intraday cache, and no causal event-surprise dataset is present. Reusing "
                "closed price-only or microstructure families would violate the research boundary."
            ),
            "next_legitimate_data_questions": [
                "Acquire and preregister a causal official event-surprise dataset with release timestamps and vintage controls.",
                "Preregister an AUDUSD intraday data census before acquisition; no strategy outcome may be opened during the census.",
                "Collect genuinely prospective locked shadow signals after implementation and parity defects are closed.",
            ],
        },
        "no_runtime_touched": True,
    }

    coverage = data_coverage()
    registry = prior_trial_registry()
    trades.to_csv(OUTPUT / "PORTFOLIO_TRADES_REPRODUCED.csv", index=False)
    overlap_rows.to_csv(OUTPUT / "OVERLAP_EXPOSURE_LEDGER.csv", index=False)
    with (OUTPUT / "PRIOR_TRIAL_REGISTRY.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=("id", "mechanism", "status"))
        writer.writeheader()
        writer.writerows(registry)
    (OUTPUT / "DATA_COVERAGE_MANIFEST.json").write_text(
        json.dumps(coverage, indent=2) + "\n", encoding="utf-8"
    )
    (OUTPUT / "AUDIT.json").write_text(
        json.dumps(audit, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    write_markdown(audit)
    print(json.dumps({"verdict": audit["verdict"], "blockers": len(blockers)}, indent=2))


if __name__ == "__main__":
    main()

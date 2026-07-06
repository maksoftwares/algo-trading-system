from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
import urllib.parse
import urllib.request

import pandas as pd


RUN_DATE = "2026_07_03"
TARGET_SYMBOLS = ("EURUSD", "GBPUSD", "USDJPY")
TARGET_TIMEFRAMES = ("M5", "M15", "H1", "H4")
FOREX_SYMBOLS = {"EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF", "EURJPY", "GBPJPY"}
RECENT_START = pd.Timestamp("2022-01-01T00:00:00Z")
LOCAL_FRESHNESS_CUTOFF = pd.Timestamp("2025-01-01T00:00:00Z")
FIXED_RISK_USD = 50.0
RECENT_PROXY_START = datetime(2025, 7, 1, tzinfo=timezone.utc)
BROKER_REFRESH_WATCHLIST_IDS = {
    "eurusd_h4_real_yield_dollar_pressure_reversal_v0",
    "eurusd_h4_rates_dollar_yield_pressure_short_session_v1",
    "usdjpy_h4_bond_vol_carry_pullback_v0",
    "usdjpy_h4_bond_vol_asia_session_carry_relief_v1",
}
BROKER_REFRESH_COST_R_P95_LIMIT = 0.05
BROKER_REFRESH_CONTEXT_STALE_GRACE_DAYS = 7
BROKER_REFRESH_PROVENANCE_FIELDS = (
    "export_terminal",
    "export_account_login",
    "export_account_server",
    "export_account_type",
    "export_broker_company",
    "exported_at_utc",
    "export_timezone",
    "export_method",
)
BROKER_REFRESH_PROVENANCE_ALIASES = {
    "export_terminal": ("export_terminal", "terminal", "terminal_path", "source_terminal"),
    "export_account_login": ("export_account_login", "account_login", "login", "account"),
    "export_account_server": ("export_account_server", "account_server", "server"),
    "export_account_type": ("export_account_type", "account_type"),
    "export_broker_company": ("export_broker_company", "broker_company", "company"),
    "exported_at_utc": ("exported_at_utc", "export_time_utc", "generated_at_utc"),
    "export_timezone": ("export_timezone", "source_timezone", "timezone"),
    "export_method": ("export_method", "method"),
}
YAHOO_FX_SYMBOLS = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "JPY=X",
}
YAHOO_COMMODITY_DOLLAR_SYMBOLS = {
    "DBC": "DBC",
    "DBB": "DBB",
    "UUP": "UUP",
}
YAHOO_REAL_ASSET_ROTATION_SYMBOLS = {
    "USO": "USO",
    "UUP": "UUP",
    "HG": "HG=F",
    "GC": "GC=F",
    "SLV": "SLV",
    "GLD": "GLD",
}
YAHOO_HAVEN_LIQUIDITY_SYMBOLS = {
    "GLD": "GLD",
    "GDX": "GDX",
    "SPY": "SPY",
    "TLT": "TLT",
    "XLU": "XLU",
    "XLK": "XLK",
}
YAHOO_RATES_DOLLAR_SYMBOLS = {
    "TLT": "TLT",
    "UUP": "UUP",
    "SHY": "SHY",
}
YAHOO_EQUITY_LEADERSHIP_SYMBOLS = {
    "ACWX": "ACWX",
    "SPY": "SPY",
    "IWM": "IWM",
    "XLF": "XLF",
    "XLU": "XLU",
}
YAHOO_SECTOR_ROTATION_SYMBOLS = {
    "XLY": "XLY",
    "XLP": "XLP",
    "QQQ": "QQQ",
    "SPY": "SPY",
    "XLE": "XLE",
    "XLU": "XLU",
    "XLI": "XLI",
    "XME": "XME",
    "TIP": "TIP",
    "IEF": "IEF",
}
YAHOO_CURRENCY_BASKET_SYMBOLS = {
    "FXA": "FXA",
    "FXF": "FXF",
    "CYB": "CYB",
    "UUP": "UUP",
}
YAHOO_BOND_VOL_SYMBOLS = {
    "MOVE": "^MOVE",
}
YAHOO_CRYPTO_RISK_SYMBOLS = {
    "BTC": "BTC-USD",
}
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
MACRO_SOURCE_FILES = {
    "real_yield_10y": ("FRED_DFII10.csv", "DFII10"),
    "dollar_index_broad": ("FRED_DTWEXBGS.csv", "DTWEXBGS"),
}
CNY_PRESSURE_SOURCE_FILES = {
    "usd_cny": ("FRED_DEXCHUS.csv", "DEXCHUS"),
    "dollar_index_broad": ("FRED_DTWEXBGS.csv", "DTWEXBGS"),
}
TREASURY_CURVE_SOURCE_FILES = {
    "dgs2": ("FRED_DGS2.csv", "DGS2"),
    "dgs10": ("FRED_DGS10.csv", "DGS10"),
    "t10y2y": ("FRED_T10Y2Y.csv", "T10Y2Y"),
}
RISK_SOURCE_FILES = {
    "vix": ("FRED_VIXCLS.csv", "VIXCLS"),
    "vxv": ("FRED_VXVCLS.csv", "VXVCLS"),
}
FINANCIAL_LIQUIDITY_SOURCE_FILES = {
    "nfci": ("financial_conditions/FRED_NFCI.csv", "NFCI"),
    "anfci": ("financial_conditions/FRED_ANFCI.csv", "ANFCI"),
    "walcl": ("liquidity/FRED_WALCL.csv", "WALCL"),
}
CFTC_HISTORICAL_COMPRESSED_URL = "https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm"
CFTC_FINANCIAL_COT_ZIP_URL = "https://www.cftc.gov/files/dea/history/fut_fin_txt_{year}.zip"
COT_FINANCIAL_YEARS = tuple(range(2016, 2027))
COT_FINANCIAL_MARKETS = {
    "EURUSD": {
        "market": "EURO FX - CHICAGO MERCANTILE EXCHANGE",
        "orientation": 1.0,
        "orientation_note": "Euro FX futures net long is EURUSD-bullish.",
    },
    "USDJPY": {
        "market": "JAPANESE YEN - CHICAGO MERCANTILE EXCHANGE",
        "orientation": -1.0,
        "orientation_note": "Japanese Yen futures net long is USDJPY-bearish, so the spot orientation is inverted.",
    },
}
CURRENCY_ETF_FILES = {
    "EURUSD": {
        "filename": "fxe_uup_daily_yahoo_2015_2025.csv",
        "base": "fxe",
        "quote": "uup",
        "orientation": "direct",
    },
    "USDJPY": {
        "filename": "fxy_uup_daily_yahoo_2015_2025.csv",
        "base": "fxy",
        "quote": "uup",
        "orientation": "inverse",
    },
}
FX_CROSS_FILES = {
    "AUDJPY_USDJPY": {
        "filename": "audjpy_usdjpy_daily_yahoo_2015_2025.csv",
        "cross": "audjpy",
        "anchor": "usdjpy",
    },
    "EURJPY_USDJPY": {
        "filename": "eurjpy_usdjpy_daily_yahoo_2015_2025.csv",
        "cross": "eurjpy",
        "anchor": "usdjpy",
    },
}
GLOBAL_RISK_FILES = {
    "eem_spy": {
        "filename": "eem_spy_daily_yahoo_2015_2025.csv",
        "risk": "eem",
        "defensive": "spy",
    },
    "hyg_ief": {
        "filename": "hyg_ief_daily_yahoo_2015_2025.csv",
        "risk": "hyg",
        "defensive": "ief",
    },
}
COMMODITY_DOLLAR_FILES = {
    "dbc_uup": {
        "filename": "dbc_uup_daily_yahoo_2015_2025.csv",
        "commodity": "dbc",
        "dollar": "uup",
    },
    "dbb_uup": {
        "filename": "dbb_uup_daily_yahoo_2015_2025.csv",
        "commodity": "dbb",
        "dollar": "uup",
    },
}
REAL_ASSET_ROTATION_FILES = {
    "uso_uup": {
        "filename": "uso_uup_daily_yahoo_2015_2025.csv",
        "source_root": "etf",
        "left": "uso",
        "right": "uup",
    },
    "hg_gc": {
        "filename": "hg_gc_daily_yahoo_2015_2025.csv",
        "source_root": "futures",
        "left": "hg",
        "right": "gc",
    },
    "slv_gld": {
        "filename": "slv_gld_daily_yahoo_2015_2025.csv",
        "source_root": "etf",
        "left": "slv",
        "right": "gld",
    },
}
HAVEN_LIQUIDITY_FILES = {
    "gld": {
        "filename": "gld_daily_yahoo_2015_2025.csv",
        "kind": "single",
        "symbol": "gld",
    },
    "gdx_gld": {
        "filename": "gdx_gld_daily_yahoo_2015_2025.csv",
        "kind": "pair",
        "left": "gdx",
        "right": "gld",
    },
    "spy_tlt": {
        "filename": "spy_tlt_daily_yahoo_2015_2025.csv",
        "kind": "pair",
        "left": "spy",
        "right": "tlt",
    },
    "xlu_xlk": {
        "filename": "xlu_xlk_daily_yahoo_2015_2025.csv",
        "kind": "pair",
        "left": "xlu",
        "right": "xlk",
    },
}
RATES_DOLLAR_FILES = {
    "tlt_uup": {
        "filename": "tlt_uup_daily_yahoo_2015_2025.csv",
        "duration": "tlt",
        "dollar": "uup",
    },
    "tlt_shy": {
        "filename": "tlt_shy_daily_yahoo_2015_2025.csv",
        "duration": "tlt",
        "cash": "shy",
    },
}
EQUITY_LEADERSHIP_FILES = {
    "acwx_spy": {
        "filename": "acwx_spy_daily_yahoo_2015_2025.csv",
        "leader": "acwx",
        "benchmark": "spy",
    },
    "iwm_spy": {
        "filename": "iwm_spy_daily_yahoo_2015_2025.csv",
        "leader": "iwm",
        "benchmark": "spy",
    },
    "xlf_xlu": {
        "filename": "xlf_xlu_daily_yahoo_2015_2025.csv",
        "leader": "xlf",
        "benchmark": "xlu",
    },
}
SECTOR_ROTATION_FILES = {
    "xly_xlp": {
        "filename": "xlp_xly_daily_yahoo_2015_2025.csv",
        "leader": "xly",
        "benchmark": "xlp",
    },
    "qqq_spy": {
        "filename": "qqq_spy_daily_yahoo_2015_2025.csv",
        "leader": "qqq",
        "benchmark": "spy",
    },
    "xle_xlu": {
        "filename": "xle_xlu_daily_yahoo_2015_2025.csv",
        "leader": "xle",
        "benchmark": "xlu",
    },
    "xli_xlu": {
        "filename": "xli_xlu_daily_yahoo_2015_2025.csv",
        "leader": "xli",
        "benchmark": "xlu",
    },
    "xme_spy": {
        "filename": "xme_spy_daily_yahoo_2015_2025.csv",
        "leader": "xme",
        "benchmark": "spy",
    },
    "tip_ief": {
        "filename": "tip_ief_daily_yahoo_2015_2025.csv",
        "leader": "tip",
        "benchmark": "ief",
    },
}
CURRENCY_BASKET_FILES = {
    "fxa_uup": {
        "filename": "fxa_uup_daily_yahoo_2015_2025.csv",
        "currency": "fxa",
        "dollar": "uup",
    },
    "fxf_uup": {
        "filename": "fxf_uup_daily_yahoo_2015_2025.csv",
        "currency": "fxf",
        "dollar": "uup",
    },
    "cyb_uup": {
        "filename": "cyb_uup_daily_yahoo_2015_2025.csv",
        "currency": "cyb",
        "dollar": "uup",
    },
}
BOND_VOL_FILES = {
    "move": {
        "filename": "move_daily_yahoo_2015_2025.csv",
        "symbol": "move",
    },
}
CRYPTO_RISK_FILES = {
    "btc": {
        "filename": "btc_usd_daily_yahoo_2015_2025.csv",
        "symbol": "btc",
    },
}
TIMEFRAME_DELTAS = {
    "M5": pd.Timedelta(minutes=5),
    "M15": pd.Timedelta(minutes=15),
    "H1": pd.Timedelta(hours=1),
    "H4": pd.Timedelta(hours=4),
}


@dataclass(frozen=True)
class Paths:
    repo: Path
    lane: Path
    bars: Path
    external: Path
    reports: Path
    tables: Path


@dataclass(frozen=True)
class CostCell:
    broker: str
    symbol: str
    timeframe: str
    file_count: int
    rows: int
    start_utc: str
    end_utc: str
    point_size: float
    clean_ohlc: bool
    has_spread: bool
    spread_median_points: float
    spread_p95_points: float
    atr14_median_points: float
    atr14_recent_median_points: float
    representative_stop_points: float
    representative_stop_recent_points: float
    cost_r_median: float
    cost_r_p95: float
    cost_r_recent_p95: float
    data_status: str
    spread_status: str


@dataclass(frozen=True)
class CandidateSpec:
    candidate_id: str
    symbol: str
    timeframe: str
    family: str
    description: str
    generator: Callable[[pd.DataFrame], list[dict[str, Any]]]
    max_hold_bars: int
    target_r: float = 1.5


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def paths(repo: Path | None = None) -> Paths:
    repo = (repo or repo_root_from_script()).resolve()
    lane = repo / "forex-research"
    return Paths(
        repo=repo,
        lane=lane,
        bars=repo / "xau-usd" / "xauusd-phase0" / "data" / "processed" / "bars",
        external=lane / "data" / "external",
        reports=lane / "outputs" / "reports",
        tables=lane / "outputs" / "tables",
    )


def ensure_dirs(p: Paths) -> None:
    p.reports.mkdir(parents=True, exist_ok=True)
    p.tables.mkdir(parents=True, exist_ok=True)
    p.external.mkdir(parents=True, exist_ok=True)
    broker_refresh_raw_root(p).mkdir(parents=True, exist_ok=True)
    broker_refresh_validated_root(p).mkdir(parents=True, exist_ok=True)


def recent_proxy_root(p: Paths) -> Path:
    return p.external / "yahoo_fx"


def recent_commodity_proxy_root(p: Paths) -> Path:
    return p.external / "yahoo_etf" / "commodity_dollar"


def recent_real_asset_rotation_proxy_root(p: Paths) -> Path:
    return p.external / "yahoo_etf" / "real_asset_rotation"


def recent_haven_liquidity_proxy_root(p: Paths) -> Path:
    return p.external / "yahoo_etf" / "haven_liquidity"


def recent_rates_proxy_root(p: Paths) -> Path:
    return p.external / "yahoo_etf" / "rates_dollar"


def recent_equity_leadership_proxy_root(p: Paths) -> Path:
    return p.external / "yahoo_etf" / "equity_leadership"


def recent_sector_rotation_proxy_root(p: Paths) -> Path:
    return p.external / "yahoo_etf" / "sector_rotation"


def recent_currency_basket_proxy_root(p: Paths) -> Path:
    return p.external / "yahoo_etf" / "currency_basket"


def recent_bond_vol_proxy_root(p: Paths) -> Path:
    return p.external / "yahoo_rates" / "bond_vol"


def recent_crypto_risk_proxy_root(p: Paths) -> Path:
    return p.external / "yahoo_crypto" / "crypto_risk"


def broker_refresh_raw_root(p: Paths) -> Path:
    return p.lane / "data" / "broker_refresh" / "raw"


def broker_refresh_validated_root(p: Paths) -> Path:
    return p.lane / "data" / "broker_refresh" / "validated"


def macro_source_root(p: Paths) -> Path:
    return p.repo / "xau-usd" / "xauusd-phase0" / "data" / "raw" / "macro"


def treasury_curve_source_root(p: Paths) -> Path:
    return p.repo / "xau-usd" / "xauusd-phase0" / "data" / "raw" / "treasury_curve"


def reference_etf_root(p: Paths) -> Path:
    return p.repo / "xau-usd" / "xauusd-phase0" / "data" / "reference" / "etf"


def reference_fx_root(p: Paths) -> Path:
    return p.repo / "xau-usd" / "xauusd-phase0" / "data" / "reference" / "fx"


def reference_futures_root(p: Paths) -> Path:
    return p.repo / "xau-usd" / "xauusd-phase0" / "data" / "reference" / "futures"


def reference_rates_root(p: Paths) -> Path:
    return p.repo / "xau-usd" / "xauusd-phase0" / "data" / "reference" / "rates"


def reference_crypto_root(p: Paths) -> Path:
    return p.repo / "xau-usd" / "xauusd-phase0" / "data" / "reference" / "crypto"


def risk_source_root(p: Paths) -> Path:
    return p.repo / "xau-usd" / "xauusd-phase0" / "data" / "raw" / "risk"


def financial_liquidity_source_root(p: Paths) -> Path:
    return p.repo / "xau-usd" / "xauusd-phase0" / "data" / "raw"


def cot_financial_root(p: Paths) -> Path:
    return p.external / "cftc_cot" / "financial_futures"


def acquire_recent_yahoo_proxy(p: Paths) -> list[dict[str, Any]]:
    acquired_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    end_dt = datetime.now(timezone.utc) + timedelta(days=1)
    manifest: list[dict[str, Any]] = []
    for symbol, yahoo_symbol in YAHOO_FX_SYMBOLS.items():
        rows = download_yahoo_h1(yahoo_symbol, RECENT_PROXY_START, end_dt)
        if len(rows) < 1000:
            raise RuntimeError(f"Expected at least 1000 recent H1 rows for {symbol}, got {len(rows)}.")
        output_dir = recent_proxy_root(p) / symbol / "H1"
        output_dir.mkdir(parents=True, exist_ok=True)
        start_token = rows[0]["bar_start_utc"][:10].replace("-", "")
        end_token = rows[-1]["bar_start_utc"][:10].replace("-", "")
        output_path = output_dir / f"{symbol}_yahoo_H1_{start_token}_{end_token}.csv"
        fieldnames = [
            "timestamp_utc",
            "bar_start_utc",
            "bar_end_utc",
            "broker",
            "symbol",
            "timeframe",
            "open",
            "high",
            "low",
            "close",
            "source",
            "acquired_at_utc",
        ]
        for row in rows:
            row["broker"] = "yahoo_recent_proxy"
            row["symbol"] = symbol
            row["timeframe"] = "H1"
            row["source"] = "Yahoo Finance chart API; public non-primary recent hourly FX proxy"
            row["acquired_at_utc"] = acquired_at
        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        manifest.append(
            {
                "symbol": symbol,
                "yahoo_symbol": yahoo_symbol,
                "timeframe": "H1",
                "rows": len(rows),
                "start_utc": rows[0]["bar_start_utc"],
                "end_utc": rows[-1]["bar_start_utc"],
                "output": relative(output_path),
                "source": "Yahoo Finance chart API; public non-primary recent hourly FX proxy",
                "acquired_at_utc": acquired_at,
            }
        )
    write_recent_proxy_acquisition_report(p, manifest)
    return manifest


def download_yahoo_h1(yahoo_symbol: str, start: datetime, end: datetime) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode(
        {
            "period1": int(start.timestamp()),
            "period2": int(end.timestamp()),
            "interval": "1h",
            "events": "history",
        }
    )
    url = f"{YAHOO_CHART_URL.format(symbol=urllib.parse.quote(yahoo_symbol, safe=''))}?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": "forex-research/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    chart = payload.get("chart", {})
    errors = chart.get("error")
    if errors:
        raise RuntimeError(f"Yahoo chart error for {yahoo_symbol}: {errors}")
    result = (chart.get("result") or [None])[0]
    if not result:
        raise RuntimeError(f"Yahoo chart returned no result for {yahoo_symbol}.")
    timestamps = result.get("timestamp") or []
    quote = result["indicators"]["quote"][0]
    rows: list[dict[str, Any]] = []
    for index, epoch in enumerate(timestamps):
        open_price = quote["open"][index]
        high = quote["high"][index]
        low = quote["low"][index]
        close = quote["close"][index]
        if None in (open_price, high, low, close):
            continue
        bar_start = datetime.fromtimestamp(int(epoch), tz=timezone.utc)
        bar_end = bar_start + timedelta(hours=1)
        rows.append(
            {
                "timestamp_utc": bar_start.isoformat().replace("+00:00", "Z"),
                "bar_start_utc": bar_start.isoformat().replace("+00:00", "Z"),
                "bar_end_utc": bar_end.isoformat().replace("+00:00", "Z"),
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
            }
        )
    return rows


def download_yahoo_daily(yahoo_symbol: str, start: datetime, end: datetime) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode(
        {
            "period1": int(start.timestamp()),
            "period2": int(end.timestamp()),
            "interval": "1d",
            "events": "history",
        }
    )
    url = f"{YAHOO_CHART_URL.format(symbol=urllib.parse.quote(yahoo_symbol, safe=''))}?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": "forex-research/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    chart = payload.get("chart", {})
    errors = chart.get("error")
    if errors:
        raise RuntimeError(f"Yahoo chart error for {yahoo_symbol}: {errors}")
    result = (chart.get("result") or [None])[0]
    if not result:
        raise RuntimeError(f"Yahoo chart returned no result for {yahoo_symbol}.")
    timestamps = result.get("timestamp") or []
    quote = result["indicators"]["quote"][0]
    rows: list[dict[str, Any]] = []
    for index, epoch in enumerate(timestamps):
        open_price = quote["open"][index]
        high = quote["high"][index]
        low = quote["low"][index]
        close = quote["close"][index]
        volume = quote.get("volume", [None] * len(timestamps))[index]
        if None in (open_price, high, low, close):
            continue
        timestamp = datetime.fromtimestamp(int(epoch), tz=timezone.utc)
        rows.append(
            {
                "timestamp_utc": timestamp.isoformat().replace("+00:00", "Z"),
                "date_utc": timestamp.date().isoformat(),
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume if volume is not None else 0,
            }
        )
    return rows


def acquire_cot_financial_reports(p: Paths, *, force: bool = False) -> list[dict[str, Any]]:
    acquired_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    output_root = cot_financial_root(p)
    output_root.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    for year in COT_FINANCIAL_YEARS:
        output_path = output_root / f"fut_fin_txt_{year}.zip"
        url = CFTC_FINANCIAL_COT_ZIP_URL.format(year=year)
        status = "existing"
        if force or not output_path.exists():
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 forex-research/1.0"})
            with urllib.request.urlopen(request, timeout=45) as response:
                payload = response.read()
            with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                if not archive.namelist():
                    raise RuntimeError(f"CFTC financial COT archive for {year} is empty: {url}")
            output_path.write_bytes(payload)
            status = "downloaded"
        summary = cot_financial_zip_summary(output_path)
        summary.update(
            {
                "year": year,
                "status": status,
                "url": url,
                "output": relative(output_path),
                "acquired_at_utc": acquired_at,
            }
        )
        manifest.append(summary)
    write_cot_financial_acquisition_report(p, manifest)
    return manifest


def cot_financial_zip_summary(path: Path) -> dict[str, Any]:
    target_markets = {str(config["market"]) for config in COT_FINANCIAL_MARKETS.values()}
    rows = 0
    target_rows = 0
    report_dates: list[pd.Timestamp] = []
    target_report_dates: list[pd.Timestamp] = []
    markets: set[str] = set()
    with zipfile.ZipFile(path) as archive:
        name = archive.namelist()[0]
        with archive.open(name) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="latin1", newline=""))
            for row in reader:
                rows += 1
                report_date = pd.to_datetime(row.get("Report_Date_as_YYYY-MM-DD"), utc=True, errors="coerce")
                if pd.notna(report_date):
                    report_dates.append(report_date)
                market = str(row.get("Market_and_Exchange_Names", "")).strip()
                if market in target_markets:
                    target_rows += 1
                    markets.add(market)
                    if pd.notna(report_date):
                        target_report_dates.append(report_date)
    return {
        "rows": rows,
        "target_rows": target_rows,
        "start_utc": iso(min(report_dates)) if report_dates else "",
        "end_utc": iso(max(report_dates)) if report_dates else "",
        "target_start_utc": iso(min(target_report_dates)) if target_report_dates else "",
        "target_end_utc": iso(max(target_report_dates)) if target_report_dates else "",
        "target_markets": sorted(markets),
    }


def write_cot_financial_acquisition_report(p: Paths, manifest: list[dict[str, Any]]) -> None:
    json_path = p.reports / f"FOREX_COT_FINANCIAL_ACQUISITION_{RUN_DATE}.json"
    json_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "CFTC_COT_FINANCIAL_ACQUIRED_RESEARCH_ONLY",
                "runtime_touched": False,
                "source": CFTC_HISTORICAL_COMPRESSED_URL,
                "rows": manifest,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    lines = [
        "# Forex CFTC Financial COT Acquisition",
        "",
        f"Generated at UTC: {datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')}",
        "Status: CFTC_COT_FINANCIAL_ACQUIRED_RESEARCH_ONLY",
        "",
        "Boundary: official CFTC archive download only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        f"Source: `{CFTC_HISTORICAL_COMPRESSED_URL}`",
        f"JSON: `{relative(json_path)}`",
        "",
        "| year | status | rows | FX target rows | target start | target end | file |",
        "| ---: | --- | ---: | ---: | --- | --- | --- |",
    ]
    for row in manifest:
        lines.append(
            "| {year} | {status} | {rows} | {target_rows} | {start} | {end} | `{output}` |".format(
                year=row["year"],
                status=row["status"],
                rows=row["rows"],
                target_rows=row["target_rows"],
                start=str(row["target_start_utc"])[:10],
                end=str(row["target_end_utc"])[:10],
                output=row["output"],
            )
        )
    lines.extend(
        [
            "",
            "Read: this is the CFTC Traders in Financial Futures futures-only archive, not the local commodity disaggregated archive. It contains the CME Euro FX and Japanese Yen contracts needed for the Forex COT screen.",
            "",
        ]
    )
    (p.reports / f"FOREX_COT_FINANCIAL_ACQUISITION_{RUN_DATE}.md").write_text("\n".join(lines), encoding="utf-8")


def acquire_recent_commodity_dollar_proxy(p: Paths) -> list[dict[str, Any]]:
    acquired_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    end_dt = datetime.now(timezone.utc) + timedelta(days=1)
    raw: dict[str, list[dict[str, Any]]] = {}
    for ticker, yahoo_symbol in YAHOO_COMMODITY_DOLLAR_SYMBOLS.items():
        rows = download_yahoo_daily(yahoo_symbol, RECENT_PROXY_START, end_dt)
        if len(rows) < 100:
            raise RuntimeError(f"Expected at least 100 recent daily rows for {ticker}, got {len(rows)}.")
        raw[ticker.lower()] = rows
    output_root = recent_commodity_proxy_root(p)
    output_root.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    for config_key, config in COMMODITY_DOLLAR_FILES.items():
        commodity = str(config["commodity"])
        dollar = str(config["dollar"])
        merged_rows = merge_yahoo_daily_pair(raw[commodity], raw[dollar], commodity, dollar, acquired_at)
        if len(merged_rows) < 100:
            raise RuntimeError(f"Expected at least 100 merged recent daily rows for {config_key}, got {len(merged_rows)}.")
        start_token = merged_rows[0]["date_utc"].replace("-", "")
        end_token = merged_rows[-1]["date_utc"].replace("-", "")
        output_path = output_root / f"{config_key}_daily_yahoo_{start_token}_{end_token}.csv"
        fieldnames = list(merged_rows[0].keys())
        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(merged_rows)
        manifest.append(
            {
                "pair": config_key,
                "commodity_symbol": commodity.upper(),
                "dollar_symbol": dollar.upper(),
                "rows": len(merged_rows),
                "start_utc": merged_rows[0]["date_utc"],
                "end_utc": merged_rows[-1]["date_utc"],
                "output": relative(output_path),
                "source": "Yahoo Finance chart API; public non-primary recent daily ETF proxy",
                "acquired_at_utc": acquired_at,
            }
        )
    write_recent_commodity_proxy_acquisition_report(p, manifest)
    return manifest


def acquire_recent_real_asset_rotation_proxy(p: Paths) -> list[dict[str, Any]]:
    acquired_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    end_dt = datetime.now(timezone.utc) + timedelta(days=1)
    raw: dict[str, list[dict[str, Any]]] = {}
    for ticker, yahoo_symbol in YAHOO_REAL_ASSET_ROTATION_SYMBOLS.items():
        rows = download_yahoo_daily(yahoo_symbol, RECENT_PROXY_START, end_dt)
        if len(rows) < 100:
            raise RuntimeError(f"Expected at least 100 recent daily rows for {ticker}, got {len(rows)}.")
        raw[ticker.lower()] = rows
    output_root = recent_real_asset_rotation_proxy_root(p)
    output_root.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    for config_key, config in REAL_ASSET_ROTATION_FILES.items():
        left = str(config["left"])
        right = str(config["right"])
        merged_rows = merge_yahoo_daily_pair(raw[left], raw[right], left, right, acquired_at)
        if len(merged_rows) < 100:
            raise RuntimeError(f"Expected at least 100 merged recent daily rows for {config_key}, got {len(merged_rows)}.")
        start_token = merged_rows[0]["date_utc"].replace("-", "")
        end_token = merged_rows[-1]["date_utc"].replace("-", "")
        output_path = output_root / f"{config_key}_daily_yahoo_{start_token}_{end_token}.csv"
        fieldnames = list(merged_rows[0].keys())
        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(merged_rows)
        manifest.append(
            {
                "pair": config_key,
                "left_symbol": left.upper(),
                "right_symbol": right.upper(),
                "rows": len(merged_rows),
                "start_utc": merged_rows[0]["date_utc"],
                "end_utc": merged_rows[-1]["date_utc"],
                "output": relative(output_path),
                "source": "Yahoo Finance chart API; public non-primary recent daily ETF/futures proxy",
                "acquired_at_utc": acquired_at,
            }
        )
    write_recent_real_asset_rotation_proxy_acquisition_report(p, manifest)
    return manifest


def acquire_recent_haven_liquidity_proxy(p: Paths) -> list[dict[str, Any]]:
    acquired_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    end_dt = datetime.now(timezone.utc) + timedelta(days=1)
    raw: dict[str, list[dict[str, Any]]] = {}
    for ticker, yahoo_symbol in YAHOO_HAVEN_LIQUIDITY_SYMBOLS.items():
        rows = download_yahoo_daily(yahoo_symbol, RECENT_PROXY_START, end_dt)
        if len(rows) < 100:
            raise RuntimeError(f"Expected at least 100 recent daily rows for {ticker}, got {len(rows)}.")
        raw[ticker.lower()] = rows
    output_root = recent_haven_liquidity_proxy_root(p)
    output_root.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    gld_rows = raw["gld"]
    formatted_gld = []
    for row in gld_rows:
        enriched = dict(row)
        enriched["source_symbol"] = "GLD"
        enriched["source"] = "Yahoo Finance chart API; public non-primary recent daily GLD ETF proxy"
        enriched["acquired_at_utc"] = acquired_at
        formatted_gld.append(enriched)
    start_token = formatted_gld[0]["date_utc"].replace("-", "")
    end_token = formatted_gld[-1]["date_utc"].replace("-", "")
    gld_output = output_root / f"gld_daily_yahoo_{start_token}_{end_token}.csv"
    with gld_output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(formatted_gld[0].keys()))
        writer.writeheader()
        writer.writerows(formatted_gld)
    manifest.append(
        {
            "series": "gld",
            "symbols": "GLD",
            "rows": len(formatted_gld),
            "start_utc": formatted_gld[0]["date_utc"],
            "end_utc": formatted_gld[-1]["date_utc"],
            "output": relative(gld_output),
            "source": "Yahoo Finance chart API; public non-primary recent daily ETF proxy",
            "acquired_at_utc": acquired_at,
        }
    )
    for config_key, config in HAVEN_LIQUIDITY_FILES.items():
        if config["kind"] != "pair":
            continue
        left = str(config["left"])
        right = str(config["right"])
        merged_rows = merge_yahoo_daily_pair(raw[left], raw[right], left, right, acquired_at)
        if len(merged_rows) < 100:
            raise RuntimeError(f"Expected at least 100 merged recent daily rows for {config_key}, got {len(merged_rows)}.")
        start_token = merged_rows[0]["date_utc"].replace("-", "")
        end_token = merged_rows[-1]["date_utc"].replace("-", "")
        output_path = output_root / f"{config_key}_daily_yahoo_{start_token}_{end_token}.csv"
        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(merged_rows[0].keys()))
            writer.writeheader()
            writer.writerows(merged_rows)
        manifest.append(
            {
                "series": config_key,
                "symbols": f"{left.upper()}/{right.upper()}",
                "rows": len(merged_rows),
                "start_utc": merged_rows[0]["date_utc"],
                "end_utc": merged_rows[-1]["date_utc"],
                "output": relative(output_path),
                "source": "Yahoo Finance chart API; public non-primary recent daily ETF proxy",
                "acquired_at_utc": acquired_at,
            }
        )
    write_recent_haven_liquidity_proxy_acquisition_report(p, manifest)
    return manifest


def acquire_recent_rates_dollar_proxy(p: Paths) -> list[dict[str, Any]]:
    acquired_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    end_dt = datetime.now(timezone.utc) + timedelta(days=1)
    raw: dict[str, list[dict[str, Any]]] = {}
    for ticker, yahoo_symbol in YAHOO_RATES_DOLLAR_SYMBOLS.items():
        rows = download_yahoo_daily(yahoo_symbol, RECENT_PROXY_START, end_dt)
        if len(rows) < 100:
            raise RuntimeError(f"Expected at least 100 recent daily rows for {ticker}, got {len(rows)}.")
        raw[ticker.lower()] = rows
    output_root = recent_rates_proxy_root(p)
    output_root.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    for config_key, config in RATES_DOLLAR_FILES.items():
        duration = str(config["duration"])
        denominator = str(config.get("dollar") or config.get("cash"))
        merged_rows = merge_yahoo_daily_pair(raw[duration], raw[denominator], duration, denominator, acquired_at)
        if len(merged_rows) < 100:
            raise RuntimeError(f"Expected at least 100 merged recent daily rows for {config_key}, got {len(merged_rows)}.")
        start_token = merged_rows[0]["date_utc"].replace("-", "")
        end_token = merged_rows[-1]["date_utc"].replace("-", "")
        output_path = output_root / f"{config_key}_daily_yahoo_{start_token}_{end_token}.csv"
        fieldnames = list(merged_rows[0].keys())
        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(merged_rows)
        manifest.append(
            {
                "pair": config_key,
                "duration_symbol": duration.upper(),
                "denominator_symbol": denominator.upper(),
                "rows": len(merged_rows),
                "start_utc": merged_rows[0]["date_utc"],
                "end_utc": merged_rows[-1]["date_utc"],
                "output": relative(output_path),
                "source": "Yahoo Finance chart API; public non-primary recent daily ETF proxy",
                "acquired_at_utc": acquired_at,
            }
        )
    write_recent_rates_proxy_acquisition_report(p, manifest)
    return manifest


def acquire_recent_equity_leadership_proxy(p: Paths) -> list[dict[str, Any]]:
    acquired_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    end_dt = datetime.now(timezone.utc) + timedelta(days=1)
    raw: dict[str, list[dict[str, Any]]] = {}
    for ticker, yahoo_symbol in YAHOO_EQUITY_LEADERSHIP_SYMBOLS.items():
        rows = download_yahoo_daily(yahoo_symbol, RECENT_PROXY_START, end_dt)
        if len(rows) < 100:
            raise RuntimeError(f"Expected at least 100 recent daily rows for {ticker}, got {len(rows)}.")
        raw[ticker.lower()] = rows
    output_root = recent_equity_leadership_proxy_root(p)
    output_root.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    for config_key, config in EQUITY_LEADERSHIP_FILES.items():
        leader = str(config["leader"])
        benchmark = str(config["benchmark"])
        merged_rows = merge_yahoo_daily_pair(raw[leader], raw[benchmark], leader, benchmark, acquired_at)
        if len(merged_rows) < 100:
            raise RuntimeError(f"Expected at least 100 merged recent daily rows for {config_key}, got {len(merged_rows)}.")
        start_token = merged_rows[0]["date_utc"].replace("-", "")
        end_token = merged_rows[-1]["date_utc"].replace("-", "")
        output_path = output_root / f"{config_key}_daily_yahoo_{start_token}_{end_token}.csv"
        fieldnames = list(merged_rows[0].keys())
        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(merged_rows)
        manifest.append(
            {
                "pair": config_key,
                "leader_symbol": leader.upper(),
                "benchmark_symbol": benchmark.upper(),
                "rows": len(merged_rows),
                "start_utc": merged_rows[0]["date_utc"],
                "end_utc": merged_rows[-1]["date_utc"],
                "output": relative(output_path),
                "source": "Yahoo Finance chart API; public non-primary recent daily ETF proxy",
                "acquired_at_utc": acquired_at,
            }
        )
    write_recent_equity_leadership_proxy_acquisition_report(p, manifest)
    return manifest


def acquire_recent_sector_rotation_proxy(p: Paths) -> list[dict[str, Any]]:
    acquired_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    end_dt = datetime.now(timezone.utc) + timedelta(days=1)
    raw: dict[str, list[dict[str, Any]]] = {}
    for ticker, yahoo_symbol in YAHOO_SECTOR_ROTATION_SYMBOLS.items():
        rows = download_yahoo_daily(yahoo_symbol, RECENT_PROXY_START, end_dt)
        if len(rows) < 100:
            raise RuntimeError(f"Expected at least 100 recent daily rows for {ticker}, got {len(rows)}.")
        raw[ticker.lower()] = rows
    output_root = recent_sector_rotation_proxy_root(p)
    output_root.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    for config_key, config in SECTOR_ROTATION_FILES.items():
        leader = str(config["leader"])
        benchmark = str(config["benchmark"])
        merged_rows = merge_yahoo_daily_pair(raw[leader], raw[benchmark], leader, benchmark, acquired_at)
        if len(merged_rows) < 100:
            raise RuntimeError(f"Expected at least 100 merged recent daily rows for {config_key}, got {len(merged_rows)}.")
        start_token = merged_rows[0]["date_utc"].replace("-", "")
        end_token = merged_rows[-1]["date_utc"].replace("-", "")
        output_path = output_root / f"{config_key}_daily_yahoo_{start_token}_{end_token}.csv"
        fieldnames = list(merged_rows[0].keys())
        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(merged_rows)
        manifest.append(
            {
                "pair": config_key,
                "leader_symbol": leader.upper(),
                "benchmark_symbol": benchmark.upper(),
                "rows": len(merged_rows),
                "start_utc": merged_rows[0]["date_utc"],
                "end_utc": merged_rows[-1]["date_utc"],
                "output": relative(output_path),
                "source": "Yahoo Finance chart API; public non-primary recent daily ETF proxy",
                "acquired_at_utc": acquired_at,
            }
        )
    write_recent_sector_rotation_proxy_acquisition_report(p, manifest)
    return manifest


def acquire_recent_currency_basket_proxy(p: Paths) -> list[dict[str, Any]]:
    acquired_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    end_dt = datetime.now(timezone.utc) + timedelta(days=1)
    raw: dict[str, list[dict[str, Any]]] = {}
    manifest: list[dict[str, Any]] = []
    for ticker, yahoo_symbol in YAHOO_CURRENCY_BASKET_SYMBOLS.items():
        rows = download_yahoo_daily(yahoo_symbol, RECENT_PROXY_START, end_dt)
        if len(rows) < 100:
            manifest.append(
                {
                    "pair": ticker.lower(),
                    "currency_symbol": ticker.upper(),
                    "dollar_symbol": "",
                    "rows": len(rows),
                    "start_utc": rows[0]["date_utc"] if rows else "",
                    "end_utc": rows[-1]["date_utc"] if rows else "",
                    "output": "",
                    "status": "UNAVAILABLE_RECENT_PROXY",
                    "error": f"expected_at_least_100_daily_rows_got_{len(rows)}",
                    "source": "Yahoo Finance chart API; public non-primary recent daily currency ETF proxy",
                    "acquired_at_utc": acquired_at,
                }
            )
            continue
        raw[ticker.lower()] = rows
    output_root = recent_currency_basket_proxy_root(p)
    output_root.mkdir(parents=True, exist_ok=True)
    for config_key, config in CURRENCY_BASKET_FILES.items():
        currency = str(config["currency"])
        dollar = str(config["dollar"])
        missing_components = [name.upper() for name in (currency, dollar) if name not in raw]
        if missing_components:
            manifest.append(
                {
                    "pair": config_key,
                    "currency_symbol": currency.upper(),
                    "dollar_symbol": dollar.upper(),
                    "rows": 0,
                    "start_utc": "",
                    "end_utc": "",
                    "output": "",
                    "status": "SKIPPED_MISSING_COMPONENT",
                    "error": "missing_recent_symbol:" + ",".join(missing_components),
                    "source": "Yahoo Finance chart API; public non-primary recent daily currency ETF proxy",
                    "acquired_at_utc": acquired_at,
                }
            )
            continue
        merged_rows = merge_yahoo_daily_pair(raw[currency], raw[dollar], currency, dollar, acquired_at)
        if len(merged_rows) < 100:
            manifest.append(
                {
                    "pair": config_key,
                    "currency_symbol": currency.upper(),
                    "dollar_symbol": dollar.upper(),
                    "rows": len(merged_rows),
                    "start_utc": merged_rows[0]["date_utc"] if merged_rows else "",
                    "end_utc": merged_rows[-1]["date_utc"] if merged_rows else "",
                    "output": "",
                    "status": "SKIPPED_LOW_MERGED_ROWS",
                    "error": f"expected_at_least_100_merged_daily_rows_got_{len(merged_rows)}",
                    "source": "Yahoo Finance chart API; public non-primary recent daily currency ETF proxy",
                    "acquired_at_utc": acquired_at,
                }
            )
            continue
        start_token = merged_rows[0]["date_utc"].replace("-", "")
        end_token = merged_rows[-1]["date_utc"].replace("-", "")
        output_path = output_root / f"{config_key}_daily_yahoo_{start_token}_{end_token}.csv"
        fieldnames = list(merged_rows[0].keys())
        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(merged_rows)
        manifest.append(
            {
                "pair": config_key,
                "currency_symbol": currency.upper(),
                "dollar_symbol": dollar.upper(),
                "rows": len(merged_rows),
                "start_utc": merged_rows[0]["date_utc"],
                "end_utc": merged_rows[-1]["date_utc"],
                "output": relative(output_path),
                "status": "ACQUIRED",
                "error": "",
                "source": "Yahoo Finance chart API; public non-primary recent daily currency ETF proxy",
                "acquired_at_utc": acquired_at,
            }
        )
    write_recent_currency_basket_proxy_acquisition_report(p, manifest)
    return manifest


def acquire_recent_bond_vol_proxy(p: Paths) -> list[dict[str, Any]]:
    acquired_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    end_dt = datetime.now(timezone.utc) + timedelta(days=1)
    output_root = recent_bond_vol_proxy_root(p)
    output_root.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    for name, yahoo_symbol in YAHOO_BOND_VOL_SYMBOLS.items():
        rows = download_yahoo_daily(yahoo_symbol, RECENT_PROXY_START, end_dt)
        if len(rows) < 100:
            raise RuntimeError(f"Expected at least 100 recent daily rows for {name}, got {len(rows)}.")
        symbol = name.lower()
        formatted = [
            {
                "timestamp_utc": row["timestamp_utc"],
                "date_utc": row["date_utc"],
                f"{symbol}_open": row["open"],
                f"{symbol}_high": row["high"],
                f"{symbol}_low": row["low"],
                f"{symbol}_close": row["close"],
                f"{symbol}_volume": row["volume"],
                "source": "Yahoo Finance chart API; public non-primary recent daily bond-volatility proxy",
                "acquired_at_utc": acquired_at,
            }
            for row in rows
        ]
        start_token = formatted[0]["date_utc"].replace("-", "")
        end_token = formatted[-1]["date_utc"].replace("-", "")
        output_path = output_root / f"{symbol}_daily_yahoo_{start_token}_{end_token}.csv"
        fieldnames = list(formatted[0].keys())
        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(formatted)
        manifest.append(
            {
                "series": symbol,
                "yahoo_symbol": yahoo_symbol,
                "rows": len(formatted),
                "start_utc": formatted[0]["date_utc"],
                "end_utc": formatted[-1]["date_utc"],
                "output": relative(output_path),
                "source": "Yahoo Finance chart API; public non-primary recent daily bond-volatility proxy",
                "acquired_at_utc": acquired_at,
            }
        )
    write_recent_bond_vol_proxy_acquisition_report(p, manifest)
    return manifest


def acquire_recent_crypto_risk_proxy(p: Paths) -> list[dict[str, Any]]:
    acquired_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    end_dt = datetime.now(timezone.utc) + timedelta(days=1)
    output_root = recent_crypto_risk_proxy_root(p)
    output_root.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    for name, yahoo_symbol in YAHOO_CRYPTO_RISK_SYMBOLS.items():
        rows = download_yahoo_daily(yahoo_symbol, RECENT_PROXY_START, end_dt)
        if len(rows) < 100:
            raise RuntimeError(f"Expected at least 100 recent daily rows for {name}, got {len(rows)}.")
        symbol = name.lower()
        formatted = [
            {
                "timestamp_utc": row["timestamp_utc"],
                "date_utc": row["date_utc"],
                f"{symbol}_open": row["open"],
                f"{symbol}_high": row["high"],
                f"{symbol}_low": row["low"],
                f"{symbol}_close": row["close"],
                f"{symbol}_volume": row["volume"],
                "source": "Yahoo Finance chart API; public non-primary recent daily crypto-risk proxy",
                "acquired_at_utc": acquired_at,
            }
            for row in rows
        ]
        start_token = formatted[0]["date_utc"].replace("-", "")
        end_token = formatted[-1]["date_utc"].replace("-", "")
        output_path = output_root / f"{symbol}_usd_daily_yahoo_{start_token}_{end_token}.csv"
        fieldnames = list(formatted[0].keys())
        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(formatted)
        manifest.append(
            {
                "series": symbol,
                "yahoo_symbol": yahoo_symbol,
                "rows": len(formatted),
                "start_utc": formatted[0]["date_utc"],
                "end_utc": formatted[-1]["date_utc"],
                "output": relative(output_path),
                "source": "Yahoo Finance chart API; public non-primary recent daily crypto-risk proxy",
                "acquired_at_utc": acquired_at,
            }
        )
    write_recent_crypto_risk_proxy_acquisition_report(p, manifest)
    return manifest


def merge_yahoo_daily_pair(
    left_rows: list[dict[str, Any]],
    right_rows: list[dict[str, Any]],
    left_name: str,
    right_name: str,
    acquired_at: str,
) -> list[dict[str, Any]]:
    left_by_date = {str(row["date_utc"]): row for row in left_rows}
    right_by_date = {str(row["date_utc"]): row for row in right_rows}
    merged: list[dict[str, Any]] = []
    for date in sorted(set(left_by_date).intersection(right_by_date)):
        left = left_by_date[date]
        right = right_by_date[date]
        row = {
            "timestamp_utc": left["timestamp_utc"],
            "date_utc": date,
            f"{left_name}_open": left["open"],
            f"{left_name}_high": left["high"],
            f"{left_name}_low": left["low"],
            f"{left_name}_close": left["close"],
            f"{left_name}_volume": left["volume"],
            f"{right_name}_open": right["open"],
            f"{right_name}_high": right["high"],
            f"{right_name}_low": right["low"],
            f"{right_name}_close": right["close"],
            f"{right_name}_volume": right["volume"],
            "source": "Yahoo Finance chart API; public non-primary recent daily ETF proxy",
            "acquired_at_utc": acquired_at,
        }
        merged.append(row)
    return merged


def write_recent_commodity_proxy_acquisition_report(p: Paths, manifest: list[dict[str, Any]]) -> None:
    manifest_path = p.reports / f"FOREX_RECENT_COMMODITY_DOLLAR_PROXY_ACQUISITION_{RUN_DATE}.json"
    manifest_path.write_text(json.dumps({"rows": manifest}, indent=2), encoding="utf-8")
    lines = [
        "# Forex Recent Commodity/Dollar Proxy Acquisition",
        "",
        f"Generated at UTC: {datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')}",
        "Status: RESEARCH_ONLY_PROXY_DATA",
        "",
        "Boundary: public web data acquisition only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Source: Yahoo Finance chart API public ETF proxy symbols. These bars are not broker-authoritative and do not include Forex broker spread; recent stress reports use historical Capital.com spread proxies where available.",
        "",
        f"Manifest JSON: `{relative(manifest_path)}`",
        "",
        "| pair | symbols | rows | start_utc | end_utc | output |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for row in manifest:
        lines.append(
            f"| {row['pair']} | {row['commodity_symbol']}/{row['dollar_symbol']} | {row['rows']} | {row['start_utc']} | {row['end_utc']} | `{row['output']}` |"
        )
    lines.append("")
    (p.reports / f"FOREX_RECENT_COMMODITY_DOLLAR_PROXY_ACQUISITION_{RUN_DATE}.md").write_text("\n".join(lines), encoding="utf-8")


def write_recent_real_asset_rotation_proxy_acquisition_report(p: Paths, manifest: list[dict[str, Any]]) -> None:
    manifest_path = p.reports / f"FOREX_RECENT_REAL_ASSET_ROTATION_PROXY_ACQUISITION_{RUN_DATE}.json"
    manifest_path.write_text(json.dumps({"rows": manifest}, indent=2), encoding="utf-8")
    lines = [
        "# Forex Recent Real-Asset Rotation Proxy Acquisition",
        "",
        f"Generated at UTC: {datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')}",
        "Status: RESEARCH_ONLY_PROXY_DATA",
        "",
        "Boundary: public web data acquisition only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Source: Yahoo Finance chart API public ETF/futures proxy symbols. These bars are not broker-authoritative and do not include Forex broker spread; recent stress reports use historical Capital.com spread proxies where available.",
        "",
        f"Manifest JSON: `{relative(manifest_path)}`",
        "",
        "| pair | symbols | rows | start_utc | end_utc | output |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for row in manifest:
        lines.append(
            f"| {row['pair']} | {row['left_symbol']}/{row['right_symbol']} | {row['rows']} | {row['start_utc']} | {row['end_utc']} | `{row['output']}` |"
        )
    lines.append("")
    (p.reports / f"FOREX_RECENT_REAL_ASSET_ROTATION_PROXY_ACQUISITION_{RUN_DATE}.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def write_recent_haven_liquidity_proxy_acquisition_report(p: Paths, manifest: list[dict[str, Any]]) -> None:
    manifest_path = p.reports / f"FOREX_RECENT_HAVEN_LIQUIDITY_PROXY_ACQUISITION_{RUN_DATE}.json"
    manifest_path.write_text(json.dumps({"rows": manifest}, indent=2), encoding="utf-8")
    lines = [
        "# Forex Recent Haven/Liquidity Proxy Acquisition",
        "",
        f"Generated at UTC: {datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')}",
        "Status: RESEARCH_ONLY_PROXY_DATA",
        "",
        "Boundary: public web data acquisition only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Source: Yahoo Finance chart API public ETF proxy symbols. These bars are not broker-authoritative and do not include Forex broker spread; recent stress reports use historical Capital.com spread proxies where available.",
        "",
        f"Manifest JSON: `{relative(manifest_path)}`",
        "",
        "| series | symbols | rows | start_utc | end_utc | output |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for row in manifest:
        lines.append(
            f"| {row['series']} | {row['symbols']} | {row['rows']} | {row['start_utc']} | {row['end_utc']} | `{row['output']}` |"
        )
    lines.append("")
    (p.reports / f"FOREX_RECENT_HAVEN_LIQUIDITY_PROXY_ACQUISITION_{RUN_DATE}.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def write_recent_rates_proxy_acquisition_report(p: Paths, manifest: list[dict[str, Any]]) -> None:
    manifest_path = p.reports / f"FOREX_RECENT_RATES_DOLLAR_PROXY_ACQUISITION_{RUN_DATE}.json"
    manifest_path.write_text(json.dumps({"rows": manifest}, indent=2), encoding="utf-8")
    lines = [
        "# Forex Recent Rates/Dollar Proxy Acquisition",
        "",
        f"Generated at UTC: {datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')}",
        "Status: RESEARCH_ONLY_PROXY_DATA",
        "",
        "Boundary: public web data acquisition only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Source: Yahoo Finance chart API public ETF proxy symbols. These bars are not broker-authoritative and do not include Forex broker spread; recent stress reports use historical Capital.com spread proxies where available.",
        "",
        f"Manifest JSON: `{relative(manifest_path)}`",
        "",
        "| pair | symbols | rows | start_utc | end_utc | output |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for row in manifest:
        lines.append(
            f"| {row['pair']} | {row['duration_symbol']}/{row['denominator_symbol']} | {row['rows']} | {row['start_utc']} | {row['end_utc']} | `{row['output']}` |"
        )
    lines.append("")
    (p.reports / f"FOREX_RECENT_RATES_DOLLAR_PROXY_ACQUISITION_{RUN_DATE}.md").write_text("\n".join(lines), encoding="utf-8")


def write_recent_equity_leadership_proxy_acquisition_report(p: Paths, manifest: list[dict[str, Any]]) -> None:
    manifest_path = p.reports / f"FOREX_RECENT_EQUITY_LEADERSHIP_PROXY_ACQUISITION_{RUN_DATE}.json"
    manifest_path.write_text(json.dumps({"rows": manifest}, indent=2), encoding="utf-8")
    lines = [
        "# Forex Recent Equity-Leadership Proxy Acquisition",
        "",
        f"Generated at UTC: {datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')}",
        "Status: RESEARCH_ONLY_PROXY_DATA",
        "",
        "Boundary: public web data acquisition only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Source: Yahoo Finance chart API public ETF proxy symbols. These bars are not broker-authoritative and do not include Forex broker spread; recent stress reports use historical Capital.com spread proxies where available.",
        "",
        f"Manifest JSON: `{relative(manifest_path)}`",
        "",
        "| pair | symbols | rows | start_utc | end_utc | output |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for row in manifest:
        lines.append(
            f"| {row['pair']} | {row['leader_symbol']}/{row['benchmark_symbol']} | {row['rows']} | {row['start_utc']} | {row['end_utc']} | `{row['output']}` |"
        )
    lines.append("")
    (p.reports / f"FOREX_RECENT_EQUITY_LEADERSHIP_PROXY_ACQUISITION_{RUN_DATE}.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def write_recent_sector_rotation_proxy_acquisition_report(p: Paths, manifest: list[dict[str, Any]]) -> None:
    manifest_path = p.reports / f"FOREX_RECENT_SECTOR_ROTATION_PROXY_ACQUISITION_{RUN_DATE}.json"
    manifest_path.write_text(json.dumps({"rows": manifest}, indent=2), encoding="utf-8")
    lines = [
        "# Forex Recent Sector-Rotation Proxy Acquisition",
        "",
        f"Generated at UTC: {datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')}",
        "Status: RESEARCH_ONLY_PROXY_DATA",
        "",
        "Boundary: public web data acquisition only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Source: Yahoo Finance chart API public ETF proxy symbols. These bars are not broker-authoritative and do not include Forex broker spread; recent stress reports use historical Capital.com spread proxies where available.",
        "",
        f"Manifest JSON: `{relative(manifest_path)}`",
        "",
        "| pair | symbols | rows | start_utc | end_utc | output |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for row in manifest:
        lines.append(
            f"| {row['pair']} | {row['leader_symbol']}/{row['benchmark_symbol']} | {row['rows']} | {row['start_utc']} | {row['end_utc']} | `{row['output']}` |"
        )
    lines.append("")
    (p.reports / f"FOREX_RECENT_SECTOR_ROTATION_PROXY_ACQUISITION_{RUN_DATE}.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def write_recent_currency_basket_proxy_acquisition_report(p: Paths, manifest: list[dict[str, Any]]) -> None:
    manifest_path = p.reports / f"FOREX_RECENT_CURRENCY_BASKET_PROXY_ACQUISITION_{RUN_DATE}.json"
    manifest_path.write_text(json.dumps({"rows": manifest}, indent=2), encoding="utf-8")
    lines = [
        "# Forex Recent Currency-Basket Proxy Acquisition",
        "",
        f"Generated at UTC: {datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')}",
        "Status: RESEARCH_ONLY_PROXY_DATA",
        "",
        "Boundary: public web data acquisition only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Source: Yahoo Finance chart API public currency ETF proxy symbols. These bars are not broker-authoritative and do not include Forex broker spread; recent stress reports use historical Capital.com spread proxies where available.",
        "",
        f"Manifest JSON: `{relative(manifest_path)}`",
        "",
        "| status | pair | symbols | rows | start_utc | end_utc | output | error |",
        "| --- | --- | --- | ---: | --- | --- | --- | --- |",
    ]
    for row in manifest:
        lines.append(
            f"| {row.get('status', 'ACQUIRED')} | {row['pair']} | {row['currency_symbol']}/{row['dollar_symbol']} | {row['rows']} | {row['start_utc']} | {row['end_utc']} | `{row['output']}` | {row.get('error', '')} |"
        )
    lines.append("")
    (p.reports / f"FOREX_RECENT_CURRENCY_BASKET_PROXY_ACQUISITION_{RUN_DATE}.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def write_recent_bond_vol_proxy_acquisition_report(p: Paths, manifest: list[dict[str, Any]]) -> None:
    manifest_path = p.reports / f"FOREX_RECENT_BOND_VOL_PROXY_ACQUISITION_{RUN_DATE}.json"
    manifest_path.write_text(json.dumps({"rows": manifest}, indent=2), encoding="utf-8")
    lines = [
        "# Forex Recent Bond-Vol Proxy Acquisition",
        "",
        f"Generated at UTC: {datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')}",
        "Status: RESEARCH_ONLY_PROXY_DATA",
        "",
        "Boundary: public web data acquisition only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Source: Yahoo Finance chart API public MOVE bond-volatility proxy. These bars are not broker-authoritative and do not include Forex broker spread; recent stress reports use historical Capital.com spread proxies where available.",
        "",
        f"Manifest JSON: `{relative(manifest_path)}`",
        "",
        "| series | yahoo_symbol | rows | start_utc | end_utc | output |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for row in manifest:
        lines.append(
            f"| {row['series']} | {row['yahoo_symbol']} | {row['rows']} | {row['start_utc']} | {row['end_utc']} | `{row['output']}` |"
        )
    lines.append("")
    (p.reports / f"FOREX_RECENT_BOND_VOL_PROXY_ACQUISITION_{RUN_DATE}.md").write_text("\n".join(lines), encoding="utf-8")


def write_recent_crypto_risk_proxy_acquisition_report(p: Paths, manifest: list[dict[str, Any]]) -> None:
    manifest_path = p.reports / f"FOREX_RECENT_CRYPTO_RISK_PROXY_ACQUISITION_{RUN_DATE}.json"
    manifest_path.write_text(json.dumps({"rows": manifest}, indent=2), encoding="utf-8")
    lines = [
        "# Forex Recent Crypto-Risk Proxy Acquisition",
        "",
        f"Generated at UTC: {datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')}",
        "Status: RESEARCH_ONLY_PROXY_DATA",
        "",
        "Boundary: public web data acquisition only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Source: Yahoo Finance chart API public BTC-USD crypto-risk proxy. These bars are not broker-authoritative FX evidence and do not include Forex broker spread; recent stress reports use historical Capital.com spread proxies where available.",
        "",
        f"Manifest JSON: `{relative(manifest_path)}`",
        "",
        "| series | yahoo_symbol | rows | start_utc | end_utc | output |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for row in manifest:
        lines.append(
            f"| {row['series']} | {row['yahoo_symbol']} | {row['rows']} | {row['start_utc']} | {row['end_utc']} | `{row['output']}` |"
        )
    lines.append("")
    (p.reports / f"FOREX_RECENT_CRYPTO_RISK_PROXY_ACQUISITION_{RUN_DATE}.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def write_recent_proxy_acquisition_report(p: Paths, manifest: list[dict[str, Any]]) -> None:
    manifest_path = p.reports / f"FOREX_RECENT_YAHOO_PROXY_ACQUISITION_{RUN_DATE}.json"
    manifest_path.write_text(json.dumps({"rows": manifest}, indent=2), encoding="utf-8")
    lines = [
        "# Forex Recent Yahoo Proxy Acquisition",
        "",
        f"Generated at UTC: {datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')}",
        "Status: RESEARCH_ONLY_PROXY_DATA",
        "",
        "Boundary: public web data acquisition only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Source: Yahoo Finance chart API public FX proxy symbols. These bars are not broker-authoritative and do not include broker spread; recency stress reports use historical Capital.com spread proxies where available.",
        "",
        f"Manifest JSON: `{relative(manifest_path)}`",
        "",
        "| symbol | yahoo_symbol | timeframe | rows | start_utc | end_utc | output |",
        "| --- | --- | --- | ---: | --- | --- | --- |",
    ]
    for row in manifest:
        lines.append(
            f"| {row['symbol']} | {row['yahoo_symbol']} | {row['timeframe']} | {row['rows']} | {row['start_utc'][:10]} | {row['end_utc'][:10]} | `{row['output']}` |"
        )
    lines.append("")
    (p.reports / f"FOREX_RECENT_YAHOO_PROXY_ACQUISITION_{RUN_DATE}.md").write_text("\n".join(lines), encoding="utf-8")


def validate_broker_refresh(p: Paths) -> list[dict[str, Any]]:
    raw_root = broker_refresh_raw_root(p)
    csv_files = sorted(raw_root.glob("*/*/*/*.csv"))
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    results: list[dict[str, Any]] = []
    for path in csv_files:
        results.append(validate_broker_refresh_file(p, path, generated_at))
    write_broker_refresh_validation_outputs(p, results, generated_at)
    return results


def validate_broker_refresh_file(p: Paths, path: Path, generated_at: str) -> dict[str, Any]:
    raw_root = broker_refresh_raw_root(p)
    broker, symbol, timeframe = infer_broker_refresh_metadata(raw_root, path)
    errors: list[str] = []
    warnings: list[str] = []
    row: dict[str, Any] = {
        "source_file": relative(path),
        "sha256": file_sha256(path),
        "normalized_sha256": "",
        "broker": broker,
        "symbol": symbol,
        "timeframe": timeframe,
        "provenance_status": "",
        "provenance_source": "",
        "rows": 0,
        "start_utc": "",
        "end_utc": "",
        "duplicate_timestamps": 0,
        "gap_count": 0,
        "max_gap_minutes": "",
        "spread_median_points_median": "",
        "spread_p95_points_median": "",
        "normalized_output": "",
        "status": "FAIL_VALIDATION",
        "errors": "",
        "warnings": "",
    }
    for field in BROKER_REFRESH_PROVENANCE_FIELDS:
        row[field] = ""
    if symbol not in FOREX_SYMBOLS:
        errors.append(f"unsupported_symbol:{symbol}")
    if timeframe not in TIMEFRAME_DELTAS:
        errors.append(f"unsupported_timeframe:{timeframe}")
    try:
        frame = pd.read_csv(path)
    except Exception as exc:  # pragma: no cover - defensive for corrupt user files
        errors.append(f"csv_read_error:{type(exc).__name__}:{exc}")
        row["errors"] = ";".join(errors)
        return row

    provenance, provenance_source, provenance_warnings = extract_broker_refresh_provenance(path, frame)
    row.update(provenance)
    row["provenance_source"] = provenance_source
    if provenance["export_terminal"] and (provenance["export_account_login"] or provenance["export_account_server"]):
        row["provenance_status"] = "PROVENANCE_COMPLETE"
    elif any(provenance.values()):
        row["provenance_status"] = "PROVENANCE_PARTIAL"
        provenance_warnings.append("partial_export_terminal_account_provenance")
    else:
        row["provenance_status"] = "PROVENANCE_MISSING"
        provenance_warnings.append("missing_export_terminal_account_provenance")
    warnings.extend(provenance_warnings)

    timestamp_column = "timestamp_utc" if "timestamp_utc" in frame.columns else "bar_start_utc" if "bar_start_utc" in frame.columns else ""
    required = {"open", "high", "low", "close", "spread_median_points"}
    if not timestamp_column:
        errors.append("missing_timestamp_utc_or_bar_start_utc")
    missing = sorted(required.difference(frame.columns))
    if missing:
        errors.append("missing_columns:" + ",".join(missing))
    if errors:
        row["rows"] = len(frame)
        row["errors"] = ";".join(errors)
        return row

    normalized = pd.DataFrame()
    normalized["timestamp_utc"] = pd.to_datetime(frame[timestamp_column], utc=True, errors="coerce")
    normalized["bar_start_utc"] = normalized["timestamp_utc"]
    delta = TIMEFRAME_DELTAS.get(timeframe, pd.Timedelta(0))
    normalized["bar_end_utc"] = normalized["bar_start_utc"] + delta
    normalized["broker"] = broker
    normalized["symbol"] = symbol
    normalized["timeframe"] = timeframe
    for column in ("open", "high", "low", "close", "spread_median_points"):
        normalized[column] = pd.to_numeric(frame[column], errors="coerce")
    for column in ("spread_p95_points", "tick_count", "volume_sum"):
        if column in frame.columns:
            normalized[column] = pd.to_numeric(frame[column], errors="coerce")
        else:
            normalized[column] = pd.NA
            warnings.append(f"missing_optional_column:{column}")
    normalized["source_file"] = relative(path)
    normalized["source_sha256"] = row["sha256"]
    normalized["validated_at_utc"] = generated_at
    normalized["provenance_status"] = row["provenance_status"]
    normalized["provenance_source"] = row["provenance_source"]
    for field in BROKER_REFRESH_PROVENANCE_FIELDS:
        normalized[field] = row[field]

    before_drop = len(normalized)
    normalized = normalized.dropna(subset=["timestamp_utc", "open", "high", "low", "close", "spread_median_points"])
    dropped = before_drop - len(normalized)
    if dropped:
        warnings.append(f"dropped_unparseable_rows:{dropped}")
    if normalized.empty:
        errors.append("no_valid_rows_after_parse")
    if not errors:
        bad_ohlc = normalized[
            (normalized["high"] < normalized[["open", "low", "close"]].max(axis=1))
            | (normalized["low"] > normalized[["open", "high", "close"]].min(axis=1))
            | (normalized[["open", "high", "low", "close"]] <= 0).any(axis=1)
        ]
        if len(bad_ohlc):
            errors.append(f"bad_ohlc_rows:{len(bad_ohlc)}")
        negative_spread = normalized[normalized["spread_median_points"] < 0]
        if len(negative_spread):
            errors.append(f"negative_spread_rows:{len(negative_spread)}")
    if not errors:
        normalized = normalized.sort_values("timestamp_utc")
        duplicate_count = int(normalized["timestamp_utc"].duplicated().sum())
        row["duplicate_timestamps"] = duplicate_count
        if duplicate_count:
            errors.append(f"duplicate_timestamps:{duplicate_count}")
        diffs = normalized["timestamp_utc"].diff().dropna()
        if not diffs.empty and timeframe in TIMEFRAME_DELTAS:
            expected = TIMEFRAME_DELTAS[timeframe]
            gaps = diffs[diffs > expected * 1.5]
            row["gap_count"] = int(len(gaps))
            if len(gaps):
                row["max_gap_minutes"] = round(float(gaps.max() / pd.Timedelta(minutes=1)), 2)
                warnings.append(f"timestamp_gaps:{len(gaps)}")
            backward = diffs[diffs <= pd.Timedelta(0)]
            if len(backward):
                errors.append(f"non_monotonic_timestamps:{len(backward)}")
    if not errors:
        output_dir = broker_refresh_validated_root(p) / broker / symbol / timeframe
        output_dir.mkdir(parents=True, exist_ok=True)
        start_token = normalized["timestamp_utc"].min().strftime("%Y%m%d")
        end_token = normalized["timestamp_utc"].max().strftime("%Y%m%d")
        output_path = output_dir / f"{symbol}_{broker}_{timeframe}_{start_token}_{end_token}_validated.csv"
        write_frame = normalized.copy()
        for column in ("timestamp_utc", "bar_start_utc", "bar_end_utc"):
            write_frame[column] = write_frame[column].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        write_frame.to_csv(output_path, index=False)
        row["normalized_output"] = relative(output_path)
        row["normalized_sha256"] = file_sha256(output_path)

    if not errors:
        row["status"] = "WARN_READY_FOR_REPLAY" if warnings else "PASS_READY_FOR_REPLAY"
    row["rows"] = int(len(normalized))
    if len(normalized):
        row["start_utc"] = iso(normalized["timestamp_utc"].min())
        row["end_utc"] = iso(normalized["timestamp_utc"].max())
        row["spread_median_points_median"] = round(float(normalized["spread_median_points"].median()), 4)
        if "spread_p95_points" in normalized.columns and normalized["spread_p95_points"].notna().any():
            row["spread_p95_points_median"] = round(float(normalized["spread_p95_points"].median()), 4)
    row["errors"] = ";".join(errors)
    row["warnings"] = ";".join(dict.fromkeys(warnings))
    return row


def infer_broker_refresh_metadata(raw_root: Path, path: Path) -> tuple[str, str, str]:
    parts = path.relative_to(raw_root).parts
    if len(parts) < 4:
        return "unknown", "unknown", "unknown"
    return parts[0], parts[1].upper(), parts[2].upper()


def extract_broker_refresh_provenance(path: Path, frame: pd.DataFrame) -> tuple[dict[str, str], str, list[str]]:
    provenance = {field: "" for field in BROKER_REFRESH_PROVENANCE_FIELDS}
    warnings: list[str] = []
    sources: list[str] = []
    sidecar = read_broker_refresh_provenance_sidecar(path, warnings)
    if sidecar:
        sources.append("sidecar")
        for field, aliases in BROKER_REFRESH_PROVENANCE_ALIASES.items():
            value = first_mapping_value(sidecar, aliases)
            if value:
                provenance[field] = value
    column_sources: set[str] = set()
    for field, aliases in BROKER_REFRESH_PROVENANCE_ALIASES.items():
        if provenance[field]:
            continue
        for alias in aliases:
            if alias not in frame.columns:
                continue
            values = []
            for raw_value in frame[alias].dropna().tolist():
                value = provenance_value_to_string(raw_value)
                if value and value not in values:
                    values.append(value)
            if values:
                provenance[field] = values[0]
                column_sources.add(alias)
                if len(values) > 1:
                    warnings.append(f"multiple_provenance_values:{field}")
                break
    if column_sources:
        sources.append("csv_columns:" + ",".join(sorted(column_sources)))
    return provenance, ";".join(sources), warnings


def read_broker_refresh_provenance_sidecar(path: Path, warnings: list[str]) -> dict[str, Any]:
    candidates = [
        path.with_suffix(path.suffix + ".provenance.json"),
        path.with_suffix(".provenance.json"),
        path.with_name(path.stem + "_provenance.json"),
    ]
    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            loaded = json.loads(candidate.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - defensive for owner-supplied files
            warnings.append(f"provenance_sidecar_read_error:{relative(candidate)}:{type(exc).__name__}")
            return {}
        if not isinstance(loaded, dict):
            warnings.append(f"provenance_sidecar_not_object:{relative(candidate)}")
            return {}
        source = loaded.get("provenance", loaded)
        if isinstance(source, dict):
            return flatten_provenance_mapping(source)
        warnings.append(f"provenance_sidecar_provenance_not_object:{relative(candidate)}")
        return {}
    return {}


def flatten_provenance_mapping(source: dict[str, Any]) -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for key, value in source.items():
        normalized_key = str(key).strip()
        flattened[normalized_key] = value
        if isinstance(value, dict):
            for nested_key, nested_value in value.items():
                flattened[f"{normalized_key}_{nested_key}"] = nested_value
                flattened[str(nested_key).strip()] = nested_value
    return flattened


def first_mapping_value(source: dict[str, Any], aliases: tuple[str, ...]) -> str:
    for alias in aliases:
        if alias in source:
            value = provenance_value_to_string(source[alias])
            if value:
                return value
    return ""


def provenance_value_to_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return ""
    return text


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_broker_refresh_validation_outputs(p: Paths, results: list[dict[str, Any]], generated_at: str) -> None:
    json_path = p.reports / f"FOREX_BROKER_REFRESH_VALIDATION_{RUN_DATE}.json"
    csv_path = p.tables / f"FOREX_BROKER_REFRESH_VALIDATION_{RUN_DATE}.csv"
    md_path = p.reports / f"FOREX_BROKER_REFRESH_VALIDATION_{RUN_DATE}.md"
    status = "NO_REFRESH_FILES_FOUND"
    if results:
        if any(row["status"].startswith("PASS") or row["status"].startswith("WARN") for row in results):
            status = "REFRESH_FILES_VALIDATED_RESEARCH_ONLY"
        if any(row["status"].startswith("FAIL") for row in results):
            status = "REFRESH_VALIDATION_HAS_FAILURES"
    json_path.write_text(
        json.dumps(
            {
                "generated_at_utc": generated_at,
                "status": status,
                "raw_root": relative(broker_refresh_raw_root(p)),
                "validated_root": relative(broker_refresh_validated_root(p)),
                "provenance_contract": {
                    "sidecar_patterns": [
                        "<file>.csv.provenance.json",
                        "<file>.provenance.json",
                        "<file>_provenance.json",
                    ],
                    "accepted_fields": list(BROKER_REFRESH_PROVENANCE_FIELDS),
                    "missing_provenance_status": "WARN_READY_FOR_REPLAY with provenance_status=PROVENANCE_MISSING",
                },
                "rows": results,
                "runtime_touched": False,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    if results:
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(results[0].keys()))
            writer.writeheader()
            writer.writerows(results)
    lines = [
        "# Forex Broker Refresh Validation",
        "",
        f"Generated at UTC: {generated_at}",
        f"Status: {status}",
        "",
        "Boundary: offline CSV validation only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        f"Raw input root: `{relative(broker_refresh_raw_root(p))}`",
        f"Validated output root: `{relative(broker_refresh_validated_root(p))}`",
        f"Status JSON: `{relative(json_path)}`",
        "",
        "Provenance contract: each broker-refresh export should include terminal/account provenance either as CSV columns or a JSON sidecar next to the CSV. The validator records raw-file SHA256, normalized-file SHA256, provenance status, terminal, account, server, export time, timezone, and method in the JSON/CSV output.",
    ]
    if results:
        lines.extend(["", f"Validation CSV: `{relative(csv_path)}`", "", "| status | provenance | broker | symbol | timeframe | rows | start | end | gaps | source | normalized_output |", "| --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- | --- |"])
        for row in results:
            lines.append(
                f"| {row['status']} | {row['provenance_status']} | {row['broker']} | {row['symbol']} | {row['timeframe']} | {row['rows']} | {str(row['start_utc'])[:10]} | {str(row['end_utc'])[:10]} | {row['gap_count']} | `{row['source_file']}` | `{row['normalized_output']}` |"
            )
        lines.extend(["", "## File Identity And Provenance", ""])
        for row in results:
            lines.extend(
                [
                    f"- `{row['source_file']}`",
                    f"  - raw_sha256: `{row['sha256']}`",
                    f"  - normalized_output: `{row['normalized_output']}`",
                    f"  - normalized_sha256: `{row['normalized_sha256']}`",
                    f"  - provenance_status: `{row['provenance_status']}`",
                    f"  - provenance_source: `{row['provenance_source']}`",
                    f"  - terminal/account: `{row['export_terminal']}` / `{row['export_account_login']}` / `{row['export_account_server']}`",
                    f"  - export_time/timezone/method: `{row['exported_at_utc']}` / `{row['export_timezone']}` / `{row['export_method']}`",
                ]
            )
        failed = [row for row in results if row["errors"]]
        warned = [row for row in results if row["warnings"]]
        if failed:
            lines.extend(["", "## Errors", ""])
            for row in failed:
                lines.append(f"- `{row['source_file']}`: {row['errors']}")
        if warned:
            lines.extend(["", "## Warnings", ""])
            for row in warned:
                lines.append(f"- `{row['source_file']}`: {row['warnings']}")
    else:
        lines.extend(
            [
                "",
                "No broker-refresh CSV files were found.",
                "",
                "Expected placement:",
                "",
                "```text",
                "forex-research/data/broker_refresh/raw/<broker>/<symbol>/<timeframe>/<file>.csv",
                "```",
                "",
                "Minimum columns: `timestamp_utc,open,high,low,close,spread_median_points`.",
                "",
                "Recommended provenance columns or sidecar fields: `export_terminal,export_account_login,export_account_server,export_account_type,export_broker_company,exported_at_utc,export_timezone,export_method`.",
            ]
        )
    lines.extend(
        [
            "",
            "Validator note: a PASS here only means the CSV is replay-ready for offline research. It does not approve a Forex EA or authorize a demo-forward-test spec.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")


def broker_refresh_retest_paths(p: Paths) -> Paths:
    return Paths(
        repo=p.repo,
        lane=p.lane,
        bars=broker_refresh_validated_root(p),
        external=p.external,
        reports=p.reports,
        tables=p.tables,
    )


def combine_refresh_context_frames(frames: list[pd.DataFrame], availability_column: str) -> pd.DataFrame:
    usable = [frame.copy() for frame in frames if frame is not None and not frame.empty]
    if not usable:
        return pd.DataFrame()
    source_files: dict[str, str] = {}
    for index, frame in enumerate(usable, start=1):
        if "source_files_json" not in frame.columns:
            continue
        try:
            files = json.loads(str(frame["source_files_json"].iloc[0]))
        except json.JSONDecodeError:
            files = {}
        for key, value in files.items():
            source_files[f"source_{index}_{key}"] = value
    combined = pd.concat(usable, ignore_index=True, sort=False)
    combined = combined.dropna(subset=["observation_utc", availability_column])
    combined = combined.sort_values(["observation_utc", availability_column])
    combined = combined.drop_duplicates("observation_utc", keep="last").reset_index(drop=True)
    combined["source_files_json"] = json.dumps(source_files, sort_keys=True)
    return combined


def optional_context(loader: Callable[[Paths], pd.DataFrame], p: Paths) -> pd.DataFrame:
    try:
        return loader(p)
    except FileNotFoundError:
        return pd.DataFrame()


def load_broker_refresh_contexts(p: Paths) -> dict[str, pd.DataFrame]:
    rates = combine_refresh_context_frames(
        [
            optional_context(load_rates_dollar_context, p),
            optional_context(load_recent_rates_dollar_context, p),
        ],
        "rates_available_utc",
    )
    bond_vol = combine_refresh_context_frames(
        [
            optional_context(load_bond_vol_context, p),
            optional_context(load_recent_bond_vol_context, p),
        ],
        "bond_vol_available_utc",
    )
    return {
        "macro": load_macro_context(p),
        "rates_dollar": rates,
        "bond_vol": bond_vol,
    }


def broker_refresh_candidate_specs(contexts: dict[str, pd.DataFrame]) -> list[CandidateSpec]:
    specs: list[CandidateSpec] = []
    if not contexts["macro"].empty:
        specs.extend(candidate_specs_macro(contexts["macro"]))
    if not contexts["rates_dollar"].empty:
        specs.extend(candidate_specs_rates_dollar(contexts["rates_dollar"]))
    if not contexts["bond_vol"].empty:
        specs.extend(candidate_specs_bond_vol(contexts["bond_vol"]))
    return specs


def broker_refresh_spec_context(
    spec: CandidateSpec,
    contexts: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, str, str]:
    if "real_yield" in spec.candidate_id:
        return contexts.get("macro", pd.DataFrame()), "macro_available_utc", "macro"
    if "rates_dollar" in spec.candidate_id:
        return contexts.get("rates_dollar", pd.DataFrame()), "rates_available_utc", "rates_dollar"
    if "bond_vol" in spec.candidate_id:
        return contexts.get("bond_vol", pd.DataFrame()), "bond_vol_available_utc", "bond_vol"
    return pd.DataFrame(), "", "unknown"


def broker_refresh_context_summary(contexts: dict[str, pd.DataFrame]) -> dict[str, dict[str, Any]]:
    columns = {
        "macro": "macro_available_utc",
        "rates_dollar": "rates_available_utc",
        "bond_vol": "bond_vol_available_utc",
    }
    summary: dict[str, dict[str, Any]] = {}
    for name, column in columns.items():
        frame = contexts.get(name, pd.DataFrame())
        source_files: dict[str, str] = {}
        if not frame.empty and "source_files_json" in frame.columns:
            try:
                source_files = json.loads(str(frame["source_files_json"].iloc[0]))
            except json.JSONDecodeError:
                source_files = {}
        summary[name] = {
            "rows": len(frame),
            "start_utc": iso(frame["observation_utc"].min()) if not frame.empty else "",
            "end_utc": iso(frame["observation_utc"].max()) if not frame.empty else "",
            "available_through_utc": iso(frame[column].max()) if not frame.empty and column in frame.columns else "",
            "source_files": source_files,
        }
    return summary


def run_broker_refresh_retest(
    p: Paths,
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, str]]:
    validation_results = validate_broker_refresh(p)
    refresh_p = broker_refresh_retest_paths(p)
    validated_files = sorted(refresh_p.bars.glob("*/*/*/*.csv"))
    contexts = load_broker_refresh_contexts(p)
    context_summary = broker_refresh_context_summary(contexts)
    if not validated_files:
        write_broker_refresh_retest_outputs(
            p,
            [],
            {},
            [],
            {},
            validation_results,
            context_summary,
            status="NO_VALIDATED_REFRESH_FILES",
        )
        return [], {}, {}

    cells = cost_geometry_scan(refresh_p)
    specs = broker_refresh_candidate_specs(contexts)
    brokers = available_brokers(refresh_p.bars)
    summary_rows: list[dict[str, Any]] = []
    trade_map: dict[str, list[dict[str, Any]]] = {}
    for spec in specs:
        candidate_trades: list[dict[str, Any]] = []
        context_frame, availability_column, context_name = broker_refresh_spec_context(spec, contexts)
        context_available = (
            pd.to_datetime(context_frame[availability_column], utc=True, errors="coerce").max()
            if not context_frame.empty and availability_column in context_frame.columns
            else pd.NaT
        )
        for broker in brokers:
            raw_frame = load_bars(refresh_p.bars, broker, spec.symbol, spec.timeframe)
            if raw_frame.empty:
                continue
            frame = raw_frame[raw_frame["timestamp_utc"] >= RECENT_START].copy()
            if pd.notna(context_available):
                max_bar_time = context_available + pd.Timedelta(days=BROKER_REFRESH_CONTEXT_STALE_GRACE_DAYS)
                frame = frame[frame["bar_start_utc"] <= max_bar_time].copy()
            trades: list[dict[str, Any]] = []
            if not frame.empty and not context_frame.empty:
                signals = spec.generator(frame)
                trades = simulate_trades(spec, frame, broker, signals, proxy_spread=None)
            candidate_trades.extend(trades)
            row = summary_metrics(spec, trades, broker=broker, level="broker")
            row.update(
                broker_refresh_row_coverage(
                    raw_frame,
                    frame,
                    context_name,
                    context_available,
                    len(signals) if not frame.empty and not context_frame.empty else 0,
                )
            )
            summary_rows.append(row)
        deduped = dedupe_trades(candidate_trades)
        trade_map[spec.candidate_id] = deduped
        overall = summary_metrics(spec, deduped, broker="all_validated_refresh", level="overall")
        overall.update(
            {
                "raw_rows": "",
                "filtered_rows": "",
                "raw_start_utc": "",
                "raw_end_utc": "",
                "filtered_start_utc": "",
                "filtered_end_utc": "",
                "context_name": context_name,
                "context_available_through_utc": iso(context_available) if pd.notna(context_available) else "",
                "generated_signals": "",
            }
        )
        summary_rows.append(overall)

    gates = broker_refresh_retest_gates(summary_rows, trade_map, cells)
    for row in summary_rows:
        row["refresh_gate"] = gates.get(row["candidate_id"], "")
        row["watchlist_target"] = row["candidate_id"] in BROKER_REFRESH_WATCHLIST_IDS
    write_broker_refresh_retest_outputs(
        p,
        summary_rows,
        trade_map,
        cells,
        gates,
        validation_results,
        context_summary,
        status="BROKER_REFRESH_RETEST_COMPLETE_RESEARCH_ONLY",
    )
    return summary_rows, trade_map, gates


def broker_refresh_row_coverage(
    raw_frame: pd.DataFrame,
    filtered_frame: pd.DataFrame,
    context_name: str,
    context_available: pd.Timestamp,
    generated_signals: int,
) -> dict[str, Any]:
    return {
        "raw_rows": len(raw_frame),
        "filtered_rows": len(filtered_frame),
        "raw_start_utc": iso(raw_frame["timestamp_utc"].min()) if not raw_frame.empty else "",
        "raw_end_utc": iso(raw_frame["timestamp_utc"].max()) if not raw_frame.empty else "",
        "filtered_start_utc": iso(filtered_frame["timestamp_utc"].min()) if not filtered_frame.empty else "",
        "filtered_end_utc": iso(filtered_frame["timestamp_utc"].max()) if not filtered_frame.empty else "",
        "context_name": context_name,
        "context_available_through_utc": iso(context_available) if pd.notna(context_available) else "",
        "generated_signals": generated_signals,
    }


def broker_refresh_retest_gates(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
) -> dict[str, str]:
    gates: dict[str, str] = {}
    overall_rows = {row["candidate_id"]: row for row in rows if row["level"] == "overall"}
    broker_rows: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row["level"] == "broker":
            broker_rows.setdefault(row["candidate_id"], []).append(row)
    for candidate_id, row in overall_rows.items():
        candidate_cells = [
            cell
            for cell in cells
            if cell.symbol == row["symbol"]
            and cell.timeframe == row["timeframe"]
            and cell.rows > 0
            and cell.has_spread
            and not math.isnan(cell.cost_r_recent_p95)
        ]
        if not broker_rows.get(candidate_id):
            gates[candidate_id] = "NO_REFRESH_DATA_FOR_SYMBOL_TIMEFRAME"
        elif not candidate_cells:
            gates[candidate_id] = "REJECT_REFRESH_NO_COST_GEOMETRY"
        elif any(cell.cost_r_recent_p95 > BROKER_REFRESH_COST_R_P95_LIMIT for cell in candidate_cells):
            gates[candidate_id] = "REJECT_REFRESH_COST_R_TOO_HIGH"
        elif int(row["trade_count"]) < 20:
            gates[candidate_id] = "REJECT_REFRESH_LOW_SAMPLE"
        elif not math.isfinite(float(row["profit_factor"])) or float(row["profit_factor"]) < 1.15:
            gates[candidate_id] = "REJECT_REFRESH_WEAK_EDGE"
        elif float(row["net_expectancy_r"]) <= 0.03:
            gates[candidate_id] = "REJECT_REFRESH_WEAK_EXPECTANCY"
        elif float(row["top_winner_removed_net_r"]) <= 0:
            gates[candidate_id] = "REJECT_REFRESH_TOP_WINNER_DEPENDENT"
        elif float(row["max_drawdown_r"]) > 12:
            gates[candidate_id] = "REJECT_REFRESH_DRAWDOWN"
        elif broker_refresh_has_material_negative_broker(broker_rows.get(candidate_id, [])):
            gates[candidate_id] = "REJECT_REFRESH_BROKER_INSTABILITY"
        else:
            gates[candidate_id] = "WATCHLIST_ONLY_REFRESH_GATE_PASS_NO_DEMO_APPROVAL"
    return gates


def broker_refresh_has_material_negative_broker(rows: list[dict[str, Any]]) -> bool:
    meaningful = [row for row in rows if int(row["trade_count"]) >= 20]
    if len(meaningful) < 2:
        return False
    return any(float(row["total_net_r"]) <= 0 or float(row["profit_factor"]) < 1.0 for row in meaningful)


def write_broker_refresh_retest_outputs(
    p: Paths,
    summary_rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    gates: dict[str, str],
    validation_results: list[dict[str, Any]],
    context_summary: dict[str, dict[str, Any]],
    *,
    status: str,
) -> None:
    summary_path = p.tables / f"FOREX_BROKER_REFRESH_RETEST_SUMMARY_{RUN_DATE}.csv"
    status_path = p.reports / f"FOREX_BROKER_REFRESH_RETEST_STATUS_{RUN_DATE}.json"
    report_path = p.reports / f"FOREX_BROKER_REFRESH_RETEST_{RUN_DATE}.md"
    if summary_rows:
        fieldnames = list(summary_rows[0].keys())
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in summary_rows:
                writer.writerow(format_summary_row(row))
    else:
        summary_path.write_text("", encoding="utf-8")
    for candidate_id, trades in trade_map.items():
        path = p.tables / f"{candidate_id}_BROKER_REFRESH_RETEST_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": status,
                "runtime_touched": False,
                "raw_root": relative(broker_refresh_raw_root(p)),
                "validated_root": relative(broker_refresh_validated_root(p)),
                "summary_csv": relative(summary_path),
                "gates": gates,
                "validation_statuses": [row.get("status", "") for row in validation_results],
                "context_summary": context_summary,
                "cost_cells": [dataclass_row(cell) for cell in cells],
                "no_demo_forward_spec_prepared": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report_path.write_text(
        render_broker_refresh_retest_report(
            status,
            summary_rows,
            summary_path,
            status_path,
            cells,
            gates,
            validation_results,
            context_summary,
        ),
        encoding="utf-8",
    )


def render_broker_refresh_retest_report(
    status: str,
    summary_rows: list[dict[str, Any]],
    summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    gates: dict[str, str],
    validation_results: list[dict[str, Any]],
    context_summary: dict[str, dict[str, Any]],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    lines = [
        "# Forex Broker Refresh Frozen Retest",
        "",
        f"Generated at UTC: {generated}",
        f"Status: {status}",
        "",
        "Boundary: offline CSV replay only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        f"Raw input root: `{relative(broker_refresh_raw_root(paths()))}`",
        f"Validated input root: `{relative(broker_refresh_validated_root(paths()))}`",
        f"Summary CSV: `{relative(summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "This command retests the frozen review-approved families only: EURUSD real-yield/dollar-pressure macro, EURUSD rates/dollar, and USDJPY bond-volatility v0/v1. It does not tune thresholds or approve a demo-forward EA.",
        "",
    ]
    if not summary_rows:
        lines.extend(
            [
                "No validated broker-refresh CSVs were available for replay.",
                "",
                "Place files under `forex-research/data/broker_refresh/raw/<broker>/<symbol>/<timeframe>/`, run `broker-refresh-validate`, then rerun `broker-refresh-retest`.",
                "",
            ]
        )
    lines.extend(["## Validation Inputs", "", "| status | broker | symbol | timeframe | rows | source |", "| --- | --- | --- | --- | ---: | --- |"])
    if validation_results:
        for row in validation_results:
            lines.append(
                f"| {row['status']} | {row['broker']} | {row['symbol']} | {row['timeframe']} | {row['rows']} | `{row['source_file']}` |"
            )
    else:
        lines.append("| NO_REFRESH_FILES_FOUND |  |  |  | 0 |  |")
    lines.extend(["", "## Context Coverage", "", "| context | rows | start | end | available through |", "| --- | ---: | --- | --- | --- |"])
    for name, row in context_summary.items():
        lines.append(
            f"| {name} | {row['rows']} | {str(row['start_utc'])[:10]} | {str(row['end_utc'])[:10]} | {str(row['available_through_utc'])[:10]} |"
        )
    if cells:
        lines.extend(["", "## Refreshed Cost Geometry", "", "| broker | symbol | timeframe | rows | p95 cost_R recent | status |", "| --- | --- | --- | ---: | ---: | --- |"])
        for cell in sorted(cells, key=lambda item: (item.symbol, item.timeframe, item.broker)):
            if cell.rows <= 0:
                continue
            cost = "" if math.isnan(cell.cost_r_recent_p95) else f"{cell.cost_r_recent_p95:.4f}"
            lines.append(f"| {cell.broker} | {cell.symbol} | {cell.timeframe} | {cell.rows} | {cost} | {cell.data_status} |")
    if summary_rows:
        overall = [row for row in summary_rows if row["level"] == "overall"]
        lines.extend(["", "## Candidate Gates", "", "| candidate | target | trades | PF | net R | max DD R | top-winner removed R | gate |", "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |"])
        for row in overall:
            lines.append(
                "| {candidate} | {target} | {trades} | {pf:.4f} | {net:.2f} | {dd:.2f} | {twr:.2f} | {gate} |".format(
                    candidate=row["candidate_id"],
                    target="yes" if row["candidate_id"] in BROKER_REFRESH_WATCHLIST_IDS else "family-control",
                    trades=int(row["trade_count"]),
                    pf=float(row["profit_factor"]) if math.isfinite(float(row["profit_factor"])) else 0.0,
                    net=float(row["total_net_r"]),
                    dd=float(row["max_drawdown_r"]),
                    twr=float(row["top_winner_removed_net_r"]),
                    gate=gates.get(row["candidate_id"], ""),
                )
            )
    lines.extend(
        [
            "",
            "Gate note: a pass can only mean `WATCHLIST_ONLY_REFRESH_GATE_PASS_NO_DEMO_APPROVAL`. Demo-forward drafting remains a separate owner-approved step.",
            "",
        ]
    )
    return "\n".join(lines)


def load_financial_liquidity_context(p: Paths) -> pd.DataFrame:
    root = financial_liquidity_source_root(p)
    frames: list[pd.DataFrame] = []
    source_files: dict[str, str] = {}
    for output_column, (filename, source_column) in FINANCIAL_LIQUIDITY_SOURCE_FILES.items():
        path = root / filename
        if not path.exists():
            raise FileNotFoundError(f"Missing financial/liquidity source file: {path}")
        frame = pd.read_csv(path)
        required = {"observation_date", source_column}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{path} missing required columns: {', '.join(sorted(missing))}")
        ctx = pd.DataFrame(
            {
                "observation_utc": pd.to_datetime(frame["observation_date"], utc=True, errors="coerce"),
                output_column: pd.to_numeric(frame[source_column].replace(".", pd.NA), errors="coerce"),
            }
        ).dropna()
        frames.append(ctx.sort_values("observation_utc").reset_index(drop=True))
        source_files[output_column] = relative(path)
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="observation_utc", how="outer")
    merged = merged.sort_values("observation_utc").ffill().dropna().reset_index(drop=True)
    merged["financial_liquidity_available_utc"] = merged["observation_utc"] + pd.Timedelta(days=7)
    merged["nfci_delta_4w"] = merged["nfci"].diff(4)
    merged["nfci_delta_13w"] = merged["nfci"].diff(13)
    merged["anfci_delta_4w"] = merged["anfci"].diff(4)
    merged["anfci_delta_13w"] = merged["anfci"].diff(13)
    merged["walcl_4w_pct"] = merged["walcl"].pct_change(4) * 100.0
    merged["walcl_13w_pct"] = merged["walcl"].pct_change(13) * 100.0
    merged["liquidity_easing_score"] = (
        (-merged["anfci_delta_4w"] / 0.08)
        + (-merged["nfci_delta_4w"] / 0.08)
        + (merged["walcl_13w_pct"] / 1.0)
    )
    merged["liquidity_tightening_score"] = (
        (merged["anfci_delta_4w"] / 0.08)
        + (merged["nfci_delta_4w"] / 0.08)
        - (merged["walcl_13w_pct"] / 1.0)
    )
    merged["source_files_json"] = json.dumps(source_files, sort_keys=True)
    return merged.dropna(
        subset=[
            "nfci_delta_4w",
            "nfci_delta_13w",
            "anfci_delta_4w",
            "anfci_delta_13w",
            "walcl_4w_pct",
            "walcl_13w_pct",
            "liquidity_easing_score",
            "liquidity_tightening_score",
        ]
    ).reset_index(drop=True)


def merge_financial_liquidity(frame: pd.DataFrame, context: pd.DataFrame, symbol: str) -> pd.DataFrame:
    features = with_features(frame, symbol).sort_values("bar_start_utc")
    context_sorted = context.sort_values("financial_liquidity_available_utc")
    return pd.merge_asof(
        features,
        context_sorted,
        left_on="bar_start_utc",
        right_on="financial_liquidity_available_utc",
        direction="backward",
    )


def financial_liquidity_context_summary(p: Paths, context: pd.DataFrame) -> dict[str, Any]:
    source_files = json.loads(str(context["source_files_json"].iloc[0])) if len(context) else {}
    return {
        "source_root": relative(financial_liquidity_source_root(p)),
        "rows": len(context),
        "start_utc": iso(context["observation_utc"].min()) if len(context) else "",
        "end_utc": iso(context["observation_utc"].max()) if len(context) else "",
        "available_through_utc": iso(context["financial_liquidity_available_utc"].max()) if len(context) else "",
        "files": source_files,
        "lag_policy": "Weekly FRED financial/liquidity observations are available to H4 bars only after a conservative seven-day lag.",
        "orientation": "Rising NFCI/ANFCI means tighter financial conditions; WALCL growth means Fed balance-sheet liquidity expansion.",
    }


def cot_number(value: Any) -> float:
    text = str(value).replace(",", "").strip()
    if not text:
        return float("nan")
    try:
        return float(text)
    except ValueError:
        return float("nan")


def load_cot_financial_context(p: Paths) -> pd.DataFrame:
    root = cot_financial_root(p)
    files = sorted(root.glob("fut_fin_txt_*.zip")) if root.exists() else []
    expected = {f"fut_fin_txt_{year}.zip" for year in COT_FINANCIAL_YEARS}
    if expected.difference(path.name for path in files):
        acquire_cot_financial_reports(p)
        files = sorted(root.glob("fut_fin_txt_*.zip"))
    market_to_symbol = {str(config["market"]): symbol for symbol, config in COT_FINANCIAL_MARKETS.items()}
    rows: list[dict[str, Any]] = []
    source_files: dict[str, str] = {}
    for path in files:
        source_files[path.stem] = relative(path)
        with zipfile.ZipFile(path) as archive:
            name = archive.namelist()[0]
            with archive.open(name) as raw:
                reader = csv.DictReader(io.TextIOWrapper(raw, encoding="latin1", newline=""))
                for record in reader:
                    market = str(record.get("Market_and_Exchange_Names", "")).strip()
                    symbol = market_to_symbol.get(market)
                    if not symbol:
                        continue
                    report_date = pd.to_datetime(record.get("Report_Date_as_YYYY-MM-DD"), utc=True, errors="coerce")
                    open_interest = cot_number(record.get("Open_Interest_All"))
                    if pd.isna(report_date) or not math.isfinite(open_interest) or open_interest <= 0:
                        continue
                    rows.append(
                        {
                            "symbol": symbol,
                            "market": market,
                            "observation_utc": report_date,
                            "open_interest": open_interest,
                            "dealer_long": cot_number(record.get("Dealer_Positions_Long_All")),
                            "dealer_short": cot_number(record.get("Dealer_Positions_Short_All")),
                            "asset_long": cot_number(record.get("Asset_Mgr_Positions_Long_All")),
                            "asset_short": cot_number(record.get("Asset_Mgr_Positions_Short_All")),
                            "lev_long": cot_number(record.get("Lev_Money_Positions_Long_All")),
                            "lev_short": cot_number(record.get("Lev_Money_Positions_Short_All")),
                            "spot_orientation": float(COT_FINANCIAL_MARKETS[symbol]["orientation"]),
                        }
                    )
    if not rows:
        raise RuntimeError(f"No EURUSD/USDJPY financial COT rows found under {root}")
    context = pd.DataFrame(rows).dropna().sort_values(["symbol", "observation_utc"]).drop_duplicates(
        ["symbol", "observation_utc"], keep="last"
    )
    parts: list[pd.DataFrame] = []
    for _symbol, group in context.groupby("symbol", sort=True):
        g = group.sort_values("observation_utc").reset_index(drop=True).copy()
        g["cot_available_utc"] = g["observation_utc"] + pd.Timedelta(days=7)
        for account in ("dealer", "asset", "lev"):
            g[f"{account}_net"] = g[f"{account}_long"] - g[f"{account}_short"]
            g[f"{account}_net_pct_oi"] = (g[f"{account}_net"] / g["open_interest"]) * 100.0
            g[f"spot_{account}_net_pct_oi"] = g[f"{account}_net_pct_oi"] * g["spot_orientation"]
            rolling_mean = g[f"spot_{account}_net_pct_oi"].rolling(156, min_periods=52).mean()
            rolling_std = g[f"spot_{account}_net_pct_oi"].rolling(156, min_periods=52).std()
            g[f"spot_{account}_z156"] = (g[f"spot_{account}_net_pct_oi"] - rolling_mean) / rolling_std
        g["spot_lev_delta_4w"] = g["spot_lev_net_pct_oi"].diff(4)
        g["spot_lev_delta_13w"] = g["spot_lev_net_pct_oi"].diff(13)
        g["spot_asset_delta_4w"] = g["spot_asset_net_pct_oi"].diff(4)
        g["source_files_json"] = json.dumps(source_files, sort_keys=True)
        parts.append(g)
    return pd.concat(parts, ignore_index=True).dropna(
        subset=["spot_lev_z156", "spot_lev_delta_4w", "spot_lev_delta_13w"]
    ).reset_index(drop=True)


def merge_cot_positioning(frame: pd.DataFrame, cot_context: pd.DataFrame, symbol: str) -> pd.DataFrame:
    features = with_features(frame, symbol).sort_values("bar_start_utc")
    cot_sorted = cot_context[cot_context["symbol"] == symbol].sort_values("cot_available_utc")
    return pd.merge_asof(
        features,
        cot_sorted,
        left_on="bar_start_utc",
        right_on="cot_available_utc",
        direction="backward",
        suffixes=("", "_cot"),
    )


def cot_financial_context_summary(p: Paths, context: pd.DataFrame) -> dict[str, Any]:
    source_files = json.loads(str(context["source_files_json"].iloc[0])) if len(context) else {}
    snapshots: list[dict[str, Any]] = []
    for symbol, group in context.groupby("symbol", sort=True):
        latest = group.sort_values("observation_utc").iloc[-1]
        snapshots.append(
            {
                "symbol": symbol,
                "market": str(latest["market"]),
                "report_utc": iso(latest["observation_utc"]),
                "available_utc": iso(latest["cot_available_utc"]),
                "spot_lev_net_pct_oi": float(latest["spot_lev_net_pct_oi"]),
                "spot_lev_z156": float(latest["spot_lev_z156"]),
                "spot_lev_delta_4w": float(latest["spot_lev_delta_4w"]),
                "spot_lev_delta_13w": float(latest["spot_lev_delta_13w"]),
            }
        )
    return {
        "source_root": relative(cot_financial_root(p)),
        "source_url": CFTC_HISTORICAL_COMPRESSED_URL,
        "rows": len(context),
        "start_utc": iso(context["observation_utc"].min()) if len(context) else "",
        "end_utc": iso(context["observation_utc"].max()) if len(context) else "",
        "available_through_utc": iso(context["cot_available_utc"].max()) if len(context) else "",
        "files": source_files,
        "lag_policy": "CFTC weekly report dates are available to H4 bars only after a conservative seven-day lag.",
        "orientation": "Positive spot-oriented leveraged-money net means EURUSD-bullish for Euro FX and USDJPY-bullish after inverting Japanese Yen futures.",
        "latest_snapshot": snapshots,
    }


def load_macro_context(p: Paths) -> pd.DataFrame:
    root = macro_source_root(p)
    frames: list[pd.DataFrame] = []
    for output_column, (filename, source_column) in MACRO_SOURCE_FILES.items():
        path = root / filename
        if not path.exists():
            raise FileNotFoundError(f"Missing macro source file: {path}")
        frame = pd.read_csv(path)
        required = {"observation_date", source_column}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{path} missing required columns: {', '.join(sorted(missing))}")
        series = pd.DataFrame(
            {
                "observation_utc": pd.to_datetime(frame["observation_date"], utc=True, errors="coerce"),
                output_column: pd.to_numeric(frame[source_column].replace(".", pd.NA), errors="coerce"),
            }
        ).dropna()
        frames.append(series)
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="observation_utc", how="outer")
    merged = merged.sort_values("observation_utc").ffill().dropna().reset_index(drop=True)
    merged["macro_available_utc"] = merged["observation_utc"] + pd.Timedelta(days=1)
    merged["real_yield_delta_20d"] = merged["real_yield_10y"].diff(20)
    merged["real_yield_delta_60d"] = merged["real_yield_10y"].diff(60)
    merged["dollar_pct_20d"] = merged["dollar_index_broad"].pct_change(20) * 100.0
    merged["dollar_pct_60d"] = merged["dollar_index_broad"].pct_change(60) * 100.0
    merged["macro_pressure_score"] = (merged["real_yield_delta_20d"] / 0.20) + (merged["dollar_pct_20d"] / 1.50)
    return merged.dropna(subset=["real_yield_delta_20d", "dollar_pct_20d", "macro_pressure_score"]).reset_index(drop=True)


def merge_macro(frame: pd.DataFrame, macro: pd.DataFrame, symbol: str) -> pd.DataFrame:
    features = with_features(frame, symbol).sort_values("bar_start_utc")
    macro_sorted = macro.sort_values("macro_available_utc")
    merged = pd.merge_asof(
        features,
        macro_sorted,
        left_on="bar_start_utc",
        right_on="macro_available_utc",
        direction="backward",
    )
    return merged


def macro_context_summary(p: Paths, macro: pd.DataFrame) -> dict[str, Any]:
    return {
        "source_root": relative(macro_source_root(p)),
        "rows": len(macro),
        "start_utc": iso(macro["observation_utc"].min()),
        "end_utc": iso(macro["observation_utc"].max()),
        "available_through_utc": iso(macro["macro_available_utc"].max()),
        "files": {
            key: relative(macro_source_root(p) / filename)
            for key, (filename, _column) in MACRO_SOURCE_FILES.items()
        },
    }


def load_treasury_curve_context(p: Paths) -> pd.DataFrame:
    root = treasury_curve_source_root(p)
    frames: list[pd.DataFrame] = []
    for output_column, (filename, source_column) in TREASURY_CURVE_SOURCE_FILES.items():
        path = root / filename
        if not path.exists():
            raise FileNotFoundError(f"Missing Treasury curve source file: {path}")
        frame = pd.read_csv(path)
        required = {"observation_date", source_column}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{path} missing required columns: {', '.join(sorted(missing))}")
        series = pd.DataFrame(
            {
                "observation_utc": pd.to_datetime(frame["observation_date"], utc=True, errors="coerce"),
                output_column: pd.to_numeric(frame[source_column].replace(".", pd.NA), errors="coerce"),
            }
        ).dropna()
        frames.append(series)
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="observation_utc", how="outer")
    merged = merged.sort_values("observation_utc").ffill().dropna().reset_index(drop=True)
    merged["treasury_curve_available_utc"] = merged["observation_utc"] + pd.Timedelta(days=1)
    merged["dgs2_delta_5d"] = merged["dgs2"].diff(5)
    merged["dgs2_delta_20d"] = merged["dgs2"].diff(20)
    merged["dgs2_delta_60d"] = merged["dgs2"].diff(60)
    merged["dgs10_delta_20d"] = merged["dgs10"].diff(20)
    merged["dgs10_delta_60d"] = merged["dgs10"].diff(60)
    merged["curve_2s10s"] = merged["t10y2y"]
    merged["curve_delta_20d"] = merged["t10y2y"].diff(20)
    merged["curve_delta_60d"] = merged["t10y2y"].diff(60)
    merged["front_end_pressure_score"] = (merged["dgs2_delta_20d"] / 0.35) - (merged["curve_delta_20d"] / 0.25)
    merged["bull_steepening_score"] = (-merged["dgs2_delta_20d"] / 0.35) + (merged["curve_delta_20d"] / 0.25)
    return merged.dropna(
        subset=[
            "dgs2_delta_5d",
            "dgs2_delta_20d",
            "dgs2_delta_60d",
            "dgs10_delta_20d",
            "curve_delta_20d",
            "curve_delta_60d",
            "front_end_pressure_score",
            "bull_steepening_score",
        ]
    ).reset_index(drop=True)


def merge_treasury_curve(frame: pd.DataFrame, curve_context: pd.DataFrame, symbol: str) -> pd.DataFrame:
    features = with_features(frame, symbol).sort_values("bar_start_utc")
    curve_sorted = curve_context.sort_values("treasury_curve_available_utc")
    return pd.merge_asof(
        features,
        curve_sorted,
        left_on="bar_start_utc",
        right_on="treasury_curve_available_utc",
        direction="backward",
    )


def treasury_curve_context_summary(p: Paths, curve_context: pd.DataFrame) -> dict[str, Any]:
    return {
        "source_root": relative(treasury_curve_source_root(p)),
        "rows": len(curve_context),
        "start_utc": iso(curve_context["observation_utc"].min()) if len(curve_context) else "",
        "end_utc": iso(curve_context["observation_utc"].max()) if len(curve_context) else "",
        "available_through_utc": iso(curve_context["treasury_curve_available_utc"].max()) if len(curve_context) else "",
        "files": {
            key: relative(treasury_curve_source_root(p) / filename)
            for key, (filename, _column) in TREASURY_CURVE_SOURCE_FILES.items()
        },
        "lag_policy": "FRED daily Treasury observations are available to H4 bars only from the next UTC date.",
        "orientation": (
            "Front-end pressure is rising DGS2 plus 2s10s flattening. Bull-steepening relief is falling DGS2 plus "
            "2s10s steepening."
        ),
    }


def load_cny_pressure_context(p: Paths) -> pd.DataFrame:
    root = macro_source_root(p)
    frames: list[pd.DataFrame] = []
    for output_column, (filename, source_column) in CNY_PRESSURE_SOURCE_FILES.items():
        path = root / filename
        if not path.exists():
            raise FileNotFoundError(f"Missing CNY pressure source file: {path}")
        frame = pd.read_csv(path)
        required = {"observation_date", source_column}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{path} missing required columns: {', '.join(sorted(missing))}")
        series = pd.DataFrame(
            {
                "observation_utc": pd.to_datetime(frame["observation_date"], utc=True, errors="coerce"),
                output_column: pd.to_numeric(frame[source_column].replace(".", pd.NA), errors="coerce"),
            }
        ).dropna()
        frames.append(series)
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="observation_utc", how="outer")
    merged = merged.sort_values("observation_utc").ffill().dropna().reset_index(drop=True)
    merged["cny_available_utc"] = merged["observation_utc"] + pd.Timedelta(days=1)
    merged["usd_cny_pct_5d"] = merged["usd_cny"].pct_change(5) * 100.0
    merged["usd_cny_pct_20d"] = merged["usd_cny"].pct_change(20) * 100.0
    merged["usd_cny_pct_60d"] = merged["usd_cny"].pct_change(60) * 100.0
    merged["dollar_pct_20d"] = merged["dollar_index_broad"].pct_change(20) * 100.0
    merged["dollar_pct_60d"] = merged["dollar_index_broad"].pct_change(60) * 100.0
    merged["cny_dollar_pressure_score"] = (merged["usd_cny_pct_20d"] / 1.00) + (merged["dollar_pct_20d"] / 1.75)
    return merged.dropna(
        subset=["usd_cny_pct_5d", "usd_cny_pct_20d", "dollar_pct_20d", "cny_dollar_pressure_score"]
    ).reset_index(drop=True)


def merge_cny_pressure(frame: pd.DataFrame, cny: pd.DataFrame, symbol: str) -> pd.DataFrame:
    features = with_features(frame, symbol).sort_values("bar_start_utc")
    cny_sorted = cny.sort_values("cny_available_utc")
    return pd.merge_asof(
        features,
        cny_sorted,
        left_on="bar_start_utc",
        right_on="cny_available_utc",
        direction="backward",
    )


def cny_pressure_context_summary(p: Paths, cny: pd.DataFrame) -> dict[str, Any]:
    return {
        "source_root": relative(macro_source_root(p)),
        "rows": len(cny),
        "start_utc": iso(cny["observation_utc"].min()),
        "end_utc": iso(cny["observation_utc"].max()),
        "available_through_utc": iso(cny["cny_available_utc"].max()),
        "files": {
            key: relative(macro_source_root(p) / filename)
            for key, (filename, _column) in CNY_PRESSURE_SOURCE_FILES.items()
        },
        "lag_policy": "CNY and broad-dollar observations are available to bars only from the next UTC date.",
        "orientation": "DEXCHUS is yuan per USD; positive USD/CNY change means CNY depreciation and dollar pressure.",
    }


def load_currency_etf_context(p: Paths) -> dict[str, pd.DataFrame]:
    root = reference_etf_root(p)
    contexts: dict[str, pd.DataFrame] = {}
    for symbol, config in CURRENCY_ETF_FILES.items():
        path = root / str(config["filename"])
        if not path.exists():
            raise FileNotFoundError(f"Missing currency ETF reference file: {path}")
        frame = pd.read_csv(path)
        base = str(config["base"])
        quote = str(config["quote"])
        required = {"date_utc", f"{base}_close", f"{quote}_close", f"{base}_volume", f"{quote}_volume"}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{path} missing required columns: {', '.join(sorted(missing))}")
        ctx = pd.DataFrame(
            {
                "observation_utc": pd.to_datetime(frame["date_utc"], utc=True, errors="coerce"),
                "base_close": pd.to_numeric(frame[f"{base}_close"], errors="coerce"),
                "quote_close": pd.to_numeric(frame[f"{quote}_close"], errors="coerce"),
                "base_volume": pd.to_numeric(frame[f"{base}_volume"], errors="coerce"),
                "quote_volume": pd.to_numeric(frame[f"{quote}_volume"], errors="coerce"),
            }
        ).dropna()
        ctx = ctx[(ctx["base_close"] > 0) & (ctx["quote_close"] > 0)].sort_values("observation_utc").reset_index(drop=True)
        ctx["relative_ratio"] = ctx["base_close"] / ctx["quote_close"]
        if config["orientation"] == "inverse":
            ctx["symbol_flow_ratio"] = 1.0 / ctx["relative_ratio"]
        else:
            ctx["symbol_flow_ratio"] = ctx["relative_ratio"]
        ctx["flow_5d_pct"] = ctx["symbol_flow_ratio"].pct_change(5) * 100.0
        ctx["flow_20d_pct"] = ctx["symbol_flow_ratio"].pct_change(20) * 100.0
        ctx["volume_ratio"] = ctx["base_volume"] / ctx["quote_volume"].replace(0, pd.NA)
        ctx["flow_available_utc"] = ctx["observation_utc"] + pd.Timedelta(days=1)
        ctx["source_file"] = relative(path)
        contexts[symbol] = ctx.dropna(subset=["flow_5d_pct", "flow_20d_pct"]).reset_index(drop=True)
    return contexts


def merge_currency_flow(frame: pd.DataFrame, flow: pd.DataFrame, symbol: str) -> pd.DataFrame:
    features = with_features(frame, symbol).sort_values("bar_start_utc")
    flow_sorted = flow.sort_values("flow_available_utc")
    return pd.merge_asof(
        features,
        flow_sorted,
        left_on="bar_start_utc",
        right_on="flow_available_utc",
        direction="backward",
    )


def currency_flow_context_summary(contexts: dict[str, pd.DataFrame]) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for symbol, frame in contexts.items():
        rows[symbol] = {
            "rows": len(frame),
            "start_utc": iso(frame["observation_utc"].min()) if len(frame) else "",
            "end_utc": iso(frame["observation_utc"].max()) if len(frame) else "",
            "available_through_utc": iso(frame["flow_available_utc"].max()) if len(frame) else "",
            "source_file": str(frame["source_file"].iloc[0]) if len(frame) else "",
        }
    return {
        "source_root": relative(reference_etf_root(paths())),
        "rows": rows,
        "lag_policy": "ETF daily observations are available to H4 bars only from the next UTC date.",
    }


def load_global_risk_context(p: Paths) -> pd.DataFrame:
    root = reference_etf_root(p)
    frames: list[pd.DataFrame] = []
    source_files: dict[str, str] = {}
    for name, config in GLOBAL_RISK_FILES.items():
        path = root / str(config["filename"])
        if not path.exists():
            raise FileNotFoundError(f"Missing global risk reference file: {path}")
        frame = pd.read_csv(path)
        risk = str(config["risk"])
        defensive = str(config["defensive"])
        required = {"date_utc", f"{risk}_close", f"{defensive}_close"}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{path} missing required columns: {', '.join(sorted(missing))}")
        ctx = pd.DataFrame(
            {
                "observation_utc": pd.to_datetime(frame["date_utc"], utc=True, errors="coerce"),
                f"{name}_risk_close": pd.to_numeric(frame[f"{risk}_close"], errors="coerce"),
                f"{name}_defensive_close": pd.to_numeric(frame[f"{defensive}_close"], errors="coerce"),
            }
        ).dropna()
        ctx = ctx[
            (ctx[f"{name}_risk_close"] > 0) & (ctx[f"{name}_defensive_close"] > 0)
        ].sort_values("observation_utc").reset_index(drop=True)
        ctx[f"{name}_ratio"] = ctx[f"{name}_risk_close"] / ctx[f"{name}_defensive_close"]
        ctx[f"{name}_5d_pct"] = ctx[f"{name}_ratio"].pct_change(5) * 100.0
        ctx[f"{name}_20d_pct"] = ctx[f"{name}_ratio"].pct_change(20) * 100.0
        frames.append(ctx[["observation_utc", f"{name}_ratio", f"{name}_5d_pct", f"{name}_20d_pct"]])
        source_files[name] = relative(path)
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="observation_utc", how="outer")
    merged = merged.sort_values("observation_utc").ffill().dropna().reset_index(drop=True)
    merged["global_risk_available_utc"] = merged["observation_utc"] + pd.Timedelta(days=1)
    merged["global_risk_score"] = (merged["eem_spy_20d_pct"] / 4.0) + (merged["hyg_ief_20d_pct"] / 2.5)
    merged["source_files_json"] = json.dumps(source_files, sort_keys=True)
    return merged.dropna(
        subset=["eem_spy_5d_pct", "eem_spy_20d_pct", "hyg_ief_5d_pct", "hyg_ief_20d_pct", "global_risk_score"]
    ).reset_index(drop=True)


def merge_global_risk(frame: pd.DataFrame, global_risk: pd.DataFrame, symbol: str) -> pd.DataFrame:
    features = with_features(frame, symbol).sort_values("bar_start_utc")
    risk_sorted = global_risk.sort_values("global_risk_available_utc")
    return pd.merge_asof(
        features,
        risk_sorted,
        left_on="bar_start_utc",
        right_on="global_risk_available_utc",
        direction="backward",
    )


def global_risk_context_summary(p: Paths, global_risk: pd.DataFrame) -> dict[str, Any]:
    source_files = json.loads(str(global_risk["source_files_json"].iloc[0])) if len(global_risk) else {}
    return {
        "source_root": relative(reference_etf_root(p)),
        "rows": len(global_risk),
        "start_utc": iso(global_risk["observation_utc"].min()) if len(global_risk) else "",
        "end_utc": iso(global_risk["observation_utc"].max()) if len(global_risk) else "",
        "available_through_utc": iso(global_risk["global_risk_available_utc"].max()) if len(global_risk) else "",
        "files": source_files,
        "lag_policy": "ETF daily observations are available to H4 bars only from the next UTC date.",
        "orientation": "Positive EEM/SPY and HYG/IEF changes indicate risk/credit appetite; negative changes indicate defensive pressure.",
    }


def load_commodity_dollar_context(p: Paths) -> pd.DataFrame:
    return load_commodity_dollar_context_from_root(reference_etf_root(p), recent=False)


def load_recent_commodity_dollar_context(p: Paths) -> pd.DataFrame:
    return load_commodity_dollar_context_from_root(recent_commodity_proxy_root(p), recent=True)


def load_commodity_dollar_context_from_root(root: Path, *, recent: bool) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    source_files: dict[str, str] = {}
    for name, config in COMMODITY_DOLLAR_FILES.items():
        if recent:
            files = sorted(root.glob(f"{name}_daily_yahoo_*.csv"))
            if not files:
                raise FileNotFoundError(f"Missing recent commodity/dollar proxy file for {name} under {root}")
            path = files[-1]
        else:
            path = root / str(config["filename"])
        if not path.exists():
            raise FileNotFoundError(f"Missing commodity/dollar reference file: {path}")
        frame = pd.read_csv(path)
        commodity = str(config["commodity"])
        dollar = str(config["dollar"])
        required = {"date_utc", f"{commodity}_close", f"{dollar}_close"}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{path} missing required columns: {', '.join(sorted(missing))}")
        ctx = pd.DataFrame(
            {
                "observation_utc": pd.to_datetime(frame["date_utc"], utc=True, errors="coerce"),
                f"{name}_commodity_close": pd.to_numeric(frame[f"{commodity}_close"], errors="coerce"),
                f"{name}_dollar_close": pd.to_numeric(frame[f"{dollar}_close"], errors="coerce"),
            }
        ).dropna()
        ctx = ctx[
            (ctx[f"{name}_commodity_close"] > 0) & (ctx[f"{name}_dollar_close"] > 0)
        ].sort_values("observation_utc").reset_index(drop=True)
        ctx[f"{name}_ratio"] = ctx[f"{name}_commodity_close"] / ctx[f"{name}_dollar_close"]
        ctx[f"{name}_5d_pct"] = ctx[f"{name}_ratio"].pct_change(5) * 100.0
        ctx[f"{name}_20d_pct"] = ctx[f"{name}_ratio"].pct_change(20) * 100.0
        frames.append(ctx[["observation_utc", f"{name}_ratio", f"{name}_5d_pct", f"{name}_20d_pct"]])
        source_files[name] = relative(path)
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="observation_utc", how="outer")
    merged = merged.sort_values("observation_utc").ffill().dropna().reset_index(drop=True)
    merged["commodity_available_utc"] = merged["observation_utc"] + pd.Timedelta(days=1)
    merged["commodity_dollar_score"] = (merged["dbc_uup_20d_pct"] / 6.0) + (merged["dbb_uup_20d_pct"] / 6.5)
    merged["source_files_json"] = json.dumps(source_files, sort_keys=True)
    return merged.dropna(
        subset=["dbc_uup_5d_pct", "dbc_uup_20d_pct", "dbb_uup_5d_pct", "dbb_uup_20d_pct", "commodity_dollar_score"]
    ).reset_index(drop=True)


def merge_commodity_dollar(frame: pd.DataFrame, commodity_context: pd.DataFrame, symbol: str) -> pd.DataFrame:
    features = with_features(frame, symbol).sort_values("bar_start_utc")
    commodity_sorted = commodity_context.sort_values("commodity_available_utc")
    return pd.merge_asof(
        features,
        commodity_sorted,
        left_on="bar_start_utc",
        right_on="commodity_available_utc",
        direction="backward",
    )


def commodity_dollar_context_summary(p: Paths, commodity_context: pd.DataFrame, source_root: Path | None = None) -> dict[str, Any]:
    source_files = json.loads(str(commodity_context["source_files_json"].iloc[0])) if len(commodity_context) else {}
    return {
        "source_root": relative(source_root or reference_etf_root(p)),
        "rows": len(commodity_context),
        "start_utc": iso(commodity_context["observation_utc"].min()) if len(commodity_context) else "",
        "end_utc": iso(commodity_context["observation_utc"].max()) if len(commodity_context) else "",
        "available_through_utc": iso(commodity_context["commodity_available_utc"].max()) if len(commodity_context) else "",
        "files": source_files,
        "lag_policy": "ETF daily observations are available to H4 bars only from the next UTC date.",
        "orientation": "Positive DBC/UUP and DBB/UUP changes indicate commodity strength versus the dollar; negative changes indicate commodity weakness versus the dollar.",
    }


def load_real_asset_rotation_context(p: Paths) -> pd.DataFrame:
    return load_real_asset_rotation_context_from_sources(p, recent=False)


def load_recent_real_asset_rotation_context(p: Paths) -> pd.DataFrame:
    return load_real_asset_rotation_context_from_sources(p, recent=True)


def real_asset_reference_path(p: Paths, config: dict[str, Any]) -> Path:
    root = reference_futures_root(p) if config["source_root"] == "futures" else reference_etf_root(p)
    return root / str(config["filename"])


def load_real_asset_rotation_context_from_sources(p: Paths, *, recent: bool) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    source_files: dict[str, str] = {}
    recent_root = recent_real_asset_rotation_proxy_root(p)
    for name, config in REAL_ASSET_ROTATION_FILES.items():
        if recent:
            files = sorted(recent_root.glob(f"{name}_daily_yahoo_*.csv"))
            if not files:
                raise FileNotFoundError(f"Missing recent real-asset rotation proxy file for {name} under {recent_root}")
            path = files[-1]
        else:
            path = real_asset_reference_path(p, config)
        if not path.exists():
            raise FileNotFoundError(f"Missing real-asset rotation reference file: {path}")
        frame = pd.read_csv(path)
        left = str(config["left"])
        right = str(config["right"])
        required = {"date_utc", f"{left}_close", f"{right}_close"}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{path} missing required columns: {', '.join(sorted(missing))}")
        ctx = pd.DataFrame(
            {
                "observation_utc": pd.to_datetime(frame["date_utc"], utc=True, errors="coerce"),
                f"{name}_left_close": pd.to_numeric(frame[f"{left}_close"], errors="coerce"),
                f"{name}_right_close": pd.to_numeric(frame[f"{right}_close"], errors="coerce"),
            }
        ).dropna()
        ctx = ctx[
            (ctx[f"{name}_left_close"] > 0) & (ctx[f"{name}_right_close"] > 0)
        ].sort_values("observation_utc").reset_index(drop=True)
        ctx[f"{name}_ratio"] = ctx[f"{name}_left_close"] / ctx[f"{name}_right_close"]
        ctx[f"{name}_5d_pct"] = ctx[f"{name}_ratio"].pct_change(5) * 100.0
        ctx[f"{name}_20d_pct"] = ctx[f"{name}_ratio"].pct_change(20) * 100.0
        frames.append(ctx[["observation_utc", f"{name}_ratio", f"{name}_5d_pct", f"{name}_20d_pct"]])
        source_files[name] = relative(path)
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="observation_utc", how="outer")
    merged = merged.sort_values("observation_utc").ffill().dropna().reset_index(drop=True)
    merged["real_asset_available_utc"] = merged["observation_utc"] + pd.Timedelta(days=1)
    merged["real_asset_reflation_score"] = (
        (merged["uso_uup_20d_pct"] / 6.0) + (merged["hg_gc_20d_pct"] / 3.0) + (merged["slv_gld_20d_pct"] / 3.0)
    )
    merged["source_files_json"] = json.dumps(source_files, sort_keys=True)
    return merged.dropna(
        subset=[
            "uso_uup_5d_pct",
            "uso_uup_20d_pct",
            "hg_gc_20d_pct",
            "slv_gld_20d_pct",
            "real_asset_reflation_score",
        ]
    ).reset_index(drop=True)


def merge_real_asset_rotation(frame: pd.DataFrame, real_asset_context: pd.DataFrame, symbol: str) -> pd.DataFrame:
    features = with_features(frame, symbol).sort_values("bar_start_utc")
    real_asset_sorted = real_asset_context.sort_values("real_asset_available_utc")
    return pd.merge_asof(
        features,
        real_asset_sorted,
        left_on="bar_start_utc",
        right_on="real_asset_available_utc",
        direction="backward",
    )


def real_asset_rotation_context_summary(
    p: Paths, real_asset_context: pd.DataFrame, source_root: Path | None = None
) -> dict[str, Any]:
    source_files = json.loads(str(real_asset_context["source_files_json"].iloc[0])) if len(real_asset_context) else {}
    return {
        "source_root": relative(source_root) if source_root else "mixed:reference/etf plus reference/futures",
        "rows": len(real_asset_context),
        "start_utc": iso(real_asset_context["observation_utc"].min()) if len(real_asset_context) else "",
        "end_utc": iso(real_asset_context["observation_utc"].max()) if len(real_asset_context) else "",
        "available_through_utc": iso(real_asset_context["real_asset_available_utc"].max()) if len(real_asset_context) else "",
        "files": source_files,
        "lag_policy": "ETF/futures daily observations are available to H4 bars only from the next UTC date.",
        "orientation": "Positive USO/UUP indicates oil strength versus the dollar; positive HG/GC and SLV/GLD indicate cyclical metal beta versus gold safe-haven strength.",
    }


def load_haven_liquidity_context(p: Paths) -> pd.DataFrame:
    return load_haven_liquidity_context_from_root(reference_etf_root(p), recent=False)


def load_recent_haven_liquidity_context(p: Paths) -> pd.DataFrame:
    return load_haven_liquidity_context_from_root(recent_haven_liquidity_proxy_root(p), recent=True)


def load_haven_liquidity_context_from_root(root: Path, *, recent: bool) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    source_files: dict[str, str] = {}
    for name, config in HAVEN_LIQUIDITY_FILES.items():
        if recent:
            files = sorted(root.glob(f"{name}_daily_yahoo_*.csv"))
            if not files:
                raise FileNotFoundError(f"Missing recent haven/liquidity proxy file for {name} under {root}")
            path = files[-1]
        else:
            path = root / str(config["filename"])
        if not path.exists():
            raise FileNotFoundError(f"Missing haven/liquidity reference file: {path}")
        frame = pd.read_csv(path)
        if config["kind"] == "single":
            required = {"date_utc", "close"}
            missing = required.difference(frame.columns)
            if missing:
                raise ValueError(f"{path} missing required columns: {', '.join(sorted(missing))}")
            ctx = pd.DataFrame(
                {
                    "observation_utc": pd.to_datetime(frame["date_utc"], utc=True, errors="coerce"),
                    "gld_close": pd.to_numeric(frame["close"], errors="coerce"),
                }
            ).dropna()
            ctx = ctx[ctx["gld_close"] > 0].sort_values("observation_utc").reset_index(drop=True)
            ctx["gld_5d_pct"] = ctx["gld_close"].pct_change(5) * 100.0
            ctx["gld_20d_pct"] = ctx["gld_close"].pct_change(20) * 100.0
            frames.append(ctx[["observation_utc", "gld_close", "gld_5d_pct", "gld_20d_pct"]])
        else:
            left = str(config["left"])
            right = str(config["right"])
            required = {"date_utc", f"{left}_close", f"{right}_close"}
            missing = required.difference(frame.columns)
            if missing:
                raise ValueError(f"{path} missing required columns: {', '.join(sorted(missing))}")
            ctx = pd.DataFrame(
                {
                    "observation_utc": pd.to_datetime(frame["date_utc"], utc=True, errors="coerce"),
                    f"{name}_left_close": pd.to_numeric(frame[f"{left}_close"], errors="coerce"),
                    f"{name}_right_close": pd.to_numeric(frame[f"{right}_close"], errors="coerce"),
                }
            ).dropna()
            ctx = ctx[
                (ctx[f"{name}_left_close"] > 0) & (ctx[f"{name}_right_close"] > 0)
            ].sort_values("observation_utc").reset_index(drop=True)
            ctx[f"{name}_ratio"] = ctx[f"{name}_left_close"] / ctx[f"{name}_right_close"]
            ctx[f"{name}_5d_pct"] = ctx[f"{name}_ratio"].pct_change(5) * 100.0
            ctx[f"{name}_20d_pct"] = ctx[f"{name}_ratio"].pct_change(20) * 100.0
            frames.append(ctx[["observation_utc", f"{name}_ratio", f"{name}_5d_pct", f"{name}_20d_pct"]])
        source_files[name] = relative(path)
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="observation_utc", how="outer")
    merged = merged.sort_values("observation_utc").ffill().dropna().reset_index(drop=True)
    merged["haven_liquidity_available_utc"] = merged["observation_utc"] + pd.Timedelta(days=1)
    merged["haven_liquidity_score"] = (
        (merged["gld_20d_pct"] / 4.0)
        + (merged["gdx_gld_20d_pct"] / 5.0)
        - (merged["spy_tlt_20d_pct"] / 5.0)
        + (merged["xlu_xlk_20d_pct"] / 3.0)
    )
    merged["source_files_json"] = json.dumps(source_files, sort_keys=True)
    return merged.dropna(
        subset=[
            "gld_5d_pct",
            "gld_20d_pct",
            "gdx_gld_20d_pct",
            "spy_tlt_20d_pct",
            "xlu_xlk_20d_pct",
            "haven_liquidity_score",
        ]
    ).reset_index(drop=True)


def merge_haven_liquidity(frame: pd.DataFrame, haven_context: pd.DataFrame, symbol: str) -> pd.DataFrame:
    features = with_features(frame, symbol).sort_values("bar_start_utc")
    haven_sorted = haven_context.sort_values("haven_liquidity_available_utc")
    return pd.merge_asof(
        features,
        haven_sorted,
        left_on="bar_start_utc",
        right_on="haven_liquidity_available_utc",
        direction="backward",
    )


def haven_liquidity_context_summary(
    p: Paths, haven_context: pd.DataFrame, source_root: Path | None = None
) -> dict[str, Any]:
    source_files = json.loads(str(haven_context["source_files_json"].iloc[0])) if len(haven_context) else {}
    return {
        "source_root": relative(source_root or reference_etf_root(p)),
        "rows": len(haven_context),
        "start_utc": iso(haven_context["observation_utc"].min()) if len(haven_context) else "",
        "end_utc": iso(haven_context["observation_utc"].max()) if len(haven_context) else "",
        "available_through_utc": iso(haven_context["haven_liquidity_available_utc"].max()) if len(haven_context) else "",
        "files": source_files,
        "lag_policy": "ETF daily observations are available to H4 bars only from the next UTC date.",
        "orientation": "Positive score indicates GLD strength, miner confirmation, equity weakness versus duration, and utilities leadership versus tech; negative score indicates liquidity/risk relief.",
    }


def load_rates_dollar_context(p: Paths) -> pd.DataFrame:
    root = reference_etf_root(p)
    frames: list[pd.DataFrame] = []
    source_files: dict[str, str] = {}
    for name, config in RATES_DOLLAR_FILES.items():
        path = root / str(config["filename"])
        if not path.exists():
            raise FileNotFoundError(f"Missing rates/dollar reference file: {path}")
        frame = pd.read_csv(path)
        duration = str(config["duration"])
        denominator = str(config.get("dollar") or config.get("cash"))
        required = {"date_utc", f"{duration}_close", f"{denominator}_close"}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{path} missing required columns: {', '.join(sorted(missing))}")
        ctx = pd.DataFrame(
            {
                "observation_utc": pd.to_datetime(frame["date_utc"], utc=True, errors="coerce"),
                f"{name}_duration_close": pd.to_numeric(frame[f"{duration}_close"], errors="coerce"),
                f"{name}_denominator_close": pd.to_numeric(frame[f"{denominator}_close"], errors="coerce"),
            }
        ).dropna()
        ctx = ctx[
            (ctx[f"{name}_duration_close"] > 0) & (ctx[f"{name}_denominator_close"] > 0)
        ].sort_values("observation_utc").reset_index(drop=True)
        ctx[f"{name}_ratio"] = ctx[f"{name}_duration_close"] / ctx[f"{name}_denominator_close"]
        ctx[f"{name}_5d_pct"] = ctx[f"{name}_ratio"].pct_change(5) * 100.0
        ctx[f"{name}_20d_pct"] = ctx[f"{name}_ratio"].pct_change(20) * 100.0
        frames.append(ctx[["observation_utc", f"{name}_ratio", f"{name}_5d_pct", f"{name}_20d_pct"]])
        source_files[name] = relative(path)
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="observation_utc", how="outer")
    merged = merged.sort_values("observation_utc").ffill().dropna().reset_index(drop=True)
    merged["rates_available_utc"] = merged["observation_utc"] + pd.Timedelta(days=1)
    merged["rates_dollar_score"] = (merged["tlt_uup_20d_pct"] / 4.0) + (merged["tlt_shy_20d_pct"] / 1.5)
    merged["source_files_json"] = json.dumps(source_files, sort_keys=True)
    return merged.dropna(
        subset=["tlt_uup_5d_pct", "tlt_uup_20d_pct", "tlt_shy_5d_pct", "tlt_shy_20d_pct", "rates_dollar_score"]
    ).reset_index(drop=True)


def load_recent_rates_dollar_context(p: Paths) -> pd.DataFrame:
    root = recent_rates_proxy_root(p)
    frames: list[pd.DataFrame] = []
    source_files: dict[str, str] = {}
    for name, config in RATES_DOLLAR_FILES.items():
        files = sorted(root.glob(f"{name}_daily_yahoo_*.csv"))
        if not files:
            raise FileNotFoundError(f"Missing recent rates/dollar proxy file for {name} under {root}")
        path = files[-1]
        frame = pd.read_csv(path)
        duration = str(config["duration"])
        denominator = str(config.get("dollar") or config.get("cash"))
        required = {"date_utc", f"{duration}_close", f"{denominator}_close"}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{path} missing required columns: {', '.join(sorted(missing))}")
        ctx = pd.DataFrame(
            {
                "observation_utc": pd.to_datetime(frame["date_utc"], utc=True, errors="coerce"),
                f"{name}_duration_close": pd.to_numeric(frame[f"{duration}_close"], errors="coerce"),
                f"{name}_denominator_close": pd.to_numeric(frame[f"{denominator}_close"], errors="coerce"),
            }
        ).dropna()
        ctx = ctx[
            (ctx[f"{name}_duration_close"] > 0) & (ctx[f"{name}_denominator_close"] > 0)
        ].sort_values("observation_utc").reset_index(drop=True)
        ctx[f"{name}_ratio"] = ctx[f"{name}_duration_close"] / ctx[f"{name}_denominator_close"]
        ctx[f"{name}_5d_pct"] = ctx[f"{name}_ratio"].pct_change(5) * 100.0
        ctx[f"{name}_20d_pct"] = ctx[f"{name}_ratio"].pct_change(20) * 100.0
        frames.append(ctx[["observation_utc", f"{name}_ratio", f"{name}_5d_pct", f"{name}_20d_pct"]])
        source_files[name] = relative(path)
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="observation_utc", how="outer")
    merged = merged.sort_values("observation_utc").ffill().dropna().reset_index(drop=True)
    merged["rates_available_utc"] = merged["observation_utc"] + pd.Timedelta(days=1)
    merged["rates_dollar_score"] = (merged["tlt_uup_20d_pct"] / 4.0) + (merged["tlt_shy_20d_pct"] / 1.5)
    merged["source_files_json"] = json.dumps(source_files, sort_keys=True)
    return merged.dropna(
        subset=["tlt_uup_5d_pct", "tlt_uup_20d_pct", "tlt_shy_5d_pct", "tlt_shy_20d_pct", "rates_dollar_score"]
    ).reset_index(drop=True)


def merge_rates_dollar(frame: pd.DataFrame, rates_context: pd.DataFrame, symbol: str) -> pd.DataFrame:
    features = with_features(frame, symbol).sort_values("bar_start_utc")
    rates_sorted = rates_context.sort_values("rates_available_utc")
    return pd.merge_asof(
        features,
        rates_sorted,
        left_on="bar_start_utc",
        right_on="rates_available_utc",
        direction="backward",
    )


def rates_dollar_context_summary(p: Paths, rates_context: pd.DataFrame, source_root: Path | None = None) -> dict[str, Any]:
    source_files = json.loads(str(rates_context["source_files_json"].iloc[0])) if len(rates_context) else {}
    return {
        "source_root": relative(source_root or reference_etf_root(p)),
        "rows": len(rates_context),
        "start_utc": iso(rates_context["observation_utc"].min()) if len(rates_context) else "",
        "end_utc": iso(rates_context["observation_utc"].max()) if len(rates_context) else "",
        "available_through_utc": iso(rates_context["rates_available_utc"].max()) if len(rates_context) else "",
        "files": source_files,
        "lag_policy": "ETF daily observations are available to H4 bars only from the next UTC date.",
        "orientation": "Positive TLT/UUP and TLT/SHY changes indicate duration strength versus the dollar/cash; negative changes indicate yield/dollar pressure.",
    }


def load_equity_leadership_context(p: Paths) -> pd.DataFrame:
    return load_equity_leadership_context_from_root(reference_etf_root(p), recent=False)


def load_recent_equity_leadership_context(p: Paths) -> pd.DataFrame:
    return load_equity_leadership_context_from_root(recent_equity_leadership_proxy_root(p), recent=True)


def load_equity_leadership_context_from_root(root: Path, *, recent: bool) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    source_files: dict[str, str] = {}
    for name, config in EQUITY_LEADERSHIP_FILES.items():
        if recent:
            files = sorted(root.glob(f"{name}_daily_yahoo_*.csv"))
            if not files:
                raise FileNotFoundError(f"Missing recent equity-leadership proxy file for {name} under {root}")
            path = files[-1]
        else:
            path = root / str(config["filename"])
        if not path.exists():
            raise FileNotFoundError(f"Missing equity-leadership reference file: {path}")
        frame = pd.read_csv(path)
        leader = str(config["leader"])
        benchmark = str(config["benchmark"])
        required = {"date_utc", f"{leader}_close", f"{benchmark}_close"}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{path} missing required columns: {', '.join(sorted(missing))}")
        ctx = pd.DataFrame(
            {
                "observation_utc": pd.to_datetime(frame["date_utc"], utc=True, errors="coerce"),
                f"{name}_leader_close": pd.to_numeric(frame[f"{leader}_close"], errors="coerce"),
                f"{name}_benchmark_close": pd.to_numeric(frame[f"{benchmark}_close"], errors="coerce"),
            }
        ).dropna()
        ctx = ctx[
            (ctx[f"{name}_leader_close"] > 0) & (ctx[f"{name}_benchmark_close"] > 0)
        ].sort_values("observation_utc").reset_index(drop=True)
        ctx[f"{name}_ratio"] = ctx[f"{name}_leader_close"] / ctx[f"{name}_benchmark_close"]
        ctx[f"{name}_5d_pct"] = ctx[f"{name}_ratio"].pct_change(5) * 100.0
        ctx[f"{name}_20d_pct"] = ctx[f"{name}_ratio"].pct_change(20) * 100.0
        frames.append(ctx[["observation_utc", f"{name}_ratio", f"{name}_5d_pct", f"{name}_20d_pct"]])
        source_files[name] = relative(path)
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="observation_utc", how="outer")
    merged = merged.sort_values("observation_utc").ffill().dropna().reset_index(drop=True)
    merged["equity_leadership_available_utc"] = merged["observation_utc"] + pd.Timedelta(days=1)
    merged["equity_leadership_score"] = (
        (merged["acwx_spy_20d_pct"] / 2.0)
        + (merged["iwm_spy_20d_pct"] / 2.5)
        + (merged["xlf_xlu_20d_pct"] / 4.0)
    )
    merged["source_files_json"] = json.dumps(source_files, sort_keys=True)
    return merged.dropna(
        subset=[
            "acwx_spy_5d_pct",
            "acwx_spy_20d_pct",
            "iwm_spy_5d_pct",
            "iwm_spy_20d_pct",
            "xlf_xlu_20d_pct",
            "equity_leadership_score",
        ]
    ).reset_index(drop=True)


def merge_equity_leadership(frame: pd.DataFrame, equity_context: pd.DataFrame, symbol: str) -> pd.DataFrame:
    features = with_features(frame, symbol).sort_values("bar_start_utc")
    equity_sorted = equity_context.sort_values("equity_leadership_available_utc")
    return pd.merge_asof(
        features,
        equity_sorted,
        left_on="bar_start_utc",
        right_on="equity_leadership_available_utc",
        direction="backward",
    )


def equity_leadership_context_summary(p: Paths, equity_context: pd.DataFrame, source_root: Path | None = None) -> dict[str, Any]:
    source_files = json.loads(str(equity_context["source_files_json"].iloc[0])) if len(equity_context) else {}
    return {
        "source_root": relative(source_root or reference_etf_root(p)),
        "rows": len(equity_context),
        "start_utc": iso(equity_context["observation_utc"].min()) if len(equity_context) else "",
        "end_utc": iso(equity_context["observation_utc"].max()) if len(equity_context) else "",
        "available_through_utc": iso(equity_context["equity_leadership_available_utc"].max()) if len(equity_context) else "",
        "files": source_files,
        "lag_policy": "ETF daily observations are available to H4 bars only from the next UTC date.",
        "orientation": "Positive ACWX/SPY indicates ex-US equity leadership; positive IWM/SPY and XLF/XLU indicate US cyclical/risk leadership.",
    }


def load_sector_rotation_context(p: Paths) -> pd.DataFrame:
    return load_sector_rotation_context_from_root(reference_etf_root(p), recent=False)


def load_recent_sector_rotation_context(p: Paths) -> pd.DataFrame:
    return load_sector_rotation_context_from_root(recent_sector_rotation_proxy_root(p), recent=True)


def load_sector_rotation_context_from_root(root: Path, *, recent: bool) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    source_files: dict[str, str] = {}
    for name, config in SECTOR_ROTATION_FILES.items():
        if recent:
            files = sorted(root.glob(f"{name}_daily_yahoo_*.csv"))
            if not files:
                raise FileNotFoundError(f"Missing recent sector-rotation proxy file for {name} under {root}")
            path = files[-1]
        else:
            path = root / str(config["filename"])
        if not path.exists():
            raise FileNotFoundError(f"Missing sector-rotation reference file: {path}")
        frame = pd.read_csv(path)
        leader = str(config["leader"])
        benchmark = str(config["benchmark"])
        required = {"date_utc", f"{leader}_close", f"{benchmark}_close"}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{path} missing required columns: {', '.join(sorted(missing))}")
        ctx = pd.DataFrame(
            {
                "observation_utc": pd.to_datetime(frame["date_utc"], utc=True, errors="coerce"),
                f"{name}_leader_close": pd.to_numeric(frame[f"{leader}_close"], errors="coerce"),
                f"{name}_benchmark_close": pd.to_numeric(frame[f"{benchmark}_close"], errors="coerce"),
            }
        ).dropna()
        ctx = ctx[
            (ctx[f"{name}_leader_close"] > 0) & (ctx[f"{name}_benchmark_close"] > 0)
        ].sort_values("observation_utc").reset_index(drop=True)
        ctx[f"{name}_ratio"] = ctx[f"{name}_leader_close"] / ctx[f"{name}_benchmark_close"]
        ctx[f"{name}_5d_pct"] = ctx[f"{name}_ratio"].pct_change(5) * 100.0
        ctx[f"{name}_20d_pct"] = ctx[f"{name}_ratio"].pct_change(20) * 100.0
        frames.append(ctx[["observation_utc", f"{name}_ratio", f"{name}_5d_pct", f"{name}_20d_pct"]])
        source_files[name] = relative(path)
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="observation_utc", how="outer")
    merged = merged.sort_values("observation_utc").ffill().dropna().reset_index(drop=True)
    merged["sector_rotation_available_utc"] = merged["observation_utc"] + pd.Timedelta(days=1)
    merged["sector_growth_score"] = (merged["xly_xlp_20d_pct"] / 3.0) + (merged["qqq_spy_20d_pct"] / 2.0)
    merged["sector_cyclical_score"] = (
        (merged["xle_xlu_20d_pct"] / 4.0)
        + (merged["xli_xlu_20d_pct"] / 3.0)
        + (merged["xme_spy_20d_pct"] / 4.0)
    )
    merged["sector_inflation_score"] = merged["tip_ief_20d_pct"] / 1.25
    merged["source_files_json"] = json.dumps(source_files, sort_keys=True)
    return merged.dropna(
        subset=[
            "xly_xlp_5d_pct",
            "xly_xlp_20d_pct",
            "qqq_spy_20d_pct",
            "xle_xlu_20d_pct",
            "xli_xlu_20d_pct",
            "xme_spy_20d_pct",
            "tip_ief_20d_pct",
            "sector_growth_score",
            "sector_cyclical_score",
            "sector_inflation_score",
        ]
    ).reset_index(drop=True)


def merge_sector_rotation(frame: pd.DataFrame, sector_context: pd.DataFrame, symbol: str) -> pd.DataFrame:
    features = with_features(frame, symbol).sort_values("bar_start_utc")
    sector_sorted = sector_context.sort_values("sector_rotation_available_utc")
    return pd.merge_asof(
        features,
        sector_sorted,
        left_on="bar_start_utc",
        right_on="sector_rotation_available_utc",
        direction="backward",
    )


def sector_rotation_context_summary(p: Paths, sector_context: pd.DataFrame, source_root: Path | None = None) -> dict[str, Any]:
    source_files = json.loads(str(sector_context["source_files_json"].iloc[0])) if len(sector_context) else {}
    return {
        "source_root": relative(source_root or reference_etf_root(p)),
        "rows": len(sector_context),
        "start_utc": iso(sector_context["observation_utc"].min()) if len(sector_context) else "",
        "end_utc": iso(sector_context["observation_utc"].max()) if len(sector_context) else "",
        "available_through_utc": iso(sector_context["sector_rotation_available_utc"].max()) if len(sector_context) else "",
        "files": source_files,
        "lag_policy": "ETF daily observations are available to H4 bars only from the next UTC date.",
        "orientation": "Positive XLY/XLP and QQQ/SPY indicate growth/risk appetite; positive XLE/XLU, XLI/XLU, and XME/SPY indicate cyclical/inflation leadership; positive TIP/IEF indicates inflation-linked bond leadership versus nominals.",
    }


def load_currency_basket_context(p: Paths) -> pd.DataFrame:
    return load_currency_basket_context_from_root(reference_etf_root(p), recent=False)


def load_recent_currency_basket_context(p: Paths) -> pd.DataFrame:
    return load_currency_basket_context_from_root(
        recent_currency_basket_proxy_root(p),
        recent=True,
        required_names=("fxa_uup", "fxf_uup"),
    )


def load_currency_basket_context_from_root(
    root: Path,
    *,
    recent: bool,
    required_names: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    source_files: dict[str, str] = {}
    names = required_names or tuple(CURRENCY_BASKET_FILES)
    for name in names:
        config = CURRENCY_BASKET_FILES[name]
        if recent:
            files = sorted(root.glob(f"{name}_daily_yahoo_*.csv"))
            if not files:
                raise FileNotFoundError(f"Missing recent currency-basket proxy file for {name} under {root}")
            path = files[-1]
        else:
            path = root / str(config["filename"])
        if not path.exists():
            raise FileNotFoundError(f"Missing currency-basket reference file: {path}")
        frame = pd.read_csv(path)
        currency = str(config["currency"])
        dollar = str(config["dollar"])
        required = {"date_utc", f"{currency}_close", f"{dollar}_close"}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{path} missing required columns: {', '.join(sorted(missing))}")
        ctx = pd.DataFrame(
            {
                "observation_utc": pd.to_datetime(frame["date_utc"], utc=True, errors="coerce"),
                f"{name}_currency_close": pd.to_numeric(frame[f"{currency}_close"], errors="coerce"),
                f"{name}_dollar_close": pd.to_numeric(frame[f"{dollar}_close"], errors="coerce"),
            }
        ).dropna()
        ctx = ctx[
            (ctx[f"{name}_currency_close"] > 0) & (ctx[f"{name}_dollar_close"] > 0)
        ].sort_values("observation_utc").reset_index(drop=True)
        ctx[f"{name}_ratio"] = ctx[f"{name}_currency_close"] / ctx[f"{name}_dollar_close"]
        ctx[f"{name}_5d_pct"] = ctx[f"{name}_ratio"].pct_change(5) * 100.0
        ctx[f"{name}_20d_pct"] = ctx[f"{name}_ratio"].pct_change(20) * 100.0
        frames.append(ctx[["observation_utc", f"{name}_ratio", f"{name}_5d_pct", f"{name}_20d_pct"]])
        source_files[name] = relative(path)
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="observation_utc", how="outer")
    merged = merged.sort_values("observation_utc").ffill().dropna().reset_index(drop=True)
    merged["currency_basket_available_utc"] = merged["observation_utc"] + pd.Timedelta(days=1)
    if {"fxa_uup_20d_pct", "cyb_uup_20d_pct"}.issubset(merged.columns):
        merged["risk_currency_score"] = (merged["fxa_uup_20d_pct"] / 2.0) + (merged["cyb_uup_20d_pct"] / 1.5)
    if {"fxf_uup_20d_pct", "fxa_uup_20d_pct"}.issubset(merged.columns):
        merged["safe_haven_score"] = (merged["fxf_uup_20d_pct"] / 1.5) - (merged["fxa_uup_20d_pct"] / 2.0)
    merged["source_files_json"] = json.dumps(source_files, sort_keys=True)
    drop_subset = [
        column
        for column in (
            "fxa_uup_5d_pct",
            "fxa_uup_20d_pct",
            "fxf_uup_5d_pct",
            "fxf_uup_20d_pct",
            "cyb_uup_5d_pct",
            "cyb_uup_20d_pct",
            "risk_currency_score",
            "safe_haven_score",
        )
        if column in merged.columns
    ]
    return merged.dropna(
        subset=drop_subset
    ).reset_index(drop=True)


def merge_currency_basket(frame: pd.DataFrame, currency_context: pd.DataFrame, symbol: str) -> pd.DataFrame:
    features = with_features(frame, symbol).sort_values("bar_start_utc")
    currency_sorted = currency_context.sort_values("currency_basket_available_utc")
    return pd.merge_asof(
        features,
        currency_sorted,
        left_on="bar_start_utc",
        right_on="currency_basket_available_utc",
        direction="backward",
    )


def currency_basket_context_summary(
    p: Paths, currency_context: pd.DataFrame, source_root: Path | None = None
) -> dict[str, Any]:
    source_files = json.loads(str(currency_context["source_files_json"].iloc[0])) if len(currency_context) else {}
    return {
        "source_root": relative(source_root or reference_etf_root(p)),
        "rows": len(currency_context),
        "start_utc": iso(currency_context["observation_utc"].min()) if len(currency_context) else "",
        "end_utc": iso(currency_context["observation_utc"].max()) if len(currency_context) else "",
        "available_through_utc": iso(currency_context["currency_basket_available_utc"].max()) if len(currency_context) else "",
        "files": source_files,
        "lag_policy": "Currency ETF daily observations are available to H4 bars only from the next UTC date.",
        "orientation": "Positive FXA/UUP and CYB/UUP indicate risk/non-USD currency strength versus UUP; positive FXF/UUP indicates Swiss-franc safe-haven strength versus UUP.",
    }


def load_bond_vol_context(p: Paths) -> pd.DataFrame:
    return load_bond_vol_context_from_root(reference_rates_root(p), recent=False)


def load_recent_bond_vol_context(p: Paths) -> pd.DataFrame:
    return load_bond_vol_context_from_root(recent_bond_vol_proxy_root(p), recent=True)


def load_bond_vol_context_from_root(root: Path, *, recent: bool) -> pd.DataFrame:
    config = BOND_VOL_FILES["move"]
    if recent:
        files = sorted(root.glob("move_daily_yahoo_*.csv"))
        if not files:
            raise FileNotFoundError(f"Missing recent bond-vol proxy file under {root}")
        path = files[-1]
    else:
        path = root / str(config["filename"])
    if not path.exists():
        raise FileNotFoundError(f"Missing bond-vol reference file: {path}")
    frame = pd.read_csv(path)
    symbol = str(config["symbol"])
    required = {"date_utc", f"{symbol}_close"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{path} missing required columns: {', '.join(sorted(missing))}")
    ctx = pd.DataFrame(
        {
            "observation_utc": pd.to_datetime(frame["date_utc"], utc=True, errors="coerce"),
            "move_close": pd.to_numeric(frame[f"{symbol}_close"], errors="coerce"),
        }
    ).dropna()
    ctx = ctx[ctx["move_close"] > 0].sort_values("observation_utc").reset_index(drop=True)
    ctx["move_5d_pct"] = ctx["move_close"].pct_change(5) * 100.0
    ctx["move_20d_pct"] = ctx["move_close"].pct_change(20) * 100.0
    ctx["move_60d_mean"] = ctx["move_close"].rolling(60, min_periods=40).mean()
    ctx["move_60d_std"] = ctx["move_close"].rolling(60, min_periods=40).std()
    ctx["move_z60"] = (ctx["move_close"] - ctx["move_60d_mean"]) / ctx["move_60d_std"]
    ctx["bond_vol_available_utc"] = ctx["observation_utc"] + pd.Timedelta(days=1)
    ctx["source_files_json"] = json.dumps({"move": relative(path)}, sort_keys=True)
    return ctx.dropna(subset=["move_5d_pct", "move_20d_pct", "move_z60"]).reset_index(drop=True)


def merge_bond_vol(frame: pd.DataFrame, bond_vol_context: pd.DataFrame, symbol: str) -> pd.DataFrame:
    features = with_features(frame, symbol).sort_values("bar_start_utc")
    bond_vol_sorted = bond_vol_context.sort_values("bond_vol_available_utc")
    return pd.merge_asof(
        features,
        bond_vol_sorted,
        left_on="bar_start_utc",
        right_on="bond_vol_available_utc",
        direction="backward",
    )


def bond_vol_context_summary(p: Paths, bond_vol_context: pd.DataFrame, source_root: Path | None = None) -> dict[str, Any]:
    source_files = json.loads(str(bond_vol_context["source_files_json"].iloc[0])) if len(bond_vol_context) else {}
    return {
        "source_root": relative(source_root or reference_rates_root(p)),
        "rows": len(bond_vol_context),
        "start_utc": iso(bond_vol_context["observation_utc"].min()) if len(bond_vol_context) else "",
        "end_utc": iso(bond_vol_context["observation_utc"].max()) if len(bond_vol_context) else "",
        "available_through_utc": iso(bond_vol_context["bond_vol_available_utc"].max()) if len(bond_vol_context) else "",
        "files": source_files,
        "lag_policy": "MOVE daily observations are available to H4 bars only from the next UTC date.",
        "orientation": "Rising/elevated MOVE indicates Treasury-rate volatility stress; falling MOVE indicates rates-vol calm/carry relief.",
    }


def load_crypto_risk_context(p: Paths) -> pd.DataFrame:
    return load_crypto_risk_context_from_root(reference_crypto_root(p), recent=False)


def load_recent_crypto_risk_context(p: Paths) -> pd.DataFrame:
    return load_crypto_risk_context_from_root(recent_crypto_risk_proxy_root(p), recent=True)


def load_crypto_risk_context_from_root(root: Path, *, recent: bool) -> pd.DataFrame:
    config = CRYPTO_RISK_FILES["btc"]
    if recent:
        files = sorted(root.glob("btc_usd_daily_yahoo_*.csv"))
        if not files:
            raise FileNotFoundError(f"Missing recent crypto-risk proxy file under {root}")
        path = files[-1]
    else:
        path = root / str(config["filename"])
    if not path.exists():
        raise FileNotFoundError(f"Missing crypto-risk reference file: {path}")
    frame = pd.read_csv(path)
    symbol = str(config["symbol"])
    required = {"date_utc", f"{symbol}_close"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{path} missing required columns: {', '.join(sorted(missing))}")
    ctx = pd.DataFrame(
        {
            "observation_utc": pd.to_datetime(frame["date_utc"], utc=True, errors="coerce"),
            "btc_close": pd.to_numeric(frame[f"{symbol}_close"], errors="coerce"),
        }
    ).dropna()
    ctx = ctx[ctx["btc_close"] > 0].sort_values("observation_utc").reset_index(drop=True)
    ctx["btc_5d_pct"] = ctx["btc_close"].pct_change(5) * 100.0
    ctx["btc_20d_pct"] = ctx["btc_close"].pct_change(20) * 100.0
    ctx["btc_60d_pct"] = ctx["btc_close"].pct_change(60) * 100.0
    ctx["btc_daily_pct"] = ctx["btc_close"].pct_change() * 100.0
    ctx["btc_vol20"] = ctx["btc_daily_pct"].rolling(20, min_periods=20).std()
    ctx["crypto_risk_available_utc"] = ctx["observation_utc"] + pd.Timedelta(days=1)
    ctx["source_files_json"] = json.dumps({"btc": relative(path)}, sort_keys=True)
    return ctx.dropna(subset=["btc_5d_pct", "btc_20d_pct", "btc_60d_pct", "btc_vol20"]).reset_index(drop=True)


def merge_crypto_risk(frame: pd.DataFrame, crypto_context: pd.DataFrame, symbol: str) -> pd.DataFrame:
    features = with_features(frame, symbol).sort_values("bar_start_utc")
    crypto_sorted = crypto_context.sort_values("crypto_risk_available_utc")
    return pd.merge_asof(
        features,
        crypto_sorted,
        left_on="bar_start_utc",
        right_on="crypto_risk_available_utc",
        direction="backward",
    )


def crypto_risk_context_summary(p: Paths, crypto_context: pd.DataFrame, source_root: Path | None = None) -> dict[str, Any]:
    source_files = json.loads(str(crypto_context["source_files_json"].iloc[0])) if len(crypto_context) else {}
    return {
        "source_root": relative(source_root or reference_crypto_root(p)),
        "rows": len(crypto_context),
        "start_utc": iso(crypto_context["observation_utc"].min()) if len(crypto_context) else "",
        "end_utc": iso(crypto_context["observation_utc"].max()) if len(crypto_context) else "",
        "available_through_utc": iso(crypto_context["crypto_risk_available_utc"].max()) if len(crypto_context) else "",
        "files": source_files,
        "lag_policy": "BTC daily observations are available to H4 bars only from the next UTC date.",
        "orientation": "Strong positive BTC momentum approximates crypto/risk appetite; sharp negative BTC momentum approximates crypto-risk stress.",
    }


def load_risk_context(p: Paths) -> pd.DataFrame:
    root = risk_source_root(p)
    frames: list[pd.DataFrame] = []
    for output_column, (filename, source_column) in RISK_SOURCE_FILES.items():
        path = root / filename
        if not path.exists():
            raise FileNotFoundError(f"Missing risk source file: {path}")
        frame = pd.read_csv(path)
        required = {"observation_date", source_column}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{path} missing required columns: {', '.join(sorted(missing))}")
        series = pd.DataFrame(
            {
                "observation_utc": pd.to_datetime(frame["observation_date"], utc=True, errors="coerce"),
                output_column: pd.to_numeric(frame[source_column].replace(".", pd.NA), errors="coerce"),
            }
        ).dropna()
        frames.append(series)
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="observation_utc", how="outer")
    merged = merged.sort_values("observation_utc").ffill().dropna().reset_index(drop=True)
    merged["risk_available_utc"] = merged["observation_utc"] + pd.Timedelta(days=1)
    merged["vix_5d_pct"] = merged["vix"].pct_change(5) * 100.0
    merged["vix_20d_pct"] = merged["vix"].pct_change(20) * 100.0
    merged["vix_vxv_ratio"] = merged["vix"] / merged["vxv"]
    return merged.dropna(subset=["vix_5d_pct", "vix_20d_pct", "vix_vxv_ratio"]).reset_index(drop=True)


def merge_risk(frame: pd.DataFrame, risk: pd.DataFrame, symbol: str) -> pd.DataFrame:
    features = with_features(frame, symbol).sort_values("bar_start_utc")
    risk_sorted = risk.sort_values("risk_available_utc")
    return pd.merge_asof(
        features,
        risk_sorted,
        left_on="bar_start_utc",
        right_on="risk_available_utc",
        direction="backward",
    )


def risk_context_summary(p: Paths, risk: pd.DataFrame) -> dict[str, Any]:
    return {
        "source_root": relative(risk_source_root(p)),
        "rows": len(risk),
        "start_utc": iso(risk["observation_utc"].min()),
        "end_utc": iso(risk["observation_utc"].max()),
        "available_through_utc": iso(risk["risk_available_utc"].max()),
        "files": {
            key: relative(risk_source_root(p) / filename)
            for key, (filename, _column) in RISK_SOURCE_FILES.items()
        },
        "lag_policy": "Risk observations are available to bars only from the next UTC date.",
    }


def load_fx_cross_context(p: Paths) -> dict[str, pd.DataFrame]:
    root = reference_fx_root(p)
    contexts: dict[str, pd.DataFrame] = {}
    for name, config in FX_CROSS_FILES.items():
        path = root / str(config["filename"])
        if not path.exists():
            raise FileNotFoundError(f"Missing FX cross reference file: {path}")
        frame = pd.read_csv(path)
        cross = str(config["cross"])
        anchor = str(config["anchor"])
        required = {"date_utc", f"{cross}_close", f"{anchor}_close"}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{path} missing required columns: {', '.join(sorted(missing))}")
        ctx = pd.DataFrame(
            {
                "observation_utc": pd.to_datetime(frame["date_utc"], utc=True, errors="coerce"),
                "cross_close": pd.to_numeric(frame[f"{cross}_close"], errors="coerce"),
                "anchor_close": pd.to_numeric(frame[f"{anchor}_close"], errors="coerce"),
            }
        ).dropna()
        ctx = ctx[(ctx["cross_close"] > 0) & (ctx["anchor_close"] > 0)].sort_values("observation_utc").reset_index(drop=True)
        ctx["cross_anchor_ratio"] = ctx["cross_close"] / ctx["anchor_close"]
        ctx["cross_anchor_5d_pct"] = ctx["cross_anchor_ratio"].pct_change(5) * 100.0
        ctx["cross_anchor_20d_pct"] = ctx["cross_anchor_ratio"].pct_change(20) * 100.0
        ctx["cross_available_utc"] = ctx["observation_utc"] + pd.Timedelta(days=1)
        ctx["source_file"] = relative(path)
        contexts[name] = ctx.dropna(subset=["cross_anchor_5d_pct", "cross_anchor_20d_pct"]).reset_index(drop=True)
    return contexts


def merge_fx_cross(frame: pd.DataFrame, cross_context: pd.DataFrame, symbol: str) -> pd.DataFrame:
    features = with_features(frame, symbol).sort_values("bar_start_utc")
    cross_sorted = cross_context.sort_values("cross_available_utc")
    return pd.merge_asof(
        features,
        cross_sorted,
        left_on="bar_start_utc",
        right_on="cross_available_utc",
        direction="backward",
    )


def fx_cross_context_summary(contexts: dict[str, pd.DataFrame]) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for name, frame in contexts.items():
        rows[name] = {
            "rows": len(frame),
            "start_utc": iso(frame["observation_utc"].min()) if len(frame) else "",
            "end_utc": iso(frame["observation_utc"].max()) if len(frame) else "",
            "available_through_utc": iso(frame["cross_available_utc"].max()) if len(frame) else "",
            "source_file": str(frame["source_file"].iloc[0]) if len(frame) else "",
        }
    return {
        "source_root": relative(reference_fx_root(paths())),
        "rows": rows,
        "lag_policy": "Daily FX cross observations are available to H4 bars only from the next UTC date.",
    }


def point_size(symbol: str) -> float:
    if "JPY" in symbol:
        return 0.001
    return 0.00001


def slippage_points(symbol: str, exit_reason: str) -> float:
    # Conservative first-screen assumptions. Stop exits carry more adverse slip.
    if "JPY" in symbol:
        entry = 2.0
        exit_slip = 5.0 if exit_reason.startswith("SL") or "ADVERSE" in exit_reason else 2.0
    else:
        entry = 1.0
        exit_slip = 3.0 if exit_reason.startswith("SL") or "ADVERSE" in exit_reason else 1.0
    return entry + exit_slip


def bar_files(bars_root: Path, broker: str, symbol: str, timeframe: str) -> list[Path]:
    folder = bars_root / broker / symbol / timeframe
    return sorted(folder.glob("*.csv")) if folder.exists() else []


def available_brokers(bars_root: Path) -> list[str]:
    if not bars_root.exists():
        return []
    return sorted(path.name for path in bars_root.iterdir() if path.is_dir())


def available_symbols(bars_root: Path) -> list[str]:
    found: set[str] = set(TARGET_SYMBOLS)
    for broker in available_brokers(bars_root):
        broker_dir = bars_root / broker
        for symbol_dir in broker_dir.iterdir():
            if symbol_dir.is_dir() and symbol_dir.name in FOREX_SYMBOLS:
                found.add(symbol_dir.name)
    return sorted(found)


def load_bars(bars_root: Path, broker: str, symbol: str, timeframe: str) -> pd.DataFrame:
    files = bar_files(bars_root, broker, symbol, timeframe)
    if not files:
        if timeframe == "H4":
            h1 = load_bars(bars_root, broker, symbol, "H1")
            if not h1.empty:
                return aggregate_h1_to_h4(h1, symbol)
        return pd.DataFrame()
    frame = pd.concat((pd.read_csv(path) for path in files), ignore_index=True)
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce")
    for column in ("open", "high", "low", "close"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    for column in ("spread_median_points", "spread_p95_points", "tick_count", "volume_sum"):
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if "bar_start_utc" in frame.columns:
        frame["bar_start_utc"] = pd.to_datetime(frame["bar_start_utc"], utc=True, errors="coerce")
    else:
        frame["bar_start_utc"] = frame["timestamp_utc"]
    frame = frame.dropna(subset=["timestamp_utc", "open", "high", "low", "close"])
    frame = frame.sort_values("timestamp_utc").drop_duplicates("timestamp_utc").reset_index(drop=True)
    return frame


def load_recent_proxy_bars(p: Paths, symbol: str, timeframe: str) -> pd.DataFrame:
    if timeframe == "H4":
        h1 = load_recent_proxy_bars(p, symbol, "H1")
        return aggregate_h1_to_h4(h1, symbol) if not h1.empty else pd.DataFrame()
    if timeframe != "H1":
        return pd.DataFrame()
    folder = recent_proxy_root(p) / symbol / "H1"
    files = sorted(folder.glob("*.csv")) if folder.exists() else []
    if not files:
        return pd.DataFrame()
    frame = pd.concat((pd.read_csv(path) for path in files), ignore_index=True)
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce")
    frame["bar_start_utc"] = pd.to_datetime(frame["bar_start_utc"], utc=True, errors="coerce")
    if "bar_end_utc" in frame.columns:
        frame["bar_end_utc"] = pd.to_datetime(frame["bar_end_utc"], utc=True, errors="coerce")
    else:
        frame["bar_end_utc"] = frame["bar_start_utc"] + pd.Timedelta(hours=1)
    for column in ("open", "high", "low", "close"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["timestamp_utc", "bar_start_utc", "open", "high", "low", "close"])
    frame["broker"] = "yahoo_recent_proxy"
    frame["symbol"] = symbol
    frame["timeframe"] = "H1"
    return frame.sort_values("timestamp_utc").drop_duplicates("timestamp_utc").reset_index(drop=True)


def aggregate_h1_to_h4(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
    if frame.empty or "bar_start_utc" not in frame.columns:
        return pd.DataFrame()
    work = frame.copy()
    work["h4_bucket"] = work["bar_start_utc"].dt.floor("4h")
    grouped = work.groupby("h4_bucket", sort=True)
    result = grouped.agg(
        timestamp_utc=("timestamp_utc", "max"),
        bar_start_utc=("bar_start_utc", "min"),
        bar_end_utc=("timestamp_utc", "max"),
        broker=("broker", "first"),
        symbol=("symbol", "first"),
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        spread_median_points=("spread_median_points", "median") if "spread_median_points" in work else ("close", "size"),
        spread_p95_points=("spread_p95_points", "max") if "spread_p95_points" in work else ("close", "size"),
        tick_count=("tick_count", "sum") if "tick_count" in work else ("close", "size"),
        volume_sum=("volume_sum", "sum") if "volume_sum" in work else ("close", "size"),
    ).reset_index(drop=True)
    result["timeframe"] = "H4"
    result["bar_end_utc"] = pd.to_datetime(result["bar_end_utc"], utc=True, errors="coerce")
    result["timestamp_utc"] = pd.to_datetime(result["timestamp_utc"], utc=True, errors="coerce")
    result["bar_start_utc"] = pd.to_datetime(result["bar_start_utc"], utc=True, errors="coerce")
    result["symbol"] = symbol
    return result.sort_values("timestamp_utc").drop_duplicates("timestamp_utc").reset_index(drop=True)


def atr_points(frame: pd.DataFrame, symbol: str, period: int = 14) -> pd.Series:
    prev_close = frame["close"].shift(1)
    true_range = pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - prev_close).abs(),
            (frame["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.rolling(period, min_periods=period).mean() / point_size(symbol)


def positive_median(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce")
    values = values[(values > 0) & values.notna()]
    if values.empty:
        return float("nan")
    return float(values.median())


def positive_quantile(series: pd.Series, q: float) -> float:
    values = pd.to_numeric(series, errors="coerce")
    values = values[(values > 0) & values.notna()]
    if values.empty:
        return float("nan")
    return float(values.quantile(q))


def cost_geometry_scan(p: Paths) -> list[CostCell]:
    rows: list[CostCell] = []
    symbols = available_symbols(p.bars)
    for broker in available_brokers(p.bars):
        for symbol in symbols:
            for timeframe in TARGET_TIMEFRAMES:
                files = bar_files(p.bars, broker, symbol, timeframe)
                frame = load_bars(p.bars, broker, symbol, timeframe)
                if not files and frame.empty:
                    rows.append(
                        CostCell(
                            broker=broker,
                            symbol=symbol,
                            timeframe=timeframe,
                            file_count=0,
                            rows=0,
                            start_utc="",
                            end_utc="",
                            point_size=point_size(symbol),
                            clean_ohlc=False,
                            has_spread=False,
                            spread_median_points=float("nan"),
                            spread_p95_points=float("nan"),
                            atr14_median_points=float("nan"),
                            atr14_recent_median_points=float("nan"),
                            representative_stop_points=float("nan"),
                            representative_stop_recent_points=float("nan"),
                            cost_r_median=float("nan"),
                            cost_r_p95=float("nan"),
                            cost_r_recent_p95=float("nan"),
                            data_status="MISSING",
                            spread_status="MISSING",
                        )
                    )
                    continue
                atr = atr_points(frame, symbol)
                recent_mask = frame["timestamp_utc"] >= RECENT_START
                atr_median = positive_median(atr)
                atr_recent = positive_median(atr[recent_mask])
                spread_median = positive_median(frame.get("spread_median_points", pd.Series(dtype=float)))
                spread_p95 = positive_quantile(frame.get("spread_p95_points", pd.Series(dtype=float)), 0.95)
                if math.isnan(spread_p95):
                    spread_p95 = positive_quantile(frame.get("spread_median_points", pd.Series(dtype=float)), 0.95)
                has_spread = not math.isnan(spread_median) and not math.isnan(spread_p95)
                representative_stop = atr_median
                representative_stop_recent = atr_recent if not math.isnan(atr_recent) else atr_median
                latest = frame["timestamp_utc"].max()
                clean_ohlc = len(frame) >= min_rows_for_timeframe(timeframe) and latest >= LOCAL_FRESHNESS_CUTOFF
                derived = not files and timeframe == "H4"
                rows.append(
                    CostCell(
                        broker=broker,
                        symbol=symbol,
                        timeframe=timeframe,
                        file_count=len(files),
                        rows=len(frame),
                        start_utc=iso(frame["timestamp_utc"].min()),
                        end_utc=iso(latest),
                        point_size=point_size(symbol),
                        clean_ohlc=clean_ohlc,
                        has_spread=has_spread,
                        spread_median_points=spread_median,
                        spread_p95_points=spread_p95,
                        atr14_median_points=atr_median,
                        atr14_recent_median_points=atr_recent,
                        representative_stop_points=representative_stop,
                        representative_stop_recent_points=representative_stop_recent,
                        cost_r_median=safe_div(spread_median, representative_stop),
                        cost_r_p95=safe_div(spread_p95, representative_stop),
                        cost_r_recent_p95=safe_div(spread_p95, representative_stop_recent),
                        data_status=("CLEAN_DERIVED_FROM_H1" if derived else "CLEAN") if clean_ohlc else ("DERIVED_LIMITED_OR_STALE" if derived else "LIMITED_OR_STALE"),
                        spread_status=("DERIVED_BAR_SPREAD" if derived else "BAR_SPREAD") if has_spread else "NO_LOCAL_SPREAD",
                    )
                )
    return rows


def min_rows_for_timeframe(timeframe: str) -> int:
    return {"M5": 100_000, "M15": 30_000, "H1": 8_000, "H4": 2_000}[timeframe]


def safe_div(numerator: float, denominator: float) -> float:
    if math.isnan(numerator) or math.isnan(denominator) or denominator <= 0:
        return float("nan")
    return numerator / denominator


def write_cost_outputs(p: Paths, cells: list[CostCell]) -> None:
    csv_path = p.tables / f"FOREX_COST_GEOMETRY_SCAN_{RUN_DATE}.csv"
    fields = list(CostCell.__dataclass_fields__.keys())
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for cell in cells:
            writer.writerow(dataclass_row(cell))

    eligible = [
        cell
        for cell in cells
        if cell.clean_ohlc and cell.has_spread and cell.timeframe in TARGET_TIMEFRAMES and not math.isnan(cell.cost_r_recent_p95)
    ]
    eligible.sort(key=lambda cell: (cell.cost_r_recent_p95, cell.cost_r_p95, cell.symbol, cell.timeframe, cell.broker))
    report = render_cost_report(cells, eligible, csv_path)
    (p.reports / f"FOREX_COST_GEOMETRY_SCAN_{RUN_DATE}.md").write_text(report, encoding="utf-8")


def dataclass_row(obj: Any) -> dict[str, Any]:
    row = {}
    for key in obj.__dataclass_fields__:
        value = getattr(obj, key)
        if isinstance(value, float):
            row[key] = "" if math.isnan(value) else f"{value:.8f}"
        else:
            row[key] = value
    return row


def render_cost_report(cells: list[CostCell], eligible: list[CostCell], csv_path: Path) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    missing_gbp = not any(cell.symbol == "GBPUSD" and cell.file_count > 0 for cell in cells)
    lines = [
        "# Forex Cost Geometry Scan",
        "",
        f"Generated at UTC: {generated}",
        "Status: RESEARCH_ONLY",
        "",
        "Boundary: offline local-bar scan only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Definition: cost_R = spread_points / representative_stop_points. Representative stop is median ATR14 in points for the symbol/timeframe cell; recent uses rows from 2022-01-01 onward.",
        "",
        f"CSV: `{relative(csv_path)}`",
        "",
        "## Available Data Read",
        "",
        f"- GBPUSD processed bars: {'missing' if missing_gbp else 'present'}",
        "- Capital.com EURUSD/USDJPY cells carry usable spread columns.",
        "- Dukascopy EURUSD derived M15/H1/H4/D1 cells are usable for OHLC robustness but do not carry clean local spread fields; use only with disclosed cost proxy.",
        "- Local processed Forex data currently ends around 2025-06/2025-07, so this is not a 2026-current-market confirmation.",
        "",
        "## Cost-Favorable Cells",
        "",
        "| rank | broker | symbol | timeframe | rows | end_utc | median_spread_pts | p95_spread_pts | median_ATR14_pts | recent_ATR14_pts | p95_cost_R_recent |",
        "| ---: | --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for rank, cell in enumerate(eligible[:20], start=1):
        lines.append(
            "| {rank} | {broker} | {symbol} | {tf} | {rows} | {end} | {spread:.2f} | {p95:.2f} | {atr:.2f} | {ratr:.2f} | {cost:.4f} |".format(
                rank=rank,
                broker=cell.broker,
                symbol=cell.symbol,
                tf=cell.timeframe,
                rows=cell.rows,
                end=cell.end_utc[:10],
                spread=cell.spread_median_points,
                p95=cell.spread_p95_points,
                atr=cell.atr14_median_points,
                ratr=cell.atr14_recent_median_points,
                cost=cell.cost_r_recent_p95,
            )
        )
    lines.extend(
        [
            "",
            "Read: the first screen should prioritize H4/H1 cells with low p95 cost_R and enough trade frequency, then use M15/M5 only if the candidate stop is demonstrably wide enough.",
            "",
        ]
    )
    return "\n".join(lines)


def with_features(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
    result = frame.copy()
    result["atr14_points"] = atr_points(result, symbol)
    result["range_points"] = (result["high"] - result["low"]) / point_size(symbol)
    result["body_points"] = (result["close"] - result["open"]).abs() / point_size(symbol)
    result["ema20"] = result["close"].ewm(span=20, adjust=False, min_periods=20).mean()
    result["ema50"] = result["close"].ewm(span=50, adjust=False, min_periods=50).mean()
    result["ema100"] = result["close"].ewm(span=100, adjust=False, min_periods=100).mean()
    result["ema200"] = result["close"].ewm(span=200, adjust=False, min_periods=200).mean()
    result["hour_utc"] = result["bar_start_utc"].dt.hour
    result["date_utc"] = result["bar_start_utc"].dt.date.astype(str)
    return result


def with_weekly_structure_features(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
    result = with_features(frame, symbol)
    result["iso_week"] = result["bar_start_utc"].dt.strftime("%G-W%V")
    weekly = (
        result.groupby("iso_week", sort=True)
        .agg(
            week_open=("open", "first"),
            week_high=("high", "max"),
            week_low=("low", "min"),
            week_close=("close", "last"),
        )
        .reset_index()
    )
    weekly["prev_week_high"] = weekly["week_high"].shift(1)
    weekly["prev_week_low"] = weekly["week_low"].shift(1)
    weekly["prev_week_open"] = weekly["week_open"].shift(1)
    weekly["prev_week_close"] = weekly["week_close"].shift(1)
    weekly["prev_week_range"] = weekly["week_high"].shift(1) - weekly["week_low"].shift(1)
    weekly["prev_week_direction"] = weekly["prev_week_close"] - weekly["prev_week_open"]
    return result.merge(
        weekly[
            [
                "iso_week",
                "week_open",
                "prev_week_high",
                "prev_week_low",
                "prev_week_open",
                "prev_week_close",
                "prev_week_range",
                "prev_week_direction",
            ]
        ],
        on="iso_week",
        how="left",
    )


def candidate_specs() -> list[CandidateSpec]:
    return [
        CandidateSpec(
            candidate_id="eurusd_h4_compression_breakout_v0",
            symbol="EURUSD",
            timeframe="H4",
            family="volatility compression / directional expansion",
            description="EURUSD H4 breakout from a 10-bar compression box, filtered by ATR contraction.",
            generator=signals_h4_compression_breakout,
            max_hold_bars=18,
        ),
        CandidateSpec(
            candidate_id="eurusd_h1_london_asia_range_breakout_v0",
            symbol="EURUSD",
            timeframe="H1",
            family="FX session structure / London expansion",
            description="EURUSD H1 London-session breakout of the completed Asia range, one signal per day.",
            generator=signals_h1_london_asia_breakout,
            max_hold_bars=8,
            target_r=1.2,
        ),
        CandidateSpec(
            candidate_id="usdjpy_h4_trend_continuation_pullback_v0",
            symbol="USDJPY",
            timeframe="H4",
            family="JPY carry-trend continuation / pullback",
            description="USDJPY H4 trend-continuation after a controlled pullback into EMA20/EMA50.",
            generator=signals_h4_usdjpy_trend_pullback,
            max_hold_bars=18,
        ),
        CandidateSpec(
            candidate_id="usdjpy_h1_tokyo_range_failed_break_v0",
            symbol="USDJPY",
            timeframe="H1",
            family="FX session liquidity / Tokyo range failed break",
            description="USDJPY H1 fade of failed Tokyo-range breaks during the London handoff.",
            generator=signals_h1_tokyo_failed_break,
            max_hold_bars=8,
            target_r=1.2,
        ),
    ]


def candidate_specs_second_pass() -> list[CandidateSpec]:
    return [
        CandidateSpec(
            candidate_id="usdjpy_h4_carry_session_pullback_v1",
            symbol="USDJPY",
            timeframe="H4",
            family="JPY carry-regime / session-filtered pullback",
            description=(
                "USDJPY H4 long-only pullback in an established upside regime, restricted to Asia "
                "and NY-morning bars. This is a new v1 derived from the failed v0 diagnostic, not a "
                "tuned approval candidate."
            ),
            generator=signals_h4_usdjpy_carry_session_pullback_v1,
            max_hold_bars=18,
            target_r=1.5,
        ),
        CandidateSpec(
            candidate_id="eurusd_h4_range_rejection_reversion_v0",
            symbol="EURUSD",
            timeframe="H4",
            family="FX range rejection / mean reversion",
            description=(
                "EURUSD H4 fade of failed 24-bar range breaks when the medium-term EMA slope is flat. "
                "This tests a non-XAU, non-momentum FX behavior on the low-cost H4 cell."
            ),
            generator=signals_h4_eurusd_range_rejection_reversion_v0,
            max_hold_bars=10,
            target_r=1.2,
        ),
    ]


def candidate_specs_recent_proxy() -> list[CandidateSpec]:
    return candidate_specs() + candidate_specs_second_pass()


def candidate_specs_calendar_session() -> list[CandidateSpec]:
    return [
        CandidateSpec(
            candidate_id="eurusd_h1_ny_fix_overextension_reversion_v0",
            symbol="EURUSD",
            timeframe="H1",
            family="FX calendar/session NY-fix reversion",
            description="EURUSD H1 fade of same-day overextension during the NY fix window after an intraday reversal candle.",
            generator=signals_h1_eurusd_ny_fix_overextension_reversion,
            max_hold_bars=6,
            target_r=1.15,
        ),
        CandidateSpec(
            candidate_id="usdjpy_h4_month_turn_carry_pullback_v0",
            symbol="USDJPY",
            timeframe="H4",
            family="FX calendar/session month-turn carry pullback",
            description="USDJPY H4 trend pullback during month-turn windows, testing carry/rebalance flow rather than raw momentum.",
            generator=signals_h4_usdjpy_month_turn_carry_pullback,
            max_hold_bars=16,
            target_r=1.35,
        ),
    ]


def candidate_specs_weekly_structure() -> list[CandidateSpec]:
    return [
        CandidateSpec(
            candidate_id="eurusd_h4_weekly_liquidity_reversion_v0",
            symbol="EURUSD",
            timeframe="H4",
            family="FX weekly liquidity reversion",
            description="EURUSD H4 fade of early-week failed probes beyond the prior week range in flat medium-term conditions.",
            generator=signals_h4_eurusd_weekly_liquidity_reversion,
            max_hold_bars=10,
            target_r=1.20,
        ),
        CandidateSpec(
            candidate_id="usdjpy_h4_weekly_carry_continuation_v0",
            symbol="USDJPY",
            timeframe="H4",
            family="FX weekly carry continuation",
            description="USDJPY H4 pullback-continuation after prior-week expansion, restricted to Asia/NY-morning entry timing.",
            generator=signals_h4_usdjpy_weekly_carry_continuation,
            max_hold_bars=14,
            target_r=1.35,
        ),
        CandidateSpec(
            candidate_id="eurusd_h4_weekly_open_reversion_v0",
            symbol="EURUSD",
            timeframe="H4",
            family="FX weekly open reversion",
            description="EURUSD H4 fade of mid/late-week extension away from the weekly open in flat medium-term conditions.",
            generator=signals_h4_eurusd_weekly_open_reversion,
            max_hold_bars=10,
            target_r=1.15,
        ),
    ]


def candidate_specs_global_risk(global_risk: pd.DataFrame) -> list[CandidateSpec]:
    return [
        CandidateSpec(
            candidate_id="eurusd_h4_global_risk_dollar_beta_pullback_v0",
            symbol="EURUSD",
            timeframe="H4",
            family="global risk/credit dollar-beta pullback",
            description="EURUSD H4 trend pullback when lagged EEM/SPY and HYG/IEF risk appetite align with euro-vs-dollar direction.",
            generator=lambda frame: signals_h4_eurusd_global_risk_pullback(frame, global_risk),
            max_hold_bars=14,
            target_r=1.35,
        ),
        CandidateSpec(
            candidate_id="usdjpy_h4_global_risk_credit_pullback_v0",
            symbol="USDJPY",
            timeframe="H4",
            family="global risk/credit yen pullback",
            description="USDJPY H4 trend pullback when lagged EEM/SPY and HYG/IEF risk appetite align with yen carry or defensive yen pressure.",
            generator=lambda frame: signals_h4_usdjpy_global_risk_pullback(frame, global_risk),
            max_hold_bars=14,
            target_r=1.35,
        ),
    ]


def candidate_specs_commodity_dollar(commodity_context: pd.DataFrame) -> list[CandidateSpec]:
    return [
        CandidateSpec(
            candidate_id="eurusd_h4_commodity_dollar_reflation_pullback_v0",
            symbol="EURUSD",
            timeframe="H4",
            family="commodity/dollar reflation pullback",
            description="EURUSD H4 trend pullback when lagged DBC/UUP and DBB/UUP commodity-vs-dollar pressure align with direction.",
            generator=lambda frame: signals_h4_eurusd_commodity_dollar_pullback(frame, commodity_context),
            max_hold_bars=14,
            target_r=1.35,
        ),
        CandidateSpec(
            candidate_id="usdjpy_h4_commodity_dollar_reflation_pullback_v0",
            symbol="USDJPY",
            timeframe="H4",
            family="commodity/dollar reflation yen pullback",
            description="USDJPY H4 trend pullback when lagged DBC/UUP and DBB/UUP commodity-vs-dollar pressure align with carry/reflation or defensive pressure.",
            generator=lambda frame: signals_h4_usdjpy_commodity_dollar_pullback(frame, commodity_context),
            max_hold_bars=14,
            target_r=1.35,
        ),
    ]


def candidate_specs_real_asset_rotation(real_asset_context: pd.DataFrame) -> list[CandidateSpec]:
    return [
        CandidateSpec(
            candidate_id="eurusd_h4_real_asset_reflation_pullback_v0",
            symbol="EURUSD",
            timeframe="H4",
            family="real-asset reflation dollar pullback",
            description="EURUSD H4 trend pullback when lagged USO/UUP, HG/GC, and SLV/GLD real-asset rotation aligns with euro-vs-dollar direction.",
            generator=lambda frame: signals_h4_eurusd_real_asset_reflation_pullback(frame, real_asset_context),
            max_hold_bars=14,
            target_r=1.35,
        ),
        CandidateSpec(
            candidate_id="usdjpy_h4_real_asset_carry_pullback_v0",
            symbol="USDJPY",
            timeframe="H4",
            family="real-asset reflation yen pullback",
            description="USDJPY H4 trend pullback when lagged oil/dollar and cyclical-metal/gold rotation aligns with carry or safe-haven pressure.",
            generator=lambda frame: signals_h4_usdjpy_real_asset_carry_pullback(frame, real_asset_context),
            max_hold_bars=14,
            target_r=1.35,
        ),
    ]


def candidate_specs_haven_liquidity(haven_context: pd.DataFrame) -> list[CandidateSpec]:
    return [
        CandidateSpec(
            candidate_id="usdjpy_h4_haven_liquidity_yen_pullback_v0",
            symbol="USDJPY",
            timeframe="H4",
            family="haven/liquidity yen pullback",
            description="USDJPY H4 pullback-continuation when lagged GLD, GDX/GLD, SPY/TLT, and XLU/XLK indicate haven pressure or liquidity relief.",
            generator=lambda frame: signals_h4_usdjpy_haven_liquidity_pullback(frame, haven_context),
            max_hold_bars=14,
            target_r=1.35,
        ),
        CandidateSpec(
            candidate_id="eurusd_h4_haven_liquidity_dollar_pullback_v0",
            symbol="EURUSD",
            timeframe="H4",
            family="haven/liquidity dollar pullback",
            description="EURUSD H4 pullback-continuation when lagged haven/liquidity pressure aligns with dollar squeeze or risk-relief direction.",
            generator=lambda frame: signals_h4_eurusd_haven_liquidity_pullback(frame, haven_context),
            max_hold_bars=14,
            target_r=1.35,
        ),
    ]


def candidate_specs_financial_liquidity(financial_context: pd.DataFrame) -> list[CandidateSpec]:
    return [
        CandidateSpec(
            candidate_id="eurusd_h4_financial_liquidity_dollar_squeeze_pullback_v0",
            symbol="EURUSD",
            timeframe="H4",
            family="financial conditions / dollar-liquidity pullback",
            description="EURUSD H4 trend pullback keyed to lagged FRED NFCI/ANFCI tightening or easing plus Fed balance-sheet liquidity.",
            generator=lambda frame: signals_h4_eurusd_financial_liquidity_pullback(frame, financial_context),
            max_hold_bars=16,
            target_r=1.35,
        ),
        CandidateSpec(
            candidate_id="usdjpy_h4_financial_liquidity_carry_pullback_v0",
            symbol="USDJPY",
            timeframe="H4",
            family="financial conditions / JPY carry-liquidity pullback",
            description="USDJPY H4 carry/risk pullback keyed to lagged FRED NFCI/ANFCI and Fed balance-sheet liquidity.",
            generator=lambda frame: signals_h4_usdjpy_financial_liquidity_pullback(frame, financial_context),
            max_hold_bars=16,
            target_r=1.35,
        ),
    ]


def candidate_specs_cot_positioning(cot_context: pd.DataFrame) -> list[CandidateSpec]:
    return [
        CandidateSpec(
            candidate_id="eurusd_h4_cot_lev_positioning_reversal_v0",
            symbol="EURUSD",
            timeframe="H4",
            family="CFTC leveraged-money positioning reversal",
            description="EURUSD H4 failed-break reversal when lagged CFTC Euro FX leveraged-money positioning is stretched and starting to unwind.",
            generator=lambda frame: signals_h4_eurusd_cot_positioning_reversal(frame, cot_context),
            max_hold_bars=18,
            target_r=1.35,
        ),
        CandidateSpec(
            candidate_id="usdjpy_h4_cot_yen_positioning_reversal_v0",
            symbol="USDJPY",
            timeframe="H4",
            family="CFTC yen leveraged-money positioning reversal",
            description="USDJPY H4 failed-break reversal when lagged CFTC Japanese Yen leveraged-money positioning is stretched after inverting to USDJPY orientation.",
            generator=lambda frame: signals_h4_usdjpy_cot_positioning_reversal(frame, cot_context),
            max_hold_bars=18,
            target_r=1.35,
        ),
    ]


def candidate_specs_treasury_curve(curve_context: pd.DataFrame) -> list[CandidateSpec]:
    return [
        CandidateSpec(
            candidate_id="usdjpy_h4_treasury_curve_frontend_pullback_v0",
            symbol="USDJPY",
            timeframe="H4",
            family="Treasury curve front-end carry pullback",
            description="USDJPY H4 pullback when lagged DGS2/DGS10/T10Y2Y front-end pressure or bull-steepening aligns with yen direction.",
            generator=lambda frame: signals_h4_usdjpy_treasury_curve_pullback(frame, curve_context),
            max_hold_bars=14,
            target_r=1.35,
        ),
        CandidateSpec(
            candidate_id="eurusd_h4_treasury_curve_dollar_pressure_pullback_v0",
            symbol="EURUSD",
            timeframe="H4",
            family="Treasury curve dollar-pressure pullback",
            description="EURUSD H4 pullback when lagged Treasury front-end/curve pressure aligns with dollar squeeze or dollar relief.",
            generator=lambda frame: signals_h4_eurusd_treasury_curve_pullback(frame, curve_context),
            max_hold_bars=14,
            target_r=1.35,
        ),
    ]


def candidate_specs_rates_dollar(rates_context: pd.DataFrame) -> list[CandidateSpec]:
    return [
        CandidateSpec(
            candidate_id="eurusd_h4_rates_dollar_duration_pullback_v0",
            symbol="EURUSD",
            timeframe="H4",
            family="rates/dollar duration pullback",
            description="EURUSD H4 pullback-continuation when lagged TLT/UUP and TLT/SHY duration pressure align with euro-vs-dollar direction.",
            generator=lambda frame: signals_h4_eurusd_rates_dollar_pullback(frame, rates_context),
            max_hold_bars=14,
            target_r=1.35,
        ),
        CandidateSpec(
            candidate_id="usdjpy_h4_rates_dollar_yield_pullback_v0",
            symbol="USDJPY",
            timeframe="H4",
            family="rates/dollar yield pullback",
            description="USDJPY H4 pullback-continuation when lagged TLT/UUP and TLT/SHY duration pressure align with yield-dollar or duration-bid yen direction.",
            generator=lambda frame: signals_h4_usdjpy_rates_dollar_pullback(frame, rates_context),
            max_hold_bars=14,
            target_r=1.35,
        ),
        CandidateSpec(
            candidate_id="eurusd_h4_rates_dollar_yield_pressure_short_session_v1",
            symbol="EURUSD",
            timeframe="H4",
            family="rates/dollar yield-pressure short session",
            description=(
                "EURUSD H4 short-only pullback under lagged TLT/UUP and TLT/SHY yield-dollar pressure, "
                "excluding NY-late and rollover timing. This is a v1 follow-up from the rates/dollar v0 "
                "direction/session diagnostic, not an approval candidate."
            ),
            generator=lambda frame: signals_h4_eurusd_rates_dollar_yield_pressure_short_session_v1(frame, rates_context),
            max_hold_bars=14,
            target_r=1.35,
        ),
    ]


def candidate_specs_equity_leadership(equity_context: pd.DataFrame) -> list[CandidateSpec]:
    return [
        CandidateSpec(
            candidate_id="eurusd_h4_exus_equity_leadership_pullback_v0",
            symbol="EURUSD",
            timeframe="H4",
            family="equity leadership FX pullback",
            description="EURUSD H4 pullback-continuation when lagged ACWX/SPY ex-US equity leadership aligns with euro-vs-dollar trend.",
            generator=lambda frame: signals_h4_eurusd_exus_equity_leadership_pullback(frame, equity_context),
            max_hold_bars=14,
            target_r=1.35,
        ),
        CandidateSpec(
            candidate_id="usdjpy_h4_us_cyclical_leadership_pullback_v0",
            symbol="USDJPY",
            timeframe="H4",
            family="equity leadership yen pullback",
            description="USDJPY H4 pullback-continuation when lagged IWM/SPY and XLF/XLU cyclical leadership aligns with carry or defensive yen pressure.",
            generator=lambda frame: signals_h4_usdjpy_us_cyclical_leadership_pullback(frame, equity_context),
            max_hold_bars=14,
            target_r=1.35,
        ),
    ]


def candidate_specs_sector_rotation(sector_context: pd.DataFrame) -> list[CandidateSpec]:
    return [
        CandidateSpec(
            candidate_id="eurusd_h4_sector_growth_rotation_pullback_v0",
            symbol="EURUSD",
            timeframe="H4",
            family="sector-rotation growth/defensive FX pullback",
            description="EURUSD H4 pullback-continuation when lagged XLY/XLP and QQQ/SPY growth rotation aligns with euro-vs-dollar trend.",
            generator=lambda frame: signals_h4_eurusd_sector_growth_rotation_pullback(frame, sector_context),
            max_hold_bars=14,
            target_r=1.35,
        ),
        CandidateSpec(
            candidate_id="usdjpy_h4_sector_cyclical_carry_pullback_v0",
            symbol="USDJPY",
            timeframe="H4",
            family="sector-rotation cyclical/inflation yen pullback",
            description="USDJPY H4 pullback-continuation when lagged cyclical sector and TIP/IEF rotation aligns with carry or defensive yen pressure.",
            generator=lambda frame: signals_h4_usdjpy_sector_cyclical_carry_pullback(frame, sector_context),
            max_hold_bars=14,
            target_r=1.35,
        ),
    ]


def candidate_specs_currency_basket(currency_context: pd.DataFrame) -> list[CandidateSpec]:
    return [
        CandidateSpec(
            candidate_id="eurusd_h4_currency_basket_dollar_pressure_pullback_v0",
            symbol="EURUSD",
            timeframe="H4",
            family="currency-basket dollar-pressure FX pullback",
            description="EURUSD H4 pullback-continuation when lagged FXA/UUP and CYB/UUP currency-basket pressure aligns with euro-vs-dollar trend.",
            generator=lambda frame: signals_h4_eurusd_currency_basket_dollar_pressure_pullback(frame, currency_context),
            max_hold_bars=14,
            target_r=1.35,
        ),
        CandidateSpec(
            candidate_id="usdjpy_h4_safe_haven_currency_rotation_pullback_v0",
            symbol="USDJPY",
            timeframe="H4",
            family="currency-basket safe-haven yen pullback",
            description="USDJPY H4 pullback-continuation when lagged FXA/UUP risk-currency and FXF/UUP safe-haven rotation aligns with carry or yen-stress trend.",
            generator=lambda frame: signals_h4_usdjpy_safe_haven_currency_rotation_pullback(frame, currency_context),
            max_hold_bars=14,
            target_r=1.35,
        ),
    ]


def candidate_specs_recent_currency_basket(currency_context: pd.DataFrame) -> list[CandidateSpec]:
    specs: list[CandidateSpec] = []
    if {
        "fxa_uup_5d_pct",
        "fxa_uup_20d_pct",
        "cyb_uup_20d_pct",
        "risk_currency_score",
    }.issubset(currency_context.columns):
        specs.append(candidate_specs_currency_basket(currency_context)[0])
    if {
        "fxa_uup_5d_pct",
        "fxa_uup_20d_pct",
        "fxf_uup_5d_pct",
        "fxf_uup_20d_pct",
        "safe_haven_score",
    }.issubset(currency_context.columns):
        specs.append(candidate_specs_currency_basket(currency_context)[1])
    return specs


def candidate_specs_bond_vol(bond_vol_context: pd.DataFrame) -> list[CandidateSpec]:
    return [
        CandidateSpec(
            candidate_id="eurusd_h4_bond_vol_dollar_stress_pullback_v0",
            symbol="EURUSD",
            timeframe="H4",
            family="bond-volatility FX pullback",
            description="EURUSD H4 pullback-continuation when lagged MOVE bond-volatility stress or calm aligns with euro-vs-dollar trend.",
            generator=lambda frame: signals_h4_eurusd_bond_vol_pullback(frame, bond_vol_context),
            max_hold_bars=14,
            target_r=1.35,
        ),
        CandidateSpec(
            candidate_id="usdjpy_h4_bond_vol_carry_pullback_v0",
            symbol="USDJPY",
            timeframe="H4",
            family="bond-volatility yen pullback",
            description="USDJPY H4 pullback-continuation when lagged MOVE bond-volatility stress or calm aligns with carry or defensive yen pressure.",
            generator=lambda frame: signals_h4_usdjpy_bond_vol_pullback(frame, bond_vol_context),
            max_hold_bars=14,
            target_r=1.35,
        ),
        CandidateSpec(
            candidate_id="usdjpy_h4_bond_vol_asia_session_carry_relief_v1",
            symbol="USDJPY",
            timeframe="H4",
            family="bond-volatility Asia-session yen pullback",
            description=(
                "USDJPY H4 Asia-session-only pullback under lagged MOVE calm or stress. This is a v1 "
                "follow-up from the bond-vol v0 session diagnostic, not an approval candidate."
            ),
            generator=lambda frame: signals_h4_usdjpy_bond_vol_asia_session_v1(frame, bond_vol_context),
            max_hold_bars=14,
            target_r=1.35,
        ),
    ]


def candidate_specs_crypto_risk(crypto_context: pd.DataFrame) -> list[CandidateSpec]:
    return [
        CandidateSpec(
            candidate_id="eurusd_h4_btc_risk_beta_pullback_v0",
            symbol="EURUSD",
            timeframe="H4",
            family="BTC crypto-risk FX pullback",
            description="EURUSD H4 pullback-continuation when lagged BTC risk-on/risk-off momentum aligns with euro-vs-dollar trend.",
            generator=lambda frame: signals_h4_eurusd_btc_risk_pullback(frame, crypto_context),
            max_hold_bars=14,
            target_r=1.35,
        ),
        CandidateSpec(
            candidate_id="usdjpy_h4_btc_risk_carry_pullback_v0",
            symbol="USDJPY",
            timeframe="H4",
            family="BTC crypto-risk yen pullback",
            description="USDJPY H4 pullback-continuation when lagged BTC risk-on/risk-off momentum aligns with carry or defensive yen pressure.",
            generator=lambda frame: signals_h4_usdjpy_btc_risk_pullback(frame, crypto_context),
            max_hold_bars=14,
            target_r=1.35,
        ),
    ]


def candidate_specs_macro(macro: pd.DataFrame) -> list[CandidateSpec]:
    return [
        CandidateSpec(
            candidate_id="eurusd_h4_real_yield_dollar_pressure_reversal_v0",
            symbol="EURUSD",
            timeframe="H4",
            family="macro/rate dollar-pressure reversal",
            description="EURUSD H4 fade of failed range breaks after lagged real-yield and broad-dollar pressure extremes.",
            generator=lambda frame: signals_h4_eurusd_macro_pressure_reversal(frame, macro),
            max_hold_bars=12,
            target_r=1.25,
        ),
        CandidateSpec(
            candidate_id="eurusd_h4_real_yield_dollar_pressure_followthrough_v0",
            symbol="EURUSD",
            timeframe="H4",
            family="macro/rate dollar-pressure follow-through",
            description="EURUSD H4 trend-continuation pullback when lagged real-yield and broad-dollar pressure align.",
            generator=lambda frame: signals_h4_eurusd_macro_pressure_followthrough(frame, macro),
            max_hold_bars=14,
            target_r=1.4,
        ),
        CandidateSpec(
            candidate_id="usdjpy_h4_real_yield_dollar_pressure_followthrough_v0",
            symbol="USDJPY",
            timeframe="H4",
            family="macro/rate USDJPY pressure follow-through",
            description="USDJPY H4 pullback-continuation when lagged real-yield and broad-dollar pressure align with trend.",
            generator=lambda frame: signals_h4_usdjpy_macro_pressure_followthrough(frame, macro),
            max_hold_bars=14,
            target_r=1.4,
        ),
    ]


def candidate_specs_cny_pressure(cny: pd.DataFrame) -> list[CandidateSpec]:
    return [
        CandidateSpec(
            candidate_id="eurusd_h4_cny_dollar_pressure_pullback_v0",
            symbol="EURUSD",
            timeframe="H4",
            family="CNY/dollar pressure pullback",
            description="EURUSD H4 pullback-continuation when lagged USD/CNY and broad-dollar pressure align with trend.",
            generator=lambda frame: signals_h4_eurusd_cny_dollar_pressure_pullback(frame, cny),
            max_hold_bars=14,
            target_r=1.35,
        ),
        CandidateSpec(
            candidate_id="usdjpy_h4_cny_shock_yen_reversion_v0",
            symbol="USDJPY",
            timeframe="H4",
            family="CNY shock yen reversion",
            description="USDJPY H4 range rejection when lagged CNY shock or unwind suggests risk-sensitive yen rotation.",
            generator=lambda frame: signals_h4_usdjpy_cny_shock_yen_reversion(frame, cny),
            max_hold_bars=12,
            target_r=1.25,
        ),
    ]


def candidate_specs_external_flow(contexts: dict[str, pd.DataFrame]) -> list[CandidateSpec]:
    eur_flow = contexts["EURUSD"]
    jpy_flow = contexts["USDJPY"]
    return [
        CandidateSpec(
            candidate_id="eurusd_h4_currency_etf_flow_pullback_v0",
            symbol="EURUSD",
            timeframe="H4",
            family="currency ETF relative-flow pullback",
            description="EURUSD H4 pullback-continuation when lagged FXE/UUP relative flow confirms euro-vs-dollar pressure.",
            generator=lambda frame: signals_h4_eurusd_currency_etf_flow_pullback(frame, eur_flow),
            max_hold_bars=14,
            target_r=1.35,
        ),
        CandidateSpec(
            candidate_id="usdjpy_h4_currency_etf_flow_pullback_v0",
            symbol="USDJPY",
            timeframe="H4",
            family="currency ETF relative-flow pullback",
            description="USDJPY H4 pullback-continuation when lagged FXY/UUP relative flow, inverted for USDJPY, confirms yen-vs-dollar pressure.",
            generator=lambda frame: signals_h4_usdjpy_currency_etf_flow_pullback(frame, jpy_flow),
            max_hold_bars=14,
            target_r=1.35,
        ),
    ]


def candidate_specs_risk_regime(risk: pd.DataFrame) -> list[CandidateSpec]:
    return [
        CandidateSpec(
            candidate_id="eurusd_h4_vix_vxv_risk_regime_pullback_v0",
            symbol="EURUSD",
            timeframe="H4",
            family="VIX/VXV risk-regime FX pullback",
            description="EURUSD H4 pullback-continuation under lagged VIX/VXV risk-off dollar strength or risk-on dollar weakness.",
            generator=lambda frame: signals_h4_eurusd_vix_vxv_risk_pullback(frame, risk),
            max_hold_bars=14,
            target_r=1.35,
        ),
        CandidateSpec(
            candidate_id="usdjpy_h4_vix_vxv_risk_regime_pullback_v0",
            symbol="USDJPY",
            timeframe="H4",
            family="VIX/VXV risk-regime yen pullback",
            description="USDJPY H4 pullback-continuation under lagged VIX/VXV risk-off yen strength or risk-on yen weakness.",
            generator=lambda frame: signals_h4_usdjpy_vix_vxv_risk_pullback(frame, risk),
            max_hold_bars=14,
            target_r=1.35,
        ),
    ]


def candidate_specs_fx_cross(contexts: dict[str, pd.DataFrame]) -> list[CandidateSpec]:
    aud_ratio = contexts["AUDJPY_USDJPY"]
    eur_ratio = contexts["EURJPY_USDJPY"]
    return [
        CandidateSpec(
            candidate_id="usdjpy_h4_audjpy_cross_risk_rotation_pullback_v0",
            symbol="USDJPY",
            timeframe="H4",
            family="FX cross risk-rotation pullback",
            description="USDJPY H4 pullback-continuation when lagged AUDJPY/USDJPY cross ratio confirms risk-on or risk-off JPY rotation.",
            generator=lambda frame: signals_h4_usdjpy_audjpy_cross_rotation_pullback(frame, aud_ratio),
            max_hold_bars=14,
            target_r=1.35,
        ),
        CandidateSpec(
            candidate_id="eurusd_h4_eurjpy_cross_confirmation_pullback_v0",
            symbol="EURUSD",
            timeframe="H4",
            family="FX cross euro-confirmation pullback",
            description="EURUSD H4 pullback-continuation when lagged EURJPY/USDJPY cross ratio confirms euro-vs-dollar pressure.",
            generator=lambda frame: signals_h4_eurusd_eurjpy_cross_confirmation_pullback(frame, eur_ratio),
            max_hold_bars=14,
            target_r=1.35,
        ),
    ]


def signals_h4_eurusd_financial_liquidity_pullback(
    frame: pd.DataFrame, financial_context: pd.DataFrame
) -> list[dict[str, Any]]:
    f = merge_financial_liquidity(frame, financial_context, "EURUSD")
    signals: list[dict[str, Any]] = []
    px = point_size("EURUSD")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if not available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["anfci_delta_4w"],
            row["nfci_delta_4w"],
            row["walcl_13w_pct"],
            row["liquidity_easing_score"],
            row["liquidity_tightening_score"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        anfci_4w = float(row["anfci_delta_4w"])
        nfci_4w = float(row["nfci_delta_4w"])
        walcl_13w = float(row["walcl_13w_pct"])
        easing_score = float(row["liquidity_easing_score"])
        tightening_score = float(row["liquidity_tightening_score"])
        tightening = tightening_score >= 1.75 and anfci_4w >= 0.04 and nfci_4w >= 0.04 and walcl_13w <= 1.0
        easing = easing_score >= 1.75 and anfci_4w <= -0.04 and nfci_4w <= -0.04 and walcl_13w >= -1.0
        if tightening and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(
                    signal(
                        "eurusd_h4_financial_liquidity_dollar_squeeze_pullback_v0",
                        idx,
                        row,
                        "SHORT",
                        stop,
                        "H4_EURUSD_FIN_COND_DOLLAR_SQUEEZE_SHORT",
                    )
                )
        elif easing and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(
                    signal(
                        "eurusd_h4_financial_liquidity_dollar_squeeze_pullback_v0",
                        idx,
                        row,
                        "LONG",
                        stop,
                        "H4_EURUSD_FIN_COND_LIQUIDITY_RELIEF_LONG",
                    )
                )
    return signals


def signals_h4_usdjpy_financial_liquidity_pullback(
    frame: pd.DataFrame, financial_context: pd.DataFrame
) -> list[dict[str, Any]]:
    f = merge_financial_liquidity(frame, financial_context, "USDJPY")
    signals: list[dict[str, Any]] = []
    px = point_size("USDJPY")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        entry_row = f.iloc[idx + 1]
        if session_bucket(int(entry_row["hour_utc"])) not in {"asia", "london", "ny_morning"}:
            continue
        if not available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["anfci_delta_4w"],
            row["nfci_delta_4w"],
            row["walcl_13w_pct"],
            row["liquidity_easing_score"],
            row["liquidity_tightening_score"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        anfci_4w = float(row["anfci_delta_4w"])
        nfci_4w = float(row["nfci_delta_4w"])
        walcl_13w = float(row["walcl_13w_pct"])
        easing_score = float(row["liquidity_easing_score"])
        tightening_score = float(row["liquidity_tightening_score"])
        carry_relief = easing_score >= 1.50 and anfci_4w <= -0.04 and nfci_4w <= -0.04 and walcl_13w >= -1.0
        stress = tightening_score >= 1.50 and anfci_4w >= 0.04 and nfci_4w >= 0.04 and walcl_13w <= 1.0
        if carry_relief and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(
                    signal(
                        "usdjpy_h4_financial_liquidity_carry_pullback_v0",
                        idx,
                        row,
                        "LONG",
                        stop,
                        "H4_USDJPY_FIN_COND_CARRY_RELIEF_LONG",
                    )
                )
        elif stress and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(
                    signal(
                        "usdjpy_h4_financial_liquidity_carry_pullback_v0",
                        idx,
                        row,
                        "SHORT",
                        stop,
                        "H4_USDJPY_FIN_COND_STRESS_SHORT",
                    )
                )
    return signals


def signals_h4_eurusd_cny_dollar_pressure_pullback(frame: pd.DataFrame, cny: pd.DataFrame) -> list[dict[str, Any]]:
    f = merge_cny_pressure(frame, cny, "EURUSD")
    signals: list[dict[str, Any]] = []
    px = point_size("EURUSD")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if not available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["usd_cny_pct_20d"],
            row["dollar_pct_20d"],
            row["cny_dollar_pressure_score"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        usd_cny_20d = float(row["usd_cny_pct_20d"])
        dollar_20d = float(row["dollar_pct_20d"])
        pressure = float(row["cny_dollar_pressure_score"])
        usd_pressure = pressure >= 1.25 and usd_cny_20d >= 0.75 and dollar_20d >= 1.00
        usd_relief = pressure <= -1.25 and usd_cny_20d <= -0.75 and dollar_20d <= -1.00
        if usd_pressure and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.10 * atr * px)
                signals.append(signal("eurusd_h4_cny_dollar_pressure_pullback_v0", idx, row, "SHORT", stop, "H4_EURUSD_CNY_DOLLAR_PRESSURE_SHORT_PULLBACK"))
        elif usd_relief and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.10 * atr * px)
                signals.append(signal("eurusd_h4_cny_dollar_pressure_pullback_v0", idx, row, "LONG", stop, "H4_EURUSD_CNY_DOLLAR_RELIEF_LONG_PULLBACK"))
    return signals


def signals_h4_usdjpy_cny_shock_yen_reversion(frame: pd.DataFrame, cny: pd.DataFrame) -> list[dict[str, Any]]:
    f = merge_cny_pressure(frame, cny, "USDJPY")
    signals: list[dict[str, Any]] = []
    px = point_size("USDJPY")
    for idx in range(240, len(f) - 1):
        row = f.iloc[idx]
        if not available(
            row["atr14_points"],
            row["usd_cny_pct_5d"],
            row["usd_cny_pct_20d"],
            row["dollar_pct_20d"],
            row["cny_dollar_pressure_score"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        usd_cny_5d = float(row["usd_cny_pct_5d"])
        usd_cny_20d = float(row["usd_cny_pct_20d"])
        dollar_20d = float(row["dollar_pct_20d"])
        pressure = float(row["cny_dollar_pressure_score"])
        risk_off_cny_shock = pressure >= 1.25 and usd_cny_5d >= 0.45 and usd_cny_20d >= 1.00 and dollar_20d >= 1.00
        risk_on_cny_unwind = pressure <= -1.25 and usd_cny_5d <= -0.45 and usd_cny_20d <= -1.00 and dollar_20d <= -1.00
        prior = f.iloc[idx - 24 : idx]
        prior_high = float(prior["high"].max())
        prior_low = float(prior["low"].min())
        close = float(row["close"])
        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        buffer = 0.08 * atr * px
        if risk_off_cny_shock and high > prior_high + buffer and close < prior_high and close < open_price:
            stop = high + 0.45 * atr * px
            signals.append(signal("usdjpy_h4_cny_shock_yen_reversion_v0", idx, row, "SHORT", stop, "H4_USDJPY_CNY_RISK_OFF_HIGH_REJECTION"))
        elif risk_on_cny_unwind and low < prior_low - buffer and close > prior_low and close > open_price:
            stop = low - 0.45 * atr * px
            signals.append(signal("usdjpy_h4_cny_shock_yen_reversion_v0", idx, row, "LONG", stop, "H4_USDJPY_CNY_RISK_ON_LOW_REJECTION"))
    return signals


def signals_h1_eurusd_ny_fix_overextension_reversion(frame: pd.DataFrame) -> list[dict[str, Any]]:
    f = with_features(frame, "EURUSD")
    signals: list[dict[str, Any]] = []
    px = point_size("EURUSD")
    for idx in range(80, len(f) - 1):
        row = f.iloc[idx]
        timestamp = pd.Timestamp(row["bar_start_utc"])
        if timestamp.weekday() >= 4 or int(row["hour_utc"]) not in {13, 14, 15}:
            continue
        if not available(row["atr14_points"], row["range_points"], row["body_points"]):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        day_rows = f[(f["date_utc"] == row["date_utc"]) & (f.index <= idx)]
        if len(day_rows) < 8:
            continue
        day_open = float(day_rows.iloc[0]["open"])
        day_high = float(day_rows["high"].max())
        day_low = float(day_rows["low"].min())
        close = float(row["close"])
        open_price = float(row["open"])
        daily_move_points = (close - day_open) / px
        candle_range_points = float(row["range_points"])
        if candle_range_points <= 0:
            continue
        close_location = (close - float(row["low"])) / (float(row["high"]) - float(row["low"])) if float(row["high"]) > float(row["low"]) else 0.5
        if daily_move_points >= 0.75 * atr and close < open_price and close_location <= 0.45:
            stop = max(day_high, close + 0.80 * atr * px)
            signals.append(signal("eurusd_h1_ny_fix_overextension_reversion_v0", idx, row, "SHORT", stop, "H1_EURUSD_NY_FIX_UP_EXT_REVERSION"))
        elif daily_move_points <= -0.75 * atr and close > open_price and close_location >= 0.55:
            stop = min(day_low, close - 0.80 * atr * px)
            signals.append(signal("eurusd_h1_ny_fix_overextension_reversion_v0", idx, row, "LONG", stop, "H1_EURUSD_NY_FIX_DOWN_EXT_REVERSION"))
    return signals


def signals_h4_usdjpy_month_turn_carry_pullback(frame: pd.DataFrame) -> list[dict[str, Any]]:
    f = with_features(frame, "USDJPY")
    signals: list[dict[str, Any]] = []
    px = point_size("USDJPY")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        timestamp = pd.Timestamp(row["bar_start_utc"])
        month_turn = timestamp.day <= 5 or timestamp.day >= 25
        if not month_turn or session_bucket(int(row["hour_utc"])) not in {"asia", "ny_morning"}:
            continue
        if not available(row["atr14_points"], row["ema20"], row["ema50"], row["ema100"], row["ema200"]):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        ema200 = float(row["ema200"])
        long_trend = ema20 > ema50 > ema100 > ema200
        short_trend = ema20 < ema50 < ema100 < ema200
        if long_trend:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(signal("usdjpy_h4_month_turn_carry_pullback_v0", idx, row, "LONG", stop, "H4_USDJPY_MONTH_TURN_CARRY_LONG_PULLBACK"))
        elif short_trend:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(signal("usdjpy_h4_month_turn_carry_pullback_v0", idx, row, "SHORT", stop, "H4_USDJPY_MONTH_TURN_CARRY_SHORT_PULLBACK"))
    return signals


def signals_h4_eurusd_weekly_liquidity_reversion(frame: pd.DataFrame) -> list[dict[str, Any]]:
    f = with_weekly_structure_features(frame, "EURUSD")
    signals: list[dict[str, Any]] = []
    px = point_size("EURUSD")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        timestamp = pd.Timestamp(row["bar_start_utc"])
        if timestamp.weekday() not in {0, 1, 2}:
            continue
        if session_bucket(int(row["hour_utc"])) not in {"london", "ny_morning"}:
            continue
        if not available(row["atr14_points"], row["prev_week_high"], row["prev_week_low"], row["ema50"], row["ema200"]):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        prior_week_range_points = (float(row["prev_week_high"]) - float(row["prev_week_low"])) / px
        if prior_week_range_points < 1.20 * atr or prior_week_range_points > 5.50 * atr:
            continue
        ema_gap_points = abs(float(row["ema50"]) - float(row["ema200"])) / px
        if ema_gap_points > 1.75 * atr:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        buffer = 0.08 * atr * px
        if high > float(row["prev_week_high"]) + buffer and close < float(row["prev_week_high"]) and close < open_price:
            stop = high + 0.40 * atr * px
            signals.append(signal("eurusd_h4_weekly_liquidity_reversion_v0", idx, row, "SHORT", stop, "H4_EURUSD_PREV_WEEK_HIGH_FADE"))
        elif low < float(row["prev_week_low"]) - buffer and close > float(row["prev_week_low"]) and close > open_price:
            stop = low - 0.40 * atr * px
            signals.append(signal("eurusd_h4_weekly_liquidity_reversion_v0", idx, row, "LONG", stop, "H4_EURUSD_PREV_WEEK_LOW_FADE"))
    return signals


def signals_h4_usdjpy_weekly_carry_continuation(frame: pd.DataFrame) -> list[dict[str, Any]]:
    f = with_weekly_structure_features(frame, "USDJPY")
    signals: list[dict[str, Any]] = []
    px = point_size("USDJPY")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        entry_row = f.iloc[idx + 1]
        timestamp = pd.Timestamp(row["bar_start_utc"])
        if timestamp.weekday() not in {1, 2, 3}:
            continue
        if session_bucket(int(entry_row["hour_utc"])) not in {"asia", "ny_morning"}:
            continue
        if not available(
            row["atr14_points"],
            row["prev_week_range"],
            row["prev_week_direction"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["ema200"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        prior_week_range_points = float(row["prev_week_range"]) / px
        prior_week_direction_points = float(row["prev_week_direction"]) / px
        if prior_week_range_points < 1.50 * atr:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        ema200 = float(row["ema200"])
        if prior_week_direction_points > 0.35 * prior_week_range_points and ema20 > ema50 > ema100 > ema200:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(signal("usdjpy_h4_weekly_carry_continuation_v0", idx, row, "LONG", stop, "H4_USDJPY_PREV_WEEK_UP_PULLBACK"))
        elif prior_week_direction_points < -0.35 * prior_week_range_points and ema20 < ema50 < ema100 < ema200:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(signal("usdjpy_h4_weekly_carry_continuation_v0", idx, row, "SHORT", stop, "H4_USDJPY_PREV_WEEK_DOWN_PULLBACK"))
    return signals


def signals_h4_eurusd_weekly_open_reversion(frame: pd.DataFrame) -> list[dict[str, Any]]:
    f = with_weekly_structure_features(frame, "EURUSD")
    signals: list[dict[str, Any]] = []
    px = point_size("EURUSD")
    for idx in range(180, len(f) - 1):
        row = f.iloc[idx]
        timestamp = pd.Timestamp(row["bar_start_utc"])
        if timestamp.weekday() not in {2, 3, 4}:
            continue
        if session_bucket(int(row["hour_utc"])) not in {"london", "ny_morning"}:
            continue
        if not available(row["atr14_points"], row["week_open"], row["ema50"], row["ema200"]):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        ema_gap_points = abs(float(row["ema50"]) - float(row["ema200"])) / px
        if ema_gap_points > 1.50 * atr:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        weekly_open = float(row["week_open"])
        distance_from_week_open_points = (close - weekly_open) / px
        if distance_from_week_open_points >= 1.20 * atr and close < open_price:
            recent_high = float(f.iloc[idx - 3 : idx + 1]["high"].max())
            stop = max(recent_high, close + 0.85 * atr * px)
            signals.append(signal("eurusd_h4_weekly_open_reversion_v0", idx, row, "SHORT", stop, "H4_EURUSD_WEEK_OPEN_UP_EXT_FADE"))
        elif distance_from_week_open_points <= -1.20 * atr and close > open_price:
            recent_low = float(f.iloc[idx - 3 : idx + 1]["low"].min())
            stop = min(recent_low, close - 0.85 * atr * px)
            signals.append(signal("eurusd_h4_weekly_open_reversion_v0", idx, row, "LONG", stop, "H4_EURUSD_WEEK_OPEN_DOWN_EXT_FADE"))
    return signals


def signals_h4_eurusd_global_risk_pullback(frame: pd.DataFrame, global_risk: pd.DataFrame) -> list[dict[str, Any]]:
    f = merge_global_risk(frame, global_risk, "EURUSD")
    signals: list[dict[str, Any]] = []
    px = point_size("EURUSD")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if not available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["eem_spy_5d_pct"],
            row["eem_spy_20d_pct"],
            row["hyg_ief_20d_pct"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        eem_5d = float(row["eem_spy_5d_pct"])
        eem_20d = float(row["eem_spy_20d_pct"])
        hyg_20d = float(row["hyg_ief_20d_pct"])
        risk_on = eem_5d >= 0.75 and eem_20d >= 2.50 and hyg_20d >= 1.25
        risk_off = eem_5d <= -1.00 and eem_20d <= -3.00 and hyg_20d <= -1.25
        if risk_on and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(signal("eurusd_h4_global_risk_dollar_beta_pullback_v0", idx, row, "LONG", stop, "H4_EURUSD_GLOBAL_RISK_ON_LONG_PULLBACK"))
        elif risk_off and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(signal("eurusd_h4_global_risk_dollar_beta_pullback_v0", idx, row, "SHORT", stop, "H4_EURUSD_GLOBAL_RISK_OFF_SHORT_PULLBACK"))
    return signals


def signals_h4_usdjpy_global_risk_pullback(frame: pd.DataFrame, global_risk: pd.DataFrame) -> list[dict[str, Any]]:
    f = merge_global_risk(frame, global_risk, "USDJPY")
    signals: list[dict[str, Any]] = []
    px = point_size("USDJPY")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if not available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["eem_spy_5d_pct"],
            row["eem_spy_20d_pct"],
            row["hyg_ief_20d_pct"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        eem_5d = float(row["eem_spy_5d_pct"])
        eem_20d = float(row["eem_spy_20d_pct"])
        hyg_20d = float(row["hyg_ief_20d_pct"])
        risk_on = eem_5d >= 0.75 and eem_20d >= 2.50 and hyg_20d >= 1.25
        risk_off = eem_5d <= -1.00 and eem_20d <= -3.00 and hyg_20d <= -1.25
        if risk_on and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(signal("usdjpy_h4_global_risk_credit_pullback_v0", idx, row, "LONG", stop, "H4_USDJPY_GLOBAL_RISK_ON_LONG_PULLBACK"))
        elif risk_off and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(signal("usdjpy_h4_global_risk_credit_pullback_v0", idx, row, "SHORT", stop, "H4_USDJPY_GLOBAL_RISK_OFF_SHORT_PULLBACK"))
    return signals


def signals_h4_eurusd_commodity_dollar_pullback(frame: pd.DataFrame, commodity_context: pd.DataFrame) -> list[dict[str, Any]]:
    f = merge_commodity_dollar(frame, commodity_context, "EURUSD")
    signals: list[dict[str, Any]] = []
    px = point_size("EURUSD")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if not available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["dbc_uup_5d_pct"],
            row["dbc_uup_20d_pct"],
            row["dbb_uup_20d_pct"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        dbc_5d = float(row["dbc_uup_5d_pct"])
        dbc_20d = float(row["dbc_uup_20d_pct"])
        dbb_20d = float(row["dbb_uup_20d_pct"])
        commodity_reflation = dbc_5d >= 1.00 and dbc_20d >= 5.00 and dbb_20d >= 5.00
        commodity_deflation = dbc_5d <= -1.00 and dbc_20d <= -5.00 and dbb_20d <= -5.00
        if commodity_reflation and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(signal("eurusd_h4_commodity_dollar_reflation_pullback_v0", idx, row, "LONG", stop, "H4_EURUSD_COMMODITY_REFLATION_LONG_PULLBACK"))
        elif commodity_deflation and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(signal("eurusd_h4_commodity_dollar_reflation_pullback_v0", idx, row, "SHORT", stop, "H4_EURUSD_COMMODITY_DEFLATION_SHORT_PULLBACK"))
    return signals


def signals_h4_usdjpy_commodity_dollar_pullback(frame: pd.DataFrame, commodity_context: pd.DataFrame) -> list[dict[str, Any]]:
    f = merge_commodity_dollar(frame, commodity_context, "USDJPY")
    signals: list[dict[str, Any]] = []
    px = point_size("USDJPY")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if not available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["dbc_uup_5d_pct"],
            row["dbc_uup_20d_pct"],
            row["dbb_uup_20d_pct"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        dbc_5d = float(row["dbc_uup_5d_pct"])
        dbc_20d = float(row["dbc_uup_20d_pct"])
        dbb_20d = float(row["dbb_uup_20d_pct"])
        commodity_reflation = dbc_5d >= 1.00 and dbc_20d >= 5.00 and dbb_20d >= 5.00
        commodity_deflation = dbc_5d <= -1.00 and dbc_20d <= -5.00 and dbb_20d <= -5.00
        if commodity_reflation and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(signal("usdjpy_h4_commodity_dollar_reflation_pullback_v0", idx, row, "LONG", stop, "H4_USDJPY_COMMODITY_REFLATION_LONG_PULLBACK"))
        elif commodity_deflation and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(signal("usdjpy_h4_commodity_dollar_reflation_pullback_v0", idx, row, "SHORT", stop, "H4_USDJPY_COMMODITY_DEFLATION_SHORT_PULLBACK"))
    return signals


def signals_h4_eurusd_real_asset_reflation_pullback(
    frame: pd.DataFrame,
    real_asset_context: pd.DataFrame,
) -> list[dict[str, Any]]:
    f = merge_real_asset_rotation(frame, real_asset_context, "EURUSD")
    signals: list[dict[str, Any]] = []
    px = point_size("EURUSD")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if not available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["uso_uup_5d_pct"],
            row["uso_uup_20d_pct"],
            row["hg_gc_20d_pct"],
            row["slv_gld_20d_pct"],
            row["real_asset_reflation_score"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        uso_5d = float(row["uso_uup_5d_pct"])
        uso_20d = float(row["uso_uup_20d_pct"])
        hg_20d = float(row["hg_gc_20d_pct"])
        slv_20d = float(row["slv_gld_20d_pct"])
        score = float(row["real_asset_reflation_score"])
        reflation = score >= 1.75 and uso_5d >= 2.00 and uso_20d >= 6.00 and hg_20d >= 2.50 and slv_20d >= 1.50
        deflation = score <= -1.75 and uso_5d <= -2.00 and uso_20d <= -6.00 and hg_20d <= -2.50 and slv_20d <= -1.50
        if reflation and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(
                    signal(
                        "eurusd_h4_real_asset_reflation_pullback_v0",
                        idx,
                        row,
                        "LONG",
                        stop,
                        "H4_EURUSD_REAL_ASSET_REFLATION_LONG",
                    )
                )
        elif deflation and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(
                    signal(
                        "eurusd_h4_real_asset_reflation_pullback_v0",
                        idx,
                        row,
                        "SHORT",
                        stop,
                        "H4_EURUSD_REAL_ASSET_DEFLATION_SHORT",
                    )
                )
    return signals


def signals_h4_usdjpy_real_asset_carry_pullback(
    frame: pd.DataFrame,
    real_asset_context: pd.DataFrame,
) -> list[dict[str, Any]]:
    f = merge_real_asset_rotation(frame, real_asset_context, "USDJPY")
    signals: list[dict[str, Any]] = []
    px = point_size("USDJPY")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        entry_row = f.iloc[idx + 1]
        if session_bucket(int(entry_row["hour_utc"])) not in {"asia", "london", "ny_morning"}:
            continue
        if not available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["uso_uup_5d_pct"],
            row["uso_uup_20d_pct"],
            row["hg_gc_20d_pct"],
            row["slv_gld_20d_pct"],
            row["real_asset_reflation_score"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        uso_5d = float(row["uso_uup_5d_pct"])
        uso_20d = float(row["uso_uup_20d_pct"])
        hg_20d = float(row["hg_gc_20d_pct"])
        slv_20d = float(row["slv_gld_20d_pct"])
        score = float(row["real_asset_reflation_score"])
        reflation_carry = score >= 1.50 and uso_5d >= 1.50 and uso_20d >= 5.00 and hg_20d >= 2.00 and slv_20d >= 1.00
        safe_haven_pressure = score <= -1.50 and uso_5d <= -1.50 and uso_20d <= -5.00 and hg_20d <= -2.00 and slv_20d <= -1.00
        if reflation_carry and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(
                    signal(
                        "usdjpy_h4_real_asset_carry_pullback_v0",
                        idx,
                        row,
                        "LONG",
                        stop,
                        "H4_USDJPY_REAL_ASSET_REFLATION_CARRY_LONG",
                    )
                )
        elif safe_haven_pressure and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(
                    signal(
                        "usdjpy_h4_real_asset_carry_pullback_v0",
                        idx,
                        row,
                        "SHORT",
                        stop,
                        "H4_USDJPY_REAL_ASSET_SAFE_HAVEN_SHORT",
                    )
                )
    return signals


def signals_h4_usdjpy_haven_liquidity_pullback(
    frame: pd.DataFrame,
    haven_context: pd.DataFrame,
) -> list[dict[str, Any]]:
    f = merge_haven_liquidity(frame, haven_context, "USDJPY")
    signals: list[dict[str, Any]] = []
    px = point_size("USDJPY")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        entry_row = f.iloc[idx + 1]
        if session_bucket(int(entry_row["hour_utc"])) not in {"asia", "london", "ny_morning"}:
            continue
        if not available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["gld_5d_pct"],
            row["gld_20d_pct"],
            row["gdx_gld_20d_pct"],
            row["spy_tlt_20d_pct"],
            row["xlu_xlk_20d_pct"],
            row["haven_liquidity_score"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        gld_5d = float(row["gld_5d_pct"])
        gld_20d = float(row["gld_20d_pct"])
        gdx_gld_20d = float(row["gdx_gld_20d_pct"])
        spy_tlt_20d = float(row["spy_tlt_20d_pct"])
        xlu_xlk_20d = float(row["xlu_xlk_20d_pct"])
        score = float(row["haven_liquidity_score"])
        haven_pressure = (
            score >= 0.85
            and gld_5d >= 0.75
            and gld_20d >= 2.50
            and gdx_gld_20d >= -5.00
            and spy_tlt_20d <= -1.50
            and xlu_xlk_20d >= 0.50
        )
        liquidity_relief = (
            score <= -0.85
            and gld_5d <= -0.50
            and gld_20d <= -1.50
            and gdx_gld_20d <= 5.00
            and spy_tlt_20d >= 1.50
            and xlu_xlk_20d <= -0.50
        )
        if haven_pressure and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(
                    signal(
                        "usdjpy_h4_haven_liquidity_yen_pullback_v0",
                        idx,
                        row,
                        "SHORT",
                        stop,
                        "H4_USDJPY_HAVEN_LIQUIDITY_YEN_SHORT",
                    )
                )
        elif liquidity_relief and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(
                    signal(
                        "usdjpy_h4_haven_liquidity_yen_pullback_v0",
                        idx,
                        row,
                        "LONG",
                        stop,
                        "H4_USDJPY_HAVEN_LIQUIDITY_RELIEF_LONG",
                    )
                )
    return signals


def signals_h4_eurusd_haven_liquidity_pullback(
    frame: pd.DataFrame,
    haven_context: pd.DataFrame,
) -> list[dict[str, Any]]:
    f = merge_haven_liquidity(frame, haven_context, "EURUSD")
    signals: list[dict[str, Any]] = []
    px = point_size("EURUSD")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        entry_row = f.iloc[idx + 1]
        if session_bucket(int(entry_row["hour_utc"])) in {"ny_late", "rollover"}:
            continue
        if not available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["gld_5d_pct"],
            row["gld_20d_pct"],
            row["gdx_gld_20d_pct"],
            row["spy_tlt_20d_pct"],
            row["xlu_xlk_20d_pct"],
            row["haven_liquidity_score"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        gld_5d = float(row["gld_5d_pct"])
        gld_20d = float(row["gld_20d_pct"])
        gdx_gld_20d = float(row["gdx_gld_20d_pct"])
        spy_tlt_20d = float(row["spy_tlt_20d_pct"])
        xlu_xlk_20d = float(row["xlu_xlk_20d_pct"])
        score = float(row["haven_liquidity_score"])
        dollar_squeeze = (
            score >= 0.85
            and gld_5d >= 0.75
            and gld_20d >= 2.50
            and gdx_gld_20d >= -5.00
            and spy_tlt_20d <= -1.50
            and xlu_xlk_20d >= 0.50
        )
        risk_relief = (
            score <= -0.85
            and gld_20d <= 0.50
            and gdx_gld_20d <= 5.00
            and spy_tlt_20d >= 1.50
            and xlu_xlk_20d <= -0.50
        )
        if dollar_squeeze and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(
                    signal(
                        "eurusd_h4_haven_liquidity_dollar_pullback_v0",
                        idx,
                        row,
                        "SHORT",
                        stop,
                        "H4_EURUSD_HAVEN_LIQUIDITY_DOLLAR_SHORT",
                    )
                )
        elif risk_relief and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(
                    signal(
                        "eurusd_h4_haven_liquidity_dollar_pullback_v0",
                        idx,
                        row,
                        "LONG",
                        stop,
                        "H4_EURUSD_HAVEN_LIQUIDITY_RELIEF_LONG",
                    )
                )
    return signals


def signals_h4_usdjpy_treasury_curve_pullback(
    frame: pd.DataFrame,
    curve_context: pd.DataFrame,
) -> list[dict[str, Any]]:
    f = merge_treasury_curve(frame, curve_context, "USDJPY")
    signals: list[dict[str, Any]] = []
    px = point_size("USDJPY")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        entry_row = f.iloc[idx + 1]
        if session_bucket(int(entry_row["hour_utc"])) not in {"asia", "london", "ny_morning"}:
            continue
        if not available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["dgs2_delta_5d"],
            row["dgs2_delta_20d"],
            row["dgs10_delta_20d"],
            row["curve_delta_20d"],
            row["front_end_pressure_score"],
            row["bull_steepening_score"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        dgs2_5d = float(row["dgs2_delta_5d"])
        dgs2_20d = float(row["dgs2_delta_20d"])
        dgs10_20d = float(row["dgs10_delta_20d"])
        curve_20d = float(row["curve_delta_20d"])
        front_end_score = float(row["front_end_pressure_score"])
        bull_steepening_score = float(row["bull_steepening_score"])
        front_end_pressure = (
            dgs2_5d >= 0.08
            and dgs2_20d >= 0.25
            and dgs10_20d >= 0.05
            and curve_20d <= -0.15
            and front_end_score >= 1.20
        )
        bull_steepening = (
            dgs2_20d <= -0.25
            and dgs10_20d >= dgs2_20d
            and curve_20d >= 0.15
            and bull_steepening_score >= 1.20
        )
        if front_end_pressure and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(
                    signal(
                        "usdjpy_h4_treasury_curve_frontend_pullback_v0",
                        idx,
                        row,
                        "LONG",
                        stop,
                        "H4_USDJPY_TREASURY_FRONTEND_LONG",
                    )
                )
        elif bull_steepening and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(
                    signal(
                        "usdjpy_h4_treasury_curve_frontend_pullback_v0",
                        idx,
                        row,
                        "SHORT",
                        stop,
                        "H4_USDJPY_TREASURY_BULL_STEEPENING_SHORT",
                    )
                )
    return signals


def signals_h4_eurusd_treasury_curve_pullback(
    frame: pd.DataFrame,
    curve_context: pd.DataFrame,
) -> list[dict[str, Any]]:
    f = merge_treasury_curve(frame, curve_context, "EURUSD")
    signals: list[dict[str, Any]] = []
    px = point_size("EURUSD")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        entry_row = f.iloc[idx + 1]
        if session_bucket(int(entry_row["hour_utc"])) in {"ny_late", "rollover"}:
            continue
        if not available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["dgs2_delta_5d"],
            row["dgs2_delta_20d"],
            row["dgs10_delta_20d"],
            row["curve_delta_20d"],
            row["front_end_pressure_score"],
            row["bull_steepening_score"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        dgs2_5d = float(row["dgs2_delta_5d"])
        dgs2_20d = float(row["dgs2_delta_20d"])
        dgs10_20d = float(row["dgs10_delta_20d"])
        curve_20d = float(row["curve_delta_20d"])
        front_end_score = float(row["front_end_pressure_score"])
        bull_steepening_score = float(row["bull_steepening_score"])
        dollar_pressure = (
            dgs2_5d >= 0.08
            and dgs2_20d >= 0.25
            and dgs10_20d >= 0.05
            and curve_20d <= -0.15
            and front_end_score >= 1.20
        )
        dollar_relief = (
            dgs2_20d <= -0.25
            and dgs10_20d >= dgs2_20d
            and curve_20d >= 0.15
            and bull_steepening_score >= 1.20
        )
        if dollar_pressure and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(
                    signal(
                        "eurusd_h4_treasury_curve_dollar_pressure_pullback_v0",
                        idx,
                        row,
                        "SHORT",
                        stop,
                        "H4_EURUSD_TREASURY_FRONTEND_DOLLAR_SHORT",
                    )
                )
        elif dollar_relief and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(
                    signal(
                        "eurusd_h4_treasury_curve_dollar_pressure_pullback_v0",
                        idx,
                        row,
                        "LONG",
                        stop,
                        "H4_EURUSD_TREASURY_BULL_STEEPENING_LONG",
                    )
                )
    return signals


def signals_h4_eurusd_cot_positioning_reversal(frame: pd.DataFrame, cot_context: pd.DataFrame) -> list[dict[str, Any]]:
    f = merge_cot_positioning(frame, cot_context, "EURUSD")
    signals: list[dict[str, Any]] = []
    px = point_size("EURUSD")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if not available(
            row["atr14_points"],
            row["spot_lev_z156"],
            row["spot_lev_delta_4w"],
            row["spot_lev_delta_13w"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        z = float(row["spot_lev_z156"])
        delta_4w = float(row["spot_lev_delta_4w"])
        delta_13w = float(row["spot_lev_delta_13w"])
        prior = f.iloc[idx - 18 : idx]
        prior_high = float(prior["high"].max())
        prior_low = float(prior["low"].min())
        close = float(row["close"])
        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        buffer = 0.08 * atr * px
        oversold_unwind = z <= -0.85 and delta_4w >= 1.25 and delta_13w >= -1.00
        crowded_long_unwind = z >= 0.85 and delta_4w <= -1.25 and delta_13w <= 1.00
        if oversold_unwind and low < prior_low - buffer and close > prior_low and close > open_price:
            stop = low - 0.45 * atr * px
            signals.append(
                signal(
                    "eurusd_h4_cot_lev_positioning_reversal_v0",
                    idx,
                    row,
                    "LONG",
                    stop,
                    "H4_EURUSD_COT_LEV_SHORT_UNWIND_LOW_RECLAIM",
                )
            )
        elif crowded_long_unwind and high > prior_high + buffer and close < prior_high and close < open_price:
            stop = high + 0.45 * atr * px
            signals.append(
                signal(
                    "eurusd_h4_cot_lev_positioning_reversal_v0",
                    idx,
                    row,
                    "SHORT",
                    stop,
                    "H4_EURUSD_COT_LEV_LONG_UNWIND_HIGH_REJECT",
                )
            )
    return signals


def signals_h4_usdjpy_cot_positioning_reversal(frame: pd.DataFrame, cot_context: pd.DataFrame) -> list[dict[str, Any]]:
    f = merge_cot_positioning(frame, cot_context, "USDJPY")
    signals: list[dict[str, Any]] = []
    px = point_size("USDJPY")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        entry_row = f.iloc[idx + 1]
        if session_bucket(int(entry_row["hour_utc"])) not in {"asia", "london", "ny_morning"}:
            continue
        if not available(
            row["atr14_points"],
            row["spot_lev_z156"],
            row["spot_lev_delta_4w"],
            row["spot_lev_delta_13w"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        z = float(row["spot_lev_z156"])
        delta_4w = float(row["spot_lev_delta_4w"])
        delta_13w = float(row["spot_lev_delta_13w"])
        prior = f.iloc[idx - 18 : idx]
        prior_high = float(prior["high"].max())
        prior_low = float(prior["low"].min())
        close = float(row["close"])
        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        buffer = 0.08 * atr * px
        usd_oversold_unwind = z <= -0.85 and delta_4w >= 1.25 and delta_13w >= -1.00
        usd_crowded_unwind = z >= 0.85 and delta_4w <= -1.25 and delta_13w <= 1.00
        if usd_oversold_unwind and low < prior_low - buffer and close > prior_low and close > open_price:
            stop = low - 0.45 * atr * px
            signals.append(
                signal(
                    "usdjpy_h4_cot_yen_positioning_reversal_v0",
                    idx,
                    row,
                    "LONG",
                    stop,
                    "H4_USDJPY_COT_YEN_LONG_UNWIND_LOW_RECLAIM",
                )
            )
        elif usd_crowded_unwind and high > prior_high + buffer and close < prior_high and close < open_price:
            stop = high + 0.45 * atr * px
            signals.append(
                signal(
                    "usdjpy_h4_cot_yen_positioning_reversal_v0",
                    idx,
                    row,
                    "SHORT",
                    stop,
                    "H4_USDJPY_COT_YEN_SHORT_UNWIND_HIGH_REJECT",
                )
            )
    return signals


def signals_h4_eurusd_rates_dollar_pullback(frame: pd.DataFrame, rates_context: pd.DataFrame) -> list[dict[str, Any]]:
    f = merge_rates_dollar(frame, rates_context, "EURUSD")
    signals: list[dict[str, Any]] = []
    px = point_size("EURUSD")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if not available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["tlt_uup_5d_pct"],
            row["tlt_uup_20d_pct"],
            row["tlt_shy_20d_pct"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        tlt_uup_5d = float(row["tlt_uup_5d_pct"])
        tlt_uup_20d = float(row["tlt_uup_20d_pct"])
        tlt_shy_20d = float(row["tlt_shy_20d_pct"])
        duration_relief = tlt_uup_5d >= 0.80 and tlt_uup_20d >= 2.00 and tlt_shy_20d >= 0.60
        yield_dollar_pressure = tlt_uup_5d <= -0.80 and tlt_uup_20d <= -2.00 and tlt_shy_20d <= -0.60
        if duration_relief and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(signal("eurusd_h4_rates_dollar_duration_pullback_v0", idx, row, "LONG", stop, "H4_EURUSD_RATES_DURATION_RELIEF_LONG"))
        elif yield_dollar_pressure and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(signal("eurusd_h4_rates_dollar_duration_pullback_v0", idx, row, "SHORT", stop, "H4_EURUSD_RATES_YIELD_DOLLAR_SHORT"))
    return signals


def signals_h4_usdjpy_rates_dollar_pullback(frame: pd.DataFrame, rates_context: pd.DataFrame) -> list[dict[str, Any]]:
    f = merge_rates_dollar(frame, rates_context, "USDJPY")
    signals: list[dict[str, Any]] = []
    px = point_size("USDJPY")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if not available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["tlt_uup_5d_pct"],
            row["tlt_uup_20d_pct"],
            row["tlt_shy_20d_pct"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        tlt_uup_5d = float(row["tlt_uup_5d_pct"])
        tlt_uup_20d = float(row["tlt_uup_20d_pct"])
        tlt_shy_20d = float(row["tlt_shy_20d_pct"])
        yield_dollar_pressure = tlt_uup_5d <= -0.80 and tlt_uup_20d <= -2.00 and tlt_shy_20d <= -0.60
        duration_bid = tlt_uup_5d >= 0.80 and tlt_uup_20d >= 2.00 and tlt_shy_20d >= 0.60
        if yield_dollar_pressure and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(signal("usdjpy_h4_rates_dollar_yield_pullback_v0", idx, row, "LONG", stop, "H4_USDJPY_RATES_YIELD_DOLLAR_LONG"))
        elif duration_bid and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(signal("usdjpy_h4_rates_dollar_yield_pullback_v0", idx, row, "SHORT", stop, "H4_USDJPY_RATES_DURATION_BID_SHORT"))
    return signals


def signals_h4_eurusd_rates_dollar_yield_pressure_short_session_v1(frame: pd.DataFrame, rates_context: pd.DataFrame) -> list[dict[str, Any]]:
    f = merge_rates_dollar(frame, rates_context, "EURUSD")
    signals: list[dict[str, Any]] = []
    px = point_size("EURUSD")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        entry_row = f.iloc[idx + 1]
        if session_bucket(int(entry_row["hour_utc"])) in {"ny_late", "rollover"}:
            continue
        if not available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["tlt_uup_5d_pct"],
            row["tlt_uup_20d_pct"],
            row["tlt_shy_20d_pct"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        tlt_uup_5d = float(row["tlt_uup_5d_pct"])
        tlt_uup_20d = float(row["tlt_uup_20d_pct"])
        tlt_shy_20d = float(row["tlt_shy_20d_pct"])
        yield_dollar_pressure = tlt_uup_5d <= -0.80 and tlt_uup_20d <= -2.00 and tlt_shy_20d <= -0.60
        if not (yield_dollar_pressure and ema20 < ema50 < ema100):
            continue
        touched = float(row["high"]) >= ema20 - 0.25 * atr * px
        confirmed = close < float(row["open"]) and close < ema20
        if touched and confirmed:
            recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
            stop = max(recent_high, close + 1.05 * atr * px)
            signals.append(
                signal(
                    "eurusd_h4_rates_dollar_yield_pressure_short_session_v1",
                    idx,
                    row,
                    "SHORT",
                    stop,
                    "H4_EURUSD_RATES_YIELD_PRESSURE_SHORT_SESSION_V1",
                )
            )
    return signals


def signals_h4_eurusd_exus_equity_leadership_pullback(frame: pd.DataFrame, equity_context: pd.DataFrame) -> list[dict[str, Any]]:
    f = merge_equity_leadership(frame, equity_context, "EURUSD")
    signals: list[dict[str, Any]] = []
    px = point_size("EURUSD")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if not available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["acwx_spy_5d_pct"],
            row["acwx_spy_20d_pct"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        acwx_5d = float(row["acwx_spy_5d_pct"])
        acwx_20d = float(row["acwx_spy_20d_pct"])
        ex_us_leadership = acwx_5d >= 0.35 and acwx_20d >= 1.00
        us_leadership = acwx_5d <= -0.35 and acwx_20d <= -1.00
        if ex_us_leadership and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(
                    signal(
                        "eurusd_h4_exus_equity_leadership_pullback_v0",
                        idx,
                        row,
                        "LONG",
                        stop,
                        "H4_EURUSD_EXUS_EQUITY_LEADERSHIP_LONG",
                    )
                )
        elif us_leadership and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(
                    signal(
                        "eurusd_h4_exus_equity_leadership_pullback_v0",
                        idx,
                        row,
                        "SHORT",
                        stop,
                        "H4_EURUSD_US_EQUITY_LEADERSHIP_SHORT",
                    )
                )
    return signals


def signals_h4_usdjpy_us_cyclical_leadership_pullback(frame: pd.DataFrame, equity_context: pd.DataFrame) -> list[dict[str, Any]]:
    f = merge_equity_leadership(frame, equity_context, "USDJPY")
    signals: list[dict[str, Any]] = []
    px = point_size("USDJPY")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if not available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["iwm_spy_5d_pct"],
            row["iwm_spy_20d_pct"],
            row["xlf_xlu_20d_pct"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        iwm_5d = float(row["iwm_spy_5d_pct"])
        iwm_20d = float(row["iwm_spy_20d_pct"])
        xlf_xlu_20d = float(row["xlf_xlu_20d_pct"])
        cyclical_leadership = iwm_5d >= 0.35 and iwm_20d >= 1.00 and xlf_xlu_20d >= 1.25
        defensive_leadership = iwm_5d <= -0.35 and iwm_20d <= -1.00 and xlf_xlu_20d <= -1.25
        if cyclical_leadership and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(
                    signal(
                        "usdjpy_h4_us_cyclical_leadership_pullback_v0",
                        idx,
                        row,
                        "LONG",
                        stop,
                        "H4_USDJPY_US_CYCLICAL_LEADERSHIP_LONG",
                    )
                )
        elif defensive_leadership and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(
                    signal(
                        "usdjpy_h4_us_cyclical_leadership_pullback_v0",
                        idx,
                        row,
                        "SHORT",
                        stop,
                        "H4_USDJPY_US_DEFENSIVE_LEADERSHIP_SHORT",
                    )
                )
    return signals


def signals_h4_eurusd_sector_growth_rotation_pullback(
    frame: pd.DataFrame,
    sector_context: pd.DataFrame,
) -> list[dict[str, Any]]:
    f = merge_sector_rotation(frame, sector_context, "EURUSD")
    signals: list[dict[str, Any]] = []
    px = point_size("EURUSD")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if not available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["xly_xlp_5d_pct"],
            row["xly_xlp_20d_pct"],
            row["qqq_spy_20d_pct"],
            row["sector_growth_score"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        xly_5d = float(row["xly_xlp_5d_pct"])
        xly_20d = float(row["xly_xlp_20d_pct"])
        qqq_20d = float(row["qqq_spy_20d_pct"])
        growth_score = float(row["sector_growth_score"])
        growth_risk_on = growth_score >= 1.25 and xly_5d >= 0.40 and xly_20d >= 1.50 and qqq_20d >= 0.80
        defensive_risk_off = growth_score <= -1.25 and xly_5d <= -0.40 and xly_20d <= -1.50 and qqq_20d <= -0.80
        if growth_risk_on and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(
                    signal(
                        "eurusd_h4_sector_growth_rotation_pullback_v0",
                        idx,
                        row,
                        "LONG",
                        stop,
                        "H4_EURUSD_SECTOR_GROWTH_RISK_ON_LONG",
                    )
                )
        elif defensive_risk_off and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(
                    signal(
                        "eurusd_h4_sector_growth_rotation_pullback_v0",
                        idx,
                        row,
                        "SHORT",
                        stop,
                        "H4_EURUSD_SECTOR_DEFENSIVE_RISK_OFF_SHORT",
                    )
                )
    return signals


def signals_h4_usdjpy_sector_cyclical_carry_pullback(
    frame: pd.DataFrame,
    sector_context: pd.DataFrame,
) -> list[dict[str, Any]]:
    f = merge_sector_rotation(frame, sector_context, "USDJPY")
    signals: list[dict[str, Any]] = []
    px = point_size("USDJPY")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        entry_row = f.iloc[idx + 1]
        if session_bucket(int(entry_row["hour_utc"])) not in {"asia", "london", "ny_morning"}:
            continue
        if not available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["xle_xlu_20d_pct"],
            row["xli_xlu_20d_pct"],
            row["xme_spy_20d_pct"],
            row["tip_ief_20d_pct"],
            row["sector_cyclical_score"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        xle_20d = float(row["xle_xlu_20d_pct"])
        xli_20d = float(row["xli_xlu_20d_pct"])
        xme_20d = float(row["xme_spy_20d_pct"])
        tip_20d = float(row["tip_ief_20d_pct"])
        cyclical_score = float(row["sector_cyclical_score"])
        cyclical_inflation_bid = (
            cyclical_score >= 1.50 and xle_20d >= 2.50 and xli_20d >= 1.50 and xme_20d >= 1.50 and tip_20d >= 0.20
        )
        defensive_rotation = (
            cyclical_score <= -1.50 and xle_20d <= -2.50 and xli_20d <= -1.50 and xme_20d <= -1.50 and tip_20d <= -0.20
        )
        if cyclical_inflation_bid and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(
                    signal(
                        "usdjpy_h4_sector_cyclical_carry_pullback_v0",
                        idx,
                        row,
                        "LONG",
                        stop,
                        "H4_USDJPY_SECTOR_CYCLICAL_INFLATION_LONG",
                    )
                )
        elif defensive_rotation and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(
                    signal(
                        "usdjpy_h4_sector_cyclical_carry_pullback_v0",
                        idx,
                        row,
                        "SHORT",
                        stop,
                        "H4_USDJPY_SECTOR_DEFENSIVE_ROTATION_SHORT",
                    )
                )
    return signals


def signals_h4_eurusd_currency_basket_dollar_pressure_pullback(
    frame: pd.DataFrame,
    currency_context: pd.DataFrame,
) -> list[dict[str, Any]]:
    f = merge_currency_basket(frame, currency_context, "EURUSD")
    signals: list[dict[str, Any]] = []
    px = point_size("EURUSD")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if not available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["fxa_uup_5d_pct"],
            row["fxa_uup_20d_pct"],
            row["cyb_uup_20d_pct"],
            row["risk_currency_score"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        fxa_5d = float(row["fxa_uup_5d_pct"])
        fxa_20d = float(row["fxa_uup_20d_pct"])
        cyb_20d = float(row["cyb_uup_20d_pct"])
        risk_score = float(row["risk_currency_score"])
        dollar_relief = risk_score >= 0.85 and fxa_5d >= 0.35 and fxa_20d >= 1.00 and cyb_20d >= 0.50
        dollar_pressure = risk_score <= -0.85 and fxa_5d <= -0.35 and fxa_20d <= -1.00 and cyb_20d <= -0.50
        if dollar_relief and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(
                    signal(
                        "eurusd_h4_currency_basket_dollar_pressure_pullback_v0",
                        idx,
                        row,
                        "LONG",
                        stop,
                        "H4_EURUSD_CURRENCY_BASKET_DOLLAR_RELIEF_LONG",
                    )
                )
        elif dollar_pressure and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(
                    signal(
                        "eurusd_h4_currency_basket_dollar_pressure_pullback_v0",
                        idx,
                        row,
                        "SHORT",
                        stop,
                        "H4_EURUSD_CURRENCY_BASKET_DOLLAR_PRESSURE_SHORT",
                    )
                )
    return signals


def signals_h4_usdjpy_safe_haven_currency_rotation_pullback(
    frame: pd.DataFrame,
    currency_context: pd.DataFrame,
) -> list[dict[str, Any]]:
    f = merge_currency_basket(frame, currency_context, "USDJPY")
    signals: list[dict[str, Any]] = []
    px = point_size("USDJPY")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        entry_row = f.iloc[idx + 1]
        if session_bucket(int(entry_row["hour_utc"])) not in {"asia", "london", "ny_morning"}:
            continue
        if not available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["fxa_uup_5d_pct"],
            row["fxa_uup_20d_pct"],
            row["fxf_uup_5d_pct"],
            row["fxf_uup_20d_pct"],
            row["safe_haven_score"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        fxa_5d = float(row["fxa_uup_5d_pct"])
        fxa_20d = float(row["fxa_uup_20d_pct"])
        fxf_5d = float(row["fxf_uup_5d_pct"])
        fxf_20d = float(row["fxf_uup_20d_pct"])
        safe_score = float(row["safe_haven_score"])
        carry_rotation = fxa_5d >= 0.35 and fxa_20d >= 1.00 and fxf_20d <= 0.40 and safe_score <= 0.10
        safe_haven_stress = fxa_5d <= -0.35 and fxa_20d <= -1.00 and fxf_5d >= 0.20 and fxf_20d >= 0.60 and safe_score >= 1.00
        if carry_rotation and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(
                    signal(
                        "usdjpy_h4_safe_haven_currency_rotation_pullback_v0",
                        idx,
                        row,
                        "LONG",
                        stop,
                        "H4_USDJPY_CURRENCY_BASKET_CARRY_ROTATION_LONG",
                    )
                )
        elif safe_haven_stress and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(
                    signal(
                        "usdjpy_h4_safe_haven_currency_rotation_pullback_v0",
                        idx,
                        row,
                        "SHORT",
                        stop,
                        "H4_USDJPY_CURRENCY_BASKET_SAFE_HAVEN_STRESS_SHORT",
                    )
                )
    return signals


def signals_h4_eurusd_bond_vol_pullback(frame: pd.DataFrame, bond_vol_context: pd.DataFrame) -> list[dict[str, Any]]:
    f = merge_bond_vol(frame, bond_vol_context, "EURUSD")
    signals: list[dict[str, Any]] = []
    px = point_size("EURUSD")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if not available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["move_5d_pct"],
            row["move_20d_pct"],
            row["move_z60"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        move_5d = float(row["move_5d_pct"])
        move_20d = float(row["move_20d_pct"])
        move_z = float(row["move_z60"])
        bond_vol_calm = move_5d <= -5.0 and move_20d <= -5.0 and move_z <= 0.25
        bond_vol_stress = move_5d >= 8.0 and move_z >= 0.75
        if bond_vol_calm and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(
                    signal(
                        "eurusd_h4_bond_vol_dollar_stress_pullback_v0",
                        idx,
                        row,
                        "LONG",
                        stop,
                        "H4_EURUSD_BOND_VOL_CALM_LONG",
                    )
                )
        elif bond_vol_stress and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(
                    signal(
                        "eurusd_h4_bond_vol_dollar_stress_pullback_v0",
                        idx,
                        row,
                        "SHORT",
                        stop,
                        "H4_EURUSD_BOND_VOL_STRESS_SHORT",
                    )
                )
    return signals


def signals_h4_usdjpy_bond_vol_pullback(frame: pd.DataFrame, bond_vol_context: pd.DataFrame) -> list[dict[str, Any]]:
    return bond_vol_usdjpy_pullback_signals(
        frame,
        bond_vol_context,
        candidate_id="usdjpy_h4_bond_vol_carry_pullback_v0",
        allowed_entry_sessions=None,
        calm_5d=-5.0,
        calm_20d=-5.0,
        stress_5d=8.0,
        stress_z=0.75,
    )


def signals_h4_usdjpy_bond_vol_asia_session_v1(frame: pd.DataFrame, bond_vol_context: pd.DataFrame) -> list[dict[str, Any]]:
    return bond_vol_usdjpy_pullback_signals(
        frame,
        bond_vol_context,
        candidate_id="usdjpy_h4_bond_vol_asia_session_carry_relief_v1",
        allowed_entry_sessions={"asia"},
        calm_5d=-4.0,
        calm_20d=-4.0,
        stress_5d=6.0,
        stress_z=0.50,
    )


def bond_vol_usdjpy_pullback_signals(
    frame: pd.DataFrame,
    bond_vol_context: pd.DataFrame,
    *,
    candidate_id: str,
    allowed_entry_sessions: set[str] | None,
    calm_5d: float,
    calm_20d: float,
    stress_5d: float,
    stress_z: float,
) -> list[dict[str, Any]]:
    f = merge_bond_vol(frame, bond_vol_context, "USDJPY")
    signals: list[dict[str, Any]] = []
    px = point_size("USDJPY")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        entry_row = f.iloc[idx + 1]
        if allowed_entry_sessions is not None and session_bucket(int(entry_row["hour_utc"])) not in allowed_entry_sessions:
            continue
        if not available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["move_5d_pct"],
            row["move_20d_pct"],
            row["move_z60"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        move_5d = float(row["move_5d_pct"])
        move_20d = float(row["move_20d_pct"])
        move_z = float(row["move_z60"])
        bond_vol_calm = move_5d <= calm_5d and move_20d <= calm_20d and move_z <= 0.25
        bond_vol_stress = move_5d >= stress_5d and move_z >= stress_z
        if bond_vol_calm and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(signal(candidate_id, idx, row, "LONG", stop, "H4_USDJPY_BOND_VOL_CALM_LONG"))
        elif bond_vol_stress and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(signal(candidate_id, idx, row, "SHORT", stop, "H4_USDJPY_BOND_VOL_STRESS_SHORT"))
    return signals


def signals_h4_eurusd_btc_risk_pullback(frame: pd.DataFrame, crypto_context: pd.DataFrame) -> list[dict[str, Any]]:
    f = merge_crypto_risk(frame, crypto_context, "EURUSD")
    signals: list[dict[str, Any]] = []
    px = point_size("EURUSD")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if not available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["btc_5d_pct"],
            row["btc_20d_pct"],
            row["btc_vol20"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        btc_5d = float(row["btc_5d_pct"])
        btc_20d = float(row["btc_20d_pct"])
        btc_vol20 = float(row["btc_vol20"])
        crypto_risk_on = btc_5d >= 5.0 and btc_20d >= 12.0 and btc_vol20 < 6.0
        crypto_risk_off = btc_5d <= -5.0 and btc_20d <= -12.0
        if crypto_risk_on and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(signal("eurusd_h4_btc_risk_beta_pullback_v0", idx, row, "LONG", stop, "H4_EURUSD_BTC_RISK_ON_LONG"))
        elif crypto_risk_off and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(signal("eurusd_h4_btc_risk_beta_pullback_v0", idx, row, "SHORT", stop, "H4_EURUSD_BTC_RISK_OFF_SHORT"))
    return signals


def signals_h4_usdjpy_btc_risk_pullback(frame: pd.DataFrame, crypto_context: pd.DataFrame) -> list[dict[str, Any]]:
    f = merge_crypto_risk(frame, crypto_context, "USDJPY")
    signals: list[dict[str, Any]] = []
    px = point_size("USDJPY")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        entry_row = f.iloc[idx + 1]
        if session_bucket(int(entry_row["hour_utc"])) not in {"asia", "ny_morning"}:
            continue
        if not available(
            row["atr14_points"],
            row["ema20"],
            row["ema50"],
            row["ema100"],
            row["btc_5d_pct"],
            row["btc_20d_pct"],
            row["btc_vol20"],
        ):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        btc_5d = float(row["btc_5d_pct"])
        btc_20d = float(row["btc_20d_pct"])
        btc_vol20 = float(row["btc_vol20"])
        crypto_risk_on = btc_5d >= 5.0 and btc_20d >= 12.0 and btc_vol20 < 6.0
        crypto_risk_off = btc_5d <= -5.0 and btc_20d <= -12.0
        if crypto_risk_on and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(signal("usdjpy_h4_btc_risk_carry_pullback_v0", idx, row, "LONG", stop, "H4_USDJPY_BTC_RISK_ON_LONG"))
        elif crypto_risk_off and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(signal("usdjpy_h4_btc_risk_carry_pullback_v0", idx, row, "SHORT", stop, "H4_USDJPY_BTC_RISK_OFF_SHORT"))
    return signals


def signals_h4_usdjpy_audjpy_cross_rotation_pullback(frame: pd.DataFrame, cross_context: pd.DataFrame) -> list[dict[str, Any]]:
    f = merge_fx_cross(frame, cross_context, "USDJPY")
    signals: list[dict[str, Any]] = []
    px = point_size("USDJPY")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if not available(row["atr14_points"], row["ema20"], row["ema50"], row["ema100"], row["cross_anchor_5d_pct"], row["cross_anchor_20d_pct"]):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        cross_5d = float(row["cross_anchor_5d_pct"])
        cross_20d = float(row["cross_anchor_20d_pct"])
        risk_on_rotation = cross_5d >= 0.75 and cross_20d >= 1.20
        risk_off_rotation = cross_5d <= -0.75 and cross_20d <= -1.20
        if risk_on_rotation and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(signal("usdjpy_h4_audjpy_cross_risk_rotation_pullback_v0", idx, row, "LONG", stop, "H4_USDJPY_AUDJPY_CROSS_RISK_ON_LONG"))
        elif risk_off_rotation and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(signal("usdjpy_h4_audjpy_cross_risk_rotation_pullback_v0", idx, row, "SHORT", stop, "H4_USDJPY_AUDJPY_CROSS_RISK_OFF_SHORT"))
    return signals


def signals_h4_eurusd_eurjpy_cross_confirmation_pullback(frame: pd.DataFrame, cross_context: pd.DataFrame) -> list[dict[str, Any]]:
    f = merge_fx_cross(frame, cross_context, "EURUSD")
    signals: list[dict[str, Any]] = []
    px = point_size("EURUSD")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if not available(row["atr14_points"], row["ema20"], row["ema50"], row["ema100"], row["cross_anchor_5d_pct"], row["cross_anchor_20d_pct"]):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        cross_5d = float(row["cross_anchor_5d_pct"])
        cross_20d = float(row["cross_anchor_20d_pct"])
        euro_strength = cross_5d >= 0.60 and cross_20d >= 1.00
        euro_weakness = cross_5d <= -0.60 and cross_20d <= -1.00
        if euro_strength and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(signal("eurusd_h4_eurjpy_cross_confirmation_pullback_v0", idx, row, "LONG", stop, "H4_EURUSD_EURJPY_CROSS_LONG"))
        elif euro_weakness and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(signal("eurusd_h4_eurjpy_cross_confirmation_pullback_v0", idx, row, "SHORT", stop, "H4_EURUSD_EURJPY_CROSS_SHORT"))
    return signals


def signals_h4_eurusd_vix_vxv_risk_pullback(frame: pd.DataFrame, risk: pd.DataFrame) -> list[dict[str, Any]]:
    f = merge_risk(frame, risk, "EURUSD")
    signals: list[dict[str, Any]] = []
    px = point_size("EURUSD")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if not available(row["atr14_points"], row["ema20"], row["ema50"], row["ema100"], row["vix"], row["vix_5d_pct"], row["vix_vxv_ratio"]):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        vix = float(row["vix"])
        vix_5d = float(row["vix_5d_pct"])
        ratio = float(row["vix_vxv_ratio"])
        risk_off = (vix_5d >= 10.0 and ratio >= 0.98) or (vix >= 25.0 and ratio >= 0.97)
        risk_on = vix_5d <= -10.0 and ratio <= 0.95
        if risk_off and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(signal("eurusd_h4_vix_vxv_risk_regime_pullback_v0", idx, row, "SHORT", stop, "H4_EURUSD_VIX_VXV_RISK_OFF_SHORT"))
        elif risk_on and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(signal("eurusd_h4_vix_vxv_risk_regime_pullback_v0", idx, row, "LONG", stop, "H4_EURUSD_VIX_VXV_RISK_ON_LONG"))
    return signals


def signals_h4_usdjpy_vix_vxv_risk_pullback(frame: pd.DataFrame, risk: pd.DataFrame) -> list[dict[str, Any]]:
    f = merge_risk(frame, risk, "USDJPY")
    signals: list[dict[str, Any]] = []
    px = point_size("USDJPY")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if not available(row["atr14_points"], row["ema20"], row["ema50"], row["ema100"], row["vix"], row["vix_5d_pct"], row["vix_vxv_ratio"]):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        vix = float(row["vix"])
        vix_5d = float(row["vix_5d_pct"])
        ratio = float(row["vix_vxv_ratio"])
        risk_off = (vix_5d >= 10.0 and ratio >= 0.98) or (vix >= 25.0 and ratio >= 0.97)
        risk_on = vix_5d <= -10.0 and ratio <= 0.95
        if risk_off and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(signal("usdjpy_h4_vix_vxv_risk_regime_pullback_v0", idx, row, "SHORT", stop, "H4_USDJPY_VIX_VXV_RISK_OFF_SHORT"))
        elif risk_on and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(signal("usdjpy_h4_vix_vxv_risk_regime_pullback_v0", idx, row, "LONG", stop, "H4_USDJPY_VIX_VXV_RISK_ON_LONG"))
    return signals


def signals_h4_eurusd_currency_etf_flow_pullback(frame: pd.DataFrame, flow: pd.DataFrame) -> list[dict[str, Any]]:
    f = merge_currency_flow(frame, flow, "EURUSD")
    signals: list[dict[str, Any]] = []
    px = point_size("EURUSD")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if not available(row["atr14_points"], row["ema20"], row["ema50"], row["ema100"], row["flow_5d_pct"], row["flow_20d_pct"]):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        flow_5d = float(row["flow_5d_pct"])
        flow_20d = float(row["flow_20d_pct"])
        if flow_5d >= 1.00 and flow_20d >= 1.35 and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(signal("eurusd_h4_currency_etf_flow_pullback_v0", idx, row, "LONG", stop, "H4_EURUSD_FXE_UUP_FLOW_LONG_PULLBACK"))
        elif flow_5d <= -1.00 and flow_20d <= -1.35 and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(signal("eurusd_h4_currency_etf_flow_pullback_v0", idx, row, "SHORT", stop, "H4_EURUSD_FXE_UUP_FLOW_SHORT_PULLBACK"))
    return signals


def signals_h4_usdjpy_currency_etf_flow_pullback(frame: pd.DataFrame, flow: pd.DataFrame) -> list[dict[str, Any]]:
    f = merge_currency_flow(frame, flow, "USDJPY")
    signals: list[dict[str, Any]] = []
    px = point_size("USDJPY")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if not available(row["atr14_points"], row["ema20"], row["ema50"], row["ema100"], row["flow_5d_pct"], row["flow_20d_pct"]):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        open_price = float(row["open"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        flow_5d = float(row["flow_5d_pct"])
        flow_20d = float(row["flow_20d_pct"])
        if flow_5d >= 1.00 and flow_20d >= 1.35 and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > open_price and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.05 * atr * px)
                signals.append(signal("usdjpy_h4_currency_etf_flow_pullback_v0", idx, row, "LONG", stop, "H4_USDJPY_FXY_UUP_FLOW_LONG_PULLBACK"))
        elif flow_5d <= -1.00 and flow_20d <= -1.35 and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < open_price and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.05 * atr * px)
                signals.append(signal("usdjpy_h4_currency_etf_flow_pullback_v0", idx, row, "SHORT", stop, "H4_USDJPY_FXY_UUP_FLOW_SHORT_PULLBACK"))
    return signals


def signals_h4_compression_breakout(frame: pd.DataFrame) -> list[dict[str, Any]]:
    f = with_features(frame, "EURUSD")
    signals: list[dict[str, Any]] = []
    used_boxes: set[int] = set()
    for idx in range(80, len(f) - 1):
        row = f.iloc[idx]
        if not available(row["atr14_points"], row["range_points"]):
            continue
        box = f.iloc[idx - 10 : idx]
        box_high = float(box["high"].max())
        box_low = float(box["low"].min())
        box_range_points = (box_high - box_low) / point_size("EURUSD")
        median_range = float(f.iloc[idx - 60 : idx]["range_points"].median())
        atr = float(row["atr14_points"])
        if box_range_points <= 0 or box_range_points > 0.85 * median_range:
            continue
        if atr <= 0:
            continue
        direction = ""
        close = float(row["close"])
        open_price = float(row["open"])
        if close > box_high and close > open_price and float(row["body_points"]) >= 0.35 * atr:
            direction = "LONG"
        elif close < box_low and close < open_price and float(row["body_points"]) >= 0.35 * atr:
            direction = "SHORT"
        if not direction:
            continue
        if idx in used_boxes:
            continue
        used_boxes.add(idx)
        if direction == "LONG":
            stop = min(box_low, close - atr * point_size("EURUSD"))
        else:
            stop = max(box_high, close + atr * point_size("EURUSD"))
        signals.append(signal("eurusd_h4_compression_breakout_v0", idx, row, direction, stop, "H4_COMPRESSION_BREAKOUT"))
    return signals


def signals_h4_usdjpy_carry_session_pullback_v1(frame: pd.DataFrame) -> list[dict[str, Any]]:
    f = with_features(frame, "USDJPY")
    signals: list[dict[str, Any]] = []
    px = point_size("USDJPY")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if session_bucket(int(row["hour_utc"])) not in {"asia", "ny_morning"}:
            continue
        if not available(row["atr14_points"], row["ema20"], row["ema50"], row["ema100"], row["ema200"]):
            continue
        prior_ema200 = f.iloc[idx - 40]["ema200"]
        if not available(prior_ema200):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        ema200 = float(row["ema200"])
        ema200_slope_points = (ema200 - float(prior_ema200)) / px
        regime_floor = float(f.iloc[idx - 120 : idx]["close"].median())
        if not (ema20 > ema50 > ema100 > ema200):
            continue
        if ema200_slope_points < 0.30 * atr or close <= regime_floor:
            continue
        touched = float(row["low"]) <= ema20 + 0.25 * atr * px
        confirmed = close > float(row["open"]) and close > ema20
        if not touched or not confirmed:
            continue
        recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
        stop = min(recent_low, close - 1.10 * atr * px)
        signals.append(signal("usdjpy_h4_carry_session_pullback_v1", idx, row, "LONG", stop, "H4_USDJPY_CARRY_SESSION_PULLBACK_V1"))
    return signals


def signals_h4_eurusd_range_rejection_reversion_v0(frame: pd.DataFrame) -> list[dict[str, Any]]:
    f = with_features(frame, "EURUSD")
    signals: list[dict[str, Any]] = []
    px = point_size("EURUSD")
    for idx in range(220, len(f) - 1):
        row = f.iloc[idx]
        if not available(row["atr14_points"], row["ema50"], row["ema200"]):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        ema_gap_points = abs(float(row["ema50"]) - float(row["ema200"])) / px
        if ema_gap_points > 1.25 * atr:
            continue
        prior = f.iloc[idx - 24 : idx]
        prior_high = float(prior["high"].max())
        prior_low = float(prior["low"].min())
        close = float(row["close"])
        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        buffer = 0.10 * atr * px
        if high > prior_high + buffer and close < prior_high and close < open_price:
            stop = high + 0.45 * atr * px
            signals.append(signal("eurusd_h4_range_rejection_reversion_v0", idx, row, "SHORT", stop, "H4_EURUSD_RANGE_HIGH_REJECTION"))
        elif low < prior_low - buffer and close > prior_low and close > open_price:
            stop = low - 0.45 * atr * px
            signals.append(signal("eurusd_h4_range_rejection_reversion_v0", idx, row, "LONG", stop, "H4_EURUSD_RANGE_LOW_REJECTION"))
    return signals


def signals_h4_eurusd_macro_pressure_reversal(frame: pd.DataFrame, macro: pd.DataFrame) -> list[dict[str, Any]]:
    f = merge_macro(frame, macro, "EURUSD")
    signals: list[dict[str, Any]] = []
    px = point_size("EURUSD")
    for idx in range(240, len(f) - 1):
        row = f.iloc[idx]
        if not available(row["atr14_points"], row["macro_pressure_score"], row["real_yield_delta_20d"], row["dollar_pct_20d"]):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        prior = f.iloc[idx - 24 : idx]
        prior_high = float(prior["high"].max())
        prior_low = float(prior["low"].min())
        close = float(row["close"])
        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        pressure = float(row["macro_pressure_score"])
        real_delta = float(row["real_yield_delta_20d"])
        dollar_delta = float(row["dollar_pct_20d"])
        buffer = 0.08 * atr * px
        if pressure >= 1.75 and real_delta > 0.10 and dollar_delta > 0.75:
            if low < prior_low - buffer and close > prior_low and close > open_price:
                stop = low - 0.45 * atr * px
                signals.append(signal("eurusd_h4_real_yield_dollar_pressure_reversal_v0", idx, row, "LONG", stop, "H4_EURUSD_MACRO_PRESSURE_LOW_REJECTION"))
        elif pressure <= -1.75 and real_delta < -0.10 and dollar_delta < -0.75:
            if high > prior_high + buffer and close < prior_high and close < open_price:
                stop = high + 0.45 * atr * px
                signals.append(signal("eurusd_h4_real_yield_dollar_pressure_reversal_v0", idx, row, "SHORT", stop, "H4_EURUSD_MACRO_PRESSURE_HIGH_REJECTION"))
    return signals


def signals_h4_eurusd_macro_pressure_followthrough(frame: pd.DataFrame, macro: pd.DataFrame) -> list[dict[str, Any]]:
    f = merge_macro(frame, macro, "EURUSD")
    signals: list[dict[str, Any]] = []
    px = point_size("EURUSD")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if not available(row["atr14_points"], row["ema20"], row["ema50"], row["ema100"], row["macro_pressure_score"]):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        pressure = float(row["macro_pressure_score"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        if pressure >= 1.50 and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.20 * atr * px
            confirmed = close < float(row["open"]) and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.10 * atr * px)
                signals.append(signal("eurusd_h4_real_yield_dollar_pressure_followthrough_v0", idx, row, "SHORT", stop, "H4_EURUSD_MACRO_PRESSURE_SHORT_PULLBACK"))
        elif pressure <= -1.50 and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.20 * atr * px
            confirmed = close > float(row["open"]) and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.10 * atr * px)
                signals.append(signal("eurusd_h4_real_yield_dollar_pressure_followthrough_v0", idx, row, "LONG", stop, "H4_EURUSD_MACRO_PRESSURE_LONG_PULLBACK"))
    return signals


def signals_h4_usdjpy_macro_pressure_followthrough(frame: pd.DataFrame, macro: pd.DataFrame) -> list[dict[str, Any]]:
    f = merge_macro(frame, macro, "USDJPY")
    signals: list[dict[str, Any]] = []
    px = point_size("USDJPY")
    for idx in range(260, len(f) - 1):
        row = f.iloc[idx]
        if not available(row["atr14_points"], row["ema20"], row["ema50"], row["ema100"], row["macro_pressure_score"]):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        pressure = float(row["macro_pressure_score"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        if pressure >= 1.50 and ema20 > ema50 > ema100:
            touched = float(row["low"]) <= ema20 + 0.25 * atr * px
            confirmed = close > float(row["open"]) and close > ema20
            if touched and confirmed:
                recent_low = float(f.iloc[idx - 5 : idx + 1]["low"].min())
                stop = min(recent_low, close - 1.10 * atr * px)
                signals.append(signal("usdjpy_h4_real_yield_dollar_pressure_followthrough_v0", idx, row, "LONG", stop, "H4_USDJPY_MACRO_PRESSURE_LONG_PULLBACK"))
        elif pressure <= -1.50 and ema20 < ema50 < ema100:
            touched = float(row["high"]) >= ema20 - 0.25 * atr * px
            confirmed = close < float(row["open"]) and close < ema20
            if touched and confirmed:
                recent_high = float(f.iloc[idx - 5 : idx + 1]["high"].max())
                stop = max(recent_high, close + 1.10 * atr * px)
                signals.append(signal("usdjpy_h4_real_yield_dollar_pressure_followthrough_v0", idx, row, "SHORT", stop, "H4_USDJPY_MACRO_PRESSURE_SHORT_PULLBACK"))
    return signals


def signals_h1_london_asia_breakout(frame: pd.DataFrame) -> list[dict[str, Any]]:
    f = with_features(frame, "EURUSD")
    signals: list[dict[str, Any]] = []
    grouped = {date: group for date, group in f.groupby("date_utc", sort=True)}
    date_to_indices = {date: list(group.index) for date, group in grouped.items()}
    for date, group in grouped.items():
        asia = group[(group["hour_utc"] >= 0) & (group["hour_utc"] <= 5)]
        london = group[(group["hour_utc"] >= 7) & (group["hour_utc"] <= 10)]
        if len(asia) < 4 or london.empty:
            continue
        asia_high = float(asia["high"].max())
        asia_low = float(asia["low"].min())
        asia_range = asia_high - asia_low
        if asia_range <= 0:
            continue
        for idx in date_to_indices[date]:
            if idx not in london.index:
                continue
            row = f.iloc[idx]
            atr = float(row["atr14_points"]) if pd.notna(row["atr14_points"]) else 0.0
            if atr <= 0:
                continue
            close = float(row["close"])
            buffer = 0.08 * atr * point_size("EURUSD")
            direction = ""
            if close > asia_high + buffer and close > float(row["open"]):
                direction = "LONG"
                stop = min(asia_low, close - 0.85 * atr * point_size("EURUSD"))
            elif close < asia_low - buffer and close < float(row["open"]):
                direction = "SHORT"
                stop = max(asia_high, close + 0.85 * atr * point_size("EURUSD"))
            if direction:
                signals.append(signal("eurusd_h1_london_asia_range_breakout_v0", idx, row, direction, stop, "H1_LONDON_ASIA_RANGE_BREAKOUT"))
                break
    return signals


def signals_h4_usdjpy_trend_pullback(frame: pd.DataFrame) -> list[dict[str, Any]]:
    f = with_features(frame, "USDJPY")
    signals: list[dict[str, Any]] = []
    for idx in range(220, len(f) - 1):
        row = f.iloc[idx]
        if not available(row["atr14_points"], row["ema20"], row["ema50"], row["ema100"], row["ema200"]):
            continue
        atr = float(row["atr14_points"])
        if atr <= 0:
            continue
        close = float(row["close"])
        ema20 = float(row["ema20"])
        ema50 = float(row["ema50"])
        ema100 = float(row["ema100"])
        ema200 = float(row["ema200"])
        long_trend = ema20 > ema50 > ema100 > ema200
        short_trend = ema20 < ema50 < ema100 < ema200
        if not long_trend and not short_trend:
            continue
        low = float(row["low"])
        high = float(row["high"])
        if long_trend:
            touched = low <= ema20 + 0.30 * atr * point_size("USDJPY")
            confirmed = close > float(row["open"]) and close > ema20
            if not touched or not confirmed:
                continue
            recent_low = float(f.iloc[idx - 4 : idx + 1]["low"].min())
            stop = min(recent_low, close - 1.05 * atr * point_size("USDJPY"))
            signals.append(signal("usdjpy_h4_trend_continuation_pullback_v0", idx, row, "LONG", stop, "H4_USDJPY_TREND_PULLBACK"))
        else:
            touched = high >= ema20 - 0.30 * atr * point_size("USDJPY")
            confirmed = close < float(row["open"]) and close < ema20
            if not touched or not confirmed:
                continue
            recent_high = float(f.iloc[idx - 4 : idx + 1]["high"].max())
            stop = max(recent_high, close + 1.05 * atr * point_size("USDJPY"))
            signals.append(signal("usdjpy_h4_trend_continuation_pullback_v0", idx, row, "SHORT", stop, "H4_USDJPY_TREND_PULLBACK"))
    return signals


def signals_h1_tokyo_failed_break(frame: pd.DataFrame) -> list[dict[str, Any]]:
    f = with_features(frame, "USDJPY")
    signals: list[dict[str, Any]] = []
    grouped = {date: group for date, group in f.groupby("date_utc", sort=True)}
    date_to_indices = {date: list(group.index) for date, group in grouped.items()}
    for date, group in grouped.items():
        tokyo = group[(group["hour_utc"] >= 0) & (group["hour_utc"] <= 5)]
        handoff = group[(group["hour_utc"] >= 6) & (group["hour_utc"] <= 10)]
        if len(tokyo) < 4 or handoff.empty:
            continue
        range_high = float(tokyo["high"].max())
        range_low = float(tokyo["low"].min())
        for idx in date_to_indices[date]:
            if idx not in handoff.index:
                continue
            row = f.iloc[idx]
            atr = float(row["atr14_points"]) if pd.notna(row["atr14_points"]) else 0.0
            if atr <= 0:
                continue
            close = float(row["close"])
            high = float(row["high"])
            low = float(row["low"])
            if high > range_high and close < range_high:
                stop = high + 0.35 * atr * point_size("USDJPY")
                signals.append(signal("usdjpy_h1_tokyo_range_failed_break_v0", idx, row, "SHORT", stop, "H1_TOKYO_FAILED_HIGH_BREAK"))
                break
            if low < range_low and close > range_low:
                stop = low - 0.35 * atr * point_size("USDJPY")
                signals.append(signal("usdjpy_h1_tokyo_range_failed_break_v0", idx, row, "LONG", stop, "H1_TOKYO_FAILED_LOW_BREAK"))
                break
    return signals


def available(*values: Any) -> bool:
    return all(pd.notna(value) for value in values)


def signal(candidate_id: str, idx: int, row: pd.Series, direction: str, stop: float, reason: str) -> dict[str, Any]:
    entry = float(row["close"])
    return {
        "candidate_id": candidate_id,
        "signal_index": int(idx),
        "signal_time_utc": row["timestamp_utc"],
        "entry_time_utc": row["timestamp_utc"],
        "direction": direction,
        "entry_price": entry,
        "stop_loss": stop,
        "reason_code": reason,
    }


def cost_proxy_from_cells(cells: list[CostCell]) -> dict[tuple[str, str], dict[str, float]]:
    proxy: dict[tuple[str, str], dict[str, float]] = {}
    for cell in cells:
        if cell.broker != "capital_com" or not cell.has_spread:
            continue
        proxy[(cell.symbol, cell.timeframe)] = {
            "median": cell.spread_median_points,
            "p95": cell.spread_p95_points,
        }
    return proxy


def run_first_screen(p: Paths, cells: list[CostCell]) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    return run_specs_screen(p, cells, candidate_specs())


def run_second_pass_screen(p: Paths, cells: list[CostCell]) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    return run_specs_screen(p, cells, candidate_specs_second_pass())


def run_specs_screen(
    p: Paths,
    cells: list[CostCell],
    specs: list[CandidateSpec],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    proxy = cost_proxy_from_cells(cells)
    summary_rows: list[dict[str, Any]] = []
    trade_map: dict[str, list[dict[str, Any]]] = {}
    for spec in specs:
        candidate_trades: list[dict[str, Any]] = []
        for broker in ("capital_com", "dukascopy", "pepperstone"):
            frame = load_bars(p.bars, broker, spec.symbol, spec.timeframe)
            if frame.empty:
                continue
            if broker != "capital_com" and (spec.symbol, spec.timeframe) not in proxy:
                continue
            signals = spec.generator(frame)
            trades = simulate_trades(spec, frame, broker, signals, proxy.get((spec.symbol, spec.timeframe)))
            candidate_trades.extend(trades)
            summary_rows.append(summary_metrics(spec, trades, broker=broker, level="broker"))
        deduped = dedupe_trades(candidate_trades)
        trade_map[spec.candidate_id] = deduped
        summary_rows.append(summary_metrics(spec, deduped, broker="all_deduped", level="overall"))
    return summary_rows, trade_map


def run_recent_proxy_stress(p: Paths, cells: list[CostCell]) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    return run_recent_proxy_stress_for_specs(p, cells, candidate_specs_recent_proxy())


def run_recent_proxy_stress_for_specs(
    p: Paths,
    cells: list[CostCell],
    specs: list[CandidateSpec],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    proxy = cost_proxy_from_cells(cells)
    summary_rows: list[dict[str, Any]] = []
    trade_map: dict[str, list[dict[str, Any]]] = {}
    for spec in specs:
        if (spec.symbol, spec.timeframe) not in proxy:
            trade_map[spec.candidate_id] = []
            summary_rows.append(summary_metrics(spec, [], broker="yahoo_recent_proxy", level="recent_proxy"))
            continue
        frame = load_recent_proxy_bars(p, spec.symbol, spec.timeframe)
        if frame.empty:
            trade_map[spec.candidate_id] = []
            summary_rows.append(summary_metrics(spec, [], broker="yahoo_recent_proxy", level="recent_proxy"))
            continue
        signals = spec.generator(frame)
        trades = simulate_trades(spec, frame, "yahoo_recent_proxy", signals, proxy.get((spec.symbol, spec.timeframe)))
        trade_map[spec.candidate_id] = trades
        summary_rows.append(summary_metrics(spec, trades, broker="yahoo_recent_proxy", level="recent_proxy"))
    return summary_rows, trade_map


def simulate_trades(
    spec: CandidateSpec,
    frame: pd.DataFrame,
    broker: str,
    signals: list[dict[str, Any]],
    proxy_spread: dict[str, float] | None,
) -> list[dict[str, Any]]:
    trades: list[dict[str, Any]] = []
    frame = frame.reset_index(drop=True)
    px = point_size(spec.symbol)
    open_until = -1
    for raw in signals:
        start_idx = int(raw["signal_index"]) + 1
        if start_idx <= open_until or start_idx >= len(frame):
            continue
        entry_row = frame.iloc[start_idx]
        entry = float(entry_row["open"])
        stop = float(raw["stop_loss"])
        direction = str(raw["direction"])
        risk_price = abs(entry - stop)
        stop_points = risk_price / px
        if stop_points < 5:
            continue
        if direction == "LONG":
            target = entry + spec.target_r * risk_price
        else:
            target = entry - spec.target_r * risk_price
        exit_idx = min(start_idx + spec.max_hold_bars - 1, len(frame) - 1)
        exit_price = float(frame.iloc[exit_idx]["close"])
        gross_r = directional_r(direction, entry, exit_price, risk_price)
        exit_reason = "TIME_EXIT"
        for idx in range(start_idx, exit_idx + 1):
            row = frame.iloc[idx]
            high = float(row["high"])
            low = float(row["low"])
            if direction == "LONG":
                stop_hit = low <= stop
                target_hit = high >= target
            else:
                stop_hit = high >= stop
                target_hit = low <= target
            if stop_hit and target_hit:
                exit_idx = idx
                exit_price = stop
                gross_r = -1.0
                exit_reason = "SL_ADVERSE_FIRST"
                break
            if stop_hit:
                exit_idx = idx
                exit_price = stop
                gross_r = -1.0
                exit_reason = "SL"
                break
            if target_hit:
                exit_idx = idx
                exit_price = target
                gross_r = spec.target_r
                exit_reason = "TP"
                break
        spread_points, spread_source = trade_spread_points(entry_row, broker, proxy_spread)
        slip_points = slippage_points(spec.symbol, exit_reason)
        cost_r = (spread_points + slip_points) / stop_points
        net_r = gross_r - cost_r
        open_until = exit_idx
        trades.append(
            {
                "candidate_id": spec.candidate_id,
                "symbol": spec.symbol,
                "timeframe": spec.timeframe,
                "broker": broker,
                "family": spec.family,
                "signal_time_utc": iso(raw["signal_time_utc"]),
                "entry_time_utc": iso(entry_row["timestamp_utc"]),
                "exit_time_utc": iso(frame.iloc[exit_idx]["timestamp_utc"]),
                "direction": direction,
                "entry_price": round(entry, 6),
                "stop_loss": round(stop, 6),
                "target_price": round(target, 6),
                "exit_price": round(exit_price, 6),
                "stop_distance_points": round(stop_points, 4),
                "spread_points": round(spread_points, 4),
                "slippage_points": round(slip_points, 4),
                "cost_r": round(cost_r, 8),
                "gross_r": round(gross_r, 8),
                "net_r": round(net_r, 8),
                "estimated_net_pnl_usd": round(net_r * FIXED_RISK_USD, 2),
                "exit_reason": exit_reason,
                "reason_code": raw["reason_code"],
                "spread_source": spread_source,
                "session_utc": session_bucket(int(entry_row["bar_start_utc"].hour)),
                "month": str(entry_row["timestamp_utc"])[:7],
                "week": pd.Timestamp(entry_row["timestamp_utc"]).strftime("%G-W%V"),
            }
        )
    return trades


def trade_spread_points(row: pd.Series, broker: str, proxy_spread: dict[str, float] | None) -> tuple[float, str]:
    direct = pd.to_numeric(pd.Series([row.get("spread_median_points")]), errors="coerce").iloc[0]
    if pd.notna(direct) and direct > 0:
        return float(direct), "bar_spread_median"
    if proxy_spread and not math.isnan(proxy_spread["median"]):
        return float(proxy_spread["median"]), "capital_com_symbol_timeframe_proxy"
    return 0.0, "missing_spread_zero_not_expected"


def directional_r(direction: str, entry: float, exit_price: float, risk_price: float) -> float:
    if direction == "LONG":
        return (exit_price - entry) / risk_price
    return (entry - exit_price) / risk_price


def dedupe_trades(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for trade in sorted(trades, key=lambda item: (item["candidate_id"], item["entry_time_utc"], item["broker"])):
        key = (
            trade["candidate_id"],
            trade["symbol"],
            trade["timeframe"],
            trade["broker"],
            trade["entry_time_utc"],
            trade["direction"],
            trade["entry_price"],
            trade["stop_loss"],
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(trade)
    return deduped


def summary_metrics(spec: CandidateSpec, trades: list[dict[str, Any]], *, broker: str, level: str) -> dict[str, Any]:
    net = [float(t["net_r"]) for t in trades]
    gross = [float(t["gross_r"]) for t in trades]
    wins = [value for value in net if value > 0]
    losses = [value for value in net if value < 0]
    trade_count = len(net)
    pf = sum(wins) / abs(sum(losses)) if losses else (float("inf") if wins else float("nan"))
    monthly = aggregate_by(trades, "month")
    weekly = aggregate_by(trades, "week")
    top_removed = sum(net) - max(wins) if wins else sum(net)
    return {
        "candidate_id": spec.candidate_id,
        "symbol": spec.symbol,
        "timeframe": spec.timeframe,
        "family": spec.family,
        "level": level,
        "broker": broker,
        "trade_count": trade_count,
        "long_trades": count_where(trades, "direction", "LONG"),
        "short_trades": count_where(trades, "direction", "SHORT"),
        "win_rate_pct": pct(len(wins), trade_count),
        "gross_expectancy_r": mean(gross),
        "net_expectancy_r": mean(net),
        "total_net_r": sum(net),
        "profit_factor": pf,
        "max_drawdown_r": max_drawdown(net),
        "median_stop_points": median([float(t["stop_distance_points"]) for t in trades]),
        "median_cost_r": median([float(t["cost_r"]) for t in trades]),
        "top_winner_removed_net_r": top_removed,
        "positive_months": sum(1 for value in monthly.values() if value > 0),
        "total_months": len(monthly),
        "positive_weeks": sum(1 for value in weekly.values() if value > 0),
        "total_weeks": len(weekly),
        "best_month_r": max(monthly.values()) if monthly else 0.0,
        "worst_month_r": min(monthly.values()) if monthly else 0.0,
        "best_week_r": max(weekly.values()) if weekly else 0.0,
        "worst_week_r": min(weekly.values()) if weekly else 0.0,
        "trades_per_year": trades_per_year(trades),
        "decision": candidate_decision(trade_count, pf, mean(net), max_drawdown(net), top_removed, monthly, weekly),
    }


def candidate_decision(
    trade_count: int,
    pf: float,
    expectancy: float,
    drawdown: float,
    top_removed: float,
    monthly: dict[str, float],
    weekly: dict[str, float],
) -> str:
    if trade_count < 80:
        return "REJECT_LOW_SAMPLE"
    if not math.isfinite(pf) or pf < 1.15:
        return "REJECT_WEAK_NET_EDGE"
    if expectancy <= 0.03:
        return "REJECT_WEAK_EXPECTANCY"
    if top_removed <= 0:
        return "REJECT_TOP_WINNER_DEPENDENT"
    if drawdown > 18:
        return "REJECT_DRAWDOWN"
    if monthly and sum(1 for value in monthly.values() if value > 0) / len(monthly) < 0.52:
        return "REJECT_MONTHLY_INSTABILITY"
    if weekly and sum(1 for value in weekly.values() if value > 0) / len(weekly) < 0.45:
        return "REJECT_WEEKLY_INSTABILITY"
    return "WATCHLIST_NEEDS_SECOND_PASS"


def aggregate_by(trades: list[dict[str, Any]], column: str) -> dict[str, float]:
    result: dict[str, float] = {}
    for trade in trades:
        key = str(trade[column])
        result[key] = result.get(key, 0.0) + float(trade["net_r"])
    return result


def count_where(trades: list[dict[str, Any]], column: str, value: str) -> int:
    return sum(1 for trade in trades if trade[column] == value)


def pct(numerator: int, denominator: int) -> float:
    return (numerator / denominator * 100.0) if denominator else 0.0


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def max_drawdown(values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    drawdown = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    return drawdown


def trades_per_year(trades: list[dict[str, Any]]) -> float:
    if len(trades) < 2:
        return float(len(trades))
    start = pd.Timestamp(trades[0]["entry_time_utc"])
    end = pd.Timestamp(trades[-1]["entry_time_utc"])
    years = max((end - start).days / 365.25, 1 / 365.25)
    return len(trades) / years


def session_bucket(hour: int) -> str:
    if 0 <= hour <= 5:
        return "asia"
    if 6 <= hour <= 11:
        return "london"
    if 12 <= hour <= 16:
        return "ny_morning"
    if 17 <= hour <= 21:
        return "ny_late"
    return "rollover"


def write_screen_outputs(
    p: Paths,
    summary_rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
) -> None:
    summary_path = p.tables / f"FOREX_FIRST_CANDIDATE_SCREEN_SUMMARY_{RUN_DATE}.csv"
    if summary_rows:
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0].keys()))
            writer.writeheader()
            for row in summary_rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in trade_map.items():
        path = p.tables / f"{candidate_id}_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    report = render_screen_report(summary_rows, trade_map, summary_path, cells)
    (p.reports / f"FOREX_FIRST_CANDIDATE_SCREEN_{RUN_DATE}.md").write_text(report, encoding="utf-8")


def write_second_pass_outputs(
    p: Paths,
    summary_rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
) -> dict[str, str]:
    summary_path = p.tables / f"FOREX_SECOND_PASS_SCREEN_SUMMARY_{RUN_DATE}.csv"
    if summary_rows:
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0].keys()))
            writer.writeheader()
            for row in summary_rows:
                writer.writerow(format_summary_row(row))
    final_gates = second_pass_gate_decisions(summary_rows, trade_map)
    for candidate_id, trades in trade_map.items():
        path = p.tables / f"{candidate_id}_SECOND_PASS_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    report = render_second_pass_report(summary_rows, trade_map, summary_path, cells, final_gates)
    (p.reports / f"FOREX_SECOND_PASS_SCREEN_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return final_gates


def write_recent_proxy_stress_outputs(
    p: Paths,
    summary_rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
) -> dict[str, str]:
    summary_path = p.tables / f"FOREX_RECENT_PROXY_STRESS_SUMMARY_{RUN_DATE}.csv"
    if summary_rows:
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0].keys()))
            writer.writeheader()
            for row in summary_rows:
                writer.writerow(format_summary_row(row))
    gates = {row["candidate_id"]: recent_proxy_gate(row) for row in summary_rows}
    for candidate_id, trades in trade_map.items():
        path = p.tables / f"{candidate_id}_RECENT_PROXY_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    status_path = p.reports / f"FOREX_RECENT_PROXY_STRESS_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "RECENT_PROXY_RESEARCH_ONLY",
                "runtime_touched": False,
                "gates": gates,
                "summary": [format_summary_row(row) for row in summary_rows],
                "caveat": "Yahoo recent H1 FX proxy bars are not broker-authoritative and carry no broker spread. Costs use local historical Capital.com spread proxies where available.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_recent_proxy_stress_report(summary_rows, trade_map, summary_path, status_path, cells, gates)
    (p.reports / f"FOREX_RECENT_PROXY_STRESS_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_macro_screen(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    macro = load_macro_context(p)
    specs = candidate_specs_macro(macro)
    historical_rows, historical_trades = run_specs_screen(p, cells, specs)
    recent_rows, recent_trades = run_recent_proxy_stress_for_specs(p, cells, specs)
    return historical_rows, historical_trades, recent_rows, recent_trades, macro_context_summary(p, macro)


def write_macro_screen_outputs(
    p: Paths,
    historical_rows: list[dict[str, Any]],
    historical_trade_map: dict[str, list[dict[str, Any]]],
    recent_rows: list[dict[str, Any]],
    recent_trade_map: dict[str, list[dict[str, Any]]],
    macro_summary: dict[str, Any],
) -> dict[str, str]:
    historical_summary_path = p.tables / f"FOREX_MACRO_RATE_SCREEN_SUMMARY_{RUN_DATE}.csv"
    recent_summary_path = p.tables / f"FOREX_MACRO_RATE_RECENT_PROXY_SUMMARY_{RUN_DATE}.csv"
    if historical_rows:
        with historical_summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(historical_rows[0].keys()))
            writer.writeheader()
            for row in historical_rows:
                writer.writerow(format_summary_row(row))
    if recent_rows:
        with recent_summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(recent_rows[0].keys()))
            writer.writeheader()
            for row in recent_rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in historical_trade_map.items():
        path = p.tables / f"{candidate_id}_MACRO_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    for candidate_id, trades in recent_trade_map.items():
        path = p.tables / f"{candidate_id}_MACRO_RECENT_PROXY_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    final_gates = macro_final_gates(historical_rows, recent_rows)
    status_path = p.reports / f"FOREX_MACRO_RATE_SCREEN_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "MACRO_RATE_RESEARCH_ONLY",
                "runtime_touched": False,
                "macro_context": macro_summary,
                "final_gates": final_gates,
                "historical_overall": [format_summary_row(row) for row in historical_rows if row.get("level") == "overall"],
                "recent_proxy": [format_summary_row(row) for row in recent_rows],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_macro_screen_report(
        historical_rows,
        recent_rows,
        historical_summary_path,
        recent_summary_path,
        status_path,
        macro_summary,
        final_gates,
    )
    (p.reports / f"FOREX_MACRO_RATE_SCREEN_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return final_gates


def run_treasury_curve_screen(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    curve_context = load_treasury_curve_context(p)
    specs = candidate_specs_treasury_curve(curve_context)
    historical_rows, historical_trades = run_specs_screen(p, cells, specs)
    recent_rows, recent_trades = run_recent_proxy_stress_for_specs(p, cells, specs)
    return historical_rows, historical_trades, recent_rows, recent_trades, treasury_curve_context_summary(p, curve_context)


def write_treasury_curve_screen_outputs(
    p: Paths,
    historical_rows: list[dict[str, Any]],
    historical_trade_map: dict[str, list[dict[str, Any]]],
    recent_rows: list[dict[str, Any]],
    recent_trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    curve_summary: dict[str, Any],
) -> dict[str, str]:
    historical_summary_path = p.tables / f"FOREX_TREASURY_CURVE_SCREEN_SUMMARY_{RUN_DATE}.csv"
    recent_summary_path = p.tables / f"FOREX_TREASURY_CURVE_RECENT_PROXY_SUMMARY_{RUN_DATE}.csv"
    if historical_rows:
        with historical_summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(historical_rows[0].keys()))
            writer.writeheader()
            for row in historical_rows:
                writer.writerow(format_summary_row(row))
    if recent_rows:
        with recent_summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(recent_rows[0].keys()))
            writer.writeheader()
            for row in recent_rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in historical_trade_map.items():
        path = p.tables / f"{candidate_id}_TREASURY_CURVE_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    for candidate_id, trades in recent_trade_map.items():
        path = p.tables / f"{candidate_id}_TREASURY_CURVE_RECENT_PROXY_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = treasury_curve_gates(historical_rows, recent_rows)
    status_path = p.reports / f"FOREX_TREASURY_CURVE_SCREEN_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "TREASURY_CURVE_RESEARCH_ONLY",
                "runtime_touched": False,
                "treasury_curve_context": curve_summary,
                "final_gates": gates,
                "historical_overall": [
                    format_summary_row(row) for row in historical_rows if row.get("level") == "overall"
                ],
                "recent_proxy": [format_summary_row(row) for row in recent_rows],
                "caveat": (
                    "FRED Treasury curve data is public macro context, not broker-authoritative FX evidence. Recent "
                    "stress uses Yahoo FX proxy bars with historical Capital.com spread proxies where available."
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_treasury_curve_screen_report(
        historical_rows,
        recent_rows,
        historical_trade_map,
        historical_summary_path,
        recent_summary_path,
        status_path,
        cells,
        curve_summary,
        gates,
    )
    (p.reports / f"FOREX_TREASURY_CURVE_SCREEN_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_cny_pressure_screen(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    cny = load_cny_pressure_context(p)
    specs = candidate_specs_cny_pressure(cny)
    historical_rows, historical_trades = run_specs_screen(p, cells, specs)
    recent_rows, recent_trades = run_recent_proxy_stress_for_specs(p, cells, specs)
    return historical_rows, historical_trades, recent_rows, recent_trades, cny_pressure_context_summary(p, cny)


def write_cny_pressure_screen_outputs(
    p: Paths,
    historical_rows: list[dict[str, Any]],
    historical_trade_map: dict[str, list[dict[str, Any]]],
    recent_rows: list[dict[str, Any]],
    recent_trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    cny_summary: dict[str, Any],
) -> dict[str, str]:
    historical_summary_path = p.tables / f"FOREX_CNY_DOLLAR_PRESSURE_SCREEN_SUMMARY_{RUN_DATE}.csv"
    recent_summary_path = p.tables / f"FOREX_CNY_DOLLAR_PRESSURE_RECENT_PROXY_SUMMARY_{RUN_DATE}.csv"
    if historical_rows:
        with historical_summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(historical_rows[0].keys()))
            writer.writeheader()
            for row in historical_rows:
                writer.writerow(format_summary_row(row))
    if recent_rows:
        with recent_summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(recent_rows[0].keys()))
            writer.writeheader()
            for row in recent_rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in historical_trade_map.items():
        path = p.tables / f"{candidate_id}_CNY_DOLLAR_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    for candidate_id, trades in recent_trade_map.items():
        path = p.tables / f"{candidate_id}_CNY_DOLLAR_RECENT_PROXY_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = cny_pressure_gates(historical_rows, recent_rows)
    status_path = p.reports / f"FOREX_CNY_DOLLAR_PRESSURE_SCREEN_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "CNY_DOLLAR_PRESSURE_RESEARCH_ONLY",
                "runtime_touched": False,
                "cny_context": cny_summary,
                "final_gates": gates,
                "historical_overall": [format_summary_row(row) for row in historical_rows if row.get("level") == "overall"],
                "recent_proxy": [format_summary_row(row) for row in recent_rows],
                "caveat": "CNY and broad-dollar public FRED data is lagged one day and is not broker-authoritative Forex evidence.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_cny_pressure_screen_report(
        historical_rows,
        recent_rows,
        historical_trade_map,
        historical_summary_path,
        recent_summary_path,
        status_path,
        cells,
        cny_summary,
        gates,
    )
    (p.reports / f"FOREX_CNY_DOLLAR_PRESSURE_SCREEN_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_calendar_session_screen(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    specs = candidate_specs_calendar_session()
    historical_rows, historical_trades = run_specs_screen(p, cells, specs)
    recent_rows, recent_trades = run_recent_proxy_stress_for_specs(p, cells, specs)
    return historical_rows, historical_trades, recent_rows, recent_trades


def write_calendar_session_screen_outputs(
    p: Paths,
    historical_rows: list[dict[str, Any]],
    historical_trade_map: dict[str, list[dict[str, Any]]],
    recent_rows: list[dict[str, Any]],
    recent_trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
) -> dict[str, str]:
    historical_summary_path = p.tables / f"FOREX_CALENDAR_SESSION_SCREEN_SUMMARY_{RUN_DATE}.csv"
    recent_summary_path = p.tables / f"FOREX_CALENDAR_SESSION_RECENT_PROXY_SUMMARY_{RUN_DATE}.csv"
    if historical_rows:
        with historical_summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(historical_rows[0].keys()))
            writer.writeheader()
            for row in historical_rows:
                writer.writerow(format_summary_row(row))
    if recent_rows:
        with recent_summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(recent_rows[0].keys()))
            writer.writeheader()
            for row in recent_rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in historical_trade_map.items():
        path = p.tables / f"{candidate_id}_CALENDAR_SESSION_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    for candidate_id, trades in recent_trade_map.items():
        path = p.tables / f"{candidate_id}_CALENDAR_SESSION_RECENT_PROXY_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = calendar_session_gates(historical_rows, recent_rows)
    status_path = p.reports / f"FOREX_CALENDAR_SESSION_SCREEN_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "CALENDAR_SESSION_RESEARCH_ONLY",
                "runtime_touched": False,
                "final_gates": gates,
                "historical_overall": [format_summary_row(row) for row in historical_rows if row.get("level") == "overall"],
                "recent_proxy": [format_summary_row(row) for row in recent_rows],
                "caveat": "Calendar/session price-only evidence can be recent-stressed on public Yahoo proxy bars, but broker-authoritative 2026 data is still required before any demo-forward step.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_calendar_session_screen_report(
        historical_rows,
        recent_rows,
        historical_trade_map,
        historical_summary_path,
        recent_summary_path,
        status_path,
        cells,
        gates,
    )
    (p.reports / f"FOREX_CALENDAR_SESSION_SCREEN_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_weekly_structure_screen(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    specs = candidate_specs_weekly_structure()
    historical_rows, historical_trades = run_specs_screen(p, cells, specs)
    recent_rows, recent_trades = run_recent_proxy_stress_for_specs(p, cells, specs)
    return historical_rows, historical_trades, recent_rows, recent_trades


def write_weekly_structure_screen_outputs(
    p: Paths,
    historical_rows: list[dict[str, Any]],
    historical_trade_map: dict[str, list[dict[str, Any]]],
    recent_rows: list[dict[str, Any]],
    recent_trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
) -> dict[str, str]:
    historical_summary_path = p.tables / f"FOREX_WEEKLY_STRUCTURE_SCREEN_SUMMARY_{RUN_DATE}.csv"
    recent_summary_path = p.tables / f"FOREX_WEEKLY_STRUCTURE_RECENT_PROXY_SUMMARY_{RUN_DATE}.csv"
    if historical_rows:
        with historical_summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(historical_rows[0].keys()))
            writer.writeheader()
            for row in historical_rows:
                writer.writerow(format_summary_row(row))
    if recent_rows:
        with recent_summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(recent_rows[0].keys()))
            writer.writeheader()
            for row in recent_rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in historical_trade_map.items():
        path = p.tables / f"{candidate_id}_WEEKLY_STRUCTURE_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    for candidate_id, trades in recent_trade_map.items():
        path = p.tables / f"{candidate_id}_WEEKLY_STRUCTURE_RECENT_PROXY_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = weekly_structure_gates(historical_rows, recent_rows)
    status_path = p.reports / f"FOREX_WEEKLY_STRUCTURE_SCREEN_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "WEEKLY_STRUCTURE_RESEARCH_ONLY",
                "runtime_touched": False,
                "final_gates": gates,
                "historical_overall": [format_summary_row(row) for row in historical_rows if row.get("level") == "overall"],
                "recent_proxy": [format_summary_row(row) for row in recent_rows],
                "caveat": "Weekly price-structure evidence can be recent-stressed on public Yahoo proxy bars, but broker-authoritative 2026 data is still required before any demo-forward step.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_weekly_structure_screen_report(
        historical_rows,
        recent_rows,
        historical_trade_map,
        historical_summary_path,
        recent_summary_path,
        status_path,
        cells,
        gates,
    )
    (p.reports / f"FOREX_WEEKLY_STRUCTURE_SCREEN_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_financial_liquidity_screen(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    financial_context = load_financial_liquidity_context(p)
    specs = candidate_specs_financial_liquidity(financial_context)
    historical_rows, historical_trades = run_specs_screen(p, cells, specs)
    recent_rows, recent_trades = run_recent_proxy_stress_for_specs(p, cells, specs)
    return historical_rows, historical_trades, recent_rows, recent_trades, financial_liquidity_context_summary(p, financial_context)


def write_financial_liquidity_screen_outputs(
    p: Paths,
    historical_rows: list[dict[str, Any]],
    historical_trade_map: dict[str, list[dict[str, Any]]],
    recent_rows: list[dict[str, Any]],
    recent_trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    financial_summary: dict[str, Any],
) -> dict[str, str]:
    historical_summary_path = p.tables / f"FOREX_FINANCIAL_LIQUIDITY_SCREEN_SUMMARY_{RUN_DATE}.csv"
    recent_summary_path = p.tables / f"FOREX_FINANCIAL_LIQUIDITY_RECENT_PROXY_SUMMARY_{RUN_DATE}.csv"
    if historical_rows:
        with historical_summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(historical_rows[0].keys()))
            writer.writeheader()
            for row in historical_rows:
                writer.writerow(format_summary_row(row))
    if recent_rows:
        with recent_summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(recent_rows[0].keys()))
            writer.writeheader()
            for row in recent_rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in historical_trade_map.items():
        path = p.tables / f"{candidate_id}_FINANCIAL_LIQUIDITY_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    for candidate_id, trades in recent_trade_map.items():
        path = p.tables / f"{candidate_id}_FINANCIAL_LIQUIDITY_RECENT_PROXY_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = financial_liquidity_gates(historical_rows, recent_rows)
    status_path = p.reports / f"FOREX_FINANCIAL_LIQUIDITY_SCREEN_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "FINANCIAL_LIQUIDITY_RESEARCH_ONLY",
                "runtime_touched": False,
                "financial_liquidity_context": financial_summary,
                "final_gates": gates,
                "historical_overall": [
                    format_summary_row(row) for row in historical_rows if row.get("level") == "overall"
                ],
                "recent_proxy": [format_summary_row(row) for row in recent_rows],
                "caveat": (
                    "FRED financial/liquidity context is public macro data, not broker-authoritative FX evidence. "
                    "Recent stress uses Yahoo FX proxy bars with historical Capital.com spread proxies where available."
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_financial_liquidity_screen_report(
        historical_rows,
        recent_rows,
        historical_trade_map,
        historical_summary_path,
        recent_summary_path,
        status_path,
        cells,
        financial_summary,
        gates,
    )
    (p.reports / f"FOREX_FINANCIAL_LIQUIDITY_SCREEN_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_cot_positioning_screen(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    cot_context = load_cot_financial_context(p)
    specs = candidate_specs_cot_positioning(cot_context)
    historical_rows, historical_trades = run_specs_screen(p, cells, specs)
    recent_rows, recent_trades = run_recent_proxy_stress_for_specs(p, cells, specs)
    return historical_rows, historical_trades, recent_rows, recent_trades, cot_financial_context_summary(p, cot_context)


def write_cot_positioning_screen_outputs(
    p: Paths,
    historical_rows: list[dict[str, Any]],
    historical_trade_map: dict[str, list[dict[str, Any]]],
    recent_rows: list[dict[str, Any]],
    recent_trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    cot_summary: dict[str, Any],
) -> dict[str, str]:
    historical_summary_path = p.tables / f"FOREX_COT_POSITIONING_SCREEN_SUMMARY_{RUN_DATE}.csv"
    recent_summary_path = p.tables / f"FOREX_COT_POSITIONING_RECENT_PROXY_SUMMARY_{RUN_DATE}.csv"
    if historical_rows:
        with historical_summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(historical_rows[0].keys()))
            writer.writeheader()
            for row in historical_rows:
                writer.writerow(format_summary_row(row))
    if recent_rows:
        with recent_summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(recent_rows[0].keys()))
            writer.writeheader()
            for row in recent_rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in historical_trade_map.items():
        path = p.tables / f"{candidate_id}_COT_POSITIONING_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    for candidate_id, trades in recent_trade_map.items():
        path = p.tables / f"{candidate_id}_COT_POSITIONING_RECENT_PROXY_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = cot_positioning_gates(historical_rows, recent_rows)
    status_path = p.reports / f"FOREX_COT_POSITIONING_SCREEN_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "COT_POSITIONING_RESEARCH_ONLY",
                "runtime_touched": False,
                "cot_context": cot_summary,
                "final_gates": gates,
                "historical_overall": [
                    format_summary_row(row) for row in historical_rows if row.get("level") == "overall"
                ],
                "recent_proxy": [format_summary_row(row) for row in recent_rows],
                "caveat": (
                    "CFTC COT financial futures data is weekly and delayed; recent stress still uses public Yahoo FX "
                    "proxy bars with historical Capital.com spread proxies. This cannot authorize a Forex EA."
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_cot_positioning_screen_report(
        historical_rows,
        recent_rows,
        historical_trade_map,
        historical_summary_path,
        recent_summary_path,
        status_path,
        cells,
        cot_summary,
        gates,
    )
    (p.reports / f"FOREX_COT_POSITIONING_SCREEN_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_global_risk_screen(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    global_risk = load_global_risk_context(p)
    specs = candidate_specs_global_risk(global_risk)
    rows, trades = run_specs_screen(p, cells, specs)
    return rows, trades, global_risk_context_summary(p, global_risk)


def write_global_risk_screen_outputs(
    p: Paths,
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    global_summary: dict[str, Any],
) -> dict[str, str]:
    summary_path = p.tables / f"FOREX_GLOBAL_RISK_CREDIT_SCREEN_SUMMARY_{RUN_DATE}.csv"
    if rows:
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in trade_map.items():
        path = p.tables / f"{candidate_id}_GLOBAL_RISK_CREDIT_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = global_risk_gates(rows)
    status_path = p.reports / f"FOREX_GLOBAL_RISK_CREDIT_SCREEN_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "GLOBAL_RISK_CREDIT_RESEARCH_ONLY",
                "runtime_touched": False,
                "global_risk_context": global_summary,
                "final_gates": gates,
                "historical_overall": [format_summary_row(row) for row in rows if row.get("level") == "overall"],
                "caveat": "EEM/SPY and HYG/IEF ETF proxy data ends in 2025-06 and is public intermarket evidence, not broker-authoritative 2026 confirmation.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_global_risk_screen_report(rows, trade_map, summary_path, status_path, cells, global_summary, gates)
    (p.reports / f"FOREX_GLOBAL_RISK_CREDIT_SCREEN_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_commodity_dollar_screen(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    commodity_context = load_commodity_dollar_context(p)
    specs = candidate_specs_commodity_dollar(commodity_context)
    rows, trades = run_specs_screen(p, cells, specs)
    return rows, trades, commodity_dollar_context_summary(p, commodity_context)


def write_commodity_dollar_screen_outputs(
    p: Paths,
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    commodity_summary: dict[str, Any],
) -> dict[str, str]:
    summary_path = p.tables / f"FOREX_COMMODITY_DOLLAR_SCREEN_SUMMARY_{RUN_DATE}.csv"
    if rows:
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in trade_map.items():
        path = p.tables / f"{candidate_id}_COMMODITY_DOLLAR_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = commodity_dollar_gates(rows)
    status_path = p.reports / f"FOREX_COMMODITY_DOLLAR_SCREEN_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "COMMODITY_DOLLAR_RESEARCH_ONLY",
                "runtime_touched": False,
                "commodity_context": commodity_summary,
                "final_gates": gates,
                "historical_overall": [format_summary_row(row) for row in rows if row.get("level") == "overall"],
                "caveat": "DBC/UUP and DBB/UUP ETF proxy data ends in 2025-06 and is public intermarket evidence, not broker-authoritative 2026 confirmation.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_commodity_dollar_screen_report(rows, trade_map, summary_path, status_path, cells, commodity_summary, gates)
    (p.reports / f"FOREX_COMMODITY_DOLLAR_SCREEN_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_real_asset_rotation_screen(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    real_asset_context = load_real_asset_rotation_context(p)
    specs = candidate_specs_real_asset_rotation(real_asset_context)
    rows, trades = run_specs_screen(p, cells, specs)
    return rows, trades, real_asset_rotation_context_summary(p, real_asset_context)


def write_real_asset_rotation_screen_outputs(
    p: Paths,
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    real_asset_summary: dict[str, Any],
) -> dict[str, str]:
    summary_path = p.tables / f"FOREX_REAL_ASSET_ROTATION_SCREEN_SUMMARY_{RUN_DATE}.csv"
    if rows:
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in trade_map.items():
        path = p.tables / f"{candidate_id}_REAL_ASSET_ROTATION_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = real_asset_rotation_gates(rows)
    status_path = p.reports / f"FOREX_REAL_ASSET_ROTATION_SCREEN_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "REAL_ASSET_ROTATION_RESEARCH_ONLY",
                "runtime_touched": False,
                "real_asset_context": real_asset_summary,
                "final_gates": gates,
                "historical_overall": [format_summary_row(row) for row in rows if row.get("level") == "overall"],
                "caveat": "USO/UUP, HG/GC, and SLV/GLD proxy data ends in 2025-06 and is public intermarket evidence, not broker-authoritative 2026 confirmation.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_real_asset_rotation_screen_report(rows, trade_map, summary_path, status_path, cells, real_asset_summary, gates)
    (p.reports / f"FOREX_REAL_ASSET_ROTATION_SCREEN_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_haven_liquidity_screen(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    haven_context = load_haven_liquidity_context(p)
    specs = candidate_specs_haven_liquidity(haven_context)
    rows, trades = run_specs_screen(p, cells, specs)
    return rows, trades, haven_liquidity_context_summary(p, haven_context)


def write_haven_liquidity_screen_outputs(
    p: Paths,
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    haven_summary: dict[str, Any],
) -> dict[str, str]:
    summary_path = p.tables / f"FOREX_HAVEN_LIQUIDITY_SCREEN_SUMMARY_{RUN_DATE}.csv"
    if rows:
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in trade_map.items():
        path = p.tables / f"{candidate_id}_HAVEN_LIQUIDITY_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = haven_liquidity_gates(rows)
    status_path = p.reports / f"FOREX_HAVEN_LIQUIDITY_SCREEN_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "HAVEN_LIQUIDITY_RESEARCH_ONLY",
                "runtime_touched": False,
                "haven_liquidity_context": haven_summary,
                "final_gates": gates,
                "historical_overall": [format_summary_row(row) for row in rows if row.get("level") == "overall"],
                "caveat": "GLD, GDX/GLD, SPY/TLT, and XLU/XLK proxy data ends in 2025-06 and is public intermarket evidence, not broker-authoritative 2026 confirmation.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_haven_liquidity_screen_report(rows, trade_map, summary_path, status_path, cells, haven_summary, gates)
    (p.reports / f"FOREX_HAVEN_LIQUIDITY_SCREEN_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_recent_haven_liquidity_stress(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    haven_context = load_recent_haven_liquidity_context(p)
    specs = candidate_specs_haven_liquidity(haven_context)
    rows, trades = run_recent_proxy_stress_for_specs(p, cells, specs)
    return rows, trades, haven_liquidity_context_summary(p, haven_context, recent_haven_liquidity_proxy_root(p))


def write_recent_haven_liquidity_stress_outputs(
    p: Paths,
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    haven_summary: dict[str, Any],
) -> dict[str, str]:
    summary_path = p.tables / f"FOREX_HAVEN_LIQUIDITY_RECENT_STRESS_SUMMARY_{RUN_DATE}.csv"
    if rows:
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in trade_map.items():
        path = p.tables / f"{candidate_id}_HAVEN_LIQUIDITY_RECENT_STRESS_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = {row["candidate_id"]: recent_proxy_gate(row) for row in rows}
    status_path = p.reports / f"FOREX_HAVEN_LIQUIDITY_RECENT_STRESS_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "HAVEN_LIQUIDITY_RECENT_STRESS_RESEARCH_ONLY",
                "runtime_touched": False,
                "haven_liquidity_context": haven_summary,
                "final_gates": gates,
                "recent_proxy": [format_summary_row(row) for row in rows],
                "caveat": "Recent stress uses public Yahoo ETF and FX proxy bars plus historical Capital.com spread proxies; it is not broker-authoritative.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_recent_haven_liquidity_stress_report(rows, trade_map, summary_path, status_path, cells, haven_summary, gates)
    (p.reports / f"FOREX_HAVEN_LIQUIDITY_RECENT_STRESS_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_rates_dollar_screen(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    rates_context = load_rates_dollar_context(p)
    specs = candidate_specs_rates_dollar(rates_context)
    rows, trades = run_specs_screen(p, cells, specs)
    return rows, trades, rates_dollar_context_summary(p, rates_context)


def write_rates_dollar_screen_outputs(
    p: Paths,
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    rates_summary: dict[str, Any],
) -> dict[str, str]:
    summary_path = p.tables / f"FOREX_RATES_DOLLAR_SCREEN_SUMMARY_{RUN_DATE}.csv"
    if rows:
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in trade_map.items():
        path = p.tables / f"{candidate_id}_RATES_DOLLAR_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = rates_dollar_gates(rows)
    status_path = p.reports / f"FOREX_RATES_DOLLAR_SCREEN_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "RATES_DOLLAR_RESEARCH_ONLY",
                "runtime_touched": False,
                "rates_context": rates_summary,
                "final_gates": gates,
                "historical_overall": [format_summary_row(row) for row in rows if row.get("level") == "overall"],
                "caveat": "TLT/UUP and TLT/SHY ETF proxy data ends in 2025-06 and is public intermarket evidence, not broker-authoritative 2026 confirmation.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_rates_dollar_screen_report(rows, trade_map, summary_path, status_path, cells, rates_summary, gates)
    (p.reports / f"FOREX_RATES_DOLLAR_SCREEN_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_recent_rates_dollar_stress(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    rates_context = load_recent_rates_dollar_context(p)
    specs = candidate_specs_rates_dollar(rates_context)
    rows, trades = run_recent_proxy_stress_for_specs(p, cells, specs)
    return rows, trades, rates_dollar_context_summary(p, rates_context, recent_rates_proxy_root(p))


def write_recent_rates_dollar_stress_outputs(
    p: Paths,
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    rates_summary: dict[str, Any],
) -> dict[str, str]:
    summary_path = p.tables / f"FOREX_RATES_DOLLAR_RECENT_STRESS_SUMMARY_{RUN_DATE}.csv"
    if rows:
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in trade_map.items():
        path = p.tables / f"{candidate_id}_RATES_DOLLAR_RECENT_STRESS_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = {row["candidate_id"]: recent_proxy_gate(row) for row in rows}
    status_path = p.reports / f"FOREX_RATES_DOLLAR_RECENT_STRESS_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "RATES_DOLLAR_RECENT_STRESS_RESEARCH_ONLY",
                "runtime_touched": False,
                "rates_context": rates_summary,
                "final_gates": gates,
                "recent_proxy": [format_summary_row(row) for row in rows],
                "caveat": "Recent stress uses public Yahoo ETF and FX proxy bars plus historical Capital.com spread proxies; it is not broker-authoritative.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_recent_rates_dollar_stress_report(rows, trade_map, summary_path, status_path, cells, rates_summary, gates)
    (p.reports / f"FOREX_RATES_DOLLAR_RECENT_STRESS_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_equity_leadership_screen(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    equity_context = load_equity_leadership_context(p)
    specs = candidate_specs_equity_leadership(equity_context)
    rows, trades = run_specs_screen(p, cells, specs)
    return rows, trades, equity_leadership_context_summary(p, equity_context)


def write_equity_leadership_screen_outputs(
    p: Paths,
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    equity_summary: dict[str, Any],
) -> dict[str, str]:
    summary_path = p.tables / f"FOREX_EQUITY_LEADERSHIP_SCREEN_SUMMARY_{RUN_DATE}.csv"
    if rows:
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in trade_map.items():
        path = p.tables / f"{candidate_id}_EQUITY_LEADERSHIP_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = equity_leadership_gates(rows)
    status_path = p.reports / f"FOREX_EQUITY_LEADERSHIP_SCREEN_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "EQUITY_LEADERSHIP_RESEARCH_ONLY",
                "runtime_touched": False,
                "equity_leadership_context": equity_summary,
                "final_gates": gates,
                "historical_overall": [format_summary_row(row) for row in rows if row.get("level") == "overall"],
                "caveat": "ACWX/SPY, IWM/SPY, and XLF/XLU ETF proxy data ends in 2025-06 and is public intermarket evidence, not broker-authoritative 2026 confirmation.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_equity_leadership_screen_report(rows, trade_map, summary_path, status_path, cells, equity_summary, gates)
    (p.reports / f"FOREX_EQUITY_LEADERSHIP_SCREEN_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_recent_equity_leadership_stress(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    equity_context = load_recent_equity_leadership_context(p)
    specs = candidate_specs_equity_leadership(equity_context)
    rows, trades = run_recent_proxy_stress_for_specs(p, cells, specs)
    return rows, trades, equity_leadership_context_summary(p, equity_context, recent_equity_leadership_proxy_root(p))


def write_recent_equity_leadership_stress_outputs(
    p: Paths,
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    equity_summary: dict[str, Any],
) -> dict[str, str]:
    summary_path = p.tables / f"FOREX_EQUITY_LEADERSHIP_RECENT_STRESS_SUMMARY_{RUN_DATE}.csv"
    if rows:
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in trade_map.items():
        path = p.tables / f"{candidate_id}_EQUITY_LEADERSHIP_RECENT_STRESS_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = {row["candidate_id"]: recent_proxy_gate(row) for row in rows}
    status_path = p.reports / f"FOREX_EQUITY_LEADERSHIP_RECENT_STRESS_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "EQUITY_LEADERSHIP_RECENT_STRESS_RESEARCH_ONLY",
                "runtime_touched": False,
                "equity_leadership_context": equity_summary,
                "final_gates": gates,
                "recent_proxy": [format_summary_row(row) for row in rows],
                "caveat": "Recent stress uses public Yahoo ETF and FX proxy bars plus historical Capital.com spread proxies; it is not broker-authoritative.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_recent_equity_leadership_stress_report(rows, trade_map, summary_path, status_path, cells, equity_summary, gates)
    (p.reports / f"FOREX_EQUITY_LEADERSHIP_RECENT_STRESS_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_sector_rotation_screen(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    sector_context = load_sector_rotation_context(p)
    specs = candidate_specs_sector_rotation(sector_context)
    rows, trades = run_specs_screen(p, cells, specs)
    return rows, trades, sector_rotation_context_summary(p, sector_context)


def write_sector_rotation_screen_outputs(
    p: Paths,
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    sector_summary: dict[str, Any],
) -> dict[str, str]:
    summary_path = p.tables / f"FOREX_SECTOR_ROTATION_SCREEN_SUMMARY_{RUN_DATE}.csv"
    if rows:
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in trade_map.items():
        path = p.tables / f"{candidate_id}_SECTOR_ROTATION_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = sector_rotation_gates(rows)
    status_path = p.reports / f"FOREX_SECTOR_ROTATION_SCREEN_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "SECTOR_ROTATION_RESEARCH_ONLY",
                "runtime_touched": False,
                "sector_rotation_context": sector_summary,
                "final_gates": gates,
                "historical_overall": [format_summary_row(row) for row in rows if row.get("level") == "overall"],
                "caveat": "Sector ETF proxy data ends in 2025-06 and is public intermarket evidence, not broker-authoritative 2026 confirmation.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_sector_rotation_screen_report(rows, trade_map, summary_path, status_path, cells, sector_summary, gates)
    (p.reports / f"FOREX_SECTOR_ROTATION_SCREEN_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_recent_sector_rotation_stress(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    sector_context = load_recent_sector_rotation_context(p)
    specs = candidate_specs_sector_rotation(sector_context)
    rows, trades = run_recent_proxy_stress_for_specs(p, cells, specs)
    return rows, trades, sector_rotation_context_summary(p, sector_context, recent_sector_rotation_proxy_root(p))


def write_recent_sector_rotation_stress_outputs(
    p: Paths,
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    sector_summary: dict[str, Any],
) -> dict[str, str]:
    summary_path = p.tables / f"FOREX_SECTOR_ROTATION_RECENT_STRESS_SUMMARY_{RUN_DATE}.csv"
    if rows:
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in trade_map.items():
        path = p.tables / f"{candidate_id}_SECTOR_ROTATION_RECENT_STRESS_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = {row["candidate_id"]: recent_proxy_gate(row) for row in rows}
    status_path = p.reports / f"FOREX_SECTOR_ROTATION_RECENT_STRESS_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "SECTOR_ROTATION_RECENT_STRESS_RESEARCH_ONLY",
                "runtime_touched": False,
                "sector_rotation_context": sector_summary,
                "final_gates": gates,
                "recent_proxy": [format_summary_row(row) for row in rows],
                "caveat": "Recent stress uses public Yahoo ETF and FX proxy bars plus historical Capital.com spread proxies; it is not broker-authoritative.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_recent_sector_rotation_stress_report(rows, trade_map, summary_path, status_path, cells, sector_summary, gates)
    (p.reports / f"FOREX_SECTOR_ROTATION_RECENT_STRESS_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_currency_basket_screen(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    currency_context = load_currency_basket_context(p)
    specs = candidate_specs_currency_basket(currency_context)
    rows, trades = run_specs_screen(p, cells, specs)
    return rows, trades, currency_basket_context_summary(p, currency_context)


def write_currency_basket_screen_outputs(
    p: Paths,
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    currency_summary: dict[str, Any],
) -> dict[str, str]:
    summary_path = p.tables / f"FOREX_CURRENCY_BASKET_SCREEN_SUMMARY_{RUN_DATE}.csv"
    if rows:
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in trade_map.items():
        path = p.tables / f"{candidate_id}_CURRENCY_BASKET_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = currency_basket_gates(rows)
    status_path = p.reports / f"FOREX_CURRENCY_BASKET_SCREEN_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "CURRENCY_BASKET_RESEARCH_ONLY",
                "runtime_touched": False,
                "currency_basket_context": currency_summary,
                "final_gates": gates,
                "historical_overall": [format_summary_row(row) for row in rows if row.get("level") == "overall"],
                "caveat": "Currency ETF proxy data ends in 2025-06 and is public intermarket evidence, not broker-authoritative 2026 confirmation.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_currency_basket_screen_report(rows, trade_map, summary_path, status_path, cells, currency_summary, gates)
    (p.reports / f"FOREX_CURRENCY_BASKET_SCREEN_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_recent_currency_basket_stress(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    currency_context = load_recent_currency_basket_context(p)
    specs = candidate_specs_recent_currency_basket(currency_context)
    rows, trades = run_recent_proxy_stress_for_specs(p, cells, specs)
    return rows, trades, currency_basket_context_summary(p, currency_context, recent_currency_basket_proxy_root(p))


def write_recent_currency_basket_stress_outputs(
    p: Paths,
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    currency_summary: dict[str, Any],
) -> dict[str, str]:
    summary_path = p.tables / f"FOREX_CURRENCY_BASKET_RECENT_STRESS_SUMMARY_{RUN_DATE}.csv"
    if rows:
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in trade_map.items():
        path = p.tables / f"{candidate_id}_CURRENCY_BASKET_RECENT_STRESS_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = {row["candidate_id"]: recent_proxy_gate(row) for row in rows}
    status_path = p.reports / f"FOREX_CURRENCY_BASKET_RECENT_STRESS_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "CURRENCY_BASKET_RECENT_STRESS_RESEARCH_ONLY",
                "runtime_touched": False,
                "currency_basket_context": currency_summary,
                "final_gates": gates,
                "recent_proxy": [format_summary_row(row) for row in rows],
                "caveat": "Recent stress uses public Yahoo currency ETF and FX proxy bars plus historical Capital.com spread proxies; it is not broker-authoritative.",
                "availability_note": "Recent Yahoo CYB returned no usable daily rows during acquisition, so recent stress includes only candidates whose required currency-basket context columns exist.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_recent_currency_basket_stress_report(rows, trade_map, summary_path, status_path, cells, currency_summary, gates)
    (p.reports / f"FOREX_CURRENCY_BASKET_RECENT_STRESS_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_bond_vol_screen(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    bond_vol_context = load_bond_vol_context(p)
    specs = candidate_specs_bond_vol(bond_vol_context)
    rows, trades = run_specs_screen(p, cells, specs)
    return rows, trades, bond_vol_context_summary(p, bond_vol_context)


def write_bond_vol_screen_outputs(
    p: Paths,
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    bond_vol_summary: dict[str, Any],
) -> dict[str, str]:
    summary_path = p.tables / f"FOREX_BOND_VOL_SCREEN_SUMMARY_{RUN_DATE}.csv"
    if rows:
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in trade_map.items():
        path = p.tables / f"{candidate_id}_BOND_VOL_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = bond_vol_gates(rows)
    status_path = p.reports / f"FOREX_BOND_VOL_SCREEN_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "BOND_VOL_RESEARCH_ONLY",
                "runtime_touched": False,
                "bond_vol_context": bond_vol_summary,
                "final_gates": gates,
                "historical_overall": [format_summary_row(row) for row in rows if row.get("level") == "overall"],
                "caveat": "MOVE bond-volatility proxy data ends in 2025-06 and is public intermarket evidence, not broker-authoritative 2026 confirmation.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_bond_vol_screen_report(rows, trade_map, summary_path, status_path, cells, bond_vol_summary, gates)
    (p.reports / f"FOREX_BOND_VOL_SCREEN_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_recent_bond_vol_stress(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    bond_vol_context = load_recent_bond_vol_context(p)
    specs = candidate_specs_bond_vol(bond_vol_context)
    rows, trades = run_recent_proxy_stress_for_specs(p, cells, specs)
    return rows, trades, bond_vol_context_summary(p, bond_vol_context, recent_bond_vol_proxy_root(p))


def write_recent_bond_vol_stress_outputs(
    p: Paths,
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    bond_vol_summary: dict[str, Any],
) -> dict[str, str]:
    summary_path = p.tables / f"FOREX_BOND_VOL_RECENT_STRESS_SUMMARY_{RUN_DATE}.csv"
    if rows:
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in trade_map.items():
        path = p.tables / f"{candidate_id}_BOND_VOL_RECENT_STRESS_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = {row["candidate_id"]: recent_proxy_gate(row) for row in rows}
    status_path = p.reports / f"FOREX_BOND_VOL_RECENT_STRESS_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "BOND_VOL_RECENT_STRESS_RESEARCH_ONLY",
                "runtime_touched": False,
                "bond_vol_context": bond_vol_summary,
                "final_gates": gates,
                "recent_proxy": [format_summary_row(row) for row in rows],
                "caveat": "Recent stress uses public Yahoo MOVE and FX proxy bars plus historical Capital.com spread proxies; it is not broker-authoritative.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_recent_bond_vol_stress_report(rows, trade_map, summary_path, status_path, cells, bond_vol_summary, gates)
    (p.reports / f"FOREX_BOND_VOL_RECENT_STRESS_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_crypto_risk_screen(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    crypto_context = load_crypto_risk_context(p)
    specs = candidate_specs_crypto_risk(crypto_context)
    rows, trades = run_specs_screen(p, cells, specs)
    return rows, trades, crypto_risk_context_summary(p, crypto_context)


def write_crypto_risk_screen_outputs(
    p: Paths,
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    crypto_summary: dict[str, Any],
) -> dict[str, str]:
    summary_path = p.tables / f"FOREX_CRYPTO_RISK_SCREEN_SUMMARY_{RUN_DATE}.csv"
    if rows:
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in trade_map.items():
        path = p.tables / f"{candidate_id}_CRYPTO_RISK_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = crypto_risk_gates(rows)
    status_path = p.reports / f"FOREX_CRYPTO_RISK_SCREEN_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "CRYPTO_RISK_RESEARCH_ONLY",
                "runtime_touched": False,
                "crypto_context": crypto_summary,
                "final_gates": gates,
                "historical_overall": [format_summary_row(row) for row in rows if row.get("level") == "overall"],
                "caveat": "BTC-USD crypto-risk proxy data ends around 2025-07 and is public intermarket evidence, not broker-authoritative 2026 confirmation.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_crypto_risk_screen_report(rows, trade_map, summary_path, status_path, cells, crypto_summary, gates)
    (p.reports / f"FOREX_CRYPTO_RISK_SCREEN_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_recent_crypto_risk_stress(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    crypto_context = load_recent_crypto_risk_context(p)
    specs = candidate_specs_crypto_risk(crypto_context)
    rows, trades = run_recent_proxy_stress_for_specs(p, cells, specs)
    return rows, trades, crypto_risk_context_summary(p, crypto_context, recent_crypto_risk_proxy_root(p))


def write_recent_crypto_risk_stress_outputs(
    p: Paths,
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    crypto_summary: dict[str, Any],
) -> dict[str, str]:
    summary_path = p.tables / f"FOREX_CRYPTO_RISK_RECENT_STRESS_SUMMARY_{RUN_DATE}.csv"
    if rows:
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in trade_map.items():
        path = p.tables / f"{candidate_id}_CRYPTO_RISK_RECENT_STRESS_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = {row["candidate_id"]: recent_proxy_gate(row) for row in rows}
    status_path = p.reports / f"FOREX_CRYPTO_RISK_RECENT_STRESS_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "CRYPTO_RISK_RECENT_STRESS_RESEARCH_ONLY",
                "runtime_touched": False,
                "crypto_context": crypto_summary,
                "final_gates": gates,
                "recent_proxy": [format_summary_row(row) for row in rows],
                "caveat": "Recent stress uses public Yahoo BTC and FX proxy bars plus historical Capital.com spread proxies; it is not broker-authoritative.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_recent_crypto_risk_stress_report(rows, trade_map, summary_path, status_path, cells, crypto_summary, gates)
    (p.reports / f"FOREX_CRYPTO_RISK_RECENT_STRESS_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_recent_commodity_dollar_stress(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    commodity_context = load_recent_commodity_dollar_context(p)
    specs = candidate_specs_commodity_dollar(commodity_context)
    rows, trades = run_recent_proxy_stress_for_specs(p, cells, specs)
    return rows, trades, commodity_dollar_context_summary(p, commodity_context, recent_commodity_proxy_root(p))


def write_recent_commodity_dollar_stress_outputs(
    p: Paths,
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    commodity_summary: dict[str, Any],
) -> dict[str, str]:
    summary_path = p.tables / f"FOREX_COMMODITY_DOLLAR_RECENT_STRESS_SUMMARY_{RUN_DATE}.csv"
    if rows:
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in trade_map.items():
        path = p.tables / f"{candidate_id}_COMMODITY_DOLLAR_RECENT_STRESS_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = {row["candidate_id"]: recent_proxy_gate(row) for row in rows}
    status_path = p.reports / f"FOREX_COMMODITY_DOLLAR_RECENT_STRESS_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "COMMODITY_DOLLAR_RECENT_STRESS_RESEARCH_ONLY",
                "runtime_touched": False,
                "commodity_context": commodity_summary,
                "final_gates": gates,
                "recent_proxy": [format_summary_row(row) for row in rows],
                "caveat": "Recent stress uses public Yahoo ETF and FX proxy bars plus historical Capital.com spread proxies; it is not broker-authoritative.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_recent_commodity_dollar_stress_report(rows, trade_map, summary_path, status_path, cells, commodity_summary, gates)
    (p.reports / f"FOREX_COMMODITY_DOLLAR_RECENT_STRESS_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_recent_real_asset_rotation_stress(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    real_asset_context = load_recent_real_asset_rotation_context(p)
    specs = candidate_specs_real_asset_rotation(real_asset_context)
    rows, trades = run_recent_proxy_stress_for_specs(p, cells, specs)
    return rows, trades, real_asset_rotation_context_summary(p, real_asset_context, recent_real_asset_rotation_proxy_root(p))


def write_recent_real_asset_rotation_stress_outputs(
    p: Paths,
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    real_asset_summary: dict[str, Any],
) -> dict[str, str]:
    summary_path = p.tables / f"FOREX_REAL_ASSET_ROTATION_RECENT_STRESS_SUMMARY_{RUN_DATE}.csv"
    if rows:
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in trade_map.items():
        path = p.tables / f"{candidate_id}_REAL_ASSET_ROTATION_RECENT_STRESS_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = {row["candidate_id"]: recent_proxy_gate(row) for row in rows}
    status_path = p.reports / f"FOREX_REAL_ASSET_ROTATION_RECENT_STRESS_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "REAL_ASSET_ROTATION_RECENT_STRESS_RESEARCH_ONLY",
                "runtime_touched": False,
                "real_asset_context": real_asset_summary,
                "final_gates": gates,
                "recent_proxy": [format_summary_row(row) for row in rows],
                "caveat": "Recent stress uses public Yahoo ETF/futures and FX proxy bars plus historical Capital.com spread proxies; it is not broker-authoritative.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_recent_real_asset_rotation_stress_report(rows, trade_map, summary_path, status_path, cells, real_asset_summary, gates)
    (p.reports / f"FOREX_REAL_ASSET_ROTATION_RECENT_STRESS_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_external_flow_screen(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    contexts = load_currency_etf_context(p)
    specs = candidate_specs_external_flow(contexts)
    rows, trades = run_specs_screen(p, cells, specs)
    return rows, trades, currency_flow_context_summary(contexts)


def write_external_flow_screen_outputs(
    p: Paths,
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    flow_summary: dict[str, Any],
) -> dict[str, str]:
    summary_path = p.tables / f"FOREX_EXTERNAL_FLOW_SCREEN_SUMMARY_{RUN_DATE}.csv"
    if rows:
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in trade_map.items():
        path = p.tables / f"{candidate_id}_EXTERNAL_FLOW_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = external_flow_gates(rows)
    status_path = p.reports / f"FOREX_EXTERNAL_FLOW_SCREEN_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "EXTERNAL_FLOW_RESEARCH_ONLY",
                "runtime_touched": False,
                "flow_context": flow_summary,
                "final_gates": gates,
                "historical_overall": [format_summary_row(row) for row in rows if row.get("level") == "overall"],
                "caveat": "Currency ETF flow data ends in 2025-06 and is public proxy evidence, not broker-authoritative 2026 confirmation.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_external_flow_screen_report(rows, trade_map, summary_path, status_path, cells, flow_summary, gates)
    (p.reports / f"FOREX_EXTERNAL_FLOW_SCREEN_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_risk_regime_screen(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    risk = load_risk_context(p)
    specs = candidate_specs_risk_regime(risk)
    historical_rows, historical_trades = run_specs_screen(p, cells, specs)
    recent_rows, recent_trades = run_recent_proxy_stress_for_specs(p, cells, specs)
    return historical_rows, historical_trades, recent_rows, recent_trades, risk_context_summary(p, risk)


def write_risk_regime_screen_outputs(
    p: Paths,
    historical_rows: list[dict[str, Any]],
    historical_trade_map: dict[str, list[dict[str, Any]]],
    recent_rows: list[dict[str, Any]],
    recent_trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    risk_summary: dict[str, Any],
) -> dict[str, str]:
    historical_summary_path = p.tables / f"FOREX_RISK_REGIME_SCREEN_SUMMARY_{RUN_DATE}.csv"
    recent_summary_path = p.tables / f"FOREX_RISK_REGIME_RECENT_PROXY_SUMMARY_{RUN_DATE}.csv"
    if historical_rows:
        with historical_summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(historical_rows[0].keys()))
            writer.writeheader()
            for row in historical_rows:
                writer.writerow(format_summary_row(row))
    if recent_rows:
        with recent_summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(recent_rows[0].keys()))
            writer.writeheader()
            for row in recent_rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in historical_trade_map.items():
        path = p.tables / f"{candidate_id}_RISK_REGIME_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    for candidate_id, trades in recent_trade_map.items():
        path = p.tables / f"{candidate_id}_RISK_REGIME_RECENT_PROXY_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = risk_regime_gates(historical_rows, recent_rows)
    status_path = p.reports / f"FOREX_RISK_REGIME_SCREEN_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "RISK_REGIME_RESEARCH_ONLY",
                "runtime_touched": False,
                "risk_context": risk_summary,
                "final_gates": gates,
                "historical_overall": [format_summary_row(row) for row in historical_rows if row.get("level") == "overall"],
                "recent_proxy": [format_summary_row(row) for row in recent_rows],
                "caveat": "VIX/VXV public risk data is lagged one day and is not broker-authoritative Forex evidence.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_risk_regime_screen_report(
        historical_rows,
        recent_rows,
        historical_summary_path,
        recent_summary_path,
        status_path,
        cells,
        risk_summary,
        gates,
    )
    (p.reports / f"FOREX_RISK_REGIME_SCREEN_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def run_fx_cross_screen(
    p: Paths,
    cells: list[CostCell],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    contexts = load_fx_cross_context(p)
    specs = candidate_specs_fx_cross(contexts)
    rows, trades = run_specs_screen(p, cells, specs)
    return rows, trades, fx_cross_context_summary(contexts)


def write_fx_cross_screen_outputs(
    p: Paths,
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    cells: list[CostCell],
    cross_summary: dict[str, Any],
) -> dict[str, str]:
    summary_path = p.tables / f"FOREX_FX_CROSS_SCREEN_SUMMARY_{RUN_DATE}.csv"
    if rows:
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                writer.writerow(format_summary_row(row))
    for candidate_id, trades in trade_map.items():
        path = p.tables / f"{candidate_id}_FX_CROSS_TRADES_{RUN_DATE}.csv"
        if not trades:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trades[0].keys()))
            writer.writeheader()
            writer.writerows(trades)
    gates = fx_cross_gates(rows)
    status_path = p.reports / f"FOREX_FX_CROSS_SCREEN_STATUS_{RUN_DATE}.json"
    status_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "status": "FX_CROSS_RESEARCH_ONLY",
                "runtime_touched": False,
                "cross_context": cross_summary,
                "final_gates": gates,
                "historical_overall": [format_summary_row(row) for row in rows if row.get("level") == "overall"],
                "caveat": "Daily FX cross proxy data ends in 2025-06 and is public proxy evidence, not broker-authoritative 2026 confirmation.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_fx_cross_screen_report(rows, trade_map, summary_path, status_path, cells, cross_summary, gates)
    (p.reports / f"FOREX_FX_CROSS_SCREEN_{RUN_DATE}.md").write_text(report, encoding="utf-8")
    return gates


def fx_cross_gates(rows: list[dict[str, Any]]) -> dict[str, str]:
    external_style = external_flow_gates(rows)
    return {
        candidate_id: gate.replace("EXTERNAL_FLOW", "FX_CROSS").replace("WATCHLIST_ONLY", "FX_CROSS_WATCHLIST_ONLY")
        for candidate_id, gate in external_style.items()
    }


def render_fx_cross_screen_report(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    cross_summary: dict[str, Any],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    overall = [row for row in rows if row.get("level") == "overall"]
    broker_rows = [row for row in rows if row.get("level") == "broker"]
    lines = [
        "# Forex FX-Cross Rotation Screen",
        "",
        f"Generated at UTC: {generated}",
        "Status: FX_CROSS_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Cross context: lagged daily public FX proxy ratios. AUDJPY/USDJPY approximates AUD-vs-USD risk rotation for USDJPY; EURJPY/USDJPY approximates euro-vs-dollar confirmation for EURUSD. Observations are shifted one day before joining to H4 bars.",
        "",
        f"Summary CSV: `{relative(summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Cross Context",
        "",
        f"- Source root: `{cross_summary['source_root']}`",
        f"- Lag policy: {cross_summary['lag_policy']}",
        "",
        "| context | rows | observation_start | observation_end | available_through | source_file |",
        "| --- | ---: | --- | --- | --- | --- |",
    ]
    for name, row in cross_summary["rows"].items():
        lines.append(
            f"| {name} | {row['rows']} | {str(row['start_utc'])[:10]} | {str(row['end_utc'])[:10]} | {str(row['available_through_utc'])[:10]} | `{row['source_file']}` |"
        )
    lines.extend(
        [
            "",
            "## Cost Context",
            "",
            "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for symbol in ("EURUSD", "USDJPY"):
        cell = best_cell(cells, symbol, "H4")
        if cell:
            lines.append(
                f"| {symbol} | H4 | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Overall Results",
            "",
            "| candidate | symbol | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | final_gate |",
            "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in overall:
        lines.append(
            "| {candidate_id} | {symbol} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                symbol=row["symbol"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Broker Split", ""])
    lines.append("| candidate | broker | trades | net_R | expectancy_R | PF | maxDD_R | months+ |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for row in broker_rows:
        lines.append(
            "| {candidate_id} | {broker} | {trade_count} | {net:.2f} | {exp:.4f} | {pf} | {dd:.2f} | {pm}/{tm} |".format(
                candidate_id=row["candidate_id"],
                broker=row["broker"],
                trade_count=row["trade_count"],
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "A `REJECT_*` result is rejected for this v0 screen. A watchlist result would still require refreshed broker-authoritative 2026 Forex bars and owner approval before any demo-forward-test spec.",
            "",
            "Data caveat: the FX cross reference files end on 2025-06-30. This screen cannot prove current 2026 behavior.",
            "",
        ]
    )
    return "\n".join(lines)


def risk_regime_gates(historical_rows: list[dict[str, Any]], recent_rows: list[dict[str, Any]]) -> dict[str, str]:
    historical_overall = {row["candidate_id"]: row for row in historical_rows if row.get("level") == "overall"}
    recent_by_id = {row["candidate_id"]: row for row in recent_rows}
    gates: dict[str, str] = {}
    for candidate_id, row in historical_overall.items():
        recent = recent_by_id.get(candidate_id)
        if int(row["trade_count"]) < 80:
            gates[candidate_id] = "REJECT_RISK_REGIME_LOW_HISTORICAL_SAMPLE"
        elif not math.isfinite(float(row["profit_factor"])) or float(row["profit_factor"]) < 1.15:
            gates[candidate_id] = "REJECT_RISK_REGIME_WEAK_HISTORICAL_EDGE"
        elif float(row["net_expectancy_r"]) <= 0.03:
            gates[candidate_id] = "REJECT_RISK_REGIME_WEAK_EXPECTANCY"
        elif float(row["top_winner_removed_net_r"]) <= 0:
            gates[candidate_id] = "REJECT_RISK_REGIME_TOP_WINNER_DEPENDENT"
        elif float(row["max_drawdown_r"]) > 20:
            gates[candidate_id] = "REJECT_RISK_REGIME_DRAWDOWN"
        elif recent is None or int(recent["trade_count"]) < 20:
            gates[candidate_id] = "REJECT_RISK_REGIME_RECENT_LOW_SAMPLE"
        elif float(recent["profit_factor"]) < 1.05 or float(recent["net_expectancy_r"]) <= 0:
            gates[candidate_id] = "REJECT_RISK_REGIME_RECENT_PROXY_FAIL"
        else:
            gates[candidate_id] = "RISK_REGIME_WATCHLIST_ONLY_NEEDS_BROKER_REFRESH"
    return gates


def external_flow_gates(rows: list[dict[str, Any]]) -> dict[str, str]:
    overall_rows = {row["candidate_id"]: row for row in rows if row.get("level") == "overall"}
    broker_rows: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row.get("level") == "broker":
            broker_rows.setdefault(row["candidate_id"], []).append(row)
    gates: dict[str, str] = {}
    for candidate_id, row in overall_rows.items():
        if int(row["trade_count"]) < 80:
            gates[candidate_id] = "REJECT_EXTERNAL_FLOW_LOW_SAMPLE"
        elif not math.isfinite(float(row["profit_factor"])) or float(row["profit_factor"]) < 1.15:
            gates[candidate_id] = "REJECT_EXTERNAL_FLOW_WEAK_EDGE"
        elif float(row["net_expectancy_r"]) <= 0.03:
            gates[candidate_id] = "REJECT_EXTERNAL_FLOW_WEAK_EXPECTANCY"
        elif float(row["top_winner_removed_net_r"]) <= 0:
            gates[candidate_id] = "REJECT_EXTERNAL_FLOW_TOP_WINNER_DEPENDENT"
        elif float(row["max_drawdown_r"]) > 20:
            gates[candidate_id] = "REJECT_EXTERNAL_FLOW_DRAWDOWN"
        else:
            gates[candidate_id] = "WATCHLIST_ONLY_NEEDS_RECENT_FLOW_AND_BROKER_REFRESH"
        if gates[candidate_id].startswith("REJECT"):
            continue
        for broker_row in broker_rows.get(candidate_id, []):
            if int(broker_row["trade_count"]) >= 30 and (
                float(broker_row["total_net_r"]) <= 0 or float(broker_row["profit_factor"]) < 1.00
            ):
                gates[candidate_id] = "REJECT_EXTERNAL_FLOW_BROKER_INSTABILITY"
                break
    return gates


def global_risk_gates(rows: list[dict[str, Any]]) -> dict[str, str]:
    external_style = external_flow_gates(rows)
    return {
        candidate_id: gate.replace("EXTERNAL_FLOW", "GLOBAL_RISK").replace("WATCHLIST_ONLY", "GLOBAL_RISK_WATCHLIST_ONLY")
        for candidate_id, gate in external_style.items()
    }


def commodity_dollar_gates(rows: list[dict[str, Any]]) -> dict[str, str]:
    external_style = external_flow_gates(rows)
    return {
        candidate_id: gate.replace("EXTERNAL_FLOW", "COMMODITY_DOLLAR").replace("WATCHLIST_ONLY", "COMMODITY_DOLLAR_WATCHLIST_ONLY")
        for candidate_id, gate in external_style.items()
    }


def real_asset_rotation_gates(rows: list[dict[str, Any]]) -> dict[str, str]:
    external_style = external_flow_gates(rows)
    return {
        candidate_id: gate.replace("EXTERNAL_FLOW", "REAL_ASSET_ROTATION").replace(
            "WATCHLIST_ONLY", "REAL_ASSET_ROTATION_WATCHLIST_ONLY"
        )
        for candidate_id, gate in external_style.items()
    }


def haven_liquidity_gates(rows: list[dict[str, Any]]) -> dict[str, str]:
    external_style = external_flow_gates(rows)
    return {
        candidate_id: gate.replace("EXTERNAL_FLOW", "HAVEN_LIQUIDITY").replace(
            "WATCHLIST_ONLY", "HAVEN_LIQUIDITY_WATCHLIST_ONLY"
        )
        for candidate_id, gate in external_style.items()
    }


def rates_dollar_gates(rows: list[dict[str, Any]]) -> dict[str, str]:
    external_style = external_flow_gates(rows)
    return {
        candidate_id: gate.replace("EXTERNAL_FLOW", "RATES_DOLLAR").replace("WATCHLIST_ONLY", "RATES_DOLLAR_WATCHLIST_ONLY")
        for candidate_id, gate in external_style.items()
    }


def equity_leadership_gates(rows: list[dict[str, Any]]) -> dict[str, str]:
    external_style = external_flow_gates(rows)
    return {
        candidate_id: gate.replace("EXTERNAL_FLOW", "EQUITY_LEADERSHIP").replace(
            "WATCHLIST_ONLY", "EQUITY_LEADERSHIP_WATCHLIST_ONLY"
        )
        for candidate_id, gate in external_style.items()
    }


def sector_rotation_gates(rows: list[dict[str, Any]]) -> dict[str, str]:
    external_style = external_flow_gates(rows)
    return {
        candidate_id: gate.replace("EXTERNAL_FLOW", "SECTOR_ROTATION").replace(
            "WATCHLIST_ONLY", "SECTOR_ROTATION_WATCHLIST_ONLY"
        )
        for candidate_id, gate in external_style.items()
    }


def currency_basket_gates(rows: list[dict[str, Any]]) -> dict[str, str]:
    external_style = external_flow_gates(rows)
    return {
        candidate_id: gate.replace("EXTERNAL_FLOW", "CURRENCY_BASKET").replace(
            "WATCHLIST_ONLY", "CURRENCY_BASKET_WATCHLIST_ONLY"
        )
        for candidate_id, gate in external_style.items()
    }


def bond_vol_gates(rows: list[dict[str, Any]]) -> dict[str, str]:
    external_style = external_flow_gates(rows)
    return {
        candidate_id: gate.replace("EXTERNAL_FLOW", "BOND_VOL").replace("WATCHLIST_ONLY", "BOND_VOL_WATCHLIST_ONLY")
        for candidate_id, gate in external_style.items()
    }


def crypto_risk_gates(rows: list[dict[str, Any]]) -> dict[str, str]:
    external_style = external_flow_gates(rows)
    return {
        candidate_id: gate.replace("EXTERNAL_FLOW", "CRYPTO_RISK").replace("WATCHLIST_ONLY", "CRYPTO_RISK_WATCHLIST_ONLY")
        for candidate_id, gate in external_style.items()
    }


def cny_pressure_gates(historical_rows: list[dict[str, Any]], recent_rows: list[dict[str, Any]]) -> dict[str, str]:
    historical_overall = {row["candidate_id"]: row for row in historical_rows if row.get("level") == "overall"}
    broker_rows: dict[str, list[dict[str, Any]]] = {}
    for row in historical_rows:
        if row.get("level") == "broker":
            broker_rows.setdefault(row["candidate_id"], []).append(row)
    recent_by_id = {row["candidate_id"]: row for row in recent_rows}
    gates: dict[str, str] = {}
    for candidate_id, row in historical_overall.items():
        recent = recent_by_id.get(candidate_id)
        if int(row["trade_count"]) < 80:
            gates[candidate_id] = "REJECT_CNY_LOW_HISTORICAL_SAMPLE"
        elif not math.isfinite(float(row["profit_factor"])) or float(row["profit_factor"]) < 1.15:
            gates[candidate_id] = "REJECT_CNY_WEAK_HISTORICAL_EDGE"
        elif float(row["net_expectancy_r"]) <= 0.03:
            gates[candidate_id] = "REJECT_CNY_WEAK_EXPECTANCY"
        elif float(row["top_winner_removed_net_r"]) <= 0:
            gates[candidate_id] = "REJECT_CNY_TOP_WINNER_DEPENDENT"
        elif float(row["max_drawdown_r"]) > 20:
            gates[candidate_id] = "REJECT_CNY_DRAWDOWN"
        elif recent is None or int(recent["trade_count"]) < 20:
            gates[candidate_id] = "REJECT_CNY_RECENT_LOW_SAMPLE"
        elif float(recent["profit_factor"]) < 1.05 or float(recent["net_expectancy_r"]) <= 0:
            gates[candidate_id] = "REJECT_CNY_RECENT_PROXY_FAIL"
        else:
            gates[candidate_id] = "CNY_WATCHLIST_ONLY_NEEDS_BROKER_REFRESH"
        if gates[candidate_id].startswith("REJECT"):
            continue
        for broker_row in broker_rows.get(candidate_id, []):
            if int(broker_row["trade_count"]) >= 30 and (
                float(broker_row["total_net_r"]) <= 0 or float(broker_row["profit_factor"]) < 1.00
            ):
                gates[candidate_id] = "REJECT_CNY_BROKER_INSTABILITY"
                break
    return gates


def financial_liquidity_gates(historical_rows: list[dict[str, Any]], recent_rows: list[dict[str, Any]]) -> dict[str, str]:
    historical_overall = {row["candidate_id"]: row for row in historical_rows if row.get("level") == "overall"}
    broker_rows: dict[str, list[dict[str, Any]]] = {}
    for row in historical_rows:
        if row.get("level") == "broker":
            broker_rows.setdefault(row["candidate_id"], []).append(row)
    recent_by_id = {row["candidate_id"]: row for row in recent_rows}
    gates: dict[str, str] = {}
    for candidate_id, row in historical_overall.items():
        recent = recent_by_id.get(candidate_id)
        if int(row["trade_count"]) < 80:
            gates[candidate_id] = "REJECT_FINANCIAL_LIQUIDITY_LOW_HISTORICAL_SAMPLE"
        elif not math.isfinite(float(row["profit_factor"])) or float(row["profit_factor"]) < 1.15:
            gates[candidate_id] = "REJECT_FINANCIAL_LIQUIDITY_WEAK_HISTORICAL_EDGE"
        elif float(row["net_expectancy_r"]) <= 0.03:
            gates[candidate_id] = "REJECT_FINANCIAL_LIQUIDITY_WEAK_EXPECTANCY"
        elif float(row["top_winner_removed_net_r"]) <= 0:
            gates[candidate_id] = "REJECT_FINANCIAL_LIQUIDITY_TOP_WINNER_DEPENDENT"
        elif float(row["max_drawdown_r"]) > 20:
            gates[candidate_id] = "REJECT_FINANCIAL_LIQUIDITY_DRAWDOWN"
        elif recent is None or int(recent["trade_count"]) < 20:
            gates[candidate_id] = "REJECT_FINANCIAL_LIQUIDITY_RECENT_LOW_SAMPLE"
        elif float(recent["profit_factor"]) < 1.05 or float(recent["net_expectancy_r"]) <= 0:
            gates[candidate_id] = "REJECT_FINANCIAL_LIQUIDITY_RECENT_PROXY_FAIL"
        else:
            gates[candidate_id] = "FINANCIAL_LIQUIDITY_WATCHLIST_ONLY_NEEDS_BROKER_REFRESH"
        if gates[candidate_id].startswith("REJECT"):
            continue
        for broker_row in broker_rows.get(candidate_id, []):
            if int(broker_row["trade_count"]) >= 30 and (
                float(broker_row["total_net_r"]) <= 0 or float(broker_row["profit_factor"]) < 1.00
            ):
                gates[candidate_id] = "REJECT_FINANCIAL_LIQUIDITY_BROKER_INSTABILITY"
                break
    return gates


def cot_positioning_gates(historical_rows: list[dict[str, Any]], recent_rows: list[dict[str, Any]]) -> dict[str, str]:
    historical_overall = {row["candidate_id"]: row for row in historical_rows if row.get("level") == "overall"}
    broker_rows: dict[str, list[dict[str, Any]]] = {}
    for row in historical_rows:
        if row.get("level") == "broker":
            broker_rows.setdefault(row["candidate_id"], []).append(row)
    recent_by_id = {row["candidate_id"]: row for row in recent_rows}
    gates: dict[str, str] = {}
    for candidate_id, row in historical_overall.items():
        recent = recent_by_id.get(candidate_id)
        if int(row["trade_count"]) < 80:
            gates[candidate_id] = "REJECT_COT_LOW_HISTORICAL_SAMPLE"
        elif not math.isfinite(float(row["profit_factor"])) or float(row["profit_factor"]) < 1.15:
            gates[candidate_id] = "REJECT_COT_WEAK_HISTORICAL_EDGE"
        elif float(row["net_expectancy_r"]) <= 0.03:
            gates[candidate_id] = "REJECT_COT_WEAK_EXPECTANCY"
        elif float(row["top_winner_removed_net_r"]) <= 0:
            gates[candidate_id] = "REJECT_COT_TOP_WINNER_DEPENDENT"
        elif float(row["max_drawdown_r"]) > 18:
            gates[candidate_id] = "REJECT_COT_DRAWDOWN"
        elif recent is None or int(recent["trade_count"]) < 20:
            gates[candidate_id] = "REJECT_COT_RECENT_LOW_SAMPLE"
        elif not math.isfinite(float(recent["profit_factor"])) or float(recent["profit_factor"]) < 1.05:
            gates[candidate_id] = "REJECT_COT_RECENT_PROXY_FAIL"
        elif float(recent["net_expectancy_r"]) <= 0:
            gates[candidate_id] = "REJECT_COT_RECENT_PROXY_FAIL"
        else:
            gates[candidate_id] = "COT_WATCHLIST_ONLY_NEEDS_BROKER_REFRESH"
        if gates[candidate_id].startswith("REJECT"):
            continue
        for broker_row in broker_rows.get(candidate_id, []):
            if int(broker_row["trade_count"]) >= 30 and (
                float(broker_row["total_net_r"]) <= 0 or float(broker_row["profit_factor"]) < 1.00
            ):
                gates[candidate_id] = "REJECT_COT_BROKER_INSTABILITY"
                break
    return gates


def treasury_curve_gates(historical_rows: list[dict[str, Any]], recent_rows: list[dict[str, Any]]) -> dict[str, str]:
    historical_overall = {row["candidate_id"]: row for row in historical_rows if row.get("level") == "overall"}
    broker_rows: dict[str, list[dict[str, Any]]] = {}
    for row in historical_rows:
        if row.get("level") == "broker":
            broker_rows.setdefault(row["candidate_id"], []).append(row)
    recent_by_id = {row["candidate_id"]: row for row in recent_rows}
    gates: dict[str, str] = {}
    for candidate_id, row in historical_overall.items():
        recent = recent_by_id.get(candidate_id)
        if int(row["trade_count"]) < 80:
            gates[candidate_id] = "REJECT_TREASURY_CURVE_LOW_HISTORICAL_SAMPLE"
        elif not math.isfinite(float(row["profit_factor"])) or float(row["profit_factor"]) < 1.15:
            gates[candidate_id] = "REJECT_TREASURY_CURVE_WEAK_HISTORICAL_EDGE"
        elif float(row["net_expectancy_r"]) <= 0.03:
            gates[candidate_id] = "REJECT_TREASURY_CURVE_WEAK_EXPECTANCY"
        elif float(row["top_winner_removed_net_r"]) <= 0:
            gates[candidate_id] = "REJECT_TREASURY_CURVE_TOP_WINNER_DEPENDENT"
        elif float(row["max_drawdown_r"]) > 20:
            gates[candidate_id] = "REJECT_TREASURY_CURVE_DRAWDOWN"
        elif recent is None or int(recent["trade_count"]) < 20:
            gates[candidate_id] = "REJECT_TREASURY_CURVE_RECENT_LOW_SAMPLE"
        elif not math.isfinite(float(recent["profit_factor"])) or float(recent["profit_factor"]) < 1.05:
            gates[candidate_id] = "REJECT_TREASURY_CURVE_RECENT_PROXY_FAIL"
        elif float(recent["net_expectancy_r"]) <= 0:
            gates[candidate_id] = "REJECT_TREASURY_CURVE_RECENT_PROXY_FAIL"
        else:
            gates[candidate_id] = "TREASURY_CURVE_WATCHLIST_ONLY_NEEDS_BROKER_REFRESH"
        if gates[candidate_id].startswith("REJECT"):
            continue
        for broker_row in broker_rows.get(candidate_id, []):
            if int(broker_row["trade_count"]) >= 30 and (
                float(broker_row["total_net_r"]) <= 0 or float(broker_row["profit_factor"]) < 1.00
            ):
                gates[candidate_id] = "REJECT_TREASURY_CURVE_BROKER_INSTABILITY"
                break
    return gates


def calendar_session_gates(historical_rows: list[dict[str, Any]], recent_rows: list[dict[str, Any]]) -> dict[str, str]:
    historical_overall = {row["candidate_id"]: row for row in historical_rows if row.get("level") == "overall"}
    broker_rows: dict[str, list[dict[str, Any]]] = {}
    for row in historical_rows:
        if row.get("level") == "broker":
            broker_rows.setdefault(row["candidate_id"], []).append(row)
    recent_by_id = {row["candidate_id"]: row for row in recent_rows}
    gates: dict[str, str] = {}
    for candidate_id, row in historical_overall.items():
        recent = recent_by_id.get(candidate_id)
        if int(row["trade_count"]) < 80:
            gates[candidate_id] = "REJECT_CALENDAR_LOW_HISTORICAL_SAMPLE"
        elif not math.isfinite(float(row["profit_factor"])) or float(row["profit_factor"]) < 1.15:
            gates[candidate_id] = "REJECT_CALENDAR_WEAK_HISTORICAL_EDGE"
        elif float(row["net_expectancy_r"]) <= 0.03:
            gates[candidate_id] = "REJECT_CALENDAR_WEAK_EXPECTANCY"
        elif float(row["top_winner_removed_net_r"]) <= 0:
            gates[candidate_id] = "REJECT_CALENDAR_TOP_WINNER_DEPENDENT"
        elif float(row["max_drawdown_r"]) > 20:
            gates[candidate_id] = "REJECT_CALENDAR_DRAWDOWN"
        elif recent is None or int(recent["trade_count"]) < 20:
            gates[candidate_id] = "REJECT_CALENDAR_RECENT_LOW_SAMPLE"
        elif not math.isfinite(float(recent["profit_factor"])) or float(recent["profit_factor"]) < 1.05 or float(recent["net_expectancy_r"]) <= 0:
            gates[candidate_id] = "REJECT_CALENDAR_RECENT_PROXY_FAIL"
        else:
            gates[candidate_id] = "CALENDAR_WATCHLIST_ONLY_NEEDS_BROKER_REFRESH"
        if gates[candidate_id].startswith("REJECT"):
            continue
        for broker_row in broker_rows.get(candidate_id, []):
            if int(broker_row["trade_count"]) >= 30 and (
                float(broker_row["total_net_r"]) <= 0 or float(broker_row["profit_factor"]) < 1.00
            ):
                gates[candidate_id] = "REJECT_CALENDAR_BROKER_INSTABILITY"
                break
    return gates


def weekly_structure_gates(historical_rows: list[dict[str, Any]], recent_rows: list[dict[str, Any]]) -> dict[str, str]:
    calendar_style = calendar_session_gates(historical_rows, recent_rows)
    return {
        candidate_id: gate.replace("CALENDAR", "WEEKLY_STRUCTURE")
        for candidate_id, gate in calendar_style.items()
    }


def macro_final_gates(historical_rows: list[dict[str, Any]], recent_rows: list[dict[str, Any]]) -> dict[str, str]:
    historical_overall = {row["candidate_id"]: row for row in historical_rows if row.get("level") == "overall"}
    recent_by_id = {row["candidate_id"]: row for row in recent_rows}
    gates: dict[str, str] = {}
    for candidate_id, row in historical_overall.items():
        recent = recent_by_id.get(candidate_id)
        if int(row["trade_count"]) < 80:
            gates[candidate_id] = "REJECT_MACRO_LOW_HISTORICAL_SAMPLE"
        elif float(row["profit_factor"]) < 1.15 or float(row["net_expectancy_r"]) <= 0.03:
            gates[candidate_id] = "REJECT_MACRO_WEAK_HISTORICAL_EDGE"
        elif float(row["max_drawdown_r"]) > 20:
            gates[candidate_id] = "REJECT_MACRO_HISTORICAL_DRAWDOWN"
        elif float(row["top_winner_removed_net_r"]) <= 0:
            gates[candidate_id] = "REJECT_MACRO_TOP_WINNER_DEPENDENT"
        elif recent is None or int(recent["trade_count"]) < 20:
            gates[candidate_id] = "REJECT_MACRO_RECENT_LOW_SAMPLE"
        elif float(recent["profit_factor"]) < 1.05 or float(recent["net_expectancy_r"]) <= 0:
            gates[candidate_id] = "REJECT_MACRO_RECENT_PROXY_FAIL"
        else:
            gates[candidate_id] = "MACRO_WATCHLIST_ONLY_NEEDS_BROKER_REFRESH"
    return gates


def format_summary_row(row: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, float):
            output[key] = display_float(value, places=8)
        else:
            output[key] = value
    return output


def recent_proxy_gate(row: dict[str, Any]) -> str:
    trade_count = int(row["trade_count"])
    pf = float(row["profit_factor"])
    expectancy = float(row["net_expectancy_r"])
    drawdown = float(row["max_drawdown_r"])
    top_removed = float(row["top_winner_removed_net_r"])
    if trade_count < 40:
        return "RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR"
    if not math.isfinite(pf) or pf < 1.10:
        return "RECENT_PROXY_FAIL_WEAK_EDGE"
    if expectancy <= 0.03:
        return "RECENT_PROXY_FAIL_WEAK_EXPECTANCY"
    if top_removed <= 0:
        return "RECENT_PROXY_FAIL_TOP_WINNER_DEPENDENT"
    if drawdown > 12:
        return "RECENT_PROXY_FAIL_DRAWDOWN"
    return "RECENT_PROXY_WATCHLIST_ONLY_NOT_APPROVED"


def second_pass_gate_decisions(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
) -> dict[str, str]:
    decisions: dict[str, str] = {}
    overall_rows = {row["candidate_id"]: row for row in rows if row["level"] == "overall"}
    broker_rows: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row["level"] == "broker":
            broker_rows.setdefault(row["candidate_id"], []).append(row)
    for candidate_id, row in overall_rows.items():
        decisions[candidate_id] = second_pass_gate_decision(
            row,
            broker_rows.get(candidate_id, []),
            trade_map.get(candidate_id, []),
        )
    return decisions


def second_pass_gate_decision(
    overall: dict[str, Any],
    broker_rows: list[dict[str, Any]],
    trades: list[dict[str, Any]],
) -> str:
    if int(overall["trade_count"]) < 100:
        return "REJECT_SECOND_PASS_LOW_SAMPLE"
    if not math.isfinite(float(overall["profit_factor"])) or float(overall["profit_factor"]) < 1.20:
        return "REJECT_SECOND_PASS_WEAK_NET_EDGE"
    if float(overall["net_expectancy_r"]) <= 0.05:
        return "REJECT_SECOND_PASS_WEAK_EXPECTANCY"
    if float(overall["top_winner_removed_net_r"]) <= 0:
        return "REJECT_SECOND_PASS_TOP_WINNER_DEPENDENT"
    if float(overall["max_drawdown_r"]) > 20:
        return "REJECT_SECOND_PASS_DRAWDOWN"
    if int(overall["total_months"]) and int(overall["positive_months"]) / int(overall["total_months"]) < 0.55:
        return "REJECT_SECOND_PASS_MONTHLY_INSTABILITY"
    for broker_row in broker_rows:
        if int(broker_row["trade_count"]) < 30:
            continue
        if float(broker_row["total_net_r"]) <= 0 or float(broker_row["profit_factor"]) < 1.05:
            return "REJECT_SECOND_PASS_BROKER_INSTABILITY"
    era_rows = era_summaries(trades)
    for row in era_rows:
        if row["trade_count"] < 30:
            continue
        if row["total_net_r"] <= 0 or row["profit_factor"] < 1.00:
            return "REJECT_SECOND_PASS_ERA_DEPENDENCE"
    return "WATCHLIST_NEEDS_FRESH_DATA_AND_FORWARD_SHADOW"


def era_summaries(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cutoff = pd.Timestamp("2022-01-01T00:00:00Z")
    buckets = {"pre_2022": [], "post_2022": []}
    for trade in trades:
        entry = pd.Timestamp(trade["entry_time_utc"])
        buckets["post_2022" if entry >= cutoff else "pre_2022"].append(trade)
    return [trade_metric_snapshot(name, bucket) for name, bucket in buckets.items()]


def trade_metric_snapshot(name: str, trades: list[dict[str, Any]]) -> dict[str, Any]:
    net = [float(t["net_r"]) for t in trades]
    wins = [value for value in net if value > 0]
    losses = [value for value in net if value < 0]
    monthly = aggregate_by(trades, "month")
    return {
        "name": name,
        "trade_count": len(trades),
        "total_net_r": sum(net),
        "net_expectancy_r": mean(net),
        "profit_factor": sum(wins) / abs(sum(losses)) if losses else (float("inf") if wins else float("nan")),
        "max_drawdown_r": max_drawdown(net),
        "positive_months": sum(1 for value in monthly.values() if value > 0),
        "total_months": len(monthly),
    }


def render_screen_report(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    summary_path: Path,
    cells: list[CostCell],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    overall = [row for row in rows if row["level"] == "overall"]
    lines = [
        "# Forex First Candidate Screen",
        "",
        f"Generated at UTC: {generated}",
        "Status: FIRST_SCREEN_RESEARCH_ONLY",
        "",
        "Boundary: offline Python backtest only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "These are first-pass screens, not approvals. A `WATCHLIST` result would still require second-pass robustness, stale-data review, and owner approval before any forward-test spec.",
        "",
        f"Summary CSV: `{relative(summary_path)}`",
        "",
        "## Cost Context",
        "",
        "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for spec in candidate_specs():
        cell = best_cell(cells, spec.symbol, spec.timeframe)
        if cell:
            lines.append(
                f"| {spec.symbol} | {spec.timeframe} | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Overall Results",
            "",
            "| candidate | family | symbol | tf | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | decision |",
            "| --- | --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |",
        ]
    )
    for row in overall:
        lines.append(
            "| {candidate_id} | {family} | {symbol} | {timeframe} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} |".format(
                candidate_id=row["candidate_id"],
                family=row["family"],
                symbol=row["symbol"],
                timeframe=row["timeframe"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
            )
        )
    lines.extend(["", "## Session Split", ""])
    for candidate_id, trades in trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| session_utc | trades | net_R | expectancy_R |")
        lines.append("| --- | ---: | ---: | ---: |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(["## Direction Split", ""])
    for candidate_id, trades in trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| direction | trades | net_R | expectancy_R |")
        lines.append("| --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "Any candidate with `REJECT_*` is rejected for this v0 screen; do not tune that same v0 in place. A materially different hypothesis must be registered as a new v0/v1 thesis.",
            "",
            "Local data staleness is a real limitation: the processed bars end in 2025, while the current date is 2026-07-03. A survivor would require refreshed Forex data or a forward-shadow period before any demo-forward-test spec.",
            "",
        ]
    )
    return "\n".join(lines)


def render_second_pass_report(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    summary_path: Path,
    cells: list[CostCell],
    final_gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    overall = [row for row in rows if row["level"] == "overall"]
    broker_rows = [row for row in rows if row["level"] == "broker"]
    spec_by_id = {spec.candidate_id: spec for spec in candidate_specs_second_pass()}
    lines = [
        "# Forex Second-Pass Candidate Screen",
        "",
        f"Generated at UTC: {generated}",
        "Status: SECOND_PASS_RESEARCH_ONLY",
        "",
        "Boundary: offline Python backtest only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Second-pass gates are stricter than the first screen: a result must survive broker split, pre/post-2022 era split, drawdown, top-winner removal, and stability checks. Passing these gates would still be a watchlist item only because the local broker bars end in 2025.",
        "",
        f"Summary CSV: `{relative(summary_path)}`",
        "",
        "## Registered Second-Pass Hypotheses",
        "",
        "| candidate | symbol | tf | family | thesis |",
        "| --- | --- | --- | --- | --- |",
    ]
    for spec in candidate_specs_second_pass():
        lines.append(f"| {spec.candidate_id} | {spec.symbol} | {spec.timeframe} | {spec.family} | {spec.description} |")
    lines.extend(
        [
            "",
            "## Cost Context",
            "",
            "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for spec in candidate_specs_second_pass():
        cell = best_cell(cells, spec.symbol, spec.timeframe)
        if cell:
            lines.append(
                f"| {spec.symbol} | {spec.timeframe} | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Overall Results",
            "",
            "| candidate | family | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | first_metric_decision | second_pass_gate |",
            "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in overall:
        lines.append(
            "| {candidate_id} | {family} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                family=row["family"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=final_gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Broker Split", ""])
    lines.append("| candidate | broker | trades | net_R | expectancy_R | PF | maxDD_R | months+ |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for row in broker_rows:
        lines.append(
            "| {candidate_id} | {broker} | {trade_count} | {net:.2f} | {exp:.4f} | {pf} | {dd:.2f} | {pm}/{tm} |".format(
                candidate_id=row["candidate_id"],
                broker=row["broker"],
                trade_count=row["trade_count"],
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
            )
        )
    lines.extend(["", "## Era Split", ""])
    for candidate_id, trades in trade_map.items():
        spec = spec_by_id.get(candidate_id)
        lines.append(f"### {candidate_id}")
        if spec:
            lines.append("")
            lines.append(spec.description)
        lines.append("")
        lines.append("| era | trades | net_R | expectancy_R | PF | maxDD_R | months+ |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: | --- |")
        for row in era_summaries(trades):
            lines.append(
                "| {name} | {trade_count} | {net:.2f} | {exp:.4f} | {pf} | {dd:.2f} | {pm}/{tm} |".format(
                    name=row["name"],
                    trade_count=row["trade_count"],
                    net=row["total_net_r"],
                    exp=row["net_expectancy_r"],
                    pf=display_float(row["profit_factor"], 4),
                    dd=row["max_drawdown_r"],
                    pm=row["positive_months"],
                    tm=row["total_months"],
                )
            )
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "Any `REJECT_SECOND_PASS_*` result remains rejected and must not be converted into a demo-forward spec. A watchlist result would still require refreshed 2026 broker data and an offline forward-shadow period before owner approval could even be requested.",
            "",
        ]
    )
    return "\n".join(lines)


def render_recent_proxy_stress_report(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    proxy_files = recent_proxy_inventory(paths())
    lines = [
        "# Forex Recent Proxy Stress Test",
        "",
        f"Generated at UTC: {generated}",
        "Status: RECENT_PROXY_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay against public proxy bars only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Source caveat: Yahoo Finance hourly FX proxy bars are useful for recency stress, but they are not broker-authoritative and do not include broker spread. The replay uses historical Capital.com median spread proxies plus the lane's conservative slippage assumptions.",
        "",
        f"Summary CSV: `{relative(summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Recent Proxy Inventory",
        "",
        "| symbol | timeframe | rows | start_utc | end_utc | source_file |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for row in proxy_files:
        lines.append(
            f"| {row['symbol']} | {row['timeframe']} | {row['rows']} | {row['start_utc'][:10]} | {row['end_utc'][:10]} | `{row['source_file']}` |"
        )
    lines.extend(
        [
            "",
            "## Cost Proxy Context",
            "",
            "| symbol | timeframe | historical spread proxy | p95_cost_R_recent |",
            "| --- | --- | --- | ---: |",
        ]
    )
    seen_cost: set[tuple[str, str]] = set()
    for spec in candidate_specs_recent_proxy():
        key = (spec.symbol, spec.timeframe)
        if key in seen_cost:
            continue
        seen_cost.add(key)
        cell = best_cell(cells, spec.symbol, spec.timeframe)
        if cell:
            lines.append(f"| {spec.symbol} | {spec.timeframe} | {cell.broker} median spread {cell.spread_median_points:.2f} pts | {cell.cost_r_recent_p95:.4f} |")
        else:
            lines.append(f"| {spec.symbol} | {spec.timeframe} | no local broker spread proxy | n/a |")
    lines.extend(
        [
            "",
            "## Results",
            "",
            "| candidate | symbol | tf | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | gate |",
            "| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| {candidate_id} | {symbol} | {timeframe} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {gate} |".format(
                candidate_id=row["candidate_id"],
                symbol=row["symbol"],
                timeframe=row["timeframe"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Session Split", ""])
    for candidate_id, trades in trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| session_utc | trades | net_R | expectancy_R |")
        lines.append("| --- | ---: | ---: | ---: |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "This is a recency stress test only. A recent proxy pass cannot approve an EA because the bars are not broker-authoritative, the spreads are historical proxies, and the sample starts after 2025-07-01. A failure here is still useful: it lowers priority for more expensive broker-data refresh work.",
            "",
        ]
    )
    return "\n".join(lines)


def render_external_flow_screen_report(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    flow_summary: dict[str, Any],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    overall = [row for row in rows if row.get("level") == "overall"]
    broker_rows = [row for row in rows if row.get("level") == "broker"]
    lines = [
        "# Forex External Flow Screen",
        "",
        f"Generated at UTC: {generated}",
        "Status: EXTERNAL_FLOW_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "External-flow context: lagged daily currency ETF relative-strength proxies. FXE/UUP is used for EURUSD, and FXY/UUP is inverted for USDJPY so positive flow aligns with USDJPY strength. ETF observations are shifted to the next UTC date before joining to H4 bars.",
        "",
        f"Summary CSV: `{relative(summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Flow Context",
        "",
        f"- Source root: `{flow_summary['source_root']}`",
        f"- Lag policy: {flow_summary['lag_policy']}",
        "",
        "| symbol | rows | observation_start | observation_end | available_through | source_file |",
        "| --- | ---: | --- | --- | --- | --- |",
    ]
    for symbol, row in flow_summary["rows"].items():
        lines.append(
            f"| {symbol} | {row['rows']} | {str(row['start_utc'])[:10]} | {str(row['end_utc'])[:10]} | {str(row['available_through_utc'])[:10]} | `{row['source_file']}` |"
        )
    lines.extend(
        [
            "",
            "## Cost Context",
            "",
            "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for symbol in ("EURUSD", "USDJPY"):
        cell = best_cell(cells, symbol, "H4")
        if cell:
            lines.append(
                f"| {symbol} | H4 | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Overall Results",
            "",
            "| candidate | family | symbol | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | final_gate |",
            "| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in overall:
        lines.append(
            "| {candidate_id} | {family} | {symbol} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                family=row["family"],
                symbol=row["symbol"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Broker Split", ""])
    lines.append("| candidate | broker | trades | net_R | expectancy_R | PF | maxDD_R | months+ |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for row in broker_rows:
        lines.append(
            "| {candidate_id} | {broker} | {trade_count} | {net:.2f} | {exp:.4f} | {pf} | {dd:.2f} | {pm}/{tm} |".format(
                candidate_id=row["candidate_id"],
                broker=row["broker"],
                trade_count=row["trade_count"],
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "A `REJECT_EXTERNAL_FLOW_*` result is rejected for this v0 screen. A watchlist result would still require refreshed 2026 broker bars and refreshed external-flow confirmation before any demo-forward-test spec.",
            "",
            "Data caveat: the currency ETF reference files end on 2025-06-30. This screen cannot prove current 2026 behavior.",
            "",
        ]
    )
    return "\n".join(lines)


def render_risk_regime_screen_report(
    historical_rows: list[dict[str, Any]],
    recent_rows: list[dict[str, Any]],
    historical_summary_path: Path,
    recent_summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    risk_summary: dict[str, Any],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    overall = [row for row in historical_rows if row.get("level") == "overall"]
    broker_rows = [row for row in historical_rows if row.get("level") == "broker"]
    lines = [
        "# Forex VIX/VXV Risk-Regime Screen",
        "",
        f"Generated at UTC: {generated}",
        "Status: RISK_REGIME_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Risk context: lagged public FRED VIX and VXV data. Risk-off uses rising VIX plus elevated VIX/VXV term structure; risk-on uses falling VIX plus calmer term structure. Observations are shifted one day before joining to bars.",
        "",
        f"Historical summary CSV: `{relative(historical_summary_path)}`",
        f"Recent proxy summary CSV: `{relative(recent_summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Risk Context",
        "",
        f"- Source root: `{risk_summary['source_root']}`",
        f"- Rows: {risk_summary['rows']}",
        f"- Observation window: {risk_summary['start_utc'][:10]} through {risk_summary['end_utc'][:10]}",
        f"- Lookahead-safe availability through: {risk_summary['available_through_utc'][:10]}",
        f"- Lag policy: {risk_summary['lag_policy']}",
        f"- VIX source: `{risk_summary['files']['vix']}`",
        f"- VXV source: `{risk_summary['files']['vxv']}`",
        "",
        "## Cost Context",
        "",
        "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for symbol in ("EURUSD", "USDJPY"):
        cell = best_cell(cells, symbol, "H4")
        if cell:
            lines.append(
                f"| {symbol} | H4 | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Historical Overall Results",
            "",
            "| candidate | symbol | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | final_gate |",
            "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in overall:
        lines.append(
            "| {candidate_id} | {symbol} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                symbol=row["symbol"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Recent Proxy Stress", ""])
    lines.append("| candidate | trades | L/S | net_R | expectancy_R | PF | maxDD_R | recent_gate |")
    lines.append("| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |")
    for row in recent_rows:
        lines.append(
            "| {candidate_id} | {trade_count} | {long_trades}/{short_trades} | {net:.2f} | {exp:.4f} | {pf} | {dd:.2f} | {gate} |".format(
                candidate_id=row["candidate_id"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                gate=recent_proxy_gate(row),
            )
        )
    lines.extend(["", "## Broker Split", ""])
    lines.append("| candidate | broker | trades | net_R | expectancy_R | PF | maxDD_R | months+ |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for row in broker_rows:
        lines.append(
            "| {candidate_id} | {broker} | {trade_count} | {net:.2f} | {exp:.4f} | {pf} | {dd:.2f} | {pm}/{tm} |".format(
                candidate_id=row["candidate_id"],
                broker=row["broker"],
                trade_count=row["trade_count"],
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
            )
        )
    lines.extend(
        [
            "",
            "## Read",
            "",
            "A `REJECT_RISK_REGIME_*` result is rejected for this v0 screen. A watchlist result would still require refreshed broker-authoritative 2026 Forex bars and owner approval before any demo-forward-test spec.",
            "",
        ]
    )
    return "\n".join(lines)


def render_macro_screen_report(
    historical_rows: list[dict[str, Any]],
    recent_rows: list[dict[str, Any]],
    historical_summary_path: Path,
    recent_summary_path: Path,
    status_path: Path,
    macro_summary: dict[str, Any],
    final_gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    overall = [row for row in historical_rows if row.get("level") == "overall"]
    broker_rows = [row for row in historical_rows if row.get("level") == "broker"]
    lines = [
        "# Forex Macro/Rate Screen",
        "",
        f"Generated at UTC: {generated}",
        "Status: MACRO_RATE_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Macro context: lagged public FRED real-yield and broad-dollar data from existing Phase 0 raw files. Observations are shifted one day before joining to bars to avoid same-day lookahead.",
        "",
        f"Historical summary CSV: `{relative(historical_summary_path)}`",
        f"Recent proxy summary CSV: `{relative(recent_summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Macro Context",
        "",
        f"- Source root: `{macro_summary['source_root']}`",
        f"- Rows: {macro_summary['rows']}",
        f"- Observation window: {macro_summary['start_utc'][:10]} through {macro_summary['end_utc'][:10]}",
        f"- Lookahead-safe availability through: {macro_summary['available_through_utc'][:10]}",
        f"- Real-yield source: `{macro_summary['files']['real_yield_10y']}`",
        f"- Broad-dollar source: `{macro_summary['files']['dollar_index_broad']}`",
        "",
        "## Historical Broker Results",
        "",
        "| candidate | symbol | tf | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | decision | final_gate |",
        "| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |",
    ]
    for row in overall:
        lines.append(
            "| {candidate_id} | {symbol} | {timeframe} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                symbol=row["symbol"],
                timeframe=row["timeframe"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                decision=row["decision"],
                gate=final_gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Broker Split", ""])
    lines.append("| candidate | broker | trades | net_R | expectancy_R | PF | maxDD_R | months+ |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for row in broker_rows:
        lines.append(
            "| {candidate_id} | {broker} | {trade_count} | {net:.2f} | {exp:.4f} | {pf} | {dd:.2f} | {pm}/{tm} |".format(
                candidate_id=row["candidate_id"],
                broker=row["broker"],
                trade_count=row["trade_count"],
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
            )
        )
    lines.extend(["", "## Recent Proxy Stress", ""])
    lines.append("| candidate | trades | net_R | expectancy_R | PF | maxDD_R | months+ | recent_gate |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |")
    for row in recent_rows:
        lines.append(
            "| {candidate_id} | {trade_count} | {net:.2f} | {exp:.4f} | {pf} | {dd:.2f} | {pm}/{tm} | {gate} |".format(
                candidate_id=row["candidate_id"],
                trade_count=row["trade_count"],
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                gate=recent_proxy_gate(row),
            )
        )
    lines.extend(
        [
            "",
            "## Read",
            "",
            "Any `REJECT_MACRO_*` result is rejected. A `MACRO_WATCHLIST_ONLY_NEEDS_BROKER_REFRESH` result would still require refreshed broker-authoritative Forex data and owner approval before any demo-forward spec. Public macro/proxy evidence alone cannot authorize an EA.",
            "",
        ]
    )
    return "\n".join(lines)


def render_treasury_curve_screen_report(
    historical_rows: list[dict[str, Any]],
    recent_rows: list[dict[str, Any]],
    historical_trade_map: dict[str, list[dict[str, Any]]],
    historical_summary_path: Path,
    recent_summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    curve_summary: dict[str, Any],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    overall = [row for row in historical_rows if row.get("level") == "overall"]
    broker_rows = [row for row in historical_rows if row.get("level") == "broker"]
    lines = [
        "# Forex Treasury Curve Screen",
        "",
        f"Generated at UTC: {generated}",
        "Status: TREASURY_CURVE_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Treasury context: lagged public FRED DGS2, DGS10, and T10Y2Y data. Front-end pressure means rising DGS2 with 2s10s flattening; bull-steepening relief means falling DGS2 with 2s10s steepening. Observations are shifted one day before joining to H4 bars.",
        "",
        f"Historical summary CSV: `{relative(historical_summary_path)}`",
        f"Recent proxy summary CSV: `{relative(recent_summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Treasury Curve Context",
        "",
        f"- Source root: `{curve_summary['source_root']}`",
        f"- Rows: {curve_summary['rows']}",
        f"- Observation window: {curve_summary['start_utc'][:10]} through {curve_summary['end_utc'][:10]}",
        f"- Lookahead-safe availability through: {curve_summary['available_through_utc'][:10]}",
        f"- Lag policy: {curve_summary['lag_policy']}",
        f"- Orientation: {curve_summary['orientation']}",
        f"- DGS2 source: `{curve_summary['files']['dgs2']}`",
        f"- DGS10 source: `{curve_summary['files']['dgs10']}`",
        f"- T10Y2Y source: `{curve_summary['files']['t10y2y']}`",
        "",
        "## Cost Context",
        "",
        "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for symbol in ("EURUSD", "USDJPY"):
        cell = best_cell(cells, symbol, "H4")
        if cell:
            lines.append(
                f"| {symbol} | H4 | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Historical Overall Results",
            "",
            "| candidate | symbol | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | final_gate |",
            "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in overall:
        lines.append(
            "| {candidate_id} | {symbol} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                symbol=row["symbol"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Broker Split", ""])
    lines.append("| candidate | broker | trades | net_R | expectancy_R | PF | maxDD_R | months+ |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for row in broker_rows:
        lines.append(
            "| {candidate_id} | {broker} | {trade_count} | {net:.2f} | {exp:.4f} | {pf} | {dd:.2f} | {pm}/{tm} |".format(
                candidate_id=row["candidate_id"],
                broker=row["broker"],
                trade_count=row["trade_count"],
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
            )
        )
    lines.extend(["", "## Recent Proxy Stress", ""])
    lines.append("| candidate | trades | L/S | net_R | expectancy_R | PF | maxDD_R | months+ | recent_gate |")
    lines.append("| --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |")
    for row in recent_rows:
        lines.append(
            "| {candidate_id} | {trade_count} | {long_trades}/{short_trades} | {net:.2f} | {exp:.4f} | {pf} | {dd:.2f} | {pm}/{tm} | {gate} |".format(
                candidate_id=row["candidate_id"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                gate=recent_proxy_gate(row),
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in historical_trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "Any `REJECT_TREASURY_CURVE_*` result is rejected for this v0 screen. A watchlist result would still require refreshed broker-authoritative Forex bars and owner approval before any demo-forward-test spec.",
            "",
            "Data caveat: the local FRED Treasury curve files currently run through the context window above. Recent proxy FX bars after that date inherit the last available curve observation, so recent stress is a clue only.",
            "",
        ]
    )
    return "\n".join(lines)


def render_cny_pressure_screen_report(
    historical_rows: list[dict[str, Any]],
    recent_rows: list[dict[str, Any]],
    historical_trade_map: dict[str, list[dict[str, Any]]],
    historical_summary_path: Path,
    recent_summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    cny_summary: dict[str, Any],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    overall = [row for row in historical_rows if row.get("level") == "overall"]
    broker_rows = [row for row in historical_rows if row.get("level") == "broker"]
    lines = [
        "# Forex CNY/Dollar Pressure Screen",
        "",
        f"Generated at UTC: {generated}",
        "Status: CNY_DOLLAR_PRESSURE_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "CNY context: lagged public FRED USD/CNY (`DEXCHUS`) plus broad-dollar (`DTWEXBGS`) data. DEXCHUS is yuan per USD, so a positive USD/CNY change means CNY depreciation and dollar pressure. Observations are shifted one day before joining to H4 bars.",
        "",
        f"Historical summary CSV: `{relative(historical_summary_path)}`",
        f"Recent proxy summary CSV: `{relative(recent_summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## CNY Context",
        "",
        f"- Source root: `{cny_summary['source_root']}`",
        f"- Rows: {cny_summary['rows']}",
        f"- Observation window: {cny_summary['start_utc'][:10]} through {cny_summary['end_utc'][:10]}",
        f"- Lookahead-safe availability through: {cny_summary['available_through_utc'][:10]}",
        f"- Lag policy: {cny_summary['lag_policy']}",
        f"- Orientation: {cny_summary['orientation']}",
        f"- USD/CNY source: `{cny_summary['files']['usd_cny']}`",
        f"- Broad-dollar source: `{cny_summary['files']['dollar_index_broad']}`",
        "",
        "## Cost Context",
        "",
        "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for symbol in ("EURUSD", "USDJPY"):
        cell = best_cell(cells, symbol, "H4")
        if cell:
            lines.append(
                f"| {symbol} | H4 | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Historical Overall Results",
            "",
            "| candidate | symbol | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | final_gate |",
            "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in overall:
        lines.append(
            "| {candidate_id} | {symbol} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                symbol=row["symbol"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Broker Split", ""])
    lines.append("| candidate | broker | trades | net_R | expectancy_R | PF | maxDD_R | months+ |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for row in broker_rows:
        lines.append(
            "| {candidate_id} | {broker} | {trade_count} | {net:.2f} | {exp:.4f} | {pf} | {dd:.2f} | {pm}/{tm} |".format(
                candidate_id=row["candidate_id"],
                broker=row["broker"],
                trade_count=row["trade_count"],
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
            )
        )
    lines.extend(["", "## Recent Proxy Stress", ""])
    lines.append("| candidate | trades | net_R | expectancy_R | PF | maxDD_R | months+ | recent_gate |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |")
    for row in recent_rows:
        lines.append(
            "| {candidate_id} | {trade_count} | {net:.2f} | {exp:.4f} | {pf} | {dd:.2f} | {pm}/{tm} | {gate} |".format(
                candidate_id=row["candidate_id"],
                trade_count=row["trade_count"],
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                gate=recent_proxy_gate(row),
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in historical_trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "Any `REJECT_CNY_*` result is rejected. A `CNY_WATCHLIST_ONLY_NEEDS_BROKER_REFRESH` result would still require refreshed broker-authoritative Forex data and owner approval before any demo-forward spec. Public CNY/macro/proxy evidence alone cannot authorize an EA.",
            "",
        ]
    )
    return "\n".join(lines)


def render_calendar_session_screen_report(
    historical_rows: list[dict[str, Any]],
    recent_rows: list[dict[str, Any]],
    historical_trade_map: dict[str, list[dict[str, Any]]],
    historical_summary_path: Path,
    recent_summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    overall = [row for row in historical_rows if row.get("level") == "overall"]
    broker_rows = [row for row in historical_rows if row.get("level") == "broker"]
    lines = [
        "# Forex Calendar/Session Screen",
        "",
        f"Generated at UTC: {generated}",
        "Status: CALENDAR_SESSION_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Screen context: price-only FX calendar/session hypotheses. EURUSD tests NY-fix overextension reversion on H1; USDJPY tests month-turn carry pullbacks on H4. These rules are fixed v0 screens and are not post-result tuning.",
        "",
        f"Historical summary CSV: `{relative(historical_summary_path)}`",
        f"Recent proxy summary CSV: `{relative(recent_summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Cost Context",
        "",
        "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for spec in candidate_specs_calendar_session():
        cell = best_cell(cells, spec.symbol, spec.timeframe)
        if cell:
            lines.append(
                f"| {spec.symbol} | {spec.timeframe} | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Historical Overall Results",
            "",
            "| candidate | symbol | tf | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | final_gate |",
            "| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in overall:
        lines.append(
            "| {candidate_id} | {symbol} | {timeframe} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                symbol=row["symbol"],
                timeframe=row["timeframe"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Broker Split", ""])
    lines.append("| candidate | broker | trades | net_R | expectancy_R | PF | maxDD_R | months+ |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for row in broker_rows:
        lines.append(
            "| {candidate_id} | {broker} | {trade_count} | {net:.2f} | {exp:.4f} | {pf} | {dd:.2f} | {pm}/{tm} |".format(
                candidate_id=row["candidate_id"],
                broker=row["broker"],
                trade_count=row["trade_count"],
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
            )
        )
    lines.extend(["", "## Recent Proxy Stress", ""])
    lines.append("| candidate | trades | net_R | expectancy_R | PF | maxDD_R | months+ | recent_gate |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |")
    for row in recent_rows:
        lines.append(
            "| {candidate_id} | {trade_count} | {net:.2f} | {exp:.4f} | {pf} | {dd:.2f} | {pm}/{tm} | {gate} |".format(
                candidate_id=row["candidate_id"],
                trade_count=row["trade_count"],
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                gate=recent_proxy_gate(row),
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in historical_trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "Any `REJECT_CALENDAR_*` result is rejected. A `CALENDAR_WATCHLIST_ONLY_NEEDS_BROKER_REFRESH` result would still require refreshed broker-authoritative 2026 Forex bars and owner approval before any demo-forward spec.",
            "",
        ]
    )
    return "\n".join(lines)


def render_weekly_structure_screen_report(
    historical_rows: list[dict[str, Any]],
    recent_rows: list[dict[str, Any]],
    historical_trade_map: dict[str, list[dict[str, Any]]],
    historical_summary_path: Path,
    recent_summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    overall = [row for row in historical_rows if row.get("level") == "overall"]
    broker_rows = [row for row in historical_rows if row.get("level") == "broker"]
    lines = [
        "# Forex Weekly Structure Screen",
        "",
        f"Generated at UTC: {generated}",
        "Status: WEEKLY_STRUCTURE_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Screen context: price-only weekly FX structure. EURUSD tests early-week prior-range liquidity fades and mid/late-week reversion toward the weekly open; USDJPY tests prior-week expansion followed by H4 carry-trend pullbacks. These are fixed v0 rules, not tuned approvals.",
        "",
        f"Historical summary CSV: `{relative(historical_summary_path)}`",
        f"Recent proxy summary CSV: `{relative(recent_summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Cost Context",
        "",
        "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for spec in candidate_specs_weekly_structure():
        cell = best_cell(cells, spec.symbol, spec.timeframe)
        if cell:
            lines.append(
                f"| {spec.symbol} | {spec.timeframe} | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Historical Overall Results",
            "",
            "| candidate | symbol | tf | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | final_gate |",
            "| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in overall:
        lines.append(
            "| {candidate_id} | {symbol} | {timeframe} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                symbol=row["symbol"],
                timeframe=row["timeframe"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Broker Split", ""])
    lines.append("| candidate | broker | trades | net_R | expectancy_R | PF | maxDD_R | months+ |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for row in broker_rows:
        lines.append(
            "| {candidate_id} | {broker} | {trade_count} | {net:.2f} | {exp:.4f} | {pf} | {dd:.2f} | {pm}/{tm} |".format(
                candidate_id=row["candidate_id"],
                broker=row["broker"],
                trade_count=row["trade_count"],
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
            )
        )
    lines.extend(["", "## Recent Proxy Stress", ""])
    lines.append("| candidate | trades | net_R | expectancy_R | PF | maxDD_R | months+ | recent_gate |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |")
    for row in recent_rows:
        lines.append(
            "| {candidate_id} | {trade_count} | {net:.2f} | {exp:.4f} | {pf} | {dd:.2f} | {pm}/{tm} | {gate} |".format(
                candidate_id=row["candidate_id"],
                trade_count=row["trade_count"],
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                gate=recent_proxy_gate(row),
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in historical_trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "Any `REJECT_WEEKLY_STRUCTURE_*` result is rejected. A watchlist result would still require refreshed broker-authoritative 2026 Forex bars and owner approval before any demo-forward spec.",
            "",
        ]
    )
    return "\n".join(lines)


def render_financial_liquidity_screen_report(
    historical_rows: list[dict[str, Any]],
    recent_rows: list[dict[str, Any]],
    historical_trade_map: dict[str, list[dict[str, Any]]],
    historical_summary_path: Path,
    recent_summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    financial_summary: dict[str, Any],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    overall = [row for row in historical_rows if row.get("level") == "overall"]
    broker_rows = [row for row in historical_rows if row.get("level") == "broker"]
    recent_by_id = {row["candidate_id"]: row for row in recent_rows}
    lines = [
        "# Forex Financial Conditions / Liquidity Screen",
        "",
        f"Generated at UTC: {generated}",
        "Status: FINANCIAL_LIQUIDITY_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Context: lagged FRED NFCI, ANFCI, and WALCL. Rising NFCI/ANFCI means tighter financial conditions; WALCL growth is Fed balance-sheet liquidity expansion. Weekly observations are shifted by seven days before joining to H4 bars.",
        "",
        f"Historical summary CSV: `{relative(historical_summary_path)}`",
        f"Recent proxy summary CSV: `{relative(recent_summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Financial/Liquidity Context",
        "",
        f"- Source root: `{financial_summary['source_root']}`",
        f"- Rows: {financial_summary['rows']}",
        f"- Observation window: {financial_summary['start_utc'][:10]} through {financial_summary['end_utc'][:10]}",
        f"- Lookahead-safe availability through: {financial_summary['available_through_utc'][:10]}",
        f"- Lag policy: {financial_summary['lag_policy']}",
        f"- Orientation: {financial_summary['orientation']}",
        f"- NFCI source: `{financial_summary['files'].get('nfci', '')}`",
        f"- ANFCI source: `{financial_summary['files'].get('anfci', '')}`",
        f"- WALCL source: `{financial_summary['files'].get('walcl', '')}`",
        "",
        "## Cost Context",
        "",
        "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for spec in candidate_specs_financial_liquidity(pd.DataFrame()):
        cell = best_cell(cells, spec.symbol, spec.timeframe)
        if cell:
            lines.append(
                f"| {spec.symbol} | {spec.timeframe} | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Historical Deduped Results",
            "",
            "| candidate | symbol | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | final_gate |",
            "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in overall:
        lines.append(
            "| {candidate_id} | {symbol} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                symbol=row["symbol"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(
        [
            "",
            "## Broker Split",
            "",
            "| candidate | broker | trades | net_R | PF | maxDD_R | decision |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in broker_rows:
        lines.append(
            "| {candidate_id} | {broker} | {trade_count} | {net:.2f} | {pf} | {dd:.2f} | {decision} |".format(
                candidate_id=row["candidate_id"],
                broker=row["broker"],
                trade_count=row["trade_count"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                decision=row["decision"],
            )
        )
    lines.extend(
        [
            "",
            "## Recent Public FX Proxy Stress",
            "",
            "| candidate | trades | PF | net_R | expectancy_R | maxDD_R | gate_input_read |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in recent_rows:
        lines.append(
            "| {candidate_id} | {trade_count} | {pf} | {net:.2f} | {exp:.4f} | {dd:.2f} | {decision} |".format(
                candidate_id=row["candidate_id"],
                trade_count=row["trade_count"],
                pf=display_float(row["profit_factor"], 4),
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                dd=row["max_drawdown_r"],
                decision=row["decision"],
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in historical_trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        if candidate_id in recent_by_id:
            recent = recent_by_id[candidate_id]
            lines.append(
                f"| recent_proxy | all | {recent['trade_count']} | {float(recent['total_net_r']):.2f} | {float(recent['net_expectancy_r']):.4f} |"
            )
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "Any `REJECT_FINANCIAL_LIQUIDITY_*` result is rejected for this v0 screen. A watchlist result would still require refreshed broker-authoritative 2026 Forex bars and owner approval before any demo-forward-test spec.",
            "",
        ]
    )
    return "\n".join(lines)


def render_cot_positioning_screen_report(
    historical_rows: list[dict[str, Any]],
    recent_rows: list[dict[str, Any]],
    historical_trade_map: dict[str, list[dict[str, Any]]],
    historical_summary_path: Path,
    recent_summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    cot_summary: dict[str, Any],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    overall = [row for row in historical_rows if row.get("level") == "overall"]
    broker_rows = [row for row in historical_rows if row.get("level") == "broker"]
    lines = [
        "# Forex CFTC COT Positioning Screen",
        "",
        f"Generated at UTC: {generated}",
        "Status: COT_POSITIONING_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Context: official CFTC Traders in Financial Futures futures-only archives. Euro FX leveraged-money net is EURUSD-oriented directly; Japanese Yen leveraged-money net is inverted so positive spot-oriented net is USDJPY-bullish. Weekly COT reports are shifted seven days before joining to H4 bars.",
        "",
        f"Historical summary CSV: `{relative(historical_summary_path)}`",
        f"Recent proxy summary CSV: `{relative(recent_summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## COT Context",
        "",
        f"- Source root: `{cot_summary['source_root']}`",
        f"- Source URL: `{cot_summary['source_url']}`",
        f"- Rows: {cot_summary['rows']}",
        f"- Observation window: {cot_summary['start_utc'][:10]} through {cot_summary['end_utc'][:10]}",
        f"- Lookahead-safe availability through: {cot_summary['available_through_utc'][:10]}",
        f"- Lag policy: {cot_summary['lag_policy']}",
        f"- Orientation: {cot_summary['orientation']}",
        "",
        "## Latest Positioning Snapshot",
        "",
        "| symbol | market | report date | available date | spot lev net % OI | z156 | delta 4w | delta 13w |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in cot_summary["latest_snapshot"]:
        lines.append(
            "| {symbol} | {market} | {report} | {available} | {net:.2f} | {z:.2f} | {d4:.2f} | {d13:.2f} |".format(
                symbol=row["symbol"],
                market=row["market"],
                report=str(row["report_utc"])[:10],
                available=str(row["available_utc"])[:10],
                net=row["spot_lev_net_pct_oi"],
                z=row["spot_lev_z156"],
                d4=row["spot_lev_delta_4w"],
                d13=row["spot_lev_delta_13w"],
            )
        )
    lines.extend(
        [
            "",
            "## Cost Context",
            "",
            "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for spec in candidate_specs_cot_positioning(pd.DataFrame()):
        cell = best_cell(cells, spec.symbol, spec.timeframe)
        if cell:
            lines.append(
                f"| {spec.symbol} | {spec.timeframe} | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Historical Deduped Results",
            "",
            "| candidate | symbol | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | final_gate |",
            "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in overall:
        lines.append(
            "| {candidate_id} | {symbol} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                symbol=row["symbol"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(
        [
            "",
            "## Broker Split",
            "",
            "| candidate | broker | trades | net_R | PF | maxDD_R | decision |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in broker_rows:
        lines.append(
            "| {candidate_id} | {broker} | {trade_count} | {net:.2f} | {pf} | {dd:.2f} | {decision} |".format(
                candidate_id=row["candidate_id"],
                broker=row["broker"],
                trade_count=row["trade_count"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                decision=row["decision"],
            )
        )
    lines.extend(
        [
            "",
            "## Recent Public FX Proxy Stress",
            "",
            "| candidate | trades | PF | net_R | expectancy_R | maxDD_R | gate_input_read |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in recent_rows:
        lines.append(
            "| {candidate_id} | {trade_count} | {pf} | {net:.2f} | {exp:.4f} | {dd:.2f} | {decision} |".format(
                candidate_id=row["candidate_id"],
                trade_count=row["trade_count"],
                pf=display_float(row["profit_factor"], 4),
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                dd=row["max_drawdown_r"],
                decision=row["decision"],
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in historical_trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "Any `REJECT_COT_*` result is rejected for this v0 screen. A `COT_WATCHLIST_ONLY_NEEDS_BROKER_REFRESH` result would still require refreshed broker-authoritative Forex bars and owner approval before any demo-forward-test spec. Weekly public positioning data alone cannot authorize an EA.",
            "",
        ]
    )
    return "\n".join(lines)


def render_global_risk_screen_report(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    global_summary: dict[str, Any],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    overall = [row for row in rows if row.get("level") == "overall"]
    broker_rows = [row for row in rows if row.get("level") == "broker"]
    lines = [
        "# Forex Global Risk/Credit Screen",
        "",
        f"Generated at UTC: {generated}",
        "Status: GLOBAL_RISK_CREDIT_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Global-risk context: lagged daily EEM/SPY and HYG/IEF ETF ratios. Positive changes indicate emerging-market and credit risk appetite; negative changes indicate defensive pressure. Observations are shifted one day before joining to H4 bars.",
        "",
        f"Summary CSV: `{relative(summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Global-Risk Context",
        "",
        f"- Source root: `{global_summary['source_root']}`",
        f"- Rows: {global_summary['rows']}",
        f"- Observation window: {global_summary['start_utc'][:10]} through {global_summary['end_utc'][:10]}",
        f"- Lookahead-safe availability through: {global_summary['available_through_utc'][:10]}",
        f"- Lag policy: {global_summary['lag_policy']}",
        f"- Orientation: {global_summary['orientation']}",
        f"- EEM/SPY source: `{global_summary['files'].get('eem_spy', '')}`",
        f"- HYG/IEF source: `{global_summary['files'].get('hyg_ief', '')}`",
        "",
        "## Cost Context",
        "",
        "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for symbol in ("EURUSD", "USDJPY"):
        cell = best_cell(cells, symbol, "H4")
        if cell:
            lines.append(
                f"| {symbol} | H4 | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Overall Results",
            "",
            "| candidate | family | symbol | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | final_gate |",
            "| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in overall:
        lines.append(
            "| {candidate_id} | {family} | {symbol} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                family=row["family"],
                symbol=row["symbol"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Broker Split", ""])
    lines.append("| candidate | broker | trades | net_R | expectancy_R | PF | maxDD_R | months+ |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for row in broker_rows:
        lines.append(
            "| {candidate_id} | {broker} | {trade_count} | {net:.2f} | {exp:.4f} | {pf} | {dd:.2f} | {pm}/{tm} |".format(
                candidate_id=row["candidate_id"],
                broker=row["broker"],
                trade_count=row["trade_count"],
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "Any `REJECT_GLOBAL_RISK_*` result is rejected for this v0 screen. A watchlist result would still require refreshed 2026 broker bars and refreshed global-risk proxy confirmation before any demo-forward-test spec.",
            "",
            "Data caveat: the EEM/SPY and HYG/IEF reference files end on 2025-06-30. This screen cannot prove current 2026 behavior.",
            "",
        ]
    )
    return "\n".join(lines)


def render_real_asset_rotation_screen_report(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    real_asset_summary: dict[str, Any],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    overall = [row for row in rows if row.get("level") == "overall"]
    broker_rows = [row for row in rows if row.get("level") == "broker"]
    lines = [
        "# Forex Real-Asset Rotation Screen",
        "",
        f"Generated at UTC: {generated}",
        "Status: REAL_ASSET_ROTATION_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Real-asset context: lagged daily USO/UUP oil-dollar ratio, HG/GC copper-versus-gold futures ratio, and SLV/GLD silver-versus-gold ratio. Observations are shifted one day before joining to H4 bars.",
        "",
        f"Summary CSV: `{relative(summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Real-Asset Context",
        "",
        f"- Source root: `{real_asset_summary['source_root']}`",
        f"- Rows: {real_asset_summary['rows']}",
        f"- Observation window: {real_asset_summary['start_utc'][:10]} through {real_asset_summary['end_utc'][:10]}",
        f"- Lookahead-safe availability through: {real_asset_summary['available_through_utc'][:10]}",
        f"- Lag policy: {real_asset_summary['lag_policy']}",
        f"- Orientation: {real_asset_summary['orientation']}",
        f"- USO/UUP source: `{real_asset_summary['files'].get('uso_uup', '')}`",
        f"- HG/GC source: `{real_asset_summary['files'].get('hg_gc', '')}`",
        f"- SLV/GLD source: `{real_asset_summary['files'].get('slv_gld', '')}`",
        "",
        "## Cost Context",
        "",
        "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for spec in candidate_specs_real_asset_rotation(pd.DataFrame()):
        cell = best_cell(cells, spec.symbol, spec.timeframe)
        if cell:
            lines.append(
                f"| {spec.symbol} | {spec.timeframe} | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Overall Results",
            "",
            "| candidate | symbol | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | final_gate |",
            "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in overall:
        lines.append(
            "| {candidate_id} | {symbol} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                symbol=row["symbol"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Broker Split", ""])
    lines.append("| candidate | broker | trades | net_R | expectancy_R | PF | maxDD_R | months+ |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for row in broker_rows:
        lines.append(
            "| {candidate_id} | {broker} | {trade_count} | {net:.2f} | {exp:.4f} | {pf} | {dd:.2f} | {pm}/{tm} |".format(
                candidate_id=row["candidate_id"],
                broker=row["broker"],
                trade_count=row["trade_count"],
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "Any `REJECT_REAL_ASSET_ROTATION_*` result is rejected for this v0 screen. A watchlist result would still require refreshed 2026 broker bars and recent real-asset proxy confirmation before any demo-forward-test spec.",
            "",
            "Data caveat: reference files end around 2025-06/2025-07. This screen cannot prove current 2026 behavior.",
            "",
        ]
    )
    return "\n".join(lines)


def render_recent_real_asset_rotation_stress_report(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    real_asset_summary: dict[str, Any],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    lines = [
        "# Forex Real-Asset Rotation Recent Stress",
        "",
        f"Generated at UTC: {generated}",
        "Status: REAL_ASSET_ROTATION_RECENT_STRESS_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay against public proxy data only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Purpose: stress the historical real-asset rotation v0 candidates against recent public Yahoo ETF/futures proxy data and recent public Yahoo FX proxy bars. This is recency triage, not broker-authoritative evidence.",
        "",
        f"Summary CSV: `{relative(summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Recent Real-Asset Context",
        "",
        f"- Source root: `{real_asset_summary['source_root']}`",
        f"- Rows: {real_asset_summary['rows']}",
        f"- Observation window: {real_asset_summary['start_utc'][:10]} through {real_asset_summary['end_utc'][:10]}",
        f"- Lookahead-safe availability through: {real_asset_summary['available_through_utc'][:10]}",
        f"- Lag policy: {real_asset_summary['lag_policy']}",
        f"- USO/UUP source: `{real_asset_summary['files'].get('uso_uup', '')}`",
        f"- HG/GC source: `{real_asset_summary['files'].get('hg_gc', '')}`",
        f"- SLV/GLD source: `{real_asset_summary['files'].get('slv_gld', '')}`",
        "",
        "## Cost Context",
        "",
        "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for spec in candidate_specs_real_asset_rotation(pd.DataFrame()):
        cell = best_cell(cells, spec.symbol, spec.timeframe)
        if cell:
            lines.append(
                f"| {spec.symbol} | {spec.timeframe} | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Recent Proxy Results",
            "",
            "| candidate | symbol | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | recent_gate |",
            "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| {candidate_id} | {symbol} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                symbol=row["symbol"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "A recent proxy pass cannot approve an EA because both the ETF/futures context and FX bars are public proxies and spreads are historical proxies. A failure or low-sample result lowers priority for broker-refresh work.",
            "",
        ]
    )
    return "\n".join(lines)


def render_haven_liquidity_screen_report(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    haven_summary: dict[str, Any],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    overall = [row for row in rows if row.get("level") == "overall"]
    broker_rows = [row for row in rows if row.get("level") == "broker"]
    lines = [
        "# Forex Haven/Liquidity Screen",
        "",
        f"Generated at UTC: {generated}",
        "Status: HAVEN_LIQUIDITY_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Haven/liquidity context: lagged daily GLD momentum, GDX/GLD miner participation, SPY/TLT risk preference, and XLU/XLK defensive leadership. Observations are shifted one day before joining to H4 bars.",
        "",
        f"Summary CSV: `{relative(summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Haven/Liquidity Context",
        "",
        f"- Source root: `{haven_summary['source_root']}`",
        f"- Rows: {haven_summary['rows']}",
        f"- Observation window: {haven_summary['start_utc'][:10]} through {haven_summary['end_utc'][:10]}",
        f"- Lookahead-safe availability through: {haven_summary['available_through_utc'][:10]}",
        f"- Lag policy: {haven_summary['lag_policy']}",
        f"- Orientation: {haven_summary['orientation']}",
        f"- GLD source: `{haven_summary['files'].get('gld', '')}`",
        f"- GDX/GLD source: `{haven_summary['files'].get('gdx_gld', '')}`",
        f"- SPY/TLT source: `{haven_summary['files'].get('spy_tlt', '')}`",
        f"- XLU/XLK source: `{haven_summary['files'].get('xlu_xlk', '')}`",
        "",
        "## Cost Context",
        "",
        "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for spec in candidate_specs_haven_liquidity(pd.DataFrame()):
        cell = best_cell(cells, spec.symbol, spec.timeframe)
        if cell:
            lines.append(
                f"| {spec.symbol} | {spec.timeframe} | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Overall Results",
            "",
            "| candidate | symbol | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | final_gate |",
            "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in overall:
        lines.append(
            "| {candidate_id} | {symbol} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                symbol=row["symbol"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Broker Split", ""])
    lines.append("| candidate | broker | trades | net_R | expectancy_R | PF | maxDD_R | months+ |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for row in broker_rows:
        lines.append(
            "| {candidate_id} | {broker} | {trade_count} | {net:.2f} | {exp:.4f} | {pf} | {dd:.2f} | {pm}/{tm} |".format(
                candidate_id=row["candidate_id"],
                broker=row["broker"],
                trade_count=row["trade_count"],
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "Any `REJECT_HAVEN_LIQUIDITY_*` result is rejected for this v0 screen. A watchlist result would still require refreshed 2026 broker bars and recent haven/liquidity proxy confirmation before any demo-forward-test spec.",
            "",
            "Data caveat: reference files end around 2025-06/2025-07. This screen cannot prove current 2026 behavior.",
            "",
        ]
    )
    return "\n".join(lines)


def render_recent_haven_liquidity_stress_report(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    haven_summary: dict[str, Any],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    lines = [
        "# Forex Haven/Liquidity Recent Stress",
        "",
        f"Generated at UTC: {generated}",
        "Status: HAVEN_LIQUIDITY_RECENT_STRESS_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay against public proxy data only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Purpose: stress the historical haven/liquidity v0 candidates against recent public Yahoo ETF proxy data and recent public Yahoo FX proxy bars. This is recency triage, not broker-authoritative evidence.",
        "",
        f"Summary CSV: `{relative(summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Recent Haven/Liquidity Context",
        "",
        f"- Source root: `{haven_summary['source_root']}`",
        f"- Rows: {haven_summary['rows']}",
        f"- Observation window: {haven_summary['start_utc'][:10]} through {haven_summary['end_utc'][:10]}",
        f"- Lookahead-safe availability through: {haven_summary['available_through_utc'][:10]}",
        f"- Lag policy: {haven_summary['lag_policy']}",
        f"- GLD source: `{haven_summary['files'].get('gld', '')}`",
        f"- GDX/GLD source: `{haven_summary['files'].get('gdx_gld', '')}`",
        f"- SPY/TLT source: `{haven_summary['files'].get('spy_tlt', '')}`",
        f"- XLU/XLK source: `{haven_summary['files'].get('xlu_xlk', '')}`",
        "",
        "## Cost Context",
        "",
        "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for spec in candidate_specs_haven_liquidity(pd.DataFrame()):
        cell = best_cell(cells, spec.symbol, spec.timeframe)
        if cell:
            lines.append(
                f"| {spec.symbol} | {spec.timeframe} | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Recent Proxy Results",
            "",
            "| candidate | symbol | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | recent_gate |",
            "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| {candidate_id} | {symbol} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                symbol=row["symbol"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "A recent proxy pass cannot approve an EA because both the ETF context and FX bars are public proxies and spreads are historical proxies. A failure or low-sample result lowers priority for broker-refresh work.",
            "",
        ]
    )
    return "\n".join(lines)


def render_commodity_dollar_screen_report(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    commodity_summary: dict[str, Any],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    overall = [row for row in rows if row.get("level") == "overall"]
    broker_rows = [row for row in rows if row.get("level") == "broker"]
    lines = [
        "# Forex Commodity/Dollar Screen",
        "",
        f"Generated at UTC: {generated}",
        "Status: COMMODITY_DOLLAR_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Commodity/dollar context: lagged daily DBC/UUP and DBB/UUP ETF ratios. Positive changes indicate commodity strength versus the dollar; negative changes indicate commodity weakness versus the dollar. Observations are shifted one day before joining to H4 bars.",
        "",
        f"Summary CSV: `{relative(summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Commodity/Dollar Context",
        "",
        f"- Source root: `{commodity_summary['source_root']}`",
        f"- Rows: {commodity_summary['rows']}",
        f"- Observation window: {commodity_summary['start_utc'][:10]} through {commodity_summary['end_utc'][:10]}",
        f"- Lookahead-safe availability through: {commodity_summary['available_through_utc'][:10]}",
        f"- Lag policy: {commodity_summary['lag_policy']}",
        f"- Orientation: {commodity_summary['orientation']}",
        f"- DBC/UUP source: `{commodity_summary['files'].get('dbc_uup', '')}`",
        f"- DBB/UUP source: `{commodity_summary['files'].get('dbb_uup', '')}`",
        "",
        "## Cost Context",
        "",
        "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for symbol in ("EURUSD", "USDJPY"):
        cell = best_cell(cells, symbol, "H4")
        if cell:
            lines.append(
                f"| {symbol} | H4 | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Overall Results",
            "",
            "| candidate | family | symbol | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | final_gate |",
            "| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in overall:
        lines.append(
            "| {candidate_id} | {family} | {symbol} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                family=row["family"],
                symbol=row["symbol"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Broker Split", ""])
    lines.append("| candidate | broker | trades | net_R | expectancy_R | PF | maxDD_R | months+ |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for row in broker_rows:
        lines.append(
            "| {candidate_id} | {broker} | {trade_count} | {net:.2f} | {exp:.4f} | {pf} | {dd:.2f} | {pm}/{tm} |".format(
                candidate_id=row["candidate_id"],
                broker=row["broker"],
                trade_count=row["trade_count"],
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "Any `REJECT_COMMODITY_DOLLAR_*` result is rejected for this v0 screen. A watchlist result would still require refreshed 2026 broker bars and refreshed commodity/dollar proxy confirmation before any demo-forward-test spec.",
            "",
            "Data caveat: the DBC/UUP and DBB/UUP reference files end on 2025-06-30. This screen cannot prove current 2026 behavior.",
            "",
        ]
    )
    return "\n".join(lines)


def render_rates_dollar_screen_report(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    rates_summary: dict[str, Any],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    overall = [row for row in rows if row.get("level") == "overall"]
    broker_rows = [row for row in rows if row.get("level") == "broker"]
    lines = [
        "# Forex Rates/Dollar Screen",
        "",
        f"Generated at UTC: {generated}",
        "Status: RATES_DOLLAR_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Rates/dollar context: lagged daily TLT/UUP and TLT/SHY ETF ratios. Positive changes indicate duration strength versus the dollar/cash; negative changes indicate yield/dollar pressure. Observations are shifted one day before joining to H4 bars.",
        "",
        f"Summary CSV: `{relative(summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Rates/Dollar Context",
        "",
        f"- Source root: `{rates_summary['source_root']}`",
        f"- Rows: {rates_summary['rows']}",
        f"- Observation window: {rates_summary['start_utc'][:10]} through {rates_summary['end_utc'][:10]}",
        f"- Lookahead-safe availability through: {rates_summary['available_through_utc'][:10]}",
        f"- Lag policy: {rates_summary['lag_policy']}",
        f"- Orientation: {rates_summary['orientation']}",
        f"- TLT/UUP source: `{rates_summary['files'].get('tlt_uup', '')}`",
        f"- TLT/SHY source: `{rates_summary['files'].get('tlt_shy', '')}`",
        "",
        "## Cost Context",
        "",
        "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for symbol in ("EURUSD", "USDJPY"):
        cell = best_cell(cells, symbol, "H4")
        if cell:
            lines.append(
                f"| {symbol} | H4 | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Overall Results",
            "",
            "| candidate | family | symbol | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | final_gate |",
            "| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in overall:
        lines.append(
            "| {candidate_id} | {family} | {symbol} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                family=row["family"],
                symbol=row["symbol"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Broker Split", ""])
    lines.append("| candidate | broker | trades | net_R | expectancy_R | PF | maxDD_R | months+ |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for row in broker_rows:
        lines.append(
            "| {candidate_id} | {broker} | {trade_count} | {net:.2f} | {exp:.4f} | {pf} | {dd:.2f} | {pm}/{tm} |".format(
                candidate_id=row["candidate_id"],
                broker=row["broker"],
                trade_count=row["trade_count"],
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "Any `REJECT_RATES_DOLLAR_*` result is rejected for this v0/v1 screen. A watchlist result would still require refreshed 2026 broker bars and refreshed rates/dollar proxy confirmation before any demo-forward-test spec.",
            "",
            "Data caveat: the TLT/UUP and TLT/SHY reference files end on 2025-06-30. This screen cannot prove current 2026 behavior.",
            "",
        ]
    )
    return "\n".join(lines)


def render_recent_rates_dollar_stress_report(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    rates_summary: dict[str, Any],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    lines = [
        "# Forex Rates/Dollar Recent Stress",
        "",
        f"Generated at UTC: {generated}",
        "Status: RATES_DOLLAR_RECENT_STRESS_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay against public proxy data only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Purpose: stress the historical EURUSD rates/dollar v1 clue against recent public Yahoo ETF proxy data and recent public Yahoo FX proxy bars. This is recency triage, not broker-authoritative evidence.",
        "",
        f"Summary CSV: `{relative(summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Recent Rates/Dollar Context",
        "",
        f"- Source root: `{rates_summary['source_root']}`",
        f"- Rows: {rates_summary['rows']}",
        f"- Observation window: {rates_summary['start_utc'][:10]} through {rates_summary['end_utc'][:10]}",
        f"- Lookahead-safe availability through: {rates_summary['available_through_utc'][:10]}",
        f"- Lag policy: {rates_summary['lag_policy']}",
        f"- TLT/UUP source: `{rates_summary['files'].get('tlt_uup', '')}`",
        f"- TLT/SHY source: `{rates_summary['files'].get('tlt_shy', '')}`",
        "",
        "## Cost Context",
        "",
        "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for symbol in ("EURUSD", "USDJPY"):
        cell = best_cell(cells, symbol, "H4")
        if cell:
            lines.append(
                f"| {symbol} | H4 | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Recent Proxy Results",
            "",
            "| candidate | symbol | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | recent_gate |",
            "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| {candidate_id} | {symbol} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                symbol=row["symbol"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "A recent proxy pass cannot approve an EA because both the ETF context and FX bars are public proxies and spreads are historical proxies. A failure or low-sample result lowers priority for broker-refresh work.",
            "",
        ]
    )
    return "\n".join(lines)


def render_equity_leadership_screen_report(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    equity_summary: dict[str, Any],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    overall = [row for row in rows if row.get("level") == "overall"]
    broker_rows = [row for row in rows if row.get("level") == "broker"]
    lines = [
        "# Forex Equity-Leadership Screen",
        "",
        f"Generated at UTC: {generated}",
        "Status: EQUITY_LEADERSHIP_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Equity-leadership context: lagged daily ACWX/SPY, IWM/SPY, and XLF/XLU ETF ratios. ACWX/SPY approximates ex-US versus US equity leadership; IWM/SPY and XLF/XLU approximate US cyclical/risk leadership. Observations are shifted one day before joining to H4 bars.",
        "",
        f"Summary CSV: `{relative(summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Equity-Leadership Context",
        "",
        f"- Source root: `{equity_summary['source_root']}`",
        f"- Rows: {equity_summary['rows']}",
        f"- Observation window: {equity_summary['start_utc'][:10]} through {equity_summary['end_utc'][:10]}",
        f"- Lookahead-safe availability through: {equity_summary['available_through_utc'][:10]}",
        f"- Lag policy: {equity_summary['lag_policy']}",
        f"- Orientation: {equity_summary['orientation']}",
        f"- ACWX/SPY source: `{equity_summary['files'].get('acwx_spy', '')}`",
        f"- IWM/SPY source: `{equity_summary['files'].get('iwm_spy', '')}`",
        f"- XLF/XLU source: `{equity_summary['files'].get('xlf_xlu', '')}`",
        "",
        "## Cost Context",
        "",
        "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for symbol in ("EURUSD", "USDJPY"):
        cell = best_cell(cells, symbol, "H4")
        if cell:
            lines.append(
                f"| {symbol} | H4 | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Overall Results",
            "",
            "| candidate | family | symbol | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | final_gate |",
            "| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in overall:
        lines.append(
            "| {candidate_id} | {family} | {symbol} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                family=row["family"],
                symbol=row["symbol"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Broker Split", ""])
    lines.append("| candidate | broker | trades | net_R | expectancy_R | PF | maxDD_R | months+ |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for row in broker_rows:
        lines.append(
            "| {candidate_id} | {broker} | {trade_count} | {net:.2f} | {exp:.4f} | {pf} | {dd:.2f} | {pm}/{tm} |".format(
                candidate_id=row["candidate_id"],
                broker=row["broker"],
                trade_count=row["trade_count"],
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "Any `REJECT_EQUITY_LEADERSHIP_*` result is rejected for this v0 screen. A watchlist result would still require refreshed 2026 broker bars and recent equity-leadership proxy confirmation before any demo-forward-test spec.",
            "",
            "Data caveat: the ACWX/SPY, IWM/SPY, and XLF/XLU reference files end on 2025-06-30. This screen cannot prove current 2026 behavior.",
            "",
        ]
    )
    return "\n".join(lines)


def render_recent_equity_leadership_stress_report(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    equity_summary: dict[str, Any],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    lines = [
        "# Forex Equity-Leadership Recent Stress",
        "",
        f"Generated at UTC: {generated}",
        "Status: EQUITY_LEADERSHIP_RECENT_STRESS_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay against public proxy data only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Purpose: stress the historical equity-leadership v0 candidates against recent public Yahoo ETF proxy data and recent public Yahoo FX proxy bars. This is recency triage, not broker-authoritative evidence.",
        "",
        f"Summary CSV: `{relative(summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Recent Equity-Leadership Context",
        "",
        f"- Source root: `{equity_summary['source_root']}`",
        f"- Rows: {equity_summary['rows']}",
        f"- Observation window: {equity_summary['start_utc'][:10]} through {equity_summary['end_utc'][:10]}",
        f"- Lookahead-safe availability through: {equity_summary['available_through_utc'][:10]}",
        f"- Lag policy: {equity_summary['lag_policy']}",
        f"- ACWX/SPY source: `{equity_summary['files'].get('acwx_spy', '')}`",
        f"- IWM/SPY source: `{equity_summary['files'].get('iwm_spy', '')}`",
        f"- XLF/XLU source: `{equity_summary['files'].get('xlf_xlu', '')}`",
        "",
        "## Cost Context",
        "",
        "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for symbol in ("EURUSD", "USDJPY"):
        cell = best_cell(cells, symbol, "H4")
        if cell:
            lines.append(
                f"| {symbol} | H4 | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Recent Proxy Results",
            "",
            "| candidate | symbol | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | recent_gate |",
            "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| {candidate_id} | {symbol} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                symbol=row["symbol"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "A recent proxy pass cannot approve an EA because both the ETF context and FX bars are public proxies and spreads are historical proxies. A failure or low-sample result lowers priority for broker-refresh work.",
            "",
        ]
    )
    return "\n".join(lines)


def render_sector_rotation_screen_report(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    sector_summary: dict[str, Any],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    overall = [row for row in rows if row.get("level") == "overall"]
    broker_rows = [row for row in rows if row.get("level") == "broker"]
    lines = [
        "# Forex Sector-Rotation Screen",
        "",
        f"Generated at UTC: {generated}",
        "Status: SECTOR_ROTATION_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Sector-rotation context: lagged daily ETF ratios for growth versus defensive leadership, cyclical/inflation leadership, and TIP/IEF inflation-linked bond leadership. Observations are shifted one day before joining to H4 bars.",
        "",
        f"Summary CSV: `{relative(summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Sector-Rotation Context",
        "",
        f"- Source root: `{sector_summary['source_root']}`",
        f"- Rows: {sector_summary['rows']}",
        f"- Observation window: {sector_summary['start_utc'][:10]} through {sector_summary['end_utc'][:10]}",
        f"- Lookahead-safe availability through: {sector_summary['available_through_utc'][:10]}",
        f"- Lag policy: {sector_summary['lag_policy']}",
        f"- Orientation: {sector_summary['orientation']}",
        f"- XLY/XLP source: `{sector_summary['files'].get('xly_xlp', '')}`",
        f"- QQQ/SPY source: `{sector_summary['files'].get('qqq_spy', '')}`",
        f"- XLE/XLU source: `{sector_summary['files'].get('xle_xlu', '')}`",
        f"- XLI/XLU source: `{sector_summary['files'].get('xli_xlu', '')}`",
        f"- XME/SPY source: `{sector_summary['files'].get('xme_spy', '')}`",
        f"- TIP/IEF source: `{sector_summary['files'].get('tip_ief', '')}`",
        "",
        "## Cost Context",
        "",
        "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for spec in candidate_specs_sector_rotation(pd.DataFrame()):
        cell = best_cell(cells, spec.symbol, spec.timeframe)
        if cell:
            lines.append(
                f"| {spec.symbol} | {spec.timeframe} | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Overall Results",
            "",
            "| candidate | symbol | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | final_gate |",
            "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in overall:
        lines.append(
            "| {candidate_id} | {symbol} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                symbol=row["symbol"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Broker Split", ""])
    lines.append("| candidate | broker | trades | net_R | expectancy_R | PF | maxDD_R | months+ |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for row in broker_rows:
        lines.append(
            "| {candidate_id} | {broker} | {trade_count} | {net:.2f} | {exp:.4f} | {pf} | {dd:.2f} | {pm}/{tm} |".format(
                candidate_id=row["candidate_id"],
                broker=row["broker"],
                trade_count=row["trade_count"],
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "Any `REJECT_SECTOR_ROTATION_*` result is rejected for this v0 screen. A watchlist result would still require refreshed 2026 broker bars and recent sector-rotation proxy confirmation before any demo-forward-test spec.",
            "",
            "Data caveat: the sector ETF reference files end on 2025-06-30. This screen cannot prove current 2026 behavior.",
            "",
        ]
    )
    return "\n".join(lines)


def render_recent_sector_rotation_stress_report(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    sector_summary: dict[str, Any],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    lines = [
        "# Forex Sector-Rotation Recent Stress",
        "",
        f"Generated at UTC: {generated}",
        "Status: SECTOR_ROTATION_RECENT_STRESS_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay against public proxy data only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Purpose: stress the historical sector-rotation v0 candidates against recent public Yahoo ETF proxy data and recent public Yahoo FX proxy bars. This is recency triage, not broker-authoritative evidence.",
        "",
        f"Summary CSV: `{relative(summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Recent Sector-Rotation Context",
        "",
        f"- Source root: `{sector_summary['source_root']}`",
        f"- Rows: {sector_summary['rows']}",
        f"- Observation window: {sector_summary['start_utc'][:10]} through {sector_summary['end_utc'][:10]}",
        f"- Lookahead-safe availability through: {sector_summary['available_through_utc'][:10]}",
        f"- Lag policy: {sector_summary['lag_policy']}",
        f"- XLY/XLP source: `{sector_summary['files'].get('xly_xlp', '')}`",
        f"- QQQ/SPY source: `{sector_summary['files'].get('qqq_spy', '')}`",
        f"- XLE/XLU source: `{sector_summary['files'].get('xle_xlu', '')}`",
        f"- XLI/XLU source: `{sector_summary['files'].get('xli_xlu', '')}`",
        f"- XME/SPY source: `{sector_summary['files'].get('xme_spy', '')}`",
        f"- TIP/IEF source: `{sector_summary['files'].get('tip_ief', '')}`",
        "",
        "## Cost Context",
        "",
        "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for spec in candidate_specs_sector_rotation(pd.DataFrame()):
        cell = best_cell(cells, spec.symbol, spec.timeframe)
        if cell:
            lines.append(
                f"| {spec.symbol} | {spec.timeframe} | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Recent Proxy Results",
            "",
            "| candidate | symbol | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | recent_gate |",
            "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| {candidate_id} | {symbol} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                symbol=row["symbol"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "A recent proxy pass cannot approve an EA because both the ETF context and FX bars are public proxies and spreads are historical proxies. A failure or low-sample result lowers priority for broker-refresh work.",
            "",
        ]
    )
    return "\n".join(lines)


def render_currency_basket_screen_report(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    currency_summary: dict[str, Any],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    overall = [row for row in rows if row.get("level") == "overall"]
    broker_rows = [row for row in rows if row.get("level") == "broker"]
    lines = [
        "# Forex Currency-Basket Screen",
        "",
        f"Generated at UTC: {generated}",
        "Status: CURRENCY_BASKET_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Currency-basket context: lagged daily FXA/UUP, FXF/UUP, and CYB/UUP ratios for non-USD/risk-currency pressure and Swiss-franc safe-haven rotation. Observations are shifted one day before joining to H4 bars.",
        "",
        f"Summary CSV: `{relative(summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Currency-Basket Context",
        "",
        f"- Source root: `{currency_summary['source_root']}`",
        f"- Rows: {currency_summary['rows']}",
        f"- Observation window: {currency_summary['start_utc'][:10]} through {currency_summary['end_utc'][:10]}",
        f"- Lookahead-safe availability through: {currency_summary['available_through_utc'][:10]}",
        f"- Lag policy: {currency_summary['lag_policy']}",
        f"- Orientation: {currency_summary['orientation']}",
        f"- FXA/UUP source: `{currency_summary['files'].get('fxa_uup', '')}`",
        f"- FXF/UUP source: `{currency_summary['files'].get('fxf_uup', '')}`",
        f"- CYB/UUP source: `{currency_summary['files'].get('cyb_uup', '')}`",
        "",
        "## Cost Context",
        "",
        "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for spec in candidate_specs_currency_basket(pd.DataFrame()):
        cell = best_cell(cells, spec.symbol, spec.timeframe)
        if cell:
            lines.append(
                f"| {spec.symbol} | {spec.timeframe} | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Overall Results",
            "",
            "| candidate | symbol | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | final_gate |",
            "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in overall:
        lines.append(
            "| {candidate_id} | {symbol} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                symbol=row["symbol"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Broker Split", ""])
    lines.append("| candidate | broker | trades | net_R | expectancy_R | PF | maxDD_R | months+ |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for row in broker_rows:
        lines.append(
            "| {candidate_id} | {broker} | {trade_count} | {net:.2f} | {exp:.4f} | {pf} | {dd:.2f} | {pm}/{tm} |".format(
                candidate_id=row["candidate_id"],
                broker=row["broker"],
                trade_count=row["trade_count"],
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "Any `REJECT_CURRENCY_BASKET_*` result is rejected for this v0 screen. A watchlist result would still require refreshed 2026 broker bars and recent currency-basket proxy confirmation before any demo-forward-test spec.",
            "",
            "Data caveat: the currency ETF reference files end on 2025-06-30. This screen cannot prove current 2026 behavior.",
            "",
        ]
    )
    return "\n".join(lines)


def render_recent_currency_basket_stress_report(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    currency_summary: dict[str, Any],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    lines = [
        "# Forex Currency-Basket Recent Stress",
        "",
        f"Generated at UTC: {generated}",
        "Status: CURRENCY_BASKET_RECENT_STRESS_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay against public proxy data only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Purpose: stress currency-basket v0 candidates whose required recent Yahoo currency ETF inputs are available against recent public Yahoo FX proxy bars. This is recency triage, not broker-authoritative evidence.",
        "",
        "Availability note: recent Yahoo CYB returned no usable daily rows during acquisition, so the EURUSD candidate that depends on CYB/UUP was not stressed in this pass.",
        "",
        f"Summary CSV: `{relative(summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Recent Currency-Basket Context",
        "",
        f"- Source root: `{currency_summary['source_root']}`",
        f"- Rows: {currency_summary['rows']}",
        f"- Observation window: {currency_summary['start_utc'][:10]} through {currency_summary['end_utc'][:10]}",
        f"- Lookahead-safe availability through: {currency_summary['available_through_utc'][:10]}",
        f"- Lag policy: {currency_summary['lag_policy']}",
        f"- FXA/UUP source: `{currency_summary['files'].get('fxa_uup', '')}`",
        f"- FXF/UUP source: `{currency_summary['files'].get('fxf_uup', '')}`",
        f"- CYB/UUP source: `{currency_summary['files'].get('cyb_uup', '')}`",
        "",
        "## Cost Context",
        "",
        "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    symbols = sorted({row["symbol"] for row in rows})
    for symbol in symbols:
        cell = best_cell(cells, symbol, "H4")
        if cell:
            lines.append(
                f"| {symbol} | H4 | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Recent Proxy Results",
            "",
            "| candidate | symbol | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | recent_gate |",
            "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| {candidate_id} | {symbol} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                symbol=row["symbol"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "A recent proxy pass cannot approve an EA because both the currency ETF context and FX bars are public proxies and spreads are historical proxies. A failure or low-sample result lowers priority for broker-refresh work.",
            "",
        ]
    )
    return "\n".join(lines)


def render_bond_vol_screen_report(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    bond_vol_summary: dict[str, Any],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    overall = [row for row in rows if row.get("level") == "overall"]
    broker_rows = [row for row in rows if row.get("level") == "broker"]
    lines = [
        "# Forex Bond-Volatility Screen",
        "",
        f"Generated at UTC: {generated}",
        "Status: BOND_VOL_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Bond-vol context: lagged daily MOVE bond-volatility proxy. Rising/elevated MOVE indicates Treasury-rate volatility stress; falling MOVE indicates rates-vol calm/carry relief. Observations are shifted one day before joining to H4 bars.",
        "",
        f"Summary CSV: `{relative(summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Bond-Vol Context",
        "",
        f"- Source root: `{bond_vol_summary['source_root']}`",
        f"- Rows: {bond_vol_summary['rows']}",
        f"- Observation window: {bond_vol_summary['start_utc'][:10]} through {bond_vol_summary['end_utc'][:10]}",
        f"- Lookahead-safe availability through: {bond_vol_summary['available_through_utc'][:10]}",
        f"- Lag policy: {bond_vol_summary['lag_policy']}",
        f"- Orientation: {bond_vol_summary['orientation']}",
        f"- MOVE source: `{bond_vol_summary['files'].get('move', '')}`",
        "",
        "## Cost Context",
        "",
        "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for symbol in ("EURUSD", "USDJPY"):
        cell = best_cell(cells, symbol, "H4")
        if cell:
            lines.append(
                f"| {symbol} | H4 | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Overall Results",
            "",
            "| candidate | family | symbol | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | final_gate |",
            "| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in overall:
        lines.append(
            "| {candidate_id} | {family} | {symbol} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                family=row["family"],
                symbol=row["symbol"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Broker Split", ""])
    lines.append("| candidate | broker | trades | net_R | expectancy_R | PF | maxDD_R | months+ |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for row in broker_rows:
        lines.append(
            "| {candidate_id} | {broker} | {trade_count} | {net:.2f} | {exp:.4f} | {pf} | {dd:.2f} | {pm}/{tm} |".format(
                candidate_id=row["candidate_id"],
                broker=row["broker"],
                trade_count=row["trade_count"],
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "Any `REJECT_BOND_VOL_*` result is rejected for this v0/v1 screen. A watchlist result would still require refreshed 2026 broker bars and recent bond-vol proxy confirmation before any demo-forward-test spec.",
            "",
            "Data caveat: the MOVE reference file ends on 2025-06-30. This screen cannot prove current 2026 behavior.",
            "",
        ]
    )
    return "\n".join(lines)


def render_recent_bond_vol_stress_report(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    bond_vol_summary: dict[str, Any],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    lines = [
        "# Forex Bond-Volatility Recent Stress",
        "",
        f"Generated at UTC: {generated}",
        "Status: BOND_VOL_RECENT_STRESS_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay against public proxy data only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Purpose: stress the historical USDJPY bond-vol Asia-session clue against recent public Yahoo MOVE proxy data and recent public Yahoo FX proxy bars. This is recency triage, not broker-authoritative evidence.",
        "",
        f"Summary CSV: `{relative(summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Recent Bond-Vol Context",
        "",
        f"- Source root: `{bond_vol_summary['source_root']}`",
        f"- Rows: {bond_vol_summary['rows']}",
        f"- Observation window: {bond_vol_summary['start_utc'][:10]} through {bond_vol_summary['end_utc'][:10]}",
        f"- Lookahead-safe availability through: {bond_vol_summary['available_through_utc'][:10]}",
        f"- Lag policy: {bond_vol_summary['lag_policy']}",
        f"- MOVE source: `{bond_vol_summary['files'].get('move', '')}`",
        "",
        "## Cost Context",
        "",
        "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for symbol in ("EURUSD", "USDJPY"):
        cell = best_cell(cells, symbol, "H4")
        if cell:
            lines.append(
                f"| {symbol} | H4 | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Recent Proxy Results",
            "",
            "| candidate | symbol | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | recent_gate |",
            "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| {candidate_id} | {symbol} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                symbol=row["symbol"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "A recent proxy pass cannot approve an EA because both the MOVE context and FX bars are public proxies and spreads are historical proxies. A failure or low-sample result lowers priority for broker-refresh work.",
            "",
        ]
    )
    return "\n".join(lines)


def render_crypto_risk_screen_report(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    crypto_summary: dict[str, Any],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    overall = [row for row in rows if row.get("level") == "overall"]
    broker_rows = [row for row in rows if row.get("level") == "broker"]
    lines = [
        "# Forex Crypto-Risk Screen",
        "",
        f"Generated at UTC: {generated}",
        "Status: CRYPTO_RISK_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Crypto-risk context: lagged daily BTC-USD proxy. Strong positive BTC momentum approximates crypto/risk appetite; sharp negative BTC momentum approximates crypto-risk stress. Observations are shifted one day before joining to H4 bars.",
        "",
        f"Historical summary CSV: `{relative(summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Context",
        "",
        f"- Source root: `{crypto_summary['source_root']}`",
        f"- Rows: {crypto_summary['rows']}",
        f"- Observation window: {crypto_summary['start_utc'][:10]} through {crypto_summary['end_utc'][:10]}",
        f"- Lookahead-safe availability through: {crypto_summary['available_through_utc'][:10]}",
        f"- Lag policy: {crypto_summary['lag_policy']}",
        f"- Orientation: {crypto_summary['orientation']}",
        f"- BTC source: `{crypto_summary['files'].get('btc', '')}`",
        "",
        "## Cost Context",
        "",
        "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for spec in candidate_specs_crypto_risk(pd.DataFrame()):
        cell = best_cell(cells, spec.symbol, spec.timeframe)
        if cell:
            lines.append(
                f"| {spec.symbol} | {spec.timeframe} | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Overall Results",
            "",
            "| candidate | symbol | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | final_gate |",
            "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in overall:
        lines.append(
            "| {candidate_id} | {symbol} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                symbol=row["symbol"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Broker Split", ""])
    lines.append("| candidate | broker | trades | net_R | expectancy_R | PF | maxDD_R | months+ |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for row in broker_rows:
        lines.append(
            "| {candidate_id} | {broker} | {trade_count} | {net:.2f} | {exp:.4f} | {pf} | {dd:.2f} | {pm}/{tm} |".format(
                candidate_id=row["candidate_id"],
                broker=row["broker"],
                trade_count=row["trade_count"],
                net=row["total_net_r"],
                exp=row["net_expectancy_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "Any `REJECT_CRYPTO_RISK_*` result is rejected for this v0 screen. A watchlist result would still require refreshed 2026 broker bars and recent BTC-risk proxy confirmation before any demo-forward-test spec.",
            "",
            "Data caveat: the BTC reference file ends around 2025-07. This screen cannot prove current 2026 behavior.",
            "",
        ]
    )
    return "\n".join(lines)


def render_recent_crypto_risk_stress_report(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    crypto_summary: dict[str, Any],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    lines = [
        "# Forex Crypto-Risk Recent Stress",
        "",
        f"Generated at UTC: {generated}",
        "Status: CRYPTO_RISK_RECENT_STRESS_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Purpose: stress the historical BTC crypto-risk v0 candidates against recent public Yahoo BTC proxy data and recent public Yahoo FX proxy bars. This is recency triage, not broker-authoritative evidence.",
        "",
        f"Recent summary CSV: `{relative(summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Context",
        "",
        f"- Source root: `{crypto_summary['source_root']}`",
        f"- Rows: {crypto_summary['rows']}",
        f"- Observation window: {crypto_summary['start_utc'][:10]} through {crypto_summary['end_utc'][:10]}",
        f"- Lookahead-safe availability through: {crypto_summary['available_through_utc'][:10]}",
        f"- Lag policy: {crypto_summary['lag_policy']}",
        f"- BTC source: `{crypto_summary['files'].get('btc', '')}`",
        "",
        "## Recent Proxy Results",
        "",
        "| candidate | symbol | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | recent_gate |",
        "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {candidate_id} | {symbol} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                symbol=row["symbol"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "A recent proxy pass cannot approve an EA because both the BTC context and FX bars are public proxies and spreads are historical proxies. A failure or low-sample result lowers priority for broker-refresh work.",
            "",
        ]
    )
    return "\n".join(lines)


def render_recent_commodity_dollar_stress_report(
    rows: list[dict[str, Any]],
    trade_map: dict[str, list[dict[str, Any]]],
    summary_path: Path,
    status_path: Path,
    cells: list[CostCell],
    commodity_summary: dict[str, Any],
    gates: dict[str, str],
) -> str:
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    lines = [
        "# Forex Commodity/Dollar Recent Stress",
        "",
        f"Generated at UTC: {generated}",
        "Status: COMMODITY_DOLLAR_RECENT_STRESS_RESEARCH_ONLY",
        "",
        "Boundary: offline Python replay against public proxy data only. No MT5 runtime, demo terminal, chart, preset, EA, order, or position was touched.",
        "",
        "Purpose: stress the historical USDJPY commodity/dollar clue against recent public Yahoo ETF proxy data and recent public Yahoo FX proxy bars. This is recency triage, not broker-authoritative evidence.",
        "",
        f"Summary CSV: `{relative(summary_path)}`",
        f"Status JSON: `{relative(status_path)}`",
        "",
        "## Recent Commodity/Dollar Context",
        "",
        f"- Source root: `{commodity_summary['source_root']}`",
        f"- Rows: {commodity_summary['rows']}",
        f"- Observation window: {commodity_summary['start_utc'][:10]} through {commodity_summary['end_utc'][:10]}",
        f"- Lookahead-safe availability through: {commodity_summary['available_through_utc'][:10]}",
        f"- Lag policy: {commodity_summary['lag_policy']}",
        f"- DBC/UUP source: `{commodity_summary['files'].get('dbc_uup', '')}`",
        f"- DBB/UUP source: `{commodity_summary['files'].get('dbb_uup', '')}`",
        "",
        "## Cost Context",
        "",
        "| symbol | timeframe | primary broker | p95_cost_R_recent | median_ATR14_points | p95_spread_points |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for symbol in ("EURUSD", "USDJPY"):
        cell = best_cell(cells, symbol, "H4")
        if cell:
            lines.append(
                f"| {symbol} | H4 | {cell.broker} | {cell.cost_r_recent_p95:.4f} | {cell.atr14_median_points:.2f} | {cell.spread_p95_points:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Recent Proxy Results",
            "",
            "| candidate | symbol | trades | L/S | win% | net_exp_R | total_net_R | PF | maxDD_R | med_cost_R | top_winner_removed_R | months+ | weeks+ | trades/yr | metric_decision | recent_gate |",
            "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| {candidate_id} | {symbol} | {trade_count} | {long_trades}/{short_trades} | {wr:.2f} | {exp:.4f} | {net:.2f} | {pf} | {dd:.2f} | {cost:.4f} | {top:.2f} | {pm}/{tm} | {pw}/{tw} | {tpy:.1f} | {decision} | {gate} |".format(
                candidate_id=row["candidate_id"],
                symbol=row["symbol"],
                trade_count=row["trade_count"],
                long_trades=row["long_trades"],
                short_trades=row["short_trades"],
                wr=row["win_rate_pct"],
                exp=row["net_expectancy_r"],
                net=row["total_net_r"],
                pf=display_float(row["profit_factor"], 4),
                dd=row["max_drawdown_r"],
                cost=row["median_cost_r"],
                top=row["top_winner_removed_net_r"],
                pm=row["positive_months"],
                tm=row["total_months"],
                pw=row["positive_weeks"],
                tw=row["total_weeks"],
                tpy=row["trades_per_year"],
                decision=row["decision"],
                gate=gates.get(row["candidate_id"], "UNKNOWN"),
            )
        )
    lines.extend(["", "## Direction And Session Split", ""])
    for candidate_id, trades in trade_map.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.append("| split | bucket | trades | net_R | expectancy_R |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for direction, direction_trades in grouped_trades(trades, "direction").items():
            net = [float(t["net_r"]) for t in direction_trades]
            lines.append(f"| direction | {direction} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        for session, session_trades in grouped_trades(trades, "session_utc").items():
            net = [float(t["net_r"]) for t in session_trades]
            lines.append(f"| session | {session} | {len(net)} | {sum(net):.2f} | {mean(net):.4f} |")
        lines.append("")
    lines.extend(
        [
            "## Read",
            "",
            "A recent proxy pass cannot approve an EA because both the ETF context and FX bars are public proxies and spreads are historical proxies. A failure or low-sample result lowers priority for broker-refresh work.",
            "",
        ]
    )
    return "\n".join(lines)


def recent_proxy_inventory(p: Paths) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    root = recent_proxy_root(p)
    for path in sorted(root.glob("*/*/*.csv")) if root.exists() else []:
        frame = pd.read_csv(path, usecols=["timestamp_utc", "symbol", "timeframe"])
        if frame.empty:
            continue
        timestamps = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce").dropna()
        if timestamps.empty:
            continue
        rows.append(
            {
                "symbol": str(frame["symbol"].iloc[0]),
                "timeframe": str(frame["timeframe"].iloc[0]),
                "rows": len(frame),
                "start_utc": timestamps.min().isoformat().replace("+00:00", "Z"),
                "end_utc": timestamps.max().isoformat().replace("+00:00", "Z"),
                "source_file": relative(path),
            }
        )
    return rows


def best_cell(cells: list[CostCell], symbol: str, timeframe: str) -> CostCell | None:
    eligible = [
        cell
        for cell in cells
        if cell.symbol == symbol and cell.timeframe == timeframe and cell.clean_ohlc and cell.has_spread
    ]
    if not eligible:
        return None
    return sorted(eligible, key=lambda cell: cell.cost_r_recent_p95)[0]


def grouped_trades(trades: list[dict[str, Any]], column: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for trade in trades:
        grouped.setdefault(str(trade[column]), []).append(trade)
    return dict(sorted(grouped.items()))


def display_float(value: float, places: int = 4) -> str:
    if isinstance(value, float) and math.isnan(value):
        return "n/a"
    if isinstance(value, float) and math.isinf(value):
        return "inf"
    return f"{value:.{places}f}"


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(repo_root_from_script())).replace("\\", "/")
    except ValueError:
        return str(path)


def iso(value: Any) -> str:
    return pd.Timestamp(value).isoformat().replace("+00:00", "Z")


def write_status_json(
    p: Paths,
    cells: list[CostCell],
    summary_rows: list[dict[str, Any]] | None = None,
    second_pass_rows: list[dict[str, Any]] | None = None,
    second_pass_gates: dict[str, str] | None = None,
) -> None:
    eligible = [
        cell
        for cell in cells
        if cell.clean_ohlc and cell.has_spread and not math.isnan(cell.cost_r_recent_p95)
    ]
    eligible.sort(key=lambda cell: cell.cost_r_recent_p95)
    overall = [row for row in (summary_rows or []) if row.get("level") == "overall"]
    second_overall = [row for row in (second_pass_rows or []) if row.get("level") == "overall"]
    status = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "lane": "forex-research",
        "status": "RESEARCH_ONLY",
        "runtime_touched": False,
        "clean_spread_cells": len(eligible),
        "top_cost_cells": [dataclass_row(cell) for cell in eligible[:10]],
        "first_screen_overall": [format_summary_row(row) for row in overall],
        "second_pass_overall": [format_summary_row(row) for row in second_overall],
        "second_pass_gates": second_pass_gates or {},
        "data_staleness_note": "Local processed Forex bars end around 2025-06/2025-07; not a 2026-current confirmation.",
    }
    (p.reports / f"FOREX_RESEARCH_STATUS_{RUN_DATE}.json").write_text(json.dumps(status, indent=2), encoding="utf-8")


def run_all() -> int:
    p = paths()
    ensure_dirs(p)
    cells = cost_geometry_scan(p)
    write_cost_outputs(p, cells)
    summary_rows, trade_map = run_first_screen(p, cells)
    write_screen_outputs(p, summary_rows, trade_map, cells)
    second_rows, second_trade_map = run_second_pass_screen(p, cells)
    second_gates = write_second_pass_outputs(p, second_rows, second_trade_map, cells)
    write_status_json(p, cells, summary_rows, second_rows, second_gates)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Forex research-only cost scan and candidate screens.")
    parser.add_argument(
        "command",
        choices=(
            "cost-scan",
            "first-screen",
            "second-pass",
            "recent-proxy-acquire",
            "recent-commodity-proxy-acquire",
            "recent-real-asset-rotation-proxy-acquire",
            "recent-haven-liquidity-proxy-acquire",
            "recent-rates-proxy-acquire",
            "recent-equity-leadership-proxy-acquire",
            "recent-sector-rotation-proxy-acquire",
            "recent-currency-basket-proxy-acquire",
            "recent-bond-vol-proxy-acquire",
            "recent-crypto-risk-proxy-acquire",
            "cot-financial-acquire",
            "recent-proxy-stress",
            "macro-screen",
            "treasury-curve-screen",
            "cny-dollar-screen",
            "calendar-session-screen",
            "weekly-structure-screen",
            "financial-liquidity-screen",
            "cot-positioning-screen",
            "global-risk-screen",
            "commodity-dollar-screen",
            "real-asset-rotation-screen",
            "haven-liquidity-screen",
            "rates-dollar-screen",
            "equity-leadership-screen",
            "sector-rotation-screen",
            "currency-basket-screen",
            "bond-vol-screen",
            "crypto-risk-screen",
            "commodity-dollar-recent-stress",
            "real-asset-rotation-recent-stress",
            "haven-liquidity-recent-stress",
            "rates-dollar-recent-stress",
            "equity-leadership-recent-stress",
            "sector-rotation-recent-stress",
            "currency-basket-recent-stress",
            "bond-vol-recent-stress",
            "crypto-risk-recent-stress",
            "broker-refresh-validate",
            "broker-refresh-retest",
            "external-flow-screen",
            "risk-regime-screen",
            "fx-cross-screen",
            "all",
        ),
    )
    args = parser.parse_args(argv)
    p = paths()
    ensure_dirs(p)
    if args.command == "recent-proxy-acquire":
        acquire_recent_yahoo_proxy(p)
        return 0
    if args.command == "recent-commodity-proxy-acquire":
        acquire_recent_commodity_dollar_proxy(p)
        return 0
    if args.command == "recent-real-asset-rotation-proxy-acquire":
        acquire_recent_real_asset_rotation_proxy(p)
        return 0
    if args.command == "recent-haven-liquidity-proxy-acquire":
        acquire_recent_haven_liquidity_proxy(p)
        return 0
    if args.command == "recent-rates-proxy-acquire":
        acquire_recent_rates_dollar_proxy(p)
        return 0
    if args.command == "recent-equity-leadership-proxy-acquire":
        acquire_recent_equity_leadership_proxy(p)
        return 0
    if args.command == "recent-sector-rotation-proxy-acquire":
        acquire_recent_sector_rotation_proxy(p)
        return 0
    if args.command == "recent-currency-basket-proxy-acquire":
        acquire_recent_currency_basket_proxy(p)
        return 0
    if args.command == "recent-bond-vol-proxy-acquire":
        acquire_recent_bond_vol_proxy(p)
        return 0
    if args.command == "recent-crypto-risk-proxy-acquire":
        acquire_recent_crypto_risk_proxy(p)
        return 0
    if args.command == "cot-financial-acquire":
        acquire_cot_financial_reports(p)
        return 0
    if args.command == "broker-refresh-validate":
        validate_broker_refresh(p)
        return 0
    if args.command == "broker-refresh-retest":
        run_broker_refresh_retest(p)
        return 0
    cells = cost_geometry_scan(p)
    if args.command == "cost-scan":
        write_cost_outputs(p, cells)
        write_status_json(p, cells)
        return 0
    if args.command == "first-screen":
        summary_rows, trade_map = run_first_screen(p, cells)
        write_screen_outputs(p, summary_rows, trade_map, cells)
        write_status_json(p, cells, summary_rows)
        return 0
    if args.command == "second-pass":
        second_rows, second_trade_map = run_second_pass_screen(p, cells)
        second_gates = write_second_pass_outputs(p, second_rows, second_trade_map, cells)
        write_status_json(p, cells, second_pass_rows=second_rows, second_pass_gates=second_gates)
        return 0
    if args.command == "recent-proxy-stress":
        recent_rows, recent_trade_map = run_recent_proxy_stress(p, cells)
        write_recent_proxy_stress_outputs(p, recent_rows, recent_trade_map, cells)
        return 0
    if args.command == "macro-screen":
        historical_rows, historical_trade_map, recent_rows, recent_trade_map, macro_summary = run_macro_screen(p, cells)
        write_macro_screen_outputs(p, historical_rows, historical_trade_map, recent_rows, recent_trade_map, macro_summary)
        return 0
    if args.command == "treasury-curve-screen":
        historical_rows, historical_trade_map, recent_rows, recent_trade_map, curve_summary = run_treasury_curve_screen(
            p, cells
        )
        write_treasury_curve_screen_outputs(
            p,
            historical_rows,
            historical_trade_map,
            recent_rows,
            recent_trade_map,
            cells,
            curve_summary,
        )
        return 0
    if args.command == "cny-dollar-screen":
        historical_rows, historical_trade_map, recent_rows, recent_trade_map, cny_summary = run_cny_pressure_screen(p, cells)
        write_cny_pressure_screen_outputs(p, historical_rows, historical_trade_map, recent_rows, recent_trade_map, cells, cny_summary)
        return 0
    if args.command == "calendar-session-screen":
        historical_rows, historical_trade_map, recent_rows, recent_trade_map = run_calendar_session_screen(p, cells)
        write_calendar_session_screen_outputs(p, historical_rows, historical_trade_map, recent_rows, recent_trade_map, cells)
        return 0
    if args.command == "weekly-structure-screen":
        historical_rows, historical_trade_map, recent_rows, recent_trade_map = run_weekly_structure_screen(p, cells)
        write_weekly_structure_screen_outputs(p, historical_rows, historical_trade_map, recent_rows, recent_trade_map, cells)
        return 0
    if args.command == "financial-liquidity-screen":
        historical_rows, historical_trade_map, recent_rows, recent_trade_map, financial_summary = run_financial_liquidity_screen(p, cells)
        write_financial_liquidity_screen_outputs(
            p,
            historical_rows,
            historical_trade_map,
            recent_rows,
            recent_trade_map,
            cells,
            financial_summary,
        )
        return 0
    if args.command == "cot-positioning-screen":
        historical_rows, historical_trade_map, recent_rows, recent_trade_map, cot_summary = run_cot_positioning_screen(p, cells)
        write_cot_positioning_screen_outputs(
            p,
            historical_rows,
            historical_trade_map,
            recent_rows,
            recent_trade_map,
            cells,
            cot_summary,
        )
        return 0
    if args.command == "global-risk-screen":
        global_rows, global_trade_map, global_summary = run_global_risk_screen(p, cells)
        write_global_risk_screen_outputs(p, global_rows, global_trade_map, cells, global_summary)
        return 0
    if args.command == "commodity-dollar-screen":
        commodity_rows, commodity_trade_map, commodity_summary = run_commodity_dollar_screen(p, cells)
        write_commodity_dollar_screen_outputs(p, commodity_rows, commodity_trade_map, cells, commodity_summary)
        return 0
    if args.command == "real-asset-rotation-screen":
        real_asset_rows, real_asset_trade_map, real_asset_summary = run_real_asset_rotation_screen(p, cells)
        write_real_asset_rotation_screen_outputs(p, real_asset_rows, real_asset_trade_map, cells, real_asset_summary)
        return 0
    if args.command == "haven-liquidity-screen":
        haven_rows, haven_trade_map, haven_summary = run_haven_liquidity_screen(p, cells)
        write_haven_liquidity_screen_outputs(p, haven_rows, haven_trade_map, cells, haven_summary)
        return 0
    if args.command == "rates-dollar-screen":
        rates_rows, rates_trade_map, rates_summary = run_rates_dollar_screen(p, cells)
        write_rates_dollar_screen_outputs(p, rates_rows, rates_trade_map, cells, rates_summary)
        return 0
    if args.command == "equity-leadership-screen":
        equity_rows, equity_trade_map, equity_summary = run_equity_leadership_screen(p, cells)
        write_equity_leadership_screen_outputs(p, equity_rows, equity_trade_map, cells, equity_summary)
        return 0
    if args.command == "sector-rotation-screen":
        sector_rows, sector_trade_map, sector_summary = run_sector_rotation_screen(p, cells)
        write_sector_rotation_screen_outputs(p, sector_rows, sector_trade_map, cells, sector_summary)
        return 0
    if args.command == "currency-basket-screen":
        currency_rows, currency_trade_map, currency_summary = run_currency_basket_screen(p, cells)
        write_currency_basket_screen_outputs(p, currency_rows, currency_trade_map, cells, currency_summary)
        return 0
    if args.command == "bond-vol-screen":
        bond_vol_rows, bond_vol_trade_map, bond_vol_summary = run_bond_vol_screen(p, cells)
        write_bond_vol_screen_outputs(p, bond_vol_rows, bond_vol_trade_map, cells, bond_vol_summary)
        return 0
    if args.command == "crypto-risk-screen":
        crypto_rows, crypto_trade_map, crypto_summary = run_crypto_risk_screen(p, cells)
        write_crypto_risk_screen_outputs(p, crypto_rows, crypto_trade_map, cells, crypto_summary)
        return 0
    if args.command == "commodity-dollar-recent-stress":
        commodity_rows, commodity_trade_map, commodity_summary = run_recent_commodity_dollar_stress(p, cells)
        write_recent_commodity_dollar_stress_outputs(p, commodity_rows, commodity_trade_map, cells, commodity_summary)
        return 0
    if args.command == "real-asset-rotation-recent-stress":
        real_asset_rows, real_asset_trade_map, real_asset_summary = run_recent_real_asset_rotation_stress(p, cells)
        write_recent_real_asset_rotation_stress_outputs(p, real_asset_rows, real_asset_trade_map, cells, real_asset_summary)
        return 0
    if args.command == "haven-liquidity-recent-stress":
        haven_rows, haven_trade_map, haven_summary = run_recent_haven_liquidity_stress(p, cells)
        write_recent_haven_liquidity_stress_outputs(p, haven_rows, haven_trade_map, cells, haven_summary)
        return 0
    if args.command == "rates-dollar-recent-stress":
        rates_rows, rates_trade_map, rates_summary = run_recent_rates_dollar_stress(p, cells)
        write_recent_rates_dollar_stress_outputs(p, rates_rows, rates_trade_map, cells, rates_summary)
        return 0
    if args.command == "equity-leadership-recent-stress":
        equity_rows, equity_trade_map, equity_summary = run_recent_equity_leadership_stress(p, cells)
        write_recent_equity_leadership_stress_outputs(p, equity_rows, equity_trade_map, cells, equity_summary)
        return 0
    if args.command == "sector-rotation-recent-stress":
        sector_rows, sector_trade_map, sector_summary = run_recent_sector_rotation_stress(p, cells)
        write_recent_sector_rotation_stress_outputs(p, sector_rows, sector_trade_map, cells, sector_summary)
        return 0
    if args.command == "currency-basket-recent-stress":
        currency_rows, currency_trade_map, currency_summary = run_recent_currency_basket_stress(p, cells)
        write_recent_currency_basket_stress_outputs(p, currency_rows, currency_trade_map, cells, currency_summary)
        return 0
    if args.command == "bond-vol-recent-stress":
        bond_vol_rows, bond_vol_trade_map, bond_vol_summary = run_recent_bond_vol_stress(p, cells)
        write_recent_bond_vol_stress_outputs(p, bond_vol_rows, bond_vol_trade_map, cells, bond_vol_summary)
        return 0
    if args.command == "crypto-risk-recent-stress":
        crypto_rows, crypto_trade_map, crypto_summary = run_recent_crypto_risk_stress(p, cells)
        write_recent_crypto_risk_stress_outputs(p, crypto_rows, crypto_trade_map, cells, crypto_summary)
        return 0
    if args.command == "external-flow-screen":
        flow_rows, flow_trade_map, flow_summary = run_external_flow_screen(p, cells)
        write_external_flow_screen_outputs(p, flow_rows, flow_trade_map, cells, flow_summary)
        return 0
    if args.command == "risk-regime-screen":
        risk_rows, risk_trade_map, risk_recent_rows, risk_recent_trade_map, risk_summary = run_risk_regime_screen(p, cells)
        write_risk_regime_screen_outputs(p, risk_rows, risk_trade_map, risk_recent_rows, risk_recent_trade_map, cells, risk_summary)
        return 0
    if args.command == "fx-cross-screen":
        cross_rows, cross_trade_map, cross_summary = run_fx_cross_screen(p, cells)
        write_fx_cross_screen_outputs(p, cross_rows, cross_trade_map, cells, cross_summary)
        return 0
    return run_all()


if __name__ == "__main__":
    raise SystemExit(main())

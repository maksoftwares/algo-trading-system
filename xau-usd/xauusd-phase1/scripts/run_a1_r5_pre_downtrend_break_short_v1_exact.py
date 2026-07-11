"""Run the single preregistered R5 short cell over exact five-/ten-year MT5 windows."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import re
import shutil
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

import run_a1_r1_pullback_long_v1_exact as r1
import run_a1_xau_extended_horizon_exact as extended
import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_owner_goal_step3_portfolio_composition import REPORTS_DIR
from run_a1_h4_d1_geometry_v2_weekly_shape import sha256_file
from run_a1_regime_router_v1_exact import ROUTER_INPUTS


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_R5_PRE_DOWNTREND_BREAK_SHORT_V1_PREREG_2026_07_11.md"
OUTPUT_STEM = "A1_XAU_R5_PRE_DOWNTREND_BREAK_SHORT_V1_EXACT_20260711"
DEFAULT_OUTPUT_DIR = REPORTS_DIR / OUTPUT_STEM
DEFAULT_H4_DEAL_LOG = (
    REPORTS_DIR
    / "A1_XAU_EXTENDED_HORIZON_EXACT_20260711"
    / "runs"
    / "ten_year"
    / "h4_d1_long_best_box2_atr80"
    / "a1_xau_extended_h4_d1_long_best_box2_atr80_ten_year_deals_with_fee.csv"
)
COMMON_WINDOW_START = datetime(2022, 7, 1)
COMMON_WINDOW_END = datetime(2026, 6, 30, 23, 59, 59)
TEN_YEAR_SPLIT = datetime(2021, 7, 1)
SHARED_WRITE_CONFIG = a1.write_config
LEGACY_CURRENCY_FIELD_NOTE = (
    "Raw shared-parser fields named profit_aed or pnl_aed contain tester-currency USD values in this packet; "
    "the names are retained only for backward-compatible schema consumption."
)


@dataclass(frozen=True)
class Horizon:
    name: str
    from_date: str
    to_date: str
    minimum_trades: int


HORIZONS = (
    Horizon("five_year", "2021.07.01", "2026.06.30", 75),
    Horizon("ten_year", "2016.07.01", "2026.06.30", 150),
)


R5_INPUTS = {
    **ROUTER_INPUTS,
    "InpRegimeRouterMode": "5",
    "InpDirectionMode": "2",
    "InpSignalMode": "19",
    "InpRiskReward": "2.00",
    "InpFixedLots": "0.01",
    "InpUseRiskNormalizedLots": "false",
    "InpRiskAmountUsd": "0.00",
    "InpMaxSpreadPoints": "75",
    "InpMaxEstimatedCostR": "0.05",
    "InpMaxTradesPerDay": "1",
    "InpCooldownMinutes": "0",
    "InpOnePositionPerMagic": "true",
    "InpMaxOpenPositionsPerMagic": "1",
    "InpPortfolioDailyGuardEnabled": "false",
    "InpBlockedEntryHoursCsv": "",
    "InpBlockedEntryDayHoursCsv": "",
    "InpBlockedLongEntryHoursCsv": "",
    "InpBlockedShortEntryHoursCsv": "",
    "InpUseDirectionalSessionFilter": "false",
    "InpUseH1TrendFilter": "false",
    "InpUseH4TrendFilter": "false",
    "InpH4D1SupportiveStateGuardEnabled": "false",
    "InpH4D1WeeklyLossGovernorEnabled": "false",
    "InpH4D1PrevMonthHealthGateEnabled": "false",
    "InpH4D1NegativeStackGuardEnabled": "false",
    "InpH4D1ThirdEntryQualityGateEnabled": "false",
    "InpD1SupportStateGateMode": "0",
    "InpD1StructuralDownGateEnabled": "false",
    "InpFeatureLossFilterEnabled": "false",
    "InpR2PullbackM5ExecutionBodyFilterEnabled": "false",
    "InpSignalClaimEnabled": "false",
    "InpRegimeSnapshotLogEnabled": "false",
    "InpProfitProtectionEnabled": "false",
    "InpPartialCloseEnabled": "false",
    "InpSplitEntryEnabled": "false",
    "InpEarlyAdverseExitEnabled": "false",
    "InpBreakAtrMultiple": "0.00",
    "InpMinRangeAtr": "0.00",
    "InpMinBodyFraction": "0.00",
    "InpMinThreeBarMoveAtr": "0.00",
    "InpMinAtrAbsoluteForEntry": "0.00",
    "InpMaxThreeBarMoveAtr": "0.00",
    "InpMinBreakDistanceAtr": "0.00",
    "InpMaxBreakDistanceAtr": "0.00",
    "InpBearRetestLookbackBars": "10",
    "InpBearRetestSupportLookbackBars": "12",
    "InpBearRetestBreakAtr": "0.10",
    "InpBearRetestTouchAtr": "0.05",
    "InpBearRetestReclaimAtr": "0.05",
    "InpBearRetestStopBufferAtr": "0.25",
    "InpBearRetestMinBodyFraction": "0.55",
    "InpShortCloseLocation": "0.25",
    "InpBearImpulseRetestImpulseBars": "3",
    "InpBearImpulseRetestMinImpulseAtr": "1.50",
    "InpBearImpulseRetestBreakMinBodyFraction": "0.55",
    "InpStopFloorPoints": "350",
    "InpStopCeilingPoints": "1000",
    "InpStopCapPoints": "0",
}

ALLOWED_R5_ORDER_TAGS = {
    "regime_router_allow_short_r5_uptrend_chop_only_state_uptrend",
    "regime_router_allow_short_r5_uptrend_chop_only_state_chop",
}
POST_ROUTER_VALID_SIGNAL_BLOCKS = {
    "daily_trade_cap_reached",
    "own_position_exists",
    "max_open_positions_reached",
}


def require_file(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)


def stable_hash(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def portable_source_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(PHASE1_ROOT.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def compile_result(log_text: str) -> tuple[int, int]:
    match = re.search(r"Result:\s*(\d+)\s+errors?,\s*(\d+)\s+warnings?", log_text, flags=re.IGNORECASE)
    if match is None:
        match = re.search(r"(\d+)\s+error\(s\),\s*(\d+)\s+warning\(s\)", log_text, flags=re.IGNORECASE)
    if match is None:
        raise RuntimeError("MetaEditor compile log has no recognized error/warning result")
    return int(match.group(1)), int(match.group(2))


def compile_ea_fail_closed(backtest_root: Path, metaeditor: Path) -> Path:
    """Compile R5 from source after deleting the old EX5; stale binaries cannot pass."""
    require_file(metaeditor)
    experts = backtest_root / "MQL5" / "Experts"
    experts.mkdir(parents=True, exist_ok=True)
    target = experts / f"{a1.EA_NAME}.mq5"
    ex5 = experts / f"{a1.EA_NAME}.ex5"
    log = backtest_root / "Logs" / f"compile_{a1.EA_NAME}_r5_exact_20260711.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(a1.EA_SOURCE, target)
    if ex5.exists():
        ex5.unlink()
    if log.exists():
        log.unlink()
    completed = subprocess.run(
        [str(metaeditor), f"/compile:{target}", f"/log:{log}"],
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    if not log.is_file():
        raise RuntimeError(f"MetaEditor produced no R5 compile log (return code {completed.returncode})")
    errors, warnings = compile_result(a1.read_text(log))
    if errors != 0 or warnings != 0:
        raise RuntimeError(f"R5 compile was not clean: {errors} errors, {warnings} warnings; log={log}")
    if not ex5.is_file() or ex5.stat().st_size <= 0:
        raise RuntimeError(f"MetaEditor did not produce a fresh R5 EX5: {ex5}")
    return log


def tester_only_config_text(text: str) -> str:
    marker = "[Tester]"
    index = text.find(marker)
    if index < 0:
        raise RuntimeError("R5 tester config has no [Tester] section")
    safe = text[index:]
    sections = re.findall(r"^\[([^\]]+)\]\s*$", safe, flags=re.MULTILINE)
    if sections != ["Tester", "TesterInputs"]:
        raise RuntimeError("R5 tester config contains an unsafe or incomplete section set")
    forbidden = {"Login", "Server", "Password", "ProxyEnable"}
    for raw in safe.splitlines():
        if "=" in raw and raw.split("=", 1)[0].strip() in forbidden:
            raise RuntimeError(f"R5 tester config contains account/session key: {raw!r}")
    return safe


def write_config_tester_only(*args: Any, **kwargs: Any) -> Path:
    path = SHARED_WRITE_CONFIG(*args, **kwargs)
    safe = tester_only_config_text(path.read_text(encoding="utf-8-sig"))
    path.write_text(safe, encoding="utf-8", newline="\n")
    return path


def run_variants_fail_closed(**kwargs: Any) -> dict[str, Any]:
    original_compile = a1.compile_ea
    original_write_config = a1.write_config
    a1.compile_ea = compile_ea_fail_closed
    a1.write_config = write_config_tester_only
    try:
        return a1.run_variants(**kwargs)
    finally:
        a1.compile_ea = original_compile
        a1.write_config = original_write_config


def build_variant() -> a1.Variant:
    return a1.Variant(
        name="r5_upchop_downside_impulse_retest_q55_v1",
        label="R5 causal UPTREND/CHOP q55 downside impulse/retest short, fixed 0.01 lot and 2R",
        run_id="BT_A1_XAU_R5_UPCHOP_DOWNSIDE_IMPULSE_RETEST_Q55_V1",
        tester_inputs=dict(R5_INPUTS),
    )


def static_checks(variant: a1.Variant) -> dict[str, bool]:
    blank_masks = (
        "InpBlockedEntryHoursCsv",
        "InpBlockedEntryDayHoursCsv",
        "InpBlockedLongEntryHoursCsv",
        "InpBlockedShortEntryHoursCsv",
    )
    disabled_filters = (
        "InpPortfolioDailyGuardEnabled",
        "InpUseDirectionalSessionFilter",
        "InpUseH1TrendFilter",
        "InpUseH4TrendFilter",
        "InpH4D1SupportiveStateGuardEnabled",
        "InpH4D1WeeklyLossGovernorEnabled",
        "InpH4D1PrevMonthHealthGateEnabled",
        "InpH4D1NegativeStackGuardEnabled",
        "InpH4D1ThirdEntryQualityGateEnabled",
        "InpD1StructuralDownGateEnabled",
        "InpFeatureLossFilterEnabled",
        "InpR2PullbackM5ExecutionBodyFilterEnabled",
        "InpSignalClaimEnabled",
        "InpRegimeSnapshotLogEnabled",
        "InpProfitProtectionEnabled",
        "InpPartialCloseEnabled",
        "InpSplitEntryEnabled",
        "InpEarlyAdverseExitEnabled",
    )
    inputs = variant.tester_inputs
    return {
        "one_preregistered_variant": variant.name == "r5_upchop_downside_impulse_retest_q55_v1",
        "router_mode_5": inputs.get("InpRegimeRouterMode") == "5",
        "short_only": inputs.get("InpDirectionMode") == "2",
        "signal_mode_19": inputs.get("InpSignalMode") == "19",
        "fixed_lot_0p01": inputs.get("InpFixedLots") == "0.01" and inputs.get("InpUseRiskNormalizedLots") == "false",
        "fixed_rr_2": inputs.get("InpRiskReward") == "2.00",
        "one_entry_per_day": inputs.get("InpMaxTradesPerDay") == "1",
        "one_position": inputs.get("InpOnePositionPerMagic") == "true" and inputs.get("InpMaxOpenPositionsPerMagic") == "1",
        "spread_75_cost_0p05": inputs.get("InpMaxSpreadPoints") == "75" and inputs.get("InpMaxEstimatedCostR") == "0.05",
        "stop_floor_350_ceiling_1000_no_cap": (
            inputs.get("InpStopFloorPoints") == "350"
            and inputs.get("InpStopCeilingPoints") == "1000"
            and inputs.get("InpStopCapPoints") == "0"
        ),
        "q55_quality_locked": (
            inputs.get("InpBearRetestMinBodyFraction") == "0.55"
            and inputs.get("InpShortCloseLocation") == "0.25"
            and inputs.get("InpBearImpulseRetestMinImpulseAtr") == "1.50"
            and inputs.get("InpBearImpulseRetestBreakMinBodyFraction") == "0.55"
        ),
        "no_hour_day_masks": all(inputs.get(key) == "" for key in blank_masks),
        "no_addon_filters_or_management": all(inputs.get(key) == "false" for key in disabled_filters)
        and inputs.get("InpD1SupportStateGateMode") == "0",
        "no_extra_atr_or_break_bands": (
            inputs.get("InpBreakAtrMultiple") == "0.00"
            and inputs.get("InpMinRangeAtr") == "0.00"
            and inputs.get("InpMinBodyFraction") == "0.00"
            and inputs.get("InpMinThreeBarMoveAtr") == "0.00"
            and inputs.get("InpMinAtrAbsoluteForEntry") == "0.00"
            and inputs.get("InpMaxThreeBarMoveAtr") == "0.00"
            and inputs.get("InpMinBreakDistanceAtr") == "0.00"
            and inputs.get("InpMaxBreakDistanceAtr") == "0.00"
        ),
    }


def parse_tester_inputs(path: Path) -> dict[str, str]:
    section = ""
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith((";", "#")):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            continue
        if section == "TesterInputs" and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def number(value: Any) -> float:
    text = str(value or "0").replace(" ", "").replace(",", "")
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    return float(match.group(0)) if match else 0.0


def percent(value: Any) -> float:
    matches = re.findall(r"([-+]?\d+(?:\.\d+)?)\s*%", str(value or ""))
    if not matches:
        raise RuntimeError(f"Missing percentage metric: {value!r}")
    return float(matches[-1])


def parse_time(value: Any) -> datetime:
    text = str(value or "").strip()
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return datetime.fromisoformat(text)


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.is_file() or path.stat().st_size == 0:
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def compress_signal_log(path: Path) -> dict[str, Any]:
    """Retain a deterministic compressed signal ledger without committing 100MB+ CSVs."""
    require_file(path)
    destination = path.with_suffix(path.suffix + ".gz")
    original_sha256 = sha256_file(path)
    original_bytes = path.stat().st_size
    with path.open("rb") as source, destination.open("wb") as raw_destination:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_destination, mtime=0) as compressed:
            shutil.copyfileobj(source, compressed, length=1024 * 1024)
    path.unlink()
    return {
        "path": str(destination),
        "uncompressed_bytes": original_bytes,
        "uncompressed_sha256": original_sha256,
        "compressed_bytes": destination.stat().st_size,
        "compressed_sha256": sha256_file(destination),
    }


def trade_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows = r1.mt5_rows(result, source_priority=125)
    for row in rows:
        row["component"] = "r5_pre_downtrend_break_short_v1"
        row["source_id"] = "r5_pre_downtrend_break_short_v1"
        row["family_group"] = "xau_r5_pre_downtrend_break_short"
        row["cell_id"] = "r5_upchop_downside_impulse_retest_q55_v1"
    return rows


def pnl_metrics(rows: Sequence[dict[str, Any]], *, cost_per_trade: float = 0.0) -> dict[str, Any]:
    pnls = [float(row["pnl_usd"]) - cost_per_trade for row in rows]
    wins = [value for value in pnls if value > 0.0]
    losses = [value for value in pnls if value < 0.0]
    gross_profit = sum(wins)
    gross_loss = -sum(losses)
    avg_win = gross_profit / len(wins) if wins else 0.0
    avg_loss = gross_loss / len(losses) if losses else 0.0
    equity = 0.0
    peak = 0.0
    maximum_dd = 0.0
    ordered = sorted(rows, key=lambda row: (row["exit_time"], row["entry_time"], row.get("source_row", 0)))
    for row in ordered:
        equity += float(row["pnl_usd"]) - cost_per_trade
        peak = max(peak, equity)
        maximum_dd = max(maximum_dd, peak - equity)
    return {
        "trades": len(rows),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round(100.0 * len(wins) / len(rows), 4) if rows else 0.0,
        "realized_win_loss": round(avg_win / avg_loss, 6) if avg_loss else None,
        "profit_factor": round(gross_profit / gross_loss, 6) if gross_loss else None,
        "net_usd": round(sum(pnls), 2),
        "max_closed_drawdown_usd": round(maximum_dd, 2),
    }


def concentration_metrics(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    net = sum(float(row["pnl_usd"]) for row in rows)
    top_wins = sorted((float(row["pnl_usd"]) for row in rows if float(row["pnl_usd"]) > 0.0), reverse=True)
    by_entry_day: defaultdict[date, float] = defaultdict(float)
    for row in rows:
        by_entry_day[row["entry_date"]] += float(row["pnl_usd"])
    best_days = sorted(((day, value) for day, value in by_entry_day.items() if value > 0.0), key=lambda item: item[1], reverse=True)
    return {
        "top10_winning_trades_removed_net_usd": round(net - sum(top_wins[:10]), 2),
        "top3_winning_entry_days_removed_net_usd": round(net - sum(value for _day, value in best_days[:3]), 2),
        "top3_winning_entry_days": [
            {"date": day.isoformat(), "net_usd": round(value, 2)} for day, value in best_days[:3]
        ],
    }


def ten_equal_year_buckets(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    # The exact horizon starts on July 1. Ten July-June buckets avoid treating the
    # two half-calendar boundary years as if they were complete annual observations.
    output: list[dict[str, Any]] = []
    for offset in range(10):
        start = datetime(2016 + offset, 7, 1)
        end = datetime(2017 + offset, 7, 1)
        selected = [row for row in rows if start <= row["exit_time"] < end]
        output.append(
            {
                "bucket": f"{start:%Y-%m-%d}/{(end.date()):%Y-%m-%d}",
                **pnl_metrics(selected),
            }
        )
    return output


def calendar_year_rows(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: defaultdict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["exit_time"].year].append(row)
    return [{"year": year, **pnl_metrics(grouped[year])} for year in sorted(grouped)]


def daily_pnl(rows: Iterable[dict[str, Any]], pnl_key: str = "pnl_usd") -> dict[date, float]:
    output: defaultdict[date, float] = defaultdict(float)
    for row in rows:
        exit_value = row["exit_time"]
        exit_day = exit_value.date() if isinstance(exit_value, datetime) else parse_time(exit_value).date()
        output[exit_day] += float(row[pnl_key])
    return dict(output)


def pearson_daily_pnl(left: dict[date, float], right: dict[date, float]) -> float | None:
    days = sorted(set(left) | set(right))
    if len(days) < 2:
        return None
    xs = [left.get(day, 0.0) for day in days]
    ys = [right.get(day, 0.0) for day in days]
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    x_var = sum((value - x_mean) ** 2 for value in xs)
    y_var = sum((value - y_mean) ** 2 for value in ys)
    if x_var <= 0.0 or y_var <= 0.0:
        return None
    covariance = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys, strict=True))
    return round(covariance / math.sqrt(x_var * y_var), 6)


def merge_exposure_episodes(h4_trades: Sequence[dict[str, Any]]) -> list[tuple[datetime, datetime]]:
    intervals = sorted((parse_time(row["entry_time"]), parse_time(row["exit_time"])) for row in h4_trades)
    episodes: list[list[datetime]] = []
    for start, end in intervals:
        if not episodes or start > episodes[-1][1]:
            episodes.append([start, end])
        else:
            episodes[-1][1] = max(episodes[-1][1], end)
    return [(start, end) for start, end in episodes]


def touched_episode_count(times: Iterable[datetime], episodes: Sequence[tuple[datetime, datetime]]) -> int:
    unique_times = sorted(set(times))
    return sum(any(start <= timestamp <= end for timestamp in unique_times) for start, end in episodes)


def valid_signal_times(order_rows: Sequence[dict[str, str]]) -> list[datetime]:
    times: set[datetime] = set()
    for row in order_rows:
        action = row.get("action", "")
        reason = row.get("reason", "")
        if action in {"ORDER_SEND_OK", "ORDER_SEND_FAIL"} or (
            action == "GUARD_BLOCK" and reason in POST_ROUTER_VALID_SIGNAL_BLOCKS
        ):
            times.add(parse_time(row.get("timestamp_broker", "")))
    return sorted(times)


def horizon_evidence(result: dict[str, Any], horizon: Horizon) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, str]]]:
    rows = trade_rows(result)
    order_rows = read_tsv(Path(result["order_csv"]))
    management_rows = read_tsv(Path(result["management_csv"]))
    report_metrics = result["mt5_report_metrics"]
    base = pnl_metrics(rows)
    stress = pnl_metrics(rows, cost_per_trade=0.30)
    order_successes = [row for row in order_rows if row.get("action") == "ORDER_SEND_OK"]
    order_failures = [row for row in order_rows if row.get("action", "").endswith("_FAIL")]
    management_failures = [row for row in management_rows if row.get("action", "").endswith("_FAIL")]
    tags = sorted({row.get("reason", "") for row in order_successes})
    directions = sorted({row.get("direction", "") for row in order_successes})
    actual_inputs = parse_tester_inputs(Path(result["tester_config"]))
    input_mismatches = {
        key: {"expected": expected, "actual": actual_inputs.get(key)}
        for key, expected in R5_INPUTS.items()
        if actual_inputs.get(key) != expected
    }
    history_quality = percent(report_metrics.get("History Quality", ""))
    equity_dd_pct = percent(report_metrics.get("Equity Drawdown Relative", ""))
    native_net = number(report_metrics.get("Total Net Profit", "0"))
    native_pf = number(report_metrics.get("Profit Factor", "0"))
    checks = {
        "history_quality_ge_98pct": history_quality >= 98.0,
        "trades_at_least_preregistered_minimum": base["trades"] >= horizon.minimum_trades,
        "net_profit_gt_0": native_net > 0.0,
        "win_rate_ge_40pct": base["win_rate_pct"] >= 40.0,
        "realized_win_loss_ge_1p80": (base["realized_win_loss"] or 0.0) >= 1.80,
        "profit_factor_ge_1p30": (base["profit_factor"] or 0.0) >= 1.30,
        "native_relative_equity_dd_lte_12pct": equity_dd_pct <= 12.0,
        "stress_030_net_gt_0": stress["net_usd"] > 0.0,
        "stress_030_pf_ge_1p20": (stress["profit_factor"] or 0.0) >= 1.20,
        "trade_net_reconciles_native_report": abs(base["net_usd"] - native_net) <= 0.02,
        "trade_count_reconciles_native_report": int(number(report_metrics.get("Total Trades", "0"))) == base["trades"],
        "profit_factor_reconciles_native_report_rounding": abs(round(base["profit_factor"] or 0.0, 2) - native_pf) <= 0.01,
        "order_successes_reconcile_trades": len(order_successes) == base["trades"],
        "zero_order_failures": len(order_failures) == 0,
        "zero_management_failures": len(management_failures) == 0,
        "every_execution_short": directions in ([], ["SHORT"]),
        "every_execution_tagged_causal_uptrend_or_chop": bool(order_successes)
        and all(row.get("reason") in ALLOWED_R5_ORDER_TAGS for row in order_successes),
        "tester_inputs_match_preregistration": not input_mismatches,
    }
    return (
        {
            "name": horizon.name,
            "from_date": horizon.from_date,
            "to_date": horizon.to_date,
            "minimum_trades": horizon.minimum_trades,
            "history_quality_pct": history_quality,
            "native_net_usd": native_net,
            "native_profit_factor": native_pf,
            "native_relative_equity_drawdown_pct": equity_dd_pct,
            "metrics": base,
            "stress_030": stress,
            "order_success_count": len(order_successes),
            "order_failure_count": len(order_failures),
            "management_failure_count": len(management_failures),
            "successful_order_tags": tags,
            "successful_order_directions": directions,
            "valid_signal_count": len(valid_signal_times(order_rows)),
            "tester_input_sha256": stable_hash(actual_inputs),
            "input_mismatches": input_mismatches,
            "checks": checks,
            "artifacts": {
                key: result[key]
                for key in (
                    "tester_config",
                    "html_report",
                    "trade_csv",
                    "order_csv",
                    "signal_csv",
                    "management_csv",
                    "deal_csv",
                    "summary_json",
                )
            },
        },
        rows,
        order_rows,
    )


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU R5 Pre-Downtrend Break Short V1 Exact-MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "Boundary: development Strategy Tester only. No broker action is authorized.",
        "",
        f"Currency note: {payload['legacy_currency_field_note']}",
        "",
        "| Horizon | Trades | WR% | W/L | PF | Net USD | Stress PF | Stress net | Native equity DD% | History | Pass |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["horizons"]:
        metrics = row["metrics"]
        stress = row["stress_030"]
        lines.append(
            f"| `{row['name']}` | {metrics['trades']} | {metrics['win_rate_pct']:.2f} | "
            f"{metrics['realized_win_loss'] or 0.0:.4f} | {metrics['profit_factor'] or 0.0:.4f} | "
            f"{row['native_net_usd']:.2f} | {stress['profit_factor'] or 0.0:.4f} | {stress['net_usd']:.2f} | "
            f"{row['native_relative_equity_drawdown_pct']:.2f} | {row['history_quality_pct']:.2f}% | "
            f"{all(row['checks'].values())} |"
        )
    robustness = payload["robustness"]
    lines.extend(
        [
            "",
            "## Robustness and independence",
            "",
            f"- Early five-year half net: `{robustness['early_five_year_net_usd']:.2f}` USD.",
            f"- Late five-year half net: `{robustness['late_five_year_net_usd']:.2f}` USD.",
            f"- Positive exact annual buckets: `{robustness['positive_annual_buckets']} / 10`.",
            f"- Top ten winning trades removed: `{robustness['top10_winning_trades_removed_net_usd']:.2f}` USD.",
            f"- Top three winning entry days removed: `{robustness['top3_winning_entry_days_removed_net_usd']:.2f}` USD.",
            f"- Daily closed-P/L correlation with H4: `{robustness['daily_pnl_correlation_with_h4']}`.",
            f"- Common-window H4 episodes touched: `{robustness['common_window_h4_episodes_touched']} / {robustness['common_window_h4_episode_count']}`.",
            f"- Full-decade H4 episodes touched: `{robustness['full_decade_h4_episodes_touched']} / {robustness['full_decade_h4_episode_count']}`.",
            "",
            "## Failed gates",
            "",
        ]
    )
    failed = payload["failed_gates"]
    lines.extend(f"- `{name}`" for name in failed)
    if not failed:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is one preregistered cell, not an optimization sweep. A standalone failure is not rescued by portfolio composition.",
            "No runtime chart, preset, account, order, or broker state is changed by this runner.",
            "",
        ]
    )
    return "\n".join(lines)


def manifest_rows(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            rows.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "size": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    return rows


def rewrite_archived_run_metadata(output_dir: Path, horizon: dict[str, Any]) -> None:
    """Make every archived run-artifact reference portable and internally valid."""
    artifacts = horizon["artifacts"]
    signal_path = artifacts["signal_csv_gzip"]
    portable_fields = {
        key: artifacts[key]
        for key in (
            "tester_config",
            "html_report",
            "trade_csv",
            "order_csv",
            "management_csv",
            "deal_csv",
            "summary_json",
        )
    }
    portable_fields["signal_csv"] = signal_path

    summary_path = output_dir / artifacts["summary_json"]
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary.update(portable_fields)
    summary["signal_log_archive"] = horizon["signal_log_archive"]
    summary["legacy_currency_field_note"] = LEGACY_CURRENCY_FIELD_NOTE
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    component_path = output_dir / "runs" / horizon["name"] / "mt5_components.json"
    component = json.loads(component_path.read_text(encoding="utf-8"))
    original_variant = dict(component["variants"][0])
    component_markdown_path = component_path.with_suffix(".md")
    if component_markdown_path.is_file():
        component_markdown = component_markdown_path.read_text(encoding="utf-8")
        for key, replacement in portable_fields.items():
            original = original_variant.get(key)
            if isinstance(original, str):
                component_markdown = component_markdown.replace(original, replacement)
        markdown_artifacts = (
            ("MT5 report", "html_report"),
            ("Trade CSV", "trade_csv"),
            ("Order CSV", "order_csv"),
            ("Signal CSV", "signal_csv"),
            ("Management CSV", "management_csv"),
            ("Summary JSON", "summary_json"),
        )
        for label, key in markdown_artifacts:
            rendered_label = "Signal CSV (gzip)" if key == "signal_csv" else label
            component_markdown = re.sub(
                rf"(?m)^- {re.escape(label)}(?: \(gzip\))?: `[^`]+`$",
                f"- {rendered_label}: `{portable_fields[key]}`",
                component_markdown,
            )
        currency_note = f"- Currency note: {LEGACY_CURRENCY_FIELD_NOTE}"
        if currency_note not in component_markdown:
            component_markdown = component_markdown.replace(
                "- Profit/loss table values are in tester currency `USD`.",
                "- Profit/loss table values are in tester currency `USD`.\n" + currency_note,
            )
        component_markdown_path.write_text(component_markdown, encoding="utf-8")
    component["compile_log"] = artifacts["compile_log"]
    component["scope"]["terminal_sandbox"] = "runtime-only; not archived"
    component["variants"][0].update(portable_fields)
    component["signal_log_archive"] = horizon["signal_log_archive"]
    component["legacy_currency_field_note"] = LEGACY_CURRENCY_FIELD_NOTE
    component_path.write_text(json.dumps(component, indent=2) + "\n", encoding="utf-8")


def compress_completed_signal_logs(output_dir: Path) -> Path:
    """Losslessly compress signal ledgers from an already completed exact run."""
    output_dir = output_dir.resolve()
    json_path = output_dir / f"{OUTPUT_STEM}.json"
    md_path = output_dir / f"{OUTPUT_STEM}.md"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    for horizon in payload["horizons"]:
        artifact = horizon["artifacts"].pop("signal_csv", None)
        if artifact is not None:
            signal_path = output_dir / artifact
            archive = compress_signal_log(signal_path)
            archive_path = Path(archive["path"]).resolve()
            relative_archive = archive_path.relative_to(output_dir).as_posix()
            horizon["artifacts"]["signal_csv_gzip"] = relative_archive
            horizon["signal_log_archive"] = {**archive, "path": relative_archive}
        rewrite_archived_run_metadata(output_dir, horizon)

    payload["legacy_currency_field_note"] = LEGACY_CURRENCY_FIELD_NOTE
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    md_path.write_text(render(payload), encoding="utf-8")
    manifest = {
        "status": payload["status"],
        "preregistration_sha256": payload["preregistration_sha256"],
        "locked_inputs_sha256": payload["locked_inputs_sha256"],
        "artifacts": manifest_rows(output_dir),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    return json_path


def run_exact(
    *,
    backtest_root: Path,
    metaeditor: Path,
    output_dir: Path,
    h4_deal_log: Path,
    timeout_seconds: int,
) -> Path:
    require_file(PREREG)
    require_file(a1.EA_SOURCE)
    require_file(h4_deal_log)
    variant = build_variant()
    locked_checks = static_checks(variant)
    if not all(locked_checks.values()):
        raise RuntimeError(f"Invalid preregistered R5 configuration: {locked_checks}")
    output_dir = output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError(f"Output directory must be new or empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "locked_inputs.json").write_text(
        json.dumps({"variant": variant.name, "inputs": R5_INPUTS, "sha256": stable_hash(R5_INPUTS)}, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )

    a1.VARIANTS = [variant]
    horizon_rows: list[dict[str, Any]] = []
    trades_by_horizon: dict[str, list[dict[str, Any]]] = {}
    orders_by_horizon: dict[str, list[dict[str, str]]] = {}
    for horizon in HORIZONS:
        run_dir = output_dir / "runs" / horizon.name
        run_dir.mkdir(parents=True, exist_ok=True)
        mt5_payload = run_variants_fail_closed(
            backtest_root=backtest_root,
            metaeditor=metaeditor,
            output_dir=run_dir,
            from_date=horizon.from_date,
            to_date=horizon.to_date,
            tag=f"R5_PRE_DOWNTREND_Q55_{horizon.name}",
            report_md=run_dir / "mt5_components.md",
            report_json=run_dir / "mt5_components.json",
            variant_timeout_seconds=timeout_seconds,
            deposit="1000",
            currency="USD",
        )
        result = mt5_payload["variants"][0]
        evidence, trades, orders = horizon_evidence(result, horizon)
        signal_archive = compress_signal_log(Path(result["signal_csv"]))
        result["signal_csv"] = signal_archive["path"]
        mt5_payload["signal_log_archive"] = signal_archive
        (run_dir / "mt5_components.json").write_text(
            json.dumps(mt5_payload, indent=2), encoding="utf-8",
        )
        copied_config = run_dir / "tester.ini"
        shutil.copy2(result["tester_config"], copied_config)
        compile_log = Path(mt5_payload["compile_log"])
        copied_compile_log = run_dir / "compile.log"
        shutil.copy2(compile_log, copied_compile_log)
        compiled_dir = run_dir / "compiled"
        compiled_dir.mkdir(parents=True, exist_ok=True)
        sandbox_experts = backtest_root.resolve() / "MQL5" / "Experts"
        compiled_source = compiled_dir / f"{a1.EA_NAME}.mq5"
        compiled_ex5 = compiled_dir / f"{a1.EA_NAME}.ex5"
        shutil.copy2(sandbox_experts / compiled_source.name, compiled_source)
        shutil.copy2(sandbox_experts / compiled_ex5.name, compiled_ex5)
        evidence["tester_config_sha256"] = sha256_file(copied_config)
        evidence["compile_log_sha256"] = sha256_file(copied_compile_log)
        evidence["compiled_source_sha256"] = sha256_file(compiled_source)
        evidence["compiled_ex5_sha256"] = sha256_file(compiled_ex5)
        evidence["artifacts"].pop("signal_csv", None)
        evidence["artifacts"] = {
            key: (
                copied_config.relative_to(output_dir).as_posix()
                if key == "tester_config"
                else Path(path).resolve().relative_to(output_dir).as_posix()
            )
            for key, path in evidence["artifacts"].items()
        }
        evidence["artifacts"]["compile_log"] = copied_compile_log.relative_to(output_dir).as_posix()
        evidence["artifacts"]["compiled_source"] = compiled_source.relative_to(output_dir).as_posix()
        evidence["artifacts"]["compiled_ex5"] = compiled_ex5.relative_to(output_dir).as_posix()
        signal_archive_path = Path(signal_archive["path"]).resolve()
        evidence["artifacts"]["signal_csv_gzip"] = signal_archive_path.relative_to(output_dir).as_posix()
        evidence["signal_log_archive"] = {
            **signal_archive,
            "path": signal_archive_path.relative_to(output_dir).as_posix(),
        }
        rewrite_archived_run_metadata(output_dir, evidence)
        horizon_rows.append(evidence)
        trades_by_horizon[horizon.name] = trades
        orders_by_horizon[horizon.name] = orders

    h4_trades = extended.build_native_trades("h4_d1_long_best_box2_atr80", h4_deal_log)
    h4_episodes = merge_exposure_episodes(h4_trades)
    common_episodes = [
        (max(start, COMMON_WINDOW_START), min(end, COMMON_WINDOW_END))
        for start, end in h4_episodes
        if end >= COMMON_WINDOW_START and start <= COMMON_WINDOW_END
    ]
    ten_year_trades = trades_by_horizon["ten_year"]
    ten_year_valid_times = valid_signal_times(orders_by_horizon["ten_year"])
    early_rows = [row for row in ten_year_trades if row["exit_time"] < TEN_YEAR_SPLIT]
    late_rows = [row for row in ten_year_trades if row["exit_time"] >= TEN_YEAR_SPLIT]
    annual = ten_equal_year_buckets(ten_year_trades)
    concentration = concentration_metrics(ten_year_trades)
    correlation = pearson_daily_pnl(daily_pnl(ten_year_trades), daily_pnl(h4_trades))
    robustness = {
        "early_five_year_net_usd": pnl_metrics(early_rows)["net_usd"],
        "late_five_year_net_usd": pnl_metrics(late_rows)["net_usd"],
        "positive_annual_buckets": sum(row["net_usd"] > 0.0 for row in annual),
        "annual_buckets": annual,
        "calendar_years": calendar_year_rows(ten_year_trades),
        **concentration,
        "daily_pnl_correlation_with_h4": correlation,
        "daily_pnl_correlation_basis": "union of broker exit dates; absent closed P/L is zero",
        "full_decade_h4_episode_count": len(h4_episodes),
        "common_window_h4_episode_count": len(common_episodes),
        "full_decade_h4_episodes_touched": touched_episode_count(ten_year_valid_times, h4_episodes),
        "common_window_h4_episodes_touched": touched_episode_count(ten_year_valid_times, common_episodes),
        "valid_signal_definition": "ORDER_SEND_OK/FAIL or post-router daily/position-cap block after locked risk gates",
    }
    robustness_checks = {
        "early_five_year_half_nonnegative": robustness["early_five_year_net_usd"] >= 0.0,
        "late_five_year_half_nonnegative": robustness["late_five_year_net_usd"] >= 0.0,
        "at_least_seven_of_ten_annual_buckets_positive": robustness["positive_annual_buckets"] >= 7,
        "top10_winning_trades_removed_net_positive": concentration["top10_winning_trades_removed_net_usd"] > 0.0,
        "top3_winning_entry_days_removed_net_positive": concentration["top3_winning_entry_days_removed_net_usd"] > 0.0,
        "daily_pnl_correlation_lte_0p30": correlation is not None and correlation <= 0.30,
        "h4_full_decade_episode_denominator_reconciles_39": len(h4_episodes) == 39,
        "h4_common_window_episode_denominator_reconciles_13": len(common_episodes) == 13,
        "valid_signals_touch_at_least_20_full_decade_episodes": robustness["full_decade_h4_episodes_touched"] >= 20,
        "valid_signals_touch_at_least_8_common_window_episodes": robustness["common_window_h4_episodes_touched"] >= 8,
    }
    all_checks: dict[str, bool] = {f"static::{key}": value for key, value in locked_checks.items()}
    for row in horizon_rows:
        all_checks.update({f"{row['name']}::{key}": value for key, value in row["checks"].items()})
    all_checks.update({f"robustness::{key}": value for key, value in robustness_checks.items()})
    failed_gates = [key for key, value in all_checks.items() if not value]
    payload = {
        "schema_version": "a1_xau_r5_pre_downtrend_break_short_v1_exact_v1",
        "status": "R5_STANDALONE_PASS" if not failed_gates else "R5_STANDALONE_FAIL",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "boundary": {
            "strategy_tester_only": True,
            "broker_action_authorized": False,
            "single_preregistered_cell": True,
            "optimization_or_neighbor_sweep": False,
        },
        "legacy_currency_field_note": LEGACY_CURRENCY_FIELD_NOTE,
        "preregistration": portable_source_path(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "ea_source": portable_source_path(a1.EA_SOURCE),
        "ea_source_sha256": sha256_file(a1.EA_SOURCE),
        "locked_inputs": R5_INPUTS,
        "locked_inputs_sha256": stable_hash(R5_INPUTS),
        "static_checks": locked_checks,
        "h4_deal_log": portable_source_path(h4_deal_log),
        "h4_deal_log_sha256": sha256_file(h4_deal_log),
        "horizons": horizon_rows,
        "robustness": robustness,
        "robustness_checks": robustness_checks,
        "all_checks": all_checks,
        "failed_gates": failed_gates,
    }
    json_path = output_dir / f"{OUTPUT_STEM}.json"
    md_path = output_dir / f"{OUTPUT_STEM}.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    md_path.write_text(render(payload), encoding="utf-8")
    manifest = {
        "status": payload["status"],
        "preregistration_sha256": payload["preregistration_sha256"],
        "locked_inputs_sha256": payload["locked_inputs_sha256"],
        "artifacts": manifest_rows(output_dir),
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return json_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backtest-root", type=Path, default=a1.DEFAULT_BACKTEST_ROOT)
    parser.add_argument("--metaeditor", type=Path, default=a1.DEFAULT_METAEDITOR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--h4-deal-log", type=Path, default=DEFAULT_H4_DEAL_LOG)
    parser.add_argument("--timeout-seconds", type=int, default=3600)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(
        run_exact(
            backtest_root=args.backtest_root,
            metaeditor=args.metaeditor,
            output_dir=args.output_dir,
            h4_deal_log=args.h4_deal_log,
            timeout_seconds=args.timeout_seconds,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

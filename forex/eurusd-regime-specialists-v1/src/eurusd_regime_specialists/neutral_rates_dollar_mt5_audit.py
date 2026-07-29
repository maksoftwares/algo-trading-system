from __future__ import annotations

import hashlib
import html
import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .adaptive_frequency_audit import (
    attach_causal_regime,
    load_neutral_oracle,
    match_oracle,
    profit_metrics,
)
from .ensemble import load_ensemble_config
from .research import PACKAGE_ROOT, load_inputs

FAMILY = "EURUSD_NEUTRAL_RATES_DOLLAR_MT5_AUDIT_V1"
REPO_ROOT = PACKAGE_ROOT.parents[1]
MT5_REPORT_ROOT = Path("D:/AlgoTradingData/C_DRIVE/MT5A1M5MomentumBacktest/Reports")
REPORTS = {
    "PRIMARY_OFFSET_0": (
        "ForexRatesDollar_2022_2026_RATES_DOLLAR_V1_MT5_EURUSD_H4_offset0.htm"
    ),
    "ROBUSTNESS_OFFSET_2": (
        "ForexRatesDollar_2022_2026_RATES_DOLLAR_V1_MT5_OFFSET2_EURUSD_H4_offset2.htm"
    ),
    "ROBUSTNESS_OFFSET_3": (
        "ForexRatesDollar_2022_2026_RATES_DOLLAR_V1_MT5_OFFSET3_EURUSD_H4_offset3.htm"
    ),
}
EA_SOURCE = (
    REPO_ROOT
    / "forex-research"
    / "mt5"
    / "Experts"
    / "ForexRatesDollarYieldPressureShortSessionV1.mq5"
)
RUNNER_SOURCE = (
    REPO_ROOT / "forex-research" / "scripts" / "run_forex_mt5_rates_dollar_backtest.py"
)
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_rates_dollar_mt5_audit"
RESULT_PATH = OUTPUT_ROOT / "AUDIT.json"
TRADES_PATH = OUTPUT_ROOT / "TRADES_WITH_CAUSAL_REGIME.csv"
ORACLE_MATCHES_PATH = OUTPUT_ROOT / "PRIMARY_NEUTRAL_ORACLE_MATCHES_15M.csv"
REPORT_PATH = PACKAGE_ROOT / "EURUSD_NEUTRAL_RATES_DOLLAR_MT5_AUDIT_2026_07_29.md"
RESULT_LOCK_PATH = (
    PACKAGE_ROOT / "EURUSD_NEUTRAL_RATES_DOLLAR_MT5_AUDIT_RESULT_2026_07_29.sha256.json"
)
LATEST_SIX_MONTH_START = pd.Timestamp("2026-01-01T00:00:00Z")
LATEST_SIX_MONTH_END = pd.Timestamp("2026-06-30T23:59:59Z")
COMMON_ORACLE_START = pd.Timestamp("2024-07-01T00:00:00Z")
COMMON_ORACLE_END = pd.Timestamp("2026-06-30T23:59:59Z")
EXTRA_ROUND_TRIP_COST_USD = 0.05


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_text(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-16", "utf-8-sig", "utf-8"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _number(value: str) -> float:
    cleaned = value.replace(" ", "").replace(",", "")
    if cleaned in {"", "-"}:
        return 0.0
    return float(cleaned)


def _html_rows(path: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    for match in re.finditer(
        r"<tr[^>]*>(.*?)</tr>", read_text(path), flags=re.IGNORECASE | re.DOTALL
    ):
        cells = re.findall(
            r"<t[dh][^>]*>(.*?)</t[dh]",
            match.group(1),
            flags=re.IGNORECASE | re.DOTALL,
        )
        cleaned = [
            html.unescape(re.sub(r"<[^>]+>", "", cell)).strip().replace("\xa0", " ")
            for cell in cells
        ]
        if cleaned:
            rows.append(cleaned)
    return rows


def _reported_metrics(rows: list[list[str]]) -> dict[str, str]:
    labels = {
        "History Quality:",
        "Total Net Profit:",
        "Gross Profit:",
        "Gross Loss:",
        "Profit Factor:",
        "Expected Payoff:",
        "Total Trades:",
        "Profit Trades (% of total):",
        "Loss Trades (% of total):",
    }
    flat = [cell for row in rows for cell in row]
    return {
        cell.rstrip(":"): flat[index + 1]
        for index, cell in enumerate(flat[:-1])
        if cell in labels
    }


def read_mt5_report(path: Path) -> tuple[pd.DataFrame, dict[str, str]]:
    """Parse a RatesDollar MT5 report without optional HTML dependencies."""
    rows = _html_rows(path)
    deals = [
        row
        for row in rows
        if len(row) >= 13 and row[2] == "EURUSD" and row[4] in {"in", "out"}
    ]
    entries = [row for row in deals if row[4] == "in"]
    exits = [row for row in deals if row[4] == "out"]
    if not entries or len(entries) != len(exits):
        raise RuntimeError(f"Unpaired or empty MT5 deal ledger: {path}")
    if any(row[3].lower() != "sell" for row in entries):
        raise RuntimeError(f"RatesDollar report is not short-only: {path}")
    if any(row[3].lower() != "buy" for row in exits):
        raise RuntimeError(f"Unexpected exit direction: {path}")

    frame = pd.DataFrame(
        {
            "entry_time": [row[0] for row in entries],
            "exit_time": [row[0] for row in exits],
            "sleeve": "RATES_DOLLAR_H4_SHORT",
            "side": "SHORT",
            "volume": [_number(row[5]) for row in entries],
            "entry_price": [_number(row[6]) for row in entries],
            "exit_price": [_number(row[6]) for row in exits],
            "commission": [_number(row[8]) for row in exits],
            "swap": [_number(row[9]) for row in exits],
            "profit": [_number(row[10]) for row in exits],
            "exit_comment": [row[12] for row in exits],
        }
    )
    for column in ("entry_time", "exit_time"):
        frame[column] = (
            pd.to_datetime(
                frame[column],
                format="%Y.%m.%d %H:%M:%S",
                errors="raise",
            )
            .dt.tz_localize("UTC")
            .dt.as_unit("ns")
        )
    if (frame["exit_time"] < frame["entry_time"]).any():
        raise RuntimeError(f"Exit precedes entry: {path}")
    frame["net_pnl_usd"] = frame["commission"] + frame["swap"] + frame["profit"]
    return frame, _reported_metrics(rows)


def _reported_number(value: str) -> float:
    match = re.search(r"-?[0-9][0-9 ,.]*", value)
    if match is None:
        raise ValueError(value)
    return _number(match.group(0))


def reconcile_report(trades: pd.DataFrame, reported: dict[str, str]) -> dict[str, Any]:
    values = trades["net_pnl_usd"].to_numpy(dtype=float)
    wins = values[values > 0]
    losses = -values[values < 0]
    reconstructed = {
        "trades": len(values),
        "wins": len(wins),
        "losses": len(losses),
        "net_pnl_usd": float(values.sum()),
        "gross_profit_usd": float(wins.sum()),
        "gross_loss_usd": float(losses.sum()),
        "profit_factor": float(wins.sum() / losses.sum()),
    }
    comparisons = {
        "trades": reconstructed["trades"]
        == int(_reported_number(reported["Total Trades"])),
        "net_pnl": math.isclose(
            reconstructed["net_pnl_usd"],
            _reported_number(reported["Total Net Profit"]),
            abs_tol=0.005,
        ),
        "gross_profit": math.isclose(
            reconstructed["gross_profit_usd"],
            _reported_number(reported["Gross Profit"]),
            abs_tol=0.005,
        ),
        "gross_loss": math.isclose(
            reconstructed["gross_loss_usd"],
            abs(_reported_number(reported["Gross Loss"])),
            abs_tol=0.005,
        ),
    }
    if not all(comparisons.values()):
        raise RuntimeError(f"MT5 report reconciliation failed: {comparisons}")
    return {
        "reported": reported,
        "reconstructed": reconstructed,
        "exact_accounting_checks": comparisons,
    }


def _period(frame: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    return frame[
        frame["entry_time"].between(
            pd.Timestamp(start), pd.Timestamp(end), inclusive="both"
        )
    ]


def _chronological_metrics(frame: pd.DataFrame) -> dict[str, Any]:
    windows = {
        "2022": ("2022-01-01T00:00:00Z", "2022-12-31T23:59:59Z"),
        "2023": ("2023-01-01T00:00:00Z", "2023-12-31T23:59:59Z"),
        "2024": ("2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z"),
        "2025": ("2025-01-01T00:00:00Z", "2025-12-31T23:59:59Z"),
        "2026_H1": (
            "2026-01-01T00:00:00Z",
            "2026-06-30T23:59:59Z",
        ),
        "DEVELOPMENT_2022_2023": (
            "2022-01-01T00:00:00Z",
            "2023-12-31T23:59:59Z",
        ),
        "RECENT_2024_2026_H1": (
            "2024-01-01T00:00:00Z",
            "2026-06-30T23:59:59Z",
        ),
        "LATEST_SIX_MONTHS": (
            LATEST_SIX_MONTH_START.isoformat(),
            LATEST_SIX_MONTH_END.isoformat(),
        ),
    }
    return {
        name: profit_metrics(_period(frame, start, end))
        for name, (start, end) in windows.items()
    }


def _by_regime(frame: pd.DataFrame) -> dict[str, Any]:
    return {
        str(regime): profit_metrics(block.sort_values("exit_time"))
        for regime, block in frame.groupby("causal_regime", sort=True)
    }


def _additional_cost_metrics(frame: pd.DataFrame) -> dict[str, Any]:
    stressed = frame.copy()
    stressed["net_pnl_usd"] = stressed["net_pnl_usd"] - EXTRA_ROUND_TRIP_COST_USD
    return profit_metrics(stressed)


def _top_5pct_winners_removed_metrics(
    frame: pd.DataFrame,
) -> dict[str, Any]:
    remove_count = math.ceil(len(frame) * 0.05)
    top_indices = frame["net_pnl_usd"].nlargest(remove_count).index
    return profit_metrics(frame.drop(index=top_indices))


def _oracle_resemblance(
    primary: pd.DataFrame,
) -> tuple[dict[str, Any], pd.DataFrame]:
    predictions = primary[
        primary["causal_regime"].eq("NEUTRAL")
        & ~primary["quarantined"]
        & primary["entry_time"].between(COMMON_ORACLE_START, COMMON_ORACLE_END)
    ].copy()
    oracle = load_neutral_oracle()
    exact = match_oracle(predictions, oracle, 0)
    tolerant = match_oracle(predictions, oracle, 15)
    return {
        "common_window_start_utc": COMMON_ORACLE_START,
        "common_window_end_utc": COMMON_ORACLE_END,
        "candidate_neutral_trades": len(predictions),
        "oracle_neutral_trades": len(oracle),
        "exact_same_side_matches": len(exact),
        "exact_precision": (
            float(len(exact) / len(predictions)) if len(predictions) else 0.0
        ),
        "exact_recall": float(len(exact) / len(oracle)),
        "same_side_15m_matches": len(tolerant),
        "same_side_15m_precision": (
            float(len(tolerant) / len(predictions)) if len(predictions) else 0.0
        ),
        "same_side_15m_recall": float(len(tolerant) / len(oracle)),
        "oracle_used_for_signal_or_selection": False,
    }, tolerant


def evaluate_gates(
    primary_neutral: dict[str, Any],
    chronological: dict[str, Any],
    robustness_neutral: dict[str, dict[str, Any]],
) -> dict[str, bool]:
    return {
        "minimum_30_neutral_trades": primary_neutral["trades"] >= 30,
        "win_rate_between_45_and_55_percent": (
            primary_neutral["win_rate"] is not None
            and 0.45 <= primary_neutral["win_rate"] <= 0.55
        ),
        "payoff_ratio_between_1p25_and_1p75": (
            primary_neutral["realized_payoff_ratio"] is not None
            and 1.25 <= primary_neutral["realized_payoff_ratio"] <= 1.75
        ),
        "primary_profit_factor_at_least_1p15": (
            primary_neutral["profit_factor"] is not None
            and primary_neutral["profit_factor"] >= 1.15
        ),
        "all_offset_profit_factors_at_least_1p15": all(
            metrics["profit_factor"] is not None and metrics["profit_factor"] >= 1.15
            for metrics in robustness_neutral.values()
        ),
        "top_5pct_removed_profit_factor_at_least_1p15": (
            primary_neutral["top_5pct_removed_profit_factor"] is not None
            and primary_neutral["top_5pct_removed_profit_factor"] >= 1.15
        ),
        "minimum_5_latest_six_month_trades": (
            chronological["LATEST_SIX_MONTHS"]["trades"] >= 5
        ),
        "recent_2024_2026_h1_positive": (
            chronological["RECENT_2024_2026_H1"]["net_pnl_usd"] > 0
        ),
        "year_2025_positive": chronological["2025"]["net_pnl_usd"] > 0,
    }


def build_audit() -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    cfg = load_ensemble_config()
    _, state, manifests = load_inputs(cfg)
    ledgers: dict[str, pd.DataFrame] = {}
    reconciliations: dict[str, Any] = {}
    for variant, filename in REPORTS.items():
        path = MT5_REPORT_ROOT / filename
        if not path.exists():
            raise FileNotFoundError(path)
        trades, reported = read_mt5_report(path)
        reconciliations[variant] = reconcile_report(trades, reported)
        attached = attach_causal_regime(trades, state, cfg)
        attached.insert(0, "report_variant", variant)
        ledgers[variant] = attached

    primary = ledgers["PRIMARY_OFFSET_0"]
    primary_neutral_frame = primary[
        primary["causal_regime"].eq("NEUTRAL") & ~primary["quarantined"]
    ].sort_values("exit_time")
    primary_neutral = profit_metrics(primary_neutral_frame)
    chronological = _chronological_metrics(primary_neutral_frame)
    robustness_neutral = {
        variant: profit_metrics(
            ledger[
                ledger["causal_regime"].eq("NEUTRAL") & ~ledger["quarantined"]
            ].sort_values("exit_time")
        )
        for variant, ledger in ledgers.items()
    }
    gates = evaluate_gates(primary_neutral, chronological, robustness_neutral)
    oracle, oracle_matches = _oracle_resemblance(primary)
    offset_2 = ledgers["ROBUSTNESS_OFFSET_2"][
        [
            "entry_time",
            "exit_time",
            "entry_price",
            "exit_price",
            "net_pnl_usd",
        ]
    ].reset_index(drop=True)
    offset_3 = ledgers["ROBUSTNESS_OFFSET_3"][
        [
            "entry_time",
            "exit_time",
            "entry_price",
            "exit_price",
            "net_pnl_usd",
        ]
    ].reset_index(drop=True)
    all_trades = pd.concat(ledgers.values(), ignore_index=True)
    result = {
        "schema_version": "eurusd_neutral_rates_dollar_mt5_audit_v1",
        "status": "REJECTED_RETROSPECTIVE_NEUTRAL_RATES_DOLLAR_MT5",
        "candidate": {
            "symbol": "EURUSD",
            "timeframe": "H4",
            "side": "SHORT_ONLY",
            "target_r": 1.35,
            "max_hold_h4_bars": 14,
            "decision_inputs": (
                "lagged TLT/UUP and TLT/SHY daily ratios plus completed "
                "EURUSD H4 EMA/ATR pullback state"
            ),
            "primary_variant_declared": "PRIMARY_OFFSET_0",
            "offsets_are_robustness_not_selection": True,
        },
        "boundary": {
            "existing_mt5_reports_only": True,
            "report_outcomes_known_before_this_audit": True,
            "retrospective_not_pristine_oos": True,
            "regime_uses_prior_completed_hour": True,
            "oracle_used_for_decisions": False,
            "parameter_search_performed": False,
            "broker_or_demo_action_performed": False,
        },
        "source_evidence": {
            "ea_source": str(EA_SOURCE),
            "ea_source_sha256": sha256_file(EA_SOURCE),
            "runner_source": str(RUNNER_SOURCE),
            "runner_source_sha256": sha256_file(RUNNER_SOURCE),
            "reports": {
                variant: {
                    "path": str(MT5_REPORT_ROOT / filename),
                    "sha256": sha256_file(MT5_REPORT_ROOT / filename),
                }
                for variant, filename in REPORTS.items()
            },
            "causal_input_manifests": manifests,
        },
        "report_reconciliation": reconciliations,
        "offset_2_and_3_trade_ledgers_identical": bool(offset_2.equals(offset_3)),
        "all_reports_by_causal_regime": {
            variant: _by_regime(ledger) for variant, ledger in ledgers.items()
        },
        "primary_neutral": {
            "observed": primary_neutral,
            "extra_half_pip_round_trip": _additional_cost_metrics(
                primary_neutral_frame
            ),
            "top_5pct_winners_removed": (
                _top_5pct_winners_removed_metrics(primary_neutral_frame)
            ),
            "chronological": chronological,
            "oracle_resemblance": oracle,
        },
        "neutral_offset_robustness": robustness_neutral,
        "research_gates": gates,
        "all_research_gates_passed": bool(all(gates.values())),
        "decision_reasons": [
            (
                "Only 12 canonical Neutral trades exist; the latest six "
                "months contain one trade."
            ),
            (
                "The canonical 66.7% win rate and 0.73 realized payoff do "
                "not match the requested approximately 50% / 1.5 profile."
            ),
            "Neutral PF falls from 1.46 at offset 0 to 1.14 at offsets 2/3.",
            "Removing the top 5% of winners lowers canonical Neutral PF to 1.13.",
            (
                "The 2025 Neutral slice lost USD 17.75, while the latest-"
                "six-month result is a single winning trade."
            ),
            (
                "The reports predate this audit, so no slice can be "
                "represented as pristine chronological out-of-sample "
                "evidence."
            ),
        ],
        "diagnostic_only": {
            "shock_regime_was_profitable_but_is_out_of_scope": True,
            "do_not_switch_regime_or_cherry_pick_shock": True,
        },
        "historical_result_can_authorize_demo": False,
    }
    return result, all_trades, oracle_matches


def _safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_safe(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return None if pd.isna(value) else value.isoformat()
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _metric_row(label: str, metrics: dict[str, Any]) -> str:
    return (
        f"| {label} | {metrics['trades']} | "
        f"{_pct(metrics['win_rate'])} | "
        f"{_decimal(metrics['realized_payoff_ratio'])} | "
        f"{_decimal(metrics['profit_factor'])} | "
        f"{metrics['net_pnl_usd']:.2f} |"
    )


def _pct(value: float | None) -> str:
    return "N/A" if value is None else f"{100.0 * value:.2f}%"


def _decimal(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.3f}"


def render_report(result: dict[str, Any]) -> str:
    neutral = result["primary_neutral"]["observed"]
    stress = result["primary_neutral"]["extra_half_pip_round_trip"]
    top_removed = result["primary_neutral"]["top_5pct_winners_removed"]
    chronology = result["primary_neutral"]["chronological"]
    robustness = result["neutral_offset_robustness"]
    regimes = result["all_reports_by_causal_regime"]["PRIMARY_OFFSET_0"]
    lines = [
        "# EURUSD Neutral Rates/Dollar MT5 Audit",
        "",
        f"Status: `{result['status']}`",
        "",
        "## Outcome",
        "",
        (
            "This existing H4 short strategy is **not** a viable Neutral "
            "expert. Its canonical Neutral subset is superficially "
            "profitable, but it is too small, does not match the requested "
            "payoff profile, weakens under timezone robustness, and failed "
            "in 2025."
        ),
        "",
        "| Scope | Trades | Win rate | Payoff | PF | Net USD |",
        "|---|---:|---:|---:|---:|---:|",
        _metric_row("Primary Neutral", neutral),
        _metric_row("Primary Neutral +0.5 pip", stress),
        _metric_row("Primary Neutral, top 5% winners removed", top_removed),
        _metric_row("Offset 2 Neutral", robustness["ROBUSTNESS_OFFSET_2"]),
        _metric_row("Offset 3 Neutral", robustness["ROBUSTNESS_OFFSET_3"]),
        "",
        "## Chronology",
        "",
        "| Window | Trades | Win rate | Payoff | PF | Net USD |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    lines.extend(_metric_row(name, metrics) for name, metrics in chronology.items())
    lines.extend(
        [
            "",
            "## Full primary regime attribution",
            "",
            "| Regime | Trades | Win rate | Payoff | PF | Net USD |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    lines.extend(_metric_row(name, metrics) for name, metrics in regimes.items())
    oracle = result["primary_neutral"]["oracle_resemblance"]
    lines.extend(
        [
            "",
            "## Oracle resemblance",
            "",
            (
                f"During the common 2024-07 through 2026-06 window, only "
                f"`{oracle['candidate_neutral_trades']}` causal Neutral "
                f"candidate trades existed versus "
                f"`{oracle['oracle_neutral_trades']}` oracle trades. Exact "
                f"same-side matches: `{oracle['exact_same_side_matches']}`; "
                f"within 15 minutes: "
                f"`{oracle['same_side_15m_matches']}`. The oracle was used "
                "only after execution for diagnosis."
            ),
            "",
            "## Why rejected",
            "",
        ]
    )
    lines.extend(f"- {reason}" for reason in result["decision_reasons"])
    lines.extend(
        [
            "",
            "## Integrity boundary",
            "",
            "- All three MT5 reports reconcile exactly to their deal ledgers when swap is included.",
            "- Offset 0 was declared primary; offsets 2 and 3 are robustness checks, not alternatives selected by outcome.",
            "- Causal regime ownership uses the state from the prior completed hour.",
            "- No thresholds, target, regime definition, or time window were retuned.",
            "- No broker, demo, or live action occurred.",
            "- The strong Shock-regime diagnostic is out of scope and was not substituted for Neutral.",
            "",
        ]
    )
    return "\n".join(lines)


def write_audit(
    result: dict[str, Any],
    trades: pd.DataFrame,
    oracle_matches: pd.DataFrame,
) -> dict[str, Any]:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(
        json.dumps(_safe(result), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    trades.to_csv(TRADES_PATH, index=False)
    oracle_matches.to_csv(ORACLE_MATCHES_PATH, index=False)
    REPORT_PATH.write_text(render_report(result), encoding="utf-8")
    lock = {
        "family": FAMILY,
        "status": result["status"],
        "result_outcomes_known": True,
        "files": {
            str(path.relative_to(PACKAGE_ROOT)).replace("\\", "/"): (sha256_file(path))
            for path in (
                RESULT_PATH,
                TRADES_PATH,
                ORACLE_MATCHES_PATH,
                REPORT_PATH,
            )
        },
        "source_reports": {
            variant: {
                "path": str(MT5_REPORT_ROOT / filename),
                "sha256": sha256_file(MT5_REPORT_ROOT / filename),
            }
            for variant, filename in REPORTS.items()
        },
    }
    RESULT_LOCK_PATH.write_text(
        json.dumps(lock, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return lock


def run_audit() -> dict[str, Any]:
    result, trades, oracle_matches = build_audit()
    lock = write_audit(result, trades, oracle_matches)
    return {**result, "result_lock": lock}


__all__ = [
    "build_audit",
    "evaluate_gates",
    "read_mt5_report",
    "reconcile_report",
    "run_audit",
    "write_audit",
]

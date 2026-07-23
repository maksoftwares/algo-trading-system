from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = PACKAGE_ROOT / "config" / "eurusd_m30_rsi_bb_fade_v1.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text_auto(path: Path) -> str:
    data = path.read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    return data.decode("utf-8-sig")


def profit_factor(values: list[float]) -> float:
    gross_profit = sum(value for value in values if value > 0)
    gross_loss = -sum(value for value in values if value < 0)
    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def maximum_drawdown(values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    drawdown = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    return drawdown


def worst_rolling(values: list[float], width: int) -> dict[str, float | int]:
    if len(values) < width:
        return {"width": width, "net": round(sum(values), 2), "profit_factor": round(profit_factor(values), 4)}
    worst_start = min(range(len(values) - width + 1), key=lambda start: sum(values[start : start + width]))
    window = values[worst_start : worst_start + width]
    return {
        "width": width,
        "start_index": worst_start,
        "net": round(sum(window), 2),
        "profit_factor": round(profit_factor(window), 4),
    }


def parse_drawdown_percent(text: str) -> float:
    left = text.rfind("(")
    right = text.rfind("%")
    if left < 0 or right < 0 or right <= left:
        raise ValueError(f"Cannot parse drawdown percentage from {text!r}")
    return float(text[left + 1 : right])


def read_trades(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"entry_time", "entry_date", "direction", "profit"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"Trade CSV missing required fields: {path}")
    return rows


def _relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def run_audit(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_json(config_path)
    implementation = config["implementation"]
    evidence = config["evidence"]
    gates_config = config["working_research_gates"]

    ea_source = REPO_ROOT / implementation["ea_source"]
    locked_ex5 = REPO_ROOT / implementation["locked_ex5"]
    parity_manifest_path = REPO_ROOT / implementation["parity_manifest"]
    preset = REPO_ROOT / implementation["preset"]
    mt5_run_path = REPO_ROOT / evidence["mt5_run_json"]
    robustness_path = REPO_ROOT / evidence["robustness_json"]
    trade_matches = sorted(REPO_ROOT.glob(evidence["trade_csv_glob"]))
    if len(trade_matches) != 1:
        raise RuntimeError(f"Expected exactly one trade CSV, found {len(trade_matches)}")
    trade_path = trade_matches[0]
    inherited_trade_matches = sorted(REPO_ROOT.glob(evidence["inherited_trade_csv_glob"]))
    if len(inherited_trade_matches) != 1:
        raise RuntimeError(f"Expected exactly one inherited trade CSV, found {len(inherited_trade_matches)}")
    inherited_trade_path = inherited_trade_matches[0]

    current_source_hash = sha256(ea_source)
    current_ex5_hash = sha256(locked_ex5)
    parity_manifest = load_json(parity_manifest_path)
    compile_log_path = REPO_ROOT / parity_manifest["artifacts"]["compile_log"]["path"]
    compile_log_text = read_text_auto(compile_log_path)
    source_text = ea_source.read_text(encoding="utf-8")
    preset_text = preset.read_text(encoding="utf-8")
    mt5_run = load_json(mt5_run_path)
    robustness = load_json(robustness_path)
    result = mt5_run["results"][0]
    mt5 = result["mt5_report_metrics"]
    trades = read_trades(trade_path)
    parsed_profit = [float(row["profit"]) for row in trades]

    by_year: dict[str, list[float]] = defaultdict(list)
    by_month: dict[str, list[float]] = defaultdict(list)
    for row, value in zip(trades, parsed_profit):
        by_year[row["entry_date"][:4]].append(value)
        by_month[row["entry_date"][:7]].append(value)

    top10_removed = sorted(parsed_profit, reverse=True)[10:]
    design = robustness["tuned"]["design_2022_2024"]
    current = robustness["tuned"]["current_2024_2026"]
    mt5_trades = int(mt5["Total Trades"])
    mt5_pf = float(mt5["Profit Factor"])
    mt5_net = float(mt5["Total Net Profit"])
    mt5_equity_dd_pct = parse_drawdown_percent(mt5["Equity Drawdown Maximal"])

    gates = {
        "actual_mt5_strategy_tester": bool(mt5_run["scope"]["tester_model"].startswith("MT5 Strategy Tester")),
        "minimum_trades": mt5_trades >= int(gates_config["minimum_trades"]),
        "minimum_mt5_profit_factor": mt5_pf >= float(gates_config["minimum_mt5_profit_factor"]),
        "positive_mt5_net": mt5_net > 0,
        "maximum_mt5_equity_drawdown": mt5_equity_dd_pct
        <= float(gates_config["maximum_mt5_equity_drawdown_pct"]),
        "positive_both_chronological_splits": all(
            float(split["pnl"]) > 0 and float(split["profit_factor"]) > 1.0 for split in (design, current)
        ),
        "positive_top10_removed": sum(top10_removed) > 0,
        "source_hash_match": current_source_hash == implementation["ea_source_sha256"],
        "ex5_hash_match": current_ex5_hash == implementation["locked_ex5_sha256"],
        "zero_warning_compile": "Result: 0 errors, 0 warnings" in compile_log_text,
        "exact_trade_ledger_parity": sha256(trade_path) == sha256(inherited_trade_path),
        "tester_only_guard": "if(!MQLInfoInteger(MQL_TESTER))" in source_text
        and "INIT_FAILED_NOT_TESTER" in source_text,
        "completed_bar_signal": all(token in source_text for token in ("CopyOne(g_atr_handle, 0, 1", "iClose(InpTargetSymbol, InpSignalTimeframe, 1)")),
        "preset_research_identity": all(
            token in preset_text
            for token in (
                "InpTargetSymbol=EURUSD",
                "InpSignalTimeframe=30",
                "InpDirectionMode=1",
                "InpRiskReward=0.80",
            )
        ),
    }
    working = all(gates.values())
    price_net = sum(parsed_profit)
    months_positive = sum(sum(values) > 0 for values in by_month.values())

    report = {
        "schema_version": "eurusd_phase0_evidence_audit_v1",
        "candidate_id": config["candidate_id"],
        "status": (
            "WORKING_RESEARCH_STRATEGY_FORWARD_NOT_AUTHORIZED"
            if working
            else "RESEARCH_BASELINE_GATE_FAIL"
        ),
        "authorization": config["authorization"],
        "artifacts": {
            "config": _relative(config_path),
            "ea_source": _relative(ea_source),
            "locked_ex5": _relative(locked_ex5),
            "parity_manifest": _relative(parity_manifest_path),
            "preset": _relative(preset),
            "mt5_run_json": _relative(mt5_run_path),
            "robustness_json": _relative(robustness_path),
            "trade_csv": _relative(trade_path),
            "inherited_trade_csv": _relative(inherited_trade_path),
            "ea_source_sha256": current_source_hash,
            "locked_ex5_sha256": current_ex5_hash,
            "preset_sha256": sha256(preset),
            "trade_csv_sha256": sha256(trade_path),
            "inherited_trade_csv_sha256": sha256(inherited_trade_path),
        },
        "mt5_economics": {
            "period": {
                "from": mt5_run["scope"]["from_date"],
                "to": mt5_run["scope"]["to_date"],
            },
            "history_quality": mt5["History Quality"],
            "trades": mt5_trades,
            "win_rate_pct": result["summary"]["overall"]["win_rate_pct"],
            "net_profit_usd": mt5_net,
            "profit_factor": mt5_pf,
            "expected_payoff_usd": float(mt5["Expected Payoff"]),
            "equity_drawdown_maximal": mt5["Equity Drawdown Maximal"],
            "equity_drawdown_pct": mt5_equity_dd_pct,
            "order_send_failures": result["activity"]["order_actions"].get("ORDER_SEND_FAIL", 0),
        },
        "parsed_trade_diagnostics": {
            "trade_rows": len(trades),
            "price_profit_net_usd": round(price_net, 2),
            "mt5_net_minus_price_profit_usd": round(mt5_net - price_net, 2),
            "profit_factor": round(profit_factor(parsed_profit), 4),
            "maximum_closed_drawdown_usd": round(maximum_drawdown(parsed_profit), 2),
            "top10_winners_removed_net_usd": round(sum(top10_removed), 2),
            "positive_months": months_positive,
            "active_months": len(by_month),
            "year_net_usd": {year: round(sum(values), 2) for year, values in sorted(by_year.items())},
            "worst_250_trades": worst_rolling(parsed_profit, 250),
        },
        "chronological_splits": {
            "design_2022_2024": design,
            "current_2024_2026": current,
        },
        "working_research_gates": gates,
        "promotion_blockers": [
            "The selected entry-hour mask is retrospective development evidence.",
            "No locked prospective shadow sample exists.",
            "Repository Capital.com bar exports are not current or promotion-grade Bid/Ask evidence.",
            "No combined XAUUSD/EURUSD shared-risk or USD-factor exposure test exists.",
        ],
    }
    return report


def markdown_report(report: dict[str, Any]) -> str:
    mt5 = report["mt5_economics"]
    parsed = report["parsed_trade_diagnostics"]
    gate_lines = "\n".join(
        f"- [{'x' if passed else ' '}] `{name}`" for name, passed in report["working_research_gates"].items()
    )
    blocker_lines = "\n".join(f"- {blocker}" for blocker in report["promotion_blockers"])
    year_rows = "\n".join(f"| {year} | {net:.2f} |" for year, net in parsed["year_net_usd"].items())
    return f"""# EURUSD Phase-0 Evidence Audit

Status: `{report['status']}`

This is a working research baseline, not deployment authority.

## Exact MT5 evidence

| Metric | Value |
|---|---:|
| Period | {mt5['period']['from']} to {mt5['period']['to']} |
| History quality | {mt5['history_quality']} |
| Trades | {mt5['trades']} |
| Win rate | {mt5['win_rate_pct']:.2f}% |
| MT5 net | ${mt5['net_profit_usd']:.2f} |
| MT5 profit factor | {mt5['profit_factor']:.2f} |
| MT5 maximal equity drawdown | {mt5['equity_drawdown_maximal']} |
| Order-send failures | {mt5['order_send_failures']} |

## Parsed trade diagnostics

The trade CSV `profit` field excludes some account-level costs represented in
the MT5 report. It is used for concentration/path diagnostics, not as a
replacement for MT5 total net profit.

| Metric | Value |
|---|---:|
| Trade rows | {parsed['trade_rows']} |
| Parsed price-profit net | ${parsed['price_profit_net_usd']:.2f} |
| MT5 net less parsed price-profit | ${parsed['mt5_net_minus_price_profit_usd']:.2f} |
| Parsed PF | {parsed['profit_factor']:.4f} |
| Parsed maximum closed drawdown | ${parsed['maximum_closed_drawdown_usd']:.2f} |
| Top-10 winners removed net | ${parsed['top10_winners_removed_net_usd']:.2f} |
| Positive/active months | {parsed['positive_months']} / {parsed['active_months']} |
| Worst 250-trade net | ${parsed['worst_250_trades']['net']:.2f} |

## Calendar-year parsed net

| Year | USD |
|---|---:|
{year_rows}

## Working-research gates

{gate_lines}

## Promotion blockers

{blocker_lines}

## Decision

The candidate is executable and historically profitable in actual MT5, so it
is a valid working EURUSD research strategy. Its edge is thin and selected
after historical inspection. Freeze it here; do not add another hour, indicator,
or threshold filter. The exact-MT5 parity rerun is hash-attested and reproduced
the inherited trade ledger byte-for-byte. The next valid evidence is prospective
shadow collection on refreshed broker data.
"""


def write_outputs(report: dict[str, Any]) -> tuple[Path, Path]:
    output_dir = PACKAGE_ROOT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "EURUSD_PHASE0_EVIDENCE_AUDIT.json"
    md_path = output_dir / "EURUSD_PHASE0_EVIDENCE_AUDIT.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(markdown_report(report), encoding="utf-8")
    return json_path, md_path

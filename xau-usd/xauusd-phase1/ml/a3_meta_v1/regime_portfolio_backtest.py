from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


WINDOWS = (
    ("last_3_months", "2026-04-01T00:00:00Z", "2026-06-30T23:59:59Z"),
    ("last_6_months", "2026-01-01T00:00:00Z", "2026-06-30T23:59:59Z"),
    ("last_5_years", "2021-07-01T00:00:00Z", "2026-06-30T23:59:59Z"),
    ("last_10_years", "2016-07-01T00:00:00Z", "2026-06-30T23:59:59Z"),
)
STRESS_COST_PER_TRADE_USD = 0.30


def analyze_regime_portfolio(
    root: Path,
    mt5_payload: dict[str, Any],
    *,
    preregistration: Path,
    report_json: Path,
    report_md: Path,
    trades_csv: Path,
) -> Path:
    root = root.resolve()
    source_roles = {
        "r1_box_clean_strict_uptrend": "R1_UPTREND_LONG",
        "r2_pullback_short_h1_confirm": "R2_DOWNTREND_SHORT",
    }
    rows: list[dict[str, Any]] = []
    source_audits: list[dict[str, Any]] = []
    for result in mt5_payload.get("variants", []):
        name = str(result.get("name", ""))
        if name not in source_roles:
            raise ValueError(f"unexpected portfolio source: {name}")
        trade_path = Path(result["trade_csv"]).resolve()
        source_rows = _read_trades(trade_path, name, source_roles[name])
        rows.extend(source_rows)
        source_audits.append(
            {
                "source": name,
                "assigned_regime": source_roles[name],
                "trade_csv": str(trade_path),
                "trade_sha256": _sha256_file(trade_path),
                "trades": len(source_rows),
                "mt5_history_quality": result.get("mt5_report_metrics", {}).get("History Quality"),
                "mt5_total_trades": result.get("mt5_report_metrics", {}).get("Total Trades"),
                "mt5_profit_factor": result.get("mt5_report_metrics", {}).get("Profit Factor"),
                "mt5_equity_drawdown_usd": _mt5_money(
                    result.get("mt5_report_metrics", {}).get("Equity Drawdown Maximal")
                ),
                "mt5_equity_drawdown_raw": result.get("mt5_report_metrics", {}).get(
                    "Equity Drawdown Maximal"
                ),
            }
        )
    if not rows:
        raise ValueError("regime portfolio has no completed trades")
    rows.sort(key=lambda row: (row["exit_time_dt"], row["source"], row["entry_time_dt"]))
    _validate_rows(rows)

    windows = {}
    for name, start, end in WINDOWS:
        selected = [row for row in rows if _parse_iso(start) <= row["exit_time_dt"] <= _parse_iso(end)]
        windows[name] = _stats(selected)
        windows[name]["start_utc"] = start
        windows[name]["end_utc"] = end

    six_month_blocks = _six_month_blocks(rows)
    nonnegative_blocks = sum(1 for block in six_month_blocks if block["stress_net_usd"] >= 0.0)
    block_share = nonnegative_blocks / len(six_month_blocks) if six_month_blocks else 0.0
    ten_year = windows["last_10_years"]
    component_equity_dd = max((float(row["mt5_equity_drawdown_usd"] or 0.0) for row in source_audits), default=0.0)
    conservative_drawdown = max(ten_year["max_closed_drawdown_usd"], component_equity_dd)
    ten_year["max_component_mt5_equity_drawdown_usd"] = round(component_equity_dd, 2)
    ten_year["conservative_drawdown_usd"] = round(conservative_drawdown, 2)
    gates = {
        "ten_year_stress_pf_ge_1p40": (ten_year["stress_profit_factor"] or 0.0) >= 1.40,
        "last_3_months_stress_net_nonnegative": windows["last_3_months"]["stress_net_usd"] >= 0.0,
        "last_6_months_stress_net_nonnegative": windows["last_6_months"]["stress_net_usd"] >= 0.0,
        "conservative_drawdown_lte_1000": conservative_drawdown <= 1000.0,
        "six_month_nonnegative_share_ge_75pct": block_share >= 0.75,
        "only_frozen_r1_r2_sources": set(row["source"] for row in rows) == set(source_roles),
    }
    status = "RESEARCH_GATES_PASS" if all(gates.values()) else "RESEARCH_GATES_FAIL"
    regime_actions = {
        "R0_SHOCK": "NO_TRADE",
        "R1_UPTREND": "ARM_R1_LONG",
        "R2_DOWNTREND": "ARM_R2_SHORT",
        "R3_COMPRESSION": "NO_TRADE_NO_QUALIFIED_SPECIALIST",
        "R4_CHOP_UNDEFINED": "NO_TRADE_NO_QUALIFIED_SPECIALIST",
        "TRANSITION": "NO_TRADE",
    }
    payload = {
        "schema_version": "a3_ml_regime_portfolio_backtest_v1",
        "status": status,
        "created_at_utc": _format_utc(datetime.now(timezone.utc)),
        "scope": {
            "symbol": "XAUUSD",
            "from": "2016-07-01T00:00:00Z",
            "to": "2026-06-30T23:59:59Z",
            "lot_size": 0.01,
            "currency": "USD",
            "pnl_recognition": "closed_trade_exit_time",
            "stress_cost_per_trade_usd": STRESS_COST_PER_TRADE_USD,
        },
        "regime_actions": regime_actions,
        "source_audits": source_audits,
        "windows": windows,
        "six_month_blocks": six_month_blocks,
        "six_month_nonnegative_blocks": nonnegative_blocks,
        "six_month_total_blocks": len(six_month_blocks),
        "six_month_nonnegative_share": round(block_share, 6),
        "gates": gates,
        "authorization": {
            "research_only": True,
            "historical_development_data": True,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "limitations": [
            "All history through 2026-06-30 is development data and is not an untouched holdout.",
            "Component runs use fixed 0.01 lots in isolated MT5 tests; summed P/L does not model shared-account margin contention.",
            "MT5 spread is included, but the extra USD 0.30 stress is a sensitivity test rather than a broker guarantee.",
            "No-trade is the evidence-backed action in regimes without a qualified specialist; the system does not force continuous market exposure.",
        ],
        "artifacts": {
            "preregistration": str(preregistration.resolve()),
            "preregistration_sha256": _sha256_file(preregistration.resolve()),
            "mt5_report_json": str(report_json.with_name(report_json.stem + "_MT5.json")),
            "portfolio_trades_csv": str(trades_csv.resolve()),
            "portfolio_trades_sha256": "",
            "report_json": str(report_json.resolve()),
            "report_md": str(report_md.resolve()),
        },
    }
    _write_trades(trades_csv, rows)
    payload["artifacts"]["portfolio_trades_sha256"] = _sha256_file(trades_csv.resolve())
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_md.write_text(_render(payload), encoding="utf-8")
    return report_json


def _read_trades(path: Path, source: str, assigned_regime: str) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            profit = float(row["profit_aed"])
            rows.append(
                {
                    "source": source,
                    "assigned_regime": assigned_regime,
                    "entry_time": row["entry_time"],
                    "entry_time_dt": _parse_broker(row["entry_time"]),
                    "exit_time": row["exit_time"],
                    "exit_time_dt": _parse_broker(row["exit_time"]),
                    "direction": row["direction"].upper(),
                    "volume": float(row["volume"]),
                    "entry_price": float(row["entry_price"]),
                    "exit_price": float(row["exit_price"]),
                    "profit_usd": profit,
                    "stress_profit_usd": profit - STRESS_COST_PER_TRADE_USD,
                    "exit_comment": row.get("exit_comment", ""),
                }
            )
    return rows


def _validate_rows(rows: list[dict[str, Any]]) -> None:
    if any(abs(row["volume"] - 0.01) > 1e-9 for row in rows):
        raise ValueError("portfolio contains a non-0.01-lot trade")
    expected_direction = {"r1_box_clean_strict_uptrend": "LONG", "r2_pullback_short_h1_confirm": "SHORT"}
    for row in rows:
        if row["direction"] != expected_direction[row["source"]]:
            raise ValueError(f"source direction mismatch: {row['source']} {row['direction']}")
        if row["exit_time_dt"] < row["entry_time_dt"]:
            raise ValueError("trade exits before entry")
    keys = [(row["source"], row["entry_time"], row["direction"]) for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate source trade keys detected")


def _stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: row["exit_time_dt"])
    profits = [row["profit_usd"] for row in ordered]
    stress = [row["stress_profit_usd"] for row in ordered]
    wins = sum(1 for value in profits if value > 0.0)
    gross_profit = sum(value for value in profits if value > 0.0)
    gross_loss = -sum(value for value in profits if value < 0.0)
    stress_gross_profit = sum(value for value in stress if value > 0.0)
    stress_gross_loss = -sum(value for value in stress if value < 0.0)
    by_source = defaultdict(float)
    for row in ordered:
        by_source[row["source"]] += row["profit_usd"]
    return {
        "trades": len(ordered),
        "wins": wins,
        "losses": len(ordered) - wins,
        "win_rate_pct": round(100.0 * wins / len(ordered), 4) if ordered else 0.0,
        "net_usd": round(sum(profits), 2),
        "stress_net_usd": round(sum(stress), 2),
        "profit_factor": round(gross_profit / gross_loss, 4) if gross_loss > 0.0 else None,
        "stress_profit_factor": round(stress_gross_profit / stress_gross_loss, 4) if stress_gross_loss > 0.0 else None,
        "max_closed_drawdown_usd": round(_max_drawdown(stress), 2),
        "positive_months": _positive_months(ordered),
        "active_months": _active_months(ordered),
        "pnl_by_source_usd": {key: round(value, 2) for key, value in sorted(by_source.items())},
    }


def _max_drawdown(profits: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    maximum = 0.0
    for profit in profits:
        equity += profit
        peak = max(peak, equity)
        maximum = max(maximum, peak - equity)
    return maximum


def _active_months(rows: list[dict[str, Any]]) -> int:
    return len({row["exit_time"][:7] for row in rows})


def _positive_months(rows: list[dict[str, Any]]) -> int:
    months = defaultdict(float)
    for row in rows:
        months[row["exit_time"][:7]] += row["stress_profit_usd"]
    return sum(1 for value in months.values() if value > 0.0)


def _six_month_blocks(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for year in range(2016, 2027):
        for half, start_month, end_month in (("H1", 1, 6), ("H2", 7, 12)):
            start = datetime(year, start_month, 1, tzinfo=timezone.utc)
            if end_month == 12:
                end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
            else:
                end = datetime(year, end_month + 1, 1, tzinfo=timezone.utc)
            if start < datetime(2016, 7, 1, tzinfo=timezone.utc) or end > datetime(2026, 7, 1, tzinfo=timezone.utc):
                continue
            selected = [row for row in rows if start <= row["exit_time_dt"] < end]
            stats = _stats(selected)
            output.append({"block": f"{year}-{half}", **stats})
    return output


def _write_trades(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = (
        "source",
        "assigned_regime",
        "entry_time",
        "exit_time",
        "direction",
        "volume",
        "entry_price",
        "exit_price",
        "profit_usd",
        "stress_profit_usd",
        "exit_comment",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _render(payload: dict[str, Any]) -> str:
    lines = [
        "# A3 ML Regime Portfolio Continuous Backtest",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This is exact-MT5 historical research, not a profit forecast or broker-action authorization.",
        "",
        "## P/L Windows",
        "",
        "| Window | Trades | WR% | Net USD | Stress net USD | PF | Stress PF | Max closed DD USD | Positive/active months |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, _, _ in WINDOWS:
        row = payload["windows"][name]
        lines.append(
            f"| `{name}` | {row['trades']} | {row['win_rate_pct']:.2f} | {row['net_usd']:.2f} | "
            f"{row['stress_net_usd']:.2f} | {row['profit_factor'] or 0.0:.4f} | "
            f"{row['stress_profit_factor'] or 0.0:.4f} | {row['max_closed_drawdown_usd']:.2f} | "
            f"{row['positive_months']}/{row['active_months']} |"
        )
    ten_year = payload["windows"]["last_10_years"]
    lines.extend(
        [
            "",
            "## Drawdown Boundary",
            "",
            f"- Combined closed-trade drawdown: `${ten_year['max_closed_drawdown_usd']:.2f}`",
            f"- Largest component MT5 equity drawdown: `${ten_year['max_component_mt5_equity_drawdown_usd']:.2f}`",
            f"- Conservative gate drawdown: `${ten_year['conservative_drawdown_usd']:.2f}`",
            f"- Nonnegative six-month blocks: `{payload['six_month_nonnegative_blocks']}/{payload['six_month_total_blocks']}` ({payload['six_month_nonnegative_share'] * 100.0:.2f}%)",
        ]
    )
    lines.extend(["", "## Regime Actions", ""])
    for regime, action in payload["regime_actions"].items():
        lines.append(f"- `{regime}`: `{action}`")
    lines.extend(["", "## Gates", ""])
    for gate, passed in payload["gates"].items():
        lines.append(f"- `{gate}`: {'PASS' if passed else 'FAIL'}")
    lines.extend(
        [
            "",
            "## Evidence Boundary",
            "",
            "All reported P/L is hypothetical historical fixed-lot P/L. All inspected history is development data. Demo/live action remains disabled.",
            "",
        ]
    )
    return "\n".join(lines)


def _parse_broker(value: str) -> datetime:
    return datetime.strptime(value, "%Y.%m.%d %H:%M:%S").replace(tzinfo=timezone.utc)


def _mt5_money(value: Any) -> float | None:
    match = re.search(r"[-+]?\d[\d ]*(?:\.\d+)?", str(value or ""))
    return float(match.group(0).replace(" ", "")) if match else None


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

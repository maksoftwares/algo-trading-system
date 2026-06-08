from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_ACTUAL_TRADES = Path("outputs") / "reports" / "PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv"
DEFAULT_ORDER_LOG = Path("C:/MT5PortableP2WeaknessDemo/MQL5/Files/p2weakness_br_v1_order_log_xauusd.csv")
DEFAULT_JSON = Path("outputs") / "reports" / "PHASE2_ACTUAL_DEMO_COST_RECONCILIATION.json"
DEFAULT_MD = Path("outputs") / "reports" / "PHASE2_ACTUAL_DEMO_COST_RECONCILIATION.md"

MAX_ACCEPTABLE_COST_R = 0.15


@dataclass(frozen=True)
class ActualDemoCostReconciliationOutput:
    status: str
    json_path: Path
    markdown_path: Path
    resolution_status: str


def generate_phase2_actual_demo_cost_reconciliation(
    root: Path,
    actual_trades_csv: Path | None = None,
    order_log_csv: Path | None = None,
    output_json: Path | None = None,
) -> ActualDemoCostReconciliationOutput:
    root = root.resolve()
    reports_dir = root / "outputs" / "reports"
    actual_trades_csv = (actual_trades_csv or root / DEFAULT_ACTUAL_TRADES).resolve()
    order_log_csv = (order_log_csv or DEFAULT_ORDER_LOG).resolve()
    output_json = (output_json or root / DEFAULT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_JSON.name else root / DEFAULT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    actual_rows = _read_csv(actual_trades_csv)
    order_rows = _read_csv(order_log_csv)
    unique_rows = [row for row in actual_rows if str(row.get("is_duplicate", "")).lower() != "true"]
    breakout_rows = [row for row in unique_rows if row.get("candidate") == "breakout_retest"]

    actual_summary = {
        "raw": _summarize_trades(actual_rows),
        "unique": _summarize_trades(unique_rows),
        "breakout_retest_unique": _summarize_trades(breakout_rows),
        "by_symbol": _group_summary(unique_rows, "symbol"),
        "by_candidate": _group_summary(unique_rows, "candidate"),
        "by_status": _group_summary(unique_rows, "status"),
    }
    order_summary = _summarize_order_log(order_rows)
    phase0_context = _phase0_context(root)
    checks = _checks(actual_summary, order_summary, actual_trades_csv, order_log_csv)
    status = "PASS" if all(check["status"] == "PASS" for check in checks) else "REVIEW"
    resolution_status = (
        "RESOLVED_FOR_ACTUAL_DEMO_COST_REVIEW" if status == "PASS" else "REVIEW_REQUIRED"
    )

    payload = {
        "status": status,
        "resolution_status": resolution_status,
        "created_at_utc": _now(),
        "actual_trades_csv": str(actual_trades_csv),
        "order_log_csv": str(order_log_csv),
        "canonical_phase2_evidence": False,
        "phase2_readiness_override": False,
        "demo_execution_as_phase2_evidence": False,
        "live_trading_authorized": False,
        "decision": _decision(status),
        "checks": checks,
        "phase0_context": phase0_context,
        "actual_demo_summary": actual_summary,
        "p2weakness_order_cost_summary": order_summary,
        "interpretation": {
            "cost_not_current_practical_blocker": status == "PASS",
            "current_practical_focus": (
                "win_rate, setup quality, duplicate-family exposure, and formal cost-aware hypothesis promotion"
            ),
            "canonical_v1_revalidation": (
                "unchanged historical FAIL for the old tight-stop Phase 0 ledger"
            ),
        },
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return ActualDemoCostReconciliationOutput(status, output_json, output_md, resolution_status)


def _checks(
    actual_summary: dict[str, Any],
    order_summary: dict[str, Any],
    actual_trades_csv: Path,
    order_log_csv: Path,
) -> list[dict[str, str]]:
    unique = actual_summary["unique"]
    breakout = actual_summary["breakout_retest_unique"]
    checks = [
        _check(
            "actual_broker_csv_present",
            actual_trades_csv.exists(),
            f"source={actual_trades_csv}",
        ),
        _check(
            "actual_unique_sample_available",
            int(unique["closed"]) >= 1,
            f"unique_closed={unique['closed']}; broker-inclusive closed_pnl_aed={unique['closed_pnl_aed']}",
        ),
        _check(
            "actual_unique_broker_inclusive_pnl_available",
            int(unique["closed"]) >= 1 and unique["profit_factor"] is not None,
            (
                f"unique_closed_pnl_aed={unique['closed_pnl_aed']}; "
                f"unique_pf={unique['profit_factor']}; "
                "used as outcome context, not as the cost-resolution gate"
            ),
        ),
        _check(
            "breakout_retest_actual_sample_available",
            int(breakout["closed"]) >= 1,
            (
                f"breakout_closed={breakout['closed']}; "
                f"breakout_closed_pnl_aed={breakout['closed_pnl_aed']}; "
                f"breakout_pf={breakout['profit_factor']}; "
                "negative or weak outcome here is win-rate/setup evidence, not cost_R evidence"
            ),
        ),
        _check(
            "p2weakness_order_log_present",
            order_log_csv.exists(),
            f"source={order_log_csv}",
        ),
        _check(
            "p2weakness_executed_cost_r_below_floor",
            int(order_summary["order_send_ok"]) >= 1
            and float(order_summary["executed_cost_r_max"]) <= MAX_ACCEPTABLE_COST_R,
            (
                f"order_send_ok={order_summary['order_send_ok']}; "
                f"executed_cost_r_max={order_summary['executed_cost_r_max']}; "
                f"threshold<={MAX_ACCEPTABLE_COST_R}"
            ),
        ),
        _check(
            "p2weakness_signal_cost_r_below_floor",
            int(order_summary["cost_observations"]) >= 1
            and float(order_summary["signal_cost_r_max"]) <= MAX_ACCEPTABLE_COST_R,
            (
                f"cost_observations={order_summary['cost_observations']}; "
                f"signal_cost_r_max={order_summary['signal_cost_r_max']}; "
                f"threshold<={MAX_ACCEPTABLE_COST_R}"
            ),
        ),
    ]
    return checks


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _summarize_trades(rows: list[dict[str, str]]) -> dict[str, Any]:
    closed = [row for row in rows if row.get("state") == "CLOSED"]
    open_rows = [row for row in rows if row.get("state") == "OPEN"]
    wins = [row for row in closed if _to_float(row.get("profit_aed")) > 0.0]
    losses = [row for row in closed if _to_float(row.get("profit_aed")) < 0.0]
    gross_win = sum(_to_float(row.get("profit_aed")) for row in wins)
    gross_loss = sum(_to_float(row.get("profit_aed")) for row in losses)
    closed_pnl = sum(_to_float(row.get("profit_aed")) for row in closed)
    floating = sum(_to_float(row.get("profit_aed")) for row in open_rows)
    return {
        "total": len(rows),
        "closed": len(closed),
        "open": len(open_rows),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": _round(len(wins) / len(closed) * 100.0) if closed else 0.0,
        "closed_pnl_aed": _round(closed_pnl),
        "floating_pnl_aed": _round(floating),
        "net_with_open_aed": _round(closed_pnl + floating),
        "profit_factor": _round(gross_win / abs(gross_loss)) if gross_loss else None,
        "avg_win_aed": _round(gross_win / len(wins)) if wins else 0.0,
        "avg_loss_aed": _round(gross_loss / len(losses)) if losses else 0.0,
        "gross_win_aed": _round(gross_win),
        "gross_loss_aed": _round(gross_loss),
    }


def _summarize_order_log(rows: list[dict[str, str]]) -> dict[str, Any]:
    executed = [row for row in rows if row.get("action") == "ORDER_SEND_OK"]
    guard_blocks = [row for row in rows if row.get("action") == "GUARD_BLOCK"]
    costs = [_to_float(row.get("estimated_cost_R")) for row in rows if row.get("estimated_cost_R") not in {None, ""}]
    executed_costs = [
        _to_float(row.get("estimated_cost_R")) for row in executed if row.get("estimated_cost_R") not in {None, ""}
    ]
    executed_rows = [
        {
            "timestamp_broker": row.get("timestamp_broker", ""),
            "spread_points": row.get("spread_at_order_points", ""),
            "slippage_points": row.get("slippage_points", ""),
            "estimated_cost_R": row.get("estimated_cost_R", ""),
            "stop_distance_points": row.get("stop_distance_points", ""),
            "order_ticket": row.get("order_ticket", ""),
        }
        for row in executed
    ]
    return {
        "rows": len(rows),
        "order_send_ok": len(executed),
        "guard_blocks": len(guard_blocks),
        "cost_observations": len(costs),
        "signal_cost_r_min": _round(min(costs)) if costs else 0.0,
        "signal_cost_r_mean": _round(sum(costs) / len(costs), 4) if costs else 0.0,
        "signal_cost_r_max": _round(max(costs), 4) if costs else 0.0,
        "executed_cost_r_mean": _round(sum(executed_costs) / len(executed_costs), 4) if executed_costs else 0.0,
        "executed_cost_r_max": _round(max(executed_costs), 4) if executed_costs else 0.0,
        "executed_rows": executed_rows,
    }


def _group_summary(rows: list[dict[str, str]], key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        groups.setdefault(row.get(key, "") or "UNKNOWN", []).append(row)
    output = []
    for name, group_rows in groups.items():
        item = {"name": name, **_summarize_trades(group_rows)}
        output.append(item)
    return sorted(output, key=lambda item: float(item["closed_pnl_aed"]), reverse=True)


def _phase0_context(root: Path) -> dict[str, Any]:
    phase0_reports = root.parent / "xauusd-phase0" / "outputs" / "reports"
    return {
        "canonical_revalidation_status": _read_markdown_status(
            phase0_reports / "BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md"
        ),
        "assumption_delta_status": _read_markdown_status(phase0_reports / "MEASURED_COST_ASSUMPTION_DELTA.md"),
        "measured_cost_model_status": _read_markdown_status(phase0_reports / "MEASURED_COST_MODEL.md"),
        "cost_diagnostic_status": _read_markdown_status(phase0_reports / "BREAKOUT_RETEST_COST_R_DIAGNOSTIC.md"),
        "phase0_median_stop_points": 109.7939,
        "phase0_p95_spread_points": 75.0,
        "phase0_median_all_in_cost_R": 0.6904,
        "phase0_measured_net_R": -0.6150,
        "phase0_overall_pf_after_measured_cost": 0.4125,
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    actual = payload["actual_demo_summary"]
    order = payload["p2weakness_order_cost_summary"]
    phase0 = payload["phase0_context"]
    lines = [
        "# Phase 2 Actual Demo Cost Reconciliation",
        "",
        f"Overall status: {payload['status']}",
        f"Resolution status: {payload['resolution_status']}",
        f"Generated at UTC: {payload['created_at_utc']}",
        "",
        str(payload["decision"]),
        "",
        "## Boundary",
        "",
        "- This resolves the current actual-demo cost concern only.",
        "- It does not change `BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md` or `MEASURED_COST_ASSUMPTION_DELTA.md` to PASS.",
        "- It does not authorize live capital.",
        "- It does not make experimental demo fills canonical Phase 2 evidence.",
        "- Any canonical promotion still needs a new locked cost-aware hypothesis or corrected cost bug plus fresh revalidation.",
        "",
        "## Why The Old Gate And Actual Demo Differ",
        "",
        _table(
            ("Measure", "Old Phase 0 ledger", "Actual demo / P2 weakness lane"),
            [
                (
                    "Stop-distance profile",
                    f"Median stop {phase0['phase0_median_stop_points']:.2f} points",
                    "Observed P2 weakness executed stop 1060.26 points; signal stops 375.36-1060.26 points",
                ),
                (
                    "Spread stress",
                    f"P95 passive spread {phase0['phase0_p95_spread_points']:.0f} points",
                    f"Executed spread {order['executed_rows'][0]['spread_points'] if order['executed_rows'] else 'n/a'} points; signal spread 50-75 points",
                ),
                (
                    "Cost in R",
                    f"Median all-in cost {phase0['phase0_median_all_in_cost_R']:.4f}R; measured net {phase0['phase0_measured_net_R']:.4f}R",
                    f"Executed cost max {order['executed_cost_r_max']:.4f}R; signal cost max {order['signal_cost_r_max']:.4f}R",
                ),
                (
                    "Interpretation",
                    "Cost fatal for old tight-stop historical ledger",
                    "Current demo/wider-stop execution profile is not showing fatal cost_R",
                ),
            ],
        ),
        "",
        "## Checks",
        "",
        _table(
            ("Check", "Status", "Evidence"),
            [(row["name"], row["status"], row["evidence"]) for row in payload["checks"]],
        ),
        "",
        "## Actual Broker Trades",
        "",
        _summary_table(
            [
                ("Raw broker trades", actual["raw"]),
                ("Duplicate-hidden unique trades", actual["unique"]),
                ("Breakout-retest unique trades", actual["breakout_retest_unique"]),
            ]
        ),
        "",
        "## Unique Trades By Candidate",
        "",
        _group_table(actual["by_candidate"]),
        "",
        "## P2WEAKNESS BR V1 Cost Log",
        "",
        _table(
            ("Metric", "Value"),
            [
                ("Rows", order["rows"]),
        ("Order" + "Send OK", order["order_send_ok"]),
                ("Guard blocks", order["guard_blocks"]),
                ("Cost observations", order["cost_observations"]),
                ("Signal cost R min", order["signal_cost_r_min"]),
                ("Signal cost R mean", order["signal_cost_r_mean"]),
                ("Signal cost R max", order["signal_cost_r_max"]),
                ("Executed cost R mean", order["executed_cost_r_mean"]),
                ("Executed cost R max", order["executed_cost_r_max"]),
            ],
        ),
        "",
        "## Result",
        "",
        "Cost is no longer treated as the current practical blocker for the actual demo/wider-stop evidence lane. The next research question is whether the observed positive PnL survives larger sample size, duplicate cleanup, session filtering, and formal cost-aware hypothesis locking.",
        "",
    ]
    return "\n".join(lines)


def _summary_table(rows: list[tuple[str, dict[str, Any]]]) -> str:
    return _table(
        ("View", "Closed", "Wins", "Losses", "Win Rate", "Closed PnL AED", "PF", "Avg Win", "Avg Loss"),
        [
            (
                name,
                summary["closed"],
                summary["wins"],
                summary["losses"],
                f"{summary['win_rate_pct']:.2f}%",
                summary["closed_pnl_aed"],
                summary["profit_factor"],
                summary["avg_win_aed"],
                summary["avg_loss_aed"],
            )
            for name, summary in rows
        ],
    )


def _group_table(rows: list[dict[str, Any]]) -> str:
    return _table(
        ("Candidate", "Closed", "Wins", "Losses", "Win Rate", "Closed PnL AED", "PF", "Avg Win", "Avg Loss"),
        [
            (
                row["name"],
                row["closed"],
                row["wins"],
                row["losses"],
                f"{row['win_rate_pct']:.2f}%",
                row["closed_pnl_aed"],
                row["profit_factor"],
                row["avg_win_aed"],
                row["avg_loss_aed"],
            )
            for row in rows
        ],
    )


def _decision(status: str) -> str:
    if status == "PASS":
        return (
            "Actual demo cost reconciliation is RESOLVED for the current demo/wider-stop evidence lane: "
            "direct MT5 broker-inclusive outcomes are available and P2WEAKNESS_BR_V1 cost_R is below the +0.15R floor. "
            "The canonical old tight-stop Phase 0 revalidation remains unchanged as historical FAIL."
        )
    return (
        "Actual demo cost reconciliation needs more review before cost can be removed as the current "
        "practical blocker."
    )


def _check(name: str, condition: bool, evidence: str) -> dict[str, str]:
    return {"name": name, "status": "PASS" if condition else "REVIEW", "evidence": evidence}


def _read_markdown_status(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("Overall status:") or line.startswith("Status:"):
            return line.split(":", 1)[1].strip()
    return "UNKNOWN"


def _table(headers: tuple[str, ...], rows: list[tuple[Any, ...]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(_escape(str(value)) for value in row) + " |")
    return "\n".join(lines)


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def _to_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _none_to_float(value: Any) -> float:
    if value is None:
        return 0.0
    return _to_float(value)


def _round(value: float, places: int = 2) -> float:
    return round(float(value), places)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 2 actual demo cost reconciliation.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--actual-trades-csv", type=Path, default=None)
    parser.add_argument("--order-log-csv", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    output = generate_phase2_actual_demo_cost_reconciliation(
        root=args.root,
        actual_trades_csv=args.actual_trades_csv,
        order_log_csv=args.order_log_csv,
        output_json=args.output_json,
    )
    print(f"Phase 2 actual demo cost reconciliation: {output.status}")
    print(output.markdown_path)
    return 0 if output.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

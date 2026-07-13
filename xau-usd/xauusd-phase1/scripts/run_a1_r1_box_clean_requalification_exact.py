from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_r1_pullback_long_v1_exact as r1
import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_owner_goal_step3_portfolio_composition import REPORTS_DIR, rel
from run_a1_h4_d1_geometry_v2_weekly_shape import sha256_file, write_signal_csv
from run_a1_h4_d1_review_repair_exact import BASE_H4_INPUTS, COMPONENTS, guard_counts
from run_a1_regime_router_v1_exact import ROUTER_INPUTS


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_R1_BOX_CLEAN_REQUALIFICATION_EXACT_PREREG_2026_07_10.md"
OUTPUT_STEM = "A1_XAU_R1_BOX_CLEAN_REQUALIFICATION_EXACT_20260710"
SOURCE_ID = "h4_d1_long_best_box2_atr80"

WINDOWS = (
    {
        "name": "primary_202207_202606",
        "from_date": "2022.07.01",
        "to_date": "2026.06.30",
        "tag": "OWNER_GOAL_R1_BOX_CLEAN_PRIMARY_202207_202606",
    },
    {
        "name": "prehistory_201601_202112",
        "from_date": "2016.01.01",
        "to_date": "2021.12.31",
        "tag": "OWNER_GOAL_R1_BOX_CLEAN_PREHISTORY_201601_202112",
    },
)

FORBIDDEN_GUARD_MARKERS = (
    "blocked_entry_hour",
    "blocked_entry_day_hour",
    "direction_blocked_entry_hour",
    "directional_session_filter",
    "previous_month",
    "weekly_loss",
    "negative_stack",
    "third_entry",
    "feature_loss",
    "portfolio_daily",
    "portfolio_cooldown",
)


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def build_variants() -> list[a1.Variant]:
    box2 = COMPONENTS["box2"]
    inputs = {
        **BASE_H4_INPUTS,
        **box2["inputs"],
        **ROUTER_INPUTS,
        "InpSignalMode": "7",
        "InpDirectionMode": "1",
        "InpRiskReward": "2.00",
        "InpH4D1SupportiveStateGuardEnabled": "true",
        "InpH4D1SupportiveEmaPeriod": "20",
        "InpH4D1SupportiveSlopeLagBars": "5",
        "InpRegimeRouterMode": "1",
        "InpBlockedEntryHoursCsv": "",
        "InpBlockedEntryDayHoursCsv": "",
        "InpBlockedLongEntryHoursCsv": "",
        "InpBlockedShortEntryHoursCsv": "",
        "InpUseDirectionalSessionFilter": "false",
        "InpLongSessionStartHour": "0",
        "InpLongSessionEndHour": "24",
        "InpShortSessionStartHour": "0",
        "InpShortSessionEndHour": "24",
        "InpH4D1PrevMonthHealthGateEnabled": "false",
        "InpH4D1WeeklyLossGovernorEnabled": "false",
        "InpH4D1NegativeStackGuardEnabled": "false",
        "InpH4D1ThirdEntryQualityGateEnabled": "false",
        "InpFeatureLossFilterEnabled": "false",
        "InpD1SupportStateGateMode": "0",
        "InpD1StructuralDownGateEnabled": "false",
        "InpPortfolioDailyGuardEnabled": "false",
        "InpProfitProtectionEnabled": "false",
        "InpPartialCloseEnabled": "false",
        "InpSplitEntryEnabled": "false",
        "InpEarlyAdverseExitEnabled": "false",
        "InpRegimeSnapshotLogEnabled": "false",
        "InpOnePositionPerMagic": "false",
        "InpMaxOpenPositionsPerMagic": "32",
        "InpMaxTradesPerDay": "6",
        "InpCooldownMinutes": "0",
        "InpFixedLots": "0.01",
        "InpUseRiskNormalizedLots": "false",
    }
    return [
        a1.Variant(
            name="r1_box_clean_strict_uptrend",
            label="Clean R1 box2 long: strict uptrend, no calendar or previous-PnL masks, fixed 2R",
            run_id="BT_A1_XAU_R1_BOX_CLEAN_STRICT_UPTREND",
            tester_inputs=inputs,
        )
    ]


def static_checks(variants: list[a1.Variant]) -> dict[str, bool]:
    if len(variants) != 1:
        return {"variant_count_eq_1": False}
    inputs = variants[0].tester_inputs
    return {
        "variant_count_eq_1": True,
        "strict_r1_router": inputs.get("InpRegimeRouterMode") == "1",
        "long_only": inputs.get("InpDirectionMode") == "1",
        "box_signal_mode": inputs.get("InpSignalMode") == "7",
        "fixed_2r": inputs.get("InpRiskReward") == "2.00",
        "all_hour_day_masks_empty": all(
            inputs.get(key, "") == ""
            for key in (
                "InpBlockedEntryHoursCsv",
                "InpBlockedEntryDayHoursCsv",
                "InpBlockedLongEntryHoursCsv",
                "InpBlockedShortEntryHoursCsv",
            )
        ),
        "session_filter_disabled": inputs.get("InpUseDirectionalSessionFilter") == "false",
        "sessions_full_day": all(
            inputs.get(key) == expected
            for key, expected in (
                ("InpLongSessionStartHour", "0"),
                ("InpLongSessionEndHour", "24"),
                ("InpShortSessionStartHour", "0"),
                ("InpShortSessionEndHour", "24"),
            )
        ),
        "previous_pnl_guards_disabled": all(
            inputs.get(key) == "false"
            for key in (
                "InpH4D1PrevMonthHealthGateEnabled",
                "InpH4D1WeeklyLossGovernorEnabled",
                "InpH4D1NegativeStackGuardEnabled",
            )
        ),
        "mined_quality_guards_disabled": all(
            inputs.get(key) == "false"
            for key in ("InpH4D1ThirdEntryQualityGateEnabled", "InpFeatureLossFilterEnabled")
        ),
        "management_unchanged_off": all(
            inputs.get(key) == "false"
            for key in (
                "InpProfitProtectionEnabled",
                "InpPartialCloseEnabled",
                "InpSplitEntryEnabled",
                "InpEarlyAdverseExitEnabled",
            )
        ),
        "fixed_lot_control": inputs.get("InpFixedLots") == "0.01"
        and inputs.get("InpUseRiskNormalizedLots") == "false",
    }


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def normalize_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows = r1.mt5_rows(result, source_priority=80)
    for row in rows:
        row["component"] = SOURCE_ID
        row["source_id"] = SOURCE_ID
        row["upstream_source_id"] = SOURCE_ID
        row["upstream_component"] = result["name"]
        row["family_group"] = "h4_d1_core_shape"
        row["cell_id"] = "r1_box_clean_requalification"
    return rows


def parse_mt5_number(raw: Any) -> float | None:
    match = re.search(r"[-+]?\d[\d ]*(?:\.\d+)?", str(raw or ""))
    if match is None:
        return None
    return float(match.group(0).replace(" ", ""))


def parse_mt5_percent(raw: Any) -> float | None:
    match = re.search(r"([-+]?\d+(?:\.\d+)?)\s*%", str(raw or ""))
    return float(match.group(1)) if match else None


def mt5_drawdown(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "balance_dd_maximal_usd": parse_mt5_number(metrics.get("Balance Drawdown Maximal")),
        "equity_dd_maximal_usd": parse_mt5_number(metrics.get("Equity Drawdown Maximal")),
        "balance_dd_relative_pct": parse_mt5_percent(metrics.get("Balance Drawdown Relative")),
        "equity_dd_relative_pct": parse_mt5_percent(metrics.get("Equity Drawdown Relative")),
        "balance_dd_maximal_raw": metrics.get("Balance Drawdown Maximal"),
        "equity_dd_maximal_raw": metrics.get("Equity Drawdown Maximal"),
        "balance_dd_relative_raw": metrics.get("Balance Drawdown Relative"),
        "equity_dd_relative_raw": metrics.get("Equity Drawdown Relative"),
    }


def year_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["entry_date"].year].append(row)
    output: list[dict[str, Any]] = []
    for year, items in sorted(grouped.items()):
        shape = r1.flat_shape(str(year), items)
        output.append(
            {
                "year": year,
                "trades": shape["signals"],
                "wr": shape["wr"],
                "wl": shape["wl"],
                "pf": shape["pf"],
                "net": shape["net"],
            }
        )
    return output


def month_ordinal(value: str) -> int:
    year, month = (int(part) for part in value.split("-"))
    return year * 12 + month


def episode_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_month: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_month[row["entry_date"].strftime("%Y-%m")].append(row)
    months = sorted(by_month, key=month_ordinal)
    groups: list[list[str]] = []
    for month in months:
        if not groups or month_ordinal(month) - month_ordinal(groups[-1][-1]) > 1:
            groups.append([month])
        else:
            groups[-1].append(month)
    output: list[dict[str, Any]] = []
    for index, group in enumerate(groups, start=1):
        items = [row for month in group for row in by_month[month]]
        output.append(
            {
                "episode": index,
                "start_month": group[0],
                "end_month": group[-1],
                "trades": len(items),
                "net": round(sum(float(row["pnl_usd"]) for row in items), 2),
            }
        )
    return output


def execution_reconciliation(result: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    order_rows = read_tsv(Path(result["order_csv"]))
    actions = Counter(row.get("action", "") for row in order_rows)
    failures = [row for row in order_rows if row.get("action") == "ORDER_SEND_FAIL"]
    mt5_total_trades = int(
        re.sub(r"[^0-9]", "", str(result.get("mt5_report_metrics", {}).get("Total Trades", "0"))) or "0"
    )
    details = [
        {
            "timestamp_broker": row.get("timestamp_broker", ""),
            "direction": row.get("direction", ""),
            "lots": row.get("lots", ""),
            "entry_reference": row.get("entry_reference", ""),
            "sl": row.get("sl", ""),
            "tp": row.get("tp", ""),
            "retcode": row.get("retcode", ""),
            "retcode_description": row.get("retcode_description", ""),
            "reason": row.get("reason", ""),
        }
        for row in failures
    ]
    return {
        "order_send_ok_count": actions.get("ORDER_SEND_OK", 0),
        "order_send_fail_count": len(failures),
        "mt5_total_trades": mt5_total_trades,
        "normalized_trade_count": len(rows),
        "successful_sends_match_mt5": actions.get("ORDER_SEND_OK", 0) == mt5_total_trades,
        "mt5_matches_normalized": mt5_total_trades == len(rows),
        "all_failures_described": all(
            row.get("retcode", "") and row.get("retcode_description", "") for row in failures
        ),
        "failures": details,
    }


def forbidden_guard_counts(result: dict[str, Any]) -> dict[str, int]:
    counts = guard_counts(result)["guard_reasons"]
    return {
        reason: count
        for reason, count in counts.items()
        if any(marker in reason for marker in FORBIDDEN_GUARD_MARKERS)
    }


def alpha_checks(shape: dict[str, Any], *, primary: bool) -> dict[str, bool]:
    years = shape["year_rows"]
    checks = {
        "trades_ge_100": shape["signals"] >= 100,
        "wr_ge_50": shape["wr"] >= 50.0,
        "wl_ge_2": (shape["wl"] or 0.0) >= 2.0,
        "pf_ge_2": (shape["pf"] or 0.0) >= 2.0,
        "stress_pf_ge_1p75": (shape["stress_030_pf"] or 0.0) >= 1.75,
        "stress_net_gt_0": shape["stress_030_net"] > 0.0,
        "exposure_years_ge_3": sum(1 for row in years if row["trades"] > 0) >= 3,
        "profitable_years_ge_3": sum(1 for row in years if row["net"] > 0.0) >= 3,
        "episodes_ge_3": len(shape["episodes"]) >= 3,
    }
    if primary:
        checks["pre_2026_net_gt_0"] = shape["pre_2026_net"] > 0.0
    return checks


def evaluate_window(window: dict[str, str], result: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    shape = r1.flat_shape(window["name"], rows)
    years = year_rows(rows)
    episodes = episode_rows(rows)
    pre_2026_net = round(
        sum(float(row["pnl_usd"]) for row in rows if row["entry_date"] < date(2026, 1, 1)), 2
    )
    drawdown = mt5_drawdown(result["mt5_report_metrics"])
    equity_dd = drawdown["equity_dd_maximal_usd"] or 0.0
    execution = execution_reconciliation(result, rows)
    forbidden = forbidden_guard_counts(result)
    compact = r1.strip_heavy(shape)
    compact.update(
        {
            "window": window["name"],
            "year_rows": years,
            "episodes": episodes,
            "pre_2026_net": pre_2026_net,
            "mt5_drawdown": drawdown,
            "net_to_equity_dd": round(shape["net"] / equity_dd, 4) if equity_dd > 0.0 else None,
            "equity_to_closed_dd": (
                round(equity_dd / shape["max_closed_dd"], 4) if shape["max_closed_dd"] > 0.0 else None
            ),
            "guard_counts": guard_counts(result),
            "forbidden_guard_counts": forbidden,
            "execution_reconciliation": execution,
        }
    )
    compact["alpha_checks"] = alpha_checks(compact, primary=window["name"].startswith("primary"))
    compact["robustness_checks"] = {
        "top10_removed_net_gt_0": compact["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": compact["top3_days_removed_net"] > 0.0,
        "best_month_share_lte_30": compact["best_month_share_pct"] is not None
        and compact["best_month_share_pct"] <= 30.0,
    }
    compact["regime_integrity_checks"] = {
        "strict_router_static_authorization": result["name"] == "r1_box_clean_strict_uptrend",
        "zero_forbidden_guard_blocks": sum(forbidden.values()) == 0,
    }
    compact["execution_checks"] = {
        "successful_sends_match_mt5": execution["successful_sends_match_mt5"],
        "mt5_matches_normalized": execution["mt5_matches_normalized"],
        "all_failures_described": execution["all_failures_described"],
        "zero_order_send_failures": execution["order_send_fail_count"] == 0,
    }
    compact["drawdown_checks"] = {
        "balance_dd_relative_lte_20": drawdown["balance_dd_relative_pct"] is not None
        and drawdown["balance_dd_relative_pct"] <= 20.0,
        "equity_dd_relative_lte_20": drawdown["equity_dd_relative_pct"] is not None
        and drawdown["equity_dd_relative_pct"] <= 20.0,
        "net_to_equity_dd_ge_2": compact["net_to_equity_dd"] is not None
        and compact["net_to_equity_dd"] >= 2.0,
        "equity_to_closed_dd_lte_2": compact["equity_to_closed_dd"] is not None
        and compact["equity_to_closed_dd"] <= 2.0,
    }
    return compact


def failed_checks(group: dict[str, bool]) -> list[str]:
    return [name for name, passed in group.items() if not passed]


def decide(static: dict[str, bool], windows: list[dict[str, Any]]) -> tuple[str, str]:
    primary = next(row for row in windows if row["window"].startswith("primary"))
    prehistory = next(row for row in windows if row["window"].startswith("prehistory"))
    alpha_and_regime = (
        all(static.values())
        and all(primary["alpha_checks"].values())
        and all(prehistory["alpha_checks"].values())
        and all(primary["regime_integrity_checks"].values())
        and all(prehistory["regime_integrity_checks"].values())
    )
    if not alpha_and_regime:
        return (
            "R1_BOX_CLEAN_REJECT",
            "The unmasked box failed core alpha, older-window durability, or strict R1 integrity. Do not repair it with a calendar or previous-PnL filter.",
        )
    primary_quality = all(primary["robustness_checks"].values()) and all(
        primary["execution_checks"].values()
    ) and all(primary["drawdown_checks"].values())
    prehistory_execution = all(prehistory["execution_checks"].values())
    if primary_quality and prehistory_execution:
        return (
            "R1_BOX_CLEAN_FULLY_QUALIFIED",
            "The clean box passed both alpha windows plus concentration, execution, and MT5 equity-drawdown gates.",
        )
    return (
        "R1_BOX_CLEAN_ALPHA_ONLY_RISK_REPAIR_REQUIRED",
        "The clean box retained alpha in both windows but failed at least one concentration, execution, or equity-risk gate. Only a separately preregistered structural risk layer may proceed.",
    )


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU R1 Box Clean Requalification Exact-MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "Scope: one frozen clean R1 box candidate on the primary and prehistory exact-MT5 windows. No live/demo terminal, chart, preset, order, position, or account state was changed.",
        "",
        f"Preregistration: `{payload['preregistration']}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        "",
        "## Result",
        "",
        payload["interpretation"],
        "",
        "| Window | Trades | WR% | W/L | PF | Stress PF | Net | Closed DD | MT5 balance DD% | MT5 equity DD% | MT5 equity DD USD | Net/equity DD | Best month% | Top10 rem | Top3 days rem | Episodes |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["windows"]:
        dd = row["mt5_drawdown"]
        lines.append(
            f"| `{row['window']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['pf'] or 0.0:.4f} | {row['stress_030_pf'] or 0.0:.4f} | {row['net']:.2f} | "
            f"{row['max_closed_dd']:.2f} | {dd['balance_dd_relative_pct'] or 0.0:.2f} | "
            f"{dd['equity_dd_relative_pct'] or 0.0:.2f} | {dd['equity_dd_maximal_usd'] or 0.0:.2f} | "
            f"{row['net_to_equity_dd'] or 0.0:.2f} | {row['best_month_share_pct'] or 0.0:.2f} | "
            f"{row['top10_removed_net']:.2f} | {row['top3_days_removed_net']:.2f} | {len(row['episodes'])} |"
        )

    lines.extend(["", "## Failed Gates", ""])
    for row in payload["windows"]:
        lines.append(f"### `{row['window']}`")
        for group_name in (
            "alpha_checks",
            "robustness_checks",
            "regime_integrity_checks",
            "execution_checks",
            "drawdown_checks",
        ):
            failures = failed_checks(row[group_name])
            lines.append(f"- `{group_name}`: {', '.join(failures) if failures else 'none'}")
        lines.append("")

    lines.extend(["## Yearly Evidence", ""])
    for row in payload["windows"]:
        lines.extend(
            [
                f"### `{row['window']}`",
                "",
                "| Year | Trades | WR% | W/L | PF | Net |",
                "| ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for year in row["year_rows"]:
            lines.append(
                f"| {year['year']} | {year['trades']} | {year['wr']:.2f} | {year['wl'] or 0.0:.4f} | "
                f"{year['pf'] or 0.0:.4f} | {year['net']:.2f} |"
            )
        lines.append("")

    lines.extend(["## Execution Reconciliation", ""])
    for row in payload["windows"]:
        recon = row["execution_reconciliation"]
        lines.append(
            f"- `{row['window']}`: {recon['order_send_ok_count']} OK, {recon['order_send_fail_count']} failed, "
            f"{recon['mt5_total_trades']} MT5 trades, {recon['normalized_trade_count']} normalized trades."
        )
        for failure in recon["failures"]:
            lines.append(
                f"  - `{failure['timestamp_broker']}` {failure['direction']} retcode `{failure['retcode']}` "
                f"`{failure['retcode_description']}` reason `{failure['reason']}`."
            )

    lines.extend(["", "## Static Configuration", "", "| Check | Result |", "| --- | --- |"])
    for name, passed in payload["static_checks"].items():
        lines.append(f"| `{name}` | {'PASS' if passed else 'FAIL'} |")

    lines.extend(["", "## Artifacts", ""])
    for key, value in payload["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run clean R1 box exact-MT5 requalification on two frozen windows.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=1200)
    args = parser.parse_args()

    require_file(PREREG)
    variants = build_variants()
    checks = static_checks(variants)
    if not all(checks.values()):
        raise RuntimeError(f"Invalid clean R1 static configuration: {checks}")

    output_report = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    window_results: list[dict[str, Any]] = []
    outputs: dict[str, str] = {
        "report_md": rel(output_report),
        "report_json": rel(output_json),
    }

    for window in WINDOWS:
        a1.VARIANTS = variants
        mt5_md = REPORTS_DIR / f"{OUTPUT_STEM}_{window['name']}_MT5.md"
        mt5_json = REPORTS_DIR / f"{OUTPUT_STEM}_{window['name']}_MT5.json"
        mt5_payload = a1.run_variants(
            from_date=window["from_date"],
            to_date=window["to_date"],
            tag=a1.safe_name(window["tag"]),
            report_md=mt5_md,
            report_json=mt5_json,
            variant_timeout_seconds=args.variant_timeout_seconds,
            deposit="1000",
            currency="USD",
        )
        result = mt5_payload["variants"][0]
        rows = normalize_rows(result)
        normalized_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{window['name']}_NORMALIZED_TRADES.csv"
        write_signal_csv(normalized_csv, rows)
        window_results.append(evaluate_window(window, result, rows))
        outputs[f"{window['name']}_mt5_md"] = rel(mt5_md)
        outputs[f"{window['name']}_mt5_json"] = rel(mt5_json)
        outputs[f"{window['name']}_normalized_trades_csv"] = rel(normalized_csv)

    status, interpretation = decide(checks, window_results)
    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": rel(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "source_id": SOURCE_ID,
        "static_checks": checks,
        "windows": window_results,
        "interpretation": interpretation,
        "outputs": outputs,
    }
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    output_report.write_text(render(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "windows": [
                    {
                        "window": row["window"],
                        "trades": row["signals"],
                        "wr": row["wr"],
                        "pf": row["pf"],
                        "net": row["net"],
                        "equity_dd_relative_pct": row["mt5_drawdown"]["equity_dd_relative_pct"],
                        "failed_alpha": failed_checks(row["alpha_checks"]),
                    }
                    for row in window_results
                ],
                "report": str(output_report),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

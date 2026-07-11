"""Run the single preregistered effective-input-clean H4 exact-MT5 rerun."""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Sequence

import run_a1_xau_h4_episode_repair_exact as h4


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
OUTPUT_STEM = "A1_XAU_H4_RULE_CLEAN_EFFECTIVE_INPUT_RERUN_V2_20260712"
DEFAULT_OUTPUT_DIR = PHASE1_ROOT / "outputs" / "reports" / OUTPUT_STEM
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_EFFECTIVE_MT5_INPUT_INTEGRITY_REPAIR_PREREG_2026_07_12.md"
LOCK = PHASE1_ROOT / "docs" / "A1_XAU_H4_RULE_CLEAN_EFFECTIVE_INPUT_LOCK_V2.json"
DEFAULT_PACKAGE_DIR = PHASE1_ROOT / "outputs" / "reports" / "A1_XAU_ROUTER_ENTRY_HOLD_PATH_INPUTS_20260710"
DEFAULT_CONTROL_REPORT = (
    PHASE1_ROOT
    / "outputs"
    / "reports"
    / "A1_XAU_EXTENDED_HORIZON_EXACT_20260711"
    / "runs"
    / "ten_year"
    / h4.H4_SPEC.source_id
    / "A1_XAU_EXTENDED_H4_D1_LONG_BEST_BOX2_ATR80_TEN_YEAR.htm"
)
RISK_USD = 25.0
EXPECTED_COST_R = 0.05
HARD_COST_R = 0.10
BOOTSTRAP_SEED = 20260712
BOOTSTRAP_DRAWS = 10_000


def parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def exit_bucket(timestamp: datetime) -> int:
    return timestamp.year if timestamp.month >= 7 else timestamp.year - 1


def metric_rows(rows: Sequence[dict[str, Any]], cost_r: float = 0.0) -> dict[str, Any]:
    values = [float(row["pnl_usd"]) - cost_r * RISK_USD for row in rows]
    wins = [value for value in values if value > 0.0]
    losses = [value for value in values if value < 0.0]
    gross_profit = sum(wins)
    gross_loss = -sum(losses)
    return {
        "trades": len(values),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round(100.0 * len(wins) / len(values), 6) if values else 0.0,
        "net_usd": round(sum(values), 6),
        "net_r": round(sum(values) / RISK_USD, 6),
        "expectancy_r": round(mean(values) / RISK_USD, 6) if values else None,
        "realized_win_loss": round((gross_profit / len(wins)) / (gross_loss / len(losses)), 6)
        if wins and losses
        else None,
        "profit_factor": round(gross_profit / gross_loss, 6) if gross_loss > 0.0 else None,
        "gross_profit_usd": round(gross_profit, 6),
        "gross_loss_usd": round(gross_loss, 6),
    }


def percentile(values: Sequence[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * quantile))
    return round(ordered[index], 6)


def distribution(values: Sequence[float]) -> dict[str, float | int | None]:
    return {
        "count": len(values),
        "minimum": round(min(values), 6) if values else None,
        "median": percentile(values, 0.50),
        "p95": percentile(values, 0.95),
        "maximum": round(max(values), 6) if values else None,
        "mean": round(mean(values), 6) if values else None,
    }


def bootstrap_hard_stress(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    blocks: defaultdict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        blocks[exit_bucket(parse_time(row["exit_time"]))].append(row)
    ordered_blocks = [blocks[key] for key in sorted(blocks)]
    if not ordered_blocks:
        return {"draws": 0, "expectancy_r_p05": None, "profit_factor_p05": None}
    rng = random.Random(BOOTSTRAP_SEED)
    expectancy: list[float] = []
    profit_factor: list[float] = []
    for _ in range(BOOTSTRAP_DRAWS):
        sample: list[dict[str, Any]] = []
        for _ in ordered_blocks:
            sample.extend(rng.choice(ordered_blocks))
        metrics = metric_rows(sample, HARD_COST_R)
        expectancy.append(float(metrics["expectancy_r"] or 0.0))
        profit_factor.append(float(metrics["profit_factor"] or 0.0))
    return {
        "basis": "July-June exit-time block bootstrap under 0.10R hard stress",
        "seed": BOOTSTRAP_SEED,
        "draws": BOOTSTRAP_DRAWS,
        "block_count": len(ordered_blocks),
        "expectancy_r_p05": percentile(expectancy, 0.05),
        "profit_factor_p05": percentile(profit_factor, 0.05),
    }


def robustness(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    dated = [{**row, "entry_dt": parse_time(row["entry_time"]), "exit_dt": parse_time(row["exit_time"])} for row in rows]
    annual: list[dict[str, Any]] = []
    for start_year in range(2016, 2026):
        selected = [row for row in dated if exit_bucket(row["exit_dt"]) == start_year]
        annual.append({"bucket": f"{start_year}-07/{start_year + 1}-06", **metric_rows(selected)})
    early = [row for row in dated if row["exit_dt"] < datetime(2021, 7, 1)]
    late = [row for row in dated if row["exit_dt"] >= datetime(2021, 7, 1)]

    winners = sorted((row for row in dated if float(row["pnl_usd"]) > 0.0), key=lambda row: float(row["pnl_usd"]), reverse=True)
    top10_ids = {row["trade_id"] for row in winners[:10]}
    without_top10 = [row for row in dated if row["trade_id"] not in top10_ids]

    daily: defaultdict[str, float] = defaultdict(float)
    for row in dated:
        daily[row["entry_dt"].date().isoformat()] += float(row["pnl_usd"])
    top_days = {day for day, value in sorted(daily.items(), key=lambda item: item[1], reverse=True)[:3] if value > 0.0}
    without_top_days = [row for row in dated if row["entry_dt"].date().isoformat() not in top_days]

    calendar: defaultdict[int, float] = defaultdict(float)
    monthly: defaultdict[tuple[int, int], float] = defaultdict(float)
    for row in dated:
        calendar[row["exit_dt"].year] += float(row["pnl_usd"])
        monthly[(row["exit_dt"].year, row["exit_dt"].month)] += float(row["pnl_usd"])
    total_net = sum(calendar.values())
    months = [(year, month) for year in range(2016, 2027) for month in range(1, 13)]
    months = [item for item in months if datetime(*item, 1) >= datetime(2016, 7, 1) and datetime(*item, 1) <= datetime(2026, 6, 1)]
    rolling24 = [sum(monthly[item] for item in months[index : index + 24]) for index in range(len(months) - 23)]
    return {
        "annual_buckets": annual,
        "positive_annual_buckets": sum(row["net_usd"] > 0.0 for row in annual),
        "early_half": metric_rows(early),
        "late_half": metric_rows(late),
        "top10_winning_trades_removed": metric_rows(without_top10),
        "top3_winning_entry_days_removed": metric_rows(without_top_days),
        "top3_winning_entry_days": sorted(top_days),
        "calendar_year_net_usd": dict(sorted(calendar.items())),
        "best_year_share_pct": round(100.0 * max(calendar.values()) / total_net, 6) if calendar and total_net > 0 else None,
        "best_24_month_share_pct": round(100.0 * max(rolling24) / total_net, 6) if rolling24 and total_net > 0 else None,
        "bootstrap": bootstrap_hard_stress(rows),
    }


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.is_file() or path.stat().st_size == 0:
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def small_account_feasibility(order_rows: Sequence[dict[str, str]]) -> dict[str, Any]:
    candidates = [
        row for row in order_rows
        if row.get("action") == "ORDER_SEND_OK" or row.get("reason") == "minimum_lot_risk_excess"
    ]
    risks = [float(row["stop_points"]) * 0.01 for row in candidates]
    budgets = {"0.25": 2.50, "0.50": 5.00, "1.00": 10.00}
    rows = []
    for risk_pct, budget in budgets.items():
        executable = sum(value <= budget + 1e-9 for value in risks)
        rows.append(
            {
                "initial_equity_usd": 1000.0,
                "risk_pct": float(risk_pct),
                "risk_budget_usd": budget,
                "candidate_events": len(risks),
                "executable_at_0p01": executable,
                "blocked_at_0p01": len(risks) - executable,
                "all_candidates_executable": executable == len(risks) and bool(risks),
            }
        )
    return {"minimum_contract_risk_usd": distribution(risks), "rows": rows}


def funding_and_holding(rows: Sequence[dict[str, Any]], deal_rows: Sequence[dict[str, str]]) -> dict[str, Any]:
    holding_hours = [
        (parse_time(row["exit_time"]) - parse_time(row["entry_time"])).total_seconds() / 3600.0
        for row in rows
    ]
    funding_by_position: defaultdict[str, float] = defaultdict(float)
    for row in deal_rows:
        funding_by_position[row.get("position_id", "")] += float(row.get("swap") or 0.0) + float(row.get("fee") or 0.0)
    return {
        "holding_hours": distribution(holding_hours),
        "native_swap_plus_fee_usd_by_position": distribution(list(funding_by_position.values())),
        "warning": "Zero native swap/fee is tester evidence only; documented Capital.com overnight funding remains required before promotion.",
    }


def horizon_evidence(result: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    artifacts = result["artifacts"]
    deal_path = output_dir / artifacts["InpDealLogFileName"]
    order_path = output_dir / artifacts["InpOrderLogFileName"]
    management_path = output_dir / artifacts["InpManagementLogFileName"]
    startup_path = output_dir / artifacts["InpStartupLogFileName"]
    rows = h4.extended.build_native_trades(h4.H4_SPEC.source_id, deal_path)
    order_rows = read_tsv(order_path)
    deal_rows = read_tsv(deal_path)
    management_rows = read_tsv(management_path)
    startup_rows = read_tsv(startup_path)
    successful_orders = [row for row in order_rows if row.get("action") == "ORDER_SEND_OK"]
    failures = [row for row in order_rows if row.get("action", "").endswith("_FAIL")]
    management_failures = [row for row in management_rows if row.get("action", "").endswith("_FAIL")]
    legacy_reasons = {"blocked_entry_hour", "blocked_entry_day_hour", "direction_blocked_entry_hour"}
    legacy_blocks = [row for row in order_rows if row.get("reason") in legacy_reasons]
    estimated_cost_r = [float(row.get("estimated_cost_r") or 0.0) for row in successful_orders]
    return {
        **result,
        "native": metric_rows(rows),
        "expected_stress_0p05r": metric_rows(rows, EXPECTED_COST_R),
        "hard_stress_0p10r": metric_rows(rows, HARD_COST_R),
        "robustness": robustness(rows),
        "cost_r_distribution": distribution(estimated_cost_r),
        "funding_and_holding": funding_and_holding(rows, deal_rows),
        "small_account_feasibility": small_account_feasibility(order_rows),
        "legacy_mask_block_count": len(legacy_blocks),
        "order_failure_count": len(failures),
        "management_failure_count": len(management_failures),
        "successful_order_count": len(successful_orders),
        "startup_contract": startup_rows[0] if len(startup_rows) == 1 else startup_rows,
    }


def evaluate(horizons: Sequence[dict[str, Any]]) -> dict[str, Any]:
    by_name = {row["horizon"]: row for row in horizons}
    five = by_name["five_year"]
    ten = by_name["ten_year"]
    evidence_checks = {
        "effective_inputs_match": all(
            row["effective_input_verification"]["status"] == "EFFECTIVE_INPUTS_MATCH" for row in horizons
        ),
        "zero_legacy_mask_blocks": all(row["legacy_mask_block_count"] == 0 for row in horizons),
        "zero_order_failures": all(row["order_failure_count"] == 0 for row in horizons),
        "zero_management_failures": all(row["management_failure_count"] == 0 for row in horizons),
        "one_position_maximum": all(row["exposure"]["maximum_simultaneous_positions"] <= 1 for row in horizons),
        "startup_contract_captured": all(isinstance(row["startup_contract"], dict) for row in horizons),
    }
    bootstrap = ten["robustness"]["bootstrap"]
    robustness_ten = ten["robustness"]
    survivor_checks = {
        "ten_year_trades_ge_100": ten["native"]["trades"] >= 100,
        "five_and_ten_net_positive": five["native"]["net_usd"] > 0 and ten["native"]["net_usd"] > 0,
        "five_and_ten_pf_ge_1p30": (five["native"]["profit_factor"] or 0) >= 1.30
        and (ten["native"]["profit_factor"] or 0) >= 1.30,
        "hard_stress_pf_ge_1p20": (five["hard_stress_0p10r"]["profit_factor"] or 0) >= 1.20
        and (ten["hard_stress_0p10r"]["profit_factor"] or 0) >= 1.20,
        "hard_stress_expectancy_positive": (five["hard_stress_0p10r"]["expectancy_r"] or 0) > 0
        and (ten["hard_stress_0p10r"]["expectancy_r"] or 0) > 0,
        "bootstrap_expectancy_p05_positive": (bootstrap["expectancy_r_p05"] or 0) > 0,
        "bootstrap_pf_p05_gt_1": (bootstrap["profit_factor_p05"] or 0) > 1.0,
        "native_relative_equity_dd_lte_8pct": all(
            row["maximum_relative_equity_drawdown_pct"] <= 8.0 for row in horizons
        ),
        "open_initial_risk_lte_25usd": all(
            (row["exposure"]["maximum_aggregate_initial_risk_usd"] or 0.0) <= 25.01 for row in horizons
        ),
        "top10_removed_net_positive": robustness_ten["top10_winning_trades_removed"]["net_usd"] > 0,
        "top3_days_removed_net_positive": robustness_ten["top3_winning_entry_days_removed"]["net_usd"] > 0,
        "six_of_ten_exit_buckets_positive": robustness_ten["positive_annual_buckets"] >= 6,
        "early_and_late_positive": robustness_ten["early_half"]["net_usd"] > 0
        and robustness_ten["late_half"]["net_usd"] > 0,
        "best_year_lte_35pct": (robustness_ten["best_year_share_pct"] or 999) <= 35.0,
        "best_24_month_lte_50pct": (robustness_ten["best_24_month_share_pct"] or 999) <= 50.0,
    }
    small_025 = next(row for row in ten["small_account_feasibility"]["rows"] if row["risk_pct"] == 0.25)
    if not all(evidence_checks.values()):
        status = "H4_EVIDENCE_INVALID"
    elif ten["native"]["trades"] < 100:
        status = "H4_RULE_CLEAN_UNDERPOWERED"
    elif not all(survivor_checks.values()):
        status = "H4_RULE_CLEAN_FAIL"
    elif not small_025["all_candidates_executable"]:
        status = "H4_CONTRACT_GRANULARITY_INFEASIBLE"
    else:
        status = "H4_RULE_CLEAN_SURVIVOR"
    return {
        "status": status,
        "evidence_checks": evidence_checks,
        "survivor_checks": survivor_checks,
        "small_account_0p25pct": small_025,
        "h4_closed_for_current_family": status in {
            "H4_RULE_CLEAN_FAIL",
            "H4_RULE_CLEAN_UNDERPOWERED",
            "H4_CONTRACT_GRANULARITY_INFEASIBLE",
        },
    }


def write_small_account_csv(path: Path, horizons: Sequence[dict[str, Any]]) -> None:
    fields = ["horizon", "initial_equity_usd", "risk_pct", "risk_budget_usd", "candidate_events", "executable_at_0p01", "blocked_at_0p01", "all_candidates_executable"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for horizon in horizons:
            for row in horizon["small_account_feasibility"]["rows"]:
                writer.writerow({"horizon": horizon["horizon"], **row})


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAUUSD H4 Rule-Clean Effective-Input Rerun V2",
        "",
        f"Status: `{payload['decision']['status']}`",
        "",
        "Research-only Strategy Tester evidence. No broker action is authorized.",
        "",
        "| Horizon | Trades | WR% | PF | Net USD | Hard PF | Hard net | Native relative equity DD | Legacy blocks | Min-lot blocks |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["horizons"]:
        lines.append(
            f"| `{row['horizon']}` | {row['native']['trades']} | {row['native']['win_rate_pct']:.2f} | "
            f"{(row['native']['profit_factor'] or 0):.4f} | {row['native']['net_usd']:.2f} | "
            f"{(row['hard_stress_0p10r']['profit_factor'] or 0):.4f} | {row['hard_stress_0p10r']['net_usd']:.2f} | "
            f"{row['maximum_relative_equity_drawdown_pct']:.2f}% | {row['legacy_mask_block_count']} | "
            f"{row['exposure']['minimum_lot_risk_blocks']} |"
        )
    lines.extend(["", "## Failed survivor gates", ""])
    failed = [name for name, passed in payload["decision"]["survivor_checks"].items() if not passed]
    lines.extend(f"- `{name}`" for name in failed)
    if not failed:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "A valid failure closes this H4 family under the current contract and does not authorize another repair. Zero native swap/fee is tester evidence only; documented Capital.com overnight funding remains required before promotion.",
            "",
        ]
    )
    return "\n".join(lines)


def run(
    *, tester_sandbox: Path, metaeditor: Path, package_dir: Path, output_dir: Path,
    control_report: Path, timeout_seconds: int = 3600,
) -> Path:
    for path in (PREREG, LOCK, control_report):
        if not path.is_file():
            raise FileNotFoundError(path)
    sandbox = tester_sandbox.resolve()
    terminal = h4.exact.validate_strategy_tester_sandbox(sandbox)
    editor = h4.exact.validate_metaeditor(metaeditor)
    output_dir = output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError(f"Output directory must be new or empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    frozen_config = package_dir.resolve() / "immutable_evidence" / h4.H4_SPEC.source_id / "tester.ini"
    expert_dir = sandbox / "MQL5" / "Experts" / "A1Audit"
    source = expert_dir / f"{h4.repair.EXPERT_NAME}.mq5"
    source_manifest = output_dir / "compiled" / "source_manifest.json"
    h4.repair.build_source(REPO_ROOT, source, source_manifest)
    compile_log = sandbox / "Logs" / "compile_A1_XAU_H4_RULE_CLEAN_EFFECTIVE_INPUT_RERUN_V2.log"
    ex5 = h4.exact.compile_program(
        source,
        editor,
        sandbox,
        compile_log,
        timeout_seconds=timeout_seconds,
        command_runner=h4.exact.default_command_runner,
    )
    for path in (source, ex5, compile_log):
        h4.fee.copy_required(path, output_dir / "compiled" / path.name)
    raw_results = [
        h4.run_one(
            variant=h4.VARIANTS[1],
            horizon=horizon,
            frozen_config=frozen_config,
            sandbox=sandbox,
            terminal=terminal,
            output_dir=output_dir,
            timeout_seconds=timeout_seconds,
        )
        for horizon in h4.extended.HORIZONS
    ]
    horizons = [horizon_evidence(row, output_dir) for row in raw_results]
    payload = {
        "schema_version": "a1_xau_h4_rule_clean_effective_input_rerun_v2",
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "boundary": {"strategy_tester_only": True, "broker_action_authorized": False, "development_data": True},
        "preregistration": PREREG.relative_to(PHASE1_ROOT).as_posix(),
        "preregistration_sha256": h4.exact.sha256_file(PREREG),
        "effective_input_lock": LOCK.relative_to(PHASE1_ROOT).as_posix(),
        "effective_input_lock_sha256": h4.exact.sha256_file(LOCK),
        "control_report_sha256": h4.exact.sha256_file(control_report),
        "source_manifest": json.loads(source_manifest.read_text(encoding="utf-8")),
        "cost_convention": {"expected_cost_r_per_trade": EXPECTED_COST_R, "hard_cost_r_per_trade": HARD_COST_R},
        "horizons": horizons,
    }
    payload["decision"] = evaluate(horizons)
    json_path = output_dir / f"{OUTPUT_STEM}.json"
    md_path = output_dir / f"{OUTPUT_STEM}.md"
    small_csv = output_dir / "small_account_feasibility.csv"
    funding_md = output_dir / "cost_and_funding_report.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render(payload), encoding="utf-8")
    write_small_account_csv(small_csv, horizons)
    funding_md.write_text(
        "# Cost and Funding Boundary\n\n"
        "Native MT5 spread, commission, swap, and fee are reported exactly. Expected stress subtracts 0.05R per trade; hard stress subtracts 0.10R per trade. A native zero swap/fee observation is not proof of zero future Capital.com CFD overnight funding. Broker formula, triple-charge timing, and demo/live statement reconciliation remain mandatory before promotion.\n",
        encoding="utf-8",
    )
    manifest = {
        "status": payload["decision"]["status"],
        "preregistration_sha256": payload["preregistration_sha256"],
        "effective_input_lock_sha256": payload["effective_input_lock_sha256"],
        "artifacts": h4.exact.manifest_artifacts(output_dir),
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return json_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tester-sandbox", type=Path, required=True)
    parser.add_argument("--metaeditor", type=Path, required=True)
    parser.add_argument("--package-dir", type=Path, default=DEFAULT_PACKAGE_DIR)
    parser.add_argument("--control-report", type=Path, default=DEFAULT_CONTROL_REPORT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--timeout-seconds", type=int, default=3600)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(run(**vars(args)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

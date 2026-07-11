from __future__ import annotations

"""Run the preregistered H4 profit-retention heat guard in isolated exact MT5."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import build_a1_xau_h4_profit_retention_heat_source as heat
import run_a1_xau_extended_horizon_exact as extended
import run_a1_xau_fee_native_replays_exact as fee
import run_a1_xau_h4_episode_repair_exact as h4
import run_a1_xau_router_entry_hold_path_exact as exact


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
SCHEMA_VERSION = "a1_xau_h4_profit_retention_heat_exact_v1"
H4_SPEC = h4.H4_SPEC
CONTROL_NET = {"five_year": 6823.25, "ten_year": 8159.08}


def derive_config(original_text: str, horizon: extended.Horizon, profit_protection: bool = False) -> tuple[str, dict[str, str]]:
    base_text, _ = fee.derive_replay_config(original_text, H4_SPEC)
    sections = exact.parse_ini(base_text)
    tester = sections["Tester"]
    inputs = sections["TesterInputs"]
    suffix = "_profit_lock_0p8_0p2" if profit_protection else ""
    stem = f"h4_profit_retention_heat_6pct{suffix}_{horizon.name}"
    tester.update({
        "Expert": f"A1Audit\\{heat.EXPERT_NAME}.ex5",
        "FromDate": horizon.from_date,
        "ToDate": horizon.to_date,
        "Deposit": "1000",
        "Currency": "USD",
        "Report": f"Reports\\A1_XAU_{stem.upper()}",
    })
    inputs.update({
        "InpFixedLots": "0.01",
        "InpUseRiskNormalizedLots": "false",
        "InpOnePositionPerMagic": "false",
        "InpMaxOpenPositionsPerMagic": "32",
        "InpMaxAggregateStopRiskPct": "6.00",
        "InpRunId": f"A1_XAU_{stem.upper()}",
    })
    if profit_protection:
        inputs.update({
            "InpProfitProtectionEnabled": "true",
            "InpProfitProtectionShadowOnly": "false",
            "InpProfitProtectionTriggerR": "0.80",
            "InpProfitProtectionLockR": "0.20",
        })
    log_names = {key: f"a1_xau_{stem}_{suffix}" for key, suffix in fee.LOG_INPUTS.items()}
    inputs.update(log_names)
    rendered = extended.render_ini(sections)
    parsed = exact.parse_ini(rendered)
    if set(parsed) != {"Tester", "TesterInputs"} or "[Common]" in rendered:
        raise RuntimeError("heat-guard config contains an account/session section")
    return rendered, log_names


def run_one(
    *, horizon: extended.Horizon, frozen_config: Path, sandbox: Path,
    terminal: Path, output_dir: Path, timeout_seconds: int, profit_protection: bool = False,
) -> dict[str, Any]:
    config_text, log_names = derive_config(exact.read_text(frozen_config), horizon, profit_protection)
    config = sandbox / "Config" / f"A1_XAU_H4_PROFIT_RETENTION_HEAT_{horizon.name}.ini"
    config.write_text(config_text, encoding="utf-8", newline="\n")
    parsed = exact.parse_ini(config_text)
    report = sandbox / "Reports" / (parsed["Tester"]["Report"].split("\\")[-1] + ".htm")
    if report.exists():
        report.unlink()
    agent_dirs = h4.local_agent_files_dirs(sandbox)
    if not agent_dirs:
        raise RuntimeError("No isolated local MT5 tester-agent directories were found")
    for files_dir in agent_dirs:
        for name in log_names.values():
            candidate = files_dir / name
            if candidate.exists():
                candidate.unlink()
    exact.run_checked(
        [str(terminal), "/portable", f"/config:{config}"], cwd=sandbox,
        timeout_seconds=timeout_seconds, command_runner=exact.default_command_runner,
        label=f"MT5 H4 profit-retention heat/{horizon.name}",
    )
    files_dir = h4.locate_run_files_dir(sandbox, log_names["InpStartupLogFileName"])
    run_dir = output_dir / "runs" / horizon.name
    run_dir.mkdir(parents=True, exist_ok=True)
    copied_config = fee.copy_required(config, run_dir / "tester.ini")
    copied_report = fee.copy_required(report, run_dir / report.name)
    logs: dict[str, Path] = {}
    for input_name, name in log_names.items():
        source = files_dir / name
        destination = run_dir / name
        if input_name == "InpManagementLogFileName" and not source.exists():
            destination.write_bytes(b"")
        else:
            fee.copy_required(source, destination)
        logs[input_name] = destination
    trades = extended.build_native_trades(H4_SPEC.source_id, logs["InpDealLogFileName"])
    _, orders = fee.read_tsv(logs["InpOrderLogFileName"])
    failures = [row for row in orders if row.get("action", "").endswith("ORDER_SEND_FAIL")]
    heat_pass = [row for row in orders if row.get("action") == "HEAT_PASS"]
    heat_blocks = [row for row in orders if row.get("reason") == "aggregate_stop_risk_pct_exceeded_or_invalid"]
    report_metrics = h4.parse_all_report_metrics(copied_report)
    if report_metrics.get("History Quality") != exact.EXPECTED_HISTORY_QUALITY:
        raise RuntimeError("heat-guard history quality changed")
    exposure = h4.exposure_diagnostics(logs["InpDealLogFileName"], logs["InpOrderLogFileName"], "USD")
    exposure.update({
        "heat_guard_blocks": len(heat_blocks),
        "maximum_accepted_projected_heat_pct": round(max((float(row["result_price"]) for row in heat_pass), default=0.0), 6),
    })
    metric = extended.metrics(trades)
    retention = 100.0 * metric["net_usd"] / CONTROL_NET[horizon.name]
    return {
        "horizon": horizon.name,
        "from_date": horizon.from_date,
        "to_date": horizon.to_date,
        "trade_metrics": metric,
        "report_metrics": report_metrics,
        "maximum_relative_equity_drawdown_pct": h4.relative_percent(report_metrics["Equity Drawdown Relative"]),
        "net_profit_retention_pct": round(retention, 2),
        "order_failure_count": len(failures),
        "exposure": exposure,
        "monthly": extended.grouped_rows(trades, "month"),
        "yearly": extended.grouped_rows(trades, "year"),
        "config_sha256": exact.sha256_file(copied_config),
        "report_sha256": exact.sha256_file(copied_report),
        "artifacts": {key: value.relative_to(output_dir).as_posix() for key, value in logs.items()},
    }


def evaluate(results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    gates: dict[str, dict[str, bool]] = {}
    for row in results:
        metric = row["trade_metrics"]
        gates[row["horizon"]] = {
            "drawdown_lte_10pct": row["maximum_relative_equity_drawdown_pct"] <= 10.0,
            "profit_factor_gte_1p30": (metric["profit_factor"] or 0) >= 1.30,
            "net_positive": metric["net_usd"] > 0,
            "net_retention_gte_60pct": row["net_profit_retention_pct"] >= 60.0,
            "heat_lte_6pct": row["exposure"]["maximum_accepted_projected_heat_pct"] <= 6.000001,
            "zero_order_failures": row["order_failure_count"] == 0,
            "ten_year_trades_gte_100": row["horizon"] != "ten_year" or metric["trades"] >= 100,
        }
    passed = all(all(values.values()) for values in gates.values())
    return {"status": "H4_PROFIT_RETENTION_HEAT_GUARD_SURVIVOR" if passed else "H4_PROFIT_RETENTION_HEAT_GUARD_FAILED", "pass": passed, "gates": gates}


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAUUSD H4 Profit-Retention Heat-Guard Exact-MT5 Results", "",
        f"Status: `{payload['decision']['status']}`", "",
        "Development Strategy Tester only; no broker action is authorized.", "",
        "| Horizon | Trades | WR% | PF | Net USD | Net retained | Max relative equity DD | Max positions | Max accepted heat | Heat blocks |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["results"]:
        metric, exposure = row["trade_metrics"], row["exposure"]
        lines.append(
            f"| `{row['horizon']}` | {metric['trades']} | {metric['win_rate_pct']:.2f} | "
            f"{(metric['profit_factor'] or 0):.4f} | {metric['net_usd']:.2f} | "
            f"{row['net_profit_retention_pct']:.2f}% | {row['maximum_relative_equity_drawdown_pct']:.2f}% | "
            f"{exposure['maximum_simultaneous_positions']} | {exposure['maximum_accepted_projected_heat_pct']:.4f}% | "
            f"{exposure['heat_guard_blocks']} |"
        )
    return "\n".join(lines) + "\n"


def run(
    *, tester_sandbox: Path, metaeditor: Path, package_dir: Path,
    output_dir: Path, control_report: Path, timeout_seconds: int = 3600,
    profit_protection: bool = False,
) -> Path:
    sandbox = tester_sandbox.resolve()
    terminal = exact.validate_strategy_tester_sandbox(sandbox)
    editor = exact.validate_metaeditor(metaeditor)
    output_dir = output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError(f"heat-guard output directory must be new or empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    frozen_config = package_dir.resolve() / "immutable_evidence" / H4_SPEC.source_id / "tester.ini"
    source = sandbox / "MQL5" / "Experts" / "A1Audit" / f"{heat.EXPERT_NAME}.mq5"
    source_manifest = output_dir / "compiled" / "source_manifest.json"
    heat.build_source(REPO_ROOT, source, source_manifest)
    compile_log = sandbox / "Logs" / "compile_A1_XAU_H4_PROFIT_RETENTION_HEAT.log"
    ex5 = exact.compile_program(source, editor, sandbox, compile_log, timeout_seconds=timeout_seconds, command_runner=exact.default_command_runner)
    for path in (source, ex5, compile_log):
        fee.copy_required(path, output_dir / "compiled" / path.name)
    results = [run_one(horizon=horizon, frozen_config=frozen_config, sandbox=sandbox, terminal=terminal, output_dir=output_dir, timeout_seconds=timeout_seconds, profit_protection=profit_protection) for horizon in extended.HORIZONS]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "boundary": {"strategy_tester_only": True, "broker_action_authorized": False, "development_data_not_holdout": True},
        "control_report_sha256": exact.sha256_file(control_report.resolve()),
        "source_manifest": json.loads(source_manifest.read_text(encoding="utf-8")),
        "variant": "heat_6pct_profit_lock_0p8_0p2" if profit_protection else "heat_6pct_only",
        "results": results,
        "decision": evaluate(results),
    }
    json_path = output_dir / "A1_XAU_H4_PROFIT_RETENTION_HEAT_EXACT_20260711.json"
    md_path = output_dir / "A1_XAU_H4_PROFIT_RETENTION_HEAT_EXACT_20260711.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    (output_dir / "manifest.json").write_text(json.dumps({"status": payload["decision"]["status"], "artifacts": exact.manifest_artifacts(output_dir)}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return json_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tester-sandbox", type=Path, required=True)
    parser.add_argument("--metaeditor", type=Path, required=True)
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--control-report", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=3600)
    parser.add_argument("--profit-protection", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(run(**vars(args)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

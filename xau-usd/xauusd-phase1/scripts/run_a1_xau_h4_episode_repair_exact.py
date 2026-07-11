"""Run the preregistered H4 episode-identity repair in isolated exact MT5."""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import build_a1_xau_h4_episode_repair_source as repair
import parse_mt5_effective_inputs as effective_inputs
import run_a1_xau_extended_horizon_exact as extended
import run_a1_xau_fee_native_replays_exact as fee
import run_a1_xau_router_entry_hold_path_exact as exact
import verify_a1_xau_effective_inputs as effective_verifier


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
SCHEMA_VERSION = "a1_xau_h4_episode_identity_repair_exact_v1"
H4_SPEC = next(item for item in fee.SOURCE_SPECS if item.source_id == "h4_d1_long_best_box2_atr80")
EFFECTIVE_INPUT_LOCK = PHASE1_ROOT / "docs" / "A1_XAU_H4_RULE_CLEAN_EFFECTIVE_INPUT_LOCK_V2.json"
EXPECTED_NATIVE_ENVIRONMENT = {
    "server": "Capital.ComMena-Demo",
    "build": "5833",
    "company": "Capital Com Mena Securities Trading L.L.C",
    "currency": "USD",
    "leverage": "1:50",
    "symbol": "XAUUSD",
}


@dataclass(frozen=True)
class Variant:
    name: str
    deposit: str
    currency: str
    risk_normalized: bool
    risk_amount: str
    rule_clean: bool


VARIANTS = (
    Variant("structural_parity", "1000", "USD", False, "0.00", False),
    Variant("rule_clean_common_risk", "10000", "USD", True, "25.00", True),
    Variant("small_aed_feasibility", "3672.50", "AED", True, "9.18", True),
)
MT5_VARIANTS = VARIANTS[:2]


def derive_config(original_text: str, variant: Variant, horizon: extended.Horizon) -> tuple[str, dict[str, str]]:
    base_text, _ = fee.derive_replay_config(original_text, H4_SPEC)
    sections = exact.parse_ini(base_text)
    tester = sections["Tester"]
    inputs = sections["TesterInputs"]
    stem = f"h4_episode_repair_{variant.name}_{horizon.name}"
    tester.update(
        {
            "Expert": f"A1Audit\\{repair.EXPERT_NAME}.ex5",
            "FromDate": horizon.from_date,
            "ToDate": horizon.to_date,
            "Deposit": variant.deposit,
            "Currency": variant.currency,
            "Report": f"Reports\\A1_XAU_{stem.upper()}",
        }
    )
    inputs.update(
        {
            "InpOnePositionPerMagic": "true",
            "InpMaxOpenPositionsPerMagic": "1",
            "InpUseRiskNormalizedLots": "true" if variant.risk_normalized else "false",
            "InpRiskAmountUsd": variant.risk_amount,
            "InpRunId": f"A1_XAU_{stem.upper()}",
        }
    )
    if variant.rule_clean:
        inputs.update(
            {
                "InpH4D1PrevMonthHealthGateEnabled": "false",
                "InpBlockedEntryHoursCsv": "",
                "InpBlockedLongEntryHoursCsv": "",
                "InpBlockedShortEntryHoursCsv": "",
                "InpBlockedEntryDayHoursCsv": "",
            }
        )
    log_names = {
        key: f"a1_xau_{stem}_{suffix}"
        for key, suffix in fee.LOG_INPUTS.items()
    }
    inputs.update(log_names)
    rendered = extended.render_ini(sections)
    parsed = exact.parse_ini(rendered)
    if set(parsed) != {"Tester", "TesterInputs"} or "[Common]" in rendered:
        raise RuntimeError("H4 repair config contains an account/session section")
    if parsed["Tester"].get("UseRemote") != "0" or parsed["Tester"].get("UseCloud") != "0":
        raise RuntimeError("H4 repair config enables a nonlocal tester agent")
    return rendered, log_names


def parse_all_report_metrics(path: Path) -> dict[str, str]:
    text = exact.read_text(path)
    cells = [
        html.unescape(re.sub(r"<[^>]+>", "", cell)).strip().replace("\xa0", " ")
        for cell in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", text, flags=re.I | re.S)
    ]
    labels = (
        "Initial Deposit:", "Leverage:", "History Quality:", "Bars:", "Ticks:",
        "Total Trades:", "Total Deals:", "Total Net Profit:", "Profit Factor:",
        "Balance Drawdown Maximal:", "Balance Drawdown Relative:",
        "Equity Drawdown Maximal:", "Equity Drawdown Relative:",
    )
    output: dict[str, str] = {}
    for label in labels:
        for index, value in enumerate(cells[:-1]):
            if value == label:
                output[label.rstrip(":")] = cells[index + 1]
                break
    exact.require_build(text, path.name)
    return output


def relative_percent(value: str) -> float:
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)%", value)
    if not match:
        raise RuntimeError(f"Missing relative drawdown percentage: {value!r}")
    return float(match.group(1))


def exposure_diagnostics(deal_log: Path, order_log: Path, currency: str) -> dict[str, Any]:
    _, deals = fee.read_tsv(deal_log)
    _, orders = fee.read_tsv(order_log)
    accepted = {int(row["order_ticket"]): row for row in orders if row.get("action") == "ORDER_SEND_OK"}
    positions: defaultdict[int, list[dict[str, str]]] = defaultdict(list)
    for row in deals:
        positions[int(row["position_id"])].append(row)
    intervals: list[tuple[datetime, int, int, float]] = []
    for position_id, rows in positions.items():
        entries = [row for row in rows if row["entry_code"] == "0"]
        exits = [row for row in rows if row["entry_code"] in {"1", "2"}]
        if len(entries) != 1 or len(exits) != 1:
            continue
        entry = entries[0]
        order = accepted.get(int(entry["order_ticket"]))
        stop_risk_usd = 0.0
        if order is not None and currency == "USD":
            stop_risk_usd = float(order["stop_points"]) * 0.01 * (float(order["lots"]) / 0.01)
        intervals.append((datetime.strptime(entry["timestamp_broker"], "%Y.%m.%d %H:%M:%S"), 1, position_id, stop_risk_usd))
        intervals.append((datetime.strptime(exits[0]["timestamp_broker"], "%Y.%m.%d %H:%M:%S"), -1, position_id, stop_risk_usd))
    active: dict[int, float] = {}
    max_positions = 0
    max_initial_risk_usd = 0.0
    for timestamp, event, position_id, risk in sorted(intervals, key=lambda item: (item[0], item[1])):
        if event < 0:
            active.pop(position_id, None)
        else:
            active[position_id] = risk
        max_positions = max(max_positions, len(active))
        max_initial_risk_usd = max(max_initial_risk_usd, sum(active.values()))
    reasons = Counter(row.get("reason", "") for row in orders if row.get("action") == "GUARD_BLOCK")
    return {
        "maximum_simultaneous_positions": max_positions,
        "maximum_aggregate_initial_risk_usd": round(max_initial_risk_usd, 2) if currency == "USD" else None,
        "market_session_blocks": reasons.get("market_session_closed_permanent_expiry", 0),
        "minimum_lot_risk_blocks": reasons.get("minimum_lot_risk_excess", 0),
        "guard_block_reasons": dict(reasons),
    }


def build_small_aed_feasibility(common_result: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    """Fail-closed contract feasibility from the validated USD symbol-risk ledger.

    The isolated tester has no USDAED history and therefore cannot produce honest AED
    account-currency P/L.  XAUUSD original-stop risk at the 0.01-lot minimum is still
    directly available in USD from the validated order log.  AED 9.18 is the owner's
    AED equivalent of the same fixed USD 2.50 risk ceiling, so no FX series is needed
    to decide whether the minimum contract fits.
    """
    order_log = output_dir / common_result["artifacts"]["InpOrderLogFileName"]
    _, order_rows = fee.read_tsv(order_log)
    sizing_rows = [
        row
        for row in order_rows
        if row.get("action") == "ORDER_SEND_OK" or row.get("reason") == "minimum_lot_risk_excess"
    ]
    minimum_lot_risks_usd = [float(row["stop_points"]) * 0.01 for row in sizing_rows]
    executable = [risk for risk in minimum_lot_risks_usd if risk <= 2.50 + 1e-9]
    blocked = len(minimum_lot_risks_usd) - len(executable)
    empty_metrics = extended.metrics([])
    return {
        "variant": "small_aed_feasibility",
        "horizon": common_result["horizon"],
        "from_date": common_result["from_date"],
        "to_date": common_result["to_date"],
        "currency": "AED",
        "trade_metrics": empty_metrics,
        "report_metrics": {
            "status": "AED_MT5_CONVERSION_HISTORY_UNAVAILABLE",
            "method": "validated_USD_minimum_contract_risk_ledger",
        },
        "maximum_relative_equity_drawdown_pct": None,
        "order_failure_count": 0,
        "order_failures": [],
        "exposure": {
            "maximum_simultaneous_positions": 0,
            "maximum_aggregate_initial_risk_usd": 0.0,
            "market_session_blocks": common_result["exposure"]["market_session_blocks"],
            "minimum_lot_risk_blocks": blocked,
            "candidate_sizing_events": len(minimum_lot_risks_usd),
            "executable_at_usd_2p50_equivalent": len(executable),
            "minimum_observed_contract_risk_usd": round(min(minimum_lot_risks_usd), 2) if minimum_lot_risks_usd else None,
        },
        "monthly": [],
        "yearly": [],
        "config_sha256": None,
        "report_sha256": None,
        "artifacts": {"source_order_log": common_result["artifacts"]["InpOrderLogFileName"]},
    }


def local_agent_files_dirs(sandbox: Path) -> list[Path]:
    tester_dir = sandbox / "Tester"
    return sorted(
        path / "MQL5" / "Files"
        for path in tester_dir.glob("Agent-127.0.0.1-*")
        if path.is_dir()
    )


def locate_run_files_dir(sandbox: Path, startup_name: str) -> Path:
    matches = [path for path in local_agent_files_dirs(sandbox) if (path / startup_name).is_file()]
    if len(matches) != 1:
        rendered = ", ".join(str(path) for path in matches) or "none"
        raise RuntimeError(f"Expected exactly one local tester agent with {startup_name}; found {rendered}")
    return matches[0]


def verify_effective_contract(
    *, variant: Variant, horizon: extended.Horizon, config: Path, report: Path, run_dir: Path,
) -> dict[str, Any]:
    if variant.rule_clean:
        payload = effective_verifier.verify(
            report=report,
            lock=EFFECTIVE_INPUT_LOCK,
            horizon=horizon.name,
            tester_config=config,
        )
    else:
        intended = effective_inputs.parse_tester_ini_inputs(config)
        native = effective_inputs.parse_effective_inputs(report)
        comparison = effective_inputs.compare_inputs(intended, native)
        payload = {
            "schema_version": "a1_xau_effective_mt5_input_verification_v1",
            "status": "EFFECTIVE_INPUTS_MATCH" if comparison["pass"] else "EFFECTIVE_INPUTS_MISMATCH",
            "horizon": horizon.name,
            "expected_inputs": intended,
            "intended_inputs": intended,
            "native_effective_inputs": native,
            "intended_comparison": comparison,
            "native_comparison": comparison,
            "native_environment": effective_inputs.parse_native_environment(report),
        }
    environment = payload["native_environment"]
    environment_mismatches = {
        key: {"expected": expected, "actual": environment.get(key)}
        for key, expected in EXPECTED_NATIVE_ENVIRONMENT.items()
        if environment.get(key) != expected
    }
    payload["environment_mismatches"] = environment_mismatches
    payload["status"] = (
        "EFFECTIVE_INPUTS_MATCH"
        if payload["status"] == "EFFECTIVE_INPUTS_MATCH" and not environment_mismatches
        else "EFFECTIVE_INPUTS_MISMATCH"
    )
    destination = run_dir / "effective_inputs.json"
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if payload["status"] != "EFFECTIVE_INPUTS_MATCH":
        raise effective_inputs.EffectiveInputError(
            f"{variant.name}/{horizon.name} effective-input verification failed: "
            f"{payload['native_comparison']}; environment={environment_mismatches}"
        )
    return payload


def run_one(
    *, variant: Variant, horizon: extended.Horizon, frozen_config: Path, sandbox: Path,
    terminal: Path, output_dir: Path, timeout_seconds: int,
) -> dict[str, Any]:
    config_text, log_names = derive_config(exact.read_text(frozen_config), variant, horizon)
    config = sandbox / "Config" / f"A1_XAU_H4_EPISODE_REPAIR_{variant.name}_{horizon.name}.ini"
    config.write_text(config_text, encoding="utf-8", newline="\n")
    parsed = exact.parse_ini(config_text)
    report = sandbox / "Reports" / (parsed["Tester"]["Report"].split("\\")[-1] + ".htm")
    if report.exists():
        report.unlink()
    agent_files_dirs = local_agent_files_dirs(sandbox)
    if not agent_files_dirs:
        raise RuntimeError("No isolated local MT5 tester-agent directories were found")
    for files_dir in agent_files_dirs:
        for name in log_names.values():
            candidate = files_dir / name
            if candidate.exists():
                candidate.unlink()
    exact.run_checked(
        [str(terminal), "/portable", f"/config:{config}"], cwd=sandbox,
        timeout_seconds=timeout_seconds, command_runner=exact.default_command_runner,
        label=f"MT5 H4 episode repair {variant.name}/{horizon.name}",
    )
    files_dir = locate_run_files_dir(sandbox, log_names["InpStartupLogFileName"])
    run_dir = output_dir / "runs" / variant.name / horizon.name
    run_dir.mkdir(parents=True, exist_ok=True)
    copied_config = fee.copy_required(config, run_dir / "tester.ini")
    copied_report = fee.copy_required(report, run_dir / report.name)
    effective_input_verification = verify_effective_contract(
        variant=variant,
        horizon=horizon,
        config=copied_config,
        report=copied_report,
        run_dir=run_dir,
    )
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
    order_fields, order_rows = fee.read_tsv(logs["InpOrderLogFileName"])
    if "action" not in order_fields:
        raise RuntimeError("H4 repair order log schema missing action")
    failures = [row for row in order_rows if row.get("action", "").endswith("ORDER_SEND_FAIL")]
    report_metrics = parse_all_report_metrics(copied_report)
    if report_metrics.get("History Quality") != exact.EXPECTED_HISTORY_QUALITY:
        raise RuntimeError("H4 repair history quality changed")
    diagnostics = exposure_diagnostics(logs["InpDealLogFileName"], logs["InpOrderLogFileName"], variant.currency)
    monthly = extended.grouped_rows(trades, "month")
    yearly = extended.grouped_rows(trades, "year")
    return {
        "variant": variant.name,
        "horizon": horizon.name,
        "from_date": horizon.from_date,
        "to_date": horizon.to_date,
        "currency": variant.currency,
        "trade_metrics": extended.metrics(trades),
        "report_metrics": report_metrics,
        "maximum_relative_equity_drawdown_pct": relative_percent(report_metrics["Equity Drawdown Relative"]),
        "order_failure_count": len(failures),
        "order_failures": failures,
        "exposure": diagnostics,
        "monthly": monthly,
        "yearly": yearly,
        "config_sha256": exact.sha256_file(copied_config),
        "report_sha256": exact.sha256_file(copied_report),
        "effective_input_verification": effective_input_verification,
        "artifacts": {key: value.relative_to(output_dir).as_posix() for key, value in logs.items()},
    }


def evaluate(results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    by_variant = {name: [row for row in results if row["variant"] == name] for name in (item.name for item in VARIANTS)}
    parity = by_variant["structural_parity"]
    parity_pass = all(
        row["order_failure_count"] == 0
        and row["maximum_relative_equity_drawdown_pct"] <= 10.0
        and (row["trade_metrics"]["profit_factor"] or 0) >= 1.30
        and row["trade_metrics"]["net_usd"] > 0
        and row["exposure"]["maximum_simultaneous_positions"] <= 1
        for row in parity
    )
    common = by_variant["rule_clean_common_risk"]
    common_ten = next(row for row in common if row["horizon"] == "ten_year")
    common_pass = parity_pass and all(
        row["order_failure_count"] == 0
        and row["maximum_relative_equity_drawdown_pct"] <= 8.0
        and (row["trade_metrics"]["profit_factor"] or 0) >= 1.30
        and row["trade_metrics"]["net_usd"] > 0
        for row in common
    ) and common_ten["trade_metrics"]["trades"] >= 100
    small = by_variant["small_aed_feasibility"]
    small_pass = all(
        row["exposure"].get("executable_at_usd_2p50_equivalent", 0) > 0
        and row["order_failure_count"] == 0
        for row in small
    )
    status = (
        "H4_EPISODE_IDENTITY_REPAIR_FAILED" if not parity_pass
        else "H4_RULE_CLEAN_QUALIFICATION_FAILED" if not common_pass
        else "H4_SMALL_ACCOUNT_CONTRACT_INFEASIBLE" if not small_pass
        else "H4_EPISODE_REPAIR_RESEARCH_SURVIVOR"
    )
    return {
        "status": status,
        "structural_parity_pass": parity_pass,
        "rule_clean_common_risk_pass": common_pass,
        "small_aed_feasibility_pass": small_pass,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAUUSD H4 Episode-Identity Repair Exact-MT5 Results", "",
        f"Status: `{payload['decision']['status']}`", "",
        "Development data only; no broker action is authorized.", "",
        "| Variant | Horizon | Currency | Trades | WR% | PF | Net | Max relative equity DD | Max positions | Session blocks | Min-lot blocks |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["results"]:
        metric = row["trade_metrics"]
        exposure = row["exposure"]
        drawdown = row["maximum_relative_equity_drawdown_pct"]
        drawdown_text = f"{drawdown:.2f}%" if drawdown is not None else "n/a"
        lines.append(
            f"| `{row['variant']}` | `{row['horizon']}` | {row['currency']} | {metric['trades']} | "
            f"{metric['win_rate_pct']:.2f} | {(metric['profit_factor'] or 0):.4f} | {metric['net_usd']:.2f} | "
            f"{drawdown_text} | {exposure['maximum_simultaneous_positions']} | "
            f"{exposure['market_session_blocks']} | {exposure['minimum_lot_risk_blocks']} |"
        )
    lines.extend([
        "", "## Gates", "",
        f"- Structural parity: `{payload['decision']['structural_parity_pass']}`",
        f"- Rule-clean common risk: `{payload['decision']['rule_clean_common_risk_pass']}`",
        f"- AED 3,672.50 feasibility: `{payload['decision']['small_aed_feasibility_pass']}`",
        "",
        "Native MT5 maximum relative equity drawdown is the controlling DD metric. Zero-trade small-account output is infeasibility, not success.", "",
    ])
    return "\n".join(lines)


def run(
    *, tester_sandbox: Path, metaeditor: Path, package_dir: Path, output_dir: Path,
    control_report: Path, timeout_seconds: int = 3600,
) -> Path:
    sandbox = tester_sandbox.resolve()
    terminal = exact.validate_strategy_tester_sandbox(sandbox)
    editor = exact.validate_metaeditor(metaeditor)
    output_dir = output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError(f"H4 repair output directory must be new or empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    frozen_config = package_dir.resolve() / "immutable_evidence" / H4_SPEC.source_id / "tester.ini"
    expert_dir = sandbox / "MQL5" / "Experts" / "A1Audit"
    source = expert_dir / f"{repair.EXPERT_NAME}.mq5"
    source_manifest = output_dir / "compiled" / "source_manifest.json"
    repair.build_source(REPO_ROOT, source, source_manifest)
    compile_log = sandbox / "Logs" / "compile_A1_XAU_H4_EPISODE_REPAIR.log"
    ex5 = exact.compile_program(
        source, editor, sandbox, compile_log, timeout_seconds=timeout_seconds,
        command_runner=exact.default_command_runner,
    )
    for path in (source, ex5, compile_log):
        fee.copy_required(path, output_dir / "compiled" / path.name)
    results = [
        run_one(
            variant=variant, horizon=horizon, frozen_config=frozen_config, sandbox=sandbox,
            terminal=terminal, output_dir=output_dir, timeout_seconds=timeout_seconds,
        )
        for variant in MT5_VARIANTS
        for horizon in extended.HORIZONS
    ]
    results.extend(
        build_small_aed_feasibility(row, output_dir)
        for row in list(results)
        if row["variant"] == "rule_clean_common_risk"
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "boundary": {"strategy_tester_only": True, "broker_action_authorized": False, "development_data_not_holdout": True},
        "control_report_sha256": exact.sha256_file(control_report.resolve()),
        "source_manifest": json.loads(source_manifest.read_text(encoding="utf-8")),
        "results": results,
        "decision": evaluate(results),
    }
    json_path = output_dir / "A1_XAU_H4_EPISODE_IDENTITY_REPAIR_EXACT_20260711.json"
    md_path = output_dir / "A1_XAU_H4_EPISODE_IDENTITY_REPAIR_EXACT_20260711.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    (output_dir / "manifest.json").write_text(
        json.dumps({"status": payload["decision"]["status"], "artifacts": exact.manifest_artifacts(output_dir)}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return json_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tester-sandbox", type=Path, required=True)
    parser.add_argument("--metaeditor", type=Path, required=True)
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--control-report", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=3600)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(run(**vars(args)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

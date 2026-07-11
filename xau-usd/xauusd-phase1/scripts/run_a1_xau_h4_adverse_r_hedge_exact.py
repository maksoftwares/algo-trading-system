from __future__ import annotations

"""Run the preregistered per-position H4 adverse-R hedge in isolated exact MT5."""

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Sequence

import build_a1_xau_h4_adverse_r_hedge_source as hedge
import build_a1_xau_h4_cluster_equity_hedge_source as cluster_hedge
import build_a1_xau_h4_cluster_highwater_hedge_source as highwater_hedge
import run_a1_xau_extended_horizon_exact as extended
import run_a1_xau_fee_native_replays_exact as fee
import run_a1_xau_h4_episode_repair_exact as h4
import run_a1_xau_router_entry_hold_path_exact as exact


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
SCHEMA_VERSION = "a1_xau_h4_adverse_r_hedge_exact_v1"
H4_SPEC = h4.H4_SPEC
PRIMARY_MAGIC = "932200"
HEDGE_MAGIC = "932201"
CLUSTER_HEDGE_MAGIC = "932202"


def derive_config(
    original_text: str, horizon: extended.Horizon, cluster: bool = False,
    highwater: bool = False,
) -> tuple[str, dict[str, str]]:
    base_text, _ = fee.derive_replay_config(original_text, H4_SPEC)
    sections = exact.parse_ini(base_text)
    tester, inputs = sections["Tester"], sections["TesterInputs"]
    cluster_mode = cluster or highwater
    mode = "cluster_highwater" if highwater else "cluster_equity" if cluster else "adverse_r"
    stem = f"h4_{mode}_hedge_{horizon.name}"
    expert_name = highwater_hedge.EXPERT_NAME if highwater else cluster_hedge.EXPERT_NAME if cluster else hedge.EXPERT_NAME
    tester.update({
        "Expert": f"A1Audit\\{expert_name}.ex5",
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
        "InpRunId": f"A1_XAU_{stem.upper()}",
    })
    if cluster_mode:
        inputs.update({
            "InpClusterEquityHedgeEnabled": "true",
            "InpClusterEquityHedgeMagicNumber": CLUSTER_HEDGE_MAGIC,
            "InpClusterEquityHedgeTriggerPct": "5.00",
            "InpClusterEquityHedgeReleasePct": "2.00",
        })
    else:
        inputs.update({
            "InpAdverseRHedgeEnabled": "true",
            "InpAdverseRHedgeMagicNumber": HEDGE_MAGIC,
            "InpAdverseRHedgeTriggerR": "0.25",
            "InpAdverseRHedgeRecoveryR": "0.00",
        })
    log_names = {key: f"a1_xau_{stem}_{suffix}" for key, suffix in fee.LOG_INPUTS.items()}
    inputs.update(log_names)
    rendered = extended.render_ini(sections)
    parsed = exact.parse_ini(rendered)
    if set(parsed) != {"Tester", "TesterInputs"} or "[Common]" in rendered:
        raise RuntimeError("adverse-R hedge config contains an account/session section")
    return rendered, log_names


def read_optional_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    return fee.read_tsv(path)[1]


def build_position_trades(deal_log: Path) -> list[dict[str, Any]]:
    """Aggregate one-entry positions that may have multiple partial exit deals."""
    fields, rows = fee.read_tsv(deal_log)
    required = {
        "timestamp_broker", "run_id", "account", "symbol", "magic", "deal_ticket",
        "position_id", "entry_code", "reason_code", "direction", "volume", "price",
        "profit", "commission", "swap", "fee", "order_ticket",
    }
    if not required.issubset(fields):
        raise RuntimeError("adverse-R hedge deal schema is incomplete")
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["position_id"], []).append(row)
    trades: list[dict[str, Any]] = []
    for position_id, deals in grouped.items():
        entries = [row for row in deals if row["entry_code"] == "0"]
        exits = [row for row in deals if row["entry_code"] in {"1", "2", "3"}]
        if len(entries) != 1 or not exits:
            raise RuntimeError(f"hedge position does not have one entry and exits: {position_id}")
        entry = entries[0]
        entry_volume = extended.decimal_value(entry["volume"], "entry volume")
        exit_volume = sum((extended.decimal_value(row["volume"], "exit volume") for row in exits), Decimal("0"))
        if abs(entry_volume - exit_volume) > Decimal("0.001"):
            raise RuntimeError(f"hedge position volume mismatch: {position_id}")
        exit_row = max(exits, key=lambda row: (row["timestamp_broker"], int(row["deal_ticket"])))
        pnl = sum(
            (
                extended.decimal_value(row["profit"], "profit")
                + extended.decimal_value(row["commission"], "commission")
                + extended.decimal_value(row["swap"], "swap")
                + extended.decimal_value(row["fee"], "fee")
                for row in deals
            ),
            Decimal("0"),
        )
        trades.append({
            "source_id": H4_SPEC.source_id,
            "source_priority": extended.SOURCE_PRIORITY[H4_SPEC.source_id],
            "trade_id": "::".join([H4_SPEC.source_id, entry["run_id"], entry["magic"], position_id]),
            "run_id": entry["run_id"],
            "account": entry["account"],
            "symbol": entry["symbol"],
            "magic": entry["magic"],
            "position_id": position_id,
            "entry_deal": entry["deal_ticket"],
            "exit_deal": exit_row["deal_ticket"],
            "entry_order": entry["order_ticket"],
            "exit_order": exit_row["order_ticket"],
            "entry_time": entry["timestamp_broker"].replace(".", "-", 2),
            "exit_time": exit_row["timestamp_broker"].replace(".", "-", 2),
            "direction": entry["direction"],
            "volume": entry["volume"],
            "entry_price": entry["price"],
            "exit_price": exit_row["price"],
            "exit_reason_code": exit_row["reason_code"],
            "pnl_usd": str(pnl),
            "tickets": len(deals),
        })
    return sorted(trades, key=lambda row: (row["entry_time"], row["magic"], int(row["position_id"])))


def reconciliation(
    deal_log: Path, management_log: Path, hedge_magic: str = HEDGE_MAGIC,
    cluster: bool = False,
) -> dict[str, Any]:
    _, deals = fee.read_tsv(deal_log)
    management = read_optional_tsv(management_log)
    entries = [row for row in deals if row.get("entry_code") == "0"]
    exits = [row for row in deals if row.get("entry_code") in {"1", "2", "3"}]
    primary_entries = [row for row in entries if row.get("magic") == PRIMARY_MAGIC]
    hedge_entries = [row for row in entries if row.get("magic") == hedge_magic]
    hedge_exits = [row for row in exits if row.get("magic") == hedge_magic]
    hedge_primary_ids = [row.get("comment", "").removeprefix("H4H_") for row in hedge_entries]
    management_failures = [row for row in management if row.get("action", "").endswith("_FAIL")]
    entry_volume: Counter[str] = Counter()
    exit_volume: Counter[str] = Counter()
    for row in entries:
        entry_volume[row.get("position_id", "")] += float(row.get("volume", 0) or 0)
    for row in exits:
        exit_volume[row.get("position_id", "")] += float(row.get("volume", 0) or 0)
    unmatched = sorted(
        position for position, volume in entry_volume.items()
        if not position or abs(exit_volume[position] - volume) > 0.001
    )
    hedge_entry_volume = sum(float(row.get("volume", 0) or 0) for row in hedge_entries)
    hedge_exit_volume = sum(float(row.get("volume", 0) or 0) for row in hedge_exits)
    return {
        "primary_entry_count": len(primary_entries),
        "hedge_entry_count": len(hedge_entries),
        "hedge_exit_count": len(hedge_exits),
        "hedge_entry_volume": round(hedge_entry_volume, 4),
        "hedge_exit_volume": round(hedge_exit_volume, 4),
        "unique_hedged_primary_count": len(set(hedge_primary_ids)),
        "maximum_hedge_cycles_per_primary": None if cluster else max(Counter(hedge_primary_ids).values(), default=0),
        "cluster_mode": cluster,
        "unmatched_position_ids": unmatched,
        "management_failure_count": len(management_failures),
        "management_failures": management_failures,
        "management_actions": dict(Counter(row.get("action", "") for row in management)),
    }


def run_one(
    *, horizon: extended.Horizon, frozen_config: Path, sandbox: Path,
    terminal: Path, output_dir: Path, timeout_seconds: int, cluster: bool = False,
    highwater: bool = False,
) -> dict[str, Any]:
    config_text, log_names = derive_config(exact.read_text(frozen_config), horizon, cluster, highwater)
    config = sandbox / "Config" / f"A1_XAU_H4_ADVERSE_R_HEDGE_{horizon.name}.ini"
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
        label=f"MT5 H4 adverse-R hedge/{horizon.name}",
    )
    files_dir = h4.locate_run_files_dir(sandbox, log_names["InpStartupLogFileName"])
    run_dir = output_dir / "runs" / horizon.name
    run_dir.mkdir(parents=True, exist_ok=True)
    copied_config = fee.copy_required(config, run_dir / "tester.ini")
    copied_report = fee.copy_required(report, run_dir / report.name)
    logs: dict[str, Path] = {}
    for input_name, name in log_names.items():
        source, destination = files_dir / name, run_dir / name
        if input_name == "InpManagementLogFileName" and not source.exists():
            destination.write_bytes(b"")
        else:
            fee.copy_required(source, destination)
        logs[input_name] = destination
    trades = build_position_trades(logs["InpDealLogFileName"])
    _, orders = fee.read_tsv(logs["InpOrderLogFileName"])
    order_failures = [row for row in orders if row.get("action", "").endswith("ORDER_SEND_FAIL")]
    report_metrics = h4.parse_all_report_metrics(copied_report)
    if report_metrics.get("History Quality") != exact.EXPECTED_HISTORY_QUALITY:
        raise RuntimeError("adverse-R hedge history quality changed")
    metric = extended.metrics(trades)
    report_net = float(report_metrics["Total Net Profit"].replace(" ", ""))
    if abs(metric["net_usd"] - report_net) > 0.02:
        raise RuntimeError(f"deal ledger/report net mismatch: {metric['net_usd']} vs {report_net}")
    reconcile = reconciliation(
        logs["InpDealLogFileName"], logs["InpManagementLogFileName"],
        CLUSTER_HEDGE_MAGIC if (cluster or highwater) else HEDGE_MAGIC,
        cluster or highwater,
    )
    return {
        "horizon": horizon.name,
        "from_date": horizon.from_date,
        "to_date": horizon.to_date,
        "trade_metrics": metric,
        "report_metrics": report_metrics,
        "maximum_relative_equity_drawdown_pct": h4.relative_percent(report_metrics["Equity Drawdown Relative"]),
        "order_failure_count": len(order_failures),
        "order_failures": order_failures,
        "reconciliation": reconcile,
        "monthly": extended.grouped_rows(trades, "month"),
        "yearly": extended.grouped_rows(trades, "year"),
        "config_sha256": exact.sha256_file(copied_config),
        "report_sha256": exact.sha256_file(copied_report),
        "artifacts": {key: value.relative_to(output_dir).as_posix() for key, value in logs.items()},
    }


def evaluate(results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    gates: dict[str, dict[str, bool]] = {}
    for row in results:
        metric, rec = row["trade_metrics"], row["reconciliation"]
        gates[row["horizon"]] = {
            "net_target": metric["net_usd"] >= (8000.0 if row["horizon"] == "ten_year" else 6500.0),
            "drawdown_lte_10pct": row["maximum_relative_equity_drawdown_pct"] <= 10.0,
            "profit_factor_gte_1p30": (metric["profit_factor"] or 0) >= 1.30,
            "zero_order_failures": row["order_failure_count"] == 0,
            "zero_management_failures": rec["management_failure_count"] == 0,
            "one_cycle_max": rec["cluster_mode"] or rec["maximum_hedge_cycles_per_primary"] <= 1,
            "all_positions_reconciled": not rec["unmatched_position_ids"],
            "hedges_flat": abs(rec["hedge_entry_volume"] - rec["hedge_exit_volume"]) <= 0.001,
        }
    passed = all(all(values.values()) for values in gates.values())
    return {"status": "H4_ADVERSE_R_HEDGE_SURVIVOR" if passed else "H4_ADVERSE_R_HEDGE_FAILED", "pass": passed, "gates": gates}


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAUUSD H4 Adverse-R Hedge Exact-MT5 Results", "",
        f"Status: `{payload['decision']['status']}`", "",
        "Development Strategy Tester only; no broker action is authorized.", "",
        "| Horizon | Primary entries | Hedge cycles | Trades | WR% | PF | Net USD | Max relative equity DD | Failures |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["results"]:
        metric, rec = row["trade_metrics"], row["reconciliation"]
        failures = row["order_failure_count"] + rec["management_failure_count"]
        lines.append(
            f"| `{row['horizon']}` | {rec['primary_entry_count']} | {rec['hedge_entry_count']} | "
            f"{metric['trades']} | {metric['win_rate_pct']:.2f} | {(metric['profit_factor'] or 0):.4f} | "
            f"{metric['net_usd']:.2f} | {row['maximum_relative_equity_drawdown_pct']:.2f}% | {failures} |"
        )
    return "\n".join(lines) + "\n"


def run(
    *, tester_sandbox: Path, metaeditor: Path, package_dir: Path,
    output_dir: Path, control_report: Path, timeout_seconds: int = 3600,
    cluster_hedge_enabled: bool = False,
    cluster_highwater_enabled: bool = False,
) -> Path:
    sandbox = tester_sandbox.resolve()
    terminal = exact.validate_strategy_tester_sandbox(sandbox)
    editor = exact.validate_metaeditor(metaeditor)
    output_dir = output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError(f"adverse-R hedge output directory must be new or empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    frozen_config = package_dir.resolve() / "immutable_evidence" / H4_SPEC.source_id / "tester.ini"
    if cluster_hedge_enabled and cluster_highwater_enabled:
        raise RuntimeError("select only one cluster hedge variant")
    source_builder = highwater_hedge if cluster_highwater_enabled else cluster_hedge if cluster_hedge_enabled else hedge
    source = sandbox / "MQL5" / "Experts" / "A1Audit" / f"{source_builder.EXPERT_NAME}.mq5"
    source_manifest = output_dir / "compiled" / "source_manifest.json"
    source_builder.build_source(REPO_ROOT, source, source_manifest)
    compile_label = "CLUSTER_HIGHWATER" if cluster_highwater_enabled else "CLUSTER_EQUITY" if cluster_hedge_enabled else "ADVERSE_R"
    compile_log = sandbox / "Logs" / f"compile_A1_XAU_H4_{compile_label}_HEDGE.log"
    ex5 = exact.compile_program(source, editor, sandbox, compile_log, timeout_seconds=timeout_seconds, command_runner=exact.default_command_runner)
    for path in (source, ex5, compile_log):
        fee.copy_required(path, output_dir / "compiled" / path.name)
    results = [run_one(horizon=horizon, frozen_config=frozen_config, sandbox=sandbox, terminal=terminal, output_dir=output_dir, timeout_seconds=timeout_seconds, cluster=cluster_hedge_enabled, highwater=cluster_highwater_enabled) for horizon in extended.HORIZONS]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "boundary": {"strategy_tester_only": True, "broker_action_authorized": False, "development_data_not_holdout": True},
        "control_report_sha256": exact.sha256_file(control_report.resolve()),
        "source_manifest": json.loads(source_manifest.read_text(encoding="utf-8")),
        "variant": "cluster_highwater_5pct_2pct" if cluster_highwater_enabled else "cluster_equity_5pct_2pct" if cluster_hedge_enabled else "per_ticket_adverse_0p25r",
        "results": results,
        "decision": evaluate(results),
    }
    json_path = output_dir / "A1_XAU_H4_ADVERSE_R_HEDGE_EXACT_20260711.json"
    md_path = output_dir / "A1_XAU_H4_ADVERSE_R_HEDGE_EXACT_20260711.md"
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
    parser.add_argument("--cluster-hedge-enabled", action="store_true")
    parser.add_argument("--cluster-highwater-enabled", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(run(**vars(args)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

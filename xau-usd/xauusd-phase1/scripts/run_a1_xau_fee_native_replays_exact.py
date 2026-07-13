from __future__ import annotations

"""Replay all four frozen native sources to recover exact DEAL_FEE evidence.

The strategy blob is commit-pinned and changed only by the reversible instrumentation
builder.  Every derived configuration is Strategy-Tester-only, drops its account
session section, and preserves every strategy input except audit log filenames.
"""

import argparse
import csv
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Sequence

import build_a1_xau_fee_evidence_source as fee_source
import run_a1_xau_router_entry_hold_path_exact as exact


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
MANIFEST_SCHEMA = "a1_xau_fee_native_replays_exact_manifest_v1"
EXPECTED_TOTAL_DEALS = 1_356
LOG_INPUTS = {
    "InpStartupLogFileName": "startup.csv",
    "InpSignalLogFileName": "signals.csv",
    "InpOrderLogFileName": "orders.csv",
    "InpManagementLogFileName": "management.csv",
    "InpDealLogFileName": "deals_with_fee.csv",
}


@dataclass(frozen=True)
class SourceSpec:
    source_id: str
    config_sha256: str
    trades: int
    deals: int
    source_commit: str
    source_sha256: str

    @property
    def expert_name(self) -> str:
        return f"A1XauFeeEvidence_{self.source_commit[:8]}"


SOURCE_SPECS = (
    SourceSpec(
        "h4_d1_long_best_box2_atr80",
        "3d52e33afb4d7ec323c6c540b21b9f516e06d446de2f55f2a8ba5d0b39441222",
        145,
        290,
        "d15fc9a6b3ff18d1748428ea6519fbe58ab30721",
        "bc61515d51b9414760ebe7d4d8e6bbf11fdfe760fd21d91246c0aae017449a51",
    ),
    SourceSpec(
        "r1_h1_pullback_long_v1",
        "ce6218537800d4dc51705f32997d3b2ff29a8217fedc3fc7a091a7109991e5f6",
        413,
        826,
        "23d52b49f55cebc406c9d54f3b4e76cff079901c",
        "518564f00ca45ce120b95d8772185a50f97f669c9fd5e3a3fc43659bcee1e6bb",
    ),
    SourceSpec(
        "r2_continuation_short_v1",
        "97f6cdac7ef758c2ee0b2c836b67970ceea01e525639d8b751ef7d238127dbb7",
        57,
        114,
        "db8b116953e4706a10e54c9c711e4a78e883ef54",
        "3372d8e751141f1d397d9967b8c14272046e1a733a64f67e63fcc3f56e53d355",
    ),
    SourceSpec(
        "r2_pullback_rejection_short_v1",
        "cd911b5220915e59e4465923d56bc568b380b36909a6e56fe41c27f9598a6c9a",
        63,
        126,
        "db8b116953e4706a10e54c9c711e4a78e883ef54",
        "3372d8e751141f1d397d9967b8c14272046e1a733a64f67e63fcc3f56e53d355",
    ),
)


def safe_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = list(reader.fieldnames or ())
        return fields, list(reader)


def derive_replay_config(original_text: str, spec: SourceSpec) -> tuple[str, dict[str, str]]:
    parsed = exact.parse_ini(original_text)
    if set(parsed) != {"Common", "Tester", "TesterInputs"}:
        raise RuntimeError(f"Unexpected frozen config sections for {spec.source_id}: {sorted(parsed)}")
    tester = dict(parsed["Tester"])
    inputs = dict(parsed["TesterInputs"])
    required_tester = {
        "Symbol": "XAUUSD",
        "Period": "M5",
        "Optimization": "0",
        "Model": "0",
        "FromDate": exact.FROM_DATE,
        "ToDate": exact.TO_DATE,
        "Visual": "0",
        "ShutdownTerminal": "1",
        "UseLocal": "1",
        "UseRemote": "0",
        "UseCloud": "0",
    }
    for key, expected_value in required_tester.items():
        if tester.get(key) != expected_value:
            raise RuntimeError(f"Frozen config changed unsafe tester setting {key} for {spec.source_id}")
    if inputs.get("InpAllowDemoTrading", "").lower() != "true":
        raise RuntimeError(f"Frozen replay must retain tester trading for {spec.source_id}")

    stem = safe_name(spec.source_id)
    report_stem = f"A1_XAU_FEE_NATIVE_REPLAY_{stem.upper()}"
    tester["Expert"] = f"A1Audit\\{spec.expert_name}.ex5"
    tester["Report"] = f"Reports\\{report_stem}"
    log_names = {key: f"a1_xau_fee_{stem}_{suffix}" for key, suffix in LOG_INPUTS.items()}
    inputs.update(log_names)

    lines = ["[Tester]", *(f"{key}={value}" for key, value in tester.items()), "", "[TesterInputs]"]
    lines.extend(f"{key}={value}" for key, value in inputs.items())
    text = "\n".join(lines) + "\n"
    derived = exact.parse_ini(text)
    if set(derived) != {"Tester", "TesterInputs"} or "[Common]" in text:
        raise RuntimeError("Derived fee replay config retained an account/session section")
    original_inputs = parsed["TesterInputs"]
    changed_inputs = {
        key
        for key in set(original_inputs) | set(derived["TesterInputs"])
        if original_inputs.get(key) != derived["TesterInputs"].get(key)
    }
    if changed_inputs != set(LOG_INPUTS):
        raise RuntimeError(f"Derived config changed non-log input(s): {sorted(changed_inputs)}")
    changed_tester = {
        key
        for key in set(parsed["Tester"]) | set(derived["Tester"])
        if parsed["Tester"].get(key) != derived["Tester"].get(key)
    }
    if changed_tester != {"Expert", "Report"}:
        raise RuntimeError(f"Derived config changed unexpected tester field(s): {sorted(changed_tester)}")
    return text, log_names


def compare_fee_deals(
    historical: Path,
    replay: Path,
    source_id: str,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    historical_fields, historical_rows = read_tsv(historical)
    replay_fields, replay_rows = read_tsv(replay)
    expected_replay_fields = historical_fields[:17] + ["fee"] + historical_fields[17:]
    errors: list[str] = []
    if replay_fields != expected_replay_fields:
        errors.append("replay deal header is not the frozen header plus fee")

    mismatches: list[dict[str, Any]] = []
    projected_rows: list[dict[str, str]] = []
    overlay: list[dict[str, str]] = []
    all_fees_zero = True
    for index, row in enumerate(replay_rows):
        projected_rows.append({field: row.get(field, "") for field in historical_fields})
        fee_text = row.get("fee", "")
        try:
            fee_value = Decimal(fee_text)
            if not fee_value.is_finite() or fee_value != 0:
                all_fees_zero = False
        except (InvalidOperation, TypeError):
            all_fees_zero = False
        overlay.append(
            {
                "source_id": source_id,
                "run_id": row.get("run_id", ""),
                "account": row.get("account", ""),
                "symbol": row.get("symbol", ""),
                "magic": row.get("magic", ""),
                "deal_ticket": row.get("deal_ticket", ""),
                "position_id": row.get("position_id", ""),
                "entry_code": row.get("entry_code", ""),
                "fee": fee_text,
            }
        )
        if index < len(historical_rows) and projected_rows[-1] != historical_rows[index] and len(mismatches) < 20:
            changed = [field for field in historical_fields if projected_rows[-1][field] != historical_rows[index][field]]
            mismatches.append({"row": index + 2, "fields": changed})
    if len(historical_rows) != len(replay_rows):
        errors.append(f"deal row count differs: frozen={len(historical_rows)} replay={len(replay_rows)}")
    if projected_rows != historical_rows:
        errors.append("replay deals projected without fee do not exactly match frozen deals")
    if not all_fees_zero:
        errors.append("one or more replay DEAL_FEE values are nonzero, nonfinite, or invalid")
    return (
        {
            "pass": not errors,
            "historical_rows": len(historical_rows),
            "replay_rows": len(replay_rows),
            "all_fee_values_exact_zero": all_fees_zero,
            "projected_rows_exact": projected_rows == historical_rows,
            "first_mismatches": mismatches,
            "errors": errors,
        },
        overlay,
    )


def compare_executed_order_rows(historical: Path, replay: Path) -> dict[str, Any]:
    historical_fields, historical_rows = read_tsv(historical)
    replay_fields, replay_rows = read_tsv(replay)
    if historical_fields != replay_fields:
        return {"pass": False, "error": "order headers differ"}
    actions = {"ORDER_SEND_OK", "SPLIT_TP1_ORDER_SEND_OK", "SPLIT_RUNNER_ORDER_SEND_OK"}
    historical_executed = [row for row in historical_rows if row.get("action") in actions]
    replay_executed = [row for row in replay_rows if row.get("action") in actions]
    return {
        "pass": historical_executed == replay_executed,
        "historical_rows": len(historical_executed),
        "replay_rows": len(replay_executed),
    }


def assert_report_metrics(report: Path, spec: SourceSpec) -> tuple[dict[str, str], list[str]]:
    metrics = exact.parse_mt5_report(report)
    errors: list[str] = []
    expected = {
        "History Quality": exact.EXPECTED_HISTORY_QUALITY,
        "Bars": exact.EXPECTED_BARS,
        "Ticks": exact.EXPECTED_TICKS,
        "Total Trades": spec.trades,
        "Total Deals": spec.deals,
    }
    for name, value in expected.items():
        actual: Any = metrics.get(name)
        if name != "History Quality":
            try:
                actual = exact.metric_int(metrics, name)
            except RuntimeError:
                actual = None
        if actual != value:
            errors.append(f"report {name} mismatch: expected={value!r} actual={actual!r}")
    return metrics, errors


def copy_required(path: Path, destination: Path) -> Path:
    if not path.is_file():
        raise FileNotFoundError(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)
    return destination


def run_source(
    *,
    spec: SourceSpec,
    package_dir: Path,
    sandbox: Path,
    terminal: Path,
    output_dir: Path,
    timeout_seconds: int,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    frozen_dir = package_dir / "immutable_evidence" / spec.source_id
    frozen_config = frozen_dir / "tester.ini"
    if exact.sha256_file(frozen_config) != spec.config_sha256:
        raise RuntimeError(f"Frozen config SHA256 mismatch for {spec.source_id}")
    config_text, log_names = derive_replay_config(exact.read_text(frozen_config), spec)
    run_dir = output_dir / "runs" / spec.source_id
    run_dir.mkdir(parents=True, exist_ok=True)
    config = sandbox / "Config" / f"A1_XAU_FEE_NATIVE_REPLAY_{safe_name(spec.source_id)}.ini"
    config.write_text(config_text, encoding="utf-8", newline="\n")
    copied_original_config = copy_required(frozen_config, run_dir / "frozen_tester.ini")
    copied_config = copy_required(config, run_dir / "derived_tester.ini")

    parsed = exact.parse_ini(config_text)
    report_stem = parsed["Tester"]["Report"].replace("\\", "/").split("/")[-1]
    report = sandbox / "Reports" / f"{report_stem}.htm"
    if report.exists():
        report.unlink()
    files_dir = sandbox / "Tester" / "Agent-127.0.0.1-3000" / "MQL5" / "Files"
    files_dir.mkdir(parents=True, exist_ok=True)
    for name in log_names.values():
        path = files_dir / name
        if path.exists():
            path.unlink()

    exact.run_checked(
        [str(terminal), "/portable", f"/config:{config}"],
        cwd=sandbox,
        timeout_seconds=timeout_seconds,
        command_runner=exact.default_command_runner,
        label=f"MT5 fee/native replay {spec.source_id}",
    )
    copied_report = copy_required(report, run_dir / report.name)
    copied_logs: dict[str, Path] = {}
    log_states: dict[str, str] = {}
    for input_name, name in log_names.items():
        source_log = files_dir / name
        destination_log = run_dir / name
        if input_name == "InpManagementLogFileName" and not source_log.exists():
            frozen_management = frozen_dir / "management.csv"
            if frozen_management.stat().st_size != 0:
                raise RuntimeError(f"Replay management log is absent but frozen evidence is nonempty: {spec.source_id}")
            destination_log.write_bytes(b"")
            copied_logs[input_name] = destination_log
            log_states[input_name] = "absent_proven_zero_against_frozen_empty_log"
        else:
            copied_logs[input_name] = copy_required(source_log, destination_log)
            log_states[input_name] = "present"

    errors: list[str] = []
    metrics, metric_errors = assert_report_metrics(copied_report, spec)
    errors.extend(metric_errors)
    deal_comparison, overlay = compare_fee_deals(
        frozen_dir / "deals.csv", copied_logs["InpDealLogFileName"], spec.source_id
    )
    errors.extend(deal_comparison["errors"])
    byte_comparisons: dict[str, Any] = {}
    for label, input_name in (
        ("signals", "InpSignalLogFileName"),
        ("orders", "InpOrderLogFileName"),
        ("management", "InpManagementLogFileName"),
    ):
        frozen = frozen_dir / f"{label}.csv"
        replay = copied_logs[input_name]
        same = frozen.read_bytes() == replay.read_bytes()
        executed_order_comparison = compare_executed_order_rows(frozen, replay) if label == "orders" else None
        comparison_pass = bool(executed_order_comparison["pass"]) if executed_order_comparison else same
        byte_comparisons[label] = {
            "pass": comparison_pass,
            "byte_exact": same,
            "frozen_sha256": exact.sha256_file(frozen),
            "replay_sha256": exact.sha256_file(replay),
            "frozen_size_bytes": frozen.stat().st_size,
            "replay_size_bytes": replay.stat().st_size,
        }
        if executed_order_comparison is not None:
            byte_comparisons[label]["executed_order_rows"] = executed_order_comparison
        if not comparison_pass:
            errors.append(f"{label} execution evidence does not match frozen evidence")

    return (
        {
            "source_id": spec.source_id,
            "pass": not errors,
            "expected_trades": spec.trades,
            "expected_deals": spec.deals,
            "frozen_config_sha256": exact.sha256_file(copied_original_config),
            "derived_config_sha256": exact.sha256_file(copied_config),
            "report_metrics": metrics,
            "deal_comparison": deal_comparison,
            "byte_comparisons": byte_comparisons,
            "log_states": log_states,
            "errors": errors,
            "artifacts": {
                "frozen_config": copied_original_config.relative_to(output_dir).as_posix(),
                "derived_config": copied_config.relative_to(output_dir).as_posix(),
                "report": copied_report.relative_to(output_dir).as_posix(),
                **{
                    key: value.relative_to(output_dir).as_posix()
                    for key, value in copied_logs.items()
                },
            },
        },
        overlay,
    )


def write_fee_overlay(path: Path, rows: list[dict[str, str]]) -> None:
    fields = [
        "source_id",
        "run_id",
        "account",
        "symbol",
        "magic",
        "deal_ticket",
        "position_id",
        "entry_code",
        "fee",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run_fee_native_replays(
    *,
    tester_sandbox: Path,
    metaeditor: Path,
    package_dir: Path,
    output_dir: Path,
    timeout_seconds: int = 1800,
) -> Path:
    sandbox = tester_sandbox.resolve()
    terminal = exact.validate_strategy_tester_sandbox(sandbox)
    editor = exact.validate_metaeditor(metaeditor)
    package_dir = package_dir.resolve()
    output_dir = output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError(f"Fee evidence directory must be new or empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    expert_dir = sandbox / "MQL5" / "Experts" / "A1Audit"
    expert_dir.mkdir(parents=True, exist_ok=True)
    runs: list[dict[str, Any]] = []
    overlay: list[dict[str, str]] = []
    source_payloads: list[dict[str, Any]] = []
    for spec in SOURCE_SPECS:
        source = expert_dir / f"{spec.expert_name}.mq5"
        source_manifest = output_dir / "compiled" / f"{safe_name(spec.source_id)}_source_manifest.json"
        source_manifest.parent.mkdir(parents=True, exist_ok=True)
        source_payload = fee_source.build_fee_evidence_source(
            REPO_ROOT,
            source,
            source_manifest,
            source_commit=spec.source_commit,
            source_sha256=spec.source_sha256,
            generated_expert_name=spec.expert_name,
        )
        source_payloads.append({"source_id": spec.source_id, **source_payload})
        compile_log = sandbox / "Logs" / f"compile_A1_XAU_FEE_{safe_name(spec.source_id)}.log"
        ex5 = exact.compile_program(
            source,
            editor,
            sandbox,
            compile_log,
            timeout_seconds=timeout_seconds,
            command_runner=exact.default_command_runner,
        )
        for path in (source, ex5, compile_log):
            copy_required(path, output_dir / "compiled" / safe_name(spec.source_id) / path.name)
        result, rows = run_source(
            spec=spec,
            package_dir=package_dir,
            sandbox=sandbox,
            terminal=terminal,
            output_dir=output_dir,
            timeout_seconds=timeout_seconds,
        )
        runs.append(result)
        overlay.extend(rows)

    overlay_path = output_dir / "A1_XAU_FEE_NATIVE_REPLAY_OVERLAY_20260710.csv"
    write_fee_overlay(overlay_path, overlay)
    overlay_keys = [
        (row["source_id"], row["run_id"], row["account"], row["symbol"], row["magic"], row["deal_ticket"])
        for row in overlay
    ]
    overlay_valid = len(overlay) == EXPECTED_TOTAL_DEALS and len(set(overlay_keys)) == EXPECTED_TOTAL_DEALS
    valid = all(run["pass"] for run in runs) and overlay_valid
    payload = {
        "schema_version": MANIFEST_SCHEMA,
        "status": "FEE_NATIVE_REPLAY_VALID" if valid else "FEE_NATIVE_REPLAY_INVALID",
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "boundary": {
            "strategy_tester_only": True,
            "broker_action_authorized": False,
            "live_or_demo_terminal_attachment": False,
            "source_strategy_changed": False,
            "source_instrumentation_reversible": all(
                item["reversible_to_pinned_source"] for item in source_payloads
            ),
            "common_account_session_section_removed": True,
        },
        "pinned_sources": source_payloads,
        "tester": {
            "build": exact.EXPECTED_BUILD,
            "terminal_path": str(terminal),
            "terminal_sha256": exact.sha256_file(terminal),
            "metaeditor_path": str(editor),
            "metaeditor_sha256": exact.sha256_file(editor),
        },
        "runs": runs,
        "overlay": {
            "path": overlay_path.relative_to(output_dir).as_posix(),
            "rows": len(overlay),
            "unique_namespaced_deal_keys": len(set(overlay_keys)),
            "pass": overlay_valid,
            "sha256": exact.sha256_file(overlay_path),
        },
    }
    payload["artifacts"] = exact.manifest_artifacts(output_dir)
    manifest = output_dir / "manifest.json"
    manifest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (output_dir / "manifest.sha256").write_text(
        f"{exact.sha256_file(manifest)}  manifest.json\n", encoding="utf-8", newline="\n"
    )
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run four exact Strategy Tester native/fee reproductions")
    parser.add_argument("--tester-sandbox", type=Path, required=True)
    parser.add_argument("--metaeditor", type=Path, required=True)
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = run_fee_native_replays(
        tester_sandbox=args.tester_sandbox,
        metaeditor=args.metaeditor,
        package_dir=args.package_dir,
        output_dir=args.output_dir,
        timeout_seconds=args.timeout_seconds,
    )
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    print(manifest)
    return 0 if payload["status"] == "FEE_NATIVE_REPLAY_VALID" else 2


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]

AUDIT_ID = "A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_V1"
MANIFEST_SCHEMA = "a1_xau_router_entry_hold_path_exact_runner_manifest_v1"
AUTHORITATIVE_COMMIT = "006824cde421ea61a0bcdb074804f9ccf95c17a9"
AUTHORITATIVE_SOURCE = "xau-usd/xauusd-phase1/mt5/Experts/A1XauM5MomentumContinuationExecutor.mq5"
AUTHORITATIVE_SOURCE_SHA256 = "3372d8e751141f1d397d9967b8c14272046e1a733a64f67e63fcc3f56e53d355"
EXPECTED_BUILD = 5833
EXPECTED_HISTORY_QUALITY = "98%"
EXPECTED_BARS = 282_644
EXPECTED_TICKS = 204_204_660
FROM_DATE = "2022.07.01"
TO_DATE = "2026.06.30"
EXPECTED_SCHEDULE_ROWS = 678

SANDBOX_MARKER = "A1_XAU_STRATEGY_TESTER_ONLY.marker"
SANDBOX_MARKER_TEXT = "A1_XAU_ROUTER_ENTRY_HOLD_PATH_STRATEGY_TESTER_ONLY_V1\n"
EXPORTER_SOURCE_NAME = "A1XauRouterEntryHoldPathExporter.mq5"
ORACLE_SOURCE_NAME = "A1XauRouterSnapshotOracle006824.mq5"

ROUTER_INPUTS = {
    "InpAtrPeriod": "14",
    "InpRegimeFastEmaPeriod": "20",
    "InpRegimeSlowEmaPeriod": "50",
    "InpRegimeSlopeLagBars": "5",
    "InpRegimePersistenceD1Bars": "2",
    "InpRegimeRequireH4Confirm": "true",
    "InpRegimeShockH1RangeAtrMultiple": "3.00",
    "InpRegimeShockD1AtrPercentileMin": "95.00",
    "InpRegimeShockD1AtrLookback": "60",
    "InpRegimeCompressionD1AtrPercentileMax": "30.00",
    "InpRegimeCompressionBoxDays": "5",
    "InpRegimeCompressionRangeMedianMax": "1.00",
}

SCHEDULE_FIELDS = (
    "trade_id",
    "source_id",
    "component",
    "expected_regime",
    "direction",
    "signal_time_broker",
    "entry_time_broker",
    "exit_time_broker",
    "native_run_id",
    "native_account",
    "native_symbol",
    "native_magic",
    "native_position_id",
    "native_entry_order",
    "native_entry_deal",
    "native_exit_order",
    "native_exit_deal",
    "executed_volume",
    "actual_entry_price",
    "original_sl",
    "original_tp",
    "order_bid",
    "order_ask",
    "spread_points",
    "estimated_cost_r",
    "signal_reason",
    "native_exit_reason_code",
)

PROHIBITED_SCHEDULE_FIELD_FRAGMENTS = (
    "pnl",
    "profit",
    "final_r",
    "mfe",
    "mae",
    "unrealized",
    "post_change",
    "primary_class",
)

EXPORTER_INPUT_NAMES = (
    "InpRunId",
    "InpTargetSymbol",
    "InpScheduleFileName",
    "InpEventLogFileName",
    "InpFeatureLogFileName",
    "InpProvenanceLogFileName",
    "InpAssertionLogFileName",
)

FORBIDDEN_BROKER_ACTION_TOKENS = (
    "OrderSend",
    "OrderSendAsync",
    "CTrade",
    "trade.Buy",
    "trade.Sell",
    "PositionOpen",
    "PositionClose",
    "PositionModify",
    "TRADE_ACTION_DEAL",
    "TRADE_ACTION_SLTP",
    "MqlTradeRequest",
)

CommandRunner = Callable[[Sequence[str], Path, int], Any]


@dataclass(frozen=True)
class ProgramSpec:
    name: str
    expert_name: str
    inputs: dict[str, str]
    causal_log_inputs: tuple[str, ...]
    order_log_name: str
    deal_log_name: str


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_text(path: Path) -> str:
    data = path.read_bytes()
    encodings = ("utf-16", "utf-8-sig", "utf-8") if data.startswith((b"\xff\xfe", b"\xfe\xff")) else ("utf-8-sig", "utf-8")
    for encoding in encodings:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def extract_authoritative_ea_blob(repo_root: Path = REPO_ROOT) -> bytes:
    spec = f"{AUTHORITATIVE_COMMIT}:{AUTHORITATIVE_SOURCE}"
    completed = subprocess.run(
        ["git", "show", spec],
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        message = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Cannot extract authoritative Router V1 source {spec}: {message}")
    assert_authoritative_oracle_source(completed.stdout)
    return completed.stdout


def assert_authoritative_oracle_source(source: bytes) -> None:
    actual = sha256_bytes(source)
    if actual != AUTHORITATIVE_SOURCE_SHA256:
        raise RuntimeError(
            "Authoritative Router V1 source SHA256 mismatch: "
            f"expected={AUTHORITATIVE_SOURCE_SHA256}; actual={actual}"
        )
    text = source.decode("utf-8")
    required = (
        "input bool   InpAllowDemoTrading              = false;",
        "input bool   InpAllowNonDemoAccounts          = false;",
        "input bool   InpRegimeSnapshotLogEnabled     = false;",
        "if(InpRegimeSnapshotLogEnabled)",
        'LogSignal("REGIME_SNAPSHOT"',
        "const string regime_name = RegimeStateName(CurrentXauRegime());",
    )
    missing = [token for token in required if token not in text]
    if missing:
        raise RuntimeError(f"Pinned Router oracle contract token(s) missing: {missing}")
    snapshot_start = text.index("if(InpRegimeSnapshotLogEnabled)")
    snapshot_return = text.find("return;", snapshot_start)
    normal_signal_path = text.find("const int compression_bars", snapshot_start)
    if snapshot_return < 0 or normal_signal_path < 0 or snapshot_return > normal_signal_path:
        raise RuntimeError("Pinned Router snapshot mode does not return before the normal signal/order path.")


def assert_exporter_source_contract(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")
    forbidden = [token for token in FORBIDDEN_BROKER_ACTION_TOKENS if token in text]
    if forbidden:
        raise RuntimeError(f"Exporter contains forbidden broker-action token(s): {forbidden}")
    missing_inputs = [name for name in EXPORTER_INPUT_NAMES if not re.search(rf"\b{name}\b", text)]
    if missing_inputs:
        raise RuntimeError(f"Exporter input contract token(s) missing: {missing_inputs}")
    for name, value in ROUTER_INPUTS.items():
        pattern = rf"\b{name}\s*=\s*{re.escape(value)}\s*;"
        if re.search(pattern, text, flags=re.IGNORECASE) is None:
            raise RuntimeError(f"Exporter frozen Router input missing or changed: {name}={value}")


def validate_schedule(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        prohibited = [
            field
            for field in (reader.fieldnames or ())
            if any(fragment in field.lower() for fragment in PROHIBITED_SCHEDULE_FIELD_FRAGMENTS)
        ]
        if prohibited:
            raise RuntimeError(f"Exporter schedule contains prohibited outcome/class field(s): {prohibited}")
        if tuple(reader.fieldnames or ()) != SCHEDULE_FIELDS:
            raise RuntimeError(
                "Exporter schedule header mismatch: "
                f"expected={list(SCHEDULE_FIELDS)}; actual={reader.fieldnames}"
            )
        rows = list(reader)
    if len(rows) != EXPECTED_SCHEDULE_ROWS:
        raise RuntimeError(f"Exporter schedule must contain exactly {EXPECTED_SCHEDULE_ROWS} rows; found {len(rows)}")
    trade_ids = [row["trade_id"].strip() for row in rows]
    if any(not value for value in trade_ids):
        raise RuntimeError("Exporter schedule contains an empty trade_id.")
    if len(set(trade_ids)) != len(trade_ids):
        raise RuntimeError("Exporter schedule trade_id values must be unique.")
    return rows


def initialize_strategy_tester_sandbox(sandbox: Path) -> Path:
    sandbox = sandbox.resolve()
    normalized = str(sandbox).replace("/", "\\").lower()
    if "\\program files\\" in normalized or "\\appdata\\roaming\\metaquotes\\terminal\\" in normalized:
        raise RuntimeError(f"Refusing to mark an installed/runtime terminal directory as a tester sandbox: {sandbox}")
    if not any(token in sandbox.name.lower() for token in ("backtest", "tester")):
        raise RuntimeError("Tester sandbox directory name must explicitly contain 'backtest' or 'tester'.")
    terminal = sandbox / "terminal64.exe"
    if not terminal.is_file():
        raise RuntimeError(f"Cannot mark a sandbox without terminal64.exe: {terminal}")
    marker = sandbox / SANDBOX_MARKER
    if marker.exists() and marker.read_text(encoding="utf-8") != SANDBOX_MARKER_TEXT:
        raise RuntimeError(f"Refusing to overwrite an invalid existing sandbox marker: {marker}")
    marker.write_text(SANDBOX_MARKER_TEXT, encoding="utf-8", newline="\n")
    return marker


def validate_strategy_tester_sandbox(sandbox: Path) -> Path:
    sandbox = sandbox.resolve()
    marker = sandbox / SANDBOX_MARKER
    if not marker.is_file() or marker.read_text(encoding="utf-8") != SANDBOX_MARKER_TEXT:
        raise RuntimeError(
            f"Isolated Strategy Tester marker missing or invalid: {marker}. "
            "Refusing to use an unmarked terminal directory."
        )
    terminal = (sandbox / "terminal64.exe").resolve()
    if not terminal.is_file() or not terminal.is_relative_to(sandbox):
        raise RuntimeError(f"Required isolated Strategy Tester executable is missing: {terminal}")
    return terminal


def validate_metaeditor(metaeditor: Path) -> Path:
    metaeditor = metaeditor.resolve()
    if not metaeditor.is_file() or metaeditor.name.lower() != "metaeditor64.exe":
        raise RuntimeError(f"Required MetaEditor64 executable is missing or incorrectly named: {metaeditor}")
    return metaeditor


def default_command_runner(command: Sequence[str], cwd: Path, timeout_seconds: int) -> Any:
    return subprocess.run(
        list(command),
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_seconds,
        check=False,
    )


def run_checked(
    command: Sequence[str],
    *,
    cwd: Path,
    timeout_seconds: int,
    command_runner: CommandRunner,
    label: str,
) -> None:
    completed = command_runner(command, cwd, timeout_seconds)
    returncode = int(getattr(completed, "returncode", 1))
    if returncode != 0:
        stderr = getattr(completed, "stderr", b"")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"{label} failed with exit code {returncode}: {str(stderr).strip()}")


def require_build(text: str, label: str) -> None:
    builds = {int(value) for value in re.findall(r"\bbuild\s+(\d{4,6})\b", text, flags=re.IGNORECASE)}
    if builds != {EXPECTED_BUILD}:
        raise RuntimeError(f"{label} must prove build {EXPECTED_BUILD}; found {sorted(builds)}")


def compile_program(
    source: Path,
    metaeditor: Path,
    sandbox: Path,
    compile_log: Path,
    *,
    timeout_seconds: int,
    command_runner: CommandRunner,
) -> Path:
    ex5 = source.with_suffix(".ex5")
    if ex5.exists():
        ex5.unlink()
    if compile_log.exists():
        compile_log.unlink()
    compile_log.parent.mkdir(parents=True, exist_ok=True)
    command = [str(metaeditor), f"/compile:{source}", f"/log:{compile_log}"]
    completed = command_runner(command, sandbox, timeout_seconds)
    # MetaEditor64 build 5833 returns 1 after a successful command-line compile on
    # this host.  The EX5 and the compiler's explicit zero-error/zero-warning log
    # are authoritative; no other nonzero code is accepted.
    returncode = int(getattr(completed, "returncode", 1))
    if returncode not in {0, 1}:
        stderr = getattr(completed, "stderr", b"")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        raise RuntimeError(
            f"MetaEditor compile for {source.name} failed with exit code {returncode}: {str(stderr).strip()}"
        )
    if not ex5.is_file() or not compile_log.is_file():
        raise RuntimeError(f"Compile did not produce both EX5 and log for {source.name}")
    compile_text = read_text(compile_log)
    if re.search(r"\b0\s+errors?\b", compile_text, flags=re.IGNORECASE) is None:
        raise RuntimeError(f"Compile log does not prove zero errors: {compile_log}")
    if re.search(r"\b0\s+warnings?\b", compile_text, flags=re.IGNORECASE) is None:
        raise RuntimeError(f"Compile log does not prove zero warnings: {compile_log}")
    return ex5


def program_specs() -> tuple[ProgramSpec, ProgramSpec]:
    stable_run_id = "A1_XAU_ROUTER_ENTRY_HOLD_PATH_EXACT_20260710"
    router_logs = {
        "InpStartupLogFileName": "a1_xau_router_oracle_startup.csv",
        "InpSignalLogFileName": "a1_xau_router_oracle_causal.csv",
        "InpOrderLogFileName": "a1_xau_router_oracle_order.csv",
        "InpManagementLogFileName": "a1_xau_router_oracle_management.csv",
        "InpDealLogFileName": "a1_xau_router_oracle_deal.csv",
    }
    router = ProgramSpec(
        name="router_snapshot_oracle",
        expert_name=Path(ORACLE_SOURCE_NAME).stem,
        inputs={
            "InpRunId": stable_run_id,
            "InpAllowDemoTrading": "false",
            "InpAllowNonDemoAccounts": "false",
            "InpAllowedAccountLogin": "0",
            "InpExpectedServerMarker": "Demo",
            "InpTargetSymbol": "XAUUSD",
            "InpMagicNumber": "939910",
            "InpRegimeRouterMode": "0",
            "InpRegimeSnapshotLogEnabled": "true",
            **ROUTER_INPUTS,
            **router_logs,
        },
        causal_log_inputs=("InpSignalLogFileName",),
        order_log_name=router_logs["InpOrderLogFileName"],
        deal_log_name=router_logs["InpDealLogFileName"],
    )
    exporter_logs = {
        "InpEventLogFileName": "a1_xau_router_path_event.tsv",
        "InpFeatureLogFileName": "a1_xau_router_path_feature.tsv",
        "InpProvenanceLogFileName": "a1_xau_router_path_provenance.tsv",
        "InpAssertionLogFileName": "a1_xau_router_path_assertion.tsv",
    }
    exporter = ProgramSpec(
        name="entry_hold_path_exporter",
        expert_name=Path(EXPORTER_SOURCE_NAME).stem,
        inputs={
            "InpRunId": stable_run_id,
            "InpTargetSymbol": "XAUUSD",
            "InpScheduleFileName": "a1_xau_router_entry_hold_path_schedule_v1.csv",
            **ROUTER_INPUTS,
            **exporter_logs,
        },
        causal_log_inputs=tuple(exporter_logs),
        order_log_name="a1_xau_router_path_order.zero",
        deal_log_name="a1_xau_router_path_deal.zero",
    )
    return router, exporter


def render_tester_config(spec: ProgramSpec, repetition: int) -> str:
    report_stem = f"A1_XAU_ROUTER_ENTRY_HOLD_PATH_{spec.name.upper()}_RUN{repetition}"
    lines = [
        "[Tester]",
        f"Expert=A1Audit\\{spec.expert_name}.ex5",
        "Symbol=XAUUSD",
        "Period=M5",
        "Optimization=0",
        "Model=0",
        "Dates=2",
        f"FromDate={FROM_DATE}",
        f"ToDate={TO_DATE}",
        "ForwardMode=0",
        "Deposit=1000",
        "Currency=USD",
        "ProfitInPips=0",
        "Leverage=200",
        "ExecutionMode=0",
        "OptimizationCriterion=0",
        "Visual=0",
        f"Report=Reports\\{report_stem}",
        "ReplaceReport=1",
        "ShutdownTerminal=1",
        "UseLocal=1",
        "UseRemote=0",
        "UseCloud=0",
        "",
        "[TesterInputs]",
        *(f"{key}={value}" for key, value in spec.inputs.items()),
        "",
    ]
    text = "\n".join(lines)
    assert_tester_config_contract(text, spec)
    return text


def parse_ini(text: str) -> dict[str, dict[str, str]]:
    sections: dict[str, dict[str, str]] = {}
    section = ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            sections.setdefault(section, {})
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            sections.setdefault(section, {})[key.strip()] = value.strip()
    return sections


def assert_tester_config_contract(text: str, spec: ProgramSpec) -> None:
    parsed = parse_ini(text)
    if set(parsed) != {"Tester", "TesterInputs"}:
        raise RuntimeError(f"Tester config contains forbidden/non-audit section(s): {sorted(parsed)}")
    tester = parsed["Tester"]
    inputs = parsed["TesterInputs"]
    required_tester = {
        "Optimization": "0",
        "Model": "0",
        "Visual": "0",
        "ShutdownTerminal": "1",
        "UseLocal": "1",
        "UseRemote": "0",
        "UseCloud": "0",
        "FromDate": FROM_DATE,
        "ToDate": TO_DATE,
    }
    for key, expected in required_tester.items():
        if tester.get(key) != expected:
            raise RuntimeError(f"Unsafe or changed tester setting {key}: {tester.get(key)!r}")
    for forbidden in ("Login", "Server", "Password", "ProxyEnable"):
        if forbidden in tester or forbidden in parsed.get("Common", {}):
            raise RuntimeError(f"Tester config must not contain account/session setting {forbidden}")
    dangerous_true = (
        "InpAllowDemoTrading",
        "InpAllowNonDemoAccounts",
        "InpBrokerActionAllowed",
        "InpManageActionAllowed",
        "InpCloseActionAllowed",
    )
    for key in dangerous_true:
        if inputs.get(key, "false").strip().lower() == "true":
            raise RuntimeError(f"Tester config enables broker action through {key}")
    if inputs.get("InpDryRunOnly", "true").strip().lower() == "false":
        raise RuntimeError("Tester config disables dry-run protection.")
    for key, expected in spec.inputs.items():
        if inputs.get(key) != expected:
            raise RuntimeError(f"Tester input changed or missing: {key}={expected}")
    if spec.name == "router_snapshot_oracle":
        if inputs.get("InpRegimeSnapshotLogEnabled") != "true":
            raise RuntimeError("Pinned Router oracle snapshot mode is not enabled.")
        if inputs.get("InpAllowDemoTrading") != "false":
            raise RuntimeError("Pinned Router oracle trading gate is not false.")


def parse_mt5_report(path: Path) -> dict[str, str]:
    text = read_text(path)
    rows: list[list[str]] = []
    for match in re.finditer(r"<tr[^>]*>(.*?)</tr>", text, flags=re.IGNORECASE | re.DOTALL):
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", match.group(1), flags=re.IGNORECASE | re.DOTALL)
        cleaned = [html.unescape(re.sub(r"<[^>]+>", "", cell)).strip().replace("\xa0", " ") for cell in cells]
        if cleaned:
            rows.append(cleaned)
    flat = [cell for row in rows for cell in row]
    metrics: dict[str, str] = {}
    for label in ("History Quality:", "Bars:", "Ticks:", "Total Trades:", "Total Deals:"):
        for index, value in enumerate(flat[:-1]):
            if value == label:
                metrics[label.rstrip(":")] = flat[index + 1]
                break
    require_build(text, f"MT5 report {path.name}")
    return metrics


def metric_int(metrics: dict[str, str], name: str) -> int:
    value = re.sub(r"[^0-9]", "", metrics.get(name, ""))
    if not value:
        raise RuntimeError(f"MT5 report metric missing or invalid: {name}")
    return int(value)


def assert_zero_activity_report(path: Path) -> dict[str, str]:
    metrics = parse_mt5_report(path)
    if metric_int(metrics, "Total Trades") != 0 or metric_int(metrics, "Total Deals") != 0:
        raise RuntimeError(f"No-trading tester run reported a trade or deal: {path}")
    if metrics.get("History Quality") != EXPECTED_HISTORY_QUALITY:
        raise RuntimeError(f"History quality must be {EXPECTED_HISTORY_QUALITY}: {path}")
    if metric_int(metrics, "Bars") != EXPECTED_BARS or metric_int(metrics, "Ticks") != EXPECTED_TICKS:
        raise RuntimeError(
            f"Tester history provenance mismatch in {path}: "
            f"bars={metrics.get('Bars')}; ticks={metrics.get('Ticks')}"
        )
    return metrics


def assert_empty_log(path: Path, label: str) -> str:
    # MT5 may remove a pre-created file when an EA never opens that log.  Both an
    # absent file and an existing zero-byte file prove zero logged activity; a
    # copied zero-byte placeholder is created only after this assertion.
    if not path.exists():
        return "absent"
    if not path.is_file() or path.stat().st_size != 0:
        raise RuntimeError(f"{label} must be absent or exactly zero bytes: {path}")
    return "zero_bytes"


def assert_causal_output(spec: ProgramSpec, input_name: str, path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"Missing or empty causal output {input_name}: {path}")
    if spec.name == "router_snapshot_oracle":
        with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
            found = any("REGIME_SNAPSHOT" in line for line in handle)
        if not found:
            raise RuntimeError("Pinned Router oracle output contains no REGIME_SNAPSHOT row.")
        return
    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        header = handle.readline().rstrip("\r\n")
        first_evidence_row = handle.readline()
    if input_name in {"InpEventLogFileName", "InpFeatureLogFileName"}:
        for key in ("tester_time_msc", "callback_sequence", "event_sequence"):
            if key not in header:
                raise RuntimeError(f"Exporter {input_name} header lacks causal key {key}")
    if not first_evidence_row:
        raise RuntimeError(f"Exporter output {input_name} contains no evidence row.")


def assert_exporter_runtime_assertions(path: Path) -> dict[str, Any]:
    required = {
        "tester_only",
        "frozen_router_inputs",
        "trade_sessions",
        "indicator_handles",
        "schedule_header_exact",
        "schedule_source_counts",
        "all_678_schedule_rows_complete",
        "zero_execution_surface_runtime",
    }
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None or not {"assertion", "status", "detail"}.issubset(reader.fieldnames):
            raise RuntimeError("Exporter assertion log header is incomplete")
        rows = list(reader)
    failed = [row for row in rows if row.get("status") != "PASS"]
    if failed:
        details = [f"{row.get('assertion')}:{row.get('detail')}" for row in failed[:20]]
        raise RuntimeError(f"Exporter runtime assertion failure(s): {details}")
    present = {str(row.get("assertion", "")) for row in rows}
    missing = sorted(required - present)
    if missing:
        raise RuntimeError(f"Exporter runtime assertion(s) missing: {missing}")
    return {"rows": len(rows), "required_assertions": sorted(required), "all_pass": True}


def copy_artifact(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination


def run_program_once(
    spec: ProgramSpec,
    repetition: int,
    *,
    terminal: Path,
    sandbox: Path,
    evidence_dir: Path,
    timeout_seconds: int,
    command_runner: CommandRunner,
) -> dict[str, Any]:
    config_text = render_tester_config(spec, repetition)
    config = sandbox / "Config" / f"A1_XAU_ROUTER_ENTRY_HOLD_PATH_{spec.name}_run{repetition}.ini"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(config_text, encoding="utf-8", newline="\n")
    report_stem = parse_ini(config_text)["Tester"]["Report"].replace("\\", "/").split("/")[-1]
    report = sandbox / "Reports" / f"{report_stem}.htm"
    report.parent.mkdir(parents=True, exist_ok=True)
    if report.exists():
        report.unlink()

    files_dir = sandbox / "Tester" / "Agent-127.0.0.1-3000" / "MQL5" / "Files"
    files_dir.mkdir(parents=True, exist_ok=True)
    causal_paths = {name: files_dir / spec.inputs[name] for name in spec.causal_log_inputs}
    for path in causal_paths.values():
        if path.exists():
            path.unlink()
    order_log = files_dir / spec.order_log_name
    deal_log = files_dir / spec.deal_log_name
    order_log.write_bytes(b"")
    deal_log.write_bytes(b"")

    command = [str(terminal), "/portable", f"/config:{config}"]
    run_checked(
        command,
        cwd=sandbox,
        timeout_seconds=timeout_seconds,
        command_runner=command_runner,
        label=f"MT5 Strategy Tester {spec.name} repetition {repetition}",
    )
    if not report.is_file():
        raise RuntimeError(f"MT5 Strategy Tester report missing: {report}")
    metrics = assert_zero_activity_report(report)
    order_log_state = assert_empty_log(order_log, f"{spec.name} order log")
    deal_log_state = assert_empty_log(deal_log, f"{spec.name} deal log")
    if not order_log.exists():
        order_log.write_bytes(b"")
    if not deal_log.exists():
        deal_log.write_bytes(b"")
    for name, path in causal_paths.items():
        assert_causal_output(spec, name, path)
    runtime_assertions = None
    if spec.name == "entry_hold_path_exporter":
        runtime_assertions = assert_exporter_runtime_assertions(causal_paths["InpAssertionLogFileName"])

    run_dir = evidence_dir / "runs" / spec.name / f"run{repetition}"
    copied = {
        "config": copy_artifact(config, run_dir / config.name),
        "report": copy_artifact(report, run_dir / report.name),
        "order_log": copy_artifact(order_log, run_dir / order_log.name),
        "deal_log": copy_artifact(deal_log, run_dir / deal_log.name),
    }
    causal_copies: dict[str, Path] = {}
    for name, path in causal_paths.items():
        causal_copies[name] = copy_artifact(path, run_dir / path.name)
    return {
        "program": spec.name,
        "repetition": repetition,
        "metrics": metrics,
        "zero_activity_log_state": {"order": order_log_state, "deal": deal_log_state},
        "runtime_assertions": runtime_assertions,
        "artifacts": {key: str(path.relative_to(evidence_dir).as_posix()) for key, path in copied.items()},
        "causal_artifacts": {
            key: str(path.relative_to(evidence_dir).as_posix()) for key, path in causal_copies.items()
        },
    }


def assert_repeat_determinism(spec: ProgramSpec, runs: list[dict[str, Any]], evidence_dir: Path) -> dict[str, str]:
    if len(runs) != 2:
        raise RuntimeError(f"Exactly two repetitions are required for {spec.name}")
    hashes: dict[str, str] = {}
    for input_name in spec.causal_log_inputs:
        first = evidence_dir / runs[0]["causal_artifacts"][input_name]
        second = evidence_dir / runs[1]["causal_artifacts"][input_name]
        if first.read_bytes() != second.read_bytes():
            raise RuntimeError(f"Causal output is not byte-deterministic for {spec.name}/{input_name}")
        hashes[input_name] = sha256_file(first)
    return hashes


def manifest_artifacts(evidence_dir: Path) -> dict[str, dict[str, Any]]:
    artifacts: dict[str, dict[str, Any]] = {}
    for path in sorted(item for item in evidence_dir.rglob("*") if item.is_file()):
        if path.name in {"manifest.json", "manifest.sha256"}:
            continue
        relative = path.relative_to(evidence_dir).as_posix()
        artifacts[relative] = {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
    return artifacts


def run_exact_snapshot_generation(
    *,
    tester_sandbox: Path,
    metaeditor: Path,
    exporter_source: Path,
    schedule: Path,
    evidence_dir: Path,
    repo_root: Path = REPO_ROOT,
    timeout_seconds: int = 3600,
    command_runner: CommandRunner = default_command_runner,
) -> Path:
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    terminal = validate_strategy_tester_sandbox(tester_sandbox)
    metaeditor = validate_metaeditor(metaeditor)
    assert_exporter_source_contract(exporter_source)
    validate_schedule(schedule)
    evidence_dir = evidence_dir.resolve()
    if evidence_dir.exists() and any(evidence_dir.iterdir()):
        raise RuntimeError(f"Evidence directory must be new or empty: {evidence_dir}")
    evidence_dir.mkdir(parents=True, exist_ok=True)

    experts_dir = tester_sandbox.resolve() / "MQL5" / "Experts" / "A1Audit"
    experts_dir.mkdir(parents=True, exist_ok=True)
    oracle_source = experts_dir / ORACLE_SOURCE_NAME
    oracle_source.write_bytes(extract_authoritative_ea_blob(repo_root))
    exporter_target = experts_dir / EXPORTER_SOURCE_NAME
    shutil.copy2(exporter_source, exporter_target)
    assert_exporter_source_contract(exporter_target)

    input_dir = evidence_dir / "inputs"
    copied_schedule = copy_artifact(schedule, input_dir / "a1_xau_router_entry_hold_path_schedule_v1.csv")
    files_dir = tester_sandbox.resolve() / "Tester" / "Agent-127.0.0.1-3000" / "MQL5" / "Files"
    files_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(copied_schedule, files_dir / copied_schedule.name)
    # Local tester agents rebuild their Files sandbox at initialization.  The
    # terminal-level MQL5\Files copy is the deployment source; the agent copy is
    # also populated for deterministic fake/local-agent coverage.
    terminal_files_dir = tester_sandbox.resolve() / "MQL5" / "Files"
    terminal_files_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(copied_schedule, terminal_files_dir / copied_schedule.name)

    compile_dir = tester_sandbox.resolve() / "Logs"
    oracle_compile_log = compile_dir / "compile_A1_XAU_ROUTER_SNAPSHOT_ORACLE_006824.log"
    exporter_compile_log = compile_dir / "compile_A1_XAU_ROUTER_ENTRY_HOLD_PATH_EXPORTER.log"
    oracle_ex5 = compile_program(
        oracle_source,
        metaeditor,
        tester_sandbox.resolve(),
        oracle_compile_log,
        timeout_seconds=timeout_seconds,
        command_runner=command_runner,
    )
    exporter_ex5 = compile_program(
        exporter_target,
        metaeditor,
        tester_sandbox.resolve(),
        exporter_compile_log,
        timeout_seconds=timeout_seconds,
        command_runner=command_runner,
    )

    compiled_dir = evidence_dir / "compiled"
    for path in (oracle_source, oracle_ex5, oracle_compile_log, exporter_target, exporter_ex5, exporter_compile_log):
        copy_artifact(path, compiled_dir / path.name)

    all_runs: list[dict[str, Any]] = []
    determinism: dict[str, dict[str, str]] = {}
    for spec in program_specs():
        spec_runs = [
            run_program_once(
                spec,
                repetition,
                terminal=terminal,
                sandbox=tester_sandbox.resolve(),
                evidence_dir=evidence_dir,
                timeout_seconds=timeout_seconds,
                command_runner=command_runner,
            )
            for repetition in (1, 2)
        ]
        determinism[spec.name] = assert_repeat_determinism(spec, spec_runs, evidence_dir)
        all_runs.extend(spec_runs)

    payload = {
        "schema_version": MANIFEST_SCHEMA,
        "audit_id": AUDIT_ID,
        "status": "EXACT_SNAPSHOT_EVIDENCE_GENERATED_NOT_CLASSIFIED",
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "boundary": {
            "strategy_tester_only": True,
            "trading_logic_changed": False,
            "broker_action_authorized": False,
            "classification_performed": False,
            "repetitions_per_program": 2,
            "zero_broker_action_contract": {
                "pinned_oracle_exact_hash_and_snapshot_early_return": True,
                "pinned_oracle_trading_input_false": True,
                "exporter_source_forbidden_action_scan_passed": True,
                "all_reports_zero_trades_and_deals": True,
                "all_order_and_deal_logs_zero_bytes": True,
            },
        },
        "authoritative_router": {
            "commit": AUTHORITATIVE_COMMIT,
            "source": AUTHORITATIVE_SOURCE,
            "sha256": AUTHORITATIVE_SOURCE_SHA256,
        },
        "tester": {
            "build": EXPECTED_BUILD,
            "terminal_path": str(terminal),
            "terminal_sha256": sha256_file(terminal),
            "metaeditor_path": str(metaeditor),
            "metaeditor_sha256": sha256_file(metaeditor),
            "model": "every_tick",
            "from_date": FROM_DATE,
            "to_date": TO_DATE,
            "history_quality": EXPECTED_HISTORY_QUALITY,
            "bars": EXPECTED_BARS,
            "ticks": EXPECTED_TICKS,
            "remote_agents": False,
            "cloud_agents": False,
        },
        "schedule": {
            "rows": EXPECTED_SCHEDULE_ROWS,
            "outcome_fields_supplied_to_exporter": False,
            "sha256": sha256_file(copied_schedule),
            "path": copied_schedule.relative_to(evidence_dir).as_posix(),
        },
        "exporter": {
            "source_name": EXPORTER_SOURCE_NAME,
            "source_sha256": sha256_file(exporter_target),
            "broker_action_tokens_found": 0,
        },
        "runs": all_runs,
        "causal_repeat_sha256": determinism,
        "artifacts": manifest_artifacts(evidence_dir),
    }
    manifest = evidence_dir / "manifest.json"
    manifest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    manifest_hash = sha256_file(manifest)
    (evidence_dir / "manifest.sha256").write_text(
        f"{manifest_hash}  manifest.json\n", encoding="utf-8", newline="\n"
    )
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate deterministic no-trading Router entry/hold-path evidence in an isolated MT5 Strategy Tester."
    )
    parser.add_argument("--tester-sandbox", type=Path, required=True)
    parser.add_argument(
        "--initialize-sandbox-marker",
        action="store_true",
        help="Write only the fail-closed Strategy Tester marker, then exit without compiling or running.",
    )
    parser.add_argument("--metaeditor", type=Path)
    parser.add_argument(
        "--exporter-source",
        type=Path,
        default=PHASE1_ROOT / "mt5" / "Experts" / EXPORTER_SOURCE_NAME,
    )
    parser.add_argument("--schedule", type=Path)
    parser.add_argument(
        "--evidence-dir",
        type=Path,
        default=PHASE1_ROOT / "outputs" / "reports" / "A1_XAU_ROUTER_ENTRY_HOLD_PATH_EXACT_20260710",
    )
    parser.add_argument("--timeout-seconds", type=int, default=3600)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.initialize_sandbox_marker:
        print(initialize_strategy_tester_sandbox(args.tester_sandbox))
        return 0
    if args.metaeditor is None:
        raise SystemExit("--metaeditor is required for exact snapshot generation.")
    if args.schedule is None:
        raise SystemExit("--schedule is required for exact snapshot generation.")
    manifest = run_exact_snapshot_generation(
        tester_sandbox=args.tester_sandbox,
        metaeditor=args.metaeditor,
        exporter_source=args.exporter_source,
        schedule=args.schedule,
        evidence_dir=args.evidence_dir,
        timeout_seconds=args.timeout_seconds,
    )
    print(manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

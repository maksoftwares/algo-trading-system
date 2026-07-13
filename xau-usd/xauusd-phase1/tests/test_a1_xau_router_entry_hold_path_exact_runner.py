from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
RUNNER_PATH = ROOT / "scripts" / "run_a1_xau_router_entry_hold_path_exact.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("run_a1_xau_router_entry_hold_path_exact", RUNNER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


R = _load_runner()


def _write_schedule(path: Path, rows: int = R.EXPECTED_SCHEDULE_ROWS) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=R.SCHEDULE_FIELDS)
        writer.writeheader()
        for index in range(rows):
            writer.writerow(
                {
                    "trade_id": f"r1::run::account::XAUUSD::932200::{index + 1}",
                    "source_id": "r1_h1_pullback_long_v1",
                    "component": "R1",
                    "expected_regime": "UPTREND",
                    "direction": "LONG",
                    "signal_time_broker": "2022.07.01 08:55:00",
                    "entry_time_broker": "2022.07.01 09:00:00",
                    "exit_time_broker": "2022.07.01 10:00:00",
                    "native_run_id": "run",
                    "native_account": "account",
                    "native_symbol": "XAUUSD",
                    "native_magic": "932200",
                    "native_position_id": str(index + 1),
                    "native_entry_order": str(10000 + index),
                    "native_entry_deal": str(20000 + index),
                    "native_exit_order": str(30000 + index),
                    "native_exit_deal": str(40000 + index),
                    "executed_volume": "0.01",
                    "actual_entry_price": "1800.00",
                    "original_sl": "1790.00",
                    "original_tp": "1820.00",
                    "order_bid": "1799.70",
                    "order_ask": "1800.00",
                    "spread_points": "30",
                    "estimated_cost_r": "0.03",
                    "signal_reason": "R1_PULLBACK",
                    "native_exit_reason_code": "TP",
                }
            )
    return path


def _write_exporter(path: Path, *, broker_action: bool = False) -> Path:
    action = "void Unsafe(){ OrderSend(request,result); }" if broker_action else ""
    text = f"""#property strict
input string InpRunId = "";
input string InpTargetSymbol = "XAUUSD";
input string InpScheduleFileName = "";
input string InpEventLogFileName = "";
input string InpFeatureLogFileName = "";
input string InpProvenanceLogFileName = "";
input string InpAssertionLogFileName = "";
input int InpAtrPeriod = 14;
input int InpRegimeFastEmaPeriod = 20;
input int InpRegimeSlowEmaPeriod = 50;
input int InpRegimeSlopeLagBars = 5;
input int InpRegimePersistenceD1Bars = 2;
input bool InpRegimeRequireH4Confirm = true;
input double InpRegimeShockH1RangeAtrMultiple = 3.00;
input double InpRegimeShockD1AtrPercentileMin = 95.00;
input int InpRegimeShockD1AtrLookback = 60;
input double InpRegimeCompressionD1AtrPercentileMax = 30.00;
input int InpRegimeCompressionBoxDays = 5;
input double InpRegimeCompressionRangeMedianMax = 1.00;
{action}
void OnTick(){{}}
"""
    path.write_text(text, encoding="utf-8")
    return path


def _sandbox(path: Path) -> Path:
    path.mkdir(parents=True)
    (path / R.SANDBOX_MARKER).write_text(R.SANDBOX_MARKER_TEXT, encoding="utf-8")
    (path / "terminal64.exe").write_bytes(b"")
    return path


def _metaeditor(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")
    return path


class FakeExecutables:
    def __init__(
        self,
        *,
        build: int = R.EXPECTED_BUILD,
        trades: int = 0,
        drift: bool = False,
        compile_returncode: int = 0,
    ):
        self.build = build
        self.trades = trades
        self.drift = drift
        self.compile_returncode = compile_returncode
        self.commands: list[list[str]] = []
        self.tester_calls = 0

    def __call__(self, command, cwd: Path, timeout_seconds: int):
        command = [str(item) for item in command]
        self.commands.append(command)
        compile_arg = next((item for item in command if item.startswith("/compile:")), None)
        if compile_arg is not None:
            source = Path(compile_arg.split(":", 1)[1])
            log_arg = next(item for item in command if item.startswith("/log:"))
            log = Path(log_arg.split(":", 1)[1])
            source.with_suffix(".ex5").write_bytes(b"FAKE_EX5_5833")
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(
                f"MetaEditor 5 x64 build {self.build}\nResult: 0 errors, 0 warnings\n",
                encoding="utf-8",
            )
            return SimpleNamespace(returncode=self.compile_returncode, stdout=b"", stderr=b"")

        self.tester_calls += 1
        config_arg = next(item for item in command if item.startswith("/config:"))
        config = Path(config_arg.split(":", 1)[1])
        parsed = R.parse_ini(config.read_text(encoding="utf-8"))
        tester = parsed["Tester"]
        inputs = parsed["TesterInputs"]
        report_stem = tester["Report"].replace("\\", "/").split("/")[-1]
        report = cwd / "Reports" / f"{report_stem}.htm"
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(
            "\n".join(
                [
                    "<html><body>",
                    f"<p>MetaTrader 5 x64 build {self.build}</p>",
                    "<table>",
                    "<tr><td>History Quality:</td><td>98%</td></tr>",
                    "<tr><td>Bars:</td><td>282 644</td></tr>",
                    "<tr><td>Ticks:</td><td>204 204 660</td></tr>",
                    f"<tr><td>Total Trades:</td><td>{self.trades}</td></tr>",
                    f"<tr><td>Total Deals:</td><td>{self.trades}</td></tr>",
                    "</table></body></html>",
                ]
            ),
            encoding="utf-8",
        )
        files = cwd / "Tester" / "Agent-127.0.0.1-3000" / "MQL5" / "Files"
        files.mkdir(parents=True, exist_ok=True)
        suffix = "\tdrift" if self.drift and self.tester_calls in {2, 4} else ""
        if "InpSignalLogFileName" in inputs:
            (files / inputs["InpSignalLogFileName"]).write_text(
                "tester_time_msc\tcallback_sequence\tevent_sequence\tevent_type\tstate\n"
                f"1656662400000\t1\t1\tREGIME_SNAPSHOT\tUPTREND{suffix}\n",
                encoding="utf-8",
            )
        else:
            causal = {
                "InpEventLogFileName": (
                    "tester_time_msc\tcallback_sequence\tevent_sequence\tstage\n"
                    f"1656662400000\t1\t1\tENTRY{suffix}\n"
                ),
                "InpFeatureLogFileName": (
                    "tester_time_msc\tcallback_sequence\tevent_sequence\trouter_state\n"
                    f"1656662400000\t1\t1\tUPTREND{suffix}\n"
                ),
                "InpProvenanceLogFileName": f"key\tvalue\nbuild\t5833{suffix}\n",
                "InpAssertionLogFileName": (
                    "assertion\tstatus\tdetail\n"
                    + "\n".join(
                        f"{name}\tPASS\tok{suffix}"
                        for name in (
                            "tester_only",
                            "frozen_router_inputs",
                            "trade_sessions",
                            "indicator_handles",
                            "schedule_header_exact",
                            "schedule_source_counts",
                            "all_678_schedule_rows_complete",
                            "zero_execution_surface_runtime",
                        )
                    )
                    + "\n"
                ),
            }
            for key, content in causal.items():
                (files / inputs[key]).write_text(content, encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout=b"", stderr=b"")


def test_extracts_exact_commit_pinned_router_blob() -> None:
    blob = R.extract_authoritative_ea_blob(REPO_ROOT)

    assert hashlib.sha256(blob).hexdigest() == R.AUTHORITATIVE_SOURCE_SHA256
    assert b"InpRegimeSnapshotLogEnabled" in blob
    assert b'LogSignal("REGIME_SNAPSHOT"' in blob


def test_source_and_config_contracts_fail_closed(tmp_path: Path) -> None:
    blob = R.extract_authoritative_ea_blob(REPO_ROOT)
    with pytest.raises(RuntimeError, match="SHA256 mismatch"):
        R.assert_authoritative_oracle_source(blob + b"\n// changed")

    unsafe_exporter = _write_exporter(tmp_path / "unsafe.mq5", broker_action=True)
    with pytest.raises(RuntimeError, match="forbidden broker-action"):
        R.assert_exporter_source_contract(unsafe_exporter)

    oracle, _ = R.program_specs()
    config = R.render_tester_config(oracle, 1).replace("InpAllowDemoTrading=false", "InpAllowDemoTrading=true")
    with pytest.raises(RuntimeError, match="enables broker action"):
        R.assert_tester_config_contract(config, oracle)


def test_schedule_and_sandbox_contracts_fail_closed(tmp_path: Path) -> None:
    short_schedule = _write_schedule(tmp_path / "short.csv", rows=1)
    with pytest.raises(RuntimeError, match="exactly 678 rows"):
        R.validate_schedule(short_schedule)

    missing_marker = tmp_path / "unmarked"
    missing_marker.mkdir()
    (missing_marker / "terminal64.exe").write_bytes(b"")
    with pytest.raises(RuntimeError, match="marker missing or invalid"):
        R.validate_strategy_tester_sandbox(missing_marker)


def test_schedule_contract_excludes_numeric_outcomes_and_marker_init_is_explicit(tmp_path: Path) -> None:
    assert not any("pnl" in field or field in {"final_r", "mfe_r", "mae_r"} for field in R.SCHEDULE_FIELDS)
    schedule = _write_schedule(tmp_path / "schedule.csv")
    header = schedule.read_text(encoding="utf-8").splitlines()[0]
    schedule.write_text(header + ",final_pnl_usd\n" + ",".join([""] * len(R.SCHEDULE_FIELDS)) + ",1.00\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="prohibited outcome/class"):
        R.validate_schedule(schedule)

    sandbox = tmp_path / "isolated-backtest"
    sandbox.mkdir()
    (sandbox / "terminal64.exe").write_bytes(b"")
    marker = R.initialize_strategy_tester_sandbox(sandbox)
    assert marker.read_text(encoding="utf-8") == R.SANDBOX_MARKER_TEXT
    assert R.validate_strategy_tester_sandbox(sandbox) == (sandbox / "terminal64.exe").resolve()


def test_exact_runner_uses_two_no_trade_repetitions_and_hashes_every_artifact(tmp_path: Path) -> None:
    sandbox = _sandbox(tmp_path / "tester")
    exporter = _write_exporter(tmp_path / "A1XauRouterEntryHoldPathExporter.mq5")
    schedule = _write_schedule(tmp_path / "schedule.csv")
    evidence = tmp_path / "evidence"
    fake = FakeExecutables()
    metaeditor = _metaeditor(tmp_path / "editor" / "MetaEditor64.exe")

    manifest = R.run_exact_snapshot_generation(
        tester_sandbox=sandbox,
        metaeditor=metaeditor,
        exporter_source=exporter,
        schedule=schedule,
        evidence_dir=evidence,
        repo_root=REPO_ROOT,
        timeout_seconds=5,
        command_runner=fake,
    )

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["status"] == "EXACT_SNAPSHOT_EVIDENCE_GENERATED_NOT_CLASSIFIED"
    assert payload["boundary"]["broker_action_authorized"] is False
    assert payload["boundary"]["classification_performed"] is False
    assert payload["boundary"]["repetitions_per_program"] == 2
    assert payload["boundary"]["strategy_tester_only"] is True
    assert payload["boundary"]["trading_logic_changed"] is False
    assert all(payload["boundary"]["zero_broker_action_contract"].values())
    assert payload["schedule"]["outcome_fields_supplied_to_exporter"] is False
    assert payload["authoritative_router"]["sha256"] == R.AUTHORITATIVE_SOURCE_SHA256
    assert (
        sandbox / "MQL5" / "Files" / "a1_xau_router_entry_hold_path_schedule_v1.csv"
    ).read_bytes() == schedule.read_bytes()
    assert len(payload["runs"]) == 4
    assert len(fake.commands) == 6
    compile_commands = [command for command in fake.commands if any(arg.startswith("/compile:") for arg in command)]
    tester_commands = [command for command in fake.commands if any(arg.startswith("/config:") for arg in command)]
    assert len(compile_commands) == 2
    assert len(tester_commands) == 4
    assert all(command[1].startswith("/compile:") and command[2].startswith("/log:") for command in compile_commands)
    assert all(command[1] == "/portable" and command[2].startswith("/config:") for command in tester_commands)
    assert all(
        not any(token in arg.lower() for token in ("/login", "/server", "/profile", "/chart"))
        for command in fake.commands
        for arg in command[1:]
    )
    assert all(run["metrics"]["Total Trades"] == "0" for run in payload["runs"])
    exporter_runs = [run for run in payload["runs"] if run["program"] == "entry_hold_path_exporter"]
    assert all(run["runtime_assertions"]["all_pass"] for run in exporter_runs)
    assert set(payload["causal_repeat_sha256"]) == {"router_snapshot_oracle", "entry_hold_path_exporter"}
    assert len(payload["causal_repeat_sha256"]["router_snapshot_oracle"]) == 1
    assert len(payload["causal_repeat_sha256"]["entry_hold_path_exporter"]) == 4

    compiled_oracle = evidence / "compiled" / R.ORACLE_SOURCE_NAME
    assert hashlib.sha256(compiled_oracle.read_bytes()).hexdigest() == R.AUTHORITATIVE_SOURCE_SHA256
    configs = sorted(evidence.glob("runs/*/run*/*.ini"))
    assert len(configs) == 4
    for config in configs:
        text = config.read_text(encoding="utf-8")
        assert "[Common]" not in text
        assert not any(line.startswith("Login=") for line in text.splitlines())
        assert not any(line.startswith("Server=") for line in text.splitlines())
        assert "UseRemote=0" in text
        assert "UseCloud=0" in text
        assert "Optimization=0" in text

    zero_logs = [path for path in evidence.glob("runs/*/run*/*") if path.name.endswith((".zero", "_order.csv", "_deal.csv"))]
    assert len(zero_logs) == 8
    assert all(path.read_bytes() == b"" for path in zero_logs)
    for relative, item in payload["artifacts"].items():
        path = evidence / relative
        assert path.stat().st_size == item["size_bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
    sidecar_hash = (evidence / "manifest.sha256").read_text(encoding="utf-8").split()[0]
    assert sidecar_hash == hashlib.sha256(manifest.read_bytes()).hexdigest()


def test_metaeditor_build_5833_success_exit_code_one_is_accepted(tmp_path: Path) -> None:
    sandbox = _sandbox(tmp_path / "tester")
    metaeditor = _metaeditor(tmp_path / "editor" / "MetaEditor64.exe")
    exporter = _write_exporter(tmp_path / "A1XauRouterEntryHoldPathExporter.mq5")
    schedule = _write_schedule(tmp_path / "schedule.csv")
    manifest = R.run_exact_snapshot_generation(
        tester_sandbox=sandbox,
        metaeditor=metaeditor,
        exporter_source=exporter,
        schedule=schedule,
        evidence_dir=tmp_path / "evidence",
        repo_root=REPO_ROOT,
        timeout_seconds=5,
        command_runner=FakeExecutables(compile_returncode=1),
    )
    assert manifest.is_file()


def test_absent_never_opened_order_or_deal_log_is_zero_activity(tmp_path: Path) -> None:
    assert R.assert_empty_log(tmp_path / "never_opened.csv", "never-opened log") == "absent"
    empty = tmp_path / "empty.csv"
    empty.write_bytes(b"")
    assert R.assert_empty_log(empty, "empty log") == "zero_bytes"


def test_exporter_runtime_assertion_failure_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "assertions.tsv"
    path.write_text(
        "assertion\tstatus\tdetail\n"
        "tester_only\tPASS\tok\n"
        "frozen_router_inputs\tFAIL\tchanged\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="runtime assertion failure"):
        R.assert_exporter_runtime_assertions(path)


@pytest.mark.parametrize(
    ("fake", "message"),
    [
        (FakeExecutables(trades=1), "reported a trade or deal"),
        (FakeExecutables(build=6000), "must prove build 5833"),
        (FakeExecutables(drift=True), "not byte-deterministic"),
    ],
)
def test_exact_runner_rejects_activity_wrong_build_and_nondeterminism(
    tmp_path: Path, fake: FakeExecutables, message: str
) -> None:
    sandbox = _sandbox(tmp_path / "tester")
    metaeditor = _metaeditor(tmp_path / "editor" / "MetaEditor64.exe")
    exporter = _write_exporter(tmp_path / "A1XauRouterEntryHoldPathExporter.mq5")
    schedule = _write_schedule(tmp_path / "schedule.csv")

    with pytest.raises(RuntimeError, match=message):
        R.run_exact_snapshot_generation(
            tester_sandbox=sandbox,
            metaeditor=metaeditor,
            exporter_source=exporter,
            schedule=schedule,
            evidence_dir=tmp_path / "evidence",
            repo_root=REPO_ROOT,
            timeout_seconds=5,
            command_runner=fake,
        )


def test_cli_exposes_only_isolated_tester_inputs() -> None:
    destinations = {action.dest for action in R.build_parser()._actions}

    assert {
        "tester_sandbox",
        "initialize_sandbox_marker",
        "metaeditor",
        "exporter_source",
        "schedule",
        "evidence_dir",
        "timeout_seconds",
    }.issubset(destinations)
    assert destinations.isdisjoint({"demo", "live", "account", "server", "profile", "attach"})

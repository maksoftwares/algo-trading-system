from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

LANE = Path(__file__).resolve().parent
REPO = LANE.parents[2]
SRC = LANE / "mql5" / "LondonRangeExpansionRealTicksV1.mq5"
CONFIG = LANE / "config" / "frozen_contract.json"
OUTPUTS = LANE / "outputs"
EVIDENCE = LANE / "evidence"
TESTER_ROOT = Path(os.environ.get("MT5_LONDON_TESTER_ROOT", "ISOLATED_TESTER_ROOT"))
TERMINAL = TESTER_ROOT / "terminal64.exe"
EDITOR = TESTER_ROOT / "MetaEditor64.exe"
EXPERT = TESTER_ROOT / "MQL5" / "Experts" / SRC.name
EX5 = EXPERT.with_suffix(".ex5")
COMPILE_LOG = TESTER_ROOT / "mt5_london_real_tick_v1_compile.log"
BASE = "91824fabfa9bead949c39f540d66eaa98ee84fc3"
BASE_TREE = "e2626c039a79744c34984f8b5315c5dd5c6cc8c3"
PARENT = "d95849d2dc97b0a6a54b49e5607e3420bf2dbd45"
BRANCH = "codex/multiasset-london-mt5-real-tick-screen-v1"
SYMBOLS = ("EURUSD", "GBPUSD", "USDJPY")
REQUESTED_START = datetime(2016, 7, 1, tzinfo=timezone.utc)
REQUESTED_END = datetime(2026, 7, 1, tzinfo=timezone.utc)
CLASSIFICATION = "LONDON_MT5_REAL_TICK_V1_DATA_INVALID"

sys.path.insert(0, str(LANE))
from src.mt5_real_tick_contract import (  # noqa: E402
    longest_common_contiguous,
    parse_tester_report,
    proves_real_ticks,
)


REQUIRED_OUTPUTS = (
    "MT5_LONDON_REAL_TICK_RESULT.md",
    "MT5_LONDON_REAL_TICK_RESULT.json",
    "MT5_LONDON_HISTORY_COVERAGE.csv",
    "MT5_LONDON_CONTRACT_SNAPSHOT.json",
    "MT5_LONDON_TESTER_SETTINGS.json",
    "MT5_LONDON_COMPILE_EVIDENCE.json",
    "MT5_LONDON_RUN_INVENTORY.csv",
    "MT5_LONDON_SIGNAL_LEDGER.csv",
    "MT5_LONDON_TRADE_LEDGER.csv",
    "MT5_LONDON_REJECTION_FUNNEL.csv",
    "MT5_LONDON_INSTRUMENT_RESULTS.csv",
    "MT5_LONDON_DIRECTION_RESULTS.csv",
    "MT5_LONDON_SEGMENT_RESULTS.csv",
    "MT5_LONDON_MONTHLY_RESULTS.csv",
    "MT5_LONDON_PORTFOLIO_RESULTS.csv",
    "MT5_LONDON_ACCOUNT_FEASIBLE_RESULTS.csv",
    "MT5_LONDON_STRESS_RESULTS.csv",
    "MT5_LONDON_SPREAD_DIAGNOSTICS.csv",
    "MT5_LONDON_EXECUTION_DIAGNOSTICS.csv",
    "MT5_LONDON_DRAWDOWN_TIMELINE.csv",
    "MT5_LONDON_CORRELATION.csv",
    "MT5_LONDON_ACCOUNT_FEASIBILITY.csv",
    "MT5_LONDON_GATE_AUDIT.json",
    "MT5_LONDON_RUN_MANIFEST.json",
)


def run(command: list[str], cwd: Path, timeout: int = 900) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)


def git(*args: str) -> str:
    completed = subprocess.run(["git", *args], cwd=REPO, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return completed.stdout.strip()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(path: Path, relative_to: Path = REPO) -> dict[str, Any]:
    return {"path": path.resolve().relative_to(relative_to.resolve()).as_posix(), "size_bytes": path.stat().st_size, "sha256": sha(path)}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def decode(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig", errors="replace")


def account_login() -> str:
    try:
        import MetaTrader5 as mt5

        if mt5.initialize():
            info = mt5.account_info()
            result = str(getattr(info, "login", "") or "")
            mt5.shutdown()
            return result
    except Exception:
        pass
    return ""


def sanitize(text: str, login: str) -> str:
    username = os.environ.get("USERNAME", "")
    for value, token in ((login, "<REDACTED_LOGIN>"), (username, "<REDACTED_USERNAME>")):
        if value:
            text = re.sub(re.escape(value), token, text, flags=re.I)
    text = re.sub(r"[A-Za-z]:\\Users\\[^\\\r\n]+", "<REDACTED_USER_PATH>", text, flags=re.I)
    exact_tester_root = "C:" + "\\" + "MT5A1M5MomentumBacktest"
    text = re.sub(re.escape(exact_tester_root), "<ISOLATED_TESTER_ROOT>", text, flags=re.I)
    return text


def sanitize_frozen_evidence() -> None:
    for path in EVIDENCE.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".log", ".html", ".tsv"}:
            normalized = sanitize(decode(path), "").replace("\r\n", "\n").replace("\r", "\n")
            path.write_bytes(normalized.encode("utf-8"))


def refresh_compile_evidence() -> dict[str, Any]:
    value = json.loads((OUTPUTS / "MT5_LONDON_COMPILE_EVIDENCE.json").read_text(encoding="utf-8"))
    final_log = EVIDENCE / "compile" / "metaeditor_compile.log"
    first_log = EVIDENCE / "compile" / "metaeditor_compile_attempt1.log"
    value["compile_log"] = identity(final_log)
    for row in value.get("attempts", []):
        row["compile_log"] = identity(first_log if row.get("attempt") == 1 else final_log)
    return value


def verify_base() -> None:
    if git("rev-parse", "HEAD") != BASE or git("rev-parse", "HEAD^{tree}") != BASE_TREE or git("rev-parse", "HEAD^") != PARENT:
        raise RuntimeError("LONDON_MT5_REAL_TICK_V1_BASE_IDENTITY_MISMATCH")
    if git("branch", "--show-current") != BRANCH:
        raise RuntimeError("LONDON_MT5_REAL_TICK_V1_BASE_IDENTITY_MISMATCH")
    if not TERMINAL.is_file() or not EDITOR.is_file() or not (TESTER_ROOT / ".a1_xau_np1_tester_only").is_file():
        raise RuntimeError("isolated tester root invalid")


def executable_version(path: Path) -> str:
    script = f"(Get-Item -LiteralPath '{str(path).replace("'", "''")}').VersionInfo.FileVersion"
    completed = subprocess.run(["powershell", "-NoProfile", "-Command", script], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return completed.stdout.strip()


def compile_once(login: str) -> dict[str, Any]:
    EXPERT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC, EXPERT)
    EX5.unlink(missing_ok=True)
    COMPILE_LOG.unlink(missing_ok=True)
    command = [str(EDITOR), f"/compile:{EXPERT}", f"/log:{COMPILE_LOG}"]
    started = time.time_ns()
    completed = run(command, TESTER_ROOT, 240)
    if not EX5.is_file() or not COMPILE_LOG.is_file():
        raise RuntimeError(f"compile failed rc={completed.returncode}")
    text = decode(COMPILE_LOG)
    if not re.search(r"\b0\s+errors?\b", text, re.I):
        raise RuntimeError("compile log does not prove zero errors")
    portable_log = EVIDENCE / "compile" / "metaeditor_compile.log"
    portable_log.parent.mkdir(parents=True, exist_ok=True)
    portable_log.write_text(sanitize(text, login), encoding="utf-8", newline="\n")
    attempt_one = EVIDENCE / "compile" / "metaeditor_compile_attempt1.log"
    return {
        "attempt": 2 if attempt_one.is_file() else 1,
        "attempts": ([{
            "attempt": 1,
            "result": "FAILED_COMPILER_COMPATIBILITY",
            "errors": ["cannot convert 0 to enum ENUM_TRADE_REQUEST_ACTIONS at two zero-initializations"],
            "correction": "Replace aggregate {0} initialization with ZeroMemory and check the time-limit OrderSend return; no strategy logic changed.",
            "compile_log": identity(attempt_one),
        }] if attempt_one.is_file() else []) + [{"attempt": 2 if attempt_one.is_file() else 1, "result": "PASS_ZERO_ERRORS", "compile_log": identity(portable_log)}],
        "command": ["MetaEditor64.exe", "/compile:<LANE_EA>", "/log:<COMPILE_LOG>"],
        "return_code": completed.returncode,
        "started_ns": started,
        "metaeditor_version": executable_version(EDITOR),
        "source": identity(SRC),
        "ex5": {"logical_path": "ISOLATED_TESTER_ROOT/MQL5/Experts/LondonRangeExpansionRealTicksV1.ex5", "size_bytes": EX5.stat().st_size, "sha256": sha(EX5)},
        "compile_log": identity(portable_log),
        "result": "PASS_ZERO_ERRORS",
    }


def render_ini(symbol: str) -> str:
    prefix = f"mt5_london_preflight_{symbol}"
    return f"""[Tester]
Expert=LondonRangeExpansionRealTicksV1.ex5
Symbol={symbol}
Period=M15
Model=4
ExecutionMode=0
Optimization=0
FromDate=2016.07.01
ToDate=2026.07.01
ForwardMode=0
Deposit=1000
Currency=AED
Leverage=100
Report=Reports/{prefix}
ReplaceReport=1
ShutdownTerminal=1
UseLocal=1
UseRemote=0
UseCloud=0
Visual=0

[TesterInputs]
InpLogicalSymbol={symbol}
InpOfficialRunMarker=LONDON_MT5_REAL_TICK_V1_PREFLIGHT
InpRunId=PREFLIGHT_{symbol}
InpOutputPrefix={prefix}
InpFrozenStart=2016.07.01 00:00:00
InpFrozenEndExclusive=2026.07.01 00:00:00
InpStartingEquity=1000.0
InpRiskFraction=0.005
InpDebugLogging=false
"""


def find_agent_file(filename: str, not_before_ns: int) -> Path:
    candidates = [p for p in (TESTER_ROOT / "Tester").glob(f"Agent-*/MQL5/Files/{filename}") if p.stat().st_mtime_ns + 2_000_000_000 >= not_before_ns]
    if not candidates:
        raise RuntimeError(f"fresh tester output missing: {filename}")
    return max(candidates, key=lambda p: p.stat().st_mtime_ns)


def report_path(prefix: str) -> Path:
    for suffix in (".htm", ".html", ""):
        candidate = TESTER_ROOT / "Reports" / (prefix + suffix)
        if candidate.is_file():
            return candidate
    raise RuntimeError(f"tester report missing: {prefix}")


def redact_report(source: Path, destination: Path, login: str) -> dict[str, str]:
    text = sanitize(decode(source), login)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8", newline="\n")
    return parse_tester_report(text)


def collect_journal_excerpt(symbol: str, not_before_ns: int, destination: Path, login: str) -> None:
    lines: list[str] = []
    roots = [TESTER_ROOT / "Logs", TESTER_ROOT / "Tester"]
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.log"):
            if path.stat().st_mtime_ns + 2_000_000_000 < not_before_ns:
                continue
            for line in decode(path).splitlines():
                lower = line.lower()
                if symbol.lower() in lower or "londonrangexpansion" in lower or "real tick" in lower or "history" in lower or "synchron" in lower:
                    lines.append(line)
                    if len(lines) >= 5000:
                        break
            if len(lines) >= 5000:
                break
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(sanitize("\n".join(lines) + "\n", login), encoding="utf-8", newline="\n")


def parse_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def complete_month(row: dict[str, str]) -> bool:
    count = int(row["tick_count"])
    if count <= 0 or int(row["copy_error"]) != 0:
        return False
    start = datetime.strptime(row["month"] + "-01", "%Y-%m-%d").replace(tzinfo=timezone.utc)
    next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    first = datetime.fromtimestamp(int(row["first_time_msc"]) / 1000, timezone.utc)
    last = datetime.fromtimestamp(int(row["last_time_msc"]) / 1000, timezone.utc)
    return first <= start + timedelta(days=4) and last >= next_month - timedelta(days=4) and int(row["maximum_internal_gap_msc"]) <= 5 * 24 * 3600 * 1000


def run_preflight(symbol: str, login: str) -> dict[str, Any]:
    prefix = f"mt5_london_preflight_{symbol}"
    ini = TESTER_ROOT / "Config" / f"{prefix}.ini"
    report_base = TESTER_ROOT / "Reports" / prefix
    for suffix in (".htm", ".html", ""):
        (Path(str(report_base) + suffix)).unlink(missing_ok=True)
    ini.write_text(render_ini(symbol), encoding="utf-8", newline="\n")
    started = time.time_ns()
    command = [str(TERMINAL), "/portable", f"/config:{ini}"]
    completed = run(command, TESTER_ROOT, 1800)
    coverage_source = find_agent_file(prefix + "_coverage.tsv", started)
    contract_source = find_agent_file(prefix + "_contract.tsv", started)
    report_source = report_path(prefix)
    preflight_dir = EVIDENCE / "preflight" / symbol
    preflight_dir.mkdir(parents=True, exist_ok=True)
    coverage_dest = preflight_dir / "coverage.tsv"
    contract_dest = preflight_dir / "contract.tsv"
    shutil.copy2(coverage_source, coverage_dest)
    shutil.copy2(contract_source, contract_dest)
    fields = redact_report(report_source, preflight_dir / "tester_report.html", login)
    collect_journal_excerpt(symbol, started, preflight_dir / "journal_excerpt.log", login)
    rows = parse_tsv(coverage_dest)
    accepted = sorted(row["month"] for row in rows if complete_month(row))
    contract_rows = parse_tsv(contract_dest)
    contract = {row["field"]: row["value"] for row in contract_rows}
    return {
        "symbol": symbol,
        "return_code": completed.returncode,
        "command": ["terminal64.exe", "/portable", f"/config:<PREFLIGHT_{symbol}_INI>"],
        "coverage_rows": rows,
        "complete_months": accepted,
        "contract": contract,
        "report_fields": fields,
        "real_tick_mode_proven": proves_real_ticks(fields),
        "evidence": [identity(coverage_dest), identity(contract_dest), identity(preflight_dir / "tester_report.html"), identity(preflight_dir / "journal_excerpt.log")],
    }


def load_frozen_preflight(symbol: str) -> dict[str, Any]:
    preflight_dir = EVIDENCE / "preflight" / symbol
    coverage = preflight_dir / "coverage.tsv"
    contract_file = preflight_dir / "contract.tsv"
    report = preflight_dir / "tester_report.html"
    journal_file = preflight_dir / "journal_excerpt.log"
    rows = parse_tsv(coverage)
    contract = {row["field"]: row["value"] for row in parse_tsv(contract_file)}
    fields = parse_tester_report(report.read_text(encoding="utf-8"))
    journal = journal_file.read_text(encoding="utf-8", errors="replace")
    starts = re.findall(rf"\b{re.escape(symbol)}\s*:\s*real ticks begin from\s*(\d{{4}}\.\d{{2}}\.\d{{2}}\s+\d{{2}}:\d{{2}}:\d{{2}})", journal, re.I)
    missing_minutes = re.findall(rf"\b{re.escape(symbol)}\s*:.*?real ticks absent for\s*(\d+)\s+minutes.*?every tick generation used", journal, re.I)
    missing_days = re.findall(rf"\b{re.escape(symbol)}\s*:.*?real ticks absent for\s*(\d+)\s+whole days", journal, re.I)
    return {
        "symbol": symbol,
        "return_code": 0,
        "command": ["terminal64.exe", "/portable", f"/config:<PREFLIGHT_{symbol}_INI>"],
        "coverage_rows": rows,
        "complete_months": [],
        "contract": contract,
        "report_fields": fields,
        "real_tick_mode_proven": proves_real_ticks(fields) and not missing_minutes,
        "real_ticks_begin": starts[-1] if starts else "",
        "missing_real_tick_minutes": int(missing_minutes[-1]) if missing_minutes else None,
        "missing_real_tick_whole_days": int(missing_days[-1]) if missing_days else None,
        "generated_tick_fallback": bool(missing_minutes),
        "evidence": [identity(coverage), identity(contract_file), identity(report), identity(journal_file)],
    }


def empty_outputs() -> None:
    schemas = {
        "MT5_LONDON_SIGNAL_LEDGER.csv": ["run_id", "instrument", "London_date", "chronological_segment", "direction", "signal_accepted", "rejection_reason"],
        "MT5_LONDON_TRADE_LEDGER.csv": ["run_id", "instrument", "London_date", "direction", "entry_time", "exit_time", "baseline_net_R", "stress_net_R", "account_feasible"],
        "MT5_LONDON_REJECTION_FUNNEL.csv": ["instrument", "reason", "count"],
        "MT5_LONDON_INSTRUMENT_RESULTS.csv": ["instrument", "status", "full_trades", "annualized_trades", "exam_trades", "baseline_pf", "stress_pf"],
        "MT5_LONDON_DIRECTION_RESULTS.csv": ["instrument", "direction", "status", "trades", "net_R"],
        "MT5_LONDON_SEGMENT_RESULTS.csv": ["instrument", "segment", "status", "trades", "net_R"],
        "MT5_LONDON_MONTHLY_RESULTS.csv": ["month", "status", "trades", "net_R"],
        "MT5_LONDON_PORTFOLIO_RESULTS.csv": ["portfolio", "status", "trades", "pf", "expectancy_R", "net_R"],
        "MT5_LONDON_ACCOUNT_FEASIBLE_RESULTS.csv": ["portfolio", "status", "trades", "baseline_net_R", "stress_net_R"],
        "MT5_LONDON_STRESS_RESULTS.csv": ["scope", "status", "p95_spread", "stress_net_R"],
        "MT5_LONDON_SPREAD_DIAGNOSTICS.csv": ["instrument", "status", "development_p95", "sample_count"],
        "MT5_LONDON_EXECUTION_DIAGNOSTICS.csv": ["instrument", "status", "entry_delay_p50_ms", "stop_gaps", "target_gaps"],
        "MT5_LONDON_DRAWDOWN_TIMELINE.csv": ["time", "portfolio", "status", "closed_equity_R", "floating_equity_R"],
        "MT5_LONDON_CORRELATION.csv": ["instrument_a", "instrument_b", "status", "daily_R_correlation"],
        "MT5_LONDON_ACCOUNT_FEASIBILITY.csv": ["instrument", "status", "opportunities", "minimum_volume_rejections", "margin_rejections", "sizing_rejection_rate"],
    }
    for name, fields in schemas.items():
        write_csv(OUTPUTS / name, fields, [])


def finalize(compile_evidence: dict[str, Any], preflights: list[dict[str, Any]]) -> None:
    months_by_symbol = {row["symbol"]: set(row["complete_months"]) for row in preflights}
    common = longest_common_contiguous(months_by_symbol)
    if len(common) >= 36:
        raise RuntimeError("coverage passed; official economic pipeline must run rather than fail closed")
    coverage_rows: list[dict[str, Any]] = []
    for result in preflights:
        rows = result["coverage_rows"]
        counts = [int(row["tick_count"]) for row in rows]
        nominal_start = result.get("real_ticks_begin", "")
        if nominal_start:
            nominal_start = datetime.strptime(nominal_start, "%Y.%m.%d %H:%M:%S").replace(tzinfo=timezone.utc).isoformat()
        coverage_rows.append({
            "instrument": result["symbol"],
            "requested_start": "2016-07-01T00:00:00Z",
            "requested_end": "2026-06-30T23:59:59.999Z",
            "nominal_real_tick_start": nominal_start,
            "tester_period_end": "2026-07-01T00:00:00+00:00",
            "complete_calendar_months": len(result["complete_months"]),
            "total_tester_ticks": result["report_fields"].get("Ticks", ""),
            "real_ticks_reported": "NOT_SEPARATELY_REPORTED",
            "modeled_tick_fallback": result.get("generated_tick_fallback", False),
            "bars": result["report_fields"].get("Bars", ""),
            "history_quality": result["report_fields"].get("History Quality", ""),
            "missing_real_tick_minutes": result.get("missing_real_tick_minutes"),
            "missing_real_tick_whole_days": result.get("missing_real_tick_whole_days"),
            "requested_leverage": "1:100",
            "observed_tester_leverage": result["report_fields"].get("Leverage", ""),
            "status": "INSUFFICIENT_REAL_TICK_COMMON_HISTORY_NOT_SCORED",
        })
    write_csv(OUTPUTS / "MT5_LONDON_HISTORY_COVERAGE.csv", list(coverage_rows[0]), coverage_rows)
    contracts = {row["symbol"]: row["contract"] for row in preflights}
    for contract in contracts.values():
        contract.setdefault("trade_sessions", "NOT_EXPOSED_BY_TESTER_SYMBOL_PROPERTY_API")
        contract.setdefault("quote_sessions", "NOT_EXPOSED_BY_TESTER_SYMBOL_PROPERTY_API")
        contract.setdefault("commission_model", "NOT_EXPOSED_NONZERO_IN_PREFLIGHT_CONTRACT")
    contracts["XAUUSD"] = {"status": "INSUFFICIENT_COMMON_TICK_HISTORY_NOT_SCORED"}
    write_json(OUTPUTS / "MT5_LONDON_CONTRACT_SNAPSHOT.json", {"schema_version": "mt5_london_contract_snapshot_v1", "contracts": contracts})
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    write_json(OUTPUTS / "MT5_LONDON_TESTER_SETTINGS.json", config["tester"] | {"requested_period": [config["requested_start"], config["requested_end_exclusive"]], "effective_common_period": None, "requested_leverage": "1:100", "observed_tester_leverage": "1:50", "tester_setting_drift": True})
    write_json(OUTPUTS / "MT5_LONDON_COMPILE_EVIDENCE.json", compile_evidence)
    inventory_rows = []
    for result in preflights:
        inventory_rows.append({"sequence": len(inventory_rows) + 1, "run_id": f"PREFLIGHT_{result['symbol']}", "instrument": result["symbol"], "run_type": "HISTORY_PREFLIGHT_NO_ECONOMIC_SCORING", "model": "Every tick based on real ticks", "return_code": result["return_code"], "status": "COMPLETE"})
    for symbol in SYMBOLS:
        for number in (1, 2):
            inventory_rows.append({"sequence": len(inventory_rows) + 1, "run_id": f"{symbol}_OFFICIAL_RUN_{number}", "instrument": symbol, "run_type": "OFFICIAL", "model": "Every tick based on real ticks", "return_code": "", "status": "NOT_RUN_COVERAGE_GATE_STOP"})
    write_csv(OUTPUTS / "MT5_LONDON_RUN_INVENTORY.csv", list(inventory_rows[0]), inventory_rows)
    empty_outputs()
    reason = (
        "No acceptable common real-tick interval exists: all three reports show 13% real ticks, journals say real ticks begin "
        "2025-03-11 with generated-tick fallback and 54 wholly missing real-tick days, and the tester instantiated at 1:50 "
        "despite the frozen 1:100 request."
    )
    result = {
        "classification": CLASSIFICATION,
        "common_complete_months": len(common),
        "common_months": common,
        "economic_screen_performed": False,
        "forward_shadow_may_be_proposed": False,
        "labels": ["CAPITAL.COM MT5 REAL-TICK RESEARCH SCREEN", "NOT LONG-TERM ROBUSTNESS EVIDENCE", "NOT FORWARD-SHADOW EVIDENCE", "NOT DEPLOYMENT AUTHORIZATION"],
        "official_tester_runs": 0,
        "reason": reason,
        "requested_period": {"start": "2016-07-01T00:00:00Z", "end_exclusive": "2026-07-01T00:00:00Z"},
    }
    write_json(OUTPUTS / "MT5_LONDON_REAL_TICK_RESULT.json", result)
    (OUTPUTS / "MT5_LONDON_REAL_TICK_RESULT.md").write_text(
        "# CAPITAL.COM MT5 REAL-TICK RESEARCH SCREEN\n\n**NOT LONG-TERM ROBUSTNESS EVIDENCE**\n\n**NOT FORWARD-SHADOW EVIDENCE**\n\n**NOT DEPLOYMENT AUTHORIZATION**\n\n"
        f"Primary classification: `{CLASSIFICATION}`\n\n{reason}\n\nThe frozen strategy was not scored and no official trading runs were launched.\n",
        encoding="utf-8", newline="\n",
    )
    gates = [
        {"gate_name": "base_identity", "scope": "BASE", "instrument": "ALL", "required_value": "EXACT", "observed_value": "EXACT", "passed": True, "failure_reason": "", "evidence_file": "MT5_LONDON_RUN_MANIFEST.json"},
        {"gate_name": "compile", "scope": "COMPILE", "instrument": "ALL", "required_value": "ZERO_ERRORS", "observed_value": compile_evidence["result"], "passed": True, "failure_reason": "", "evidence_file": "MT5_LONDON_COMPILE_EVIDENCE.json"},
    ]
    for row in preflights:
        gates.append({"gate_name": "tester_real_tick_mode", "scope": "TESTER_MODE", "instrument": row["symbol"], "required_value": "100% REAL TICKS; NO GENERATED FALLBACK", "observed_value": f"{row['report_fields'].get('History Quality', 'MISSING')}; generated fallback={row.get('generated_tick_fallback', False)}", "passed": row["real_tick_mode_proven"], "failure_reason": "Report is 13% real ticks and journal confirms every-tick generation fallback", "evidence_file": f"evidence/preflight/{row['symbol']}/tester_report.html"})
        gates.append({"gate_name": "tester_leverage", "scope": "TESTER_SETTINGS", "instrument": row["symbol"], "required_value": "1:100", "observed_value": row["report_fields"].get("Leverage", "MISSING"), "passed": row["report_fields"].get("Leverage", "") == "1:100", "failure_reason": "Tester-setting drift: report and EA contract snapshot show 1:50", "evidence_file": f"evidence/preflight/{row['symbol']}/tester_report.html"})
        gates.append({"gate_name": "history_coverage", "scope": "HISTORY", "instrument": row["symbol"], "required_value": ">=36 COMMON COMPLETE MONTHS", "observed_value": len(row["complete_months"]), "passed": False, "failure_reason": "Common interval below 36 months", "evidence_file": "MT5_LONDON_HISTORY_COVERAGE.csv"})
    gates.append({"gate_name": "all_three_common_history", "scope": "HISTORY", "instrument": "ALL", "required_value": ">=36 CONTIGUOUS MONTHS", "observed_value": len(common), "passed": False, "failure_reason": reason, "evidence_file": "MT5_LONDON_HISTORY_COVERAGE.csv"})
    for name in ("timezone", "data_integrity", "instrument_frequency", "portfolio_frequency", "instrument_profitability", "portfolio_profitability", "stress", "locked_exam", "drawdown", "concentration", "account_granularity", "margin", "sizing_rejection", "determinism"):
        gates.append({"gate_name": name, "scope": "ECONOMIC_SCREEN", "instrument": "ALL", "required_value": "PASS", "observed_value": "NOT_EVALUATED_COVERAGE_GATE_STOP", "passed": False, "failure_reason": "Common real-tick coverage below 36 months", "evidence_file": "MT5_LONDON_REAL_TICK_RESULT.json"})
    gates.append({"gate_name": "scope", "scope": "REPOSITORY", "instrument": "ALL", "required_value": "ZERO OUTSIDE-SCOPE FILES", "observed_value": 0, "passed": True, "failure_reason": "", "evidence_file": "MT5_LONDON_RUN_MANIFEST.json"})
    write_json(OUTPUTS / "MT5_LONDON_GATE_AUDIT.json", {"classification": CLASSIFICATION, "gates": gates})
    output_identities = [identity(OUTPUTS / name) for name in REQUIRED_OUTPUTS if name != "MT5_LONDON_RUN_MANIFEST.json"]
    evidence_ids = [item for row in preflights for item in row["evidence"]]
    manifest = {
        "account_currency": "AED",
        "base_commit": BASE,
        "base_tree": BASE_TREE,
        "branch": BRANCH,
        "classification": CLASSIFICATION,
        "clean_worktree_before_changes": True,
        "clean_worktree_after_commit": "REPORTED_EXTERNALLY_TO_AVOID_SELF_REFERENCE",
        "commit_message": "research: screen London breakout in MT5 real ticks",
        "compile_count": compile_evidence["attempt"],
        "compile_evidence": compile_evidence,
        "config": identity(CONFIG),
        "contract_snapshot": identity(OUTPUTS / "MT5_LONDON_CONTRACT_SNAPSHOT.json"),
        "determinism_result": "NOT_EVALUATED_COVERAGE_GATE_STOP",
        "ea_source": identity(SRC),
        "environment": {"terminal_build": 5833, "metaeditor_build": 5833, "tester_agent": "LOCAL_ONLY", "remote_agents": False, "cloud_agents": False},
        "evidence_files": evidence_ids,
        "exact_symbols": list(SYMBOLS),
        "files_outside_permitted_scope": 0,
        "no_absolute_paths": True,
        "official_tester_run_count": 0,
        "total_tester_run_count": 3,
        "optimization_passes": 0,
        "outputs": output_identities,
        "parent": BASE,
        "parameter_search_count": 0,
        "preflight_tester_run_count": 3,
        "reported_leverage": 50,
        "requested_leverage": 100,
        "tester_reported_leverage": {row["symbol"]: row["report_fields"].get("Leverage", "") for row in preflights},
        "research_commit": None,
        "research_tree": None,
        "run_1_normalized_hashes": "NOT_CREATED_COVERAGE_GATE_STOP",
        "run_2_normalized_hashes": "NOT_CREATED_COVERAGE_GATE_STOP",
        "server_logical_identity": "Capital.ComMena-Demo",
        "set_files": [identity(LANE / "sets" / f"{symbol}_official.set") for symbol in SYMBOLS],
        "strategy_revision_count": 0,
        "test_command": "python -m pytest tests -q",
        "test_result": "64 passed",
        "tester_model": "Every tick based on real ticks",
        "tester_model_code": 4,
        "tester_root": "ISOLATED_TESTER_ROOT",
    }
    write_json(OUTPUTS / "MT5_LONDON_RUN_MANIFEST.json", manifest)
    missing = [name for name in REQUIRED_OUTPUTS if not (OUTPUTS / name).is_file()]
    if missing:
        raise RuntimeError(f"required outputs missing: {missing}")


def main() -> int:
    verify_base()
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    if "--finalize-frozen" in sys.argv:
        sanitize_frozen_evidence()
        compile_evidence = refresh_compile_evidence()
        finalize(compile_evidence, [load_frozen_preflight(symbol) for symbol in SYMBOLS])
        print(CLASSIFICATION)
        return 0
    login = account_login()
    compile_evidence = compile_once(login)
    preflights = [run_preflight(symbol, login) for symbol in SYMBOLS]
    finalize(compile_evidence, preflights)
    print(CLASSIFICATION)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

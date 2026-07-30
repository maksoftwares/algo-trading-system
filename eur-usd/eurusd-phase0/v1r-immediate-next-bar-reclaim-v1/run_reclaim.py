from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
SOURCE = ROOT / "mt5" / "Experts" / "EurUsdM30RsiBbImmediateReclaimLongV1.mq5"
PRESET = ROOT / "mt5" / "Presets" / "EURUSD_M30_RSI_BB_CLOSE_FADE_LONG_V1R_IMMEDIATE_NEXT_BAR_RECLAIM_V1.set"
OUTPUT = ROOT / "outputs"
RUN_OUTPUT = OUTPUT / "mt5"
LOCKED = OUTPUT / "locked"
EA_NAME = "EurUsdM30RsiBbImmediateReclaimLongV1"
REPORT_BASE = "EURUSD_V1R_IMMEDIATE_RECLAIM_V1"
FROM_DATE = "2022.07.01"
TO_DATE = "2026.07.02"
CANDIDATE_ID = "EURUSD_M30_RSI_BB_CLOSE_FADE_LONG_V1R_IMMEDIATE_NEXT_BAR_RECLAIM_V1"
LOG_INPUTS = {
    "InpStartupLogFileName",
    "InpSignalLogFileName",
    "InpOrderLogFileName",
    "InpStateLogFileName",
    "InpEnvironmentLogFileName",
    "InpExecutionLogFileName",
    "InpTransactionLogFileName",
    "InpManagementLogFileName",
}

sys.path.insert(0, str(REPO / "forex-research" / "scripts"))
import run_forex_mt5_frequency_scout as freq  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path, *, base: Path = REPO) -> dict[str, Any]:
    resolved = path.resolve()
    try:
        display = resolved.relative_to(base.resolve()).as_posix()
    except ValueError:
        display = str(resolved)
    return {"path": display, "bytes": path.stat().st_size, "sha256": sha256(path)}


def read_text_auto(path: Path) -> str:
    data = path.read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    return data.decode("utf-8-sig")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_preset(path: Path = PRESET) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        key, separator, value = raw.partition("=")
        if not separator:
            raise RuntimeError(f"Malformed preset line: {raw}")
        if key in result:
            raise RuntimeError(f"Duplicate preset key: {key}")
        result[key] = value
    return result


def source_input_schema(path: Path = SOURCE) -> list[dict[str, str]]:
    rows = []
    pattern = re.compile(r"^\s*input\s+(.+?)\s+(Inp[A-Za-z0-9_]+)\s*=\s*(.+?)\s*;\s*$")
    for line_number, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        match = pattern.match(raw)
        if not match:
            continue
        rows.append(
            {
                "name": match.group(2),
                "type": match.group(1).strip(),
                "default": match.group(3).strip(),
                "source_line": str(line_number),
            }
        )
    if not rows:
        raise RuntimeError("No MQL5 input declarations found")
    return rows


def validate_input_contract(preset: dict[str, str], schema: list[dict[str, str]]) -> list[dict[str, str]]:
    declared = {row["name"] for row in schema}
    executed = set(preset)
    unknown = sorted(executed - declared)
    missing = sorted(declared - executed)
    if unknown or missing:
        raise RuntimeError(f"Input contract mismatch unknown={unknown} missing={missing}")
    return [{**row, "executed": preset[row["name"]]} for row in schema]


def safe_clean_output() -> None:
    if OUTPUT.exists():
        resolved = OUTPUT.resolve()
        if ROOT.resolve() not in resolved.parents:
            raise RuntimeError(f"Refusing to clean output outside package: {resolved}")
        shutil.rmtree(resolved)
    RUN_OUTPUT.mkdir(parents=True, exist_ok=True)
    LOCKED.mkdir(parents=True, exist_ok=True)


def log_names(preset: dict[str, str]) -> list[str]:
    return [preset[key] for key in sorted(LOG_INPUTS)]


def remove_stale_tester_outputs(tester: Path, preset: dict[str, str]) -> list[str]:
    removed: list[str] = []
    candidates = [
        tester / "Reports" / f"{REPORT_BASE}{suffix}"
        for suffix in (".htm", ".png", "-holding.png", "-mfemae.png", "-hst.png")
    ]
    candidates.append(tester / "Config" / f"{REPORT_BASE}.ini")
    for name in log_names(preset):
        candidates.extend(tester.glob(f"Tester/Agent*/MQL5/Files/{name}"))
    for path in candidates:
        if not path.exists():
            continue
        absolute = path.absolute()
        if tester.absolute() not in absolute.parents:
            raise RuntimeError(f"Refusing to remove tester artifact outside root: {absolute}")
        path.unlink()
        removed.append(str(absolute))
    return removed


def clean_compile(tester: Path, metaeditor: Path) -> tuple[Path, Path, Path, dict[str, Any]]:
    experts = tester / "MQL5" / "Experts"
    experts.mkdir(parents=True, exist_ok=True)
    target_source = experts / SOURCE.name
    target_ex5 = experts / f"{EA_NAME}.ex5"
    shutil.copy2(SOURCE, target_source)
    copied_source_hash = sha256(target_source)
    if copied_source_hash != sha256(SOURCE):
        raise RuntimeError("Copied tester source does not match repository source")
    prior_ex5_existed = target_ex5.exists()
    if prior_ex5_existed:
        target_ex5.unlink()
    if target_ex5.exists():
        raise RuntimeError("Clean compile precondition failed: prior EX5 still exists")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    compile_log = tester / "Logs" / f"compile_{EA_NAME}_{stamp}.log"
    process = subprocess.run(
        [str(metaeditor), f"/compile:{target_source}", f"/log:{compile_log}"],
        cwd=tester,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    if not target_ex5.exists():
        raise RuntimeError(f"MetaEditor did not create {target_ex5}\n{read_text_auto(compile_log)}")
    compile_text = read_text_auto(compile_log)
    if "Result: 0 errors, 0 warnings" not in compile_text:
        raise RuntimeError(f"Compile did not pass zero-error/zero-warning gate\n{compile_text}")
    proof = {
        "prior_ex5_existed": prior_ex5_existed,
        "ex5_absent_before_compile": True,
        "metaeditor_process_returncode": process.returncode,
        "source_hash_before_copy": sha256(SOURCE),
        "source_hash_after_copy": copied_source_hash,
        "ex5_hash_after_compile": sha256(target_ex5),
        "compile_zero_errors_zero_warnings": True,
        "command": [str(metaeditor), f"/compile:{target_source}", f"/log:{compile_log}"],
    }
    return target_source, target_ex5, compile_log, proof


def write_tester_config(tester: Path, preset: dict[str, str]) -> Path:
    lines = [
        "[Common]",
        "Login=1025742",
        "Server=Capital.ComMena-Demo",
        "KeepPrivate=1",
        "NewsEnable=0",
        "",
        "[Tester]",
        f"Expert={EA_NAME}.ex5",
        "Symbol=EURUSD",
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
        "Leverage=50",
        "ExecutionMode=0",
        "OptimizationCriterion=0",
        "Visual=0",
        f"Report=Reports\\{REPORT_BASE}",
        "ReplaceReport=1",
        "ShutdownTerminal=1",
        "UseLocal=1",
        "UseRemote=0",
        "UseCloud=0",
        "",
        "[TesterInputs]",
    ]
    lines.extend(f"{key}={value}" for key, value in preset.items())
    config = tester / "Config" / f"{REPORT_BASE}.ini"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return config


def run_tester(tester: Path, config: Path, timeout_seconds: int) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    process = subprocess.Popen(
        [str(tester / "terminal64.exe"), "/portable", f"/config:{config}"],
        cwd=tester,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        returncode = process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            process.kill()
        raise RuntimeError("Timed out waiting for isolated MT5 Strategy Tester")
    return {
        "returncode": returncode,
        "started_at_utc": started.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "elapsed_seconds": round((datetime.now(timezone.utc) - started).total_seconds(), 2),
        "command": [str(tester / "terminal64.exe"), "/portable", f"/config:{config}"],
    }


def one_tester_log(tester: Path, name: str) -> Path:
    matches = sorted(tester.glob(f"Tester/Agent*/MQL5/Files/{name}"))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one tester log {name}, found {len(matches)}: {matches}")
    return matches[0]


def copy_run_outputs(tester: Path, config: Path, preset: dict[str, str]) -> dict[str, Path]:
    report = tester / "Reports" / f"{REPORT_BASE}.htm"
    if not report.exists():
        raise RuntimeError(f"MT5 report missing: {report}")
    artifacts: dict[str, Path] = {}
    for source in [report, config]:
        destination = RUN_OUTPUT / source.name
        shutil.copy2(source, destination)
        artifacts[source.suffix.lstrip(".") or source.name] = destination
    for suffix in (".png", "-holding.png", "-mfemae.png", "-hst.png"):
        source = tester / "Reports" / f"{REPORT_BASE}{suffix}"
        if source.exists():
            destination = RUN_OUTPUT / source.name
            shutil.copy2(source, destination)
            artifacts[source.name] = destination
    for key in sorted(LOG_INPUTS):
        name = preset[key]
        source = one_tester_log(tester, name)
        destination = RUN_OUTPUT / name
        shutil.copy2(source, destination)
        artifacts[key] = destination
    return artifacts


def html_rows(path: Path) -> list[list[str]]:
    rows = []
    text = read_text_auto(path)
    for match in re.finditer(r"<tr[^>]*>(.*?)</tr>", text, flags=re.I | re.S):
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", match.group(1), flags=re.I | re.S)
        cleaned = [
            html.unescape(re.sub(r"<[^>]+>", "", cell)).strip().replace("\xa0", " ")
            for cell in cells
        ]
        if cleaned:
            rows.append(cleaned)
    return rows


def report_label(rows: list[list[str]], label: str) -> str:
    flat = [cell for row in rows for cell in row]
    for index, value in enumerate(flat):
        if value == label and index + 1 < len(flat):
            return flat[index + 1]
    return ""


def number(value: str) -> float:
    stripped = value.replace(",", "").replace(" ", "").strip()
    return float(stripped) if stripped else 0.0


def deal_costs(report: Path) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for cells in html_rows(report):
        if len(cells) < 13 or cells[2] != "EURUSD" or cells[4] != "out":
            continue
        commission = number(cells[8])
        swap = number(cells[9])
        price_profit = number(cells[10])
        result[cells[1]] = {
            "commission": commission,
            "swap": swap,
            "price_profit": price_profit,
            "net": commission + swap + price_profit,
        }
    return result


def enrich_trades(trades: list[dict[str, Any]], report: Path) -> list[dict[str, Any]]:
    costs = deal_costs(report)
    result = []
    for row in trades:
        deal = str(row["exit_deal"])
        if deal not in costs:
            raise RuntimeError(f"Missing exit-deal cost row for {deal}")
        result.append({**row, **costs[deal]})
    return result


def trade_metrics(trades: list[dict[str, Any]]) -> dict[str, Any]:
    values = [float(row["net"]) for row in trades]
    wins = [value for value in values if value > 0]
    losses = [value for value in values if value < 0]
    gross_profit = sum(wins)
    gross_loss = -sum(losses)
    return {
        "trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "net_usd": round(sum(values), 2),
        "gross_profit_usd": round(gross_profit, 2),
        "gross_loss_usd": round(gross_loss, 2),
        "profit_factor_unrounded": gross_profit / gross_loss,
    }


def parse_include_paths(compile_log: Path) -> list[Path]:
    paths = []
    pattern = re.compile(r"information: including (.+?\.mqh)\s*$", re.I)
    for line in read_text_auto(compile_log).splitlines():
        match = pattern.search(line)
        if match:
            path = Path(match.group(1).strip())
            if path.exists() and path not in paths:
                paths.append(path)
    return paths


def freeze_compile_chain(
    target_source: Path,
    target_ex5: Path,
    compile_log: Path,
    tester: Path,
    metaeditor: Path,
    compile_proof: dict[str, Any],
) -> dict[str, Any]:
    source_dir = LOCKED / "source"
    include_dir = LOCKED / "includes"
    source_dir.mkdir(parents=True, exist_ok=True)
    include_dir.mkdir(parents=True, exist_ok=True)
    frozen_source = source_dir / SOURCE.name
    frozen_ex5 = LOCKED / target_ex5.name
    frozen_compile_log = LOCKED / compile_log.name
    shutil.copy2(target_source, frozen_source)
    shutil.copy2(target_ex5, frozen_ex5)
    shutil.copy2(compile_log, frozen_compile_log)

    frozen_includes = []
    for include in parse_include_paths(compile_log):
        destination = include_dir / f"{sha256(include)[:12]}_{include.name}"
        shutil.copy2(include, destination)
        frozen_includes.append(
            {
                "original_path": str(include.resolve()),
                "frozen": artifact(destination),
            }
        )

    chain = {
        "schema_version": "eurusd_v1r_source_ex5_chain_v1",
        "candidate_id": CANDIDATE_ID,
        "compile_proof": compile_proof,
        "repository_source": artifact(SOURCE),
        "tester_source": artifact(target_source, base=tester),
        "frozen_source": artifact(frozen_source),
        "frozen_ex5": artifact(frozen_ex5),
        "frozen_compile_log": artifact(frozen_compile_log),
        "includes": frozen_includes,
        "compiler": {
            "metaeditor": artifact(metaeditor, base=tester),
            "terminal": artifact(tester / "terminal64.exe", base=tester),
        },
    }
    chain_path = LOCKED / "SOURCE_EX5_CHAIN.json"
    chain_path.write_text(json.dumps(chain, indent=2) + "\n", encoding="utf-8", newline="\n")
    return chain


def environment_values(path: Path) -> dict[str, str]:
    return {row["key"]: row["value"] for row in read_csv(path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the frozen EURUSD V1R immediate next-bar reclaim candidate.")
    parser.add_argument("--tester-root", type=Path, default=Path("C:/MT5A1M5MomentumBacktest"))
    parser.add_argument("--timeout-seconds", type=int, default=600)
    args = parser.parse_args()

    tester = args.tester_root.resolve()
    terminal = tester / "terminal64.exe"
    metaeditor = tester / "MetaEditor64.exe"
    for required in (SOURCE, PRESET, terminal, metaeditor):
        if not required.exists():
            raise FileNotFoundError(required)
    allowed_tester = Path("C:/MT5A1M5MomentumBacktest").resolve()
    if tester != allowed_tester:
        raise RuntimeError("V1R run is restricted to the isolated MT5A1M5MomentumBacktest root")

    preset = load_preset()
    schema = source_input_schema()
    executed_schema = validate_input_contract(preset, schema)
    safe_clean_output()
    stale_removed = remove_stale_tester_outputs(tester, preset)
    target_source, target_ex5, compile_log, compile_proof = clean_compile(tester, metaeditor)
    config = write_tester_config(tester, preset)
    run_proof = run_tester(tester, config, args.timeout_seconds)
    artifacts = copy_run_outputs(tester, config, preset)
    report = RUN_OUTPUT / f"{REPORT_BASE}.htm"
    trades, mt5_metrics = freq.parse_mt5_report(report, "EURUSD")
    enriched = enrich_trades(trades, report)
    trade_fields = list(enriched[0])
    trade_path = RUN_OUTPUT / "EURUSD_V1R_RECLAIM_TRADE_LEDGER.csv"
    write_csv(trade_path, enriched, trade_fields)

    input_schema_path = LOCKED / "COMPILED_INPUT_SCHEMA.json"
    input_schema_payload = {
        "schema_version": "eurusd_v1r_compiled_input_schema_v1",
        "candidate_id": CANDIDATE_ID,
        "declared_input_count": len(executed_schema),
        "unknown_ini_keys": [],
        "missing_ini_keys": [],
        "inputs": executed_schema,
    }
    input_schema_path.write_text(
        json.dumps(input_schema_payload, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    chain = freeze_compile_chain(
        target_source, target_ex5, compile_log, tester, metaeditor, compile_proof
    )
    environment = environment_values(RUN_OUTPUT / preset["InpEnvironmentLogFileName"])
    report_rows = html_rows(report)
    report_leverage = report_label(report_rows, "Leverage:")
    metrics = trade_metrics(enriched)
    summary = {
        "schema_version": "eurusd_v1r_reclaim_exact_mt5_result_v1",
        "candidate_id": CANDIDATE_ID,
        "status": "RECLAIM_MT5_RUN_COMPLETE_NOT_YET_ADJUDICATED",
        "boundary": {
            "strategy_tester_only": True,
            "chart_demo_live_touched": False,
            "reclaim_implemented": True,
            "reclaim_run": True,
            "model": "Model=0 Every tick; may contain generated ticks",
            "from_inclusive": FROM_DATE,
            "to_exclusive": TO_DATE,
        },
        "clean_run": {
            "stale_artifacts_removed": stale_removed,
            "compile": compile_proof,
            "tester": run_proof,
        },
        "input_contract": {
            "declared_input_count": len(executed_schema),
            "unknown_ini_keys": [],
            "missing_ini_keys": [],
            "ini_leverage": "1:50",
            "report_leverage": report_leverage,
        },
        "environment": environment,
        "deal_ledger": metrics,
        "mt5_report_metrics": mt5_metrics,
        "activity": {
            "signals": len(read_csv(RUN_OUTPUT / preset["InpSignalLogFileName"])),
            "decisions": len(read_csv(RUN_OUTPUT / preset["InpOrderLogFileName"])),
            "state_rows": len(read_csv(RUN_OUTPUT / preset["InpStateLogFileName"])),
            "execution_rows": len(read_csv(RUN_OUTPUT / preset["InpExecutionLogFileName"])),
            "transaction_rows": len(read_csv(RUN_OUTPUT / preset["InpTransactionLogFileName"])),
        },
        "source_chain": chain,
        "artifacts": {
            "report": artifact(report),
            "tester_ini": artifact(RUN_OUTPUT / config.name),
            "trade_ledger": artifact(trade_path),
            **{
                key: artifact(path)
                for key, path in artifacts.items()
                if path.exists()
            },
            "compiled_input_schema": artifact(input_schema_path),
        },
    }
    summary_path = RUN_OUTPUT / "EURUSD_V1R_RECLAIM_EXACT_MT5_RESULT.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "status": summary["status"],
                "signals": summary["activity"]["signals"],
                "decisions": summary["activity"]["decisions"],
                **metrics,
                "ini_leverage": "1:50",
                "report_leverage": report_leverage,
                "summary": str(summary_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



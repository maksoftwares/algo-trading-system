"""Execute the review-authorized NP1-G1 clean-root zero-action probe."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

import build_a1_xau_r6_native_spread_provenance_probe as B


ROOT = Path(__file__).resolve().parents[1]
CLEAN_ROOT = Path(r"C:\MT5A1NP1SpreadProvenanceClean")
OLD_ROOT = Path(r"C:\MT5A1M5MomentumBacktest")
MARKER = ".a1_xau_np1_spread_probe_only"
MARKER_BYTES = b"NP1 SPREAD PROBE ONLY\n"
AUTH_SHA256 = "f288535f1944a25a3a92cc62f8f83a692841093aeea56821b27bbe53f1b9985f"
REVIEWED_COMMIT = "9a76c1c81714769bbfcdbdfa4b002def5303d02c"
REVIEWED_TREE = "76d438d6c37fa7fc4ec8c7501a0a3c8099081d9a"
EXPECTED_VERSION = "5.0.0.5833"
LOCK = ROOT / "outputs" / "manifests" / "A1_XAU_R6_NATIVE_SPREAD_PROVENANCE_PROBE_LOCK_V1.json"
RUN_IDS = ("warmup", "probe1", "probe2")
OFFICIAL_NAMES = (
    "h1_bars.tsv", "h4_bars.tsv", "d1_bars.tsv", "bar_spread_interfaces.tsv",
    "ticks_20250618.tsv", "ticks_20250929.tsv", "ticks_20251117.tsv", "ticks_20260414.tsv",
    "assertions.tsv", "order.zero", "deal.zero",
)
WARMUP_NAMES = ("assertions.tsv", "order.zero", "deal.zero")
CommandRunner = Callable[[Sequence[str], Path, int], object]


@dataclass(frozen=True)
class CompileResult:
    source: Path
    ex5: Path
    log: Path
    source_sha256: str
    ex5_sha256: str
    version: str
    command_record: dict[str, object]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command_runner(command: Sequence[str], cwd: Path, timeout: int) -> object:
    return subprocess.run(list(command), cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)


def record(command: Sequence[str], completed: object) -> dict[str, object]:
    stdout = bytes(getattr(completed, "stdout", b"") or b"")
    stderr = bytes(getattr(completed, "stderr", b"") or b"")
    return {
        "command": list(map(str, command)), "exit_code": int(getattr(completed, "returncode", 1)),
        "stdout_base64": base64.b64encode(stdout).decode("ascii"),
        "stderr_base64": base64.b64encode(stderr).decode("ascii"),
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(), "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
    }


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        raise RuntimeError(f"git command failed: {' '.join(args)}")
    return result.stdout.decode("utf-8").strip()


def clean_git_identity() -> dict[str, str]:
    if git("status", "--porcelain=v1", "--untracked-files=all"):
        raise RuntimeError("NP1-G1 evidence requires a clean exact-commit worktree")
    return {"commit": git("rev-parse", "HEAD"), "tree": git("show", "-s", "--format=%T", "HEAD")}


def parse_authorization(path: Path) -> dict[str, str]:
    if not path.is_file() or sha256_file(path) != AUTH_SHA256:
        raise PermissionError("NP1-G1 review artifact hash mismatch")
    text = path.read_text(encoding="utf-8")
    begin, end = "NP1_G1_AUTHORIZATION_BLOCK_BEGIN", "NP1_G1_AUTHORIZATION_BLOCK_END"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise PermissionError("NP1-G1 authorization block mismatch")
    fields = {}
    for raw in text.split(begin, 1)[1].split(end, 1)[0].splitlines():
        if ":" in raw:
            key, value = (part.strip().strip("`") for part in raw.split(":", 1))
            fields[key] = value
    expected = {
        "NP1_G1_AUTHORIZATION_STATUS": "AUTHORIZED", "REVIEW_VERDICT": "PASS",
        "REVIEWED_DIAGNOSTIC_COMMIT": REVIEWED_COMMIT, "REVIEWED_DIAGNOSTIC_TREE": REVIEWED_TREE,
        "CLEAN_MT5_ROOT_AUTHORIZED": "true", "INDEPENDENT_TICK_HISTORY_ACQUISITION_AUTHORIZED": "true",
        "STRATEGY_TESTER_MAX_RUNS": "3", "CANONICAL_NP1C_RESULT_AUTHORIZED": "false",
        "R6_CENSUS_AUTHORIZED": "false", "BROKER_ACTION_AUTHORIZED": "false",
    }
    if fields != expected:
        raise PermissionError("NP1-G1 authorization fields mismatch")
    return fields


def verify_lock() -> dict[str, object]:
    payload = json.loads(LOCK.read_text(encoding="utf-8"))
    for relative, expected in payload.get("implementation_sha256", {}).items():
        path = ROOT / relative
        if not path.is_file() or sha256_file(path) != expected:
            raise RuntimeError(f"NP1-G1 implementation lock mismatch: {relative}")
    return payload


def validate_clean_root(root: Path, *, before_first_invocation: bool) -> tuple[Path, Path]:
    root = root.resolve()
    if root != CLEAN_ROOT.resolve():
        raise RuntimeError("NP1-G1 clean root path mismatch")
    if not (root / MARKER).is_file() or (root / MARKER).read_bytes() != MARKER_BYTES:
        raise RuntimeError("NP1-G1 clean-root marker mismatch")
    terminal, editor = root / "terminal64.exe", root / "MetaEditor64.exe"
    if not terminal.is_file() or not editor.is_file():
        raise RuntimeError("clean root terminal/editor binaries missing")
    if before_first_invocation:
        forbidden = [root / "Bases", root / "bases", root / "history", root / "Tester" / "bases", root / "Tester" / "cache", root / "MQL5" / "Files"]
        forbidden.extend((root / "Tester").glob("Agent-*"))
        present = [str(path) for path in forbidden if path.exists()]
        if present:
            raise RuntimeError(f"clean root contains prior history/cache surface: {present}")
    return terminal, editor


def executable_version(path: Path) -> str:
    literal = str(path).replace("'", "''")
    script = f"(Get-Item -LiteralPath '{literal}').VersionInfo.FileVersion"
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    result = subprocess.run(["powershell", "-NoProfile", "-EncodedCommand", encoded], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=30)
    if result.returncode:
        raise RuntimeError("could not read MetaEditor version")
    return result.stdout.decode("utf-8-sig").strip()


def compile_once(root: Path, editor: Path, *, runner: CommandRunner = command_runner, version_reader: Callable[[Path], str] = executable_version) -> CompileResult:
    experts = root / "MQL5" / "Experts"
    experts.mkdir(parents=True, exist_ok=True)
    source = experts / B.PROBE_NAME
    B.build_probe(source)
    B.verify_source(source)
    ex5, log = source.with_suffix(".ex5"), root / "compile.log"
    if ex5.exists() or log.exists():
        raise RuntimeError("clean-root compile outputs already exist")
    command = [str(editor), f"/compile:{source}", f"/log:{log}"]
    completed = runner(command, root, 180)
    if int(getattr(completed, "returncode", 1)) not in {0, 1} or not ex5.is_file() or not log.is_file():
        raise RuntimeError("single MetaEditor compilation failed")
    raw = log.read_bytes()
    text = raw.decode("utf-16") if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else raw.decode("utf-8-sig", errors="replace")
    if re.search(r"\b0\s+errors?\b", text, re.I) is None or re.search(r"\b0\s+warnings?\b", text, re.I) is None:
        raise RuntimeError("compile log is not zero-error/zero-warning")
    version = version_reader(editor)
    if version != EXPECTED_VERSION:
        raise RuntimeError(f"MetaEditor version mismatch: {version}")
    log.write_text(f"MetaEditor executable version: {version}\n{text.strip()}\n", encoding="utf-8", newline="\n")
    return CompileResult(source, ex5, log, sha256_file(source), sha256_file(ex5), version, record(command, completed))


def render_ini(run_id: str) -> str:
    if run_id not in RUN_IDS:
        raise ValueError(run_id)
    warmup = "true" if run_id == "warmup" else "false"
    prefix = f"np1_g1_{run_id}_"
    return f"""[Tester]
Expert=A1XauR6NativeSpreadProvenanceProbe.ex5
Symbol=XAUUSD
Period=M5
Model=4
ExecutionMode=0
Optimization=0
FromDate=2015.06.01
ToDate=2026.07.01
ForwardMode=0
Deposit=10000
Currency=USD
Leverage=50
Report=Reports/np1_g1_{run_id}
ReplaceReport=1
ShutdownTerminal=1
UseLocal=1
UseRemote=0
UseCloud=0

[TesterInputs]
InpRunId={run_id}
InpWarmup={warmup}
InpH1File={prefix}h1_bars.tsv
InpH4File={prefix}h4_bars.tsv
InpD1File={prefix}d1_bars.tsv
InpInterfacesFile={prefix}bar_spread_interfaces.tsv
InpTicks20250618File={prefix}ticks_20250618.tsv
InpTicks20250929File={prefix}ticks_20250929.tsv
InpTicks20251117File={prefix}ticks_20251117.tsv
InpTicks20260414File={prefix}ticks_20260414.tsv
InpAssertionsFile={prefix}assertions.tsv
InpOrderZeroFile={prefix}order.zero
InpDealZeroFile={prefix}deal.zero
"""


def emitted(run_id: str, name: str) -> str:
    return f"np1_g1_{run_id}_{name}"


def collect(root: Path, run_id: str, ini: Path, destination: Path, not_before_ns: int) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(ini, destination / "tester.ini")
    report = root / "Reports" / f"np1_g1_{run_id}.htm"
    if not report.is_file() or report.stat().st_mtime_ns + 2_000_000_000 < not_before_ns:
        raise RuntimeError(f"missing/stale native report: {run_id}")
    shutil.copyfile(report, destination / "native_report.htm")
    for name in WARMUP_NAMES if run_id == "warmup" else OFFICIAL_NAMES:
        matches = list((root / "Tester").glob(f"Agent-*/MQL5/Files/{emitted(run_id, name)}"))
        if len(matches) != 1:
            raise RuntimeError(f"expected one {run_id} output {name}; found {len(matches)}")
        shutil.copyfile(matches[0], destination / name)


def run_campaign(
    *, root: Path, output: Path, authorization_artifact: Path,
    runner: CommandRunner = command_runner, compile_runner: CommandRunner = command_runner,
    version_reader: Callable[[Path], str] = executable_version, timeout: int = 7200,
) -> dict[str, object]:
    identity = clean_git_identity()
    parse_authorization(authorization_artifact)
    verify_lock()
    terminal, editor = validate_clean_root(root, before_first_invocation=True)
    ledger = root / ".np1_g1_invocation_ledger.json"
    if ledger.exists() or output.exists():
        raise RuntimeError("NP1-G1 fixed ledger/output already exists; retry forbidden")
    compiled = compile_once(root, editor, runner=compile_runner, version_reader=version_reader)
    output.mkdir(parents=True)
    compiled_dir = output / "compiled"
    compiled_dir.mkdir()
    shutil.copyfile(compiled.source, compiled_dir / B.PROBE_NAME)
    shutil.copyfile(compiled.ex5, compiled_dir / compiled.ex5.name)
    shutil.copyfile(compiled.log, compiled_dir / "compile.log")
    B.build_probe(compiled_dir / B.PROBE_NAME, compiled_dir / "source_manifest.json")
    commands = [compiled.command_record]
    ledger_data = {"compilations": 1, "tester_runs": []}
    ledger.write_text(json.dumps(ledger_data, sort_keys=True) + "\n", encoding="utf-8")
    configs = root / "Config"
    configs.mkdir(exist_ok=True)
    expected_ex5 = compiled.ex5_sha256
    for run_id in RUN_IDS:
        if len(ledger_data["tester_runs"]) >= 3:
            raise RuntimeError("fourth Strategy Tester invocation forbidden")
        if sha256_file(compiled.ex5) != expected_ex5:
            raise RuntimeError("EX5 drift before Strategy Tester invocation")
        ini = configs / f"np1_g1_{run_id}.ini"
        ini.write_text(render_ini(run_id), encoding="utf-8", newline="\n")
        command = [str(terminal), "/portable", f"/config:{ini}"]
        started = time.time_ns()
        completed = runner(command, root, timeout)
        ledger_data["tester_runs"].append(run_id)
        ledger.write_text(json.dumps(ledger_data, sort_keys=True) + "\n", encoding="utf-8")
        commands.append(record(command, completed))
        if int(getattr(completed, "returncode", 1)) != 0:
            raise RuntimeError(f"Strategy Tester {run_id} failed; retry forbidden")
        collect(root, run_id, ini, output / "runs" / run_id, started)
    if ledger_data != {"compilations": 1, "tester_runs": list(RUN_IDS)} or sha256_file(compiled.ex5) != expected_ex5:
        raise RuntimeError("invocation budget or EX5 identity mismatch")
    attestation = {
        "schema_version": "a1_xau_r6_np1_g1_campaign_attestation_v1", "git_identity": identity,
        "authorization_sha256": AUTH_SHA256, "reviewed_commit": REVIEWED_COMMIT, "reviewed_tree": REVIEWED_TREE,
        "clean_root": str(root.resolve()), "prior_root_executed": False, "history_cache_copied": False,
        "metaeditor_compilations": 1, "strategy_tester_runs": list(RUN_IDS),
        "ex5_sha256": expected_ex5, "commands": commands,
    }
    source_manifest = compiled_dir / "source_manifest.json"
    source_payload = json.loads(source_manifest.read_text(encoding="utf-8"))
    source_payload["campaign_attestation"] = attestation
    source_manifest.write_text(json.dumps(source_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    import analyze_a1_xau_r6_native_spread_provenance_probe as A
    return A.build_packet(output)


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--authorization-artifact", type=Path, required=True)
    args = parser.parse_args()
    result = run_campaign(root=args.root, output=args.output, authorization_artifact=args.authorization_artifact)
    print(json.dumps({"status": result["status"], "flags": result["flags"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

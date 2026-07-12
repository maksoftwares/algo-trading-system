"""Compile-only NP1-B runner and review-gated future NP1-C executor."""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

import build_a1_xau_r6_market_only_native_parity_oracle as B


EXPECTED_BUILD = 5833
NP1_C_AUTHORIZATION = "NP1-C_EXACT_COMMIT_REVIEWED_AUTHORIZATION"
OUTPUT_NAMES = (
    "native_router_rows.tsv", "native_h1_bars.tsv", "native_h4_bars.tsv", "native_d1_bars.tsv",
    "native_contract.tsv", "native_ordercalcprofit.tsv", "native_assertions.tsv", "order.zero", "deal.zero",
)
CommandRunner = Callable[[Sequence[str], Path, int], object]


@dataclass(frozen=True)
class CompileResult:
    source: Path
    ex5: Path
    log: Path
    source_sha256: str
    ex5_sha256: str
    returncode: int
    metaeditor_version: str
    command: tuple[str, ...]
    stdout_sha256: str
    stderr_sha256: str
    stdout_base64: str
    stderr_base64: str


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_compile_log(path: Path) -> str:
    data = path.read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    return data.decode("utf-8-sig", errors="replace")


def default_command_runner(command: Sequence[str], cwd: Path, timeout_seconds: int) -> object:
    return subprocess.run(
        list(command), cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=timeout_seconds, check=False,
    )


def default_metaeditor_version_reader(path: Path) -> str:
    literal = str(path).replace("'", "''")
    script = f"(Get-Item -LiteralPath '{literal}').VersionInfo.FileVersion"
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    command = ["powershell", "-NoProfile", "-EncodedCommand", encoded]
    completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=30)
    if completed.returncode != 0:
        raise RuntimeError("could not read MetaEditor executable version")
    return completed.stdout.decode("utf-8-sig", errors="replace").strip()


def validate_metaeditor(path: Path) -> Path:
    path = path.resolve()
    if not path.is_file() or path.name.lower() != "metaeditor64.exe":
        raise RuntimeError(f"required MetaEditor64.exe is missing: {path}")
    return path


def compile_only_safety_check(
    *,
    metaeditor: Path,
    workspace: Path,
    timeout_seconds: int = 120,
    command_runner: CommandRunner = default_command_runner,
    version_reader: Callable[[Path], str] = default_metaeditor_version_reader,
) -> CompileResult:
    """Build and compile only in an explicit temporary/test workspace."""
    metaeditor = validate_metaeditor(metaeditor)
    workspace = workspace.resolve()
    if not any(token in workspace.name.lower() for token in ("tmp", "temp", "test", "compile")):
        raise RuntimeError("compile-only workspace name must identify a temporary/test/compile workspace")
    workspace.mkdir(parents=True, exist_ok=True)
    source = workspace / B.ORACLE_NAME
    equivalence = workspace / "source_equivalence.json"
    B.build_oracle(source, equivalence)
    B.verify_generated_source(source)
    ex5 = source.with_suffix(".ex5")
    log = workspace / "compile_A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY.log"
    ex5.unlink(missing_ok=True)
    log.unlink(missing_ok=True)
    command = [str(metaeditor), f"/compile:{source}", f"/log:{log}"]
    completed = command_runner(command, workspace, timeout_seconds)
    returncode = int(getattr(completed, "returncode", 1))
    if returncode not in {0, 1}:
        raise RuntimeError(f"MetaEditor compile failed with exit code {returncode}")
    if not ex5.is_file() or not log.is_file():
        raise RuntimeError("compile-only check did not produce both EX5 and compile log")
    text = read_compile_log(log)
    if re.search(r"\b0\s+errors?\b", text, re.IGNORECASE) is None:
        raise RuntimeError("compile log does not prove zero errors")
    if re.search(r"\b0\s+warnings?\b", text, re.IGNORECASE) is None:
        raise RuntimeError("compile log does not prove zero warnings")
    builds = {int(value) for value in re.findall(r"\bbuild\s+(\d{4,6})\b", text, re.IGNORECASE)}
    if builds and builds != {EXPECTED_BUILD}:
        raise RuntimeError(f"compile log build mismatch: {sorted(builds)}")
    version = version_reader(metaeditor)
    if version != "5.0.0.5833":
        raise RuntimeError(f"MetaEditor executable version must be 5.0.0.5833; found {version!r}")
    normalized_log = f"MetaEditor executable version: {version}\n{text.strip()}\n"
    log.write_text(normalized_log, encoding="utf-8", newline="\n")
    stdout = bytes(getattr(completed, "stdout", b"") or b"")
    stderr = bytes(getattr(completed, "stderr", b"") or b"")
    return CompileResult(
        source, ex5, log, sha256_file(source), sha256_file(ex5), returncode, version,
        tuple(command), sha256_bytes(stdout), sha256_bytes(stderr),
        base64.b64encode(stdout).decode("ascii"), base64.b64encode(stderr).decode("ascii"),
    )


def render_tester_ini(*, run_id: str, report_relative: str) -> str:
    if run_id not in {"run1", "run2"}:
        raise ValueError("run_id must be run1 or run2")
    return f"""[Tester]
Expert=A1XauR6MarketOnlyNativeParityOracle.ex5
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
Report={report_relative}
ReplaceReport=1
ShutdownTerminal=1
UseLocal=1
UseRemote=0
UseCloud=0

[TesterInputs]
InpRunId={run_id}
InpRouterRowsFileName=np1_{run_id}_native_router_rows.tsv
InpH1BarsFileName=np1_{run_id}_native_h1_bars.tsv
InpH4BarsFileName=np1_{run_id}_native_h4_bars.tsv
InpD1BarsFileName=np1_{run_id}_native_d1_bars.tsv
InpContractFileName=np1_{run_id}_native_contract.tsv
InpOrderCalcProfitFileName=np1_{run_id}_native_ordercalcprofit.tsv
InpAssertionsFileName=np1_{run_id}_native_assertions.tsv
InpOrderZeroFileName=np1_{run_id}_order.zero
InpDealZeroFileName=np1_{run_id}_deal.zero
"""


def parse_ini_exact(text: str) -> dict[str, dict[str, str]]:
    sections: dict[str, dict[str, str]] = {}
    current: dict[str, str] | None = None
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith((";", "#")):
            continue
        if line.startswith("[") and line.endswith("]"):
            name = line[1:-1]
            if not name or name in sections:
                raise RuntimeError(f"duplicate/invalid INI section at line {number}")
            current = sections.setdefault(name, {})
            continue
        if current is None or "=" not in line:
            raise RuntimeError(f"invalid INI line {number}")
        key, value = line.split("=", 1)
        if not key or key in current:
            raise RuntimeError(f"duplicate/invalid INI key {key!r} at line {number}")
        current[key] = value
    return sections


def assert_tester_ini_contract(text: str, *, run_id: str | None = None) -> None:
    if run_id is None:
        parsed = parse_ini_exact(text)
        run_id = parsed.get("TesterInputs", {}).get("InpRunId", "")
    expected = parse_ini_exact(render_tester_ini(run_id=run_id, report_relative=f"Reports/np1_{run_id}"))
    actual = parse_ini_exact(text)
    if actual != expected:
        raise RuntimeError("tester INI exact key/value contract mismatch")
    forbidden = {"Login", "Server", "Profile", "Chart", "Visual"}
    found = sorted(forbidden & set().union(*(set(values) for values in actual.values())))
    if found:
        raise RuntimeError(f"tester INI contains prohibited runtime setting(s): {found}")


def validate_tester_sandbox(path: Path) -> Path:
    path = path.resolve()
    marker = path / ".a1_xau_np1_tester_only"
    terminal = path / "terminal64.exe"
    if not marker.is_file() or marker.read_text(encoding="utf-8") != "NP1 TESTER ONLY\n":
        raise RuntimeError("NP1 tester-only marker is missing or invalid")
    if not terminal.is_file():
        raise RuntimeError("isolated terminal64.exe is missing")
    return terminal


def emitted_names(run_id: str) -> dict[str, str]:
    if run_id not in {"run1", "run2"}:
        raise ValueError(run_id)
    return {name: f"np1_{run_id}_{name}" for name in OUTPUT_NAMES}


def clear_emitted_outputs(tester_sandbox: Path, run_id: str) -> None:
    for files_dir in (tester_sandbox / "Tester").glob("Agent-*/MQL5/Files"):
        for filename in emitted_names(run_id).values():
            (files_dir / filename).unlink(missing_ok=True)
    (tester_sandbox / "Reports" / f"np1_{run_id}.htm").unlink(missing_ok=True)


def collect_run_outputs(
    tester_sandbox: Path, run_id: str, ini: Path, run_dir: Path, *, not_before_ns: int | None = None
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ini, run_dir / "tester.ini")
    report = tester_sandbox / "Reports" / f"np1_{run_id}.htm"
    if not report.is_file():
        raise RuntimeError(f"Strategy Tester report missing for {run_id}: {report}")
    if not_before_ns is not None and report.stat().st_mtime_ns + 2_000_000_000 < not_before_ns:
        raise RuntimeError(f"Strategy Tester report is stale for {run_id}: {report}")
    shutil.copyfile(report, run_dir / "native_report.htm")
    for destination_name, emitted_name in emitted_names(run_id).items():
        matches = list((tester_sandbox / "Tester").glob(f"Agent-*/MQL5/Files/{emitted_name}"))
        if len(matches) != 1:
            raise RuntimeError(f"expected exactly one isolated {run_id} output {emitted_name}; found {len(matches)}")
        shutil.copyfile(matches[0], run_dir / destination_name)


def _command_record(command: Sequence[str], completed: object) -> dict[str, object]:
    stdout = bytes(getattr(completed, "stdout", b"") or b"")
    stderr = bytes(getattr(completed, "stderr", b"") or b"")
    return {
        "command": [str(value) for value in command],
        "exit_code": int(getattr(completed, "returncode", 1)),
        "stdout_base64": base64.b64encode(stdout).decode("ascii"),
        "stderr_base64": base64.b64encode(stderr).decode("ascii"),
        "stdout_sha256": sha256_bytes(stdout),
        "stderr_sha256": sha256_bytes(stderr),
    }


def _git(*args: str) -> str:
    completed = subprocess.run(["git", *args], cwd=B.ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"git attestation command failed: {' '.join(args)}")
    return completed.stdout.decode("utf-8", errors="strict").strip()


def capture_clean_git_identity() -> dict[str, str]:
    status = _git("status", "--porcelain=v1", "--untracked-files=all")
    if status:
        raise RuntimeError("exact-commit attestation requires a clean worktree before evidence generation")
    return {"git_head": _git("rev-parse", "HEAD"), "git_tree": _git("rev-parse", "HEAD^{tree}"), "git_status_porcelain": ""}


def parse_np1_c_review_authorization(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    begin, end = "NP1_C_AUTHORIZATION_BLOCK_BEGIN", "NP1_C_AUTHORIZATION_BLOCK_END"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise PermissionError("review artifact must contain exactly one NP1-C authorization block")
    block = text.split(begin, 1)[1].split(end, 1)[0]
    fields: dict[str, str] = {}
    for raw in block.splitlines():
        line = raw.strip().strip("`")
        if not line:
            continue
        if ":" not in line:
            raise PermissionError("NP1-C authorization block contains an invalid line")
        key, value = (part.strip() for part in line.split(":", 1))
        if key in fields:
            raise PermissionError(f"duplicate NP1-C authorization field: {key}")
        fields[key] = value
    required = {
        "NP1_C_AUTHORIZATION_STATUS", "REVIEW_VERDICT", "REVIEWED_GENERATOR_COMMIT", "REVIEWED_GENERATOR_TREE"
    }
    if set(fields) != required:
        raise PermissionError("NP1-C authorization block field set mismatch")
    if fields["NP1_C_AUTHORIZATION_STATUS"] != "AUTHORIZED" or fields["REVIEW_VERDICT"] != "PASS":
        raise PermissionError("review artifact does not authorize NP1-C with a PASS verdict")
    if re.search(r"NP1-B4\s*:\s*(?:FAIL|NO-GO)|NP1-C\s*:\s*NOT AUTHORIZED", text, re.IGNORECASE):
        raise PermissionError("review artifact contains a rejecting B4/NP1-C verdict")
    if re.fullmatch(r"[0-9a-f]{40}", fields["REVIEWED_GENERATOR_COMMIT"]) is None or re.fullmatch(r"[0-9a-f]{40}", fields["REVIEWED_GENERATOR_TREE"]) is None:
        raise PermissionError("review artifact generator commit/tree is malformed")
    return fields


def build_campaign_attestation(
    output_dir: Path, compiled: CompileResult, commands: list[dict[str, object]], git_identity: dict[str, str],
    review_authority: dict[str, str], finalizer_commands: list[dict[str, object]],
) -> dict[str, object]:
    if _git("rev-parse", "HEAD") != git_identity["git_head"] or _git("rev-parse", "HEAD^{tree}") != git_identity["git_tree"]:
        raise RuntimeError("exact commit/tree changed during evidence generation")
    tracked = subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], cwd=B.ROOT, check=False)
    if tracked.returncode != 0:
        raise RuntimeError("tracked files changed during evidence generation")
    artifact_hashes = {
        path.relative_to(output_dir).as_posix(): sha256_file(path)
        for path in sorted(output_dir.rglob("*")) if path.is_file()
        and path.name not in {"test_validation.md", "manifest.json", "manifest.sha256"}
        and path.parent.name != "parity"
        and not path.name.startswith("A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY_EXACT_")
    }
    return {
        "schema_version": "a1_xau_np1_exact_commit_attestation_v1",
        **git_identity,
        "os": platform.platform(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "dependency_versions": {
            "python_implementation": platform.python_implementation(),
            "pytest": importlib.metadata.version("pytest"),
            "third_party_runtime_dependencies": {},
        },
        "mt5_terminal_build": EXPECTED_BUILD,
        "metaeditor_version": compiled.metaeditor_version,
        "same_ex5_sha256_run1_run2": compiled.ex5_sha256,
        "commands": [
            {
                "command": list(compiled.command), "exit_code": compiled.returncode,
                "stdout_base64": compiled.stdout_base64, "stderr_base64": compiled.stderr_base64,
                "stdout_sha256": compiled.stdout_sha256, "stderr_sha256": compiled.stderr_sha256,
            },
            *commands,
            *finalizer_commands,
        ],
        "artifact_sha256": artifact_hashes,
        "review_authority": review_authority,
        "environment": {
            "cwd": str(B.ROOT), "timezone": os.environ.get("TZ", "system-local"),
            "account_login": 1025742, "server": "Capital.ComMena-Demo",
            "currency": "USD", "leverage": "1:50", "symbol": "XAUUSD",
        },
    }


def run_historical_evidence_campaign(
    *,
    authorization: str,
    tester_sandbox: Path,
    metaeditor: Path,
    compile_workspace: Path,
    output_dir: Path,
    timeout_seconds: int = 7200,
    command_runner: CommandRunner = default_command_runner,
    compile_command_runner: CommandRunner = default_command_runner,
    metaeditor_version_reader: Callable[[Path], str] = default_metaeditor_version_reader,
    verification_command_runner: CommandRunner = default_command_runner,
    review_artifact: Path | None = None,
    review_sha256: str | None = None,
    reviewed_generator_commit: str | None = None,
    reviewed_generator_tree: str | None = None,
) -> list[Path]:
    """Future NP1-C hook. It is fail-closed unless exact review authorization is supplied."""
    if authorization != NP1_C_AUTHORIZATION:
        raise PermissionError("real historical Strategy Tester evidence remains prohibited before NP1-C review")
    git_identity = capture_clean_git_identity()
    review_path = review_artifact.resolve() if review_artifact is not None else None
    parsed_review = parse_np1_c_review_authorization(review_path) if review_path is not None and review_path.is_file() else {}
    review_authority = {
        "controlling_review_artifact": review_path.name if review_path is not None else "",
        "controlling_review_sha256": review_sha256 or "",
        "reviewed_generator_commit": reviewed_generator_commit or "",
        "reviewed_generator_tree": reviewed_generator_tree or "",
        "authorization_status": parsed_review.get("NP1_C_AUTHORIZATION_STATUS", ""),
        "review_verdict": parsed_review.get("REVIEW_VERDICT", ""),
    }
    if (
        re.fullmatch(r"A1_XAU_NP1B4_[A-Z0-9_]+\.md", review_authority["controlling_review_artifact"]) is None
        or review_path is None or not review_path.is_file()
        or re.fullmatch(r"[0-9a-f]{64}", review_authority["controlling_review_sha256"]) is None
        or sha256_file(review_path) != review_authority["controlling_review_sha256"]
        or review_authority["reviewed_generator_commit"] != git_identity["git_head"]
        or review_authority["reviewed_generator_tree"] != git_identity["git_tree"]
        or parsed_review.get("REVIEWED_GENERATOR_COMMIT") != git_identity["git_head"]
        or parsed_review.get("REVIEWED_GENERATOR_TREE") != git_identity["git_tree"]
        or review_authority["authorization_status"] != "AUTHORIZED"
        or review_authority["review_verdict"] != "PASS"
    ):
        raise PermissionError("NP1-C requires the exact reviewed NP1-B3 artifact, SHA256, generator commit, and tree")
    terminal = validate_tester_sandbox(tester_sandbox)
    compiled = compile_only_safety_check(
        metaeditor=metaeditor, workspace=compile_workspace, command_runner=compile_command_runner,
        version_reader=metaeditor_version_reader,
    )
    compiled_ex5 = compiled.ex5
    experts = tester_sandbox / "MQL5" / "Experts"
    experts.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(compiled_ex5, experts / compiled_ex5.name)
    configs = tester_sandbox / "Config"
    configs.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=False)
    compiled_dir = output_dir / "compiled"
    compiled_dir.mkdir()
    shutil.copyfile(compiled.source, compiled_dir / B.ORACLE_NAME)
    shutil.copyfile(compiled.ex5, compiled_dir / compiled.ex5.name)
    shutil.copyfile(compiled.log, compiled_dir / "compile_A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY.log")
    B.build_oracle(compiled_dir / B.ORACLE_NAME, compiled_dir / "source_equivalence.json")
    produced: list[Path] = []
    command_records: list[dict[str, object]] = []
    for run_id in ("run1", "run2"):
        run_dir = output_dir / "runs" / run_id
        ini = configs / f"np1_{run_id}.ini"
        text = render_tester_ini(run_id=run_id, report_relative=f"Reports/np1_{run_id}")
        assert_tester_ini_contract(text, run_id=run_id)
        ini.write_text(text, encoding="utf-8", newline="\n")
        clear_emitted_outputs(tester_sandbox, run_id)
        command = [str(terminal), "/portable", f"/config:{ini}"]
        not_before_ns = time.time_ns()
        completed = command_runner(command, tester_sandbox, timeout_seconds)
        command_records.append(_command_record(command, completed))
        if int(getattr(completed, "returncode", 1)) != 0:
            raise RuntimeError(f"Strategy Tester {run_id} failed")
        collect_run_outputs(tester_sandbox, run_id, ini, run_dir, not_before_ns=not_before_ns)
        produced.append(run_dir)
    if sha256_file(compiled_dir / compiled.ex5.name) != compiled.ex5_sha256:
        raise RuntimeError("compiled EX5 changed during evidence assembly")
    import verify_a1_xau_r6_market_only_native_parity as verifier
    attestation_path = compile_workspace / "np1_campaign_attestation.json"
    finalizer_command = [
        sys.executable, str(Path(verifier.__file__).resolve()), str(output_dir), "--finalize",
        "--attestation-json", str(attestation_path), "--quiet",
    ]
    verifier_command = [sys.executable, str(Path(verifier.__file__).resolve()), str(output_dir), "--quiet"]
    empty = sha256_bytes(b"")
    finalizer_commands = [
        {"command": command, "exit_code": 0, "stdout_base64": "", "stderr_base64": "", "stdout_sha256": empty, "stderr_sha256": empty}
        for command in (finalizer_command, verifier_command)
    ]
    attestation = build_campaign_attestation(
        output_dir, compiled, command_records, git_identity, review_authority, finalizer_commands
    )
    verifier.finalize_evidence_directory(output_dir, attestation=attestation)
    attestation["artifact_sha256"] = verifier.attested_artifact_hashes(output_dir)
    attestation_path.write_text(json.dumps(attestation, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    for command in (finalizer_command, verifier_command):
        completed = verification_command_runner(command, B.ROOT, timeout_seconds)
        record = _command_record(command, completed)
        if record["exit_code"] != 0 or record["stdout_base64"] or record["stderr_base64"]:
            raise RuntimeError(f"finalizer/read-only verifier command failed or emitted unexpected output: {command}")
    payload = json.loads((output_dir / "A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY_EXACT_20260712.json").read_text(encoding="utf-8"))
    if payload.get("status") not in {
        "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_FAIL",
        "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_PASS",
    }:
        raise RuntimeError(f"NP1 evidence assembly failed: {payload.get('status')}: {payload.get('errors')}")
    return produced


def _main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metaeditor", type=Path)
    parser.add_argument("--compile-workspace", type=Path)
    parser.add_argument("--historical-evidence", action="store_true")
    parser.add_argument("--authorization")
    parser.add_argument("--tester-sandbox", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--review-artifact", type=Path)
    parser.add_argument("--review-sha256")
    parser.add_argument("--reviewed-generator-commit")
    parser.add_argument("--reviewed-generator-tree")
    args = parser.parse_args(argv)
    if args.historical_evidence:
        required = {
            "--metaeditor": args.metaeditor, "--compile-workspace": args.compile_workspace,
            "--tester-sandbox": args.tester_sandbox, "--output-dir": args.output_dir,
            "--review-artifact": args.review_artifact, "--review-sha256": args.review_sha256,
            "--reviewed-generator-commit": args.reviewed_generator_commit,
            "--reviewed-generator-tree": args.reviewed_generator_tree,
        }
        missing = [name for name, value in required.items() if value is None]
        if missing:
            raise SystemExit(f"historical evidence command missing required arguments: {missing}")
        run_historical_evidence_campaign(
            authorization=args.authorization or "", tester_sandbox=args.tester_sandbox,
            metaeditor=args.metaeditor, compile_workspace=args.compile_workspace, output_dir=args.output_dir,
            review_artifact=args.review_artifact, review_sha256=args.review_sha256,
            reviewed_generator_commit=args.reviewed_generator_commit,
            reviewed_generator_tree=args.reviewed_generator_tree,
        )
        return 0
    if args.metaeditor is None or args.compile_workspace is None:
        raise SystemExit("--metaeditor and --compile-workspace are required for NP1-B compile-only validation")
    result = compile_only_safety_check(metaeditor=args.metaeditor, workspace=args.compile_workspace)
    print(f"Compile-only PASS: {result.ex5_sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

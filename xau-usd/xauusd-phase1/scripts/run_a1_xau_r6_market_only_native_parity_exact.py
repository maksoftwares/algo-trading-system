"""Compile-only NP1-B runner and review-gated future NP1-C executor."""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

import build_a1_xau_r6_market_only_native_parity_oracle as B


EXPECTED_BUILD = 5833
NP1_C_AUTHORIZATION = "NP1-C_EXACT_COMMIT_REVIEWED_AUTHORIZATION"
CommandRunner = Callable[[Sequence[str], Path, int], object]


@dataclass(frozen=True)
class CompileResult:
    source: Path
    ex5: Path
    log: Path
    source_sha256: str
    ex5_sha256: str
    returncode: int


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    return CompileResult(source, ex5, log, sha256_file(source), sha256_file(ex5), returncode)


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
InpRouterRowsFileName=native_router_rows.tsv
InpH1BarsFileName=native_h1_bars.tsv
InpH4BarsFileName=native_h4_bars.tsv
InpD1BarsFileName=native_d1_bars.tsv
InpContractFileName=native_contract.tsv
InpOrderCalcProfitFileName=native_ordercalcprofit.tsv
InpAssertionsFileName=native_assertions.tsv
InpOrderZeroFileName=order.zero
InpDealZeroFileName=deal.zero
"""


def assert_tester_ini_contract(text: str) -> None:
    required = (
        "Expert=A1XauR6MarketOnlyNativeParityOracle.ex5", "Symbol=XAUUSD", "Period=M5",
        "Model=4", "Optimization=0", "FromDate=2015.06.01", "ToDate=2026.07.01",
        "Deposit=10000", "Currency=USD", "Leverage=50", "UseRemote=0", "UseCloud=0",
    )
    missing = [item for item in required if item not in text]
    if missing:
        raise RuntimeError(f"tester INI contract missing: {missing}")
    forbidden = ("Login=", "Server=", "Profile=", "Chart=", "Visual=1")
    found = [item for item in forbidden if item in text]
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


def run_historical_evidence_campaign(
    *,
    authorization: str,
    tester_sandbox: Path,
    compiled_ex5: Path,
    output_dir: Path,
    timeout_seconds: int = 7200,
    command_runner: CommandRunner = default_command_runner,
) -> list[Path]:
    """Future NP1-C hook. It is fail-closed unless exact review authorization is supplied."""
    if authorization != NP1_C_AUTHORIZATION:
        raise PermissionError("real historical Strategy Tester evidence remains prohibited before NP1-C review")
    terminal = validate_tester_sandbox(tester_sandbox)
    if not compiled_ex5.is_file():
        raise FileNotFoundError(compiled_ex5)
    experts = tester_sandbox / "MQL5" / "Experts"
    experts.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(compiled_ex5, experts / compiled_ex5.name)
    configs = tester_sandbox / "Config"
    configs.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=False)
    produced: list[Path] = []
    for run_id in ("run1", "run2"):
        run_dir = output_dir / "runs" / run_id
        run_dir.mkdir(parents=True)
        ini = configs / f"np1_{run_id}.ini"
        text = render_tester_ini(run_id=run_id, report_relative=f"Reports/np1_{run_id}")
        assert_tester_ini_contract(text)
        ini.write_text(text, encoding="utf-8", newline="\n")
        completed = command_runner([str(terminal), "/portable", f"/config:{ini}"], tester_sandbox, timeout_seconds)
        if int(getattr(completed, "returncode", 1)) != 0:
            raise RuntimeError(f"Strategy Tester {run_id} failed")
        produced.append(ini)
    return produced


def _main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metaeditor", type=Path)
    parser.add_argument("--compile-workspace", type=Path)
    parser.add_argument("--historical-evidence", action="store_true")
    args = parser.parse_args(argv)
    if args.historical_evidence:
        raise SystemExit("NP1-C historical evidence execution is not authorized in NP1-B")
    if args.metaeditor is None or args.compile_workspace is None:
        raise SystemExit("--metaeditor and --compile-workspace are required for NP1-B compile-only validation")
    result = compile_only_safety_check(metaeditor=args.metaeditor, workspace=args.compile_workspace)
    print(f"Compile-only PASS: {result.ex5_sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

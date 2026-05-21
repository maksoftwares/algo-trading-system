from __future__ import annotations

import argparse
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


EXPERT_NAME = "Phase1DryRunShell.mq5"
COMPILE_LOG_NAME = "compile_Phase1DryRunShell.log"


@dataclass(frozen=True)
class DeployOutput:
    deployed_count: int
    compile_status: str
    compile_log: Path | None
    destinations: tuple[Path, ...]


def deploy_phase1_mt5(
    root: Path,
    portable_root: Path,
    data_mql5_root: Path | None = None,
    compile_shell: bool = False,
    compile_timeout_seconds: int = 60,
    compile_log: Path | None = None,
) -> DeployOutput:
    root = root.resolve()
    portable_root = portable_root.resolve()
    portable_mql5_root = portable_root / "MQL5"
    destinations = [portable_mql5_root]
    if data_mql5_root is not None:
        destinations.append(data_mql5_root.resolve())

    deployed_count = 0
    for destination in destinations:
        deployed_count += _copy_phase1_mql5_tree(root, destination)

    deployed_count += _copy_configs(root, portable_root / "Config")

    resolved_compile_log: Path | None = None
    compile_status = "SKIPPED"
    if compile_shell:
        resolved_compile_log = (compile_log or portable_root / COMPILE_LOG_NAME).resolve()
        compile_status = _compile_with_metaeditor(
            portable_root=portable_root,
            expert_path=portable_mql5_root / "Experts" / EXPERT_NAME,
            compile_log=resolved_compile_log,
            timeout_seconds=compile_timeout_seconds,
        )

    return DeployOutput(
        deployed_count=deployed_count,
        compile_status=compile_status,
        compile_log=resolved_compile_log,
        destinations=tuple(destinations),
    )


def _copy_phase1_mql5_tree(root: Path, destination_mql5_root: Path) -> int:
    copied = 0
    copied += _copy_one(root / "mt5" / "Experts" / EXPERT_NAME, destination_mql5_root / "Experts" / EXPERT_NAME)
    for include in sorted((root / "mt5" / "Include" / "Phase1").glob("*.mqh")):
        copied += _copy_one(include, destination_mql5_root / "Include" / "Phase1" / include.name)
    for preset in sorted((root / "mt5" / "Presets").glob("*.set")):
        copied += _copy_one(preset, destination_mql5_root / "Presets" / preset.name)
    return copied


def _copy_configs(root: Path, destination_config_root: Path) -> int:
    copied = 0
    for config in sorted((root / "mt5" / "Config").glob("*.ini")):
        copied += _copy_one(config, destination_config_root / config.name)
    return copied


def _copy_one(source: Path, destination: Path) -> int:
    if not source.exists():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return 1


def _compile_with_metaeditor(
    portable_root: Path,
    expert_path: Path,
    compile_log: Path,
    timeout_seconds: int,
) -> str:
    metaeditor = portable_root / "MetaEditor64.exe"
    if not metaeditor.exists():
        raise FileNotFoundError(metaeditor)
    if not expert_path.exists():
        raise FileNotFoundError(expert_path)

    if compile_log.exists():
        compile_log.unlink()
    compile_log.parent.mkdir(parents=True, exist_ok=True)

    completed = subprocess.run(
        [
            str(metaeditor),
            "/portable",
            f"/compile:{expert_path}",
            f"/log:{compile_log}",
        ],
        check=False,
        timeout=timeout_seconds,
    )
    if completed.returncode not in (0, 1):
        return f"PROCESS_RETURNED_{completed.returncode}"
    if not compile_log.exists():
        return "LOG_MISSING"

    text = _read_compile_log(compile_log)
    if "Result: 0 errors, 0 warnings" in text or "Result: 0 errors, 0 warning" in text:
        return "PASS"
    if "error" in text.lower():
        return "FAIL"
    return "UNKNOWN"


def _read_compile_log(path: Path) -> str:
    payload = path.read_bytes()
    for encoding in ("utf-16", "utf-8-sig", "cp1252"):
        try:
            text = payload.decode(encoding)
        except UnicodeError:
            continue
        if "Result:" in text:
            return text
    return payload.decode("utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deploy and optionally compile the Phase 1 MT5 dry-run shell.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Phase 1 workspace root.",
    )
    parser.add_argument(
        "--portable-root",
        type=Path,
        default=Path("C:/MT5PortableGoldMission"),
        help="MT5 portable root containing terminal64.exe and MQL5.",
    )
    parser.add_argument(
        "--data-mql5-root",
        type=Path,
        default=None,
        help="Optional mapped terminal data MQL5 root to mirror files into.",
    )
    parser.add_argument("--compile", action="store_true", help="Compile the deployed shell through MetaEditor.")
    parser.add_argument("--compile-timeout-seconds", type=int, default=60)
    parser.add_argument("--compile-log", type=Path, default=None)
    args = parser.parse_args(argv)

    output = deploy_phase1_mt5(
        root=args.root,
        portable_root=args.portable_root,
        data_mql5_root=args.data_mql5_root,
        compile_shell=args.compile,
        compile_timeout_seconds=args.compile_timeout_seconds,
        compile_log=args.compile_log,
    )
    print(f"Deployed files: {output.deployed_count}")
    print("Destinations:")
    for destination in output.destinations:
        print(f"- {destination}")
    print(f"Compile status: {output.compile_status}")
    if output.compile_log is not None:
        print(f"Compile log: {output.compile_log}")
    return 0 if output.compile_status in ("SKIPPED", "PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())

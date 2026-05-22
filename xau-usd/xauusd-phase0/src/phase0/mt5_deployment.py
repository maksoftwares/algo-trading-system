from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from phase0.config import ProjectConfig


LOGGER_NAME = "PassiveSpreadLogger_XAUUSD"


@dataclass(frozen=True)
class PassiveSpreadLoggerDeploymentOutput:
    status: str
    report_path: Path
    mt5_root: Path
    mq5_path: Path
    ex5_path: Path
    preset_path: Path
    compile_log_path: Path
    spread_log_count: int


def check_passive_spread_logger_deployment(
    config: ProjectConfig,
    mt5_root: str | Path = "C:/MT5PortableGoldMission",
) -> PassiveSpreadLoggerDeploymentOutput:
    mt5_root = Path(mt5_root)
    mq5_path = mt5_root / "MQL5" / "Experts" / "Phase0" / f"{LOGGER_NAME}.mq5"
    ex5_path = mt5_root / "MQL5" / "Experts" / "Phase0" / f"{LOGGER_NAME}.ex5"
    preset_path = mt5_root / "MQL5" / "Presets" / f"{LOGGER_NAME}.safe.set"
    compile_log_path = mt5_root / f"compile_{LOGGER_NAME}.log"
    files_dir = mt5_root / "MQL5" / "Files"

    local_logs = sorted(files_dir.glob("spread_log_*.csv")) if files_dir.exists() else []
    common_logs = sorted(_common_files_dir().glob("spread_log_*.csv")) if _common_files_dir().exists() else []
    checks = [
        _file_check("MT5 root", mt5_root),
        _file_check("Logger source", mq5_path),
        _file_check("Logger binary", ex5_path),
        _file_check("Logger preset", preset_path),
        _compile_check(compile_log_path),
        _spread_log_check(local_logs, common_logs),
    ]
    status = _overall_status(checks)
    report_path = config.root / "outputs" / "reports" / "PASSIVE_SPREAD_LOGGER_DEPLOYMENT.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        _render_report(
            status=status,
            mt5_root=mt5_root,
            mq5_path=mq5_path,
            ex5_path=ex5_path,
            preset_path=preset_path,
            compile_log_path=compile_log_path,
            local_logs=local_logs,
            common_logs=common_logs,
            checks=checks,
        ),
        encoding="utf-8",
    )
    return PassiveSpreadLoggerDeploymentOutput(
        status=status,
        report_path=report_path,
        mt5_root=mt5_root,
        mq5_path=mq5_path,
        ex5_path=ex5_path,
        preset_path=preset_path,
        compile_log_path=compile_log_path,
        spread_log_count=len(local_logs) + len(common_logs),
    )


def _file_check(name: str, path: Path) -> dict[str, str]:
    if path.exists():
        return {"Check": name, "Status": "PASS", "Evidence": f"Found `{path}`."}
    return {"Check": name, "Status": "FAIL", "Evidence": f"Missing `{path}`."}


def _compile_check(path: Path) -> dict[str, str]:
    if not path.exists():
        return {"Check": "Compile log", "Status": "FAIL", "Evidence": f"Missing `{path}`."}
    text = _read_text(path)
    if "Result: 0 errors, 0 warnings" in text:
        return {"Check": "Compile log", "Status": "PASS", "Evidence": f"`{path}` reports 0 errors / 0 warnings."}
    return {"Check": "Compile log", "Status": "FAIL", "Evidence": f"`{path}` does not report a clean compile."}


def _spread_log_check(local_logs: list[Path], common_logs: list[Path]) -> dict[str, str]:
    count = len(local_logs) + len(common_logs)
    if count:
        return {"Check": "Spread logs", "Status": "PASS", "Evidence": f"Found {count} spread log file(s)."}
    return {
        "Check": "Spread logs",
        "Status": "PENDING",
        "Evidence": "No `spread_log_*.csv` files found yet; attach the passive logger to an XAUUSD chart.",
    }


def _overall_status(checks: list[dict[str, str]]) -> str:
    if any(check["Status"] == "FAIL" for check in checks):
        return "FAIL"
    if any(check["Status"] == "PENDING" for check in checks):
        return "PENDING"
    return "PASS"


def _render_report(
    status: str,
    mt5_root: Path,
    mq5_path: Path,
    ex5_path: Path,
    preset_path: Path,
    compile_log_path: Path,
    local_logs: list[Path],
    common_logs: list[Path],
    checks: list[dict[str, str]],
) -> str:
    return "\n".join(
        [
            "# Passive Spread Logger Deployment",
            "",
            f"Overall status: {status}",
            "",
            "## Decision",
            "",
            _decision_text(status),
            "",
            "## Checks",
            "",
            _markdown_table(checks, ["Check", "Status", "Evidence"]),
            "",
            "## Paths",
            "",
            _markdown_table(
                [
                    {"Item": "MT5 root", "Path": str(mt5_root)},
                    {"Item": "Source", "Path": str(mq5_path)},
                    {"Item": "Binary", "Path": str(ex5_path)},
                    {"Item": "Preset", "Path": str(preset_path)},
                    {"Item": "Compile log", "Path": str(compile_log_path)},
                ],
                ["Item", "Path"],
            ),
            "",
            "## Spread Logs",
            "",
            _log_list("Local MT5 Files", local_logs),
            "",
            _log_list("Common Files", common_logs),
            "",
            "## Next Action",
            "",
            "Attach `PassiveSpreadLogger_XAUUSD` to an XAUUSD chart using `PassiveSpreadLogger_XAUUSD.safe.set` and verify that `spread_log_*.csv` starts appearing.",
            "",
        ]
    )


def _decision_text(status: str) -> str:
    if status == "PASS":
        return "Passive spread logging is deployed, compiled, and producing logs."
    if status == "PENDING":
        return "Passive spread logging is deployed and compiled, but no spread log files have appeared yet."
    return "Passive spread logger deployment is incomplete."


def _log_list(title: str, logs: list[Path]) -> str:
    if not logs:
        return f"{title}: no files found."
    return "\n".join([f"{title}:", *[f"- `{path}`" for path in logs]])


def _markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row.get(column, "") for column in columns) + " |")
    return "\n".join(lines)


def _common_files_dir() -> Path:
    return Path.home() / "AppData" / "Roaming" / "MetaQuotes" / "Terminal" / "Common" / "Files"


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16", errors="replace")
    return raw.decode("utf-8", errors="replace")

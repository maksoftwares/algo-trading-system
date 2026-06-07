from __future__ import annotations

import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_TERMINAL_EXE = Path("C:/Program Files/MetaTrader 5/terminal64.exe")
DEFAULT_TERMINAL_DATA_DIR = Path(
    "C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075"
)
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "PHASE2_WEAKNESS_BR_V1_LAUNCH.json"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "PHASE2_WEAKNESS_BR_V1_LAUNCH.md"
CONFIG_REL = Path("mt5") / "Config" / "p2weakness_br_v1_startup.ini"
STARTUP_LOG = "p2weakness_br_v1_startup_xauusd.csv"
SIGNAL_LOG = "p2weakness_br_v1_signal_log_xauusd.csv"
ORDER_LOG = "p2weakness_br_v1_order_log_xauusd.csv"


def launch_phase2_weakness_breakout_executor(
    phase1_root: Path,
    terminal_exe: Path = DEFAULT_TERMINAL_EXE,
    terminal_data_dir: Path = DEFAULT_TERMINAL_DATA_DIR,
    output_json: Path | None = None,
    wait_seconds: int = 30,
) -> Path:
    phase1_root = phase1_root.resolve()
    terminal_exe = terminal_exe.resolve()
    terminal_data_dir = terminal_data_dir.resolve()
    config = (phase1_root / CONFIG_REL).resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_OUTPUT_JSON.name else phase1_root / DEFAULT_OUTPUT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    if not terminal_exe.exists():
        raise FileNotFoundError(f"MT5 terminal not found: {terminal_exe}")
    if not config.exists():
        raise FileNotFoundError(f"Startup config not found: {config}")

    before = _file_state(terminal_data_dir)
    subprocess.Popen([str(terminal_exe), f"/config:{config}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        after = _file_state(terminal_data_dir)
        if after["startup_log_exists"] or after["signal_log_exists"]:
            break
        time.sleep(1)
    after = _file_state(terminal_data_dir)

    status = "ATTACHMENT_LOG_DETECTED" if after["startup_log_exists"] or after["signal_log_exists"] else "LAUNCH_SENT_NO_LOG_DETECTED_YET"
    payload: dict[str, Any] = {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": (
            "Experimental demo launch request for P2WEAKNESS_BR_V1 only. This script does not close MT5, "
            "replace profiles, remove existing EAs, or authorize live trading."
        ),
        "terminal_exe": str(terminal_exe),
        "terminal_data_dir": str(terminal_data_dir),
        "startup_config": str(config),
        "profile_touched": False,
        "terminal_closed_or_restarted": False,
        "before": before,
        "after": after,
        "wait_seconds": wait_seconds,
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return output_json


def _file_state(terminal_data_dir: Path) -> dict[str, Any]:
    files = terminal_data_dir / "MQL5" / "Files"
    startup = files / STARTUP_LOG
    signal = files / SIGNAL_LOG
    order = files / ORDER_LOG
    return {
        "startup_log": str(startup),
        "startup_log_exists": startup.exists(),
        "startup_log_size": startup.stat().st_size if startup.exists() else 0,
        "signal_log": str(signal),
        "signal_log_exists": signal.exists(),
        "signal_log_size": signal.stat().st_size if signal.exists() else 0,
        "order_log": str(order),
        "order_log_exists": order.exists(),
        "order_log_size": order.stat().st_size if order.exists() else 0,
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 2 Weakness Breakout-Retest V1 Launch",
        "",
        f"Status: {payload['status']}",
        "",
        payload["authority"],
        "",
        f"- Terminal: `{payload['terminal_exe']}`",
        f"- Data folder: `{payload['terminal_data_dir']}`",
        f"- Startup config: `{payload['startup_config']}`",
        f"- Profile touched: `{payload['profile_touched']}`",
        f"- Terminal closed/restarted: `{payload['terminal_closed_or_restarted']}`",
        f"- Startup log exists: `{payload['after']['startup_log_exists']}`",
        f"- Signal log exists: `{payload['after']['signal_log_exists']}`",
        f"- Order log exists: `{payload['after']['order_log_exists']}`",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Launch P2WEAKNESS_BR_V1 through MT5 startup config without profile replacement.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--terminal-exe", type=Path, default=DEFAULT_TERMINAL_EXE)
    parser.add_argument("--terminal-data-dir", type=Path, default=DEFAULT_TERMINAL_DATA_DIR)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--wait-seconds", type=int, default=30)
    args = parser.parse_args(argv)
    output = launch_phase2_weakness_breakout_executor(
        args.phase1_root,
        terminal_exe=args.terminal_exe,
        terminal_data_dir=args.terminal_data_dir,
        output_json=args.output_json,
        wait_seconds=args.wait_seconds,
    )
    print(output.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

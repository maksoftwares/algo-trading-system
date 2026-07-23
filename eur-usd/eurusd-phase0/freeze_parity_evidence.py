from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from src.evidence_audit import read_text_auto, sha256  # noqa: E402


RUN_JSON = PACKAGE_ROOT / "outputs" / "mt5_parity" / "FOREX_MT5_FREQUENCY_SCOUT_EURUSD_PHASE0_PARITY_V1.json"
LOCK_ROOT = PACKAGE_ROOT / "outputs" / "mt5_parity" / "locked"
ISOLATED_EX5 = Path("C:/MT5A1M5MomentumBacktest/MQL5/Experts/ForexMeanReversionScout.ex5")
SOURCE = REPO_ROOT / "forex-research" / "mt5" / "Experts" / "ForexMeanReversionScout.mq5"
PRESET = PACKAGE_ROOT / "mt5" / "Presets" / "EURUSD_M30_RSI_BB_FADE_V1_RESEARCH_ONLY.set"


def relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def artifact(path: Path) -> dict[str, str | int]:
    return {"path": relative(path), "sha256": sha256(path), "bytes": path.stat().st_size}


def main() -> int:
    payload = json.loads(RUN_JSON.read_text(encoding="utf-8"))
    result = payload["results"][0]
    LOCK_ROOT.mkdir(parents=True, exist_ok=True)

    frozen_ex5 = LOCK_ROOT / ISOLATED_EX5.name
    frozen_compile_log = LOCK_ROOT / "compile_ForexMeanReversionScout.log"
    shutil.copy2(ISOLATED_EX5, frozen_ex5)
    shutil.copy2(Path(payload["compile_log"]), frozen_compile_log)

    paths = {
        "source": SOURCE,
        "ex5": frozen_ex5,
        "compile_log": frozen_compile_log,
        "preset": PRESET,
        "run_json": RUN_JSON,
        "tester_config": REPO_ROOT / result["artifacts"]["tester_config"],
        "mt5_report": REPO_ROOT / result["artifacts"]["mt5_report"],
        "trade_csv": REPO_ROOT / result["artifacts"]["trade_csv"],
        "signal_log": REPO_ROOT / result["artifacts"]["signal_log"],
        "order_log": REPO_ROOT / result["artifacts"]["order_log"],
        "startup_log": REPO_ROOT / result["artifacts"]["startup_log"],
    }
    manifest = {
        "schema_version": "eurusd_phase0_mt5_parity_manifest_v1",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "boundary": payload["boundary"],
        "candidate": {
            "id": "EURUSD_M30_RSI_BB_CLOSE_FADE_LONG_V1",
            "variant": result["variant"],
            "from_date": payload["scope"]["from_date"],
            "to_date": payload["scope"]["to_date"],
        },
        "parity_result": {
            "trades": int(result["mt5_report_metrics"]["Total Trades"]),
            "net_profit_usd": float(result["mt5_report_metrics"]["Total Net Profit"]),
            "profit_factor": float(result["mt5_report_metrics"]["Profit Factor"]),
            "equity_drawdown": result["mt5_report_metrics"]["Equity Drawdown Maximal"],
            "compile_zero_errors_zero_warnings": "Result: 0 errors, 0 warnings"
            in read_text_auto(frozen_compile_log),
        },
        "artifacts": {name: artifact(path) for name, path in paths.items()},
    }
    manifest_path = LOCK_ROOT / "PARITY_MANIFEST.json"
    with manifest_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(manifest, indent=2) + "\n")
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

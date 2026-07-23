from __future__ import annotations

import argparse
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "mt5" / "Experts" / "EurUsdM30BarAuditExporter.mq5"
EA_NAME = SOURCE.stem
REPORT_BASE = "EURUSD_V1_UNMASKED_M30_BAR_AUDIT"
CSV_NAME = "eurusd_v1_unmasked_m30_bar_audit.csv"


def read_text_auto(path: Path) -> str:
    data = path.read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    return data.decode("utf-8-sig")


def find_tester_files(root: Path, name: str) -> list[Path]:
    return sorted(
        (
            path
            for path in (root / "Tester").glob(f"Agent-*/MQL5/Files/{name}")
            if path.is_file()
        ),
        key=lambda path: path.stat().st_mtime_ns,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tester-root", type=Path, default=Path("C:/MT5A1M5MomentumBacktest"))
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "bar_audit")
    args = parser.parse_args()

    tester = args.tester_root.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    experts = tester / "MQL5" / "Experts"
    experts.mkdir(parents=True, exist_ok=True)
    target_source = experts / SOURCE.name
    shutil.copy2(SOURCE, target_source)

    compile_log = tester / "Logs" / (
        "compile_EurUsdM30BarAuditExporter_"
        + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        + ".log"
    )
    subprocess.run(
        [
            str(tester / "MetaEditor64.exe"),
            f"/compile:{target_source}",
            f"/log:{compile_log}",
        ],
        cwd=tester,
        check=False,
        timeout=120,
    )
    compile_text = read_text_auto(compile_log)
    if "Result: 0 errors, 0 warnings" not in compile_text:
        raise RuntimeError(f"Bar exporter compile failed:\n{compile_text}")

    ex5 = experts / f"{EA_NAME}.ex5"
    if not ex5.exists():
        raise RuntimeError("Bar exporter EX5 was not produced")

    for stale in find_tester_files(tester, CSV_NAME):
        stale.unlink()

    config = tester / "Config" / f"{REPORT_BASE}.ini"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        "\n".join(
            [
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
                "FromDate=2022.07.01",
                "ToDate=2026.07.02",
                "ForwardMode=0",
                "Deposit=1000",
                "Currency=USD",
                "ProfitInPips=0",
                "Leverage=200",
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
                "InpTargetSymbol=EURUSD",
                f"InpOutputFileName={CSV_NAME}",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )

    process = subprocess.Popen(
        [str(tester / "terminal64.exe"), "/portable", f"/config:{config}"],
        cwd=tester,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    process.wait(timeout=600)

    csv_paths = find_tester_files(tester, CSV_NAME)
    if len(csv_paths) != 1:
        raise RuntimeError(f"Expected one bar export, found {len(csv_paths)}")

    report = tester / "Reports" / f"{REPORT_BASE}.htm"
    if not report.exists():
        raise RuntimeError("Bar exporter MT5 report was not produced")

    shutil.copy2(config, output / config.name)
    shutil.copy2(csv_paths[0], output / CSV_NAME)
    shutil.copy2(report, output / report.name)
    shutil.copy2(compile_log, output / compile_log.name)
    shutil.copy2(ex5, output / ex5.name)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from m15_comex_ranker import align_comex_context, run_m15_ranker, source_date  # noqa: E402
from tbbo_features import load_trade_feature_config, load_trades_dbn  # noqa: E402
from trade_campaign import discover_dbn_files  # noqa: E402


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Rank M15 spot candidates with primary COMEX flow.")
    command.add_argument("--config", type=Path, default=ROOT / "config" / "comex_m15_ranker_v1.json")
    command.add_argument("--candidate-csv", type=Path, default=ROOT.parent / "ml-candidate-rankers-v1" / "outputs" / "ML_CANDIDATE_RANKERS_CANDIDATES.csv")
    command.add_argument("--job-directory", type=Path, default=Path("C:/ComexGoldFuturesFoundationV1/raw/GLBX-20260717-5MX758XBAQ"))
    command.add_argument("--output-directory", type=Path, default=Path("C:/ComexGoldFuturesFoundationV1/research/comex-m15-ranker-v1"))
    return command


def main() -> int:
    args = parser().parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    feature_config = load_trade_feature_config()
    candidates = pd.read_csv(args.candidate_csv, parse_dates=["signal_time", "entry_time", "exit_time"])
    start = pd.Timestamp(config["windows"]["fit"][0])
    end = pd.Timestamp(config["windows"]["exam"][0])
    local = candidates["signal_time"].dt.tz_convert(feature_config["session"]["timezone"])
    minutes = local.dt.hour * 60 + local.dt.minute
    candidates = candidates.loc[(candidates["signal_time"] >= start) & (candidates["signal_time"] < end) & (minutes >= 500) & (minutes < 810)].copy()
    candidates["source_date"] = candidates["signal_time"].dt.strftime("%Y%m%d")
    by_date = {date: frame for date, frame in candidates.groupby("source_date", sort=False)}
    aligned = []
    files = discover_dbn_files(args.job_directory)
    for index, path in enumerate(files, start=1):
        date = source_date(path)
        if date in by_date:
            frame = align_comex_context(load_trades_dbn(path), by_date[date], feature_config)
            if not frame.empty:
                aligned.append(frame)
        if index == 1 or index % 100 == 0 or index == len(files):
            print(f"aligned files: {index}/{len(files)}", flush=True)
    dataset = pd.concat(aligned, ignore_index=True).sort_values("signal_time", kind="stable")
    report, selected = run_m15_ranker(dataset, config)
    args.output_directory.mkdir(parents=True, exist_ok=True)
    dataset.to_parquet(args.output_directory / "context_dataset_fit_calibration_validation.parquet", index=False)
    selected.to_parquet(args.output_directory / "selected_trades.parquet", index=False)
    report_path = args.output_directory / "evidence_report.json"
    report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["research_decision"], "report": str(report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

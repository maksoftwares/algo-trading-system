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

from context_ranker import join_context, load_partitions, run_ranker  # noqa: E402


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Run the frozen COMEX plus spot context ranker.")
    command.add_argument("--config", type=Path, default=ROOT / "config" / "comex_context_ranker_v1.json")
    command.add_argument("--research-directory", type=Path, default=Path("C:/ComexGoldFuturesFoundationV1/research/comex-zero-payment-trades-v1"))
    command.add_argument("--spot-cache", type=Path, default=Path("C:/DukascopyTickDataFoundationV1/research/xau-confirmed-event-specialists-v1/m5_bidask_features_v1.parquet"))
    command.add_argument("--output-directory", type=Path, default=Path("C:/ComexGoldFuturesFoundationV1/research/comex-context-ranker-v1"))
    return command


def main() -> int:
    args = parser().parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    candidates = load_partitions(args.research_directory / "candidates")
    labels = load_partitions(args.research_directory / "labels")
    m5 = pd.read_parquet(args.spot_cache)
    dataset = join_context(candidates, labels, m5)
    exam_start = pd.Timestamp(config["windows"]["exam"][0])
    development = dataset.loc[dataset["feature_time_utc"] < exam_start].copy()
    report, selected = run_ranker(development, config)
    args.output_directory.mkdir(parents=True, exist_ok=True)
    development.to_parquet(args.output_directory / "context_dataset_fit_calibration_validation.parquet", index=False)
    selected.to_parquet(args.output_directory / "selected_trades.parquet", index=False)
    report_path = args.output_directory / "evidence_report.json"
    report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["research_decision"], "report": str(report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from hour_ranker import align_hour_comex, label_both_directions, regular_signals, run_hour_ranker  # noqa: E402
from m15_comex_ranker import source_date  # noqa: E402
from tbbo_features import load_trade_feature_config, load_trades_dbn  # noqa: E402
from trade_campaign import discover_dbn_files  # noqa: E402


def main() -> int:
    config_path = ROOT / "config" / "comex_hour_ranker_v1.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    spot_path = Path("C:/DukascopyTickDataFoundationV1/research/xau-confirmed-event-specialists-v1/m5_bidask_features_v1.parquet")
    job_path = Path("C:/ComexGoldFuturesFoundationV1/raw/GLBX-20260717-5MX758XBAQ")
    output = Path("C:/ComexGoldFuturesFoundationV1/research/comex-hour-ranker-v1")
    m5 = pd.read_parquet(spot_path)
    signals = regular_signals(m5, config["windows"]["fit"][0], config["windows"]["exam"][0])
    signals = label_both_directions(signals, m5, config["label"])
    by_date = {date: frame for date, frame in signals.groupby("source_date", sort=False)}
    feature_config = load_trade_feature_config()
    aligned = []
    files = discover_dbn_files(job_path)
    for index, path in enumerate(files, start=1):
        date = source_date(path)
        if date in by_date:
            frame = align_hour_comex(load_trades_dbn(path), by_date[date], feature_config)
            if not frame.empty:
                aligned.append(frame)
        if index == 1 or index % 100 == 0 or index == len(files):
            print(f"aligned files: {index}/{len(files)}", flush=True)
    dataset = pd.concat(aligned, ignore_index=True).sort_values("signal_time", kind="stable")
    report, selected = run_hour_ranker(dataset, config)
    output.mkdir(parents=True, exist_ok=True)
    dataset.to_parquet(output / "context_dataset_fit_calibration_validation.parquet", index=False)
    selected.to_parquet(output / "selected_trades.parquet", index=False)
    report_path = output / "evidence_report.json"
    report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["research_decision"], "report": str(report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from spot_labels import (  # noqa: E402
    DEFAULT_LABEL_CONFIG,
    VerifiedSpotTickStore,
    load_completed_atr,
    load_dukascopy_foundation,
    load_label_config,
    resolve_spot_storage,
)
from tbbo_features import DEFAULT_TRADE_FEATURE_CONFIG, load_trade_feature_config  # noqa: E402
from trade_campaign import (  # noqa: E402
    build_evidence_report,
    discover_dbn_files,
    process_candidate_file,
    process_label_file,
)


DEFAULT_JOB_DIRECTORY = Path("C:/ComexGoldFuturesFoundationV1/raw/GLBX-20260717-5MX758XBAQ")
DEFAULT_OUTPUT_DIRECTORY = Path(
    "C:/ComexGoldFuturesFoundationV1/research/comex-zero-payment-trades-v1"
)


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Run the frozen COMEX trade-flow specialists.")
    command.add_argument("--job-directory", type=Path, default=DEFAULT_JOB_DIRECTORY)
    command.add_argument("--output-directory", type=Path, default=DEFAULT_OUTPUT_DIRECTORY)
    command.add_argument("--feature-config", type=Path, default=DEFAULT_TRADE_FEATURE_CONFIG)
    command.add_argument("--label-config", type=Path, default=DEFAULT_LABEL_CONFIG)
    command.add_argument("--candidate-only", action="store_true")
    command.add_argument("--force", action="store_true")
    command.add_argument("--limit-files", type=int)
    return command


def _partition_name(source: Path) -> str:
    name = source.name.replace(".dbn.zst", "").replace(".dbn", "")
    return f"{name}.parquet"


def _load_partitions(paths: list[Path]) -> pd.DataFrame:
    frames = [pd.read_parquet(path) for path in paths if path.is_file()]
    nonempty = [frame for frame in frames if not frame.empty]
    return pd.concat(nonempty, ignore_index=True) if nonempty else pd.DataFrame()


def main() -> int:
    args = parser().parse_args()
    if args.limit_files is not None and args.limit_files <= 0:
        raise ValueError("--limit-files must be positive.")
    feature_config = load_trade_feature_config(args.feature_config)
    label_config = load_label_config(args.label_config)
    sources = discover_dbn_files(args.job_directory)
    if args.limit_files is not None:
        sources = sources[: args.limit_files]
    candidate_directory = args.output_directory / "candidates"
    label_directory = args.output_directory / "labels"
    candidate_paths: list[Path] = []
    for index, source in enumerate(sources, start=1):
        destination = candidate_directory / _partition_name(source)
        if args.force or not destination.is_file():
            process_candidate_file(source, destination, feature_config)
        candidate_paths.append(destination)
        if index == 1 or index % 25 == 0 or index == len(sources):
            print(f"candidate files: {index}/{len(sources)}", flush=True)

    if args.candidate_only:
        candidates = _load_partitions(candidate_paths)
        print(json.dumps({"candidate_rows": len(candidates), "files": len(sources)}, indent=2))
        return 0

    storage_root = resolve_spot_storage(label_config)
    foundation = load_dukascopy_foundation()
    tick_store = VerifiedSpotTickStore(
        storage_root=storage_root,
        symbol=label_config["spot_source"]["symbol"],
        foundation=foundation,
    )
    atr_source = load_completed_atr(label_config, storage_root)
    label_paths: list[Path] = []
    for index, candidates_path in enumerate(candidate_paths, start=1):
        destination = label_directory / candidates_path.name
        if args.force or not destination.is_file():
            process_label_file(
                candidates_path,
                destination,
                atr_source=atr_source,
                tick_store=tick_store,
                config=label_config,
            )
        label_paths.append(destination)
        if index == 1 or index % 25 == 0 or index == len(candidate_paths):
            print(f"label files: {index}/{len(candidate_paths)}", flush=True)

    labels = _load_partitions(label_paths)
    report = build_evidence_report(labels, label_config)
    report.update(
        {
            "generated_utc": datetime.now(UTC).isoformat(),
            "job_directory": str(args.job_directory.resolve()),
            "source_file_count": len(sources),
            "feature_contract_id": feature_config["contract_id"],
        }
    )
    args.output_directory.mkdir(parents=True, exist_ok=True)
    report_path = args.output_directory / "evidence_report.json"
    report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["research_decision"], "report": str(report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

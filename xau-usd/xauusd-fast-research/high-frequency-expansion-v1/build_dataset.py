from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
SHARED_SRC = ROOT.parent / "independent-specialists-v1" / "src"
sys.path.insert(0, str(SHARED_SRC))
sys.path.insert(0, str(ROOT / "src"))

from data import load_bundle  # noqa: E402
from research import classify_h4  # noqa: E402
from dataset import (  # noqa: E402
    build_action_labels,
    build_candidate_events,
    prepare_market_features,
    sha256_file,
)
from evaluation import business_days, metrics  # noqa: E402


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if hasattr(value, "item"):
        return json_ready(value.item())
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(json_ready(value), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def frame_digest(frame: pd.DataFrame, columns: list[str]) -> str:
    payload = frame[columns].to_csv(
        index=False, lineterminator="\n", float_format="%.10g"
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def independent_cluster_count(events: pd.DataFrame, minutes: int) -> int:
    threshold = pd.Timedelta(minutes=minutes)
    count = 0
    cluster_end = pd.Timestamp.min.tz_localize("UTC")
    for timestamp in events["signal_time"].drop_duplicates().sort_values():
        if timestamp > cluster_end:
            count += 1
            cluster_end = timestamp + threshold
    return count


def main() -> int:
    config_path = ROOT / "config" / "high_frequency_expansion_v1.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    bundle = load_bundle(config)
    classified_h4 = classify_h4(bundle.bars["H4"], config["regime"])
    market = prepare_market_features(bundle.bars["M5"], bundle.bars["H1"], classified_h4)
    events, event_evidence = build_candidate_events(REPO_ROOT, config, market)
    actions = build_action_labels(events, bundle.bars["M5"], config["actions"], config["execution"])
    if actions.empty:
        raise ValueError("No action labels were produced")

    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    event_path = output / config["outputs"]["candidate_events"]
    action_path = output / config["outputs"]["candidate_actions"]
    events.to_parquet(event_path, index=False)
    actions.to_parquet(action_path, index=False)

    metric_rows: list[dict[str, Any]] = []
    for stage, window in config["windows"].items():
        start, end = map(pd.Timestamp, window)
        for action_id, trades in actions.groupby("action_id", sort=True):
            value = metrics(trades, start, end, 10)
            metric_rows.append({"stage": stage, "action_id": action_id, **value})
    baseline = pd.DataFrame(metric_rows)
    baseline.to_csv(
        output / config["outputs"]["baseline_metrics"], index=False, lineterminator="\n"
    )

    source_start = pd.Timestamp(config["source"]["start_utc"])
    source_end = pd.Timestamp(config["source"]["end_exclusive_utc"])
    source_weekdays = business_days(source_start, source_end)
    daily = events.groupby(events["signal_time"].dt.tz_localize(None).dt.normalize()).size()
    evidence = {
        "schema_version": config["schema_version"],
        "data_evidence": bundle.evidence,
        "candidate_event_evidence": event_evidence,
        "candidate_event_rows": int(len(events)),
        "candidate_action_rows": int(len(actions)),
        "source_weekdays": source_weekdays,
        "events_per_weekday": len(events) / source_weekdays,
        "thirty_minute_clusters": independent_cluster_count(events, 30),
        "thirty_minute_clusters_per_weekday": independent_cluster_count(events, 30) / source_weekdays,
        "weekday_share_with_at_least_three_events": float((daily >= 3).sum() / source_weekdays),
        "weekday_share_with_at_least_four_events": float((daily >= 4).sum() / source_weekdays),
        "ambiguous_m5_action_rows": int(actions["ambiguous_m5"].sum()),
        "current_account_feasible_share": float(actions["current_account_feasible"].mean()),
        "event_digest": frame_digest(events, ["event_id", "signal_time", "direction", "regime"]),
        "action_digest": frame_digest(
            actions,
            ["event_id", "action_id", "entry_time", "exit_time", "stress_net_r"],
        ),
        "authorization": config["research_controls"],
    }
    write_json(output / config["outputs"]["dataset_evidence"], evidence)
    manifest = {
        "config_sha256": sha256_file(config_path),
        "preregistration_sha256": sha256_file(ROOT / "PREREGISTRATION.md"),
        "dataset_code_sha256": sha256_file(ROOT / "src" / "dataset.py"),
        "evaluation_code_sha256": sha256_file(ROOT / "src" / "evaluation.py"),
        "feature_cache_sha256": bundle.evidence["feature_sha256"],
        "candidate_source_sha256": {
            source["path"]: source["sha256"] for source in config["candidate_sources"]
        },
        "event_parquet_sha256": sha256_file(event_path),
        "action_parquet_sha256": sha256_file(action_path),
        "event_digest": evidence["event_digest"],
        "action_digest": evidence["action_digest"],
    }
    write_json(output / config["outputs"]["manifest"], manifest)
    print(json.dumps(json_ready(evidence), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

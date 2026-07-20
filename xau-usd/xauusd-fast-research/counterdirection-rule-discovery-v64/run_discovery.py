from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("v64_family", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    config_path = ROOT / "config" / "counterdirection_rule_discovery_v64.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    for source_id, source in config["sources"].items():
        actual = sha256_file(REPO_ROOT / source["path"])
        if actual != source["sha256"]:
            raise ValueError(f"Source hash mismatch for {source_id}: {actual}")
    family = load_module(REPO_ROOT / config["sources"]["family_module"]["path"])
    cutoff = pd.Timestamp(config["selection_cutoff_exclusive_utc"])
    actions = pd.read_parquet(
        REPO_ROOT / config["sources"]["bidirectional_actions"]["path"]
    )
    for column in ("signal_time", "entry_time", "exit_time"):
        actions[column] = pd.to_datetime(actions[column], utc=True)
    actions = actions.loc[
        actions["signal_time"].lt(cutoff)
        & actions["exit_time"].lt(cutoff)
        & actions["direction_flipped"].eq(1.0)
        & actions["current_account_feasible"].astype(bool)
        & actions["risk_usd"].astype(float).le(
            float(config["candidate_filter"]["maximum_risk_usd"])
        )
    ].copy()
    v57 = pd.read_parquet(
        REPO_ROOT / config["sources"]["qualified_v57_candidates"]["path"]
    )
    excluded_times = set(pd.to_datetime(v57["signal_time"], utc=True))
    actions = actions.loc[~actions["signal_time"].isin(excluded_times)].copy()
    actions["action_id"] = actions["base_action_id"].astype(str)
    frame = family.enrich(actions)
    candidates = family.generate_forward_candidates(frame, config)

    rule_rows: list[dict] = []
    trade_frames: list[pd.DataFrame] = []
    ordered = sorted(
        candidates,
        key=lambda item: (
            -min(item["forward"]["D2"]["pf"], item["forward"]["F4"]["pf"]),
            -min(
                item["forward"]["D2"]["frequency"],
                item["forward"]["F4"]["frequency"],
            ),
            item["rule"],
        ),
    )
    for index, candidate in enumerate(ordered, start=1):
        rule_id = f"V64_R{index:04d}"
        row = {
            "rule_id": rule_id,
            "rule": candidate["rule"],
            "width": len(candidate["features"]),
        }
        for window_name, metrics in candidate["forward"].items():
            for metric, value in metrics.items():
                row[f"{window_name}_{metric}"] = value
        row["minimum_window_pf"] = min(row["D2_pf"], row["F4_pf"])
        row["minimum_window_frequency"] = min(
            row["D2_frequency"], row["F4_frequency"]
        )
        rule_rows.append(row)
        trade_frames.append(
            candidate["executed"].assign(rule_id=rule_id, rule=candidate["rule"])
        )
    rules = pd.DataFrame(rule_rows)
    trades = (
        pd.concat(trade_frames, ignore_index=True)
        if trade_frames
        else pd.DataFrame()
    )
    output_dir = ROOT / config["outputs"]["directory"]
    output_dir.mkdir(parents=True, exist_ok=True)
    rules.to_csv(output_dir / config["outputs"]["rules"], index=False)
    trades.to_parquet(output_dir / config["outputs"]["trades"], index=False)
    payload = {
        "schema_version": config["schema_version"],
        "screened_counter_action_rows": int(len(frame)),
        "surviving_unique_rules": int(len(rules)),
        "selection_cutoff_exclusive_utc": str(cutoff),
        "research_controls": config["research_controls"],
    }
    (output_dir / config["outputs"]["result"]).write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    print(rules.head(25).to_string(index=False))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

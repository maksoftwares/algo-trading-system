from __future__ import annotations

from datetime import UTC, datetime
import importlib.util
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG = ROOT / "config" / "experiment.json"
OUTPUT = ROOT / "inputs" / "AUGUST_2026_CAUSAL_FEATURES.csv"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    import MetaTrader5 as mt5

    experiment = json.loads(CONFIG.read_text(encoding="utf-8"))
    prospective_item = experiment["inputs"]["prospective_observer_config"]
    prospective_path = REPO_ROOT / prospective_item["path"]
    if digest(prospective_path) != prospective_item["sha256"]:
        raise ValueError("Locked prospective observer config changed")
    prospective = json.loads(prospective_path.read_text(encoding="utf-8"))
    ranker_path = ROOT.parent / "v60-mature-source-health-rank-veto-prospective-v2" / "src" / "ranker.py"
    if digest(ranker_path) != prospective["lock"]["observer_ranker_sha256"]:
        raise ValueError("Locked observer ranker changed")
    ranker = load_module("v60_antichase_capture_ranker", ranker_path)
    account = prospective["account"]
    if not mt5.initialize(path=str(account["terminal_exe"]), portable=True):
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
    try:
        info = mt5.account_info()
        terminal = mt5.terminal_info()
        if info is None or terminal is None or not bool(terminal.connected):
            raise RuntimeError("MT5 read-only account state is unavailable")
        if int(info.login) != int(account["expected_login"]):
            raise RuntimeError(f"Wrong account: {info.login}")
        if str(info.server) != str(account["expected_server"]):
            raise RuntimeError(f"Wrong server: {info.server}")
        runtime = ranker.prepare_runtime(mt5, REPO_ROOT, prospective)
    finally:
        mt5.shutdown()

    deployed_path = REPO_ROOT / prospective["read_only_inputs"][
        "candidate_source_config"
    ]
    deployed = json.loads(deployed_path.read_text(encoding="utf-8"))
    source = next(
        row
        for row in deployed["sources"]
        if row["source_id"] == "V57_BREAK_SWING_H4ADX_HIGH"
    )
    candidates = [
        json.loads(line)
        for line in Path(source["path"]).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    candidates = [
        row
        for row in candidates
        if row["specialist_id"] == "V57_BREAK_SWING_H4ADX_HIGH"
        and str(row["scheduled_entry_time_utc"]).startswith("2026-08-")
        and str(row["scheduled_entry_time_utc"]) < "2026-08-26T00:00:00Z"
    ]
    features = runtime["feature_bars"]
    rows = []
    for candidate in sorted(
        candidates, key=lambda row: (row["scheduled_entry_time_utc"], row["candidate_id"])
    ):
        timestamp = pd.Timestamp(candidate["scheduled_entry_time_utc"])
        completed = features.loc[features["decision_time_utc"].le(timestamp)]
        if completed.empty:
            raise ValueError(f"No causal feature bar: {candidate['candidate_id']}")
        feature = completed.iloc[-1]
        age = timestamp - pd.Timestamp(feature["decision_time_utc"])
        if age > pd.Timedelta(minutes=10):
            raise ValueError(f"Stale causal feature bar: {candidate['candidate_id']}")
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "execution_source_id": candidate["specialist_id"],
                "direction": candidate["direction"],
                "scheduled_entry_time_utc": candidate["scheduled_entry_time_utc"],
                "feature_bar_time_utc": pd.Timestamp(
                    feature["decision_time_utc"]
                ).isoformat().replace("+00:00", "Z"),
                "atr_ratio": float(feature["atr_ratio"]),
                "rv_1h": float(feature["rv_1h"]),
                "rv_24h": float(feature["rv_24h"]),
                "slope_atr": float(feature["slope_atr"]),
                "ret_1h": float(feature["ret_1h"]),
                "ret_4h": float(feature["ret_4h"]),
                "ret_24h": float(feature["ret_24h"]),
                "dist_hi_24h": float(feature["dist_hi_24h"]),
                "dist_lo_24h": float(feature["dist_lo_24h"]),
            }
        )
    output = pd.DataFrame(rows)
    if output.empty or output["candidate_id"].duplicated().any():
        raise ValueError("Invalid August causal feature snapshot")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT, index=False, lineterminator="\n")
    print(
        json.dumps(
            {
                "generated_at_utc": datetime.now(UTC)
                .isoformat()
                .replace("+00:00", "Z"),
                "rows": len(output),
                "output": str(OUTPUT),
                "broker_action_authorized": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

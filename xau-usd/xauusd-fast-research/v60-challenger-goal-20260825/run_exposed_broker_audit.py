from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
import importlib.util
import json
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
V2_ROOT = (
    REPO_ROOT
    / "xau-usd"
    / "xauusd-fast-research"
    / "v60-mature-source-health-rank-veto-prospective-v2"
)
V2_RUNNER = V2_ROOT / "run_observer.py"
V2_CONFIG = V2_ROOT / "config" / "prospective.json"
EXPOSED_START_UTC = "2026-07-21T00:00:00Z"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def summarize(status: dict, rows: list[dict]) -> dict:
    executed_resolved = [
        row
        for row in rows
        if row["baseline_executed"] and row["broker_outcome_resolved"]
    ]
    values = [float(row["broker_pnl_usd"]) for row in executed_resolved]
    wins = [value for value in values if value > 0.0]
    losses = [value for value in values if value < 0.0]
    gross_loss = -sum(losses)
    vetoes = [row for row in executed_resolved if row["would_veto"]]
    return {
        "schema_version": "xauusd_v60_v2_exposed_broker_audit_20260825",
        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "evidence_status": "RETROSPECTIVE_EXPOSED_NOT_PROSPECTIVE",
        "start_inclusive_utc": EXPOSED_START_UTC,
        "end_inclusive_utc": status["generated_at_utc"],
        "authorization": {
            "read_only_mt5": True,
            "broker_actions": False,
            "deployment": False,
        },
        "baseline": {
            "resolved_executions": len(executed_resolved),
            "wins": len(wins),
            "losses": len(losses),
            "net_pnl_usd": sum(values),
            "profit_factor": sum(wins) / gross_loss if gross_loss > 0.0 else None,
        },
        "v2": {
            "would_veto_resolved": len(vetoes),
            "vetoed_broker_pnl_usd": sum(float(row["broker_pnl_usd"]) for row in vetoes),
            "avoided_broker_pnl_usd": -sum(
                float(row["broker_pnl_usd"]) for row in vetoes
            ),
        },
        "observer_counts": status["counts"],
        "limitations": [
            "These outcomes were visible before the clean V2 evidence boundary.",
            "This audit cannot authorize deployment or count toward prospective gates.",
            "Only candidates emitted to the locked V2 observer ledgers are evaluated.",
        ],
    }


def main() -> int:
    runner = load_module("v60_v2_exposed_audit_runner", V2_RUNNER)
    config = runner.load_locked_config(V2_CONFIG)
    runner.verify_shared_observer(config)
    exposed_config = deepcopy(config)
    exposed_config["lock"]["evidence_start_inclusive_utc"] = EXPOSED_START_UTC
    deals = runner.read_mt5_deals(exposed_config)
    status, rows = runner.build_snapshot(exposed_config, deals)
    result = summarize(status, rows)
    (ROOT / "EXPOSED_BROKER_AUDIT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    pd.DataFrame(rows).to_csv(ROOT / "EXPOSED_BROKER_AUDIT.csv", index=False)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

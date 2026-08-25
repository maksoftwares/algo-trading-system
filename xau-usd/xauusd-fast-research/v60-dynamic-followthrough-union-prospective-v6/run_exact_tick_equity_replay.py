from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from src.evidence import atomic_write, load_chain
from src.tick_replay import iter_tick_files, replay_ticks, trades_from_evidence


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG = ROOT / "config" / "prospective.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    locks = config["lock"]
    wrapper = ROOT / "src" / "tick_replay.py"
    base = ROOT.parent / "v60-mature-source-health-rank-veto-prospective-v2" / "src" / "tick_replay.py"
    checks = (
        (Path(__file__), "tick_replay_runner_sha256"),
        (wrapper, "tick_replay_sha256"),
        (base, "base_tick_replay_sha256"),
    )
    for path, key in checks:
        actual = sha256_file(path)
        if actual != locks[key]:
            raise ValueError(f"Locked exact replay source changed: {key}: {actual}")
    runtime = Path(config["outputs"]["runtime_directory"])
    records = load_chain(runtime / "EVIDENCE_CHAIN.jsonl")
    trades = trades_from_evidence(
        records,
        maximum_decision_recording_delay_seconds=int(
            config["acceptance"]["maximum_decision_recording_delay_seconds"]
        ),
    )
    output_path = runtime / "EXACT_TICK_EQUITY_REPLAY.json"
    if not trades:
        result = {
            "schema_version": "v60_dynamic_v6_exact_tick_equity_replay_v1",
            "decision": "NOT_READY_NO_RESOLVED_TRADES",
            "deployment_authorized": False,
        }
        atomic_write(output_path, json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, sort_keys=True))
        return 0
    portfolio_path = Path(config["read_only_inputs"]["candidate_source_config"])
    if not portfolio_path.is_absolute():
        portfolio_path = REPO_ROOT / portfolio_path
    portfolio = json.loads(portfolio_path.read_text(encoding="utf-8"))
    tick_directory = Path(portfolio["feeds"]["terminal_files_directory"])
    tick_paths = list(tick_directory.glob(portfolio["feeds"]["tick_filename_glob"]))
    if not tick_paths:
        raise FileNotFoundError("No prospective XAUUSD tick files were found")
    account = portfolio["account"]
    units_per_lot = float(account["expected_ounces_at_fixed_lot"]) / float(account["fixed_lot"])
    first_entry = min(trade.entry_time_msc for trade in trades)
    final_exit = max(trade.exit_time_msc for trade in trades)
    first_date = datetime.fromtimestamp(first_entry / 1000.0, UTC).date()
    final_date = datetime.fromtimestamp(final_exit / 1000.0, UTC).date()
    if final_date >= datetime.now(UTC).date():
        result = {
            "schema_version": "v60_dynamic_v6_exact_tick_equity_replay_v1",
            "decision": "NOT_READY_FINAL_TICK_DAY_STILL_OPEN",
            "final_exit_utc_date": final_date.isoformat(),
            "deployment_authorized": False,
        }
        atomic_write(output_path, json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, sort_keys=True))
        return 0
    relevant = []
    for path in tick_paths:
        try:
            file_date = datetime.strptime(path.stem.rsplit("_", 1)[-1], "%Y%m%d").date()
        except ValueError:
            continue
        if first_date <= file_date <= final_date:
            relevant.append(path)
    if not relevant:
        raise FileNotFoundError("No dated tick files cover the resolved trades")
    result = replay_ticks(
        trades,
        iter_tick_files(relevant, first_time_msc=first_entry, final_time_msc=final_exit),
        contract_units_per_lot=units_per_lot,
    )
    result.update(
        {
            "schema_version": "v60_dynamic_v6_exact_tick_equity_replay_v1",
            "decision": (
                "EXACT_TICK_EQUITY_GATE_PASSES_REVIEW_REQUIRED"
                if result["challenger_v2_equity_drawdown_usd"]
                <= result["baseline_v60_equity_drawdown_usd"]
                else "KEEP_DEPLOYED_V60_EXACT_TICK_GATE_FAILS"
            ),
            "tick_files_considered": len(relevant),
            "tick_file_sha256": {path.name: sha256_file(path) for path in sorted(relevant)},
            "contract_units_per_lot": units_per_lot,
            "deployment_authorized": False,
        }
    )
    atomic_write(output_path, json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

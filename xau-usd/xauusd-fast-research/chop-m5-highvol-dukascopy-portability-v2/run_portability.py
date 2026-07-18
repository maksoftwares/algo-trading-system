from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
from typing import Any, Mapping

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from portability import evaluate_gate, run_portability, stage_metrics  # noqa: E402


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def self_hash(payload: dict[str, Any]) -> str:
    work = dict(payload)
    work.pop("contract_sha256", None)
    encoded = json.dumps(
        work, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def verify_record(record: Mapping[str, Any], base: Path, label: str) -> None:
    path = (base / str(record["path"])).resolve()
    path.relative_to(base.resolve())
    if not path.is_file() or path.stat().st_size != int(record["bytes"]):
        raise ValueError(f"{label} file missing or size mismatch: {record['path']}")
    if sha256_file(path) != str(record["sha256"]):
        raise ValueError(f"{label} SHA-256 mismatch: {record['path']}")


def verify_lock(config: Mapping[str, Any]) -> dict[str, Any]:
    output = ROOT / str(config["outputs"]["directory"])
    path = output / str(config["outputs"]["contract_lock"])
    if not path.is_file():
        raise FileNotFoundError("Run lock_contract.py before opening outcomes")
    lock = json.loads(path.read_text(encoding="utf-8"))
    if self_hash(lock) != str(lock["contract_sha256"]):
        raise ValueError("Contract self-hash mismatch")
    for item in lock["package_files"] + lock["dependency_files"]:
        verify_record(item, REPO, "repository")
    source = config["source"]
    storage = Path(
        os.environ.get(source["storage_environment_variable"], source["default_storage_root"])
    ).resolve()
    for item in lock["external_files"]:
        verify_record(item, storage, "external")
    if int(lock["candidate_count"]) != 1 or int(lock["parameter_search_count"]) != 0:
        raise ValueError("Candidate cardinality differs from the contract")
    return lock


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


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(json_ready(dict(payload)), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def frame_digest(frame: pd.DataFrame) -> str:
    if frame.empty:
        return hashlib.sha256(b"").hexdigest()
    columns = [
        "strategy_id",
        "entry_time",
        "exit_time",
        "direction",
        "net_r",
        "stress_net_r",
    ]
    payload = frame[columns].to_csv(
        index=False, lineterminator="\n", float_format="%.10g"
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def render(payload: Mapping[str, Any], stages: pd.DataFrame) -> str:
    lines = [
        "# XAUUSD M5 High-Volatility Chop Dukascopy Portability V2 Result",
        "",
        f"Decision: `{payload['decision']}`",
        "",
        "| Stage | Trades | Trades/day | PF | Stress PF | Stress avg R | Stress net R | DD R | Gate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in stages.to_dict("records"):
        pf = "NA" if row["profit_factor"] is None else f"{row['profit_factor']:.3f}"
        stress_pf = (
            "NA" if row["stress_profit_factor"] is None else f"{row['stress_profit_factor']:.3f}"
        )
        lines.append(
            f"| {row['stage']} | {row['trades']} | {row['trades_per_source_day']:.3f} | "
            f"{pf} | {stress_pf} | {row['average_stress_r']:.3f} | "
            f"{row['stress_net_r']:.3f} | {row['stress_drawdown_r']:.3f} | "
            f"{'PASS' if row['pass'] else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            payload["interpretation"],
            "",
            "Research only. No training or execution is authorized.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    config = json.loads(
        (ROOT / "config" / "portability_v2.json").read_text(encoding="utf-8")
    )
    lock = verify_lock(config)
    if args.verify_only:
        print(
            json.dumps(
                {
                    "verified": True,
                    "contract_sha256": lock["contract_sha256"],
                    "outcomes_opened": False,
                },
                sort_keys=True,
            )
        )
        return 0
    output = ROOT / config["outputs"]["directory"]
    result_path = output / config["outputs"]["result_json"]
    if result_path.exists():
        raise FileExistsError("V2 outcomes already exist; same-version reruns are forbidden")
    run = run_portability(config)
    rows = []
    audit = {}
    for stage in ("train", "validation", "exam", "full"):
        start, end = map(pd.Timestamp, config["windows"][stage])
        gate = config["gates"][stage]
        metrics = stage_metrics(
            run.trades,
            run.source_m5,
            start,
            end,
            int(gate["top_winners_removed"]),
        )
        passed, checks = evaluate_gate(metrics, gate)
        rows.append({"stage": stage, "pass": passed, **metrics})
        audit[stage] = {"pass": passed, "checks": checks, "metrics": metrics}
    stages = pd.DataFrame(rows)
    passed = bool(stages["pass"].all())
    decision = (
        "RETROSPECTIVE_CHOP_M5_HIGHVOL_PORTABILITY_SURVIVOR"
        if passed
        else "CHOP_M5_HIGHVOL_DUKASCOPY_PORTABILITY_REJECTED"
    )
    interpretation = (
        "The unchanged high-volatility chop specialist passed every independent-feed chronological and cost gate. Exact MT5 parity and prospective shadow evidence are still required."
        if passed
        else "The fixed high-volatility chop specialist failed at least one independent-feed gate and is not rescued or tuned in V2."
    )
    digest = frame_digest(run.trades)
    payload = {
        "schema_version": config["schema_version"],
        "contract_sha256": lock["contract_sha256"],
        "decision": decision,
        "interpretation": interpretation,
        "gate_audit": audit,
        "signal_rows": int(len(run.signals)),
        "trade_rows": int(len(run.trades)),
        "trade_digest": digest,
        "data_evidence": run.evidence,
        "source_selection_evidence": lock["source_selection_evidence"],
        "authorization": {
            **config["research_controls"],
            "training_authorized": False,
            "execution_authorized": False,
        },
    }
    signals_path = output / config["outputs"]["signals"]
    trades_path = output / config["outputs"]["trades"]
    metrics_path = output / config["outputs"]["stage_metrics"]
    markdown_path = output / config["outputs"]["result_markdown"]
    run.signals.to_csv(signals_path, index=False, lineterminator="\n")
    run.trades.to_csv(trades_path, index=False, lineterminator="\n")
    stages.to_csv(metrics_path, index=False, lineterminator="\n")
    write_json(result_path, payload)
    markdown_path.write_text(render(payload, stages), encoding="utf-8")
    artifact_names = [
        config["outputs"]["contract_lock"],
        config["outputs"]["signals"],
        config["outputs"]["trades"],
        config["outputs"]["stage_metrics"],
        config["outputs"]["result_json"],
        config["outputs"]["result_markdown"],
    ]
    write_json(
        output / config["outputs"]["artifact_manifest"],
        {
            "schema_version": "xauusd_chop_m5_highvol_portability_v2_artifacts",
            "files": {
                name: {
                    "bytes": int((output / name).stat().st_size),
                    "sha256": sha256_file(output / name),
                }
                for name in artifact_names
            },
        },
    )
    print(json.dumps({"decision": decision, "trades": len(run.trades), "trade_digest": digest}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

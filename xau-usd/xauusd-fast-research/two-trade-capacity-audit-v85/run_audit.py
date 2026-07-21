from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from capacity import (  # noqa: E402
    canonical_hash,
    sha256_file,
    validate_ledgers,
    window_capacity,
)
from lock_contract import CONFIG, verify_lock  # noqa: E402


def main() -> int:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    contract = verify_lock(config)
    output = ROOT / str(config["outputs"]["directory"])
    paths = {
        key: output / str(config["outputs"][key])
        for key in ("windows", "rejection_reasons", "result_json", "result_markdown")
    }
    if existing := [str(path) for path in paths.values() if path.exists()]:
        raise FileExistsError(f"V85 outputs already exist: {existing}")

    sources = {
        key: REPO_ROOT / str(value["path"])
        for key, value in config["sources"].items()
    }
    v59 = json.loads(sources["v59_result"].read_text(encoding="utf-8"))
    v60 = json.loads(sources["v60_result"].read_text(encoding="utf-8"))
    if v59["decision"] != config["expected"]["v59_decision"]:
        raise ValueError("V85 V59 decision changed")
    if v60["decision"] != config["expected"]["v60_decision"]:
        raise ValueError("V85 V60 decision changed")

    core = pd.read_parquet(sources["v59_core"])
    candidates = pd.read_parquet(sources["v57_candidates"])
    decisions = pd.read_parquet(sources["v59_decisions"])
    combined = pd.read_parquet(sources["v59_trades"])
    for frame in (core, candidates, decisions, combined):
        frame["entry_time"] = pd.to_datetime(frame["entry_time"], utc=True)
    validate_ledgers(core, candidates, decisions, combined, config["expected"])

    rows: list[dict[str, Any]] = []
    reason_frames: list[pd.DataFrame] = []
    for window, bounds in config["required_windows"].items():
        row, reasons = window_capacity(
            window=window,
            start=pd.Timestamp(bounds[0]),
            end=pd.Timestamp(bounds[1]),
            core=core,
            candidates=candidates,
            decisions=decisions,
            target=float(config["target_trades_per_weekday"]),
        )
        rows.append(row)
        reason_frames.append(reasons)
    windows = pd.DataFrame(rows)
    reasons = pd.concat(reason_frames, ignore_index=True)
    all_reach = bool(windows["upper_bound_reaches_two_per_weekday"].all())
    decision = (
        "V85_SCHEDULING_CAPACITY_EXISTS_REQUIRES_UNTOUCHED_POLICY"
        if all_reach
        else "V85_EXISTING_RESERVOIR_INSUFFICIENT_FOR_TWO_PER_DAY"
    )
    result: dict[str, Any] = {
        "schema_version": "xauusd_two_trade_capacity_audit_v85_result",
        "campaign_id": config["campaign_id"],
        "decision": decision,
        "contract_sha256": contract["contract_sha256"],
        "target_trades_per_weekday": config["target_trades_per_weekday"],
        "windows": rows,
        "all_required_windows_have_mechanical_capacity": all_reach,
        "upper_bound_ignores_overlap_risk_drawdown_and_economics": True,
        "scheduling_policy_authorized": False,
        "fractional_r5_rows_excluded": config["expected"][
            "fractional_r5_rows_excluded"
        ],
        "source_hashes": {
            key: sha256_file(path) for key, path in sources.items()
        },
        **config["research_controls"],
    }
    result["result_sha256"] = canonical_hash(result, "result_sha256")

    windows.to_csv(paths["windows"], index=False, lineterminator="\n")
    reasons.to_csv(paths["rejection_reasons"], index=False, lineterminator="\n")
    paths["result_json"].write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# V85 Two-Trade Capacity Audit Result",
        "",
        f"Decision: `{decision}`",
        "",
        "| Window | Current/day | Rejected | Upper/day | Upper shortfall | Capacity |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {window} | {current_trades_per_weekday:.3f} | {rejected_addons} | "
            "{mechanical_upper_bound_trades_per_weekday:.3f} | "
            "{upper_bound_trade_shortfall} | {upper_bound_reaches_two_per_weekday} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "The upper bound counts every distinct broker-executable V57 candidate and ignores overlap, risk, drawdown, and economics.",
            "It cannot authorize admitting a rejected trade. V59/V60 remain byte-identical.",
        ]
    )
    paths["result_markdown"].write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    artifacts = {
        key: {
            "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "bytes": int(path.stat().st_size),
            "sha256": sha256_file(path),
        }
        for key, path in paths.items()
    }
    manifest = {
        "schema_version": "xauusd_two_trade_capacity_audit_v85_manifest",
        "artifacts": artifacts,
    }
    manifest_path = output / str(config["outputs"]["manifest"])
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"decision": decision, "windows": rows}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

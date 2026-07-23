from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.campaign import (  # noqa: E402
    build_candidate_manifest,
    build_or_load_h1_cache,
    manifest_sha,
    screen,
    summarize_family_results,
    write_csv,
)


def main() -> int:
    config_path = ROOT / "config" / "eurusd_thousand_strategy_campaign_v1.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    storage_root = Path(
        os.environ.get(
            config["source"]["storage_environment_variable"],
            config["source"]["default_storage_root"],
        )
    )
    if not storage_root.is_absolute() or not storage_root.exists():
        raise RuntimeError(f"External Dukascopy storage is unavailable: {storage_root}")
    outputs = ROOT / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)

    candidates = build_candidate_manifest()
    candidate_rows = [candidate.as_dict() for candidate in candidates]
    write_csv(outputs / "EURUSD_HUNT_V1_CANDIDATE_MANIFEST.csv", candidate_rows)
    contract = {
        "schema_version": "eurusd_thousand_strategy_campaign_v1_contract_lock",
        "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "candidate_manifest_sha256": manifest_sha(candidates),
        "attempts": len(candidates),
        "research_controls": config["research_controls"],
    }
    (outputs / "EURUSD_HUNT_V1_CONTRACT_LOCK.json").write_text(
        json.dumps(contract, indent=2) + "\n", encoding="utf-8", newline="\n"
    )

    frame, source_metadata = build_or_load_h1_cache(storage_root, config)
    from src.campaign import add_features

    featured = add_features(frame, config)
    metrics_rows, shortlist, selected_trades = screen(featured, candidates, config)
    write_csv(outputs / "EURUSD_HUNT_V1_DISCOVERY_METRICS.csv", metrics_rows)
    write_csv(
        outputs / "EURUSD_HUNT_V1_SHORTLIST.csv",
        shortlist,
        fieldnames=[
            "candidate_id",
            "attempt",
            "archetype",
            "direction",
            "threshold",
            "stop_atr",
            "target_r",
            "max_hold_bars",
            "sha256",
            "fit_trades",
            "fit_stress_pf",
            "confirm_trades",
            "confirm_stress_pf",
            "weakest_discovery_stress_pf",
            "worst_one_sided_p_value",
            "bh_adjusted_p_value",
            "both_stage_gates_pass",
            "fdr_gate_pass",
        ],
    )
    write_csv(
        outputs / "EURUSD_HUNT_V1_SHORTLIST_TRADES.csv",
        selected_trades,
        fieldnames=[
            "candidate_id",
            "archetype",
            "direction",
            "signal_time",
            "entry_time",
            "exit_time",
            "entry",
            "exit",
            "stop",
            "target",
            "spread_pips",
            "net_pips",
            "stress_net_pips",
            "exit_reason",
            "stage",
        ],
    )
    family_summary = summarize_family_results(metrics_rows)
    write_csv(outputs / "EURUSD_HUNT_V1_FAMILY_SUMMARY.csv", family_summary)

    result = {
        "schema_version": "eurusd_thousand_strategy_campaign_v1_result",
        "status": (
            "DISCOVERY_SHORTLIST_FROZEN_M5_VALIDATION_REQUIRED"
            if shortlist
            else "NO_DISCOVERY_SURVIVOR_STOP_V1"
        ),
        "candidate_manifest_sha256": manifest_sha(candidates),
        "attempts": len(candidates),
        "archetypes": len(family_summary),
        "source": source_metadata,
        "opened_windows": ["discovery_fit", "discovery_confirm"],
        "quarantined_windows": [
            "validation_quarantine",
            "internal_test_quarantine",
            "exam_quarantine",
        ],
        "stage_gate_pass_rows": sum(row["stage_gate_pass"] for row in metrics_rows),
        "both_window_and_fdr_survivors": len(shortlist),
        "shortlist": shortlist,
        "family_summary": family_summary,
        "boundary": {
            "h1_screen_only": True,
            "strategy_authorized": False,
            "ea_created": False,
            "mt5_run": False,
            "reviewer_involved": False,
            "chart_demo_live_shadow_touched": False,
        },
    }
    result_path = outputs / "EURUSD_HUNT_V1_RESULT.json"
    result_path.write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    lines = [
        "# EURUSD Thousand-Strategy Campaign V1 Result",
        "",
        f"Status: `{result['status']}`",
        "",
        f"- Frozen attempts: {result['attempts']:,}.",
        f"- Archetypes: {result['archetypes']}.",
        f"- H1 rows: {source_metadata['nonempty_h1_rows']:,}.",
        f"- Discovery stage-gate rows: {result['stage_gate_pass_rows']:,}.",
        f"- Both-window plus FDR shortlist: {len(shortlist):,}.",
        "",
        "## Family census",
        "",
        "| Archetype | Stage-pass rows | Both-window passes | Best stress PF (>=60 trades) |",
        "|---|---:|---:|---:|",
        *[
            f"| {row['archetype']} | {row['stage_gate_pass_rows']} | "
            f"{row['both_window_gate_pass_candidates']} | "
            f"{row['best_minimum_trade_stress_pf']:.4f} |"
            for row in family_summary
        ],
        "",
        "## Boundary",
        "",
        "This is a retrospective H1 rejection screen only. It does not authorize",
        "an EA, MT5 run, chart/demo/live/shadow activity, or strategy promotion.",
        "Only the two discovery windows were opened; later windows remain quarantined.",
        (
            "October 2024 lacks a frozen-month manifest; it remains quarantined "
            "and was not used by this campaign."
        ),
        "",
    ]
    (outputs / "EURUSD_HUNT_V1_RESULT.md").write_text(
        "\n".join(lines), encoding="utf-8", newline="\n"
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

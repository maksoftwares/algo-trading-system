"""Refresh runtime-rule and primary-entry identity metadata in exact hedge evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

import run_a1_xau_h4_adverse_r_hedge_exact as hedge


def refresh(evidence_dir: Path, control_report: Path) -> Path:
    evidence_dir = evidence_dir.resolve()
    json_path = evidence_dir / "A1_XAU_H4_ADVERSE_R_HEDGE_EXACT_20260711.json"
    md_path = evidence_dir / "A1_XAU_H4_ADVERSE_R_HEDGE_EXACT_20260711.md"
    source_manifest_path = evidence_dir / "compiled" / "source_manifest.json"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    variant = payload["variant"]
    scaled = variant == "cluster_highwater_2pct_0p8pct"
    rearm = variant == "cluster_highwater_rearm_v2_5pct_2pct"
    total_mtm = variant == "cluster_highwater_total_mtm_v3_5pct_2pct"
    if not (scaled or rearm or total_mtm):
        raise RuntimeError(f"unsupported refresh variant: {variant}")

    payload["source_manifest"] = hedge.normalize_source_manifest(
        source_manifest_path,
        scaled_highwater=scaled,
        rearm_highwater=rearm,
        total_mtm_highwater=total_mtm,
    )
    horizons = {row.name: row for row in hedge.extended.HORIZONS}
    for row in payload["results"]:
        horizon = horizons[row["horizon"]]
        candidate_log = evidence_dir / row["artifacts"]["InpDealLogFileName"]
        identity = hedge.primary_entry_identity(
            hedge.control_deal_log(control_report, horizon), candidate_log,
        )
        row["reconciliation"]["primary_entry_identity"] = identity
        row["reconciliation"]["primary_entry_identity_exact"] = identity["exact_match"]

    if total_mtm:
        payload["decision"] = hedge.evaluate_total_mtm_highwater(payload["results"])
    elif rearm:
        payload["decision"] = hedge.evaluate_rearm_highwater(payload["results"])
    else:
        payload["decision"] = hedge.evaluate_scaled_highwater(payload["results"])

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(hedge.render_markdown(payload), encoding="utf-8")
    (evidence_dir / "manifest.json").write_text(
        json.dumps({
            "status": payload["decision"]["status"],
            "artifacts": hedge.exact.manifest_artifacts(evidence_dir),
        }, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return json_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control-report", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, action="append", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    for evidence_dir in args.evidence_dir:
        print(refresh(evidence_dir, args.control_report.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

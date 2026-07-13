from __future__ import annotations

"""Build the H4 cluster hedge aligned to primary floating-P/L high-water giveback."""

import argparse
import json
from pathlib import Path
from typing import Sequence

import build_a1_xau_fee_evidence_source as fee_source
import build_a1_xau_h4_cluster_equity_hedge_source as cluster


SCHEMA_VERSION = "a1_xau_h4_cluster_highwater_hedge_source_v1"
SOURCE_COMMIT = cluster.SOURCE_COMMIT
SOURCE_SHA256 = cluster.SOURCE_SHA256
EXPERT_NAME = "A1XauH4ClusterHighwaterHedgeV1"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label} replacement expected once, found {count}")
    return text.replace(old, new, 1)


def apply_highwater(instrumented_source: bytes) -> bytes:
    text = cluster.apply_cluster_hedge(instrumented_source).decode("utf-8")
    text = replace_once(
        text,
        "bool     g_cluster_hedge_rearm_ready = true;\nint      g_atr_handle",
        "bool     g_cluster_hedge_rearm_ready = true;\ndouble   g_primary_cluster_peak_profit = 0.0;\nint      g_atr_handle",
        "primary high-water global",
    )
    text = replace_once(
        text,
        "   const double loss_pct = 100.0 * MathMax(0.0, -primary_profit) / balance;",
        "   if(primary_profit > g_primary_cluster_peak_profit)\n"
        "      g_primary_cluster_peak_profit = primary_profit;\n"
        "   const double drawdown_pct = 100.0 * MathMax(0.0, g_primary_cluster_peak_profit - primary_profit) / balance;",
        "high-water drawdown calculation",
    )
    text = replace_once(
        text,
        "      if(hedge_volume > 0.0)\n"
        "         CloseClusterHedgeVolume(hedge_volume, \"CLUSTER_HEDGE_FLAT_CLOSE\");\n"
        "      g_cluster_hedge_rearm_ready = true;\n"
        "      return;",
        "      if(hedge_volume > 0.0)\n"
        "         CloseClusterHedgeVolume(hedge_volume, \"CLUSTER_HEDGE_FLAT_CLOSE\");\n"
        "      g_cluster_hedge_rearm_ready = true;\n"
        "      g_primary_cluster_peak_profit = 0.0;\n"
        "      return;",
        "flat high-water reset",
    )
    text = text.replace("loss_pct <= InpClusterEquityHedgeReleasePct", "drawdown_pct <= InpClusterEquityHedgeReleasePct")
    text = text.replace("if(primary_profit >= 0.0)\n         g_cluster_hedge_rearm_ready = true;", "if(drawdown_pct <= 0.000001)\n         g_cluster_hedge_rearm_ready = true;")
    text = text.replace("if(loss_pct >= InpClusterEquityHedgeTriggerPct)", "if(drawdown_pct >= InpClusterEquityHedgeTriggerPct)")
    if "loss_pct" in text:
        raise RuntimeError("unconverted balance-loss trigger remains")
    return text.encode("utf-8")


def build_source(repo_root: Path, output_source: Path, manifest_path: Path) -> dict[str, object]:
    pinned = fee_source.read_source(repo_root.resolve(), commit=SOURCE_COMMIT, expected_sha256=SOURCE_SHA256)
    instrumented = fee_source.instrument_deal_fee(pinned, expected_sha256=SOURCE_SHA256)
    repaired = apply_highwater(instrumented)
    output_source.parent.mkdir(parents=True, exist_ok=True)
    output_source.write_bytes(repaired)
    payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "purpose": "h4_cluster_primary_floating_highwater_hedge_exact_mt5",
        "pinned_commit": SOURCE_COMMIT,
        "pinned_source_sha256": SOURCE_SHA256,
        "fee_instrumented_base_sha256": fee_source.sha256_bytes(instrumented),
        "repaired_source_sha256": fee_source.sha256_bytes(repaired),
        "generated_expert_name": EXPERT_NAME,
        "fixed_rule": {"primary_highwater_trigger_pct": 5.0, "primary_highwater_release_pct": 2.0, "equal_total_volume": True},
        "broker_action_authorized": False,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output-source", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(build_source(args.repo_root, args.output_source, args.manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

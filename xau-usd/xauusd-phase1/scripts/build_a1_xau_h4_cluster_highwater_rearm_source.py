"""Build the H4 high-water hedge with realization-invariant MTM/rearm state."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

import build_a1_xau_fee_evidence_source as fee_source
import build_a1_xau_h4_cluster_highwater_hedge_source as highwater


SCHEMA_VERSION = "a1_xau_h4_cluster_highwater_rearm_source_v2"
SOURCE_COMMIT = highwater.SOURCE_COMMIT
SOURCE_SHA256 = highwater.SOURCE_SHA256
EXPERT_NAME = "A1XauH4ClusterHighwaterRearmV2"


RELEASE_OLD = '''         if(CloseClusterHedgeVolume(hedge_volume, "CLUSTER_HEDGE_RELEASE_CLOSE"))
            g_cluster_hedge_rearm_ready = false;'''


RELEASE_REPAIR = '''         if(CloseClusterHedgeVolume(hedge_volume, "CLUSTER_HEDGE_RELEASE_CLOSE"))
            g_cluster_hedge_rearm_ready = true;
         return;'''


GLOBAL_OLD = '''double   g_primary_cluster_peak_profit = 0.0;
int      g_atr_handle'''


GLOBAL_REPAIR = '''double   g_primary_cluster_peak_profit = 0.0;
double   g_primary_cluster_realized_profit = 0.0;
bool     g_primary_cluster_active = false;
int      g_atr_handle'''


CALCULATION_OLD = '''   if(primary_profit > g_primary_cluster_peak_profit)
      g_primary_cluster_peak_profit = primary_profit;
   const double drawdown_pct = 100.0 * MathMax(0.0, g_primary_cluster_peak_profit - primary_profit) / balance;'''


CALCULATION_REPAIR = '''   if(primary_volume > 0.0 && !g_primary_cluster_active)
     {
      g_primary_cluster_realized_profit = 0.0;
      g_primary_cluster_peak_profit = 0.0;
      g_primary_cluster_active = true;
     }
   const double primary_cluster_total_mtm = g_primary_cluster_realized_profit + primary_profit;
   if(primary_cluster_total_mtm > g_primary_cluster_peak_profit)
      g_primary_cluster_peak_profit = primary_cluster_total_mtm;
   const double drawdown_pct = 100.0 * MathMax(0.0, g_primary_cluster_peak_profit - primary_cluster_total_mtm) / balance;'''


FLAT_OLD = '''   if(primary_volume <= 0.0)
     {
      if(hedge_volume > 0.0)
         CloseClusterHedgeVolume(hedge_volume, "CLUSTER_HEDGE_FLAT_CLOSE");
      g_cluster_hedge_rearm_ready = true;
      g_primary_cluster_peak_profit = 0.0;
      return;
     }'''


FLAT_REPAIR = '''   if(primary_volume <= 0.0)
     {
      if(hedge_volume > 0.0 &&
         !CloseClusterHedgeVolume(hedge_volume, "CLUSTER_HEDGE_FLAT_CLOSE"))
         return;
      g_cluster_hedge_rearm_ready = true;
      g_primary_cluster_peak_profit = 0.0;
      g_primary_cluster_realized_profit = 0.0;
      g_primary_cluster_active = false;
      return;
     }'''


REARM_OLD = '''   if(!g_cluster_hedge_rearm_ready)
     {
      if(drawdown_pct <= 0.000001)
         g_cluster_hedge_rearm_ready = true;
      return;
     }'''


REARM_REPAIR = '''   if(!g_cluster_hedge_rearm_ready)
      return;'''


TRANSACTION_OLD = '''   LogDealTransaction(trans.deal);
   if(transaction_magic != InpMagicNumber)
      return;'''


TRANSACTION_REPAIR = '''   if(transaction_magic == InpMagicNumber)
     {
      if(!g_primary_cluster_active)
        {
         g_primary_cluster_realized_profit = 0.0;
         g_primary_cluster_peak_profit = 0.0;
         g_primary_cluster_active = true;
        }
      g_primary_cluster_realized_profit +=
         HistoryDealGetDouble(trans.deal, DEAL_PROFIT) +
         HistoryDealGetDouble(trans.deal, DEAL_COMMISSION) +
         HistoryDealGetDouble(trans.deal, DEAL_SWAP) +
         HistoryDealGetDouble(trans.deal, DEAL_FEE);
     }
   LogDealTransaction(trans.deal);
   if(transaction_magic != InpMagicNumber)
      return;'''


def apply_total_mtm_rearm(instrumented_source: bytes) -> bytes:
    text = highwater.apply_highwater(instrumented_source).decode("utf-8")
    replacements = (
        (GLOBAL_OLD, GLOBAL_REPAIR, "total-MTM globals"),
        (CALCULATION_OLD, CALCULATION_REPAIR, "realization-invariant drawdown"),
        (FLAT_OLD, FLAT_REPAIR, "flat pending-close reset"),
        (RELEASE_OLD, RELEASE_REPAIR, "successful-release direct rearm"),
        (REARM_OLD, REARM_REPAIR, "remove stale-peak rearm lock"),
        (TRANSACTION_OLD, TRANSACTION_REPAIR, "primary realized-P/L accumulator"),
    )
    for old, new, label in replacements:
        text = highwater.replace_once(text, old, new, label)
    return text.encode("utf-8")


def build_source(repo_root: Path, output_source: Path, manifest_path: Path) -> dict[str, object]:
    pinned = fee_source.read_source(
        repo_root.resolve(), commit=SOURCE_COMMIT, expected_sha256=SOURCE_SHA256,
    )
    instrumented = fee_source.instrument_deal_fee(pinned, expected_sha256=SOURCE_SHA256)
    repaired = apply_total_mtm_rearm(instrumented)
    output_source.parent.mkdir(parents=True, exist_ok=True)
    output_source.write_bytes(repaired)
    payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "purpose": "h4_cluster_highwater_total_mtm_rearm_repair_exact_mt5",
        "pinned_commit": SOURCE_COMMIT,
        "pinned_source_sha256": SOURCE_SHA256,
        "fee_instrumented_base_sha256": fee_source.sha256_bytes(instrumented),
        "repaired_source_sha256": fee_source.sha256_bytes(repaired),
        "generated_expert_name": EXPERT_NAME,
        "fixed_rule": {
            "primary_highwater_trigger_pct": 5.0,
            "primary_highwater_release_pct": 2.0,
            "primary_metric": "cluster_realized_plus_current_floating",
            "successful_release_rearms_without_rebasing_peak": True,
            "flat_reset_waits_for_hedge_close": True,
            "equal_total_volume": True,
        },
        "broker_action_authorized": False,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
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

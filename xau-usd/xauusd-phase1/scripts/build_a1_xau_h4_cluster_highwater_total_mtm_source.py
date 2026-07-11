"""Build the H4 high-water hedge with settlement-synchronized total primary MTM."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

import build_a1_xau_fee_evidence_source as fee_source
import build_a1_xau_h4_cluster_highwater_hedge_source as highwater
import build_a1_xau_h4_cluster_highwater_rearm_source as transaction_v2


SCHEMA_VERSION = "a1_xau_h4_cluster_highwater_total_mtm_source_v3"
SOURCE_COMMIT = highwater.SOURCE_COMMIT
SOURCE_SHA256 = highwater.SOURCE_SHA256
EXPERT_NAME = "A1XauH4ClusterHighwaterTotalMtmV3"


GLOBAL_REPAIR = '''double   g_primary_cluster_peak_profit = 0.0;
double   g_primary_lifetime_realized_profit = 0.0;
double   g_primary_cluster_realized_baseline = 0.0;
double   g_primary_cluster_last_volume = 0.0;
bool     g_primary_cluster_active = false;
bool     g_primary_history_sync_required = false;
int      g_atr_handle'''


HISTORY_HELPER = r'''bool PrimaryLifetimeRealizedProfit(double &realized_profit)
  {
   realized_profit = 0.0;
   if(!HistorySelect(0, TimeCurrent()))
      return false;
   const int deals = HistoryDealsTotal();
   for(int index = 0; index < deals; index++)
     {
      const ulong deal_ticket = HistoryDealGetTicket(index);
      if(deal_ticket == 0)
         continue;
      if(HistoryDealGetString(deal_ticket, DEAL_SYMBOL) != InpTargetSymbol ||
         (long)HistoryDealGetInteger(deal_ticket, DEAL_MAGIC) != InpMagicNumber)
         continue;
      realized_profit +=
         HistoryDealGetDouble(deal_ticket, DEAL_PROFIT) +
         HistoryDealGetDouble(deal_ticket, DEAL_COMMISSION) +
         HistoryDealGetDouble(deal_ticket, DEAL_SWAP) +
         HistoryDealGetDouble(deal_ticket, DEAL_FEE);
     }
   return true;
  }

'''


CALCULATION_REPAIR = '''   const double primary_volume_step = SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_STEP);
   const bool primary_volume_changed = MathAbs(primary_volume - g_primary_cluster_last_volume) > 0.5 * primary_volume_step;
   const bool primary_settlement_tick = primary_volume_changed || g_primary_history_sync_required;
   if(primary_settlement_tick)
     {
      double synchronized_realized_profit = 0.0;
      if(!PrimaryLifetimeRealizedProfit(synchronized_realized_profit))
         return;
      g_primary_lifetime_realized_profit = synchronized_realized_profit;
      g_primary_cluster_last_volume = primary_volume;
      g_primary_history_sync_required = false;
     }
   if(primary_volume > 0.0 && !g_primary_cluster_active)
     {
      g_primary_cluster_peak_profit = 0.0;
      g_primary_cluster_active = true;
     }
   const double primary_cluster_total_mtm =
      (g_primary_lifetime_realized_profit - g_primary_cluster_realized_baseline) + primary_profit;
   if(primary_cluster_total_mtm > g_primary_cluster_peak_profit)
      g_primary_cluster_peak_profit = primary_cluster_total_mtm;
   const double drawdown_pct = 100.0 * MathMax(0.0, g_primary_cluster_peak_profit - primary_cluster_total_mtm) / balance;'''


FLAT_REPAIR = '''   if(primary_volume <= 0.0)
     {
      if(hedge_volume > 0.0 &&
         !CloseClusterHedgeVolume(hedge_volume, "CLUSTER_HEDGE_FLAT_CLOSE"))
         return;
      g_cluster_hedge_rearm_ready = true;
      g_primary_cluster_peak_profit = 0.0;
      g_primary_cluster_realized_baseline = g_primary_lifetime_realized_profit;
      g_primary_cluster_last_volume = 0.0;
      g_primary_cluster_active = false;
      return;
     }

   // Position settlement may change floating and realized P/L in different MT5
   // callbacks.  Total MTM is synchronized above; defer hedge action until the
   // following tick so one economic event cannot create a false hedge cycle.
   if(primary_settlement_tick)
      return;'''


RELEASE_REPAIR = '''         if(CloseClusterHedgeVolume(hedge_volume, "CLUSTER_HEDGE_RELEASE_CLOSE"))
            g_cluster_hedge_rearm_ready = true;
         return;'''


TRANSACTION_REPAIR = '''   if(transaction_magic == InpMagicNumber)
      g_primary_history_sync_required = true;
   LogDealTransaction(trans.deal);
   if(transaction_magic != InpMagicNumber)
      return;'''


def apply_total_mtm(instrumented_source: bytes) -> bytes:
    text = highwater.apply_highwater(instrumented_source).decode("utf-8")
    replacements = (
        (transaction_v2.GLOBAL_OLD, GLOBAL_REPAIR, "total-MTM history globals"),
        ("void ManageClusterEquityHedge()\n", HISTORY_HELPER + "void ManageClusterEquityHedge()\n", "realized-history helper"),
        (transaction_v2.CALCULATION_OLD, CALCULATION_REPAIR, "settlement-synchronized total MTM"),
        (transaction_v2.FLAT_OLD, FLAT_REPAIR, "flat reset after hedge close"),
        (transaction_v2.RELEASE_OLD, RELEASE_REPAIR, "direct hysteresis rearm"),
        (transaction_v2.REARM_OLD, transaction_v2.REARM_REPAIR, "remove stale-peak lock"),
        (transaction_v2.TRANSACTION_OLD, TRANSACTION_REPAIR, "primary history-sync flag"),
    )
    for old, new, label in replacements:
        text = highwater.replace_once(text, old, new, label)
    return text.encode("utf-8")


def build_source(repo_root: Path, output_source: Path, manifest_path: Path) -> dict[str, object]:
    pinned = fee_source.read_source(
        repo_root.resolve(), commit=SOURCE_COMMIT, expected_sha256=SOURCE_SHA256,
    )
    instrumented = fee_source.instrument_deal_fee(pinned, expected_sha256=SOURCE_SHA256)
    repaired = apply_total_mtm(instrumented)
    output_source.parent.mkdir(parents=True, exist_ok=True)
    output_source.write_bytes(repaired)
    payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "purpose": "h4_cluster_highwater_settlement_synchronized_total_mtm_exact_mt5",
        "pinned_commit": SOURCE_COMMIT,
        "pinned_source_sha256": SOURCE_SHA256,
        "fee_instrumented_base_sha256": fee_source.sha256_bytes(instrumented),
        "repaired_source_sha256": fee_source.sha256_bytes(repaired),
        "generated_expert_name": EXPERT_NAME,
        "fixed_rule": {
            "primary_highwater_trigger_pct": 5.0,
            "primary_highwater_release_pct": 2.0,
            "primary_metric": "history_synchronized_cluster_realized_plus_current_floating",
            "successful_release_rearms_without_rebasing_peak": True,
            "settlement_tick_defers_hedge_action": True,
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

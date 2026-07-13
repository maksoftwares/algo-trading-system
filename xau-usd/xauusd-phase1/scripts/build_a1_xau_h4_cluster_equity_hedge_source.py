from __future__ import annotations

"""Build the preregistered H4 cluster-equity hedge from the pinned source."""

import argparse
import json
from pathlib import Path
from typing import Sequence

import build_a1_xau_fee_evidence_source as fee_source
import build_a1_xau_h4_adverse_r_hedge_source as per_ticket
import build_a1_xau_h4_episode_repair_source as episode


SCHEMA_VERSION = "a1_xau_h4_cluster_equity_hedge_source_v1"
SOURCE_COMMIT = episode.SOURCE_COMMIT
SOURCE_SHA256 = episode.SOURCE_SHA256
EXPERT_NAME = "A1XauH4ClusterEquityHedgeV1"


INPUTS = per_ticket.INPUT_ANCHOR + r'''
input bool   InpClusterEquityHedgeEnabled      = true;
input long   InpClusterEquityHedgeMagicNumber  = 932202;
input double InpClusterEquityHedgeTriggerPct   = 5.00;
input double InpClusterEquityHedgeReleasePct   = 2.00;'''


GLOBALS = r'''CTrade   g_trade;
CTrade   g_hedge_trade;
bool     g_cluster_hedge_rearm_ready = true;
int      g_atr_handle = INVALID_HANDLE;'''


HELPERS = r'''double NormalizeHedgeVolume(const double requested)
  {
   const double minimum = SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_MIN);
   const double maximum = SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_MAX);
   const double step = SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_STEP);
   if(requested <= 0.0 || minimum <= 0.0 || step <= 0.0)
      return 0.0;
   double volume = MathFloor(requested / step + 0.0000001) * step;
   volume = MathMin(volume, maximum);
   if(volume < minimum)
      return 0.0;
   return NormalizeDouble(volume, 2);
  }

void PrimaryClusterState(double &volume, double &floating_profit)
  {
   volume = 0.0;
   floating_profit = 0.0;
   for(int index = PositionsTotal() - 1; index >= 0; index--)
     {
      const ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetString(POSITION_SYMBOL) != InpTargetSymbol ||
         PositionGetInteger(POSITION_MAGIC) != InpMagicNumber ||
         (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE) != POSITION_TYPE_BUY)
         continue;
      volume += PositionGetDouble(POSITION_VOLUME);
      floating_profit += PositionGetDouble(POSITION_PROFIT) + PositionGetDouble(POSITION_SWAP);
     }
  }

double ClusterHedgeVolume()
  {
   double volume = 0.0;
   for(int index = PositionsTotal() - 1; index >= 0; index--)
     {
      const ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetString(POSITION_SYMBOL) == InpTargetSymbol &&
         PositionGetInteger(POSITION_MAGIC) == InpClusterEquityHedgeMagicNumber)
         volume += PositionGetDouble(POSITION_VOLUME);
     }
   return volume;
  }

bool CloseClusterHedgeVolume(double volume_to_close, const string action_prefix)
  {
   // Risk-reducing closes are deferred, not discarded, through the broker's daily
   // closed session.  ManageClusterEquityHedge retries on the first executable tick.
   if(!CurrentTradeSessionOpen())
      return false;
   double remaining = NormalizeHedgeVolume(volume_to_close);
   const double minimum = SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_MIN);
   const double step = SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_STEP);
   for(int index = PositionsTotal() - 1; index >= 0 && remaining >= minimum - 0.5 * step; index--)
     {
      const ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetString(POSITION_SYMBOL) != InpTargetSymbol ||
         PositionGetInteger(POSITION_MAGIC) != InpClusterEquityHedgeMagicNumber)
         continue;
      const double position_volume = PositionGetDouble(POSITION_VOLUME);
      const double close_volume = NormalizeHedgeVolume(MathMin(position_volume, remaining));
      if(close_volume <= 0.0)
         continue;
      const bool full_close = close_volume >= position_volume - 0.5 * step;
      const bool closed = full_close
         ? g_hedge_trade.PositionClose(ticket, InpDeviationPoints)
         : g_hedge_trade.PositionClosePartial(ticket, close_volume, InpDeviationPoints);
      LogManagement(closed ? action_prefix + "_OK" : action_prefix + "_FAIL", "SHORT", ticket, close_volume, PositionGetDouble(POSITION_PRICE_OPEN), PositionGetDouble(POSITION_PRICE_CURRENT), 0.0, 0.0, 0.0, 0.0, 0.0, (long)g_hedge_trade.ResultRetcode(), closed ? "pass" : "cluster_hedge_close_failed", InpClusterEquityHedgeTriggerPct, InpClusterEquityHedgeReleasePct);
      if(!closed)
         return false;
      remaining = NormalizeDouble(remaining - close_volume, 2);
     }
   return remaining < minimum - 0.5 * step;
  }

bool OpenClusterHedgeVolume(const double requested, const string action_prefix)
  {
   if(!CurrentTradeSessionOpen())
      return false;
   const double volume = NormalizeHedgeVolume(requested);
   if(volume <= 0.0)
      return false;
   const bool opened = g_hedge_trade.Sell(volume, InpTargetSymbol, 0.0, 0.0, 0.0, "H4_CLUSTER_HEDGE");
   LogManagement(opened ? action_prefix + "_OK" : action_prefix + "_FAIL", "SHORT", g_hedge_trade.ResultOrder(), volume, 0.0, SymbolInfoDouble(InpTargetSymbol, SYMBOL_BID), 0.0, 0.0, 0.0, 0.0, 0.0, (long)g_hedge_trade.ResultRetcode(), opened ? "pass" : "cluster_hedge_open_failed", InpClusterEquityHedgeTriggerPct, InpClusterEquityHedgeReleasePct);
   return opened;
  }

void ManageClusterEquityHedge()
  {
   if(!InpClusterEquityHedgeEnabled)
      return;
   double primary_volume = 0.0;
   double primary_profit = 0.0;
   PrimaryClusterState(primary_volume, primary_profit);
   double hedge_volume = ClusterHedgeVolume();
   const double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   if(balance <= 0.0)
      return;
   const double loss_pct = 100.0 * MathMax(0.0, -primary_profit) / balance;

   if(primary_volume <= 0.0)
     {
      if(hedge_volume > 0.0)
         CloseClusterHedgeVolume(hedge_volume, "CLUSTER_HEDGE_FLAT_CLOSE");
      g_cluster_hedge_rearm_ready = true;
      return;
     }

   if(hedge_volume > 0.0)
     {
      if(loss_pct <= InpClusterEquityHedgeReleasePct)
        {
         if(CloseClusterHedgeVolume(hedge_volume, "CLUSTER_HEDGE_RELEASE_CLOSE"))
            g_cluster_hedge_rearm_ready = false;
         return;
        }
      const double difference = NormalizeDouble(primary_volume - hedge_volume, 2);
      const double half_step = 0.5 * SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_STEP);
      if(difference > half_step)
         OpenClusterHedgeVolume(difference, "CLUSTER_HEDGE_REBALANCE_OPEN");
      else if(difference < -half_step)
         CloseClusterHedgeVolume(-difference, "CLUSTER_HEDGE_REBALANCE_CLOSE");
      return;
     }

   if(!g_cluster_hedge_rearm_ready)
     {
      if(primary_profit >= 0.0)
         g_cluster_hedge_rearm_ready = true;
      return;
     }
   if(loss_pct >= InpClusterEquityHedgeTriggerPct)
     {
      if(OpenClusterHedgeVolume(primary_volume, "CLUSTER_HEDGE_TRIGGER_OPEN"))
         g_cluster_hedge_rearm_ready = false;
     }
  }

'''


ON_INIT_REPLACEMENT = r'''   if(InpClusterEquityHedgeEnabled && AccountInfoInteger(ACCOUNT_MARGIN_MODE) != ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)
     {
      LogStartup("INIT_FAILED_HEDGING_MARGIN_MODE_REQUIRED");
      return INIT_FAILED;
     }
   g_trade.SetExpertMagicNumber(InpMagicNumber);
   g_trade.SetDeviationInPoints(InpDeviationPoints);
   g_hedge_trade.SetExpertMagicNumber(InpClusterEquityHedgeMagicNumber);
   g_hedge_trade.SetDeviationInPoints(InpDeviationPoints);'''


ON_TICK_REPLACEMENT = r'''void OnTick()
  {
   ManageClusterEquityHedge();
   ManageOpenPositions();'''


LOG_DEAL_FILTER_REPLACEMENT = r'''   const long deal_magic = (long)HistoryDealGetInteger(deal_ticket, DEAL_MAGIC);
   if((deal_magic != InpMagicNumber && deal_magic != InpClusterEquityHedgeMagicNumber) ||
      HistoryDealGetString(deal_ticket, DEAL_SYMBOL) != InpTargetSymbol)
      return;'''


TRANSACTION_FILTER_REPLACEMENT = r'''   const long transaction_magic = (long)HistoryDealGetInteger(trans.deal, DEAL_MAGIC);
   if((transaction_magic != InpMagicNumber && transaction_magic != InpClusterEquityHedgeMagicNumber) ||
      HistoryDealGetString(trans.deal, DEAL_SYMBOL) != InpTargetSymbol)
      return;
   LogDealTransaction(trans.deal);
   if(transaction_magic != InpMagicNumber)
      return;

   if(!InpSplitEntryEnabled'''


def apply_cluster_hedge(instrumented_source: bytes) -> bytes:
    text = instrumented_source.decode("utf-8")
    replace = per_ticket.replace_once
    text = replace(text, per_ticket.INPUT_ANCHOR, INPUTS, "cluster inputs")
    text = replace(text, per_ticket.GLOBALS_ANCHOR, GLOBALS, "cluster globals")
    text = replace(text, "int OnInit()\n", episode.SESSION_HELPER + HELPERS + "int OnInit()\n", "cluster helpers")
    text = replace(text, per_ticket.ON_INIT_ANCHOR, ON_INIT_REPLACEMENT, "cluster initialization")
    text = replace(text, per_ticket.ON_TICK_ANCHOR, ON_TICK_REPLACEMENT, "cluster tick management")
    text = replace(text, per_ticket.LOG_DEAL_FILTER, LOG_DEAL_FILTER_REPLACEMENT, "cluster deal logging")
    text = replace(text, per_ticket.TRANSACTION_FILTER, TRANSACTION_FILTER_REPLACEMENT, "cluster transaction logging")
    text = replace(text, per_ticket.MAGIC_VALUE_ANCHOR, per_ticket.MAGIC_VALUE_REPLACEMENT, "actual deal magic logging")
    text = replace(text, episode.SESSION_GUARD_ANCHOR, episode.SESSION_GUARD_REPLACEMENT, "market-session expiry")
    return text.encode("utf-8")


def build_source(repo_root: Path, output_source: Path, manifest_path: Path) -> dict[str, object]:
    pinned = fee_source.read_source(repo_root.resolve(), commit=SOURCE_COMMIT, expected_sha256=SOURCE_SHA256)
    instrumented = fee_source.instrument_deal_fee(pinned, expected_sha256=SOURCE_SHA256)
    repaired = apply_cluster_hedge(instrumented)
    output_source.parent.mkdir(parents=True, exist_ok=True)
    output_source.write_bytes(repaired)
    payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "purpose": "h4_cluster_equity_hedge_exact_mt5",
        "pinned_commit": SOURCE_COMMIT,
        "pinned_source_sha256": SOURCE_SHA256,
        "fee_instrumented_base_sha256": fee_source.sha256_bytes(instrumented),
        "repaired_source_sha256": fee_source.sha256_bytes(repaired),
        "generated_expert_name": EXPERT_NAME,
        "fixed_rule": {"trigger_balance_pct": 5.0, "release_balance_pct": 2.0, "equal_total_volume": True},
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

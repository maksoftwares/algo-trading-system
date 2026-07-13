from __future__ import annotations

"""Build the preregistered per-position H4 adverse-R hedge from pinned source."""

import argparse
import json
from pathlib import Path
from typing import Sequence

import build_a1_xau_fee_evidence_source as fee_source
import build_a1_xau_h4_episode_repair_source as episode


SCHEMA_VERSION = "a1_xau_h4_adverse_r_hedge_source_v1"
SOURCE_COMMIT = episode.SOURCE_COMMIT
SOURCE_SHA256 = episode.SOURCE_SHA256
EXPERT_NAME = "A1XauH4AdverseRHedgeV1"


class HedgeSourceError(RuntimeError):
    pass


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise HedgeSourceError(f"{label} replacement expected once, found {count}")
    return text.replace(old, new, 1)


INPUT_ANCHOR = "input double InpRiskAmountUsd                 = 0.00;"
INPUTS = INPUT_ANCHOR + r'''
input bool   InpAdverseRHedgeEnabled           = true;
input long   InpAdverseRHedgeMagicNumber       = 932201;
input double InpAdverseRHedgeTriggerR           = 0.25;
input double InpAdverseRHedgeRecoveryR          = 0.00;'''


GLOBALS_ANCHOR = r'''CTrade   g_trade;
int      g_atr_handle = INVALID_HANDLE;'''
GLOBALS = r'''CTrade   g_trade;
CTrade   g_hedge_trade;
ulong    g_hedge_cycle_primary_tickets[];
int      g_atr_handle = INVALID_HANDLE;'''


HEDGE_HELPERS = r'''bool HedgeCycleDone(const ulong primary_ticket)
  {
   for(int index = 0; index < ArraySize(g_hedge_cycle_primary_tickets); index++)
      if(g_hedge_cycle_primary_tickets[index] == primary_ticket)
         return true;
   return false;
  }

void MarkHedgeCycleDone(const ulong primary_ticket)
  {
   if(HedgeCycleDone(primary_ticket))
      return;
   const int size = ArraySize(g_hedge_cycle_primary_tickets);
   ArrayResize(g_hedge_cycle_primary_tickets, size + 1);
   g_hedge_cycle_primary_tickets[size] = primary_ticket;
  }

string HedgeComment(const ulong primary_ticket)
  {
   return "H4H_" + IntegerToString((long)primary_ticket);
  }

ulong PrimaryTicketFromHedgeComment(const string comment)
  {
   if(StringFind(comment, "H4H_") != 0)
      return 0;
   return (ulong)StringToInteger(StringSubstr(comment, 4));
  }

bool FindActiveHedge(const ulong primary_ticket, ulong &hedge_ticket)
  {
   hedge_ticket = 0;
   const string expected_comment = HedgeComment(primary_ticket);
   for(int index = PositionsTotal() - 1; index >= 0; index--)
     {
      const ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetString(POSITION_SYMBOL) == InpTargetSymbol &&
         PositionGetInteger(POSITION_MAGIC) == InpAdverseRHedgeMagicNumber &&
         PositionGetString(POSITION_COMMENT) == expected_comment)
        {
         hedge_ticket = ticket;
         return true;
        }
     }
   return false;
  }

void ManageAdverseRHedges()
  {
   if(!InpAdverseRHedgeEnabled)
      return;

   // Reconcile orphan hedges first after their primary long closed at SL/TP.
   for(int index = PositionsTotal() - 1; index >= 0; index--)
     {
      const ulong hedge_ticket = PositionGetTicket(index);
      if(hedge_ticket == 0 || !PositionSelectByTicket(hedge_ticket))
         continue;
      if(PositionGetString(POSITION_SYMBOL) != InpTargetSymbol ||
         PositionGetInteger(POSITION_MAGIC) != InpAdverseRHedgeMagicNumber)
         continue;
      const ulong primary_ticket = PrimaryTicketFromHedgeComment(PositionGetString(POSITION_COMMENT));
      if(primary_ticket > 0 && PositionSelectByTicket(primary_ticket))
         continue;
      const double volume = PositionGetDouble(POSITION_VOLUME);
      const double entry = PositionGetDouble(POSITION_PRICE_OPEN);
      const double current = PositionGetDouble(POSITION_PRICE_CURRENT);
      const bool closed = g_hedge_trade.PositionClose(hedge_ticket, InpDeviationPoints);
      LogManagement(closed ? "ADVERSE_HEDGE_ORPHAN_CLOSE_OK" : "ADVERSE_HEDGE_ORPHAN_CLOSE_FAIL", "SHORT", hedge_ticket, volume, entry, current, 0.0, 0.0, 0.0, 0.0, 0.0, (long)g_hedge_trade.ResultRetcode(), closed ? "pass" : "hedge_orphan_close_failed", InpAdverseRHedgeTriggerR, InpAdverseRHedgeRecoveryR);
     }

   const int position_count = PositionsTotal();
   for(int index = position_count - 1; index >= 0; index--)
     {
      const ulong primary_ticket = PositionGetTicket(index);
      if(primary_ticket == 0 || !PositionSelectByTicket(primary_ticket))
         continue;
      if(PositionGetString(POSITION_SYMBOL) != InpTargetSymbol ||
         PositionGetInteger(POSITION_MAGIC) != InpMagicNumber ||
         (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE) != POSITION_TYPE_BUY)
         continue;
      const double volume = PositionGetDouble(POSITION_VOLUME);
      const double entry = PositionGetDouble(POSITION_PRICE_OPEN);
      const double current = PositionGetDouble(POSITION_PRICE_CURRENT);
      const double stop = PositionGetDouble(POSITION_SL);
      const double risk = entry - stop;
      if(volume <= 0.0 || entry <= 0.0 || current <= 0.0 || stop <= 0.0 || risk <= 0.0)
         continue;
      const double unrealized_r = (current - entry) / risk;
      ulong hedge_ticket = 0;
      const bool active = FindActiveHedge(primary_ticket, hedge_ticket);
      if(active)
        {
         if(unrealized_r < InpAdverseRHedgeRecoveryR)
            continue;
         if(!PositionSelectByTicket(hedge_ticket))
            continue;
         const double hedge_entry = PositionGetDouble(POSITION_PRICE_OPEN);
         const double hedge_current = PositionGetDouble(POSITION_PRICE_CURRENT);
         const bool closed = g_hedge_trade.PositionClose(hedge_ticket, InpDeviationPoints);
         LogManagement(closed ? "ADVERSE_HEDGE_RECOVERY_CLOSE_OK" : "ADVERSE_HEDGE_RECOVERY_CLOSE_FAIL", "SHORT", hedge_ticket, volume, hedge_entry, hedge_current, 0.0, 0.0, 0.0, risk / SymbolInfoDouble(InpTargetSymbol, SYMBOL_POINT), unrealized_r, (long)g_hedge_trade.ResultRetcode(), closed ? "pass" : "hedge_recovery_close_failed", InpAdverseRHedgeTriggerR, InpAdverseRHedgeRecoveryR);
         continue;
        }
      if(HedgeCycleDone(primary_ticket) || unrealized_r > -InpAdverseRHedgeTriggerR)
         continue;
      const bool opened = g_hedge_trade.Sell(volume, InpTargetSymbol, 0.0, 0.0, 0.0, HedgeComment(primary_ticket));
      const ulong opened_ticket = g_hedge_trade.ResultOrder();
      LogManagement(opened ? "ADVERSE_HEDGE_OPEN_OK" : "ADVERSE_HEDGE_OPEN_FAIL", "SHORT", opened_ticket, volume, entry, current, stop, 0.0, 0.0, risk / SymbolInfoDouble(InpTargetSymbol, SYMBOL_POINT), unrealized_r, (long)g_hedge_trade.ResultRetcode(), opened ? "pass" : "hedge_open_failed", InpAdverseRHedgeTriggerR, InpAdverseRHedgeRecoveryR);
      if(opened)
         MarkHedgeCycleDone(primary_ticket);
     }
  }

'''


ON_INIT_ANCHOR = r'''   g_trade.SetExpertMagicNumber(InpMagicNumber);
   g_trade.SetDeviationInPoints(InpDeviationPoints);'''
ON_INIT_REPLACEMENT = r'''   if(InpAdverseRHedgeEnabled && AccountInfoInteger(ACCOUNT_MARGIN_MODE) != ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)
     {
      LogStartup("INIT_FAILED_HEDGING_MARGIN_MODE_REQUIRED");
      return INIT_FAILED;
     }
   g_trade.SetExpertMagicNumber(InpMagicNumber);
   g_trade.SetDeviationInPoints(InpDeviationPoints);
   g_hedge_trade.SetExpertMagicNumber(InpAdverseRHedgeMagicNumber);
   g_hedge_trade.SetDeviationInPoints(InpDeviationPoints);'''


ON_TICK_ANCHOR = r'''void OnTick()
  {
   ManageOpenPositions();'''
ON_TICK_REPLACEMENT = r'''void OnTick()
  {
   ManageAdverseRHedges();
   ManageOpenPositions();'''


LOG_DEAL_FILTER = r'''   if((long)HistoryDealGetInteger(deal_ticket, DEAL_MAGIC) != InpMagicNumber ||
      HistoryDealGetString(deal_ticket, DEAL_SYMBOL) != InpTargetSymbol)
      return;'''
LOG_DEAL_FILTER_REPLACEMENT = r'''   const long deal_magic = (long)HistoryDealGetInteger(deal_ticket, DEAL_MAGIC);
   if((deal_magic != InpMagicNumber && deal_magic != InpAdverseRHedgeMagicNumber) ||
      HistoryDealGetString(deal_ticket, DEAL_SYMBOL) != InpTargetSymbol)
      return;'''


TRANSACTION_FILTER = r'''   if((long)HistoryDealGetInteger(trans.deal, DEAL_MAGIC) != InpMagicNumber ||
      HistoryDealGetString(trans.deal, DEAL_SYMBOL) != InpTargetSymbol)
      return;
   LogDealTransaction(trans.deal);

   if(!InpSplitEntryEnabled'''
TRANSACTION_FILTER_REPLACEMENT = r'''   const long transaction_magic = (long)HistoryDealGetInteger(trans.deal, DEAL_MAGIC);
   if((transaction_magic != InpMagicNumber && transaction_magic != InpAdverseRHedgeMagicNumber) ||
      HistoryDealGetString(trans.deal, DEAL_SYMBOL) != InpTargetSymbol)
      return;
   LogDealTransaction(trans.deal);
   if(transaction_magic != InpMagicNumber)
      return;

   if(!InpSplitEntryEnabled'''


MAGIC_VALUE_ANCHOR = r'''   values[4] = InpTargetSymbol;
   values[5] = IntegerToString((int)InpMagicNumber);
   values[6] = IntegerToString((long)deal_ticket);'''
MAGIC_VALUE_REPLACEMENT = r'''   values[4] = InpTargetSymbol;
   values[5] = IntegerToString((long)HistoryDealGetInteger(deal_ticket, DEAL_MAGIC));
   values[6] = IntegerToString((long)deal_ticket);'''


def apply_hedge(instrumented_source: bytes) -> bytes:
    text = instrumented_source.decode("utf-8")
    text = replace_once(text, INPUT_ANCHOR, INPUTS, "hedge inputs")
    text = replace_once(text, GLOBALS_ANCHOR, GLOBALS, "hedge globals")
    text = replace_once(text, "int OnInit()\n", episode.SESSION_HELPER + HEDGE_HELPERS + "int OnInit()\n", "hedge helpers")
    text = replace_once(text, ON_INIT_ANCHOR, ON_INIT_REPLACEMENT, "hedging-mode initialization")
    text = replace_once(text, ON_TICK_ANCHOR, ON_TICK_REPLACEMENT, "hedge tick management")
    text = replace_once(text, LOG_DEAL_FILTER, LOG_DEAL_FILTER_REPLACEMENT, "hedge deal logging")
    text = replace_once(text, TRANSACTION_FILTER, TRANSACTION_FILTER_REPLACEMENT, "hedge transaction logging")
    text = replace_once(text, MAGIC_VALUE_ANCHOR, MAGIC_VALUE_REPLACEMENT, "actual deal magic logging")
    text = replace_once(text, episode.SESSION_GUARD_ANCHOR, episode.SESSION_GUARD_REPLACEMENT, "market-session expiry")
    return text.encode("utf-8")


def build_source(repo_root: Path, output_source: Path, manifest_path: Path) -> dict[str, object]:
    pinned = fee_source.read_source(repo_root.resolve(), commit=SOURCE_COMMIT, expected_sha256=SOURCE_SHA256)
    instrumented = fee_source.instrument_deal_fee(pinned, expected_sha256=SOURCE_SHA256)
    repaired = apply_hedge(instrumented)
    output_source.parent.mkdir(parents=True, exist_ok=True)
    output_source.write_bytes(repaired)
    payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "purpose": "h4_per_position_adverse_r_hedge_exact_mt5",
        "pinned_commit": SOURCE_COMMIT,
        "pinned_source_sha256": SOURCE_SHA256,
        "fee_instrumented_base_sha256": fee_source.sha256_bytes(instrumented),
        "repaired_source_sha256": fee_source.sha256_bytes(repaired),
        "generated_expert_name": EXPERT_NAME,
        "fixed_rule": {"trigger_r": -0.25, "recovery_r": 0.0, "maximum_cycles_per_primary": 1, "equal_volume": True},
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

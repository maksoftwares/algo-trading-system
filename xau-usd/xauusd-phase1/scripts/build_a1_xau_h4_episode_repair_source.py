from __future__ import annotations

"""Build the preregistered H4 episode-identity repair from the pinned source blob."""

import argparse
import json
from pathlib import Path
from typing import Sequence

import build_a1_xau_fee_evidence_source as fee_source


SCHEMA_VERSION = "a1_xau_h4_episode_identity_repair_source_v1"
SOURCE_COMMIT = "d15fc9a6b3ff18d1748428ea6519fbe58ab30721"
SOURCE_SHA256 = "bc61515d51b9414760ebe7d4d8e6bbf11fdfe760fd21d91246c0aae017449a51"
EXPERT_NAME = "A1XauH4EpisodeIdentityRepairV1"


class H4EpisodeRepairSourceError(RuntimeError):
    pass


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise H4EpisodeRepairSourceError(f"{label} replacement expected once, found {count}")
    return text.replace(old, new, 1)


SESSION_HELPER = r'''bool CurrentTradeSessionOpen()
  {
   MqlDateTime now_parts;
   if(!TimeToStruct(TimeCurrent(), now_parts))
      return false;
   const int now_seconds = now_parts.hour * 3600 + now_parts.min * 60 + now_parts.sec;
   for(uint session_index = 0; ; session_index++)
     {
      datetime session_from = 0;
      datetime session_to = 0;
      if(!SymbolInfoSessionTrade(
         InpTargetSymbol,
         (ENUM_DAY_OF_WEEK)now_parts.day_of_week,
         session_index,
         session_from,
         session_to
      ))
         break;
      MqlDateTime from_parts;
      MqlDateTime to_parts;
      if(!TimeToStruct(session_from, from_parts) || !TimeToStruct(session_to, to_parts))
         return false;
      const int from_seconds = from_parts.hour * 3600 + from_parts.min * 60 + from_parts.sec;
      const int to_seconds = to_parts.hour * 3600 + to_parts.min * 60 + to_parts.sec;
      if(from_seconds == to_seconds)
         return true;
      if(from_seconds < to_seconds && now_seconds >= from_seconds && now_seconds < to_seconds)
         return true;
      if(from_seconds > to_seconds && (now_seconds >= from_seconds || now_seconds < to_seconds))
         return true;
     }
   return false;
  }

'''


ORIGINAL_CROSS_DATA = r'''   const double h4_open = iOpen(InpTargetSymbol, PERIOD_H4, 1);
   const double h4_high = iHigh(InpTargetSymbol, PERIOD_H4, 1);
   const double h4_low = iLow(InpTargetSymbol, PERIOD_H4, 1);
   const double h4_close = iClose(InpTargetSymbol, PERIOD_H4, 1);
   const double h4_range = h4_high - h4_low;
   const double h4_body = MathAbs(h4_close - h4_open);
   const double h4_atr = IndicatorAtrPrice(PERIOD_H4, 14, 1);
   if(h4_open <= 0.0 || h4_high <= 0.0 || h4_low <= 0.0 || h4_close <= 0.0 || h4_range <= 0.0 || h4_atr <= 0.0)
      return false;'''


REPAIRED_CROSS_DATA = r'''   const double h4_open = iOpen(InpTargetSymbol, PERIOD_H4, 1);
   const double h4_high = iHigh(InpTargetSymbol, PERIOD_H4, 1);
   const double h4_low = iLow(InpTargetSymbol, PERIOD_H4, 1);
   const double h4_close = iClose(InpTargetSymbol, PERIOD_H4, 1);
   const double h4_previous_close = iClose(InpTargetSymbol, PERIOD_H4, 2);
   const double h4_range = h4_high - h4_low;
   const double h4_body = MathAbs(h4_close - h4_open);
   const double h4_atr = IndicatorAtrPrice(PERIOD_H4, 14, 1);
   if(h4_open <= 0.0 || h4_high <= 0.0 || h4_low <= 0.0 || h4_close <= 0.0 || h4_previous_close <= 0.0 || h4_range <= 0.0 || h4_atr <= 0.0)
      return false;'''


ORIGINAL_CROSS_CONDITION = r'''   const bool is_long = h4_close > box_high && h4_close > h4_open;
   const bool is_short = h4_close < box_low && h4_close < h4_open;'''


REPAIRED_CROSS_CONDITION = r'''   // Episode identity repair: an above-box state is not a fresh breakout.
   const bool is_long = h4_previous_close <= box_high && h4_close > box_high && h4_close > h4_open;
   const bool is_short = h4_previous_close >= box_low && h4_close < box_low && h4_close < h4_open;'''


ORIGINAL_LOTS_RETURN = r'''   const double risk_per_lot = (stop_distance / tick_size) * tick_value_loss;
   if(risk_per_lot <= 0.0)
      return fixed_lots;
   return NormalizeLotsForSymbol(InpRiskAmountUsd / risk_per_lot);'''


REPAIRED_LOTS_RETURN = r'''   const double risk_per_lot = (stop_distance / tick_size) * tick_value_loss;
   if(risk_per_lot <= 0.0)
      return fixed_lots;
   const double requested_lots = InpRiskAmountUsd / risk_per_lot;
   const double min_lots = SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_MIN);
   if(min_lots <= 0.0 || requested_lots + 0.0000001 < min_lots)
      return 0.0;
   return NormalizeLotsForSymbol(requested_lots);'''


ORIGINAL_INVALID_LOTS_REASON = r'''LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "invalid_order_lots");'''


REPAIRED_INVALID_LOTS_REASON = r'''LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, InpUseRiskNormalizedLots ? "minimum_lot_risk_excess" : "invalid_order_lots");'''


SESSION_GUARD_ANCHOR = r'''   double sl = 0.0;
   double tp = 0.0;
   double entry_reference = 0.0;'''


SESSION_GUARD_REPLACEMENT = r'''   if(!CurrentTradeSessionOpen())
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 10018, "market closed", 0, 0, 0.0, "market_session_closed_permanent_expiry");
      return;
     }

   double sl = 0.0;
   double tp = 0.0;
   double entry_reference = 0.0;'''


def apply_episode_repair(instrumented_source: bytes) -> bytes:
    text = instrumented_source.decode("utf-8")
    text = _replace_once(text, "void OnTick()\n", SESSION_HELPER + "void OnTick()\n", "session helper")
    text = _replace_once(text, ORIGINAL_CROSS_DATA, REPAIRED_CROSS_DATA, "H4 prior close")
    text = _replace_once(text, ORIGINAL_CROSS_CONDITION, REPAIRED_CROSS_CONDITION, "H4 transition")
    text = _replace_once(text, ORIGINAL_LOTS_RETURN, REPAIRED_LOTS_RETURN, "minimum-lot risk block")
    text = _replace_once(text, ORIGINAL_INVALID_LOTS_REASON, REPAIRED_INVALID_LOTS_REASON, "risk-block reason")
    text = _replace_once(text, SESSION_GUARD_ANCHOR, SESSION_GUARD_REPLACEMENT, "market-session guard")
    return text.encode("utf-8")


def build_source(repo_root: Path, output_source: Path, manifest_path: Path) -> dict[str, object]:
    pinned = fee_source.read_source(repo_root.resolve(), commit=SOURCE_COMMIT, expected_sha256=SOURCE_SHA256)
    instrumented = fee_source.instrument_deal_fee(pinned, expected_sha256=SOURCE_SHA256)
    repaired = apply_episode_repair(instrumented)
    output_source.parent.mkdir(parents=True, exist_ok=True)
    output_source.write_bytes(repaired)
    payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "purpose": "h4_breakout_episode_identity_repair_exact_mt5",
        "strategy_change": True,
        "pinned_commit": SOURCE_COMMIT,
        "pinned_source_sha256": SOURCE_SHA256,
        "fee_instrumented_base_sha256": fee_source.sha256_bytes(instrumented),
        "repaired_source_sha256": fee_source.sha256_bytes(repaired),
        "generated_expert_name": EXPERT_NAME,
        "fixed_repairs": [
            "completed_h4_first_cross_required",
            "single_open_position_by_config",
            "market_session_permanent_expiry",
            "minimum_lot_risk_excess_block",
        ],
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

from __future__ import annotations

"""Build the preregistered H4 aggregate stop-risk heat guard from pinned source."""

import argparse
import json
from pathlib import Path
from typing import Sequence

import build_a1_xau_fee_evidence_source as fee_source
import build_a1_xau_h4_episode_repair_source as episode


SCHEMA_VERSION = "a1_xau_h4_profit_retention_heat_source_v1"
SOURCE_COMMIT = episode.SOURCE_COMMIT
SOURCE_SHA256 = episode.SOURCE_SHA256
EXPERT_NAME = "A1XauH4ProfitRetentionHeatV1"


class HeatSourceError(RuntimeError):
    pass


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise HeatSourceError(f"{label} replacement expected once, found {count}")
    return text.replace(old, new, 1)


HEAT_INPUT_ANCHOR = "input double InpRiskAmountUsd                 = 0.00;"
HEAT_INPUT_REPLACEMENT = HEAT_INPUT_ANCHOR + "\ninput double InpMaxAggregateStopRiskPct       = 6.00;"


HEAT_HELPER = r'''bool CalculateStopRiskAccountCurrency(
   const ENUM_ORDER_TYPE order_type,
   const double volume,
   const double from_price,
   const double stop_price,
   double &risk
)
  {
   risk = 0.0;
   if(volume <= 0.0 || from_price <= 0.0 || stop_price <= 0.0)
      return false;
   double profit_at_stop = 0.0;
   if(!OrderCalcProfit(order_type, InpTargetSymbol, volume, from_price, stop_price, profit_at_stop))
      return false;
   risk = MathMax(0.0, -profit_at_stop);
   return MathIsValidNumber(risk);
  }

bool AggregateStopRiskAllows(
   const string direction,
   const double candidate_lots,
   const double candidate_entry,
   const double candidate_stop,
   double &open_risk,
   double &candidate_risk,
   double &projected_pct
)
  {
   open_risk = 0.0;
   candidate_risk = 0.0;
   projected_pct = 999.0;
   if(InpMaxAggregateStopRiskPct <= 0.0)
      return false;
   const ENUM_ORDER_TYPE candidate_type = direction == "LONG" ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   if(!CalculateStopRiskAccountCurrency(candidate_type, candidate_lots, candidate_entry, candidate_stop, candidate_risk))
      return false;
   for(int index = PositionsTotal() - 1; index >= 0; index--)
     {
      const ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         return false;
      if(PositionGetString(POSITION_SYMBOL) != InpTargetSymbol || PositionGetInteger(POSITION_MAGIC) != InpMagicNumber)
         continue;
      const double volume = PositionGetDouble(POSITION_VOLUME);
      const double current_price = PositionGetDouble(POSITION_PRICE_CURRENT);
      const double stop_price = PositionGetDouble(POSITION_SL);
      const ENUM_POSITION_TYPE position_type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      const ENUM_ORDER_TYPE order_type = position_type == POSITION_TYPE_BUY ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
      double position_risk = 0.0;
      if(!CalculateStopRiskAccountCurrency(order_type, volume, current_price, stop_price, position_risk))
         return false;
      open_risk += position_risk;
     }
   const double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   if(equity <= 0.0 || !MathIsValidNumber(open_risk + candidate_risk))
      return false;
   projected_pct = 100.0 * (open_risk + candidate_risk) / equity;
   return projected_pct <= InpMaxAggregateStopRiskPct + 0.0000001;
  }

'''


LOTS_ANCHOR = r'''   if(order_lots <= 0.0)
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "invalid_order_lots");
      return;
     }

   if(!ClaimSignalSlot(direction, signal_time, bid, ask, spread_points, close, stop_points, estimated_cost_r))'''


HEAT_GUARD = r'''   if(order_lots <= 0.0)
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "invalid_order_lots");
      return;
     }

   const double heat_entry = direction == "LONG" ? ask : bid;
   const double heat_stop = direction == "LONG"
      ? NormalizeDouble(heat_entry - stop_distance, digits)
      : NormalizeDouble(heat_entry + stop_distance, digits);
   double heat_open_risk = 0.0;
   double heat_candidate_risk = 0.0;
   double heat_projected_pct = 999.0;
   if(!AggregateStopRiskAllows(direction, order_lots, heat_entry, heat_stop, heat_open_risk, heat_candidate_risk, heat_projected_pct))
     {
      LogOrder("GUARD_BLOCK", direction, order_lots, bid, ask, spread_points, close, heat_open_risk, heat_candidate_risk, stop_points, estimated_cost_r, 0, "", 0, 0, heat_projected_pct, "aggregate_stop_risk_pct_exceeded_or_invalid");
      return;
     }
   LogOrder("HEAT_PASS", direction, order_lots, bid, ask, spread_points, close, heat_open_risk, heat_candidate_risk, stop_points, estimated_cost_r, 0, "", 0, 0, heat_projected_pct, "aggregate_stop_risk_pct_pass");

   if(!ClaimSignalSlot(direction, signal_time, bid, ask, spread_points, close, stop_points, estimated_cost_r))'''


def apply_heat_guard(instrumented_source: bytes) -> bytes:
    text = instrumented_source.decode("utf-8")
    text = _replace_once(text, HEAT_INPUT_ANCHOR, HEAT_INPUT_REPLACEMENT, "heat input")
    text = _replace_once(text, "void OnTick()\n", episode.SESSION_HELPER + HEAT_HELPER + "void OnTick()\n", "helpers")
    text = _replace_once(text, episode.SESSION_GUARD_ANCHOR, episode.SESSION_GUARD_REPLACEMENT, "session guard")
    text = _replace_once(text, LOTS_ANCHOR, HEAT_GUARD, "aggregate heat guard")
    return text.encode("utf-8")


def build_source(repo_root: Path, output_source: Path, manifest_path: Path) -> dict[str, object]:
    pinned = fee_source.read_source(repo_root.resolve(), commit=SOURCE_COMMIT, expected_sha256=SOURCE_SHA256)
    instrumented = fee_source.instrument_deal_fee(pinned, expected_sha256=SOURCE_SHA256)
    repaired = apply_heat_guard(instrumented)
    output_source.parent.mkdir(parents=True, exist_ok=True)
    output_source.write_bytes(repaired)
    payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "purpose": "h4_profit_retention_aggregate_stop_risk_guard_exact_mt5",
        "strategy_change": True,
        "pinned_commit": SOURCE_COMMIT,
        "pinned_source_sha256": SOURCE_SHA256,
        "fee_instrumented_base_sha256": fee_source.sha256_bytes(instrumented),
        "repaired_source_sha256": fee_source.sha256_bytes(repaired),
        "generated_expert_name": EXPERT_NAME,
        "fixed_repairs": ["six_pct_aggregate_equity_to_stop_heat_guard", "market_session_permanent_expiry"],
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

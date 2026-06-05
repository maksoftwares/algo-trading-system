#ifndef WR50_RISK_GUARD_MQH
#define WR50_RISK_GUARD_MQH

#include "WR50_MagicNumbers.mqh"
#include "WR50_SessionFilter.mqh"
#include "WR50_SpreadGuard.mqh"
#include "WR50_Types.mqh"

int WR50_CountOpenPositionsByMagic(const string symbol, const int magic)
{
   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetString(POSITION_SYMBOL) == symbol && (int)PositionGetInteger(POSITION_MAGIC) == magic)
         count++;
   }
   return count;
}

int WR50_CountOpenWR50Positions()
{
   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(WR50_IsWR50Magic(PositionGetInteger(POSITION_MAGIC)))
         count++;
   }
   return count;
}

bool WR50_HasSameSymbolNonWR50Exposure(const string symbol)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetString(POSITION_SYMBOL) == symbol && !WR50_IsWR50Magic(PositionGetInteger(POSITION_MAGIC)))
         return true;
   }
   return false;
}

int WR50_CountDealsTodayByMagic(const int magic)
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   dt.hour = 0;
   dt.min = 0;
   dt.sec = 0;
   datetime day_start = StructToTime(dt);
   if(!HistorySelect(day_start, TimeCurrent()))
      return 0;
   int count = 0;
   for(int i = 0; i < HistoryDealsTotal(); i++)
   {
      ulong ticket = HistoryDealGetTicket(i);
      if(ticket == 0)
         continue;
      if((int)HistoryDealGetInteger(ticket, DEAL_MAGIC) == magic && HistoryDealGetInteger(ticket, DEAL_ENTRY) == DEAL_ENTRY_IN)
         count++;
   }
   return count;
}

double WR50_DailyWR50ClosedProfit()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   dt.hour = 0;
   dt.min = 0;
   dt.sec = 0;
   datetime day_start = StructToTime(dt);
   if(!HistorySelect(day_start, TimeCurrent()))
      return 0.0;
   double profit = 0.0;
   for(int i = 0; i < HistoryDealsTotal(); i++)
   {
      ulong ticket = HistoryDealGetTicket(i);
      if(ticket == 0)
         continue;
      if(WR50_IsWR50Magic(HistoryDealGetInteger(ticket, DEAL_MAGIC)))
         profit += HistoryDealGetDouble(ticket, DEAL_PROFIT) +
                   HistoryDealGetDouble(ticket, DEAL_COMMISSION) +
                   HistoryDealGetDouble(ticket, DEAL_SWAP);
   }
   return profit;
}

double WR50_NormalizeLot(const string symbol, const double requested_lot)
{
   double min_lot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
   double max_lot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
   double step = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
   double lot = requested_lot;
   if(lot <= 0.0)
      lot = min_lot;
   if(step > 0.0)
      lot = MathFloor(lot / step) * step;
   lot = MathMax(min_lot, MathMin(max_lot, lot));
   return NormalizeDouble(lot, 2);
}

bool WR50_StopsValid(const string symbol,
                     const int direction,
                     const double entry,
                     const double sl,
                     const double tp,
                     string &reason)
{
   double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
   int stop_level_points = (int)SymbolInfoInteger(symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double min_distance = stop_level_points * point;
   if(point <= 0.0)
   {
      reason = "invalid_symbol_point";
      return false;
   }
   if(direction == WR50_DIRECTION_LONG)
   {
      if(sl >= entry || tp <= entry)
      {
         reason = "long_sl_tp_direction_invalid";
         return false;
      }
      if((entry - sl) < min_distance || (tp - entry) < min_distance)
      {
         reason = "long_sl_tp_inside_broker_stop_level";
         return false;
      }
   }
   else if(direction == WR50_DIRECTION_SHORT)
   {
      if(sl <= entry || tp >= entry)
      {
         reason = "short_sl_tp_direction_invalid";
         return false;
      }
      if((sl - entry) < min_distance || (entry - tp) < min_distance)
      {
         reason = "short_sl_tp_inside_broker_stop_level";
         return false;
      }
   }
   else
   {
      reason = "missing_direction";
      return false;
   }
   reason = "stops_ok";
   return true;
}

bool WR50_MarginSufficient(const string symbol,
                           const int direction,
                           const double lot,
                           const double entry,
                           string &reason)
{
   ENUM_ORDER_TYPE order_type = direction == WR50_DIRECTION_LONG ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   double margin = 0.0;
   if(!OrderCalcMargin(order_type, symbol, lot, entry, margin))
   {
      reason = "margin_calc_failed";
      return false;
   }
   if(AccountInfoDouble(ACCOUNT_MARGIN_FREE) < margin)
   {
      reason = "margin_insufficient";
      return false;
   }
   reason = "margin_ok";
   return true;
}

bool WR50_EntryPricePendingSideValid(const string symbol, const int direction, const double entry, string &reason)
{
   double ask = 0.0;
   double bid = 0.0;
   double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
   SymbolInfoDouble(symbol, SYMBOL_ASK, ask);
   SymbolInfoDouble(symbol, SYMBOL_BID, bid);
   if(direction == WR50_DIRECTION_LONG && entry <= ask + point)
   {
      reason = "buy_stop_entry_not_above_ask";
      return false;
   }
   if(direction == WR50_DIRECTION_SHORT && entry >= bid - point)
   {
      reason = "sell_stop_entry_not_below_bid";
      return false;
   }
   reason = "entry_side_ok";
   return true;
}

bool WR50_PassPreOrderRiskGuards(const string symbol,
                                 const int magic,
                                 const WR50Signal &signal,
                                 const double lot,
                                 const int max_spread_points,
                                 const int max_trades_per_day,
                                 const int max_open_positions_for_this_ea,
                                 const int max_open_wr50_positions_total,
                                 const double max_daily_loss_account_currency,
                                 const bool allow_shared_symbol_exposure,
                                 const int rollover_start_hour,
                                 const int rollover_start_minute,
                                 const int rollover_end_hour,
                                 const int rollover_end_minute,
                                 const string manual_blackout_file,
                                 double &current_spread_points,
                                 string &reason)
{
   if(!WR50_SpreadAllowed(symbol, max_spread_points, current_spread_points, reason))
      return false;
   if(WR50_CountOpenPositionsByMagic(symbol, magic) >= max_open_positions_for_this_ea)
   {
      reason = "max_open_positions_for_this_ea";
      return false;
   }
   if(WR50_CountOpenWR50Positions() >= max_open_wr50_positions_total)
   {
      reason = "max_open_wr50_positions_total";
      return false;
   }
   if(WR50_CountDealsTodayByMagic(magic) >= max_trades_per_day)
   {
      reason = "max_trades_per_day";
      return false;
   }
   if(max_daily_loss_account_currency > 0.0 && WR50_DailyWR50ClosedProfit() <= -max_daily_loss_account_currency)
   {
      reason = "max_daily_loss_account_currency";
      return false;
   }
   if(!allow_shared_symbol_exposure && WR50_HasSameSymbolNonWR50Exposure(symbol))
   {
      reason = "same_symbol_non_wr50_exposure";
      return false;
   }
   if(WR50_InRolloverBlackout(rollover_start_hour, rollover_start_minute, rollover_end_hour, rollover_end_minute))
   {
      reason = "rollover_blackout";
      return false;
   }
   string blackout_reason = "";
   if(WR50_InManualBlackout(manual_blackout_file, blackout_reason))
   {
      reason = blackout_reason;
      return false;
   }
   if(!WR50_StopsValid(symbol, signal.direction, signal.entry_price, signal.sl_price, signal.tp_price, reason))
      return false;
   if(!WR50_EntryPricePendingSideValid(symbol, signal.direction, signal.entry_price, reason))
      return false;
   if(!WR50_MarginSufficient(symbol, signal.direction, lot, signal.entry_price, reason))
      return false;
   reason = "risk_guards_ok";
   return true;
}

#endif

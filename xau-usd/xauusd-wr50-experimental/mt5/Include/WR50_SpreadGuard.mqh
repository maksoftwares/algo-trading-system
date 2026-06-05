#ifndef WR50_SPREAD_GUARD_MQH
#define WR50_SPREAD_GUARD_MQH

double WR50_CurrentSpreadPoints(const string symbol)
{
   double ask = 0.0;
   double bid = 0.0;
   double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
   if(point <= 0.0)
      return 999999.0;
   if(!SymbolInfoDouble(symbol, SYMBOL_ASK, ask) || !SymbolInfoDouble(symbol, SYMBOL_BID, bid))
      return 999999.0;
   return (ask - bid) / point;
}

bool WR50_SpreadAllowed(const string symbol, const int max_spread_points, double &current_spread_points, string &reason)
{
   current_spread_points = WR50_CurrentSpreadPoints(symbol);
   if(current_spread_points > (double)max_spread_points)
   {
      reason = "spread_block=true";
      return false;
   }
   reason = "spread_ok";
   return true;
}

#endif


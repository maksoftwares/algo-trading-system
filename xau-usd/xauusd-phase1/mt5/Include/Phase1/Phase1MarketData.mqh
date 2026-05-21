#ifndef PHASE1_MARKET_DATA_MQH
#define PHASE1_MARKET_DATA_MQH

#include <Phase1/Phase1Types.mqh>

class CPhase1MarketDataEngine
{
public:
   bool BuildSnapshot(const string symbol_name, Phase1MarketSnapshot &snapshot) const
   {
      Phase1ResetMarketSnapshot(snapshot);
      snapshot.symbol_name = symbol_name;
      snapshot.broker_time = TimeCurrent();
      snapshot.utc_time = TimeGMT();
      snapshot.local_time = TimeLocal();
      snapshot.m5_bar_time = iTime(symbol_name, PERIOD_M5, 0);
      snapshot.bid = SymbolInfoDouble(symbol_name, SYMBOL_BID);
      snapshot.ask = SymbolInfoDouble(symbol_name, SYMBOL_ASK);
      snapshot.point = SymbolInfoDouble(symbol_name, SYMBOL_POINT);
      snapshot.digits = (int)SymbolInfoInteger(symbol_name, SYMBOL_DIGITS);

      if(snapshot.point > 0.0)
         snapshot.spread_points = (snapshot.ask - snapshot.bid) / snapshot.point;

      MqlTick tick;
      snapshot.tick_ok = SymbolInfoTick(symbol_name, tick);
      if(snapshot.tick_ok)
         snapshot.stale_seconds = (int)(snapshot.broker_time - tick.time);

      long trade_mode = SymbolInfoInteger(symbol_name, SYMBOL_TRADE_MODE);
      snapshot.symbol_tradeable = (trade_mode != SYMBOL_TRADE_MODE_DISABLED);

      return snapshot.tick_ok && snapshot.point > 0.0 && snapshot.m5_bar_time > 0;
   }
};

#endif

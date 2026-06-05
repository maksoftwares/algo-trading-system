#ifndef WR50_TYPES_MQH
#define WR50_TYPES_MQH

#define WR50_DIRECTION_NONE 0
#define WR50_DIRECTION_LONG 1
#define WR50_DIRECTION_SHORT -1

struct WR50Signal
{
   bool has_signal;
   int direction;
   double entry_price;
   double sl_price;
   double tp_price;
   double atr_points;
   double entry_spread_points;
   string entry_type;
   string reason_code;
   string session_bucket;
   string block_reason;
};

void WR50_ResetSignal(WR50Signal &signal)
{
   signal.has_signal = false;
   signal.direction = WR50_DIRECTION_NONE;
   signal.entry_price = 0.0;
   signal.sl_price = 0.0;
   signal.tp_price = 0.0;
   signal.atr_points = 0.0;
   signal.entry_spread_points = 0.0;
   signal.entry_type = "";
   signal.reason_code = "";
   signal.session_bucket = "";
   signal.block_reason = "";
}

string WR50_BoolText(const bool value)
{
   return value ? "true" : "false";
}

string WR50_DirectionText(const int direction)
{
   if(direction == WR50_DIRECTION_LONG)
      return "BUY";
   if(direction == WR50_DIRECTION_SHORT)
      return "SELL";
   return "NONE";
}

#endif


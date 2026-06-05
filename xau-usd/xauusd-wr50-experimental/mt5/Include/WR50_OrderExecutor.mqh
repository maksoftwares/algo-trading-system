#ifndef WR50_ORDER_EXECUTOR_MQH
#define WR50_ORDER_EXECUTOR_MQH

#include "WR50_Types.mqh"

bool WR50_SendPendingOrder(const string symbol,
                           const int magic,
                           const WR50Signal &signal,
                           const double lot,
                           const string comment,
                           const int expiry_m5_bars,
                           MqlTradeResult &result,
                           string &reason)
{
   ZeroMemory(result);
   if(!signal.has_signal)
   {
      reason = "no_signal";
      return false;
   }
   if(signal.sl_price <= 0.0 || signal.tp_price <= 0.0)
   {
      reason = "hard_sl_tp_required";
      return false;
   }
   if(StringLen(comment) > 31 || StringFind(comment, "WR50|") != 0)
   {
      reason = "comment_invalid";
      return false;
   }

   MqlTradeRequest request;
   ZeroMemory(request);
   request.action = TRADE_ACTION_PENDING;
   request.symbol = symbol;
   request.magic = magic;
   request.volume = lot;
   request.price = signal.entry_price;
   request.sl = signal.sl_price;
   request.tp = signal.tp_price;
   request.deviation = 20;
   request.comment = comment;
   request.type = signal.direction == WR50_DIRECTION_LONG ? ORDER_TYPE_BUY_STOP : ORDER_TYPE_SELL_STOP;
   request.type_filling = ORDER_FILLING_RETURN;
   request.type_time = ORDER_TIME_SPECIFIED;
   request.expiration = TimeCurrent() + (expiry_m5_bars * PeriodSeconds(PERIOD_M5));

   ResetLastError();
   bool sent = OrderSend(request, result);
   if(!sent)
   {
      reason = "OrderSend_failed:" + IntegerToString(GetLastError());
      ResetLastError();
      return false;
   }
   if(result.retcode != TRADE_RETCODE_PLACED && result.retcode != TRADE_RETCODE_DONE)
   {
      reason = "order_rejected_retcode:" + IntegerToString((int)result.retcode);
      return false;
   }
   reason = "order_sent";
   return true;
}

#endif


#property strict
#property version   "1.00"
#property description "Development-only exact MT5 execution check for the single locked R6 event."

#include <Trade/Trade.mqh>

input string InpSignalTime = "2024.08.30 17:00:00";
input double InpStructuralStop = 2507.65;
input double InpRiskReward = 2.00;
input double InpLots = 0.01;
input ulong InpMagic = 926001;

CTrade trade;
datetime signal_time = 0;
bool attempted = false;

int OnInit()
{
   if(!MQLInfoInteger(MQL_TESTER))
      return INIT_FAILED;
   signal_time = StringToTime(InpSignalTime);
   if(signal_time <= 0 || InpStructuralStop <= 0.0 || InpRiskReward <= 0.0 || InpLots <= 0.0)
      return INIT_PARAMETERS_INCORRECT;
   trade.SetExpertMagicNumber(InpMagic);
   trade.SetTypeFillingBySymbol(_Symbol);
   return INIT_SUCCEEDED;
}

void OnTick()
{
   if(attempted || TimeCurrent() < signal_time)
      return;

   attempted = true;
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick) || tick.bid <= 0.0 || tick.ask <= 0.0)
   {
      Print("R6_SINGLE_EVENT_NO_TICK error=", GetLastError());
      return;
   }

   const int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   const double stop = NormalizeDouble(InpStructuralStop, digits);
   const double risk = stop - tick.bid;
   if(risk <= 0.0 || stop <= tick.ask)
   {
      Print("R6_SINGLE_EVENT_INVALID_RISK bid=", tick.bid, " ask=", tick.ask, " stop=", stop);
      return;
   }
   const double target = NormalizeDouble(tick.bid - InpRiskReward * risk, digits);
   const bool sent = trade.Sell(InpLots, _Symbol, 0.0, stop, target, "R6_OWNER_SCREEN");
   Print(
      "R6_SINGLE_EVENT_ORDER sent=", sent,
      " retcode=", trade.ResultRetcode(),
      " description=", trade.ResultRetcodeDescription(),
      " bid=", DoubleToString(tick.bid, digits),
      " ask=", DoubleToString(tick.ask, digits),
      " stop=", DoubleToString(stop, digits),
      " target=", DoubleToString(target, digits)
   );
}

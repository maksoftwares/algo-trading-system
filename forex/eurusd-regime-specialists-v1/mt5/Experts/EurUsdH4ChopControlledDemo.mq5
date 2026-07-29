#property strict
#property version   "1.10"
#property description "EURUSD H4-chop Asia/London short controlled demo observer"

#include <Trade/Trade.mqh>

input string InpRunId = "EURUSD_H4_CHOP_PROSPECTIVE_V1";
input string InpTargetSymbol = "EURUSD";
input long InpMagicNumber = 26073041;
input string InpOrderComment = "EUH4CHOP_DEMO_V1";
input bool InpShadowMode = true;
input bool InpEnableDemoOrders = false;
input bool InpEmergencyStop = true;
input bool InpTesterOrdersEnabled = false;
input long InpAllowedAccountLogin = 0;
input string InpAllowedServer = "";
input string InpDemoArmToken = "DISARMED";
input string InpProspectiveStartUtc = "2026.08.01 00:00";
input int InpBrokerUtcOffsetHours = 0;
input double InpFixedLots = 0.01;
input double InpMaximumSpreadPips = 2.0;
input int InpMaximumHoldH1Bars = 12;
input int InpMaximumTradesPerUtcDay = 1;
input double InpMaximumDailyClosedLossUsd = 10.0;
input double InpMaximumRolling5DayClosedLossUsd = 20.0;
input double InpMaximumSessionEquityDrawdownUsd = 25.0;
input int InpDeviationPoints = 10;
input string InpAuditLogName = "EURUSD_H4_CHOP_CONTROLLED_DEMO.csv";

const int ATR_PERIOD = 14;
const int ADX_PERIOD = 14;
const int EMA_PERIOD = 50;
const int BASELINE_BARS = 504;
const double BODY_MINIMUM = 0.35;
const double STOP_ATR_MULTIPLE = 1.75;
const double TARGET_R_MULTIPLE = 1.25;
const string ARM_TOKEN = "I_ACCEPT_DEMO_001";

CTrade trade;
int h1Atr = INVALID_HANDLE;
int h4Atr = INVALID_HANDLE;
int h4Adx = INVALID_HANDLE;
int h4Ema = INVALID_HANDLE;
datetime lastH1Open = 0;
int lastSignalDate = 0;
double sessionStartEquity = 0.0;
string mutexName = "";
bool mutexOwned = false;

string BoolText(const bool value)
{
   return value ? "true" : "false";
}

double PipSize()
{
   return (_Digits == 3 || _Digits == 5) ? 10.0 * _Point : _Point;
}

datetime UtcNow()
{
   if((bool)MQLInfoInteger(MQL_TESTER))
      return TimeCurrent() - InpBrokerUtcOffsetHours * 3600;
   return TimeGMT();
}

int UtcDateKey(const datetime brokerTime, int &hour)
{
   datetime utcTime = brokerTime - InpBrokerUtcOffsetHours * 3600;
   MqlDateTime parts;
   TimeToStruct(utcTime, parts);
   hour = parts.hour;
   return parts.year * 10000 + parts.mon * 100 + parts.day;
}

void Audit(
   const string eventName,
   const string detail,
   const string side = "NONE",
   const double entry = 0.0,
   const double stop = 0.0,
   const double target = 0.0
)
{
   int handle = FileOpen(
      InpAuditLogName,
      FILE_READ | FILE_WRITE | FILE_CSV | FILE_COMMON | FILE_SHARE_READ,
      ','
   );
   if(handle == INVALID_HANDLE)
   {
      PrintFormat("EURUSD_H4_CHOP audit open failed err=%d", GetLastError());
      return;
   }
   if(FileSize(handle) == 0)
      FileWrite(
         handle,
         "recorded_at_broker",
         "recorded_at_utc",
         "run_id",
         "event",
         "detail",
         "account",
         "server",
         "symbol",
         "magic",
         "side",
         "entry",
         "stop",
         "target",
         "shadow",
         "orders_enabled",
         "emergency_stop"
      );
   FileSeek(handle, 0, SEEK_END);
   FileWrite(
      handle,
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      TimeToString(UtcNow(), TIME_DATE | TIME_SECONDS),
      InpRunId,
      eventName,
      detail,
      (long)AccountInfoInteger(ACCOUNT_LOGIN),
      AccountInfoString(ACCOUNT_SERVER),
      _Symbol,
      InpMagicNumber,
      side,
      DoubleToString(entry, _Digits),
      DoubleToString(stop, _Digits),
      DoubleToString(target, _Digits),
      BoolText(InpShadowMode),
      BoolText(InpEnableDemoOrders),
      BoolText(InpEmergencyStop)
   );
   FileClose(handle);
}

double Quantile(double &values[], const double q)
{
   double copy[];
   ArrayCopy(copy, values);
   ArraySort(copy);
   int count = ArraySize(copy);
   if(count == 0)
      return 0.0;
   double position = q * (count - 1);
   int low = (int)MathFloor(position);
   int high = (int)MathCeil(position);
   if(low == high)
      return copy[low];
   return copy[low] + (position - low) * (copy[high] - copy[low]);
}

bool CopyIndicator(
   const int handle,
   const int buffer,
   const int startShift,
   const int count,
   double &values[]
)
{
   ArrayResize(values, count);
   ArraySetAsSeries(values, true);
   return CopyBuffer(handle, buffer, startShift, count, values) == count;
}

bool OwnedChopRegimePass()
{
   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   if(CopyRates(_Symbol, PERIOD_H4, 1, BASELINE_BARS + 30, rates) <
      BASELINE_BARS + 25)
      return false;

   double atr[], adx[], ema[];
   if(!CopyIndicator(h4Atr, 0, 1, BASELINE_BARS + 1, atr))
      return false;
   if(!CopyIndicator(h4Adx, 0, 1, 1, adx))
      return false;
   if(!CopyIndicator(h4Ema, 0, 1, 7, ema))
      return false;
   double currentAtr = atr[0];
   if(currentAtr <= 0.0 || adx[0] <= 0.0)
      return false;

   double priorAtr[];
   ArrayResize(priorAtr, BASELINE_BARS);
   for(int i = 0; i < BASELINE_BARS; ++i)
      priorAtr[i] = atr[i + 1];
   double atrMedian = Quantile(priorAtr, 0.5);
   double atrP95 = Quantile(priorAtr, 0.95);
   if(atrMedian <= 0.0)
      return false;

   double path = 0.0;
   for(int i = 0; i < 24; ++i)
      path += MathAbs(rates[i].close - rates[i + 1].close);
   double efficiency = path > 0.0
      ? MathAbs(rates[0].close - rates[24].close) / path
      : 0.0;
   double high = rates[0].high;
   double low = rates[0].low;
   for(int i = 1; i < 24; ++i)
   {
      high = MathMax(high, rates[i].high);
      low = MathMin(low, rates[i].low);
   }
   double widthAtr = (high - low) / currentAtr;
   double slopeAtr = (ema[0] - ema[6]) / currentAtr;
   double displacementAtr = MathAbs(rates[0].close - ema[0]) / currentAtr;
   double gapAtr = MathAbs(rates[0].open - rates[1].close) / currentAtr;
   bool unsafe = currentAtr >= atrP95 || gapAtr >= 1.5;
   bool trendCommon = !unsafe && adx[0] >= 18.0 && efficiency >= 0.25;
   bool trendUp = trendCommon && slopeAtr >= 0.10;
   bool trendDown = trendCommon && slopeAtr <= -0.10;
   bool compression = !unsafe && !trendUp && !trendDown
      && adx[0] <= 26.0
      && currentAtr / atrMedian <= 0.90
      && widthAtr <= 6.0;
   return !unsafe && !trendUp && !trendDown && !compression
      && adx[0] <= 30.0
      && efficiency <= 0.50
      && displacementAtr <= 2.50
      && widthAtr >= 1.0
      && widthAtr <= 10.0;
}

int CountSymbolPositions()
{
   int count = 0;
   for(int index = PositionsTotal() - 1; index >= 0; --index)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetString(POSITION_SYMBOL) == InpTargetSymbol)
         count++;
   }
   return count;
}

int CountOwnPositions()
{
   int count = 0;
   for(int index = PositionsTotal() - 1; index >= 0; --index)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(
         PositionGetString(POSITION_SYMBOL) == InpTargetSymbol
         && PositionGetInteger(POSITION_MAGIC) == InpMagicNumber
      )
         count++;
   }
   return count;
}

bool SelectOwnPosition()
{
   for(int index = PositionsTotal() - 1; index >= 0; --index)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(
         PositionGetString(POSITION_SYMBOL) == InpTargetSymbol
         && PositionGetInteger(POSITION_MAGIC) == InpMagicNumber
      )
         return true;
   }
   return false;
}

datetime StartOfUtcDay()
{
   MqlDateTime parts;
   TimeToStruct(UtcNow(), parts);
   parts.hour = 0;
   parts.min = 0;
   parts.sec = 0;
   datetime utcStart = StructToTime(parts);
   return utcStart + InpBrokerUtcOffsetHours * 3600;
}

double ClosedPnlSince(const datetime brokerStart, int &entries)
{
   entries = 0;
   if(!HistorySelect(brokerStart, TimeCurrent()))
      return 0.0;
   double pnl = 0.0;
   int total = HistoryDealsTotal();
   for(int index = 0; index < total; ++index)
   {
      ulong ticket = HistoryDealGetTicket(index);
      if(ticket == 0)
         continue;
      if(
         HistoryDealGetString(ticket, DEAL_SYMBOL) != InpTargetSymbol
         || HistoryDealGetInteger(ticket, DEAL_MAGIC) != InpMagicNumber
      )
         continue;
      long entryType = HistoryDealGetInteger(ticket, DEAL_ENTRY);
      if(entryType == DEAL_ENTRY_IN || entryType == DEAL_ENTRY_INOUT)
         entries++;
      if(
         entryType == DEAL_ENTRY_OUT
         || entryType == DEAL_ENTRY_OUT_BY
         || entryType == DEAL_ENTRY_INOUT
      )
      {
         pnl += HistoryDealGetDouble(ticket, DEAL_PROFIT);
         pnl += HistoryDealGetDouble(ticket, DEAL_COMMISSION);
         pnl += HistoryDealGetDouble(ticket, DEAL_SWAP);
      }
   }
   return pnl;
}

bool IdentityAllowsManagement(string &reason)
{
   if((bool)MQLInfoInteger(MQL_TESTER))
   {
      reason = "tester";
      return true;
   }
   if(
      (ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)
      != ACCOUNT_TRADE_MODE_DEMO
   )
   {
      reason = "account_not_demo";
      return false;
   }
   if(
      InpAllowedAccountLogin <= 0
      || AccountInfoInteger(ACCOUNT_LOGIN) != InpAllowedAccountLogin
   )
   {
      reason = "account_allowlist_mismatch";
      return false;
   }
   if(
      InpAllowedServer == ""
      || AccountInfoString(ACCOUNT_SERVER) != InpAllowedServer
   )
   {
      reason = "server_allowlist_mismatch";
      return false;
   }
   if(
      !TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)
      || !MQLInfoInteger(MQL_TRADE_ALLOWED)
      || !AccountInfoInteger(ACCOUNT_TRADE_ALLOWED)
   )
   {
      reason = "trading_not_allowed";
      return false;
   }
   reason = "identity_ok";
   return true;
}

bool NewOrderAllowed(string &reason)
{
   if((bool)MQLInfoInteger(MQL_TESTER))
   {
      reason = InpTesterOrdersEnabled ? "tester_armed" : "tester_disarmed";
      return InpTesterOrdersEnabled;
   }
   if(InpShadowMode || !InpEnableDemoOrders)
   {
      reason = "shadow_or_orders_disabled";
      return false;
   }
   if(InpEmergencyStop)
   {
      reason = "emergency_stop";
      return false;
   }
   if(InpDemoArmToken != ARM_TOKEN)
   {
      reason = "demo_arm_token_mismatch";
      return false;
   }
   if(!IdentityAllowsManagement(reason))
      return false;
   datetime prospectiveStart = StringToTime(InpProspectiveStartUtc);
   if(prospectiveStart <= 0 || UtcNow() < prospectiveStart)
   {
      reason = "prospective_start_not_reached";
      return false;
   }
   if(CountSymbolPositions() > 0)
   {
      reason = "eurusd_position_mutex";
      return false;
   }
   if(MathAbs(InpFixedLots - 0.01) > 0.0000001)
   {
      reason = "fixed_lot_must_equal_0p01";
      return false;
   }
   MqlTick tick;
   if(!SymbolInfoTick(InpTargetSymbol, tick))
   {
      reason = "tick_unavailable";
      return false;
   }
   if((tick.ask - tick.bid) / PipSize() > InpMaximumSpreadPips)
   {
      reason = "spread_limit";
      return false;
   }
   int dailyEntries = 0;
   double dailyPnl = ClosedPnlSince(StartOfUtcDay(), dailyEntries);
   if(
      InpMaximumTradesPerUtcDay > 0
      && dailyEntries >= InpMaximumTradesPerUtcDay
   )
   {
      reason = "daily_trade_cap";
      return false;
   }
   if(
      InpMaximumDailyClosedLossUsd > 0.0
      && dailyPnl <= -InpMaximumDailyClosedLossUsd
   )
   {
      reason = "daily_loss_breaker";
      return false;
   }
   int rollingEntries = 0;
   double rollingPnl = ClosedPnlSince(
      TimeCurrent() - 5 * 24 * 60 * 60,
      rollingEntries
   );
   if(
      InpMaximumRolling5DayClosedLossUsd > 0.0
      && rollingPnl <= -InpMaximumRolling5DayClosedLossUsd
   )
   {
      reason = "rolling_5day_loss_breaker";
      return false;
   }
   if(
      InpMaximumSessionEquityDrawdownUsd > 0.0
      && sessionStartEquity - AccountInfoDouble(ACCOUNT_EQUITY)
         >= InpMaximumSessionEquityDrawdownUsd
   )
   {
      reason = "session_equity_drawdown_breaker";
      return false;
   }
   reason = "all_order_guards_pass";
   return true;
}

void ManageTimeExit()
{
   if(!SelectOwnPosition())
      return;
   datetime opened = (datetime)PositionGetInteger(POSITION_TIME);
   int bars = iBarShift(_Symbol, PERIOD_H1, opened, false);
   if(bars < InpMaximumHoldH1Bars)
      return;
   if((bool)MQLInfoInteger(MQL_TESTER))
   {
      if(!InpTesterOrdersEnabled)
         return;
   }
   else
   {
      string reason = "";
      if(!IdentityAllowsManagement(reason))
      {
         Audit("TIME_EXIT_BLOCKED", reason);
         return;
      }
   }
   ulong ticket = (ulong)PositionGetInteger(POSITION_TICKET);
   bool closed = trade.PositionClose(ticket, InpDeviationPoints);
   Audit(
      closed ? "TIME_EXIT_OK" : "TIME_EXIT_FAILED",
      trade.ResultRetcodeDescription()
   );
}

void EvaluateSignal()
{
   if(CountOwnPositions() > 0)
      return;
   MqlRates h1[];
   ArraySetAsSeries(h1, true);
   if(CopyRates(_Symbol, PERIOD_H1, 1, 40, h1) < 30)
      return;
   int signalHour = 0;
   int signalDate = UtcDateKey(h1[0].time, signalHour);
   if(
      signalHour < 6
      || signalHour > 9
      || signalDate == lastSignalDate
      || !OwnedChopRegimePass()
   )
      return;

   double referenceLow = DBL_MAX;
   int referenceBars = 0;
   for(int index = 1; index < ArraySize(h1); ++index)
   {
      int hour = 0;
      int dateKey = UtcDateKey(h1[index].time, hour);
      if(dateKey == signalDate && hour >= 0 && hour <= 5)
      {
         referenceLow = MathMin(referenceLow, h1[index].low);
         referenceBars++;
      }
   }
   if(referenceBars < 6 || h1[0].close >= referenceLow)
      return;
   double range = h1[0].high - h1[0].low;
   if(
      range <= 0.0
      || MathAbs(h1[0].close - h1[0].open) / range < BODY_MINIMUM
   )
      return;

   double atr[];
   if(!CopyIndicator(h1Atr, 0, 1, 1, atr) || atr[0] <= 0.0)
      return;
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick))
      return;
   double stop = NormalizeDouble(
      tick.bid + STOP_ATR_MULTIPLE * atr[0],
      _Digits
   );
   double target = NormalizeDouble(
      tick.bid - TARGET_R_MULTIPLE * STOP_ATR_MULTIPLE * atr[0],
      _Digits
   );
   lastSignalDate = signalDate;
   Audit("SIGNAL", "H4_CHOP_ASIA_LONDON_SHORT", "SHORT", tick.bid, stop, target);

   string guardReason = "";
   if(!NewOrderAllowed(guardReason))
   {
      Audit("ORDER_BLOCKED", guardReason, "SHORT", tick.bid, stop, target);
      return;
   }
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetDeviationInPoints(InpDeviationPoints);
   bool sent = trade.Sell(
      InpFixedLots,
      _Symbol,
      0.0,
      stop,
      target,
      InpOrderComment
   );
   Audit(
      sent ? "ORDER_SEND_OK" : "ORDER_SEND_FAILED",
      trade.ResultRetcodeDescription(),
      "SHORT",
      tick.bid,
      stop,
      target
   );
}

bool AcquireMutex()
{
   mutexName = StringFormat(
      "CODEX_EUH4CHOP_%I64d_%s",
      AccountInfoInteger(ACCOUNT_LOGIN),
      InpTargetSymbol
   );
   double now = (double)TimeLocal();
   if(GlobalVariableCheck(mutexName))
   {
      double heartbeat = GlobalVariableGet(mutexName);
      if(now - heartbeat < 180.0)
         return false;
   }
   GlobalVariableSet(mutexName, now);
   mutexOwned = true;
   EventSetTimer(60);
   return true;
}

int OnInit()
{
   if(_Symbol != InpTargetSymbol)
      return INIT_PARAMETERS_INCORRECT;
   if(
      !(bool)MQLInfoInteger(MQL_TESTER)
      && (ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)
         != ACCOUNT_TRADE_MODE_DEMO
   )
   {
      Audit("INIT_FAILED", "account_not_demo");
      return INIT_FAILED;
   }
   if(!AcquireMutex())
   {
      Audit("INIT_FAILED", "duplicate_instance_mutex");
      return INIT_FAILED;
   }
   if(
      !(bool)MQLInfoInteger(MQL_TESTER)
      && !InpShadowMode
      && (
         !InpEnableDemoOrders
         || InpAllowedAccountLogin <= 0
         || InpAllowedServer == ""
         || InpDemoArmToken != ARM_TOKEN
         || InpEmergencyStop
      )
   )
   {
      Audit("INIT_FAILED", "ordering_configuration_not_fully_armed");
      return INIT_FAILED;
   }
   if(CountSymbolPositions() != CountOwnPositions() || CountOwnPositions() > 1)
   {
      Audit("INIT_FAILED", "position_ownership_reconciliation_failed");
      return INIT_FAILED;
   }
   h1Atr = iATR(_Symbol, PERIOD_H1, ATR_PERIOD);
   h4Atr = iATR(_Symbol, PERIOD_H4, ATR_PERIOD);
   h4Adx = iADX(_Symbol, PERIOD_H4, ADX_PERIOD);
   h4Ema = iMA(_Symbol, PERIOD_H4, EMA_PERIOD, 0, MODE_EMA, PRICE_CLOSE);
   if(
      h1Atr == INVALID_HANDLE
      || h4Atr == INVALID_HANDLE
      || h4Adx == INVALID_HANDLE
      || h4Ema == INVALID_HANDLE
   )
   {
      Audit("INIT_FAILED", "indicator_handle_invalid");
      return INIT_FAILED;
   }
   sessionStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   lastH1Open = iTime(_Symbol, PERIOD_H1, 0);
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetDeviationInPoints(InpDeviationPoints);
   Audit(
      "INIT_OK",
      (bool)MQLInfoInteger(MQL_TESTER)
         ? "tester"
         : (InpShadowMode ? "shadow_demo" : "ordering_demo")
   );
   return INIT_SUCCEEDED;
}

void OnTimer()
{
   if(mutexOwned)
      GlobalVariableSet(mutexName, (double)TimeLocal());
}

void OnDeinit(const int reason)
{
   Audit("DEINIT", IntegerToString(reason));
   EventKillTimer();
   if(mutexOwned && GlobalVariableCheck(mutexName))
      GlobalVariableDel(mutexName);
   if(h1Atr != INVALID_HANDLE)
      IndicatorRelease(h1Atr);
   if(h4Atr != INVALID_HANDLE)
      IndicatorRelease(h4Atr);
   if(h4Adx != INVALID_HANDLE)
      IndicatorRelease(h4Adx);
   if(h4Ema != INVALID_HANDLE)
      IndicatorRelease(h4Ema);
}

void OnTick()
{
   ManageTimeExit();
   datetime currentH1 = iTime(_Symbol, PERIOD_H1, 0);
   if(currentH1 == 0 || currentH1 == lastH1Open)
      return;
   lastH1Open = currentH1;
   EvaluateSignal();
}

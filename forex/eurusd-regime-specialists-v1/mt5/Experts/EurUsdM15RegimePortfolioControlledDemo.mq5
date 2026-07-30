#property strict
#property version   "1.00"
#property description "EURUSD M15 chop/compression first-break controlled demo EA"

#include <Trade/Trade.mqh>

input string InpRunId = "EURUSD_M15_REGIME_FORWARD_V1";
input string InpTargetSymbol = "EURUSD";
input long InpBaseMagicNumber = 26073060;
input string InpOrderComment = "EUM15REGIME_V1";
input bool InpShadowMode = true;
input bool InpEnableDemoOrders = false;
input bool InpEmergencyStop = true;
input bool InpTesterOrdersEnabled = false;
input long InpAllowedAccountLogin = 0;
input string InpAllowedServer = "";
input string InpDemoArmToken = "DISARMED";
input string InpProspectiveStartUtc = "2026.08.01 00:00";
input int InpBrokerUtcOffsetHours = 0;
input double InpChopLots = 0.02;
input double InpCompressionLots = 0.01;
input double InpMaximumSpreadPips = 2.0;
input int InpMaximumHoldM15Bars = 48;
input int InpMaximumTradesPerUtcDay = 2;
input double InpMaximumDailyClosedLossUsd = 15.0;
input double InpMaximumRolling5DayClosedLossUsd = 30.0;
input double InpMaximumSessionEquityDrawdownUsd = 40.0;
input int InpDeviationPoints = 10;
input string InpAuditLogName = "EURUSD_M15_REGIME_CONTROLLED_DEMO.csv";

const int ATR_PERIOD = 14;
const int ADX_PERIOD = 14;
const int EMA_PERIOD = 50;
const int BASELINE_BARS = 504;
const double CHOP_BODY_MINIMUM = 0.35;
const double COMPRESSION_BODY_MINIMUM = 0.55;
const double STOP_ATR_MULTIPLE = 1.75;
const double CHOP_TARGET_R = 1.25;
const double COMPRESSION_TARGET_R = 2.0;
const string ARM_TOKEN = "I_ACCEPT_DEMO_001";

enum OwnedRegime
{
   REGIME_UNAVAILABLE = 0,
   REGIME_CHOP = 1,
   REGIME_COMPRESSION = 2,
   REGIME_OTHER = 3
};

CTrade trade;
int h1Atr = INVALID_HANDLE;
int h4Atr = INVALID_HANDLE;
int h4Adx = INVALID_HANDLE;
int h4Ema = INVALID_HANDLE;
datetime lastM15Open = 0;
int lastChopSignalDate = 0;
int lastCompressionSignalDate = 0;
double sessionStartEquity = 0.0;
string mutexName = "";
string chopDateName = "";
string compressionDateName = "";
bool mutexOwned = false;

string BoolText(const bool value)
{
   return value ? "true" : "false";
}

string RegimeText(const OwnedRegime regime)
{
   if(regime == REGIME_CHOP)
      return "CHOP";
   if(regime == REGIME_COMPRESSION)
      return "COMPRESSION";
   if(regime == REGIME_OTHER)
      return "OTHER";
   return "UNAVAILABLE";
}

long RegimeMagic(const OwnedRegime regime)
{
   return InpBaseMagicNumber + (regime == REGIME_CHOP ? 1 : 2);
}

double RegimeLots(const OwnedRegime regime)
{
   return regime == REGIME_CHOP ? InpChopLots : InpCompressionLots;
}

double RegimeBodyMinimum(const OwnedRegime regime)
{
   return regime == REGIME_CHOP
      ? CHOP_BODY_MINIMUM
      : COMPRESSION_BODY_MINIMUM;
}

double RegimeTargetR(const OwnedRegime regime)
{
   return regime == REGIME_CHOP ? CHOP_TARGET_R : COMPRESSION_TARGET_R;
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

void UtcParts(const datetime brokerTime, MqlDateTime &parts)
{
   datetime utcTime = brokerTime - InpBrokerUtcOffsetHours * 3600;
   TimeToStruct(utcTime, parts);
}

int UtcDateKey(const datetime brokerTime)
{
   MqlDateTime parts;
   UtcParts(brokerTime, parts);
   return parts.year * 10000 + parts.mon * 100 + parts.day;
}

void Audit(
   const string eventName,
   const string detail,
   const OwnedRegime regime = REGIME_UNAVAILABLE,
   const string side = "NONE",
   const double lots = 0.0,
   const double entry = 0.0,
   const double stop = 0.0,
   const double target = 0.0
)
{
   int handle = FileOpen(
      InpAuditLogName,
      FILE_READ | FILE_WRITE | FILE_CSV | FILE_COMMON |
         FILE_SHARE_READ | FILE_SHARE_WRITE,
      ','
   );
   if(handle == INVALID_HANDLE)
   {
      PrintFormat("EURUSD_M15_REGIME audit open failed err=%d", GetLastError());
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
         "regime",
         "side",
         "lots",
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
      regime == REGIME_UNAVAILABLE ? InpBaseMagicNumber : RegimeMagic(regime),
      RegimeText(regime),
      side,
      DoubleToString(lots, 2),
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

int LatestCompletedH4Shift(const datetime signalOpen)
{
   datetime utcTime = signalOpen - InpBrokerUtcOffsetHours * 3600;
   MqlDateTime parts;
   TimeToStruct(utcTime, parts);
   parts.hour = (parts.hour / 4) * 4;
   parts.min = 0;
   parts.sec = 0;
   datetime completedOpenUtc = StructToTime(parts) - 4 * 3600;
   datetime completedOpenBroker =
      completedOpenUtc + InpBrokerUtcOffsetHours * 3600;
   return iBarShift(_Symbol, PERIOD_H4, completedOpenBroker, true);
}

OwnedRegime ClassifyRegime(const datetime signalOpen)
{
   int shift = LatestCompletedH4Shift(signalOpen);
   if(shift < 1)
      return REGIME_UNAVAILABLE;

   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   if(CopyRates(_Symbol, PERIOD_H4, shift, BASELINE_BARS + 30, rates) <
      BASELINE_BARS + 25)
      return REGIME_UNAVAILABLE;

   double atr[], adx[], ema[];
   if(!CopyIndicator(h4Atr, 0, shift, BASELINE_BARS + 1, atr))
      return REGIME_UNAVAILABLE;
   if(!CopyIndicator(h4Adx, 0, shift, 1, adx))
      return REGIME_UNAVAILABLE;
   if(!CopyIndicator(h4Ema, 0, shift, 7, ema))
      return REGIME_UNAVAILABLE;

   double currentAtr = atr[0];
   if(currentAtr <= 0.0 || adx[0] <= 0.0)
      return REGIME_UNAVAILABLE;

   double priorAtr[];
   ArrayResize(priorAtr, BASELINE_BARS);
   for(int index = 0; index < BASELINE_BARS; ++index)
      priorAtr[index] = atr[index + 1];
   double atrMedian = Quantile(priorAtr, 0.5);
   double atrP95 = Quantile(priorAtr, 0.95);
   if(atrMedian <= 0.0)
      return REGIME_UNAVAILABLE;

   double path = 0.0;
   for(int index = 0; index < 24; ++index)
      path += MathAbs(rates[index].close - rates[index + 1].close);
   double efficiency = path > 0.0
      ? MathAbs(rates[0].close - rates[24].close) / path
      : 0.0;
   double high = rates[0].high;
   double low = rates[0].low;
   for(int index = 1; index < 24; ++index)
   {
      high = MathMax(high, rates[index].high);
      low = MathMin(low, rates[index].low);
   }
   double widthAtr = (high - low) / currentAtr;
   double slopeAtr = (ema[0] - ema[6]) / currentAtr;
   double displacementAtr =
      MathAbs(rates[0].close - ema[0]) / currentAtr;
   double gapAtr =
      MathAbs(rates[0].open - rates[1].close) / currentAtr;

   bool unsafe = currentAtr >= atrP95 || gapAtr >= 1.5;
   bool trendCommon = !unsafe && adx[0] >= 18.0 && efficiency >= 0.25;
   bool trendUp = trendCommon && slopeAtr >= 0.10;
   bool trendDown = trendCommon && slopeAtr <= -0.10;
   bool compression = !unsafe && !trendUp && !trendDown
      && adx[0] <= 26.0
      && currentAtr / atrMedian <= 0.90
      && widthAtr <= 6.0;
   if(compression)
      return REGIME_COMPRESSION;
   bool chop = !unsafe && !trendUp && !trendDown
      && adx[0] <= 30.0
      && efficiency <= 0.50
      && displacementAtr <= 2.50
      && widthAtr >= 1.0
      && widthAtr <= 10.0;
   return chop ? REGIME_CHOP : REGIME_OTHER;
}

bool IsOwnMagic(const long magic)
{
   return magic == RegimeMagic(REGIME_CHOP)
      || magic == RegimeMagic(REGIME_COMPRESSION);
}

int CountForeignSymbolPositions()
{
   int count = 0;
   for(int index = PositionsTotal() - 1; index >= 0; --index)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(
         PositionGetString(POSITION_SYMBOL) == InpTargetSymbol
         && !IsOwnMagic(PositionGetInteger(POSITION_MAGIC))
      )
         count++;
   }
   return count;
}

int CountRegimePositions(const OwnedRegime regime)
{
   int count = 0;
   for(int index = PositionsTotal() - 1; index >= 0; --index)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(
         PositionGetString(POSITION_SYMBOL) == InpTargetSymbol
         && PositionGetInteger(POSITION_MAGIC) == RegimeMagic(regime)
      )
         count++;
   }
   return count;
}

int CountOwnPositions()
{
   return CountRegimePositions(REGIME_CHOP)
      + CountRegimePositions(REGIME_COMPRESSION);
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
         || !IsOwnMagic(HistoryDealGetInteger(ticket, DEAL_MAGIC))
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

bool NewOrderAllowed(
   const OwnedRegime regime,
   const double lots,
   string &reason
)
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
   if(CountForeignSymbolPositions() > 0)
   {
      reason = "foreign_eurusd_position_mutex";
      return false;
   }
   if(CountRegimePositions(regime) > 0)
   {
      reason = "specialist_position_mutex";
      return false;
   }
   double requiredLots =
      regime == REGIME_CHOP ? 0.02 : 0.01;
   if(MathAbs(lots - requiredLots) > 0.0000001)
   {
      reason = "executable_2_to_1_risk_allocation_required";
      return false;
   }
   if(
      (ENUM_ACCOUNT_MARGIN_MODE)AccountInfoInteger(ACCOUNT_MARGIN_MODE)
      != ACCOUNT_MARGIN_MODE_RETAIL_HEDGING
   )
   {
      reason = "hedging_account_required";
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

void ManageTimeExits()
{
   for(int index = PositionsTotal() - 1; index >= 0; --index)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      long magic = PositionGetInteger(POSITION_MAGIC);
      if(
         PositionGetString(POSITION_SYMBOL) != InpTargetSymbol
         || !IsOwnMagic(magic)
      )
         continue;
      datetime opened = (datetime)PositionGetInteger(POSITION_TIME);
      int bars = iBarShift(_Symbol, PERIOD_M15, opened, false);
      if(bars < InpMaximumHoldM15Bars)
         continue;
      if((bool)MQLInfoInteger(MQL_TESTER))
      {
         if(!InpTesterOrdersEnabled)
            continue;
      }
      else
      {
         string reason = "";
         if(!IdentityAllowsManagement(reason))
         {
            Audit("TIME_EXIT_BLOCKED", reason);
            continue;
         }
      }
      OwnedRegime regime =
         magic == RegimeMagic(REGIME_CHOP)
            ? REGIME_CHOP
            : REGIME_COMPRESSION;
      trade.SetExpertMagicNumber(magic);
      bool closed = trade.PositionClose(ticket, InpDeviationPoints);
      Audit(
         closed ? "TIME_EXIT_OK" : "TIME_EXIT_FAILED",
         trade.ResultRetcodeDescription(),
         regime
      );
   }
}

void PersistSignalDate(const OwnedRegime regime, const int dateKey)
{
   if((bool)MQLInfoInteger(MQL_TESTER))
      return;
   if(regime == REGIME_CHOP)
      GlobalVariableSet(chopDateName, (double)dateKey);
   else if(regime == REGIME_COMPRESSION)
      GlobalVariableSet(compressionDateName, (double)dateKey);
}

void EvaluateSignal()
{
   if(
      !(bool)MQLInfoInteger(MQL_TESTER)
      && UtcNow() < StringToTime(InpProspectiveStartUtc)
   )
      return;

   MqlRates m15[];
   ArraySetAsSeries(m15, true);
   if(CopyRates(_Symbol, PERIOD_M15, 1, 80, m15) < 60)
      return;
   datetime signalOpen = m15[0].time;
   MqlDateTime signalParts;
   UtcParts(signalOpen, signalParts);
   if(signalParts.hour < 6 || signalParts.hour > 9)
      return;
   int signalDate = UtcDateKey(signalOpen);

   double referenceLow = DBL_MAX;
   int referenceBars = 0;
   for(int index = 1; index < ArraySize(m15); ++index)
   {
      MqlDateTime parts;
      UtcParts(m15[index].time, parts);
      int dateKey =
         parts.year * 10000 + parts.mon * 100 + parts.day;
      if(dateKey == signalDate && parts.hour >= 0 && parts.hour <= 5)
      {
         referenceLow = MathMin(referenceLow, m15[index].low);
         referenceBars++;
      }
   }
   if(referenceBars != 24 || m15[0].close >= referenceLow)
      return;

   OwnedRegime regime = ClassifyRegime(signalOpen);
   if(regime != REGIME_CHOP && regime != REGIME_COMPRESSION)
      return;
   if(
      (regime == REGIME_CHOP && signalDate == lastChopSignalDate)
      || (
         regime == REGIME_COMPRESSION
         && signalDate == lastCompressionSignalDate
      )
   )
      return;

   double range = m15[0].high - m15[0].low;
   if(
      range <= 0.0
      || MathAbs(m15[0].close - m15[0].open) / range
         < RegimeBodyMinimum(regime)
   )
      return;

   double atr[];
   if(!CopyIndicator(h1Atr, 0, 1, 1, atr) || atr[0] <= 0.0)
      return;
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick))
      return;
   double stopDistance = STOP_ATR_MULTIPLE * atr[0];
   double stop = NormalizeDouble(tick.bid + stopDistance, _Digits);
   double target = NormalizeDouble(
      tick.bid - RegimeTargetR(regime) * stopDistance,
      _Digits
   );
   double lots = RegimeLots(regime);
   if(regime == REGIME_CHOP)
      lastChopSignalDate = signalDate;
   else
      lastCompressionSignalDate = signalDate;
   PersistSignalDate(regime, signalDate);

   Audit(
      "SIGNAL",
      "M15_FIRST_BREAK",
      regime,
      "SHORT",
      lots,
      tick.bid,
      stop,
      target
   );
   string guardReason = "";
   if(!NewOrderAllowed(regime, lots, guardReason))
   {
      Audit(
         "ORDER_BLOCKED",
         guardReason,
         regime,
         "SHORT",
         lots,
         tick.bid,
         stop,
         target
      );
      return;
   }

   long magic = RegimeMagic(regime);
   trade.SetExpertMagicNumber(magic);
   trade.SetDeviationInPoints(InpDeviationPoints);
   trade.SetTypeFillingBySymbol(_Symbol);
   string comment = InpOrderComment + "_" + RegimeText(regime);
   bool sent = trade.Sell(
      lots,
      _Symbol,
      0.0,
      stop,
      target,
      comment
   );
   Audit(
      sent ? "ORDER_SEND_OK" : "ORDER_SEND_FAILED",
      trade.ResultRetcodeDescription(),
      regime,
      "SHORT",
      lots,
      tick.bid,
      stop,
      target
   );
}

bool AcquireMutex()
{
   mutexName = StringFormat(
      "CODEX_EUM15REG_%I64d_%s",
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
   if(_Symbol != InpTargetSymbol || _Period != PERIOD_M15)
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
   if(
      CountForeignSymbolPositions() > 0
      || CountRegimePositions(REGIME_CHOP) > 1
      || CountRegimePositions(REGIME_COMPRESSION) > 1
      || CountOwnPositions() > 2
   )
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

   chopDateName = StringFormat(
      "CODEX_EUM15_CHOP_%I64d",
      AccountInfoInteger(ACCOUNT_LOGIN)
   );
   compressionDateName = StringFormat(
      "CODEX_EUM15_COMP_%I64d",
      AccountInfoInteger(ACCOUNT_LOGIN)
   );
   if(
      !(bool)MQLInfoInteger(MQL_TESTER)
      && GlobalVariableCheck(chopDateName)
   )
      lastChopSignalDate = (int)GlobalVariableGet(chopDateName);
   if(
      !(bool)MQLInfoInteger(MQL_TESTER)
      && GlobalVariableCheck(compressionDateName)
   )
      lastCompressionSignalDate =
         (int)GlobalVariableGet(compressionDateName);

   sessionStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   lastM15Open = iTime(_Symbol, PERIOD_M15, 0);
   trade.SetDeviationInPoints(InpDeviationPoints);
   Audit(
      "INIT_OK",
      (bool)MQLInfoInteger(MQL_TESTER)
         ? "tester"
         : (InpShadowMode ? "shadow_demo" : "ordering_demo")
   );
   Audit(
      "STARTUP_LATCH",
      TimeToString(lastM15Open, TIME_DATE | TIME_MINUTES)
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
   ManageTimeExits();
   datetime currentM15 = iTime(_Symbol, PERIOD_M15, 0);
   if(currentM15 == 0 || currentM15 == lastM15Open)
      return;
   lastM15Open = currentM15;
   EvaluateSignal();
}

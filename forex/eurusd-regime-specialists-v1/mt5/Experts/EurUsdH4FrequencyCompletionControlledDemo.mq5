#property strict
#property version   "2.00"
#property description "EURUSD hardened chop-regime frequency-completion controlled demo EA"

#include <Trade/Trade.mqh>

input string InpRunId = "EURUSD_H4_FREQUENCY_COMPLETION_V2";
input string InpTargetSymbol = "EURUSD";
input long InpBaseMagicNumber = 26073100;
input string InpOrderComment = "EUH4FREQV2";
input bool InpShadowMode = true;
input bool InpEnableDemoOrders = false;
input bool InpEmergencyStop = true;
input bool InpTesterOrdersEnabled = false;
input bool InpEnableCompressionSleeves = false;
input long InpAllowedAccountLogin = 0;
input string InpAllowedServer = "";
input string InpDemoArmToken = "DISARMED";
input string InpProspectiveStartUtc = "2026.08.01 00:00";
input int InpBrokerUtcOffsetHours = 0;
input double InpLotsPerTrade = 0.01;
input double InpMaximumSpreadPips = 2.0;
input int InpMaximumHoldM15Bars = 48;
input int InpMaximumTradesPerUtcDay = 6;
input int InpMaximumOwnPositions = 6;
input double InpMaximumDailyClosedLossUsd = 20.0;
input double InpMaximumRolling5DayClosedLossUsd = 40.0;
input double InpMaximumSessionEquityDrawdownUsd = 60.0;
input double InpMaximumAggregateInitialRiskUsd = 25.0;
input double InpMinimumAccountEquityUsd = 5000.0;
input double InpMinimumFreeMarginAfterOrderUsd = 2500.0;
input int InpMaximumTickAgeSeconds = 10;
input int InpDeviationPoints = 10;
input int InpRestartExerciseUtcHour = -1;
input string InpAuditLogName = "EURUSD_H4_FREQUENCY_COMPLETION_CONTROLLED_DEMO.csv";

const int ATR_PERIOD = 14;
const int ADX_PERIOD = 14;
const int EMA_PERIOD = 50;
const int BASELINE_BARS = 504;
const double CHOP_BODY_MINIMUM = 0.35;
const double COMPRESSION_BODY_MINIMUM = 0.55;
const double STOP_ATR_MULTIPLE = 1.75;
const double CHOP_TARGET_R = 1.25;
const double COMPRESSION_TARGET_R = 2.0;
const double STAGE_ONE_MAXIMUM_RISK = 2.0;
const double STAGE_TWO_MAXIMUM_RISK = 2.5;
const string ARM_TOKEN = "I_ACCEPT_DEMO_001";
const double CONTRACT_SCHEMA_FINGERPRINT = 220260731.0;
const double FROZEN_DAILY_LOSS_USD = 20.0;
const double FROZEN_ROLLING_LOSS_USD = 40.0;
const double FROZEN_EQUITY_DRAWDOWN_USD = 60.0;
const double FROZEN_AGGREGATE_INITIAL_RISK_USD = 25.0;
const double FROZEN_MINIMUM_ACCOUNT_EQUITY_USD = 5000.0;
const double FROZEN_MINIMUM_FREE_MARGIN_USD = 2500.0;

enum OwnedRegime
{
   REGIME_UNAVAILABLE = 0,
   REGIME_CHOP = 1,
   REGIME_COMPRESSION = 2,
   REGIME_OTHER = 3
};

enum Sleeve
{
   BASELINE_CHOP = 0,
   BASELINE_COMPRESSION = 1,
   NEXT_CLOSE_CHOP = 2,
   NEXT_CLOSE_COMPRESSION = 3,
   RETEST_CHOP = 4,
   RETEST_COMPRESSION = 5,
   M15_FOLLOW_3_CHOP = 6,
   M15_FOLLOW_5_CHOP = 7,
   M15_FOLLOW_5_COMPRESSION = 8,
   M15_FOLLOW_7_COMPRESSION = 9,
   M30_FIRST_BREAK_CHOP = 10,
   M30_FIRST_BREAK_COMPRESSION = 11
};

const int SLEEVE_COUNT = 12;
CTrade trade;
int h1Atr = INVALID_HANDLE;
int h4Atr = INVALID_HANDLE;
int h4Adx = INVALID_HANDLE;
int h4Ema = INVALID_HANDLE;
datetime lastM15Open = 0;
datetime m15BreakOpen[2];
datetime m30BreakOpen[2];
int stateDateKey = 0;
int lastSignalDate[12];
datetime lastTimeExitAttemptBar[12];
int lastRestartExerciseDate = 0;
double sessionStartEquity = 0.0;
double sessionPeakEquity = 0.0;
double mutexOwnerToken = 0.0;
string mutexOwnerName = "";
string mutexHeartbeatName = "";
string schemaName = "";
string peakEquityName = "";
string breakerLatchName = "";
string signalDateNames[12];
bool mutexOwned = false;
bool stateReady = false;
bool auditHealthy = true;
bool persistentBreakerLatched = false;

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

string SleeveText(const int sleeve)
{
   switch(sleeve)
   {
      case BASELINE_CHOP: return "BASELINE_CHOP";
      case BASELINE_COMPRESSION: return "BASELINE_COMPRESSION";
      case NEXT_CLOSE_CHOP: return "NEXT_CLOSE_CHOP";
      case NEXT_CLOSE_COMPRESSION: return "NEXT_CLOSE_COMPRESSION";
      case RETEST_CHOP: return "RETEST_CHOP";
      case RETEST_COMPRESSION: return "RETEST_COMPRESSION";
      case M15_FOLLOW_3_CHOP: return "M15_FOLLOW_3_CHOP";
      case M15_FOLLOW_5_CHOP: return "M15_FOLLOW_5_CHOP";
      case M15_FOLLOW_5_COMPRESSION: return "M15_FOLLOW_5_COMPRESSION";
      case M15_FOLLOW_7_COMPRESSION: return "M15_FOLLOW_7_COMPRESSION";
      case M30_FIRST_BREAK_CHOP: return "M30_FIRST_BREAK_CHOP";
      case M30_FIRST_BREAK_COMPRESSION:
         return "M30_FIRST_BREAK_COMPRESSION";
   }
   return "NONE";
}

string SleeveCode(const int sleeve)
{
   switch(sleeve)
   {
      case BASELINE_CHOP: return "BC";
      case BASELINE_COMPRESSION: return "BX";
      case NEXT_CLOSE_CHOP: return "NC";
      case NEXT_CLOSE_COMPRESSION: return "NX";
      case RETEST_CHOP: return "RC";
      case RETEST_COMPRESSION: return "RX";
      case M15_FOLLOW_3_CHOP: return "F3C";
      case M15_FOLLOW_5_CHOP: return "F5C";
      case M15_FOLLOW_5_COMPRESSION: return "F5X";
      case M15_FOLLOW_7_COMPRESSION: return "F7X";
      case M30_FIRST_BREAK_CHOP: return "M30C";
      case M30_FIRST_BREAK_COMPRESSION: return "M30X";
   }
   return "NONE";
}

OwnedRegime SleeveRegime(const int sleeve)
{
   if(
      sleeve == BASELINE_CHOP
      || sleeve == NEXT_CLOSE_CHOP
      || sleeve == RETEST_CHOP
      || sleeve == M15_FOLLOW_3_CHOP
      || sleeve == M15_FOLLOW_5_CHOP
      || sleeve == M30_FIRST_BREAK_CHOP
   )
      return REGIME_CHOP;
   return REGIME_COMPRESSION;
}

bool IsParentSleeve(const int sleeve)
{
   return sleeve >= BASELINE_CHOP && sleeve <= RETEST_COMPRESSION;
}

double StageOneWeight(const int sleeve)
{
   return SleeveRegime(sleeve) == REGIME_CHOP ? 1.0 : 0.5;
}

double StageTwoWeight(const int sleeve)
{
   if(IsParentSleeve(sleeve))
      return SleeveRegime(sleeve) == REGIME_CHOP ? 0.75 : 0.375;
   if(sleeve == M30_FIRST_BREAK_COMPRESSION)
      return 0.125;
   return 0.25;
}

long SleeveMagic(const int sleeve)
{
   return InpBaseMagicNumber + sleeve + 1;
}

int MagicSleeve(const long magic)
{
   int sleeve = (int)(magic - InpBaseMagicNumber - 1);
   return sleeve >= 0 && sleeve < SLEEVE_COUNT ? sleeve : -1;
}

bool IsOwnMagic(const long magic)
{
   return MagicSleeve(magic) >= 0;
}

double BodyMinimum(const OwnedRegime regime)
{
   return regime == REGIME_CHOP
      ? CHOP_BODY_MINIMUM
      : COMPRESSION_BODY_MINIMUM;
}

double TargetR(const OwnedRegime regime)
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

datetime BrokerFromUtc(const datetime utcTime)
{
   return utcTime + InpBrokerUtcOffsetHours * 3600;
}

datetime UtcFromBroker(const datetime brokerTime)
{
   return brokerTime - InpBrokerUtcOffsetHours * 3600;
}

void UtcParts(const datetime brokerTime, MqlDateTime &parts)
{
   TimeToStruct(UtcFromBroker(brokerTime), parts);
}

int UtcDateKey(const datetime brokerTime)
{
   MqlDateTime parts;
   UtcParts(brokerTime, parts);
   return parts.year * 10000 + parts.mon * 100 + parts.day;
}

datetime UtcDayStart(const datetime brokerTime)
{
   MqlDateTime parts;
   UtcParts(brokerTime, parts);
   parts.hour = 0;
   parts.min = 0;
   parts.sec = 0;
   return BrokerFromUtc(StructToTime(parts));
}

bool Audit(
   const string eventName,
   const string detail,
   const int sleeve = -1,
   const string side = "NONE",
   const double lots = 0.0,
   const double entry = 0.0,
   const double stop = 0.0,
   const double target = 0.0
)
{
   int handle = FileOpen(
      InpAuditLogName,
      FILE_READ | FILE_WRITE | FILE_CSV | FILE_COMMON
         | FILE_SHARE_READ | FILE_SHARE_WRITE,
      ','
   );
   if(handle == INVALID_HANDLE)
   {
      auditHealthy = false;
      PrintFormat("EURUSD_H4_FREQ audit open failed err=%d", GetLastError());
      return false;
   }
   bool okay = true;
   if(FileSize(handle) <= 2)
      okay = FileWrite(
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
         "sleeve",
         "regime",
         "side",
         "lots",
         "entry",
         "stop",
         "target",
         "shadow",
         "orders_enabled",
         "emergency_stop"
      ) > 0;
   FileSeek(handle, 0, SEEK_END);
   OwnedRegime regime =
      sleeve >= 0 ? SleeveRegime(sleeve) : REGIME_UNAVAILABLE;
   okay = FileWrite(
      handle,
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      TimeToString(UtcNow(), TIME_DATE | TIME_SECONDS),
      InpRunId,
      eventName,
      detail,
      (long)AccountInfoInteger(ACCOUNT_LOGIN),
      AccountInfoString(ACCOUNT_SERVER),
      _Symbol,
      sleeve >= 0 ? SleeveMagic(sleeve) : InpBaseMagicNumber,
      SleeveText(sleeve),
      RegimeText(regime),
      side,
      DoubleToString(lots, 2),
      DoubleToString(entry, _Digits),
      DoubleToString(stop, _Digits),
      DoubleToString(target, _Digits),
      BoolText(InpShadowMode),
      BoolText(InpEnableDemoOrders),
      BoolText(InpEmergencyStop)
   ) > 0 && okay;
   FileFlush(handle);
   FileClose(handle);
   if(!okay)
   {
      auditHealthy = false;
      Print("EURUSD_H4_FREQ audit write failed");
      return false;
   }
   return true;
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
   datetime utcTime = UtcFromBroker(signalOpen);
   MqlDateTime parts;
   TimeToStruct(utcTime, parts);
   parts.hour = (parts.hour / 4) * 4;
   parts.min = 0;
   parts.sec = 0;
   datetime completedOpenUtc = StructToTime(parts) - 4 * 3600;
   return iBarShift(
      _Symbol,
      PERIOD_H4,
      BrokerFromUtc(completedOpenUtc),
      true
   );
}

OwnedRegime ClassifyRegime(const datetime signalOpen)
{
   int shift = LatestCompletedH4Shift(signalOpen);
   if(shift < 1)
      return REGIME_UNAVAILABLE;
   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   if(
      CopyRates(_Symbol, PERIOD_H4, shift, BASELINE_BARS + 30, rates)
      < BASELINE_BARS + 25
   )
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

bool ReadBar(
   const ENUM_TIMEFRAMES timeframe,
   const datetime brokerOpen,
   MqlRates &bar
)
{
   int shift = iBarShift(_Symbol, timeframe, brokerOpen, true);
   if(shift < 0)
      return false;
   MqlRates values[];
   ArraySetAsSeries(values, true);
   if(CopyRates(_Symbol, timeframe, shift, 1, values) != 1)
      return false;
   if(values[0].time != brokerOpen)
      return false;
   bar = values[0];
   return true;
}

double ReferenceLow(
   const ENUM_TIMEFRAMES timeframe,
   const datetime anyBarToday,
   const int expectedBars
)
{
   datetime start = UtcDayStart(anyBarToday);
   int seconds = PeriodSeconds(timeframe);
   double low = DBL_MAX;
   int count = 0;
   for(int index = 0; index < expectedBars; ++index)
   {
      MqlRates bar;
      if(!ReadBar(timeframe, start + index * seconds, bar))
         continue;
      low = MathMin(low, bar.low);
      count++;
   }
   return count == expectedBars ? low : DBL_MAX;
}

int RegimeSlot(const OwnedRegime regime)
{
   return regime == REGIME_CHOP ? 0 : 1;
}

void ResetCandidateFlags(bool &candidate[])
{
   ArrayResize(candidate, SLEEVE_COUNT);
   for(int sleeve = 0; sleeve < SLEEVE_COUNT; ++sleeve)
      candidate[sleeve] = false;
}

void EnsureStateDate(const datetime barOpen)
{
   int dateKey = UtcDateKey(barOpen);
   if(dateKey == stateDateKey)
      return;
   stateDateKey = dateKey;
   for(int index = 0; index < 2; ++index)
   {
      m15BreakOpen[index] = 0;
      m30BreakOpen[index] = 0;
   }
}

void AddM15Candidates(
   const datetime barOpen,
   bool &candidate[]
)
{
   MqlDateTime parts;
   UtcParts(barOpen, parts);
   int minute = parts.hour * 60 + parts.min;
   if(minute < 360 || minute >= 600)
      return;
   MqlRates bar;
   if(!ReadBar(PERIOD_M15, barOpen, bar))
      return;
   double refLow = ReferenceLow(PERIOD_M15, barOpen, 24);
   if(refLow == DBL_MAX)
      return;
   OwnedRegime regime = ClassifyRegime(barOpen);
   if(regime != REGIME_CHOP && regime != REGIME_COMPRESSION)
      return;
   if(regime == REGIME_COMPRESSION && !InpEnableCompressionSleeves)
      return;
   int slot = RegimeSlot(regime);
   double range = bar.high - bar.low;
   bool qualifiedBreak =
      bar.close < refLow
      && range > 0.0
      && MathAbs(bar.close - bar.open) / range >= BodyMinimum(regime);
   if(m15BreakOpen[slot] == 0)
   {
      if(!qualifiedBreak)
         return;
      m15BreakOpen[slot] = barOpen;
      candidate[
         regime == REGIME_CHOP ? BASELINE_CHOP : BASELINE_COMPRESSION
      ] = true;
      return;
   }
   int offset = (int)((barOpen - m15BreakOpen[slot]) / 900);
   if(offset <= 0 || barOpen - m15BreakOpen[slot] != offset * 900)
      return;
   bool closesBeyond = bar.close < refLow;
   if(offset == 1 && closesBeyond)
      candidate[
         regime == REGIME_CHOP ? NEXT_CLOSE_CHOP : NEXT_CLOSE_COMPRESSION
      ] = true;
   if(
      offset >= 1
      && offset <= 4
      && bar.high >= refLow
      && closesBeyond
   )
      candidate[
         regime == REGIME_CHOP ? RETEST_CHOP : RETEST_COMPRESSION
      ] = true;
   if(regime == REGIME_CHOP && offset == 3 && closesBeyond)
      candidate[M15_FOLLOW_3_CHOP] = true;
   if(regime == REGIME_CHOP && offset == 5 && closesBeyond)
      candidate[M15_FOLLOW_5_CHOP] = true;
   if(regime == REGIME_COMPRESSION && offset == 5 && closesBeyond)
      candidate[M15_FOLLOW_5_COMPRESSION] = true;
   if(regime == REGIME_COMPRESSION && offset == 7 && closesBeyond)
      candidate[M15_FOLLOW_7_COMPRESSION] = true;
}

void AddM30Candidates(
   const datetime barOpen,
   bool &candidate[]
)
{
   MqlDateTime parts;
   UtcParts(barOpen, parts);
   int minute = parts.hour * 60 + parts.min;
   if(minute < 360 || minute >= 600 || parts.min % 30 != 0)
      return;
   MqlRates bar;
   if(!ReadBar(PERIOD_M30, barOpen, bar))
      return;
   double refLow = ReferenceLow(PERIOD_M30, barOpen, 12);
   if(refLow == DBL_MAX)
      return;
   OwnedRegime regime = ClassifyRegime(barOpen);
   if(regime != REGIME_CHOP && regime != REGIME_COMPRESSION)
      return;
   if(regime == REGIME_COMPRESSION && !InpEnableCompressionSleeves)
      return;
   int slot = RegimeSlot(regime);
   if(m30BreakOpen[slot] != 0)
      return;
   double range = bar.high - bar.low;
   if(
      bar.close >= refLow
      || range <= 0.0
      || MathAbs(bar.close - bar.open) / range < BodyMinimum(regime)
   )
      return;
   m30BreakOpen[slot] = barOpen;
   candidate[
      regime == REGIME_CHOP
         ? M30_FIRST_BREAK_CHOP
         : M30_FIRST_BREAK_COMPRESSION
   ] = true;
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

int CountSleevePositions(const int sleeve)
{
   int count = 0;
   for(int index = PositionsTotal() - 1; index >= 0; --index)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(
         PositionGetString(POSITION_SYMBOL) == InpTargetSymbol
         && PositionGetInteger(POSITION_MAGIC) == SleeveMagic(sleeve)
      )
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
         && IsOwnMagic(PositionGetInteger(POSITION_MAGIC))
      )
         count++;
   }
   return count;
}

double OpenStageRisk(const bool parentOnly)
{
   double risk = 0.0;
   for(int index = PositionsTotal() - 1; index >= 0; --index)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetString(POSITION_SYMBOL) != InpTargetSymbol)
         continue;
      int sleeve = MagicSleeve(PositionGetInteger(POSITION_MAGIC));
      if(sleeve < 0 || (parentOnly && !IsParentSleeve(sleeve)))
         continue;
      risk += parentOnly ? StageOneWeight(sleeve) : StageTwoWeight(sleeve);
   }
   return risk;
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

bool VolumeGridAllows(const double lots, string &reason)
{
   double minimum = SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_MIN);
   double maximum = SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_MAX);
   double step = SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_STEP);
   if(minimum <= 0.0 || maximum < minimum || step <= 0.0)
   {
      reason = "invalid_broker_volume_grid";
      return false;
   }
   if(lots < minimum - 1e-9 || lots > maximum + 1e-9)
   {
      reason = "lot_outside_broker_limits";
      return false;
   }
   double units = lots / step;
   if(MathAbs(units - MathRound(units)) > 1e-7)
   {
      reason = "lot_not_on_broker_step";
      return false;
   }
   reason = StringFormat(
      "volume_grid_ok_min_%.2f_step_%.2f",
      minimum,
      step
   );
   return true;
}

void LatchPersistentBreaker(const string detail)
{
   persistentBreakerLatched = true;
   if(!(bool)MQLInfoInteger(MQL_TESTER) && breakerLatchName != "")
      GlobalVariableSet(breakerLatchName, 1.0);
   Audit("RISK_BREAKER_LATCHED", detail);
}

void RefreshPersistentEquityState()
{
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   if(equity <= 0.0)
      return;
   if(sessionPeakEquity <= 0.0 || equity > sessionPeakEquity)
   {
      sessionPeakEquity = equity;
      if(!(bool)MQLInfoInteger(MQL_TESTER) && peakEquityName != "")
         GlobalVariableSet(peakEquityName, sessionPeakEquity);
   }
   if(
      !persistentBreakerLatched
      && InpMaximumSessionEquityDrawdownUsd > 0.0
      && sessionPeakEquity - equity >= InpMaximumSessionEquityDrawdownUsd
   )
      LatchPersistentBreaker("persistent_peak_equity_drawdown");
}

bool TickIsFresh(const MqlTick &tick, string &reason)
{
   if(!(bool)MQLInfoInteger(MQL_TESTER))
   {
      if(!TerminalInfoInteger(TERMINAL_CONNECTED))
      {
         reason = "terminal_disconnected";
         return false;
      }
      if(tick.time <= 0 || TimeCurrent() - tick.time > InpMaximumTickAgeSeconds)
      {
         reason = "stale_tick";
         return false;
      }
   }
   reason = "tick_fresh";
   return true;
}

double OpenInitialRiskUsd(bool &valid)
{
   valid = true;
   double risk = 0.0;
   for(int index = PositionsTotal() - 1; index >= 0; --index)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(
         PositionGetString(POSITION_SYMBOL) != InpTargetSymbol
         || !IsOwnMagic(PositionGetInteger(POSITION_MAGIC))
      )
         continue;
      double stop = PositionGetDouble(POSITION_SL);
      double open = PositionGetDouble(POSITION_PRICE_OPEN);
      double volume = PositionGetDouble(POSITION_VOLUME);
      if(stop <= 0.0 || open <= 0.0 || volume <= 0.0)
      {
         valid = false;
         return DBL_MAX;
      }
      ENUM_ORDER_TYPE orderType =
         PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY
            ? ORDER_TYPE_BUY
            : ORDER_TYPE_SELL;
      double atStop = 0.0;
      if(
         !OrderCalcProfit(
            orderType,
            InpTargetSymbol,
            volume,
            open,
            stop,
            atStop
         )
      )
      {
         valid = false;
         return DBL_MAX;
      }
      risk += MathMax(0.0, -atStop);
   }
   return risk;
}

bool FundingAndCashRiskAllow(
   const MqlTick &tick,
   const double proposedStop,
   string &reason
)
{
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   if(equity < InpMinimumAccountEquityUsd)
   {
      reason = "minimum_account_equity";
      return false;
   }
   double margin = 0.0;
   if(
      !OrderCalcMargin(
         ORDER_TYPE_SELL,
         InpTargetSymbol,
         InpLotsPerTrade,
         tick.bid,
         margin
      )
      || margin < 0.0
   )
   {
      reason = "margin_calculation_failed";
      return false;
   }
   if(
      AccountInfoDouble(ACCOUNT_MARGIN_FREE) - margin
      < InpMinimumFreeMarginAfterOrderUsd
   )
   {
      reason = "minimum_free_margin_after_order";
      return false;
   }
   bool openRiskValid = false;
   double openRisk = OpenInitialRiskUsd(openRiskValid);
   double proposedAtStop = 0.0;
   if(
      !openRiskValid
      || !OrderCalcProfit(
         ORDER_TYPE_SELL,
         InpTargetSymbol,
         InpLotsPerTrade,
         tick.bid,
         proposedStop,
         proposedAtStop
      )
   )
   {
      reason = "cash_risk_calculation_failed";
      return false;
   }
   double totalRisk = openRisk + MathMax(0.0, -proposedAtStop);
   if(totalRisk > InpMaximumAggregateInitialRiskUsd + 1e-9)
   {
      reason = "maximum_aggregate_initial_risk";
      return false;
   }
   reason = "funding_and_cash_risk_ok";
   return true;
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
   const int sleeve,
   const double proposedStop,
   string &reason
)
{
   if(!auditHealthy)
   {
      reason = "audit_unavailable";
      return false;
   }
   RefreshPersistentEquityState();
   if(persistentBreakerLatched)
   {
      reason = "persistent_risk_breaker";
      return false;
   }
   if((bool)MQLInfoInteger(MQL_TESTER))
   {
      if(!InpTesterOrdersEnabled)
      {
         reason = "tester_disarmed";
         return false;
      }
   }
   else
   {
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
   }
   if(CountForeignSymbolPositions() > 0)
   {
      reason = "foreign_eurusd_position_mutex";
      return false;
   }
   if(CountSleevePositions(sleeve) > 0)
   {
      reason = "sleeve_position_mutex";
      return false;
   }
   if(CountOwnPositions() >= InpMaximumOwnPositions)
   {
      reason = "maximum_own_positions";
      return false;
   }
   if(MathAbs(InpLotsPerTrade - 0.01) > 1e-9)
   {
      reason = "frozen_0p01_lot_required";
      return false;
   }
   if(!VolumeGridAllows(InpLotsPerTrade, reason))
      return false;
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
   if(!TickIsFresh(tick, reason))
      return false;
   if((tick.ask - tick.bid) / PipSize() > InpMaximumSpreadPips)
   {
      reason = "spread_limit";
      return false;
   }
   int dailyEntries = 0;
   double dailyPnl = ClosedPnlSince(UtcDayStart(TimeCurrent()), dailyEntries);
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
   if(!FundingAndCashRiskAllow(tick, proposedStop, reason))
      return false;
   reason = "all_order_guards_pass";
   return true;
}

void PersistSignalDate(const int sleeve, const int dateKey)
{
   lastSignalDate[sleeve] = dateKey;
   if(!(bool)MQLInfoInteger(MQL_TESTER))
      GlobalVariableSet(signalDateNames[sleeve], (double)dateKey);
}

void MarkCandidatesHandled(bool &candidate[])
{
   for(int sleeve = 0; sleeve < SLEEVE_COUNT; ++sleeve)
      if(candidate[sleeve])
         PersistSignalDate(sleeve, stateDateKey);
}

bool ConfirmSleevePosition(
   const int sleeve,
   const double expectedStop,
   const double expectedTarget,
   string &reason
)
{
   if(trade.ResultRetcode() != TRADE_RETCODE_DONE)
   {
      reason = StringFormat(
         "retcode_%u_%s",
         trade.ResultRetcode(),
         trade.ResultRetcodeDescription()
      );
      return false;
   }
   if(
      trade.ResultDeal() == 0
      || MathAbs(trade.ResultVolume() - InpLotsPerTrade) > 1e-9
   )
   {
      reason = "missing_deal_or_wrong_fill_volume";
      return false;
   }
   if(CountSleevePositions(sleeve) != 1)
   {
      reason = "confirmed_sleeve_position_count_not_one";
      return false;
   }
   for(int index = PositionsTotal() - 1; index >= 0; --index)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(
         PositionGetString(POSITION_SYMBOL) != InpTargetSymbol
         || PositionGetInteger(POSITION_MAGIC) != SleeveMagic(sleeve)
      )
         continue;
      double volume = PositionGetDouble(POSITION_VOLUME);
      double stop = PositionGetDouble(POSITION_SL);
      double target = PositionGetDouble(POSITION_TP);
      if(MathAbs(volume - InpLotsPerTrade) > 1e-9)
      {
         reason = "position_volume_mismatch";
         return false;
      }
      if(
         stop <= 0.0
         || target <= 0.0
         || MathAbs(stop - expectedStop) > 2.0 * _Point
         || MathAbs(target - expectedTarget) > 2.0 * _Point
      )
      {
         reason = "broker_side_stop_or_target_mismatch";
         return false;
      }
      reason = StringFormat(
         "deal_%I64u_position_%I64u_volume_%.2f",
         trade.ResultDeal(),
         ticket,
         volume
      );
      return true;
   }
   reason = "owned_position_not_found_after_fill";
   return false;
}

void ProcessCandidates(bool &candidate[])
{
   bool eligible[];
   bool stageOnePass[];
   ArrayResize(eligible, SLEEVE_COUNT);
   ArrayResize(stageOnePass, SLEEVE_COUNT);
   MqlTick tick;
   bool haveTick = SymbolInfoTick(_Symbol, tick);
   bool spreadOkay = haveTick
      && (tick.ask - tick.bid) / PipSize() <= InpMaximumSpreadPips;
   for(int sleeve = 0; sleeve < SLEEVE_COUNT; ++sleeve)
   {
      eligible[sleeve] =
         candidate[sleeve] && lastSignalDate[sleeve] != stateDateKey;
      stageOnePass[sleeve] = !IsParentSleeve(sleeve);
      if(eligible[sleeve])
         PersistSignalDate(sleeve, stateDateKey);
      if(eligible[sleeve] && !spreadOkay)
      {
         Audit("ENTRY_FILTER_REJECTED", "spread_or_tick", sleeve);
         eligible[sleeve] = false;
      }
   }
   int stageOnePriority[6] = {
      BASELINE_CHOP,
      BASELINE_COMPRESSION,
      NEXT_CLOSE_CHOP,
      NEXT_CLOSE_COMPRESSION,
      RETEST_CHOP,
      RETEST_COMPRESSION
   };
   double stageOneRisk = OpenStageRisk(true);
   for(int index = 0; index < 6; ++index)
   {
      int sleeve = stageOnePriority[index];
      if(!eligible[sleeve])
         continue;
      double nextRisk = stageOneRisk + StageOneWeight(sleeve);
      if(nextRisk > STAGE_ONE_MAXIMUM_RISK + 1e-9)
      {
         Audit("STAGE1_CAP_REJECTED", "parent_2R_cap", sleeve);
         continue;
      }
      stageOnePass[sleeve] = true;
      stageOneRisk = nextRisk;
   }
   int stageTwoPriority[12] = {
      NEXT_CLOSE_CHOP,
      BASELINE_CHOP,
      BASELINE_COMPRESSION,
      RETEST_COMPRESSION,
      NEXT_CLOSE_COMPRESSION,
      RETEST_CHOP,
      M30_FIRST_BREAK_CHOP,
      M30_FIRST_BREAK_COMPRESSION,
      M15_FOLLOW_3_CHOP,
      M15_FOLLOW_5_CHOP,
      M15_FOLLOW_5_COMPRESSION,
      M15_FOLLOW_7_COMPRESSION
   };
   double stageTwoRisk = OpenStageRisk(false);
   for(int index = 0; index < SLEEVE_COUNT; ++index)
   {
      int sleeve = stageTwoPriority[index];
      if(!eligible[sleeve] || !stageOnePass[sleeve])
         continue;
      double nextRisk = stageTwoRisk + StageTwoWeight(sleeve);
      if(nextRisk > STAGE_TWO_MAXIMUM_RISK + 1e-9)
      {
         Audit("STAGE2_CAP_REJECTED", "portfolio_2p5R_cap", sleeve);
         continue;
      }
      stageTwoRisk = nextRisk;
      OwnedRegime regime = SleeveRegime(sleeve);
      double atr[];
      if(!CopyIndicator(h1Atr, 0, 1, 1, atr) || atr[0] <= 0.0)
      {
         Audit("ENTRY_FILTER_REJECTED", "h1_atr_unavailable", sleeve);
         continue;
      }
      double stopDistance = STOP_ATR_MULTIPLE * atr[0];
      double stop = NormalizeDouble(tick.bid + stopDistance, _Digits);
      double target = NormalizeDouble(
         tick.bid - TargetR(regime) * stopDistance,
         _Digits
      );
      if(!Audit(
         "SIGNAL",
         "two_stage_causal_caps_passed",
         sleeve,
         "SHORT",
         InpLotsPerTrade,
         tick.bid,
         stop,
         target
      ))
         continue;
      string guardReason = "";
      if(!NewOrderAllowed(sleeve, stop, guardReason))
      {
         Audit(
            "ORDER_BLOCKED",
            guardReason,
            sleeve,
            "SHORT",
            InpLotsPerTrade,
            tick.bid,
            stop,
            target
         );
         continue;
      }
      if(
         !Audit(
            "ORDER_INTENT",
            "all_pretrade_guards_passed",
            sleeve,
            "SHORT",
            InpLotsPerTrade,
            tick.bid,
            stop,
            target
         )
      )
         continue;
      trade.SetExpertMagicNumber(SleeveMagic(sleeve));
      trade.SetDeviationInPoints(InpDeviationPoints);
      trade.SetTypeFillingBySymbol(_Symbol);
      string comment = InpOrderComment + "_" + SleeveCode(sleeve);
      bool sent = trade.Sell(
         InpLotsPerTrade,
         _Symbol,
         0.0,
         stop,
         target,
         comment
      );
      string executionReason = "";
      bool confirmed = sent
         && ConfirmSleevePosition(
            sleeve,
            stop,
            target,
            executionReason
         );
      Audit(
         confirmed ? "ORDER_CONFIRMED" : "ORDER_EXECUTION_UNCERTAIN",
         executionReason == ""
            ? trade.ResultRetcodeDescription()
            : executionReason,
         sleeve,
         "SHORT",
         InpLotsPerTrade,
         tick.bid,
         stop,
         target
      );
      if(!confirmed)
         LatchPersistentBreaker("order_execution_not_confirmed");
   }
}

void EvaluateCompletedAt(const datetime currentM15Open, const bool emit)
{
   bool candidate[];
   ResetCandidateFlags(candidate);
   datetime m15Open = currentM15Open - 15 * 60;
   EnsureStateDate(m15Open);
   AddM15Candidates(m15Open, candidate);
   MqlDateTime parts;
   UtcParts(currentM15Open, parts);
   if(parts.min % 30 == 0)
      AddM30Candidates(currentM15Open - 30 * 60, candidate);
   if(emit)
      ProcessCandidates(candidate);
   else
      MarkCandidatesHandled(candidate);
}

bool RebuildDailyState(const datetime currentM15Open)
{
   datetime start = UtcDayStart(currentM15Open);
   EnsureStateDate(currentM15Open);
   m15BreakOpen[0] = 0;
   m15BreakOpen[1] = 0;
   m30BreakOpen[0] = 0;
   m30BreakOpen[1] = 0;
   datetime firstClose = start + 6 * 3600 + 15 * 60;
   if(currentM15Open < firstClose)
      return true;
   for(
      datetime closeTime = firstClose;
      closeTime <= currentM15Open;
      closeTime += 15 * 60
   )
      EvaluateCompletedAt(closeTime, false);
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
      int sleeve = MagicSleeve(magic);
      if(
         PositionGetString(POSITION_SYMBOL) != InpTargetSymbol
         || sleeve < 0
      )
         continue;
      datetime opened = (datetime)PositionGetInteger(POSITION_TIME);
      if(TimeCurrent() - opened < InpMaximumHoldM15Bars * 15 * 60)
         continue;
      datetime attemptBar = iTime(_Symbol, PERIOD_M15, 0);
      if(
         attemptBar > 0
         && lastTimeExitAttemptBar[sleeve] == attemptBar
      )
         continue;
      lastTimeExitAttemptBar[sleeve] = attemptBar;
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
            Audit("TIME_EXIT_BLOCKED", reason, sleeve);
            continue;
         }
      }
      trade.SetExpertMagicNumber(magic);
      bool closed = trade.PositionClose(ticket, InpDeviationPoints);
      string eventName = "TIME_EXIT_FAILED";
      bool confirmedClosed = closed
         && trade.ResultRetcode() == TRADE_RETCODE_DONE
         && !PositionSelectByTicket(ticket);
      if(confirmedClosed)
         eventName = "TIME_EXIT_CONFIRMED";
      else if(trade.ResultRetcode() == TRADE_RETCODE_MARKET_CLOSED)
         eventName = "TIME_EXIT_DEFERRED";
      Audit(
         eventName,
         trade.ResultRetcodeDescription(),
         sleeve
      );
      if(!confirmedClosed && eventName != "TIME_EXIT_DEFERRED")
         LatchPersistentBreaker("time_exit_not_confirmed");
   }
}

void ManagePersistentBreakerExits()
{
   if(!persistentBreakerLatched)
      return;
   if((bool)MQLInfoInteger(MQL_TESTER))
   {
      if(!InpTesterOrdersEnabled)
         return;
   }
   else
   {
      string identityReason = "";
      if(!IdentityAllowsManagement(identityReason))
      {
         Audit("BREAKER_EXIT_BLOCKED", identityReason);
         return;
      }
   }
   for(int index = PositionsTotal() - 1; index >= 0; --index)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      long magic = PositionGetInteger(POSITION_MAGIC);
      int sleeve = MagicSleeve(magic);
      if(
         PositionGetString(POSITION_SYMBOL) != InpTargetSymbol
         || sleeve < 0
      )
         continue;
      trade.SetExpertMagicNumber(magic);
      bool requested = trade.PositionClose(ticket, InpDeviationPoints);
      bool confirmed = requested
         && trade.ResultRetcode() == TRADE_RETCODE_DONE
         && !PositionSelectByTicket(ticket);
      Audit(
         confirmed
            ? "BREAKER_EXIT_CONFIRMED"
            : "BREAKER_EXIT_RETRY_REQUIRED",
         trade.ResultRetcodeDescription(),
         sleeve
      );
   }
}

bool AcquireMutex()
{
   string mutexBase = StringFormat(
      "CODEX_EUH4FREQV2_%I64d_%s",
      AccountInfoInteger(ACCOUNT_LOGIN),
      InpTargetSymbol
   );
   mutexOwnerName = mutexBase + "_OWNER";
   mutexHeartbeatName = mutexBase + "_HEARTBEAT";
   double now = (double)TimeLocal();
   if(GlobalVariableCheck(mutexHeartbeatName))
   {
      double heartbeat = GlobalVariableGet(mutexHeartbeatName);
      if(now - heartbeat < 180.0)
         return false;
   }
   mutexOwnerToken =
      now * 1000.0 + (double)(GetTickCount() % 997);
   GlobalVariableSet(mutexOwnerName, mutexOwnerToken);
   GlobalVariableSet(mutexHeartbeatName, now);
   mutexOwned = true;
   EventSetTimer(60);
   return true;
}

bool ReconcilePositions(string &reason)
{
   if(CountForeignSymbolPositions() > 0)
   {
      reason = "foreign_eurusd_position";
      return false;
   }
   if(CountOwnPositions() > InpMaximumOwnPositions)
   {
      reason = "too_many_owned_positions";
      return false;
   }
   for(int sleeve = 0; sleeve < SLEEVE_COUNT; ++sleeve)
      if(CountSleevePositions(sleeve) > 1)
      {
         reason = "duplicate_sleeve_position_" + SleeveText(sleeve);
         return false;
      }
   reason = "position_reconciliation_ok";
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
      InpBaseMagicNumber != 26073100
      || InpOrderComment != "EUH4FREQV2"
      || InpEnableCompressionSleeves
      || InpBrokerUtcOffsetHours != 0
      || MathAbs(InpMaximumSpreadPips - 2.0) > 1e-9
      || InpMaximumHoldM15Bars != 48
      || InpMaximumOwnPositions != 6
      || InpMaximumTradesPerUtcDay != 6
      || MathAbs(
         InpMaximumDailyClosedLossUsd - FROZEN_DAILY_LOSS_USD
      ) > 1e-9
      || MathAbs(
         InpMaximumRolling5DayClosedLossUsd
            - FROZEN_ROLLING_LOSS_USD
      ) > 1e-9
      || MathAbs(
         InpMaximumSessionEquityDrawdownUsd
            - FROZEN_EQUITY_DRAWDOWN_USD
      ) > 1e-9
      || MathAbs(
         InpMaximumAggregateInitialRiskUsd
            - FROZEN_AGGREGATE_INITIAL_RISK_USD
      ) > 1e-9
      || MathAbs(
         InpMinimumAccountEquityUsd
            - FROZEN_MINIMUM_ACCOUNT_EQUITY_USD
      ) > 1e-9
      || MathAbs(
         InpMinimumFreeMarginAfterOrderUsd
            - FROZEN_MINIMUM_FREE_MARGIN_USD
      ) > 1e-9
      || InpMaximumTickAgeSeconds != 10
      || InpDeviationPoints != 10
   )
   {
      Audit("INIT_FAILED", "frozen_exposure_limits_changed");
      return INIT_PARAMETERS_INCORRECT;
   }
   string volumeReason = "";
   if(
      MathAbs(InpLotsPerTrade - 0.01) > 1e-9
      || !VolumeGridAllows(InpLotsPerTrade, volumeReason)
   )
   {
      Audit("INIT_FAILED", "illegal_volume_" + volumeReason);
      return INIT_PARAMETERS_INCORRECT;
   }
   string reconcileReason = "";
   if(!ReconcilePositions(reconcileReason))
   {
      Audit("INIT_FAILED", reconcileReason);
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
   schemaName = StringFormat(
      "CODEX_EUH4FREQV2_SCHEMA_%I64d_%s",
      AccountInfoInteger(ACCOUNT_LOGIN),
      InpTargetSymbol
   );
   peakEquityName = StringFormat(
      "CODEX_EUH4FREQV2_PEAK_%I64d_%s",
      AccountInfoInteger(ACCOUNT_LOGIN),
      InpTargetSymbol
   );
   breakerLatchName = StringFormat(
      "CODEX_EUH4FREQV2_BREAKER_%I64d_%s",
      AccountInfoInteger(ACCOUNT_LOGIN),
      InpTargetSymbol
   );
   if(
      !(bool)MQLInfoInteger(MQL_TESTER)
      && GlobalVariableCheck(schemaName)
      && MathAbs(GlobalVariableGet(schemaName) - CONTRACT_SCHEMA_FINGERPRINT)
         > 0.5
   )
   {
      Audit("INIT_FAILED", "persisted_schema_mismatch");
      return INIT_FAILED;
   }
   if(!(bool)MQLInfoInteger(MQL_TESTER))
      GlobalVariableSet(schemaName, CONTRACT_SCHEMA_FINGERPRINT);
   for(int sleeve = 0; sleeve < SLEEVE_COUNT; ++sleeve)
   {
      lastSignalDate[sleeve] = 0;
      lastTimeExitAttemptBar[sleeve] = 0;
      signalDateNames[sleeve] = StringFormat(
         "CODEX_EUH4FREQV2_SIG_%I64d_%s_%02d",
         AccountInfoInteger(ACCOUNT_LOGIN),
         InpTargetSymbol,
         sleeve
      );
      if(
         !(bool)MQLInfoInteger(MQL_TESTER)
         && GlobalVariableCheck(signalDateNames[sleeve])
      )
         lastSignalDate[sleeve] =
            (int)GlobalVariableGet(signalDateNames[sleeve]);
   }
   sessionStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   sessionPeakEquity = sessionStartEquity;
   if(!(bool)MQLInfoInteger(MQL_TESTER))
   {
      if(GlobalVariableCheck(peakEquityName))
         sessionPeakEquity = MathMax(
            sessionPeakEquity,
            GlobalVariableGet(peakEquityName)
         );
      GlobalVariableSet(peakEquityName, sessionPeakEquity);
      persistentBreakerLatched =
         GlobalVariableCheck(breakerLatchName)
         && GlobalVariableGet(breakerLatchName) >= 0.5;
   }
   lastM15Open = iTime(_Symbol, PERIOD_M15, 0);
   trade.SetDeviationInPoints(InpDeviationPoints);
   if(!Audit(
      "INIT_OK",
      ((bool)MQLInfoInteger(MQL_TESTER)
         ? "tester_"
         : (InpShadowMode ? "shadow_demo_" : "ordering_demo_"))
         + volumeReason
   ))
      return INIT_FAILED;
   if(!Audit(
      "STARTUP_LATCH",
      TimeToString(lastM15Open, TIME_DATE | TIME_MINUTES)
   ))
      return INIT_FAILED;
   return INIT_SUCCEEDED;
}

void OnTimer()
{
   RefreshPersistentEquityState();
   if(!mutexOwned)
      return;
   if(
      !GlobalVariableCheck(mutexOwnerName)
      || MathAbs(
         GlobalVariableGet(mutexOwnerName) - mutexOwnerToken
      ) > 0.5
   )
   {
      mutexOwned = false;
      Audit("MUTEX_OWNERSHIP_LOST", "instance_removed_fail_closed");
      ExpertRemove();
      return;
   }
   GlobalVariableSet(mutexHeartbeatName, (double)TimeLocal());
}

void OnDeinit(const int reason)
{
   Audit("DEINIT", IntegerToString(reason));
   EventKillTimer();
   if(
      mutexOwned
      && GlobalVariableCheck(mutexOwnerName)
      && MathAbs(
         GlobalVariableGet(mutexOwnerName) - mutexOwnerToken
      ) <= 0.5
   )
   {
      GlobalVariableDel(mutexOwnerName);
      if(GlobalVariableCheck(mutexHeartbeatName))
         GlobalVariableDel(mutexHeartbeatName);
   }
   if(h1Atr != INVALID_HANDLE)
      IndicatorRelease(h1Atr);
   if(h4Atr != INVALID_HANDLE)
      IndicatorRelease(h4Atr);
   if(h4Adx != INVALID_HANDLE)
      IndicatorRelease(h4Adx);
   if(h4Ema != INVALID_HANDLE)
      IndicatorRelease(h4Ema);
}

void OnTradeTransaction(
   const MqlTradeTransaction &transaction,
   const MqlTradeRequest &request,
   const MqlTradeResult &result
)
{
   if(
      transaction.symbol != InpTargetSymbol
      && request.symbol != InpTargetSymbol
   )
      return;
   if(transaction.type == TRADE_TRANSACTION_REQUEST)
      Audit(
         "TRADE_TRANSACTION_REQUEST",
         StringFormat(
            "retcode_%u_deal_%I64u_order_%I64u_volume_%.2f",
            result.retcode,
            result.deal,
            result.order,
            result.volume
         )
      );
   else if(transaction.type == TRADE_TRANSACTION_DEAL_ADD)
      Audit(
         "TRADE_TRANSACTION_DEAL",
         StringFormat(
            "deal_%I64u_order_%I64u_position_%I64u_volume_%.2f_price_%s",
            transaction.deal,
            transaction.order,
            transaction.position,
            transaction.volume,
            DoubleToString(transaction.price, _Digits)
         )
      );
   else if(transaction.type == TRADE_TRANSACTION_POSITION)
      Audit(
         "TRADE_TRANSACTION_POSITION",
         StringFormat(
            "position_%I64u_volume_%.2f_price_%s_sl_%s_tp_%s",
            transaction.position,
            transaction.volume,
            DoubleToString(transaction.price, _Digits),
            DoubleToString(transaction.price_sl, _Digits),
            DoubleToString(transaction.price_tp, _Digits)
         )
      );
}

void OnTick()
{
   RefreshPersistentEquityState();
   ManagePersistentBreakerExits();
   ManageTimeExits();
   datetime currentM15 = iTime(_Symbol, PERIOD_M15, 0);
   if(currentM15 == 0)
      return;
   if(!stateReady)
   {
      if(!RebuildDailyState(currentM15))
         return;
      stateReady = true;
      lastM15Open = currentM15;
      Audit(
         "RESTART_RECOVERY_OK",
         TimeToString(currentM15, TIME_DATE | TIME_MINUTES)
      );
      return;
   }
   if(currentM15 == lastM15Open)
      return;
   lastM15Open = currentM15;
   EvaluateCompletedAt(currentM15, true);
   MqlDateTime parts;
   UtcParts(currentM15, parts);
   int dateKey = UtcDateKey(currentM15);
   if(
      InpRestartExerciseUtcHour >= 0
      && parts.hour == InpRestartExerciseUtcHour
      && parts.min == 0
      && dateKey != lastRestartExerciseDate
   )
   {
      RebuildDailyState(currentM15);
      lastRestartExerciseDate = dateKey;
      Audit(
         "RESTART_EXERCISE_OK",
         TimeToString(currentM15, TIME_DATE | TIME_MINUTES)
      );
   }
}

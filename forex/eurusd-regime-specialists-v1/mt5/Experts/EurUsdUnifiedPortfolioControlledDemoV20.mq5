#property strict
#property version   "20.66"
#property description "EURUSD V20R6 shared account; strategy-scoped USD risk; no artificial funding floor"

#include <Trade/Trade.mqh>

input string InpRunId = "EURUSD_UNIFIED_PORTFOLIO_V20R6_ACCOUNT_1033030";
input string InpTargetSymbol = "EURUSD";
input long InpBaseMagicNumber = 26082000;
input long InpRsiMagicNumber = 26082090;
input string InpOrderComment = "EUV20";
input bool InpShadowMode = true;
input bool InpEnableDemoOrders = false;
input bool InpEmergencyStop = true;
input bool InpTesterOrdersEnabled = false;
input int InpTesterSleeveMask = 3;
input bool InpEnableCompressionSleeves = true;
input bool InpEnableRsiOrders = false;
input long InpAllowedAccountLogin = 0;
input string InpAllowedServer = "";
input string InpDemoArmToken = "DISARMED";
input string InpProspectiveStartUtc = "2026.08.01 00:00";
input int InpBrokerUtcOffsetHours = 0;
input bool InpResetPersistentState = false;
input string InpPersistentResetToken = "NO_RESET";
input double InpLotsPerTrade = 0.01;
input double InpMaximumSpreadPips = 2.0;
input int InpMaximumHoldM15Bars = 48;
input int InpMaximumTradesPerUtcDay = 7;
input int InpMaximumOwnPositions = 7;
input int InpMaximumPortfolioPositions = 7;
input double InpMaximumOwnVolumeLots = 0.15;
input double InpMaximumPortfolioVolumeLots = 0.16;
input double InpMaximumDailyClosedLossUsd = 60.0;
input double InpMaximumRolling5DayClosedLossUsd = 120.0;
input double InpMaximumCoreCalendarMonthClosedLossUsd = 10.0;
input double InpMaximumFrequencySleeveCalendarMonthClosedLossUsd = 1.0;
input double InpMaximumSessionEquityDrawdownUsd = 180.0;
input double InpMaximumAggregateInitialRiskUsd = 75.0;
input double InpMinimumAccountEquityUsd = 0.0;
input double InpMinimumFreeMarginAfterOrderUsd = 0.0;
input int InpMaximumTickAgeSeconds = 10;
input int InpHeartbeatIntervalSeconds = 300;
input int InpDeviationPoints = 10;
input int InpStateRoundTripExerciseUtcHour = -1;
input int InpTesterStateFaultMode = 0;
input int InpTesterGuardFaultMode = 0;
input string InpAuditLogName = "EURUSD_UNIFIED_PORTFOLIO_V20R6_SHARED_ACCOUNT.csv";

const int ATR_PERIOD = 14;
const int ADX_PERIOD = 14;
const int EMA_PERIOD = 50;
const int BASELINE_BARS = 504;
const double CHOP_BODY_MINIMUM = 0.35;
const double COMPRESSION_BODY_MINIMUM = 0.55;
input double InpResearchStopAtrMultiple = 2.00;
const double CHOP_TARGET_R = 1.25;
const double BASELINE_COMPRESSION_TARGET_R = 1.75;
const double M15_FOLLOW_5_CHOP_TARGET_R = 0.75;
input int InpResearchSleeveMask = 2047;
input int InpResearchM30Mode = 6;
input int InpResearchFridayReversalMaxBars = 6;
input double InpResearchFridayReversalBodyMinimum = 0.35;
input double InpResearchFridayReversalStopAtrMultiple = 1.50;
input double InpResearchFridayReversalTargetR = 1.50;
input double InpResearchMonthlyPeakActivationUsd = 7.50;
input double InpResearchMonthlyGivebackUsd = 7.50;
const double COMPRESSION_TARGET_R = 2.0;
const double STAGE_ONE_MAXIMUM_RISK = 2.0;
const double STAGE_TWO_MAXIMUM_RISK = 2.5;
input int InpResearchEventTradeCap = 7;
const string ARM_TOKEN = "I_ACCEPT_DEMO_001";
const string PERSISTENT_RESET_TOKEN = "RESET_EUV20R2_ONCE";
const double CONTRACT_SCHEMA_FINGERPRINT = 2020260809.0;
const double FROZEN_DAILY_LOSS_USD = 60.0;
const double FROZEN_ROLLING_LOSS_USD = 120.0;
const double FROZEN_CORE_MONTHLY_LOSS_USD = 10.0;
const double FROZEN_FREQUENCY_SLEEVE_MONTHLY_LOSS_USD = 1.0;
const double FROZEN_EQUITY_DRAWDOWN_USD = 180.0;
const double FROZEN_AGGREGATE_INITIAL_RISK_USD = 75.0;
const double FROZEN_MINIMUM_ACCOUNT_EQUITY_USD = 0.0;
const long FROZEN_MINIMUM_EQUITY_WAIVER_ACCOUNT = 1033030;
const double FROZEN_MINIMUM_FREE_MARGIN_USD = 0.0;
const int RSI_SLEEVE_ID = 12;
const int RSI_STATE_SCHEMA = 22;
const long RSI_CONTRACT_FINGERPRINT = 2020260809;
const int RSI_BANDS_PERIOD = 20;
const int RSI_PERIOD = 14;
const double RSI_OVERSOLD_INCLUSIVE = 30.0;
const double RSI_MINIMUM_BODY_FRACTION = 0.4;
const int RSI_RECENT_STOP_LOOKBACK_M15_BARS = 6;
const double RSI_STOP_ATR_MULTIPLE = 1.4;
const double RSI_STOP_FLOOR_PIPS = 3.0;
const double RSI_STOP_CEILING_PIPS = 70.0;
const double RSI_TARGET_R = 1.5;
const double RSI_RAW_SIGNAL_SPREAD_PIPS = 10.0;
const int RSI_MAXIMUM_TRADES_PER_UTC_DAY = 20;
const double AED_PER_USD = 3.6725;

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
int rsiAtr = INVALID_HANDLE;
int rsiBands = INVALID_HANDLE;
int rsiIndicator = INVALID_HANDLE;
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
string breakerLatchFileName = "";
string signalDateNames[12];
bool mutexOwned = false;
bool stateReady = false;
bool auditHealthy = true;
bool persistentBreakerLatched = false;
bool criticalPersistenceHealthy = true;
string portfolioOrderLockName = "";
double portfolioOrderLockToken = 0.0;
bool managerOnlyMode = false;
string managerOnlyReason = "";
datetime rsiProspectiveStart = 0;
datetime rsiVirtualEntryTime = 0;
datetime rsiLastVirtualExitTime = 0;
int rsiDailyDateKey = 0;
int rsiDailyEntryCount = 0;
bool rsiVirtualActive = false;
double rsiVirtualEntry = 0.0;
double rsiVirtualStop = 0.0;
double rsiVirtualTarget = 0.0;
string rsiStatePrefix = "";
bool rsiStateReady = false;
bool rsiTesterStateRoundTrip = false;
bool rsiTesterStateSaveExercise = false;
int restartExercisesWithOpenPositions = 0;
datetime lastHeartbeatAuditLocal = 0;

string BoolText(const bool value)
{
   return value ? "true" : "false";
}

bool AccountCurrencyUsdFactor(double &factor)
{
   string currency = AccountInfoString(ACCOUNT_CURRENCY);
   if(currency == "USD")
   {
      factor = 1.0;
      return true;
   }
   if(currency == "AED")
   {
      factor = 1.0 / AED_PER_USD;
      return true;
   }
   factor = 0.0;
   return false;
}

double AccountValueUsd(const double accountValue)
{
   double factor = 0.0;
   if(!AccountCurrencyUsdFactor(factor))
      return DBL_MAX;
   return accountValue * factor;
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
      case BASELINE_CHOP: return "FRIDAY_FALSE_BREAK_REVERSAL";
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
      case 12: return "H4_STRENGTH_RSI";
   }
   return "NONE";
}

string SleeveCode(const int sleeve)
{
   switch(sleeve)
   {
      case BASELINE_CHOP: return "FR";
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
      case 12: return "RSI";
   }
   return "NONE";
}


double ResearchLots(const int sleeve)
{
   // Every specialist expresses closely related EURUSD risk.  Equal sizing
   // prevents the historically weaker NC/F3C/M30C sleeves from dominating a
   // losing month merely because they were assigned 2x-3x more volume.
   return InpLotsPerTrade;
}

bool IsProtectedCoreSleeve(const int sleeve)
{
   return (
      sleeve == NEXT_CLOSE_CHOP
      || sleeve == M15_FOLLOW_3_CHOP
      || sleeve == M30_FIRST_BREAK_CHOP
   );
}

bool IsGuardedFrequencySleeve(const int sleeve)
{
   return (
      sleeve == BASELINE_COMPRESSION
      || sleeve == M15_FOLLOW_5_CHOP
      || sleeve == M30_FIRST_BREAK_COMPRESSION
   );
}

OwnedRegime SleeveRegime(const int sleeve)
{
   if(sleeve == RSI_SLEEVE_ID)
      return REGIME_OTHER;
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

bool IsOrderEnabledSleeve(const int sleeve)
{
   return (
      (sleeve == BASELINE_CHOP && (InpResearchSleeveMask & 1) != 0)
      || (sleeve == BASELINE_COMPRESSION && (InpResearchSleeveMask & 2) != 0)
      || (sleeve == NEXT_CLOSE_CHOP && (InpResearchSleeveMask & 4) != 0)
      || (sleeve == NEXT_CLOSE_COMPRESSION && (InpResearchSleeveMask & 8) != 0)
      || (sleeve == RETEST_CHOP && (InpResearchSleeveMask & 16) != 0)
      || (sleeve == RETEST_COMPRESSION && (InpResearchSleeveMask & 32) != 0)
      || (sleeve == M15_FOLLOW_3_CHOP && (InpResearchSleeveMask & 64) != 0)
      || (sleeve == M15_FOLLOW_5_CHOP && (InpResearchSleeveMask & 128) != 0)
      || (sleeve == M15_FOLLOW_5_COMPRESSION && (InpResearchSleeveMask & 256) != 0)
      || (sleeve == M15_FOLLOW_7_COMPRESSION && (InpResearchSleeveMask & 512) != 0)
      || (sleeve == M30_FIRST_BREAK_CHOP && (InpResearchSleeveMask & 1024) != 0)
      || (sleeve == M30_FIRST_BREAK_COMPRESSION && (InpResearchSleeveMask & 2048) != 0)
   );
}

bool IsLongSleeve(const int sleeve)
{
   return sleeve == BASELINE_CHOP || sleeve == RSI_SLEEVE_ID;
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

bool IsPortfolioMagic(const long magic)
{
   return IsOwnMagic(magic) || magic == InpRsiMagicNumber;
}

double BodyMinimum(const OwnedRegime regime)
{
   return regime == REGIME_CHOP
      ? CHOP_BODY_MINIMUM
      : COMPRESSION_BODY_MINIMUM;
}

double TargetR(const OwnedRegime regime, const int sleeve)
{
   if(sleeve == BASELINE_CHOP)
      return InpResearchFridayReversalTargetR;
   if(sleeve == BASELINE_COMPRESSION)
      return BASELINE_COMPRESSION_TARGET_R;
   if(sleeve == M15_FOLLOW_5_CHOP)
      return M15_FOLLOW_5_CHOP_TARGET_R;
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

bool ServerClockIsUtcAligned(string &reason)
{
   if((bool)MQLInfoInteger(MQL_TESTER))
   {
      reason = "tester_clock_contract";
      return InpBrokerUtcOffsetHours == 0;
   }
   datetime serverNow = TimeTradeServer();
   datetime utcNow = TimeGMT();
   if(serverNow <= 0 || utcNow <= 0)
   {
      reason = "server_or_utc_clock_unavailable";
      return false;
   }
   long difference = (long)MathAbs((double)(serverNow - utcNow));
   if(difference > 5 * 60)
   {
      reason = StringFormat("server_not_utc_offset_seconds_%I64d", difference);
      return false;
   }
   reason = "server_clock_utc_aligned";
   return true;
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


datetime UtcMonthStart(const datetime brokerTime)
{
   MqlDateTime parts;
   UtcParts(brokerTime, parts);
   parts.day = 1;
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
   long auditMagic = sleeve == RSI_SLEEVE_ID
      ? InpRsiMagicNumber
      : (sleeve >= 0 ? SleeveMagic(sleeve) : InpBaseMagicNumber);
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
      auditMagic,
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

bool PersistGlobalVerified(
   const string name,
   const double value,
   const string detail
)
{
   if(name == "")
   {
      criticalPersistenceHealthy = false;
      Audit("CRITICAL_STATE_PERSIST_FAILED", detail + "_empty_name");
      return false;
   }
   ResetLastError();
   if(GlobalVariableSet(name, value) == 0)
   {
      criticalPersistenceHealthy = false;
      Audit(
         "CRITICAL_STATE_PERSIST_FAILED",
         detail + StringFormat("_set_error_%d", GetLastError())
      );
      return false;
   }
   GlobalVariablesFlush();
   double observed = 0.0;
   if(
      !GlobalVariableGet(name, observed)
      || MathAbs(observed - value) > 1e-7
   )
   {
      criticalPersistenceHealthy = false;
      Audit("CRITICAL_STATE_PERSIST_FAILED", detail + "_readback_mismatch");
      return false;
   }
   return true;
}

bool PersistBreakerFile(const string detail)
{
   if((bool)MQLInfoInteger(MQL_TESTER))
      return true;
   int handle = FileOpen(
      breakerLatchFileName,
      FILE_WRITE | FILE_TXT | FILE_COMMON
   );
   if(handle == INVALID_HANDLE)
   {
      criticalPersistenceHealthy = false;
      Audit(
         "CRITICAL_STATE_PERSIST_FAILED",
         detail + StringFormat("_breaker_file_open_error_%d", GetLastError())
      );
      return false;
   }
   bool okay = FileWrite(
      handle,
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      detail
   ) > 0;
   FileFlush(handle);
   FileClose(handle);
   if(!okay || !FileIsExist(breakerLatchFileName, FILE_COMMON))
   {
      criticalPersistenceHealthy = false;
      Audit("CRITICAL_STATE_PERSIST_FAILED", detail + "_breaker_file_verify");
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
   // Friday uses a different, causal market mechanism.  The original
   // continuation shorts failed across every sleeve and entry hour because
   // the downside break usually snapped back.  Record the break, then trade
   // only after a completed bullish M15 bar closes back above the fixed
   // midnight-to-05:45 UTC reference low.  No future bar is inspected.
   if(parts.day_of_week == 5)
   {
      if(m15BreakOpen[slot] == 0)
      {
         if(qualifiedBreak)
            m15BreakOpen[slot] = barOpen;
         return;
      }
      int fridayOffset = (int)((barOpen - m15BreakOpen[slot]) / 900);
      if(
         fridayOffset >= 1
         && fridayOffset <= InpResearchFridayReversalMaxBars
         && barOpen - m15BreakOpen[slot] == fridayOffset * 900
         && range > 0.0
         && bar.close > refLow
         && bar.close > bar.open
         && MathAbs(bar.close - bar.open) / range
            >= InpResearchFridayReversalBodyMinimum
      )
         candidate[BASELINE_CHOP] = true;
      return;
   }
   if(m15BreakOpen[slot] == 0)
   {
      if(!qualifiedBreak)
         return;
      m15BreakOpen[slot] = barOpen;
      if(regime == REGIME_COMPRESSION)
         candidate[BASELINE_COMPRESSION] = true;
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
      && offset <= 3
      && bar.high >= refLow
      && closesBeyond
      && bar.close < bar.open
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
   // Friday continuation is replaced by the M15 false-break reversal above.
   if(parts.day_of_week == 5)
      return;
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
   double bodyFraction = MathAbs(bar.close - bar.open) / range;
   bool researchConfirmed = true;
   if(InpResearchM30Mode == 1)
      researchConfirmed = minute < 480;
   else if(InpResearchM30Mode == 2)
      researchConfirmed = minute >= 480;
   else if(InpResearchM30Mode == 3)
      researchConfirmed = bodyFraction >= 0.45;
   else if(InpResearchM30Mode == 4)
      researchConfirmed = bodyFraction >= 0.55;
   else if(InpResearchM30Mode == 5)
      researchConfirmed = minute < 480 && bodyFraction >= 0.45;
   else if(InpResearchM30Mode == 6)
      researchConfirmed = minute >= 480 && bodyFraction >= 0.45;
   if(!researchConfirmed)
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
         && !IsPortfolioMagic(PositionGetInteger(POSITION_MAGIC))
      )
         count++;
   }
   return count;
}

int CountSleevePositions(const int sleeve)
{
   int count = 0;
   long expectedMagic = sleeve == RSI_SLEEVE_ID
      ? InpRsiMagicNumber
      : SleeveMagic(sleeve);
   for(int index = PositionsTotal() - 1; index >= 0; --index)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(
         PositionGetString(POSITION_SYMBOL) == InpTargetSymbol
         && PositionGetInteger(POSITION_MAGIC) == expectedMagic
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

int CountPortfolioPositions()
{
   int count = 0;
   for(int index = PositionsTotal() - 1; index >= 0; --index)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(
         PositionGetString(POSITION_SYMBOL) == InpTargetSymbol
         && IsPortfolioMagic(PositionGetInteger(POSITION_MAGIC))
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
      pnl += HistoryDealGetDouble(ticket, DEAL_COMMISSION);
      pnl += HistoryDealGetDouble(ticket, DEAL_FEE);
      if(
         entryType == DEAL_ENTRY_OUT
         || entryType == DEAL_ENTRY_OUT_BY
         || entryType == DEAL_ENTRY_INOUT
      )
      {
         pnl += HistoryDealGetDouble(ticket, DEAL_PROFIT);
         pnl += HistoryDealGetDouble(ticket, DEAL_SWAP);
      }
   }
   return AccountValueUsd(pnl);
}


double ClosedProtectedCorePnlSince(const datetime brokerStart)
{
   if(!HistorySelect(brokerStart, TimeCurrent()))
      return 0.0;
   double pnl = 0.0;
   int total = HistoryDealsTotal();
   for(int index = 0; index < total; ++index)
   {
      ulong ticket = HistoryDealGetTicket(index);
      if(ticket == 0)
         continue;
      if(HistoryDealGetString(ticket, DEAL_SYMBOL) != InpTargetSymbol)
         continue;
      int sleeve = MagicSleeve(HistoryDealGetInteger(ticket, DEAL_MAGIC));
      if(sleeve < 0 || !IsProtectedCoreSleeve(sleeve))
         continue;
      long entryType = HistoryDealGetInteger(ticket, DEAL_ENTRY);
      pnl += HistoryDealGetDouble(ticket, DEAL_COMMISSION);
      pnl += HistoryDealGetDouble(ticket, DEAL_FEE);
      if(
         entryType == DEAL_ENTRY_OUT
         || entryType == DEAL_ENTRY_OUT_BY
         || entryType == DEAL_ENTRY_INOUT
      )
      {
         pnl += HistoryDealGetDouble(ticket, DEAL_PROFIT);
         pnl += HistoryDealGetDouble(ticket, DEAL_SWAP);
      }
   }
   return AccountValueUsd(pnl);
}

double ClosedSleevePnlSince(
   const datetime brokerStart,
   const int targetSleeve
)
{
   if(!HistorySelect(brokerStart, TimeCurrent()))
      return 0.0;
   double pnl = 0.0;
   int total = HistoryDealsTotal();
   for(int index = 0; index < total; ++index)
   {
      ulong ticket = HistoryDealGetTicket(index);
      if(ticket == 0)
         continue;
      if(HistoryDealGetString(ticket, DEAL_SYMBOL) != InpTargetSymbol)
         continue;
      int sleeve = MagicSleeve(HistoryDealGetInteger(ticket, DEAL_MAGIC));
      if(sleeve != targetSleeve)
         continue;
      long entryType = HistoryDealGetInteger(ticket, DEAL_ENTRY);
      pnl += HistoryDealGetDouble(ticket, DEAL_COMMISSION);
      pnl += HistoryDealGetDouble(ticket, DEAL_FEE);
      if(
         entryType == DEAL_ENTRY_OUT
         || entryType == DEAL_ENTRY_OUT_BY
         || entryType == DEAL_ENTRY_INOUT
      )
      {
         pnl += HistoryDealGetDouble(ticket, DEAL_PROFIT);
         pnl += HistoryDealGetDouble(ticket, DEAL_SWAP);
      }
   }
   return AccountValueUsd(pnl);
}

double OpenOwnVolumeLots()
{
   double lots = 0.0;
   for(int index = PositionsTotal() - 1; index >= 0; --index)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(
         PositionGetString(POSITION_SYMBOL) == InpTargetSymbol
         && IsOwnMagic(PositionGetInteger(POSITION_MAGIC))
      )
         lots += PositionGetDouble(POSITION_VOLUME);
   }
   return lots;
}

double OpenPortfolioVolumeLots()
{
   double lots = 0.0;
   for(int index = PositionsTotal() - 1; index >= 0; --index)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(
         PositionGetString(POSITION_SYMBOL) == InpTargetSymbol
         && IsPortfolioMagic(PositionGetInteger(POSITION_MAGIC))
      )
         lots += PositionGetDouble(POSITION_VOLUME);
   }
   return lots;
}

double ClosedPortfolioPnlSince(const datetime brokerStart)
{
   if(!HistorySelect(brokerStart, TimeCurrent()))
      return 0.0;
   double pnl = 0.0;
   for(int index = 0; index < HistoryDealsTotal(); ++index)
   {
      ulong ticket = HistoryDealGetTicket(index);
      if(ticket == 0)
         continue;
      if(
         HistoryDealGetString(ticket, DEAL_SYMBOL) != InpTargetSymbol
         || !IsPortfolioMagic(HistoryDealGetInteger(ticket, DEAL_MAGIC))
      )
         continue;
      long entryType = HistoryDealGetInteger(ticket, DEAL_ENTRY);
      pnl += HistoryDealGetDouble(ticket, DEAL_COMMISSION);
      pnl += HistoryDealGetDouble(ticket, DEAL_FEE);
      if(
         entryType == DEAL_ENTRY_OUT
         || entryType == DEAL_ENTRY_OUT_BY
         || entryType == DEAL_ENTRY_INOUT
      )
      {
         pnl += HistoryDealGetDouble(ticket, DEAL_PROFIT);
         pnl += HistoryDealGetDouble(ticket, DEAL_SWAP);
      }
   }
   return AccountValueUsd(pnl);
}

double OpenPortfolioPnlUsd()
{
   double pnl = 0.0;
   for(int index = PositionsTotal() - 1; index >= 0; --index)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(
         PositionGetString(POSITION_SYMBOL) != InpTargetSymbol
         || !IsPortfolioMagic(PositionGetInteger(POSITION_MAGIC))
      )
         continue;
      pnl += PositionGetDouble(POSITION_PROFIT);
      pnl += PositionGetDouble(POSITION_SWAP);
   }
   return AccountValueUsd(pnl);
}

double PortfolioStrategyEquityUsd()
{
   datetime prospectiveStart = StringToTime(InpProspectiveStartUtc);
   if(prospectiveStart <= 0)
      return DBL_MAX;
   return ClosedPortfolioPnlSince(prospectiveStart) + OpenPortfolioPnlUsd();
}

bool MonthlyGivebackAllows(string &reason)
{
   datetime monthStart = UtcMonthStart(TimeCurrent());
   if(!HistorySelect(monthStart, TimeCurrent()))
   {
      reason = "monthly_giveback_history_unavailable";
      return false;
   }
   double cumulative = 0.0;
   double peak = 0.0;
   for(int index = 0; index < HistoryDealsTotal(); ++index)
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
      cumulative += HistoryDealGetDouble(ticket, DEAL_COMMISSION);
      cumulative += HistoryDealGetDouble(ticket, DEAL_FEE);
      if(
         entryType == DEAL_ENTRY_OUT
         || entryType == DEAL_ENTRY_OUT_BY
         || entryType == DEAL_ENTRY_INOUT
      )
      {
         cumulative += HistoryDealGetDouble(ticket, DEAL_PROFIT);
         cumulative += HistoryDealGetDouble(ticket, DEAL_SWAP);
      }
      peak = MathMax(peak, cumulative);
   }
   double peakUsd = AccountValueUsd(peak);
   double cumulativeUsd = AccountValueUsd(cumulative);
   if(
      peakUsd >= InpResearchMonthlyPeakActivationUsd
      && peakUsd - cumulativeUsd >= InpResearchMonthlyGivebackUsd
   )
   {
      reason = StringFormat(
         "portfolio_monthly_giveback_peak_%.2f_current_%.2f",
          peakUsd,
          cumulativeUsd
      );
      return false;
   }
   reason = "portfolio_monthly_giveback_allows";
   return true;
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
   if(!(bool)MQLInfoInteger(MQL_TESTER))
   {
      bool globalOkay = PersistGlobalVerified(
         breakerLatchName,
         1.0,
         detail + "_breaker_global"
      );
      bool fileOkay = PersistBreakerFile(detail);
      if(!globalOkay || !fileOkay)
         criticalPersistenceHealthy = false;
   }
   Audit("RISK_BREAKER_LATCHED", detail);
}

void RefreshPersistentEquityState()
{
   double equity = PortfolioStrategyEquityUsd();
   if(equity == DBL_MAX)
      return;
   if(equity > sessionPeakEquity)
   {
      sessionPeakEquity = equity;
      if(!(bool)MQLInfoInteger(MQL_TESTER) && peakEquityName != "")
      {
         if(!PersistGlobalVerified(
            peakEquityName,
            sessionPeakEquity,
            "peak_equity_update"
         ))
            LatchPersistentBreaker("peak_equity_persistence_failed");
      }
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
         || !IsPortfolioMagic(PositionGetInteger(POSITION_MAGIC))
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
   return AccountValueUsd(risk);
}

bool FundingAndCashRiskAllow(
   const ENUM_ORDER_TYPE orderType,
   const MqlTick &tick,
   const double proposedStop,
   const double requestedLots,
   string &reason
)
{
   double equity = AccountValueUsd(AccountInfoDouble(ACCOUNT_EQUITY));
   if(
      InpMinimumAccountEquityUsd > 0.0
      && equity < InpMinimumAccountEquityUsd
   )
   {
      reason = "minimum_account_equity";
      return false;
   }
   double margin = 0.0;
   if(
      !OrderCalcMargin(
          orderType,
         InpTargetSymbol,
         requestedLots,
          orderType == ORDER_TYPE_BUY ? tick.ask : tick.bid,
         margin
      )
      || margin < 0.0
   )
   {
      reason = "margin_calculation_failed";
      return false;
   }
   if(
      AccountValueUsd(AccountInfoDouble(ACCOUNT_MARGIN_FREE) - margin)
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
          orderType,
         InpTargetSymbol,
         requestedLots,
          orderType == ORDER_TYPE_BUY ? tick.ask : tick.bid,
         proposedStop,
         proposedAtStop
      )
   )
   {
      reason = "cash_risk_calculation_failed";
      return false;
   }
   double proposedAtStopUsd = AccountValueUsd(proposedAtStop);
   double totalRisk = openRisk + MathMax(0.0, -proposedAtStopUsd);
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

bool AcquirePortfolioOrderLock()
{
   if(portfolioOrderLockName == "")
      return false;
   if(
      !GlobalVariableCheck(portfolioOrderLockName)
      && GlobalVariableSet(portfolioOrderLockName, 0.0) == 0
   )
      return false;
   double observed = GlobalVariableGet(portfolioOrderLockName);
   double now = (double)TimeLocal();
   double observedTime = MathFloor(observed / 1000.0);
   if(observed > 0.0 && now - observedTime < 10.0)
      return false;
   portfolioOrderLockToken =
      now * 1000.0 + (double)(GetTickCount() % 997 + 1);
   return GlobalVariableSetOnCondition(
      portfolioOrderLockName,
      portfolioOrderLockToken,
      observed
   );
}

void ReleasePortfolioOrderLock()
{
   if(portfolioOrderLockToken <= 0.0 || portfolioOrderLockName == "")
      return;
   GlobalVariableSetOnCondition(
      portfolioOrderLockName,
      0.0,
      portfolioOrderLockToken
   );
   portfolioOrderLockToken = 0.0;
}

bool NewOrderAllowed(
   const int sleeve,
   const double proposedStop,
   const double requestedLots,
   string &reason
)
{
   if(managerOnlyMode)
   {
      reason = "manager_only_mode";
      return false;
   }
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
   if(
      sleeve != RSI_SLEEVE_ID
      && CountOwnPositions() >= InpMaximumOwnPositions
   )
   {
      reason = "maximum_own_positions";
      return false;
   }
   int effectivePortfolioPositionCap = InpMaximumPortfolioPositions;
   if(
      (bool)MQLInfoInteger(MQL_TESTER)
      && InpTesterGuardFaultMode == 1
   )
      effectivePortfolioPositionCap = 1;
   if(CountPortfolioPositions() >= effectivePortfolioPositionCap)
   {
      reason = "maximum_portfolio_positions";
      return false;
   }
   if(!VolumeGridAllows(requestedLots, reason))
      return false;
   if(
      sleeve != RSI_SLEEVE_ID
      && OpenOwnVolumeLots() + requestedLots
         > InpMaximumOwnVolumeLots + 1e-9
   )
   {
      reason = "maximum_own_volume";
      return false;
   }
   double effectivePortfolioVolumeCap = InpMaximumPortfolioVolumeLots;
   if(
      (bool)MQLInfoInteger(MQL_TESTER)
      && InpTesterGuardFaultMode == 2
   )
      effectivePortfolioVolumeCap = 0.01;
   if(
      OpenPortfolioVolumeLots() + requestedLots
      > effectivePortfolioVolumeCap + 1e-9
   )
   {
      reason = "maximum_portfolio_volume";
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
   if(!TickIsFresh(tick, reason))
      return false;
   if((tick.ask - tick.bid) / PipSize() > InpMaximumSpreadPips)
   {
      reason = "spread_limit";
      return false;
   }
   int dailyEntries = 0;
   ClosedPnlSince(UtcDayStart(TimeCurrent()), dailyEntries);
   double dailyPnl = ClosedPortfolioPnlSince(UtcDayStart(TimeCurrent()));
   if(
      sleeve != RSI_SLEEVE_ID
      && InpMaximumTradesPerUtcDay > 0
      && dailyEntries >= MathMin(
         InpMaximumTradesPerUtcDay,
         InpResearchEventTradeCap
      )
   )
   {
      reason = "chop_event_risk_budget";
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
   ClosedPnlSince(TimeCurrent() - 5 * 24 * 60 * 60, rollingEntries);
   double rollingPnl = ClosedPortfolioPnlSince(
      TimeCurrent() - 5 * 24 * 60 * 60
   );
   if(
      InpMaximumRolling5DayClosedLossUsd > 0.0
      && rollingPnl <= -InpMaximumRolling5DayClosedLossUsd
   )
   {
      reason = "rolling_5day_loss_breaker";
      return false;
   }
   if(sleeve != RSI_SLEEVE_ID && !MonthlyGivebackAllows(reason))
      return false;
   if(
      IsGuardedFrequencySleeve(sleeve)
      && InpMaximumFrequencySleeveCalendarMonthClosedLossUsd > 0.0
      && ClosedSleevePnlSince(UtcMonthStart(TimeCurrent()), sleeve)
         <= -InpMaximumFrequencySleeveCalendarMonthClosedLossUsd
   )
   {
      reason = "frequency_sleeve_calendar_month_loss_breaker";
      return false;
   }
   if(
      IsProtectedCoreSleeve(sleeve)
      && InpMaximumCoreCalendarMonthClosedLossUsd > 0.0
      && ClosedProtectedCorePnlSince(UtcMonthStart(TimeCurrent()))
         <= -InpMaximumCoreCalendarMonthClosedLossUsd
   )
   {
      reason = "protected_core_calendar_month_loss_breaker";
      return false;
   }
   ENUM_ORDER_TYPE orderType = IsLongSleeve(sleeve)
      ? ORDER_TYPE_BUY
      : ORDER_TYPE_SELL;
   if(!FundingAndCashRiskAllow(
      orderType, tick, proposedStop, requestedLots, reason
   ))
      return false;
   reason = "all_order_guards_pass";
   return true;
}

void PersistSignalDate(const int sleeve, const int dateKey)
{
   lastSignalDate[sleeve] = dateKey;
   if(!(bool)MQLInfoInteger(MQL_TESTER))
   {
      if(!PersistGlobalVerified(
         signalDateNames[sleeve],
         (double)dateKey,
         "signal_date_" + IntegerToString(sleeve)
      ))
         LatchPersistentBreaker("signal_date_persistence_failed");
   }
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
   const double expectedLots,
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
      || MathAbs(trade.ResultVolume() - expectedLots) > 1e-9
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
      if(MathAbs(volume - expectedLots) > 1e-9)
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
      bool unseenCandidate =
         candidate[sleeve] && lastSignalDate[sleeve] != stateDateKey;
      if(unseenCandidate && !IsOrderEnabledSleeve(sleeve))
      {
         PersistSignalDate(sleeve, stateDateKey);
         Audit(
            "SLEEVE_OBSERVED_DISABLED",
            "failed_individual_admission_or_duplicate_event_edge",
            sleeve
         );
      }
      eligible[sleeve] =
         unseenCandidate && IsOrderEnabledSleeve(sleeve);
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
      double requestedLots = ResearchLots(sleeve);
      OwnedRegime regime = SleeveRegime(sleeve);
      double atr[];
      if(!CopyIndicator(h1Atr, 0, 1, 1, atr) || atr[0] <= 0.0)
      {
         Audit("ENTRY_FILTER_REJECTED", "h1_atr_unavailable", sleeve);
         continue;
      }
      bool isLong = IsLongSleeve(sleeve);
      string side = isLong ? "LONG" : "SHORT";
      double entry = isLong ? tick.ask : tick.bid;
      double stopMultiple = sleeve == BASELINE_CHOP
         ? InpResearchFridayReversalStopAtrMultiple
         : InpResearchStopAtrMultiple;
      double stopDistance = stopMultiple * atr[0];
      double stop = NormalizeDouble(
         isLong ? entry - stopDistance : entry + stopDistance,
         _Digits
      );
      double target = NormalizeDouble(
         isLong
            ? entry + TargetR(regime, sleeve) * stopDistance
            : entry - TargetR(regime, sleeve) * stopDistance,
         _Digits
      );
      if(!Audit(
         "SIGNAL",
         sleeve == BASELINE_CHOP
            ? "friday_false_break_reversal_confirmed"
            : "two_stage_causal_caps_passed",
         sleeve,
         side,
         requestedLots,
         entry,
         stop,
         target
      ))
         continue;
      string guardReason = "";
      if(!NewOrderAllowed(sleeve, stop, requestedLots, guardReason))
      {
         Audit(
            "ORDER_BLOCKED",
            guardReason,
            sleeve,
            side,
            requestedLots,
            entry,
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
            side,
            requestedLots,
            entry,
            stop,
            target
         )
      )
         continue;
      if(!AcquirePortfolioOrderLock())
      {
         Audit(
            "ORDER_BLOCKED",
            "portfolio_order_lock_busy",
            sleeve,
            side,
            requestedLots,
            entry,
            stop,
            target
         );
         continue;
      }
      if(!NewOrderAllowed(sleeve, stop, requestedLots, guardReason))
      {
         Audit(
            "ORDER_BLOCKED",
            "locked_recheck_" + guardReason,
            sleeve,
            side,
            requestedLots,
            entry,
            stop,
            target
         );
         ReleasePortfolioOrderLock();
         continue;
      }
      trade.SetExpertMagicNumber(SleeveMagic(sleeve));
      trade.SetDeviationInPoints(InpDeviationPoints);
      trade.SetTypeFillingBySymbol(_Symbol);
      string comment = InpOrderComment + "_" + SleeveCode(sleeve);
      bool sent = isLong
         ? trade.Buy(
            requestedLots,
            _Symbol,
            0.0,
            stop,
            target,
            comment
         )
         : trade.Sell(
            requestedLots,
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
            requestedLots,
            executionReason
         );
      Audit(
         confirmed ? "ORDER_CONFIRMED" : "ORDER_EXECUTION_UNCERTAIN",
         executionReason == ""
            ? trade.ResultRetcodeDescription()
            : executionReason,
         sleeve,
         side,
         requestedLots,
         entry,
         stop,
         target
      );
      ReleasePortfolioOrderLock();
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

string RsiStateName(const string suffix)
{
   return rsiStatePrefix + suffix;
}

bool RsiReadRequiredState(const string suffix, double &value)
{
   string name = RsiStateName(suffix);
   if(!GlobalVariableCheck(name))
      return false;
   value = GlobalVariableGet(name);
   return true;
}

void RsiSaveState()
{
   if(
      ((bool)MQLInfoInteger(MQL_TESTER) && !rsiTesterStateSaveExercise)
      || !rsiStateReady
   )
      return;
   GlobalVariableDel(RsiStateName("SCHEMA"));
   GlobalVariablesFlush();
   bool okay = PersistGlobalVerified(
      RsiStateName("CONTRACT"),
      (double)RSI_CONTRACT_FINGERPRINT,
      "rsi_contract"
   );
   okay = PersistGlobalVerified(
      RsiStateName("START"),
      (double)rsiProspectiveStart,
      "rsi_start"
   ) && okay;
   okay = PersistGlobalVerified(
      RsiStateName("LASTEXIT"),
      (double)rsiLastVirtualExitTime,
      "rsi_last_exit"
   ) && okay;
   okay = PersistGlobalVerified(
      RsiStateName("DAY"),
      (double)rsiDailyDateKey,
      "rsi_day"
   ) && okay;
   okay = PersistGlobalVerified(
      RsiStateName("DAYCOUNT"),
      (double)rsiDailyEntryCount,
      "rsi_day_count"
   ) && okay;
   okay = PersistGlobalVerified(
      RsiStateName("ACTIVE"),
      rsiVirtualActive ? 1.0 : 0.0,
      "rsi_active"
   ) && okay;
   okay = PersistGlobalVerified(
      RsiStateName("ENTRYTIME"),
      (double)rsiVirtualEntryTime,
      "rsi_entry_time"
   ) && okay;
   okay = PersistGlobalVerified(
      RsiStateName("ENTRY"), rsiVirtualEntry, "rsi_entry"
   ) && okay;
   okay = PersistGlobalVerified(
      RsiStateName("STOP"), rsiVirtualStop, "rsi_stop"
   ) && okay;
   okay = PersistGlobalVerified(
      RsiStateName("TARGET"), rsiVirtualTarget, "rsi_target"
   ) && okay;
   if(okay)
      okay = PersistGlobalVerified(
         RsiStateName("SCHEMA"),
         (double)RSI_STATE_SCHEMA,
         "rsi_schema_commit"
      );
   if(!okay)
      LatchPersistentBreaker("rsi_state_persistence_failed");
}

bool RsiDeletePersistentState()
{
   string suffixes[] = {
      "SCHEMA", "CONTRACT", "START", "LASTEXIT", "DAY", "DAYCOUNT",
      "ACTIVE", "ENTRYTIME", "ENTRY", "STOP", "TARGET"
   };
   bool okay = true;
   for(int index = 0; index < ArraySize(suffixes); ++index)
   {
      string name = RsiStateName(suffixes[index]);
      if(
         GlobalVariableCheck(name)
         && (!GlobalVariableDel(name) || GlobalVariableCheck(name))
      )
         okay = false;
   }
   GlobalVariablesFlush();
   return okay;
}

bool DeletePersistentGlobalVerified(const string name)
{
   if(name == "" || !GlobalVariableCheck(name))
      return true;
   ResetLastError();
   if(!GlobalVariableDel(name))
   {
      Audit(
         "PERSISTENT_RESET_FAILED",
         name + StringFormat("_delete_error_%d", GetLastError())
      );
      return false;
   }
   return !GlobalVariableCheck(name);
}

bool ResetAllPersistentState()
{
   bool okay = true;
   okay = DeletePersistentGlobalVerified(schemaName) && okay;
   okay = DeletePersistentGlobalVerified(peakEquityName) && okay;
   okay = DeletePersistentGlobalVerified(breakerLatchName) && okay;
   for(int sleeve = 0; sleeve < SLEEVE_COUNT; ++sleeve)
      okay = DeletePersistentGlobalVerified(signalDateNames[sleeve]) && okay;
   okay = RsiDeletePersistentState() && okay;
   if(FileIsExist(breakerLatchFileName, FILE_COMMON))
   {
      ResetLastError();
      if(!FileDelete(breakerLatchFileName, FILE_COMMON))
      {
         Audit(
            "PERSISTENT_RESET_FAILED",
            StringFormat("breaker_file_delete_error_%d", GetLastError())
         );
         okay = false;
      }
   }
   GlobalVariablesFlush();
   if(okay)
      Audit("PERSISTENT_STATE_RESET", "all_scoped_state_removed");
   return okay;
}

void RsiInitializeEmptyState()
{
   rsiLastVirtualExitTime = 0;
   rsiDailyDateKey = UtcDateKey(TimeCurrent());
   rsiDailyEntryCount = 0;
   rsiVirtualActive = false;
   rsiVirtualEntryTime = 0;
   rsiVirtualEntry = 0.0;
   rsiVirtualStop = 0.0;
   rsiVirtualTarget = 0.0;
}

bool RsiRestoreState(string &reason)
{
   if((bool)MQLInfoInteger(MQL_TESTER) && !rsiTesterStateRoundTrip)
   {
      RsiInitializeEmptyState();
      rsiStateReady = true;
      reason = "tester_empty_state";
      return true;
   }
   if(!GlobalVariableCheck(RsiStateName("SCHEMA")))
   {
      if(CountSleevePositions(RSI_SLEEVE_ID) > 0)
      {
         reason = "rsi_state_missing_with_open_position";
         return false;
      }
      RsiInitializeEmptyState();
      rsiStateReady = true;
      RsiSaveState();
      reason = "new_empty_state";
      return true;
   }
   double value = 0.0;
   double schema = 0.0;
   double contract = 0.0;
   double start = 0.0;
   if(
      !RsiReadRequiredState("SCHEMA", schema)
      || !RsiReadRequiredState("CONTRACT", contract)
      || !RsiReadRequiredState("START", start)
   )
   {
      reason = "rsi_state_header_incomplete";
      return false;
   }
   if((int)schema != RSI_STATE_SCHEMA)
   {
      reason = "rsi_state_schema_mismatch";
      return false;
   }
   if((long)contract != RSI_CONTRACT_FINGERPRINT)
   {
      reason = "rsi_state_contract_mismatch";
      return false;
   }
   if((datetime)start != rsiProspectiveStart)
   {
      reason = "rsi_state_prospective_floor_mismatch";
      return false;
   }
   if(!RsiReadRequiredState("LASTEXIT", value))
   {
      reason = "rsi_state_last_exit_missing";
      return false;
   }
   rsiLastVirtualExitTime = (datetime)value;
   if(!RsiReadRequiredState("DAY", value))
   {
      reason = "rsi_state_day_missing";
      return false;
   }
   rsiDailyDateKey = (int)value;
   if(!RsiReadRequiredState("DAYCOUNT", value))
   {
      reason = "rsi_state_day_count_missing";
      return false;
   }
   rsiDailyEntryCount = (int)value;
   if(!RsiReadRequiredState("ACTIVE", value))
   {
      reason = "rsi_state_active_missing";
      return false;
   }
   rsiVirtualActive = value >= 0.5;
   if(!RsiReadRequiredState("ENTRYTIME", value))
   {
      reason = "rsi_state_entry_time_missing";
      return false;
   }
   rsiVirtualEntryTime = (datetime)value;
   if(!RsiReadRequiredState("ENTRY", rsiVirtualEntry))
   {
      reason = "rsi_state_entry_missing";
      return false;
   }
   if(!RsiReadRequiredState("STOP", rsiVirtualStop))
   {
      reason = "rsi_state_stop_missing";
      return false;
   }
   if(!RsiReadRequiredState("TARGET", rsiVirtualTarget))
   {
      reason = "rsi_state_target_missing";
      return false;
   }
   if(
      rsiDailyEntryCount < 0
      || rsiDailyEntryCount > RSI_MAXIMUM_TRADES_PER_UTC_DAY
      || (
         rsiVirtualActive
         && (
            rsiVirtualEntryTime <= 0
            || rsiVirtualEntry <= 0.0
            || rsiVirtualStop <= 0.0
            || rsiVirtualTarget <= rsiVirtualEntry
            || rsiVirtualStop >= rsiVirtualEntry
         )
      )
   )
   {
      reason = "rsi_state_value_invalid";
      return false;
   }
   rsiStateReady = true;
   reason = "rsi_persistent_state_restored";
   return true;
}

bool RsiExerciseStateRoundTrip(string &reason)
{
   datetime snapshotExit = rsiLastVirtualExitTime;
   int snapshotDay = rsiDailyDateKey;
   int snapshotCount = rsiDailyEntryCount;
   bool snapshotActive = rsiVirtualActive;
   datetime snapshotEntryTime = rsiVirtualEntryTime;
   double snapshotEntry = rsiVirtualEntry;
   double snapshotStop = rsiVirtualStop;
   double snapshotTarget = rsiVirtualTarget;
   rsiTesterStateSaveExercise = true;
   RsiSaveState();
   rsiTesterStateSaveExercise = false;
   RsiInitializeEmptyState();
   rsiStateReady = false;
   rsiTesterStateRoundTrip = true;
   bool restored = RsiRestoreState(reason);
   rsiTesterStateRoundTrip = false;
   if(!restored)
      return false;
   bool exact = (
      rsiLastVirtualExitTime == snapshotExit
      && rsiDailyDateKey == snapshotDay
      && rsiDailyEntryCount == snapshotCount
      && rsiVirtualActive == snapshotActive
      && rsiVirtualEntryTime == snapshotEntryTime
      && MathAbs(rsiVirtualEntry - snapshotEntry) <= 1e-12
      && MathAbs(rsiVirtualStop - snapshotStop) <= 1e-12
      && MathAbs(rsiVirtualTarget - snapshotTarget) <= 1e-12
   );
   reason = exact ? "rsi_state_round_trip_exact" : "rsi_state_round_trip_mismatch";
   return exact;
}

void EnterManagerOnlyMode(const string reason)
{
   if(managerOnlyMode)
      return;
   managerOnlyMode = true;
   managerOnlyReason = reason;
   LatchPersistentBreaker("manager_only_" + reason);
   Audit("MANAGER_ONLY_ENTERED", reason);
}

void MaybeExerciseCorruptStateWithOpenPosition()
{
   static bool exercised = false;
   if(
      exercised
      || !(bool)MQLInfoInteger(MQL_TESTER)
      || InpTesterStateFaultMode != 1
      || CountPortfolioPositions() <= 0
   )
      return;
   exercised = true;
   rsiTesterStateSaveExercise = true;
   RsiSaveState();
   rsiTesterStateSaveExercise = false;
   GlobalVariableDel(RsiStateName("TARGET"));
   rsiStateReady = false;
   rsiTesterStateRoundTrip = true;
   string reason = "";
   bool restored = RsiRestoreState(reason);
   rsiTesterStateRoundTrip = false;
   if(restored)
   {
      Audit("STATE_FAULT_EXERCISE_FAILED", "corrupt_state_was_accepted");
      return;
   }
   Audit("STATE_FAULT_REJECTED", reason);
   EnterManagerOnlyMode(reason);
}

void RsiClearVirtualTrade()
{
   rsiVirtualActive = false;
   rsiVirtualEntryTime = 0;
   rsiVirtualEntry = 0.0;
   rsiVirtualStop = 0.0;
   rsiVirtualTarget = 0.0;
}

bool RsiResolveVirtualTrade(const MqlTick &tick)
{
   if(!rsiVirtualActive)
      return false;
   string exitReason = "";
   if(tick.bid <= rsiVirtualStop)
      exitReason = "STOP_FIRST";
   else if(tick.bid >= rsiVirtualTarget)
      exitReason = "TARGET";
   else
      return false;
   Audit(
      "RSI_VIRTUAL_CLOSE",
      exitReason,
      RSI_SLEEVE_ID,
      "LONG",
      0.01,
      rsiVirtualEntry,
      rsiVirtualStop,
      rsiVirtualTarget
   );
   rsiLastVirtualExitTime = TimeCurrent();
   RsiClearVirtualTrade();
   RsiSaveState();
   return true;
}

bool RsiReadSignalInputs(
   MqlRates &signalBar,
   double &atr,
   double &bandMid,
   double &rsi,
   double &recentLow
)
{
   MqlRates bars[];
   ArraySetAsSeries(bars, true);
   if(
      CopyRates(
         _Symbol,
         PERIOD_M15,
         1,
         RSI_RECENT_STOP_LOOKBACK_M15_BARS,
         bars
      ) != RSI_RECENT_STOP_LOOKBACK_M15_BARS
   )
      return false;
   signalBar = bars[0];
   recentLow = bars[0].low;
   for(int index = 1; index < ArraySize(bars); ++index)
      recentLow = MathMin(recentLow, bars[index].low);
   double values[];
   ArraySetAsSeries(values, true);
   if(CopyBuffer(rsiAtr, 0, 1, 1, values) != 1)
      return false;
   atr = values[0];
   if(CopyBuffer(rsiBands, 0, 1, 1, values) != 1)
      return false;
   bandMid = values[0];
   if(CopyBuffer(rsiIndicator, 0, 1, 1, values) != 1)
      return false;
   rsi = values[0];
   return atr > 0.0 && bandMid > 0.0 && rsi >= 0.0 && rsi <= 100.0;
}

bool RsiH4LongStrengthAllows()
{
   double values[];
   ArraySetAsSeries(values, true);
   if(CopyBuffer(h4Atr, 0, 1, 1, values) != 1 || values[0] <= 0.0)
      return false;
   double atrClosed = values[0];
   if(CopyBuffer(h4Ema, 0, 1, 1, values) != 1)
      return false;
   double emaClosed = values[0];
   if(CopyBuffer(h4Ema, 0, 2, 1, values) != 1)
      return false;
   double emaPrior = values[0];
   double closeClosed = iClose(InpTargetSymbol, PERIOD_H4, 1);
   return (
      closeClosed > 0.0
      && closeClosed > emaClosed + 0.05 * atrClosed
      && emaClosed > emaPrior + 0.01 * atrClosed
   );
}

bool ConfirmRsiPosition(
   const double expectedStop,
   const double expectedTarget,
   string &reason
)
{
   if(trade.ResultRetcode() != TRADE_RETCODE_DONE || trade.ResultDeal() == 0)
   {
      reason = "rsi_fill_not_confirmed";
      return false;
   }
   if(CountSleevePositions(RSI_SLEEVE_ID) != 1)
   {
      reason = "rsi_position_count_not_one";
      return false;
   }
   for(int index = PositionsTotal() - 1; index >= 0; --index)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(
         PositionGetString(POSITION_SYMBOL) != InpTargetSymbol
         || PositionGetInteger(POSITION_MAGIC) != InpRsiMagicNumber
      )
         continue;
      if(
         PositionGetInteger(POSITION_TYPE) != POSITION_TYPE_BUY
         || MathAbs(PositionGetDouble(POSITION_VOLUME) - 0.01) > 1e-9
         || MathAbs(PositionGetDouble(POSITION_SL) - expectedStop) > 2.0 * _Point
         || MathAbs(PositionGetDouble(POSITION_TP) - expectedTarget) > 2.0 * _Point
      )
      {
         reason = "rsi_position_contract_mismatch";
         return false;
      }
      reason = "rsi_position_confirmed";
      return true;
   }
   reason = "rsi_position_not_found";
   return false;
}

bool RsiEnsureBrokerStopDistances(
   const MqlTick &tick,
   double &stop,
   double &target,
   bool &adjusted,
   string &reason
)
{
   adjusted = false;
   int stopsLevelPoints = (int)SymbolInfoInteger(
      InpTargetSymbol,
      SYMBOL_TRADE_STOPS_LEVEL
   );
   double point = SymbolInfoDouble(InpTargetSymbol, SYMBOL_POINT);
   int digits = (int)SymbolInfoInteger(InpTargetSymbol, SYMBOL_DIGITS);
   if(point <= 0.0 || digits < 0)
   {
      reason = "rsi_symbol_geometry_unavailable";
      return false;
   }
   // Buy stops are validated from bid while the entry is ask.  Preserve a
   // two-point buffer so normalization and a one-tick quote change cannot
   // turn a locally valid stop into a broker-side INVALID_STOPS rejection.
   double minimumDistance = (stopsLevelPoints + 2) * point;
   double maximumStop = tick.bid - minimumDistance;
   if(stop > maximumStop)
   {
      stop = NormalizeDouble(maximumStop, digits);
      adjusted = true;
   }
   double riskDistance = tick.ask - stop;
   if(stop <= 0.0 || riskDistance <= 0.0)
   {
      reason = "rsi_broker_stop_geometry_invalid";
      return false;
   }
   double minimumTarget = tick.ask + minimumDistance;
   double riskMatchedTarget = tick.ask + RSI_TARGET_R * riskDistance;
   double requiredTarget = MathMax(minimumTarget, riskMatchedTarget);
   if(target < requiredTarget)
   {
      target = NormalizeDouble(requiredTarget, digits);
      adjusted = true;
   }
   if(target <= tick.ask)
   {
      reason = "rsi_broker_target_geometry_invalid";
      return false;
   }
   reason = StringFormat(
      "broker_min_%d_points_stop_%.5f_target_%.5f",
      stopsLevelPoints,
      stop,
      target
   );
   return true;
}

void RsiTryPlaceOrder(double stop, double target)
{
   if(!InpEnableRsiOrders)
   {
      Audit(
         "RSI_ORDER_OBSERVED_ONLY",
         "rsi_orders_disabled_by_frozen_candidate",
         RSI_SLEEVE_ID,
         "LONG",
         0.01,
         0.0,
         stop,
         target
      );
      return;
   }
   MqlTick orderTick;
   if(!SymbolInfoTick(InpTargetSymbol, orderTick))
   {
      Audit("ORDER_BLOCKED", "rsi_order_tick_unavailable", RSI_SLEEVE_ID);
      return;
   }
   bool stopsAdjusted = false;
   string stopReason = "";
   if(!RsiEnsureBrokerStopDistances(
      orderTick,
      stop,
      target,
      stopsAdjusted,
      stopReason
   ))
   {
      Audit("ORDER_BLOCKED", stopReason, RSI_SLEEVE_ID, "LONG", 0.01, orderTick.ask, stop, target);
      return;
   }
   if(stopsAdjusted)
   {
      rsiVirtualStop = stop;
      rsiVirtualTarget = target;
      RsiSaveState();
      Audit("RSI_STOPS_ADJUSTED", "pre_send_" + stopReason, RSI_SLEEVE_ID, "LONG", 0.01, orderTick.ask, stop, target);
   }
   string reason = "";
   if(!NewOrderAllowed(RSI_SLEEVE_ID, stop, 0.01, reason))
   {
      Audit("ORDER_BLOCKED", reason, RSI_SLEEVE_ID, "LONG", 0.01, 0.0, stop, target);
      return;
   }
   if(!Audit("ORDER_INTENT", "all_pretrade_guards_passed", RSI_SLEEVE_ID, "LONG", 0.01, 0.0, stop, target))
      return;
   if(!AcquirePortfolioOrderLock())
   {
      Audit("ORDER_BLOCKED", "portfolio_order_lock_busy", RSI_SLEEVE_ID, "LONG", 0.01, 0.0, stop, target);
      return;
   }
   if(!NewOrderAllowed(RSI_SLEEVE_ID, stop, 0.01, reason))
   {
      Audit("ORDER_BLOCKED", "locked_recheck_" + reason, RSI_SLEEVE_ID, "LONG", 0.01, 0.0, stop, target);
      ReleasePortfolioOrderLock();
      return;
   }
   trade.SetExpertMagicNumber(InpRsiMagicNumber);
   trade.SetDeviationInPoints(InpDeviationPoints);
   trade.SetTypeFillingBySymbol(InpTargetSymbol);
   bool sent = trade.Buy(
      0.01,
      InpTargetSymbol,
      0.0,
      stop,
      target,
      "EUV20_RSI"
   );
   string confirmation = "";
   bool confirmed = sent && ConfirmRsiPosition(stop, target, confirmation);
   bool definiteInvalidStopsRejection =
      !sent
      && trade.ResultRetcode() == TRADE_RETCODE_INVALID_STOPS
      && trade.ResultDeal() == 0
      && CountSleevePositions(RSI_SLEEVE_ID) == 0;
   Audit(
      confirmed
         ? "ORDER_CONFIRMED"
         : (definiteInvalidStopsRejection
            ? "ORDER_REJECTED"
            : "ORDER_EXECUTION_UNCERTAIN"),
      confirmation == "" ? trade.ResultRetcodeDescription() : confirmation,
      RSI_SLEEVE_ID,
      "LONG",
      0.01,
      trade.ResultPrice(),
      stop,
      target
   );
   ReleasePortfolioOrderLock();
   if(!confirmed && !definiteInvalidStopsRejection)
      LatchPersistentBreaker("rsi_order_execution_not_confirmed");
}

void RsiEvaluateCompletedBar(
   const datetime newBarOpen,
   const bool resolvedOnThisTick
)
{
   if(UtcFromBroker(newBarOpen) < rsiProspectiveStart || rsiVirtualActive)
      return;
   if(resolvedOnThisTick || rsiLastVirtualExitTime >= newBarOpen)
      return;
   int dateKey = UtcDateKey(newBarOpen);
   if(dateKey != rsiDailyDateKey)
   {
      rsiDailyDateKey = dateKey;
      rsiDailyEntryCount = 0;
   }
   if(rsiDailyEntryCount >= RSI_MAXIMUM_TRADES_PER_UTC_DAY)
      return;
   MqlDateTime parts;
   UtcParts(newBarOpen, parts);
   if(parts.hour == 1 || parts.hour == 7 || parts.hour == 21)
      return;
   MqlRates signalBar;
   double atr = 0.0;
   double bandMid = 0.0;
   double rsi = 0.0;
   double recentLow = 0.0;
   if(!RsiReadSignalInputs(signalBar, atr, bandMid, rsi, recentLow))
      return;
   double range = signalBar.high - signalBar.low;
   double bodyFraction = range > 0.0
      ? MathAbs(signalBar.close - signalBar.open) / range
      : 0.0;
   if(
      rsi > RSI_OVERSOLD_INCLUSIVE
      || signalBar.close >= bandMid
      || bodyFraction < RSI_MINIMUM_BODY_FRACTION
      || !RsiH4LongStrengthAllows()
   )
      return;
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick))
      return;
   if((tick.ask - tick.bid) / PipSize() > RSI_RAW_SIGNAL_SPREAD_PIPS)
      return;
   double entry = tick.ask;
   double minimumStopDistance = MathMax(
      RSI_STOP_ATR_MULTIPLE * atr,
      RSI_STOP_FLOOR_PIPS * PipSize()
   );
   double stop = NormalizeDouble(
      MathMin(recentLow, entry - minimumStopDistance),
      _Digits
   );
   double stopPips = (entry - stop) / PipSize();
   if(stopPips > RSI_STOP_CEILING_PIPS)
      return;
   double target = NormalizeDouble(
      entry + RSI_TARGET_R * (entry - stop),
      _Digits
   );
   bool stopsAdjusted = false;
   string stopReason = "";
   if(!RsiEnsureBrokerStopDistances(
      tick,
      stop,
      target,
      stopsAdjusted,
      stopReason
   ))
   {
      Audit("ENTRY_FILTER_REJECTED", stopReason, RSI_SLEEVE_ID, "LONG", 0.01, entry, stop, target);
      return;
   }
   if(stopsAdjusted)
      Audit("RSI_STOPS_ADJUSTED", "signal_" + stopReason, RSI_SLEEVE_ID, "LONG", 0.01, entry, stop, target);
   Audit(
      "SIGNAL",
      "rsi_v13_h4_strength",
      RSI_SLEEVE_ID,
      "LONG",
      0.01,
      entry,
      stop,
      target
   );
   rsiVirtualActive = true;
   rsiVirtualEntryTime = newBarOpen;
   rsiVirtualEntry = entry;
   rsiVirtualStop = stop;
   rsiVirtualTarget = target;
   rsiDailyEntryCount++;
   RsiSaveState();
   RsiTryPlaceOrder(stop, target);
}

bool RsiInitialize(string &reason)
{
   rsiProspectiveStart = StringToTime(InpProspectiveStartUtc);
   if(rsiProspectiveStart <= 0)
   {
      reason = "rsi_prospective_start_invalid";
      return false;
   }
   rsiAtr = iATR(_Symbol, PERIOD_M15, ATR_PERIOD);
   rsiBands = iBands(
      _Symbol,
      PERIOD_M15,
      RSI_BANDS_PERIOD,
      0,
      2.0,
      PRICE_CLOSE
   );
   rsiIndicator = iRSI(_Symbol, PERIOD_M15, RSI_PERIOD, PRICE_CLOSE);
   if(
      rsiAtr == INVALID_HANDLE
      || rsiBands == INVALID_HANDLE
      || rsiIndicator == INVALID_HANDLE
   )
   {
      reason = "rsi_indicator_handle_invalid";
      return false;
   }
   return RsiRestoreState(reason);
}

void RsiReleaseIndicators()
{
   RsiSaveState();
   if(rsiAtr != INVALID_HANDLE)
      IndicatorRelease(rsiAtr);
   if(rsiBands != INVALID_HANDLE)
      IndicatorRelease(rsiBands);
   if(rsiIndicator != INVALID_HANDLE)
      IndicatorRelease(rsiIndicator);
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
      int sleeve = magic == InpRsiMagicNumber
         ? RSI_SLEEVE_ID
         : MagicSleeve(magic);
      if(
         PositionGetString(POSITION_SYMBOL) != InpTargetSymbol
         || !IsPortfolioMagic(magic)
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
      "CODEX_EUV20_%I64d_%s",
      AccountInfoInteger(ACCOUNT_LOGIN),
      InpTargetSymbol
   );
   mutexOwnerName = mutexBase + "_OWNER";
   mutexHeartbeatName = mutexBase + "_HEARTBEAT";
   double now = (double)TimeLocal();
   if(
      !GlobalVariableCheck(mutexHeartbeatName)
      && GlobalVariableSet(mutexHeartbeatName, 0.0) == 0
   )
      return false;
   double observedHeartbeat = GlobalVariableGet(mutexHeartbeatName);
   if(observedHeartbeat > 0.0 && now - observedHeartbeat < 180.0)
      return false;
   if(
      !GlobalVariableSetOnCondition(
         mutexHeartbeatName,
         now,
         observedHeartbeat
      )
   )
      return false;
   GlobalVariablesFlush();
   if(
      !GlobalVariableCheck(mutexHeartbeatName)
      || MathAbs(GlobalVariableGet(mutexHeartbeatName) - now) > 0.5
   )
      return false;
   mutexOwnerToken =
      now * 1000.0 + (double)(GetTickCount() % 997);
   if(GlobalVariableSet(mutexOwnerName, mutexOwnerToken) == 0)
   {
      GlobalVariableSetOnCondition(
         mutexHeartbeatName,
         observedHeartbeat,
         now
      );
      return false;
   }
   GlobalVariablesFlush();
   if(
      !GlobalVariableCheck(mutexOwnerName)
      || MathAbs(GlobalVariableGet(mutexOwnerName) - mutexOwnerToken) > 0.5
   )
   {
      GlobalVariableSetOnCondition(
         mutexHeartbeatName,
         observedHeartbeat,
         now
      );
      return false;
   }
   mutexOwned = true;
   EventSetTimer(60);
   return true;
}

bool MutexOwnershipValid()
{
   return (
      mutexOwned
      && GlobalVariableCheck(mutexOwnerName)
      && MathAbs(
         GlobalVariableGet(mutexOwnerName) - mutexOwnerToken
      ) <= 0.5
   );
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
   if(
      CountPortfolioPositions() > InpMaximumPortfolioPositions
      || OpenOwnVolumeLots() > InpMaximumOwnVolumeLots + 1e-9
      || OpenPortfolioVolumeLots() > InpMaximumPortfolioVolumeLots + 1e-9
   )
   {
      reason = "portfolio_exposure_reconciliation_failed";
      return false;
   }
   for(int sleeve = 0; sleeve < SLEEVE_COUNT; ++sleeve)
      if(CountSleevePositions(sleeve) > 1)
      {
         reason = "duplicate_sleeve_position_" + SleeveText(sleeve);
         return false;
      }
   if(CountSleevePositions(RSI_SLEEVE_ID) > 1)
   {
      reason = "duplicate_rsi_position";
      return false;
   }
   for(int index = PositionsTotal() - 1; index >= 0; --index)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetString(POSITION_SYMBOL) != InpTargetSymbol)
         continue;
      long magic = PositionGetInteger(POSITION_MAGIC);
      if(!IsPortfolioMagic(magic))
         continue;
      double open = PositionGetDouble(POSITION_PRICE_OPEN);
      double stop = PositionGetDouble(POSITION_SL);
      double target = PositionGetDouble(POSITION_TP);
      double volume = PositionGetDouble(POSITION_VOLUME);
      if(open <= 0.0 || stop <= 0.0 || target <= 0.0 || volume <= 0.0)
      {
         reason = "owned_position_missing_broker_protection";
         return false;
      }
      if(magic == InpRsiMagicNumber)
      {
         if(
            PositionGetInteger(POSITION_TYPE) != POSITION_TYPE_BUY
            || MathAbs(volume - 0.01) > 1e-9
            || stop >= open
            || target <= open
         )
         {
            reason = "rsi_position_contract_mismatch";
            return false;
         }
      }
      else
      {
         int sleeve = MagicSleeve(magic);
         bool expectedLong = IsLongSleeve(sleeve);
         if(
            sleeve < 0
            || PositionGetInteger(POSITION_TYPE)
               != (expectedLong ? POSITION_TYPE_BUY : POSITION_TYPE_SELL)
            || MathAbs(volume - ResearchLots(sleeve)) > 1e-9
            || (expectedLong && (stop >= open || target <= open))
            || (!expectedLong && (stop <= open || target >= open))
         )
         {
            reason = "h4_position_contract_mismatch";
            return false;
         }
      }
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
   double accountCurrencyUsdFactor = 0.0;
   if(!AccountCurrencyUsdFactor(accountCurrencyUsdFactor))
   {
      Audit("INIT_FAILED", "unsupported_account_currency_for_usd_risk");
      return INIT_FAILED;
   }
   if(!AcquireMutex())
   {
      Audit("INIT_FAILED", "duplicate_instance_mutex");
      return INIT_FAILED;
   }
   portfolioOrderLockName = StringFormat(
      "CODEX_EURUSD_V20_PORTFOLIO_ORDER_LOCK_%I64d_%s",
      AccountInfoInteger(ACCOUNT_LOGIN),
      InpTargetSymbol
   );
   schemaName = StringFormat(
      "CODEX_EUV20R2_SCHEMA_%I64d_%s",
      AccountInfoInteger(ACCOUNT_LOGIN),
      InpTargetSymbol
   );
   peakEquityName = StringFormat(
      "CODEX_EUV20R6_STRATEGY_PEAK_%I64d_%s",
      AccountInfoInteger(ACCOUNT_LOGIN),
      InpTargetSymbol
   );
   breakerLatchName = StringFormat(
      "CODEX_EUV20R6_BREAKER_%I64d_%s",
      AccountInfoInteger(ACCOUNT_LOGIN),
      InpTargetSymbol
   );
   breakerLatchFileName = StringFormat(
      "CODEX_EUV20R6_BREAKER_%I64d_%s.flag",
      AccountInfoInteger(ACCOUNT_LOGIN),
      InpTargetSymbol
   );
   rsiStatePrefix = StringFormat(
      "CDX_EUV20R2_RSI_%I64d_%I64d_",
      AccountInfoInteger(ACCOUNT_LOGIN),
      InpRsiMagicNumber
   );
   for(int sleeve = 0; sleeve < SLEEVE_COUNT; ++sleeve)
      signalDateNames[sleeve] = StringFormat(
         "CODEX_EUV20R2_SIG_%I64d_%s_%02d",
         AccountInfoInteger(ACCOUNT_LOGIN),
         InpTargetSymbol,
         sleeve
      );
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
      if(CountPortfolioPositions() > 0)
         EnterManagerOnlyMode("ordering_configuration_not_fully_armed");
      else
      {
         Audit("INIT_FAILED", "ordering_configuration_not_fully_armed");
         return INIT_FAILED;
      }
   }
   if(
      !(bool)MQLInfoInteger(MQL_TESTER)
      && !InpShadowMode
      && !InpEnableRsiOrders
   )
   {
      if(CountPortfolioPositions() > 0)
         EnterManagerOnlyMode("ordering_requires_rsi_orders");
      else
      {
         Audit("INIT_FAILED", "ordering_requires_rsi_orders");
         return INIT_FAILED;
      }
   }
   if(
      InpBaseMagicNumber != 26082000
      || InpRsiMagicNumber != 26082090
      || InpOrderComment != "EUV20"
      || InpTesterSleeveMask != 3
      || !InpEnableCompressionSleeves
      || InpBrokerUtcOffsetHours != 0
      || MathAbs(InpResearchStopAtrMultiple - 2.00) > 1e-9
      || InpResearchSleeveMask != 2047
      || InpResearchM30Mode != 6
      || InpResearchFridayReversalMaxBars < 1
      || InpResearchFridayReversalMaxBars > 12
      || InpResearchFridayReversalBodyMinimum < 0.0
      || InpResearchFridayReversalBodyMinimum > 0.9
      || InpResearchFridayReversalStopAtrMultiple < 0.5
      || InpResearchFridayReversalStopAtrMultiple > 3.0
      || InpResearchFridayReversalTargetR < 0.5
      || InpResearchFridayReversalTargetR > 3.0
      || MathAbs(InpResearchMonthlyPeakActivationUsd - 7.50) > 1e-9
      || MathAbs(InpResearchMonthlyGivebackUsd - 7.50) > 1e-9
      || InpResearchEventTradeCap != 7
      || MathAbs(InpMaximumSpreadPips - 2.0) > 1e-9
      || InpMaximumHoldM15Bars != 48
      || InpMaximumOwnPositions != InpResearchEventTradeCap
      || InpMaximumTradesPerUtcDay != InpResearchEventTradeCap
      || InpMaximumPortfolioPositions != 7
      || MathAbs(InpMaximumOwnVolumeLots - 0.15) > 1e-9
      || MathAbs(InpMaximumPortfolioVolumeLots - 0.16) > 1e-9
      || MathAbs(
         InpMaximumDailyClosedLossUsd - FROZEN_DAILY_LOSS_USD
      ) > 1e-9
      || MathAbs(
         InpMaximumRolling5DayClosedLossUsd
            - FROZEN_ROLLING_LOSS_USD
      ) > 1e-9
      || MathAbs(
         InpMaximumCoreCalendarMonthClosedLossUsd
            - FROZEN_CORE_MONTHLY_LOSS_USD
      ) > 1e-9
      || MathAbs(
         InpMaximumFrequencySleeveCalendarMonthClosedLossUsd
            - FROZEN_FREQUENCY_SLEEVE_MONTHLY_LOSS_USD
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
      || (
         !(bool)MQLInfoInteger(MQL_TESTER)
         && InpMinimumAccountEquityUsd <= 0.0
         && InpAllowedAccountLogin
            != FROZEN_MINIMUM_EQUITY_WAIVER_ACCOUNT
      )
      || MathAbs(
         InpMinimumFreeMarginAfterOrderUsd
            - FROZEN_MINIMUM_FREE_MARGIN_USD
      ) > 1e-9
      || InpMaximumTickAgeSeconds != 10
      || InpHeartbeatIntervalSeconds != 300
      || InpDeviationPoints != 10
      || InpStateRoundTripExerciseUtcHour < -1
      || InpStateRoundTripExerciseUtcHour > 23
      || (
         !(bool)MQLInfoInteger(MQL_TESTER)
         && InpStateRoundTripExerciseUtcHour != -1
      )
      || InpTesterStateFaultMode < 0
      || InpTesterStateFaultMode > 1
      || (
         !(bool)MQLInfoInteger(MQL_TESTER)
         && InpTesterStateFaultMode != 0
      )
      || InpTesterGuardFaultMode < 0
      || InpTesterGuardFaultMode > 2
      || (
         !(bool)MQLInfoInteger(MQL_TESTER)
         && InpTesterGuardFaultMode != 0
      )
      || (
         !(bool)MQLInfoInteger(MQL_TESTER)
         && InpResetPersistentState
         && (
            !InpShadowMode
            || InpEnableDemoOrders
            || !InpEmergencyStop
            || InpPersistentResetToken != PERSISTENT_RESET_TOKEN
         )
      )
      || (
         !(bool)MQLInfoInteger(MQL_TESTER)
         && !InpResetPersistentState
         && InpPersistentResetToken != "NO_RESET"
      )
   )
   {
      if(CountPortfolioPositions() > 0)
         EnterManagerOnlyMode("frozen_exposure_limits_changed");
      else
      {
         Audit("INIT_FAILED", "frozen_exposure_limits_changed");
         return INIT_PARAMETERS_INCORRECT;
      }
   }
   if(InpResetPersistentState && !(bool)MQLInfoInteger(MQL_TESTER))
   {
      if(CountPortfolioPositions() > 0)
         EnterManagerOnlyMode("reset_requested_with_open_position");
      else if(!ResetAllPersistentState())
      {
         Audit("INIT_FAILED", "persistent_state_reset_failed");
         return INIT_FAILED;
      }
   }
   string volumeReason = "";
   if(
      MathAbs(InpLotsPerTrade - 0.01) > 1e-9
      || !VolumeGridAllows(0.01, volumeReason)
      || !VolumeGridAllows(0.02, volumeReason)
      || !VolumeGridAllows(0.03, volumeReason)
      || !VolumeGridAllows(0.08, volumeReason)
   )
   {
      if(CountPortfolioPositions() > 0)
         EnterManagerOnlyMode("illegal_volume_" + volumeReason);
      else
      {
         Audit("INIT_FAILED", "illegal_volume_" + volumeReason);
         return INIT_PARAMETERS_INCORRECT;
      }
   }
   string reconcileReason = "";
   if(!ReconcilePositions(reconcileReason))
   {
      if(CountPortfolioPositions() > 0)
         EnterManagerOnlyMode(reconcileReason);
      else
      {
         Audit("INIT_FAILED", reconcileReason);
         return INIT_FAILED;
      }
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
      if(CountPortfolioPositions() > 0)
         EnterManagerOnlyMode("indicator_handle_invalid");
      else
      {
         Audit("INIT_FAILED", "indicator_handle_invalid");
         return INIT_FAILED;
      }
   }
   if(
      !(bool)MQLInfoInteger(MQL_TESTER)
      && GlobalVariableCheck(schemaName)
      && MathAbs(GlobalVariableGet(schemaName) - CONTRACT_SCHEMA_FINGERPRINT)
         > 0.5
   )
   {
      if(CountPortfolioPositions() > 0)
         EnterManagerOnlyMode("persisted_schema_mismatch");
      else
      {
         Audit("INIT_FAILED", "persisted_schema_mismatch");
         return INIT_FAILED;
      }
   }
   if(
      !(bool)MQLInfoInteger(MQL_TESTER)
      && !PersistGlobalVerified(
         schemaName,
         CONTRACT_SCHEMA_FINGERPRINT,
         "contract_schema"
      )
   )
   {
      if(CountPortfolioPositions() > 0)
         EnterManagerOnlyMode("contract_schema_persistence_failed");
      else
      {
         Audit("INIT_FAILED", "contract_schema_persistence_failed");
         return INIT_FAILED;
      }
   }
   for(int sleeve = 0; sleeve < SLEEVE_COUNT; ++sleeve)
   {
      lastSignalDate[sleeve] = 0;
      lastTimeExitAttemptBar[sleeve] = 0;
      if(
         !(bool)MQLInfoInteger(MQL_TESTER)
         && GlobalVariableCheck(signalDateNames[sleeve])
      )
         lastSignalDate[sleeve] =
            (int)GlobalVariableGet(signalDateNames[sleeve]);
   }
   sessionStartEquity = PortfolioStrategyEquityUsd();
   if(sessionStartEquity == DBL_MAX)
   {
      Audit("INIT_FAILED", "strategy_equity_unavailable");
      return INIT_FAILED;
   }
   sessionPeakEquity = MathMax(0.0, sessionStartEquity);
   if(!(bool)MQLInfoInteger(MQL_TESTER))
   {
      if(GlobalVariableCheck(peakEquityName))
         sessionPeakEquity = MathMax(
            sessionPeakEquity,
            GlobalVariableGet(peakEquityName)
         );
      if(!PersistGlobalVerified(
         peakEquityName,
         sessionPeakEquity,
         "startup_peak_equity"
      ))
      {
         if(CountPortfolioPositions() > 0)
            EnterManagerOnlyMode("startup_peak_persistence_failed");
         else
         {
            Audit("INIT_FAILED", "startup_peak_persistence_failed");
            return INIT_FAILED;
         }
      }
      persistentBreakerLatched =
         (
            GlobalVariableCheck(breakerLatchName)
            && GlobalVariableGet(breakerLatchName) >= 0.5
         )
         || FileIsExist(breakerLatchFileName, FILE_COMMON);
   }
   if(managerOnlyMode)
      LatchPersistentBreaker("startup_manager_only");
   lastM15Open = iTime(_Symbol, PERIOD_M15, 0);
   string clockReason = "";
   if(!ServerClockIsUtcAligned(clockReason))
   {
      if(CountPortfolioPositions() > 0)
         EnterManagerOnlyMode(clockReason);
      else
      {
         Audit("INIT_FAILED", clockReason);
         return INIT_FAILED;
      }
   }
   string rsiReason = "";
   if(!RsiInitialize(rsiReason))
   {
      if(CountPortfolioPositions() > 0)
         EnterManagerOnlyMode(rsiReason);
      else
      {
         Audit("INIT_FAILED", rsiReason, RSI_SLEEVE_ID);
         return INIT_FAILED;
      }
   }
   trade.SetDeviationInPoints(InpDeviationPoints);
   if(!Audit(
      "INIT_OK",
      ((bool)MQLInfoInteger(MQL_TESTER)
         ? "tester_"
         : (InpShadowMode ? "shadow_demo_" : "ordering_demo_"))
           + volumeReason
           + (InpEnableRsiOrders ? "_rsi_orders_armed" : "_rsi_observer")
           + (managerOnlyMode ? "_manager_only" : "_coordinator_ready")
   ))
   {
      if(CountPortfolioPositions() <= 0)
         return INIT_FAILED;
      EnterManagerOnlyMode("audit_unavailable");
      return INIT_SUCCEEDED;
   }
   if(!Audit(
      "STARTUP_LATCH",
      TimeToString(lastM15Open, TIME_DATE | TIME_MINUTES)
   ))
   {
      if(CountPortfolioPositions() <= 0)
         return INIT_FAILED;
      EnterManagerOnlyMode("audit_unavailable");
   }
   return INIT_SUCCEEDED;
}

bool EmitHeartbeat()
{
   MqlTick tick;
   long tickAgeSeconds = -1;
   if(SymbolInfoTick(_Symbol, tick) && tick.time > 0)
      tickAgeSeconds = (long)(TimeCurrent() - tick.time);
   string mode = managerOnlyMode
      ? "manager_only"
      : (InpShadowMode ? "shadow_disarmed" : "ordering");
   return Audit(
      "HEARTBEAT",
      StringFormat(
          "mode=%s;rsi_orders=%s;positions=%d;lots=%.2f;balance=%.2f;equity=%.2f;"
          "strategy_equity_usd=%.2f;breaker=%s;persistence=%s;mutex=%s;"
          "last_m15=%I64d;tick_age=%I64d",
         mode,
         BoolText(InpEnableRsiOrders),
         CountPortfolioPositions(),
         OpenPortfolioVolumeLots(),
          AccountInfoDouble(ACCOUNT_BALANCE),
          AccountInfoDouble(ACCOUNT_EQUITY),
          PortfolioStrategyEquityUsd(),
         BoolText(persistentBreakerLatched),
         BoolText(criticalPersistenceHealthy),
         BoolText(MutexOwnershipValid()),
         (long)lastM15Open,
         tickAgeSeconds
      )
   );
}

void OnTimer()
{
   RefreshPersistentEquityState();
   RsiSaveState();
   if(!managerOnlyMode && !MutexOwnershipValid())
   {
      mutexOwned = false;
      managerOnlyMode = true;
      managerOnlyReason = "mutex_ownership_lost";
      persistentBreakerLatched = true;
      Audit("MUTEX_OWNERSHIP_LOST", "manager_only_until_flat");
   }
   if(mutexOwned)
   {
      if(!PersistGlobalVerified(
         mutexHeartbeatName,
         (double)TimeLocal(),
         "mutex_heartbeat"
      ))
         EnterManagerOnlyMode("mutex_heartbeat_persistence_failed");
   }
   if(
      lastHeartbeatAuditLocal <= 0
      || TimeLocal() - lastHeartbeatAuditLocal >= InpHeartbeatIntervalSeconds
   )
   {
      if(!EmitHeartbeat())
         EnterManagerOnlyMode("heartbeat_audit_failed");
      lastHeartbeatAuditLocal = TimeLocal();
   }
   if(managerOnlyMode)
   {
      ManagePersistentBreakerExits();
      if(!mutexOwned && CountPortfolioPositions() == 0)
         ExpertRemove();
   }
}

void OnDeinit(const int reason)
{
   RsiReleaseIndicators();
   Audit("DEINIT", IntegerToString(reason));
   EventKillTimer();
   ReleasePortfolioOrderLock();
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
   if(!managerOnlyMode && !MutexOwnershipValid())
   {
      mutexOwned = false;
      managerOnlyMode = true;
      managerOnlyReason = "mutex_ownership_lost";
      persistentBreakerLatched = true;
      Audit("MUTEX_OWNERSHIP_LOST", "manager_only_until_flat");
   }
   RefreshPersistentEquityState();
   ManagePersistentBreakerExits();
   if(managerOnlyMode)
   {
      if(!mutexOwned && CountPortfolioPositions() == 0)
         ExpertRemove();
      return;
   }
   ManageTimeExits();
   MaybeExerciseCorruptStateWithOpenPosition();
   if(managerOnlyMode)
   {
      ManagePersistentBreakerExits();
      return;
   }
   MqlTick tick;
   bool rsiResolved = SymbolInfoTick(_Symbol, tick)
      && RsiResolveVirtualTrade(tick);
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
   RsiEvaluateCompletedBar(currentM15, rsiResolved);
   MqlDateTime parts;
   UtcParts(currentM15, parts);
   int dateKey = UtcDateKey(currentM15);
   if(
      InpStateRoundTripExerciseUtcHour >= 0
      && parts.hour == InpStateRoundTripExerciseUtcHour
      && parts.min == 0
      && dateKey != lastRestartExerciseDate
   )
   {
      bool rebuilt = RebuildDailyState(currentM15);
      string rsiRestartReason = "";
      bool rsiExact = RsiExerciseStateRoundTrip(rsiRestartReason);
      string reconcileReason = "";
      bool positionsExact = ReconcilePositions(reconcileReason);
      if(CountPortfolioPositions() > 0)
         restartExercisesWithOpenPositions++;
      lastRestartExerciseDate = dateKey;
      Audit(
         rebuilt && rsiExact && positionsExact
            ? "STATE_ROUNDTRIP_OK"
            : "STATE_ROUNDTRIP_FAILED",
         StringFormat(
            "open_positions_%d_%s_%s",
            CountPortfolioPositions(),
            rsiRestartReason,
            reconcileReason
         )
      );
      if(!rebuilt || !rsiExact || !positionsExact)
         EnterManagerOnlyMode("state_roundtrip_reinitialization_failed");
   }
}

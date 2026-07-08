//+------------------------------------------------------------------+
//| A1XauM5MomentumContinuationExecutor.mq5                           |
//| EXPERIMENTAL DEMO ONLY - A1 XAUUSD M5 break-and-run continuation. |
//| This is a separate lane from 920101 breakout_retest. It exists to |
//| catch clean impulse moves that do not retest a broken level.       |
//|                                                                   |
//| Defaults are observer-safe. Broker action requires explicit chart  |
//| inputs, demo account, account allowlist, and no kill switch file.  |
//| Magic 932200. Fixed 0.01 lot. Never manages other EAs' positions. |
//+------------------------------------------------------------------+
#property copyright "maksoftwares - experimental demo lane"
#property version   "1.000"
#property strict

#include <Trade/Trade.mqh>

enum MomentumDirectionMode
  {
   MOMENTUM_BOTH_DIRECTIONS = 0,
   MOMENTUM_LONG_ONLY = 1,
   MOMENTUM_SHORT_ONLY = 2
  };

enum MomentumSignalMode
  {
   SIGNAL_BREAK_AND_RUN = 0,
   SIGNAL_EMA_PULLBACK = 1,
   SIGNAL_COMPRESSION_EXPANSION = 2,
   SIGNAL_SWEEP_RECLAIM = 3,
   SIGNAL_OPENING_RANGE_CONTINUATION = 4,
   SIGNAL_M5_EMA_TREND_CONTINUATION = 5,
   SIGNAL_OPENING_RANGE_REVERSAL = 6,
   SIGNAL_D1_COMPRESSION_H4_EXPANSION = 7,
   SIGNAL_H4_TREND_PULLBACK_D1_BIAS = 8,
   SIGNAL_WEEKLY_LEVEL_H4_REJECTION = 9,
   SIGNAL_D1_COMPRESSION_H1_EXPANSION = 10,
   SIGNAL_DAILY_EXTREME_RECLAIM = 11,
   SIGNAL_WEEKLY_DAMAGE_H1 = 12,
   SIGNAL_PRIOR_DAY_LEVEL_M5 = 13,
   SIGNAL_EVENT_REACTION_M5 = 14,
   SIGNAL_BEAR_BREAKDOWN_RETEST = 15,
   SIGNAL_BEAR_SWEEP_RECLAIM = 16,
   SIGNAL_BEAR_LOWER_HIGH_REJECTION = 17
  };

input string InpRunId                         = "A1_XAU_M5_MOMENTUM_CONTINUATION_SAFE_DEFAULT";
input bool   InpAllowDemoTrading              = false;
input bool   InpAllowNonDemoAccounts          = false;
input long   InpAllowedAccountLogin           = 0;
input string InpExpectedServerMarker          = "Demo";
input string InpTargetSymbol                  = "XAUUSD";
input long   InpMagicNumber                   = 932200;
input double InpFixedLots                     = 0.01;
input bool   InpUseRiskNormalizedLots         = false;
input double InpRiskAmountUsd                 = 0.00;
input double InpMaxRiskLots                   = 0.05;
input int    InpDeviationPoints               = 80;
input int    InpMaxSpreadPoints               = 75;
input double InpMaxEstimatedCostR             = 0.15;
input int    InpMaxTradesPerDay               = 6;
input bool   InpPortfolioDailyGuardEnabled    = false;
input string InpPortfolioGuardMagicCsv        = "";
input int    InpPortfolioMaxTradesPerDay      = 0;
input double InpPortfolioDailyProfitTargetUsd = 0.00;
input double InpPortfolioDailyLossStopUsd     = 0.00;
input int    InpPortfolioCooldownAfterLossMinutes = 0;
input int    InpCooldownMinutes               = 10;
input bool   InpOnePositionPerMagic           = true;
input int    InpMaxOpenPositionsPerMagic      = 1;     // used only when InpOnePositionPerMagic=false
input string InpKillSwitchFileName            = "experimental_demo_kill_switch.txt";
input string InpStartupLogFileName            = "a1_xau_m5_momentum_startup_log.csv";
input string InpSignalLogFileName             = "a1_xau_m5_momentum_signal_log.csv";
input string InpOrderLogFileName              = "a1_xau_m5_momentum_order_log.csv";
input string InpManagementLogFileName         = "a1_xau_m5_momentum_management_log.csv";
input string InpDealLogFileName               = "a1_xau_m5_momentum_deal_log.csv";
input string InpOrderComment                  = "A1_XAU_M5_MOM";

// Mechanical trigger inputs. These are deliberately few and auditable.
input MomentumSignalMode InpSignalMode        = SIGNAL_BREAK_AND_RUN;
input int    InpBreakLookbackBars             = 12;    // previous 60 minutes on M5
input int    InpAtrPeriod                     = 14;
input int    InpPullbackEmaPeriod             = 20;
input double InpPullbackTouchAtr              = 0.25;
input int    InpCompressionLookbackBars       = 8;
input double InpCompressionMaxRangeAtr        = 1.20;
input double InpCompressionBreakAtrMultiple   = 0.10;
input int    InpSweepLookbackBars             = 12;
input double InpSweepAtrMultiple              = 0.10;
input double InpReclaimAtrMultiple            = 0.05;
input int    InpOpeningRangeStartHour         = 7;
input int    InpOpeningRangeMinutes           = 60;
input int    InpOpeningTradeWindowHours       = 5;
input double InpOpeningBreakAtrMultiple       = 0.10;
input int    InpM5TrendEmaFastPeriod          = 8;
input int    InpM5TrendEmaSlowPeriod          = 21;
input int    InpM5TrendSlopeBars              = 3;
input double InpM5TrendMinSlopeAtr            = 0.05;
input double InpM5TrendMaxDistanceAtr         = 1.20;
input double InpBreakAtrMultiple              = 0.20;
input double InpMinRangeAtr                   = 0.60;
input double InpMinBodyFraction               = 0.45;
input double InpLongCloseLocation             = 0.72;
input double InpShortCloseLocation            = 0.28;
input double InpMinThreeBarMoveAtr            = 0.70;
input double InpMaxThreeBarMoveAtr            = 0.00;   // 0 disables exhaustion cap
input double InpMinBreakDistanceAtr           = 0.00;   // 0 disables minimum break-distance guard
input double InpMaxBreakDistanceAtr           = 0.00;   // 0 disables maximum break-distance guard
input double InpMinAtrAbsoluteForEntry        = 0.00;   // 0 disables absolute ATR floor
input double InpD1CompressionAtrPercentileMax = 30.00;
input int    InpD1CompressionBoxDays          = 5;
input double InpD1CompressionRangeMedianMax   = 1.00;
input double InpD1CompressionH4MinBodyFraction = 0.50;
input bool   InpH4D1SupportiveStateGuardEnabled = false;
input int    InpH4D1SupportiveEmaPeriod      = 20;
input int    InpH4D1SupportiveSlopeLagBars   = 5;
input int    InpD1SupportStateGateMode       = 0;      // 0=off, 1=require supportive, 2=require non-supportive, 3=require bearish, 4=require non-up
input int    InpD1SupportStateEmaPeriod      = 20;
input int    InpD1SupportStateSlopeLagBars   = 5;
input bool   InpD1StructuralDownGateEnabled  = false;
input int    InpD1StructuralDownEmaPeriod    = 50;
input int    InpD1StructuralDownSlopeLagBars = 5;
input bool   InpH4D1WeeklyLossGovernorEnabled = false;
input double InpH4D1WeeklyLossLimitUsd       = 150.00;
input double InpDailyExtremeMinMoveAtr        = 1.00;
input double InpDailyExtremeTouchAtr          = 0.05;
input double InpDailyExtremeReclaimAtr        = 0.10;
input double InpDailyExtremeStopBufferAtr     = 0.10;
input double InpDailyExtremeMinBodyFraction   = 0.25;
input int    InpDailyExtremeMinBarsSinceOpen  = 24;
input int    InpDailyExtremeStartHour         = 0;
input int    InpDailyExtremeEndHour           = 24;
input int    InpWeeklyDamageMode              = 0;      // 0=reversal, 1=continuation.
input int    InpWeeklyDamageStartDay          = 3;      // MQL day_of_week: Wednesday.
input int    InpWeeklyDamageEndDay            = 5;      // Friday.
input double InpWeeklyDamageMinMoveAtr        = 1.00;
input double InpWeeklyDamageTouchAtr          = 0.10;
input double InpWeeklyDamageReclaimAtr        = 0.15;
input double InpWeeklyDamageStopBufferAtr     = 0.20;
input double InpWeeklyDamageMinBodyFraction   = 0.25;
input int    InpPriorDayLevelMode             = 0;      // 0=continuation, 1=reversal.
input int    InpPriorDayLevelStartHour        = 6;
input int    InpPriorDayLevelEndHour          = 22;
input double InpPriorDayLevelBreakAtr         = 0.10;
input double InpPriorDayLevelTouchAtr         = 0.05;
input double InpPriorDayLevelReclaimAtr       = 0.10;
input double InpPriorDayLevelStopBufferAtr    = 0.25;
input double InpPriorDayLevelMinBodyFraction  = 0.35;
input string InpEventReactionCalendarFileName = "A1_XAU_EVENT_REACTION_CALENDAR_202207_202606.csv";
input int    InpEventReactionEventType        = 0;      // 0=NFP, 1=CPI, 2=FOMC.
input int    InpEventReactionMode             = 0;      // 0=impulse continuation, 1=spike fade.
input int    InpEventReactionServerUtcOffsetMinutes = 0;
input int    InpEventReactionImpulseMinutes   = 15;
input int    InpEventReactionStartMinutes     = 5;
input int    InpEventReactionEndMinutes       = 60;
input double InpEventReactionBreakAtr         = 0.10;
input double InpEventReactionStopBufferAtr    = 0.10;
input double InpEventReactionMinBodyFraction  = 0.35;
input int    InpBearRetestLookbackBars        = 10;
input int    InpBearRetestSupportLookbackBars = 12;
input double InpBearRetestBreakAtr            = 0.10;
input double InpBearRetestTouchAtr            = 0.05;
input double InpBearRetestReclaimAtr          = 0.05;
input double InpBearRetestStopBufferAtr       = 0.25;
input double InpBearRetestMinBodyFraction     = 0.30;
input int    InpBearSweepReclaimBars          = 2;
input double InpBearSweepTouchAtr             = 0.05;
input double InpBearSweepReclaimAtr           = 0.05;
input double InpBearSweepStopBufferAtr        = 0.25;
input double InpBearSweepMinBodyFraction      = 0.20;
input int    InpBearLowerHighLookbackBars     = 48;
input int    InpBearLowerHighRecentBars       = 12;
input double InpBearLowerHighMinGapAtr        = 0.25;
input double InpBearLowerHighMinDropAtr       = 0.80;
input double InpBearLowerHighEmaTouchAtr      = 0.20;
input double InpBearLowerHighReclaimAtr       = 0.05;
input double InpBearLowerHighStopBufferAtr    = 0.25;
input double InpBearLowerHighMinBodyFraction  = 0.45;
input double InpStopAtrMultiple               = 2.50;
input int    InpStopFloorPoints               = 350;
input int    InpStopCeilingPoints             = 1800;
input int    InpStopCapPoints                 = 0;     // 0 disables; caps effective stop distance instead of filtering.
input double InpRiskReward                    = 1.50;
input string InpBlockedEntryHoursCsv          = "";     // comma-separated server hours, e.g. "9,10"
input string InpBlockedEntryDayHoursCsv       = "";     // comma-separated MQL day:hour pairs, e.g. "5:20"
input string InpBlockedLongEntryHoursCsv      = "";     // optional direction-specific server-hour block list
input string InpBlockedShortEntryHoursCsv     = "";     // optional direction-specific server-hour block list
input MomentumDirectionMode InpDirectionMode  = MOMENTUM_BOTH_DIRECTIONS;
input bool   InpUseH1TrendFilter              = false;
input bool   InpH1TrendApplyToLong            = true;
input bool   InpH1TrendApplyToShort           = true;
input int    InpH1EmaFastPeriod               = 20;
input int    InpH1EmaSlowPeriod               = 50;
input int    InpH1TrendSlopeBars              = 3;
input int    InpH1TrendMinSlopePoints         = 0;
input bool   InpUseH4TrendFilter              = false;
input bool   InpH4TrendApplyToLong            = true;
input bool   InpH4TrendApplyToShort           = true;
input int    InpH4EmaFastPeriod               = 20;
input int    InpH4EmaSlowPeriod               = 50;
input int    InpH4TrendSlopeBars              = 3;
input int    InpH4TrendMinSlopePoints         = 0;
input bool   InpUseDirectionalSessionFilter   = false;
input int    InpLongSessionStartHour          = 0;
input int    InpLongSessionEndHour            = 24;
input int    InpShortSessionStartHour         = 0;
input int    InpShortSessionEndHour           = 24;
input bool   InpFeatureLossFilterEnabled      = false;
input bool   InpFeatureLossFilterShadowOnly   = true;
input double InpShortCloseToRecentExtremeBlockMin = -0.75;
input bool   InpShortCloseToRecentExtremeBlockMaxEnabled = false;
input double InpShortCloseToRecentExtremeBlockMax = -2.51;

// Default-off trade management for offline repair testing.
input bool   InpProfitProtectionEnabled       = false;
input bool   InpProfitProtectionShadowOnly    = true;
input double InpProfitProtectionTriggerR      = 0.80;
input double InpProfitProtectionLockR         = 0.20;
input bool   InpPartialCloseEnabled           = false;
input bool   InpPartialCloseShadowOnly        = true;
input double InpPartialFraction               = 0.50;
input double InpPartialTriggerR               = 0.70;
input double InpRunnerTargetR                 = 1.50;
input bool   InpMoveSLToBEOnPartial           = true;
input bool   InpSplitEntryEnabled             = false;
input bool   InpSplitEntryShadowOnly          = true;
input double InpSplitEntryFirstTargetR        = 0.70;
input double InpSplitEntryFirstLotFraction    = 0.50;
input double InpSplitEntryRunnerTargetR       = 2.00;
input bool   InpSplitEntryMoveRunnerSLToBE    = true;
input int    InpSplitEntryBreakEvenMode       = 1;     // 0=never, 1=on TP1 fill, 2=at +1.0R.
input bool   InpSplitEntryUseMinLotPair       = false;
input bool   InpEarlyAdverseExitEnabled       = false;
input bool   InpEarlyAdverseExitShadowOnly    = true;
input int    InpEarlyAdverseExitAfterMinutes  = 60;
input double InpEarlyAdverseExitR             = 0.50;
input int    InpManagementLogMode             = 1;     // 0=off, 1=normal.
input bool   InpSignalClaimEnabled            = false;
input string InpSignalClaimNamespace          = "A1MOM_SPLIT_BE";
input int    InpSignalClaimPriority           = 0;     // 1 is highest priority; lower-priority charts skip when a higher claim exists.
input int    InpSignalClaimWindowMinutes      = 4;
input int    InpSignalClaimGraceSeconds       = 2;

CTrade   g_trade;
int      g_atr_handle = INVALID_HANDLE;
int      g_m5_pullback_ema_handle = INVALID_HANDLE;
int      g_m5_trend_ema_fast_handle = INVALID_HANDLE;
int      g_m5_trend_ema_slow_handle = INVALID_HANDLE;
int      g_h1_ema_fast_handle = INVALID_HANDLE;
int      g_h1_ema_slow_handle = INVALID_HANDLE;
int      g_h4_ema_fast_handle = INVALID_HANDLE;
int      g_h4_ema_slow_handle = INVALID_HANDLE;
datetime g_last_m5_bar = 0;
datetime g_last_h4_decision_bar = 0;
datetime g_last_h1_decision_bar = 0;
datetime g_last_trade_time = 0;
string   g_trade_day = "";
int      g_trades_today = 0;
datetime g_event_reaction_times[];
string   g_event_reaction_types[];
bool     g_event_reaction_consumed[];

string BoolText(const bool value) { return value ? "true" : "false"; }

string Timestamp()
  {
   return TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS);
  }

bool ContainsText(const string haystack, const string needle)
  {
   if(needle == "")
      return true;
   return StringFind(haystack, needle) >= 0;
  }

void AppendCsv(
   const string file_name,
   const string &values[]
)
  {
   const bool exists = FileIsExist(file_name);
   int handle = FileOpen(file_name, FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI);
   if(handle == INVALID_HANDLE)
     {
      PrintFormat("A1_M5_MOM: failed to open log %s err=%d", file_name, GetLastError());
      return;
     }
   FileSeek(handle, 0, SEEK_END);
   if(!exists)
     {
      if(file_name == InpStartupLogFileName)
         FileWrite(handle, "timestamp_broker", "run_id", "server", "account", "symbol", "magic", "demo_trading", "broker_action", "status");
      else if(file_name == InpSignalLogFileName)
         FileWrite(handle, "timestamp_broker", "timestamp_local", "run_id", "account", "symbol", "magic", "stage", "direction", "reason", "bid", "ask", "spread_points", "recent_high", "recent_low", "signal_open", "signal_high", "signal_low", "signal_close", "atr", "body_fraction", "close_location", "three_bar_move_atr", "break_distance_atr", "estimated_cost_r");
      else if(file_name == InpOrderLogFileName)
         FileWrite(handle, "timestamp_broker", "timestamp_local", "run_id", "account", "symbol", "magic", "action", "direction", "lots", "bid", "ask", "spread_points", "entry_reference", "sl", "tp", "stop_points", "estimated_cost_r", "retcode", "retcode_description", "order_ticket", "deal_ticket", "result_price", "reason");
      else if(file_name == InpManagementLogFileName)
         FileWrite(handle, "timestamp_broker", "timestamp_local", "run_id", "account", "symbol", "magic", "action", "direction", "position_ticket", "volume", "entry_price", "current_price", "current_sl", "new_sl", "tp", "risk_points", "unrealized_r", "trigger_r", "lock_r", "retcode", "reason");
      else if(file_name == InpDealLogFileName)
         FileWrite(handle, "timestamp_broker", "timestamp_local", "run_id", "account", "symbol", "magic", "deal_ticket", "position_id", "entry_code", "type_code", "reason_code", "direction", "volume", "price", "profit", "commission", "swap", "order_ticket", "comment");
     }
   const int n = ArraySize(values);
   switch(n)
     {
      case 9:  FileWrite(handle, values[0], values[1], values[2], values[3], values[4], values[5], values[6], values[7], values[8]); break;
      case 19: FileWrite(handle, values[0], values[1], values[2], values[3], values[4], values[5], values[6], values[7], values[8], values[9], values[10], values[11], values[12], values[13], values[14], values[15], values[16], values[17], values[18]); break;
      case 21: FileWrite(handle, values[0], values[1], values[2], values[3], values[4], values[5], values[6], values[7], values[8], values[9], values[10], values[11], values[12], values[13], values[14], values[15], values[16], values[17], values[18], values[19], values[20]); break;
      case 24: FileWrite(handle, values[0], values[1], values[2], values[3], values[4], values[5], values[6], values[7], values[8], values[9], values[10], values[11], values[12], values[13], values[14], values[15], values[16], values[17], values[18], values[19], values[20], values[21], values[22], values[23]); break;
      case 24 + 1: FileWrite(handle, values[0], values[1], values[2], values[3], values[4], values[5], values[6], values[7], values[8], values[9], values[10], values[11], values[12], values[13], values[14], values[15], values[16], values[17], values[18], values[19], values[20], values[21], values[22], values[23], values[24]); break;
      default:
        {
         string row = "";
         for(int i = 0; i < n; i++)
           {
            if(i > 0)
               row += ",";
            row += values[i];
           }
         FileWrite(handle, row);
        }
     }
   FileClose(handle);
  }

void LogStartup(const string status)
  {
   string values[];
   ArrayResize(values, 9);
   values[0] = Timestamp();
   values[1] = InpRunId;
   values[2] = AccountInfoString(ACCOUNT_SERVER);
   values[3] = IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN));
   values[4] = _Symbol;
   values[5] = IntegerToString((int)InpMagicNumber);
   values[6] = BoolText(AccountInfoInteger(ACCOUNT_TRADE_MODE) == ACCOUNT_TRADE_MODE_DEMO);
   values[7] = BoolText(InpAllowDemoTrading);
   values[8] = status;
   AppendCsv(InpStartupLogFileName, values);
  }

void LogSignal(
   const string stage,
   const string direction,
   const string reason,
   const double bid,
   const double ask,
   const long spread_points,
   const double recent_high,
   const double recent_low,
   const double open,
   const double high,
   const double low,
   const double close,
   const double atr,
   const double body_fraction,
   const double close_location,
   const double three_bar_move_atr,
   const double break_distance_atr,
   const double estimated_cost_r
)
  {
   string values[];
   ArrayResize(values, 24);
   values[0] = Timestamp();
   values[1] = TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS);
   values[2] = InpRunId;
   values[3] = IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN));
   values[4] = _Symbol;
   values[5] = IntegerToString((int)InpMagicNumber);
   values[6] = stage;
   values[7] = direction;
   values[8] = reason;
   values[9] = DoubleToString(bid, _Digits);
   values[10] = DoubleToString(ask, _Digits);
   values[11] = IntegerToString((int)spread_points);
   values[12] = DoubleToString(recent_high, _Digits);
   values[13] = DoubleToString(recent_low, _Digits);
   values[14] = DoubleToString(open, _Digits);
   values[15] = DoubleToString(high, _Digits);
   values[16] = DoubleToString(low, _Digits);
   values[17] = DoubleToString(close, _Digits);
   values[18] = DoubleToString(atr, _Digits);
   values[19] = DoubleToString(body_fraction, 4);
   values[20] = DoubleToString(close_location, 4);
   values[21] = DoubleToString(three_bar_move_atr, 4);
   values[22] = DoubleToString(break_distance_atr, 4);
   values[23] = DoubleToString(estimated_cost_r, 4);
   AppendCsv(InpSignalLogFileName, values);
  }

void LogOrder(
   const string action,
   const string direction,
   const double lots,
   const double bid,
   const double ask,
   const long spread_points,
   const double entry_reference,
   const double sl,
   const double tp,
   const double stop_points,
   const double estimated_cost_r,
   const long retcode,
   const string retcode_description,
   const ulong order_ticket,
   const ulong deal_ticket,
   const double result_price,
   const string reason
)
  {
   string values[];
   ArrayResize(values, 24);
   values[0] = Timestamp();
   values[1] = TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS);
   values[2] = InpRunId;
   values[3] = IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN));
   values[4] = _Symbol;
   values[5] = IntegerToString((int)InpMagicNumber);
   values[6] = action;
   values[7] = direction;
   values[8] = DoubleToString(lots, 2);
   values[9] = DoubleToString(bid, _Digits);
   values[10] = DoubleToString(ask, _Digits);
   values[11] = IntegerToString((int)spread_points);
   values[12] = DoubleToString(entry_reference, _Digits);
   values[13] = DoubleToString(sl, _Digits);
   values[14] = DoubleToString(tp, _Digits);
   values[15] = DoubleToString(stop_points, 2);
   values[16] = DoubleToString(estimated_cost_r, 4);
   values[17] = IntegerToString((int)retcode);
   values[18] = retcode_description;
   values[19] = IntegerToString((int)order_ticket);
   values[20] = IntegerToString((int)deal_ticket);
   values[21] = DoubleToString(result_price, _Digits);
   values[22] = reason;
   values[23] = "";
  AppendCsv(InpOrderLogFileName, values);
  }

void LogManagement(
   const string action,
   const string direction,
   const ulong position_ticket,
   const double volume,
   const double entry_price,
   const double current_price,
   const double current_sl,
   const double new_sl,
   const double tp,
   const double risk_points,
   const double unrealized_r,
   const long retcode,
   const string reason,
   const double trigger_r = -1.0,
   const double lock_r = -1.0
)
  {
   if(InpManagementLogMode <= 0)
      return;

   string values[];
   ArrayResize(values, 21);
   values[0] = Timestamp();
   values[1] = TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS);
   values[2] = InpRunId;
   values[3] = IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN));
   values[4] = _Symbol;
   values[5] = IntegerToString((int)InpMagicNumber);
   values[6] = action;
   values[7] = direction;
   values[8] = IntegerToString((long)position_ticket);
   values[9] = DoubleToString(volume, 2);
   values[10] = DoubleToString(entry_price, _Digits);
   values[11] = DoubleToString(current_price, _Digits);
   values[12] = DoubleToString(current_sl, _Digits);
   values[13] = DoubleToString(new_sl, _Digits);
   values[14] = DoubleToString(tp, _Digits);
   values[15] = DoubleToString(risk_points, 2);
   values[16] = DoubleToString(unrealized_r, 4);
   values[17] = DoubleToString(trigger_r >= 0.0 ? trigger_r : InpProfitProtectionTriggerR, 2);
   values[18] = DoubleToString(lock_r >= 0.0 ? lock_r : InpProfitProtectionLockR, 2);
   values[19] = IntegerToString((int)retcode);
   values[20] = reason;
  AppendCsv(InpManagementLogFileName, values);
  }

string DealDirection(
   const ENUM_DEAL_ENTRY entry,
   const ENUM_DEAL_TYPE type
)
  {
   if(type == DEAL_TYPE_BUY)
      return entry == DEAL_ENTRY_IN ? "LONG" : "SHORT";
   if(type == DEAL_TYPE_SELL)
      return entry == DEAL_ENTRY_IN ? "SHORT" : "LONG";
   return "";
  }

void LogDealTransaction(const ulong deal_ticket)
  {
   if(InpDealLogFileName == "")
      return;
   if(!HistoryDealSelect(deal_ticket))
      return;
   if((long)HistoryDealGetInteger(deal_ticket, DEAL_MAGIC) != InpMagicNumber ||
      HistoryDealGetString(deal_ticket, DEAL_SYMBOL) != InpTargetSymbol)
      return;

   const ENUM_DEAL_ENTRY entry = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(deal_ticket, DEAL_ENTRY);
   const ENUM_DEAL_TYPE type = (ENUM_DEAL_TYPE)HistoryDealGetInteger(deal_ticket, DEAL_TYPE);
   string values[];
   ArrayResize(values, 19);
   values[0] = Timestamp();
   values[1] = TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS);
   values[2] = InpRunId;
   values[3] = IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN));
   values[4] = InpTargetSymbol;
   values[5] = IntegerToString((int)InpMagicNumber);
   values[6] = IntegerToString((long)deal_ticket);
   values[7] = IntegerToString((long)HistoryDealGetInteger(deal_ticket, DEAL_POSITION_ID));
   values[8] = IntegerToString((int)entry);
   values[9] = IntegerToString((int)type);
   values[10] = IntegerToString((int)HistoryDealGetInteger(deal_ticket, DEAL_REASON));
   values[11] = DealDirection(entry, type);
   values[12] = DoubleToString(HistoryDealGetDouble(deal_ticket, DEAL_VOLUME), 2);
   values[13] = DoubleToString(HistoryDealGetDouble(deal_ticket, DEAL_PRICE), _Digits);
   values[14] = DoubleToString(HistoryDealGetDouble(deal_ticket, DEAL_PROFIT), 2);
   values[15] = DoubleToString(HistoryDealGetDouble(deal_ticket, DEAL_COMMISSION), 2);
   values[16] = DoubleToString(HistoryDealGetDouble(deal_ticket, DEAL_SWAP), 2);
   values[17] = IntegerToString((long)HistoryDealGetInteger(deal_ticket, DEAL_ORDER));
   values[18] = HistoryDealGetString(deal_ticket, DEAL_COMMENT);
   AppendCsv(InpDealLogFileName, values);
  }

void SkipCsvRecordRemainder(const int handle)
  {
   while(!FileIsEnding(handle) && !FileIsLineEnding(handle))
      FileReadString(handle);
  }

datetime ParseUtcCalendarTimestamp(string value)
  {
   StringTrimLeft(value);
   StringTrimRight(value);
   StringReplace(value, "T", " ");
   StringReplace(value, "-", ".");
   StringReplace(value, "Z", "");
   const datetime parsed = StringToTime(value);
   if(parsed <= 0)
      return 0;
   return parsed + InpEventReactionServerUtcOffsetMinutes * 60;
  }

bool IsSupportedEventReactionType(const string event_type)
  {
   return event_type == "NFP" || event_type == "CPI" || event_type == "FOMC";
  }

string SelectedEventReactionType()
  {
   if(InpEventReactionEventType == 1)
      return "CPI";
   if(InpEventReactionEventType == 2)
      return "FOMC";
   return "NFP";
  }

bool LoadEventReactionCalendar()
  {
   ArrayResize(g_event_reaction_times, 0);
   ArrayResize(g_event_reaction_types, 0);
   ArrayResize(g_event_reaction_consumed, 0);

   int handle = FileOpen(InpEventReactionCalendarFileName, FILE_READ | FILE_CSV | FILE_ANSI, ',');
   if(handle == INVALID_HANDLE)
      handle = FileOpen(InpEventReactionCalendarFileName, FILE_READ | FILE_CSV | FILE_ANSI | FILE_COMMON, ',');
   if(handle == INVALID_HANDLE)
     {
      PrintFormat("A1_M5_MOM: failed to open event calendar %s err=%d", InpEventReactionCalendarFileName, GetLastError());
      return false;
     }

   while(!FileIsEnding(handle))
     {
      string fields[7];
      fields[0] = FileReadString(handle);
      for(int col = 1; col < 7 && !FileIsEnding(handle); col++)
         fields[col] = FileReadString(handle);
      SkipCsvRecordRemainder(handle);

      string event_id = fields[0];
      string event_type = fields[1];
      string timestamp_utc = fields[6];
      StringTrimLeft(event_id);
      StringTrimRight(event_id);
      StringTrimLeft(event_type);
      StringTrimRight(event_type);
      StringTrimLeft(timestamp_utc);
      StringTrimRight(timestamp_utc);

      if(event_id == "" || event_id == "event_id")
         continue;
      if(!IsSupportedEventReactionType(event_type))
         continue;

      const datetime event_time = ParseUtcCalendarTimestamp(timestamp_utc);
      if(event_time <= 0)
         continue;

      const int row = ArraySize(g_event_reaction_times);
      ArrayResize(g_event_reaction_times, row + 1);
      ArrayResize(g_event_reaction_types, row + 1);
      ArrayResize(g_event_reaction_consumed, row + 1);
      g_event_reaction_times[row] = event_time;
      g_event_reaction_types[row] = event_type;
      g_event_reaction_consumed[row] = false;
     }
   FileClose(handle);

   const int loaded = ArraySize(g_event_reaction_times);
   PrintFormat("A1_M5_MOM: loaded %d event-reaction calendar rows from %s", loaded, InpEventReactionCalendarFileName);
   return loaded > 0;
  }

int OnInit()
  {
   if(_Symbol != InpTargetSymbol)
     {
      PrintFormat("A1_M5_MOM: attached to %s but target is %s.", _Symbol, InpTargetSymbol);
      LogStartup("INIT_FAILED_WRONG_SYMBOL");
      return INIT_FAILED;
     }
   if(!SymbolSelect(InpTargetSymbol, true))
     {
      LogStartup("INIT_FAILED_SYMBOL_SELECT");
      return INIT_FAILED;
     }
   if(!InpAllowNonDemoAccounts && AccountInfoInteger(ACCOUNT_TRADE_MODE) != ACCOUNT_TRADE_MODE_DEMO)
     {
      LogStartup("INIT_FAILED_NOT_DEMO");
      return INIT_FAILED;
     }
   if(InpAllowedAccountLogin != 0 && AccountInfoInteger(ACCOUNT_LOGIN) != InpAllowedAccountLogin)
     {
      LogStartup("INIT_FAILED_ACCOUNT_NOT_ALLOWED");
      return INIT_FAILED;
     }
   if(!ContainsText(AccountInfoString(ACCOUNT_SERVER), InpExpectedServerMarker))
     {
      LogStartup("INIT_FAILED_SERVER_MARKER");
      return INIT_FAILED;
     }
   if(InpSignalMode == SIGNAL_EVENT_REACTION_M5 && !LoadEventReactionCalendar())
     {
      LogStartup("INIT_FAILED_EVENT_REACTION_CALENDAR");
      return INIT_FAILED;
     }
   g_atr_handle = iATR(InpTargetSymbol, PERIOD_M5, InpAtrPeriod);
   if(g_atr_handle == INVALID_HANDLE)
     {
      LogStartup("INIT_FAILED_ATR_HANDLE");
      return INIT_FAILED;
     }
   g_m5_pullback_ema_handle = iMA(InpTargetSymbol, PERIOD_M5, InpPullbackEmaPeriod, 0, MODE_EMA, PRICE_CLOSE);
   if(g_m5_pullback_ema_handle == INVALID_HANDLE)
     {
      LogStartup("INIT_FAILED_M5_PULLBACK_EMA_HANDLE");
      return INIT_FAILED;
     }
   g_m5_trend_ema_fast_handle = iMA(InpTargetSymbol, PERIOD_M5, InpM5TrendEmaFastPeriod, 0, MODE_EMA, PRICE_CLOSE);
   g_m5_trend_ema_slow_handle = iMA(InpTargetSymbol, PERIOD_M5, InpM5TrendEmaSlowPeriod, 0, MODE_EMA, PRICE_CLOSE);
   if(g_m5_trend_ema_fast_handle == INVALID_HANDLE || g_m5_trend_ema_slow_handle == INVALID_HANDLE)
     {
      LogStartup("INIT_FAILED_M5_TREND_EMA_HANDLE");
      return INIT_FAILED;
     }
   g_h1_ema_fast_handle = iMA(InpTargetSymbol, PERIOD_H1, InpH1EmaFastPeriod, 0, MODE_EMA, PRICE_CLOSE);
   g_h1_ema_slow_handle = iMA(InpTargetSymbol, PERIOD_H1, InpH1EmaSlowPeriod, 0, MODE_EMA, PRICE_CLOSE);
   if(g_h1_ema_fast_handle == INVALID_HANDLE || g_h1_ema_slow_handle == INVALID_HANDLE)
     {
      LogStartup("INIT_FAILED_H1_EMA_HANDLE");
      return INIT_FAILED;
     }
   g_h4_ema_fast_handle = iMA(InpTargetSymbol, PERIOD_H4, InpH4EmaFastPeriod, 0, MODE_EMA, PRICE_CLOSE);
   g_h4_ema_slow_handle = iMA(InpTargetSymbol, PERIOD_H4, InpH4EmaSlowPeriod, 0, MODE_EMA, PRICE_CLOSE);
   if(g_h4_ema_fast_handle == INVALID_HANDLE || g_h4_ema_slow_handle == INVALID_HANDLE)
     {
      LogStartup("INIT_FAILED_H4_EMA_HANDLE");
      return INIT_FAILED;
     }
   g_trade.SetExpertMagicNumber(InpMagicNumber);
   g_trade.SetDeviationInPoints(InpDeviationPoints);
   LogStartup("INIT_OK");
   PrintFormat("A1_M5_MOM: started run=%s magic=%I64d trading=%s", InpRunId, InpMagicNumber, BoolText(InpAllowDemoTrading));
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   if(g_atr_handle != INVALID_HANDLE)
      IndicatorRelease(g_atr_handle);
   if(g_m5_pullback_ema_handle != INVALID_HANDLE)
      IndicatorRelease(g_m5_pullback_ema_handle);
   if(g_m5_trend_ema_fast_handle != INVALID_HANDLE)
      IndicatorRelease(g_m5_trend_ema_fast_handle);
   if(g_m5_trend_ema_slow_handle != INVALID_HANDLE)
      IndicatorRelease(g_m5_trend_ema_slow_handle);
   if(g_h1_ema_fast_handle != INVALID_HANDLE)
      IndicatorRelease(g_h1_ema_fast_handle);
   if(g_h1_ema_slow_handle != INVALID_HANDLE)
      IndicatorRelease(g_h1_ema_slow_handle);
   if(g_h4_ema_fast_handle != INVALID_HANDLE)
      IndicatorRelease(g_h4_ema_fast_handle);
   if(g_h4_ema_slow_handle != INVALID_HANDLE)
      IndicatorRelease(g_h4_ema_slow_handle);
  }

void OnTick()
  {
   ManageOpenPositions();

   datetime current_m5 = iTime(InpTargetSymbol, PERIOD_M5, 0);
   if(current_m5 == 0 || current_m5 == g_last_m5_bar)
      return;
   g_last_m5_bar = current_m5;
   EvaluateCompletedM5Bar();
  }

void OnTradeTransaction(
   const MqlTradeTransaction &trans,
   const MqlTradeRequest &request,
   const MqlTradeResult &result
)
  {
   if(trans.type != TRADE_TRANSACTION_DEAL_ADD || trans.deal == 0)
      return;
   if(!HistoryDealSelect(trans.deal))
      return;
   if((long)HistoryDealGetInteger(trans.deal, DEAL_MAGIC) != InpMagicNumber ||
      HistoryDealGetString(trans.deal, DEAL_SYMBOL) != InpTargetSymbol)
      return;
   LogDealTransaction(trans.deal);

   if(!InpSplitEntryEnabled || InpSplitEntryShadowOnly || !InpSplitEntryMoveRunnerSLToBE)
      return;
   if(InpSplitEntryBreakEvenMode != 1)
      return;
   if((ENUM_DEAL_ENTRY)HistoryDealGetInteger(trans.deal, DEAL_ENTRY) != DEAL_ENTRY_OUT)
      return;
   if((ENUM_DEAL_REASON)HistoryDealGetInteger(trans.deal, DEAL_REASON) != DEAL_REASON_TP)
      return;

   const long position_id = (long)HistoryDealGetInteger(trans.deal, DEAL_POSITION_ID);
   datetime tp1_entry_time = 0;
   ENUM_POSITION_TYPE tp1_type = POSITION_TYPE_BUY;
   double tp1_entry_price = 0.0;
   if(!FindSplitTp1EntryDeal(position_id, tp1_entry_time, tp1_type, tp1_entry_price))
      return;

   MoveMatchingSplitRunnerToBreakEvenOnTp1(tp1_entry_time, tp1_type, tp1_entry_price);
  }

double EffectiveInitialTargetR()
  {
   if(InpPartialCloseEnabled && !InpPartialCloseShadowOnly && InpRunnerTargetR > InpPartialTriggerR)
      return InpRunnerTargetR;
   return InpRiskReward;
  }

double NormalizePartialCloseLots(const double current_volume)
  {
   if(current_volume <= 0.0 || InpPartialFraction <= 0.0 || InpPartialFraction >= 1.0)
      return 0.0;

   const double min_lots = SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_MIN);
   const double step = SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_STEP);
   if(min_lots <= 0.0 || step <= 0.0)
      return 0.0;

   double close_volume = MathFloor((current_volume * InpPartialFraction) / step + 0.0000001) * step;
   const double max_close_volume = current_volume - min_lots;
   if(close_volume > max_close_volume)
      close_volume = MathFloor(max_close_volume / step + 0.0000001) * step;

   close_volume = NormalizeDouble(close_volume, 2);
   const double remaining_volume = NormalizeDouble(current_volume - close_volume, 2);
   if(close_volume < min_lots || remaining_volume < min_lots || close_volume >= current_volume)
      return 0.0;
   return close_volume;
  }

string PartialStateKey(const ulong position_ticket)
  {
   return StringFormat("A1MOM_PC_%I64d_%I64u", InpMagicNumber, position_ticket);
  }

string SplitRunnerStateKey(const ulong position_ticket)
  {
   return StringFormat("A1MOM_SPLIT_BE_%I64d_%I64u", InpMagicNumber, position_ticket);
  }

bool TextContains(const string value, const string needle)
  {
   return StringFind(value, needle) >= 0;
  }

string GlobalKeyToken(string value, const int max_len)
  {
   StringReplace(value, " ", "_");
   StringReplace(value, ".", "_");
   StringReplace(value, "-", "_");
   StringReplace(value, "/", "_");
   StringReplace(value, "\\", "_");
   StringReplace(value, ":", "_");
   if(StringLen(value) <= 0)
      value = "NA";
   if(max_len > 0 && StringLen(value) > max_len)
      value = StringSubstr(value, 0, max_len);
   return value;
  }

string SignalClaimDirectionCode(const string direction)
  {
   if(direction == "LONG")
      return "L";
   if(direction == "SHORT")
      return "S";
   return "N";
  }

string SignalClaimKey(const string direction, const datetime signal_time, const int priority)
  {
   const string ns = GlobalKeyToken(InpSignalClaimNamespace, 14);
   const string sym = GlobalKeyToken(InpTargetSymbol, 12);
   return StringFormat("%s_%I64d_%s_%s_%I64d_P%d",
                       ns,
                       AccountInfoInteger(ACCOUNT_LOGIN),
                       sym,
                       SignalClaimDirectionCode(direction),
                       (long)signal_time,
                       priority);
  }

bool HigherPrioritySignalClaimExists(const string direction, const datetime signal_time)
  {
   if(!InpSignalClaimEnabled || InpSignalClaimPriority <= 1)
      return false;

   const int window_minutes = MathMax(0, MathMin(10, InpSignalClaimWindowMinutes));
   for(int priority = 1; priority < InpSignalClaimPriority; priority++)
     {
      for(int offset = -window_minutes; offset <= window_minutes; offset++)
        {
         const datetime candidate_time = signal_time + offset * 60;
         if(GlobalVariableCheck(SignalClaimKey(direction, candidate_time, priority)))
            return true;
        }
     }
   return false;
  }

bool ClaimSignalSlot(
   const string direction,
   const datetime signal_time,
   const double bid,
   const double ask,
   const long spread_points,
   const double entry_reference,
   const double stop_points,
   const double estimated_cost_r
)
  {
   if(!InpSignalClaimEnabled)
      return true;

   if(InpSignalClaimPriority <= 0)
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, entry_reference, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "signal_claim_invalid_priority");
      return false;
     }

   if(InpSignalClaimPriority > 1 && InpSignalClaimGraceSeconds > 0)
     {
      const int wait_seconds = MathMax(0, MathMin(10, InpSignalClaimGraceSeconds));
      if(wait_seconds > 0)
         Sleep(wait_seconds * 1000);
     }

   if(HigherPrioritySignalClaimExists(direction, signal_time))
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, entry_reference, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "signal_claimed_by_higher_priority");
      return false;
     }

   const string key = SignalClaimKey(direction, signal_time, InpSignalClaimPriority);
   const double claim_value = (double)TimeCurrent();
   ResetLastError();
   if(!GlobalVariableCheck(key))
      GlobalVariableSet(key, 0.0);
   if(!GlobalVariableSetOnCondition(key, claim_value, 0.0))
     {
      if(GlobalVariableCheck(key) && GlobalVariableGet(key) > 0.0)
        {
         LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, entry_reference, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "signal_claim_slot_already_claimed");
         return false;
        }
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, entry_reference, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "signal_claim_set_failed");
      return false;
     }
   GlobalVariablesFlush();

   if(HigherPrioritySignalClaimExists(direction, signal_time))
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, entry_reference, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "signal_claimed_by_higher_priority_after_claim");
      return false;
     }

   LogOrder("SIGNAL_CLAIM_OK", direction, 0.0, bid, ask, spread_points, entry_reference, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, SignalClaimKey(direction, signal_time, InpSignalClaimPriority));
   return true;
  }

bool IsPartialCloseAlreadyDone(const ulong position_ticket, const double entry_price, const double current_sl, const ENUM_POSITION_TYPE type, const double point)
  {
   if(GlobalVariableCheck(PartialStateKey(position_ticket)))
      return true;
   if(!InpMoveSLToBEOnPartial || current_sl <= 0.0 || point <= 0.0)
      return false;
   if(type == POSITION_TYPE_BUY && current_sl >= entry_price - 0.1 * point)
      return true;
   if(type == POSITION_TYPE_SELL && current_sl <= entry_price + 0.1 * point)
      return true;
   return false;
  }

bool CalculateSplitEntryLots(const double total_lots, double &first_lots, double &runner_lots, string &reason)
  {
   first_lots = 0.0;
   runner_lots = 0.0;
   reason = "pass";

   const double min_lots = SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_MIN);
   const double step = SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_STEP);
   if(min_lots <= 0.0 || step <= 0.0 || total_lots <= 0.0)
     {
      reason = "invalid_symbol_volume";
      return false;
     }

   double first_fraction = InpSplitEntryFirstLotFraction;
   if(first_fraction < 0.01)
      first_fraction = 0.01;
   if(first_fraction > 0.99)
      first_fraction = 0.99;

   if(total_lots >= 2.0 * min_lots)
     {
      first_lots = MathFloor((total_lots * first_fraction) / step + 0.0000001) * step;
      if(first_lots < min_lots)
         first_lots = min_lots;
      runner_lots = NormalizeDouble(total_lots - first_lots, 2);
      if(runner_lots < min_lots)
        {
         runner_lots = min_lots;
         first_lots = NormalizeDouble(total_lots - runner_lots, 2);
        }
      first_lots = NormalizeDouble(first_lots, 2);
      if(first_lots >= min_lots && runner_lots >= min_lots)
         return true;
     }

   if(InpSplitEntryUseMinLotPair)
     {
      if(first_fraction < 0.45)
        {
         first_lots = NormalizeDouble(min_lots, 2);
         runner_lots = NormalizeDouble(2.0 * min_lots, 2);
         reason = "min_lot_fraction_pair_1_to_2";
        }
      else if(first_fraction > 0.55)
        {
         first_lots = NormalizeDouble(2.0 * min_lots, 2);
         runner_lots = NormalizeDouble(min_lots, 2);
         reason = "min_lot_fraction_pair_2_to_1";
        }
      else
        {
         first_lots = NormalizeDouble(min_lots, 2);
         runner_lots = NormalizeDouble(min_lots, 2);
         reason = "min_lot_pair_doubles_small_position";
        }
      return true;
     }

   reason = "split_lots_too_small";
   return false;
  }

bool ModifyPositionStops(const ulong ticket, const double new_sl, const double new_tp, long &retcode)
  {
   MqlTradeRequest request = {};
   MqlTradeResult result = {};
   request.action = TRADE_ACTION_SLTP;
   request.position = ticket;
   request.symbol = InpTargetSymbol;
   request.sl = new_sl;
   request.tp = new_tp;
   request.magic = InpMagicNumber;
   const bool sent = OrderSend(request, result);
   retcode = (long)result.retcode;
   return sent && (result.retcode == TRADE_RETCODE_DONE || result.retcode == TRADE_RETCODE_PLACED);
  }

bool SendPartialClose(const ulong ticket, const ENUM_POSITION_TYPE type, const double close_volume, const double bid, const double ask, long &retcode)
  {
   MqlTradeRequest request = {};
   MqlTradeResult result = {};
   request.action = TRADE_ACTION_DEAL;
   request.position = ticket;
   request.symbol = InpTargetSymbol;
   request.volume = close_volume;
   request.magic = InpMagicNumber;
   request.deviation = InpDeviationPoints;
   request.comment = InpOrderComment + "_PARTIAL";
   if(type == POSITION_TYPE_BUY)
     {
      request.type = ORDER_TYPE_SELL;
      request.price = bid;
     }
   else
     {
      request.type = ORDER_TYPE_BUY;
      request.price = ask;
     }
   const bool sent = OrderSend(request, result);
   retcode = (long)result.retcode;
   return sent && (result.retcode == TRADE_RETCODE_DONE || result.retcode == TRADE_RETCODE_PLACED);
  }

bool SendManagedClose(const ulong ticket, const ENUM_POSITION_TYPE type, const double close_volume, const double bid, const double ask, const string suffix, long &retcode)
  {
   MqlTradeRequest request = {};
   MqlTradeResult result = {};
   request.action = TRADE_ACTION_DEAL;
   request.position = ticket;
   request.symbol = InpTargetSymbol;
   request.volume = close_volume;
   request.magic = InpMagicNumber;
   request.deviation = InpDeviationPoints;
   request.comment = InpOrderComment + suffix;
   if(type == POSITION_TYPE_BUY)
     {
      request.type = ORDER_TYPE_SELL;
      request.price = bid;
     }
   else
     {
      request.type = ORDER_TYPE_BUY;
      request.price = ask;
     }
   const bool sent = OrderSend(request, result);
   retcode = (long)result.retcode;
   return sent && (result.retcode == TRADE_RETCODE_DONE || result.retcode == TRADE_RETCODE_PLACED);
  }

bool FindSplitTp1EntryDeal(
   const long position_id,
   datetime &entry_time,
   ENUM_POSITION_TYPE &entry_type,
   double &entry_price
)
  {
   entry_time = 0;
   entry_price = 0.0;
   const datetime now = TimeCurrent();
   if(!HistorySelect(now - 366 * 86400, now + 60))
      return false;

   const int total = HistoryDealsTotal();
   for(int i = total - 1; i >= 0; i--)
     {
      const ulong deal_ticket = HistoryDealGetTicket(i);
      if(deal_ticket == 0)
         continue;
      if((long)HistoryDealGetInteger(deal_ticket, DEAL_POSITION_ID) != position_id)
         continue;
      if((long)HistoryDealGetInteger(deal_ticket, DEAL_MAGIC) != InpMagicNumber ||
         HistoryDealGetString(deal_ticket, DEAL_SYMBOL) != InpTargetSymbol)
         continue;
      if((ENUM_DEAL_ENTRY)HistoryDealGetInteger(deal_ticket, DEAL_ENTRY) != DEAL_ENTRY_IN)
         continue;

      const string comment = HistoryDealGetString(deal_ticket, DEAL_COMMENT);
      if(!TextContains(comment, "_TP1"))
         continue;

      const ENUM_DEAL_TYPE deal_type = (ENUM_DEAL_TYPE)HistoryDealGetInteger(deal_ticket, DEAL_TYPE);
      if(deal_type == DEAL_TYPE_BUY)
         entry_type = POSITION_TYPE_BUY;
      else if(deal_type == DEAL_TYPE_SELL)
         entry_type = POSITION_TYPE_SELL;
      else
         continue;

      entry_time = (datetime)HistoryDealGetInteger(deal_ticket, DEAL_TIME);
      entry_price = HistoryDealGetDouble(deal_ticket, DEAL_PRICE);
      return entry_time > 0 && entry_price > 0.0;
     }

   return false;
  }

void MoveMatchingSplitRunnerToBreakEvenOnTp1(
   const datetime tp1_entry_time,
   const ENUM_POSITION_TYPE tp1_type,
   const double tp1_entry_price
)
  {
   const double point = SymbolInfoDouble(InpTargetSymbol, SYMBOL_POINT);
   const int digits = (int)SymbolInfoInteger(InpTargetSymbol, SYMBOL_DIGITS);
   const double bid = SymbolInfoDouble(InpTargetSymbol, SYMBOL_BID);
   const double ask = SymbolInfoDouble(InpTargetSymbol, SYMBOL_ASK);
   if(tp1_entry_time <= 0 || point <= 0.0 || bid <= 0.0 || ask <= 0.0)
      return;

   ulong best_ticket = 0;
   long best_time_delta = 999999;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      const ulong ticket = PositionGetTicket(i);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber ||
         PositionGetString(POSITION_SYMBOL) != InpTargetSymbol)
         continue;
      if((ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE) != tp1_type)
         continue;
      if(!TextContains(PositionGetString(POSITION_COMMENT), "_RUN"))
         continue;

      const datetime runner_entry_time = (datetime)PositionGetInteger(POSITION_TIME);
      const long time_delta = (long)MathAbs((double)((long)runner_entry_time - (long)tp1_entry_time));
      if(time_delta <= 120 && time_delta < best_time_delta)
        {
         best_time_delta = time_delta;
         best_ticket = ticket;
        }
     }

   const string direction = (tp1_type == POSITION_TYPE_BUY) ? "LONG" : "SHORT";
   if(best_ticket == 0 || !PositionSelectByTicket(best_ticket))
     {
      LogManagement("SPLIT_RUNNER_BE_ON_TP1_NO_MATCH", direction, 0, 0.0, tp1_entry_price, tp1_entry_price, 0.0, tp1_entry_price, 0.0, 0.0, 0.0, 0, "runner_not_found_after_tp1", InpSplitEntryFirstTargetR, InpSplitEntryRunnerTargetR);
      return;
     }

   const double runner_entry = PositionGetDouble(POSITION_PRICE_OPEN);
   const double current_sl = PositionGetDouble(POSITION_SL);
   const double tp = PositionGetDouble(POSITION_TP);
   const double volume = PositionGetDouble(POSITION_VOLUME);
   const double current_price = (tp1_type == POSITION_TYPE_BUY) ? bid : ask;
   const double risk = (tp1_type == POSITION_TYPE_BUY) ? runner_entry - current_sl : current_sl - runner_entry;
   const double move = (tp1_type == POSITION_TYPE_BUY) ? current_price - runner_entry : runner_entry - current_price;
   const double unrealized_r = (risk > 0.0) ? move / risk : 0.0;
   const double risk_points = (risk > 0.0) ? risk / point : 0.0;
   const double break_even_sl = NormalizeDouble(runner_entry, digits);

   bool already_at_be = false;
   if(tp1_type == POSITION_TYPE_BUY && current_sl >= break_even_sl - 0.1 * point)
      already_at_be = true;
   if(tp1_type == POSITION_TYPE_SELL && current_sl <= break_even_sl + 0.1 * point)
      already_at_be = true;

   if(already_at_be)
     {
      GlobalVariableSet(SplitRunnerStateKey(best_ticket), 1.0);
      LogManagement("SPLIT_RUNNER_BE_ON_TP1_ALREADY_BE", direction, best_ticket, volume, runner_entry, current_price, current_sl, break_even_sl, tp, risk_points, unrealized_r, 0, "pass", InpSplitEntryFirstTargetR, InpSplitEntryRunnerTargetR);
      return;
     }

   long retcode = 0;
   const bool modify_ok = ModifyPositionStops(best_ticket, break_even_sl, tp, retcode);
   if(modify_ok)
      GlobalVariableSet(SplitRunnerStateKey(best_ticket), 1.0);
   LogManagement(modify_ok ? "SPLIT_RUNNER_BE_ON_TP1_MODIFY_OK" : "SPLIT_RUNNER_BE_ON_TP1_MODIFY_FAIL", direction, best_ticket, volume, runner_entry, current_price, current_sl, break_even_sl, tp, risk_points, unrealized_r, retcode, modify_ok ? "pass" : "split_runner_be_on_tp1_failed", InpSplitEntryFirstTargetR, InpSplitEntryRunnerTargetR);
  }

void ManageOpenPositions()
  {
   if(!InpProfitProtectionEnabled && !InpPartialCloseEnabled && !InpSplitEntryEnabled && !InpEarlyAdverseExitEnabled)
      return;

   const double point = SymbolInfoDouble(InpTargetSymbol, SYMBOL_POINT);
   const int digits = (int)SymbolInfoInteger(InpTargetSymbol, SYMBOL_DIGITS);
   const double bid = SymbolInfoDouble(InpTargetSymbol, SYMBOL_BID);
   const double ask = SymbolInfoDouble(InpTargetSymbol, SYMBOL_ASK);
   if(point <= 0.0 || bid <= 0.0 || ask <= 0.0)
      return;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      const ulong ticket = PositionGetTicket(i);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber ||
         PositionGetString(POSITION_SYMBOL) != InpTargetSymbol)
         continue;

      const ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      const double entry_price = PositionGetDouble(POSITION_PRICE_OPEN);
      const double current_sl = PositionGetDouble(POSITION_SL);
      const double tp = PositionGetDouble(POSITION_TP);
      const double volume = PositionGetDouble(POSITION_VOLUME);
      if(entry_price <= 0.0 || current_sl <= 0.0)
         continue;

      string direction = "";
      double current_price = 0.0;
      double risk = 0.0;
      double move = 0.0;
      double new_sl = 0.0;

      if(type == POSITION_TYPE_BUY)
        {
         direction = "LONG";
         current_price = bid;
         risk = entry_price - current_sl;
         move = current_price - entry_price;
         new_sl = NormalizeDouble(entry_price + InpProfitProtectionLockR * risk, digits);
         if(current_sl >= new_sl - 0.1 * point)
            continue;
        }
      else if(type == POSITION_TYPE_SELL)
        {
         direction = "SHORT";
         current_price = ask;
         risk = current_sl - entry_price;
         move = entry_price - current_price;
         new_sl = NormalizeDouble(entry_price - InpProfitProtectionLockR * risk, digits);
         if(current_sl > 0.0 && current_sl <= new_sl + 0.1 * point)
            continue;
        }
      else
         continue;

      if(risk <= 0.0)
         continue;

      const double unrealized_r = move / risk;
      const double risk_points = risk / point;
      const string position_comment = PositionGetString(POSITION_COMMENT);
      const datetime position_time = (datetime)PositionGetInteger(POSITION_TIME);
      const double age_minutes = (position_time > 0) ? ((double)(TimeCurrent() - position_time) / 60.0) : 0.0;
      double split_break_even_trigger_r = 0.0;
      if(InpSplitEntryBreakEvenMode == 2)
         split_break_even_trigger_r = 1.0;

      if(InpEarlyAdverseExitEnabled &&
         InpEarlyAdverseExitAfterMinutes >= 0 &&
         InpEarlyAdverseExitR > 0.0 &&
         age_minutes >= (double)InpEarlyAdverseExitAfterMinutes &&
         unrealized_r <= -InpEarlyAdverseExitR)
        {
         if(InpEarlyAdverseExitShadowOnly)
           {
            LogManagement("EARLY_ADVERSE_EXIT_SHADOW", direction, ticket, volume, entry_price, current_price, current_sl, current_sl, tp, risk_points, unrealized_r, 0, "shadow_only", InpEarlyAdverseExitR, age_minutes);
           }
         else
           {
            long early_close_retcode = 0;
            const bool close_ok = SendManagedClose(ticket, type, volume, bid, ask, "_EARLY", early_close_retcode);
            LogManagement(close_ok ? "EARLY_ADVERSE_EXIT_OK" : "EARLY_ADVERSE_EXIT_FAIL", direction, ticket, volume, entry_price, current_price, current_sl, current_sl, tp, risk_points, unrealized_r, early_close_retcode, close_ok ? "pass" : "early_adverse_close_failed", InpEarlyAdverseExitR, age_minutes);
            if(close_ok)
               continue;
           }
        }

      if(InpSplitEntryEnabled && !InpSplitEntryShadowOnly && InpSplitEntryMoveRunnerSLToBE &&
         InpSplitEntryBreakEvenMode == 2 &&
         TextContains(position_comment, "_RUN") && unrealized_r >= split_break_even_trigger_r &&
         !GlobalVariableCheck(SplitRunnerStateKey(ticket)))
        {
         const double break_even_sl = NormalizeDouble(entry_price, digits);
         bool already_at_be = false;
         if(type == POSITION_TYPE_BUY && current_sl >= break_even_sl - 0.1 * point)
            already_at_be = true;
         if(type == POSITION_TYPE_SELL && current_sl <= break_even_sl + 0.1 * point)
            already_at_be = true;

         if(already_at_be)
           {
            GlobalVariableSet(SplitRunnerStateKey(ticket), 1.0);
           }
         else
           {
            long split_be_retcode = 0;
            const bool split_be_ok = ModifyPositionStops(ticket, break_even_sl, tp, split_be_retcode);
            if(split_be_ok)
               GlobalVariableSet(SplitRunnerStateKey(ticket), 1.0);
            LogManagement(split_be_ok ? "SPLIT_RUNNER_BE_MODIFY_OK" : "SPLIT_RUNNER_BE_MODIFY_FAIL", direction, ticket, volume, entry_price, current_price, current_sl, break_even_sl, tp, risk_points, unrealized_r, split_be_retcode, split_be_ok ? "pass" : "split_runner_be_failed", split_break_even_trigger_r, InpSplitEntryRunnerTargetR);
           }
        }

      if(InpPartialCloseEnabled && unrealized_r >= InpPartialTriggerR)
        {
         const double runner_tp = type == POSITION_TYPE_BUY
                                  ? NormalizeDouble(entry_price + InpRunnerTargetR * risk, digits)
                                  : NormalizeDouble(entry_price - InpRunnerTargetR * risk, digits);
         const double break_even_sl = NormalizeDouble(entry_price, digits);
         if(IsPartialCloseAlreadyDone(ticket, entry_price, current_sl, type, point))
           {
            continue;
           }
         else if(InpPartialCloseShadowOnly)
           {
            LogManagement("PARTIAL_CLOSE_SHADOW", direction, ticket, volume, entry_price, current_price, current_sl, break_even_sl, runner_tp, risk_points, unrealized_r, 0, "shadow_only", InpPartialTriggerR, InpRunnerTargetR);
            GlobalVariableSet(PartialStateKey(ticket), 1.0);
           }
         else
           {
            const double partial_volume = NormalizePartialCloseLots(volume);
            if(partial_volume <= 0.0)
              {
               LogManagement("PARTIAL_CLOSE_SKIPPED", direction, ticket, volume, entry_price, current_price, current_sl, break_even_sl, runner_tp, risk_points, unrealized_r, 0, "volume_too_small_for_partial", InpPartialTriggerR, InpRunnerTargetR);
               GlobalVariableSet(PartialStateKey(ticket), 1.0);
              }
            else
              {
               long close_retcode = 0;
               const bool close_ok = SendPartialClose(ticket, type, partial_volume, bid, ask, close_retcode);
               if(close_ok)
                  GlobalVariableSet(PartialStateKey(ticket), 1.0);
               LogManagement(close_ok ? "PARTIAL_CLOSE_OK" : "PARTIAL_CLOSE_FAIL", direction, ticket, partial_volume, entry_price, current_price, current_sl, break_even_sl, runner_tp, risk_points, unrealized_r, close_retcode, close_ok ? "pass" : "partial_close_failed", InpPartialTriggerR, InpRunnerTargetR);

               if(close_ok && InpMoveSLToBEOnPartial)
                 {
                  long modify_retcode = 0;
                  const bool modify_ok = ModifyPositionStops(ticket, break_even_sl, runner_tp, modify_retcode);
                  LogManagement(modify_ok ? "PARTIAL_BE_RUNNER_MODIFY_OK" : "PARTIAL_BE_RUNNER_MODIFY_FAIL", direction, ticket, volume - partial_volume, entry_price, current_price, current_sl, break_even_sl, runner_tp, risk_points, unrealized_r, modify_retcode, modify_ok ? "pass" : "modify_after_partial_failed", InpPartialTriggerR, InpRunnerTargetR);
                 }
               continue;
              }
           }
        }

      if(!InpProfitProtectionEnabled)
         continue;

      if(unrealized_r < InpProfitProtectionTriggerR)
         continue;

      if(InpProfitProtectionShadowOnly)
        {
         LogManagement("PROFIT_LOCK_SHADOW", direction, ticket, volume, entry_price, current_price, current_sl, new_sl, tp, risk_points, unrealized_r, 0, "shadow_only");
         continue;
        }

      MqlTradeRequest request = {};
      MqlTradeResult result = {};
      request.action = TRADE_ACTION_SLTP;
      request.position = ticket;
      request.symbol = InpTargetSymbol;
      request.sl = new_sl;
      request.tp = tp;
      request.magic = InpMagicNumber;

      const bool sent = OrderSend(request, result);
      LogManagement(
         sent ? "PROFIT_LOCK_MODIFY_OK" : "PROFIT_LOCK_MODIFY_FAIL",
         direction,
         ticket,
         volume,
         entry_price,
         current_price,
         current_sl,
         new_sl,
         tp,
         risk_points,
         unrealized_r,
         (long)result.retcode,
         sent ? "pass" : "modify_failed"
      );
     }
  }

void ResetDailyCounterIfNeeded()
  {
   string today = TimeToString(TimeCurrent(), TIME_DATE);
   if(today != g_trade_day)
     {
      g_trade_day = today;
      g_trades_today = 0;
     }
  }

bool KillSwitchPresent()
  {
   return FileIsExist(InpKillSwitchFileName);
  }

datetime CurrentBrokerDayStart()
  {
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   dt.hour = 0;
   dt.min = 0;
   dt.sec = 0;
   return StructToTime(dt);
  }

bool PortfolioGuardTracksMagic(const long magic)
  {
   string csv = InpPortfolioGuardMagicCsv;
   StringReplace(csv, " ", "");
   if(csv == "")
      return magic == InpMagicNumber;
   string wrapped = "," + csv + ",";
   string needle = "," + IntegerToString(magic) + ",";
   return StringFind(wrapped, needle) >= 0;
  }

int PortfolioEntriesToday()
  {
   if(!InpPortfolioDailyGuardEnabled)
      return 0;
   datetime start_time = CurrentBrokerDayStart();
   if(!HistorySelect(start_time, TimeCurrent()))
      return 0;
   int count = 0;
   const int total = HistoryDealsTotal();
   for(int i = 0; i < total; i++)
     {
      ulong ticket = HistoryDealGetTicket(i);
      if(ticket == 0)
         continue;
      if(HistoryDealGetString(ticket, DEAL_SYMBOL) != InpTargetSymbol)
         continue;
      long magic = (long)HistoryDealGetInteger(ticket, DEAL_MAGIC);
      if(!PortfolioGuardTracksMagic(magic))
         continue;
      long entry = (long)HistoryDealGetInteger(ticket, DEAL_ENTRY);
      if(entry == DEAL_ENTRY_IN || entry == DEAL_ENTRY_INOUT)
         count++;
     }
   return count;
  }

double PortfolioClosedPnlToday()
  {
   if(!InpPortfolioDailyGuardEnabled)
      return 0.0;
   datetime start_time = CurrentBrokerDayStart();
   if(!HistorySelect(start_time, TimeCurrent()))
      return 0.0;
   double pnl = 0.0;
   const int total = HistoryDealsTotal();
   for(int i = 0; i < total; i++)
     {
      ulong ticket = HistoryDealGetTicket(i);
      if(ticket == 0)
         continue;
      if(HistoryDealGetString(ticket, DEAL_SYMBOL) != InpTargetSymbol)
         continue;
      long magic = (long)HistoryDealGetInteger(ticket, DEAL_MAGIC);
      if(!PortfolioGuardTracksMagic(magic))
         continue;
      pnl += HistoryDealGetDouble(ticket, DEAL_PROFIT);
      pnl += HistoryDealGetDouble(ticket, DEAL_SWAP);
      pnl += HistoryDealGetDouble(ticket, DEAL_COMMISSION);
     }
   return pnl;
  }

datetime LastPortfolioLosingExitTimeToday()
  {
   if(!InpPortfolioDailyGuardEnabled)
      return 0;
   datetime start_time = CurrentBrokerDayStart();
   if(!HistorySelect(start_time, TimeCurrent()))
      return 0;
   datetime latest_loss_time = 0;
   const int total = HistoryDealsTotal();
   for(int i = 0; i < total; i++)
     {
      ulong ticket = HistoryDealGetTicket(i);
      if(ticket == 0)
         continue;
      if(HistoryDealGetString(ticket, DEAL_SYMBOL) != InpTargetSymbol)
         continue;
      long magic = (long)HistoryDealGetInteger(ticket, DEAL_MAGIC);
      if(!PortfolioGuardTracksMagic(magic))
         continue;
      long entry = (long)HistoryDealGetInteger(ticket, DEAL_ENTRY);
      if(entry != DEAL_ENTRY_OUT && entry != DEAL_ENTRY_INOUT && entry != DEAL_ENTRY_OUT_BY)
         continue;
      double pnl = HistoryDealGetDouble(ticket, DEAL_PROFIT);
      pnl += HistoryDealGetDouble(ticket, DEAL_SWAP);
      pnl += HistoryDealGetDouble(ticket, DEAL_COMMISSION);
      if(pnl >= 0.0)
         continue;
      datetime deal_time = (datetime)HistoryDealGetInteger(ticket, DEAL_TIME);
      if(deal_time > latest_loss_time)
         latest_loss_time = deal_time;
     }
   return latest_loss_time;
  }

int CountOwnOpenPositions()
  {
   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetInteger(POSITION_MAGIC) == InpMagicNumber &&
         PositionGetString(POSITION_SYMBOL) == InpTargetSymbol)
         count++;
     }
   return count;
  }

double NormalizeLotsForSymbol(const double requested_lots)
  {
   const double min_lots = SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_MIN);
   const double max_lots_symbol = SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_MAX);
   const double step = SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_STEP);
   double max_lots = max_lots_symbol;
   if(InpMaxRiskLots > 0.0)
      max_lots = MathMin(max_lots_symbol, InpMaxRiskLots);
   double lots = requested_lots;
   if(min_lots > 0.0)
      lots = MathMax(min_lots, lots);
   if(max_lots > 0.0)
      lots = MathMin(max_lots, lots);
   if(step > 0.0)
      lots = MathFloor(lots / step + 0.0000001) * step;
   return NormalizeDouble(lots, 2);
  }

double LotsForStopDistance(const double stop_distance)
  {
   const double fixed_lots = NormalizeLotsForSymbol(InpFixedLots);
   if(!InpUseRiskNormalizedLots || InpRiskAmountUsd <= 0.0)
      return fixed_lots;
   const double tick_size = SymbolInfoDouble(InpTargetSymbol, SYMBOL_TRADE_TICK_SIZE);
   double tick_value_loss = SymbolInfoDouble(InpTargetSymbol, SYMBOL_TRADE_TICK_VALUE_LOSS);
   if(tick_value_loss <= 0.0)
      tick_value_loss = SymbolInfoDouble(InpTargetSymbol, SYMBOL_TRADE_TICK_VALUE);
   if(tick_size <= 0.0 || tick_value_loss <= 0.0 || stop_distance <= 0.0)
      return fixed_lots;
   const double risk_per_lot = (stop_distance / tick_size) * tick_value_loss;
   if(risk_per_lot <= 0.0)
      return fixed_lots;
   return NormalizeLotsForSymbol(InpRiskAmountUsd / risk_per_lot);
  }

double RecentHigh(const int start_shift, const int count)
  {
   double value = 0.0;
   for(int i = 0; i < count; i++)
     {
      double high = iHigh(InpTargetSymbol, PERIOD_M5, start_shift + i);
      if(high <= 0.0)
         return 0.0;
      if(value == 0.0 || high > value)
         value = high;
     }
   return value;
  }

double RecentLow(const int start_shift, const int count)
  {
   double value = 0.0;
   for(int i = 0; i < count; i++)
     {
      double low = iLow(InpTargetSymbol, PERIOD_M5, start_shift + i);
      if(low <= 0.0)
         return 0.0;
      if(value == 0.0 || low < value)
         value = low;
     }
   return value;
  }

double RecentRangeHigh(const int start_shift, const int count)
  {
   return RecentHigh(start_shift, count);
  }

double RecentRangeLow(const int start_shift, const int count)
  {
   return RecentLow(start_shift, count);
  }

bool OpeningRangeForSignal(
   const datetime signal_time,
   double &range_high,
   double &range_low
)
  {
   range_high = 0.0;
   range_low = 0.0;

   MqlDateTime parts;
   TimeToStruct(signal_time, parts);
   parts.hour = MathMax(0, MathMin(23, InpOpeningRangeStartHour));
   parts.min = 0;
   parts.sec = 0;
   const datetime range_start = StructToTime(parts);
   const datetime range_end = range_start + MathMax(5, InpOpeningRangeMinutes) * 60;
   const datetime trade_end = range_end + MathMax(1, InpOpeningTradeWindowHours) * 3600;

   if(signal_time < range_end || signal_time > trade_end)
      return false;

   const int bars = iBars(InpTargetSymbol, PERIOD_M5);
   int found = 0;
   for(int shift = 1; shift < bars && shift < 600; shift++)
     {
      const datetime bar_time = iTime(InpTargetSymbol, PERIOD_M5, shift);
      if(bar_time == 0)
         break;
      if(bar_time >= signal_time)
         continue;
      if(bar_time < range_start)
         break;
      if(bar_time >= range_start && bar_time < range_end)
        {
         const double bar_high = iHigh(InpTargetSymbol, PERIOD_M5, shift);
         const double bar_low = iLow(InpTargetSymbol, PERIOD_M5, shift);
         if(bar_high <= 0.0 || bar_low <= 0.0)
            continue;
         if(found == 0)
           {
            range_high = bar_high;
            range_low = bar_low;
           }
         else
           {
            range_high = MathMax(range_high, bar_high);
            range_low = MathMin(range_low, bar_low);
           }
         found++;
        }
     }
   return found >= MathMax(1, InpOpeningRangeMinutes / 5) && range_high > range_low;
  }

bool EventReactionRangeForSignal(
   const datetime event_time,
   const int impulse_minutes_input,
   const datetime signal_time,
   double &range_high,
   double &range_low
)
  {
   range_high = 0.0;
   range_low = 0.0;

   const int impulse_minutes = MathMax(5, impulse_minutes_input);
   const datetime range_start = event_time;
   const datetime range_end = range_start + impulse_minutes * 60;
   if(signal_time < range_end)
      return false;

   const int bars = iBars(InpTargetSymbol, PERIOD_M5);
   const int min_bars = MathMax(1, (impulse_minutes + 4) / 5);
   int found = 0;
   for(int shift = 1; shift < bars && shift < 240; shift++)
     {
      const datetime bar_time = iTime(InpTargetSymbol, PERIOD_M5, shift);
      if(bar_time == 0)
         break;
      if(bar_time >= signal_time)
         continue;
      if(bar_time < range_start)
         break;
      if(bar_time >= range_start && bar_time < range_end)
        {
         const double bar_high = iHigh(InpTargetSymbol, PERIOD_M5, shift);
         const double bar_low = iLow(InpTargetSymbol, PERIOD_M5, shift);
         if(bar_high <= 0.0 || bar_low <= 0.0)
            continue;
         if(found == 0)
           {
            range_high = bar_high;
            range_low = bar_low;
           }
         else
           {
            range_high = MathMax(range_high, bar_high);
            range_low = MathMin(range_low, bar_low);
           }
         found++;
        }
     }
   return found >= min_bars && range_high > range_low;
  }

bool ReadAtr(double &atr)
  {
   double buffer[1];
   if(CopyBuffer(g_atr_handle, 0, 1, 1, buffer) != 1)
      return false;
   atr = buffer[0];
   return atr > 0.0;
  }

bool DirectionModeAllows(const string direction)
  {
   if(InpDirectionMode == MOMENTUM_BOTH_DIRECTIONS)
      return true;
   if(InpDirectionMode == MOMENTUM_LONG_ONLY && direction == "LONG")
      return true;
   if(InpDirectionMode == MOMENTUM_SHORT_ONLY && direction == "SHORT")
      return true;
   return false;
  }

bool H1TrendAllows(const string direction)
  {
   if(!InpUseH1TrendFilter)
      return true;
   if(direction == "LONG" && !InpH1TrendApplyToLong)
      return true;
   if(direction == "SHORT" && !InpH1TrendApplyToShort)
      return true;
   return TrendAllows(
      direction,
      PERIOD_H1,
      g_h1_ema_fast_handle,
      g_h1_ema_slow_handle,
      InpH1TrendSlopeBars,
      InpH1TrendMinSlopePoints
   );
  }

bool H4TrendAllows(const string direction)
  {
   if(!InpUseH4TrendFilter)
      return true;
   if(direction == "LONG" && !InpH4TrendApplyToLong)
      return true;
   if(direction == "SHORT" && !InpH4TrendApplyToShort)
      return true;
   return TrendAllows(
      direction,
      PERIOD_H4,
      g_h4_ema_fast_handle,
      g_h4_ema_slow_handle,
      InpH4TrendSlopeBars,
      InpH4TrendMinSlopePoints
   );
  }

bool TrendAllows(
   const string direction,
   const ENUM_TIMEFRAMES timeframe,
   const int fast_handle,
   const int slow_handle,
   const int slope_bars_input,
   const int min_slope_points
)
  {
   const int slope_bars = MathMax(1, slope_bars_input);
   double fast_now[1];
   double fast_prior[1];
   double slow_now[1];
   if(CopyBuffer(fast_handle, 0, 1, 1, fast_now) != 1)
      return false;
   if(CopyBuffer(fast_handle, 0, 1 + slope_bars, 1, fast_prior) != 1)
      return false;
   if(CopyBuffer(slow_handle, 0, 1, 1, slow_now) != 1)
      return false;

   const double htf_close = iClose(InpTargetSymbol, timeframe, 1);
   const double point = SymbolInfoDouble(InpTargetSymbol, SYMBOL_POINT);
   if(htf_close <= 0.0 || point <= 0.0)
      return false;

   const double slope_points = (fast_now[0] - fast_prior[0]) / point;
   if(direction == "LONG")
      return htf_close > fast_now[0] &&
             fast_now[0] > slow_now[0] &&
             slope_points >= min_slope_points;
   if(direction == "SHORT")
      return htf_close < fast_now[0] &&
             fast_now[0] < slow_now[0] &&
             slope_points <= -min_slope_points;
   return false;
  }

bool D1SupportiveState(const int ema_period_input, const int slope_lag_input, bool &available)
  {
   available = false;
   const int ema_period = MathMax(1, ema_period_input);
   const int slope_lag = MathMax(1, slope_lag_input);
   if(iBars(InpTargetSymbol, PERIOD_D1) < ema_period + slope_lag + 5)
      return false;

   const double d1_close = iClose(InpTargetSymbol, PERIOD_D1, 1);
   const double ema_now = IndicatorEmaClose(PERIOD_D1, ema_period, 1);
   const double ema_prior = IndicatorEmaClose(PERIOD_D1, ema_period, 1 + slope_lag);
   if(d1_close <= 0.0 || ema_now <= 0.0 || ema_prior <= 0.0)
      return false;

   available = true;
   return d1_close > ema_now && ema_now >= ema_prior;
  }

bool D1BearishState(const int ema_period_input, const int slope_lag_input, bool &available)
  {
   available = false;
   const int ema_period = MathMax(1, ema_period_input);
   const int slope_lag = MathMax(1, slope_lag_input);
   if(iBars(InpTargetSymbol, PERIOD_D1) < ema_period + slope_lag + 5)
      return false;

   const double d1_close = iClose(InpTargetSymbol, PERIOD_D1, 1);
   const double ema_now = IndicatorEmaClose(PERIOD_D1, ema_period, 1);
   const double ema_prior = IndicatorEmaClose(PERIOD_D1, ema_period, 1 + slope_lag);
   if(d1_close <= 0.0 || ema_now <= 0.0 || ema_prior <= 0.0)
      return false;

   available = true;
   return d1_close < ema_now && ema_now <= ema_prior;
  }

bool D1NonUpState(const int ema_period_input, const int slope_lag_input, bool &available)
  {
   available = false;
   const int ema_period = MathMax(1, ema_period_input);
   const int slope_lag = MathMax(1, slope_lag_input);
   if(iBars(InpTargetSymbol, PERIOD_D1) < ema_period + slope_lag + 5)
      return false;

   const double d1_close = iClose(InpTargetSymbol, PERIOD_D1, 1);
   const double ema_now = IndicatorEmaClose(PERIOD_D1, ema_period, 1);
   const double ema_prior = IndicatorEmaClose(PERIOD_D1, ema_period, 1 + slope_lag);
   if(d1_close <= 0.0 || ema_now <= 0.0 || ema_prior <= 0.0)
      return false;

   available = true;
   return d1_close <= ema_now || ema_now < ema_prior;
  }

bool D1StructuralDownState(const int ema_period_input, const int slope_lag_input, bool &available)
  {
   available = false;
   const int ema_period = MathMax(1, ema_period_input);
   const int slope_lag = MathMax(1, slope_lag_input);
   if(iBars(InpTargetSymbol, PERIOD_D1) < ema_period + slope_lag + 5)
      return false;

   const double d1_close = iClose(InpTargetSymbol, PERIOD_D1, 1);
   const double ema_now = IndicatorEmaClose(PERIOD_D1, ema_period, 1);
   const double ema_prior = IndicatorEmaClose(PERIOD_D1, ema_period, 1 + slope_lag);
   if(d1_close <= 0.0 || ema_now <= 0.0 || ema_prior <= 0.0)
      return false;

   available = true;
   return d1_close < ema_now && ema_now <= ema_prior;
  }

bool H4D1SupportiveStateAllows(const string direction)
  {
   if(!InpH4D1SupportiveStateGuardEnabled)
      return true;
   if(!IsH4DecisionSignalMode())
      return true;
   if(direction != "LONG")
      return true;

   bool available = false;
   const bool supportive = D1SupportiveState(InpH4D1SupportiveEmaPeriod, InpH4D1SupportiveSlopeLagBars, available);
   if(!available)
      return false;
   return supportive;
  }

bool D1SupportStateGateAllows()
  {
   if(InpD1StructuralDownGateEnabled)
     {
      bool available = false;
      const bool structural_down = D1StructuralDownState(InpD1StructuralDownEmaPeriod, InpD1StructuralDownSlopeLagBars, available);
      if(!available)
         return false;
      return structural_down;
     }

   if(InpD1SupportStateGateMode <= 0)
      return true;

   if(InpD1SupportStateGateMode == 1 || InpD1SupportStateGateMode == 2)
     {
      bool available = false;
      const bool supportive = D1SupportiveState(InpD1SupportStateEmaPeriod, InpD1SupportStateSlopeLagBars, available);
      if(!available)
         return false;
      if(InpD1SupportStateGateMode == 1)
         return supportive;
      return !supportive;
     }
   if(InpD1SupportStateGateMode == 3)
     {
      bool available = false;
      const bool bearish = D1BearishState(InpD1SupportStateEmaPeriod, InpD1SupportStateSlopeLagBars, available);
      if(!available)
         return false;
      return bearish;
     }
   if(InpD1SupportStateGateMode == 4)
     {
      bool available = false;
      const bool non_up = D1NonUpState(InpD1SupportStateEmaPeriod, InpD1SupportStateSlopeLagBars, available);
      if(!available)
         return false;
      return non_up;
     }
   return false;
  }

double OwnClosedPnlBetween(const datetime from_time, const datetime to_time)
  {
   if(from_time <= 0 || to_time <= from_time)
      return 0.0;
   if(!HistorySelect(from_time, to_time))
      return 0.0;

   double pnl = 0.0;
   const int total = HistoryDealsTotal();
   for(int i = 0; i < total; i++)
     {
      const ulong ticket = HistoryDealGetTicket(i);
      if(ticket == 0)
         continue;
      if(HistoryDealGetString(ticket, DEAL_SYMBOL) != InpTargetSymbol)
         continue;
      if((long)HistoryDealGetInteger(ticket, DEAL_MAGIC) != InpMagicNumber)
         continue;

      const long entry = (long)HistoryDealGetInteger(ticket, DEAL_ENTRY);
      if(entry != DEAL_ENTRY_OUT && entry != DEAL_ENTRY_INOUT && entry != DEAL_ENTRY_OUT_BY)
         continue;

      pnl += HistoryDealGetDouble(ticket, DEAL_PROFIT);
      pnl += HistoryDealGetDouble(ticket, DEAL_SWAP);
      pnl += HistoryDealGetDouble(ticket, DEAL_COMMISSION);
     }
   return pnl;
  }

bool H4D1WeeklyLossGovernorAllows()
  {
   if(!InpH4D1WeeklyLossGovernorEnabled)
      return true;
   if(!IsH4DecisionSignalMode())
      return true;
   if(InpH4D1WeeklyLossLimitUsd <= 0.0)
      return true;

   const datetime week_start = BrokerWeekStart(TimeCurrent());
   const double week_pnl = OwnClosedPnlBetween(week_start, TimeCurrent());
   return week_pnl > -InpH4D1WeeklyLossLimitUsd;
  }

bool HourInWindow(const int hour, const int start_hour_input, const int end_hour_input)
  {
   const int start_hour = MathMax(0, MathMin(23, start_hour_input));
   const int end_hour = MathMax(0, MathMin(24, end_hour_input));
   if(start_hour == end_hour)
      return true;
   if(start_hour < end_hour)
      return hour >= start_hour && hour < end_hour;
   return hour >= start_hour || hour < end_hour;
  }

bool CurrentHourInCsv(const string csv_hours)
  {
   if(csv_hours == "")
      return false;
   MqlDateTime parts;
   TimeToStruct(TimeCurrent(), parts);
   string tokens[];
   const int count = StringSplit(csv_hours, ',', tokens);
   for(int i = 0; i < count; i++)
     {
      string token = tokens[i];
      StringTrimLeft(token);
      StringTrimRight(token);
      if(token == "")
         continue;
      const int hour = (int)StringToInteger(token);
      if(hour == parts.hour)
         return true;
     }
   return false;
  }

bool EntryHourBlocked()
  {
   return CurrentHourInCsv(InpBlockedEntryHoursCsv);
  }

bool EntryDayHourBlocked()
  {
   if(InpBlockedEntryDayHoursCsv == "")
      return false;
   MqlDateTime parts;
   TimeToStruct(TimeCurrent(), parts);
   string tokens[];
   const int count = StringSplit(InpBlockedEntryDayHoursCsv, ',', tokens);
   for(int i = 0; i < count; i++)
     {
      string token = tokens[i];
      StringTrimLeft(token);
      StringTrimRight(token);
      if(token == "")
         continue;
      const int colon = StringFind(token, ":");
      if(colon <= 0)
         continue;
      const int day = (int)StringToInteger(StringSubstr(token, 0, colon));
      const int hour = (int)StringToInteger(StringSubstr(token, colon + 1));
      if(day == parts.day_of_week && hour == parts.hour)
         return true;
     }
   return false;
  }

bool DirectionEntryHourBlocked(const string direction)
  {
   if(direction == "LONG")
      return CurrentHourInCsv(InpBlockedLongEntryHoursCsv);
   if(direction == "SHORT")
      return CurrentHourInCsv(InpBlockedShortEntryHoursCsv);
   return false;
  }

bool DirectionalSessionAllows(const string direction)
  {
   if(!InpUseDirectionalSessionFilter)
      return true;
   MqlDateTime parts;
   TimeToStruct(TimeCurrent(), parts);
   if(direction == "LONG")
      return HourInWindow(parts.hour, InpLongSessionStartHour, InpLongSessionEndHour);
   if(direction == "SHORT")
      return HourInWindow(parts.hour, InpShortSessionStartHour, InpShortSessionEndHour);
   return false;
  }

double CloseToRecentExtreme(
   const string direction,
   const double recent_high,
   const double recent_low,
   const double close
)
  {
   if(direction == "LONG")
      return close - recent_high;
   if(direction == "SHORT")
      return recent_low - close;
   return 0.0;
  }

bool FeatureLossFilterBlocks(
   const string direction,
   const double recent_high,
   const double recent_low,
   const double close,
   double &close_to_recent_extreme,
   string &feature_reason
)
  {
   close_to_recent_extreme = CloseToRecentExtreme(direction, recent_high, recent_low, close);
   feature_reason = "";
   if(!InpFeatureLossFilterEnabled)
      return false;
   if(direction == "SHORT")
     {
      if(close_to_recent_extreme >= InpShortCloseToRecentExtremeBlockMin)
        {
         feature_reason = "feature_loss_filter_short_close_to_recent_extreme_min";
         return true;
        }
      if(InpShortCloseToRecentExtremeBlockMaxEnabled && close_to_recent_extreme <= InpShortCloseToRecentExtremeBlockMax)
        {
         feature_reason = "feature_loss_filter_short_close_to_recent_extreme_max";
         return true;
        }
     }
   return false;
  }

bool IsH4DecisionSignalMode()
  {
   return InpSignalMode == SIGNAL_D1_COMPRESSION_H4_EXPANSION ||
          InpSignalMode == SIGNAL_H4_TREND_PULLBACK_D1_BIAS ||
          InpSignalMode == SIGNAL_WEEKLY_LEVEL_H4_REJECTION;
  }

bool IsH1DecisionSignalMode()
  {
   return InpSignalMode == SIGNAL_D1_COMPRESSION_H1_EXPANSION ||
          InpSignalMode == SIGNAL_WEEKLY_DAMAGE_H1;
  }

double TimeframeHigh(const ENUM_TIMEFRAMES timeframe, const int start_shift, const int count)
  {
   double value = 0.0;
   for(int i = 0; i < count; i++)
     {
      const double high = iHigh(InpTargetSymbol, timeframe, start_shift + i);
      if(high <= 0.0)
         return 0.0;
      if(value == 0.0 || high > value)
         value = high;
     }
   return value;
  }

double TimeframeLow(const ENUM_TIMEFRAMES timeframe, const int start_shift, const int count)
  {
   double value = 0.0;
   for(int i = 0; i < count; i++)
     {
      const double low = iLow(InpTargetSymbol, timeframe, start_shift + i);
      if(low <= 0.0)
         return 0.0;
      if(value == 0.0 || low < value)
         value = low;
     }
   return value;
  }

double TimeframeMedianRange(const ENUM_TIMEFRAMES timeframe, const int count, const int start_shift)
  {
   double ranges[];
   ArrayResize(ranges, count);
   int found = 0;
   for(int i = 0; i < count; i++)
     {
      const double high = iHigh(InpTargetSymbol, timeframe, start_shift + i);
      const double low = iLow(InpTargetSymbol, timeframe, start_shift + i);
      if(high <= 0.0 || low <= 0.0 || high <= low)
         continue;
      ranges[found] = high - low;
      found++;
     }
   if(found <= 0)
      return 0.0;
   ArrayResize(ranges, found);
   ArraySort(ranges);
   if((found % 2) == 1)
      return ranges[found / 2];
   return 0.5 * (ranges[(found / 2) - 1] + ranges[found / 2]);
  }

double IndicatorAtrPrice(const ENUM_TIMEFRAMES timeframe, const int period, const int shift)
  {
   const int handle = iATR(InpTargetSymbol, timeframe, period);
   if(handle == INVALID_HANDLE)
      return 0.0;
   double buffer[1];
   const int copied = CopyBuffer(handle, 0, shift, 1, buffer);
   IndicatorRelease(handle);
   if(copied != 1 || buffer[0] <= 0.0)
      return 0.0;
   return buffer[0];
  }

double IndicatorEmaClose(const ENUM_TIMEFRAMES timeframe, const int period, const int shift)
  {
   const int handle = iMA(InpTargetSymbol, timeframe, period, 0, MODE_EMA, PRICE_CLOSE);
   if(handle == INVALID_HANDLE)
      return 0.0;
   double buffer[1];
   const int copied = CopyBuffer(handle, 0, shift, 1, buffer);
   IndicatorRelease(handle);
   if(copied != 1 || buffer[0] <= 0.0)
      return 0.0;
   return buffer[0];
  }

double IndicatorAtrPercentile(const ENUM_TIMEFRAMES timeframe, const int period, const int lookback, const int shift)
  {
   const double current_atr = IndicatorAtrPrice(timeframe, period, shift);
   if(current_atr <= 0.0)
      return 100.0;

   const int handle = iATR(InpTargetSymbol, timeframe, period);
   if(handle == INVALID_HANDLE)
      return 100.0;
   double values[];
   ArrayResize(values, lookback);
   const int copied = CopyBuffer(handle, 0, shift, lookback, values);
   IndicatorRelease(handle);
   if(copied <= 0)
      return 100.0;

   int valid = 0;
   int less_or_equal = 0;
   for(int i = 0; i < copied; i++)
     {
      if(values[i] <= 0.0)
         continue;
      valid++;
      if(values[i] <= current_atr)
         less_or_equal++;
     }
   if(valid <= 0)
      return 100.0;
   return 100.0 * (double)less_or_equal / (double)valid;
  }

double ClosePositionInRange(const double high, const double low, const double close)
  {
   const double range = high - low;
   if(range <= 0.0)
      return 0.5;
   return (close - low) / range;
  }

bool CurrentBrokerDayStateFromM5(
   const datetime signal_time,
   double &day_open,
   double &day_high,
   double &day_low,
   int &bars_found
)
  {
   day_open = 0.0;
   day_high = 0.0;
   day_low = 0.0;
   bars_found = 0;

   MqlDateTime parts;
   TimeToStruct(signal_time, parts);
   parts.hour = 0;
   parts.min = 0;
   parts.sec = 0;
   const datetime day_start = StructToTime(parts);
   const int bars = iBars(InpTargetSymbol, PERIOD_M5);

   for(int shift = 1; shift < bars && shift < 400; shift++)
     {
      const datetime bar_time = iTime(InpTargetSymbol, PERIOD_M5, shift);
      if(bar_time == 0)
         break;
      if(bar_time > signal_time)
         continue;
      if(bar_time < day_start)
         break;

      const double bar_open = iOpen(InpTargetSymbol, PERIOD_M5, shift);
      const double bar_high = iHigh(InpTargetSymbol, PERIOD_M5, shift);
      const double bar_low = iLow(InpTargetSymbol, PERIOD_M5, shift);
      if(bar_open <= 0.0 || bar_high <= 0.0 || bar_low <= 0.0)
         continue;

      if(bars_found == 0)
        {
         day_high = bar_high;
         day_low = bar_low;
        }
      else
        {
         day_high = MathMax(day_high, bar_high);
         day_low = MathMin(day_low, bar_low);
        }
      day_open = bar_open;
      bars_found++;
     }

   return bars_found >= MathMax(1, InpDailyExtremeMinBarsSinceOpen) &&
          day_open > 0.0 &&
          day_high > day_low;
  }

bool TryDailyExtremeReclaimSignal(
   const datetime signal_time,
   const double open,
   const double high,
   const double low,
   const double close,
   const double range,
   const double m5_atr,
   const double body_fraction,
   const double close_location,
   string &direction,
   string &reason,
   double &stop_distance,
   double &break_distance_atr
)
  {
   MqlDateTime parts;
   TimeToStruct(signal_time, parts);
   if(!HourInWindow(parts.hour, InpDailyExtremeStartHour, InpDailyExtremeEndHour))
      return false;

   const double d1_atr = IndicatorAtrPrice(PERIOD_D1, MathMax(1, InpAtrPeriod), 1);
   if(d1_atr <= 0.0 || m5_atr <= 0.0 || range <= 0.0)
      return false;

   double day_open = 0.0;
   double day_high = 0.0;
   double day_low = 0.0;
   int bars_found = 0;
   if(!CurrentBrokerDayStateFromM5(signal_time, day_open, day_high, day_low, bars_found))
      return false;

   if(range < InpMinRangeAtr * m5_atr || body_fraction < InpDailyExtremeMinBodyFraction)
      return false;

   const double up_move_atr = (day_high - day_open) / d1_atr;
   const double down_move_atr = (day_open - day_low) / d1_atr;
   const bool short_reclaim =
      up_move_atr >= InpDailyExtremeMinMoveAtr &&
      high >= day_high - InpDailyExtremeTouchAtr * d1_atr &&
      close <= day_high - InpDailyExtremeReclaimAtr * d1_atr &&
      close < open &&
      close_location <= InpShortCloseLocation;
   const bool long_reclaim =
      down_move_atr >= InpDailyExtremeMinMoveAtr &&
      low <= day_low + InpDailyExtremeTouchAtr * d1_atr &&
      close >= day_low + InpDailyExtremeReclaimAtr * d1_atr &&
      close > open &&
      close_location >= InpLongCloseLocation;

   if(!short_reclaim && !long_reclaim)
      return false;

   const bool choose_short = short_reclaim && (!long_reclaim || up_move_atr >= down_move_atr);
   if(choose_short)
     {
      const double projected_sl = day_high + InpDailyExtremeStopBufferAtr * d1_atr;
      direction = "SHORT";
      reason = "M5_DAILY_EXTREME_RECLAIM_SHORT";
      stop_distance = projected_sl - close;
      break_distance_atr = (day_high - close) / d1_atr;
     }
   else
     {
      const double projected_sl = day_low - InpDailyExtremeStopBufferAtr * d1_atr;
      direction = "LONG";
      reason = "M5_DAILY_EXTREME_RECLAIM_LONG";
      stop_distance = close - projected_sl;
      break_distance_atr = (close - day_low) / d1_atr;
     }
   return stop_distance > 0.0;
  }

bool TryD1CompressionH4ExpansionSignal(string &direction, string &reason, double &stop_distance, double &break_distance_atr)
  {
   if(iBars(InpTargetSymbol, PERIOD_D1) < 280 || iBars(InpTargetSymbol, PERIOD_H4) < 60)
      return false;

   const int box_days = MathMax(2, InpD1CompressionBoxDays);
   const double d1_atr_percentile = IndicatorAtrPercentile(PERIOD_D1, 14, 252, 1);
   const double box_high = TimeframeHigh(PERIOD_D1, 1, box_days);
   const double box_low = TimeframeLow(PERIOD_D1, 1, box_days);
   const double d1_median_range = TimeframeMedianRange(PERIOD_D1, 20, 1);
   const double box_width = box_high - box_low;
   const double box_average = box_width / (double)box_days;
   if(box_high <= 0.0 || box_low <= 0.0 || d1_median_range <= 0.0 || box_width <= 0.0)
      return false;
   if(d1_atr_percentile > InpD1CompressionAtrPercentileMax || box_average > InpD1CompressionRangeMedianMax * d1_median_range)
      return false;

   const double h4_open = iOpen(InpTargetSymbol, PERIOD_H4, 1);
   const double h4_high = iHigh(InpTargetSymbol, PERIOD_H4, 1);
   const double h4_low = iLow(InpTargetSymbol, PERIOD_H4, 1);
   const double h4_close = iClose(InpTargetSymbol, PERIOD_H4, 1);
   const double h4_range = h4_high - h4_low;
   const double h4_body = MathAbs(h4_close - h4_open);
   const double h4_atr = IndicatorAtrPrice(PERIOD_H4, 14, 1);
   if(h4_open <= 0.0 || h4_high <= 0.0 || h4_low <= 0.0 || h4_close <= 0.0 || h4_range <= 0.0 || h4_atr <= 0.0)
      return false;
   if(h4_body / h4_range < InpD1CompressionH4MinBodyFraction)
      return false;

   const bool is_long = h4_close > box_high && h4_close > h4_open;
   const bool is_short = h4_close < box_low && h4_close < h4_open;
   if(!is_long && !is_short)
      return false;

   if(is_long)
     {
      direction = "LONG";
      stop_distance = MathMax(h4_close - box_low, h4_atr);
      break_distance_atr = (h4_close - box_high) / h4_atr;
      reason = "D1_COMPRESSION_H4_EXPANSION_LONG";
     }
   else
     {
      direction = "SHORT";
      stop_distance = MathMax(box_high - h4_close, h4_atr);
      break_distance_atr = (box_low - h4_close) / h4_atr;
      reason = "D1_COMPRESSION_H4_EXPANSION_SHORT";
     }
   return stop_distance > 0.0;
  }

bool TryD1CompressionH1ExpansionSignal(string &direction, string &reason, double &stop_distance, double &break_distance_atr)
  {
   if(iBars(InpTargetSymbol, PERIOD_D1) < 280 || iBars(InpTargetSymbol, PERIOD_H1) < 240)
      return false;

   const int box_days = MathMax(2, InpD1CompressionBoxDays);
   const double d1_atr_percentile = IndicatorAtrPercentile(PERIOD_D1, 14, 252, 1);
   const double box_high = TimeframeHigh(PERIOD_D1, 1, box_days);
   const double box_low = TimeframeLow(PERIOD_D1, 1, box_days);
   const double d1_median_range = TimeframeMedianRange(PERIOD_D1, 20, 1);
   const double box_width = box_high - box_low;
   const double box_average = box_width / (double)box_days;
   if(box_high <= 0.0 || box_low <= 0.0 || d1_median_range <= 0.0 || box_width <= 0.0)
      return false;
   if(d1_atr_percentile > InpD1CompressionAtrPercentileMax || box_average > InpD1CompressionRangeMedianMax * d1_median_range)
      return false;

   const double h1_open = iOpen(InpTargetSymbol, PERIOD_H1, 1);
   const double h1_high = iHigh(InpTargetSymbol, PERIOD_H1, 1);
   const double h1_low = iLow(InpTargetSymbol, PERIOD_H1, 1);
   const double h1_close = iClose(InpTargetSymbol, PERIOD_H1, 1);
   const double h1_range = h1_high - h1_low;
   const double h1_body = MathAbs(h1_close - h1_open);
   const double h1_atr = IndicatorAtrPrice(PERIOD_H1, 14, 1);
   if(h1_open <= 0.0 || h1_high <= 0.0 || h1_low <= 0.0 || h1_close <= 0.0 || h1_range <= 0.0 || h1_atr <= 0.0)
      return false;
   if(h1_body / h1_range < InpD1CompressionH4MinBodyFraction)
      return false;

   const bool is_long = h1_close > box_high && h1_close > h1_open;
   const bool is_short = h1_close < box_low && h1_close < h1_open;
   if(!is_long && !is_short)
      return false;

   if(is_long)
     {
      direction = "LONG";
      stop_distance = MathMax(h1_close - box_low, h1_atr);
      break_distance_atr = (h1_close - box_high) / h1_atr;
      reason = "D1_COMPRESSION_H1_EXPANSION_LONG";
     }
   else
     {
      direction = "SHORT";
      stop_distance = MathMax(box_high - h1_close, h1_atr);
      break_distance_atr = (box_low - h1_close) / h1_atr;
      reason = "D1_COMPRESSION_H1_EXPANSION_SHORT";
     }
   return stop_distance > 0.0;
  }

bool TryH4TrendPullbackD1BiasSignal(string &direction, string &reason, double &stop_distance, double &break_distance_atr)
  {
   if(iBars(InpTargetSymbol, PERIOD_D1) < 230 || iBars(InpTargetSymbol, PERIOD_H4) < 80)
      return false;

   const double d1_ema50 = IndicatorEmaClose(PERIOD_D1, 50, 1);
   const double d1_ema200 = IndicatorEmaClose(PERIOD_D1, 200, 1);
   const double d1_ema50_prior = IndicatorEmaClose(PERIOD_D1, 50, 21);
   const double h4_ema21 = IndicatorEmaClose(PERIOD_H4, 21, 1);
   const double h4_ema50 = IndicatorEmaClose(PERIOD_H4, 50, 1);
   const double h4_atr = IndicatorAtrPrice(PERIOD_H4, 14, 1);
   if(d1_ema50 <= 0.0 || d1_ema200 <= 0.0 || d1_ema50_prior <= 0.0 || h4_ema21 <= 0.0 || h4_ema50 <= 0.0 || h4_atr <= 0.0)
      return false;

   const bool long_bias = d1_ema50 > d1_ema200 && d1_ema50 > d1_ema50_prior;
   const bool short_bias = d1_ema50 < d1_ema200 && d1_ema50 < d1_ema50_prior;
   if(!long_bias && !short_bias)
      return false;

   const double h4_open = iOpen(InpTargetSymbol, PERIOD_H4, 1);
   const double h4_high = iHigh(InpTargetSymbol, PERIOD_H4, 1);
   const double h4_low = iLow(InpTargetSymbol, PERIOD_H4, 1);
   const double h4_close = iClose(InpTargetSymbol, PERIOD_H4, 1);
   const double h4_range = h4_high - h4_low;
   if(h4_open <= 0.0 || h4_high <= 0.0 || h4_low <= 0.0 || h4_close <= 0.0 || h4_range <= 0.0)
      return false;

   const double pullback_reference = long_bias ? h4_low : h4_high;
   const double distance_to_ema21 = MathAbs(pullback_reference - h4_ema21);
   const double distance_to_ema50 = MathAbs(pullback_reference - h4_ema50);
   const bool pullback_near_average = MathMin(distance_to_ema21, distance_to_ema50) <= 0.5 * h4_atr;
   const bool trend_structure_ok = long_bias ? h4_close > d1_ema200 : h4_close < d1_ema200;
   if(!pullback_near_average || !trend_structure_ok)
      return false;

   const double close_position = ClosePositionInRange(h4_high, h4_low, h4_close);
   const bool long_confirmation = long_bias && h4_close > h4_open && close_position >= 0.65;
   const bool short_confirmation = short_bias && h4_close < h4_open && close_position <= 0.35;
   if(!long_confirmation && !short_confirmation)
      return false;

   if(long_confirmation)
     {
      const double swing_low = TimeframeLow(PERIOD_H4, 1, 5);
      const double projected_sl = swing_low - 0.25 * h4_atr;
      direction = "LONG";
      stop_distance = h4_close - projected_sl;
      break_distance_atr = (h4_close - MathMin(h4_ema21, h4_ema50)) / h4_atr;
      reason = "H4_TREND_PULLBACK_D1_BIAS_LONG";
     }
   else
     {
      const double swing_high = TimeframeHigh(PERIOD_H4, 1, 5);
      const double projected_sl = swing_high + 0.25 * h4_atr;
      direction = "SHORT";
      stop_distance = projected_sl - h4_close;
      break_distance_atr = (MathMax(h4_ema21, h4_ema50) - h4_close) / h4_atr;
      reason = "H4_TREND_PULLBACK_D1_BIAS_SHORT";
     }
   return stop_distance > 0.0;
  }

bool TryWeeklyLevel(
   const double level_price,
   const bool resistance_level,
   const string level_name,
   const double h4_atr,
   string &direction,
   string &reason,
   double &stop_distance,
   double &break_distance_atr
)
  {
   const double h4_open = iOpen(InpTargetSymbol, PERIOD_H4, 1);
   const double h4_high = iHigh(InpTargetSymbol, PERIOD_H4, 1);
   const double h4_low = iLow(InpTargetSymbol, PERIOD_H4, 1);
   const double h4_close = iClose(InpTargetSymbol, PERIOD_H4, 1);
   const double point = SymbolInfoDouble(InpTargetSymbol, SYMBOL_POINT);
   double body = MathAbs(h4_close - h4_open);
   if(body < point)
      body = point;
   const double upper_wick = h4_high - MathMax(h4_open, h4_close);
   const double lower_wick = MathMin(h4_open, h4_close) - h4_low;
   const double zone = 0.25 * h4_atr;
   if(level_price <= 0.0 || h4_atr <= 0.0 || point <= 0.0 || h4_high <= 0.0 || h4_low <= 0.0 || h4_close <= 0.0)
      return false;

   if(resistance_level)
     {
      const bool touched = h4_high >= level_price - zone && h4_low <= level_price + zone;
      const bool rejected = upper_wick >= 1.5 * body && h4_close < level_price;
      if(!touched || !rejected)
         return false;
      direction = "SHORT";
      stop_distance = (h4_high + 0.25 * h4_atr) - h4_close;
      break_distance_atr = (level_price - h4_close) / h4_atr;
      reason = "WEEKLY_LEVEL_H4_REJECTION_SHORT_" + level_name;
      return stop_distance > 0.0;
     }

   const bool touched = h4_low <= level_price + zone && h4_high >= level_price - zone;
   const bool rejected = lower_wick >= 1.5 * body && h4_close > level_price;
   if(!touched || !rejected)
      return false;
   direction = "LONG";
   stop_distance = h4_close - (h4_low - 0.25 * h4_atr);
   break_distance_atr = (h4_close - level_price) / h4_atr;
   reason = "WEEKLY_LEVEL_H4_REJECTION_LONG_" + level_name;
   return stop_distance > 0.0;
  }

bool TryWeeklyLevelH4RejectionSignal(string &direction, string &reason, double &stop_distance, double &break_distance_atr)
  {
   if(iBars(InpTargetSymbol, PERIOD_W1) < 10 || iBars(InpTargetSymbol, PERIOD_H4) < 60)
      return false;

   const double h4_atr = IndicatorAtrPrice(PERIOD_H4, 14, 1);
   if(h4_atr <= 0.0)
      return false;

   const double previous_week_high = iHigh(InpTargetSymbol, PERIOD_W1, 1);
   const double previous_week_low = iLow(InpTargetSymbol, PERIOD_W1, 1);
   const double four_week_high = TimeframeHigh(PERIOD_W1, 1, 4);
   const double four_week_low = TimeframeLow(PERIOD_W1, 1, 4);

   if(TryWeeklyLevel(previous_week_high, true, "previous_week_high", h4_atr, direction, reason, stop_distance, break_distance_atr))
      return true;
   if(TryWeeklyLevel(previous_week_low, false, "previous_week_low", h4_atr, direction, reason, stop_distance, break_distance_atr))
      return true;
   if(TryWeeklyLevel(four_week_high, true, "prior_4_week_high", h4_atr, direction, reason, stop_distance, break_distance_atr))
      return true;
   if(TryWeeklyLevel(four_week_low, false, "prior_4_week_low", h4_atr, direction, reason, stop_distance, break_distance_atr))
      return true;
   return false;
  }

datetime BrokerWeekStart(const datetime value)
  {
   MqlDateTime parts;
   TimeToStruct(value, parts);
   parts.hour = 0;
   parts.min = 0;
   parts.sec = 0;
   const datetime day_start = StructToTime(parts);
   const int days_since_monday = (parts.day_of_week == 0) ? 6 : parts.day_of_week - 1;
   return day_start - days_since_monday * 86400;
  }

bool CurrentBrokerWeekStateFromH1(
   const datetime signal_time,
   double &week_open,
   double &week_high,
   double &week_low,
   int &week_bars,
   double &monday_high,
   double &monday_low,
   int &monday_bars
)
  {
   week_open = 0.0;
   week_high = 0.0;
   week_low = 0.0;
   week_bars = 0;
   monday_high = 0.0;
   monday_low = 0.0;
   monday_bars = 0;

   const datetime week_start = BrokerWeekStart(signal_time);
   const datetime monday_end = week_start + 86400;
   const int bars = iBars(InpTargetSymbol, PERIOD_H1);

   for(int shift = 1; shift < bars && shift < 240; shift++)
     {
      const datetime bar_time = iTime(InpTargetSymbol, PERIOD_H1, shift);
      if(bar_time == 0)
         break;
      if(bar_time > signal_time)
         continue;
      if(bar_time < week_start)
         break;

      const double bar_open = iOpen(InpTargetSymbol, PERIOD_H1, shift);
      const double bar_high = iHigh(InpTargetSymbol, PERIOD_H1, shift);
      const double bar_low = iLow(InpTargetSymbol, PERIOD_H1, shift);
      if(bar_open <= 0.0 || bar_high <= 0.0 || bar_low <= 0.0 || bar_high <= bar_low)
         continue;

      if(week_bars == 0)
        {
         week_high = bar_high;
         week_low = bar_low;
        }
      else
        {
         week_high = MathMax(week_high, bar_high);
         week_low = MathMin(week_low, bar_low);
        }
      week_open = bar_open;
      week_bars++;

      if(bar_time >= week_start && bar_time < monday_end)
        {
         if(monday_bars == 0)
           {
            monday_high = bar_high;
            monday_low = bar_low;
           }
         else
           {
            monday_high = MathMax(monday_high, bar_high);
            monday_low = MathMin(monday_low, bar_low);
           }
         monday_bars++;
        }
     }

   return week_bars >= 24 &&
          monday_bars >= 1 &&
          week_open > 0.0 &&
          week_high > week_low &&
          monday_high > monday_low;
  }

bool TryWeeklyDamageH1Signal(string &direction, string &reason, double &stop_distance, double &break_distance_atr)
  {
   if(iBars(InpTargetSymbol, PERIOD_W1) < 10 || iBars(InpTargetSymbol, PERIOD_H1) < 240)
      return false;

   const datetime signal_time = iTime(InpTargetSymbol, PERIOD_H1, 1);
   if(signal_time == 0)
      return false;

   MqlDateTime parts;
   TimeToStruct(signal_time, parts);
   const int start_day = MathMax(0, MathMin(6, InpWeeklyDamageStartDay));
   const int end_day = MathMax(0, MathMin(6, InpWeeklyDamageEndDay));
   if(parts.day_of_week < start_day || parts.day_of_week > end_day)
      return false;

   const double h1_open = iOpen(InpTargetSymbol, PERIOD_H1, 1);
   const double h1_high = iHigh(InpTargetSymbol, PERIOD_H1, 1);
   const double h1_low = iLow(InpTargetSymbol, PERIOD_H1, 1);
   const double h1_close = iClose(InpTargetSymbol, PERIOD_H1, 1);
   const double h1_range = h1_high - h1_low;
   if(h1_open <= 0.0 || h1_high <= 0.0 || h1_low <= 0.0 || h1_close <= 0.0 || h1_range <= 0.0)
      return false;

   const double body_fraction = MathAbs(h1_close - h1_open) / h1_range;
   if(body_fraction < InpWeeklyDamageMinBodyFraction)
      return false;

   double week_open = 0.0;
   double week_high = 0.0;
   double week_low = 0.0;
   int week_bars = 0;
   double monday_high = 0.0;
   double monday_low = 0.0;
   int monday_bars = 0;
   if(!CurrentBrokerWeekStateFromH1(signal_time, week_open, week_high, week_low, week_bars, monday_high, monday_low, monday_bars))
      return false;

   const double d1_atr = IndicatorAtrPrice(PERIOD_D1, MathMax(1, InpAtrPeriod), 1);
   if(d1_atr <= 0.0)
      return false;

   const double previous_week_high = iHigh(InpTargetSymbol, PERIOD_W1, 1);
   const double previous_week_low = iLow(InpTargetSymbol, PERIOD_W1, 1);
   if(previous_week_high <= 0.0 || previous_week_low <= 0.0 || previous_week_high <= previous_week_low)
      return false;

   const double close_position = ClosePositionInRange(h1_high, h1_low, h1_close);
   const double up_move_atr = (week_high - week_open) / d1_atr;
   const double down_move_atr = (week_open - week_low) / d1_atr;
   const bool extended_up = up_move_atr >= InpWeeklyDamageMinMoveAtr;
   const bool extended_down = down_move_atr >= InpWeeklyDamageMinMoveAtr;
   if(!extended_up && !extended_down)
      return false;

   const double touch_zone = InpWeeklyDamageTouchAtr * d1_atr;
   const double reclaim_zone = InpWeeklyDamageReclaimAtr * d1_atr;
   const double stop_buffer = InpWeeklyDamageStopBufferAtr * d1_atr;
   const bool reversal_mode = InpWeeklyDamageMode == 0;

   if(reversal_mode)
     {
      const bool short_touch =
         h1_high >= week_high - touch_zone ||
         h1_high >= previous_week_high - touch_zone ||
         h1_high >= monday_high - touch_zone;
      const bool long_touch =
         h1_low <= week_low + touch_zone ||
         h1_low <= previous_week_low + touch_zone ||
         h1_low <= monday_low + touch_zone;
      const bool short_reversal =
         extended_up &&
         short_touch &&
         h1_close <= h1_high - reclaim_zone &&
         h1_close < h1_open &&
         close_position <= InpShortCloseLocation;
      const bool long_reversal =
         extended_down &&
         long_touch &&
         h1_close >= h1_low + reclaim_zone &&
         h1_close > h1_open &&
         close_position >= InpLongCloseLocation;
      if(!short_reversal && !long_reversal)
         return false;

      const bool choose_short = short_reversal && (!long_reversal || up_move_atr >= down_move_atr);
      if(choose_short)
        {
         direction = "SHORT";
         stop_distance = h1_high + stop_buffer - h1_close;
         break_distance_atr = (h1_high - h1_close) / d1_atr;
         reason = "WEEKLY_DAMAGE_H1_REVERSAL_SHORT";
        }
      else
        {
         direction = "LONG";
         stop_distance = h1_close - (h1_low - stop_buffer);
         break_distance_atr = (h1_close - h1_low) / d1_atr;
         reason = "WEEKLY_DAMAGE_H1_REVERSAL_LONG";
        }
      return stop_distance > 0.0;
     }

   const double upside_break_level = MathMax(monday_high, previous_week_high);
   const double downside_break_level = MathMin(monday_low, previous_week_low);
   const bool long_continuation =
      extended_up &&
      h1_close >= upside_break_level + reclaim_zone &&
      h1_close > h1_open &&
      close_position >= InpLongCloseLocation;
   const bool short_continuation =
      extended_down &&
      h1_close <= downside_break_level - reclaim_zone &&
      h1_close < h1_open &&
      close_position <= InpShortCloseLocation;
   if(!long_continuation && !short_continuation)
      return false;

   const bool choose_long = long_continuation && (!short_continuation || up_move_atr >= down_move_atr);
   if(choose_long)
     {
      direction = "LONG";
      stop_distance = h1_close - (h1_low - stop_buffer);
      break_distance_atr = (h1_close - upside_break_level) / d1_atr;
      reason = "WEEKLY_DAMAGE_H1_CONTINUATION_LONG";
     }
   else
     {
      direction = "SHORT";
      stop_distance = h1_high + stop_buffer - h1_close;
      break_distance_atr = (downside_break_level - h1_close) / d1_atr;
      reason = "WEEKLY_DAMAGE_H1_CONTINUATION_SHORT";
     }
   return stop_distance > 0.0;
  }

bool TryPriorDayLevelM5Signal(
   const datetime signal_time,
   const double open,
   const double high,
   const double low,
   const double close,
   const double range,
   const double m5_atr,
   const double body_fraction,
   const double close_location,
   string &direction,
   string &reason,
   double &stop_distance,
   double &break_distance_atr
)
  {
   if(iBars(InpTargetSymbol, PERIOD_D1) < 5 || m5_atr <= 0.0 || range <= 0.0)
      return false;

   MqlDateTime parts;
   TimeToStruct(signal_time, parts);
   if(!HourInWindow(parts.hour, InpPriorDayLevelStartHour, InpPriorDayLevelEndHour))
      return false;
   if(body_fraction < InpPriorDayLevelMinBodyFraction)
      return false;

   const double previous_day_high = iHigh(InpTargetSymbol, PERIOD_D1, 1);
   const double previous_day_low = iLow(InpTargetSymbol, PERIOD_D1, 1);
   if(previous_day_high <= 0.0 || previous_day_low <= 0.0 || previous_day_high <= previous_day_low)
      return false;

   const double break_zone = InpPriorDayLevelBreakAtr * m5_atr;
   const double touch_zone = InpPriorDayLevelTouchAtr * m5_atr;
   const double reclaim_zone = InpPriorDayLevelReclaimAtr * m5_atr;
   const double stop_buffer = InpPriorDayLevelStopBufferAtr * m5_atr;
   const bool reversal_mode = InpPriorDayLevelMode == 1;

   if(!reversal_mode)
     {
      const bool long_break =
         close >= previous_day_high + break_zone &&
         close > open &&
         close_location >= InpLongCloseLocation;
      const bool short_break =
         close <= previous_day_low - break_zone &&
         close < open &&
         close_location <= InpShortCloseLocation;
      if(!long_break && !short_break)
         return false;

      if(long_break)
        {
         const double projected_sl = MathMin(low, previous_day_high) - stop_buffer;
         direction = "LONG";
         stop_distance = close - projected_sl;
         break_distance_atr = (close - previous_day_high) / m5_atr;
         reason = "PRIOR_DAY_LEVEL_M5_CONTINUATION_LONG";
        }
      else
        {
         const double projected_sl = MathMax(high, previous_day_low) + stop_buffer;
         direction = "SHORT";
         stop_distance = projected_sl - close;
         break_distance_atr = (previous_day_low - close) / m5_atr;
         reason = "PRIOR_DAY_LEVEL_M5_CONTINUATION_SHORT";
        }
      return stop_distance > 0.0;
     }

   const bool short_reversal =
      high >= previous_day_high + touch_zone &&
      close <= previous_day_high - reclaim_zone &&
      close < open &&
      close_location <= InpShortCloseLocation;
   const bool long_reversal =
      low <= previous_day_low - touch_zone &&
      close >= previous_day_low + reclaim_zone &&
      close > open &&
      close_location >= InpLongCloseLocation;
   if(!short_reversal && !long_reversal)
      return false;

   if(short_reversal)
     {
      direction = "SHORT";
      stop_distance = (high + stop_buffer) - close;
      break_distance_atr = (high - close) / m5_atr;
      reason = "PRIOR_DAY_LEVEL_M5_REVERSAL_SHORT";
     }
   else
     {
      direction = "LONG";
      stop_distance = close - (low - stop_buffer);
      break_distance_atr = (close - low) / m5_atr;
      reason = "PRIOR_DAY_LEVEL_M5_REVERSAL_LONG";
     }
   return stop_distance > 0.0;
  }

bool TryBearBreakdownRetestSignal(
   const double open,
   const double high,
   const double close,
   const double range,
   const double m5_atr,
   const double body_fraction,
   const double close_location,
   string &direction,
   string &reason,
   double &stop_distance,
   double &break_distance_atr
)
  {
   const int break_lookback = MathMax(2, InpBearRetestLookbackBars);
   const int support_lookback = MathMax(3, InpBearRetestSupportLookbackBars);
   if(iBars(InpTargetSymbol, PERIOD_M5) < break_lookback + support_lookback + InpAtrPeriod + 10)
      return false;
   if(m5_atr <= 0.0 || range <= 0.0)
      return false;
   if(body_fraction < InpBearRetestMinBodyFraction)
      return false;
   if(close >= open || close_location > InpShortCloseLocation)
      return false;

   const double break_zone = InpBearRetestBreakAtr * m5_atr;
   const double touch_zone = InpBearRetestTouchAtr * m5_atr;
   const double reclaim_zone = InpBearRetestReclaimAtr * m5_atr;
   const double stop_buffer = InpBearRetestStopBufferAtr * m5_atr;

   for(int break_shift = 2; break_shift <= break_lookback + 1; break_shift++)
     {
      double support = 0.0;
      for(int support_shift = break_shift + 1; support_shift <= break_shift + support_lookback; support_shift++)
        {
         const double prior_low = iLow(InpTargetSymbol, PERIOD_M5, support_shift);
         if(prior_low <= 0.0)
            return false;
         if(support <= 0.0 || prior_low < support)
            support = prior_low;
        }
      if(support <= 0.0)
         continue;

      const double break_close = iClose(InpTargetSymbol, PERIOD_M5, break_shift);
      if(break_close <= 0.0 || break_close > support - break_zone)
         continue;

      double retest_high = high;
      bool reclaimed_above_support = false;
      for(int retest_shift = 1; retest_shift < break_shift; retest_shift++)
        {
         const double candidate_high = iHigh(InpTargetSymbol, PERIOD_M5, retest_shift);
         const double candidate_close = iClose(InpTargetSymbol, PERIOD_M5, retest_shift);
         if(candidate_high <= 0.0 || candidate_close <= 0.0)
            return false;
         if(candidate_high > retest_high)
            retest_high = candidate_high;
         if(candidate_close >= support + reclaim_zone)
           {
            reclaimed_above_support = true;
            break;
           }
        }
      if(reclaimed_above_support)
         continue;
      if(retest_high < support - touch_zone)
         continue;
      if(close > support - reclaim_zone)
         continue;

      direction = "SHORT";
      reason = "BEAR_BREAKDOWN_RETEST_SHORT";
      stop_distance = (retest_high + stop_buffer) - close;
      break_distance_atr = (support - close) / m5_atr;
      return stop_distance > 0.0;
     }

   return false;
  }

bool TryBearSweepReclaimSignal(
   const double high,
   const double close,
   const double range,
   const double m5_atr,
   const double body_fraction,
   string &direction,
   string &reason,
   double &stop_distance,
   double &break_distance_atr
)
  {
   const int reclaim_bars = MathMax(1, InpBearSweepReclaimBars);
   if(iBars(InpTargetSymbol, PERIOD_D1) < 5 || iBars(InpTargetSymbol, PERIOD_M5) < reclaim_bars + InpAtrPeriod + 10)
      return false;
   if(m5_atr <= 0.0 || range <= 0.0)
      return false;
   if(body_fraction < InpBearSweepMinBodyFraction)
      return false;

   const double previous_day_high = iHigh(InpTargetSymbol, PERIOD_D1, 1);
   if(previous_day_high <= 0.0)
      return false;

   const double touch_zone = InpBearSweepTouchAtr * m5_atr;
   const double reclaim_zone = InpBearSweepReclaimAtr * m5_atr;
   const double stop_buffer = InpBearSweepStopBufferAtr * m5_atr;
   if(close > previous_day_high - reclaim_zone)
      return false;

   double sweep_high = high;
   bool swept_high = high >= previous_day_high + touch_zone;
   for(int shift = 2; shift <= reclaim_bars + 1; shift++)
     {
      const double candidate_high = iHigh(InpTargetSymbol, PERIOD_M5, shift);
      if(candidate_high <= 0.0)
         return false;
      if(candidate_high > sweep_high)
         sweep_high = candidate_high;
      if(candidate_high >= previous_day_high + touch_zone)
         swept_high = true;
     }
   if(!swept_high)
      return false;

   direction = "SHORT";
   reason = "BEAR_PRIOR_DAY_HIGH_SWEEP_RECLAIM_SHORT";
   stop_distance = (sweep_high + stop_buffer) - close;
   break_distance_atr = (sweep_high - close) / m5_atr;
   return stop_distance > 0.0;
  }

bool TryBearLowerHighRejectionSignal(
   const double open,
   const double high,
   const double low,
   const double close,
   const double range,
   const double m5_atr,
   const double body_fraction,
   const double close_location,
   string &direction,
   string &reason,
   double &stop_distance,
   double &break_distance_atr
)
  {
   const int lookback_bars = MathMax(12, InpBearLowerHighLookbackBars);
   const int recent_bars = MathMax(3, InpBearLowerHighRecentBars);
   if(iBars(InpTargetSymbol, PERIOD_M5) < lookback_bars + recent_bars + InpAtrPeriod + 10)
      return false;
   if(m5_atr <= 0.0 || range <= 0.0)
      return false;
   if(body_fraction < InpBearLowerHighMinBodyFraction)
      return false;
   if(close >= open || close_location > InpShortCloseLocation)
      return false;

   const double pullback_ema = IndicatorEmaClose(PERIOD_M5, InpPullbackEmaPeriod, 1);
   if(pullback_ema <= 0.0)
      return false;

   const double prior_swing_high = RecentHigh(recent_bars + 1, lookback_bars);
   const double pullback_high = RecentHigh(1, recent_bars);
   const double pullback_low = RecentLow(1, recent_bars);
   if(prior_swing_high <= 0.0 || pullback_high <= 0.0 || pullback_low <= 0.0)
      return false;

   const double lower_high_gap = InpBearLowerHighMinGapAtr * m5_atr;
   if(pullback_high >= prior_swing_high - lower_high_gap)
      return false;

   const double prior_drop = prior_swing_high - pullback_low;
   if(prior_drop < InpBearLowerHighMinDropAtr * m5_atr)
      return false;

   const double ema_touch_zone = InpBearLowerHighEmaTouchAtr * m5_atr;
   const double ema_reclaim_zone = InpBearLowerHighReclaimAtr * m5_atr;
   if(pullback_high < pullback_ema - ema_touch_zone)
      return false;
   if(close > pullback_ema - ema_reclaim_zone)
      return false;

   const double stop_buffer = InpBearLowerHighStopBufferAtr * m5_atr;
   direction = "SHORT";
   reason = "BEAR_LOWER_HIGH_REJECTION_SHORT";
   stop_distance = (pullback_high + stop_buffer) - close;
   break_distance_atr = (pullback_high - close) / m5_atr;
   return stop_distance > 0.0;
  }

bool TryEventReactionM5Signal(
   const datetime signal_time,
   const double open,
   const double high,
   const double low,
   const double close,
   const double range,
   const double m5_atr,
   const double body_fraction,
   string &direction,
   string &reason,
   double &stop_distance,
   double &break_distance_atr
)
  {
   if(ArraySize(g_event_reaction_times) <= 0 || m5_atr <= 0.0 || range <= 0.0)
      return false;

   const string selected_type = SelectedEventReactionType();
   const bool fade_mode = InpEventReactionMode == 1;
   const int start_minutes = MathMax(0, InpEventReactionStartMinutes);
   const int end_minutes = MathMax(start_minutes, InpEventReactionEndMinutes);
   const int impulse_minutes = MathMax(5, InpEventReactionImpulseMinutes);
   const datetime decision_time = signal_time + PeriodSeconds(PERIOD_M5);
   const double break_zone = InpEventReactionBreakAtr * m5_atr;
   const double stop_buffer = InpEventReactionStopBufferAtr * m5_atr;

   for(int event_index = 0; event_index < ArraySize(g_event_reaction_times); event_index++)
     {
      if(g_event_reaction_consumed[event_index])
         continue;
      if(g_event_reaction_types[event_index] != selected_type)
         continue;

      const datetime event_time = g_event_reaction_times[event_index];
      if(event_time > decision_time)
         break;

      const int minutes_since = (int)((decision_time - event_time) / 60);
      if(minutes_since < start_minutes || minutes_since > end_minutes)
         continue;

      double event_high = 0.0;
      double event_low = 0.0;
      if(!EventReactionRangeForSignal(event_time, impulse_minutes, signal_time, event_high, event_low))
         continue;

      if(!fade_mode)
        {
         const bool long_impulse =
            close >= event_high + break_zone &&
            close > open &&
            body_fraction >= InpEventReactionMinBodyFraction;
         const bool short_impulse =
            close <= event_low - break_zone &&
            close < open &&
            body_fraction >= InpEventReactionMinBodyFraction;
         if(!long_impulse && !short_impulse)
            continue;

         if(long_impulse)
           {
            const double projected_sl = event_low - stop_buffer;
            direction = "LONG";
            stop_distance = close - projected_sl;
            break_distance_atr = (close - event_high) / m5_atr;
            reason = "EVENT_REACTION_" + selected_type + "_IMPULSE_LONG";
           }
         else
           {
            const double projected_sl = event_high + stop_buffer;
            direction = "SHORT";
            stop_distance = projected_sl - close;
            break_distance_atr = (event_low - close) / m5_atr;
            reason = "EVENT_REACTION_" + selected_type + "_IMPULSE_SHORT";
           }
         g_event_reaction_consumed[event_index] = true;
         return stop_distance > 0.0;
        }

      const bool close_inside_event_range = close >= event_low && close <= event_high;
      const bool long_fade =
         low <= event_low - break_zone &&
         close_inside_event_range &&
         close > open &&
         body_fraction >= InpEventReactionMinBodyFraction;
      const bool short_fade =
         high >= event_high + break_zone &&
         close_inside_event_range &&
         close < open &&
         body_fraction >= InpEventReactionMinBodyFraction;
      if(!long_fade && !short_fade)
         continue;

      if(long_fade)
        {
         direction = "LONG";
         stop_distance = close - (low - stop_buffer);
         break_distance_atr = (close - low) / m5_atr;
         reason = "EVENT_REACTION_" + selected_type + "_FADE_LONG";
        }
      else
        {
         direction = "SHORT";
         stop_distance = (high + stop_buffer) - close;
         break_distance_atr = (high - close) / m5_atr;
         reason = "EVENT_REACTION_" + selected_type + "_FADE_SHORT";
        }
      g_event_reaction_consumed[event_index] = true;
      return stop_distance > 0.0;
     }
   return false;
  }

void EvaluateCompletedM5Bar()
  {
   ResetDailyCounterIfNeeded();

   const bool h4_decision_signal_mode = IsH4DecisionSignalMode();
   const bool h1_decision_signal_mode = IsH1DecisionSignalMode();
   if(h4_decision_signal_mode)
     {
      const datetime h4_decision_bar = iTime(InpTargetSymbol, PERIOD_H4, 1);
      if(h4_decision_bar <= 0 || h4_decision_bar == g_last_h4_decision_bar)
         return;
      g_last_h4_decision_bar = h4_decision_bar;
     }
   if(h1_decision_signal_mode)
     {
      const datetime h1_decision_bar = iTime(InpTargetSymbol, PERIOD_H1, 1);
      if(h1_decision_bar <= 0 || h1_decision_bar == g_last_h1_decision_bar)
         return;
      g_last_h1_decision_bar = h1_decision_bar;
     }

   if(iBars(InpTargetSymbol, PERIOD_M5) < InpBreakLookbackBars + InpAtrPeriod + 5)
      return;

   double atr = 0.0;
   if(!ReadAtr(atr))
      return;
   if(InpMinAtrAbsoluteForEntry > 0.0 && atr <= InpMinAtrAbsoluteForEntry)
     {
      const double bid = SymbolInfoDouble(InpTargetSymbol, SYMBOL_BID);
      const double ask = SymbolInfoDouble(InpTargetSymbol, SYMBOL_ASK);
      const long spread_points = SymbolInfoInteger(InpTargetSymbol, SYMBOL_SPREAD);
      LogSignal("NO_SIGNAL", "NONE", "atr_below_entry_floor", bid, ask, spread_points, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, atr, 0.0, 0.0, 0.0, 0.0, 0.0);
      return;
     }

   const datetime signal_time = iTime(InpTargetSymbol, PERIOD_M5, 1);
   if(signal_time == 0)
      return;
   const double open = iOpen(InpTargetSymbol, PERIOD_M5, 1);
   const double high = iHigh(InpTargetSymbol, PERIOD_M5, 1);
   const double low = iLow(InpTargetSymbol, PERIOD_M5, 1);
   const double close = iClose(InpTargetSymbol, PERIOD_M5, 1);
   const double close_3_back = iClose(InpTargetSymbol, PERIOD_M5, 4);
   if(open <= 0.0 || high <= 0.0 || low <= 0.0 || close <= 0.0 || close_3_back <= 0.0)
      return;

   const double recent_high = RecentHigh(2, InpBreakLookbackBars);
   const double recent_low = RecentLow(2, InpBreakLookbackBars);
   if(recent_high <= 0.0 || recent_low <= 0.0)
      return;

   const double range = high - low;
   if(range <= 0.0)
      return;

   const double bid = SymbolInfoDouble(InpTargetSymbol, SYMBOL_BID);
   const double ask = SymbolInfoDouble(InpTargetSymbol, SYMBOL_ASK);
   const long spread_points = SymbolInfoInteger(InpTargetSymbol, SYMBOL_SPREAD);
   const double point = SymbolInfoDouble(InpTargetSymbol, SYMBOL_POINT);
   const int digits = (int)SymbolInfoInteger(InpTargetSymbol, SYMBOL_DIGITS);
   if(bid <= 0.0 || ask <= 0.0 || point <= 0.0)
      return;

   const double body_fraction = MathAbs(close - open) / range;
   const double close_location = (close - low) / range;
   const double three_bar_move_atr = (close - close_3_back) / atr;
   const double long_break_distance_atr = (close - recent_high) / atr;
   const double short_break_distance_atr = (recent_low - close) / atr;
   const int compression_bars = MathMax(2, InpCompressionLookbackBars);
   const double compression_high = RecentRangeHigh(2, compression_bars);
   const double compression_low = RecentRangeLow(2, compression_bars);
   const double compression_range_atr = (compression_high > 0.0 && compression_low > 0.0) ? (compression_high - compression_low) / atr : 999.0;
   double pullback_ema = 0.0;
   double opening_high = 0.0;
   double opening_low = 0.0;
   double m5_trend_fast = 0.0;
   double m5_trend_slow = 0.0;
   double m5_trend_fast_prior = 0.0;
   if(InpSignalMode == SIGNAL_EMA_PULLBACK)
     {
      double ema_buffer[1];
      if(CopyBuffer(g_m5_pullback_ema_handle, 0, 1, 1, ema_buffer) != 1)
         return;
      pullback_ema = ema_buffer[0];
      if(pullback_ema <= 0.0)
         return;
     }
   else if(InpSignalMode == SIGNAL_OPENING_RANGE_CONTINUATION || InpSignalMode == SIGNAL_OPENING_RANGE_REVERSAL)
     {
      if(!OpeningRangeForSignal(signal_time, opening_high, opening_low))
        {
         LogSignal("NO_SIGNAL", "NONE", "outside_opening_range_window", bid, ask, spread_points, recent_high, recent_low, open, high, low, close, atr, body_fraction, close_location, three_bar_move_atr, 0.0, 0.0);
         return;
        }
     }
   else if(InpSignalMode == SIGNAL_M5_EMA_TREND_CONTINUATION)
     {
      const int slope_bars = MathMax(1, InpM5TrendSlopeBars);
      double fast_now_buffer[1];
      double fast_prior_buffer[1];
      double slow_now_buffer[1];
      if(CopyBuffer(g_m5_trend_ema_fast_handle, 0, 1, 1, fast_now_buffer) != 1)
         return;
      if(CopyBuffer(g_m5_trend_ema_fast_handle, 0, 1 + slope_bars, 1, fast_prior_buffer) != 1)
         return;
      if(CopyBuffer(g_m5_trend_ema_slow_handle, 0, 1, 1, slow_now_buffer) != 1)
         return;
      m5_trend_fast = fast_now_buffer[0];
      m5_trend_slow = slow_now_buffer[0];
      m5_trend_fast_prior = fast_prior_buffer[0];
      if(m5_trend_fast <= 0.0 || m5_trend_slow <= 0.0 || m5_trend_fast_prior <= 0.0)
         return;
     }

   string direction = "";
   string reason = "";
   double break_distance_atr = 0.0;
   double htf_stop_distance = 0.0;

   if(InpSignalMode == SIGNAL_BREAK_AND_RUN)
     {
      if(close >= recent_high + InpBreakAtrMultiple * atr &&
         close > open &&
         range >= InpMinRangeAtr * atr &&
         body_fraction >= InpMinBodyFraction &&
         close_location >= InpLongCloseLocation &&
         three_bar_move_atr >= InpMinThreeBarMoveAtr)
        {
         direction = "LONG";
         reason = "M5_BREAK_AND_RUN_LONG";
         break_distance_atr = long_break_distance_atr;
        }
      else if(close <= recent_low - InpBreakAtrMultiple * atr &&
              close < open &&
              range >= InpMinRangeAtr * atr &&
              body_fraction >= InpMinBodyFraction &&
              close_location <= InpShortCloseLocation &&
              three_bar_move_atr <= -InpMinThreeBarMoveAtr)
        {
         direction = "SHORT";
         reason = "M5_BREAK_AND_RUN_SHORT";
         break_distance_atr = short_break_distance_atr;
        }
     }
   else if(InpSignalMode == SIGNAL_EMA_PULLBACK)
     {
      const bool long_pullback =
         close > pullback_ema &&
         low <= pullback_ema + InpPullbackTouchAtr * atr &&
         close > open &&
         range >= InpMinRangeAtr * atr &&
         body_fraction >= InpMinBodyFraction &&
         close_location >= InpLongCloseLocation &&
         three_bar_move_atr >= InpMinThreeBarMoveAtr;
      const bool short_pullback =
         close < pullback_ema &&
         high >= pullback_ema - InpPullbackTouchAtr * atr &&
         close < open &&
         range >= InpMinRangeAtr * atr &&
         body_fraction >= InpMinBodyFraction &&
         close_location <= InpShortCloseLocation &&
         three_bar_move_atr <= -InpMinThreeBarMoveAtr;
      if(long_pullback)
        {
         direction = "LONG";
         reason = "M5_EMA_PULLBACK_CONTINUATION_LONG";
         break_distance_atr = (close - pullback_ema) / atr;
        }
      else if(short_pullback)
        {
         direction = "SHORT";
         reason = "M5_EMA_PULLBACK_CONTINUATION_SHORT";
         break_distance_atr = (pullback_ema - close) / atr;
        }
     }
   else if(InpSignalMode == SIGNAL_COMPRESSION_EXPANSION)
     {
      const bool compression_ok = compression_range_atr <= InpCompressionMaxRangeAtr;
      const bool long_expansion =
         compression_ok &&
         close >= compression_high + InpCompressionBreakAtrMultiple * atr &&
         close > open &&
         range >= InpMinRangeAtr * atr &&
         body_fraction >= InpMinBodyFraction &&
         close_location >= InpLongCloseLocation &&
         three_bar_move_atr >= InpMinThreeBarMoveAtr;
      const bool short_expansion =
         compression_ok &&
         close <= compression_low - InpCompressionBreakAtrMultiple * atr &&
         close < open &&
         range >= InpMinRangeAtr * atr &&
         body_fraction >= InpMinBodyFraction &&
         close_location <= InpShortCloseLocation &&
         three_bar_move_atr <= -InpMinThreeBarMoveAtr;
      if(long_expansion)
        {
         direction = "LONG";
         reason = "M5_COMPRESSION_EXPANSION_LONG";
         break_distance_atr = (close - compression_high) / atr;
        }
      else if(short_expansion)
        {
         direction = "SHORT";
         reason = "M5_COMPRESSION_EXPANSION_SHORT";
         break_distance_atr = (compression_low - close) / atr;
        }
     }
   else if(InpSignalMode == SIGNAL_SWEEP_RECLAIM)
     {
      const int sweep_bars = MathMax(2, InpSweepLookbackBars);
      const double sweep_high = RecentRangeHigh(2, sweep_bars);
      const double sweep_low = RecentRangeLow(2, sweep_bars);
      if(sweep_high <= 0.0 || sweep_low <= 0.0)
         return;
      const bool long_reclaim =
         low <= sweep_low - InpSweepAtrMultiple * atr &&
         close >= sweep_low + InpReclaimAtrMultiple * atr &&
         close > open &&
         range >= InpMinRangeAtr * atr &&
         body_fraction >= InpMinBodyFraction &&
         close_location >= InpLongCloseLocation;
      const bool short_reclaim =
         high >= sweep_high + InpSweepAtrMultiple * atr &&
         close <= sweep_high - InpReclaimAtrMultiple * atr &&
         close < open &&
         range >= InpMinRangeAtr * atr &&
         body_fraction >= InpMinBodyFraction &&
         close_location <= InpShortCloseLocation;
      if(long_reclaim)
        {
         direction = "LONG";
         reason = "M5_SWEEP_RECLAIM_LONG";
         break_distance_atr = (close - sweep_low) / atr;
        }
      else if(short_reclaim)
        {
         direction = "SHORT";
         reason = "M5_SWEEP_RECLAIM_SHORT";
         break_distance_atr = (sweep_high - close) / atr;
        }
     }
   else if(InpSignalMode == SIGNAL_OPENING_RANGE_CONTINUATION)
     {
      const bool long_opening_break =
         close >= opening_high + InpOpeningBreakAtrMultiple * atr &&
         close > open &&
         range >= InpMinRangeAtr * atr &&
         body_fraction >= InpMinBodyFraction &&
         close_location >= InpLongCloseLocation &&
         three_bar_move_atr >= InpMinThreeBarMoveAtr;
      const bool short_opening_break =
         close <= opening_low - InpOpeningBreakAtrMultiple * atr &&
         close < open &&
         range >= InpMinRangeAtr * atr &&
         body_fraction >= InpMinBodyFraction &&
         close_location <= InpShortCloseLocation &&
         three_bar_move_atr <= -InpMinThreeBarMoveAtr;
      if(long_opening_break)
        {
         direction = "LONG";
         reason = "M5_OPENING_RANGE_CONTINUATION_LONG";
         break_distance_atr = (close - opening_high) / atr;
        }
      else if(short_opening_break)
        {
         direction = "SHORT";
         reason = "M5_OPENING_RANGE_CONTINUATION_SHORT";
         break_distance_atr = (opening_low - close) / atr;
        }
     }
   else if(InpSignalMode == SIGNAL_OPENING_RANGE_REVERSAL)
     {
      const bool long_opening_reversal =
         low <= opening_low - InpOpeningBreakAtrMultiple * atr &&
         close >= opening_low + InpReclaimAtrMultiple * atr &&
         close > open &&
         range >= InpMinRangeAtr * atr &&
         body_fraction >= InpMinBodyFraction &&
         close_location >= InpLongCloseLocation;
      const bool short_opening_reversal =
         high >= opening_high + InpOpeningBreakAtrMultiple * atr &&
         close <= opening_high - InpReclaimAtrMultiple * atr &&
         close < open &&
         range >= InpMinRangeAtr * atr &&
         body_fraction >= InpMinBodyFraction &&
         close_location <= InpShortCloseLocation;
      if(long_opening_reversal)
        {
         direction = "LONG";
         reason = "M5_OPENING_RANGE_REVERSAL_LONG";
         break_distance_atr = (close - opening_low) / atr;
        }
      else if(short_opening_reversal)
        {
         direction = "SHORT";
         reason = "M5_OPENING_RANGE_REVERSAL_SHORT";
         break_distance_atr = (opening_high - close) / atr;
        }
     }
   else if(InpSignalMode == SIGNAL_M5_EMA_TREND_CONTINUATION)
     {
      const double slope_atr = (m5_trend_fast - m5_trend_fast_prior) / atr;
      const double long_distance_atr = (close - m5_trend_fast) / atr;
      const double short_distance_atr = (m5_trend_fast - close) / atr;
      const bool long_ema_trend =
         m5_trend_fast > m5_trend_slow &&
         slope_atr >= InpM5TrendMinSlopeAtr &&
         close > m5_trend_fast &&
         long_distance_atr <= InpM5TrendMaxDistanceAtr &&
         close > open &&
         range >= InpMinRangeAtr * atr &&
         body_fraction >= InpMinBodyFraction &&
         close_location >= InpLongCloseLocation &&
         three_bar_move_atr >= InpMinThreeBarMoveAtr;
      const bool short_ema_trend =
         m5_trend_fast < m5_trend_slow &&
         slope_atr <= -InpM5TrendMinSlopeAtr &&
         close < m5_trend_fast &&
         short_distance_atr <= InpM5TrendMaxDistanceAtr &&
         close < open &&
         range >= InpMinRangeAtr * atr &&
         body_fraction >= InpMinBodyFraction &&
         close_location <= InpShortCloseLocation &&
         three_bar_move_atr <= -InpMinThreeBarMoveAtr;
      if(long_ema_trend)
        {
         direction = "LONG";
         reason = "M5_EMA_TREND_CONTINUATION_LONG";
         break_distance_atr = long_distance_atr;
        }
      else if(short_ema_trend)
        {
         direction = "SHORT";
         reason = "M5_EMA_TREND_CONTINUATION_SHORT";
         break_distance_atr = short_distance_atr;
        }
     }
   else if(InpSignalMode == SIGNAL_D1_COMPRESSION_H4_EXPANSION)
     {
      TryD1CompressionH4ExpansionSignal(direction, reason, htf_stop_distance, break_distance_atr);
     }
   else if(InpSignalMode == SIGNAL_D1_COMPRESSION_H1_EXPANSION)
     {
      TryD1CompressionH1ExpansionSignal(direction, reason, htf_stop_distance, break_distance_atr);
     }
   else if(InpSignalMode == SIGNAL_H4_TREND_PULLBACK_D1_BIAS)
     {
      TryH4TrendPullbackD1BiasSignal(direction, reason, htf_stop_distance, break_distance_atr);
     }
   else if(InpSignalMode == SIGNAL_WEEKLY_LEVEL_H4_REJECTION)
     {
      TryWeeklyLevelH4RejectionSignal(direction, reason, htf_stop_distance, break_distance_atr);
     }
   else if(InpSignalMode == SIGNAL_DAILY_EXTREME_RECLAIM)
     {
      TryDailyExtremeReclaimSignal(signal_time, open, high, low, close, range, atr, body_fraction, close_location, direction, reason, htf_stop_distance, break_distance_atr);
     }
   else if(InpSignalMode == SIGNAL_WEEKLY_DAMAGE_H1)
     {
      TryWeeklyDamageH1Signal(direction, reason, htf_stop_distance, break_distance_atr);
     }
   else if(InpSignalMode == SIGNAL_PRIOR_DAY_LEVEL_M5)
     {
      TryPriorDayLevelM5Signal(signal_time, open, high, low, close, range, atr, body_fraction, close_location, direction, reason, htf_stop_distance, break_distance_atr);
     }
   else if(InpSignalMode == SIGNAL_EVENT_REACTION_M5)
     {
      TryEventReactionM5Signal(signal_time, open, high, low, close, range, atr, body_fraction, direction, reason, htf_stop_distance, break_distance_atr);
     }
   else if(InpSignalMode == SIGNAL_BEAR_BREAKDOWN_RETEST)
     {
      TryBearBreakdownRetestSignal(open, high, close, range, atr, body_fraction, close_location, direction, reason, htf_stop_distance, break_distance_atr);
     }
   else if(InpSignalMode == SIGNAL_BEAR_SWEEP_RECLAIM)
     {
      TryBearSweepReclaimSignal(high, close, range, atr, body_fraction, direction, reason, htf_stop_distance, break_distance_atr);
     }
   else if(InpSignalMode == SIGNAL_BEAR_LOWER_HIGH_REJECTION)
     {
      TryBearLowerHighRejectionSignal(open, high, low, close, range, atr, body_fraction, close_location, direction, reason, htf_stop_distance, break_distance_atr);
     }

   if(direction == "")
     {
      const string no_signal_reason = h4_decision_signal_mode ? "no_h4_independent_candidate" : (h1_decision_signal_mode ? "no_h1_independent_candidate" : (InpSignalMode == SIGNAL_EVENT_REACTION_M5 ? "no_event_reaction_candidate" : "no_m5_momentum_candidate"));
      LogSignal("NO_SIGNAL", "NONE", no_signal_reason, bid, ask, spread_points, recent_high, recent_low, open, high, low, close, atr, body_fraction, close_location, three_bar_move_atr, 0.0, 0.0);
      return;
     }

   if(InpMaxThreeBarMoveAtr > 0.0 && MathAbs(three_bar_move_atr) > InpMaxThreeBarMoveAtr)
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, 0.0, 0.0, 0, "", 0, 0, 0.0, "three_bar_move_atr_exceeds_cap");
      return;
     }
   if(InpMinBreakDistanceAtr > 0.0 && break_distance_atr < InpMinBreakDistanceAtr)
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, 0.0, 0.0, 0, "", 0, 0, 0.0, "break_distance_atr_below_floor");
      return;
     }
   if(InpMaxBreakDistanceAtr > 0.0 && break_distance_atr > InpMaxBreakDistanceAtr)
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, 0.0, 0.0, 0, "", 0, 0, 0.0, "break_distance_atr_exceeds_cap");
      return;
     }

   double stop_distance = htf_stop_distance > 0.0 ? htf_stop_distance : InpStopAtrMultiple * atr;
   stop_distance = MathMax(stop_distance, InpStopFloorPoints * point);
   double stop_points = stop_distance / point;
   if(InpStopCapPoints > 0 && stop_points > InpStopCapPoints)
     {
      const double cap_points = MathMax((double)InpStopCapPoints, (double)InpStopFloorPoints);
      stop_distance = cap_points * point;
      stop_points = cap_points;
     }
   const double estimated_cost_r = (stop_points > 0.0) ? (double)spread_points / stop_points : 999.0;

   LogSignal("WOULD_SIGNAL", direction, reason, bid, ask, spread_points, recent_high, recent_low, open, high, low, close, atr, body_fraction, close_location, three_bar_move_atr, break_distance_atr, estimated_cost_r);

   if(EntryHourBlocked())
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "blocked_entry_hour");
      return;
     }
   if(EntryDayHourBlocked())
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "blocked_entry_day_hour");
      return;
     }
   if(DirectionEntryHourBlocked(direction))
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "direction_blocked_entry_hour");
      return;
     }
   if(!DirectionModeAllows(direction))
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "direction_mode_block");
      return;
     }
   if(!DirectionalSessionAllows(direction))
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "directional_session_filter_block");
      return;
     }
   if(!H1TrendAllows(direction))
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "h1_trend_filter_block");
      return;
     }
   if(!H4TrendAllows(direction))
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "h4_trend_filter_block");
      return;
     }
   if(!H4D1SupportiveStateAllows(direction))
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "h4_d1_supportive_state_guard");
      return;
     }
   if(!H4D1WeeklyLossGovernorAllows())
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "h4_d1_weekly_loss_governor");
      return;
     }
   if(!D1SupportStateGateAllows())
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "d1_support_state_gate");
      return;
     }
   double close_to_recent_extreme = 0.0;
   string feature_reason = "";
   if(FeatureLossFilterBlocks(direction, recent_high, recent_low, close, close_to_recent_extreme, feature_reason))
     {
      if(InpFeatureLossFilterShadowOnly)
         LogOrder("GUARD_SHADOW", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, close_to_recent_extreme, feature_reason);
      else
        {
         LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, close_to_recent_extreme, feature_reason);
         return;
        }
     }

   if(!InpAllowDemoTrading)
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "observer_mode");
      return;
     }
   if(KillSwitchPresent())
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "kill_switch_present");
      return;
     }
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) || !MQLInfoInteger(MQL_TRADE_ALLOWED) || !AccountInfoInteger(ACCOUNT_TRADE_ALLOWED))
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "terminal_or_account_trading_disabled");
      return;
     }
   if(spread_points > InpMaxSpreadPoints)
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "spread_too_high");
      return;
     }
   if(estimated_cost_r > InpMaxEstimatedCostR)
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "estimated_cost_r_too_high");
      return;
     }
   if(InpStopCeilingPoints > 0 && stop_points > InpStopCeilingPoints)
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "stop_ceiling_exceeded");
      return;
     }
   if(InpMaxTradesPerDay > 0 && g_trades_today >= InpMaxTradesPerDay)
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "daily_trade_cap_reached");
      return;
     }
   if(InpPortfolioDailyGuardEnabled)
     {
      const int portfolio_entries_today = PortfolioEntriesToday();
      if(InpPortfolioMaxTradesPerDay > 0 && portfolio_entries_today >= InpPortfolioMaxTradesPerDay)
        {
         LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "portfolio_daily_trade_cap_reached");
         return;
        }
      const double portfolio_pnl_today = PortfolioClosedPnlToday();
      if(InpPortfolioDailyProfitTargetUsd > 0.0 && portfolio_pnl_today >= InpPortfolioDailyProfitTargetUsd)
        {
         LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "portfolio_daily_profit_target_reached");
         return;
        }
      if(InpPortfolioDailyLossStopUsd > 0.0 && portfolio_pnl_today <= -InpPortfolioDailyLossStopUsd)
        {
         LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "portfolio_daily_loss_stop_reached");
         return;
        }
      if(InpPortfolioCooldownAfterLossMinutes > 0)
        {
         const datetime last_loss_time = LastPortfolioLosingExitTimeToday();
         if(last_loss_time > 0 && TimeCurrent() - last_loss_time < InpPortfolioCooldownAfterLossMinutes * 60)
           {
            LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "portfolio_cooldown_after_loss_active");
            return;
           }
        }
     }
   if(g_last_trade_time > 0 && TimeCurrent() - g_last_trade_time < InpCooldownMinutes * 60)
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "cooldown_active");
      return;
     }
   const int own_open_positions = CountOwnOpenPositions();
   if(InpOnePositionPerMagic && own_open_positions >= 1)
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "own_position_exists");
      return;
     }
   if(!InpOnePositionPerMagic && InpMaxOpenPositionsPerMagic > 0 && own_open_positions >= InpMaxOpenPositionsPerMagic)
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "max_open_positions_reached");
      return;
     }

   double sl = 0.0;
   double tp = 0.0;
   double entry_reference = 0.0;
   bool sent = false;
   const double order_lots = LotsForStopDistance(stop_distance);
   if(order_lots <= 0.0)
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "invalid_order_lots");
      return;
     }

   if(!ClaimSignalSlot(direction, signal_time, bid, ask, spread_points, close, stop_points, estimated_cost_r))
      return;

   if(InpSplitEntryEnabled && !InpSplitEntryShadowOnly)
     {
      double first_lots = 0.0;
      double runner_lots = 0.0;
      string split_reason = "";
      if(!CalculateSplitEntryLots(order_lots, first_lots, runner_lots, split_reason))
        {
         LogOrder("GUARD_BLOCK", direction, order_lots, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, split_reason);
         return;
        }

      double first_sl = 0.0;
      double first_tp = 0.0;
      double runner_sl = 0.0;
      double runner_tp = 0.0;
      if(direction == "LONG")
        {
         entry_reference = ask;
         first_sl = NormalizeDouble(ask - stop_distance, digits);
         first_tp = NormalizeDouble(ask + InpSplitEntryFirstTargetR * stop_distance, digits);
         runner_sl = first_sl;
         runner_tp = NormalizeDouble(ask + InpSplitEntryRunnerTargetR * stop_distance, digits);
         sent = g_trade.Buy(first_lots, InpTargetSymbol, 0.0, first_sl, first_tp, InpOrderComment + "_TP1");
        }
      else
        {
         entry_reference = bid;
         first_sl = NormalizeDouble(bid + stop_distance, digits);
         first_tp = NormalizeDouble(bid - InpSplitEntryFirstTargetR * stop_distance, digits);
         runner_sl = first_sl;
         runner_tp = NormalizeDouble(bid - InpSplitEntryRunnerTargetR * stop_distance, digits);
         sent = g_trade.Sell(first_lots, InpTargetSymbol, 0.0, first_sl, first_tp, InpOrderComment + "_TP1");
        }

      const long first_retcode = (long)g_trade.ResultRetcode();
      const string first_retcode_description = g_trade.ResultRetcodeDescription();
      LogOrder(sent ? "SPLIT_TP1_ORDER_SEND_OK" : "SPLIT_TP1_ORDER_SEND_FAIL", direction, first_lots, bid, ask, spread_points, entry_reference, first_sl, first_tp, stop_points, estimated_cost_r, first_retcode, first_retcode_description, g_trade.ResultOrder(), g_trade.ResultDeal(), g_trade.ResultPrice(), sent ? split_reason : "split_tp1_order_failed");
      if(!sent)
         return;

      bool runner_sent = false;
      if(direction == "LONG")
         runner_sent = g_trade.Buy(runner_lots, InpTargetSymbol, 0.0, runner_sl, runner_tp, InpOrderComment + "_RUN");
      else
         runner_sent = g_trade.Sell(runner_lots, InpTargetSymbol, 0.0, runner_sl, runner_tp, InpOrderComment + "_RUN");

      const long runner_retcode = (long)g_trade.ResultRetcode();
      const string runner_retcode_description = g_trade.ResultRetcodeDescription();
      LogOrder(runner_sent ? "SPLIT_RUNNER_ORDER_SEND_OK" : "SPLIT_RUNNER_ORDER_SEND_FAIL", direction, runner_lots, bid, ask, spread_points, entry_reference, runner_sl, runner_tp, stop_points, estimated_cost_r, runner_retcode, runner_retcode_description, g_trade.ResultOrder(), g_trade.ResultDeal(), g_trade.ResultPrice(), runner_sent ? split_reason : "split_runner_order_failed");

      g_trades_today++;
      g_last_trade_time = TimeCurrent();
      return;
     }

   if(direction == "LONG")
     {
      entry_reference = ask;
      sl = NormalizeDouble(ask - stop_distance, digits);
      tp = NormalizeDouble(ask + EffectiveInitialTargetR() * stop_distance, digits);
      sent = g_trade.Buy(order_lots, InpTargetSymbol, 0.0, sl, tp, InpOrderComment);
     }
   else
     {
      entry_reference = bid;
      sl = NormalizeDouble(bid + stop_distance, digits);
      tp = NormalizeDouble(bid - EffectiveInitialTargetR() * stop_distance, digits);
      sent = g_trade.Sell(order_lots, InpTargetSymbol, 0.0, sl, tp, InpOrderComment);
     }

   const long retcode = (long)g_trade.ResultRetcode();
   const string retcode_description = g_trade.ResultRetcodeDescription();
   if(sent)
     {
      g_trades_today++;
      g_last_trade_time = TimeCurrent();
      LogOrder("ORDER_SEND_OK", direction, order_lots, bid, ask, spread_points, entry_reference, sl, tp, stop_points, estimated_cost_r, retcode, retcode_description, g_trade.ResultOrder(), g_trade.ResultDeal(), g_trade.ResultPrice(), "pass");
     }
   else
      LogOrder("ORDER_SEND_FAIL", direction, order_lots, bid, ask, spread_points, entry_reference, sl, tp, stop_points, estimated_cost_r, retcode, retcode_description, g_trade.ResultOrder(), g_trade.ResultDeal(), g_trade.ResultPrice(), "order_send_failed");
  }
//+------------------------------------------------------------------+

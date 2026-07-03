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
   SIGNAL_M5_EMA_TREND_CONTINUATION = 5
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
input double InpMinAtrAbsoluteForEntry        = 0.00;   // 0 disables absolute ATR floor
input double InpStopAtrMultiple               = 2.50;
input int    InpStopFloorPoints               = 350;
input int    InpStopCeilingPoints             = 1800;
input double InpRiskReward                    = 1.50;
input string InpBlockedEntryHoursCsv          = "";     // comma-separated server hours, e.g. "9,10"
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
input double InpSplitEntryRunnerTargetR       = 2.00;
input bool   InpSplitEntryMoveRunnerSLToBE    = true;
input bool   InpSplitEntryUseMinLotPair       = false;
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
datetime g_last_trade_time = 0;
string   g_trade_day = "";
int      g_trades_today = 0;

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
     }
   const int n = ArraySize(values);
   switch(n)
     {
      case 9:  FileWrite(handle, values[0], values[1], values[2], values[3], values[4], values[5], values[6], values[7], values[8]); break;
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
   if(!InpSplitEntryEnabled || InpSplitEntryShadowOnly || !InpSplitEntryMoveRunnerSLToBE)
      return;
   if(trans.type != TRADE_TRANSACTION_DEAL_ADD || trans.deal == 0)
      return;
   if(!HistoryDealSelect(trans.deal))
      return;
   if((long)HistoryDealGetInteger(trans.deal, DEAL_MAGIC) != InpMagicNumber ||
      HistoryDealGetString(trans.deal, DEAL_SYMBOL) != InpTargetSymbol)
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

   if(total_lots >= 2.0 * min_lots)
     {
      first_lots = MathFloor((total_lots * 0.5) / step + 0.0000001) * step;
      if(first_lots < min_lots)
         first_lots = min_lots;
      runner_lots = NormalizeDouble(total_lots - first_lots, 2);
      first_lots = NormalizeDouble(first_lots, 2);
      if(first_lots >= min_lots && runner_lots >= min_lots)
         return true;
     }

   if(InpSplitEntryUseMinLotPair)
     {
      first_lots = NormalizeDouble(min_lots, 2);
      runner_lots = NormalizeDouble(min_lots, 2);
      reason = "min_lot_pair_doubles_small_position";
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
   if(!InpProfitProtectionEnabled && !InpPartialCloseEnabled && !InpSplitEntryEnabled)
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
      if(InpSplitEntryEnabled && !InpSplitEntryShadowOnly && InpSplitEntryMoveRunnerSLToBE &&
         TextContains(position_comment, "_RUN") && unrealized_r >= InpSplitEntryFirstTargetR &&
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
            LogManagement(split_be_ok ? "SPLIT_RUNNER_BE_MODIFY_OK" : "SPLIT_RUNNER_BE_MODIFY_FAIL", direction, ticket, volume, entry_price, current_price, current_sl, break_even_sl, tp, risk_points, unrealized_r, split_be_retcode, split_be_ok ? "pass" : "split_runner_be_failed", InpSplitEntryFirstTargetR, InpSplitEntryRunnerTargetR);
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

void EvaluateCompletedM5Bar()
  {
   ResetDailyCounterIfNeeded();

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
   else if(InpSignalMode == SIGNAL_OPENING_RANGE_CONTINUATION)
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

   if(direction == "")
     {
      LogSignal("NO_SIGNAL", "NONE", "no_m5_momentum_candidate", bid, ask, spread_points, recent_high, recent_low, open, high, low, close, atr, body_fraction, close_location, three_bar_move_atr, 0.0, 0.0);
      return;
     }

   if(InpMaxThreeBarMoveAtr > 0.0 && MathAbs(three_bar_move_atr) > InpMaxThreeBarMoveAtr)
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, 0.0, 0.0, 0, "", 0, 0, 0.0, "three_bar_move_atr_exceeds_cap");
      return;
     }

   double stop_distance = MathMax(InpStopAtrMultiple * atr, InpStopFloorPoints * point);
   const double stop_points = stop_distance / point;
   const double estimated_cost_r = (stop_points > 0.0) ? (double)spread_points / stop_points : 999.0;

   LogSignal("WOULD_SIGNAL", direction, reason, bid, ask, spread_points, recent_high, recent_low, open, high, low, close, atr, body_fraction, close_location, three_bar_move_atr, break_distance_atr, estimated_cost_r);

   if(EntryHourBlocked())
     {
      LogOrder("GUARD_BLOCK", direction, 0.0, bid, ask, spread_points, close, 0.0, 0.0, stop_points, estimated_cost_r, 0, "", 0, 0, 0.0, "blocked_entry_hour");
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

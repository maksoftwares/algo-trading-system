#property strict
#property version   "1.00"
#property description "EURUSD M15 RSI health-gate prospective observer; zero order capability"

input string InpRunId = "EURUSD_RSI_HEALTH_GATE_FORWARD_V1";
input string InpTargetSymbol = "EURUSD";
input long InpObserverId = 26073093;
input long InpAllowedAccountLogin = 0;
input string InpAllowedServer = "";
input bool InpRequireDemoAccount = true;
input string InpProspectiveStartUtc = "2026.08.01 00:00";
input int InpBrokerUtcOffsetHours = 0;
input bool InpResetPersistentState = false;
input string InpAuditLogName =
   "EURUSD_RSI_HEALTH_GATE_PROSPECTIVE_OBSERVER.csv";

const int STATE_SCHEMA = 1;
const long CONTRACT_FINGERPRINT = 2607300101;
const int ATR_PERIOD = 14;
const int BANDS_PERIOD = 20;
const int RSI_PERIOD = 14;
const double RSI_OVERSOLD_INCLUSIVE = 30.0;
const double MINIMUM_BODY_FRACTION = 0.4;
const int RECENT_STOP_LOOKBACK_M15_BARS = 6;
const double STOP_ATR_MULTIPLE = 1.4;
const double STOP_FLOOR_PIPS = 3.0;
const double STOP_CEILING_PIPS = 70.0;
const double TARGET_R = 0.8;
const double MAXIMUM_ENTRY_SPREAD_PIPS = 10.0;
const int MAXIMUM_TRADES_PER_UTC_DAY = 20;
const double ADVERSE_SLIPPAGE_PIPS_PER_SIDE = 0.1;
const int HEALTH_LOOKBACK_COMPLETED_TRADES = 30;
const double HEALTH_MINIMUM_PROFIT_FACTOR = 1.05;
const double USD_PER_PIP_AT_001_LOT = 1.0;

int atrHandle = INVALID_HANDLE;
int bandsHandle = INVALID_HANDLE;
int rsiHandle = INVALID_HANDLE;
datetime prospectiveStart = 0;
datetime lastM15Open = 0;
datetime virtualEntryTime = 0;
datetime lastVirtualExitTime = 0;
int dailyDateKey = 0;
int dailyEntryCount = 0;
bool virtualActive = false;
bool virtualAdmitted = false;
double virtualEntry = 0.0;
double virtualStop = 0.0;
double virtualTarget = 0.0;
double virtualStopPips = 0.0;
double virtualEntryTrailingPf = 0.0;
int virtualEntryBufferCount = 0;
double healthOutcomes[30];
int healthCount = 0;
int healthHead = 0;
string statePrefix = "";
string mutexName = "";
bool mutexOwned = false;
bool stateReady = false;
datetime lastPeriodicStateSave = 0;

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

datetime BrokerToUtc(const datetime brokerTime)
{
   return brokerTime - InpBrokerUtcOffsetHours * 3600;
}

int UtcDateKey(const datetime brokerTime)
{
   MqlDateTime parts;
   TimeToStruct(BrokerToUtc(brokerTime), parts);
   return parts.year * 10000 + parts.mon * 100 + parts.day;
}

int UtcHour(const datetime brokerTime)
{
   MqlDateTime parts;
   TimeToStruct(BrokerToUtc(brokerTime), parts);
   return parts.hour;
}

bool IsBlockedEntryHour(const int hour)
{
   return hour == 1 || hour == 7 || hour == 21;
}

double TrailingProfitFactor()
{
   double gains = 0.0;
   double losses = 0.0;
   for(int index = 0; index < healthCount; ++index)
   {
      double value = healthOutcomes[index];
      if(value > 0.0)
         gains += value;
      else if(value < 0.0)
         losses -= value;
   }
   if(losses <= 0.0)
      return gains > 0.0 ? DBL_MAX : 0.0;
   return gains / losses;
}

void Audit(
   const string eventName,
   const string detail,
   const datetime signalTime = 0,
   const double entry = 0.0,
   const double stop = 0.0,
   const double target = 0.0,
   const double exitPrice = 0.0,
   const double pnlPips = 0.0,
   const double pnlUsd = 0.0,
   const bool admitted = false
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
      PrintFormat("EURUSD_RSI_HEALTH audit open failed err=%d", GetLastError());
      return;
   }
   if(FileSize(handle) <= 2)
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
         "observer_id",
         "signal_time_utc",
         "entry",
         "stop",
         "target",
         "exit",
         "pnl_pips",
         "pnl_usd_001_lot",
         "health_buffer_count",
         "trailing_profit_factor",
         "health_gate_admitted",
         "virtual_active"
      );
   FileSeek(handle, 0, SEEK_END);
   double factor = TrailingProfitFactor();
   string factorText =
      factor == DBL_MAX ? "INF" : DoubleToString(factor, 8);
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
      InpObserverId,
      signalTime > 0
         ? TimeToString(BrokerToUtc(signalTime), TIME_DATE | TIME_SECONDS)
         : "",
      DoubleToString(entry, _Digits),
      DoubleToString(stop, _Digits),
      DoubleToString(target, _Digits),
      DoubleToString(exitPrice, _Digits),
      DoubleToString(pnlPips, 4),
      DoubleToString(pnlUsd, 4),
      healthCount,
      factorText,
      BoolText(admitted),
      BoolText(virtualActive)
   );
   FileClose(handle);
}

string StateName(const string suffix)
{
   return statePrefix + suffix;
}

bool ReadRequiredState(const string suffix, double &value)
{
   string name = StateName(suffix);
   if(!GlobalVariableCheck(name))
      return false;
   value = GlobalVariableGet(name);
   return true;
}

void SaveState()
{
   if((bool)MQLInfoInteger(MQL_TESTER) || !stateReady)
      return;
   GlobalVariableDel(StateName("SCHEMA"));
   GlobalVariablesFlush();
   GlobalVariableSet(StateName("CONTRACT"), (double)CONTRACT_FINGERPRINT);
   GlobalVariableSet(StateName("START"), (double)prospectiveStart);
   GlobalVariableSet(StateName("LASTBAR"), (double)lastM15Open);
   GlobalVariableSet(StateName("LASTEXIT"), (double)lastVirtualExitTime);
   GlobalVariableSet(StateName("DAY"), (double)dailyDateKey);
   GlobalVariableSet(StateName("DAYCOUNT"), (double)dailyEntryCount);
   GlobalVariableSet(StateName("ACTIVE"), virtualActive ? 1.0 : 0.0);
   GlobalVariableSet(StateName("ADMITTED"), virtualAdmitted ? 1.0 : 0.0);
   GlobalVariableSet(StateName("ENTRYTIME"), (double)virtualEntryTime);
   GlobalVariableSet(StateName("ENTRY"), virtualEntry);
   GlobalVariableSet(StateName("STOP"), virtualStop);
   GlobalVariableSet(StateName("TARGET"), virtualTarget);
   GlobalVariableSet(StateName("STOPPIPS"), virtualStopPips);
   GlobalVariableSet(StateName("ENTRYPF"), virtualEntryTrailingPf);
   GlobalVariableSet(
      StateName("ENTRYCOUNT"),
      (double)virtualEntryBufferCount
   );
   GlobalVariableSet(StateName("HEALTHCOUNT"), (double)healthCount);
   GlobalVariableSet(StateName("HEALTHHEAD"), (double)healthHead);
   for(int index = 0; index < HEALTH_LOOKBACK_COMPLETED_TRADES; ++index)
      GlobalVariableSet(
         StateName(StringFormat("R%02d", index)),
         healthOutcomes[index]
      );
   GlobalVariablesFlush();
   GlobalVariableSet(StateName("SCHEMA"), (double)STATE_SCHEMA);
   GlobalVariablesFlush();
}

void DeletePersistentState()
{
   string suffixes[] = {
      "SCHEMA", "CONTRACT", "START", "LASTBAR", "LASTEXIT", "DAY",
      "DAYCOUNT", "ACTIVE", "ADMITTED", "ENTRYTIME", "ENTRY", "STOP",
      "TARGET", "STOPPIPS", "ENTRYPF", "ENTRYCOUNT", "HEALTHCOUNT",
      "HEALTHHEAD"
   };
   for(int index = 0; index < ArraySize(suffixes); ++index)
      GlobalVariableDel(StateName(suffixes[index]));
   for(int ringIndex = 0;
       ringIndex < HEALTH_LOOKBACK_COMPLETED_TRADES;
       ++ringIndex)
      GlobalVariableDel(StateName(StringFormat("R%02d", ringIndex)));
   GlobalVariablesFlush();
}

void InitializeEmptyState()
{
   ArrayInitialize(healthOutcomes, 0.0);
   lastM15Open = iTime(_Symbol, PERIOD_M15, 0);
   lastVirtualExitTime = 0;
   dailyDateKey = UtcDateKey(TimeCurrent());
   dailyEntryCount = 0;
   virtualActive = false;
   virtualAdmitted = false;
   virtualEntryTime = 0;
   virtualEntry = 0.0;
   virtualStop = 0.0;
   virtualTarget = 0.0;
   virtualStopPips = 0.0;
   virtualEntryTrailingPf = 0.0;
   virtualEntryBufferCount = 0;
   healthCount = 0;
   healthHead = 0;
}

bool RestoreState(string &reason)
{
   if((bool)MQLInfoInteger(MQL_TESTER))
   {
      InitializeEmptyState();
      if(lastM15Open <= 0)
      {
         reason = "tester_m15_bar_unavailable";
         return false;
      }
      stateReady = true;
      reason = "tester_empty_state";
      return true;
   }
   if(!GlobalVariableCheck(StateName("SCHEMA")))
   {
      InitializeEmptyState();
      if(lastM15Open <= 0)
      {
         reason = "new_state_m15_bar_unavailable";
         return false;
      }
      stateReady = true;
      SaveState();
      reason = "new_empty_state";
      return true;
   }

   double schema = 0.0;
   double contract = 0.0;
   double start = 0.0;
   if(
      !ReadRequiredState("SCHEMA", schema)
      || !ReadRequiredState("CONTRACT", contract)
      || !ReadRequiredState("START", start)
   )
   {
      reason = "state_header_incomplete";
      return false;
   }
   if((int)schema != STATE_SCHEMA)
   {
      reason = "state_schema_mismatch";
      return false;
   }
   if((long)contract != CONTRACT_FINGERPRINT)
   {
      reason = "state_contract_mismatch";
      return false;
   }
   if((datetime)start != prospectiveStart)
   {
      reason = "state_prospective_floor_mismatch";
      return false;
   }

   double value = 0.0;
   if(!ReadRequiredState("LASTBAR", value))
   {
      reason = "state_lastbar_missing";
      return false;
   }
   lastM15Open = (datetime)value;
   if(!ReadRequiredState("LASTEXIT", value))
   {
      reason = "state_lastexit_missing";
      return false;
   }
   lastVirtualExitTime = (datetime)value;
   if(!ReadRequiredState("DAY", value))
   {
      reason = "state_day_missing";
      return false;
   }
   dailyDateKey = (int)value;
   if(!ReadRequiredState("DAYCOUNT", value))
   {
      reason = "state_daycount_missing";
      return false;
   }
   dailyEntryCount = (int)value;
   if(!ReadRequiredState("ACTIVE", value))
   {
      reason = "state_active_missing";
      return false;
   }
   virtualActive = value > 0.5;
   if(!ReadRequiredState("ADMITTED", value))
   {
      reason = "state_admitted_missing";
      return false;
   }
   virtualAdmitted = value > 0.5;
   if(!ReadRequiredState("ENTRYTIME", value))
   {
      reason = "state_entrytime_missing";
      return false;
   }
   virtualEntryTime = (datetime)value;
   if(!ReadRequiredState("ENTRY", virtualEntry)
      || !ReadRequiredState("STOP", virtualStop)
      || !ReadRequiredState("TARGET", virtualTarget)
      || !ReadRequiredState("STOPPIPS", virtualStopPips)
      || !ReadRequiredState("ENTRYPF", virtualEntryTrailingPf))
   {
      reason = "state_virtual_prices_incomplete";
      return false;
   }
   if(!ReadRequiredState("ENTRYCOUNT", value))
   {
      reason = "state_entrycount_missing";
      return false;
   }
   virtualEntryBufferCount = (int)value;
   if(!ReadRequiredState("HEALTHCOUNT", value))
   {
      reason = "state_healthcount_missing";
      return false;
   }
   healthCount = (int)value;
   if(!ReadRequiredState("HEALTHHEAD", value))
   {
      reason = "state_healthhead_missing";
      return false;
   }
   healthHead = (int)value;
   if(
      lastM15Open <= 0
      || healthCount < 0
      || healthCount > HEALTH_LOOKBACK_COMPLETED_TRADES
      || healthHead < 0
      || healthHead >= HEALTH_LOOKBACK_COMPLETED_TRADES
      || dailyEntryCount < 0
      || dailyEntryCount > MAXIMUM_TRADES_PER_UTC_DAY
   )
   {
      reason = "state_bounds_invalid";
      return false;
   }
   for(int index = 0; index < HEALTH_LOOKBACK_COMPLETED_TRADES; ++index)
   {
      if(
         !ReadRequiredState(
            StringFormat("R%02d", index),
            healthOutcomes[index]
         )
      )
      {
         reason = "state_health_ring_incomplete";
         return false;
      }
   }
   if(
      virtualActive
      && (
         virtualEntryTime <= 0
         || virtualEntry <= 0.0
         || virtualStop <= 0.0
         || virtualTarget <= virtualEntry
         || virtualStop >= virtualEntry
         || virtualStopPips <= 0.0
      )
   )
   {
      reason = "state_active_virtual_trade_invalid";
      return false;
   }
   stateReady = true;
   reason = "persistent_state_restored";
   return true;
}

bool AcquireMutex()
{
   mutexName = statePrefix + "MUTEX";
   double now = (double)TimeLocal();
   if(GlobalVariableCheck(mutexName))
   {
      double heartbeat = GlobalVariableGet(mutexName);
      if(now - heartbeat < 6.0)
         return false;
   }
   GlobalVariableSet(mutexName, now);
   mutexOwned = true;
   EventSetTimer(2);
   return true;
}

void PushHealthOutcome(const double pnlPips)
{
   healthOutcomes[healthHead] = pnlPips;
   healthHead =
      (healthHead + 1) % HEALTH_LOOKBACK_COMPLETED_TRADES;
   if(healthCount < HEALTH_LOOKBACK_COMPLETED_TRADES)
      healthCount++;
}

void ClearVirtualTrade()
{
   virtualActive = false;
   virtualAdmitted = false;
   virtualEntryTime = 0;
   virtualEntry = 0.0;
   virtualStop = 0.0;
   virtualTarget = 0.0;
   virtualStopPips = 0.0;
   virtualEntryTrailingPf = 0.0;
   virtualEntryBufferCount = 0;
}

bool ResolveVirtualTrade(const MqlTick &tick)
{
   if(!virtualActive)
      return false;

   string exitReason = "";
   double exitPrice = 0.0;
   double slippage = ADVERSE_SLIPPAGE_PIPS_PER_SIDE * PipSize();
   if(tick.bid <= virtualStop)
   {
      exitReason = "STOP_FIRST";
      exitPrice = virtualStop - slippage;
   }
   else if(tick.bid >= virtualTarget)
   {
      exitReason = "TARGET";
      exitPrice = virtualTarget - slippage;
   }
   else
      return false;

   double entry = virtualEntry;
   double stop = virtualStop;
   double target = virtualTarget;
   datetime entryTime = virtualEntryTime;
   bool admitted = virtualAdmitted;
   double pnlPips = (exitPrice - entry) / PipSize();
   double pnlUsd = pnlPips * USD_PER_PIP_AT_001_LOT;
   PushHealthOutcome(pnlPips);
   lastVirtualExitTime = TimeCurrent();
   ClearVirtualTrade();
   SaveState();
   Audit(
      "VIRTUAL_CLOSE",
      exitReason,
      entryTime,
      entry,
      stop,
      target,
      exitPrice,
      pnlPips,
      pnlUsd,
      admitted
   );
   return true;
}

bool ReadSignalInputs(
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
         RECENT_STOP_LOOKBACK_M15_BARS,
         bars
      ) != RECENT_STOP_LOOKBACK_M15_BARS
   )
      return false;
   signalBar = bars[0];
   recentLow = bars[0].low;
   for(int index = 1; index < ArraySize(bars); ++index)
      recentLow = MathMin(recentLow, bars[index].low);

   double values[];
   ArraySetAsSeries(values, true);
   if(CopyBuffer(atrHandle, 0, 1, 1, values) != 1)
      return false;
   atr = values[0];
   if(CopyBuffer(bandsHandle, 0, 1, 1, values) != 1)
      return false;
   bandMid = values[0];
   if(CopyBuffer(rsiHandle, 0, 1, 1, values) != 1)
      return false;
   rsi = values[0];
   return (
      atr > 0.0
      && bandMid > 0.0
      && rsi >= 0.0
      && rsi <= 100.0
      && recentLow > 0.0
   );
}

void EvaluateCompletedBar(
   const datetime newBarOpen,
   const bool resolvedOnThisTick
)
{
   if(BrokerToUtc(newBarOpen) < prospectiveStart)
      return;
   if(virtualActive)
      return;
   if(resolvedOnThisTick || lastVirtualExitTime >= newBarOpen)
   {
      Audit("SIGNAL_BLOCK", "same_bar_as_virtual_exit", newBarOpen - 900);
      return;
   }

   int dateKey = UtcDateKey(newBarOpen);
   if(dateKey != dailyDateKey)
   {
      dailyDateKey = dateKey;
      dailyEntryCount = 0;
   }
   if(dailyEntryCount >= MAXIMUM_TRADES_PER_UTC_DAY)
   {
      Audit("SIGNAL_BLOCK", "daily_virtual_trade_cap", newBarOpen - 900);
      SaveState();
      return;
   }
   int entryHour = UtcHour(newBarOpen);
   if(IsBlockedEntryHour(entryHour))
      return;

   MqlRates signalBar;
   double atr = 0.0;
   double bandMid = 0.0;
   double rsi = 0.0;
   double recentLow = 0.0;
   if(!ReadSignalInputs(signalBar, atr, bandMid, rsi, recentLow))
   {
      Audit("SIGNAL_BLOCK", "indicator_or_bar_data_unavailable");
      return;
   }
   if(BrokerToUtc(signalBar.time) < prospectiveStart)
      return;
   double range = signalBar.high - signalBar.low;
   double bodyFraction =
      range > 0.0
         ? MathAbs(signalBar.close - signalBar.open) / range
         : 0.0;
   if(
      rsi > RSI_OVERSOLD_INCLUSIVE
      || signalBar.close >= bandMid
      || bodyFraction < MINIMUM_BODY_FRACTION
   )
      return;

   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick))
   {
      Audit("SIGNAL_BLOCK", "entry_tick_unavailable", signalBar.time);
      return;
   }
   double spreadPips = (tick.ask - tick.bid) / PipSize();
   if(spreadPips > MAXIMUM_ENTRY_SPREAD_PIPS)
   {
      Audit("SIGNAL_BLOCK", "maximum_entry_spread", signalBar.time);
      return;
   }

   double slippage = ADVERSE_SLIPPAGE_PIPS_PER_SIDE * PipSize();
   double entry = tick.ask + slippage;
   double minimumStopDistance = MathMax(
      STOP_ATR_MULTIPLE * atr,
      STOP_FLOOR_PIPS * PipSize()
   );
   double stop = MathMin(recentLow, entry - minimumStopDistance);
   double stopPips = (entry - stop) / PipSize();
   if(stopPips > STOP_CEILING_PIPS)
   {
      Audit(
         "SIGNAL_BLOCK",
         "maximum_stop_distance",
         signalBar.time,
         entry,
         stop
      );
      return;
   }
   double target = entry + TARGET_R * (entry - stop);
   double factor = TrailingProfitFactor();
   bool admitted =
      healthCount == HEALTH_LOOKBACK_COMPLETED_TRADES
      && factor >= HEALTH_MINIMUM_PROFIT_FACTOR;

   virtualActive = true;
   virtualAdmitted = admitted;
   virtualEntryTime = newBarOpen;
   virtualEntry = NormalizeDouble(entry, _Digits);
   virtualStop = NormalizeDouble(stop, _Digits);
   virtualTarget = NormalizeDouble(target, _Digits);
   virtualStopPips = stopPips;
   virtualEntryTrailingPf = factor;
   virtualEntryBufferCount = healthCount;
   dailyEntryCount++;
   SaveState();
   Audit(
      "VIRTUAL_OPEN",
      admitted ? "health_gate_admitted" : "health_gate_rejected",
      signalBar.time,
      virtualEntry,
      virtualStop,
      virtualTarget,
      0.0,
      0.0,
      0.0,
      admitted
   );
}

int OnInit()
{
   if(_Symbol != InpTargetSymbol || _Period != PERIOD_M15)
      return INIT_PARAMETERS_INCORRECT;
   if(InpObserverId <= 0)
      return INIT_PARAMETERS_INCORRECT;
   prospectiveStart = StringToTime(InpProspectiveStartUtc);
   if(prospectiveStart <= 0)
      return INIT_PARAMETERS_INCORRECT;
   if(
      !(bool)MQLInfoInteger(MQL_TESTER)
      && InpRequireDemoAccount
      && (ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)
         != ACCOUNT_TRADE_MODE_DEMO
   )
      return INIT_FAILED;
   if(
      !(bool)MQLInfoInteger(MQL_TESTER)
      && InpAllowedAccountLogin > 0
      && AccountInfoInteger(ACCOUNT_LOGIN) != InpAllowedAccountLogin
   )
      return INIT_FAILED;
   if(
      !(bool)MQLInfoInteger(MQL_TESTER)
      && InpAllowedServer != ""
      && AccountInfoString(ACCOUNT_SERVER) != InpAllowedServer
   )
      return INIT_FAILED;

   statePrefix = StringFormat(
      "CDX_RSIHG_%I64d_%I64d_",
      AccountInfoInteger(ACCOUNT_LOGIN),
      InpObserverId
   );
   if(!AcquireMutex())
   {
      Audit("INIT_FAILED", "duplicate_instance_mutex");
      return INIT_FAILED;
   }

   atrHandle = iATR(_Symbol, PERIOD_M15, ATR_PERIOD);
   bandsHandle = iBands(
      _Symbol,
      PERIOD_M15,
      BANDS_PERIOD,
      0,
      2.0,
      PRICE_CLOSE
   );
   rsiHandle = iRSI(_Symbol, PERIOD_M15, RSI_PERIOD, PRICE_CLOSE);
   if(
      atrHandle == INVALID_HANDLE
      || bandsHandle == INVALID_HANDLE
      || rsiHandle == INVALID_HANDLE
   )
   {
      Audit("INIT_FAILED", "indicator_handle_invalid");
      return INIT_FAILED;
   }

   if(InpResetPersistentState && !(bool)MQLInfoInteger(MQL_TESTER))
   {
      DeletePersistentState();
      Audit("STATE_RESET", "operator_requested_empty_state");
   }
   string restoreReason = "";
   if(!RestoreState(restoreReason))
   {
      Audit("INIT_FAILED", restoreReason);
      return INIT_FAILED;
   }
   if(lastM15Open <= 0)
   {
      Audit("INIT_FAILED", "current_m15_bar_unavailable");
      return INIT_FAILED;
   }
   Audit(
      restoreReason == "persistent_state_restored"
         ? "STATE_RESTORED"
         : "STATE_INITIALIZED",
      restoreReason
   );
   Audit(
      "INIT_OK",
      (bool)MQLInfoInteger(MQL_TESTER)
         ? "tester_zero_order_observer"
         : "demo_zero_order_observer"
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
   datetime now = TimeLocal();
   if(now - lastPeriodicStateSave >= 30)
   {
      SaveState();
      lastPeriodicStateSave = now;
   }
}

void OnDeinit(const int reason)
{
   SaveState();
   Audit("DEINIT", IntegerToString(reason));
   EventKillTimer();
   if(mutexOwned && GlobalVariableCheck(mutexName))
      GlobalVariableDel(mutexName);
   if(atrHandle != INVALID_HANDLE)
      IndicatorRelease(atrHandle);
   if(bandsHandle != INVALID_HANDLE)
      IndicatorRelease(bandsHandle);
   if(rsiHandle != INVALID_HANDLE)
      IndicatorRelease(rsiHandle);
}

void OnTick()
{
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick))
      return;
   bool resolvedOnThisTick = ResolveVirtualTrade(tick);
   datetime currentM15Open = iTime(_Symbol, PERIOD_M15, 0);
   if(currentM15Open <= 0 || currentM15Open == lastM15Open)
      return;
   lastM15Open = currentM15Open;
   SaveState();
   EvaluateCompletedBar(currentM15Open, resolvedOnThisTick);
}

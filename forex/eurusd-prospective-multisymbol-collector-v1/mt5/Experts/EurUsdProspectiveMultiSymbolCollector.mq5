#property strict
#property version   "1.00"
#property description "Read-only prospective EURUSD multi-symbol M5 tick collector"

input string InpRunId = "EURUSD_PROSPECTIVE_MULTISYMBOL_V1";
input string InpTargetSymbol = "EURUSD";
input string InpReferenceSymbols =
   "EURUSD,EURGBP,EURJPY,GBPUSD,USDJPY,GBPJPY,DOLLARIDXUSD,USTBONDTRUSD";
input string InpProspectiveStartUtc = "2026.08.01 00:00";
input int InpBrokerUtcOffsetSeconds = 0;
input int InpTimerSeconds = 5;
input int InpHeartbeatSeconds = 60;
input string InpFeatureLogName = "EURUSD_PROSPECTIVE_M5_FEATURES_V1.csv";
input string InpEnvironmentLogName =
   "EURUSD_PROSPECTIVE_M5_ENVIRONMENT_V1.csv";
input string InpHeartbeatLogName =
   "EURUSD_PROSPECTIVE_M5_HEARTBEAT_V1.csv";

const string FROZEN_FORWARD_FLOOR_UTC = "2026.08.01 00:00";

struct QuoteAggregate
{
   int copied_ticks;
   int valid_quotes;
   ulong first_tick_msc;
   ulong last_tick_msc;
   double first_bid;
   double first_ask;
   double last_bid;
   double last_ask;
   double bid_high;
   double bid_low;
   double ask_high;
   double ask_low;
   double spread_min_points;
   double spread_sum_points;
   double spread_max_points;
   int spread_samples;
};

string sourceSymbols[];
datetime lastSeenM5Open = 0;
datetime lastCompletedM5Open = 0;
datetime lastHeartbeatLocal = 0;
string mutexName = "";
bool mutexOwned = false;
int lastOkRows = 0;
int lastMissingRows = 0;

string BoolText(const bool value)
{
   return value ? "true" : "false";
}

string TimeText(const datetime value)
{
   if(value <= 0)
      return "";
   return TimeToString(value, TIME_DATE | TIME_SECONDS);
}

string MillisecondTimeText(const ulong value)
{
   if(value == 0)
      return "";
   return TimeText((datetime)(value / 1000));
}

datetime BrokerToConfiguredUtc(const datetime brokerTime)
{
   return brokerTime - InpBrokerUtcOffsetSeconds;
}

datetime CurrentConfiguredUtc()
{
   if((bool)MQLInfoInteger(MQL_TESTER))
      return BrokerToConfiguredUtc(TimeCurrent());
   return TimeGMT();
}

string EvidenceScope()
{
   return (bool)MQLInfoInteger(MQL_TESTER)
      ? "TESTER_SMOKE_NOT_FORWARD"
      : "PROSPECTIVE_DEMO";
}

int OpenAppendCsv(const string fileName)
{
   int handle = FileOpen(
      fileName,
      FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON
         | FILE_SHARE_READ | FILE_SHARE_WRITE,
      ','
   );
   if(handle != INVALID_HANDLE)
      FileSeek(handle, 0, SEEK_END);
   return handle;
}

bool EnsureFeatureHeader()
{
   int handle = OpenAppendCsv(InpFeatureLogName);
   if(handle == INVALID_HANDLE)
      return false;
   if(FileSize(handle) == 0)
   {
      FileWrite(
         handle,
         "recorded_at_broker",
         "recorded_at_utc",
         "evidence_scope",
         "run_id",
         "account_login",
         "account_server",
         "terminal_build",
         "target_symbol",
         "source_symbol",
         "interval_open_broker",
         "interval_close_broker_exclusive",
         "interval_open_configured_utc",
         "interval_close_configured_utc_exclusive",
         "configured_broker_utc_offset_seconds",
         "source_status",
         "terminal_error_code",
         "copied_tick_count",
         "valid_two_sided_quote_count",
         "first_tick_msc",
         "last_tick_msc",
         "first_tick_time",
         "last_tick_time",
         "first_bid",
         "bid_high",
         "bid_low",
         "last_bid",
         "first_ask",
         "ask_high",
         "ask_low",
         "last_ask",
         "spread_min_points",
         "spread_mean_points",
         "spread_max_points",
         "symbol_digits",
         "symbol_point"
      );
      FileFlush(handle);
   }
   FileClose(handle);
   return true;
}

bool EnsureEnvironmentHeader()
{
   int handle = OpenAppendCsv(InpEnvironmentLogName);
   if(handle == INVALID_HANDLE)
      return false;
   if(FileSize(handle) == 0)
   {
      FileWrite(
         handle,
         "recorded_at_broker",
         "recorded_at_utc",
         "evidence_scope",
         "run_id",
         "event",
         "key",
         "value"
      );
      FileFlush(handle);
   }
   FileClose(handle);
   return true;
}

bool EnsureHeartbeatHeader()
{
   int handle = OpenAppendCsv(InpHeartbeatLogName);
   if(handle == INVALID_HANDLE)
      return false;
   if(FileSize(handle) == 0)
   {
      FileWrite(
         handle,
         "recorded_at_broker",
         "recorded_at_utc",
         "evidence_scope",
         "run_id",
         "event",
         "detail",
         "last_seen_m5_open",
         "last_completed_m5_open",
         "ok_source_rows",
         "missing_source_rows"
      );
      FileFlush(handle);
   }
   FileClose(handle);
   return true;
}

void WriteEnvironment(
   const string eventName,
   const string key,
   const string value
)
{
   int handle = OpenAppendCsv(InpEnvironmentLogName);
   if(handle == INVALID_HANDLE)
   {
      PrintFormat("Prospective collector environment open failed err=%d", GetLastError());
      return;
   }
   FileWrite(
      handle,
      TimeText(TimeCurrent()),
      TimeText(CurrentConfiguredUtc()),
      EvidenceScope(),
      InpRunId,
      eventName,
      key,
      value
   );
   FileFlush(handle);
   FileClose(handle);
}

void WriteHeartbeat(const string eventName, const string detail)
{
   int handle = OpenAppendCsv(InpHeartbeatLogName);
   if(handle == INVALID_HANDLE)
   {
      PrintFormat("Prospective collector heartbeat open failed err=%d", GetLastError());
      return;
   }
   FileWrite(
      handle,
      TimeText(TimeCurrent()),
      TimeText(CurrentConfiguredUtc()),
      EvidenceScope(),
      InpRunId,
      eventName,
      detail,
      TimeText(lastSeenM5Open),
      TimeText(lastCompletedM5Open),
      lastOkRows,
      lastMissingRows
   );
   FileFlush(handle);
   FileClose(handle);
}

void ResetAggregate(QuoteAggregate &aggregate)
{
   aggregate.copied_ticks = 0;
   aggregate.valid_quotes = 0;
   aggregate.first_tick_msc = 0;
   aggregate.last_tick_msc = 0;
   aggregate.first_bid = 0.0;
   aggregate.first_ask = 0.0;
   aggregate.last_bid = 0.0;
   aggregate.last_ask = 0.0;
   aggregate.bid_high = 0.0;
   aggregate.bid_low = 0.0;
   aggregate.ask_high = 0.0;
   aggregate.ask_low = 0.0;
   aggregate.spread_min_points = 0.0;
   aggregate.spread_sum_points = 0.0;
   aggregate.spread_max_points = 0.0;
   aggregate.spread_samples = 0;
}

void AddQuote(
   QuoteAggregate &aggregate,
   const MqlTick &tick,
   const double point
)
{
   if(tick.bid <= 0.0 || tick.ask <= 0.0 || tick.ask < tick.bid)
      return;

   const double spreadPoints =
      point > 0.0 ? (tick.ask - tick.bid) / point : 0.0;
   if(aggregate.valid_quotes == 0)
   {
      aggregate.first_tick_msc = tick.time_msc;
      aggregate.first_bid = tick.bid;
      aggregate.first_ask = tick.ask;
      aggregate.bid_high = tick.bid;
      aggregate.bid_low = tick.bid;
      aggregate.ask_high = tick.ask;
      aggregate.ask_low = tick.ask;
      aggregate.spread_min_points = spreadPoints;
      aggregate.spread_max_points = spreadPoints;
   }
   else
   {
      aggregate.bid_high = MathMax(aggregate.bid_high, tick.bid);
      aggregate.bid_low = MathMin(aggregate.bid_low, tick.bid);
      aggregate.ask_high = MathMax(aggregate.ask_high, tick.ask);
      aggregate.ask_low = MathMin(aggregate.ask_low, tick.ask);
      aggregate.spread_min_points =
         MathMin(aggregate.spread_min_points, spreadPoints);
      aggregate.spread_max_points =
         MathMax(aggregate.spread_max_points, spreadPoints);
   }
   aggregate.last_tick_msc = tick.time_msc;
   aggregate.last_bid = tick.bid;
   aggregate.last_ask = tick.ask;
   aggregate.spread_sum_points += spreadPoints;
   aggregate.spread_samples++;
   aggregate.valid_quotes++;
}

void WriteFeatureRow(
   const string sourceSymbol,
   const datetime intervalOpen,
   const datetime intervalClose,
   const string sourceStatus,
   const int terminalError,
   const QuoteAggregate &aggregate
)
{
   const int digits = (int)SymbolInfoInteger(sourceSymbol, SYMBOL_DIGITS);
   const double point = SymbolInfoDouble(sourceSymbol, SYMBOL_POINT);
   const double spreadMean = aggregate.spread_samples > 0
      ? aggregate.spread_sum_points / aggregate.spread_samples
      : 0.0;
   int handle = OpenAppendCsv(InpFeatureLogName);
   if(handle == INVALID_HANDLE)
   {
      PrintFormat("Prospective collector feature open failed err=%d", GetLastError());
      return;
   }
   FileWrite(
      handle,
      TimeText(TimeCurrent()),
      TimeText(CurrentConfiguredUtc()),
      EvidenceScope(),
      InpRunId,
      (long)AccountInfoInteger(ACCOUNT_LOGIN),
      AccountInfoString(ACCOUNT_SERVER),
      (int)TerminalInfoInteger(TERMINAL_BUILD),
      InpTargetSymbol,
      sourceSymbol,
      TimeText(intervalOpen),
      TimeText(intervalClose),
      TimeText(BrokerToConfiguredUtc(intervalOpen)),
      TimeText(BrokerToConfiguredUtc(intervalClose)),
      InpBrokerUtcOffsetSeconds,
      sourceStatus,
      terminalError,
      aggregate.copied_ticks,
      aggregate.valid_quotes,
      (long)aggregate.first_tick_msc,
      (long)aggregate.last_tick_msc,
      MillisecondTimeText(aggregate.first_tick_msc),
      MillisecondTimeText(aggregate.last_tick_msc),
      DoubleToString(aggregate.first_bid, digits),
      DoubleToString(aggregate.bid_high, digits),
      DoubleToString(aggregate.bid_low, digits),
      DoubleToString(aggregate.last_bid, digits),
      DoubleToString(aggregate.first_ask, digits),
      DoubleToString(aggregate.ask_high, digits),
      DoubleToString(aggregate.ask_low, digits),
      DoubleToString(aggregate.last_ask, digits),
      DoubleToString(aggregate.spread_min_points, 3),
      DoubleToString(spreadMean, 3),
      DoubleToString(aggregate.spread_max_points, 3),
      digits,
      DoubleToString(point, digits)
   );
   FileFlush(handle);
   FileClose(handle);
}

string CaptureSource(
   const string sourceSymbol,
   const datetime intervalOpen,
   const datetime intervalClose,
   QuoteAggregate &aggregate,
   int &terminalError
)
{
   ResetAggregate(aggregate);
   terminalError = 0;
   ResetLastError();
   if(!SymbolSelect(sourceSymbol, true))
   {
      terminalError = GetLastError();
      return "SYMBOL_UNAVAILABLE";
   }

   MqlTick ticks[];
   const ulong fromMsc = (ulong)intervalOpen * 1000;
   const ulong toMsc = (ulong)intervalClose * 1000 - 1;
   ResetLastError();
   const int copied = CopyTicksRange(
      sourceSymbol,
      ticks,
      COPY_TICKS_ALL,
      fromMsc,
      toMsc
   );
   terminalError = GetLastError();
   aggregate.copied_ticks = copied > 0 ? copied : 0;
   if(copied < 0)
      return "COPY_FAILED";
   if(copied == 0)
      return "NO_TICKS";

   const double point = SymbolInfoDouble(sourceSymbol, SYMBOL_POINT);
   for(int index = 0; index < copied; ++index)
      AddQuote(aggregate, ticks[index], point);
   if(aggregate.valid_quotes == 0)
      return "NO_VALID_TWO_SIDED_QUOTES";
   return "OK";
}

bool ProspectiveStartReached(const datetime intervalOpen)
{
   if((bool)MQLInfoInteger(MQL_TESTER))
      return true;
   const datetime configuredStart = StringToTime(InpProspectiveStartUtc);
   const datetime frozenFloor = StringToTime(FROZEN_FORWARD_FLOOR_UTC);
   if(configuredStart < frozenFloor)
      return false;
   return BrokerToConfiguredUtc(intervalOpen) >= configuredStart;
}

void CaptureCompletedInterval(const datetime intervalOpen)
{
   const datetime intervalClose = intervalOpen + 5 * 60;
   if(!ProspectiveStartReached(intervalOpen))
   {
      WriteHeartbeat(
         "INTERVAL_REFUSED",
         "before_frozen_or_configured_prospective_start"
      );
      return;
   }

   lastOkRows = 0;
   lastMissingRows = 0;
   for(int index = 0; index < ArraySize(sourceSymbols); ++index)
   {
      QuoteAggregate aggregate;
      int terminalError = 0;
      const string status = CaptureSource(
         sourceSymbols[index],
         intervalOpen,
         intervalClose,
         aggregate,
         terminalError
      );
      WriteFeatureRow(
         sourceSymbols[index],
         intervalOpen,
         intervalClose,
         status,
         terminalError,
         aggregate
      );
      if(status == "OK")
         lastOkRows++;
      else
         lastMissingRows++;
   }
   lastCompletedM5Open = intervalOpen;
   WriteHeartbeat("INTERVAL_CAPTURED", "completed_native_m5_no_backfill");
}

void CheckForNativeM5Transition()
{
   const datetime currentM5Open = iTime(_Symbol, PERIOD_M5, 0);
   if(currentM5Open <= 0 || currentM5Open == lastSeenM5Open)
      return;
   if(currentM5Open < lastSeenM5Open)
   {
      WriteHeartbeat("CLOCK_REGRESSION", "transition_refused");
      lastSeenM5Open = currentM5Open;
      return;
   }

   const int transitionGapSeconds = (int)(currentM5Open - lastSeenM5Open);
   lastSeenM5Open = currentM5Open;
   const datetime completedOpen = iTime(_Symbol, PERIOD_M5, 1);
   if(completedOpen <= 0)
   {
      WriteHeartbeat("INTERVAL_REFUSED", "completed_m5_open_unavailable");
      return;
   }
   if(transitionGapSeconds > 5 * 60)
   {
      WriteHeartbeat(
         "BAR_GAP",
         "no_catchup_gap_seconds=" + IntegerToString(transitionGapSeconds)
      );
   }
   CaptureCompletedInterval(completedOpen);
}

bool ParseSourceSymbols()
{
   string rawSymbols[];
   const ushort delimiter = StringGetCharacter(",", 0);
   const int count = StringSplit(InpReferenceSymbols, delimiter, rawSymbols);
   if(count <= 0)
      return false;

   ArrayResize(sourceSymbols, 0);
   for(int index = 0; index < count; ++index)
   {
      string symbol = rawSymbols[index];
      StringTrimLeft(symbol);
      StringTrimRight(symbol);
      if(symbol == "")
         continue;
      const int outputIndex = ArraySize(sourceSymbols);
      ArrayResize(sourceSymbols, outputIndex + 1);
      sourceSymbols[outputIndex] = symbol;
   }
   return ArraySize(sourceSymbols) > 0;
}

bool AcquireMutex()
{
   mutexName = StringFormat(
      "CODEX_EU_M5_COLLECT_%I64d_%s",
      AccountInfoInteger(ACCOUNT_LOGIN),
      InpTargetSymbol
   );
   const double now = (double)TimeLocal();
   if(GlobalVariableCheck(mutexName))
   {
      const double priorHeartbeat = GlobalVariableGet(mutexName);
      if(now - priorHeartbeat < 3.0 * MathMax(InpHeartbeatSeconds, 20))
         return false;
   }
   GlobalVariableSet(mutexName, now);
   mutexOwned = true;
   return true;
}

void WriteStartupEnvironment()
{
   string referenceSymbolsLog = InpReferenceSymbols;
   StringReplace(referenceSymbolsLog, ",", "|");
   WriteEnvironment("STARTUP", "account_login",
      (string)AccountInfoInteger(ACCOUNT_LOGIN));
   WriteEnvironment("STARTUP", "account_server",
      AccountInfoString(ACCOUNT_SERVER));
   WriteEnvironment("STARTUP", "account_company",
      AccountInfoString(ACCOUNT_COMPANY));
   WriteEnvironment("STARTUP", "account_trade_mode",
      (string)AccountInfoInteger(ACCOUNT_TRADE_MODE));
   WriteEnvironment("STARTUP", "terminal_build",
      (string)TerminalInfoInteger(TERMINAL_BUILD));
   WriteEnvironment("STARTUP", "terminal_name",
      TerminalInfoString(TERMINAL_NAME));
   WriteEnvironment("STARTUP", "terminal_path",
      TerminalInfoString(TERMINAL_PATH));
   WriteEnvironment("STARTUP", "target_symbol", InpTargetSymbol);
   WriteEnvironment("STARTUP", "chart_period", EnumToString(_Period));
   WriteEnvironment("STARTUP", "reference_symbols", referenceSymbolsLog);
   WriteEnvironment("STARTUP", "prospective_start_utc",
      InpProspectiveStartUtc);
   WriteEnvironment("STARTUP", "frozen_forward_floor_utc",
      FROZEN_FORWARD_FLOOR_UTC);
   WriteEnvironment("STARTUP", "configured_broker_utc_offset_seconds",
      IntegerToString(InpBrokerUtcOffsetSeconds));
   WriteEnvironment("STARTUP", "observed_current_minus_gmt_seconds",
      IntegerToString((int)(TimeCurrent() - TimeGMT())));
   WriteEnvironment("STARTUP", "trade_permission", "NONE_READ_ONLY");
}

int OnInit()
{
   if(_Symbol != InpTargetSymbol || _Period != PERIOD_M5)
   {
      Print("Prospective collector requires exact target symbol on M5");
      return INIT_PARAMETERS_INCORRECT;
   }
   if(
      !(bool)MQLInfoInteger(MQL_TESTER)
      && (ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)
         != ACCOUNT_TRADE_MODE_DEMO
   )
   {
      Print("Prospective collector refuses non-demo live accounts");
      return INIT_FAILED;
   }
   if(InpTimerSeconds < 1 || InpTimerSeconds > 60)
      return INIT_PARAMETERS_INCORRECT;
   if(InpHeartbeatSeconds < 20 || InpHeartbeatSeconds > 3600)
      return INIT_PARAMETERS_INCORRECT;
   if(!ParseSourceSymbols())
      return INIT_PARAMETERS_INCORRECT;
   if(
      !(bool)MQLInfoInteger(MQL_TESTER)
      && StringToTime(InpProspectiveStartUtc)
         < StringToTime(FROZEN_FORWARD_FLOOR_UTC)
   )
   {
      Print("Prospective collector refuses a start before frozen floor");
      return INIT_PARAMETERS_INCORRECT;
   }
   if(
      !EnsureFeatureHeader()
      || !EnsureEnvironmentHeader()
      || !EnsureHeartbeatHeader()
   )
   {
      PrintFormat("Prospective collector log initialization failed err=%d",
         GetLastError());
      return INIT_FAILED;
   }
   if(!AcquireMutex())
   {
      WriteHeartbeat("INIT_FAILED", "duplicate_instance_mutex");
      return INIT_FAILED;
   }

   lastSeenM5Open = iTime(_Symbol, PERIOD_M5, 0);
   if(lastSeenM5Open <= 0)
   {
      WriteHeartbeat("INIT_FAILED", "native_m5_open_unavailable");
      return INIT_FAILED;
   }
   lastHeartbeatLocal = TimeLocal();
   WriteStartupEnvironment();
   WriteHeartbeat("STARTUP_LATCH", "current_bar_latched_no_historical_backfill");
   EventSetTimer(InpTimerSeconds);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   WriteHeartbeat("DEINIT", "reason=" + IntegerToString(reason));
   EventKillTimer();
   if(mutexOwned && GlobalVariableCheck(mutexName))
      GlobalVariableDel(mutexName);
}

void OnTimer()
{
   if(mutexOwned)
      GlobalVariableSet(mutexName, (double)TimeLocal());
   CheckForNativeM5Transition();
   if(TimeLocal() - lastHeartbeatLocal >= InpHeartbeatSeconds)
   {
      lastHeartbeatLocal = TimeLocal();
      WriteHeartbeat("HEARTBEAT", "collector_alive");
   }
}

void OnTick()
{
   CheckForNativeM5Transition();
}

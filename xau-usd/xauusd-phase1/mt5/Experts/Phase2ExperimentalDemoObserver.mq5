#property strict
#property version   "1.000"
#property description "Experimental demo observer attachment. Telemetry only; no broker actions."

#include <Phase1/Phase1Types.mqh>
#include <Phase1/Phase1BreakoutRetest.mqh>

input string InpRunId = "phase2-experimental-demo-observer-v0.1";
input bool InpDryRunOnly = true;
input string InpCandidate = "breakout_retest";
input string InpCandidateStatus = "ACCEPTED";
input string InpTargetSymbol = "XAUUSD";
input string InpQualifiedSymbolsCsv = "XAUUSD,EURUSD,USDJPY";
input string InpExpectedServerMarker = "Demo";
input string InpAttachmentLogFileName = "experimental_demo_attachment_log.csv";
input string InpStartupLogFileName = "experimental_demo_attachment_startup.csv";

CPhase1BreakoutRetestObserver g_breakout_observer;
datetime g_last_m5_bar_time = 0;

string BoolText(const bool value)
{
   return value ? "true" : "false";
}

string LowerText(string value)
{
   StringToLower(value);
   return value;
}

bool ContainsText(const string haystack, const string needle)
{
   return StringFind(LowerText(haystack), LowerText(needle)) >= 0;
}

string TrimToken(string value)
{
   StringTrimLeft(value);
   StringTrimRight(value);
   return value;
}

bool CsvContainsSymbol(const string csv, const string symbol_name)
{
   string tokens[];
   int count = StringSplit(csv, ',', tokens);
   for(int index = 0; index < count; index++)
   {
      if(TrimToken(tokens[index]) == symbol_name)
         return true;
   }
   return false;
}

bool IsAllowedCandidate(const string candidate)
{
   return candidate == "breakout_retest"
      || candidate == "swing_breakout_retest_v0"
      || candidate == "symbol_normalized_round_retest_v0"
      || candidate == "round_number_retest_v0"
      || candidate == "session_extreme_retest_v0";
}

bool CandidateHasNativeObserver(const string candidate)
{
   return candidate == "breakout_retest" || candidate == "swing_breakout_retest_v0";
}

bool CandidateUsesSwingObserver(const string candidate)
{
   return candidate == "swing_breakout_retest_v0";
}

bool AppendCsvRow(const string file_name, const string &values[])
{
   int handle = INVALID_HANDLE;
   for(int attempt = 0; attempt < 20; attempt++)
   {
      handle = FileOpen(file_name, FILE_READ | FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_SHARE_READ | FILE_SHARE_WRITE);
      if(handle != INVALID_HANDLE)
         break;
      Sleep(50);
   }
   if(handle == INVALID_HANDLE)
   {
      Print("Could not open ", file_name, " error=", GetLastError());
      return false;
   }
   FileSeek(handle, 0, SEEK_END);
   string line = "";
   for(int index = 0; index < ArraySize(values); index++)
   {
      if(index > 0)
         line += ",";
      line += CsvEscape(values[index]);
   }
   FileWriteString(handle, line + "\r\n");
   FileFlush(handle);
   FileClose(handle);
   return true;
}

string CsvEscape(string value)
{
   bool needs_quote = StringFind(value, ",") >= 0 || StringFind(value, "\"") >= 0 || StringFind(value, "\n") >= 0;
   StringReplace(value, "\"", "\"\"");
   if(needs_quote)
      return "\"" + value + "\"";
   return value;
}

bool EnsureAttachmentLogHeader()
{
   if(FileIsExist(InpAttachmentLogFileName))
      return true;

   string header[] = {
      "timestamp_broker",
      "timestamp_utc",
      "timestamp_local",
      "run_id",
      "account_server",
      "symbol",
      "candidate",
      "candidate_status",
      "qualified_symbol",
      "dry_run",
      "broker_action_allowed",
      "observer_supported",
      "m5_bar_time",
      "bid",
      "ask",
      "spread_points",
      "stage",
      "direction",
      "would_signal",
      "reason_code",
      "level_kind",
      "level_price",
      "entry_price",
      "stop_loss",
      "take_profit",
      "stop_distance_points"
   };
   return AppendCsvRow(InpAttachmentLogFileName, header);
}

bool EnsureStartupLogHeader()
{
   if(FileIsExist(InpStartupLogFileName))
      return true;

   string header[] = {
      "timestamp_broker",
      "timestamp_utc",
      "timestamp_local",
      "run_id",
      "account_server",
      "symbol",
      "candidate",
      "candidate_status",
      "qualified_symbols",
      "dry_run",
      "broker_action_allowed",
      "observer_supported",
      "startup_status"
   };
   return AppendCsvRow(InpStartupLogFileName, header);
}

bool WriteStartupRow(const string status_text)
{
   string row[] = {
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS),
      InpRunId,
      AccountInfoString(ACCOUNT_SERVER),
      _Symbol,
      InpCandidate,
      InpCandidateStatus,
      InpQualifiedSymbolsCsv,
      BoolText(InpDryRunOnly),
      "false",
      BoolText(CandidateHasNativeObserver(InpCandidate)),
      status_text
   };
   return AppendCsvRow(InpStartupLogFileName, row);
}

int OnInit()
{
   if(!InpDryRunOnly)
   {
      Print("Phase2ExperimentalDemoObserver refused to start because dry-run mode is locked.");
      return INIT_FAILED;
   }

   string server = AccountInfoString(ACCOUNT_SERVER);
   if(server == "" || !ContainsText(server, InpExpectedServerMarker) || ContainsText(server, "live") || ContainsText(server, "real"))
   {
      Print("Phase2ExperimentalDemoObserver refused to start outside the expected demo server. Server=", server);
      return INIT_FAILED;
   }

   if(_Symbol != InpTargetSymbol)
   {
      Print("Phase2ExperimentalDemoObserver attached to ", _Symbol, " but target is ", InpTargetSymbol);
      return INIT_FAILED;
   }

   if(!CsvContainsSymbol(InpQualifiedSymbolsCsv, _Symbol))
   {
      Print("Phase2ExperimentalDemoObserver refused symbol ", _Symbol, " because it is not qualified for ", InpCandidate);
      return INIT_FAILED;
   }

   if(!IsAllowedCandidate(InpCandidate))
   {
      Print("Phase2ExperimentalDemoObserver refused unknown candidate ", InpCandidate);
      return INIT_FAILED;
   }

   if(!EnsureAttachmentLogHeader() || !EnsureStartupLogHeader())
      return INIT_FAILED;

   g_breakout_observer.Configure(CandidateUsesSwingObserver(InpCandidate));
   WriteStartupRow("ATTACHED_DEMO_TELEMETRY_ONLY");
   EventSetTimer(1);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   string row[] = {
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS),
      InpRunId,
      AccountInfoString(ACCOUNT_SERVER),
      _Symbol,
      InpCandidate,
      InpCandidateStatus,
      InpQualifiedSymbolsCsv,
      BoolText(InpDryRunOnly),
      "false",
      BoolText(CandidateHasNativeObserver(InpCandidate)),
      "REMOVED_REASON_" + IntegerToString(reason)
   };
   AppendCsvRow(InpStartupLogFileName, row);
}

void OnTimer()
{
   datetime m5_bar_time = iTime(_Symbol, PERIOD_M5, 0);
   if(m5_bar_time <= 0 || m5_bar_time == g_last_m5_bar_time)
      return;
   g_last_m5_bar_time = m5_bar_time;

   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double spread_points = point > 0.0 ? (ask - bid) / point : 0.0;

   Phase1BreakoutRetestObservation observation;
   Phase1ResetBreakoutRetestObservation(observation);
   bool observer_supported = CandidateHasNativeObserver(InpCandidate);
   if(observer_supported)
   {
      g_breakout_observer.Evaluate(_Symbol, point, observation);
   }
   else
   {
      observation.stage = "ATTACHED_OBSERVER_PENDING_IMPL";
      observation.reason_code = "candidate_attached_no_mql_observer_yet";
      observation.direction_text = "NONE";
   }

   string row[] = {
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS),
      InpRunId,
      AccountInfoString(ACCOUNT_SERVER),
      _Symbol,
      InpCandidate,
      InpCandidateStatus,
      BoolText(CsvContainsSymbol(InpQualifiedSymbolsCsv, _Symbol)),
      BoolText(InpDryRunOnly),
      "false",
      BoolText(observer_supported),
      TimeToString(m5_bar_time, TIME_DATE | TIME_SECONDS),
      DoubleToString(bid, (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS)),
      DoubleToString(ask, (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS)),
      DoubleToString(spread_points, 2),
      observation.stage,
      observation.direction_text,
      BoolText(observation.would_signal),
      observation.reason_code,
      observation.level_kind,
      DoubleToString(observation.level_price, (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS)),
      DoubleToString(observation.entry_price, (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS)),
      DoubleToString(observation.stop_loss, (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS)),
      DoubleToString(observation.take_profit, (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS)),
      DoubleToString(observation.stop_distance_points, 2)
   };
   AppendCsvRow(InpAttachmentLogFileName, row);
}

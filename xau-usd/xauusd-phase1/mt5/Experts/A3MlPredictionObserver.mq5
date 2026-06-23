#property strict
#property version   "1.000"
#property description "A3 ML prediction observer. Telemetry only; reads Python handoff CSV and writes passive logs."

#include <A3MlEaHandoff.mqh>

input string InpRunId = "a3-ml-prediction-observer-v1";
input bool InpDryRunOnly = true;
input string InpTargetSymbol = "XAUUSD";
input string InpExpectedServerMarker = "Demo";
input string InpAllowedAccountLoginsCsv = "1025742,1033030,1033669";
input string InpHandoffFileName = "A3_ML_EA_HANDOFF.csv";
input string InpObserverLogFileName = "a3_ml_prediction_observer_log.csv";
input string InpStartupLogFileName = "a3_ml_prediction_observer_startup.csv";
input int InpPollSeconds = 10;

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

bool CsvContainsTextToken(const string csv, const string wanted)
{
   string tokens[];
   int count = StringSplit(csv, ',', tokens);
   string wanted_trimmed = TrimToken(wanted);
   for(int index = 0; index < count; index++)
   {
      if(TrimToken(tokens[index]) == wanted_trimmed)
         return true;
   }
   return false;
}

bool AccountLoginWhitelisted()
{
   string allowed = TrimToken(InpAllowedAccountLoginsCsv);
   if(allowed == "")
      return true;
   return CsvContainsTextToken(allowed, IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)));
}

string CsvEscape(string value)
{
   bool needs_quote = StringFind(value, ",") >= 0 || StringFind(value, "\"") >= 0 || StringFind(value, "\n") >= 0;
   StringReplace(value, "\"", "\"\"");
   if(needs_quote)
      return "\"" + value + "\"";
   return value;
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

void WriteStartupRow(const string status, const string reason)
{
   string values[] = {
      "a3_ml_prediction_observer_startup_v1",
      TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
      InpRunId,
      status,
      reason,
      IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)),
      AccountInfoString(ACCOUNT_SERVER),
      _Symbol,
      InpTargetSymbol,
      BoolText(InpDryRunOnly),
      InpHandoffFileName,
      InpObserverLogFileName
   };
   AppendCsvRow(InpStartupLogFileName, values);
}

void WritePredictionLogRow(const A3MlEaHandoffDecision &decision, const bool available, const string fallback_reason)
{
   string values[] = {
      "a3_ml_prediction_observer_log_v1",
      TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
      InpRunId,
      IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)),
      AccountInfoString(ACCOUNT_SERVER),
      _Symbol,
      BoolText(available),
      available ? decision.generated_at_utc : "",
      available ? decision.expires_at_utc : "",
      available ? decision.dataset_version : "",
      available ? decision.exact_signal_id : "",
      available ? decision.setup_group_id : "",
      available ? decision.decision_time_utc : "",
      available ? decision.direction : "",
      available ? DoubleToString(decision.p_win_calibrated, 6) : "",
      available ? DoubleToString(decision.threshold, 6) : "",
      available ? decision.action : "ABSTAIN",
      available ? decision.reason : fallback_reason,
      available ? decision.model_id : "",
      available ? decision.model_hash : "",
      available ? decision.feature_schema_hash : "",
      available ? decision.drift_status : "ML_HANDOFF_UNAVAILABLE",
      "false"
   };
   AppendCsvRow(InpObserverLogFileName, values);
}

int OnInit()
{
   if(!InpDryRunOnly)
   {
      WriteStartupRow("REFUSED", "InpDryRunOnly must remain true");
      return INIT_FAILED;
   }
   if(InpTargetSymbol != _Symbol)
   {
      WriteStartupRow("REFUSED", "attached symbol does not match InpTargetSymbol");
      return INIT_FAILED;
   }
   if(StringLen(TrimToken(InpExpectedServerMarker)) > 0 && !ContainsText(AccountInfoString(ACCOUNT_SERVER), InpExpectedServerMarker))
   {
      WriteStartupRow("REFUSED", "server marker mismatch");
      return INIT_FAILED;
   }
   if(!AccountLoginWhitelisted())
   {
      WriteStartupRow("REFUSED", "account login not whitelisted");
      return INIT_FAILED;
   }
   int seconds = InpPollSeconds;
   if(seconds < 1)
      seconds = 1;
   EventSetTimer(seconds);
   WriteStartupRow("ACTIVE", "passive observer only");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
}

void OnTick()
{
}

void OnTimer()
{
   A3MlEaHandoffDecision decision;
   A3MlEaHandoffReset(decision);
   bool available = A3MlEaHandoffReadLatest(decision, InpTargetSymbol, InpHandoffFileName);
   WritePredictionLogRow(decision, available, "handoff file missing or no matching row");
}

#ifndef A3_ML_SHADOW_TAP_MQH
#define A3_ML_SHADOW_TAP_MQH

#include <A3MlEaHandoff.mqh>

input bool InpMlShadowReadEnabled = true;
input string InpMlHandoffFileName = A3_ML_EA_HANDOFF_DEFAULT_FILE;
input string InpMlShadowLogFileName = "a3_ml_broker_shadow_tap.csv";

string A3MlShadowTapBoolText(const bool value)
{
   return value ? "true" : "false";
}

string A3MlShadowTapCsvEscape(string value)
{
   StringReplace(value, "\"", "\"\"");
   if(StringFind(value, ",") >= 0 || StringFind(value, "\"") >= 0 || StringFind(value, "\n") >= 0 || StringFind(value, "\r") >= 0)
      return "\"" + value + "\"";
   return value;
}

bool A3MlShadowTapAppendCsvRow(const string file_name, const string &values[])
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
      Print("A3MlShadowTap could not open ", file_name, " error=", GetLastError());
      return false;
   }
   FileSeek(handle, 0, SEEK_END);
   string line = "";
   for(int index = 0; index < ArraySize(values); index++)
   {
      if(index > 0)
         line += ",";
      line += A3MlShadowTapCsvEscape(values[index]);
   }
   FileWriteString(handle, line + "\r\n");
   FileFlush(handle);
   FileClose(handle);
   return true;
}

bool A3MlShadowTapEnsureHeader()
{
   if(!InpMlShadowReadEnabled)
      return true;
   if(FileIsExist(InpMlShadowLogFileName))
      return true;
   string header[] = {
      "timestamp_broker",
      "timestamp_utc",
      "timestamp_local",
      "account_server",
      "account_login",
      "symbol",
      "event_source",
      "run_id",
      "ea_dry_run",
      "ea_broker_action_allowed",
      "ml_shadow_read_enabled",
      "ml_handoff_file",
      "ml_available",
      "ml_action",
      "ml_probability",
      "ml_threshold",
      "ml_direction",
      "ml_reason",
      "ml_model_id",
      "ml_drift_status",
      "ml_broker_action_authorized",
      "candidate_or_comment",
      "signal_stage",
      "signal_direction",
      "signal_would_signal",
      "reason_code",
      "guard_reason"
   };
   return A3MlShadowTapAppendCsvRow(InpMlShadowLogFileName, header);
}

bool A3MlShadowTapWriteRow(
   const string event_source,
   const string run_id,
   const bool ea_dry_run,
   const bool ea_broker_action_allowed,
   const string candidate_or_comment,
   const string signal_stage,
   const string signal_direction,
   const bool signal_would_signal,
   const string reason_code,
   const string guard_reason
)
{
   if(!InpMlShadowReadEnabled)
      return true;
   if(!A3MlShadowTapEnsureHeader())
      return false;

   A3MlEaHandoffDecision decision;
   A3MlEaHandoffReset(decision);
   bool available = A3MlEaHandoffReadLatest(decision, _Symbol, InpMlHandoffFileName);
   string action = available ? decision.action : "ABSTAIN";
   string probability = available ? DoubleToString(decision.p_win_calibrated, 6) : "";
   string threshold = available ? DoubleToString(decision.threshold, 6) : "";
   string ml_direction = available ? decision.direction : "";
   string ml_reason = available ? decision.reason : "ML_HANDOFF_UNAVAILABLE";
   string model_id = available ? decision.model_id : "";
   string drift_status = available ? decision.drift_status : "ML_HANDOFF_UNAVAILABLE";
   string row[] = {
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS),
      AccountInfoString(ACCOUNT_SERVER),
      IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)),
      _Symbol,
      event_source,
      run_id,
      A3MlShadowTapBoolText(ea_dry_run),
      A3MlShadowTapBoolText(ea_broker_action_allowed),
      A3MlShadowTapBoolText(InpMlShadowReadEnabled),
      InpMlHandoffFileName,
      A3MlShadowTapBoolText(available),
      action,
      probability,
      threshold,
      ml_direction,
      ml_reason,
      model_id,
      drift_status,
      A3MlShadowTapBoolText(available && decision.broker_action_authorized),
      candidate_or_comment,
      signal_stage,
      signal_direction,
      A3MlShadowTapBoolText(signal_would_signal),
      reason_code,
      guard_reason
   };
   return A3MlShadowTapAppendCsvRow(InpMlShadowLogFileName, row);
}

#endif

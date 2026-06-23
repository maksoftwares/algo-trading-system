#ifndef A3_ML_EA_HANDOFF_MQH
#define A3_ML_EA_HANDOFF_MQH

#define A3_ML_EA_HANDOFF_DEFAULT_FILE "A3_ML_EA_HANDOFF.csv"

struct A3MlEaHandoffDecision
{
   bool available;
   string generated_at_utc;
   string expires_at_utc;
   string dataset_version;
   string account_scope;
   string account_label;
   string symbol;
   string exact_signal_id;
   string setup_group_id;
   string decision_time_utc;
   string direction;
   double p_win_calibrated;
   double threshold;
   string action;
   string reason;
   string model_id;
   string model_hash;
   string feature_schema_hash;
   string drift_status;
   bool broker_action_authorized;
};

string A3MlEaHandoffTrim(string value)
{
   StringTrimLeft(value);
   StringTrimRight(value);
   return value;
}

string A3MlEaHandoffLower(string value)
{
   StringToLower(value);
   return value;
}

string A3MlEaHandoffUnquote(string value)
{
   value = A3MlEaHandoffTrim(value);
   StringReplace(value, "\r", "");
   StringReplace(value, "\n", "");
   int length = StringLen(value);
   if(length >= 2 && StringSubstr(value, 0, 1) == "\"" && StringSubstr(value, length - 1, 1) == "\"")
   {
      value = StringSubstr(value, 1, length - 2);
      StringReplace(value, "\"\"", "\"");
   }
   return value;
}

void A3MlEaHandoffReset(A3MlEaHandoffDecision &decision)
{
   decision.available = false;
   decision.generated_at_utc = "";
   decision.expires_at_utc = "";
   decision.dataset_version = "";
   decision.account_scope = "";
   decision.account_label = "";
   decision.symbol = "";
   decision.exact_signal_id = "";
   decision.setup_group_id = "";
   decision.decision_time_utc = "";
   decision.direction = "";
   decision.p_win_calibrated = 0.0;
   decision.threshold = 0.0;
   decision.action = "ABSTAIN";
   decision.reason = "";
   decision.model_id = "";
   decision.model_hash = "";
   decision.feature_schema_hash = "";
   decision.drift_status = "";
   decision.broker_action_authorized = false;
}

bool A3MlEaHandoffActionAllowed(const string action)
{
   string normalized = A3MlEaHandoffTrim(action);
   return normalized == "TAKE" || normalized == "SKIP" || normalized == "ABSTAIN";
}

bool A3MlEaHandoffParseUtc(const string value, datetime &parsed)
{
   string text = A3MlEaHandoffUnquote(value);
   if(StringLen(text) < 20)
      return false;
   if(StringSubstr(text, 4, 1) != "-" || StringSubstr(text, 7, 1) != "-" || StringSubstr(text, 10, 1) != "T")
      return false;

   MqlDateTime parts;
   parts.year = (int)StringToInteger(StringSubstr(text, 0, 4));
   parts.mon = (int)StringToInteger(StringSubstr(text, 5, 2));
   parts.day = (int)StringToInteger(StringSubstr(text, 8, 2));
   parts.hour = (int)StringToInteger(StringSubstr(text, 11, 2));
   parts.min = (int)StringToInteger(StringSubstr(text, 14, 2));
   parts.sec = (int)StringToInteger(StringSubstr(text, 17, 2));

   if(parts.year < 2020 || parts.mon < 1 || parts.mon > 12 || parts.day < 1 || parts.day > 31)
      return false;
   if(parts.hour < 0 || parts.hour > 23 || parts.min < 0 || parts.min > 59 || parts.sec < 0 || parts.sec > 59)
      return false;

   parsed = StructToTime(parts);
   return parsed > 0;
}

bool A3MlEaHandoffNotExpired(const string expires_at_utc)
{
   datetime expires_at;
   if(!A3MlEaHandoffParseUtc(expires_at_utc, expires_at))
      return false;
   return TimeGMT() <= expires_at;
}

bool A3MlEaHandoffReadLatest(
   A3MlEaHandoffDecision &decision,
   const string symbol_name,
   const string file_name = A3_ML_EA_HANDOFF_DEFAULT_FILE
)
{
   A3MlEaHandoffReset(decision);
   int handle = FileOpen(file_name, FILE_READ | FILE_TXT | FILE_ANSI | FILE_SHARE_READ | FILE_SHARE_WRITE);
   if(handle == INVALID_HANDLE)
      return false;

   string account_scope = IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN));
   string last_line = "";
   while(!FileIsEnding(handle))
   {
      string line = A3MlEaHandoffTrim(FileReadString(handle));
      if(line == "" || StringFind(line, "schema_version") == 0)
         continue;
      string fields[];
      int count = StringSplit(line, ',', fields);
      if(count < 20)
         continue;
      if(A3MlEaHandoffUnquote(fields[4]) != account_scope)
         continue;
      if(A3MlEaHandoffUnquote(fields[6]) != symbol_name)
         continue;
      last_line = line;
   }
   FileClose(handle);

   if(last_line == "")
      return false;

   string values[];
   int value_count = StringSplit(last_line, ',', values);
   if(value_count < 20)
      return false;

   decision.generated_at_utc = A3MlEaHandoffUnquote(values[1]);
   decision.expires_at_utc = A3MlEaHandoffUnquote(values[2]);
   decision.dataset_version = A3MlEaHandoffUnquote(values[3]);
   decision.account_scope = A3MlEaHandoffUnquote(values[4]);
   decision.account_label = A3MlEaHandoffUnquote(values[5]);
   decision.symbol = A3MlEaHandoffUnquote(values[6]);
   decision.exact_signal_id = A3MlEaHandoffUnquote(values[7]);
   decision.setup_group_id = A3MlEaHandoffUnquote(values[8]);
   decision.decision_time_utc = A3MlEaHandoffUnquote(values[9]);
   decision.direction = A3MlEaHandoffUnquote(values[10]);
   decision.p_win_calibrated = StringToDouble(A3MlEaHandoffUnquote(values[11]));
   decision.threshold = StringToDouble(A3MlEaHandoffUnquote(values[12]));
   decision.action = A3MlEaHandoffUnquote(values[13]);
   decision.reason = A3MlEaHandoffUnquote(values[14]);
   decision.model_id = A3MlEaHandoffUnquote(values[15]);
   decision.model_hash = A3MlEaHandoffUnquote(values[16]);
   decision.feature_schema_hash = A3MlEaHandoffUnquote(values[17]);
   decision.drift_status = A3MlEaHandoffUnquote(values[18]);
   decision.broker_action_authorized = A3MlEaHandoffLower(A3MlEaHandoffUnquote(values[19])) == "true";

   if(!A3MlEaHandoffActionAllowed(decision.action))
      return false;
   if(!A3MlEaHandoffNotExpired(decision.expires_at_utc))
      return false;
   if(decision.broker_action_authorized)
      return false;

   decision.available = true;
   return true;
}

void A3MlEaHandoffFieldsForLog(
   string &ml_available,
   string &ml_action,
   string &ml_probability,
   string &ml_model_id,
   string &ml_drift_status,
   const string symbol_name,
   const string file_name = A3_ML_EA_HANDOFF_DEFAULT_FILE
)
{
   A3MlEaHandoffDecision decision;
   A3MlEaHandoffReset(decision);
   if(A3MlEaHandoffReadLatest(decision, symbol_name, file_name))
   {
      ml_available = "true";
      ml_action = decision.action;
      ml_probability = DoubleToString(decision.p_win_calibrated, 6);
      ml_model_id = decision.model_id;
      ml_drift_status = decision.drift_status;
      return;
   }
   ml_available = "false";
   ml_action = "ABSTAIN";
   ml_probability = "";
   ml_model_id = "";
   ml_drift_status = "ML_HANDOFF_UNAVAILABLE";
}

#endif

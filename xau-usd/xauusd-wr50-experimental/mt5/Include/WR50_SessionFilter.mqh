#ifndef WR50_SESSION_FILTER_MQH
#define WR50_SESSION_FILTER_MQH

bool WR50_HourInWindow(const int hour, const int start_hour, const int end_hour)
{
   if(start_hour <= end_hour)
      return hour >= start_hour && hour <= end_hour;
   return hour >= start_hour || hour <= end_hour;
}

string WR50_SessionBucket()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   if(dt.hour >= 0 && dt.hour < 6)
      return "night";
   if(dt.hour >= 6 && dt.hour < 12)
      return "morning";
   if(dt.hour >= 12 && dt.hour < 18)
      return "afternoon";
   return "evening";
}

bool WR50_InConfiguredSession(const int start_a,
                              const int end_a,
                              const int start_b,
                              const int end_b)
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   return WR50_HourInWindow(dt.hour, start_a, end_a) || WR50_HourInWindow(dt.hour, start_b, end_b);
}

bool WR50_InRolloverBlackout(const int start_hour,
                             const int start_minute,
                             const int end_hour,
                             const int end_minute)
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   int now_minutes = dt.hour * 60 + dt.min;
   int start_minutes = start_hour * 60 + start_minute;
   int end_minutes = end_hour * 60 + end_minute;
   if(start_minutes <= end_minutes)
      return now_minutes >= start_minutes && now_minutes <= end_minutes;
   return now_minutes >= start_minutes || now_minutes <= end_minutes;
}

string WR50_UtcIsoNow()
{
   string value = TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS);
   StringReplace(value, ".", "-");
   StringReplace(value, " ", "T");
   return value + "Z";
}

bool WR50_InManualBlackout(const string file_name, string &reason)
{
   if(file_name == "")
   {
      reason = "manual_blackout_not_configured";
      return false;
   }
   if(!FileIsExist(file_name))
   {
      reason = "blackout_file_not_loaded";
      return false;
   }
   int handle = FileOpen(file_name, FILE_READ | FILE_CSV | FILE_ANSI, ',');
   if(handle == INVALID_HANDLE)
   {
      reason = "blackout_file_open_failed";
      return false;
   }
   string now_utc = WR50_UtcIsoNow();
   bool first = true;
   while(!FileIsEnding(handle))
   {
      string start_utc = FileReadString(handle);
      string end_utc = FileReadString(handle);
      string row_reason = FileReadString(handle);
      string enabled = FileReadString(handle);
      if(first)
      {
         first = false;
         if(start_utc == "start_utc")
            continue;
      }
      string enabled_lower = enabled;
      StringToLower(enabled_lower);
      if(enabled_lower == "true" && now_utc >= start_utc && now_utc <= end_utc)
      {
         reason = "manual_blackout:" + row_reason;
         FileClose(handle);
         return true;
      }
   }
   FileClose(handle);
   reason = "manual_blackout_clear";
   return false;
}

#endif


#ifndef WR50_FILE_UTIL_MQH
#define WR50_FILE_UTIL_MQH

bool WR50_EnsureFilesFolder()
{
   if(!FolderCreate("WR50"))
   {
      int err = GetLastError();
      if(err != 5016)
      {
         ResetLastError();
         return false;
      }
      ResetLastError();
   }
   return true;
}

string WR50_CsvEscape(const string raw_value)
{
   string value = raw_value;
   StringReplace(value, "\"", "\"\"");
   if(StringFind(value, ",") >= 0 || StringFind(value, "\"") >= 0 || StringFind(value, "\n") >= 0 || StringFind(value, "\r") >= 0)
      return "\"" + value + "\"";
   return value;
}

string WR50_JoinCsv(string &values[])
{
   string line = "";
   const int total = ArraySize(values);
   for(int i = 0; i < total; i++)
   {
      if(i > 0)
         line += ",";
      line += WR50_CsvEscape(values[i]);
   }
   return line;
}

bool WR50_WriteCsvLine(const string file_name, const string header, string &values[])
{
   WR50_EnsureFilesFolder();
   const bool exists = FileIsExist(file_name);
   int handle = FileOpen(file_name, FILE_READ | FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_SHARE_READ | FILE_SHARE_WRITE);
   if(handle == INVALID_HANDLE)
      return false;
   if(!exists || FileSize(handle) == 0)
      FileWriteString(handle, header + "\r\n");
   FileSeek(handle, 0, SEEK_END);
   FileWriteString(handle, WR50_JoinCsv(values) + "\r\n");
   FileClose(handle);
   return true;
}

string WR50_TimeBroker()
{
   return TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS);
}

string WR50_TimeUtc()
{
   return TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS);
}

string WR50_TimeLocal()
{
   return TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS);
}

#endif


#property strict
#property version   "1.00"
#property script_show_inputs
#property description "Passive Phase 0 historical bar exporter. File output only."

input string InpSymbol = "";
input string InpBrokerLabel = "capital_com";
input string InpTimeframes = "M5,M15,H1,H4,D1";
input string InpStartServerTime = "2016.01.01 00:00";
input string InpEndServerTime = "2025.06.30 23:59";
input int    InpServerToUtcOffsetHours = 0;
input bool   InpUseCommonFiles = true;
input bool   InpPrintToExpertsTab = true;

string g_symbol = "";

void OnStart()
{
   g_symbol = InpSymbol;
   if(g_symbol == "")
      g_symbol = _Symbol;

   if(!SymbolSelect(g_symbol, true))
   {
      Print("Passive bar exporter could not select symbol: ", g_symbol);
      return;
   }

   datetime start_server = StringToTime(InpStartServerTime);
   datetime end_server = StringToTime(InpEndServerTime);
   if(start_server <= 0 || end_server <= 0 || end_server <= start_server)
   {
      Print("Passive bar exporter received an invalid server-time window.");
      return;
   }

   string timeframe_parts[];
   int count = StringSplit(InpTimeframes, StringGetCharacter(",", 0), timeframe_parts);
   if(count <= 0)
   {
      Print("Passive bar exporter did not receive any timeframes.");
      return;
   }

   int exported_sets = 0;
   for(int index = 0; index < count; index++)
   {
      string label = Trim(timeframe_parts[index]);
      ENUM_TIMEFRAMES period;
      if(!TimeframeFromText(label, period))
      {
         Print("Passive bar exporter skipped unsupported timeframe: ", label);
         continue;
      }

      int rows = ExportBars(label, period, start_server, end_server);
      if(rows > 0)
         exported_sets++;
   }

   Print("Passive bar exporter complete. Exported timeframe files: ", exported_sets);
}

int ExportBars(string label, ENUM_TIMEFRAMES period, datetime start_server, datetime end_server)
{
   MqlRates rates[];
   int copied = CopyRates(g_symbol, period, start_server, end_server, rates);
   if(copied <= 0)
   {
      Print("Passive bar exporter found no bars for ", g_symbol, " ", label);
      return 0;
   }

   string file_name = BarFileName(label, start_server, end_server);
   int flags = FILE_WRITE | FILE_CSV | FILE_ANSI;
   if(InpUseCommonFiles)
      flags |= FILE_COMMON;

   int handle = FileOpen(file_name, flags, ',');
   if(handle == INVALID_HANDLE)
   {
      Print("Passive bar exporter could not open file: ", file_name);
      return 0;
   }

   FileWrite(
      handle,
      "<DATE>",
      "<TIME>",
      "<OPEN>",
      "<HIGH>",
      "<LOW>",
      "<CLOSE>",
      "<TICKVOL>",
      "<SPREAD>"
   );

   int digits = (int)SymbolInfoInteger(g_symbol, SYMBOL_DIGITS);
   int written = 0;
   for(int index = 0; index < copied; index++)
   {
      datetime utc_time = rates[index].time - (InpServerToUtcOffsetHours * 3600);
      FileWrite(
         handle,
         TimeToString(utc_time, TIME_DATE),
         TimeToString(utc_time, TIME_SECONDS),
         DoubleToString(rates[index].open, digits),
         DoubleToString(rates[index].high, digits),
         DoubleToString(rates[index].low, digits),
         DoubleToString(rates[index].close, digits),
         (string)rates[index].tick_volume,
         (string)rates[index].spread
      );
      written++;
   }
   FileClose(handle);

   if(InpPrintToExpertsTab)
      Print("Passive bar exporter wrote ", written, " rows to ", file_name);
   return written;
}

string BarFileName(string label, datetime start_server, datetime end_server)
{
   datetime start_utc = start_server - (InpServerToUtcOffsetHours * 3600);
   datetime end_utc = end_server - (InpServerToUtcOffsetHours * 3600);
   return CleanFilePart(g_symbol)
      + "_"
      + label
      + "_"
      + DateStamp(start_utc)
      + "_"
      + DateStamp(end_utc)
      + "_"
      + CleanFilePart(InpBrokerLabel)
      + ".csv";
}

string DateStamp(datetime value)
{
   string text = TimeToString(value, TIME_DATE);
   StringReplace(text, ".", "");
   return text;
}

string CleanFilePart(string value)
{
   string cleaned = value;
   StringReplace(cleaned, " ", "_");
   StringReplace(cleaned, "\\", "_");
   StringReplace(cleaned, "/", "_");
   StringReplace(cleaned, ":", "_");
   return cleaned;
}

string Trim(string value)
{
   int start = 0;
   int end = StringLen(value) - 1;
   while(start <= end && IsSpace(StringGetCharacter(value, start)))
      start++;
   while(end >= start && IsSpace(StringGetCharacter(value, end)))
      end--;
   if(end < start)
      return "";
   return StringSubstr(value, start, end - start + 1);
}

bool IsSpace(ushort character)
{
   return character == 32 || character == 9 || character == 10 || character == 13;
}

bool TimeframeFromText(string text, ENUM_TIMEFRAMES &period)
{
   string value = Trim(text);
   StringToUpper(value);
   if(value == "M1")
   {
      period = PERIOD_M1;
      return true;
   }
   if(value == "M5")
   {
      period = PERIOD_M5;
      return true;
   }
   if(value == "M15")
   {
      period = PERIOD_M15;
      return true;
   }
   if(value == "M30")
   {
      period = PERIOD_M30;
      return true;
   }
   if(value == "H1")
   {
      period = PERIOD_H1;
      return true;
   }
   if(value == "H4")
   {
      period = PERIOD_H4;
      return true;
   }
   if(value == "D1")
   {
      period = PERIOD_D1;
      return true;
   }
   if(value == "W1")
   {
      period = PERIOD_W1;
      return true;
   }
   if(value == "MN1")
   {
      period = PERIOD_MN1;
      return true;
   }
   return false;
}

#property strict
#property version   "1.00"
#property description "Passive Phase 0 spread logger. File output only."

input string InpSymbol = "";
input int    InpLogIntervalSeconds = 5;
input bool   InpUseCommonFiles = false;
input string InpFilePrefix = "spread_log";
input bool   InpPrintToExpertsTab = false;
input int    InpRolloverHourServer = 22;
input int    InpRolloverWindowMinutes = 30;

string g_symbol = "";
string g_current_date = "";
int g_rows_today = 0;

int OnInit()
{
   g_symbol = InpSymbol;
   if(g_symbol == "")
      g_symbol = _Symbol;

   if(!SymbolSelect(g_symbol, true))
   {
      Print("Passive spread logger could not select symbol: ", g_symbol);
      return INIT_FAILED;
   }

   EventSetTimer(MathMax(1, InpLogIntervalSeconds));
   Comment("Passive Spread Logger\nSymbol: ", g_symbol, "\nWaiting for first timer event...");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   Comment("");
}

void OnTimer()
{
   MqlTick tick;
   if(!SymbolInfoTick(g_symbol, tick))
   {
      if(InpPrintToExpertsTab)
         Print("Passive spread logger could not read tick for ", g_symbol);
      return;
   }

   datetime broker_time = TimeCurrent();
   datetime gmt_time = TimeGMT();
   datetime local_time = TimeLocal();
   double point = SymbolInfoDouble(g_symbol, SYMBOL_POINT);
   int digits = (int)SymbolInfoInteger(g_symbol, SYMBOL_DIGITS);
   double spread_price = tick.ask - tick.bid;
   double spread_points = point > 0.0 ? spread_price / point : 0.0;
   bool rollover = IsRolloverWindow(broker_time);
   string session_label = SessionLabel(gmt_time, rollover);
   string file_name = LogFileName(gmt_time);

   int flags = FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI;
   if(InpUseCommonFiles)
      flags |= FILE_COMMON;

   int handle = FileOpen(file_name, flags, ',');
   if(handle == INVALID_HANDLE)
   {
      if(InpPrintToExpertsTab)
         Print("Passive spread logger could not open file: ", file_name);
      return;
   }

   bool write_header = FileSize(handle) == 0;
   FileSeek(handle, 0, SEEK_END);
   if(write_header)
   {
      FileWrite(
         handle,
         "broker_time",
         "gmt_time",
         "local_time",
         "account",
         "server",
         "symbol",
         "bid",
         "ask",
         "spread_price",
         "spread_points",
         "point",
         "digits",
         "session_label",
         "is_rollover_window"
      );
   }

   FileWrite(
      handle,
      TimeToString(broker_time, TIME_DATE | TIME_SECONDS),
      TimeToString(gmt_time, TIME_DATE | TIME_SECONDS),
      TimeToString(local_time, TIME_DATE | TIME_SECONDS),
      (string)AccountInfoInteger(ACCOUNT_LOGIN),
      AccountInfoString(ACCOUNT_SERVER),
      g_symbol,
      DoubleToString(tick.bid, digits),
      DoubleToString(tick.ask, digits),
      DoubleToString(spread_price, digits),
      DoubleToString(spread_points, 2),
      DoubleToString(point, digits),
      (string)digits,
      session_label,
      rollover ? "true" : "false"
   );
   FileClose(handle);

   TrackRowsToday(gmt_time);
   g_rows_today++;
   UpdateDashboard(gmt_time, tick.bid, tick.ask, spread_points);
}

void TrackRowsToday(datetime gmt_time)
{
   string today = TimeToString(gmt_time, TIME_DATE);
   if(today != g_current_date)
   {
      g_current_date = today;
      g_rows_today = 0;
   }
}

string LogFileName(datetime gmt_time)
{
   string account = (string)AccountInfoInteger(ACCOUNT_LOGIN);
   string server = CleanFilePart(AccountInfoString(ACCOUNT_SERVER));
   string symbol = CleanFilePart(g_symbol);
   string date_part = TimeToString(gmt_time, TIME_DATE);
   StringReplace(date_part, ".", "");
   return InpFilePrefix + "_" + account + "_" + server + "_" + symbol + "_" + date_part + ".csv";
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

bool IsRolloverWindow(datetime broker_time)
{
   MqlDateTime parts;
   TimeToStruct(broker_time, parts);
   int current_minutes = parts.hour * 60 + parts.min;
   int rollover_minutes = InpRolloverHourServer * 60;
   int delta = MathAbs(current_minutes - rollover_minutes);
   delta = MathMin(delta, 1440 - delta);
   return delta <= InpRolloverWindowMinutes;
}

string SessionLabel(datetime gmt_time, bool rollover)
{
   if(rollover)
      return "ROLLOVER";

   MqlDateTime parts;
   TimeToStruct(gmt_time, parts);
   int hour = parts.hour;
   if(hour >= 0 && hour <= 6)
      return "ASIA";
   if(hour == 7)
      return "PRE_LONDON";
   if(hour >= 8 && hour <= 12)
      return "LONDON";
   if(hour >= 13 && hour <= 16)
      return "NY_OVERLAP";
   if(hour >= 17 && hour <= 20)
      return "NEW_YORK";
   return "OFF_HOURS";
}

void UpdateDashboard(datetime gmt_time, double bid, double ask, double spread_points)
{
   Comment(
      "Passive Spread Logger\n",
      "Symbol: ", g_symbol, "\n",
      "Account: ", (string)AccountInfoInteger(ACCOUNT_LOGIN), "\n",
      "Server: ", AccountInfoString(ACCOUNT_SERVER), "\n",
      "Last log: ", TimeToString(gmt_time, TIME_DATE | TIME_SECONDS), "\n",
      "Bid/Ask: ", DoubleToString(bid, _Digits), "/", DoubleToString(ask, _Digits), "\n",
      "Spread points: ", DoubleToString(spread_points, 2), "\n",
      "Rows written today: ", (string)g_rows_today, "\n",
      "NO TRADING FUNCTIONS PRESENT"
   );
}

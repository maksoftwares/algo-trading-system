// DirectionState shadow publisher. Writes FILE_COMMON CSV state only.
#property strict
#property version   "1.000"
#property description "Publishes XAUUSD H1 DirectionState telemetry to FILE_COMMON."

input string InpRunId = "direction-state-shadow-publisher-v0.1";
input string InpSymbol = "XAUUSD";
input ENUM_TIMEFRAMES InpTimeframe = PERIOD_H1;
input int InpEmaFast = 12;
input int InpEmaSlow = 34;
input int InpSlopeBars = 6;
input int InpEfficiencyRatioBars = 12;
input double InpEfficiencyRatioFlat = 0.30;
input double InpEfficiencyRatioStrong = 0.50;
input int InpHistoryBars = 200;
input int InpTimerSeconds = 30;
input int InpDubaiUtcOffsetMinutes = 240;
input string InpStateFileName = "dirstate_xauusd.csv";
input string InpHistoryFileName = "dirstate_xauusd_history.csv";
input string InpStartupFileName = "dirstate_xauusd_publisher_startup.csv";

datetime g_last_history_bar_time = 0;

string BoolText(const bool value)
{
   return value ? "true" : "false";
}

string CsvEscape(string value)
{
   StringReplace(value, "\"", "\"\"");
   if(StringFind(value, ",") >= 0 || StringFind(value, "\"") >= 0 || StringFind(value, "\n") >= 0 || StringFind(value, "\r") >= 0)
      return "\"" + value + "\"";
   return value;
}

string CsvLine(const string &values[])
{
   string line = "";
   for(int index = 0; index < ArraySize(values); index++)
   {
      if(index > 0)
         line += ",";
      line += CsvEscape(values[index]);
   }
   return line;
}

bool AppendCommonCsvRow(const string file_name, const string &values[])
{
   int handle = INVALID_HANDLE;
   for(int attempt = 0; attempt < 20; attempt++)
   {
      handle = FileOpen(file_name, FILE_READ | FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON | FILE_SHARE_READ | FILE_SHARE_WRITE);
      if(handle != INVALID_HANDLE)
         break;
      Sleep(50);
   }
   if(handle == INVALID_HANDLE)
   {
      Print("DirectionStatePublisher could not open common file ", file_name, " error=", GetLastError());
      return false;
   }
   FileSeek(handle, 0, SEEK_END);
   FileWriteString(handle, CsvLine(values) + "\r\n");
   FileFlush(handle);
   FileClose(handle);
   return true;
}

bool EnsureHistoryHeader()
{
   if(FileIsExist(InpHistoryFileName, FILE_COMMON))
      return true;
   string header[] = {
      "utc_time",
      "dubai_time",
      "direction",
      "regime",
      "strength",
      "ema_fast",
      "ema_slow",
      "er"
   };
   return AppendCommonCsvRow(InpHistoryFileName, header);
}

bool EnsureStartupHeader()
{
   if(FileIsExist(InpStartupFileName, FILE_COMMON))
      return true;
   string header[] = {
      "timestamp_broker",
      "timestamp_utc",
      "timestamp_local",
      "run_id",
      "account_server",
      "account_login",
      "chart_symbol",
      "state_symbol",
      "timeframe",
      "ema_fast",
      "ema_slow",
      "slope_bars",
      "er_bars",
      "er_flat",
      "er_strong",
      "state_file",
      "history_file",
      "startup_status"
   };
   return AppendCommonCsvRow(InpStartupFileName, header);
}

bool WriteStartupRow(const string status_text)
{
   string row[] = {
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS),
      InpRunId,
      AccountInfoString(ACCOUNT_SERVER),
      IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)),
      _Symbol,
      InpSymbol,
      EnumToString(InpTimeframe),
      IntegerToString(InpEmaFast),
      IntegerToString(InpEmaSlow),
      IntegerToString(InpSlopeBars),
      IntegerToString(InpEfficiencyRatioBars),
      DoubleToString(InpEfficiencyRatioFlat, 2),
      DoubleToString(InpEfficiencyRatioStrong, 2),
      InpStateFileName,
      InpHistoryFileName,
      status_text
   };
   return AppendCommonCsvRow(InpStartupFileName, row);
}

int SignOf(const double value)
{
   if(value > 0.0)
      return 1;
   if(value < 0.0)
      return -1;
   return 0;
}

int IntMax(const int left, const int right)
{
   return left > right ? left : right;
}

string RegimeForState(const int direction, const double er)
{
   if(direction > 0 && er >= InpEfficiencyRatioStrong)
      return "STRONG_UP";
   if(direction > 0)
      return "UP";
   if(direction < 0 && er >= InpEfficiencyRatioStrong)
      return "STRONG_DOWN";
   if(direction < 0)
      return "DOWN";
   return "FLAT";
}

bool WriteStateRow(
   const datetime bar_time,
   const int direction,
   const string regime,
   const double strength,
   const double ema_fast,
   const double ema_slow,
   const double er
)
{
   string row[] = {
      TimeToString(bar_time, TIME_DATE | TIME_SECONDS),
      TimeToString(bar_time + InpDubaiUtcOffsetMinutes * 60, TIME_DATE | TIME_SECONDS),
      IntegerToString(direction),
      regime,
      DoubleToString(strength, 3),
      DoubleToString(ema_fast, 6),
      DoubleToString(ema_slow, 6),
      DoubleToString(er, 6)
   };

   string header[] = {
      "utc_time",
      "dubai_time",
      "direction",
      "regime",
      "strength",
      "ema_fast",
      "ema_slow",
      "er"
   };

   int state_handle = FileOpen(InpStateFileName, FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON | FILE_SHARE_READ | FILE_SHARE_WRITE);
   if(state_handle == INVALID_HANDLE)
   {
      Print("DirectionStatePublisher could not write state file ", InpStateFileName, " error=", GetLastError());
      return false;
   }
   FileWriteString(state_handle, CsvLine(header) + "\r\n");
   FileWriteString(state_handle, CsvLine(row) + "\r\n");
   FileFlush(state_handle);
   FileClose(state_handle);

   if(bar_time != g_last_history_bar_time)
   {
      AppendCommonCsvRow(InpHistoryFileName, row);
      g_last_history_bar_time = bar_time;
   }
   return true;
}

bool PublishDirectionState()
{
   int min_bars = IntMax(InpEmaSlow + InpSlopeBars + 2, InpEfficiencyRatioBars + 2);
   int wanted_bars = IntMax(InpHistoryBars, min_bars + 25);
   MqlRates rates[];
   int copied = CopyRates(InpSymbol, InpTimeframe, 1, wanted_bars, rates);
   if(copied < min_bars)
   {
      Print("DirectionStatePublisher waiting for H1 history. copied=", copied, " min=", min_bars);
      return false;
   }
   ArraySetAsSeries(rates, false);

   double ema_fast_values[];
   double ema_slow_values[];
   ArrayResize(ema_fast_values, copied);
   ArrayResize(ema_slow_values, copied);
   double fast_alpha = 2.0 / (InpEmaFast + 1.0);
   double slow_alpha = 2.0 / (InpEmaSlow + 1.0);
   for(int index = 0; index < copied; index++)
   {
      double close_price = rates[index].close;
      if(index == 0)
      {
         ema_fast_values[index] = close_price;
         ema_slow_values[index] = close_price;
      }
      else
      {
         ema_fast_values[index] = fast_alpha * close_price + (1.0 - fast_alpha) * ema_fast_values[index - 1];
         ema_slow_values[index] = slow_alpha * close_price + (1.0 - slow_alpha) * ema_slow_values[index - 1];
      }
   }

   int last = copied - 1;
   double net_move = MathAbs(rates[last].close - rates[last - InpEfficiencyRatioBars].close);
   double path_move = 0.0;
   for(int index = last - InpEfficiencyRatioBars + 1; index <= last; index++)
      path_move += MathAbs(rates[index].close - rates[index - 1].close);

   double er = path_move > 0.0 ? net_move / path_move : 0.0;
   if(er < 0.0)
      er = 0.0;
   if(er > 1.0)
      er = 1.0;

   double slope = ema_slow_values[last] - ema_slow_values[last - InpSlopeBars];
   int dir_ema = SignOf(ema_fast_values[last] - ema_slow_values[last]);
   int dir_slope = SignOf(slope);
   int direction = (dir_ema * dir_slope > 0) ? dir_ema : 0;
   if(er < InpEfficiencyRatioFlat)
      direction = 0;

   string regime = RegimeForState(direction, er);
   return WriteStateRow(
      rates[last].time,
      direction,
      regime,
      er,
      ema_fast_values[last],
      ema_slow_values[last],
      er
   );
}

int OnInit()
{
   if(!EnsureStartupHeader() || !EnsureHistoryHeader())
      return INIT_FAILED;
   WriteStartupRow("ATTACHED_DIRECTION_STATE_SHADOW_PUBLISHER");
   EventSetTimer(IntMax(1, InpTimerSeconds));
   PublishDirectionState();
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   WriteStartupRow("REMOVED_REASON_" + IntegerToString(reason));
}

void OnTimer()
{
   PublishDirectionState();
}

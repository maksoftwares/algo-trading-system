#property strict

input string InpRunId = "A1_DAILY_PROFIT_FLOOR_GUARDIAN_V1";
input bool InpDryRunOnly = true;
input bool InpCloseActionAllowed = false;
input long InpAllowedAccountLogin = 1025742;
input string InpExpectedServerMarker = "Demo";
input string InpOwnerAuthorizationToken = "";
input string InpRequiredOwnerAuthorizationToken = "A1_DAILY_PROFIT_FLOOR_OWNER_AUTHORIZED_20260618";
input bool InpDailyProfitFloorEnabled = true;
input double InpDailyFloorAed = 50.0;
input bool InpNextDailyFloorEnabled = false;
input double InpNextDailyFloorAed = 100.0;
input bool InpHaltEntriesWhenArmed = true;
input bool InpDailyLossStopEnabled = false;
input double InpDailyLossStopAed = -150.0;
input bool InpDailyLossStopClosePositions = true;
input string InpCloseScopeSymbol = "";
input string InpAllowedPositionMagicsCsv = "";
input bool InpStrategyScopedPnl = true;
input int InpDubaiUtcOffsetMinutes = 240;
input int InpTimerSeconds = 2;
input int InpDeviationPoints = 100;
input long InpGuardianMagic = 919100;
input string InpGuardianKillSwitchFileName = "A1_DAILY_PROFIT_FLOOR_GUARDIAN_KILL.txt";
input string InpEntryHaltFileName = "experimental_demo_kill_switch.txt";
input string InpStateFileName = "A1_DAILY_PROFIT_FLOOR_GUARDIAN_STATE.txt";
input string InpEventLogFileName = "A1_DAILY_PROFIT_FLOOR_GUARDIAN_EVENTS.csv";
input string InpDailySummaryFileName = "A1_DAILY_PROFIT_FLOOR_GUARDIAN_DAILY_SUMMARY.csv";
input string InpStartupLogFileName = "A1_DAILY_PROFIT_FLOOR_GUARDIAN_STARTUP.csv";

string MARKER = "A1_DAILY_PROFIT_FLOOR_GUARDIAN";

string g_dubai_date = "";
double g_day_start_equity = 0.0;
double g_day_start_strategy_open_pnl = 0.0;
double g_peak_day_pnl = 0.0;
bool g_armed = false;
bool g_next_floor_armed = false;
bool g_locked = false;
string g_armed_time = "";
string g_trigger_time = "";
string g_trigger_reason = "";
int g_positions_closed_today = 0;
int g_close_failures_today = 0;
double g_locked_equity = 0.0;
double g_locked_day_pnl = 0.0;

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

bool CsvContainsLong(const string csv, const long expected)
{
   string normalized = TrimToken(csv);
   if(normalized == "")
      return true;
   string tokens[];
   ushort separator = StringGetCharacter(",", 0);
   int count = StringSplit(normalized, separator, tokens);
   for(int index = 0; index < count; index++)
   {
      string token = TrimToken(tokens[index]);
      if(token != "" && (long)StringToInteger(token) == expected)
         return true;
   }
   return false;
}

string CsvEscape(string value)
{
   StringReplace(value, "\"", "\"\"");
   if(StringFind(value, ",") >= 0 || StringFind(value, "\"") >= 0 || StringFind(value, "\n") >= 0 || StringFind(value, "\r") >= 0)
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
      Print("A1 profit-floor guardian could not open ", file_name, " error=", GetLastError());
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

bool FileContainsText(const string file_name, const string needle)
{
   if(!FileIsExist(file_name))
      return false;
   int handle = FileOpen(file_name, FILE_READ | FILE_TXT | FILE_ANSI | FILE_SHARE_READ | FILE_SHARE_WRITE);
   if(handle == INVALID_HANDLE)
      return false;
   string content = "";
   while(!FileIsEnding(handle))
      content += " " + FileReadString(handle);
   FileClose(handle);
   return ContainsText(content, needle);
}

bool GuardianKillSwitchActive()
{
   return FileContainsText(InpGuardianKillSwitchFileName, "KILL");
}

bool OwnerTokenValid()
{
   return TrimToken(InpOwnerAuthorizationToken) == TrimToken(InpRequiredOwnerAuthorizationToken);
}

bool DemoServerValid()
{
   string server = AccountInfoString(ACCOUNT_SERVER);
   return server != "" && ContainsText(server, InpExpectedServerMarker) && !ContainsText(server, "live") && !ContainsText(server, "real");
}

bool AccountLockValid()
{
   return (long)AccountInfoInteger(ACCOUNT_LOGIN) == InpAllowedAccountLogin
      && AccountInfoInteger(ACCOUNT_TRADE_MODE) == ACCOUNT_TRADE_MODE_DEMO
      && DemoServerValid();
}

datetime DubaiNow()
{
   return TimeGMT() + InpDubaiUtcOffsetMinutes * 60;
}

string DubaiDate()
{
   return TimeToString(DubaiNow(), TIME_DATE);
}

string NowBroker()
{
   return TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS);
}

string NowUtc()
{
   return TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS);
}

string NowDubai()
{
   return TimeToString(DubaiNow(), TIME_DATE | TIME_SECONDS);
}

void EnsureEventHeader()
{
   if(FileIsExist(InpEventLogFileName))
      return;
   string header[] = {
      "timestamp_broker",
      "timestamp_utc",
      "timestamp_dubai",
      "run_id",
      "account_login",
      "server",
      "event",
      "reason",
      "dubai_date",
      "day_start_equity",
      "equity",
      "day_pnl",
      "peak_day_pnl",
      "armed",
      "locked",
      "positions_total",
      "positions_closed_today",
      "close_failures_today",
      "ticket",
      "symbol",
      "direction",
      "volume",
      "price",
      "retcode",
      "retcode_description",
      "dry_run",
      "close_action_allowed"
   };
   AppendCsvRow(InpEventLogFileName, header);
}

void EnsureStartupHeader()
{
   if(FileIsExist(InpStartupLogFileName))
      return;
   string header[] = {
      "timestamp_broker",
      "timestamp_utc",
      "timestamp_dubai",
      "run_id",
      "account_login",
      "server",
      "dry_run",
      "close_action_allowed",
      "owner_token_present",
      "daily_floor_aed",
      "next_daily_floor_enabled",
      "next_daily_floor_aed",
      "daily_loss_stop_enabled",
      "daily_loss_stop_aed",
      "daily_loss_stop_close_positions",
      "guardian_kill_switch_file",
      "entry_halt_file",
      "state_file",
      "event_log",
      "daily_summary_log",
      "startup_status",
      "detail"
   };
   AppendCsvRow(InpStartupLogFileName, header);
}

void EnsureSummaryHeader()
{
   if(FileIsExist(InpDailySummaryFileName))
      return;
   string header[] = {
      "summary_written_broker",
      "summary_written_utc",
      "summary_written_dubai",
      "dubai_date",
      "day_start_equity",
      "ending_equity",
      "ending_day_pnl",
      "peak_day_pnl",
      "armed_time",
      "trigger_time",
      "trigger_reason",
      "positions_closed",
      "close_failures",
      "locked_equity",
      "locked_day_pnl",
      "counterfactual_unprotected_close_pnl",
      "counterfactual_status"
   };
   AppendCsvRow(InpDailySummaryFileName, header);
}

void WriteStartupRow(const string status, const string detail)
{
   EnsureStartupHeader();
   string row[] = {
      NowBroker(),
      NowUtc(),
      NowDubai(),
      InpRunId,
      IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)),
      AccountInfoString(ACCOUNT_SERVER),
      BoolText(InpDryRunOnly),
      BoolText(InpCloseActionAllowed),
      BoolText(StringLen(TrimToken(InpOwnerAuthorizationToken)) > 0),
      DoubleToString(InpDailyFloorAed, 2),
      BoolText(InpNextDailyFloorEnabled),
      DoubleToString(InpNextDailyFloorAed, 2),
      BoolText(InpDailyLossStopEnabled),
      DoubleToString(InpDailyLossStopAed, 2),
      BoolText(InpDailyLossStopClosePositions),
      InpGuardianKillSwitchFileName,
      InpEntryHaltFileName,
      InpStateFileName,
      InpEventLogFileName,
      InpDailySummaryFileName,
      status,
      detail
   };
   AppendCsvRow(InpStartupLogFileName, row);
}

void WriteEvent(
   const string event_name,
   const string reason,
   const ulong ticket = 0,
   const string symbol = "",
   const string direction = "",
   const double volume = 0.0,
   const double price = 0.0,
   const long retcode = 0,
   const string retcode_description = ""
)
{
   EnsureEventHeader();
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   bool day_pnl_valid = false;
   double day_pnl = CurrentDayPnlAed(day_pnl_valid);
   string row[] = {
      NowBroker(),
      NowUtc(),
      NowDubai(),
      InpRunId,
      IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)),
      AccountInfoString(ACCOUNT_SERVER),
      event_name,
      reason,
      g_dubai_date,
      DoubleToString(g_day_start_equity, 2),
      DoubleToString(equity, 2),
      DoubleToString(day_pnl, 2),
      DoubleToString(g_peak_day_pnl, 2),
      BoolText(g_armed),
      BoolText(g_locked),
      IntegerToString(PositionsTotal()),
      IntegerToString(g_positions_closed_today),
      IntegerToString(g_close_failures_today),
      IntegerToString((int)ticket),
      symbol,
      direction,
      DoubleToString(volume, 2),
      DoubleToString(price, 5),
      IntegerToString((int)retcode),
      retcode_description,
      BoolText(InpDryRunOnly),
      BoolText(InpCloseActionAllowed)
   };
   AppendCsvRow(InpEventLogFileName, row);
}

string StateLine(const string key, const string value)
{
   return key + "=" + value + "\r\n";
}

void SaveState()
{
   int handle = FileOpen(InpStateFileName, FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_SHARE_READ | FILE_SHARE_WRITE);
   if(handle == INVALID_HANDLE)
   {
      Print("A1 profit-floor guardian could not write state file: ", GetLastError());
      return;
   }
   string content = "";
   content += StateLine("dubai_date", g_dubai_date);
   content += StateLine("day_start_equity", DoubleToString(g_day_start_equity, 2));
   content += StateLine("day_start_strategy_open_pnl", DoubleToString(g_day_start_strategy_open_pnl, 2));
   content += StateLine("peak_day_pnl", DoubleToString(g_peak_day_pnl, 2));
   content += StateLine("armed", BoolText(g_armed));
   content += StateLine("next_floor_armed", BoolText(g_next_floor_armed));
   content += StateLine("locked", BoolText(g_locked));
   content += StateLine("armed_time", g_armed_time);
   content += StateLine("trigger_time", g_trigger_time);
   content += StateLine("trigger_reason", g_trigger_reason);
   content += StateLine("positions_closed_today", IntegerToString(g_positions_closed_today));
   content += StateLine("close_failures_today", IntegerToString(g_close_failures_today));
   content += StateLine("locked_equity", DoubleToString(g_locked_equity, 2));
   content += StateLine("locked_day_pnl", DoubleToString(g_locked_day_pnl, 2));
   FileWriteString(handle, content);
   FileFlush(handle);
   FileClose(handle);
}

string ValueAfterEquals(const string line)
{
   int pos = StringFind(line, "=");
   if(pos < 0)
      return "";
   return StringSubstr(line, pos + 1);
}

void ApplyStateLine(const string line)
{
   int pos = StringFind(line, "=");
   if(pos < 0)
      return;
   string key = StringSubstr(line, 0, pos);
   string value = ValueAfterEquals(line);
   if(key == "dubai_date") g_dubai_date = value;
   else if(key == "day_start_equity") g_day_start_equity = StringToDouble(value);
   else if(key == "day_start_strategy_open_pnl") g_day_start_strategy_open_pnl = StringToDouble(value);
   else if(key == "peak_day_pnl") g_peak_day_pnl = StringToDouble(value);
   else if(key == "armed") g_armed = ContainsText(value, "true");
   else if(key == "next_floor_armed") g_next_floor_armed = ContainsText(value, "true");
   else if(key == "locked") g_locked = ContainsText(value, "true");
   else if(key == "armed_time") g_armed_time = value;
   else if(key == "trigger_time") g_trigger_time = value;
   else if(key == "trigger_reason") g_trigger_reason = value;
   else if(key == "positions_closed_today") g_positions_closed_today = (int)StringToInteger(value);
   else if(key == "close_failures_today") g_close_failures_today = (int)StringToInteger(value);
   else if(key == "locked_equity") g_locked_equity = StringToDouble(value);
   else if(key == "locked_day_pnl") g_locked_day_pnl = StringToDouble(value);
}

bool LoadState()
{
   if(!FileIsExist(InpStateFileName))
      return false;
   int handle = FileOpen(InpStateFileName, FILE_READ | FILE_TXT | FILE_ANSI | FILE_SHARE_READ | FILE_SHARE_WRITE);
   if(handle == INVALID_HANDLE)
      return false;
   while(!FileIsEnding(handle))
   {
      string line = FileReadString(handle);
      ApplyStateLine(line);
   }
   FileClose(handle);
   return g_dubai_date != "" && g_day_start_equity > 0.0;
}

void WriteDailySummary(const string date_to_write)
{
   EnsureSummaryHeader();
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   bool day_pnl_valid = false;
   double ending_day_pnl = CurrentDayPnlAed(day_pnl_valid);
   string row[] = {
      NowBroker(),
      NowUtc(),
      NowDubai(),
      date_to_write,
      DoubleToString(g_day_start_equity, 2),
      DoubleToString(equity, 2),
      DoubleToString(ending_day_pnl, 2),
      DoubleToString(g_peak_day_pnl, 2),
      g_armed_time,
      g_trigger_time,
      g_trigger_reason,
      IntegerToString(g_positions_closed_today),
      IntegerToString(g_close_failures_today),
      DoubleToString(g_locked_equity, 2),
      DoubleToString(g_locked_day_pnl, 2),
      "NA_RUNTIME_REPLAY_REQUIRED",
      "runtime_guardian_cannot_observe_unprotected_counterfactual_after_it_closes_and_halts"
   };
   AppendCsvRow(InpDailySummaryFileName, row);
}

void ResetForNewDubaiDay(const string new_date, const bool write_summary)
{
   if(write_summary && g_dubai_date != "")
      WriteDailySummary(g_dubai_date);
   if(EntryHaltFileOwnedByGuardian())
      RemoveEntryHaltFile("new_dubai_day_reset");
   g_dubai_date = new_date;
   g_day_start_equity = AccountInfoDouble(ACCOUNT_EQUITY);
   bool strategy_open_pnl_valid = false;
   g_day_start_strategy_open_pnl = OpenScopedPnlAed(strategy_open_pnl_valid);
   if(!strategy_open_pnl_valid)
      g_day_start_strategy_open_pnl = 0.0;
   g_peak_day_pnl = 0.0;
   g_armed = false;
   g_next_floor_armed = false;
   g_locked = false;
   g_armed_time = "";
   g_trigger_time = "";
   g_trigger_reason = "";
   g_positions_closed_today = 0;
   g_close_failures_today = 0;
   g_locked_equity = 0.0;
   g_locked_day_pnl = 0.0;
   SaveState();
   WriteEvent("DAY_RESET", "dubai_day_start");
}

void EnsureCurrentDubaiDay()
{
   string today = DubaiDate();
   if(g_dubai_date == "")
   {
      ResetForNewDubaiDay(today, false);
      return;
   }
   if(g_dubai_date != today)
      ResetForNewDubaiDay(today, true);
}

bool EntryHaltFileOwnedByGuardian()
{
   return FileContainsText(InpEntryHaltFileName, MARKER);
}

bool EntryHaltFileActiveByGuardian()
{
   return EntryHaltFileOwnedByGuardian() && FileContainsText(InpEntryHaltFileName, "KILL");
}

void WriteEntryHaltFile(const string reason)
{
   if(EntryHaltFileActiveByGuardian())
      return;
   if(InpDryRunOnly || !InpCloseActionAllowed)
   {
      WriteEvent("WOULD_WRITE_ENTRY_HALT", reason);
      return;
   }
   int handle = FileOpen(InpEntryHaltFileName, FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_SHARE_READ | FILE_SHARE_WRITE);
   if(handle == INVALID_HANDLE)
   {
      WriteEvent("ENTRY_HALT_WRITE_FAILED", "file_open_failed");
      return;
   }
   FileWriteString(handle,
      "KILL\r\n"
      + MARKER + "\r\n"
      + "reason=" + reason + "\r\n"
      + "timestamp_broker=" + NowBroker() + "\r\n"
      + "timestamp_utc=" + NowUtc() + "\r\n"
      + "timestamp_dubai=" + NowDubai() + "\r\n"
      + "account_login=" + IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)) + "\r\n");
   FileFlush(handle);
   FileClose(handle);
   WriteEvent("ENTRY_HALT_WRITTEN", reason);
}

void RemoveEntryHaltFile(const string reason)
{
   if(!FileIsExist(InpEntryHaltFileName))
      return;
   if(!EntryHaltFileOwnedByGuardian())
      return;
   if(InpDryRunOnly || !InpCloseActionAllowed)
   {
      WriteEvent("WOULD_REMOVE_ENTRY_HALT", reason);
      return;
   }
   if(FileDelete(InpEntryHaltFileName))
      WriteEvent("ENTRY_HALT_REMOVED", reason);
   else
      WriteEvent("ENTRY_HALT_REMOVE_FAILED", reason);
}

ENUM_ORDER_TYPE_FILLING FillPolicyForSymbol(const string symbol)
{
   int filling = (int)SymbolInfoInteger(symbol, SYMBOL_FILLING_MODE);
   if((filling & SYMBOL_FILLING_IOC) == SYMBOL_FILLING_IOC)
      return ORDER_FILLING_IOC;
   if((filling & SYMBOL_FILLING_FOK) == SYMBOL_FILLING_FOK)
      return ORDER_FILLING_FOK;
   return ORDER_FILLING_RETURN;
}

string PositionDirectionText(const ENUM_POSITION_TYPE type)
{
   if(type == POSITION_TYPE_BUY)
      return "BUY";
   if(type == POSITION_TYPE_SELL)
      return "SELL";
   return "UNKNOWN";
}

bool ClosePositionByTicket(const ulong ticket, const string reason)
{
   if(!PositionSelectByTicket(ticket))
      return true;
   string symbol = PositionGetString(POSITION_SYMBOL);
   ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
   double volume = PositionGetDouble(POSITION_VOLUME);
   MqlTick tick;
   if(!SymbolInfoTick(symbol, tick))
   {
      g_close_failures_today++;
      WriteEvent("CLOSE_FAILED", "symbol_tick_unavailable|" + reason, ticket, symbol, PositionDirectionText(type), volume);
      SaveState();
      return false;
   }
   double price = type == POSITION_TYPE_BUY ? tick.bid : tick.ask;
   if(InpDryRunOnly || !InpCloseActionAllowed)
   {
      WriteEvent("WOULD_CLOSE", reason, ticket, symbol, PositionDirectionText(type), volume, price);
      return false;
   }
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) || !MQLInfoInteger(MQL_TRADE_ALLOWED) || !AccountInfoInteger(ACCOUNT_TRADE_ALLOWED))
   {
      g_close_failures_today++;
      WriteEvent("CLOSE_FAILED", "terminal_or_account_trading_disabled|" + reason, ticket, symbol, PositionDirectionText(type), volume, price);
      SaveState();
      return false;
   }
   MqlTradeRequest request;
   MqlTradeResult result;
   ZeroMemory(request);
   ZeroMemory(result);
   request.action = TRADE_ACTION_DEAL;
   request.symbol = symbol;
   request.position = ticket;
   request.magic = InpGuardianMagic;
   request.volume = volume;
   request.type = type == POSITION_TYPE_BUY ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
   request.price = price;
   request.deviation = InpDeviationPoints;
   request.type_filling = FillPolicyForSymbol(symbol);
   request.type_time = ORDER_TIME_GTC;
   request.comment = "A1_PROFIT_FLOOR_CLOSE";
   bool sent = OrderSend(request, result);
   bool done = sent && (result.retcode == TRADE_RETCODE_DONE || result.retcode == TRADE_RETCODE_DONE_PARTIAL || result.retcode == TRADE_RETCODE_PLACED);
   if(done)
      g_positions_closed_today++;
   else
      g_close_failures_today++;
   WriteEvent(done ? "CLOSE_SENT" : "CLOSE_FAILED",
      reason,
      ticket,
      symbol,
      PositionDirectionText(type),
      volume,
      price,
      (long)result.retcode,
      result.comment);
   SaveState();
   return done;
}

bool IdentityInCloseScope(const string symbol, const long magic)
{
   string target_symbol = TrimToken(InpCloseScopeSymbol);
   if(target_symbol != "" && symbol != target_symbol)
      return false;
   return CsvContainsLong(InpAllowedPositionMagicsCsv, magic);
}

bool PositionInCloseScope()
{
   return IdentityInCloseScope(
      PositionGetString(POSITION_SYMBOL),
      PositionGetInteger(POSITION_MAGIC)
   );
}

datetime DubaiDayStartBroker()
{
   string date_value = g_dubai_date != "" ? g_dubai_date : DubaiDate();
   datetime dubai_midnight = StringToTime(date_value + " 00:00");
   datetime utc_start = dubai_midnight - InpDubaiUtcOffsetMinutes * 60;
   long broker_utc_offset = (long)(TimeCurrent() - TimeGMT());
   return (datetime)(utc_start + broker_utc_offset);
}

bool PositionIdPresent(const ulong &values[], const ulong expected)
{
   for(int index = 0; index < ArraySize(values); index++)
   {
      if(values[index] == expected)
         return true;
   }
   return false;
}

void AddPositionId(ulong &values[], const ulong value)
{
   if(value == 0 || PositionIdPresent(values, value))
      return;
   int size = ArraySize(values);
   ArrayResize(values, size + 1);
   values[size] = value;
}

double OpenScopedPnlAed(bool &valid)
{
   double pnl = 0.0;
   for(int index = PositionsTotal() - 1; index >= 0; index--)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket) || !PositionInCloseScope())
         continue;
      pnl += PositionGetDouble(POSITION_PROFIT);
      pnl += PositionGetDouble(POSITION_SWAP);
   }
   valid = true;
   return pnl;
}

double StrategyDayPnlAed(bool &valid)
{
   valid = false;
   datetime day_start = DubaiDayStartBroker();
   datetime now = TimeCurrent();
   if(day_start <= 0 || now < day_start)
      return 0.0;
   datetime origin_lookback = day_start - 60 * 24 * 60 * 60;
   if(!HistorySelect(origin_lookback, now))
      return 0.0;

   ulong owned_position_ids[];
   int total = HistoryDealsTotal();
   for(int index = 0; index < total; index++)
   {
      ulong ticket = HistoryDealGetTicket(index);
      if(ticket == 0)
         continue;
      if(IdentityInCloseScope(
         HistoryDealGetString(ticket, DEAL_SYMBOL),
         HistoryDealGetInteger(ticket, DEAL_MAGIC)
      ))
         AddPositionId(
            owned_position_ids,
            (ulong)HistoryDealGetInteger(ticket, DEAL_POSITION_ID)
         );
   }

   double pnl = 0.0;
   for(int index = 0; index < total; index++)
   {
      ulong ticket = HistoryDealGetTicket(index);
      if(ticket == 0 || (datetime)HistoryDealGetInteger(ticket, DEAL_TIME) < day_start)
         continue;
      ulong position_id = (ulong)HistoryDealGetInteger(ticket, DEAL_POSITION_ID);
      if(!PositionIdPresent(owned_position_ids, position_id))
         continue;
      pnl += HistoryDealGetDouble(ticket, DEAL_PROFIT);
      pnl += HistoryDealGetDouble(ticket, DEAL_COMMISSION);
      pnl += HistoryDealGetDouble(ticket, DEAL_SWAP);
      pnl += HistoryDealGetDouble(ticket, DEAL_FEE);
   }

   bool open_pnl_valid = false;
   pnl += OpenScopedPnlAed(open_pnl_valid) - g_day_start_strategy_open_pnl;
   if(!open_pnl_valid)
      return 0.0;
   valid = true;
   return pnl;
}

double CurrentDayPnlAed(bool &valid)
{
   if(InpStrategyScopedPnl)
      return StrategyDayPnlAed(valid);
   valid = true;
   return AccountInfoDouble(ACCOUNT_EQUITY) - g_day_start_equity;
}

int CloseAllPositions(const string reason)
{
   int attempted = 0;
   for(int index = PositionsTotal() - 1; index >= 0; index--)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0)
         continue;
      if(!PositionSelectByTicket(ticket))
         continue;
      if(!PositionInCloseScope())
         continue;
      attempted++;
      ClosePositionByTicket(ticket, reason);
   }
   return attempted;
}

bool LockedStateRequiresPositionClose()
{
   if(ContainsText(g_trigger_reason, "DAILY_LOSS_STOP"))
      return InpDailyLossStopClosePositions;
   return true;
}

void TriggerLock(const string reason)
{
   if(!g_locked)
   {
      g_locked = true;
      g_trigger_time = NowDubai();
      g_trigger_reason = reason;
      g_locked_equity = AccountInfoDouble(ACCOUNT_EQUITY);
      bool day_pnl_valid = false;
      g_locked_day_pnl = CurrentDayPnlAed(day_pnl_valid);
      SaveState();
      WriteEvent("LOCKED", reason);
   }
   WriteEntryHaltFile(reason);
   if(LockedStateRequiresPositionClose())
      CloseAllPositions(reason);
   SaveState();
}

double ActiveProfitFloorAed()
{
   if(InpNextDailyFloorEnabled && g_next_floor_armed && InpNextDailyFloorAed > InpDailyFloorAed)
      return InpNextDailyFloorAed;
   return InpDailyFloorAed;
}

void EvaluateFloor()
{
   bool day_pnl_valid = false;
   double day_pnl = CurrentDayPnlAed(day_pnl_valid);
   if(!day_pnl_valid)
   {
      WriteEvent("EVALUATION_SKIPPED", "strategy_pnl_history_unavailable");
      return;
   }
   if(day_pnl > g_peak_day_pnl)
      g_peak_day_pnl = day_pnl;

   if(g_locked)
   {
      if(LockedStateRequiresPositionClose())
      {
         WriteEntryHaltFile("keep_flat_locked_today");
         CloseAllPositions("keep_flat_locked_today");
      }
      else
      {
         WriteEntryHaltFile("keep_entries_halted_today");
      }
      SaveState();
      return;
   }

   if(InpDailyLossStopEnabled && day_pnl <= InpDailyLossStopAed)
   {
      TriggerLock("DAILY_LOSS_STOP");
      return;
   }

   if(!InpDailyProfitFloorEnabled)
   {
      SaveState();
      return;
   }

   bool just_armed = false;
   if(!g_armed && day_pnl >= InpDailyFloorAed)
   {
      g_armed = true;
      g_armed_time = NowDubai();
      just_armed = true;
      SaveState();
      WriteEvent("ARMED", "day_pnl_reached_floor");
      if(InpHaltEntriesWhenArmed)
         WriteEntryHaltFile("daily_profit_floor_armed_no_new_entries");
   }

   if(g_armed && InpNextDailyFloorEnabled && !g_next_floor_armed && InpNextDailyFloorAed > InpDailyFloorAed && day_pnl >= InpNextDailyFloorAed)
   {
      g_next_floor_armed = true;
      SaveState();
      WriteEvent("NEXT_FLOOR_ARMED", "day_pnl_reached_next_floor");
   }

   if(g_armed && InpHaltEntriesWhenArmed)
      WriteEntryHaltFile("daily_profit_floor_armed_no_new_entries");

   double active_floor = ActiveProfitFloorAed();
   if(g_armed && !just_armed && day_pnl <= active_floor && g_peak_day_pnl > active_floor)
      TriggerLock("DAILY_PROFIT_FLOOR_RETURN_" + DoubleToString(active_floor, 2));
   else
      SaveState();
}

void ReconcileProfitFloorPolicy()
{
   if(InpDailyProfitFloorEnabled)
      return;
   bool changed = false;
   if(g_armed || g_next_floor_armed)
   {
      g_armed = false;
      g_next_floor_armed = false;
      g_armed_time = "";
      changed = true;
   }
   if(g_locked && ContainsText(g_trigger_reason, "DAILY_PROFIT_FLOOR"))
   {
      g_locked = false;
      g_trigger_time = "";
      g_trigger_reason = "";
      g_locked_equity = 0.0;
      g_locked_day_pnl = 0.0;
      changed = true;
   }
   if(!g_locked)
      RemoveEntryHaltFile("daily_profit_floor_disabled");
   if(changed)
   {
      SaveState();
      WriteEvent("PROFIT_FLOOR_DISABLED", "loss_only_guardian_active");
   }
}

int OnInit()
{
   EnsureEventHeader();
   EnsureStartupHeader();
   EnsureSummaryHeader();
   if(!AccountLockValid())
   {
      WriteStartupRow("INIT_FAILED", "account_or_demo_lock_failed");
      return INIT_FAILED;
   }
   if(!InpDryRunOnly && InpCloseActionAllowed && !OwnerTokenValid())
   {
      WriteStartupRow("INIT_FAILED", "owner_authorization_token_missing_or_invalid");
      return INIT_FAILED;
   }
   bool restored = LoadState();
   EnsureCurrentDubaiDay();
   ReconcileProfitFloorPolicy();
   WriteStartupRow("ATTACHED_A1_DAILY_PROFIT_FLOOR_GUARDIAN", restored ? "state_restored" : "state_initialized");
   EventSetTimer(MathMax(InpTimerSeconds, 1));
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   WriteStartupRow("REMOVED_REASON_" + IntegerToString(reason), "guardian_deinit");
}

void OnTimer()
{
   if(GuardianKillSwitchActive())
   {
      WriteEvent("GUARDIAN_KILL_SWITCH_ACTIVE", "guardian_paused");
      return;
   }
   EnsureCurrentDubaiDay();
   EvaluateFloor();
   bool day_pnl_valid = false;
   double day_pnl = CurrentDayPnlAed(day_pnl_valid);
   Comment(StringFormat("A1 Profit Floor Guardian: date=%s pnl=%.2f peak=%.2f armed=%s locked=%s",
      g_dubai_date,
      day_pnl,
      g_peak_day_pnl,
      BoolText(g_armed),
      BoolText(g_locked)));
}

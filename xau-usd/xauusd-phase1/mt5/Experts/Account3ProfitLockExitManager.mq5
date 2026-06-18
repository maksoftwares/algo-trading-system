#property strict

input string InpRunId = "A3_PROFIT_LOCK_EXIT_MANAGER_V1";
input bool InpDryRunOnly = true;
input bool InpManageActionAllowed = false;
input string InpTargetSymbol = "XAUUSD";
input string InpExpectedServerMarker = "Demo";
input string InpAllowedAccountLoginsCsv = "1033669";
input string InpExecutionKillSwitchFileName = "A3_EXECUTION_KILL.txt";
input string InpFullStopFileName = "A3_FULL_STOP.txt";
input string InpManagedMagicsCsv = "933200,933400";
input bool InpPrimaryRungEnabled = true;
input double InpPrimaryTriggerR = 1.25;
input double InpPrimaryLockR = 0.80;
input bool InpSecondaryRungEnabled = false;
input double InpSecondaryTriggerR = 1.00;
input double InpSecondaryLockR = 0.50;
input bool InpTertiaryRungEnabled = false;
input double InpTertiaryTriggerR = 0.75;
input double InpTertiaryLockR = 0.25;
input int InpTimerSeconds = 2;
input int InpDeviationPoints = 50;
input string InpStartupLogFileName = "a3_profit_lock_exit_manager_startup.csv";
input string InpManagementLogFileName = "a3_profit_lock_exit_manager_log.csv";

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
      Print("A3 profit-lock manager could not open ", file_name, " error=", GetLastError());
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

bool KillSwitchFileContainsKill(const string file_name)
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
   return ContainsText(content, "KILL");
}

bool FullStopActive()
{
   return KillSwitchFileContainsKill(InpFullStopFileName);
}

bool ExecutionKillSwitchActive()
{
   return KillSwitchFileContainsKill(InpExecutionKillSwitchFileName);
}

bool AccountLoginWhitelisted()
{
   return CsvContainsTextToken(InpAllowedAccountLoginsCsv, IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)));
}

bool MagicManaged(const long magic)
{
   if(magic == 933300)
      return false;
   return CsvContainsTextToken(InpManagedMagicsCsv, IntegerToString((int)magic));
}

string PositionStateName(const string prefix, const ulong ticket)
{
   return prefix + "_" + IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)) + "_" + IntegerToString((int)ticket);
}

double InitialStopForPosition(const ulong ticket, const double current_sl)
{
   string name = PositionStateName("A3PL_INITIAL_SL", ticket);
   if(GlobalVariableCheck(name))
      return GlobalVariableGet(name);
   if(current_sl > 0.0)
      GlobalVariableSet(name, current_sl);
   return current_sl;
}

double PositionRiskPrice(const ENUM_POSITION_TYPE type, const double open_price, const double initial_sl)
{
   if(initial_sl <= 0.0)
      return 0.0;
   if(type == POSITION_TYPE_BUY && initial_sl >= open_price)
      return 0.0;
   if(type == POSITION_TYPE_SELL && initial_sl <= open_price)
      return 0.0;
   return MathAbs(open_price - initial_sl);
}

double PositionUnrealizedR(const ENUM_POSITION_TYPE type, const double open_price, const double risk_price, const double bid, const double ask)
{
   if(risk_price <= 0.0)
      return 0.0;
   if(type == POSITION_TYPE_BUY)
      return (bid - open_price) / risk_price;
   if(type == POSITION_TYPE_SELL)
      return (open_price - ask) / risk_price;
   return 0.0;
}

double BestEnabledLockR(const double unrealized_r, string &rung_name, double &trigger_r)
{
   double best_lock_r = -DBL_MAX;
   rung_name = "";
   trigger_r = 0.0;
   if(InpPrimaryRungEnabled && unrealized_r >= InpPrimaryTriggerR && InpPrimaryLockR > best_lock_r)
   {
      best_lock_r = InpPrimaryLockR;
      rung_name = "PRIMARY_1_25_TO_0_80";
      trigger_r = InpPrimaryTriggerR;
   }
   if(InpSecondaryRungEnabled && unrealized_r >= InpSecondaryTriggerR && InpSecondaryLockR > best_lock_r)
   {
      best_lock_r = InpSecondaryLockR;
      rung_name = "SECONDARY";
      trigger_r = InpSecondaryTriggerR;
   }
   if(InpTertiaryRungEnabled && unrealized_r >= InpTertiaryTriggerR && InpTertiaryLockR > best_lock_r)
   {
      best_lock_r = InpTertiaryLockR;
      rung_name = "TERTIARY";
      trigger_r = InpTertiaryTriggerR;
   }
   return best_lock_r;
}

bool StopImprovesOnly(const ENUM_POSITION_TYPE type, const double current_sl, const double desired_sl)
{
   if(desired_sl <= 0.0)
      return false;
   if(type == POSITION_TYPE_BUY)
      return current_sl <= 0.0 || desired_sl > current_sl;
   if(type == POSITION_TYPE_SELL)
      return current_sl <= 0.0 || desired_sl < current_sl;
   return false;
}

bool StopRespectsBrokerDistance(const ENUM_POSITION_TYPE type, const string symbol, const double desired_sl, string &reason)
{
   double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
   if(point <= 0.0)
   {
      reason = "NO_SYMBOL_POINT";
      return false;
   }
   double stop_level = (double)SymbolInfoInteger(symbol, SYMBOL_TRADE_STOPS_LEVEL) * point;
   double freeze_level = (double)SymbolInfoInteger(symbol, SYMBOL_TRADE_FREEZE_LEVEL) * point;
   double min_distance = MathMax(stop_level, freeze_level);
   double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
   if(type == POSITION_TYPE_BUY && desired_sl > bid - min_distance)
   {
      reason = "BUY_SL_TOO_CLOSE_TO_BID";
      return false;
   }
   if(type == POSITION_TYPE_SELL && desired_sl < ask + min_distance)
   {
      reason = "SELL_SL_TOO_CLOSE_TO_ASK";
      return false;
   }
   reason = "OK";
   return true;
}

void WriteStartupRow(const string status, const string reason)
{
   string row[] = {
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      InpRunId,
      AccountInfoString(ACCOUNT_SERVER),
      IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)),
      _Symbol,
      InpTargetSymbol,
      InpManagedMagicsCsv,
      BoolText(InpDryRunOnly),
      BoolText(InpManageActionAllowed),
      InpExecutionKillSwitchFileName,
      InpFullStopFileName,
      BoolText(InpPrimaryRungEnabled),
      DoubleToString(InpPrimaryTriggerR, 2),
      DoubleToString(InpPrimaryLockR, 2),
      BoolText(InpSecondaryRungEnabled),
      BoolText(InpTertiaryRungEnabled),
      status,
      reason
   };
   AppendCsvRow(InpStartupLogFileName, row);
}

void WriteManagementRow(
   const string action,
   const ulong ticket,
   const long magic,
   const ENUM_POSITION_TYPE type,
   const double volume,
   const double open_price,
   const double initial_sl,
   const double current_sl,
   const double desired_sl,
   const double tp,
   const double unrealized_r,
   const double trigger_r,
   const double lock_r,
   const string rung_name,
   const uint retcode,
   const string reason)
{
   int digits = (int)SymbolInfoInteger(InpTargetSymbol, SYMBOL_DIGITS);
   string row[] = {
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      InpRunId,
      AccountInfoString(ACCOUNT_SERVER),
      IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)),
      InpTargetSymbol,
      IntegerToString((int)ticket),
      IntegerToString((int)magic),
      type == POSITION_TYPE_BUY ? "BUY" : "SELL",
      DoubleToString(volume, 2),
      DoubleToString(open_price, digits),
      DoubleToString(initial_sl, digits),
      DoubleToString(current_sl, digits),
      DoubleToString(desired_sl, digits),
      DoubleToString(tp, digits),
      DoubleToString(unrealized_r, 4),
      DoubleToString(trigger_r, 2),
      DoubleToString(lock_r, 2),
      rung_name,
      BoolText(InpDryRunOnly),
      BoolText(InpManageActionAllowed),
      action,
      IntegerToString((int)retcode),
      reason
   };
   AppendCsvRow(InpManagementLogFileName, row);
}

bool ModifyStopLossOnly(const ulong ticket, const long magic, const double desired_sl, const double tp, MqlTradeResult &result)
{
   MqlTradeRequest request;
   ZeroMemory(request);
   ZeroMemory(result);
   request.action = TRADE_ACTION_SLTP;
   request.position = ticket;
   request.symbol = InpTargetSymbol;
   request.magic = magic;
   request.sl = desired_sl;
   request.tp = tp;
   request.deviation = InpDeviationPoints;
   return OrderSend(request, result);
}

void ManagePosition()
{
   string symbol = PositionGetString(POSITION_SYMBOL);
   if(symbol != InpTargetSymbol)
      return;

   long magic = PositionGetInteger(POSITION_MAGIC);
   if(!MagicManaged(magic))
      return;

   ulong ticket = (ulong)PositionGetInteger(POSITION_TICKET);
   ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
   double volume = PositionGetDouble(POSITION_VOLUME);
   double open_price = PositionGetDouble(POSITION_PRICE_OPEN);
   double current_sl = PositionGetDouble(POSITION_SL);
   double tp = PositionGetDouble(POSITION_TP);
   double initial_sl = InitialStopForPosition(ticket, current_sl);
   double risk_price = PositionRiskPrice(type, open_price, initial_sl);
   if(risk_price <= 0.0)
   {
      WriteManagementRow("SKIP_INVALID_INITIAL_RISK", ticket, magic, type, volume, open_price, initial_sl, current_sl, current_sl, tp, 0.0, 0.0, 0.0, "", 0, "initial SL missing or not an original risk stop");
      return;
   }

   double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
   double unrealized_r = PositionUnrealizedR(type, open_price, risk_price, bid, ask);
   string rung_name = "";
   double trigger_r = 0.0;
   double lock_r = BestEnabledLockR(unrealized_r, rung_name, trigger_r);
   if(lock_r == -DBL_MAX)
      return;

   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   double floor_sl = type == POSITION_TYPE_BUY ? open_price + (lock_r * risk_price) : open_price - (lock_r * risk_price);
   double desired_sl = NormalizeDouble(floor_sl, digits);
   if(!StopImprovesOnly(type, current_sl, desired_sl))
      return;

   string distance_reason = "";
   if(!StopRespectsBrokerDistance(type, symbol, desired_sl, distance_reason))
   {
      WriteManagementRow("DEFER_STOPS_LEVEL", ticket, magic, type, volume, open_price, initial_sl, current_sl, desired_sl, tp, unrealized_r, trigger_r, lock_r, rung_name, 0, distance_reason);
      return;
   }

   if(ExecutionKillSwitchActive())
   {
      WriteManagementRow("EXECUTION_KILL_WOULD_BLOCK_SLTP", ticket, magic, type, volume, open_price, initial_sl, current_sl, desired_sl, tp, unrealized_r, trigger_r, lock_r, rung_name, 0, "execution kill switch active");
      return;
   }

   if(InpDryRunOnly || !InpManageActionAllowed)
   {
      string dry_state = PositionStateName("A3PL_DRYRUN_LOGGED", ticket);
      if(!GlobalVariableCheck(dry_state))
      {
         GlobalVariableSet(dry_state, TimeCurrent());
         WriteManagementRow("DRY_RUN_WOULD_MOVE_SL", ticket, magic, type, volume, open_price, initial_sl, current_sl, desired_sl, tp, unrealized_r, trigger_r, lock_r, rung_name, 0, "dry-run or manage action disabled");
      }
      return;
   }

   MqlTradeResult result;
   bool sent = ModifyStopLossOnly(ticket, magic, desired_sl, tp, result);
   WriteManagementRow(sent ? "SLTP_MODIFY_SENT" : "SLTP_MODIFY_FAILED", ticket, magic, type, volume, open_price, initial_sl, current_sl, desired_sl, tp, unrealized_r, trigger_r, lock_r, rung_name, result.retcode, result.comment);
}

bool ScopeLocksPass(string &reason)
{
   if(_Symbol != InpTargetSymbol)
   {
      reason = "chart symbol mismatch";
      return false;
   }
   if(!ContainsText(AccountInfoString(ACCOUNT_SERVER), InpExpectedServerMarker))
   {
      reason = "server marker is not demo";
      return false;
   }
   if(!AccountLoginWhitelisted())
   {
      reason = "account login not allowlisted";
      return false;
   }
   if(CsvContainsTextToken(InpManagedMagicsCsv, "933300"))
   {
      reason = "magic 933300 is excluded while internal exit logic is enabled";
      return false;
   }
   if(FullStopActive())
   {
      reason = "full stop is active";
      return false;
   }
   reason = "OK";
   return true;
}

int OnInit()
{
   string reason = "";
   if(!ScopeLocksPass(reason))
   {
      WriteStartupRow("INIT_FAILED", reason);
      Print("A3 profit-lock manager refused to start: ", reason);
      return INIT_FAILED;
   }

   EventSetTimer(MathMax(1, InpTimerSeconds));
   WriteStartupRow("ATTACHED_A3_PROFIT_LOCK_EXIT_MANAGER", "OK");
   Print("A3 profit-lock exit manager attached for ", InpTargetSymbol, " managed magics ", InpManagedMagicsCsv);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   string row[] = {
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      InpRunId,
      AccountInfoString(ACCOUNT_SERVER),
      IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)),
      _Symbol,
      "DEINIT",
      IntegerToString(reason)
   };
   AppendCsvRow(InpStartupLogFileName, row);
}

void OnTimer()
{
   if(FullStopActive())
      return;
   for(int index = PositionsTotal() - 1; index >= 0; index--)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0)
         continue;
      if(!PositionSelectByTicket(ticket))
         continue;
      ManagePosition();
   }
}

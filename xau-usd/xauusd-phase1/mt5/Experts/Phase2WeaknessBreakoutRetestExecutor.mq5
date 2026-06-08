// NON_CANONICAL / EXPERIMENTAL DEMO ONLY / DO NOT DEPLOY AS PHASE2.
// Owner-requested weakness-review executor. It trades only XAUUSD breakout_retest
// on a demo account, with a separate magic/comment/log namespace from older EAs.
#property strict
#property version   "1.000"
#property description "P2WEAKNESS_BR_V1 demo-only XAUUSD breakout-retest executor."

#include <Phase1/Phase1Types.mqh>
#include <Phase1/Phase1BreakoutRetest.mqh>

input string InpRunId = "P2WEAKNESS_BR_V1";
input bool InpDryRunOnly = true;
input bool InpBrokerActionAllowed = false;
input string InpTargetSymbol = "XAUUSD";
input string InpExpectedServerMarker = "Demo";
input string InpAllowedAccountLoginsCsv = "";
input string InpExperimentalAuthorizationToken = "";
input string InpRequiredExperimentalAuthorizationToken = "EXPERIMENTAL_DEMO_AUTHORIZED_REVIEW_ONLY";
input string InpCostSuspensionAcknowledgementToken = "";
input string InpRequiredCostSuspensionAcknowledgementToken = "I_ACKNOWLEDGE_COST_SUSPENDED_NON_CANONICAL_EXPERIMENT";
input string InpCandidateStatus = "EXPERIMENTAL_QUARANTINE_REVIEW_ONLY";
input string InpFamilyLifecycleStatus = "COST_SUSPENDED_CANONICAL";
input string InpKillSwitchFileName = "p2weakness_br_v1_kill_switch.txt";
input string InpSignalLogFileName = "p2weakness_br_v1_signal_log_xauusd.csv";
input string InpStartupLogFileName = "p2weakness_br_v1_startup_xauusd.csv";
input string InpOrderLogFileName = "p2weakness_br_v1_order_log_xauusd.csv";
input double InpFixedLot = 0.01;
input int InpMagicNumber = 931000;
input int InpMaxOrdersPerDay = 6;
input int InpMaxAccountOrdersPerDay = 12;
input int InpMinSecondsBetweenOrders = 300;
input int InpMaxOpenPositionsPerInstance = 1;
input int InpMaxFamilyOpenPositions = 3;
input int InpDuplicateLockBars = 12;
input int InpDeviationPoints = 50;
input double InpMaxEstimatedCostR = 0.30;
input double InpMaxMeasuredSpreadPoints = 75.0;

CPhase1BreakoutRetestObserver g_breakout_observer;
datetime g_last_m5_bar_time = 0;
datetime g_last_order_submit_time = 0;
string g_order_day_key = "";
int g_orders_today = 0;

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
   return CsvContainsTextToken(InpAllowedAccountLoginsCsv, IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)));
}

bool ExperimentalAuthorizationTokenValid()
{
   return TrimToken(InpExperimentalAuthorizationToken) == TrimToken(InpRequiredExperimentalAuthorizationToken);
}

bool CostSuspensionAcknowledgementTokenValid()
{
   if(!ContainsText(InpFamilyLifecycleStatus, "COST_SUSPENDED"))
      return true;
   return TrimToken(InpCostSuspensionAcknowledgementToken) == TrimToken(InpRequiredCostSuspensionAcknowledgementToken);
}

bool BrokerActionModeRequested()
{
   return !InpDryRunOnly && InpBrokerActionAllowed;
}

bool SourceDefaultSafe()
{
   return true;
}

bool OwnerAuthorizedSetUsed()
{
   return BrokerActionModeRequested()
      && StringLen(TrimToken(InpAllowedAccountLoginsCsv)) > 0
      && StringLen(TrimToken(InpExperimentalAuthorizationToken)) > 0
      && ExperimentalAuthorizationTokenValid()
      && CostSuspensionAcknowledgementTokenValid();
}

double CurrentSpreadPoints()
{
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   if(point <= 0.0)
      return 0.0;
   return (SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID)) / point;
}

double EstimatedCostRForObservation(const Phase1BreakoutRetestObservation &observation, const double spread_points)
{
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double risk_price = MathAbs(observation.entry_price - observation.stop_loss);
   if(point <= 0.0 || risk_price <= 0.0)
      return 0.0;
   return spread_points * point / risk_price;
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

bool KillSwitchActive()
{
   if(!FileIsExist(InpKillSwitchFileName))
      return false;
   int handle = FileOpen(InpKillSwitchFileName, FILE_READ | FILE_TXT | FILE_ANSI | FILE_SHARE_READ | FILE_SHARE_WRITE);
   if(handle == INVALID_HANDLE)
      return false;
   string content = "";
   while(!FileIsEnding(handle))
      content += " " + FileReadString(handle);
   FileClose(handle);
   return ContainsText(content, "KILL");
}

string CompactDateKey()
{
   string key = TimeToString(TimeCurrent(), TIME_DATE);
   StringReplace(key, ".", "");
   StringReplace(key, "-", "");
   StringReplace(key, " ", "");
   return key;
}

string AccountOrderCounterName()
{
   return "P2W_ORD_" + IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)) + "_" + CompactDateKey();
}

int AccountOrdersToday()
{
   string name = AccountOrderCounterName();
   if(!GlobalVariableCheck(name))
      return 0;
   return (int)GlobalVariableGet(name);
}

void IncrementAccountOrdersToday()
{
   string name = AccountOrderCounterName();
   GlobalVariableSet(name, (double)(AccountOrdersToday() + 1));
}

bool IsDemoFamilyMagic(const long magic)
{
   return (magic >= 920000 && magic < 921000)
      || (magic >= 930000 && magic < 931000)
      || (magic >= 931000 && magic < 931100);
}

bool DirectionMatchesPosition(const bool is_long)
{
   long type = PositionGetInteger(POSITION_TYPE);
   return (is_long && type == POSITION_TYPE_BUY) || (!is_long && type == POSITION_TYPE_SELL);
}

bool DirectionMatchesOrder(const bool is_long)
{
   long type = OrderGetInteger(ORDER_TYPE);
   if(is_long)
      return type == ORDER_TYPE_BUY || type == ORDER_TYPE_BUY_LIMIT || type == ORDER_TYPE_BUY_STOP || type == ORDER_TYPE_BUY_STOP_LIMIT;
   return type == ORDER_TYPE_SELL || type == ORDER_TYPE_SELL_LIMIT || type == ORDER_TYPE_SELL_STOP || type == ORDER_TYPE_SELL_STOP_LIMIT;
}

int CountOpenExposureForInstance()
{
   int count = 0;
   for(int index = 0; index < PositionsTotal(); index++)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == InpMagicNumber)
         count++;
   }
   for(int index = 0; index < OrdersTotal(); index++)
   {
      ulong ticket = OrderGetTicket(index);
      if(ticket == 0 || !OrderSelect(ticket))
         continue;
      if(OrderGetString(ORDER_SYMBOL) == _Symbol && OrderGetInteger(ORDER_MAGIC) == InpMagicNumber)
         count++;
   }
   return count;
}

int CountOpenExposureForDemoFamily()
{
   int count = 0;
   for(int index = 0; index < PositionsTotal(); index++)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol && IsDemoFamilyMagic((long)PositionGetInteger(POSITION_MAGIC)))
         count++;
   }
   for(int index = 0; index < OrdersTotal(); index++)
   {
      ulong ticket = OrderGetTicket(index);
      if(ticket == 0 || !OrderSelect(ticket))
         continue;
      if(OrderGetString(ORDER_SYMBOL) == _Symbol && IsDemoFamilyMagic((long)OrderGetInteger(ORDER_MAGIC)))
         count++;
   }
   return count;
}

bool SameDirectionFamilyExposureExists(const bool is_long)
{
   for(int index = 0; index < PositionsTotal(); index++)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol
         && IsDemoFamilyMagic((long)PositionGetInteger(POSITION_MAGIC))
         && DirectionMatchesPosition(is_long))
         return true;
   }
   for(int index = 0; index < OrdersTotal(); index++)
   {
      ulong ticket = OrderGetTicket(index);
      if(ticket == 0 || !OrderSelect(ticket))
         continue;
      if(OrderGetString(ORDER_SYMBOL) == _Symbol
         && IsDemoFamilyMagic((long)OrderGetInteger(ORDER_MAGIC))
         && DirectionMatchesOrder(is_long))
         return true;
   }
   return false;
}

string DuplicateLockKey(const Phase1BreakoutRetestObservation &observation)
{
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double bucket_size = point > 0.0 ? 50.0 * point : 0.50;
   int level_bucket = bucket_size > 0.0 ? (int)MathRound(observation.level_price / bucket_size) : 0;
   string direction = observation.direction_text == "LONG" ? "L" : "S";
   return "P2WBR_" + IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)) + "_" + _Symbol + "_" + direction + "_" + IntegerToString(level_bucket);
}

bool DuplicateFamilyLockActive(const Phase1BreakoutRetestObservation &observation)
{
   if(InpDuplicateLockBars <= 0)
      return false;
   string key = DuplicateLockKey(observation);
   if(!GlobalVariableCheck(key))
      return false;
   double last_time = GlobalVariableGet(key);
   int lock_seconds = InpDuplicateLockBars * PeriodSeconds(PERIOD_M5);
   return lock_seconds > 0 && (TimeCurrent() - (datetime)last_time) < lock_seconds;
}

void SetDuplicateFamilyLock(const Phase1BreakoutRetestObservation &observation)
{
   if(InpDuplicateLockBars <= 0)
      return;
   GlobalVariableSet(DuplicateLockKey(observation), (double)TimeCurrent());
}

void ResetDailyOrderCounterIfNeeded()
{
   string today = TimeToString(TimeCurrent(), TIME_DATE);
   if(today != g_order_day_key)
   {
      g_order_day_key = today;
      g_orders_today = 0;
   }
}

double NormalizeVolumeForSymbol(const double requested)
{
   double min_volume = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double max_volume = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double volume = requested;
   if(min_volume > 0.0 && volume < min_volume)
      volume = min_volume;
   if(max_volume > 0.0 && volume > max_volume)
      volume = max_volume;
   if(step > 0.0)
      volume = MathFloor(volume / step) * step;
   int digits = 2;
   if(step > 0.0 && step < 0.01)
      digits = 3;
   if(step > 0.0 && step < 0.001)
      digits = 4;
   return NormalizeDouble(volume, digits);
}

ENUM_ORDER_TYPE_FILLING FillPolicy()
{
   int filling = (int)SymbolInfoInteger(_Symbol, SYMBOL_FILLING_MODE);
   if((filling & SYMBOL_FILLING_IOC) == SYMBOL_FILLING_IOC)
      return ORDER_FILLING_IOC;
   if((filling & SYMBOL_FILLING_FOK) == SYMBOL_FILLING_FOK)
      return ORDER_FILLING_FOK;
   return ORDER_FILLING_RETURN;
}

bool EnsureSignalLogHeader()
{
   if(FileIsExist(InpSignalLogFileName))
      return true;
   string header[] = {
      "timestamp_broker",
      "timestamp_utc",
      "timestamp_local",
      "run_id",
      "account_server",
      "account_login",
      "symbol",
      "candidate",
      "candidate_status",
      "family_lifecycle_status",
      "magic",
      "order_comment",
      "m5_bar_time",
      "bid",
      "ask",
      "spread_points",
      "stage",
      "direction",
      "would_signal",
      "reason_code",
      "level_kind",
      "level_price",
      "entry_price",
      "stop_loss",
      "take_profit",
      "stop_distance_points",
      "duplicate_lock_key"
   };
   return AppendCsvRow(InpSignalLogFileName, header);
}

bool EnsureStartupLogHeader()
{
   if(FileIsExist(InpStartupLogFileName))
      return true;
   string header[] = {
      "timestamp_broker",
      "timestamp_utc",
      "timestamp_local",
      "run_id",
      "account_server",
      "account_login",
      "symbol",
      "candidate",
      "candidate_status",
      "family_lifecycle_status",
      "magic",
      "order_comment",
      "dry_run",
      "broker_action_allowed",
      "allowed_account_logins",
      "authorization_token_present",
      "source_default_safe",
      "owner_authorized_set_used",
      "experimental_authorization_token_present",
      "cost_suspension_acknowledged",
      "max_orders_per_day",
      "max_account_orders_per_day",
      "max_family_open_positions",
      "duplicate_lock_bars",
      "max_estimated_cost_R",
      "max_measured_spread_points",
      "kill_switch_file",
      "startup_status"
   };
   return AppendCsvRow(InpStartupLogFileName, header);
}

bool EnsureOrderLogHeader()
{
   if(FileIsExist(InpOrderLogFileName))
      return true;
   string header[] = {
      "timestamp_broker",
      "timestamp_utc",
      "timestamp_local",
      "run_id",
      "account_server",
      "account_login",
      "symbol",
      "candidate",
      "candidate_status",
      "family_lifecycle_status",
      "magic",
      "order_comment",
      "broker_action_allowed",
      "dry_run",
      "action",
      "direction",
      "volume",
      "order_mode",
      "spread_at_signal_points",
      "spread_at_order_points",
      "signal_entry_price",
      "request_price",
      "sl",
      "tp",
      "retcode",
      "retcode_description",
      "order_ticket",
      "deal_ticket",
      "result_price",
      "result_volume",
      "slippage_points",
      "estimated_cost_R",
      "stop_distance_points",
      "account_orders_today",
      "family_open_exposure",
      "duplicate_lock_key",
      "reason_code",
      "guard_reason"
   };
   return AppendCsvRow(InpOrderLogFileName, header);
}

string InstanceComment()
{
   return "P2WEAKNESS_BR_V1";
}

string CandidateName()
{
   return "breakout_retest";
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
      CandidateName(),
      InpCandidateStatus,
      InpFamilyLifecycleStatus,
      IntegerToString(InpMagicNumber),
      InstanceComment(),
      BoolText(InpDryRunOnly),
      BoolText(InpBrokerActionAllowed),
      InpAllowedAccountLoginsCsv,
      BoolText(StringLen(TrimToken(InpExperimentalAuthorizationToken)) > 0),
      BoolText(SourceDefaultSafe()),
      BoolText(OwnerAuthorizedSetUsed()),
      BoolText(StringLen(TrimToken(InpExperimentalAuthorizationToken)) > 0),
      BoolText(CostSuspensionAcknowledgementTokenValid()),
      IntegerToString(InpMaxOrdersPerDay),
      IntegerToString(InpMaxAccountOrdersPerDay),
      IntegerToString(InpMaxFamilyOpenPositions),
      IntegerToString(InpDuplicateLockBars),
      DoubleToString(InpMaxEstimatedCostR, 4),
      DoubleToString(InpMaxMeasuredSpreadPoints, 2),
      InpKillSwitchFileName,
      status_text
   };
   return AppendCsvRow(InpStartupLogFileName, row);
}

void WriteSignalLogRow(const Phase1BreakoutRetestObservation &observation, const datetime m5_bar_time)
{
   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double spread_points = CurrentSpreadPoints();
   string duplicate_key = observation.level_price > 0.0 ? DuplicateLockKey(observation) : "";
   string row[] = {
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS),
      InpRunId,
      AccountInfoString(ACCOUNT_SERVER),
      IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)),
      _Symbol,
      CandidateName(),
      InpCandidateStatus,
      InpFamilyLifecycleStatus,
      IntegerToString(InpMagicNumber),
      InstanceComment(),
      TimeToString(m5_bar_time, TIME_DATE | TIME_SECONDS),
      DoubleToString(bid, digits),
      DoubleToString(ask, digits),
      DoubleToString(spread_points, 2),
      observation.stage,
      observation.direction_text,
      BoolText(observation.would_signal),
      observation.reason_code,
      observation.level_kind,
      DoubleToString(observation.level_price, digits),
      DoubleToString(observation.entry_price, digits),
      DoubleToString(observation.stop_loss, digits),
      DoubleToString(observation.take_profit, digits),
      DoubleToString(observation.stop_distance_points, 2),
      duplicate_key
   };
   AppendCsvRow(InpSignalLogFileName, row);
}

void WriteOrderLogRow(
   const string action,
   const Phase1BreakoutRetestObservation &observation,
   const double volume,
   const double request_price,
   const double sl,
   const double tp,
   const MqlTradeResult &result,
   const string guard_reason,
   const string order_mode,
   const double spread_at_signal_points,
   const double spread_at_order_points,
   const double estimated_cost_r,
   const double stop_distance_points
)
{
   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double slippage_points = (point > 0.0 && result.price > 0.0 && request_price > 0.0)
      ? MathAbs(result.price - request_price) / point
      : 0.0;
   string duplicate_key = observation.level_price > 0.0 ? DuplicateLockKey(observation) : "";
   string row[] = {
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS),
      InpRunId,
      AccountInfoString(ACCOUNT_SERVER),
      IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)),
      _Symbol,
      CandidateName(),
      InpCandidateStatus,
      InpFamilyLifecycleStatus,
      IntegerToString(InpMagicNumber),
      InstanceComment(),
      BoolText(InpBrokerActionAllowed),
      BoolText(InpDryRunOnly),
      action,
      observation.direction_text,
      DoubleToString(volume, 2),
      order_mode,
      DoubleToString(spread_at_signal_points, 2),
      DoubleToString(spread_at_order_points, 2),
      DoubleToString(observation.entry_price, digits),
      DoubleToString(request_price, digits),
      DoubleToString(sl, digits),
      DoubleToString(tp, digits),
      IntegerToString((int)result.retcode),
      result.comment,
      IntegerToString((int)result.order),
      IntegerToString((int)result.deal),
      DoubleToString(result.price, digits),
      DoubleToString(result.volume, 2),
      DoubleToString(slippage_points, 2),
      DoubleToString(estimated_cost_r, 4),
      DoubleToString(stop_distance_points, 2),
      IntegerToString(AccountOrdersToday()),
      IntegerToString(CountOpenExposureForDemoFamily()),
      duplicate_key,
      observation.reason_code,
      guard_reason
   };
   AppendCsvRow(InpOrderLogFileName, row);
}

bool TradingGuardsPass(
   const Phase1BreakoutRetestObservation &observation,
   const double spread_points,
   const double estimated_cost_r,
   string &guard_reason
)
{
   ResetDailyOrderCounterIfNeeded();
   if(InpDryRunOnly)
   {
      guard_reason = "dry_run_only_true";
      return false;
   }
   if(!InpBrokerActionAllowed)
   {
      guard_reason = "broker_action_not_allowed";
      return false;
   }
   if(KillSwitchActive())
   {
      guard_reason = "kill_switch_active";
      return false;
   }
   if(!ExperimentalAuthorizationTokenValid())
   {
      guard_reason = "experimental_authorization_token_missing_or_invalid";
      return false;
   }
   if(!CostSuspensionAcknowledgementTokenValid())
   {
      guard_reason = "cost_suspension_acknowledgement_token_missing_or_invalid";
      return false;
   }
   if(!AccountLoginWhitelisted())
   {
      guard_reason = "account_login_not_whitelisted";
      return false;
   }
   string server = AccountInfoString(ACCOUNT_SERVER);
   if(server == "" || !ContainsText(server, InpExpectedServerMarker) || ContainsText(server, "live") || ContainsText(server, "real"))
   {
      guard_reason = "not_demo_server";
      return false;
   }
   if(_Symbol != InpTargetSymbol || _Symbol != "XAUUSD")
   {
      guard_reason = "symbol_not_xauusd_target";
      return false;
   }
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) || !MQLInfoInteger(MQL_TRADE_ALLOWED) || !AccountInfoInteger(ACCOUNT_TRADE_ALLOWED))
   {
      guard_reason = "terminal_or_account_trading_disabled";
      return false;
   }
   if(!observation.would_signal)
   {
      guard_reason = "no_signal";
      return false;
   }
   if(observation.entry_price <= 0.0 || observation.stop_loss <= 0.0 || observation.take_profit <= 0.0)
   {
      guard_reason = "missing_entry_sl_tp";
      return false;
   }
   if(InpMaxMeasuredSpreadPoints > 0.0 && spread_points > InpMaxMeasuredSpreadPoints)
   {
      guard_reason = "measured_spread_points_exceeds_threshold";
      return false;
   }
   if(InpMaxEstimatedCostR > 0.0 && estimated_cost_r > InpMaxEstimatedCostR)
   {
      guard_reason = "estimated_cost_r_exceeds_threshold";
      return false;
   }
   if(InpMaxOrdersPerDay > 0 && g_orders_today >= InpMaxOrdersPerDay)
   {
      guard_reason = "max_orders_per_day_reached";
      return false;
   }
   if(InpMaxAccountOrdersPerDay > 0 && AccountOrdersToday() >= InpMaxAccountOrdersPerDay)
   {
      guard_reason = "max_account_orders_per_day_reached";
      return false;
   }
   if(InpMinSecondsBetweenOrders > 0 && g_last_order_submit_time > 0 && TimeCurrent() - g_last_order_submit_time < InpMinSecondsBetweenOrders)
   {
      guard_reason = "min_seconds_between_orders";
      return false;
   }
   if(InpMaxOpenPositionsPerInstance > 0 && CountOpenExposureForInstance() >= InpMaxOpenPositionsPerInstance)
   {
      guard_reason = "open_instance_exposure_exists";
      return false;
   }
   if(InpMaxFamilyOpenPositions > 0 && CountOpenExposureForDemoFamily() >= InpMaxFamilyOpenPositions)
   {
      guard_reason = "family_open_exposure_cap_reached";
      return false;
   }
   bool is_long = observation.direction_text == "LONG";
   if(SameDirectionFamilyExposureExists(is_long))
   {
      guard_reason = "duplicate_same_direction_family_exposure_exists";
      return false;
   }
   if(DuplicateFamilyLockActive(observation))
   {
      guard_reason = "duplicate_family_lock_active";
      return false;
   }
   guard_reason = "pass";
   return true;
}

bool SendDemoMarketOrder(const Phase1BreakoutRetestObservation &observation)
{
   string guard_reason = "";
   MqlTradeResult result;
   ZeroMemory(result);
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double spread_at_signal_points = CurrentSpreadPoints();
   double estimated_cost_r_signal = EstimatedCostRForObservation(observation, spread_at_signal_points);
   if(!TradingGuardsPass(observation, spread_at_signal_points, estimated_cost_r_signal, guard_reason))
   {
      WriteOrderLogRow("GUARD_BLOCK", observation, 0.0, 0.0, 0.0, 0.0, result, guard_reason, "MARKET_PROXY", spread_at_signal_points, spread_at_signal_points, estimated_cost_r_signal, observation.stop_distance_points);
      return false;
   }

   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   bool is_long = observation.direction_text == "LONG";
   double price = is_long ? ask : bid;
   double signal_risk = MathAbs(observation.entry_price - observation.stop_loss);
   int stops_level = (int)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double min_distance = (stops_level + 5) * point;
   double spread_distance = MathAbs(ask - bid);
   if(spread_distance > 0.0 && min_distance < 3.0 * spread_distance)
      min_distance = 3.0 * spread_distance;
   if(_Symbol == "XAUUSD" && min_distance < 300.0 * point)
      min_distance = 300.0 * point;
   if(signal_risk < min_distance)
      signal_risk = min_distance;
   if(signal_risk <= 0.0 || price <= 0.0)
   {
      guard_reason = "invalid_price_or_risk";
      WriteOrderLogRow("GUARD_BLOCK", observation, 0.0, price, 0.0, 0.0, result, guard_reason, "MARKET_PROXY", spread_at_signal_points, spread_at_signal_points, 0.0, observation.stop_distance_points);
      return false;
   }
   double stop_distance_points = point > 0.0 ? signal_risk / point : 0.0;
   double sl = is_long ? price - signal_risk : price + signal_risk;
   double tp = is_long ? price + 1.50 * signal_risk : price - 1.50 * signal_risk;
   sl = NormalizeDouble(sl, digits);
   tp = NormalizeDouble(tp, digits);
   price = NormalizeDouble(price, digits);
   double volume = NormalizeVolumeForSymbol(InpFixedLot);
   if(volume <= 0.0)
   {
      guard_reason = "invalid_volume";
      WriteOrderLogRow("GUARD_BLOCK", observation, 0.0, price, sl, tp, result, guard_reason, "MARKET_PROXY", spread_at_signal_points, spread_at_signal_points, 0.0, stop_distance_points);
      return false;
   }

   MqlTradeRequest request;
   ZeroMemory(request);
   request.action = TRADE_ACTION_DEAL;
   request.symbol = _Symbol;
   request.magic = InpMagicNumber;
   request.volume = volume;
   request.type = is_long ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   request.price = price;
   request.sl = sl;
   request.tp = tp;
   request.deviation = InpDeviationPoints;
   request.type_filling = FillPolicy();
   request.type_time = ORDER_TIME_GTC;
   request.comment = InstanceComment();

   bool sent = OrderSend(request, result);
   string action = sent ? "ORDER_SEND_OK" : "ORDER_SEND_FAIL";
   if(sent && (result.retcode == TRADE_RETCODE_DONE || result.retcode == TRADE_RETCODE_PLACED || result.retcode == TRADE_RETCODE_DONE_PARTIAL))
   {
      g_last_order_submit_time = TimeCurrent();
      g_orders_today++;
      IncrementAccountOrdersToday();
      SetDuplicateFamilyLock(observation);
   }
   double spread_at_order_points = CurrentSpreadPoints();
   double estimated_cost_r = signal_risk > 0.0 ? (spread_at_order_points * point / signal_risk) : 0.0;
   WriteOrderLogRow(action, observation, volume, price, sl, tp, result, guard_reason, "MARKET_PROXY", spread_at_signal_points, spread_at_order_points, estimated_cost_r, stop_distance_points);
   return sent;
}

int OnInit()
{
   if(_Symbol != InpTargetSymbol || _Symbol != "XAUUSD")
   {
      Print("P2WEAKNESS_BR_V1 attached to ", _Symbol, " but target is XAUUSD.");
      return INIT_FAILED;
   }
   if(InpMagicNumber < 931000 || InpMagicNumber >= 931100)
   {
      Print("P2WEAKNESS_BR_V1 refused magic number outside 931000-931099: ", InpMagicNumber);
      return INIT_FAILED;
   }
   if(!EnsureSignalLogHeader() || !EnsureStartupLogHeader() || !EnsureOrderLogHeader())
      return INIT_FAILED;

   if(BrokerActionModeRequested())
   {
      string server = AccountInfoString(ACCOUNT_SERVER);
      if(server == "" || !ContainsText(server, InpExpectedServerMarker) || ContainsText(server, "live") || ContainsText(server, "real"))
      {
         WriteStartupRow("REFUSED_NOT_DEMO_SERVER");
         Print("P2WEAKNESS_BR_V1 refused to start outside expected demo server. Server=", server);
         return INIT_FAILED;
      }
      if(!ExperimentalAuthorizationTokenValid())
      {
         WriteStartupRow("REFUSED_INVALID_EXPERIMENTAL_AUTHORIZATION_TOKEN");
         Print("P2WEAKNESS_BR_V1 refused to start without a valid experimental authorization token.");
         return INIT_FAILED;
      }
      if(!CostSuspensionAcknowledgementTokenValid())
      {
         WriteStartupRow("REFUSED_MISSING_COST_SUSPENSION_ACKNOWLEDGEMENT");
         Print("P2WEAKNESS_BR_V1 refused to start without a valid cost-suspension acknowledgement token.");
         return INIT_FAILED;
      }
      if(!AccountLoginWhitelisted())
      {
         WriteStartupRow("REFUSED_ACCOUNT_LOGIN_NOT_WHITELISTED");
         Print("P2WEAKNESS_BR_V1 refused account login ", (int)AccountInfoInteger(ACCOUNT_LOGIN), " because it is not in InpAllowedAccountLoginsCsv.");
         return INIT_FAILED;
      }
      if(KillSwitchActive())
      {
         WriteStartupRow("REFUSED_KILL_SWITCH_ACTIVE");
         Print("P2WEAKNESS_BR_V1 refused to start because kill switch is active.");
         return INIT_FAILED;
      }
   }

   g_breakout_observer.Configure(false);
   ResetDailyOrderCounterIfNeeded();
   WriteStartupRow(BrokerActionModeRequested() ? "ATTACHED_OWNER_AUTHORIZED_WEAKNESS_REVIEW_DEMO_EXECUTOR_ENABLED" : "ATTACHED_SAFE_DEFAULT_REVIEW_ONLY_NO_BROKER_ACTION");
   EventSetTimer(1);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   WriteStartupRow("REMOVED_REASON_" + IntegerToString(reason));
}

void OnTimer()
{
   datetime m5_bar_time = iTime(_Symbol, PERIOD_M5, 0);
   if(m5_bar_time <= 0 || m5_bar_time == g_last_m5_bar_time)
      return;
   g_last_m5_bar_time = m5_bar_time;

   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   Phase1BreakoutRetestObservation observation;
   Phase1ResetBreakoutRetestObservation(observation);
   g_breakout_observer.Evaluate(_Symbol, point, observation);
   WriteSignalLogRow(observation, m5_bar_time);
   if(observation.would_signal)
      SendDemoMarketOrder(observation);
}

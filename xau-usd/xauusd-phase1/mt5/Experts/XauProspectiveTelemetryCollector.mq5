#property strict
#property version   "1.000"
#property description "Passive XAU prospective telemetry collector. No broker actions or order placement."

input string InpRunId = "xau-prospective-telemetry-v1";
input bool InpDryRunOnly = true;
input string InpTargetSymbol = "XAUUSD";
input string InpExpectedServerMarker = "Demo";
input string InpAllowedAccountLoginsCsv = "1025742,1033030,1033669";
input bool InpCollectTicks = true;
input bool InpCollectMarketDepth = true;
input bool InpCollectTradeTransactions = true;
input int InpHeartbeatSeconds = 5;
input int InpFlushEveryRows = 100;
input string InpFilePrefix = "xau_prospective";

const bool BROKER_ACTION_ALLOWED = false;
const bool TRADE_PERMISSION = false;
const bool PYTHON_EXECUTION_AUTHORIZED = false;

int g_tick_handle = INVALID_HANDLE;
int g_book_handle = INVALID_HANDLE;
int g_transaction_handle = INVALID_HANDLE;
int g_heartbeat_handle = INVALID_HANDLE;
string g_file_date = "";
bool g_book_subscribed = false;
int g_book_subscription_error = 0;
int g_book_get_failures = 0;
long g_tick_rows = 0;
long g_book_rows = 0;
long g_transaction_rows = 0;
long g_heartbeat_rows = 0;
ulong g_book_snapshot_sequence = 0;

string BoolText(const bool value)
  {
   return value ? "true" : "false";
  }

string LowerText(string value)
  {
   StringToLower(value);
   return value;
  }

bool ContainsText(const string haystack,const string needle)
  {
   return StringFind(LowerText(haystack),LowerText(needle)) >= 0;
  }

string TrimToken(string value)
  {
   StringTrimLeft(value);
   StringTrimRight(value);
   return value;
  }

bool CsvContainsToken(const string csv,const string wanted)
  {
   string tokens[];
   int count=StringSplit(csv,',',tokens);
   string wanted_trimmed=TrimToken(wanted);
   for(int index=0; index<count; index++)
     {
      if(TrimToken(tokens[index]) == wanted_trimmed)
         return true;
     }
   return false;
  }

string LoginText()
  {
   return StringFormat("%I64d",AccountInfoInteger(ACCOUNT_LOGIN));
  }

bool AccountLoginWhitelisted()
  {
   string allowed=TrimToken(InpAllowedAccountLoginsCsv);
   if(allowed == "")
      return true;
   return CsvContainsToken(allowed,LoginText());
  }

string SafeFileToken(string value)
  {
   StringReplace(value," ","_");
   StringReplace(value,".","_");
   StringReplace(value,"-","_");
   StringReplace(value,"/","_");
   StringReplace(value,"\\","_");
   StringReplace(value,":","_");
   if(value == "")
      value="unknown";
   return value;
  }

string DateToken(const datetime value)
  {
   MqlDateTime parts;
   TimeToStruct(value,parts);
   return StringFormat("%04d%02d%02d",parts.year,parts.mon,parts.day);
  }

string UtcTimestamp(const datetime value)
  {
   return TimeToString(value,TIME_DATE | TIME_SECONDS) + "Z";
  }

string UtcTimestampMilliseconds(const long time_msc)
  {
   if(time_msc <= 0)
      return UtcTimestamp(TimeGMT());
   datetime seconds=(datetime)(time_msc / 1000);
   int milliseconds=(int)(time_msc % 1000);
   return TimeToString(seconds,TIME_DATE | TIME_SECONDS)
          + StringFormat(".%03dZ",milliseconds);
  }

string LedgerFileName(const string ledger,const bool daily,const string daily_token)
  {
   string base=SafeFileToken(InpFilePrefix)
               + "_" + SafeFileToken(LoginText())
               + "_" + SafeFileToken(AccountInfoString(ACCOUNT_SERVER))
               + "_" + SafeFileToken(InpTargetSymbol)
               + "_" + SafeFileToken(ledger);
   if(daily)
      base += "_" + daily_token;
   return base + ".csv";
  }

int OpenCsvForAppend(const string file_name)
  {
   int handle=FileOpen(
      file_name,
      FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_SHARE_READ | FILE_SHARE_WRITE,
      ','
   );
   if(handle == INVALID_HANDLE)
     {
      Print("XAU prospective collector could not open ",file_name," error=",GetLastError());
      return INVALID_HANDLE;
     }
   FileSeek(handle,0,SEEK_END);
   return handle;
  }

void CloseHandle(int &handle)
  {
   if(handle == INVALID_HANDLE)
      return;
   FileFlush(handle);
   FileClose(handle);
   handle=INVALID_HANDLE;
  }

void CloseDailyLedgers()
  {
   CloseHandle(g_tick_handle);
   CloseHandle(g_book_handle);
   CloseHandle(g_transaction_handle);
   CloseHandle(g_heartbeat_handle);
  }

void WriteTickHeader(const int handle)
  {
   FileWrite(handle,
      "schema_version","timestamp_utc","tick_time_msc","run_id","account_login",
      "account_server","broker_company","symbol","bid","ask","last","volume",
      "volume_real","tick_flags","spread_price","spread_points","point_size","digits",
      "dry_run","trade_permission","broker_action_allowed","python_execution_authorized"
   );
  }

void WriteBookHeader(const int handle)
  {
   FileWrite(handle,
      "schema_version","timestamp_utc","snapshot_id","source_event","run_id",
      "account_login","account_server","symbol","level_index","level_count","book_type",
      "price","volume","volume_real","subscription_active","subscription_error",
      "dry_run","trade_permission","broker_action_allowed","python_execution_authorized"
   );
  }

void WriteTransactionHeader(const int handle)
  {
   FileWrite(handle,
      "schema_version","timestamp_utc","run_id","account_login","account_server",
      "transaction_type","order_ticket","deal_ticket","position_id","position_by_id",
      "symbol","order_type","order_state","deal_type","transaction_volume",
      "transaction_price","price_trigger","price_sl","price_tp","request_action",
      "request_magic","request_order","request_symbol","request_volume","request_price",
      "request_sl","request_tp","request_deviation","request_order_type",
      "request_filling_type","request_time_type","request_expiration","request_comment",
      "result_retcode","result_deal","result_order","result_volume","result_price",
      "result_bid","result_ask","result_comment","request_id","retcode_external",
      "dry_run","trade_permission","broker_action_allowed","python_execution_authorized"
   );
  }

void WriteHeartbeatHeader(const int handle)
  {
   FileWrite(handle,
      "schema_version","timestamp_utc","timestamp_broker","run_id","account_login",
      "account_server","broker_company","symbol","terminal_connected","terminal_trade_allowed",
      "mql_trade_allowed","terminal_ping_us","account_trade_mode","account_balance","account_equity","account_margin",
      "account_margin_free","bid","ask","spread_points","last_tick_time_msc",
      "last_tick_age_ms","book_requested","book_subscribed","book_subscription_error",
      "book_get_failures","tick_rows","book_rows","transaction_rows","heartbeat_rows",
      "dry_run","trade_permission","broker_action_allowed","python_execution_authorized"
   );
  }

int OpenDailyLedger(const string ledger,const string daily_token)
  {
   string file_name=LedgerFileName(ledger,true,daily_token);
   bool needs_header=!FileIsExist(file_name);
   int handle=OpenCsvForAppend(file_name);
   if(handle == INVALID_HANDLE)
      return INVALID_HANDLE;
   if(needs_header || FileSize(handle) == 0)
     {
      if(ledger == "ticks")
         WriteTickHeader(handle);
      else if(ledger == "book")
         WriteBookHeader(handle);
      else if(ledger == "transactions")
         WriteTransactionHeader(handle);
      else if(ledger == "heartbeat")
         WriteHeartbeatHeader(handle);
      FileFlush(handle);
     }
   return handle;
  }

bool EnsureDailyLedgers(const string daily_token)
  {
   if(daily_token == g_file_date
      && g_tick_handle != INVALID_HANDLE
      && g_book_handle != INVALID_HANDLE
      && g_transaction_handle != INVALID_HANDLE
      && g_heartbeat_handle != INVALID_HANDLE)
      return true;

   CloseDailyLedgers();
   g_file_date=daily_token;
   g_tick_handle=OpenDailyLedger("ticks",daily_token);
   g_book_handle=OpenDailyLedger("book",daily_token);
   g_transaction_handle=OpenDailyLedger("transactions",daily_token);
   g_heartbeat_handle=OpenDailyLedger("heartbeat",daily_token);
   return g_tick_handle != INVALID_HANDLE
          && g_book_handle != INVALID_HANDLE
          && g_transaction_handle != INVALID_HANDLE
          && g_heartbeat_handle != INVALID_HANDLE;
  }

void FlushAtInterval(const int handle,const long row_count)
  {
   int interval=InpFlushEveryRows;
   if(interval < 1)
      interval=1;
   if(handle != INVALID_HANDLE && row_count % interval == 0)
      FileFlush(handle);
  }

void FlushAll()
  {
   if(g_tick_handle != INVALID_HANDLE)
      FileFlush(g_tick_handle);
   if(g_book_handle != INVALID_HANDLE)
      FileFlush(g_book_handle);
   if(g_transaction_handle != INVALID_HANDLE)
      FileFlush(g_transaction_handle);
   if(g_heartbeat_handle != INVALID_HANDLE)
      FileFlush(g_heartbeat_handle);
  }

void WriteStartupRow(const string status,const string reason)
  {
   string file_name=LedgerFileName("startup",false,"");
   bool needs_header=!FileIsExist(file_name);
   int handle=OpenCsvForAppend(file_name);
   if(handle == INVALID_HANDLE)
      return;
   if(needs_header || FileSize(handle) == 0)
     {
      FileWrite(handle,
         "schema_version","timestamp_utc","run_id","status","reason","account_login",
         "account_server","broker_company","account_trade_mode","terminal_trade_allowed",
         "mql_trade_allowed","symbol","target_symbol",
         "point_size","digits","tick_size","tick_value","contract_size","volume_min",
         "volume_step","swap_long","swap_short","symbol_trade_mode","symbol_book_depth","spread_float",
         "collect_ticks","collect_market_depth","collect_trade_transactions",
         "book_subscribed","book_subscription_error","dry_run","trade_permission",
         "broker_action_allowed","python_execution_authorized"
      );
     }
   FileWrite(handle,
      "xau_prospective_startup_v1",UtcTimestamp(TimeGMT()),InpRunId,status,reason,
      LoginText(),AccountInfoString(ACCOUNT_SERVER),AccountInfoString(ACCOUNT_COMPANY),
      StringFormat("%d",(int)AccountInfoInteger(ACCOUNT_TRADE_MODE)),
      BoolText((bool)TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)),
      BoolText((bool)MQLInfoInteger(MQL_TRADE_ALLOWED)),_Symbol,InpTargetSymbol,
      DoubleToString(SymbolInfoDouble(_Symbol,SYMBOL_POINT),8),
      StringFormat("%d",(int)SymbolInfoInteger(_Symbol,SYMBOL_DIGITS)),
      DoubleToString(SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_SIZE),8),
      DoubleToString(SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_VALUE),8),
      DoubleToString(SymbolInfoDouble(_Symbol,SYMBOL_TRADE_CONTRACT_SIZE),4),
      DoubleToString(SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN),4),
      DoubleToString(SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP),4),
      DoubleToString(SymbolInfoDouble(_Symbol,SYMBOL_SWAP_LONG),6),
      DoubleToString(SymbolInfoDouble(_Symbol,SYMBOL_SWAP_SHORT),6),
      StringFormat("%d",(int)SymbolInfoInteger(_Symbol,SYMBOL_TRADE_MODE)),
      StringFormat("%d",(int)SymbolInfoInteger(_Symbol,SYMBOL_TICKS_BOOKDEPTH)),
      BoolText((bool)SymbolInfoInteger(_Symbol,SYMBOL_SPREAD_FLOAT)),
      BoolText(InpCollectTicks),BoolText(InpCollectMarketDepth),
      BoolText(InpCollectTradeTransactions),BoolText(g_book_subscribed),
      StringFormat("%d",g_book_subscription_error),BoolText(InpDryRunOnly),
      BoolText(TRADE_PERMISSION),BoolText(BROKER_ACTION_ALLOWED),
      BoolText(PYTHON_EXECUTION_AUTHORIZED)
   );
   FileFlush(handle);
   FileClose(handle);
  }

void WriteTickRow()
  {
   if(!InpCollectTicks)
      return;
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol,tick))
      return;
   datetime tick_seconds=(datetime)(tick.time_msc / 1000);
   if(!EnsureDailyLedgers(DateToken(tick_seconds)))
      return;
   double point=SymbolInfoDouble(_Symbol,SYMBOL_POINT);
   double spread_price=tick.ask - tick.bid;
   double spread_points=point > 0.0 ? spread_price / point : 0.0;
   FileWrite(g_tick_handle,
      "xau_prospective_tick_v1",UtcTimestampMilliseconds(tick.time_msc),
      StringFormat("%I64d",tick.time_msc),InpRunId,LoginText(),
      AccountInfoString(ACCOUNT_SERVER),AccountInfoString(ACCOUNT_COMPANY),_Symbol,
      DoubleToString(tick.bid,_Digits),DoubleToString(tick.ask,_Digits),
      DoubleToString(tick.last,_Digits),StringFormat("%I64d",(long)tick.volume),
      DoubleToString(tick.volume_real,4),StringFormat("%u",tick.flags),
      DoubleToString(spread_price,_Digits),DoubleToString(spread_points,3),
      DoubleToString(point,8),StringFormat("%d",_Digits),BoolText(InpDryRunOnly),
      BoolText(TRADE_PERMISSION),BoolText(BROKER_ACTION_ALLOWED),
      BoolText(PYTHON_EXECUTION_AUTHORIZED)
   );
   g_tick_rows++;
   FlushAtInterval(g_tick_handle,g_tick_rows);
  }

void CaptureBookSnapshot(const string source_event)
  {
   if(!InpCollectMarketDepth || !g_book_subscribed)
      return;
   MqlTick tick;
   long time_msc=0;
   if(SymbolInfoTick(_Symbol,tick))
      time_msc=tick.time_msc;
   datetime event_seconds=time_msc > 0
      ? (datetime)(time_msc / 1000)
      : TimeGMT();
   if(!EnsureDailyLedgers(DateToken(event_seconds)))
      return;
   MqlBookInfo book[];
   ResetLastError();
   if(!MarketBookGet(_Symbol,book))
     {
      g_book_get_failures++;
      return;
     }
   int level_count=ArraySize(book);
   g_book_snapshot_sequence++;
   string snapshot_id=LoginText() + "-" + StringFormat("%I64u",g_book_snapshot_sequence);
   if(level_count == 0)
     {
      FileWrite(g_book_handle,
         "xau_prospective_book_v1",UtcTimestampMilliseconds(time_msc),snapshot_id,
         source_event,InpRunId,LoginText(),AccountInfoString(ACCOUNT_SERVER),_Symbol,
         "-1","0","EMPTY","","","",BoolText(g_book_subscribed),
         StringFormat("%d",g_book_subscription_error),BoolText(InpDryRunOnly),
         BoolText(TRADE_PERMISSION),BoolText(BROKER_ACTION_ALLOWED),
         BoolText(PYTHON_EXECUTION_AUTHORIZED)
      );
      g_book_rows++;
      FlushAtInterval(g_book_handle,g_book_rows);
      return;
     }
   for(int index=0; index<level_count; index++)
     {
      FileWrite(g_book_handle,
         "xau_prospective_book_v1",UtcTimestampMilliseconds(time_msc),snapshot_id,
         source_event,InpRunId,LoginText(),AccountInfoString(ACCOUNT_SERVER),_Symbol,
         StringFormat("%d",index),StringFormat("%d",level_count),EnumToString(book[index].type),
         DoubleToString(book[index].price,_Digits),StringFormat("%I64d",(long)book[index].volume),
         DoubleToString(book[index].volume_real,4),BoolText(g_book_subscribed),
         StringFormat("%d",g_book_subscription_error),BoolText(InpDryRunOnly),
         BoolText(TRADE_PERMISSION),BoolText(BROKER_ACTION_ALLOWED),
         BoolText(PYTHON_EXECUTION_AUTHORIZED)
      );
      g_book_rows++;
     }
   FlushAtInterval(g_book_handle,g_book_rows);
  }

void WriteHeartbeatRow()
  {
   datetime observed_at=TimeGMT();
   MqlTick tick;
   bool tick_available=SymbolInfoTick(_Symbol,tick);
   if(!EnsureDailyLedgers(DateToken(observed_at)))
      return;
   long now_msc=(long)TimeCurrent() * 1000;
   long tick_time_msc=tick_available ? tick.time_msc : 0;
   long tick_age_msc=tick_available ? (now_msc >= tick_time_msc ? now_msc - tick_time_msc : 0) : -1;
   double point=SymbolInfoDouble(_Symbol,SYMBOL_POINT);
   double spread_points=tick_available && point > 0.0 ? (tick.ask - tick.bid) / point : 0.0;
   FileWrite(g_heartbeat_handle,
      "xau_prospective_heartbeat_v1",UtcTimestamp(observed_at),
      TimeToString(TimeTradeServer(),TIME_DATE | TIME_SECONDS),InpRunId,LoginText(),
      AccountInfoString(ACCOUNT_SERVER),AccountInfoString(ACCOUNT_COMPANY),_Symbol,
      BoolText((bool)TerminalInfoInteger(TERMINAL_CONNECTED)),
      BoolText((bool)TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)),
      BoolText((bool)MQLInfoInteger(MQL_TRADE_ALLOWED)),
      StringFormat("%I64d",TerminalInfoInteger(TERMINAL_PING_LAST)),
      StringFormat("%d",(int)AccountInfoInteger(ACCOUNT_TRADE_MODE)),
      DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE),2),
      DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY),2),
      DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN),2),
      DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_FREE),2),
      tick_available ? DoubleToString(tick.bid,_Digits) : "",
      tick_available ? DoubleToString(tick.ask,_Digits) : "",
      tick_available ? DoubleToString(spread_points,3) : "",
      tick_available ? StringFormat("%I64d",tick.time_msc) : "",
      StringFormat("%I64d",tick_age_msc),BoolText(InpCollectMarketDepth),
      BoolText(g_book_subscribed),StringFormat("%d",g_book_subscription_error),
      StringFormat("%d",g_book_get_failures),StringFormat("%I64d",g_tick_rows),
      StringFormat("%I64d",g_book_rows),StringFormat("%I64d",g_transaction_rows),
      StringFormat("%I64d",g_heartbeat_rows + 1),BoolText(InpDryRunOnly),
      BoolText(TRADE_PERMISSION),BoolText(BROKER_ACTION_ALLOWED),
      BoolText(PYTHON_EXECUTION_AUTHORIZED)
   );
   g_heartbeat_rows++;
   FileFlush(g_heartbeat_handle);
   FlushAll();
  }

int OnInit()
  {
   if(!InpDryRunOnly)
     {
      WriteStartupRow("REFUSED","InpDryRunOnly must remain true");
      return INIT_FAILED;
     }
   if(_Symbol != InpTargetSymbol)
     {
      WriteStartupRow("REFUSED","attached symbol does not match InpTargetSymbol");
      return INIT_FAILED;
     }
   if(StringLen(TrimToken(InpExpectedServerMarker)) > 0
      && !ContainsText(AccountInfoString(ACCOUNT_SERVER),InpExpectedServerMarker))
     {
      WriteStartupRow("REFUSED","server marker mismatch");
      return INIT_FAILED;
     }
   if(!AccountLoginWhitelisted())
     {
      WriteStartupRow("REFUSED","account login not whitelisted");
      return INIT_FAILED;
     }
   if((bool)MQLInfoInteger(MQL_TRADE_ALLOWED))
     {
      WriteStartupRow("REFUSED","EA-level trading permission must remain disabled");
      return INIT_FAILED;
     }
   if(!EnsureDailyLedgers(DateToken(TimeGMT())))
     {
      WriteStartupRow("REFUSED","one or more telemetry ledgers could not be opened");
      return INIT_FAILED;
     }

   if(InpCollectMarketDepth)
     {
      ResetLastError();
      g_book_subscribed=MarketBookAdd(_Symbol);
      if(!g_book_subscribed)
         g_book_subscription_error=GetLastError();
     }

   int seconds=InpHeartbeatSeconds;
   if(seconds < 1)
      seconds=1;
   EventSetTimer(seconds);
   WriteStartupRow("ACTIVE",g_book_subscribed ? "passive collection active with depth subscription" : "passive collection active; depth unavailable");
   WriteHeartbeatRow();
   CaptureBookSnapshot("INIT");
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   EventKillTimer();
   if(g_book_subscribed)
      MarketBookRelease(_Symbol);
   WriteStartupRow("STOPPED","deinit reason=" + StringFormat("%d",reason));
   CloseDailyLedgers();
  }

void OnTick()
  {
   WriteTickRow();
  }

void OnTimer()
  {
   WriteHeartbeatRow();
   if(g_book_rows == 0)
      CaptureBookSnapshot("TIMER_FALLBACK");
  }

void OnBookEvent(const string &symbol)
  {
   if(symbol != _Symbol)
      return;
   CaptureBookSnapshot("BOOK_EVENT");
  }

void OnTradeTransaction(
   const MqlTradeTransaction &trans,
   const MqlTradeRequest &request,
   const MqlTradeResult &result
)
  {
   datetime observed_at=TimeGMT();
   if(!InpCollectTradeTransactions
      || !EnsureDailyLedgers(DateToken(observed_at)))
      return;
   FileWrite(g_transaction_handle,
      "xau_prospective_transaction_v1",UtcTimestamp(observed_at),InpRunId,LoginText(),
      AccountInfoString(ACCOUNT_SERVER),EnumToString(trans.type),
      StringFormat("%I64u",trans.order),StringFormat("%I64u",trans.deal),
      StringFormat("%I64u",trans.position),StringFormat("%I64u",trans.position_by),
      trans.symbol,EnumToString(trans.order_type),EnumToString(trans.order_state),
      EnumToString(trans.deal_type),DoubleToString(trans.volume,4),
      DoubleToString(trans.price,_Digits),DoubleToString(trans.price_trigger,_Digits),
      DoubleToString(trans.price_sl,_Digits),DoubleToString(trans.price_tp,_Digits),
      EnumToString(request.action),StringFormat("%I64u",request.magic),
      StringFormat("%I64u",request.order),request.symbol,DoubleToString(request.volume,4),
      DoubleToString(request.price,_Digits),DoubleToString(request.sl,_Digits),
      DoubleToString(request.tp,_Digits),StringFormat("%I64u",request.deviation),
      EnumToString(request.type),EnumToString(request.type_filling),EnumToString(request.type_time),
      TimeToString(request.expiration,TIME_DATE | TIME_SECONDS),request.comment,
      StringFormat("%u",result.retcode),StringFormat("%I64u",result.deal),
      StringFormat("%I64u",result.order),DoubleToString(result.volume,4),
      DoubleToString(result.price,_Digits),DoubleToString(result.bid,_Digits),
      DoubleToString(result.ask,_Digits),result.comment,StringFormat("%u",result.request_id),
      StringFormat("%d",result.retcode_external),BoolText(InpDryRunOnly),
      BoolText(TRADE_PERMISSION),BoolText(BROKER_ACTION_ALLOWED),
      BoolText(PYTHON_EXECUTION_AUTHORIZED)
   );
   g_transaction_rows++;
   FileFlush(g_transaction_handle);
  }

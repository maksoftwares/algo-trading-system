#property copyright "ZHAO ZHU INFORMATION"
#property version   "1.00"
#property strict
#property description "US500 V41 causal minimal-core coordinator; order-capable, fail-closed, disarmed by default"

input bool   InpEnableOrders = false;
input bool   InpBrokerActionAllowed = false;
input string InpAuthorizationToken = "NO_ORDER_AUTHORITY";
input string InpConfigSha256 = "48e8b4f9545b8d37ca131abc3126eacf42609ae1fd7318e2a605c7fbe520b16e";
input long   InpAllowedAccountLogin = 1033030;
input string InpExpectedServer = "Capital.ComMena-Demo";
input string InpExpectedSymbol = "US500";
input string InpUS100Symbol = "US100";
input string InpUS30Symbol = "US30";
input double InpInitialStopRiskUsd = 20.0;
input double InpIntradayRetryRiskScale = 0.2;
input int    InpMaxSpreadPoints = 15;
input int    InpMaxDeviationPoints = 10;
input int    InpMaxOrdersPerNyDay = 3;
input double InpDailyLossLimitR = 3.0;
input double InpMaxMarginFraction = 1.00;
input int    InpServerUtcOffsetMinutes = 0;
input int    InpHistoryBars = 90000;
input int    InpHeartbeatSeconds = 60;
input int    InpMutexStaleSeconds = 180;
input bool   InpEnforceProspectiveBoundary = true;
input string InpEmergencyStopFile = "SHARED_1033030_US500_V41_EMERGENCY_STOP.txt";
input string InpAuditLogFile = "SHARED_1033030_US500_V41_AUDIT.csv";
input string InpInstanceId = "SHARED_V41";
input bool   InpResetPersistentState = false;
input string InpPersistentResetToken = "NO_RESET";
input bool   InpTesterBypassBinding = false;
input bool   InpTesterBypassBoundary = false;
input string InpTesterTraceFile = "";

const string CONTRACT_ID = "SHARED_1033030_US500_V41_CAUSAL_CORE_20260804";
const string CONFIG_SHA256 = "48e8b4f9545b8d37ca131abc3126eacf42609ae1fd7318e2a605c7fbe520b16e";
const string ORDER_AUTH_TOKEN = "AUTHORIZE_SHARED_1033030_US500_V41_DEMO_V1";
const string RESET_TOKEN = "RESET_US500_V41_PERSISTENT_STATE";
const string EXPECTED_SERVER = "Capital.ComMena-Demo";
const string EXPECTED_SYMBOL = "US500";
const string OPERATIONAL_HEALTH_LOG = "SHARED_1033030_US500_V41_HEALTH.csv";
const long EXPECTED_ACCOUNT_LOGIN = 1033030;
const ulong MAGIC_V6 = 65005041;
const ulong MAGIC_V19 = 65005042;
const double STOP_ATR = 3.0;
const double TARGET_ATR = 5.0;
const int LOSS_STREAK_TRIGGER = 3;
const double LOSS_STREAK_SCALE = 0.4;
const datetime RESEARCH_HISTORY_START_UTC = D'2025.06.06 12:05';
const int RESEARCH_HISTORY_START_DATE_KEY = 20250606;
const datetime PROSPECTIVE_BOUNDARY_UTC = D'2026.08.04 00:00';
#define WINDOW_COUNT 3
const int WINDOW_ENTRY_MINUTES[3] = {600,660,840};
const int WINDOW_DECISION_MINUTES[3] = {595,655,835};

struct RouteState
{
   bool eligible;
   bool shock;
   string regime;
   string band;
   string setup;
   double atr;
   double open_range_atr;
   double open_location;
   double atr_ratio_20;
   double atr_limit;
   double range_limit;
   int macro_sign;
   int date_key;
};

struct SignalState
{
   bool selected;
   string component;
   string action_id;
   int direction;
   int exit_minute;
   ulong magic;
};

string g_prefix="";
string g_mutex_owner="";
string g_mutex_heartbeat="";
double g_mutex_token=0.0;
bool g_mutex_owned=false;
int g_lock_handle=INVALID_HANDLE;
bool g_integrity_failed=false;
bool g_timer_set=false;
ulong g_audit_sequence=0;
ulong g_health_sequence=0;
int g_last_mutex_refresh=0;

int NthSundayDay(const int year,const int month,const int occurrence)
{
   MqlDateTime first={};
   first.year=year; first.mon=month; first.day=1;
   datetime value=StructToTime(first);
   TimeToStruct(value,first);
   return 1+((7-first.day_of_week)%7)+7*(occurrence-1);
}

datetime MakeHour(const int year,const int month,const int day,const int hour)
{
   MqlDateTime value={};
   value.year=year; value.mon=month; value.day=day; value.hour=hour;
   return StructToTime(value);
}

bool IsNewYorkDstUtc(const datetime utc)
{
   MqlDateTime value={};
   TimeToStruct(utc,value);
   datetime start=MakeHour(value.year,3,NthSundayDay(value.year,3,2),7);
   datetime finish=MakeHour(value.year,11,NthSundayDay(value.year,11,1),6);
   return utc>=start && utc<finish;
}

datetime ServerToUtc(const datetime server_time)
{
   return server_time-InpServerUtcOffsetMinutes*60;
}

datetime RuntimeUtcNow()
{
   return MQLInfoInteger(MQL_TESTER) ? ServerToUtc(TimeCurrent()) : TimeGMT();
}

void ServerTimeToNewYork(const datetime server_time,MqlDateTime &ny)
{
   datetime utc=ServerToUtc(server_time);
   int offset=IsNewYorkDstUtc(utc) ? -4 : -5;
   TimeToStruct(utc+offset*3600,ny);
}

int DateKey(const MqlDateTime &value)
{
   return value.year*10000+value.mon*100+value.day;
}

int NewYorkMinute(const datetime server_time,int &date_key,int &weekday)
{
   MqlDateTime ny={};
   ServerTimeToNewYork(server_time,ny);
   date_key=DateKey(ny);
   weekday=ny.day_of_week;
   return ny.hour*60+ny.min;
}

string StateName(const string suffix)
{
   return g_prefix+"_"+suffix;
}

bool SetState(const string suffix,const double value)
{
   if(GlobalVariableSet(StateName(suffix),value)==0)
      return false;
   GlobalVariablesFlush();
   return true;
}

bool DeleteState(const string suffix)
{
   string name=StateName(suffix);
   if(!GlobalVariableCheck(name))
      return true;
   bool ok=GlobalVariableDel(name);
   GlobalVariablesFlush();
   return ok;
}

bool ResetPersistentState()
{
   string names[9]={"LAST_600","LAST_660","LAST_840","STREAK_V6","STREAK_V19",
      "LAST_DEAL","ORDERS_DATE","ORDERS_COUNT","INTEGRITY"};
   for(int i=0;i<ArraySize(names);++i)
      if(!DeleteState(names[i]))
         return false;
   return true;
}

void RollbackMutexAcquire()
{
   if(g_lock_handle!=INVALID_HANDLE)
   {
      FileClose(g_lock_handle);
      g_lock_handle=INVALID_HANDLE;
   }
   if(GlobalVariableCheck(g_mutex_owner)
      && MathAbs(GlobalVariableGet(g_mutex_owner)-g_mutex_token)<=1e-8)
      GlobalVariableDel(g_mutex_owner);
   double heartbeat=MathFloor(g_mutex_token);
   if(GlobalVariableCheck(g_mutex_heartbeat))
      GlobalVariableSetOnCondition(g_mutex_heartbeat,0.0,heartbeat);
   GlobalVariablesFlush();
   g_mutex_token=0.0;
   g_mutex_owned=false;
}

bool AcquireMutex()
{
   double now=(double)TimeLocal();
   if(!GlobalVariableCheck(g_mutex_heartbeat)
      && GlobalVariableSet(g_mutex_heartbeat,0.0)==0)
   {
      PrintFormat("V41_INIT_FAIL|MUTEX_HEARTBEAT_CREATE|error=%d",GetLastError());
      return false;
   }
   double observed=GlobalVariableGet(g_mutex_heartbeat);
   if(observed>0.0 && now-observed<(double)InpMutexStaleSeconds)
   {
      PrintFormat("V41_INIT_FAIL|MUTEX_BUSY|age=%.0f",now-observed);
      return false;
   }
   if(!GlobalVariableSetOnCondition(g_mutex_heartbeat,now,observed))
   {
      PrintFormat("V41_INIT_FAIL|MUTEX_HEARTBEAT_CAS|error=%d",GetLastError());
      return false;
   }
   g_mutex_token=now+(double)(ChartID()%1000000)/1000000.0;
   if(GlobalVariableSet(g_mutex_owner,g_mutex_token)==0)
   {
      PrintFormat("V41_INIT_FAIL|MUTEX_OWNER_CREATE|error=%d",GetLastError());
      RollbackMutexAcquire();
      return false;
   }
   string lock_name="US500_V41_"+InpInstanceId+".lifecycle.lock";
   g_lock_handle=FileOpen(lock_name,FILE_READ|FILE_WRITE|FILE_BIN|FILE_ANSI|FILE_COMMON);
   if(g_lock_handle==INVALID_HANDLE)
   {
      PrintFormat("V41_INIT_FAIL|MUTEX_FILE_OPEN|error=%d|file=%s",GetLastError(),lock_name);
      RollbackMutexAcquire();
      return false;
   }
   string payload=StringFormat("%s|%s|%I64d|%I64d",CONTRACT_ID,CONFIG_SHA256,
      AccountInfoInteger(ACCOUNT_LOGIN),(long)TimeLocal());
   if(FileWriteString(g_lock_handle,payload)==0)
   {
      PrintFormat("V41_INIT_FAIL|MUTEX_FILE_WRITE|error=%d|file=%s",GetLastError(),lock_name);
      RollbackMutexAcquire();
      return false;
   }
   FileFlush(g_lock_handle);
   GlobalVariablesFlush();
   g_mutex_owned=true;
   return true;
}

bool RefreshMutex()
{
   if(!g_mutex_owned || g_lock_handle==INVALID_HANDLE
      || !GlobalVariableCheck(g_mutex_owner)
      || MathAbs(GlobalVariableGet(g_mutex_owner)-g_mutex_token)>1e-8)
      return false;
   if(GlobalVariableSet(g_mutex_heartbeat,(double)TimeLocal())==0)
      return false;
   FileSeek(g_lock_handle,0,SEEK_SET);
   if(FileWriteString(g_lock_handle,StringFormat("%s|%I64d",CONFIG_SHA256,(long)TimeLocal()))==0)
      return false;
   FileFlush(g_lock_handle);
   g_last_mutex_refresh=(int)TimeLocal();
   return true;
}

void ReleaseMutex()
{
   if(g_lock_handle!=INVALID_HANDLE)
   {
      FileClose(g_lock_handle);
      g_lock_handle=INVALID_HANDLE;
   }
   if(g_mutex_owned && GlobalVariableCheck(g_mutex_owner)
      && MathAbs(GlobalVariableGet(g_mutex_owner)-g_mutex_token)<=1e-8)
   {
      GlobalVariableDel(g_mutex_owner);
      GlobalVariableDel(g_mutex_heartbeat);
      GlobalVariablesFlush();
   }
   g_mutex_owned=false;
}

bool EmergencyStopPresent()
{
   return FileIsExist(InpEmergencyStopFile,FILE_COMMON);
}

bool IsOwnMagic(const ulong magic)
{
   return magic==MAGIC_V6 || magic==MAGIC_V19;
}

bool HasAnySymbolExposure()
{
   for(int i=PositionsTotal()-1;i>=0;--i)
   {
      ulong ticket=PositionGetTicket(i);
      if(ticket!=0 && PositionSelectByTicket(ticket)
         && PositionGetString(POSITION_SYMBOL)==_Symbol)
         return true;
   }
   for(int i=OrdersTotal()-1;i>=0;--i)
   {
      ulong ticket=OrderGetTicket(i);
      if(ticket!=0 && OrderSelect(ticket)
         && OrderGetString(ORDER_SYMBOL)==_Symbol)
         return true;
   }
   return false;
}

int CountOwnPositions()
{
   int count=0;
   for(int i=PositionsTotal()-1;i>=0;--i)
   {
      ulong ticket=PositionGetTicket(i);
      if(ticket!=0 && PositionSelectByTicket(ticket)
         && PositionGetString(POSITION_SYMBOL)==_Symbol
         && IsOwnMagic((ulong)PositionGetInteger(POSITION_MAGIC)))
         ++count;
   }
   return count;
}

bool Audit(const string event_name,const string detail,const int date_key,
           const int ny_minute,const string component,const string action_id,
           const RouteState &route,const SignalState &signal,const double volume,
           const double price,const double sl,const double tp,const ulong ticket,
           const double effective_risk_scale=-1.0)
{
   int handle=FileOpen(InpAuditLogFile,
      FILE_READ|FILE_WRITE|FILE_CSV|FILE_COMMON|FILE_SHARE_READ,',');
   if(handle==INVALID_HANDLE)
   {
      PrintFormat("V41 audit open failed err=%d",GetLastError());
      g_integrity_failed=true;
      return false;
   }
   bool ok=true;
   if(FileSize(handle)<=2)
   {
      if(FileWrite(handle,"server_time","utc_time","event","detail","contract_id",
         "config_sha256","instance_id","account","server","symbol","date_key",
         "ny_minute","component","action_id","eligible","shock","regime","band",
         "setup","atr","open_range_atr","open_location","atr_ratio_20","atr_limit",
         "range_limit","macro_sign","selected","direction","exit_minute","risk_scale",
         "volume","price","sl","tp","ticket","orders_enabled","broker_allowed",
         "symbol_exposure","own_positions","event_id")==0)
         ok=false;
   }
   if(ok && !FileSeek(handle,0,SEEK_END))
      ok=false;
   ++g_audit_sequence;
   string event_id=StringFormat("V41-%I64d-%I64u-%I64u",(long)RuntimeUtcNow(),
      GetTickCount64(),g_audit_sequence);
   double risk_scale=effective_risk_scale>=0.0 ? effective_risk_scale : 1.0;
   if(effective_risk_scale<0.0 && component!="")
   {
      int streak=(int)(GlobalVariableCheck(StateName(component=="V6_PROTECTED" ? "STREAK_V6" : "STREAK_V19"))
         ? GlobalVariableGet(StateName(component=="V6_PROTECTED" ? "STREAK_V6" : "STREAK_V19")) : 0.0);
      if(streak>=LOSS_STREAK_TRIGGER)
         risk_scale=LOSS_STREAK_SCALE;
   }
   uint bytes=0;
   if(ok)
      bytes=FileWrite(handle,TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS),
         TimeToString(RuntimeUtcNow(),TIME_DATE|TIME_SECONDS),event_name,detail,CONTRACT_ID,
         CONFIG_SHA256,InpInstanceId,AccountInfoInteger(ACCOUNT_LOGIN),
         AccountInfoString(ACCOUNT_SERVER),_Symbol,date_key,ny_minute,component,action_id,
         route.eligible?1:0,route.shock?1:0,route.regime,route.band,route.setup,
         DoubleToString(route.atr,8),DoubleToString(route.open_range_atr,8),
         DoubleToString(route.open_location,8),DoubleToString(route.atr_ratio_20,8),
         DoubleToString(route.atr_limit,8),DoubleToString(route.range_limit,8),
         route.macro_sign,signal.selected?1:0,signal.direction,signal.exit_minute,
         DoubleToString(risk_scale,2),DoubleToString(volume,4),DoubleToString(price,_Digits),
         DoubleToString(sl,_Digits),DoubleToString(tp,_Digits),ticket,
         InpEnableOrders?1:0,InpBrokerActionAllowed?1:0,HasAnySymbolExposure()?1:0,
         CountOwnPositions(),event_id);
   FileFlush(handle);
   FileClose(handle);
   if(!ok || bytes==0)
   {
      g_integrity_failed=true;
      return false;
   }
   return true;
}

// Best-effort operational telemetry only.  This function is deliberately
// non-blocking with respect to trading state: a telemetry I/O failure is
// printed, but never changes integrity, authorization, or order decisions.
void OperationalHealth(const string event_name,const double order_check_ms=-1.0,
                       const double order_send_ms=-1.0,
                       const double requested_price=0.0,
                       const double fill_price=0.0,const uint retcode=0)
{
   datetime utc_now=RuntimeUtcNow();
   MqlTick tick={};
   bool have_tick=SymbolInfoTick(_Symbol,tick) && tick.time_msc>0;
   long tick_age_ms=-1;
   if(have_tick)
   {
      long raw_tick_age_ms=(long)utc_now*1000-tick.time_msc;
      tick_age_ms=raw_tick_age_ms>0 ? raw_tick_age_ms : 0;
   }
   long server_lag_seconds=(long)utc_now-(long)ServerToUtc(TimeCurrent());
   long ping_us=TerminalInfoInteger(TERMINAL_PING_LAST);
   double ping_ms=ping_us>=0 ? (double)ping_us/1000.0 : -1.0;
   int handle=FileOpen(OPERATIONAL_HEALTH_LOG,
      FILE_READ|FILE_WRITE|FILE_CSV|FILE_COMMON|FILE_SHARE_READ,',');
   if(handle==INVALID_HANDLE)
   {
      PrintFormat("V41 health telemetry open failed err=%d",GetLastError());
      return;
   }
   bool ok=true;
   if(FileSize(handle)<=2)
   {
      if(FileWrite(handle,"utc_time","server_time","event","contract_id",
         "config_sha256","instance_id","account","server","symbol","connected",
         "terminal_trade_allowed","mql_trade_allowed","account_trade_allowed",
         "ping_ms","tick_time_msc","tick_age_ms","server_lag_seconds",
         "order_check_ms","order_send_ms","requested_price","fill_price",
         "retcode","event_id")==0)
         ok=false;
   }
   if(ok && !FileSeek(handle,0,SEEK_END))
      ok=false;
   ++g_health_sequence;
   string event_id=StringFormat("V41H-%I64d-%I64u-%I64u",(long)utc_now,
      GetTickCount64(),g_health_sequence);
   uint bytes=0;
   if(ok)
      bytes=FileWrite(handle,TimeToString(utc_now,TIME_DATE|TIME_SECONDS),
         TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS),event_name,CONTRACT_ID,
         CONFIG_SHA256,InpInstanceId,AccountInfoInteger(ACCOUNT_LOGIN),
         AccountInfoString(ACCOUNT_SERVER),_Symbol,
         TerminalInfoInteger(TERMINAL_CONNECTED),
         TerminalInfoInteger(TERMINAL_TRADE_ALLOWED),MQLInfoInteger(MQL_TRADE_ALLOWED),
         AccountInfoInteger(ACCOUNT_TRADE_ALLOWED),DoubleToString(ping_ms,3),
         have_tick ? tick.time_msc : (long)0,tick_age_ms,server_lag_seconds,
         DoubleToString(order_check_ms,3),DoubleToString(order_send_ms,3),
         DoubleToString(requested_price,_Digits),DoubleToString(fill_price,_Digits),
         retcode,event_id);
   FileFlush(handle);
   FileClose(handle);
   if(!ok || bytes==0)
      PrintFormat("V41 health telemetry write failed err=%d event=%s",GetLastError(),event_name);
}

bool TesterTrace(const string event_name,const int date_key,const int minute,
                 const SignalState &signal,const RouteState &route)
{
   if(InpTesterTraceFile=="")
      return true;
   if(!MQLInfoInteger(MQL_TESTER))
      return false;
   int handle=FileOpen(InpTesterTraceFile,
      FILE_READ|FILE_WRITE|FILE_CSV|FILE_COMMON|FILE_SHARE_READ,',');
   if(handle==INVALID_HANDLE)
      return false;
   double us500_open=0.0,us500_close=0.0,us100_open=0.0,us100_close=0.0;
   double us30_open=0.0,us30_close=0.0;
   OpeningPrices(_Symbol,date_key,us500_open,us500_close);
   OpeningPrices(InpUS100Symbol,date_key,us100_open,us100_close);
   OpeningPrices(InpUS30Symbol,date_key,us30_open,us30_close);
   if(FileSize(handle)<=2)
      FileWrite(handle,"event","date_key","entry_minute","component","action_id",
         "direction","exit_minute","atr","regime","band","setup","macro_sign",
         "eligible","shock","us500_open","us500_close","us100_open","us100_close",
         "us30_open","us30_close");
   FileSeek(handle,0,SEEK_END);
   uint bytes=FileWrite(handle,event_name,date_key,minute,signal.component,signal.action_id,
      signal.direction,signal.exit_minute,DoubleToString(route.atr,10),route.regime,
      route.band,route.setup,route.macro_sign,route.eligible?1:0,route.shock?1:0,
      DoubleToString(us500_open,10),DoubleToString(us500_close,10),
      DoubleToString(us100_open,10),DoubleToString(us100_close,10),
      DoubleToString(us30_open,10),DoubleToString(us30_close,10));
   FileFlush(handle);
   FileClose(handle);
   return bytes>0;
}

double RollingBidAtr(const MqlRates &rates[],const int index)
{
   double total=0.0;
   int count=0;
   int first=MathMax(1,index-155);
   for(int i=first;i<=index;++i)
   {
      if(ServerToUtc(rates[i].time)<RESEARCH_HISTORY_START_UTC)
         continue;
      double previous=rates[i-1].close;
      double range=rates[i].high-rates[i].low;
      total+=MathMax(range,MathMax(MathAbs(rates[i].high-previous),
         MathAbs(rates[i].low-previous)));
      ++count;
   }
   return count>=78 ? total/(double)count : 0.0;
}

int FindRate(const MqlRates &rates[],const int before_or_at,const int wanted_key,
             const int wanted_minute)
{
   for(int i=before_or_at;i>=0;--i)
   {
      int key=0,weekday=0;
      int minute=NewYorkMinute(rates[i].time,key,weekday);
      if(key==wanted_key && minute==wanted_minute)
         return i;
      if(key<wanted_key)
         break;
   }
   return -1;
}

bool HasCompleteResearchCashGrid(const MqlRates &rates[],const int close_index,
                                 const int date_key)
{
   for(int minute=565;minute<=955;minute+=5)
      if(FindRate(rates,close_index,date_key,minute)<0)
         return false;
   return true;
}

double MedianSlice(const double &values[],const int start,const int count)
{
   double copy[];
   ArrayResize(copy,count);
   for(int i=0;i<count;++i)
      copy[i]=values[start+i];
   ArraySort(copy);
   if((count%2)==1)
      return copy[count/2];
   return (copy[count/2-1]+copy[count/2])/2.0;
}

double LinearQuantile(const double &values[],const int count,const double q)
{
   double copy[];
   ArrayResize(copy,count);
   for(int i=0;i<count;++i)
      copy[i]=values[i];
   ArraySort(copy);
   double position=(count-1)*q;
   int lower=(int)MathFloor(position);
   int upper=(int)MathCeil(position);
   if(lower==upper)
      return copy[lower];
   return copy[lower]+(position-lower)*(copy[upper]-copy[lower]);
}

bool OpeningRange(const MqlRates &rates[],const int close_index,const int date_key,
                  const int decision_minute,double &high,double &low)
{
   int open_index=FindRate(rates,close_index,date_key,570);
   if(open_index<0)
      return false;
   high=-DBL_MAX; low=DBL_MAX;
   for(int i=open_index;i<=close_index;++i)
   {
      int key=0,weekday=0;
      int minute=NewYorkMinute(rates[i].time,key,weekday);
      if(key==date_key && minute>=570 && minute<=decision_minute)
      {
         high=MathMax(high,rates[i].high);
         low=MathMin(low,rates[i].low);
      }
   }
   return high>low && low>0.0;
}

bool BuildRoute(const int decision_minute,RouteState &route)
{
   route.eligible=false; route.shock=false; route.regime="WARMUP";
   route.band="WARMUP"; route.setup="WARMUP"; route.atr=0.0;
   route.open_range_atr=0.0; route.open_location=0.0;
   route.atr_ratio_20=0.0; route.atr_limit=0.0; route.range_limit=0.0;
   route.macro_sign=0; route.date_key=0;
   MqlRates rates[];
   ArraySetAsSeries(rates,false);
   int copied=CopyRates(_Symbol,PERIOD_M5,0,InpHistoryBars,rates);
   if(copied<20000)
      return false;
   MqlDateTime now_ny={};
   ServerTimeToNewYork(TimeCurrent(),now_ny);
   int today=DateKey(now_ny);
   if(today<RESEARCH_HISTORY_START_DATE_KEY)
      return false;
   route.date_key=today;
   int decision=-1;
   for(int i=copied-1;i>=0;--i)
   {
      int key=0,weekday=0;
      int minute=NewYorkMinute(rates[i].time,key,weekday);
      if(key==today && minute==decision_minute)
      {
         decision=i;
         break;
      }
      if(key<today)
         break;
   }
   if(decision<0)
      return false;
   double current_atr=RollingBidAtr(rates,decision);
   double current_high=0.0,current_low=0.0;
   if(current_atr<=0.0 || !OpeningRange(rates,decision,today,decision_minute,
      current_high,current_low))
      return false;

   double closes[170],opens[170],atrs[170],ranges[170];
   int sessions=0,last_key=0;
   for(int i=decision-1;i>=0 && sessions<170;--i)
   {
      int key=0,weekday=0;
      int minute=NewYorkMinute(rates[i].time,key,weekday);
      if(key<RESEARCH_HISTORY_START_DATE_KEY)
         break;
      if(key>=today || key==last_key || minute!=955)
         continue;
      if(!HasCompleteResearchCashGrid(rates,i,key))
         continue;
      int open_index=FindRate(rates,i,key,570);
      int past_decision=FindRate(rates,i,key,decision_minute);
      if(open_index<0 || past_decision<0)
         continue;
      double past_atr=RollingBidAtr(rates,past_decision);
      double past_high=0.0,past_low=0.0;
      if(past_atr<=0.0 || !OpeningRange(rates,past_decision,key,decision_minute,
         past_high,past_low))
         continue;
      closes[sessions]=rates[i].close;
      opens[sessions]=rates[open_index].open;
      atrs[sessions]=past_atr;
      ranges[sessions]=(past_high-past_low)/past_atr;
      last_key=key;
      ++sessions;
   }
   if(sessions<70)
      return false;
   double prior_cash=(closes[0]-opens[0])/atrs[0];
   double mean20=0.0,mean50=0.0;
   for(int i=0;i<50;++i)
   {
      mean50+=closes[i];
      if(i<20)
         mean20+=closes[i];
   }
   mean20/=20.0; mean50/=50.0;
   double ma20=(closes[0]-mean20)/current_atr;
   double ma50=(closes[0]-mean50)/current_atr;
   double current_ratio=current_atr/MedianSlice(atrs,0,20);
   int ratio_count=MathMin(126,sessions-20);
   int range_count=MathMin(126,sessions);
   if(ratio_count<50 || range_count<50 || !MathIsValidNumber(prior_cash))
      return false;
   double ratios[];
   ArrayResize(ratios,ratio_count);
   for(int j=0;j<ratio_count;++j)
      ratios[j]=atrs[j]/MedianSlice(atrs,j+1,20);
   double range_history[];
   ArrayResize(range_history,range_count);
   for(int j=0;j<range_count;++j)
      range_history[j]=ranges[j];
   double width=MathMax(current_high-current_low,1e-9);
   route.atr=current_atr;
   route.open_range_atr=width/current_atr;
   route.open_location=(rates[decision].close-current_low)/width;
   route.atr_ratio_20=current_ratio;
   route.atr_limit=LinearQuantile(ratios,ratio_count,0.90);
   route.range_limit=LinearQuantile(range_history,range_count,0.95);
   route.shock=current_ratio>route.atr_limit || route.open_range_atr>route.range_limit;
   if(route.shock)
      route.regime="SHOCK";
   else if(ma20>0.0 && ma50>0.0)
      route.regime="BULL";
   else if(ma20<0.0 && ma50<0.0)
      route.regime="BEAR";
   else
      route.regime="NEUTRAL";
   if(route.open_location<0.35)
      route.band="LOW";
   else if(route.open_location>0.65)
      route.band="HIGH";
   else
      route.band="MID";
   route.setup=route.shock ? "SHOCK" : route.regime+"_"+route.band;
   if(sessions>=100)
   {
      double mean100=0.0;
      for(int i=0;i<100;++i)
         mean100+=closes[i];
      mean100/=100.0;
      route.macro_sign=closes[0]>mean100 ? 1 : (closes[0]<mean100 ? -1 : 0);
   }
   route.eligible=true;
   return true;
}

bool OpeningPrices(const string symbol,const int date_key,double &opening,double &closing)
{
   opening=0.0;
   closing=0.0;
   MqlRates rates[];
   ArraySetAsSeries(rates,false);
   int copied=CopyRates(symbol,PERIOD_M5,0,1000,rates);
   if(copied<=0)
      return false;
   int close_index=-1;
   for(int i=copied-1;i>=0;--i)
   {
      int key=0,weekday=0;
      int minute=NewYorkMinute(rates[i].time,key,weekday);
      if(key==date_key && minute==595)
      {
         close_index=i;
         break;
      }
      if(key<date_key)
         break;
   }
   if(close_index<0)
      return false;
   int open_index=FindRate(rates,close_index,date_key,570);
   if(open_index<0 || rates[open_index].open<=0.0)
      return false;
   opening=rates[open_index].open;
   closing=rates[close_index].close;
   return closing>0.0;
}

int OpeningSign(const string symbol,const int date_key)
{
   double opening=0.0,closing=0.0;
   if(!OpeningPrices(symbol,date_key,opening,closing))
      return 0;
   double change=closing/opening-1.0;
   return change>0.0 ? 1 : (change<0.0 ? -1 : 0);
}

SignalState EmptySignal()
{
   SignalState signal;
   signal.selected=false; signal.component=""; signal.action_id="";
   signal.direction=0; signal.exit_minute=0; signal.magic=0;
   return signal;
}

SignalState V6Signal(const int window_index,const RouteState &route)
{
   SignalState signal=EmptySignal();
   if(!route.eligible || route.shock)
      return signal;
   string setup=route.setup;
   if(window_index==0)
   {
      if(setup=="BEAR_HIGH")
      { signal.direction=-1; signal.exit_minute=840; signal.action_id="W1000_SHORT_840_S3T5"; }
      else if(setup=="NEUTRAL_HIGH")
      { signal.direction=1; signal.exit_minute=720; signal.action_id="W1000_LONG_720_S3T5"; }
      else if(setup=="NEUTRAL_LOW")
      { signal.direction=1; signal.exit_minute=840; signal.action_id="W1000_LONG_840_S3T5"; }
      if(signal.direction!=0 && signal.direction!=route.macro_sign)
         return EmptySignal();
   }
   else if(window_index==1)
   {
      if(setup=="BEAR_HIGH")
      { signal.direction=1; signal.exit_minute=955; signal.action_id="W1100_LONG_955_S3T5"; }
      else if(setup=="NEUTRAL_HIGH")
      { signal.direction=1; signal.exit_minute=900; signal.action_id="W1100_LONG_900_S3T5"; }
      else if(setup=="NEUTRAL_LOW")
      { signal.direction=1; signal.exit_minute=955; signal.action_id="W1100_LONG_955_S3T5"; }
      else if(setup=="NEUTRAL_MID")
      { signal.direction=1; signal.exit_minute=955; signal.action_id="W1100_LONG_955_S3T5"; }
   }
   else if(window_index==2)
   {
      if(setup=="NEUTRAL_LOW")
      { signal.direction=-1; signal.exit_minute=955; signal.action_id="W1400_SHORT_955_S3T5"; }
      else if(setup=="NEUTRAL_MID")
      { signal.direction=1; signal.exit_minute=900; signal.action_id="W1400_LONG_900_S3T5"; }
      if(signal.direction!=0 && signal.direction!=route.macro_sign)
         return EmptySignal();
   }
   if(signal.direction!=0)
   {
      signal.selected=true;
      signal.component="V6_PROTECTED";
      signal.magic=MAGIC_V6;
   }
   return signal;
}

SignalState V19Signal(const RouteState &route)
{
   SignalState signal=EmptySignal();
   if(!route.eligible || route.shock)
      return signal;
   int us500=OpeningSign(_Symbol,route.date_key);
   int us100=OpeningSign(InpUS100Symbol,route.date_key);
   int us30=OpeningSign(InpUS30Symbol,route.date_key);
   if(us500==0 || us100==0 || us30==0 || us500+us100+us30<=0)
      return signal;
   signal.selected=true;
   signal.component="V19_OPENING_SHORT";
   signal.action_id="POSITIVE_OPENING_BREADTH_SHORT";
   signal.direction=-1;
   signal.exit_minute=840;
   signal.magic=MAGIC_V19;
   return signal;
}

string LatchSuffix(const int entry_minute)
{
   return "LAST_"+IntegerToString(entry_minute);
}

bool IsLatched(const int entry_minute,const int date_key)
{
   string name=StateName(LatchSuffix(entry_minute));
   return GlobalVariableCheck(name) && (int)GlobalVariableGet(name)==date_key;
}

bool Latch(const int entry_minute,const int date_key)
{
   return SetState(LatchSuffix(entry_minute),(double)date_key);
}

int LossStreak(const string component)
{
   string suffix=component=="V6_PROTECTED" ? "STREAK_V6" : "STREAK_V19";
   return GlobalVariableCheck(StateName(suffix)) ? (int)GlobalVariableGet(StateName(suffix)) : 0;
}

double RiskScale(const string component)
{
   return LossStreak(component)>=LOSS_STREAK_TRIGGER ? LOSS_STREAK_SCALE : 1.0;
}

int VolumeDigits(const double step)
{
   if(step>=1.0) return 0;
   if(step>=0.1) return 1;
   if(step>=0.01) return 2;
   if(step>=0.001) return 3;
   return 4;
}

double NormalizeVolumeDown(const double requested)
{
   double minimum=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double maximum=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX);
   double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   if(minimum<=0.0 || maximum<=0.0 || step<=0.0 || requested<minimum)
      return 0.0;
   double bounded=MathMin(requested,maximum);
   double volume=MathFloor((bounded+1e-12)/step)*step;
   if(volume<minimum)
      return 0.0;
   return NormalizeDouble(volume,VolumeDigits(step));
}

bool UsdToAccountRate(double &rate)
{
   if(SymbolInfoString(_Symbol,SYMBOL_CURRENCY_PROFIT)!="USD")
      return false;
   MqlTick tick={};
   if(!SymbolInfoTick(_Symbol,tick) || tick.ask<=0.0)
      return false;
   double pnl=0.0;
   if(!OrderCalcProfit(ORDER_TYPE_BUY,_Symbol,1.0,tick.ask,tick.ask+1.0,pnl))
      return false;
   rate=MathAbs(pnl);
   return rate>0.0 && MathIsValidNumber(rate);
}

double RiskSizedVolume(const int direction,const double entry,const double stop,
                       const double risk_scale)
{
   double usd_rate=0.0;
   if(!UsdToAccountRate(usd_rate))
      return 0.0;
   double loss_one_lot=0.0;
   ENUM_ORDER_TYPE type=direction>0 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   if(!OrderCalcProfit(type,_Symbol,1.0,entry,stop,loss_one_lot))
      return 0.0;
   loss_one_lot=MathAbs(loss_one_lot);
   if(loss_one_lot<=0.0)
      return 0.0;
   double desired_account_risk=InpInitialStopRiskUsd*usd_rate*risk_scale;
   return NormalizeVolumeDown(desired_account_risk/loss_one_lot);
}

ENUM_ORDER_TYPE_FILLING FillPolicy()
{
   int filling=(int)SymbolInfoInteger(_Symbol,SYMBOL_FILLING_MODE);
   if((filling&SYMBOL_FILLING_IOC)==SYMBOL_FILLING_IOC)
      return ORDER_FILLING_IOC;
   if((filling&SYMBOL_FILLING_FOK)==SYMBOL_FILLING_FOK)
      return ORDER_FILLING_FOK;
   return ORDER_FILLING_RETURN;
}

bool CountOwnEntryOrdersToday(const int date_key,int &count)
{
   count=0;
   if(!HistorySelect(TimeCurrent()-3*86400,TimeCurrent()))
      return false;
   ulong orders[];
   int deals=HistoryDealsTotal();
   for(int i=0;i<deals;++i)
   {
      ulong ticket=HistoryDealGetTicket(i);
      if(ticket==0
         || HistoryDealGetString(ticket,DEAL_SYMBOL)!=_Symbol
         || !IsOwnMagic((ulong)HistoryDealGetInteger(ticket,DEAL_MAGIC)))
         continue;
      ENUM_DEAL_ENTRY entry=(ENUM_DEAL_ENTRY)HistoryDealGetInteger(ticket,DEAL_ENTRY);
      if(entry!=DEAL_ENTRY_IN && entry!=DEAL_ENTRY_INOUT)
         continue;
      int deal_key=0,weekday=0;
      NewYorkMinute((datetime)HistoryDealGetInteger(ticket,DEAL_TIME),deal_key,weekday);
      if(deal_key!=date_key)
         continue;
      ulong order=(ulong)HistoryDealGetInteger(ticket,DEAL_ORDER);
      if(order==0)
         order=ticket;
      bool seen=false;
      for(int j=0;j<ArraySize(orders);++j)
         if(orders[j]==order)
         {
            seen=true;
            break;
         }
      if(seen)
         continue;
      int size=ArraySize(orders);
      if(ArrayResize(orders,size+1)!=size+1)
         return false;
      orders[size]=order;
   }
   count=ArraySize(orders);
   return true;
}

bool OrdersToday(const int date_key,int &count)
{
   string date_name=StateName("ORDERS_DATE");
   string count_name=StateName("ORDERS_COUNT");
   if(!GlobalVariableCheck(date_name) || (int)GlobalVariableGet(date_name)!=date_key)
   {
      if(!CountOwnEntryOrdersToday(date_key,count)
         || !SetState("ORDERS_DATE",(double)date_key)
         || !SetState("ORDERS_COUNT",(double)count))
         return false;
      return true;
   }
   if(!GlobalVariableCheck(count_name))
   {
      if(!CountOwnEntryOrdersToday(date_key,count)
         || !SetState("ORDERS_COUNT",(double)count))
         return false;
      return true;
   }
   count=(int)GlobalVariableGet(count_name);
   return true;
}

bool IncrementOrdersToday(const int date_key)
{
   int count=0;
   if(!OrdersToday(date_key,count))
      return false;
   return SetState("ORDERS_COUNT",(double)(count+1));
}

bool OwnRealizedToday(const int date_key,double &total,bool &loss_seen)
{
   total=0.0;
   loss_seen=false;
   if(!HistorySelect(TimeCurrent()-3*86400,TimeCurrent()))
      return false;
   int deals=HistoryDealsTotal();
   for(int i=0;i<deals;++i)
   {
      ulong ticket=HistoryDealGetTicket(i);
      if(ticket==0)
         continue;
      if(HistoryDealGetString(ticket,DEAL_SYMBOL)!=_Symbol
         || !IsOwnMagic((ulong)HistoryDealGetInteger(ticket,DEAL_MAGIC)))
         continue;
      ENUM_DEAL_ENTRY entry=(ENUM_DEAL_ENTRY)HistoryDealGetInteger(ticket,DEAL_ENTRY);
      if(entry!=DEAL_ENTRY_OUT && entry!=DEAL_ENTRY_OUT_BY && entry!=DEAL_ENTRY_INOUT)
         continue;
      int key=0,weekday=0;
      NewYorkMinute((datetime)HistoryDealGetInteger(ticket,DEAL_TIME),key,weekday);
      if(key==date_key)
      {
         double pnl=HistoryDealGetDouble(ticket,DEAL_PROFIT)
            +HistoryDealGetDouble(ticket,DEAL_COMMISSION)
            +HistoryDealGetDouble(ticket,DEAL_SWAP);
         total+=pnl;
         if(pnl<0.0)
            loss_seen=true;
      }
   }
   return true;
}

bool DailyLossLimitHit(const int date_key)
{
   double rate=0.0;
   if(!UsdToAccountRate(rate))
      return true;
   double realized=0.0;
   bool loss_seen=false;
   if(!OwnRealizedToday(date_key,realized,loss_seen))
      return true;
   return realized<=-InpDailyLossLimitR*InpInitialStopRiskUsd*rate;
}

bool AuthorizationValid()
{
   if(!InpEnableOrders)
      return true;
   return InpBrokerActionAllowed && InpAuthorizationToken==ORDER_AUTH_TOKEN;
}

bool OrderModeReady(const int date_key,string &reason)
{
   if(!InpEnableOrders) { reason="DISARMED"; return false; }
   if(!InpBrokerActionAllowed) { reason="BROKER_ACTION_NOT_ALLOWED"; return false; }
   if(InpAuthorizationToken!=ORDER_AUTH_TOKEN) { reason="INVALID_AUTH_TOKEN"; return false; }
   if(EmergencyStopPresent()) { reason="EMERGENCY_STOP"; return false; }
   if(!MQLInfoInteger(MQL_TESTER)
      && (ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)!=ACCOUNT_TRADE_MODE_DEMO)
   { reason="NOT_DEMO_ACCOUNT"; return false; }
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)
      || !MQLInfoInteger(MQL_TRADE_ALLOWED)
      || !AccountInfoInteger(ACCOUNT_TRADE_ALLOWED))
   { reason="TRADING_DISABLED"; return false; }
   if(HasAnySymbolExposure()) { reason="SYMBOL_EXPOSURE_EXISTS"; return false; }
   int orders_today=0;
   if(!OrdersToday(date_key,orders_today))
   {
      g_integrity_failed=true;
      reason="ORDERS_STATE_FAIL";
      return false;
   }
   if(orders_today>=InpMaxOrdersPerNyDay) { reason="ORDER_LIMIT"; return false; }
   if(DailyLossLimitHit(date_key)) { reason="DAILY_LOSS_LIMIT"; return false; }
   reason="PASS";
   return true;
}

bool SubmitEntry(const SignalState &signal,const RouteState &route,const int minute)
{
   string reason="";
   if(!OrderModeReady(route.date_key,reason))
   {
      Audit("ENTRY_BLOCK",reason,route.date_key,minute,signal.component,
         signal.action_id,route,signal,0.0,0.0,0.0,0.0,0);
      return false;
   }
   MqlTick tick={};
   if(!SymbolInfoTick(_Symbol,tick) || tick.ask<=0.0 || tick.bid<=0.0)
      return false;
   double spread=(tick.ask-tick.bid)/_Point;
   if(spread>(double)InpMaxSpreadPoints)
   {
      Audit("ENTRY_BLOCK","SPREAD_LIMIT",route.date_key,minute,signal.component,
         signal.action_id,route,signal,0.0,0.0,0.0,0.0,0);
      return false;
   }
   double price=signal.direction>0 ? tick.ask : tick.bid;
   double stop=signal.direction>0 ? price-STOP_ATR*route.atr : price+STOP_ATR*route.atr;
   double target=signal.direction>0 ? price+TARGET_ATR*route.atr : price-TARGET_ATR*route.atr;
   int digits=(int)SymbolInfoInteger(_Symbol,SYMBOL_DIGITS);
   stop=NormalizeDouble(stop,digits);
   target=NormalizeDouble(target,digits);
   price=NormalizeDouble(price,digits);
   int stops_level=(int)SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL);
   if(MathAbs(price-stop)<stops_level*_Point || MathAbs(target-price)<stops_level*_Point)
   {
      Audit("ENTRY_BLOCK","BROKER_STOPS_LEVEL",route.date_key,minute,signal.component,
         signal.action_id,route,signal,0.0,price,stop,target,0);
      return false;
   }
   double realized_today=0.0;
   bool intraday_loss_seen=false;
   if(!OwnRealizedToday(route.date_key,realized_today,intraday_loss_seen))
   {
      g_integrity_failed=true;
      Audit("ENTRY_BLOCK","HISTORY_RISK_SCAN_FAILED",route.date_key,minute,
         signal.component,signal.action_id,route,signal,0.0,price,stop,target,0);
      return false;
   }
   double scale=RiskScale(signal.component);
   if(intraday_loss_seen)
      scale=MathMin(scale,InpIntradayRetryRiskScale);
   double volume=RiskSizedVolume(signal.direction,price,stop,scale);
   if(volume<=0.0)
   {
      Audit("ENTRY_BLOCK","RISK_VOLUME_INVALID",route.date_key,minute,signal.component,
         signal.action_id,route,signal,0.0,price,stop,target,0);
      return false;
   }
   double margin=0.0;
   ENUM_ORDER_TYPE type=signal.direction>0 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   if(!OrderCalcMargin(type,_Symbol,volume,price,margin)
      || margin>AccountInfoDouble(ACCOUNT_MARGIN_FREE)*InpMaxMarginFraction)
   {
      Audit("ENTRY_BLOCK","MARGIN_LIMIT",route.date_key,minute,signal.component,
         signal.action_id,route,signal,volume,price,stop,target,0);
      return false;
   }
   MqlTradeRequest request={};
   MqlTradeResult result={};
   MqlTradeCheckResult check={};
   request.action=TRADE_ACTION_DEAL;
   request.symbol=_Symbol;
   request.magic=signal.magic;
   request.volume=volume;
   request.type=type;
   request.price=price;
   request.sl=stop;
   request.tp=target;
   request.deviation=InpMaxDeviationPoints;
   request.type_filling=FillPolicy();
   request.type_time=ORDER_TIME_GTC;
   request.comment=StringFormat("V41|%s|%d|%d",
      signal.component=="V6_PROTECTED" ? "V6" : "V19",signal.exit_minute,route.date_key);
   ResetLastError();
   ulong check_started=GetTickCount64();
   bool check_ok=OrderCheck(request,check);
   double check_ms=(double)(GetTickCount64()-check_started);
   int check_error=GetLastError();
   // MqlTradeCheckResult uses retcode 0 for a successful "Done" check.
   // TRADE_RETCODE_DONE/PLACED belong to the later MqlTradeResult from OrderSend.
   bool check_pass=check_ok && check.retcode==0;
   if(!check_pass)
   {
      PrintFormat("V41_ORDER_CHECK_FAIL|retcode=%u|error=%d|comment=%s|tester=%s",
         check.retcode,check_error,check.comment,
         (bool)MQLInfoInteger(MQL_TESTER)?"true":"false");
      // Some local MT5 agents return no check result (retcode 0) even though
      // their simulated matching engine accepts the same request.  Production
      // remains fail-closed; only Strategy Tester may continue to OrderSend.
      if(!(bool)MQLInfoInteger(MQL_TESTER))
      {
         OperationalHealth("ORDER_CHECK_FAILED",check_ms,-1.0,price,0.0,check.retcode);
         Audit("ENTRY_BLOCK","ORDER_CHECK_"+IntegerToString((int)check.retcode)
            +"_ERR_"+IntegerToString(check_error),route.date_key,minute,
            signal.component,signal.action_id,route,signal,volume,price,stop,target,0);
         return false;
      }
   }
   ulong send_started=GetTickCount64();
   bool sent=OrderSend(request,result);
   double send_ms=(double)(GetTickCount64()-send_started);
   bool filled=sent && (result.retcode==TRADE_RETCODE_DONE
      || result.retcode==TRADE_RETCODE_PLACED || result.retcode==TRADE_RETCODE_DONE_PARTIAL);
   Audit(filled?"ENTRY_SENT":"ENTRY_FAILED",IntegerToString((int)result.retcode),
      route.date_key,minute,signal.component,signal.action_id,route,signal,volume,
      price,stop,target,result.deal!=0 ? result.deal : result.order,scale);
   if(filled && !IncrementOrdersToday(route.date_key))
   {
      g_integrity_failed=true;
      Audit("STATE_FAIL","ORDERS_COUNT_PERSIST_FAILED",route.date_key,minute,
         signal.component,signal.action_id,route,signal,volume,price,stop,target,
         result.deal!=0 ? result.deal : result.order,scale);
   }
   OperationalHealth("ORDER_EXECUTION",check_ms,send_ms,price,result.price,result.retcode);
   return filled;
}

int CommentExitMinute(const string comment)
{
   string parts[];
   int count=StringSplit(comment,'|',parts);
   if(count<4 || parts[0]!="V41")
      return 0;
   return (int)StringToInteger(parts[2]);
}

int CommentDateKey(const string comment)
{
   string parts[];
   int count=StringSplit(comment,'|',parts);
   if(count<4 || parts[0]!="V41")
      return 0;
   return (int)StringToInteger(parts[3]);
}

bool ClosePositionTicket(const ulong ticket,const string reason)
{
   if(!PositionSelectByTicket(ticket))
      return true;
   string symbol=PositionGetString(POSITION_SYMBOL);
   ulong magic=(ulong)PositionGetInteger(POSITION_MAGIC);
   if(symbol!=_Symbol || !IsOwnMagic(magic))
      return false;
   double volume=PositionGetDouble(POSITION_VOLUME);
   ENUM_POSITION_TYPE position_type=(ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
   MqlTick tick={};
   if(!SymbolInfoTick(_Symbol,tick))
      return false;
   MqlTradeRequest request={};
   MqlTradeResult result={};
   request.action=TRADE_ACTION_DEAL;
   request.position=ticket;
   request.symbol=_Symbol;
   request.magic=magic;
   request.volume=volume;
   request.type=position_type==POSITION_TYPE_BUY ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
   request.price=request.type==ORDER_TYPE_BUY ? tick.ask : tick.bid;
   request.deviation=InpMaxDeviationPoints;
   request.type_filling=FillPolicy();
   request.comment="V41_CLOSE_"+reason;
   ulong close_send_started=GetTickCount64();
   bool sent=OrderSend(request,result);
   double close_send_ms=(double)(GetTickCount64()-close_send_started);
   OperationalHealth("CLOSE_EXECUTION",-1.0,close_send_ms,request.price,result.price,result.retcode);
   return sent && (result.retcode==TRADE_RETCODE_DONE
      || result.retcode==TRADE_RETCODE_DONE_PARTIAL || result.retcode==TRADE_RETCODE_PLACED);
}

void ManageOwnedPositions()
{
   int date_key=0,weekday=0;
   int minute=NewYorkMinute(TimeCurrent(),date_key,weekday);
   for(int i=PositionsTotal()-1;i>=0;--i)
   {
      ulong ticket=PositionGetTicket(i);
      if(ticket==0 || !PositionSelectByTicket(ticket)
         || PositionGetString(POSITION_SYMBOL)!=_Symbol
         || !IsOwnMagic((ulong)PositionGetInteger(POSITION_MAGIC)))
         continue;
      string comment=PositionGetString(POSITION_COMMENT);
      int exit_minute=CommentExitMinute(comment);
      int entry_date=CommentDateKey(comment);
      bool emergency=EmergencyStopPresent();
      bool time_exit=exit_minute>0 && (date_key>entry_date || minute>=exit_minute);
      if(emergency || time_exit)
      {
         if(!InpEnableOrders || !InpBrokerActionAllowed || InpAuthorizationToken!=ORDER_AUTH_TOKEN)
         {
            g_integrity_failed=true;
            return;
         }
         if(!ClosePositionTicket(ticket,emergency?"EMERGENCY":"TIME"))
            g_integrity_failed=true;
      }
   }
}

void RebuildLossStreaks()
{
   int streak_v6=0,streak_v19=0;
   ulong last_deal=0;
   if(HistorySelect(0,TimeCurrent()))
   {
      int total=HistoryDealsTotal();
      for(int i=0;i<total;++i)
      {
         ulong ticket=HistoryDealGetTicket(i);
         if(ticket==0
            || HistoryDealGetString(ticket,DEAL_SYMBOL)!=_Symbol)
            continue;
         ulong magic=(ulong)HistoryDealGetInteger(ticket,DEAL_MAGIC);
         if(!IsOwnMagic(magic))
            continue;
         ENUM_DEAL_ENTRY entry=(ENUM_DEAL_ENTRY)HistoryDealGetInteger(ticket,DEAL_ENTRY);
         if(entry!=DEAL_ENTRY_OUT && entry!=DEAL_ENTRY_OUT_BY && entry!=DEAL_ENTRY_INOUT)
            continue;
         double pnl=HistoryDealGetDouble(ticket,DEAL_PROFIT)
            +HistoryDealGetDouble(ticket,DEAL_COMMISSION)+HistoryDealGetDouble(ticket,DEAL_SWAP);
         if(magic==MAGIC_V6)
            streak_v6=pnl>0.0 ? 0 : streak_v6+1;
         else
            streak_v19=pnl>0.0 ? 0 : streak_v19+1;
         last_deal=MathMax(last_deal,ticket);
      }
   }
   SetState("STREAK_V6",(double)streak_v6);
   SetState("STREAK_V19",(double)streak_v19);
   SetState("LAST_DEAL",(double)last_deal);
}

void UpdateLossStreakFromDeal(const ulong ticket)
{
   if(ticket==0 || !HistoryDealSelect(ticket))
      return;
   ulong magic=(ulong)HistoryDealGetInteger(ticket,DEAL_MAGIC);
   if(!IsOwnMagic(magic) || HistoryDealGetString(ticket,DEAL_SYMBOL)!=_Symbol)
      return;
   ENUM_DEAL_ENTRY entry=(ENUM_DEAL_ENTRY)HistoryDealGetInteger(ticket,DEAL_ENTRY);
   if(entry!=DEAL_ENTRY_OUT && entry!=DEAL_ENTRY_OUT_BY && entry!=DEAL_ENTRY_INOUT)
      return;
   ulong previous=(ulong)(GlobalVariableCheck(StateName("LAST_DEAL"))
      ? GlobalVariableGet(StateName("LAST_DEAL")) : 0.0);
   if(ticket<=previous)
      return;
   double pnl=HistoryDealGetDouble(ticket,DEAL_PROFIT)
      +HistoryDealGetDouble(ticket,DEAL_COMMISSION)+HistoryDealGetDouble(ticket,DEAL_SWAP);
   string suffix=magic==MAGIC_V6 ? "STREAK_V6" : "STREAK_V19";
   int streak=GlobalVariableCheck(StateName(suffix)) ? (int)GlobalVariableGet(StateName(suffix)) : 0;
   SetState(suffix,(double)(pnl>0.0 ? 0 : streak+1));
   SetState("LAST_DEAL",(double)ticket);
}

void OnTradeTransaction(const MqlTradeTransaction &transaction,
                        const MqlTradeRequest &request,
                        const MqlTradeResult &result)
{
   if(transaction.type==TRADE_TRANSACTION_DEAL_ADD)
      UpdateLossStreakFromDeal(transaction.deal);
}

bool ValidateInputs()
{
   bool tester=(bool)MQLInfoInteger(MQL_TESTER);
   if(InpConfigSha256!=CONFIG_SHA256 || InpExpectedSymbol!=EXPECTED_SYMBOL
      || InpExpectedServer!=EXPECTED_SERVER || InpAllowedAccountLogin!=EXPECTED_ACCOUNT_LOGIN
       || InpInitialStopRiskUsd!=20.0 || InpIntradayRetryRiskScale!=0.2
      || InpMaxSpreadPoints!=15
      || InpMaxDeviationPoints!=10 || InpMaxOrdersPerNyDay!=3
       || InpDailyLossLimitR!=3.0 || InpMaxMarginFraction!=1.00
      || InpServerUtcOffsetMinutes!=0 || InpHistoryBars!=90000
      || InpHeartbeatSeconds!=60 || InpMutexStaleSeconds!=180
      || InpInstanceId=="" || StringLen(InpInstanceId)>12 || !AuthorizationValid())
      return false;
    if((!tester && (InpEmergencyStopFile!="SHARED_1033030_US500_V41_EMERGENCY_STOP.txt"
       || InpAuditLogFile!="SHARED_1033030_US500_V41_AUDIT.csv"))
      || (tester && (InpEmergencyStopFile=="" || InpAuditLogFile=="")))
      return false;
   if((InpTesterBypassBinding || InpTesterBypassBoundary || InpTesterTraceFile!="") && !tester)
      return false;
   bool reset_ok=(!InpResetPersistentState && InpPersistentResetToken=="NO_RESET")
      || (InpResetPersistentState && InpPersistentResetToken==RESET_TOKEN);
   return reset_ok;
}

int OnInit()
{
   bool tester=(bool)MQLInfoInteger(MQL_TESTER);
   if(!ValidateInputs())
   {
      Print("V41_INIT_FAIL|INPUT_VALIDATION");
      return INIT_PARAMETERS_INCORRECT;
   }
   if(!tester || !InpTesterBypassBinding)
   {
      if(AccountInfoInteger(ACCOUNT_LOGIN)!=EXPECTED_ACCOUNT_LOGIN
         || AccountInfoString(ACCOUNT_SERVER)!=EXPECTED_SERVER || _Symbol!=EXPECTED_SYMBOL)
      {
         PrintFormat("V41_INIT_FAIL|BINDING|login=%I64d|server=%s|symbol=%s",
            AccountInfoInteger(ACCOUNT_LOGIN),AccountInfoString(ACCOUNT_SERVER),_Symbol);
         return INIT_FAILED;
      }
      if((ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)!=ACCOUNT_TRADE_MODE_DEMO)
      {
         PrintFormat("V41_INIT_FAIL|NOT_DEMO|mode=%d",AccountInfoInteger(ACCOUNT_TRADE_MODE));
         return INIT_FAILED;
      }
   }
   else if(_Symbol!=InpExpectedSymbol)
   {
      PrintFormat("V41_INIT_FAIL|TESTER_SYMBOL|actual=%s|expected=%s",_Symbol,InpExpectedSymbol);
      return INIT_FAILED;
   }
   if(!SymbolSelect(InpUS100Symbol,true) || !SymbolSelect(InpUS30Symbol,true))
   {
      PrintFormat("V41_INIT_FAIL|BREADTH_SYMBOL_SELECT|us100=%s|us30=%s|error=%d",
         InpUS100Symbol,InpUS30Symbol,GetLastError());
      return INIT_FAILED;
   }
   if(InpEnforceProspectiveBoundary && !(tester && InpTesterBypassBoundary)
      && ServerToUtc(TimeCurrent())<PROSPECTIVE_BOUNDARY_UTC)
   {
      PrintFormat("V41_INIT_FAIL|PROSPECTIVE_BOUNDARY|now=%I64d|boundary=%I64d",
         (long)ServerToUtc(TimeCurrent()),(long)PROSPECTIVE_BOUNDARY_UTC);
      return INIT_FAILED;
   }
   g_prefix=StringFormat("US500_V41_%s_%I64d_%s_%s",InpInstanceId,
      AccountInfoInteger(ACCOUNT_LOGIN),_Symbol,StringSubstr(CONFIG_SHA256,0,8));
   g_mutex_owner=StateName("MUTEX_OWNER");
   g_mutex_heartbeat=StateName("MUTEX_HEARTBEAT");
   if(!AcquireMutex())
   {
      Print("V41_INIT_FAIL|MUTEX_ACQUIRE");
      return INIT_FAILED;
   }
   if(InpResetPersistentState)
   {
      if(InpPersistentResetToken!=RESET_TOKEN || !ResetPersistentState())
      {
         PrintFormat("V41_INIT_FAIL|PERSISTENT_RESET|error=%d",GetLastError());
         ReleaseMutex();
         return INIT_FAILED;
      }
   }
   if(EmergencyStopPresent())
   {
      PrintFormat("V41_INIT_FAIL|EMERGENCY_STOP_PRESENT|file=%s",InpEmergencyStopFile);
      ReleaseMutex();
      return INIT_FAILED;
   }
   RebuildLossStreaks();
   // Strategy Tester advances simulated timers far faster than wall time.  The
   // production timer remains mandatory; tester safety checks run on every tick.
   if(!tester && !EventSetTimer(InpHeartbeatSeconds))
   {
      PrintFormat("V41_INIT_FAIL|EVENT_TIMER|error=%d",GetLastError());
      ReleaseMutex();
      return INIT_FAILED;
   }
   g_timer_set=!tester;
   RouteState route={};
   SignalState signal=EmptySignal();
   MqlDateTime ny={};
   ServerTimeToNewYork(TimeCurrent(),ny);
   if(!Audit("INIT",InpEnableOrders?"ORDER_MODE_AUTHORIZED":"DISARMED_READY",
      DateKey(ny),ny.hour*60+ny.min,"","",route,signal,0.0,0.0,0.0,0.0,0))
   {
      PrintFormat("V41_INIT_FAIL|AUDIT_INIT|error=%d|file=%s",GetLastError(),InpAuditLogFile);
      EventKillTimer();
      g_timer_set=false;
      ReleaseMutex();
      return INIT_FAILED;
   }
   PrintFormat("V41_INIT_OK|contract=%s|config=%s|tester=%s",
      CONTRACT_ID,CONFIG_SHA256,tester?"true":"false");
   OperationalHealth("INIT_HEALTH");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   if(g_timer_set)
   {
      EventKillTimer();
      g_timer_set=false;
   }
   ReleaseMutex();
}

void OnTimer()
{
   if(!RefreshMutex())
      g_integrity_failed=true;
   RouteState route={};
   SignalState signal=EmptySignal();
   MqlDateTime ny={};
   ServerTimeToNewYork(TimeCurrent(),ny);
   Audit("HEARTBEAT",EmergencyStopPresent()?"EMERGENCY_STOP":
      (g_integrity_failed?"INTEGRITY_FAILED":"OK"),DateKey(ny),ny.hour*60+ny.min,
      "","",route,signal,0.0,0.0,0.0,0.0,0);
   OperationalHealth("HEARTBEAT_HEALTH");
}

void ProcessWindow(const int window_index,const int date_key,const int minute)
{
   int entry_minute=WINDOW_ENTRY_MINUTES[window_index];
   if(minute<entry_minute || minute>entry_minute+4 || IsLatched(entry_minute,date_key))
      return;
   RouteState route={};
   if(!BuildRoute(WINDOW_DECISION_MINUTES[window_index],route) || route.date_key!=date_key)
   {
      if(minute>=entry_minute+4)
      {
         SignalState empty=EmptySignal();
         Audit("DATA_FAIL","ROUTE_BUILD_FAILED",date_key,minute,"","",route,empty,
            0.0,0.0,0.0,0.0,0);
         Latch(entry_minute,date_key);
      }
      return;
   }
   SignalState signal=V6Signal(window_index,route);
   if(window_index==0 && !signal.selected)
      signal=V19Signal(route);
   if(!Audit("DECISION",signal.selected?"SELECTED":"NO_SIGNAL",date_key,minute,
      signal.component,signal.action_id,route,signal,0.0,0.0,0.0,0.0,0))
      return;
   if(!TesterTrace("DECISION",date_key,entry_minute,signal,route))
   {
      g_integrity_failed=true;
      return;
   }
   if(!Latch(entry_minute,date_key))
   {
      g_integrity_failed=true;
      return;
   }
   if(!signal.selected)
      return;
   if(HasAnySymbolExposure())
   {
      Audit("ENTRY_BLOCK","SYMBOL_EXPOSURE_EXISTS",date_key,minute,signal.component,
         signal.action_id,route,signal,0.0,0.0,0.0,0.0,0);
      return;
   }
   if(!InpEnableOrders)
   {
      Audit("ENTRY_BLOCK","DISARMED",date_key,minute,signal.component,signal.action_id,
         route,signal,0.0,0.0,0.0,0.0,0);
      return;
   }
   SubmitEntry(signal,route,minute);
}

void OnTick()
{
   if(!(bool)MQLInfoInteger(MQL_TESTER) && g_mutex_owned
      && (int)TimeLocal()-g_last_mutex_refresh>=InpHeartbeatSeconds)
      if(!RefreshMutex())
         g_integrity_failed=true;
   ManageOwnedPositions();
   if(g_integrity_failed || EmergencyStopPresent())
      return;
   int date_key=0,weekday=0;
   int minute=NewYorkMinute(TimeCurrent(),date_key,weekday);
   for(int i=0;i<WINDOW_COUNT;++i)
      ProcessWindow(i,date_key,minute);
}

#property copyright "Research-only Capital.com MT5 real-tick screen"
#property version   "1.00"
#property strict

input string InpLogicalSymbol="";
input string InpOfficialRunMarker="";
input string InpRunId="";
input string InpOutputPrefix="mt5_london";
input datetime InpFrozenStart=D'2016.07.01 00:00:00';
input datetime InpFrozenEndExclusive=D'2026.07.01 00:00:00';
input double InpStartingEquity=1000.0;
input double InpRiskFraction=0.005;
input bool InpDebugLogging=false;

const string REQUIRED_MARKER="LONDON_MT5_REAL_TICK_V1_OFFICIAL";
const string PREFLIGHT_MARKER="LONDON_MT5_REAL_TICK_V1_PREFLIGHT";
const long MAGIC=26071401;
const double H1_SLOPE_THRESHOLD=0.10;
const double RANGE_MIN_ATR=0.50;
const double RANGE_MAX_ATR=2.00;
const double BREAK_ATR=0.10;
const double BODY_MIN=0.50;
const double CLOSE_LONG_MIN=0.75;
const double CLOSE_SHORT_MAX=0.25;
const double STOP_BUFFER_ATR=0.10;
const double STOP_MIN_ATR=0.75;
const double STOP_MAX_ATR=1.50;
const double TARGET_R=2.0;

struct MidBar
  {
   datetime start_utc;
   double open;
   double high;
   double low;
   double close;
  };

MidBar g_m15_current;
MidBar g_h1_current;
MidBar g_m15[];
MidBar g_h1[];
bool g_m15_initialized=false;
bool g_h1_initialized=false;
bool g_preflight=false;
datetime g_range_date=0;
double g_overnight_high=0.0;
double g_overnight_low=0.0;
bool g_range_has_data=false;
bool g_range_frozen=false;
bool g_daily_used=false;
int g_signal_handle=INVALID_HANDLE;
int g_trade_handle=INVALID_HANDLE;
datetime g_entry_time=0;
double g_entry_price=0.0;
double g_initial_risk=0.0;
double g_requested_stop=0.0;
double g_requested_target=0.0;
string g_direction="";

int LastSundayDay(const int year,const int month)
  {
   MqlDateTime value={0};
   value.year=year;
   value.mon=month;
   value.day=31;
   if(month==4 || month==6 || month==9 || month==11)
      value.day=30;
   if(month==2)
      value.day=((year%4==0 && year%100!=0) || year%400==0) ? 29 : 28;
   datetime stamp=StructToTime(value);
   TimeToStruct(stamp,value);
   return value.day-value.day_of_week;
  }

datetime MakeUTC(const int year,const int month,const int day,const int hour)
  {
   MqlDateTime value={0};
   value.year=year;
   value.mon=month;
   value.day=day;
   value.hour=hour;
   return StructToTime(value);
  }

int LondonOffsetUTC(const datetime utc)
  {
   MqlDateTime value;
   TimeToStruct(utc,value);
   datetime start=MakeUTC(value.year,3,LastSundayDay(value.year,3),1);
   datetime finish=MakeUTC(value.year,10,LastSundayDay(value.year,10),1);
   return (utc>=start && utc<finish) ? 1 : 0;
  }

int BrokerOffsetUTC(const datetime utc)
  {
   return 2+LondonOffsetUTC(utc);
  }

datetime BrokerToUTC(const datetime broker)
  {
   datetime candidate=broker-3*3600;
   if(BrokerOffsetUTC(candidate)==3)
      return candidate;
   candidate=broker-2*3600;
   if(BrokerOffsetUTC(candidate)==2)
      return candidate;
   return 0;
  }

datetime UTCToLondon(const datetime utc)
  {
   return utc+LondonOffsetUTC(utc)*3600;
  }

datetime FloorInterval(const datetime value,const int seconds)
  {
   return (datetime)(((long)value/seconds)*seconds);
  }

void ResetBar(MidBar &bar,const datetime start,const double mid)
  {
   bar.start_utc=start;
   bar.open=mid;
   bar.high=mid;
   bar.low=mid;
   bar.close=mid;
  }

void UpdateBar(MidBar &bar,const double mid)
  {
   bar.high=MathMax(bar.high,mid);
   bar.low=MathMin(bar.low,mid);
   bar.close=mid;
  }

void AppendBar(MidBar &bars[],const MidBar &bar,const int maximum)
  {
   int size=ArraySize(bars);
   if(size>=maximum)
     {
      for(int i=1;i<size;i++)
         bars[i-1]=bars[i];
      bars[size-1]=bar;
      return;
     }
   ArrayResize(bars,size+1);
   bars[size]=bar;
  }

double TrueRange(const MidBar &current,const MidBar &previous)
  {
   return MathMax(current.high-current.low,MathMax(MathAbs(current.high-previous.close),MathAbs(current.low-previous.close)));
  }

double WilderATR(MidBar &bars[],const int period)
  {
   int size=ArraySize(bars);
   if(size<period+1)
      return 0.0;
   int first=size-period;
   double atr=0.0;
   for(int i=first;i<size;i++)
      atr+=TrueRange(bars[i],bars[i-1]);
   return atr/period;
  }

double EMAAt(MidBar &bars[],const int end_index,const int period)
  {
   if(end_index+1<period)
      return 0.0;
   double ema=0.0;
   for(int i=0;i<period;i++)
      ema+=bars[i].close;
   ema/=period;
   double alpha=2.0/(period+1.0);
   for(int i=period;i<=end_index;i++)
      ema=alpha*bars[i].close+(1.0-alpha)*ema;
   return ema;
  }

string DirectionalBias()
  {
   int size=ArraySize(g_h1);
   if(size<57)
      return "NO_DIRECTIONAL_BIAS";
   double atr=WilderATR(g_h1,14);
   double current=EMAAt(g_h1,size-1,50);
   double prior=EMAAt(g_h1,size-7,50);
   if(atr<=0.0 || current<=0.0 || prior<=0.0)
      return "NO_DIRECTIONAL_BIAS";
   double slope=(current-prior)/atr;
   if(g_h1[size-1].close>current && slope>=H1_SLOPE_THRESHOLD)
      return "LONG";
   if(g_h1[size-1].close<current && slope<=-H1_SLOPE_THRESHOLD)
      return "SHORT";
   return "NO_DIRECTIONAL_BIAS";
  }

double RoundVolumeDown(const double raw)
  {
   double minimum=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double maximum=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX);
   double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   if(step<=0.0 || raw<minimum)
      return 0.0;
   double bounded=MathMin(raw,maximum);
   double steps=MathFloor((bounded-minimum+1e-12)/step);
   return NormalizeDouble(minimum+steps*step,8);
  }

bool TesterContainmentOK()
  {
   if(!MQLInfoInteger(MQL_TESTER))
      return false;
   if(MQLInfoInteger(MQL_OPTIMIZATION) || MQLInfoInteger(MQL_FORWARD))
      return false;
   if(_Symbol!=InpLogicalSymbol)
      return false;
   if(InpOfficialRunMarker!=REQUIRED_MARKER && InpOfficialRunMarker!=PREFLIGHT_MARKER)
      return false;
   if(StringLen(InpRunId)==0)
      return false;
   return true;
  }

void WriteContractSnapshot()
  {
   string name=InpOutputPrefix+"_contract.tsv";
   int handle=FileOpen(name,FILE_WRITE|FILE_CSV|FILE_ANSI,'\t');
   if(handle==INVALID_HANDLE)
      return;
   FileWrite(handle,"field","value");
   FileWrite(handle,"exact_symbol",_Symbol);
   FileWrite(handle,"description",SymbolInfoString(_Symbol,SYMBOL_DESCRIPTION));
   FileWrite(handle,"digits",(string)SymbolInfoInteger(_Symbol,SYMBOL_DIGITS));
   FileWrite(handle,"point",DoubleToString(SymbolInfoDouble(_Symbol,SYMBOL_POINT),10));
   FileWrite(handle,"tick_size",DoubleToString(SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_SIZE),10));
   FileWrite(handle,"tick_value",DoubleToString(SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_VALUE),10));
   FileWrite(handle,"tick_value_profit",DoubleToString(SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_VALUE_PROFIT),10));
   FileWrite(handle,"tick_value_loss",DoubleToString(SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_VALUE_LOSS),10));
   FileWrite(handle,"contract_size",DoubleToString(SymbolInfoDouble(_Symbol,SYMBOL_TRADE_CONTRACT_SIZE),4));
   FileWrite(handle,"volume_min",DoubleToString(SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN),8));
   FileWrite(handle,"volume_max",DoubleToString(SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX),8));
   FileWrite(handle,"volume_step",DoubleToString(SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP),8));
   FileWrite(handle,"stops_level",(string)SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL));
   FileWrite(handle,"freeze_level",(string)SymbolInfoInteger(_Symbol,SYMBOL_TRADE_FREEZE_LEVEL));
   FileWrite(handle,"calculation_mode",(string)SymbolInfoInteger(_Symbol,SYMBOL_TRADE_CALC_MODE));
   FileWrite(handle,"margin_initial",DoubleToString(SymbolInfoDouble(_Symbol,SYMBOL_MARGIN_INITIAL),8));
   FileWrite(handle,"margin_maintenance",DoubleToString(SymbolInfoDouble(_Symbol,SYMBOL_MARGIN_MAINTENANCE),8));
   FileWrite(handle,"currency_base",SymbolInfoString(_Symbol,SYMBOL_CURRENCY_BASE));
   FileWrite(handle,"currency_profit",SymbolInfoString(_Symbol,SYMBOL_CURRENCY_PROFIT));
   FileWrite(handle,"currency_margin",SymbolInfoString(_Symbol,SYMBOL_CURRENCY_MARGIN));
   FileWrite(handle,"swap_mode",(string)SymbolInfoInteger(_Symbol,SYMBOL_SWAP_MODE));
   FileWrite(handle,"swap_long",DoubleToString(SymbolInfoDouble(_Symbol,SYMBOL_SWAP_LONG),8));
   FileWrite(handle,"swap_short",DoubleToString(SymbolInfoDouble(_Symbol,SYMBOL_SWAP_SHORT),8));
   FileWrite(handle,"triple_rollover_day",(string)SymbolInfoInteger(_Symbol,SYMBOL_SWAP_ROLLOVER3DAYS));
   FileWrite(handle,"account_server",AccountInfoString(ACCOUNT_SERVER));
   FileWrite(handle,"account_currency",AccountInfoString(ACCOUNT_CURRENCY));
   FileWrite(handle,"account_leverage",(string)AccountInfoInteger(ACCOUNT_LEVERAGE));
   FileWrite(handle,"account_margin_mode",(string)AccountInfoInteger(ACCOUNT_MARGIN_MODE));
   FileClose(handle);
  }

datetime NextMonth(const datetime value)
  {
   MqlDateTime part;
   TimeToStruct(value,part);
   part.day=1;
   part.hour=0;
   part.min=0;
   part.sec=0;
   part.mon++;
   if(part.mon==13)
     {
      part.mon=1;
      part.year++;
     }
   return StructToTime(part);
  }

void WriteCoveragePreflight()
  {
   int handle=FileOpen(InpOutputPrefix+"_coverage.tsv",FILE_WRITE|FILE_CSV|FILE_ANSI,'\t');
   if(handle==INVALID_HANDLE)
      return;
   FileWrite(handle,"instrument","month","tick_count","first_time_msc","last_time_msc","maximum_internal_gap_msc","copy_error");
   datetime month=InpFrozenStart;
   while(month<InpFrozenEndExclusive)
     {
      datetime next=NextMonth(month);
      MqlTick ticks[];
      ResetLastError();
      long count=CopyTicksRange(_Symbol,ticks,COPY_TICKS_ALL,(ulong)month*1000,(ulong)next*1000-1);
      int error=GetLastError();
      long first=0;
      long last=0;
      long maximum_gap=0;
      if(count>0)
        {
         first=(long)ticks[0].time_msc;
         last=(long)ticks[count-1].time_msc;
         for(long i=1;i<count;i++)
           {
            long gap=(long)ticks[i].time_msc-(long)ticks[i-1].time_msc;
            if(gap>maximum_gap)
               maximum_gap=gap;
           }
        }
      MqlDateTime part;
      TimeToStruct(month,part);
      string key=StringFormat("%04d-%02d",part.year,part.mon);
      FileWrite(handle,_Symbol,key,(string)count,(string)first,(string)last,(string)maximum_gap,(string)error);
      ArrayFree(ticks);
      month=next;
     }
   FileClose(handle);
  }

void OpenLedgers()
  {
   g_signal_handle=FileOpen(InpOutputPrefix+"_signals.tsv",FILE_WRITE|FILE_CSV|FILE_ANSI,'\t');
   if(g_signal_handle!=INVALID_HANDLE)
      FileWrite(g_signal_handle,"run_id","instrument","London_date","direction","signal_time","signal_accepted","rejection_reason","entry_time","entry_Bid","entry_Ask","entry_price","stop","target","requested_volume","rounded_volume","account_feasible","account_rejection_reason");
   g_trade_handle=FileOpen(InpOutputPrefix+"_trades.tsv",FILE_WRITE|FILE_CSV|FILE_ANSI,'\t');
   if(g_trade_handle!=INVALID_HANDLE)
      FileWrite(g_trade_handle,"run_id","instrument","direction","entry_time","entry_price","stop_requested","target_requested","initial_risk_price","exit_time","actual_exit_price","exit_reason","executed_volume","commission");
  }

bool SendTesterDeal(const string direction,const MqlTick &tick,const double stop,const double target,double &requested,double &rounded,string &rejection)
  {
   if(!TesterContainmentOK() || g_preflight)
      return false;
   double entry=(direction=="LONG") ? tick.ask : tick.bid;
   ENUM_ORDER_TYPE type=(direction=="LONG") ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   double one_lot=0.0;
   if(!OrderCalcProfit(type,_Symbol,1.0,entry,stop,one_lot))
     {
      rejection="ORDER_CALC_PROFIT_FAILED";
      return false;
     }
   one_lot=MathAbs(one_lot);
   if(one_lot<=0.0)
     {
      rejection="ORDER_CALC_PROFIT_NONPOSITIVE";
      return false;
     }
   requested=InpStartingEquity*InpRiskFraction/one_lot;
   rounded=RoundVolumeDown(requested);
   if(rounded<=0.0)
     {
      rejection="ACCOUNT_MINIMUM_VOLUME_RISK_REJECT";
      return false;
     }
   double minimum=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double minimum_loss=0.0;
   if(!OrderCalcProfit(type,_Symbol,minimum,entry,stop,minimum_loss) || MathAbs(minimum_loss)>InpStartingEquity*InpRiskFraction+1e-9)
     {
      rejection="ACCOUNT_MINIMUM_VOLUME_RISK_REJECT";
      return false;
     }
   double margin=0.0;
   if(!OrderCalcMargin(type,_Symbol,rounded,entry,margin) || margin>InpStartingEquity*0.20+1e-9)
     {
      rejection="ACCOUNT_MARGIN_REJECT";
      return false;
     }
   MqlTradeRequest request;
   MqlTradeResult result;
   ZeroMemory(request);
   ZeroMemory(result);
   request.action=TRADE_ACTION_DEAL;
   request.magic=MAGIC;
   request.symbol=_Symbol;
   request.volume=rounded;
   request.type=type;
   request.price=entry;
   request.sl=stop;
   request.tp=target;
   request.deviation=0;
   request.type_filling=ORDER_FILLING_FOK;
   request.comment=InpRunId;
   if(!OrderSend(request,result) || (result.retcode!=TRADE_RETCODE_DONE && result.retcode!=TRADE_RETCODE_PLACED))
     {
      rejection="TESTER_ORDER_SEND_REJECT_"+(string)result.retcode;
      return false;
     }
   return true;
  }

void EvaluateCompletedM15(const MidBar &bar,const MqlTick &entry_tick)
  {
   datetime london=UTCToLondon(bar.start_utc);
   MqlDateTime local;
   TimeToStruct(london,local);
   datetime london_day=MakeUTC(local.year,local.mon,local.day,0);
   if(london_day!=g_range_date)
     {
      g_range_date=london_day;
      g_overnight_high=0.0;
      g_overnight_low=0.0;
      g_range_has_data=false;
      g_range_frozen=false;
      g_daily_used=false;
     }
   if(local.hour<8)
     {
      if(!g_range_has_data)
        {
         g_overnight_high=bar.high;
         g_overnight_low=bar.low;
         g_range_has_data=true;
        }
      else
        {
         g_overnight_high=MathMax(g_overnight_high,bar.high);
         g_overnight_low=MathMin(g_overnight_low,bar.low);
        }
      return;
     }
   if(!g_range_frozen)
      g_range_frozen=true;
   if(local.hour<8 || local.hour>=12 || g_daily_used || !g_range_has_data)
      return;
   double h1_atr=WilderATR(g_h1,14);
   double m15_atr=WilderATR(g_m15,14);
   double width=g_overnight_high-g_overnight_low;
   string direction=DirectionalBias();
   if(h1_atr<=0.0 || m15_atr<=0.0 || width<0.50*h1_atr || width>2.00*h1_atr || direction=="NO_DIRECTIONAL_BIAS")
      return;
   double span=bar.high-bar.low;
   if(span<=0.0)
      return;
   double body=MathAbs(bar.close-bar.open)/span;
   double location=(bar.close-bar.low)/span;
   bool signal=false;
   if(direction=="LONG")
      signal=(bar.close>=g_overnight_high+BREAK_ATR*m15_atr && bar.close>bar.open && body>=BODY_MIN && location>=CLOSE_LONG_MIN);
   else
      signal=(bar.close<=g_overnight_low-BREAK_ATR*m15_atr && bar.close<bar.open && body>=BODY_MIN && location<=CLOSE_SHORT_MAX);
   if(!signal)
      return;
   double entry=(direction=="LONG") ? entry_tick.ask : entry_tick.bid;
   double stop=(direction=="LONG") ? bar.low-STOP_BUFFER_ATR*m15_atr : bar.high+STOP_BUFFER_ATR*m15_atr;
   double risk=MathAbs(entry-stop);
   string rejection="";
   double requested=0.0;
   double rounded=0.0;
   bool stop_valid=(risk>=STOP_MIN_ATR*m15_atr && risk<=STOP_MAX_ATR*m15_atr);
   double target=(direction=="LONG") ? entry+TARGET_R*risk : entry-TARGET_R*risk;
   bool accepted=false;
   if(!stop_valid)
      rejection="STOP_DISTANCE_OUTSIDE_FROZEN_RANGE";
   else
      accepted=SendTesterDeal(direction,entry_tick,stop,target,requested,rounded,rejection);
   g_daily_used=stop_valid;
   if(g_signal_handle!=INVALID_HANDLE)
      FileWrite(g_signal_handle,InpRunId,_Symbol,TimeToString(london_day,TIME_DATE),direction,TimeToString(bar.start_utc+15*60,TIME_DATE|TIME_SECONDS),(accepted ? "true" : "false"),rejection,TimeToString((datetime)entry_tick.time,TIME_DATE|TIME_SECONDS),DoubleToString(entry_tick.bid,_Digits),DoubleToString(entry_tick.ask,_Digits),DoubleToString(entry,_Digits),DoubleToString(stop,_Digits),DoubleToString(target,_Digits),DoubleToString(requested,8),DoubleToString(rounded,8),(accepted ? "true" : "false"),rejection);
   if(accepted)
     {
      g_entry_time=(datetime)entry_tick.time;
      g_entry_price=entry;
      g_initial_risk=risk;
      g_requested_stop=stop;
      g_requested_target=target;
      g_direction=direction;
     }
  }

void CloseAtTimeLimit(const MqlTick &tick)
  {
   if(!PositionSelect(_Symbol) || (long)PositionGetInteger(POSITION_MAGIC)!=MAGIC)
      return;
   datetime utc=BrokerToUTC((datetime)tick.time);
   datetime london=UTCToLondon(utc);
   MqlDateTime local;
   TimeToStruct(london,local);
   bool maximum_hold=((datetime)tick.time-g_entry_time)>=8*3600;
   bool forced=(local.hour>=16);
   if(!maximum_hold && !forced)
      return;
   ENUM_POSITION_TYPE position_type=(ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
   double volume=PositionGetDouble(POSITION_VOLUME);
   MqlTradeRequest request;
   MqlTradeResult result;
   ZeroMemory(request);
   ZeroMemory(result);
   request.action=TRADE_ACTION_DEAL;
   request.position=(ulong)PositionGetInteger(POSITION_TICKET);
   request.magic=MAGIC;
   request.symbol=_Symbol;
   request.volume=volume;
   request.type=(position_type==POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
   request.price=(position_type==POSITION_TYPE_BUY) ? tick.bid : tick.ask;
   request.type_filling=ORDER_FILLING_FOK;
   request.comment=maximum_hold ? "MAXIMUM_HOLD" : "FORCED_LONDON_EXIT";
   if(TesterContainmentOK() && !OrderSend(request,result) && InpDebugLogging)
      Print("time-limit tester close rejected: ",result.retcode);
  }

int OnInit()
  {
   if(!TesterContainmentOK())
     {
      Print("LONDON_MT5_REAL_TICK_V1_CONTAINMENT_REJECT");
      return INIT_FAILED;
     }
   g_preflight=(InpOfficialRunMarker==PREFLIGHT_MARKER);
   WriteContractSnapshot();
   if(g_preflight)
      WriteCoveragePreflight();
   else
      OpenLedgers();
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   if(g_signal_handle!=INVALID_HANDLE)
      FileClose(g_signal_handle);
   if(g_trade_handle!=INVALID_HANDLE)
      FileClose(g_trade_handle);
  }

void OnTick()
  {
   if(g_preflight)
      return;
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol,tick) || tick.bid<=0.0 || tick.ask<tick.bid)
      return;
   datetime utc=BrokerToUTC((datetime)tick.time);
   if(utc==0)
      return;
   double mid=(tick.bid+tick.ask)/2.0;
   datetime m15_start=FloorInterval(utc,15*60);
   datetime h1_start=FloorInterval(utc,60*60);
   if(!g_h1_initialized)
     {
      ResetBar(g_h1_current,h1_start,mid);
      g_h1_initialized=true;
     }
   else if(h1_start!=g_h1_current.start_utc)
     {
      AppendBar(g_h1,g_h1_current,256);
      ResetBar(g_h1_current,h1_start,mid);
     }
   else
      UpdateBar(g_h1_current,mid);
   if(!g_m15_initialized)
     {
      ResetBar(g_m15_current,m15_start,mid);
      g_m15_initialized=true;
     }
   else if(m15_start!=g_m15_current.start_utc)
     {
      AppendBar(g_m15,g_m15_current,256);
      EvaluateCompletedM15(g_m15_current,tick);
      ResetBar(g_m15_current,m15_start,mid);
     }
   else
      UpdateBar(g_m15_current,mid);
   CloseAtTimeLimit(tick);
  }

void OnTradeTransaction(const MqlTradeTransaction &transaction,const MqlTradeRequest &request,const MqlTradeResult &result)
  {
   if(g_preflight || g_trade_handle==INVALID_HANDLE || transaction.type!=TRADE_TRANSACTION_DEAL_ADD)
      return;
   ulong deal=transaction.deal;
   if(!HistoryDealSelect(deal) || (long)HistoryDealGetInteger(deal,DEAL_MAGIC)!=MAGIC)
      return;
   ENUM_DEAL_ENTRY entry=(ENUM_DEAL_ENTRY)HistoryDealGetInteger(deal,DEAL_ENTRY);
   if(entry!=DEAL_ENTRY_OUT && entry!=DEAL_ENTRY_OUT_BY)
      return;
   datetime exit_time=(datetime)HistoryDealGetInteger(deal,DEAL_TIME);
   double exit_price=HistoryDealGetDouble(deal,DEAL_PRICE);
   double volume=HistoryDealGetDouble(deal,DEAL_VOLUME);
   double commission=HistoryDealGetDouble(deal,DEAL_COMMISSION);
   string reason=EnumToString((ENUM_DEAL_REASON)HistoryDealGetInteger(deal,DEAL_REASON));
   FileWrite(g_trade_handle,InpRunId,_Symbol,g_direction,TimeToString(g_entry_time,TIME_DATE|TIME_SECONDS),DoubleToString(g_entry_price,_Digits),DoubleToString(g_requested_stop,_Digits),DoubleToString(g_requested_target,_Digits),DoubleToString(g_initial_risk,_Digits),TimeToString(exit_time,TIME_DATE|TIME_SECONDS),DoubleToString(exit_price,_Digits),reason,DoubleToString(volume,8),DoubleToString(commission,2));
  }

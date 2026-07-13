//+------------------------------------------------------------------+
//| A1XauR6NativeSpreadProvenanceProbe.mq5                           |
//| NP1-G1 ZERO-ACTION NATIVE HISTORY PROVENANCE PROBE               |
//+------------------------------------------------------------------+
#property copyright "maksoftwares - NP1-G1 diagnostic only"
#property version   "1.000"
#property strict

input string InpRunId="compile_only";
input bool InpWarmup=false;
input string InpH1File="h1_bars.tsv";
input string InpH4File="h4_bars.tsv";
input string InpD1File="d1_bars.tsv";
input string InpInterfacesFile="bar_spread_interfaces.tsv";
input string InpTicks20250618File="ticks_20250618.tsv";
input string InpTicks20250929File="ticks_20250929.tsv";
input string InpTicks20251117File="ticks_20251117.tsv";
input string InpTicks20260414File="ticks_20260414.tsv";
input string InpAssertionsFile="assertions.tsv";
input string InpOrderZeroFile="order.zero";
input string InpDealZeroFile="deal.zero";

const string TARGET_SYMBOL="XAUUSD";

string T(const datetime value)
  {
   MqlDateTime p;
   TimeToStruct(value,p);
   return StringFormat("%04d-%02d-%02dT%02d:%02d:%02d",p.year,p.mon,p.day,p.hour,p.min,p.sec);
  }

string F(const double value)
  {
   if(!MathIsValidNumber(value)) return "";
   return StringFormat("%.17g",value);
  }

bool ZeroFile(const string name)
  {
   int h=FileOpen(name,FILE_WRITE|FILE_BIN);
   if(h==INVALID_HANDLE) return false;
   FileClose(h);
   return true;
  }

void AssertRow(const string id,const bool pass,const string observed,const string expected)
  {
   int h=FileOpen(InpAssertionsFile,FILE_READ|FILE_WRITE|FILE_TXT|FILE_ANSI,'\t');
   if(h==INVALID_HANDLE) return;
   FileSeek(h,0,SEEK_END);
   FileWrite(h,id,pass ? "true" : "false",observed,expected);
   FileClose(h);
  }

bool EnvironmentPass()
  {
   return MQLInfoInteger(MQL_TESTER) && _Symbol==TARGET_SYMBOL && _Period==PERIOD_M5 &&
          AccountInfoInteger(ACCOUNT_LOGIN)==1025742 &&
          AccountInfoString(ACCOUNT_SERVER)=="Capital.ComMena-Demo" &&
          AccountInfoString(ACCOUNT_COMPANY)=="Capital Com Mena Securities Trading L.L.C" &&
          AccountInfoString(ACCOUNT_CURRENCY)=="USD" &&
          AccountInfoInteger(ACCOUNT_LEVERAGE)==50 && TerminalInfoInteger(TERMINAL_BUILD)==5833;
  }

bool ExportBars(const ENUM_TIMEFRAMES tf,const string tf_name,const string filename)
  {
   MqlRates rates[];
   ArraySetAsSeries(rates,false);
   ResetLastError();
   int copied=CopyRates(TARGET_SYMBOL,tf,StringToTime("2015.06.01 00:00:00"),StringToTime("2026.07.01 00:00:00")-1,rates);
   int error=GetLastError();
   int h=FileOpen(filename,FILE_WRITE|FILE_CSV|FILE_ANSI,'\t');
   if(h==INVALID_HANDLE || copied<=0) return false;
   FileWrite(h,"schema_version","timeframe","open_time_broker","open","high","low","close","tick_volume","spread","real_volume","copyrates_return","copyrates_error");
   for(int i=0;i<copied;i++)
      FileWrite(h,"a1_xau_np1_g1_bar_v1",tf_name,T(rates[i].time),F(rates[i].open),F(rates[i].high),F(rates[i].low),F(rates[i].close),(long)rates[i].tick_volume,(int)rates[i].spread,(long)rates[i].real_volume,copied,error);
   FileClose(h);
   return true;
  }

bool AffectedDay(const datetime value)
  {
   string d=StringSubstr(T(value),0,10);
   return d=="2025-06-18" || d=="2025-09-29" || d=="2025-11-17" || d=="2026-04-14";
  }

bool ExportInterfaces()
  {
   int h=FileOpen(InpInterfacesFile,FILE_WRITE|FILE_CSV|FILE_ANSI,'\t');
   if(h==INVALID_HANDLE) return false;
   FileWrite(h,"schema_version","timeframe","open_time_broker","open","high","low","close","tick_volume","real_volume","copyrates_spread","copyspread_spread","ispread_spread","copyspread_return","copyspread_error","ibarshift","ispread_error","point","digits");
   ENUM_TIMEFRAMES tfs[3]={PERIOD_H1,PERIOD_H4,PERIOD_D1};
   string names[3]={"H1","H4","D1"};
   double point=SymbolInfoDouble(TARGET_SYMBOL,SYMBOL_POINT);
   int digits=(int)SymbolInfoInteger(TARGET_SYMBOL,SYMBOL_DIGITS);
   for(int t=0;t<3;t++)
     {
      MqlRates rates[];
      ArraySetAsSeries(rates,false);
      int n=CopyRates(TARGET_SYMBOL,tfs[t],StringToTime("2025.06.18 00:00:00"),StringToTime("2026.04.15 00:00:00")-1,rates);
      if(n<=0) { FileClose(h); return false; }
      for(int i=0;i<n;i++)
        {
         if(!AffectedDay(rates[i].time)) continue;
         int values[];
         ArraySetAsSeries(values,false);
         ResetLastError();
         int rc=CopySpread(TARGET_SYMBOL,tfs[t],rates[i].time,1,values);
         int copy_error=GetLastError();
         int shift=iBarShift(TARGET_SYMBOL,tfs[t],rates[i].time,true);
         ResetLastError();
         int isp=(shift>=0 ? iSpread(TARGET_SYMBOL,tfs[t],shift) : 0);
         int isp_error=GetLastError();
         string cs=(rc==1 ? IntegerToString(values[0]) : "");
         FileWrite(h,"a1_xau_np1_g1_interface_v1",names[t],T(rates[i].time),F(rates[i].open),F(rates[i].high),F(rates[i].low),F(rates[i].close),(long)rates[i].tick_volume,(long)rates[i].real_volume,(int)rates[i].spread,cs,isp,rc,copy_error,shift,isp_error,F(point),digits);
        }
     }
   FileClose(h);
   return true;
  }

bool ExportTicks(const string day,const string filename)
  {
   datetime from=StringToTime(day+" 00:00:00");
   datetime until=from+86400;
   MqlTick ticks[];
   ResetLastError();
   int copied=CopyTicksRange(TARGET_SYMBOL,ticks,COPY_TICKS_ALL,(ulong)from*1000,(ulong)until*1000-1);
   int error=GetLastError();
   int h=FileOpen(filename,FILE_WRITE|FILE_CSV|FILE_ANSI,'\t');
   if(h==INVALID_HANDLE || copied<0) return false;
   FileWrite(h,"schema_version","broker_day","time_msc","time","bid","ask","last","volume","volume_real","flags","raw_ask_minus_bid","raw_spread_points","negative_spread_boolean","quote_sides_positive","copyticks_return","copyticks_error");
   double point=SymbolInfoDouble(TARGET_SYMBOL,SYMBOL_POINT);
   for(int i=0;i<copied;i++)
     {
      bool positive=ticks[i].bid>0 && ticks[i].ask>0;
      double raw=ticks[i].ask-ticks[i].bid;
      FileWrite(h,"a1_xau_np1_g1_tick_v1",day,(long)ticks[i].time_msc,T(ticks[i].time),F(ticks[i].bid),F(ticks[i].ask),F(ticks[i].last),(long)ticks[i].volume,F(ticks[i].volume_real),(uint)ticks[i].flags,positive?F(raw):"",positive&&point>0?F(raw/point):"",positive?(raw<0?"true":"false"):"",positive?"true":"false",copied,error);
     }
   FileClose(h);
   return copied>0;
  }

int OnInit()
  {
   int ah=FileOpen(InpAssertionsFile,FILE_WRITE|FILE_CSV|FILE_ANSI,'\t');
   if(ah==INVALID_HANDLE) return INIT_FAILED;
   FileWrite(ah,"assertion_id","passed","observed","expected");
   FileClose(ah);
   bool zero=ZeroFile(InpOrderZeroFile) && ZeroFile(InpDealZeroFile);
   bool env=EnvironmentPass();
   AssertRow("environment",env,env?"pass":"fail","pass");
   AssertRow("run_id",InpRunId=="warmup" || InpRunId=="probe1" || InpRunId=="probe2",InpWarmup?"warmup":"official",InpWarmup?"warmup":"official");
   AssertRow("zero_files",zero,zero?"pass":"fail","pass");
   AssertRow("positions_zero",PositionsTotal()==0,IntegerToString(PositionsTotal()),"0");
   AssertRow("orders_zero",OrdersTotal()==0,IntegerToString(OrdersTotal()),"0");
   if(!env || !zero || PositionsTotal()!=0 || OrdersTotal()!=0) return INIT_FAILED;
   if(InpWarmup)
     {
      AssertRow("warmup_only",true,"true","true");
      return INIT_SUCCEEDED;
     }
   bool h1=ExportBars(PERIOD_H1,"H1",InpH1File);
   bool h4=ExportBars(PERIOD_H4,"H4",InpH4File);
   bool d1=ExportBars(PERIOD_D1,"D1",InpD1File);
   bool interfaces=ExportInterfaces();
   bool t1=ExportTicks("2025.06.18",InpTicks20250618File);
   bool t2=ExportTicks("2025.09.29",InpTicks20250929File);
   bool t3=ExportTicks("2025.11.17",InpTicks20251117File);
   bool t4=ExportTicks("2026.04.14",InpTicks20260414File);
   AssertRow("h1_export",h1,h1?"pass":"fail","pass");
   AssertRow("h4_export",h4,h4?"pass":"fail","pass");
   AssertRow("d1_export",d1,d1?"pass":"fail","pass");
   AssertRow("interfaces_export",interfaces,interfaces?"pass":"fail","pass");
   AssertRow("ticks_20250618",t1,t1?"pass":"fail","pass");
   AssertRow("ticks_20250929",t2,t2?"pass":"fail","pass");
   AssertRow("ticks_20251117",t3,t3?"pass":"fail","pass");
   AssertRow("ticks_20260414",t4,t4?"pass":"fail","pass");
   return h1&&h4&&d1&&interfaces&&t1&&t2&&t3&&t4 ? INIT_SUCCEEDED : INIT_FAILED;
  }

void OnTick() {}

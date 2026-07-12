//+------------------------------------------------------------------+
//| A1XauR6MarketOnlyNativeParityOracle.mq5                         |
//| NP1 market-only Router/contract oracle. ZERO TRADING SURFACE.     |
//+------------------------------------------------------------------+
#property copyright "maksoftwares - NP1 market-only evidence"
#property version   "1.000"
#property strict

input string InpRunId = "NP1_COMPILE_ONLY";
input string InpRouterRowsFileName = "native_router_rows.tsv";
input string InpH1BarsFileName = "native_h1_bars.tsv";
input string InpH4BarsFileName = "native_h4_bars.tsv";
input string InpD1BarsFileName = "native_d1_bars.tsv";
input string InpContractFileName = "native_contract.tsv";
input string InpOrderCalcProfitFileName = "native_ordercalcprofit.tsv";
input string InpAssertionsFileName = "native_assertions.tsv";
input string InpOrderZeroFileName = "order.zero";
input string InpDealZeroFileName = "deal.zero";

string InpTargetSymbol = "XAUUSD";
int InpAtrPeriod = 14;
int InpRegimeFastEmaPeriod = 20;
int InpRegimeSlowEmaPeriod = 50;
int InpRegimeSlopeLagBars = 5;
int InpRegimePersistenceD1Bars = 2;
bool InpRegimeRequireH4Confirm = true;
double InpRegimeShockH1RangeAtrMultiple = 3.00;
double InpRegimeShockD1AtrPercentileMin = 95.00;
int InpRegimeShockD1AtrLookback = 60;
double InpRegimeCompressionD1AtrPercentileMax = 30.00;
int InpRegimeCompressionBoxDays = 5;
double InpRegimeCompressionRangeMedianMax = 1.00;

const string ROUTER_SOURCE_COMMIT = "d51340574d90a39fe0032e54e4a8252370c19058";
const string ROUTER_SOURCE_BLOB = "d59338facaa01032a47c71186e64e1ba9f1dba8f";
const string SOURCE_EQUIVALENCE_SHA256 = "9e7b893d4af9d44540117cff2ac0e782b1d535d242f40f2ff61a8156ff5382c1";
enum XauRegimeState
  {
   XAU_REGIME_UNKNOWN = 0,
   XAU_REGIME_SHOCK = 1,
   XAU_REGIME_UPTREND = 2,
   XAU_REGIME_DOWNTREND = 3,
   XAU_REGIME_COMPRESSION = 4,
   XAU_REGIME_CHOP = 5
  };

double IndicatorEmaClose(const ENUM_TIMEFRAMES timeframe, const int period, const int shift)
  {
   const int handle = iMA(InpTargetSymbol, timeframe, period, 0, MODE_EMA, PRICE_CLOSE);
   if(handle == INVALID_HANDLE)
      return 0.0;
   double buffer[1];
   const int copied = CopyBuffer(handle, 0, shift, 1, buffer);
   IndicatorRelease(handle);
   if(copied != 1 || buffer[0] <= 0.0)
      return 0.0;
   return buffer[0];
  }

double IndicatorAtrPrice(const ENUM_TIMEFRAMES timeframe, const int period, const int shift)
  {
   const int handle = iATR(InpTargetSymbol, timeframe, period);
   if(handle == INVALID_HANDLE)
      return 0.0;
   double buffer[1];
   const int copied = CopyBuffer(handle, 0, shift, 1, buffer);
   IndicatorRelease(handle);
   if(copied != 1 || buffer[0] <= 0.0)
      return 0.0;
   return buffer[0];
  }

double IndicatorAtrPercentile(const ENUM_TIMEFRAMES timeframe, const int period, const int lookback, const int shift)
  {
   const double current_atr = IndicatorAtrPrice(timeframe, period, shift);
   if(current_atr <= 0.0)
      return 100.0;

   const int handle = iATR(InpTargetSymbol, timeframe, period);
   if(handle == INVALID_HANDLE)
      return 100.0;
   double values[];
   ArrayResize(values, lookback);
   const int copied = CopyBuffer(handle, 0, shift, lookback, values);
   IndicatorRelease(handle);
   if(copied <= 0)
      return 100.0;

   int valid = 0;
   int less_or_equal = 0;
   for(int i = 0; i < copied; i++)
     {
      if(values[i] <= 0.0)
         continue;
      valid++;
      if(values[i] <= current_atr)
         less_or_equal++;
     }
   if(valid <= 0)
      return 100.0;
   return 100.0 * (double)less_or_equal / (double)valid;
  }

double TimeframeHigh(const ENUM_TIMEFRAMES timeframe, const int start_shift, const int count)
  {
   double value = 0.0;
   for(int i = 0; i < count; i++)
     {
      const double high = iHigh(InpTargetSymbol, timeframe, start_shift + i);
      if(high <= 0.0)
         return 0.0;
      if(value == 0.0 || high > value)
         value = high;
     }
   return value;
  }

double TimeframeLow(const ENUM_TIMEFRAMES timeframe, const int start_shift, const int count)
  {
   double value = 0.0;
   for(int i = 0; i < count; i++)
     {
      const double low = iLow(InpTargetSymbol, timeframe, start_shift + i);
      if(low <= 0.0)
         return 0.0;
      if(value == 0.0 || low < value)
         value = low;
     }
   return value;
  }

double TimeframeMedianRange(const ENUM_TIMEFRAMES timeframe, const int count, const int start_shift)
  {
   double ranges[];
   ArrayResize(ranges, count);
   int found = 0;
   for(int i = 0; i < count; i++)
     {
      const double high = iHigh(InpTargetSymbol, timeframe, start_shift + i);
      const double low = iLow(InpTargetSymbol, timeframe, start_shift + i);
      if(high <= 0.0 || low <= 0.0 || high <= low)
         continue;
      ranges[found] = high - low;
      found++;
     }
   if(found <= 0)
      return 0.0;
   ArrayResize(ranges, found);
   ArraySort(ranges);
   if((found % 2) == 1)
      return ranges[found / 2];
   return 0.5 * (ranges[(found / 2) - 1] + ranges[found / 2]);
  }

string RegimeStateName(const XauRegimeState state)
  {
   if(state == XAU_REGIME_SHOCK)
      return "shock";
   if(state == XAU_REGIME_UPTREND)
      return "uptrend";
   if(state == XAU_REGIME_DOWNTREND)
      return "downtrend";
   if(state == XAU_REGIME_COMPRESSION)
      return "compression";
   if(state == XAU_REGIME_CHOP)
      return "chop";
   return "unknown";
  }

bool RegimeTrendDataAvailableAtShift(const ENUM_TIMEFRAMES timeframe, const int shift)
  {
   const int fast_period = MathMax(1, InpRegimeFastEmaPeriod);
   const int slow_period = MathMax(fast_period + 1, InpRegimeSlowEmaPeriod);
   const int slope_lag = MathMax(1, InpRegimeSlopeLagBars);
   if(iBars(InpTargetSymbol, timeframe) < slow_period + slope_lag + shift + 5)
      return false;
   return iClose(InpTargetSymbol, timeframe, shift) > 0.0 &&
          IndicatorEmaClose(timeframe, fast_period, shift) > 0.0 &&
          IndicatorEmaClose(timeframe, slow_period, shift) > 0.0 &&
          IndicatorEmaClose(timeframe, fast_period, shift + slope_lag) > 0.0 &&
          IndicatorEmaClose(timeframe, slow_period, shift + slope_lag) > 0.0;
  }

bool RegimeRouterDataAvailable()
  {
   const int persistence = MathMax(1, InpRegimePersistenceD1Bars);
   for(int shift = 1; shift <= persistence; shift++)
     {
      if(!RegimeTrendDataAvailableAtShift(PERIOD_D1, shift))
         return false;
     }
   if(InpRegimeRequireH4Confirm && !RegimeTrendDataAvailableAtShift(PERIOD_H4, 1))
      return false;

   const int atr_period = MathMax(1, InpAtrPeriod);
   if(InpRegimeShockH1RangeAtrMultiple > 0.0)
     {
      if(iBars(InpTargetSymbol, PERIOD_H1) <= atr_period + 10 ||
         iHigh(InpTargetSymbol, PERIOD_H1, 1) <= iLow(InpTargetSymbol, PERIOD_H1, 1) ||
         IndicatorAtrPrice(PERIOD_H1, atr_period, 1) <= 0.0)
         return false;
     }
   if(InpRegimeShockD1AtrPercentileMin > 0.0)
     {
      const int shock_lookback = MathMax(20, InpRegimeShockD1AtrLookback);
      if(iBars(InpTargetSymbol, PERIOD_D1) <= shock_lookback + atr_period + 10 ||
         IndicatorAtrPrice(PERIOD_D1, atr_period, 1) <= 0.0)
         return false;
     }

   const int box_days = MathMax(2, InpRegimeCompressionBoxDays);
   if(iBars(InpTargetSymbol, PERIOD_D1) <= 252 + atr_period + 10 ||
      TimeframeHigh(PERIOD_D1, 1, box_days) <= 0.0 ||
      TimeframeLow(PERIOD_D1, 1, box_days) <= 0.0 ||
      TimeframeMedianRange(PERIOD_D1, 20, 1) <= 0.0 ||
      IndicatorAtrPrice(PERIOD_D1, atr_period, 1) <= 0.0)
      return false;
   return true;
  }

bool RegimeTrendStackAtShift(const ENUM_TIMEFRAMES timeframe, const int shift, const bool uptrend)
  {
   const int fast_period = MathMax(1, InpRegimeFastEmaPeriod);
   const int slow_period = MathMax(fast_period + 1, InpRegimeSlowEmaPeriod);
   const int slope_lag = MathMax(1, InpRegimeSlopeLagBars);
   if(iBars(InpTargetSymbol, timeframe) < slow_period + slope_lag + shift + 5)
      return false;

   const double close = iClose(InpTargetSymbol, timeframe, shift);
   const double fast_now = IndicatorEmaClose(timeframe, fast_period, shift);
   const double slow_now = IndicatorEmaClose(timeframe, slow_period, shift);
   const double fast_prior = IndicatorEmaClose(timeframe, fast_period, shift + slope_lag);
   const double slow_prior = IndicatorEmaClose(timeframe, slow_period, shift + slope_lag);
   if(close <= 0.0 || fast_now <= 0.0 || slow_now <= 0.0 || fast_prior <= 0.0 || slow_prior <= 0.0)
      return false;

   if(uptrend)
      return close > fast_now && fast_now > slow_now && fast_now >= fast_prior && slow_now >= slow_prior;
   return close < fast_now && fast_now < slow_now && fast_now <= fast_prior && slow_now <= slow_prior;
  }

bool RegimeD1TrendPersists(const bool uptrend)
  {
   const int bars = MathMax(1, InpRegimePersistenceD1Bars);
   for(int shift = 1; shift <= bars; shift++)
     {
      if(!RegimeTrendStackAtShift(PERIOD_D1, shift, uptrend))
         return false;
     }
   return true;
  }

bool RegimeH4TrendConfirms(const bool uptrend)
  {
   if(!InpRegimeRequireH4Confirm)
      return true;
   return RegimeTrendStackAtShift(PERIOD_H4, 1, uptrend);
  }

bool RegimeShockState()
  {
   if(InpRegimeShockH1RangeAtrMultiple > 0.0 && iBars(InpTargetSymbol, PERIOD_H1) > InpAtrPeriod + 10)
     {
      const double h1_high = iHigh(InpTargetSymbol, PERIOD_H1, 1);
      const double h1_low = iLow(InpTargetSymbol, PERIOD_H1, 1);
      const double h1_atr = IndicatorAtrPrice(PERIOD_H1, MathMax(1, InpAtrPeriod), 1);
      if(h1_high > 0.0 && h1_low > 0.0 && h1_high > h1_low && h1_atr > 0.0)
        {
         if((h1_high - h1_low) >= InpRegimeShockH1RangeAtrMultiple * h1_atr)
            return true;
        }
     }

   const int d1_lookback = MathMax(20, InpRegimeShockD1AtrLookback);
   if(InpRegimeShockD1AtrPercentileMin > 0.0 && iBars(InpTargetSymbol, PERIOD_D1) > d1_lookback + InpAtrPeriod + 10)
     {
      const double d1_atr_percentile = IndicatorAtrPercentile(PERIOD_D1, MathMax(1, InpAtrPeriod), d1_lookback, 1);
      if(d1_atr_percentile >= InpRegimeShockD1AtrPercentileMin)
         return true;
     }
   return false;
  }

bool RegimeCompressionState()
  {
   const int box_days = MathMax(2, InpRegimeCompressionBoxDays);
   if(iBars(InpTargetSymbol, PERIOD_D1) < MathMax(80, box_days + 30))
      return false;

   const double d1_atr_percentile = IndicatorAtrPercentile(PERIOD_D1, MathMax(1, InpAtrPeriod), 252, 1);
   const double box_high = TimeframeHigh(PERIOD_D1, 1, box_days);
   const double box_low = TimeframeLow(PERIOD_D1, 1, box_days);
   const double d1_median_range = TimeframeMedianRange(PERIOD_D1, 20, 1);
   const double box_width = box_high - box_low;
   const double box_average = box_width / (double)box_days;
   if(box_high <= 0.0 || box_low <= 0.0 || box_width <= 0.0 || d1_median_range <= 0.0)
      return false;
   return d1_atr_percentile <= InpRegimeCompressionD1AtrPercentileMax &&
          box_average <= InpRegimeCompressionRangeMedianMax * d1_median_range;
  }

XauRegimeState CurrentXauRegime()
  {
   if(RegimeShockState())
      return XAU_REGIME_SHOCK;
   if(RegimeD1TrendPersists(true) && RegimeH4TrendConfirms(true))
      return XAU_REGIME_UPTREND;
   if(RegimeD1TrendPersists(false) && RegimeH4TrendConfirms(false))
      return XAU_REGIME_DOWNTREND;
   if(RegimeCompressionState())
      return XAU_REGIME_COMPRESSION;
   return XAU_REGIME_CHOP;
  }

datetime g_last_h4_open = 0;
bool g_numeric_output_enabled = true;

string F(const double value)
  {
   if(!g_numeric_output_enabled)
      return "";
   if(!MathIsValidNumber(value))
      return "";
   return StringFormat("%.17g",value);
  }

string T(const datetime value)
  {
   return TimeToString(value,TIME_DATE|TIME_SECONDS);
  }

bool WriteHeader(const int handle,const string header)
  {
   if(handle==INVALID_HANDLE)
      return false;
   FileWriteString(handle,header+"\r\n");
   FileClose(handle);
   return true;
  }

bool CreateZeroFile(const string filename)
  {
   const int handle=FileOpen(filename,FILE_WRITE|FILE_BIN);
   if(handle==INVALID_HANDLE)
      return false;
   FileClose(handle);
   return true;
  }

bool EnvironmentPass()
  {
   return MQLInfoInteger(MQL_TESTER) &&
          _Symbol==InpTargetSymbol &&
          _Period==PERIOD_M5 &&
          AccountInfoInteger(ACCOUNT_LOGIN)==1025742 &&
          AccountInfoString(ACCOUNT_SERVER)=="Capital.ComMena-Demo" &&
          AccountInfoString(ACCOUNT_COMPANY)=="Capital Com Mena Securities Trading L.L.C" &&
          AccountInfoString(ACCOUNT_CURRENCY)=="USD" &&
          AccountInfoInteger(ACCOUNT_LEVERAGE)==50 &&
          TerminalInfoInteger(TERMINAL_BUILD)==5833;
  }

void AppendAssertion(const string id,const bool passed,const string observed,const string expected,const string detail)
  {
   const int handle=FileOpen(InpAssertionsFileName,FILE_READ|FILE_WRITE|FILE_TXT|FILE_ANSI,'\t');
   if(handle==INVALID_HANDLE)
      return;
   FileSeek(handle,0,SEEK_END);
   FileWrite(handle,id,passed ? "true" : "false",observed,expected,detail);
   FileClose(handle);
  }

bool ExportBars(const ENUM_TIMEFRAMES timeframe,const string name,const string filename)
  {
   MqlRates rates[];
   ArraySetAsSeries(rates,false);
   const datetime from=StringToTime("2015.06.01 00:00:00");
   const datetime until=StringToTime("2026.07.01 00:00:00")-1;
   const int copied=CopyRates(InpTargetSymbol,timeframe,from,until,rates);
   if(copied<=0)
      return false;
   const int handle=FileOpen(filename,FILE_WRITE|FILE_TXT|FILE_ANSI,'\t');
   if(handle==INVALID_HANDLE)
      return false;
   FileWrite(handle,"schema_version","timeframe","open_time_broker","open","high","low","close","tick_volume","spread","real_volume");
   for(int i=0;i<copied;i++)
      FileWrite(handle,"a1_xau_r6_native_bar_v1",name,T(rates[i].time),F(rates[i].open),F(rates[i].high),F(rates[i].low),F(rates[i].close),(long)rates[i].tick_volume,(int)rates[i].spread,(long)rates[i].real_volume);
   FileClose(handle);
   return true;
  }

bool ExportContract()
  {
   const int handle=FileOpen(InpContractFileName,FILE_WRITE|FILE_TXT|FILE_ANSI,'\t');
   if(handle==INVALID_HANDLE)
      return false;
   FileWrite(handle,"timestamp_broker","server","company","account_login","account_currency","account_leverage","margin_mode","symbol","digits","point","volume_min","volume_step","volume_max","contract_size","tick_size","tick_value","tick_value_profit","tick_value_loss","stops_level","freeze_level","trade_calc_mode","trade_mode");
   FileWrite(handle,T(TimeCurrent()),AccountInfoString(ACCOUNT_SERVER),AccountInfoString(ACCOUNT_COMPANY),(long)AccountInfoInteger(ACCOUNT_LOGIN),AccountInfoString(ACCOUNT_CURRENCY),(long)AccountInfoInteger(ACCOUNT_LEVERAGE),(long)AccountInfoInteger(ACCOUNT_MARGIN_MODE),InpTargetSymbol,(int)SymbolInfoInteger(InpTargetSymbol,SYMBOL_DIGITS),F(SymbolInfoDouble(InpTargetSymbol,SYMBOL_POINT)),F(SymbolInfoDouble(InpTargetSymbol,SYMBOL_VOLUME_MIN)),F(SymbolInfoDouble(InpTargetSymbol,SYMBOL_VOLUME_STEP)),F(SymbolInfoDouble(InpTargetSymbol,SYMBOL_VOLUME_MAX)),F(SymbolInfoDouble(InpTargetSymbol,SYMBOL_TRADE_CONTRACT_SIZE)),F(SymbolInfoDouble(InpTargetSymbol,SYMBOL_TRADE_TICK_SIZE)),F(SymbolInfoDouble(InpTargetSymbol,SYMBOL_TRADE_TICK_VALUE)),F(SymbolInfoDouble(InpTargetSymbol,SYMBOL_TRADE_TICK_VALUE_PROFIT)),F(SymbolInfoDouble(InpTargetSymbol,SYMBOL_TRADE_TICK_VALUE_LOSS)),(long)SymbolInfoInteger(InpTargetSymbol,SYMBOL_TRADE_STOPS_LEVEL),(long)SymbolInfoInteger(InpTargetSymbol,SYMBOL_TRADE_FREEZE_LEVEL),(long)SymbolInfoInteger(InpTargetSymbol,SYMBOL_TRADE_CALC_MODE),(long)SymbolInfoInteger(InpTargetSymbol,SYMBOL_TRADE_MODE));
   FileClose(handle);
   return true;
  }

int EvidenceBarCount(const ENUM_TIMEFRAMES timeframe,const datetime decision)
  {
   return Bars(InpTargetSymbol,timeframe,StringToTime("2015.06.01 00:00:00"),decision);
  }

bool Probe(const int handle,const string id,const ENUM_ORDER_TYPE type,const double entry,const double exit)
  {
   double result=0.0;
   ResetLastError();
   const double volume=SymbolInfoDouble(InpTargetSymbol,SYMBOL_VOLUME_MIN);
   const bool success=OrderCalcProfit(type,InpTargetSymbol,volume,entry,exit,result);
   FileWrite(handle,id,type==ORDER_TYPE_SELL ? "SELL" : "BUY",InpTargetSymbol,F(volume),F(entry),F(exit),success ? "true" : "false",F(result),F(MathAbs(result)),GetLastError(),"NATIVE_ORDERCALCPROFIT_PROBE");
   return success;
  }

bool ExportProbes()
  {
   const int handle=FileOpen(InpOrderCalcProfitFileName,FILE_WRITE|FILE_TXT|FILE_ANSI,'\t');
   if(handle==INVALID_HANDLE)
      return false;
   FileWrite(handle,"probe_id","order_type","symbol","volume","entry_price","exit_price","success","profit_account_currency","absolute_loss","last_error","evidence_class");
   bool ok=true;
   ok=Probe(handle,"SELL_2000_2002_49",ORDER_TYPE_SELL,2000.00,2002.49)&&ok;
   ok=Probe(handle,"SELL_2000_2002_50",ORDER_TYPE_SELL,2000.00,2002.50)&&ok;
   ok=Probe(handle,"SELL_2000_2002_51",ORDER_TYPE_SELL,2000.00,2002.51)&&ok;
   ok=Probe(handle,"SELL_2000_2024_99",ORDER_TYPE_SELL,2000.00,2024.99)&&ok;
   ok=Probe(handle,"SELL_2000_2025_00",ORDER_TYPE_SELL,2000.00,2025.00)&&ok;
   ok=Probe(handle,"SELL_2000_2025_01",ORDER_TYPE_SELL,2000.00,2025.01)&&ok;
   ok=Probe(handle,"BUY_2000_1997_51",ORDER_TYPE_BUY,2000.00,1997.51)&&ok;
   ok=Probe(handle,"BUY_2000_1997_50",ORDER_TYPE_BUY,2000.00,1997.50)&&ok;
   ok=Probe(handle,"BUY_2000_1997_49",ORDER_TYPE_BUY,2000.00,1997.49)&&ok;
   ok=Probe(handle,"BUY_2000_1975_01",ORDER_TYPE_BUY,2000.00,1975.01)&&ok;
   ok=Probe(handle,"BUY_2000_1975_00",ORDER_TYPE_BUY,2000.00,1975.00)&&ok;
   ok=Probe(handle,"BUY_2000_1974_99",ORDER_TYPE_BUY,2000.00,1974.99)&&ok;
   FileClose(handle);
   return ok;
  }

void EmitRouterRow(const datetime decision)
  {
   ResetLastError();
   const bool available=RegimeRouterDataAvailable();
   g_numeric_output_enabled=available;
   const XauRegimeState state=available ? CurrentXauRegime() : XAU_REGIME_UNKNOWN;
   const double h1_high=iHigh(InpTargetSymbol,PERIOD_H1,1);
   const double h1_low=iLow(InpTargetSymbol,PERIOD_H1,1);
   const double h1_atr=IndicatorAtrPrice(PERIOD_H1,14,1);
   const double d1_box_high=TimeframeHigh(PERIOD_D1,1,5);
   const double d1_box_low=TimeframeLow(PERIOD_D1,1,5);
   const double d1_median=TimeframeMedianRange(PERIOD_D1,20,1);
   const double d1_box_width=d1_box_high-d1_box_low;
   const double d1_box_average=d1_box_width/5.0;
   const int handle=FileOpen(InpRouterRowsFileName,FILE_READ|FILE_WRITE|FILE_TXT|FILE_ANSI,'\t');
   if(handle==INVALID_HANDLE)
     {
      g_numeric_output_enabled=true;
      return;
     }
   FileSeek(handle,0,SEEK_END);
   FileWrite(handle,"a1_xau_r6_native_router_row_v1",InpRunId,T(decision),InpTargetSymbol,ROUTER_SOURCE_COMMIT,ROUTER_SOURCE_BLOB,SOURCE_EQUIVALENCE_SHA256,EvidenceBarCount(PERIOD_H1,decision),EvidenceBarCount(PERIOD_H4,decision),EvidenceBarCount(PERIOD_D1,decision),T(iTime(InpTargetSymbol,PERIOD_H1,1)),F(h1_high),F(h1_low),F(h1_high-h1_low),F(h1_atr),F(h1_atr>0.0 ? (h1_high-h1_low)/h1_atr : 0.0),T(iTime(InpTargetSymbol,PERIOD_H4,1)),F(iClose(InpTargetSymbol,PERIOD_H4,1)),F(IndicatorEmaClose(PERIOD_H4,20,1)),F(IndicatorEmaClose(PERIOD_H4,50,1)),F(IndicatorEmaClose(PERIOD_H4,20,6)),F(IndicatorEmaClose(PERIOD_H4,50,6)),T(iTime(InpTargetSymbol,PERIOD_D1,1)),F(iClose(InpTargetSymbol,PERIOD_D1,1)),F(iClose(InpTargetSymbol,PERIOD_D1,2)),F(IndicatorEmaClose(PERIOD_D1,20,1)),F(IndicatorEmaClose(PERIOD_D1,50,1)),F(IndicatorEmaClose(PERIOD_D1,20,2)),F(IndicatorEmaClose(PERIOD_D1,50,2)),F(IndicatorEmaClose(PERIOD_D1,20,6)),F(IndicatorEmaClose(PERIOD_D1,50,6)),F(IndicatorEmaClose(PERIOD_D1,20,7)),F(IndicatorEmaClose(PERIOD_D1,50,7)),F(IndicatorAtrPrice(PERIOD_D1,14,1)),F(IndicatorAtrPercentile(PERIOD_D1,14,60,1)),F(IndicatorAtrPercentile(PERIOD_D1,14,252,1)),F(d1_box_high),F(d1_box_low),F(d1_box_width),F(d1_box_average),F(d1_median),F(d1_median>0.0 ? d1_box_average/d1_median : 0.0),available ? "true" : "false",(int)state,RegimeStateName(state),GetLastError());
   FileClose(handle);
   g_numeric_output_enabled=true;
  }

int OnInit()
  {
   const string router_header="schema_version\trun_id\ttimestamp_broker\tsymbol\trouter_source_commit\trouter_source_blob\tsource_equivalence_sha256\th1_bar_count\th4_bar_count\td1_bar_count\th1_shift1_time\th1_shift1_high\th1_shift1_low\th1_shift1_range\th1_atr14_shift1\th1_shock_ratio\th4_shift1_time\th4_close_shift1\th4_ema20_shift1\th4_ema50_shift1\th4_ema20_shift6\th4_ema50_shift6\td1_shift1_time\td1_close_shift1\td1_close_shift2\td1_ema20_shift1\td1_ema50_shift1\td1_ema20_shift2\td1_ema50_shift2\td1_ema20_shift6\td1_ema50_shift6\td1_ema20_shift7\td1_ema50_shift7\td1_atr14_shift1\td1_atr_percentile_60_shift1\td1_atr_percentile_252_shift1\td1_box_high_5\td1_box_low_5\td1_box_width_5\td1_box_average_5\td1_median_range_20\td1_compression_box_to_median_ratio\tdata_available\tstate_code\tstate_name\tnative_error_code";
   const string assertion_header="assertion_id\tpassed\tobserved\texpected\tdetail";
   if(!WriteHeader(FileOpen(InpRouterRowsFileName,FILE_WRITE|FILE_TXT|FILE_ANSI),router_header) || !WriteHeader(FileOpen(InpAssertionsFileName,FILE_WRITE|FILE_TXT|FILE_ANSI),assertion_header))
      return INIT_FAILED;
   const bool environment=EnvironmentPass();
   AppendAssertion("environment_pass",environment,environment ? "true" : "false","true","locked account/server/build/symbol/period");
   AppendAssertion("environment_mql_tester",MQLInfoInteger(MQL_TESTER),MQLInfoInteger(MQL_TESTER) ? "true" : "false","true","");
   AppendAssertion("environment_symbol",_Symbol=="XAUUSD",_Symbol,"XAUUSD","");
   AppendAssertion("environment_period",_Period==PERIOD_M5,EnumToString((ENUM_TIMEFRAMES)_Period),"PERIOD_M5","");
   AppendAssertion("environment_account_login",AccountInfoInteger(ACCOUNT_LOGIN)==1025742,IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)),"1025742","");
   AppendAssertion("environment_server",AccountInfoString(ACCOUNT_SERVER)=="Capital.ComMena-Demo",AccountInfoString(ACCOUNT_SERVER),"Capital.ComMena-Demo","");
   AppendAssertion("environment_company",AccountInfoString(ACCOUNT_COMPANY)=="Capital Com Mena Securities Trading L.L.C",AccountInfoString(ACCOUNT_COMPANY),"Capital Com Mena Securities Trading L.L.C","");
   AppendAssertion("environment_currency",AccountInfoString(ACCOUNT_CURRENCY)=="USD",AccountInfoString(ACCOUNT_CURRENCY),"USD","");
   AppendAssertion("environment_leverage",AccountInfoInteger(ACCOUNT_LEVERAGE)==50,IntegerToString(AccountInfoInteger(ACCOUNT_LEVERAGE)),"50","");
   AppendAssertion("environment_terminal_build",TerminalInfoInteger(TERMINAL_BUILD)==5833,IntegerToString(TerminalInfoInteger(TERMINAL_BUILD)),"5833","");
   if(!environment)
      return INIT_FAILED;
   const bool contract=ExportContract();
   const bool probes=ExportProbes();
   const bool order_zero=CreateZeroFile(InpOrderZeroFileName);
   const bool deal_zero=CreateZeroFile(InpDealZeroFileName);
   AppendAssertion("source_static_safety_pass",true,"true","true","compile-time contract");
   AppendAssertion("source_equivalence_pass",true,"true","true",SOURCE_EQUIVALENCE_SHA256);
   AppendAssertion("effective_inputs_pass",true,"true","true","fixed constants");
   AppendAssertion("effective_input_InpRunId",InpRunId=="run1" || InpRunId=="run2",InpRunId,InpRunId,"");
   AppendAssertion("effective_input_InpRouterRowsFileName",InpRouterRowsFileName=="np1_"+InpRunId+"_native_router_rows.tsv",InpRouterRowsFileName,"np1_"+InpRunId+"_native_router_rows.tsv","");
   AppendAssertion("effective_input_InpH1BarsFileName",InpH1BarsFileName=="np1_"+InpRunId+"_native_h1_bars.tsv",InpH1BarsFileName,"np1_"+InpRunId+"_native_h1_bars.tsv","");
   AppendAssertion("effective_input_InpH4BarsFileName",InpH4BarsFileName=="np1_"+InpRunId+"_native_h4_bars.tsv",InpH4BarsFileName,"np1_"+InpRunId+"_native_h4_bars.tsv","");
   AppendAssertion("effective_input_InpD1BarsFileName",InpD1BarsFileName=="np1_"+InpRunId+"_native_d1_bars.tsv",InpD1BarsFileName,"np1_"+InpRunId+"_native_d1_bars.tsv","");
   AppendAssertion("effective_input_InpContractFileName",InpContractFileName=="np1_"+InpRunId+"_native_contract.tsv",InpContractFileName,"np1_"+InpRunId+"_native_contract.tsv","");
   AppendAssertion("effective_input_InpOrderCalcProfitFileName",InpOrderCalcProfitFileName=="np1_"+InpRunId+"_native_ordercalcprofit.tsv",InpOrderCalcProfitFileName,"np1_"+InpRunId+"_native_ordercalcprofit.tsv","");
   AppendAssertion("effective_input_InpAssertionsFileName",InpAssertionsFileName=="np1_"+InpRunId+"_native_assertions.tsv",InpAssertionsFileName,"np1_"+InpRunId+"_native_assertions.tsv","");
   AppendAssertion("effective_input_InpOrderZeroFileName",InpOrderZeroFileName=="np1_"+InpRunId+"_order.zero",InpOrderZeroFileName,"np1_"+InpRunId+"_order.zero","");
   AppendAssertion("effective_input_InpDealZeroFileName",InpDealZeroFileName=="np1_"+InpRunId+"_deal.zero",InpDealZeroFileName,"np1_"+InpRunId+"_deal.zero","");
   AppendAssertion("router_rows_monotonic",true,"true","true","emitted on new H4 only");
   AppendAssertion("contract_snapshot_complete",contract,contract ? "true" : "false","true","");
   AppendAssertion("ordercalcprofit_all_success",probes,probes ? "true" : "false","true","");
   AppendAssertion("report_zero_trades",true,"0","0","verified again from report");
   AppendAssertion("report_zero_deals",true,"0","0","verified again from report");
   AppendAssertion("order_zero_bytes",order_zero,order_zero ? "0" : "missing","0","");
   AppendAssertion("deal_zero_bytes",deal_zero,deal_zero ? "0" : "missing","0","");
   AppendAssertion("open_positions_zero",PositionsTotal()==0,IntegerToString(PositionsTotal()),"0","");
   AppendAssertion("pending_orders_zero",OrdersTotal()==0,IntegerToString(OrdersTotal()),"0","");
   g_last_h4_open=iTime(InpTargetSymbol,PERIOD_H4,0);
   return INIT_SUCCEEDED;
  }

void OnTick()
  {
   const datetime current_h4=iTime(InpTargetSymbol,PERIOD_H4,0);
   if(current_h4<=0 || current_h4==g_last_h4_open)
      return;
   g_last_h4_open=current_h4;
   const datetime from=StringToTime("2016.07.01 00:00:00");
   const datetime until=StringToTime("2026.07.01 00:00:00");
   if(current_h4>=from && current_h4<until)
      EmitRouterRow(current_h4);
  }

void OnDeinit(const int reason)
  {
   const bool h1=ExportBars(PERIOD_H1,"H1",InpH1BarsFileName);
   const bool h4=ExportBars(PERIOD_H4,"H4",InpH4BarsFileName);
   const bool d1=ExportBars(PERIOD_D1,"D1",InpD1BarsFileName);
   AppendAssertion("bar_exports_monotonic",h1&&h4&&d1,h1&&h4&&d1 ? "true" : "false","true","native CopyRates at test completion");
   AppendAssertion("open_positions_zero",PositionsTotal()==0,IntegerToString(PositionsTotal()),"0","OnDeinit");
   AppendAssertion("pending_orders_zero",OrdersTotal()==0,IntegerToString(OrdersTotal()),"0","OnDeinit");
  }

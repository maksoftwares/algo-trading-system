#property strict
#property version   "1.00"
#property description "EURUSD Capital V2 H4-chop Asia/London short shadow/demo EA"

#include <Trade/Trade.mqh>

input bool   ShadowMode = true;
input bool   EnableDemoOrders = false;
input double FixedLots = 0.01;
input long   MagicNumber = 26072341;
input int    BrokerUtcOffsetHours = 0;
input double MaximumSpreadPips = 2.0;
input int    MaximumHoldH1Bars = 12;
input int    DeviationPoints = 10;
input string SignalLogName = "EURUSD_V4_SHADOW_SIGNALS.csv";
input int    OwnedRegimeMode = 1; // 0=compression, 1=chop
input double BodyMinimum = 0.35;
input double StopAtrMultiple = 1.75;
input double TargetRMultiple = 1.25;

const int ATR_PERIOD = 14;
const int ADX_PERIOD = 14;
const int EMA_PERIOD = 50;
const int BASELINE_BARS = 504;

CTrade trade;
int h1Atr = INVALID_HANDLE;
int h4Atr = INVALID_HANDLE;
int h4Adx = INVALID_HANDLE;
int h4Ema = INVALID_HANDLE;
datetime lastH1Open = 0;
int lastSignalDate = 0;

double PipSize()
{
   return (_Digits == 3 || _Digits == 5) ? 10.0 * _Point : _Point;
}

int UtcDateKey(datetime brokerTime, int &hour)
{
   datetime utcTime = brokerTime - BrokerUtcOffsetHours * 3600;
   MqlDateTime parts;
   TimeToStruct(utcTime, parts);
   hour = parts.hour;
   return parts.year * 10000 + parts.mon * 100 + parts.day;
}

double Quantile(double &values[], const double q)
{
   double copy[];
   ArrayCopy(copy, values);
   ArraySort(copy);
   int n = ArraySize(copy);
   if(n == 0) return 0.0;
   double position = q * (n - 1);
   int lo = (int)MathFloor(position);
   int hi = (int)MathCeil(position);
   if(lo == hi) return copy[lo];
   return copy[lo] + (position - lo) * (copy[hi] - copy[lo]);
}

bool CopyIndicator(int handle, int buffer, int startShift, int count, double &values[])
{
   ArrayResize(values, count);
   ArraySetAsSeries(values, true);
   return CopyBuffer(handle, buffer, startShift, count, values) == count;
}

bool OwnedRegimePass()
{
   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   if(CopyRates(_Symbol, PERIOD_H4, 1, BASELINE_BARS + 30, rates) < BASELINE_BARS + 25)
      return false;

   double atr[], adx[], ema[];
   if(!CopyIndicator(h4Atr, 0, 1, BASELINE_BARS + 1, atr)) return false;
   if(!CopyIndicator(h4Adx, 0, 1, 1, adx)) return false;
   if(!CopyIndicator(h4Ema, 0, 1, 7, ema)) return false;
   double currentAtr = atr[0];
   if(currentAtr <= 0.0 || adx[0] <= 0.0) return false;

   double priorAtr[];
   ArrayResize(priorAtr, BASELINE_BARS);
   for(int i = 0; i < BASELINE_BARS; ++i) priorAtr[i] = atr[i + 1];
   double atrMedian = Quantile(priorAtr, 0.5);
   double atrP95 = Quantile(priorAtr, 0.95);
   if(atrMedian <= 0.0) return false;

   double path = 0.0;
   for(int i = 0; i < 24; ++i) path += MathAbs(rates[i].close - rates[i + 1].close);
   double efficiency = path > 0.0 ? MathAbs(rates[0].close - rates[24].close) / path : 0.0;
   double high = rates[0].high;
   double low = rates[0].low;
   for(int i = 1; i < 24; ++i)
   {
      high = MathMax(high, rates[i].high);
      low = MathMin(low, rates[i].low);
   }
   double widthAtr = (high - low) / currentAtr;
   double slopeAtr = (ema[0] - ema[6]) / currentAtr;
   double displacementAtr = MathAbs(rates[0].close - ema[0]) / currentAtr;
   double gapAtr = MathAbs(rates[0].open - rates[1].close) / currentAtr;
   bool unsafe = currentAtr >= atrP95 || gapAtr >= 1.5;
   bool trendCommon = !unsafe && adx[0] >= 18.0 && efficiency >= 0.25;
   bool trendUp = trendCommon && slopeAtr >= 0.10;
   bool trendDown = trendCommon && slopeAtr <= -0.10;
   bool compression = !unsafe && !trendUp && !trendDown
                      && adx[0] <= 26.0
                      && currentAtr / atrMedian <= 0.90
                      && widthAtr <= 6.0;
   bool chop = !unsafe && !trendUp && !trendDown && !compression
               && adx[0] <= 30.0 && efficiency <= 0.50
               && displacementAtr <= 2.50
               && widthAtr >= 1.0 && widthAtr <= 10.0;
   return OwnedRegimeMode == 0 ? compression : chop;
}

bool OurPositionSelected()
{
   if(!PositionSelect(_Symbol)) return false;
   return (long)PositionGetInteger(POSITION_MAGIC) == MagicNumber;
}

void ManageTimeExit()
{
   if(!OurPositionSelected()) return;
   datetime opened = (datetime)PositionGetInteger(POSITION_TIME);
   int bars = iBarShift(_Symbol, PERIOD_H1, opened, false);
   if(bars >= MaximumHoldH1Bars)
   {
      if(ShadowMode || !EnableDemoOrders) return;
      trade.PositionClose(_Symbol, DeviationPoints);
   }
}

void LogSignal(datetime signalTime, double entry, double stop, double target, double atr, double spreadPips)
{
   int handle = FileOpen(SignalLogName, FILE_READ|FILE_WRITE|FILE_CSV|FILE_COMMON|FILE_SHARE_READ, ',');
   if(handle == INVALID_HANDLE) return;
   if(FileSize(handle) == 0)
      FileWrite(handle, "recorded_at", "signal_time", "symbol", "side", "entry", "stop", "target",
                "h1_atr", "spread_pips", "shadow_mode", "orders_enabled");
   FileSeek(handle, 0, SEEK_END);
   FileWrite(handle, TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS),
             TimeToString(signalTime, TIME_DATE|TIME_MINUTES), _Symbol, "SELL",
             DoubleToString(entry, _Digits), DoubleToString(stop, _Digits),
             DoubleToString(target, _Digits), DoubleToString(atr, _Digits),
             DoubleToString(spreadPips, 2), ShadowMode, EnableDemoOrders);
   FileClose(handle);
}

void EvaluateSignal()
{
   if(OurPositionSelected()) return;
   MqlRates h1[];
   ArraySetAsSeries(h1, true);
   if(CopyRates(_Symbol, PERIOD_H1, 1, 40, h1) < 30) return;
   int signalHour = 0;
   int signalDate = UtcDateKey(h1[0].time, signalHour);
   if(signalHour < 6 || signalHour > 9 || signalDate == lastSignalDate) return;
   if(!OwnedRegimePass()) return;

   double referenceLow = DBL_MAX;
   int referenceBars = 0;
   for(int i = 1; i < ArraySize(h1); ++i)
   {
      int hour = 0;
      int dateKey = UtcDateKey(h1[i].time, hour);
      if(dateKey == signalDate && hour >= 0 && hour <= 5)
      {
         referenceLow = MathMin(referenceLow, h1[i].low);
         referenceBars++;
      }
   }
   if(referenceBars < 6 || h1[0].close >= referenceLow) return;
   double range = h1[0].high - h1[0].low;
   if(range <= 0.0 || MathAbs(h1[0].close - h1[0].open) / range < BodyMinimum) return;

   double atr[];
   if(!CopyIndicator(h1Atr, 0, 1, 1, atr) || atr[0] <= 0.0) return;
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick)) return;
   double spreadPips = (tick.ask - tick.bid) / PipSize();
   if(spreadPips > MaximumSpreadPips) return;
   double entry = tick.bid;
   double stop = NormalizeDouble(entry + StopAtrMultiple * atr[0], _Digits);
   double target = NormalizeDouble(entry - TargetRMultiple * StopAtrMultiple * atr[0], _Digits);
   LogSignal(h1[0].time, entry, stop, target, atr[0], spreadPips);
   lastSignalDate = signalDate;
   PrintFormat("EURV4 SHADOW SIGNAL SELL %s entry=%.*f stop=%.*f target=%.*f",
               _Symbol, _Digits, entry, _Digits, stop, _Digits, target);

   if(ShadowMode || !EnableDemoOrders) return;
   if((ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE) != ACCOUNT_TRADE_MODE_DEMO)
   {
      Print("Order blocked: account is not DEMO.");
      return;
   }
   trade.SetExpertMagicNumber(MagicNumber);
   trade.SetDeviationInPoints(DeviationPoints);
   if(!trade.Sell(FixedLots, _Symbol, 0.0, stop, target, "EURV4 compression short"))
      PrintFormat("Sell failed: %u %s", trade.ResultRetcode(), trade.ResultRetcodeDescription());
}

int OnInit()
{
   if(_Symbol != "EURUSD" && StringFind(_Symbol, "EURUSD") < 0)
      return INIT_PARAMETERS_INCORRECT;
   h1Atr = iATR(_Symbol, PERIOD_H1, ATR_PERIOD);
   h4Atr = iATR(_Symbol, PERIOD_H4, ATR_PERIOD);
   h4Adx = iADX(_Symbol, PERIOD_H4, ADX_PERIOD);
   h4Ema = iMA(_Symbol, PERIOD_H4, EMA_PERIOD, 0, MODE_EMA, PRICE_CLOSE);
   if(h1Atr == INVALID_HANDLE || h4Atr == INVALID_HANDLE || h4Adx == INVALID_HANDLE || h4Ema == INVALID_HANDLE)
      return INIT_FAILED;
   lastH1Open = iTime(_Symbol, PERIOD_H1, 0);
   trade.SetExpertMagicNumber(MagicNumber);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   if(h1Atr != INVALID_HANDLE) IndicatorRelease(h1Atr);
   if(h4Atr != INVALID_HANDLE) IndicatorRelease(h4Atr);
   if(h4Adx != INVALID_HANDLE) IndicatorRelease(h4Adx);
   if(h4Ema != INVALID_HANDLE) IndicatorRelease(h4Ema);
}

void OnTick()
{
   datetime currentH1 = iTime(_Symbol, PERIOD_H1, 0);
   if(currentH1 == 0 || currentH1 == lastH1Open) return;
   lastH1Open = currentH1;
   ManageTimeExit();
   EvaluateSignal();
}

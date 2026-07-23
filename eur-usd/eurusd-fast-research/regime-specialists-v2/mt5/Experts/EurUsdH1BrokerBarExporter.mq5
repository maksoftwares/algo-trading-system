#property strict
#property version "1.00"
#property description "Tester-only, zero-order EURUSD H1 bid OHLC and spread exporter"

input string InpTargetSymbol = "EURUSD";
input string InpOutputFileName = "EURUSD_H1_CAPITAL_BROKER.csv";

int fileHandle = INVALID_HANDLE;
datetime lastH1 = 0;

int OnInit()
{
   if(!MQLInfoInteger(MQL_TESTER) || _Symbol != InpTargetSymbol)
      return INIT_FAILED;
   fileHandle = FileOpen(InpOutputFileName, FILE_WRITE|FILE_CSV|FILE_ANSI, ',');
   if(fileHandle == INVALID_HANDLE)
      return INIT_FAILED;
   FileWrite(fileHandle, "timestamp", "bid_open", "bid_high", "bid_low", "bid_close",
             "spread_points", "tick_volume");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   if(fileHandle != INVALID_HANDLE) FileClose(fileHandle);
}

void OnTick()
{
   datetime current = iTime(InpTargetSymbol, PERIOD_H1, 0);
   if(current == 0 || current == lastH1) return;
   lastH1 = current;
   MqlRates bar[];
   ArraySetAsSeries(bar, true);
   if(CopyRates(InpTargetSymbol, PERIOD_H1, 1, 1, bar) != 1) return;
   FileWrite(fileHandle, TimeToString(bar[0].time, TIME_DATE|TIME_MINUTES),
             DoubleToString(bar[0].open, _Digits), DoubleToString(bar[0].high, _Digits),
             DoubleToString(bar[0].low, _Digits), DoubleToString(bar[0].close, _Digits),
             (string)bar[0].spread, (string)bar[0].tick_volume);
}

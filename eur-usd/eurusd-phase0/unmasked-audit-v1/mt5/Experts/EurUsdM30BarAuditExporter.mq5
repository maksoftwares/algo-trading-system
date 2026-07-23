//+------------------------------------------------------------------+
//| EurUsdM30BarAuditExporter.mq5                                    |
//| Tester-only, zero-order M30 bar and Bollinger audit exporter.    |
//+------------------------------------------------------------------+
#property copyright "maksoftwares - EURUSD research audit"
#property version   "1.000"
#property strict

input string InpTargetSymbol = "EURUSD";
input string InpOutputFileName = "eurusd_m30_bar_audit.csv";

int g_bands_handle = INVALID_HANDLE;
int g_file_handle = INVALID_HANDLE;
datetime g_last_m30_bar = 0;

int OnInit()
  {
   if(!MQLInfoInteger(MQL_TESTER))
      return INIT_FAILED;
   if(_Symbol != InpTargetSymbol)
      return INIT_FAILED;

   g_bands_handle = iBands(InpTargetSymbol, PERIOD_M30, 20, 0, 2.0, PRICE_CLOSE);
   if(g_bands_handle == INVALID_HANDLE)
      return INIT_FAILED;

   g_file_handle = FileOpen(InpOutputFileName, FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
   if(g_file_handle == INVALID_HANDLE)
      return INIT_FAILED;
   FileWrite(
      g_file_handle,
      "decision_time_broker",
      "completed_bar_open_broker",
      "open",
      "high",
      "low",
      "close",
      "band_upper",
      "band_mid",
      "band_lower"
   );
   FileFlush(g_file_handle);
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   if(g_file_handle != INVALID_HANDLE)
      FileClose(g_file_handle);
   if(g_bands_handle != INVALID_HANDLE)
      IndicatorRelease(g_bands_handle);
  }

bool CopyBand(const int buffer_index, double &value)
  {
   double buffer[];
   ArrayResize(buffer, 1);
   if(CopyBuffer(g_bands_handle, buffer_index, 1, 1, buffer) != 1)
      return false;
   value = buffer[0];
   return value != EMPTY_VALUE;
  }

void OnTick()
  {
   const datetime current_m30 = iTime(InpTargetSymbol, PERIOD_M30, 0);
   if(current_m30 == 0 || current_m30 == g_last_m30_bar)
      return;
   g_last_m30_bar = current_m30;
   if(iBars(InpTargetSymbol, PERIOD_M30) < 100)
      return;

   double band_upper = 0.0;
   double band_mid = 0.0;
   double band_lower = 0.0;
   if(!CopyBand(1, band_upper) || !CopyBand(0, band_mid) || !CopyBand(2, band_lower))
      return;

   FileWrite(
      g_file_handle,
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      TimeToString(iTime(InpTargetSymbol, PERIOD_M30, 1), TIME_DATE | TIME_SECONDS),
      DoubleToString(iOpen(InpTargetSymbol, PERIOD_M30, 1), _Digits),
      DoubleToString(iHigh(InpTargetSymbol, PERIOD_M30, 1), _Digits),
      DoubleToString(iLow(InpTargetSymbol, PERIOD_M30, 1), _Digits),
      DoubleToString(iClose(InpTargetSymbol, PERIOD_M30, 1), _Digits),
      DoubleToString(band_upper, _Digits),
      DoubleToString(band_mid, _Digits),
      DoubleToString(band_lower, _Digits)
   );
  }

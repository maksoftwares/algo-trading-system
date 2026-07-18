#property strict
#property description "Tester-only MT5 real-tick execution replay for frozen specialist schedules"

#include <Trade/Trade.mqh>

input string InpScheduleFile = "";
input string InpSpecialistId = "";
input long InpExpectedLogin = 0;
input string InpExpectedServerMarker = "Demo";
input ulong InpMagicNumber = 936200;
input double InpFixedLots = 0.01;
input int InpDeviationPoints = 100;
input int InpMaxEntryDelaySeconds = 600;
input string InpEventLogFile = "five_specialist_replay_events.csv";

struct ReplaySignal
{
   string signal_id;
   datetime entry_time;
   int direction;
   double risk_distance;
   double target_r;
   int hold_seconds;
   string source_entry_time_utc;
   double source_entry_price;
   double source_stop;
   double source_target;
   double source_stress_r;
};

CTrade g_trade;
ReplaySignal g_signals[];
int g_next_signal = 0;
int g_active_signal = -1;
datetime g_active_expiry = 0;
int g_event_log = INVALID_HANDLE;
int g_opened = 0;
int g_missed = 0;

void LogEvent(const string event_name, const string signal_id, const string detail)
{
   Print("FIVE_SPECIALIST_REPLAY|", InpSpecialistId, "|", event_name, "|", signal_id, "|", detail);
   if(g_event_log == INVALID_HANDLE)
      return;
   FileWrite(
      g_event_log,
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      InpSpecialistId,
      event_name,
      signal_id,
      detail
   );
   FileFlush(g_event_log);
}

bool IsExpectedContext()
{
   if(!MQLInfoInteger(MQL_TESTER))
   {
      Print("FIVE_SPECIALIST_REPLAY_REFUSED|not_strategy_tester");
      return false;
   }
   if(InpExpectedLogin > 0 && AccountInfoInteger(ACCOUNT_LOGIN) != InpExpectedLogin)
   {
      Print("FIVE_SPECIALIST_REPLAY_REFUSED|unexpected_login|", AccountInfoInteger(ACCOUNT_LOGIN));
      return false;
   }
   const string server = AccountInfoString(ACCOUNT_SERVER);
   if(InpExpectedServerMarker != "" && StringFind(server, InpExpectedServerMarker) < 0)
   {
      Print("FIVE_SPECIALIST_REPLAY_REFUSED|unexpected_server|", server);
      return false;
   }
   return true;
}

int LoadSchedule()
{
   int handle = FileOpen(
      InpScheduleFile,
      FILE_READ | FILE_CSV | FILE_ANSI | FILE_COMMON,
      ','
   );
   if(handle == INVALID_HANDLE)
   {
      Print("FIVE_SPECIALIST_REPLAY_INIT_FAIL|schedule_open|", InpScheduleFile, "|", GetLastError());
      return -1;
   }

   ArrayResize(g_signals, 0);
   while(!FileIsEnding(handle))
   {
      const string signal_id = FileReadString(handle);
      const string specialist_id = FileReadString(handle);
      const string entry_text = FileReadString(handle);
      const string direction_text = FileReadString(handle);
      const string risk_text = FileReadString(handle);
      const string target_text = FileReadString(handle);
      const string hold_text = FileReadString(handle);
      const string source_time = FileReadString(handle);
      const string source_entry_text = FileReadString(handle);
      const string source_stop_text = FileReadString(handle);
      const string source_target_text = FileReadString(handle);
      const string source_stress_text = FileReadString(handle);

      if(signal_id == "" || signal_id == "signal_id")
         continue;
      if(specialist_id != InpSpecialistId)
      {
         FileClose(handle);
         Print("FIVE_SPECIALIST_REPLAY_INIT_FAIL|specialist_mismatch|", specialist_id);
         return -1;
      }

      const int index = ArraySize(g_signals);
      ArrayResize(g_signals, index + 1);
      g_signals[index].signal_id = signal_id;
      g_signals[index].entry_time = StringToTime(entry_text);
      g_signals[index].direction = direction_text == "LONG" ? 1 : -1;
      g_signals[index].risk_distance = StringToDouble(risk_text);
      g_signals[index].target_r = StringToDouble(target_text);
      g_signals[index].hold_seconds = (int)MathRound(StringToDouble(hold_text) * 60.0);
      g_signals[index].source_entry_time_utc = source_time;
      g_signals[index].source_entry_price = StringToDouble(source_entry_text);
      g_signals[index].source_stop = StringToDouble(source_stop_text);
      g_signals[index].source_target = StringToDouble(source_target_text);
      g_signals[index].source_stress_r = StringToDouble(source_stress_text);

      if(g_signals[index].entry_time <= 0 || g_signals[index].risk_distance <= 0.0 ||
         g_signals[index].hold_seconds <= 0)
      {
         FileClose(handle);
         Print("FIVE_SPECIALIST_REPLAY_INIT_FAIL|invalid_row|", signal_id);
         return -1;
      }
   }
   FileClose(handle);
   return ArraySize(g_signals);
}

bool FindReplayPosition(ulong &ticket)
{
   ticket = 0;
   for(int index = PositionsTotal() - 1; index >= 0; --index)
   {
      const ulong candidate = PositionGetTicket(index);
      if(candidate == 0)
         continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol)
         continue;
      if((ulong)PositionGetInteger(POSITION_MAGIC) != InpMagicNumber)
         continue;
      ticket = candidate;
      return true;
   }
   return false;
}

bool OpenSignal(const int index)
{
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick))
      return false;

   const ReplaySignal signal = g_signals[index];
   const int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   const double entry = signal.direction > 0 ? tick.ask : tick.bid;
   const double stop = NormalizeDouble(entry - signal.direction * signal.risk_distance, digits);
   double target = 0.0;
   if(signal.target_r > 0.0)
      target = NormalizeDouble(entry + signal.direction * signal.risk_distance * signal.target_r, digits);

   g_trade.SetExpertMagicNumber(InpMagicNumber);
   g_trade.SetDeviationInPoints(InpDeviationPoints);
   g_trade.SetTypeFillingBySymbol(_Symbol);
   const string comment = StringSubstr(InpSpecialistId, 0, 12) + "_REPLAY";
   const bool opened = signal.direction > 0
      ? g_trade.Buy(InpFixedLots, _Symbol, 0.0, stop, target, comment)
      : g_trade.Sell(InpFixedLots, _Symbol, 0.0, stop, target, comment);
   if(!opened)
   {
      LogEvent(
         "OPEN_RETRY",
         signal.signal_id,
         IntegerToString((int)g_trade.ResultRetcode()) + ":" + g_trade.ResultRetcodeDescription()
      );
      return false;
   }

   g_active_signal = index;
   g_active_expiry = signal.entry_time + signal.hold_seconds;
   g_opened++;
   LogEvent(
      "OPENED",
      signal.signal_id,
      StringFormat(
         "entry=%.3f;stop=%.3f;target=%.3f;source_entry=%.3f;expiry=%s",
         g_trade.ResultPrice(),
         stop,
         target,
         signal.source_entry_price,
         TimeToString(g_active_expiry, TIME_DATE | TIME_SECONDS)
      )
   );
   return true;
}

int OnInit()
{
   if(!IsExpectedContext())
      return INIT_FAILED;
   if(InpScheduleFile == "" || InpSpecialistId == "" || InpFixedLots <= 0.0)
      return INIT_PARAMETERS_INCORRECT;

   g_event_log = FileOpen(
      InpEventLogFile,
      FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON,
      ','
   );
   if(g_event_log != INVALID_HANDLE)
      FileWrite(g_event_log, "server_time", "specialist_id", "event", "signal_id", "detail");

   const int loaded = LoadSchedule();
   if(loaded < 0)
      return INIT_FAILED;
   LogEvent("INITIALIZED", "", "schedule_rows=" + IntegerToString(loaded));
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   LogEvent(
      "DEINITIALIZED",
      "",
      "reason=" + IntegerToString(reason) + ";opened=" + IntegerToString(g_opened) +
      ";missed=" + IntegerToString(g_missed)
   );
   if(g_event_log != INVALID_HANDLE)
      FileClose(g_event_log);
}

void OnTick()
{
   ulong ticket = 0;
   const bool has_position = FindReplayPosition(ticket);
   if(g_active_signal >= 0 && !has_position)
   {
      LogEvent("POSITION_CLOSED", g_signals[g_active_signal].signal_id, "terminal_or_market_exit");
      g_active_signal = -1;
      g_active_expiry = 0;
   }

   if(has_position)
   {
      if(g_active_expiry > 0 && TimeCurrent() >= g_active_expiry)
      {
         const string signal_id = g_active_signal >= 0 ? g_signals[g_active_signal].signal_id : "";
         if(g_trade.PositionClose(ticket, InpDeviationPoints))
            LogEvent("HORIZON_CLOSE", signal_id, "ticket=" + IntegerToString((int)ticket));
         else
            LogEvent("HORIZON_CLOSE_RETRY", signal_id, g_trade.ResultRetcodeDescription());
      }
      return;
   }

   while(g_next_signal < ArraySize(g_signals))
   {
      const ReplaySignal signal = g_signals[g_next_signal];
      if(TimeCurrent() < signal.entry_time)
         return;
      if(TimeCurrent() > signal.entry_time + InpMaxEntryDelaySeconds)
      {
         LogEvent("MISSED", signal.signal_id, "no_eligible_tick_in_entry_window");
         g_missed++;
         g_next_signal++;
         continue;
      }
      if(OpenSignal(g_next_signal))
         g_next_signal++;
      return;
   }
}

double OnTester()
{
   Print(
      "FIVE_SPECIALIST_REPLAY_COMPLETE|",
      InpSpecialistId,
      "|scheduled=",
      ArraySize(g_signals),
      "|opened=",
      g_opened,
      "|missed=",
      g_missed,
      "|profit=",
      DoubleToString(TesterStatistics(STAT_PROFIT), 2)
   );
   return TesterStatistics(STAT_PROFIT);
}


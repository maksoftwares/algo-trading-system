#property strict
#property description "Tester-only, no-order parity kernel for frozen EURUSD Neutral inventory execution"
#property tester_file "EURUSD_NEUTRAL_INVENTORY_EXECUTION_PARITY_INPUT.csv"

input string InpFixtureFile = "EURUSD_NEUTRAL_INVENTORY_EXECUTION_PARITY_INPUT.csv";
input string InpOutputFile = "EURUSD_NEUTRAL_INVENTORY_EXECUTION_PARITY_OUTPUT.csv";

const double PIP = 0.0001;
const double MINIMUM_SPREAD_PIPS = 0.7;
const double MAXIMUM_ENTRY_SPREAD_PIPS = 1.5;
const double ADVERSE_SLIPPAGE_PIPS_PER_SIDE = 0.1;
const double FIXED_STOP_PIPS = 6.0;
const double FIXED_TARGET_PIPS = 9.0;
const int MAXIMUM_HOLD_SECONDS = 21600;

struct FixtureRow
{
   string case_id;
   int direction;
   datetime entry_time;
   datetime tick_time;
   double bid;
   double ask;
   string expected_status;
   string expected_exit_reason;
   datetime expected_entry_tick;
   datetime expected_exit_tick;
   double expected_entry_fill;
   double expected_exit_fill;
   double expected_r;
};

struct CaseResult
{
   string status;
   string exit_reason;
   datetime entry_tick;
   datetime exit_tick;
   double entry_fill;
   double exit_fill;
   double result_r;
};

FixtureRow g_rows[];
int g_output = INVALID_HANDLE;
int g_cases = 0;
int g_failures = 0;

bool CloseEnough(const double left, const double right)
{
   return MathAbs(left - right) <= 1e-9;
}

bool EmptyExpectedNumber(const double value)
{
   return value == 0.0;
}

int LoadFixture()
{
   const int handle = FileOpen(
      InpFixtureFile,
      FILE_READ | FILE_CSV | FILE_ANSI,
      ','
   );
   if(handle == INVALID_HANDLE)
   {
      Print("EURUSD_NEUTRAL_PARITY_INIT_FAIL|fixture_open|", GetLastError());
      return -1;
   }

   ArrayResize(g_rows, 0);
   while(!FileIsEnding(handle))
   {
      const string case_id = FileReadString(handle);
      const string side = FileReadString(handle);
      const string entry_text = FileReadString(handle);
      const string tick_text = FileReadString(handle);
      const string bid_text = FileReadString(handle);
      const string ask_text = FileReadString(handle);
      const string expected_status = FileReadString(handle);
      const string expected_reason = FileReadString(handle);
      const string expected_entry_text = FileReadString(handle);
      const string expected_exit_text = FileReadString(handle);
      const string expected_entry_fill_text = FileReadString(handle);
      const string expected_exit_fill_text = FileReadString(handle);
      const string expected_r_text = FileReadString(handle);

      if(case_id == "" || case_id == "case_id")
         continue;
      if(side != "LONG" && side != "SHORT")
      {
         FileClose(handle);
         Print("EURUSD_NEUTRAL_PARITY_INIT_FAIL|side|", case_id);
         return -1;
      }
      const int index = ArraySize(g_rows);
      ArrayResize(g_rows, index + 1);
      g_rows[index].case_id = case_id;
      g_rows[index].direction = side == "LONG" ? 1 : -1;
      g_rows[index].entry_time = (datetime)StringToInteger(entry_text);
      g_rows[index].tick_time = (datetime)StringToInteger(tick_text);
      g_rows[index].bid = StringToDouble(bid_text);
      g_rows[index].ask = StringToDouble(ask_text);
      g_rows[index].expected_status = expected_status;
      g_rows[index].expected_exit_reason = expected_reason;
      g_rows[index].expected_entry_tick = (datetime)StringToInteger(
         expected_entry_text
      );
      g_rows[index].expected_exit_tick = (datetime)StringToInteger(
         expected_exit_text
      );
      g_rows[index].expected_entry_fill = StringToDouble(
         expected_entry_fill_text
      );
      g_rows[index].expected_exit_fill = StringToDouble(
         expected_exit_fill_text
      );
      g_rows[index].expected_r = StringToDouble(expected_r_text);
      if(
         g_rows[index].entry_time <= 0 ||
         g_rows[index].tick_time <= 0 ||
         g_rows[index].ask < g_rows[index].bid
      )
      {
         FileClose(handle);
         Print("EURUSD_NEUTRAL_PARITY_INIT_FAIL|invalid_row|", case_id);
         return -1;
      }
   }
   FileClose(handle);
   return ArraySize(g_rows);
}

CaseResult EvaluateCase(const int first, const int last)
{
   CaseResult result;
   result.status = "";
   result.exit_reason = "";
   result.entry_tick = 0;
   result.exit_tick = 0;
   result.entry_fill = 0.0;
   result.exit_fill = 0.0;
   result.result_r = 0.0;

   const int direction = g_rows[first].direction;
   const datetime entry_time = g_rows[first].entry_time;
   int entry_index = -1;
   for(int index = first; index <= last; ++index)
   {
      if(g_rows[index].tick_time >= entry_time)
      {
         entry_index = index;
         break;
      }
   }
   if(entry_index < 0)
   {
      result.status = "NO_TRADE_MISSING_ENTRY_TICK";
      return result;
   }

   const FixtureRow entry = g_rows[entry_index];
   result.entry_tick = entry.tick_time;
   const double actual_spread_pips = (entry.ask - entry.bid) / PIP;
   const double effective_spread_pips = MathMax(
      actual_spread_pips,
      MINIMUM_SPREAD_PIPS
   );
   const double mid = 0.5 * (entry.bid + entry.ask);
   const double effective_bid = mid - 0.5 * effective_spread_pips * PIP;
   const double effective_ask = mid + 0.5 * effective_spread_pips * PIP;
   if(actual_spread_pips > MAXIMUM_ENTRY_SPREAD_PIPS)
   {
      result.status = "NO_TRADE_EXCESS_ENTRY_SPREAD";
      return result;
   }

   result.entry_fill = direction > 0
      ? effective_ask + ADVERSE_SLIPPAGE_PIPS_PER_SIDE * PIP
      : effective_bid - ADVERSE_SLIPPAGE_PIPS_PER_SIDE * PIP;
   const double stop_price = result.entry_fill -
      direction * FIXED_STOP_PIPS * PIP;
   const double target_price = result.entry_fill +
      direction * FIXED_TARGET_PIPS * PIP;
   const datetime deadline = entry_time + MAXIMUM_HOLD_SECONDS;
   int exit_index = -1;

   for(int index = entry_index; index <= last; ++index)
   {
      if(g_rows[index].tick_time >= deadline)
         break;
      const double observed = direction > 0
         ? g_rows[index].bid
         : g_rows[index].ask;
      const bool stop_hit = direction > 0
         ? observed <= stop_price
         : observed >= stop_price;
      const bool target_hit = direction > 0
         ? observed >= target_price
         : observed <= target_price;
      if(stop_hit)
      {
         result.exit_reason = "STOP";
         exit_index = index;
         break;
      }
      if(target_hit)
      {
         result.exit_reason = "TARGET";
         exit_index = index;
         break;
      }
   }

   if(exit_index < 0)
   {
      for(int index = entry_index; index <= last; ++index)
      {
         if(g_rows[index].tick_time >= deadline)
         {
            result.exit_reason = "TIME";
            exit_index = index;
            break;
         }
      }
   }
   if(exit_index < 0)
   {
      result.status = "PENDING_MISSING_TIME_EXIT_TICK";
      return result;
   }

   const FixtureRow exit_row = g_rows[exit_index];
   result.exit_tick = exit_row.tick_time;
   const double market_exit = direction > 0 ? exit_row.bid : exit_row.ask;
   result.exit_fill = direction > 0
      ? market_exit - ADVERSE_SLIPPAGE_PIPS_PER_SIDE * PIP
      : market_exit + ADVERSE_SLIPPAGE_PIPS_PER_SIDE * PIP;
   const double pnl_pips = direction *
      (result.exit_fill - result.entry_fill) / PIP;
   result.result_r = pnl_pips / FIXED_STOP_PIPS;
   result.status = "CLOSED";
   return result;
}

bool VerifyCase(const int first, const int last, const CaseResult &actual)
{
   const FixtureRow expected = g_rows[first];
   bool passed = actual.status == expected.expected_status;
   if(actual.status == "CLOSED" && expected.expected_status == "CLOSED")
   {
      passed = passed &&
         actual.exit_reason == expected.expected_exit_reason &&
         actual.entry_tick == expected.expected_entry_tick &&
         actual.exit_tick == expected.expected_exit_tick &&
         CloseEnough(actual.entry_fill, expected.expected_entry_fill) &&
         CloseEnough(actual.exit_fill, expected.expected_exit_fill) &&
         CloseEnough(actual.result_r, expected.expected_r);
   }
   else if(
      actual.status == "NO_TRADE_EXCESS_ENTRY_SPREAD" &&
      expected.expected_status == "NO_TRADE_EXCESS_ENTRY_SPREAD"
   )
   {
      passed = passed && actual.entry_tick == expected.expected_entry_tick;
   }
   FileWrite(
      g_output,
      expected.case_id,
      passed ? "PASS" : "FAIL",
      actual.status,
      actual.exit_reason,
      (long)actual.entry_tick,
      (long)actual.exit_tick,
      DoubleToString(actual.entry_fill, 12),
      DoubleToString(actual.exit_fill, 12),
      DoubleToString(actual.result_r, 12)
   );
   FileFlush(g_output);
   Print(
      "EURUSD_NEUTRAL_PARITY|",
      expected.case_id,
      "|",
      passed ? "PASS" : "FAIL",
      "|",
      actual.status,
      "|",
      actual.exit_reason
   );
   return passed;
}

int OnInit()
{
   if(!MQLInfoInteger(MQL_TESTER))
   {
      Print("EURUSD_NEUTRAL_PARITY_REFUSED|not_strategy_tester");
      return INIT_FAILED;
   }
   if(PositionsTotal() != 0)
   {
      Print("EURUSD_NEUTRAL_PARITY_REFUSED|positions_exist");
      return INIT_FAILED;
   }
   const int loaded = LoadFixture();
   if(loaded <= 0)
      return INIT_FAILED;
   g_output = FileOpen(
      InpOutputFile,
      FILE_WRITE | FILE_CSV | FILE_ANSI,
      ','
   );
   if(g_output == INVALID_HANDLE)
   {
      Print("EURUSD_NEUTRAL_PARITY_INIT_FAIL|output_open|", GetLastError());
      return INIT_FAILED;
   }
   FileWrite(
      g_output,
      "case_id",
      "result",
      "status",
      "exit_reason",
      "entry_tick_epoch",
      "exit_tick_epoch",
      "entry_fill",
      "exit_fill",
      "r"
   );

   int first = 0;
   while(first < loaded)
   {
      int last = first;
      while(
         last + 1 < loaded &&
         g_rows[last + 1].case_id == g_rows[first].case_id
      )
         ++last;
      const CaseResult actual = EvaluateCase(first, last);
      ++g_cases;
      if(!VerifyCase(first, last, actual))
         ++g_failures;
      first = last + 1;
   }
   Print(
      "EURUSD_NEUTRAL_PARITY_SUMMARY|cases=",
      g_cases,
      "|failures=",
      g_failures,
      "|broker_action_allowed=false"
   );
   return g_failures == 0 ? INIT_SUCCEEDED : INIT_FAILED;
}

void OnDeinit(const int reason)
{
   if(g_output != INVALID_HANDLE)
      FileClose(g_output);
}

void OnTick()
{
}

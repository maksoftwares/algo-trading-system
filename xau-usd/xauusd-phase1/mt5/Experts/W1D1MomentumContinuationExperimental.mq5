//+------------------------------------------------------------------+
//| W1D1MomentumContinuationExperimental.mq5                          |
//| EXPERIMENTAL FORWARD TEST - independent family (not breakout      |
//| retest). Byte-faithful MQL5 port of the locked research rules in  |
//| xauusd-phase0/docs/hypothesis_w1_d1_momentum_continuation_v0.md   |
//| (the 2026-06-10 locked full-window campaign's closest miss:       |
//| Dukascopy decade PF 1.276 / n=193; FAIL_REJECTED_VERSION_FINAL    |
//| for canonical approval - this deployment is demo forward          |
//| evidence collection in the experimental lane, NOT a validated     |
//| edge and NOT canonical Phase 2).                                  |
//|                                                                   |
//| Safety: demo-only guard, account allowlist, kill-switch file,     |
//| observer-safe default (InpAllowDemoTrading=false), fixed 0.01     |
//| lots, one position, max one setup per ISO week, spread guard.     |
//| Magic 932000. Never touches other EAs' positions.                 |
//+------------------------------------------------------------------+
#property copyright "maksoftwares - experimental demo lane"
#property version   "0.10"
#property strict

#include <Trade/Trade.mqh>

input bool   InpAllowDemoTrading     = false;  // false = observer (logs signals only)
input bool   InpAllowNonDemoAccounts = false;  // hard demo-only by default
input long   InpAllowedAccountLogin  = 0;      // 0 = any (demo) account
input long   InpMagicNumber          = 932000;
input double InpFixedLots            = 0.01;
input int    InpMaxSpreadPoints      = 75;     // measured p95 spread guard
input string InpKillSwitchFileName   = "W1D1_MOMENTUM_KILL.txt";

// Locked v0 mechanical constants - DO NOT TUNE (new locked vN required)
const int    ATR_PERIOD        = 14;
const double RANGE_MIN_ATR     = 0.75;
const double BODY_MIN_RATIO    = 0.35;
const double MOM20_MIN_ATR     = 1.25;
const double MOM5_MIN_ATR      = 0.25;
const double CLOSE_POS_LONG    = 0.65;
const double CLOSE_POS_SHORT   = 0.35;
const double STOP_PAD_ATR      = 0.20;
const double RISK_REWARD       = 1.5;

CTrade   g_trade;
int      g_atr_handle = INVALID_HANDLE;
datetime g_last_d1_bar = 0;
long     g_last_traded_week = 0;

int OnInit()
  {
   if(!InpAllowNonDemoAccounts &&
      AccountInfoInteger(ACCOUNT_TRADE_MODE) != ACCOUNT_TRADE_MODE_DEMO)
     {
      Print("W1D1Momentum: not a demo account. Refusing to run.");
      return(INIT_FAILED);
     }
   if(InpAllowedAccountLogin != 0 &&
      AccountInfoInteger(ACCOUNT_LOGIN) != InpAllowedAccountLogin)
     {
      Print("W1D1Momentum: account login not allowlisted. Refusing to run.");
      return(INIT_FAILED);
     }
   g_atr_handle = iATR(_Symbol, PERIOD_D1, ATR_PERIOD);
   if(g_atr_handle == INVALID_HANDLE) return(INIT_FAILED);
   g_trade.SetExpertMagicNumber(InpMagicNumber);
   g_last_traded_week = (long)GlobalVariableGet("W1D1MOM_LAST_WEEK_" + (string)InpMagicNumber);
   PrintFormat("W1D1Momentum: started. trading=%s (observer-safe default is false)",
               InpAllowDemoTrading ? "ENABLED" : "DISABLED");
   return(INIT_SUCCEEDED);
  }

void OnDeinit(const int reason) { if(g_atr_handle != INVALID_HANDLE) IndicatorRelease(g_atr_handle); }

void OnTick()
  {
   datetime current_d1 = iTime(_Symbol, PERIOD_D1, 0);
   if(current_d1 == g_last_d1_bar || current_d1 == 0) return;
   g_last_d1_bar = current_d1;
   EvaluateCompletedDailyBar();
  }

long IsoWeekKey(datetime t)
  {
   MqlDateTime s; TimeToStruct(t, s);
   int dow = (s.day_of_week == 0) ? 7 : s.day_of_week;       // Mon=1..Sun=7
   datetime thursday = t + (4 - dow) * 86400;
   MqlDateTime th; TimeToStruct(thursday, th);
   int iso_week = ((th.day_of_year - 1) / 7) + 1;
   return((long)th.year * 100 + iso_week);
  }

bool KillSwitchPresent() { return(FileIsExist(InpKillSwitchFileName)); }

bool HasOwnOpenPosition()
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0 || !PositionSelectByTicket(ticket)) continue;
      if(PositionGetInteger(POSITION_MAGIC) == InpMagicNumber &&
         PositionGetString(POSITION_SYMBOL) == _Symbol)
         return(true);
     }
   return(false);
  }

void EvaluateCompletedDailyBar()
  {
   // Signal bar = the just-completed D1 bar (shift 1); needs 25 bars of history.
   if(iBars(_Symbol, PERIOD_D1) < 30) return;

   double atr_buffer[2];
   if(CopyBuffer(g_atr_handle, 0, 1, 1, atr_buffer) != 1) return;
   double d1_atr = atr_buffer[0];

   double open  = iOpen(_Symbol, PERIOD_D1, 1);
   double high  = iHigh(_Symbol, PERIOD_D1, 1);
   double low   = iLow(_Symbol, PERIOD_D1, 1);
   double close = iClose(_Symbol, PERIOD_D1, 1);
   double close5_back  = iClose(_Symbol, PERIOD_D1, 6);   // close.shift(5) of signal bar
   double close20_back = iClose(_Symbol, PERIOD_D1, 21);  // close.shift(20) of signal bar
   if(d1_atr <= 0 || close5_back <= 0 || close20_back <= 0) return;

   double momentum5  = close - close5_back;
   double momentum20 = close - close20_back;
   double range = high - low;
   double body  = MathAbs(close - open);
   if(range <= 0) return;
   double body_ratio = body / range;
   double close_position = (close - low) / range;

   if(range < RANGE_MIN_ATR * d1_atr || body_ratio < BODY_MIN_RATIO) return;

   string direction = "";
   if(momentum20 >= MOM20_MIN_ATR * d1_atr && momentum5 >= MOM5_MIN_ATR * d1_atr &&
      close > open && close_position >= CLOSE_POS_LONG)
      direction = "LONG";
   else if(momentum20 <= -MOM20_MIN_ATR * d1_atr && momentum5 <= -MOM5_MIN_ATR * d1_atr &&
           close < open && close_position <= CLOSE_POS_SHORT)
      direction = "SHORT";
   if(direction == "") return;

   long week_key = IsoWeekKey(iTime(_Symbol, PERIOD_D1, 1));
   if(week_key == g_last_traded_week) return;          // one setup per ISO week
   if(HasOwnOpenPosition()) return;                    // one position at a time

   double stop_loss, take_profit;
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(direction == "LONG")
     {
      stop_loss = low - STOP_PAD_ATR * d1_atr;
      double risk = ask - stop_loss;
      if(risk <= 0) return;
      take_profit = ask + RISK_REWARD * risk;
     }
   else
     {
      stop_loss = high + STOP_PAD_ATR * d1_atr;
      double risk = stop_loss - bid;
      if(risk <= 0) return;
      take_profit = bid - RISK_REWARD * risk;
     }

   PrintFormat("W1D1Momentum SIGNAL %s week=%I64d close=%.2f sl=%.2f tp=%.2f atr=%.2f",
               direction, week_key, close, stop_loss, take_profit, d1_atr);

   if(!InpAllowDemoTrading) { Print("W1D1Momentum: observer mode - no order sent."); return; }
   if(KillSwitchPresent())  { Print("W1D1Momentum: kill switch present - no order sent."); return; }

   long spread_points = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   if(spread_points > InpMaxSpreadPoints)
     {
      PrintFormat("W1D1Momentum: spread %I64d > cap %d - skipped.", spread_points, InpMaxSpreadPoints);
      return;
     }

   bool sent = (direction == "LONG")
               ? g_trade.Buy(InpFixedLots, _Symbol, 0.0, stop_loss, take_profit, "W1D1MOM_EXP")
               : g_trade.Sell(InpFixedLots, _Symbol, 0.0, stop_loss, take_profit, "W1D1MOM_EXP");
   if(sent)
     {
      g_last_traded_week = week_key;
      GlobalVariableSet("W1D1MOM_LAST_WEEK_" + (string)InpMagicNumber, (double)week_key);
      PrintFormat("W1D1Momentum: %s order sent (%.2f lots).", direction, InpFixedLots);
     }
   else
      PrintFormat("W1D1Momentum: order failed, retcode=%d", g_trade.ResultRetcode());
  }
//+------------------------------------------------------------------+

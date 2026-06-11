//+------------------------------------------------------------------+
//| W1D1MomentumM5ContinuationExperimental.mq5                        |
//| EXPERIMENTAL DEMO ONLY - v2 of the W1/D1 momentum family:         |
//| W1/D1 bias layer + active M5 pullback/impulse trigger layer.      |
//| NOT canonical Phase 2. NOT Phase 0 approved. No real capital.     |
//| Independent magic 932100; never touches other EAs' positions.     |
//|                                                                   |
//| Matching Phase 0 research mirror is still required before any      |
//| owner decision to arm demo trading. See the deployment note.       |
//+------------------------------------------------------------------+
#property copyright "maksoftwares - experimental demo lane"
#property version   "1.010"
#property strict

#include <Trade/Trade.mqh>

//--- safety inputs (observer-safe defaults)
input bool   InpAllowDemoTrading      = false;   // false = observer (logs only)
input bool   InpAllowNonDemoAccounts  = false;   // hard demo-only by default
input long   InpAllowedAccountLogin   = 0;       // 0 = any (demo) account
input string InpKillSwitchFileName    = "W1D1_M5_MOMENTUM_KILL.txt";
//--- execution inputs
input long   InpMagicNumber           = 932100;
input double InpFixedLots             = 0.01;
input int    InpMaxSpreadPoints       = 75;
input int    InpMaxTradesPerDay       = 12;
input int    InpCooldownMinutes       = 10;
input bool   InpOnePositionAtATime    = false;
//--- mechanical inputs (defaults are the locked research-mirror values)
input int    InpD1EmaFast             = 20;
input int    InpD1EmaSlow             = 50;
input int    InpW1MomentumWeeks       = 4;
input int    InpM5EmaPeriod           = 20;
input int    InpM5AtrPeriod           = 14;
input double InpStopAtrMultiple       = 4.0;     // of M5 ATR
input int    InpStopFloorPoints       = 250;     // cost-safety floor
input double InpRiskReward            = 1.5;
input double InpMinBodyFraction       = 0.35;
input bool   InpEnableImpulseTrigger  = false;  // default off: scan showed impulse reduced PF
input double InpImpulseBodyFraction   = 0.45;
input double InpImpulseAtrMultiple    = 0.45;

CTrade   g_trade;
int      g_d1_ema_fast = INVALID_HANDLE;
int      g_d1_ema_slow = INVALID_HANDLE;
int      g_m5_ema      = INVALID_HANDLE;
int      g_m5_atr      = INVALID_HANDLE;
datetime g_last_m5_bar = 0;
datetime g_last_trade_time = 0;
string   g_trade_day = "";
int      g_trades_today = 0;

int OnInit()
  {
   if(!InpAllowNonDemoAccounts &&
      AccountInfoInteger(ACCOUNT_TRADE_MODE) != ACCOUNT_TRADE_MODE_DEMO)
     {
      Print("W1D1_M5_EXP: not a demo account and overrides disabled. Refusing to run.");
      return(INIT_FAILED);
     }
   if(InpAllowedAccountLogin != 0 &&
      AccountInfoInteger(ACCOUNT_LOGIN) != InpAllowedAccountLogin)
     {
      Print("W1D1_M5_EXP: account login not allowlisted. Refusing to run.");
      return(INIT_FAILED);
     }
   g_d1_ema_fast = iMA(_Symbol, PERIOD_D1, InpD1EmaFast, 0, MODE_EMA, PRICE_CLOSE);
   g_d1_ema_slow = iMA(_Symbol, PERIOD_D1, InpD1EmaSlow, 0, MODE_EMA, PRICE_CLOSE);
   g_m5_ema      = iMA(_Symbol, PERIOD_M5, InpM5EmaPeriod, 0, MODE_EMA, PRICE_CLOSE);
   g_m5_atr      = iATR(_Symbol, PERIOD_M5, InpM5AtrPeriod);
   if(g_d1_ema_fast == INVALID_HANDLE || g_d1_ema_slow == INVALID_HANDLE ||
      g_m5_ema == INVALID_HANDLE || g_m5_atr == INVALID_HANDLE)
      return(INIT_FAILED);
   g_trade.SetExpertMagicNumber(InpMagicNumber);
   PrintFormat("W1D1_M5_EXP: started. trading=%s magic=%I64d",
               InpAllowDemoTrading ? "ENABLED" : "DISABLED(observer)", InpMagicNumber);
   if(Period() != PERIOD_M5)
      Print("W1D1_M5_EXP: attach to M5 for operator clarity; internal decisions still use PERIOD_M5.");
   return(INIT_SUCCEEDED);
  }

void OnDeinit(const int reason)
  {
   if(g_d1_ema_fast != INVALID_HANDLE) IndicatorRelease(g_d1_ema_fast);
   if(g_d1_ema_slow != INVALID_HANDLE) IndicatorRelease(g_d1_ema_slow);
   if(g_m5_ema != INVALID_HANDLE)      IndicatorRelease(g_m5_ema);
   if(g_m5_atr != INVALID_HANDLE)      IndicatorRelease(g_m5_atr);
  }

void OnTick()
  {
   datetime current_m5 = iTime(_Symbol, PERIOD_M5, 0);
   if(current_m5 == g_last_m5_bar || current_m5 == 0) return;  // one decision per M5 bar
   g_last_m5_bar = current_m5;
   EvaluateNewM5Bar();
  }

//--- bias layer: completed W1 + D1 bars only -------------------------------
// Returns +1 bullish, -1 bearish, 0 no-trade.
int HigherTimeframeBias(string &reason)
  {
   double fast[1], slow[1];
   if(CopyBuffer(g_d1_ema_fast, 0, 1, 1, fast) != 1 ||
      CopyBuffer(g_d1_ema_slow, 0, 1, 1, slow) != 1)
     { reason = "d1_ema_unavailable"; return(0); }

   int d1_bias = 0;
   if(fast[0] > slow[0]) d1_bias = 1;
   else if(fast[0] < slow[0]) d1_bias = -1;
   if(d1_bias == 0) { reason = "d1_ema_flat"; return(0); }

   double w1_close_1 = iClose(_Symbol, PERIOD_W1, 1);
   double w1_close_n = iClose(_Symbol, PERIOD_W1, 1 + InpW1MomentumWeeks);
   if(w1_close_1 <= 0 || w1_close_n <= 0) { reason = "w1_history_unavailable"; return(0); }
   double w1_momentum = w1_close_1 - w1_close_n;

   if(d1_bias == 1 && w1_momentum >= 0) { reason = "bull"; return(1); }
   if(d1_bias == -1 && w1_momentum <= 0) { reason = "bear"; return(-1); }
   reason = "w1_d1_disagree";
   return(0);
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

void ResetDailyCounterIfNewDay()
  {
   string today = TimeToString(TimeCurrent(), TIME_DATE);
   if(today != g_trade_day) { g_trade_day = today; g_trades_today = 0; }
  }

//--- trigger layer: completed M5 bar (shift 1) -----------------------------
void EvaluateNewM5Bar()
  {
   ResetDailyCounterIfNewDay();

   string bias_reason = "";
   int bias = HigherTimeframeBias(bias_reason);
   if(bias == 0)
     {
      // log sparsely: only on the first M5 bar of each hour to avoid spam
      MqlDateTime now_struct; TimeToStruct(TimeCurrent(), now_struct);
      if(now_struct.min < 5) PrintFormat("W1D1_M5_EXP: no-trade bias (%s).", bias_reason);
      return;
     }

   double ema_buffer[1], atr_buffer[1];
   if(CopyBuffer(g_m5_ema, 0, 1, 1, ema_buffer) != 1 ||
      CopyBuffer(g_m5_atr, 0, 1, 1, atr_buffer) != 1) return;
   double m5_ema_signal = ema_buffer[0];   // EMA at the completed signal bar (shift 1)
   double m5_atr = atr_buffer[0];
   if(m5_atr <= 0) return;

   double open  = iOpen(_Symbol, PERIOD_M5, 1);
   double high  = iHigh(_Symbol, PERIOD_M5, 1);
   double low   = iLow(_Symbol, PERIOD_M5, 1);
   double close = iClose(_Symbol, PERIOD_M5, 1);
   double prev_close = iClose(_Symbol, PERIOD_M5, 2);
   double range = high - low;
   if(range <= 0) return;
   double body_fraction = MathAbs(close - open) / range;
   double close_position = (close - low) / range;
   double net_move = MathAbs(close - prev_close);

   // M5 trigger layer:
   // 1) pullback continuation: bar touches the EMA against the bias and
   //    closes back through it in the bias direction with a decisive body.
   // 2) impulse continuation: bar is already on the bias side of the EMA,
   //    expands at least 0.45 ATR from the prior close, and closes in the
   //    outer part of its range. This keeps the EA active during clean moves
   //    that do not offer a perfect EMA touch.
   string direction = "";
   string trigger_type = "";
   if(bias == 1 && low <= m5_ema_signal && close > m5_ema_signal &&
      close > open && body_fraction >= InpMinBodyFraction)
     { direction = "LONG"; trigger_type = "pullback"; }
   else if(bias == -1 && high >= m5_ema_signal && close < m5_ema_signal &&
           close < open && body_fraction >= InpMinBodyFraction)
     { direction = "SHORT"; trigger_type = "pullback"; }
   else if(InpEnableImpulseTrigger &&
           bias == 1 && close > m5_ema_signal && close > prev_close &&
           close > open && body_fraction >= InpImpulseBodyFraction &&
           close_position >= 0.65 && net_move >= InpImpulseAtrMultiple * m5_atr)
     { direction = "LONG"; trigger_type = "impulse"; }
   else if(InpEnableImpulseTrigger &&
           bias == -1 && close < m5_ema_signal && close < prev_close &&
           close < open && body_fraction >= InpImpulseBodyFraction &&
           close_position <= 0.35 && net_move >= InpImpulseAtrMultiple * m5_atr)
     { direction = "SHORT"; trigger_type = "impulse"; }
   if(direction == "") return;

   PrintFormat("W1D1_M5_EXP SIGNAL %s trigger=%s bias=%s close=%.2f ema=%.2f atr=%.2f body=%.2f",
               direction, trigger_type, bias_reason, close, m5_ema_signal, m5_atr, body_fraction);

   //--- anti-spam and safety gates (each skip is logged)
   if(!InpAllowDemoTrading) { Print("W1D1_M5_EXP skip: observer mode."); return; }
   if(KillSwitchPresent())  { Print("W1D1_M5_EXP skip: kill switch present."); return; }
   if(InpMaxTradesPerDay > 0 && g_trades_today >= InpMaxTradesPerDay)
     { PrintFormat("W1D1_M5_EXP skip: daily cap %d reached.", InpMaxTradesPerDay); return; }
   if(g_last_trade_time > 0 &&
      TimeCurrent() - g_last_trade_time < (datetime)(InpCooldownMinutes * 60))
     { Print("W1D1_M5_EXP skip: cooldown active."); return; }
   if(InpOnePositionAtATime && HasOwnOpenPosition())
     { Print("W1D1_M5_EXP skip: own position already open."); return; }
   long spread_points = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   if(spread_points > InpMaxSpreadPoints)
     { PrintFormat("W1D1_M5_EXP skip: spread %I64d > %d.", spread_points, InpMaxSpreadPoints); return; }

   //--- ATR-based stop with cost-safety floor; fixed lot; 1.5R target.
   //    No martingale, no grid, no averaging, no lot scaling - by design.
   double stop_distance = MathMax(InpStopAtrMultiple * m5_atr,
                                  InpStopFloorPoints * _Point);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double stop_loss, take_profit;
   bool sent;
   if(direction == "LONG")
     {
      stop_loss   = ask - stop_distance;
      take_profit = ask + InpRiskReward * stop_distance;
      sent = g_trade.Buy(InpFixedLots, _Symbol, 0.0, stop_loss, take_profit, "W1D1_M5_EXP");
     }
   else
     {
      stop_loss   = bid + stop_distance;
      take_profit = bid - InpRiskReward * stop_distance;
      sent = g_trade.Sell(InpFixedLots, _Symbol, 0.0, stop_loss, take_profit, "W1D1_M5_EXP");
     }

   if(sent)
     {
      g_trades_today++;
      g_last_trade_time = TimeCurrent();
      PrintFormat("W1D1_M5_EXP: %s order sent (%.2f lots, stop=%.2f, tp=%.2f, trades_today=%d).",
                  direction, InpFixedLots, stop_loss, take_profit, g_trades_today);
     }
   else
      PrintFormat("W1D1_M5_EXP: order failed, retcode=%d", g_trade.ResultRetcode());
  }
//+------------------------------------------------------------------+

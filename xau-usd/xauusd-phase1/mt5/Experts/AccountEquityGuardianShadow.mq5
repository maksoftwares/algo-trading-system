//+------------------------------------------------------------------+
//| AccountEquityGuardianShadow.mq5                                   |
//| Stage A SHADOW account-level supervisor (observer; closes NOTHING)|
//| Spec: Downloads/CODEX_BRIEF_ACCOUNT_EQUITY_GUARDIAN_2026_06_09.md |
//|                                                                   |
//| Watches TOTAL account equity/floating PnL and LOGS what rules     |
//| R1-R5 WOULD do. Contains no broker order submission or             |
//| position-changing calls of any kind by design.                    |
//| Demo-only guard + account allowlist + kill-switch file.           |
//| Rule parameters below are locked config v0 (2026-06-11);          |
//| changing them after results = new locked config vN.               |
//+------------------------------------------------------------------+
#property copyright "maksoftwares - experimental demo lane"
#property version   "1.000"
#property strict

input bool   InpEnableShadowLogging      = true;
input bool   InpAllowNonDemoAccounts     = false;   // safety: demo-only by default
input long   InpAllowedAccountLogin      = 0;       // 0 = any (demo) account
input int    InpTimerSeconds             = 10;
input double InpDailyLossLimitAed        = 150.0;   // R1 (locked v0)
input double InpPeakArmAtAed             = 150.0;   // R2 arm threshold (locked v0)
input double InpGivebackPct              = 0.40;    // R2 giveback fraction (locked v0)
input double InpProfitTargetAed          = 300.0;   // R3 (locked v0)
input int    InpMaxSameDirectionCount    = 2;       // R5 correlation cap (locked v0)
input string InpKillSwitchFileName       = "GUARDIAN_SHADOW_KILL.txt";
input string InpLogFileName              = "EQUITY_GUARDIAN_SHADOW_LOG.csv";
input string InpStartupFileName          = "EQUITY_GUARDIAN_SHADOW_STARTUP.csv";

double   g_session_peak_floating = 0.0;
datetime g_session_start         = 0;
string   g_log_header = "timestamp,balance,equity,total_floating,session_peak_floating,day_realized,"
                        "open_positions,max_same_dir_count,rule_fired,would_action,"
                        "hypothetical_locked_pnl_at_trigger";
string   g_startup_header = "timestamp_broker,timestamp_utc,account_login,server,trade_mode,"
                            "enable_shadow_logging,timer_seconds,daily_loss_limit_aed,"
                            "peak_arm_at_aed,giveback_pct,profit_target_aed,"
                            "max_same_direction_count,kill_switch_file,log_file,status";

string BoolText(const bool value)
  {
   return value ? "true" : "false";
  }

int OnInit()
  {
   if(!InpAllowNonDemoAccounts &&
      AccountInfoInteger(ACCOUNT_TRADE_MODE) != ACCOUNT_TRADE_MODE_DEMO)
     {
      Print("GuardianShadow: not a demo account and InpAllowNonDemoAccounts=false. Refusing to run.");
      return(INIT_FAILED);
     }
   if(InpAllowedAccountLogin != 0 &&
      AccountInfoInteger(ACCOUNT_LOGIN) != InpAllowedAccountLogin)
     {
      Print("GuardianShadow: account login not in allowlist. Refusing to run.");
      return(INIT_FAILED);
     }
   g_session_start = TimeCurrent();
   g_session_peak_floating = 0.0;
   WriteHeaderIfNeeded();
   WriteStartupRow("ATTACHED_GUARDIAN_SHADOW_STAGE_A");
   EventSetTimer(MathMax(InpTimerSeconds, 5));
   Print("GuardianShadow: Stage A observer started (closes nothing).");
   return(INIT_SUCCEEDED);
  }

void OnDeinit(const int reason) { EventKillTimer(); }

void OnTimer()
  {
   if(!InpEnableShadowLogging) return;
   if(KillSwitchPresent())
     {
      Comment("GuardianShadow: kill switch present - logging paused.");
      return;
     }
   EvaluateAndLog();
  }

bool KillSwitchPresent()
  {
   return(FileIsExist(InpKillSwitchFileName));
  }

void WriteHeaderIfNeeded()
  {
   if(FileIsExist(InpLogFileName)) return;
   int handle = FileOpen(InpLogFileName, FILE_WRITE|FILE_READ|FILE_CSV|FILE_ANSI, ',');
   if(handle == INVALID_HANDLE) return;
   FileSeek(handle, 0, SEEK_END);
   FileWrite(handle, g_log_header);
   FileClose(handle);
  }

void WriteStartupRow(const string status)
  {
   bool new_file = !FileIsExist(InpStartupFileName);
   int handle = FileOpen(InpStartupFileName, FILE_WRITE|FILE_READ|FILE_CSV|FILE_ANSI, ',');
   if(handle == INVALID_HANDLE) return;
   FileSeek(handle, 0, SEEK_END);
   if(new_file)
      FileWrite(handle, g_startup_header);
   FileWrite(handle,
             TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS),
             TimeToString(TimeGMT(), TIME_DATE|TIME_SECONDS),
             IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)),
             AccountInfoString(ACCOUNT_SERVER),
             IntegerToString((int)AccountInfoInteger(ACCOUNT_TRADE_MODE)),
             BoolText(InpEnableShadowLogging),
             IntegerToString(InpTimerSeconds),
             DoubleToString(InpDailyLossLimitAed, 2),
             DoubleToString(InpPeakArmAtAed, 2),
             DoubleToString(InpGivebackPct, 4),
             DoubleToString(InpProfitTargetAed, 2),
             IntegerToString(InpMaxSameDirectionCount),
             InpKillSwitchFileName,
             InpLogFileName,
             status);
   FileClose(handle);
  }

double DayRealizedPnl()
  {
   MqlDateTime now_struct;
   TimeCurrent(now_struct);
   now_struct.hour = 0; now_struct.min = 0; now_struct.sec = 0;
   datetime day_start = StructToTime(now_struct);
   if(!HistorySelect(day_start, TimeCurrent())) return(0.0);
   double realized = 0.0;
   int deals = HistoryDealsTotal();
   for(int i = 0; i < deals; i++)
     {
      ulong ticket = HistoryDealGetTicket(i);
      if(ticket == 0) continue;
      if((ENUM_DEAL_ENTRY)HistoryDealGetInteger(ticket, DEAL_ENTRY) == DEAL_ENTRY_IN) continue;
      realized += HistoryDealGetDouble(ticket, DEAL_PROFIT)
                + HistoryDealGetDouble(ticket, DEAL_SWAP)
                + HistoryDealGetDouble(ticket, DEAL_COMMISSION);
     }
   return(realized);
  }

int MaxSameDirectionCount()
  {
   int best = 0;
   int total = PositionsTotal();
   for(int i = 0; i < total; i++)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0 || !PositionSelectByTicket(ticket)) continue;
      string symbol = PositionGetString(POSITION_SYMBOL);
      long   ptype  = PositionGetInteger(POSITION_TYPE);
      int count = 0;
      for(int j = 0; j < total; j++)
        {
         ulong other = PositionGetTicket(j);
         if(other == 0 || !PositionSelectByTicket(other)) continue;
         if(PositionGetString(POSITION_SYMBOL) == symbol &&
            PositionGetInteger(POSITION_TYPE) == ptype)
            count++;
        }
      if(count > best) best = count;
     }
   return(best);
  }

void EvaluateAndLog()
  {
   double balance        = AccountInfoDouble(ACCOUNT_BALANCE);
   double equity         = AccountInfoDouble(ACCOUNT_EQUITY);
   double total_floating = equity - balance;
   double day_realized   = DayRealizedPnl();
   int    open_positions = PositionsTotal();
   int    max_same_dir   = MaxSameDirectionCount();

   if(total_floating > g_session_peak_floating)
      g_session_peak_floating = total_floating;

   string rule_fired   = "none";
   string would_action = "NONE";
   double locked_pnl   = 0.0;

   // R1 hard daily loss stop (priority)
   if(day_realized + total_floating <= -InpDailyLossLimitAed)
     {
      rule_fired = "R1_DAILY_LOSS_STOP"; would_action = "FLATTEN_ALL_AND_HALT";
      locked_pnl = day_realized + total_floating;
     }
   // R2 peak-giveback trail (the +300 -> -100 answer)
   else if(g_session_peak_floating >= InpPeakArmAtAed &&
           total_floating <= g_session_peak_floating * (1.0 - InpGivebackPct))
     {
      rule_fired = "R2_PEAK_GIVEBACK_TRAIL"; would_action = "FLATTEN_ALL";
      locked_pnl = total_floating;
     }
   // R3 profit target
   else if(total_floating >= InpProfitTargetAed)
     {
      rule_fired = "R3_PROFIT_TARGET"; would_action = "FLATTEN_ALL";
      locked_pnl = total_floating;
     }
   // R5 correlation cap (report-only; runtime caps are the real fix)
   else if(max_same_dir > InpMaxSameDirectionCount)
     {
      rule_fired = "R5_CORRELATION_CAP"; would_action = "WOULD_HAVE_BLOCKED_ENTRY";
      locked_pnl = total_floating;
     }

   int handle = FileOpen(InpLogFileName, FILE_WRITE|FILE_READ|FILE_CSV|FILE_ANSI, ',');
   if(handle == INVALID_HANDLE) return;
   FileSeek(handle, 0, SEEK_END);
   FileWrite(handle,
             TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS),
             DoubleToString(balance, 2),
             DoubleToString(equity, 2),
             DoubleToString(total_floating, 2),
             DoubleToString(g_session_peak_floating, 2),
             DoubleToString(day_realized, 2),
             IntegerToString(open_positions),
             IntegerToString(max_same_dir),
             rule_fired,
             would_action,
             DoubleToString(locked_pnl, 2));
   FileClose(handle);

   Comment(StringFormat("GuardianShadow (observer): floating=%.2f peak=%.2f dayPnL=%.2f rule=%s",
                        total_floating, g_session_peak_floating, day_realized, rule_fired));
  }
//+------------------------------------------------------------------+

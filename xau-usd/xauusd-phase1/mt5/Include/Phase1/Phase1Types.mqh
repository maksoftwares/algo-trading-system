#ifndef PHASE1_TYPES_MQH
#define PHASE1_TYPES_MQH

enum Phase1LifecycleState
{
   PHASE1_DISABLED = 0,
   PHASE1_DRY_RUN = 1
};

enum Phase1ExpertLifecycleState
{
   PHASE1_EXPERT_DISABLED = 0,
   PHASE1_EXPERT_DRY_RUN_ONLY = 1,
   PHASE1_EXPERT_ACTIVE = 2,
   PHASE1_EXPERT_SUSPENDED = 3,
   PHASE1_EXPERT_RETIRED = 4,
   PHASE1_EXPERT_COST_REVALIDATION_PENDING = 5,
   PHASE1_EXPERT_COST_SUSPENDED = 6
};

enum Phase1SessionState
{
   PHASE1_SESSION_UNKNOWN = 0,
   PHASE1_SESSION_ASIA = 1,
   PHASE1_SESSION_LONDON = 2,
   PHASE1_SESSION_NEW_YORK = 3,
   PHASE1_SESSION_ROLLOVER = 4,
   PHASE1_SESSION_WEEKEND = 5,
   PHASE1_SESSION_THIN = 6
};

enum Phase1RegimeState
{
   PHASE1_REGIME_NO_TRADE = 0,
   PHASE1_REGIME_TREND_WITH_PULLBACK = 1,
   PHASE1_REGIME_RANGE = 2,
   PHASE1_REGIME_COMPRESSION = 3,
   PHASE1_REGIME_BREAKOUT_RETEST = 4,
   PHASE1_REGIME_ABNORMAL_MARKET = 5,
   PHASE1_REGIME_NEWS_BLACKOUT = 6
};

enum Phase1RiskState
{
   PHASE1_RISK_NORMAL = 0,
   PHASE1_RISK_REDUCED = 1,
   PHASE1_RISK_DEFENSIVE = 2,
   PHASE1_RISK_LOCKED_DAILY = 3,
   PHASE1_RISK_LOCKED_WEEKLY = 4,
   PHASE1_RISK_LOCKED_MONTHLY = 5,
   PHASE1_RISK_MANUAL_LOCK = 6
};

enum Phase1ExecutionState
{
   PHASE1_EXECUTION_OK = 0,
   PHASE1_EXECUTION_SPREAD_TOO_HIGH = 1,
   PHASE1_EXECUTION_SLIPPAGE_TOO_HIGH = 2,
   PHASE1_EXECUTION_STALE_TICK = 3,
   PHASE1_EXECUTION_SYMBOL_NOT_TRADEABLE = 4,
   PHASE1_EXECUTION_MARKET_CLOSED = 5,
   PHASE1_EXECUTION_BROKER_ERROR = 6
};

enum Phase1NewsState
{
   PHASE1_NEWS_NO_RISK = 0,
   PHASE1_NEWS_PRE_BLACKOUT = 1,
   PHASE1_NEWS_POST_COOLDOWN = 2,
   PHASE1_NEWS_MANUAL_LOCKDOWN = 3
};

enum Phase1SignalDirection
{
   PHASE1_SIGNAL_NONE = 0,
   PHASE1_SIGNAL_LONG = 1,
   PHASE1_SIGNAL_SHORT = -1
};

struct Phase1MarketSnapshot
{
   string symbol_name;
   datetime broker_time;
   datetime utc_time;
   datetime local_time;
   datetime m5_bar_time;
   double bid;
   double ask;
   double point;
   double spread_points;
   int digits;
   int stale_seconds;
   bool tick_ok;
   bool symbol_tradeable;
};

struct Phase1FeatureSnapshot
{
   double atr14_points;
   double m5_range_points;
   double m5_body_points;
   double m5_upper_wick_points;
   double m5_lower_wick_points;
   double m15_range_points;
   double h1_range_points;
   bool compression_state;
   bool feature_ok;
};

struct Phase1ServerTimeStatus
{
   long broker_utc_offset_seconds;
   long local_utc_offset_seconds;
   long local_clock_drift_seconds;
   bool clock_ok;
   string status_text;
};

struct Phase1RiskSnapshot
{
   double requested_risk_pct;
   double max_risk_pct;
   double simulated_daily_pnl_pct;
   double simulated_weekly_pnl_pct;
   double simulated_monthly_pnl_pct;
   double daily_loss_limit_pct;
   double weekly_loss_limit_pct;
   double monthly_loss_limit_pct;
   bool manual_lock;
   bool risk_ok;
};

struct Phase1BreakoutRetestObservation
{
   string stage;
   string direction_text;
   string reason_code;
   bool would_signal;
   bool level_found;
   bool break_found;
   bool retest_valid;
   bool confirmation_valid;
   string level_kind;
   double level_price;
   double entry_price;
   double stop_loss;
   double take_profit;
   double stop_distance_points;
   int break_shift;
   int retest_shift;
   int confirmation_shift;
};

struct Phase1Signal
{
   string expert_name;
   int magic_number;
   Phase1SignalDirection direction;
   double entry_price;
   double stop_loss;
   double take_profit;
   double risk_pct;
   string reason_code;
   string blocked_reason;
};

struct Phase1Decision
{
   string run_id;
   string lifecycle_state;
   Phase1MarketSnapshot market;
   Phase1SessionState session_state;
   Phase1RegimeState regime_state;
   Phase1RiskState risk_state;
   Phase1ExecutionState execution_state;
   Phase1NewsState news_state;
   Phase1FeatureSnapshot features;
   Phase1ServerTimeStatus server_time;
   Phase1RiskSnapshot risk_details;
   Phase1BreakoutRetestObservation breakout_retest;
   Phase1BreakoutRetestObservation swing_breakout_retest;
   string allowed_expert;
   string would_have_allowed_experts;
   string expert_lifecycle_state;
   string br_lifecycle_state;
   string sbr_lifecycle_state;
   bool magic_namespace_ok;
   bool trade_permission;
   bool dry_run;
   string block_reason;
   Phase1Signal signal;
};

void Phase1ResetMarketSnapshot(Phase1MarketSnapshot &snapshot)
{
   snapshot.symbol_name = "";
   snapshot.broker_time = 0;
   snapshot.utc_time = 0;
   snapshot.local_time = 0;
   snapshot.m5_bar_time = 0;
   snapshot.bid = 0.0;
   snapshot.ask = 0.0;
   snapshot.point = 0.0;
   snapshot.spread_points = 0.0;
   snapshot.digits = 0;
   snapshot.stale_seconds = 0;
   snapshot.tick_ok = false;
   snapshot.symbol_tradeable = false;
}

void Phase1ResetFeatureSnapshot(Phase1FeatureSnapshot &features)
{
   features.atr14_points = 0.0;
   features.m5_range_points = 0.0;
   features.m5_body_points = 0.0;
   features.m5_upper_wick_points = 0.0;
   features.m5_lower_wick_points = 0.0;
   features.m15_range_points = 0.0;
   features.h1_range_points = 0.0;
   features.compression_state = false;
   features.feature_ok = false;
}

void Phase1ResetServerTimeStatus(Phase1ServerTimeStatus &status)
{
   status.broker_utc_offset_seconds = 0;
   status.local_utc_offset_seconds = 0;
   status.local_clock_drift_seconds = 0;
   status.clock_ok = false;
   status.status_text = "NOT_CHECKED";
}

void Phase1ResetRiskSnapshot(Phase1RiskSnapshot &risk)
{
   risk.requested_risk_pct = 0.0;
   risk.max_risk_pct = 0.0;
   risk.simulated_daily_pnl_pct = 0.0;
   risk.simulated_weekly_pnl_pct = 0.0;
   risk.simulated_monthly_pnl_pct = 0.0;
   risk.daily_loss_limit_pct = 0.0;
   risk.weekly_loss_limit_pct = 0.0;
   risk.monthly_loss_limit_pct = 0.0;
   risk.manual_lock = false;
   risk.risk_ok = false;
}

void Phase1ResetBreakoutRetestObservation(Phase1BreakoutRetestObservation &observation)
{
   observation.stage = "NOT_EVALUATED";
   observation.direction_text = "NONE";
   observation.reason_code = "breakout_retest_not_evaluated";
   observation.would_signal = false;
   observation.level_found = false;
   observation.break_found = false;
   observation.retest_valid = false;
   observation.confirmation_valid = false;
   observation.level_kind = "none";
   observation.level_price = 0.0;
   observation.entry_price = 0.0;
   observation.stop_loss = 0.0;
   observation.take_profit = 0.0;
   observation.stop_distance_points = 0.0;
   observation.break_shift = -1;
   observation.retest_shift = 2;
   observation.confirmation_shift = 1;
}

void Phase1ResetSignal(Phase1Signal &signal)
{
   signal.expert_name = "none";
   signal.magic_number = 910000;
   signal.direction = PHASE1_SIGNAL_NONE;
   signal.entry_price = 0.0;
   signal.stop_loss = 0.0;
   signal.take_profit = 0.0;
   signal.risk_pct = 0.0;
   signal.reason_code = "no_signal";
   signal.blocked_reason = "no_approved_expert";
}

void Phase1ResetDecision(Phase1Decision &decision)
{
   decision.run_id = "";
   decision.lifecycle_state = "DRY_RUN";
   Phase1ResetMarketSnapshot(decision.market);
   decision.session_state = PHASE1_SESSION_UNKNOWN;
   decision.regime_state = PHASE1_REGIME_NO_TRADE;
   decision.risk_state = PHASE1_RISK_NORMAL;
   decision.execution_state = PHASE1_EXECUTION_OK;
   decision.news_state = PHASE1_NEWS_NO_RISK;
   Phase1ResetFeatureSnapshot(decision.features);
   Phase1ResetServerTimeStatus(decision.server_time);
   Phase1ResetRiskSnapshot(decision.risk_details);
   Phase1ResetBreakoutRetestObservation(decision.breakout_retest);
   Phase1ResetBreakoutRetestObservation(decision.swing_breakout_retest);
   decision.allowed_expert = "none";
   decision.would_have_allowed_experts = "none";
   decision.expert_lifecycle_state = "DISABLED";
   decision.br_lifecycle_state = "DISABLED";
   decision.sbr_lifecycle_state = "DISABLED";
   decision.magic_namespace_ok = false;
   decision.trade_permission = false;
   decision.dry_run = true;
   decision.block_reason = "phase1_dry_run_only";
   Phase1ResetSignal(decision.signal);
}

string Phase1DirectionText(const Phase1SignalDirection direction)
{
   if(direction == PHASE1_SIGNAL_LONG)
      return "LONG";
   if(direction == PHASE1_SIGNAL_SHORT)
      return "SHORT";
   return "NONE";
}

string Phase1ExpertLifecycleText(const Phase1ExpertLifecycleState state)
{
   if(state == PHASE1_EXPERT_DRY_RUN_ONLY)
      return "DRY_RUN_ONLY";
   if(state == PHASE1_EXPERT_ACTIVE)
      return "ACTIVE";
   if(state == PHASE1_EXPERT_SUSPENDED)
      return "SUSPENDED";
   if(state == PHASE1_EXPERT_RETIRED)
      return "RETIRED";
   if(state == PHASE1_EXPERT_COST_REVALIDATION_PENDING)
      return "COST_REVALIDATION_PENDING";
   if(state == PHASE1_EXPERT_COST_SUSPENDED)
      return "COST_SUSPENDED";
   return "DISABLED";
}

string Phase1SessionText(const Phase1SessionState state)
{
   if(state == PHASE1_SESSION_ASIA)
      return "ASIA";
   if(state == PHASE1_SESSION_LONDON)
      return "LONDON";
   if(state == PHASE1_SESSION_NEW_YORK)
      return "NEW_YORK";
   if(state == PHASE1_SESSION_ROLLOVER)
      return "ROLLOVER";
   if(state == PHASE1_SESSION_WEEKEND)
      return "WEEKEND";
   if(state == PHASE1_SESSION_THIN)
      return "THIN";
   return "UNKNOWN";
}

string Phase1RegimeText(const Phase1RegimeState state)
{
   if(state == PHASE1_REGIME_TREND_WITH_PULLBACK)
      return "TREND_WITH_PULLBACK";
   if(state == PHASE1_REGIME_RANGE)
      return "RANGE";
   if(state == PHASE1_REGIME_COMPRESSION)
      return "COMPRESSION";
   if(state == PHASE1_REGIME_BREAKOUT_RETEST)
      return "BREAKOUT_RETEST";
   if(state == PHASE1_REGIME_ABNORMAL_MARKET)
      return "ABNORMAL_MARKET";
   if(state == PHASE1_REGIME_NEWS_BLACKOUT)
      return "NEWS_BLACKOUT";
   return "NO_TRADE";
}

string Phase1RiskText(const Phase1RiskState state)
{
   if(state == PHASE1_RISK_REDUCED)
      return "REDUCED_RISK";
   if(state == PHASE1_RISK_DEFENSIVE)
      return "DEFENSIVE";
   if(state == PHASE1_RISK_LOCKED_DAILY)
      return "LOCKED_DAILY_LOSS";
   if(state == PHASE1_RISK_LOCKED_WEEKLY)
      return "LOCKED_WEEKLY_LOSS";
   if(state == PHASE1_RISK_LOCKED_MONTHLY)
      return "LOCKED_MONTHLY_LOSS";
   if(state == PHASE1_RISK_MANUAL_LOCK)
      return "MANUAL_LOCK";
   return "NORMAL";
}

string Phase1ExecutionText(const Phase1ExecutionState state)
{
   if(state == PHASE1_EXECUTION_SPREAD_TOO_HIGH)
      return "SPREAD_TOO_HIGH";
   if(state == PHASE1_EXECUTION_SLIPPAGE_TOO_HIGH)
      return "SLIPPAGE_TOO_HIGH";
   if(state == PHASE1_EXECUTION_STALE_TICK)
      return "STALE_TICK";
   if(state == PHASE1_EXECUTION_SYMBOL_NOT_TRADEABLE)
      return "SYMBOL_NOT_TRADEABLE";
   if(state == PHASE1_EXECUTION_MARKET_CLOSED)
      return "MARKET_CLOSED";
   if(state == PHASE1_EXECUTION_BROKER_ERROR)
      return "BROKER_ERROR";
   return "EXECUTION_OK";
}

string Phase1NewsText(const Phase1NewsState state)
{
   if(state == PHASE1_NEWS_PRE_BLACKOUT)
      return "PRE_NEWS_BLACKOUT";
   if(state == PHASE1_NEWS_POST_COOLDOWN)
      return "POST_NEWS_COOLDOWN";
   if(state == PHASE1_NEWS_MANUAL_LOCKDOWN)
      return "MANUAL_NEWS_LOCKDOWN";
   return "NO_NEWS_RISK";
}

#endif

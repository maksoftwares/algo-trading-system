// Account 3 breakout repair lane. Experimental demo only; not canonical Phase 2.
// A3_BREAKOUT_TIER1_COMPAT_V1: A2-compatible session gate + XAU stop floor, with trend guard shadowed first.
#property strict
#property version   "1.000"
#property description "A3 tier1-compatible breakout executor. Demo-only, dry-run by committed default."

#define A3_BREAKOUT_DEFAULT_RUN_ID "A3_BREAKOUT_TIER1_COMPAT_V1"
#define A3_BREAKOUT_DEFAULT_MAGIC 933400
#define A3_BREAKOUT_EXPECTED_MAGIC 933400
#define A3_BREAKOUT_DEFAULT_COMMENT "A3_BREAKOUT_TIER1_COMPAT"
#define A3_BREAKOUT_SIGNAL_LOG "a3_breakout_tier1_compat_signal_log.csv"
#define A3_BREAKOUT_STARTUP_LOG "a3_breakout_tier1_compat_startup.csv"
#define A3_BREAKOUT_ORDER_LOG "a3_breakout_tier1_compat_order_log.csv"
#define A3_BREAKOUT_MANAGEMENT_LOG "a3_breakout_tier1_compat_management_log.csv"
#define A3_BREAKOUT_ATTACHED_STATUS "ATTACHED_A3_BREAKOUT_TIER1_COMPAT"
#define A3_BREAKOUT_TREND_GUARD_DEFAULT false
#define A3_BREAKOUT_EXIT_PROTECTION_DEFAULT false
#define A3_BREAKOUT_SESSION_GATE_DEFAULT true
#define A3_BREAKOUT_STOP_FLOOR_DEFAULT true
#define A3_BREAKOUT_TREND_SHADOW_DEFAULT true

#include <A3BreakoutExecutorBase.mqh>

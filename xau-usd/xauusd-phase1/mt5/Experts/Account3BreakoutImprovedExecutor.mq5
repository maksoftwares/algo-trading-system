// Account 3 breakout A/B lane B. Experimental demo only; not canonical Phase 2.
// Lane B / A3_BREAKOUT_IMPROVED: plain breakout-retest entry plus trend guard and exit protection.
#property strict
#property version   "1.000"
#property description "A3 improved breakout executor. Demo-only, dry-run by committed default."

#define A3_BREAKOUT_DEFAULT_RUN_ID "A3_BREAKOUT_IMPROVED_V1"
#define A3_BREAKOUT_DEFAULT_MAGIC 933300
#define A3_BREAKOUT_EXPECTED_MAGIC 933300
#define A3_BREAKOUT_DEFAULT_COMMENT "A3_BREAKOUT_IMPROVED"
#define A3_BREAKOUT_SIGNAL_LOG "a3_breakout_improved_signal_log.csv"
#define A3_BREAKOUT_STARTUP_LOG "a3_breakout_improved_startup.csv"
#define A3_BREAKOUT_ORDER_LOG "a3_breakout_improved_order_log.csv"
#define A3_BREAKOUT_MANAGEMENT_LOG "a3_breakout_improved_management_log.csv"
#define A3_BREAKOUT_ATTACHED_STATUS "ATTACHED_A3_BREAKOUT_IMPROVED"
#define A3_BREAKOUT_TREND_GUARD_DEFAULT true
#define A3_BREAKOUT_EXIT_PROTECTION_DEFAULT true

#include <A3BreakoutExecutorBase.mqh>

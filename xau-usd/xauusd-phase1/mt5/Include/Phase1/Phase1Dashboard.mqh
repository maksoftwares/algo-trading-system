#ifndef PHASE1_DASHBOARD_MQH
#define PHASE1_DASHBOARD_MQH

#include <Phase1/Phase1Types.mqh>

class CPhase1Dashboard
{
public:
   void Render(const Phase1Decision &decision) const
   {
      string text = "XAUUSD Phase 1 Dry Run\n";
      text += "Run: " + decision.run_id + "\n";
      text += "Symbol: " + decision.market.symbol_name + "\n";
      text += "Mode: " + decision.lifecycle_state + "\n";
      text += "Spread: " + DoubleToString(decision.market.spread_points, 2) + "\n";
      text += "Session: " + Phase1SessionText(decision.session_state) + "\n";
      text += "Regime: " + Phase1RegimeText(decision.regime_state) + "\n";
      text += "Risk: " + Phase1RiskText(decision.risk_state) + "\n";
      text += "Risk sim D/W/M: "
         + DoubleToString(decision.risk_details.simulated_daily_pnl_pct, 2)
         + " / "
         + DoubleToString(decision.risk_details.simulated_weekly_pnl_pct, 2)
         + " / "
         + DoubleToString(decision.risk_details.simulated_monthly_pnl_pct, 2)
         + "\n";
      text += "Execution: " + Phase1ExecutionText(decision.execution_state) + "\n";
      text += "News: " + Phase1NewsText(decision.news_state) + "\n";
      text += "Lifecycle: " + decision.expert_lifecycle_state + "\n";
      text += "Magic namespace: " + (decision.magic_namespace_ok ? "ok" : "invalid") + "\n";
      text += "Server time: " + decision.server_time.status_text + "\n";
      text += "ATR14 M5: " + DoubleToString(decision.features.atr14_points, 2) + "\n";
      text += "M5 range/body: "
         + DoubleToString(decision.features.m5_range_points, 2)
         + " / "
         + DoubleToString(decision.features.m5_body_points, 2)
         + "\n";
      text += "Compression: " + (decision.features.compression_state ? "true" : "false") + "\n";
      text += "BR stage: " + decision.breakout_retest.stage + "\n";
      text += "BR direction: " + decision.breakout_retest.direction_text + "\n";
      text += "BR would signal: " + (decision.breakout_retest.would_signal ? "true" : "false") + "\n";
      text += "BR level: "
         + decision.breakout_retest.level_kind
         + " "
         + DoubleToString(decision.breakout_retest.level_price, decision.market.digits)
         + "\n";
      text += "Allowed expert: " + decision.allowed_expert + "\n";
      text += "Would allow: " + decision.would_have_allowed_experts + "\n";
      text += "Permission: " + (decision.trade_permission ? "true" : "false") + "\n";
      text += "Block: " + decision.block_reason + "\n";
      text += "Last bar: " + TimeToString(decision.market.m5_bar_time, TIME_DATE | TIME_MINUTES);
      Comment(text);
   }

   void Clear() const
   {
      Comment("");
   }
};

#endif

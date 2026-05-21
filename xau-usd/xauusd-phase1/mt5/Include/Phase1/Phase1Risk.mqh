#ifndef PHASE1_RISK_MQH
#define PHASE1_RISK_MQH

#include <Phase1/Phase1Types.mqh>

class CPhase1RiskGate
{
private:
   double m_max_spread_points;
   double m_max_risk_pct;
   double m_daily_loss_limit_pct;
   double m_weekly_loss_limit_pct;
   double m_monthly_loss_limit_pct;
   double m_simulated_daily_pnl_pct;
   double m_simulated_weekly_pnl_pct;
   double m_simulated_monthly_pnl_pct;
   bool m_manual_lock;

public:
   void Configure(
      const double max_spread_points,
      const double max_risk_pct,
      const double daily_loss_limit_pct,
      const double weekly_loss_limit_pct,
      const double monthly_loss_limit_pct,
      const double simulated_daily_pnl_pct,
      const double simulated_weekly_pnl_pct,
      const double simulated_monthly_pnl_pct,
      const bool manual_lock
   )
   {
      m_max_spread_points = max_spread_points;
      m_max_risk_pct = max_risk_pct;
      m_daily_loss_limit_pct = daily_loss_limit_pct;
      m_weekly_loss_limit_pct = weekly_loss_limit_pct;
      m_monthly_loss_limit_pct = monthly_loss_limit_pct;
      m_simulated_daily_pnl_pct = simulated_daily_pnl_pct;
      m_simulated_weekly_pnl_pct = simulated_weekly_pnl_pct;
      m_simulated_monthly_pnl_pct = simulated_monthly_pnl_pct;
      m_manual_lock = manual_lock;
   }

   bool SpreadAllowed(const double spread_points) const
   {
      return spread_points >= 0.0 && spread_points <= m_max_spread_points;
   }

   bool RiskAllowed(const double requested_risk_pct) const
   {
      return requested_risk_pct > 0.0 && requested_risk_pct <= m_max_risk_pct;
   }

   Phase1RiskState Evaluate(const double requested_risk_pct, Phase1RiskSnapshot &risk) const
   {
      Phase1ResetRiskSnapshot(risk);
      risk.requested_risk_pct = requested_risk_pct;
      risk.max_risk_pct = m_max_risk_pct;
      risk.simulated_daily_pnl_pct = m_simulated_daily_pnl_pct;
      risk.simulated_weekly_pnl_pct = m_simulated_weekly_pnl_pct;
      risk.simulated_monthly_pnl_pct = m_simulated_monthly_pnl_pct;
      risk.daily_loss_limit_pct = m_daily_loss_limit_pct;
      risk.weekly_loss_limit_pct = m_weekly_loss_limit_pct;
      risk.monthly_loss_limit_pct = m_monthly_loss_limit_pct;
      risk.manual_lock = m_manual_lock;

      Phase1RiskState state = PHASE1_RISK_NORMAL;
      if(m_manual_lock)
         state = PHASE1_RISK_MANUAL_LOCK;
      else if(LimitBreached(m_monthly_loss_limit_pct, m_simulated_monthly_pnl_pct))
         state = PHASE1_RISK_LOCKED_MONTHLY;
      else if(LimitBreached(m_weekly_loss_limit_pct, m_simulated_weekly_pnl_pct))
         state = PHASE1_RISK_LOCKED_WEEKLY;
      else if(LimitBreached(m_daily_loss_limit_pct, m_simulated_daily_pnl_pct))
         state = PHASE1_RISK_LOCKED_DAILY;
      else if(!RiskAllowed(requested_risk_pct))
         state = PHASE1_RISK_MANUAL_LOCK;

      risk.risk_ok = (state == PHASE1_RISK_NORMAL);
      return state;
   }

private:
   bool LimitBreached(const double loss_limit_pct, const double simulated_pnl_pct) const
   {
      if(loss_limit_pct <= 0.0)
         return false;
      return simulated_pnl_pct <= -MathAbs(loss_limit_pct);
   }
};

#endif

#ifndef PHASE1_RISK_MQH
#define PHASE1_RISK_MQH

class CPhase1RiskGate
{
private:
   double m_max_spread_points;
   double m_max_risk_pct;

public:
   void Configure(const double max_spread_points, const double max_risk_pct)
   {
      m_max_spread_points = max_spread_points;
      m_max_risk_pct = max_risk_pct;
   }

   bool SpreadAllowed(const double spread_points) const
   {
      return spread_points >= 0.0 && spread_points <= m_max_spread_points;
   }

   bool RiskAllowed(const double requested_risk_pct) const
   {
      return requested_risk_pct > 0.0 && requested_risk_pct <= m_max_risk_pct;
   }
};

#endif

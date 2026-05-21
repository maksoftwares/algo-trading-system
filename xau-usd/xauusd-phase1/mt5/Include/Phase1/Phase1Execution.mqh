#ifndef PHASE1_EXECUTION_MQH
#define PHASE1_EXECUTION_MQH

#include <Phase1/Phase1Types.mqh>

class CPhase1ExecutionGuard
{
private:
   double m_configured_spread_cap;
   double m_spreads[20];
   int m_count;
   int m_next_index;

public:
   void Configure(const double configured_spread_cap)
   {
      m_configured_spread_cap = configured_spread_cap;
      m_count = 0;
      m_next_index = 0;
      ArrayInitialize(m_spreads, 0.0);
   }

   void RecordSpread(const double spread_points)
   {
      if(spread_points < 0.0)
         return;
      m_spreads[m_next_index] = spread_points;
      m_next_index = (m_next_index + 1) % 20;
      if(m_count < 20)
         m_count++;
   }

   Phase1ExecutionState Evaluate(const Phase1MarketSnapshot &snapshot) const
   {
      if(!snapshot.symbol_tradeable)
         return PHASE1_EXECUTION_SYMBOL_NOT_TRADEABLE;
      if(!snapshot.tick_ok || snapshot.stale_seconds > 30)
         return PHASE1_EXECUTION_STALE_TICK;
      if(snapshot.spread_points > DynamicSpreadLimit())
         return PHASE1_EXECUTION_SPREAD_TOO_HIGH;
      return PHASE1_EXECUTION_OK;
   }

   double DynamicSpreadLimit() const
   {
      if(m_count < 5)
         return m_configured_spread_cap;

      double median = MedianSpread();
      double dynamic_limit = MathMax(30.0, 1.5 * median);
      if(m_configured_spread_cap <= 0.0)
         return dynamic_limit;
      return MathMin(m_configured_spread_cap, dynamic_limit);
   }

private:
   double MedianSpread() const
   {
      double values[20];
      int copied = 0;
      for(int i = 0; i < m_count; i++)
      {
         values[copied] = m_spreads[i];
         copied++;
      }

      for(int i = 0; i < copied - 1; i++)
      {
         for(int j = i + 1; j < copied; j++)
         {
            if(values[j] < values[i])
            {
               double temp = values[i];
               values[i] = values[j];
               values[j] = temp;
            }
         }
      }

      if(copied <= 0)
         return m_configured_spread_cap;
      if((copied % 2) == 1)
         return values[copied / 2];
      return (values[(copied / 2) - 1] + values[copied / 2]) / 2.0;
   }
};

#endif

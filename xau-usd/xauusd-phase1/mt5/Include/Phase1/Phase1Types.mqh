#ifndef PHASE1_TYPES_MQH
#define PHASE1_TYPES_MQH

enum Phase1LifecycleState
{
   PHASE1_DISABLED = 0,
   PHASE1_DRY_RUN = 1
};

enum Phase1SignalDirection
{
   PHASE1_SIGNAL_NONE = 0,
   PHASE1_SIGNAL_LONG = 1,
   PHASE1_SIGNAL_SHORT = -1
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

string Phase1DirectionText(const Phase1SignalDirection direction)
{
   if(direction == PHASE1_SIGNAL_LONG)
      return "LONG";
   if(direction == PHASE1_SIGNAL_SHORT)
      return "SHORT";
   return "NONE";
}

#endif

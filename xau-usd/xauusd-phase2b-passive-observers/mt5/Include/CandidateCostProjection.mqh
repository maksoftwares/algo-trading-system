#ifndef CANDIDATE_COST_PROJECTION_MQH
#define CANDIDATE_COST_PROJECTION_MQH

#include "CandidateObserverCommon.mqh"

#define CANDIDATE_MEASURED_MEDIAN_SPREAD_POINTS 50.0
#define CANDIDATE_MEASURED_P95_SPREAD_POINTS 75.0
#define CANDIDATE_MEASURED_MAX_SPREAD_POINTS 180.0
#define CANDIDATE_NET_R_FLOOR_ASSUMPTION 0.15

double CandidateProjectedCostR(const double spread_points, const double stop_distance_points)
{
   if(stop_distance_points <= 0.0)
      return 0.0;
   return spread_points / stop_distance_points;
}

void CandidateApplyCostProjection(CandidateObservation &observation)
{
   observation.measured_median_spread_points = CANDIDATE_MEASURED_MEDIAN_SPREAD_POINTS;
   observation.measured_p95_spread_points = CANDIDATE_MEASURED_P95_SPREAD_POINTS;
   observation.projected_net_r_floor_assumption = CANDIDATE_NET_R_FLOOR_ASSUMPTION;
   observation.projected_cost_r_median = CandidateProjectedCostR(CANDIDATE_MEASURED_MEDIAN_SPREAD_POINTS, observation.stop_distance_points);
   observation.projected_cost_r_p95 = CandidateProjectedCostR(CANDIDATE_MEASURED_P95_SPREAD_POINTS, observation.stop_distance_points);

   if(observation.stop_distance_points <= 0.0)
   {
      observation.cost_feasible = false;
      if(observation.block_reason == "not_evaluated")
         observation.block_reason = "no_projected_stop";
      return;
   }

   observation.cost_feasible = observation.projected_cost_r_p95 <= 0.30 && observation.projected_cost_r_median <= 0.30;
   if(!observation.cost_feasible)
   {
      observation.candidate_state = "STRUCTURAL_COST_RISK";
      observation.block_reason = "measured_p95_cost_r_above_0_30";
   }
   else if(observation.block_reason == "not_evaluated")
   {
      observation.block_reason = "none";
   }
}

#endif

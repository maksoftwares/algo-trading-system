# Post-Run Verifier Repair

The first frozen experiment run completed before the independent verifier ran.
The verifier then stopped because `candidate_id` was both an index level and a
column label in its replay frame, making the sort ambiguous in pandas.

The repair resets the replay frame index before sorting. It does not change the
dataset, features, model, fitting population, thresholds, folds, acceptance
gates, predictions, or metrics. The contract is re-locked and the experiment is
rerun so every published artifact references the repaired verifier.

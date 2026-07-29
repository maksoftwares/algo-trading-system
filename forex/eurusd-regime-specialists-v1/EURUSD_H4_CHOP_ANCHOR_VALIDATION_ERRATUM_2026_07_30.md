# EURUSD H4 chop anchor validation verifier erratum

The first frozen execution correctly reproduced 349 rows and all numeric values but marked timestamp parity false. Investigation showed pandas represented regenerated signal/exit timestamps at millisecond resolution and CSV timestamps at microsecond resolution. `Series.equals` treats those dtypes as unequal even when every displayed instant is identical.

The verifier now normalizes both timestamp series to nanosecond UTC resolution before equality comparison. A synthetic regression test locks this behavior. No strategy parameter, source row, trade outcome, stress scenario, bootstrap seed, sample count, threshold, or gate changed.

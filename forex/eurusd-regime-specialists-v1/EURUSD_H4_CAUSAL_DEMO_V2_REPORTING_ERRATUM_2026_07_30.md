# EURUSD causal demo V2 reporting erratum

The first frozen outcome run reached the fail-closed condition in which no
side/regime component passed every admission gate. The runner raised an
exception before writing the already-computed variant metrics.

This erratum changes only that terminal reporting branch. It now writes the
unchanged frozen variant outcomes and failed checks, returns
`NO_STANDALONE_COMPONENT_PASSED`, and still refuses to assemble a portfolio.
Signal definitions, parameters, selection, admission gates, portfolio gates,
and the preregistration lock are unchanged.

# Phase 0R No-Tuning And Versioning Rules

Do not tune a candidate after seeing results.

Bad:

```text
d1_compression_h4_expansion_v0 failed, so change the ATR percentile from 30 to 40.
```

Good:

```text
Create d1_compression_h4_expansion_v1 with a new market-mechanics thesis, lock it before testing, and rerun all gates.
```

Allowed after lock:

- Correct coding mistakes that clearly diverge from the locked mechanical definition.
- Correct logging or report formatting errors that do not alter signal logic.
- Record the fix and preserve the original locked hypothesis hash.

Forbidden after lock:

- Parameter changes after seeing results.
- Adding filters after seeing results.
- Reclassifying the family after seeing results.
- Promoting a failed candidate through reinterpretation instead of evidence.

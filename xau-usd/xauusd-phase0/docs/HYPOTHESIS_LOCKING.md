# Hypothesis Locking

Phase 0 uses external SHA256 registration. The hypothesis markdown files do not store their own hash, which avoids a self-hash loop where adding the digest changes the file being hashed.

Required flow for real-data runs:

1. Complete every enabled hypothesis file.
2. Run `phase0 validate-hypotheses-complete`.
3. Run `phase0 hash-hypotheses --register --force` only before any result-producing run.
4. Run `phase0 hash-hypotheses` before matrix, decile, multisymbol, and run-all commands.

The manifest is written to `outputs/hashes/hypothesis_hash_manifest.csv` and stores expert name, hypothesis file path, SHA256, registration timestamp, file size, and current git commit when available.

If a hypothesis changes after results exist, do not silently overwrite the manifest. Create a new hypothesis version, register that version, and treat previous results as exploratory unless there is a clean audit trail proving the run happened after registration.

## Required Research Metadata

Every new hypothesis must declare:

- mechanic family
- entry / decision timeframe
- expected median hold bars in M5-equivalent bars
- expected median hold hours
- expected decisions per week
- whether it qualifies as timeframe diversification

Timeframe diversification is classified by the entry and decision cadence, not by the source of a reference level. A weekly level with M5 entries remains an intraday execution candidate.

## Sequential Testing Rule

Every candidate that enters the non-empty matrix ledger remains in future D2 Reality Check / SPA runs unless there is a documented data-quality reason to exclude it.

If the non-empty matrix-ledger candidate universe reaches 30 candidates, Phase 2 authorization requires Reality Check / SPA to clear alpha = 0.01 instead of alpha = 0.10. This avoids letting a growing candidate universe weaken the statistical evidence chain.

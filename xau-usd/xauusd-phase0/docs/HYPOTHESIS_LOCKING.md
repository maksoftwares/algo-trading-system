# Hypothesis Locking

Phase 0 uses external SHA256 registration. The hypothesis markdown files do not store their own hash, which avoids a self-hash loop where adding the digest changes the file being hashed.

Required flow for real-data runs:

1. Complete every enabled hypothesis file.
2. Run `phase0 validate-hypotheses-complete`.
3. Run `phase0 hash-hypotheses --register --force` only before any result-producing run.
4. Run `phase0 hash-hypotheses` before matrix, decile, multisymbol, and run-all commands.

The manifest is written to `outputs/hashes/hypothesis_hash_manifest.csv` and stores expert name, hypothesis file path, SHA256, registration timestamp, file size, and current git commit when available.

If a hypothesis changes after results exist, do not silently overwrite the manifest. Create a new hypothesis version, register that version, and treat previous results as exploratory unless there is a clean audit trail proving the run happened after registration.

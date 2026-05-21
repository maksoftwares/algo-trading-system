# Reference Status

The original reviewer prompt expected these reference files:

- `reference/xauusd_phase0_codex_implementation_spec.md`
- `reference/PHASE0_STATISTICAL_STUDY_SPEC.md`
- `reference/PATH_TO_10.md`
- `reference/PLAN_V01_REVIEW_FINDINGS.md`
- `reference/xauusd_master_ea_plan_v0_3_phase0_first_review_ready.md`

These are missing reference documents in this local package. Until they are supplied, the active implementation references are:

- `CODEX_IMPLEMENTATION_SPEC.md`
- `../CODEX_PHASE0_REPO_COMPLETION_PROMPT.md`
- The committed Phase 0 config, hypothesis files, and policy docs in this package.

This README exists so `phase0 validate-reference` can distinguish a documented reference gap from an accidental missing-spec condition. Synthetic smoke tests are allowed with this status. Real-data final approval remains blocked until the evidence bundle and final verdict explicitly document the reference status.

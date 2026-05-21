# True Holdout Policy

The true holdout period is reserved for final pre-live review:

- Start: `2025-07-01T00:00:00Z`
- End: `2025-12-31T23:59:59Z`
- Unlock file: `docs/FINAL_HOLDOUT_UNLOCK_APPROVAL.md`
- Unlock CLI flag: `--unlock-true-holdout`

Normal Phase 0 workflows must not read the true holdout unless both the unlock file and CLI flag are present. Matrix windows end before the holdout. Longer decile and multisymbol windows are guarded and are trimmed or blocked unless explicitly unlocked.

Every generated result manifest now emits `outputs/manifests/PHASE0_RUN_CONTEXT.json` with:

- `true_holdout_period_start`
- `true_holdout_period_end`
- `true_holdout_unlocked`
- `true_holdout_unlock_file`
- `true_holdout_unlock_file_present`
- `true_holdout_overlap_detected`

If a result touches the true holdout without the required unlock, that result must be treated as invalid and must not approve Phase 1 or EA work.

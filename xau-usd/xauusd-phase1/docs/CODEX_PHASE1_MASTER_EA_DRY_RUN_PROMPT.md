# Codex Phase 1 Master EA Dry-Run Prompt

Use this prompt for the active Phase 1 dry-run build.

```text
Implement the XAUUSD Phase 1 Master EA dry-run shell according to docs/PHASE1_MASTER_EA_DRY_RUN_SPEC.md.

Current boundary:
- dry-run only
- no broker-side execution
- no active expert
- no live position management
- one decision_log.csv row per new M5 bar
- dashboard visible on chart
- safety audit must pass

Build modules incrementally:
1. Common enums and types
2. Logger
3. Server time validator
4. Market data engine
5. Session engine
6. Feature engine
7. News guard
8. Risk manager
9. Execution guard
10. Regime router
11. Magic number allocator
12. Expert lifecycle manager
13. Dashboard
14. MasterEA orchestration

Keep every expert disabled or dry-run only. The approved future expert list contains `breakout_retest` only.

Required verification:
- static safety audit
- unit/static tests
- MetaEditor compile with zero warnings
- MT5 portable launch on demo
- decision log writes rows across M5 bars
```

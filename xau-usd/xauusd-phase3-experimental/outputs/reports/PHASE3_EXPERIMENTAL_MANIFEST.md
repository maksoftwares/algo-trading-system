# Phase 3 Experimental Manifest

This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.

Overall status: DIRTY_WORKTREE

## Snapshot

| Field | Value |
| --- | --- |
| Created at UTC | 2026-05-28T12:22:47.376758Z |
| Commit | 8cc2b76 |
| Simulation status | EXPERIMENTAL_COST_SUSPEND_SCENARIO |
| Safety status | PASS |
| Working tree clean | False |
| Boundary | repo_only_no_mt5_deployment_no_phase2_status_change |

## Working Tree

```text
M .github/workflows/phase3_experimental.yml
 M status.html
 M xau-usd/xauusd-phase1/scripts/generate_project_status_page.py
 M xau-usd/xauusd-phase1/scripts/verify_status_dashboard_freshness.py
 M xau-usd/xauusd-phase1/tests/test_project_status_page.py
 M xau-usd/xauusd-phase3-experimental/README.md
 M xau-usd/xauusd-phase3-experimental/docs/PHASE3_EXPERIMENTAL_SCOPE.md
 M xau-usd/xauusd-phase3-experimental/outputs/reports/PHASE3_COMPLETION_AUDIT.json
 M xau-usd/xauusd-phase3-experimental/outputs/reports/PHASE3_COMPLETION_AUDIT.md
 M xau-usd/xauusd-phase3-experimental/outputs/reports/PHASE3_COST_GATE_REVIEW.json
 M xau-usd/xauusd-phase3-experimental/outputs/reports/PHASE3_COST_MODE_COMPARISON.json
 M xau-usd/xauusd-phase3-experimental/outputs/reports/PHASE3_EXPERIMENTAL_MANIFEST.json
 M xau-usd/xauusd-phase3-experimental/outputs/reports/PHASE3_EXPERIMENTAL_MANIFEST.md
 M xau-usd/xauusd-phase3-experimental/outputs/reports/PHASE3_EXPERIMENTAL_SAFETY_REPORT.json
 M xau-usd/xauusd-phase3-experimental/outputs/reports/PHASE3_EXPERIMENTAL_SIMULATION.json
 M xau-usd/xauusd-phase3-experimental/outputs/reports/PHASE3_EXPERIMENTAL_STATUS.json
 M xau-usd/xauusd-phase3-experimental/outputs/reports/PHASE3_EXPERIMENTAL_STATUS.md
 M xau-usd/xauusd-phase3-experimental/outputs/reports/PHASE3_FAMILY_DEDUP_AUDIT.json
 M xau-usd/xauusd-phase3-experimental/outputs/reports/PHASE3_PAPER_SHADOW_SUMMARY.json
 M xau-usd/xauusd-phase3-experimental/outputs/reports/PHASE3_SHADOW_LIFECYCLE_SUMMARY.json
 M xau-usd/xauusd-phase3-experimental/outputs/reports/PHASE3_SUSPEND_FAMILY_DECISION.json
 M xau-usd/xauusd-phase3-experimental/outputs/reports/PHASE3_SUSPEND_FAMILY_REVIEW.json
 M xau-usd/xauusd-phase3-experimental/outputs/review_bundles/PHASE3_EXPERIMENTAL_REVIEW_BUNDLE_LATEST.zip
 M xau-usd/xauusd-phase3-experimental/outputs/review_bundles/PHASE3_EXPERIMENTAL_REVIEW_BUNDLE_LATEST_manifest.json
 M xau-usd/xauusd-phase3-experimental/scripts/generate_phase3_completion_audit.py
 M xau-usd/xauusd-phase3-experimental/scripts/generate_phase3_experimental_manifest.py
 M xau-usd/xauusd-phase3-experimental/scripts/generate_phase3_experimental_status.py
 M xau-usd/xauusd-phase3-experimental/scripts/generate_phase3_review_bundle.py
 M xau-usd/xauusd-phase3-experimental/scripts/verify_phase3_experimental_artifacts.py
 M xau-usd/xauusd-phase3-experimental/tests/test_phase3_experimental.py
?? xau-usd/xauusd-phase3-experimental/scripts/generate_phase3_lifecycle_guard_experiment.py
```

## Source Hashes

| Name | Exists | Bytes | SHA256 | Path |
| --- | --- | ---: | --- | --- |
| phase1_status_summary | True | 3173 | d229c2e437f746c6b5dda493a4404ec01e4d496a4a074a2a330dac04eeb58b21 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_STATUS_SUMMARY.json |
| phase2_readiness_report | True | 6314 | 173c94d7d840e92d8e94c925c61279759406f8764ef4a4dc2163a56d0e65f2f3 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_READINESS_REPORT.md |
| phase3_cost_gate_review_csv | True | 1620 | 8b06d2f9ef6cca5d7ed79b419e0c4b56228aa26bf9c0c1a46352861368f5f4c3 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\reports\PHASE3_COST_GATE_REVIEW.csv |
| phase3_cost_gate_review_json | True | 8704 | aed5ab72892db0fcdf04df9743aa3422847292828766c65f273def070079c5c2 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\reports\PHASE3_COST_GATE_REVIEW.json |
| phase3_cost_gate_review_md | True | 3997 | 15b5d734e3f7f0330bc4070f0deee072519ea5d007b824ae291cd2f217f948d3 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\reports\PHASE3_COST_GATE_REVIEW.md |
| phase3_cost_mode_comparison_csv | True | 968 | 8871cbe938ed095941262f0faa747de5a981361097ff06de0b4ed61c545d5a0c | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\reports\PHASE3_COST_MODE_COMPARISON.csv |
| phase3_cost_mode_comparison_json | True | 3721 | 1036b59e2d20e5da1d37fbccd7261c4109517ed526e356f8f7a55243936b45f5 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\reports\PHASE3_COST_MODE_COMPARISON.json |
| phase3_cost_mode_comparison_md | True | 1566 | bfeb7ed113d9ebdff2bdc0227941d4488018292a8f893cee32bc61bd950669f2 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\reports\PHASE3_COST_MODE_COMPARISON.md |
| phase3_design_doc | True | 5696 | 7c9e77456fef038f1d9f4c3d2e66d222ca02a0c672b5fd6e7f2b1538b9b381ae | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\docs\PHASE3_EXECUTION_READINESS_DESIGN.md |
| phase3_family_dedup_audit_csv | True | 10613 | b9ef75d805625a9c48e95a30df53b948d8578944714706d596ca9b89b1832efc | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\reports\PHASE3_FAMILY_DEDUP_AUDIT.csv |
| phase3_family_dedup_audit_json | True | 35827 | 1fad680c66b88c27ca0ce72ffbb6ba87193aded03c7e1dd1cfea76f11298465b | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\reports\PHASE3_FAMILY_DEDUP_AUDIT.json |
| phase3_family_dedup_audit_md | True | 9827 | a757909c463b0b713f656231e8e3217c9dd9670e4816a58d5e2c56e6380e4018 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\reports\PHASE3_FAMILY_DEDUP_AUDIT.md |
| phase3_input_would_signals | True | 30485 | 2a91789bd7ba9d27df0aeda6f84b845f7993b449c250f7f29e0c021aefc17211 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_WOULD_SIGNAL_REVIEW.csv |
| phase3_lifecycle_guard_ledger_csv | True | 50392 | 1392cd8bd6a8d0195edab539db41bcd272af1d00ce2b8406bd43804a3029ca61 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\reports\PHASE3_LIFECYCLE_GUARD_LEDGER.csv |
| phase3_lifecycle_guard_summary_json | True | 2350 | f95c96b172f31f8291d54f58e0227afff0b3e610d8bdc254e3127d78fa61ff3d | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\reports\PHASE3_LIFECYCLE_GUARD_SUMMARY.json |
| phase3_lifecycle_guard_summary_md | True | 4288 | 4532b2a14b26e6df8545701bebe0d336baa9dc7f27407b93cebd3ecdd2dd41f9 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\reports\PHASE3_LIFECYCLE_GUARD_SUMMARY.md |
| phase3_observer_conflict_playbook | True | 1981 | 61871c85c043cbb34be86df874943c4cd31e2a4c6a2e9d03c3f922d60a4449be | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\docs\PHASE3_OBSERVER_CONFLICT_PLAYBOOK.md |
| phase3_paper_shadow_ledger_csv | True | 57729 | 2e2a8f2731b668033d5fb7aed4a7b6a16d19b9954c57a5133fb9bec3b15ba9e1 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\reports\PHASE3_PAPER_SHADOW_LEDGER.csv |
| phase3_paper_shadow_summary_json | True | 1985 | f473df80d39fe7eb6669d4a2a1036e8d98e8397525c0a14ff6d2338c373cb3d8 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\reports\PHASE3_PAPER_SHADOW_SUMMARY.json |
| phase3_paper_shadow_summary_md | True | 4089 | bc206aa99b87bb20e1a5a4ca45804880b6561c1b030c3c9a5e4691380b0058fe | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\reports\PHASE3_PAPER_SHADOW_SUMMARY.md |
| phase3_promotion_rollback_doc | True | 3888 | e3d44bd18cc479ccc62e7e7215d8e0f567482602a48e1995b757f5f0ce19b688 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\docs\PHASE3_PROMOTION_ROLLBACK_CRITERIA.md |
| phase3_real_implementation_prompt | True | 2031 | f66cc798ad386212e7674d4d37a6e51517be54f711af4a39c366e9fe51109dff | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\docs\PHASE3_REAL_IMPLEMENTATION_PROMPT.md |
| phase3_review_bundle_latest_manifest | True | 5707 | 1897a64aeb649decb74d58fb2db98d7c0ae2d757be3d4d95c935c99a12432942 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\review_bundles\PHASE3_EXPERIMENTAL_REVIEW_BUNDLE_LATEST_manifest.json |
| phase3_review_bundle_latest_zip | True | 86050 | bfe8473ad447cfc905dc0204e88a48f30b66990f0f782ee2f63a1e9ad37dbfde | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\review_bundles\PHASE3_EXPERIMENTAL_REVIEW_BUNDLE_LATEST.zip |
| phase3_safety_json | True | 664 | 23de30b8d2dbf444563a2c5599e628275f5125898820024144021a6def19136c | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\reports\PHASE3_EXPERIMENTAL_SAFETY_REPORT.json |
| phase3_scope_doc | True | 4966 | 41e4c862a5364dde15c2dfb1ee31383debfbd49302390b093101603f719fcfc5 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\docs\PHASE3_EXPERIMENTAL_SCOPE.md |
| phase3_shadow_lifecycle_ledger_csv | True | 64626 | ce5ea54158040a76bf27023055fb8712b3dc4655d74192d119bbbfdc74f1954b | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\reports\PHASE3_SHADOW_LIFECYCLE_LEDGER.csv |
| phase3_shadow_lifecycle_summary_json | True | 2337 | 630b1e606780369677bc5589aec061108356b1c684f6ae4174709ce505a45df9 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\reports\PHASE3_SHADOW_LIFECYCLE_SUMMARY.json |
| phase3_shadow_lifecycle_summary_md | True | 4203 | f84d6fc658720d81a8a535815401f9d3cc442633175c4db08d492a7dc7721f6c | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\reports\PHASE3_SHADOW_LIFECYCLE_SUMMARY.md |
| phase3_simulation_json | True | 2007 | f950f7776d21f1ebc2a67f919af6fee88d1a102a5654a8cbd97fce4cd71902f0 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\reports\PHASE3_EXPERIMENTAL_SIMULATION.json |
| phase3_suspend_family_csv | True | 6886 | 1e903aaeae6a8e3a3afe3d2370515a5f2badb66a6b9ce52599b79c73ffb90e38 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\reports\PHASE3_SUSPEND_FAMILY_ROWS.csv |
| phase3_suspend_family_decision_csv | True | 3733 | 31ba16d1d42b25b4dfcbcec38803741e583ed08a4b4483891055156a116f0a9d | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\reports\PHASE3_SUSPEND_FAMILY_DECISION.csv |
| phase3_suspend_family_decision_json | True | 10147 | d0b8d59d7c0f187dcd76023962e2e9d14ab2114beb0b4821fae2b2e6bcbc90ec | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\reports\PHASE3_SUSPEND_FAMILY_DECISION.json |
| phase3_suspend_family_decision_md | True | 3286 | 3fb2190bc92d2ed57d60480bb60e4c068121ab1b850b97b47d5179b279f38f27 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\reports\PHASE3_SUSPEND_FAMILY_DECISION.md |
| phase3_suspend_family_json | True | 2062 | 9ca1a1571840e9d6f72bb159067159e4268103455f7e8da021d21709c42c513a | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\reports\PHASE3_SUSPEND_FAMILY_REVIEW.json |
| phase3_suspend_family_md | True | 5010 | 936a00a0d791d69dc31e620b1768a8df6a4dc186d75b3ed5a11eb2db5d9e1787 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\outputs\reports\PHASE3_SUSPEND_FAMILY_REVIEW.md |
| script_artifact_verifier | True | 4369 | 51c56da8f6bf21b6f49cba9c22a6297b98ebe6c447de749d8810456342f049ac | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\scripts\verify_phase3_experimental_artifacts.py |
| script_cost_gate_review | True | 12615 | 2a34b873ac58faac702ab7b423c2fc02d6b4d377bbe2e1147af1e7994cfeac21 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\scripts\generate_phase3_cost_gate_review.py |
| script_cost_mode_comparison | True | 7963 | 811341903c70125ac37875cc3a9a3dcd16b71a319498fca743981d3d25e625e4 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\scripts\generate_phase3_cost_mode_comparison.py |
| script_family_dedup_audit | True | 8359 | 662d3f5ffc55cd60581b0026ee8bedadb443d85aa92b2b7eab74dd81a722c66b | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\scripts\generate_phase3_family_dedup_audit.py |
| script_lifecycle_guard_experiment | True | 17046 | b359ce26a1bda76e197ffe251712708651d6ae3e935bfce37cb260e75ab492b7 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\scripts\generate_phase3_lifecycle_guard_experiment.py |
| script_manifest | True | 11983 | f831bcf620228fe34d94c7533b5f443485020743e108f8618ccb1346791ea792 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\scripts\generate_phase3_experimental_manifest.py |
| script_paper_shadow_experiment | True | 17334 | 996ede552ab866ae1224d15241bfaff360c447d62c0d4efc5f0029c4f5ce9dff | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\scripts\generate_phase3_paper_shadow_experiment.py |
| script_review_bundle | True | 5077 | ac2cdddad8a7ea32731cba68ace434c1eae1996b974bb73b4664e25c9682a360 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\scripts\generate_phase3_review_bundle.py |
| script_safety | True | 6157 | 428ccb22a7ba55e5451a296f3a797bb5294321cfbd8d3b5e663cd479ac8bc9e5 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\scripts\audit_phase3_experimental_safety.py |
| script_shadow_lifecycle_experiment | True | 16600 | 870bf3e34c554beb2f2d0b945a8d35fc5d7a57607585966c9dbe503fd465bdf6 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\scripts\generate_phase3_shadow_lifecycle_experiment.py |
| script_simulation | True | 24283 | d6f88b84457a38d4545a214f659d11125802229cb3ce81b8964045b37a615e1c | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\scripts\simulate_phase3_from_would_signals.py |
| script_status | True | 24054 | 70e22ac7bdaec86e161e12ef71bdc3147ef15d77e9f554fe1ed38b84d45225eb | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\scripts\generate_phase3_experimental_status.py |
| script_status_dashboard_freshness | True | 6522 | 8c09dddb9cd8e9f1c8345fb3a5b3300e86a77aca85977fca143f599463ef4e11 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\scripts\verify_status_dashboard_freshness.py |
| script_suspend_family_decision | True | 7827 | 523c1b56a92de426f8e53e4cf0ea175f29841efd8ad16f5d117af1505a9a463f | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase3-experimental\scripts\generate_phase3_suspend_family_decision.py |

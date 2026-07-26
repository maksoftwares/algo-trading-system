# Expanded Candidate Dataset V4 Preregistration

V4 is a correction-only successor to Expanded Candidate Dataset V3. It is
frozen before artifacts are generated.

Complete Candidate Dataset V5 supplies the same `29,419` mechanical events and
`73,116` resolved event/action labels as before. Event identities, labels,
structural episodes, weights, chronological folds, overlap policy, and all
columns except `prior_events_1h` and `prior_events_4h` must match V3 exactly.
The two corrected columns use nanosecond-normalized causal windows and must not
exceed 12 and 48 events respectively.

The 3,752-row canonical population remains benchmark-only. The 117,534 journey
rows remain quarantined and cannot enter fitting. The same 58 causal feature
names and six purged July-to-July development folds are retained so a later
model evaluation can isolate the feature correction from unrelated changes.

V4 is a dataset only. It cannot authorize model or threshold fitting,
portfolio simulation, Python serving, ML shadowing, EA consumption, demo/live
trading, or broker action.

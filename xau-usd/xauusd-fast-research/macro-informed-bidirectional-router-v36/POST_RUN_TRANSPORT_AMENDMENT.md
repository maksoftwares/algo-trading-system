# V36 Post-Run Transport Amendment

The staged Git audit found that `* text eol=lf` would normalize Windows-generated
JSON and CSV evidence bytes and invalidate their recorded SHA-256 values after a
checkout. After all economics were complete, `.gitattributes` was changed to
`* -text` so Git preserves every artifact byte exactly.

This amendment changes no source logic, configuration, feature, action, label,
model, split, policy, gate, metric, result, or authorization. The static contract
was relocked, and only the manifest's contract-lock hash was refreshed. Economic
artifacts were not recalculated.

- Final contract-lock file SHA-256:
  `8f7831444854995c7b77854c388bfc762c64e1db450d61bb9f1feb69a5b1eaf6`.
- Refreshed manifest SHA-256:
  `6944d281b52054eec87bb926ba1fb2e01b3a695bb22ec950b9ccbef782e3c80d`.

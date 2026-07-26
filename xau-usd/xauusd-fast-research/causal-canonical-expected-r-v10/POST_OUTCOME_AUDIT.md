# V10 Post-Outcome Audit

V10 passed all 18 machine-registered historical gates and independently
verified. The post-run fold audit nevertheless found a weakness that prevents
V10 from being the final policy:

- F2020 had 548 fit rows and filtering reduced mean outcome by 0.068825R.
- F2021 had 817 fit rows and filtering reduced mean outcome by 0.059283R.
- F2022-F2025 had at least 1,162 fit rows and filtering improved mean outcome
  in every fold.

The preregistration's introductory purpose referred to improving every annual
fold, while the machine gate required positive selected expectancy in every
fold rather than positive uplift in every fold. The machine decision remains
reproducible, but this wording-versus-gate distinction is material.

V11 is therefore a separate, explicitly post-outcome development policy. It
requires at least 1,000 fit rows before V10 may filter candidates. Below that
availability threshold, ML abstains and retains every deterministic candidate.
V10 code, predictions, models, thresholds, result, and contract remain frozen.

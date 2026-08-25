# V13 Pre-Outcome Contract Correction

The preregistration commit `af5359f3` transcribed the rounded August V6 values
correctly in prose but used two incorrect higher-precision values in the JSON
acceptance thresholds.

Before any V13 historical or August policy replay was run, the thresholds were
corrected to the immutable frozen V6 result:

- minimum August PF: `1.1620572292953486`;
- maximum August closed drawdown: `56.6861810755616`.

No policy, input, other gate, or outcome changed. This correction ensures exact
V6 parity passes the intended "not worse than V6" rule.

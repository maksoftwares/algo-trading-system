# EURUSD H4 intrahour ladder pre-outcome implementation erratum

The first run stopped during intrahour bar construction before any signal,
trade, or performance outcome was produced. A zero-range bar denominator was
replaced with pandas `NA` and then cast to float, which pandas rejects.

The implementation now masks a zero denominator directly, producing floating
`NaN`. No strategy parameter, source row, signal rule, execution rule,
threshold, selection rule, or validation gate changed.

The next construction attempt also stopped before signals when pandas found
millisecond and microsecond UTC merge keys. All as-of merge keys are now
normalized to nanosecond UTC resolution. This changes representation only;
no market time or information-availability boundary moved.

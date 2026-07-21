# Two-Trade Capacity Audit V85

V85 measures whether the immutable V59/V60 candidate reservoir can reach an
average of two trades per weekday through scheduling alone. It does not change
signals, accept rejected trades, inspect alternative directions, or authorize
execution.

The upper bound counts every distinct broker-executable V57 add-on candidate
beside the unchanged V59 Core. It deliberately ignores overlap, risk, drawdown,
and economics. Failure of this optimistic bound proves that a scheduling change
cannot solve the remaining frequency gap.

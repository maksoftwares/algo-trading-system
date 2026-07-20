# V67 Capital Forward Handoff Watch Preregistration

## Purpose

V67 is operational infrastructure only. It periodically invokes the immutable
V27 one-shot evaluator so that sealed V24.1 and V26 validation or confirmation
artifacts are consumed when they become available.

## Frozen Behavior

1. Invoke V27 with the current Python interpreter and no strategy arguments.
2. Use V27's package directory as the child working directory.
3. Require a successful child exit and valid, self-hashed V27 status and any
   available stage-audit files.
4. Read V24.1 and V26 inventory metadata only for health reporting.
5. Poll every 300 seconds unless an operator supplies a positive override.
6. On any error, publish a fail-closed V67 status and continue only in watch
   mode.
7. Never alter a component contract, stage artifact, economic gate, strategy,
   portfolio router, or authority flag.

## Interpretation

V67 can report that the handoff process is healthy. It cannot report that a
component, portfolio, model, or account is profitable or ready for execution.
Those decisions remain exclusively inside the locked downstream packages.

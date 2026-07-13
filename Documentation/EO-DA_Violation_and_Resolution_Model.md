# EO-DA Violation and Resolution Model

Invariant failures create `InvariantViolationRecord` evidence with:

- invariant ID,
- violation code,
- severity,
- domain,
- blocking status,
- affected authority,
- affected workflow,
- affected truth domain,
- evidence,
- remediation owner,
- first observed,
- last observed,
- occurrence count,
- current status.

Repeated identical violations are deduplicated by stable signature while occurrence count and last observed time are updated.

Critical financial-truth violations cannot be manually marked passed. Resolution requires executable passing invariant evidence.


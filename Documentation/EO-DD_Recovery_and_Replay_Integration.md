# EO-DD Recovery and Replay Integration

`recover_nonterminal` scans journal state and marks nonterminal transactions as `RECOVERY_REQUIRED`.

Recovery is idempotent and evidence-preserving. Repeated recovery replay does not repair ledgers, synthesize missing fills, or force commit. It only makes the incomplete state visible for participant-authority recovery or quarantine.

The hash-chained journal supports replay integrity checks through `validate_integrity`.


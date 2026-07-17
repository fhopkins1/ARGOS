# EO-DF Campaign Admission Model

Campaign admission is fail-closed. EO-DF checks:
- immutable repository commit
- valid duration and metric interval
- clean working tree unless explicitly allowed
- live trading disabled
- accepted truth domain
- EO-DA critical invariants passing
- EO-DC operational state
- EO-DD journal health
- EO-DE fault hooks disabled except recovery campaigns
- persistence and recovery health
- no unresolved critical reconciliation discrepancy
- evidence storage and halt mechanism availability
- frozen pass criteria

Blocked campaigns produce an admission-failure report and do not claim executed duration.


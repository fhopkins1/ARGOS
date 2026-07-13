# EO-DE Determinism Report

EO-DE computes a determinism signature for each fault execution from stable evidence:
- fault id
- EO-DA verdict
- EO-DC decision
- EO-DD state
- recovery status
- resource boundedness
- pass criteria result

Timestamps, transient ids, and wall-clock values are excluded from the determinism signature.

Repeated campaign runs must produce one signature per fault id. Any fault with multiple signatures is listed in `nondeterministic_faults` and prevents a PASS verdict.


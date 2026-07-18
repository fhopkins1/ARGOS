# EO-DG Concurrency and Consistency Model

EO-DG supports consistency levels:
- strong snapshot
- authority-consistent
- eventual read model
- telemetry-only

Certification tests use deterministic quiescent state. Future controlled-concurrency campaigns should distinguish mutation caused by a read from authorized concurrent mutation.


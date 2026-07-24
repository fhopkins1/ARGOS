# BROKER-RM-002A-008 Reproduction Procedure

1. Extract the repository package ZIP into an empty directory.
2. From the extracted root, run `set PYTHONPATH=.;src;Scripts` on Windows PowerShell as `$env:PYTHONPATH='.;src;Scripts'`.
3. Run `python Scripts/broker_rm002a_007_final_certification.py` to reproduce the independent ECS-003 audit.
4. Run `python Scripts/broker_rm002a_008_reproducibility.py` to regenerate the canonical proof reconciliation package.

The runner does not require `.git` metadata; it falls back to a portable file-manifest digest.

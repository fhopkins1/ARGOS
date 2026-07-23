# AUTH-IC-001-011 Package-Bound Certification Closure Evidence

AUTH-IC-001-011 closes the Authorizations Office implementation certification path by making the delivered repository ZIP the sole authoritative candidate.

The executable package-bound runner is `src/argos/authorization_package_certification.py`, exposed through:

```powershell
python -m argos.authorization_certify --candidate <final-repository-zip> --output <isolated-output-directory>
```

The candidate identity is the SHA-256 digest of the complete repository ZIP bytes. The runner does not use Git state, branch state, the development checkout, inherited PASS records, miniature archives, or reconstructed candidate subsets as certification inputs.

The generated evidence package records:

- complete ZIP-entry inventory for every non-directory candidate artifact;
- fresh extraction and digest reconciliation;
- constitutional closure and traceability checks against the full candidate inventory;
- package-bound focused and regression artifact verification;
- structured Python compilation evidence from the extracted candidate;
- primary execution plus two subprocess clean-room executions;
- normalized clean-room comparison;
- final reconciliation requiring all component results to be PASS with zero unresolved, UNKNOWN, or NOT_EXECUTED results.

The focused tests are in `Tests/test_authorization_package_certification.py`.

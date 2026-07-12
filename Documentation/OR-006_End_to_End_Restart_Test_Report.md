# OR-006 End-to-End Restart Test Report

The focused restart test persists a canonical runtime after scheduled mission admission, reloads the durable backup from disk, recovers a fresh runtime, and verifies:

- mission ID survives,
- workflow ID survives,
- Workflow Execution Token context survives,
- paper operation is allowed,
- no broker orders or positions are fabricated.

Result: passed in `Tests.test_or006_enterprise_persistence`.

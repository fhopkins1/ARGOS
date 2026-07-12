# OR-006 Recovery Architecture

Recovery is handled by `DurableEnterprisePersistenceStore.recover_runtime()`.

Recovery steps:

1. Validate repository hash chains and entity identity.
2. Construct a fresh `CanonicalEnterpriseRuntime`.
3. Recover Scheduler and Mission Planner.
4. Recover Workflow Orchestrator and Workflow Execution Tokens.
5. Restore runtime continuity state.
6. Confirm broker, position, and Performance Truth evidence is present.
7. Start paper runtime only if no critical diagnostics exist.
8. Persist immutable recovery audit.

Recovery never fabricates missing evidence. Missing authoritative families are deferred.

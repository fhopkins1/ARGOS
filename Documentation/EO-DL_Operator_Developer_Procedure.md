# EO-DL Operator and Developer Procedure

1. View office inventory through EO-DL evidence or `OfficeLifecycleController.read_only_snapshot()`.
2. Confirm active offices have a workflow ID, token ID, proof domain, and activation authority.
3. Investigate orphan findings in `eo_dl_orphan_analysis.json`.
4. Suspend, quarantine, or retire offices through explicit lifecycle transitions only.
5. Confirm all source offices return to Dormant after handoff.
6. For new components, decide first whether the component is an office, service, gateway, registry, adapter, or store.
7. Register true offices with classification, lifecycle, activation authority, ingress, egress, proof domains, token requirements, recovery policy, and Dormancy policy.
8. Add lifecycle, activation, Dormancy, recovery, and read-side tests before claiming production certification.

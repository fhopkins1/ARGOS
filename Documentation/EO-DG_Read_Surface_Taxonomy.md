# EO-DG Read Surface Taxonomy

EO-DG classifies read surfaces as pure snapshots, derived projections, cached reads, historical queries, replay views, Decision Laboratory views, health checks, status checks, streaming or polling reads, administrative inspection, or mutating commands falsely exposed as reads.

The prohibited category is `MUTATING_COMMAND_FALSELY_EXPOSED_AS_READ`; the guard rejects those surfaces before execution.


# EO-DG Health, Cache, API, and Cost Boundaries

Health checks report state and must not repair it.

Cache reads may update only permitted ephemeral access metadata. Cache misses must not create analytical work or alter authoritative decisions.

Reads must not invoke external APIs or increase authoritative Cost Governor totals.


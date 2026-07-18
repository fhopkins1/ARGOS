# EO-DB Persistence and Recovery Bridge Model

Each bridge declares persistence and recovery behavior. Certified or conditional bridges must be durable or reconstructable, idempotent across retry, and safe across restart boundaries.

Current recovery evidence is conditional for Persistence -> Recovery and Recovery -> Canonical Runtime. Remaining partial lifecycle bridges require deeper EO-DI evidence before final operational certification.


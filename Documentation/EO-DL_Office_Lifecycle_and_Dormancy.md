# EO-DL Office Lifecycle and Dormancy

EO-DL introduces `OfficeLifecycleController`, `OfficeRegistry`, and immutable office definitions. The lifecycle model distinguishes office existence from active authority and makes Dormancy the default state.

Supported states include `UNINITIALIZED`, `DORMANT`, `ACTIVATION_PENDING`, `ACTIVE`, `HANDOFF_PENDING`, `WAITING_EXTERNAL`, `SUSPENDED`, `RECOVERY_PENDING`, `QUARANTINED`, `RETIRING`, `RETIRED`, and `FAILED`.

Activation requires an explicit authority such as a canonical bridge, scheduler, duty officer, Commander, recovery procedure, replay harness, or test harness. Ownership-bearing offices require a valid token. Dormant offices cannot perform active workflow mutation.

EO-DL evidence is generated under `Documentation/EO-DL_Evidence/`. The formal verdict is `INCOMPLETE` while unresolved/future endpoint offices remain disabled or untraced.

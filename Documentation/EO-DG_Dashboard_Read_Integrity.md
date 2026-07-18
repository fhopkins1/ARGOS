# EO-DG Dashboard Read Integrity

Dashboard rendering and polling must consume snapshots, read models, pure projections, and nonauthoritative telemetry.

Dashboard reads must not schedule missions, process broker events, enroll EO-CK, evaluate exits in mutation mode, create Closed Position Truth, ingest Performance Truth, run recovery, invoke external APIs, or create cost.


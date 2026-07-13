# EO-DD EO-DA and EO-DC Integration

EO-DD requires EO-DC approval before registering transaction intent. Rejected, inconclusive, revoked, or missing EO-DC decisions fail closed.

EO-DD integrates with EO-DA by using the broker-position invariant monitor for reconciliation. Blocking EO-DA discrepancies block EO-DD commit.

Live and non-paper truth domains are rejected. EO-DD does not bypass EO-DA invariant enforcement and does not promote truth independently of EO-DC.


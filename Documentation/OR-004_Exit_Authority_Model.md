# OR-004 Exit Authority Model

## Authority Boundary

Exit recommendations and exit authorizations are separate. A recommendation can describe why a position should be closed or reduced, but it cannot mutate quantity or submit a broker order.

## Authorization Requirements

An exit authorization requires:

- A known active position.
- A linked exit decision record.
- A decision object with operational provenance.
- Risk approval ID.
- Policy approval ID.
- A requested quantity that does not exceed available quantity.

## Broker Submission Requirements

`submit_authorized_exit()` requires:

- An existing authorized exit record.
- No prior broker order for the same authorization.
- A workflow token currently owned by Trader.
- OR-003 broker acceptance and fill/settlement.

## State Changes

Authorization reserves quantity and moves the position to `exit_pending`. Broker-confirmed sell fills reduce quantity. Full closure requires the registry quantity to reach zero and closed-position truth to reconcile the round trip.

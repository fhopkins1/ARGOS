# EO-DC Persistence and Recovery Integration

Durable operational persistence now records an EO-DC promotion decision inside `operational_truth_envelope.eo_dc_promotion_decision`.

Persistence rejects missing, invalid, proof, simulation, live, revoked, expired, unapproved, wrong-authority, and wrong-scope envelopes.

Recovery may restore prior envelopes. Recovery does not create approval merely because an object was persisted.


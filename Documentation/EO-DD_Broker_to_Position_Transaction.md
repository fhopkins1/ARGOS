# EO-DD Broker to Position Transaction

Broker-fill coordination uses `coordinate_broker_fill`.

Required participants:
- Paper Broker
- Position Registry
- Performance Truth
- Historian

Preconditions:
- EO-DC approval is present
- truth domain is `PAPER`
- live trading remains disabled

Postconditions:
- broker fill has position lineage
- performance truth is preserved
- historian evidence is preserved

EO-DD records this chain but does not create the broker fill or mutate the Position Registry.


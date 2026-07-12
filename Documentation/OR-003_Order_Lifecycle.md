# OR-003 Order Lifecycle

The implemented lifecycle is:

Created -> Validated -> Accepted -> Queued -> Working -> Partially Filled -> Filled -> Settled

Terminal alternatives are:

- Cancelled
- Rejected
- Expired
- Settled

Every lifecycle event is represented as a `BrokerEventRecord` with order ID, Decision Object ID, workflow ID, mission ID, workflow token, Trader identity, broker adapter, truth domain, execution mode, source market state, certification state, timestamp, and paper/live designation.

Supported order types are market, limit, stop, and stop-limit. Supported time in force values are day, GTC, IOC, and FOK. Unsupported values reject deterministically and are not converted.

Market orders require an executable paper market session. Non-executable limit and stop orders remain queued or working and do not fabricate fills.


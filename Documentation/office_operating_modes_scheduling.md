# Office Operating Modes & Scheduling

The Office Operating Modes & Scheduling system deterministically manages the operational lifecycle of every ARGOS organization and office.

## Operating Modes

Every office operates in exactly one mode:

- Dormant
- Event Driven
- Scheduled
- Business Hours
- Continuous Operation

## Commander Configuration

The dashboard supports configuration of:

- Operating mode
- Business hours
- Time zone
- Scheduled tasks
- Wake triggers
- Sleep triggers
- Runtime limits
- Resource budgets

## Lifecycle Controls

Offices can be activated by scheduled events, Commander requests, enterprise events, or critical alerts.

Offices can be suspended when workflows complete, business hours end, market conditions close relevant work, Commander requests suspension, or runtime limits expire.

## Analytics

The scheduler continuously publishes:

- Active offices
- Sleeping offices
- Runtime statistics
- CPU usage
- Memory usage
- Token consumption
- Queue length
- Estimated compute cost
- Scheduling efficiency
- Resource allocation
- Wake frequency

## Detection

The system detects:

- Runaway processes
- Schedule conflicts
- Resource exhaustion
- Missed activations
- Unexpected wake events
- Stalled offices
- Runtime violations

Every Commander scheduling action emits an Enterprise Activity Bus event so the operational lifecycle remains auditable and visible in the command center.

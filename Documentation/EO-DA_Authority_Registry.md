# EO-DA Authority Registry

The canonical registry is `constitutional_authority_registry()`.

## Summary

Registered authorities include Runtime Provider, Canonical Runtime, Scheduler, Mission Planner, Duty Officer, Workflow Orchestrator, Strategic Intelligence, Seeker, Analyst, Risk, Executive, Trader, Paper Broker, Position Registry, EO-CK, Surveillance, Exit Decision, Performance Truth, Closed Position Truth, Historian, Commander, Doctrine, Policy, Persistence, Replay, Communications Bus, Cost Governor, and API Gateway.

Each registry entry declares owned entities, permitted writes, prohibited writes, truth domains, persistence namespace, source implementation, construction site, and active status.

EO-DA uses this registry to detect duplicate owners, unknown owners, unauthorized writers, missing owners, and inactive required owners as future checks are added.


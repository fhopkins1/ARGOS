# 2. Executive Group

Executive-level orchestration, approval gates, strategic policy boundaries, and enterprise coordination interfaces.

## EO-011 Executive Group Framework

Commander Office, Executive mailboxes, Decision Queue, Decision Registry, and Command Decision Record generation live in `src/argos/executive`.

## EO-012 Commander Decision Engine

Commander decisions consume only Executive Briefing Packets and produce CDRs for approve, reject, resize, defer, and request-more-analysis paths.

## EO-013 Executive Workflow

Executive Workflow validates EBPs before Commander routing, verifies evidence and risk reports, detects contradictions and stale reports, and records deterministic routing logs.

## EO-014 Chief of Staff

Chief of Staff validates every EBP, rejects incomplete packets through Courier, and routes only complete packets to Commander.

## EO-015 Executive Dashboard

Executive Dashboard provides read-only status boards, queue displays, command tables, metrics, health reporting, and deterministic refresh over existing services.

## EO-016 Human Override and Kill Switch Framework

Human Override Service manages authorized override levels, pause/lockdown/replay/read-only/emergency controls, immutable override records, and audit events.

## EO-017 Executive Operational Readiness Review

Executive readiness verification certifies Executive Group and authorizes Group 3 Seeker implementation after checks pass.

# Commander Notification & Alert Center

The Commander Notification & Alert Center (CNAC) evaluates enterprise activity and delivers the right operational information to the Commander with deterministic priority, timing, and channel selection.

## Inputs

CNAC consumes normalized Enterprise Activity Bus events from:

- Executive Group
- Seeker Department
- Analyst Department
- Risk Office
- Trader Group
- Historian Group
- Librarian Group
- Academy
- Infrastructure
- Commander Interface

## Notification Classes

Every enterprise event is classified as:

- Notification
- Alert
- Warning
- Critical Event
- Emergency Event

## Priorities

Priorities are deterministic:

- Information
- Notice
- Warning
- Critical
- Emergency

## Delivery Channels

CNAC determines appropriate delivery through:

- Enterprise Dashboard
- Commander Activity Feed
- Desktop Notifications
- Push Notifications
- Email
- SMS
- Mobile Application

The current local dashboard records channel selection deterministically; external push, email, SMS, and mobile transports are represented as planned delivery channels and are not sent outside the local ARGOS runtime.

## Briefings

CNAC generates recurring Commander briefings:

- Morning Briefing
- Midday Summary
- Market Close Summary
- Daily Enterprise Report
- Weekly Operational Review
- Monthly Enterprise Assessment

## Monitoring

CNAC reports notification volume, delivery success, alert response time, escalation accuracy, notification latency, acknowledged notifications, escalated notifications, duplicate notifications, alert flooding, delivery failures, escalation failures, missed critical events, and priority classification errors.

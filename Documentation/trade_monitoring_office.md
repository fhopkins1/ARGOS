# EO-058 Trade Monitoring Office

## Purpose

The Trade Monitoring Office (TMO) is the Trader Group operations center. It continuously monitors active orders, execution progress, open positions, broker connectivity, market status, system health, execution throughput, and enterprise alerts without determining trades, executing trades, or modifying positions.

## Deterministic Responsibilities

- Consume deterministic monitoring snapshots from Order Management, Broker Integration, Position Management, Execution Quality, Risk, and market/system health feeds.
- Detect stalled orders, missing broker responses, unexpected position changes, duplicate executions, communication failures, broker disconnects, market halts, position limit violations, excessive latency, data feed interruptions, degraded infrastructure, and execution failures.
- Generate Trade Monitoring Reports, Trade Monitoring Dashboards, and Trade Monitoring Case Files.
- Preserve operational timelines for order events, position events, broker events, market events, infrastructure events, and alert events.
- Notify the Executive Group for critical and emergency alerts.
- Persist every generated artifact through Foundation persistence and audit services.

## Alert Priorities

TMO supports deterministic alert priorities:

1. Information
2. Notice
3. Warning
4. Critical
5. Emergency

Critical and emergency alerts are marked for Executive Group notification.

## Produced Artifacts

- `TRADE_MONITORING_REPORT`
- `TRADE_MONITORING_DASHBOARD`
- `TRADE_MONITORING_CASE`
- `TradeMonitoringSystemPrompt`
- `OperationalTimelineEvent`
- `TradeMonitoringAlert`

## Interfaces

TMO consumes `TradeMonitoringSnapshot` objects containing:

- Managed order records
- Position records
- Portfolio state
- Broker health records
- Market status
- System health
- Risk status
- Execution quality status

TMO returns persisted `OperationalContract` artifacts and never mutates orders, positions, broker records, or market data.

## Governance Boundaries

TMO may detect, report, escalate, dashboard, and preserve operational evidence. It may not determine what should be traded, execute trades, modify positions, suppress anomalies, discard monitoring history, or bypass Foundation audit and persistence services.

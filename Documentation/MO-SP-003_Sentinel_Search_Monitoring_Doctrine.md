# MO-SP-003 Sentinel Search and Monitoring Doctrine

## 1. Sentinel Monitoring Philosophy

The Sentinel detects potentially material change and emits deterministic alerts. It does not investigate, verify, interpret, analyze, rank opportunities, evaluate risk, recommend trades, or execute actions. It monitors only MO-SP-001 approved sources through Intelligence Office collection authority and routes material alerts to the proper workflow offices.

## 2. Monitoring Domains

The Sentinel monitors exchange status, sessions, halts, market-wide indices, volatility indices, owned/watchlist/candidate securities, ETFs, options activity, volume, volatility, liquidity, spreads, macro calendars, scheduled releases, Federal Reserve and Treasury events, earnings calendars, investor relations announcements, SEC filings, corporate actions, insider activity, regulatory notices, brokerage notifications, account events, portfolio state, execution anomalies, source health, API availability, data freshness, approved newswires, industry publications, and low-authority early-warning sources.

Each domain must identify source ID, monitored fields, polling class, cache rule, duplicate key, alert expiration, and evidence requirements before monitoring begins.

## 3. Trigger Algorithms

Every trigger record contains monitored field, observation window, baseline, threshold, persistence requirement, debounce interval, duplicate suppression window, severity, expiration, evidence, destination, and workflow priority.

Price movement: compare current official/authorized price to prior close, session open, 5-minute baseline, and 30-minute baseline. Critical is absolute move >= 10% or portfolio-owned move causing unrealized loss >= 5% of portfolio equity. High is >= 5%. Medium is >= 3%. Low is >= 1.5%.

Volume: abnormal when current 5-minute volume is >= 3x 20-session same-window median. Critical >= 10x, High >= 5x, Medium >= 3x.

Volatility: abnormal when realized 15-minute volatility >= 3x 20-session median. IV expansion/collapse alerts at +/- 25 percentage points or +/- 50% relative move.

Spread: widening when spread exceeds 3x 20-session median or 1% of midprice for liquid securities.

Persistence: price/volume/spread triggers require two consecutive observations except exchange halt, broker restriction, order failure, SEC filing, official release, and source outage triggers, which fire on first authoritative observation.

Debounce: same trigger key suppresses duplicate alerts for 15 minutes for market triggers, 60 minutes for filings/releases, and until state change for broker/order/exchange status.

## 4. Market Trigger Classes

Percentage price movement, absolute price movement, intraday volatility, overnight gap, abnormal volume, options activity, IV expansion/collapse, liquidity deterioration, spread widening, market halt, exchange notices, circuit breakers, opening auction abnormalities, and closing auction abnormalities all route to Sentinel alert queue. Halts, circuit breakers, broker restrictions, and owned-security severe price moves are Critical. Watchlist severe moves are High. Candidate-only medium moves are Medium.

## 5. Corporate Trigger Classes

Earnings release, guidance change, SEC filing, investor presentation, press release, dividend, split, reverse split, merger, acquisition, management change, bankruptcy filing, litigation announcement, regulatory investigation, credit rating action, and analyst event detection produce alerts without interpretation. Official issuer/regulatory events are High unless bankruptcy, trading suspension, merger, reverse split, or enforcement action, which are Critical. Analyst event detection is Informational unless paired with official source evidence.

## 6. Macroeconomic Trigger Classes

CPI, PPI, PCE, GDP, unemployment, payrolls, FOMC schedule, Treasury auctions, rate decisions, consumer confidence, manufacturing, housing, energy, commodity, and scheduled government publications trigger at official publication or revision. FOMC rate decisions, payrolls, CPI, emergency Fed actions, and Treasury auction failures are High; emergency central-bank events are Critical.

## 7. Portfolio Monitoring

Position exposure alerts fire at 10%, 20%, and 30% single-name concentration. Unrealized loss alerts fire at -2%, -5%, and -10% portfolio equity impact. Unrealized gain alerts are Informational at +5% and +10% position return. Cash/buying-power/margin/broker restriction/order anomaly alerts come only from broker-authoritative sources. Option expiration alerts fire at 5 trading days, 1 trading day, and same day; assignment-risk alerts require broker or OCC-supported evidence and are routed to Risk and Trader operations only.

## 8. Monitoring Cycle Architecture

Cycle order is source health, exchange status, broker/account state, owned securities, open orders, watchlist securities, candidate securities, scheduled calendars, filings/releases, newswire/industry sources, early-warning research sources, duplicate suppression, alert routing, evidence archive. Regular session cycle runs every 15 seconds for critical classes, 60 seconds for standard classes. Premarket/after-hours standard cycle is 120 seconds. Overnight/weekend/holiday cycle is 60 minutes except scheduled publications.

## 9. Cost Governance

Maximum 20 source calls per standard cycle, 100 per emergency cycle, 10 browser pages per investigation-triggered monitoring cycle, and zero acceptance of unapproved substitute sources. Batching is mandatory where the registered surface supports batch queries. Cache may suppress redundant retrieval only while freshness and provenance remain valid.

## 10. Alert Generation

Every alert contains alert ID, cycle ID, workflow ID, trigger ID, monitored domain, source ID, surface ID, observation IDs, publication/retrieval/evaluation timestamps, trigger value, baseline value, threshold, severity, duplicate key, expiration, confidence classification, evidence references, failure state if applicable, route destination, and no interpretation fields.

Confidence classes are `OBSERVED_PRIMARY`, `OBSERVED_LICENSED`, `CORROBORATED`, `LOW_AUTHORITY_LEAD`, `UNKNOWN`, `STALE`, `CONFLICTED`, and `UNAVAILABLE`.

## 11. Alert Prioritization

Critical: exchange halt/resumption, circuit breaker, broker order failure, broker restriction, owned-security >= 10% move, margin restriction, bankruptcy, enforcement action, emergency market closure, source outage affecting critical owned security.

High: owned/watchlist >= 5% move, official filing/release, earnings/guidance, merger/acquisition, macro release, abnormal options >= 5x, volume >= 5x.

Medium: candidate >= 3% move, volume >= 3x, spread widening, delayed official release, reference data conflict.

Low: watchlist minor moves, source-health degradation, noncritical duplicate publication.

Informational: analyst event detection, successful calendar refresh, reference update, early-warning lead.

## 12. Escalation Rules

Wake Commander for Critical alerts. Wake Intelligence for any alert needing fresh collection. Wake Seeker for evidence acquisition after authorized investigation request. Notify Risk for broker, margin, concentration, regulatory, litigation, bankruptcy, and portfolio loss alerts. Trader is notified only for broker/order/position execution-critical alerts and never for general research. Duplicate alerts are suppressed by duplicate key and retained as evidence. Monitoring terminates when source status is suspended, budget exhausted, market state prohibits class, or workflow closes.

## 13. Failure Doctrine

Source unavailable, API outage, stale data, delayed publication, malformed response, authentication failure, rate limiting, conflicting observations, missing observations, and network outage produce explicit `UNKNOWN`, `UNAVAILABLE`, `STALE`, `CONFLICTED`, or `INCOMPLETE` alert/failure records. Sentinel never invents continuity or assumes no event occurred.

## 14. Evidence Preservation

Mandatory evidence: observation time, publication time, retrieval time, trigger value, baseline value, source, surface, monitored fields, threshold, cache state, duplicate suppression state, cycle ID, alert ID, registry version, query parameters, response digest, raw evidence reference, and failure state.

## 15. Synthetic Truth Prevention

Open-ended searching, interpretation, causal conclusions, predictions, inferred trigger values, assumed observations, guessed prices, guessed filings, guessed market status, guessed broker state, fabricated alerts, conflicting-alert suppression, estimates replacing missing data, and language-model memory as evidence are prohibited. Unavailable observations remain `UNKNOWN`, `UNAVAILABLE`, `STALE`, `CONFLICTED`, or `INCOMPLETE`.

## 16. Deterministic Acceptance Criteria

Identical inputs produce identical monitoring decisions. Every alert references objective thresholds, exact source, exact trigger, supporting evidence, cost accounting, duplicate state, and expiration. Monitoring failures are explicit. Costs are bounded by cycle rules. No missing observation can become a fabricated alert or silent non-alert.

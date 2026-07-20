# MO-SP-002 Intelligence Office Collection and Retrieval Doctrine

## 1. Institutional Mission

The Intelligence Office Collection System is the sole constitutional collection authority for external information unless another office has explicit constitutional retrieval authority. It may retrieve only from active MO-SP-001 source-registry entries and only for the source, surface, office, purpose, environment, fact type, field set, method, cost class, and evidence obligations authorized before retrieval begins.

It may collect observations, documents, structured records, official references, retrieval metadata, source-health evidence, cache records, outage records, and failure states. It may not analyze, forecast, rank truth, infer missing facts, recommend trades, fabricate continuity, or substitute unapproved sources.

## 2. Collection Categories

Continuous monitoring: triggered only by Sentinel-approved monitoring rules; authorized offices are Sentinel and Intelligence; permitted sources are active exchange, broker, market-data, and source-health records; frequency follows market-state schedule; stop on market close, source suspension, budget exhaustion, or explicit workflow termination; evidence must retain cycle ID, source ID, surface ID, observed fields, timestamps, cache status, cost, and result state.

High-frequency polling: triggered only during premarket, regular session, after-hours, emergency, or active workflow states; authorized for exchange status, trading halts, broker account state, and licensed market observations; stop on expiration, duplicate lock, unavailable source, or workflow completion.

Scheduled polling: triggered by registered publication calendars or registry freshness classes; authorized for SEC filings, economic releases, Federal Reserve events, issuer releases, corporate actions, and reference data; stop after mandatory sources complete, publication window closes, or source produces a constitutional failure state.

Publication calendar retrieval: triggered by known official release time; permitted sources are primary official publishers; retrieval begins five minutes before publication window and terminates at maximum freshness expiration or successful official retrieval.

Event-triggered retrieval: triggered by Sentinel alert, official feed notification, broker event, exchange notice, or workflow request; evidence must include triggering event and source authorization decision.

Workflow-triggered retrieval: triggered only by a valid Workflow Execution Token and approved request purpose; terminates when requested fact classes are collected, denied, or explicitly unavailable.

Bulk synchronization: triggered by registry-approved maintenance windows; permitted for reference data, historical archives, SEC index data, and broker statements; never wakes Sentinel without a separate material-change event.

Historical acquisition: permitted for reconstruction and backfill only; cannot establish current operational truth.

Formal investigation support: triggered by Seeker/Risk/Analyst authorized investigation requests; must preserve negative searches, unavailable searches, contrary evidence, and all source decisions.

Broker synchronization: triggered by order, fill, account, position, margin, or reconciliation workflow; broker authority is limited to broker-controlled facts.

Reference data synchronization: triggered by daily or static-reference schedules; direct to archive unless a separate material-change rule authorizes Sentinel wake.

## 3. Market State Scheduling

Market closed: collect exchange calendars, scheduled filings, issuer releases, economic calendars, broker reconciliation, and source health every 30 minutes; suspend high-frequency market prices and options polling.

Premarket: exchange status and halt checks every 60 seconds; owned/watchlist market observations every 120 seconds; broker account state every 5 minutes; scheduled releases at official windows.

Regular session: exchange status, halts, owned securities, broker order state, and account restrictions every 15 seconds; watchlist/candidate securities every 60 seconds; filings and issuer releases every 60 seconds; source health every 5 minutes.

After-hours: exchange status and broker state every 120 seconds; issuer releases and filings every 60 seconds; market prices only when authorized by active after-hours workflow.

Weekends and exchange holidays: filings, official releases, reference data, broker statements, and source health every 60 minutes; market-price polling suspended except emergency authorization.

Emergency closure: exchange status every 30 seconds; broker restrictions every 60 seconds; all cost-sensitive nonessential retrieval suspended.

## 4. Information-Class Schedules

Real-time market observations use licensed provider API or stream, 15-second regular-session polling, real-time freshness, retry sequence `5s, 15s, 45s`, stop after three failed attempts or stale state.

Delayed market data uses licensed delayed provider, 5-minute polling, declared-delay freshness, retry `60s, 180s`, stop after stale designation.

Exchange status and trading halts use official exchange source, 15-second regular-session polling, near-real-time freshness, retry `5s, 15s, 45s`.

SEC filings use official API/repository/feed, 60-second publication-window polling, official acceptance-time freshness, retry `30s, 90s, 270s`.

Investor relations releases, earnings, and corporate actions use issuer official pages/feeds, 60-second event-window polling, event-driven freshness, retry `60s, 180s, 540s`.

Economic, Federal Reserve, Treasury, and regulatory releases use official government sources, official release-window polling, publication-scheduled freshness, retry `30s, 90s, 270s`.

Broker account, portfolio, and order reconciliation use broker API or statements, 15-second order-state polling during active execution and 5-minute account reconciliation, retry `5s, 15s, 45s`, stop on broker outage or authentication failure.

Daily reference data uses official/reference sources once daily after market close, static/daily freshness, retry `15m, 45m`.

Historical data uses official archives or approved providers during maintenance windows, historical freshness, no operational wake.

Early-warning information uses research-only sources, 5-minute research monitoring, never establishes truth or trade eligibility.

## 5. Retrieval Hierarchy

The hierarchy is official API, official machine-readable file, official RSS/event feed, official document repository, official web page, licensed institutional provider, approved secondary provider, browser source discovery. Movement down the hierarchy is permitted only when the higher source is registered for the fact type and produces `UNAVAILABLE`, `SOURCE_OFFLINE`, `AUTHENTICATION_FAILED`, `RATE_LIMITED`, `TIMEOUT`, or `INCOMPLETE` evidence. Secondary or discovery sources may never replace a required primary authority.

## 6. Structured Data Preference

Machine-readable official data is mandatory where registered. HTML retrieval is permitted only when no registered machine-readable surface exists or when the HTML page is the official publication. Browser automation is discovery-only unless the registered surface explicitly authorizes browser retrieval. OCR is permitted only for official documents with no machine-readable text and must retain image hash, OCR engine identity, and confidence metadata; OCR output is incomplete until reviewed by the appropriate downstream office.

## 7. Source Availability Doctrine

Availability verification records DNS/TLS status, authentication, authorization, rate-limit state, response code, content type, schema validity, payload completeness, digest, and source timestamp. Timeout is 10 seconds for low-latency sources, 30 seconds for official APIs, 60 seconds for document retrieval, and 180 seconds for bulk downloads. Malformed, partial, corrupted, stale, or unauthorized responses terminate current attempt and preserve failure evidence.

## 8. Retry Doctrine

Low-latency classes retry `5s, 15s, 45s`; official publication classes retry `30s, 90s, 270s`; document retrieval retries `60s, 180s, 540s`; bulk synchronization retries `15m, 45m, 135m`. No retrieval class may exceed three retries without a new scheduled collection event. Every retry must retain attempt ID, prior failure, timestamp, delay, and cost.

## 9. Caching Doctrine

Cache is owned by the Intelligence Office. Cache may be used only when provenance is complete, source permits caching, freshness remains valid, no newer authoritative observation exists, and the requesting purpose accepts cached evidence. Broker order state, account restrictions, live halt status, authentication failures, rate-limit status, and active emergency market status may never be satisfied from stale cache. Cache hits, misses, age, digest, source authorization, and invalidation reason are mandatory evidence.

## 10. Duplicate Suppression

Duplicate retrieval is suppressed by `(source_id, surface_id, fact_type, field_set, instrument, jurisdiction, workflow, publication_window)`. Suppression creates an evidence record rather than discarding the request. Revised publications, amended filings, replacement issuer notices, and broker corrections create new observations with lineage to the prior record.

## 11. Cost Governance

Zero-marginal public sources have no per-cycle cap beyond rate limits. Low-marginal public sources are capped at 50 requests per monitoring cycle. Metered and licensed-metered sources require workflow cost authorization and are capped by source registry cost class. Browser retrieval is capped at 10 pages per investigation unless Risk or Compliance authorizes escalation. Cost controls never authorize fabrication, unapproved fallback, or stale continuity.

## 12. Unknown-State Doctrine

Failure to establish a fact produces exactly one of `UNKNOWN`, `UNAVAILABLE`, `STALE`, `INCOMPLETE`, `CONFLICTED`, `PARTIALLY_RETRIEVED`, `SOURCE_OFFLINE`, `RATE_LIMITED`, `AUTHENTICATION_FAILED`, or `TIMEOUT`. No default price, timestamp, filing, broker state, or publication status may be created.

## 13. Required Evidence

Every retrieval preserves authorization request, authorization decision, workflow, office, source, surface, method, query parameters, start/completion timestamps, retry records, cache usage, response metadata, response digest, raw evidence reference, collection cost, completion state, failure state, final URL, redirect chain, and registry version.

## 14. Prohibited Behavior

Prohibited: guessing unavailable data, assuming publication success, replacing unavailable APIs, silent source substitution, retrieval outside authorized schedules, unauthorized browser searches, fabricated timestamps, fabricated continuity, undocumented retries, undocumented cache usage, undocumented source changes, accepting snippets as evidence, using model memory as evidence, and paper-source promotion into live.

## 15. Synthetic Truth Analysis

Missing source response can create false continuity; prevention is explicit failure state and no cached extension. Secondary commentary can imply primary facts; prevention is source-jurisdiction enforcement. Search snippets can appear evidentiary; prevention is discovery-only classification. Retry loops can hide outages; prevention is attempt cap and outage record. Cache reuse can hide staleness; prevention is freshness proof and invalidation record. Browser extraction can mutate source meaning; prevention is official-surface registration and raw evidence retention.

## 16. Acceptance Criteria

Every trigger, method, retry, cache rule, schedule, stop condition, failure state, evidence record, and cost boundary is predetermined above. Identical collection inputs produce identical authorization and retrieval decisions. Missing information can only become an explicit constitutional unknown/failure state. No developer, model, adapter, or operator may choose a source, method, retry, cache exception, or fallback outside this doctrine and MO-SP-001.

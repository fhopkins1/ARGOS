# EO-DF Loop and Task Uniqueness

EO-DF monitors thread and task growth as loop-uniqueness proxies in the laboratory harness.

Blocking conditions:
- duplicate production runtime loop
- duplicate Scheduler loop
- duplicate EO-CK loop
- duplicate Broker-processing loop
- duplicate Communications loop
- unbounded campaign workers

The targeted tests simulate duplicate-loop growth and verify the campaign fails.


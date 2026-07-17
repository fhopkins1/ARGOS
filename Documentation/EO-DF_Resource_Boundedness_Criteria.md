# EO-DF Resource Boundedness Criteria

Default pass criteria include:
- max memory growth units: 8
- max thread growth: 0
- max task growth: 2
- max queue growth: 2
- max message backlog: 4
- max cache growth: 4
- max scheduler drift: 50 ms
- max transaction journal growth per cycle: 4
- max checkpoint growth per cycle: 2
- idle API calls: 0
- total cost: 0.0
- live disabled required
- no read-only mutation
- no truth-domain contamination
- evidence hash required

Memory, thread, queue, API/cost, LAW VII, and read-only mutation breaches are blocking.


# EO-DD Commander and Operator Model

`commander_read_model` exposes:
- engine identity and EO-DD version
- transaction count
- blocked and recovery-required transactions
- journal integrity findings
- outbox depth
- transaction taxonomy
- Commander limitations

Commander can observe transaction status but cannot create fills, mutate positions, create Performance Truth, fabricate repairs, mark partial work complete, or enable live trading.


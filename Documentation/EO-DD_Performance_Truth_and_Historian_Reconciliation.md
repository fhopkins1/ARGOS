# EO-DD Performance Truth and Historian Reconciliation

Performance Truth and Historian are participants, not subordinate mutable stores. EO-DD requires their durable acknowledgments when a transaction type lists them as participants.

EO-DD does not create Performance Truth records and does not preserve Historian records itself. It records evidence references and output versions supplied by those authorities, then exposes the state to Commander read models.

Historian preservation remains a participant proof requirement before transaction completion where the taxonomy requires Historian.


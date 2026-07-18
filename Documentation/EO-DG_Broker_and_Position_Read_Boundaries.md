# EO-DG Broker and Position Read Boundaries

Broker reads may display existing orders, events, fills, cash, buying power, settlements, and rejection history. They may not submit orders, create fills, cancel orders, process delayed events, or settle state.

Position reads may display open/closed positions, derived unrealized P&L, health, surveillance summaries, and pending exits. They may not append history, mutate quantity, close positions, or change EO-CK enrollment.


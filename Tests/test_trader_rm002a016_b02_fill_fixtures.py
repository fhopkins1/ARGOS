from pathlib import Path
import hashlib
import json
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.position_registry import PositionRegistry  # noqa: E402
from argos.control_panel.position_surveillance_engine import PositionSurveillanceEngine  # noqa: E402
from argos.control_panel.position_exit_decision_engine import ExitDecisionEngine  # noqa: E402


def _fill(order: dict, *, fill_id: str | None = None, **overrides) -> dict:
    payload = {
        "fill_id": f"AUTH-FILL-{order['order_id']}" if fill_id is None else fill_id,
        "order_id": order["order_id"],
        "broker_event_id": f"AUTH-EVENT-{order['order_id']}",
        "workflow_id": order["workflow_id"],
        "account_id": order.get("account_id", ""),
        "portfolio_id": order.get("portfolio_id", ""),
        "symbol": order["symbol"],
        "side": order["side"],
        "quantity": float(order["filled_quantity"]),
        "price": float(order["average_fill_price"]),
        "timestamp": order.get("timestamp", "2026-07-24T14:30:00Z"),
        "candidate_digest": order.get("candidate_digest", "candidate-b02"),
        "fixture_execution_identifier": order.get("fixture_execution_identifier", "fixture-b02"),
        "owner": "Paper Broker",
        "producer": "TRADER-RM-002A-016-B02",
        "source": "authorized_simulator_event",
        "provenance": "canonical_order_to_broker_event_to_fill",
        "evidence_reference": f"raw/{order['order_id']}.json",
    }
    payload.update(overrides)
    payload["evidence_digest"] = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return payload


def _order(order_id: str, *, symbol: str = "SPY", side: str = "BUY", quantity: float = 5.0, price: float = 100.0, workflow_id: str = "WF-B02", decision_object_id: str = "DO-B02") -> dict:
    order = {
        "order_id": order_id,
        "workflow_id": workflow_id,
        "decision_object_id": decision_object_id,
        "symbol": symbol,
        "asset_type": "ETF",
        "side": side,
        "status": "FILLED",
        "filled_quantity": quantity,
        "average_fill_price": price,
        "mid_price": price,
        "timestamp": "2026-07-24T14:30:00Z",
        "account_id": "ACCT-B02",
        "portfolio_id": "PORT-B02",
        "candidate_digest": "candidate-b02",
        "fixture_execution_identifier": f"FIX-{order_id}",
    }
    order["fills"] = (_fill(order),)
    return order


class TraderRM002A016B02FillFixturesTests(unittest.TestCase):
    def test_valid_position_creation_mutation_and_lineage(self) -> None:
        registry = PositionRegistry()
        first = _order("B02-ORD-001", quantity=5, price=100.0)
        second = _order("B02-ORD-002", quantity=3, price=103.0)

        position = registry.create_from_execution(first, {"recommendation": "BUY", "targetPrice": 110.0, "stopLoss": 95.0})
        updated = registry.create_from_execution(second, {"recommendation": "BUY"})

        self.assertEqual(position.position_id, updated.position_id)
        self.assertEqual(8.0, updated.quantity)
        self.assertEqual(("AUTH-FILL-B02-ORD-001", "AUTH-FILL-B02-ORD-002"), updated.fill_ids)
        self.assertEqual(("B02-ORD-001", "B02-ORD-002"), updated.broker_order_ids)
        self.assertGreaterEqual(len(registry.snapshot()["positionHistory"]), 2)

    def test_partial_multiple_replay_recovery_surveillance_and_exit_paths_are_fill_backed(self) -> None:
        registry = PositionRegistry()
        partial = _order("B02-ORD-PARTIAL", quantity=2.5, price=99.0)
        partial["status"] = "PARTIALLY_FILLED"
        position = registry.create_from_execution(partial, {"recommendation": "BUY", "targetPrice": 104.0, "stopLoss": 96.0})

        replay = PositionRegistry()
        replayed = replay.create_from_execution(partial, {"recommendation": "BUY", "targetPrice": 104.0, "stopLoss": 96.0})
        recovery = PositionRegistry()
        recovered = recovery.create_from_execution(dict(partial), {"recommendation": "BUY", "targetPrice": 104.0, "stopLoss": 96.0})

        surveillance = PositionSurveillanceEngine().surveil(
            position_registry=registry,
            market_data_provider={"normalizedObjects": {"quotes": ({"symbol": "SPY", "bid": 103.99, "ask": 104.01, "last": 104.0},), "marketStatus": ({"status": "PAPER_OPEN"},)}},
            timestamp_utc="2026-07-24T15:00:00Z",
        )
        exit_state = ExitDecisionEngine().evaluate(
            position_registry=registry,
            position_surveillance={"latestSnapshots": surveillance["latestSnapshots"], "latestEscalations": ()},
            timestamp_utc="2026-07-24T15:01:00Z",
        )

        self.assertEqual(position.fill_ids, replayed.fill_ids)
        self.assertEqual(position.fill_ids, recovered.fill_ids)
        self.assertEqual(("AUTH-FILL-B02-ORD-PARTIAL",), position.fill_ids)
        self.assertTrue(surveillance["latestSnapshots"])
        self.assertTrue(exit_state["latestDecisions"])

    def test_missing_invalid_mismatched_and_stale_fills_fail_closed(self) -> None:
        cases = []
        base = _order("B02-ORD-NEG")
        no_fills = dict(base)
        no_fills.pop("fills")
        cases.append(("missing authoritative fill", no_fills))
        empty_id = _order("B02-ORD-EMPTY")
        empty_id["fills"] = (_fill(empty_id, fill_id=""),)
        cases.append(("empty authoritative fill", empty_id))
        malformed = _order("B02-ORD-MALFORMED")
        malformed["fills"] = (_fill(malformed, fill_id="BAD ID"),)
        cases.append(("malformed authoritative fill", malformed))
        unknown = _order("B02-ORD-UNKNOWN")
        unknown["fills"] = (_fill(unknown, fill_id="UNKNOWN-FILL-001"),)
        cases.append(("unknown authoritative fill", unknown))
        wrong_order = _order("B02-ORD-WRONG-ORDER")
        wrong_order["fills"] = (_fill(wrong_order, order_id="OTHER-ORDER"),)
        cases.append(("wrong order", wrong_order))
        wrong_symbol = _order("B02-ORD-WRONG-SYMBOL")
        wrong_symbol["fills"] = (_fill(wrong_symbol, symbol="QQQ"),)
        cases.append(("wrong instrument", wrong_symbol))
        wrong_workflow = _order("B02-ORD-WRONG-WF")
        wrong_workflow["fills"] = (_fill(wrong_workflow, workflow_id="WF-OTHER"),)
        cases.append(("wrong workflow", wrong_workflow))
        wrong_account = _order("B02-ORD-WRONG-ACCT")
        wrong_account["fills"] = (_fill(wrong_account, account_id="ACCT-OTHER"),)
        cases.append(("wrong account", wrong_account))
        wrong_portfolio = _order("B02-ORD-WRONG-PORT")
        wrong_portfolio["fills"] = (_fill(wrong_portfolio, portfolio_id="PORT-OTHER"),)
        cases.append(("wrong portfolio", wrong_portfolio))
        wrong_side = _order("B02-ORD-WRONG-SIDE")
        wrong_side["fills"] = (_fill(wrong_side, side="SELL"),)
        cases.append(("wrong side", wrong_side))
        bad_quantity = _order("B02-ORD-BAD-QTY")
        bad_quantity["fills"] = (_fill(bad_quantity, quantity=0),)
        cases.append(("invalid quantity", bad_quantity))
        bad_price = _order("B02-ORD-BAD-PRICE")
        bad_price["fills"] = (_fill(bad_price, price=0),)
        cases.append(("invalid price", bad_price))
        bad_timestamp = _order("B02-ORD-BAD-TIME")
        bad_timestamp["fills"] = (_fill(bad_timestamp, timestamp=""),)
        cases.append(("invalid timestamp", bad_timestamp))
        bad_source = _order("B02-ORD-BAD-SOURCE")
        bad_source["fills"] = (_fill(bad_source, source="PLACEHOLDER"),)
        cases.append(("invalid source", bad_source))
        bad_digest = _order("B02-ORD-BAD-DIGEST")
        fill = _fill(bad_digest)
        fill["evidence_digest"] = "not-the-digest"
        bad_digest["fills"] = (fill,)
        cases.append(("invalid digest", bad_digest))
        wrong_candidate = _order("B02-ORD-WRONG-CANDIDATE")
        wrong_candidate["fills"] = (_fill(wrong_candidate, candidate_digest="other-candidate"),)
        cases.append(("wrong candidate", wrong_candidate))

        for label, order in cases:
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    PositionRegistry().create_from_execution(order, {"recommendation": "BUY"})

    def test_duplicate_and_terminal_fill_mutations_fail_closed(self) -> None:
        registry = PositionRegistry()
        buy = _order("B02-ORD-DUP", quantity=4.0)
        position = registry.create_from_execution(buy, {"recommendation": "BUY"})
        with self.assertRaises(ValueError):
            registry.create_from_execution(buy, {"recommendation": "BUY"})

        registry.close_position(position.position_id, reason="controlled terminal close")
        sell = _order("B02-ORD-SELL-AFTER-CLOSE", side="SELL", quantity=1.0, workflow_id=buy["workflow_id"], decision_object_id=buy["decision_object_id"])
        with self.assertRaises(ValueError):
            registry.apply_sell_execution(sell)


if __name__ == "__main__":
    unittest.main()

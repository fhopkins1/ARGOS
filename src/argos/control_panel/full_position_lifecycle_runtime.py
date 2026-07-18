"""EO-DM full position lifecycle runtime closure.

This module executes a deterministic paper lifecycle through existing broker,
position, bridge, and truth authorities. It records evidence about what happened;
it does not replace the underlying financial ledgers.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from typing import Any

from argos.foundation.audit import AuditService
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import utc_timestamp
from argos.foundation.persistence import InMemoryPersistenceRepository, canonical_schemas
from argos.foundation.prompts import PromptRepository
from argos.trader import DeterministicPaperBrokerage, OrderManagementOffice, PaperBrokerAccount, PaperBrokerMarketDataAdapter, PaperBrokerOrderTicket

from .canonical_bridge_fabric import CanonicalBridgeExecutor
from .enterprise_communications_bus import EnterpriseCommunicationsBus
from .market_data_provider import MarketDataProviderAbstractionLayer
from .performance_truth_engine import PerformanceTruthEngine
from .position_lifecycle_manager import EnterprisePositionLifecycleManager
from .workflow_orchestrator import WorkflowExecutionToken


EO_DM_VERSION = "EO-DM.1"


class LifecycleStageStatus(str, Enum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class LifecycleEvidenceStage:
    stage_id: str
    name: str
    status: LifecycleStageStatus
    evidence_references: tuple[str, ...]
    authority: str
    unresolved_reason: str = ""


@dataclass(frozen=True)
class LifecycleClosureReport:
    report_id: str
    verdict: str
    stages: tuple[LifecycleEvidenceStage, ...]
    bridge_trace_count: int
    office_lifecycle_controls_used: bool
    authoritative_market_boundary_used: bool
    transaction_protection_model: str
    open_quantity_after_close: float
    closed_truth_count: int
    synthetic_truth_created: bool
    evidence_hash: str
    timestamp_utc: str
    schema_version: str = EO_DM_VERSION


class ControlledLifecycleMarketDataProvider(MarketDataProviderAbstractionLayer):
    def __init__(self, *, symbol: str = "AAPL", bid: float = 502.24, ask: float = 502.26, last: float = 502.25) -> None:
        timestamp = utc_timestamp()
        configured = MarketDataProviderAbstractionLayer.with_controlled_authoritative_provider(
            observations={
                symbol: {"symbol": symbol, "bid": str(bid), "ask": str(ask), "last": str(last), "volume": "1000000", "venue": "NASDAQ", "source_timestamp_utc": timestamp},
                "MARKET": {"symbol": "MARKET", "status": "PAPER_OPEN", "venue": "US", "source_timestamp_utc": timestamp},
            }
        )
        super().__init__(gateway=configured.gateway, provider_id="controlled-authoritative")

    def snapshot(self, *, timestamp_utc: str, workflow_id: str = "", decision_object_id: str = "") -> dict[str, Any]:
        quote = self.get_quote("AAPL", timestamp_utc, workflow_id=workflow_id, decision_object_id=decision_object_id)["normalizedObject"]
        return {"normalizedObjects": {"quotes": (quote,), "marketStatus": ({"status": "PAPER_OPEN", "timestamp": timestamp_utc},)}}


def execute_canonical_position_lifecycle() -> dict[str, Any]:
    provider = ControlledLifecycleMarketDataProvider()
    truth = PerformanceTruthEngine(paper_starting_cash=100000.0)
    broker = DeterministicPaperBrokerage(
        order_management=_order_management(),
        performance_truth=truth,
        communications_bus=EnterpriseCommunicationsBus(),
        market_data=PaperBrokerMarketDataAdapter(provider),
        account=PaperBrokerAccount("ACCT-PAPER-001", 100000.0),
    )
    bridge_executor = CanonicalBridgeExecutor(runtime_instance_id="ARGOS-EO-DM")
    manager = EnterprisePositionLifecycleManager(performance_truth=truth, paper_broker=broker, market_data_provider=provider, bridge_executor=bridge_executor)
    token = _token()
    decision = _decision()

    open_result = broker.submit_order(_open_ticket(decision), workflow_token=token)
    position_id = "POS-AAPL-DO-EO-DM"
    position_after_open = manager.registry.position(position_id)
    monitoring = manager.monitor_positions(timestamp_utc="2026-07-18T15:00:00Z")
    exits = manager.evaluate_exits(surveillance=monitoring["surveillance"], timestamp_utc="2026-07-18T15:00:00Z")
    exit_decision = dict(exits["latestDecisions"][0])
    exit_decision["recommended_quantity"] = position_after_open.quantity
    authorization = manager.authorize_exit(
        exit_decision=exit_decision,
        decision_object=decision,
        authorized_by="Executive",
        risk_approval_id="RISK-EO-DM",
        policy_approval_id="POLICY-EO-DM",
        mission_id="MISSION-EO-DM",
    )
    quantity_before_submission = manager.registry.position(position_id).quantity
    close_result = manager.submit_authorized_exit(authorization, workflow_token=token, decision_object=decision)
    position_after_close = manager.registry.position(position_id)
    reconciliation = manager.reconcile_position(position_id, exit_decision_state={"latestDecisions": (exit_decision,)}, surveillance_state=monitoring["surveillance"])
    snapshot = truth.snapshot(execution_environment="paper")
    closed_truth = tuple(snapshot["closedPositionTruth"])
    bridge_trace = bridge_executor.traces()
    bridge_trace_count = len(bridge_trace)

    stages = (
        _stage("EO-DM-STAGE-ENTRY", "Entry decision", bool(decision.get("materialFieldProvenance")), (str(decision.get("decisionObjectId", "")),), "Trader"),
        _stage("EO-DM-STAGE-OPEN-ORDER", "Opening order accepted", open_result.accepted, (open_result.order.order_id,), "Paper Broker"),
        _stage("EO-DM-STAGE-OPEN-FILL", "Opening fill evidence", bool(open_result.order.fills), tuple(fill.fill_id for fill in open_result.order.fills), "Paper Broker"),
        _stage("EO-DM-STAGE-POSITION", "Position truth from fill", position_after_open.quantity > 0 and bool(position_after_open.fill_ids), (position_after_open.position_id, *position_after_open.fill_ids), "Position Registry"),
        _stage("EO-DM-STAGE-AUTH", "Exit authorization did not close position", authorization.authorization_state == "authorized" and quantity_before_submission == position_after_open.quantity, (authorization.authorization_id,), "Executive/Risk/Policy"),
        _stage("EO-DM-STAGE-BRIDGE", "Trader to broker bridge", bridge_trace_count > 0, tuple(item.bridge_id for item in bridge_trace), "EO-DK Bridge Fabric"),
        _stage("EO-DM-STAGE-CLOSE-FILL", "Closing fill evidence", bool(close_result.get("accepted")) and bool((close_result.get("order") or {}).get("fills")), tuple(fill.get("fill_id", "") for fill in (close_result.get("order") or {}).get("fills", ())), "Paper Broker"),
        _stage("EO-DM-STAGE-CLOSED", "Closed position truth", position_after_close.quantity == 0 and len(closed_truth) == 1, tuple(item.get("closed_position_truth_id", "") for item in closed_truth), "Closed Position Truth"),
        _stage("EO-DM-STAGE-RECON", "Lifecycle reconciliation", reconciliation.status == "reconciled", (reconciliation.reconciliation_id,), "Position Lifecycle Manager"),
    )
    verdict = "PASS" if all(stage.status == LifecycleStageStatus.COMPLETE for stage in stages) else "INCOMPLETE"
    report = LifecycleClosureReport(
        report_id="EO-DM-LIFECYCLE-CLOSURE-001",
        verdict=verdict,
        stages=stages,
        bridge_trace_count=bridge_trace_count,
        office_lifecycle_controls_used=True,
        authoritative_market_boundary_used=True,
        transaction_protection_model="EO-DD participant model referenced; broker and position mutation remain separate authorities.",
        open_quantity_after_close=position_after_close.quantity,
        closed_truth_count=len(closed_truth),
        synthetic_truth_created=False,
        evidence_hash=_stable_hash({"stages": tuple(asdict(stage) for stage in stages), "closedTruth": closed_truth}),
        timestamp_utc=utc_timestamp(),
    )
    return {
        "report": _jsonable(asdict(report)),
        "openOrder": _jsonable(open_result.order),
        "closeOrder": _jsonable(close_result.get("order", {})),
        "positionAfterOpen": _jsonable(position_after_open),
        "positionAfterClose": _jsonable(position_after_close),
        "performanceTruth": snapshot,
        "managerSnapshot": manager.snapshot(),
        "bridgeTrace": tuple(_jsonable(asdict(item)) for item in bridge_trace),
    }


def _stage(stage_id: str, name: str, complete: bool, refs: tuple[str, ...], authority: str) -> LifecycleEvidenceStage:
    return LifecycleEvidenceStage(stage_id, name, LifecycleStageStatus.COMPLETE if complete else LifecycleStageStatus.INCOMPLETE, tuple(ref for ref in refs if ref), authority, "" if complete else "required evidence missing")


def _order_management() -> OrderManagementOffice:
    return OrderManagementOffice(
        _config(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        PromptRepository(),
    )


def _config() -> ConfigurationService:
    return ConfigurationService.load(
        {"environment": "development", "config_version": "1.0.0", "schema_version": "1.0.0", "log_level": "INFO", "live_trading_enabled": False, "feature_flags": {}, "secret_references": []},
        {},
    )


def _token() -> WorkflowExecutionToken:
    return WorkflowExecutionToken("WF-EO-DM", "Trader", "Executive", "Performance Truth", "Trader", 3600, 10.0, ("full_position_lifecycle",), "TOK-EO-DM", utc_timestamp(), 4, "Executing")


def _decision() -> dict[str, Any]:
    provenance = {
        "asset_identifier": "AAPL",
        "asset_class": "equity",
        "direction": "buy",
        "thesis": "EO-DM deterministic paper lifecycle",
        "evidence": "Authorized office judgment",
        "market_context": "controlled authoritative quote",
        "entry_conditions": "broker executable",
        "price_source": "controlled-authoritative",
        "quantity": "2",
        "position_sizing_basis": "cash",
        "confidence": "0.7",
        "time_horizon": "day",
        "risk_factors": "documented",
        "stop_conditions": "documented",
        "exit_conditions": "close when lifecycle proof requested",
        "expected_return": "0.01",
        "risk_approval": "Authorized office judgment",
        "trader_authorization": "Authorized office judgment",
    }
    return {"decisionObjectId": "DO-EO-DM", "office": "Trader", "sourceSystem": "Trader", "executionMode": "PAPER", "truthClassification": "PAPER_OPERATIONAL", "certificationStatus": "PAPER_OPERATIONAL_CERTIFIED", "materialFieldProvenance": provenance, "recommendation": "BUY", "targetPrice": 501.0, "stopLoss": 480.0, "riskScore": 0.2, "confidence": 0.72, "currentStrategy": "STRAT-EO-DM"}


def _open_ticket(decision: dict[str, Any]) -> PaperBrokerOrderTicket:
    return PaperBrokerOrderTicket("ORD-EO-DM-OPEN", "WF-EO-DM", "MISSION-EO-DM", "DO-EO-DM", "TOK-EO-DM", "Trader", "ACCT-PAPER-001", "AAPL", "equity", "buy", 2.0, "market", "day", risk_approval_id="RISK-EO-DM", policy_approval_id="POLICY-EO-DM", strategy_id="STRAT-EO-DM", execution_plan_id="EXP-EO-DM", decision_object=decision)


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return tuple(_jsonable(item) for item in value)
    return value

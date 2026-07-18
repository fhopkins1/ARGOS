"""OR-004 enterprise position lifecycle coordinator."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from enum import Enum
import hashlib
import json
from typing import Any

from argos.foundation.contracts import utc_timestamp
from argos.trader.paper_brokerage import DeterministicPaperBrokerage, PaperBrokerOrderTicket

from .canonical_bridge_fabric import CanonicalBridgeExecutor, BridgeResultStatus, make_bridge_request
from .closed_position_truth import ClosedPositionTruthBuilder
from .enterprise_communications_bus import EnterpriseCommunicationsBus, MessageMode
from .market_data_provider import MarketDataProviderAbstractionLayer
from .performance_truth_engine import PerformanceTruthEngine
from .position_exit_decision_engine import ExitDecisionEngine
from .position_monitoring_network import PositionMonitoringNetwork
from .position_registry import PositionObject, PositionRegistry
from .position_surveillance_engine import PositionSurveillanceEngine
from .truth_domain import validate_decision_object_for_operational_truth


class PositionLifecycleRejectionCode(str, Enum):
    POSITION_NOT_FOUND = "POSITION_NOT_FOUND"
    POSITION_NOT_OPEN = "POSITION_NOT_OPEN"
    INVALID_POSITION_LINEAGE = "INVALID_POSITION_LINEAGE"
    MISSING_FILL_PROVENANCE = "MISSING_FILL_PROVENANCE"
    MISSING_MARKET_PROVENANCE = "MISSING_MARKET_PROVENANCE"
    EXIT_AUTHORITY_MISSING = "EXIT_AUTHORITY_MISSING"
    POLICY_APPROVAL_MISSING = "POLICY_APPROVAL_MISSING"
    TRADER_AUTHORITY_MISSING = "TRADER_AUTHORITY_MISSING"
    WORKFLOW_TOKEN_INVALID = "WORKFLOW_TOKEN_INVALID"
    CLOSING_QUANTITY_EXCEEDS_POSITION = "CLOSING_QUANTITY_EXCEEDS_POSITION"
    DUPLICATE_EXIT_REQUEST = "DUPLICATE_EXIT_REQUEST"
    DUPLICATE_CLOSING_ORDER = "DUPLICATE_CLOSING_ORDER"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    PROOF_MODE_NOT_ACTIONABLE = "PROOF_MODE_NOT_ACTIONABLE"
    SIMULATION_NOT_OPERATIONAL = "SIMULATION_NOT_OPERATIONAL"
    LIVE_DISABLED = "LIVE_DISABLED"


@dataclass(frozen=True)
class ExitAuthorizationRecord:
    authorization_id: str
    exit_decision_id: str
    position_id: str
    workflow_id: str
    mission_id: str
    decision_object_id: str
    authorized_quantity: float
    authorized_by: str
    risk_approval_id: str
    policy_approval_id: str
    authorization_state: str
    created_at: str
    rejection_code: str = ""


@dataclass(frozen=True)
class PositionLifecycleReconciliation:
    reconciliation_id: str
    position_id: str
    status: str
    open_quantity: float
    pending_close_quantity: float
    broker_order_ids: tuple[str, ...]
    fill_ids: tuple[str, ...]
    closed_truth_ids: tuple[str, ...]
    exceptions: tuple[str, ...]
    timestamp: str


class EnterprisePositionLifecycleManager:
    """Bridge existing OR-004 components without replacing their authority."""

    def __init__(
        self,
        *,
        performance_truth: PerformanceTruthEngine,
        paper_broker: DeterministicPaperBrokerage,
        market_data_provider: MarketDataProviderAbstractionLayer | None = None,
        monitoring_network: PositionMonitoringNetwork | None = None,
        surveillance_engine: PositionSurveillanceEngine | None = None,
        exit_decision_engine: ExitDecisionEngine | None = None,
        closed_truth_builder: ClosedPositionTruthBuilder | None = None,
        communications_bus: EnterpriseCommunicationsBus | None = None,
        bridge_executor: CanonicalBridgeExecutor | None = None,
    ) -> None:
        self.performance_truth = performance_truth
        self.paper_broker = paper_broker
        self.market_data_provider = market_data_provider or MarketDataProviderAbstractionLayer()
        self.monitoring_network = monitoring_network or PositionMonitoringNetwork()
        self.surveillance_engine = surveillance_engine or PositionSurveillanceEngine()
        self.exit_decision_engine = exit_decision_engine or ExitDecisionEngine()
        self.closed_truth_builder = closed_truth_builder or ClosedPositionTruthBuilder()
        self.communications_bus = communications_bus
        self.bridge_executor = bridge_executor or CanonicalBridgeExecutor(runtime_instance_id="ARGOS-POSITION-LIFECYCLE")
        self._authorizations: dict[str, ExitAuthorizationRecord] = {}
        self._closing_order_by_authorization: dict[str, str] = {}
        self._reconciliations: list[PositionLifecycleReconciliation] = []
        self._sequence = 0

    @property
    def registry(self) -> PositionRegistry:
        return self.performance_truth.position_registry

    def monitor_positions(self, *, timestamp_utc: str | None = None, mutate_registry: bool = True) -> dict[str, Any]:
        timestamp = timestamp_utc or utc_timestamp()
        market = self.market_data_provider.snapshot(timestamp_utc=timestamp)
        surveillance = self.surveillance_engine.surveil(
            position_registry=self.registry,
            market_data_provider=market,
            timestamp_utc=timestamp,
            mutate_registry=mutate_registry,
        )
        monitoring = self.monitoring_network.scan(
            position_registry=self.registry.snapshot(),
            market_data_provider=market,
            performance_truth=self.performance_truth.snapshot(execution_environment="paper"),
            timestamp_utc=timestamp,
        )
        self._publish("POSITION_MONITORING_OBSERVATION", {"summary": "Position monitoring pass completed.", "severity": "INFO", "surveillance": surveillance, "monitoring": monitoring})
        return {"marketData": market, "surveillance": surveillance, "monitoring": monitoring}

    def evaluate_exits(self, *, surveillance: dict[str, Any] | None = None, timestamp_utc: str | None = None, risk_context: dict[str, Any] | None = None) -> dict[str, Any]:
        timestamp = timestamp_utc or utc_timestamp()
        if surveillance is None:
            surveillance = self.monitor_positions(timestamp_utc=timestamp, mutate_registry=False)["surveillance"]
        state = self.exit_decision_engine.evaluate(
            position_registry=self.registry,
            position_surveillance=surveillance,
            timestamp_utc=timestamp,
            risk_context=risk_context or {},
            mutate_registry=True,
        )
        self._publish("ENTERPRISE_ACTIVITY_EVENT", {"summary": "Exit evaluation completed.", "severity": "INFO", "exitDecisionEngine": state})
        return state

    def authorize_exit(
        self,
        *,
        exit_decision: dict[str, Any],
        decision_object: dict[str, Any],
        authorized_by: str,
        risk_approval_id: str,
        policy_approval_id: str,
        mission_id: str = "",
    ) -> ExitAuthorizationRecord:
        timestamp = utc_timestamp()
        position_id = str(exit_decision.get("position_id", ""))
        position = self._position_or_none(position_id)
        rejection = self._authorization_rejection(position, exit_decision, decision_object, risk_approval_id, policy_approval_id)
        quantity = round(float(exit_decision.get("recommended_quantity", 0.0) or 0.0), 4)
        auth_id = _stable_id("EXIT-AUTH", position_id, str(exit_decision.get("exit_decision_id", "")), str(quantity))
        if auth_id in self._authorizations:
            return self._authorizations[auth_id]
        if rejection:
            record = ExitAuthorizationRecord(auth_id, str(exit_decision.get("exit_decision_id", "")), position_id, str(exit_decision.get("workflow_id", "")), mission_id, str(exit_decision.get("decision_object_id", "")), quantity, authorized_by, risk_approval_id, policy_approval_id, "rejected", timestamp, rejection.value)
            self._authorizations[auth_id] = record
            self._publish("ENTERPRISE_ACTIVITY_EVENT", {"summary": "Exit authorization rejected.", "severity": "WARNING", "authorization": _json_ready(record)})
            return record
        assert position is not None
        self.registry.reserve_close_quantity(position_id, quantity, reason="exit authorized pending broker execution", source="EnterprisePositionLifecycleManager")
        record = ExitAuthorizationRecord(auth_id, str(exit_decision.get("exit_decision_id", "")), position_id, position.workflow_id, mission_id or position.mission_id, position.decision_object_id, quantity, authorized_by, risk_approval_id, policy_approval_id, "authorized", timestamp)
        self._authorizations[auth_id] = record
        self._publish("ENTERPRISE_ACTIVITY_EVENT", {"summary": "Exit authorized.", "severity": "INFO", "authorization": _json_ready(record)})
        return record

    def submit_authorized_exit(self, authorization: ExitAuthorizationRecord, *, workflow_token: Any, decision_object: dict[str, Any], order_type: str = "market", time_in_force: str = "day") -> dict[str, Any]:
        if authorization.authorization_state != "authorized":
            return {"accepted": False, "reason": authorization.rejection_code or PositionLifecycleRejectionCode.EXIT_AUTHORITY_MISSING.value}
        if authorization.authorization_id in self._closing_order_by_authorization:
            return {"accepted": False, "reason": PositionLifecycleRejectionCode.DUPLICATE_CLOSING_ORDER.value, "orderId": self._closing_order_by_authorization[authorization.authorization_id]}
        if str(getattr(workflow_token, "current_owner", "")) != "Trader":
            return {"accepted": False, "reason": PositionLifecycleRejectionCode.TRADER_AUTHORITY_MISSING.value}
        position = self.registry.position(authorization.position_id)
        order_id = _stable_id("ORD-EXIT", authorization.authorization_id, position.position_id)
        ticket = PaperBrokerOrderTicket(
            order_id=order_id,
            workflow_id=position.workflow_id,
            mission_id=authorization.mission_id,
            decision_object_id=position.decision_object_id,
            workflow_token=str(getattr(workflow_token, "audit_identifier", "")),
            trader_identity="Trader",
            account_id=position.account_id or "ACCT-PAPER-001",
            symbol=position.symbol,
            asset_type=position.asset_type.lower(),
            side="sell",
            quantity=authorization.authorized_quantity,
            order_type=order_type,
            time_in_force=time_in_force,
            risk_approval_id=authorization.risk_approval_id,
            policy_approval_id=authorization.policy_approval_id,
            strategy_id=str(decision_object.get("currentStrategy", "")),
            execution_plan_id=authorization.exit_decision_id,
            decision_object=decision_object,
        )
        bridge_payload = {"authorization_id": authorization.authorization_id, "order_id": order_id, "position_id": position.position_id, "quantity": authorization.authorized_quantity}
        workflow_token_id = str(getattr(workflow_token, "audit_identifier", ""))
        if not self.bridge_executor.ownership.owner(position.workflow_id):
            self.bridge_executor.ownership.establish(position.workflow_id, "Trader", workflow_token_id)
        bridge_result = self.bridge_executor.execute(
            make_bridge_request(
                bridge_id="BRIDGE-TRADER-BROKER-001",
                runtime_instance_id=self.bridge_executor.runtime_instance_id,
                workflow_id=position.workflow_id,
                source="Trader",
                destination="Paper Broker",
                artifact_id=order_id,
                payload=bridge_payload,
                current_owner="Trader",
                token_id=workflow_token_id,
            )
        )
        if bridge_result.status != BridgeResultStatus.ACCEPTED:
            return {"accepted": False, "reason": bridge_result.rejection_code.value if bridge_result.rejection_code else "BRIDGE_REJECTED", "bridgeResult": _json_ready(bridge_result)}
        result = self.paper_broker.submit_order(ticket, workflow_token=workflow_token)
        if result.accepted:
            self._closing_order_by_authorization[authorization.authorization_id] = order_id
        self._publish("ENTERPRISE_ACTIVITY_EVENT", {"summary": "Authorized exit submitted to Paper Broker.", "severity": "INFO" if result.accepted else "WARNING", "brokerResult": _json_ready(result)})
        return {"accepted": result.accepted, "order": _json_ready(result.order), "events": _json_ready(result.events), "rejectionCode": result.rejection_code}

    def reconcile_position(self, position_id: str, *, exit_decision_state: dict[str, Any] | None = None, surveillance_state: dict[str, Any] | None = None) -> PositionLifecycleReconciliation:
        position = self.registry.position(position_id)
        truth = self.performance_truth.snapshot(execution_environment="paper")
        closed_truth = self.closed_truth_builder.build(
            position_registry=self.registry.snapshot(),
            performance_truth=truth,
            position_surveillance=surveillance_state or {},
            exit_decision_engine=exit_decision_state or {},
            enterprise_benchmark_engine=_benchmark_engine_from_performance_truth(truth, position.decision_object_id),
            timestamp_utc=utc_timestamp(),
        )
        self.performance_truth.ingest_closed_position_truth(tuple(closed_truth.get("latestClosedPositionTruthRecords", ())))
        exceptions = []
        if position.lifecycle_status == "closed" and position.quantity != 0:
            exceptions.append(PositionLifecycleRejectionCode.RECONCILIATION_REQUIRED.value)
        if position.quantity > 0 and position.pending_close_quantity > position.quantity:
            exceptions.append(PositionLifecycleRejectionCode.CLOSING_QUANTITY_EXCEEDS_POSITION.value)
        record = PositionLifecycleReconciliation(
            reconciliation_id=_stable_id("POS-REC", position_id, str(len(self._reconciliations) + 1)),
            position_id=position_id,
            status="reconciled" if not exceptions else "exception",
            open_quantity=position.quantity,
            pending_close_quantity=position.pending_close_quantity,
            broker_order_ids=position.broker_order_ids,
            fill_ids=position.fill_ids,
            closed_truth_ids=tuple(item.get("closed_position_truth_id", "") for item in closed_truth.get("latestClosedPositionTruthRecords", ())),
            exceptions=tuple(exceptions),
            timestamp=utc_timestamp(),
        )
        self._reconciliations.append(record)
        self._publish("ENTERPRISE_ACTIVITY_EVENT", {"summary": "Position reconciliation completed.", "severity": "INFO" if not exceptions else "WARNING", "reconciliation": _json_ready(record)})
        return record

    def snapshot(self) -> dict[str, Any]:
        return {
            "managerName": "Enterprise Position Lifecycle Manager",
            "engineeringOrder": "OR-004",
            "positionRegistry": self.registry.snapshot(),
            "exitAuthorizations": tuple(_json_ready(item) for item in self._authorizations.values()),
            "closingOrders": dict(self._closing_order_by_authorization),
            "reconciliations": tuple(_json_ready(item) for item in self._reconciliations),
            "authority": {
                "brokerOwnsOrdersAndFills": True,
                "enterpriseOwnsPositions": True,
                "monitoringDoesNotMutateWithoutRegistry": True,
                "exitRecommendationDoesNotClose": True,
                "brokerFillRequiredForReduction": True,
            },
        }

    def _authorization_rejection(self, position: PositionObject | None, exit_decision: dict[str, Any], decision_object: dict[str, Any], risk_approval_id: str, policy_approval_id: str) -> PositionLifecycleRejectionCode | None:
        if position is None:
            return PositionLifecycleRejectionCode.POSITION_NOT_FOUND
        if position.quantity <= 0 or position.lifecycle_status in {"closed", "archived", "cancelled", "rejected"}:
            return PositionLifecycleRejectionCode.POSITION_NOT_OPEN
        if not position.broker_order_ids or not position.fill_ids:
            return PositionLifecycleRejectionCode.MISSING_FILL_PROVENANCE
        if not position.decision_object_id or not position.workflow_id:
            return PositionLifecycleRejectionCode.INVALID_POSITION_LINEAGE
        provenance = validate_decision_object_for_operational_truth(decision_object, execution_environment="paper")
        if not provenance.valid:
            if "PROOF_MODE_NOT_ACTIONABLE" in provenance.codes:
                return PositionLifecycleRejectionCode.PROOF_MODE_NOT_ACTIONABLE
            if "SIMULATION_VALUE_IN_OPERATIONAL_PATH" in provenance.codes:
                return PositionLifecycleRejectionCode.SIMULATION_NOT_OPERATIONAL
            if "LIVE_DISABLED" in provenance.codes:
                return PositionLifecycleRejectionCode.LIVE_DISABLED
            return PositionLifecycleRejectionCode.INVALID_POSITION_LINEAGE
        if not risk_approval_id:
            return PositionLifecycleRejectionCode.EXIT_AUTHORITY_MISSING
        if not policy_approval_id:
            return PositionLifecycleRejectionCode.POLICY_APPROVAL_MISSING
        quantity = round(float(exit_decision.get("recommended_quantity", 0.0) or 0.0), 4)
        available = round(max(0.0, position.quantity - position.pending_close_quantity), 4)
        if quantity <= 0 or quantity > available:
            return PositionLifecycleRejectionCode.CLOSING_QUANTITY_EXCEEDS_POSITION
        return None

    def _position_or_none(self, position_id: str) -> PositionObject | None:
        try:
            return self.registry.position(position_id)
        except ValueError:
            return None

    def _publish(self, message_type: str, payload: dict[str, Any]) -> None:
        if not self.communications_bus:
            return
        self._sequence += 1
        self.communications_bus.publish_event(
            message_type=message_type,
            source_service_id="Enterprise Position Lifecycle Manager",
            source_office_id="Trader",
            payload=payload,
            paper_live_mode=MessageMode.PAPER,
            sequence_number=self._sequence,
            ordering_key="OR-004-POSITION-LIFECYCLE",
            idempotency_key=_stable_id("EPLM-MSG", message_type, str(self._sequence), _hash(payload)),
        )


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256(":".join(parts).encode("utf-8")).hexdigest()[:12].upper()
    return f"{prefix}-{digest}"


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(_json_ready(value), sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return tuple(_json_ready(item) for item in value)
    return value


def _benchmark_engine_from_performance_truth(performance_truth: dict[str, Any], decision_object_id: str) -> dict[str, Any]:
    latest_by_benchmark: dict[str, dict[str, Any]] = {}
    for record in performance_truth.get("benchmarkHistory", ()):
        name = str(record.get("benchmark", ""))
        if name:
            latest_by_benchmark[name] = dict(record)
    comparisons = []
    for name in ("SPY", "SPY Buy And Hold"):
        source = latest_by_benchmark.get("SPY") if name.startswith("SPY") else latest_by_benchmark.get(name)
        if source:
            comparisons.append(
                {
                    "decisionObjectId": decision_object_id,
                    "benchmarkName": name,
                    "benchmarkReturn": float(source.get("benchmark_return", 0.0) or 0.0),
                    "source": "PerformanceTruthEngine.benchmarkHistory",
                }
            )
            break
    return {"tradeLevelComparisons": tuple(comparisons)}

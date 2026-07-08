"""Enterprise Credit Governor for ARGOS."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
from typing import Any


AUTHORIZED_ACTIVATORS = {
    "Commander",
    "Executive",
    "Seeker",
    "Analyst",
    "Risk",
    "Trader",
    "Historian",
    "Librarian",
    "Academy",
    "Scheduled Workflow",
    "Enterprise Event",
    "Critical Alert",
}

WORKFLOW_PRECEDENCE = ("Commander", "Executive", "Seeker", "Analyst", "Risk", "Executive", "Trader", "Historian", "Librarian", "Academy")

AUTHORIZED_PREDECESSORS = {
    "Executive": {"Commander", "Risk"},
    "Seeker": {"Executive"},
    "Analyst": {"Seeker"},
    "Risk": {"Analyst"},
    "Trader": {"Executive"},
    "Historian": {"Trader"},
    "Librarian": {"Historian"},
    "Academy": {"Librarian"},
}

NON_PREDECESSOR_ACTIVATORS = {"Commander", "Scheduled Workflow", "Enterprise Event", "Critical Alert"}

MARKET_DATA_ONLY_TERMS = {"tick", "quote", "candle", "market data", "market-data", "price update"}

THRESHOLD_EVIDENCE_TERMS = {
    "TRADE-CANDIDATE",
    "RISK-THRESHOLD",
    "POSITION-ANOMALY",
    "EXECUTIVE-APPROVAL",
    "UNUSUAL-MARKET-EVENT",
    "COMMANDER-REQUEST",
    "THRESHOLD",
}

AI_RESERVED_PURPOSES = {
    "Executive synthesis",
    "Ambiguous reasoning",
    "Conflict analysis",
    "Historian reflection",
    "Librarian summary",
    "Academy lesson generation",
    "Commander explanation",
    "Real API Pilot",
}

DETERMINISTIC_CODE_PURPOSES = {
    "Market data ingestion",
    "Indicator calculations",
    "Portfolio math",
    "Logs",
    "Alerts",
    "Scheduling",
    "Dashboard updates",
    "Event routing",
}


class BudgetMode(str, Enum):
    """Credit threshold modes."""

    NORMAL = "Normal"
    WARNING = "Warning Mode"
    RESTRICTED = "Restricted Mode"
    COMMANDER_APPROVAL = "Commander Approval Mode"
    HARD_STOP = "Hard Stop Mode"


@dataclass(frozen=True)
class CreditBudgets:
    """Enterprise, office, workflow, and task credit budgets."""

    daily_budget_usd: float
    weekly_budget_usd: float
    monthly_budget_usd: float
    office_budgets_usd: dict[str, float]
    workflow_budgets_usd: dict[str, float]
    task_budgets_usd: dict[str, float]


@dataclass(frozen=True)
class ActivationRequest:
    """Deterministic AI activation request."""

    activation_id: str
    task_identifier: str
    activating_source: str
    receiving_office: str
    purpose: str
    required_output: str
    maximum_runtime_minutes: int
    maximum_credit_budget_usd: float
    evidence_package: tuple[str, ...]
    return_route: str
    audit_identifier: str
    workflow: str
    organization: str
    workflow_id: str
    workflow_token_id: str
    law_vii_validation: str
    status: str
    reason: str


@dataclass(frozen=True)
class CreditDetection:
    """Credit-governor control detection."""

    detection_id: str
    category: str
    severity: str
    summary: str
    evidence: tuple[str, ...]


class EnterpriseCreditGovernor:
    """Dormant-by-default AI activation and credit discipline layer."""

    def __init__(self) -> None:
        self.budgets = CreditBudgets(
            daily_budget_usd=25.0,
            weekly_budget_usd=100.0,
            monthly_budget_usd=250.0,
            office_budgets_usd={},
            workflow_budgets_usd={},
            task_budgets_usd={},
        )
        self._activations: list[ActivationRequest] = []
        self._overrides: list[dict[str, Any]] = []

    def snapshot(
        self,
        *,
        timestamp_utc: str,
        scheduler: dict[str, Any],
        infrastructure: dict[str, Any],
        eab: dict[str, Any],
        audit_event_count: int,
    ) -> dict[str, Any]:
        """Return current credit-governor state."""
        spend = self._spend_report(infrastructure, eab)
        mode = self._mode(spend)
        detections = self._detections(scheduler, spend, mode)
        return {
            "mode": mode.value,
            "budgets": asdict(self.budgets),
            "dormantByDefault": True,
            "workflowPrecedence": WORKFLOW_PRECEDENCE,
            "authorizedActivators": tuple(sorted(AUTHORIZED_ACTIVATORS)),
            "aiReservedPurposes": tuple(sorted(AI_RESERVED_PURPOSES)),
            "deterministicCodePurposes": tuple(sorted(DETERMINISTIC_CODE_PURPOSES)),
            "activations": tuple(asdict(item) for item in reversed(self._activations[-40:])),
            "spendReport": spend,
            "detections": tuple(asdict(item) for item in detections),
            "overrides": tuple(self._overrides[-30:]),
            "metrics": {
                "activationHistoryDepth": len(self._activations),
                "approvedActivations": sum(1 for item in self._activations if item.status == "APPROVED"),
                "rejectedActivations": sum(1 for item in self._activations if item.status == "REJECTED"),
                "detectionCount": len(detections),
                "auditReference": f"AE-CREDIT-{audit_event_count + len(self._activations) + 1:06d}",
                "lastUpdatedUtc": timestamp_utc,
            },
        }

    def configure_budgets(
        self,
        *,
        daily_budget_usd: float,
        weekly_budget_usd: float,
        monthly_budget_usd: float,
        office: str = "",
        office_budget_usd: float | None = None,
        workflow: str = "",
        workflow_budget_usd: float | None = None,
        task_identifier: str = "",
        task_budget_usd: float | None = None,
        timestamp_utc: str,
    ) -> dict[str, Any]:
        """Apply Commander budget limits."""
        office_budgets = dict(self.budgets.office_budgets_usd)
        workflow_budgets = dict(self.budgets.workflow_budgets_usd)
        task_budgets = dict(self.budgets.task_budgets_usd)
        if office and office_budget_usd is not None:
            office_budgets[office] = round(max(0.0, float(office_budget_usd)), 2)
        if workflow and workflow_budget_usd is not None:
            workflow_budgets[workflow] = round(max(0.0, float(workflow_budget_usd)), 2)
        if task_identifier and task_budget_usd is not None:
            task_budgets[task_identifier] = round(max(0.0, float(task_budget_usd)), 2)
        self.budgets = replace(
            self.budgets,
            daily_budget_usd=round(max(0.0, float(daily_budget_usd)), 2),
            weekly_budget_usd=round(max(0.0, float(weekly_budget_usd)), 2),
            monthly_budget_usd=round(max(0.0, float(monthly_budget_usd)), 2),
            office_budgets_usd=office_budgets,
            workflow_budgets_usd=workflow_budgets,
            task_budgets_usd=task_budgets,
        )
        override = {
            "overrideId": f"ECG-OVR-{len(self._overrides) + 1:06d}",
            "timestampUtc": timestamp_utc,
            "dailyBudgetUsd": self.budgets.daily_budget_usd,
            "weeklyBudgetUsd": self.budgets.weekly_budget_usd,
            "monthlyBudgetUsd": self.budgets.monthly_budget_usd,
            "office": office,
            "workflow": workflow,
            "taskIdentifier": task_identifier,
        }
        self._overrides.append(override)
        return override

    def request_activation(
        self,
        *,
        task_identifier: str,
        activating_source: str,
        receiving_office: str,
        purpose: str,
        required_output: str,
        maximum_runtime_minutes: int,
        maximum_credit_budget_usd: float,
        evidence_package: tuple[str, ...],
        return_route: str,
        workflow: str,
        organization: str,
        audit_identifier: str,
        current_spend: dict[str, Any],
        paper_trading_active: bool = False,
        workflow_id: str = "",
        workflow_token_id: str = "",
        law_vii_validation: str = "LAW_VII_API_USAGE_AUTHORIZED",
    ) -> ActivationRequest:
        """Validate one AI activation request."""
        status, reason = self._validate_activation(
            task_identifier=task_identifier,
            activating_source=activating_source,
            receiving_office=receiving_office,
            purpose=purpose,
            maximum_credit_budget_usd=maximum_credit_budget_usd,
            workflow=workflow,
            organization=organization,
            evidence_package=evidence_package,
            current_spend=current_spend,
            paper_trading_active=paper_trading_active,
        )
        record = ActivationRequest(
            activation_id=f"ECG-ACT-{len(self._activations) + 1:06d}",
            task_identifier=task_identifier,
            activating_source=activating_source,
            receiving_office=receiving_office,
            purpose=purpose,
            required_output=required_output,
            maximum_runtime_minutes=max(1, int(maximum_runtime_minutes)),
            maximum_credit_budget_usd=round(max(0.0, float(maximum_credit_budget_usd)), 4),
            evidence_package=tuple(evidence_package),
            return_route=return_route,
            audit_identifier=audit_identifier,
            workflow=workflow,
            organization=organization,
            workflow_id=workflow_id,
            workflow_token_id=workflow_token_id,
            law_vii_validation=law_vii_validation,
            status=status,
            reason=reason,
        )
        self._activations.append(record)
        return record

    def record_blocked_activation(
        self,
        *,
        task_identifier: str,
        activating_source: str,
        receiving_office: str,
        purpose: str,
        required_output: str,
        maximum_runtime_minutes: int,
        maximum_credit_budget_usd: float,
        evidence_package: tuple[str, ...],
        return_route: str,
        workflow: str,
        organization: str,
        audit_identifier: str,
        workflow_id: str,
        workflow_token_id: str,
        law_vii_validation: str,
        reason: str,
    ) -> ActivationRequest:
        """Record a blocked activation without recording credit/API usage."""
        record = ActivationRequest(
            activation_id=f"ECG-ACT-{len(self._activations) + 1:06d}",
            task_identifier=task_identifier,
            activating_source=activating_source,
            receiving_office=receiving_office,
            purpose=purpose,
            required_output=required_output,
            maximum_runtime_minutes=max(1, int(maximum_runtime_minutes)),
            maximum_credit_budget_usd=round(max(0.0, float(maximum_credit_budget_usd)), 4),
            evidence_package=tuple(evidence_package),
            return_route=return_route,
            audit_identifier=audit_identifier,
            workflow=workflow,
            organization=organization,
            workflow_id=workflow_id,
            workflow_token_id=workflow_token_id,
            law_vii_validation=law_vii_validation,
            status="REJECTED",
            reason=reason,
        )
        self._activations.append(record)
        return record

    def complete_activation(self, activation_id: str) -> ActivationRequest:
        """Return an activation to dormancy after structured result emission."""
        for index, activation in enumerate(self._activations):
            if activation.activation_id == activation_id:
                completed = replace(activation, status="COMPLETED", reason="Structured result emitted; office returned to dormancy.")
                self._activations[index] = completed
                return completed
        raise ValueError(f"unknown activation: {activation_id}")

    def _validate_activation(
        self,
        *,
        task_identifier: str,
        activating_source: str,
        receiving_office: str,
        purpose: str,
        maximum_credit_budget_usd: float,
        workflow: str,
        organization: str,
        evidence_package: tuple[str, ...],
        current_spend: dict[str, Any],
        paper_trading_active: bool,
    ) -> tuple[str, str]:
        if activating_source not in AUTHORIZED_ACTIVATORS:
            return "REJECTED", "Unauthorized activating source."
        if activating_source == receiving_office:
            return "REJECTED", "Self-activation is not authorized."
        if not _authorized_predecessor(activating_source, organization or receiving_office):
            return "REJECTED", "Activating source is not an authorized predecessor for the receiving office."
        if purpose in DETERMINISTIC_CODE_PURPOSES:
            return "REJECTED", "Purpose must use deterministic code instead of AI inference."
        if purpose not in AI_RESERVED_PURPOSES:
            return "REJECTED", "Purpose is outside reserved AI inference roles."
        if paper_trading_active and _paper_trading_overactivation(task_identifier, workflow, evidence_package):
            return "REJECTED", "Paper trading cannot activate AI reasoning on tick, quote, candle, or market-data updates without threshold evidence."
        if _market_data_only(task_identifier, workflow, purpose, evidence_package):
            return "REJECTED", "Market data alone may not trigger AI reasoning; deterministic threshold evidence is required."
        if not task_identifier:
            return "REJECTED", "Missing task identifier."
        if not workflow:
            return "REJECTED", "Missing workflow."
        if maximum_credit_budget_usd <= 0:
            return "REJECTED", "Activation requires a positive credit budget."
        if current_spend["dailySpendUsd"] + maximum_credit_budget_usd > self.budgets.daily_budget_usd:
            return "REJECTED", "Daily budget would be exceeded."
        if current_spend["monthlySpendUsd"] + maximum_credit_budget_usd > self.budgets.monthly_budget_usd:
            return "REJECTED", "Monthly budget would be exceeded."
        if maximum_credit_budget_usd > self.budgets.task_budgets_usd.get(task_identifier, maximum_credit_budget_usd):
            return "REJECTED", "Task budget would be exceeded."
        if maximum_credit_budget_usd > self.budgets.workflow_budgets_usd.get(workflow, maximum_credit_budget_usd):
            return "REJECTED", "Workflow budget would be exceeded."
        if maximum_credit_budget_usd > self.budgets.office_budgets_usd.get(receiving_office, maximum_credit_budget_usd):
            return "REJECTED", "Office budget would be exceeded."
        return "APPROVED", "Activation approved for one structured result and mandatory dormancy return."

    def _mode(self, spend: dict[str, Any]) -> BudgetMode:
        daily_ratio = _ratio(spend["dailySpendUsd"], self.budgets.daily_budget_usd)
        monthly_ratio = _ratio(spend["monthlySpendUsd"], self.budgets.monthly_budget_usd)
        ratio = max(daily_ratio, monthly_ratio)
        if ratio >= 1.0:
            return BudgetMode.HARD_STOP
        if ratio >= 0.9:
            return BudgetMode.COMMANDER_APPROVAL
        if ratio >= 0.75:
            return BudgetMode.RESTRICTED
        if ratio >= 0.6:
            return BudgetMode.WARNING
        return BudgetMode.NORMAL

    def _spend_report(self, infrastructure: dict[str, Any], eab: dict[str, Any]) -> dict[str, Any]:
        operating = infrastructure.get("operatingCost", {})
        daily = round(float(operating.get("dailyOperatingCostUsd", 0.0)), 4)
        monthly = round(float(operating.get("monthlyOperatingCostUsd", 0.0)), 4)
        events = eab.get("events", ())
        org_counts: dict[str, int] = {}
        workflow_counts: dict[str, int] = {}
        task_counts: dict[str, int] = {}
        for event in events:
            org_counts[event["organization"]] = org_counts.get(event["organization"], 0) + 1
            workflow_counts[event["workflow"]] = workflow_counts.get(event["workflow"], 0) + 1
            task_counts[event["task_identifier"]] = task_counts.get(event["task_identifier"], 0) + 1
        total_events = max(1, sum(org_counts.values()))
        organization_spend = {key: round(monthly * value / total_events, 4) for key, value in org_counts.items()}
        workflow_spend = {key: round(monthly * value / total_events, 4) for key, value in workflow_counts.items()}
        task_spend = {key: round(monthly * value / total_events, 4) for key, value in task_counts.items()}
        office_spend = {
            f"{item['organization']} / {item['office']}": item["estimatedCostUsd"]
            for item in infrastructure.get("officeResourceConsumption", ())[:20]
        }
        return {
            "dailySpendUsd": daily,
            "weeklySpendUsd": round(daily * 7, 4),
            "monthlySpendUsd": monthly,
            "spendByOrganization": organization_spend,
            "spendByOffice": office_spend,
            "spendByWorkflow": workflow_spend,
            "spendByTask": task_spend,
            "costPerTradingCycle": round(workflow_spend.get("Paper Trading Workflow", 0.0), 4),
            "costPerBriefing": round(workflow_spend.get("Commander Briefing Workflow", 0.0), 4),
            "costPerHistorianReview": round(organization_spend.get("Historian", 0.0), 4),
            "costPerAcademyOutput": round(organization_spend.get("Academy", 0.0), 4),
        }

    def _detections(self, scheduler: dict[str, Any], spend: dict[str, Any], mode: BudgetMode) -> tuple[CreditDetection, ...]:
        detections: list[CreditDetection] = []
        active_ai_offices = [
            office for office in scheduler.get("offices", ())
            if office["organization"] not in {"Executive", "Infrastructure"} and office["status"] == "ACTIVE"
        ]
        if active_ai_offices:
            detections.append(_detection(len(detections) + 1, "Idle AI Activity", "WARNING", "AI offices are active outside an approved credit activation.", tuple(office["schedule_id"] for office in active_ai_offices[:8])))
        for activation in self._activations:
            if activation.status == "APPROVED":
                same_task = [item for item in self._activations if item.task_identifier == activation.task_identifier and item.status == "APPROVED"]
                if len(same_task) > 1:
                    detections.append(_detection(len(detections) + 1, "Duplicate AI Calls", "WARNING", "Multiple approved activations exist for one task.", (activation.task_identifier,)))
        if mode == BudgetMode.HARD_STOP:
            detections.append(_detection(len(detections) + 1, "Budget Overrun", "CRITICAL", "Credit budget is exhausted; AI activation must stop.", (str(spend["dailySpendUsd"]), str(spend["monthlySpendUsd"]))))
        if any(item.purpose == "Commander explanation" and item.maximum_credit_budget_usd > 5 for item in self._activations):
            detections.append(_detection(len(detections) + 1, "Low-Value Expensive Task", "NOTICE", "Commander explanation budget exceeds routine threshold.", ("Commander explanation",)))
        for activation in self._activations:
            if activation.status != "REJECTED":
                continue
            reason = activation.reason.lower()
            if "market data alone" in reason:
                detections.append(_detection(len(detections) + 1, "Market Data AI Trigger", "CRITICAL", "Market data alone attempted to trigger AI reasoning.", (activation.activation_id, activation.task_identifier)))
            if "paper trading cannot activate" in reason:
                detections.append(_detection(len(detections) + 1, "Paper-Trading Overactivation", "CRITICAL", "Paper trading attempted to activate AI reasoning without threshold evidence.", (activation.activation_id, activation.task_identifier)))
            if "authorized predecessor" in reason:
                detections.append(_detection(len(detections) + 1, "Cross-Office Chatter", "WARNING", "Activation violated deterministic workflow predecessor rules.", (activation.activation_id, activation.activating_source, activation.organization)))
            if activation.law_vii_validation.startswith("LAW_VII_VIOLATION"):
                detections.append(_detection(len(detections) + 1, activation.law_vii_validation, "CRITICAL", activation.reason, (activation.activation_id, activation.workflow_id, activation.receiving_office)))
        return tuple(detections)


def _ratio(value: float, budget: float) -> float:
    return value / budget if budget else 1.0


def _detection(index: int, category: str, severity: str, summary: str, evidence: tuple[str, ...]) -> CreditDetection:
    return CreditDetection(f"ECG-DET-{index:06d}", category, severity, summary, evidence)


def _authorized_predecessor(activating_source: str, receiving_organization: str) -> bool:
    if activating_source in NON_PREDECESSOR_ACTIVATORS:
        return True
    return activating_source in AUTHORIZED_PREDECESSORS.get(receiving_organization, set())


def _market_data_only(task_identifier: str, workflow: str, purpose: str, evidence_package: tuple[str, ...]) -> bool:
    source_text = f"{task_identifier} {workflow} {purpose}".lower()
    if not any(term in source_text for term in MARKET_DATA_ONLY_TERMS):
        return False
    return not _has_threshold_evidence(evidence_package)


def _paper_trading_overactivation(task_identifier: str, workflow: str, evidence_package: tuple[str, ...]) -> bool:
    source_text = f"{task_identifier} {workflow}".lower()
    if not any(term in source_text for term in MARKET_DATA_ONLY_TERMS):
        return False
    return not _has_threshold_evidence(evidence_package)


def _has_threshold_evidence(evidence_package: tuple[str, ...]) -> bool:
    evidence_text = " ".join(evidence_package).upper()
    return any(term in evidence_text for term in THRESHOLD_EVIDENCE_TERMS)

"""Decision Laboratory for ARGOS OE-011D."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from argos.foundation.contracts import utc_timestamp


OFFICE_SEQUENCE = ("Seeker", "Analyst", "Risk", "Trader", "Historian")


@dataclass(frozen=True)
class ReplaySession:
    """Immutable replay session state."""

    replay_id: str
    workflow_id: str
    decision_object_id: str
    status: str
    current_revision: int
    current_stage: str
    replay_speed: float
    created_timestamp: str
    audit_identifier: str


@dataclass(frozen=True)
class Experiment:
    """Isolated laboratory experiment forked from production truth."""

    experiment_id: str
    original_decision_object_id: str
    original_workflow_id: str
    parent_experiment_id: str
    experiment_revision: int
    parameter_changes: dict[str, Any]
    experiment_decision_object: dict[str, Any]
    created_timestamp: str
    audit_identifier: str


@dataclass(frozen=True)
class ExperimentAudit:
    """Append-only laboratory audit record."""

    audit_id: str
    timestamp: str
    action: str
    target_identifier: str
    summary: str
    immutable_production_preserved: bool


class DecisionLaboratory:
    """Interactive replay and experimentation lab over immutable historical truth."""

    def __init__(self) -> None:
        self._experiments: list[Experiment] = []
        self._replay_sessions: list[ReplaySession] = []
        self._experiment_audit: list[ExperimentAudit] = []

    def snapshot(
        self,
        *,
        workflow_orchestrator: dict[str, Any],
        workflow_runtime_monitor: dict[str, Any],
        performance_truth: dict[str, Any],
        strategy_performance: dict[str, Any],
        search_query: str = "",
    ) -> dict[str, Any]:
        """Return Commander-facing Decision Laboratory state."""
        workflows = _completed_workflows(workflow_orchestrator)
        replay_packages = tuple(_workflow_replay_package(workflow, performance_truth) for workflow in workflows)
        decision_replays = tuple(_decision_replay(item) for item in replay_packages)
        office_replays = tuple(_office_replay(item) for item in replay_packages)
        comparisons = tuple(self._decision_comparison(experiment, performance_truth) for experiment in self._experiments)
        performance_comparisons = tuple(self._performance_comparison(experiment, performance_truth) for experiment in self._experiments)
        historian_reports = tuple(self._historian_report(experiment, performance_truth) for experiment in self._experiments)
        tree = self._decision_tree(replay_packages)
        search_results = _search(search_query, replay_packages, self._experiments, performance_truth) if search_query else ()
        prompt_revision_comparisons = tuple(_prompt_revision_comparison(item) for item in replay_packages)
        return {
            "laboratoryName": "Decision Laboratory",
            "engineeringOrder": "OE-011D",
            "philosophy": "Performance Truth represents reality. Decision Objects represent belief.",
            "productionHistoryImmutable": True,
            "workflowReplay": replay_packages,
            "decisionObjectReplay": decision_replays,
            "officeContributionReplay": office_replays,
            "replaySessions": tuple(asdict(item) for item in self._replay_sessions),
            "experiments": tuple(asdict(item) for item in self._experiments),
            "decisionComparisons": comparisons,
            "performanceComparisons": performance_comparisons,
            "historianReports": historian_reports,
            "promptRevisionComparisons": prompt_revision_comparisons,
            "decisionTree": tree,
            "experimentAudit": tuple(asdict(item) for item in self._experiment_audit),
            "searchResults": search_results,
            "commanderInterface": {
                "replayControls": ("Pause", "Resume", "Step Forward", "Step Back", "Jump To Stage", "Jump To Revision", "Replay Speed", "Automatic Replay", "Timeline Scrubbing"),
                "decisionTimeline": len(decision_replays),
                "workflowTimeline": len(workflow_runtime_monitor.get("workflowTimeline", ())),
                "officeTimeline": len(office_replays),
                "performanceComparison": len(performance_comparisons),
                "historianNotes": len(historian_reports),
                "experimentTree": len(tree),
                "decisionDiff": len(comparisons),
            },
            "integration": {
                "oe010WorkflowOrchestrator": "SYNCHRONIZED",
                "oe011WorkflowRuntimeMonitor": "SYNCHRONIZED",
                "oe011aApiExecutionGateway": "READ_ONLY_TRACE",
                "oe011bLiveStrategyPerformanceConsole": strategy_performance.get("trace", {}).get("performanceSource", "UNKNOWN"),
                "oe011cPerformanceTruthEngine": performance_truth.get("sourceOfTruth", "UNKNOWN"),
                "oe011fPromptContract": "REPLAYABLE",
                "workflowExecutionToken": "READ_ONLY_HISTORY",
                "decisionObject": "REPLAYABLE",
                "tradeLedger": "IMMUTABLE_LEDGER",
                "portfolioLedger": "IMMUTABLE_LEDGER",
                "historian": "LAB_REPORTS_ONLY",
            },
            "metrics": {
                "completedWorkflowCount": len(replay_packages),
                "decisionReplayCount": len(decision_replays),
                "experimentCount": len(self._experiments),
                "replaySessionCount": len(self._replay_sessions),
                "historianReportCount": len(historian_reports),
                "promptRevisionCount": sum(len(item["promptVersions"]) for item in replay_packages),
                "productionMutationCount": 0,
            },
        }

    def create_experiment(self, workflow_id: str, parameter_changes: dict[str, Any], *, parent_experiment_id: str = "", workflow_orchestrator: dict[str, Any], performance_truth: dict[str, Any]) -> dict[str, Any]:
        """Fork a completed Decision Object into an isolated experiment."""
        workflow = next((item for item in _completed_workflows(workflow_orchestrator) if item["workflow_id"] == workflow_id), None)
        if workflow is None:
            raise ValueError(f"completed workflow not found: {workflow_id}")
        latest = _latest_decision(workflow)
        if not latest:
            raise ValueError("workflow has no Decision Object revisions")
        experiment_id = f"DL-EXP-{len(self._experiments) + 1:06d}"
        experiment_revision = len([item for item in self._experiments if item.original_decision_object_id == latest["decisionObjectId"]]) + 1
        forked = dict(latest)
        forked["decisionObjectId"] = f"{latest['decisionObjectId']}-EXP-{experiment_revision:03d}"
        forked["experimentId"] = experiment_id
        forked["experimentRevision"] = experiment_revision
        forked["productionImmutable"] = True
        for key, value in parameter_changes.items():
            if key in {"confidence", "stopLoss", "positionSizeRecommendation", "riskScore", "expectedReturn", "recommendation", "currentStrategy"}:
                forked[key] = value
        experiment = Experiment(
            experiment_id=experiment_id,
            original_decision_object_id=latest["decisionObjectId"],
            original_workflow_id=workflow_id,
            parent_experiment_id=parent_experiment_id,
            experiment_revision=experiment_revision,
            parameter_changes=dict(parameter_changes),
            experiment_decision_object=forked,
            created_timestamp=utc_timestamp(),
            audit_identifier=f"AE-DL-EXP-{len(self._experiments) + 1:06d}",
        )
        self._experiments.append(experiment)
        self._audit("Experiment Created", experiment_id, f"Experiment forked from {latest['decisionObjectId']}.")
        return {
            "experiment": asdict(experiment),
            "decisionComparison": self._decision_comparison(experiment, performance_truth),
            "performanceComparison": self._performance_comparison(experiment, performance_truth),
            "historianReport": self._historian_report(experiment, performance_truth),
        }

    def start_replay(self, workflow_id: str, *, workflow_orchestrator: dict[str, Any]) -> dict[str, Any]:
        """Create a deterministic replay session for a completed workflow."""
        workflow = next((item for item in _completed_workflows(workflow_orchestrator) if item["workflow_id"] == workflow_id), None)
        if workflow is None:
            raise ValueError(f"completed workflow not found: {workflow_id}")
        latest = _latest_decision(workflow)
        session = ReplaySession(
            replay_id=f"DL-RPL-{len(self._replay_sessions) + 1:06d}",
            workflow_id=workflow_id,
            decision_object_id=latest.get("decisionObjectId", ""),
            status="PAUSED_AT_START",
            current_revision=1,
            current_stage=workflow["stages"][0],
            replay_speed=1.0,
            created_timestamp=utc_timestamp(),
            audit_identifier=f"AE-DL-RPL-{len(self._replay_sessions) + 1:06d}",
        )
        self._replay_sessions.append(session)
        self._audit("Replay Session Created", session.replay_id, f"Replay session created for {workflow_id}.")
        return asdict(session)

    def replay_control(self, replay_id: str, action: str, value: str = "") -> dict[str, Any]:
        """Apply deterministic replay controls to a lab replay session."""
        index = next((idx for idx, item in enumerate(self._replay_sessions) if item.replay_id == replay_id), None)
        if index is None:
            raise ValueError(f"unknown replay session: {replay_id}")
        session = self._replay_sessions[index]
        action_key = action.lower().replace(" ", "_")
        revision = session.current_revision
        status = session.status
        speed = session.replay_speed
        stage = session.current_stage
        if action_key == "pause":
            status = "PAUSED"
        elif action_key == "resume":
            status = "RUNNING"
        elif action_key == "step_forward":
            revision = min(5, revision + 1)
            stage = OFFICE_SEQUENCE[revision - 1]
            status = "PAUSED"
        elif action_key == "step_back":
            revision = max(1, revision - 1)
            stage = OFFICE_SEQUENCE[revision - 1]
            status = "PAUSED"
        elif action_key == "jump_to_stage" and value in OFFICE_SEQUENCE:
            stage = value
            revision = OFFICE_SEQUENCE.index(value) + 1
            status = "PAUSED"
        elif action_key == "jump_to_revision":
            revision = min(5, max(1, int(float(value or 1))))
            stage = OFFICE_SEQUENCE[revision - 1]
            status = "PAUSED"
        elif action_key == "replay_speed":
            speed = max(0.25, float(value or 1.0))
        elif action_key == "automatic_replay":
            status = "RUNNING_AUTOMATIC"
        updated = ReplaySession(
            replay_id=session.replay_id,
            workflow_id=session.workflow_id,
            decision_object_id=session.decision_object_id,
            status=status,
            current_revision=revision,
            current_stage=stage,
            replay_speed=speed,
            created_timestamp=session.created_timestamp,
            audit_identifier=session.audit_identifier,
        )
        self._replay_sessions[index] = updated
        self._audit("Replay Control", replay_id, f"{action} applied to replay session.")
        return asdict(updated)

    def _decision_comparison(self, experiment: Experiment, performance_truth: dict[str, Any]) -> dict[str, Any]:
        original = _decision_by_id(experiment.original_decision_object_id, performance_truth)
        exp = experiment.experiment_decision_object
        return {
            "comparisonId": f"DL-CMP-{experiment.experiment_id[-6:]}",
            "originalDecisionObjectId": experiment.original_decision_object_id,
            "experimentDecisionObjectId": exp["decisionObjectId"],
            "differences": {
                "recommendation": (original.get("final_recommendation", ""), exp.get("recommendation", "")),
                "confidence": (original.get("confidence", 0.0), exp.get("confidence", 0.0)),
                "risk": (original.get("risk_accuracy", 0.0), exp.get("riskScore", 0.0)),
                "positionSize": (0.0, exp.get("positionSizeRecommendation", 0.0)),
                "expectedReturn": (original.get("expected_return", 0.0), exp.get("expectedReturn", 0.0)),
                "actualReturn": (original.get("actual_return", 0.0), "EXPERIMENT_ONLY"),
                "predictionError": (original.get("prediction_error", 0.0), "SIMULATED_ONLY"),
                "officeChanges": tuple(experiment.parameter_changes.keys()),
            },
        }

    def _performance_comparison(self, experiment: Experiment, performance_truth: dict[str, Any]) -> dict[str, Any]:
        outcome = _outcome_by_decision(experiment.original_decision_object_id, performance_truth)
        expected = float(experiment.experiment_decision_object.get("expectedReturn", 0.0))
        original_return = float(outcome.get("actual_return", 0.0))
        simulated_return = round(original_return + (expected - float(outcome.get("expected_return", 0.0))) * 0.25, 6)
        return {
            "performanceComparisonId": f"DL-PCMP-{experiment.experiment_id[-6:]}",
            "originalOutcome": original_return,
            "experimentOutcome": simulated_return,
            "difference": round(simulated_return - original_return, 6),
            "alpha": round(simulated_return * 100 - 0.82, 4),
            "drawdown": max(0.0, round(float(experiment.experiment_decision_object.get("riskScore", 0.0)) * 100, 4)),
            "sharpe": round(max(0.0, simulated_return) * 10, 4),
            "capitalGrowth": round(simulated_return * 100, 4),
            "winRate": 100.0 if simulated_return >= 0 else 0.0,
            "risk": experiment.experiment_decision_object.get("riskScore", 0.0),
        }

    def _historian_report(self, experiment: Experiment, performance_truth: dict[str, Any]) -> dict[str, Any]:
        comparison = self._performance_comparison(experiment, performance_truth)
        return {
            "historianReportId": f"DL-HIST-{experiment.experiment_id[-6:]}",
            "originalDecisionObject": experiment.original_decision_object_id,
            "experimentDecisionObject": experiment.experiment_decision_object["decisionObjectId"],
            "performanceTruthSource": "IMMUTABLE_LEDGER",
            "outcomeDifference": comparison["difference"],
            "lessonsLearned": ("Counterfactual changes are isolated from production truth.", "Outcome deltas require Historian validation before doctrine changes."),
            "improvementOpportunities": tuple(experiment.parameter_changes.keys()),
            "potentialStrategyUpdates": ("candidate_for_historian_review",),
            "productionStrategyModified": False,
        }

    def _decision_tree(self, replay_packages: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
        roots = []
        for package in replay_packages:
            decision_id = package["decisionObjectId"]
            children = [experiment.experiment_id for experiment in self._experiments if experiment.original_decision_object_id == decision_id and not experiment.parent_experiment_id]
            roots.append({"nodeId": decision_id, "type": "Original", "workflowId": package["workflowId"], "children": tuple(children)})
        for experiment in self._experiments:
            children = [item.experiment_id for item in self._experiments if item.parent_experiment_id == experiment.experiment_id]
            roots.append({"nodeId": experiment.experiment_id, "type": "Experiment", "workflowId": experiment.original_workflow_id, "children": tuple(children)})
        return tuple(roots)

    def _audit(self, action: str, target: str, summary: str) -> None:
        self._experiment_audit.append(
            ExperimentAudit(
                audit_id=f"DL-AUD-{len(self._experiment_audit) + 1:06d}",
                timestamp=utc_timestamp(),
                action=action,
                target_identifier=target,
                summary=summary,
                immutable_production_preserved=True,
            )
        )


def _completed_workflows(orchestrator: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    return tuple(item for item in orchestrator.get("workflows", ()) if item.get("token", {}).get("workflow_status") == "Archived")


def _workflow_replay_package(workflow: dict[str, Any], performance_truth: dict[str, Any]) -> dict[str, Any]:
    latest = _latest_decision(workflow)
    outcome = _outcome_by_decision(latest.get("decisionObjectId", ""), performance_truth)
    trade = next((item for item in performance_truth.get("tradeLedger", ()) if item["workflow_id"] == workflow["workflow_id"]), {})
    order = next((item for item in performance_truth.get("orderLedger", ()) if item["workflow_id"] == workflow["workflow_id"]), {})
    return {
        "workflowId": workflow["workflow_id"],
        "decisionObjectId": latest.get("decisionObjectId", ""),
        "workflowTokenId": workflow["token"]["audit_identifier"],
        "strategy": trade.get("strategy_id") or order.get("strategy_id", latest.get("currentStrategy", "")),
        "executionEnvironment": trade.get("execution_environment") or order.get("execution_environment", "paper"),
        "brokerOrderStatus": order.get("status", ""),
        "brokerOrderSymbol": order.get("symbol", ""),
        "portfolioOutcome": outcome.get("actual_trade_result", 0.0),
        "officeSequence": tuple(workflow.get("stages", ())),
        "executionTimeline": tuple(_timeline_from_outputs(workflow)),
        "promptVersions": tuple(_prompt_versions_from_outputs(workflow)),
        "replayable": True,
    }


def _decision_replay(package: dict[str, Any]) -> dict[str, Any]:
    return {
        "workflowId": package["workflowId"],
        "decisionObjectId": package["decisionObjectId"],
        "revisionFlow": tuple(item["revision"] for item in package["executionTimeline"]),
        "revisions": tuple(package["executionTimeline"]),
    }


def _office_replay(package: dict[str, Any]) -> dict[str, Any]:
    return {
        "workflowId": package["workflowId"],
        "decisionObjectId": package["decisionObjectId"],
        "offices": tuple(
            {
                "office": item["office"],
                "question": _office_question(item["office"]),
                "changeSummary": item["structuredOutput"].get("summary", ""),
                "confidence": item["confidence"],
                "risk": item["risk"],
                "recommendation": item["recommendation"],
            }
            for item in package["executionTimeline"]
        ),
    }


def _timeline_from_outputs(workflow: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    rows = []
    for index, output in enumerate(workflow.get("output_history", ()), start=1):
        decision = output.get("decision_object", {})
        rows.append(
            {
                "revision": index,
                "office": output.get("workflow_stage", ""),
                "timestamp": workflow["token"]["creation_timestamp"],
                "confidence": decision.get("confidence", 0.0),
                "evidence": output.get("evidence", ""),
                "signals": tuple(decision.get("supportingSignals", ())),
                "recommendation": decision.get("recommendation", ""),
                "risk": decision.get("riskScore", 0.0),
                "positionSize": decision.get("positionSizeRecommendation", 0.0),
                "expectedReturn": decision.get("expectedReturn", 0.0),
                "structuredOutput": dict(output),
                "promptContract": dict(output.get("prompt_contract", {})),
                "promptVersion": output.get("prompt_contract", {}).get("promptVersion", ""),
                "promptTemplateId": output.get("prompt_contract", {}).get("promptTemplateId", ""),
                "schemaVersion": output.get("prompt_contract", {}).get("schemaVersion", ""),
            }
        )
    return tuple(rows)


def _prompt_versions_from_outputs(workflow: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    versions = []
    for output in workflow.get("output_history", ()):
        prompt_contract = output.get("prompt_contract", {})
        versions.append(
            {
                "office": output.get("workflow_stage", ""),
                "promptVersion": prompt_contract.get("promptVersion", ""),
                "promptTemplateId": prompt_contract.get("promptTemplateId", ""),
                "officeVersion": prompt_contract.get("officeVersion", ""),
                "schemaVersion": prompt_contract.get("schemaVersion", ""),
                "contractVersion": prompt_contract.get("contractVersion", ""),
                "responseValidationResult": prompt_contract.get("responseValidationResult", ""),
                "replayable": bool(prompt_contract.get("replayable", False)),
            }
        )
    return tuple(versions)


def _prompt_revision_comparison(package: dict[str, Any]) -> dict[str, Any]:
    versions = tuple(package.get("promptVersions", ()))
    unique_templates = tuple(sorted({item["promptTemplateId"] for item in versions if item.get("promptTemplateId")}))
    return {
        "workflowId": package["workflowId"],
        "decisionObjectId": package["decisionObjectId"],
        "promptVersions": versions,
        "uniquePromptTemplates": unique_templates,
        "historianComparisonStatus": "READY_FOR_HISTORIAN_REVIEW" if versions else "NO_PROMPT_HISTORY",
        "allPromptVersionsPreserved": all(item.get("promptVersion") for item in versions),
        "allSchemaVersionsPreserved": all(item.get("schemaVersion") for item in versions),
    }


def _latest_decision(workflow: dict[str, Any]) -> dict[str, Any]:
    for output in reversed(workflow.get("output_history", ())):
        if output.get("decision_object"):
            return output["decision_object"]
    return {}


def _outcome_by_decision(decision_object_id: str, performance_truth: dict[str, Any]) -> dict[str, Any]:
    return next((item for item in performance_truth.get("decisionObjectOutcomes", ()) if item["decision_object_id"] == decision_object_id), {})


def _decision_by_id(decision_object_id: str, performance_truth: dict[str, Any]) -> dict[str, Any]:
    return _outcome_by_decision(decision_object_id, performance_truth)


def _office_question(office: str) -> str:
    return {
        "Seeker": "What information was discovered?",
        "Analyst": "What changed?",
        "Risk": "What risks were added or removed?",
        "Trader": "Why was the trade executed?",
        "Historian": "How was knowledge archived?",
    }.get(office, "What contribution was made?")


def _search(query: str, replay_packages: tuple[dict[str, Any], ...], experiments: list[Experiment], performance_truth: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    needle = query.lower()
    results: list[dict[str, Any]] = []
    for package in replay_packages:
        haystack = " ".join(str(value) for value in package.values()).lower()
        if needle in haystack:
            results.append({"type": "Workflow Replay", "identifier": package["workflowId"], "summary": package["decisionObjectId"]})
    for trade in performance_truth.get("tradeLedger", ()):
        haystack = " ".join(str(value) for value in trade.values()).lower()
        if needle in haystack:
            results.append({"type": "Trade Ledger", "identifier": trade["trade_id"], "summary": trade["symbol"]})
    for order in performance_truth.get("orderLedger", ()):
        haystack = " ".join(str(value) for value in order.values()).lower()
        if needle in haystack:
            results.append({"type": "Broker Order", "identifier": order["order_id"], "summary": order["symbol"]})
    for experiment in experiments:
        haystack = " ".join(str(value) for value in asdict(experiment).values()).lower()
        if needle in haystack:
            results.append({"type": "Experiment", "identifier": experiment.experiment_id, "summary": experiment.original_decision_object_id})
    return tuple(results)

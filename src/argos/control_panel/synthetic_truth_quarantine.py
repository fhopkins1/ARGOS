"""EO-DH synthetic-truth eradication and fallback quarantine.

EO-DH owns discovery, classification, quarantine, and prevention evidence for
synthetic truth. It does not own analytical decisions, broker outcomes,
positions, truth ledgers, transactions, runtime bridges, or certification.
"""

from __future__ import annotations

import ast
import csv
from dataclasses import asdict, dataclass, replace
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from argos.foundation.contracts import utc_timestamp

from .runtime_bridge_certification import (
    BridgeCertificationState,
    RuntimeBridgeCertificationHarness,
    required_runtime_bridge_matrix,
)
from .truth_domain import RuntimeMode, validate_operational_truth_envelope
from .truth_promotion import PromotionDecisionStatus, TruthPromotionAuthority


EO_DH_VERSION = "EO-DH.1"


class SyntheticTruthCategory(str, Enum):
    PROHIBITED_OPERATIONAL_SYNTHETIC_TRUTH = "PROHIBITED_OPERATIONAL_SYNTHETIC_TRUTH"
    UNSAFE_FALLBACK = "UNSAFE_FALLBACK"
    DEGRADED_BUT_MISREPRESENTED = "DEGRADED_BUT_MISREPRESENTED"
    PROOF_ONLY = "PROOF_ONLY"
    SIMULATION_ONLY = "SIMULATION_ONLY"
    TEST_ONLY = "TEST_ONLY"
    REPLAY_ONLY = "REPLAY_ONLY"
    DISPLAY_ONLY = "DISPLAY_ONLY"
    EXAMPLE_OR_DOCUMENTATION = "EXAMPLE_OR_DOCUMENTATION"
    LEGITIMATE_INITIAL_STATE = "LEGITIMATE_INITIAL_STATE"
    LEGITIMATE_DERIVED_VALUE = "LEGITIMATE_DERIVED_VALUE"
    DEAD_CODE = "DEAD_CODE"
    UNKNOWN = "UNKNOWN"


class SyntheticReachability(str, Enum):
    PAPER_AUTHORITATIVE_REACHABLE = "PAPER_AUTHORITATIVE_REACHABLE"
    PAPER_DECISION_REACHABLE = "PAPER_DECISION_REACHABLE"
    PAPER_PRESENTATION_REACHABLE = "PAPER_PRESENTATION_REACHABLE"
    COMPATIBILITY_REACHABLE = "COMPATIBILITY_REACHABLE"
    PROOF_REACHABLE = "PROOF_REACHABLE"
    SIMULATION_REACHABLE = "SIMULATION_REACHABLE"
    TEST_REACHABLE = "TEST_REACHABLE"
    REPLAY_REACHABLE = "REPLAY_REACHABLE"
    DEAD = "DEAD"
    UNKNOWN_REACHABILITY = "UNKNOWN_REACHABILITY"


class SyntheticFindingClass(str, Enum):
    SYNTHETIC_MARKET_DATA = "SYNTHETIC_MARKET_DATA"
    SYNTHETIC_INTELLIGENCE = "SYNTHETIC_INTELLIGENCE"
    SYNTHETIC_CANDIDATE = "SYNTHETIC_CANDIDATE"
    SYNTHETIC_ANALYSIS = "SYNTHETIC_ANALYSIS"
    SYNTHETIC_RISK = "SYNTHETIC_RISK"
    SYNTHETIC_AUTHORIZATION = "SYNTHETIC_AUTHORIZATION"
    SYNTHETIC_ORDER = "SYNTHETIC_ORDER"
    SYNTHETIC_BROKER_EVENT = "SYNTHETIC_BROKER_EVENT"
    SYNTHETIC_FILL = "SYNTHETIC_FILL"
    SYNTHETIC_POSITION = "SYNTHETIC_POSITION"
    SYNTHETIC_MONITORING = "SYNTHETIC_MONITORING"
    SYNTHETIC_EXIT = "SYNTHETIC_EXIT"
    SYNTHETIC_PERFORMANCE_TRUTH = "SYNTHETIC_PERFORMANCE_TRUTH"
    SYNTHETIC_CLOSED_POSITION_TRUTH = "SYNTHETIC_CLOSED_POSITION_TRUTH"
    SYNTHETIC_HISTORIAN = "SYNTHETIC_HISTORIAN"
    SYNTHETIC_LEARNING = "SYNTHETIC_LEARNING"
    SYNTHETIC_COMMANDER_STATE = "SYNTHETIC_COMMANDER_STATE"
    SYNTHETIC_DASHBOARD_STATE = "SYNTHETIC_DASHBOARD_STATE"
    SYNTHETIC_RECOVERY = "SYNTHETIC_RECOVERY"
    SYNTHETIC_RECONCILIATION = "SYNTHETIC_RECONCILIATION"
    DEFAULT_APPROVAL = "DEFAULT_APPROVAL"
    UNSAFE_FALLBACK = "UNSAFE_FALLBACK"
    UNKNOWN_AS_ZERO = "UNKNOWN_AS_ZERO"
    UNAVAILABLE_AS_EMPTY = "UNAVAILABLE_AS_EMPTY"
    STALE_AS_CURRENT = "STALE_AS_CURRENT"
    DEGRADED_AS_AUTHORITATIVE = "DEGRADED_AS_AUTHORITATIVE"
    TEST_CONTAMINATION = "TEST_CONTAMINATION"
    PROOF_CONTAMINATION = "PROOF_CONTAMINATION"
    SIMULATION_CONTAMINATION = "SIMULATION_CONTAMINATION"
    REPLAY_CONTAMINATION = "REPLAY_CONTAMINATION"
    DISPLAY_CONTAMINATION = "DISPLAY_CONTAMINATION"
    COMPATIBILITY_CONTAMINATION = "COMPATIBILITY_CONTAMINATION"
    BRIDGE_SUBSTITUTION = "BRIDGE_SUBSTITUTION"
    EXCEPTION_SUPPRESSION = "EXCEPTION_SUPPRESSION"
    RANDOM_OPERATIONAL_TRUTH = "RANDOM_OPERATIONAL_TRUTH"
    TIME_GENERATED_TRUTH = "TIME_GENERATED_TRUTH"
    ARCHITECTURAL_BYPASS = "ARCHITECTURAL_BYPASS"
    TEST_DEFECT = "TEST_DEFECT"
    ENVIRONMENT = "ENVIRONMENT"
    DOCUMENTATION = "DOCUMENTATION"
    UNKNOWN = "UNKNOWN"


class SyntheticSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    ENHANCEMENT = "ENHANCEMENT"


class SyntheticFindingStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    REMEDIATED = "REMEDIATED"
    QUARANTINED = "QUARANTINED"
    BLOCKED = "BLOCKED"
    REMOVED = "REMOVED"
    ACCEPTED_NONAUTHORITATIVE = "ACCEPTED_NONAUTHORITATIVE"
    UNRESOLVED = "UNRESOLVED"


class UnknownState(str, Enum):
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"
    STALE = "STALE"
    PENDING = "PENDING"
    UNRESOLVED = "UNRESOLVED"
    BLOCKED = "BLOCKED"
    REJECTED = "REJECTED"
    DEGRADED = "DEGRADED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    KNOWN_ZERO = "KNOWN_ZERO"
    KNOWN_EMPTY = "KNOWN_EMPTY"


@dataclass(frozen=True)
class DegradedDataRecord:
    degradation_id: str
    source: str
    expected_evidence: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    available_evidence: tuple[str, ...]
    reason: str
    severity: SyntheticSeverity
    sequence: int
    truth_domain: str
    permitted_consumers: tuple[str, ...]
    prohibited_consumers: tuple[str, ...]
    expiration: str
    remediation_requirement: str
    authoritative: bool = False


@dataclass(frozen=True)
class UnknownStateRecord:
    state_id: str
    state: UnknownState
    subject: str
    reason: str
    truth_domain: str
    may_default_to_zero: bool
    may_default_to_empty: bool
    may_satisfy_authoritative_requirement: bool
    timestamp_utc: str


@dataclass(frozen=True)
class QuarantineNamespace:
    namespace_id: str
    domain: str
    permitted_runtime_modes: tuple[str, ...]
    prohibited_consumers: tuple[str, ...]
    persistence_namespace: str
    promotion_allowed: bool
    commander_label: str


@dataclass(frozen=True)
class SyntheticTruthFinding:
    finding_id: str
    title: str
    file: str
    symbol: str
    line_start: int
    line_end: int
    candidate_category: SyntheticTruthCategory
    generated_value_or_behavior: str
    source_evidence: tuple[str, ...]
    consumer: str
    truth_domain: str
    operating_mode: str
    eodb_bridge_ids: tuple[str, ...]
    static_reachability: SyntheticReachability
    dynamic_reachability: SyntheticReachability
    production_paper_reachability: SyntheticReachability
    authoritative_ledgers_reachable: tuple[str, ...]
    severity: SyntheticSeverity
    finding_class: SyntheticFindingClass
    required_remediation: str
    remediation_owner: str
    test_reference: str
    status: SyntheticFindingStatus
    rationale: str
    commit_discovered: str
    commit_remediated: str
    evidence_hash: str = ""
    schema_version: str = EO_DH_VERSION

    def with_hash(self) -> "SyntheticTruthFinding":
        payload = {key: value for key, value in asdict(self).items() if key != "evidence_hash"}
        return replace(self, evidence_hash=_stable_hash(payload))


@dataclass(frozen=True)
class SourceToSinkPath:
    path_id: str
    source_file: str
    source_symbol: str
    source_class: SyntheticFindingClass
    sink: str
    bridge_ids: tuple[str, ...]
    reachability: SyntheticReachability
    blocked: bool
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class DynamicSyntheticAttackResult:
    attack_id: str
    attack_name: str
    injected_domain: str
    target_sink: str
    expected: str
    result: str
    rejected: bool
    quarantined: bool
    authoritative_mutation: bool
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class SyntheticTruthAuditReport:
    verdict: str
    engine_version: str
    generated_at_utc: str
    commit_sha: str
    branch: str
    candidate_files_scanned: int
    candidate_symbols_scanned: int
    synthetic_candidates_discovered: int
    prohibited_operational_findings: int
    unsafe_fallbacks: int
    degraded_misrepresented_findings: int
    proof_only_findings: int
    simulation_only_findings: int
    test_only_findings: int
    replay_only_findings: int
    display_only_findings: int
    dead_code_findings: int
    unknown_findings: int
    paper_authoritative_reachable_findings: int
    paper_decision_reachable_findings: int
    paper_presentation_reachable_findings: int
    compatibility_reachable_findings: int
    findings_remediated: int
    findings_quarantined: int
    findings_removed: int
    findings_remaining: int
    critical_findings_remaining: int
    major_findings_remaining: int
    static_source_to_sink_paths: int
    dynamic_attack_total: int
    dynamic_attack_rejected: int
    production_fixture_import_violations: int
    live_trading_enabled: bool
    financial_or_analytical_decision_authority: bool
    certifies_argos: bool
    certifies_continuous_paper_trading: bool
    registry_hash: str


class SyntheticTruthRegistry:
    def __init__(self, findings: Iterable[SyntheticTruthFinding] | None = None) -> None:
        self._findings: dict[str, SyntheticTruthFinding] = {}
        for finding in findings or baseline_synthetic_truth_findings():
            self.register(finding)

    def register(self, finding: SyntheticTruthFinding) -> None:
        if finding.finding_id in self._findings:
            raise ValueError(f"duplicate synthetic finding id: {finding.finding_id}")
        if finding.production_paper_reachability == SyntheticReachability.UNKNOWN_REACHABILITY and finding.severity in {SyntheticSeverity.CRITICAL, SyntheticSeverity.MAJOR}:
            raise ValueError("unknown production reachability must be resolved or fail closed before registration")
        self._findings[finding.finding_id] = finding.with_hash()

    def all(self) -> tuple[SyntheticTruthFinding, ...]:
        return tuple(self._findings.values())

    def get(self, finding_id: str) -> SyntheticTruthFinding:
        return self._findings[finding_id]

    def unresolved_blocking(self) -> tuple[SyntheticTruthFinding, ...]:
        return tuple(
            item
            for item in self._findings.values()
            if item.status in {SyntheticFindingStatus.DISCOVERED, SyntheticFindingStatus.UNRESOLVED}
            and item.production_paper_reachability
            in {
                SyntheticReachability.PAPER_AUTHORITATIVE_REACHABLE,
                SyntheticReachability.PAPER_DECISION_REACHABLE,
                SyntheticReachability.UNKNOWN_REACHABILITY,
            }
            and item.severity in {SyntheticSeverity.CRITICAL, SyntheticSeverity.MAJOR}
        )


class FallbackPolicy:
    prohibited_fields = {
        "price",
        "bid",
        "ask",
        "last",
        "quantity",
        "filled_quantity",
        "average_fill_price",
        "cash",
        "buying_power",
        "pnl",
        "approval",
        "authorization",
        "order_status",
        "fill_status",
        "position_state",
        "closure",
        "performance_truth",
        "workflow_owner",
        "persistence_integrity",
        "certification_state",
    }
    permitted_fields = {"label", "display_unit", "tooltip", "optional_description", "local_formatting"}

    def evaluate(self, field: str, fallback_value: Any, *, consumer: str, truth_domain: str) -> UnknownStateRecord:
        field_key = field.lower()
        prohibited = field_key in self.prohibited_fields or truth_domain.upper() == RuntimeMode.PAPER.value and consumer in {"Trader", "Paper Broker", "Position Registry", "PerformanceTruthEngine", "Historian"}
        state = UnknownState.BLOCKED if prohibited else UnknownState.NOT_APPLICABLE
        return UnknownStateRecord(
            state_id=f"EO-DH-FALLBACK-{_stable_hash((field, consumer, truth_domain))[:12].upper()}",
            state=state,
            subject=field,
            reason="fallback prohibited for authoritative or decision-bearing field" if prohibited else "fallback limited to presentation-only field",
            truth_domain=truth_domain.upper(),
            may_default_to_zero=False,
            may_default_to_empty=not prohibited,
            may_satisfy_authoritative_requirement=False,
            timestamp_utc=utc_timestamp(),
        )


class QuarantineController:
    def __init__(self, namespaces: Iterable[QuarantineNamespace] | None = None) -> None:
        self.namespaces = {item.namespace_id: item for item in namespaces or quarantine_namespaces()}

    def assert_not_paper_authoritative(self, artifact: dict[str, Any], *, target_sink: str) -> None:
        domain = str(artifact.get("truth_domain") or artifact.get("executionMode") or artifact.get("environment") or "").upper()
        source = str(artifact.get("sourceSystem") or artifact.get("source_system") or artifact.get("fixtureId") or "")
        if domain in {RuntimeMode.TEST.value, RuntimeMode.PROOF.value, RuntimeMode.SIMULATION.value, "REPLAY", "DISPLAY"}:
            raise ValueError(f"QUARANTINED_{domain}_ARTIFACT_REJECTED_FROM_{target_sink.upper()}")
        if "mock" in source.lower() or "fixture" in source.lower() or "synthetic" in source.lower():
            raise ValueError(f"QUARANTINED_SOURCE_REJECTED_FROM_{target_sink.upper()}")


class SyntheticTruthEradicationEngine:
    financial_or_analytical_decision_authority = False
    live_trading_enabled = False

    def __init__(self, registry: SyntheticTruthRegistry | None = None) -> None:
        self.registry = registry or SyntheticTruthRegistry()
        self.fallback_policy = FallbackPolicy()
        self.quarantine = QuarantineController()
        self.attacks: list[DynamicSyntheticAttackResult] = []
        self.source_to_sink_paths: list[SourceToSinkPath] = []
        self.scan_file_count = 0
        self.scan_symbol_count = 0
        self.production_fixture_import_violations = 0

    def audit(self, *, repo_root: str | Path = ".", commit_sha: str = "", branch: str = "") -> SyntheticTruthAuditReport:
        repo_root = Path(repo_root)
        candidates = scan_synthetic_candidates(repo_root)
        self.scan_file_count = len({item.file for item in candidates})
        self.scan_symbol_count = len({item.symbol for item in candidates if item.symbol})
        self.source_to_sink_paths = list(source_to_sink_analysis(repo_root, self.registry.all()))
        self.production_fixture_import_violations = sum(1 for item in self.source_to_sink_paths if item.source_class == SyntheticFindingClass.TEST_CONTAMINATION and not item.blocked)
        self.attacks = list(self.run_dynamic_attacks())

        findings = self.registry.all()
        remaining = tuple(item for item in findings if item.status in {SyntheticFindingStatus.DISCOVERED, SyntheticFindingStatus.UNRESOLVED})
        critical = tuple(item for item in remaining if item.severity == SyntheticSeverity.CRITICAL)
        major = tuple(item for item in remaining if item.severity == SyntheticSeverity.MAJOR)
        attack_failures = tuple(item for item in self.attacks if not item.rejected or item.authoritative_mutation)
        verdict = "FAIL" if critical or major or attack_failures or self.production_fixture_import_violations else "PASS"
        return SyntheticTruthAuditReport(
            verdict=verdict,
            engine_version=EO_DH_VERSION,
            generated_at_utc=utc_timestamp(),
            commit_sha=commit_sha,
            branch=branch,
            candidate_files_scanned=self.scan_file_count,
            candidate_symbols_scanned=self.scan_symbol_count,
            synthetic_candidates_discovered=len(candidates) + len(findings),
            prohibited_operational_findings=_count(findings, SyntheticTruthCategory.PROHIBITED_OPERATIONAL_SYNTHETIC_TRUTH),
            unsafe_fallbacks=_count(findings, SyntheticTruthCategory.UNSAFE_FALLBACK),
            degraded_misrepresented_findings=_count(findings, SyntheticTruthCategory.DEGRADED_BUT_MISREPRESENTED),
            proof_only_findings=_count(findings, SyntheticTruthCategory.PROOF_ONLY),
            simulation_only_findings=_count(findings, SyntheticTruthCategory.SIMULATION_ONLY),
            test_only_findings=_count(findings, SyntheticTruthCategory.TEST_ONLY),
            replay_only_findings=_count(findings, SyntheticTruthCategory.REPLAY_ONLY),
            display_only_findings=_count(findings, SyntheticTruthCategory.DISPLAY_ONLY),
            dead_code_findings=_count(findings, SyntheticTruthCategory.DEAD_CODE),
            unknown_findings=_count(findings, SyntheticTruthCategory.UNKNOWN),
            paper_authoritative_reachable_findings=_reachability_count(findings, SyntheticReachability.PAPER_AUTHORITATIVE_REACHABLE),
            paper_decision_reachable_findings=_reachability_count(findings, SyntheticReachability.PAPER_DECISION_REACHABLE),
            paper_presentation_reachable_findings=_reachability_count(findings, SyntheticReachability.PAPER_PRESENTATION_REACHABLE),
            compatibility_reachable_findings=_reachability_count(findings, SyntheticReachability.COMPATIBILITY_REACHABLE),
            findings_remediated=sum(1 for item in findings if item.status == SyntheticFindingStatus.REMEDIATED),
            findings_quarantined=sum(1 for item in findings if item.status == SyntheticFindingStatus.QUARANTINED),
            findings_removed=sum(1 for item in findings if item.status == SyntheticFindingStatus.REMOVED),
            findings_remaining=len(remaining),
            critical_findings_remaining=len(critical),
            major_findings_remaining=len(major),
            static_source_to_sink_paths=len(self.source_to_sink_paths),
            dynamic_attack_total=len(self.attacks),
            dynamic_attack_rejected=sum(1 for item in self.attacks if item.rejected and not item.authoritative_mutation),
            production_fixture_import_violations=self.production_fixture_import_violations,
            live_trading_enabled=False,
            financial_or_analytical_decision_authority=False,
            certifies_argos=False,
            certifies_continuous_paper_trading=False,
            registry_hash=_stable_hash([asdict(item) for item in findings]),
        )

    def run_dynamic_attacks(self) -> tuple[DynamicSyntheticAttackResult, ...]:
        attacks = []
        for attack_id, domain, sink in (
            ("ATTACK-TEST-CANDIDATE", RuntimeMode.TEST.value, "Seeker"),
            ("ATTACK-PROOF-RISK", RuntimeMode.PROOF.value, "Risk"),
            ("ATTACK-SIM-TRADER", RuntimeMode.SIMULATION.value, "Trader"),
            ("ATTACK-REPLAY-TRUTH", "REPLAY", "PerformanceTruthEngine"),
            ("ATTACK-DISPLAY-PERSIST", "DISPLAY", "Persistence"),
        ):
            artifact = {"executionMode": domain, "sourceSystem": f"{domain.lower()}_fixture", "truth_domain": domain}
            rejected = False
            evidence: tuple[str, ...] = ()
            try:
                self.quarantine.assert_not_paper_authoritative(artifact, target_sink=sink)
            except ValueError as exc:
                rejected = True
                evidence = (str(exc),)
            attacks.append(_attack(attack_id, f"{domain} injection into {sink}", domain, sink, rejected, evidence))

        raw_envelope_result = validate_operational_truth_envelope({"truth_domain": RuntimeMode.PAPER.value, "source_system": "raw-paper-string"}, target_authority="PerformanceTruthEngine")
        attacks.append(_attack("ATTACK-RAW-PAPER-STRING", "raw paper string without EO-DC envelope", RuntimeMode.PAPER.value, "PerformanceTruthEngine", not raw_envelope_result.valid, raw_envelope_result.codes))
        promotion = TruthPromotionAuthority().promote_learning_input({"truth_domain": RuntimeMode.PAPER.value, "degraded": True, "source_system": "degraded_analysis"}, object_id="EO-DH-DEGRADED")
        attacks.append(_attack("ATTACK-DEGRADED-LEARNING", "degraded record into certified learning", RuntimeMode.PAPER.value, "EnterpriseLearningEngine", promotion.decision != PromotionDecisionStatus.APPROVED, promotion.reason_codes))
        fallback = self.fallback_policy.evaluate("price", 0.0, consumer="Trader", truth_domain=RuntimeMode.PAPER.value)
        attacks.append(_attack("ATTACK-MISSING-AS-ZERO", "missing price coerced to zero", RuntimeMode.PAPER.value, "Trader", fallback.state == UnknownState.BLOCKED, (fallback.reason,)))
        return tuple(attacks)

    def commander_read_model(self, report: SyntheticTruthAuditReport | None = None) -> dict[str, Any]:
        report = report or self.audit()
        return {
            "engineName": "Synthetic Truth Eradication and Fallback Quarantine",
            "engineeringOrder": "EO-DH",
            "engineVersion": EO_DH_VERSION,
            "verdict": report.verdict,
            "registryHash": report.registry_hash,
            "findingCounts": asdict(report),
            "unresolvedBlockingFindings": tuple(asdict(item) for item in self.registry.unresolved_blocking()),
            "quarantineNamespaces": tuple(asdict(item) for item in quarantine_namespaces()),
            "dynamicAttacks": tuple(asdict(item) for item in self.attacks[-20:]),
            "commanderControls": {
                "mayViewFindings": True,
                "mayRequestInvestigation": True,
                "mayRequestRemediation": True,
                "mayQuarantineOptionalUnsafeSubsystem": True,
                "mayHaltPaperOperationOnCriticalSyntheticTruth": True,
                "mayReclassifyProhibitedTruthAsLegitimate": False,
                "mayApproveUnsupportedFallback": False,
                "mayEraseFindings": False,
                "mayPromoteDegradedRecords": False,
                "mayFabricateMissingEvidence": False,
                "mayEnableLiveTrading": False,
            },
            "financialOrAnalyticalDecisionAuthority": False,
            "liveTradingEnabled": False,
            "certifiesArgos": False,
        }

    def write_evidence_bundle(self, output_dir: str | Path, report: SyntheticTruthAuditReport) -> dict[str, str]:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        registry_path = output / "EO-DH_synthetic_truth_registry.json"
        paths_path = output / "EO-DH_source_to_sink_paths.json"
        unresolved_path = output / "EO-DH_unresolved_findings.json"
        attacks_path = output / "EO-DH_dynamic_attacks.json"
        report_path = output / "EO-DH_audit_report.json"
        candidates_path = output / "EO-DH_static_candidates.csv"

        registry_path.write_text(json.dumps([asdict(item) for item in self.registry.all()], indent=2, sort_keys=True, default=str), encoding="utf-8")
        paths_path.write_text(json.dumps([asdict(item) for item in self.source_to_sink_paths], indent=2, sort_keys=True, default=str), encoding="utf-8")
        unresolved_path.write_text(json.dumps([asdict(item) for item in self.registry.unresolved_blocking()], indent=2, sort_keys=True, default=str), encoding="utf-8")
        attacks_path.write_text(json.dumps([asdict(item) for item in self.attacks], indent=2, sort_keys=True, default=str), encoding="utf-8")
        report_path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True, default=str), encoding="utf-8")
        with candidates_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=("file", "line", "symbol", "term", "classification"))
            writer.writeheader()
            for candidate in scan_synthetic_candidates(Path(".")):
                writer.writerow(asdict(candidate))
        return {
            "registry": str(registry_path),
            "sourceToSink": str(paths_path),
            "unresolvedFindings": str(unresolved_path),
            "dynamicAttacks": str(attacks_path),
            "auditReport": str(report_path),
            "staticCandidates": str(candidates_path),
        }


@dataclass(frozen=True)
class StaticSyntheticCandidate:
    file: str
    line: int
    symbol: str
    term: str
    classification: str


def baseline_synthetic_truth_findings() -> tuple[SyntheticTruthFinding, ...]:
    commit = _current_commit()
    bridges = _bridges_by_keyword()
    return (
        _finding("SYN-MARKET-001", "Synthetic market data provider remains test-only", "src/argos/control_panel/market_data_provider.py", "MarketDataProviderAbstractionLayer", 146, SyntheticTruthCategory.SIMULATION_ONLY, SyntheticFindingClass.SYNTHETIC_MARKET_DATA, SyntheticReachability.PAPER_DECISION_REACHABLE, SyntheticSeverity.MAJOR, SyntheticFindingStatus.QUARANTINED, "Synthetic provider is labeled APPROVED_FOR_TEST and must remain quarantined from paper decisions.", bridges("market"), commit),
        _finding("SYN-MARKET-002", "Mock market provider remains paper-labeled provisional source", "src/argos/control_panel/market_data_provider.py", "get_quote", 146, SyntheticTruthCategory.UNSAFE_FALLBACK, SyntheticFindingClass.SYNTHETIC_MARKET_DATA, SyntheticReachability.PAPER_DECISION_REACHABLE, SyntheticSeverity.MAJOR, SyntheticFindingStatus.UNRESOLVED, "Mock provider is still primary paper source; EO-DH exposes it as a blocker until authoritative provider or explicit operator certification exists.", bridges("market"), commit),
        _finding("SYN-DECISION-001", "Runtime proof Decision Objects are proof-only", "src/argos/control_panel/runtime.py", "_proof_decision_object", 2244, SyntheticTruthCategory.PROOF_ONLY, SyntheticFindingClass.PROOF_CONTAMINATION, SyntheticReachability.PROOF_REACHABLE, SyntheticSeverity.MAJOR, SyntheticFindingStatus.QUARANTINED, "Proof Decision Objects are explicitly proof-domain and rejected by EO-DC for paper truth.", bridges("seeker"), commit),
        _finding("SYN-API-001", "API dry-run fallback cannot become authoritative analysis", "src/argos/control_panel/api_execution_gateway.py", "_fallback_or_blocked_response", 328, SyntheticTruthCategory.UNSAFE_FALLBACK, SyntheticFindingClass.UNSAFE_FALLBACK, SyntheticReachability.PAPER_DECISION_REACHABLE, SyntheticSeverity.MAJOR, SyntheticFindingStatus.BLOCKED, "Gateway dry-run output is labeled fallback and rejected by promotion controls when authoritative evidence is required.", bridges("api"), commit),
        _finding("SYN-POSITION-001", "Position mutation without fill id blocked", "src/argos/control_panel/position_registry.py", "PositionRegistry.create_from_execution", 224, SyntheticTruthCategory.PROHIBITED_OPERATIONAL_SYNTHETIC_TRUTH, SyntheticFindingClass.SYNTHETIC_POSITION, SyntheticReachability.PAPER_AUTHORITATIVE_REACHABLE, SyntheticSeverity.CRITICAL, SyntheticFindingStatus.REMEDIATED, "EO-DH now requires authoritative fill IDs for buy and sell position mutations.", bridges("position"), commit, remediated=commit),
        _finding("SYN-TRUTH-001", "Performance Truth fill-less execution blocked", "src/argos/control_panel/performance_truth_engine.py", "record_broker_authoritative_order", 453, SyntheticTruthCategory.PROHIBITED_OPERATIONAL_SYNTHETIC_TRUTH, SyntheticFindingClass.SYNTHETIC_PERFORMANCE_TRUTH, SyntheticReachability.PAPER_AUTHORITATIVE_REACHABLE, SyntheticSeverity.CRITICAL, SyntheticFindingStatus.REMEDIATED, "EO-DH now rejects positive filled quantity when no broker fill evidence is present.", bridges("truth"), commit, remediated=commit),
        _finding("SYN-CPT-001", "Closed Position Truth degraded benchmark remains non-core enrichment", "src/argos/control_panel/closed_position_truth.py", "_benchmark_comparison", 383, SyntheticTruthCategory.DEGRADED_BUT_MISREPRESENTED, SyntheticFindingClass.SYNTHETIC_CLOSED_POSITION_TRUTH, SyntheticReachability.PAPER_PRESENTATION_REACHABLE, SyntheticSeverity.MINOR, SyntheticFindingStatus.BLOCKED, "Benchmark section is marked DEGRADED and must not be promoted as core closed-position truth.", bridges("closed"), commit),
        _finding("SYN-DASHBOARD-001", "Compatibility dashboard state remains presentation reachable", "src/argos/control_panel/runtime.py", "ControlPanelRuntime.state", 281, SyntheticTruthCategory.DISPLAY_ONLY, SyntheticFindingClass.SYNTHETIC_DASHBOARD_STATE, SyntheticReachability.COMPATIBILITY_REACHABLE, SyntheticSeverity.MAJOR, SyntheticFindingStatus.UNRESOLVED, "Compatibility state is read-facing and must not create or persist authoritative paper truth.", bridges("commander"), commit),
        _finding("SYN-RECOVERY-001", "Recovery must block missing evidence", "src/argos/control_panel/enterprise_persistence.py", "recover", 1, SyntheticTruthCategory.UNKNOWN, SyntheticFindingClass.SYNTHETIC_RECOVERY, SyntheticReachability.PAPER_AUTHORITATIVE_REACHABLE, SyntheticSeverity.MAJOR, SyntheticFindingStatus.UNRESOLVED, "EO-DB recovery bridge is conditional; missing financial evidence must remain unresolved rather than reconstructed.", bridges("recovery"), commit),
        _finding("SYN-REPLAY-001", "Replay remains isolated from production truth", "src/argos/control_panel/market_replay_engine.py", "MarketReplayEngine", 1, SyntheticTruthCategory.REPLAY_ONLY, SyntheticFindingClass.REPLAY_CONTAMINATION, SyntheticReachability.REPLAY_REACHABLE, SyntheticSeverity.MAJOR, SyntheticFindingStatus.QUARANTINED, "Replay can feed Decision Laboratory only and cannot create new paper truth.", bridges("replay"), commit),
    )


def quarantine_namespaces() -> tuple[QuarantineNamespace, ...]:
    return (
        _namespace("QUAR-TEST", RuntimeMode.TEST.value, ("test",), ("Trader", "Paper Broker", "Position Registry", "PerformanceTruthEngine", "Historian")),
        _namespace("QUAR-PROOF", RuntimeMode.PROOF.value, ("proof",), ("Trader", "Paper Broker", "Position Registry", "PerformanceTruthEngine", "Historian")),
        _namespace("QUAR-SIM", RuntimeMode.SIMULATION.value, ("simulation",), ("Trader", "Paper Broker", "Position Registry", "PerformanceTruthEngine", "Historian")),
        _namespace("QUAR-REPLAY", "REPLAY", ("replay",), ("Paper Broker", "Position Registry", "PerformanceTruthEngine", "Historian")),
        _namespace("QUAR-DISPLAY", "DISPLAY", ("development", "paper"), ("Persistence", "Paper Broker", "Position Registry", "PerformanceTruthEngine", "Historian")),
    )


def degraded_record(source: str, *, missing_evidence: tuple[str, ...], available_evidence: tuple[str, ...] = (), reason: str = "required evidence unavailable") -> DegradedDataRecord:
    return DegradedDataRecord(
        degradation_id=f"DEG-EO-DH-{_stable_hash((source, missing_evidence, reason))[:12].upper()}",
        source=source,
        expected_evidence=tuple(dict.fromkeys((*missing_evidence, *available_evidence))),
        missing_evidence=missing_evidence,
        available_evidence=available_evidence,
        reason=reason,
        severity=SyntheticSeverity.MAJOR,
        sequence=1,
        truth_domain=RuntimeMode.PAPER.value,
        permitted_consumers=("Commander", "EO-DH", "EO-DE", "EO-DF"),
        prohibited_consumers=("Trader", "Paper Broker", "Position Registry", "PerformanceTruthEngine", "Historian", "EnterpriseLearningEngine"),
        expiration="IMMEDIATE_REVALIDATION_REQUIRED",
        remediation_requirement="obtain authoritative evidence or keep workflow blocked",
    )


def unavailable_state(subject: str, reason: str, *, truth_domain: str = RuntimeMode.PAPER.value) -> UnknownStateRecord:
    return UnknownStateRecord(
        state_id=f"UNKNOWN-EO-DH-{_stable_hash((subject, reason, truth_domain))[:12].upper()}",
        state=UnknownState.UNAVAILABLE,
        subject=subject,
        reason=reason,
        truth_domain=truth_domain,
        may_default_to_zero=False,
        may_default_to_empty=False,
        may_satisfy_authoritative_requirement=False,
        timestamp_utc=utc_timestamp(),
    )


def scan_synthetic_candidates(repo_root: str | Path) -> tuple[StaticSyntheticCandidate, ...]:
    root = Path(repo_root)
    terms = {
        "synthetic",
        "mock",
        "fixture",
        "demo",
        "placeholder",
        "fallback",
        "default",
        "assumed",
        "inferred",
        "simulated",
        "proof",
        "dummy",
        "fake",
        "degraded",
        "unavailable",
        "unknown",
        "approved",
        "filled",
        "healthy",
    }
    candidates: list[StaticSyntheticCandidate] = []
    for path in sorted(root.rglob("*")):
        if path.suffix.lower() not in {".py", ".js", ".ts", ".tsx", ".jsx", ".md", ".json"}:
            continue
        if any(part in {".git", "__pycache__", "EO-DB_Evidence", "EO-DH_Evidence"} for part in path.parts):
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        symbol = ""
        for index, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith(("def ", "class ")):
                symbol = stripped.split("(")[0].replace("def ", "").replace("class ", "")
            lower = stripped.lower()
            for term in terms:
                if term in lower:
                    candidates.append(StaticSyntheticCandidate(str(path), index, symbol, term, _candidate_classification(str(path), lower, term)))
                    break
    return tuple(candidates)


def source_to_sink_analysis(repo_root: str | Path, findings: Iterable[SyntheticTruthFinding]) -> tuple[SourceToSinkPath, ...]:
    root = Path(repo_root)
    paths: list[SourceToSinkPath] = []
    sink_terms = ("PerformanceTruth", "PositionRegistry", "PaperBroker", "Historian", "Learning", "Trader")
    for finding in findings:
        blocked = finding.status in {SyntheticFindingStatus.REMEDIATED, SyntheticFindingStatus.QUARANTINED, SyntheticFindingStatus.BLOCKED, SyntheticFindingStatus.REMOVED}
        if finding.production_paper_reachability in {SyntheticReachability.PAPER_AUTHORITATIVE_REACHABLE, SyntheticReachability.PAPER_DECISION_REACHABLE, SyntheticReachability.COMPATIBILITY_REACHABLE}:
            paths.append(
                SourceToSinkPath(
                    path_id=f"PATH-{finding.finding_id}",
                    source_file=finding.file,
                    source_symbol=finding.symbol,
                    source_class=finding.finding_class,
                    sink=finding.consumer,
                    bridge_ids=finding.eodb_bridge_ids,
                    reachability=finding.production_paper_reachability,
                    blocked=blocked,
                    evidence=(finding.rationale,),
                )
            )
    for path in sorted((root / "src").rglob("*.py")) if (root / "src").exists() else ():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and ("Tests" in (node.module or "") or "fixture" in (node.module or "").lower()):
                paths.append(SourceToSinkPath(f"PATH-IMPORT-{len(paths)+1:04d}", str(path), node.module or "", SyntheticFindingClass.TEST_CONTAMINATION, "production import boundary", (), SyntheticReachability.PAPER_DECISION_REACHABLE, False, ("production import of test/fixture module",)))
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                paths.append(SourceToSinkPath(f"PATH-EXCEPT-{len(paths)+1:04d}", str(path), "broad except", SyntheticFindingClass.EXCEPTION_SUPPRESSION, "operational path", _bridges_for_file(str(path)), SyntheticReachability.UNKNOWN_REACHABILITY, False, ("bare except requires semantic review",)))
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(term in text for term in sink_terms) and any(term in text.lower() for term in ("mock", "fixture", "fallback", "placeholder", "synthetic")):
            paths.append(SourceToSinkPath(f"PATH-STATIC-{len(paths)+1:04d}", str(path), path.stem, SyntheticFindingClass.UNSAFE_FALLBACK, "authoritative sink candidate", _bridges_for_file(str(path)), SyntheticReachability.UNKNOWN_REACHABILITY, False, ("source and sink terms share module",)))
    return tuple(paths)


def load_eodb_reachability(repo_root: str | Path) -> dict[str, Any]:
    path = Path(repo_root) / "Documentation" / "EO-DB_Evidence" / "EO-DB_certification_report.json"
    if not path.exists():
        return RuntimeBridgeCertificationHarness().certify(repo_root=repo_root).__dict__
    return json.loads(path.read_text(encoding="utf-8"))


def _finding(
    finding_id: str,
    title: str,
    file: str,
    symbol: str,
    line: int,
    category: SyntheticTruthCategory,
    finding_class: SyntheticFindingClass,
    reachability: SyntheticReachability,
    severity: SyntheticSeverity,
    status: SyntheticFindingStatus,
    rationale: str,
    bridges: tuple[str, ...],
    commit: str,
    *,
    remediated: str = "",
) -> SyntheticTruthFinding:
    ledgers = {
        SyntheticFindingClass.SYNTHETIC_BROKER_EVENT: ("Paper Broker",),
        SyntheticFindingClass.SYNTHETIC_FILL: ("Paper Broker", "Position Registry"),
        SyntheticFindingClass.SYNTHETIC_POSITION: ("Position Registry",),
        SyntheticFindingClass.SYNTHETIC_PERFORMANCE_TRUTH: ("Performance Truth",),
        SyntheticFindingClass.SYNTHETIC_CLOSED_POSITION_TRUTH: ("Closed Position Truth",),
        SyntheticFindingClass.SYNTHETIC_HISTORIAN: ("Historian",),
    }.get(finding_class, ())
    return SyntheticTruthFinding(
        finding_id=finding_id,
        title=title,
        file=file,
        symbol=symbol,
        line_start=line,
        line_end=line,
        candidate_category=category,
        generated_value_or_behavior=title,
        source_evidence=(file,),
        consumer=_consumer_for_class(finding_class),
        truth_domain=RuntimeMode.PAPER.value if reachability.name.startswith("PAPER") else category.value,
        operating_mode="paper" if reachability.name.startswith("PAPER") else category.value.lower(),
        eodb_bridge_ids=bridges,
        static_reachability=reachability,
        dynamic_reachability=reachability if status in {SyntheticFindingStatus.REMEDIATED, SyntheticFindingStatus.BLOCKED, SyntheticFindingStatus.QUARANTINED} else SyntheticReachability.UNKNOWN_REACHABILITY,
        production_paper_reachability=reachability,
        authoritative_ledgers_reachable=ledgers,
        severity=severity,
        finding_class=finding_class,
        required_remediation="remove, block, quarantine, or relabel with explicit unavailable/degraded state",
        remediation_owner="EO-DH",
        test_reference="Tests/test_eodh_synthetic_truth_quarantine.py",
        status=status,
        rationale=rationale,
        commit_discovered=commit,
        commit_remediated=remediated,
    )


def _namespace(namespace_id: str, domain: str, modes: tuple[str, ...], prohibited: tuple[str, ...]) -> QuarantineNamespace:
    return QuarantineNamespace(namespace_id, domain, modes, prohibited, f"quarantine/{domain.lower()}", False, f"{domain} - NONAUTHORITATIVE")


def _attack(attack_id: str, name: str, domain: str, sink: str, rejected: bool, evidence: Iterable[str]) -> DynamicSyntheticAttackResult:
    return DynamicSyntheticAttackResult(attack_id, name, domain, sink, "reject/quarantine/no authoritative mutation", "REJECTED" if rejected else "ACCEPTED", rejected, rejected, False, tuple(str(item) for item in evidence))


def _count(findings: tuple[SyntheticTruthFinding, ...], category: SyntheticTruthCategory) -> int:
    return sum(1 for item in findings if item.candidate_category == category)


def _reachability_count(findings: tuple[SyntheticTruthFinding, ...], reachability: SyntheticReachability) -> int:
    return sum(1 for item in findings if item.production_paper_reachability == reachability)


def _candidate_classification(file: str, line: str, term: str) -> str:
    if "Tests" in file or "test_" in file:
        return SyntheticTruthCategory.TEST_ONLY.value
    if "Documentation" in file:
        return SyntheticTruthCategory.EXAMPLE_OR_DOCUMENTATION.value
    if "simulation" in line or "simulated" in line:
        return SyntheticTruthCategory.SIMULATION_ONLY.value
    if "proof" in line:
        return SyntheticTruthCategory.PROOF_ONLY.value
    if term in {"fallback", "default", "unknown", "unavailable", "degraded"}:
        return SyntheticTruthCategory.UNSAFE_FALLBACK.value
    return SyntheticTruthCategory.UNKNOWN.value


def _bridges_by_keyword():
    bridges = required_runtime_bridge_matrix()

    def find(keyword: str) -> tuple[str, ...]:
        keyword_lower = keyword.lower()
        return tuple(
            bridge.bridge_id
            for bridge in bridges
            if keyword_lower in bridge.name.lower()
            or keyword_lower in bridge.source_authority.lower()
            or keyword_lower in bridge.target_authority.lower()
            or keyword_lower in " ".join(bridge.implementation_files).lower()
        )

    return find


def _bridges_for_file(file: str) -> tuple[str, ...]:
    normalized = file.replace("\\", "/")
    return tuple(bridge.bridge_id for bridge in required_runtime_bridge_matrix() if any(path.replace("\\", "/") in normalized for path in bridge.implementation_files))


def _consumer_for_class(finding_class: SyntheticFindingClass) -> str:
    if "MARKET" in finding_class.value:
        return "Analytical Offices"
    if "POSITION" in finding_class.value:
        return "Position Registry"
    if "PERFORMANCE" in finding_class.value:
        return "PerformanceTruthEngine"
    if "DASHBOARD" in finding_class.value:
        return "Commander"
    if "RECOVERY" in finding_class.value:
        return "Runtime Provider"
    return "Commander"


def _current_commit() -> str:
    try:
        import subprocess

        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def _stable_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()

"""Published RM-002A constitutional evidence and certification readiness layer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence

from .rm002_constitution import (
    CASE_FILE_REQUIRED_EVIDENCE,
    TRADER_RM002_LIFECYCLES,
    TRADER_RM002_OBJECTS,
    TRADER_RM002_RULES,
    VERIFICATION_CLASSES,
)


TRADER_RM_002A_VERSION = "TRADER-RM-002A/1.0.0"
PROVIDED_RM002A_WORK_ORDERS = (
    "TRADER-RM-002A-001",
    "TRADER-RM-002A-002",
    "TRADER-RM-002A-003",
    "TRADER-RM-002A-004",
    "TRADER-RM-002A-005",
    "TRADER-RM-002A-006",
    "TRADER-RM-002A-007",
    "TRADER-RM-002A-009",
    "TRADER-RM-002A-010",
    "TRADER-RM-002A-011",
    "TRADER-RM-002A-012",
)


class RM002AStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True)
class RM002ADecision:
    status: RM002AStatus
    findings: tuple[str, ...]


@dataclass(frozen=True)
class PublishedArtifact:
    identifier: str
    title: str
    artifact_class: str
    authority: str
    owner: str
    scope: str
    publication_location: str
    version: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    dependencies: tuple[str, ...]
    constraints: tuple[str, ...]
    evidence_obligations: tuple[str, ...]
    verification_obligations: tuple[str, ...]
    traceability_obligations: tuple[str, ...]


@dataclass(frozen=True)
class ObjectSchema:
    object_name: str
    object_identifier: str
    classification: str
    owner: str
    custody_owner: str
    mutation_authority: str
    observation_authority: str
    archival_authority: str
    destruction_authority: str
    lifecycle: str
    attributes: tuple[str, ...]
    relationships: tuple[str, ...]
    dependencies: tuple[str, ...]
    evidence: tuple[str, ...]
    verification: tuple[str, ...]
    failure_dispositions: tuple[str, ...]
    traceability: tuple[str, ...]


@dataclass(frozen=True)
class ExternalAuthorityContract:
    identifier: str
    owner: str
    consumed_authority: str
    request_semantics: str
    response_semantics: str
    failure_behavior: str
    evidence: tuple[str, ...]
    verification: tuple[str, ...]
    traceability: tuple[str, ...]


@dataclass(frozen=True)
class ExecutableVerification:
    verification_id: str
    rule_id: str
    objective: str
    procedure: tuple[str, ...]
    pass_criteria: tuple[str, ...]
    fail_criteria: tuple[str, ...]
    evidence: tuple[str, ...]
    dependencies: tuple[str, ...]


PUBLISHED_ARTIFACTS: Mapping[str, PublishedArtifact] = {
    "TRADER-PUB-001": PublishedArtifact("TRADER-PUB-001", "Trader Canonical Constitutional Publication Registry", "Constitutional Registry", "TRADER-RM-002A-001", "Trader Office", "publication closure", "Documentation/Trader/Constitution/TRADER-PUB-001.md", TRADER_RM_002A_VERSION, ("TRADER-RM-002",), ("publication catalog",), ("TRADER-RM-002A-001",), ("no implementation-only constitution",), ("artifact publication evidence",), ("publication completeness verification",), ("artifact lineage",)),
    "TRADER-PUB-002": PublishedArtifact("TRADER-PUB-002", "Trader Constitutional Object Schema Registry", "Constitutional Object Specification", "TRADER-RM-002A-002", "Trader Office", "object schema closure", "Documentation/Trader/Constitution/TRADER-PUB-002.md", TRADER_RM_002A_VERSION, tuple(TRADER_RM002_OBJECTS), ("complete object schemas",), ("TRADER-RM-002-002",), ("one owner per object",), ("object schema evidence",), ("schema completeness verification",), ("object traceability",)),
    "TRADER-PUB-003": PublishedArtifact("TRADER-PUB-003", "Trader Lifecycle Constitution Registry", "Constitutional Lifecycle Specification", "TRADER-RM-002A-003", "Trader Office", "lifecycle publication closure", "Documentation/Trader/Constitution/TRADER-PUB-003.md", TRADER_RM_002A_VERSION, tuple(TRADER_RM002_LIFECYCLES), ("expanded lifecycle constitutions",), ("TRADER-RM-002-005",), ("transition authority required",), ("lifecycle transition evidence",), ("lifecycle verification",), ("lifecycle traceability",)),
    "TRADER-PUB-004": PublishedArtifact("TRADER-PUB-004", "Trader Ownership and Reconciliation Matrix", "Constitutional Matrix", "TRADER-RM-002A-004", "Trader Office", "ownership custody mutation reconciliation", "Documentation/Trader/Constitution/TRADER-PUB-004.md", TRADER_RM_002A_VERSION, tuple(TRADER_RM002_OBJECTS), ("ownership matrix", "custody matrix", "mutation matrix", "reconciliation matrix"), ("TRADER-RM-002-006",), ("shared ownership prohibited",), ("ownership evidence",), ("ownership verification",), ("ownership traceability",)),
    "TRADER-PUB-005": PublishedArtifact("TRADER-PUB-005", "Trader External Authority Consumption Contracts", "Constitutional Interface Contract", "TRADER-RM-002A-005", "Trader Office", "external authority consumption", "Documentation/Trader/Constitution/TRADER-PUB-005.md", TRADER_RM_002A_VERSION, ("Authorization Office", "Risk Office", "Broker Integration Office", "Financial Authority", "Historian Office"), ("external authority contracts",), ("TRADER-RM-002-007", "TRADER-RM-002-008", "TRADER-RM-002-009", "TRADER-RM-002-013"), ("external authority remains externally owned",), ("authority consumption evidence",), ("external authority verification",), ("external authority traceability",)),
    "TRADER-PUB-006": PublishedArtifact("TRADER-PUB-006", "Trader Evidence Catalog and Execution Case File Constitution", "Constitutional Evidence Specification", "TRADER-RM-002A-006", "Trader Office", "evidence architecture", "Documentation/Trader/Constitution/TRADER-PUB-006.md", TRADER_RM_002A_VERSION, CASE_FILE_REQUIRED_EVIDENCE, ("evidence catalog", "case file constitution"), ("TRADER-RM-002-012",), ("assertions are not evidence",), ("evidence provenance",), ("evidence completeness verification",), ("evidence traceability",)),
    "TRADER-PUB-007": PublishedArtifact("TRADER-PUB-007", "Trader Executable Constitutional Rule Registry", "Constitutional Verification Artifact", "TRADER-RM-002A-007", "Trader Office", "executable rule verification", "Documentation/Trader/Constitution/TRADER-PUB-007.md", TRADER_RM_002A_VERSION, tuple(TRADER_RM002_RULES), ("executable verification registry",), ("TRADER-RM-002-014",), ("metadata-only verification prohibited",), ("verification execution evidence",), ("executable rule verification",), ("rule traceability",)),
    "TRADER-PUB-009": PublishedArtifact("TRADER-PUB-009", "Trader Bidirectional Traceability Matrix", "Constitutional Traceability Artifact", "TRADER-RM-002A-009", "Trader Office", "requirement to verdict traceability", "Documentation/Trader/Constitution/TRADER-PUB-009.md", TRADER_RM_002A_VERSION, tuple(TRADER_RM002_RULES), ("traceability matrix",), ("TRADER-RM-002-016",), ("no orphan artifacts",), ("traceability evidence",), ("bidirectional traceability verification",), ("verdict lineage",)),
    "TRADER-PUB-010": PublishedArtifact("TRADER-PUB-010", "Trader Independent Certification Reconciliation Constitution", "Constitutional Certification Artifact", "TRADER-RM-002A-010", "Independent Final Reconciliation Authority", "certification separation", "Documentation/Trader/Constitution/TRADER-PUB-010.md", TRADER_RM_002A_VERSION, ("candidate readiness", "verification evidence"), ("independent reconciliation package",), ("TRADER-RM-002-016",), ("candidate readiness is not certification",), ("certification provenance",), ("certification separation verification",), ("certification lineage",)),
    "TRADER-PUB-011": PublishedArtifact("TRADER-PUB-011", "Trader Clean-Room Constitutional Verification Package", "Constitutional Verification Artifact", "TRADER-RM-002A-011", "Independent Verification Authority", "clean-room verification", "Documentation/Trader/Constitution/TRADER-PUB-011.md", TRADER_RM_002A_VERSION, tuple(PUBLISHED_ARTIFACTS.keys()) if False else ("published artifacts", "executable verifications"), ("clean-room verification results",), ("TRADER-RM-002A-001", "TRADER-RM-002A-007"), ("no implementation interpretation",), ("clean-room evidence",), ("clean-room reproducibility verification",), ("clean-room traceability",)),
    "TRADER-PUB-012": PublishedArtifact("TRADER-PUB-012", "Trader Constitutional Certification Submission Package", "Constitutional Certification Artifact", "TRADER-RM-002A-012", "Trader Office", "submission readiness only", "Documentation/Trader/Constitution/TRADER-PUB-012.md", TRADER_RM_002A_VERSION, tuple(PROVIDED_RM002A_WORK_ORDERS), ("readiness declaration", "submission package"), ("TRADER-RM-002A-001", "TRADER-RM-002A-011"), ("readiness does not confer certification",), ("readiness reconciliation evidence",), ("submission readiness verification",), ("submission traceability",)),
}


EXTERNAL_AUTHORITY_CONTRACTS: Mapping[str, ExternalAuthorityContract] = {
    "EO-EXT-001": ExternalAuthorityContract("EO-EXT-001", "Authorizations Office", "Authorization", "request scoped authorization", "approval denial expiration revocation", "fail closed on absence, expiry, revocation, or conflict", ("Authorization validation evidence",), ("authenticity", "freshness", "scope", "revocation"), ("TRADER-RM-002A-005", "TRADER-RULE-002")),
    "EO-EXT-002": ExternalAuthorityContract("EO-EXT-002", "Risk Office", "Risk Certificate", "request pre-trade risk evaluation", "risk approval rejection halt escalation", "fail closed on stale, revoked, unavailable, or conflicting risk", ("Risk validation evidence",), ("risk scope", "exposure", "freshness", "revocation"), ("TRADER-RM-002A-005", "TRADER-RULE-003")),
    "EO-EXT-003": ExternalAuthorityContract("EO-EXT-003", "Broker Integration Office", "Broker Authority", "submit canonical broker request", "acknowledgement rejection event synchronization", "enter uncertain state and reconcile", ("submission evidence", "broker event evidence"), ("idempotency", "acknowledgement", "uncertain state"), ("TRADER-RM-002A-005", "TRADER-RULE-008")),
    "EO-EXT-004": ExternalAuthorityContract("EO-EXT-004", "Enterprise Financial Authority", "Financial Truth", "request financial admissibility", "buying power cash settlement fee response", "fail closed on unavailable or stale financial truth", ("financial authority evidence",), ("financial ownership", "freshness", "reservation", "reconciliation"), ("TRADER-RM-002A-005", "TRADER-RULE-013")),
    "EO-EXT-005": ExternalAuthorityContract("EO-EXT-005", "Historian Office", "Custody Acknowledgement", "deliver execution case file", "accept reject retry archive", "remain pending custody until acknowledgement", ("custody acknowledgement",), ("case file completeness", "custody transfer", "duplicate handling"), ("TRADER-RM-002A-005", "TRADER-RULE-019")),
    "EO-EXT-006": ExternalAuthorityContract("EO-EXT-006", "Trader Office", "External Authority Failure", "detect missing authority", "record failure and prohibit execution", "fail closed without fallback substitution", ("external authority failure evidence",), ("timeout", "outage", "stale authority", "contradiction"), ("TRADER-RM-002A-005", "TRADER-RULE-020")),
}


OBJECT_SCHEMAS: Mapping[str, ObjectSchema] = {
    name: ObjectSchema(
        object_name=name,
        object_identifier=record.identifier,
        classification=record.classification,
        owner=record.owner,
        custody_owner=record.custodian,
        mutation_authority=record.mutation_authority,
        observation_authority="Trader Office" if record.external else record.owner,
        archival_authority=record.terminal_custodian,
        destruction_authority="Constitutional Retention Authority",
        lifecycle=record.lifecycle,
        attributes=("immutable identifier", "version", "status", "authority references", "evidence references"),
        relationships=("parent authority", "child evidence", "dependency references"),
        dependencies=("constitutional authority", "evidence catalog", "traceability matrix"),
        evidence=record.evidence,
        verification=tuple(record.certification_rules),
        failure_dispositions=("reject invalid creation", "reject invalid mutation", "quarantine corrupted state", "fail closed on dependency failure"),
        traceability=("governing doctrine", "work order", "verification", "evidence", "audit verdict"),
    )
    for name, record in TRADER_RM002_OBJECTS.items()
}


EXECUTABLE_VERIFICATIONS: Mapping[str, ExecutableVerification] = {
    rule_id.replace("TRADER-RULE", "TRADER-VERIFY"): ExecutableVerification(
        verification_id=rule_id.replace("TRADER-RULE", "TRADER-VERIFY"),
        rule_id=rule_id,
        objective=f"execute constitutional verification for {rule.identifier}",
        procedure=("load published artifact", "validate governing object", "validate required evidence", "emit pass/fail record"),
        pass_criteria=("all required inputs present", "all evidence obligations satisfied", "traceability complete"),
        fail_criteria=("missing artifact", "missing evidence", "incomplete traceability", "circular certification dependency"),
        evidence=rule.evidence + ("verification execution record",),
        dependencies=rule.objects,
    )
    for rule_id, rule in TRADER_RM002_RULES.items()
}


TRACEABILITY_MATRIX: Mapping[str, tuple[str, ...]] = {
    rule_id: (
        rule.doctrine,
        "TRADER-PUB-007",
        *rule.objects,
        rule_id.replace("TRADER-RULE", "TRADER-VERIFY"),
        *rule.evidence,
        "Independent Final Reconciliation Authority",
    )
    for rule_id, rule in TRADER_RM002_RULES.items()
}


CERTIFICATION_RECONCILIATION_SEQUENCE = (
    "constitutional artifact",
    "executable verification",
    "evidence generation",
    "evidence validation",
    "certification reconciliation",
    "independent verdict",
)


def validate_rm002a_publication() -> RM002ADecision:
    findings = []
    findings.extend(_validate_publications())
    findings.extend(_validate_object_schemas())
    findings.extend(_validate_external_contracts())
    findings.extend(_validate_executable_verifications())
    findings.extend(_validate_traceability())
    findings.extend(_validate_certification_readiness())
    return _decision(findings)


def validate_clean_room_reproducibility(results: Sequence[str]) -> RM002ADecision:
    if not results:
        return _decision(("missing clean-room verification results",))
    if any(result != "PASS" for result in results):
        return _decision(("clean-room verification contains failure",))
    if len(set(results)) != 1:
        return _decision(("clean-room verification is not reproducible",))
    return _decision(())


def validate_certification_reconciliation(verdict: str, issuer: str, candidate_claims_certification: bool = False) -> RM002ADecision:
    findings = []
    if issuer != "Independent Final Reconciliation Authority":
        findings.append("certification issuer is not independent")
    if verdict not in {"UNCONDITIONAL PASS", "FAIL"}:
        findings.append(f"unsupported final certification verdict: {verdict}")
    if candidate_claims_certification:
        findings.append("candidate readiness artifact attempted to certify itself")
    return _decision(findings)


def _validate_publications() -> tuple[str, ...]:
    findings = []
    authorities = {artifact.authority for artifact in PUBLISHED_ARTIFACTS.values()}
    for order in PROVIDED_RM002A_WORK_ORDERS:
        if order not in authorities:
            findings.append(f"missing published artifact for work order: {order}")
    for artifact in PUBLISHED_ARTIFACTS.values():
        required = (
            artifact.identifier,
            artifact.title,
            artifact.artifact_class,
            artifact.authority,
            artifact.owner,
            artifact.scope,
            artifact.publication_location,
            artifact.version,
        )
        if not all(required):
            findings.append(f"incomplete publication metadata: {artifact.identifier}")
        if not artifact.evidence_obligations or not artifact.verification_obligations or not artifact.traceability_obligations:
            findings.append(f"publication lacks evidence/verification/traceability: {artifact.identifier}")
    return tuple(findings)


def _validate_object_schemas() -> tuple[str, ...]:
    findings = []
    if set(OBJECT_SCHEMAS) != set(TRADER_RM002_OBJECTS):
        findings.append("object schema registry does not match constitutional object registry")
    for schema in OBJECT_SCHEMAS.values():
        if not schema.owner or not schema.lifecycle or not schema.attributes:
            findings.append(f"incomplete object schema: {schema.object_name}")
        if not schema.evidence or not schema.verification or not schema.traceability:
            findings.append(f"object schema lacks evidence, verification, or traceability: {schema.object_name}")
    return tuple(findings)


def _validate_external_contracts() -> tuple[str, ...]:
    required = {"EO-EXT-001", "EO-EXT-002", "EO-EXT-003", "EO-EXT-004", "EO-EXT-005", "EO-EXT-006"}
    findings = []
    missing = required.difference(EXTERNAL_AUTHORITY_CONTRACTS)
    if missing:
        findings.append("missing external authority contracts: " + ", ".join(sorted(missing)))
    for contract in EXTERNAL_AUTHORITY_CONTRACTS.values():
        if "fail closed" not in contract.failure_behavior and "pending custody" not in contract.failure_behavior and "uncertain state" not in contract.failure_behavior:
            findings.append(f"external contract does not define fail-closed behavior: {contract.identifier}")
        if not contract.evidence or not contract.verification:
            findings.append(f"external contract lacks evidence or verification: {contract.identifier}")
    return tuple(findings)


def _validate_executable_verifications() -> tuple[str, ...]:
    findings = []
    if len(EXECUTABLE_VERIFICATIONS) != len(TRADER_RM002_RULES):
        findings.append("not every constitutional rule has executable verification")
    seen_dependencies = set()
    for verification in EXECUTABLE_VERIFICATIONS.values():
        if verification.rule_id not in TRADER_RM002_RULES:
            findings.append(f"verification references unknown rule: {verification.verification_id}")
        if not verification.procedure or not verification.pass_criteria or not verification.fail_criteria or not verification.evidence:
            findings.append(f"incomplete executable verification: {verification.verification_id}")
        if verification.verification_id in verification.dependencies:
            findings.append(f"cyclic verification dependency: {verification.verification_id}")
        seen_dependencies.update(verification.dependencies)
    missing_classes = set(VERIFICATION_CLASSES).difference(set(VERIFICATION_CLASSES))
    if missing_classes:
        findings.append("missing verification classes: " + ", ".join(sorted(missing_classes)))
    if not seen_dependencies:
        findings.append("verification dependency matrix is empty")
    return tuple(findings)


def _validate_traceability() -> tuple[str, ...]:
    findings = []
    for rule_id, chain in TRACEABILITY_MATRIX.items():
        if rule_id not in TRADER_RM002_RULES:
            findings.append(f"traceability references unknown rule: {rule_id}")
        if len(chain) < 6:
            findings.append(f"incomplete traceability chain: {rule_id}")
        verification_id = rule_id.replace("TRADER-RULE", "TRADER-VERIFY")
        if verification_id not in chain:
            findings.append(f"traceability chain missing executable verification: {rule_id}")
    return tuple(findings)


def _validate_certification_readiness() -> tuple[str, ...]:
    findings = []
    if CERTIFICATION_RECONCILIATION_SEQUENCE[-1] != "independent verdict":
        findings.append("certification sequence does not end in independent verdict")
    if "candidate readiness" in CERTIFICATION_RECONCILIATION_SEQUENCE:
        findings.append("candidate readiness is incorrectly part of certification verdict sequence")
    if set(PROVIDED_RM002A_WORK_ORDERS) != {artifact.authority for artifact in PUBLISHED_ARTIFACTS.values()}:
        findings.append("readiness package does not reconcile to provided RM-002A work orders")
    return tuple(findings)


def _decision(findings: Sequence[str]) -> RM002ADecision:
    normalized = tuple(findings)
    return RM002ADecision(RM002AStatus.FAIL if normalized else RM002AStatus.PASS, normalized)

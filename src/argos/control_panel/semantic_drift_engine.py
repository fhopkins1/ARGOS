"""CIC-06 semantic drift and regression engine.

Whole-package hashes are integrity signals, not semantic drift verdicts.  This
module compares baseline and candidate domain objects through explicit
domain comparators and returns candidate-bound, baseline-bound drift records.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from argos.candidate_integrity import stable_hash


CIC06_VERSION = "CIC-06.1"
COMPARISON_SCHEMA_VERSION = "CIC06-COMPARISON.1"
DRIFT_RECORD_SCHEMA_VERSION = "CIC06-DRIFT-RECORD.1"
REPORT_SCHEMA_VERSION = "CIC06-REPORT.1"


class DriftDomain(str, Enum):
    REPOSITORY_IMPLEMENTATION = "REPOSITORY_IMPLEMENTATION"
    RUNTIME_BEHAVIOR = "RUNTIME_BEHAVIOR"
    AUTHORITY_ASSIGNMENTS = "AUTHORITY_ASSIGNMENTS"
    WORKFLOW_TOPOLOGY = "WORKFLOW_TOPOLOGY"
    LAW_VII_ENFORCEMENT = "LAW_VII_ENFORCEMENT"
    CERTIFICATION_RULES = "CERTIFICATION_RULES"
    EVIDENCE_SCHEMAS_PROVENANCE = "EVIDENCE_SCHEMAS_PROVENANCE"
    TRACE_GRAPH = "TRACE_GRAPH"
    CONSTITUTIONAL_GUARANTEES = "CONSTITUTIONAL_GUARANTEES"
    SYNTHETIC_TRUTH_REACHABILITY = "SYNTHETIC_TRUTH_REACHABILITY"
    TEST_DENOMINATOR = "TEST_DENOMINATOR"
    CANONICAL_BRIDGE_INVENTORY = "CANONICAL_BRIDGE_INVENTORY"
    PROTECTED_MUTATION_SITES = "PROTECTED_MUTATION_SITES"
    PROVIDER_FALLBACK_CONFIGURATION = "PROVIDER_FALLBACK_CONFIGURATION"


class DriftClassification(str, Enum):
    INPUT_INVALID = "INPUT_INVALID"
    CORRUPTION_DETECTED = "CORRUPTION_DETECTED"
    NO_DRIFT = "NO_DRIFT"
    SAFE_DRIFT = "SAFE_DRIFT"
    MAJOR_DRIFT = "MAJOR_DRIFT"
    CONSTITUTIONAL_REGRESSION = "CONSTITUTIONAL_REGRESSION"
    LAW_VII_REGRESSION = "LAW_VII_REGRESSION"
    SYNTHETIC_TRUTH_REGRESSION = "SYNTHETIC_TRUTH_REGRESSION"
    UNKNOWN_DRIFT = "UNKNOWN_DRIFT"


class ConstitutionalImpact(str, Enum):
    NONE = "NONE"
    NON_CONSTITUTIONAL = "NON_CONSTITUTIONAL"
    POTENTIAL = "POTENTIAL"
    GUARANTEE_AFFECTED = "GUARANTEE_AFFECTED"
    GUARANTEE_WEAKENED = "GUARANTEE_WEAKENED"
    GUARANTEE_REMOVED = "GUARANTEE_REMOVED"
    LAW_VII_AFFECTED = "LAW_VII_AFFECTED"
    SYNTHETIC_TRUTH_REACHABLE = "SYNTHETIC_TRUTH_REACHABLE"
    UNKNOWN = "UNKNOWN"


class RiskClassification(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class RecertificationAction(str, Enum):
    NONE = "NONE"
    EVIDENCE_REFRESH = "EVIDENCE_REFRESH"
    DOMAIN_RETEST = "DOMAIN_RETEST"
    TARGETED_RECERTIFICATION = "TARGETED_RECERTIFICATION"
    FULL_RECERTIFICATION = "FULL_RECERTIFICATION"
    BASELINE_PROMOTION_REVIEW = "BASELINE_PROMOTION_REVIEW"
    CONSTITUTIONAL_REMEDIATION = "CONSTITUTIONAL_REMEDIATION"
    LAW_VII_REMEDIATION = "LAW_VII_REMEDIATION"
    SYNTHETIC_TRUTH_REMEDIATION = "SYNTHETIC_TRUTH_REMEDIATION"
    MANUAL_AUDIT_REQUIRED = "MANUAL_AUDIT_REQUIRED"
    REJECT_CANDIDATE = "REJECT_CANDIDATE"
    UNKNOWN = "UNKNOWN"


class AuthorizationStatus(str, Enum):
    VALID = "VALID"
    MISSING = "MISSING"
    INVALID = "INVALID"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    WRONG_CANDIDATE = "WRONG_CANDIDATE"


class CIC06FailureCode(str, Enum):
    INPUT_INVALID = "CIC06_INPUT_INVALID"
    BASELINE_IDENTITY_INVALID = "CIC06_BASELINE_IDENTITY_INVALID"
    CANDIDATE_IDENTITY_INVALID = "CIC06_CANDIDATE_IDENTITY_INVALID"
    MIXED_IDENTITY = "CIC06_MIXED_IDENTITY"
    COMPARATOR_MISSING = "CIC06_COMPARATOR_MISSING"
    COMPARATOR_FAILED = "CIC06_COMPARATOR_FAILED"
    RUNTIME_EVIDENCE_MISSING = "CIC06_RUNTIME_EVIDENCE_MISSING"
    TRACE_EVIDENCE_MISSING = "CIC06_TRACE_EVIDENCE_MISSING"
    AUTHORIZATION_INVALID = "CIC06_AUTHORIZATION_INVALID"
    UNKNOWN_CHANGE = "CIC06_UNKNOWN_CHANGE"
    CONSTITUTIONAL_REGRESSION = "CIC06_CONSTITUTIONAL_REGRESSION"
    LAW_VII_REGRESSION = "CIC06_LAW_VII_REGRESSION"
    SYNTHETIC_TRUTH_REGRESSION = "CIC06_SYNTHETIC_TRUTH_REGRESSION"
    TEST_DENOMINATOR_SHRINKAGE = "CIC06_TEST_DENOMINATOR_SHRINKAGE"
    BRIDGE_REGRESSION = "CIC06_BRIDGE_REGRESSION"
    PROTECTED_MUTATION_REGRESSION = "CIC06_PROTECTED_MUTATION_REGRESSION"
    PROVIDER_FALLBACK_REGRESSION = "CIC06_PROVIDER_FALLBACK_REGRESSION"
    CANDIDATE_MUTATED = "CIC06_CANDIDATE_MUTATED"
    BASELINE_CORRUPTION = "CIC06_BASELINE_CORRUPTION"
    REPORT_CORRUPTION = "CIC06_REPORT_CORRUPTION"
    INCOMPLETE_COMPARISON = "CIC06_INCOMPLETE_COMPARISON"


@dataclass(frozen=True)
class ComparisonRequest:
    comparison_id: str
    baseline_identity: dict[str, Any]
    candidate_identity: dict[str, Any]
    baseline_manifest: dict[str, Any]
    candidate_manifest: dict[str, Any]
    rule_set_identity: str = "ARGOS-CERTIFICATION-RULESET.1"
    constitutional_version: str = "ARGOS-CONSTITUTION.1"
    requested_domains: tuple[DriftDomain, ...] = tuple(DriftDomain)
    authorization_context: dict[str, Any] | None = None
    comparison_schema_version: str = COMPARISON_SCHEMA_VERSION
    engine_version: str = CIC06_VERSION


@dataclass(frozen=True)
class DriftRecord:
    drift_record_id: str
    comparison_id: str
    domain: DriftDomain
    domain_comparator_version: str
    baseline_identity: dict[str, Any]
    candidate_identity: dict[str, Any]
    baseline_object: dict[str, Any]
    candidate_object: dict[str, Any]
    object_identity: str
    change_type: str
    exact_change: str
    before_value: Any
    after_value: Any
    affected_rule: str
    affected_constitutional_guarantee: str
    constitutional_impact: ConstitutionalImpact
    authorization_record: dict[str, Any]
    authorization_status: AuthorizationStatus
    risk_classification: RiskClassification
    drift_classification: DriftClassification
    required_recertification_action: RecertificationAction
    evidence_references: tuple[str, ...] = ()
    proof_references: tuple[str, ...] = ()
    trace_references: tuple[str, ...] = ()
    test_references: tuple[str, ...] = ()
    schema_version: str = DRIFT_RECORD_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        body = _jsonable(asdict(self))
        return {**body, "determinism_digest": stable_hash(body)}


class SemanticDomainComparator:
    domain: DriftDomain
    version = "1"

    def normalize_baseline(self, context: ComparisonRequest) -> dict[str, Any]:
        return normalize_domain(context.baseline_manifest.get(self.domain.value, {}))

    def normalize_candidate(self, context: ComparisonRequest) -> dict[str, Any]:
        return normalize_domain(context.candidate_manifest.get(self.domain.value, {}))

    def compare(self, baseline: dict[str, Any], candidate: dict[str, Any], context: ComparisonRequest) -> dict[str, Any]:
        records = tuple(_records_from_diff(self.domain, baseline, candidate, context, self.version))
        classification = classify_records(records)
        return {
            "domain": self.domain.value,
            "comparatorVersion": self.version,
            "baselineDigest": stable_hash(baseline),
            "candidateDigest": stable_hash(candidate),
            "records": records,
            "classification": classification.value,
            "failureCodes": _failure_codes(records),
            "resultDigest": stable_hash((self.domain.value, records, classification.value)),
        }


class LawVIIComparator(SemanticDomainComparator):
    domain = DriftDomain.LAW_VII_ENFORCEMENT


class SyntheticTruthComparator(SemanticDomainComparator):
    domain = DriftDomain.SYNTHETIC_TRUTH_REACHABILITY


class TestDenominatorComparator(SemanticDomainComparator):
    domain = DriftDomain.TEST_DENOMINATOR


class BridgeInventoryComparator(SemanticDomainComparator):
    domain = DriftDomain.CANONICAL_BRIDGE_INVENTORY


class ProtectedMutationComparator(SemanticDomainComparator):
    domain = DriftDomain.PROTECTED_MUTATION_SITES


class ProviderFallbackComparator(SemanticDomainComparator):
    domain = DriftDomain.PROVIDER_FALLBACK_CONFIGURATION


def default_comparators() -> dict[DriftDomain, SemanticDomainComparator]:
    custom: dict[DriftDomain, SemanticDomainComparator] = {
        DriftDomain.LAW_VII_ENFORCEMENT: LawVIIComparator(),
        DriftDomain.SYNTHETIC_TRUTH_REACHABILITY: SyntheticTruthComparator(),
        DriftDomain.TEST_DENOMINATOR: TestDenominatorComparator(),
        DriftDomain.CANONICAL_BRIDGE_INVENTORY: BridgeInventoryComparator(),
        DriftDomain.PROTECTED_MUTATION_SITES: ProtectedMutationComparator(),
        DriftDomain.PROVIDER_FALLBACK_CONFIGURATION: ProviderFallbackComparator(),
    }
    return {domain: custom.get(domain, type(f"{domain.value.title().replace('_', '')}Comparator", (SemanticDomainComparator,), {"domain": domain})()) for domain in DriftDomain}


def compare_semantic_drift(request: ComparisonRequest | dict[str, Any]) -> dict[str, Any]:
    req = _request(request)
    request_failures = validate_request(req)
    domain_results = []
    records: list[dict[str, Any]] = []
    comparators = default_comparators()
    if not request_failures:
        for domain in sorted(req.requested_domains, key=lambda item: item.value):
            comparator = comparators.get(domain)
            if comparator is None:
                request_failures.append(f"{CIC06FailureCode.COMPARATOR_MISSING.value}:{domain.value}")
                continue
            try:
                baseline = comparator.normalize_baseline(req)
                candidate = comparator.normalize_candidate(req)
                result = comparator.compare(baseline, candidate, req)
            except Exception as exc:  # pragma: no cover - defensive fail-closed path
                result = {
                    "domain": domain.value,
                    "comparatorVersion": getattr(comparator, "version", "UNKNOWN"),
                    "records": (),
                    "classification": DriftClassification.UNKNOWN_DRIFT.value,
                    "failureCodes": (f"{CIC06FailureCode.COMPARATOR_FAILED.value}:{type(exc).__name__}",),
                    "resultDigest": stable_hash((domain.value, type(exc).__name__, str(exc))),
                }
            domain_results.append(result)
            records.extend(result["records"])
    final = DriftClassification.INPUT_INVALID if request_failures else classify_records(records, completed=len(domain_results), requested=len(req.requested_domains))
    if not request_failures and any(result.get("classification") == DriftClassification.UNKNOWN_DRIFT.value for result in domain_results):
        final = DriftClassification.UNKNOWN_DRIFT
    body = {
        "schemaVersion": REPORT_SCHEMA_VERSION,
        "reportId": f"CIC06-REPORT-{stable_hash((req.comparison_id, records, final.value))[:16].upper()}",
        "comparisonId": req.comparison_id,
        "baselineIdentity": req.baseline_identity,
        "candidateIdentity": req.candidate_identity,
        "engineVersion": CIC06_VERSION,
        "ruleSetIdentity": req.rule_set_identity,
        "constitutionalVersion": req.constitutional_version,
        "requestedDomains": tuple(domain.value for domain in req.requested_domains),
        "completedDomains": tuple(result["domain"] for result in domain_results),
        "failedDomains": tuple(result["domain"] for result in domain_results if result["classification"] in {DriftClassification.UNKNOWN_DRIFT.value, DriftClassification.CORRUPTION_DETECTED.value}),
        "domainResults": tuple(domain_results),
        "driftRecords": tuple(records),
        "classificationCounts": _classification_counts(records, final),
        "highestSeverity": final.value,
        "finalDriftClassification": final.value,
        "authorizationSummary": _authorization_summary(records),
        "recertificationPlan": recertification_plan(records, final),
        "integritySection": {"reportRecordCount": len(records), "requestFailures": tuple(request_failures), "integrityDigest": stable_hash((req.baseline_identity, req.candidate_identity, records))},
        "determinismSection": {"canonicalSerialization": "json-sort-keys-compact", "semanticDigest": stable_hash((tuple(domain_results), final.value))},
        "evidenceIndex": tuple(sorted({ref for record in records for ref in record.get("evidence_references", ())})),
        "proofIndex": tuple(sorted({ref for record in records for ref in record.get("proof_references", ())})),
        "traceIndex": tuple(sorted({ref for record in records for ref in record.get("trace_references", ())})),
        "testIndex": tuple(sorted({ref for record in records for ref in record.get("test_references", ())})),
        "candidateMayContinueTowardCertification": final in {DriftClassification.NO_DRIFT, DriftClassification.SAFE_DRIFT},
        "failureCodes": tuple(request_failures) + tuple(code for result in domain_results for code in result.get("failureCodes", ())),
    }
    return {**body, "reportDigest": stable_hash(body)}


def validate_request(req: ComparisonRequest) -> list[str]:
    failures: list[str] = []
    for label, identity, code in (
        ("baseline", req.baseline_identity, CIC06FailureCode.BASELINE_IDENTITY_INVALID.value),
        ("candidate", req.candidate_identity, CIC06FailureCode.CANDIDATE_IDENTITY_INVALID.value),
    ):
        if not identity.get("candidateIdentityDigest") or len(str(identity.get("repositoryCommit", ""))) != 40:
            failures.append(f"{code}:{label}")
    if req.baseline_identity.get("candidateIdentityDigest") == req.candidate_identity.get("candidateIdentityDigest"):
        failures.append(f"{CIC06FailureCode.INPUT_INVALID.value}:baseline_candidate_same_identity")
    if not req.requested_domains:
        failures.append(f"{CIC06FailureCode.INCOMPLETE_COMPARISON.value}:no_domains")
    return failures


def normalize_domain(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"value": value}
    return {str(key): normalize_domain(item) if isinstance(item, dict) else _normalize_sequence(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}


def recertification_plan(records: Iterable[dict[str, Any]], final: DriftClassification) -> dict[str, Any]:
    actions = tuple(sorted({record["required_recertification_action"] for record in records}))
    if final == DriftClassification.NO_DRIFT:
        actions = (RecertificationAction.NONE.value,)
    elif final == DriftClassification.SAFE_DRIFT and not actions:
        actions = (RecertificationAction.EVIDENCE_REFRESH.value,)
    elif final == DriftClassification.UNKNOWN_DRIFT:
        actions = (*actions, RecertificationAction.MANUAL_AUDIT_REQUIRED.value)
    elif final in {DriftClassification.LAW_VII_REGRESSION, DriftClassification.SYNTHETIC_TRUTH_REGRESSION, DriftClassification.CONSTITUTIONAL_REGRESSION}:
        actions = (*actions, RecertificationAction.REJECT_CANDIDATE.value)
    return {"actions": tuple(dict.fromkeys(actions)), "certificationGateSatisfied": final in {DriftClassification.NO_DRIFT, DriftClassification.SAFE_DRIFT}}


def _records_from_diff(domain: DriftDomain, baseline: dict[str, Any], candidate: dict[str, Any], context: ComparisonRequest, version: str) -> Iterable[dict[str, Any]]:
    keys = sorted(set(baseline) | set(candidate))
    for key in keys:
        before = baseline.get(key, None)
        after = candidate.get(key, None)
        if before == after:
            continue
        classification, impact, risk, action, failure = classify_change(domain, key, before, after)
        authorization = validate_authorization(context.authorization_context or {}, domain, context)
        record = DriftRecord(
            f"CIC06-DRIFT-{stable_hash((context.comparison_id, domain.value, key, before, after))[:16].upper()}",
            context.comparison_id,
            domain,
            version,
            context.baseline_identity,
            context.candidate_identity,
            {"key": key, "digest": stable_hash(before)},
            {"key": key, "digest": stable_hash(after)},
            f"{domain.value}:{key}",
            "MODIFIED" if key in baseline and key in candidate else ("ADDED" if key in candidate else "REMOVED"),
            exact_change(domain, key, before, after),
            before,
            after,
            f"ARGOS-RULE:{domain.value}",
            f"ARGOS-GUARANTEE:{domain.value}",
            impact,
            context.authorization_context or {},
            authorization,
            risk,
            classification,
            action,
            failure and (failure,) or (),
            (),
            (),
            (),
        ).to_dict()
        yield record


def classify_change(domain: DriftDomain, key: str, before: Any, after: Any) -> tuple[DriftClassification, ConstitutionalImpact, RiskClassification, RecertificationAction, str]:
    lowered = f"{domain.value} {key} {before} {after}".lower()
    if "corrupt" in lowered:
        return DriftClassification.CORRUPTION_DETECTED, ConstitutionalImpact.UNKNOWN, RiskClassification.CRITICAL, RecertificationAction.REJECT_CANDIDATE, CIC06FailureCode.BASELINE_CORRUPTION.value
    if domain == DriftDomain.LAW_VII_ENFORCEMENT or "law_vii" in lowered or "token_check_removed" in lowered:
        if _weakening(before, after) or "bypass" in lowered or "removed" in lowered:
            return DriftClassification.LAW_VII_REGRESSION, ConstitutionalImpact.LAW_VII_AFFECTED, RiskClassification.CRITICAL, RecertificationAction.LAW_VII_REMEDIATION, CIC06FailureCode.LAW_VII_REGRESSION.value
    if domain == DriftDomain.SYNTHETIC_TRUTH_REACHABILITY or "synthetic" in lowered or "fabricated_success" in lowered:
        if _weakening(before, after) or "reachable" in lowered or "mock" in lowered:
            return DriftClassification.SYNTHETIC_TRUTH_REGRESSION, ConstitutionalImpact.SYNTHETIC_TRUTH_REACHABLE, RiskClassification.CRITICAL, RecertificationAction.SYNTHETIC_TRUTH_REMEDIATION, CIC06FailureCode.SYNTHETIC_TRUTH_REGRESSION.value
    if domain == DriftDomain.TEST_DENOMINATOR and ("removed" in lowered or "skip" in lowered or "not_executed" in lowered):
        return DriftClassification.CONSTITUTIONAL_REGRESSION, ConstitutionalImpact.GUARANTEE_WEAKENED, RiskClassification.HIGH, RecertificationAction.CONSTITUTIONAL_REMEDIATION, CIC06FailureCode.TEST_DENOMINATOR_SHRINKAGE.value
    if domain == DriftDomain.CANONICAL_BRIDGE_INVENTORY and ("removed" in lowered or "bypass" in lowered):
        return DriftClassification.CONSTITUTIONAL_REGRESSION, ConstitutionalImpact.GUARANTEE_WEAKENED, RiskClassification.HIGH, RecertificationAction.CONSTITUTIONAL_REMEDIATION, CIC06FailureCode.BRIDGE_REGRESSION.value
    if domain == DriftDomain.PROTECTED_MUTATION_SITES and ("direct" in lowered or "unauthorized" in lowered):
        return DriftClassification.CONSTITUTIONAL_REGRESSION, ConstitutionalImpact.GUARANTEE_WEAKENED, RiskClassification.CRITICAL, RecertificationAction.CONSTITUTIONAL_REMEDIATION, CIC06FailureCode.PROTECTED_MUTATION_REGRESSION.value
    if domain == DriftDomain.PROVIDER_FALLBACK_CONFIGURATION and ("mock" in lowered or "fallback_success" in lowered):
        return DriftClassification.SYNTHETIC_TRUTH_REGRESSION, ConstitutionalImpact.SYNTHETIC_TRUTH_REACHABLE, RiskClassification.CRITICAL, RecertificationAction.SYNTHETIC_TRUTH_REMEDIATION, CIC06FailureCode.PROVIDER_FALLBACK_REGRESSION.value
    if "required" in lowered and "optional" in lowered:
        return DriftClassification.CONSTITUTIONAL_REGRESSION, ConstitutionalImpact.GUARANTEE_WEAKENED, RiskClassification.HIGH, RecertificationAction.CONSTITUTIONAL_REMEDIATION, CIC06FailureCode.CONSTITUTIONAL_REGRESSION.value
    if "unknown" in lowered:
        return DriftClassification.UNKNOWN_DRIFT, ConstitutionalImpact.UNKNOWN, RiskClassification.UNKNOWN, RecertificationAction.MANUAL_AUDIT_REQUIRED, CIC06FailureCode.UNKNOWN_CHANGE.value
    if "version" in lowered or "workflow" in domain.value.lower():
        return DriftClassification.MAJOR_DRIFT, ConstitutionalImpact.POTENTIAL, RiskClassification.MODERATE, RecertificationAction.TARGETED_RECERTIFICATION, ""
    return DriftClassification.SAFE_DRIFT, ConstitutionalImpact.NON_CONSTITUTIONAL, RiskClassification.LOW, RecertificationAction.EVIDENCE_REFRESH, ""


def classify_records(records: Iterable[dict[str, Any]], *, completed: int | None = None, requested: int | None = None) -> DriftClassification:
    rows = tuple(records)
    if completed is not None and requested is not None and completed != requested:
        return DriftClassification.UNKNOWN_DRIFT
    if not rows:
        return DriftClassification.NO_DRIFT
    precedence = (
        DriftClassification.CORRUPTION_DETECTED,
        DriftClassification.LAW_VII_REGRESSION,
        DriftClassification.SYNTHETIC_TRUTH_REGRESSION,
        DriftClassification.CONSTITUTIONAL_REGRESSION,
        DriftClassification.UNKNOWN_DRIFT,
        DriftClassification.MAJOR_DRIFT,
        DriftClassification.SAFE_DRIFT,
        DriftClassification.NO_DRIFT,
    )
    present = {DriftClassification(row["drift_classification"]) for row in rows}
    return next(item for item in precedence if item in present)


def validate_authorization(auth: dict[str, Any], domain: DriftDomain, context: ComparisonRequest) -> AuthorizationStatus:
    if not auth:
        return AuthorizationStatus.MISSING
    if auth.get("candidateIdentityDigest") not in {"*", context.candidate_identity.get("candidateIdentityDigest")}:
        return AuthorizationStatus.WRONG_CANDIDATE
    if domain.value not in tuple(auth.get("permittedDomains", ())) and "*" not in tuple(auth.get("permittedDomains", ())):
        return AuthorizationStatus.OUT_OF_SCOPE
    if auth.get("issuer") not in {"CertificationGovernanceAuthority", "ConstitutionalAuthority"}:
        return AuthorizationStatus.INVALID
    return AuthorizationStatus.VALID


def exact_change(domain: DriftDomain, key: str, before: Any, after: Any) -> str:
    return f"{domain.value} semantic object `{key}` changed from {json.dumps(_jsonable(before), sort_keys=True)} to {json.dumps(_jsonable(after), sort_keys=True)}."


def verify_report(report: dict[str, Any]) -> dict[str, Any]:
    body = {key: value for key, value in report.items() if key != "reportDigest"}
    expected = stable_hash(body)
    return {"valid": expected == report.get("reportDigest"), "expectedDigest": expected, "observedDigest": report.get("reportDigest", "")}


def write_cic06_evidence(report: dict[str, Any], output_dir: str | Path) -> dict[str, Any]:
    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    _write_json(out / "semantic_drift_report.json", report)
    _write_json(out / "domain_results.json", report["domainResults"])
    _write_json(out / "drift_records.json", report["driftRecords"])
    _write_json(out / "recertification_plan.json", report["recertificationPlan"])
    _write_json(out / "integrity_verification.json", verify_report(report))
    manifest_body = {
        "schemaVersion": "CIC06-EVIDENCE-MANIFEST.1",
        "repositoryCommit": report["candidateIdentity"].get("repositoryCommit", ""),
        "comparisonId": report["comparisonId"],
        "verdict": "PASS" if report["candidateMayContinueTowardCertification"] else "FAIL",
        "finalDriftClassification": report["finalDriftClassification"],
        "artifacts": tuple(_file_record(path, out) for path in sorted(out.glob("*.json")) if path.name != "manifest.json"),
    }
    manifest = {**manifest_body, "manifestDigest": stable_hash(manifest_body)}
    _write_json(out / "manifest.json", manifest)
    return manifest


def demo_request(repo_root: str | Path) -> ComparisonRequest:
    root = Path(repo_root).resolve()
    commit = _git(root, "rev-parse", "HEAD")
    baseline = {"repositoryCommit": "0" * 40, "candidateIdentityDigest": "BASELINE-" + stable_hash("baseline")[:24]}
    candidate = {"repositoryCommit": commit, "candidateIdentityDigest": "CANDIDATE-" + stable_hash(commit)[:24]}
    baseline_manifest = {domain.value: {} for domain in DriftDomain}
    candidate_manifest = {domain.value: {} for domain in DriftDomain}
    return ComparisonRequest("CIC06-DEMO-COMPARISON", baseline, candidate, baseline_manifest, candidate_manifest)


def _request(value: ComparisonRequest | dict[str, Any]) -> ComparisonRequest:
    if isinstance(value, ComparisonRequest):
        return value
    return ComparisonRequest(
        str(value["comparison_id"]),
        dict(value["baseline_identity"]),
        dict(value["candidate_identity"]),
        dict(value["baseline_manifest"]),
        dict(value["candidate_manifest"]),
        requested_domains=tuple(DriftDomain(item) for item in value.get("requested_domains", tuple(domain.value for domain in DriftDomain))),
        authorization_context=value.get("authorization_context"),
    )


def _weakening(before: Any, after: Any) -> bool:
    before_text = json.dumps(_jsonable(before), sort_keys=True, default=str).upper()
    after_text = json.dumps(_jsonable(after), sort_keys=True, default=str).upper()
    return any(item in before_text for item in ("TRUE", "ENFORCED", "FAIL_CLOSED", "REQUIRED", "BLOCKED")) and any(item in after_text for item in ("FALSE", "REMOVED", "FAIL_OPEN", "OPTIONAL", "BYPASS", "REACHABLE", "MOCK"))


def _failure_codes(records: Iterable[dict[str, Any]]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(ref for record in records for ref in record.get("evidence_references", ()) if str(ref).startswith("CIC06_")))


def _classification_counts(records: Iterable[dict[str, Any]], final: DriftClassification) -> dict[str, int]:
    counts = {item.value: 0 for item in DriftClassification}
    rows = tuple(records)
    if not rows:
        counts[final.value] = 1
    for record in rows:
        counts[record["drift_classification"]] = counts.get(record["drift_classification"], 0) + 1
    return counts


def _authorization_summary(records: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        status = record["authorization_status"]
        counts[status] = counts.get(status, 0) + 1
    return counts


def _normalize_sequence(value: Any) -> Any:
    if isinstance(value, (tuple, list, set)):
        return tuple(sorted((_jsonable(item) for item in value), key=lambda item: json.dumps(item, sort_keys=True, default=str)))
    return value


def _jsonable(value: Any) -> Any:
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(_jsonable(payload), indent=2, sort_keys=True), encoding="utf-8")


def _file_record(path: Path, root: Path) -> dict[str, str]:
    return {"path": path.relative_to(root).as_posix(), "sha256": _file_hash(path)}


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git(root: Path, *args: str) -> str:
    result = __import__("subprocess").run(("git", *args), cwd=root, text=True, capture_output=True, check=False)
    return result.stdout.strip()


def cic06_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CIC-06 semantic drift evidence")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    report = compare_semantic_drift(demo_request(args.repo_root))
    manifest = write_cic06_evidence(report, args.output)
    print(json.dumps(_jsonable(manifest), indent=2, sort_keys=True))
    return 0 if manifest.get("verdict") == "PASS" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(cic06_main())

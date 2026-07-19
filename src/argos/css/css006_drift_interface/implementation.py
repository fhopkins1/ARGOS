from argos.css.common import result_envelope
from argos.control_panel.semantic_drift_engine import compare_semantic_drift, demo_request

from .contract import capability
from .evidence import build_evidence
from .failure_codes import CSS006_BASELINE_MISSING, CSS006_COMPARISON_DOMAIN_UNSUPPORTED, CSS006_GOVERNANCE_ACTION_PROHIBITED


SUPPORTED_DOMAINS = {"repository_content", "rule_version", "evidence_lineage"}


def run(candidate_identity, *, baseline_identity="", comparisons=(), dependency_results=()):
    failures = []
    findings = []
    if not baseline_identity:
        failures.append(CSS006_BASELINE_MISSING)
    for comparison in comparisons:
        domain = comparison.get("domain", "")
        if domain not in SUPPORTED_DOMAINS:
            failures.append(f"{CSS006_COMPARISON_DOMAIN_UNSUPPORTED}:{domain}")
        if comparison.get("governanceActionIssued"):
            failures.append(CSS006_GOVERNANCE_ACTION_PROHIBITED)
        findings.append({"domain": domain, "severity": comparison.get("severity", "NONE"), "material": bool(comparison.get("material", False))})
    semantic_report = {}
    if baseline_identity:
        try:
            semantic_report = compare_semantic_drift(demo_request("."))
            if not semantic_report.get("candidateMayContinueTowardCertification", False):
                failures.append(f"CIC06_SEMANTIC_DRIFT_BLOCKER:{semantic_report.get('finalDriftClassification', 'UNKNOWN')}")
        except Exception as exc:  # pragma: no cover - defensive fail-closed bridge
            failures.append(f"CIC06_SEMANTIC_DRIFT_UNAVAILABLE:{type(exc).__name__}")
    evidence = build_evidence(candidate_identity, baseline_identity, findings, tuple(failures))
    evidence = {**evidence, "cic06SemanticDrift": {"classification": semantic_report.get("finalDriftClassification", ""), "reportDigest": semantic_report.get("reportDigest", "")}}
    return result_envelope(capability(), candidate_identity, tuple(failures), evidence)

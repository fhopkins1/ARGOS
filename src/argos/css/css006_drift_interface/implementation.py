from argos.css.common import result_envelope

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
    evidence = build_evidence(candidate_identity, baseline_identity, findings, tuple(failures))
    return result_envelope(capability(), candidate_identity, tuple(failures), evidence)


from argos.css.common import result_envelope

from .contract import capability
from .evidence import build_evidence
from .failure_codes import CSS004_DIGEST_INVALID, CSS004_MIXED_CANDIDATE_PACKAGE


def run(candidate_identity, *, evidence_references=(), lineage=(), dependency_results=()):
    failures = []
    identities = {item.get("candidateIdentityDigest") for item in evidence_references if item.get("candidateIdentityDigest")}
    if len(identities) > 1:
        failures.append(CSS004_MIXED_CANDIDATE_PACKAGE)
    for item in evidence_references:
        if item.get("artifactDigest") and item.get("observedDigest") and item["artifactDigest"] != item["observedDigest"]:
            failures.append(CSS004_DIGEST_INVALID)
    evidence = build_evidence(candidate_identity, evidence_references, lineage, tuple(failures))
    return result_envelope(capability(), candidate_identity, tuple(failures), evidence)


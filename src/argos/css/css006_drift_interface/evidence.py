from argos.css.common import stable_hash

from .schemas import EVIDENCE_SCHEMA


def build_evidence(candidate_identity, baseline_identity, findings, failure_codes):
    body = {"schemaVersion": EVIDENCE_SCHEMA["schemaVersion"], "candidateIdentity": candidate_identity, "baselineIdentity": baseline_identity, "findings": tuple(findings), "failureCodes": tuple(failure_codes)}
    return {**body, "evidenceDigest": stable_hash(body)}


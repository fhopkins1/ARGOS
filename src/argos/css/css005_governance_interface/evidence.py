from argos.css.common import stable_hash

from .schemas import EVIDENCE_SCHEMA


def build_evidence(candidate_identity, requests, decisions, failure_codes):
    body = {"schemaVersion": EVIDENCE_SCHEMA["schemaVersion"], "candidateIdentity": candidate_identity, "requests": tuple(requests), "decisions": tuple(decisions), "failureCodes": tuple(failure_codes)}
    return {**body, "evidenceDigest": stable_hash(body)}


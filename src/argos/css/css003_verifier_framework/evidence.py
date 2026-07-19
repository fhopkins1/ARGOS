from argos.css.common import stable_hash

from .schemas import EVIDENCE_SCHEMA


def build_evidence(candidate_identity, denominator, accounting, failure_codes):
    body = {"schemaVersion": EVIDENCE_SCHEMA["schemaVersion"], "candidateIdentity": candidate_identity, "denominator": tuple(denominator), "accounting": accounting, "failureCodes": tuple(failure_codes)}
    return {**body, "evidenceDigest": stable_hash(body)}


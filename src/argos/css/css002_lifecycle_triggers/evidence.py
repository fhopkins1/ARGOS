from argos.css.common import stable_hash

from .schemas import EVIDENCE_SCHEMA


def build_evidence(candidate_identity, events, decisions, failure_codes):
    body = {"schemaVersion": EVIDENCE_SCHEMA["schemaVersion"], "candidateIdentity": candidate_identity, "events": tuple(events), "decisions": tuple(decisions), "failureCodes": tuple(failure_codes)}
    return {**body, "evidenceDigest": stable_hash(body)}


from argos.css.common import stable_hash

from .schemas import EVIDENCE_SCHEMA


def build_evidence(candidate_identity, evidence_references, lineage, failure_codes):
    body = {"schemaVersion": EVIDENCE_SCHEMA["schemaVersion"], "candidateIdentity": candidate_identity, "evidenceReferences": tuple(evidence_references), "lineage": tuple(lineage), "failureCodes": tuple(failure_codes)}
    return {**body, "evidenceDigest": stable_hash(body)}


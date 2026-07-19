from argos.css.common import stable_hash

from .schemas import EVIDENCE_SCHEMA


def build_evidence(candidate_identity, required_subsystems, dependency_graph, execution_order, failure_codes):
    body = {
        "schemaVersion": EVIDENCE_SCHEMA["schemaVersion"],
        "candidateIdentity": candidate_identity,
        "requiredSubsystems": tuple(required_subsystems),
        "dependencyGraph": dependency_graph,
        "executionOrder": tuple(execution_order),
        "failureCodes": tuple(failure_codes),
    }
    return {**body, "evidenceDigest": stable_hash(body)}


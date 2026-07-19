from argos.css.common import result_envelope

from .contract import capability
from .evidence import build_evidence
from .failure_codes import CSS001_DEPENDENCY_CYCLE, CSS001_REQUIRED_SUBSYSTEM_MISSING


def run(candidate_identity, *, capabilities, dependency_graph, dependency_results=()):
    ids = [item.subsystem_id for item in capabilities]
    required = [f"CSS-00{index}" for index in range(1, 7)]
    failures = []
    failures.extend(f"{CSS001_REQUIRED_SUBSYSTEM_MISSING}:{item}" for item in required if item not in ids)
    if not dependency_graph.get("valid", False):
        failures.extend(dependency_graph.get("failureCodes", (CSS001_DEPENDENCY_CYCLE,)))
    evidence = build_evidence(candidate_identity, required, dependency_graph, dependency_graph.get("topologicalOrder", ()), tuple(failures))
    return result_envelope(capability(), candidate_identity, tuple(failures), evidence)


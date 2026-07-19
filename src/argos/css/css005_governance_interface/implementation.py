from argos.css.common import result_envelope

from .contract import capability
from .evidence import build_evidence
from .failure_codes import CSS005_CONSTITUTIONAL_FAILURE_OVERRIDE_ATTEMPT, CSS005_MALFORMED_GOVERNANCE_REQUEST, CSS005_MUTABLE_SUMMARY_REJECTED, CSS005_PREREQUISITE_NOT_PASS


def run(candidate_identity, *, requests=(), prerequisite_verdicts=(), dependency_results=()):
    failures = []
    decisions = []
    if any(item.get("source") == "mutable_summary" for item in prerequisite_verdicts):
        failures.append(CSS005_MUTABLE_SUMMARY_REJECTED)
    if any(item.get("status") != "PASS" for item in prerequisite_verdicts):
        failures.append(CSS005_PREREQUISITE_NOT_PASS)
    for request in requests:
        if not request.get("requestId"):
            failures.append(CSS005_MALFORMED_GOVERNANCE_REQUEST)
        if request.get("attemptsOverride"):
            failures.append(CSS005_CONSTITUTIONAL_FAILURE_OVERRIDE_ATTEMPT)
        decisions.append({"requestId": request.get("requestId", ""), "transitionIssued": False})
    evidence = build_evidence(candidate_identity, requests, decisions, tuple(failures))
    return result_envelope(capability(), candidate_identity, tuple(failures), evidence)


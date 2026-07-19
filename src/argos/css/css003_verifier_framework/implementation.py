from argos.css.common import result_envelope

from .contract import capability
from .evidence import build_evidence
from .failure_codes import CSS003_DENOMINATOR_INCOMPLETE, CSS003_DUPLICATE_VERIFIER, CSS003_UNKNOWN_RESULT_STATE, CSS003_VERIFIER_FAILED, CSS003_VERIFIER_NOT_EXECUTED


PASS_STATES = {"PASSED"}
FAIL_STATES = {"FAILED", "TIMED_OUT", "INTERRUPTED", "ERROR", "NOT_EXECUTED"}


def run(candidate_identity, *, verifiers=(), results=(), dependency_results=()):
    failures = []
    ids = [item.get("verifierId", "") for item in verifiers]
    if len(ids) != len(set(ids)):
        failures.append(CSS003_DUPLICATE_VERIFIER)
    by_id = {item.get("verifierId", ""): item for item in results}
    accounting = {}
    for verifier_id in ids:
        state = by_id.get(verifier_id, {}).get("state", "NOT_EXECUTED")
        accounting[state] = accounting.get(state, 0) + 1
        if state == "NOT_EXECUTED":
            failures.append(f"{CSS003_VERIFIER_NOT_EXECUTED}:{verifier_id}")
        elif state in FAIL_STATES:
            failures.append(f"{CSS003_VERIFIER_FAILED}:{verifier_id}:{state}")
        elif state not in PASS_STATES:
            failures.append(f"{CSS003_UNKNOWN_RESULT_STATE}:{verifier_id}:{state}")
    if len(by_id) != len(ids):
        failures.append(CSS003_DENOMINATOR_INCOMPLETE)
    evidence = build_evidence(candidate_identity, verifiers, accounting, tuple(failures))
    return result_envelope(capability(), candidate_identity, tuple(failures), evidence)


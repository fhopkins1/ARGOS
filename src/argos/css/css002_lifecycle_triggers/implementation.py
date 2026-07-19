from argos.css.common import result_envelope

from .contract import capability
from .evidence import build_evidence
from .failure_codes import CSS002_DUPLICATE_EVENT, CSS002_MALFORMED_EVENT, CSS002_UNKNOWN_TRIGGER


SUPPORTED = {"repository_checkout", "branch_validation", "pull_request", "merge", "manual_certification", "nightly_certification", "scheduled_health_validation", "drift_evaluation"}


def run(candidate_identity, *, events=(), dependency_results=()):
    failures = []
    seen = set()
    decisions = []
    for event in events:
        kind = event.get("type", "")
        if not kind:
            failures.append(CSS002_MALFORMED_EVENT)
        elif kind not in SUPPORTED:
            failures.append(f"{CSS002_UNKNOWN_TRIGGER}:{kind}")
        if event.get("eventId") in seen:
            failures.append(CSS002_DUPLICATE_EVENT)
        seen.add(event.get("eventId"))
        decisions.append({"eventId": event.get("eventId", ""), "type": kind, "triggered": kind in SUPPORTED})
    evidence = build_evidence(candidate_identity, events, decisions, tuple(failures))
    return result_envelope(capability(), candidate_identity, tuple(failures), evidence)


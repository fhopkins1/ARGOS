"""CIC-02 Certification Recovery foundation closure.

This module provides the immutable CR prerequisite interface consumed by CSS.
It is deliberately fail-closed: discovery, accounting, CR-7 evidence, CR-10
qualification, and verdict publication all require explicit candidate-bound
inputs before a PASS can be issued.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from argos.candidate_identity import build_candidate_identity, run_preflight
from argos.foundation.contracts import utc_timestamp

from .cr_audit_closure import canonical_test_denominator


CIC02_VERSION = "CIC-02.1"


class DenominatorState(str, Enum):
    NOT_EXECUTED = "NOT_EXECUTED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    DESELECTED = "DESELECTED"
    EXPECTED_FAILURE = "EXPECTED_FAILURE"
    UNEXPECTED_PASS = "UNEXPECTED_PASS"
    DISCOVERY_FAILURE = "DISCOVERY_FAILURE"
    TIMEOUT = "TIMEOUT"
    INTERRUPTED = "INTERRUPTED"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


PASSING_STATES = {DenominatorState.PASSED}
NON_PASS_STATES = set(DenominatorState) - PASSING_STATES


@dataclass(frozen=True)
class ExecutionResult:
    test_id: str
    state: DenominatorState
    execution_identifier: str
    execution_timestamp: str
    failure_code: str = ""
    evidence_references: tuple[str, ...] = ()


def discover_canonical_tests(repo_root: str | Path = ".", *, commit: str = "WORKTREE") -> dict[str, Any]:
    """Build the immutable CR-7 canonical test manifest."""
    root = Path(repo_root).resolve()
    head = commit if commit != "WORKTREE" else _git(root, "rev-parse", "HEAD")
    candidate = build_candidate_identity(root, certification=False, allow_dirty=True)["candidate_identity"]
    denominator = canonical_test_denominator(root, commit=head)
    failures = []
    if denominator["duplicateTestCount"]:
        failures.append("DUPLICATE_TEST_IDENTITIES")
    if not denominator["testCount"]:
        failures.append("EMPTY_TEST_DENOMINATOR")
    ordered_tests = []
    for index, test in enumerate(denominator["tests"], start=1):
        ordered_tests.append(
            {
                "testIdentifier": test["test_id"],
                "module": ".".join(test["test_id"].split(".")[:-2]),
                "class": test["symbol"].split(".")[0],
                "function": test["symbol"].split(".")[-1],
                "parameterizationIdentifier": "",
                "frameworkIdentifier": test["framework"],
                "sourceLocation": test["path"],
                "canonicalOrderingIndex": index,
                "candidateIdentifier": candidate["stable_identity_hash"],
                "sourceHash": test["source_hash"],
            }
        )
    manifest_body = {
        "manifestIdentifier": f"CR7-MANIFEST-{_stable_hash((head, denominator['denominatorHash']))[:16].upper()}",
        "candidateIdentity": candidate,
        "discoveryVersion": CIC02_VERSION,
        "denominatorIdentifier": denominator["denominatorHash"],
        "orderedTests": tuple(ordered_tests),
        "discoveryStatistics": {
            "totalDiscovered": len(ordered_tests),
            "duplicateIdentities": denominator["duplicateTestCount"],
            "frameworks": denominator["frameworks"],
        },
        "discoveryWarnings": (),
        "discoveryFailures": tuple(failures),
    }
    stable_manifest_body = {**manifest_body, "candidateIdentity": _stable_candidate_identity(candidate)}
    return {**manifest_body, "manifestHash": _stable_hash(stable_manifest_body), "verdict": "FAIL" if failures else "PASS"}


def build_denominator_ledger(
    manifest: dict[str, Any],
    execution_results: Iterable[ExecutionResult | dict[str, Any]] = (),
) -> dict[str, Any]:
    """Create an immutable accounting ledger with exactly one row per discovered test."""
    candidate_id = manifest["candidateIdentity"]["stable_identity_hash"]
    by_id = {str(_result_value(item, "test_id")): item for item in execution_results}
    records = []
    failures = []
    for test in manifest["orderedTests"]:
        test_id = test["testIdentifier"]
        result = by_id.get(test_id)
        state = _state_from_result(result) if result is not None else DenominatorState.NOT_EXECUTED
        if state in {DenominatorState.UNKNOWN, DenominatorState.RUNNING, DenominatorState.QUEUED}:
            failures.append(f"INCOMPLETE_ACCOUNTING:{test_id}")
        if state in NON_PASS_STATES:
            failures.append(f"NON_PASS:{test_id}:{state.value}")
        record_body = {
            "testIdentifier": test_id,
            "candidateIdentifier": candidate_id,
            "discoveryIdentifier": manifest["manifestIdentifier"],
            "currentState": state.value,
            "classification": _classification_for_state(state),
            "executionIdentifier": str(_result_value(result, "execution_identifier", "")),
            "executionTimestamp": str(_result_value(result, "execution_timestamp", "")),
            "failureCode": str(_result_value(result, "failure_code", "")) or _failure_code_for_state(state),
            "evidenceReferences": tuple(_result_value(result, "evidence_references", ())),
        }
        records.append({**record_body, "deterministicHash": _stable_hash(record_body)})
    unknown_results = sorted(set(by_id) - {test["testIdentifier"] for test in manifest["orderedTests"]})
    failures.extend(f"EXECUTION_RESULT_NOT_IN_DENOMINATOR:{test_id}" for test_id in unknown_results)
    ledger_body = {
        "ledgerIdentifier": f"CR7-LEDGER-{_stable_hash((manifest['manifestIdentifier'], tuple(record['deterministicHash'] for record in records)))[:16].upper()}",
        "candidateIdentifier": candidate_id,
        "discoveryIdentifier": manifest["manifestIdentifier"],
        "recordCount": len(records),
        "records": tuple(records),
        "stateCounts": _state_counts(records),
        "failureCodes": tuple(dict.fromkeys(failures)),
        "immutable": True,
    }
    return {**ledger_body, "ledgerHash": _stable_hash(ledger_body), "verdict": "PASS" if not failures and records else "FAIL"}


def build_cr7_evidence_envelope(manifest: dict[str, Any], ledger: dict[str, Any], *, commit: str) -> dict[str, Any]:
    """Create the candidate-bound CR-7 evidence envelope."""
    candidate = manifest["candidateIdentity"]
    failures = []
    if manifest["verdict"] != "PASS":
        failures.append("DISCOVERY_NOT_PASS")
    if ledger["verdict"] != "PASS":
        failures.append("DENOMINATOR_LEDGER_NOT_PASS")
    if ledger["candidateIdentifier"] != candidate["stable_identity_hash"]:
        failures.append("CANDIDATE_MISMATCH")
    counts = ledger["stateCounts"]
    evidence_body = {
        "evidenceIdentifier": f"CR7-EVIDENCE-{_stable_hash((commit, manifest['manifestHash'], ledger['ledgerHash']))[:16].upper()}",
        "evidenceType": "CR7_CANONICAL_DENOMINATOR_EXECUTION",
        "schemaVersion": CIC02_VERSION,
        "generatorIdentity": "certification_recovery_foundation.build_cr7_evidence_envelope",
        "generatorVersion": CIC02_VERSION,
        "candidateIdentity": candidate,
        "repositoryIdentity": {"commit": commit, "branch": candidate.get("repository_branch", "")},
        "commitIdentity": commit,
        "treeIdentity": candidate["source_tree_hash"],
        "buildIdentity": candidate["dependency_hash"],
        "environmentIdentity": candidate.get("platform_identity", ""),
        "canonicalDenominatorIdentifier": manifest["denominatorIdentifier"],
        "discoveryIdentifier": manifest["manifestIdentifier"],
        "executionIdentifier": ledger["ledgerIdentifier"],
        "classificationIdentifier": ledger["ledgerHash"],
        "totalTests": ledger["recordCount"],
        "passCount": counts.get(DenominatorState.PASSED.value, 0),
        "failCount": counts.get(DenominatorState.FAILED.value, 0),
        "skipCount": counts.get(DenominatorState.SKIPPED.value, 0),
        "deselectionCount": counts.get(DenominatorState.DESELECTED.value, 0),
        "expectedFailureCount": counts.get(DenominatorState.EXPECTED_FAILURE.value, 0),
        "unexpectedPassCount": counts.get(DenominatorState.UNEXPECTED_PASS.value, 0),
        "timeoutCount": counts.get(DenominatorState.TIMEOUT.value, 0),
        "interruptedCount": counts.get(DenominatorState.INTERRUPTED.value, 0),
        "discoveryFailureCount": counts.get(DenominatorState.DISCOVERY_FAILURE.value, 0),
        "errorCount": counts.get(DenominatorState.ERROR.value, 0),
        "unknownCount": counts.get(DenominatorState.UNKNOWN.value, 0),
        "constitutionalVerdict": "PASS" if not failures else "FAIL",
        "failureCodes": tuple(dict.fromkeys(failures + list(ledger["failureCodes"]))),
        "executionTimestamp": utc_timestamp(),
    }
    return {**evidence_body, "deterministicContentHash": _stable_hash(evidence_body)}


def qualify_controlled_paper_candidate(
    repo_root: str | Path,
    cr7_evidence: dict[str, Any],
    *,
    commit: str = "WORKTREE",
) -> dict[str, Any]:
    """Evaluate CR-10 qualification against the exact CR-7 candidate."""
    root = Path(repo_root).resolve()
    head = commit if commit != "WORKTREE" else _git(root, "rev-parse", "HEAD")
    current = build_candidate_identity(root, certification=False, allow_dirty=True)["candidate_identity"]
    preflight = run_preflight(root, certification=True).get("preflight_result", {})
    failures = []
    if cr7_evidence.get("constitutionalVerdict") != "PASS":
        failures.append("CR7_EVIDENCE_NOT_PASS")
    if cr7_evidence.get("commitIdentity") != head:
        failures.append("CR7_CANDIDATE_COMMIT_MISMATCH")
    if cr7_evidence.get("candidateIdentity", {}).get("stable_identity_hash") != current["stable_identity_hash"]:
        failures.append("CR7_CANDIDATE_IDENTITY_MISMATCH")
    if preflight.get("verdict") != "PASS":
        failures.append("CANDIDATE_PREFLIGHT_NOT_PASS")
    qualification_body = {
        "qualificationIdentifier": f"CR10-QUALIFICATION-{_stable_hash((head, cr7_evidence.get('deterministicContentHash', ''), failures))[:16].upper()}",
        "designation": "Controlled Paper Candidate",
        "candidateIdentity": current,
        "cr7EvidenceIdentifier": cr7_evidence.get("evidenceIdentifier", ""),
        "cr7EvidenceHash": cr7_evidence.get("deterministicContentHash", ""),
        "repositoryCommit": head,
        "qualified": not failures,
        "failureCodes": tuple(failures),
        "preflightVerdict": preflight.get("verdict", "FAIL"),
        "timestampUtc": utc_timestamp(),
    }
    return {**qualification_body, "deterministicHash": _stable_hash(qualification_body)}


def publish_cr_prerequisite_verdict(
    cr7_evidence: dict[str, Any],
    cr10_qualification: dict[str, Any],
) -> dict[str, Any]:
    failures = []
    if cr7_evidence.get("constitutionalVerdict") != "PASS":
        failures.append("CR7_NOT_PASS")
    if not cr10_qualification.get("qualified"):
        failures.append("CR10_NOT_QUALIFIED")
    if cr7_evidence.get("candidateIdentity", {}).get("stable_identity_hash") != cr10_qualification.get("candidateIdentity", {}).get("stable_identity_hash"):
        failures.append("CR7_CR10_CANDIDATE_MISMATCH")
    body = {
        "verdictIdentifier": f"CR-PREREQ-{_stable_hash((cr7_evidence.get('evidenceIdentifier'), cr10_qualification.get('qualificationIdentifier'), failures))[:16].upper()}",
        "candidateIdentifier": cr10_qualification.get("candidateIdentity", {}).get("stable_identity_hash", ""),
        "cr7EvidenceIdentifier": cr7_evidence.get("evidenceIdentifier", ""),
        "cr10QualificationIdentifier": cr10_qualification.get("qualificationIdentifier", ""),
        "verdictStatus": "PASS" if not failures else "FAIL",
        "verdictTimestamp": utc_timestamp(),
        "failureCodes": tuple(failures),
        "evidenceReferences": (cr7_evidence.get("evidenceIdentifier", ""), cr10_qualification.get("qualificationIdentifier", "")),
        "schemaVersion": CIC02_VERSION,
        "generatorIdentity": "certification_recovery_foundation.publish_cr_prerequisite_verdict",
        "appendOnly": True,
    }
    return {**body, "deterministicHash": _stable_hash(body)}


def execute_cic02_recovery_foundation(
    repo_root: str | Path = ".",
    *,
    commit: str = "WORKTREE",
    execution_results: Iterable[ExecutionResult | dict[str, Any]] = (),
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    head = commit if commit != "WORKTREE" else _git(root, "rev-parse", "HEAD")
    manifest = discover_canonical_tests(root, commit=head)
    ledger = build_denominator_ledger(manifest, execution_results)
    cr7 = build_cr7_evidence_envelope(manifest, ledger, commit=head)
    cr10 = qualify_controlled_paper_candidate(root, cr7, commit=head)
    verdict = publish_cr_prerequisite_verdict(cr7, cr10)
    return {
        "schemaVersion": CIC02_VERSION,
        "orderId": "CIC-02",
        "generatedAtUtc": utc_timestamp(),
        "repositoryCommit": head,
        "canonicalTestManifest": manifest,
        "denominatorLedger": ledger,
        "cr7Evidence": cr7,
        "cr10Qualification": cr10,
        "cssPrerequisitePublication": verdict,
        "runtimeInterface": {
            "candidateIdentifier": verdict["candidateIdentifier"],
            "cr7Status": cr7["constitutionalVerdict"],
            "cr10Status": "PASS" if cr10["qualified"] else "FAIL",
            "verdictIdentifier": verdict["verdictIdentifier"],
            "evidenceIdentifiers": verdict["evidenceReferences"],
            "failureCodes": verdict["failureCodes"],
            "schemaVersion": CIC02_VERSION,
            "publicationTimestamp": verdict["verdictTimestamp"],
            "mutable": False,
        },
        "verdict": verdict["verdictStatus"],
        "constitutionalStatement": "CIC-02 publishes immutable CR prerequisite truth for CSS. It fails closed unless CR-7 denominator execution and CR-10 Controlled Paper Candidate qualification both pass for one exact candidate.",
    }


def _classification_for_state(state: DenominatorState) -> str:
    if state == DenominatorState.PASSED:
        return "CONSTITUTIONAL_PASS"
    if state in {DenominatorState.FAILED, DenominatorState.ERROR, DenominatorState.TIMEOUT, DenominatorState.INTERRUPTED, DenominatorState.DISCOVERY_FAILURE}:
        return "CONSTITUTIONAL_FAILURE"
    if state in {DenominatorState.NOT_EXECUTED, DenominatorState.QUEUED, DenominatorState.RUNNING, DenominatorState.UNKNOWN}:
        return "INCOMPLETE_RECOVERY"
    return "NON_PASS_ACCOUNTED"


def _stable_candidate_identity(candidate: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "repository_commit",
        "repository_branch",
        "source_tree_hash",
        "dependency_hash",
        "configuration_hash",
        "policy_hash",
        "schema_hash",
        "manifest_hash",
        "stable_identity_hash",
        "working_tree_clean",
    )
    return {key: candidate.get(key, "") for key in keys}


def _failure_code_for_state(state: DenominatorState) -> str:
    return "" if state == DenominatorState.PASSED else f"CR7_{state.value}"


def _state_from_result(result: ExecutionResult | dict[str, Any] | None) -> DenominatorState:
    raw = _result_value(result, "state", DenominatorState.UNKNOWN)
    if isinstance(raw, DenominatorState):
        return raw
    try:
        return DenominatorState(str(raw))
    except ValueError:
        return DenominatorState.UNKNOWN


def _result_value(result: ExecutionResult | dict[str, Any] | None, key: str, default: Any = None) -> Any:
    if result is None:
        return default
    if isinstance(result, dict):
        return result.get(key, default)
    return getattr(result, key, default)


def _state_counts(records: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        state = str(record["currentState"])
        counts[state] = counts.get(state, 0) + 1
    return counts


def _git(root: Path, *args: str) -> str:
    result = __import__("subprocess").run(("git", *args), cwd=root, text=True, capture_output=True, check=False)
    return result.stdout.strip()


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value

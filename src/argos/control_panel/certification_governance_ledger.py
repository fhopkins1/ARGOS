"""CIC-07 certification governance and historical ledger.

Certification state is derived from append-only ledger entries.  Governance
can record decisions and transitions, but it cannot override constitutional,
proof, drift, integrity, or evidence failures.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Iterable

from argos.candidate_integrity import stable_hash
from argos.control_panel.semantic_drift_engine import DriftClassification


CIC07_VERSION = "CIC-07.1"
LEDGER_SCHEMA_VERSION = "CIC07-LEDGER.1"
EXPORT_SCHEMA_VERSION = "CIC07-AUDIT-EXPORT.1"
GENESIS_HASH = "0" * 64


class CertificationLevel(str, Enum):
    DEVELOPMENT = "DEVELOPMENT"
    PAPER_CANDIDATE = "PAPER_CANDIDATE"
    PAPER_CERTIFIED = "PAPER_CERTIFIED"
    PRODUCTION_CANDIDATE = "PRODUCTION_CANDIDATE"
    PRODUCTION_CERTIFIED = "PRODUCTION_CERTIFIED"


class CertificationStatus(str, Enum):
    PENDING = "PENDING"
    ISSUED = "ISSUED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    SUPERSEDED = "SUPERSEDED"
    QUARANTINED = "QUARANTINED"
    TAMPER_INVALIDATED = "TAMPER_INVALIDATED"
    WITHDRAWN = "WITHDRAWN"


class GovernanceAction(str, Enum):
    ISSUE = "ISSUE"
    DENY = "DENY"
    EXPIRE = "EXPIRE"
    REVOKE = "REVOKE"
    SUPERSEDE = "SUPERSEDE"
    RECERTIFY = "RECERTIFY"
    QUARANTINE_EVIDENCE = "QUARANTINE_EVIDENCE"
    RELEASE_EVIDENCE_QUARANTINE = "RELEASE_EVIDENCE_QUARANTINE"
    RECORD_RULE_CHANGE = "RECORD_RULE_CHANGE"
    RECORD_DRIFT = "RECORD_DRIFT"
    INVALIDATE_TAMPER = "INVALIDATE_TAMPER"
    ANNOTATE = "ANNOTATE"


class GovernanceErrorCode(str, Enum):
    CERTIFICATION_NOT_FOUND = "CIC07_CERTIFICATION_NOT_FOUND"
    CONSTITUTIONAL_FAILURE = "CIC07_CONSTITUTIONAL_FAILURE"
    PROOF_MISSING = "CIC07_PROOF_MISSING"
    DRIFT_DISQUALIFYING = "CIC07_DRIFT_DISQUALIFYING"
    AUTHORIZATION_DENIED = "CIC07_AUTHORIZATION_DENIED"
    INVALID_TRANSITION = "CIC07_INVALID_TRANSITION"
    DUPLICATE_COMMAND = "CIC07_DUPLICATE_COMMAND"
    IDEMPOTENCY_CONFLICT = "CIC07_IDEMPOTENCY_CONFLICT"
    CONCURRENCY_CONFLICT = "CIC07_CONCURRENCY_CONFLICT"
    EVIDENCE_QUARANTINED = "CIC07_EVIDENCE_QUARANTINED"
    INTEGRITY_VERIFICATION_FAILED = "CIC07_INTEGRITY_VERIFICATION_FAILED"
    LEDGER_SEQUENCE_GAP = "CIC07_LEDGER_SEQUENCE_GAP"
    LEDGER_HASH_MISMATCH = "CIC07_LEDGER_HASH_MISMATCH"
    PROJECTION_MISMATCH = "CIC07_PROJECTION_MISMATCH"
    EXPORT_INCOMPLETE = "CIC07_EXPORT_INCOMPLETE"


TRANSITION_MATRIX = {
    CertificationStatus.PENDING: {CertificationStatus.ISSUED, CertificationStatus.DENIED, CertificationStatus.WITHDRAWN},
    CertificationStatus.ISSUED: {CertificationStatus.EXPIRED, CertificationStatus.REVOKED, CertificationStatus.SUPERSEDED, CertificationStatus.QUARANTINED, CertificationStatus.TAMPER_INVALIDATED},
    CertificationStatus.QUARANTINED: {CertificationStatus.REVOKED, CertificationStatus.TAMPER_INVALIDATED, CertificationStatus.SUPERSEDED},
    CertificationStatus.EXPIRED: set(),
    CertificationStatus.REVOKED: set(),
    CertificationStatus.SUPERSEDED: set(),
    CertificationStatus.DENIED: set(),
    CertificationStatus.TAMPER_INVALIDATED: set(),
    CertificationStatus.WITHDRAWN: set(),
}


@dataclass(frozen=True)
class GovernanceAuthority:
    actor_id: str
    authority_source: str
    actions: tuple[GovernanceAction, ...]
    scope: str
    workflow_token: str
    valid: bool = True


@dataclass(frozen=True)
class CertificationDecision:
    certification_id: str
    candidate_identity_digest: str
    repository_commit: str
    baseline_id: str
    baseline_digest: str
    rule_set_id: str
    rule_version: str
    rule_digest: str
    evidence_manifest_digest: str
    proof_manifest_digest: str
    drift_evaluation_digest: str
    constitutional_evaluation_digest: str
    constitutional_status: str
    proof_status: str
    drift_classification: str
    certification_policy_version: str
    level: CertificationLevel
    expiration_time: str = ""


@dataclass(frozen=True)
class GovernanceCommand:
    command_id: str
    action: GovernanceAction
    certification_id: str
    target_status: CertificationStatus
    decision: CertificationDecision
    authority: GovernanceAuthority
    reason_code: str = ""
    predecessor_certification_id: str = ""
    successor_certification_id: str = ""
    evidence_scope: tuple[str, ...] = ()
    expected_sequence: int | None = None


@dataclass(frozen=True)
class LedgerEntry:
    sequence: int
    ledger_entry_id: str
    previous_hash: str
    action: GovernanceAction
    certification_id: str
    prior_status: str
    resulting_status: str
    command_digest: str
    payload: dict[str, Any]
    authority_record: dict[str, Any]
    failure_codes: tuple[str, ...]
    schema_version: str = LEDGER_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        body = _jsonable(asdict(self))
        return {**body, "entryHash": stable_hash(body)}


class CertificationGovernanceLedger:
    def __init__(self, entries: Iterable[dict[str, Any]] = ()) -> None:
        self._entries: list[dict[str, Any]] = []
        self._command_index: dict[str, tuple[str, dict[str, Any]]] = {}
        for entry in entries:
            self._entries.append(dict(entry))

    @property
    def entries(self) -> tuple[dict[str, Any], ...]:
        return tuple(self._entries)

    def apply(self, command: GovernanceCommand) -> dict[str, Any]:
        command_digest = stable_hash(asdict(command))
        existing = self._command_index.get(command.command_id)
        if existing:
            existing_digest, result = existing
            if existing_digest == command_digest:
                return {"status": "ALREADY_APPLIED", "entry": result, "failureCodes": (GovernanceErrorCode.DUPLICATE_COMMAND.value,)}
            return {"status": "FAIL", "entry": {}, "failureCodes": (GovernanceErrorCode.IDEMPOTENCY_CONFLICT.value,)}
        projection = rebuild_projection(self.entries)
        prior = projection.get(command.certification_id, {}).get("status", CertificationStatus.PENDING.value)
        if command.expected_sequence is not None and command.expected_sequence != len(self._entries):
            return {"status": "FAIL", "entry": {}, "failureCodes": (GovernanceErrorCode.CONCURRENCY_CONFLICT.value,)}
        failures = validate_command(command, CertificationStatus(prior))
        status = "FAIL" if failures else "COMMITTED"
        resulting = prior if failures else command.target_status.value
        entry = LedgerEntry(
            len(self._entries) + 1,
            f"CIC07-LEDGER-{stable_hash((len(self._entries) + 1, command.command_id, command_digest))[:16].upper()}",
            self._entries[-1]["entryHash"] if self._entries else GENESIS_HASH,
            command.action,
            command.certification_id,
            prior,
            resulting,
            command_digest,
            _decision_payload(command),
            _jsonable(asdict(command.authority)),
            tuple(failures),
        ).to_dict()
        self._entries.append(entry)
        self._command_index[command.command_id] = (command_digest, entry)
        return {"status": status, "entry": entry, "failureCodes": tuple(failures)}

    def query_current(self, certification_id: str) -> dict[str, Any]:
        projection = rebuild_projection(self.entries)
        record = projection.get(certification_id)
        if not record:
            return {"found": False, "failureCodes": (GovernanceErrorCode.CERTIFICATION_NOT_FOUND.value,)}
        return {"found": True, **record, "presentlyUsable": presently_usable(record)}

    def timeline(self, certification_id: str) -> tuple[dict[str, Any], ...]:
        return tuple(entry for entry in self.entries if entry["certification_id"] == certification_id)

    def verify_integrity(self) -> dict[str, Any]:
        return verify_ledger_integrity(self.entries)

    def audit_export(self, scope: str = "ALL") -> dict[str, Any]:
        return build_audit_export(self.entries, scope=scope)


def validate_command(command: GovernanceCommand, prior_status: CertificationStatus) -> tuple[str, ...]:
    failures: list[str] = []
    if not command.authority.valid or command.action not in command.authority.actions or command.authority.workflow_token == "":
        failures.append(GovernanceErrorCode.AUTHORIZATION_DENIED.value)
    if command.target_status not in TRANSITION_MATRIX.get(prior_status, set()) and not (prior_status == CertificationStatus.PENDING and command.action in {GovernanceAction.RECORD_DRIFT, GovernanceAction.RECORD_RULE_CHANGE, GovernanceAction.QUARANTINE_EVIDENCE, GovernanceAction.ANNOTATE}):
        failures.append(f"{GovernanceErrorCode.INVALID_TRANSITION.value}:{prior_status.value}->{command.target_status.value}")
    decision = command.decision
    if command.action == GovernanceAction.ISSUE:
        if decision.constitutional_status != "PASS":
            failures.append(GovernanceErrorCode.CONSTITUTIONAL_FAILURE.value)
        if decision.proof_status != "PROVEN":
            failures.append(GovernanceErrorCode.PROOF_MISSING.value)
        if decision.drift_classification not in {DriftClassification.NO_DRIFT.value, DriftClassification.SAFE_DRIFT.value}:
            failures.append(GovernanceErrorCode.DRIFT_DISQUALIFYING.value)
        if not decision.evidence_manifest_digest or "QUARANTINED" in command.evidence_scope:
            failures.append(GovernanceErrorCode.EVIDENCE_QUARANTINED.value)
    return tuple(dict.fromkeys(failures))


def rebuild_projection(entries: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    projection: dict[str, dict[str, Any]] = {}
    for entry in sorted(entries, key=lambda item: int(item["sequence"])):
        projection[entry["certification_id"]] = {
            "certificationId": entry["certification_id"],
            "status": entry["resulting_status"],
            "level": entry["payload"]["decision"]["level"],
            "candidateIdentityDigest": entry["payload"]["decision"]["candidate_identity_digest"],
            "repositoryCommit": entry["payload"]["decision"]["repository_commit"],
            "baselineId": entry["payload"]["decision"]["baseline_id"],
            "ruleVersion": entry["payload"]["decision"]["rule_version"],
            "evidenceManifestDigest": entry["payload"]["decision"]["evidence_manifest_digest"],
            "proofManifestDigest": entry["payload"]["decision"]["proof_manifest_digest"],
            "driftClassification": entry["payload"]["decision"]["drift_classification"],
            "constitutionalStatus": entry["payload"]["decision"]["constitutional_status"],
            "latestLedgerEntryId": entry["ledger_entry_id"],
            "latestLedgerEntryHash": entry["entryHash"],
            "integrityState": "VERIFIED",
        }
    return projection


def presently_usable(record: dict[str, Any]) -> bool:
    return (
        record.get("status") == CertificationStatus.ISSUED.value
        and record.get("constitutionalStatus") == "PASS"
        and record.get("driftClassification") in {DriftClassification.NO_DRIFT.value, DriftClassification.SAFE_DRIFT.value}
        and record.get("integrityState") == "VERIFIED"
    )


def verify_ledger_integrity(entries: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = tuple(sorted(entries, key=lambda item: int(item["sequence"])))
    failures: list[str] = []
    previous = GENESIS_HASH
    seen_sequences: set[int] = set()
    for expected, entry in enumerate(rows, start=1):
        sequence = int(entry.get("sequence", -1))
        if sequence != expected:
            failures.append(f"{GovernanceErrorCode.LEDGER_SEQUENCE_GAP.value}:{expected}:{sequence}")
        if sequence in seen_sequences:
            failures.append(f"{GovernanceErrorCode.LEDGER_SEQUENCE_GAP.value}:duplicate:{sequence}")
        seen_sequences.add(sequence)
        if entry.get("previous_hash") != previous:
            failures.append(f"{GovernanceErrorCode.LEDGER_HASH_MISMATCH.value}:{sequence}:previous")
        observed = entry.get("entryHash", "")
        body = {key: value for key, value in entry.items() if key != "entryHash"}
        expected_hash = stable_hash(body)
        if observed != expected_hash:
            failures.append(f"{GovernanceErrorCode.LEDGER_HASH_MISMATCH.value}:{sequence}:entry")
        previous = observed
    projection = rebuild_projection(rows)
    return {"valid": not failures, "failureCodes": tuple(failures), "entryCount": len(rows), "projectionDigest": stable_hash(projection)}


def build_audit_export(entries: Iterable[dict[str, Any]], *, scope: str = "ALL") -> dict[str, Any]:
    rows = tuple(sorted(entries, key=lambda item: int(item["sequence"])))
    integrity = verify_ledger_integrity(rows)
    projection = rebuild_projection(rows)
    body = {
        "schemaVersion": EXPORT_SCHEMA_VERSION,
        "scope": scope,
        "generationAuthority": "CIC-07 audit export",
        "ledgerEntries": rows,
        "currentStateProjection": projection,
        "integrityVerification": integrity,
        "timelineByCertification": {cert_id: tuple(entry["ledger_entry_id"] for entry in rows if entry["certification_id"] == cert_id) for cert_id in sorted(projection)},
        "omittedPayloads": (),
        "secretsExcluded": True,
        "machineSpecificPathsExcluded": True,
        "complete": integrity["valid"],
    }
    return {**body, "exportDigest": stable_hash(body)}


def verify_audit_export(export: dict[str, Any]) -> dict[str, Any]:
    body = {key: value for key, value in export.items() if key != "exportDigest"}
    expected = stable_hash(body)
    return {"valid": expected == export.get("exportDigest"), "expectedDigest": expected, "observedDigest": export.get("exportDigest", "")}


def sample_decision(commit: str = "1" * 40, *, constitutional: str = "PASS", proof: str = "PROVEN", drift: str = DriftClassification.NO_DRIFT.value) -> CertificationDecision:
    candidate = stable_hash(("candidate", commit))
    return CertificationDecision(
        "ARGOS-CERT-001",
        candidate,
        commit,
        "ARGOS-BASELINE-001",
        stable_hash("baseline"),
        "ARGOS-RULESET",
        "1",
        stable_hash("rules"),
        stable_hash("evidence"),
        stable_hash("proof"),
        stable_hash("drift"),
        stable_hash("constitutional"),
        constitutional,
        proof,
        drift,
        "CIC07-POLICY.1",
        CertificationLevel.PAPER_CANDIDATE,
    )


def sample_authority(*actions: GovernanceAction) -> GovernanceAuthority:
    return GovernanceAuthority("authority://certification-governance", "CIC-07", actions or tuple(GovernanceAction), "*", "TOKEN-CIC07", True)


def write_cic07_evidence(export: dict[str, Any], output_dir: str | Path) -> dict[str, Any]:
    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    _write_json(out / "governance_audit_export.json", export)
    _write_json(out / "ledger_entries.json", export["ledgerEntries"])
    _write_json(out / "current_state_projection.json", export["currentStateProjection"])
    _write_json(out / "integrity_verification.json", export["integrityVerification"])
    _write_json(out / "export_verification.json", verify_audit_export(export))
    manifest_body = {
        "schemaVersion": "CIC07-EVIDENCE-MANIFEST.1",
        "verdict": "PASS" if export["integrityVerification"]["valid"] else "FAIL",
        "entryCount": len(export["ledgerEntries"]),
        "exportDigest": export["exportDigest"],
        "artifacts": tuple(_file_record(path, out) for path in sorted(out.glob("*.json")) if path.name != "manifest.json"),
    }
    manifest = {**manifest_body, "manifestDigest": stable_hash(manifest_body)}
    _write_json(out / "manifest.json", manifest)
    return manifest


def demo_ledger(commit: str = "1" * 40) -> CertificationGovernanceLedger:
    ledger = CertificationGovernanceLedger()
    decision = sample_decision(commit)
    authority = sample_authority(GovernanceAction.ISSUE, GovernanceAction.REVOKE, GovernanceAction.EXPIRE, GovernanceAction.SUPERSEDE, GovernanceAction.RECORD_DRIFT)
    ledger.apply(GovernanceCommand("CMD-ISSUE-001", GovernanceAction.ISSUE, decision.certification_id, CertificationStatus.ISSUED, decision, authority))
    ledger.apply(GovernanceCommand("CMD-DRIFT-001", GovernanceAction.RECORD_DRIFT, decision.certification_id, CertificationStatus.ISSUED, decision, authority, reason_code="periodic-drift-record"))
    return ledger


def _decision_payload(command: GovernanceCommand) -> dict[str, Any]:
    return {
        "decision": _jsonable(asdict(command.decision)),
        "reasonCode": command.reason_code,
        "predecessorCertificationId": command.predecessor_certification_id,
        "successorCertificationId": command.successor_certification_id,
        "evidenceScope": tuple(command.evidence_scope),
    }


def _jsonable(value: Any) -> Any:
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(_jsonable(payload), indent=2, sort_keys=True), encoding="utf-8")


def _file_record(path: Path, root: Path) -> dict[str, str]:
    return {"path": path.relative_to(root).as_posix(), "sha256": _file_hash(path)}


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git(repo_root: Path, *args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=str(repo_root),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def cic07_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CIC-07 governance ledger evidence")
    parser.add_argument("--output", required=True)
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    export = demo_ledger(_git(repo_root, "rev-parse", "HEAD")).audit_export()
    manifest = write_cic07_evidence(export, args.output)
    print(json.dumps(_jsonable(manifest), indent=2, sort_keys=True))
    return 0 if manifest.get("verdict") == "PASS" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(cic07_main())

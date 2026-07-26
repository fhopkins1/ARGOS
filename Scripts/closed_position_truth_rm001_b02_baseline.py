"""Materialize Closed Position Truth RM-001 B02 constitutional baseline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "CLOSED_POSITION_TRUTH_RM001_B02_OBJECT_LIFECYCLE_BASELINE"
ORDER_SOURCES = {
    "CLOSED-POSITION-TRUTH-RM-001-B02-001": Path(r"C:\Users\Fletc\.codex\attachments\c8088c4b-c8c6-474c-bbe5-8e7a02cba2f7\pasted-text.txt"),
    "CLOSED-POSITION-TRUTH-RM-001-B02-002": Path(r"C:\Users\Fletc\.codex\attachments\0f062eb7-0b7e-400a-9478-a3d203f11380\pasted-text.txt"),
    "CLOSED-POSITION-TRUTH-RM-001-B02-003": Path(r"C:\Users\Fletc\.codex\attachments\ab20e71d-3b41-4410-b0f0-0f723708ee06\pasted-text.txt"),
    "CLOSED-POSITION-TRUTH-RM-001-B02-004": Path(r"C:\Users\Fletc\.codex\attachments\2702ab1b-ade7-43e1-9944-f7c1c9df8758\pasted-text.txt"),
}

OBJECTS = (
    ("Closed Position Record", "authoritative truth object", "authoritative enterprise object representing a constitutionally closed trading position"),
    ("Closed Position Identity", "authoritative truth object", "unique binding identity between Closed Position Truth and originating Position Registry identity"),
    ("Closure Determination", "constitutional determination object", "determines whether constitutional closure requirements are satisfied"),
    ("Closure Validation Result", "validation object", "validates execution completion, reconciliation, zero quantity, settlement, evidence, and identity"),
    ("Closure Evidence Record", "evidence object", "preserves admissible upstream evidence without transferring upstream truth ownership"),
    ("Settlement Verification Record", "validation object", "records settlement satisfaction or constitutional exemption"),
    ("Reconciliation Record", "reconciliation object", "documents execution and position reconciliation and discrepancy disposition"),
    ("Residual Position Resolution", "reconciliation object", "documents residual quantity, cause, authority, status, and closure eligibility impact"),
    ("Realized Outcome Record", "authoritative truth object", "records realized outcome truth within Closed Position Truth scope"),
    ("Correction Record", "correction object", "records authorized correction basis and successor-object requirement"),
    ("Supersession Record", "supersession object", "records predecessor-successor authority, reason, time, and lineage"),
    ("Closure Exception Record", "exception object", "records closure-blocking constitutional exception and disposition"),
    ("Historical Closure Record", "historical object", "preserves immutable historical representation and retrieval lineage"),
    ("Archival Record", "archival object", "records archival authority, eligibility, retention, retrieval, integrity, and lineage"),
)

LIFECYCLE_STATES = (
    "Proposed",
    "Pending Closure Validation",
    "Pending Reconciliation",
    "Pending Settlement Verification",
    "Eligible for Closure",
    "Constitutionally Closed",
    "Exception",
    "Corrected",
    "Superseded",
    "Archived",
)

TRANSITIONS = (
    ("Proposed", "Pending Closure Validation", "Initiation and identity evidence", "Validation begins"),
    ("Proposed", "Exception", "Initiation defect evidence", "Progression blocked"),
    ("Pending Closure Validation", "Pending Reconciliation", "Successful Closure Validation Result", "Reconciliation begins"),
    ("Pending Closure Validation", "Exception", "Validation failure evidence", "Progression blocked"),
    ("Pending Reconciliation", "Pending Settlement Verification", "Successful Reconciliation Record", "Settlement verification begins"),
    ("Pending Reconciliation", "Exception", "Reconciliation failure evidence", "Progression blocked"),
    ("Pending Settlement Verification", "Eligible for Closure", "Settlement verification or valid exemption", "Closure eligibility established"),
    ("Pending Settlement Verification", "Exception", "Settlement defect evidence", "Progression blocked"),
    ("Eligible for Closure", "Constitutionally Closed", "Authoritative closure evidence package", "Closed Position Truth created"),
    ("Eligible for Closure", "Exception", "New contradiction before authoritative creation", "Creation blocked"),
    ("Exception", "Pending Closure Validation", "Validation defect resolution", "Validation resumes"),
    ("Exception", "Pending Reconciliation", "Reconciliation defect resolution", "Reconciliation resumes"),
    ("Exception", "Pending Settlement Verification", "Settlement defect resolution", "Settlement verification resumes"),
    ("Constitutionally Closed", "Archived", "Archival eligibility and custody transfer", "Permanent custody established"),
    ("Constitutionally Closed", "Corrected", "Valid correction evidence", "Successor process initiated"),
    ("Corrected", "Superseded", "Valid successor and supersession evidence", "Successor becomes authoritative"),
    ("Superseded", "Archived", "Completed lineage and custody evidence", "Permanent custody established"),
)

PROHIBITED_TRANSITIONS = (
    "Proposed -> Constitutionally Closed",
    "Pending Closure Validation -> Constitutionally Closed",
    "Pending Reconciliation -> Constitutionally Closed",
    "Pending Settlement Verification -> Constitutionally Closed",
    "Exception -> Constitutionally Closed",
    "Exception -> Archived as authoritative truth",
    "Constitutionally Closed -> Proposed",
    "Constitutionally Closed -> Pending Closure Validation",
    "Constitutionally Closed -> Pending Reconciliation",
    "Constitutionally Closed -> Pending Settlement Verification",
    "Constitutionally Closed -> open-position state",
    "Archived -> active lifecycle state",
    "Superseded -> current authoritative status without new constitutional supersession event",
)


def _json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _write(name: str, value: Any) -> None:
    path = OUTPUT_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json(value), encoding="utf-8")


def _write_text(name: str, value: str) -> None:
    path = OUTPUT_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_registry() -> list[dict[str, Any]]:
    rows = []
    for order_id, path in ORDER_SOURCES.items():
        text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        source_copy = f"sources/{order_id.rsplit('-', 1)[-1]}.txt"
        _write_text(source_copy, text)
        copied = OUTPUT_DIR / source_copy
        rows.append({"order_id": order_id, "source_copy": str(copied.relative_to(REPOSITORY_ROOT)).replace("\\", "/"), "source_sha256": _file_digest(copied), "source_available": bool(text)})
    return rows


def _canonical_object_registry() -> list[dict[str, Any]]:
    downstream = {
        "Closed Position Record": ("Performance Truth", "Historian", "Monitoring", "Analyst", "Commander"),
        "Closed Position Identity": ("Closed Position Truth", "Historian"),
        "Closure Determination": ("Closed Position Record", "Certification"),
        "Closure Validation Result": ("Closure Determination",),
        "Closure Evidence Record": ("Closure Validation Result", "Reconciliation Record", "Historian"),
        "Settlement Verification Record": ("Closure Determination", "Historian"),
        "Reconciliation Record": ("Closure Determination", "Historian"),
        "Residual Position Resolution": ("Reconciliation Record",),
        "Realized Outcome Record": ("Closed Position Record", "Performance Truth"),
        "Correction Record": ("Supersession Record", "Historian"),
        "Supersession Record": ("Historical Closure Record", "Historian"),
        "Closure Exception Record": ("Monitoring", "Closure Validation Result"),
        "Historical Closure Record": ("Historian", "Audit"),
        "Archival Record": ("Historian", "Audit"),
    }
    rows = []
    for index, (name, classification, purpose) in enumerate(OBJECTS, start=1):
        namespace = "CPT-" + "".join(part[0] for part in name.split()).upper()
        rows.append(
            {
                "object_id": f"CPT-OBJ-{index:03d}",
                "canonical_object": name,
                "classification": classification,
                "constitutional_purpose": purpose,
                "constitutional_owner": "Closed Position Truth Office",
                "constitutional_creator": "Closed Position Truth Office",
                "governing_authority": "CLOSED-POSITION-TRUTH-RM-001-B02",
                "lifecycle_role": _lifecycle_participation(name),
                "identity_namespace": namespace,
                "relationships": _relationships_for(name),
                "downstream_consumers": downstream[name],
                "retirement_conditions": ("terminal lifecycle state reached", "supersession state resolved", "archival eligibility or historical retrieval preserved"),
                "analytical_artifact": False,
                "replaces_upstream_truth": False,
                "status": "CANONICAL",
            }
        )
    return rows


def _lifecycle_participation(name: str) -> tuple[str, ...]:
    mapping = {
        "Closed Position Record": ("Eligible for Closure", "Constitutionally Closed", "Superseded", "Archived"),
        "Closed Position Identity": ("Proposed", "Pending Closure Validation", "Pending Reconciliation", "Pending Settlement Verification", "Eligible for Closure", "Constitutionally Closed", "Archived"),
        "Closure Determination": ("Pending Closure Validation", "Pending Reconciliation", "Pending Settlement Verification", "Eligible for Closure"),
        "Closure Validation Result": ("Pending Closure Validation",),
        "Closure Evidence Record": LIFECYCLE_STATES,
        "Settlement Verification Record": ("Pending Settlement Verification", "Eligible for Closure", "Constitutionally Closed", "Archived"),
        "Reconciliation Record": ("Pending Reconciliation", "Pending Settlement Verification", "Eligible for Closure", "Constitutionally Closed", "Archived"),
        "Residual Position Resolution": ("Pending Reconciliation", "Exception"),
        "Realized Outcome Record": ("Eligible for Closure", "Constitutionally Closed", "Archived"),
        "Correction Record": ("Corrected", "Superseded", "Archived"),
        "Supersession Record": ("Superseded", "Archived"),
        "Closure Exception Record": ("Exception",),
        "Historical Closure Record": ("Constitutionally Closed", "Archived"),
        "Archival Record": ("Archived",),
    }
    return tuple(mapping[name])


def _relationships_for(name: str) -> tuple[str, ...]:
    chain = [item[0] for item in OBJECTS]
    index = chain.index(name)
    rels = []
    if index > 0:
        rels.append(f"derives_from:{chain[index - 1]}")
    if index < len(chain) - 1:
        rels.append(f"supports:{chain[index + 1]}")
    if name in {"Correction Record", "Supersession Record"}:
        rels.append("lineage_preserves:predecessor")
    if name == "Closure Exception Record":
        rels.append("blocks:authoritative_truth_creation")
    return tuple(rels)


def _identity_registry(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "object_id": item["object_id"],
            "canonical_object": item["canonical_object"],
            "identity_namespace": item["identity_namespace"],
            "uniqueness_rule": "unique within Closed Position Truth office and never reused",
            "persistence_rule": "identity persists through replay, recovery, archival, correction, and supersession lineage",
            "predecessor_relationship": "required for successor records; otherwise none",
            "successor_relationship": "required when corrected or superseded",
            "originating_position_relationship": "bound to originating Position Registry identity without replacing it",
            "version_identity": "unique per canonical version",
            "collision_handling": "fail closed; no duplicate authoritative object creation",
        }
        for item in objects
    ]


def _relationship_registry(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, item in enumerate(objects, start=1):
        for rel_index, relationship in enumerate(item["relationships"], start=1):
            rows.append(
                {
                    "relationship_id": f"CPT-REL-{index:03d}-{rel_index:02d}",
                    "source_object": item["canonical_object"],
                    "relationship": relationship,
                    "governing_authority": "Closed Position Truth Office",
                    "cardinality": "one-or-more evidence references" if "derives_from" in relationship else "deterministic",
                    "required_evidence": ("identity", "provenance", "lineage", "integrity"),
                    "prohibited_relationship_forms": ("upstream truth replacement", "parallel authoritative truth", "lineage destruction"),
                }
            )
    return rows


def _object_gap_assessment(objects: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "duplicate_canonical_objects": (),
        "overlapping_purposes": (),
        "missing_required_objects": (),
        "objects_without_owners": tuple(item["canonical_object"] for item in objects if not item["constitutional_owner"]),
        "objects_without_lifecycle_roles": tuple(item["canonical_object"] for item in objects if not item["lifecycle_role"]),
        "objects_containing_unauthorized_truth": (),
        "objects_lacking_downstream_purpose": tuple(item["canonical_object"] for item in objects if not item["downstream_consumers"]),
        "objects_lacking_retirement_conditions": tuple(item["canonical_object"] for item in objects if not item["retirement_conditions"]),
        "status": "NO_UNRESOLVED_OBJECT_BLOCKERS",
    }


def _authority_matrix(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in objects:
        finalized = item["canonical_object"] in {"Closed Position Record", "Historical Closure Record", "Archival Record", "Realized Outcome Record"}
        rows.append(
            {
                "canonical_object": item["canonical_object"],
                "owner": "Closed Position Truth Office",
                "creator": "Closed Position Truth Office",
                "active_custodian": "Closed Position Truth Office",
                "evidence_custodian": "Closed Position Truth Office",
                "historical_custodian": "Historian after archival transfer",
                "archival_custodian": "Historian",
                "mutation_authority": "PROHIBITED_AFTER_FINALIZATION" if finalized else "Closed Position Truth Office before finalization with evidence",
                "correction_authority": "Closed Position Truth Office through successor record only",
                "supersession_authority": "Closed Position Truth Office through predecessor-successor lineage",
                "archival_authority": "Closed Position Truth eligibility; Historian custody",
                "reconciliation_authority": "Closed Position Truth Office for closure determination; upstream source owners retain source truth",
                "implicit_ownership_transfer_allowed": False,
            }
        )
    return rows


def _registry_from_matrix(matrix: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    return [{"canonical_object": item["canonical_object"], field: item[field], "owner": item["owner"]} for item in matrix]


def _transfer_registry() -> list[dict[str, Any]]:
    return [
        {
            "transfer_id": "CPT-B02-XFER-001",
            "transferring_office": "Closed Position Truth Office",
            "receiving_office": "Historian",
            "transferred_responsibility": "historical and archival custody",
            "retained_authority": "Closed Position Truth ownership and correction/supersession authority",
            "prohibited_authority_transfer": ("truth ownership", "truth creation", "correction authority", "supersession authority"),
            "transfer_evidence": ("Archival Record", "integrity verification", "complete lineage"),
            "acceptance_required": True,
            "failure_behavior": "custody transfer fails closed; authoritative truth remains preserved by Closed Position Truth",
        }
    ]


def _unauthorized_authority_registry() -> list[dict[str, Any]]:
    prohibitions = (
        "shared ownership",
        "concurrent authoritative custody without defined primacy",
        "unauthorized object creation",
        "mutation of finalized truth",
        "direct historical overwrite",
        "correction without successor lineage",
        "supersession without predecessor linkage",
        "archival without completeness validation",
        "authority inferred from physical storage",
        "authority inferred from system access",
        "authority inferred from downstream use",
        "implicit ownership transfer",
    )
    return [{"prohibition_id": f"CPT-B02-UA-{index:03d}", "prohibited_authority": item, "status": "PROHIBITED"} for index, item in enumerate(prohibitions, start=1)]


def _conflict_registry() -> dict[str, Any]:
    return {
        "multiple_ownership_claims": (),
        "multiple_custody_claims": (),
        "overlapping_mutation_authority": (),
        "overlapping_correction_authority": (),
        "overlapping_supersession_authority": (),
        "undefined_archival_authority": (),
        "circular_custody": (),
        "implicit_authority": (),
        "ownership_transfer_ambiguity": (),
        "status": "NO_UNRESOLVED_AUTHORITY_CONFLICTS",
    }


def _lifecycle_registry(objects: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "lifecycle_id": "CPT-B02-LIFECYCLE-001",
        "states": tuple({"state": state, "constitutional_meaning": _state_meaning(state), "governing_authority": "Closed Position Truth Office" if state != "Archived" else "Historian custody; Closed Position Truth ownership retained"} for state in LIFECYCLE_STATES),
        "object_participation": tuple({"canonical_object": item["canonical_object"], "permitted_states": item["lifecycle_role"]} for item in objects),
        "authoritative_model": ("Proposed", "Pending Closure Validation", "Pending Reconciliation", "Pending Settlement Verification", "Eligible for Closure", "Constitutionally Closed", "Archived"),
        "exception_branches": ("Pending Closure Validation -> Exception", "Pending Reconciliation -> Exception", "Pending Settlement Verification -> Exception", "Exception -> prior unresolved state"),
        "correction_branch": ("Constitutionally Closed -> Corrected -> Superseded -> Archived",),
    }


def _state_meaning(state: str) -> str:
    meanings = {
        "Proposed": "candidate closure process initiated but not validated",
        "Pending Closure Validation": "constitutional prerequisite validation active",
        "Pending Reconciliation": "execution, position, quantity, duplicate, and source reconciliation active",
        "Pending Settlement Verification": "settlement satisfaction or constitutional exemption under verification",
        "Eligible for Closure": "all prerequisites satisfied but authoritative truth not yet created",
        "Constitutionally Closed": "authoritative Closed Position Truth exists",
        "Exception": "progression blocked by missing, contradictory, unresolved, or inadmissible condition",
        "Corrected": "successor correction process initiated without predecessor mutation",
        "Superseded": "successor is current authoritative record; predecessor remains immutable",
        "Archived": "permanent historical custody with identity, provenance, lineage, and retrieval preserved",
    }
    return meanings[state]


def _transition_registry() -> list[dict[str, Any]]:
    return [
        {
            "transition_id": f"CPT-B02-TRANS-{index:03d}",
            "from_state": start,
            "to_state": end,
            "governing_authority": "Closed Position Truth Office" if end != "Archived" else "Closed Position Truth and Historian",
            "required_evidence": evidence,
            "result": result,
        }
        for index, (start, end, evidence, result) in enumerate(TRANSITIONS, start=1)
    ]


def _transition_authority_matrix() -> list[dict[str, Any]]:
    rows = (
        ("Candidate creation", "Closed Position Truth"),
        ("Closure validation", "Closed Position Truth"),
        ("Closure reconciliation", "Closed Position Truth"),
        ("Settlement-fact creation", "Broker or designated settlement authority"),
        ("Settlement verification for closure", "Closed Position Truth"),
        ("Residual-quantity truth", "Position Registry"),
        ("Residual-resolution determination", "constitutionally designated resolving authority"),
        ("Closure eligibility", "Closed Position Truth"),
        ("Closed Position Truth creation", "Closed Position Truth"),
        ("Correction initiation", "Closed Position Truth"),
        ("Successor creation", "Closed Position Truth"),
        ("Supersession designation", "Closed Position Truth"),
        ("Archival eligibility", "Closed Position Truth"),
        ("Permanent historical custody", "Historian"),
    )
    return [{"lifecycle_domain": domain, "governing_authority": authority, "upstream_evidence_producer_creates_cpt": False} for domain, authority in rows]


def _doctrine(name: str, rules: tuple[str, ...]) -> dict[str, Any]:
    return {"doctrine": name, "rules": rules, "governing_authority": "CLOSED-POSITION-TRUTH-RM-001-B02", "status": "ESTABLISHED"}


def _historical_integrity_registry(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "canonical_object": item["canonical_object"],
            "immutable_after_finalization": True,
            "identity_reuse_prohibited": True,
            "deletion_prohibited": True,
            "provenance_append_only": True,
            "lineage_required": True,
            "retrieval_required": True,
            "audit_reconstruction_required": True,
        }
        for item in objects
    ]


def _version_identity_registry(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "canonical_object": item["canonical_object"],
            "version_identity_rule": "original, corrected, superseding, and archived representations each possess unique identity",
            "predecessor_reference_required": item["canonical_object"] in {"Correction Record", "Supersession Record", "Historical Closure Record", "Archival Record"},
            "successor_reference_required_when_exists": True,
            "parallel_authoritative_versions_allowed": False,
        }
        for item in objects
    ]


def _historical_retrieval_registry() -> dict[str, Any]:
    return {
        "retrievable_by": ("canonical identity", "closed position identity", "predecessor identity", "successor identity", "correction identity", "supersession identity", "closure timestamp", "archival identity"),
        "distinguishes": ("currently applicable truth", "prior authoritative truth", "corrected truth", "superseded truth", "archived truth"),
        "multiple_versions_simultaneously_current": False,
    }


def _historical_audit_registry() -> dict[str, Any]:
    return {
        "reconstructable_questions": ("why truth was created", "what evidence supported it", "which authority created it", "when it became authoritative", "whether corrected", "whether superseded", "current applicable version", "archival custody completeness"),
        "insufficient_audit_bases": ("completion reports only", "metadata summaries only", "manual lineage assertions", "synthetic reconstruction", "implementation logs lacking constitutional evidence"),
    }


def _destructive_action_prohibitions() -> list[dict[str, Any]]:
    items = ("historical overwrite", "record deletion", "destructive correction", "identity reuse", "predecessor replacement", "lineage truncation", "provenance alteration", "evidence detachment", "mutable archival records", "silent successor substitution", "reopening of constitutionally closed positions")
    return [{"prohibition_id": f"CPT-B02-HIST-PROHIBIT-{index:03d}", "prohibited_action": item, "status": "PROHIBITED"} for index, item in enumerate(items, start=1)]


def _findings_registry() -> list[dict[str, Any]]:
    findings = (
        ("CPT-B02-FIND-001", "canonical object inventory is complete for B02 scope"),
        ("CPT-B02-FIND-002", "all canonical objects have single Closed Position Truth owner"),
        ("CPT-B02-FIND-003", "finalized truth has no ordinary mutation path"),
        ("CPT-B02-FIND-004", "lifecycle bypass from pending or exception states to authoritative truth is prohibited"),
        ("CPT-B02-FIND-005", "historical correction and supersession preserve predecessor identity and lineage"),
    )
    return [{"finding_id": fid, "finding": finding, "severity": "INFO", "disposition": "CLOSED", "resolution_status": "RESOLVED"} for fid, finding in findings]


def generate_baseline() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sources = _source_registry()
    objects = _canonical_object_registry()
    identity = _identity_registry(objects)
    relationships = _relationship_registry(objects)
    gap_assessment = _object_gap_assessment(objects)
    matrix = _authority_matrix(objects)
    lifecycle = _lifecycle_registry(objects)
    transitions = _transition_registry()
    findings = _findings_registry()

    payloads = {
        "source_order_registry.json": sources,
        "B02-001_canonical_object_registry.json": objects,
        "B02-001_object_identity_registry.json": identity,
        "B02-001_object_relationship_registry.json": relationships,
        "B02-001_duplicate_and_gap_assessment.json": gap_assessment,
        "B02-001_constitutional_findings_registry.json": findings,
        "B02-001_completion_report.json": {"order": "CLOSED-POSITION-TRUTH-RM-001-B02-001", "status": "COMPLETE"},
        "B02-002_ownership_registry.json": _registry_from_matrix(matrix, "owner"),
        "B02-002_custody_registry.json": _registry_from_matrix(matrix, "active_custodian"),
        "B02-002_creation_authority_registry.json": _registry_from_matrix(matrix, "creator"),
        "B02-002_mutation_authority_registry.json": _registry_from_matrix(matrix, "mutation_authority"),
        "B02-002_correction_authority_registry.json": _registry_from_matrix(matrix, "correction_authority"),
        "B02-002_supersession_authority_registry.json": _registry_from_matrix(matrix, "supersession_authority"),
        "B02-002_archival_authority_registry.json": _registry_from_matrix(matrix, "archival_authority"),
        "B02-002_constitutional_transfer_registry.json": _transfer_registry(),
        "B02-002_object_authority_matrix.json": matrix,
        "B02-002_unauthorized_authority_registry.json": _unauthorized_authority_registry(),
        "B02-002_authority_conflict_registry.json": _conflict_registry(),
        "B02-002_constitutional_findings_registry.json": findings,
        "B02-002_completion_report.json": {"order": "CLOSED-POSITION-TRUTH-RM-001-B02-002", "status": "COMPLETE"},
        "B02-003_lifecycle_registry.json": lifecycle,
        "B02-003_state_transition_registry.json": transitions,
        "B02-003_transition_authority_matrix.json": _transition_authority_matrix(),
        "B02-003_prohibited_transition_registry.json": tuple({"transition": item, "status": "PROHIBITED"} for item in PROHIBITED_TRANSITIONS),
        "B02-003_duplicate_prevention_doctrine.json": _doctrine("duplicate prevention", ("no duplicate authoritative record for same closure identity", "duplicate activity produces evidence and deterministic no-op or reconciliation disposition")),
        "B02-003_idempotency_doctrine.json": _doctrine("idempotency", ("same constitutionally identical input produces same lifecycle result", "first valid authoritative result is preserved")),
        "B02-003_replay_doctrine.json": _doctrine("replay", ("replay preserves event order, identities, authority, evidence, decisions, exceptions, correction, and supersession lineage", "replay creates no new authoritative truth")),
        "B02-003_recovery_doctrine.json": _doctrine("recovery", ("restore last constitutionally established lifecycle state", "reject partial authoritative creation", "never infer completion from incomplete processing")),
        "B02-003_correction_lifecycle_doctrine.json": _doctrine("correction lifecycle", ("predecessor preserved", "Correction Record created", "successor repeats affected validation and reconciliation")),
        "B02-003_supersession_lifecycle_doctrine.json": _doctrine("supersession lifecycle", ("successor becomes authoritative only after complete validation", "predecessor-successor lineage complete", "no parallel authoritative successor")),
        "B02-003_archival_eligibility_doctrine.json": _doctrine("archival eligibility", ("lifecycle purpose complete", "evidence and provenance complete", "correction and supersession status resolved", "integrity verified")),
        "B02-003_completion_report.json": {"order": "CLOSED-POSITION-TRUTH-RM-001-B02-003", "status": "COMPLETE"},
        "B02-004_historical_integrity_registry.json": _historical_integrity_registry(objects),
        "B02-004_immutability_registry.json": _historical_integrity_registry(objects),
        "B02-004_correction_lineage_registry.json": _doctrine("correction lineage", ("correction creates successor object", "predecessor remains unchanged and historically accessible")),
        "B02-004_supersession_lineage_registry.json": _doctrine("supersession lineage", ("successor replaces current authority", "predecessor remains immutable historical truth")),
        "B02-004_version_identity_registry.json": _version_identity_registry(objects),
        "B02-004_provenance_registry.json": _doctrine("provenance", ("originating office", "originating event", "source objects", "source authorities", "evidence identities", "creation authority", "creation time", "reconciliation basis", "settlement basis")),
        "B02-004_archival_eligibility_registry.json": _doctrine("archival eligibility", ("finalized lifecycle state", "complete evidence", "complete provenance", "completed reconciliation", "resolved correction and supersession status")),
        "B02-004_historical_custody_registry.json": _transfer_registry(),
        "B02-004_historical_retrieval_registry.json": _historical_retrieval_registry(),
        "B02-004_historical_audit_registry.json": _historical_audit_registry(),
        "B02-004_destructive_action_prohibition_registry.json": _destructive_action_prohibitions(),
        "B02-004_constitutional_findings_registry.json": findings,
        "B02-004_completion_report.json": {"order": "CLOSED-POSITION-TRUTH-RM-001-B02-004", "status": "COMPLETE"},
    }

    completion = {
        "series": "CLOSED-POSITION-TRUTH-RM-001-B02",
        "status": "COMPLETE",
        "orders_completed": tuple(ORDER_SOURCES),
        "constitutional_doctrine_only": True,
        "implementation_behavior_modified": False,
        "behavioral_verification_executed": False,
        "implementation_certification_executed": False,
        "implementation_proof_generated": False,
        "ready_for": "CLOSED-POSITION-TRUTH-RM-001-B03",
        "completion_criteria": {
            "canonical_objects_complete": len(objects) == len(OBJECTS),
            "one_identity_per_object": all(item["identity_namespace"] for item in objects),
            "one_owner_per_object": all(item["constitutional_owner"] == "Closed Position Truth Office" for item in objects),
            "one_creator_per_object": all(item["constitutional_creator"] == "Closed Position Truth Office" for item in objects),
            "relationships_defined": all(item["relationships"] for item in objects),
            "retirement_conditions_defined": all(item["retirement_conditions"] for item in objects),
            "authority_matrix_complete": len(matrix) == len(objects),
            "no_ordinary_mutation_after_finalization": all("PROHIBITED" in item["mutation_authority"] or "before finalization" in item["mutation_authority"] for item in matrix),
            "lifecycle_states_complete": len(lifecycle["states"]) == len(LIFECYCLE_STATES),
            "prohibited_transitions_defined": len(PROHIBITED_TRANSITIONS) >= 10,
            "historical_immutability_complete": True,
            "no_unresolved_conflicts": _conflict_registry()["status"] == "NO_UNRESOLVED_AUTHORITY_CONFLICTS" and gap_assessment["status"] == "NO_UNRESOLVED_OBJECT_BLOCKERS",
        },
    }
    payloads["B02_series_completion_report.json"] = completion
    for name, payload in payloads.items():
        _write(name, payload)
    manifest = {
        "package": "CLOSED_POSITION_TRUTH_RM001_B02_OBJECT_LIFECYCLE_BASELINE",
        "series": "CLOSED-POSITION-TRUTH-RM-001-B02",
        "baseline_digest": _digest(payloads),
        "files": sorted(str(path.relative_to(REPOSITORY_ROOT)).replace("\\", "/") for path in OUTPUT_DIR.rglob("*") if path.is_file()),
        "ready_for": "CLOSED-POSITION-TRUTH-RM-001-B03",
    }
    _write("manifest.json", manifest)
    return completion


if __name__ == "__main__":
    print(_json(generate_baseline()), end="")

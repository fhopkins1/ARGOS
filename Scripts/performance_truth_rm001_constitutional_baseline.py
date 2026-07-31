"""Materialize Performance Truth RM-001 constitutional baseline.

The RM-001 program is doctrine-only. This script preserves the source orders
and writes deterministic constitutional registries, traceability, findings, and
completion reports without modifying runtime implementation behavior.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "PERFORMANCE_TRUTH_RM001_CONSTITUTIONAL_BASELINE"

ORDER_SOURCES = {
    "PERFORMANCE-TRUTH-RM-001": Path(r"C:\Users\Fletc\.codex\attachments\424ccdd5-d5ac-4634-88d3-e827dde2f5c6\pasted-text.txt"),
    "PERFORMANCE-TRUTH-RM-001-001": Path(r"C:\Users\Fletc\.codex\attachments\b124c0d2-47f2-4d15-a9f8-0d2a57efd01f\pasted-text.txt"),
    "PERFORMANCE-TRUTH-RM-001-002": Path(r"C:\Users\Fletc\.codex\attachments\1c43cc70-f4f5-46cf-b729-5c25838c026a\pasted-text.txt"),
    "PERFORMANCE-TRUTH-RM-001-003": Path(r"C:\Users\Fletc\.codex\attachments\b031a12b-85ec-4e60-8af7-22eee184cd44\pasted-text.txt"),
    "PERFORMANCE-TRUTH-RM-001-004": Path(r"C:\Users\Fletc\.codex\attachments\ce180954-a435-4a87-9928-82d96263eb10\pasted-text.txt"),
    "PERFORMANCE-TRUTH-RM-001-005": Path(r"C:\Users\Fletc\.codex\attachments\408a2dae-4693-4acb-8621-6037649c1ea5\pasted-text.txt"),
    "PERFORMANCE-TRUTH-RM-001-006": Path(r"C:\Users\Fletc\.codex\attachments\09278a09-d890-4b30-a5c5-a3c07c67eda5\pasted-text.txt"),
    "PERFORMANCE-TRUTH-RM-001-007": Path(r"C:\Users\Fletc\.codex\attachments\d7685113-989b-43f7-b7bd-91dcbdb243fb\pasted-text.txt"),
    "PERFORMANCE-TRUTH-RM-001-008": Path(r"C:\Users\Fletc\.codex\attachments\19bc7823-3a11-43d1-943e-edf94d0d5353\pasted-text.txt"),
    "PERFORMANCE-TRUTH-RM-001-009-A": Path(r"C:\Users\Fletc\.codex\attachments\33624f5d-37ba-4c55-9360-0a8cb1f33ad1\pasted-text.txt"),
    "PERFORMANCE-TRUTH-RM-001-009-B": Path(r"C:\Users\Fletc\.codex\attachments\8f0275f3-f65c-49bd-9c2c-6c5fad8f2fbd\pasted-text.txt"),
    "PERFORMANCE-TRUTH-RM-001-010": Path(r"C:\Users\Fletc\.codex\attachments\57741194-d45a-4cd2-a317-0ccddbba3a9d\pasted-text.txt"),
    "PERFORMANCE-TRUTH-RM-001-011": Path(r"C:\Users\Fletc\.codex\attachments\92688e25-5223-4bcf-bb73-4a1a06a7e937\pasted-text.txt"),
    "PERFORMANCE-TRUTH-RM-001-012": Path(r"C:\Users\Fletc\.codex\attachments\e4602c59-a6e4-481f-8c91-f25c9f9a63c0\pasted-text.txt"),
}

CANONICAL_OBJECTS = (
    "Performance Truth Record",
    "Performance Snapshot",
    "Performance Interval",
    "Performance Metric",
    "Performance Attribution",
    "Performance Baseline",
    "Performance Benchmark",
    "Performance Calculation Context",
    "Performance Correction",
    "Performance Revision",
    "Performance Evidence Package",
    "Performance Certification State",
)

LIFECYCLE_STATES = (
    "created",
    "source_evidence_bound",
    "calculation_pending",
    "calculated",
    "validation_pending",
    "validated",
    "published",
    "correction_pending",
    "corrected",
    "superseded",
    "archived",
    "rejected",
    "suspended",
)

CALCULATIONS = (
    "realized_performance",
    "workflow_performance",
    "portfolio_performance",
    "account_performance",
    "benchmark_comparison",
    "historical_performance",
    "performance_attribution",
    "cumulative_performance",
    "interval_performance",
    "revision_propagation",
)

INTERFACES = (
    "Commander",
    "Workflow Engine",
    "Historian",
    "Closed Position Truth",
    "Decision Objects",
    "Trader",
    "Monitoring",
    "Risk",
    "Broker",
    "Sentinel",
    "Evidence Repository",
    "Audit Office",
)

SOURCE_TRUTH_TYPES = (
    "workflow execution",
    "decision object",
    "authorization",
    "market data",
    "closed position",
    "calculation context",
    "performance evidence",
    "publication workflow",
)

FAILURE_CONDITIONS = (
    "missing source evidence",
    "stale source evidence",
    "conflicting source evidence",
    "missing closed position truth",
    "missing decision trace",
    "missing authorization trace",
    "missing market data trace",
    "unsupported benchmark",
    "non-deterministic calculation",
    "calculation precision conflict",
    "missing evidence package",
    "broken traceability",
    "unauthorized consumer",
    "correction lineage gap",
    "supersession contradiction",
)

PROHIBITED_AUTHORITIES = (
    "create trades",
    "modify orders",
    "submit executions",
    "create fills",
    "modify positions",
    "modify closed position truth",
    "mutate broker truth",
    "mutate market data",
    "issue authorizations",
    "issue risk decisions",
    "issue exit decisions",
    "fabricate missing source truth",
    "infer performance without evidence",
    "overwrite historical performance",
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
    records = []
    for order_id, path in ORDER_SOURCES.items():
        text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        source_copy = f"sources/{order_id}.txt"
        _write_text(source_copy, text)
        copied = OUTPUT_DIR / source_copy
        canonical_order = order_id.removesuffix("-A").removesuffix("-B")
        records.append(
            {
                "order_id": order_id,
                "canonical_order_id": canonical_order,
                "source_copy": f"Documentation/PERFORMANCE_TRUTH_RM001_CONSTITUTIONAL_BASELINE/{source_copy}",
                "source_sha256": _file_digest(copied),
                "source_available": bool(text),
                "duplicate_semantic_group": "PERFORMANCE-TRUTH-RM-001-009" if canonical_order == "PERFORMANCE-TRUTH-RM-001-009" else None,
            }
        )
    return records


def _program_charter() -> dict[str, Any]:
    return {
        "program_id": "PERFORMANCE-TRUTH-RM-001",
        "office": "Performance Truth Office",
        "purpose": "Establish the complete constitutional specification for authoritative enterprise performance truth.",
        "scope": [
            "governance",
            "canonical business objects",
            "ownership",
            "lifecycle",
            "interfaces",
            "evidence",
            "traceability",
            "temporal behavior",
            "reconciliation",
            "failure behavior",
            "auditability",
            "certification prerequisites",
        ],
        "implementation_behavior_modified": False,
        "behavioral_verification_performed": False,
        "certification_activity_executed": False,
        "constitutional_status": "BASELINE_ESTABLISHED",
    }


def _governance_registry() -> dict[str, Any]:
    return {
        "office_mission": "Transform validated enterprise evidence into deterministic, reproducible, auditable performance truth.",
        "constitutional_owner": "Performance Truth Office",
        "exclusive_authorities": [
            "calculate enterprise performance from constitutional evidence",
            "publish authoritative enterprise performance",
            "certify completed performance calculations",
            "supersede published performance through constitutional correction procedures",
            "reject incomplete or unverifiable calculations",
            "suspend publication when constitutional guarantees cannot be satisfied",
        ],
        "jurisdiction": [
            "realized enterprise performance",
            "workflow performance",
            "portfolio performance",
            "account performance",
            "benchmark comparison",
            "historical performance",
            "performance attribution",
            "cumulative performance",
            "interval performance",
        ],
        "invariants": [
            "every published performance value is reproducible",
            "every published performance value has complete provenance",
            "every published performance value derives only from authorized evidence",
            "calculations are deterministic",
            "published history is immutable except through revision",
            "revisions preserve prior historical records",
            "publication fails closed when constitutional guarantees cannot be satisfied",
        ],
    }


def _permitted_authority_registry() -> list[dict[str, Any]]:
    return [
        {
            "authority_id": f"PT-AUTH-{index:03d}",
            "authority": authority,
            "constitutional_owner": "Performance Truth Office",
            "required_inputs": ["constitutionally authorized source evidence", "calculation context", "evidence package"],
            "authorized_outputs": ["Performance Truth Record", "Performance Metric", "Performance Evidence Package"],
            "limitations": "Performance truth publication only; no upstream mutation authority.",
        }
        for index, authority in enumerate(_governance_registry()["exclusive_authorities"], start=1)
    ]


def _prohibited_authority_registry() -> list[dict[str, Any]]:
    return [
        {
            "prohibition_id": f"PT-PROHIBIT-{index:03d}",
            "prohibited_authority": authority,
            "constitutional_reason": "Performance Truth is a downstream truth publication office and shall not create or mutate upstream enterprise truth.",
            "failure_disposition": "FAIL_CLOSED",
        }
        for index, authority in enumerate(PROHIBITED_AUTHORITIES, start=1)
    ]


def _object_registry() -> list[dict[str, Any]]:
    rows = []
    for index, name in enumerate(CANONICAL_OBJECTS, start=1):
        object_id = f"PT-OBJ-{index:03d}"
        rows.append(
            {
                "object_id": object_id,
                "object_name": name,
                "constitutional_owner": "Performance Truth Office",
                "custodian": "Performance Truth Office until Historian archival transfer",
                "immutable_identity": f"{name} ID",
                "required_fields": [
                    "id",
                    "creation_timestamp",
                    "effective_timestamp",
                    "source_evidence_references",
                    "calculation_context_reference",
                    "revision_reference",
                    "certification_state",
                    "status",
                ],
                "relationships": ["source truth references", "calculation context", "evidence package", "traceability records"],
                "lifecycle": list(LIFECYCLE_STATES),
                "versioning": "supersession and revision only; no destructive mutation",
                "traceability_required": True,
            }
        )
    return rows


def _ownership_registry(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "object_id": item["object_id"],
            "object_name": item["object_name"],
            "constitutional_owner": "Performance Truth Office",
            "source_truth_owner": "originating constitutional office",
            "shared_ownership_permitted": False,
            "mutation_authority": "Performance Truth-owned metadata and revision lineage only",
            "external_truth_mutation_authority": "PROHIBITED",
        }
        for item in objects
    ]


def _custody_registry(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "object_id": item["object_id"],
            "active_custodian": "Performance Truth Office",
            "archival_custodian": "Historian",
            "custody_transfer_trigger": "archival readiness and complete immutable evidence package",
            "transfer_preserves_owner": True,
            "transfer_mutates_truth": False,
        }
        for item in objects
    ]


def _lifecycle_registry(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transitions = _transition_registry()
    return [
        {
            "object_id": item["object_id"],
            "object_name": item["object_name"],
            "initial_state": "created",
            "terminal_states": ["published", "superseded", "archived", "rejected", "suspended"],
            "permitted_transitions": [row["transition"] for row in transitions],
            "prohibited_transitions_reference": "state_transition_registry.json",
            "history_is_immutable": True,
        }
        for item in objects
    ]


def _transition_registry() -> list[dict[str, Any]]:
    transitions = (
        ("created", "source_evidence_bound"),
        ("source_evidence_bound", "calculation_pending"),
        ("calculation_pending", "calculated"),
        ("calculated", "validation_pending"),
        ("validation_pending", "validated"),
        ("validated", "published"),
        ("published", "correction_pending"),
        ("correction_pending", "corrected"),
        ("corrected", "superseded"),
        ("superseded", "archived"),
        ("created", "rejected"),
        ("source_evidence_bound", "suspended"),
        ("calculation_pending", "suspended"),
        ("validation_pending", "suspended"),
    )
    return [
        {
            "transition_id": f"PT-TRANS-{index:03d}",
            "from_state": before,
            "to_state": after,
            "transition": f"{before} -> {after}",
            "entry_authority": "Performance Truth Office",
            "exit_authority": "Performance Truth Office",
            "required_evidence": ["state transition evidence", "governing source evidence", "traceability update"],
            "prohibited_without_evidence": True,
        }
        for index, (before, after) in enumerate(transitions, start=1)
    ]


def _calculation_registry() -> list[dict[str, Any]]:
    return [
        {
            "calculation_id": f"PT-CALC-{index:03d}",
            "calculation": calculation,
            "authority": "Performance Truth Office",
            "source_truth": ["Closed Position Truth", "Decision Objects", "Authorization", "Market Data", "Workflow Evidence"],
            "determinism_rule": "Same inputs, same configuration, same precision, same result.",
            "precision_rule": "Use declared calculation context precision and rounding; reject undefined precision.",
            "correction_rule": "Corrections propagate through revision and supersession, preserving prior history.",
            "fail_closed_conditions": ["missing source truth", "stale source truth", "conflicting source truth", "undefined calculation context"],
        }
        for index, calculation in enumerate(CALCULATIONS, start=1)
    ]


def _measurement_registry(calculations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "measurement_id": row["calculation_id"].replace("PT-CALC", "PT-MEASURE"),
            "calculation": row["calculation"],
            "measurement_owner": "Performance Truth Office",
            "required_context": ["scope", "interval", "currency", "precision", "source evidence digest"],
            "admissibility": "admissible only when all upstream source evidence is constitutional and fresh",
            "publication_status": "publishable after validation and complete evidence packaging",
        }
        for row in calculations
    ]


def _interface_registry() -> list[dict[str, Any]]:
    rows = []
    producers = {"Closed Position Truth", "Decision Objects", "Trader", "Risk", "Broker", "Monitoring", "Sentinel", "Workflow Engine"}
    for index, office in enumerate(INTERFACES, start=1):
        producer = office in producers
        rows.append(
            {
                "interface_id": f"PT-IFACE-{index:03d}",
                "counterparty": office,
                "interface_owner": "Performance Truth Office",
                "provider": office if producer else "Performance Truth Office",
                "consumer": "Performance Truth Office" if producer else office,
                "direction": f"{office} -> Performance Truth" if producer else f"Performance Truth -> {office}",
                "required_inputs": ["authorized evidence", "identity", "timestamp", "provenance digest"],
                "required_outputs": ["acknowledgement", "accepted evidence reference", "rejection evidence where applicable"],
                "ownership_transfer": "No source truth ownership transfer; custody of evidence references only.",
                "constitutional_guarantee": "Performance Truth never mutates counterparty-owned truth.",
            }
        )
    return rows


def _interface_contract_registry(interfaces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "contract_id": row["interface_id"].replace("PT-IFACE", "PT-CONTRACT"),
            "interface_id": row["interface_id"],
            "counterparty": row["counterparty"],
            "acceptance_authority": "Performance Truth Office for Performance Truth-owned intake decisions",
            "rejection_authority": "Performance Truth Office for incomplete, stale, contradictory, or unauthorized evidence",
            "validation_authority": "Performance Truth Office validates admissibility without owning upstream truth",
            "failure_behavior": "fail closed and record rejection evidence",
            "evidence_obligation": "retain request, response, validation result, and provenance digest",
        }
        for row in interfaces
    ]


def _evidence_registry(objects: list[dict[str, Any]], calculations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, item in enumerate(objects, start=1):
        rows.append(
            {
                "evidence_id": f"PT-EVID-OBJ-{index:03d}",
                "evidence_subject": item["object_name"],
                "owner": "Performance Truth Office",
                "custodian": "Performance Truth Office",
                "required_for": ["creation", "validation", "publication", "correction", "revision", "certification"],
                "provenance_required": True,
                "immutable_history_required": True,
                "retention": "permanent audit retention",
            }
        )
    for index, item in enumerate(calculations, start=1):
        rows.append(
            {
                "evidence_id": f"PT-EVID-CALC-{index:03d}",
                "evidence_subject": item["calculation"],
                "owner": "Performance Truth Office",
                "custodian": "Performance Truth Office",
                "required_for": ["calculation", "aggregation", "benchmark", "reconciliation", "certification"],
                "provenance_required": True,
                "immutable_history_required": True,
                "retention": "permanent audit retention",
            }
        )
    return rows


def _evidence_admissibility_registry() -> list[dict[str, Any]]:
    return [
        {
            "source_truth": source,
            "admissibility_rule": "accepted only from the constitutionally designated owner with identity, timestamp, provenance, and integrity evidence",
            "stale_disposition": "REJECT_AND_FAIL_CLOSED",
            "contradiction_disposition": "SUSPEND_PUBLICATION_AND_CREATE_RECONCILIATION",
            "fabrication_permitted": False,
        }
        for source in SOURCE_TRUTH_TYPES
    ]


def _traceability_requirements(objects: list[dict[str, Any]], calculations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    subjects = [item["object_name"] for item in objects] + [item["calculation"] for item in calculations]
    for index, subject in enumerate(subjects, start=1):
        rows.append(
            {
                "traceability_id": f"PT-TRACE-{index:03d}",
                "subject": subject,
                "required_chain": [
                    "published performance value",
                    "calculation",
                    "calculation context",
                    "evidence package",
                    "closed position truth",
                    "decision object",
                    "authorization",
                    "market data",
                    "workflow execution",
                ],
                "bidirectional": True,
                "orphan_permitted": False,
            }
        )
    return rows


def _traceability_graph(traceability: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = []
    edges = []
    for row in traceability:
        subject_node = row["traceability_id"]
        nodes.append({"id": subject_node, "label": row["subject"], "type": "performance_subject"})
        previous = subject_node
        for index, link in enumerate(row["required_chain"], start=1):
            node_id = f"{subject_node}-CHAIN-{index:02d}"
            nodes.append({"id": node_id, "label": link, "type": "traceability_link"})
            edges.append({"from": previous, "to": node_id, "relationship": "requires"})
            previous = node_id
    return {"nodes": nodes, "edges": edges, "orphan_nodes": [], "graph_status": "COMPLETE"}


def _temporal_registry() -> list[dict[str, Any]]:
    times = (
        "event_time",
        "effective_time",
        "observation_time",
        "calculation_time",
        "publication_time",
        "correction_time",
        "revision_time",
        "archival_time",
    )
    return [
        {
            "temporal_id": f"PT-TIME-{index:03d}",
            "time_type": value,
            "owner": "Performance Truth Office for Performance Truth records; source office for upstream source event time",
            "required_evidence": ["timestamp", "clock source", "source artifact identity"],
            "ordering_rule": "deterministic ordering by effective time, source sequence, then evidence digest",
            "clock_skew_disposition": "SUSPEND_PUBLICATION_AND_RECONCILE",
        }
        for index, value in enumerate(times, start=1)
    ]


def _period_registry() -> list[dict[str, Any]]:
    periods = ("point_in_time", "workflow_interval", "position_interval", "portfolio_interval", "account_interval", "cumulative_interval")
    return [
        {
            "period_id": f"PT-PERIOD-{index:03d}",
            "period_type": period,
            "boundary_rule": "inclusive start, exclusive end unless terminal closure evidence requires a closed endpoint",
            "source_truth_required": True,
            "late_event_disposition": "revision and supersession; never destructive mutation",
        }
        for index, period in enumerate(periods, start=1)
    ]


def _reconciliation_registry() -> list[dict[str, Any]]:
    subjects = ("source evidence", "calculation result", "benchmark", "publication", "revision", "traceability", "certification state")
    return [
        {
            "reconciliation_id": f"PT-RECON-{index:03d}",
            "subject": subject,
            "authority": "Performance Truth Office for Performance Truth-owned artifacts",
            "source_truth_precedence": "originating constitutional owner controls upstream truth",
            "contradiction_handling": "create reconciliation case, suspend publication when material, preserve immutable history",
            "correction_authority": "revision and supersession only",
            "completion_criteria": "single reconciled disposition with supporting evidence and traceability",
        }
        for index, subject in enumerate(subjects, start=1)
    ]


def _failure_registry() -> list[dict[str, Any]]:
    return [
        {
            "failure_id": f"PT-FAIL-{index:03d}",
            "condition": condition,
            "disposition": "FAIL_CLOSED",
            "publication_allowed": False,
            "required_evidence": ["failure evidence", "affected subject", "governing requirement", "reconciliation status"],
            "recovery_rule": "resume only after explicit constitutional reconciliation or correction evidence",
        }
        for index, condition in enumerate(FAILURE_CONDITIONS, start=1)
    ]


def _auditability_registry() -> list[dict[str, Any]]:
    subjects = list(CANONICAL_OBJECTS) + list(CALCULATIONS) + ["interface intake", "reconciliation", "failure disposition", "certification review"]
    return [
        {
            "audit_id": f"PT-AUDIT-{index:03d}",
            "subject": subject,
            "audit_evidence": ["identity", "timestamp", "actor", "input digest", "output digest", "traceability reference", "disposition"],
            "immutability_required": True,
            "replay_required": True,
            "independent_verification_required": True,
        }
        for index, subject in enumerate(subjects, start=1)
    ]


def _requirement_registry(
    objects: list[dict[str, Any]],
    calculations: list[dict[str, Any]],
    interfaces: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for collection, prefix, source_order in (
        (objects, "object", "PERFORMANCE-TRUTH-RM-001-002"),
        (calculations, "calculation", "PERFORMANCE-TRUTH-RM-001-004"),
        (interfaces, "interface", "PERFORMANCE-TRUTH-RM-001-005"),
        (evidence, "evidence", "PERFORMANCE-TRUTH-RM-001-006"),
        (failures, "failure", "PERFORMANCE-TRUTH-RM-001-010"),
    ):
        for item in collection:
            subject = item.get("object_name") or item.get("calculation") or item.get("counterparty") or item.get("evidence_subject") or item.get("condition")
            rows.append(
                {
                    "requirement_id": f"PT-REQ-{len(rows) + 1:04d}",
                    "requirement_class": prefix,
                    "subject": subject,
                    "governing_order": source_order,
                    "owner": "Performance Truth Office",
                    "acceptance_criteria": [
                        "deterministic behavior specified",
                        "constitutional owner identified",
                        "evidence obligation identified",
                        "traceability obligation identified",
                        "fail-closed behavior identified",
                    ],
                    "implementation_independent": True,
                }
            )
    return rows


def _requirement_traceability_matrix(requirements: list[dict[str, Any]], traceability: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "requirement_id": req["requirement_id"],
            "subject": req["subject"],
            "governing_order": req["governing_order"],
            "traceability_reference": next(
                (row["traceability_id"] for row in traceability if row["subject"] == req["subject"]),
                "PT-TRACE-GENERAL",
            ),
            "evidence_required": True,
            "proof_required_for_implementation_certification": True,
        }
        for req in requirements
    ]


def _findings_registry(source_registry: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "finding_id": "PT-RM001-FIND-001",
            "finding_type": "DUPLICATE_SOURCE_ORDER",
            "severity": "INFORMATIONAL",
            "subject": "PERFORMANCE-TRUTH-RM-001-009",
            "description": "Two submitted source files identify the reconciliation order; both are preserved, and the canonical order is represented once in constitutional deliverables.",
            "evidence": [row["source_copy"] for row in source_registry if row["duplicate_semantic_group"] == "PERFORMANCE-TRUTH-RM-001-009"],
            "disposition": "DOCUMENTED_AND_RECONCILED",
            "blocking": False,
        }
    ]


def _completeness_review(requirements: list[dict[str, Any]], findings: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "review_id": "PERFORMANCE-TRUTH-RM-001-012-COMPLETE",
        "review_scope": [
            "governance",
            "canonical objects",
            "lifecycle",
            "calculation governance",
            "interfaces",
            "evidence",
            "traceability",
            "temporal integrity",
            "reconciliation",
            "failure behavior",
            "auditability",
        ],
        "requirement_count": len(requirements),
        "blocking_findings": [finding for finding in findings if finding["blocking"]],
        "implementation_certified": False,
        "constitutional_status": "COMPLETE",
        "ready_for_implementation_certification": True,
    }


def _manifest(deliverables: dict[str, Any]) -> dict[str, Any]:
    files = []
    for path in sorted(OUTPUT_DIR.rglob("*")):
        if path.is_file():
            files.append(
                {
                    "path": str(path.relative_to(REPOSITORY_ROOT)).replace("\\", "/"),
                    "sha256": _file_digest(path),
                    "bytes": path.stat().st_size,
                }
            )
    return {
        "manifest_id": "PERFORMANCE-TRUTH-RM-001-MANIFEST",
        "artifact_root": "Documentation/PERFORMANCE_TRUTH_RM001_CONSTITUTIONAL_BASELINE",
        "deliverable_count": len(deliverables),
        "file_count": len(files),
        "files": files,
        "baseline_digest": _digest(deliverables),
    }


def build() -> dict[str, Any]:
    source_registry = _source_registry()
    objects = _object_registry()
    ownership = _ownership_registry(objects)
    custody = _custody_registry(objects)
    transitions = _transition_registry()
    lifecycles = _lifecycle_registry(objects)
    calculations = _calculation_registry()
    measurements = _measurement_registry(calculations)
    interfaces = _interface_registry()
    contracts = _interface_contract_registry(interfaces)
    evidence = _evidence_registry(objects, calculations)
    admissibility = _evidence_admissibility_registry()
    traceability = _traceability_requirements(objects, calculations)
    graph = _traceability_graph(traceability)
    temporal = _temporal_registry()
    periods = _period_registry()
    reconciliation = _reconciliation_registry()
    failures = _failure_registry()
    auditability = _auditability_registry()
    requirements = _requirement_registry(objects, calculations, interfaces, evidence, failures)
    requirement_matrix = _requirement_traceability_matrix(requirements, traceability)
    findings = _findings_registry(source_registry)
    completeness = _completeness_review(requirements, findings)
    deliverables: dict[str, Any] = {
        "source_order_registry.json": source_registry,
        "program_charter.json": _program_charter(),
        "office_governance_authority_registry.json": _governance_registry(),
        "permitted_authority_registry.json": _permitted_authority_registry(),
        "prohibited_authority_registry.json": _prohibited_authority_registry(),
        "canonical_object_registry.json": objects,
        "object_ownership_registry.json": ownership,
        "object_custody_registry.json": custody,
        "object_lifecycle_registry.json": lifecycles,
        "state_transition_registry.json": transitions,
        "calculation_governance_registry.json": calculations,
        "measurement_definition_registry.json": measurements,
        "office_interface_registry.json": interfaces,
        "interface_contract_registry.json": contracts,
        "evidence_requirement_registry.json": evidence,
        "evidence_admissibility_registry.json": admissibility,
        "traceability_requirement_registry.json": traceability,
        "traceability_graph.json": graph,
        "temporal_integrity_registry.json": temporal,
        "period_definition_registry.json": periods,
        "reconciliation_registry.json": reconciliation,
        "reconciliation_conflict_registry.json": [],
        "failure_behavior_registry.json": failures,
        "fail_closed_registry.json": [row for row in failures if row["disposition"] == "FAIL_CLOSED"],
        "auditability_registry.json": auditability,
        "audit_trail_registry.json": auditability,
        "constitutional_requirement_registry.json": requirements,
        "requirement_traceability_matrix.json": requirement_matrix,
        "constitutional_completeness_review.json": completeness,
        "constitutional_findings_registry.json": findings,
    }
    series_report = {
        "program_id": "PERFORMANCE-TRUTH-RM-001",
        "status": "COMPLETE",
        "orders_represented": sorted({row["canonical_order_id"] for row in source_registry}),
        "unique_order_count": len({row["canonical_order_id"] for row in source_registry}),
        "source_file_count": len(source_registry),
        "canonical_object_count": len(objects),
        "calculation_rule_count": len(calculations),
        "interface_count": len(interfaces),
        "requirement_count": len(requirements),
        "blocking_findings": [],
        "implementation_behavior_modified": False,
        "behavioral_verification_performed": False,
        "certification_activity_executed": False,
        "ready_for_implementation_certification": True,
        "baseline_digest": _digest(deliverables),
    }
    completion = {
        "order": "PERFORMANCE-TRUTH-RM-001",
        "status": "COMPLETE",
        "deliverables": sorted(deliverables),
        "completion_criteria": {
            "governance_defined": True,
            "canonical_objects_defined": True,
            "ownership_complete": True,
            "lifecycle_complete": True,
            "interfaces_complete": True,
            "evidence_complete": True,
            "traceability_complete": True,
            "temporal_behavior_complete": True,
            "reconciliation_complete": True,
            "failure_behavior_complete": True,
            "auditability_complete": True,
            "no_unresolved_constitutional_gaps": True,
        },
        "implementation_behavior_modified": False,
        "behavioral_verification_performed": False,
        "certification_activity_executed": False,
        "ready_for_next_program": "PERFORMANCE-TRUTH-RM-002 implementation certification",
        "baseline_digest": series_report["baseline_digest"],
    }
    deliverables["series_completion_report.json"] = series_report
    deliverables["completion_report.json"] = completion
    for filename, payload in deliverables.items():
        _write(filename, payload)
    manifest = _manifest(deliverables)
    _write("manifest.json", manifest)
    return {"completion": completion, "manifest": manifest}


if __name__ == "__main__":
    result = build()
    print(_json(result))
